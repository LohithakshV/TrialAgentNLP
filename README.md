# TrialAgent

An educational clinical-research website with a natural-language search, real registry records, and beginner reading guides. React/Next.js + FastAPI; no database. Astra planned the website direction in `docs/website-direction-v2.md` and the parent implemented it.

## Run locally

```powershell
npm run dev
```

Open http://localhost:3000. Next.js and FastAPI bind to this computer on ports 3000 and 8000. Dependencies and Python `.venv` are project-local; no environment activation is needed. The Gemini key is read server-side from `.env`; restart the command after changing it. Never prefix the key with `NEXT_PUBLIC_`.

## Current experience

- A true-black, scrollable website with locally served **Fredoka** rounded headings and **Hanken Grotesk** body copy. No serif/default Inter treatment.
- Custom generated privacy, learning, and conversation symbols, plus generated research artwork. Assets live in `public/brand` and `public/art`; prompts/provenance are in `docs/brand-assets.md`.
- One natural-language composer occupies an independent, centered 880px stage with a filled surface, larger input type, and a visible field label. Supporting content uses a wider grid. The illustration is removed from the hero so the prompt is the main first-screen interaction. After it scrolls past the header, the same form becomes a compact floating box; the draft, consent, errors, and submission flow stay connected. Expanding it reveals the privacy notice and custom checkbox. A condition name can be enough; other details are optional.
- A spacious navigation header contracts into a rounded floating island as the page scrolls. The composer reserves its original height when it detaches so section headings do not jump behind the header.
- Filled cards, controls, and hover/selected states replace decorative hairline outlines. Typography and icon strokes have more weight; keyboard focus indicators remain visible.
- Three distinct steps: describe a scenario → check Gemini’s interpretation → explore recruiting registry records on `/results`.
- Supporting process cards, a four-card reading library linking directly to NIH/NCI/ClinicalTrials.gov, practical search guidance, and mobile navigation with Start a new search. The repeated closing search call-to-action is removed.
- Motion coordinates page/step transitions, card disclosures, and user-controlled process navigation. Reduced-motion preferences are respected.

## One model request per prepared query

1. After a required acknowledgment, `/api/extract` filters obvious identifiers and sends the fictional text to Gemini. **One structured response** classifies the request as `ready`, `needs_details`, or `off_topic`. A ready query includes condition, stage, biomarkers, city, and five general discussion questions. Unrelated or incomplete queries return HTTP 422 with an actionable code/message and never start a registry search. Their draft stays editable; unchanged rejected drafts cannot be re-submitted from the UI. No invented study records or eligibility decisions are requested.
2. The user reviews those details and can edit any field. Returning to an unchanged prompt reuses the prepared response without another model call. Editing the prompt invalidates it.
3. `/api/search` receives the confirmed profile and queries ClinicalTrials.gov v2 for up to eight recruiting records. **This stage makes zero Gemini calls**, including retries. Study overviews and eligibility text come from the registry and are labeled as source material, not AI summaries.
4. Questions from the original preparation are used only if the profile remains unchanged. Edited profiles get standard questions based on the corrected details, preventing stale guidance.

Study titles and “Read study details” open an in-app reader with registry facts, overview/criteria excerpts, and registry-listed contacts. Each card also offers the official record, source JSON, and a copyable NCT ID, so the external website is not the only route to the retrieved information. Public contacts are deduplicated and capped at six; selected-contact lists are labeled. This adds no Gemini request. A source-overlap checklist counts supplied details literally mentioned in the record. Mint checks mark structured registry facts; criteria mentions require review because they may describe exclusions. Missing wording and missing input remain distinct. This is not an eligibility percentage and does not reorder records. The JSON contract and limitations are in `docs/api-contract.md`.

Info disclosures close unrelated panels when opened and collapse after leaving the viewport. Nested eligibility text preserves its parent disclosure.

This replaces the previous labeled-line parser and batched AI study-summary approach. Gemini does not claim to have read the later registry records. Even a zero-result search consumes the initial preparation call; registry-only retries do not consume additional model requests. No automatic model retries occur.

Default model: `gemini-3.5-flash-lite`, configurable with `GEMINI_MODEL`. The key is never returned to the browser or printed by tests/smoke scripts.

## Limits

Defaults, configurable in `.env`:

```dotenv
GEMINI_DAILY_LIMIT=500
GEMINI_RPM_LIMIT=5
```

- Atomic reservation before a model request; 500 attempted calls per day with midnight Pacific reset, including daylight-saving changes. Failed attempts count conservatively.
- Five model calls per rolling minute, 15 incoming admission checks per client and 30 globally per minute, one active request per client, three concurrent operations globally, bounded request bodies.
- Daily quota applies to query preparation. Registry retrieval can complete after the final allowed model call. HTTP/SSE errors distinguish daily exhaustion, temporary provider limits, burst overload, duplicate operations, and busy service. HTTP 429 includes `Retry-After`; users see retry delay or localized reset time.
- Only counters, active slots, and expiring keyed hashes of client addresses are kept in server memory. No raw IP/clinical payload is retained by the limiter. Forwarded IP headers are not trusted.

These are **single-process prototype protections**, not distributed DDoS protection. Restart resets app counters; multiple workers/machines and other applications using the same Google project do not share them. Google enforces project quotas independently. Shared quotas and edge protection are required before public deployment. No deployment or DNS changes are configured.

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

`.env`, `.venv`, `node_modules`, and `.artifacts` are ignored by Git. `requirements.txt` lists runtime dependencies; the lock file also includes artwork conversion tools.

## Modules

- `app/components/research-session.js`: ephemeral session, preparation reuse, cancellation, stale-request protection.
- `research-workspace.js`, `research-composer.js`, `research-results.js`: primary composer, review, and separate scrollable results.
- `app/hooks/use-docked-composer.js`, `use-navigation-state.js`: preserved composer space and scroll-aware navigation.
- `website-sections.js`, `site-shell.js`, `ui.js`: editorial sections, navigation/footer, shared primitives.
- `app/lib/resources.mjs`: authoritative external reading links.
- `research-client.mjs`, `prepared-guide.mjs`: streaming/errors and prevention of stale questions.
- `backend/models.py`, `privacy.py`: schema validation and best-effort identifier filtering.
- `providers.py`, `research.py`: provider adapters, one-call preparation, registry-only search.
- `limits.py`, `main.py`: request budgets and HTTP/SSE admission.

## Privacy and use

**Fictional, non-sensitive details only.** This is not for clinical practice, diagnosis, treatment, or medical advice. No HIPAA or other compliance certification is claimed. A checkbox cannot override Google’s terms or establish legal compliance.

The app has no database, accounts, browser storage, analytics, cookies, or request-body logging. Notes/results remain in the open session until cleared or reloaded; this is not a forensic memory-erasure guarantee. The initial text goes to Google after the warning and acknowledgment. A best-effort filter can miss identifiers. Google may retain/process content under its own service-tier and regional terms. Hosts may retain operational metadata if deployed.

Only condition and city go to ClinicalTrials.gov. Records can be broad, incomplete, or stale. A registry search and recruiting status do not establish clinical suitability or available enrollment. Generated details/questions can be wrong. Only study teams determine eligibility. `/privacy` provides the full user-facing notice and Google terms/privacy links.

`Project_Context.md` preserves the original idea; this README supersedes its unsupported zero-PII, immediate-erasure, and compliance claims.

## Verification

```powershell
npm test
npm run build
# Optional: one real Gemini call using a fictional scenario, then registry retrieval.
.\.venv\Scripts\python.exe scripts/smoke_live.py
```

Tests cover consent before extraction, input bounds, generic errors, single-call preparation, no second model call during retrieval, reviewed-profile use, question freshness, source validation, empty results, quota races/resets/classification, and stream/error presentation. Browser checks cover desktop/mobile layout, custom fonts/artwork, process interaction, external guide destinations, and the real prompt-to-results flow, including submission from the detached composer. See `docs/navigation-composer-verification.md` for the latest UI checks.
