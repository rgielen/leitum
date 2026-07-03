#!/usr/bin/env python3
"""Outline the 'leitum' wordmark from Urbanist (variable) at wght=600 into an SVG path.

Emits src/wordmark.json: { d, bbox:[xMin,yMin,xMax,yMax], advance } in a coordinate
space where 1 em = 100 SVG units, baseline at y=0, y pointing down (ascenders < 0).

Requires the Urbanist variable font (https://fonts.google.com/specimen/Urbanist)
and fonttools:  uv run --with fonttools python src/outline_wordmark.py
"""
import json
import shutil
import subprocess
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

TEXT = "leitum"
WGHT = 600
TRACKING = 6  # extra spacing between glyphs, in font units (~0.6% em)
HERE = Path(__file__).resolve().parent


def find_font() -> str:
    candidates = [
        Path.home() / "Library/Fonts/Urbanist-VariableFont_wght.ttf",
        Path.home() / ".fonts/Urbanist-VariableFont_wght.ttf",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    if shutil.which("fc-match"):
        out = subprocess.check_output(["fc-match", "--format=%{file}", "Urbanist"], text=True).strip()
        if out and "urbanist" in out.lower():
            return out
    raise SystemExit("Urbanist variable font not found. Install from Google Fonts.")


f = TTFont(find_font())
instantiateVariableFont(f, {"wght": WGHT}, inplace=True)
upm = f["head"].unitsPerEm
cmap = f.getBestCmap()
gs = f.getGlyphSet()
hmtx = f["hmtx"]
scale = 100.0 / upm  # em -> 100 units

paths: list[str] = []
bounds = BoundsPen(gs)
x_cursor = 0.0  # font units

for ch in TEXT:
    gname = cmap[ord(ch)]
    matrix = (scale, 0, 0, -scale, x_cursor * scale, 0)  # scale + flip Y + shift X
    spen = SVGPathPen(gs)
    gs[gname].draw(TransformPen(spen, matrix))
    d = spen.getCommands()
    if d.strip():
        paths.append(d)
    gs[gname].draw(TransformPen(bounds, matrix))
    x_cursor += hmtx[gname][0] + TRACKING

xmin, ymin, xmax, ymax = bounds.bounds
out = {
    "d": " ".join(paths),
    "bbox": [round(xmin, 3), round(ymin, 3), round(xmax, 3), round(ymax, 3)],
    "advance": round((x_cursor - TRACKING) * scale, 3),
}
(HERE / "wordmark.json").write_text(json.dumps(out), encoding="utf-8")
print(json.dumps({"bbox": out["bbox"], "advance": out["advance"], "d_len": len(out["d"])}))
