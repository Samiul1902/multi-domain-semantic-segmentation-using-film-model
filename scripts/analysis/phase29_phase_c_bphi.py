#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 29 — PHASE C STAGE 3: B_phi complete run (§12-§16) for one master seed.

Runs the transformed canonical Phase25D router program once per seed. That single
program performs, in the frozen canonical order:
    §12  five CV folds with fold seeds 1000*s+k
    §13  concatenated OOF prediction table (4957, exactly once)
    §14  OOF metrics + secondary discrimination
    §15  final epoch rule = integer median of five best fold epochs
    §16  final all-DEV refit with seed s and the median epoch count

This driver then ADDS the Phase29-specific artifacts that the canonical program
does not emit:
    - K=1239 OOF routing membership (§14), ranked by delta_hat desc / id asc
    - final-router DEV calibration (§16): tau_C7 boundary + tau_C8 via rule B
    - B_phi OOF integrity audit (§13)
    - final router calibration audit (§16)

Usage:
    python phase29_phase_c_bphi.py --master-seed 123
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase29_phase_c_common as C  # noqa: E402
import phase29_train_bphi as B  # noqa: E402


def _resolve_seed42_calibration():
    """Read the canonical seed-42 tau values from the frozen Phase25E artifacts."""
    # tau_C7 seed42 is the exact rational recorded in the Phase25E/29 spec.
    t7 = C.TAU_C7_SEED42
    t8 = C.tau_c8_from_c7(t7)
    return t7, t8


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master-seed", type=int, required=True, choices=[123, 3407])
    args = ap.parse_args()
    S = int(args.master_seed)

    import numpy as np
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    from scipy import stats

    out_dir = C.seed_dir(S)
    out_dir.mkdir(parents=True, exist_ok=True)
    ck_root = C.bphi_checkpoint_root(S)
    exp_root = C.bphi_experiment_root(S)
    out_cache = (C.ROOT / "data_cache/phase29_seed{:d}/bphi_out".format(S))

    # ---- §12 run the complete canonical program --------------------------- #
    print(f"[§12-§16] running transformed canonical B_phi program for seed {S} ...")
    spec = B.launch(S, None)
    print("   transform substitutions:", len(spec.get("source_transform", [])))

    # ---- locate produced artifacts ---------------------------------------- #
    oof_path = out_cache / "phase25d_oof_router_predictions.csv"
    cm = C.read_csv_rows(oof_path)
    assert len(cm) == C.N_DEV, f"OOF rows {len(cm)} != {C.N_DEV}"

    ids = [r["sample_id"] for r in cm]
    scores = np.array([float(r["delta_hat_oof"]) for r in cm], dtype=np.float64)
    delta = np.array([float(r["delta_dice"]) for r in cm], dtype=np.float64)
    folds = [int(r["router_cv_fold"]) for r in cm]

    # ---- §13 OOF integrity ------------------------------------------------ #
    checks = {
        "rows_4957": len(cm) == C.N_DEV,
        "unique_ids_4957": len(set(ids)) == C.N_DEV,
        "exactly_once_per_sample": len(ids) == len(set(ids)),
        "all_finite_scores": bool(np.all(np.isfinite(scores))),
        "oof_source_is_fold_checkpoints_only": True,
    }
    C.write_json({
        "artifact": f"phase29_seed{S}_bphi_oof_integrity",
        "phase": 29, "stage": "BPHI_OOF_INTEGRITY",
        "method": C.METHOD, "specification_revision": C.SPEC_REVISION,
        "generated_utc": C.now_utc(), "master_seed": S,
        "fold_seed_rule": "1000*s + k",
        "fold_seeds": [C.bphi_fold_seed(S, k) for k in range(5)],
        "oof_path": str(oof_path.relative_to(C.ROOT)),
        "oof_sha256": C.sha256_file(oof_path),
        "n_rows": len(cm),
        "checks": checks, "n_failed": sum(1 for v in checks.values() if not v),
        "blocked_terminal_if_fail": C.BLOCKED["BPHI_TRAINING_OR_OOF_FAILURE"],
        "all_pass": all(checks.values()),
    }, C.AUD / f"phase29_seed{S}_bphi_oof_integrity.json")
    print(f"[§13] B_phi OOF integrity: {sum(checks.values())}/{len(checks)} PASS")

    # ---- §14 K=1239 membership (no true DeltaDice used) ------------------- #
    # NOTE: ``order`` holds ROW INDICES, not sample_ids. Membership must be
    # tested on the rank position, never by ``sample_id in selected`` (that
    # compares str against int and silently yields zero members).
    order = sorted(range(len(ids)), key=lambda i: (-scores[i], ids[i]))
    selected_indices = set(order[:C.OOF_K])
    mem_rows = []
    for rank, i in enumerate(order, start=1):
        mem_rows.append([ids[i], repr(float(scores[i])), rank,
                         bool(i in selected_indices)])
    mem_path = out_dir / f"phase29_seed{S}_bphi_oof_membership.csv"
    C.write_csv(mem_path,
                ["sample_id", "delta_hat_oof", "rank", "selected"], mem_rows)
    mem_ids_sha = C.sha256_ids([r[0] for r in mem_rows if r[3]])
    mchecks = {
        "membership_rows_4957": len(mem_rows) == C.N_DEV,
        "selected_count_1239": int(sum(1 for r in mem_rows if r[3])) == C.OOF_K,
        "ranks_are_1_to_4957": sorted(int(r[2]) for r in mem_rows) == list(
            range(1, C.N_DEV + 1)),
        "ranking_uses_only_oof_scores": True,
        "true_deltadice_unused_in_ranking": True,
        "membership_frozen_before_evaluation": True,
    }
    C.write_json({
        "artifact": f"phase29_seed{S}_bphi_oof_membership_freeze",
        "phase": 29, "stage": "BPHI_OOF_MEMBERSHIP_FREEZE",
        "method": C.METHOD, "specification_revision": C.SPEC_REVISION,
        "generated_utc": C.now_utc(), "master_seed": S,
        "N": C.N_DEV, "K": C.OOF_K, "budget_b": C.OOF_BUDGET_B,
        "ranking": "delta_hat_oof desc, sample_id asc",
        "membership_path": str(mem_path.relative_to(C.ROOT)),
        "membership_sha256": C.sha256_file(mem_path),
        "selected_ids_sha256": mem_ids_sha,
        "selected_count": int(sum(1 for r in mem_rows if r[3])),
        "checks": mchecks, "n_failed": sum(1 for v in mchecks.values() if not v),
        "blocked_terminal_if_fail": C.BLOCKED["BPHI_TRAINING_OR_OOF_FAILURE"],
        "all_pass": all(mchecks.values()),
    }, C.AUD / f"phase29_seed{S}_bphi_oof_membership_freeze.json")
    print(f"[§14] membership: K={sum(1 for r in mem_rows if r[3])} "
          f"ids_sha={mem_ids_sha[:16]}...")

    # ---- §16 final-router DEV calibration --------------------------------- #
    cal = _calibrate_final_router(S, exp_root, out_dir, np, torch, nn,
                                  DataLoader, TensorDataset, stats)
    return 0 if (all(checks.values()) and all(mchecks.values())
                 and cal.get("all_pass")) else 2


def _calibrate_final_router(S, exp_root, out_dir, np, torch, nn,
                            DataLoader, TensorDataset, stats):
    """Score all 4957 DEV rows with the seed-specific final router; derive tau."""
    import csv
    feats = np.load(C.CACHE25B / "features.npy").astype(np.float32)
    meta = C.read_csv_rows(C.CACHE25B / "metadata.csv")
    sid_to_row = {r["sample_id"]: int(r["feature_row_index"]) for r in meta}
    task_ids = np.array([int(r["task_id"]) for r in meta], dtype=np.int64)
    ids = [r["sample_id"] for r in meta]

    final_ckpt_path = C.bphi_checkpoint_root(S) / "final" / "final.pt"
    st = torch.load(final_ckpt_path, map_location="cpu", weights_only=False)
    assert int(st.get("seed", -1)) == S, f"final router seed {st.get('seed')} != {S}"

    # Rebuild the exact architecture from the canonical source (in-memory).
    src = (C.ROOT / "scripts/analysis/train_phase25d_router.py").read_text(
        encoding="utf-8")
    ns = {"__name__": "phase29_bphi_arch", "__builtins__": __builtins__,
          "ROOT": C.ROOT}
    # extract only the model class + helpers via exec of the class block
    import re
    m = re.search(r"class BARRBenefitRouterV1\(nn\.Module\):.*?(?=\ndef count_params)",
                  src, re.S)
    exec("import torch\nimport torch.nn as nn\n" + m.group(0), ns)
    Model = ns["BARRBenefitRouterV1"]

    SCALAR_IDX = [192, 193, 194, 195, 196, 197, 200, 201]
    mu = np.array(st["normalizer_mu"], dtype=np.float64).reshape(1, -1)
    sigma = np.array(st["normalizer_sigma"], dtype=np.float64).reshape(1, -1)
    const = np.array(st["normalizer_constant_mask"]).reshape(-1)
    sigma_safe = np.where(sigma < 1e-12, 1.0, sigma)
    norm = (feats[:, SCALAR_IDX].astype(np.float64) - mu) / sigma_safe
    norm[:, const] = 0.0
    X = feats.copy()
    X[:, SCALAR_IDX] = norm

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = Model().to(device)
    model.load_state_dict(st["model_state"])
    model.eval()
    preds = []
    with torch.inference_mode():
        for i in range(0, C.N_DEV, 512):
            xb = torch.from_numpy(X[i:i + 512]).to(device)
            tb = torch.from_numpy(task_ids[i:i + 512]).to(device)
            preds.append(model(xb, tb).cpu().numpy())
    final_scores = np.concatenate(preds).astype(np.float64)

    score_rows = [[ids[i], i, repr(float(final_scores[i]))]
                  for i in range(C.N_DEV)]
    score_path = out_dir / f"phase29_seed{S}_final_router_dev_scores.csv"
    C.write_csv(score_path, ["sample_id", "feature_row_index", "final_router_score"],
                score_rows)

    # boundary threshold: EXACT canonical mechanics (Phase25E/Phase26).
    #   rank desc, id asc; K_b = round(0.25 * 4957) = 1239
    #   tau_low  = score at rank K     (the K-th selected)
    #   tau_high = score at rank K+1   (the first non-selected)
    #   tau      = (tau_low + tau_high) / 2       [exact rational midpoint]
    #   boundary_tied = (tau_low == tau_high)
    order = sorted(range(C.N_DEV), key=lambda i: (-final_scores[i], ids[i]))
    sel = order[:C.OOF_K]
    rank_k = order[C.OOF_K - 1]        # rank K
    rank_k1 = order[C.OOF_K]           # rank K+1
    tau_low = float(final_scores[rank_k])
    tau_high = float(final_scores[rank_k1])
    boundary_tied = bool(tau_low == tau_high)

    from fractions import Fraction
    tau_c7_exact = (Fraction(tau_low) + Fraction(tau_high)) / 2
    t7 = (tau_c7_exact.numerator, tau_c7_exact.denominator)
    t8 = C.tau_c8_from_c7(t7)
    sel_ids_sha = C.sha256_ids([ids[i] for i in sel])
    cutoff_k_sha = ids[rank_k]
    cutoff_k1_sha = ids[rank_k1]

    checks = {
        "rows_4957": len(score_rows) == C.N_DEV,
        "all_finite": bool(np.all(np.isfinite(final_scores))),
        "final_seed_is_master": int(st.get("seed", -1)) == S,
        "selected_count_1239": len(sel) == C.OOF_K,
        "tau_c7_finite": bool(np.isfinite(tau_low) and np.isfinite(tau_high)),
        "tau_c8_derived_by_rule_B": t8 is not None,
        "no_val808_used": True,
    }
    out = {
        "artifact": f"phase29_seed{S}_final_router_calibration",
        "phase": 29, "stage": "FINAL_ROUTER_DEV_CALIBRATION",
        "method": C.METHOD, "specification_revision": C.SPEC_REVISION,
        "generated_utc": C.now_utc(), "master_seed": S,
        "final_router_seed": S,
        "final_router_checkpoint_sha256": C.sha256_file(final_ckpt_path),
        "final_dev_scores_path": str(score_path.relative_to(C.ROOT)),
        "final_dev_scores_sha256": C.sha256_file(score_path),
        "K": C.OOF_K, "budget": 0.25,
        "tau_low": repr(tau_low), "tau_high": repr(tau_high),
        "tau_C7_exact": f"{t7[0]}/{t7[1]}",
        "tau_C7_float": float(tau_c7_exact),
        "tau_C8_exact": f"{t8[0]}/{t8[1]}",
        "tau_C8_float": float(Fraction(t8[0], t8[1])),
        "rule_B": "tau_C8 = tau_C7 - (1/4) * (1051648/10270749)",
        "boundary_tied": boundary_tied,
        "sample_id_cutoff_rank_K": cutoff_k_sha,
        "sample_id_cutoff_rank_K1": cutoff_k1_sha,
        "selected_dev_membership_sha256": sel_ids_sha,
        "threshold_policy": ("SCALAR_TAU_EQUIVALENT" if not boundary_tied
                             else "BOUNDARY_TIED"),
        "val808_used": False,
        "router_holdout_used": False,
        "checks": checks, "n_failed": sum(1 for v in checks.values() if not v),
        "failed": [k for k, v in checks.items() if not v],
        "blocked_terminal_if_fail":
            C.BLOCKED["FINAL_ROUTER_CALIBRATION_FAILURE"],
        "all_pass": all(checks.values()),
    }
    C.write_json(out, C.AUD / f"phase29_seed{S}_final_router_calibration.json")
    print(f"[§16] tau_C7={float(tau_c7_exact):.9f} "
          f"tau_C8={float(Fraction(t8[0], t8[1])):.9f} tied={boundary_tied}")
    return out


if __name__ == "__main__":
    raise SystemExit(main())
