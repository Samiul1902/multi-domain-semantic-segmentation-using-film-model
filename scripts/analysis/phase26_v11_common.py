"""Phase26 v1.1 - CANONICAL ROUTER SCORE / THRESHOLD SEMANTICS RECONCILIATION.

RA-MedFiLM-BARR.  Governance / specification ONLY.

NO MODEL FORWARD.  NO TRAINING.  NO POLICY RETUNING.  NO HOLDOUT.  NO VAL808.  NO TEST.

Only frozen score-cache arithmetic is permitted here.
"""
from __future__ import annotations

import csv
import hashlib
import json
from fractions import Fraction
from pathlib import Path

# --------------------------------------------------------------------------- paths
ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
TABLE = ROOT / "reports" / "tables"

METHOD = "RA-MedFiLM-BARR"
REVISION_V10 = "ra_medfilm_barr_phase26_integration_v1_0"
REVISION_V11 = "ra_medfilm_barr_phase26_router_threshold_reconciliation_v1_1"
CLASSIFICATION = "PHASE26_ROUTER_SCORE_THRESHOLD_SEMANTICS_RECONCILIATION"

PREDECESSOR_TERMINAL = (
    "PHASE26_SPEC_V1_0_COMPLETE__MODULAR_INTEGRATION_NO_RETRAINING_AND_"
    "CANONICAL_25PCT_A8_POLICY_FROZEN__PHASE26_EXECUTION_ELIGIBLE_NOT_STARTED"
)

# ---------------------------------------------------------------- frozen constants
CANONICAL_VARIANT = "A8_C9"
CANONICAL_BUDGET = 0.25
CANONICAL_LAMBDA = Fraction(1, 4)
EXPECTED_DEV_SELECTED_COUNT = 1239

N_ROUTER_DEVELOPMENT = 4957
N_ELIGIBLE = 4957

# action-cost (normalized) - Phase25E cost binding audit
C_ACTION_EXACT = Fraction(1051648, 10270749)
# lambda*C exact
LAMBDA_C_EXACT = CANONICAL_LAMBDA * C_ACTION_EXACT          # 262912/10270749

# ---------------------------------------------------------------- threshold spaces
# Space A: canonical policy / OOF space.  s_C7 = delta_hat_oof ; s_C8 = delta_hat_oof - lambda*C
#   This is the space of the FROZEN canonical 25%-budget membership
#   (policy membership CSVs + Phase25F C9 manifest), and it is the space named by the
#   frozen Phase25E comparator-direction contract:  C7 score = "delta_hat_oof".
TAU_C7_POLICY_SPACE = Fraction(29487973, 10000000000)        # from membership manifest, C7_budget0.25
TAU_C8_POLICY_SPACE = TAU_C7_POLICY_SPACE - LAMBDA_C_EXACT   # -2326256430798223/102707490000000000

# Space B: final-router DEV calibration space.  s = delta_hat_final_dev
#   This is the space of the Phase25E closure *dev-calibration* artifact, used to derive a
#   scalar tau for future-cohort deployment.  It is NOT the space of the frozen membership.
TAU_C7_DEV_SPACE = Fraction(24796109646558761, 20000000000000000000)
TAU_C8_DEV_SPACE = TAU_C7_DEV_SPACE - LAMBDA_C_EXACT

# work-order declared reported threshold (this is the DEV-space tau)
WORK_ORDER_REPORTED_TAU_C7 = Fraction(24796109646558761, 20000000000000000000)
WORK_ORDER_EXPECTED_TAU_C8_APPROX = -0.024358327624

# membership SHA of the frozen canonical 25% membership (sorted ids, newline-joined + trailing NL)
FROZEN_MEMBERSHIP_IDS_SHA256 = (
    "e71e368cbb95b8d3398b47427df243bb8b387dd6d442ccf038188446677f446f"
)

TERMINAL_SUCCESS = (
    "PHASE26_SPEC_V1_1_COMPLETE__C8_RESOURCE_UTILITY_THRESHOLD_ALGEBRAICALLY_BOUND__"
    "25PCT_MEMBERSHIP_EXACTLY_REPRODUCED__PHASE26_EXECUTION_ELIGIBLE_NOT_STARTED"
)
TERMINAL_BLOCKED_MEMBERSHIP = "PHASE26_SPEC_REPAIR_BLOCKED__ROUTER_THRESHOLD_MEMBERSHIP_MISMATCH"
TERMINAL_BLOCKED_PROVENANCE = "PHASE26_SPEC_REPAIR_BLOCKED__RAW_GAIN_THRESHOLD_PROVENANCE_UNRESOLVED"
TERMINAL_BLOCKED_AMBIGUOUS = "PHASE26_SPEC_REPAIR_BLOCKED__ROUTER_SCORE_THRESHOLD_SPACE_AMBIGUOUS"

# ---------------------------------------------------------------- predecessor SHAs
PREDECESSOR_V10_BINDINGS = {
    "reports/audits/phase26_spec_repair_terminal.json":
        "a86026e3bf9c0cb9dd83b31588634a0f96ba2b34d92f008fcefc51f79fb7f77c",
    "reports/audits/phase26_specification_final_check_v1_0.json":
        "50817c690f0212b0f3e4384590ab0c47b3d902a67ad3964eb30b223702510b22",
    "reports/audits/phase26_inference_state_machine_v1_0.json":
        "56f32c4b092c9957afe679468a549530a7affaa3cf4076b44a98637eea71167d",
    "reports/audits/phase26_checkpoint_bundle_contract_v1_0.json":
        "fe33a92f841027b293ad75c35c849aa6d6df11d3ce219c547877ee00f2829004",
    "reports/audits/phase26_canonical_router_threshold_binding_v1_0.json":
        "c49a1e53fd3e85ff793cc4ce41fd3f20210f33e6b1880ea0f55bd2b788fbbb37",
    "reports/tables/phase26_specification_completeness_v1_0.csv":
        "22b9e4a7ac38625d4ef53f3f088f4cccc8fc483ea582e265a923de1c876be834",
}

# The machine-readable spec doc is the AUTHORIZED TARGET of the additive §11 update.
# Its v1.0 SHA is recorded as provenance; the additive append is authorized by the
# work order (§11 "Update additively"), so a change here is NOT drift.
SPEC_DOC_V10_SHA = "283f156b58f36bff1a96c91d68036cf08d676c882b7449879410f4cb4d3651c5"

# Phase25E source SHAs, frozen at reconciliation time.
PHASE25E_SOURCE_SHAS = {
    "reports/audits/phase25e_comparator_direction_contract_v1_0.json":
        "7652e7bdf65722c0877e17f35e565f0ee809aaff8c99448928372a71f58e2beb",
    "reports/audits/phase25e_cost_binding_audit.json":
        "c79e8f74cefeea36cdc9310da60468bd5f3c74cf936d1a409c9bd1c0645946cc",
    "reports/audits/phase25e_lambda_grid_contract_v1_0.json":
        "ffefe0db74725c2436d8e651b770949183640db5ad718bd32cf35fab55a613b2",
    "reports/audits/phase25e_tie_break_contract_v1_0.json":
        "9bb910f0439329ebf8988860fe4909cb34d541d43170fde63ccd1ee57e78bfdf",
    "reports/audits/phase25e_fixed_budget_contract_v1_0.json":
        "c8ade16f835617c23aa6c363e2f27ac4a7d175d9e2dd6dc8544d962976050ff8",
    "reports/audits/phase25e_final_router_dev_calibration.json":
        "9696f5d665913bcecf1f2343bfc4b7a9e2b81815117e4d151ad319643306f0e5",
    "reports/tables/phase25e_final_router_dev_thresholds.csv":
        "980e44aba6bb57bc86b2fa03060eaa181207297367fe7f7b1bbbde9c9b3bcfd1",
    "data_cache/phase25e_barr_resource_gate_v1_0/phase25e_final_router_dev_scores.csv":
        "2d23e11090a5b3164d5b125c633bbccfbe307ecdc717d0f5689bf401bd849f9d",
    "reports/tables/phase25e_policy_membership_manifest.csv":
        "f4ff4b235c664339d237fd7ec51f948dbc233431a6fd45522bde2166327e679a",
    "reports/tables/phase25e_policy_memberships_v1_0/C7_budget0.25.csv":
        "a3b4b2b365366c9cb2da4b734b51b48095b0d65421b52684fa9d0f5fae93c390",
    "reports/tables/phase25e_policy_memberships_v1_0/C8_lambda0.25_budget0.25.csv":
        "4c411d589866434b824245d3c940bc09873f3cbc096ddc8a44776cd56273393b",
    "data_cache/phase25d_barr_benefit_router_v1_2_1/phase25d_oof_router_predictions.csv":
        "837be08e569053676b71d1ab216ff604184b2b61df567cca45e6f8a5546d4441",
    "reports/tables/phase25f_c9_decision_manifest.csv":
        "cde91c474bf19bb36368357ce4b38dd1cc7dad1b37d900fcec7cde6b9e72dbd1",
    "reports/audits/phase25e_final_freeze.json":
        "e20581efab5bb81ec63d118923558df82089b2509f7d5a964da42db4252bab4e",
    "reports/audits/phase25e_cost_variability_and_policy_redundancy_audit.json":
        "72546015f08163e0b0269e08f47edcea86519cdf4a246b88da0a7f0d761949c2",
}

# Phase25E source artifacts used for binding (existence checked at runtime; SHAs recorded)
PHASE25E_SOURCES = {
    "comparator_direction": "reports/audits/phase25e_comparator_direction_contract_v1_0.json",
    "cost_binding": "reports/audits/phase25e_cost_binding_audit.json",
    "lambda_grid": "reports/audits/phase25e_lambda_grid_contract_v1_0.json",
    "tie_break": "reports/audits/phase25e_tie_break_contract_v1_0.json",
    "fixed_budget": "reports/audits/phase25e_fixed_budget_contract_v1_0.json",
    "dev_calibration": "reports/audits/phase25e_final_router_dev_calibration.json",
    "dev_thresholds": "reports/tables/phase25e_final_router_dev_thresholds.csv",
    "dev_scores_cache": "data_cache/phase25e_barr_resource_gate_v1_0/phase25e_final_router_dev_scores.csv",
    "membership_manifest": "reports/tables/phase25e_policy_membership_manifest.csv",
    "c7_membership": "reports/tables/phase25e_policy_memberships_v1_0/C7_budget0.25.csv",
    "c8_membership": "reports/tables/phase25e_policy_memberships_v1_0/C8_lambda0.25_budget0.25.csv",
    "oof_predictions": "data_cache/phase25d_barr_benefit_router_v1_2_1/phase25d_oof_router_predictions.csv",
    "c9_manifest": "reports/tables/phase25f_c9_decision_manifest.csv",
    "phase25e_final_freeze": "reports/audits/phase25e_final_freeze.json",
    "cost_variability": "reports/audits/phase25e_cost_variability_and_policy_redundancy_audit.json",
}


# --------------------------------------------------------------------------- io
def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def jload(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")


def write_csv(path, rows, fields):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fields})


def exact(value) -> str:
    """Render an exact rational / numeric as a canonical string."""
    if isinstance(value, Fraction):
        return f"{value.numerator}/{value.denominator}"
    return str(value)


def frac_from_str(s) -> Fraction:
    return Fraction(s)


def membership_ids_sha(ids) -> str:
    """Sorted-id newline-join digest, matching the Phase25E manifest convention."""
    joined = "\n".join(sorted(ids)) + "\n"
    return sha256_bytes(joined.encode("utf-8"))


def read_csv_rows(path):
    p = ROOT / path if not Path(path).is_absolute() else Path(path)
    with p.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))
