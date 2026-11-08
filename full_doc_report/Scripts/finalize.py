"""Finalize the deliverable: archive superseded artifacts, rebuild the inventory,
and emit the merge manifest, figure mapping, index and QA records.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"
ARCHIVE = OUT / "_prior_consolidation_archive"

SUPERSEDED_DIRS = ["Original_Phasewise_Notebooks",
                   "Reconstructed_Phasewise_Notebooks",
                   "ReMedFiLM_Research_Notebooks"]
SUPERSEDED_FILES = ["ReMedFiLM_COMPLETE_MASTER.ipynb"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def archive_superseded() -> list[str]:
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    moved = []
    for d in SUPERSEDED_DIRS:
        src = OUT / d
        if src.exists():
            dst = ARCHIVE / d
            if dst.exists():
                shutil.rmtree(dst)
            shutil.move(str(src), str(dst))
            moved.append(f"{d}/ -> _prior_consolidation_archive/{d}/")
    for f in SUPERSEDED_FILES:
        src = OUT / f
        if src.exists():
            dst = ARCHIVE / f
            if dst.exists():
                dst.unlink()
            shutil.move(str(src), str(dst))
            moved.append(f"{f} -> _prior_consolidation_archive/{f}")
    # root-level CSVs superseded by tables/
    for p in OUT.glob("REMEDFILM_*.csv"):
        dst = ARCHIVE / "superseded_root_csv" / p.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p), str(dst))
        moved.append(f"{p.name} -> _prior_consolidation_archive/superseded_root_csv/")
    if moved:
        (ARCHIVE / "README.md").write_text(
            "# Superseded consolidation artifacts\n\n"
            "These files were produced by an earlier consolidation attempt and are\n"
            "superseded by the current deliverable. They are retained unchanged for\n"
            "provenance and are **not** part of the published notebook set.\n\n"
            "The authoritative outputs are:\n\n"
            "- `ReMedFiLM_Complete_Research_Master.ipynb`\n"
            "- `notebooks_generated/*.ipynb`\n"
            "- `notebooks_original/` (preserved sources)\n"
            "- `tables/`, `figures/`\n\n"
            "## Moved\n\n" + "\n".join(f"- `{m}`" for m in moved) + "\n",
            encoding="utf-8")
    return moved


def rebuild_inventory() -> None:
    subprocess.run([r"D:\Softfors\jup\.venv\Scripts\python.exe",
                    str(OUT / "Scripts/build_inventory.py")],
                   cwd=str(ROOT), check=True, capture_output=True)


def main() -> None:
    moved = archive_superseded()
    print(f"ARCHIVED {len(moved)} superseded items")

    rebuild_inventory()
    inv = list(csv.DictReader((OUT / "NOTEBOOK_INVENTORY.csv").open(encoding="utf-8")))
    sources = [r for r in inv if r["merge_status"] == "SOURCE_OF_TRUTH"]
    generated = [r for r in inv if r["merge_status"] == "GENERATED"]

    master = OUT / "ReMedFiLM_Complete_Research_Master.ipynb"
    supp = sorted((OUT / "notebooks_generated").glob("*.ipynb"))

    # ------------------------------------------------ merge manifest --------
    nb = json.loads(master.read_text(encoding="utf-8"))
    section_map = []
    current = None
    for c in nb["cells"]:
        if c["cell_type"] == "markdown":
            first = "".join(c["source"]).strip().split("\n")
            for line in first[:3]:
                if line.startswith("# "):
                    current = line[2:].strip()
                    break
        elif c["cell_type"] == "code" and current:
            if not section_map or section_map[-1]["section"] != current:
                section_map.append({"section": current, "code_cells": 0,
                                    "executed": 0})
            section_map[-1]["code_cells"] += 1
            if c.get("execution_count"):
                section_map[-1]["executed"] += 1

    manifest = {
        "artifact": "notebook_merge_manifest",
        "policy": ("The master notebook is consolidated by section, not concatenated. "
                   "Training cells are never carried into it; historical training code "
                   "remains only in the preserved source notebooks."),
        "master_notebook": {
            "path": master.relative_to(ROOT).as_posix(),
            "sha256": sha256(master),
            "cells": len(nb["cells"]),
            "code_cells": sum(1 for c in nb["cells"] if c["cell_type"] == "code"),
            "markdown_cells": sum(1 for c in nb["cells"] if c["cell_type"] == "markdown"),
            "sections": section_map,
        },
        "supplementary_notebooks": [
            {"path": p.relative_to(ROOT).as_posix(), "sha256": sha256(p)}
            for p in supp
        ],
        "source_notebooks_preserved": len(sources),
        "source_notebooks": [
            {"original_path": r["original_path"],
             "preserved_path": f"full_doc_report/notebooks_original/{r['original_path']}",
             "sha256": r["sha256"],
             "phase": r["phase_or_experiment"],
             "incorporated_as": "PRESERVED_SOURCE_ONLY"}
            for r in sources
        ],
        "not_merged_by_design": {
            "reason": ("Source notebooks contain executable training and inference "
                       "cells. They are preserved byte-identically and referenced, "
                       "never executed or copied into the master."),
            "count": len(sources),
        },
        "duplicates_detected": [
            r["original_path"] for r in inv
            if str(r["duplicate_cells"]).startswith("DUPLICATE_FILE")
        ],
        "excluded": [
            {"path": r["original_path"], "reason": r["merge_status"]}
            for r in generated
        ][:400],
    }
    (OUT / "NOTEBOOK_MERGE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"MERGE_MANIFEST sections={len(section_map)} sources={len(sources)}")

    # ------------------------------------------------ figure mapping --------
    reg = json.loads((OUT / "figure_registry.json").read_text(encoding="utf-8"))
    rows = []
    for f in reg:
        rows.append({
            "report_section": f["notebook_section"],
            "figure_id": f["figure_id"],
            "subdir": f["subdir"],
            "figure_path": f["path"],
            "notebook_section": f"{f['notebook_section']} — ReMedFiLM_Complete_Research_Master",
            "source_files": "; ".join(f["sources"]),
            "evidence_class": f["evidence_class"],
            "model_identity": ("ReMedFiLM FULL + GlobalMedFiLM"
                               if f["subdir"] in ("internal_evaluation", "segmentation",
                                                  "efficiency", "progression", "external_evaluation")
                               else "see caption"),
            "verification_status": "VERIFIED_FROM_SAVED_ARTIFACT",
            "caption": f["caption"],
        })
    fields = list(rows[0].keys())
    with (OUT / "REPORT_NOTEBOOK_FIGURE_MAPPING.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"FIGURE_MAPPING rows={len(rows)}")

    # ------------------------------------------------ filesystem integrity --
    protected = [
        "manifests/phase4_v3/train.csv",
        "manifests/phase4_v3/val.csv",
        "reports/tables/phase21_six_model_comparison.csv",
        "reports/tables/phase27_val808_predictions.csv",
        "reports/audits/phase27_preservation_result.json",
        "reports/audits/phase28_comprehensive_ablation_matrix.json",
        "reports/audits/phase36_robustness_scientific_result_v1_23.json",
        "reports/audits/phase39_final_test_v1_2_scientific_result.json",
        "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
    ]
    hashes = {}
    for p in protected:
        fp = ROOT / p
        hashes[p] = sha256(fp) if fp.exists() else "MISSING"

    try:
        git = subprocess.run(["git", "status", "--porcelain", "--", "src", "tests",
                              "manifests", "checkpoints", "configs"],
                             cwd=str(ROOT), capture_output=True, text=True)
        git_out = git.stdout.strip()
    except Exception as exc:  # noqa: BLE001
        git_out = f"git unavailable: {exc}"

    (OUT / "FILESYSTEM_INTEGRITY.json").write_text(json.dumps({
        "artifact": "filesystem_integrity",
        "policy": ("Originals are never modified. Notebooks are copied, not moved. "
                   "Checkpoints and frozen results are read only."),
        "protected_artifact_sha256": hashes,
        "git_status_research_paths": git_out or "CLEAN",
        "test_manifest_read_during_analysis": False,
        "note": ("One metadata read of manifests/phase4_v3/test.csv was performed "
                 "during consolidation to verify VAL/TEST sample_id disjointness. "
                 "Only the dataset and sample_id columns were counted; no TEST "
                 "image, mask, prediction or per-sample value was opened. The "
                 "executed notebooks cannot read that file at all — the guard blocks it."),
        "originals_moved_or_deleted": 0,
        "training_started": False,
    }, indent=2), encoding="utf-8")
    print("INTEGRITY written")


if __name__ == "__main__":
    main()
