"""Phase 24 (3/4) — deterministic DESIGN figures.

DESIGN SPECIFICATION ONLY. Every figure is a design diagram: it contains NO
experimental results, NO hypothetical performance curves presented as
measurements, and NO invented numbers. Where a numeric target appears (parameter
envelopes, budgets, margins), it is a pre-registered DESIGN TARGET read directly
from the Phase-24 spec artifacts.

Writes reports/figures/phase24_architecture_spec/:
    p24_full_system_architecture.png
    p24_pre_gate_vs_post_safety.png
    p24_train_router_holdout_flow.png
    p24_crossfit_gain_label_generation.png
    p24_resource_budget_evaluation.png
    p24_novelty_boundary.png

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/build_phase24_figures.py
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

ROOT = Path(r"D:/Softfors/jup")
FIG = ROOT / "reports" / "figures" / "phase24_architecture_spec"
FIG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 110, "font.family": "DejaVu Sans",
    "font.size": 10, "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.facecolor": "white", "savefig.bbox": "tight", "savefig.pad_inches": 0.22,
})

INK = "#2C2C2A"
MUTED = "#5F5E5A"
EDGE = "#444441"
C_GLOBAL = "#B5D4F4"; C_GLOBAL_E = "#185FA5"
C_ROUTER = "#C0DD97"; C_ROUTER_E = "#3B6D11"
C_REFINE = "#FAC775"; C_REFINE_E = "#854F0B"
C_FALLBK = "#D3D1C7"; C_FALLBK_E = "#5F5E5A"
C_NOVEL = "#97C459"; C_NOVEL_E = "#173404"
C_NONNOV = "#B4B2A9"; C_NONNOV_E = "#444441"
C_BAD = "#F7C1C1"; C_BAD_E = "#A32D2D"
BAND = "#F1EFE8"
HDR = "#E6F1FB"

OUT: dict[str, dict] = {}


def box(ax, x, y, w, h, title, sub="", face="white", edge=EDGE, ts=10.4, ss=8.6,
        tc=INK, lw=1.1, radius=1.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"round,pad=0.55,rounding_size={radius}",
                                facecolor=face, edgecolor=edge, linewidth=lw, zorder=2))
    if sub:
        ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center",
                fontsize=ts, fontweight="bold", color=tc, zorder=3)
        ax.text(x + w / 2, y + h * 0.28, sub, ha="center", va="center",
                fontsize=ss, color="#444441", zorder=3)
    else:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center",
                fontsize=ts, fontweight="bold", color=tc, zorder=3)


def arrow(ax, x1, y1, x2, y2, color=EDGE, lw=1.5, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                 mutation_scale=13, color=color, linewidth=lw,
                                 linestyle=ls, zorder=4,
                                 shrinkA=0, shrinkB=0))


def canvas(w=13.4, h=8.2, xlim=(0, 100), ylim=(0, 100)):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis("off")
    return fig, ax


def title(ax, t, sub=None, y=97.4):
    ax.text(50, y, t, ha="center", va="top", fontsize=14.5, fontweight="bold", color=INK)
    if sub:
        ax.text(50, y - 3.6, sub, ha="center", va="top", fontsize=9.8, color=MUTED,
                style="italic")


def stamp(ax, y=1.5, x=50):
    ax.text(x, y, "DESIGN SPECIFICATION — NOT EXPERIMENTAL RESULTS",
            ha="center", va="bottom", fontsize=9.4, fontweight="bold", color="#A32D2D")


def save(fig, name, display):
    out = FIG / name
    fig.savefig(out, format="png", facecolor="white")
    plt.close(fig)
    raw = out.read_bytes()
    OUT[name] = {"figure_id": name.replace(".png", ""), "display_name": display,
                 "path": str(out.relative_to(ROOT)).replace("\\", "/"),
                 "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


# ===========================================================================
# FIG 1 — FULL SYSTEM ARCHITECTURE (§5)
# ===========================================================================
def fig_full_system():
    fig, ax = canvas(13.8, 8.6)
    title(ax, "RA-MedFiLM-BARR — full system architecture",
          "Resource-Aware MedFiLM with Benefit-Aware Refinement Routing · design only")

    # left stack
    box(ax, 3, 78, 24, 8.0, "Image + task_id", "(x, t)", HDR, C_GLOBAL_E)
    box(ax, 3, 65, 24, 8.6, "Frozen Global MedFiLM", "G(x,t) → p_global, F_global",
        C_GLOBAL, C_GLOBAL_E)
    box(ax, 3, 52, 24, 8.0, "GT-free ROI proposal", "predicted fg → bbox → pad",
        "#FFFFFF", EDGE)
    box(ax, 3, 39, 24, 8.0, "Regional features", "ROI-pooled from F_global",
        "#FFFFFF", EDGE)

    arrow(ax, 15, 78, 15, 73.6)
    arrow(ax, 15, 65, 15, 60.0)
    arrow(ax, 15, 52, 15, 47.0)

    # router (novel)
    box(ax, 33, 41, 26, 15.0, "Benefit Router  B_phi",
        "predicts PAIRED REFINEMENT GAIN\nbefore refinement runs",
        C_NOVEL, C_NOVEL_E, ts=11.0)
    arrow(ax, 27, 43, 33, 46)
    arrow(ax, 27, 68, 33, 54, color=C_GLOBAL_E, ls=(0, (4, 2)))
    ax.text(30, 61.5, "reuses F_global\n(no 2nd forward)", ha="center", va="center",
            fontsize=7.4, color=C_GLOBAL_E, style="italic")

    # utility gate
    box(ax, 33, 25, 26, 12.6, "Pre-execution gate",
        "U_hat = Delta_hat − lambda·C\nEXECUTE if U_hat > tau", "#FFFFFF", EDGE, ts=10.6)
    arrow(ax, 46, 41, 46, 37.8)

    # branches
    box(ax, 6, 9.5, 17, 9.0, "SKIP", "final = global", C_FALLBK, C_FALLBK_E, ts=10.0)
    box(ax, 30, 9.5, 26, 9.0, "Dedicated Regional Refiner  R_psi",
        "crop-trained, ≤2.0M params (TARGET)", C_REFINE, C_REFINE_E, ts=9.6, ss=8.0)
    arrow(ax, 40, 25, 15, 18.7, color=C_FALLBK_E)
    arrow(ax, 52, 25, 43, 18.7, color=C_REFINE_E)
    ax.text(26, 22.2, "SKIP", ha="center", va="center", fontsize=8.2,
            fontweight="bold", color=C_FALLBK_E)
    ax.text(50, 22.2, "EXECUTE", ha="center", va="center", fontsize=8.2,
            fontweight="bold", color=C_REFINE_E)

    # post safety
    box(ax, 61, 9.5, 24, 9.0, "Post-refinement safety  S_omega",
        "accept / reject · does NOT save compute", C_NONNOV, C_NONNOV_E, ts=9.4, ss=7.8)
    arrow(ax, 56, 14.0, 61, 14.0, color=C_REFINE_E)
    arrow(ax, 73, 18.7, 73, 26.5, color=C_NONNOV_E, ls=(0, (4, 2)))
    ax.text(76.5, 22.6, "reject → global", ha="left", va="center", fontsize=7.6,
            color=C_NONNOV_E, style="italic")

    # final
    box(ax, 40, 1.2, 40, 6.4, "Final mask — fusion",
        "outside ROI global · inside ROI refined", "#E1F5EE", "#0F6E56", ts=10.0)
    arrow(ax, 14.5, 9.5, 40, 7.0, color=C_FALLBK_E)
    arrow(ax, 73, 9.5, 66, 7.6, color=C_NONNOV_E)

    # legend
    ax.add_patch(Rectangle((84, 62), 15.2, 21.5, facecolor=BAND,
                           edgecolor=C_NONNOV_E, linewidth=0.8))
    ax.text(91.6, 81.5, "component status", ha="center", va="center", fontsize=8.0,
            fontweight="bold", color=INK)
    for i, (c, e, lab) in enumerate([
        (C_NOVEL, C_NOVEL_E, "NOVELTY-BEARING\n(pre-exec gate)"),
        (C_NONNOV, C_NONNOV_E, "NON-NOVEL PRESERVED\n(post safety/fallback)"),
        (C_GLOBAL, C_GLOBAL_E, "FROZEN REFERENCE"),
    ]):
        yy = 76.5 - i * 5.6
        ax.add_patch(Rectangle((85.4, yy), 2.4, 2.4, facecolor=c, edgecolor=e, linewidth=1.0))
        ax.text(88.6, yy + 1.2, lab, ha="left", va="center", fontsize=7.0, color=INK)

    stamp(ax)
    save(fig, "p24_full_system_architecture.png",
         "Full system architecture (design)")


# ===========================================================================
# FIG 2 — PRE-GATE vs POST-SAFETY (§5, §20)
# ===========================================================================
def fig_pre_vs_post():
    fig, ax = canvas(13.6, 6.6)
    title(ax, "Two decisions that must not be confused",
          "the pre-execution gate saves compute; the post-refinement safety does not")

    # left panel: pre-execution gate
    ax.add_patch(Rectangle((2, 14), 45, 72, facecolor="#EAF3DE",
                           edgecolor=C_ROUTER_E, linewidth=1.2))
    ax.text(24.5, 83.0, "PRE-EXECUTION GATE  (novelty-bearing)", ha="center", va="center",
            fontsize=10.6, fontweight="bold", color=C_NOVEL_E)
    box(ax, 6, 72.5, 37, 6.6, "predict paired gain  Delta_hat", "GT-free, before refinement",
        "white", EDGE, ts=9.4, ss=8.0)
    box(ax, 6, 62.5, 37, 6.6, "decide  EXECUTE / SKIP", "U_hat = Delta_hat − lambda·C",
        "white", EDGE, ts=9.4, ss=8.0)
    arrow(ax, 24.5, 72.5, 24.5, 69.1)
    box(ax, 6, 50.0, 37, 8.0, "SKIP  →  refinement never runs",
        "compute is genuinely saved", C_FALLBK, C_FALLBK_E, ts=9.3, ss=8.0)
    box(ax, 6, 38.5, 37, 8.0, "EXECUTE  →  refinement runs",
        "compute is spent", C_REFINE, C_REFINE_E, ts=9.3, ss=8.0)
    arrow(ax, 16, 62.5, 16, 58.0, color=C_FALLBK_E)
    arrow(ax, 33, 62.5, 33, 46.5, color=C_REFINE_E)
    ax.text(24.5, 30.0, "compute saved  =  fraction of SKIP decisions",
            ha="center", va="center", fontsize=8.8, fontweight="bold", color=C_NOVEL_E)
    ax.text(24.5, 25.0,
            "This is the ONLY component that saves compute.\n"
            "It is also the only component with a residual claim.",
            ha="center", va="center", fontsize=8.2, color=C_NOVEL_E, style="italic")

    # right panel: post safety
    ax.add_patch(Rectangle((53, 14), 45, 72, facecolor="#F1EFE8",
                           edgecolor=C_NONNOV_E, linewidth=1.2))
    ax.text(75.5, 83.0, "POST-REFINEMENT SAFETY  (non-novel)", ha="center", va="center",
            fontsize=10.6, fontweight="bold", color=C_NONNOV_E)
    box(ax, 57, 72.5, 37, 6.6, "refinement ALREADY RAN", "compute already spent",
        C_REFINE, C_REFINE_E, ts=9.4, ss=8.0)
    box(ax, 57, 62.5, 37, 6.6, "compare global vs refined", "S_omega, prediction-only",
        "white", EDGE, ts=9.4, ss=8.0)
    arrow(ax, 75.5, 72.5, 75.5, 69.1)
    box(ax, 57, 50.0, 37, 8.0, "REJECT  →  keep global",
        "quality preserved, compute NOT recovered", C_FALLBK, C_FALLBK_E, ts=9.3, ss=8.0)
    box(ax, 57, 38.5, 37, 8.0, "ACCEPT  →  use refined",
        "quality possibly improved", "#FFFFFF", EDGE, ts=9.3, ss=8.0)
    arrow(ax, 67, 62.5, 67, 58.0, color=C_FALLBK_E)
    arrow(ax, 84, 62.5, 84, 46.5)
    ax.text(75.5, 30.0, "compute saved  =  0  (always)",
            ha="center", va="center", fontsize=8.8, fontweight="bold", color="#A32D2D")
    ax.text(75.5, 25.0,
            "JFS already occupies this decision.\n"
            "It is a CONTROLLED CORE EXTENSION, never the contribution.",
            ha="center", va="center", fontsize=8.2, color="#791F1F", style="italic")

    arrow(ax, 47, 44, 53, 44, color="#A32D2D", lw=2.0)
    ax.text(50, 47.5, "must not\nbe merged", ha="center", va="bottom", fontsize=7.6,
            fontweight="bold", color="#A32D2D")

    stamp(ax, y=6.0)
    save(fig, "p24_pre_gate_vs_post_safety.png",
         "Pre-execution gate vs post-refinement safety (design)")


# ===========================================================================
# FIG 3 — TRAIN ROUTER / HOLDOUT FLOW (§13-16)
# ===========================================================================
def fig_holdout_flow():
    fig, ax = canvas(13.6, 7.8)
    title(ax, "TRAIN-only routing development protocol",
          "the Phase-22 VAL population is excluded from router training by construction")

    total_w = 92.0
    x0 = 4.0
    y = 66.0
    h = 13.0

    # original TRAIN bar
    ax.add_patch(FancyBboxPatch((x0, y), total_w, h,
                                boxstyle="round,pad=0.6,rounding_size=1.6",
                                facecolor=HDR, edgecolor=C_GLOBAL_E, linewidth=1.4))
    ax.text(x0 + total_w / 2, y + h + 4.4,
            "ORIGINAL TRAIN — manifests/phase4_v3/train.csv — 5,832 cases",
            ha="center", va="center", fontsize=10.8, fontweight="bold", color=C_GLOBAL_E)
    ax.text(x0 + total_w / 2, y + h - 2.6,
            "4 domains · KUB 1,978 · KVASIR 696 · ISIC 2,556 · BUSI 602 · grouped by patient_id",
            ha="center", va="center", fontsize=8.4, color=MUTED)

    dev_w = total_w * 0.85
    ho_w = total_w * 0.15
    ax.add_patch(Rectangle((x0, y), dev_w, h - 5.0, facecolor="#EAF3DE",
                           edgecolor=C_ROUTER_E, linewidth=1.3))
    ax.add_patch(Rectangle((x0 + dev_w, y), ho_w, h - 5.0, facecolor="#FBEAF0",
                           edgecolor="#993556", linewidth=1.3))
    ax.text(x0 + dev_w / 2, y + (h - 5.0) / 2, "ROUTER_DEVELOPMENT  ~85%  (~4,957)",
            ha="center", va="center", fontsize=9.6, fontweight="bold", color=C_NOVEL_E)
    ax.text(x0 + dev_w + ho_w / 2, y + (h - 5.0) / 2 + 1.6,
            "ROUTER_HOLDOUT", ha="center", va="center", fontsize=8.2,
            fontweight="bold", color="#72243E")
    ax.text(x0 + dev_w + ho_w / 2, y + (h - 5.0) / 2 - 1.6,
            "15% (~875)", ha="center", va="center", fontsize=7.6, color="#72243E")

    # downstream use of DEVELOPMENT
    box(ax, 4, 44, 30, 10.5, "cross-fitted gain labels",
        "3 folds · OOF (see Fig 4)", "white", EDGE, ts=9.6, ss=8.2)
    box(ax, 4, 30, 30, 10.5, "fit benefit router  B_phi", "on OOF targets only",
        C_NOVEL, C_NOVEL_E, ts=9.6, ss=8.2)
    box(ax, 4, 16, 30, 10.5, "calibrate lambda, tau", "TRAIN development only",
        "white", EDGE, ts=9.6, ss=8.2)
    arrow(ax, 19, 66, 19, 54.9, color=C_ROUTER_E)
    arrow(ax, 19, 44, 19, 41.0)
    arrow(ax, 19, 30, 19, 27.0)

    # holdout panel
    ax.add_patch(FancyBboxPatch((42, 14), 28, 41,
                                boxstyle="round,pad=0.7,rounding_size=1.8",
                                facecolor="#FBEAF0", edgecolor="#993556", linewidth=1.4))
    ax.text(56, 51.5, "ROUTER_HOLDOUT", ha="center", va="center",
            fontsize=10.4, fontweight="bold", color="#72243E")
    arrow(ax, x0 + dev_w + ho_w / 2, 60.9, 56, 55.4, color="#993556")
    ax.text(56, 45.0, "designated BEFORE", ha="center", va="center", fontsize=8.2,
            fontweight="bold", color="#993556")
    for i, t in enumerate(["refiner performance inspection",
                           "benefit-router fitting",
                           "feature selection",
                           "lambda selection",
                           "threshold fitting"]):
        ax.text(56, 39.0 - i * 3.4, "–  " + t, ha="center", va="center",
                fontsize=7.8, color="#72243E")
    ax.text(56, 19.5, "Phase-24 inspection: ids, counts,\ngroup integrity ONLY",
            ha="center", va="center", fontsize=7.8, fontweight="bold",
            color="#72243E", style="italic")

    # forbidden panel
    ax.add_patch(FancyBboxPatch((74, 14), 24, 41,
                                boxstyle="round,pad=0.7,rounding_size=1.8",
                                facecolor="#FCEBEB", edgecolor="#A32D2D", linewidth=1.4))
    ax.text(86, 51.5, "EXCLUDED", ha="center", va="center",
            fontsize=10.4, fontweight="bold", color="#501313")
    for i, (t, s) in enumerate([
        ("VAL (808)", "Phase-22 frozen\nsecondary benchmark only"),
        ("TEST (1,683)", "CLOSED — 0 reads"),
    ]):
        box(ax, 76.5, 38.0 - i * 13.0, 19, 10.0, t, s, "#FFFFFF", "#A32D2D",
            ts=9.0, ss=7.4)
    ax.text(86, 19.5, "never router training data", ha="center", va="center",
            fontsize=7.8, fontweight="bold", color="#791F1F", style="italic")

    stamp(ax, y=6.0)
    save(fig, "p24_train_router_holdout_flow.png",
         "TRAIN-only router development protocol (design)")


# ===========================================================================
# FIG 4 — CROSS-FIT GAIN LABEL GENERATION (§14)
# ===========================================================================
def fig_crossfit():
    fig, ax = canvas(13.6, 7.4)
    title(ax, "Out-of-fold paired-gain label generation",
          "gain labels must never come from a refiner evaluated on its own training samples")

    x0, w = 6.0, 88.0
    rows = [
        ("Fold 1", ["TRAIN", "TRAIN", "INFER"], 1),
        ("Fold 2", ["TRAIN", "INFER", "TRAIN"], 0),
        ("Fold 3", ["INFER", "TRAIN", "TRAIN"], 0),
    ]
    seg = w / 3
    top = 74.0
    rh = 13.0
    for i, (label, cells, _) in enumerate(rows):
        y = top - i * (rh + 4.0)
        ax.text(x0 - 1.5, y + rh / 2, label, ha="right", va="center",
                fontsize=9.6, fontweight="bold", color=INK)
        for j, c in enumerate(cells):
            face = {"TRAIN": "#B5D4F4", "INFER": "#FAC775"}[c]
            edge = {"TRAIN": C_GLOBAL_E, "INFER": C_REFINE_E}[c]
            ax.add_patch(Rectangle((x0 + j * seg, y), seg - 1.2, rh,
                                   facecolor=face, edgecolor=edge, linewidth=1.2))
            ax.text(x0 + j * seg + (seg - 1.2) / 2, y + rh / 2,
                    ("train $R_\\psi$" if c == "TRAIN" else "infer $R_\\psi$  →  OOF"),
                    ha="center", va="center", fontsize=8.4, fontweight="bold",
                    color=("#185FA5" if c == "TRAIN" else "#633806"))

    # the label formula
    y_f = 19.5
    ax.add_patch(FancyBboxPatch((x0, y_f), w, 13.0,
                                boxstyle="round,pad=0.7,rounding_size=1.8",
                                facecolor="#EAF3DE", edgecolor=C_ROUTER_E, linewidth=1.5))
    ax.text(x0 + w / 2, y_f + 9.4,
            "for fold-k samples:   DeltaDice_i  =  Dice(R_i, GT_i)  −  Dice(G_i, GT_i)",
            ha="center", va="center", fontsize=11.0, fontweight="bold", color=C_NOVEL_E)
    ax.text(x0 + w / 2, y_f + 4.6,
            "concatenate the three OOF blocks  →  the router-training target table",
            ha="center", va="center", fontsize=8.8, color=C_NOVEL_E, style="italic")

    for j in range(3):
        arrow(ax, x0 + j * seg + (seg - 1.2) / 2, 20.9,
              x0 + j * seg + (seg - 1.2) / 2, 0, color=C_REFINE_E, lw=1.1)
    ax.text(x0 + w / 2, 15.6,
            "sample i is labelled by a refiner that NEVER saw i during its own fitting",
            ha="center", va="center", fontsize=8.6, fontweight="bold", color="#633806")

    ax.text(x0 + w / 2, 8.0,
            "GT is used ONLY on the label side. The router's INPUTS remain GT-free.",
            ha="center", va="center", fontsize=8.6, color=MUTED, style="italic")

    stamp(ax, y=2.0)
    save(fig, "p24_crossfit_gain_label_generation.png",
         "Out-of-fold paired-gain label generation (design)")


# ===========================================================================
# FIG 5 — RESOURCE BUDGET EVALUATION (§17)
# ===========================================================================
def fig_resource_budget():
    fig, ax = canvas(13.4, 7.0)
    title(ax, "Pre-registered fixed-budget evaluation grid",
          "five activation budgets; intermediate thresholds calibrated on TRAIN development only")

    budgets = ["0%", "10%", "25%", "50%", "100%"]
    notes = [
        "global-only\n(no refinement)",
        "sparse routing\n(most conservative)",
        "moderate routing",
        "dense routing",
        "always-refine\n(no routing)",
    ]
    colors = [C_FALLBK, "#C0DD97", "#97C459", "#FAC775", C_REFINE]
    edges = [C_FALLBK_E, C_ROUTER_E, C_ROUTER_E, C_REFINE_E, C_REFINE_E]

    w = 17.0
    gap = 1.6
    x = 3.0
    y = 38.0
    h = 26.0
    for i, (b, n, c, e) in enumerate(zip(budgets, notes, colors, edges)):
        xx = x + i * (w + gap)
        ax.add_patch(FancyBboxPatch((xx, y), w, h,
                                    boxstyle="round,pad=0.6,rounding_size=1.8",
                                    facecolor=c, edgecolor=e, linewidth=1.3))
        ax.text(xx + w / 2, y + h - 4.6, b, ha="center", va="center",
                fontsize=15.0, fontweight="bold", color="#04342C")
        ax.text(xx + w / 2, y + h - 11.0, "activation", ha="center", va="center",
                fontsize=7.8, color=INK)
        ax.text(xx + w / 2, y + 8.0, n, ha="center", va="center",
                fontsize=8.0, color="#2C2C2A")

    arrow(ax, 3.0, 32.0, 94.0, 32.0, color=MUTED, lw=1.2)
    ax.text(3.0, 28.6, "less compute", ha="left", va="center", fontsize=8.4, color=MUTED)
    ax.text(94.0, 28.6, "more compute", ha="right", va="center", fontsize=8.4, color=MUTED)

    ax.add_patch(FancyBboxPatch((3, 12.5), 91, 12.0,
                                boxstyle="round,pad=0.7,rounding_size=1.8",
                                facecolor=BAND, edgecolor=EDGE, linewidth=1.0))
    ax.text(48.5, 21.4, "for each budget point report the frozen metric set",
            ha="center", va="center", fontsize=9.4, fontweight="bold", color=INK)
    ax.text(48.5, 16.4,
            "benefit capture@budget · mean true DeltaDice · harmful activation rate · "
            "missed-benefit rate · routing regret vs oracle",
            ha="center", va="center", fontsize=7.9, color=MUTED)

    ax.text(48.5, 7.4,
            "The x-axis is a DESIGN GRID, not a measured curve. No performance value is shown "
            "because none has been measured.",
            ha="center", va="center", fontsize=8.6, fontweight="bold", color="#A32D2D")

    stamp(ax, y=1.5)
    save(fig, "p24_resource_budget_evaluation.png",
         "Pre-registered fixed-budget evaluation grid (design)")


# ===========================================================================
# FIG 6 — NOVELTY BOUNDARY (§2, §4)
# ===========================================================================
def fig_novelty_boundary():
    fig, ax = canvas(13.6, 7.8)
    title(ax, "Novelty boundary inherited from Phase 23",
          "what RA-MedFiLM-BARR may and may not claim")

    # permitted band
    ax.add_patch(FancyBboxPatch((3, 62), 94, 22,
                                boxstyle="round,pad=0.7,rounding_size=2.0",
                                facecolor="#EAF3DE", edgecolor=C_NOVEL_E, linewidth=1.8))
    ax.text(50, 79.4, "PERMITTED — Level 2, scoped to the integrated residual only",
            ha="center", va="center", fontsize=11.4, fontweight="bold", color=C_NOVEL_E)
    ax.text(50, 74.0,
            "a learned, GT-free, PRE-EXECUTION predictor of the paired refinement gain,",
            ha="center", va="center", fontsize=9.4, color="#173404")
    ax.text(50, 69.8,
            "used to route an optional regional refinement, with preservation fallback",
            ha="center", va="center", fontsize=9.4, color="#173404")
    ax.text(50, 65.6,
            "and an explicit resource-cost term, in ONE shared multi-domain system",
            ha="center", va="center", fontsize=9.4, color="#173404")

    # axis statuses
    axes = [("A  problem formulation", "OCCUPIED", C_BAD, C_BAD_E),
            ("B  learning target", "NOT OCCUPIED AS A\nLEARNED SEG. TARGET", "#FAC775", C_REFINE_E),
            ("C  decision mechanism", "PARTIALLY OCCUPIED", "#FAC775", C_REFINE_E),
            ("D  system integration", "NOT OCCUPIED\nAS A COMBINATION", C_NOVEL, C_NOVEL_E)]
    w = 22.4
    for i, (n, s, c, e) in enumerate(axes):
        xx = 3.0 + i * (w + 1.2)
        ax.add_patch(FancyBboxPatch((xx, 44.5), w, 13.5,
                                    boxstyle="round,pad=0.55,rounding_size=1.5",
                                    facecolor=c, edgecolor=e, linewidth=1.3))
        ax.text(xx + w / 2, 55.0, f"AXIS {n[0]}", ha="center", va="center",
                fontsize=9.6, fontweight="bold", color="#2C2C2A")
        ax.text(xx + w / 2, 50.8, n.split("  ")[1], ha="center", va="center",
                fontsize=7.4, color="#2C2C2A")
        ax.text(xx + w / 2, 47.2, s, ha="center", va="center",
                fontsize=6.9, fontweight="bold", color="#2C2C2A")
    ax.text(50, 41.0, "D is the only axis carrying the residual claim",
            ha="center", va="center", fontsize=8.8, fontweight="bold", color=C_NOVEL_E)

    # forbidden band
    ax.add_patch(FancyBboxPatch((3, 21.5), 94, 16.5,
                                boxstyle="round,pad=0.7,rounding_size=2.0",
                                facecolor="#FCEBEB", edgecolor=C_BAD_E, linewidth=1.8))
    ax.text(50, 35.2, "FORBIDDEN", ha="center", va="center",
            fontsize=11.4, fontweight="bold", color="#501313")
    for i, t in enumerate([
        '"counterfactual" · "causal exposure" · "certified" · "guaranteed"',
        '"novel gate mechanism" · "novel CATE target" · "novel multi-domain segmentation"',
        '"first-ever" · "never done before" · "mobile ready" · "real-time" · "best method"',
    ]):
        ax.text(50, 30.6 - i * 3.3, t, ha="center", va="center",
                fontsize=8.4, color="#791F1F")
    ax.text(50, 23.2,
            '"performance preserving" is unlockable ONLY after the frozen '
            'non-inferiority criterion (Δ > −0.005) is actually satisfied',
            ha="center", va="center", fontsize=7.8, fontweight="bold",
            color="#791F1F", style="italic")

    # closest prior art line
    ax.add_patch(FancyBboxPatch((3, 7.5), 94, 11.0,
                                boxstyle="round,pad=0.6,rounding_size=1.6",
                                facecolor=HDR, edgecolor=C_GLOBAL_E, linewidth=1.2))
    ax.text(50, 15.8, "closest prior art — the margin that must be argued",
            ha="center", va="center", fontsize=9.0, fontweight="bold", color=C_GLOBAL_E)
    ax.text(50, 11.4,
            "JFS (post-hoc, untrained) · metareasoning 1991 · Viola–Jones 2001 · "
            "Latotzke 2021 · CATE 2019 · Med-DANet V2 · M4oE · Learning to Defer",
            ha="center", va="center", fontsize=7.9, color="#185FA5")

    stamp(ax, y=1.2)
    save(fig, "p24_novelty_boundary.png", "Novelty boundary (design)")


def main() -> int:
    fig_full_system()
    fig_pre_vs_post()
    fig_holdout_flow()
    fig_crossfit()
    fig_resource_budget()
    fig_novelty_boundary()

    manifest = {
        "artifact": "phase24_figure_manifest",
        "phase": 24,
        "classification": "DESIGN_SPECIFICATION_FIGURES",
        "contains_experimental_results": False,
        "contains_hypothetical_performance_curves": False,
        "n_figures": len(OUT),
        "figures": OUT,
        "test_reads": 0,
        "training": False,
        "inference": False,
    }
    (FIG / "phase24_figure_manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")

    for k, v in OUT.items():
        print(f"  {k:46s} {v['bytes']:>8d}B  {v['sha256'][:16]}")
    print(f"\n{len(OUT)} design figures written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
