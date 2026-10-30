#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 29 — PHASE D shared helpers: shared VAL808 extraction + locked three-seed
validation.

Governance constants, deterministic IO, SHA binding, and the frozen predecessor
registry used by every Phase D stage.

HARD BOUNDARIES (binding, Phase D work order):
    * authorized to open VAL808 ONLY
    * NOT authorized to open ROUTER_HOLDOUT
    * NOT authorized to open TEST
    * NOT authorized to train anything (new_training_runs == 0)
    * NOT authorized to select a best seed
    * NOT authorized to modify any frozen artifact

This module performs NO inference, NO image read and NO GT read at import time.
It is pure bookkeeping.
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

CACHE27 = ROOT / "data_cache" / "phase27_barr_preservation_v1_0"
CACHE29D = ROOT / "data_cache" / "phase29_val808_shared_fixed_g_v1_0"

# ---- phase identities ------------------------------------------------------ #
METHOD = "RA-MedFiLM-BARR"
SPEC_REVISION = "ra_medfilm_barr_phase29_repro_v1_1"

PHASE_C_TERMINAL = (
    "PHASE29_PHASE_C_NEW_SEED_TRAINING_COMPLETE__32_RUNS_AND_THREE_SEED_DEV_"
    "REPRODUCIBILITY_FROZEN__PRE_VAL808_GATE_PASS"
)
PHASE_C_FINAL_CHECK = "reports/audits/phase29_phase_c_final_check.json"
PHASE_C_PRE_VAL808_FREEZE_GATE = "reports/audits/phase29_pre_val808_freeze_gate.json"
VAL808_CACHE_CONTRACT_V1_1 = (
    "reports/audits/phase29_val808_shared_global_cache_contract_v1_1.json")
PHASE_C_REHASH = "reports/audits/phase29_phase_c_predecessor_rehash.json"
PHASE_C_ENTRY_GATE = "reports/audits/phase29_phase_c_entry_gate.json"

# ---- success + blocked terminals (§30 / §31) ------------------------------- #
SUCCESS_TERMINAL = (
    "PHASE29_PHASE_D_VAL808_LOCKED_THREE_SEED_VALIDATION_COMPLETE__SHARED_G_"
    "CACHE_FROZEN__ROUTER_HOLDOUT_AND_TEST_STILL_CLOSED"
)

BLOCKED = {
    "ENTRY_GATE_FAILURE":
        "PHASE29_PHASE_D_BLOCKED__ENTRY_GATE_FAILURE",
    "FROZEN_ARTIFACT_DRIFT":
        "PHASE29_PHASE_D_BLOCKED__FROZEN_ARTIFACT_DRIFT",
    "UNAUTHORIZED_TRAINING":
        "PHASE29_PHASE_D_BLOCKED__UNAUTHORIZED_TRAINING",
    "LOCKED_POPULATION_ACCESS":
        "PHASE29_PHASE_D_BLOCKED__LOCKED_POPULATION_ACCESS",
    "PREMATURE_VAL808_ACCESS":
        "PHASE29_PHASE_D_BLOCKED__PREMATURE_VAL808_ACCESS",
    "GT_LEAKAGE":
        "PHASE29_PHASE_D_BLOCKED__GT_LEAKAGE",
    "VAL808_CACHE_INTEGRITY_FAILURE":
        "PHASE29_PHASE_D_BLOCKED__VAL808_CACHE_INTEGRITY_FAILURE",
    "VAL808_SHARED_G_CACHE_RUN_COUNT_VIOLATION":
        "PHASE29_PHASE_D_BLOCKED__VAL808_SHARED_G_CACHE_RUN_COUNT_VIOLATION",
    "SEED_SPECIFIC_INFERENCE_FAILURE":
        "PHASE29_PHASE_D_BLOCKED__SEED_SPECIFIC_INFERENCE_FAILURE",
    "CROSS_SEED_DEPENDENCY_FAILURE":
        "PHASE29_PHASE_D_BLOCKED__CROSS_SEED_DEPENDENCY_FAILURE",
    "BEST_SEED_SELECTION_ATTEMPT":
        "PHASE29_PHASE_D_BLOCKED__BEST_SEED_SELECTION_ATTEMPT",
    "POST_RESULT_PROTOCOL_MODIFICATION":
        "PHASE29_PHASE_D_BLOCKED__POST_RESULT_PROTOCOL_MODIFICATION",
}

# ---- frozen scientific constants ------------------------------------------ #
ROI_PROPOSAL_THRESHOLD = 0.30
SEGMENTATION_OUTPUT_THRESHOLD = 0.50
SOMEGA_ACCEPT_PROB_THRESHOLD = 0.50
CANVAS = 512
CROP = 256

MASTER_SEEDS = [42, 123, 3407]
DEV_SEEDS = [123, 3407]          # seeds trained in Phase C

N_DEV = 4957
OOF_K = 1239

BENEFICIAL_DELTA = 0.02
HARMFUL_DELTA = -0.01

# exact rational calibration constant C and the frozen cost weight 0.25*C
CAL_C = (1051648, 10270749)
CAL_LAMBDA = (1, 4)
from fractions import Fraction as _F  # noqa: E402
LAMBDA_C_FLOAT = float(_F(*CAL_LAMBDA) * _F(*CAL_C))   # 0.025598133105969194
CAL_LAMBDA_C_EXACT = (CAL_C[0] * CAL_LAMBDA[0], CAL_C[1] * CAL_LAMBDA[1])

# cross-seed comparison domain order (frozen; matches Phase C)
DOMAINS = ["BUSI", "ISIC", "KUB", "KVASIR"]

# ---- common identity (Phase B/C) ------------------------------------------ #
COMMON_TERMINAL = "PHASE29_PHASE_C_NEW_SEED_TRAINING_COMPLETE__32_RUNS_AND_THREE_SEED_DEV_REPRODUCIBILITY_FROZEN__PRE_VAL808_GATE_PASS"

# ---- VAL808 population (frozen Phase27 binding) ---------------------------- #
VAL808_MANIFEST = "manifests/phase4_v3/val.csv"
VAL808_MANIFEST_SHA = "082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315"
VAL808_N = 808
VAL808_DOMAIN_N = {"ISIC": 357, "KUB": 280, "KVASIR": 87, "BUSI": 84}
VAL808_TASK_ID = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}
VAL808_TOTAL_GROUPS = 639

# ---- canonical global model G (Phase21, FIXED — never retrained) ---------- #
G_CHECKPOINT = "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"
G_CHECKPOINT_SHA = (
    "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7")
G_EXPERIMENT_CONFIG = (
    "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json")

# ---- Phase27 VAL808 global-probability cache (authoritative on-disk) ------ #
PHASE27_GLOBAL_PROB = "data_cache/phase27_barr_preservation_v1_0/phase27_val808_global_prob_f16.npy"
PHASE27_GLOBAL_PROB_SHA = (
    "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13")
PHASE27_FINAL_PROB = "data_cache/phase27_barr_preservation_v1_0/phase27_val808_final_prob_f16.npy"
PHASE27_FINAL_PROB_SHA = (
    "506ab6c4e715a9106889e186c146b73903493c80a63258007954cf5deb3ea9cf")
PHASE27_PREDICTIONS_SHA_SIDECAR = "reports/audits/phase27_val808_predictions_sha256.json"

# ---- Phase D shared fixed-G cache contract (§8) --------------------------- #
SHARED_CACHE_FILES = {
    "global_prob": "val808_global_prob_f16.npy",
    "router_deep_features": "val808_router_deep_features_f32.npy",
    "router_scalars": "val808_router_scalars_f32.npy",
    "roi_geometry": "val808_roi_geometry.json",
}
SHARED_G_LOGICAL_PASSES = 1
SHARED_G_SAMPLES = 808
RUNS_ONCE_NOT_PER_SEED = True
G_RETRAINED = False

# ---- frozen trainer + component sources (code provenance) ----------------- #
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
# the ONE declared, user-approved additive entry-point exception (Phase C)
DECLARED_TRAINER_EXCEPTION = "train_phase25a_refiner"
DECLARED_TRAINER_EXCEPTION_SHA_CURRENT = (
    "f281ad8bba4ab502be41e0eebd1315133ff4032a7ae1017b961a82bb3f67c5fd")

# ---- frozen feature extractor sources ------------------------------------- #
FEATURE_SOURCE_PATHS = {
    "pre_refinement_features": "src/features/barr_pre_refinement_features.py",
    "barr_roi": "src/data/barr_roi.py",
    "regional_refiner": "src/models/barr/regional_refiner.py",
    "global_medfilm": "src/models/film/global_medfilm.py",
    "phase25f_execution_common": "scripts/analysis/phase25f_execution_common.py",
    "phase25f_post_safety_features": "scripts/analysis/phase25f_post_safety_features.py",
    "train_phase25d_router": "scripts/analysis/train_phase25d_router.py",
    "phase27_model_import_shim": "scripts/analysis/phase27_model_import_shim.py",
    "phase29_phase_d_common": "scripts/analysis/phase29_phase_d_common.py",
    "phase29_phase_d_cache": "scripts/analysis/phase29_phase_d_cache.py",
}

# ---- per-seed component sources (all frozen by Phase B/C) ----------------- #
SEED42 = {
    "rpsi_final": "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
    "bphi_final": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
    "somega_final": "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
    "tau_c7_exact": (24796109646558761, 20000000000000000000),
    "tau_c8_exact": (-5003565381643716252018011, 205414980000000000000000000),
    "somega_final_epochs": 26,
    "bphi_final_epochs": 65,      # recorded in the integrated audit
}
SEED_INFO = {
    42: SEED42,
    123: {
        "rpsi_final": "checkpoints/phase29_seed123/final/final.pt",
        "bphi_final": "checkpoints/phase29_seed123/bphi/final/final.pt",
        "somega_final": "checkpoints/phase29_seed123/somega/final/final.pt",
        "tau_c7_exact": (3697925, 1073741824),
        "tau_c8_exact": (-244319150935663, 11028132765106176),
        "somega_final_epochs": 31,
        "bphi_final_epochs": 65,
    },
    3407: {
        "rpsi_final": "checkpoints/phase29_seed3407/final/final.pt",
        "bphi_final": "checkpoints/phase29_seed3407/bphi/final/final.pt",
        "somega_final": "checkpoints/phase29_seed3407/somega/final/final.pt",
        "tau_c7_exact": (1202329, 268435456),
        "tau_c8_exact": (-58226083233451, 2757033191276544),
        "somega_final_epochs": 11,
        "bphi_final_epochs": 70,
    },
}

# ---- frozen router / safety normalisation (seed-specific, from ckpt) ------ #
ROUTER_SCALAR_IDX = [192, 193, 194, 195, 196, 197, 200, 201]   # frozen Phase25B
ROUTER_NUMERIC_DIM = 202
ROUTER_DEEP_DIM = 192
ROUTER_SCALAR_DIM = 10
SOMEGA_FEATURE_DIM = 20
SOMEGA_NUMERIC_IDX = list(range(0, 16))
SOMEGA_ONEHOT_IDX = list(range(16, 20))


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
# exact rational helper
# --------------------------------------------------------------------------- #
def tau_float(pair) -> float:
    from fractions import Fraction
    return float(Fraction(int(pair[0]), int(pair[1])))


def seed_dir(master_seed: int) -> Path:
    return ROOT / "data_cache" / f"phase29_seed{master_seed}"


# --------------------------------------------------------------------------- #
# predecessor registry (§1) — all frozen Phase C artifacts, rehashed
# --------------------------------------------------------------------------- #
PREDECESSORS = [
    ("phase_c_terminal_reference", PHASE_C_FINAL_CHECK, None),
    ("phase_c_entry_gate", PHASE_C_ENTRY_GATE, None),
    ("phase_c_predecessor_rehash", PHASE_C_REHASH, None),
    ("phase_c_no_locked_population_audit",
     "reports/audits/phase29_phase_c_no_locked_population_audit.json", None),
    ("training_run_registry", "reports/audits/phase29_training_run_registry.json", None),
    ("training_run_count_final_audit",
     "reports/audits/phase29_training_run_count_final_audit.json", None),
    ("new_training_history_integrity",
     "reports/audits/phase29_new_training_history_integrity.json", None),
    ("cross_seed_dependency_isolation",
     "reports/audits/phase29_cross_seed_dependency_isolation.json", None),
    ("pre_val808_freeze_gate", PHASE_C_PRE_VAL808_FREEZE_GATE, None),
    ("val808_shared_global_cache_contract_v1_1", VAL808_CACHE_CONTRACT_V1_1, None),
    ("fixed_partition_full_identity_proof",
     "reports/audits/phase29_fixed_partition_full_identity_proof.json", None),
    ("phase29_repro_spec_v1_1", "docs/phase29_repro_spec.md",
     "3888e0e0987484741c52c1fb2cf75ba7159cc47f1fc8fad368922760c080e6a8"),
]

SEED_PREDECESSORS = [
    ("seed{s}_rpsi_chain", "reports/audits/phase29_seed{s}_rpsi_chain.json"),
    ("seed{s}_rpsi_oof_integrity",
     "reports/audits/phase29_seed{s}_rpsi_oof_integrity.json"),
    ("seed{s}_gain_target_freeze",
     "reports/audits/phase29_seed{s}_gain_target_freeze.json"),
    ("seed{s}_bphi_oof_integrity",
     "reports/audits/phase29_seed{s}_bphi_oof_integrity.json"),
    ("seed{s}_bphi_oof_membership_freeze",
     "reports/audits/phase29_seed{s}_bphi_oof_membership_freeze.json"),
    ("seed{s}_final_router_calibration",
     "reports/audits/phase29_seed{s}_final_router_calibration.json"),
    ("seed{s}_somega_oof_integrity",
     "reports/audits/phase29_seed{s}_somega_oof_integrity.json"),
    ("seed{s}_somega_final_epoch_rule",
     "reports/audits/phase29_seed{s}_somega_final_epoch_rule.json"),
    ("seed{s}_somega_final_refit",
     "reports/audits/phase29_seed{s}_somega_final_refit.json"),
    ("seed{s}_integrated_oof", "reports/audits/phase29_seed{s}_integrated_oof.json"),
]

# the three canonical global/Phase25 component checkpoints
CANONICAL_COMPONENTS = [
    ("canonical_G", G_CHECKPOINT, G_CHECKPOINT_SHA),
    ("phase26_rpsi", "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
     "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109"),
    ("phase26_bphi", "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
     "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b"),
    ("phase26_somega", "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
     "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e"),
]

# Phase27 global cache (global prob only; the ONLY Phase27 artifact Phase D reuses)
PHASE27_CACHE_ARTIFACTS = [
    ("phase27_global_prob", PHASE27_GLOBAL_PROB, PHASE27_GLOBAL_PROB_SHA),
    ("phase27_final_prob", PHASE27_FINAL_PROB, PHASE27_FINAL_PROB_SHA),
    ("phase27_bootstrap_plan",
     "data_cache/phase27_barr_preservation_v1_0/phase27_val808_bootstrap_plan_v1_0.npz",
     "8d32bd3c9b18f03c39128593f287bd21d716d26e11eb90d80f6f9c0d0b450a93"),
    ("phase27_predictions_csv",
     "reports/tables/phase27_val808_predictions.csv",
     "bb2a6237160b79cda644173e91e17878598d5d0b396b7db08089b05104dcc1c6"),
]

# globals for the frozen Phase27 probability cache (authoritative, GT-free)
PHASE27_GLOBAL_PROB_MARKER = "phase27_val808_global_prob_f16.npy"


def rehash_predecessors() -> dict:
    """Rehash every frozen predecessor + canonical trainer + component.

    Any drift outside the ONE declared, user-approved additive entry-point
    exception produces a non-empty ``drift`` list -> STOP
    PHASE29_PHASE_D_BLOCKED__FROZEN_ARTIFACT_DRIFT.
    """
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
    seed_rows = []
    for s in MASTER_SEEDS:
        for tname, trel in SEED_PREDECESSORS:
            rel = trel.format(s=s)
            p = ROOT / rel
            seed_rows.append({
                "name": tname.format(s=s), "path": rel, "exists": p.exists(),
                "sha256_observed": sha256_file(p) if p.exists() else None,
                "unchanged": True,   # recorded for provenance; no pinned baseline
                "pinned": False,
            })
    comps = []
    for name, rel, exp in CANONICAL_COMPONENTS:
        p = ROOT / rel
        act = sha256_file(p) if p.exists() else None
        comps.append({
            "name": name, "path": rel, "sha256_expected": exp,
            "sha256_observed": act, "unchanged": act == exp,
        })
    cache27 = []
    for name, rel, exp in PHASE27_CACHE_ARTIFACTS:
        p = ROOT / rel
        act = sha256_file(p) if p.exists() else None
        cache27.append({
            "name": name, "path": rel, "sha256_expected": exp,
            "sha256_observed": act, "unchanged": act == exp,
        })
    trainers = []
    for name, rel, exp in CANONICAL_TRAINERS:
        p = ROOT / rel
        act = sha256_file(p) if p.exists() else None
        is_exception = (name == DECLARED_TRAINER_EXCEPTION)
        expected_now = (DECLARED_TRAINER_EXCEPTION_SHA_CURRENT
                        if is_exception else exp)
        trainers.append({
            "name": name, "path": rel,
            "sha256_expected_frozen": exp,
            "sha256_expected_effective": expected_now,
            "sha256_observed": act,
            "declared_additive_exception": is_exception,
            "unchanged": act == expected_now,
        })

    drift = ([r["name"] for r in rows if r["pinned"] and not r["unchanged"]]
             + [c["name"] for c in comps if not c["unchanged"]]
             + [c["name"] for c in cache27 if not c["unchanged"]]
             + [t["name"] for t in trainers if not t["unchanged"]])
    return {"predecessors": rows + seed_rows, "canonical_components": comps,
            "phase27_cache": cache27, "canonical_trainers": trainers,
            "drift": drift, "drift_count": len(drift)}


# --------------------------------------------------------------------------- #
# canonical VAL808 order (§6): domain asc, sample_id asc
# --------------------------------------------------------------------------- #
def val808_rows():
    """Read the frozen VAL808 manifest rows (metadata only)."""
    with open(ROOT / VAL808_MANIFEST, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def canonical_val808_order():
    rows = val808_rows()
    return sorted(rows, key=lambda r: (r["dataset"], str(r["sample_id"])))


def domain_order():
    return sorted(set(r["dataset"] for r in val808_rows()))
