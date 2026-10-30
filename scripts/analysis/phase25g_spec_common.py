"""Phase 25G — PRE-EXECUTION INTEGRATED EVALUATION SPECIFICATION AUDIT.

Shared helpers for the Phase25G specification-audit scripts.

GOVERNANCE / SPECIFICATION ONLY. This module performs NO model construction,
NO training, NO forward pass, NO refinement, NO DeltaDice recomputation, NO
threshold tuning, and NO A7/A8 or C8/C9 evaluation. It reads only frozen
Phase24/25A-25F artifacts and writes audit/contract JSON + CSV artifacts.

Nothing in this module may open ROUTER_HOLDOUT, VAL808 or TEST.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"

METHOD = "RA-MedFiLM-BARR"
CLASSIFICATION = "PHASE25G_PRE_EXECUTION_INTEGRATED_EVALUATION_SPECIFICATION_AUDIT"
REVISION = "ra_medfilm_barr_integrated_evaluation_v1_0"

MASTER_SEED = 42

# ---- §0 required predecessor ------------------------------------------------- #
PREDECESSOR_TERMINAL = (
    "PHASE25F_CANONICAL_CLOSURE_REPAIRED__FULL_CV_EPOCH_NOTEBOOK_FROZEN__"
    "SCIENTIFIC_ARTIFACTS_UNCHANGED__PHASE25G_ELIGIBLE_NOT_STARTED"
)
PHASE25F_EXECUTION_TERMINAL = (
    "PHASE25F_POST_SAFETY_EXECUTION_COMPLETE__OOF_SAFETY_PREDICTIONS_FINAL_"
    "CHECKPOINT_AND_C9_ARTIFACTS_FROZEN__PHASE25G_ELIGIBLE_NOT_STARTED"
)

NOTEBOOK_SHA = "1ba9c08bee97e95926994b11268017e8d6b45150929ebe6edfca4dfe95715c90"
FINAL_FREEZE_SHA = "383280b9bbd015b8f85b962a453d7a14b40dea424b55b2fe3189d6bac127bb1c"
FINAL_CKPT_SHA = "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e"
OOF_SHA = "a9f63edd6d58a9a1d78a052a3e4539c6e0dd4d68bfb1c09c4c36789c441ebdee"
C9_MANIFEST_SHA = "cde91c474bf19bb36368357ce4b38dd1cc7dad1b37d900fcec7cde6b9e72dbd1"
PHASE25E_FINAL_FREEZE_SHA = "e20581efab5bb81ec63d118923558df82089b2509f7d5a964da42db4252bab4e"

NOTEBOOK_PATH = "notebooks/phasewise/phase_25f_post_safety/phase25f_post_safety_execution.ipynb"
FINAL_FREEZE_PATH = "reports/audits/phase25f_final_freeze.json"
FINAL_CKPT_PATH = "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt"
OOF_PATH = "data_cache/phase25f_barr_post_safety_v1_0/phase25f_oof_safety_predictions.csv"
C9_MANIFEST_PATH = "reports/tables/phase25f_c9_decision_manifest.csv"

# ---- terminals --------------------------------------------------------------- #
TERMINAL_SUCCESS = (
    "PHASE25G_INTEGRATED_EVALUATION_SPEC_COMPLETE__A7_A8_PRESERVATION_STATISTICS_"
    "AND_POPULATION_OWNERSHIP_FROZEN__PHASE25G_EXECUTION_ELIGIBLE_NOT_STARTED"
)
TERMINAL_HOLDOUT_UNRESOLVED = "PHASE25G_BLOCKED__ONE_SHOT_HOLDOUT_OWNERSHIP_UNRESOLVED"
TERMINAL_SPEC_INCOMPLETE = "PHASE25G_BLOCKED__INTEGRATED_EVALUATION_SPEC_INCOMPLETE"
TERMINAL_PREDECESSOR_DRIFT = "PHASE25G_BLOCKED__PREDECESSOR_ARTIFACT_DRIFT"

# ---- §3 holdout ownership classifications ------------------------------------ #
OWN_25G = "PHASE25G_ONE_SHOT_HOLDOUT_EXPLICITLY_AUTHORIZED"
OWN_LATER = "LATER_PHASE_ONE_SHOT_HOLDOUT_EXPLICITLY_AUTHORIZED"
OWN_NOT_EXPLICIT = "ONE_SHOT_HOLDOUT_PHASE_OWNERSHIP_NOT_EXPLICIT"

# ---- frozen evaluation constants --------------------------------------------- #
LAMBDA_GRID = ["0.00", "0.25", "0.50", "1.00"]
BUDGET_GRID = ["0.00", "0.10", "0.25", "0.50", "1.00"]
BUDGET_CARDINALITIES = {"0.00": 0, "0.10": 495, "0.25": 1239, "0.50": 2478, "1.00": 4957}
N_ROUTER_DEVELOPMENT = 4957
N_POLICIES = 20
C9_ROWS = 99140

BENEFICIAL_THRESHOLD = 0.02
HARMFUL_THRESHOLD = -0.01

PRESERVATION_MARGIN = 0.005

BOOTSTRAP_TYPE = "DOMAIN_STRATIFIED_GROUP_BOOTSTRAP"
BOOTSTRAP_N = 2000
BOOTSTRAP_SEED = 42
BOOTSTRAP_GROUP_UNIT = "phase24_router_split_manifest.csv:group_key"
BOOTSTRAP_TOTAL_GROUPS = 3544

GLOBAL_MACS = 31551740928
REFINER_MACS = 3230662656
ROUTER_MACS = 36160
SOMEGA_MACS = 1168  # Linear(20,32) + Linear(32,16) + Linear(16,1) = 640+512+16

SOMEGA_ACCEPT_PROBABILITY_THRESHOLD = 0.50

SEGMENTATION_OUTPUT_THRESHOLD = 0.50
ROI_PROPOSAL_THRESHOLD = 0.30

# ---- §1 authoritative sources ------------------------------------------------ #
# (path, role)
SOURCES = [
    # Phase24 architectural + protocol sources
    ("reports/audits/phase24_architecture_spec.json",
     "Phase24 architecture spec: ablation A7/A8, post_safety S_omega, gate rule, VAL/TEST roles"),
    ("reports/audits/phase24_exact_implementation_spec.json",
     "Phase24 exact implementation spec: holdout_use, forbidden tuning sources, hypotheses H1-H6"),
    ("reports/audits/phase24_preservation_contract.json",
     "Phase24 preservation contract: non-inferiority Delta rule, margin 0.005, per-domain"),
    ("reports/audits/phase24_benefit_data_protocol.json",
     "Phase24 benefit data protocol: ROUTER_DEVELOPMENT / ROUTER_HOLDOUT split roles"),
    ("reports/audits/phase24_phase25_module_plan.json",
     "Phase24 module plan: 25G name/deliverable/starts_after"),
    ("reports/audits/phase24_resource_utility_contract.json",
     "Phase24 resource utility contract"),
    ("reports/tables/phase24_data_role_contract.csv",
     "Phase24 data role contract: ROUTER_HOLDOUT / ROUTER_DEVELOPMENT / VAL808 / TEST"),
    ("reports/tables/phase24_ablation_plan.csv",
     "Phase24 ablation plan: A7 = A6+resource cost; A8 = A7+post-safety"),
    ("reports/tables/phase24_comparator_plan.csv",
     "Phase24 comparator plan: C1-C11 definitions"),
    ("reports/tables/phase24_success_failure_criteria.csv",
     "Phase24 success/failure criteria: F1-F5, S1-S3"),
    ("reports/audits/phase24_router_split_manifest.csv",
     "Phase24 router split manifest: ROUTER_HOLDOUT/DEVELOPMENT membership + group_key"),
    # Phase25E resource-gate contracts
    ("reports/audits/phase25e_phase24_resource_contract_binding.json",
     "Phase25E resource-gate contract binding"),
    ("reports/audits/phase25e_lambda_grid_contract_v1_0.json",
     "Phase25E lambda grid contract (0.00/0.25/0.50/1.00)"),
    ("reports/audits/phase25e_fixed_budget_contract_v1_0.json",
     "Phase25E fixed budget contract (0/10/25/50/100%) + cardinalities"),
    ("reports/audits/phase25e_resource_cost_contract_v1_0.json",
     "Phase25E resource cost contract (C_i, MACs, accounting label)"),
    ("reports/audits/phase25e_evaluation_statistics_contract_v1_0.json",
     "Phase25E statistics contract (bootstrap plan, p-value, multiplicity)"),
    ("reports/audits/phase25e_final_freeze.json",
     "Phase25E reconciled final closure"),
    ("reports/audits/phase25e_adjudication_reconciled.json",
     "Phase25E reconciled adjudication (Holm secondary)"),
    ("reports/audits/phase25e_success_failure_criteria_binding.json",
     "Phase25E success/failure criteria binding"),
    ("reports/audits/phase25e_phase25f_handoff_schema.json",
     "Phase25E->Phase25F handoff schema (C9 scope)"),
    ("reports/audits/phase25e_comparator_direction_contract_v1_0.json",
     "Phase25E comparator direction contract (C9 direction)"),
    ("reports/tables/phase25e_analytical_compute_contract.csv",
     "Phase25E analytical compute contract (GLOBAL/ROUTER/REFINER MACs)"),
    ("reports/tables/phase25e_policy_evaluation_metrics.csv",
     "Phase25E policy evaluation metrics (DEV)"),
    ("reports/audits/phase25e_test_lock_audit.json",
     "Phase25E TEST lock audit"),
    # Phase25F post-safety sources
    ("reports/audits/phase25f_a7_a8_ownership_ruling_v1_0.json",
     "Phase25F A7/A8 ownership ruling (supervisor ruling F1)"),
    ("reports/audits/phase25f_a7_a8_execution_guard.json",
     "Phase25F A7/A8 execution guard"),
    ("reports/audits/phase25f_c9_decision_artifact.json",
     "Phase25F C9 construction contract (state/decision artifact)"),
    ("reports/audits/phase25f_c9_scope_guard.json",
     "Phase25F C9 scope guard"),
    ("reports/audits/phase25f_phase25g_handoff.json",
     "Phase25F -> Phase25G handoff"),
    ("reports/audits/phase25f_final_freeze.json",
     "Phase25F final scientific freeze"),
    ("reports/audits/phase25f_final_freeze_notebook_compliance_addendum.json",
     "Phase25F final-freeze notebook compliance addendum"),
    ("reports/audits/phase25f_test_lock_audit.json",
     "Phase25F TEST lock audit"),
    ("reports/audits/phase25f_classifier_metrics.json",
     "Phase25F classifier-level metrics (descriptive only)"),
    ("reports/audits/phase25f_post_safety_spec_completion_v1_0.json",
     "Phase25F post-safety spec completion (A7/A8 owner)"),
    ("reports/tables/phase25f_c9_decision_manifest.csv",
     "Phase25F C9 decision manifest (20 DEV policies, 99140 rows)"),
    # Phase25D router + Phase25C labels
    ("reports/audits/phase25d_final_freeze.json",
     "Phase25D benefit-router final freeze"),
    ("data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/phase25c_oof_paired_gain_labels.csv",
     "Phase25C OOF paired-gain labels (DEV reconstruction source d_i)"),
    ("reports/tables/phase25e_final_router_dev_thresholds.csv",
     "Phase25E final DEV-calibrated router thresholds"),
]


# --------------------------------------------------------------------------- #
def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jload(p) -> dict:
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def jdump(obj, p) -> None:
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")


def bind(p) -> dict:
    p = Path(p)
    return {
        "path": str(p.relative_to(ROOT)).replace("\\", "/"),
        "exists": p.exists(),
        "sha256": sha256_file(p) if p.exists() else None,
    }


def source_binding() -> list:
    out = []
    for rel, role in SOURCES:
        p = ROOT / rel
        out.append({
            "path": rel,
            "role": role,
            "exists": p.exists(),
            "sha256": sha256_file(p) if p.exists() else None,
        })
    return out


def base_audit(name: str, **extra) -> dict:
    d = {
        "artifact": name,
        "phase": "25G",
        "classification": CLASSIFICATION,
        "method": METHOD,
        "specification_revision": REVISION,
        "governance_only": True,
        "no_execution": True,
    }
    d.update(extra)
    return d


def write_json(name: str, obj: dict) -> dict:
    jdump(obj, AUD / f"{name}.json")
    return obj


def csv_text(rows: list, header: list) -> str:
    import csv
    import io
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    for r in rows:
        w.writerow([r.get(h, "") for h in header])
    return buf.getvalue()


def write_csv(name: str, rows: list, header: list) -> None:
    (TAB / f"{name}.csv").write_text(csv_text(rows, header), encoding="utf-8")
