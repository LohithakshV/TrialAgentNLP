# TrialAgent

An educational clinical-research website with a natural-language search, real registry records, an AI-assisted eligibility review, and beginner reading guides. React/Next.js + FastAPI; no database. Astra planned the website direction in `docs/website-direction-v2.md` and the parent implemented it.

## Run locally

```powershell
npm run dev
```

Open http://localhost:3000. Next.js and FastAPI bind to this computer on ports 3000 and 8000. Dependencies and Python `.venv` are project-local; no environment activation is needed. The Gemini key is read server-side from `.env`; restart the command after changing it. Never prefix the key with `NEXT_PUBLIC_`.

## Deploy to Vercel

This repository is configured as **one Vercel project**: Next.js serves the site and `api/index.py` exposes the same FastAPI app as a Python function.

1. Commit and push these changes, then import the GitHub repository into Vercel. Keep the **Next.js** framework preset. If the site should be public, leave Deployment Protection off for the production domain.
2. Add these Environment Variables for Production, Preview, and Development:
   - `GEMINI_API_KEY` (required for live searches)
   - `GEMINI_MODEL` (optional; default `gemini-3.5-flash-lite`)
   - `GEMINI_DAILY_LIMIT` and `GEMINI_RPM_LIMIT` (optional)
   - `MAX_CONCURRENT_SEARCHES` (optional; default `20`)
   - `ALLOWED_ORIGINS` (optional; comma-separated extra origins)
3. Deploy. Vercel installs the root `requirements.txt`, builds `api/index.py`, and routes `/api/*` to that function through `vercel.json`. `next.config.mjs` proxies to localhost only when not running on Vercel.
4. Verify the deployment with `/api/health`; `liveAvailable` should be `true`. Then run a fictional extract and search.

`vercel.json` sets a 300-second maximum for the Python function. `/api/extract` is bounded to 60 seconds and `/api/search` to 240 seconds. Streaming SSE works from the Python function; no separate backend service is required. Rate limits remain per instance and are best-effort, not distributed protection. See `docs/vercel-deployment.md` for troubleshooting.

## Current experience

- A true-black, scrollable website with locally served **Fredoka** rounded headings and **Hanken Grotesk** body copy. No serif/default Inter treatment.
- Custom generated privacy, learning, and conversation symbols, plus generated research artwork. Assets live in `public/brand` and `public/art`; prompts/provenance are in `docs/brand-assets.md`.
- One natural-language composer occupies an independent, centered 880px stage with a filled surface, larger input type, and a visible field label. Supporting content uses a wider grid. The illustration is removed from the hero so the prompt is the main first-screen interaction. After it scrolls past the header, the same form becomes a compact floating box; the draft, consent, errors, and submission flow stay connected. Expanding it reveals the privacy notice and custom checkbox. A condition name can be enough; other details are optional.
- A spacious navigation header contracts into a rounded floating island as the page scrolls. The composer reserves its original height when it detaches so section headings do not jump behind the header.
- Filled cards, controls, and hover/selected states replace decorative hairline outlines. Typography and icon strokes have more weight; keyboard focus indicators remain visible.
- Three distinct steps: describe a scenario → check Gemini’s interpretation → explore recruiting registry records and eligibility reviews on `/results`.
- Supporting process cards, a four-card reading library linking directly to NIH/NCI/ClinicalTrials.gov, practical search guidance, and mobile navigation with Start a new search. The repeated closing search call-to-action is removed.
- Motion coordinates page/step transitions, card disclosures, and user-controlled process navigation. Reduced-motion preferences are respected.

## How a search works

1. After a required acknowledgment, `/api/extract` sends the fictional text to Gemini. **One structured response** classifies the request as `ready`, `needs_details`, or `off_topic` and extracts condition, stage, biomarkers, and city. It does not write discussion questions. Unrelated or incomplete queries return HTTP 422 with an actionable code/message and never start a registry search. Their draft stays editable; unchanged rejected drafts cannot be re-submitted from the UI.
2. The user reviews those details and can edit any field. Returning to an unchanged prompt reuses the prepared response without another model call. Editing the prompt invalidates it.
3. `/api/search` receives the confirmed profile and queries ClinicalTrials.gov v2 for up to eight recruiting records. Stage and biomarkers are **not** registry filters.
4. The same request makes **one batched Agent 3 call** to Gemini. It compares the reviewed condition, stage, and biomarkers with each record’s published eligibility text and brief summary, then returns one evaluation per trial plus five discussion questions. Only reviewed profile fields and public registry text are sent; the original note, name, city, and contacts are not.
5. Each trial receives a 0–100 educational estimate, a tier (`strong`, `potential`, `low`), a plain-language summary, and criteria marked `met`, `unmet`, or `unknown`. Missing facts stay `unknown`; they are never converted into a mismatch.
6. If the audit fails after bounded retries, real registry records are still returned with `partial: true`, `matchScore: null`, and the standard five questions. Zero-result searches skip the audit entirely.

Study titles and “Read study details” open an in-app reader with registry facts, overview/criteria excerpts, and registry-listed contacts. Each card also offers the official record, source JSON, and a copyable NCT ID, so the external website is not the only route to the retrieved information. Public contacts are deduplicated and capped at six; selected-contact lists are labeled. A secondary source-overlap checklist counts supplied details literally mentioned in the record; it does not replace the eligibility review. The JSON contract and limitations are in `docs/api-contract.md`.

Info disclosures close unrelated panels when opened and collapse after leaving the viewport. Nested eligibility text preserves its parent disclosure.

Default model: `gemini-3.5-flash-lite`, configurable with `GEMINI_MODEL`. The key is never returned to the browser or printed by tests/smoke scripts.

## Limits

Defaults, configurable in `.env`:

```dotenv
GEMINI_DAILY_LIMIT=500
GEMINI_RPM_LIMIT=5
MAX_CONCURRENT_SEARCHES=20
ALLOWED_ORIGINS=
```

- Atomic reservation before every model attempt; 500 attempted calls per day with midnight Pacific reset, including daylight-saving changes. Failed attempts and bounded retries count conservatively.
- Five model calls per rolling minute, 15 incoming admission checks per client and 30 globally per minute, one active search per client, configurable concurrent operations globally, bounded request bodies.
- Daily quota applies to both extraction and audit. Registry retrieval can complete after the final allowed model call; an unavailable audit falls back to unscored records.
- HTTP/SSE errors distinguish daily exhaustion, temporary provider limits, burst overload, duplicate operations, and busy service. HTTP 429 includes `Retry-After`; users see retry delay or localized reset time.
- Only counters, active slots, and expiring keyed hashes of client addresses are kept in server memory. No raw IP/clinical payload is retained by the limiter. On Vercel the platform-provided client address header is used; elsewhere forwarded headers are not trusted.

These are **single-process prototype protections**, not distributed DDoS protection. Restart and cold starts reset app counters; multiple instances and other applications using the same Google project do not share them. Google enforces project quotas independently. Shared rate limiting needs KV/Upstash or an edge provider before public scale.

Google’s quota varies by account/model/project. The 500 value is this app's budget, not a verified account allowance. Check https://aistudio.google.com/rate-limit and https://ai.google.dev/gemini-api/docs/rate-limits.

## Fresh setup

Requires Node.js 20.9+ and Python 3.11+ already installed on the computer:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
npm ci
# Copy .env.example to .env only if .env does not already exist.
npm run dev
```

`.env`, `.venv`, `node_modules`, `.vercel`, and `.artifacts` are ignored by Git. `requirements.txt` lists runtime dependencies; the lock file also includes artwork conversion tools.

## Modules

- `app/components/research-session.js`: ephemeral session, prepared-profile reuse, cancellation, stale-request protection.
- `research-workspace.js`, `research-composer.js`, `research-results.js`: primary composer, review, eligibility review UI, and separate scrollable results.
- `app/hooks/use-docked-composer.js`, `use-navigation-state.js`: preserved composer space and scroll-aware navigation.
- `website-sections.js`, `site-shell.js`, `ui.js`: editorial sections, navigation/footer, shared primitives.
- `app/lib/resources.mjs`: authoritative external reading links.
- `research-client.mjs`: SSE parsing, HTTP errors, and retry presentation.
- `backend/models.py`, `privacy.py`: schema validation, evidence checklist, and profile normalization.
- `evaluation.py`: Agent 3 audit prompt, normalization, and tier recomputation.
- `providers.py`, `research.py`: Gemini/ClinicalTrials.gov adapters, bounded retries, and the two-call search pipeline.
- `limits.py`, `main.py`: request budgets and HTTP/SSE admission.
- `api/index.py`, `vercel.json`: Vercel Python-function entry point and deployment configuration.

## Privacy and use

**Fictional, non-sensitive details only.** This is not for clinical practice, diagnosis, treatment, or medical advice. No HIPAA or other compliance certification is claimed. A checkbox cannot override Google’s terms or establish legal compliance.

The app has no database, accounts, browser storage, analytics, cookies, or request-body logging. Notes/results remain in the open session until cleared or reloaded; this is not a forensic memory-erasure guarantee. The initial text goes to Google after the warning and acknowledgment. A second request sends the reviewed condition, stage, and biomarkers plus public registry eligibility text and summaries. The app does not detect or remove personal information; do not enter it. Google may retain/process content under its own service-tier and regional terms. Hosts may retain operational metadata if deployed.

Only condition and city go to ClinicalTrials.gov. Records can be broad, incomplete, or stale. A registry search, recruiting status, and match score do not establish clinical suitability or available enrollment. Generated details, questions, and scores can be wrong. Only study teams determine eligibility. `/privacy` provides the full user-facing notice and Google terms/privacy links.

`Project_Context.md` preserves the original idea; this README supersedes its unsupported zero-PII, immediate-erasure, and compliance claims.

## Verification

```powershell
npm test
npm run build
# Optional: one real Gemini extraction, then registry retrieval plus one audit.
.\.venv\Scripts\python.exe scripts/smoke_live.py
```

Tests cover consent before provider calls, input bounds, generic errors, extraction, the two-call pipeline, batched audit normalization, partial fallback, reviewed-profile use, source validation, empty results, quota races/resets/classification, and stream/error presentation. Browser checks cover desktop/mobile layout, custom fonts/artwork, process interaction, external guide destinations, and the real prompt-to-results flow. See `docs/navigation-composer-verification.md` for the latest UI checks.
