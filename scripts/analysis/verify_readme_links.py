"""Verify every relative link and image target in the root README.md.

Read-only.  Resolves each Markdown link target against the filesystem after
percent-decoding (GitHub encodes spaces in directory names, e.g.
``full_doc_report/figures/Internal%20validation/``).

Exit code 0  -> every relative target resolves
Exit code 1  -> at least one broken target

Usage:
    .venv\\Scripts\\python.exe scripts\\analysis\\verify_readme_links.py
"""
from __future__ import annotations

import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
README = ROOT / "README.md"

LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\(([^)]+)\)")


def main() -> int:
    if not README.exists():
        print(f"FATAL: {README} not found")
        return 1

    text = README.read_text(encoding="utf-8")
    entries = []
    for m in LINK_RE.finditer(text):
        is_img = m.group(1) == "!"
        label = m.group(2)
        target = m.group(3).strip()
        entries.append((is_img, label, target))

    broken: list[str] = []
    external: list[str] = []
    relative = 0

    for is_img, label, target in entries:
        if target.startswith(("http://", "https://")):
            external.append(target)
            continue
        if target.startswith("#"):
            continue
        relative += 1
        decoded = urllib.parse.unquote(target)
        if not (ROOT / decoded).exists():
            broken.append(target)

    print("=" * 68)
    print("README LINK VERIFICATION")
    print("=" * 68)
    print(f"file              : {README.relative_to(ROOT)}")
    print(f"references parsed : {len(entries)}")
    print(f"relative targets  : {relative}")
    print(f"external URLs     : {len(set(external))}")
    print(f"broken            : {len(broken)}")
    print("-" * 68)

    if broken:
        for t in broken:
            print(f"  BROKEN  {t}")
        print("-" * 68)
        print("RESULT: FAIL — one or more relative targets do not resolve.")
        return 1

    print("  all relative targets resolve.")
    print("-" * 68)
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
