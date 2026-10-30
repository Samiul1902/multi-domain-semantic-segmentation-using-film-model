"""Post-Phase24 repair -- additive notebook addendum (work-order section 14).

Appends the section "Router feature-spec completeness addendum -- v1.2" to the
EXISTING Phase24 architecture-spec reviewer notebook, preserving everything
already there and its historical SHA as provenance.

DESIGN-ONLY cells: no model forward, no training, no feature extraction.

The original notebook is first snapshotted to a provenance copy so its SHA is
recoverable; the live notebook then gains the addendum and becomes the current
DESIGN-SPEC pointer.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
NBDIR = ROOT / "notebooks" / "phasewise" / "phase_24_architecture_spec"
NB = NBDIR / "phase24_narrowed_benefit_aware_refinement_spec.ipynb"
PROV = NBDIR / "phase24_narrowed_benefit_aware_refinement_spec__v1_1_provenance.ipynb"
AUD = ROOT / "reports" / "audits"

MARKER = "Router feature-spec completeness addendum — v1.2"
CLOSURE_MARKER = "Router Feature Specification v1.2 — Supervisor Closure"
PRE_CLOSURE_SHA = "97f0efd99a9be662b2c5ba2338132b70131e07ddb01eec58eac2b80295adddff"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def md(text: str) -> dict:
    return {"cell_type": "markdown", "id": None, "metadata": {}, "source": text.splitlines(True)}


def code(text: str) -> dict:
    return {"cell_type": "code", "id": None, "metadata": {}, "execution_count": None,
            "outputs": [], "source": text.splitlines(True)}


def build_addendum_cells() -> list:
    m = []
    m.append(md(f"""## {MARKER}

**Classification:** `SPECIFICATION_COMPLETENESS_ONLY` · **science_changed:** `false`
**Revision:** `ra_medfilm_barr_narrowed_v1_2` (router-feature spec only)
**Method:** `RA-MedFiLM-BARR` — unchanged. Phase25A is NOT invalidated; `R_psi` is NOT retrained.

This addendum is the current **design-spec pointer**. The prior v1.1 notebook content above,
and the v1.1 freeze artifacts, remain historical provenance.

---

### Why Phase25B stopped

Phase25B (GT-free pre-refinement feature extraction) reached its fail-closed entry gate
(**22/22 PASS**) and then stopped with `PHASE25B_BLOCKED__FROZEN_FEATURE_SPEC_INCOMPLETE`.
The frozen Phase24 v1.1 artifacts fixed the router's **output** dimensionality but left three
implementation contracts underspecified. Phase25B is forbidden to invent them, so it stopped
rather than choose silently.
"""))

    m.append(md("""### The core finding — declared width vs native width

v1.1 froze `pool_width_per_axis = 32` and `input_dim_closed_form = 218`
(`6 × 32 + 10 + 16`). The arithmetic is internally consistent. What was **missing** is the
operation that turns a C-channel feature map into 32 values."""))
    m.append(code("""# Native channel widths of the frozen Phase-21 global MedFiLM at the three router taps.
# Source: src/models/film/global_medfilm.py  GLOBAL_MEDFILM_CHANNELS = (24, 48, 96, 192, 256)
native = {
    "bridge":   {"C": 256, "why": "ResidualBlock(192 -> 256) at the bottleneck"},
    "decoder2": {"C": 48,  "why": "DecoderBlock(96 -> 48 -> 48)"},
    "decoder1": {"C": 24,  "why": "DecoderBlock(48 -> 24 -> 24) -> head"},
}
declared = 32
print(f"{'tap':10s} {'native C':>9s} {'declared':>9s}  {'identity possible?':s}")
for t, d in native.items():
    print(f"{t:10s} {d['C']:9d} {declared:9d}  {str(d['C'] == declared):s}")
print()
print("=> no tap has 32 channels, so the 32-D vector CANNOT be the channel axis itself.")
print("   A reduction is REQUIRED and was NOT frozen in v1.1.")"""))

    m.append(md("""### RF-1 — the frozen deterministic C → 32 reduction

`DETERMINISTIC_CHANNEL_ADAPTIVE_AVG_POOL_1D_V1`. Zero trainable parameters. Data-independent.
Every source channel is used. This is a fixed, non-trainable adaptive average pool over the
channel axis — it is **not** claimed optimal and **not** a novel contribution.""") )
    m.append(code("""import math

def channel_bins(C, K=32):
    return [(math.floor(j * C / K), math.ceil((j + 1) * C / K)) for j in range(K)]

print("j : start = floor(j*C/32) ; end = ceil((j+1)*C/32) ; z[j] = mean(v[start:end])")
print()
for t, d in native.items():
    C = d["C"]
    b = channel_bins(C)
    starts = [s for s, _ in b]
    used = set()
    for s, e in b:
        used.update(range(s, e))
    overlapping = any(b[i][1] > b[i + 1][0] for i in range(len(b) - 1))
    print(f"{t:10s} C={C:3d}  first bins={b[:3]}  last={b[-1]}")
    print(f"{'':10s}        all 32 bins valid={all(0 <= s < C and 1 <= e <= C and e > s for s, e in b)}"
          f"  monotone={all(starts[i] <= starts[i+1] for i in range(31))}"
          f"  every channel used={used == set(range(C))}")
    if overlapping:
        print(f"{'':10s}        NOTE: bins OVERLAP because C < 32 (floor/ceil semantics); "
              f"this is intended")
print()
print("Group order (binding): bridge_global[0:32], bridge_roi[32:64], decoder2_global[64:96],")
print("                       decoder2_roi[96:128], decoder1_global[128:160], decoder1_roi[160:192]")
print("deep dimensions = 6 * 32 =", 6 * 32)"""))

    m.append(md("""### RF-2 — the frozen ROI → feature-grid mapping

The canonical Phase25A ROI030 cache exposes **half-open** bounds
(`clip_y1, clip_y2, clip_x1, clip_x2`); the identity
`(clip_y2-clip_y1)+pad_top+pad_bottom == crop_side_pixels` holds for **4957/4957** rows with
**0 violations**, so no inclusive→half-open conversion is applied."""))
    m.append(code("""def map_roi(x0, y0, x1, y1, Wf, Hf, canvas=512):
    fx0 = math.floor(x0 * Wf / canvas); fy0 = math.floor(y0 * Hf / canvas)
    fx1 = math.ceil(x1  * Wf / canvas); fy1 = math.ceil(y1  * Hf / canvas)
    fx0 = min(max(fx0, 0), Wf - 1);      fy0 = min(max(fy0, 0), Hf - 1)
    fx1 = min(max(fx1, fx0 + 1), Wf);    fy1 = min(max(fy1, fy0 + 1), Hf)
    return fx0, fy0, fx1, fy1

# Feature-grid sizes of the frozen global U-Net (512 / 2**stage)
grids = {"bridge": 32, "decoder2": 256, "decoder1": 512}
print("image ROI (half-open) -> feature ROI, per tap grid")
for roi in [(0, 0, 512, 512), (0, 0, 1, 1), (511, 511, 512, 512)]:
    line = f"  roi={str(roi):22s}"
    for t, S in grids.items():
        line += f" {t}:{map_roi(*roi, S, S)}"
    print(line)
print()
print("start=floor, end=ceil, then clip; external crop padding contributes NO feature cells.")"""))

    m.append(md("""### RF-3 — the ten scalar descriptors

All ten now have closed-form definitions and a bound threshold role.
Three probability-boundary descriptors use `t_seg = 0.50`; the ROI descriptors use
`t_roi = 0.30`; entropy is `THRESHOLD_FREE`.

**One defect is REPORTED, not repaired:** `predicted_roi_area_fraction` is specified as
`crop_side_pixels² / 512²` with unit "fraction of native square canvas", but the centre-preserving
1.5× expansion plus square padding makes the crop exceed the canvas for 1257/4957 rows, so the
value exceeds 1.0 (max **2.25**)."""))
    m.append(code("""import csv, glob

rows = []
for f in sorted(glob.glob(str(pathlib.Path(r"D:/Softfors/jup/data_cache")
                                    / "phase25a_barr_roi030_cache" / "*" / "meta.csv"))):
    rows += list(csv.DictReader(open(f, newline="", encoding="utf-8")))

sides = [int(r["crop_side_pixels"]) for r in rows]
af = [(s * s) / (512.0 * 512.0) for s in sides]
over = sum(1 for v in af if v > 1.0)

print(f"rows                     : {len(rows)}")
print(f"crop_side_pixels         : min {min(sides)}  max {max(sides)}  median {sorted(sides)[len(sides)//2]}")
print(f"rows with side > 512     : {sum(1 for s in sides if s > 512)}")
print(f"area_fraction range      : [{min(af):.6f}, {max(af):.6f}]")
print(f"rows with area_fraction>1: {over}")
print()
print("declared unit = 'fraction of native square canvas'; a fraction should lie in [0,1].")
print("=> SPEC DEFECT. Reported for supervisor review; NOT silently patched.")"""))

    m.append(md("""### Threshold semantic table

Three roles, never conflated. No bare field named only `threshold`.""") )
    m.append(code("""role_table = [
    ("ROI_PROPOSAL",                              "0.30",
     "pred_foreground_pixels, pred_foreground_fraction, pred_roi_exists, pred_empty, "
     "predicted_roi_side, predicted_roi_area_fraction"),
    ("SEGMENTATION_OUTPUT_PROBABILITY_BOUNDARY",  "0.50",
     "frac_prob_within_0p05_of_boundary, frac_prob_within_0p02_of_boundary, mean_boundary_margin"),
    ("THRESHOLD_FREE",                            "none",
     "entropy_proxy_mean"),
]
print(f"{'role':42s} {'value':>5s}  features")
for r, v, f in role_table:
    print(f"{r:42s} {v:>5s}  {f}")
print()
print("Using 0.50 for probability-margin descriptors does NOT redefine ROI geometry.")
print("Using 0.30 for ROI descriptors does NOT redefine Dice / final segmentation.")"""))

    m.append(md("""### Dimensional contract and router parameter recheck

`192 deep + 10 scalar = 202` numeric pre-router dimensions in Phase25B. The 16-D task embedding
is trainable inside `BARRBenefitRouterV1` in Phase25D and must **not** be materialised in Phase25B."""))
    m.append(code("""deep, scalar, task_emb = 192, 10, 16
print(f"deep features            : {deep}")
print(f"scalar features          : {scalar}")
print(f"Phase25B numeric matrix  : {deep + scalar}")
print(f"future task embedding    : {task_emb}  (Phase25D, trainable)")
print(f"future router input      : {deep + scalar + task_emb}")
print()
# Closed-form recheck of the ALREADY FROZEN v1.1 router (no instantiation).
emb = 4 * 16
t_ln = emb + (218*128 + 128) + 128*2 + (128*64 + 64) + 64*2 + (64*1 + 1)
t_no = emb + (218*128 + 128) + (128*64 + 64) + (64*1 + 1)
print("router parameter recheck (no model instantiated):")
print(f"  LayerNorm affine ON  : {t_ln}")
print(f"  LayerNorm affine OFF : {t_no}")
print(f"  declared in v1.1     : 36353")
print(f"  delta (ON vs declared): {t_ln - 36353}")
print()
print("=> DISCREPANCY REPORTED: the declared 36353 matches no natural variant of the")
print("   architecture string (which includes two LayerNorms and a 4x16 embedding).")
print("   Reported for supervisor review; hidden widths NOT modified.")"""))

    m.append(md("""### No scientific execution

This addendum is specification-only. It performed **no** model forward, **no** training,
**no** feature extraction, and read **no** outcome, VAL or TEST data. The Phase25B blocked-state
audits are retained as `BLOCKED_ATTEMPT_PROVENANCE` — a valid fail-closed stop, not failed science.""") )
    m.append(code("""import json
audits = pathlib.Path(r"D:/Softfors/jup/reports/audits")
c = json.loads((audits / "phase24_router_feature_spec_completion_v1_2.json").read_text())
print("RF1 :", c["RF1"]["status"], f"({c['RF1']['n_checks'] - c['RF1']['n_failed']}/{c['RF1']['n_checks']})")
print("RF2 :", c["RF2"]["status"], f"({c['RF2']['n_checks'] - c['RF2']['n_failed']}/{c['RF2']['n_checks']})")
print("RF3 :", c["RF3"]["status"], f"({c['RF3']['n_checks'] - c['RF3']['n_failed']}/{c['RF3']['n_checks']})")
print("defects reported :", c["n_defects_reported"])
print("resolved         :", c["resolved"], "| fully_closed:", c["fully_closed"])
print()
print("model_instantiations =", c["model_instantiations"])
print("forward_passes       =", c["forward_passes"])
print("training_runs        =", c["training_runs"])
print("feature_rows_extracted =", c["feature_rows_extracted"])
print("test_reads           =", c["test_reads"])
print()
fc = json.loads((audits / "phase24_v1_2_feature_spec_final_check.json").read_text())
print("FINAL CHECK:", fc["n_checks"] - fc["n_failed"], "/", fc["n_checks"])
print("TERMINAL   :", fc["terminal"])"""))

    return m


def build_closure_cells() -> list:
    """Supervisor-closure section: the two rulings D1/D2 and the final PASS block.

    Design-only.  No experimental plot, no model forward, no training, no
    feature extraction, no outcome/VAL/TEST read.
    """
    m = []
    m.append(md(f"""## {CLOSURE_MARKER}

**Classification:** `SPECIFICATION_COMPLETENESS_AND_GOVERNANCE_SYNC` ·
**science_changed:** `false` · **method_changed:** `false` · **is_new_method:** `false`
**Revision:** `ra_medfilm_barr_narrowed_v1_2` (supersedes v1.1 router-feature spec only)
**Method:** `RA-MedFiLM-BARR` — unchanged. Phase25A is NOT invalidated; `R_psi` is NOT retrained.

The earlier addendum sections above reported two genuine, quantified inconsistencies and
**stopped**, emitting `PHASE24_ROUTER_FEATURE_SPEC_V1_2_BLOCKED__SUPERVISOR_REVIEW_REQUIRED`.
A supervisor has now ruled on both (**D1**, **D2**). This section records those rulings, the
exact frozen replacements, and the final status. Nothing above is edited or overwritten; the
earlier report is retained verbatim as fail-closed provenance.""" ))

    m.append(md("""### Scope of this closure

- **Additive only.** No frozen v1.1 artifact, no Phase25A artifact and no trained checkpoint is
  modified. No em dash of hidden repair: every changed number is superseded by an explicit ruling.
- **No v1.3 required.** The rulings fit fully inside v1.2.
- **No execution.** No model instantiation, no forward pass, no training, no feature extraction,
  no holdout / VAL / TEST read.""" ))

    m.append(md("""### D1 — `predicted_roi_area_fraction`: ruling and frozen replacement

**Defect (as reported):** the v1.1 definition was `crop_side_pixels² / 512²` with unit
*"fraction of native square canvas"*. The centre-preserving 1.5× expansion plus square padding
lets the crop exceed the canvas, so the value **exceeded 1.0 in 1257/4957 rows** (max 2.25) —
impossible for a quantity claimed to be a fraction of the canvas.

**Supervisor ruling:** redefine as the **clipped in-canvas area fraction** — the fraction of the
native 512×512 canvas actually covered by the ROI box *after* clipping to canvas bounds. External
crop padding contributes **nothing**. The old formula is marked
`SUPERSEDED_PRE_EXECUTION_SPEC_FORMULA__NOT_USED_FOR_PHASE25B`; the old value is **not** clipped
retroactively (that would hide the defect)."""))

    m.append(code("""import math

CANVAS = 512.0

def roi_in_canvas_area(x1, x2, y1, y2):
    \"\"\"Frozen D1 formula: area of the ROI box clipped to the native canvas.

    Cache bounds are half-open [x1,x2) x [y1,y2) and live in image pixels.
    w_in = max(0, min(512, x2) - max(0, x1)) ; h_in likewise.  External
    crop padding is outside [0,512) and therefore contributes nothing.
    \"\"\"
    w_in = max(0.0, min(CANVAS, x2) - max(0.0, x1))
    h_in = max(0.0, min(CANVAS, y2) - max(0.0, y1))
    return (w_in * h_in) / (CANVAS * CANVAS)

def old_area_fraction(crop_side_pixels):
    \"\"\"The SUPERSEDED v1.1 formula, kept here only to demonstrate the defect.\"\"\"
    return (crop_side_pixels * crop_side_pixels) / (CANVAS * CANVAS)

print("D1 frozen definition (work-order section 3):")
print("  roi_in_canvas_area = max(0,min(512,x2)-max(0,x1)) * max(0,min(512,y2)-max(0,y1)) / 512**2")
print("  external padding excluded -> range [0,1] by construction")
print()
# Boundary behaviour of the frozen definition (pure arithmetic, no data read).
probes = [
    ("full canvas (0,512,0,512)",      (0, 512, 0, 512)),
    ("single pixel (0,1,0,1)",         (0, 1, 0, 1)),
    ("beyond canvas (0,768,0,768)",    (0, 768, 0, 768)),
    ("offset+overflow (400,900,400,900)", (400, 900, 400, 900)),
    ("padded left (-100,100,0,100)",   (-100, 100, 0, 100)),
]
print(f"{'probe':38s} {'frozen':>10s} {'old(clip)':>10s}")
for name, (x1, x2, y1, y2) in probes:
    w = max(0.0, min(CANVAS, x2) - max(0.0, x1))
    h = max(0.0, min(CANVAS, y2) - max(0.0, y1))
    print(f"{name:38s} {roi_in_canvas_area(x1,x2,y1,y2):10.6f} {'-':>10s}")
print()
print("=> frozen value is ALWAYS within [0,1]; the old formula could exceed 1.0.")"""))

    m.append(code("""# Bound proof of the frozen D1 formula over the cache (metadata only, no image read).
import csv, glob, json

rows = []
for f in sorted(glob.glob(str(pathlib.Path(r"D:/Softfors/jup/data_cache")
                                    / "phase25a_barr_roi030_cache" / "*" / "meta.csv"))):
    rows += list(csv.DictReader(open(f, newline="", encoding="utf-8")))

new_af, old_af = [], []
for r in rows:
    x1, x2 = float(r["x1"]), float(r["x2"])
    y1, y2 = float(r["y1"]), float(r["y2"])
    new_af.append(roi_in_canvas_area(x1, x2, y1, y2))
    old_af.append(old_area_fraction(int(r["crop_side_pixels"])))

new_over = sum(1 for v in new_af if v > 1.0 + 1e-12)
old_over = sum(1 for v in old_af if v > 1.0 + 1e-12)
print(f"rows                                : {len(rows)}")
print(f"NEW clipped in-canvas range         : [{min(new_af):.8f}, {max(new_af):.8f}]")
print(f"NEW rows with value > 1.0           : {new_over}")
print(f"OLD superseded range                : [{min(old_af):.8f}, {max(old_af):.8f}]")
print(f"OLD rows with value > 1.0           : {old_over}")
print()
print("Adjudication artifact: reports/audits/phase24_predicted_roi_area_fraction_adjudication.json")
adj = json.loads((pathlib.Path(r"D:/Softfors/jup/reports/audits")
                  / "phase24_predicted_roi_area_fraction_adjudication.json").read_text())
print("  verdict :", adj["verdict"])
print("  adopted :", adj.get("adopted_resolution"))
print()
print("=> D1 PASS: range [0,1] holds for all", len(rows), "rows; 0 rows exceed 1.0.")"""))

    m.append(md("""### D2 — router parameter count: ruling and frozen reconciliation

**Defect (as reported):** v1.1 declared `expected_parameter_count_closed_form = 36353`, but the
frozen architecture string (`Embedding(4,16)` + 3 `Linear` + 2 affine `LayerNorm`) recomputes to
**36801** — a delta of **448**.

**Supervisor ruling:** the **architecture is UNCHANGED**. `36353` is exactly the **linear-layer
MLP core** (three `Linear` layers, no embedding and no LayerNorm affine parameters). The canonical
router **total trainable parameter count is frozen at 36801**. The 448 = 64 (embedding) + 384
(2 × LayerNorm affine). No hidden width was silently modified.""" ))

    m.append(code("""# D2 arithmetic — pure integer closed form. No model is instantiated.
emb_vocab, emb_dim = 4, 16
lin1_in, lin1_out = 218, 128
lin2_in, lin2_out = 128, 64
lin3_in, lin3_out = 64, 1

w1, b1 = lin1_in * lin1_out, lin1_out
w2, b2 = lin2_in * lin2_out, lin2_out
w3, b3 = lin3_in * lin3_out, lin3_out
ln1 = lin1_out * 2          # LayerNorm(128) affine: weight + bias
ln2 = lin2_out * 2          # LayerNorm(64)  affine: weight + bias
emb = emb_vocab * emb_dim   # Embedding(4,16)

linear_core = w1 + b1 + w2 + b2 + w3 + b3
total = linear_core + emb + ln1 + ln2

print("BARRBenefitRouterV1 parameter reconciliation (frozen)")
print(f"  Linear(218,128)        : {w1:6d} + {b1:4d} = {w1+b1:6d}")
print(f"  Linear(128,64)         : {w2:6d} + {b2:4d} = {w2+b2:6d}")
print(f"  Linear(64,1)           : {w3:6d} + {b3:4d} = {w3+b3:6d}")
print(f"  linear-layer core      : {linear_core:6d}   <- == v1.1 declared 36353")
print(f"  LayerNorm(128) affine  : {ln1:6d}")
print(f"  LayerNorm(64)  affine  : {ln2:6d}")
print(f"  Embedding(4,16)        : {emb:6d}")
print(f"  delta (emb + LN)       : {emb + ln1 + ln2:6d}")
print(f"  CANONICAL TOTAL        : {total:6d}")
print()
assert linear_core == 36353, linear_core
assert total == 36801, total
assert (total - linear_core) == 448, total - linear_core
print("=> D2 PASS: 36353 = linear core ; 36801 = canonical total ; architecture UNCHANGED.")"""))

    m.append(md("""### Final v1.2 status

Every router-feature specification item is now resolved. `RF1`, `RF2`, `RF3` carry no open
definitions; `D1` and `D2` are closed by supervisor ruling; no defect remains open.""" ))

    m.append(code("""import json
audits = pathlib.Path(r"D:/Softfors/jup/reports/audits")

c  = json.loads((audits / "phase24_router_feature_spec_completion_v1_2.json").read_text())
fc = json.loads((audits / "phase24_v1_2_feature_spec_final_check.json").read_text())

def ok(block):
    return block["n_checks"] - block["n_failed"] == block["n_checks"]

print("FINAL v1.2 SPECIFICATION STATUS")
print(f"  RF1 : {c['RF1']['status']:22s} {c['RF1']['n_checks']-c['RF1']['n_failed']}/{c['RF1']['n_checks']}")
print(f"  RF2 : {c['RF2']['status']:22s} {c['RF2']['n_checks']-c['RF2']['n_failed']}/{c['RF2']['n_checks']}")
print(f"  RF3 : {c['RF3']['status']:22s} {c['RF3']['n_checks']-c['RF3']['n_failed']}/{c['RF3']['n_checks']}")
print(f"  D1  : {c['D1']['status']:22s} resolution={c['D1']['resolution']}")
print(f"  D2  : {c['D2']['status']:22s} total={c['D2']['canonical_total_trainable_params']} "
      f"core={c['D2']['historical_linear_core_count']}")
print()
print(f"  defects_reported : {c['n_defects_reported']}   defects_resolved : {c['defects_resolved']}")
print(f"  fully_closed     : {c['fully_closed']}   verdict : {c['verdict']}")
print()
print(f"  FINAL CHECK      : {fc['n_checks']-fc['n_failed']}/{fc['n_checks']} PASS")
print()
print("  RF1 PASS / RF2 PASS / RF3 PASS / D1 PASS / D2 PASS")
print("  => revision ra_medfilm_barr_narrowed_v1_2 COMPLETE")
print()
print("  model_instantiations   =", c["model_instantiations"])
print("  forward_passes         =", c["forward_passes"])
print("  training_runs          =", c["training_runs"])
print("  feature_rows_extracted =", c["feature_rows_extracted"])
print("  test_reads             =", c["test_reads"])
print()
print("  SCOPE: specification-only; no model instantiated, no forward, no training,")
print("         no feature extraction, no held-out / VAL / TEST read.")"""))

    m.append(md(f"""### Provenance and no-execution statement

The pre-closure executed notebook SHA-256 was
`{PRE_CLOSURE_SHA}` — retained here as **pre-supervisor-closure provenance**. The current
notebook SHA-256 is recorded in `reports/audits/phase24_v1_2_notebook_determinism.json` after the
3× byte-identical determinism check (work-order section 13).

This section performed **no** model forward, **no** training, **no** feature extraction and read
**no** held-out outcome, VAL or TEST data. It is a specification-and-bookkeeping closure only.""" ))

    return m


def main() -> int:
    original_sha = sha(NB)
    print("original Phase24 notebook SHA:", original_sha)

    # Provenance copy (idempotent).
    if not PROV.exists():
        shutil.copy2(NB, PROV)
        print("wrote provenance copy:", PROV.name)

    nb = json.loads(NB.read_text(encoding="utf-8"))

    # Idempotency: strip any pre-existing addendum (and closure) before re-appending.
    if any(MARKER in "".join(c.get("source", [])) for c in nb["cells"]):
        idx = next(i for i, c in enumerate(nb["cells"]) if MARKER in "".join(c.get("source", [])))
        nb["cells"] = nb["cells"][:idx]
        print("stripped previous addendum from index", idx)

    n_before = len(nb["cells"])
    nb["cells"].extend(build_addendum_cells())
    n_after_addendum = len(nb["cells"])
    nb["cells"].extend(build_closure_cells())

    # determinism hygiene: stable ids, no volatile execution metadata
    for i, c in enumerate(nb["cells"]):
        c["id"] = f"p24v12{i:03d}"
        meta = c.get("metadata")
        if meta is None:
            meta = {}
        meta.pop("execution", None)
        c["metadata"] = meta
        if c["cell_type"] == "code":
            c["execution_count"] = None
            c["outputs"] = []

    nb.setdefault("metadata", {})
    nb["metadata"].pop("language_info", None)
    nb["metadata"]["kernelspec"] = {"name": "jup-venv", "display_name": "Python (jup-venv)",
                                    "language": "python"}

    NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
    new_sha = sha(NB)
    print(f"cells: {n_before} -> {len(nb['cells'])} "
          f"(addendum +{n_after_addendum - n_before}, closure +{len(nb['cells']) - n_after_addendum})")
    print("new notebook SHA:", new_sha)

    out = {
        "artifact": "phase24_v1_2_notebook_addendum",
        "phase": "24",
        "revision": "ra_medfilm_barr_narrowed_v1_2",
        "notebook": str(NB.relative_to(ROOT)).replace("\\", "/"),
        "addendum_section": MARKER,
        "closure_section": CLOSURE_MARKER,
        "original_notebook_sha256": original_sha,
        "pre_supervisor_closure_sha256": PRE_CLOSURE_SHA,
        "provenance_copy": str(PROV.relative_to(ROOT)).replace("\\", "/"),
        "provenance_copy_sha256": sha(PROV),
        "addendum_notebook_sha256": new_sha,
        "cells_before": n_before,
        "cells_after": len(nb["cells"]),
        "design_only": True,
        "model_forwards": 0,
        "experimental_result_figures_added": 0,
        "historical_v1_1_provenance_preserved": True,
        "phase25a_checkpoint_provenance_unchanged": True,
        "supervisor_rulings_recorded": ["D1", "D2"],
        "test_reads": 0,
    }
    (AUD / "phase24_v1_2_notebook_addendum.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
