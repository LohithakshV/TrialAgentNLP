"""Local, stateless educational research API. Never logs request bodies."""
import asyncio
import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError

from .models import Extraction, Search
from .privacy import clean_profile
from .research import prepare, search

load_dotenv(Path(__file__).resolve().parents[1] / '.env')
from .limits import limits, LimitError
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
UPSTREAM_ERRORS = (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError, TimeoutError)


def error(message, status=400):
    return JSONResponse({'error': message}, status_code=status, headers={'Cache-Control': 'no-store'})


async def parse_request(request, model):
    origin = request.headers.get('origin')
    if origin and origin not in ('http://localhost:3000', 'http://127.0.0.1:3000'):
        return error('This prototype accepts local requests only.', 403)
    try:
        limits.guard(request.client.host if request.client else 'unknown')
    except LimitError as exc:
        return limit_response(exc)
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 30000:
            return error('Input is too long.', 413)
    try:
        submission = model.model_validate_json(body)
    except ValidationError:
        return error('Check your details and try again. A condition and valid field lengths are required.')
    if not submission.consent:
        return error('Review the privacy notice before continuing.')
    if isinstance(submission, Extraction) and not os.getenv('GEMINI_API_KEY', '').strip():
        return error('The research service is not configured yet. Please try again later.', 503)
    return submission


@app.get('/api/health')
async def health():
    return JSONResponse({'liveAvailable': bool(os.getenv('GEMINI_API_KEY', '').strip()), 'quota': limits.snapshot()}, headers={'Cache-Control': 'no-store'})


def limit_response(exc):
    return JSONResponse({'error': exc.message, 'code': exc.code, 'retryAfter': exc.retry_after, 'resetsAt': limits.snapshot()['resetsAt']}, status_code=429, headers={'Retry-After': str(exc.retry_after), 'Cache-Control': 'no-store'})


@app.post('/api/extract')
async def extract_route(request: Request):
    submission = await parse_request(request, Extraction)
    if isinstance(submission, JSONResponse):
        return submission
    client_key = None
    try:
        client_key = limits.guard(request.client.host if request.client else 'unknown', search=True, model=True)
        async with asyncio.timeout(50):
            prepared = await prepare(submission.note)
        if prepared.status != 'ready':
            message = {
                'off_topic': 'Please describe a condition or clinical research topic to look up study records.',
                'needs_details': 'Add the condition you want to research, or use the clinical trial basics to get started.',
            }[prepared.status]
            return JSONResponse({'error': message, 'code': prepared.status}, status_code=422, headers={'Cache-Control': 'no-store'})
        return JSONResponse(prepared.model_dump(), headers={'Cache-Control': 'no-store'})
    except LimitError as exc:
        return limit_response(exc)
    except httpx.HTTPStatusError:
        return error('The research service is temporarily unavailable. Please try again later.', 502)
    except (httpx.RequestError, TimeoutError):
        return error('We could not reach the research service. Check your connection and try again.', 504)
    except UPSTREAM_ERRORS:
        return error('We could not understand the search. Include a condition, then try again. Your text has been kept.', 502)
    finally:
        if client_key:
            limits.release(client_key)


@app.post('/api/search')
async def search_route(request: Request):
    submission = await parse_request(request, Search)
    if isinstance(submission, JSONResponse):
        return submission
    try:
        client_key = limits.guard(request.client.host if request.client else 'unknown', search=True)
    except LimitError as exc:
        return limit_response(exc)

    async def stream():
        try:
            async with asyncio.timeout(110):
                async for kind, data in search(clean_profile(submission.profile)):
                    if await request.is_disconnected():
                        return
                    yield f'event: {kind}\ndata: {json.dumps(data)}\n\n'
        except LimitError as exc:
            yield 'event: error\ndata: ' + json.dumps({'message': exc.message, 'code': exc.code, 'retryAfter': exc.retry_after, 'resetsAt': limits.snapshot()['resetsAt']}) + '\n\n'
        except UPSTREAM_ERRORS:
            yield 'event: error\ndata: ' + json.dumps({'message': 'The search was interrupted. Please try again. Any records already retrieved remain available for manual review.'}) + '\n\n'
        finally:
            limits.release(client_key)
    return StreamingResponse(stream(), media_type='text/event-stream', headers={'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no'})
