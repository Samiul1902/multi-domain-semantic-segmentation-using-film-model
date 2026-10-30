#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 29 — PHASE C shared helpers.

Governance constants, deterministic IO, SHA binding, and the frozen
predecessor registry used by every Phase C stage.

NO training, NO forward pass, NO locked-population access happens at import
time.  This module is pure bookkeeping.

Frozen seed semantics (Phase29 spec v1.1):
    R_psi      fold/final seed = master seed s
    B_phi      fold seed       = 1000*s + k          (k = 0..4)
               final seed      = s
    S_omega    fold seed       = 1000*s + 12000 + k  (k = 0..4)
               final seed      = s
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")

AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures"

CACHE25A = ROOT / "data_cache" / "phase25a_barr_roi030_cache"
CACHE25B = ROOT / "data_cache" / "phase25b_barr_pre_refinement_features_v1_2"
CACHE25C = ROOT / "data_cache" / "phase25c_barr_oof_paired_gain_labels_v1_2"
CACHE25F = ROOT / "data_cache" / "phase25f_barr_post_safety_v1_0"

# ---- phase identities ------------------------------------------------------ #
METHOD = "RA-MedFiLM-BARR"
SPEC_REVISION = "ra_medfilm_barr_phase29_repro_v1_1"
MASTER_SEEDS = [42, 123, 3407]
NEW_SEEDS = [123, 3407]

PHASE_B_TERMINAL = (
    "PHASE29_PHASE_B_TRAINER_PARAMETERIZATION_COMPLETE__SEED42_CONFIG_PARITY_"
    "AND_32_RUN_PLAN_FROZEN__TRAINING_ELIGIBLE_NOT_STARTED"
)
PHASE_A_TERMINAL = "PHASE29_PHASE_A_GATES_PASS__TRAINING_NOT_STARTED"
SPEC_V1_1_TERMINAL = (
    "PHASE29_SPEC_V1_1_COMPLETE__FIXED_GLOBAL_THREE_SEED_BARR_STACK_DEPENDENCIES_"
    "DEV_CALIBRATION_AND_EVALUATION_FROZEN__PHASE29_EXECUTION_ELIGIBLE_NOT_STARTED"
)

SUCCESS_TERMINAL = (
    "PHASE29_PHASE_C_NEW_SEED_TRAINING_COMPLETE__32_RUNS_AND_THREE_SEED_DEV_"
    "REPRODUCIBILITY_FROZEN__PRE_VAL808_GATE_PASS"
)

BLOCKED = {
    "ENTRY_GATE_FAILURE":
        "PHASE29_PHASE_C_BLOCKED__ENTRY_GATE_FAILURE",
    "PREDECESSOR_ARTIFACT_DRIFT":
        "PHASE29_PHASE_C_BLOCKED__PREDECESSOR_ARTIFACT_DRIFT",
    "RUN_ROOT_CONTAMINATION":
        "PHASE29_PHASE_C_BLOCKED__RUN_ROOT_CONTAMINATION",
    "UNAUTHORIZED_TRAINING_RUN":
        "PHASE29_PHASE_C_BLOCKED__UNAUTHORIZED_TRAINING_RUN",
    "RPSI_TRAINING_OR_OOF_FAILURE":
        "PHASE29_PHASE_C_BLOCKED__RPSI_TRAINING_OR_OOF_FAILURE",
    "SEED_SPECIFIC_TARGET_FAILURE":
        "PHASE29_PHASE_C_BLOCKED__SEED_SPECIFIC_TARGET_FAILURE",
    "BPHI_TRAINING_OR_OOF_FAILURE":
        "PHASE29_PHASE_C_BLOCKED__BPHI_TRAINING_OR_OOF_FAILURE",
    "FINAL_ROUTER_CALIBRATION_FAILURE":
        "PHASE29_PHASE_C_BLOCKED__FINAL_ROUTER_CALIBRATION_FAILURE",
    "SOMEGA_TRAINING_OR_OOF_FAILURE":
        "PHASE29_PHASE_C_BLOCKED__SOMEGA_TRAINING_OR_OOF_FAILURE",
    "CROSS_SEED_DEPENDENCY_FAILURE":
        "PHASE29_PHASE_C_BLOCKED__CROSS_SEED_DEPENDENCY_FAILURE",
    "TRAINING_HISTORY_INTEGRITY_FAILURE":
        "PHASE29_PHASE_C_BLOCKED__TRAINING_HISTORY_INTEGRITY_FAILURE",
    "PREMATURE_VAL808_ACCESS":
        "PHASE29_PHASE_C_BLOCKED__PREMATURE_VAL808_ACCESS",
    "VAL808_CACHE_SCHEMA_UNRESOLVED":
        "PHASE29_PHASE_C_BLOCKED__VAL808_CACHE_SCHEMA_UNRESOLVED",
}

# ---- frozen scientific constants ------------------------------------------ #
ROI_PROPOSAL_THRESHOLD = 0.30
SEGMENTATION_OUTPUT_THRESHOLD = 0.50
SOMEGA_ACCEPT_PROB_THRESHOLD = 0.50
CANVAS = 512
CROP = 256

N_DEV = 4957
OOF_BUDGET_B = 0.25
OOF_K = 1239

BENEFICIAL_DELTA = 0.02
HARMFUL_DELTA = -0.01

# exact rational calibration constants (spec v1.1 §20 rule B)
CAL_C = (1051648, 10270749)          # C = 1051648 / 10270749
CAL_LAMBDA = (1, 4)                  # lambda = 1/4
TAU_C7_SEED42 = (24796109646558761, 20000000000000000000)
TAU_C8_SEED42 = (-5003565381643716252018011,
                 205414980000000000000000000)

# ---- seed-42 canonical reuse paths ---------------------------------------- #
SEED42_RPSI_CKPT = ROOT / "checkpoints" / "phase25a_barr_regional_refiner_v1_1_roi030"
SEED42_BPHI_CKPT = (ROOT / "checkpoints"
                    / "phase25d_barr_benefit_router_v1_2_1_seed42")
SEED42_SOMEGA_CKPT = (ROOT / "checkpoints"
                      / "phase25f_barr_post_safety_v1_0_seed42")
SEED42_DELTADICE_CSV = CACHE25C / "phase25c_oof_paired_gain_labels.csv"
SEED42_SOMEGA_FEATURES = CACHE25F / "features.npy"
SEED42_SOMEGA_TARGETS = CACHE25F / "targets.csv"
SEED42_BPHI_OOF_CSV = (ROOT / "data_cache/phase25d_barr_benefit_router_v1_2_1"
                       / "phase25d_oof_router_predictions.csv")

PHASE29_V1_1_SPEC = ROOT / "docs" / "phase29_repro_spec.md"


# --------------------------------------------------------------------------- #
# deterministic io
# --------------------------------------------------------------------------- #
def sha256_file(p) -> str:
    p = Path(p)
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_array(a) -> str:
    import numpy as np
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def sha256_ids(ids) -> str:
    """Stable SHA over an ordered sample-id list (newline joined)."""
    return sha256_bytes(("\n".join(str(i) for i in ids) + "\n").encode("utf-8"))


def atomic_write_bytes(data: bytes, path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(path) + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def atomic_write_text(text: str, path) -> None:
    atomic_write_bytes(text.encode("utf-8"), path)


def atomic_torch_save(obj, path) -> None:
    import io
    import torch
    buf = io.BytesIO()
    torch.save(obj, buf)
    atomic_write_bytes(buf.getvalue(), path)


def write_json(obj, path, indent: int = 1) -> None:
    atomic_write_text(json.dumps(_convert(obj), indent=indent,
                                 ensure_ascii=False) + "\n", path)


def _convert(o):
    try:
        import numpy as np
    except ImportError:
        np = None
    if np is not None and isinstance(o, np.ndarray):
        return o.tolist()
    if np is not None and isinstance(o, (np.float32, np.float64)):
        return float(o)
    if np is not None and isinstance(o, (np.int32, np.int64)):
        return int(o)
    if np is not None and isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, Path):
        return str(o)
    if isinstance(o, dict):
        return {k: _convert(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_convert(v) for v in o]
    return o


def write_csv(path, header, rows) -> None:
    import io
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    for r in rows:
        w.writerow(r)
    atomic_write_bytes(buf.getvalue().encode("utf-8"), path)


def read_csv_rows(path):
    with open(path, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_json(path) -> dict:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------------------- #
# seed helpers
# --------------------------------------------------------------------------- #
def rpsi_seed(master_seed: int) -> int:
    return int(master_seed)


def bphi_fold_seed(master_seed: int, k: int) -> int:
    return 1000 * int(master_seed) + int(k)


def bphi_final_seed(master_seed: int) -> int:
    return int(master_seed)


def somega_fold_seed(master_seed: int, k: int) -> int:
    return 1000 * int(master_seed) + 12000 + int(k)


def somega_final_seed(master_seed: int) -> int:
    return int(master_seed)


def tau_c8_from_c7(tau_c7):
    """Exact rational tau_C8 = tau_C7 - (1/4) * (1051648/10270749).

    Accepts/returns exact (num, den) integer pairs so no float rounding enters
    the frozen calibration constant.
    """
    from fractions import Fraction
    t7 = Fraction(int(tau_c7[0]), int(tau_c7[1]))
    c = Fraction(CAL_C[0], CAL_C[1])
    lam = Fraction(CAL_LAMBDA[0], CAL_LAMBDA[1])
    t8 = t7 - lam * c
    return (t8.numerator, t8.denominator)


# --------------------------------------------------------------------------- #
# seed-specific derived paths
# --------------------------------------------------------------------------- #
def seed_dir(master_seed: int) -> Path:
    return ROOT / "data_cache" / f"phase29_seed{master_seed}"


def rpsi_checkpoint_root(master_seed: int) -> Path:
    if master_seed == 42:
        return SEED42_RPSI_CKPT
    return ROOT / f"checkpoints/phase29_seed{master_seed}"


def rpsi_experiment_root(master_seed: int) -> Path:
    if master_seed == 42:
        return ROOT / "experiments" / "phase25a_barr_regional_refiner_v1_1_roi030"
    return ROOT / f"experiments/phase29_seed{master_seed}"


def bphi_checkpoint_root(master_seed: int) -> Path:
    if master_seed == 42:
        return SEED42_BPHI_CKPT
    return ROOT / f"checkpoints/phase29_seed{master_seed}" / "bphi"


def bphi_experiment_root(master_seed: int) -> Path:
    if master_seed == 42:
        return ROOT / "experiments" / "phase25d_barr_benefit_router_v1_2_1_seed42"
    return ROOT / f"experiments/phase29_seed{master_seed}" / "bphi"


def somega_checkpoint_root(master_seed: int) -> Path:
    if master_seed == 42:
        return SEED42_SOMEGA_CKPT
    return ROOT / f"checkpoints/phase29_seed{master_seed}" / "somega"


def somega_experiment_root(master_seed: int) -> Path:
    if master_seed == 42:
        return ROOT / "experiments" / "phase25f_barr_post_safety_v1_0_seed42"
    return ROOT / f"experiments/phase29_seed{master_seed}" / "somega"


def deltadice_target_path(master_seed: int) -> Path:
    if master_seed == 42:
        return SEED42_DELTADICE_CSV
    return seed_dir(master_seed) / f"phase29_seed{master_seed}_deltadice_targets.csv"


def somega_features_path(master_seed: int) -> Path:
    if master_seed == 42:
        return SEED42_SOMEGA_FEATURES
    return seed_dir(master_seed) / f"phase29_seed{master_seed}_somega_features.npy"


def somega_targets_path(master_seed: int) -> Path:
    if master_seed == 42:
        return SEED42_SOMEGA_TARGETS
    return seed_dir(master_seed) / f"phase29_seed{master_seed}_somega_targets.csv"


# --------------------------------------------------------------------------- #
# frozen predecessor registry (§1)
# --------------------------------------------------------------------------- #
# (name, path, expected_sha256)
PREDECESSORS = [
    ("canonical_G_checkpoint",
     "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
     "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"),
    ("phase25b_feature_matrix",
     "data_cache/phase25b_barr_pre_refinement_features_v1_2/features.npy",
     "9c241963b54f23de1c9671ff6670dde7d6f7e2510869ef5ebc1baf3f7c833e0a"),
    ("phase25b_metadata",
     "data_cache/phase25b_barr_pre_refinement_features_v1_2/metadata.csv",
     "ee8c304350d28d907c053a355da1f878ff7f9dd137761034283459aeed071093"),
    ("phase25c_deltadice_labels",
     "data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/"
     "phase25c_oof_paired_gain_labels.csv",
     "fd6ca32c33a3bddb75f986b1350d54ec35b11d3bf5cb0fdc029962a5aa94865f"),
    ("phase25f_oof_global_crop_prob",
     "data_cache/phase25f_barr_post_safety_v1_0/oof_global_crop_prob.npy",
     "214c83b5754ccaed9f7b504313c93d3297bdb53ca66d7f033b502d54aa6eec64"),
    ("phase25f_oof_refined_crop_prob",
     "data_cache/phase25f_barr_post_safety_v1_0/oof_refined_crop_prob.npy",
     "4c574e3baff158111eb3d609a445e8c43aa359c96cc89aa3ef154cc4af273b87"),
    ("phase25a_roi030_refit_epoch_rule",
     "reports/audits/phase25a_roi030_final_refit_epoch_rule.json",
     "abca1d7242f8ed221d21236a82fbdaf135b153d3a1a92a9d26e8b2a4b898949b"),
    ("phase29_repro_spec_v1_1",
     "docs/phase29_repro_spec.md",
     "3888e0e0987484741c52c1fb2cf75ba7159cc47f1fc8fad368922760c080e6a8"),
    ("phase29_phase_b_final_check",
     "reports/audits/phase29_phase_b_final_check.json", None),
    ("phase29_phase_b_terminal",
     "reports/audits/phase29_phase_b_terminal.json", None),
    ("phase29_new_run_config_registry",
     "reports/audits/phase29_new_run_config_registry.json", None),
    ("phase29_phase_a_terminal",
     "reports/audits/phase29_phase_a_terminal.json", None),
]

# three historical canonical trainer sources that MUST remain byte-identical
CANONICAL_TRAINERS = [
    ("train_phase25a_refiner",
     "scripts/training/train_phase25a_refiner.py",
     "487efd3a934c97bf3b4db13717ac29b567a535346a2510a946943e2506345835"),
    ("train_phase25d_router",
     "scripts/analysis/train_phase25d_router.py",
     "fc7c1bdf263ae4551dcb8f170d3203adb8540fbc189846265b74f6eca1541e91"),
    ("phase25f_execution_common",
     "scripts/analysis/phase25f_execution_common.py",
     "98cf958a377e2de30e0b67e63fd56bafea418b2b061a362ee7284e852012cd2e"),
]


def rehash_predecessors() -> dict:
    """Rehash every frozen predecessor + canonical trainer. Any drift -> drift>0."""
    rows = []
    for name, rel, exp in PREDECESSORS:
        p = ROOT / rel
        exists = p.exists()
        act = sha256_file(p) if exists else None
        rows.append({
            "name": name, "path": rel, "exists": exists,
            "sha256_expected": exp, "sha256_observed": act,
            "unchanged": (None if exp is None else (act == exp)) if exists else False,
            "pinned": exp is not None,
        })
    trainers = []
    for name, rel, exp in CANONICAL_TRAINERS:
        p = ROOT / rel
        act = sha256_file(p) if p.exists() else None
        trainers.append({
            "name": name, "path": rel, "sha256_expected": exp,
            "sha256_observed": act, "unchanged": act == exp,
        })
    drift = ([r["name"] for r in rows
              if r["pinned"] and not r["unchanged"]]
             + [t["name"] for t in trainers if not t["unchanged"]])
    return {"predecessors": rows, "canonical_trainers": trainers,
            "drift": drift, "drift_count": len(drift)}
