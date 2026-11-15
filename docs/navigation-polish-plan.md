# Navigation and artwork polish

Planning only. This agent owns this document; the parent owns implementation. The requested direction is a spacious top navigation that becomes a centered rounded island after scrolling. The supplied reference is a behavior/style reference, not a reason to copy its branding.

## Implementation direction

- Give the header a dedicated `navigation-shell` with constant height, sticky positioning, and stable stacking order. Place a centered `navigation-island` inside it; morph its maximum width, padding, background, border, radius, and shadow. Keep logo and text at their natural size rather than scaling the entire header. Suggested duration: 280–360ms, ease-out.
- Use a threshold with hysteresis, such as compact above 80px and expanded below 40px, so small scroll oscillations do not repeatedly trigger the morph. Initialize from actual scroll position, including restored pages. Use a passive listener and update React state only when the compact state changes.
- Consolidate old `.site-header` rules across `globals.css` and `website.css`. Their existing responsive height/padding rules and broad `.site-header nav` selector can override new island/menu styles. Dedicated selectors should own the final behavior, with no competing negative offsets.
- The island's compact width must fit all desktop links before the mobile breakpoint. Do not combine an attractive but too-small fixed width with nowrap labels. Switch to the mobile menu when content needs it, not only at a device label. On mobile, leave 12–16px viewport gutters and protect the logo, menu button, and 44px targets.
- Keep the shell's empty side regions from intercepting content clicks while the island is narrow: shell pointer-events can be none with pointer-events restored on the island/menu. Do not add a visually invisible full-width overlay.

## Content and accessibility

Use shared CSS variables for shell height, results subnav height, and anchor clearance. Existing `scroll-padding-top:95px`, `.results-nav` top offsets, and result scroll margins currently encode different assumptions. Establish one offset contract: ordinary section targets clear the shell plus breathing room; result section targets clear shell + subnav + breathing room. Avoid accidentally adding the full offset twice through both scroll-padding and scroll-margin.

The results subnav should sit below the shell throughout the morph, without a moving overlap. Keep the skip link above both. Native anchor navigation and keyboard focus must reveal headings and controls, including after direct hash navigation.

Keep the mobile menu a navigation disclosure, not an ARIA application menu. Preserve `aria-expanded`, `aria-controls`, descriptive button names, Escape-to-close, and focus return. Hidden menu links must leave the tab order. Close on link selection and pathname change; reset on desktop breakpoint entry. If focus was inside a menu being removed, move it to a visible equivalent or the toggle. Route changes should recompute header scroll state rather than retaining the previous page's state. Do not reset the research session merely by changing navigation appearance.

Active-section feedback should use one subtle underline/pill and `aria-current="location"`; route-level Privacy may use `aria-current="page"`. Clear home-section selection on other routes. Calculate section activation below the sticky header so two sections do not compete.

Style the existing native consent checkbox with `appearance:none` or a visual sibling. Retain the actual focusable input, associated label, required/checked/disabled semantics, Space behavior, and validation. Show a checkmark as well as color. Add visible focus and a forced-colors fallback; do not hide the input with `display:none`.

## Artwork

Replace negative-positioned, oversized hero imagery and `object-fit:cover` with a normal-flow figure, constrained responsive image using `object-fit:contain`, explicit dimensions/aspect ratio, and a separate `figcaption`. Remove conflicting mobile `left`, `top`, width-above-100%, and negative margins. Avoid `overflow:hidden` on the figure when it would clip the caption or focus rings. Keep decorative images empty-alt and preserve real text outside generated artwork. Logo assets need a sensible viewBox/canvas with consistent optical size; do not crop marks to disguise excessive internal padding.

## Acceptance

- At 320px, 360px, 768px, 1024px, and wide desktop: no horizontal overflow, clipped logo/text, overlapping buttons, cut-off artwork, or missing caption. Repeat at 200% zoom and short landscape height.
- Test top → threshold → deep scroll → top, rapid direction changes, restored scroll, and direct hashes. The page must not jump when the island changes shape.
- Test home, results with sticky subnav, privacy, and route transitions with the menu open. All target headings and focused controls remain visible.
- Test keyboard navigation, checkbox Space/required validation, mobile Escape/focus return, visible active state, and backdrop-filter fallback.
- Reduced motion disables morph transitions and smooth scrolling while preserving compact/expanded states. Print hides the entire shell and menu.
