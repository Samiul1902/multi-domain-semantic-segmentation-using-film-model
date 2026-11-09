"""Phase 28 -- notebook compliance repair §0/§1/§2/§3.

Entry gate + classification + archive + defect confirmation.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/repair_phase28_notebook_gate.py
"""
from __future__ import annotations

import base64
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
NB = ROOT / "notebooks" / "phasewise" / "phase_28_model_ablation" / "phase28_comprehensive_ablation.ipynb"

OLD_SHA = "72cfbc12e76a58fab3449e6dbf8163cbe988e7473e716e10bf87741fa8c10326"
TERMINAL = ("PHASE28_COMPREHENSIVE_ABLATION_MATRIX_COMPLETE__"
            "CORE_ROUTER_AND_REFINER_ABLATIONS_FROZEN__PHASE29_ELIGIBLE_NOT_STARTED")
ARCHIVE = AUD / "phase28_comprehensive_ablation_pre_notebook_compliance_repair.ipynb"


def sha(p: Path):
    p = Path(p)
    if not p.exists():
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def wj(p: Path, o):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(o, f, indent=1, ensure_ascii=False)
        f.write("\n")


def main() -> int:
    # ---------------- §0 required current state ----------------
    term = json.load(open(AUD / "phase28_terminal_state.json", encoding="utf-8"))
    freeze = json.load(open(AUD / "phase28_final_freeze.json", encoding="utf-8"))
    tlock = json.load(open(AUD / "phase28_test_lock.json", encoding="utf-8"))
    hlock = json.load(open(AUD / "phase28_phase30_holdout_lock.json", encoding="utf-8"))
    vlock = json.load(open(AUD / "phase28_val808_reuse_rule.json", encoding="utf-8"))

    freeze_sha = sha(AUD / "phase28_final_freeze.json")
    nb_sha = sha(NB)

    checks = {
        "terminal_exact": term.get("terminal") == TERMINAL,
        "base_final_freeze_exists": (AUD / "phase28_final_freeze.json").exists(),
        "base_final_freeze_sha": freeze_sha,
        "canonical_notebook_exists": NB.exists(),
        "canonical_notebook_sha_exact": nb_sha == OLD_SHA,
        "phase29_started_false": term.get("blocked_terminals", {}).get("PHASE29_STARTED") is False,
        "phase30_started_false": term.get("blocked_terminals", {}).get("PHASE30_STARTED") is False,
        "ROUTER_HOLDOUT_reads_zero": term.get("ROUTER_HOLDOUT_reads") == 0,
        "VAL808_reads_zero": term.get("VAL808_reads") == 0,
        "TEST_reads_zero": term.get("TEST_reads") == 0,
        "test_lock_all_pass": tlock.get("all_pass") is True,
        "holdout_lock_all_pass": hlock.get("all_pass") is True,
        "val808_rule_all_pass": vlock.get("all_pass") is True,
    }
    gate_pass = all(v is True for k, v in checks.items()
                    if k not in ("base_final_freeze_sha",))

    entry = {
        "artifact": "phase28_notebook_compliance_repair_entry_gate",
        "phase": 28,
        "method": "RA-MedFiLM-BARR",
        "classification": "PHASE28_REVIEWER_NOTEBOOK_COMPLIANCE_REPAIR_ONLY",
        "required_terminal": TERMINAL,
        "observed_terminal": term.get("terminal"),
        "terminal_match": checks["terminal_exact"],
        "base_final_freeze": {
            "path": "reports/audits/phase28_final_freeze.json",
            "sha256": freeze_sha,
            "classification": freeze.get("classification"),
        },
        "canonical_notebook": {
            "path": str(NB.relative_to(ROOT)).replace("\\", "/"),
            "sha256": nb_sha,
            "required_sha256": OLD_SHA,
            "sha_exact": nb_sha == OLD_SHA,
        },
        "governance_state": {
            "phase29_started": False,
            "phase30_started": False,
            "ROUTER_HOLDOUT_reads": 0,
            "VAL808_reads": 0,
            "TEST_reads": 0,
        },
        "checks": checks,
        "scope": {
            "training": False,
            "model_forward": False,
            "OOF_recomputation": False,
            "membership_recomputation": False,
            "metric_recomputation": False,
            "bootstrap_recomputation": False,
            "ROUTER_HOLDOUT": False,
            "VAL808": False,
            "TEST": False,
        },
        "gate_pass": gate_pass,
        "all_pass": gate_pass,
    }
    wj(AUD / "phase28_notebook_compliance_repair_entry_gate.json", entry)
    print("entry gate:", gate_pass, "| nb sha:", nb_sha[:16])

    # ---------------- §1 classification freeze ----------------
    cls = {
        "artifact": "phase28_notebook_compliance_repair_classification",
        "phase": 28,
        "classification": "PHASE28_REVIEWER_NOTEBOOK_COMPLIANCE_REPAIR_ONLY",
        "scope_statement": "Repair the canonical Phase28 reviewer notebook ONLY. "
                           "Scientific execution, checkpoints, OOF predictions, "
                           "memberships, metrics, statistics, figures, tables and the "
                           "final scientific freeze are frozen and MUST NOT change.",
        "frozen_invariants": {
            "science_changed": False,
            "training_changed": False,
            "checkpoints_changed": False,
            "OOF_predictions_changed": False,
            "memberships_changed": False,
            "metrics_changed": False,
            "statistics_changed": False,
            "figures_scientific_content_changed": False,
            "canonical_bundle_changed": False,
        },
        "permitted_actions": [
            "rebuild notebook source from frozen artifacts",
            "execute notebook with nbclient",
            "normalize reviewer-presentation nondeterminism",
            "write additive audit artifacts",
        ],
        "forbidden_actions": [
            "training", "checkpoint selection", "model construction for inference",
            "model forward", "OOF prediction", "membership construction",
            "outcome opening", "metric recomputation", "bootstrap recomputation",
        ],
        "all_pass": True,
    }
    wj(AUD / "phase28_notebook_compliance_repair_classification.json", cls)
    print("classification frozen")

    # ---------------- §2 archive current notebook ----------------
    if ARCHIVE.exists():
        arch_sha = sha(ARCHIVE)
        print("archive already exists, sha:", arch_sha[:16])
    else:
        shutil.copyfile(NB, ARCHIVE)
        arch_sha = sha(ARCHIVE)
    arch_ok = arch_sha == OLD_SHA

    arch = {
        "artifact": "phase28_pre_compliance_repair_reviewer_notebook_provenance",
        "phase": 28,
        "classification": "PRE_COMPLIANCE_REPAIR_REVIEWER_NOTEBOOK_PROVENANCE",
        "archive_path": str(ARCHIVE.relative_to(ROOT)).replace("\\", "/"),
        "archive_sha256": arch_sha,
        "required_sha256": OLD_SHA,
        "sha_exact": arch_ok,
        "byte_for_byte_preserved": arch_ok,
        "deleted_or_overwritten": False,
        "note": "This archive is the pre-repair canonical notebook. It must never be "
                "deleted or overwritten.",
        "all_pass": arch_ok,
    }
    wj(AUD / "phase28_pre_compliance_repair_reviewer_notebook_provenance.json", arch)
    print("archive sha exact:", arch_ok)

    # ---------------- §3 confirm the current defect ----------------
    nb = json.load(open(ARCHIVE, encoding="utf-8"))
    cells = nb["cells"]
    md_cells = [c for c in cells if c["cell_type"] == "markdown"]
    code_cells = [c for c in cells if c["cell_type"] == "code"]
    exec_counters = [c.get("execution_count") for c in code_cells]
    null_count = sum(1 for e in exec_counters if e is None)
    n_outputs = sum(len(c.get("outputs", [])) for c in code_cells)
    err_outputs = sum(1 for c in code_cells for o in c.get("outputs", [])
                      if o.get("output_type") == "error")
    png_outputs = 0
    for c in code_cells:
        for o in c.get("outputs", []):
            data = o.get("data", {})
            if "image/png" in data:
                png_outputs += 1

    physical = {
        "total_cells": len(cells),
        "markdown_cells": len(md_cells),
        "code_cells": len(code_cells),
        "executed_code_cells": sum(1 for e in exec_counters if e is not None),
        "code_cells_with_null_execution_count": null_count,
        "error_outputs": err_outputs,
        "embedded_png_outputs": png_outputs,
        "total_outputs": n_outputs,
    }
    expected = {
        "total_cells": 81, "markdown_cells": 46, "code_cells": 35,
        "executed_code_cells": 0, "code_cells_with_null_execution_count": 35,
        "error_outputs": 0, "embedded_png_outputs": 0,
    }
    matches = {k: physical[k] == v for k, v in expected.items()}

    defect = {
        "artifact": "phase28_notebook_pre_repair_defect_confirmation",
        "phase": 28,
        "classification": "PHASE28_PRE_REPAIR_DEFECT_CONFIRMATION",
        "inspected_notebook": str(ARCHIVE.relative_to(ROOT)).replace("\\", "/"),
        "inspected_sha256": arch_sha,
        "expected": expected,
        "physical": physical,
        "matches_expected": matches,
        "all_expected_matched": all(matches.values()),
        "difference_explanation": None if all(matches.values()) else
        "Physical values differ from the work-order hypothesis; physical values are "
        "authoritative and are recorded above.",
        "defect_1_unexecuted": physical["executed_code_cells"] == 0 and physical["code_cells"] > 0,
        "defect_1_description": "Canonical notebook is UNEXECUTED: all code cells have "
                               "null execution_count and there are zero code outputs.",
        "defect_2_history_incomplete": True,
        "defect_2_description": "Complete epoch histories are not visibly rendered for "
                               "all 18 runs; only summaries plus fold0 row-level histories.",
        "all_pass": all(matches.values()),
    }
    wj(AUD / "phase28_notebook_pre_repair_defect_confirmation.json", defect)
    print("defect confirmation:", defect["all_pass"], "| physical:", physical)
    return 0 if (gate_pass and arch_ok and defect["all_pass"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
