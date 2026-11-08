"""ReMedFiLM figure engine.

Builds every publication figure from persisted artifacts only. No model is
executed and no training occurs. Each figure records the evidence class it is
entitled to display.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
from PIL import Image

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"
FIG = OUT / "figures"
TABLES = OUT / "tables"

# Requested report layout.
SUBDIRS = ["Architecture", "Training curves", "Internal validation",
           "Semantic segmentation", "External evaluation", "Ablation",
           "Progression", "Routing and safety", "Statistics", "Robustness",
           "Efficiency"]

# Internal section keys -> requested report directory.
SUBDIR_MAP = {
    "architecture": "Architecture",
    "training_epochs": "Training curves",
    "internal_evaluation": "Internal validation",
    "subgroups": "Internal validation",
    "datasets": "Statistics",
    "segmentation": "Semantic segmentation",
    "external_evaluation": "External evaluation",
    "ablation": "Ablation",
    "progression": "Progression",
    "routing_safety": "Routing and safety",
    "robustness": "Robustness",
    "efficiency": "Efficiency",
    "statistics": "Statistics",
}
for s in SUBDIRS:
    (FIG / s).mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- styling ----
# Okabe-Ito colour-blind safe palette.
BLUE = "#0072B2"
SKY = "#56B4E9"
VERM = "#D55E00"
GREEN = "#009E73"
ORANGE = "#E69F00"
PURPLE = "#CC79A7"
GREY = "#7F7F7F"
LGREY = "#BFBFBF"
DARK = "#1A1A1A"

MODEL_COLORS = {
    "U-Net": "#B0B0B0",
    "Attention U-Net": "#999999",
    "U-Net++": "#808080",
    "Transformer/MiT-style U-Net": "#666666",
    "DeepLabV3+": "#4D4D4D",
    "GlobalMedFiLM": BLUE,
    "ReMedFiLM": VERM,
}
DOMAIN_COLORS = {"ISIC": "#0072B2", "BUSI": "#D55E00", "KVASIR": "#009E73", "KUB": "#CC79A7"}

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "axes.linewidth": 0.7,
    "axes.edgecolor": "#333333",
    "axes.grid": True,
    "grid.color": "#E6E6E6",
    "grid.linewidth": 0.6,
    "legend.frameon": False,
    "legend.fontsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "figure.dpi": 110,
})

REGISTRY: list[dict] = []


def save(fig, subdir: str, name: str, evidence: str, caption: str,
         notebook_section: str, sources: list[str]) -> None:
    subdir = SUBDIR_MAP.get(subdir, subdir)
    png = FIG / subdir / f"{name}.png"
    fig.savefig(png, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(FIG / subdir / f"{name}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    REGISTRY.append({
        "figure_id": name,
        "subdir": subdir,
        "path": png.relative_to(ROOT).as_posix(),
        "svg_path": (FIG / subdir / f"{name}.svg").relative_to(ROOT).as_posix(),
        "evidence_class": evidence,
        "caption": caption,
        "notebook_section": notebook_section,
        "sources": sources,
    })
    print(f"  FIG {subdir}/{name}")


def load_csv(p) -> list[dict]:
    with Path(p).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


# =========================================================== architecture ====
def fig_architecture() -> None:
    comp = [
        ("G  GlobalMedFiLM\nbackbone", 3523001, BLUE),
        ("R_psi  Regional\nRefiner", 1276401, GREEN),
        ("B_phi  Benefit\nRouter", 36801, ORANGE),
        ("S_omega  Post-Safety\nGate", 1217, PURPLE),
    ]
    fig, ax = plt.subplots(figsize=(6.4, 2.5))
    names = [c[0] for c in comp]
    vals = [c[1] for c in comp]
    cols = [c[2] for c in comp]
    bars = ax.bar(names, vals, color=cols, width=0.62, edgecolor="white", linewidth=0.8)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v * 1.06, f"{v:,}",
                ha="center", va="bottom", fontsize=7, color=DARK)
    ax.set_yscale("log")
    ax.set_ylabel("Parameters (log scale)")
    ax.set_ylim(700, 2e7)
    ax.set_title("ReMedFiLM component parameter budget — total 4,837,420")
    ax.grid(axis="x", visible=False)
    ax.text(0.99, 0.95, "backbone = 72.8% of total", transform=ax.transAxes,
            ha="right", va="top", fontsize=6.5, color=GREY)
    save(fig, "architecture", "A01_component_parameter_budget",
         "CANONICAL_ARCHITECTURE_CONTRACT",
         "Parameter budget of the four ReMedFiLM components (log scale).",
         "03", ["reports/audits/phase34_parameter_count_contract.json"])

    # component presence matrix
    models = ["U-Net", "Attention U-Net", "U-Net++", "DeepLabV3+",
              "Transformer/MiT U-Net", "GlobalMedFiLM", "ReMedFiLM FULL"]
    comps = ["Task-conditioned\nFiLM (G)", "Regional refiner\nR_psi",
             "Benefit router\nB_phi", "Post-safety gate\nS_omega"]
    presence = np.array([
        [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0],
        [0, 0, 0, 0], [1, 0, 0, 0], [1, 1, 1, 1],
    ])
    fig, ax = plt.subplots(figsize=(4.6, 2.9))
    cmap = matplotlib.colors.ListedColormap(["#F2F2F2", GREEN])
    ax.imshow(presence, cmap=cmap, aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(len(comps)))
    ax.set_xticklabels(comps, fontsize=6.5)
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(models, fontsize=7)
    for i in range(presence.shape[0]):
        for j in range(presence.shape[1]):
            ax.text(j, i, "●" if presence[i, j] else "—", ha="center", va="center",
                    fontsize=8, color="white" if presence[i, j] else "#BBBBBB")
    ax.set_title("Component presence by model identity")
    ax.grid(False)
    ax.set_xticks(np.arange(-.5, len(comps), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(models), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.4)
    ax.tick_params(which="minor", length=0)
    save(fig, "architecture", "A02_component_presence_matrix",
         "CANONICAL_ARCHITECTURE_CONTRACT",
         "Which components each model actually instantiates. Only the FULL "
         "assembly is ReMedFiLM; GlobalMedFiLM is the backbone.",
         "03", ["src/models/barr/ra_medfilm_barr.py",
                "reports/audits/phase25f_architecture_contract_v1_0.json"])

    # pipeline flow
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    ax.set_xlim(0, 10.4)
    ax.set_ylim(0, 5)
    ax.axis("off")

    def box(x, y, w, h, label, color, fs=7.0):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.05,rounding_size=0.10",
                                    linewidth=1.0, edgecolor=color,
                                    facecolor=color + "1F"))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                fontsize=fs, color=DARK, linespacing=1.35)

    def arrow(x1, y1, x2, y2, color="#555555", rad=0.0, dashed=False):
        ax.add_patch(FancyArrowPatch(
            (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=10,
            linewidth=1.0, color=color,
            linestyle="--" if dashed else "-",
            connectionstyle=f"arc3,rad={rad}", shrinkA=3, shrinkB=4))

    # top row of components
    box(0.10, 3.35, 1.35, 0.95, "Image +\ntask id", "#8C8C8C")
    box(1.75, 3.35, 2.10, 0.95, "G\nGlobalMedFiLM", BLUE)
    box(4.15, 3.35, 1.55, 0.95, "B_phi\nBenefit Router", ORANGE)
    box(6.00, 3.35, 1.55, 0.95, "R_psi\nRegional Refiner", GREEN)
    box(7.85, 3.35, 1.55, 0.95, "S_omega\nPost-Safety", PURPLE)

    for x1, x2 in ((1.45, 1.75), (3.85, 4.15), (5.70, 6.00), (7.55, 7.85)):
        arrow(x1, 3.82, x2, 3.82)

    # final mask box
    box(3.55, 0.30, 3.30, 0.85, "Final segmentation mask", VERM, fs=7.6)

    # three outcomes, each from its own component to its own landing point
    arrow(2.80, 3.35, 4.05, 1.19, color=BLUE, rad=-0.18)
    arrow(6.78, 3.35, 5.60, 1.19, color=GREEN, rad=0.10)
    arrow(8.62, 3.35, 6.95, 1.19, color=PURPLE, rad=0.30, dashed=True)

    ax.text(3.05, 2.22, "outcome 1 · SKIP\n(global kept)", fontsize=6.3,
            color=BLUE, rotation=-33, ha="center", va="center")
    ax.text(6.42, 2.02, "outcome 2 · REFINE + ACCEPT", fontsize=6.3,
            color=GREEN, rotation=38, ha="center", va="center")
    ax.text(8.42, 2.10, "outcome 3 · REFINE\n+ REJECT (fallback)", fontsize=6.3,
            color=PURPLE, rotation=52, ha="center", va="center")

    ax.text(0.10, 4.72, "ReMedFiLM FULL inference path", fontsize=8.8,
            fontweight="bold")
    ax.text(0.10, 0.05,
            "GlobalMedFiLM alone produces only outcome 1; the FULL system can take any of the three.",
            fontsize=6.2, color=GREY)
    save(fig, "architecture", "A03_remedfilm_inference_path",
         "CANONICAL_ARCHITECTURE_CONTRACT",
         "Three outcome branches of the FULL assembly: skip, refine+accept, "
         "refine+reject. Only the four-component assembly can take branches 2 and 3.",
         "03", ["src/models/barr/ra_medfilm_barr.py",
                "reports/tables/phase27_val808_predictions.csv"])


# =============================================================== datasets ====
def fig_datasets() -> None:
    comp = load_csv(TABLES / "REMEDFILM_DATASET_COMPOSITION.csv")
    domains = ["ISIC", "BUSI", "KVASIR", "KUB"]
    train = [int(r["train"]) for r in comp if r["domain"] in domains]
    val = [int(r["val"]) for r in comp if r["domain"] in domains]
    order = [domains.index(r["domain"]) for r in comp if r["domain"] in domains]
    train = [train[i] for i in order]
    val = [val[i] for i in order]

    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.5),
                             gridspec_kw={"width_ratios": [1.35, 1]})
    ax = axes[0]
    x = np.arange(4)
    ax.bar(x - 0.19, train, 0.36, label="TRAIN (5,832)", color=BLUE)
    ax.bar(x + 0.19, val, 0.36, label="VAL (808)", color=ORANGE)
    for i, (a, b) in enumerate(zip(train, val)):
        ax.text(i - 0.19, a + 12, f"{a:,}", ha="center", fontsize=6.2)
        ax.text(i + 0.19, b + 12, f"{b:,}", ha="center", fontsize=6.2)
    ax.set_xticks(x)
    ax.set_xticklabels(domains)
    ax.set_ylabel("Images")
    ax.set_title("Domain composition of the frozen development population")
    ax.legend(loc="upper right")
    ax.set_ylim(0, max(train) * 1.18)
    ax.grid(axis="x", visible=False)

    ax = axes[1]
    sizes = [5832, 808, 1683]
    labels = ["TRAIN", "VAL", "TEST\n(consumed)"]
    colors = [BLUE, ORANGE, LGREY]
    wedges, _, autot = ax.pie(sizes, labels=None, colors=colors, autopct=lambda p: f"{p:.1f}%",
                              startangle=90, textprops={"fontsize": 6.5},
                              wedgeprops={"linewidth": 0.8, "edgecolor": "white"})
    ax.legend(wedges, [f"{l.replace(chr(10),' ')}  {s:,}" for l, s in zip(labels, sizes)],
              loc="center left", bbox_to_anchor=(0.95, 0.5))
    ax.set_title("Split sizes (TEST not reopened)")
    save(fig, "datasets", "D01_domain_and_split_composition",
         "FROZEN_MANIFEST",
         "Per-domain TRAIN/VAL counts and overall split sizes from the phase4_v3 manifest.",
         "02", ["manifests/phase4_v3/train.csv", "manifests/phase4_v3/val.csv"])

    # foreground area distribution from derived per-sample table
    ps = load_csv(TABLES / "REMEDFILM_INTERNAL_PER_SAMPLE.csv")
    fig, ax = plt.subplots(figsize=(5.2, 2.6))
    data, labels = [], []
    for d in domains:
        vals = [float(r["gt_fg"]) / (512 * 512) * 100 for r in ps if r["domain"] == d]
        data.append(vals)
        labels.append(f"{d}\nn={len(vals)}")
    parts = ax.violinplot(data, showmedians=True, widths=0.8)
    for i, pc in enumerate(parts["bodies"]):
        pc.set_facecolor(list(DOMAIN_COLORS.values())[i])
        pc.set_alpha(0.55)
        pc.set_edgecolor("white")
    for key in ("cmedians", "cmaxes", "cmins", "cbars"):
        if key in parts:
            parts[key].set_color("#333333")
            parts[key].set_linewidth(0.7)
    ax.set_xticks(range(1, 5))
    ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylabel("Foreground area (% of 512×512 field)")
    ax.set_title("Ground-truth foreground burden by domain (VAL808)")
    save(fig, "datasets", "D02_foreground_area_distribution",
         "DERIVED_FROM_SAVED_PREDICTIONS",
         "Distribution of ground-truth lesion area per domain; KUB lesions are "
         "the smallest and most variable.",
         "02", ["full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv"])

    # KUB unit of analysis
    fig, ax = plt.subplots(figsize=(4.6, 2.3))
    cats = ["Full-field\nimages", "ROI instance\npatches"]
    vals = [873, 1385]
    bars = ax.bar(cats, vals, color=[BLUE, ORANGE], width=0.5)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 25, f"{v:,}", ha="center", fontsize=7)
    ax.set_ylabel("Manifest rows (TRAIN+VAL)")
    ax.set_title("KUB uses a mixed unit of analysis")
    ax.text(0.5, 0.72, "2,258 KUB rows total — not 2,258 distinct full images",
            transform=ax.transAxes, ha="center", fontsize=6.4, color=VERM)
    ax.grid(axis="x", visible=False)
    save(fig, "datasets", "D03_kub_unit_of_analysis",
         "FROZEN_MANIFEST",
         "KUB contributes both full-field images and ROI instance patches; "
         "pooling them as one image unit would be incorrect.",
         "02", ["manifests/phase4_v3/train.csv", "manifests/phase4_v3/val.csv"])


# ======================================================== training epochs ====
def _series(rows, metric):
    xs, ys = [], []
    for r in rows:
        if r["metric"] != metric:
            continue
        try:
            xs.append(int(r["epoch"]))
            ys.append(float(r["value"]))
        except (TypeError, ValueError):
            continue
    order = np.argsort(xs)
    return np.array(xs)[order], np.array(ys)[order]


def fig_training() -> None:
    hist = load_csv(TABLES / "REMEDFILM_EPOCH_HISTORY.csv")
    g = [r for r in hist if r["run_id"] == "phase21_global_medfilm_fourdomain_seed42_clean_v3"]
    assert g, "GlobalMedFiLM history missing"
    best_epoch = 66

    # T1 loss
    fig, ax = plt.subplots(figsize=(5.4, 2.7))
    for m, lab, c in (("train_loss", "Training loss", BLUE),
                      ("val_loss", "Validation loss", VERM)):
        x, y = _series(g, m)
        ax.plot(x, y, color=c, linewidth=1.3, label=lab)
    ax.axvline(best_epoch, color=GREEN, linestyle="--", linewidth=0.9)
    ax.annotate(f"selected epoch {best_epoch}", xy=(best_epoch, ax.get_ylim()[1] * 0.92),
                fontsize=6.5, color=GREEN, ha="left", xytext=(4, 0),
                textcoords="offset points")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("BCE + Dice loss")
    ax.set_title("GlobalMedFiLM — training and validation loss (81 epochs, seed 42)")
    ax.legend(loc="upper right")
    save(fig, "training_epochs", "T1_train_val_loss",
         "GENUINE_HISTORICAL_TRAINING",
         "Epoch-wise BCE+Dice loss for the frozen GlobalMedFiLM backbone.",
         "05", ["experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/history.csv"])

    # T2 dice
    fig, ax = plt.subplots(figsize=(5.4, 2.7))
    x, y = _series(g, "val_macro_dice")
    ax.plot(x, y, color=BLUE, linewidth=1.4)
    ax.scatter([x[best_epoch - 1]], [y[best_epoch - 1]], s=32, color=VERM, zorder=5,
               edgecolor="white", linewidth=0.8)
    ax.set_ylim(y.min() - 0.012, y.max() + 0.016)
    ax.annotate(f"best {y[best_epoch-1]:.4f} @ ep {best_epoch}",
                xy=(best_epoch, y[best_epoch - 1]), fontsize=6.5, color=VERM,
                xytext=(-92, -26), textcoords="offset points",
                arrowprops=dict(arrowstyle="-", color=VERM, linewidth=0.6,
                                shrinkA=2, shrinkB=3))
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Macro-domain VAL Dice")
    ax.set_title("Validation Dice improvement across epochs")
    save(fig, "training_epochs", "T2_val_dice_across_epochs",
         "GENUINE_HISTORICAL_TRAINING",
         "Macro-domain validation Dice per epoch with the selected checkpoint marked.",
         "05", ["experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/history.csv"])

    # T3 iou
    fig, ax = plt.subplots(figsize=(5.4, 2.7))
    doms = ["ISIC", "BUSI", "KVASIR", "KUB"]
    ious = [_series(g, f"val_iou_{d}") for d in doms]
    macro_iou = np.mean([v for _, v in ious], axis=0)
    ax.plot(x, macro_iou, color=VERM, linewidth=1.4, label="Macro-domain IoU")
    for d, (xs, ys) in zip(doms, ious):
        ax.plot(xs, ys, color=DOMAIN_COLORS[d], linewidth=0.7, alpha=0.75, label=d)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Validation IoU")
    ax.set_title("Validation IoU improvement across epochs")
    ax.legend(ncol=2, loc="lower right")
    save(fig, "training_epochs", "T3_val_iou_across_epochs",
         "GENUINE_HISTORICAL_TRAINING",
         "Per-domain and macro validation IoU per epoch (IoU was logged per epoch, "
         "so no interpolation is required).",
         "05", ["experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/history.csv"])

    # T4 per-domain learning curves
    fig, ax = plt.subplots(figsize=(5.4, 2.7))
    for d in doms:
        xs, ys = _series(g, f"val_dice_{d}")
        ax.plot(xs, ys, color=DOMAIN_COLORS[d], linewidth=1.2, label=d)
    ax.axvline(best_epoch, color=GREY, linestyle=":", linewidth=0.8)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Validation Dice")
    ax.set_title("Per-domain learning curves (genuine per-epoch records)")
    ax.legend(ncol=4, loc="lower center")
    save(fig, "training_epochs", "T4_per_domain_learning_curves",
         "GENUINE_HISTORICAL_TRAINING",
         "Per-domain validation Dice logged every epoch for the backbone. "
         "KUB lags throughout, consistent with its smaller lesions.",
         "05", ["experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/history.csv"])

    # T5 lr
    fig, ax = plt.subplots(figsize=(5.4, 2.2))
    xs, ys = _series(g, "learning_rate")
    ax.plot(xs, ys, color=PURPLE, linewidth=1.4)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Learning rate")
    ax.set_title("Cosine-annealing learning-rate schedule (recorded per epoch)")
    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    save(fig, "training_epochs", "T5_learning_rate_schedule",
         "GENUINE_HISTORICAL_TRAINING",
         "Learning rate recorded at every epoch; no reconstruction required.",
         "05", ["experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/history.csv"])

    # T6 best epoch / selection
    reg = load_csv(TABLES / "TRAINING_RUN_REGISTRY.csv")
    core = [r for r in reg if r["model"] in
            ("GlobalMedFiLM (G)", "U-Net", "Attention U-Net", "U-Net++",
             "DeepLabV3+", "Transformer/MiT-style U-Net", "R_psi (Regional Refiner)",
             "B_phi (Benefit Router)", "S_omega (Post-Safety Gate)")]
    core = [r for r in core if r["best_epoch"] not in ("NOT_RECORDED", "NOT_APPLICABLE")]
    core = core[:14]
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    ys = np.arange(len(core))
    for i, r in enumerate(core):
        be = int(float(r["best_epoch"]))
        tot = int(float(r["epochs_completed"]))
        ax.plot([0, tot], [i, i], color="#DDDDDD", linewidth=2.4, solid_capstyle="round")
        ax.scatter([be], [i], s=30, color=VERM, zorder=4, edgecolor="white", linewidth=0.6)
        ax.text(tot + 2, i, f"{tot} ep", va="center", fontsize=5.8, color=GREY)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{r['model'][:26]}" for r in core], fontsize=6.2)
    ax.invert_yaxis()
    ax.set_xlabel("Epoch")
    ax.set_title("Selected (best) epoch versus total epochs run")
    ax.scatter([], [], s=30, color=VERM, label="selected epoch")
    ax.plot([], [], color="#DDDDDD", linewidth=2.4, label="epochs completed")
    ax.legend(loc="lower right")
    save(fig, "training_epochs", "T6_best_epoch_selection",
         "GENUINE_HISTORICAL_TRAINING",
         "Checkpoint-selection epochs across recovered runs. Early stopping with "
         "patience 15 is visible in the trailing gap.",
         "05", ["full_doc_report/tables/TRAINING_RUN_REGISTRY.csv"])

    # T7 multi-seed
    fig, ax = plt.subplots(figsize=(5.6, 2.8))
    seed_runs = {
        "42": "phase21_global_medfilm_fourdomain_seed42_clean_v3",
    }
    xs, ys = _series(g, "val_macro_dice")
    ax.plot(xs, ys, color=BLUE, linewidth=1.6, label="backbone, seed 42 (trained)")
    for seed, color, marker in (("123", GREEN, "o"), ("3407", ORANGE, "s")):
        sub = [r for r in hist if r["run_id"].startswith(f"phase29_seed{seed}")
               and r["metric"] == "val_refiner_dice"]
        if not sub:
            continue
        rid = sorted({r["run_id"] for r in sub})[0]
        rr = [r for r in sub if r["run_id"] == rid]
        x2, y2 = _series(rr, "val_refiner_dice")
        ax.plot(x2, y2, color=color, linewidth=0.9, alpha=0.7,
                label=f"R_psi, seed {seed} ({rid.split('__')[-1]})")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Validation Dice")
    ax.set_title("Separate runs — the backbone was trained once and shared")
    ax.legend(loc="lower right", fontsize=6)
    ax.text(0.02, 0.96,
            "Seeds 123/3407 re-fit R_psi, B_phi and S_omega on a SHARED frozen\n"
            "backbone. They are not three independent global-model trainings.",
            transform=ax.transAxes, fontsize=5.8, va="top", color=VERM)
    save(fig, "training_epochs", "T7_multiseed_histories",
         "GENUINE_HISTORICAL_TRAINING",
         "Downstream component runs per seed, explicitly separated from the single "
         "backbone training.",
         "05", ["experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/history.csv",
                "experiments/phase29_seed123/", "experiments/phase29_seed3407/"])

    # T8 improvement summary
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    models = [
        ("GlobalMedFiLM (G)", "phase21_global_medfilm_fourdomain_seed42_clean_v3", "val_macro_dice"),
        ("U-Net++", "phase20_shared_unetpp_fourdomain_seed42_clean_v3", "val_macro_dice"),
        ("U-Net", "phase20b_shared_unet_fourdomain_seed42_clean_v3", "val_macro_dice"),
        ("Attention U-Net", "phase20b_shared_attention_unet_fourdomain_seed42_clean_v3", "val_macro_dice"),
        ("DeepLabV3+", "phase20b_shared_deeplabv3plus_fourdomain_seed42_clean_v3", "val_macro_dice"),
        ("Transformer/MiT", "phase20b_shared_transformer_mit_unet_fourdomain_seed42_clean_v3", "val_macro_dice"),
    ]
    labels, firsts, bests, finals = [], [], [], []
    for name, rid, metric in models:
        sub = [r for r in hist if r["run_id"] == rid]
        if not sub:
            continue
        x, y = _series(sub, metric)
        if len(y) < 3:
            continue
        labels.append(name)
        firsts.append(y[0])
        bests.append(y.max())
        finals.append(y[-1])
    xpos = np.arange(len(labels))
    ax.plot(xpos, firsts, "o-", color=LGREY, label="epoch 1", markersize=4)
    ax.plot(xpos, bests, "o-", color=VERM, label="best epoch", markersize=4)
    ax.plot(xpos, finals, "o-", color=BLUE, label="final epoch", markersize=4)
    ax.set_xticks(xpos)
    ax.set_xticklabels(labels, rotation=18, ha="right", fontsize=6.4)
    ax.set_ylabel("Macro-domain VAL Dice")
    ax.set_title("Training improvement on the identical VAL808 population")
    ax.legend(ncol=3, loc="lower right")
    save(fig, "training_epochs", "T8_training_improvement_summary",
         "GENUINE_HISTORICAL_TRAINING",
         "Epoch 1, best, and final validation Dice for every four-domain run that "
         "logged the metric.",
         "05", ["experiments/*/history.csv"])


# ==================================================== internal evaluation ====
def fig_internal() -> None:
    rows = load_csv(TABLES / "REMEDFILM_INTERNAL_METRICS.csv")
    doms = ["ISIC", "BUSI", "KVASIR", "KUB", "MACRO_DOMAIN_EQUAL_WEIGHT"]
    short = ["ISIC", "BUSI", "KVASIR", "KUB", "MACRO"]
    by = {r["domain"]: r for r in rows}

    # I1 grouped metric comparison
    metrics = [("dice", "Dice"), ("iou", "IoU"), ("precision", "Precision"), ("recall", "Recall")]
    fig, axes = plt.subplots(1, 4, figsize=(7.4, 2.5), sharey=True)
    for ax, (m, lab) in zip(axes, metrics):
        g = [float(by[d][f"global_{m}"]) for d in doms]
        f = [float(by[d][f"final_{m}"]) for d in doms]
        x = np.arange(len(doms))
        ax.bar(x - 0.2, g, 0.38, color=BLUE, label="GlobalMedFiLM")
        ax.bar(x + 0.2, f, 0.38, color=VERM, label="ReMedFiLM FULL")
        ax.set_xticks(x)
        ax.set_xticklabels(short, rotation=45, ha="right", fontsize=6.2)
        ax.set_title(lab)
        ax.grid(axis="x", visible=False)
        lo = min(g + f)
        ax.set_ylim(max(0.0, lo - 0.08), 1.0)
    axes[0].set_ylabel("Score")
    axes[0].legend(loc="lower left", fontsize=5.8)
    fig.suptitle("VAL808 (n = 808): backbone versus FULL system, identical samples", y=1.02, fontsize=8.5)
    save(fig, "internal_evaluation", "I1_domain_metric_comparison",
         "DERIVED_FROM_SAVED_PREDICTIONS",
         "Dice, IoU, precision and recall per domain for the backbone and the FULL system.",
         "07", ["full_doc_report/tables/REMEDFILM_INTERNAL_METRICS.csv"])

    # I2 forest
    paired = jload(TABLES / "REMEDFILM_PAIRED_DELTA.json")
    fig, ax = plt.subplots(figsize=(5.0, 2.6))
    order = ["KUB", "ISIC", "KVASIR", "BUSI"]
    ys = np.arange(len(order) + 1)
    labels = []
    for i, d in enumerate(order):
        pd_ = paired["per_domain"][d]
        ax.scatter([pd_["point"]], [i], color=DOMAIN_COLORS[d], s=34, zorder=4)
        ax.text(pd_["point"], i + 0.28, f"{pd_['point']*100:+.3f} pp  (n={pd_['n']})",
                fontsize=5.8, ha="center", color=DARK)
        labels.append(d)
    ax.scatter([paired["point"]], [len(order)], color=VERM, s=46, marker="D", zorder=5)
    ax.plot([paired["ci_low"], paired["ci_high"]], [len(order)] * 2, color=VERM, linewidth=1.6)
    ax.text(paired["point"], len(order) + 0.3,
            f"{paired['point']*100:+.3f} pp  [{paired['ci_low']*100:+.3f}, {paired['ci_high']*100:+.3f}]",
            fontsize=6.0, ha="center", color=VERM)
    labels.append("MACRO (95% CI)")
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set_yticks(ys)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("Δ Dice (ReMedFiLM FULL − GlobalMedFiLM)")
    ax.set_title("Paired domain-stratified improvement, VAL808 seed 42")
    ax.grid(axis="y", visible=False)
    save(fig, "internal_evaluation", "I2_paired_delta_forest",
         "DERIVED_FROM_SAVED_PREDICTIONS",
         "Per-domain and macro paired Δ Dice with a 10,000-replicate "
         "domain-stratified bootstrap CI.",
         "07", ["full_doc_report/tables/REMEDFILM_PAIRED_DELTA.json"])

    # I3 delta distribution
    ps = load_csv(TABLES / "REMEDFILM_INTERNAL_PER_SAMPLE.csv")
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.5),
                             gridspec_kw={"width_ratios": [1.5, 1]})
    ax = axes[0]
    for d in ["ISIC", "BUSI", "KVASIR", "KUB"]:
        vals = [float(r["delta_dice"]) for r in ps if r["domain"] == d]
        ax.hist(vals, bins=41, range=(-0.5, 0.5), histtype="step", linewidth=1.1,
                color=DOMAIN_COLORS[d], label=d, density=True)
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set_xlabel("Δ Dice per image")
    ax.set_ylabel("Density")
    ax.set_title("Per-image paired difference")
    ax.legend(fontsize=6)
    ax = axes[1]
    cats = ["Beneficial", "Unchanged", "Harmful"]
    vals = [
        sum(r["beneficial"] == "True" for r in ps),
        sum(r["unchanged"] == "True" for r in ps),
        sum(r["harmful"] == "True" for r in ps),
    ]
    bars = ax.bar(cats, vals, color=[GREEN, LGREY, VERM], width=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 6, f"{v}", ha="center", fontsize=7)
    ax.set_ylabel("Images (n = 808)")
    ax.set_title("Refinement outcome")
    ax.grid(axis="x", visible=False)
    save(fig, "internal_evaluation", "I3_paired_delta_distribution",
         "DERIVED_FROM_SAVED_PREDICTIONS",
         "Distribution of per-image Δ Dice and the beneficial/unchanged/harmful split.",
         "07", ["full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv"])

    # I4 HD95
    fig, ax = plt.subplots(figsize=(5.0, 2.5))
    x = np.arange(4)
    g = [float(by[d]["global_hd95"]) for d in doms[:4]]
    f = [float(by[d]["final_hd95"]) for d in doms[:4]]
    ax.bar(x - 0.2, g, 0.38, color=BLUE, label="GlobalMedFiLM")
    ax.bar(x + 0.2, f, 0.38, color=VERM, label="ReMedFiLM FULL")
    for i, (a, b) in enumerate(zip(g, f)):
        ax.text(i - 0.2, a + 1.2, f"{a:.1f}", ha="center", fontsize=6)
        ax.text(i + 0.2, b + 1.2, f"{b:.1f}", ha="center", fontsize=6)
    ax.set_xticks(x)
    ax.set_xticklabels(doms[:4])
    ax.set_ylabel("HD95 (pixels)")
    ax.set_title("Boundary error (lower is better)")
    ax.legend()
    ax.grid(axis="x", visible=False)
    save(fig, "internal_evaluation", "I4_hd95_comparison",
         "DERIVED_FROM_SAVED_PREDICTIONS",
         "95th-percentile symmetric surface distance computed from the saved masks.",
         "07", ["full_doc_report/tables/REMEDFILM_INTERNAL_METRICS.csv"])


# =============================================================== subgroups ====
def fig_subgroups() -> None:
    rows = load_csv(ROOT / "reports/tables/phase21_kub_subgroup_analysis.csv")
    cols = list(rows[0].keys())
    print("    kub subgroup cols:", cols)
    fig, ax = plt.subplots(figsize=(5.0, 2.5))
    key = "category" if "category" in cols else cols[0]
    metric = next((c for c in cols if c.lower() in ("dice", "mean_dice", "macro_dice")), None)
    if metric:
        cats = [r[key] for r in rows]
        vals = [float(r[metric]) for r in rows]
        nkey = next((c for c in cols if "n" == c.lower() or c.lower().endswith("_n")), None)
        bars = ax.bar(range(len(cats)), vals, color=[ORANGE, BLUE, GREEN, PURPLE][:len(cats)],
                      width=0.6)
        for i, (b, v) in enumerate(zip(bars, vals)):
            n = f" (n={rows[i][nkey]})" if nkey else ""
            ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.3f}{n}",
                    ha="center", fontsize=6)
        ax.set_xticks(range(len(cats)))
        ax.set_xticklabels([c.replace("_", " ").title() for c in cats], fontsize=6.5)
        ax.set_ylabel("Dice")
        ax.set_ylim(0, 1)
        ax.set_title("KUB stone subgroup performance (VAL808)")
        ax.grid(axis="x", visible=False)
        save(fig, "subgroups", "SG1_kub_stone_subgroups",
             "FROZEN_HISTORICAL_EVALUATION",
             "Per-subgroup Dice inside the KUB domain.",
             "08", ["reports/tables/phase21_kub_subgroup_analysis.csv"])

    # size strata
    rows = load_csv(ROOT / "reports/tables/phase21_kub_size_stratification.csv")
    cols = list(rows[0].keys())
    print("    kub size cols:", cols)
    metric = next((c for c in cols if "dice" in c.lower()), None)
    bin_key = next((c for c in cols if "bin" in c.lower() or "stratum" in c.lower()), cols[0])
    if metric:
        fig, ax = plt.subplots(figsize=(5.0, 2.5))
        cats = [r[bin_key] for r in rows]
        vals = [float(r[metric]) for r in rows]
        ax.bar(range(len(cats)), vals, color=SKY, width=0.6)
        for i, v in enumerate(vals):
            ax.text(i, v + 0.01, f"{v:.3f}", ha="center", fontsize=6)
        ax.set_xticks(range(len(cats)))
        ax.set_xticklabels(cats, fontsize=6.5)
        ax.set_ylabel("Dice")
        ax.set_title("KUB performance by object-size stratum")
        ax.grid(axis="x", visible=False)
        save(fig, "subgroups", "SG2_kub_size_stratification",
             "FROZEN_HISTORICAL_EVALUATION",
             "Dice against the frozen KUB size taxonomy.",
             "08", ["reports/tables/phase21_kub_size_stratification.csv"])


# ============================================================ segmentation ====
def _img_from_gt(gt_path: str, domain: str) -> Path | None:
    s = gt_path
    if domain == "ISIC":
        c = s.replace("_segmentation.png", ".jpg") \
             .replace("Task1_Training_GroundTruth", "Task1-2_Training_Input") \
             .replace("Task1_Validation_GroundTruth", "Task1-2_Validation_Input") \
             .replace("Task1_Test_GroundTruth", "Task1-2_Test_Input")
    elif domain == "BUSI":
        c = s.replace("\\gt\\", "\\img\\").replace("_anno.bmp", ".bmp")
    elif domain == "KVASIR":
        c = s.replace("\\masks\\", "\\images\\")
    else:
        c = s.replace("\\Masks\\", "\\Images\\").replace("_mask.png", ".png")
    q = Path(c)
    return q if q.exists() else None


def _fit512(img: np.ndarray) -> np.ndarray:
    """Aspect-preserving resize + centre pad, matching the frozen contract."""
    from PIL import Image as I
    h, w = img.shape[:2]
    sc = 512.0 / max(h, w)
    nh, nw = max(1, int(round(h * sc))), max(1, int(round(w * sc)))
    im = I.fromarray(img).resize((nw, nh), I.BILINEAR)
    out = np.zeros((512, 512, 3), dtype=np.uint8)
    y0, x0 = (512 - nh) // 2, (512 - nw) // 2
    out[y0:y0 + nh, x0:x0 + nw] = np.array(im)
    return out


def _overlay(img512, gt, pred):
    vis = img512.copy().astype(np.float32)
    tp = gt & pred
    fp = (~gt) & pred
    fn = gt & (~pred)
    vis[tp] = vis[tp] * 0.45 + np.array([0, 158, 115]) * 0.55
    vis[fp] = vis[fp] * 0.35 + np.array([213, 94, 0]) * 0.65
    vis[fn] = vis[fn] * 0.45 + np.array([0, 114, 178]) * 0.55
    return np.clip(vis, 0, 255).astype(np.uint8)


SEG_SELECTION: list[dict] = []


def _panel_figure(dom, picks, tag, title, filename, caption):
    """6-column gallery: image | GT | global | FULL | TP/FP/FN | metrics."""
    preds = {r["sample_id"]: r for r in load_csv(
        ROOT / "reports/tables/phase27_val808_predictions.csv")}
    man = {r["sample_id"]: r for r in load_csv(
        ROOT / "reports/tables/phase21_prediction_manifest.csv")}
    ps = {r["sample_id"]: r for r in load_csv(TABLES / "REMEDFILM_INTERNAL_PER_SAMPLE.csv")}

    fig, axes = plt.subplots(len(picks), 6, figsize=(12.4, 2.05 * len(picks)),
                             gridspec_kw={"width_ratios": [1, 1, 1, 1, 1, 0.95]})
    if len(picks) == 1:
        axes = np.array([axes])
    heads = ["Image", "Ground truth", "GlobalMedFiLM", "ReMedFiLM FULL",
             "TP / FP / FN", "Metrics"]
    for j, h in enumerate(heads):
        axes[0, j].set_title(h, fontsize=7.2)

    for i, sid in enumerate(picks):
        r = preds[sid]
        gt_p = Path(man[sid]["gt_mask_path"])
        img_p = _img_from_gt(str(gt_p), dom)
        if img_p is None:
            continue
        img512 = _fit512(np.array(Image.open(img_p).convert("RGB")))
        with np.load(ROOT / man[sid]["npz_path"]) as z:
            gt = z["gt"] > 0
        gm = np.array(Image.open(ROOT / r["global_mask_path"]).convert("L")) > 0
        fm = np.array(Image.open(ROOT / r["final_mask_path"]).convert("L")) > 0
        if gm.shape != (512, 512):
            gm = np.array(Image.fromarray(gm.astype(np.uint8) * 255)
                          .resize((512, 512), Image.NEAREST)) > 0
            fm = np.array(Image.fromarray(fm.astype(np.uint8) * 255)
                          .resize((512, 512), Image.NEAREST)) > 0

        panels = [img512,
                  np.repeat((gt * 255)[..., None], 3, 2),
                  np.repeat((gm * 255)[..., None], 3, 2),
                  np.repeat((fm * 255)[..., None], 3, 2),
                  _overlay(img512, gt, fm)]
        for j, pnl in enumerate(panels):
            axes[i, j].imshow(pnl)
            axes[i, j].set_xticks([])
            axes[i, j].set_yticks([])
            axes[i, j].grid(False)

        d0 = float(ps[sid]["global_dice"])
        d1 = float(ps[sid]["final_dice"])
        iou1 = float(ps[sid]["final_iou"])
        hd = ps[sid]["final_hd95"]
        br = r["state_machine_branch"].replace("_", " ").lower()
        txt = (f"sample {sid[:10]}\n"
               f"G Dice {d0:.4f}\n"
               f"R Dice {d1:.4f}\n"
               f"$\\Delta$ {d1 - d0:+.4f}\n"
               f"R IoU {iou1:.4f}\n"
               f"R HD95 {float(hd):.1f} px\n"
               f"{br}")
        ax = axes[i, 5]
        ax.axis("off")
        ax.text(0.02, 0.5, txt, fontsize=5.6, va="center", family="DejaVu Sans Mono")
        axes[i, 0].set_ylabel(dom, fontsize=7)

        SEG_SELECTION.append({
            "figure": filename, "panel": tag, "row": i + 1, "domain": dom,
            "sample_id": sid, "branch": r["state_machine_branch"],
            "global_dice": round(d0, 6), "final_dice": round(d1, 6),
            "delta_dice": round(d1 - d0, 6),
            "final_iou": round(iou1, 6),
            "final_hd95": (round(float(hd), 4) if hd not in ("", None) else ""),
            "source_image": str(img_p),
            "gt_mask": str(gt_p),
            "global_mask": r["global_mask_path"],
            "final_mask": r["final_mask_path"],
        })

    fig.suptitle(title, fontsize=9)
    fig.tight_layout()
    save(fig, "segmentation", filename, "SAVED_PREDICTIONS_VAL808", caption, "08/09",
         ["reports/tables/phase27_val808_predictions.csv",
          "reports/predictions/phase21_global_medfilm_fourdomain_seed42_clean_v3/",
          "full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv"])


def fig_segmentation() -> None:
    ps = {r["sample_id"]: r for r in load_csv(TABLES / "REMEDFILM_INTERNAL_PER_SAMPLE.csv")}
    man = {r["sample_id"]: r for r in load_csv(
        ROOT / "reports/tables/phase21_prediction_manifest.csv")}

    for dom in ("ISIC", "BUSI", "KVASIR", "KUB"):
        ids = [s for s, r in ps.items() if r["domain"] == dom and s in man]
        if len(ids) < 6:
            continue
        ids.sort(key=lambda s: float(ps[s]["delta_dice"]))
        picks = [ids[0], ids[len(ids) // 2], ids[-1]]  # worst, median, best
        _panel_figure(
            dom, picks, "worst/median/best",
            f"{dom} — deterministic selection: worst / median / best $\\Delta$ Dice "
            f"(not cherry-picked)",
            f"SEG_{dom}_global_vs_full",
            f"{dom}: original, ground truth, backbone mask, FULL mask, TP/FP/FN "
            f"overlay and per-sample metrics for the worst, median and best paired "
            f"improvement.")

    # A second gallery proving FULL differs from the backbone when refinement is accepted.
    for dom in ("ISIC", "BUSI", "KVASIR", "KUB"):
        acc = [s for s, r in ps.items()
               if r["domain"] == dom and r["branch"] == "EXECUTE_THEN_ACCEPT"]
        if not acc:
            continue
        acc.sort(key=lambda s: float(ps[s]["delta_dice"]))
        pick = [acc[len(acc) // 2]]  # median accepted refinement
        _panel_figure(
            dom, pick, "accepted refinement",
            f"{dom} — refinement ACCEPTED by the safety gate: FULL differs from the backbone",
            f"SEG_{dom}_refinement_accepted",
            f"{dom}: a single accepted refinement showing the FULL mask diverging "
            f"from the backbone mask. This is the visual proof that ReMedFiLM FULL is "
            f"not a relabelled GlobalMedFiLM output.")

    # Failure montage
    harm = sorted(ps.values(), key=lambda r: float(r["delta_dice"]))[:6]
    preds = {r["sample_id"]: r for r in load_csv(
        ROOT / "reports/tables/phase27_val808_predictions.csv")}
    fig, axes = plt.subplots(2, 6, figsize=(11.0, 4.0))
    for j, r in enumerate(harm):
        sid = r["sample_id"]
        if sid not in preds or sid not in man:
            continue
        dom = r["domain"]
        gt_p = Path(man[sid]["gt_mask_path"])
        img_p = _img_from_gt(str(gt_p), dom)
        if img_p is None:
            continue
        img512 = _fit512(np.array(Image.open(img_p).convert("RGB")))
        with np.load(ROOT / man[sid]["npz_path"]) as z:
            gt = z["gt"] > 0
        fm = np.array(Image.open(ROOT / preds[sid]["final_mask_path"])
                      .convert("L").resize((512, 512), Image.NEAREST)) > 0
        axes[0, j].imshow(img512)
        axes[0, j].set_title(dom, fontsize=7)
        axes[0, j].set_xticks([]); axes[0, j].set_yticks([])
        axes[1, j].imshow(_overlay(img512, gt, fm))
        axes[1, j].set_xlabel(f"$\\Delta$ {float(r['delta_dice']):+.3f}", fontsize=6)
        axes[1, j].set_xticks([]); axes[1, j].set_yticks([])
        SEG_SELECTION.append({
            "figure": "SEG_failure_cases", "panel": "harmful", "row": j + 1,
            "domain": dom, "sample_id": sid, "branch": r["branch"],
            "global_dice": round(float(r["global_dice"]), 6),
            "final_dice": round(float(r["final_dice"]), 6),
            "delta_dice": round(float(r["delta_dice"]), 6),
            "final_iou": round(float(r["final_iou"]), 6),
            "final_hd95": (round(float(r["final_hd95"]), 4)
                           if r["final_hd95"] not in ("", None) else ""),
            "source_image": str(img_p), "gt_mask": str(gt_p),
            "global_mask": preds[sid]["global_mask_path"],
            "final_mask": preds[sid]["final_mask_path"],
        })
    fig.suptitle("Worst six refinements by $\\Delta$ Dice — genuine failure cases",
                 fontsize=9)
    fig.tight_layout()
    save(fig, "segmentation", "SEG_failure_cases", "SAVED_PREDICTIONS_VAL808",
         "The six largest negative Delta Dice cases; the safety gate accepted these, "
         "so they are genuine residual failures.", "09",
         ["full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv"])

    import csv as _csv
    with (TABLES / "REMEDFILM_SEGMENTATION_SELECTION.csv").open("w", newline="",
                                                               encoding="utf-8") as fh:
        w = _csv.DictWriter(fh, fieldnames=list(SEG_SELECTION[0].keys()))
        w.writeheader()
        w.writerows(SEG_SELECTION)
    print(f"    segmentation selection rows: {len(SEG_SELECTION)}")


# ==================================================== external evaluation ====
def fig_external() -> None:
    rows = load_csv(TABLES / "REMEDFILM_EXTERNAL_METRICS.csv")
    cohorts = []
    for r in rows:
        if r["cohort"] not in cohorts:
            cohorts.append(r["cohort"])
    dice = {}
    for r in rows:
        if r["metric"] == "Dice":
            dice[(r["cohort"], r["arm"])] = r
    fig, ax = plt.subplots(figsize=(6.4, 2.7))
    x = np.arange(len(cohorts))
    gv = [float(dice[(c, "GlobalMedFiLM")]["mean"]) for c in cohorts]
    fv = [float(dice[(c, "ReMedFiLM_FULL")]["mean"]) for c in cohorts]
    gl = [float(dice[(c, "GlobalMedFiLM")]["ci_low"]) for c in cohorts]
    gh = [float(dice[(c, "GlobalMedFiLM")]["ci_high"]) for c in cohorts]
    fl = [float(dice[(c, "ReMedFiLM_FULL")]["ci_low"]) for c in cohorts]
    fh = [float(dice[(c, "ReMedFiLM_FULL")]["ci_high"]) for c in cohorts]
    ax.bar(x - 0.2, gv, 0.38, color=BLUE, label="GlobalMedFiLM")
    ax.bar(x + 0.2, fv, 0.38, color=VERM, label="ReMedFiLM FULL")
    ax.errorbar(x - 0.2, gv, yerr=[np.array(gv) - np.array(gl), np.array(gh) - np.array(gv)],
                fmt="none", ecolor="#333333", elinewidth=0.8, capsize=2)
    ax.errorbar(x + 0.2, fv, yerr=[np.array(fv) - np.array(fl), np.array(fh) - np.array(fv)],
                fmt="none", ecolor="#333333", elinewidth=0.8, capsize=2)
    ns = [dice[(c, "ReMedFiLM_FULL")]["n_total"] for c in cohorts]
    ax.set_xticks(x)
    ax.set_xticklabels([f"{c}\nn={n}" for c, n in zip(cohorts, ns)], fontsize=6.3)
    ax.set_ylabel("Dice (macro over cases)")
    ax.set_title("External retrospective cohorts (884 cases) — 95% bootstrap CI")
    ax.legend()
    ax.grid(axis="x", visible=False)
    save(fig, "external_evaluation", "EXT01_external_dice",
         "EXTERNAL_RETROSPECTIVE_SAVED_PREDICTIONS",
         "External Dice per cohort with case-level bootstrap CIs. Cohort sizes differ; "
         "no pooling across cohorts.",
         "10", ["reports/tables/c1_external_stress_summary.csv"])

    # delta
    fig, ax = plt.subplots(figsize=(5.2, 2.5))
    deltas = [fv[i] - gv[i] for i in range(len(cohorts))]
    bars = ax.bar(range(len(cohorts)), deltas, color=[GREEN if d >= 0 else VERM for d in deltas],
                  width=0.55)
    for i, d in enumerate(deltas):
        ax.text(i, d + (0.001 if d >= 0 else -0.0015), f"{d:+.4f}", ha="center", fontsize=6.5)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_xticks(range(len(cohorts)))
    ax.set_xticklabels(cohorts, rotation=15, ha="right", fontsize=6.4)
    ax.set_ylabel("Δ Dice (FULL − backbone)")
    ax.set_title("External paired difference by cohort")
    ax.grid(axis="x", visible=False)
    save(fig, "external_evaluation", "EXT02_external_delta",
         "EXTERNAL_RETROSPECTIVE_SAVED_PREDICTIONS",
         "Paired Dice difference per external cohort.",
         "10", ["reports/tables/c1_external_stress_summary.csv"])

    # stone-free failure
    pc = load_csv(ROOT / "reports/tables/c1_external_stress_per_case.csv")
    sf = [r for r in pc if r.get("gt_empty") == "True"]
    fig, ax = plt.subplots(figsize=(4.8, 2.4))
    if sf:
        by_arm = defaultdict(list)
        for r in sf:
            by_arm[r["arm"]].append(int(r["pred_empty"] == "False"))
        arms = list(by_arm)
        vals = [sum(by_arm[a]) for a in arms]
        tot = [len(by_arm[a]) for a in arms]
        ax.bar([a.upper() for a in arms], vals, color=[BLUE, VERM][:len(arms)], width=0.5)
        for i, (v, t) in enumerate(zip(vals, tot)):
            ax.text(i, v + 0.2, f"{v}/{t}", ha="center", fontsize=7.5)
        ax.set_ylabel("Stone-free cases receiving foreground")
        ax.set_title("Documented false-positive failure on stone-free images")
        ax.set_ylim(0, max(tot) * 1.25)
        ax.grid(axis="x", visible=False)
    save(fig, "external_evaluation", "EXT03_stonefree_false_positive",
         "EXTERNAL_RETROSPECTIVE_SAVED_PREDICTIONS",
         "The stone-free cohort receives foreground on every case — a preserved "
         "negative finding, not a success.",
         "10", ["reports/tables/c1_external_stress_per_case.csv"])


# ============================================================= progression ====
def fig_progression() -> None:
    rows = load_csv(TABLES / "REMEDFILM_PROGRESSION_RESULTS.csv")
    fig, ax = plt.subplots(figsize=(6.6, 2.9))
    labels, gmacs, harm = [], [], []
    for r in rows:
        if not r.get("gmacs_lower_bound"):
            continue
        labels.append(r["stage_name"].split("(")[0].strip())
        gmacs.append(float(r["gmacs_lower_bound"]))
        harm.append(float(r["harm_rate"]) if r["harm_rate"] else 0.0)
    x = np.arange(len(labels))
    ax.bar(x, gmacs, color=[BLUE, GREY, ORANGE, PURPLE, VERM][:len(labels)], width=0.6)
    for i, g in enumerate(gmacs):
        ax.text(i, g + 0.15, f"{g:.2f}", ha="center", fontsize=6.5)
    ax.set_xticks(x)
    ax.set_xticklabels([l.replace(" ", "\n", 1) for l in labels], fontsize=6.0)
    ax.set_ylabel("Analytical GMACs (lower bound)")
    ax.set_title("Component progression: compute cost of each assembly stage")
    ax2 = ax.twinx()
    ax2.plot(x, [h * 100 for h in harm], "o--", color=VERM, markersize=4, linewidth=1.0)
    ax2.set_ylabel("Harmful activation share (%)", color=VERM)
    ax2.tick_params(axis="y", colors=VERM)
    ax2.grid(False)
    save(fig, "progression", "PROG01_stage_compute_and_harm",
         "DEVELOPMENT_EVIDENCE_MIXED_POPULATION",
         "Analytical compute and harmful-activation share across assembly stages. "
         "Stages 1–3 are measured on ROUTER_DEVELOPMENT; stage 4 on VAL808.",
         "11", ["full_doc_report/tables/REMEDFILM_PROGRESSION_RESULTS.csv"])

    # harm vs benefit
    abl = load_csv(TABLES / "REMEDFILM_ABLATION_RESULTS.csv")
    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    for r in abl:
        n = int(float(r["n_routed"]))
        if n == 0:
            continue
        b = int(float(r["n_beneficial_routed"])) / n * 100
        h = float(r["harmful_activation_share"]) * 100
        col = VERM if r["arm"] in ("A8", "A7") else (PURPLE if r["arm"].startswith(("R", "F")) else GREY)
        ax.scatter(b, h, s=44, color=col, edgecolor="white", linewidth=0.7, zorder=3)
        ax.annotate(r["arm"], (b, h), fontsize=6.2, xytext=(4, 3), textcoords="offset points")
    ax.set_xlabel("Beneficial share of routed cases (%)")
    ax.set_ylabel("Harmful activation share (%)")
    ax.set_title("Benefit versus harm across the 13 ablation arms")
    save(fig, "progression", "PROG02_benefit_harm_tradeoff",
         "FROZEN_HISTORICAL_ABLATION",
         "Each arm's beneficial and harmful activation shares on ROUTER_DEVELOPMENT.",
         "11", ["full_doc_report/tables/REMEDFILM_ABLATION_RESULTS.csv"])


# ================================================================= ablation ====
def fig_ablation() -> None:
    abl = load_csv(TABLES / "REMEDFILM_ABLATION_RESULTS.csv")
    arms = [r["arm"] for r in abl]
    deltas = [float(r["mean_true_delta_dice_routed"]) for r in abl]
    harms = [float(r["harmful_activation_share"]) * 100 for r in abl]
    caps = [float(r["benefit_capture_vs_positive_mass"]) * 100 for r in abl]

    fig, ax = plt.subplots(figsize=(6.8, 2.8))
    colors = [VERM if a == "A8" else (ORANGE if a == "A7" else GREY) for a in arms]
    bars = ax.bar(arms, deltas, color=colors, width=0.66)
    for b, v in zip(bars, deltas):
        ax.text(b.get_x() + b.get_width() / 2, v + (0.0012 if v >= 0 else -0.0026),
                f"{v:+.4f}", ha="center", fontsize=5.6, rotation=90)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_ylabel("Mean Δ Dice on routed cases")
    ax.set_title("13-arm ablation: routed mean improvement (ROUTER_DEVELOPMENT, n = 4,957)")
    ax.grid(axis="x", visible=False)
    save(fig, "ablation", "ABL01_arm_mean_delta",
         "FROZEN_HISTORICAL_ABLATION",
         "Routed mean Δ Dice per arm. A8 (FULL) is the proposed assembly; "
         "F1 collapses under alpha-blend fusion.",
         "12", ["full_doc_report/tables/REMEDFILM_ABLATION_RESULTS.csv"])

    # paired contrasts with CI
    pc = load_csv(ROOT / "reports/tables/phase28_table_07_matched_paired_contrasts.csv")
    bs = {r["contrast"]: r for r in load_csv(
        ROOT / "reports/tables/phase28_table_08_bootstrap_statistics.csv")}
    for r in pc:
        b = bs.get(r["contrast"], {})
        r["ci_low"] = b.get("ci95_low", "")
        r["ci_high"] = b.get("ci95_high", "")
    cols = list(pc[0].keys())
    print("    paired contrast cols:", cols)
    ckey = "contrast"
    pkey = "paired_mean_difference"
    lo = "ci_low"
    hi = "ci_high"
    if pkey and lo and hi:
        fig, ax = plt.subplots(figsize=(6.0, 2.9))
        ys = np.arange(len(pc))
        ticklabels = []
        for i, r in enumerate(pc):
            p = float(r[pkey]); l = float(r[lo]); h = float(r[hi])
            excl = (l > 0 or h < 0)
            col = VERM if excl else GREY
            ax.plot([l, h], [i, i], color=col, linewidth=1.6, solid_capstyle="butt")
            ax.scatter([p], [i], color=col, s=30, zorder=4,
                       edgecolor="white", linewidth=0.5)
            ticklabels.append(f"{r[ckey]}   {'CI excludes 0' if excl else 'CI includes 0'}")
        ax.axvline(0, color="#333333", linewidth=0.8)
        ax.set_yticks(ys)
        ax.set_yticklabels(ticklabels, fontsize=6.2)
        ax.invert_yaxis()
        ax.set_xlabel("Paired Δ Dice (95% CI)")
        ax.set_title("Matched paired contrasts — A8 vs A7 includes zero")
        ax.grid(axis="y", visible=False)
        ax.text(0.03, 0.62,
                "A8_vs_A7 CI is 1.6e-5 wide and is drawn to scale",
                transform=ax.transAxes, fontsize=5.6, color=GREY, va="center")
        save(fig, "ablation", "ABL02_paired_contrasts_forest",
             "FROZEN_HISTORICAL_ABLATION",
             "Paired contrasts with 95% CIs. The only pre-specified matched "
             "contrast (A8 vs A7) includes zero and is reported as such.",
             "12", ["reports/tables/phase28_table_07_matched_paired_contrasts.csv"])

    # harm / capture / n_routed panel
    fig, axes = plt.subplots(1, 3, figsize=(8.0, 2.4), sharex=True)
    x = np.arange(len(arms))
    axes[0].bar(x, harms, color=GREY, width=0.66)
    axes[0].axhline(harms[arms.index("A8")], color=VERM, linestyle="--", linewidth=0.9)
    axes[0].set_title("Harmful activation share (%)")
    axes[1].bar(x, caps, color=SKY, width=0.66)
    axes[1].axhline(caps[arms.index("A8")], color=VERM, linestyle="--", linewidth=0.9)
    axes[1].set_title("Benefit capture (%)")
    axes[2].bar(x, [int(float(r["n_routed"])) for r in abl], color=LGREY, width=0.66)
    axes[2].set_title("Cases routed")
    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(arms, rotation=90, fontsize=5.8)
        ax.grid(axis="x", visible=False)
    fig.suptitle("Ablation diagnostics (dashed = A8 FULL)", fontsize=8.5, y=1.04)
    save(fig, "ablation", "ABL03_ablation_diagnostics",
         "FROZEN_HISTORICAL_ABLATION",
         "Harmful share, benefit capture and routed volume for all 13 arms.",
         "12", ["full_doc_report/tables/REMEDFILM_ABLATION_RESULTS.csv"])


# ========================================================= routing / safety ====
def fig_routing() -> None:
    ps = load_csv(TABLES / "REMEDFILM_INTERNAL_PER_SAMPLE.csv")
    branches = defaultdict(int)
    for r in ps:
        branches[r["branch"]] += 1
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.5),
                             gridspec_kw={"width_ratios": [1, 1.3]})
    ax = axes[0]
    labels = ["SKIP_GLOBAL", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT"]
    vals = [branches.get(l, 0) for l in labels]
    wedges, _, _ = ax.pie(vals, colors=[BLUE, GREEN, PURPLE], startangle=90,
                          autopct=lambda p: f"{p:.1f}%", textprops={"fontsize": 6.5},
                          wedgeprops={"linewidth": 0.8, "edgecolor": "white"})
    ax.legend(wedges, [f"{l.replace('_', ' ').lower()}  {v}" for l, v in zip(labels, vals)],
              loc="center left", bbox_to_anchor=(0.9, 0.5), fontsize=6)
    ax.set_title("Routing outcome on VAL808")

    ax = axes[1]
    order = ["SKIP_GLOBAL", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT"]
    cols = [BLUE, GREEN, PURPLE]
    for i, b in enumerate(order):
        vals = [float(r["delta_dice"]) for r in ps if r["branch"] == b]
        if not vals:
            continue
        ax.hist(vals, bins=31, range=(-0.6, 0.6), histtype="stepfilled", alpha=0.55,
                color=cols[i], label=f"{b.replace('_',' ').lower()} (n={len(vals)})")
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set_xlabel("Δ Dice")
    ax.set_ylabel("Images")
    ax.set_title("Improvement by routing outcome")
    ax.legend(fontsize=6)
    save(fig, "routing_safety", "RT01_routing_outcomes",
         "SAVED_PREDICTIONS_VAL808",
         "Branch distribution and the Δ Dice each branch produces. Rejected "
         "refinements fall back to the backbone.",
         "13", ["full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv"])

    # stage flow
    fig, ax = plt.subplots(figsize=(6.6, 2.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")
    stages = [("808\nimages", "#888888"), ("808 G\nforwards", BLUE),
              ("279 ROI\nselected", ORANGE), ("266\naccepted", GREEN),
              ("13\nrejected", PURPLE)]
    for i, (lab, c) in enumerate(stages):
        x = 0.4 + i * 2.0
        ax.add_patch(FancyBboxPatch((x, 1.5), 1.35, 1.0, boxstyle="round,pad=0.05,rounding_size=0.1",
                                    linewidth=0.9, edgecolor=c, facecolor=c + "22"))
        ax.text(x + 0.67, 2.0, lab, ha="center", va="center", fontsize=7)
        if i:
            ax.add_patch(FancyArrowPatch((x - 0.28, 2.0), (x - 0.02, 2.0),
                                         arrowstyle="-|>", mutation_scale=9,
                                         linewidth=0.9, color="#555555"))
    ax.text(0.4, 3.3, "Stage-wise flow of the FULL assembly on VAL808 (seed 42)",
            fontsize=8.5, fontweight="bold")
    ax.text(0.4, 0.7, "529 images skipped the refiner entirely (65.5%). "
                      "Rejected proposals revert to the backbone mask.",
            fontsize=6.5, color=GREY)
    save(fig, "routing_safety", "RT02_stage_flow",
         "SAVED_PREDICTIONS_VAL808",
         "Counts at every stage of the routing and safety pipeline.",
         "13", ["reports/tables/phase27_val808_predictions.csv"])


# =============================================================== robustness ====
def fig_robustness() -> None:
    d = jload(ROOT / "reports/audits/phase36_robustness_scientific_result_v1_23.json")
    rows = d["image_rows"]
    by = defaultdict(list)
    for r in rows:
        by[r["condition"]].append(float(r["paired_delta_dice"]))
    conds = sorted(by)
    fig, ax = plt.subplots(figsize=(7.0, 2.7))
    means = [np.mean(by[c]) for c in conds]
    cols = [VERM if m < -0.05 else (ORANGE if m < 0 else GREEN) for m in means]
    bars = ax.bar(range(len(conds)), means, color=cols, width=0.68)
    for i, m in enumerate(means):
        ax.text(i, m - 0.008 if m < 0 else m + 0.003, f"{m:+.3f}", ha="center",
                fontsize=5.6, rotation=90, va="top" if m < 0 else "bottom")
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_xticks(range(len(conds)))
    ax.set_xticklabels([c.replace("_", " ").lower() for c in conds], rotation=40,
                       ha="right", fontsize=6.0)
    ax.set_ylabel("Mean Δ Dice vs clean")
    ax.set_title("Phase 36 robustness: 12,928 perturbation instances over 808 clean images")
    ax.grid(axis="x", visible=False)
    save(fig, "robustness", "ROB01_perturbation_degradation",
         "FROZEN_ROBUSTNESS_EXECUTION",
         "Mean paired Δ Dice for each perturbation condition. Resolution loss "
         "dominates; no condition improves accuracy.",
         "14", ["reports/audits/phase36_robustness_scientific_result_v1_23.json"])

    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    doms = ["ISIC", "BUSI", "KVASIR", "KUB"]
    families = {"Blur": "GAUSSIAN_BLUR", "Noise": "GAUSSIAN_NOISE",
                "Contrast": "CONTRAST", "Resolution": "RESOLUTION"}
    width = 0.2
    for i, (fam, prefix) in enumerate(families.items()):
        vals = []
        for dom in doms:
            sub = [float(r["paired_delta_dice"]) for r in rows
                   if r["domain"] == dom and r["condition"].startswith(prefix)]
            vals.append(np.mean(sub) if sub else 0.0)
        ax.bar(np.arange(4) + (i - 1.5) * width, vals, width, label=fam,
               color=[SKY, ORANGE, GREEN, PURPLE][i])
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_xticks(range(4))
    ax.set_xticklabels(doms)
    ax.set_ylabel("Mean Δ Dice vs clean")
    ax.set_title("Domain-specific degradation under perturbation")
    ax.legend(ncol=4, fontsize=6)
    ax.grid(axis="x", visible=False)
    save(fig, "robustness", "ROB02_domain_degradation",
         "FROZEN_ROBUSTNESS_EXECUTION",
         "Perturbation families broken down by clinical domain; KUB degrades most.",
         "14", ["reports/audits/phase36_robustness_scientific_result_v1_23.json"])

    # clean equivalence statement
    ce = d["clean_equivalence"]
    fig, ax = plt.subplots(figsize=(5.2, 2.2))
    ax.axis("off")
    ax.text(0.02, 0.92, "Clean-equivalence gate (Phase 36)", fontsize=9, fontweight="bold")
    lines = [
        f"clean passes                 : {d['counters']['clean_passes']}",
        f"dice comparisons             : {ce['n_dice_comparisons']}",
        f"dice mismatches              : {len(ce['dice_mismatches'])}",
        f"router-decision mismatches   : {len(ce['router_decision_mismatches'])}",
        f"route-branch mismatches      : {len(ce['route_branch_mismatches'])}",
        f"max |Δ Dice| vs frozen       : {ce.get('max_abs_dice_difference', 0.0):.1e}",
        f"test reads                   : {d['counters']['test_reads']}",
        f"training / optimizer steps   : {d['counters']['training']} / {d['counters']['optimizer_steps']}",
    ]
    for i, l in enumerate(lines):
        ax.text(0.02, 0.78 - i * 0.095, l, fontsize=7.2, family="DejaVu Sans Mono")
    save(fig, "robustness", "ROB03_clean_equivalence_gate",
         "FROZEN_ROBUSTNESS_EXECUTION",
         "The robustness execution reproduces the frozen clean predictions exactly, "
         "with zero TEST reads and zero training.",
         "14", ["reports/audits/phase36_robustness_scientific_result_v1_23.json"])


# =============================================================== efficiency ====
def fig_efficiency() -> None:
    rows = load_csv(TABLES / "REMEDFILM_EFFICIENCY.csv")
    dice = {r["model"]: float(r["macro_dice"]) for r in rows}
    params = {r["model"]: int(float(r["params"])) for r in rows}
    gmacs = {r["model"]: (float(r["gmacs"]) if r["gmacs"] else None) for r in rows}

    six_g = load_csv(ROOT / "reports/tables/phase21_six_model_compute.csv")
    gmap = {r["model_key"]: float(r["gmacs"]) for r in six_g}
    name_to_key = {
        "U-Net": "unet", "Attention U-Net": "attention_unet", "U-Net++": "unetpp",
        "DeepLabV3+": "deeplabv3plus",
        "Transformer/MiT-style U-Net": "transformer_mit_unet",
        "GlobalMedFiLM (G)": "global_medfilm",
    }

    fig, ax = plt.subplots(figsize=(5.8, 3.2))
    for m, key in name_to_key.items():
        if m not in dice:
            continue
        gm = gmap.get(key)
        if gm is None:
            continue
        is_g = m.startswith("GlobalMedFiLM")
        ax.scatter(gm, dice[m], s=52 if is_g else 42,
                   color=BLUE if is_g else "#9A9A9A",
                   edgecolor="white", linewidth=0.8, zorder=3)
        name = m.replace(" (G)", "")
        off, ha = {
            "U-Net": ((-36, -10), "left"),
            "Attention U-Net": ((6, 3), "left"),
            "GlobalMedFiLM": ((3, -16), "left"),
            "Transformer/MiT-style U-Net": ((7, -2), "left"),
            "DeepLabV3+": ((7, -2), "left"),
        }.get(name, ((6, -2), "left"))
        ax.annotate(name, (gm, dice[m]), fontsize=6.2, xytext=off, ha=ha,
                    textcoords="offset points", color=DARK)
    # ReMedFiLM FULL — its own point, not a reference line
    rx = gmacs["ReMedFiLM (FULL)"]
    ax.scatter(rx, dice["ReMedFiLM (FULL)"], s=130, marker="*", color=VERM,
               edgecolor="#7A3500", linewidth=0.9, zorder=6)
    ax.annotate("ReMedFiLM FULL\n4.84M params\n32.44 cond. GMACs",
                (rx, dice["ReMedFiLM (FULL)"]), fontsize=6.4, color=VERM,
                xytext=(34, -52), textcoords="offset points", ha="left",
                arrowprops=dict(arrowstyle="-", color=VERM, linewidth=0.7,
                                shrinkA=0, shrinkB=6))
    ax.set_xlabel("Analytical GMACs @ 1×3×512×512 (lower bound)")
    ax.set_ylabel("Macro-domain VAL808 Dice")
    ax.set_title("Accuracy versus architectural cost — ReMedFiLM plotted explicitly")
    ax.set_xlim(25, 136)
    ax.set_ylim(0.780, 0.845)
    save(fig, "efficiency", "EFF01_accuracy_vs_compute",
         "MIXED_ANALYTICAL_COMPUTE_AND_FROZEN_ACCURACY",
         "Accuracy against analytical compute. ReMedFiLM FULL has its own marker; "
         "the earlier report version omitted it.",
         "15", ["reports/tables/phase21_six_model_compute.csv",
                "reports/tables/c2_barr/c2_barr_aggregate.json",
                "full_doc_report/tables/REMEDFILM_EFFICIENCY.csv"])

    # latency
    eff = jload(ROOT / "reports/audits/phase34_efficiency_result_v1_4.json")
    lat = eff["MEASURED_HARDWARE_SPECIFIC_RUNTIME_PROFILE"]["batch1_latency_v1_4"]
    keys = [("GLOBAL_ONLY_C1", "G only\n(skip path)"), ("SKIP_CONTROLLED_PATH", "skip path"),
            ("EXECUTE_CONTROLLED_PATH", "execute path"), ("R_PSI_COMPONENT", "R_psi"),
            ("B_PHI_COMPONENT", "B_phi"), ("S_OMEGA_COMPONENT", "S_omega")]
    fig, ax = plt.subplots(figsize=(5.8, 2.5))
    names = [k[1] for k in keys]
    p50 = [lat[k[0]]["p50_ms"] for k in keys]
    cols = [BLUE, BLUE, VERM, GREEN, ORANGE, PURPLE]
    bars = ax.bar(names, p50, color=cols, width=0.62)
    for b, v in zip(bars, p50):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.3, f"{v:.2f}", ha="center", fontsize=6.5)
    ax.set_ylabel("Batch-1 p50 latency (ms)")
    ax.set_title("Measured GPU latency, RTX 3060 Ti (n = 1,000 per path)")
    ax.grid(axis="x", visible=False)
    ax.text(0.02, 0.95, "forward only, not full data pipeline", transform=ax.transAxes,
            fontsize=6, va="top", color=GREY)
    save(fig, "efficiency", "EFF02_latency_breakdown",
         "MEASURED_HARDWARE_PROFILE",
         "Measured per-component latency. Skip and execute paths bracket the "
         "FULL system's cost.",
         "15", ["reports/audits/phase34_efficiency_result_v1_4.json"])

    # params vs dice
    fig, ax = plt.subplots(figsize=(5.2, 2.8))
    for m, p in params.items():
        if m not in dice:
            continue
        is_full = m == "ReMedFiLM (FULL)"
        is_g = m.startswith("GlobalMedFiLM")
        ax.scatter(p / 1e6, dice[m], s=120 if is_full else 46,
                   marker="*" if is_full else "o",
                   color=VERM if is_full else (BLUE if is_g else "#9A9A9A"),
                   edgecolor="white", linewidth=0.8, zorder=3)
        ax.annotate(m.replace(" (G)", "").replace(" (FULL)", " FULL"),
                    (p / 1e6, dice[m]), fontsize=6.0, xytext=(4, -8),
                    textcoords="offset points")
    ax.set_xlabel("Parameters (millions)")
    ax.set_ylabel("Macro-domain VAL808 Dice")
    ax.set_title("Accuracy versus parameter budget")
    ax.set_xscale("log")
    save(fig, "efficiency", "EFF03_accuracy_vs_parameters",
         "FROZEN_ACCURACY_AND_MEASURED_PARAMETERS",
         "Accuracy against parameter count on a log axis; ReMedFiLM achieves its "
         "score with far fewer parameters than DeepLabV3+.",
         "15", ["full_doc_report/tables/REMEDFILM_EFFICIENCY.csv"])


# =============================================================== statistics ====
def fig_statistics() -> None:
    """Reproducibility and inferential statistics from frozen Phase 29 evidence."""
    d29 = jload(ROOT / "reports/audits/phase29_phase_d_three_seed_descriptive_summary.json")
    per = {m["metric"]: m for m in d29["per_metric"]}
    seeds = ["42", "123", "3407"]

    # STAT01 — seed-wise macro Dice and delta
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.6))
    for ax, key, title, col in (
            (axes[0], "macro_final_dice", "Macro-domain VAL808 Dice", BLUE),
            (axes[1], "macro_delta_dice", "Macro Δ Dice vs backbone", VERM)):
        m = per[key]
        vals = [m[f"seed{x}"] for x in seeds]
        ax.bar(range(3), vals, color=col, width=0.5, alpha=0.85)
        mean, sd = m["mean"], m["sample_sd_ddof1"]
        ax.axhline(mean, color="#333333", linewidth=0.9, linestyle="--")
        ax.fill_between([-0.6, 2.6], mean - sd, mean + sd, color=col, alpha=0.12)
        for i, v in enumerate(vals):
            ax.text(i, v, f"{v:.6f}", ha="center", va="bottom", fontsize=6.0)
        ax.set_xticks(range(3))
        ax.set_xticklabels([f"seed {x}" for x in seeds])
        ax.set_title(title)
        ax.grid(axis="x", visible=False)
        lo = min(vals) - abs(mean) * 0.35 if mean else min(vals) * 0.9
        ax.set_ylim(lo, max(vals) + abs(mean) * 0.45)
        ax.text(0.02, 0.05, f"mean {mean:.6f}\nSD {sd:.2e}", transform=ax.transAxes,
                fontsize=6.0, va="bottom", color=GREY)
    fig.suptitle("Three downstream seeds — descriptive only, shared frozen backbone",
                 fontsize=8.5, y=1.03)
    save(fig, "statistics", "STAT01_seedwise_macro_metrics",
         "FROZEN_PHASE29_DESCRIPTIVE",
         "Per-seed macro Dice and Δ Dice with the across-seed mean and SD band. "
         "The backbone is identical across seeds, so this is not end-to-end replication.",
         "09", ["reports/audits/phase29_phase_d_three_seed_descriptive_summary.json"])

    # STAT02 — bootstrap distribution of the paired macro delta
    pd_ = jload(TABLES / "REMEDFILM_PAIRED_DELTA.json")
    hist = pd_.get("bootstrap_hist")
    fig, ax = plt.subplots(figsize=(5.4, 2.6))
    if hist:
        edges = np.array(hist["bin_edges"])
        counts = np.array(hist["counts"])
        centers = (edges[:-1] + edges[1:]) / 2
        width = edges[1] - edges[0]
        ax.bar(centers, counts, width=width, color=SKY, edgecolor="white", linewidth=0.3)
    ax.axvline(pd_["point"], color=VERM, linewidth=1.4, label=f"point {pd_['point']:+.5f}")
    for v, lab in ((pd_["ci_low"], "2.5%"), (pd_["ci_high"], "97.5%")):
        ax.axvline(v, color="#333333", linewidth=0.9, linestyle="--")
        ax.text(v, ax.get_ylim()[1] * 0.62, f" {lab}", fontsize=6, color="#333333")
    ax.axvline(0, color="#999999", linewidth=0.8, linestyle=":")
    ax.set_xlabel("Macro Δ Dice (ReMedFiLM FULL − GlobalMedFiLM)")
    ax.set_ylabel("Bootstrap replicates")
    ax.set_title(f"Domain-stratified bootstrap, B = {pd_['n_boot']:,}, seed {pd_['seed']}")
    ax.legend(loc="upper left", fontsize=6.5)
    save(fig, "statistics", "STAT02_bootstrap_distribution",
         "DERIVED_FROM_SAVED_PREDICTIONS",
         "Empirical bootstrap distribution of the paired macro Δ Dice on VAL808; "
         "the whole distribution lies above zero.",
         "09", ["full_doc_report/tables/REMEDFILM_PAIRED_DELTA.json"])

    # STAT03 — per-domain Dice by seed
    d29v = jload(ROOT / "reports/audits/phase29_val808_seedwise_metrics.json")
    by_seed = d29v["metrics_by_seed"]
    doms = ["ISIC", "BUSI", "KVASIR", "KUB"]
    fig, ax = plt.subplots(figsize=(6.2, 2.6))
    w = 0.24
    for i, sd_ in enumerate(seeds):
        vals = [by_seed[sd_]["per_domain"][d]["final_dice"] for d in doms]
        ax.bar(np.arange(4) + (i - 1) * w, vals, w, label=f"seed {sd_}",
               color=[BLUE, ORANGE, PURPLE][i])
    ax.set_xticks(range(4))
    ax.set_xticklabels(doms)
    ax.set_ylabel("ReMedFiLM FULL Dice")
    ax.set_ylim(0.70, 0.95)
    ax.set_title("Per-domain FULL-system Dice across the three downstream seeds")
    ax.legend(ncol=3, fontsize=6.5)
    ax.grid(axis="x", visible=False)
    save(fig, "statistics", "STAT03_seedwise_per_domain",
         "FROZEN_PHASE29_DESCRIPTIVE",
         "Per-domain FULL-system Dice for seeds 42/123/3407. Variation is confined "
         "to the re-fitted components, not the backbone.",
         "09", ["reports/audits/phase29_val808_seedwise_metrics.json"])

    # STAT04 — population accounting
    fig, ax = plt.subplots(figsize=(6.0, 2.3))
    labels = ["TRAIN\n5,832", "ROUTER_DEV\n4,957", "ROUTER_HOLDOUT\n875",
              "VAL\n808", "TEST\n1,683\n(consumed)"]
    vals = [5832, 4957, 875, 808, 1683]
    cols = [BLUE, SKY, GREEN, ORANGE, LGREY]
    bars = ax.bar(labels, vals, color=cols, width=0.62)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 60, f"{v:,}", ha="center", fontsize=6.8)
    ax.set_ylabel("Images")
    ax.set_ylim(0, 6600)
    ax.set_title("Population accounting — which cohort each result belongs to")
    ax.grid(axis="x", visible=False)
    ax.text(0.015, 0.90, "TRAIN splits exactly into ROUTER_DEV + ROUTER_HOLDOUT",
            transform=ax.transAxes, fontsize=6.2, color=GREY)
    save(fig, "statistics", "STAT04_population_accounting",
         "FROZEN_MANIFEST",
         "Every reported metric is tied to one of these cohorts; they are never pooled.",
         "02", ["manifests/phase4_v3/train.csv", "manifests/phase4_v3/val.csv",
                "reports/audits/phase25g_holdout_reservation_for_phase30.json"])


def main() -> None:
    print("Building figures...")
    fig_architecture()
    fig_datasets()
    fig_training()
    fig_internal()
    fig_subgroups()
    fig_segmentation()
    fig_external()
    fig_progression()
    fig_ablation()
    fig_routing()
    fig_robustness()
    fig_efficiency()
    fig_statistics()
    (OUT / "figure_registry.json").write_text(json.dumps(REGISTRY, indent=2), encoding="utf-8")
    print(f"\nTOTAL FIGURES {len(REGISTRY)}")


if __name__ == "__main__":
    main()
