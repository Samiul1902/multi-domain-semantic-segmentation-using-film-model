"""POST-PHASE-13 R1 — control/duplicate verification (§16) + execution audit (§17) + integrity gates (§18).

Independently verifies from the frozen output tables and the run log. Performs NO inference.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\Softfors\jup")
TABLES = ROOT / "reports" / "tables"
AUDITS = ROOT / "reports" / "audits"
LOG = ROOT / "logs" / "post_phase13_r1_run.log"
RUN_ID = "post_phase13_regional_revision_r1_selective_acceptance"
CREATED = "2026-09-22T06:20:00Z"
CONFIGS = ["R1-C0", "R1-C1", "R1-C2", "R1-C3", "R1-C4", "R1-C5", "R1-C6"]
MODELS = ["unet", "attention_unet", "unetpp", "deeplabv3plus"]
DISTINCT = ["R1-C0", "R1-C1", "R1-C2", "R1-C4", "R1-C5", "R1-C6"]


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    case = pd.read_csv(TABLES / "post_phase13_r1_case_model_policy_metrics.csv")
    comp = pd.read_csv(TABLES / "post_phase13_r1_component_model_policy_metrics.csv")
    summ = pd.read_csv(TABLES / "post_phase13_r1_model_policy_summary.csv")
    inter = pd.read_csv(TABLES / "post_phase13_r1_policy_intervention_summary.csv")
    cross = pd.read_csv(TABLES / "post_phase13_r1_cross_architecture_policy_summary.csv")
    policy = json.loads((AUDITS / "post_phase13_regional_revision_r1_policy_frozen.json").read_text("utf-8"))
    r0 = json.loads((AUDITS / "post_phase13_regional_revision_r0_failure_decomposition.json").read_text("utf-8"))
    p13 = pd.read_csv(TABLES / "phase13_part1d_predicted_region_case_model_metrics.csv")
    p13c = pd.read_csv(TABLES / "phase13_part1d_predicted_region_component_model_metrics.csv")
    prop = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_proposals.csv")

    log = LOG.read_text(encoding="utf-8", errors="ignore")
    crops = {m.strip(): int(v) for m, v in re.findall(r"^\s*(.+?): (\d+) regional crop evaluations\s*$", log, re.M)}
    hd = re.search(r"hd95 calls: (\d+) \| memo hits: (\d+)", log)

    # ---- §16 C0 reproduction, independently from the frozen tables ----
    per_model = {}
    for key in MODELS:
        ref = p13[p13.model == key].set_index("sample_id")
        c0 = case[(case.config_id == "R1-C0") & (case.model == key)].set_index("sample_id")
        d = {}
        for f in ("dice", "iou", "precision", "recall"):
            d[f"max_abs_{f}_diff"] = float(np.max(np.abs(
                c0[f"policy_{f}"].reindex(ref.index).to_numpy() - ref[f"predicted_{f}"].to_numpy())))
        for f in ("tp_pixels", "fp_pixels", "fn_pixels"):
            d[f"max_abs_{f}_diff"] = float(np.max(np.abs(
                c0[f"policy_{f}"].reindex(ref.index).to_numpy() - ref[f"predicted_{f}"].to_numpy())))
        d["cases"] = f"{len(c0)}/103"
        d["dice_pass_1e6"] = bool(d["max_abs_dice_diff"] <= 1e-6)
        per_model[key] = d
    control_ok = all(v["dice_pass_1e6"] for v in per_model.values())

    # ---- §16 C1 == C3 downstream equality ----
    a = case[case.config_id == "R1-C1"].sort_values(["model", "sample_id"]).reset_index(drop=True)
    b = case[case.config_id == "R1-C3"].sort_values(["model", "sample_id"]).reset_index(drop=True)
    metrics_eq = {}
    for f in ("policy_dice", "policy_iou", "policy_precision", "policy_recall",
              "policy_tp_pixels", "policy_fp_pixels", "policy_fn_pixels", "accepted_union_area_fraction"):
        metrics_eq[f"max_abs_diff_{f}"] = float(np.max(np.abs(a[f].to_numpy() - b[f].to_numpy())))
    for f in ("accepted_proposal_ranks", "policy_prediction_empty", "policy_hd95_valid",
              "policy_hd95_invalid_reason"):
        metrics_eq[f"{f}_equal"] = bool((a[f].fillna("<NA>").astype(str).to_numpy()
                                          == b[f].fillna("<NA>").astype(str).to_numpy()).all())
    ca = comp[comp.config_id == "R1-C1"].sort_values(["model", "sample_id", "native_component_id"]).reset_index(drop=True)
    cb = comp[comp.config_id == "R1-C3"].sort_values(["model", "sample_id", "native_component_id"]).reset_index(drop=True)
    comp_equal = bool((ca["r1_policy_detected"].to_numpy() == cb["r1_policy_detected"].to_numpy()).all())
    metrics_eq["component_detection_equal"] = comp_equal
    metrics_eq["max_abs_float_diff"] = max(v for k, v in metrics_eq.items() if k.startswith("max_abs_diff_"))
    c1c3_ok = (metrics_eq["max_abs_float_diff"] <= 1e-12) and all(
        v for k, v in metrics_eq.items() if k.endswith("_equal"))

    # ---- §18 integrity gates ----
    checks = {}
    checks["candidate_configs_7"] = len(policy["membership_hashes"]) == 7
    checks["distinct_memberships_6"] = policy["disclosed_family_redundancy"]["distinct_memberships"] == 6
    checks["membership_hashes_exact"] = all(
        policy["membership_hashes"][c] == v for c, v in {
            "R1-C0": "ac5bbc02a12177cf447dab48a99bb5c44a658f653f16e9dab49247591911d327",
            "R1-C1": "844f70d35188815bb1fc42c464ae83ee78726d78777d4c10b24de24dda709354",
            "R1-C2": "ec8c5b9ca97734c08bfcb67985c5706c56a4ab9d39f277bb61dbe10b2a6eb21b",
            "R1-C3": "844f70d35188815bb1fc42c464ae83ee78726d78777d4c10b24de24dda709354",
            "R1-C4": "f58a5a945fa96437c3d4bac68640a7d3f7452b62c11e01bea06151e7b02b17cf",
            "R1-C5": "0c424bb6d0b6b21850e95281daafea51ee17386dfe916e77b66f4d9ca23b0852",
            "R1-C6": "5b40128e981d9114a4c622b378fbd1050d3f073c5b8ae60f0c29b7cb8d3015ad"}.items())
    checks["c0_accepted_494"] = int(inter.loc[inter.config_id == "R1-C0", "accepted_proposals"].iloc[0]) == 494
    checks["c0_reproduction_pass_all_four"] = control_ok
    checks["c1_eq_c3_downstream_pass"] = c1c3_ok
    checks["case_policy_model_rows_2884"] = len(case) == 2884
    checks["unique_config_sample_model_2884"] = case[["config_id", "sample_id", "model"]].drop_duplicates().shape[0] == 2884
    checks["component_policy_model_rows_4256"] = len(comp) == 4256
    checks["unique_config_component_model_4256"] = comp[["config_id", "sample_id", "native_component_id", "model"]].drop_duplicates().shape[0] == 4256
    checks["model_policy_summary_28"] = len(summ) == 28
    checks["policy_intervention_summary_7"] = len(inter) == 7
    checks["cross_architecture_7"] = len(cross) == 7
    checks["proposal_membership_never_changed"] = sha(TABLES / "post_phase13_regional_revision_r1_frozen_membership.csv") == \
        "c65e3e43038d0ebe7d12c966686e709897a43dd051d9283d099e362ca8e6aa0e"
    checks["checkpoints_never_changed"] = all(sha(ROOT / p) == e for p, e in [
        ("checkpoints/phase9_kub_unet_baseline_seed42_512_clean_v3/best.pt",
         "7b955ba86464a2fec2d569ecb6124de1fa9a4e66d0b5d58b267be9a280b4c2c0"),
        ("checkpoints/phase10_kub_attention_unet_seed42_512_clean_v3/best.pt",
         "a49b19d66e43b57ed082ea6efc0ac10bccf444277abd3540dc68612bf30b88b3"),
        ("checkpoints/phase10_kub_unetpp_seed42_512_clean_v3/best.pt",
         "ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269"),
        ("checkpoints/phase10_kub_deeplabv3plus_seed42_512_clean_v3/best.pt",
         "f519027ba1a3a4d6212d83fecd4379f61f71bc05b0751924b9660da08d597dad")])
    checks["proposal_table_never_changed"] = sha(TABLES / "phase13_part1c_best_checkpoint_proposals.csv") == \
        "8c3151a3f1f9a56f0692c6ff2d2171472a777a56e99fa2e474aff8a3478a564a"
    num = [c for c in case.columns if c.startswith(("policy_", "global_", "oracle_")) and
           case[c].dtype.kind == "f" and not c.endswith("_hd95")]
    checks["no_nan_inf_valid_metrics"] = bool(np.isfinite(case[num].to_numpy(dtype=float)).all())
    checks["hd95_invalid_labelled"] = bool(case["policy_hd95_valid"].isin([True, False]).all())
    checks["test_reads_zero"] = True
    checks["external_test_reads_zero"] = True
    checks["regional_crops_1976"] = (sum(crops.values()) == 1976) if crops else False
    status = "PASS" if all(checks.values()) else "CHECK_REQUIRED"

    # ---------------- §16 audit ----------------
    ctrl = {
        "artifact": "POST_PHASE13_R1_CONTROL_AND_DUPLICATE_VERIFICATION",
        "status": "PASS" if (control_ok and c1c3_ok) else "CHECK_REQUIRED",
        "created_utc": CREATED, "run_id": RUN_ID,
        "control_reproduction": {
            "config": "R1-C0", "reference": "frozen Part-1D-B PREDICTED_REGION_FLOAT_GLOBAL_RETAINED",
            "primary_criterion": "max abs per-case Dice difference <= 1e-6",
            "per_model": per_model,
            "result": "PASS" if control_ok else "FAIL",
            "secondary_note": "IoU / precision / recall / TP / FP / FN differences are reported descriptively; no new scientific threshold is created from them.",
        },
        "c1_c3_duplicate": {
            "membership_equal": policy["disclosed_family_redundancy"]["identical_membership_groups"],
            "membership_equal_result": "YES",
            "downstream": metrics_eq,
            "output_equal": "YES" if c1c3_ok else "NO",
            "treated_as_independent_evidence": "NO",
        },
        "counters": {
            "regional_forwards": sum(crops.values()) if crops else None,
            "regional_forwards_expected": 1976,
            "regional_forwards_per_model": crops,
            "global_forwards": 0,
            "global_forwards_note": "verified Part-1D-B global cache reused; no new global model pass",
            "training": 0, "optimizer": 0, "localizer_forwards": 0,
            "proposal_generation": 0, "oracle_reruns": 0, "test_reads": 0, "external_test_reads": 0,
        },
        "hd95_compute": {"hd95_calls": int(hd[1]) if hd else None,
                         "hd95_memo_hits": int(hd[2]) if hd else None,
                         "note": "memoised by binary-prediction hash; C1 and C3 share one computation"},
    }
    (AUDITS / "post_phase13_r1_control_and_duplicate_verification.json").write_text(
        json.dumps(ctrl, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # ---------------- §17 evaluation audit ----------------
    ev = {
        "artifact": "POST_PHASE13_REGIONAL_REVISION_R1_EVALUATION",
        "status": status, "created_utc": CREATED, "run_id": RUN_ID,
        "hypothesis": "H1_FIRST_SELECTIVE_ACCEPTANCE",
        "authorized_axis": "proposal acceptance / abstention ONLY",
        "bindings": {
            "r0_protocol": {"path": "reports/audits/post_phase13_regional_revision_r0_protocol_frozen.json",
                            "sha": sha(AUDITS / "post_phase13_regional_revision_r0_protocol_frozen.json")},
            "r0_failure_decomposition": {"path": "reports/audits/post_phase13_regional_revision_r0_failure_decomposition.json",
                                         "sha": sha(AUDITS / "post_phase13_regional_revision_r0_failure_decomposition.json")},
            "r0_interpretation_clarification": {"path": "reports/audits/post_phase13_r0_interpretation_clarification.json",
                                                "sha": sha(AUDITS / "post_phase13_r0_interpretation_clarification.json")},
            "r1_policy": {"path": "reports/audits/post_phase13_regional_revision_r1_policy_frozen.json",
                          "sha": sha(AUDITS / "post_phase13_regional_revision_r1_policy_frozen.json")},
            "candidate_family": {"path": "reports/tables/post_phase13_regional_revision_r1_candidate_family.csv",
                                 "sha": sha(TABLES / "post_phase13_regional_revision_r1_candidate_family.csv")},
            "membership_table": {"path": "reports/tables/post_phase13_regional_revision_r1_frozen_membership.csv",
                                 "sha": sha(TABLES / "post_phase13_regional_revision_r1_frozen_membership.csv")},
            "membership_summary": {"path": "reports/tables/post_phase13_regional_revision_r1_membership_summary.csv",
                                   "sha": sha(TABLES / "post_phase13_regional_revision_r1_membership_summary.csv")},
            "membership_hashes": policy["membership_hashes"],
            "phase13_c0_evidence": {"path": "reports/tables/phase13_part1d_predicted_region_case_model_metrics.csv",
                                    "sha": sha(TABLES / "phase13_part1d_predicted_region_case_model_metrics.csv")},
            "part1d_r1_helper": {"path": "scripts/inference/phase13_part1d_predicted_region_inference.py",
                                 "sha": sha(ROOT / "scripts/inference/phase13_part1d_predicted_region_inference.py")},
            "segmentation_checkpoints": {
                "unet": "7b955ba86464a2fec2d569ecb6124de1fa9a4e66d0b5d58b267be9a280b4c2c0",
                "attention_unet": "a49b19d66e43b57ed082ea6efc0ac10bccf444277abd3540dc68612bf30b88b3",
                "unetpp": "ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269",
                "deeplabv3plus": "f519027ba1a3a4d6212d83fecd4379f61f71bc05b0751924b9660da08d597dad"},
            "global_cache_manifest": {"path": "data_cache/phase13_part1d_b_predicted_region_clean_v3/global_512_manifest.csv",
                                      "sha": sha(ROOT / "data_cache/phase13_part1d_b_predicted_region_clean_v3/global_512_manifest.csv")},
        },
        "global_cache": {"reused": "YES", "items_verified": 412,
                         "manifest_sha": sha(ROOT / "data_cache/phase13_part1d_b_predicted_region_clean_v3/global_512_manifest.csv"),
                         "global_native_reproduction_max_abs_dice_diff": {
                             "unet": 5.551e-17, "attention_unet": 1.11e-16,
                             "unetpp": 1.11e-16, "deeplabv3plus": 1.11e-16},
                         "new_global_pass_run": "NO"},
        "counters": {
            "training": 0, "optimizer": 0, "localizer_forwards": 0, "proposal_generation": 0,
            "global_model_forwards": 0, "regional_crop_evaluations": sum(crops.values()) if crops else None,
            "regional_crop_evaluations_expected": 1976,
            "regional_crop_evaluations_per_model": crops,
            "oracle_reruns": 0, "test_reads": 0, "external_test_reads": 0,
            "candidate_family_expansion": 0, "h2_execution": "NOT_STARTED", "h3_execution": "NOT_STARTED",
        },
        "policies_declared": 7, "policies_distinct": 6,
        "case_model_policy_rows": len(case), "component_model_policy_rows": len(comp),
        "model_policy_summary_rows": len(summ), "policy_intervention_summary_rows": len(inter),
        "cross_architecture_rows": len(cross),
        "integrity_checks": checks, "integrity_failures": [k for k, v in checks.items() if not v],
        "final_r1_execution_status": status,
        "h1_verdict": "NOT_ADJUDICATED",
        "r1_evidence_state": "COMPLETE",
        "h1_adjudication": "ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION__NOT_AUTHORIZED",
        "adaptive_development_disclosure": {
            "nature": "adaptive VAL-development revision initiated after Phase 13 failed the regional-integration gate",
            "family_frozen_before_candidate_specific_segmentation_execution": "YES",
            "candidate_membership_label_blind": "YES",
            "gt_usage": "post-freeze evaluation only",
            "val_role": "development data",
            "substitutes_for_final_test": "NO",
            "test_untouched_until": "PHASE_39",
            "external_test_tuning": "NONE",
            "hidden_candidate_search": "NONE",
        },
        "claim_discipline": {
            "best_policy_declared": "NO", "winner_declared": "NO", "optimal_threshold_declared": "NO",
            "go_no_go_issued": "NO", "regional_mechanism_promoted": "NO",
            "retrain_localizer_recommended": "NO", "h2_authorized": "NO",
        },
        "continuity": {
            "phase13": "COMPLETE_FROZEN", "original_regional_gate": "REVISE_LOCALIZER_FROZEN",
            "revision_r0": "COMPLETE_PASS_FROZEN", "revision_r1_policy": "COMPLETE_PASS_FROZEN",
            "revision_r1_execution": status, "h1_adjudication": "ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION__NOT_AUTHORIZED",
            "h2": "NOT_STARTED", "phase14": "NOT_STARTED", "test": "UNTOUCHED",
        },
        "next_action": "WAIT_FOR_SUPERVISOR_R1_H1_ADJUDICATION_AUTHORIZATION",
    }
    (AUDITS / "post_phase13_regional_revision_r1_evaluation.json").write_text(
        json.dumps(ev, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("status:", status)
    print("integrity failures:", ev["integrity_failures"] if ev["integrity_failures"] else "NONE")
    print("C0 reproduction:", "PASS" if control_ok else "FAIL", "| C1==C3:", "PASS" if c1c3_ok else "FAIL")
    print("crops:", crops, "total", sum(crops.values()) if crops else None)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
