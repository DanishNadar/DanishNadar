"""Profile quality gate.

    python scripts/validate.py            # offline checks (run in CI)
    python scripts/validate.py --online   # also checks every external link

Checks: SVG well-formedness and size budget, no external resources inside
SVGs (GitHub's proxy blocks them), every local README reference exists,
README markers are intact, alt text on every image, and (online) that each
external link answers with a non-error status.
"""
from __future__ import annotations

import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
MAX_SVG_KB = 120
errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)
    print(f"  FAIL {msg}")


def check_svgs() -> None:
    svgs = sorted((ROOT / "assets").rglob("*.svg"))
    for f in svgs:
        rel = f.relative_to(ROOT)
        try:
            root = ET.parse(f).getroot()
        except ET.ParseError as e:
            fail(f"{rel}: invalid XML ({e})")
            continue
        kb = f.stat().st_size / 1024
        if kb > MAX_SVG_KB:
            fail(f"{rel}: {kb:.0f} KB exceeds {MAX_SVG_KB} KB budget")
        text = f.read_text(encoding="utf-8")
        if re.search(r'(?:href|src)="https?://', text) or "@import" in text or "<script" in text:
            fail(f"{rel}: references an external resource or script")
        ns = "{http://www.w3.org/2000/svg}"
        if root.find(f"{ns}title") is None:
            fail(f"{rel}: missing <title> for accessibility")
    print(f"  ok {len(svgs)} SVGs parsed")


def check_readme() -> list[str]:
    text = README.read_text(encoding="utf-8")
    for name in ("RECENT", "INSIGHT"):
        if f"<!-- {name}:START -->" not in text or f"<!-- {name}:END -->" not in text:
            fail(f"README missing {name} markers")
    for img in re.findall(r"<img\b[^>]*>", text):
        if 'alt="' not in img or re.search(r'alt=""', img):
            fail(f"image without alt text: {img[:80]}")
    refs = re.findall(r'(?:src|srcset|href)="([^"#][^"]*)"', text) + re.findall(r"\]\(([^)#][^)]*)\)", text)
    local = [r for r in refs if not r.startswith(("http://", "https://", "mailto:"))]
    for r in sorted(set(local)):
        if not (ROOT / r).exists():
            fail(f"README references missing file: {r}")
    anchors = set(re.findall(r'href="#([^"]+)"', text)) | set(re.findall(r"\]\(#([^)]+)\)", text))
    slugs = {re.sub(r"[^\w\- ]", "", h.strip().lower()).replace(" ", "-") for h in re.findall(r"^#{2,4} (.+)$", text, re.M)}
    for a in sorted(anchors):
        if a not in slugs:
            fail(f"README anchor #{a} has no matching heading")
    print(f"  ok README: {len(set(local))} local refs, {len(anchors)} anchors checked")
    return sorted({r for r in refs if r.startswith("http")})


def check_links(urls: list[str]) -> None:
    for u in urls:
        if "linkedin.com" in u:  # LinkedIn rejects bots with HTTP 999; verified manually
            continue
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 profile-link-check"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                code = r.status
        except urllib.error.HTTPError as e:
            code = e.code
        except Exception as e:  # noqa: BLE001
            fail(f"{u}: {e}")
            continue
        if code >= 400:
            fail(f"{u}: HTTP {code}")
    print(f"  ok {len(urls)} external links checked")


if __name__ == "__main__":
    print("Validating profile...")
    check_svgs()
    urls = check_readme()
    if "--online" in sys.argv:
        check_links(urls)
    if errors:
        print(f"\n{len(errors)} problem(s) found")
        sys.exit(1)
    print("\nAll checks passed")
