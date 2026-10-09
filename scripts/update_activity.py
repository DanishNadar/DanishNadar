"""Refresh the live parts of the profile. Run daily by .github/workflows/update-profile.yml.

  * README "recently active" table (public, non-fork, non-archived, curated repos)
  * assets/live/contributions.svg — red/blue contribution map from the GraphQL calendar
  * assets/live/insight.svg       — weekly rotating design decision from data/insights.json

Needs GITHUB_TOKEN (the Actions token is enough; locally: GITHUB_TOKEN=$(gh auth token)).
Every step fails soft: if an API call fails, the previous output is kept.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import urllib.request

from svgkit import (BLUE, DIM, ICE, LINE, NAVY, RED_HI, ROOT, STEEL, WHITE, Svg, chip, measure, panel, wrap)

USER = "DanishNadar"
DATA = json.loads((ROOT / "data" / "profile.json").read_text(encoding="utf-8"))
README = ROOT / "README.md"
LIVE = ROOT / "assets" / "live"
TODAY = dt.datetime.now(dt.timezone.utc).date()


def api(url: str, body: dict | None = None):
    token = os.environ.get("GITHUB_TOKEN", "")
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", f"{USER}-profile-updater")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def replace_block(text: str, name: str, content: str) -> str:
    pattern = re.compile(rf"(<!-- {name}:START -->)(.*?)(<!-- {name}:END -->)", re.S)
    if not pattern.search(text):
        raise SystemExit(f"README is missing the {name} markers")
    return pattern.sub(lambda m: f"{m[1]}\n{content}\n{m[3]}", text)


# ── Recently active repositories ───────────────────────────────────────────

def recent_table() -> str:
    cfg = DATA["activity"]
    repos = api(f"https://api.github.com/users/{USER}/repos?type=owner&sort=pushed&per_page=100")
    rows = []
    for r in repos:
        if r["fork"] or r["archived"] or r["private"] or r["name"] in cfg["exclude"] or r["size"] == 0:
            continue
        desc = cfg["descriptions"].get(r["name"]) or (r["description"] or "").strip()
        if not desc:
            continue  # undocumented repos stay out of the showcase
        pushed = r["pushed_at"][:10]
        lang = r["language"] or "—"
        url = cfg["demos"].get(r["name"])
        demo = f" · [demo]({url})" if url else ""
        rows.append(f"| [**{r['name']}**]({r['html_url']}){demo} | {desc} | `{lang}` | {pushed} |")
        if len(rows) == 6:
            break
    head = "| Repository | What it is | Language | Last push |\n|:--|:--|:--|:--|"
    return f"{head}\n" + "\n".join(rows) + f"\n\n_Auto-updated {TODAY.isoformat()} by GitHub Actions · forks, archives and coursework stubs are filtered out_"


# ── Contribution map ──────────────────────────────────────────────────────

GQL = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
totalContributions weeks{contributionDays{date contributionCount weekday}}}}}}"""


def contributions_svg() -> Svg:
    res = api("https://api.github.com/graphql", {"query": GQL, "variables": {"login": USER}})
    cal = res["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    counts = sorted(d["contributionCount"] for d in days if d["contributionCount"] > 0)

    def q(p):
        return counts[min(len(counts) - 1, int(p * len(counts)))] if counts else 0

    t1, t2, t3, hot = q(.25), q(.5), q(.75), q(.95)
    streak = best = 0
    for d in days:
        streak = streak + 1 if d["contributionCount"] else 0
        best = max(best, streak)
    by_wd = [0] * 7
    for d in days:
        by_wd[d["weekday"]] += d["contributionCount"]
    busiest = ["Sundays", "Mondays", "Tuesdays", "Wednesdays", "Thursdays", "Fridays", "Saturdays"][by_wd.index(max(by_wd))]
    active = sum(1 for d in days if d["contributionCount"])

    W, H, cell, gapc, gx, gy = 1200, 260, 13, 3, 44, 96
    svg = Svg(W, H, "Contribution activity, last 12 months",
              f"{cal['totalContributions']} contributions in the last year across {active} active days; "
              f"longest streak {best} days; most active on {busiest}.")
    panel(svg, accent=BLUE)
    svg.add(f'<rect x="{gx}" y="34" width="8" height="8" fill="{BLUE}"/>')
    svg.text(gx + 18, 42, "CONTRIBUTION SIGNAL  ·  LAST 12 MONTHS", "monobold", 12, BLUE, ls=2.2)
    svg.text(gx, 74, f"{cal['totalContributions']:,} contributions", "displaysemi", 24, WHITE)
    tw = measure(f"{cal['totalContributions']:,} contributions", "displaysemi", 24)
    svg.text(gx + tw + 14, 74, f"· {active} active days · longest streak {best} days · most active on {busiest}", "sans", 14, STEEL)
    palette = ["#0F2140", "#123E6B", "#1F6FB5", BLUE, ICE]
    month_seen = set()
    for wi, w in enumerate(weeks[-53:]):
        x = gx + wi * (cell + gapc)
        for d in w["contributionDays"]:
            c = d["contributionCount"]
            lvl = 0 if c == 0 else 1 if c <= t1 else 2 if c <= t2 else 3 if c <= t3 else 4
            color = RED_HI if c and c >= hot and hot > 0 else palette[lvl]
            y = gy + d["weekday"] * (cell + gapc)
            svg.add(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{color}"/>')
        first = w["contributionDays"][0]["date"]
        m = first[:7]
        if m not in month_seen and int(first[8:]) <= 7:
            month_seen.add(m)
            svg.text(x, gy + 7 * (cell + gapc) + 16, dt.date.fromisoformat(first).strftime("%b").upper(), "mono", 10, DIM, ls=1)
    lx = gx + 53 * (cell + gapc) + 24
    svg.text(lx, gy + 10, "INTENSITY", "monobold", 10, DIM, ls=1.4)
    for i, c in enumerate(palette):
        svg.add(f'<rect x="{lx + i * 18}" y="{gy + 22}" width="13" height="13" rx="3" fill="{c}"/>')
    svg.add(f'<rect x="{lx}" y="{gy + 50}" width="13" height="13" rx="3" fill="{RED_HI}"/>')
    svg.text(lx + 20, gy + 61, "top 5% days", "mono", 10.5, STEEL)
    svg.text(lx, gy + 92, "Public + private counts", "mono", 10, DIM)
    svg.text(lx, gy + 106, "as shown by GitHub.", "mono", 10, DIM)
    svg.text(W - 44, H - 18, f"Generated {TODAY.isoformat()} from the GitHub GraphQL API", "mono", 10, DIM, "end")
    return svg


# ── Weekly design decision ────────────────────────────────────────────────

def insight() -> tuple[Svg, dict]:
    items = json.loads((ROOT / "data" / "insights.json").read_text(encoding="utf-8"))
    year, week, _ = TODAY.isocalendar()
    it = items[(year * 53 + week) % len(items)]
    W, H = 1200, 200
    svg = Svg(W, H, f"Design decision: {it['title']}", f"{it['title']}. {it['body']} From {it['project']}.")
    panel(svg, accent=RED_HI)
    svg.add(f'<rect x="44" y="34" width="8" height="8" fill="{RED_HI}"/>')
    svg.text(62, 42, f"DESIGN DECISION LOG  ·  WEEK {week:02d}", "monobold", 12, RED_HI, ls=2.2)
    pw = measure(it["project"], "mono", 11) + 20
    chip(svg, W - 44 - pw, 26, it["project"], BLUE, size=11, h=24)
    svg.text(44, 88, it["title"], "displaysemi", 27, WHITE, ls=-.3)
    for i, line in enumerate(wrap(it["body"], W - 88, "sans", 16)[:3]):
        svg.text(44, 122 + i * 23, line, "sans", 16, STEEL)
    svg.text(W - 44, H - 18, "rotates weekly · every entry comes from real project code →", "mono", 10, DIM, "end")
    return svg, it


def main() -> int:
    text = README.read_text(encoding="utf-8")
    ok = True
    try:
        text = replace_block(text, "RECENT", recent_table())
    except Exception as e:  # noqa: BLE001 — keep the old table on any API failure
        print(f"recent work skipped: {e}", file=sys.stderr)
        ok = False
    try:
        contributions_svg().save(LIVE / "contributions.svg")
    except Exception as e:  # noqa: BLE001
        print(f"contributions skipped: {e}", file=sys.stderr)
        ok = False
    svg, it = insight()
    svg.save(LIVE / "insight.svg")
    link = (f'<a href="{it["url"]}"><img src="assets/live/insight.svg" width="100%" '
            f'alt="Design decision of the week: {it["title"]}. {it["body"]}"/></a>')
    text = replace_block(text, "INSIGHT", link)
    README.write_text(text, encoding="utf-8")
    print("updated" + ("" if ok else " (with skipped steps)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
