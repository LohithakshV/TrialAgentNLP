# Navigation and persistent composer verification

Verified November 14, 2026, against the local Next.js/FastAPI demo.

## Latest visual refinement

The input now has an independent, centered stage instead of sharing a row with hero artwork. The inline form, supporting cards, checkbox, navigation controls, and hover states use filled surfaces without decorative hairline borders. Headings, body labels, actions, and icon strokes have stronger weights. A visible label identifies the textbox; keyboard focus is preserved.

- Desktop 1440 × 1000: composer width 880px, top 290.28px, bottom 704.11px; border width 0px; centered separately from the wider supporting sections.
- Mobile 390 × 854: complete empty form spans 282.56–786.41px with no horizontal overflow. Draft text can change the content height; the detachment placeholder retains the measured inline height.
- A fictional draft was typed, consent toggled, and the enabled preparation action verified without submitting a new model request. The single textbox retained the draft while floating. Privacy expansion and Escape collapse worked.
- Process-card hover and selection were exercised in the browser: filled selected background, 0px borders on all process and reading cards. The composer and action buttons also have 0px borders; decorative button inset shadows are removed.
- Production build passed after the final styling change. This pass changes presentation only; the regression-suite evidence below is from the preceding implementation pass.
- Current screenshots: `.artifacts/standalone-composer-desktop.jpg` and `.artifacts/standalone-composer-mobile.jpg`.

## Implemented behavior

- The natural-language prompt is visible on the first screen. Supporting content remains below it; the duplicate closing call-to-action is removed.
- The spacious header contracts to a centered rounded island on scroll, with custom logo and privacy mark, active section links, and a mobile menu.
- A single form and textarea switch between the original position and the floating composer. Draft, acknowledgment, busy state, errors, and cancel stay attached to the existing research session.
- Floating submission without consent opens the privacy disclosure and focuses its custom checkbox. No preparation request starts before acknowledgment.
- The floating form reserves the original inline height. ResizeObserver callbacks ignore the compact class, preventing a queued measurement from shrinking the placeholder and shifting page content.
- Hero art is contained in normal flow, including its caption. Reduced-motion and print styles are provided.

## Observed checks

- Desktop 1280 × 900: initial form top 301.94 px, bottom 630.52 px, height 328.58 px; main interaction fully visible.
- After navigating to Learning library: compact header bottom 80 px, section top 116.42 px, heading top 209.97 px, reserved composer height still 328.58 px. The heading clears the header with no detachment jump.
- Returning to the page top restores the inline form at the same 328.58 px height.
- Re-selecting the current section link after manually scrolling away now returns to that section. The mobile Learning library link was checked with the URL already at `/#learn`: section top 99.5 px, heading top 158.5 px, header bottom 68 px.
- Mobile 390 × 854: initial form top 308.22 px, bottom 734.17 px; no horizontal overflow; exactly one research textarea.
- Mobile floating composer stays inside the viewport. Typing into it retains the draft. Expanding privacy focuses the checkbox; Escape collapses the disclosure and returns focus to the textarea.
- Mobile compact floating bounds: top 732.5 px, bottom 842 px inside the 854 px viewport; reserved inline height remains 425.95 px.
- A fictional lung-cancer/Atlanta prompt submitted from the floating form reached the review screen and then eight real ClinicalTrials.gov records on `/results`, with five prepared discussion questions. Review removes the floating form. Registry retrieval retains the existing zero-additional-Gemini-call behavior.
- Production build passed; regression suite passed all 23 Python and 7 JavaScript tests. No new dependencies, database, deployment, or DNS changes in this pass.

## Preview artifacts

- `.artifacts/persistent-composer-home.jpg`
- `.artifacts/persistent-composer-docked.jpg`
- `.artifacts/persistent-composer-mobile.jpg`
- `.artifacts/persistent-composer-mobile-docked.jpg`

The navigation proportions reference the supplied DeepSeek Harness screenshots and its public page at https://www.deepseek.com/en/harness/. The TrialAgent identity, custom generated marks, typography, and true-black palette remain its own.
