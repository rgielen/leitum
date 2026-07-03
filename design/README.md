# leitum brand assets

Visual identity for **leitum**. Concept: **Detour** — a bold path leaves the
direct route (the dimmed, discontinued line to the default endpoint) and
*reroutes*. It mirrors what leitum does: intercept the default path to the
Anthropic API and send the request to a chosen provider.

![leitum logo — dark and light](png/leitum-lockup-1024.png)

## Colors

| Token            | Hex        | Use                                             |
| ---------------- | ---------- | ----------------------------------------------- |
| Accent (Indigo)  | `#8B93FF`  | The rerouted path, arrowhead, highlights        |
| Ink — dark bg    | `#E6EDF3`  | Mark + wordmark on dark backgrounds             |
| Ink — light bg   | `#1C2230`  | Mark + wordmark on light backgrounds            |
| Canvas / Tile    | `#0D1117`  | App-icon tile, dark backdrops                   |

The mark's main stroke uses a gradient from **Ink → Accent** along the reroute,
to suggest the hand-off. The dimmed "ghost" route is Ink at low opacity.

## Typeface

**Urbanist SemiBold (600)** — geometric, open-source ([OFL], Google Fonts).
In the shipped logo files the wordmark is **converted to outlines**, so no font
needs to be installed to render it correctly anywhere.

- Wordmark / UI pairing: Urbanist.
- Code / terminal contexts (e.g. the demo video): JetBrains Mono.

[OFL]: https://fonts.google.com/specimen/Urbanist

## Files

```
design/
├── logo/
│   ├── leitum-mark.svg          # mark only            (dark bg)
│   ├── leitum-mark-light.svg    # mark only            (light bg)
│   ├── leitum-mark-mono.svg     # mark, single-color   (currentColor)
│   ├── leitum-lockup.svg        # mark + wordmark      (dark bg)
│   ├── leitum-lockup-light.svg  # mark + wordmark      (light bg)
│   ├── leitum-lockup-mono.svg   # mark + wordmark      (currentColor)
│   ├── leitum-wordmark.svg      # wordmark only        (dark bg)
│   ├── leitum-wordmark-light.svg
│   └── leitum-wordmark-mono.svg
├── favicon/
│   ├── icon.svg                 # self-contained app-icon tile (recommended favicon)
│   └── favicon.svg              # bare mark (transparent)
├── png/                         # rasterized exports (mark, lockup, wordmark, icon 32–512)
└── src/                         # build scripts to regenerate everything
```

SVG is the master format. PNGs in `png/` are convenience exports.

### Variants

- **dark** (default, no suffix): light ink — use on dark backgrounds.
- **light** (`-light`): dark ink — use on light backgrounds.
- **mono** (`-mono`): uses `currentColor` for every element; set the color via
  CSS (`color: …`) or the SVG `color` attribute. For single-color contexts
  (print, embroidery, watermarks).

## Usage

- **Clear space:** keep free space of at least 25% of the mark height around the
  logo (≈ 24px when the mark is 96px).
- **Minimum size:** mark ≥ 24px; lockup ≥ 120px wide.
- **Background pairing:** dark variant on dark, light variant on light. Never put
  the dark variant on a light background or vice versa; use `-mono` if a single
  color is required.
- **Don't:** recolor the accent, stretch or skew, rotate, add shadows/outlines,
  or reconstruct the wordmark in a different font.

### Favicon

```html
<link rel="icon" type="image/svg+xml" href="favicon/icon.svg" />
<link rel="apple-touch-icon" href="png/icon-180.png" />
```

## Regenerating

The assets are generated from source in `src/`:

1. `outline_wordmark.py` — instantiates Urbanist at wght=600 and outlines
   "leitum" to an SVG path (`wordmark.json`). Requires the Urbanist variable
   font and `fonttools` (`uv run --with fonttools python src/outline_wordmark.py`).
2. `generate_assets.py` — emits every SVG in `logo/` and `favicon/` from a single
   source of truth (`python src/generate_assets.py`).
3. PNGs are rendered with `rsvg-convert` (librsvg).
