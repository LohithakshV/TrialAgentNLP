# TrialAgent redesign plan

## Final implementation amendments

The user subsequently requested a standalone scrollable results page and a single Gemini request per search, plus request limits. These changes supersede the original extraction contract below:

- `/api/extract` now drafts **locally** from labeled condition/diagnosis, stage, biomarker, and city lines. Unknown prose is left blank for explicit manual review. No model call is made here, and no AI extraction claim is shown.
- The review checkbox precedes all outbound registry/model processing. Only the confirmed profile is sent onward; the original note stays local.
- `/api/search` retrieves registry records, then makes one batched structured Gemini call for all summaries and five discussion questions. Empty searches use zero Gemini calls.
- `/results` is a separate route, with an overview section followed by scroll-linked study and question sections. `/privacy` explains data flow. No deployed subdomains or DNS changes were requested/configured.
- The app enforces a configurable 500-call daily budget, midnight Pacific reset, model RPM cap, client/global burst caps, duplicate active-search rejection, and bounded concurrency. Counters live in one Python process and reset on restart; a distributed/global quota across processes or DDoS protection requires hosting controls. No database is added.
- The input includes generated red warning artwork and a clear personal-information warning. Logo and warning assets are generated artwork traced to SVG rather than hand-drawn code.

Planning only. Based on the current repository; no product code changed. The Gemini and America.gov references are interpreted as the user's preference for direct interactions and clear information hierarchy, not as sites inspected during this task.

## Product direction

Build a focused research workspace, not a landing page. A useful promise is **“Find studies. Prepare better questions.”** TrialAgent helps a person organize a condition, discover registry records, and prepare for screening conversations. The current code cannot establish eligibility, rank clinical suitability, recommend treatment, or guarantee available local sites. Preserve that distinction in the interface without repeating a disclaimer on every card.

Replace the large editorial hero, decorative orbit, repeated explanatory panels, sample selector, demo/live switch, and “NLP” suffix. The initial screen should contain the TrialAgent wordmark, one short heading, one task surface, and one obvious next action. No fabricated studies or default examples. A service outage must never substitute fictional results.

The existing project is explicitly an educational prototype restricted to non-sensitive input. A visual redesign does not change that operational scope. Keep a short input warning and accessible full privacy details; do not imply clinical approval or certified privacy protection.

## Critical data-flow decision

The existing `/api/match` calls Gemini to extract a profile before searching. Therefore **AI extraction cannot happen before consent to sending text to Google**. A progress label or profile preview does not fix that ordering.

Selected implementation, confirmed by the parent: notes → concise Google disclosure and explicit consent → `/api/extract` with Gemini → editable profile review → `/api/search` with the confirmed profile and streaming registry/summary progress → results. Consent precedes the first outbound call; profile review precedes registry search. Condition is required; optional fields may remain unknown. Call the review “Check your details,” not “AI verified.”

Do not send the note through extraction again after the user corrects its fields. `/api/search` must use those corrections directly. Remove demo/sample product modes. No local parser is required; manual editing belongs in review and extraction-error recovery.

## Guided interaction

Use a single mounted workspace with an explicit state machine. Only the current step is visible. A quiet progress row reads **Details · Review · Search**; privacy appears within Details before extraction, and results belong to Search. Completed steps can be revisited; future steps are not clickable.

| State | Content and primary action | Secondary behavior |
| --- | --- | --- |
| Details | Heading “Find clinical research”; short supporting sentence and a clearly labeled notes field with neutral guidance, not sample content. **Review details** leads to the compact consent disclosure before extraction. | Short notice: “Use non-sensitive details. Leave out names and contact information.” Privacy link. Require a meaningful condition; optional fields show “Not provided,” never guessed values. |
| Review | Heading “Check your details”; editable condition, stage, biomarkers, city; small note that these details guide a registry search. **Search studies** | **Back** retains values. Distinguish omitted fields from negative findings. Editing input invalidates any old results and prior consent tied to those details. |
| Privacy | Shown before extraction: heading “Before we continue”; concise list of actual recipients and purpose; unchecked consent; **Extract details** | Explain that notes first go to Google for extraction; after review, condition/city go to ClinicalTrials.gov and profile/protocol text go to Google for summaries. Link full policy. Say “No app database” rather than “Private” or “Never stored.” **Back** retains edits. |
| Searching | Heading “Searching registry records”; compact live status and honest completed/active steps; **Cancel search** | Use backend events, not timers or made-up percentages. Cancellation returns to Review with input intact. Cancel the browser request and stop further backend stages when disconnection is observed. Already transmitted provider requests cannot be recalled. |
| Results | Heading “Research records” with count; compact query summary and **Edit details**. Study cards lead with title, then location, phase, registry status. **View details** expands summary, source date, NCT ID, and **Open registry record**. | One page notice: “Search results are not confirmed eligibility matches.” Clearly label generated summaries. Questions appear in a separate expandable panel, not a permanent text-heavy sidebar. Print only visible research context, sources, and questions. |

Only use “Listed as recruiting” for confirmed registry-reported status. Do not imply location text proves that a nearby site is recruiting. No match scores, green eligibility checkmarks, “best trial,” or synthetic confidence figures.

On desktop, keep entry/review centered at roughly 680px; results can expand to 1120px with the records and a compact questions panel. At mobile widths, use one column and inline disclosures rather than a side drawer. A persistent footer action may be used only if safe-area padding and content clearance prevent obscured fields.

## Back, cancellation, and recovery

- **Back:** preserve user-entered values. Do not repeat outbound requests simply because a step is revisited. Use explicit buttons; if browser history is supported, keep sensitive values out of URLs and history state.
- **Clear session:** abort the current request; invalidate its request ID; reset profile, notes, consent, results, errors, and expanded records. Late events from an old request must not repopulate the screen. No localStorage, sessionStorage, database, or accounts.
- **No results:** “No records found for this search.” Offer **Edit condition or location**. Explain in one sentence that this search does not cover every possible study. Do not automatically broaden a condition or remove geography without the user choosing it.
- **Summary failure:** retain fetched registry records, source links, and standard screening questions. Show a small “Summaries unavailable” notice with manual-review guidance.
- **Network/stream failure:** retain the profile, show a plain error near the task surface, and provide **Try again** and **Edit details**. A stream ending before a result is an error. Do not expose provider payloads or configuration details.
- **Service unavailable:** allow local drafting and review; disable the outbound action with a visible explanation. Key configuration belongs in README/developer output, not the main user flow.

## Visual system

Use graphite and deep navy surfaces, warm white text, and a restrained pale-teal action color. Avoid purple gradients, glowing borders, floating health badges, animated backgrounds, and oversized reassurance copy.

| Token | Starting value |
| --- | --- |
| Canvas | `#0B1118` |
| Main surface / raised surface | `#121B25` / `#192432` |
| Subtle border / control border | `#2B3948` / `#64788D` |
| Primary text / secondary text | `#F2F5F8` / `#AEBBC9` |
| Action fill / action text | `#B6E4D5` / `#102820` |
| Focus ring | `#93C5FD` |
| Error text | `#FDA4AF` |
| Radius / spacing | 12px surface, 8px control; 4/8/12/16/24/32/48px spacing |

Validate contrast in the rendered combinations. Subtle surface borders must not be the sole boundary for essential form controls. Body and input text 16px, supporting text 14px minimum; headings 32–40px desktop and 28–32px mobile. Use an available sans-serif stack; no new remote font dependency is required. Keep lines short and actions explicit. Use the existing Lucide package sparingly.

The parent generated mint leaf/route logo artwork in `public/brand`; use it to implement this brief: a compact, original abstract research/navigation mark, no medical certification symbols, readable at 24px on dark backgrounds. Render the image beside live-text “TrialAgent” so raster lettering does not carry the brand. Use empty alt text when the adjacent wordmark conveys the same information. Provide fixed dimensions to prevent layout shift.

## Motion

At initial inspection, package files contained no animation library. The parent subsequently installed Motion, Radix, Tailwind, and local Inter; reuse those project-local dependencies. Use **Motion** for React and verify its installed API documentation during implementation.

- Step change: opacity 0→1 and vertical translation 8px→0 over 180–220ms, ease-out; outgoing step exits in 100ms. Avoid large horizontal slides and spring overshoot.
- Disclosure: brief opacity/height transition, 160ms; move keyboard focus only when navigation requires it.
- First results: optional 30ms stagger, capped at 150ms total. No repeated animation on every stream event.
- Buttons: 120ms color/border transition; optional 1px press movement. No looping hero motion, shimmer, or animated gradients.
- Reduced motion: remove translation, stagger, and layout animation; use instant state changes or a short opacity change. Replace a rotating loader with static text/status. Functionality and progress announcements must be identical.

## Implementation ownership and sequence

This planning agent owns only `docs/redesign-plan.md`. The parent owns all implementation and may consolidate small modules. No database migration or persistence work is needed.

| Files/modules | Responsibility |
| --- | --- |
| `app/page.js`, `app/layout.js` | Minimal page composition, metadata and branding. Keep interactive state within the client workspace boundary. |
| `app/components/research-workspace.js` | Explicit step state, navigation, consent invalidation, session reset, focus transitions, request identity. |
| `app/components/profile-form.js` | Accessible local entry and editable review; explicit optional fields and bounded values. |
| `app/components/privacy-panel.js` | Consent and truthful data-flow disclosure; accessible full-details dialog if used. |
| `app/components/search-progress.js` | Real progress events, live region, cancel action. |
| `app/components/research-results.js` | Result list, record details, no-results/partial states, screening questions, print behavior. |
| `app/lib/research-client.js` | Fetch/SSE handling, AbortController, robust chunk parsing, terminal-event requirements, sanitized client errors. |
| `app/lib/profile.js` | Client normalization/validation of reviewed fields; no local clinical parsing, secret, or external call. |
| `app/globals.css`, `public/` logo assets | Tokens, responsive layout, focus styles, reduced motion, print styles, generated logo. |
| `backend/main.py` | Separate `/api/extract` from `/api/search`; validate consent before any external call and validate the confirmed search profile; keep provider integration/source validation; remove sample mode. |
| `backend/tests/test_main.py`, `scripts/test.mjs`, focused frontend tests | Protect consent, request bounds, edited-profile use, stream/cancel races, partial and empty results. |
| `README.md` | Updated user flow, real data flow and limitations, setup kept out of UI. |

Sequence: (1) choose extraction/consent contract; (2) implement and test backend contract; (3) implement local step flow and request lifecycle; (4) apply visual system and logo; (5) integrate real progress/results; (6) validate responsive and accessible behavior. Installed Next documentation read: `use-client.md` and `05-server-and-client-components.md`. Read additional local guides relevant to APIs used during implementation.

## Acceptance checks

- First viewport presents one task and next action, with no sample buttons, example studies, mode toggle, or NLP suffix.
- Review allows correction of every extracted/drafted field. The exact corrected profile drives registry queries and summaries; no hidden re-extraction overwrites it.
- Inspect network behavior: no external clinical-data request before relevant consent. Reject missing consent server-side. No note/profile values in URLs, logs, browser persistence, or error payloads.
- Exercise happy path, empty results, summary-only failure, service unavailable, malformed/early-closed stream, repeated clicks, cancel/retry, and clear while a request is active.
- Verify keyboard-only traversal; visible focus; labeled fields; focused heading on step changes; polite progress announcements; error association; Escape/focus return and containment for any dialog.
- Check 360px mobile, tablet, desktop, and 200% zoom: no horizontal overflow, clipped titles, unreachable actions, obscured fields, or tiny disclosure text. Touch targets at least 44px.
- Check reduced motion and printed output. All registry sources remain usable. No interface claim implies eligibility, current local availability, compliance, or guaranteed erasure.
- Run `npm test` and `npm run build`; exercise the browser with mocked edge states and a genuine permitted service request when configured. Do not report a real integration as verified from mocks alone.

