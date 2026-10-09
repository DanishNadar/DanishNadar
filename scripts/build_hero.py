"""Hero banner: identity on the left, an autonomous EV perceiving its scene on the right.

The vehicle is an original fastback silhouette (no manufacturer styling or
logos). Perception overlays are visual metaphors, not claims about any one
project. Writes assets/hero.svg (animated) and assets/hero-static.svg.
"""
from __future__ import annotations

from svgkit import (BLUE, DIM, ICE, LINE, NAVY, RED, RED_HI, ROOT, STEEL, WHITE,
                    Svg, measure, panel, polar)

W, H = 1200, 500
GROUND = 420
FRONT_WHEEL, REAR_WHEEL, WHEEL_Y, WHEEL_R = 962, 712, 384, 35
SENSOR = (868, 300)          # in vehicle coordinates
CAR_SCALE, CAR_PIVOT = .9, (1048, 420)
SENSOR_T = (CAR_PIVOT[0] + CAR_SCALE * (SENSOR[0] - CAR_PIVOT[0]), CAR_PIVOT[1] + CAR_SCALE * (SENSOR[1] - CAR_PIVOT[1]))

HERO_CSS = """
.shimmer{animation:shimmer 7s ease-in-out infinite}
@keyframes shimmer{0%,100%{opacity:1}50%{opacity:.86}}
.wave{transform-origin:886px 312px;animation:wave 3.6s ease-out infinite;opacity:.35}
.w2{animation-delay:1.2s}.w3{animation-delay:2.4s}
@keyframes wave{0%{opacity:0;transform:scale(.35)}15%{opacity:.9}100%{opacity:0;transform:scale(1.15)}}
.spin{transform-box:fill-box;transform-origin:center;animation:spin 1.4s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.lane{stroke-dasharray:38 30;animation:lane 1.1s linear infinite}
@keyframes lane{to{stroke-dashoffset:68}}
.traj{stroke-dasharray:6 8;animation:flow 1.2s linear infinite}
.reveal{stroke-dasharray:260;stroke-dashoffset:0;animation:reveal 4.8s ease-in-out infinite}
@keyframes reveal{0%{stroke-dashoffset:260}45%,80%{stroke-dashoffset:0}100%{stroke-dashoffset:-260}}
.node{animation:pulse 2.6s ease-in-out infinite}
.n2{animation-delay:.4s}.n3{animation-delay:.8s}.n4{animation-delay:1.2s}
.glowbar{animation:blink 3s ease-in-out infinite}
.particle{animation:particle 2.6s linear infinite}
.p2{animation-delay:.9s}.p3{animation-delay:1.7s}
@keyframes particle{0%{transform:translateX(0);opacity:0}10%{opacity:1}90%{opacity:1}100%{transform:translateX(150px);opacity:0}}
"""

STATIC_CSS = "*{animation:none!important}"


def skyline(svg: Svg) -> None:
    """Chicago skyline silhouette, abstracted (Willis, Hancock, Trump, Aon, Marina City)."""
    g = svg.uid("sky")
    svg.defs.append(f'<linearGradient id="{g}" x1="0" y1="0" x2="0" y2="1">'
                    f'<stop offset="0" stop-color="#16325A" stop-opacity=".9"/>'
                    f'<stop offset="1" stop-color="#0A1730" stop-opacity=".2"/></linearGradient>')
    base = 404
    blocks = [
        # x, width, height
        (560, 22, 48), (584, 16, 70), (602, 26, 58), (630, 18, 92), (650, 30, 64),
        (684, 20, 118), (706, 26, 84), (736, 18, 66), (756, 24, 102),
        (842, 22, 88), (866, 18, 60), (888, 28, 126), (920, 20, 74),
        (1010, 24, 96), (1036, 18, 70), (1058, 30, 112), (1092, 20, 64), (1114, 26, 90),
        (1142, 18, 58), (1162, 30, 80),
    ]
    parts = [f'<rect x="{x}" y="{base - h}" width="{w}" height="{h}"/>' for x, w, h in blocks]
    # Willis Tower: stepped bundled tubes + twin antennas
    wx = 784
    parts += [f'<rect x="{wx}" y="{base - 150}" width="44" height="150"/>',
              f'<rect x="{wx + 6}" y="{base - 182}" width="32" height="40"/>',
              f'<rect x="{wx + 12}" y="{base - 206}" width="20" height="30"/>',
              f'<rect x="{wx + 14}" y="{base - 236}" width="2.5" height="32"/>',
              f'<rect x="{wx + 27}" y="{base - 230}" width="2.5" height="26"/>']
    # John Hancock: tapered with antennas
    hx = 952
    parts += [f'<path d="M{hx} {base}L{hx + 6} {base - 168}H{hx + 30}L{hx + 36} {base}Z"/>',
              f'<rect x="{hx + 11}" y="{base - 198}" width="2.2" height="32"/>',
              f'<rect x="{hx + 23}" y="{base - 198}" width="2.2" height="32"/>']
    # Trump Tower: stepped spire
    tx = 988
    parts += [f'<path d="M{tx} {base}V{base - 120}H{tx + 4}V{base - 140}H{tx + 8}V{base - 156}H{tx + 12}V{base - 156}'
              f'H{tx + 14}V{base - 190}H{tx + 15.5}V{base - 156}H{tx + 18}V{base - 140}H{tx + 22}V{base - 120}H{tx + 22}V{base}Z"/>']
    # Marina City corn cobs
    for mx in (1126, 1148):
        parts.append(f'<rect x="{mx}" y="{base - 92}" width="16" height="92" rx="8"/>')
    svg.add(f'<g fill="url(#{g})">{"".join(parts)}</g>')
    # sparse window lights
    lights = [(792, 290), (806, 320), (818, 270), (962, 300), (972, 340), (700, 330), (896, 312), (1066, 330), (640, 350)]
    svg.add("".join(f'<rect x="{x}" y="{y}" width="3" height="2" fill="{ICE}" opacity=".35"/>' for x, y in lights))


def road(svg: Svg) -> None:
    m = svg.uid("roadfade")
    svg.defs.append(f'<linearGradient id="{m}" x1="0" x2="1">'
                    f'<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".18" stop-color="#fff" stop-opacity="1"/>'
                    f'<stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>'
                    f'<mask id="{m}m"><rect x="520" y="380" width="680" height="120" fill="url(#{m})"/></mask>')
    seg = svg.uid("seg")
    svg.defs.append(f'<linearGradient id="{seg}" x1="0" x2="1"><stop offset="0" stop-color="{BLUE}" stop-opacity="0"/>'
                    f'<stop offset=".5" stop-color="{BLUE}" stop-opacity=".16"/><stop offset="1" stop-color="{BLUE}" stop-opacity=".04"/></linearGradient>')
    svg.add(f'<g mask="url(#{m}m)">'
            f'<rect x="520" y="404" width="680" height="96" fill="#071226"/>'
            f'<path d="M520 404.5H1200" stroke="{LINE}" stroke-width="1.5"/>'
            # drivable-area segmentation ahead of the vehicle
            f'<path d="M940 426H1200V470H940Z" fill="url(#{seg})"/>'
            f'<path d="M520 474H1200" stroke="{STEEL}" stroke-opacity=".35" stroke-width="2" class="lane"/>'
            f'<path d="M520 496H1200" stroke="{STEEL}" stroke-opacity=".18" stroke-width="2"/>'
            f'</g>')


def lidar(svg: Svg) -> None:
    cx, cy = SENSOR_T
    fov = svg.uid("fov")
    svg.defs.append(f'<radialGradient id="{fov}" cx="{cx}" cy="{cy}" r="320" gradientUnits="userSpaceOnUse">'
                    f'<stop offset="0" stop-color="{BLUE}" stop-opacity=".22"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>')
    a0, a1 = -34, 22
    x0, y0 = polar(cx, cy, 320, a0)
    x1, y1 = polar(cx, cy, 320, a1)
    svg.add(f'<path d="M{cx} {cy}L{x0:.1f} {y0:.1f}A320 320 0 0 1 {x1:.1f} {y1:.1f}Z" fill="url(#{fov})"/>')
    for r, cls in ((150, "wave"), (150, "wave w2"), (150, "wave w3")):
        ax0, ay0 = polar(cx, cy, r, a0 + 6)
        ax1, ay1 = polar(cx, cy, r, a1 - 4)
        svg.add(f'<path class="{cls}" d="M{ax0:.1f} {ay0:.1f}A{r} {r} 0 0 1 {ax1:.1f} {ay1:.1f}" fill="none" stroke="{BLUE}" stroke-width="2"/>')
    # static range rings
    for r, op in ((210, .28), (290, .16)):
        ax0, ay0 = polar(cx, cy, r, a0 + 6)
        ax1, ay1 = polar(cx, cy, r, a1 - 4)
        svg.add(f'<path d="M{ax0:.1f} {ay0:.1f}A{r} {r} 0 0 1 {ax1:.1f} {ay1:.1f}" fill="none" stroke="{ICE}" stroke-opacity="{op}" stroke-dasharray="2 6"/>')
    # point-cloud returns on the pedestrian and road edge
    pts = [(1118, 360), (1124, 352), (1131, 348), (1137, 356), (1142, 372), (1121, 386), (1139, 392), (1128, 402),
           (1060, 404), (1078, 405), (1096, 404), (1160, 404), (1180, 405)]
    svg.add("".join(f'<circle cx="{x}" cy="{y}" r="1.6" fill="{ICE}" opacity=".8"/>' for x, y in pts))


def pedestrian(svg: Svg) -> None:
    x, base = 1130, 404
    svg.add(f'<g fill="{STEEL}" opacity=".85">'
            f'<circle cx="{x}" cy="{base - 54}" r="6"/>'
            f'<path d="M{x - 7} {base - 46}h14l3 24h-4l-1 22h-4l-2-18-2 18h-4l-1-22h-4z"/></g>')
    # bounding box corners
    bx, by, bw, bh, c = x - 18, base - 66, 36, 70, 9
    corners = (f'M{bx} {by + c}V{by}H{bx + c} M{bx + bw - c} {by}H{bx + bw}V{by + c} '
               f'M{bx + bw} {by + bh - c}V{by + bh}H{bx + bw - c} M{bx + c} {by + bh}H{bx}V{by + bh - c}')
    svg.add(f'<path d="{corners}" fill="none" stroke="{RED_HI}" stroke-width="2" class="blink"/>')
    svg.add(f'<rect x="{bx}" y="{by - 18}" width="70" height="15" rx="3" fill="{RED}" fill-opacity=".9"/>')
    svg.text(bx + 5, by - 7, "PERSON·T07", "monobold", 9, WHITE, ls=.6)


def trajectory(svg: Svg) -> None:
    # planned path: eases left, away from the pedestrian's side of the road
    d = "M990 446C1050 446 1100 450 1200 452"
    svg.add(f'<path d="{d}" fill="none" stroke="{BLUE}" stroke-width="2.5" class="reveal"/>')
    svg.add(f'<path d="{d}" fill="none" stroke="{ICE}" stroke-opacity=".45" stroke-width="1" class="traj"/>')
    for i, (x, y) in enumerate(((1052, 446.5), (1100, 448.5), (1150, 450.5))):
        svg.add(f'<rect x="{x - 9}" y="{y - 5}" width="18" height="10" rx="2" fill="none" stroke="{BLUE}" stroke-opacity="{.6 - i * .17:.2f}"/>')


def vehicle(svg: Svg) -> None:
    body, glass, shade, rim = svg.uid("body"), svg.uid("glass"), svg.uid("shade"), svg.uid("rim")
    svg.defs.append(
        f'<linearGradient id="{body}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{WHITE}"/><stop offset=".42" stop-color="#C9D8EA"/>'
        f'<stop offset=".78" stop-color="#7F96B4"/><stop offset="1" stop-color="#3B5070"/></linearGradient>'
        f'<linearGradient id="{glass}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="#1B3A63"/><stop offset=".55" stop-color="#0A1830"/><stop offset="1" stop-color="#050B18"/></linearGradient>'
        f'<radialGradient id="{shade}" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#000" stop-opacity=".7"/>'
        f'<stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="{rim}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#B9CBE0"/>'
        f'<stop offset="1" stop-color="#3A4F6E"/></linearGradient>')
    px, py = CAR_PIVOT
    svg.add(f'<g transform="translate({px} {py}) scale({CAR_SCALE}) translate({-px} {-py})">')
    svg.add(f'<ellipse cx="840" cy="{GROUND}" rx="230" ry="12" fill="url(#{shade})"/>')

    def arch(cx):
        import math
        dx = math.sqrt(47 ** 2 - (398 - WHEEL_Y) ** 2)
        return cx + dx, cx - dx

    fr, fl = arch(FRONT_WHEEL)
    rr, rl = arch(REAR_WHEEL)
    outline = (
        f"M650 392V374C650 362 654 354 664 350"
        f"C702 340 742 320 792 307C832 297 880 296 914 305"
        f"C952 315 986 335 1012 347C1032 353 1044 361 1048 373V388"
        f"C1048 394 1042 398 1034 398H{fr:.1f}"
        f"A47 47 0 1 0 {fl:.1f} 398H{rr:.1f}"
        f"A47 47 0 1 0 {rl:.1f} 398H658C653 398 650 396 650 392Z"
    )
    svg.add(f'<path d="{outline}" fill="url(#{body})" stroke="#E6F0FB" stroke-opacity=".6" stroke-width="1"/>')
    # rocker shadow and character line
    svg.add(f'<path d="M760 390H{fl - 4:.1f}V397H760Z" fill="#22344F" opacity=".75"/>')
    svg.add(f'<path d="M668 364C780 360 900 360 1036 366" fill="none" stroke="#FFFFFF" stroke-opacity=".55" stroke-width="1.2"/>')
    # greenhouse
    svg.add(f'<path d="M706 347C742 331 774 317 804 311C844 303 880 303 906 310C936 319 962 332 986 346Z" fill="url(#{glass})"/>')
    svg.add('<path d="M736 336C780 318 830 309 880 309" fill="none" stroke="#7FC4FF" stroke-opacity=".35" stroke-width="2"/>')
    svg.add('<path d="M852 305V347" stroke="#9EB3CD" stroke-opacity=".5" stroke-width="3"/>')
    # mirror, door handles
    svg.add('<path d="M972 340l14-2 4 6-16 2z" fill="#7F96B4"/>')
    svg.add('<path d="M806 356h16M902 356h16" stroke="#5E7595" stroke-width="2" stroke-linecap="round"/>')
    # lighting: full-width front bar (ice) and rear bar (red)
    svg.add(f'<path d="M1016 352C1028 355 1038 359 1045 366" fill="none" stroke="{WHITE}" stroke-width="3" stroke-linecap="round" class="glowbar"/>')
    svg.add(f'<path d="M651 356C655 352 660 350 668 348" fill="none" stroke="{RED_HI}" stroke-width="3.5" stroke-linecap="round" class="glowbar"/>')
    # roof sensor puck
    cx, cy = SENSOR
    svg.add(f'<rect x="{cx - 12}" y="{cy - 2}" width="24" height="7" rx="3.5" fill="#0E2140" stroke="{BLUE}"/>')
    svg.add(f'<circle cx="{cx}" cy="{cy + 1.5}" r="2" fill="{BLUE}" class="blink"/>')

    for wx, cls in ((FRONT_WHEEL, "spin"), (REAR_WHEEL, "spin")):
        spokes = "".join(
            f'<path d="M{wx} {WHEEL_Y}L{wx + 22 * __import__("math").cos(a):.1f} {WHEEL_Y + 22 * __import__("math").sin(a):.1f}" stroke="#0E1A2E" stroke-width="5" stroke-linecap="round"/>'
            for a in [i * 2 * 3.14159 / 5 for i in range(5)])
        svg.add(f'<circle cx="{wx}" cy="{WHEEL_Y}" r="{WHEEL_R}" fill="#0A111D" stroke="#1C2A40" stroke-width="2"/>'
                f'<circle cx="{wx}" cy="{WHEEL_Y}" r="25" fill="url(#{rim})"/>'
                f'<g class="{cls}">{spokes}<circle cx="{wx}" cy="{WHEEL_Y}" r="25" fill="none" stroke="#0E1A2E" stroke-width="2" stroke-dasharray="8 7"/></g>'
                f'<circle cx="{wx}" cy="{WHEEL_Y}" r="5" fill="#0E1A2E" stroke="{BLUE}" stroke-opacity=".7"/>')
    svg.add("</g>")


def fusion_panel(svg: Svg) -> None:
    x, y, w, h = 990, 34, 176, 142
    svg.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#0A1A31" fill-opacity=".92" stroke="{LINE}"/>')
    svg.text(x + 14, y + 22, "SENSOR FUSION", "monobold", 10, ICE, ls=1.6)
    svg.add(f'<circle cx="{x + w - 16}" cy="{y + 18}" r="3" fill="{RED_HI}" class="pulse"/>')
    ins = ["CAM", "LIDAR", "RADAR"]
    cols = [(x + 50, [y + 50, y + 80, y + 110]), (x + 90, [y + 44, y + 68, y + 92, y + 116]), (x + 128, [y + 64, y + 96])]
    lines = []
    for (x0, ys0), (x1, ys1) in zip(cols, cols[1:]):
        for a in ys0:
            for b in ys1:
                lines.append(f'<path d="M{x0} {a}L{x1} {b}" stroke="{BLUE}" stroke-opacity=".28"/>')
    svg.add("".join(lines))
    # highlighted active path
    svg.add(f'<path d="M{x + 50} {y + 80}L{x + 90} {y + 68}L{x + 128} {y + 64}" fill="none" stroke="{ICE}" stroke-width="1.6" class="flow"/>')
    k = 0
    for ci, (cx, ys) in enumerate(cols):
        for cy in ys:
            k += 1
            color = RED_HI if ci == 2 and cy == ys[0] else BLUE
            svg.add(f'<circle cx="{cx}" cy="{cy}" r="4.5" fill="{NAVY}" stroke="{color}" stroke-width="1.6" class="node n{k % 4 + 1}"/>')
    for lab, cy in zip(ins, cols[0][1]):
        svg.text(x + 40, cy + 3.5, lab, "mono", 8.5, STEEL, "end")
    svg.text(x + 137, y + 67.5, "plan", "mono", 8.5, RED_HI)
    svg.text(x + 137, y + 99.5, "track", "mono", 8.5, STEEL)
    # data link from roof sensor to the fusion panel
    cx, cy = SENSOR_T
    svg.add(f'<path d="M{cx} {cy - 4}C{cx + 10} 230 940 190 {x} {y + 112}" fill="none" stroke="{BLUE}" stroke-opacity=".7" stroke-width="1.4" class="flow"/>')


def identity(svg: Svg) -> None:
    ice, red, rule = svg.uid("ice"), svg.uid("red"), svg.uid("rule")
    svg.defs.append(
        f'<linearGradient id="{ice}" x1="0" y1="0" x2="1" y2=".25"><stop offset="0" stop-color="{WHITE}"/>'
        f'<stop offset=".45" stop-color="{ICE}"/><stop offset="1" stop-color="{BLUE}"/></linearGradient>'
        f'<linearGradient id="{red}" x1="0" y1="0" x2="1" y2=".25"><stop offset="0" stop-color="#FF6B76"/>'
        f'<stop offset=".5" stop-color="{RED_HI}"/><stop offset="1" stop-color="#C4183A"/></linearGradient>'
        f'<linearGradient id="{rule}"><stop offset="0" stop-color="{BLUE}"/><stop offset="1" stop-color="{RED}"/></linearGradient>')
    x = 60
    # brand label
    svg.add('<g>')
    svg.add(f'<rect x="{x}" y="52" width="10" height="10" fill="{RED}"/>'
            f'<rect x="{x + 13}" y="52" width="10" height="10" fill="none" stroke="{BLUE}" stroke-width="1.5"/>')
    label = "INTELLIGENT SYSTEMS LAB"
    svg.text(x + 36, 62, label, "monobold", 13, ICE, ls=2.6)
    lw = measure(label, "monobold", 13, 2.6)
    svg.text(x + 36 + lw + 8, 62, "/ PERCEIVE · REASON · ACT", "mono", 13, STEEL, ls=2.2)
    svg.add('</g>')
    # name
    svg.add('<g class="shimmer">')
    svg.text(x - 5, 178, "DANISH", "display", 108, f"url(#{ice})", ls=-3)
    svg.text(x - 5, 284, "NADAR", "display", 108, f"url(#{red})", ls=-3)
    svg.add('</g>')
    svg.add(f'<rect x="{x}" y="306" width="128" height="3" rx="1.5" fill="url(#{rule})"/>')
    # role line
    parts = [("AI Engineer", "sanssemi", WHITE), ("  •  ", "sanssemi", RED_HI),
             ("Autonomous Systems", "sanssemi", WHITE), ("  •  ", "sanssemi", RED_HI),
             ("Applied Machine Learning", "sanssemi", WHITE)]
    svg.rich(x, 348, parts, size=19.5)
    svg.rich(x, 386, [("Building intelligent systems that ", "sans", STEEL), ("perceive", "sanssemi", BLUE),
                      (", ", "sans", STEEL), ("reason", "sanssemi", ICE), (", and ", "sans", STEEL),
                      ("act", "sanssemi", RED_HI), (".", "sans", STEEL)], size=20)
    # meta line
    svg.add('<g>')
    meta = [("CHICAGO, IL", ICE), ("ILLINOIS TECH", ICE), ("B.S. + M.A.S. ARTIFICIAL INTELLIGENCE", STEEL)]
    mx = x
    for i, (m, c) in enumerate(meta):
        if i:
            svg.add(f'<rect x="{mx + 8}" y="446" width="5" height="5" fill="{RED}" transform="rotate(45 {mx + 10.5} 448.5)"/>')
            mx += 22
        svg.text(mx, 453, m, "mono", 12, c, ls=1.6)
        mx += measure(m, "mono", 12, 1.6)
    svg.add('</g>')


def hud(svg: Svg) -> None:
    svg.text(990, 200, "LOCALIZED  41.88°N 87.63°W", "mono", 10, DIM, ls=1)
    svg.add(f'<path d="M990 210H1166" stroke="{LINE}"/>')
    svg.text(990, 226, "PLANNER  lane-keep · yield", "mono", 10, DIM, ls=1)


def particles(svg: Svg) -> None:
    for i, y in enumerate((436, 456, 446)):
        svg.add(f'<circle cx="1010" cy="{y}" r="2" fill="{ICE}" class="particle p{i + 1}"/>')


def build(static: bool = False) -> Svg:
    svg = Svg(W, H, "Danish Nadar — AI Engineer, Autonomous Systems, Applied Machine Learning",
              "Banner with the name Danish Nadar, the tagline 'Building intelligent systems that perceive, reason, and act', "
              "and an illustrated electric vehicle sensing a pedestrian with LiDAR-style scan arcs, a bounding box, "
              "a sensor-fusion network panel and a planned trajectory in front of a Chicago skyline.")
    svg.css.append(HERO_CSS)
    if static:
        svg.css.append(STATIC_CSS)
    clip = svg.uid("clip")
    svg.defs.append(f'<clipPath id="{clip}"><rect width="{W}" height="{H}" rx="26"/></clipPath>')
    svg.add(f'<g clip-path="url(#{clip})">')
    panel(svg, rx=26)
    glow = svg.uid("glow")
    svg.defs.append(f'<radialGradient id="{glow}" cx="850" cy="330" r="360" gradientUnits="userSpaceOnUse">'
                    f'<stop offset="0" stop-color="{BLUE}" stop-opacity=".18"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>')
    svg.add(f'<rect width="{W}" height="{H}" rx="26" fill="url(#{glow})"/>')
    skyline(svg)
    road(svg)
    lidar(svg)
    trajectory(svg)
    particles(svg)
    vehicle(svg)
    pedestrian(svg)
    fusion_panel(svg)
    hud(svg)
    identity(svg)
    svg.add("</g>")
    svg.add(f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="26" fill="none" stroke="{LINE}"/>')
    return svg


if __name__ == "__main__":
    print(build().save(ROOT / "assets" / "hero.svg"))
    print(build(static=True).save(ROOT / "assets" / "hero-static.svg"))
