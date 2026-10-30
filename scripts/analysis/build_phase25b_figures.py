"""Phase 25B -- required figures (work-order section 21).

Six required figures (one optional).  All are DESCRIPTIVE / SCHEMATIC of the
frozen feature construction -- none carries an experimental result or a
hypothetical performance curve.  Deterministic (fixed seed, no randomness in
content), written as PNG + a manifest with sha256.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

from src.features.barr_pre_refinement_features import (  # noqa: E402
    FEATURE_GRID,
    GROUP_ORDER,
    NATIVE_CHANNELS,
    NUMERIC_DIM,
    REDUCTION_K,
    REDUCTION_OP,
    SCALAR_ORDER,
    TAPS,
    channel_bins,
    feature_group_offsets,
    scalar_definitions,
)

FIG = ROOT / "reports" / "figures" / "phase25b_gt_free_features"
CACHE = ROOT / "data_cache" / "phase25b_barr_pre_refinement_features_v1_2"
UTC = datetime.now(timezone.utc).isoformat()
plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 130, "font.size": 9,
                     "axes.grid": False, "figure.facecolor": "white"})


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(fig, name):
    p = FIG / name
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    return p


# ---------------------------------------------------------------- figure 1
def fig_pipeline():
    """End-to-end GT-free pre-refinement feature construction pipeline."""
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.axis("off")
    stages = [
        ("Frozen Global\nMedFiLM (eval)", "#dbeafe"),
        ("Tap feature maps\nbridge 32x32x256\ndecoder2 256x256x48\ndecoder1 512x512x24",
         "#e0f2fe"),
        ("Channel-adaptive\navg-pool to K=32\n(DETERMINISTIC_\nCHANNEL_ADAPTIVE_\nAVG_POOL_1D_V1)",
         "#ede9fe"),
        ("Global mean +\nROI-aware mean\n(6 logical vectors)", "#fce7f3"),
        ("10 probability\nscalars (GT-free)", "#fef3c7"),
        ("202-D numeric\nfeature vector", "#dcfce7"),
    ]
    x = 0.02
    w = 0.145
    for i, (txt, col) in enumerate(stages):
        ax.add_patch(Rectangle((x, 0.28), w, 0.42, facecolor=col, edgecolor="#334155",
                               lw=1.2, zorder=2))
        ax.text(x + w / 2, 0.49, txt, ha="center", va="center", fontsize=8, zorder=3)
        if i < len(stages) - 1:
            ax.add_patch(FancyArrowPatch((x + w, 0.49), (x + w + 0.035, 0.49),
                                         arrowstyle="-|>", mutation_scale=14,
                                         color="#475569", lw=1.4))
        x += w + 0.035
    ax.text(0.5, 0.86, "Phase 25B -- GT-free, pre-refinement, inference-available "
                       "feature construction", ha="center", fontsize=12, fontweight="bold")
    ax.text(0.5, 0.14, "No GT  ·  no refiner  ·  no router  ·  no post-safety  ·  "
                       "no Dice / DeltaDice  ·  population = ROUTER_DEVELOPMENT (4957)",
            ha="center", fontsize=8.5, color="#334155")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    return save(fig, "p25b_feature_pipeline.png")


# ---------------------------------------------------------------- figure 2
def fig_reduction():
    """Deterministic channel-adaptive average pooling: bins per tap."""
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
    rows = []
    for ax, tap in zip(axes, TAPS):
        C = NATIVE_CHANNELS[tap]
        b = channel_bins(C)
        for j, (s, e) in enumerate(b):
            ax.barh(j, e - s, left=s, height=0.7,
                    color=plt.cm.viridis(j / REDUCTION_K))
        ax.set_xlim(0, C)
        ax.set_ylim(-0.5, REDUCTION_K - 0.5)
        ax.set_title(f"{tap}  (C={C}, K={REDUCTION_K}"
                     + (", overlapping bins)" if C < REDUCTION_K else ", disjoint bins)"))
        ax.set_xlabel("native channel index")
        if tap == "bridge":
            ax.set_ylabel("output bin j")
        rows.append({"tap": tap, "native_C": C, "K": REDUCTION_K,
                     "overlap": C < REDUCTION_K})
    fig.suptitle("DETERMINISTIC_CHANNEL_ADAPTIVE_AVG_POOL_1D_V1 -- "
                 "start_j=floor(j*C/32), end_j=ceil((j+1)*C/32)", fontsize=11)
    fig.tight_layout()
    return save(fig, "p25b_channel_adaptive_reduction.png")


# ---------------------------------------------------------------- figure 3
def fig_group_layout():
    """202-D layout: six 32-D groups + ten scalars."""
    fig, ax = plt.subplots(figsize=(12, 3.0))
    off = feature_group_offsets()["groups"]
    cols = plt.cm.tab20(np.linspace(0, 1, 7))
    for i, g in enumerate(off):
        start = g["start"]
        ax.add_patch(Rectangle((start, 0.35), 32, 0.3, facecolor=cols[i],
                               edgecolor="#334155", lw=1.1))
        ax.text(start + 16, 0.5, g["name"], ha="center", va="center", fontsize=7.5)
        ax.text(start + 16, 0.24, f"[{start}:{start+32}]", ha="center", va="center",
                fontsize=6.5, color="#475569")
    ax.add_patch(Rectangle((192, 0.35), 10, 0.3, facecolor="#fde68a", edgecolor="#334155",
                           lw=1.1))
    ax.text(197, 0.5, "10 scalars", ha="center", va="center", fontsize=7.5)
    ax.text(197, 0.24, "[192:202]", ha="center", va="center", fontsize=6.5, color="#475569")
    ax.set_xlim(0, 202)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xlabel("numeric feature index (202-D total)")
    ax.set_title("202-D numeric feature layout (task embedding appended separately by "
                 "Phase25C to reach 218-D)")
    return save(fig, "p25b_feature_group_layout.png")


# ---------------------------------------------------------------- figure 4
def fig_scalars():
    """Ten scalar descriptors with their threshold roles."""
    fig, ax = plt.subplots(figsize=(11, 4.4))
    defs = scalar_definitions()
    roles = {"ROI_PROPOSAL": "#fca5a5", "SEGMENTATION_OUTPUT": "#93c5fd",
             "THRESHOLD_FREE": "#86efac", "NONE": "#e5e7eb"}
    names = [d["feature_name"] for d in defs][::-1]
    rolec = [roles.get(d["threshold_role"], "#e5e7eb") for d in defs][::-1]
    idx = [192 + i for i in range(10)][::-1]
    ax.barh(range(10), [1] * 10, color=rolec, edgecolor="#334155", lw=1.0)
    for i, (n, ix) in enumerate(zip(names, idx)):
        ax.text(0.02, i, f"{ix}  {n}", va="center", fontsize=8)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_xlim(0, 1)
    handles = [plt.Rectangle((0, 0), 1, 1, fc=c, ec="#334155") for c in roles.values()]
    ax.legend(handles, list(roles.keys()), loc="lower right", fontsize=7.5,
              title="threshold role")
    ax.set_title("Ten GT-free scalar descriptors (indices 192-201)")
    return save(fig, "p25b_scalar_descriptors.png")


# ---------------------------------------------------------------- figure 5
def fig_population():
    """Extraction population by domain + per-domain fold composition."""
    meta = pd.read_csv(CACHE / "metadata.csv")
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
    vc = meta["domain"].value_counts().reindex(["BUSI", "ISIC", "KUB", "KVASIR"])
    axes[0].bar(vc.index, vc.values, color="#60a5fa", edgecolor="#1e3a8a")
    for i, v in enumerate(vc.values):
        axes[0].text(i, v + 30, str(int(v)), ha="center", fontsize=8)
    axes[0].set_title("ROUTER_DEVELOPMENT rows by domain (n=4957)")
    axes[0].set_ylabel("rows")
    ct = pd.crosstab(meta["domain"], meta["outer_fold"]).reindex(
        ["BUSI", "ISIC", "KUB", "KVASIR"])
    ct.plot(kind="bar", stacked=True, ax=axes[1], colormap="Set2", edgecolor="#334155")
    axes[1].set_title("rows by domain x outer fold")
    axes[1].set_ylabel("rows")
    axes[1].legend(fontsize=7)
    fig.tight_layout()
    return save(fig, "p25b_extraction_population.png")


# ---------------------------------------------------------------- figure 6
def fig_integrity():
    """Cache integrity summary: dtype / finiteness / population containment."""
    feats = np.load(CACHE / "features.npy")
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.4))
    axes[0].bar(["rows", "cols"], [feats.shape[0], feats.shape[1]],
                color=["#34d399", "#34d399"], edgecolor="#065f46")
    axes[0].text(0, feats.shape[0] + 40, str(feats.shape[0]), ha="center", fontsize=8)
    axes[0].text(1, feats.shape[1] + 40, str(feats.shape[1]), ha="center", fontsize=8)
    axes[0].set_title(f"matrix shape {feats.shape}")
    h = axes[1].hist(feats.ravel(), bins=80, color="#a78bfa", edgecolor="#4c1d95")
    axes[1].set_title("value distribution (all finite)")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("feature value")
    per_col_std = feats.std(axis=0)
    axes[2].plot(per_col_std, color="#f97316", lw=1.2)
    axes[2].set_title("per-column std (no selection applied)")
    axes[2].set_xlabel("feature index")
    fig.tight_layout()
    return save(fig, "p25b_cache_integrity_summary.png")


# ---------------------------------------------------------------- figure 7 (optional)
def fig_roi_mapping():
    """ROI -> feature-grid mapping (floor start / ceil end / clip)."""
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    for ax, tap in zip(axes, TAPS):
        S = FEATURE_GRID[tap]
        ax.imshow(np.zeros((S, S, 3)) + 0.16, extent=(0, S, S, 0))
        # a representative ROI box in canvas coords -> grid
        x0, y0, x1, y1 = int(0.30 * 512), int(0.35 * 512), int(0.72 * 512), int(0.80 * 512)
        from src.features.barr_pre_refinement_features import map_roi_to_grid
        fx0, fy0, fx1, fy1 = map_roi_to_grid(x0, y0, x1, y1, S)
        ax.add_patch(Rectangle((fx0, fy0), fx1 - fx0, fy1 - fy0, fill=False,
                               edgecolor="#dc2626", lw=2))
        ax.set_title(f"{tap}: grid {S}x{S}\nmapped cells=({fx1-fx0})x({fy1-fy0})")
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle("ROI -> feature-grid mapping: start=floor, end=ceil, clipped to grid "
                 "(external padding contributes no cells)", fontsize=10)
    fig.tight_layout()
    return save(fig, "p25b_roi_to_feature_grid_mapping.png")


def main() -> int:
    FIG.mkdir(parents=True, exist_ok=True)
    paths = [fig_pipeline(), fig_reduction(), fig_group_layout(), fig_scalars(),
             fig_population(), fig_integrity(), fig_roi_mapping()]
    display = {
        "p25b_feature_pipeline": "GT-free pre-refinement feature construction pipeline",
        "p25b_channel_adaptive_reduction": "Deterministic channel-adaptive avg-pool bins",
        "p25b_feature_group_layout": "202-D numeric feature layout",
        "p25b_scalar_descriptors": "Ten GT-free scalar descriptors + threshold roles",
        "p25b_extraction_population": "ROUTER_DEVELOPMENT extraction population",
        "p25b_cache_integrity_summary": "Feature cache integrity summary",
        "p25b_roi_to_feature_grid_mapping": "ROI -> feature-grid mapping (optional)",
    }
    man = {
        "artifact": "phase25b_figure_manifest",
        "phase": "25B",
        "classification": "DESCRIPTIVE_SCHEMATIC_FEATURES",
        "contains_experimental_results": False,
        "contains_hypothetical_performance_curves": False,
        "n_required_figures": 6,
        "n_optional_figures": 1,
        "n_figures": len(paths),
        "figures": {p.name: {"figure_id": p.stem,
                             "display_name": display[p.stem],
                             "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                             "bytes": p.stat().st_size, "sha256": sha(p)}
                    for p in paths},
        "test_reads": 0, "training": False, "inference": True,
        "generated_utc": UTC,
    }
    (FIG / "phase25b_figure_manifest.json").write_text(
        json.dumps(man, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(paths)} figures + manifest")
    return 0


if __name__ == "__main__":
    sys.exit(main())
