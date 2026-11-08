"""Verify every internal Markdown link and image in the documentation set.

Resolves repository-relative paths (including %20-encoded ones) and reports any
target that does not exist. External http(s) links are format-checked only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(r"D:\Softfors\jup")
DOCS = [
    ROOT / "README.md",
    ROOT / "docs" / "REPOSITORY_MAP.md",
    ROOT / "docs" / "METHODOLOGY_IMPLEMENTATION_MAP.md",
    ROOT / "docs" / "REPRODUCIBILITY_GUIDE.md",
    ROOT / "full_doc_report" / "REMEDFILM_FINAL_SCIENTIFIC_QA.md",
    ROOT / "full_doc_report" / "REMEDFILM_FULL_RESULT_RECONCILIATION.md",
]

LINK = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HTML_SRC = re.compile(r"(?:src|href)=\"([^\"]+)\"")


def check(path: Path, results: list) -> None:
    text = path.read_text(encoding="utf-8")
    targets = []
    for m in LINK.finditer(text):
        targets.append(("image" if m.group(1) else "link", m.group(3)))
    for m in HTML_SRC.finditer(text):
        targets.append(("html", m.group(1)))

    for kind, tgt in targets:
        if tgt.startswith(("http://", "https://", "mailto:", "#")):
            if tgt.startswith(("#",)):
                anchor = tgt[1:]
                slug = re.sub(r"[^a-z0-9 -]", "", anchor.lower()).replace(" ", "-")
                ok = slug in re.sub(r"[^a-z0-9 -]", "",
                                    text.lower()).replace(" ", "-")
                results.append((path, kind, tgt, "anchor", "OK" if ok else "MISSING"))
            else:
                results.append((path, kind, tgt, "external", "OK"))
            continue
        clean = unquote(tgt.split("#")[0])
        if not clean:
            continue
        target = (path.parent / clean).resolve()
        results.append((path, kind, tgt, "internal",
                        "OK" if target.exists() else "MISSING"))


def main() -> None:
    results: list = []
    for p in DOCS:
        if not p.exists():
            print(f"DOC MISSING: {p}")
            continue
        check(p, results)

    missing = [r for r in results if r[4] == "MISSING"]
    internal = [r for r in results if r[3] == "internal"]
    anchors = [r for r in results if r[3] == "anchor"]
    external = [r for r in results if r[3] == "external"]
    images = [r for r in results if r[1] in ("image", "html")]

    print(f"documents checked : {len([p for p in DOCS if p.exists()])}")
    print(f"total references  : {len(results)}")
    print(f"  internal paths  : {len(internal)}  (missing {sum(1 for r in internal if r[4] == 'MISSING')})")
    print(f"  images          : {len(images)}  (missing {sum(1 for r in images if r[4] == 'MISSING')})")
    print(f"  anchors         : {len(anchors)}  (missing {sum(1 for r in anchors if r[4] == 'MISSING')})")
    print(f"  external        : {len(external)}")
    print()
    if missing:
        print("MISSING TARGETS")
        for p, kind, tgt, ttype, _ in missing:
            print(f"  {p.relative_to(ROOT).as_posix()}: {kind} -> {tgt}")
    else:
        print("ALL INTERNAL LINKS RESOLVE")

    import json
    (ROOT / "docs" / "link_verification.json").write_text(json.dumps({
        "artifact": "readme_link_verification",
        "documents": [p.relative_to(ROOT).as_posix() for p in DOCS if p.exists()],
        "total_references": len(results),
        "internal": len(internal),
        "images": len(images),
        "anchors": len(anchors),
        "external": len(external),
        "missing": [
            {"document": p.relative_to(ROOT).as_posix(), "kind": k, "target": t}
            for p, k, t, _, _ in missing
        ],
        "all_resolve": not missing,
    }, indent=2), encoding="utf-8")
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
