#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.2 §R — STATIC NEGATIVE CONTROLS (NC1..NC6).

Purpose
-------
Prove that the v1.2 static auditor DETECTS the exact defects recorded in
``reports/audits/phase36_v1_1_executability_false_positive_defect_v1_2.json``
(D1..D10). Each control applies ONE deterministic text/AST probe to the FROZEN
v1.1 subject file and asserts the probe FIRES (i.e. the auditor WOULD reject v1.1).
The SAME probes are then applied to the v1.2 subject and asserted to PASS.

No torch. No model. No checkpoint deserialization. No medical data. No protected
data access. Pure text/AST analysis of source bytes on disk.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "reports" / "audits" / "phase36_v1_2_negative_controls.json"
V1_1 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_1.py"
V1_2 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_2.py"

RESULTS: list[dict] = []


def rec(nc, desc, defect, subject, fires, detail):
    RESULTS.append({
        "control": nc, "desc": desc, "defect_id": defect, "subject": subject,
        "auditor_fires_reject": bool(fires), "detail": detail,
    })


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _funcs(path: Path) -> dict:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    src_lines = path.read_text(encoding="utf-8").splitlines()
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body_lines = src_lines[node.lineno - 1: node.end_lineno]
            out[node.name] = "\n".join(body_lines)
    return out


def nc1_unconditional_reachable_runtime_error(src: str) -> tuple:
    """NC1 (D1): _load_models contains an unconditional reachable RuntimeError."""
    fns = _funcs(V1_1 if src == "v1_1" else V1_2)
    body = fns.get("_load_models", "")
    # an unconditional raise at function-body top level (not inside try/if/for guard)
    fires = bool(re.search(r"^\s{4}raise RuntimeError\(", body, re.MULTILINE))
    detail = {"body_has_bare_raise_runtimeerror": fires}
    return fires, detail


def nc2_metadata_only_clean_generator(src: str) -> tuple:
    """NC2 (D3): _generate_clean_reference_once returns METADATA only (no per-sample loop)."""
    fns = _funcs(V1_1 if src == "v1_1" else V1_2)
    body = fns.get("_generate_clean_reference_once", "")
    loops_samples = "_load_population()" in body and ("for " in body)
    returns_records = "'records'" in body or '"records"' in body
    fires = not (loops_samples and returns_records)          # fires when NOT real
    return fires, {"iterates_population": loops_samples, "returns_records": returns_records}


def nc3_empty_bound_masks(src: str) -> tuple:
    """NC3 (D4): _bind_clean_reference returns EMPTY roi_geometry/final_pred."""
    fns = _funcs(V1_1 if src == "v1_1" else V1_2)
    body = fns.get("_bind_clean_reference", "")
    empty_geom = bool(re.search(r'"roi_geometry"\s*:\s*\{\s*\}', body))
    empty_pred = bool(re.search(r'"final_pred"\s*:\s*\{\s*\}', body))
    # In v1.1 these empties are DECLARED (subject to later STAGE-1 fill) but the gate then
    # tolerates them; NC3 fires when the gate does not enforce population equality.
    gate = fns.get("_clean_equivalence_gate", "")
    gate_enforces_808 = ("POPULATION_N" in gate and
                         ("missing_generated_dice" in gate or "generated_exactly_808" in gate))
    fires = (not gate_enforces_808)
    return fires, {"gate_enforces_808": gate_enforces_808,
                   "declared_empty_geometry": empty_geom, "declared_empty_pred": empty_pred}


def nc4_permissive_equivalence_gate(src: str) -> tuple:
    """NC4 (D5): equivalence gate silently skips missing generated/bound Dice."""
    fns = _funcs(V1_1 if src == "v1_1" else V1_2)
    body = fns.get("_clean_equivalence_gate", "")
    # v1.1: `if gen is not None and bound is not None:` -> silently skips otherwise.
    silent_skip = bool(re.search(r"if\s+gen\s+is\s+not\s+None\s+and\s+bound\s+is\s+not\s+None", body))
    strict_missing = ("missing_generated_dice" in body and "missing_bound_dice" in body)
    fires = silent_skip or (not strict_missing)
    return fires, {"silent_skip_present": silent_skip, "strict_missing_checks": strict_missing}


def nc5_science_loop_no_sample_ids(src: str) -> tuple:
    """NC5 (D7): run_science perturbation rows carry NO sample_id (metadata-only rows)."""
    fns = _funcs(V1_1 if src == "v1_1" else V1_2)
    body = fns.get("run_science", "")
    rows_have_sid = '"sample_id"' in body
    executes_image = "_evaluate_frozen_system(" in body
    executes_proposal = "_evaluate_frozen_system_proposal(" in body
    fires = not (rows_have_sid and executes_image and executes_proposal)
    return fires, {"rows_have_sample_id": rows_have_sid,
                   "executes_image_perturbation": executes_image,
                   "executes_proposal_perturbation": executes_proposal}


def nc6_smoke_hardcoded_truth_flags(src: str) -> tuple:
    """NC6 (D8/D9): smoke never loads real components; state machine uses hardcoded flags."""
    fns = _funcs(V1_1 if src == "v1_1" else V1_2)
    smoke = fns.get("run_smoke", "")
    sm = fns.get("_smoke_state_machine", "")
    smoke_loads = "_load_models()" in smoke
    # v1.1 hardcodes: {"skip_returns_global": True, "reject_returns_global": True, "accept_returns_regional": True}
    hardcoded = bool(re.search(r'"skip_returns_global"\s*:\s*True', sm))
    fires = (not smoke_loads) or hardcoded
    return fires, {"smoke_loads_real_components": smoke_loads,
                   "hardcoded_truth_flags_present": hardcoded}


CONTROLS = [
    ("NC1", "unconditional reachable RuntimeError in _load_models", "D1", nc1_unconditional_reachable_runtime_error),
    ("NC2", "clean generator is metadata-only (no 808 loop)", "D3", nc2_metadata_only_clean_generator),
    ("NC3", "clean equivalence gate does not enforce 808 population", "D4", nc3_empty_bound_masks),
    ("NC4", "clean equivalence gate permissive (silent skip)", "D5", nc4_permissive_equivalence_gate),
    ("NC5", "science loop has no sample_id / no real execution", "D7", nc5_science_loop_no_sample_ids),
    ("NC6", "smoke never loads components / hardcoded truth flags", "D8", nc6_smoke_hardcoded_truth_flags),
]


def main() -> int:
    verdicts = []
    for nc, desc, defect, fn in CONTROLS:
        fires_v1_1, detail_v1_1 = fn("v1_1")
        fires_v1_2, detail_v1_2 = fn("v1_2")
        rec(nc, desc, defect, "v1_1_subject", fires_v1_1, detail_v1_1)
        rec(nc, desc, defect, "v1_2_subject", fires_v1_2, detail_v1_2)
        verdicts.append({
            "control": nc, "desc": desc, "defect_id": defect,
            "v1_1_auditor_rejects": bool(fires_v1_1),
            "v1_2_auditor_passes": bool(not fires_v1_2),
            "control_valid": bool(fires_v1_1 and not fires_v1_2),
        })

    all_valid = all(v["control_valid"] for v in verdicts)
    payload = {
        "artifact": "phase36_v1_2_negative_controls",
        "section": "§R", "phase": 36, "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_2",
        "classification": "STATIC_NEGATIVE_CONTROLS__AUDITOR_WOULD_REJECT_V1_1",
        "no_execution": True, "torch_imported": False,
        "v1_1_subject_sha256": _sha(V1_1), "v1_2_subject_sha256": _sha(V1_2),
        "controls": RESULTS, "verdicts": verdicts,
        "all_controls_valid": bool(all_valid),
        "interpretation": (
            "Each control fires on the frozen v1.1 subject and stays silent on the v1.2 "
            "subject, proving the v1.2 static auditor detects the recorded v1.1 defects "
            "rather than accepting them."),
    }
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"all_controls_valid": all_valid,
                      "verdicts": [{"control": v["control"], "v1_1_rejects": v["v1_1_auditor_rejects"],
                                    "v1_2_passes": v["v1_2_auditor_passes"]} for v in verdicts],
                      "sha256": _sha(OUT)}, indent=1))
    return 0 if all_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
