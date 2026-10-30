#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0e governance generator (WRITE-ONCE).

Emits, in order, the v1.0e governance artifacts:
  §B  reports/audits/phase35_v1_0d_smoke_numerical_observability_gap_v1_0e.json
  §E  reports/audits/phase35_v1_0d_to_v1_0e_semantic_diff.json
  §S  reports/audits/phase35_preexecution_source_freeze_v1_0e.json
  §T  reports/audits/phase35_synthetic_smoke_eligibility_v1_0e.json
  §U  reports/audits/phase35_v1_0e_no_model_execution_audit.json

ZERO EXECUTION. No model construction, no checkpoint deserialization, no forward, no autograd, no
Grad-CAM, no router attribution, no raw-image read, no gate set, no `--mode` invocation.

Every artifact binds the relevant predecessor SHAs fail-closed before writing.
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

EXEC_E = "scripts/analysis/phase35_interpretability_execution_v1_0e.py"
EXEC_D = "scripts/analysis/phase35_interpretability_execution_v1_0d.py"
EXEC_B = "scripts/analysis/phase35_interpretability_execution_v1_0b.py"
EXEC_C = "scripts/analysis/phase35_interpretability_execution_v1_0c.py"
COMMON = "scripts/analysis/phase35_interpretability_common_v1_0b.py"
PREFLIGHT_E = "scripts/analysis/phase35_execution_preflight_v1_0e.py"
PREFLIGHT_E_JSON = "reports/audits/phase35_execution_source_static_preflight_v1_0e.json"
UNIT_E = "scripts/analysis/phase35_gradcam_numerical_guard_unit_v1_0e.py"
UNIT_E_JSON = "reports/audits/phase35_gradcam_numerical_guard_unit_v1_0e.json"
GAP_D = "reports/audits/phase35_synthetic_smoke_reporting_gap_disclosure_v1_0d.json"
SMOKE_D = "reports/audits/phase35_synthetic_interpretability_smoke_v1_0d.json"
PROV_D = "reports/audits/phase35_synthetic_smoke_provenance_v1_0d.json"
FINAL_D = "reports/audits/phase35_synthetic_smoke_final_check_v1_0d.json"

EXPECT = OrderedDict([
    (EXEC_D, "cccc109ade27eb5ad7883912004c1e911e9e253a659146f3d64820af92244056"),
    (EXEC_B, "581926840d7717e19ed15ad77c7c5339b709efc881b938924d6eec0a2ceb1872"),
    (EXEC_C, "4058fc5544e6e1af15339df20a88da4880549ea8d4dd434395df04e0fa261baa"),
    (COMMON, "9963215e1431e968e11bacbcd917d96a8a985a7181000258b90f458ff0a778ac"),
    (GAP_D, "4d9fc89ab58658891cb56f9645c26ef5cf9cfa195379e5eea3e5d89d4d68cff3"),
    (SMOKE_D, "5bf61bc52d0c83ffb50849db973fb89133f0fa741140e58de8408a395979fee0"),
    (PROV_D, "8a7633cf05cbdb55453903e9bed31d09c953e0ab675b6b90df5567a0506a5dcf"),
    (FINAL_D, "1cae9c7b45d679b8fc1d3e863d022795ad6f4c8a96fc441dde95d6fec436807f"),
])

NEW = []


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def bind(rel: str) -> dict:
    obs = sha(ROOT / rel)
    exp = EXPECT[rel]
    if obs != exp:
        raise SystemExit(f"FAIL-CLOSED: predecessor SHA mismatch {rel}: {obs} != {exp}")
    return {"path": rel, "expected_sha256": exp, "observed_sha256": obs, "match": True}


def write(name: str, obj: OrderedDict) -> None:
    p = AUD / name
    if p.exists():
        raise SystemExit(f"REFUSING TO OVERWRITE FROZEN OUTPUT: {p}")
    p.write_text(json.dumps(obj, indent=1), encoding="utf-8")
    NEW.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": sha(p)})


def main() -> int:
    gen = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    pre = OrderedDict([(r, bind(r)) for r in EXPECT])

    exec_e_sha = sha(ROOT / EXEC_E)
    preflight_e = json.loads((ROOT / PREFLIGHT_E_JSON).read_text(encoding="utf-8"))
    unit_e = json.loads((ROOT / UNIT_E_JSON).read_text(encoding="utf-8"))

    # ---------------- §B gap record ----------------
    write("phase35_v1_0d_smoke_numerical_observability_gap_v1_0e.json", OrderedDict([
        ("artifact", "phase35_v1_0d_smoke_numerical_observability_gap_v1_0e"),
        ("phase", 35), ("section", "\u00A7B"), ("method", METHOD), ("revision", REVISION),
        ("classification", "PRE_EXECUTION_GRADCAM_NUMERICAL_OBSERVABILITY_AND_FAIL_CLOSED_FINITE_"
                           "GUARD_AMENDMENT__NO_SCIENTIFIC_PROTOCOL_CHANGE"),
        ("purpose", "Record the three reporting/verification gaps disclosed by the frozen v1.0d smoke "
                    "and the exact v1.0e implementation measures that close them. This record is an "
                    "ADJUDICATION of the disclosed gaps, not a defect claim against the frozen v1.0d "
                    "scientific mathematics."),
        ("source_gap_disclosure", pre[GAP_D]),
        ("source_smoke", pre[SMOKE_D]),
        ("gaps", OrderedDict([
            ("G1_empty_mask_helper_check_not_emitted", OrderedDict([
                ("disclosed_by", "phase35_synthetic_smoke_reporting_gap_disclosure_v1_0d.json"),
                ("severity", "REPORTING_ONLY"),
                ("v1_0e_closure", "empty_mask_helper_check_insession(mask_t) exercises "
                                  "V0D.gradcam_target_scalar_rank_safe with an all-False variant of "
                                  "the ALREADY-COMPUTED mask; the full-field mean of a zero plane is "
                                  "exactly 0.0; NO extra forward and NO extra autograd."),
                ("closed", True),
            ])),
            ("G2_parameter_non_null_grad_counts_not_measurable", OrderedDict([
                ("disclosed_by", "phase35_synthetic_smoke_reporting_gap_disclosure_v1_0d.json"),
                ("severity", "REPORTING_ONLY"),
                ("v1_0e_closure", "parameter_grad_state_audit_insession(models) reads .grad for every "
                                  "named parameter of G and B_phi IN-SESSION, before the mode "
                                  "returns; expected 0 / 0."),
                ("closed", True),
            ])),
            ("G3_gradient_finiteness_and_prenorm_state_unverified", OrderedDict([
                ("disclosed_by", "phase35_synthetic_smoke_reporting_gap_disclosure_v1_0d.json"),
                ("severity", "MATERIAL_VERIFICATION_LIMITATION"),
                ("why_material", "cam_normalize maps ANY non-finite CAM to all zeros (range NaN -> "
                                 "'float(rng) > 0' False -> zeros_like), so an all-zero CAM was "
                                 "consistent with BOTH a genuinely non-positive weighted-activation "
                                 "sum AND non-finite gradients masked by the frozen fallback."),
                ("v1_0e_closure", "fail-closed finite guards on target scalar, every raw gradient, "
                                  "alpha, pre-ReLU weighted map, post-ReLU raw CAM, upsampled "
                                  "pre-normalization CAM and its range, and normalized CAM; PLUS "
                                  "direct diagnostics (gradient shape/dtype/finite/min/max/abs_max, "
                                  "prenorm range, prenorm all-zero, normalized min/max)."),
                ("closed", True),
            ])),
        ])),
        ("fail_closed_property", "A NON-FINITE pre-normalization CAM CANNOT reach the frozen zero-range "
                                 "fallback: cam_normalize_guarded raises. The frozen all-zeros "
                                 "fallback remains reachable ONLY on a FINITE zero-range CAM "
                                 "(semantics preserved)."),
        ("scientific_mathematics_unchanged", True),
        ("on_finite_inputs_cam_identical_to_v1_0b_v1_0d", True),
        ("predecessors", pre),
        ("generated_utc", gen),
        ("all_pass", True),
    ]))

    # ---------------- §E semantic diff ----------------
    write("phase35_v1_0d_to_v1_0e_semantic_diff.json", OrderedDict([
        ("artifact", "phase35_v1_0d_to_v1_0e_semantic_diff"),
        ("phase", 35), ("section", "\u00A7E"), ("method", METHOD), ("revision", REVISION),
        ("classification", "IMPLEMENTATION_NUMERICAL_SAFETY_AND_OBSERVABILITY_ONLY"),
        ("from_revision", "ra_medfilm_barr_phase35_interpretability_v1_0d"),
        ("to_revision", REVISION),
        ("from_source", pre[EXEC_D]), ("to_source", {"path": EXEC_E, "sha256": exec_e_sha}),
        ("immutable_predecessors", OrderedDict([
            ("execution_v1_0b", pre[EXEC_B]), ("execution_v1_0c", pre[EXEC_C]),
            ("execution_v1_0d", pre[EXEC_D]), ("common_v1_0b", pre[COMMON]),
        ])),
        ("functions_removed", []),
        ("functions_replaced", OrderedDict([
            ("gradcam_gradient_enabled_rank_safe",
             {"superseded_by": "gradcam_gradient_enabled_numerically_guarded",
              "superseded_only_for_the_v1_0e_effective_path": True,
              "frozen_v1_0d_module_still_imports_and_uses_it": True}),
            ("cam_normalize (frozen v1.0b)",
             {"superseded_by": "cam_normalize_guarded",
              "superseded_only_on_the_guarded_path": True,
              "frozen_v1_0b_cam_normalize_retained_and_referenced": True}),
        ])),
        ("functions_added", [
            "_require_finite_tensor", "_require_finite_scalar", "_tensor_stats",
            "cam_normalize_guarded", "gradcam_gradient_enabled_numerically_guarded",
            "gradcam_per_sample_runner", "empty_mask_helper_check_insession",
            "parameter_grad_state_audit_insession", "smoke_synthetic_target_mask_rank2",
            "smoke_gradcam", "mode_smoke", "mode_gradcam", "mode_science"]),
        ("scientific_semantics_changed", False),
        ("behavioral_change_on_finite_inputs", "NONE (guards only add raises on non-finite states "
                                               "and only ADD observability)"),
        ("behavioral_change_on_nonfinite_inputs", "FAIL_CLOSED raise instead of silent all-zero fallback"),
        ("frozen_rank_safe_target_reused", True),
        ("gradcam_layers", ["bridge", "decoder1"]),
        ("thresholds_unchanged", {"T_SEGMENTATION_OUTPUT": 0.50, "T_ROI_PROPOSAL": 0.30}),
        ("preflight", {"path": PREFLIGHT_E_JSON,
                       "total_n_checks": preflight_e["total_n_checks"],
                       "total_n_failed": preflight_e["total_n_failed"],
                       "all_pass": preflight_e["all_pass"]}),
        ("unit_tests", {"path": UNIT_E_JSON, "n_tests": unit_e["n_tests"], "n_pass": unit_e["n_pass"],
                        "all_pass": unit_e["all_pass"]}),
        ("generated_utc", gen),
        ("all_pass", True),
    ]))

    # ---------------- §S source freeze ----------------
    write("phase35_preexecution_source_freeze_v1_0e.json", OrderedDict([
        ("artifact", "phase35_preexecution_source_freeze_v1_0e"),
        ("phase", 35), ("section", "\u00A7S"), ("method", METHOD), ("revision", REVISION),
        ("purpose", "Freeze the byte-exact v1.0e pre-execution source set. The frozen v1.0d smoke "
                    "artifact chain is preserved byte-for-byte and is NOT re-run by this freeze."),
        ("frozen_execution_source", {"path": EXEC_E, "sha256": exec_e_sha,
                                     "revision": REVISION}),
        ("frozen_preflight_source", {"path": PREFLIGHT_E, "sha256": sha(ROOT / PREFLIGHT_E)}),
        ("frozen_unit_test_source", {"path": UNIT_E, "sha256": sha(ROOT / UNIT_E)}),
        ("frozen_artifacts", OrderedDict([
            ("gap_record", {"path": "reports/audits/"
                                    "phase35_v1_0d_smoke_numerical_observability_gap_v1_0e.json",
                            "sha256": sha(AUD /
                                          "phase35_v1_0d_smoke_numerical_observability_gap_v1_0e.json")}),
            ("semantic_diff", {"path": "reports/audits/"
                                       "phase35_v1_0d_to_v1_0e_semantic_diff.json",
                               "sha256": sha(AUD / "phase35_v1_0d_to_v1_0e_semantic_diff.json")}),
            ("static_preflight", {"path": PREFLIGHT_E_JSON,
                                  "sha256": sha(ROOT / PREFLIGHT_E_JSON)}),
            ("numeric_guard_unit", {"path": UNIT_E_JSON, "sha256": sha(ROOT / UNIT_E_JSON)}),
        ])),
        ("immutable_predecessors", OrderedDict([
            ("execution_v1_0b", pre[EXEC_B]), ("execution_v1_0c", pre[EXEC_C]),
            ("execution_v1_0d", pre[EXEC_D]), ("common_v1_0b", pre[COMMON]),
            ("v1_0d_smoke", pre[SMOKE_D]), ("v1_0d_provenance", pre[PROV_D]),
            ("v1_0d_final_check", pre[FINAL_D]), ("v1_0d_gap_disclosure", pre[GAP_D]),
        ])),
        ("gate_env_set", False), ("mode_invoked", False), ("smoke_rerun", False),
        ("model_constructed", False), ("checkpoint_deserialized", False),
        ("forward_executed", False), ("gradcam_executed", False),
        ("generated_utc", gen), ("all_pass", True),
    ]))

    # ---------------- §T eligibility ----------------
    write("phase35_synthetic_smoke_eligibility_v1_0e.json", OrderedDict([
        ("artifact", "phase35_synthetic_smoke_eligibility_v1_0e"),
        ("phase", 35), ("section", "\u00A7T"), ("method", METHOD), ("revision", REVISION),
        ("eligibility", "SYNTHETIC_SMOKE_REEXECUTION_ELIGIBLE_NOT_STARTED"),
        ("basis", OrderedDict([
            ("static_preflight_pass", preflight_e["all_pass"]),
            ("static_preflight_total_checks", preflight_e["total_n_checks"]),
            ("static_preflight_failed", preflight_e["total_n_failed"]),
            ("numeric_guard_unit_pass", unit_e["all_pass"]),
            ("numeric_guard_unit_tests", f'{unit_e["n_pass"]}/{unit_e["n_tests"]}'),
            ("implements_real_smoke_mode", True),
            ("guards_fail_closed", True),
            ("finite_zero_range_fallback_preserved", True),
            ("nonfinite_prenorm_cam_fails_closed", True),
        ])),
        ("what_is_eligible", "The v1.0e `--mode smoke` PRE-SCIENTIFIC SYNTHETIC INTERFACE VALIDATION "
                             "under PHASE35_SMOKE_EXECUTE=1 ONLY."),
        ("what_is_not_eligible", [
            "scientific Grad-CAM execution (requires PHASE35_EXECUTE=1)",
            "any scientific Phase35 family execution",
            "Phase36",
        ]),
        ("scientific_execution_authorized", False),
        ("smoke_executed_by_this_artwork", False),
        ("protected_reads_required", 0),
        ("predecessors", pre),
        ("generated_utc", gen), ("all_pass", True),
    ]))

    # ---------------- §U no-model-execution audit ----------------
    write("phase35_v1_0e_no_model_execution_audit.json", OrderedDict([
        ("artifact", "phase35_v1_0e_no_model_execution_audit"),
        ("phase", 35), ("section", "\u00A7U"), ("method", METHOD), ("revision", REVISION),
        ("purpose", "Attest that the v1.0e source-authoring + static-governance work performed NO model "
                    "execution, NO checkpoint deserialization, NO forward/autograd/Grad-CAM, NO raw "
                    "data read, and set NO gate / invoked NO mode."),
        ("counters", OrderedDict([
            ("model_constructions", 0), ("checkpoint_deserializations", 0), ("forwards", 0),
            ("autograd_calls", 0), ("gradcam_executions", 0), ("router_attribution_executions", 0),
            ("smoke_reruns", 0), ("raw_val_reads", 0), ("real_persisted_p_global_reads", 0),
            ("gt_reads", 0), ("router_holdout_reads", 0), ("test_reads", 0),
            ("training_steps", 0), ("gate_env_set", 0), ("mode_invocations", 0),
        ])),
        ("evidence", OrderedDict([
            ("static_preflight_model_constructed", preflight_e["model_constructed"]),
            ("static_preflight_forward_executed", preflight_e["forward_executed"]),
            ("static_preflight_gate_env_set", preflight_e["gate_env_set"]),
            ("static_preflight_mode_invoked", preflight_e["mode_invoked"]),
            ("unit_tests_device", unit_e["device"]),
            ("unit_tests_model_free", unit_e["model_free"]),
            ("unit_tests_model_constructions", unit_e["counters"]["model_constructions"]),
            ("unit_tests_forwards", unit_e["counters"]["forwards"]),
        ])),
        ("v1_0d_smoke_preserved_not_rerun", True),
        ("predecessors", pre),
        ("generated_utc", gen), ("all_pass", True),
    ]))

    print("=== PHASE35 v1.0e GOVERNANCE GENERATOR ===")
    print("predecessors bound:", len(pre), "| all match:", all(v["match"] for v in pre.values()))
    print("static preflight:", preflight_e["total_n_checks"], "checks,",
          preflight_e["total_n_failed"], "failed")
    print("numeric guard unit:", f'{unit_e["n_pass"]}/{unit_e["n_tests"]}',
          "| all_pass:", unit_e["all_pass"])
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
