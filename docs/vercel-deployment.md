# Vercel deployment

This repository deploys as one Vercel project: Next.js serves the UI, and `api/index.py` exposes the FastAPI app as a Python function.

## Architecture

```
Browser
  → Next.js page
  → /api/extract or /api/search
  → api/index.py (Python function)
  → backend.main
  → Gemini + ClinicalTrials.gov
```

Production requests are routed by `vercel.json` from `/api/*` to `api/index.py`. `next.config.mjs` proxies `/api/*` to FastAPI on `127.0.0.1:8000` only when not running on Vercel.

## First deploy

Commit and push the deployment files to the branch connected to Vercel before importing or redeploying.

1. Import the GitHub repository into Vercel.
2. Keep the **Next.js** framework preset.
3. Add environment variables for Production, Preview, and Development:

```dotenv
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.5-flash-lite
GEMINI_DAILY_LIMIT=500
GEMINI_RPM_LIMIT=5
MAX_CONCURRENT_SEARCHES=20
ALLOWED_ORIGINS=
```

`ALLOWED_ORIGINS` is optional. Same-host requests and localhost are always allowed. Add comma-separated extra origins only if the frontend is served from a different domain.

4. Deploy. Vercel installs `requirements.txt`, builds `api/index.py`, and applies `vercel.json`.
5. Check `/api/health`. `liveAvailable` must be `true`.
6. Run a fictional extraction, then a search. The search should stream progress and end with a `result` event containing trials, scores, and five questions.

## Configuration files

- `api/index.py` imports the FastAPI `app`.
- `vercel.json` sets `maxDuration: 300` for the Python function and excludes build-only folders from the bundle. Do not exclude `backend/` or `requirements.txt`.
- `.python-version` selects Python 3.12.
- `.env` is gitignored and is not uploaded. Use Vercel environment variables.

## Timeouts

- `/api/extract`: 60 seconds.
- `/api/search`: 240 seconds.
- Vercel function limit: 300 seconds.

Provider retries are bounded. If the audit still fails, the search returns real registry records with `partial: true` and `matchScore: null` instead of failing the whole request.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `liveAvailable: false` | `GEMINI_API_KEY` is missing or empty in the deployed environment. |
| `/api/search` returns 403 | The request origin is not same-host, localhost, or in `ALLOWED_ORIGINS`. |
| `/api/*` returns 404 | The deployment did not detect `api/index.py`; confirm the file is at the repository root and `vercel.json` is committed. |
| Search fails immediately | Confirm `requirements.txt` includes `fastapi`, `httpx`, `python-dotenv`, and `tzdata`. Open the Vercel function logs. |
| Audit always falls back | Check Gemini model access, daily quota, and function logs. A missing key affects extraction first. |
| Visitors see a Vercel login | Disable Deployment Protection for the production domain in the Vercel project settings if the site should be public. |
| Everyone shares a quota bucket | Vercel may not provide a stable client address in every environment; limits are per instance and best-effort. Use shared storage for production-grade limiting. |

## Limitations

- In-memory counters reset on cold starts and are not shared across instances.
- The 300-second limit is the plan maximum; lower limits on some plans may require shortening `SEARCH_TIMEOUT`.
- No database, accounts, or browser storage is used.
- Streaming is supported, but some proxies may buffer SSE. `X-Accel-Buffering: no` is set by the API.
