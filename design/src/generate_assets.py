#!/usr/bin/env python3
"""Generate the full leitum logo asset set (Detour concept).

Single source of truth for every SVG in design/logo/ and design/favicon/.
Run after src/outline_wordmark.py:  python src/generate_assets.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent   # design/src
OUT = HERE.parent                        # design
(OUT / "logo").mkdir(parents=True, exist_ok=True)
(OUT / "favicon").mkdir(parents=True, exist_ok=True)
(OUT / "png").mkdir(parents=True, exist_ok=True)

WORD = json.loads((HERE / "wordmark.json").read_text())
WD, WBB = WORD["d"], WORD["bbox"]  # bbox: xMin,yMin,xMax,yMax in em=100 space, baseline y=0

ACCENT = "#8B93FF"

VARIANTS = {
    "dark":  dict(ghost="#E6EDF3", ghost_op=0.16, g0="#E6EDF3", g1=ACCENT, accent=ACCENT, word="#E6EDF3", grad=True),
    "light": dict(ghost="#1C2230", ghost_op=0.20, g0="#1C2230", g1=ACCENT, accent=ACCENT, word="#1C2230", grad=True),
    "mono":  dict(ghost="currentColor", ghost_op=0.30, g0=None, g1=None, accent="currentColor", word="currentColor", grad=False),
}


def mark_body(v: str, gid: str) -> str:
    p = VARIANTS[v]
    bold = f"url(#{gid})" if p["grad"] else p["accent"]
    return f'''  <line x1="14" y1="70" x2="86" y2="70" stroke="{p['ghost']}" stroke-opacity="{p['ghost_op']}"
        stroke-width="8" stroke-linecap="round" stroke-dasharray="0.5 15"/>
  <circle cx="86" cy="70" r="5" fill="none" stroke="{p['ghost']}" stroke-opacity="{p['ghost_op']}" stroke-width="4"/>
  <path d="M14 70 H40 V34 H78" fill="none" stroke="{bold}" stroke-width="11"
        stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M69 24 L82 34 L69 44" fill="none" stroke="{p['accent']}" stroke-width="11"
        stroke-linecap="round" stroke-linejoin="round"/>'''


def grad_def(v: str, gid: str) -> str:
    p = VARIANTS[v]
    if not p["grad"]:
        return ""
    return (f'  <defs><linearGradient id="{gid}" x1="0" y1="1" x2="1" y2="0">'
            f'<stop offset="0" stop-color="{p["g0"]}"/>'
            f'<stop offset="1" stop-color="{p["g1"]}"/></linearGradient></defs>\n')


HEAD = '<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="{vb}">'


def write(path: Path, content: str) -> None:
    path.write_text(content + "\n", encoding="utf-8")
    print("wrote", path.relative_to(OUT.parent))


def suffix(v: str) -> str:
    return "" if v == "dark" else f"-{v}"


# 1) mark only
for v in VARIANTS:
    gid = f"lg-{v}"
    svg = HEAD.format(w=96, h=96, vb="0 0 96 96") + "\n" + grad_def(v, gid) + mark_body(v, gid) + "\n</svg>"
    write(OUT / "logo" / f"leitum-mark{suffix(v)}.svg", svg)

# 3) wordmark only
pad = 10
vb = f"{WBB[0]-pad:.2f} {WBB[1]-pad:.2f} {WBB[2]-WBB[0]+2*pad:.2f} {WBB[3]-WBB[1]+2*pad:.2f}"
ww, wh = WBB[2] - WBB[0] + 2 * pad, WBB[3] - WBB[1] + 2 * pad
for v in VARIANTS:
    svg = HEAD.format(w=round(ww * 2), h=round(wh * 2), vb=vb) + "\n" + f'  <path d="{WD}" fill="{VARIANTS[v]["word"]}"/>\n</svg>'
    write(OUT / "logo" / f"leitum-wordmark{suffix(v)}.svg", svg)

# 2) lockup: mark + wordmark
K, GAP, RPAD = 0.60, 26, 10
mark_center_y = (18.5 + 75) / 2
word_center_em = (WBB[1] + WBB[3]) / 2
tx = 96 + GAP - K * WBB[0]
ty = mark_center_y - K * word_center_em
lockup_w = tx + K * WBB[2] + RPAD
for v in VARIANTS:
    gid = f"lg-{v}"
    svg = (HEAD.format(w=round(lockup_w * 2), h=192, vb=f"0 0 {lockup_w:.2f} 96") + "\n"
           + grad_def(v, gid)
           + f'  <g fill="none">\n{mark_body(v, gid)}\n  </g>\n'
           + f'  <g transform="translate({tx:.2f},{ty:.2f}) scale({K})"><path d="{WD}" fill="{VARIANTS[v]["word"]}"/></g>\n</svg>')
    write(OUT / "logo" / f"leitum-lockup{suffix(v)}.svg", svg)

# favicon / app-icon tile (self-contained)
TILE_BG, TS = "#0D1117", 0.74
off = (128 - 96 * TS) / 2
gid = "lg-icon"
icon = (HEAD.format(w=128, h=128, vb="0 0 128 128") + "\n"
        + f'  <rect width="128" height="128" rx="30" fill="{TILE_BG}"/>\n'
        + f'  <rect x="1.5" y="1.5" width="125" height="125" rx="28.5" fill="none" stroke="{ACCENT}" stroke-opacity="0.22" stroke-width="1.5"/>\n'
        + f'  <defs><linearGradient id="{gid}" x1="0" y1="1" x2="1" y2="0">'
        + f'<stop offset="0" stop-color="#E6EDF3"/><stop offset="1" stop-color="{ACCENT}"/></linearGradient></defs>\n'
        + f'  <g fill="none" transform="translate({off:.2f},{off:.2f}) scale({TS})">\n{mark_body("dark", gid)}\n  </g>\n</svg>')
write(OUT / "favicon" / "icon.svg", icon)

gid = "lg-fav"
fav = HEAD.format(w=96, h=96, vb="0 0 96 96") + "\n" + grad_def("dark", gid) + mark_body("dark", gid) + "\n</svg>"
write(OUT / "favicon" / "favicon.svg", fav)

print("DONE")
