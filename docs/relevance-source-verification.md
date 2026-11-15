# Relevance, source evidence, and disclosure checks

Verified locally on November 14, 2026.

## Automated checks

- `npm test`: 31 Python tests and 10 JavaScript tests passed after the source-access follow-up.
- `npm run build`: production build passed.
- Tests cover actionable HTTP 422 classification errors, discarded model-invented profiles for rejected prompts, empty-condition fallback, missing/unknown status rejection, one-call preparation, source facts, and exclusion wording remaining unassessed.
- Existing tests continue to cover consent, input limits, identifiers, provider errors, quotas, reviewed-profile use, registry-only retrieval, SSE errors, and question freshness.
- `.env` and runtime example artifacts are ignored by Git. Temporary browser diagnostic logging was removed.

## Live checks

- A general question about randomized trials returned `422 needs_details`.
- An attempt to override instructions and request a pizza poem returned `422 off_topic`.
- A pizza-poem request in the browser showed the actionable notice, retained the draft, kept the textbox editable, focused the notice, and disabled unchanged resubmission. The example action cleared feedback and reset consent.
- A fictional non-small-cell lung-cancer query near Atlanta reached review and returned eight registry records with five questions. A fresh-load repeat also completed successfully.
- The live counter showed exactly one model request for each prepared prompt. Registry searches consumed no additional model requests. A registry-only HTTP check validated the new JSON source facts, search scope, and overlap statuses.
- An actual registry JSON example is saved at `.artifacts/source-result-example.json`; it contains a fictional profile and public registry material only.

## Browser checks

- Desktop 1440 × 1000 and mobile 390 × 854: source checklist, direct record links, source facts, and source excerpts render; no horizontal overflow. Mobile cards are 336px wide.
- Mint checks identify structured source facts. Stage/biomarker criteria mentions remain wording to review, and missing input differs from text not located.
- Opening another disclosure closes unrelated open panels. Opening nested eligibility text preserves its source-details parent.
- Scrolling expanded panels fully away collapses them. The same behavior was verified in the home-page help dropdowns.
- A section-navigation overshoot discovered during testing was corrected by collapsing before scheduling navigation against the settled layout. The Questions section landed at 189.73px, with its heading at 295.53px and the sticky navigation ending at 162px.
- Temporary viewport overrides were reset, and the demo tab was retained.

Current previews: `.artifacts/source-checklist-desktop.jpg` and `.artifacts/source-checklist-mobile.jpg`.

## Limits of the indicator

The overlap count is a deterministic count of literal mentions in inspected registry fields/excerpts. It is not a clinical eligibility score, synonym-aware comparison, assessment of inclusion/exclusion rules, or a suitability ranking. Source terminology and text outside the displayed excerpts can be missed. See `docs/api-contract.md` for the full contract and limitations.

## Source-access follow-up

The user reported an external ClinicalTrials.gov 403 after a testicular-torsion search. The registry returned three recruiting records with valid NCT IDs: NCT07554313, NCT07499024, and NCT05097820. For NCT07554313, the official HTML page and JSON endpoint returned HTTP 200; the record also loaded in the test browser. The user's exact 403 cause was not reproduced or established.

To remove the external page as the only reading path, titles and the primary action now open the in-app source-details panel. The existing public registry response supplies contacts, alongside a copy-ID action and official JSON/website links. This does not bypass an access restriction or add a model call.

Browser verification with the same condition returned three records. Both the primary reader action and title action kept navigation on localhost and opened source details. Opening the second reader closed the first. Registry contacts were visible, the copy action reported success, and the mobile layout at 390px had no horizontal overflow. Production build and all 41 tests passed. Previews: `.artifacts/torsion-study-reader.jpg` and `.artifacts/torsion-source-actions.jpg`.
