"""ReMedFiLM V8 -- code-verified methodology figure family.

This is the V8 replacement for the V5/V6/V7 infographic.  The user's raster
``assets/figures/remedfilm_inference_infographic.png`` remains the *visual*
reference (three panels, 16:9 canvas, white ground, navy type), but every
arrow, module name, tensor dimension, loss and threshold below was re-derived
from the frozen implementation.  Where the reference image asserts something
the code does not support, the V8 figure OMITS or CORRECTS it; the full list
is emitted as ``REMEDFILM_V8_METHODOLOGY_ARROWS.json``.

Verified sources (read-only, never modified)
-------------------------------------------
  src/models/film/global_medfilm.py        G, E(t) in R^32, 5 FiLM sites
  src/models/barr/regional_refiner.py      R_psi, 4-channel crop input
  src/models/barr/phase25_models.py        B_phi (202+16=218), S_omega (16+4=20)
  src/models/barr/ra_medfilm_barr.py       canonical 4-state machine, fusion,
                                           thresholds, utility, frozen inputs
  scripts/training/train_phase25a_refiner.py   0.5*BCE + 0.5*soft Dice
  scripts/analysis/train_phase25d_router.py    HuberLoss(delta=0.05)
  scripts/analysis/phase25f_execution_common.py BCEWithLogitsLoss
  reports/tables/phase27_val808_predictions.csv  VAL808 state counts

Critical V8 corrections vs the user's infographic / V7
------------------------------------------------------
  C01  G has its OWN 32-D task embedding; B_phi has a SEPARATE 16-D embedding;
       S_omega takes a 4-D one-hot.  There is no single shared "E(t)".
  C02  B_phi is PRE-refinement and consumes a frozen 202-D GT-free feature
       vector, NOT "global features Fg" and NOT the cropped ROI.
  C03  R_psi is a 4-channel CNN (BARRRegionalRefinerV1), NOT a "residual
       refiner" with FiLM bars, and does NOT emit a "delta P" correction.
  C04  Fusion is deterministic ROI REPLACEMENT (no alpha blending, no "+").
  C05  The canonical wrapper registers R_psi but NEVER CALLS IT.  The refined
       crop probability is supplied as a frozen out-of-fold cache.  R_psi is
       therefore shown as an offline producer, not an online inference call.
  C06  S_omega is POST-refinement / POST-composition, consuming 16 frozen
       post-candidate features + 4-D one-hot task, not the raw refined mask.
  C07  There are TWO skip states (FORCED_SKIP and SKIP_GLOBAL), not one.
  C08  Staged training is sequential and uses three different losses; there is
       no joint end-to-end objective and no "consistency/reliability" loss.
  C09  ReMedFiLM FULL = G + R_psi + B_phi + S_omega.  GlobalMedFiLM is only
       the backbone / ablation baseline, never the proposed model.

Outputs (all under full_doc_report/figures/, write-once)
--------------------------------------------------------
  ReMedFiLM_Methodology_V8.svg / .pdf / .png          main 3-panel figure
  ReMedFiLM_Methodology_GitHub_16x9.png / .svg        16:9 README variant
  ReMedFiLM_Methodology_Manuscript.svg / .pdf / .png  compact print variant
  REMEDFILM_V8_METHODOLOGY_ARROWS.json                 arrow provenance table

No model is trained, no inference is executed, no test split is opened.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import matplotlib.image as mpimg

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent))  # repository root

import matplotlib  # noqa: E402

matplotlib.use("Agg")

from v8_methodology import (  # noqa: E402  -- drawing primitives only
    SAMPLES, ROOT, STABLE_METADATA, Board, arrow, bbox_overlay, chip,
    diamond, elbow, img_tile, mask_tile, rect, rbox, roi_mask_tile, shield,
    txt, film_bars, step_bars, panel_header,
)
from v8_common import (  # noqa: E402
    FDR, FIG, NAVY, BLUE, BLUE_LIGHT, TEAL, TEAL_LIGHT, PURPLE, AMBER, RED,
    GREY, GREY_LIGHT, WHITE, write_artifact, write_json, sha256,
)

# --------------------------------------------------------------------------- #
# V8 design tokens (white ground, navy type; blue = G, teal = FULL)
# --------------------------------------------------------------------------- #
INK = NAVY
BODY = "#283B52"
EDGE_BLUE = "#5C93CF"
EDGE_TEAL = "#3AA79A"
EDGE_PURPLE = "#9B82C4"
EDGE_GREY = "#A9B5C2"
EDGE_AMBER = "#D9A24A"
PURPLE_LIGHT = "#F0EAF9"
AMBER_LIGHT = "#FBF1DE"
RED_LIGHT = "#FBE9E9"
GREEN = "#1E7A54"
GREEN_LIGHT = "#E3F2EA"
RULE = "#D5DEE8"
SERIF = "DejaVu Serif"
SANS = "DejaVu Sans"

# machine-local coordinate space
MW, MH = 1360.0, 600.0
COLS = [10.0, 235.0, 460.0, 685.0, 910.0, 1135.0]
CW = 205.0
R1, R2, R3, R4 = 445.0, 320.0, 195.0, 10.0
RH = 100.0

# main-figure placement: inner frame of Panel B is x=282..1648, y=312..868
MAIN_OX, MAIN_OY, MAIN_S = 339.0, 312.0, 0.92

# verified runtime constants -- imported, never retyped
from src.models.barr.ra_medfilm_barr import (  # noqa: E402
    TAU_C8_FINAL_FLOAT, ROI_PROPOSAL_THRESHOLD, ROI_EXPANSION,
    SOMEGA_ACCEPT_THRESHOLD, SEGMENTATION_OUTPUT_THRESHOLD,
    ROUTER_NUMERIC_DIM, ROUTER_TASK_EMBED_DIM, ROUTER_TOTAL_DIM,
    SOMEGA_NUMERIC_DIM, SOMEGA_TOTAL_DIM, STATES,
)
from src.models.film.global_medfilm import (  # noqa: E402
    GLOBAL_MEDFILM_TASK_EMBEDDING_DIM, GLOBAL_MEDFILM_FILM_SITES,
)
from src.models.barr.phase25_models import (  # noqa: E402
    ROUTER_EXPECTED_PARAMETERS, SAFETY_EXPECTED_PARAMETERS,
)

VAL808_STATES = {"FORCED_SKIP": 0, "SKIP_GLOBAL": 529,
                 "EXECUTE_THEN_ACCEPT": 266, "EXECUTE_THEN_REJECT": 13}
VAL808_N = 808
G_PARAMS, R_PARAMS = 3_523_001, 1_276_401
_SUP = str.maketrans("0123456789", "\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079")


def sup(n: int) -> str:
    return str(n).translate(_SUP)


# --------------------------------------------------------------------------- #
# scaled view: one drawing routine, three output geometries
# --------------------------------------------------------------------------- #
class View:
    """Map machine-local coordinates onto a Board at an arbitrary scale."""

    def __init__(self, board: Board, ox: float, oy: float, s: float = 1.0):
        self.b, self.ox, self.oy, self.s = board, ox, oy, s

    def p(self, x, y):
        return (self.ox + x * self.s, self.oy + y * self.s)

    def box(self, x, y, w, h, fc, ec, lw=1.2, r=10, z=3, ls=None):
        X, Y = self.p(x, y)
        return rbox(self.b, X, Y, w * self.s, h * self.s, fc, ec,
                    lw=lw * self.s, r=r * self.s, z=z)

    def fill(self, x, y, w, h, fc, ec="none", lw=0.0, z=2):
        X, Y = self.p(x, y)
        return rect(self.b, X, Y, w * self.s, h * self.s, fc, ec,
                    lw * self.s, z)

    def text(self, x, y, s, size=8.0, color=INK, weight="normal", ha="center",
             va="center", style="normal", family=SANS, z=8, rot=0):
        X, Y = self.p(x, y)
        return txt(self.b, X, Y, s, size=size * self.s, color=color,
                   weight=weight, ha=ha, va=va, style=style, family=family,
                   z=z, rot=rot)

    def arrow(self, p0, p1, color=INK, lw=1.3, ls="-", z=6, head=7.0, rad=0.0):
        return arrow(self.b, self.p(*p0), self.p(*p1), color=color,
                     lw=lw * self.s, ls=ls, z=z, head=head * self.s, rad=rad)

    def elbow(self, pts, color=INK, lw=1.3, ls="-", z=6, head=7.0):
        return elbow(self.b, [self.p(*q) for q in pts], color=color,
                     lw=lw * self.s, ls=ls, z=z, head=head * self.s)

    def diamond(self, cx, cy, w, h, fc, ec, label, fs=8.4, z=7):
        X, Y = self.p(cx, cy)
        return diamond(self.b, X, Y, w * self.s, h * self.s, fc, ec, label,
                       fs=fs * self.s, z=z)

    def img(self, x, y, w, h, path, ec=RULE, lw=1.0, z=5):
        X, Y = self.p(x, y)
        return img_tile(self.b, X, Y, w * self.s, h * self.s, path,
                        ec=ec, lw=lw * self.s, z=z)

    def mask(self, x, y, w, h, path, ec="#1A1A1A", lw=1.0, z=5):
        X, Y = self.p(x, y)
        W, H = w * self.s, h * self.s
        rgba = _opaque_mask_rgba(Path(path))
        self.b.ax.imshow(rgba, extent=(X, X + W, Y, Y + H), aspect="auto",
                         interpolation="nearest", zorder=z)
        return rect(self.b, X, Y, W, H, "none", ec, lw * self.s, z + 1)

    def roi(self, x, y, w, h, key="ISIC", ec="#1A1A1A", lw=1.0, z=5):
        X, Y = self.p(x, y)
        W, H = w * self.s, h * self.s
        rgba = _opaque_mask_rgba(
            SAMPLES / key / "04_global_probability.png", roi_key=key)
        self.b.ax.imshow(rgba, extent=(X, X + W, Y, Y + H), aspect="auto",
                         interpolation="nearest", zorder=z)
        return rect(self.b, X, Y, W, H, "none", ec, lw * self.s, z + 1)

    def bbox(self, x, y, w, h, key="ISIC", color=RED, lw=1.8, z=7):
        X, Y = self.p(x, y)
        return bbox_overlay(self.b, X, Y, w * self.s, h * self.s, key=key,
                            color=color, lw=lw * self.s, z=z)


def _opaque_mask_rgba(path: Path, roi_key: str | None = None,
                      thresh: float = 0.45) -> np.ndarray:
    """White foreground on an OPAQUE black ground.

    The V5-V7 helper left the background fully transparent, so on a white
    canvas the mask rendered as an empty framed square (a real visual defect
    inherited by earlier reports).  V8 composites explicitly instead.
    """
    try:
        arr = np.asarray(mpimg.imread(path))
        if arr.ndim == 3:
            arr = arr[..., :3].mean(axis=2)
        arr = arr.astype(float)
        if roi_key is not None:
            meta = json.loads((SAMPLES / roi_key / "sample_metadata.json").read_text())
            y0, x0, y1, x1 = meta["05_roi_proposal"]["roi_box"]
            arr = arr[max(y0, 0):max(y1, 0), max(x0, 0):max(x1, 0)]
        if arr.size == 0:
            raise ValueError("empty crop")
        if arr.max() > 1e-6:
            arr = arr / arr.max()
        rgba = np.zeros((arr.shape[0], arr.shape[1], 4), dtype=float)
        rgba[..., 3] = 1.0                       # opaque black background
        rgba[arr > thresh, :3] = 1.0            # opaque white foreground
        return rgba
    except Exception:
        out = np.zeros((8, 8, 4), dtype=float)
        out[..., 3] = 1.0
        return out


def node(v: View, col: int, row_y: float, *, title: str, lines: list[str],
         fc: str, ec: str, tc: str, h: float = RH, w: float = CW,
         fs: float = 8.6, lfs: float = 7.2, dashed: bool = False) -> tuple:
    """Draw a titled module card.  Returns (left, right, mid_y) in local units."""
    x = COLS[col]
    v.box(x, row_y, w, h, fc, ec, lw=1.3 if not dashed else 1.2, r=9, z=3)
    v.fill(x + 2, row_y + h - 26, w - 4, 24, fc, z=4)
    v.text(x + w / 2, row_y + h - 14, title, size=fs, color=tc,
           weight="bold", z=6)
    n = len(lines)
    top = row_y + h - 38
    step = min(13.5, (h - 46) / max(n, 1))
    for i, ln in enumerate(lines):
        v.text(x + w / 2, top - i * step, ln, size=lfs, color=BODY, z=6)
    return (x, x + w, row_y + h / 2)


def small_tile(v: View, x: float, y: float, kind: str, key="ISIC",
               w: float = 54, h: float = 54):
    if kind == "input":
        v.img(x, y, w, h, SAMPLES / key / "01_input.png")
    elif kind == "global":
        v.mask(x, y, w, h, SAMPLES / key / "04_global_probability.png")
    elif kind == "roi":
        v.roi(x, y, w, h, key=key)
    elif kind == "final":
        v.mask(x, y, w, h, SAMPLES / key / "07_final_segmentation.png")


# --------------------------------------------------------------------------- #
# the verified inference state machine (drawn once, reused at three scales)
# --------------------------------------------------------------------------- #
def draw_machine(v: View, show_tiles: bool = True) -> None:
    # identity ribbon -------------------------------------------------------
    v.box(10, 560, 1340, 34, NAVY, NAVY, lw=0.8, r=9, z=3)
    v.text(680, 577,
           "ReMedFiLM FULL  =  G + R\u03c8 + B\u03c6 + S\u03c9     \u00b7     "
           "frozen modular assembly, 0 joint parameters, 0 joint backward graph",
           size=9.4, color=WHITE, weight="bold", z=7)

    # ======================= ROW 1 : global stage ========================= #
    v.text(COLS[0] + CW / 2, R1 + RH + 12, "Input", size=7.6, color=GREY,
           weight="bold", z=6)
    if show_tiles:
        v.img(COLS[0] + 20, R1 + 12, 62, 62, SAMPLES / "ISIC" / "01_input.png")
        v.text(COLS[0] + CW - 26, R1 + 62, "x", size=10.4, color=INK,
               weight="bold", style="italic", z=6)
        v.text(COLS[0] + CW - 26, R1 + 40, "t", size=9.4, color=PURPLE,
               weight="bold", style="italic", z=6)
    else:
        v.text(COLS[0] + CW / 2, R1 + RH / 2, "image x\n+ task id t",
               size=9.0, color=INK, weight="bold", z=6)

    node(v, 1, R1, title="G \u00b7 GlobalMedFiLM", fc=BLUE_LIGHT, ec=EDGE_BLUE,
         tc=BLUE, lines=[
             "Task-conditioned backbone",
             f"E(t) \u2208 R{sup(GLOBAL_MEDFILM_TASK_EMBEDDING_DIM)} \u2192 \u03b3, \u03b2",
             "F\u0302 = (1+\u03b3(t))\u00b7F + \u03b2(t)",
             f"{len(GLOBAL_MEDFILM_FILM_SITES)} FiLM sites \u00b7 {G_PARAMS:,} params",
         ], fs=8.4, lfs=6.9)

    if show_tiles:
        small_tile(v, COLS[2] + 14, R1 + 20, "global", w=56, h=56)
    v.text(COLS[2] + CW - 24, R1 + 74, "p_global", size=8.2, color=INK,
           weight="bold", style="italic", z=6)
    v.text(COLS[2] + CW - 24, R1 + 56, "G(x,t)", size=7.2, color=GREY, z=6)
    v.text(COLS[2] + CW / 2, R1 + 7, "exactly one G forward", size=6.8,
           color=GREY, z=6)

    node(v, 3, R1, title="GT-free ROI window", fc=PURPLE_LIGHT, ec=EDGE_PURPLE,
         tc=PURPLE, lines=[
             f"p_global \u2265 {ROI_PROPOSAL_THRESHOLD:.2f} \u2192 bbox",
             f"\u00d7{ROI_EXPANSION:.2f} centre-preserving expansion",
             "window (y0,y1,x0,x1)",
             "no ground-truth mask used",
         ], fs=8.4, lfs=6.9)
    # NOTE: no sample tile is drawn inside this card.  In V5-V7 the tile
    # overlapped the two lower text lines; the four verified statements are
    # more informative than a decorative thumbnail.
    v.diamond(COLS[4] + CW / 2, R1 + 50, 150, 74, WHITE, EDGE_BLUE,
              "action\navailable?", fs=8.2, z=7)
    v.text(COLS[4] + CW / 2, R1 + 8, "window is None \u2192 no", size=6.8,
           color=GREY, z=6)

    v.box(COLS[5], R1 + 8, CW, 84, BLUE_LIGHT, EDGE_BLUE, lw=1.2, r=9, z=3)
    v.text(COLS[5] + CW / 2, R1 + 72, "FORCED_SKIP", size=9.2, color=BLUE,
           weight="bold", z=6)
    v.text(COLS[5] + CW / 2, R1 + 52, "P_out = p_global", size=8.0,
           color=BODY, z=6)
    v.text(COLS[5] + CW / 2, R1 + 32, "no ROI above 0.30", size=7.0,
           color=GREY, z=6)
    v.text(COLS[5] + CW / 2, R1 + 18, "0 / 808 on VAL808", size=7.0,
           color=BLUE, weight="bold", z=6)

    for c in range(4):
        a = COLS[c] + CW + 4
        b = COLS[c + 1] - 4
        y = R1 + 50
        v.arrow((a, y), (b, y), color=INK if c < 3 else EDGE_BLUE, lw=1.4, z=6)
    v.arrow((COLS[4] + CW / 2 + 75, R1 + 50), (COLS[5] - 4, R1 + 50),
            color=BLUE, lw=1.5, z=6)
    v.text(COLS[4] + CW + 10, R1 + 62, "no", size=7.0, color=BLUE,
           weight="bold", z=7)
    v.text(COLS[4] + CW / 2 + 34, R1 + 96, "yes \u2193", size=7.0,
           color=TEAL, weight="bold", z=7)

    # ======================= ROW 2 : benefit router ======================= #
    v.text(COLS[0] + CW / 2, R2 + RH + 12, "Frozen pre-refinement inputs",
           size=7.6, color=GREY, weight="bold", z=6)
    node(v, 0, R2, title="202-D GT-free features", fc=GREY_LIGHT, ec=EDGE_GREY,
         tc=GREY, dashed=True, lines=[
             "Phase25B frozen cache",
             "supplied to the wrapper",
             "NOT a readout of G features",
             "no ground truth at inference",
         ], fs=8.0, lfs=6.9)
    node(v, 1, R2, title="task id t \u2192 embedding", fc=PURPLE_LIGHT,
         ec=EDGE_PURPLE, tc=PURPLE, lines=[
             f"B\u03c6's OWN {ROUTER_TASK_EMBED_DIM}-D embedding",
             f"{ROUTER_NUMERIC_DIM} + {ROUTER_TASK_EMBED_DIM} = {ROUTER_TOTAL_DIM}-D input",
             "separate from G's 32-D E(t)",
         ], fs=8.0, lfs=6.9)
    node(v, 2, R2, title="B\u03c6 \u00b7 Benefit Router", fc=TEAL_LIGHT,
         ec=EDGE_TEAL, tc=TEAL, lines=[
             "BARRBenefitRouterV1",
             "\u03b4\u0302 = B\u03c6(f\u2082\u2080\u2082, t)",
             f"{ROUTER_EXPECTED_PARAMETERS:,} params",
             "trained: HuberLoss(\u0394=0.05)",
         ], fs=8.4, lfs=6.9)
    node(v, 3, R2, title="Resource-aware utility", fc=WHITE, ec=EDGE_GREY,
         tc=INK, lines=[
             "U = \u03b4\u0302_final \u2212 \u03bb\u00b7C",
             "\u03bb = 1/4 \u00b7 C = 1051648/10270749",
             f"\u03c4_C8 = {TAU_C8_FINAL_FLOAT:.7f}",
             "frozen decision threshold",
         ], fs=8.4, lfs=6.7)
    v.diamond(COLS[4] + CW / 2, R2 + 50, 150, 74, WHITE, EDGE_TEAL,
              "U \u2265 \u03c4_C8 ?", fs=8.4, z=7)
    v.box(COLS[5], R2 + 8, CW, 84, BLUE_LIGHT, EDGE_BLUE, lw=1.2, r=9, z=3)
    v.text(COLS[5] + CW / 2, R2 + 72, "SKIP_GLOBAL", size=9.2, color=BLUE,
           weight="bold", z=6)
    v.text(COLS[5] + CW / 2, R2 + 52, "P_out = p_global", size=8.0,
           color=BODY, z=6)
    v.text(COLS[5] + CW / 2, R2 + 32, "R\u03c8 and S\u03c9 not invoked", size=7.0,
           color=GREY, z=6)
    v.text(COLS[5] + CW / 2, R2 + 18, "529 / 808 on VAL808", size=7.0,
           color=BLUE, weight="bold", z=6)

    # route the frozen-cache arrow through the column gaps, never through a card
    v.elbow([(COLS[0] + CW, R2 + 50), (COLS[0] + CW + 12, R2 + 50),
             (COLS[0] + CW + 12, R2 + RH + 14), (COLS[2] - 14, R2 + RH + 14),
             (COLS[2] - 14, R2 + 70), (COLS[2], R2 + 70)],
            color=EDGE_GREY, lw=1.3, ls=(0, (3, 2)), z=6)
    v.arrow((COLS[1] + CW, R2 + 50), (COLS[2], R2 + 50), color=PURPLE,
            lw=1.3, z=6)
    v.arrow((COLS[2] + CW, R2 + 50), (COLS[3], R2 + 50), color=TEAL,
            lw=1.4, z=6)
    v.arrow((COLS[3] + CW, R2 + 50), (COLS[4] + CW / 2 - 75, R2 + 50),
            color=INK, lw=1.4, z=6)
    v.arrow((COLS[4] + CW / 2 + 75, R2 + 50), (COLS[5], R2 + 50),
            color=BLUE, lw=1.5, z=6)
    v.text(COLS[4] + CW - 16, R2 + 62, "no", size=7.0, color=BLUE,
           weight="bold", z=7)
    v.text(COLS[4] + CW / 2 - 20, R2 + 96, "yes (EXECUTE) \u2193", size=7.0,
           color=TEAL, weight="bold", z=7)

    # ======================= ROW 3 : execute + safety ===================== #
    v.text(COLS[0] + CW / 2, R3 + RH + 12, "Offline OOF producer \u2192 frozen cache",
           size=7.6, color=GREY, weight="bold", z=6)
    node(v, 0, R3, title="R\u03c8 \u00b7 Regional Refiner", fc=PURPLE_LIGHT,
         ec=EDGE_PURPLE, tc=PURPLE, lines=[
             "BARRRegionalRefinerV1",
             "4-ch [RGB, p_global crop]",
             f"{R_PARAMS:,} params \u00b7 raw logits",
             "0.5\u00b7BCE + 0.5\u00b7soft Dice",
         ], fs=8.4, lfs=6.9)
    node(v, 1, R3, title="p_refine (OOF cache)", fc=GREY_LIGHT, ec=EDGE_GREY,
         tc=GREY, dashed=True, lines=[
             "256\u00d7256 refined probability",
             "frozen out-of-fold cache",
             "wrapper registers R\u03c8 but",
             "does NOT call it at runtime",
         ], fs=8.0, lfs=6.8)
    node(v, 2, R3, title="Deterministic ROI fusion", fc=GREEN_LIGHT,
         ec=GREEN, tc=GREEN, lines=[
             "inside ROI \u2190 p_refine",
             "outside ROI \u2190 p_global",
             "replacement, NO alpha blend",
             "NO addition / learned fusion",
         ], fs=8.2, lfs=6.8)
    if show_tiles:
        small_tile(v, COLS[3] + 16, R3 + 24, "final", w=56, h=50)
    v.text(COLS[3] + CW - 22, R3 + 72, "P_cand", size=8.4, color=INK,
           weight="bold", style="italic", z=6)
    v.text(COLS[3] + CW - 22, R3 + 54, "composed", size=7.0, color=GREY, z=6)
    v.text(COLS[3] + CW - 22, R3 + 40, "candidate", size=7.0, color=GREY, z=6)
    v.text(COLS[3] + CW / 2, R3 + 8, "fused probability map", size=6.8,
           color=GREY, z=6)
    node(v, 4, R3, title="Post-candidate features", fc=GREY_LIGHT,
         ec=EDGE_GREY, tc=GREY, dashed=True, lines=[
             f"{SOMEGA_NUMERIC_DIM}-D Phase25F frozen cache",
             "+ 4-D one-hot task t",
             f"= {SOMEGA_TOTAL_DIM}-D S\u03c9 input",
             "derived from P_cand offline",
         ], fs=8.0, lfs=6.8)
    node(v, 5, R3, title="S\u03c9 \u00b7 Post-Safety Gate", fc=TEAL_LIGHT,
         ec=EDGE_TEAL, tc=TEAL, lines=[
             "BARRPostSafetyV1",
             "logit \u2192 a = sigmoid(logit)",
             f"{SAFETY_EXPECTED_PARAMETERS:,} params",
             "trained: BCEWithLogitsLoss",
         ], fs=8.4, lfs=6.9)

    for c in range(5):
        v.arrow((COLS[c] + CW + 3, R3 + 50), (COLS[c + 1] - 3, R3 + 50),
                color=GREEN if c in (1, 2) else (EDGE_GREY if c in (0, 3) else INK),
                lw=1.35, ls=(0, (3, 2)) if c == 0 else "-", z=6)
    # p_global also feeds the fusion (verified: out = p_global.copy()).
    # Both long feedback arrows are routed exclusively through column gaps.
    gap_x = COLS[2] - 16           # 444, between C1 (ends 440) and C2 (starts 460)
    v.elbow([(COLS[2] + 14, R1 + 20), (COLS[2] + 14, R1 - 6),
             (gap_x, R1 - 6), (gap_x, R3 + RH + 16),
             (COLS[2] + 24, R3 + RH + 16), (COLS[2] + 24, R3 + RH)],
            color=BLUE, lw=1.2, ls=(0, (4, 3)), z=5)
    # the two long dashed arrows are colour-keyed (blue = p_global reused at
    # fusion, purple = frozen ROI window geometry); they are explained in the
    # legend rather than carrying tiny labels that the arrows strike through.
    # ROI window geometry feeds the fusion
    gap2 = COLS[3] - 16            # 669, between C2 (ends 665) and C3 (starts 685)
    v.elbow([(COLS[3] + CW / 2, R1 + 4), (COLS[3] + CW / 2, R1 - 12),
             (gap2, R1 - 12), (gap2, R3 + RH + 6),
             (COLS[2] + CW - 26, R3 + RH + 6), (COLS[2] + CW - 26, R3 + RH)],
            color=PURPLE, lw=1.1, ls=(0, (4, 3)), z=5)

    # ======================= decision strip ============================== #
    v.diamond(COLS[5] + CW / 2, 155, 168, 64, TEAL_LIGHT, EDGE_TEAL,
              f"a \u2265 {SOMEGA_ACCEPT_THRESHOLD:.2f} ?", fs=8.6, z=7)
    v.arrow((COLS[5] + CW / 2, R3), (COLS[5] + CW / 2, 187), color=TEAL,
            lw=1.4, z=6)
    v.text(COLS[5] + CW / 2 - 62, 155, "no", size=7.0, color=AMBER,
           weight="bold", z=7)
    v.text(COLS[5] + CW / 2 + 62, 169, "yes", size=7.0, color=TEAL,
           weight="bold", z=7)

    # ======================= ROW 4 : four canonical states =============== #
    states = [
        ("FORCED_SKIP", "P_out = p_global", "action unavailable", BLUE, BLUE_LIGHT, EDGE_BLUE),
        ("SKIP_GLOBAL", "P_out = p_global", "U < \u03c4_C8", BLUE, BLUE_LIGHT, EDGE_BLUE),
        ("EXECUTE_THEN_ACCEPT", "P_out = P_cand", "a \u2265 0.50", TEAL, TEAL_LIGHT, EDGE_TEAL),
        ("EXECUTE_THEN_REJECT", "P_out = p_global", "a < 0.50", AMBER, AMBER_LIGHT, EDGE_AMBER),
    ]
    sw = 326.0
    for i, (name, out, cond, col, soft, edge) in enumerate(states):
        x = 10 + i * (sw + 12)
        v.box(x, R4, sw, 100, soft, edge, lw=1.2, r=9, z=3)
        v.fill(x + 2, R4 + 76, sw - 4, 22, soft, z=4)
        v.text(x + sw / 2, R4 + 87, name, size=8.6, color=col,
               weight="bold", z=6)
        v.text(x + sw / 2, R4 + 60, out, size=8.0, color=BODY,
               weight="bold", z=6)
        v.text(x + sw / 2, R4 + 42, cond, size=7.2, color=GREY, z=6)
        v.text(x + sw / 2, R4 + 25,
               f"{VAL808_STATES[name]:>3d} / {VAL808_N} VAL808 images",
               size=7.4, color=col, weight="bold", z=6)
        v.text(x + sw / 2, R4 + 10,
               f"P\u0302 = 1[P_out \u2265 {SEGMENTATION_OUTPUT_THRESHOLD:.2f}]",
               size=6.8, color=GREY, z=6)
    v.elbow([(COLS[5] + CW / 2 - 84, 155), (COLS[5] - 60, 155),
             (COLS[5] - 60, 120), (10 + 2 * (sw + 12) + sw / 2, 120),
             (10 + 2 * (sw + 12) + sw / 2, R4 + 100)],
            color=TEAL, lw=1.4, z=6)
    v.elbow([(COLS[5] + CW / 2 + 84, 155), (COLS[5] + CW + 26, 155),
             (COLS[5] + CW + 26, 120), (10 + 3 * (sw + 12) + sw / 2, 120),
             (10 + 3 * (sw + 12) + sw / 2, R4 + 100)],
            color=AMBER, lw=1.4, z=6)


# --------------------------------------------------------------------------- #
# Panel A : multi-domain inputs and the THREE distinct task representations
# --------------------------------------------------------------------------- #
def panel_a_v8(b: Board) -> dict:
    X, Y, W, H = 10, 300, 250, 630
    panel_header(b, X, Y, W, H, "A", "", edge=EDGE_PURPLE, head=PURPLE_LIGHT,
                 tfs=10.4, two_line=("Multi-domain inputs and",
                                     "task conditioning"))
    rows = [("ISIC 2018", "(Dermoscopy)", "ISIC"),
            ("BUSI-WHU", "(Breast US)", "BUSI"),
            ("Kvasir-SEG", "(Endoscopy)", "KVASIR"),
            ("KUB-StoneX", "(KUB X-ray)", "KUB")]
    top = Y + H - 56          # 874
    row_h, gap = 58, 7
    lx, lw_ = X + 12, W - 24
    for i, (name, mod, key) in enumerate(rows):
        ry = top - (i + 1) * row_h - i * gap
        rbox(b, lx, ry, lw_, row_h, WHITE, "#C9D2DE", lw=1.0, r=9, z=2)
        img_tile(b, lx + 7, ry + 6, 46, row_h - 12,
                 SAMPLES / key / "01_input.png", ec="#C9CED8", lw=0.9, z=3)
        txt(b, lx + 60, ry + row_h * 0.64, name, size=8.4, color=INK,
            weight="bold", ha="left", z=6)
        txt(b, lx + 60, ry + row_h * 0.31, mod, size=7.2, color=GREY,
            ha="left", z=6)

    # convergence bracket -> task identity
    last_bottom = top - 4 * row_h - 3 * gap    # 621
    elbow(b, [(X + W - 10, top - row_h / 2), (X + W - 18, top - row_h / 2),
              (X + W - 18, last_bottom - 18), (X + 26, last_bottom - 18),
              (X + 26, last_bottom - 21)],
          color=INK, lw=1.2, z=5)

    # task identity node
    ty = 552
    rbox(b, X + 12, ty, W - 24, 44, PURPLE_LIGHT, EDGE_PURPLE, lw=1.3, r=9, z=4)
    txt(b, X + W / 2, ty + 30, "Task identity  t \u2208 {0,1,2,3}", size=8.4,
        color=PURPLE, weight="bold", z=6)
    txt(b, X + W / 2, ty + 13, "known domain label, GT-free", size=7.0,
        color=GREY, z=6)

    # three DISTINCT task representations (V8 correction C01)
    reps = [
        ("E(t) \u2208 R\u00b3\u00b2", "G FiLM \u03b3,\u03b2", BLUE, BLUE_LIGHT, EDGE_BLUE),
        ("emb\u03c6(t) \u2208 R\u00b9\u2076", "B\u03c6 input", TEAL, TEAL_LIGHT, EDGE_TEAL),
        ("onehot(t) \u2208 R\u2074", "S\u03c9 input", PURPLE, PURPLE_LIGHT, EDGE_PURPLE),
    ]
    for k, (lab, dest, col, soft, edge) in enumerate(reps):
        ry = 498 - k * 52
        rbox(b, X + 12, ry, W - 24, 44, soft, edge, lw=1.2, r=8, z=4)
        txt(b, X + 22, ry + 29, lab, size=8.2, color=col, weight="bold",
            ha="left", z=6)
        txt(b, X + 22, ry + 13, dest, size=7.0, color=GREY, ha="left", z=6)
        arrow(b, (X + W - 12, ry + 22), (X + W + 8, ry + 22), color=col,
              lw=1.4, z=6, head=6.0)
    txt(b, X + W / 2, 380, "three separate encodings \u2192 Panel B",
        size=6.8, color=GREY, style="italic", z=6)

    rbox(b, X + 12, Y + 12, W - 24, 64, GREY_LIGHT, EDGE_GREY, lw=1.0,
         r=8, z=3)
    txt(b, X + W / 2, Y + 60, "Frozen split protocol", size=7.6, color=INK,
        weight="bold", z=6)
    txt(b, X + W / 2, Y + 44, "TRAIN 5,832 \u00b7 VAL 808", size=7.2,
        color=BODY, z=6)
    txt(b, X + W / 2, Y + 29, "TEST 1,683 (protected;", size=7.2,
        color=BODY, z=6)
    txt(b, X + W / 2, Y + 16, "not opened for V8)", size=7.0, color=RED,
        weight="bold", z=6)
    return None


# --------------------------------------------------------------------------- #
# Panel C : verified sequential staged training
# --------------------------------------------------------------------------- #
STEPS = [
    ("1", "Train G", "Task-conditioned\nGlobalMedFiLM on\nTRAIN 5,832.",
     "supervised\nsegmentation", BLUE, BLUE_LIGHT, EDGE_BLUE),
    ("2", "Freeze G;\nbuild caches", "Global predictions,\nROI crops and OOF\nfeature caches.",
     "no joint\nbackward graph", PURPLE, PURPLE_LIGHT, EDGE_PURPLE),
    ("3", "Train R\u03c8", "4-channel ROI crop\nrefiner, logits \u2192\np_refine.",
     "0.5\u00b7BCE +\n0.5\u00b7soft Dice", PURPLE, PURPLE_LIGHT, EDGE_PURPLE),
    ("4", "Paired gain\nlabels", "\u03b4 = Dice(P_cand)\n\u2212 Dice(p_global);\nOOF, cross-fitted.",
     "\u03b4 \u2208 [\u22121, 1]", GREY, GREY_LIGHT, EDGE_GREY),
    ("5", "Train B\u03c6", "Regress \u03b4 from 202-D\nGT-free features +\n16-D task embedding.",
     "HuberLoss\n(\u0394 = 0.05)", TEAL, TEAL_LIGHT, EDGE_TEAL),
    ("6", "Train S\u03c9", "Binary target from\nsign(\u03b4) on 16-D post\nfeatures + one-hot t.",
     "BCEWith-\nLogitsLoss", TEAL, TEAL_LIGHT, EDGE_TEAL),
]


def panel_c_v8(b: Board, X=10, Y=10, W=1046, H=278, s=1.0) -> None:
    panel_header(b, X, Y, W, H, "C", "Sequential staged training (no joint end-to-end optimisation)",
                 edge=EDGE_BLUE, head=BLUE_LIGHT, tfs=10.8 * s)
    txt(b, X + W - 14 * s, Y + H - 14 * s,
        "each stage consumes the frozen outputs of its predecessors",
        size=7.4 * s, color=GREY, style="italic", ha="right", z=6)
    sx, sy = X + 12 * s, Y + 44 * s
    sh = H - 44 * s - 12 * s
    sw = (W - 24 * s - 5 * 8 * s) / 6.0
    for i, (num, title, body, loss, col, soft, edge) in enumerate(STEPS):
        cx = sx + i * (sw + 8 * s)
        rbox(b, cx, sy, sw, sh, WHITE, edge, lw=1.15 * s, r=8 * s, z=3)
        rect(b, cx + 2 * s, sy + sh - 42 * s, sw - 4 * s, 40 * s, soft, z=4)
        b.ax.add_patch(plt_circle((cx + 18 * s, sy + sh - 21 * s), 10 * s,
                                  facecolor=col, edgecolor="none", zorder=6))
        txt(b, cx + 18 * s, sy + sh - 21 * s, num, size=8.6 * s,
            color=WHITE, weight="bold", z=7)
        txt(b, cx + 33 * s, sy + sh - 21 * s, title, size=7.8 * s, color=col,
            weight="bold", ha="left", z=7, lsp=1.05)
        txt(b, cx + sw / 2, sy + sh - 62 * s, body, size=6.9 * s, color=BODY,
            z=7, lsp=1.22)
        rbox(b, cx + 8 * s, sy + 8 * s, sw - 16 * s, 30 * s, soft, edge,
             lw=0.9 * s, r=6 * s, z=5)
        txt(b, cx + sw / 2, sy + 23 * s, loss, size=6.9 * s, color=col,
            weight="bold", z=7, lsp=1.1)
        if i < 5:
            arrow(b, (cx + sw, sy + sh * 0.52), (cx + sw + 8 * s, sy + sh * 0.52),
                  color=INK, lw=1.1 * s, ls=(0, (3, 2)), z=6, head=4.5 * s)


def plt_circle(xy, radius, **kw):
    import matplotlib.pyplot as plt
    return plt.Circle(xy, radius, **kw)


def legend_v8(b: Board, X=1066, Y=10, W=596, H=278, s=1.0) -> None:
    rbox(b, X, Y, W, H, WHITE, EDGE_BLUE, lw=1.4 * s, r=10 * s, z=1)
    rect(b, X + 2 * s, Y + H - 26 * s, W - 4 * s, 24 * s, BLUE_LIGHT, z=2)
    txt(b, X + 14 * s, Y + H - 14 * s, "Verification key and caveats",
        size=10.4 * s, color=NAVY, weight="bold", ha="left", z=6,
        family=SERIF)
    entries = [
        (BLUE_LIGHT, EDGE_BLUE, "G / GlobalMedFiLM \u2014 backbone and ablation baseline"),
        (TEAL_LIGHT, EDGE_TEAL, "B\u03c6, S\u03c9 \u2014 ReMedFiLM FULL decision modules"),
        (PURPLE_LIGHT, EDGE_PURPLE, "R\u03c8, ROI geometry, task conditioning"),
        (GREY_LIGHT, EDGE_GREY, "Frozen cache supplied to the wrapper (dashed)"),
        (GREEN_LIGHT, GREEN, "Deterministic ROI replacement (no blending)"),
    ]
    ry = Y + H - 42 * s
    for fc, ec, lab in entries:
        rbox(b, X + 14 * s, ry - 8 * s, 34 * s, 17 * s, fc, ec,
             lw=1.0 * s, r=4 * s, z=5)
        txt(b, X + 56 * s, ry, lab, size=7.4 * s, color=BODY, ha="left", z=6)
        ry -= 24 * s
    ry -= 4 * s
    notes = [
        "Canonical assembly: RAMedFiLMBARR.forward_inference().",
        "Dashed blue / purple: p_global and ROI window reused at fusion.",
        "B\u03c6 runs PRE-refinement; S\u03c9 runs POST-composition.",
        "The wrapper does not invoke R\u03c8; p_refine is an OOF cache.",
        "OOF boundary: R\u03c8 / B\u03c6 / S\u03c9 OOF=TRUE; backbone OOF=FALSE.",
        "No ground truth, diagnosis label or joint loss at inference.",
        "VAL808 state counts: 0 / 529 / 266 / 13 = 808 images.",
        "C1, C2, C3 controlled comparisons: NOT_ESTABLISHED.",
    ]
    for note in notes:
        txt(b, X + 14 * s, ry, "\u2022  " + note, size=7.0 * s,
            color=GREY, ha="left", z=6)
        ry -= 15 * s


# --------------------------------------------------------------------------- #
# three output geometries
# --------------------------------------------------------------------------- #
def build_full_v8() -> Board:
    b = Board(1672, 941)
    rbox(b, 268, 300, 1394, 630, WHITE, EDGE_BLUE, lw=1.5, r=11, z=1)
    rect(b, 270, 891, 1390, 37, BLUE_LIGHT, z=2)
    txt(b, 292, 909, "B", size=12.0, color=WHITE, weight="bold", z=6)
    b.ax.add_patch(plt_circle((292, 909), 13, facecolor=BLUE,
                              edgecolor="none", zorder=5))
    txt(b, 316, 909,
        "ReMedFiLM FULL \u2014 verified inference state machine (RA-MedFiLM-BARR)",
        size=12.4, color=NAVY, weight="bold", ha="left", z=6, family=SERIF)
    txt(b, 1646, 909, "G is the backbone only", size=8.0, color=BLUE,
        weight="bold", style="italic", ha="right", z=6)
    panel_a_v8(b)
    v = View(b, MAIN_OX, MAIN_OY, s=MAIN_S)
    draw_machine(v, show_tiles=True)
    panel_c_v8(b)
    legend_v8(b)
    return b


def build_github_v8() -> Board:
    """Exact 1600x900 (16:9) README variant: larger type, no sample tiles."""
    b = Board(1600, 900)
    rect(b, 8, 852, 1584, 42, BLUE_LIGHT, z=2)
    txt(b, 26, 873,
        "ReMedFiLM FULL  =  G + R\u03c8 + B\u03c6 + S\u03c9    \u2014    "
        "code-verified inference state machine",
        size=13.4, color=NAVY, weight="bold", ha="left", z=6, family=SERIF)
    txt(b, 1574, 873, "G = backbone only", size=8.6, color=BLUE,
        weight="bold", style="italic", ha="right", z=6)
    # machine occupies y=160..841 (681 px tall at scale 1.135)
    v = View(b, 20, 160, s=1.135)
    draw_machine(v, show_tiles=False)
    # compact bottom strip: staged training, one card per stage
    rbox(b, 8, 8, 1584, 142, WHITE, EDGE_BLUE, lw=1.2, r=8, z=1)
    rect(b, 10, 120, 1580, 28, BLUE_LIGHT, z=2)
    txt(b, 24, 134, "C   Sequential staged training \u2014 no joint end-to-end optimisation",
        size=10.6, color=NAVY, weight="bold", ha="left", z=6, family=SERIF)
    txt(b, 1574, 134, "G \u2192 R\u03c8 \u2192 B\u03c6 \u2192 S\u03c9", size=9.0,
        color=BLUE, weight="bold", style="italic", ha="right", z=6)
    sw = (1584 - 2 * 16 - 5 * 10) / 6.0
    for i, (num, title, body, loss, col, soft, edge) in enumerate(STEPS):
        x = 16 + i * (sw + 10)
        rbox(b, x, 16, sw, 98, WHITE, edge, lw=1.1, r=7, z=3)
        rect(b, x + 2, 88, sw - 4, 24, soft, z=4)
        b.ax.add_patch(plt_circle((x + 17, 100), 9, facecolor=col,
                                  edgecolor="none", zorder=6))
        txt(b, x + 17, 100, num, size=9.0, color=WHITE, weight="bold", z=7)
        txt(b, x + 32, 100, title, size=8.2, color=col, weight="bold",
            ha="left", z=7)
        txt(b, x + sw / 2, 66, body, size=7.0, color=BODY, z=7, lsp=1.18)
        rbox(b, x + 8, 22, sw - 16, 26, soft, edge, lw=0.9, r=5, z=5)
        txt(b, x + sw / 2, 35, loss, size=7.2, color=col, weight="bold", z=7,
            lsp=1.05)
        if i < 5:
            arrow(b, (x + sw, 62), (x + sw + 10, 62), color=INK, lw=1.1,
                  ls=(0, (3, 2)), z=6, head=5.0)
    return b


def build_manuscript_v8() -> Board:
    """Print-oriented single-column figure (1000 x 1360)."""
    b = Board(1000, 1360)
    txt(b, 500, 1324, "ReMedFiLM FULL \u2014 verified four-state inference system",
        size=15.0, color=NAVY, weight="bold", family=SERIF, z=6)
    txt(b, 500, 1302,
        "G + R\u03c8 + B\u03c6 + S\u03c9 \u00b7 frozen modular assembly \u00b7 no joint optimisation",
        size=9.4, color=GREY, z=6)
    # machine scaled to 0.71, placed upper
    v = View(b, 18, 800, s=0.71)
    draw_machine(v, show_tiles=False)
    # staged training strip below
    txt(b, 500, 748, "Sequential staged training", size=12.6, color=NAVY,
        weight="bold", family=SERIF, z=6)
    sw = (964 - 5 * 8) / 6.0
    for i, (num, title, body, loss, col, soft, edge) in enumerate(STEPS):
        x = 18 + i * (sw + 8)
        rbox(b, x, 560, sw, 172, WHITE, edge, lw=1.0, r=7, z=3)
        rect(b, x + 2, 694, sw - 4, 36, soft, z=4)
        b.ax.add_patch(plt_circle((x + 18, 712), 10, facecolor=col,
                                  edgecolor="none", zorder=6))
        txt(b, x + 18, 712, num, size=9.0, color=WHITE, weight="bold", z=7)
        txt(b, x + 34, 712, title, size=7.6, color=col, weight="bold",
            ha="left", z=7)
        txt(b, x + sw / 2, 645, body, size=6.6, color=BODY, z=7, lsp=1.22)
        rbox(b, x + 8, 570, sw - 16, 34, soft, edge, lw=0.8, r=5, z=5)
        txt(b, x + sw / 2, 587, loss, size=6.8, color=col, weight="bold", z=7,
            lsp=1.12)
    # caption block
    rbox(b, 18, 40, 964, 498, WHITE, EDGE_GREY, lw=1.0, r=8, z=2)
    txt(b, 36, 516, "Figure notes \u2014 verified against source",
        size=11.0, color=NAVY, weight="bold", ha="left", z=6, family=SERIF)
    notes = [
        "G = GlobalMedFiLM: one shared encoder\u2013decoder, task-conditioned only through",
        f"   a {GLOBAL_MEDFILM_TASK_EMBEDDING_DIM}-D embedding and {len(GLOBAL_MEDFILM_FILM_SITES)} FiLM sites, F\u0302=(1+\u03b3)F+\u03b2. "
        "It is the backbone and the",
        "   legitimate single-model baseline, NOT the proposed system.",
        "R\u03c8 = BARRRegionalRefinerV1: 4-channel [RGB, p_global crop] CNN, trained with",
        "   0.5\u00b7BCEWithLogits + 0.5\u00b7soft Dice. It is not a residual/\u0394-mask module.",
        "B\u03c6 = BARRBenefitRouterV1: 202-D frozen GT-free features + its own 16-D task",
        "   embedding = 218-D; HuberLoss(\u0394=0.05) on paired \u03b4-Dice gain labels.",
        "S\u03c9 = BARRPostSafetyV1: 16-D frozen post-candidate features + 4-D one-hot",
        "   task = 20-D; BCEWithLogitsLoss on binary safety_target.",
        "Decision thresholds: ROI p_global \u2265 0.30; U \u2265 \u03c4_C8 = "
        f"{TAU_C8_FINAL_FLOAT:.7f}; S\u03c9 accept a \u2265 0.50;",
        f"   final mask P\u0302 = 1[P_out \u2265 {SEGMENTATION_OUTPUT_THRESHOLD:.2f}]. "
        "U = \u03b4\u0302_final \u2212 (1/4)\u00b7(1051648/10270749).",
        "Fusion is deterministic replacement inside the ROI; no alpha blending,",
        "   no learned fusion, no additive correction.",
        "The canonical wrapper registers R\u03c8 but does not call it: p_refine is supplied",
        "   from a frozen out-of-fold cache. Accordingly R\u03c8 is drawn as an offline",
        "   producer. OOF=TRUE for R\u03c8/B\u03c6/S\u03c9; OOF=FALSE for the backbone.",
        "VAL808 states: FORCED_SKIP 0, SKIP_GLOBAL 529, EXECUTE_THEN_ACCEPT 266,",
        "   EXECUTE_THEN_REJECT 13 (n = 808). No TEST1683 images were opened.",
        "No ground truth, diagnosis label or joint loss is present at inference.",
        "C1 (FiLM), C2 (BARR) and C3 (faithful baselines) remain NOT_ESTABLISHED;",
        "   the reported comparison is descriptive, not a controlled ablation.",
    ]
    y = 494
    for line in notes:
        txt(b, 36, y, line, size=7.8, color=BODY, ha="left", z=6)
        y -= 21
    return b


# --------------------------------------------------------------------------- #
# arrow provenance table (feeds QA and V7->V8 corrections)
# --------------------------------------------------------------------------- #
def arrow_registry() -> dict:
    R = "src/models/barr/ra_medfilm_barr.py"
    G = "src/models/film/global_medfilm.py"
    P = "src/models/barr/phase25_models.py"
    T = "reports/tables/phase27_val808_predictions.csv"
    verified = [
        ("x, t", "G", "single global forward", R, 260, "G(x, task_ids) -> p_global"),
        ("E(t) R^32", "G FiLM gamma/beta", "32-D task embedding conditions 5 FiLM sites", G, 47, "GLOBAL_MEDFILM_TASK_EMBEDDING_DIM = 32"),
        ("G", "p_global", "exactly one forward; probability map", R, 262, "_to_prob_map(g_out)"),
        ("p_global", "ROI window", "threshold 0.30, bbox, x1.50 expansion", R, 161, "_roi_window_from_probability"),
        ("ROI window", "action available?", "None window -> FORCED_SKIP", R, 268, "avail = (window is not None)"),
        ("action unavailable", "FORCED_SKIP -> p_global", "state 1 of 4", R, 272, "return _result('FORCED_SKIP', p_global, ...)"),
        ("202-D frozen cache", "B_phi", "GT-free Phase25B numeric features, normalised", R, 277, "rf.shape[0] == ROUTER_NUMERIC_DIM"),
        ("task id t", "B_phi 16-D embedding", "B_phi's own nn.Embedding(4,16)", P, 76, "emb = self.task_embedding(task_ids); cat -> 218"),
        ("B_phi", "delta_hat_final", "scalar predicted paired gain", R, 284, "float(self.benefit_router(x_num, t_ids))"),
        ("delta_hat_final", "U", "U = delta_hat_final - lambda*C", R, 286, "canonical_utility(delta_hat_final)"),
        ("U < tau_C8", "SKIP_GLOBAL -> p_global", "state 2 of 4", R, 290, "return _result('SKIP_GLOBAL', p_global, ...)"),
        ("U >= tau_C8", "EXECUTE branch", "requires oof_refined_crop_prob", R, 295, "raise if oof_refined_crop_prob is None"),
        ("R_psi (offline)", "p_refine OOF cache", "frozen OOF refined crop probability", R, 246, "oof_refined_crop_prob: 256x256 refined probability crop"),
        ("p_global + p_refine + window", "deterministic ROI fusion", "replacement, no alpha blending", R, 197, "out[y0:y1, x0:x1] = crop"),
        ("P_cand", "16-D post features + one-hot(t)", "Phase25F frozen cache, 16+4=20", R, 311, "np.concatenate([sf_norm, self._onehot_task(task_id)])"),
        ("20-D features", "S_omega", "logit -> sigmoid", R, 313, "float(self.post_safety(...))"),
        ("a >= 0.50", "EXECUTE_THEN_ACCEPT -> P_cand", "state 3 of 4", R, 319, "return _result('EXECUTE_THEN_ACCEPT', fused, ...)"),
        ("a < 0.50", "EXECUTE_THEN_REJECT -> p_global", "state 4 of 4", R, 321, "return _result('EXECUTE_THEN_REJECT', p_global, ...)"),
        ("P_out", "final binary mask", "threshold 0.50", R, 331, "prob >= self.segmentation_output_threshold"),
        ("state counts", "VAL808", "0 / 529 / 266 / 13 = 808", T, 1, "state_machine_branch value_counts"),
    ]
    removed = [
        ("Global features Fg -> B_phi", "UNSUPPORTED", "G exposes no separate Fg tensor to the router; B_phi consumes a 202-D frozen cache", R, 277),
        ("Cropped ROI xroi -> B_phi", "UNSUPPORTED", "B_phi is pre-refinement and never sees the ROI crop", R, 274),
        ("R_psi invoked at online inference", "UNSUPPORTED", "forward_inference registers R_psi but never calls it; p_refine is a supplied OOF cache", R, 295),
        ("R_psi = 'Regional Residual Refiner' with FiLM bars", "MISNAMED", "class is BARRRegionalRefinerV1, a plain 4-channel CNN with no FiLM, attention or residual head", "src/models/barr/regional_refiner.py", 1),
        ("R_psi -> 'delta P' corrected local mask", "UNSUPPORTED", "refiner emits a refined crop probability, not an additive correction", R, 300),
        ("'ROI composition' with '+' / alpha blending", "UNSUPPORTED", "fusion is deterministic replacement inside the ROI", R, 197),
        ("S_omega before candidate composition", "WRONG ORDER", "S_omega consumes post-candidate features and runs after fusion", R, 303),
        ("Single SKIP state ('no useful ROI')", "INCOMPLETE", "four states; two distinct skips: FORCED_SKIP and SKIP_GLOBAL", R, 68),
        ("Single shared E(t) for all modules", "UNSUPPORTED", "three distinct task representations: G 32-D, B_phi 16-D, S_omega 4-D one-hot", P, 76),
        ("S_omega 'consistency / reliability supervision'", "UNSUPPORTED", "target is binary sign(delta_dice); loss is BCEWithLogitsLoss", "scripts/analysis/phase25f_execution_common.py", 342),
        ("R_psi trained on 'residual correction'", "MISNAMED", "loss is 0.5*BCEWithLogits + 0.5*soft Dice on 4-channel ROI crops", "scripts/training/train_phase25a_refiner.py", 488),
        ("Joint end-to-end training / unified objective", "UNSUPPORTED", "wrapper defines 0 trainable parameters and no loss; stages trained sequentially", R, 6),
        ("Three legitimate inference outcomes (as 3 states)", "INCOMPLETE", "four canonical states; two skip states and two execute states", R, 68),
    ]
    return {
        "figure_id": "ReMedFiLM_Methodology_V8",
        "generated_from": "full_doc_report/v8_build/v8_figure_methodology.py",
        "visual_reference": "assets/figures/remedfilm_inference_infographic.png",
        "canonical_model_identity": "ReMedFiLM FULL = G + R_psi + B_phi + S_omega",
        "backbone_role": "GlobalMedFiLM is the backbone and ablation baseline ONLY",
        "runtime_constants": {
            "tau_C8_final": TAU_C8_FINAL_FLOAT,
            "roi_proposal_threshold": ROI_PROPOSAL_THRESHOLD,
            "roi_expansion": ROI_EXPANSION,
            "somega_accept_threshold": SOMEGA_ACCEPT_THRESHOLD,
            "segmentation_output_threshold": SEGMENTATION_OUTPUT_THRESHOLD,
            "router_input_dim": ROUTER_TOTAL_DIM,
            "safety_input_dim": SOMEGA_TOTAL_DIM,
            "states": list(STATES),
        },
        "verified_arrows": [
            {"from": a, "to": b_, "claim": c, "source_path": p,
             "source_line": ln, "evidence": e}
            for a, b_, c, p, ln, e in verified
        ],
        "removed_or_corrected_arrows": [
            {"v7_arrow": a, "verdict": v, "reason": r, "source_path": p,
             "source_line": ln}
            for a, v, r, p, ln in removed
        ],
        "verified_arrow_count": len(verified),
        "removed_or_corrected_count": len(removed),
        "execution": {
            "model_retrained": False,
            "new_inference_run": False,
            "TEST1683_opened": False,
            "checkpoints_modified": False,
        },
    }


# --------------------------------------------------------------------------- #
# output
# --------------------------------------------------------------------------- #
def save_board(b: Board, stem: str, formats=("svg", "png", "pdf"), dpi=300) -> dict:
    """Save via write-once artifacts; return path/size/sha for each format."""
    out = {}
    for ext in formats:
        target = FIG / f"{stem}.{ext}"
        tmp = FIG / f".v8_tmp_{stem}.{ext}"
        b.fig.savefig(tmp, format=ext, dpi=dpi, facecolor="white",
                      pad_inches=0, metadata=STABLE_METADATA.get(ext, {}))
        raw = tmp.read_bytes()
        tmp.unlink()
        write_artifact(target, raw)
        out[ext] = {"path": str(target.relative_to(FDR)).replace("\\", "/"),
                    "bytes": len(raw), "sha256": sha256(target)}
        print(f"  wrote {target.name}: {len(raw):,} bytes")
    b.close()
    return out


def main() -> None:
    print("V8 methodology figure family")
    manifest = {"outputs": {}}

    print("[1/3] main three-panel figure (1672 x 941)")
    manifest["outputs"]["main"] = save_board(
        build_full_v8(), "ReMedFiLM_Methodology_V8", ("svg", "pdf", "png"), dpi=300)

    print("[2/3] GitHub 16:9 variant (1600 x 900)")
    manifest["outputs"]["github_16x9"] = save_board(
        build_github_v8(), "ReMedFiLM_Methodology_GitHub_16x9", ("png", "svg"), dpi=200)

    print("[3/3] manuscript variant (1000 x 1360)")
    manifest["outputs"]["manuscript"] = save_board(
        build_manuscript_v8(), "ReMedFiLM_Methodology_Manuscript",
        ("svg", "pdf", "png"), dpi=250)

    reg = arrow_registry()
    reg["output_manifest"] = manifest
    p = write_json(FDR / "REMEDFILM_V8_METHODOLOGY_ARROWS.json", reg)
    print(f"  wrote {p.name}: {reg['verified_arrow_count']} verified arrows, "
          f"{reg['removed_or_corrected_count']} corrections")
    print("done.")


if __name__ == "__main__":
    main()
