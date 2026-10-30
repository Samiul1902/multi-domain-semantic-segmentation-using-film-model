"""Phase27 canonical multi-domain performance preservation EXECUTION - common.

CLASSIFICATION: PHASE27_CANONICAL_MULTIDOMAIN_PRESERVATION_EXECUTION
Operational meaning: FROZEN_SYSTEM_EVALUATION_ONLY__NO_TRAINING

This is the REAL scientific run.  It opens the VAL808 image population (never
before read) to evaluate the FROZEN Phase26 A8/C9 canonical bundle.

HARD BOUNDARIES (binding):
    * NO training / fine-tuning / recalibration / policy selection
    * NO threshold change / budget change / lambda change
    * NO ROUTER_HOLDOUT (owned by Phase30)
    * NO TEST (locked until Phase39)
    * NO Phase28 / NO Phase30

Two-phase protocol with a hash barrier (§5 / §9 of the spec):
    Phase A  read VAL808 IMAGES ONLY -> global + final probability/binary
             artifacts -> hash -> freeze
    Phase B  read VAL808 GT masks -> score -> bootstrap -> adjudicate
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

import phase27_spec_common as S  # noqa: E402

AUD = ROOT / "reports" / "audits"
TABLE = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures" / "phase27_preservation"
CACHE27 = ROOT / "data_cache" / "phase27_barr_preservation_v1_0"

CLASSIFICATION = "PHASE27_CANONICAL_MULTIDOMAIN_PRESERVATION_EXECUTION"
OPERATIONAL_MEANING = "FROZEN_SYSTEM_EVALUATION_ONLY__NO_TRAINING"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_preservation_v1_0"

# ------------------------------------------------------------------ predecessor terminal
PREDECESSOR_TERMINAL_EXPECTED = (
    "PHASE27_SPEC_V1_1_COMPLETE__PHASE26_NOTEBOOK_CLOSURE_RECONCILED__"
    "NUMERICAL_INFERENCE_AND_EVIDENCE_PROVENANCE_FROZEN__PHASE27_EXECUTION_ELIGIBLE_NOT_STARTED"
)
PREDECESSOR_TERMINAL_PATH = "reports/audits/phase27_spec_v1_1_terminal.json"
PHASE26_TERMINAL_PATH = "reports/audits/phase26_canonical_integration_terminal.json"
PHASE26_TERMINAL_EXPECTED = (
    "PHASE26_CANONICAL_INTEGRATION_COMPLETE__A8_C9_25PCT_FINAL_ROUTER_RUNTIME_POLICY_AND_"
    "BUNDLE_FROZEN__PHASE27_ELIGIBLE_NOT_STARTED"
)

# ------------------------------------------------------------------ Phase26 notebook / freeze
NOTEBOOK26_PATH = (
    "notebooks/phasewise/phase_26_full_system_integration/"
    "phase26_canonical_integration_and_bundle_freeze.ipynb"
)
NOTEBOOK26_SHA = "5d063ecb57a7e213c2260a11e1daa66bb58bc2f6b5b4029cfc1ae0e3e91aa8c8"
FREEZE26_PATH = "reports/audits/phase26_final_freeze.json"
FREEZE26_SHA = "e709f5301894dc0377420500a9b6d6e95bd54858fde4cb472cad73d630b8adb4"

# ------------------------------------------------------------------ canonical bundle
BUNDLE_MANIFEST = "artifacts/phase26_ra_medfilm_barr_bundle_v1_0/canonical_bundle_manifest.json"
BUNDLE_MANIFEST_SHA = "f7aebb0f646bcc8de49fa91b70a4c4cc1051c9998ab6b055a8d4d187809cb3d9"
WRAPPER_PATH = "src/models/barr/ra_medfilm_barr.py"
WRAPPER_SHA = "342f2163690c2fa8d5a601ab1d18178b982d701b916935c33e0793b0801c3724"
VALIDATOR_PATH = "scripts/analysis/validate_phase26_canonical_bundle.py"
VALIDATOR_SHA = "912d886599adae810db14edf17331a25c37d4e92abd8fbe1fe67f94ab7810300"

COMPONENT_PATHS = {
    "global_medfilm": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
    "regional_refiner": "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
    "benefit_router": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
    "post_safety": "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
}
COMPONENT_SHAS = {
    "global_medfilm": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
    "regional_refiner": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
    "benefit_router": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
    "post_safety": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
}
COMPONENT_MODEL_CLASSES = {
    "global_medfilm": "GlobalMedFiLM",
    "regional_refiner": "BARRRegionalRefinerV1",
    "benefit_router": "BARRBenefitRouterV1",
    "post_safety": "BARRPostSafetyV1",
}
COMPONENT_PARAM_COUNTS = {
    "global_medfilm": 3523001,
    "regional_refiner": 1276401,
    "benefit_router": 36801,
    "post_safety": 1217,
}
NORMALIZATION_PATHS = {
    "router_normalization": "reports/tables/phase25d_final_normalization_stats.csv",
    "post_safety_normalization": "reports/tables/phase25f_final_normalization_stats.csv",
}
NORMALIZATION_SHAS = {
    "router_normalization": "ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb",
    "post_safety_normalization": "e112e18b134c6edcdcd0c254c362d0a954a75faffe634cc37a2a17e4fe6f4e7b",
}
SCHEMA_PATHS = {
    "router_schema": "reports/tables/phase25b_feature_schema.csv",
    "post_safety_schema": "reports/tables/phase25f_feature_schema_v1_0.csv",
}
SCHEMA_SHAS = {
    "router_schema": "da76aa34f14006146f46ca799f173378274d8c9d0792dc18edb30711a2486dd4",
    "post_safety_schema": "3e70e20c541b93de752980c34cdfb6fe5af17ebe4c18cbb64397c0bbae465ee5",
}

# ------------------------------------------------------------------ VAL808 population
VAL808_MANIFEST = "manifests/phase4_v3/val.csv"
VAL808_MANIFEST_SHA = "082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315"
VAL808_N = 808
DOMAIN_EXPECTED_N = {"ISIC": 357, "KUB": 280, "KVASIR": 87, "BUSI": 84}
DOMAIN_TASK_ID = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}
DOMAIN_EXPECTED_GROUPS = {"ISIC": 357, "BUSI": 84, "KVASIR": 87, "KUB": 111}
VAL808_TOTAL_GROUPS = 639
VAL808_GROUP_IDS_SHA = "5d7db45c324098a14199f1d453541373078ef5748f255021a132558a62e19dd0"

# ------------------------------------------------------------------ numerics (frozen v1.1 CASE A)
DEVICE = "cuda"
CANONICAL_REQUIRES_CUDA = True
AUTOCAST_ENABLED = True
AUTOCAST_DTYPE = "float16"
BATCH_SIZE = 8
PROB_OUTPUT_DTYPE = "float32"
PROB_STORAGE_DTYPE = "float16"
SEED = 42

# ------------------------------------------------------------------ thresholds (three distinct)
ROI_PROPOSAL_THRESHOLD = 0.30
SOMEGA_ACCEPT_THRESHOLD = 0.50
SEGMENTATION_OUTPUT_THRESHOLD = 0.50
ROI_EXPANSION = 1.50

# ------------------------------------------------------------------ runtime policy (frozen)
RUNTIME_SCORE = "delta_hat_final - 0.25*C"
TAU_C8_FINAL_EXACT = "-5003565381643716252018011/205414980000000000000000000"

# ------------------------------------------------------------------ preservation contract (frozen)
NONINFERIORITY_MARGIN = 0.005
NONINFERIORITY_CRITERION = "lower 95% CI bound > -0.005 (strict)"
N_BOOT = 2000
BOOTSTRAP_SEED = 42
CI_PERCENTILES = [2.5, 97.5]
DICE_TOLERANCE = 1e-12

# ------------------------------------------------------------------ planned artifact paths (Phase A)
PREDICTIONS_CSV = "reports/tables/phase27_val808_predictions.csv"
PREDICTIONS_CSV_SHA_SIDECAR = "reports/audits/phase27_val808_predictions_sha256.json"
MASK_DIR = "reports/figures/phase27_preservation/masks"

# ------------------------------------------------------------------ evidence class
EVIDENCE_CLASS = "CONTINUITY_DEVELOPMENT_EVIDENCE"

# ------------------------------------------------------------------ terminals
TERMINAL_SUCCESS = (
    "PHASE27_MULTIDOMAIN_PRESERVATION_AUDIT_COMPLETE__VAL808_CONTINUITY_RESULT_FROZEN__"
    "PHASE28_ELIGIBLE_NOT_STARTED"
)
TERMINAL_BLOCKED_BINARY_SEMANTICS = (
    "PHASE27_BLOCKED__BINARY_PREDICTION_PERSISTENCE_SEMANTICS_UNRESOLVED"
)
TERMINAL_BUNDLE_DRIFT = "PHASE27_BLOCKED__PHASE26_BUNDLE_DRIFT"
TERMINAL_ENTRY_FAILURE = "PHASE27_EXECUTION_BLOCKED__ENTRY_GATE_FAILURE"
TERMINAL_NUMERIC_MODE_FAILURE = "PHASE27_EXECUTION_BLOCKED__NUMERIC_MODE_UNDEFINED"
TERMINAL_VAL808_BINDING_FAILURE = "PHASE27_EXECUTION_BLOCKED__VAL808_BINDING_FAILURE"

# ------------------------------------------------------------------ helpers


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def write_json(p, o):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(o, indent=1) + "\n", encoding="utf-8")


def write_csv(p, rows, fields):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fields})


def bind(rel_path, expected_sha=None):
    p = ROOT / rel_path
    exists = p.exists()
    actual = sha256_file(p) if exists else None
    return {
        "path": rel_path,
        "exists": bool(exists),
        "sha256": actual,
        "expected_sha256": expected_sha,
        "match": bool(exists and (expected_sha is None or actual == expected_sha)),
    }


def canonical_val808_order():
    """VAL808 rows in the frozen canonical order: sort by (dataset, sample_id)."""
    rows = S.val808_rows()
    return sorted(rows, key=lambda r: (r["dataset"], str(r["sample_id"])))


def domain_order():
    return sorted(set(r["dataset"] for r in S.val808_rows()))


def expected_batch_counts():
    """§6: contiguous chunks of 8 inside a single domain -> batch counts."""
    counts = {}
    total = 0
    for dom in domain_order():
        n = DOMAIN_EXPECTED_N[dom]
        k = (n + BATCH_SIZE - 1) // BATCH_SIZE
        counts[dom] = {"n": n, "batches": k}
        total += k
    return counts, total
