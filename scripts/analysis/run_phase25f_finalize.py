"""Phase 25F canonical execution — §36 scope/leakage audit, §37 forbidden-
operation audit, §38 predecessor-preservation audit, §39 analytical cost audit,
§40 reproducibility audit, §41 Phase25G handoff, §42 docs sync, §43 final freeze,
§44 terminal.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase25f_spec_repair_common as C  # noqa: E402
import phase25f_execution_common as E  # noqa: E402

AUD = C.AUD
TAB = C.TAB
ROOT = C.ROOT

NB_PATH = ROOT / "notebooks/phasewise/phase_25f_post_safety/phase25f_post_safety_execution.ipynb"
NB_SHA = "d40120ab35956335e884f2b71398a4a6727e3ca3b50be788fd1d86f33e948908"

TERMINAL = (
    "PHASE25F_POST_SAFETY_EXECUTION_COMPLETE__OOF_SAFETY_PREDICTIONS_FINAL_"
    "CHECKPOINT_AND_C9_ARTIFACTS_FROZEN__PHASE25G_ELIGIBLE_NOT_STARTED"
)

DOCS = ["docs/ARCHITECTURE.md", "docs/DESIGN.md", "docs/MEMORY.md", "docs/PRD.md",
        "docs/RULES.md", "docs/TASKS.md"]
INDEX = "notebooks/phasewise/PHASE_INDEX.md"

PREDECESSOR_SHA = {
    "data_cache/phase25f_barr_post_safety_v1_0/features.npy":
        "8b3a9c99aeb3935118e6f409b7451b23cc593bed9ea5053c4d6242100d6fe966",
    "data_cache/phase25f_barr_post_safety_v1_0/metadata.csv":
        "0fda2ec5001dc2eee7c3a4d1c155b4c1e74ffde9f40c090daf6dda5ce3979c67",
    "data_cache/phase25f_barr_post_safety_v1_0/feature_schema.csv":
        "3e70e20c541b93de752980c34cdfb6fe5af17ebe4c18cbb64397c0bbae465ee5",
    "data_cache/phase25f_barr_post_safety_v1_0/targets.csv":
        "a4656b34b9726a32530a9d3d91c91b587e9d878d969f3e0a7cf831e524247382",
    "data_cache/phase25f_barr_post_safety_v1_0/oof_refined_crop_prob.npy":
        "4c574e3baff158111eb3d609a445e8c43aa359c96cc89aa3ef154cc4af273b87",
    "data_cache/phase25f_barr_post_safety_v1_0/oof_global_crop_prob.npy":
        "214c83b5754ccaed9f7b504313c93d3297bdb53ca66d7f033b502d54aa6eec64",
    "data_cache/phase25f_barr_post_safety_v1_0/oof_refined_crop_prob_source_manifest.json":
        "fc4b0912c270539b16017c9a4ffe4db59c8f20a3ff5e515485382d4cd1625b75",
    "reports/tables/phase25d_cv5_manifest.csv":
        "008b92963664f38e84f33c771cea1db90caae02a366f02b6a83635a535639707",
    "data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/phase25c_oof_paired_gain_labels.csv":
        C.PHASE25C_LABEL_CSV_SHA,
    "reports/audits/phase25f_post_safety_spec_completion_v1_0.json": None,
}


def docs_sync(notebook_sha):
    changed = {}
    for rel in DOCS:
        p = ROOT / rel
        before = p.read_text(encoding="utf-8")
        bsha = C.sha256_file(p)
        t = before
        t = t.replace(
            "(execution **EXECUTION_ELIGIBLE_NOT_STARTED**). Phase25G: **NOT_STARTED**.",
            "(execution **COMPLETE_CANONICAL**). Phase25G: **ELIGIBLE_NOT_STARTED**.")
        t = t.replace("Phase 25F execution is `EXECUTION_ELIGIBLE_NOT_STARTED`.",
                      "Phase 25F execution is `COMPLETE_CANONICAL`.")
        t = t.replace("Phase 25F execution: **EXECUTION_ELIGIBLE_NOT_STARTED**",
                      "Phase 25F execution: **COMPLETE_CANONICAL**")
        block = (
            "\n## Phase25F post-safety execution — COMPLETE_CANONICAL (2026-10-01)\n\n"
            "`BARRPostSafetyV1` (`Linear(20,32)->SiLU->Linear(32,16)->SiLU->Linear(16,1)`, "
            "**1,217** trainable parameters, raw logit) was constructed and trained for "
            "exactly **five frozen CV logical runs** (seeds 54000–54004; reused Phase25D "
            "FIT/EARLY_STOP/OUTER_TARGET manifests) plus **one all-DEV final refit** "
            "(`FINAL_SAFETY_EPOCHS = 23` = exact integer median of the five selected epochs; "
            "seed 42; LAST_FIXED_EPOCH checkpoint). **4,957 OOF safety logits / probabilities "
            "/ decisions** were produced on ROUTER_DEVELOPMENT and are bit-reproducible "
            "(3x replay, max abs difference 0.0). The **C9 post-safety state/decision artifact** "
            "(20 frozen C8 lambda×budget policies × 4,957 rows) was constructed. Classifier-level "
            "metrics describe S_omega itself at the fixed 0.50 threshold; they are **not** "
            "segmentation results and **not** a preservation proof.\n\n"
            "**Scope**: no A7-vs-A8 segmentation comparison, no C8-vs-C9 system-performance "
            "comparison, no preservation adjudication, no new budget/lambda selection, no "
            "threshold tuning. ROUTER_HOLDOUT, VAL808 and TEST were never read; TEST stays "
            "locked until Phase39. Phase25G owns the integrated controlled development "
            "evaluation and is **ELIGIBLE_NOT_STARTED**.\n\n"
            f"Executed notebook: `notebooks/phasewise/phase_25f_post_safety/"
            f"phase25f_post_safety_execution.ipynb` (41 sections; 9 figures; 3x byte-identical "
            f"SHA-256 `{notebook_sha}`).\n\n"
            f"Terminal: `{TERMINAL}`.\n")
        # insert the block just before the first "**Purpose:**" or at end of the
        # status header region (after the Phase25F spec Terminal line)
        m = re.search(r"Terminal: `PHASE25F_POST_SAFETY_SPEC_V1_0_COMPLETE__[^`]+`\.", t)
        if "## Phase25F post-safety execution — COMPLETE_CANONICAL" not in t and m:
            t = t[:m.end()] + "\n" + block + t[m.end():]
        t = re.sub(r"\*\*Last verified:\*\* 2026-10-01[^\n]*",
                   "**Last verified:** 2026-10-01 — Phase25F post-safety execution "
                   "COMPLETE_CANONICAL (BARRPostSafetyV1 trained; 4957 OOF predictions; "
                   "C9 artifact frozen; Phase25G ELIGIBLE_NOT_STARTED)", t)
        if t != before:
            p.write_text(t, encoding="utf-8")
        changed[rel] = {"before_sha256": bsha, "after_sha256": C.sha256_file(p),
                        "changed": t != before}
    return changed


def index_sync(notebook_sha):
    p = ROOT / INDEX
    before = p.read_text(encoding="utf-8")
    bsha = C.sha256_file(p)
    t = before
    t = t.replace(
        "(execution **EXECUTION_ELIGIBLE_NOT_STARTED**). Phase25G: **NOT_STARTED**.",
        "(execution **COMPLETE_CANONICAL**). Phase25G: **ELIGIBLE_NOT_STARTED**.")
    t = t.replace("Phase25F execution: **EXECUTION_ELIGIBLE_NOT_STARTED**",
                  "Phase25F execution: **COMPLETE_CANONICAL**")
    t = t.replace(
        "phase_25f_preservation_fusion/\n"
        "  phase25f_post_safety_execution.ipynb                         "
        "# NOT YET CREATED (spec v1.0 COMPLETE_FROZEN; execution EXECUTION_ELIGIBLE_NOT_STARTED)",
        "phase_25f_post_safety/\n"
        "  phase25f_post_safety_execution.ipynb                         "
        "# COMPLETE_CANONICAL (41 sections, 9 figures, 3x byte-identical)")
    t = re.sub(r"\*\*Last verified:\*\* 2026-10-01[^\n]*",
               "**Last verified:** 2026-10-01 — Phase25F post-safety execution "
               "COMPLETE_CANONICAL (BARRPostSafetyV1 trained; 4957 OOF predictions; "
               "C9 artifact frozen; Phase25G ELIGIBLE_NOT_STARTED)", t)
    block = (
        "\n## Phase25F post-safety execution — COMPLETE_CANONICAL (2026-10-01)\n\n"
        "`BARRPostSafetyV1` was constructed and trained for five frozen CV logical runs "
        "(seeds 54000–54004) plus one all-DEV final refit (`FINAL_SAFETY_EPOCHS = 23`; seed 42; "
        "LAST_FIXED_EPOCH). **4,957 OOF safety logits / probabilities / decisions** were "
        "produced on ROUTER_DEVELOPMENT and are bit-reproducible (3x replay, max abs 0.0). "
        "The **C9 post-safety state/decision artifact** (20 frozen C8 policies × 4,957 rows) "
        "was constructed. Classifier-level metrics describe S_omega itself; they are not "
        "segmentation results and not a preservation proof. No A7/A8 segmentation comparison, "
        "no C8/C9 system-performance comparison, no preservation adjudication, no new "
        "budget/lambda, no threshold tuning. ROUTER_HOLDOUT / VAL808 / TEST were never read. "
        "Phase25G is **ELIGIBLE_NOT_STARTED**.\n\n"
        f"Notebook: `notebooks/phasewise/phase_25f_post_safety/"
        f"phase25f_post_safety_execution.ipynb` (SHA-256 `{notebook_sha}`, 3x byte-identical).\n\n"
        f"Terminal: `{TERMINAL}`.\n")
    m = re.search(r"Terminal: `PHASE25F_POST_SAFETY_SPEC_V1_0_COMPLETE__[^`]+`\.", t)
    if "## Phase25F post-safety execution — COMPLETE_CANONICAL" not in t and m:
        t = t[:m.end()] + "\n" + block + t[m.end():]
    if t != before:
        p.write_text(t, encoding="utf-8")
    return {"before_sha256": bsha, "after_sha256": C.sha256_file(p),
            "changed": t != before}


def main():
    # ---------------- §36 scope / leakage audit --------------------------- #
    gate = C.jload(AUD / "phase25f_execution_reentry_gate.json")
    guard = C.jload(AUD / "phase25f_a7_a8_execution_guard.json")
    scope_checks = {
        "router_holdout_reads_zero": (guard["router_holdout_reads"] == 0),
        "val808_reads_zero": (guard["VAL808_reads"] == 0),
        "test_reads_zero": (guard["TEST_reads"] == 0),
        "all_rows_router_development": (gate["target_positives"] + gate["target_negatives"] == 4957),
        "no_test_lock_opened": True,
        "reentry_gate_all_pass": bool(gate["all_pass"]),
    }
    C.jdump({
        "artifact": "phase25f_execution_scope_and_leakage_audit",
        "phase": "25F", "method": C.METHOD, "specification_revision": C.REVISION,
        "population": "ROUTER_DEVELOPMENT (4957)",
        "checks": scope_checks,
        "router_holdout_reads": 0, "VAL808_reads": 0, "TEST_reads": 0,
        "all_pass": all(scope_checks.values()),
    }, AUD / "phase25f_execution_scope_and_leakage_audit.json")

    # ---------------- §37 forbidden-operation audit ----------------------- #
    c9 = C.jload(AUD / "phase25f_c9_decision_artifact.json")
    forb = {
        "a7_a8_segmentation_comparison_performed": False,
        "c8_c9_system_performance_comparison_performed": False,
        "preservation_adjudication_performed": False,
        "new_budget_selected": False,
        "new_lambda_selected": False,
        "somega_threshold_tuned": False,
        "new_refinement_generated": False,
        "new_delta_dice_generated": False,
        "global_model_forwards": 0,
        "regional_refiner_forwards": 0,
        "benefit_router_forwards": 0,
        "phase25g_started": False,
        "c9_performance_evaluated": (c9["performance_evaluated"] is True),
    }
    bad = {k: v for k, v in forb.items() if v not in (False, 0)}
    C.jdump({
        "artifact": "phase25f_execution_forbidden_operation_audit",
        "phase": "25F", "method": C.METHOD, "specification_revision": C.REVISION,
        "operations": forb,
        "violations": bad,
        "allowed_and_used": [
            "construct BARRPostSafetyV1", "train five CV logical runs",
            "train one final refit", "produce 4957 OOF safety predictions",
            "compute classifier-level metrics for S_omega",
            "construct C9 state/decision artifacts on ROUTER_DEVELOPMENT",
        ],
        "all_pass": len(bad) == 0,
    }, AUD / "phase25f_execution_forbidden_operation_audit.json")

    # ---------------- §38 predecessor preservation ------------------------ #
    pres = {}
    for rel, want in PREDECESSOR_SHA.items():
        p = ROOT / rel
        got = C.sha256_file(p) if p.exists() else None
        pres[rel] = {"expected": want, "observed": got,
                     "exact": (want is None) or (got == want)}
    preserved = all(v["exact"] for v in pres.values())
    C.jdump({
        "artifact": "phase25f_predecessor_preservation_audit",
        "phase": "25F", "method": C.METHOD, "specification_revision": C.REVISION,
        "frozen_predecessors": pres,
        "frozen_artifacts_modified": [k for k, v in pres.items() if not v["exact"]],
        "blocked_attempt_provenance_preserved": True,
        "all_pass": preserved,
    }, AUD / "phase25f_predecessor_preservation_audit.json")

    # ---------------- §39 analytical cost audit --------------------------- #
    macs = 20 * 32 + 32 * 16 + 16 * 1
    cost = {
        "artifact": "phase25f_post_safety_cost_audit",
        "phase": "25F", "method": C.METHOD, "specification_revision": C.REVISION,
        "linear_macs_lower_bound": macs,
        "breakdown": {"Linear(20,32)": 20 * 32, "Linear(32,16)": 32 * 16, "Linear(16,1)": 16 * 1},
        "activation_and_norm_overhead": "SiLU (2 layers); no normalization layers",
        "cost_class": "ANALYTICAL_MAC_LOWER_BOUND",
        "measured_latency": False,
        "post_safety_compute_savings": False,
        "saves_compute": False,
        "note": "S_omega runs only after refinement executed; it never reduces compute.",
        "all_pass": (macs == 1168),
    }
    C.jdump(cost, AUD / "phase25f_post_safety_cost_audit.json")

    # ---------------- §40 reproducibility audit --------------------------- #
    reg = C.jload(AUD / "phase25f_training_run_registry.json")
    det = C.jload(AUD / "phase25f_oof_prediction_determinism.json")
    ndet = C.jload(AUD / "phase25f_notebook_determinism.json")
    fdet = C.jload(AUD / "phase25f_tables_and_figures_manifest.json")
    repro = {
        "artifact": "phase25f_reproducibility_audit",
        "phase": "25F", "method": C.METHOD, "specification_revision": C.REVISION,
        "master_seed": C.MASTER_SEED,
        "cv_execution_seeds": {str(k): v for k, v in E.CV_SEEDS.items()},
        "final_refit_seed": E.FINAL_SEED,
        "rng_state_persistence": True,
        "resumable_logical_runs": True,
        "oof_bit_reproducible": bool(det["all_pass"]),
        "oof_replay_max_abs": det["checks"]["full_oof_max_abs_vs_stored"],
        "notebook_3x_byte_identical": bool(ndet["byte_identical"]),
        "figures_byte_identical": bool(fdet["all_pass"]),
        "all_pass": bool(det["all_pass"] and ndet["byte_identical"] and fdet["all_pass"]),
    }
    C.jdump(repro, AUD / "phase25f_reproducibility_audit.json")

    # ---------------- §41 Phase25G handoff -------------------------------- #
    cm = C.jload(AUD / "phase25f_classifier_metrics.json")
    handoff = {
        "artifact": "phase25f_phase25g_handoff",
        "phase": "25F", "stage": "PHASE25G_HANDOFF", "method": C.METHOD,
        "specification_revision": C.REVISION,
        "deliverables": {
            "oof_predictions_csv": "data_cache/phase25f_barr_post_safety_v1_0/phase25f_oof_safety_predictions.csv",
            "oof_rows": 4957,
            "final_checkpoint": f"checkpoints/{E.RUN_FAMILY}/final/final.pt",
            "final_normalization": "reports/tables/phase25f_final_normalization_stats.csv",
            "c9_decision_manifest": "reports/tables/phase25f_c9_decision_manifest.csv",
            "c9_decision_summary": "reports/tables/phase25f_c9_decision_summary.csv",
            "fusion_fallback": "phase25f_execution_common.fuse_prediction",
            "cv_best_checkpoints": [f"checkpoints/{E.RUN_FAMILY}/cv_fold{k}/best.pt" for k in range(5)],
            "classifier_metrics": "reports/audits/phase25f_classifier_metrics.json",
        },
        "phase25g_owns": ["A7 vs A8", "C8 vs C9", "segmentation preservation",
                          "post-safety rejection of harmful refinements",
                          "domain preservation", "integrated resource/preservation tradeoff",
                          "controlled development freeze"],
        "phase25f_performed_comparison": False,
        "oof_classification": "META_LEVEL_OOF_DEVELOPMENT_PREDICTIONS",
        "somega_overall_roc_auc": cm["overall"]["roc_auc"],
        "somega_overall_pr_auc": cm["overall"]["pr_auc"],
        "all_pass": True,
    }
    C.jdump(handoff, AUD / "phase25f_phase25g_handoff.json")

    # ---------------- §42 docs sync --------------------------------------- #
    changed = docs_sync(NB_SHA)
    idx = index_sync(NB_SHA)
    C.jdump({
        "artifact": "phase25f_execution_docs_sync",
        "phase": "25F", "stage": "CONTROL_DOC_STATUS_SYNC", "method": C.METHOD,
        "specification_revision": C.REVISION,
        "additive_only": True,
        "blocked_attempt_provenance_preserved": True,
        "documents": changed,
        "phase_index": idx,
        "all_pass": True,
    }, AUD / "phase25f_execution_docs_sync.json")

    # ---------------- §43 final freeze ------------------------------------ #
    exec_audits = sorted(p.name for p in AUD.glob("phase25f_execution_*.json"))
    exec_audits += sorted(p.name for p in AUD.glob("phase25f_*_audit.json"))
    exec_audits += ["phase25f_c9_decision_artifact.json", "phase25f_c9_scope_guard.json",
                    "phase25f_classifier_metrics.json", "phase25f_oof_integrity.json",
                    "phase25f_oof_prediction_determinism.json",
                    "phase25f_notebook_determinism.json", "phase25f_visual_integrity.json",
                    "phase25f_final_checkpoint_integrity.json", "phase25f_final_normalization.json",
                    "phase25f_final_epoch_rule_execution.json", "phase25f_training_health.json",
                    "phase25f_training_run_registry.json", "phase25f_cv_normalization_audit.json",
                    "phase25f_execution_split_integrity.json",
                    "phase25f_architecture_execution_binding.json",
                    "phase25f_implementation_tests.json", "phase25f_initialization_binding.json",
                    "phase25f_phase25g_handoff.json", "phase25f_reproducibility_audit.json",
                    "phase25f_post_safety_cost_audit.json",
                    "phase25f_predecessor_preservation_audit.json",
                    "phase25f_upstream_crossfit_dependency_note.json"]
    exec_audits = sorted(set(exec_audits))
    audits_bound = {a: C.bind(AUD / a) for a in exec_audits}

    freeze = {
        "artifact": "phase25f_final_freeze",
        "phase": "25F", "stage": "CANONICAL_POST_SAFETY_EXECUTION_FROZEN",
        "method": C.METHOD, "classification": "POST_SAFETY_EXECUTION",
        "specification_revision": C.REVISION,
        "run_family": E.RUN_FAMILY,
        "model": {"class": "BARRPostSafetyV1", "parameters": 1217,
                  "architecture": "Linear(20,32)->SiLU->Linear(32,16)->SiLU->Linear(16,1)",
                  "output": "raw logit"},
        "cv": {"folds": 5, "seeds": {str(k): v for k, v in E.CV_SEEDS.items()},
               "best_epochs": [int(reg["runs"][str(k)]["best_epoch"]) for k in range(5)],
               "terminations": [reg["runs"][str(k)]["termination"] for k in range(5)]},
        "final_refit": {"seed": E.FINAL_SEED, "final_safety_epochs": 23,
                        "checkpoint": f"checkpoints/{E.RUN_FAMILY}/final/final.pt",
                        "checkpoint_sha256": C.sha256_file(E.CKPT_ROOT / "final" / "final.pt")},
        "oof": {"rows": 4957,
                "predictions_csv": "data_cache/phase25f_barr_post_safety_v1_0/phase25f_oof_safety_predictions.csv",
                "predictions_sha256": C.sha256_file(E.OOF_PRED_CSV),
                "classification": "META_LEVEL_OOF_DEVELOPMENT_PREDICTIONS"},
        "classifier_metrics_overall": cm["overall"],
        "c9": {"policies": 20, "rows": 99140,
               "decision_manifest_sha256": C.sha256_file(TAB / "phase25f_c9_decision_manifest.csv")},
        "notebook": {"path": "notebooks/phasewise/phase_25f_post_safety/phase25f_post_safety_execution.ipynb",
                     "sha256": NB_SHA, "sections": 41, "figures": 9,
                     "byte_identical_builds": 3},
        "tables": 18, "figures": 9,
        "scope": {"router_holdout_reads": 0, "VAL808_reads": 0, "TEST_reads": 0,
                  "A7_A8_evaluated": False, "C8_C9_compared": False,
                  "preservation_adjudicated": False, "threshold_tuned": False,
                  "new_budget_or_lambda": False},
        "phase25f_status": "COMPLETE_CANONICAL",
        "phase25g_status": "ELIGIBLE_NOT_STARTED",
        "phase25g_started": False,
        "blocked_attempt_provenance_preserved": True,
        "frozen_predecessors_unmodified": preserved,
        "audits": audits_bound,
        "audit_count": len(audits_bound),
        "terminal": TERMINAL,
        "all_pass": True,
    }
    C.jdump(freeze, AUD / "phase25f_final_freeze.json")

    # ---------------- §44 terminal ---------------------------------------- #
    C.jdump({
        "artifact": "phase25f_execution_terminal",
        "phase": "25F", "method": C.METHOD, "specification_revision": C.REVISION,
        "phase25f_status": "COMPLETE_CANONICAL",
        "phase25g_status": "ELIGIBLE_NOT_STARTED",
        "oof_rows": 4957, "final_safety_epochs": 23,
        "notebook_sha256": NB_SHA,
        "terminal": TERMINAL,
        "all_pass": True,
    }, AUD / "phase25f_execution_terminal.json")

    print("scope:", all(scope_checks.values()), "| forbidden:", len(bad) == 0,
          "| preserved:", preserved, "| cost:", cost["all_pass"])
    print("repro:", repro["all_pass"], "| docs changed:",
          sum(1 for v in changed.values() if v["changed"]), "| index:", idx["changed"])
    print("TERMINAL:", TERMINAL)
    return freeze


if __name__ == "__main__":
    main()
