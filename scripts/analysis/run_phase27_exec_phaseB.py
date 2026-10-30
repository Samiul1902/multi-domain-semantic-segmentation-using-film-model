"""Phase27 EXECUTION - PHASE B: VAL808 GT SCORING + PRESERVATION ADJUDICATION.

This is the FIRST and ONLY place where VAL808 ground-truth masks are read.  It runs
ONLY after the Phase A prediction artifact was written and hashed (hash barrier).

Canonical scorer (byte-compatible with the Phase25C/25G paired DeltaDice pipeline):
    * prediction binary  = (prob_fp32 >= 0.50)
    * GT binary          = canonical full_field_gt(mask_path): aspect-preserving
                           NEAREST resize to 512 + centre pad, then (arr > 0)
    * Dice               = src.metrics.evaluation_metrics.dice(
                               binary_confusion_counts(pred, gt) )   [eps = 1e-7]

What it does:
    1. re-verify the frozen prediction artifact hash == the Phase A sidecar
       (fail-closed if the predictions changed after hashing)
    2. read VAL808 GT masks and build the GT binary in the canonical 512 canvas
    3. per sample: Dice(global_i, GT_i) and Dice(final_A8_i, GT_i)
    4. Delta_i = Dice(final_i) - Dice(global_i)
    5. macro-domain equal-weight mean estimand (mean of the 4 domain means)
    6. domain-stratified GROUP bootstrap replaying the FROZEN plan
       (data_cache/.../phase27_val808_bootstrap_plan_v1_0.npz), B=2000, PCG64(42)
       identical draws for global / final / delta; percentile CI 2.5 / 97.5
    7. non-inferiority adjudication: PRESERVATION_ASSERTED iff macro lower 95% CI
       bound > -0.005 (strict).  Per-domain harm flag if a domain 95% CI upper
       bound < 0.
    8. secondary descriptive metric: mean Dice (global / final) point estimates,
       and observed branch counts / activation fractions.

NO training / retuning / threshold change / policy change / holdout / test.

Writes:
    reports/tables/phase27_val808_per_sample_scores.csv
    reports/tables/phase27_preservation_domain_summary.csv
    reports/tables/phase27_preservation_macro_bootstrap.csv
    reports/audits/phase27_phaseB_scoring_summary.json
    reports/audits/phase27_preservation_result.json
    data_cache/phase27_barr_preservation_v1_0/phase27_val808_bootstrap_replicates.npz

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/run_phase27_exec_phaseB.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase27_exec_common as E  # noqa: E402
import phase27_spec_common as S  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image, ImageOps  # noqa: E402

from src.metrics.evaluation_metrics import binary_confusion_counts, dice as dice_fn  # noqa: E402
from src.utils.test_lock import verify_test_lock  # noqa: E402

say = print

STRATA = ["BUSI", "ISIC", "KUB", "KVASIR"]
N_BOOT = 2000
MARGIN = 0.005
CI_PCT = (2.5, 97.5)
CANVAS = 512
SEG = 0.50


# --------------------------------------------------------------------------- #
def full_field_gt(mask_path: str, size: int = CANVAS) -> np.ndarray:
    """Canonical full-field GT on the 512 canvas (NEAREST resize, centre padded).

    Exact replica of run_phase25c_oof_inference.full_field_gt.
    """
    img = Image.open(mask_path).convert("L")
    w, h = img.size
    scale = min(size / w, size / h)
    rw, rh = max(1, round(w * scale)), max(1, round(h * scale))
    img = img.resize((rw, rh), Image.Resampling.NEAREST)
    left, top = (size - rw) // 2, (size - rh) // 2
    img = ImageOps.expand(img, (left, top, size - rw - left, size - rh - top))
    return (np.asarray(img) > 0).astype(np.uint8)


def canon_dice(pred_bin: np.ndarray, gt_bin: np.ndarray) -> float:
    return float(dice_fn(binary_confusion_counts(pred_bin, gt_bin)))


def ci(arr: np.ndarray):
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return None, None, None, 0
    return (float(np.mean(finite)),
            float(np.percentile(finite, CI_PCT[0])),
            float(np.percentile(finite, CI_PCT[1])),
            int(finite.size))


# --------------------------------------------------------------------------- #
def main() -> int:
    t0 = time.time()
    verify_test_lock(str(E.ROOT))
    say("TEST lock verified")

    # ---- hash barrier: prediction artifact must still match Phase A -------------
    side = E.jload(E.ROOT / E.PREDICTIONS_CSV_SHA_SIDECAR)
    assert side["hashed_before_gt_read"] is True
    assert side["gt_reads_at_hash_time"] == 0
    pred_now = E.sha256_file(E.ROOT / E.PREDICTIONS_CSV)
    if pred_now != side["predictions_csv_sha256"]:
        raise SystemExit(
            "FAIL-CLOSED: prediction artifact changed after hashing "
            f"({pred_now} != {side['predictions_csv_sha256']})")
    gp_now = E.sha256_file(E.CACHE27 / "phase27_val808_global_prob_f16.npy")
    fp_now = E.sha256_file(E.CACHE27 / "phase27_val808_final_prob_f16.npy")
    assert gp_now == side["global_prob_npy_sha256"], "global prob npy drift"
    assert fp_now == side["final_prob_npy_sha256"], "final prob npy drift"
    say(f"hash barrier OK: predictions sha {pred_now}")

    # ---- population (canonical order) ------------------------------------------ #
    rows = S.val808_rows()
    df = pd.DataFrame(rows).sort_values(["dataset", "sample_id"]).reset_index(drop=True)
    assert len(df) == E.VAL808_N, len(df)

    preds = pd.read_csv(E.ROOT / E.PREDICTIONS_CSV)
    assert preds["sample_id"].tolist() == df["sample_id"].astype(str).tolist(), \
        "prediction order must equal canonical VAL808 order"

    gp = np.load(E.CACHE27 / "phase27_val808_global_prob_f16.npy")
    fp = np.load(E.CACHE27 / "phase27_val808_final_prob_f16.npy")
    assert gp.shape == (len(df), CANVAS, CANVAS), gp.shape
    assert fp.shape == (len(df), CANVAS, CANVAS), fp.shape

    # ---- GT read (PHASE B ONLY) ------------------------------------------------- #
    per_rows = []
    gt_reads = 0
    for i, r in df.iterrows():
        sid = str(r["sample_id"])
        gt_bin = full_field_gt(r["mask_path"])
        gt_reads += 1

        g_bin = (np.asarray(gp[i], dtype=np.float32) >= SEG).astype(np.uint8)
        f_bin = (np.asarray(fp[i], dtype=np.float32) >= SEG).astype(np.uint8)

        g_dice = canon_dice(g_bin, gt_bin)
        f_dice = canon_dice(f_bin, gt_bin)
        delta = f_dice - g_dice

        pr = preds.iloc[i]
        per_rows.append({
            "sample_id": sid,
            "dataset": r["dataset"],
            "task_id": int(r["task_id"]),
            "group_key": S.metadata_group_key(r),
            "state_machine_branch": pr["state_machine_branch"],
            "router_decision": pr["router_decision"],
            "global_dice": repr(float(g_dice)),
            "final_dice": repr(float(f_dice)),
            "delta_dice": repr(float(delta)),
            "gt_foreground_pixels": int(gt_bin.sum()),
            "global_fg_pixels": int(g_bin.sum()),
            "final_fg_pixels": int(f_bin.sum()),
        })
        if (i + 1) % 200 == 0:
            say(f"   scored {i+1}/{len(df)} elapsed={time.time()-t0:.0f}s")

    sc = pd.DataFrame(per_rows).sort_values(["dataset", "sample_id"]).reset_index(drop=True)
    E.write_csv(E.ROOT / "reports/tables/phase27_val808_per_sample_scores.csv",
                per_rows,
                ["sample_id", "dataset", "task_id", "group_key", "state_machine_branch",
                 "router_decision", "global_dice", "final_dice", "delta_dice",
                 "gt_foreground_pixels", "global_fg_pixels", "final_fg_pixels"])
    say(f"per-sample scores written: {len(sc)} rows  gt_reads={gt_reads}")

    # ---- point estimates -------------------------------------------------------- #
    d_vec = sc["delta_dice"].astype(np.float64).to_numpy()
    g_vec = sc["global_dice"].astype(np.float64).to_numpy()
    f_vec = sc["final_dice"].astype(np.float64).to_numpy()
    dom_arr = sc["dataset"].to_numpy()
    dom_idx = {d: (dom_arr == d) for d in STRATA}

    dom_point = {}
    for d in STRATA:
        m = dom_idx[d]
        dom_point[d] = {
            "n": int(m.sum()),
            "groups": int(sc.loc[m, "group_key"].nunique()),
            "global_dice": float(g_vec[m].mean()),
            "final_dice": float(f_vec[m].mean()),
            "delta_point": float(d_vec[m].mean()),
        }
    macro_point = float(np.mean([dom_point[d]["delta_point"] for d in STRATA]))

    # ---- domain-stratified GROUP bootstrap (frozen plan replay) ----------------- #
    plan_path = E.CACHE27 / "phase27_val808_bootstrap_plan_v1_0.npz"
    plan_sha = E.sha256_file(plan_path)
    assert plan_sha == "8d32bd3c9b18f03c39128593f287bd21d716d26e11eb90d80f6f9c0d0b450a93", plan_sha
    z = np.load(plan_path)

    gm = pd.read_csv(E.CACHE27 / "phase27_val808_group_manifest_v1_0.csv", dtype=str)
    group_lists = {d: gm.loc[gm.stratum == d]
                   .assign(_gi=lambda x: x.group_index.astype(int))
                   .sort_values("_gi")["group_key"].tolist() for d in STRATA}
    rows_by_group = {}
    for i, r in sc.iterrows():
        rows_by_group.setdefault(r["group_key"], []).append(i)
    grp_members = {g: np.array(sorted(v), dtype=np.int64) for g, v in rows_by_group.items()}

    rep_macro = np.full(N_BOOT, np.nan)
    rep_delta = np.full(N_BOOT, np.nan)
    rep_global = np.full(N_BOOT, np.nan)
    rep_final = np.full(N_BOOT, np.nan)
    rep_dom = {d: np.full(N_BOOT, np.nan) for d in STRATA}

    for b in range(N_BOOT):
        dom_means = []
        pooled_segs = []
        for d in STRATA:
            draws = z[f"{b}:{d}"]
            gl = group_lists[d]
            segs = [grp_members[gl[j]] for j in draws]
            idx = np.concatenate(segs) if segs else np.array([], dtype=np.int64)
            pooled_segs.append(idx)
            rep_dom[d][b] = float(d_vec[idx].mean())
            dom_means.append(rep_dom[d][b])
        rep_macro[b] = float(np.mean(dom_means))
        all_idx = np.concatenate(pooled_segs)
        rep_delta[b] = float(d_vec[all_idx].mean())
        rep_global[b] = float(g_vec[all_idx].mean())
        rep_final[b] = float(f_vec[all_idx].mean())
        if (b + 1) % 500 == 0:
            say(f"   bootstrap {b+1}/{N_BOOT} elapsed={time.time()-t0:.0f}s")

    np.savez_compressed(
        E.CACHE27 / "phase27_val808_bootstrap_replicates.npz",
        rep_macro=rep_macro, rep_delta=rep_delta,
        rep_global=rep_global, rep_final=rep_final,
        **{f"rep_dom_{d}": rep_dom[d] for d in STRATA})

    macro_mean, macro_lo, macro_hi, macro_n = ci(rep_macro)
    dom_ci = {d: ci(rep_dom[d]) for d in STRATA}
    glob_mean, glob_lo, glob_hi, _ = ci(rep_global)
    fin_mean, fin_lo, fin_hi, _ = ci(rep_final)

    # ---- adjudication ----------------------------------------------------------- #
    preservation_asserted = bool(macro_lo is not None and macro_lo > -MARGIN)
    per_domain_harm = {d: bool(dom_ci[d][2] is not None and dom_ci[d][2] < 0.0)
                       for d in STRATA}

    # ---- branch / activation reporting ------------------------------------------ #
    n = len(preds)
    executed = int((preds["router_decision"] == "EXECUTE").sum())
    accepted = int((preds["state_machine_branch"] == "EXECUTE_THEN_ACCEPT").sum())
    rejected = int((preds["state_machine_branch"] == "EXECUTE_THEN_REJECT").sum())
    skipped = int((preds["state_machine_branch"] == "SKIP_GLOBAL").sum())
    forced = int((preds["state_machine_branch"] == "FORCED_SKIP").sum())
    action_available = n - forced
    activation = {
        "nominal_budget": 0.25,
        "action_available_fraction": action_available / n,
        "router_execute_fraction": executed / n,
        "realized_activation_fraction": executed / n,
        "somega_accept_among_executed": (accepted / executed) if executed else None,
        "somega_reject_among_executed": (rejected / executed) if executed else None,
        "state_counts": {
            "FORCED_SKIP": forced, "SKIP_GLOBAL": skipped,
            "EXECUTE_THEN_ACCEPT": accepted, "EXECUTE_THEN_REJECT": rejected,
        },
    }

    # ---- tables ----------------------------------------------------------------- #
    dom_tbl = []
    for d in STRATA:
        p = dom_point[d]
        mean_d, lo_d, hi_d, nb_d = dom_ci[d]
        dom_tbl.append({
            "domain": d, "n": p["n"], "groups": p["groups"],
            "global_dice_point": p["global_dice"],
            "final_dice_point": p["final_dice"],
            "delta_point": p["delta_point"],
            "delta_boot_mean": mean_d,
            "delta_ci_lower": lo_d,
            "delta_ci_upper": hi_d,
            "delta_boot_replicates": nb_d,
            "harm_flag": per_domain_harm[d],
        })
    E.write_csv(E.ROOT / "reports/tables/phase27_preservation_domain_summary.csv",
                dom_tbl,
                ["domain", "n", "groups", "global_dice_point", "final_dice_point",
                 "delta_point", "delta_boot_mean", "delta_ci_lower", "delta_ci_upper",
                 "delta_boot_replicates", "harm_flag"])

    macro_tbl = [{
        "estimand": "MACRO_DOMAIN_EQUAL_WEIGHT_MEAN_DICE_DELTA",
        "macro_point": macro_point,
        "macro_boot_mean": macro_mean,
        "macro_ci_lower": macro_lo,
        "macro_ci_upper": macro_hi,
        "margin": MARGIN,
        "criterion": "lower 95% CI bound > -0.005 (strict)",
        "preservation_asserted": preservation_asserted,
        "global_dice_boot_mean": glob_mean,
        "global_dice_ci_lower": glob_lo,
        "global_dice_ci_upper": glob_hi,
        "final_dice_boot_mean": fin_mean,
        "final_dice_ci_lower": fin_lo,
        "final_dice_ci_upper": fin_hi,
        "n_boot": N_BOOT,
        "bootstrap_plan_sha256": plan_sha,
    }]
    E.write_csv(E.ROOT / "reports/tables/phase27_preservation_macro_bootstrap.csv",
                macro_tbl,
                ["estimand", "macro_point", "macro_boot_mean", "macro_ci_lower",
                 "macro_ci_upper", "margin", "criterion", "preservation_asserted",
                 "global_dice_boot_mean", "global_dice_ci_lower", "global_dice_ci_upper",
                 "final_dice_boot_mean", "final_dice_ci_lower", "final_dice_ci_upper",
                 "n_boot", "bootstrap_plan_sha256"])

    # ---- audits ----------------------------------------------------------------- #
    summary = {
        "artifact": "phase27_phaseB_scoring_summary",
        "phase": "27",
        "classification": E.CLASSIFICATION,
        "method": E.METHOD,
        "execution_phase": "PHASE_B",
        "evidence_class": E.EVIDENCE_CLASS,
        "canonical_scorer": "src.metrics.evaluation_metrics.dice(binary_confusion_counts)",
        "canonical_scorer_eps": 1e-7,
        "gt_construction": "full_field_gt: NEAREST resize to 512 + centre pad, binary = (arr > 0)",
        "population_n": int(n),
        "val808_gt_reads": gt_reads,
        "val808_images_read": 0,
        "prediction_artifact_sha256": pred_now,
        "prediction_artifact_verified": True,
        "estimand": "MACRO_DOMAIN_EQUAL_WEIGHT_MEAN_DICE_DELTA",
        "macro_point": macro_point,
        "macro_ci_lower": macro_lo,
        "macro_ci_upper": macro_hi,
        "margin": MARGIN,
        "preservation_asserted": preservation_asserted,
        "per_domain_harm": per_domain_harm,
        "activation": activation,
        "device_note": "scoring is CPU artifact-level only (no model forward)",
        "bootstrap_plan_sha256": plan_sha,
        "bootstrap_replayed_frozen_plan": True,
        "secondary_metrics": "NOT_REPORTED__SEMANTICS_NOT_FROZEN (IoU/precision/recall withheld; Dice is primary)",
        "compute_label": "ANALYTICAL MAC LOWER BOUND",
        "elapsed_seconds": round(time.time() - t0, 1),
        "all_pass": True,
    }
    E.write_json(E.AUD / "phase27_phaseB_scoring_summary.json", summary)

    result = {
        "artifact": "phase27_preservation_result",
        "phase": "27",
        "classification": E.CLASSIFICATION,
        "method": E.METHOD,
        "evidence_class": E.EVIDENCE_CLASS,
        "estimand": "MACRO_DOMAIN_EQUAL_WEIGHT_MEAN_DICE_DELTA",
        "macro_ci": [macro_lo, macro_hi],
        "macro_point": macro_point,
        "margin": MARGIN,
        "criterion": "lower 95% CI bound > -0.005 (strict)",
        "preservation_asserted": preservation_asserted,
        "per_domain": dom_tbl,
        "per_domain_harm": per_domain_harm,
        "any_domain_harm": any(per_domain_harm.values()),
        "no_policy_selection": True,
        "no_threshold_change": True,
        "no_training": True,
        "holdout_opened": False,
        "test_opened": False,
        "frozen_before_outcomes": True,
    }
    E.write_json(E.AUD / "phase27_preservation_result.json", result)

    say("")
    say("=" * 74)
    say(f"PHASE B COMPLETE  n={n}  GT reads={gt_reads}")
    say(f"macro-domain delta point = {macro_point:+.6f}")
    say(f"macro 95% CI = [{macro_lo:+.6f}, {macro_hi:+.6f}]  margin=-{MARGIN}")
    for d in STRATA:
        say(f"   {d:7s} n={dom_point[d]['n']:3d} groups={dom_point[d]['groups']:3d} "
            f"delta={dom_point[d]['delta_point']:+.6f} "
            f"CI=[{dom_ci[d][1]:+.6f},{dom_ci[d][2]:+.6f}] harm={per_domain_harm[d]}")
    say(f"PRESERVATION_ASSERTED = {preservation_asserted}")
    say(f"activation: {activation['state_counts']}  "
        f"realized={activation['realized_activation_fraction']:.4f}")
    say(f"elapsed={time.time()-t0:.0f}s")
    say("=" * 74)
    say("PHASE27_PHASE_B_COMPLETE__SCORED_AND_ADJUDICATED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
