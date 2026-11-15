"""Local, stateless educational research API. Never logs request bodies."""
import asyncio
import json
import os
from pathlib import Path
from urllib.parse import urlparse

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
LOCAL_ORIGINS = {'http://localhost:3000', 'http://127.0.0.1:3000'}
EXTRACT_TIMEOUT = 60
SEARCH_TIMEOUT = 240


def error(message, status=400):
    return JSONResponse({'error': message}, status_code=status, headers={'Cache-Control': 'no-store'})


def client_host(request):
    """Use the platform-provided client address on Vercel, the socket address locally."""
    if os.getenv('VERCEL'):
        forwarded = request.headers.get('x-vercel-forwarded-for') or request.headers.get('x-forwarded-for', '')
        first = forwarded.split(',')[0].strip()
        if first:
            return first
    return request.client.host if request.client else 'unknown'


def origin_allowed(request):
    origin = request.headers.get('origin')
    if not origin:
        return True
    configured = {
        value.strip().rstrip('/')
        for value in os.getenv('ALLOWED_ORIGINS', '').split(',')
        if value.strip()
    }
    if '*' in configured:
        return True
    normalized = origin.rstrip('/')
    if normalized in configured or normalized in LOCAL_ORIGINS:
        return True
    try:
        return urlparse(normalized).netloc == request.headers.get('host', '')
    except ValueError:
        return False


async def parse_request(request, model):
    if not origin_allowed(request):
        return error('This request origin is not allowed.', 403)
    try:
        limits.guard(client_host(request))
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
        client_key = limits.guard(client_host(request), search=True, model=True)
        async with asyncio.timeout(EXTRACT_TIMEOUT):
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
        client_key = limits.guard(client_host(request), search=True)
    except LimitError as exc:
        return limit_response(exc)

    async def stream():
        try:
            async with asyncio.timeout(SEARCH_TIMEOUT):
                async for kind, data in search(clean_profile(submission.profile)):
                    if await request.is_disconnected():
                        return
                    yield f'event: {kind}\ndata: {json.dumps(data)}\n\n'
        except LimitError as exc:
            yield 'event: error\ndata: ' + json.dumps({'message': exc.message, 'code': exc.code, 'retryAfter': exc.retry_after, 'resetsAt': limits.snapshot()['resetsAt']}) + '\n\n'
        except UPSTREAM_ERRORS:
            yield 'event: error\ndata: ' + json.dumps({'message': 'The search was interrupted. Please try again. Any records already retrieved remain available to review.'}) + '\n\n'
        finally:
            limits.release(client_key)
    return StreamingResponse(stream(), media_type='text/event-stream', headers={'Cache-Control': 'no-store', 'X-Accel-Buffering': 'no'})
