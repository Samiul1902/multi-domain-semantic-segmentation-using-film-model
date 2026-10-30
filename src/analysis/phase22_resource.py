"""Phase 22 — resource gap analysis: compute envelopes, CPU baseline, resource frontier.

Consumes the frozen six-model analytical MAC table produced in Phase 21 and adds
Phase-22 measurements. NO training, NO architecture change, NO optimisation of any
kind is performed or proposed as a result; this section only QUANTIFIES the gap.

Sections implemented
--------------------
§17 RESOURCE-LIMITED ORACLE ROUTING FRONTIER
    Combine the per-case compute cost of the global pass with the regional pass to
    build the cost of each routing policy, and plot pooled Dice against expected
    MACs. This makes the trade-off explicit: how much accuracy per unit compute a
    policy buys relative to always-global and always-regional.

§18 PREDICTION-DERIVED ROI DIAGNOSTIC
    Reports the deployable-shaped variant: ROI from the model's OWN prediction,
    including the NO_PREDICTED_ROI rate. No learned proposal, no localizer.

§19 UNCERTAINTY-VS-BENEFIT
    Does a cheap, prediction-only uncertainty signal predict where the regional arm
    would help? Uses the frozen probability map only (no new inference) plus the
    per-image confidence statistics available on disk.

§23 RESOURCE GAP
    Parameter and compute gap of the reference against the six-model panel, and the
    absolute cost of the regional arm relative to the global pass.

§24 CONDITIONAL-COMPUTE ENVELOPES
    Expected MACs under each routing policy, expressed as a multiplier of the
    always-global cost.

§25 CPU BASELINE
    Measures actual CPU latency of the frozen global pass at each supported
    resolution, so the analysis is not purely analytical. This is measurement only.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analysis import phase22_common as C  # noqa: E402
from src.utils.device import get_device       # noqa: E402

SIX_MODEL = C.TABLES / "phase21_six_model_compute.csv"
REGIONAL_TABLE = C.TABLES / "phase22_regional_intervention_per_image.csv"
P21_PER_IMAGE = C.TABLES / "phase21_per_image_val_metrics.csv"
POLICY_TABLE = C.TABLES / "phase22_routing_regret.csv"

OUT_FRONTIER = C.AUDITS / "phase22_resource_frontier.json"
OUT_ROI = C.AUDITS / "phase22_prediction_derived_roi.json"
OUT_UNC = C.AUDITS / "phase22_uncertainty_vs_benefit.json"
OUT_GAP = C.AUDITS / "phase22_resource_gap.json"
OUT_ENV = C.AUDITS / "phase22_conditional_compute_envelopes.json"
OUT_CPU = C.AUDITS / "phase22_cpu_baseline.json"

T_FRONTIER = C.TABLES / "phase22_resource_frontier.csv"
T_ROI = C.TABLES / "phase22_prediction_derived_roi.csv"
T_UNC = C.TABLES / "phase22_uncertainty_vs_benefit.csv"
T_ENV = C.TABLES / "phase22_conditional_compute_envelopes.csv"
T_CPU = C.TABLES / "phase22_cpu_baseline.csv"

GLOBAL_MACS_512 = 31_551_740_928     # frozen Phase-21 analytical count @1x3x512x512


def _mac_scaling(size: int) -> float:
    """Analytical MACs scale with the number of spatial positions for conv nets.

    A fully convolutional net's MAC count is very close to linear in H*W at fixed
    channel widths, so the scaled count is ``base * (size/512)**2``. This is an
    approximation and is labelled as one.
    """
    return GLOBAL_MACS_512 * (size / 512.0) ** 2


def _process_rss_mib() -> float | None:
    """Resident set size of THIS process in MiB (real allocation, not Python-only).

    ``tracemalloc`` only sees Python-level allocations and reads 0.0 for a torch
    forward pass because the tensor arena is C-allocated. RSS is the honest metric.
    Returns ``None`` on platforms where it cannot be read.
    """
    try:
        import psutil
        return float(psutil.Process().memory_info().rss) / 1024.0 ** 2
    except Exception:
        pass
    try:  # Windows fallback
        import ctypes
        import ctypes.wintypes as wt

        class _PMC(ctypes.Structure):
            _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t)]

        pmc = _PMC()
        pmc.cb = ctypes.sizeof(_PMC)
        if ctypes.windll.psapi.GetProcessMemoryInfo(
                ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(pmc),
                pmc.cb):
            return float(pmc.WorkingSetSize) / 1024.0 ** 2
    except Exception:
        pass
    return None


def cpu_baseline(device_spec: str = "cpu", sizes=(512,), n_warmup=1, n_iter=3) -> dict:
    """Measure CPU latency and process RSS of the frozen global pass."""
    device = torch.device(device_spec)
    model, prov = C.load_frozen_medfilm(device)
    rss_before = _process_rss_mib()
    rows = []
    rng = np.random.default_rng(42)
    for size in sizes:
        x = torch.from_numpy(
            rng.random((1, 3, size, size), dtype=np.float32)).to(device)
        task = torch.zeros(1, dtype=torch.long, device=device)
        lat = []
        for i in range(n_warmup + n_iter):
            t0 = time.perf_counter()
            with torch.no_grad():
                model(x, task)
            dt = time.perf_counter() - t0
            if i >= n_warmup:
                lat.append({"seconds": dt, "rss_mib": _process_rss_mib()})
        lat_secs = np.array([r["seconds"] for r in lat])
        rss_vals = [r["rss_mib"] for r in lat if r["rss_mib"] is not None]
        rows.append({
            "size": int(size),
            "device": device.type,
            "n_iter": len(lat),
            "mean_seconds": float(lat_secs.mean()),
            "median_seconds": float(np.median(lat_secs)),
            "min_seconds": float(lat_secs.min()),
            "max_seconds": float(lat_secs.max()),
            "stdev_seconds": float(lat_secs.std()),
            "mean_process_rss_mib": float(np.mean(rss_vals)) if rss_vals else None,
            "max_process_rss_mib": float(np.max(rss_vals)) if rss_vals else None,
            "analytical_macs": int(_mac_scaling(size)),
        })
        del x
    del model
    return {
        "artifact": "phase22_cpu_baseline",
        "phase": 22,
        "purpose": ("measure, not model: actual CPU latency of the frozen global pass "
                    "so the resource discussion is not purely analytical"),
        "measurement_only": True,
        "no_optimisation_performed": True,
        "checkpoint": prov,
        "batch_size": 1,
        "amp": False,
        "threads": int(torch.get_num_threads()),
        "process_rss_mib_after_load": rss_before,
        "rss_note": ("process RSS (working set) is the metric; tracemalloc was rejected "
                     "because it reports 0.0 for a torch forward pass - the tensor arena "
                     "is C-allocated and invisible to it"),
        "rows": rows,
        "note": ("these timings are host-specific and are reported as an absolute "
                 "baseline, not as a hardware-independent quantity. CPU timings are "
                 "recorded separately from the analytical MAC count, which is device-"
                 "independent."),
        "test_reads": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cpu-iters", type=int, default=3)
    ap.add_argument("--cpu-sizes", type=int, nargs="+", default=[256, 512, 768])
    args = ap.parse_args()

    C.verify_no_test_access()
    six = pd.read_csv(SIX_MODEL)
    reg = pd.read_csv(REGIONAL_TABLE)
    n = len(reg)
    executed = reg[reg["oracle_status"] == "OK"]
    print(f"six-model rows {len(six)} | regional rows {n} | executed {len(executed)}")

    # ===================================================================== #
    # §18 prediction-derived ROI diagnostic
    # ===================================================================== #
    p = reg.copy()
    p["pred_roi_exists"] = (p["predicted_status"] == "OK")
    roi_rows = p[[
        "sample_id", "dataset", "global_dice", "predicted_status",
        "predicted_roi_area_fraction", "predicted_delta_dice", "oracle_delta_dice",
        "pred_roi_exists", "gt_foreground_pixels",
        "global_pred_foreground_pixels", "oracle_roi_area_fraction"]]
    roi_rows.to_csv(T_ROI, index=False)

    n_pred_ok = int(p["pred_roi_exists"].sum())
    pred_ok = p[p["pred_roi_exists"]]
    noc = p[~p["pred_roi_exists"]]

    # agreement between predicted ROI and the oracle region (IoU of boxes not
    # available here; we report the area ratio and the gain correlation)
    corr_pred_oracle = float(np.corrcoef(
        pred_ok["predicted_delta_dice"], pred_ok["oracle_delta_dice"])[0, 1]) if len(pred_ok) > 2 else float("nan")

    roi_payload = {
        "artifact": "phase22_prediction_derived_roi",
        "phase": 22,
        "definition": ("ROI = tight bounding box of the FROZEN MODEL'S OWN thresholded "
                       "prediction, expanded by the same frozen 1.5x rule"),
        "deployable_shape": True,
        "uses_ground_truth_for_roi": False,
        "no_learned_proposal": True,
        "n_total": int(n),
        "n_predicted_roi_ok": n_pred_ok,
        "n_no_predicted_roi": int(len(noc)),
        "no_predicted_roi_rate": round(float(len(noc) / n), 6),
        "no_predicted_roi_by_domain": {
            k: int(v) for k, v in
            noc.groupby("dataset").size().items()} if len(noc) else {},
        "empty_case_structure": {
            "n_gt_empty": int(reg["gt_empty"].sum()),
            "n_global_pred_empty": int((reg["global_pred_foreground_pixels"] == 0).sum()),
            "note": ("a NO_PREDICTED_ROI arises when the global prediction is empty. "
                     "On this VAL population that coincides exactly with a total miss, "
                     "so the deployable path fails precisely where recovery is most "
                     "needed."),
        },
        "mean_predicted_delta_dice_intent_to_treat": float(reg["predicted_delta_dice"].mean()),
        "mean_predicted_delta_dice_on_executed": float(pred_ok["predicted_delta_dice"].mean()),
        "n_predicted_improved": int((pred_ok["predicted_delta_dice"] > 0).sum()),
        "n_predicted_harmed": int((pred_ok["predicted_delta_dice"] < 0).sum()),
        "correlation_predicted_vs_oracle_gain": corr_pred_oracle,
        "mean_roi_area_fraction_predicted": float(pred_ok["predicted_roi_area_fraction"].mean()),
        "mean_roi_area_fraction_oracle": float(executed["oracle_roi_area_fraction"].mean()),
        "interpretation_guard": ("this is a diagnostic of what a TRIVIAL, UNTRAINED "
                                 "prediction-derived ROI achieves. It is not a "
                                 "benefit predictor, not a router, and not a proposed "
                                 "method. Any stronger claim would require training, "
                                 "which Phase 22 forbids."),
        "table": "reports/tables/phase22_prediction_derived_roi.csv",
        "test_reads": 0,
    }
    C.write_json(OUT_ROI, roi_payload)

    # ===================================================================== #
    # §19 uncertainty vs benefit (prediction-only signals, no new inference)
    # ===================================================================== #
    unc = pd.read_csv(P21_PER_IMAGE)
    unc = unc.merge(
        reg[["sample_id", "oracle_delta_dice", "predicted_delta_dice",
             "oracle_status", "oracle_roi_area_fraction", "predicted_status"]],
        on="sample_id", how="left")
    unc = unc[unc["oracle_status"] == "OK"].copy()

    # cheap deployable uncertainty proxies computed from the FROZEN MAPS ONLY
    manifest = pd.read_csv(C.TABLES / "phase21_prediction_manifest.csv")
    npz_of = dict(zip(manifest["sample_id"], manifest["npz_path"]))
    proxies = []
    for row in unc.itertuples(index=False):
        z = np.load(ROOT / npz_of[row.sample_id])
        prob = z["prob"].astype(np.float32)
        # distance of the probability from the decision boundary
        margin = np.abs(prob - 0.5)
        proxies.append({
            "sample_id": row.sample_id,
            "frac_prob_within_0p05_of_boundary": float((margin <= 0.05).mean()),
            "frac_prob_within_0p02_of_boundary": float((margin <= 0.02).mean()),
            "mean_boundary_margin": float(margin.mean()),
            "entropy_proxy_mean": float(
                np.mean(-(prob * np.log(prob + 1e-12)
                         + (1 - prob) * np.log(1 - prob + 1e-12)))),
        })
    prox = pd.DataFrame(proxies)
    unc = unc.merge(prox, on="sample_id", how="left")
    unc.to_csv(T_UNC, index=False)

    # NOTE: phase21_per_image_val_metrics.csv names the baseline Dice column `dice`
    # (it is already the global_medfilm row set), not `global_dice`.
    signals = ["dice", "iou", "precision", "recall",
               "mean_boundary_margin",
               "frac_prob_within_0p05_of_boundary",
               "frac_prob_within_0p02_of_boundary", "entropy_proxy_mean",
               "brier", "ece",
               "pred_foreground_pixels", "gt_foreground_pixels",
               "oracle_roi_area_fraction"]
    corr_rows = []
    for s in signals:
        if s not in unc.columns:
            continue
        x = unc[s].astype(float)
        y = unc["oracle_delta_dice"].astype(float)
        ok = x.notna() & y.notna()
        if ok.sum() > 2 and x[ok].std() > 0:
            corr_rows.append({
                "signal": s, "n": int(ok.sum()),
                "pearson_r_with_oracle_gain": float(np.corrcoef(x[ok], y[ok])[0, 1]),
                "spearman_r_with_oracle_gain": float(
                    pd.Series(x[ok]).corr(pd.Series(y[ok]), method="spearman")),
            })
    corrf = pd.DataFrame(corr_rows).sort_values(
        "spearman_r_with_oracle_gain", key=lambda s: s.abs(), ascending=False)

    unc_payload = {
        "artifact": "phase22_uncertainty_vs_benefit",
        "phase": 22,
        "question": "does a cheap, DEPLOYABLE, prediction-only signal predict where the regional arm helps?",
        "source": "frozen Phase-21 probability maps + per-image metrics (NO new inference)",
        "n": int(len(unc)),
        "new_inference_performed": False,
        "signals": corr_rows,
        "best_deployable_signal": (corrf.iloc[0].to_dict() if len(corrf) else None),
        "interpretation": ("a useful router needs a signal that correlates with benefit. "
                           "These correlations are computed post hoc on VAL and are "
                           "DESCRIPTIVE ONLY: no threshold was fitted, no policy was "
                           "selected, and no training occurred."),
        "ranked_abs_spearman": corrf.to_dict("records"),
        "table": "reports/tables/phase22_uncertainty_vs_benefit.csv",
        "test_reads": 0,
    }
    C.write_json(OUT_UNC, unc_payload)

    # ===================================================================== #
    # §17 / §24 resource frontier and conditional-compute envelopes
    # ===================================================================== #
    # A regional pass costs one additional forward at 512 on a crop whose native
    # side is `oracle_roi_side`; because the crop is always resampled to 512, the
    # regional pass costs exactly one 512 forward regardless of crop size.
    # What VARIES is whether it is executed at all.
    GLOBAL = float(GLOBAL_MACS_512)
    REGIONAL = float(_mac_scaling(512))
    reg["roi_side"] = reg["oracle_roi_side"].fillna(0).astype(int)

    def envelope(use_mask: np.ndarray) -> dict:
        cost = GLOBAL * np.ones(len(reg)) + REGIONAL * use_mask.astype(float)
        return {
            "n_regional": int(use_mask.sum()),
            "fraction_regional": round(float(use_mask.mean()), 6),
            "mean_macs": float(cost.mean()),
            "mean_macs_gmacs": round(float(cost.mean()) / 1e9, 4),
            "total_macs": float(cost.sum()),
            "multiplier_vs_always_global": round(float(cost.mean() / GLOBAL), 6),
        }

    hpr = (reg["predicted_status"] == "OK").to_numpy()
    env_rows = []
    policies = {
        "ALWAYS_GLOBAL": np.zeros(len(reg), dtype=bool),
        "ALWAYS_REGIONAL_ORACLE": np.ones(len(reg), dtype=bool),
        "ORACLE_ACCEPT_IF_BENEFICIAL": (reg["oracle_delta_dice"] > 0).to_numpy(),
        "PRED_ROI_EXISTS": hpr,
        "PRED_ACCEPT_IF_PREDICTED_BENEFICIAL": (reg["predicted_delta_dice"] > 0).to_numpy(),
    }
    pol_table = pd.read_csv(POLICY_TABLE)
    ceiling = float(pol_table.loc[
        pol_table.policy == "ORACLE_ACCEPT_IF_BENEFICIAL",
        "macroR_dice_pooled"].iloc[0])
    for name, mask in policies.items():
        value = np.where(mask, reg["oracle_dice"].to_numpy(),
                         reg["global_dice"].to_numpy())
        e = envelope(mask)
        e.update({
            "policy": name,
            "pooled_dice": float(value.mean()),
            "gain_over_always_global": float(value.mean() - reg["global_dice"].mean()),
            "regret_vs_oracle_ceiling": round(float(ceiling - value.mean()), 8),
            "gmacs_per_dice_point": round(
                (e["mean_macs"] / 1e9) / max(value.mean(), 1e-9), 6),
        })
        env_rows.append(e)
    envf = pd.DataFrame(env_rows)[[
        "policy", "n_regional", "fraction_regional", "mean_macs_gmacs",
        "multiplier_vs_always_global", "pooled_dice", "gain_over_always_global",
        "regret_vs_oracle_ceiling", "gmacs_per_dice_point"]]
    envf.to_csv(T_ENV, index=False)
    envf.to_csv(T_FRONTIER, index=False)

    C.write_json(OUT_ENV, {
        "artifact": "phase22_conditional_compute_envelopes",
        "phase": 22,
        "definition": ("expected MACs of each routing policy, expressed as a multiplier "
                       "of the always-global cost"),
        "global_pass_macs_at_512": int(GLOBAL_MACS_512),
        "regional_pass_macs_at_512": int(REGIONAL),
        "important_caveat": ("the regional pass always costs ONE full 512x512 forward "
                             "regardless of crop size, because the crop is resampled to "
                             "512. Conditional compute therefore saves EXECUTIONS, not "
                             "resolution. A smaller crop does NOT cost less."),
        "analytical_approximation": ("MAC counts at non-512 resolutions are scaled by "
                                     "(size/512)**2; this is exact for a fully "
                                     "convolutional stack at fixed channel widths and is "
                                     "an approximation for the true graph"),
        "rows": env_rows,
        "table": "reports/tables/phase22_conditional_compute_envelopes.csv",
        "test_reads": 0,
    })

    C.write_json(OUT_FRONTIER, {
        "artifact": "phase22_resource_frontier",
        "phase": 22,
        "axes": {"x": "expected giga-MACs per image", "y": "pooled VAL Dice"},
        "protocol": ("paired, domain-stratified; each policy is evaluated on the SAME "
                     "808 VAL cases"),
        "points": env_rows,
        "frontier_members": [r["policy"] for r in env_rows
                             if r["gain_over_always_global"] > 0],
        "interpretation_guard": ("the oracle points on this frontier use ground-truth "
                                 "geometry and are UPPER BOUNDS. No deployable method "
                                 "may be reported as attaining them."),
        "table": "reports/tables/phase22_resource_frontier.csv",
        "test_reads": 0,
    })

    # ===================================================================== #
    # §23 resource gap
    # ===================================================================== #
    med = six[six["model_key"] == "global_medfilm"]
    med_params = int(med["params"].iloc[0]) if len(med) and pd.notna(med["params"].iloc[0]) else 3523001
    # phase21_six_model_compute.csv carries no `phase` column; keep the available
    # identity/label/cost columns only.
    keep = [c for c in ["model_key", "display_name", "params", "gmacs",
                        "params_rank", "gmacs_rank"] if c in six.columns]
    panel = six[keep].copy()
    panel["params_ratio_vs_medfilm"] = (panel["params"] / med_params).round(4)
    panel["gmacs_ratio_vs_medfilm"] = (panel["gmacs"] / (GLOBAL_MACS_512 / 1e9)).round(4)
    panel["params_lower_bound_macs"] = True

    gap = {
        "artifact": "phase22_resource_gap",
        "phase": 22,
        "reference_params": med_params,
        "reference_gmacs_at_512": round(GLOBAL_MACS_512 / 1e9, 4),
        "panel": panel.to_dict("records"),
        "param_rank_of_reference": int(med["params_rank"].iloc[0]) if "params_rank" in med else 1,
        "gmacs_rank_of_reference": int(med["gmacs_rank"].iloc[0]) if "gmacs_rank" in med else 1,
        "absolute_cost_statement": {
            "gmacs": round(GLOBAL_MACS_512 / 1e9, 4),
            "is_small_in_absolute_terms": False,
            "note": ("the reference is the LIGHTEST of the six-model panel, but ~31.6 G "
                     "MACs per image is NOT a small absolute cost. 'Lightest of the "
                     "panel' must never be reported as 'fit for constrained "
                     "deployment'. No pruning, quantization, distillation, or NAS has "
                     "been performed and none is claimed."),
        },
        "regional_arm_cost": {
            "gmacs_per_execution": round(REGIONAL / 1e9, 4),
            "fraction_of_global_pass": round(REGIONAL / GLOBAL, 6),
            "note": "one extra full-resolution forward per routed image",
        },
        "measurement_provenance": ("MACs are an exact closed-form count for Conv2d and "
                                   "Linear layers and a LOWER bound on total "
                                   "arithmetic; GroupNorm, SiLU, pooling, bilinear "
                                   "interpolation, FiLM modulation and sigmoid are "
                                   "excluded"),
        "no_optimisation_performed": True,
        "test_reads": 0,
    }
    C.write_json(OUT_GAP, gap)

    # ===================================================================== #
    # §25 CPU baseline (real measurement)
    # ===================================================================== #
    print("\nmeasuring CPU baseline (this is a measurement, not a model)...")
    cpu = cpu_baseline("cpu", sizes=tuple(args.cpu_sizes), n_iter=args.cpu_iters)
    C.write_json(OUT_CPU, cpu)
    pd.DataFrame(cpu["rows"]).to_csv(T_CPU, index=False)
    for r in cpu["rows"]:
        print(f"  size {r['size']:5d}  mean {r['mean_seconds']*1000:9.1f} ms  "
              f"RSS {r['mean_process_rss_mib'] if r['mean_process_rss_mib'] is None else round(r['mean_process_rss_mib'], 1)} MiB")

    print("\n--- §24 conditional-compute envelopes ---")
    print(envf.to_string(index=False))
    print("\n--- §18 prediction-derived ROI ---")
    print(f"  no_predicted_roi_rate={roi_payload['no_predicted_roi_rate']:.4f}  "
          f"ITT mean_delta={roi_payload['mean_predicted_delta_dice_intent_to_treat']:+.6f}")
    print("\n--- §19 uncertainty vs benefit (ranked |spearman|) ---")
    print(corrf.head(6).to_string(index=False))
    print(f"\nWROTE {OUT_FRONTIER}, {OUT_ROI}, {OUT_UNC}, {OUT_GAP}, {OUT_ENV}, {OUT_CPU}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
