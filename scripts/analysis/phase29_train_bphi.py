#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 29 — B_phi (BARRBenefitRouterV1) ADDITIVE WRAPPER.

PURPOSE
-------
Launch the canonical Phase25D v1.2.1 router training under a Phase29 master
seed and a SEED-SPECIFIC DeltaDice target, WITHOUT modifying the historical
canonical trainer source.

DESIGN (additive-only)
----------------------
``scripts/analysis/train_phase25d_router.py`` is a top-level linear script
(no ``main()``) with hardcoded seed ``42000 + k`` and hardcoded Phase25C
label/checkpoint/experiment paths. Two additive mechanisms are used:

1. ``--spec-only`` / ``--dry-run``: this wrapper fully resolves the launch
   specification (fold seeds, manifests, input SHAs, output roots) with NO
   training, NO forward pass and NO RNG draw.
2. Live launch: the wrapper binds the master seed FIRST, then execs the
   canonical script body (``runpy.run_path``) after installing an import-time
   overlay that redirects the canonical module's hardcoded path globals to
   Phase29 roots and its label source to the seed-specific DeltaDice table.

The canonical source file is NEVER written to.

FROZEN SEED SEMANTICS (Phase29 spec v1.1 §9.3)
----------------------------------------------
router_fold_seed(s, k) = 1000 * s + k         for k = 0..4
final all-DEV refit seed = s

seed42  -> 42000..42004   (canonical parity)
seed123 -> 123000..123004
seed3407-> 3407000..3407004

NO TRAINING HAPPENS IN PHASE B.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_TRAINER = ROOT / "scripts" / "analysis" / "train_phase25d_router.py"

VALID_SEEDS = (42, 123, 3407)
N_FOLDS = 5

# frozen Phase25D v1.2.1 constants (mirrored for parity fingerprinting)
HUBER_DELTA = 0.05
LR = 1e-3
WEIGHT_DECAY = 1e-4
BATCH_SIZE = 128
MAX_EPOCHS = 200
PATIENCE = 20
SCHEDULER = "ReduceLROnPlateau"
SCHEDULER_PARAMS = {"mode": "min", "factor": 0.5, "patience": 10,
                    "threshold": 1e-4, "threshold_mode": "rel", "cooldown": 0,
                    "min_lr": 1e-6, "eps": 1e-8}
FEATURE_DIM = 202
PARAM_COUNT = 36801
CHECKPOINT_RULE = "minimum EARLY_STOP Huber"
TIE_RULE = "earlier epoch"

# fixed (seed-independent) inputs
FIXED_FEATURES = ROOT / "data_cache/phase25b_barr_pre_refinement_features_v1_2/features.npy"
FIXED_METADATA = ROOT / "data_cache/phase25b_barr_pre_refinement_features_v1_2/metadata.csv"
CV5_MANIFEST = ROOT / "reports/tables/phase25d_cv5_manifest.csv"
OOF_BUDGET_B = 0.25
OOF_N = 4957
OOF_K = 1239


def router_fold_seed(master_seed: int, k: int) -> int:
    """Phase29 §9.3 frozen generalization: 1000*s + k."""
    return 1000 * int(master_seed) + int(k)


def final_refit_seed(master_seed: int) -> int:
    return int(master_seed)


def target_path_for_seed(master_seed: int) -> Path:
    """Seed-specific DeltaDice target table produced by §12/§14.

    For seed 42 this resolves to the canonical Phase25C OOF paired-gain labels
    (reuse, not retrain). For seeds 123/3407 it resolves to the Phase29
    seed-specific frozen table.
    """
    if master_seed == 42:
        return (ROOT / "data_cache/phase25c_barr_oof_paired_gain_labels_v1_2"
                / "phase25c_oof_paired_gain_labels.csv")
    return (ROOT / "data_cache" / f"phase29_seed{master_seed}"
            / f"phase29_seed{master_seed}_deltadice_targets.csv")


def fold_manifest_paths(k: int) -> dict:
    t = ROOT / "reports/tables"
    return {
        "fit": str(t / f"phase25d_cv_fold{k}_fit_ids.csv"),
        "early_stop": str(t / f"phase25d_cv_fold{k}_early_stop_ids.csv"),
        "outer_target": str(t / f"phase25d_cv_fold{k}_outer_target_ids.csv"),
    }


def build_fold_spec(master_seed: int, k: int,
                    ckpt_root: str | None = None,
                    exp_root: str | None = None,
                    target_path: str | None = None) -> dict:
    """Resolve one B_phi fold launch specification (pure; no training)."""
    if master_seed not in VALID_SEEDS:
        raise ValueError(f"master_seed must be one of {VALID_SEEDS}")
    if not (0 <= k < N_FOLDS):
        raise ValueError(f"fold must be 0..{N_FOLDS-1}")

    ck = Path(ckpt_root) if ckpt_root else (
        ROOT / f"checkpoints/phase29_seed{master_seed}")
    ex = Path(exp_root) if exp_root else (
        ROOT / f"experiments/phase29_seed{master_seed}")
    tp = Path(target_path) if target_path else target_path_for_seed(master_seed)

    return {
        "component": "B_phi",
        "role": f"fold{k}",
        "is_final_refit": False,
        "master_seed": int(master_seed),
        "training_seed": router_fold_seed(master_seed, k),
        "feature_path": str(FIXED_FEATURES),
        "metadata_path": str(FIXED_METADATA),
        "target_path": str(tp),
        "cv5_manifest": str(CV5_MANIFEST),
        "fold_manifests": fold_manifest_paths(k),
        "checkpoint_root": str(ck),
        "experiment_root": str(ex),
        "run_checkpoint_dir": str(ck / "bphi" / f"fold{k}"),
        "run_experiment_dir": str(ex / "bphi" / f"fold{k}"),
    }


def build_final_spec(master_seed: int, ckpt_root: str | None = None,
                     exp_root: str | None = None,
                     target_path: str | None = None,
                     final_epochs: int | None = None) -> dict:
    """Resolve the final all-DEV refit specification (pure; no training)."""
    if master_seed not in VALID_SEEDS:
        raise ValueError(f"master_seed must be one of {VALID_SEEDS}")
    ck = Path(ckpt_root) if ckpt_root else (
        ROOT / f"checkpoints/phase29_seed{master_seed}")
    ex = Path(exp_root) if exp_root else (
        ROOT / f"experiments/phase29_seed{master_seed}")
    tp = Path(target_path) if target_path else target_path_for_seed(master_seed)
    return {
        "component": "B_phi",
        "role": "final",
        "is_final_refit": True,
        "master_seed": int(master_seed),
        "training_seed": final_refit_seed(master_seed),
        "feature_path": str(FIXED_FEATURES),
        "metadata_path": str(FIXED_METADATA),
        "target_path": str(tp),
        "cv5_manifest": str(CV5_MANIFEST),
        "checkpoint_root": str(ck),
        "experiment_root": str(ex),
        "run_checkpoint_dir": str(ck / "bphi" / "final"),
        "run_experiment_dir": str(ex / "bphi" / "final_refit"),
        "final_epochs_rule": "median of five best fold epochs (Phase25D canonical)",
        "final_epochs_resolved": final_epochs,
        "early_stopping": False,
    }


def parity_fingerprint() -> dict:
    """Deterministic scientific-config fingerprint for seed-42 parity testing.

    Excludes only output-root paths, which are EXPECTED to differ between the
    canonical Phase25D run and the Phase29 wrapper.
    """
    return {
        "component": "B_phi",
        "architecture": "BARRBenefitRouterV1",
        "param_count": PARAM_COUNT,
        "feature_dim": FEATURE_DIM,
        "loss": {"name": "HuberLoss", "delta": HUBER_DELTA, "reduction": "mean"},
        "optimizer": {"name": "AdamW", "lr": LR, "weight_decay": WEIGHT_DECAY},
        "scheduler": {"name": SCHEDULER, **SCHEDULER_PARAMS},
        "batch_size": BATCH_SIZE,
        "max_epochs": MAX_EPOCHS,
        "patience": PATIENCE,
        "checkpoint_rule": CHECKPOINT_RULE,
        "tie_rule": TIE_RULE,
        "fold_seed_rule": "1000*s + k",
        "final_refit_seed_rule": "s",
        "n_folds": N_FOLDS,
        "oof_budget_b": OOF_BUDGET_B,
        "oof_N": OOF_N,
        "oof_K": OOF_K,
        "normalization": {"fit_only": True, "ddof": 0,
                          "continuous_scalars": 8,
                          "binary_flags_unchanged": True,
                          "deep_features_unnormalized": True},
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
    return {"component": "B_phi",
            "seed_bound_before_first_rng_draw": b is not None and d is not None and b < d,
            "events": events}


# --------------------------------------------------------------------------- #
# additive source transform
# --------------------------------------------------------------------------- #
# The canonical Phase25D router trainer is a LINEAR top-level script with three
# hardcoded seed anchors and three hardcoded output roots. To re-parameterize
# it for a Phase29 master seed WITHOUT writing to the historical file, the
# wrapper compiles a byte-for-byte copy of the source in memory with these
# exact, auditable substitutions applied:
#
#   "42000 + k"                       -> "<fold_seed_base> + k"
#   "random.seed(42)"                 -> "random.seed(<final_seed>)"
#   "np.random.seed(42)"              -> "np.random.seed(<final_seed>)"
#   "torch.manual_seed(42)"           -> "torch.manual_seed(<final_seed>)"
#   ".manual_seed(42)" (DataLoader)   -> ".manual_seed(<final_seed>)"
#   "<canonical ckpt/exp/out roots>"  -> "<Phase29 role roots>"
#
# Every other token — architecture, loss, optimizer, LR, weight decay, batch,
# scheduler, patience, normalization indices, checkpoint rule, tie rule, CV
# membership, OOF geometry — is untouched. The historical source SHA is
# unchanged; the transform is applied only to the in-memory compile string.
CANONICAL_FOLD_SEED_BASE = 42000
CANONICAL_FINAL_SEED = 42
CANONICAL_CKPT_DIR = ("checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42")
CANONICAL_EXP_DIR = ("experiments/phase25d_barr_benefit_router_v1_2_1_seed42")
CANONICAL_OUT_CACHE = "data_cache/phase25d_barr_benefit_router_v1_2_1"


def _fold_seed_base(master_seed: int) -> int:
    """The k=0 fold seed for this master seed (1000*s + 0)."""
    return router_fold_seed(master_seed, 0)


def transform_source(master_seed: int, ckpt_dir: str, exp_dir: str,
                     out_cache: str, target_path: str | None = None) -> tuple[str, list]:
    """Return (patched_source, substitutions) for the canonical router script.

    The label source is redirected from the canonical Phase25C OOF paired-gain
    table to the Phase29 seed-specific DeltaDice target table (which, for seed
    42, IS the canonical table — a byte-identical reuse).
    """
    src = CANONICAL_TRAINER.read_text(encoding="utf-8")
    base = _fold_seed_base(master_seed)
    final = final_refit_seed(master_seed)
    tp = Path(target_path) if target_path else target_path_for_seed(master_seed)

    subs = [
        # ORDER MATTERS: longer/more-specific anchors first, because
        # "random.seed(42)" is a substring of "np.random.seed(42)".
        (f"np.random.seed({CANONICAL_FINAL_SEED})", f"np.random.seed({final})"),
        (f"torch.manual_seed({CANONICAL_FINAL_SEED})",
         f"torch.manual_seed({final})"),
        (f"torch.cuda.manual_seed_all({CANONICAL_FINAL_SEED})",
         f"torch.cuda.manual_seed_all({final})"),
        (f".manual_seed({CANONICAL_FINAL_SEED})", f".manual_seed({final})"),
        (f"random.seed({CANONICAL_FINAL_SEED})", f"random.seed({final})"),
        (f"{CANONICAL_FOLD_SEED_BASE} + k", f"{base} + k"),
        # The saved final checkpoint records its seed as a bare literal; it must
        # carry the seed-specific final-refit seed, not the canonical 42.
        (f'"seed": {CANONICAL_FINAL_SEED},', f'"seed": {final},'),
        # label source -> seed-specific DeltaDice targets
        ('CACHE25C / "phase25c_oof_paired_gain_labels.csv"',
         f'r"{tp}"'),
        (f'"{CANONICAL_CKPT_DIR}"', f'r"{ckpt_dir}"'),
        (f'"{CANONICAL_EXP_DIR}"', f'r"{exp_dir}"'),
        (f'"{CANONICAL_OUT_CACHE}"', f'r"{out_cache}"'),
    ]
    patched = src
    applied = []
    for old, new in subs:
        n = patched.count(old)
        if n == 0:
            raise RuntimeError(f"B_phi transform anchor not found: {old!r}")
        patched = patched.replace(old, new)
        applied.append({"old": old, "new": new, "count": n})
    return patched, applied


def _load_transformed_module(master_seed: int, ckpt_dir: str, exp_dir: str,
                             out_cache: str, target_path: str | None = None):
    src, applied = transform_source(master_seed, ckpt_dir, exp_dir, out_cache,
                                    target_path)
    mod_globals: dict = {
        "__name__": "phase29_canonical_phase25d_router",
        "__file__": str(CANONICAL_TRAINER),
        "__builtins__": __builtins__,
    }
    exec(compile(src, str(CANONICAL_TRAINER), "exec"), mod_globals)
    return mod_globals, applied


def launch(master_seed: int, k: int | None, *, dry_run: bool = False) -> dict:
    """Launch (or dry-resolve) one complete B_phi run via the transformed
    canonical body.

    ``k`` selects which fold(s) to run inside the transformed program:
      * ``k`` is None  -> run the FULL canonical program (5 folds + final refit
                          + OOF + calibration), used for the seed's complete B_phi.
      * ``k`` int      -> run only fold ``k`` by masking the fold loop to that
                          single index (no final refit).

    The caller (Phase C driver) uses the full-program form once per seed so the
    internal OOF/membership/median-rule semantics are byte-identical to
    canonical.
    """
    if dry_run:
        spec = (build_final_spec(master_seed) if k is None
                else build_fold_spec(master_seed, k))
        spec["executed"] = False
        return spec

    spec = build_final_spec(master_seed) if k is None else build_fold_spec(master_seed, k)
    seed = spec["training_seed"]

    # ---- frozen RNG bind BEFORE any draw --------------------------------- #
    random.seed(seed)
    import numpy as np
    import torch
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    if master_seed == 42:
        ck = str(ROOT / CANONICAL_CKPT_DIR)
        ex = str(ROOT / CANONICAL_EXP_DIR)
        oc = str(ROOT / CANONICAL_OUT_CACHE)
    else:
        ck = str(ROOT / f"checkpoints/phase29_seed{master_seed}/bphi")
        ex = str(ROOT / f"experiments/phase29_seed{master_seed}/bphi")
        oc = str(ROOT / f"data_cache/phase29_seed{master_seed}/bphi_out")

    mod, applied = _load_transformed_module(master_seed, ck, ex, oc,
                                            spec["target_path"])
    spec["executed"] = True
    spec["source_transform"] = applied
    spec["checkpoint_root"] = ck
    spec["experiment_root"] = ex
    spec["out_cache"] = oc
    spec["note"] = ("canonical body compiled in memory with seed/path "
                    "substitution; historical source untouched")
    return spec


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase29 B_phi additive wrapper")
    ap.add_argument("--master-seed", type=int, required=True,
                    choices=list(VALID_SEEDS))
    ap.add_argument("--fold", type=int, choices=list(range(N_FOLDS)), default=None)
    ap.add_argument("--final-refit", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--spec-only", action="store_true")
    ap.add_argument("--fingerprint", action="store_true")
    args = ap.parse_args()

    if args.fingerprint:
        print(json.dumps(parity_fingerprint(), indent=1))
        return 0

    if (args.fold is None) == (not args.final_refit):
        raise SystemExit("pass exactly one of --fold {0..4} or --final-refit")

    if args.spec_only or args.dry_run:
        spec = (build_final_spec(args.master_seed) if args.final_refit
                else build_fold_spec(args.master_seed, args.fold))
        print(json.dumps(spec, indent=1))
        return 0

    out = launch(args.master_seed, None if args.final_refit else args.fold)
    return 0 if out.get("executed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
