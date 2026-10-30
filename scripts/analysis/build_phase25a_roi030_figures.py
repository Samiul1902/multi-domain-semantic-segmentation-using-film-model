"""Phase 25A (CANONICAL RERUN) — ROI-0.30 canonical training figures.

Produces the 9 required ROI-0.30 figures into
``reports/figures/phase25a_regional_refiner/`` with the ``p25a_roi030_`` prefix.
The historical ROI-0.50 figures (``p25a_*``) are NOT overwritten.

No OOF benefit gallery is produced.

Writes:
    reports/figures/phase25a_regional_refiner/FIG_MANIFEST_ROI030.json

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/build_phase25a_roi030_figures.py
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures" / "phase25a_regional_refiner"
EXP_ROOT = ROOT / "experiments" / "phase25a_barr_regional_refiner_v1_1_roi030"
CACHE = ROOT / "data_cache" / "phase25a_barr_roi030_cache"
UTC = datetime.now(timezone.utc).isoformat()

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 110, "font.size": 9,
    "axes.grid": True, "grid.alpha": 0.3, "axes.spines.top": False,
    "axes.spines.right": False, "figure.facecolor": "white",
    "savefig.facecolor": "white", "savefig.bbox": "tight",
})

FOLD_COLORS = {"fold0": "#1f77b4", "fold1": "#d62728", "fold2": "#2ca02c"}
BANNER = ("PHASE 25A CANONICAL — ROI PROPOSAL THRESHOLD = 0.30 "
          "(supersedes the noncanonical ROI-0.50 run)")


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_history(run: str) -> pd.DataFrame:
    d = EXP_ROOT / ("final_refit" if run == "final" else run)
    return pd.read_csv(d / "history.csv")


def emit(fig, name: str) -> str:
    p = FIG / f"{name}.png"
    fig.savefig(p)
    plt.close(fig)
    return name


def main() -> int:
    FIG.mkdir(parents=True, exist_ok=True)
    produced: list[str] = []
    h = {r: load_history(r) for r in ("fold0", "fold1", "fold2", "final")}

    # 1-3. per-fold loss curves ------------------------------------------- #
    for run in ("fold0", "fold1", "fold2"):
        df = h[run]
        fig, ax = plt.subplots(figsize=(7.2, 3.6))
        ax.plot(df["epoch"], df["train_loss"], label="FIT train loss", color="#1f77b4", lw=1.6)
        ax.plot(df["epoch"], df["early_stop_loss"], label="EARLY_STOP loss", color="#d62728", lw=1.6)
        ax.plot(df["epoch"], df["train_BCE"], label="FIT BCE", color="#7f7f7f", lw=1.0, ls="--")
        ax.plot(df["epoch"], df["train_Dice_loss"], label="FIT Dice loss", color="#bcbd22",
                lw=1.0, ls=":")
        best = int(df.loc[df["early_stop_loss"].idxmin(), "epoch"])
        ax.axvline(best, color="#2ca02c", ls="-.", lw=1.2)
        ax.annotate(f"best epoch {best}", xy=(best, ax.get_ylim()[1]),
                    xytext=(3, -12), textcoords="offset points", color="#2ca02c", fontsize=8)
        ax.set_xlabel("epoch")
        ax.set_ylabel("loss")
        ax.set_title(f"{run} — ROI-0.30 training curve\n{BANNER}", fontsize=8.5)
        ax.legend(fontsize=7, loc="upper right")
        produced.append(emit(fig, f"p25a_roi030_{run}_loss_curve"))

    # 4. fold comparison ---------------------------------------------------- #
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.8))
    for run in ("fold0", "fold1", "fold2"):
        df = h[run]
        axes[0].plot(df["epoch"], df["train_loss"], color=FOLD_COLORS[run], lw=1.4, label=run)
        axes[1].plot(df["epoch"], df["early_stop_loss"], color=FOLD_COLORS[run], lw=1.4, label=run)
    axes[0].set_title("FIT train loss", fontsize=9)
    axes[1].set_title("EARLY_STOP loss (checkpoint selection)", fontsize=9)
    for ax in axes:
        ax.set_xlabel("epoch")
        ax.set_ylabel("loss")
        ax.legend(fontsize=7)
    fig.suptitle(f"Three-fold ROI-0.30 regional-refiner comparison\n{BANNER}", fontsize=8.5)
    produced.append(emit(fig, "p25a_roi030_fold_training_comparison"))

    # 5. best epoch summary ------------------------------------------------- #
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    runs = ["fold0", "fold1", "fold2"]
    bests = [int(h[r].loc[h[r]["early_stop_loss"].idxmin(), "epoch"]) for r in runs]
    losses = [float(h[r]["early_stop_loss"].min()) for r in runs]
    ax.bar(runs, bests, color=[FOLD_COLORS[r] for r in runs])
    for i, (b, l) in enumerate(zip(bests, losses)):
        ax.text(i, b + 0.4, f"ep {b}\nloss {l:.4f}", ha="center", fontsize=8)
    med = int(np.sort(bests)[1])
    ax.axhline(med, color="#9467bd", ls="--", lw=1.3,
               label=f"integer median = {med} (FINAL_REFIT_EPOCHS_ROI030)")
    ax.set_ylabel("best epoch (min EARLY_STOP loss)")
    ax.set_title(f"Selected epoch per ROI-0.30 fold\n{BANNER}", fontsize=8.5)
    ax.legend(fontsize=7)
    produced.append(emit(fig, "p25a_roi030_best_epoch_summary"))

    # 6. final refit curve -------------------------------------------------- #
    df = h["final"]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.plot(df["epoch"], df["train_loss"], color="#ff7f0e", lw=1.8, label="final refit train loss")
    ax.plot(df["epoch"], df["train_BCE"], color="#7f7f7f", lw=1.0, ls="--", label="BCE")
    ax.plot(df["epoch"], df["train_Dice_loss"], color="#bcbd22", lw=1.0, ls=":", label="Dice loss")
    ax.set_xlabel("epoch")
    ax.set_ylabel("loss")
    ax.set_title(f"R_psi_final refit — ROI-0.30 ({len(df)} epochs, no early stopping)\n{BANNER}",
                 fontsize=8.5)
    ax.legend(fontsize=7)
    produced.append(emit(fig, "p25a_roi030_final_refit_training_curve"))

    # 7. action availability ------------------------------------------------ #
    aa = pd.read_csv(TAB / "phase25a_roi030_action_availability_by_domain.csv")
    aa = aa[aa["domain"] != "ALL"]
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    x = np.arange(len(aa))
    ax.bar(x, aa["action_available"], color="#2ca02c", label="action_available")
    ax.bar(x, aa["action_unavailable_global_empty"], bottom=aa["action_available"],
           color="#d62728", label="ACTION_UNAVAILABLE_GLOBAL_EMPTY (FORCED_SKIP)")
    for i, row in enumerate(aa.itertuples()):
        ax.text(i, row.router_development_total + 12, f"{row.availability_fraction:.3f}",
                ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(aa["domain"])
    ax.set_ylabel("ROUTER_DEVELOPMENT samples")
    ax.set_title(f"Action availability by domain (ROI proposal threshold 0.30)\n{BANNER}",
                 fontsize=8.5)
    ax.legend(fontsize=7)
    produced.append(emit(fig, "p25a_roi030_action_availability_by_domain"))

    # 8. architecture summary ----------------------------------------------- #
    ra = json.loads((AUD / "phase25a_resource_accounting.json").read_text(encoding="utf-8"))
    layers = sorted(ra["per_layer_macs"], key=lambda r: -r["macs"])[:14]
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.2))
    names = [l["layer"] for l in layers][::-1]
    vals = [l["macs"] / 1e6 for l in layers][::-1]
    axes[0].barh(names, vals, color="#1f77b4")
    axes[0].set_xlabel("MACs (millions)")
    axes[0].set_title("Top MAC contributors", fontsize=9)
    axes[0].tick_params(axis="y", labelsize=6.5)
    axes[1].axis("off")
    txt = (f"BARRRegionalRefinerV1  (R_psi)\n"
           f"input  : 1 x 4 x 256 x 256  [R,G,B,p_global_crop]\n"
           f"output : 1 x 1 x 256 x 256  (raw logits)\n"
           f"channels (active) : [16, 32, 64, 96, 128]\n"
           f"channels (rejected): [16, 32, 64, 128, 192] = 2,317,553 > ceiling\n"
           f"trainable parameters : {ra['trainable_parameters']:,}\n"
           f"hard ceiling         : 2,000,000\n"
           f"analytical MACs      : {ra['analytical_gmacs']:.4f} G\n"
           f"analytical FLOPs     : {ra['analytical_gflops']:.4f} G\n"
           f"vs Phase-21 global   : {ra['context_vs_global']['refiner_over_global_macs_ratio']:.4f}x MACs\n"
           f"host latency         : HOST_SPECIFIC (not a deployment claim)\n"
           f"normalisation        : GroupNorm(8)   activation: SiLU\n"
           f"forbidden            : SE / attention / transformer / FiLM /\n"
           f"                       dropout / deep supervision / pretrained\n")
    axes[1].text(0.0, 0.5, txt, va="center", ha="left", fontsize=8, family="monospace")
    fig.suptitle(f"Regional refiner architecture summary (ROI-0.30 canonical)\n{BANNER}",
                 fontsize=8.5)
    produced.append(emit(fig, "p25a_roi030_refiner_architecture_summary"))

    # 9. crop geometry distribution ----------------------------------------- #
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.6))
    for dom in ("BUSI", "ISIC", "KUB", "KVASIR"):
        meta = pd.read_csv(CACHE / dom / "meta.csv")
        ok = meta[meta["action_available"].astype(bool)]
        if dom == "BUSI":
            axes[0].hist(ok["crop_side_pixels"].astype(float), bins=40, color="#1f77b4")
        axes[1].hist(ok["crop_side_pixels"].astype(float), bins=30, histtype="step",
                     lw=1.4, label=dom)
    axes[0].set_xlabel("crop side (canvas pixels)")
    axes[0].set_ylabel("count")
    axes[0].set_title("Predicted-ROI crop side (ROI thr 0.30, before 256 resize)", fontsize=8.5)
    axes[1].set_xlabel("crop side (canvas pixels)")
    axes[1].set_ylabel("count")
    axes[1].set_title("By domain", fontsize=9)
    axes[1].legend(fontsize=7)
    fig.suptitle(f"Crop geometry distribution — ROI proposal threshold 0.30\n{BANNER}", fontsize=8.5)
    produced.append(emit(fig, "p25a_roi030_crop_geometry_distribution"))

    manifest = {
        "artifact": "phase25a_roi030_figure_manifest",
        "phase": "25A",
        "classification": "CANONICAL_PHASE25A",
        "directory": "reports/figures/phase25a_regional_refiner",
        "roi_proposal_threshold": 0.30,
        "segmentation_output_threshold": 0.50,
        "required": ["p25a_roi030_fold0_loss_curve", "p25a_roi030_fold1_loss_curve",
                     "p25a_roi030_fold2_loss_curve", "p25a_roi030_fold_training_comparison",
                     "p25a_roi030_best_epoch_summary", "p25a_roi030_final_refit_training_curve",
                     "p25a_roi030_action_availability_by_domain",
                     "p25a_roi030_crop_geometry_distribution",
                     "p25a_roi030_refiner_architecture_summary"],
        "produced": produced,
        "figures": {f"{n}.png": sha(FIG / f"{n}.png") for n in produced},
        "contains_paired_gain_or_router_results": False,
        "contains_oof_gallery": False,
        "banner": BANNER,
        "generated_utc": UTC,
    }
    (FIG / "FIG_MANIFEST_ROI030.json").write_text(json.dumps(manifest, indent=1) + "\n",
                                                  encoding="utf-8")
    print(f"produced {len(produced)} ROI-0.30 figures -> {FIG}")
    for n in produced:
        print(f"   {n}.png  {sha(FIG / f'{n}.png')[:16]}...")
    print("PHASE25A_ROI030_FIGURES_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
