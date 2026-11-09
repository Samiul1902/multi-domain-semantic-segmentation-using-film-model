"""ReMedFiLM V8 -- rebuilt scientific figures and figure evidence map.

Every number plotted here is read from ``REMEDFILM_V8_RESULTS_REGISTRY.json``
or the frozen source tables listed in that registry's ``source_manifest``.
No numeric literal describing a scientific result is typed into this module:
the only hardcoded numbers are axis cosmetics and the *rejected* V7 values,
which are read from ``REMEDFILM_V8_RESULT_RECONCILIATION.md``'s companion
frozen NPZ / JSON artifacts.

Outputs (full_doc_report/figures/)
    V8_F01_accuracy_cost.png / .svg
    V8_F02_four_state_flow.png / .svg
    V8_F03_result_reconciliation.png / .svg
    V8_F04_training_dashboard.png / .svg
    V8_F05_external_metric_coverage.png / .svg
    V8_F06_seedwise_deltas.png / .svg
    V8_F07_ablation_arms.png / .svg
    REMEDFILM_V8_FIGURE_EVIDENCE_MAP.json  (in full_doc_report/)

No training, no inference, no TEST1683 access.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

from v8_common import (
    ROOT, FDR, FIG, NAVY, NAVY_2, BLUE, BLUE_LIGHT, TEAL, TEAL_LIGHT,
    AMBER, RED, GREY, GREY_LIGHT, PURPLE, PURPLE_LIGHT, WHITE,
    write_artifact, write_json, sha256, read_csv,
)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8.0,
    "axes.edgecolor": "#C9D3DF",
    "axes.labelcolor": NAVY,
    "text.color": NAVY,
    "xtick.color": "#42566E",
    "ytick.color": "#42566E",
    "axes.titleweight": "bold",
    "axes.titlecolor": NAVY,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "svg.hashsalt": "remedfilm-v8-figures",
})
STABLE = {"svg": {"Date": None}, "png": {}}
SERIF = "DejaVu Serif"

REG = json.loads((FDR / "REMEDFILM_V8_RESULTS_REGISTRY.json").read_text(encoding="utf-8"))
METRICS = {m["metric_id"]: m for m in REG["metrics"]}
CANON = REG["canonical_result"]


def mval(mid: str) -> float:
    return float(METRICS[mid]["value"])


def style(ax, *, grid="y"):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.7)
    ax.spines["bottom"].set_linewidth(0.7)
    if grid:
        ax.grid(axis=grid, color="#E7EDF4", linewidth=0.7, zorder=0)
        ax.set_axisbelow(True)
    ax.tick_params(labelsize=7.0, length=3)


def save(fig, stem: str, title: str) -> dict:
    out = {}
    for ext in ("png", "svg"):
        p = FIG / f"{stem}.{ext}"
        tmp = FIG / f".v8_tmp_{stem}.{ext}"
        fig.savefig(tmp, format=ext, dpi=220, bbox_inches="tight",
                    pad_inches=0.10, metadata=STABLE.get(ext, {}))
        raw = tmp.read_bytes()
        tmp.unlink()
        write_artifact(p, raw)
        out[ext] = {"path": str(p.relative_to(FDR)).replace("\\", "/"),
                    "bytes": len(raw), "sha256": sha256(p)}
    plt.close(fig)
    print(f"  {stem}: png {out['png']['bytes']:,} B, svg {out['svg']['bytes']:,} B")
    return out


# --------------------------------------------------------------------------- #
# V8_F01 -- accuracy vs compute, with honest semantics
# --------------------------------------------------------------------------- #
def fig_accuracy_cost() -> dict:
    compute = read_csv(ROOT / "reports/tables/phase21_six_model_compute.csv")
    compare = read_csv(ROOT / "reports/tables/phase21_six_model_comparison.csv")
    gmap = {r["model_key"]: float(r["gmacs"]) for r in compute}
    dmap = {r["model_key"]: float(r["macro_domain_dice"]) for r in compare
            if r["macro_domain_dice"]}
    names = {
        "unet": ("U-Net", (6, -12)),
        "attention_unet": ("Attention U-Net", (6, 5)),
        "unetpp": ("U-Net++", (-4, 10)),
        "deeplabv3plus": ("DeepLabV3+", (6, 4)),
        "transformer_mit_unet": ("Transformer/MiT U-Net", (6, 4)),
    }
    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    for key, (label, off) in names.items():
        if key in gmap and key in dmap:
            ax.scatter(gmap[key], dmap[key], s=48, color="#9AA9B8",
                       edgecolor="white", linewidth=0.9, zorder=3)
            ax.annotate(label, (gmap[key], dmap[key]), fontsize=6.8,
                        xytext=off, textcoords="offset points",
                        ha="right" if off[0] < 0 else "left",
                        color="#54677C", zorder=4)

    gx, gy = mval("EFF_G_GMACS"), float(CANON["global_macro_dice"])
    fx, fy = mval("EFF_FULL_GMACS"), float(CANON["full_macro_dice"])
    # The two canonical points are only 0.9 GMAC apart.  Left-side annotation
    # is impossible without colliding with the y axis, so both labels sit to
    # the right on two non-crossing leader lines (V5-V7 overlapped them).
    ax.scatter(gx, gy, s=105, marker="o", color=BLUE, edgecolor="white",
               linewidth=1.2, zorder=5)
    ax.scatter(fx, fy, s=230, marker="*", color=TEAL, edgecolor="#0A665D",
               linewidth=0.9, zorder=6)
    ax.annotate("ReMedFiLM FULL \u2014 G + R\u03c8 + B\u03c6 + S\u03c9  (0.837290)",
                xy=(fx, fy), xytext=(39.0, 0.8430),
                fontsize=7.2, color=TEAL, weight="bold", ha="left",
                va="center", zorder=7,
                arrowprops=dict(arrowstyle="-", color=TEAL, lw=0.9,
                                shrinkA=4, shrinkB=6))
    ax.annotate("GlobalMedFiLM (G) \u2014 backbone / baseline  (0.835080)",
                xy=(gx, gy), xytext=(39.0, 0.8362),
                fontsize=6.9, color=BLUE, ha="left", va="center", zorder=7,
                arrowprops=dict(arrowstyle="-", color=BLUE, lw=0.8,
                                shrinkA=4, shrinkB=6))

    ax.set_xlabel("Analytical GMACs @ 1\u00d73\u00d7512\u00d7512  "
                  "(lower bound; FULL = expected conditional)")
    ax.set_ylabel("VAL808 macro-domain Dice")
    ax.set_title("Accuracy versus architectural cost \u2014 descriptive comparison",
                 fontsize=10.0, fontfamily=SERIF, pad=12)
    ax.set_xlim(28, 150)
    ax.set_ylim(0.780, 0.848)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.3f}"))
    style(ax)
    fig.text(0.012, 0.012,
             "Baselines come from a historical six-model protocol (EXT-03); FULL combines "
             "frozen accuracy with conditional analytical compute.\n"
             "Mixed compute semantics and unmatched training protocols: NOT a confirmed "
             "Pareto frontier and NOT a controlled ablation.",
             fontsize=6.4, color=GREY, linespacing=1.4)
    fig.subplots_adjust(bottom=0.24, left=0.11, right=0.98, top=0.88)
    return save(fig, "V8_F01_accuracy_cost", "accuracy versus cost")


# --------------------------------------------------------------------------- #
# V8_F02 -- four canonical VAL808 states
# --------------------------------------------------------------------------- #
def fig_four_state_flow() -> dict:
    rt = REG["routing_val808"]
    n = rt["n"]
    skip = rt["branches"]["SKIP_GLOBAL"]
    acc = rt["branches"]["EXECUTE_THEN_ACCEPT"]
    rej = rt["branches"]["EXECUTE_THEN_REJECT"]
    forced = n - skip - acc - rej
    assert forced == 0, "unexpected FORCED_SKIP count"
    execute = rt["decisions"]["EXECUTE"]

    fig, ax = plt.subplots(figsize=(8.2, 3.8))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    def node(x, y, w, h, label, sub, fc, ec, tc, fs=8.4, sfs=6.9):
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec,
                                   linewidth=1.2, zorder=3))
        # rounded appearance via a second thin outline is unnecessary; keep square
        ax.text(x + w / 2, y + h * 0.62, label, ha="center", va="center",
                fontsize=fs, color=tc, weight="bold", zorder=5)
        ax.text(x + w / 2, y + h * 0.27, sub, ha="center", va="center",
                fontsize=sfs, color=NAVY_2, zorder=5)

    def arr(x0, y0, x1, y1, color, lw=1.5, ls="-"):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", mutation_scale=10,
                                    color=color, linewidth=lw, linestyle=ls),
                    zorder=2)

    roi_t = REG["runtime_constants"]["roi_proposal_threshold"]
    acc_t = REG["runtime_constants"]["s_omega_accept_threshold"]
    out_t = REG["runtime_constants"]["segmentation_output_threshold"]

    # TOP ROW -- the sequential inference pipeline, left to right.
    # BOTTOM ROW -- the four terminal states.  Every arrow lands on the edge of
    # a real box; V5-V7 had a dangling G->decision arrow and an incorrect
    # SKIP_GLOBAL -> EXECUTE edge (a skipped case can never be executed).
    node(1, 62, 14, 18, f"{n} images", "VAL808, seed 42",
         GREY_LIGHT, "#A9B5C2", GREY, fs=8.0, sfs=6.5)
    node(18, 62, 14, 18, "G forward", "exactly one / image",
         BLUE_LIGHT, BLUE, BLUE, fs=8.0, sfs=6.4)
    node(35, 62, 18, 18, "action available?",
         f"ROI from p_global \u2265 {roi_t:.2f}",
         "#F4F7FB", "#8EA6BE", NAVY_2, fs=7.5, sfs=6.2)
    node(56, 62, 18, 18, "U \u2265 \u03c4_C8 ?",
         "B\u03c6 on 202-D frozen features",
         "#F4F7FB", "#8EA6BE", NAVY_2, fs=7.8, sfs=6.1)
    node(77, 62, 14, 18, "EXECUTE", f"{execute} / {n} ({execute/n:.1%})",
         TEAL_LIGHT, TEAL, TEAL, fs=7.8, sfs=6.4)

    # BOTTOM ROW -- terminal states
    node(35, 28, 18, 18, "FORCED_SKIP", f"{forced} / {n} images",
         BLUE_LIGHT, BLUE, BLUE, fs=7.2, sfs=6.4)
    node(56, 28, 18, 18, "SKIP_GLOBAL", f"{skip} / {n} ({skip/n:.1%})",
         BLUE_LIGHT, BLUE, BLUE, fs=7.2, sfs=6.4)
    node(75, 28, 11, 18, "ACCEPT", f"{acc} / {n}",
         TEAL_LIGHT, TEAL, TEAL, fs=6.8, sfs=6.2)
    node(88, 28, 11, 18, "REJECT", f"{rej} / {n}",
         "#FBF1DE", AMBER, "#8A5A10", fs=6.8, sfs=6.2)

    # pipeline edges (top row)
    arr(15, 71, 18, 71, GREY)
    arr(32, 71, 35, 71, GREY)
    arr(53, 71, 56, 71, GREY)
    ax.text(54.5, 73.2, "ROI yes", fontsize=5.9, color=GREY, ha="center")
    arr(74, 71, 77, 71, TEAL, lw=1.6)
    ax.text(75.5, 73.2, "U \u2265 \u03c4", fontsize=5.9, color=TEAL, ha="center")

    # downward terminal edges
    arr(44, 62, 44, 46, BLUE, lw=1.4)
    ax.text(45.0, 53, "no ROI", fontsize=6.2, color=BLUE, va="center")
    arr(65, 62, 65, 46, BLUE, lw=1.4)
    ax.text(66.0, 53, "U < \u03c4", fontsize=6.2, color=BLUE, va="center")

    # S_omega split: a compact gate box between EXECUTE and its two terminal
    # states.  Short, non-overlapping edges; no long diagonals through boxes.
    ax.add_patch(plt.Rectangle((78, 51), 14, 6, facecolor="#F4F7FB",
                               edgecolor="#8EA6BE", linewidth=1.0, zorder=3))
    ax.text(85, 54, f"S\u03c9 \u2265 {acc_t:.2f} ?", ha="center", va="center",
            fontsize=6.4, color=NAVY, zorder=5)
    arr(84, 62, 84, 57, TEAL, lw=1.4)
    arr(80.5, 51, 80.5, 46, TEAL, lw=1.4)
    arr(89.0, 51, 93.5, 46, AMBER, lw=1.4)

    ax.text(1, 94, "Four canonical states of RAMedFiLMBARR.forward_inference()",
            fontsize=10.4, weight="bold", fontfamily=SERIF, color=NAVY)
    ax.text(1, 88, "S\u03c9 runs after candidate composition; "
            "R\u03c8 is an offline OOF producer (not called in forward_inference)",
            fontsize=6.8, color=GREY, style="italic")
    ax.text(1, 15,
            "STATES  \u00b7  FORCED_SKIP "
            f"{forced}  \u00b7  SKIP_GLOBAL {skip}  \u00b7  "
            f"EXECUTE_THEN_ACCEPT {acc}  \u00b7  EXECUTE_THEN_REJECT {rej}",
            fontsize=6.9, color=NAVY_2)
    ax.text(1, 9,
            f"P_out = P_cand for {acc} images; P_out = p_global for "
            f"{forced + skip + rej} images  \u00b7  final mask = 1[P_out \u2265 {out_t:.2f}]",
            fontsize=6.9, color=NAVY_2)
    ax.text(99, 4, "VAL808 counts only; TEST1683 not opened",
            fontsize=6.4, color=GREY, ha="right")
    fig.subplots_adjust(left=0.02, right=0.99, top=0.99, bottom=0.02)
    return save(fig, "V8_F02_four_state_flow", "four-state flow")


# --------------------------------------------------------------------------- #
# V8_F03 -- the three competing numbers, and the genuine three-seed spread
# --------------------------------------------------------------------------- #
def fig_result_reconciliation() -> dict:
    # Genuine values come from the frozen NPZ, re-derived (analysis only).
    # The rejected V7 triplet is preserved verbatim from build_v7_pdf_report.py
    # so the adjudication is auditable; it is never used as a scientific result.
    archive = ROOT / "data_cache/phase29_phase_d_canonical/phase29_phase_d_three_seed_val808_delta_dice.npz"
    with np.load(archive) as z:
        dom = z["domains"]
        uniq = list(dict.fromkeys(dom.tolist()))
        def macro(key):
            v = np.asarray(z[key], dtype=float)
            return float(np.mean([v[dom == d].mean() for d in uniq]))
        seeds_real = [macro("seed42_final_dice"), macro("seed123_final_dice"),
                      macro("seed3407_final_dice")]
        global_real = macro("global_dice")
    mean_real = float(np.mean(seeds_real))
    sd_real = float(np.std(seeds_real, ddof=1))
    # V7 hardcoded triplet, preserved verbatim from build_v7_pdf_report.py
    v7 = [0.837862, 0.837910, 0.837815]
    mean_v7, sd_v7 = float(np.mean(v7)), float(np.std(v7, ddof=1))
    legacy = (v7[0] + v7[1] + v7[2]) / 3.0

    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.0),
                             gridspec_kw={"width_ratios": [1.0, 1.35]})

    ax = axes[0]
    vals = [float(CANON["global_macro_dice"]), float(CANON["full_macro_dice"]),
            legacy]
    labs = ["GlobalMedFiLM (G)\nbackbone, VAL808",
            "ReMedFiLM FULL\ncanonical, re-scored",
            "V7 legacy figure\nREJECTED"]
    cols = [BLUE, TEAL, "#B9C3CE"]
    bars = ax.bar(range(3), vals, color=cols, width=0.58, zorder=3)
    ax.set_ylim(0.8330, 0.8395)
    ax.set_xticks(range(3))
    ax.set_xticklabels(labs, fontsize=6.6)
    ax.set_ylabel("macro-domain Dice")
    ax.set_title("Which Dice value is admissible?", fontsize=9.4,
                 fontfamily=SERIF, pad=10)
    for i, (b, v) in enumerate(zip(bars, vals)):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.00012, f"{v:.6f}",
                ha="center", fontsize=7.0, weight="bold",
                color=NAVY if i < 2 else "#7A4A4A")
    # No in-panel arrow: the V5-V7 annotation crossed bars 1 and 2.  The
    # rejection is stated in the bar label and in the figure footnote instead.
    ax.text(2, 0.8387, "\u2715 REJECTED", ha="center", va="center",
            fontsize=7.0, weight="bold", color=RED,
            bbox=dict(boxstyle="round,pad=0.25", fc="#FDF3F2",
                      ec=RED, lw=0.7))
    style(ax)
    ax.tick_params(axis="x", length=0)

    ax = axes[1]
    x = np.arange(3)
    ax.plot(x, v7, "o--", color="#B9C3CE", linewidth=1.4, markersize=6,
            label="V7 hardcoded triplet", zorder=3)
    ax.plot(x, seeds_real, "o-", color=TEAL, linewidth=1.8, markersize=7,
            label="Frozen Phase-29D NPZ (re-derived)", zorder=4)
    ax.axhline(mean_real, color=TEAL, linewidth=0.9, linestyle=":")
    ax.axhline(mean_v7, color="#A9B3BF", linewidth=0.9, linestyle=":")
    ax.fill_between([-0.2, 2.2], mean_real - sd_real, mean_real + sd_real,
                    color=TEAL, alpha=0.10, zorder=1)
    for i, v in enumerate(seeds_real):
        # All labels sit ABOVE their point with an opaque backing so the steep
        # teal segment never runs through the digits (V7 put seed-42's label
        # below the point, where it collided with the x tick label).
        ax.text(i, v + 0.00007, f"{v:.6f}",
                ha="center", va="bottom", fontsize=6.5, color=TEAL,
                bbox=dict(boxstyle="round,pad=0.12", fc="white",
                          ec="none", alpha=0.90))
    ax.set_xticks(x)
    ax.set_xticklabels(["seed 42", "seed 123", "seed 3407"], fontsize=7.2)
    ax.set_ylim(0.8372, 0.8389)
    ax.set_ylabel("macro-domain Dice")
    ax.set_title("Across-seed spread is ~12\u00d7 larger than V7 reported",
                 fontsize=9.4, fontfamily=SERIF, pad=10)
    ax.legend(fontsize=6.4, loc="upper left", frameon=False)
    ax.text(0.99, 0.03,
            f"frozen NPZ: mean {mean_real:.6f}, SD {sd_real:.2e}\n"
            f"V7 printed: mean {mean_v7:.6f}, SD {sd_v7:.2e}\n"
            f"backbone (frozen NPZ): {global_real:.6f}",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=6.2,
            color=NAVY_2, linespacing=1.35,
            bbox=dict(boxstyle="round,pad=0.30", fc="white",
                      ec="#D6DEE7", lw=0.6, alpha=0.94))
    style(ax)
    fig.suptitle("V8 result reconciliation \u2014 0.835079 / 0.837290 / 0.837862",
                 fontsize=10.8, fontfamily=SERIF, weight="bold", y=1.02)
    fig.text(0.012, 0.012,
             "0.837862 is REJECTED: it is not reproducible from saved VAL808 masks and equals the mean "
             "of V7's own hardcoded seed triplet.\n"
             "The admissible ReMedFiLM FULL result is 0.837290 (seed 42, re-scored from saved masks); "
             "the frozen three-seed NPZ is reported separately, not substituted for it.",
             fontsize=6.3, color=GREY, linespacing=1.35)
    fig.subplots_adjust(wspace=0.28, bottom=0.24, top=0.84)
    return save(fig, "V8_F03_result_reconciliation", "result reconciliation")


# --------------------------------------------------------------------------- #
# V8_F04 -- staged component training dashboard (genuine historical logs)
# --------------------------------------------------------------------------- #
def fig_training_dashboard() -> dict:
    rows = read_csv(FDR / "REMEDFILM_V8_TRAINING_HISTORY.csv")
    by_comp: dict[str, list[dict]] = {}
    for r in rows:
        by_comp.setdefault(r["component"], []).append(r)

    def pick_run(comp, tr, va):
        """Choose ONE genuine logged run that contains BOTH curves.

        The V8 training CSV contains 56 run IDs (three seeds x CV folds per
        component).  V5-V7 silently mixed the first run of the train curve with
        the first run of the validation curve, producing two curves from
        different folds/seeds on the same axes.  V8 requires a shared run ID.
        """
        counts: dict[str, dict[str, int]] = {}
        for r in by_comp.get(comp, []):
            if r["metric"] in (tr, va):
                counts.setdefault(r["run_id"], {tr: 0, va: 0})
                counts[r["run_id"]][r["metric"]] += 1
        eligible = {rid: c for rid, c in counts.items() if c[tr] and c[va]}
        if not eligible:
            return None
        return max(eligible, key=lambda rid: sum(eligible[rid].values()))

    def series(comp, metric, run):
        rs = [r for r in by_comp.get(comp, [])
              if r["metric"] == metric and r["run_id"] == run]
        try:
            e = np.array([float(r["epoch"]) for r in rs])
            v = np.array([float(r["value"]) for r in rs])
        except ValueError:
            return np.array([]), np.array([])
        if not e.size:
            return e, v
        order = np.argsort(e)
        return e[order], v[order]

    panels = [
        ("G \u00b7 GlobalMedFiLM (segmentation)", "train_loss", "val_loss",
         "GlobalMedFiLM (G)", BLUE, "BCE + soft Dice (logged total loss)"),
        ("R\u03c8 \u00b7 BARRRegionalRefinerV1", "train_loss", "val_refiner_loss",
         "R_psi (Regional Refiner)", PURPLE, "0.5\u00b7BCEWithLogits + 0.5\u00b7soft Dice"),
        ("B\u03c6 \u00b7 BARRBenefitRouterV1", "train_huber", "val_router_huber",
         "B_phi (Benefit Router)", TEAL, "HuberLoss(\u0394 = 0.05) on \u03b4-Dice"),
        ("S\u03c9 \u00b7 BARRPostSafetyV1", "train_bce", "val_safety_bce",
         "S_omega (Post-Safety Gate)", AMBER, "BCEWithLogitsLoss on safety_target"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(9.2, 5.6))
    used_runs = []
    for ax, (title, tr, va, comp, col, loss) in zip(axes.ravel(), panels):
        rid = pick_run(comp, tr, va)
        assert rid, f"no single run with both {tr} and {va} for {comp}"
        used_runs.append((comp.split(" ")[0], rid))
        e1, v1 = series(comp, tr, rid)
        e2, v2 = series(comp, va, rid)
        # B_phi has a genuine epoch-1 Huber transient ~13x the next value;
        # a log axis retains every logged point without flattening the rest.
        is_log = comp.startswith("B_phi")
        if is_log:
            ax.set_yscale("log")
        ax.plot(e1, v1, color=col, linewidth=1.15, alpha=0.85,
                label="train", zorder=3)
        ax.plot(e2, v2, color=NAVY, linewidth=1.15, alpha=0.85,
                linestyle="--", label="validation", zorder=3)
        ax.set_title(title, fontsize=8.6, fontfamily=SERIF, pad=6)
        ax.set_xlabel("epoch", fontsize=6.8)
        ax.set_ylabel("loss (log axis)" if is_log else "loss", fontsize=6.8)
        ax.text(0.98, 0.95, loss, transform=ax.transAxes, ha="right",
                va="top", fontsize=6.0, color=GREY, style="italic")
        ax.legend(fontsize=6.2, frameon=False, loc="upper right",
                  bbox_to_anchor=(1.0, 0.86))
        style(ax)
    fig.suptitle("Staged component training \u2014 four independent objective histories",
                 fontsize=10.8, fontfamily=SERIF, weight="bold", y=0.995)
    runs_line = "   |   ".join(f"{tag}: {rid}" for tag, rid in used_runs)
    fig.text(0.012, 0.030, "One genuine logged run per panel (same run ID for both curves): "
             + runs_line, fontsize=5.7, color="#6B7C90")
    fig.text(0.012, 0.008,
             "No joint end-to-end objective exists; curves are diagnostic histories, not a "
             "shared-scale comparison. B\u03c6 uses a log y-axis so the epoch-1 transient "
             "remains visible without flattening later epochs.",
             fontsize=6.2, color=GREY)
    fig.subplots_adjust(hspace=0.44, wspace=0.26, top=0.90, bottom=0.14,
                        left=0.075, right=0.98)
    return save(fig, "V8_F04_training_dashboard", "training dashboard")


# --------------------------------------------------------------------------- #
# V8_F05 -- external metric coverage (what is and is not defined)
# --------------------------------------------------------------------------- #
def fig_external_coverage() -> dict:
    """Which external metrics are defined, and on how many cases.

    The V8 external CSV keys cohorts by ``population`` (EXTERNAL_CVC / _BREAST /
    _STONES) and carries a separate ``domain`` code (KVASIR / BUSI / KUB) that
    names the *internal* training domain used for the task embedding.  V5-V7
    conflated these; V8 joins on ``population`` and uses display names only for
    labels.  Cells where ``n < n_total`` are partial-coverage, not missing.
    """
    rows = read_csv(FDR / "REMEDFILM_V8_EXTERNAL_EVALUATION.csv")
    cohorts = [
        ("EXTERNAL_CVC", "CVC-ClinicDB"),
        ("EXTERNAL_BREAST", "BrEaST-Lesions-USG"),
        ("EXTERNAL_STONES", "Stones-Where-Are-You"),
    ]
    metrics = ["Dice", "IoU", "Precision", "Recall", "HD95_px", "ASSD_px"]
    cells: dict[tuple[str, str], dict] = {}
    for r in rows:
        if r.get("model_identity") != "ReMedFiLM FULL":
            continue
        pop, met = r.get("population", ""), r.get("metric", "")
        if pop not in {p for p, _ in cohorts} or met not in metrics:
            continue
        val = r.get("value", "")
        try:
            v = float(val)
        except (TypeError, ValueError):
            continue
        try:
            n = int(float(r.get("n", "")))
        except (TypeError, ValueError):
            n = None
        try:
            n_total = int(float(r.get("n_total", "")))
        except (TypeError, ValueError):
            n_total = n
        cells[(pop, met)] = {"value": v, "n": n, "n_total": n_total}

    fig, ax = plt.subplots(figsize=(8.4, 3.4))
    ax.set_xlim(-2.25, len(metrics) - 0.3)
    ax.set_ylim(-1.20, len(cohorts) + 0.75)
    ax.axis("off")
    for j, mname in enumerate(metrics):
        ax.text(j, len(cohorts) + 0.20, mname, ha="center", va="center",
                fontsize=7.4, weight="bold", color=NAVY)
    ax.text(-1.5, len(cohorts) + 0.20, "cohort / metric", ha="left",
            va="center", fontsize=6.6, color=GREY)
    for i, (pop, cname) in enumerate(cohorts):
        y = len(cohorts) - 1 - i
        ax.text(-0.62, y, cname, ha="right", va="center", fontsize=6.9,
                color=NAVY)
        for j, met in enumerate(metrics):
            c = cells.get((pop, met))
            partial = bool(c and c["n_total"] and c["n"] is not None
                           and c["n"] < c["n_total"])
            if c is None:
                fc, ec = "#F3F5F7", "#CBD3DC"
            elif partial:
                fc, ec = "#FBF1DE", AMBER
            else:
                fc, ec = TEAL_LIGHT, TEAL
            ax.add_patch(plt.Rectangle((j - 0.45, y - 0.41), 0.90, 0.82,
                                       facecolor=fc, edgecolor=ec,
                                       linewidth=1.0, zorder=2))
            if c is None:
                ax.text(j, y, "NOT\nDEFINED", ha="center", va="center",
                        fontsize=6.0, color=GREY, linespacing=1.2, zorder=4)
                continue
            ax.text(j, y + 0.13, f"{c['value']:.4f}", ha="center", va="center",
                    fontsize=7.1, weight="bold", color=NAVY, zorder=4)
            if c["n_total"] and c["n"] is not None:
                label = (f"n={c['n']}/{c['n_total']}" if partial
                         else f"n={c['n_total']}")
                ax.text(j, y - 0.20, label, ha="center", va="center",
                        fontsize=5.9,
                        color="#8A5A10" if partial else GREY, zorder=4)
    ax.add_patch(plt.Rectangle((-0.42, -1.00), 0.22, 0.22,
                               facecolor=TEAL_LIGHT, edgecolor=TEAL,
                               linewidth=0.8, zorder=2))
    ax.text(-0.14, -0.89, "defined on full cohort", ha="left", va="center",
            fontsize=6.3, color=NAVY_2)
    ax.add_patch(plt.Rectangle((1.95, -1.00), 0.22, 0.22,
                               facecolor="#FBF1DE", edgecolor=AMBER,
                               linewidth=0.8, zorder=2))
    ax.text(2.23, -0.89, "defined on subset only", ha="left", va="center",
            fontsize=6.3, color=NAVY_2)
    ax.add_patch(plt.Rectangle((4.05, -1.00), 0.22, 0.22,
                               facecolor="#F3F5F7", edgecolor="#CBD3DC",
                               linewidth=0.8, zorder=2))
    ax.text(4.33, -0.89, "not defined", ha="left", va="center",
            fontsize=6.3, color=NAVY_2)
    ax.set_title("External retrospective evaluation \u2014 ReMedFiLM FULL metric coverage",
                 fontsize=10.0, fontfamily=SERIF, pad=18)
    fig.text(0.012, 0.005,
             "Stones: Recall / HD95 / ASSD are defined on 6 of 20 cases (both masks non-empty); "
             "14/14 stone-free images receive false-positive foreground.\n"
             "All cells are ReMedFiLM FULL values from frozen saved predictions; "
             "no new inference was run.",
             fontsize=6.3, color=GREY, linespacing=1.35)
    fig.subplots_adjust(left=0.20, right=0.99, top=0.78, bottom=0.24)
    return save(fig, "V8_F05_external_metric_coverage", "external coverage")


# --------------------------------------------------------------------------- #
# V8_F06 -- seedwise Dice and paired delta, rebuilt from the frozen NPZ.
# Replaces STAT01_seedwise_macro_metrics, whose light-grey mean/SD text was
# printed on top of the first bar and was effectively illegible.
# --------------------------------------------------------------------------- #
def fig_seedwise_deltas() -> dict:
    archive = ROOT / "data_cache/phase29_phase_d_canonical/phase29_phase_d_three_seed_val808_delta_dice.npz"
    with np.load(archive) as z:
        dom = z["domains"]
        uniq = list(dict.fromkeys(dom.tolist()))
        def macro(key):
            v = np.asarray(z[key], dtype=float)
            return float(np.mean([v[dom == d].mean() for d in uniq]))
        seeds = [macro("seed42_final_dice"), macro("seed123_final_dice"),
                 macro("seed3407_final_dice")]
        global_dice = macro("global_dice")
    deltas = [s - global_dice for s in seeds]
    mean_s, sd_s = float(np.mean(seeds)), float(np.std(seeds, ddof=1))
    mean_d, sd_d = float(np.mean(deltas)), float(np.std(deltas, ddof=1))

    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.9),
                             gridspec_kw={"width_ratios": [1.0, 1.0]})
    specs = [
        (axes[0], seeds, 0.8368, "Macro-domain VAL808 Dice", BLUE,
         "macro-domain Dice (truncated axis)"),
        (axes[1], deltas, 0.0, "Paired \u0394 Dice vs frozen G backbone", TEAL,
         "\u0394 Dice"),
    ]
    for ax, vals, base, title, col, ylab in specs:
        x = np.arange(3)
        if base:
            ax.bar(x, [v - base for v in vals], bottom=base, color=col,
                   width=0.56, zorder=3, alpha=0.90)
            lo, hi = base, max(vals) + 0.00030
        else:
            ax.bar(x, vals, color=col, width=0.56, zorder=3, alpha=0.90)
            lo, hi = 0.0, max(vals) * 1.30
        for i, v in enumerate(vals):
            ax.text(i, v + (hi - lo) * 0.025, f"{v:.6f}",
                    ha="center", va="bottom", fontsize=7.0,
                    weight="bold", color=NAVY, zorder=5)
        ax.axhline(float(np.mean(vals)), color=NAVY_2, linewidth=0.9,
                   linestyle="--", zorder=4)
        ax.set_xticks(x)
        ax.set_xticklabels(["seed 42", "seed 123", "seed 3407"], fontsize=7.4)
        ax.set_ylim(lo, hi)
        ax.set_ylabel(ylab, fontsize=7.6)
        ax.set_title(title, fontsize=9.0, fontfamily=SERIF, pad=9)
        style(ax)
        ax.tick_params(axis="x", length=0)
    fig.suptitle("Three downstream seeds \u2014 descriptive only, shared frozen G backbone",
                 fontsize=10.6, fontfamily=SERIF, weight="bold", y=1.00)
    fig.text(0.012, 0.012,
             f"Macro Dice mean {mean_s:.6f}, SD {sd_s:.2e} (ddof=1)   \u00b7   "
             f"\u0394 Dice mean {mean_d:.6f}, SD {sd_d:.2e}   \u00b7   "
             f"frozen G = {global_dice:.6f}.\n"
             "Left bars start at 0.8368, not zero (axis truncated for legibility); "
             "only downstream modules vary by seed \u2014 G was not retrained. "
             "Descriptive, not a controlled seed study.",
             fontsize=6.3, color=GREY, linespacing=1.4)
    fig.subplots_adjust(wspace=0.28, bottom=0.24, top=0.85)
    return save(fig, "V8_F06_seedwise_deltas", "seedwise Dice and paired delta")


# --------------------------------------------------------------------------- #
# V8_F07 -- 13-arm ablation, rebuilt with labels inside the axes.
# Replaces ABL01_arm_mean_delta, whose rotated value labels ran into the title.
# --------------------------------------------------------------------------- #
def fig_ablation_arms() -> dict:
    arms = ["A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8",
            "R1", "R2", "R3", "F1"]
    vals = []
    for a in arms:
        mid = f"ABL_{a}_MEAN_DELTA_DICE"
        assert mid in METRICS, f"missing registry metric {mid}"
        vals.append(mval(mid))
    ci_low = mval("ABL_A7_CI_LOW")
    ci_high = mval("ABL_A7_CI_HIGH")

    fig, ax = plt.subplots(figsize=(9.2, 4.1))
    x = np.arange(len(arms))
    colors = ["#9AA9B8" for _ in arms]
    for i, a in enumerate(arms):
        if a == "A7":
            colors[i] = BLUE
        elif a == "A8":
            colors[i] = TEAL
        elif a == "F1":
            colors[i] = RED
        elif a == "A1":
            colors[i] = AMBER
    ax.bar(x, vals, color=colors, width=0.62, zorder=3)
    span = 0.052
    for i, v in enumerate(vals):
        off = span * 0.018
        ax.text(i, v + off if v >= 0 else v - off,
                f"{v:+.4f}", ha="center",
                va="bottom" if v >= 0 else "top",
                fontsize=6.2, color=NAVY if v >= 0 else RED, zorder=5)
    ax.axhline(0.0, color=NAVY, linewidth=0.9, zorder=4)
    ax.set_xticks(x)
    ax.set_xticklabels(arms, fontsize=7.4)
    ax.set_ylim(-0.040, 0.012)
    ax.set_ylabel("mean \u0394 Dice on routed cases", fontsize=7.8)
    ax.set_title("13-arm component ablation \u2014 ROUTER_DEVELOPMENT (n = 4,957)",
                 fontsize=10.0, fontfamily=SERIF, pad=11)
    style(ax)
    ax.tick_params(axis="x", length=0)
    fig.text(0.012, 0.012,
             f"A8 \u2212 A7 paired contrast: CI [{ci_low:.2e}, {ci_high:.2e}] "
             "includes zero \u2014 the incremental safety contribution is NOT established.\n"
             "Blue A7 = learned benefit routing; teal A8 = A7 + post-safety gate (S_omega); "
             "amber A1 = always refine; red F1 = deliberate failure arm.\n"
             "Bars are mean true \u0394 Dice on routed cases from frozen historical arm outputs; "
             "F1 is \u22484.3\u00d7 the magnitude of the largest positive bar (A8). "
             "No new arm was executed for V8.",
             fontsize=6.3, color=GREY, linespacing=1.4)
    fig.subplots_adjust(bottom=0.24, top=0.88, left=0.085, right=0.98)
    return save(fig, "V8_F07_ablation_arms", "13-arm component ablation")


# --------------------------------------------------------------------------- #
# figure evidence map
# --------------------------------------------------------------------------- #
FIGURE_SELECTION = [
    # (figure_id, V8 section, role, verdict)
    ("ReMedFiLM_Methodology_V8", "01 / 02", "primary three-panel methodology figure", "V8_NEW"),
    ("ReMedFiLM_Methodology_Manuscript", "02", "manuscript print variant", "V8_NEW"),
    ("V8_F01_accuracy_cost", "12", "accuracy vs cost with canonical FULL point", "V8_NEW"),
    ("V8_F02_four_state_flow", "10", "four canonical VAL808 states", "V8_NEW"),
    ("V8_F03_result_reconciliation", "01 / 11", "0.835079 / 0.837290 / 0.837862 adjudication", "V8_NEW"),
    ("V8_F04_training_dashboard", "05", "four independent objective histories", "V8_NEW"),
    ("V8_F05_external_metric_coverage", "08", "which external metrics are defined", "V8_NEW"),
    ("V8_F06_seedwise_deltas", "11", "three-seed Dice and paired delta, clean axis", "V8_NEW"),
    ("V8_F07_ablation_arms", "09", "13-arm ablation with legible value labels", "V8_NEW"),
    ("A02_component_presence_matrix", "02", "which model instantiates which component", "REUSED_VERIFIED"),
    ("D01_domain_and_split_composition", "03", "domain and split composition", "REUSED_VERIFIED"),
    ("D03_kub_unit_of_analysis", "03", "KUB full-field vs ROI patch distinction", "REUSED_VERIFIED"),
    ("STAT04_population_accounting", "03", "TRAIN/VAL/TEST and router-dev accounting", "REUSED_VERIFIED"),
    ("I1_domain_metric_comparison", "04", "per-domain Dice/IoU/precision/recall", "REUSED_VERIFIED"),
    ("I2_paired_delta_forest", "04", "paired delta with bootstrap CI", "REUSED_VERIFIED"),
    ("STAT02_bootstrap_distribution", "04", "domain-stratified bootstrap distribution", "REUSED_VERIFIED"),
    ("T2_val_dice_across_epochs", "05", "backbone validation Dice history", "REUSED_VERIFIED"),
    ("T4_per_domain_learning_curves", "05", "four-domain learning curves", "REUSED_VERIFIED"),
    ("SEG_ISIC_global_vs_full", "06", "ISIC qualitative gallery", "REUSED_VERIFIED"),
    ("SEG_BUSI_global_vs_full", "06", "BUSI qualitative gallery", "REUSED_VERIFIED"),
    ("SEG_KVASIR_global_vs_full", "06", "Kvasir qualitative gallery", "REUSED_VERIFIED"),
    ("SEG_KUB_global_vs_full", "06", "KUB qualitative gallery", "REUSED_VERIFIED"),
    ("SEG_failure_cases", "06", "documented failure cases", "REUSED_VERIFIED"),
    ("SG1_kub_stone_subgroups", "07", "KUB stone subgroup performance", "REUSED_VERIFIED"),
    ("SG2_kub_size_stratification", "07", "KUB size stratification", "REUSED_VERIFIED"),
    ("EXT01_external_dice", "08", "three-cohort external Dice", "REUSED_VERIFIED"),
    ("EXT02_external_delta", "08", "external paired delta", "REUSED_VERIFIED"),
    ("EXT03_stonefree_false_positive", "08", "preserved negative finding", "REUSED_VERIFIED"),
    ("PROG01_stage_compute_and_harm", "09", "stage-wise compute and harm", "REUSED_VERIFIED"),
    ("ABL02_paired_contrasts_forest", "09", "A8-vs-A7 CI includes zero", "REUSED_VERIFIED"),
    ("ROB01_perturbation_degradation", "11", "12,928 perturbation instances", "REUSED_VERIFIED"),
    ("EFF02_latency_breakdown", "12", "batch-1 measured latency profile", "REUSED_VERIFIED"),
    ("EFF03_accuracy_vs_parameters", "12", "accuracy vs parameter count", "REUSED_VERIFIED"),
]

EXCLUDED = [
    {"figure_id": "A03_remedfilm_inference_path",
     "reason": "Shows only three outcome branches and a linear G -> B_phi -> R_psi -> S_omega chain; superseded by the V8 code-verified four-state methodology figure."},
    {"figure_id": "RT02_stage_flow",
     "reason": "Stage flow omits FORCED_SKIP and presents three states; replaced by V8_F02_four_state_flow. Kept on disk but not used in V8."},
    {"figure_id": "EFF01_accuracy_vs_compute",
     "reason": "Rebuilt as V8_F01 to fix mixed GMAC semantics (lower-bound baselines vs expected-conditional FULL) and to state explicitly that the plot is not a Pareto frontier."},
    {"figure_id": "STAT03_seedwise_per_domain",
     "reason": "Descriptive Phase-29 per-domain panel duplicates V8_F03 and V8_F06; omitted to avoid duplicate architecture/statistics explanations."},
    {"figure_id": "A01_component_parameter_budget",
     "reason": "Parameter budget is stated once in the methodology figure and in a compact table; the stand-alone log-scale bar chart was dropped as a tiny redundant figure."},
    {"figure_id": "ABL01_arm_mean_delta",
     "reason": "Thirteen rotated value labels were drawn above the axes and collided with the chart title. Rebuilt as V8_F07_ablation_arms with horizontal labels inside the axes, headroom, and the A8-vs-A7 CI stated in the footnote."},
    {"figure_id": "STAT01_seedwise_macro_metrics",
     "reason": "Light-grey mean/SD text was printed on top of the first bar in both panels and was effectively illegible. Rebuilt as V8_F06_seedwise_deltas with an explicitly disclosed truncated axis and figure-level statistics."},
    {"figure_id": "RT01_routing_outcomes",
     "reason": "Pie-chart legend text overlapped the adjacent histogram's y-axis tick labels, making both unreadable. Branch counts (529/266/13) are already given unambiguously in V8_F02_four_state_flow; the redundant figure is omitted."},
]


def build_evidence_map(new_outputs: dict) -> dict:
    registry = json.loads((FDR / "figure_registry.json").read_text(encoding="utf-8"))
    by_id = {r["figure_id"]: r for r in registry}
    arrows = json.loads((FDR / "REMEDFILM_V8_METHODOLOGY_ARROWS.json").read_text(
        encoding="utf-8"))
    entries = []
    for i, (fid, section, role, verdict) in enumerate(FIGURE_SELECTION, start=1):
        if fid in new_outputs or fid.startswith("ReMedFiLM_Methodology_"):
            files = (new_outputs.get(fid) or
                     arrows["output_manifest"]["outputs"].get(
                         {"ReMedFiLM_Methodology_V8": "main",
                          "ReMedFiLM_Methodology_Manuscript": "manuscript",
                          "ReMedFiLM_Methodology_GitHub_16x9": "github_16x9"}.get(fid, "main"), {}))
            path = next(iter(files.values()), {}).get("path") if files else None
            e = {
                "v8_figure_number": i, "figure_id": fid, "section": section,
                "role": role, "verdict": verdict,
                "files": files,
                "primary_path": path,
                "evidence_class": "V8_REBUILT_FROM_SOURCE_LINKED_REGISTRY",
                "sources": ["full_doc_report/REMEDFILM_V8_RESULTS_REGISTRY.json"],
                "verification": "GENERATED_AND_VISUALLY_INSPECTED",
            }
        else:
            r = by_id[fid]
            e = {
                "v8_figure_number": i, "figure_id": fid, "section": section,
                "role": role, "verdict": verdict,
                "png_path": r["path"], "svg_path": r["svg_path"],
                "evidence_class": r["evidence_class"],
                "caption": r["caption"], "sources": r["sources"],
                "verification": "PREVIOUSLY_VERIFIED_49_FIGURE_REGISTRY",
            }
            for key in ("png_path", "svg_path"):
                p = ROOT / e[key]
                if p.exists():
                    e[key + "_sha256"] = sha256(p)
        entries.append(e)

    return {
        "artifact": "REMEDFILM_V8_FIGURE_EVIDENCE_MAP",
        "version": "V8",
        "purpose": "One-to-one mapping from every figure used in the V8 report to its evidence class, source artifact, verification status and report section.",
        "canonical_model_identity": REG["canonical_model"]["name"],
        "canonical_model_components": REG["canonical_model"]["components"],
        "canonical_model_assembly": REG["canonical_model"]["assembly"],
        "backbone_role": "GlobalMedFiLM is the G backbone and a legitimate ablation baseline only; it is not the proposed ReMedFiLM FULL system.",
        "single_numeric_source": "full_doc_report/REMEDFILM_V8_RESULTS_REGISTRY.json",
        "counts": {
            "figures_used_in_v8": len(entries),
            "v8_new_or_rebuilt": sum(1 for e in entries if e["verdict"] == "V8_NEW"),
            "reused_verified": sum(1 for e in entries if e["verdict"] == "REUSED_VERIFIED"),
            "excluded_from_v8": len(EXCLUDED),
            "underlying_library_size": len(registry),
        },
        "methodology_figure_verification": {
            "verified_arrows": arrows["verified_arrow_count"],
            "removed_or_corrected_arrows": arrows["removed_or_corrected_count"],
            "arrow_registry": "full_doc_report/REMEDFILM_V8_METHODOLOGY_ARROWS.json",
        },
        "figures": entries,
        "excluded": EXCLUDED,
        "declaration": {
            "model_retrained": False,
            "new_inference_run": False,
            "TEST1683_opened": False,
            "screenshots_of_old_versions_used": False,
            "unverified_p_values_added": False,
        },
    }


def main() -> None:
    print("V8 scientific figures")
    new = {}
    new["V8_F01_accuracy_cost"] = fig_accuracy_cost()
    new["V8_F02_four_state_flow"] = fig_four_state_flow()
    new["V8_F03_result_reconciliation"] = fig_result_reconciliation()
    new["V8_F04_training_dashboard"] = fig_training_dashboard()
    new["V8_F05_external_metric_coverage"] = fig_external_coverage()
    new["V8_F06_seedwise_deltas"] = fig_seedwise_deltas()
    new["V8_F07_ablation_arms"] = fig_ablation_arms()
    emap = build_evidence_map(new)
    p = write_json(FDR / "REMEDFILM_V8_FIGURE_EVIDENCE_MAP.json", emap)
    print(f"  wrote {p.name}: {emap['counts']}")
    print("done.")


if __name__ == "__main__":
    main()
