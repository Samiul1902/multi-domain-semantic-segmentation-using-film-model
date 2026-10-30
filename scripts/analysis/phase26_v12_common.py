"""Phase26 v1.2 - ROUTER DEPLOYMENT-SEMANTICS RECONCILIATION.

Separates the OOF scientific policy space (Space B, immutable evidence) from the
final-router DEV calibration space (Space A, canonical runtime authority).

Governance / specification ONLY.  Frozen score-cache arithmetic only.
NO model forward / training / retuning / reselection / HOLDOUT / VAL808 / TEST.
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

METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase26_deployment_semantics_v1_2"
CLASSIFICATION = "ROUTER_CALIBRATION_ROLE_RECONCILIATION"

PREDECESSOR_TERMINAL = (
    "PHASE26_SPEC_V1_1_COMPLETE__C8_RESOURCE_UTILITY_THRESHOLD_ALGEBRAICALLY_BOUND__"
    "25PCT_MEMBERSHIP_EXACTLY_REPRODUCED__PHASE26_EXECUTION_ELIGIBLE_NOT_STARTED"
)

# ---------------------------------------------------------------- frozen constants
CANONICAL_VARIANT = "A8_C9"
CANONICAL_BUDGET = 0.25
CANONICAL_LAMBDA = Fraction(1, 4)
C_ACTION = Fraction(1051648, 10270749)
LAMBDA_C = CANONICAL_LAMBDA * C_ACTION               # 262912/10270749

# Space A - final-router DEV calibration (CANONICAL RUNTIME)
TAU_C7_FINAL = Fraction(24796109646558761, 20000000000000000000)
TAU_C8_FINAL = TAU_C7_FINAL - LAMBDA_C               # -5003565381643716252018011/205414980000000000000000000

# Space B - scientific OOF policy (evidence only, immutable)
TAU_C7_OOF = Fraction(29487973, 10000000000)
TAU_C8_OOF = TAU_C7_OOF - LAMBDA_C                   # -2326256430798223/102707490000000000

FINAL_DEV_CUTOFF_K = "e0301756008d8e0a184c2c9296f969ab"
FINAL_DEV_CUTOFF_K1 = "c3145e7864db95b7aeda72129a67cf44"
OOF_MEMBERSHIP_SHA = "e71e368cbb95b8d3398b47427df243bb8b387dd6d442ccf038188446677f446f"

EXPECTED_COUNT = 1239
EXPECTED_INTERSECTION = 1086

TERMINAL_SUCCESS = (
    "PHASE26_SPEC_V1_2_COMPLETE__OOF_SCIENTIFIC_AND_FINAL_ROUTER_RUNTIME_CALIBRATIONS_SEPARATED__"
    "FINAL_BPHI_25PCT_THRESHOLD_FROZEN__PHASE26_EXECUTION_ELIGIBLE_NOT_STARTED"
)
TERMINAL_BLOCKED_PROVENANCE = "PHASE26_V1_2_BLOCKED__FINAL_ROUTER_CALIBRATION_PROVENANCE_UNRESOLVED"
TERMINAL_BLOCKED_REPLAY = "PHASE26_V1_2_BLOCKED__FINAL_ROUTER_CALIBRATION_REPLAY_FAILURE"
TERMINAL_BLOCKED_AMBIGUOUS = "PHASE26_V1_2_BLOCKED__OOF_RUNTIME_SCORE_ROLE_AMBIGUOUS"

# ---------------------------------------------------------------- predecessor SHAs
V11_BINDINGS = {
    "reports/audits/phase26_router_threshold_reconciliation_terminal_v1_1.json":
        "c2904384086bbd17a925041df361c127730d501004cae9c02517e47ce7cd8059",
    "reports/audits/phase26_router_threshold_reconciliation_v1_1.json":
        "a775f9959a26ea2f009fab877013377c4afc5932fd2e4c5d0eee99261120f35d",
    "reports/audits/phase26_router_threshold_exact_transform.json":
        "9fd4d88f75fd18079b8c051845b059115de98d04a7466c1480c4e7bf9562198c",
    "reports/audits/phase26_router_threshold_membership_equivalence.json":
        "1a571f3d68e3a127ed9ee6e170366b0bceb7633cc2701644802e035271f87e83",
    "reports/audits/phase26_specification_final_check_v1_1.json":
        "ff622dd81de61420bc5885016f037edfe6e933b6b0ee4477b0be1e68c908ba8a",
    "reports/tables/phase26_specification_completeness_v1_1.csv":
        "c76ed77e8fe307fd21eb90b92f98cf6baf46b38421b5e89bcd82fd1944e4d087",
}

# Phase25E sources used for the v1.2 binding (SHA verified at runtime)
P25E_SOURCES = {
    "final_router_contract":
        "reports/audits/phase25e_final_router_threshold_calibration_contract_v1_0.json",
    "dev_scores": "data_cache/phase25e_barr_resource_gate_v1_0/phase25e_final_router_dev_scores.csv",
    "dev_thresholds": "reports/tables/phase25e_final_router_dev_thresholds.csv",
    "dev_calibration_audit": "reports/audits/phase25e_final_router_dev_calibration.json",
    "cost_binding": "reports/audits/phase25e_cost_binding_audit.json",
    "cost_variability":
        "reports/audits/phase25e_cost_variability_and_policy_redundancy_audit.json",
    "lambda_grid": "reports/audits/phase25e_lambda_grid_contract_v1_0.json",
    "comparator_direction": "reports/audits/phase25e_comparator_direction_contract_v1_0.json",
    "oof_predictions":
        "data_cache/phase25d_barr_benefit_router_v1_2_1/phase25d_oof_router_predictions.csv",
    "membership_manifest": "reports/tables/phase25e_policy_membership_manifest.csv",
    "c9_manifest": "reports/tables/phase25f_c9_decision_manifest.csv",
}

# expected SHAs (verified while building v1.1)
P25E_SHAS = {
    "reports/audits/phase25e_final_router_threshold_calibration_contract_v1_0.json":
        "8b2cb0a220241db0aeb4795af9ae31af651e1a88dc7437b2e4afbcd5d249510f",
    "data_cache/phase25e_barr_resource_gate_v1_0/phase25e_final_router_dev_scores.csv":
        "2d23e11090a5b3164d5b125c633bbccfbe307ecdc717d0f5689bf401bd849f9d",
    "reports/tables/phase25e_final_router_dev_thresholds.csv":
        "980e44aba6bb57bc86b2fa03060eaa181207297367fe7f7b1bbbde9c9b3bcfd1",
    "reports/audits/phase25e_final_router_dev_calibration.json":
        "9696f5d665913bcecf1f2343bfc4b7a9e2b81815117e4d151ad319643306f0e5",
    "reports/audits/phase25e_cost_binding_audit.json":
        "c79e8f74cefeea36cdc9310da60468bd5f3c74cf936d1a409c9bd1c0645946cc",
    "reports/audits/phase25e_cost_variability_and_policy_redundancy_audit.json":
        "72546015f08163e0b0269e08f47edcea86519cdf4a246b88da0a7f0d761949c2",
    "reports/audits/phase25e_lambda_grid_contract_v1_0.json":
        "ffefe0db74725c2436d8e651b770949183640db5ad718bd32cf35fab55a613b2",
    "reports/audits/phase25e_comparator_direction_contract_v1_0.json":
        "7652e7bdf65722c0877e17f35e565f0ee809aaff8c99448928372a71f58e2beb",
    "data_cache/phase25d_barr_benefit_router_v1_2_1/phase25d_oof_router_predictions.csv":
        "837be08e569053676b71d1ab216ff604184b2b61df567cca45e6f8a5546d4441",
    "reports/tables/phase25e_policy_membership_manifest.csv":
        "f4ff4b235c664339d237fd7ec51f948dbc233431a6fd45522bde2166327e679a",
    "reports/tables/phase25f_c9_decision_manifest.csv":
        "cde91c474bf19bb36368357ce4b38dd1cc7dad1b37d900fcec7cde6b9e72dbd1",
}

FINAL_ROUTER_CHECKPOINT_SHA = "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b"
FINAL_NORMALIZATION_SHA = "ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb"

SPEC_MARKER = "<!-- PHASE26_DEPLOYMENT_SEMANTICS_V1_2 -->"


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


def rows_of(p):
    with open(ROOT / p, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def exact(x):
    return f"{x.numerator}/{x.denominator}" if isinstance(x, Fraction) else str(x)


def ids_sha(ids):
    return sha256_bytes(("\n".join(sorted(ids)) + "\n").encode("utf-8"))
