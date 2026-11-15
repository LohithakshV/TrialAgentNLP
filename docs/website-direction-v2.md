# TrialAgent website direction v2

Final user refinements: natural-language input was explicitly selected. The user rejected serif/Newsreader typography and asked for flowing, rounded sans letters, so the implementation uses locally served Fredoka headings with Hanken Grotesk body copy. All page canvases are pure black. Additional generated symbols identify privacy in the header, learning resources, and conversations. The main input no longer offers a redundant manual-entry route. The preparation call is cached in the open session until the prompt changes.

This revision supersedes the sparse workspace direction. Planning only; implementation remains with the parent. Keep React/Next and the existing interactive session, `/results`, and privacy route. Astro is a reasonable content-site framework, but migrating now adds routing/session work without delivering the requested visual changes. Do not imply a migration happened.

## Website composition

Create a full, editorial website around the working search, with a 1200px content width, generous section spacing, structured cards, and a genuinely black canvas.

1. **Header:** original generated mark and live-text TrialAgent wordmark; anchors for How it works, Learn, and Resources; discreet Privacy link. Remove the “CLINICAL RESEARCH” eyebrow and decorative status dots. Mobile navigation remains accessible without crowding the logo.
2. **Hero and search:** two-column desktop composition. Left: “Find research. Know what to ask.” and two short supporting lines. Right: the real prompt composer in a substantial black card, with a generated research-path illustration behind or beside it. No fake chat conversation. Label “What would you like to research?”; helper “Include a condition and location. Add other details you know.” Show the sensitive-information warning and consent near the submit action. Remove the redundant manual-entry link. The review form is the place to edit structured details.
3. **How it works:** three connected, numbered cards: Describe your search → Check the details → Explore studies and questions. A generated abstract route motif connects the cards visually; real headings/text remain HTML. Each card gets one sentence, not a second tutorial.
4. **Start with the basics:** three substantial article cards: “What is a clinical trial?”, “What screening can tell you”, and “Questions to bring to a study team.” Each has an original small illustration, a two-sentence useful introduction, and a descriptive reading link. Use genuine content, not decorative cards or invented reading times.
5. **Research resources:** compact rows with organization, purpose, and external-link indicator. Start with [NIH: Clinical research basics](https://www.nih.gov/health-information/nih-clinical-research-trials-you/basics), covering participation, screening, and questions, and [ClinicalTrials.gov: How to search](https://clinicaltrials.gov/find-studies/how-to-search), the registry's search-help destination. The NIH content was inspected; the registry page opens but its full client-rendered body was not available to the text tool. Verify destination rendering before shipping. No government-affiliation implication.
6. **Footer:** wordmark, short research-only limitation, Privacy, sources, and Back to search. No redundant marketing slogan.

On mobile, show hero copy then composer; illustrations become smaller accents. Stack process and article cards. Preserve a rich page without delaying access to the working tool. Review replaces the composer in place; results remain a dedicated, scrollable route.

## Visual and motion system

Use canvas `#000000`, surfaces `#0B0B0B`/`#141414`, borders `#303030`, text `#F7F7F5`, secondary text `#B8B8B8`, mint `#B9F3D2`, and dark action text `#092016`. No navy tint. Use local Fredoka and Hanken Grotesk, 16px body, 14px supporting text, and 48–74px desktop hero type. Mint, coral, and lavender provide limited accents and geometric patterns. Render a coordinated generated illustration/symbol family; avoid hospital crosses, glowing globes, and rasterized UI text.

Reuse installed Motion. Animate section entrances once over 400ms with 16px translation; stagger card groups by 60ms, capped at 180ms. Use 220ms disclosure/step transitions and 160ms hover lift of 3px. A process connector may reveal once as its section enters view. No scroll hijacking, perpetual floating, or animated background noise. Reduced motion removes translation, stagger, connector drawing, and smooth scrolling. All content stays visible if motion fails.

## One-call natural-language contract

The current parser only understands labeled lines; it cannot honestly power a natural-language composer. Recommended replacement:

**Prompt + consent → one Gemini call returning profile and five general screening questions → editable review → registry fetch → source-based results.**

Move the existing daily/RPM quota reservation to the extraction call, and enforce consent server-side before it. Do not automatically retry model failures. `/api/search` must make zero Gemini calls. Retrieve `descriptionModule.briefSummary` alongside title, phase, sites, update date, and eligibility. Label it **Registry overview**, retain source links, render plain text, and offer expansion for long text. Never claim the model reviewed fetched studies or generated study-specific summaries.

Tradeoff: this gives the user real language understanding but replaces the current batched AI study summaries. Empty searches now consume the initial call. Registry-only retry can reuse the reviewed profile without another model call. If review changes the profile, replace potentially stale generated questions with the existing deterministic questions based on corrected details. Missing condition returns to editable review; model failure preserves input with explicit retry. Keep existing daily limits, duplicate-request protection, cancellation, no database, and no browser persistence.

Acceptance: arbitrary prose extracts real fields; one model call maximum per flow; corrected fields drive registry queries; no stale questions; consent precedes extraction; educational links work; all sections fit 360px/200% zoom; keyboard, reduced motion, quota exhaustion, cancellation, empty results, and source labeling remain correct.
