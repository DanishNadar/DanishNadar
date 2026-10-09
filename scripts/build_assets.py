"""Generate the static profile graphics from data/profile.json.

    python scripts/build_assets.py          # everything (hero included)

Outputs land in assets/. Live, data-driven panels (recent work,
contribution map, weekly design decision) come from update_activity.py.
"""
from __future__ import annotations

import json
import math

import build_hero
from svgkit import (BLUE, DIM, ICE, LINE, MIDNIGHT, NAVY, PANEL, PANEL_HI, RED, RED_HI, ROOT, STEEL,
                    WHITE, Svg, arrow_marker, chip, chips, measure, panel, wrap)

DATA = json.loads((ROOT / "data" / "profile.json").read_text(encoding="utf-8"))
OUT = ROOT / "assets"
STATUS = DATA["statuses"]


# ═══ Shared drawing helpers ═══════════════════════════════════════════════

def header(svg: Svg, kicker: str, title: str, x=44, y=50, color=RED_HI, sub: str | None = None) -> None:
    svg.add(f'<rect x="{x}" y="{y - 10}" width="8" height="8" fill="{color}"/>')
    svg.text(x + 18, y - 2, kicker, "monobold", 12, color, ls=2.4)
    svg.text(x, y + 36, title, "displaysemi", 28, WHITE, ls=-.4)
    if sub:
        svg.text(x, y + 62, sub, "sans", 15, STEEL)


def text_block(svg: Svg, x, y, s, maxw, font="sans", size=15, fill=STEEL, lh=None, max_lines=None) -> float:
    lines = wrap(s, maxw, font, size)
    if max_lines and len(lines) > max_lines:
        raise ValueError(f"text too long for {max_lines} lines: {s!r}")
    lh = lh or size * 1.45
    for i, line in enumerate(lines):
        svg.text(x, y + i * lh, line, font, size, fill)
    return y + (len(lines) - 1) * lh


def node(svg: Svg, x, y, w, h, title, sub="", color=BLUE, dashed=False, title_size=14, sub_size=11.5, fill=PANEL):
    dash = ' stroke-dasharray="5 4"' if dashed else ""
    svg.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{color}" stroke-opacity=".75"{dash}/>')
    svg.add(f'<rect x="{x}" y="{y + 10}" width="3" height="{h - 20}" rx="1.5" fill="{color}"/>')
    lines = wrap(sub, w - 28, "mono", sub_size) if sub else []
    total = title_size + (len(lines) * (sub_size + 5) + 4 if lines else 0)
    ty = y + (h - total) / 2 + title_size * .85
    svg.text(x + 14, ty, title, "sanssemi", title_size, WHITE)
    for i, line in enumerate(lines):
        svg.text(x + 14, ty + 8 + (i + 1) * (sub_size + 5) - 4, line, "mono", sub_size, STEEL)
    return (x, y, w, h)


def group(svg: Svg, x, y, w, h, label, color=BLUE, dashed=True):
    dash = ' stroke-dasharray="6 6"' if dashed else ""
    svg.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{color}" fill-opacity=".035" stroke="{color}" stroke-opacity=".45"{dash}/>')
    lw = measure(label, "monobold", 10.5, 1.6) + 16
    svg.add(f'<rect x="{x + 14}" y="{y - 9}" width="{lw}" height="18" rx="9" fill="{NAVY}" stroke="{color}" stroke-opacity=".6"/>')
    svg.text(x + 22, y + 4, label, "monobold", 10.5, color, ls=1.6)


def edge(svg: Svg, pts, color=BLUE, marker=None, dashed=False, curve=True):
    """Polyline/curve with arrowhead plus an animated flow overlay."""
    if curve and len(pts) == 2:
        (x0, y0), (x1, y1) = pts
        if abs(y1 - y0) < 1:
            d = f"M{x0} {y0}L{x1} {y1}"
        else:
            mx = (x0 + x1) / 2
            d = f"M{x0} {y0}C{mx} {y0} {mx} {y1} {x1} {y1}"
    else:
        d = "M" + "L".join(f"{x} {y}" for x, y in pts)
    m = f' marker-end="url(#{marker})"' if marker else ""
    dash = ' stroke-dasharray="4 5"' if dashed else ""
    svg.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-opacity=".55" stroke-width="1.6"{dash}{m}/>')
    if not dashed:
        svg.add(f'<path d="{d}" fill="none" stroke="{ICE}" stroke-width="1.6" class="flow" opacity=".8"/>')


def R(n):  # right-middle anchor of a node tuple
    x, y, w, h = n
    return (x + w, y + h / 2)


def L(n):
    x, y, w, h = n
    return (x, y + h / 2)


def T(n):
    x, y, w, h = n
    return (x + w / 2, y)


def B(n):
    x, y, w, h = n
    return (x + w / 2, y + h)


def footnote(svg: Svg, y, label, s, x=44, color=RED_HI):
    svg.text(x, y, label, "monobold", 11, color, ls=1.6)
    svg.text(x + measure(label, "monobold", 11, 1.6) + 12, y, s, "sans", 13.5, STEEL)


# ═══ Buttons ══════════════════════════════════════════════════════════════

def icon(kind: str, x, y, c):
    s = {
        "globe": f'<circle cx="{x}" cy="{y}" r="9" fill="none" stroke="{c}" stroke-width="1.8"/><ellipse cx="{x}" cy="{y}" rx="4" ry="9" fill="none" stroke="{c}" stroke-width="1.4"/><path d="M{x - 9} {y}H{x + 9}" stroke="{c}" stroke-width="1.4"/>',
        "grid": "".join(f'<rect x="{x - 9 + dx}" y="{y - 9 + dy}" width="7.5" height="7.5" rx="1.5" fill="{c if (dx, dy) != (10.5, 10.5) else "none"}" stroke="{c}" stroke-width="1.4"/>' for dx in (0, 10.5) for dy in (0, 10.5)),
        "doc": f'<path d="M{x - 7} {y - 10}h9l5 5v15h-14z" fill="none" stroke="{c}" stroke-width="1.8" stroke-linejoin="round"/><path d="M{x - 3.5} {y - 1}h7M{x - 3.5} {y + 3.5}h7" stroke="{c}" stroke-width="1.4"/>',
        "in": f'<rect x="{x - 10}" y="{y - 10}" width="20" height="20" rx="4" fill="none" stroke="{c}" stroke-width="1.8"/><path d="M{x - 5} {y - 1}v7M{x} {y + 6}v-7M{x} {y + 1}c0-3 6-3 6 0v5" fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round"/><circle cx="{x - 5}" cy="{y - 5}" r="1.3" fill="{c}"/>',
        "mail": f'<rect x="{x - 10}" y="{y - 7}" width="20" height="14" rx="2.5" fill="none" stroke="{c}" stroke-width="1.8"/><path d="M{x - 9} {y - 5}l9 6 9-6" fill="none" stroke="{c}" stroke-width="1.6"/>',
        "car": f'<path d="M{x - 10} {y + 3}l2.5-7h15l2.5 7v4h-20z" fill="none" stroke="{c}" stroke-width="1.8" stroke-linejoin="round"/><circle cx="{x - 5}" cy="{y + 7}" r="2" fill="{c}"/><circle cx="{x + 5}" cy="{y + 7}" r="2" fill="{c}"/>',
    }
    return s[kind]


def button(name, label, sub, kind, primary=False):
    h = 54
    w = int(58 + max(measure(label, "sanssemi", 15), measure(sub, "mono", 10.5, .6)) + 26)
    svg = Svg(w, h, f"{label}: {sub}", f"Link button: {label} ({sub})")
    color = RED_HI if primary else BLUE
    fill = "#1A0F1E" if primary else PANEL
    svg.add(f'<rect x=".75" y=".75" width="{w - 1.5}" height="{h - 1.5}" rx="12" fill="{fill}" stroke="{color}" stroke-opacity=".8" stroke-width="1.5"/>')
    svg.add(f'<rect x="10" y="10" width="34" height="34" rx="9" fill="{color}" fill-opacity=".14"/>')
    svg.add(icon(kind, 27, 27, color))
    svg.text(56, 25, label, "sanssemi", 15, WHITE)
    svg.text(56, 41, sub, "mono", 10.5, STEEL, ls=.6)
    svg.save(OUT / "buttons" / f"{name}.svg")


def buttons():
    button("portfolio", "Portfolio", "danishnadar.com", "globe", primary=True)
    button("projects", "Case Studies", "/projects", "grid")
    button("autonomy", "Autonomy Work", "/autonomous-vehicles", "car")
    button("resume", "Resume", "/resume", "doc")
    button("linkedin", "LinkedIn", "in/danish-nadar", "in")
    button("contact", "Contact", "/contact", "mail")


# ═══ Engineering pipeline ═════════════════════════════════════════════════

def stage_icon(svg: Svg, i, cx, cy, c):
    if i == 0:  # perception: lens + scan arcs
        svg.add(f'<circle cx="{cx}" cy="{cy}" r="9" fill="none" stroke="{c}" stroke-width="2"/><circle cx="{cx}" cy="{cy}" r="3" fill="{c}"/>'
                f'<path d="M{cx - 18} {cy - 10}A20 20 0 0 1 {cx - 18} {cy + 10}M{cx + 18} {cy - 10}A20 20 0 0 0 {cx + 18} {cy + 10}" fill="none" stroke="{c}" stroke-width="1.6" class="pulse"/>')
    elif i == 1:  # representation: embedding grid
        svg.add("".join(f'<rect x="{cx - 14 + dx * 8}" y="{cy - 14 + dy * 8}" width="5" height="5" rx="1" fill="{c}" opacity="{.25 + .75 * ((dx * 3 + dy * 5) % 4) / 3:.2f}"/>' for dx in range(4) for dy in range(4)))
    elif i == 2:  # reasoning: graph
        pts = [(cx - 14, cy + 8), (cx, cy - 12), (cx + 14, cy + 8), (cx, cy + 2)]
        svg.add("".join(f'<path d="M{a[0]} {a[1]}L{b[0]} {b[1]}" stroke="{c}" stroke-width="1.5"/>' for a, b in [(pts[0], pts[1]), (pts[1], pts[2]), (pts[0], pts[3]), (pts[3], pts[2]), (pts[1], pts[3])]))
        svg.add("".join(f'<circle cx="{x}" cy="{y}" r="3.6" fill="{NAVY}" stroke="{c}" stroke-width="1.8"/>' for x, y in pts))
    elif i == 3:  # decision: fork
        svg.add(f'<path d="M{cx - 16} {cy}H{cx - 3}M{cx - 3} {cy}L{cx + 12} {cy - 11}M{cx - 3} {cy}L{cx + 12} {cy + 11}" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round"/>'
                f'<circle cx="{cx + 14}" cy="{cy - 12}" r="3.5" fill="{c}"/><circle cx="{cx + 14}" cy="{cy + 12}" r="3.5" fill="none" stroke="{c}" stroke-width="1.6"/>')
    else:  # action: steering wheel
        svg.add(f'<circle cx="{cx}" cy="{cy}" r="13" fill="none" stroke="{c}" stroke-width="2"/><circle cx="{cx}" cy="{cy}" r="3.5" fill="{c}"/>'
                f'<path d="M{cx - 13} {cy}H{cx - 3.5}M{cx + 3.5} {cy}H{cx + 13}M{cx} {cy + 3.5}V{cy + 13}" stroke="{c}" stroke-width="2"/>')


def pipeline():
    stages = DATA["pipeline"]
    W, colw, gap, x0 = 1200, 212, 15, 40
    svg = Svg(W, 470, "Engineering pipeline: Perception, Representation, Reasoning, Decision, Action",
              "Five-stage intelligent-system pipeline with the projects that implement each stage: "
              + "; ".join(f"{s['stage'].title()}: {', '.join(e.split(' · ')[0] for e in s['evidence'])}" for s in stages))
    panel(svg, accent=BLUE)
    header(svg, "ENGINEERING SNAPSHOT", "From raw signals to real-world action", color=BLUE,
           sub="Where my systems sit in the perceive → reason → act loop. Each project appears only under the stages it implements.")
    top = 150
    mk = arrow_marker(svg, STEEL)
    for i, s in enumerate(stages):
        x = x0 + i * (colw + gap)
        c = s["color"]
        svg.add(f'<rect x="{x}" y="{top}" width="{colw}" height="282" rx="14" fill="{PANEL}" fill-opacity=".85" stroke="{LINE}"/>')
        svg.add(f'<rect x="{x}" y="{top}" width="{colw}" height="3" rx="1.5" fill="{c}"/>')
        stage_icon(svg, i, x + 34, top + 38, c)
        svg.text(x + colw - 16, top + 30, f"0{i + 1}", "mono", 12, DIM, "end")
        svg.text(x + 16, top + 82, s["stage"], "monobold", 13.5, c, ls=1.8)
        svg.text(x + 16, top + 102, s["verb"], "sans", 13.5, STEEL)
        svg.add(f'<path d="M{x + 16} {top + 116}H{x + colw - 16}" stroke="{LINE}"/>')
        y = top + 140
        for ev in s["evidence"]:
            proj, detail = ev.split(" · ")
            svg.add(f'<rect x="{x + 16}" y="{y - 9}" width="5" height="5" fill="{c}"/>')
            svg.text(x + 28, y - 3, proj, "sanssemi", 13, WHITE)
            svg.text(x + 28, y + 13, detail, "mono", 10.5, STEEL)
            y += 36
        if i < len(stages) - 1:
            ax = x + colw + 1
            svg.add(f'<path d="M{ax} {top + 82}H{ax + gap - 3}" stroke="{STEEL}" stroke-width="1.5" marker-end="url(#{mk})"/>')
    # feedback loop: action returns new observations
    svg.add(f'<path d="M{x0 + 4 * (colw + gap) + colw / 2} {top + 284}V{top + 300}H{x0 + colw / 2}V{top + 286}" fill="none" stroke="{RED_HI}" stroke-opacity=".6" stroke-width="1.5" class="flowslow" marker-end="url(#{arrow_marker(svg, RED_HI)})"/>')
    svg.text(W / 2, top + 296, "ACTIONS CHANGE WHAT THE SYSTEM PERCEIVES NEXT", "monobold", 10, RED_HI, "middle", ls=1.8,
             extra=f'paint-order="stroke" stroke="{MIDNIGHT}" stroke-width="8"')
    svg.save(OUT / "diagrams" / "pipeline.svg")


# ═══ Project motifs ═══════════════════════════════════════════════════════

def motif(svg: Svg, kind, x, y, w, h, c):
    cx, cy = x + w / 2, y + h / 2
    out = []
    if kind == "multimodal":
        # waveform (audio), landmark mesh (vision), aligned evidence lanes (fusion)
        pts = []
        for i in range(60):
            px = x + 20 + i * (w - 40) / 59
            amp = (math.sin(i * .55) * math.sin(i * .13) + .25 * math.sin(i * 1.7)) * h * .12
            pts.append(f"{px:.1f},{y + h * .24 - amp:.1f}")
        out.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{BLUE}" stroke-width="2"/>')
        fx, fy = x + w * .27, y + h * .58
        mesh = [(0, -34), (-20, -24), (20, -24), (-26, -4), (26, -4), (-22, 16), (22, 16), (-10, 30), (10, 30), (0, 34),
                (-10, -8), (10, -8), (0, 6), (-8, 18), (8, 18)]
        for (ax, ay) in mesh:
            out.append(f'<circle cx="{fx + ax}" cy="{fy + ay}" r="2" fill="{ICE}"/>')
        for a, b in [(0, 1), (0, 2), (1, 3), (2, 4), (3, 5), (4, 6), (5, 7), (6, 8), (7, 9), (8, 9), (10, 12), (11, 12), (12, 13), (12, 14), (13, 14)]:
            out.append(f'<path d="M{fx + mesh[a][0]} {fy + mesh[a][1]}L{fx + mesh[b][0]} {fy + mesh[b][1]}" stroke="{ICE}" stroke-opacity=".35"/>')
        out.append(f'<rect x="{fx - 34}" y="{fy - 44}" width="68" height="88" fill="none" stroke="{RED_HI}" stroke-width="1.6" class="blink"/>')
        lx = x + w * .52
        for i, (lab, col, segs) in enumerate([("AUDIO", BLUE, [(0, .25), (.45, .7)]), ("VISION", ICE, [(.1, .3), (.5, .85)]), ("TEXT", STEEL, [(0, .4), (.55, .95)])]):
            ly = y + h * .44 + i * 26
            out.append(f'<text x="{lx}" y="{ly + 4}" style="font-family:DNMono,monospace" font-size="9" fill="{DIM}">{lab}</text>')
            for s0, s1 in segs:
                out.append(f'<rect x="{lx + 48 + s0 * (w * .34)}" y="{ly - 5}" width="{(s1 - s0) * w * .34:.1f}" height="9" rx="3" fill="{col}" opacity=".75"/>')
        svg.used.setdefault("mono", set()).update("AUDIOVISNTEX")
        out.append(f'<path d="M{lx + 48 + .5 * w * .34} {y + h * .36}V{y + h * .44 + 62}" stroke="{RED_HI}" stroke-width="1.5" stroke-dasharray="3 3"/>')
    elif kind == "layers":
        n, bw, bh = 12, w * .32, (h - 60) / 12 - 4
        keep = [0, 2, 4, 7, 9, 11]
        for i in range(n):
            by = y + 30 + i * (bh + 4)
            k = i in keep
            out.append(f'<rect x="{x + 24}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="3" fill="{ICE if k else LINE}" opacity="{.95 if k else .8}"/>')
        for j, i in enumerate(keep):
            by0 = y + 30 + i * (bh + 4) + bh / 2
            by1 = y + 30 + j * 2 * (bh + 4) + bh
            out.append(f'<path d="M{x + 24 + bw} {by0:.1f}C{cx} {by0:.1f} {cx} {by1:.1f} {x + w - 24 - bw} {by1:.1f}" fill="none" stroke="{BLUE}" stroke-opacity=".6" class="flow"/>')
            out.append(f'<rect x="{x + w - 24 - bw:.1f}" y="{by1 - bh:.1f}" width="{bw:.1f}" height="{bh * 2:.1f}" rx="3" fill="{BLUE}" opacity=".9"/>')
        out.append(f'<text x="{x + 24}" y="{y + h - 10}" style="font-family:DNMono,monospace" font-size="10" fill="{DIM}">TEACHER · 12</text>')
        out.append(f'<text x="{x + w - 24}" y="{y + h - 10}" text-anchor="end" style="font-family:DNMono,monospace" font-size="10" fill="{BLUE}">STUDENT · 6</text>')
        svg.used.setdefault("mono", set()).update("TEACHER·12STUDN6 ")
    elif kind == "tracking":
        sc = min(w / 200, h / 170)
        out.append(f'<g transform="translate({cx} {cy}) scale({sc:.2f}) translate({-cx} {-cy})">')
        gx, gy = cx - 10, cy + 6
        out.append(f'<path d="M{cx - 120} {gy + 48}H{cx + 110}" stroke="{LINE}" stroke-width="2"/>')
        out.append(f'<g fill="{STEEL}"><circle cx="{gx}" cy="{gy - 40}" r="9"/><path d="M{gx - 11} {gy - 28}h22l4 36h-6l-2 34h-6l-3-28-3 28h-6l-2-34h-6z"/></g>')
        out.append(f'<rect x="{gx - 26}" y="{gy - 56}" width="52" height="104" fill="none" stroke="{RED_HI}" stroke-width="2"/>')
        out.append(f'<rect x="{gx + 4}" y="{gy - 54}" width="52" height="104" fill="none" stroke="{BLUE}" stroke-width="1.6" stroke-dasharray="5 4" class="blink"/>')
        out.append(f'<text x="{gx - 26}" y="{gy + 62}" style="font-family:DNMono,monospace" font-size="9.5" fill="{RED_HI}">MEASURED</text>')
        out.append(f'<text x="{gx + 56}" y="{gy - 62}" text-anchor="end" style="font-family:DNMono,monospace" font-size="9.5" fill="{BLUE}">PREDICTED</text>')
        svg.used.setdefault("mono", set()).update("MEASUREDPRICT")
        trail = [(cx - 110 + i * 18, gy + 30 - math.sin(i * .5) * 8) for i in range(5)]
        out += [f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{2 + i * .5}" fill="{BLUE}" opacity="{.2 + i * .15:.2f}"/>' for i, (px, py) in enumerate(trail)]
        out.append(f'<path d="M{gx + 30} {gy - 2}C{gx + 60} {gy - 6} {gx + 80} {gy - 14} {cx + 95} {gy - 24}" fill="none" stroke="{BLUE}" stroke-width="2" stroke-dasharray="4 5" class="flow"/>')
        out.append("</g>")
    elif kind == "fusion":
        sx = x + w - 24
        for i, (lab, col) in enumerate([("CAM", BLUE), ("RADAR", ICE), ("LIDAR", RED_HI)]):
            yy = y + h * .18 + i * h * .32
            out.append(f'<path d="M{x + 16} {yy}L{sx} {cy}" stroke="{col}" stroke-width="1.6" stroke-opacity=".7" class="flow"/>')
            out.append(f'<circle cx="{x + 16}" cy="{yy}" r="4.5" fill="{col}"/>')
            out.append(f'<text x="{x + 26}" y="{yy - 5}" style="font-family:DNMono,monospace" font-size="9" fill="{col}">{lab}</text>')
        svg.used.setdefault("mono", set()).update("CAMRDLI")
        out.append(f'<circle cx="{sx}" cy="{cy}" r="14" fill="{NAVY}" stroke="{WHITE}" stroke-width="2"/><circle cx="{sx}" cy="{cy}" r="5" fill="{WHITE}" class="pulse"/>')
    elif kind == "lanes":
        vx, vy = cx, y + 14
        for k, col in ((-1, BLUE), (1, BLUE), (0, STEEL)):
            bx = cx + k * w * .42
            out.append(f'<path d="M{vx + k * 6} {vy}L{bx} {y + h - 8}" stroke="{col}" stroke-width="{2.5 if k else 1.5}" {"stroke-dasharray=\"6 6\"" if k == 0 else ""}/>')
        for t in (.3, .5, .7, .9):
            for k in (-1, 1):
                px = vx + k * 6 + (cx + k * w * .42 - vx - k * 6) * t
                py = vy + (y + h - 8 - vy) * t
                out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{2 + t * 2:.1f}" fill="{RED_HI}"/>')
    elif kind == "rl":
        d = f"M{x + 10} {y + h - 14}C{x + w * .45} {y + h - 14} {x + w * .5} {y + h * .45} {x + w - 10} {y + h * .42}"
        out.append(f'<path d="{d}" fill="none" stroke="{LINE}" stroke-width="16" stroke-linecap="round"/>')
        out.append(f'<path d="{d}" fill="none" stroke="{STEEL}" stroke-width="1.2" stroke-dasharray="5 6"/>')
        out.append(f'<path d="{d}" fill="none" stroke="{BLUE}" stroke-width="2.5" class="flow"/>')
        spark = " ".join(f"{x + 12 + i * 7:.1f},{y + 30 - min(22, (i ** 1.2) * 1.4 + 4 * math.sin(i)):.1f}" for i in range(9))
        out.append(f'<polyline points="{spark}" fill="none" stroke="{RED_HI}" stroke-width="1.8"/>')
        out.append(f'<text x="{x + 76}" y="{y + 14}" style="font-family:DNMono,monospace" font-size="9" fill="{DIM}">REWARD</text>')
        svg.used.setdefault("mono", set()).update("REWAD")
    elif kind == "equilibrium":
        labs = ["HAPPY", "ANGRY", "SAD", "NEUTRAL"] if w > 200 else ["H", "A", "S", "N"]
        bw = (w - 60) / 4
        for i, lab in enumerate(labs):
            bh = (h - 50) * .5
            bx = x + 20 + i * (bw + 7)
            out.append(f'<rect x="{bx:.1f}" y="{y + h - 26 - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="3" fill="{BLUE if i % 2 == 0 else ICE}" opacity=".85" class="pulse" style="animation-delay:{i * .4}s"/>')
            out.append(f'<text x="{bx + bw / 2:.1f}" y="{y + h - 10}" text-anchor="middle" style="font-family:DNMono,monospace" font-size="8.5" fill="{STEEL}">{lab}</text>')
        out.append(f'<path d="M{x + 14} {y + h - 26 - (h - 50) * .5}H{x + w - 14}" stroke="{RED_HI}" stroke-dasharray="4 4"/>')
        out.append(f'<text x="{x + w - 14}" y="{y + h - 32 - (h - 50) * .5}" text-anchor="end" style="font-family:DNMono,monospace" font-size="9" fill="{RED_HI}">25%</text>')
        svg.used.setdefault("mono", set()).update("HAPYNGRSDEUTL25%")
    elif kind == "voice":
        for i, r in enumerate((14, 26, 38)):
            if r > h / 2 - 2:
                continue
            out.append(f'<circle cx="{x + 46}" cy="{cy}" r="{r}" fill="none" stroke="{ICE}" stroke-opacity="{.8 - i * .25:.2f}" class="pulse" style="animation-delay:{i * .5}s"/>')
        out.append(f'<circle cx="{x + 46}" cy="{cy}" r="8" fill="{ICE}"/>')
        nbars = max(6, int((w - 100) / 7))
        step = (w - 100) / nbars
        for i in range(nbars):
            bh = 8 + abs(math.sin(i * .9)) * (h * .5)
            out.append(f'<rect x="{x + 96 + i * step:.1f}" y="{cy - bh / 2:.1f}" width="4" height="{bh:.1f}" rx="2" fill="{BLUE}" opacity=".85"/>')
    elif kind == "grid":
        belts = ["#F3F8FF", "#FFD24B", "#FF9B3D", "#3DCB7A", "#35A7FF", "#A070FF", "#8B5A2B", "#1A1A1A"]
        cols, rows = 7, 8
        cw, ch = (w - 50) / cols, (h - 24) / rows
        for r in range(rows):
            out.append(f'<rect x="{x + 12}" y="{y + 12 + r * ch:.1f}" width="10" height="{ch - 3:.1f}" rx="2" fill="{belts[r]}" stroke="{LINE}"/>')
            for cidx in range(cols):
                on = r < 5 and cidx in (1, 2, 4)
                out.append(f'<rect x="{x + 30 + cidx * cw:.1f}" y="{y + 12 + r * ch:.1f}" width="{cw - 3:.1f}" height="{ch - 3:.1f}" rx="2" fill="{RED_HI if on else LINE}" opacity="{.85 if on else .7}"/>')
    elif kind == "gpu":
        for i in range(4):
            gy = y + 14 + i * (h - 28) / 4
            out.append(f'<rect x="{x + 14}" y="{gy:.1f}" width="{w * .55:.1f}" height="{(h - 28) / 4 - 6:.1f}" rx="4" fill="{PANEL_HI}" stroke="{LINE}"/>')
            for f in range(3):
                out.append(f'<circle cx="{x + 30 + f * 18}" cy="{gy + ((h - 28) / 4 - 6) / 2:.1f}" r="5" fill="none" stroke="{BLUE}" stroke-opacity=".8"/>')
            out.append(f'<rect x="{x + w * .55 - 14:.1f}" y="{gy + 6:.1f}" width="14" height="{(h - 28) / 4 - 18:.1f}" rx="2" fill="{RED_HI}" class="pulse" style="animation-delay:{i * .5}s"/>')
        for i, v in enumerate((.35, .6, .85)):
            bx = x + w * .68 + i * 16
            out.append(f'<rect x="{bx:.1f}" y="{y + h - 14 - v * (h - 28):.1f}" width="10" height="{v * (h - 28):.1f}" rx="2" fill="{BLUE if i < 2 else ICE}"/>')
    svg.add("".join(out))


# ═══ Project cards ════════════════════════════════════════════════════════

def status_chips(svg, x, y, keys, maxw=None, h=24):
    cx = x
    for k in keys:
        label, color = STATUS[k]
        cx += chip(svg, cx, y, label, color, size=10.5, h=h) + 8
    return cx


def flagship_card(p):
    W, cw = 1200, 700
    tag_lines = wrap(p["tagline"], cw, "sans", 18)
    fact_lines = [wrap(f, cw - 26, "sans", 15) for f in p["facts"]]
    y_facts = 150 + len(tag_lines) * 26 + 18
    fh = sum(len(l) * 22 + 12 for l in fact_lines)
    H = int(y_facts + fh + 80)
    svg = Svg(W, H, f"{p['name']}: {p['kicker'].title()}", f"{p['name']}. {p['tagline']} " + " ".join(p["facts"]))
    accent = p["accent"]
    panel(svg, accent=accent)
    svg.text(44, 52, p["kicker"], "monobold", 12, accent, ls=2.2)
    svg.text(42, 106, p["name"], "display", 48, WHITE, ls=-1)
    status_chips(svg, 44 + measure(p["name"], "display", 48, -1) + 24, 78, p["status"])
    for i, line in enumerate(tag_lines):
        svg.text(44, 148 + i * 26, line, "sans", 18, ICE)
    y = y_facts
    for lines in fact_lines:
        svg.add(f'<path d="M46 {y - 5}h10" stroke="{accent}" stroke-width="2.5" stroke-linecap="round"/>')
        for j, line in enumerate(lines):
            svg.text(70, y + j * 22, line, "sans", 15, STEEL)
        y += len(lines) * 22 + 12
    chips(svg, 44, H - 54, p["stack"], cw, STEEL, size=11, h=26)
    mx, my, mw, mh = 790, 34, 366, H - 68
    svg.add(f'<rect x="{mx}" y="{my}" width="{mw}" height="{mh}" rx="16" fill="{NAVY}" fill-opacity=".7" stroke="{LINE}"/>')
    motif(svg, p["motif"], mx + 10, my + 10, mw - 20, mh - 20, accent)
    svg.save(OUT / "projects" / f"{p['id']}.svg")


def compact_card(p):
    W, H = 600, 300
    svg = Svg(W, H, f"{p['name']}: {p['kicker'].title()}", f"{p['name']}. {p['tagline']}")
    accent = p["accent"]
    panel(svg, accent=accent, rx=20)
    svg.text(32, 44, p["kicker"], "monobold", 11, accent, ls=1.8)
    svg.text(30, 84, p["name"], "display", 31, WHITE, ls=-.6)
    lines = wrap(p["tagline"], 536, "sans", 15.5)
    if len(lines) > 3:
        raise ValueError(f"{p['id']} tagline wraps to {len(lines)} lines")
    for i, line in enumerate(lines):
        svg.text(32, 116 + i * 22, line, "sans", 15.5, STEEL)
    status_chips(svg, 32, 190, p["status"], h=22)
    chips(svg, 32, 224, p["stack"], 380, STEEL, gap=6, size=10.5, h=22)
    mx, my, mw, mh = 428, 182, 142, 92
    svg.add(f'<rect x="{mx}" y="{my}" width="{mw}" height="{mh}" rx="12" fill="{NAVY}" fill-opacity=".7" stroke="{LINE}"/>')
    motif(svg, p["motif"], mx + 4, my + 4, mw - 8, mh - 8, accent)
    svg.save(OUT / "projects" / f"{p['id']}.svg")


# ═══ Architecture diagrams ════════════════════════════════════════════════

def arch_taloncv():
    svg = Svg(1200, 520, "TalonCV architecture",
              "Browser-only pipeline. MediaRecorder and file import feed an IndexedDB session store. An analysis worker runs Whisper "
              "transcription, audio DSP and MiniLM semantic analysis; a vision worker runs a YOLO11 face ONNX model, MediaPipe face and pose "
              "landmarks, cue rules, a random-forest cue classifier and a temporal state machine. Events are aligned by overlapping time "
              "windows, scored deterministically and rendered as an eight-tab explainable report. An optional SmolLM2 worker only rewords coaching text.")
    panel(svg, accent=BLUE)
    header(svg, "TALONCV · ARCHITECTURE", "Multimodal inference that never leaves the browser", color=BLUE)
    mk = arrow_marker(svg, BLUE)
    group(svg, 28, 112, 1144, 352, "USER'S BROWSER  ·  NO BACKEND  ·  NO INFERENCE API", BLUE)
    cap = node(svg, 52, 160, 180, 82, "Capture", "MediaRecorder · Web Audio · file import", ICE)
    store = node(svg, 52, 300, 180, 82, "Session store", "IndexedDB · replay · ZIP import/export", ICE)
    group(svg, 268, 140, 330, 150, "analysis.worker", BLUE, dashed=False)
    a1 = node(svg, 284, 158, 298, 36, "Whisper tiny.en  →  transcript", "", BLUE, title_size=13)
    a2 = node(svg, 284, 200, 298, 36, "Audio DSP  →  pauses · rate · volume", "", BLUE, title_size=13)
    a3 = node(svg, 284, 242, 298, 36, "MiniLM-L6  →  answer semantics", "", BLUE, title_size=13)
    group(svg, 268, 312, 330, 140, "vision.worker", RED_HI, dashed=False)
    v1 = node(svg, 284, 328, 298, 34, "YOLO11n-face (ONNX)  →  face box", "", RED_HI, title_size=13)
    v2 = node(svg, 284, 368, 298, 34, "MediaPipe face + pose landmarks", "", RED_HI, title_size=13)
    v3 = node(svg, 284, 408, 298, 34, "Cue rules · random forest · state machine", "", RED_HI, title_size=12.5)
    al = node(svg, 640, 220, 220, 96, "Multimodal alignment", "overlapping time windows → evidence moments", WHITE)
    sc = node(svg, 640, 344, 220, 82, "Deterministic scoring", "reproducible, explainable", WHITE)
    rp = node(svg, 904, 220, 244, 96, "Explainable report", "8 tabs: transcript, vocal, visual, moments…", ICE)
    co = node(svg, 904, 344, 244, 82, "coaching.worker", "SmolLM2-135M · optional wording only", STEEL, dashed=True)
    edge(svg, [B(cap), T(store)], BLUE, mk)
    edge(svg, [R(store), (268, 215)], BLUE, mk)
    edge(svg, [R(store), (268, 382)], BLUE, mk)
    edge(svg, [(598, 215), (640, 256)], BLUE, mk)
    edge(svg, [(598, 382), (640, 290)], RED_HI, arrow_marker(svg, RED_HI))
    edge(svg, [B(al), T(sc)], BLUE, mk)
    edge(svg, [(860, 385), (880, 385), (880, 268), (904, 268)], BLUE, mk, curve=False)
    edge(svg, [T(co), B(rp)], STEEL, arrow_marker(svg, STEEL), dashed=True)
    footnote(svg, 494, "DESIGN DECISION", "Scores never depend on the language model. After the first model download, analysis works without a network.")
    svg.save(OUT / "architecture" / "taloncv.svg")


def arch_morph():
    svg = Svg(1200, 470, "Morph architecture",
              "Teacher causal LM with N blocks; the block list is located via known attribute paths; k blocks are selected uniformly "
              "across depth; a reduced student copies embeddings, norms, LM head and the selected blocks. Either save directly "
              "(compress-only) or distill with cross-entropy, temperature-scaled KL and optional hidden-state MSE against a frozen, "
              "optionally 4/8-bit quantized teacher. Output is a standard Transformers checkpoint plus compression metadata.")
    panel(svg, accent=ICE)
    header(svg, "MORPH · ARCHITECTURE", "Remove depth, keep behaviour", color=ICE)
    mk = arrow_marker(svg, BLUE)
    t = node(svg, 40, 150, 190, 92, "Teacher LM", "HF causal model · N transformer blocks", ICE)
    f = node(svg, 262, 150, 200, 92, "find_layer_path", "Llama · Mistral · Qwen2 · GPT-2 · OPT · NeoX · MPT", BLUE)
    s = node(svg, 494, 150, 200, 92, "select_uniform_layers", "N → k, spread across depth incl. late layers", BLUE)
    st = node(svg, 726, 150, 210, 92, "make_reduced_student", "copy embeddings · norms · LM head · k blocks", BLUE)
    out = node(svg, 968, 150, 196, 92, "Student checkpoint", "safetensors + compression_metadata.json", RED_HI)
    for a, b in ((t, f), (f, s), (s, st)):
        edge(svg, [R(a), L(b)], BLUE, mk)
    edge(svg, [R(st), L(out)], STEEL, arrow_marker(svg, STEEL), dashed=True)
    svg.text(950, 140, "--compress_only", "mono", 10.5, DIM, "middle")
    group(svg, 40, 290, 1124, 140, "distill()  ·  frozen teacher + trainable student on packed sequences", RED_HI, dashed=False)
    d1 = node(svg, 60, 316, 250, 92, "Frozen teacher", "optional 4-bit / 8-bit quantization (bitsandbytes)", ICE)
    svg.add(f'<rect x="340" y="316" width="440" height="92" rx="10" fill="{PANEL}" stroke="{RED_HI}" stroke-opacity=".75"/>')
    svg.text(358, 342, "Loss", "sanssemi", 14, WHITE)
    svg.rich(358, 370, [("L = ", "mono", STEEL), ("w_hard", "mono", ICE), ("·CE(tokens) + ", "mono", STEEL),
                        ("w_soft", "mono", BLUE), ("·T²·KL(teacher‖student)", "mono", STEEL)], size=13)
    svg.rich(358, 392, [("  + ", "mono", STEEL), ("w_hid", "mono", RED_HI), ("·MSE(hidden states)", "mono", STEEL),
                        ("   defaults .5 / .5 / 0, T = 2", "mono", DIM)], size=13)
    d3 = node(svg, 810, 316, 334, 92, "Optimizer", "AdamW + warmup · grad accumulation · checkpointing · FP16/BF16", BLUE)
    edge(svg, [R(d1), (340, 362)], BLUE, mk)
    edge(svg, [(780, 362), L(d3)], BLUE, mk)
    edge(svg, [B(st), (831, 290)], RED_HI, arrow_marker(svg, RED_HI))
    edge(svg, [(1066, 290), B(out)], RED_HI, arrow_marker(svg, RED_HI))
    footnote(svg, 452, "LIMITS, STATED", "Depth only: width, heads and vocabulary are unchanged. Quality must be measured on held-out data, not inferred from the ratio.")
    svg.save(OUT / "architecture" / "morph.svg")


def arch_observe():
    svg = Svg(1200, 500, "OBSERV-E architecture",
              "Camera frames feed two loops. Tracking: YOLO11 person detector, target selector, tracker with OpenCV and Lucas-Kanade "
              "fallback, constant-velocity Kalman filter, and a high-rate projector that publishes the gimbal state at 100 to 300 Hz to the "
              "teammates' STM32 firmware with a BNO085 IMU. Safety: hazard detector and risk engine feed an event-driven speech planner "
              "that drives text-to-speech and a Bluetooth or Web Serial companion app. An optional asynchronous VLM narrates the scene.")
    panel(svg, accent=RED_HI)
    header(svg, "OBSERV-E · ARCHITECTURE", "Perception loops for a human-following guide robot", color=RED_HI)
    mk, mr, ms = arrow_marker(svg, BLUE), arrow_marker(svg, RED_HI), arrow_marker(svg, STEEL)
    cam = node(svg, 36, 236, 120, 80, "Camera", "frames", ICE)
    group(svg, 186, 118, 978, 128, "TRACKING + CONTROL LOOP", BLUE, dashed=False)
    n1 = node(svg, 204, 142, 160, 84, "YOLO11n", "person detector", BLUE)
    n2 = node(svg, 384, 142, 160, 84, "Target lock", "select · reacquire", BLUE)
    n3 = node(svg, 564, 142, 184, 84, "Tracker", "OpenCV → LK flow + template", BLUE)
    n4 = node(svg, 768, 142, 170, 84, "Kalman filter", "constant-velocity box", BLUE)
    n5 = node(svg, 958, 142, 188, 84, "Projector 100–300 Hz", "→ gimbal state matrix", WHITE)
    group(svg, 186, 278, 978, 112, "SAFETY + GUIDANCE LOOP", RED_HI, dashed=False)
    h1 = node(svg, 204, 300, 190, 72, "Hazard detector", "YOLO · on-device", RED_HI)
    h2 = node(svg, 414, 300, 170, 72, "Risk engine", "path + proximity", RED_HI)
    h3 = node(svg, 604, 300, 220, 72, "Speech planner", "speaks on change, not on timers", RED_HI)
    h4 = node(svg, 844, 300, 302, 72, "TTS + companion app", "BLE / Web Serial / SSE bridge", WHITE)
    v = node(svg, 414, 410, 300, 60, "VLM scene narrator", "async · optional · sampled frames", STEEL, dashed=True)
    hw = node(svg, 958, 410, 188, 60, "STM32WB + BNO085", "gimbal firmware (team)", STEEL, dashed=True)
    edge(svg, [R(cam), L(n1)], BLUE, mk)
    edge(svg, [R(cam), L(h1)], RED_HI, mr)
    for a, b in ((n1, n2), (n2, n3), (n3, n4), (n4, n5)):
        edge(svg, [R(a), L(b)], BLUE, mk)
    for a, b in ((h1, h2), (h2, h3), (h3, h4)):
        edge(svg, [R(a), L(b)], RED_HI, mr)
    edge(svg, [R(n5), (1158, 184), (1158, 440), R(hw)], STEEL, ms, dashed=True, curve=False)
    edge(svg, [R(v), (714, 440), (714, 372)], STEEL, ms, dashed=True, curve=False)
    edge(svg, [(156, 300), (180, 300), (180, 440), (414, 440)], STEEL, ms, dashed=True, curve=False)
    footnote(svg, 488, "DESIGN DECISION", "Control output runs faster than inference, so the gimbal follows a predicted state between detections.", color=RED_HI)
    svg.save(OUT / "architecture" / "observe.svg")


def arch_campgrids():
    svg = Svg(1200, 520, "CampGrids architecture",
              "Content pipeline: the Excel workbook with hyperlinks goes through generateCampgrids.py into generated campData and a static "
              "site on Vercel. Accounts: students sign in with class code and username, staff with password and an emailed one-time code; "
              "Supabase Auth, Postgres with row-level security and RPCs, admin-only Edge Functions for provisioning, Realtime for live "
              "navigation, and Mother Grid CSV import that upserts on belt and column. A documented AWS migration target uses Cognito, "
              "RDS PostgreSQL, an EC2 API, S3 exports and Redshift for reporting only.")
    panel(svg, accent=RED_HI)
    header(svg, "CAMPGRIDS · ARCHITECTURE", "From a spreadsheet to a role-based platform", color=RED_HI)
    mk, mr, ms = arrow_marker(svg, BLUE), arrow_marker(svg, RED_HI), arrow_marker(svg, STEEL)
    group(svg, 28, 116, 1144, 110, "CONTENT PIPELINE", BLUE, dashed=False)
    c1 = node(svg, 48, 138, 220, 70, "Curriculum workbook", "Excel · hyperlink targets", ICE)
    c2 = node(svg, 300, 138, 240, 70, "generateCampgrids.py", "reads links · matches images", BLUE)
    c3 = node(svg, 572, 138, 230, 70, "Generated campData", "script.js data block", BLUE)
    c4 = node(svg, 834, 138, 318, 70, "Static site (Vercel)", "grid · camps · galleries · partner pages", WHITE)
    for a, b in ((c1, c2), (c2, c3), (c3, c4)):
        edge(svg, [R(a), L(b)], BLUE, mk)
    group(svg, 28, 256, 1144, 150, "ACCOUNTS + ADMINISTRATION  ·  SUPABASE", RED_HI, dashed=False)
    u1 = node(svg, 48, 278, 220, 50, "Students", "class code + username", ICE, title_size=13, sub_size=10.5)
    u2 = node(svg, 48, 338, 220, 50, "Teachers / MSI staff", "password + emailed OTP", ICE, title_size=13, sub_size=10.5)
    au = node(svg, 300, 300, 170, 70, "Supabase Auth", "role-based sessions", RED_HI)
    db = node(svg, 502, 286, 300, 98, "Postgres + RLS", "RPCs: set_class_grid_cells (belt-run rule), partner_page · upsert on (belt, column)", RED_HI)
    ef = node(svg, 834, 278, 318, 50, "Edge Functions", "provision-students / teachers · is_admin()", WHITE, title_size=13, sub_size=10.5)
    rt = node(svg, 834, 338, 318, 50, "Realtime", "admin edits update open browsers", WHITE, title_size=13, sub_size=10.5)
    edge(svg, [R(u1), L(au)], RED_HI, mr)
    edge(svg, [R(u2), L(au)], RED_HI, mr)
    edge(svg, [R(au), L(db)], RED_HI, mr)
    edge(svg, [L(ef), (802, 318)], RED_HI, mr)
    edge(svg, [(802, 352), L(rt)], RED_HI, mr)
    edge(svg, [B(c4), (993, 278)], STEEL, ms, dashed=True)
    group(svg, 28, 436, 1144, 50, "DOCUMENTED AWS TARGET (CLOUDFORMATION, NOT LIVE)", STEEL)
    svg.text(600, 469, "Cognito (credentials + MFA)  ·  RDS PostgreSQL (source of truth)  ·  EC2 API  ·  S3 encrypted exports  ·  Redshift (reporting only)",
             "mono", 12, STEEL, "middle")
    footnote(svg, 508, "DESIGN DECISION", "Re-imports deactivate cells instead of deleting them, so teachers' class selections survive.", color=RED_HI)
    svg.save(OUT / "architecture" / "campgrids.svg")


# ═══ Skills matrix ════════════════════════════════════════════════════════

def skills():
    cols = DATA["skills"]
    W, colw, gap, x0, top = 1200, 212, 15, 40, 140
    layout = []
    for c in cols:
        rows, y = [], 0
        for name, ev in c["items"]:
            lines = wrap(name, colw - 30, "sanssemi", 13)
            evl = wrap("→ " + ev, colw - 30, "mono", 10.5)
            rows.append((lines, evl, y))
            y += len(lines) * 17 + len(evl) * 14 + 12
        layout.append((rows, y))
    inner = max(h for _, h in layout)
    H = top + 70 + inner + 40
    svg = Svg(W, int(H), "Engineering capability matrix",
              "Capabilities grouped into five areas, each paired with the project that demonstrates it. "
              + " ".join(f"{c['title']}: " + "; ".join(f"{n} ({e})" for n, e in c["items"]) + "." for c in cols))
    panel(svg, accent=RED_HI)
    header(svg, "CAPABILITY MATRIX", "What I build with, and where you can see it", color=RED_HI,
           sub="Every capability links to a project. No skill bars, no self-ratings.")
    for i, (c, (rows, _)) in enumerate(zip(cols, layout)):
        x = x0 + i * (colw + gap)
        col = c["color"]
        svg.add(f'<rect x="{x}" y="{top}" width="{colw}" height="{H - top - 30}" rx="14" fill="{PANEL}" fill-opacity=".85" stroke="{LINE}"/>')
        svg.add(f'<rect x="{x}" y="{top}" width="{colw}" height="46" rx="14" fill="{col}" fill-opacity=".12"/>')
        svg.add(f'<rect x="{x}" y="{top + 44}" width="{colw}" height="2" fill="{col}" opacity=".8"/>')
        svg.text(x + 16, top + 29, c["title"], "monobold", 10.5, col, ls=1.1)
        for lines, evl, y in rows:
            yy = top + 76 + y
            svg.add(f'<rect x="{x + 16}" y="{yy - 9}" width="5" height="5" rx="1" fill="{col}"/>')
            for j, line in enumerate(lines):
                svg.text(x + 28, yy - 3 + j * 17, line, "sanssemi", 13, WHITE)
            for j, line in enumerate(evl):
                svg.text(x + 28, yy + 13 + (len(lines) - 1) * 17 + j * 14, line, "mono", 10.5, DIM)
    svg.save(OUT / "diagrams" / "capabilities.svg")


# ═══ Leadership ═══════════════════════════════════════════════════════════

def leadership():
    roles = DATA["leadership"]
    W, cw, ch, gap, x0, top = 1200, 362, 196, 17, 44, 140
    rows = math.ceil(len(roles) / 3)
    H = top + rows * (ch + gap) + 104
    svg = Svg(W, H, "Leadership and impact",
              "Leadership roles: " + "; ".join(f"{r['role']}, {r['org']}: {r['body']}" for r in DATA["leadership"])
              + " Recognition: " + "; ".join(f"{a}: {b}" for a, b in DATA["recognition"]))
    panel(svg, accent=RED_HI)
    header(svg, "BEYOND THE CODE", "Engineering leadership and impact", color=RED_HI,
           sub="Roles where I set technical direction, teach, and ship with teams.")
    for i, r in enumerate(roles):
        x = x0 + (i % 3) * (cw + gap)
        y = top + (i // 3) * (ch + gap)
        c = r["color"]
        svg.add(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="14" fill="{PANEL}" fill-opacity=".9" stroke="{LINE}"/>')
        svg.add(f'<rect x="{x}" y="{y + 18}" width="3" height="{ch - 36}" rx="1.5" fill="{c}"/>')
        svg.text(x + 22, y + 32, r["when"], "monobold", 10, DIM, ls=1.4)
        svg.text(x + 22, y + 64, r["role"], "displaysemi", 22, WHITE, ls=-.3)
        svg.text(x + 22, y + 88, r["org"], "sanssemi", 14.5, c)
        lines = wrap(r["body"], cw - 44, "sans", 13.5)
        if len(lines) > 4:
            raise ValueError(f"leadership body too long: {r['org']}")
        for j, line in enumerate(lines):
            svg.text(x + 22, y + 118 + j * 19.5, line, "sans", 13.5, STEEL)
    ry = top + rows * (ch + gap) + 12
    svg.add(f'<rect x="{x0}" y="{ry}" width="{W - 2 * x0}" height="62" rx="12" fill="{NAVY}" stroke="{LINE}"/>')
    colw = (W - 2 * x0) / len(DATA["recognition"])
    for i, (lab, txt) in enumerate(DATA["recognition"]):
        rx = x0 + 18 + i * colw
        cwid = chip(svg, rx, ry + 19, lab, RED_HI if lab == "WINNER" else BLUE, size=10, h=24)
        lines = wrap(txt, colw - cwid - 40, "sans", 13)
        if len(lines) > 2:
            raise ValueError(f"recognition text too long: {txt}")
        base = ry + 36 - (len(lines) - 1) * 8.5
        for j, line in enumerate(lines):
            svg.text(rx + cwid + 10, base + j * 17, line, "sans", 13, ICE)
    svg.save(OUT / "diagrams" / "leadership.svg")


# ═══ Timeline ═════════════════════════════════════════════════════════════

def timeline():
    items = DATA["timeline"]
    W, H, axis = 1200, 470, 262
    svg = Svg(W, H, "Engineering timeline 2023–2027",
              "Milestones: " + "; ".join(f"{y}: {t}, {b}" for y, t, b, _ in items))
    panel(svg, accent=BLUE)
    header(svg, "TRAJECTORY", "How the work and the responsibility grew", color=BLUE)
    x0, x1 = 90, 1110
    g = svg.uid("ax")
    svg.defs.append(f'<linearGradient id="{g}"><stop offset="0" stop-color="{BLUE}"/><stop offset="1" stop-color="{RED_HI}"/></linearGradient>')
    svg.add(f'<path d="M{x0 - 40} {axis}H{x1 + 40}" stroke="url(#{g})" stroke-width="2.5"/>')
    svg.add(f'<path d="M{x0 - 40} {axis}H{x1 + 40}" stroke="{ICE}" stroke-width="2.5" class="flowslow" opacity=".6"/>')
    step = (x1 - x0) / (len(items) - 1)
    last_year = None
    for i, (year, title, body, tone) in enumerate(items):
        x = x0 + i * step
        c = RED_HI if tone == "red" else BLUE
        up = i % 2 == 0
        if year != last_year:
            svg.add(f'<rect x="{x - 22}" y="{axis - 11}" width="44" height="22" rx="11" fill="{NAVY}" stroke="{c}"/>')
            svg.text(x, axis + 4.5, year, "monobold", 11, c, "middle")
            last_year = year
        else:
            svg.add(f'<circle cx="{x}" cy="{axis}" r="6" fill="{NAVY}" stroke="{c}" stroke-width="2"/>'
                    f'<circle cx="{x}" cy="{axis}" r="2.5" fill="{c}"/>')
        sy0, sy1 = (axis - 14, axis - 46) if up else (axis + 14, axis + 46)
        svg.add(f'<path d="M{x} {sy0}V{sy1}" stroke="{c}" stroke-opacity=".6" stroke-dasharray="2 3"/>')
        lines = wrap(body, 182, "sans", 12)
        if len(lines) > 4:
            raise ValueError(f"timeline body too long: {title}")
        if up:
            ty = axis - 56 - len(lines) * 16 - 4
        else:
            ty = axis + 66
        svg.text(x, ty, title, "sanssemi", 13.5, WHITE, "middle")
        for j, line in enumerate(lines):
            svg.text(x, ty + 19 + j * 16, line, "sans", 12, STEEL, "middle")
    svg.text(W - 44, H - 22, "Dates from danishnadar.com, Illinois Tech and public repositories", "mono", 10, DIM, "end")
    svg.save(OUT / "diagrams" / "timeline.svg")


def main():
    build_hero.build().save(OUT / "hero.svg")
    build_hero.build(static=True).save(OUT / "hero-static.svg")
    buttons()
    pipeline()
    for p in DATA["flagships"]:
        flagship_card(p)
    for g in DATA["groups"]:
        for p in g["projects"]:
            compact_card(p)
    arch_taloncv()
    arch_morph()
    arch_observe()
    arch_campgrids()
    skills()
    leadership()
    timeline()
    for f in sorted(OUT.rglob("*.svg")):
        print(f"{f.relative_to(ROOT)}  {f.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
