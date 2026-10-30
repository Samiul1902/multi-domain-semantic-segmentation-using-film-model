"""Phase26 common module - RA-MedFiLM-BARR pre-execution training-specification audit.

GOVERNANCE / SPECIFICATION ONLY.
No training.  No fine-tuning.  No model construction.  No forward pass.
No policy selection.  No lambda selection.  No budget selection.
No ROUTER_HOLDOUT.  No VAL808.  No TEST.

The single question: does an authoritative, frozen source operationally define what
"Full four-domain RA-MedFiLM-BARR training" (Phase26) means?  This module gathers the
evidence and NEVER infers an answer.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

# --------------------------------------------------------------------------- paths
ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
TABLE = ROOT / "reports" / "tables"
NB25G = ROOT / "notebooks" / "phasewise" / "phase_25g_controlled_validation"
NB26 = ROOT / "notebooks" / "phasewise" / "phase_26_full_four_domain_training"

# --------------------------------------------------------------- frozen constants
METHOD_NAME = "RA-MedFiLM-BARR"
ARCHITECTURE_ID = "ra_medfilm_barr_narrowed_v1_1"
SEED = 42

# populations
N_TRAIN_TOTAL = 5832          # manifests/phase4_v3/train.csv
N_ROUTER_DEVELOPMENT = 4957   # 85% of TRAIN, DEV
N_ROUTER_HOLDOUT = 875        # 15% of TRAIN, RESERVED for Phase30
N_VAL = 808                   # continuity benchmark, UNOPENED
N_TEST = 1683                 # LOCKED until Phase39

# the exact predecessor terminal Phase26 must observe
PREDECESSOR_TERMINAL = (
    "PHASE25G_INTEGRATED_CONTROLLED_DEVELOPMENT_EVALUATION_COMPLETE__"
    "A7_A8_C8_C9_PRESERVATION_AND_H3_FROZEN__PHASE25_COMPLETE__"
    "PHASE26_ELIGIBLE_NOT_STARTED"
)
PHASE25G_NOTEBOOK_SHA = (
    "5f6b6642fe013d9ad69cac8a0e319d5f86362d8457febdab42fde6cbe14c4487"
)

# terminal outcomes
TERMINAL_SUCCESS = (
    "PHASE26_TRAINING_SPEC_COMPLETE__MODULES_DATA_OBJECTIVE_OPTIMIZATION_AND_"
    "CHECKPOINT_CONTRACT_FROZEN__PHASE26_EXECUTION_ELIGIBLE_NOT_STARTED"
)
TERMINAL_BLOCKED_INCOMPLETE = "PHASE26_BLOCKED__FULL_SYSTEM_TRAINING_SPEC_INCOMPLETE"
TERMINAL_BLOCKED_POLICY = "PHASE26_BLOCKED__NO_PROSPECTIVE_POLICY_SELECTION_RULE"
TERMINAL_BLOCKED_HOLDOUT = "PHASE26_BLOCKED__PHASE30_HOLDOUT_CONTAMINATION_RISK"
TERMINAL_BLOCKED_DRIFT = "PHASE26_BLOCKED__PREDECESSOR_ARTIFACT_DRIFT"

CLASSIFICATION = "PHASE26_PRE_EXECUTION_TRAINING_SPECIFICATION_AUDIT"

# --------------------------------------------------------------------------- SHAs
# Predecessor artifacts whose bytes MUST NOT change.  Verified before and after.
PREDECESSOR_BINDINGS = {
    "notebooks/phasewise/phase_25g_controlled_validation/phase25g_integrated_controlled_evaluation.ipynb":
        PHASE25G_NOTEBOOK_SHA,
    "reports/audits/phase25g_final_freeze.json":
        "48fb05f88fdc88fa33f25342be64bf1f8cc1e62ba7a36eb0e6484c9208c6d276",
    "reports/audits/phase25g_terminal.json":
        "cfe63a7fe1ac031f8e0831a170a82e8ce58e35fd3fa9c94b01fdc9f270addbb1",
    "reports/audits/phase25f_final_freeze.json":
        "383280b9bbd015b8f85b962a453d7a14b40dea424b55b2fe3189d6bac127bb1c",
    "reports/audits/phase25e_final_freeze.json":
        "e20581efab5bb81ec63d118923558df82089b2509f7d5a964da42db4252bab4e",
    "data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/phase25c_oof_paired_gain_labels.csv":
        "fd6ca32c33a3bddb75f986b1350d54ec35b11d3bf5cb0fdc029962a5aa94865f",
    "reports/tables/phase25f_c9_decision_manifest.csv":
        "cde91c474bf19bb36368357ce4b38dd1cc7dad1b37d900fcec7cde6b9e72dbd1",
    "reports/audits/phase24_router_split_manifest.csv":
        "b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555",
    "reports/audits/phase24_exact_implementation_spec.json":
        "6b1a71d5e88ce06baa8f200523be32773428417ffd233ff218d7e50b6af271dd",
    "reports/audits/phase24_benefit_data_protocol_exact.json":
        "6e37a7c82668041e3a83a80e92465e5ea6036acb10e3104a25aa11cdc10a123f",
    "reports/audits/phase25g_no_policy_selection.json":
        "8671d60acf531d03e0b42d606a5e4501fbe7c3947602afc4ccf200f4be12eef0",
    "reports/audits/phase25g_holdout_reservation_for_phase30.json":
        "2935d2dbe00d6658ba52d2bfccd154322145c40e2fbf439b46725cec98b16129",
    "reports/audits/phase30_router_holdout_deferred_contract_stub.json":
        "bfe66b0062785fb61b629fbb0ba7b328dd8bcc7aae671ddb140a4d04d45c716e",
    "reports/audits/phase25g_router_holdout_ownership_supervisor_ruling_v1_0.json":
        "88aa8f272b2bbb05c0ebd85d8e5e69ab92607a9513224cb2457addecee02c90b",
}

# Sources searched for an operational definition of Phase26 (bound by SHA, no inference).
DEFINITION_SOURCES = [
    "notebooks/phasewise/phase_26_full_four_domain_training/README.md",
    "PROJECT_MASTER_PLAN.md",
    "docs/ARCHITECTURE.md",
    "docs/DESIGN.md",
    "docs/PRD.md",
    "docs/RULES.md",
    "docs/TASKS.md",
    "docs/MEMORY.md",
    "notebooks/phasewise/PHASE_INDEX.md",
    "reports/audits/phase24_exact_implementation_spec.json",
    "reports/audits/phase24_benefit_data_protocol_exact.json",
    "reports/audits/phase25g_no_policy_selection.json",
    "reports/audits/phase30_router_holdout_deferred_contract_stub.json",
]

# Declared canonical provenance source named by the Phase26 README; ABSENT on disk.
DECLARED_PHASE26_SPEC = "docs/phase26_training_spec.md"


# --------------------------------------------------------------------------- io
def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_dir(path) -> str:
    """Deterministic digest of a directory: sorted (relpath, size, sha256) lines."""
    p = Path(path)
    lines = []
    for f in sorted(p.rglob("*")):
        if f.is_file():
            lines.append(f"{f.relative_to(p).as_posix()}|{f.stat().st_size}|{sha256_file(f)}")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


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


def bind(path, sha=None):
    """Return a binding record; sha=None means 'compute from disk'."""
    p = ROOT / path
    exists = p.exists()
    actual = sha256_file(p) if (exists and p.is_file()) else (sha256_dir(p) if exists else None)
    return {
        "path": path,
        "exists": bool(exists),
        "sha256": actual,
        "expected_sha256": sha,
        "matches_expected": (sha is None) or (actual == sha),
    }
