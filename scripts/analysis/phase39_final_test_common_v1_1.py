"""Phase39 final TEST execution — frozen protocol constants (v1.1).

v1.1 differs from v1.0 ONLY by:
  (a) the D98 dependency-closure loader repair (technical, scientific_delta=0),
  (b) an operational ordering repair that moves all TEST-independent
      pre-inference work (model construction / strict load / device / metric /
      comparator binding / output-absence) BEFORE first TEST-manifest access,
  (c) a distinct v1.1 output namespace and a v1.0 consumed-history gate.

No scientific semantic changes: checkpoints, architecture, weights, comparators,
metrics, thresholds, D61, D75/POLICY_B, task IDs, population, sample inclusion,
statistical method, claim policy, result shells, subgroup rules are UNCHANGED.
"""
from __future__ import annotations

from pathlib import Path

PHASE = 39
REVISION = "ra_medfilm_barr_phase39_final_test_v1_1"
METHOD = "RA-MedFiLM-BARR"
CLASSIFICATION = "PHASE39_FINAL_TEST_SCIENTIFIC_RESULT"
EVIDENCE_CLASS = "FINAL_UNTOUCHED_INTERNAL_TEST_GENERALIZATION_EVIDENCE"

ROOT = Path(__file__).resolve().parents[2]

GATE_ENV = "PHASE39_FINAL_TEST_GATE"
GATE_ENV_VALUE = "I_ACKNOWLEDGE_PHASE39_ONE_SHOT_TEST_EXECUTION"

AUTHORITY_BUNDLE = "reports/audits/phase39_v1_1_prelaunch_authority_bundle.json"
PHASE37_ROOT_MANIFEST = "reports/audits/phase37_sha256_manifest.json"
PHASE37_ROOT_MANIFEST_SHA256 = "221a918b0c87b62ebb568020be90653218808488485c59945789e0f03e8098a6"

POPULATION_NAME = "TEST"
TEST_N = 1683
TEST_MANIFEST = "manifests/phase4_v3/test.csv"
TASKS = {0: "ISIC", 1: "BUSI", 2: "KVASIR", 3: "KUB"}
TASKS_REV = {v: k for k, v in TASKS.items()}
DOMAIN_ORDER = ["ISIC", "BUSI", "KVASIR", "KUB"]

COMPONENTS = {
    "G": {"class": "GlobalMedFiLM",
          "checkpoint": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
          "sha256": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
          "params": 3523001, "role": "always_executed"},
    "B_phi": {"class": "BARRBenefitRouterV1",
              "checkpoint": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
              "sha256": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
              "params": 36801, "role": "pre_gate_always_executed"},
    "R_psi": {"class": "BARRRegionalRefinerV1",
              "checkpoint": "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
              "sha256": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
              "params": 1276401, "role": "EXECUTE_branch_only"},
    "S_omega": {"class": "BARRPostSafetyV1",
                "checkpoint": "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
                "sha256": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
                "params": 1217, "role": "EXECUTE_branch_only"},
}

G_INPUT_SHAPE = (3, 512, 512)
G_BATCH_SIZE = 8
CANONICAL_DEVICE_CONTRACT = {"call": "get_device(require_cuda=True)", "required_device_type": "cuda",
                             "cpu_scientific_fallback_permitted": False}
PROBABILITY_OPERATOR = "sigmoid(logits.float())"
D75_POLICY_B = {"live": "float32", "persist": "float16", "score": "float32", "threshold": 0.50}
SEGMENTATION_THRESHOLD = 0.50
ROI_P_GLOBAL_THRESHOLD = 0.30
ROI_MARGIN = 0.25
ROI_EXPANSION = 1.5
ROI_CANVAS = 512
ROI_CROP = 256
S_OMEGA_ACCEPT_THRESHOLD = 0.50
STATE_MACHINE = ["FORCED_SKIP", "SKIP_GLOBAL", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT"]
CANONICAL_STRUCTURAL_CHOICES = {"system": "A8/C9", "nominal_budget": 0.25, "lambda_representative": 0.25,
                                "roi_proposal_threshold": 0.3, "s_omega_threshold": 0.5,
                                "segmentation_threshold": 0.5, "K": 1239}

# ---- v1.1 OUTPUT NAMESPACE (distinct from v1.0) ----
OUT = {
    "START": "reports/audits/phase39_final_test_v1_1_start.json",
    "RESULT": "reports/audits/phase39_final_test_v1_1_scientific_result.json",
    "FAILURE": "reports/audits/phase39_final_test_v1_1_failure.json",
    "PROCESS_EXIT": "reports/audits/phase39_final_test_v1_1_process_exit.json",
    "per_sample_table": "reports/tables/phase39_final_test_v1_1/per_sample.csv",
    "per_domain_summary": "reports/tables/phase39_final_test_v1_1/per_domain.csv",
    "statistical_output": "reports/audits/phase39_final_test_v1_1_statistical.json",
    "figure_registry": "reports/audits/phase39_final_test_v1_1_figure_registry.json",
    "journal": "reports/audits/phase39_final_test_v1_1_journal.jsonl",
}
WRITE_SEMANTICS = "open(x, 'x') exclusive-create; no overwrite fallback"
METRIC_MODULE = "src.metrics.evaluation_metrics"

PHASE30_QUALIFIER = "ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION"
COUNTERS_FOREVER_ZERO = ["training", "optimizer_steps", "parameter_mutations",
                         "checkpoint_selections", "threshold_selections", "hyperparameter_selections"]

# ---- v1.0 CONSUMED-HISTORY GATE (exact hashes) ----
V1_0_HISTORY = {
    "failure_path": "reports/audits/phase39_final_test_failure.json",
    "failure_sha256": "19e8d3f545c3c977fb273c16d21c383276b25fb85227be1048eaa19a8e5134ff",
    "process_exit_path": "reports/audits/phase39_final_test_process_exit.json",
    "process_exit_sha256": "3924c407919147ac556cfa0721a9d95b17eff4c19bf722953368a27375845e8a",
    "journal_path": "reports/audits/phase39_final_test_journal.jsonl",
    "journal_sha256": "65c051135c4ecc04c95930f66a3f0f898e93e2636f1da67ccc1faf2c8244cb43",
    "result_path": "reports/audits/phase39_final_test_scientific_result.json",
    "start_path": "reports/audits/phase39_final_test_start.json",
    "execution_source_sha256": "0f2fcad3fc2de19cd24b86777a48fe7fe30349cef5fef9467b84a3faf274c7df",
    "launcher_sha256": "bd06c74e977a5c3a9cf4a1246c616d5a18c4f9b10c6c4483ddc2000247d6f1ac",
    "supervisor_sha256": "5e4e24fec2c0614363b15f0ccea976cb13d08b9b0d13ce5e80a0e8ba32a2f485",
    "authority_bundle_sha256": "ffe5e14717a6117df16df6a80ab2ac3ea801d9c5bce6f12c50b7c4fc56c38ca1",
    "failure_stage": "MODEL_LOAD",
    "test_inference_started": False,
    "same_version_rerun_permitted": False,
}
