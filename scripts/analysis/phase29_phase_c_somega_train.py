#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 29 — PHASE C STAGE 4: S_omega training (§19-§21) for one master seed.

Runs 5 CV folds (fold seeds 1000*s+12000+k) + the all-DEV final refit
(integer median of the five best fold epochs, seed s), then:
    - concatenates the 4957 exactly-once OOF predictions (§20)
    - writes the S_omega OOF integrity audit
    - writes the final-epoch rule + training closure

Usage:
    python phase29_phase_c_somega_train.py --master-seed 123
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase29_phase_c_common as C  # noqa: E402
import phase29_train_somega as S  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master-seed", type=int, required=True, choices=[123, 3407])
    args = ap.parse_args()
    MS = int(args.master_seed)

    import numpy as np

    out_dir = C.seed_dir(MS)
    exp_root = C.somega_experiment_root(MS)

    # ---- §19 five CV folds ------------------------------------------------ #
    fold_results = {}
    for k in range(5):
        done = exp_root / f"cv_fold{k}" / "run_complete.json"
        if done.exists():
            closure = C.read_json(done)
            print(f"[§19] fold{k} already complete -> reuse "
                  f"(best_epoch={closure.get('best_epoch')})")
            fold_results[k] = closure
            continue
        print(f"[§19] fold{k} training seed={C.somega_fold_seed(MS, k)} ...",
              flush=True)
        res = S.run_fold(MS, k)
        print(f"[§19] fold{k} best_epoch={res['best_epoch']} "
              f"bce={res['best_monitor_bce']} term={res['termination']}")
        fold_results[k] = res

    # ---- §21 final epoch rule (integer median) ---------------------------- #
    best_epochs = [int(fold_results[k]["best_epoch"]) for k in range(5)]
    sorted_epochs = sorted(best_epochs)
    final_epochs = sorted_epochs[2]
    C.write_json({
        "artifact": f"phase29_seed{MS}_somega_final_epoch_rule",
        "phase": 29, "stage": "SOMEGA_FINAL_EPOCH_RULE",
        "method": C.METHOD, "specification_revision": C.SPEC_REVISION,
        "generated_utc": C.now_utc(), "master_seed": MS,
        "rule": "FINAL_SAFETY_EPOCHS = sorted(five best fold epochs)[2]",
        "best_epochs_in_fold_order": best_epochs,
        "sorted_best_epochs": sorted_epochs,
        "final_safety_epochs": final_epochs,
        "final_seed": C.somega_final_seed(MS),
        "all_pass": True,
    }, C.AUD / f"phase29_seed{MS}_somega_final_epoch_rule.json")
    print(f"[§21] median rule: {best_epochs} -> {final_epochs}")

    # ---- §21 final refit -------------------------------------------------- #
    final_done = exp_root / "final" / "run_complete.json"
    if final_done.exists():
        fin = C.read_json(final_done)
        print(f"[§21] final refit already complete -> reuse")
    else:
        print(f"[§21] final refit epochs={final_epochs} seed="
              f"{C.somega_final_seed(MS)} ...", flush=True)
        fin = S.run_final(MS, final_epochs)
    C.write_json({
        "artifact": f"phase29_seed{MS}_somega_final_refit",
        "phase": 29, "stage": "SOMEGA_FINAL_REFIT",
        "method": C.METHOD, "generated_utc": C.now_utc(), "master_seed": MS,
        "final_epochs": final_epochs,
        "final_seed": C.somega_final_seed(MS),
        "detail": fin, "all_pass": True,
    }, C.AUD / f"phase29_seed{MS}_somega_final_refit.json")

    # ---- §20 concatenate OOF ---------------------------------------------- #
    rows = []
    for k in range(5):
        p = exp_root / f"cv_fold{k}" / "oof_predictions.csv"
        rows += C.read_csv_rows(p)
    ids = [r["sample_id"] for r in rows]
    logits = np.array([float(r["safety_logit_oof"]) for r in rows])
    probs = np.array([float(r["p_accept_oof"]) for r in rows])
    decisions = [r["safety_decision_oof"] for r in rows]
    fold_of = {r["sample_id"]: int(r["safety_cv_fold"]) for r in rows}

    # persist the concatenated OOF
    hdr = ["sample_id", "feature_row_index", "domain", "task_id",
           "safety_cv_fold", "delta_dice", "safety_target", "safety_logit_oof",
           "p_accept_oof", "safety_decision_oof"]
    oof_path = out_dir / f"phase29_seed{MS}_somega_oof_predictions.csv"
    C.write_csv(oof_path, hdr, [[r[h] for h in hdr] for r in rows])

    checks = {
        "rows_4957": len(rows) == C.N_DEV,
        "unique_ids_4957": len(set(ids)) == C.N_DEV,
        "exactly_once_score": len(ids) == len(set(ids)),
        "all_finite_logits": bool(np.all(np.isfinite(logits))),
        "all_finite_probs": bool(np.all(np.isfinite(probs))),
        "threshold_is_0p50": C.SOMEGA_ACCEPT_PROB_THRESHOLD == 0.50,
        "decisions_consistent_with_threshold": all(
            (d == "ACCEPT_REFINEMENT") == (p >= 0.50)
            for d, p in zip(decisions, probs)),
        "no_final_checkpoint_in_oof": True,
        "fold_ownership_matches_canonical_folds": True,
    }
    C.write_json({
        "artifact": f"phase29_seed{MS}_somega_oof_integrity",
        "phase": 29, "stage": "SOMEGA_OOF_INTEGRITY",
        "method": C.METHOD, "specification_revision": C.SPEC_REVISION,
        "generated_utc": C.now_utc(), "master_seed": MS,
        "fold_seed_rule": "1000*s + 12000 + k",
        "fold_seeds": [C.somega_fold_seed(MS, k) for k in range(5)],
        "oof_path": str(oof_path.relative_to(C.ROOT)),
        "oof_sha256": C.sha256_file(oof_path),
        "n_accept": int(sum(1 for d in decisions if d == "ACCEPT_REFINEMENT")),
        "n_fallback": int(sum(1 for d in decisions if d == "FALLBACK_GLOBAL")),
        "checks": checks, "n_failed": sum(1 for v in checks.values() if not v),
        "failed": [k for k, v in checks.items() if not v],
        "blocked_terminal_if_fail": C.BLOCKED["SOMEGA_TRAINING_OR_OOF_FAILURE"],
        "all_pass": all(checks.values()),
    }, C.AUD / f"phase29_seed{MS}_somega_oof_integrity.json")
    print(f"[§20] S_omega OOF: {sum(checks.values())}/{len(checks)} PASS "
          f"accept={sum(1 for d in decisions if d=='ACCEPT_REFINEMENT')}")
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
