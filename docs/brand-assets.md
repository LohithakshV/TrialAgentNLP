# TrialAgent brand assets

## Website expansion assets

Built-in imagegen generated `public/art/research-glass.png` (served as `.webp`) and `public/brand/learning.png`, `privacy.png`, and `questions.png` (served as automatically traced SVGs). All assets are project-local. The privacy mark appears in navigation; the book and conversation marks identify learning/process sections. `scripts/trace_brand.py` preserves visible silhouettes and discards transparent-pixel noise during vectorization.

### researchVisual

Use case: stylized-concept. Asset: premium editorial illustration for a pure black healthcare research website, wide 3:2 composition. A sculptural group of three translucent frosted glass document tiles standing upright at different depths, with a satin silver magnifying lens leaning against the front tile and a very fine mint-colored route connecting two small nodes inside one tile. Highly controlled studio product photography mixed with minimalist scientific art direction. Mostly grayscale, restrained pale mint glass edges. Background absolutely solid black #000000 fading seamlessly into a black website. Grounded, coherent geometry, soft directional rim light, plenty of negative space on left quarter, object group on right half. No text, no letters, no numbers, no brand logo, no sparkle, no floating pills, no purple, no blue light, no stock doctors, no medical cross. Precise elegant tangible objects, understated depth.

### learnVisual

Use case: logo-brand. Asset: one original standalone graphic symbol for the TrialAgent learning library. A refined open book that also suggests two gently spreading leaves, made of two continuous interlocking rounded bands. Flat solid pale mint #BCECD5. Optically balanced at small sizes, simple geometric silhouette. Square canvas, centered symbol, 12 percent clear space. Actually transparent background. No words, no letters, no numbers, no medical cross, no shine, no shadow, no gradients, no extra symbols. Sophisticated custom brand symbol, vector-style.

### privacySymbol

Use case: logo-brand. Asset: custom privacy navigation symbol for TrialAgent. One elegant original shield built from two interlocking curved bands with a tiny protected circular point in its center. Human, serene, simple enough to read at 20 pixels, rounded geometric silhouette. Flat solid ivory #EDEDE6, square canvas, centered, 12 percent margins. Genuinely transparent background. No text, no letters, no numbers, no check mark, no medical cross, no gradients, no shadows, no glow, no sketch texture. A quiet high-end web brand pictogram, vector-style.

### questionsSymbol

Use case: logo-brand. Asset: custom section symbol for questions and conversations on a serene healthcare research website. Two softly rounded interlocking speech bubbles shaped as one flowing open loop, with a single small circular point. Original very simple geometric silhouette, optically balanced at 24 pixels. Flat solid pale mint #BCECD5, square canvas, centered with 12 percent margins. Genuinely transparent background. No text, no letters, no numbers, no medical cross, no gradient, no shading, no shadow, no texture. Refined vector-style brand pictogram.


Generated using the built-in imagegen tool, then automatically traced into compact SVG silhouettes. No logo paths were hand-drawn in code. PNG originals are kept alongside the SVGs in `public/brand/`.

- `trialagent-mark.svg` / `.png`: original mint research-route / protective-leaf mark.
- `warning.svg` / `.png`: original coral warning triangle.
- `scripts/trace_brand.py`: reproducible artwork-to-vector conversion; development-only Pillow and vtracer dependencies are recorded in the local environment lock file.

Prompts:

## Brand mark

Use case: logo-brand. Asset: standalone symbol for TrialAgent, an independent healthcare research discovery web app. Create one original refined minimal vector-style brand mark, no text, no letters: two interlocking rounded paths suggesting a forward route and an open protective leaf, with one small circular endpoint. Calm clinical confidence, Swiss identity design, optically balanced, simple silhouette readable at 24px. Flat solid pale mint #BCECD5 on genuinely transparent background. Square canvas, symbol large and centered with only 10 percent clear space. No medical cross, no red cross, no snake, no heart/ECG, no four-point AI sparkle, no gradients, no shadows, no mockup, no decorative backdrop. Deliver clean logo artwork with real alpha transparency.

## Warning mark

Use case: logo-brand. Asset: small standalone UI warning symbol, transparent background. Single simple coral red outline equilateral warning triangle with rounded corners and a centered coral exclamation mark. Flat vector-style uniform thick stroke, geometric optical balance, readable at 20 pixels, centered square canvas with 12 percent margins. Exact color #F29A9A. No text, no label, no shadow, no glow, no gradient, no texture, no border outside the triangle, no backdrop. Actual alpha transparency.
