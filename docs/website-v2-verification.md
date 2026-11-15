# Website v2 verification

This supersedes the earlier workspace verification for the current website revision.

## Implemented scope

- Natural-language prompt explicitly selected by the user; the old manual-entry shortcut is removed.
- One Gemini preparation call returns extracted details and five general questions. Review shows these details as a preview with optional inline editing. Registry retrieval and retries make no second model call.
- Pure black `rgb(0, 0, 0)` canvas; local rounded Fredoka headings and Hanken Grotesk body text. Newsreader and Inter are no longer imported or installed.
- Custom generated privacy, learning, and conversation symbols, plus generated research glass artwork. Small mint/coral/lavender accents and geometric patterns; no clinical-research dot/eyebrow.
- Fuller website: hero/search, interactive three-step cards, four authoritative learning links, practical search guidance, closing action, and full footer.
- Separate results route with readable source cards, expanded registry overviews, published criteria, source IDs/links, and a clearly attributed question guide.
- Mobile navigation with Escape dismissal and a reachable Start a new search action. Existing ephemeral session, consent, request cancellation, source validation, and quota protections remain.

## Evidence

- `npm test`: 23 Python + 7 JavaScript tests pass. These now cover consent before model extraction, short condition-name prompts, one model call across preparation/retrieval, zero model calls for registry-only retries, reviewed-profile use, and replacement of stale generated questions after edits.
- `npm run build`: passes for `/`, `/privacy`, `/results`.
- Live fictional natural-language smoke check: recognized condition and Atlanta without labeled fields, generated five questions, then retrieved eight records using the registry-only second stage.
- Browser fictional prose check: stage II prostate cancer, PSA 8.5 ng/mL, Seattle were correctly extracted into the review preview, followed by eight genuine registry records and five generated questions.
- Browser quota observation: complete prompt-to-results flow left 499/500 requests. Revisiting the unchanged prompt and continuing again still left 499/500, proving reuse in the running app.
- Browser computed styles: body background `rgb(0, 0, 0)`; heading font Fredoka Variable; body font Hanken Grotesk Variable. All generated images loaded.
- Browser desktop/mobile checks: source overviews expand; process cards change selected state and explanatory content; mobile navigation opens/closes; learning links point directly to authoritative pages in new tabs. At 390px, document width was 375px (no horizontal overflow).
- Final breakpoint checks: at 360px the document width was 345px; at 1280px it was 1265px. The 44px mobile menu button stayed within the header bounds. Start a new search was reachable through the mobile menu and reset the prompt/acknowledgment. The redundant manual-entry button count was zero.
- Final screenshots: `.artifacts/website-home-v2.jpg` and `.artifacts/website-library-v2.jpg`. Temporary viewport overrides were reset, and the clean home page was left available.
- The ClinicalTrials.gov search-help destination was opened in the browser and rendered the actual “How to Search for Clinical Studies” guide.

## Important limits

This remains a fictional-scenario educational prototype. The single-call NLP flow replaces AI study-specific summaries with registry-provided source overviews. Questions are general preparation, not eligibility decisions. The model has not read the later registry records. No account/database/browser persistence, deployment, distributed limiter, or DDoS certification is introduced. Counters are single-process and reset on restart, while Google's project quota remains independent.
