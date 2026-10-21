# Deck icons

Two families, reconciled into one system. See `kit.resolve_icon`.

| | |
| --- | --- |
| **Lucide** (`lucide.ttf`, `lucide-info.json`) | The house set. Same icons the product uses (`lucide-react`), so deck icons match app screenshots. ~2,000 icons. |
| **Material Symbols Rounded** (`MaterialSymbolsRounded.ttf`, `codepoints-rounded.txt`) | Gap filler only, for the abstract business vocabulary Lucide is thin on. Rendered at **wght 600** and **1.09x scale**, which is what makes it sit beside Lucide as one set rather than two. |

Rounded, not Outlined. Outlined next to Lucide reads as two different systems;
the rounded terminals are what Lucide's look depends on.

`svg/` holds the Lucide vector originals for Figma and for hand-editing in Slides.
Slides themselves carry PNGs, because python-pptx accepts only BMP/GIF/JPEG/PNG/TIFF/WMF.

Naming is forgiving: `circle-check` and `circle_check` both resolve.
