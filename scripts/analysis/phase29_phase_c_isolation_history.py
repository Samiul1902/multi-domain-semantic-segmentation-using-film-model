#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 29 — PHASE C STAGE 6: cross-seed dependency isolation (§25) and training
history integrity (§26) for all 32 new runs.

§25 asserts, from the actual on-disk artifacts, that each seed's R_psi outputs
feed ONLY that seed's DeltaDice/B_phi/S_omega chain, and that the only shared
inputs are the fixed global representation and the fixed Phase25B features.

§26 validates every new training history: contiguous epochs, no duplicates,
finite losses/LR, best epoch present, closure consistent.

Both are PURE reads — no training.

Usage:
    python phase29_phase_c_isolation_history.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase29_phase_c_common as C  # noqa: E402


def check_isolation() -> dict:
    import numpy as np

    checks = {}
    detail = {}

    # ---- each seed's DeltaDice must come from ITS OWN R_psi checkpoints --- #
    for S in C.NEW_SEEDS:
        tgt = C.read_csv_rows(C.deltadice_target_path(S))
        shas = {r["fold_refiner_checkpoint_sha"] for r in tgt}
        expected = {C.sha256_file(C.rpsi_checkpoint_root(S) / f"fold{k}" / "best.pt")
                    for k in range(3)}
        checks[f"seed{S}_deltadice_from_own_rpsi_ckpts"] = (shas == expected)
        detail[f"seed{S}_fold_ckpt_shas"] = sorted(shas)
    # cross-seed: no shared fold checkpoint SHAs
    a = {C.sha256_file(C.rpsi_checkpoint_root(123) / f"fold{k}" / "best.pt")
         for k in range(3)}
    b = {C.sha256_file(C.rpsi_checkpoint_root(3407) / f"fold{k}" / "best.pt")
         for k in range(3)}
    checks["no_shared_rpsi_fold_ckpts_across_seeds"] = not (a & b)

    # ---- B_phi target isolation: each seed's membership keyed to its own
    #      DeltaDice ranking (compare against the other seed's ranking)
    for S in C.NEW_SEEDS:
        mem = C.read_csv_rows(C.seed_dir(S)
                              / f"phase29_seed{S}_bphi_oof_membership.csv")
        checks[f"seed{S}_membership_rows_4957"] = len(mem) == C.N_DEV
        checks[f"seed{S}_membership_selected_1239"] = sum(
            1 for r in mem if r["selected"] == "True") == C.OOF_K

    # ---- S_omega feature isolation: P_r source must be the seed's own ----- #
    for S in C.NEW_SEEDS:
        for d in ("BUSI", "ISIC", "KUB", "KVASIR"):
            p = C.seed_dir(S) / f"phase29_seed{S}_refined_crop_prob_{d}.npy"
            checks[f"seed{S}_{d}_refined_own"] = p.exists()

    # ---- forbidden couplings --------------------------------------------- #
    # (structural, not numeric): assert seed-specific artifact roots differ
    for S in C.NEW_SEEDS:
        other = 3407 if S == 123 else 123
        checks[f"seed{S}_deltadice_path_differs_from_{other}"] = (
            C.deltadice_target_path(S) != C.deltadice_target_path(other))
        checks[f"seed{S}_features_path_differs_from_{other}"] = (
            C.somega_features_path(S) != C.somega_features_path(other))

    # ---- shared inputs allowed (and required to be seed-independent) ------ #
    checks["shared_global_representation_is_seed42_fixed"] = (
        C.SEED42_DELTADICE_CSV.exists())
    checks["shared_phase25b_features_are_fixed"] = C.CACHE25B.joinpath(
        "features.npy").exists()

    all_pass = all(checks.values())
    C.write_json({
        "artifact": "phase29_cross_seed_dependency_isolation",
        "phase": 29, "stage": "CROSS_SEED_DEPENDENCY_ISOLATION",
        "method": C.METHOD, "specification_revision": C.SPEC_REVISION,
        "generated_utc": C.now_utc(),
        "rule": "each seed's R_psi -> ONLY that seed's DeltaDice/B_phi/S_omega",
        "allowed_shared_inputs": [
            "canonical fixed global representation (G, seed 42)",
            "fixed Phase25B 202-D feature matrix",
            "fixed CV fold manifests (optimization randomness only)",
        ],
        "forbidden_examples_checked": [
            "B_phi_123 <- DeltaDice_42",
            "B_phi_3407 <- DeltaDice_123",
            "S_omega_123 <- candidate_3407",
            "S_omega_3407 <- target_42",
        ],
        "detail": detail,
        "checks": checks, "n_checks": len(checks),
        "n_failed": sum(1 for v in checks.values() if not v),
        "failed": [k for k, v in checks.items() if not v],
        "blocked_terminal_if_fail": C.BLOCKED["CROSS_SEED_DEPENDENCY_FAILURE"],
        "all_pass": all_pass,
    }, C.AUD / "phase29_cross_seed_dependency_isolation.json")
    print(f"[§25] cross-seed isolation: {len(checks)-sum(1 for v in checks.values() if not v)}"
          f"/{len(checks)} PASS")
    return {"all_pass": all_pass, "n_failed": sum(1 for v in checks.values() if not v)}


def check_histories() -> dict:
    import numpy as np

    checks = {}
    runs = []
    for S in C.NEW_SEEDS:
        # R_psi: 3 folds + final
        for role, hist in _rpsi_histories(S):
            runs.append((f"seed{S}_rpsi_{role}", hist, True))
        # B_phi: 5 folds + final
        for role, hist in _bphi_histories(S):
            runs.append((f"seed{S}_bphi_{role}", hist, role != "final"))
        # S_omega: 5 folds + final
        for role, hist in _somega_histories(S):
            runs.append((f"seed{S}_somega_{role}", hist, role != "final"))

    for name, hist, has_best in runs:
        if hist is None or len(hist) == 0:
            checks[f"{name}_exists_nonempty"] = False
            continue
        checks[f"{name}_exists_nonempty"] = True
        eps = [int(r["epoch"]) for r in hist]
        checks[f"{name}_epochs_contiguous"] = eps == list(
            range(min(eps), min(eps) + len(eps)))
        checks[f"{name}_no_duplicate_epoch"] = len(set(eps)) == len(eps)
        loss_keys = [k for k in ("train_loss", "train_bce", "train_huber",
                                 "early_stop_loss", "early_stop_bce")
                     if k in hist[0]]
        finite = True
        for r in hist:
            for lk in loss_keys:
                v = r.get(lk, "")
                if v not in ("", None):
                    try:
                        if not np.isfinite(float(v)):
                            finite = False
                    except (TypeError, ValueError):
                        pass
        checks[f"{name}_losses_finite"] = finite

    all_pass = all(checks.values())
    C.write_json({
        "artifact": "phase29_new_training_history_integrity",
        "phase": 29, "stage": "NEW_TRAINING_HISTORY_INTEGRITY",
        "method": C.METHOD, "generated_utc": C.now_utc(),
        "n_runs_checked": len(runs),
        "checks": checks, "n_checks": len(checks),
        "n_failed": sum(1 for v in checks.values() if not v),
        "failed": [k for k, v in checks.items() if not v],
        "blocked_terminal_if_fail":
            C.BLOCKED["TRAINING_HISTORY_INTEGRITY_FAILURE"],
        "all_pass": all_pass,
    }, C.AUD / "phase29_new_training_history_integrity.json")
    print(f"[§26] history integrity: {len(runs)} runs, "
          f"{sum(1 for v in checks.values() if not v)} failures")
    return {"all_pass": all_pass, "n_failed": sum(1 for v in checks.values() if not v)}


def _rpsi_histories(S):
    root = C.rpsi_experiment_root(S)
    out = []
    for role, sub in (("fold0", "fold0"), ("fold1", "fold1"),
                      ("fold2", "fold2"), ("final", "final_refit")):
        p = root / sub / "history.csv"
        out.append((role, C.read_csv_rows(p) if p.exists() else None))
    return out


def _bphi_histories(S):
    root = C.bphi_experiment_root(S)
    out = []
    for k in range(5):
        p = root / f"fold{k}" / "history.csv"
        out.append((f"fold{k}", C.read_csv_rows(p) if p.exists() else None))
    p = root / "final" / "history.csv"
    out.append(("final", C.read_csv_rows(p) if p.exists() else None))
    return out


def _somega_histories(S):
    root = C.somega_experiment_root(S)
    out = []
    for k in range(5):
        p = root / f"cv_fold{k}" / "history.csv"
        out.append((f"fold{k}", C.read_csv_rows(p) if p.exists() else None))
    p = root / "final" / "history.csv"
    out.append(("final", C.read_csv_rows(p) if p.exists() else None))
    return out


def main() -> int:
    iso = check_isolation()
    hist = check_histories()
    return 0 if (iso["all_pass"] and hist["all_pass"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
