#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 29 — S_omega (BARRPostSafetyV1) ADDITIVE WRAPPER.

PURPOSE
-------
Launch the canonical Phase25F post-safety training under a Phase29 master seed
and SEED-SPECIFIC features/targets, WITHOUT modifying the historical canonical
execution module.

DESIGN (additive-only)
----------------------
``scripts/analysis/phase25f_execution_common.py`` is an importable module whose
constants (``CV_SEEDS``, ``FINAL_SEED``, ``CKPT_ROOT``, ``EXP_ROOT``,
``FEATURES_NPY``, ``TARGETS_CSV``) are module-level and therefore overlayable
IN MEMORY at import time. The canonical source is NEVER written to.

FROZEN SEED SEMANTICS (Phase29 spec v1.1 §9.5)
----------------------------------------------
safety_fold_seed(s, k) = 1000*s + 12000 + k    for k = 0..4
final all-DEV safety refit seed = s

seed42  -> 54000..54004    (canonical parity)
seed123 -> 135000..135004
seed3407-> 3419000..3419004

NO TRAINING HAPPENS IN PHASE B.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_MODULE = ROOT / "scripts" / "analysis" / "phase25f_execution_common.py"

VALID_SEEDS = (42, 123, 3407)
N_FOLDS = 5

# frozen Phase25F constants (mirrored for parity fingerprinting)
FEATURE_DIM = 20
NUMERIC_IDX = list(range(0, 16))
ONEHOT_IDX = list(range(16, 20))
HIDDEN = (32, 16)
PARAM_COUNT = 1217
LOSS = "BCEWithLogitsLoss(reduction='mean')"
LR = 1e-3
WEIGHT_DECAY = 1e-4
BATCH_SIZE = 128
MAX_EPOCHS = 200
PATIENCE = 20
IMPROVEMENT_EPS = 1e-12
SCHEDULER = "ReduceLROnPlateau"
CHECKPOINT_RULE = "minimum EARLY_STOP mean BCE"
DECISION_THRESHOLD = 0.50
FINAL_EPOCH_RULE = "integer median of five best fold epochs"

FIXED_TARGETS_SEED42 = (ROOT / "data_cache/phase25f_barr_post_safety_v1_0"
                        / "targets.csv")
FIXED_FEATURES_SEED42 = (ROOT / "data_cache/phase25f_barr_post_safety_v1_0"
                         / "features.npy")


def safety_fold_seed(master_seed: int, k: int) -> int:
    """Phase29 §9.5 frozen generalization: 1000*s + 12000 + k."""
    return 1000 * int(master_seed) + 12000 + int(k)


def final_refit_seed(master_seed: int) -> int:
    return int(master_seed)


def seed_roots(master_seed: int) -> tuple[Path, Path]:
    return (ROOT / f"checkpoints/phase29_seed{master_seed}",
            ROOT / f"experiments/phase29_seed{master_seed}")


def features_path_for_seed(master_seed: int) -> Path:
    if master_seed == 42:
        return FIXED_FEATURES_SEED42
    return (ROOT / "data_cache" / f"phase29_seed{master_seed}"
            / f"phase29_seed{master_seed}_somega_features.npy")


def targets_path_for_seed(master_seed: int) -> Path:
    if master_seed == 42:
        return FIXED_TARGETS_SEED42
    return (ROOT / "data_cache" / f"phase29_seed{master_seed}"
            / f"phase29_seed{master_seed}_somega_targets.csv")


def build_fold_spec(master_seed: int, k: int,
                    ckpt_root: str | None = None,
                    exp_root: str | None = None,
                    features_path: str | None = None,
                    targets_path: str | None = None) -> dict:
    """Resolve one S_omega fold launch specification (pure; no training)."""
    if master_seed not in VALID_SEEDS:
        raise ValueError(f"master_seed must be one of {VALID_SEEDS}")
    if not (0 <= k < N_FOLDS):
        raise ValueError(f"fold must be 0..{N_FOLDS-1}")

    dck, dex = seed_roots(master_seed)
    ck = Path(ckpt_root) if ckpt_root else dck
    ex = Path(exp_root) if exp_root else dex
    fp = Path(features_path) if features_path else features_path_for_seed(master_seed)
    tp = Path(targets_path) if targets_path else targets_path_for_seed(master_seed)

    return {
        "component": "S_omega",
        "role": f"fold{k}",
        "is_final_refit": False,
        "master_seed": int(master_seed),
        "training_seed": safety_fold_seed(master_seed, k),
        "features_path": str(fp),
        "targets_path": str(tp),
        "fold_members_source":
            "reports/tables/phase25f_cv_fold_role_assignments.csv",
        "checkpoint_root": str(ck),
        "experiment_root": str(ex),
        "run_checkpoint_dir": str(ck / "somega" / f"fold{k}"),
        "run_experiment_dir": str(ex / "somega" / f"fold{k}"),
        "decision_threshold": DECISION_THRESHOLD,
    }


def build_final_spec(master_seed: int, ckpt_root: str | None = None,
                     exp_root: str | None = None,
                     features_path: str | None = None,
                     targets_path: str | None = None,
                     final_epochs: int | None = None) -> dict:
    if master_seed not in VALID_SEEDS:
        raise ValueError(f"master_seed must be one of {VALID_SEEDS}")
    dck, dex = seed_roots(master_seed)
    ck = Path(ckpt_root) if ckpt_root else dck
    ex = Path(exp_root) if exp_root else dex
    fp = Path(features_path) if features_path else features_path_for_seed(master_seed)
    tp = Path(targets_path) if targets_path else targets_path_for_seed(master_seed)
    return {
        "component": "S_omega",
        "role": "final",
        "is_final_refit": True,
        "master_seed": int(master_seed),
        "training_seed": final_refit_seed(master_seed),
        "features_path": str(fp),
        "targets_path": str(tp),
        "checkpoint_root": str(ck),
        "experiment_root": str(ex),
        "run_checkpoint_dir": str(ck / "somega" / "final"),
        "run_experiment_dir": str(ex / "somega" / "final_refit"),
        "final_epochs_rule": FINAL_EPOCH_RULE,
        "final_epochs_resolved": final_epochs,
        "early_stopping": False,
        "decision_threshold": DECISION_THRESHOLD,
    }


def parity_fingerprint() -> dict:
    """Deterministic scientific-config fingerprint for seed-42 parity testing.

    Output roots and seed-specific data paths are EXCLUDED (expected to differ).
    """
    return {
        "component": "S_omega",
        "architecture": "BARRPostSafetyV1",
        "param_count": PARAM_COUNT,
        "feature_dim": FEATURE_DIM,
        "numeric_idx": NUMERIC_IDX,
        "onehot_idx": ONEHOT_IDX,
        "hidden": list(HIDDEN),
        "loss": LOSS,
        "optimizer": {"name": "AdamW", "lr": LR, "weight_decay": WEIGHT_DECAY},
        "scheduler": {"name": SCHEDULER},
        "batch_size": BATCH_SIZE,
        "max_epochs": MAX_EPOCHS,
        "patience": PATIENCE,
        "improvement_eps": IMPROVEMENT_EPS,
        "checkpoint_rule": CHECKPOINT_RULE,
        "decision_threshold": DECISION_THRESHOLD,
        "fold_seed_rule": "1000*s + 12000 + k",
        "final_refit_seed_rule": "s",
        "final_epoch_rule": FINAL_EPOCH_RULE,
        "n_folds": N_FOLDS,
        "normalization": {"fit_only": True, "ddof": 0,
                          "numeric_idx": NUMERIC_IDX,
                          "binary_flags_unchanged": True},
    }


def seed_bind_before_rng() -> dict:
    import numpy as np
    import torch

    events = []
    orig = random.seed

    def traced(value=None, version=2):
        events.append({"event": "SEED_BIND", "value": value})
        return orig(value, version)

    random.seed = traced  # type: ignore[assignment]
    try:
        s = 3407
        random.seed(s)
        np.random.seed(s)
        torch.manual_seed(s)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(s)
        _ = random.random()
        events.append({"event": "FIRST_RNG_DRAW", "kind": "random.random"})
    finally:
        random.seed = orig  # type: ignore[assignment]

    b = next((i for i, e in enumerate(events) if e["event"] == "SEED_BIND"), None)
    d = next((i for i, e in enumerate(events) if e["event"] == "FIRST_RNG_DRAW"), None)
    return {"component": "S_omega",
            "seed_bound_before_first_rng_draw": b is not None and d is not None and b < d,
            "events": events}


def resolve_runtime_constants(master_seed: int) -> dict:
    """Compute the in-memory constant overlay for the canonical module.

    Returned as data only — nothing is imported or executed in Phase B.
    """
    dck, dex = seed_roots(master_seed)
    return {
        "CV_SEEDS": {k: safety_fold_seed(master_seed, k) for k in range(N_FOLDS)},
        "FINAL_SEED": final_refit_seed(master_seed),
        "CKPT_ROOT": str(dck / "somega"),
        "EXP_ROOT": str(dex / "somega"),
        "FEATURES_NPY": str(features_path_for_seed(master_seed)),
        "TARGETS_CSV": str(targets_path_for_seed(master_seed)),
    }


def _load_canonical_module(master_seed: int):
    """Import ``phase25f_execution_common`` and overlay the Phase29 constants.

    The canonical module computes its constants at import time but its
    FUNCTIONS read them from module globals at call time, so an in-memory
    attribute overlay is effective and the historical source stays untouched.

    Returns the module with CV_SEEDS / FINAL_SEED / CKPT_ROOT / EXP_ROOT /
    FEATURES_NPY / TARGETS_CSV rebound for ``master_seed``.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "phase29_canonical_phase25f_common", str(CANONICAL_MODULE))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    dck, dex = seed_roots(master_seed)
    mod.CV_SEEDS = {k: safety_fold_seed(master_seed, k) for k in range(N_FOLDS)}
    mod.FINAL_SEED = final_refit_seed(master_seed)
    mod.CKPT_ROOT = dck / "somega"
    mod.EXP_ROOT = dex / "somega"
    mod.FEATURES_NPY = features_path_for_seed(master_seed)
    mod.TARGETS_CSV = targets_path_for_seed(master_seed)
    return mod


def run_fold(master_seed: int, k: int) -> dict:
    """Train ONE S_omega CV fold under the Phase29 seed contract.

    Reuses the canonical ``train_logical_run`` verbatim (FIT-only normalization,
    BCEWithLogits + AdamW + ReduceLROnPlateau, EARLY_STOP-min checkpoint rule),
    with only the seed and the feature/target source rebound.
    """
    import numpy as np
    import torch

    mod = _load_canonical_module(master_seed)
    feats = np.load(mod.FEATURES_NPY).astype(np.float32)
    meta = mod.load_metadata()
    targ = mod.load_targets()
    members = mod.load_fold_members()

    sid_to_row = {r["sample_id"]: int(r["feature_row_index"]) for r in meta}
    y_by_id = {r["sample_id"]: float(r["safety_target"]) for r in targ}

    fit_ids = members[k]["fit"]
    es_ids = members[k]["early_stop"]
    ot_ids = members[k]["outer_target"]
    fit_idx = [sid_to_row[s] for s in fit_ids]
    es_idx = [sid_to_row[s] for s in es_ids]
    ot_idx = [sid_to_row[s] for s in ot_ids]

    fit_raw, es_raw, ot_raw = feats[fit_idx], feats[es_idx], feats[ot_idx]
    mu, sigma, const = mod.fit_normalization(fit_raw)
    fit_X = mod.apply_normalization(fit_raw, mu, sigma, const)
    es_X = mod.apply_normalization(es_raw, mu, sigma, const)
    ot_X = mod.apply_normalization(ot_raw, mu, sigma, const)
    fit_y = np.array([y_by_id[s] for s in fit_ids], dtype=np.float32)
    es_y = np.array([y_by_id[s] for s in es_ids], dtype=np.float32)

    names = [r["name"] for r in mod.read_csv_rows(mod.FEATURE_SCHEMA_CSV)]
    stats_path = (ROOT / "reports" / "tables"
                  / f"phase29_seed{master_seed}_somega_fold{k}_normalization_stats.csv")
    mod.write_csv(stats_path, ["feature_index", "name", "mu", "sigma", "is_constant"],
                  [[i, names[i], repr(float(mu[i])), repr(float(sigma[i])), bool(const[i])]
                   for i in range(16)])

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    run_id = f"phase29_seed{master_seed}_somega_cv_fold{k}"
    ckpt_dir = mod.CKPT_ROOT / f"cv_fold{k}"
    exp_dir = mod.EXP_ROOT / f"cv_fold{k}"
    closure = mod.train_logical_run(
        run_id=run_id, ckpt_dir=ckpt_dir, exp_dir=exp_dir,
        seed=mod.CV_SEEDS[k], fit_X=fit_X, fit_y=fit_y,
        es_X=es_X, es_y=es_y, device=device, verbose=True)

    model = mod.load_best_model(ckpt_dir / "best.pt", device)
    logit = mod.predict_logits(model, ot_X, device)
    p = 1.0 / (1.0 + np.exp(-logit.astype(np.float64)))
    rows = []
    meta_by_id = {r["sample_id"]: r for r in meta}
    dd_by_id = {r["sample_id"]: float(r["delta_dice"]) for r in targ}
    for j, sid in enumerate(ot_ids):
        m = meta_by_id[sid]
        dec = ("ACCEPT_REFINEMENT" if logit[j] >= mod.SOMEGA_ACCEPT_LOGIT_THRESHOLD
               else "FALLBACK_GLOBAL")
        rows.append([sid, sid_to_row[sid], m["domain"], m["task_id"], k,
                     repr(float(dd_by_id[sid])), repr(float(y_by_id[sid])),
                     repr(float(logit[j])), repr(float(p[j])), dec])
    mod.write_csv(exp_dir / "oof_predictions.csv",
                  ["sample_id", "feature_row_index", "domain", "task_id",
                   "safety_cv_fold", "delta_dice", "safety_target",
                   "safety_logit_oof", "p_accept_oof", "safety_decision_oof"], rows)

    return {
        "run_id": run_id, "seed": mod.CV_SEEDS[k],
        "best_epoch": closure["best_epoch"],
        "best_monitor_bce": closure["best_monitor_bce"],
        "termination": closure["termination"],
        "total_epochs": closure["total_epochs"],
        "n_fit": len(fit_ids), "n_early_stop": len(es_ids),
        "n_outer_target": len(ot_ids),
        "mu": mu.tolist(), "sigma": sigma.tolist(), "const": const.tolist(),
        "normalization_stats_sha256": sha_file(stats_path),
        "best_checkpoint_sha256": closure["best_checkpoint_sha256"],
        "state_checkpoint_sha256": closure["state_checkpoint_sha256"],
        "history_sha256": closure["history_sha256"],
        "oof_predictions_sha256": sha_file(exp_dir / "oof_predictions.csv"),
        "checkpoint_dir": str(ckpt_dir), "experiment_dir": str(exp_dir),
    }


def run_final(master_seed: int, final_epochs: int) -> dict:
    """Train the all-DEV S_omega final refit using the integer-median rule."""
    import numpy as np
    import torch

    mod = _load_canonical_module(master_seed)
    feats = np.load(mod.FEATURES_NPY).astype(np.float32)
    meta = mod.load_metadata()
    targ = mod.load_targets()
    sid_to_row = {r["sample_id"]: int(r["feature_row_index"]) for r in meta}
    y_by_id = {r["sample_id"]: float(r["safety_target"]) for r in targ}

    all_ids = [r["sample_id"] for r in meta]
    all_idx = [sid_to_row[s] for s in all_ids]
    raw_all = feats[all_idx]
    mu, sigma, const = mod.fit_normalization(raw_all)
    final_X = mod.apply_normalization(raw_all, mu, sigma, const)
    final_y = np.array([y_by_id[s] for s in all_ids], dtype=np.float32)

    names = [r["name"] for r in mod.read_csv_rows(mod.FEATURE_SCHEMA_CSV)]
    stats_path = (ROOT / "reports" / "tables"
                  / f"phase29_seed{master_seed}_somega_final_normalization_stats.csv")
    mod.write_csv(stats_path, ["feature_index", "name", "mu", "sigma", "is_constant"],
                  [[i, names[i], repr(float(mu[i])), repr(float(sigma[i])), bool(const[i])]
                   for i in range(16)])

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    final_dir = mod.CKPT_ROOT / "final"
    exp_dir = mod.EXP_ROOT / "final"
    closure = mod.train_logical_run(
        run_id=f"phase29_seed{master_seed}_somega_final",
        ckpt_dir=final_dir, exp_dir=exp_dir, seed=mod.FINAL_SEED,
        fit_X=final_X, fit_y=final_y, es_X=final_X[:1], es_y=final_y[:1],
        device=device, use_early_stop=False, force_epochs=final_epochs, verbose=True)

    state = torch.load(final_dir / "state.pt", map_location="cpu", weights_only=False)
    final_ckpt = {
        "model_state": state["model_state"], "epoch": state["epoch"],
        "seed": mod.FINAL_SEED, "final_safety_epochs": final_epochs,
        "normalizer_mu": [float(x) for x in mu],
        "normalizer_sigma": [float(x) for x in sigma],
        "normalizer_constant_mask": [bool(x) for x in const],
    }
    atomic_save(final_ckpt, final_dir / "final.pt")
    return {
        "run_id": closure["run_id"], "seed": mod.FINAL_SEED,
        "final_epochs": final_epochs, "termination": closure["termination"],
        "total_epochs": closure["total_epochs"],
        "final_checkpoint_sha256": sha_file(final_dir / "final.pt"),
        "history_sha256": closure["history_sha256"],
        "normalization_stats_sha256": sha_file(stats_path),
        "checkpoint_dir": str(final_dir), "experiment_dir": str(exp_dir),
    }


def sha_file(p) -> str:
    import hashlib
    p = Path(p)
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_save(obj, path) -> None:
    import os
    path = Path(path)
    tmp = str(path) + ".tmp"
    import torch
    torch.save(obj, tmp)
    os.replace(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase29 S_omega additive wrapper")
    ap.add_argument("--master-seed", type=int, required=True,
                    choices=list(VALID_SEEDS))
    ap.add_argument("--fold", type=int, choices=list(range(N_FOLDS)), default=None)
    ap.add_argument("--final-refit", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--spec-only", action="store_true")
    ap.add_argument("--fingerprint", action="store_true")
    ap.add_argument("--constants", action="store_true")
    args = ap.parse_args()

    if args.fingerprint:
        print(json.dumps(parity_fingerprint(), indent=1))
        return 0
    if args.constants:
        print(json.dumps(resolve_runtime_constants(args.master_seed), indent=1))
        return 0

    if (args.fold is None) == (not args.final_refit):
        raise SystemExit("pass exactly one of --fold {0..4} or --final-refit")

    if args.spec_only or args.dry_run:
        spec = (build_final_spec(args.master_seed) if args.final_refit
                else build_fold_spec(args.master_seed, args.fold))
        print(json.dumps(spec, indent=1))
        return 0

    if args.final_refit:
        raise SystemExit("final refit requires the median rule; "
                         "use run_final(master_seed, final_epochs)")
    out = run_fold(args.master_seed, args.fold)
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
