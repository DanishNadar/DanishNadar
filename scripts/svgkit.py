"""Shared SVG toolkit for the profile assets.

Every generated SVG is a self-contained dark panel so it reads well on both
GitHub themes. Fonts are subset to the glyphs each file uses and embedded as
WOFF data URIs (GitHub's image proxy blocks external font requests). All
motion is CSS keyframes, disabled under prefers-reduced-motion.
"""
from __future__ import annotations

import base64
import io
import math
from functools import lru_cache
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / "fonts"

# ── Palette ────────────────────────────────────────────────────────────────
NAVY = "#050B18"
MIDNIGHT = "#08162C"
PANEL = "#0B1B33"
PANEL_HI = "#10233F"
LINE = "#1E3556"
BLUE = "#35A7FF"
ICE = "#BFE1FF"
RED = "#EF314B"
RED_HI = "#FF4B57"
WHITE = "#F3F8FF"
STEEL = "#9EB3CD"
DIM = "#5F7898"

# ── Fonts ──────────────────────────────────────────────────────────────────
FALLBACK_SANS = "Inter,'Segoe UI',-apple-system,Helvetica,Arial,sans-serif"
FALLBACK_MONO = "'JetBrains Mono',Consolas,'SFMono-Regular',Menlo,monospace"

FONTS = {
    "display": ("InterDisplay-ExtraBold.ttf", "DNDisplay", FALLBACK_SANS, 800),
    "displaysemi": ("InterDisplay-SemiBold.ttf", "DNDisplaySemi", FALLBACK_SANS, 600),
    "sans": ("Inter-Regular.ttf", "DNSans", FALLBACK_SANS, 400),
    "sanssemi": ("Inter-SemiBold.ttf", "DNSansSemi", FALLBACK_SANS, 600),
    "mono": ("JetBrainsMono-Medium.ttf", "DNMono", FALLBACK_MONO, 500),
    "monobold": ("JetBrainsMono-Bold.ttf", "DNMonoBold", FALLBACK_MONO, 700),
}


@lru_cache(maxsize=None)
def _font(key: str) -> TTFont:
    return TTFont(FONT_DIR / FONTS[key][0])


@lru_cache(maxsize=None)
def _metrics(key: str):
    f = _font(key)
    return f.getBestCmap(), f["hmtx"].metrics, f["head"].unitsPerEm


def measure(text: str, font: str = "sans", size: float = 16, ls: float = 0) -> float:
    """Advance width of `text` in px using the real font metrics."""
    cmap, hmtx, upm = _metrics(font)
    total = 0
    for ch in text:
        glyph = cmap.get(ord(ch)) or cmap.get(ord("?"))
        total += hmtx[glyph][0]
    return total * size / upm + ls * len(text)


def wrap(text: str, maxw: float, font: str = "sans", size: float = 16, ls: float = 0) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if measure(trial, font, size, ls) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _font_face(key: str, chars: set[str]) -> str:
    opts = subset.Options()
    opts.flavor = "woff"
    opts.layout_features = ["kern", "liga", "calt", "tnum"]
    opts.notdef_outline = True
    font = TTFont(FONT_DIR / FONTS[key][0])
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(chars) + " ")
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff"
    font.save(buf)
    data = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:{FONTS[key][1]};src:url(data:font/woff;base64,{data}) format('woff');}}"


def fam(key: str) -> str:
    _, name, fallback, weight = FONTS[key]
    return f"font-family:{name},{fallback};font-weight:{weight}"


BASE_CSS = """
text{dominant-baseline:auto}
.flow{stroke-dasharray:3 9;animation:flow 1.8s linear infinite}
.flowslow{stroke-dasharray:2 10;animation:flow 3.2s linear infinite}
.pulse{animation:pulse 3.2s ease-in-out infinite}
.blink{animation:blink 2.4s ease-in-out infinite}
@keyframes flow{to{stroke-dashoffset:-24}}
@keyframes pulse{0%,100%{opacity:.35}50%{opacity:1}}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.45}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
"""


class Svg:
    """Minimal SVG builder that tracks glyph usage for font subsetting."""

    def __init__(self, w: int, h: int, title: str, desc: str):
        self.w, self.h, self.title, self.desc = w, h, title, desc
        self.defs: list[str] = []
        self.css: list[str] = [BASE_CSS]
        self.body: list[str] = []
        self.used: dict[str, set[str]] = {}
        self._ids = 0

    # ids keep gradients unique within a file
    def uid(self, prefix: str = "g") -> str:
        self._ids += 1
        return f"{prefix}{self._ids}"

    def add(self, markup: str) -> "Svg":
        self.body.append(markup)
        return self

    def text(self, x, y, s, font="sans", size=16, fill=WHITE, anchor="start", ls=0,
             cls="", extra="", opacity=None) -> str:
        self.used.setdefault(font, set()).update(s)
        attrs = [f'x="{x:.1f}"' if isinstance(x, float) else f'x="{x}"',
                 f'y="{y:.1f}"' if isinstance(y, float) else f'y="{y}"',
                 f'style="{fam(font)}"', f'font-size="{size}"', f'fill="{fill}"']
        if anchor != "start":
            attrs.append(f'text-anchor="{anchor}"')
        if ls:
            attrs.append(f'letter-spacing="{ls}"')
        if cls:
            attrs.append(f'class="{cls}"')
        if opacity is not None:
            attrs.append(f'opacity="{opacity}"')
        if extra:
            attrs.append(extra)
        el = f'<text {" ".join(attrs)}>{escape(s)}</text>'
        self.body.append(el)
        return el

    def rich(self, x, y, parts, size=16, anchor="start", ls=0, cls="", extra="") -> None:
        """parts: [(text, font, fill), ...] rendered as tspans on one line."""
        spans = []
        for s, font, fill in parts:
            self.used.setdefault(font, set()).update(s)
            spans.append(f'<tspan style="{fam(font)}" fill="{fill}">{escape(s)}</tspan>')
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        l = f' letter-spacing="{ls}"' if ls else ""
        c = f' class="{cls}"' if cls else ""
        self.body.append(f'<text x="{x}" y="{y}" font-size="{size}"{a}{l}{c} {extra}>{"".join(spans)}</text>')

    def render(self) -> str:
        faces = "".join(_font_face(k, v) for k, v in sorted(self.used.items()) if v)
        style = f"<style>{faces}{''.join(self.css)}</style>"
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="t d">'
            f'<title id="t">{escape(self.title)}</title><desc id="d">{escape(self.desc)}</desc>'
            f'{style}<defs>{"".join(self.defs)}</defs>{"".join(self.body)}</svg>\n'
        )

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render(), encoding="utf-8")
        return path


# ── Reusable pieces ────────────────────────────────────────────────────────

def panel(svg: Svg, x=0, y=0, w=None, h=None, rx=22, accent: str | None = None, grid=True) -> None:
    """Brand panel: navy gradient, faint engineering grid, hairline border."""
    w = w or svg.w
    h = h or svg.h
    bg, gr, fade = svg.uid("bg"), svg.uid("grid"), svg.uid("fade")
    svg.defs.append(
        f'<linearGradient id="{bg}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{NAVY}"/><stop offset="1" stop-color="{MIDNIGHT}"/></linearGradient>'
        f'<pattern id="{gr}" width="32" height="32" patternUnits="userSpaceOnUse">'
        f'<path d="M32 0H0V32" fill="none" stroke="{BLUE}" stroke-opacity=".055"/></pattern>'
        f'<radialGradient id="{fade}" cx=".75" cy=".3" r=".9">'
        f'<stop offset="0" stop-color="{BLUE}" stop-opacity=".10"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>'
    )
    svg.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="url(#{bg})"/>')
    if grid:
        svg.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="url(#{gr})"/>')
    svg.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="url(#{fade})"/>')
    svg.add(f'<rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="none" stroke="{LINE}"/>')
    if accent:
        ag = svg.uid("acc")
        svg.defs.append(f'<linearGradient id="{ag}"><stop stop-color="{accent}"/><stop offset="1" stop-color="{accent}" stop-opacity="0"/></linearGradient>')
        svg.add(f'<rect x="{x + rx}" y="{y}" width="{min(w * .45, 420)}" height="3" fill="url(#{ag})"/>')


def chip(svg: Svg, x, y, label, color=STEEL, fill=None, size=12, font="mono", pad=10, h=26) -> float:
    """Pill label; returns its width so callers can flow chips horizontally."""
    w = measure(label, font, size) + pad * 2
    svg.add(f'<rect x="{x}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" '
            f'fill="{fill or color}" fill-opacity="{0.12 if fill is None else 1}" stroke="{color}" stroke-opacity=".45"/>')
    svg.text(x + w / 2, y + h / 2 + size * .36, label, font, size, color if fill is None else NAVY, "middle")
    return w


def chips(svg: Svg, x, y, labels, maxw, color=STEEL, gap=8, size=12, h=26) -> float:
    """Flow chips left-to-right, wrapping; returns the bottom y."""
    cx, cy = x, y
    for lab in labels:
        w = measure(lab, "mono", size) + 20
        if cx + w > x + maxw and cx > x:
            cx, cy = x, cy + h + gap
        chip(svg, cx, cy, lab, color, size=size, h=h)
        cx += w + gap
    return cy + h


def status_dot(svg: Svg, x, y, label, color) -> float:
    svg.add(f'<circle cx="{x + 4}" cy="{y - 4}" r="4" fill="{color}" class="pulse"/>')
    svg.text(x + 14, y, label, "monobold", 11, color, ls=1.2)
    return 14 + measure(label, "monobold", 11, 1.2)


def arrow_marker(svg: Svg, color=BLUE) -> str:
    mid = svg.uid("arr")
    svg.defs.append(f'<marker id="{mid}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                    f'<path d="M0 0L10 5L0 10z" fill="{color}"/></marker>')
    return mid


def polar(cx, cy, r, deg):
    a = math.radians(deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)
