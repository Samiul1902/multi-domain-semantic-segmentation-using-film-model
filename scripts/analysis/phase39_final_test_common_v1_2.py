"""Phase39 final TEST execution — v1.2 (post-protocol technical recovery).

v1.2 authority derives SOLELY from
reports/audits/phase39_post_protocol_technical_recovery_amendment.json.

Minimal delta from v1.1:
  (D99) canonical manifest schema parsing (dataset / task_id);
  (reuse) per-sample inference DELEGATES to the frozen canonical Phase36 v1.23
          functions (canonical_learned_core / canonical_g_forward_batched / ...);
  (observability) independent failure-state counters;
  (namespace/version) v1_2 output namespace.

scientific_delta_v1_1_to_v1_2 = 0.
"""
from __future__ import annotations

from pathlib import Path

PHASE = 39
REVISION = "ra_medfilm_barr_phase39_final_test_v1_2"
METHOD = "RA-MedFiLM-BARR"
CLASSIFICATION = "PHASE39_FINAL_TEST_SCIENTIFIC_RESULT"
EVIDENCE_CLASS = "POST_PROTOCOL_TECHNICAL_RECOVERY_TEST_RESULT_WITH_TWO_DISCLOSED_PREOUTCOME_TECHNICAL_FAILURES"

ROOT = Path(__file__).resolve().parents[2]

GATE_ENV = "PHASE39_FINAL_TEST_GATE"
GATE_ENV_VALUE = "I_ACKNOWLEDGE_PHASE39_ONE_SHOT_TEST_EXECUTION"

AMENDMENT = "reports/audits/phase39_post_protocol_technical_recovery_amendment.json"
AUTHORITY_BUNDLE = "reports/audits/phase39_v1_2_prelaunch_authority_bundle.json"
PHASE37_ROOT_MANIFEST = "reports/audits/phase37_sha256_manifest.json"
PHASE37_ROOT_MANIFEST_SHA256 = "221a918b0c87b62ebb568020be90653218808488485c59945789e0f03e8098a6"
CANONICAL_PHASE36_MODULE = "scripts/analysis/phase36_robustness_execution_v1_23.py"

POPULATION_NAME = "TEST"
TEST_N = 1683
TEST_MANIFEST = "manifests/phase4_v3/test.csv"
# CANONICAL Phase4-v3 manifest schema (D99 fix): domain column is `dataset`.
MANIFEST_COLUMNS = ["dataset", "task_id", "image_path", "mask_path",
                    "patient_id", "case_id", "category", "sample_id", "split"]
DOMAIN_FIELD = "dataset"
TASK_FIELD = "task_id"
TASKS = {0: "ISIC", 1: "BUSI", 2: "KVASIR", 3: "KUB"}
TASKS_REV = {v: k for k, v in TASKS.items()}
DOMAIN_ORDER = ["ISIC", "BUSI", "KVASIR", "KUB"]

COMPONENTS = {
    "G": {"class": "GlobalMedFiLM",
          "checkpoint": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
          "sha256": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7", "params": 3523001},
    "B_phi": {"class": "BARRBenefitRouterV1",
              "checkpoint": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
              "sha256": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b", "params": 36801},
    "R_psi": {"class": "BARRRegionalRefinerV1",
              "checkpoint": "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
              "sha256": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109", "params": 1276401},
    "S_omega": {"class": "BARRPostSafetyV1",
                "checkpoint": "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
                "sha256": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e", "params": 1217},
}

G_INPUT_SHAPE = (3, 512, 512)
CANONICAL_DEVICE_CONTRACT = {"call": "get_device(require_cuda=True)", "required_device_type": "cuda",
                             "cpu_scientific_fallback_permitted": False}
SEGMENTATION_THRESHOLD = 0.50
ROI_P_GLOBAL_THRESHOLD = 0.30
ROI_MARGIN = 0.25
S_OMEGA_ACCEPT_THRESHOLD = 0.50
STATE_MACHINE = ["FORCED_SKIP", "SKIP_GLOBAL", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT"]

# ---- v1.2 OUTPUT NAMESPACE (distinct) ----
OUT = {
    "START": "reports/audits/phase39_final_test_v1_2_start.json",
    "RESULT": "reports/audits/phase39_final_test_v1_2_scientific_result.json",
    "FAILURE": "reports/audits/phase39_final_test_v1_2_failure.json",
    "PROCESS_EXIT": "reports/audits/phase39_final_test_v1_2_process_exit.json",
    "per_sample_table": "reports/tables/phase39_final_test_v1_2/per_sample.csv",
    "per_domain_summary": "reports/tables/phase39_final_test_v1_2/per_domain.csv",
    "statistical_output": "reports/audits/phase39_final_test_v1_2_statistical.json",
    "figure_registry": "reports/audits/phase39_final_test_v1_2_figure_registry.json",
    "journal": "reports/audits/phase39_final_test_v1_2_journal.jsonl",
}
WRITE_SEMANTICS = "open(x, 'x') exclusive-create; no overwrite fallback"

PHASE30_QUALIFIER = "ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION"

# ---- v1.0 + v1.1 CONSUMED-HISTORY GATE ----
HISTORY = {
    "v1_0": {
        "failure_path": "reports/audits/phase39_final_test_failure.json",
        "failure_sha256": "19e8d3f545c3c977fb273c16d21c383276b25fb85227be1048eaa19a8e5134ff",
        "process_exit_path": "reports/audits/phase39_final_test_process_exit.json",
        "process_exit_sha256": "3924c407919147ac556cfa0721a9d95b17eff4c19bf722953368a27375845e8a",
        "journal_path": "reports/audits/phase39_final_test_journal.jsonl",
        "journal_sha256": "65c051135c4ecc04c95930f66a3f0f898e93e2636f1da67ccc1faf2c8244cb43",
        "result_path": "reports/audits/phase39_final_test_scientific_result.json",
    },
    "v1_1": {
        "start_path": "reports/audits/phase39_final_test_v1_1_start.json",
        "start_sha256": "77486cdff23329bfa2fe368583702de94762d580f3bf197fafe6f0f15a348d08",
        "failure_path": "reports/audits/phase39_final_test_v1_1_failure.json",
        "failure_sha256": "e0a1ebe35031f675b3fdcd6ce8323d1e2f013d47a2b6d0e1e5c4f97e4ba207eb",
        "process_exit_path": "reports/audits/phase39_final_test_v1_1_process_exit.json",
        "process_exit_sha256": "4c616957c6f8c98856ac5ef94611871439bfa3e351d2af686db4aa1a4a91af4d",
        "journal_path": "reports/audits/phase39_final_test_v1_1_journal.jsonl",
        "journal_sha256": "3690d1b7b0e4b8429323f6bfd0322150732b7e67e4b5d5e8d0a8d4784d2c0fea",
        "result_path": "reports/audits/phase39_final_test_v1_1_scientific_result.json",
    },
}
