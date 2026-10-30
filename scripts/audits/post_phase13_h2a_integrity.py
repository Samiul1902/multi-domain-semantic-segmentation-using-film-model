"""H2-A-B1 post-training integrity analysis (§10 trajectory, §11 checkpoint state, §14 selection replay).

Runs AFTER the H2A training replay terminates. Performs NO training and NO model construction.
Reads the H2A history/checkpoints and the frozen Phase-13 history/checkpoints.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(r"D:\Softfors\jup")
TABLES = ROOT / "reports" / "tables"
AUDITS = ROOT / "reports" / "audits"
H2A_ID = "post_phase13_h2a_kub_localizer_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3"
P13_ID = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"
H2A_CK = ROOT / "checkpoints" / H2A_ID
H2A_EXP = ROOT / "experiments" / H2A_ID
P13_CK = ROOT / "checkpoints" / P13_ID
P13_EXP = ROOT / "experiments" / P13_ID
CREATED = "2026-09-22T08:00:00Z"

SELECTION_TERM_NAMES = [
    "DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90", "tiny_recall90", "overall_recall90",
    "PROPOSAL_PIXEL_ANY_HIT_PRECISION", "negative_mean_roi_area_fraction", "negative_val_loss",
]


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def replay_selection(hist: pd.DataFrame, patience: int = 15) -> dict:
    """Independently replay the frozen 6-term strict-lexicographic rule from history."""
    best = None
    best_epoch = None
    bad = 0
    rows = []
    stop_epoch = None
    for r in hist.itertuples():
        score = (
            float(r.deployment_balance_hmean), float(r.tiny_recall90), float(r.overall_recall90),
            float(r.proposal_pixel_any_hit_precision), -float(r.mean_roi_area_fraction),
            -float(r.val_loss),
        )
        improved = (best is None) or (score > best)
        if improved:
            best, best_epoch, bad = score, int(r.epoch), 0
        else:
            bad += 1
        rows.append({"epoch": int(r.epoch), "is_new_best": improved, "bad_epochs": bad})
        if stop_epoch is None and best is not None and bad >= patience:
            stop_epoch = int(r.epoch)
    return {"best_score": list(best) if best else None, "best_epoch": best_epoch,
            "final_bad_epochs": bad, "early_stop_epoch": stop_epoch, "rows": rows}


def main() -> int:
    hist_p = H2A_EXP / "history.csv"
    if not hist_p.exists():
        print("H2A history.csv not found - training has not completed."); return 2
    hist = pd.read_csv(hist_p)
    p13_hist = pd.read_csv(P13_EXP / "history.csv")
    checks, fail = {}, []

    def ck(name, ok, detail=""):
        checks[name] = {"pass": bool(ok), "detail": detail}
        if not ok:
            fail.append(name)

    # ---------- §13 history contract ----------
    ck("history_rows_ge_1", len(hist) >= 1, f"rows={len(hist)}")
    ck("epochs_contiguous_from_1", bool((hist.epoch.diff().dropna() == 1).all()) and int(hist.epoch.iloc[0]) == 1,
       f"epochs {int(hist.epoch.iloc[0])}..{int(hist.epoch.iloc[-1])}")
    ck("no_duplicate_epochs", hist.epoch.duplicated().sum() == 0, f"dupes={int(hist.epoch.duplicated().sum())}")
    required = ["epoch", "train_loss", "val_loss", "proposal_pixel_hit_count", "proposal_total_count",
                "proposal_pixel_any_hit_precision", "tiny_recall90", "overall_recall90",
                "deployment_balance_hmean", "mean_roi_area_fraction", "is_new_best", "bad_epochs",
                "proposal_count_per_image"]
    missing = [c for c in required if c not in hist.columns]
    ck("history_required_columns", not missing, f"missing={missing}")

    # ---------- §10 trajectory reproduction ----------
    n = min(len(hist), len(p13_hist))
    a = hist.iloc[:n].reset_index(drop=True)
    b = p13_hist.iloc[:n].reset_index(drop=True)
    same_epochs = bool((a.epoch.to_numpy() == b.epoch.to_numpy()).all())
    d_train = float(np.max(np.abs(a.train_loss.to_numpy() - b.train_loss.to_numpy())))
    d_val = float(np.max(np.abs(a.val_loss.to_numpy() - b.val_loss.to_numpy())))
    lr_mismatch = int((np.abs(a.learning_rate.to_numpy() - b.learning_rate.to_numpy()) > 1e-12).sum()) \
        if "learning_rate" in a.columns and "learning_rate" in b.columns else None
    traj = {
        "overlapping_epochs": n,
        "epochs_aligned": same_epochs,
        "max_abs_train_loss_diff": d_train,
        "max_abs_val_loss_diff": d_val,
        "lr_mismatches": lr_mismatch,
        "train_loss_exact_match": bool(np.array_equal(a.train_loss.to_numpy(), b.train_loss.to_numpy())),
        "val_loss_exact_match": bool(np.array_equal(a.val_loss.to_numpy(), b.val_loss.to_numpy())),
        "gradient_semantics_changed": "NO" if (d_train <= 1e-6 and d_val <= 1e-6) else "REVIEW",
    }
    ck("trajectory_reproduction_train_loss", d_train <= 1e-6, f"max abs diff={d_train:.3e}")
    ck("trajectory_reproduction_val_loss", d_val <= 1e-6, f"max abs diff={d_val:.3e}")

    # ---------- §11 checkpoint state cross-checks ----------
    ck_compare = []
    h2a_ckpts = {}
    for p in sorted(H2A_CK.glob("*.pt")):
        c = torch.load(p, map_location="cpu", weights_only=False)
        h2a_ckpts[int(c["epoch"])] = (p, c)
    for ep in sorted(h2a_ckpts):
        p13_path = P13_CK / "best.pt" if ep == 53 else (P13_CK / "latest.pt" if ep == 68 else None)
        if p13_path is None:
            cand = P13_CK / "provenance" / f"r2b_pixel_epoch{ep}_best.pt"
            p13_path = cand if cand.exists() else None
        if p13_path is None or not p13_path.exists():
            continue
        s1 = h2a_ckpts[ep][1]["model_state"]
        s2 = torch.load(p13_path, map_location="cpu", weights_only=False)["model_state"]
        common = sorted(set(s1) & set(s2))
        worst, nbad = 0.0, 0
        for k in common:
            d = float((s1[k].float() - s2[k].float()).abs().max())
            worst = max(worst, d)
            if d > 0:
                nbad += 1
        ck_compare.append({"epoch": ep, "reference": str(p13_path.relative_to(ROOT)).replace("\\", "/"),
                           "tensors_compared": len(common),
                           "max_tensor_abs_diff": worst, "mismatching_tensors": nbad,
                           "material_mismatch": worst > 1e-6})
    ck("checkpoint_state_consistent", all(not c["material_mismatch"] for c in ck_compare),
       f"compared {len(ck_compare)} overlapping epochs")

    # ---------- §14 selection replay ----------
    rep = replay_selection(hist)
    best_ck = torch.load(H2A_CK / "best.pt", map_location="cpu", weights_only=False)
    stored = tuple(float(v) for v in best_ck["best_validation_score"])
    replay_best = tuple(rep["best_score"]) if rep["best_score"] else None
    # The replayed tuple is rebuilt from history.csv, whose floats round-trip through
    # text; exact float equality is therefore too strict. Use 1e-12 (machine-level).
    term_diffs = [abs(a - b) for a, b in zip(stored, replay_best)] if replay_best else [float("inf")]
    max_term_diff = max(term_diffs)
    tuple_ok = max_term_diff <= 1e-12
    epoch_ok = int(best_ck["epoch"]) == rep["best_epoch"]
    replay_ok = tuple_ok and epoch_ok
    mismatch = []
    if not tuple_ok:
        mismatch.append({"field": "best_validation_score", "max_abs_term_diff": max_term_diff,
                         "stored": list(stored), "replayed": rep["best_score"]})
    if not epoch_ok:
        mismatch.append({"field": "best_epoch", "stored": int(best_ck["epoch"]), "replayed": rep["best_epoch"]})
    ck("selection_replay_zero_mismatches", replay_ok,
       f"mismatches={len(mismatch)} | max_abs_term_diff={max_term_diff:.3e} | best_epoch {rep['best_epoch']}")
    _sel_tuple = best_ck.get("configuration", {}).get("checkpoint_selection", {}).get("tuple", [])
    ck("selection_term_names_6", len(_sel_tuple) == 6, str(_sel_tuple))

    status = "PASS" if not fail else "CHECK_REQUIRED"

    # ---------- write artifacts ----------
    traj_obj = {
        "artifact": "POST_PHASE13_H2A_TRAINING_TRAJECTORY_REPRODUCTION",
        "status": "PASS" if (d_train <= 1e-6 and d_val <= 1e-6) else "CHECK_REQUIRED",
        "created_utc": CREATED, "h2a_experiment_id": H2A_ID, "phase13_experiment_id": P13_ID,
        "h2a_history_path": str(hist_p.relative_to(ROOT)).replace("\\", "/"),
        "h2a_history_sha": sha(hist_p),
        "phase13_history_sha": sha(P13_EXP / "history.csv"),
        "comparison": traj,
        "interpretation": (
            "The H2A run changes CHECKPOINT SELECTION ONLY. Its gradient-update semantics must therefore be "
            "identical to the Phase-13 clean-v3 run, so train_loss/val_loss must agree epoch-by-epoch until "
            "the two runs' early stopping diverges."),
        "checkpoint_state_cross_checks": ck_compare,
        "checkpoint_state_note": ("Model tensors are compared, NOT whole-file SHAs, because the checkpoint "
                                  "metadata/selection tuple legitimately differs."),
        "counters": {"training": 0, "model_constructions": 0, "cuda_requests": 0,
                     "localizer_forwards": 0, "test_reads": 0, "external_test_reads": 0},
    }
    (AUDITS / "post_phase13_h2a_training_trajectory_reproduction.json").write_text(
        json.dumps(traj_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    rep_obj = {
        "artifact": "POST_PHASE13_H2A_SELECTION_REPLAY_VERIFICATION",
        "status": "PASS" if replay_ok else "CHECK_REQUIRED",
        "created_utc": CREATED, "h2a_experiment_id": H2A_ID,
        "history_sha": sha(hist_p),
        "replay_rule": "strict lexicographic > on the frozen 6-term tuple; ties = BAD_EPOCH; patience 15",
        "selection_term_names": SELECTION_TERM_NAMES,
        "replayed": {"best_epoch": rep["best_epoch"], "best_score": rep["best_score"],
                     "final_bad_epochs": rep["final_bad_epochs"], "early_stop_epoch": rep["early_stop_epoch"]},
        "stored": {"best_epoch": int(best_ck["epoch"]), "best_score": list(stored),
                   "early_stopping_state": best_ck.get("early_stopping_state")},
        "mismatches": mismatch, "mismatch_count": len(mismatch),
        "max_abs_term_diff": max_term_diff,
        "comparison_tolerance": 1e-12,
        "comparison_tolerance_note": "replayed tuple is rebuilt from history.csv; floats round-trip through text, so exact equality is too strict at the 1e-17 level",
        "counters": {"training": 0, "model_constructions": 0, "cuda_requests": 0, "test_reads": 0},
    }
    (AUDITS / "post_phase13_h2a_selection_replay_verification.json").write_text(
        json.dumps(rep_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # markdown companions
    L = ["# POST-PHASE-13 H2-A-B1 — TRAINING TRAJECTORY REPRODUCTION", "",
         f"- status: **{traj_obj['status']}**", f"- H2A history SHA: `{traj_obj['h2a_history_sha']}`",
         f"- Phase-13 history SHA: `{traj_obj['phase13_history_sha']}`", "",
         "| quantity | value |", "|---|---|",
         f"| overlapping epochs | {n} |", f"| epochs aligned | {traj['epochs_aligned']} |",
         f"| max abs train_loss diff | {d_train:.3e} |", f"| max abs val_loss diff | {d_val:.3e} |",
         f"| train_loss exact match | {traj['train_loss_exact_match']} |",
         f"| val_loss exact match | {traj['val_loss_exact_match']} |",
         f"| LR mismatches | {lr_mismatch} |", f"| gradient semantics changed | **{traj['gradient_semantics_changed']}** |", "",
         "## Checkpoint model-state cross-checks", "",
         "| epoch | reference | tensors | max abs diff | mismatching | material |", "|---|---|---|---|---|---|"]
    for c in ck_compare:
        L.append(f"| {c['epoch']} | `{c['reference']}` | {c['tensors_compared']} | {c['max_tensor_abs_diff']:.3e} | "
                 f"{c['mismatching_tensors']} | {'**YES**' if c['material_mismatch'] else 'no'} |")
    if not ck_compare:
        L.append("| — | no overlapping historical checkpoint reached | — | — | — | — |")
    L += ["", traj_obj["interpretation"], "", traj_obj["checkpoint_state_note"], ""]
    (AUDITS / "post_phase13_h2a_training_trajectory_reproduction.md").write_text("\n".join(L), encoding="utf-8")

    M = ["# POST-PHASE-13 H2-A-B1 — SELECTION REPLAY VERIFICATION", "",
         f"- status: **{rep_obj['status']}**", f"- replay rule: {rep_obj['replay_rule']}", "",
         "| quantity | replayed | stored |", "|---|---|---|",
         f"| best epoch | {rep['best_epoch']} | {int(best_ck['epoch'])} |",
         f"| final bad_epochs | {rep['final_bad_epochs']} | {best_ck.get('early_stopping_state', {}).get('bad_epochs')} |",
         f"| early-stop epoch | {rep['early_stop_epoch']} | — |", "",
         "**best tuple (replayed):**", "```", str(rep["best_score"]), "```",
         "**best tuple (stored):**", "```", str(list(stored)), "```", "",
         f"**mismatches: {len(mismatch)}**", ""]
    for m in mismatch:
        M.append(f"- {m}")
    (AUDITS / "post_phase13_h2a_selection_replay_verification.md").write_text("\n".join(M), encoding="utf-8")

    print("STATUS:", status)
    print("integrity failures:", fail if fail else "NONE")
    print(f"overlapping epochs {n} | max train {d_train:.3e} | max val {d_val:.3e} | LR mismatches {lr_mismatch}")
    print("checkpoint cross-checks:", ck_compare if ck_compare else "none (no overlapping epoch reached)")
    print("selection replay:", "PASS" if replay_ok else "FAIL", "| best epoch", rep["best_epoch"],
          "| final bad_epochs", rep["final_bad_epochs"], "| early stop", rep["early_stop_epoch"])
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
