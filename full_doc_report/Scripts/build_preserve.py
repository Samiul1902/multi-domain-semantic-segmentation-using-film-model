"""Phase B — Preserve original notebooks.

Copies every genuine source notebook into full_doc_report/notebooks_original/
preserving its repository-relative directory hierarchy, then verifies each copy
is byte-identical to its source.

Never moves or deletes an original. Read-only on the source tree.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"
DEST = OUT / "notebooks_original"
INVENTORY = OUT / "NOTEBOOK_INVENTORY.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    rows = list(csv.DictReader(INVENTORY.open(encoding="utf-8")))
    # Genuine sources only: exclude copies produced by consolidation runs.
    sources = [r for r in rows if r["merge_status"] == "SOURCE_OF_TRUTH"]
    # The two prior master stubs are consolidation output, not research sources.
    sources = [r for r in sources
               if not r["original_path"].startswith("full_doc_report/")]

    manifest = []
    verified = 0
    for r in sources:
        rel = r["original_path"]
        src = ROOT / rel
        dst = DEST / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        s_sha = sha256(src)
        d_sha = sha256(dst)
        if s_sha != d_sha:
            raise SystemExit(f"COPY_MISMATCH {rel}: {s_sha} != {d_sha}")
        if s_sha != r["sha256"]:
            raise SystemExit(f"INVENTORY_SHA_DRIFT {rel}")
        verified += 1
        manifest.append({
            "original_path": rel,
            "preserved_path": dst.relative_to(ROOT).as_posix(),
            "sha256": s_sha,
            "size_bytes": src.stat().st_size,
            "byte_identical": True,
            "phase_or_experiment": r["phase_or_experiment"],
            "has_embedded_outputs": r["has_outputs"] == "YES",
        })

    (OUT / "NOTEBOOK_PRESERVATION_MANIFEST.json").write_text(
        json.dumps({
            "artifact": "notebook_preservation_manifest",
            "policy": "copy-only; originals never moved or deleted",
            "n_source_notebooks": len(sources),
            "n_verified_byte_identical": verified,
            "note": ("Embedded outputs in preserved copies are historical artifacts "
                     "and are not evidence that a run occurred during consolidation."),
            "notebooks": manifest,
        }, indent=2),
        encoding="utf-8",
    )
    print(f"COPIED {verified}")
    print(f"MISMATCHES 0")
    print(f"MANIFEST {OUT / 'NOTEBOOK_PRESERVATION_MANIFEST.json'}")
    print(f"DEST {DEST}")


if __name__ == "__main__":
    main()
