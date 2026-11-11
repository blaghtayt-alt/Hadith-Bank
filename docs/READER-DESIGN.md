# Hadith Bank reading room

This reader uses an editorial layout with emerald actions, warm paper surfaces,
serif headings and restrained gold accents. The search field leads into a filter
column and a reading column. Below 861 CSS pixels, filters become a native
disclosure above the results. The layout also supports narrow 320-pixel screens.

## Components and dependencies

The existing reader is plain HTML and JavaScript and is also distributed as a
single downloadable file. Radix Colors 3.0.0 and selected Radix SVG icons provide
a consistent foundation without adding a JavaScript framework or runtime CDN.
Their exact sources, checksums and licenses are recorded in
[THIRD-PARTY-UI.md](THIRD-PARTY-UI.md) and `reader/vendor/manifest.json`.

`reader/reading-room.css` contains the product's styles. The builder verifies the
vendored assets and embeds the CSS, icon sprite, reader code and existing corpus
into the generated HTML. Source records are never interpreted as markup.

Native buttons, selects, checkboxes and disclosure elements retain their browser
keyboard behavior. The UI includes a skip link, visible focus, reduced-motion
styles, an announced result count and labels for icon controls.

## Reading and search

- Ctrl+K or Command+K focuses search; `/` does so when the user is not typing in
  another control. Escape clears the focused search field.
- Active query and filter chips remove one condition at a time. Dependent
  collection and source-edition choices are recalculated using the existing
  filtering rules.
- Standard or larger text affects narration text, including Arabic passages.
- Cards keep the language, collection/reference, translation origin, primary
  text and source name in view. Complete source and translation metadata sits
  inside a disclosure. Printing opens those source details temporarily.
- Available materials remain accessible from the filter column. Source and
  contribution links remain available in the footer at every width.
- Selection, pagination and complete-record JSON export retain their existing
  semantics. Resetting search or filters does not clear an export selection.

The source content, canonical identity, translation classifications, OCR review
policy, citation scopes and right-to-left handling retain the bank's existing
rules. A visual update is not a review or certification of religious content.

## Design reference

The supplied UI-library transcript emphasizes reusing appropriate foundations,
customizing typography/color/radius, choosing specialist components only for a
real interaction need, and avoiding excessive animation. This implementation
applies those principles to a reading application. It does not introduce React
components, command-palette dependencies or landing-page effects for controls
already served by semantic HTML.

Reference: <https://www.youtube.com/watch?v=zsCGS-Yzjnw>.
