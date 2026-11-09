"""ReMedFiLM methodology figure generator -- authoritative editable source.

This generator reproduces, from ONE code path, the layout of the authoritative
raster figure

    assets/figures/remedfilm_inference_infographic.png
    sha256 a5a5b1457efa51ded03de52518bfdc3812e0d5d0e191aa8a5793cb97c4dc3223

and emits, from the same drawing code:

    assets/figures/remedfilm_full_methodology.svg    (editable vector, primary)
    assets/figures/remedfilm_full_methodology.png    (raster preview)
    assets/figures/remedfilm_full_methodology.pdf    (vector print)
    assets/figures/remedfilm_methodology_compact.svg (single-column variant)
    assets/figures/remedfilm_methodology_compact.png

Scientific authority (all values read from source, never retyped by hand):

  * G  = ``GlobalMedFiLM``          src/models/film/global_medfilm.py
  * R  = ``BARRRegionalRefinerV1``  src/models/barr/regional_refiner.py
  * B  = ``BARRBenefitRouterV1``    src/models/barr/phase25_models.py
  * S  = ``BARRPostSafetyV1``       src/models/barr/phase25_models.py
  * assembly = ``RAMedFiLMBARR``     src/models/barr/ra_medfilm_barr.py

The node -> code table lives in ``docs/METHODOLOGY_IMPLEMENTATION_MAP.md``.  If an
operation could not be verified in the source, it is NOT drawn.

Coordinate system
-----------------
All geometry is expressed in **native canvas pixels** (a 1672 x 941 board).
The canvas is scaled to whatever physical size is requested, so the layout is
resolution independent and the aspect ratio never distorts.

Run:
    .venv\\Scripts\\python.exe assets/figures/generate_methodology.py

The figure is deliberately a *training-and-inference* diagram: Panel B shows the
inference state machine, Panel C shows the sequential staged training order.
No joint end-to-end backpropagation is drawn, because none is implemented.
No ground-truth mask appears on any inference path.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

# Byte-reproducible vector output: fix the SVG clip-path ID salt and suppress
# the auto-inserted Dublin-Core / PDF creation timestamp.  Together these make
# repeated regeneration produce identical SVG/PDF bytes, so a rebuild never
# shows up as a meaningless git diff.  No timestamp is hand-authored.
# Each backend accepts a different metadata key set, hence the per-format map.
matplotlib.rcParams["svg.hashsalt"] = "remedfilm-methodology-v1"
STABLE_METADATA = {
    "svg": {"Date": None},
    "pdf": {"CreationDate": None},
    "png": {},
}

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SAMPLES = ROOT / "reports" / "figures" / "methodology_diagram_package" / "representative_samples"

# --------------------------------------------------------------------------- #
# design tokens
# --------------------------------------------------------------------------- #
NAVY = "#1B2A4A"
INK = "#101828"
GREY = "#5B6472"
RULE = "#C7CEDB"

PANEL_A_EDGE = "#7B5EA7"
PANEL_A_HEAD = "#E4D7F0"
PANEL_A_BOX = "#F3EDF9"
PANEL_A_EDGE2 = "#A98BC9"

PANEL_B_EDGE = "#1D6FB8"
PANEL_B_HEAD = "#DCEAF8"
PANEL_B_FILL = "#F4F9FE"

BLUE = "#1D4ED8"
BLUE_SOFT = "#DCE9FB"
BLUE_EDGE = "#2F6FD0"

PURPLE = "#6D28A8"
PURPLE_SOFT = "#EDE2F8"
PURPLE_EDGE = "#8B4FC4"

TEAL = "#0F766E"
TEAL_SOFT = "#D8EFEC"
TEAL_EDGE = "#14958A"

GREEN = "#2E7D32"
GREEN_SOFT = "#DDF0DC"
GREEN_EDGE = "#3E9B42"

ORANGE = "#C1440E"
ORANGE_SOFT = "#FCE4DA"
ORANGE_EDGE = "#E05A22"

GREY_SOFT = "#F1F3F7"
GREY_EDGE = "#9AA3B2"

SERIF = "DejaVu Serif"
SANS = "DejaVu Sans"

INK_SOFT = "#374151"

# native board size (pixels)
BW, BH = 1672, 941


# --------------------------------------------------------------------------- #
# board: pixel coordinate system
# --------------------------------------------------------------------------- #
class Board:
    """Canvas with pixel coordinates.  Origin (0,0) = bottom-left."""

    def __init__(self, w_px=BW, h_px=BH, dpi=100):
        self.w = w_px
        self.h = h_px
        self.fig = plt.figure(figsize=(w_px / dpi, h_px / dpi), dpi=dpi)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, w_px)
        self.ax.set_ylim(0, h_px)
        self.ax.axis("off")
        self.ax.set_facecolor("#FFFFFF")
        self.ax.set_aspect("equal", adjustable="box")
        # scale factor from px -> points for font sizes
        self.k = (w_px / dpi) / w_px * 72.0

    def save(self, base: Path, formats=("svg", "png", "pdf"), dpi=400):
        for ext in formats:
            out = base.with_suffix("." + ext)
            self.fig.savefig(out, format=ext, dpi=dpi, facecolor="white",
                             pad_inches=0, metadata=STABLE_METADATA.get(ext, {}))
            print(f"  wrote {out.relative_to(ROOT)}  ({out.stat().st_size:,} bytes)")

    def close(self):
        plt.close(self.fig)


# --------------------------------------------------------------------------- #
# primitives
# --------------------------------------------------------------------------- #
def rbox(b, x, y, w, h, fc, ec, lw=1.2, r=12, z=2, alpha=1.0):
    """Rounded rectangle in pixel coordinates (y = bottom)."""
    p = FancyBboxPatch((x + r, y + r), max(w - 2 * r, 0.5), max(h - 2 * r, 0.5),
                       boxstyle=f"round,pad={r}",
                       linewidth=lw, edgecolor=ec, facecolor=fc, zorder=z,
                       alpha=alpha)
    b.ax.add_patch(p)
    return p


def rect(b, x, y, w, h, fc, ec="none", lw=0.0, z=2):
    b.ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec,
                             linewidth=lw, zorder=z))


def circ(b, cx, cy, r, fc, ec="none", lw=0.0, z=5):
    b.ax.add_patch(plt.Circle((cx, cy), r, facecolor=fc, edgecolor=ec,
                              linewidth=lw, zorder=z))


def txt(b, x, y, s, size=9.0, color=INK, weight="normal", ha="center",
        va="center", z=8, style="normal", family=SANS, lsp=1.22, rot=0):
    return b.ax.text(x, y, s, fontsize=size, color=color, fontweight=weight,
                     ha=ha, va=va, zorder=z, style=style, family=family,
                     linespacing=lsp, rotation=rot)


def arrow(b, p0, p1, color=NAVY, lw=1.4, ls="-", rad=0.0, z=6, head=7.0):
    b.ax.add_patch(FancyArrowPatch(
        p0, p1, arrowstyle="-|>", mutation_scale=head,
        linewidth=lw, color=color, linestyle=ls, zorder=z,
        shrinkA=0.0, shrinkB=0.0,
        connectionstyle=f"arc3,rad={rad}",
    ))


def elbow(b, pts, color=NAVY, lw=1.4, ls="-", z=6, head=7.0):
    """Poly-line with an arrow head on the final segment only."""
    for a, c in zip(pts[:-2], pts[1:-1]):
        b.ax.plot([a[0], c[0]], [a[1], c[1]], color=color, linewidth=lw,
                  linestyle=ls, zorder=z, solid_capstyle="round")
    arrow(b, pts[-2], pts[-1], color=color, lw=lw, ls=ls, z=z, head=head)


def diamond(b, cx, cy, w, h, fc, ec, label, fs=8.5, z=7):
    pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
    b.ax.add_patch(Polygon(pts, closed=True, facecolor=fc, edgecolor=ec,
                           linewidth=1.3, zorder=z))
    txt(b, cx, cy, label, size=fs, color=INK, weight="bold", z=z + 1)


def chip(b, cx, cy, w, h, label, sub, fc, ec, tcol, fs=8.4, subfs=7.4, z=6):
    """Rounded label chip centred on (cx, cy)."""
    x, y = cx - w / 2, cy - h / 2
    rbox(b, x, y, w, h, fc, ec, lw=1.2, r=9, z=z)
    if sub:
        txt(b, cx, cy + h * 0.18, label, size=fs, color=tcol, weight="bold", z=z + 2)
        txt(b, cx, cy - h * 0.20, sub, size=subfs, color=tcol, weight="bold", z=z + 2)
    else:
        txt(b, cx, cy, label, size=fs, color=tcol, weight="bold", z=z + 2)


def img_tile(b, x, y, w, h, path, ec="#C9CED8", lw=1.0, z=5):
    """Place an RGB image inside a framed tile (pixel coordinates, y = bottom)."""
    try:
        arr = mpimg.imread(path)
    except Exception:
        rect(b, x, y, w, h, "#DDE2EA", ec, lw=lw, z=z)
        return
    b.ax.imshow(arr, extent=(x, x + w, y, y + h), aspect="auto",
                interpolation="nearest", zorder=z)
    rect(b, x, y, w, h, "none", ec, lw=lw, z=z + 1)


def mask_tile(b, x, y, w, h, path, ec="#1A1A1A", lw=1.1, z=5, thresh=0.45):
    """Render a probability map as white foreground on black.

    ``path`` may point at a single-channel probability map (04 / 07) or at an
    RGB overlay (05); RGB inputs are reduced to luminance first.
    """
    try:
        arr = np.asarray(mpimg.imread(path))
        if arr.ndim == 3:
            arr = arr[..., :3].mean(axis=2)
        arr = arr.astype(float)
        if arr.max() > 1e-6:
            arr = arr / arr.max()
        rgba = np.zeros((arr.shape[0], arr.shape[1], 4), dtype=float)
        fg = arr > thresh
        rgba[fg, 0] = rgba[fg, 1] = rgba[fg, 2] = 1.0
        rgba[fg, 3] = 1.0
        b.ax.imshow(rgba, extent=(x, x + w, y, y + h), aspect="auto",
                    interpolation="nearest", zorder=z)
        rect(b, x, y, w, h, "none", ec, lw=lw, z=z + 1)
    except Exception:
        rect(b, x, y, w, h, "#101010", ec, lw=lw, z=z)


def roi_mask_tile(b, x, y, w, h, key="ISIC", ec="#1A1A1A", lw=1.1, z=5):
    """Render the ROI-proposal *box region* of the global probability map.

    Reads the frozen ROI box from the provenance-verified sample metadata and
    crops the corresponding window out of the global probability map.
    """
    try:
        meta = json.loads((SAMPLES / key / "sample_metadata.json").read_text())
        roi = meta["05_roi_proposal"]["roi_box"]
        arr = np.asarray(mpimg.imread(SAMPLES / key / "04_global_probability.png"))
        if arr.ndim == 3:
            arr = arr[..., :3].mean(axis=2)
        arr = arr.astype(float)
        y0, x0, y1, x1 = roi
        sub = arr[max(y0, 0):max(y1, 0), max(x0, 0):max(x1, 0)]
        if sub.size == 0:
            raise ValueError("empty crop")
        if sub.max() > 1e-6:
            sub = sub / sub.max()
        rgba = np.zeros((sub.shape[0], sub.shape[1], 4), dtype=float)
        fg = sub > 0.45
        rgba[fg, 0] = rgba[fg, 1] = rgba[fg, 2] = 1.0
        rgba[fg, 3] = 1.0
        b.ax.imshow(rgba, extent=(x, x + w, y, y + h), aspect="auto",
                    interpolation="nearest", zorder=z)
        rect(b, x, y, w, h, "none", ec, lw=lw, z=z + 1)
    except Exception:
        rect(b, x, y, w, h, "#101010", ec, lw=lw, z=z)


def bbox_overlay(b, x, y, w, h, key="ISIC", color="#FF2D2D", lw=2.0, z=7):
    """Draw the frozen red ROI box over an image tile."""
    try:
        meta = json.loads((SAMPLES / key / "sample_metadata.json").read_text())
        roi = meta["05_roi_proposal"]["roi_box"]
        im = mpimg.imread(SAMPLES / key / "01_input.png")
        ih, iw = im.shape[0], im.shape[1]
    except Exception:
        return
    y0, x0, y1, x1 = roi
    fx0 = x + (x0 / iw) * w
    fx1 = x + (x1 / iw) * w
    fy0 = y + (y0 / ih) * h
    fy1 = y + (y1 / ih) * h
    rect(b, fx0, fy0, max(fx1 - fx0, 1), max(fy1 - fy0, 1), "none", color, lw=lw, z=z)


def film_bars(b, x, y, w, h, color, z=8):
    """Stylised encoder-decoder channel profile (schematic, not measured data)."""
    widths = [0.16, 0.26, 0.40, 0.62, 0.85, 0.62, 0.40, 0.26, 0.16]
    m = len(widths)
    gap = w * 0.055
    bw = (w - gap * (m - 1)) / m
    for i, wf in enumerate(widths):
        bh = h * wf
        rect(b, x + i * (bw + gap), y + (h - bh) / 2, bw, bh, color, "none", 0, z=z)


def step_bars(b, x, y, w, h, color, heights=(0.45, 0.75, 1.0), z=8):
    n = len(heights)
    gap = w * 0.22
    bw = (w - gap * (n - 1)) / n
    for i, hf in enumerate(heights):
        bh = h * hf
        rect(b, x + i * (bw + gap), y + (h - bh) / 2, bw, bh, color, "none", 0, z=z)


def shield(b, cx, cy, s, color, z=8):
    """Shield glyph used for the post-safety gate."""
    pts = [(cx, cy + s * 0.55), (cx + s * 0.42, cy + s * 0.28),
           (cx + s * 0.42, cy - s * 0.20), (cx, cy - s * 0.58),
           (cx - s * 0.42, cy - s * 0.20), (cx - s * 0.42, cy + s * 0.28)]
    b.ax.add_patch(Polygon(pts, closed=True, facecolor="none", edgecolor=color,
                           linewidth=1.8, zorder=z))
    b.ax.plot([cx - s * 0.17, cx - s * 0.03, cx + s * 0.22],
              [cy + s * 0.02, cy - s * 0.18, cy + s * 0.21],
              color=color, linewidth=1.8, zorder=z + 1, solid_capstyle="round")


def tag_icon(b, cx, cy, s, color, z=8):
    """Price-tag glyph used for the task-identity node."""
    b.ax.add_patch(Polygon(
        [(cx - s * 0.48, cy - s * 0.30), (cx + s * 0.08, cy + s * 0.40),
         (cx + s * 0.48, cy + s * 0.04), (cx - s * 0.10, cy - s * 0.46)],
        closed=True, facecolor="none", edgecolor=color, linewidth=1.6, zorder=z))
    b.ax.add_patch(plt.Circle((cx + s * 0.20, cy + s * 0.19), s * 0.085,
                              facecolor="none", edgecolor=color,
                              linewidth=1.4, zorder=z + 1))


def snowflake(b, cx, cy, s, color, z=8):
    """Small snowflake glyph: frozen modules."""
    for ang in (0, 60, 120):
        a = np.deg2rad(ang)
        dx, dy = np.cos(a) * s, np.sin(a) * s
        b.ax.plot([cx - dx, cx + dx], [cy - dy, cy + dy], color=color,
                  linewidth=1.6, zorder=z, solid_capstyle="round")


def panel_header(b, x, y, w, h, letter, title, sub=None, edge=PANEL_B_EDGE,
                 head=PANEL_B_HEAD, tfs=13.0, subfs=8.4, two_line=None):
    """Panel frame + coloured header band + letter badge + title."""
    rbox(b, x, y, w, h, "#FFFFFF", edge, lw=1.6, r=12, z=1)
    band = h * 0.062
    rect(b, x + 2, y + h - band, w - 4, band - 2, head, z=2)
    badge = 20.0
    circ(b, x + 22, y + h - band / 2 - 1, badge / 2, edge, z=5)
    txt(b, x + 22, y + h - band / 2 - 1.5, letter, size=12.5, color="white",
        weight="bold", z=6)
    tx = x + 22 + badge / 2 + 9
    if two_line:
        txt(b, tx, y + h - band / 2 - 1.5, two_line[0], size=tfs, color=NAVY,
            weight="bold", ha="left", z=6, family=SERIF)
        txt(b, tx, y + h - band / 2 - 17.5, two_line[1], size=tfs, color=NAVY,
            weight="bold", ha="left", z=6, family=SERIF)
    elif sub:
        txt(b, tx, y + h - band / 2 - 1.5, title, size=tfs, color=NAVY,
            weight="bold", ha="left", z=6, family=SERIF)
        tw = tfs * 0.62 * len(title)
        txt(b, tx + tw + 6, y + h - band / 2 - 1.5, sub, size=subfs, color=NAVY,
            weight="bold", ha="left", z=6, style="italic")
    else:
        txt(b, tx, y + h - band / 2 - 1.5, title, size=tfs, color=NAVY,
            weight="bold", ha="left", z=6, family=SERIF)


# --------------------------------------------------------------------------- #
# PANEL A -- multi-domain inputs and task conditioning
# --------------------------------------------------------------------------- #
def panel_a(b):
    X, Y, W, H = 10, 300, 250, 630
    panel_header(b, X, Y, W, H, "A", "", edge=PANEL_A_EDGE, head=PANEL_A_HEAD,
                 tfs=10.4, two_line=("Multi-domain inputs and",
                                     "task conditioning"))

    rows = [("ISIC 2018", ["(Dermoscopy)"], "ISIC"),
            ("BUSI-WHU", ["(Breast", "Ultrasound)"], "BUSI"),
            ("Kvasir-SEG", ["(Endoscopy)"], "KVASIR"),
            ("KUB-StoneX", ["(KUB", "Radiography)"], "KUB")]
    top = Y + H - 56
    row_h = 74
    gap = 9
    lx = X + 14
    lw_ = W - 28
    for i, (name, mods, key) in enumerate(rows):
        ry = top - (i + 1) * row_h - i * gap
        rbox(b, lx, ry, lw_, row_h, "#FFFFFF", "#B9C0CC", lw=1.1, r=12, z=2)
        img_tile(b, lx + 8, ry + 7, 58, row_h - 14,
                 SAMPLES / key / "01_input.png", ec="#C9CED8", lw=1.0, z=3)
        tx = lx + 74
        if len(mods) == 1:
            txt(b, tx, ry + row_h * 0.62, name, size=9.4, color=INK,
                weight="bold", ha="left", z=6)
            txt(b, tx, ry + row_h * 0.27, mods[0], size=8.2, color=INK,
                ha="left", z=6)
        else:
            txt(b, tx, ry + row_h * 0.70, name, size=9.4, color=INK,
                weight="bold", ha="left", z=6)
            txt(b, tx, ry + row_h * 0.43, mods[0], size=8.2, color=INK,
                ha="left", z=6)
            txt(b, tx, ry + row_h * 0.18, mods[1], size=8.2, color=INK,
                ha="left", z=6)

    # convergence bracket  ->  task identity
    ty = top - 4 * row_h - 3 * gap
    jx = X + W - 14
    elbow(b, [(X + W - 8, top - row_h * 0.5),
              (jx, top - row_h * 0.5),
              (jx, ty - 22),
              (X + 32, ty - 22),
              (X + 32, ty - 40)], color="#1F2937", lw=1.3, z=5)

    # task identity node
    idw, idh = 118, 50
    idy = ty - 40 - idh
    rbox(b, X + 14, idy, idw, idh, PANEL_A_BOX, PANEL_A_EDGE2, lw=1.4, r=11, z=4)
    tag_icon(b, X + 32, idy + idh / 2, 19, PURPLE, z=6)
    txt(b, X + 46, idy + idh * 0.66, "Task identity /", size=8.2, color=INK,
        weight="bold", ha="left", z=6)
    txt(b, X + 46, idy + idh * 0.26, "domain label  t", size=8.2, color=INK,
        weight="bold", ha="left", z=6)

    # task embedding node
    ew, eh = 56, 50
    ex = X + 142
    rbox(b, ex, idy, ew, eh, PANEL_A_BOX, PANEL_A_EDGE2, lw=1.4, r=11, z=4)
    txt(b, ex + ew / 2, idy + eh * 0.72, "Task", size=7.8, color=INK,
        weight="bold", z=6)
    txt(b, ex + ew / 2, idy + eh * 0.44, "embedding", size=7.8, color=INK,
        weight="bold", z=6)
    txt(b, ex + ew / 2, idy + eh * 0.15, "E(t)", size=8.4, color=NAVY,
        weight="bold", style="italic", z=6)
    arrow(b, (X + 136, idy + idh / 2), (ex, idy + eh / 2), color="#1F2937",
          lw=1.4, z=5)

    # E(t) out to the backbone (Panel B)
    return (ex + ew, idy + eh / 2)


# --------------------------------------------------------------------------- #
# PANEL B -- FULL proposed inference system
# --------------------------------------------------------------------------- #
def panel_b(b, e_out):
    X, Y, W, H = 268, 300, 1394, 630
    panel_header(b, X, Y, W, H, "B", "ReMedFiLM -- FULL Proposed Inference System",
                 edge=PANEL_B_EDGE, head=PANEL_B_HEAD, tfs=13.0)

    # inner system frame
    ix, iy = X + 14, Y + 12
    iw, ih = W - 28, H - 74
    rbox(b, ix, iy, iw, ih, PANEL_B_FILL, PANEL_B_EDGE, lw=1.2, r=12, z=1)

    # system title ribbon
    rb_w, rb_h = 300, 30
    rb_x = ix + 490
    rb_y = iy + ih - 40
    rbox(b, rb_x, rb_y, rb_w, rb_h, "#0B4E9B", "#0B4E9B", lw=0.9, r=12, z=5)
    txt(b, rb_x + rb_w / 2, rb_y + rb_h / 2,
        "ReMedFiLM (G + B\u03c6 + R\u03c8 + S\u03c9)", size=10.6, color="white",
        weight="bold", z=7)

    # ---- G backbone -------------------------------------------------------
    gx, gy, gw, gh = ix + 46, iy + 330, 150, 190
    rbox(b, gx, gy, gw, gh, BLUE_SOFT, BLUE_EDGE, lw=1.5, r=12, z=3)
    txt(b, gx + gw / 2, gy + gh - 26, "G: Task-conditioned", size=9.2,
        color=BLUE, weight="bold", z=6)
    txt(b, gx + gw / 2, gy + gh - 44, "GlobalMedFiLM", size=9.2, color=BLUE,
        weight="bold", z=6)
    txt(b, gx + gw / 2, gy + gh - 62, "Backbone", size=9.2, color=BLUE,
        weight="bold", z=6)
    film_bars(b, gx + 16, gy + 34, gw - 32, 78, "#7FB2F0", z=6)

    # ---- global probability map Pg ---------------------------------------
    pgx, pgy = ix + 276, iy + 446
    txt(b, pgx, pgy + 74, "Global", size=7.4, color=INK, z=6)
    txt(b, pgx, pgy + 60, "probability map", size=7.4, color=INK, z=6)
    txt(b, pgx, pgy + 44, "Pg", size=9.2, color=NAVY, weight="bold",
        style="italic", z=6)
    mask_tile(b, pgx - 28, pgy, 56, 40, SAMPLES / "ISIC" / "04_global_probability.png",
              ec="#1A1A1A", lw=1.1, z=5)

    # ---- global features Fg ----------------------------------------------
    gfx, gfy = ix + 276, iy + 324
    txt(b, gfx, gfy + 58, "Global", size=7.4, color=INK, z=6)
    txt(b, gfx, gfy + 44, "features", size=7.4, color=INK, z=6)
    txt(b, gfx, gfy + 28, "Fg", size=9.2, color=NAVY, weight="bold",
        style="italic", z=6)
    for i in range(3):
        rect(b, gfx - 34 + i * 6, gfy - 22 + i * 6, 34, 30, "#5FA8E8", "none", 0, 4 + i)
        rect(b, gfx - 34 + i * 6, gfy - 22 + i * 6, 34, 30, "none", "#2F6FD0", 1.0, 5 + i)

    # ---- ROI proposal -----------------------------------------------------
    rx, ry, rw, rh = ix + 348, iy + 350, 190, 150
    rbox(b, rx, ry, rw, rh, PURPLE_SOFT, PURPLE_EDGE, lw=1.5, r=12, z=3)
    txt(b, rx + rw / 2, ry + rh - 24, "ROI proposal /", size=9.0, color=PURPLE,
        weight="bold", z=6)
    txt(b, rx + rw / 2, ry + rh - 41, "candidate region", size=9.0, color=PURPLE,
        weight="bold", z=6)
    txt(b, rx + rw / 2, ry + rh - 58, "extraction", size=9.0, color=PURPLE,
        weight="bold", z=6)
    img_tile(b, rx + 18, ry + 16, 58, 58, SAMPLES / "ISIC" / "01_input.png",
             ec="#C9CED8", lw=1.0, z=5)
    bbox_overlay(b, rx + 18, ry + 16, 58, 58, key="ISIC", z=7)
    arrow(b, (rx + 82, ry + 45), (rx + 104, ry + 45), color="#1F2937", lw=1.3, z=7)
    roi_mask_tile(b, rx + 110, ry + 16, 58, 58, key="ISIC", ec="#1A1A1A",
                  lw=1.0, z=5)
    bbox_overlay(b, rx + 110, ry + 16, 58, 58, key="ISIC", color="#FF2D2D",
                 lw=1.6, z=7)

    # ---- cropped candidate ROI -------------------------------------------
    crx, cry = ix + 578, iy + 424
    txt(b, crx, cry + 56, "Cropped", size=7.4, color=INK, weight="bold", z=6)
    txt(b, crx, cry + 42, "candidate ROI", size=7.4, color=INK, weight="bold", z=6)
    txt(b, crx, cry + 26, "xroi", size=8.8, color=NAVY, weight="bold",
        style="italic", z=6)
    roi_mask_tile(b, crx - 30, cry - 8, 60, 32, key="ISIC", ec="#1A1A1A",
                  lw=1.2, z=5)

    # ---- R_psi refiner ----------------------------------------------------
    fx, fy, fw, fh = ix + 760, iy + 350, 180, 150
    rbox(b, fx, fy, fw, fh, PURPLE_SOFT, PURPLE_EDGE, lw=1.5, r=12, z=3)
    txt(b, fx + fw / 2, fy + fh - 24, "R\u03c8: Regional", size=9.0, color=PURPLE,
        weight="bold", z=6)
    txt(b, fx + fw / 2, fy + fh - 41, "Residual Refiner", size=9.0, color=PURPLE,
        weight="bold", z=6)
    film_bars(b, fx + 16, fy + 24, fw - 32, 58, "#B083D8", z=6)

    # ---- dP corrected local mask ------------------------------------------
    dpx, dpy = ix + 1000, iy + 428
    txt(b, dpx, dpy + 56, "\u0394P", size=10.0, color=INK, weight="bold", z=6)
    txt(b, dpx, dpy + 40, "(corrected", size=7.4, color=INK, z=6)
    txt(b, dpx, dpy + 26, "local mask)", size=7.4, color=INK, z=6)
    mask_tile(b, dpx - 30, dpy - 8, 60, 32, SAMPLES / "ISIC" / "07_final_segmentation.png",
              ec="#1A1A1A", lw=1.2, z=5)

    # ---- B_phi benefit router ---------------------------------------------
    bxx, byy, bww, bhh = ix + 392, iy + 300, 232, 48
    rbox(b, bxx, byy, bww, bhh, TEAL_SOFT, TEAL_EDGE, lw=1.5, r=12, z=3)
    step_bars(b, bxx + 16, byy + 12, 40, 28, "#14958A", z=6)
    txt(b, bxx + 68, byy + bhh / 2, "B\u03c6: Benefit Router", size=9.2, color=TEAL,
        weight="bold", ha="left", z=6)

    # ---- S_omega post-safety gate ----------------------------------------
    sxx, syy, sww, shh = ix + 800, iy + 300, 218, 48
    rbox(b, sxx, syy, sww, shh, TEAL_SOFT, TEAL_EDGE, lw=1.5, r=12, z=3)
    shield(b, sxx + 26, syy + shh / 2, 20, TEAL, z=6)
    txt(b, sxx + 46, syy + shh / 2, "S\u03c9: Post-Safety Gate", size=9.2, color=TEAL,
        weight="bold", ha="left", z=6)

    # ---- ROI composition ---------------------------------------------------
    ccx, ccy, ccw, cch = ix + 292, iy + 108, 234, 100
    rbox(b, ccx, ccy, ccw, cch, GREEN_SOFT, GREEN_EDGE, lw=1.5, r=12, z=3)
    txt(b, ccx + ccw / 2, ccy + cch - 22, "ROI composition", size=9.0,
        color=GREEN, weight="bold", z=6)
    txt(b, ccx + ccw / 2, ccy + cch - 37, "(insert refined local mask)",
        size=7.6, color=GREEN, weight="bold", z=6)
    mask_tile(b, ccx + 12, ccy + 13, 48, 40, SAMPLES / "ISIC" / "04_global_probability.png",
              ec="#1A1A1A", lw=1.1, z=5)
    txt(b, ccx + 89, ccy + 33, "+", size=11.0, color=INK, weight="bold", z=7)
    roi_mask_tile(b, ccx + 104, ccy + 13, 48, 40, key="ISIC", ec="#1A1A1A",
                  lw=1.1, z=5)
    arrow(b, (ccx + 158, ccy + 33), (ccx + 170, ccy + 33), color="#1F2937",
          lw=1.3, z=7)
    mask_tile(b, ccx + 176, ccy + 13, 36, 40, SAMPLES / "ISIC" / "07_final_segmentation.png",
              ec="#1A1A1A", lw=1.1, z=5)

    # ---- final output -----------------------------------------------------
    fox, foy, fow, foh = ix + 588, iy + 134, 318, 48
    rbox(b, fox, foy, fow, foh, "#0B4E9B", "#0B4E9B", lw=0.9, r=12, z=5)
    mask_tile(b, fox + 12, foy + 8, 36, 34, SAMPLES / "ISIC" / "07_final_segmentation.png",
              ec="#FFFFFF", lw=1.0, z=6)
    txt(b, fox + 60, foy + foh / 2, "ReMedFiLM Final Segmentation  P\u0302",
        size=9.8, color="white", weight="bold", ha="left", z=7)

    # ---- decisions --------------------------------------------------------
    dx, dy = ix + 452, iy + 232
    diamond(b, dx, dy, 96, 62, "#FFFFFF", BLUE_EDGE, "Refine?", fs=9.0)

    chip(b, ix + 322, dy, 100, 38, "SKIP", "(no useful ROI)",
         "#FFFFFF", BLUE_EDGE, BLUE, fs=8.8, subfs=7.4)
    chip(b, ix + 586, dy, 108, 38, "REFINE", "(beneficial)",
         GREEN_SOFT, GREEN_EDGE, GREEN, fs=8.8, subfs=7.4)

    ax2, ay2 = ix + 928, iy + 232
    diamond(b, ax2, ay2, 92, 60, TEAL_SOFT, TEAL_EDGE, "Accept?", fs=9.0)

    chip(b, ix + 778, ay2, 96, 36, "ACCEPT", "(use refinement)",
         GREEN_SOFT, GREEN_EDGE, GREEN, fs=8.4, subfs=7.2)
    chip(b, ix + 1054, ay2, 104, 36, "REJECT", "(fallback to Pg)",
         ORANGE_SOFT, ORANGE_EDGE, ORANGE, fs=8.4, subfs=7.2)

    # ---- inference arrows -------------------------------------------------
    arrow(b, (gx - 30, gy + gh * 0.70), (gx, gy + gh * 0.70),
          color="#1F2937", lw=1.4, z=5)
    txt(b, gx - 36, gy + gh * 0.70 + 15, "x", size=10.0, color=INK,
        weight="bold", style="italic", ha="right", z=6)

    # E(t) from Panel A into the backbone
    ex, ey = e_out
    elbow(b, [(ex, ey), (X + 40, ey), (X + 40, gy + gh * 0.32),
              (gx, gy + gh * 0.32)], color="#1F2937", lw=1.3, z=4)
    txt(b, X + 52, gy + gh * 0.32 - 15, "E(t)", size=9.4, color=INK, weight="bold",
        style="italic", ha="left", z=6)

    # G -> Pg and G -> Fg
    arrow(b, (gx + gw, gy + gh * 0.78), (pgx - 34, pgy + 26),
          color="#1F2937", lw=1.4, z=5)
    arrow(b, (gx + gw, gy + gh * 0.30), (gfx - 40, gfy + 4),
          color="#1F2937", lw=1.4, z=5)
    # Pg -> ROI proposal
    arrow(b, (pgx + 34, pgy + 16), (rx, ry + rh * 0.66), color="#1F2937",
          lw=1.4, z=5)
    # ROI proposal -> cropped ROI
    arrow(b, (rx + rw, ry + rh * 0.62), (crx - 34, cry + 8),
          color="#1F2937", lw=1.4, z=5)

    # Fg -> router
    elbow(b, [(gfx + 38, gfy - 18), (gfx + 38, gfy - 44), (bxx + 32, gfy - 44),
              (bxx + 32, byy)], color="#1F2937", lw=1.3, z=4)
    # cropped ROI -> router (candidate context)
    elbow(b, [(crx, cry - 6), (crx, byy - 18), (bxx + bww, byy - 18),
              (bxx + bww, byy + bhh * 0.5)], color="#1F2937", lw=1.3, z=4)

    # router -> Refine?
    arrow(b, (bxx + bww * 0.58, byy + bhh), (dx - 10, dy + 31), color="#1F2937",
          lw=1.3, z=5)
    # Refine? -> SKIP / REFINE
    arrow(b, (dx - 48, dy), (ix + 372, dy), color=BLUE, lw=1.4, z=5)
    arrow(b, (dx + 48, dy), (ix + 532, dy), color=GREEN, lw=1.4, z=5)
    # REFINE -> R_psi
    elbow(b, [(ix + 640, dy), (ix + 664, dy), (ix + 664, fy + fh * 0.55),
              (fx, fy + fh * 0.55)], color=GREEN, lw=1.5, z=5)
    # R_psi -> dP
    arrow(b, (fx + fw, fy + fh * 0.58), (dpx - 36, dpy + 8),
          color="#1F2937", lw=1.4, z=5)
    # dP -> S_omega
    elbow(b, [(dpx, dpy - 14), (dpx, syy - 18), (sxx + sww * 0.5, syy - 18),
              (sxx + sww * 0.5, syy)], color="#1F2937", lw=1.3, z=4)
    # S_omega -> Accept?
    arrow(b, (sxx + sww * 0.74, syy), (ax2 - 10, ay2 + 30), color="#1F2937",
          lw=1.3, z=5)
    # Accept? -> ACCEPT / REJECT
    arrow(b, (ax2 - 46, ay2), (ix + 826, ay2), color=GREEN, lw=1.4, z=5)
    arrow(b, (ax2 + 46, ay2), (ix + 1002, ay2), color=ORANGE, lw=1.4, z=5)
    # ACCEPT -> ROI composition
    elbow(b, [(ix + 778, ay2 - 18), (ix + 778, ccy + cch * 0.60),
              (ccx + ccw, ccy + cch * 0.60)], color=GREEN, lw=1.5, z=5)
    # ROI composition -> final
    elbow(b, [(ccx + ccw / 2, ccy), (ccx + ccw / 2, foy + foh + 14),
              (fox + 28, foy + foh + 14), (fox + 28, foy + foh)],
          color=GREEN, lw=1.5, z=5)
    # REJECT -> final (global fallback)
    elbow(b, [(ix + 1106, ay2 - 18), (ix + 1106, foy + foh * 0.55),
              (fox + fow, foy + foh * 0.55)], color=ORANGE, lw=1.5, z=5)
    # SKIP -> final (global output)
    elbow(b, [(ix + 322, dy - 19), (ix + 322, foy + foh * 0.22),
              (fox, foy + foh * 0.22)], color=BLUE, lw=1.5, z=5)

    # ---- three legitimate inference outcomes ------------------------------
    oy = iy + 8
    ox = ix + 26
    ow_ = iw - 26 - 16
    rbox(b, ox, oy, ow_, 58, "#FBFCFE", "#C7CEDB", lw=1.1, r=10, z=3)
    rbox(b, ox + 6, oy + 30, 150, 24, PANEL_A_HEAD, PANEL_A_EDGE2, lw=1.1,
         r=9, z=4)
    txt(b, ox + 81, oy + 47, "Three legitimate inference", size=7.8,
        color=NAVY, weight="bold", style="italic", z=6)
    txt(b, ox + 81, oy + 34, "outcomes (of ReMedFiLM)", size=7.8,
        color=NAVY, weight="bold", style="italic", z=6)

    outs = [("(a) No useful ROI / Skip", "\u2192 global output (Pg)", BLUE, BLUE_EDGE),
            ("(b) Refine + Accept", "\u2192 composed refined output", GREEN, GREEN_EDGE),
            ("(c) Refine + Reject", "\u2192 global fallback (Pg)", ORANGE, ORANGE_EDGE)]
    cell = (ow_ - 160) / 3.0
    for i, (l1, l2, col, ecol) in enumerate(outs):
        cx = ox + 156 + cell * i
        rbox(b, cx, oy + 5, cell - 6, 48, "#FFFFFF", ecol, lw=1.1, r=9, z=4)
        mask_tile(b, cx + 8, oy + 13, 40, 32, SAMPLES / "ISIC" / "07_final_segmentation.png",
                  ec="#1A1A1A", lw=1.0, z=5)
        txt(b, cx + 54, oy + 37, l1, size=7.2, color=col, weight="bold",
            ha="left", z=6)
        txt(b, cx + 54, oy + 19, l2, size=7.2, color=INK, ha="left", z=6)


# --------------------------------------------------------------------------- #
# PANEL C -- staged training strategy
# --------------------------------------------------------------------------- #
def panel_c(b):
    X, Y, W, H = 10, 10, 1046, 278
    panel_header(b, X, Y, W, H, "C", "Staged training strategy",
                 edge=PANEL_B_EDGE, head=PANEL_B_HEAD, tfs=11.6)
    txt(b, X + W - 16, Y + H - 15, "(separate training with progressive dependency)",
        size=8.0, color=NAVY, weight="bold", style="italic", ha="right", z=6)

    steps = [
        ("1", "Train G", "Train global backbone G\n(GlobalMedFiLM) on\nmulti-domain data.",
         BLUE, BLUE_SOFT, BLUE_EDGE, "bars"),
        ("2", "Generate\npredictions & ROIs",
         "Generate global\npredictions (Pg) and\nROI crops.",
         PURPLE, PURPLE_SOFT, PURPLE_EDGE, "img"),
        ("3", "Train R\u03c8", "Train regional refiner\nR\u03c8 on residual\ncorrection.",
         PURPLE, PURPLE_SOFT, PURPLE_EDGE, "bars"),
        ("4", "Create gain labels",
         "Create paired gain labels /\nexpected refinement benefit\n(e.g., performance gain g).",
         GREY, GREY_SOFT, GREY_EDGE, "eq"),
        ("5", "Train B\u03c6", "Train benefit router\nB\u03c6 using gain labels.",
         TEAL, TEAL_SOFT, TEAL_EDGE, "bars"),
        ("6", "Train S\u03c9",
         "Train post-safety gate\nS\u03c9 (consistency /\nreliability supervision).",
         TEAL, TEAL_SOFT, TEAL_EDGE, "shield"),
    ]
    sx = X + 14
    sy = Y + 56
    sh = H - 56 - 44
    sw = (W - 28 - 5 * 10) / 6.0
    for i, (num, title, body, col, soft, edge, kind) in enumerate(steps):
        cx = sx + i * (sw + 10)
        rbox(b, cx, sy, sw, sh, "#FFFFFF", edge, lw=1.3, r=11, z=3)
        # header band
        rect(b, cx + 2, sy + sh - 48, sw - 4, 46, soft, z=4)
        circ(b, cx + 21, sy + sh - 25, 11.5, col, z=6)
        txt(b, cx + 21, sy + sh - 25.5, num, size=9.4, color="white",
            weight="bold", z=7)
        txt(b, cx + 38, sy + sh - 25, title, size=8.4, color=col, weight="bold",
            ha="left", z=7, lsp=1.08)

        if kind == "bars":
            film_bars(b, cx + 16, sy + sh - 112, sw - 32, 52,
                      "#7FB2F0" if col == BLUE else "#B083D8", z=6)
        elif kind == "img":
            mask_tile(b, cx + 22, sy + sh - 108, 36, 36,
                      SAMPLES / "ISIC" / "04_global_probability.png",
                      ec="#1A1A1A", lw=1.0, z=6)
            arrow(b, (cx + 62, sy + sh - 90), (cx + 78, sy + sh - 90),
                  color="#1F2937", lw=1.2, z=6)
            mask_tile(b, cx + 82, sy + sh - 108, 36, 36,
                      SAMPLES / "ISIC" / "07_final_segmentation.png",
                      ec="#1A1A1A", lw=1.0, z=6)
        elif kind == "eq":
            rbox(b, cx + 12, sy + sh - 108, sw - 24, 36, soft, edge, lw=1.0,
                 r=7, z=6)
            txt(b, cx + sw / 2, sy + sh - 90, "g = M(P_refine) \u2212 M(Pg)",
                size=7.8, color=INK, weight="bold", style="italic", z=7)
        elif kind == "shield":
            shield(b, cx + sw / 2, sy + sh - 88, 19, TEAL, z=6)

        txt(b, cx + sw / 2, sy + 40, body, size=7.4, color=INK, z=7, lsp=1.32)

        if i < len(steps) - 1:
            arrow(b, (cx + sw, sy + sh * 0.55), (cx + sw + 10, sy + sh * 0.55),
                  color="#1F2937", lw=1.2, ls=(0, (3, 2)), z=6, head=5.0)

    # summary bar
    rbox(b, X + 130, Y + 10, 400, 34, PANEL_A_HEAD, PANEL_A_EDGE2, lw=1.1,
         r=9, z=3)
    txt(b, X + 330, Y + 27, "Staged training (G \u2192 R\u03c8 \u2192 B\u03c6 \u2192 S\u03c9)",
        size=9.4, color=NAVY, weight="bold", style="italic", z=5)

    rbox(b, X + 548, Y + 10, 484, 34, "#FFFFFF", BLUE_EDGE, lw=1.1, r=9, z=3)
    snowflake(b, X + 572, Y + 27, 10, BLUE, z=6)
    txt(b, X + 590, Y + 27,
        "Inference uses the frozen trained modules: G, B\u03c6, R\u03c8 and S\u03c9.",
        size=8.0, color=BLUE, weight="bold", style="italic", ha="left", z=5)


# --------------------------------------------------------------------------- #
# LEGEND
# --------------------------------------------------------------------------- #
def legend(b):
    X, Y, W, H = 1066, 10, 596, 278
    rbox(b, X, Y, W, H, "#FFFFFF", PANEL_B_EDGE, lw=1.6, r=12, z=1)
    rect(b, X + 2, Y + H - 26, W - 4, 24, PANEL_B_HEAD, z=2)
    txt(b, X + 16, Y + H - 14, "Legend", size=11.5, color=NAVY, weight="bold",
        ha="left", z=6, family=SERIF)

    rows = [
        ("line", NAVY, "-", "Inference flow (used in inference)"),
        ("line", NAVY, "--", "Training-only dependency (used in training)"),
        ("box", BLUE_SOFT, BLUE_EDGE, "Global backbone (G: GlobalMedFiLM)"),
        ("box", PURPLE_SOFT, PURPLE_EDGE, "Task conditioning / ROI module"),
        ("box", TEAL_SOFT, TEAL_EDGE, "Routing / decision module (B\u03c6, S\u03c9)"),
        ("box", GREEN_SOFT, GREEN_EDGE,
         "Accepted refinement path\n(refine + accept, use refined result)"),
        ("box", ORANGE_SOFT, ORANGE_EDGE,
         "Rejected fallback path\n(refine + reject, or direct skip, use Pg)"),
    ]
    ry = Y + H - 46
    for kind, c1, c2, label in rows:
        if kind == "line":
            ls = "-" if c2 == "-" else (0, (3, 2))
            b.ax.plot([X + 20, X + 58], [ry, ry], color=c1, linewidth=1.6,
                      linestyle=ls, zorder=6, solid_capstyle="round")
            arrow(b, (X + 50, ry), (X + 60, ry), color=c1, lw=1.6, z=6, head=5.0)
        else:
            rbox(b, X + 20, ry - 10, 42, 20, c1, c2, lw=1.2, r=6, z=5)
        nlines = label.count("\n") + 1
        txt(b, X + 74, ry + (6 if nlines > 1 else 0), label, size=8.2, color=INK,
            ha="left", va="center", z=6, lsp=1.22)
        ry -= 28 if nlines == 1 else 38


# --------------------------------------------------------------------------- #
# assembly
# --------------------------------------------------------------------------- #
def build_full():
    b = Board(BW, BH)
    e_out = panel_a(b)
    panel_b(b, e_out)
    panel_c(b)
    legend(b)
    return b


def build_compact():
    """Single-column variant: the FULL inference system only, simplified."""
    b = Board(1000, 700)
    X, Y, W, H = 12, 12, 976, 676
    rbox(b, X, Y, W, H, "#FFFFFF", PANEL_B_EDGE, lw=1.6, r=12, z=1)
    txt(b, X + W / 2, Y + H - 26,
        "ReMedFiLM -- FULL Proposed Inference System", size=14.0, color=NAVY,
        weight="bold", z=6, family=SERIF)

    # x -> G
    gx, gy, gw, gh = X + 130, Y + 300, 190, 220
    rbox(b, gx, gy, gw, gh, BLUE_SOFT, BLUE_EDGE, lw=1.6, r=12, z=3)
    txt(b, gx + gw / 2, gy + gh - 32, "G: Task-conditioned", size=10.0,
        color=BLUE, weight="bold", z=6)
    txt(b, gx + gw / 2, gy + gh - 53, "GlobalMedFiLM Backbone", size=10.0,
        color=BLUE, weight="bold", z=6)
    film_bars(b, gx + 16, gy + 70, gw - 32, 82, "#7FB2F0", z=6)
    txt(b, gx - 22, gy + gh * 0.6, "x", size=11.0, color=INK, weight="bold",
        style="italic", ha="right", z=6)
    arrow(b, (gx - 14, gy + gh * 0.6), (gx, gy + gh * 0.6), color="#1F2937",
          lw=1.5, z=5)

    # ROI proposal
    rx, ry, rw, rh = X + 380, Y + 300, 200, 220
    rbox(b, rx, ry, rw, rh, PURPLE_SOFT, PURPLE_EDGE, lw=1.6, r=12, z=3)
    txt(b, rx + rw / 2, ry + rh - 30, "ROI proposal /", size=10.0, color=PURPLE,
        weight="bold", z=6)
    txt(b, rx + rw / 2, ry + rh - 52, "candidate region", size=10.0, color=PURPLE,
        weight="bold", z=6)
    txt(b, rx + rw / 2, ry + rh - 72, "extraction", size=10.0, color=PURPLE,
        weight="bold", z=6)
    img_tile(b, rx + 18, ry + 24, 76, 76, SAMPLES / "ISIC" / "01_input.png",
             ec="#C9CED8", lw=1.0, z=5)
    bbox_overlay(b, rx + 18, ry + 24, 76, 76, key="ISIC", z=7)
    arrow(b, (rx + 100, ry + 62), (rx + 124, ry + 62), color="#1F2937", lw=1.4, z=7)
    roi_mask_tile(b, rx + 130, ry + 24, 56, 76, key="ISIC", ec="#1A1A1A",
                  lw=1.0, z=5)
    arrow(b, (gx + gw, gy + gh * 0.72), (rx, ry + rh * 0.72), color="#1F2937",
          lw=1.5, z=5)

    # R_psi
    fx, fy, fw, fh = X + 630, Y + 330, 190, 160
    rbox(b, fx, fy, fw, fh, PURPLE_SOFT, PURPLE_EDGE, lw=1.6, r=12, z=3)
    txt(b, fx + fw / 2, fy + fh - 30, "R\u03c8: Regional", size=10.0, color=PURPLE,
        weight="bold", z=6)
    txt(b, fx + fw / 2, fy + fh - 52, "Residual Refiner", size=10.0, color=PURPLE,
        weight="bold", z=6)
    film_bars(b, fx + 16, fy + 26, fw - 32, 60, "#B083D8", z=6)
    arrow(b, (rx + rw, ry + rh * 0.5), (fx, fy + fh * 0.5), color=GREEN, lw=1.6, z=5)

    # B_phi
    bxx, byy, bww, bhh = X + 200, Y + 190, 250, 60
    rbox(b, bxx, byy, bww, bhh, TEAL_SOFT, TEAL_EDGE, lw=1.6, r=12, z=3)
    step_bars(b, bxx + 18, byy + 15, 42, 30, "#14958A", z=6)
    txt(b, bxx + 74, byy + bhh / 2, "B\u03c6: Benefit Router", size=10.0, color=TEAL,
        weight="bold", ha="left", z=6)
    arrow(b, (gx + gw * 0.5, gy), (bxx + bww * 0.5, byy + bhh), color="#1F2937",
          lw=1.5, z=5)

    # S_omega
    sxx, syy, sww, shh = X + 560, Y + 190, 250, 60
    rbox(b, sxx, syy, sww, shh, TEAL_SOFT, TEAL_EDGE, lw=1.6, r=12, z=3)
    shield(b, sxx + 28, syy + shh / 2, 22, TEAL, z=6)
    txt(b, sxx + 50, syy + shh / 2, "S\u03c9: Post-Safety Gate", size=10.0, color=TEAL,
        weight="bold", ha="left", z=6)
    arrow(b, (fx + fw * 0.5, fy), (sxx + sww * 0.5, syy + shh), color="#1F2937",
          lw=1.5, z=5)

    # decisions
    dx, dy = X + 480, Y + 120
    diamond(b, dx, dy, 120, 76, "#FFFFFF", BLUE_EDGE, "Refine?", fs=10.0)
    chip(b, X + 330, dy, 120, 44, "SKIP", "(no useful ROI)",
         "#FFFFFF", BLUE_EDGE, BLUE, fs=9.4, subfs=8.0)
    chip(b, X + 560, dy, 130, 44, "REFINE", "(beneficial)",
         GREEN_SOFT, GREEN_EDGE, GREEN, fs=9.4, subfs=8.0)
    ax2, ay2 = X + 800, Y + 120
    diamond(b, ax2, ay2, 110, 72, TEAL_SOFT, TEAL_EDGE, "Accept?", fs=10.0)
    chip(b, X + 690, ay2, 108, 42, "ACCEPT", "(use refinement)",
         GREEN_SOFT, GREEN_EDGE, GREEN, fs=9.0, subfs=7.6)
    chip(b, X + 862, ay2, 120, 42, "REJECT", "(fallback to Pg)",
         ORANGE_SOFT, ORANGE_EDGE, ORANGE, fs=9.0, subfs=7.6)
    arrow(b, (bxx + bww * 0.6, byy + bhh), (dx, dy + 38), color="#1F2937",
          lw=1.4, z=5)
    arrow(b, (dx - 60, dy), (X + 390, dy), color=BLUE, lw=1.5, z=5)
    arrow(b, (dx + 60, dy), (X + 560, dy), color=GREEN, lw=1.5, z=5)
    arrow(b, (sxx + sww * 0.7, syy), (ax2, ay2 + 36), color="#1F2937", lw=1.4, z=5)
    arrow(b, (ax2 - 55, ay2), (X + 744, ay2), color=GREEN, lw=1.5, z=5)
    arrow(b, (ax2 + 55, ay2), (X + 922, ay2), color=ORANGE, lw=1.5, z=5)

    # ROI composition
    ccx, ccy, ccw, cch = X + 300, Y + 40, 250, 100
    rbox(b, ccx, ccy, ccw, cch, GREEN_SOFT, GREEN_EDGE, lw=1.6, r=12, z=3)
    txt(b, ccx + ccw / 2, ccy + cch - 26, "ROI composition", size=9.6,
        color=GREEN, weight="bold", z=6)
    txt(b, ccx + ccw / 2, ccy + cch - 43, "(insert refined local mask)",
        size=8.4, color=GREEN, weight="bold", z=6)
    mask_tile(b, ccx + 16, ccy + 14, 52, 44, SAMPLES / "ISIC" / "04_global_probability.png",
              ec="#1A1A1A", lw=1.1, z=5)
    txt(b, ccx + 96, ccy + 36, "+", size=12.0, color=INK, weight="bold", z=7)
    roi_mask_tile(b, ccx + 114, ccy + 14, 52, 44, key="ISIC", ec="#1A1A1A",
                  lw=1.1, z=5)
    arrow(b, (ccx + 172, ccy + 36), (ccx + 190, ccy + 36), color="#1F2937",
          lw=1.3, z=7)
    mask_tile(b, ccx + 194, ccy + 14, 42, 44, SAMPLES / "ISIC" / "07_final_segmentation.png",
              ec="#1A1A1A", lw=1.1, z=5)

    # final
    fox, foy, fow, foh = X + 620, Y + 40, 330, 56
    rbox(b, fox, foy, fow, foh, "#0B4E9B", "#0B4E9B", lw=1.0, r=12, z=5)
    mask_tile(b, fox + 12, foy + 9, 40, 38, SAMPLES / "ISIC" / "07_final_segmentation.png",
              ec="#FFFFFF", lw=1.0, z=6)
    txt(b, fox + 64, foy + foh / 2, "ReMedFiLM Final Segmentation  P\u0302",
        size=10.0, color="white", weight="bold", ha="left", z=7)

    elbow(b, [(X + 744, ay2 - 21), (X + 744, ccy + cch * 0.5), (ccx + ccw, ccy + cch * 0.5)],
          color=GREEN, lw=1.6, z=5)
    elbow(b, [(ccx + ccw / 2, ccy), (ccx + ccw / 2, foy + foh + 12),
              (fox + 34, foy + foh + 12), (fox + 34, foy + foh)],
          color=GREEN, lw=1.6, z=5)
    elbow(b, [(X + 922, ay2 - 21), (X + 922, foy + foh * 0.55), (fox + fow, foy + foh * 0.55)],
          color=ORANGE, lw=1.6, z=5)
    elbow(b, [(X + 330, dy - 22), (X + 330, foy + foh * 0.18), (fox, foy + foh * 0.18)],
          color=BLUE, lw=1.6, z=5)

    # mini legend
    rbox(b, X + 12, Y + 620, 300, 44, "#FFFFFF", "#C7CEDB", lw=1.1, r=9, z=4)
    txt(b, X + 24, Y + 642, "\u2192 inference flow", size=8.4, color=NAVY,
        ha="left", z=6)
    b.ax.plot([X + 20, X + 60], [Y + 642, Y + 642], color=NAVY, linewidth=1.6,
              zorder=7, solid_capstyle="round")
    arrow(b, (X + 52, Y + 642), (X + 64, Y + 642), color=NAVY, lw=1.6, z=7, head=5.0)
    return b


def main():
    print("building ReMedFiLM methodology figures ...")
    b = build_full()
    b.save(HERE / "remedfilm_full_methodology", formats=("svg", "png", "pdf"))
    b.close()

    print("building compact single-column variant ...")
    b = build_compact()
    b.save(HERE / "remedfilm_methodology_compact", formats=("svg", "png"))
    b.close()
    print("done.")


if __name__ == "__main__":
    main()
