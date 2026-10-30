"""Write the Phase-20B reviewer-package audit artifacts (additive, read-only science).

Produces:
  * reports/audits/phase20b_notebook_location_migration.json
  * reports/audits/phase20b_notebook_determinism.json          (updated, new path)
  * reports/audits/phase20b_reviewer_package_audit.json
  * reports/audits/phase20b_reviewer_package_freeze.json       (additive companion)

Never trains, never runs inference, never touches TEST, never modifies the frozen
scientific freeze / protocol / binding JSONs.

    ./.venv/Scripts/python.exe scripts/analysis/write_phase20b_audits.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

from src.analysis import phase20b_reviewer as R  # noqa: E402

A = ROOT / "reports" / "audits"
NB_PATH = (ROOT / "notebooks/phasewise/phase_20b_five_model_baselines"
           / "phase20b_five_model_conventional_baselines.ipynb")
NB_REL = R.rel(NB_PATH)
NB_SHA = hashlib.sha256(NB_PATH.read_bytes()).hexdigest()

FREEZE_PATH = A / "phase20_five_model_baseline_benchmark_freeze.json"
PROTOCOL_PATH = A / "phase20_shared_global_baseline_protocol.json"

TERMINAL_SCIENTIFIC = "PHASE20_FIVE_MODEL_BASELINE_BENCHMARK_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED"
TERMINAL_DOC = "PHASE20B_REVIEWER_PACKAGE_COMPLETE__FULL_VISUAL_EVIDENCE__PHASE21_ELIGIBLE_NOT_STARTED"

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def nb_stats() -> dict:
    nb = json.loads(NB_PATH.read_text(encoding="utf-8"))
    cells = nb["cells"]
    code = [c for c in cells if c["cell_type"] == "code"]
    err = sum(1 for c in code for o in c.get("outputs", []) if o.get("output_type") == "error")
    png = sum(1 for c in code for o in c.get("outputs", []) if "image/png" in (o.get("data", {}) or {}))
    html = sum(1 for c in code for o in c.get("outputs", []) if "text/html" in (o.get("data", {}) or {}))
    counts = [c.get("execution_count") for c in code]
    mono = all(counts[i] == i + 1 for i in range(len(counts)))
    return {
        "cells_total": len(cells),
        "cells_markdown": sum(1 for c in cells if c["cell_type"] == "markdown"),
        "cells_code": len(code),
        "zero_tracebacks": err == 0,
        "error_count": err,
        "monotonic_exec_counts": mono,
        "png_outputs": png,
        "html_table_outputs": html,
    }


def build_shas() -> list[str]:
    shas = []
    for i in (1, 2, 3):
        log = ROOT / f"logs/phase20b_nb_build{i}.log"
        if log.exists():
            m = re.search(r"Notebook SHA: ([0-9a-f]{64})", log.read_text(encoding="utf-8", errors="ignore"))
            if m:
                shas.append(m.group(1))
    return shas


def main() -> int:
    print("=== PHASE-20B AUDIT ARTIFACTS ===")
    inv = json.loads((A / "phase20b_figure_inventory.json").read_text(encoding="utf-8"))
    cov_rows = list(csv.DictReader((A / "phase20b_evaluation_matrix_visualization_coverage.csv").open(encoding="utf-8")))
    cov_total = len(cov_rows)
    cov_viz = sum(1 for r in cov_rows if r["status"] == "VISUALIZED")
    st = nb_stats()
    shas = build_shas()
    det = len(shas) == 3 and len(set(shas)) == 1

    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    freeze_sha = sha256(FREEZE_PATH)
    proto_sha = sha256(PROTOCOL_PATH)

    head = R.headline_table().set_index("model_key")
    ranking = [{"model_key": m, "model": R.DISPLAY[m], "phase": R.PHASE[m],
                "macro_domain_val_dice": float(head.loc[m, "macro_dice"]),
                "best_epoch": int(head.loc[m, "best_epoch"]),
                "params": int(head.loc[m, "params"])}
               for m in head.sort_values("macro_dice", ascending=False).index]

    # ---- 1. location migration -------------------------------------------- #
    mig = {
        "artifact": "phase20b_notebook_location_migration",
        "phase": 20, "subphase": "20B",
        "migration_type": "RELOCATION_TO_CANONICAL_PHASEWISE_FOLDER + FULL_EVIDENCE_REBUILD",
        "old_path": "notebooks/phasewise/phase_20_multidomain_baselines/phase20b_five_model_conventional_baselines.ipynb",
        "new_path": NB_REL,
        "old_path_exists": (ROOT / "notebooks/phasewise/phase_20_multidomain_baselines/phase20b_five_model_conventional_baselines.ipynb").exists(),
        "new_path_exists": NB_PATH.exists(),
        "old_sha256": "8c13cd146b52692d2c2b58ec42b87f949286beb46702095caf262dd9d888b08c",
        "new_sha256": NB_SHA,
        "old_cells": 18,
        "new_cells": st["cells_total"],
        "reason": ("Phase 20B is a distinct sub-phase benchmark; its reviewer notebook now lives in a "
                   "dedicated canonical phasewise folder and was rebuilt from a thin 18-cell notebook "
                   "into a full scientific-evidence notebook. No frozen artifact was modified."),
        "canonical_folder": "notebooks/phasewise/phase_20b_five_model_baselines/",
        "readme": "notebooks/phasewise/phase_20b_five_model_baselines/README.md",
        "recorded_at": NOW,
    }
    (A / "phase20b_notebook_location_migration.json").write_text(json.dumps(mig, indent=2), encoding="utf-8")
    print("migration  ->", mig["old_path_exists"], "->", mig["new_path_exists"], "sha", NB_SHA[:12])

    # ---- 2. determinism ---------------------------------------------------- #
    detj = {
        "artifact": "phase20b_notebook_determinism",
        "phase": 20, "subphase": "20B",
        "notebook_path": NB_REL,
        "final_notebook_sha256": NB_SHA,
        "rebuild_sha256": shas[-1] if shas else None,
        "build_shas": shas,
        "consecutive_builds_compared": len(shas),
        "all_builds_identical": det,
        "deterministic": det,
        "cells_total": st["cells_total"],
        "cells_markdown": st["cells_markdown"],
        "cells_code": st["cells_code"],
        "zero_tracebacks": st["zero_tracebacks"],
        "monotonic_exec_counts": st["monotonic_exec_counts"],
        "png_outputs": st["png_outputs"],
        "html_table_outputs": st["html_table_outputs"],
        "method": ("deterministic cell ids (p20b###) + stripped metadata.execution + coalesced stream "
                   "outputs + fixed pandas Styler uuids (.set_uuid) + normalised object memory addresses "
                   "(0x[0-9a-fA-F]{6,} -> 0xADDR) in every output text/plain/text/html"),
        "nondeterminism_sources_fixed": [
            "pandas 3.x Styler random table id T_<hex> regenerated on every render -> fixed via Styler.set_uuid(...)",
            "pandas Styler text/plain fallback embeds the object memory address (<Styler at 0x...>) -> fixed via address normalisation",
        ],
        "note": ("Phase-20A notebook was already deterministic because it used no pandas Styler; Phase-20B "
                 "introduced .style.format(...) for reviewer-readable tables, which required the two fixes above."),
        "generated_by": "scripts/notebooks/build_phase20b_notebook.py",
        "recorded_at": NOW,
    }
    (A / "phase20b_notebook_determinism.json").write_text(json.dumps(detj, indent=2), encoding="utf-8")
    print("determinism-> builds", len(shas), "identical:", det)

    # ---- 3. reviewer package audit ---------------------------------------- #
    audit = {
        "artifact": "phase20b_reviewer_package_audit",
        "phase": 20, "subphase": "20B",
        "generated_at": NOW,
        "no_training": True,
        "no_new_model_inference": True,
        "no_canonical_val_inference_rerun": True,
        "no_test_access": True,
        "notebook": {"path": NB_REL, "sha256": NB_SHA, **st,
                     "deterministic_3_builds": det, "build_shas": shas},
        "figures": {
            "figures_total": inv["figures_total"],
            "embedded_in_notebook": inv["embedded_total"],
            "figure_root": inv["figure_root"],
            "by_group": inv["by_group"],
            "by_category": inv["by_category"],
            "inventory_csv": "reports/audits/phase20b_figure_inventory.csv",
            "inventory_json": "reports/audits/phase20b_figure_inventory.json",
        },
        "matrix_coverage": {
            "matrices_total": cov_total,
            "visualized": cov_viz,
            "coverage": round(cov_viz / cov_total, 6),
            "all_visualized": cov_viz == cov_total,
            "csv": "reports/audits/phase20b_evaluation_matrix_visualization_coverage.csv",
        },
        "governance_synced": [
            "reports/audits/phasewise_notebook_map.csv",
            "reports/audits/phasewise_notebook_map.json",
            "reports/audits/phasewise_notebook_map.md",
            "notebooks/phasewise/README.md",
            "PROJECT_MASTER_PLAN.md",
            "notebooks/phasewise/00_PHASEWISE_PROJECT_INDEX.ipynb",
            "reports/audits/trained_model_visualization_registry.csv",
            "reports/audits/trained_model_visualization_registry.json",
            "reports/audits/dataset_visualization_coverage.csv",
            "reports/audits/phasewise_notebook_execution_manifest.csv",
            "reports/audits/phasewise_notebook_execution_manifest.json",
            "reports/audits/phasewise_notebook_execution_manifest.md",
        ],
        "frozen_science_unchanged": {
            "scientific_freeze": "reports/audits/phase20_five_model_baseline_benchmark_freeze.json",
            "scientific_freeze_sha256": freeze_sha,
            "protocol_sha256": proto_sha,
            "protocol_sha_matches_freeze": freeze.get("protocol_sha256") == proto_sha,
            "terminal_state": freeze.get("terminal_state"),
        },
        "test_reads": freeze.get("test_reads_total"),
        "scientific_terminal_state": TERMINAL_SCIENTIFIC,
        "documentation_terminal_state": TERMINAL_DOC,
        "phase21_started": False,
    }
    (A / "phase20b_reviewer_package_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print("audit      -> figures", inv["figures_total"], "| coverage", f"{cov_viz}/{cov_total}")

    # ---- 4. additive reviewer-package freeze companion --------------------- #
    companion = {
        "artifact": "phase20b_reviewer_package_freeze",
        "phase": 20, "subphase": "20B",
        "additive_to": "reports/audits/phase20_five_model_baseline_benchmark_freeze.json",
        "does_not_modify_frozen_science": True,
        "frozen_scientific_freeze_sha256": freeze_sha,
        "frozen_protocol_sha256": proto_sha,
        "protocol_sha_unchanged": freeze.get("protocol_sha256") == proto_sha,
        "ranking_by_macro_domain_dice": ranking,
        "top_model": freeze.get("top_model"),
        "top_two_margin": freeze.get("top_two_margin"),
        "top_two_ranking_significant": freeze.get("top_two_ranking_significant"),
        "reviewer_package": {
            "notebook_path": NB_REL,
            "notebook_sha256": NB_SHA,
            "notebook_deterministic": det,
            "figures_total": inv["figures_total"],
            "figures_embedded": inv["embedded_total"],
            "matrix_coverage": round(cov_viz / cov_total, 6),
            "figure_inventory_csv": "reports/audits/phase20b_figure_inventory.csv",
            "matrix_coverage_csv": "reports/audits/phase20b_evaluation_matrix_visualization_coverage.csv",
            "audit": "reports/audits/phase20b_reviewer_package_audit.json",
            "location_migration": "reports/audits/phase20b_notebook_location_migration.json",
            "determinism": "reports/audits/phase20b_notebook_determinism.json",
        },
        "test_reads_total": freeze.get("test_reads_total"),
        "terminal_state": TERMINAL_SCIENTIFIC,
        "documentation_terminal_state": TERMINAL_DOC,
        "phase21_started": False,
        "phase21_authorization_required": True,
        "generated_at": NOW,
    }
    (A / "phase20b_reviewer_package_freeze.json").write_text(json.dumps(companion, indent=2), encoding="utf-8")
    print("companion  -> terminal", companion["terminal_state"])
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
