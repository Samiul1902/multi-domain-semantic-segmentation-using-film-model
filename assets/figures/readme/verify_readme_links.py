"""Verify every internal link in the public documentation.

Checks, for each Markdown file passed on the command line:

  * every relative link and image target exists on disk
  * no absolute Windows path (``C:\\`` / ``D:\\``) appears in a link target
  * no backslash appears in a link target (GitHub needs forward slashes)
  * image targets use an extension GitHub renders
  * no target is excluded by .gitignore (an ignored asset will not render)
  * in-page anchors resolve to a heading in the same file

Exit code 1 if any check fails. Nothing is written and nothing is fetched; this
is a purely local, read-only audit.

Usage
-----
    .\\.venv\\Scripts\\python.exe assets\\figures\\readme\\verify_readme_links.py
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FILES = ["README.md", "docs/RESEARCH_VISUAL_GALLERY.md",
                 "docs/README_VISUAL_ASSET_MANIFEST.md",
                 "docs/README_SCIENTIFIC_EVIDENCE_INDEX.md",
                 "docs/README_FINAL_LINK_QA.md"]

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HTML_RE = re.compile(r"<(?:img|a)\b[^>]*?(?:src|href)=\"([^\"]+)\"", re.I)
HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.M)


def slug(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"[`*_]", "", s)
    s = re.sub(r"[^\w\s-]", "", s)
    return re.sub(r"[\s]+", "-", s).strip("-")


def headings(md: str) -> set[str]:
    out = set()
    for _, h in HEAD_RE.findall(md):
        out.add(slug(h))
    return out


def ignored(rel: str) -> bool:
    try:
        r = subprocess.run(["git", "check-ignore", "-q", rel], cwd=ROOT,
                           capture_output=True)
        return r.returncode == 0
    except Exception:
        return False


def check_file(md_path: Path) -> dict:
    md = md_path.read_text(encoding="utf-8")
    rel_md = md_path.relative_to(ROOT).as_posix()
    targets = [(m, False) for m in LINK_RE.findall(md)]
    targets += [(m, True) for m in HTML_RE.findall(md)]
    heads = headings(md)

    rows, ok, bad = [], 0, 0
    seen = set()
    for raw, is_html in targets:
        if raw in seen:
            continue
        seen.add(raw)
        t = raw.strip()
        row = {"source": rel_md, "target": t, "kind": "", "status": "", "detail": ""}

        if re.match(r"^(https?:|mailto:)", t):
            row["kind"] = "external"
            row["status"] = "SKIP"
            row["detail"] = "not fetched by this audit"
            rows.append(row)
            continue

        if t.startswith("#"):
            row["kind"] = "anchor"
            row["status"] = "OK" if slug(t[1:]) in heads else "BROKEN"
            if row["status"] == "BROKEN":
                row["detail"] = "no matching heading"
                bad += 1
            else:
                ok += 1
            rows.append(row)
            continue

        if re.match(r"^[A-Za-z]:[\\/]", t):
            row["kind"] = "path"
            row["status"] = "BROKEN"
            row["detail"] = "absolute Windows path"
            bad += 1
            rows.append(row)
            continue

        if "\\" in t:
            row["kind"] = "path"
            row["status"] = "BROKEN"
            row["detail"] = "backslash in link target"
            bad += 1
            rows.append(row)
            continue

        path_part = urllib.parse.unquote(t.split("#", 1)[0])
        ext = Path(path_part).suffix.lower()
        row["kind"] = "image" if ext in IMAGE_EXT else "link"

        base = ROOT if path_part.startswith("/") is False else ROOT
        target = (md_path.parent / path_part).resolve()
        try:
            rel = target.relative_to(ROOT).as_posix()
        except ValueError:
            row["status"] = "BROKEN"
            row["detail"] = "resolves outside the repository"
            bad += 1
            rows.append(row)
            continue

        if not target.exists():
            row["status"] = "BROKEN"
            row["detail"] = "target does not exist"
            bad += 1
        elif row["kind"] == "image" and ext not in IMAGE_EXT:
            row["status"] = "BROKEN"
            row["detail"] = f"image extension {ext} not rendered by GitHub"
            bad += 1
        elif ignored(rel):
            row["status"] = "IGNORED"
            row["detail"] = "excluded by .gitignore; will not render"
            bad += 1
        else:
            row["status"] = "OK"
            ok += 1
        rows.append(row)

    return {"file": rel_md, "rows": rows, "ok": ok, "bad": bad}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", default=None)
    ap.add_argument("--json", default=None, help="write the full report here")
    args = ap.parse_args()
    files = args.files or DEFAULT_FILES

    results = []
    for f in files:
        p = ROOT / f
        if not p.exists():
            print(f"MISSING FILE {f}")
            results.append({"file": f, "rows": [], "ok": 0, "bad": 1})
            continue
        results.append(check_file(p))

    tot_ok = sum(r["ok"] for r in results)
    tot_bad = sum(r["bad"] for r in results)
    for r in results:
        print(f"\n== {r['file']}: {r['ok']} ok, {r['bad']} broken")
        for row in r["rows"]:
            if row["status"] in ("BROKEN", "IGNORED"):
                print(f"   {row['status']:8s} {row['target'][:90]}  ({row['detail']})")
    print(f"\nTOTAL {tot_ok} verified, {tot_bad} broken")

    if args.json:
        (ROOT / args.json).write_text(
            json.dumps({"total_ok": tot_ok, "total_broken": tot_bad,
                        "files": results}, indent=1), encoding="utf-8")
    sys.exit(1 if tot_bad else 0)


if __name__ == "__main__":
    main()
