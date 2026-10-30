"""Phase27 multi-domain performance preservation audit - specification-only
shared constants and helpers.

CLASSIFICATION: PHASE27_PRE_EXECUTION_PRESERVATION_AUDIT_SPECIFICATION
Operational meaning: GOVERNANCE_SPECIFICATION_ONLY__NO_INFERENCE

NO VAL808 scientific inference / NO ROUTER_HOLDOUT / NO TEST / NO training /
NO fine-tuning / NO recalibration / NO policy selection / NO threshold change /
NO model construction.

Supervisor ruling: Phase27 owns VAL808 as the
SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK.  Phase30 retains exclusive
ROUTER_HOLDOUT ownership.

Spec authority: ra_medfilm_barr_preservation_v1_0
Predecessor: ra_medfilm_barr_phase26_integration_v1_0 (Phase26 COMPLETE_CANONICAL).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
TABLE = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures" / "phase27_preservation"
CACHE27 = ROOT / "data_cache" / "phase27_barr_preservation_v1_0"

METHOD = "RA-MedFiLM-BARR"
PHASE27_REVISION = "ra_medfilm_barr_preservation_v1_0"
PREDECESSOR_REVISION = "ra_medfilm_barr_phase26_integration_v1_0"
CLASSIFICATION = "PHASE27_PRE_EXECUTION_PRESERVATION_AUDIT_SPECIFICATION"
OPERATIONAL_MEANING = "GOVERNANCE_SPECIFICATION_ONLY__NO_INFERENCE"
PHASE27_TITLE = "Multi-Domain Performance Preservation Audit"

# ------------------------------------------------------------------ predecessor binding
PREDECESSOR_TERMINAL = (
    "PHASE26_CANONICAL_INTEGRATION_COMPLETE__A8_C9_25PCT_FINAL_ROUTER_RUNTIME_POLICY_AND_"
    "BUNDLE_FROZEN__PHASE27_ELIGIBLE_NOT_STARTED"
)
PREDECESSOR_TERMINAL_PATH = "reports/audits/phase26_canonical_integration_terminal.json"

BUNDLE_MANIFEST = "artifacts/phase26_ra_medfilm_barr_bundle_v1_0/canonical_bundle_manifest.json"
BUNDLE_MANIFEST_SHA = "f7aebb0f646bcc8de49fa91b70a4c4cc1051c9998ab6b055a8d4d187809cb3d9"

WRAPPER_PATH = "src/models/barr/ra_medfilm_barr.py"
WRAPPER_SHA = "342f2163690c2fa8d5a601ab1d18178b982d701b916935c33e0793b0801c3724"

NOTEBOOK26_PATH = (
    "notebooks/phasewise/phase_26_full_system_integration/"
    "phase26_canonical_integration_and_bundle_freeze.ipynb"
)
NOTEBOOK26_SHA = "57552c16b5a444f1b2404077eeac0004d37fd198355d679a66eb5c24ea15b4e0"

FREEZE26_PATH = "reports/audits/phase26_final_freeze.json"
# FYI (informational only - bound by content, never asserted against a hardcoded
# digest, because the freeze document is the authority Phase27 inherits from):
FREEZE26_SHA_INFO = "reports/audits/phase26_final_freeze.json"

# ------------------------------------------------------------------ canonical op point (frozen)
CANONICAL_VARIANT = "A8_C9"
NOMINAL_BUDGET = 0.25
CANONICAL_LAMBDA = Fraction(1, 4)
C_ACTION = Fraction(1051648, 10270749)
LAMBDA_C = CANONICAL_LAMBDA * C_ACTION
RUNTIME_THRESHOLD_EXACT = "-5003565381643716252018011/205414980000000000000000000"
RUNTIME_SCORE = "delta_hat_final - 0.25*C"
RUNTIME_DECISION = "EXECUTE iff utility >= -5003565381643716252018011/205414980000000000000000000"

# component identity (inherited from Phase26 bundle, never re-derived)
COMPONENT_CHECKPOINT_PATHS = {
    "global_medfilm": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
    "regional_refiner": "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
    "benefit_router": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
    "post_safety": "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
}
COMPONENT_CHECKPOINT_SHAS = {
    "global_medfilm": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
    "regional_refiner": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
    "benefit_router": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
    "post_safety": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
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

# ------------------------------------------------------------------ three distinct thresholds
ROI_PROPOSAL_THRESHOLD = 0.30
SOMEGA_ACCEPT_THRESHOLD = 0.50
SEGMENTATION_OUTPUT_THRESHOLD = 0.50

# ------------------------------------------------------------------ VAL808 population
VAL808_MANIFEST = "manifests/phase4_v3/val.csv"
VAL808_MANIFEST_SHA = "082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315"
VAL808_N = 808
VAL808_ROLE = "SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK"
DOMAINS = ["BUSI", "ISIC", "KUB", "KVASIR"]
DOMAIN_EXPECTED_N = {"ISIC": 357, "KUB": 280, "KVASIR": 87, "BUSI": 84}
DOMAIN_TASK_ID = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}
# group counts under the metadata-only composite rule (KUB patient-level; others singleton)
DOMAIN_EXPECTED_GROUPS = {"ISIC": 357, "BUSI": 84, "KVASIR": 87, "KUB": 111}
VAL808_TOTAL_GROUPS = 639
VAL808_GROUP_SIZE_DIST = {1: 531, 2: 47, 3: 61}
# rounded group-key digest (order-independent names) - computed at spec time
VAL808_GROUP_IDS_SHA = "5d7db45c324098a14199f1d453541373078ef5748f255021a132558a62e19dd0"
TRAIN_GROUP_COUNT_PROOF = 4172  # canonical == metadata-only partition (proven identical)

# ------------------------------------------------------------------ preservation statistics contract
PRESERVATION_ESTIMAND = "MACRO_DOMAIN_EQUAL_WEIGHT_MEAN_DICE_DELTA"
DELTA_DEFINITION = "Delta_i = Dice(final_A8_i, GT) - Dice(global_i, GT)"
NONINFERIORITY_MARGIN = 0.005
NONINFERIORITY_CRITERION = "lower 95% CI bound > -0.005 (strict)"
NONINFERIORITY_CRITERION_PRIOR = "lower 95% CI > -0.005"  # exact prior Phase25G text
POINT_ESTIMATE = "mean over 4 domain-mean deltas (equal domain weight)"
# NOTE: the estimand is "mean of domain means" - a macro-average, NOT a pooled row mean.
BOOTSTRAP_TYPE = "DOMAIN_STRATIFIED_GROUP_BOOTSTRAP"
N_BOOT = 2000
SEED = 42
RNG = "numpy.random.Generator(numpy.random.PCG64(42))"
CI_METHOD = "percentile"
CI_PERCENTILES = [2.5, 97.5]
PER_DOMAIN_REPORTING = "mandatory"
MACRO_MAY_NOT_HIDE_DOMAIN_HARM = True
PAIRED = True
DICE_TOLERANCE = 1e-12

# ------------------------------------------------------------------ group rule
GROUP_RULE = "METADATA_ONLY_COMPOSITE_PATIENT_SINGLETON"
GROUP_RULE_DETAIL = (
    "KUB -> PATIENT::<patient_id>; ISIC/BUSI/KVASIR -> SINGLETON::<dataset>::<sample_id>"
)
GROUP_RULE_PROVENANCE = "reports/audits/phase24_router_split_manifest.csv"
GROUP_RULE_PROVENANCE_SHA_REQUIRED = True
GROUP_RULE_EQUIVALENCE_EVIDENCE = (
    "Metadata-only rule reproduces the canonical Phase24 group_key exactly on all 5832 TRAIN "
    "rows (4172 groups): all 16 RISK:: pHash groups are singletons, so pHash relabelling never "
    "merges rows and cannot affect group counts or bootstrap resampling."
)

# ------------------------------------------------------------------ predecessor read audits
PRIOR_VAL808_READS = 0
PRIOR_HOLDOUT_READS = 0
PRIOR_TEST_READS = 0

# ------------------------------------------------------------------ locks
HOLDOUT_OWNER = "PHASE30"
HOLDOUT_STATE = "RESERVED_UNOPENED_FOR_PHASE30"
HOLDOUT_N = 875
VAL808_STATE = "OWNED_BY_PHASE27__UNOPENED_UNTIL_PHASE27_EXECUTION"
TEST_STATE = "LOCKED_UNTIL_PHASE39"
TEST_N = 1683

# ------------------------------------------------------------------ terminals
TERMINAL_SUCCESS = (
    "PHASE27_PRESERVATION_SPEC_COMPLETE__VAL808_CONTINUITY_BENCHMARK_AND_"
    "NONINFERIORITY_PROTOCOL_FROZEN__PHASE27_EXECUTION_ELIGIBLE_NOT_STARTED"
)
TERMINAL_SPEC_INCOMPLETE = "PHASE27_BLOCKED__PRESERVATION_AUDIT_SPEC_INCOMPLETE"
TERMINAL_POPULATION_FAILURE = "PHASE27_BLOCKED__VAL808_POPULATION_BINDING_FAILURE"
TERMINAL_BUNDLE_DRIFT = "PHASE27_BLOCKED__PHASE26_BUNDLE_DRIFT"
TERMINAL_HOLDOUT_RISK = "PHASE27_BLOCKED__PHASE30_HOLDOUT_CONTAMINATION_RISK"

RUN_LOG = {
    "model_forwards": 0,
    "scientific_forwards": 0,
    "synthetic_forwards": 0,
    "backward_passes": 0,
    "optimizer_steps": 0,
    "training_runs": 0,
    "val808_images_read": 0,
    "val808_masks_read": 0,
    "holdout_reads": 0,
    "test_reads": 0,
}


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
    """Read a CSV as a list of dicts.  Never touches image or mask bytes."""
    with open(ROOT / p, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def rows_of_abs(p):
    with open(p, "r", encoding="utf-8", newline="") as f:
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


def val808_rows():
    """VAL808 manifest metadata rows.  Metadata only - no image/mask access."""
    return rows_of(VAL808_MANIFEST)


def metadata_group_key(row):
    """Composite group key under the metadata-only rule (proven equivalent to
    the canonical Phase24 group_key on every population with recoverable KUB
    patients)."""
    if row["dataset"] == "KUB":
        return "PATIENT::" + row["patient_id"]
    return "SINGLETON::" + row["dataset"] + "::" + row["sample_id"]
