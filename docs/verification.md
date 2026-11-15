# Redesign verification — November 14, 2026

Historical verification for the first redesign. The current website and natural-language pipeline are verified in `website-v2-verification.md`; see README.md for the current data flow.

## Delivered

- Astra produced `redesign-plan.md` as a planning-only agent; the parent implemented the app. Final amendments at the top capture later user changes.
- Dark graphite/mint interface, locally served typography, generated logo and red warning SVG artwork, Motion step/result transitions, animated native disclosures, and reduced-motion CSS/Motion settings.
- Removed product sample data and sample/live controls. One task at a time: local draft → editable review/acknowledgment → `/results`.
- Dedicated `/results` and `/privacy` routes; no clinical values in route/query strings or browser persistence. Results have scroll-linked overview, studies, and questions sections.
- Modules separate session/request lifecycle, UI, results, local parsing, privacy filtering, provider calls, orchestration, and rate limits.
- At most one Gemini request per search, with all retrieved protocol criteria and the confirmed profile in structured input; the structured output supplies all summaries and five questions. Empty searches make zero model requests.
- Configurable 500/day model budget with Pacific reset, model RPM, burst limits, duplicate active-search protection, and bounded concurrency. Error UI distinguishes daily exhaustion and retryable limits.

## Evidence

- `npm test`: **21 Python tests + 6 JavaScript tests passed**. Covers atomic 500-call reservation under concurrent attempts, Pacific-day rollover, burst/duplicate/concurrency limits, Google quota classification, consent before outbound work, one-call batching, local parsing without a model, edited-profile use, source validation, empty/partial results, stream chunk boundaries, early termination, and user-visible retry/reset messages.
- `npm run build`: passed; generated `/`, `/privacy`, and `/results`.
- Genuine fictional live searches: retrieved **8 registry records**, generated summaries and **5 discussion questions** in one Gemini request. A transient run used fallback; a subsequent instrumented check confirmed eight summaries, five questions, all supplied IDs, and `partial=false`. No key or provider payload was printed.
- Browser verified labeled-note drafting, editable review, disabled search until acknowledgment, acknowledgment invalidation after edits, actual registry results on `/results`, expanded AI/source details and NCT links, scroll navigation, and questions.
- Browser verified a 390px entry/results layout and 360px results layout with no horizontal overflow. Narrow result titles wrap and study sources remain accessible.
- Browser verified cancel returns to review without losing the draft; client request identities reject stale events. Internal privacy navigation using client-side links preserves the session. Direct/reloaded results render a start-search action.
- Help dialog traps interaction, focuses Close, closes with Escape, and restores focus to its trigger. Review headings receive focus after animated navigation; icon-only new-search has an accessible name.
- Proof images are in ignored `.artifacts/`: `entry-mobile.jpg`, `results-desktop.jpg`, `questions-mobile.jpg`, and the final `trialagent-redesign.jpg`.

## Explicit limits

- Local drafting reads labeled lines; it does not perform semantic extraction of arbitrary clinical prose. Every field is editable, and unknown prose is left blank.
- Limits are memory-only, scoped to one Python process, and reset on restart. Google project quotas are independent. Shared deployment-wide quotas and DDoS defenses require hosting/edge infrastructure; none is claimed or deployed.
- Quota 500/day is an application setting, not a verified account allowance. No notes/results database or logging was introduced.
- Accessibility checks were targeted browser checks and implementation inspection, not a full assistive-technology certification.
- No medical/regulatory compliance guarantee, clinical eligibility determination, or deployment/subdomain DNS setup is claimed.
