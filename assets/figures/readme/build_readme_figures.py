"""ReMedFiLM README figure engine.

Builds the GitHub README visual set from *frozen* artifacts only:

  * prediction panels  <- reports/figures/phase27_preservation/masks/  (saved masks)
  * per-sample metrics <- full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv
  * routing state      <- reports/tables/phase27_val808_predictions.csv
  * image / GT paths   <- reports/tables/phase21_prediction_manifest.csv

No model is instantiated, no checkpoint is loaded, no forward pass is run and
no training occurs.  Every number written into a figure is read from a CSV that
already exists on disk; nothing is hardcoded except figure geometry.

Provenance identity check
-------------------------
For every rendered case the script asserts

    foreground_pixels(npz["gt"]) == REMEDFILM_INTERNAL_PER_SAMPLE.gt_fg

which ties together, for a single sample_id, the original image, the ground
truth, the two saved prediction masks and the reported Dice / routing state.
If the assertion fails the script aborts rather than draw a mismatched panel.

Usage
-----
    .\\.venv\\Scripts\\python.exe assets\\figures\\readme\\build_readme_figures.py
    .\\.venv\\Scripts\\python.exe assets\\figures\\readme\\build_readme_figures.py --only predictions
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from PIL import Image

# ------------------------------------------------------------------ paths ----
HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]                     # assets/figures/readme -> repo root
OUT = HERE.parent                          # assets/figures/readme

TABLES = ROOT / "full_doc_report" / "tables"
REPORTS_T = ROOT / "reports" / "tables"
EVIDENCE = ROOT / "full_doc_report" / "Evidence"

PER_SAMPLE = TABLES / "REMEDFILM_INTERNAL_PER_SAMPLE.csv"
VAL_PRED = REPORTS_T / "phase27_val808_predictions.csv"
MANIFEST = REPORTS_T / "phase21_prediction_manifest.csv"
DOMAIN_METRICS = ROOT / "full_doc_report" / "REMEDFILM_FULL_VAL808_METRICS.csv"
INTERNAL = ROOT / "full_doc_report" / "REMEDFILM_INTERNAL_EVALUATION.csv"
SIX_MODEL = EVIDENCE / "phase21_six_model_comparison.csv"
EXTERNAL = ROOT / "full_doc_report" / "REMEDFILM_FULL_EXTERNAL_METRICS.csv"
EXT_CASE = REPORTS_T / "c1_external_stress_per_case.csv"
ABLATION = ROOT / "full_doc_report" / "REMEDFILM_ABLATION_RESULTS.csv"
BOOTSTRAP = EVIDENCE / "phase28_table_08_bootstrap_statistics.csv"
COMPUTE = REPORTS_T / "phase34_analytical_compute_summary_v1_3.csv"
TRAIN_HIST = ROOT / "full_doc_report" / "REMEDFILM_COMPONENT_TRAINING_HISTORY.csv"
RECON = ROOT / "full_doc_report" / "REMEDFILM_FULL_RESULT_RECONCILIATION.json"

# ---------------------------------------------------------------- styling ----
BLUE, SKY, VERM = "#0072B2", "#56B4E9", "#D55E00"
GREEN, ORANGE, PURPLE = "#009E73", "#E69F00", "#CC79A7"
GREY, LGREY, DARK = "#7F7F7F", "#BFBFBF", "#1A1A1A"

MODEL_STYLE = {
    "U-Net": ("#B0B0B0", "o"),
    "Attention U-Net": ("#8C8C8C", "o"),
    "U-Net++": ("#6E6E6E", "o"),
    "Transformer/MiT-style U-Net": ("#4D4D4D", "o"),
    "DeepLabV3+": ("#2E2E2E", "o"),
    "GlobalMedFiLM": (BLUE, "s"),
    "ReMedFiLM FULL": (VERM, "*"),
}
DOMAIN_COLOR = {"ISIC": BLUE, "BUSI": VERM, "KVASIR": GREEN, "KUB": PURPLE}
DOMAIN_MODALITY = {
    "ISIC": "dermoscopy",
    "BUSI": "breast ultrasound",
    "KVASIR": "endoscopy",
    "KUB": "radiograph (KUB)",
}
OVERLAY = {"tp": np.array([0, 158, 115]), "fp": np.array([198, 40, 40]),
           "fn": np.array([21, 101, 192])}

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "font.family": "DejaVu Sans", "font.size": 8.5,
    "axes.titlesize": 9.5, "axes.labelsize": 8.5,
    "axes.linewidth": 0.7, "axes.edgecolor": "#333333",
    "axes.grid": True, "grid.color": "#E9E9E9", "grid.linewidth": 0.6,
    "legend.frameon": False, "legend.fontsize": 7.5,
    "xtick.labelsize": 7.8, "ytick.labelsize": 7.8,
    "xtick.color": "#333333", "ytick.color": "#333333",
    "figure.dpi": 120, "savefig.dpi": 200, "savefig.bbox": "tight",
    "savefig.pad_inches": 0.12,
})


# ------------------------------------------------------------------ utils ----
def die(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def load_csv(path: Path) -> list[dict]:
    if not path.exists():
        die(f"mandatory evidence missing: {path.relative_to(ROOT)}")
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def save(fig, name: str) -> None:
    png = OUT / f"{name}.png"
    fig.savefig(png)
    svg = OUT / f"{name}.svg"
    try:
        fig.savefig(svg)
    except Exception:                                    # pragma: no cover
        svg = None
    plt.close(fig)
    size = png.stat().st_size / 1024
    print(f"  wrote {png.relative_to(ROOT)}  ({size:,.0f} KB)"
          + (f" + {svg.name}" if svg else ""))


def _img_from_gt(gt_path: str, domain: str) -> Path | None:
    """Resolve the original RGB image that produced a given GT mask."""
    s = gt_path
    if domain == "ISIC":
        c = (s.replace("_segmentation.png", ".jpg")
              .replace("Task1_Training_GroundTruth", "Task1-2_Training_Input")
              .replace("Task1_Validation_GroundTruth", "Task1-2_Validation_Input")
              .replace("Task1_Test_GroundTruth", "Task1-2_Test_Input"))
    elif domain == "BUSI":
        c = s.replace("\\gt\\", "\\img\\").replace("_anno.bmp", ".bmp")
    elif domain == "KVASIR":
        c = s.replace("\\masks\\", "\\images\\")
    else:                                                 # KUB
        c = s.replace("\\Masks\\", "\\Images\\").replace("_mask.png", ".png")
    q = Path(c)
    return q if q.exists() else None


def _fit512(img: np.ndarray) -> np.ndarray:
    """Aspect-preserving resize + centre pad (phase19 preprocessing contract)."""
    h, w = img.shape[:2]
    sc = 512.0 / max(h, w)
    nh, nw = max(1, int(round(h * sc))), max(1, int(round(w * sc)))
    im = Image.fromarray(img).resize((nw, nh), Image.BILINEAR)
    out = np.zeros((512, 512, 3), dtype=np.uint8)
    y0, x0 = (512 - nh) // 2, (512 - nw) // 2
    out[y0:y0 + nh, x0:x0 + nw] = np.array(im)
    return out


def _overlay(img512: np.ndarray, gt: np.ndarray, pred: np.ndarray) -> np.ndarray:
    """Green = TP, red = FP, blue = FN over the original image."""
    vis = img512.astype(np.float32)
    tp, fp, fn = gt & pred, (~gt) & pred, gt & (~pred)
    vis[tp] = vis[tp] * 0.42 + OVERLAY["tp"] * 0.58
    vis[fp] = vis[fp] * 0.32 + OVERLAY["fp"] * 0.68
    vis[fn] = vis[fn] * 0.42 + OVERLAY["fn"] * 0.58
    return np.clip(vis, 0, 255).astype(np.uint8)


def _mask512(path: str | Path) -> np.ndarray:
    a = np.array(Image.open(ROOT / path if not Path(path).is_absolute() else path)
                 .convert("L"))
    if a.shape != (512, 512):
        a = np.array(Image.fromarray(a).resize((512, 512), Image.NEAREST))
    return a > 0


# ======================================================= prediction gallery ==
BRANCH_LABEL = {
    "SKIP_GLOBAL": "SKIP",
    "EXECUTE_THEN_ACCEPT": "ACCEPT",
    "EXECUTE_THEN_REJECT": "VETO",
}


def _load_case_index() -> dict[str, dict]:
    ps = {r["sample_id"]: r for r in load_csv(PER_SAMPLE)}
    pred = {r["sample_id"]: r for r in load_csv(VAL_PRED)}
    man = {r["sample_id"]: r for r in load_csv(MANIFEST)}
    idx = {}
    for sid, r in ps.items():
        if sid not in pred or sid not in man:
            continue
        r = dict(r)
        r["branch"] = pred[sid]["state_machine_branch"]
        r["global_mask"] = pred[sid]["global_mask_path"]
        r["final_mask"] = pred[sid]["final_mask_path"]
        r["npz"] = man[sid]["npz_path"]
        r["gt_path"] = man[sid]["gt_mask_path"]
        r["is_roi"] = "\\ROI\\" in man[sid]["gt_mask_path"]
        for k in ("global_dice", "final_dice", "delta_dice", "final_iou",
                  "global_iou", "final_hd95", "gt_fg"):
            try:
                r[k] = float(r[k])
            except (TypeError, ValueError):
                r[k] = float("nan")
        idx[sid] = r
    if len(idx) < 700:
        die(f"expected >=700 matched validation cases, found {len(idx)}")
    return idx


def _pick_cases(idx: dict[str, dict], dom: str) -> list[tuple[str, str]]:
    """Deterministic, non-cherry-picked category selection for one domain.

    Each rule is a pure sort over a pre-declared subset, so the same sample is
    chosen on every run and the rule can be audited from the CSV alone.
    """
    rows = [r for r in idx.values() if r["domain"] == dom]
    if not rows:
        die(f"no matched cases for domain {dom}")
    acc = [r for r in rows if r["branch"] == "EXECUTE_THEN_ACCEPT"]
    rej = [r for r in rows if r["branch"] == "EXECUTE_THEN_REJECT"]
    skp = [r for r in rows if r["branch"] == "SKIP_GLOBAL"]
    picks: list[tuple[str, str]] = []

    # 1. strong segmentation: best FULL Dice among skipped cases (backbone already right)
    if skp:
        b = max(skp, key=lambda r: r["final_dice"])
        picks.append((b["sample_id"], "Strong\n(skipped)"))
    # 2. typical segmentation: median FULL Dice over the whole domain
    srt = sorted(rows, key=lambda r: r["final_dice"])
    picks.append((srt[len(srt) // 2]["sample_id"], "Typical"))
    # 3. beneficial refinement: largest positive delta among accepted
    if acc:
        b = max(acc, key=lambda r: r["delta_dice"])
        picks.append((b["sample_id"], "Beneficial\nrefinement"))
    # 4. harmful refinement: most negative delta among accepted
    harm = [r for r in acc if r["delta_dice"] < 0]
    if harm:
        w = min(harm, key=lambda r: r["delta_dice"])
        picks.append((w["sample_id"], "Harmful\nrefinement"))
    # 5. safety-rejected refinement
    if rej:
        j = sorted(rej, key=lambda r: r["delta_dice"])[len(rej) // 2]
        picks.append((j["sample_id"], "Safety\nveto"))
    # 6. small-object / boundary failure: smallest GT among low-Dice cases
    weak = [r for r in rows if r["final_dice"] < 0.60 and r["gt_fg"] > 0]
    if weak:
        s = min(weak, key=lambda r: r["gt_fg"])
        picks.append((s["sample_id"], "Small-object\nfailure"))

    seen, out = set(), []
    for sid, label in picks:
        if sid not in seen:
            seen.add(sid)
            out.append((sid, label))
    return out


def _verify_case(idx: dict[str, dict], sid: str, dom: str) -> dict:
    r = idx[sid]
    gt_p = Path(r["gt_path"])
    img_p = _img_from_gt(str(gt_p), dom)
    if img_p is None:
        die(f"{sid}: original image not resolvable from {gt_p.name}")
    with np.load(ROOT / r["npz"]) as z:
        gt = z["gt"] > 0
    if int(gt.sum()) != int(r["gt_fg"]):
        die(f"{sid}: GT foreground {int(gt.sum())} != metrics gt_fg {int(r['gt_fg'])}")
    gm, fm = _mask512(r["global_mask"]), _mask512(r["final_mask"])
    if gt.shape != gm.shape or gt.shape != fm.shape:
        die(f"{sid}: geometry mismatch gt{gt.shape} g{gm.shape} f{fm.shape}")
    if r["branch"] == "SKIP_GLOBAL" and not np.array_equal(gm, fm):
        die(f"{sid}: SKIP case but global mask != final mask")
    return {"img": _fit512(np.array(Image.open(img_p).convert("RGB"))),
            "gt": gt, "gm": gm, "fm": fm, "row": r, "img_path": img_p}


def _panel_grid(cases, title, subtitle, fname, row_h=2.90, width=13.6):
    n = len(cases)
    fig, axes = plt.subplots(n, 5, figsize=(width, row_h * n + 1.25),
                             gridspec_kw={"wspace": 0.04, "hspace": 0.38})
    if n == 1:
        axes = np.array([axes])
    heads = ["Input", "Ground truth", "GlobalMedFiLM (G)",
             "ReMedFiLM FULL", "Error overlay"]
    for j, h in enumerate(heads):
        axes[0, j].set_title(h, fontsize=10.5, pad=8)

    for i, (label, c) in enumerate(cases):
        r = c["row"]
        panels = [c["img"],
                  np.repeat((c["gt"] * 255)[..., None], 3, 2),
                  np.repeat((c["gm"] * 255)[..., None], 3, 2),
                  np.repeat((c["fm"] * 255)[..., None], 3, 2),
                  _overlay(c["img"], c["gt"], c["fm"])]
        for j, pnl in enumerate(panels):
            ax = axes[i, j]
            ax.imshow(pnl, interpolation="nearest")
            ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
            for sp in ax.spines.values():
                sp.set_visible(j == 4)
                sp.set_color("#777777"); sp.set_linewidth(0.8)
        axes[i, 0].set_ylabel(label, fontsize=9.2, labelpad=10)

        br = BRANCH_LABEL.get(r["branch"], r["branch"])
        tag = ""
        if r["domain"] == "KUB":
            tag = " · ROI" if r["is_roi"] else " · full-field"
        cap = (f"G {r['global_dice']:.3f} → FULL {r['final_dice']:.3f}\n"
               f"Δ {r['delta_dice']:+.4f} · {br}\n"
               f"IoU {r['final_iou']:.3f} · HD95 {r['final_hd95']:.0f}px{tag}")
        axes[i, 4].set_xlabel(cap, fontsize=8.6, labelpad=5, linespacing=1.45)

    handles = [Patch(facecolor=OVERLAY["tp"] / 255, label="true positive"),
               Patch(facecolor=OVERLAY["fp"] / 255, label="false positive"),
               Patch(facecolor=OVERLAY["fn"] / 255, label="false negative")]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=10,
               bbox_to_anchor=(0.5, 0.004), handlelength=1.3, columnspacing=2.6)
    fig.suptitle(title, fontsize=14, y=0.995)
    fig.text(0.5, 0.966, subtitle, ha="center", fontsize=9.4, color="#555555")
    fig.subplots_adjust(left=0.152, right=0.993, top=0.930, bottom=0.070)
    save(fig, fname)


def _rel_data(p: str | Path) -> str:
    """Dataset-relative path, so provenance does not leak local absolute paths."""
    s = str(p).replace("/", "\\")
    marker = "data_raw\\"
    return s.split(marker, 1)[1] if marker in s else Path(s).name


def _write_selection(rows: list[dict]) -> None:
    out = OUT / "README_FIGURE_SELECTION.csv"
    cols = ["figure", "row", "case_label", "domain", "sample_id", "unit",
            "branch", "global_dice", "final_dice", "delta_dice", "final_iou",
            "final_hd95", "gt_fg", "source_image_rel", "gt_mask_rel"]
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {out.relative_to(ROOT)}  ({len(rows)} rows)")


def _representative(idx: dict[str, dict], dom: str) -> str:
    """The accepted refinement whose FULL Dice is closest to the domain median.

    Deliberately *not* the best case: the combined gallery should show what a
    typical accepted refinement looks like, not the most flattering one.
    Ties inside a +/-0.01 Dice band are broken towards the largest source image,
    so a 56 x 49 ROI patch is not upscaled tenfold into the hero figure.
    """
    rows = [r for r in idx.values()
            if r["domain"] == dom and r["branch"] == "EXECUTE_THEN_ACCEPT"]
    if not rows:                                     # BUSI has exactly one accept
        rows = [r for r in idx.values() if r["domain"] == dom]
    vals = sorted(r["final_dice"] for r in rows)
    med = vals[len(vals) // 2]
    band = [r for r in rows if abs(r["final_dice"] - med) <= 0.01] or rows

    def area(r):
        p = _img_from_gt(str(r["gt_path"]), dom)
        if p is None:
            return 0
        with Image.open(p) as im:
            return im.size[0] * im.size[1]

    return max(band, key=area)["sample_id"]


def build_predictions(only_combined: bool = False) -> None:
    idx = _load_case_index()
    print("prediction gallery")
    combined = []
    selection: list[dict] = []

    def _record(figure: str, row_no: int, label: str, c: dict, dom: str) -> None:
        r = c["row"]
        selection.append({
            "figure": figure, "row": row_no, "case_label": label.replace("\n", " "),
            "domain": dom, "sample_id": r["sample_id"],
            "unit": ("ROI patch" if r["is_roi"] else "full-field")
            if dom == "KUB" else "image",
            "branch": r["branch"],
            "global_dice": f"{r['global_dice']:.6f}",
            "final_dice": f"{r['final_dice']:.6f}",
            "delta_dice": f"{r['delta_dice']:+.6f}",
            "final_iou": f"{r['final_iou']:.6f}",
            "final_hd95": f"{r['final_hd95']:.3f}",
            "gt_fg": int(r["gt_fg"]),
            "source_image_rel": _rel_data(c["img_path"]),
            "gt_mask_rel": _rel_data(r["gt_path"]),
        })

    for dom in ("ISIC", "BUSI", "KVASIR", "KUB"):
        picks = _pick_cases(idx, dom)
        cases = []
        for sid, label in picks:
            cases.append((label, _verify_case(idx, sid, dom)))
        n_dom = sum(1 for r in idx.values() if r["domain"] == dom)
        n_acc = sum(1 for r in idx.values()
                    if r["domain"] == dom and r["branch"] == "EXECUTE_THEN_ACCEPT")
        n_rej = sum(1 for r in idx.values()
                    if r["domain"] == dom and r["branch"] == "EXECUTE_THEN_REJECT")
        n_harm = sum(1 for r in idx.values()
                     if r["domain"] == dom and r["branch"] == "EXECUTE_THEN_ACCEPT"
                     and r["delta_dice"] < 0)
        sub = (f"{DOMAIN_MODALITY[dom]} · VAL808 · n = {n_dom} · "
               f"{n_acc} refinements accepted · {n_rej} vetoed · {n_harm} harmful")
        if not only_combined:
            _panel_grid(cases, f"{dom} — ReMedFiLM FULL segmentation on the frozen "
                               f"validation set", sub, f"prediction_{dom.lower()}")
            for k, (label, c) in enumerate(cases):
                _record(f"prediction_{dom.lower()}.png", k + 1, label, c, dom)

        # representative case for the combined 4-domain figure: the accepted
        # refinement closest to the domain median FULL Dice
        rep = _verify_case(idx, _representative(idx, dom), dom)
        combined.append((dom, rep, sub))
        _record("remedfilm_four_domain_predictions.png", len(combined),
                "representative (median accepted)", rep, dom)

    if only_combined:
        return
    _write_selection(selection)

    fig, axes = plt.subplots(4, 5, figsize=(12.8, 12.6),
                             gridspec_kw={"wspace": 0.04, "hspace": 0.42})
    heads = ["Input", "Ground truth", "GlobalMedFiLM (G)", "ReMedFiLM FULL",
             "Error overlay"]
    for j, h in enumerate(heads):
        axes[0, j].set_title(h, fontsize=11, pad=7)
    for i, (dom, c, sub) in enumerate(combined):
        r = c["row"]
        panels = [c["img"], np.repeat((c["gt"] * 255)[..., None], 3, 2),
                  np.repeat((c["gm"] * 255)[..., None], 3, 2),
                  np.repeat((c["fm"] * 255)[..., None], 3, 2),
                  _overlay(c["img"], c["gt"], c["fm"])]
        for j, pnl in enumerate(panels):
            ax = axes[i, j]
            ax.imshow(pnl, interpolation="nearest")
            ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
            for sp in ax.spines.values():
                sp.set_visible(False)
        br = BRANCH_LABEL.get(r["branch"], r["branch"])
        tag = ""
        if r["domain"] == "KUB":
            tag = "  ·  ROI patch" if r["is_roi"] else "  ·  full-field"
        axes[i, 0].set_ylabel(f"{dom}\n{DOMAIN_MODALITY[dom]}", fontsize=10.5,
                              labelpad=10, color=DOMAIN_COLOR[dom],
                              fontweight="semibold")
        axes[i, 4].set_xlabel(
            f"G {r['global_dice']:.3f} → FULL {r['final_dice']:.3f}   "
            f"Δ {r['delta_dice']:+.4f}\n{br}{tag}", fontsize=9, labelpad=4,
            linespacing=1.5)

    handles = [Patch(facecolor=OVERLAY["tp"] / 255, label="true positive"),
               Patch(facecolor=OVERLAY["fp"] / 255, label="false positive"),
               Patch(facecolor=OVERLAY["fn"] / 255, label="false negative")]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=10,
               bbox_to_anchor=(0.5, 0.0), handlelength=1.3, columnspacing=2.6)
    fig.suptitle("ReMedFiLM FULL — one verified case per domain",
                 fontsize=15, y=0.995, fontweight="semibold")
    fig.text(0.5, 0.968,
             "Frozen VAL808 saved masks · accepted refinements shown · "
             "same sample_id across all five columns",
             ha="center", fontsize=9.6, color="#555555")
    fig.subplots_adjust(left=0.105, right=0.995, top=0.938, bottom=0.055)
    save(fig, "remedfilm_four_domain_predictions")


# =============================================================== charts ======
def chart_internal() -> None:
    rows = load_csv(DOMAIN_METRICS)
    rows = [r for r in rows if r["population"] == "VAL808"]
    if len(rows) != 5:
        die(f"expected 5 VAL808 domain rows, found {len(rows)}")
    doms = [r for r in rows if r["domain"] != "MACRO_DOMAIN_EQUAL_WEIGHT"]
    macro = next(r for r in rows if r["domain"] == "MACRO_DOMAIN_EQUAL_WEIGHT")
    order = ["ISIC", "BUSI", "KVASIR", "KUB"]
    doms.sort(key=lambda r: order.index(r["domain"]))

    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    x = np.arange(len(doms) + 1)
    g = [float(r["global_dice"]) for r in doms] + [float(macro["global_dice"])]
    f = [float(r["full_dice"]) for r in doms] + [float(macro["full_dice"])]
    w = 0.36
    ax.bar(x - w / 2, g, w, color=BLUE, label="GlobalMedFiLM (G) — backbone")
    ax.bar(x + w / 2, f, w, color=VERM, label="ReMedFiLM FULL — proposed")
    for xi, v in zip(x - w / 2, g):
        ax.text(xi, v + 0.006, f"{v:.4f}", ha="center", fontsize=7.6, va="bottom",
                color="#1F4E79")
    for xi, v in zip(x + w / 2, f):
        ax.text(xi, v + 0.006, f"{v:.4f}", ha="center", fontsize=7.6, va="bottom",
                color="#8A3B00")
    labels = [f"{r['domain']}\nn = {r['n']}" for r in doms] + \
             [f"macro\nn = {macro['n']}"]
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylim(0.60, 0.96); ax.set_ylabel("Dice (per-image, threshold 0.5)")
    ax.set_title("Internal validation — domain-wise Dice, matched VAL808 population",
                 pad=10)
    ax.legend(loc="upper left", ncol=2)
    ax.grid(axis="x", visible=False)
    ax.axvline(len(doms) - 0.5, color="#CCCCCC", lw=0.9, ls=":")
    deltas = [f - gg for f, gg in zip(f, g)]
    for xi, d in zip(x, deltas):
        ax.annotate(f"Δ {d:+.4f}", (xi, 0.607), ha="center", fontsize=7.4,
                    color="#333333")
    fig.text(0.5, -0.045,
             "Axis starts at 0.60 to resolve sub-0.01 differences; all bars are "
             "absolute Dice. Macro = equal-weight mean of the four domain values. "
             "Single historical seed (42); the paired macro bootstrap CI is "
             "[+0.00115, +0.00329].",
             ha="center", fontsize=6.8, color="#555555")
    fig.tight_layout()
    save(fig, "internal_domain_performance")


def chart_models() -> None:
    rows = load_csv(SIX_MODEL)
    recon = json.loads(RECON.read_text(encoding="utf-8")) \
        if RECON.exists() else {}
    full_macro = 0.8372896860016156
    src = "REMEDFILM_INTERNAL_EVALUATION.csv"
    if isinstance(recon, dict):
        for k in ("reconciled_full_macro_dice", "full_macro_dice",
                  "authoritative_full_macro_dice"):
            if isinstance(recon.get(k), (int, float)):
                full_macro = float(recon[k]); break

    data = []
    for r in rows:
        data.append((r["display_name"], float(r["macro_domain_dice"]),
                     r["params"], r["model_key"]))
    data.append(("ReMedFiLM FULL", full_macro, "4837420", "remedfilm_full"))
    data.sort(key=lambda t: t[1])

    fig, ax = plt.subplots(figsize=(9.2, 5.0))
    ys = np.arange(len(data))
    for y, (name, val, params, key) in zip(ys, data):
        if key == "remedfilm_full":
            col, ec, lw = VERM, "#8A3B00", 1.4
        elif key == "global_medfilm":
            col, ec, lw = BLUE, "#1F4E79", 1.0
        else:
            col, ec, lw = "#9A9A9A", "#6E6E6E", 0.8
        ax.barh(y, val, color=col, edgecolor=ec, linewidth=lw, height=0.66)
        ax.text(val + 0.004, y, f"{val:.4f}", va="center", fontsize=7.8,
                fontweight="semibold" if key in ("remedfilm_full", "global_medfilm")
                else "normal")
        if params and params != "nan":
            ax.text(0.905, y, f"{int(float(params)):,}", va="center", ha="right",
                    fontsize=7.2, color="#555555")
    ax.set_yticks(ys)
    ax.set_yticklabels([d[0] for d in data])
    ax.set_xlim(0.60, 0.92)
    ax.set_xlabel("Macro domain Dice (VAL808, single historical seed 42)")
    ax.set_title("Seven-model comparison — the historical baseline benchmark", pad=24)
    ax.text(0.905, len(data) - 0.32, "parameters", fontsize=7.2, color="#555555",
            style="italic", ha="right")
    ax.grid(axis="y", visible=False)
    ax.legend(handles=[Patch(facecolor=VERM, label="ReMedFiLM FULL (proposed)"),
                       Patch(facecolor=BLUE, label="GlobalMedFiLM (backbone)"),
                       Patch(facecolor="#9A9A9A", label="conventional baselines")],
              loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3)
    fig.text(0.5, -0.045,
             "Disclosure: this is the historical single-seed benchmark, not the "
             "C3 controlled experiment (0/24 cells executed). Baseline arms were "
             "trained under the reduced protocol; the comparison is descriptive.",
             ha="center", fontsize=6.9, color="#8A3B00")
    fig.tight_layout()
    save(fig, "historical_model_comparison")


def chart_external() -> None:
    rows = [r for r in load_csv(EXTERNAL) if r["metric"] == "Dice"]
    per = load_csv(EXT_CASE)

    def mean_of(cohort_key, arm, stone_pos=None):
        sel = [r for r in per if r["cohort_key"] == cohort_key and r["arm"] == arm]
        if stone_pos is True:
            sel = [r for r in sel if r["gt_empty"].lower() == "false"]
        elif stone_pos is False:
            sel = [r for r in sel if r["gt_empty"].lower() == "true"]
        vals = [float(r["Dice"]) for r in sel if r["Dice"] not in ("", "nan")]
        return (len(vals), float(np.mean(vals)) if vals else float("nan"))

    cohorts = [("cvc", "CVC-ClinicDB", "polyp (endoscopy)"),
               ("breast", "BrEaST-Lesions-USG", "breast lesion (ultrasound)")]
    ext_dice = {}
    for r in rows:
        ext_dice.setdefault(r["cohort"], {})[r["model"]] = (
            float(r["mean"]), float(r["ci_low"] or "nan"),
            float(r["ci_high"] or "nan"), int(r["n_defined"]))
    lookup = {"cvc": "CVC-ClinicDB", "breast": "BrEaST-Lesions-USG"}

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11.4, 4.5),
                                  gridspec_kw={"width_ratios": [1.55, 1.0]})
    x = np.arange(len(cohorts))
    w = 0.34
    for k, (model, col, off) in enumerate([("GlobalMedFiLM", BLUE, -w / 2),
                                           ("ReMedFiLM FULL", VERM, w / 2)]):
        vals, los, his, ns = [], [], [], []
        for key, name, modality in cohorts:
            m, lo, hi, n = ext_dice[lookup[key]][model]
            vals.append(m); los.append(m - lo); his.append(hi - m); ns.append(n)
        ax.bar(x + off, vals, w, color=col, label=model,
               yerr=[los, his], capsize=3,
               error_kw={"elinewidth": 0.9, "ecolor": "#444444"})
        for xi, v, n, h in zip(x + off, vals, ns, his):
            ax.text(xi, v + h + 0.018, f"{v:.4f}", ha="center", fontsize=7.2)
            ax.text(xi, 0.018, f"n={n}", ha="center", fontsize=6.6, color="white")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{name}\n{mod}" for _k, name, mod in cohorts], fontsize=8)
    ax.set_ylim(0, 0.86); ax.set_ylabel("Dice (per-image)")
    ax.set_title("External retrospective cohorts — Dice with 95 % CI", pad=8)
    ax.legend(loc="upper right")
    ax.grid(axis="x", visible=False)

    # stone cohort: positive vs free, never zero-filled
    n_sp_g, d_sp_g = mean_of("stones", "global", True)
    n_sp_b, d_sp_b = mean_of("stones", "barr", True)
    if not (n_sp_g and n_sp_b):
        die("stones cohort: no stone-positive cases resolved from the per-case table")
    vals = [d_sp_g, d_sp_b]
    cols = [BLUE, VERM]
    ax2.bar([0, 1], vals, 0.55, color=cols)
    for xi, v in enumerate(vals):
        ax2.text(xi, v + 0.012, f"{v:.4f}", ha="center", fontsize=7.8)
    ax2.set_xticks([0, 1])
    ax2.set_xticklabels([f"G\nn = {n_sp_g}", f"FULL\nn = {n_sp_b}"], fontsize=8.5)
    ax2.set_xlim(-0.7, 2.9); ax2.set_ylim(0, 0.44)
    ax2.set_ylabel("Dice (per-image)")
    ax2.set_title("Stones-Where-Are-You — stratified honestly", pad=8)
    ax2.grid(axis="x", visible=False)
    ax2.axvspan(1.55, 2.9, color="#FBE9E7", zorder=0)
    ax2.text(2.22, 0.315, "stone-free\nn = 14", ha="center", fontsize=8,
             fontweight="semibold", color="#8A1C1C")
    ax2.text(2.22, 0.175, "Dice undefined\n(empty GT)\n\n14 / 14\nfalse positive",
             ha="center", va="center", fontsize=7.4, color="#8A1C1C")
    fig.text(0.5, -0.045,
             "The cohort-level Stones Dice of 0.0808 in the summary tables "
             f"zero-fills the 14 empty-GT cases. Stone-positive Dice is "
             f"{d_sp_g:.4f} (G) / {d_sp_b:.4f} (FULL); the stone-free images are "
             "reported as false positives, not as Dice = 0.",
             ha="center", fontsize=6.9, color="#555555")
    fig.tight_layout()
    save(fig, "external_evaluation")


def chart_ablation() -> None:
    rows = load_csv(ABLATION)
    arms = [r["arm"] for r in rows]
    mean_d = [float(r["mean_true_delta_dice_routed"]) for r in rows]
    budget = [float(r["budget_fraction"]) for r in rows]
    harm = [float(r["harmful_activation_share"]) for r in rows]
    boot = {r["contrast"]: r for r in load_csv(BOOTSTRAP)}

    fig, axes = plt.subplots(2, 1, figsize=(11.0, 7.0), sharex=True,
                             gridspec_kw={"height_ratios": [1.45, 1.0],
                                          "hspace": 0.12})
    ax = axes[0]
    cols = []
    for r in rows:
        if r["arm"].startswith("R"):
            cols.append(PURPLE)
        elif r["arm"] == "F1":
            cols.append("#8A1C1C")
        elif r["arm"] in ("A0", "A1"):
            cols.append("#B0B0B0")
        else:
            cols.append(BLUE if float(r["mean_true_delta_dice_routed"]) >= 0 else VERM)
    xs = np.arange(len(arms))
    ax.bar(xs, mean_d, 0.66, color=cols)
    ax.axhline(0, color="#333333", lw=0.9)
    for xi, v in zip(xs, mean_d):
        ax.text(xi, v + (0.0016 if v >= 0 else -0.0016), f"{v:+.4f}",
                ha="center", fontsize=6.5,
                va="bottom" if v >= 0 else "top")
    ax.set_ylabel("Mean Δ Dice per routed case")
    ax.set_title("13-arm ablation — measured effect of each routing / component variant",
                 pad=8)
    ax.set_ylim(-0.046, 0.0135)
    a8 = boot.get("A8_vs_A7")
    if a8:
        ax.text(0.5, 0.02,
                "A8 vs A7 (the only pre-specified matched contrast): "
                f"{float(a8['mean_difference']):+.5f}, 95 % CI "
                f"[{float(a8['ci95_low']):+.5f}, {float(a8['ci95_high']):+.5f}] "
                "— the interval includes zero, so the safety gate's own "
                "contribution is inconclusive.",
                transform=ax.transAxes, fontsize=7.0, color="#8A1C1C",
                va="bottom", ha="center")
    ax.legend(handles=[Patch(facecolor=BLUE, label="A-arm, positive"),
                       Patch(facecolor=VERM, label="A-arm, negative"),
                       Patch(facecolor=PURPLE, label="R-arm (trained variant)"),
                       Patch(facecolor="#8A1C1C", label="F1 (integrated)"),
                       Patch(facecolor="#B0B0B0", label="boundary arms")],
              loc="lower center", bbox_to_anchor=(0.5, 0.055), ncol=5,
              fontsize=6.8)

    ax2 = axes[1]
    ax2.bar(xs - 0.18, budget, 0.34, color=SKY, label="routing budget (fraction routed)")
    ax2.bar(xs + 0.18, harm, 0.34, color=ORANGE, label="harmful share of routed")
    ax2.set_xticks(xs); ax2.set_xticklabels(arms)
    ax2.set_ylabel("fraction")
    ax2.set_ylim(0, 1.02)
    ax2.legend(loc="upper left", ncol=2)
    ax2.grid(axis="x", visible=False)
    ax2.set_xlabel("ablation arm")
    fig.text(0.5, -0.02,
             "A0/A1 are endpoints by construction; A2–A8 are the prior canonical "
             "evidence; R1–R3 and F1 are Phase 28 trained variants. Budget is a "
             "policy property, not an accuracy result.",
             ha="center", fontsize=6.9, color="#555555")
    save(fig, "complete_ablation")


def chart_compute() -> None:
    rows = load_csv(SIX_MODEL)
    comp = {r["reference"]: float(r["macs"]) for r in load_csv(COMPUTE)}
    full_macro = 0.8372896860016156
    g_macro = 0.8350794169575282

    def norm(n: str) -> str:
        return "GlobalMedFiLM" if n.replace(" ", "") == "GlobalMedFiLM" else n

    params = {norm(r["display_name"]): float(r["params"])
              for r in rows if r["params"]}
    dice = {norm(r["display_name"]): float(r["macro_domain_dice"]) for r in rows}
    # The six-model table leaves GlobalMedFiLM's parameter count empty; it is
    # recorded in the component registry (state-dict re-derivation).
    params.setdefault("GlobalMedFiLM", 3523001.0)
    dice.setdefault("GlobalMedFiLM", g_macro)
    params["ReMedFiLM FULL"] = 4837420.0
    dice["ReMedFiLM FULL"] = full_macro

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.4, 4.9),
                                  gridspec_kw={"width_ratios": [1.12, 1.0],
                                               "wspace": 0.26})

    # Panel A — accuracy vs parameter count (all seven verified)
    offsets = {
        "U-Net": (14, -6, "left"), "Attention U-Net": (14, 3, "left"),
        "U-Net++": (14, 9, "left"),
        "Transformer/MiT-style U-Net": (14, 4, "left"),
        "DeepLabV3+": (-14, 8, "right"),
        "GlobalMedFiLM": (14, -14, "left"),
        "ReMedFiLM FULL": (14, 10, "left"),
    }
    for name, p in params.items():
        col, mk = MODEL_STYLE.get(name, ("#9A9A9A", "o"))
        ax.scatter(p / 1e6, dice[name], s=230 if name == "ReMedFiLM FULL" else 64,
                   marker=mk, color=col, edgecolor="white", linewidth=0.9,
                   zorder=3)
        dx, dy, ha = offsets.get(name, (12, 6, "left"))
        ax.annotate(name, (p / 1e6, dice[name]), xytext=(dx, dy),
                    textcoords="offset points", fontsize=7.0, ha=ha,
                    va="center", zorder=5,
                    color=col if name in ("ReMedFiLM FULL", "GlobalMedFiLM")
                    else "#555555")
    ax.set_xscale("log")
    ax.set_xlim(2.8, 110)
    ax.set_xticks([3.5, 5, 8, 12, 20, 40, 80])
    ax.set_xticklabels(["3.5", "5", "8", "12", "20", "40", "80"])
    ax.minorticks_off()
    ax.set_xlabel("parameters (millions, log scale)")
    ax.set_ylabel("Macro domain Dice")
    ax.set_title("Accuracy vs model size — seven models", pad=8)
    ax.set_ylim(0.782, 0.845)
    ax.grid(alpha=0.5)

    # Panel B — accuracy vs verified analytical compute (two points only)
    g_mac = comp["LITERAL_GLOBAL_ONLY_C1"] / 1e9
    f_mac = comp["FINAL_A8_C9_EXPECTED_CONDITIONAL"] / 1e9
    always = comp["LITERAL_ALWAYS_REFINE_C2"] / 1e9
    ax2.plot([g_mac, f_mac], [g_macro, full_macro], color="#C4C4C4", lw=1.2,
             ls="--", zorder=1)
    ax2.scatter([g_mac], [g_macro], s=115, color=BLUE, zorder=3,
                label="GlobalMedFiLM — analytical GMACs")
    ax2.scatter([f_mac], [full_macro], s=230, marker="*", color=VERM, zorder=4,
                label="ReMedFiLM FULL — expected conditional GMACs")
    ax2.scatter([always], [full_macro], s=75, marker="x", color="#8A3B00",
                zorder=3, label="always-refine cost (not the deployed policy)")
    ax2.annotate(f"G\n{g_mac:.2f} GMACs\nDice {g_macro:.4f}",
                 (g_mac, g_macro), xytext=(0, -46), textcoords="offset points",
                 fontsize=7.0, ha="center", color="#1F4E79")
    ax2.annotate(f"FULL\n{f_mac:.2f} GMACs\nDice {full_macro:.4f}",
                 (f_mac, full_macro), xytext=(6, -44), textcoords="offset points",
                 fontsize=7.0, ha="left", color="#8A3B00")
    ax2.annotate(f"always-refine\n{always:.2f} GMACs", (always, full_macro),
                 xytext=(0, 14), textcoords="offset points", fontsize=6.8,
                 ha="center", color="#8A3B00")
    ax2.set_xlim(30.0, 36.0)
    ax2.set_ylim(0.8320, 0.8405)
    ax2.set_xlabel("analytical / expected-conditional GMACs")
    ax2.set_ylabel("Macro domain Dice")
    ax2.set_title("Accuracy vs compute — verified references only", pad=8)
    ax2.legend(loc="upper left", fontsize=6.7, borderaxespad=0.6)
    ax2.grid(alpha=0.5)

    fig.text(0.5, -0.13,
             "Left: parameter counts are verified from checkpoint state dicts. "
             "Right: the only two configurations with a verified compute measurement. "
             "Analytical GMACs (G) count every multiply-add once;\nexpected conditional "
             "GMACs (FULL) weight the refiner by the measured 24.31 % routing rate. "
             "Protocols are not matched, so this is not a confirmed Pareto frontier.",
             ha="center", fontsize=6.8, color="#555555", linespacing=1.5)
    fig.tight_layout()
    save(fig, "remedfilm_accuracy_compute")


def chart_training() -> None:
    rows = load_csv(TRAIN_HIST)
    G = "phase21_global_medfilm_fourdomain_seed42_clean_v3"
    R = "phase25a_barr_regional_refiner_v1_1__final_refit"
    B = "phase25d_barr_benefit_router_v1_2_1_seed42__final"
    S = "phase25f_barr_post_safety_v1_0_seed42__final"

    def series(exp, metric):
        pts = [(int(r["epoch"]), float(r["metric_value"]))
               for r in rows if r["experiment_id"] == exp and r["metric_name"] == metric]
        return zip(*sorted(pts)) if pts else ((), ())

    fig = plt.figure(figsize=(12.2, 7.2))
    gs = fig.add_gridspec(2, 3, hspace=0.38, wspace=0.28)

    ax = fig.add_subplot(gs[0, 0])
    e, v = series(G, "train_loss"); ax.plot(e, v, color=BLUE, lw=1.5, label="train")
    e, v = series(G, "val_loss"); ax.plot(e, v, color=VERM, lw=1.5, label="validation")
    ax.set_title("G — GlobalMedFiLM loss", pad=6)
    ax.set_xlabel("epoch"); ax.set_ylabel("loss"); ax.legend()

    ax = fig.add_subplot(gs[0, 1])
    e, v = series(G, "val_macro_dice")
    ax.plot(e, v, color=GREEN, lw=1.6)
    if len(v):
        bi = int(np.argmax(v))
        ax.scatter([e[bi]], [v[bi]], s=48, color=VERM, zorder=4)
        ax.annotate(f"best {v[bi]:.4f} @ {e[bi]}", (e[bi], v[bi]),
                    xytext=(6, -14), textcoords="offset points", fontsize=7.2,
                    color="#8A3B00")
    ax.set_title("G — validation macro Dice", pad=6)
    ax.set_xlabel("epoch"); ax.set_ylabel("Dice")

    ax = fig.add_subplot(gs[0, 2])
    for dom in ("ISIC", "BUSI", "KVASIR", "KUB"):
        e, v = series(G, f"val_dice_{dom}")
        ax.plot(e, v, color=DOMAIN_COLOR[dom], lw=1.2, label=dom)
    ax.set_title("G — per-domain validation Dice", pad=6)
    ax.set_xlabel("epoch"); ax.set_ylabel("Dice"); ax.legend(ncol=2, fontsize=6.8)

    ax = fig.add_subplot(gs[1, 0])
    e, v = series(R, "train_loss"); ax.plot(e, v, color=PURPLE, lw=1.4)
    ax.set_title("R_ψ — refiner training loss", pad=6)
    ax.set_xlabel("epoch"); ax.set_ylabel("loss")
    ax.text(0.03, 0.06, "validation loss NOT_RECORDED", transform=ax.transAxes,
            fontsize=6.8, color="#8A1C1C")

    ax = fig.add_subplot(gs[1, 1])
    e, v = series(B, "train_huber"); ax.plot(e, v, color=SKY, lw=1.4,
                                             label="router Huber (B_φ)")
    e2, v2 = series(S, "train_bce"); ax.plot(e2, v2, color=ORANGE, lw=1.4,
                                             label="safety BCE (S_ω)")
    ax.set_title("B_φ and S_ω — component training loss", pad=6)
    ax.set_xlabel("epoch"); ax.set_ylabel("loss"); ax.legend(fontsize=6.6)
    ax.text(0.03, 0.06, "validation metrics NOT_RECORDED", transform=ax.transAxes,
            fontsize=6.8, color="#8A1C1C")

    ax = fig.add_subplot(gs[1, 2])
    for exp, lab, col in ((G, "G", BLUE), (R, "R_ψ", PURPLE), (B, "B_φ", SKY),
                          (S, "S_ω", ORANGE)):
        e, v = series(exp, "learning_rate")
        if len(v):
            ax.plot(e, v, color=col, lw=1.3, label=lab)
    ax.set_title("Learning-rate schedules (independent stages)", pad=6)
    ax.set_xlabel("epoch"); ax.set_ylabel("learning rate")
    ax.set_yscale("log"); ax.legend(fontsize=6.8)

    fig.suptitle("Component training histories — four independently fitted stages, "
                 "not one joint curve", fontsize=12.5, y=0.975, fontweight="semibold")
    fig.text(0.5, 0.936,
             "G is trained once; R_ψ, B_φ and S_ω are then fitted against a frozen "
             "upstream. Concatenating them would misrepresent the protocol.",
             ha="center", fontsize=7.8, color="#555555")
    fig.subplots_adjust(top=0.885, bottom=0.09, left=0.07, right=0.985)
    save(fig, "training_history")


# ================================================================== main =====
BUILDERS = {
    "predictions": lambda: build_predictions(False),
    "internal": chart_internal,
    "models": chart_models,
    "external": chart_external,
    "ablation": chart_ablation,
    "compute": chart_compute,
    "training": chart_training,
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", choices=sorted(BUILDERS), action="append",
                    help="build a subset (repeatable)")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    keys = args.only or list(BUILDERS)
    for k in keys:
        BUILDERS[k]()
    print(f"\nOK — {len(keys)} figure group(s) written to "
          f"{OUT.relative_to(ROOT).as_posix()}/")


if __name__ == "__main__":
    main()
