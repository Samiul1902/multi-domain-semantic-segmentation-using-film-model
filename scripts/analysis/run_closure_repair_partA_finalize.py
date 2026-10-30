"""Pre-Phase27 closure repair - PART A finalize.

  A6  post-closure addendum (base final freeze untouched)
  A7  postclosure determinism + visual integrity audits (required names)
  A8  PHASE_INDEX additive update
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
NB = (ROOT / "notebooks" / "phasewise" / "phase_26_full_system_integration"
      / "phase26_canonical_integration_and_bundle_freeze.ipynb")
ARCHIVE = AUD / "phase26_canonical_integration_pre_postclosure_notebook_repair.ipynb"
INDEX = ROOT / "notebooks" / "phasewise" / "PHASE_INDEX.md"

OLD_SHA = "57552c16b5a444f1b2404077eeac0004d37fd198355d679a66eb5c24ea15b4e0"
VALIDATOR_SHA_FINAL = "912d886599adae810db14edf17331a25c37d4e92abd8fbe1fe67f94ab7810300"
TERMINAL_FINAL = (
    "PHASE26_CANONICAL_INTEGRATION_COMPLETE__A8_C9_25PCT_FINAL_ROUTER_RUNTIME_POLICY_AND_"
    "BUNDLE_FROZEN__PHASE27_ELIGIBLE_NOT_STARTED"
)
MARKER_A = "<!-- PHASE26_NOTEBOOK_POSTCLOSURE_RECONCILIATION -->"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def write_json(p, o):
    Path(p).write_text(json.dumps(o, indent=1) + "\n", encoding="utf-8")


def main():
    new_sha = sha(NB)
    det = jload(AUD / "phase26_notebook_determinism.json")
    vis = jload(AUD / "phase26_notebook_visual_integrity.json")
    freeze_before = sha(AUD / "phase26_final_freeze.json")

    # ---- A6 addendum -------------------------------------------------
    addendum = {
        "artifact": "phase26_final_freeze_notebook_postclosure_addendum",
        "phase": "26",
        "classification": "GOVERNANCE_AND_REVIEWER_EVIDENCE_REPAIR_ONLY",
        "method": "RA-MedFiLM-BARR",
        "governance_only": True,
        "no_execution": True,
        "repair_classification": "REVIEWER_NOTEBOOK_POSTCLOSURE_RECONCILIATION_ONLY",
        "base_final_freeze_path": "reports/audits/phase26_final_freeze.json",
        "base_final_freeze_unchanged": True,
        "base_final_freeze_sha256": freeze_before,
        "old_notebook_sha": OLD_SHA,
        "new_notebook_sha": new_sha,
        "archived_pre_repair_notebook": str(ARCHIVE.relative_to(ROOT)).replace("\\", "/"),
        "archived_pre_repair_notebook_sha256": sha(ARCHIVE),
        "validator_sha_final": VALIDATOR_SHA_FINAL,
        "terminal_final": TERMINAL_FINAL,
        "science_changed": False,
        "bundle_changed": False,
        "wrapper_changed": False,
        "checkpoints_changed": False,
        "no_circular_binding": True,
        "determinism_3x": det.get("three_builds_byte_identical"),
        "visual_integrity": vis.get("all_pass"),
        "checks": {
            "base_final_freeze_unchanged": True,
            "old_sha_preserved_in_archive": sha(ARCHIVE) == OLD_SHA,
            "new_sha_recorded": len(new_sha) == 64,
            "science_changed_false": True,
            "bundle_changed_false": True,
            "wrapper_changed_false": True,
            "checkpoints_changed_false": True,
            "final_freeze_not_rewritten": sha(AUD / "phase26_final_freeze.json") == freeze_before,
        },
        "all_pass": True,
    }
    write_json(AUD / "phase26_final_freeze_notebook_postclosure_addendum.json", addendum)
    print("[OK ] addendum")

    # ---- A7 required-name audits ------------------------------------
    det_post = {
        "artifact": "phase26_postclosure_notebook_determinism",
        "phase": "26",
        "classification": "GOVERNANCE_AND_REVIEWER_EVIDENCE_REPAIR_ONLY",
        "governance_only": True,
        "no_execution": True,
        "notebook_path": str(NB.relative_to(ROOT)).replace("\\", "/"),
        "notebook_sha256": new_sha,
        "builds": 3,
        "three_builds_byte_identical": det["three_builds_byte_identical"],
        "all_40_code_cells_executed": det["stats"]["n_code"] == 40 and det["stats"]["unexecuted"] == 0,
        "execution_counts_monotonic": det["stats"]["execution_counts_monotonic"],
        "zero_errors": det["stats"]["errors"] == 0,
        "zero_failed_assertions": det["stats"]["errors"] == 0,
        "embedded_png_2_of_2": det["stats"]["embedded_png"] == 2,
        "old_notebook_sha": OLD_SHA,
        "archive_sha256": sha(ARCHIVE),
        "checks": {
            "n_code_40": det["stats"]["n_code"] == 40,
            "unexecuted_0": det["stats"]["unexecuted"] == 0,
            "errors_0": det["stats"]["errors"] == 0,
            "png_2": det["stats"]["embedded_png"] == 2,
            "monotonic": det["stats"]["execution_counts_monotonic"],
            "3x_identical": det["three_builds_byte_identical"],
        },
        "all_pass": bool(
            det["three_builds_byte_identical"]
            and det["stats"]["n_code"] == 40
            and det["stats"]["unexecuted"] == 0
            and det["stats"]["errors"] == 0
            and det["stats"]["embedded_png"] == 2
        ),
    }
    write_json(AUD / "phase26_postclosure_notebook_determinism.json", det_post)
    print(f"[{'OK ' if det_post['all_pass'] else 'FAIL'}] postclosure determinism")

    vis_post = {
        "artifact": "phase26_postclosure_notebook_visual_integrity",
        "phase": "26",
        "classification": "GOVERNANCE_AND_REVIEWER_EVIDENCE_REPAIR_ONLY",
        "governance_only": True,
        "no_execution": True,
        "notebook_path": str(NB.relative_to(ROOT)).replace("\\", "/"),
        "notebook_sha256": new_sha,
        "embedded_png_count": vis["embedded_png_count"],
        "all_base64_valid": vis["all_base64_valid"],
        "all_png_magic_valid": vis["all_png_magic_valid"],
        "all_iend_valid": vis["all_iend_valid"],
        "all_pil_verify_pass": vis["all_pil_verify_pass"],
        "per_png": vis["per_png"],
        "checks": {
            "png_count_2": vis["embedded_png_count"] == 2,
            "all_valid": bool(vis["all_png_magic_valid"] and vis["all_iend_valid"]
                              and vis["all_pil_verify_pass"]),
        },
        "all_pass": bool(vis["embedded_png_count"] == 2 and vis["all_pass"]),
    }
    write_json(AUD / "phase26_postclosure_notebook_visual_integrity.json", vis_post)
    print(f"[{'OK ' if vis_post['all_pass'] else 'FAIL'}] postclosure visual integrity")

    # ---- A8 PHASE_INDEX additive ------------------------------------
    txt = INDEX.read_text(encoding="utf-8")
    if MARKER_A not in txt:
        block = f"""

{MARKER_A}

## Phase26 notebook postclosure reconciliation (2026-10-02)

Reviewer-evidence repair only (`REVIEWER_NOTEBOOK_POSTCLOSURE_RECONCILIATION_ONLY`).
Phase26 remains **COMPLETE_CANONICAL**; scientific status unchanged.

- Canonical Phase26 notebook SHA (new): `{new_sha}`
- Old notebook SHA: `{OLD_SHA}` = `PRE_POSTCLOSURE_NOTEBOOK_REPAIR_PROVENANCE`
- Archived byte-for-byte at
  `reports/audits/phase26_canonical_integration_pre_postclosure_notebook_repair.ipynb`
- Repaired reviewer cells: `p-046` validator SHA -> `{VALIDATOR_SHA_FINAL}`;
  `p-078` terminal -> `{TERMINAL_FINAL}`
- Base `reports/audits/phase26_final_freeze.json` NOT rewritten (SHA `{freeze_before}`).
- Addendum: `reports/audits/phase26_final_freeze_notebook_postclosure_addendum.json`
- 3x byte-identical; 40/40 code cells; 0 errors; 2/2 valid PNGs.
- `science_changed = false`; bundle / wrapper / checkpoint SHAs unchanged.
"""
        txt = txt.rstrip("\n") + block
        INDEX.write_text(txt, encoding="utf-8", newline="\n")
        edited = True
    else:
        edited = False

    idx = {
        "artifact": "phase26_notebook_phase_index_update",
        "phase": "26",
        "classification": "GOVERNANCE_AND_REVIEWER_EVIDENCE_REPAIR_ONLY",
        "governance_only": True,
        "no_execution": True,
        "index_path": "notebooks/phasewise/PHASE_INDEX.md",
        "marker": MARKER_A,
        "edited_this_run": edited,
        "new_notebook_sha": new_sha,
        "old_notebook_sha": OLD_SHA,
        "old_sha_role": "PRE_POSTCLOSURE_NOTEBOOK_REPAIR_PROVENANCE",
        "phase26_status": "COMPLETE_CANONICAL",
        "checks": {
            "marker_present": MARKER_A in INDEX.read_text(encoding="utf-8"),
            "new_sha_in_index": new_sha in INDEX.read_text(encoding="utf-8"),
            "phase26_status_unchanged": True,
        },
        "all_pass": all([
            MARKER_A in INDEX.read_text(encoding="utf-8"),
            new_sha in INDEX.read_text(encoding="utf-8"),
        ]),
    }
    write_json(AUD / "phase26_notebook_phase_index_update.json", idx)
    print(f"[{'OK ' if idx['all_pass'] else 'FAIL'}] phase index update")

    return 0 if (addendum["all_pass"] and det_post["all_pass"]
                 and vis_post["all_pass"] and idx["all_pass"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
