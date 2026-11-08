"""Phase A/C — Notebook inventory.

Scans every .ipynb in the repository (excluding virtualenvs, caches and build
copies), classifies each one, and writes NOTEBOOK_INVENTORY.csv.

Read-only with respect to research artifacts: this script only reads.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"

# `.workbuddy-ai` is deliberately NOT excluded: it holds two genuine Phase 21
# notebook revisions (pre-repair backup and repaired copy) that are real
# historical artifacts rather than cache.
EXCLUDE_DIRS = {
    ".venv", "node_modules", ".git", "__pycache__", "_tmp",
    "site-packages", ".ipynb_checkpoints", "build", "dist", ".mypy_cache",
    ".pytest_cache",
}
# Generated notebooks produced by this consolidation task are inventoried but
# flagged, never treated as historical sources.
GENERATED_DIRS = {
    OUT / "notebooks_generated",
    OUT / "ReMedFiLM_Research_Notebooks",
    OUT / "Reconstructed_Phasewise_Notebooks",
    OUT / "notebooks_original",
    OUT / "_prior_consolidation_archive",
}

DATASET_TOKENS = {
    "ISIC": [r"isic2018", r"ISIC2018", r"\bISIC_"],
    "BUSI": [r"BUSI", r"busi"],
    "KVASIR": [r"[Kk]vasir", r"KVASIR"],
    "KUB": [r"KUB-Stone", r"KUB-Stonex", r"\bKUB\b"],
    "CVC": [r"CVC-ClinicDB", r"\bCVC\b"],
    "BREAST_EXT": [r"BrEaST", r"Breast-Lesions"],
    "HAM10000": [r"HAM10000"],
    "PH2": [r"\bPH2\b"],
}
TRAINING_TOKENS = [
    r"\.fit\(", r"trainer\.train\(", r"optimizer\.step\(", r"loss\.backward\(",
    r"\.train\(\)", r"torch\.optim\.", r"Adam\(", r"AdamW\(", r"SGD\(",
    r"train_one_epoch", r"run_training", r"launch\(", r"--execute",
]
INFERENCE_TOKENS = [
    r"torch\.no_grad", r"@torch\.inference_mode", r"\.eval\(\)",
    r"predict", r"inference", r"forward\(",
]
TEST_TOKENS = [r"phase4_v3[/\\]test", r"test\.csv", r"TEST1683", r"test_lock"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_notebooks() -> list[Path]:
    found = []
    for p in ROOT.rglob("*.ipynb"):
        parts = set(p.parts)
        if parts & EXCLUDE_DIRS:
            continue
        found.append(p)
    return sorted(found, key=lambda x: str(x).lower())


def classify_phase(path: Path, text: str) -> str:
    low = str(path).lower()
    m = re.search(r"phase[_\-]?(\d{2})", low)
    if m:
        return f"PHASE_{m.group(1)}"
    m = re.search(r"phase[_\-]?(\d{2})", text[:4000].lower())
    if m:
        return f"PHASE_{m.group(1)}"
    if "phasewise" in low:
        return "PHASEWISE_INDEX"
    return "UNMAPPED"


def main() -> None:
    rows = []
    seen_hashes: dict[str, list[str]] = {}
    for p in iter_notebooks():
        rel = p.relative_to(ROOT).as_posix()
        try:
            raw = p.read_bytes()
            nb = json.loads(raw.decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            rows.append({
                "original_path": rel, "filename": p.name, "sha256": "",
                "size_bytes": p.stat().st_size, "phase_or_experiment": "UNREADABLE",
                "purpose": f"PARSE_ERROR: {type(exc).__name__}", "code_cells": 0,
                "markdown_cells": 0, "has_outputs": "NO", "kernel": "",
                "datasets_referenced": "", "checkpoints_referenced": "",
                "logs_referenced": "", "predictions_referenced": "",
                "duplicate_cells": "", "side_effects": "UNKNOWN",
                "execution_eligibility": "EXCLUDED_UNREADABLE", "merge_status": "EXCLUDED",
            })
            continue
        digest = hashlib.sha256(raw).hexdigest()
        seen_hashes.setdefault(digest, []).append(rel)

        cells = nb.get("cells", [])
        code_cells = [c for c in cells if c.get("cell_type") == "code"]
        md_cells = [c for c in cells if c.get("cell_type") == "markdown"]
        src_all = "\n".join(
            "".join(c.get("source", [])) for c in cells
        )
        has_out = any(c.get("outputs") for c in code_cells)
        exec_counts = [c.get("execution_count") for c in code_cells if c.get("execution_count")]
        kernel = (nb.get("metadata", {}).get("kernelspec", {}) or {}).get("name", "")

        datasets = sorted({k for k, pats in DATASET_TOKENS.items()
                           if any(re.search(pt, src_all) for pt in pats)})
        ckpts = sorted(set(re.findall(r"checkpoints[\\/][A-Za-z0-9_\-]+", src_all)))[:6]
        logs = sorted(set(re.findall(r"[A-Za-z0-9_\-]+\.log\b", src_all)))[:6]
        preds = sorted(set(re.findall(r"[A-Za-z0-9_\-]*predictions?[A-Za-z0-9_\-]*\.(?:csv|npy|npz|json)", src_all)))[:6]

        train_hits = [t for t in TRAINING_TOKENS if re.search(t, src_all)]
        inf_hits = [t for t in INFERENCE_TOKENS if re.search(t, src_all)]
        test_hits = [t for t in TEST_TOKENS if re.search(t, src_all)]

        # duplicate code cells within a notebook
        code_srcs = ["".join(c.get("source", [])).strip() for c in code_cells]
        dups = len(code_srcs) - len(set(s for s in code_srcs if s))

        side = []
        if train_hits:
            side.append(f"TRAINING({len(train_hits)})")
        if inf_hits:
            side.append(f"INFERENCE({len(inf_hits)})")
        if test_hits:
            side.append("TEST_PATH_REFERENCE")
        if not side:
            side.append("NONE_DETECTED")

        in_report = str(p).startswith(str(OUT))
        preserved = (str(p).startswith(str(OUT / "notebooks_original"))
                     or str(p).startswith(str(OUT / "Original_Phasewise_Notebooks")))
        archived = str(p).startswith(str(OUT / "_prior_consolidation_archive"))
        deliverable = in_report and not preserved and not archived

        if archived:
            status = "ARCHIVED_SUPERSEDED"
            eligibility = "NOT_PART_OF_DELIVERABLE"
        elif preserved:
            status = "PRESERVED_SOURCE"
            eligibility = "ARCHIVAL_ONLY_TRAINING_CELLS_BLOCKED"
        elif deliverable:
            status = "DELIVERABLE"
            eligibility = "ANALYSIS_ELIGIBLE"
        elif "TRAINING" in "".join(side):
            status = "SOURCE_OF_TRUTH"
            eligibility = "ARCHIVAL_ONLY_TRAINING_CELLS_BLOCKED"
        else:
            status = "SOURCE_OF_TRUTH"
            eligibility = "ANALYSIS_ELIGIBLE"

        rows.append({
            "original_path": rel,
            "filename": p.name,
            "sha256": digest,
            "size_bytes": len(raw),
            "phase_or_experiment": classify_phase(p, src_all),
            "purpose": (md_cells[0].get("source", [""])[0].strip()[:160]
                        if md_cells else ""),
            "code_cells": len(code_cells),
            "markdown_cells": len(md_cells),
            "has_outputs": "YES" if has_out else "NO",
            "kernel": kernel,
            "datasets_referenced": "|".join(datasets),
            "checkpoints_referenced": "|".join(ckpts),
            "logs_referenced": "|".join(logs),
            "predictions_referenced": "|".join(preds),
            "duplicate_cells": dups,
            "side_effects": "|".join(side),
            "execution_eligibility": eligibility,
            "merge_status": status,
            "_exec_counts": len(exec_counts),
        })

    # duplicate detection across files
    for r in rows:
        d = r["sha256"]
        if d and len(seen_hashes.get(d, [])) > 1:
            r["duplicate_cells"] = f"DUPLICATE_FILE({len(seen_hashes[d])})"

    fields = [k for k in rows[0] if not k.startswith("_")] + ["executed_cells"]
    out_csv = OUT / "NOTEBOOK_INVENTORY.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in rows:
            rr = {k: v for k, v in r.items() if not k.startswith("_")}
            rr["executed_cells"] = r["_exec_counts"]
            w.writerow(rr)

    print(f"NOTEBOOKS_INVENTORIED {len(rows)}")
    print(f"UNIQUE_SHA {len(seen_hashes)}")
    print(f"WITH_OUTPUTS {sum(1 for r in rows if r['has_outputs']=='YES')}")
    from collections import Counter as _C
    print("STATUS:", dict(_C(r["merge_status"] for r in rows)))
    print(f"WRITTEN {out_csv}")
    by_phase: dict[str, int] = {}
    for r in rows:
        by_phase[r["phase_or_experiment"]] = by_phase.get(r["phase_or_experiment"], 0) + 1
    for k in sorted(by_phase):
        print(f"  {k}: {by_phase[k]}")


if __name__ == "__main__":
    main()
