# Vercel deployment

This repository deploys as one Vercel project: Next.js serves the UI, and three top-level Python functions expose the FastAPI app. Vercel maps each file directly to its route; no rewrites are used.

## Architecture

```
Browser
  -> Next.js page
  -> /api/health, /api/extract, or /api/search
  -> api/health.py, api/extract.py, api/search.py (Python functions)
  -> backend.main
  -> Gemini + ClinicalTrials.gov
```

`api/health.py`, `api/extract.py`, and `api/search.py` each import the FastAPI `app`. Vercel maps the files to `/api/health`, `/api/extract`, and `/api/search` respectively. `next.config.mjs` proxies `/api/*` to FastAPI on `127.0.0.1:8000` only when not running on Vercel.

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

4. Deploy. Vercel installs `requirements.txt` and builds the three function files.
5. Check `/api/health`. `liveAvailable` must be `true`.
6. Run a fictional extraction, then a search. The search should stream progress and end with a `result` event containing trials, scores, and five questions.
7. Use the project's production domain. Deployment-specific URLs such as `project-abc123-team.vercel.app` are protected by Vercel Authentication by default.

## Configuration files

- `api/health.py`, `api/extract.py`, `api/search.py` import the FastAPI `app`.
- `vercel.json` configures the three functions. `excludeFiles` is a single glob string, matching the working TrialHacks configuration. Do not exclude `backend/` or `requirements.txt`.
- `.python-version` selects Python 3.12.
- `.env` is gitignored and is not uploaded. Use Vercel environment variables.

## Timeouts

- `/api/extract`: 60 seconds.
- `/api/search`: bounded internally to 240 seconds, but Vercel enforces the function's `maxDuration`.
- `/api/health`: 60 seconds.
- `vercel.json` sets `maxDuration: 60` for health and extraction, and `"max"` for search so the deployment uses the plan's maximum.

Provider retries are bounded. If the audit still fails, the search returns real registry records with `partial: true` and `matchScore: null` instead of failing the whole request.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `liveAvailable: false` | `GEMINI_API_KEY` is missing or empty in the deployed environment. |
| `/api/search` returns 403 | The request origin is not same-host, localhost, or in `ALLOWED_ORIGINS`. |
| `/api/*` returns 404 | Confirm all three files exist at the repository root: `api/health.py`, `api/extract.py`, and `api/search.py`. Do not route `/api/*` through `api/index.py`; Vercel maps one file to one route. |
| Search fails immediately | Confirm `requirements.txt` includes `fastapi`, `httpx`, `python-dotenv`, and `tzdata`. Open the Vercel function logs. |
| Audit always falls back | Check Gemini model access, daily quota, and function logs. A missing key affects extraction first. |
| Visitors see a Vercel login | Use the production domain rather than a deployment URL. If the production domain is protected, review Deployment Protection in the Vercel project settings. |
| Search is cut off near 60 seconds | The Vercel plan's maximum duration is 60 seconds. Reduce the number of trials or lower `SEARCH_TIMEOUT` so the API can return a clean error. |
| Everyone shares a quota bucket | Vercel may not provide a stable client address in every environment; limits are per instance and best-effort. Use shared storage for production-grade limiting. |

## Limitations

- In-memory counters reset on cold starts and are not shared across instances.
- The plan's maximum function duration may be lower than the internal 240-second search timeout.
- No database, accounts, or browser storage is used.
- Streaming is supported, but some proxies may buffer SSE. `X-Accel-Buffering: no` is set by the API.
