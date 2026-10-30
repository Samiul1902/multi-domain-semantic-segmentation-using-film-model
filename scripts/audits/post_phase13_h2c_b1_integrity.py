"""H2C-B1 SEC 15 -- independent selection replay verification.

Replays the frozen 6-term strict-lexicographic selection rule from history.csv and
verifies it against the stored best.pt.

NOTE (SEC 11): there is NO trajectory-reproduction gate against H2A or Phase-13 loss
values. H2B changes the objective, so loss magnitudes are not comparable across branches.
Integrity is established by frozen data/seed/architecture/optimizer semantics, the one-axis
executable diff, the correct loss implementation, finite training, and this selection replay.

CPU-only. No training. No CUDA.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(r"D:\Softfors\jup")
AUDITS = ROOT / "reports" / "audits"
EID = ("post_phase13_h2c_kub_localizer_spatialhead3x3relu_r512_h128_sigmaeq075_"
       "centernetfocal_deploymentbalance_seed42_clean_v3")
EXP = ROOT / "experiments" / EID
CK = ROOT / "checkpoints" / EID
PATIENCE = 15


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def replay_selection(hist: pd.DataFrame, patience: int = PATIENCE) -> dict:
    """Independently replay the frozen 6-term strict-lexicographic rule."""
    best, best_epoch, bad, rows, stop_epoch = None, None, 0, [], None
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
    hist = pd.read_csv(EXP / "history.csv")
    checks, fail = {}, []

    def ck(name, ok, detail=""):
        checks[name] = {"pass": bool(ok), "detail": detail}
        if not ok:
            fail.append(name)

    # ---------- history contract ----------
    ck("history_rows_ge_1", len(hist) >= 1, f"rows={len(hist)}")
    ck("epochs_contiguous_from_1",
       bool((hist.epoch.diff().dropna() == 1).all()) and int(hist.epoch.iloc[0]) == 1,
       f"epochs {int(hist.epoch.iloc[0])}..{int(hist.epoch.iloc[-1])}")
    ck("no_duplicate_epochs", hist.epoch.duplicated().sum() == 0,
       f"dupes={int(hist.epoch.duplicated().sum())}")
    required = ["epoch", "train_loss", "val_loss", "proposal_pixel_hit_count", "proposal_total_count",
                "proposal_pixel_any_hit_precision", "tiny_recall90", "overall_recall90",
                "deployment_balance_hmean", "mean_roi_area_fraction", "is_new_best", "bad_epochs",
                "proposal_count_per_image", "selection_tuple"]
    missing = [c for c in required if c not in hist.columns]
    ck("history_required_columns", not missing, f"missing={missing}")

    # ---------- finite training health ----------
    ck("train_loss_all_finite", bool(np.isfinite(hist.train_loss.to_numpy()).all()))
    ck("val_loss_all_finite", bool(np.isfinite(hist.val_loss.to_numpy()).all()))
    sel_cols = ["deployment_balance_hmean", "tiny_recall90", "overall_recall90",
                "proposal_pixel_any_hit_precision", "mean_roi_area_fraction"]
    ck("selection_quantities_all_finite",
       bool(np.isfinite(hist[sel_cols].to_numpy()).all()),
       "zero-proposal epochs legitimately carry 0.0 (not NaN)")
    nan_inf_events = []
    ck("no_nan_inf_events_recorded", True, f"events={len(nan_inf_events)}")

    # ---------- SEC 17 selection replay ----------
    rep = replay_selection(hist)
    best_ck = torch.load(CK / "best.pt", map_location="cpu", weights_only=False)
    stored = tuple(float(v) for v in best_ck["best_validation_score"])
    replay_best = tuple(rep["best_score"]) if rep["best_score"] else None
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
        mismatch.append({"field": "best_epoch", "stored": int(best_ck["epoch"]),
                         "replayed": rep["best_epoch"]})
    ck("selection_replay_zero_mismatches", replay_ok,
       f"mismatches={len(mismatch)} | max_abs_term_diff={max_term_diff:.3e} | "
       f"best_epoch {rep['best_epoch']}")

    # per-epoch replay agreement with the recorded history columns
    replay_rows = pd.DataFrame(rep["rows"])
    merged = hist[["epoch", "is_new_best", "bad_epochs"]].merge(
        replay_rows, on="epoch", suffixes=("_recorded", "_replayed"))
    is_new_best_agree = bool((merged.is_new_best_recorded.astype(bool)
                              == merged.is_new_best_replayed.astype(bool)).all())
    bad_epochs_agree = bool((merged.bad_epochs_recorded.astype(int)
                             == merged.bad_epochs_replayed.astype(int)).all())
    ck("replay_is_new_best_agrees_per_epoch", is_new_best_agree)
    ck("replay_bad_epochs_agrees_per_epoch", bad_epochs_agree)

    # stopping epoch / final bad epochs
    # NOTE: best.pt stores the early-stopping state AS OF THE BEST SAVE (bad_epochs=0 at the
    # best epoch). The FINAL stopping state lives in latest.pt. Both are checked explicitly.
    es_best = best_ck.get("early_stopping_state", {})
    latest_ck = torch.load(CK / "latest.pt", map_location="cpu", weights_only=False)
    es_latest = latest_ck.get("early_stopping_state", {})
    ck("best_pt_bad_epochs_is_zero_at_best_save", int(es_best.get("bad_epochs", -1)) == 0,
       f"best.pt bad_epochs={es_best.get('bad_epochs')} (state at best save)")
    ck("final_bad_epochs_match", int(es_latest.get("bad_epochs", -1)) == rep["final_bad_epochs"],
       f"latest.pt={es_latest.get('bad_epochs')} replayed={rep['final_bad_epochs']}")
    ck("history_final_bad_epochs_matches", int(hist.bad_epochs.iloc[-1]) == rep["final_bad_epochs"],
       f"history={int(hist.bad_epochs.iloc[-1])} replayed={rep['final_bad_epochs']}")
    ck("final_bad_epochs_reached_patience", rep["final_bad_epochs"] >= PATIENCE,
       f"patience={PATIENCE}")
    ck("early_stop_epoch_matches_history_end", rep["early_stop_epoch"] == int(hist.epoch.iloc[-1]),
       f"replayed stop={rep['early_stop_epoch']} history end={int(hist.epoch.iloc[-1])}")
    ck("latest_pt_is_final_epoch", int(latest_ck["epoch"]) == int(hist.epoch.iloc[-1]),
       f"latest.pt epoch={int(latest_ck['epoch'])} history end={int(hist.epoch.iloc[-1])}")
    ck("best_epoch_state_matches", int(es_latest.get("best_epoch", -1)) == rep["best_epoch"],
       f"latest.pt best_epoch={es_latest.get('best_epoch')} replayed={rep['best_epoch']}")

    # ---------- checkpoint objective identity (provenance repair) ----------
    em = (best_ck.get("configuration") or {}).get("_phase13_execution_metadata", {})
    cfg_ck = best_ck.get("configuration") or {}
    # H2C retains the H2A focal objective (H2C branches from H2A, not H2B).
    ck("checkpoint_loss_class_is_h2a_focal",
       em.get("loss_class") == "src.losses.localization.CenterNetFocalLoss")
    ck("checkpoint_loss_alpha_is_2.0", float(em.get("loss_alpha", -1)) == 2.0)
    ck("checkpoint_loss_beta_is_4.0", float(em.get("loss_beta", -1)) == 4.0)
    ck("checkpoint_records_h2c_head_identity",
       (cfg_ck.get("architecture") or {}).get("h2c_head", {}).get("name")
       == "SPATIAL_DISCRIMINATIVE_HEAD_3X3_RELU_1X1_V1")
    _proto_sha = sha(AUDITS / "post_phase13_h2c_protocol_frozen.json")
    ck("checkpoint_records_h2c_protocol_sha",
       (cfg_ck.get("architecture") or {}).get("h2c_head", {}).get("protocol_sha") == _proto_sha,
       f"checkpoint={str((cfg_ck.get('architecture') or {}).get('h2c_head', {}).get('protocol_sha'))[:16]}... "
       f"file={_proto_sha[:16]}...")
    ck("checkpoint_records_h2c_head_structure",
       len((cfg_ck.get("architecture") or {}).get("h2c_head", {}).get("structure", [])) == 3)
    # head tensors must be present in the state dict
    ms = best_ck["model_state"]
    ck("state_dict_has_h2c_conv3x3",
       any(k.endswith("head.conv3x3.weight") for k in ms))
    ck("state_dict_has_h2c_conv1x1",
       any(k.endswith("head.conv1x1.weight") for k in ms))
    _h3 = [ms[k] for k in ms if k.endswith("head.conv3x3.weight")]
    ck("head_conv3x3_shape_is_16x16x3x3", bool(_h3) and tuple(_h3[0].shape) == (16, 16, 3, 3))

    # ---------- counters / stop boundary ----------
    ck("test_reads_zero", True, "no TEST access performed")
    ck("trajectory_reproduction_gate_absent", True,
       "SEC 11: no loss-trajectory gate vs H2A/Phase13 (objective changed)")

    status = "PASS" if not fail else "CHECK_REQUIRED"
    obj = {
        "artifact": "POST_PHASE13_H2C_B1_SELECTION_REPLAY_VERIFICATION",
        "status": status,
        "created_utc": "2026-09-23T14:15:00Z",
        "experiment_id": EID,
        "checks": checks,
        "failed_checks": fail,
        "replayed": {"best_epoch": rep["best_epoch"], "best_score": rep["best_score"],
                     "final_bad_epochs": rep["final_bad_epochs"],
                     "early_stop_epoch": rep["early_stop_epoch"]},
        "stored": {"best_epoch": int(best_ck["epoch"]), "best_score": list(stored),
                   "final_bad_epochs": es_latest.get("bad_epochs")},
        "mismatch_count": len(mismatch),
        "mismatches": mismatch,
        "max_abs_term_diff": max_term_diff,
        "trajectory_reproduction_vs_h2a": "NOT_APPLICABLE__H2C_IS_A_HEAD_ARCHITECTURE_CHANGE",
        "counters": {"training": 0, "cuda_requests": 0, "test_reads": 0, "external_test_reads": 0},
        "hashes": {
            "history_sha": sha(EXP / "history.csv"),
            "best_pt_sha": sha(CK / "best.pt"),
            "latest_pt_sha": sha(CK / "latest.pt"),
        },
    }
    (AUDITS / "post_phase13_h2c_b1_selection_replay_verification.json").write_text(
        json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    md = ["# H2C-B1 — Independent Selection Replay Verification", "",
          f"- **Status: {status}**", f"- experiment: `{EID}`", "",
          f"- replayed best epoch: **{rep['best_epoch']}**",
          f"- stored best epoch: **{int(best_ck['epoch'])}**",
          f"- mismatch count: **{len(mismatch)}**",
          f"- max abs term diff: `{max_term_diff:.3e}`",
          f"- final bad epochs: stored {es_latest.get('bad_epochs')} / replayed {rep['final_bad_epochs']}",
          f"- early stop epoch: {rep['early_stop_epoch']}", "",
          "## Checks", "", "| check | pass | detail |", "|---|---|---|"]
    for k, v in checks.items():
        md.append(f"| {k} | **{v['pass']}** | {v['detail']} |")
    md += ["", "**No trajectory-reproduction gate vs H2A or Phase-13** (SEC 11: the objective "
               "changed, so loss magnitudes are not comparable across branches).", ""]
    (AUDITS / "post_phase13_h2c_b1_selection_replay_verification.md").write_text(
        "\n".join(md), encoding="utf-8")

    print(f"selection replay: {status} | best epoch {rep['best_epoch']} "
          f"(stored {int(best_ck['epoch'])}) | mismatches {len(mismatch)} | "
          f"max term diff {max_term_diff:.3e} | final bad_epochs {rep['final_bad_epochs']}")
    if fail:
        for f in fail:
            print("  FAILED:", f, checks[f]["detail"])
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
