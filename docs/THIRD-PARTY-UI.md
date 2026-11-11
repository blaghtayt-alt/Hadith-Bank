# Reader UI dependencies

The reading-room interface uses locally vendored Radix color scales and SVG
icons. It retains the existing static HTML/JavaScript reader. No React runtime,
package registry, font service or CDN is required when opening the built reader.

## Pinned upstream assets

| Asset | Pinned source | Local files |
| --- | --- | --- |
| Radix Colors | `@radix-ui/colors` **3.0.0**, official npm release | `reader/vendor/radix-colors/{jade,sand,gold}.css` |
| Radix Icons | upstream commit `112af91ad275a63c3a29b0da2588342af74ef9bf`; upstream package metadata **1.3.2** | `reader/vendor/radix-icons/*.svg` |

The color archive was downloaded from
<https://registry.npmjs.org/@radix-ui/colors/-/colors-3.0.0.tgz> and verified
against the SHA-512 integrity recorded by the official registry metadata at
<https://registry.npmjs.org/@radix-ui%2fcolors/3.0.0>. Only the three light scales
and the upstream license were extracted. These files retain their exact
upstream bytes, including their sRGB fallbacks and display-P3 definitions.

The icons retain their exact upstream SVG bytes from
<https://github.com/radix-ui/icons/tree/112af91ad275a63c3a29b0da2588342af74ef9bf/packages/radix-icons/icons>.
The selected names are `reader`, `magnifying-glass`, `mixer-horizontal`,
`download`, `external-link`, `chevron-right`, `chevron-down`, `arrow-left`,
`arrow-right`, `cross-2`, `check`, `globe`, `file-text`, `reset` and `text`.
The React wrappers from the upstream package are not included or used.

`reader/vendor/manifest.json` records each file's byte count and SHA-256,
the release archive's integrity and SHA-256, and each icon's immutable source URL.

## Licenses and build behavior

Both asset sets are MIT licensed. Their original notices are retained in
`reader/vendor/radix-colors/LICENSE` and `reader/vendor/radix-icons/LICENSE`.
The builder also embeds both full notices in the reader's CSS, so a downloaded
standalone HTML file keeps its license notices.

`scripts/build_reader.py` verifies every vendored file against the manifest
before writing output. It combines the color scales with
`reader/reading-room.css` at the `__HADITH_UI_STYLES__` marker. It converts only
the outer wrapper of each SVG into a symbol, preserving the original path data,
then inserts the hidden inline sprite at `__HADITH_UI_ICONS__`. Each symbol has
an ID such as `icon-reader` and a `0 0 15 15` view box. Runtime references use
same-document fragments, for example `<use href="#icon-reader">`.

The application stylesheet must not import external resources. The build
rejects CSS imports, CSS URL references, unexpected SVG elements/attributes,
missing assets and checksum mismatches. Template substitutions happen in one
pass, so a marker appearing inside quoted source material is preserved as text.
No corpus, quotation, source reference or translation classification is changed.

To update these dependencies, select a specific upstream release or commit,
verify the release integrity, replace only the chosen asset files and license,
update the manifest, and review the resulting reader before publishing. Builds
never download dependencies or silently move to a newer upstream revision.

## Design reference

This selection follows the supplied UI-library transcript: use established
assets, customize the product's color and type system, and keep motion restrained.
Radix Colors supports plain CSS and assigns consistent roles to color scale
steps. These are useful foundations for the emerald, warm neutral and gold
reader theme. The final foreground/background combinations still require visual
and contrast checks.

- [Radix Colors installation](https://www.radix-ui.com/colors/docs/overview/installation)
- [Radix Colors usage in plain CSS](https://www.radix-ui.com/colors/docs/overview/usage)
- [Radix color scale roles](https://www.radix-ui.com/colors/docs/palette-composition/understanding-the-scale)
- [Radix Icons and SVG distribution](https://www.radix-ui.com/icons)
- [Pick UI Library guidance](https://github.com/emilkowalski/skills/blob/main/skills/pick-ui-library/SKILL.md)

Base UI, Radix Primitives, Sonner and cmdk target React and are not runtime
dependencies of this reader. Vaul's upstream repository currently identifies
itself as unmaintained. NumberFlow's documented limitations exclude non-Latin
digits and RTL locales; it is not used for this multilingual bank's counts.
