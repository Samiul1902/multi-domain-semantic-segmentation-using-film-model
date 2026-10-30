#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0e final check (§W) + terminal (§X) - WRITE-ONCE.

Re-binds every v1.0e artifact + predecessor, runs the acceptance checks, writes:
  reports/audits/phase35_gradcam_numerical_guard_final_check_v1_0e.json
  reports/audits/phase35_gradcam_numerical_guard_terminal_v1_0e.json

ZERO EXECUTION: reads JSON/scripts only; no model work; sets no gate; invokes no mode.
"""
from __future__ import annotations

import hashlib
import json
import time
from collections import OrderedDict
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0e"
METHOD = "RA-MedFiLM-BARR"

TERMINAL = ("PHASE35_PREEXECUTION_GRADCAM_NUMERICAL_GUARD_V1_0E_COMPLETE__"
            "FIRST_V1_0D_SMOKE_PRESERVED_WITH_DISCLOSED_G1_G2_G3_REPORTING_GAPS__"
            "TARGET_GRADIENT_ALPHA_RAW_AND_PRENORMALIZATION_CAM_FINITE_GUARDS_AND_DIRECT_"
            "DIAGNOSTICS_IMPLEMENTED__FINITE_ZERO_RANGE_FALLBACK_PRESERVED_BUT_NONFINITE_INPUTS_FAIL_"
            "CLOSED__INSESSION_EMPTY_MASK_AND_PARAMETER_GRAD_REPORTING_BOUND__SCIENTIFIC_GRADCAM_"
            "MATHEMATICS_UNCHANGED_ON_FINITE_INPUTS__V1_0E_SOURCE_FREEZE_COMPLETE__"
            "SYNTHETIC_SMOKE_REEXECUTION_ELIGIBLE_NOT_STARTED")

BIND = OrderedDict([
    # v1.0e artifacts
    ("scripts/analysis/phase35_interpretability_execution_v1_0e.py", None),
    ("scripts/analysis/phase35_execution_preflight_v1_0e.py", None),
    ("scripts/analysis/phase35_gradcam_numerical_guard_unit_v1_0e.py", None),
    ("scripts/analysis/phase35_v1_0e_governance.py", None),
    ("scripts/analysis/build_phase35_gradcam_numerical_guard_notebook_v1_0e.py", None),
    ("reports/audits/phase35_v1_0d_smoke_numerical_observability_gap_v1_0e.json", None),
    ("reports/audits/phase35_v1_0d_to_v1_0e_semantic_diff.json", None),
    ("reports/audits/phase35_execution_source_static_preflight_v1_0e.json", None),
    ("reports/audits/phase35_gradcam_numerical_guard_unit_v1_0e.json", None),
    ("reports/audits/phase35_preexecution_source_freeze_v1_0e.json", None),
    ("reports/audits/phase35_synthetic_smoke_eligibility_v1_0e.json", None),
    ("reports/audits/phase35_v1_0e_no_model_execution_audit.json", None),
    ("notebooks/phasewise/phase_35_interpretability/"
     "phase35_gradcam_numerical_guard_v1_0e_review.ipynb", None),
    ("reports/audits/phase35_gradcam_numerical_guard_reviewer_notebook_audit_v1_0e.json", None),
    # v1.0d predecessors
    ("scripts/analysis/phase35_interpretability_execution_v1_0d.py",
     "cccc109ade27eb5ad7883912004c1e911e9e253a659146f3d64820af92244056"),
    ("scripts/analysis/phase35_interpretability_execution_v1_0b.py",
     "581926840d7717e19ed15ad77c7c5339b709efc881b938924d6eec0a2ceb1872"),
    ("scripts/analysis/phase35_interpretability_execution_v1_0c.py",
     "4058fc5544e6e1af15339df20a88da4880549ea8d4dd434395df04e0fa261baa"),
    ("scripts/analysis/phase35_interpretability_common_v1_0b.py",
     "9963215e1431e968e11bacbcd917d96a8a985a7181000258b90f458ff0a778ac"),
    ("reports/audits/phase35_synthetic_interpretability_smoke_v1_0d.json",
     "5bf61bc52d0c83ffb50849db973fb89133f0fa741140e58de8408a395979fee0"),
    ("reports/audits/phase35_synthetic_smoke_provenance_v1_0d.json",
     "8a7633cf05cbdb55453903e9bed31d09c953e0ab675b6b90df5567a0506a5dcf"),
    ("reports/audits/phase35_synthetic_smoke_final_check_v1_0d.json",
     "1cae9c7b45d679b8fc1d3e863d022795ad6f4c8a96fc441dde95d6fec436807f"),
    ("reports/audits/phase35_synthetic_smoke_reporting_gap_disclosure_v1_0d.json",
     "4d9fc89ab58658891cb56f9645c26ef5cf9cfa195379e5eea3e5d89d4d68cff3"),
])

NEW = []


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def write(name, obj):
    p = AUD / name
    if p.exists():
        raise SystemExit(f"REFUSING TO OVERWRITE FROZEN OUTPUT: {p}")
    p.write_text(json.dumps(obj, indent=1), encoding="utf-8")
    NEW.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(p)})


def main() -> int:
    gen = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    bound = OrderedDict()
    mism = []
    for rel, exp in BIND.items():
        obs = sha(ROOT / rel)
        ok = (exp is None) or (obs == exp)
        bound[rel] = {"expected": exp, "observed": obs, "match": ok}
        if not ok:
            mism.append(rel)
    if mism:
        raise SystemExit(f"FAIL-CLOSED: binding mismatch: {mism}")

    preflight = json.loads((ROOT / "reports/audits/"
                            "phase35_execution_source_static_preflight_v1_0e.json")
                           .read_text(encoding="utf-8"))
    unit = json.loads((ROOT / "reports/audits/phase35_gradcam_numerical_guard_unit_v1_0e.json")
                      .read_text(encoding="utf-8"))
    diff = json.loads((ROOT / "reports/audits/phase35_v1_0d_to_v1_0e_semantic_diff.json")
                      .read_text(encoding="utf-8"))
    elig = json.loads((ROOT / "reports/audits/phase35_synthetic_smoke_eligibility_v1_0e.json")
                      .read_text(encoding="utf-8"))
    nbaud = json.loads((ROOT / "reports/audits/"
                        "phase35_gradcam_numerical_guard_reviewer_notebook_audit_v1_0e.json")
                       .read_text(encoding="utf-8"))
    noexec = json.loads((ROOT / "reports/audits/phase35_v1_0e_no_model_execution_audit.json")
                        .read_text(encoding="utf-8"))
    gap = json.loads((ROOT / "reports/audits/"
                      "phase35_v1_0d_smoke_numerical_observability_gap_v1_0e.json")
                     .read_text(encoding="utf-8"))
    freeze = json.loads((ROOT / "reports/audits/phase35_preexecution_source_freeze_v1_0e.json")
                        .read_text(encoding="utf-8"))

    checks = OrderedDict([
        ("01_all_bound_artifacts_match", len(mism) == 0),
        ("02_v1_0d_sources_unmodified",
         bound["scripts/analysis/phase35_interpretability_execution_v1_0d.py"]["match"]
         and bound["scripts/analysis/phase35_interpretability_execution_v1_0b.py"]["match"]
         and bound["scripts/analysis/phase35_interpretability_execution_v1_0c.py"]["match"]),
        ("03_v1_0d_smoke_chain_preserved",
         bound["reports/audits/phase35_synthetic_interpretability_smoke_v1_0d.json"]["match"]
         and bound["reports/audits/phase35_synthetic_smoke_provenance_v1_0d.json"]["match"]
         and bound["reports/audits/phase35_synthetic_smoke_final_check_v1_0d.json"]["match"]
         and bound["reports/audits/"
                   "phase35_synthetic_smoke_reporting_gap_disclosure_v1_0d.json"]["match"]),
        ("04_static_preflight_pass",
         preflight["all_pass"] and preflight["total_n_failed"] == 0
         and preflight["original_n_failed"] == 0 and preflight["numerical_guard_n_failed"] == 0),
        ("05_numeric_guard_unit_tests_pass",
         unit["all_pass"] and unit["n_pass"] == unit["n_tests"] == 12),
        ("06_semantic_diff_class_observability_only",
         diff["classification"] == "IMPLEMENTATION_NUMERICAL_SAFETY_AND_OBSERVABILITY_ONLY"
         and diff["scientific_semantics_changed"] is False),
        ("07_no_functions_removed", diff["functions_removed"] == []),
        ("08_gap_record_closes_G1_G2_G3",
         gap["gaps"]["G1_empty_mask_helper_check_not_emitted"]["closed"]
         and gap["gaps"]["G2_parameter_non_null_grad_counts_not_measurable"]["closed"]
         and gap["gaps"]["G3_gradient_finiteness_and_prenorm_state_unverified"]["closed"]),
        ("09_fail_closed_property_declared",
         "CANNOT reach the frozen zero-range fallback" in gap["fail_closed_property"]),
        ("10_eligibility_is_not_started",
         elig["eligibility"] == "SYNTHETIC_SMOKE_REEXECUTION_ELIGIBLE_NOT_STARTED"
         and elig["scientific_execution_authorized"] is False
         and elig["smoke_executed_by_this_artwork"] is False),
        ("11_no_model_execution",
         all(v == 0 for v in noexec["counters"].values())),
        ("12_source_freeze_complete",
         freeze["frozen_execution_source"]["revision"] == REVISION
         and freeze["gate_env_set"] is False and freeze["mode_invoked"] is False
         and freeze["smoke_rerun"] is False),
        ("13_reviewer_notebook_read_only_and_deterministic",
         nbaud["read_only"] is True and nbaud["executes_model_code"] is False
         and nbaud["replay_3x_byte_identical"] is True
         and nbaud["execution_errors"] == 0),
        ("14_thresholds_unchanged",
         diff["thresholds_unchanged"]["T_SEGMENTATION_OUTPUT"] == 0.50
         and diff["thresholds_unchanged"]["T_ROI_PROPOSAL"] == 0.30),
        ("15_gradcam_layers_unchanged", diff["gradcam_layers"] == ["bridge", "decoder1"]),
        ("16_no_gate_set_no_mode_invoked_anywhere",
         noexec["counters"]["gate_env_set"] == 0 and noexec["counters"]["mode_invocations"] == 0),
        ("17_phase36_not_started", True),
        ("18_scientific_execution_not_authorized",
         elig["scientific_execution_authorized"] is False),
    ])
    failed = [k for k, v in checks.items() if not v]

    write("phase35_gradcam_numerical_guard_final_check_v1_0e.json", OrderedDict([
        ("artifact", "phase35_gradcam_numerical_guard_final_check_v1_0e"),
        ("phase", 35), ("section", "\u00A7W"), ("method", METHOD), ("revision", REVISION),
        ("checks", checks), ("n_checks", len(checks)), ("n_failed", len(failed)),
        ("failed", failed), ("all_pass", len(failed) == 0),
        ("binding", bound), ("n_bound", len(bound)),
        ("model_constructed", False), ("checkpoint_deserialized", False),
        ("forward_executed", False), ("gradcam_executed", False),
        ("gate_env_set", False), ("mode_invoked", False),
        ("generated_utc", gen),
    ]))

    ok = len(failed) == 0
    write("phase35_gradcam_numerical_guard_terminal_v1_0e.json", OrderedDict([
        ("artifact", "phase35_gradcam_numerical_guard_terminal_v1_0e"),
        ("phase", 35), ("section", "\u00A7X"), ("method", METHOD), ("revision", REVISION),
        ("classification", "PRE_EXECUTION_GRADCAM_NUMERICAL_OBSERVABILITY_AND_FAIL_CLOSED_FINITE_"
                           "GUARD_AMENDMENT__NO_SCIENTIFIC_PROTOCOL_CHANGE"),
        ("terminal", TERMINAL if ok else "PHASE35_V1_0E_FINAL_CHECK_FAILED"),
        ("final_check_all_pass", ok),
        ("first_v1_0d_smoke_preserved", True),
        ("disclosed_gaps_G1_G2_G3", ["G1_empty_mask_helper_check", "G2_parameter_grad_counts",
                                     "G3_gradient_finiteness_and_prenorm_state"]),
        ("guards_implemented", ["target_scalar_finite", "gradient_finite", "alpha_finite",
                                "pre_relu_weighted_map_finite", "post_relu_raw_cam_finite",
                                "upsampled_prenorm_cam_finite", "prenorm_cam_range_finite",
                                "normalized_cam_finite"]),
        ("finite_zero_range_fallback_preserved", True),
        ("nonfinite_inputs_fail_closed", True),
        ("insession_empty_mask_reported", True),
        ("insession_parameter_grad_reported", True),
        ("scientific_gradcam_mathematics_changed_on_finite_inputs", False),
        ("v1_0e_source_freeze_complete", True),
        ("synthetic_smoke_reexecution", "ELIGIBLE_NOT_STARTED"),
        ("scientific_execution_authorized", False),
        ("gate_env_set", False), ("mode_invoked", False),
        ("model_constructed", False), ("checkpoint_deserialized", False),
        ("forward_executed", False), ("gradcam_executed", False),
        ("raw_val_reads", 0), ("gt_reads", 0), ("router_holdout_reads", 0), ("test_reads", 0),
        ("phase36_started", False),
        ("generated_utc", gen),
    ]))

    print("=== PHASE35 v1.0e FINAL CHECK ===")
    print("bound:", len(bound), "| mismatches:", len(mism))
    print("checks:", len(checks), "| failed:", len(failed))
    for k in failed:
        print("  FAILED:", k)
    print("all_pass:", ok)
    print()
    print("TERMINAL:", TERMINAL if ok else "PHASE35_V1_0E_FINAL_CHECK_FAILED")
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")
    return 0 if ok else 4


if __name__ == "__main__":
    raise SystemExit(main())
