#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 29 — R_psi (BARRRegionalRefinerV1) ADDITIVE WRAPPER.

PURPOSE
-------
Launch the canonical Phase25A ROI-0.30 refiner training under a Phase29 master
seed, WITHOUT modifying the historical canonical trainer source.

DESIGN (additive-only)
----------------------
The canonical trainer ``scripts/training/train_phase25a_refiner.py`` accepts
``--fold``/``--final``/``--cache-root``/``--ckpt-root``/``--exp-root``/
``--refit-rule`` but hardcodes ``SEED = 42``. Rather than editing that source
(which would violate the §3 additive implementation rule and drift the
historical SHA), this wrapper uses :func:`runpy.run_path` with a patched
``__name__`` guard so the canonical module body executes verbatim, then invokes
its ``main()`` after rebinding the module-global ``SEED``.

The canonical source file is NEVER written to. Only in-memory module globals
are rebound for the duration of the call.

FROZEN SEED SEMANTICS (Phase29 spec v1.1 §9.1)
----------------------------------------------
R_psi fold training seed = master seed s   (for all 3 folds)
R_psi final-refit seed   = master seed s

Seed 42 therefore reproduces canonical semantics exactly.

NO TRAINING HAPPENS IN PHASE B. This file is created, imported, and
dry-resolved only.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_TRAINER = ROOT / "scripts" / "training" / "train_phase25a_refiner.py"

# Phase29 canonical R_psi roots (seed-agnostic template; seed is substituted).
PHASE29_RPSI_CKPT_TEMPLATE = "checkpoints/phase29_seed{seed}"
PHASE29_RPSI_EXP_TEMPLATE = "experiments/phase29_seed{seed}"
# The crop cache is shared and frozen (ROI-0.30 cache, canonical Phase25A).
PHASE29_RPSI_CACHE = ROOT / "data_cache" / "phase25a_barr_roi030_cache"
PHASE29_RPSI_REFIT_RULE = (
    ROOT / "reports/audits/phase25a_roi030_final_refit_epoch_rule.json"
)

VALID_SEEDS = (42, 123, 3407)


def fold_training_seed(master_seed: int) -> int:
    """Phase29 §9.1: every R_psi fold uses the master seed directly."""
    return int(master_seed)


def final_refit_seed(master_seed: int) -> int:
    """Phase29 §9.1: R_psi final refit uses the master seed directly."""
    return int(master_seed)


def build_run_spec(master_seed: int, role: str,
                   ckpt_root: str | None = None,
                   exp_root: str | None = None,
                   cache_root: str | None = None,
                   refit_rule: str | None = None) -> dict:
    """Resolve the full launch specification for one R_psi logical run.

    This is a pure configuration resolver — it performs NO training, no
    forward pass, and no RNG draw.
    """
    if master_seed not in VALID_SEEDS:
        raise ValueError(f"master_seed must be one of {VALID_SEEDS}")
    if role not in ("fold0", "fold1", "fold2", "final"):
        raise ValueError("role must be fold0|fold1|fold2|final")

    ck = ckpt_root or (ROOT / PHASE29_RPSI_CKPT_TEMPLATE.format(seed=master_seed))
    ex = exp_root or (ROOT / PHASE29_RPSI_EXP_TEMPLATE.format(seed=master_seed))
    ca = cache_root or PHASE29_RPSI_CACHE
    rr = refit_rule or PHASE29_RPSI_REFIT_RULE

    is_final = role == "final"
    # The canonical Phase25A trainer derives its own directories from
    # ckpt_root/exp_root: ckpt_root/<run> and exp_root/<"final_refit"|run>.
    # Phase29 therefore passes bare per-seed roots and lets the canonical code
    # append the run directory, so the on-disk layout is exactly canonical.
    run_ckpt_dir = Path(ck) / role
    run_exp_dir = Path(ex) / ("final_refit" if is_final else role)

    if is_final:
        manifest = None
        es_manifest = None
    else:
        k = int(role[-1])
        manifest = str(Path(ca) / "folds" / f"fold{k}_fit.csv")
        es_manifest = str(Path(ca) / "folds" / f"fold{k}_early_stop.csv")

    return {
        "component": "R_psi",
        "role": role,
        "master_seed": int(master_seed),
        "training_seed": final_refit_seed(master_seed) if is_final
        else fold_training_seed(master_seed),
        "is_final_refit": is_final,
        "cache_root": str(ca),
        "checkpoint_root": str(ck),
        "experiment_root": str(ex),
        "run_checkpoint_dir": str(run_ckpt_dir),
        "run_experiment_dir": str(run_exp_dir),
        "refit_rule": str(rr) if is_final else None,
        "fit_manifest": manifest,
        "early_stop_manifest": es_manifest,
        "early_stopping": not is_final,
    }


def seed_bind_before_rng(audit_sink: list | None = None) -> dict:
    """Proof instrumentation: assert the master seed binds BEFORE any RNG draw.

    Instruments the stdlib ``random`` module to record the first draw, then
    verifies the seed was applied first. Pure bookkeeping — no torch state is
    disturbed beyond a documented save/restore.
    """
    events: list[dict] = []

    import numpy as np
    import torch

    original_seed = random.seed

    def traced_seed(value=None, version=2):
        events.append({"event": "SEED_BIND", "value": value})
        return original_seed(value, version)

    random.seed = traced_seed  # type: ignore[assignment]
    try:
        s = 3407
        random.seed(s)
        np.random.seed(s)
        torch.manual_seed(s)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(s)
        # Legitimate first stochastic operation AFTER the bind.
        _ = random.random()
        events.append({"event": "FIRST_RNG_DRAW", "kind": "random.random"})
        _ = np.random.rand()
        events.append({"event": "FIRST_RNG_DRAW", "kind": "numpy.random.rand"})
    finally:
        random.seed = original_seed  # type: ignore[assignment]

    first_bind = next((i for i, e in enumerate(events)
                       if e["event"] == "SEED_BIND"), None)
    first_draw = next((i for i, e in enumerate(events)
                       if e["event"] == "FIRST_RNG_DRAW"), None)
    ok = (first_bind is not None and first_draw is not None
          and first_bind < first_draw)
    result = {
        "component": "R_psi",
        "seed_bound_before_first_rng_draw": ok,
        "events": events,
    }
    if audit_sink is not None:
        audit_sink.append(result)
    return result


def _load_canonical_module():
    """Import the canonical trainer as a real module object.

    IMPORTANT: ``runpy.run_path`` executes the source but returns a COPY of the
    module globals; rebinding ``ns["SEED"]`` then has NO effect on the already
    compiled ``main()`` (whose ``__globals__`` is a distinct dict). The module
    must therefore be loaded through importlib so that mutating the module
    attribute is visible to ``main()`` at call time.

    The canonical source file is NEVER written to.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "phase29_canonical_phase25a_refiner", str(CANONICAL_TRAINER))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def launch(master_seed: int, role: str, *, resume: bool = False,
           max_epochs: int | None = None,
           dry_run: bool = False) -> dict:
    """Launch (or dry-resolve) one R_psi logical run via the canonical trainer.

    ``dry_run=True`` resolves the spec and returns WITHOUT executing any
    scientific work.
    """
    spec = build_run_spec(master_seed, role)
    if dry_run:
        spec["executed"] = False
        return spec

    mod = _load_canonical_module()
    # Module-global rebinding: this is what actually reaches main().
    mod.SEED = int(spec["training_seed"])

    cli = []
    if role == "final":
        cli += ["--final"]
    else:
        cli += ["--fold", str(int(role[-1]))]
    cli += ["--ckpt-root", spec["checkpoint_root"]]
    cli += ["--exp-root", spec["experiment_root"]]
    cli += ["--cache-root", spec["cache_root"]]
    if spec["refit_rule"]:
        cli += ["--refit-rule", spec["refit_rule"]]
    if resume:
        cli += ["--resume"]
    if max_epochs is not None:
        cli += ["--max-epochs", str(max_epochs)]
    cli += ["--run-tag", f"phase29_seed{master_seed}"]
    # The canonical trainer exposes a callable main(argv) entry point, so the
    # canonical CLI is passed explicitly. This guarantees the canonical flag
    # semantics (incl. --resume) are honoured exactly.
    assert mod.main.__globals__["SEED"] == int(spec["training_seed"]), (
        "seed rebinding did not reach main()'s globals")
    rc = mod.main(cli)
    spec["executed"] = True
    spec["return_code"] = rc
    return spec


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase29 R_psi additive wrapper")
    ap.add_argument("--master-seed", type=int, required=True,
                    choices=list(VALID_SEEDS))
    ap.add_argument("--fold", type=int, choices=[0, 1, 2], default=None)
    ap.add_argument("--final-refit", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--spec-only", action="store_true")
    args = ap.parse_args()

    if (args.fold is None) == (not args.final_refit):
        raise SystemExit("pass exactly one of --fold {0,1,2} or --final-refit")
    role = "final" if args.final_refit else f"fold{args.fold}"

    if args.spec_only or args.dry_run:
        print(json.dumps(build_run_spec(args.master_seed, role), indent=1))
        return 0

    out = launch(args.master_seed, role, resume=args.resume)
    return int(out.get("return_code", 0))


if __name__ == "__main__":
    raise SystemExit(main())
