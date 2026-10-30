"""Phase39 final TEST execution — frozen protocol constants (v1.0).

FROZEN DURING PHASE38 (PRE-TEST). This module encodes the exact frozen
RA-MedFiLM-BARR protocol for the ONE final untouched internal TEST evaluation.
It performs NO science and opens NO TEST data at import time.

Provenance: reports/audits/phase38_* freeze artifacts.
Scientific method delta: 0. TEST must remain unopened until Phase39 executes.
"""
from __future__ import annotations

from pathlib import Path

PHASE = 39
REVISION = "ra_medfilm_barr_phase39_final_test_v1_0"
METHOD = "RA-MedFiLM-BARR"
CLASSIFICATION = "PHASE39_FINAL_TEST_SCIENTIFIC_RESULT"
EVIDENCE_CLASS = "FINAL_UNTOUCHED_INTERNAL_TEST_GENERALIZATION_EVIDENCE"

ROOT = Path(__file__).resolve().parents[2]

# ---- GATE ENV (must be set to execute science; NOT set during Phase38) ----
GATE_ENV = "PHASE39_FINAL_TEST_GATE"
GATE_ENV_VALUE = "I_ACKNOWLEDGE_PHASE39_ONE_SHOT_TEST_EXECUTION"

# ---- AUTHORITY ----
AUTHORITY_BUNDLE = "reports/audits/phase38_phase39_prelaunch_authority_bundle.json"
PHASE37_ROOT_MANIFEST = "reports/audits/phase37_sha256_manifest.json"
PHASE37_ROOT_MANIFEST_SHA256 = "221a918b0c87b62ebb568020be90653218808488485c59945789e0f03e8098a6"

# ---- POPULATION ----
POPULATION_NAME = "TEST"
TEST_N = 1683
TEST_MANIFEST = "manifests/phase4_v3/test.csv"
TASKS = {0: "ISIC", 1: "BUSI", 2: "KVASIR", 3: "KUB"}
TASKS_REV = {v: k for k, v in TASKS.items()}
DOMAIN_ORDER = ["ISIC", "BUSI", "KVASIR", "KUB"]

# ---- CHECKPOINTS (frozen identities) ----
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

# ---- INFERENCE SEMANTICS (frozen) ----
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

# ---- OUTPUT NAMESPACE (write-once / exclusive-create) ----
OUT = {
    "START": "reports/audits/phase39_final_test_start.json",
    "RESULT": "reports/audits/phase39_final_test_scientific_result.json",
    "FAILURE": "reports/audits/phase39_final_test_failure.json",
    "PROCESS_EXIT": "reports/audits/phase39_final_test_process_exit.json",
    "per_sample_table": "reports/tables/phase39_final_test/per_sample.csv",
    "per_domain_summary": "reports/tables/phase39_final_test/per_domain.csv",
    "statistical_output": "reports/audits/phase39_final_test_statistical.json",
    "figure_registry": "reports/audits/phase39_final_test_figure_registry.json",
    "journal": "reports/audits/phase39_final_test_journal.jsonl",
}
WRITE_SEMANTICS = "open(x, 'x') exclusive-create; no overwrite fallback"

# ---- METRIC MODULES (frozen) ----
METRIC_MODULE = "src.metrics.evaluation_metrics"

# ---- QUALIFIER ----
PHASE30_QUALIFIER = "ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION"

# ---- COUNTERS (forever zero) ----
COUNTERS_FOREVER_ZERO = ["training", "optimizer_steps", "parameter_mutations",
                         "checkpoint_selections", "threshold_selections", "hyperparameter_selections"]
