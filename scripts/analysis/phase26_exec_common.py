"""Phase26 canonical integration execution - shared constants and helpers.

CANONICAL_FULL_SYSTEM_INTEGRATION_AND_CONFIGURATION_FREEZE
Operational meaning: ASSEMBLY_ONLY__NO_PARAMETER_OPTIMIZATION

NO training / fine-tuning / backward / optimizer / scientific-data inference /
threshold recalibration / policy reselection / ROUTER_HOLDOUT / VAL808 / TEST.

Spec authority: ra_medfilm_barr_phase26_integration_v1_0 + router deployment
semantics v1.2.
"""
from __future__ import annotations

import csv
import hashlib
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
TABLE = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures" / "phase26_integration"
BUNDLE = ROOT / "artifacts" / "phase26_ra_medfilm_barr_bundle_v1_0"

METHOD = "RA-MedFiLM-BARR"
BUNDLE_REVISION = "ra_medfilm_barr_bundle_v1_0"
PHASE26_REVISION = "ra_medfilm_barr_phase26_integration_v1_0"
ROUTER_SEMANTICS_REVISION = "phase26_v1_2"
CLASSIFICATION = "CANONICAL_FULL_SYSTEM_INTEGRATION_AND_CONFIGURATION_FREEZE"

# ------------------------------------------------------------------ predecessor
PREDECESSOR_TERMINAL = (
    "PHASE26_SPEC_V1_2_COMPLETE__OOF_SCIENTIFIC_AND_FINAL_ROUTER_RUNTIME_CALIBRATIONS_SEPARATED__"
    "FINAL_BPHI_25PCT_THRESHOLD_FROZEN__PHASE26_EXECUTION_ELIGIBLE_NOT_STARTED"
)

# ------------------------------------------------------------------ canonical op point
CANONICAL_VARIANT = "A8_C9"
NOMINAL_BUDGET = 0.25
CANONICAL_LAMBDA = Fraction(1, 4)
LAMBDA_ROLE = "MEMBERSHIP_EQUIVALENT_SERIALIZATION_REPRESENTATIVE"
LAMBDA_PERFORMANCE_SELECTED = False
SELECTION_TIME = "POST_PHASE25_DEVELOPMENT__PRE_PHASE30_HOLDOUT"

C_ACTION = Fraction(1051648, 10270749)                 # normalized action cost
LAMBDA_C = CANONICAL_LAMBDA * C_ACTION                 # 262912/10270749

# runtime (Space A) - FINAL router DEV calibration
TAU_C7_FINAL = Fraction(24796109646558761, 20000000000000000000)
TAU_C8_FINAL = TAU_C7_FINAL - LAMBDA_C
# scientific OOF (Space B) - evidence only
TAU_C7_OOF = Fraction(29487973, 10000000000)
TAU_C8_OOF = TAU_C7_OOF - LAMBDA_C

OOF_SELECTED_COUNT = 1239
OOF_MEMBERSHIP_SHA = "e71e368cbb95b8d3398b47427df243bb8b387dd6d442ccf038188446677f446f"
FINAL_DEV_CUTOFF_K = "e0301756008d8e0a184c2c9296f969ab"
FINAL_DEV_CUTOFF_K1 = "c3145e7864db95b7aeda72129a67cf44"
FINAL_ROUTER_SELECTED_COUNT = 1239
FINAL_ROUTER_MEMBERSHIP_SHA = "10de16dec21e6750c8e9451af96bed0ca3f2686bbf0d6084a6300cf0d4adbbe5"

# three DISTINCT thresholds (never conflated)
ROI_PROPOSAL_THRESHOLD = 0.30
SOMEGA_ACCEPT_THRESHOLD = 0.50
SEGMENTATION_OUTPUT_THRESHOLD = 0.50

ROI_EXPANSION = 1.50
ROI_FRACTIONAL_MARGIN = 0.25

# ------------------------------------------------------------------ component identities
GLOBAL_CHECKPOINT = "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"
GLOBAL_SHA = "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"

REFINER_CHECKPOINT = "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt"
REFINER_SHA = "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109"

ROUTER_CHECKPOINT = "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt"
ROUTER_SHA = "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b"

SOMEGA_CHECKPOINT = "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt"
SOMEGA_SHA = "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e"

ROUTER_NORMALIZATION = "reports/tables/phase25d_final_normalization_stats.csv"
ROUTER_NORMALIZATION_SHA = "ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb"

SOMEGA_NORMALIZATION_PATH = "reports/audits/phase25f_final_normalization.json"
SOMEGA_STATS_CSV = "reports/tables/phase25f_final_normalization_stats.csv"

ROUTER_SCHEMA = "reports/tables/phase25b_feature_schema.csv"
ROUTER_SCHEMA_SHA = "da76aa34f14006146f46ca799f173378274d8c9d0792dc18edb30711a2486dd4"
SOMEGA_SCHEMA = "reports/tables/phase25f_feature_schema_v1_0.csv"

ROI_GEOMETRY_CONTRACT = "reports/audits/phase24_roi_feature_mapping_contract_v1_2.json"
FUSION_FALLBACK_CONTRACT = "reports/audits/phase25f_fusion_fallback_contract_audit.json"
ROI_TRANSFORM_AUDIT = "reports/audits/phase25a_roi_transform_audit.json"

SPEC_DOC = "docs/phase26_training_spec.md"
V11_TERMINAL = "reports/audits/phase26_router_threshold_reconciliation_terminal_v1_1.json"
V12_TERMINAL = "reports/audits/phase26_router_deployment_semantics_terminal_v1_2.json"

# ------------------------------------------------------------------ data caches
FINAL_DEV_SCORES = "data_cache/phase25e_barr_resource_gate_v1_0/phase25e_final_router_dev_scores.csv"
OOF_PREDICTIONS = "data_cache/phase25d_barr_benefit_router_v1_2_1/phase25d_oof_router_predictions.csv"
C9_MANIFEST = "reports/tables/phase25f_c9_decision_manifest.csv"
PRE_REFINEMENT_FEATURES = "data_cache/phase25b_barr_pre_refinement_features_v1_2/features.npy"

# ------------------------------------------------------------------ resource (analytical MACs)
MACS_GLOBAL = 31551740928
MACS_ROUTER = 36160
MACS_REFINER = 3230662656
MACS_SOMEGA = 1168
MAC_LABEL = "ANALYTICAL MAC LOWER BOUND"

# ------------------------------------------------------------------ locks
HOLDOUT_OWNER = "PHASE30"
HOLDOUT_STATE = "RESERVED_UNOPENED_FOR_PHASE30"
VAL808 = "UNOPENED"
TEST = "LOCKED_UNTIL_PHASE39"

# ------------------------------------------------------------------ terminals
TERMINAL_SUCCESS = (
    "PHASE26_CANONICAL_INTEGRATION_COMPLETE__A8_C9_25PCT_FINAL_ROUTER_RUNTIME_POLICY_AND_BUNDLE_"
    "FROZEN__PHASE27_ELIGIBLE_NOT_STARTED"
)
TERMINAL_DRIFT = "PHASE26_BLOCKED__PREDECESSOR_ARTIFACT_DRIFT"
TERMINAL_LOAD = "PHASE26_BLOCKED__CANONICAL_COMPONENT_LOAD_FAILURE"
TERMINAL_STATE = "PHASE26_BLOCKED__INTEGRATION_STATE_MACHINE_FAILURE"
TERMINAL_THRESHOLD = "PHASE26_BLOCKED__FINAL_ROUTER_RUNTIME_THRESHOLD_FAILURE"
TERMINAL_BUNDLE = "PHASE26_BLOCKED__CANONICAL_BUNDLE_INTEGRITY_FAILURE"
TERMINAL_NOTEBOOK = "PHASE26_BLOCKED__REVIEWER_NOTEBOOK_INCOMPLETE"

RUN_LOG = {"model_forwards": 0, "synthetic_forwards": 0, "scientific_forwards": 0,
           "backward_passes": 0, "optimizer_steps": 0, "training_runs": 0}


# --------------------------------------------------------------------------- io
def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


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


def write_text_deterministic(p, s: str):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")


def rows_of(p):
    with open(ROOT / p, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def exact(x):
    return f"{x.numerator}/{x.denominator}" if isinstance(x, Fraction) else str(x)


def ids_sha(ids):
    return sha256_bytes(("\n".join(sorted(ids)) + "\n").encode("utf-8"))


def bind(rel_path, expected_sha=None):
    p = ROOT / rel_path
    exists = p.exists()
    actual = sha256_file(p) if exists else None
    return {
        "path": rel_path,
        "exists": bool(exists),
        "sha256": actual,
        "expected_sha256": expected_sha,
        "match": (expected_sha is None and exists) or (actual == expected_sha),
    }
