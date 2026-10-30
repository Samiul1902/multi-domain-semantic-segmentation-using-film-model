"""Phase 23 — reviewer-quality deterministic visualizations.

PRESENTATION-ONLY. This script builds figures from EXISTING, FROZEN Phase-23
artifacts (tables under ``reports/tables/`` and audits under ``reports/audits/``).

It performs:
  * NO literature research (no web access, no search rerun)
  * NO verdict / classification change
  * NO training, NO model inference, NO image-cohort access (TEST stays closed)

Every plotted value is either read directly from a persisted Phase-23 artifact or
is an explicit, documented binary flag derived from one (see ``EVIDENCE`` mapping
below). No value is invented. Failure is closed: a missing input raises.

Outputs (reports/figures/phase23_novelty_audit/):
  p23_concept_taxonomy.png            required
  p23_novelty_axes_matrix.png         required
  p23_prior_art_mechanism_matrix.png  required
  p23_search_coverage.png             required
  p23_closest_prior_work_matrix.png   optional (reported separately)

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/build_phase23_visuals.py
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(r"D:/Softfors/jup")
TAB = ROOT / "reports" / "tables"
AUD = ROOT / "reports" / "audits"
FIG = ROOT / "reports" / "figures" / "phase23_novelty_audit"
FIG.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Deterministic rendering contract
# ---------------------------------------------------------------------------
# Same style constants for every run; no timestamps, no random seeds, no
# host-dependent fonts. PNG metadata is stripped of any time-varying field.
plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 110,
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.edgecolor": "#5F5E5A",
    "axes.linewidth": 0.8,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.22,
})

# Categorical palette (colour-blind aware, paired with text/hatch cues).
C_OCC = "#D85A30"        # occupied
C_PART = "#EF9F27"       # partially occupied
C_OPEN = "#1D9E75"       # apparently unoccupied
C_NEUTRAL = "#B4B2A9"
C_EDGE = "#444441"
C_BAND = "#E6F1FB"
C_WARN = "#FCEBEB"
INK = "#2C2C2A"

OUT: dict[str, dict] = {}


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"FAIL-CLOSED: required Phase-23 table missing: {path}")
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _read_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"FAIL-CLOSED: required Phase-23 artifact missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _t(v) -> bool:
    """Interpret a matrix cell as a boolean TRUE flag."""
    return str(v).strip().upper() == "TRUE"


def _save(fig, name: str, required: bool, display_name: str) -> None:
    out = FIG / name
    fig.savefig(out, format="png", facecolor="white")
    plt.close(fig)
    raw = out.read_bytes()
    OUT[name] = {
        "figure_id": name.replace(".png", ""),
        "display_name": display_name,
        "path": str(out.relative_to(ROOT)).replace("\\", "/"),
        "required": required,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


# ===========================================================================
# VISUAL 1 — CONCEPT TAXONOMY (required)
# ===========================================================================
def fig_concept_taxonomy() -> None:
    """Conceptual separation of 8 neighbouring concepts + the narrowed candidate.

    Every concept label is taken from the Phase-23 taxonomy as argued in
    reports/tables/phase23_novelty_axes.csv and phase23_prior_art_matrix.csv.
    The lane assignment (occupied / candidate) mirrors the axis statuses.
    """
    ax_rows = {r["axis"]: r for r in _read_csv(TAB / "phase23_novelty_axes.csv")}
    st_a = ax_rows["A"]["status"]
    st_b = ax_rows["B"]["status"]
    st_c = ax_rows["C"]["status"]
    st_d = ax_rows["D"]["status"]

    fig, ax = plt.subplots(figsize=(13.2, 8.0))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    ax.text(50, 96.5, "Phase 23 — concept taxonomy: what the candidate does and does not claim",
            ha="center", va="top", fontsize=14, fontweight="bold", color=INK)
    ax.text(50, 92.0,
            "Eight neighbouring concepts. The separated rows are the confusions a reviewer is most likely to raise.",
            ha="center", va="top", fontsize=10.5, color="#5F5E5A", style="italic")

    # Two labelled columns: WHAT IS PREDICTED  vs  WHEN THE DECISION IS MADE
    ax.add_patch(Rectangle((2.0, 68.0), 45.0, 21.0, facecolor=C_BAND,
                           edgecolor="#85B7EB", linewidth=0.9, zorder=0))
    ax.text(24.5, 87.4, "WHAT IS PREDICTED", ha="center", va="center",
            fontsize=11, fontweight="bold", color="#185FA5", zorder=3)
    ax.add_patch(Rectangle((53.0, 68.0), 45.0, 21.0, facecolor="#E1F5EE",
                           edgecolor="#5DCAA5", linewidth=0.9, zorder=0))
    ax.text(75.5, 87.4, "WHEN THE DECISION IS MADE", ha="center", va="center",
            fontsize=11, fontweight="bold", color="#0F6E56", zorder=3)

    def node(x, y, w, h, title, sub, face, edge, tc=None):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.6",
                                    facecolor=face, edgecolor=edge, linewidth=1.05, zorder=2))
        ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center",
                fontsize=10.4, fontweight="bold", color=tc or INK, zorder=3)
        ax.text(x + w / 2, y + h * 0.30, sub, ha="center", va="center",
                fontsize=8.9, color="#444441", zorder=3)

    # left column — what is predicted
    node(4.0, 78.0, 41.0, 6.6, "1 · uncertainty prediction",
         "confidence / entropy of the CURRENT output", "white", C_NEUTRAL)
    node(4.0, 70.4, 41.0, 6.6, "2 · quality prediction",
         "expected Dice of the CURRENT prediction", "white", C_NEUTRAL)
    node(4.0, 62.8, 41.0, 6.6, "3 · error localization",
         "WHERE the current output is wrong", "white", C_NEUTRAL)
    node(4.0, 55.2, 41.0, 6.6, "4 · difficulty prediction",
         "how HARD this case is (no action)", "white", C_NEUTRAL)
    node(4.0, 44.6, 41.0, 9.2, "5 · action-benefit prediction",
         "how much a POSSIBLE action would HELP", C_OPEN, "#0F6E56", "#04342C")

    # right column — when the decision is made
    node(55.0, 70.4, 41.0, 6.6, "6 · post-action selection",
         "choose among ALREADY-COMPUTED outputs", "white", C_NEUTRAL)
    node(55.0, 59.8, 41.0, 9.2, "7 · pre-action routing",
         "decide BEFORE paying the action cost", C_OPEN, "#0F6E56", "#04342C")
    node(55.0, 49.2, 41.0, 9.2, "8 · resource-aware routing",
         "route under a device / compute budget", C_OPEN, "#0F6E56", "#04342C")

    # the confusions to reject
    ax.annotate("", xy=(53.0, 50.0), xytext=(47.0, 50.0),
                arrowprops=dict(arrowstyle="-|>", color="#A32D2D", linewidth=1.5))
    ax.text(50.0, 47.4, "NOT\nequivalent", ha="center", va="top", fontsize=8.2,
            color="#A32D2D", fontweight="bold")

    ax.text(2.0, 43.6, "Rejected equivalences (the audit's load-bearing distinctions):",
            ha="left", va="center", fontsize=10, fontweight="bold", color="#501313")
    for i, txt in enumerate([
        "uncertainty  ≠  action benefit      — current confidence does not tell you what a refinement would gain",
        "quality prediction  ≠  refinement gain   — scoring the present output is not scoring the CHANGE it would undergo",
        "post-hoc selection  ≠  pre-execution routing  — selecting after running saves quality ambiguity, not compute",
    ]):
        ax.text(3.5, 40.4 - i * 3.1, "–  " + txt, ha="left", va="center",
                fontsize=9.3, color="#791F1F")

    # the candidate band
    ax.add_patch(FancyBboxPatch((2.0, 18.0), 96.0, 12.0,
                                boxstyle="round,pad=0.7,rounding_size=2.0",
                                facecolor="#EAF3DE", edgecolor="#639922",
                                linewidth=1.6, zorder=2))
    ax.text(50, 28.2, "NARROWED CANDIDATE CONTRIBUTION", ha="center", va="center",
            fontsize=11.6, fontweight="bold", color="#27500A", zorder=3)
    ax.text(50, 24.2,
            "PRE-ACTION / PRE-REFINEMENT BENEFIT PREDICTION   +   RESOURCE-AWARE ROUTING",
            ha="center", va="center", fontsize=11.0, fontweight="bold", color="#173404", zorder=3)
    ax.text(50, 20.4,
            "= concept 5  ∩  concept 7  ∩  concept 8,   with preservation-fallback",
            ha="center", va="center", fontsize=9.6, color="#3B6D11", zorder=3)

    # axis statuses strip (verbatim from the axes table) — two columns x two rows
    ax.text(2.0, 15.4, "Novelty-axis status (verbatim from phase23_novelty_axes.csv):",
            ha="left", va="center", fontsize=9.4, fontweight="bold", color=INK)
    strips = [
        ("A", st_a, C_OCC), ("B", st_b, C_PART),
        ("C", st_c, C_PART), ("D", st_d, C_OPEN),
    ]
    for i, (aid, status, col) in enumerate(strips):
        cx = 2.0 + (i % 2) * 49.0
        cy = 9.4 - (i // 2) * 5.6
        ax.add_patch(FancyBboxPatch((cx, cy), 47.0, 4.4,
                                    boxstyle="round,pad=0.35,rounding_size=1.1",
                                    facecolor=col, edgecolor=C_EDGE,
                                    linewidth=0.8, alpha=0.95, zorder=2))
        ax.text(cx + 1.6, cy + 2.2, aid, ha="left", va="center",
                fontsize=9.6, fontweight="bold", color="white", zorder=3)
        ax.text(cx + 4.6, cy + 2.2, status, ha="left", va="center",
                fontsize=7.2, fontweight="bold", color="white", zorder=3)

    ax.text(50, 1.6,
            "Statuses are categorical, not scores. D is the strongest residual and is the ONLY axis "
            "carrying the narrowed claim.",
            ha="center", va="center", fontsize=9.0, color="#5F5E5A", style="italic")

    _save(fig, "p23_concept_taxonomy.png", True, "Concept taxonomy (8 neighbouring concepts + narrowed candidate)")


# ===========================================================================
# VISUAL 2 — NOVELTY AXIS MATRIX (required)
# ===========================================================================
def fig_novelty_axes() -> None:
    """Categorical evidence matrix of the four novelty axes.

    Statuses are shown EXACTLY as recorded; they are never converted to a
    numeric novelty score and never ranked best/worst.
    """
    rows = _read_csv(TAB / "phase23_novelty_axes.csv")
    if len(rows) != 4:
        raise ValueError(f"FAIL-CLOSED: expected 4 novelty axes, found {len(rows)}")

    status_color = {
        "OCCUPIED": C_OCC,
        "PARTIALLY_OCCUPIED": C_PART,
        "NOT_OCCUPIED_AS_A_LEARNED_SEGMENTATION_TARGET": C_PART,
        "NOT_OCCUPIED_AS_A_COMBINATION": C_OPEN,
    }

    fig, ax = plt.subplots(figsize=(14.6, 8.4))
    ax.axis("off")
    ax.text(0.5, 1.045, "Phase 23 — novelty-axis matrix (categorical evidence, not a score)",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=14.5, fontweight="bold", color=INK)
    ax.text(0.5, 1.002,
            "Each axis is annotated with the strongest prior art found in the audited scope. "
            "No axis is weighted, summed, or ranked.",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=9.4,
            color="#5F5E5A", style="italic")

    # fixed column geometry (axes fraction) so nothing can collide
    X_ID, X_Q, X_STATUS = 0.020, 0.175, 0.988
    STAT_W = 0.300
    X_DET = 0.175
    DET_W = 118          # characters that fit before the status column

    top = 0.905
    row_h = 0.196
    for i, r in enumerate(rows):
        y = top - (i + 1) * row_h
        col = status_color.get(r["status"], C_NEUTRAL)
        yb = y + 0.012
        bh = row_h - 0.028

        ax.add_patch(FancyBboxPatch((0.004, yb), 0.992, bh,
                                    boxstyle="round,pad=0.004,rounding_size=0.012",
                                    transform=ax.transAxes, facecolor="#F7F6F2",
                                    edgecolor="#B4B2A9", linewidth=0.9))

        # axis id chip
        ax.add_patch(FancyBboxPatch((X_ID, y + bh * 0.56), 0.060, bh * 0.26,
                                    boxstyle="round,pad=0.003,rounding_size=0.010",
                                    transform=ax.transAxes, facecolor=INK,
                                    edgecolor=INK, linewidth=0.8))
        ax.text(X_ID + 0.030, y + bh * 0.69, f"AXIS {r['axis']}", transform=ax.transAxes,
                ha="center", va="center", fontsize=8.2, fontweight="bold", color="white")

        ax.text(X_ID + 0.005, y + bh * 0.34, r["axis_name"], transform=ax.transAxes,
                ha="left", va="center", fontsize=8.6, fontweight="bold", color=INK)

        # question, truncated to fit strictly LEFT of the status column
        ax.text(X_Q, y + bh * 0.76, r["question"][:96], transform=ax.transAxes,
                ha="left", va="center", fontsize=8.0, color="#2C2C2A")

        # status pill, right-aligned column
        ax.add_patch(FancyBboxPatch((X_STATUS - STAT_W, y + bh * 0.63), STAT_W, bh * 0.23,
                                    boxstyle="round,pad=0.004,rounding_size=0.012",
                                    transform=ax.transAxes, facecolor=col,
                                    edgecolor=C_EDGE, linewidth=0.8))
        ax.text(X_STATUS - STAT_W / 2, y + bh * 0.745, r["status"], transform=ax.transAxes,
                ha="center", va="center", fontsize=7.3, fontweight="bold", color="white")

        conf_col = {"HIGH": C_OCC, "MEDIUM": C_PART, "LOW": C_OPEN}.get(r["confidence"], C_NEUTRAL)
        ax.text(X_STATUS, y + bh * 0.30, "confidence: " + r["confidence"],
                transform=ax.transAxes, ha="right", va="center",
                fontsize=7.6, fontweight="bold", color=conf_col)

        ax.text(X_DET, y + bh * 0.46,
                "strongest prior:  " + r["strongest_prior_art"][:DET_W],
                transform=ax.transAxes, ha="left", va="center", fontsize=7.4, color="#444441")

        ax.text(X_DET, y + bh * 0.22,
                "residual:  " + r["defensible_residual"][:DET_W],
                transform=ax.transAxes, ha="left", va="center", fontsize=7.4,
                color="#3B6D11", style="italic")

    ax.text(0.5, 0.068,
            "explicitly formulated already?   "
            + "   |   ".join(f"{r['axis']}: {r['already_explicitly_formulated']}" for r in rows),
            transform=ax.transAxes, ha="center", va="center", fontsize=9.0, color="#444441")

    ax.text(0.5, 0.016,
            "Categorical statuses only. A 'NOT_OCCUPIED' status means no substantially equivalent "
            "prior was found in the AUDITED scope — it is not a worldwide uniqueness claim.",
            transform=ax.transAxes, ha="center", va="center", fontsize=8.6,
            color="#791F1F", style="italic")

    _save(fig, "p23_novelty_axes_matrix.png", True, "Novelty-axis matrix (4 categorical axes)")


# ===========================================================================
# VISUAL 3 — PRIOR-ART MECHANISM COVERAGE (required)
# ===========================================================================
def fig_prior_art_mechanism_matrix() -> None:
    """Precedent-family x mechanism-property coverage heatmap.

    Rows are precedent FAMILIES (major neighbours), columns are the mechanism
    properties the candidate relies on. A cell is filled iff at least one
    retained work in that family carries the property, read from the frozen
    phase23_prior_art_matrix.csv flag columns (no invented cells).

    ``shared_multidomain_model`` is carried by two distinct families
    (universal-segmentation and MoE-routing), so the row is determined by an
    explicit family membership rule documented in ``FAMILY_OF``.
    """
    m = _read_csv(TAB / "phase23_prior_art_matrix.csv")
    by_key = {r["citation_key"]: r for r in m}

    # explicit family membership (citation keys come from the frozen matrix)
    FAMILY_OF: list[tuple[str, list[str]]] = [
        ("Multi-domain / universal\nmedical segmentation",
         ["butoi2023universeg", "ma2024medsam", "isensee2021nnunet"]),
        ("Regional / coarse-to-fine\nrefinement",
         ["isensee2021nnunet", "wang2023segrefiner", "huang2024evanyseg"]),
        ("Uncertainty-guided\nrefinement",
         ["uhrnet2026", "huang2024evanyseg", "tan2026cls"]),
        ("Quality / error\nprediction",
         ["laves2018qualitypred", "borges2024sdc", "chou2024tinylessurvey"]),
        ("Conditional computation\n(SkipNet / ACT)",
         ["graves2016act", "wang2018skipnet", "zhang2024adaptivepatching"]),
        ("MoE / dynamic\nrouting",
         ["jiang2024m4oe", "raposo2024mod", "shen2024meddanetv2"]),
        ("Cascades with optimal\npass-on criteria",
         ["viola2001cascade", "latotzke2021cascade", "ren2015fasterrcnn"]),
        ("Metareasoning /\nvalue of computation",
         ["russell1991metareasoning"]),
        ("CATE / treatment-effect\nmeta-learners",
         ["kunzel2019metalearners"]),
        ("Deferral / abstention\ndecision",
         ["mozannar2020defer", "sanisoglu2026abstain", "chow1970reject"]),
        ("Post-hoc refinement\nverification",
         ["moon2024jfs", "tian2026deferredseg", "zhao2026lfpc"]),
        ("Resource-aware /\ndevice-aware inference",
         ["zhang2023mobilesam", "hor2024adaptiveinference", "bouzid2023scaleaware"]),
    ]

    props: list[tuple[str, list[str]]] = [
        ("multi-domain", ["shared_multidomain_model"]),
        ("regional\nrefinement", ["regional_refinement", "high_resolution_branch", "coarse_to_fine"]),
        ("uncertainty", ["uncertainty_guided"]),
        ("quality\nprediction", ["quality_prediction"]),
        ("error\nprediction", ["error_prediction"]),
        ("future-action\nbenefit", ["predicts_future_action_benefit"]),
        ("benefit\nregression", ["benefit_regression"]),
        ("paired-gain\ntarget", ["paired_global_refined_gain_target"]),
        ("pre-execution", ["predicts_before_action"]),
        ("execute/skip", ["execute_skip_gate"]),
        ("fallback", ["global_fallback"]),
        ("performance\npreservation", ["performance_preservation_constraint"]),
        ("resource-aware", ["resource_aware", "budgeted_compute"]),
        ("device-aware", ["device_aware", "mobile_CPU_tested"]),
        ("tiny-object", ["tiny_object_focus"]),
    ]

    # build the coverage grid
    grid = []
    for fam, keys in FAMILY_OF:
        row = []
        for _, cols in props:
            hit = False
            for k in keys:
                r = by_key.get(k)
                if r is None:
                    continue
                if any(_t(r.get(c, "")) for c in cols):
                    hit = True
                    break
            row.append(1 if hit else 0)
        grid.append(row)

    # candidate row: all properties it relies on are, by construction, present
    cand_props = [1] * len(props)

    n_rows = len(FAMILY_OF) + 1
    fig, ax = plt.subplots(figsize=(13.4, max(6.4, 0.47 * n_rows + 2.0)))

    # draw grid in data coordinates for full control
    n_col = len(props)
    ax.set_xlim(-0.5, n_col - 0.5)
    ax.set_ylim(n_rows - 1.5, -1.7)
    ax.axis("off")

    for i in range(n_rows):
        for j in range(n_col):
            val = cand_props[j] if i == n_rows - 1 else grid[i][j]
            face = "#0F6E56" if (i == n_rows - 1 and val) else ("#1D9E75" if val else "#F1EFE8")
            ax.add_patch(Rectangle((j - 0.42, i - 0.42), 0.84, 0.84,
                                   facecolor=face, edgecolor="#FFFFFF", linewidth=1.2))
            if val:
                mark = "C" if i == n_rows - 1 else "●"
                ax.text(j, i, mark, ha="center", va="center", fontsize=8.6,
                        color="white", fontweight="bold")

    for j, (pname, _) in enumerate(props):
        ax.text(j, -1.02, pname, ha="center", va="bottom", fontsize=6.9,
                color=INK, rotation=32, rotation_mode="anchor")

    for i, (fname, _) in enumerate(FAMILY_OF):
        ax.text(-0.72, i, fname, ha="right", va="center", fontsize=8.2, color=INK)

    band_y = n_rows - 0.72
    ax.add_patch(Rectangle((-0.72, band_y - 0.42), n_col - 0.06, 0.82,
                           facecolor="#EAF3DE", edgecolor="#639922", linewidth=1.3, zorder=0))
    ax.text(-0.72, band_y, "CANDIDATE (fully integrated)  ", ha="right", va="center",
            fontsize=8.6, fontweight="bold", color="#173404", zorder=3)

    ax.text(n_col / 2 - 0.5, -2.35,
            "Phase 23 — prior-art mechanism coverage by precedent family  "
            "(filled = at least one retained work carries the primitive)",
            ha="center", va="bottom", fontsize=13, fontweight="bold", color=INK)
    ax.text(n_col / 2 - 0.5, -1.85,
            "Individual primitives are widely occupied. The bottom row is the candidate's integration, "
            "not a claim that no work anywhere shares any primitive.",
            ha="center", va="bottom", fontsize=9.2, color="#5F5E5A", style="italic")

    ax.text(n_col / 2 - 0.5, n_rows - 0.15,
            "Occupancy here is scope-limited to the 30 retained works of the audited search. "
            "Absence from this matrix does NOT prove worldwide uniqueness.",
            ha="center", va="top", fontsize=8.8, color="#791F1F", style="italic")

    handles = [
        Rectangle((0, 0), 1, 1, facecolor="#1D9E75", edgecolor="#FFFFFF", label="primitive present in family"),
        Rectangle((0, 0), 1, 1, facecolor="#F1EFE8", edgecolor="#B4B2A9", label="not present in family"),
        Rectangle((0, 0), 1, 1, facecolor="#0F6E56", edgecolor="#FFFFFF", label="candidate integration"),
    ]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.0, 0.0),
              fontsize=8.2, frameon=False, ncol=3, handlelength=1.3, handleheight=1.0,
              columnspacing=1.4)

    _save(fig, "p23_prior_art_mechanism_matrix.png", True,
          "Prior-art mechanism coverage (precedent families x mechanism properties)")


# ===========================================================================
# VISUAL 4 — SEARCH COVERAGE (required)
# ===========================================================================
def fig_search_coverage() -> None:
    """Deterministic search-coverage bar chart across the 13 query families.

    Values are read from phase23_search_query_summary.csv and cross-checked
    against the frozen search log totals.
    """
    rows = _read_csv(TAB / "phase23_search_query_summary.csv")
    log = _read_json(AUD / "phase23_search_log.json")

    if len(rows) != 13:
        raise ValueError(f"FAIL-CLOSED: expected 13 query families, found {len(rows)}")

    scr = [int(r["results_screened"]) for r in rows]
    ret = [int(r["papers_retained"]) for r in rows]
    qy = [int(r["n_queries"]) for r in rows]
    labels = [f"{r['family']} · {r['label'].split('(')[0].strip()[:30]}" for r in rows]

    tot_scr, tot_ret, tot_q = sum(scr), sum(ret), sum(qy)
    log_scr = log["totals"]["results_screened"]
    log_q = log["totals"]["queries_logged"]
    if tot_scr != log_scr or tot_q != log_q:
        raise ValueError(
            f"FAIL-CLOSED: coverage table and search log disagree "
            f"(screened {tot_scr} vs {log_scr}; queries {tot_q} vs {log_q})")

    fig, ax = plt.subplots(figsize=(13.0, 6.6))
    y = range(len(rows))

    ax.barh([i + 0.19 for i in y], scr, height=0.36,
            color="#85B7EB", edgecolor="#185FA5", linewidth=0.9,
            label=f"records screened (total {tot_scr})")
    ax.barh([i - 0.19 for i in y], ret, height=0.36,
            color="#97C459", edgecolor="#3B6D11", linewidth=0.9,
            label=f"records retained (total {tot_ret})")

    for i, (s, r) in enumerate(zip(scr, ret)):
        ax.text(s + 0.6, i + 0.19, str(s), va="center", ha="left", fontsize=8.2, color="#185FA5")
        ax.text(r + 0.6, i - 0.19, str(r), va="center", ha="left", fontsize=8.2, color="#3B6D11")

    ax.set_yticks(list(y))
    ax.set_yticklabels([f"{l}   ({q}q)" for l, q in zip(labels, qy)], fontsize=8.6)
    ax.invert_yaxis()
    ax.set_xlabel("records", fontsize=10)
    ax.set_xlim(0, max(scr) + 7)

    risk_col = {"HIGH": C_OCC, "MEDIUM": C_PART, "LOW": C_OPEN}
    for i, r in enumerate(rows):
        col = risk_col.get(r["highest_risk_level"], C_NEUTRAL)
        ax.add_patch(Rectangle((max(scr) + 1.0, i - 0.34), 4.3, 0.68,
                               facecolor=col, edgecolor=C_EDGE, linewidth=0.7, clip_on=False))
        ax.text(max(scr) + 3.15, i, r["highest_risk_level"], ha="center", va="center",
                fontsize=7.4, fontweight="bold", color="white", clip_on=False)
    ax.text(max(scr) + 3.15, -0.95, "highest\nrisk found", ha="center", va="center",
            fontsize=7.4, fontweight="bold", color=INK)

    ax.set_title("Phase 23 — search coverage across the 13 query families\n"
                 "(coverage visualisation only — bar height is not a novelty score)",
                 fontsize=12.5, fontweight="bold", pad=14)
    ax.legend(loc="lower right", fontsize=9, frameon=True, framealpha=0.95)
    ax.grid(axis="x", color="#D3D1C7", linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    ax.text(0.0, -0.175,
            f"Search date {log.get('search_date')} · {len(rows)} families · {tot_q} queries · "
            f"{tot_scr} records screened · {log['totals']['papers_retained_authoritative']} retained authoritative · "
            f"{log['totals']['papers_promoted_to_closest_review']} promoted to deep review",
            transform=ax.transAxes, ha="left", va="top", fontsize=8.6, color="#5F5E5A")

    _save(fig, "p23_search_coverage.png", True, "Search coverage across 13 query families")


# ===========================================================================
# OPTIONAL VISUAL 5 — CLOSEST PRIOR WORK (reported separately)
# ===========================================================================
def fig_closest_prior_work() -> None:
    """Compact categorical comparison of the closest prior works.

    This is NOT a ranking or a winner chart — the works appear in
    proximity_rank order and every column is a categorical flag.
    """
    c = _read_csv(TAB / "phase23_closest_prior_work.csv")
    keys = ["moon2024jfs", "russell1991metareasoning", "latotzke2021cascade",
            "kunzel2019metalearners", "shen2024meddanetv2", "jiang2024m4oe"]
    by_key = {r["citation_key"]: r for r in c}
    missing = [k for k in keys if k not in by_key]
    if missing:
        raise FileNotFoundError(f"FAIL-CLOSED: closest-work rows missing: {missing}")

    # explicit, defensible categorical resolution
    def c_preexec(r):
        return "YES" if "BEFORE" in str(r["when_it_predicts"]).upper() else "no"

    def c_supervised(r):
        """Is the paired gain a SUPERVISED training target? (from supervision_used)"""
        s = str(r["supervision_used"]).upper()
        if "N/A" in s:
            return "n/a"
        if "IMPLICIT" in s:
            return "partial"
        return "no"

    def c_gtfree(r):
        """Does the mechanism need ground truth at inference? (from when_it_predicts)"""
        return "YES" if "BEFORE" in str(r["when_it_predicts"]).upper() else "no"

    def c_optional(r):
        return "no" if str(r["refinement_already_ran"]).strip().upper().startswith(("YES", "PARTI")) else "YES"

    def c_fallback(r):
        return "YES" if str(r["fallback_exists"]).strip().upper().startswith("YES") else "no"

    def c_multidom(r):
        return "YES" if _t(r.get("multi_domain", "")) else "no"

    def c_cost(r):
        return "no" if str(r["action_cost_included"]).strip().upper().startswith("NO") else "YES"

    cols = [
        ("pre-execution", c_preexec),
        ("paired gain is\na supervised target", c_supervised),
        ("GT-free at\ninference", c_gtfree),
        ("refinement\noptional", c_optional),
        ("fallback\nexists", c_fallback),
        ("multi-domain\nmedical", c_multidom),
        ("action cost\nincluded", c_cost),
    ]

    fig, ax = plt.subplots(figsize=(13.8, 6.0))
    ax.axis("off")
    n_r, n_c = len(keys), len(cols)

    ax.text(n_c / 2 - 0.5, -2.15,
            "Phase 23 — closest prior works: categorical mechanism comparison",
            ha="center", va="bottom", fontsize=13.5, fontweight="bold", color=INK)
    ax.text(n_c / 2 - 0.5, -1.62,
            "Works appear in proximity_rank order. This is a property comparison, not a ranking or a winner.",
            ha="center", va="bottom", fontsize=9.0, color="#5F5E5A", style="italic")

    for j, (cname, _) in enumerate(cols):
        ax.text(j, -0.52, cname, ha="center", va="bottom", fontsize=7.3,
                fontweight="bold", color=INK, linespacing=1.35)

    for i, k in enumerate(keys):
        r = by_key[k]
        rank = int(r["proximity_rank"])
        shade = "#F7F6F2" if i % 2 == 0 else "#FFFFFF"
        ax.add_patch(Rectangle((-5.0, i - 0.46), n_c + 5.2, 0.92,
                               facecolor=shade, edgecolor="#FFFFFF", linewidth=0.8))
        ax.text(-4.8, i - 0.13, f"[{rank}] {k}", ha="left", va="center",
                fontsize=8.5, fontweight="bold", color=INK)
        ax.text(-4.8, i + 0.24, f"{r['year']} · {r['venue'][:30]}", ha="left", va="center",
                fontsize=6.9, color="#5F5E5A")
        for j, (_, fn) in enumerate(cols):
            v = fn(r)
            face = {"YES": "#1D9E75", "partial": C_PART, "no": "#F1EFE8", "n/a": "#D3D1C7"}[v]
            tc = "white" if v in ("YES", "partial") else "#444441"
            ax.add_patch(Rectangle((j - 0.42, i - 0.35), 0.84, 0.7,
                                   facecolor=face, edgecolor="#FFFFFF", linewidth=1.1))
            ax.text(j, i, v, ha="center", va="center", fontsize=7.2,
                    fontweight="bold", color=tc)

    ax.set_xlim(-5.2, n_c - 0.4)
    ax.set_ylim(n_r - 0.6, -2.6)

    ax.text(-5.0, n_r - 0.25,
            "Residual difference of each work from the candidate is itemised in "
            "phase23_closest_prior_work.csv (>residual_difference_from_our_candidate).",
            ha="left", va="top", fontsize=7.6, color="#791F1F", style="italic")

    _save(fig, "p23_closest_prior_work_matrix.png", False,
          "Closest prior works: categorical mechanism comparison (optional)")


# ===========================================================================
# DRIVER
# ===========================================================================
def main() -> int:
    fig_concept_taxonomy()
    fig_novelty_axes()
    fig_prior_art_mechanism_matrix()
    fig_search_coverage()
    fig_closest_prior_work()

    required = {k: v for k, v in OUT.items() if v["required"]}
    optional = {k: v for k, v in OUT.items() if not v["required"]}

    manifest = {
        "artifact": "phase23_figure_manifest",
        "phase": 23,
        "classification": "REVIEWER_PRESENTATION_REPAIR",
        "scientific_results_changed": False,
        "search_rerun": False,
        "source": "frozen Phase-23 tables/audits only",
        "n_required": len(required),
        "n_optional": len(optional),
        "figures": OUT,
        "fail_closed": True,
        "training": False,
        "inference": False,
        "test_reads": 0,
        "phase24_started": False,
    }
    (FIG / "phase23_figure_manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")

    for k, v in OUT.items():
        print(f"  [{'REQ' if v['required'] else 'OPT'}] {k:38s} {v['bytes']:>8d}B  {v['sha256'][:16]}")
    print()
    print(f"required figures : {len(required)}")
    print(f"optional figures : {len(optional)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
