"""Phase 25F — POST-SAFETY SPECIFICATION REPAIR (supervisor ruling / additive
pre-execution freeze).

Shared helpers for the repair scripts. This module performs NO model
construction, NO training, NO forward pass, NO refinement and NO DeltaDice
recomputation. It only reads frozen caches, materialises provenance-safe
derived caches, computes GT-free features and writes audit/contract artifacts.

Revision created by this repair: ``ra_medfilm_barr_post_safety_v1_0``.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
CACHE25F = ROOT / "data_cache" / "phase25f_barr_post_safety_v1_0"

METHOD = "RA-MedFiLM-BARR"
CLASSIFICATION = "PRE_EXECUTION_POST_SAFETY_SPECIFICATION_COMPLETENESS_REPAIR"
REVISION = "ra_medfilm_barr_post_safety_v1_0"

MASTER_SEED = 42

# ---- frozen predecessors --------------------------------------------------- #
PHASE25F_BLOCKED_TERMINAL = "PHASE25F_BLOCKED__POST_SAFETY_EXECUTION_SPEC_INCOMPLETE"
PHASE25E_RECONCILED_TERMINAL = (
    "PHASE25E_CANONICAL_ADJUDICATION_REPAIRED__PRIMARY_PHASE24_STATISTICS_RESTORED__"
    "HOLM_RETAINED_AS_SENSITIVITY__PHASE25F_ELIGIBLE_NOT_STARTED"
)
PHASE25E_RECONCILED_NOTEBOOK_SHA = (
    "b587cc925fa178f1a0eaaa986caa3cb77dbc71ecd9fd520312af7f2097091797"
)
PHASE25E_FINAL_FREEZE_SHA = (
    "e20581efab5bb81ec63d118923558df82089b2509f7d5a964da42db4252bab4e"
)

EXPECTED_BLOCKING_FIELD_COUNT = 54
EXPECTED_HARD_STOP_COUNT = 12

# ---- frozen Phase25C source ------------------------------------------------- #
PHASE25C_DIR = ROOT / "data_cache" / "phase25c_barr_oof_paired_gain_labels_v1_2"
PHASE25C_LABEL_CSV = PHASE25C_DIR / "phase25c_oof_paired_gain_labels.csv"
PHASE25C_LABEL_MANIFEST = PHASE25C_DIR / "label_manifest.json"
PHASE25C_LABEL_CSV_SHA = "fd6ca32c33a3bddb75f986b1350d54ec35b11d3bf5cb0fdc029962a5aa94865f"
PHASE25C_WRITER = ROOT / "scripts" / "analysis" / "run_phase25c_oof_inference.py"
PHASE25C_COMMON = (
    ROOT / "notebooks" / "phasewise" / "phase_25c_paired_gain_labels" / "code"
    / "phase25c_common.py"
)

# ---- frozen Phase25A ROI-0.30 cache (global probabilities + geometry) -------- #
ROI030_CACHE = ROOT / "data_cache" / "phase25a_barr_roi030_cache"
DOMAINS = ("BUSI", "ISIC", "KUB", "KVASIR")
TASK_ID = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}
TASK_ONEHOT_ORDER = ["task_0_ISIC", "task_1_BUSI", "task_2_KVASIR", "task_3_KUB"]

# ---- frozen Phase25B pre-refinement scalar cache (features 14 / 15) ---------- #
PHASE25B_CACHE = ROOT / "data_cache" / "phase25b_barr_pre_refinement_features_v1_2"
PHASE25B_METADATA = PHASE25B_CACHE / "metadata.csv"
PHASE25B_FEATURES = PHASE25B_CACHE / "features.npy"
PHASE25B_FEATURES_SHA = "9c241963b54f23de1c9671ff6670dde7d6f7e2510869ef5ebc1baf3f7c833e0a"
PHASE25B_METADATA_SHA = "ee8c304350d28d907c053a355da1f878ff7f9dd137761034283459aeed071093"
# scalar offsets in the 202-D Phase25B matrix
PHASE25B_SCALAR_START = 192
PHASE25B_IDX_ROI_AREA_FRACTION = 200
PHASE25B_IDX_ROI_SIDE = 201

# ---- frozen Phase25D CV identity manifests (reused, not reinvented) ---------- #
PHASE25D_CV5_MANIFEST = TAB / "phase25d_cv5_manifest.csv"
PHASE25D_CV_FOLD = {
    k: {
        "fit": TAB / f"phase25d_cv_fold{k}_fit_ids.csv",
        "early_stop": TAB / f"phase25d_cv_fold{k}_early_stop_ids.csv",
        "outer_target": TAB / f"phase25d_cv_fold{k}_outer_target_ids.csv",
    }
    for k in range(5)
}

# ---- frozen thresholds (three distinct roles; never conflated) -------------- #
ROI_PROPOSAL_THRESHOLD = 0.30
SEGMENTATION_OUTPUT_THRESHOLD = 0.50
SOMEGA_ACCEPT_PROBABILITY_THRESHOLD = 0.50
SOMEGA_ACCEPT_LOGIT_THRESHOLD = 0.0

# ---- frozen S_omega constants ---------------------------------------------- #
FEATURE_DIM = 20
NUMERIC_DIM = 16
ONEHOT_DIM = 4
HIDDEN_DIMS = (32, 16)
EXPECTED_PARAM_COUNT = 1217

N_ROUTER_DEVELOPMENT = 4957

# execution seeds
SOMEGA_CV_SEEDS = {0: 54000, 1: 54001, 2: 54002, 3: 54003, 4: 54004}
FINAL_REFIT_SEED = 42

# training
OPTIMIZER = "AdamW"
LR = 1e-3
WEIGHT_DECAY = 1e-4
BATCH_SIZE = 128
MAX_EPOCHS = 200
PATIENCE = 20

_EPOCH_RE = re.compile(r"^[0-9]+$")

# ---- Work Order F blocked-attempt artifacts (provenance, must stay verbatim) -- #
# Pinned explicitly so a post-repair re-run of the entry gate can never capture
# the repair's own outputs (which would be a self-reference).
BLOCKED_ATTEMPT_ARTIFACTS = [
    "reports/audits/phase25f_frozen_spec_entry_gate.json",
    "reports/audits/phase25f_role_and_novelty_boundary.json",
    "reports/audits/phase25f_post_safety_spec_binding.json",
    "reports/audits/phase25f_training_data_source_audit.json",
    "reports/audits/phase25f_leakage_safety_audit.json",
    "reports/audits/phase25f_threshold_semantics_audit.json",
    "reports/audits/phase25f_fusion_fallback_contract_audit.json",
    "reports/audits/phase25f_a7_a8_evaluation_ownership.json",
    "reports/audits/phase25f_scope_guard.json",
    "reports/audits/phase25f_test_lock_audit.json",
    "reports/audits/phase25f_specification_final_check.json",
    "reports/tables/phase25f_specification_completeness.csv",
    "reports/tables/phase25f_training_data_leakage_contract.csv",
    "reports/tables/phase25f_post_safety_input_contract.csv",
]


# --------------------------------------------------------------------------- #
# hashing / io
# --------------------------------------------------------------------------- #
def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_array(a) -> str:
    import numpy as np
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def jload(p: Path) -> dict:
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def jdump(obj, p: Path) -> None:
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")


def bind(p: Path) -> dict:
    p = Path(p)
    return {"path": str(p.relative_to(ROOT)).replace("\\", "/"),
            "exists": p.exists(),
            "sha256": sha256_file(p) if p.exists() else None}


def csv_text(df) -> str:
    """Deterministic CSV serialisation (LF, no index, utf-8)."""
    return df.to_csv(index=False, lineterminator="\n")
