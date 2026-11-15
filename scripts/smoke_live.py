"""Explicit live check, using a fictional scenario. Never prints keys/provider bodies."""
import asyncio
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
import httpx
from backend.research import prepare, search
from backend.models import Profile

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

async def main():
    try:
        prepared = await prepare('For a fictional research exercise, I want to explore non-small cell lung cancer studies around Atlanta. The stage is IIIA, with an EGFR exon 19 deletion.')
        profile = Profile(**prepared.profile.model_dump())
        print(json.dumps({'naturalLanguageUnderstood': bool(profile.condition), 'cityUnderstood': profile.city.lower() == 'atlanta', 'generatedQuestions': len(prepared.guide)}), flush=True)
        async for kind, data in search(profile):
            if kind == 'result':
                print(json.dumps({'registryRecords': len(data['trials']), 'registryOnlySecondStage': True}), flush=True)
    except httpx.HTTPStatusError as exc:
        print(json.dumps({'status': exc.response.status_code, 'provider': exc.request.url.host}), flush=True)
        sys.exit(1)
    except Exception as exc:
        print('Live check failed: ' + type(exc).__name__, flush=True)
        sys.exit(1)

asyncio.run(main())
