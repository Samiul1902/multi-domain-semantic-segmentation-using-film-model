"""Phase 22 — build the Multi-Domain Scale / Regional-Benefit / Resource-Gap notebook.

Determinism contract (identical to the Phase-21 builder)
--------------------------------------------------------
deterministic cell ids (``p22NNN``) + stripped ``metadata.execution`` + coalesced
stream outputs + fixed pandas Styler uuids (``set_uuid``) + normalised object
memory addresses (``0x...`` -> ``0xADDR``). Three consecutive builds must be
byte-identical.

The notebook performs NO training, NO new model inference, and reads NO TEST data.
Every number is rebuilt from persisted Phase-21/Phase-22 artifacts and every table
is re-derived through the SAME module functions the driver used.

Usage
-----
    ./.venv/Scripts/python.exe scripts/notebooks/build_phase22_notebook.py
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
# NOTE: the canonical folder and notebook filename are FROZEN by the protocol's
# required_outputs list and must match it exactly:
#   notebooks/phasewise/phase_22_resource_gap/phase22_resource_gap_analysis.ipynb
NB_DIR = ROOT / "notebooks/phasewise/phase_22_resource_gap"
NB_PATH = NB_DIR / "phase22_resource_gap_analysis.ipynb"
NB_DIR.mkdir(parents=True, exist_ok=True)

md = lambda s: nbformat.v4.new_markdown_cell(s.strip("\n"))     # noqa: E731
code = lambda s: nbformat.v4.new_code_cell(s.strip("\n"))       # noqa: E731

cells: list = []

# 000 ---------------------------------------------------------------------- #
cells.append(md("""
# Phase 22 — Multi-Domain Scale, Regional-Benefit & Resource Gap Analysis
### A diagnostic, inference-only gap analysis on the frozen Phase-21 reference

| Item | Value |
|---|---|
| Phase | 22 (Stage B, diagnostic) |
| Canonical folder | `notebooks/phasewise/phase_22_resource_gap/` |
| Reference model | frozen Phase-21 **Global MedFiLM** (unchanged, 3,523,001 params) |
| Checkpoint | `checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt` |
| Protocol | `reports/audits/phase22_diagnostic_protocol.json` (frozen before execution) |
| Reference binding | `reports/audits/phase22_phase21_reference_binding.json` (38/38 PASS) |
| Population | the **same 808 VAL cases** as Phase 21 (patient-disjoint) |
| New training | **NONE** — zero optimisers, zero backward passes, zero writes |
| Architecture change | **NONE** |
| Benefit predictor | **NONE trained** (labels are *contracted*, not used) |
| Cohort read | VAL only (plus TRAIN/VAL manifest metadata) |
| TEST | **CLOSED** — 0 image reads, 0 mask reads, 0 inference, 0 visualizations |
| Terminal state | `PHASE22_MULTIDOMAIN_SCALE_REGIONAL_RESOURCE_GAP_ANALYSIS_COMPLETE__PHASE23_ELIGIBLE_NOT_STARTED` |

**What Phase 22 is.** A *gap analysis*: it measures how large the headroom is along three
candidate axes — **input scale**, **regional refinement**, and **conditional compute** —
without proposing, training, or claiming any method. It exists to inform the Phase-24
design, not to pre-empt it.

**What Phase 22 is NOT.** It is **NOT** the RA-MedFiLM-Seg++ model. It contains **NO**
trained router, **NO** learned localizer, **NO** benefit predictor, **NO** architecture
search, **NO** compression/pruning/quantization/distillation, and **NO** Phase-23
literature audit. Phase 23 is **not started**.

**Interpretation guards (binding on every claim in this notebook).**

1. The **ORACLE regional arm uses ground-truth geometry**. It is an **upper bound**. It
   must never be presented as a deployable gain, and no method may be said to "achieve" it.
2. Where a paired CI overlaps zero, the arms are **not separable** and **no ordering** may
   be stated.
3. The reference is the **lightest of the six-model panel**, but ~31.6 G MACs per image is
   **not** a small absolute cost. "Lightest of the panel" must never be reported as "fit
   for constrained deployment."
4. No claim may be phrased as **"X caused +Y"**. Only *"the reference achieved X compared
   with baseline Y"* is permitted.
"""))

# 001 ---------------------------------------------------------------------- #
cells.append(md("## 1. Environment and deterministic setup"))
cells.append(code("""
import sys, json, hashlib, warnings
from pathlib import Path
warnings.filterwarnings("ignore")

ROOT = Path(r"D:/Softfors/jup")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from IPython.display import display, Markdown, Image

AUD = ROOT / "reports/audits"
TAB = ROOT / "reports/tables"
FIG = ROOT / "reports/figures/phase22_resource_gap"

def load(name):
    p = AUD / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None

def sty(df, uid, fmt=None, **kw):
    \"\"\"Deterministic Styler (fixed uuid => SHA-stable notebook output).\"\"\"
    fmt = {**(fmt or {}), **kw}
    return df.style.format(fmt).set_uuid(uid)

def show(fname, width=900):
    \"\"\"Display a required figure from the EXPLICIT figure manifest.

    The manifest (``reports/figures/phase22_resource_gap/phase22_figure_manifest.csv``)
    declares every required figure with ``figure_id, source_path, section, caption,
    semantic_role, expected_to_embed, source_sha256``. This helper is FAIL-CLOSED:
    if a required figure cannot be located, decoded, or PIL-verified it raises, so
    the notebook can never print "figure unavailable" and keep building while
    claiming the reviewer package is complete.

    The frozen on-disk names use the short ``p22_`` prefix while the notebook
    historically referred to them by their ``phase22_`` descriptive names; both
    forms resolve to the same manifest row.
    \"\"\"
    want = fname
    if want.endswith(".png"):
        want = want[:-4]
    if want.startswith("phase22_"):
        want = "p22_" + want[len("phase22_"):]

    man = globals().get("FIG_MANIFEST")
    if man is None or not len(man):
        _m = FIG / "phase22_figure_manifest.csv"
        if not _m.exists():
            raise FileNotFoundError(
                "figure manifest missing; run "
                "src.analysis.phase22_figures.build_all() first: " + str(_m))
        man = pd.read_csv(_m)
        globals()["FIG_MANIFEST"] = man

    _row = man[man["figure_id"] == want]
    if not len(_row):
        raise KeyError(f"figure not declared in manifest: {want!r}")
    row = _row.iloc[0]
    if not bool(row.get("expected_to_embed", True)):
        print("figure declared not required for embedding:", want)
        return
    p = ROOT / str(row["source_path"]) if "source_path" in row.index and \
        str(row.get("source_path", "")) not in ("", "nan") else FIG / f"{want}.png"
    if not p.exists():
        p = ROOT / str(row.get("file", ""))
    if not p.exists():
        raise FileNotFoundError(f"required figure missing on disk: {p}")
    import io
    from PIL import Image as _PILImage
    raw = p.read_bytes()
    if not raw.startswith(b"\\x89PNG\\r\\n\\x1a\\n"):
        raise ValueError(f"required figure is not a PNG: {p}")
    with _PILImage.open(io.BytesIO(raw)) as _im:
        _im.verify()
    with _PILImage.open(io.BytesIO(raw)) as _im:
        w, h = _im.size
    if w <= 0 or h <= 0:
        raise ValueError(f"required figure has degenerate dimensions: {p} {w}x{h}")
    _src = str(row.get("source_sha256", ""))
    if _src and _src != "nan":
        got = hashlib.sha256(raw).hexdigest()
        if got != _src:
            raise ValueError(
                f"required figure SHA mismatch for {want}: manifest={_src[:16]} "
                f"disk={got[:16]} — rebuild the figures before the notebook")
    # Downscale for embedding only when the payload is large; the ORIGINAL
    # source file is never modified.
    if len(raw) > 250_000:
        with _PILImage.open(io.BytesIO(raw)) as _im:
            _im = _im.convert("RGB")
            sw, sh = _im.size
            if sw > 1600:
                _im = _im.resize((1600, max(1, int(round(sh * 1600 / sw))))) 
            buf = io.BytesIO()
            _im.save(buf, format="PNG", optimize=True)
        raw = buf.getvalue()
    display(Image(data=raw, format="png", embed=True, width=min(width, w)))

def table(name):
    p = TAB / name
    return pd.read_csv(p) if p.exists() else pd.DataFrame()

print("numpy", np.__version__, "| pandas", pd.__version__)
_mf = FIG / "phase22_figure_manifest.csv"
FIG_MANIFEST = pd.read_csv(_mf) if _mf.exists() else pd.DataFrame()
if len(FIG_MANIFEST):
    print("figure manifest:", len(FIG_MANIFEST), "declared figures |",
          int(FIG_MANIFEST["expected_to_embed"].sum()), "required for embedding")
else:
    print("figure manifest NOT FOUND — run phase22_figures.build_all() first")
"""))

# 002 ---------------------------------------------------------------------- #
cells.append(md("## 2. Governance: TEST lock and the frozen diagnostic protocol"))
cells.append(code("""
from src.utils.test_lock import verify_test_lock
verify_test_lock(str(ROOT))

PROT = load("phase22_diagnostic_protocol.json")
EG = load("phase22_entry_gate.json")
RB = load("phase22_phase21_reference_binding.json")

display(sty(pd.DataFrame([
    {"item": "protocol id", "value": PROT.get("protocol_id")},
    {"item": "frozen before execution", "value": PROT.get("frozen_before_execution")},
    {"item": "protocol SHA-256", "value": (PROT.get("protocol_sha256") or "")[:32]},
    {"item": "entry-gate verdict", "value": EG.get("verdict")},
    {"item": "entry-gate checks", "value": f"{EG.get('n_passed')}/{EG.get('n_checks')}"},
    {"item": "reference binding verdict", "value": RB.get("verdict")},
    {"item": "reference binding checks", "value": f"{RB.get('n_passed')}/{RB.get('n_checks')}"},
    {"item": "TEST image reads", "value": PROT.get("test_reads", {}).get("test_image_reads", 0)},
    {"item": "TEST mask reads", "value": PROT.get("test_reads", {}).get("test_mask_reads", 0)},
    {"item": "TEST inference", "value": PROT.get("test_reads", {}).get("test_inference", 0)},
    {"item": "TEST visualizations", "value": PROT.get("test_reads", {}).get("test_visualization", 0)},
]), "p22_gov", value="{!s}"))

print("Required outputs declared in the frozen protocol:", len(PROT.get("required_outputs", [])))
print("TEST lock verified against manifests/test.csv sha256.")
"""))

# 003 ---------------------------------------------------------------------- #
cells.append(md("""
## 3. Reference binding — every Phase-22 identity anchored to the frozen Phase-21 run

Phase 22 may not invent a new reference. Every identity it depends on (experiment id,
checkpoint SHA, protocol SHA, task-id map, threshold, channel policy, population) is bound
to the frozen Phase-21 artifacts *fail-closed*: any mismatch aborts rather than warns.
"""))
cells.append(code("""
rows = RB.get("checks", [])
df_checks = pd.DataFrame(rows)
keep = [c for c in ["check", "pass", "observed", "expected"] if c in df_checks.columns]
if len(df_checks):
    display(sty(df_checks[keep], "p22_bind"))
print("Verdict:", RB.get("verdict"), "|", RB.get("n_passed"), "/", RB.get("n_checks"))

b = RB.get("binding", {})
display(sty(pd.DataFrame([
    {"item": "phase-21 experiment", "value": b.get("phase21_experiment_id")},
    {"item": "architecture id", "value": b.get("phase21_architecture_id")},
    {"item": "checkpoint SHA-256", "value": (b.get("phase21_checkpoint_sha256") or "")[:32]},
    {"item": "Phase-20 protocol SHA", "value": (b.get("phase20_protocol_sha256") or "")[:16]},
    {"item": "Phase-22 protocol SHA", "value": (b.get("phase22_protocol_sha256") or "")[:32]},
    {"item": "persisted prediction counts", "value": json.dumps(b.get("persisted_prediction_counts"))},
    {"item": "Phase-21 reference macro Dice", "value": b.get("phase21_reference_macro_domain_dice")},
]), "p22_bind_sum", value="{!s}"))
print("Inference performed while binding:", not RB.get("no_inference_performed_here", True))
"""))

# 004 ---------------------------------------------------------------------- #
cells.append(md("""
## 4. Decision-rule audit — the float16 probability / uint8 prediction incompatibility

The persisted Phase-21 maps store a **float16** probability and a **uint8** prediction. A
float16 probability cannot reproduce the stored uint8 prediction exactly: pixels sitting at
*exactly* 0.5 are labelled both ways across the corpus. This section quantifies the
incompatibility and pins the single rule applied everywhere in Phase 22.
"""))
cells.append(code("""
TA = load("phase22_threshold_rule_audit.json")
fnd = TA.get("finding", {})
dec = TA.get("decision", {})
cand = TA.get("candidate_rules", {})
ge = cand.get("ge_float32_prob_ge_0p5", {})
gt = cand.get("gt_float32_prob_gt_0p5", {})
display(sty(pd.DataFrame([
    {"item": "adopted rule", "value": dec.get("adopted_rule")},
    {"item": "exact-0.5 pixels", "value": fnd.get("pixels_exactly_float16_0p5")},
    {"item": "  of which labelled foreground", "value": fnd.get("of_which_labelled_foreground")},
    {"item": "  of which labelled background", "value": fnd.get("of_which_labelled_background")},
    {"item": "mixed labels present", "value": fnd.get("mixed_labels_present")},
    {"item": "maps with mixed tie labels", "value": fnd.get("maps_with_mixed_tie_labels")},
    {"item": ">= rule: mismatch pixels", "value": ge.get("mismatch_pixels")},
    {"item": ">= rule: mismatch maps", "value": ge.get("maps_with_any_mismatch")},
    {"item": ">= rule: matches frozen eval code", "value": ge.get("matches_frozen_evaluation_code")},
    {"item": ">  rule: mismatch pixels", "value": gt.get("mismatch_pixels")},
    {"item": ">  rule: mismatch maps", "value": gt.get("maps_with_any_mismatch")},
]), "p22_thr", value="{!s}"))
print("Root cause:", fnd.get("root_cause"))
print("Unexplained disagreements at other values:",
      fnd.get("unexplained_disagreements_at_other_values"))
print()
for r in dec.get("rationale", []):
    print(" -", r)
print()
print("The adopted rule is the SMALLER-RESIDUAL rule AND is the frozen evaluation rule; it")
print("is applied IDENTICALLY to the reference map and to every probe arm, so no arm is advantaged.")
"""))

# 005 ---------------------------------------------------------------------- #
cells.append(md("## 5. Global failure atlas (§10) — where the frozen reference fails"))
cells.append(code("""
AT = load("phase22_global_failure_atlas.json")
ov = AT.get("overall", {})
display(sty(pd.DataFrame([
    {"item": "population (VAL)", "value": AT.get("n_samples")},
    {"item": "pooled mean Dice", "value": ov.get("mean_dice")},
    {"item": "median Dice", "value": ov.get("median_dice")},
    {"item": "p05 Dice", "value": ov.get("p05_dice")},
    {"item": "mean IoU / precision / recall",
     "value": f"{ov.get('mean_iou')} / {ov.get('mean_precision')} / {ov.get('mean_recall')}"},
    {"item": "Dice < 0.5 / < 0.7", "value": f"{ov.get('n_dice_below_0p5')} / {ov.get('n_dice_below_0p7')}"},
    {"item": "empty-case rows", "value": ov.get("n_empty_case")},
    {"item": "total foreground pixel error", "value": ov.get("total_foreground_pixel_error")},
]), "p22_atlas", value="{!s}"))

tc = AT.get("taxonomy_counts", {})
tp = AT.get("taxonomy_pct", {})
if tc:
    display(sty(pd.DataFrame([
        {"category": k, "n": v, "pct": tp.get(k)} for k, v in tc.items()]), "p22_atlas_taxo"))

fbd = table("phase22_failure_by_domain.csv")
if len(fbd):
    display(sty(fbd, "p22_atlas_dom"))
show("phase22_atlas_dice_distribution.png")
show("phase22_atlas_taxonomy.png")
"""))

# 006 ---------------------------------------------------------------------- #
cells.append(md("""
## 6. Worst cases per domain (§10)

The taxonomy thresholds were **declared prospectively** in the frozen protocol and were
**not** used to select any case for intervention. They are descriptive only.
"""))
cells.append(code("""
worst = table("phase22_worst_cases_per_domain.csv")
if len(worst):
    display(sty(worst.head(24), "p22_worst"))
show("phase22_atlas_worst_cases.png")
"""))

# 007 ---------------------------------------------------------------------- #
cells.append(md("""
## 7. Scale sensitivity (§11 / §13) — 256 / 512 / 768 / 1024

Every probe re-runs the **same frozen checkpoint** at a different input resolution and is
scored in **NATIVE image space**, so a resolution change cannot be mistaken for a
segmentation change. 512 is the canonical reference and is read from the persisted Phase-21
probability maps (never re-inferred).

> **Required wording (B5).** For the frozen checkpoint trained at 512, 512 had the highest
> observed performance among the tested diagnostic resolutions (256/512/768/1024); all tested
> off-canonical sizes were worse. **This does not establish a globally optimal inference
> resolution.**
"""))
cells.append(code("""
SS = load("phase22_scale_sensitivity.json")
sf = table("phase22_scale_sensitivity.csv")
if len(sf):
    display(sty(sf, "p22_scale"))
sfb = table("phase22_scale_sensitivity_by_domain.csv")
if len(sfb):
    display(sty(sfb, "p22_scale_dom"))

for r in SS.get("summary", []):
    print(f"  size {r.get('probe_size')}: macro Dice {r.get('macro_domain_dice_native')} "
          f"delta {r.get('macro_domain_dice_delta_vs_512')} "
          f"CI [{r.get('delta_ci_low')}, {r.get('delta_ci_high')}] "
          f"separable={r.get('delta_separable_from_512')}")
print()
print(SS.get("interpretation_guard"))
show("phase22_scale_curve.png")
show("phase22_scale_delta_ci.png")
"""))

# 008 ---------------------------------------------------------------------- #
cells.append(md("""
## 8. Scale-probe fidelity gates (§11)

A scale probe is only meaningful if the probing code path is faithful to the canonical one.
Three gates are declared: (A) pipeline fidelity at 512 vs the canonical probability map in
the **shared 512 canvas**, (B) probability agreement, (C) agreement against the stored
prediction (**reported, not gated**, because of the float16 incompatibility in §4).
"""))
cells.append(code("""
SF = load("phase22_scale_probe_fidelity.json")
gA = SF.get("gate_A_pipeline_fidelity", {})
gB = SF.get("gate_B_probability_map_agreement", {})
gC = SF.get("gate_C_disagreement_with_stored_pred", {})
display(sty(pd.DataFrame([
    {"item": "verdict", "value": SF.get("verdict")},
    {"item": "gate A (pipeline fidelity @512)", "value": gA.get("verdict")},
    {"item": "gate A disagreeing pixels", "value": gA.get("total_disagreeing_pixels")},
    {"item": "gate A all within boundary band", "value": gA.get("all_disagreements_within_boundary_band")},
    {"item": "gate A boundary tolerance", "value": gA.get("boundary_tolerance")},
    {"item": "gate B max |dp| (square)", "value": gB.get("max_abs_probability_difference_square")},
    {"item": "gate B verdict", "value": gB.get("verdict")},
    {"item": "gate C verdict (reported only)", "value": gC.get("verdict")},
]), "p22_fid", value="{!s}"))
print(gA.get("note"))
print()
print("Dice by decision source:", json.dumps(SF.get("dice_by_decision_source")))
print()
print("Gate A compares in the SHARED 512 square canvas. Comparing after unmap+re-map would")
print("insert two extra bilinear resamples per side and manufacture spurious disagreements.")
"""))

# 009 ---------------------------------------------------------------------- #
cells.append(md("""
## 9. Regional intervention (§12 / §13) — ORACLE and PREDICTION-DERIVED

Both arms answer the **same** counterfactual: *if a region of interest were cropped,
resampled to 512 with the frozen contract, re-run through the same frozen checkpoint, and
re-projected into the full-field map, what would change?* Only the **source of the ROI**
differs. The ROI rule (tight bbox → centre-preserving 1.5× expansion → clip → square-pad →
resize → paste over the ROI footprint) is **frozen in the protocol** and identical for both.
"""))
cells.append(code("""
RG = load("phase22_oracle_regional_intervention.json")
if RG:
    rrf = load("phase22_regional_fidelity.json")
    display(sty(pd.DataFrame([
        {"item": "region fidelity max |dp| (square)", "value": rrf.get("max_abs_probability_difference_square")},
        {"item": "region fidelity thresholded px", "value": rrf.get("total_thresholded_disagreement_pixels")},
        {"item": "ROI margin", "value": RG.get("roi_rule", {}).get("margin")},
        {"item": "expanded extent factor", "value": RG.get("roi_rule", {}).get("expanded_extent_factor")},
        {"item": "re-centred after clip", "value": RG.get("roi_rule", {}).get("recentre_after_clip")},
        {"item": "decision rule", "value": RG.get("decision_rule")},
    ]), "p22_reg_spec", value="{!s}"))

    for v, s in RG.get("summaries", {}).items():
        print(f"[{v}] n_ok={s.get('n_ok')} n_no_roi={s.get('n_no_roi')} "
              f"mean_delta(exec)={s.get('mean_delta_dice_on_ok')} "
              f"ITT={s.get('mean_delta_dice_intent_to_treat')}")
    print()
    print(RG.get("interpretation_guard"))

gdom = table("phase22_oracle_gain_by_domain.csv")
if len(gdom):
    display(sty(gdom, "p22_reg_dom"))

# Per-image regional intervention table (the raw evidence behind the summaries
# above and behind the harm/regret sections that follow).
_rpi = table("phase22_regional_intervention_per_image.csv")
if len(_rpi):
    _ok = _rpi[_rpi["oracle_status"] == "OK"] if "oracle_status" in _rpi.columns else _rpi
    display(sty(_rpi.head(10), "p22_reg_perimg_head"))
    print(f"phase22_regional_intervention_per_image.csv: {len(_rpi)} rows | "
          f"{len(_ok)} with oracle_status=OK")

# Oracle ROI geometry — the footprint and effective magnification of the
# oracle regional crop (the evidence behind the p22_regional_roi_geometry figure).
_rgeo = table("phase22_roi_geometry.csv")
if len(_rgeo):
    display(sty(_rgeo.head(10), "p22_reg_roi_geo_head"))
    print(f"phase22_roi_geometry.csv: {len(_rgeo)} rows | "
          f"columns {list(_rgeo.columns)}")

show("phase22_regional_gain_distribution.png")
show("phase22_regional_roi_geometry.png")
"""))

# 010 ---------------------------------------------------------------------- #
cells.append(md("## 10. Benefit heterogeneity (§15) — is the gain broad or concentrated?"))
cells.append(code("""
HET = load("phase22_benefit_heterogeneity.json")
if HET:
    g = HET.get("gain_distribution_executed", {})
    display(sty(pd.DataFrame([
        {"item": "n executed", "value": HET.get("n_executed")},
        {"item": "mean delta Dice (executed)", "value": g.get("mean_delta_dice")},
        {"item": "median delta Dice (executed)", "value": g.get("median_delta_dice")},
        {"item": "p05 / p95", "value": f"{g.get('p05')} / {g.get('p95')}"},
        {"item": "improved / worsened / unchanged",
         "value": f"{g.get('n_positive')} / {g.get('n_negative')} / {g.get('n_zero')}"},
        {"item": "share improved", "value": g.get("share_positive")},
        {"item": "Gini of positive benefit", "value": HET.get("concentration", {}).get("gini_of_positive_benefit")},
        {"item": "top-10% share of benefit",
         "value": HET.get("concentration", {}).get("share_of_positive_benefit_from_top_10pct_of_benefiting_cases")},
        {"item": "r(gain, baseline Dice)", "value": HET.get("correlates_of_gain", {}).get("pearson_r_baseline_global_dice")},
        {"item": "r(gain, ROI area fraction)", "value": HET.get("correlates_of_gain", {}).get("pearson_r_roi_area_fraction")},
    ]), "p22_het", value="{!s}"))
    display(sty(pd.DataFrame(HET.get("per_domain", [])), "p22_het_dom"))
ht = table("phase22_benefit_heterogeneity.csv")
if len(ht):
    display(sty(ht, "p22_het_dec"))
"""))

# 011 ---------------------------------------------------------------------- #
cells.append(md("""
## 11. Oracle accept-if-beneficial ceiling (§16) and routing regret (§20)

The accept-if-beneficial policy is a **perfect selector**: it applies the regional arm only
where it strictly helps. It is the **ceiling of any routing policy** — oracle or learned — and
it is **not deployable**. The rule-based policies use **predicted information only** and are
the honest, deployable-shaped comparison.
"""))
cells.append(code("""
ACC = load("phase22_oracle_accept_if_beneficial.json")
REG = load("phase22_routing_regret.json")
if ACC:
    display(sty(pd.DataFrame([
        {"item": "acceptance rate", "value": ACC.get("acceptance_rate")},
        {"item": "always-global pooled Dice", "value": ACC.get("baseline_always_global_pooled_dice")},
        {"item": "always-regional pooled Dice", "value": ACC.get("baseline_always_regional_pooled_dice")},
        {"item": "ORACLE ceiling pooled Dice", "value": ACC.get("oracle_ceiling_pooled_dice")},
        {"item": "ceiling gain over always-global", "value": ACC.get("ceiling_gain_over_always_global")},
        {"item": "is deployable", "value": ACC.get("is_deployable")},
        {"item": "uses ground truth", "value": ACC.get("uses_ground_truth")},
    ]), "p22_ceil", value="{!s}"))
    print(ACC.get("forbidden_claim"))
rt = table("phase22_routing_regret.csv")
if len(rt):
    display(sty(rt, "p22_regret"))
show("phase22_routing_regret.png")
"""))

# 012 ---------------------------------------------------------------------- #
cells.append(md("## 12. Harm analysis (§22) — where does the regional arm make things worse?"))
cells.append(code("""
HARM = load("phase22_harm_analysis.json")
if HARM:
    display(sty(pd.DataFrame([
        {"item": "n executed", "value": HARM.get("n_executed")},
        {"item": "n harmed", "value": HARM.get("n_harmed")},
        {"item": "harm rate (executed)", "value": HARM.get("harm_rate_among_executed")},
        {"item": "harm rate (ITT)", "value": HARM.get("harm_rate_intent_to_treat")},
        {"item": "mean harm", "value": HARM.get("mean_harm")},
        {"item": "worst harm", "value": HARM.get("worst_harm")},
        {"item": "total harm magnitude", "value": HARM.get("total_harm_magnitude")},
        {"item": "net gain (executed)", "value": HARM.get("net_gain_executed")},
    ]), "p22_harm", value="{!s}"))
    display(sty(pd.DataFrame(HARM.get("harm_by_domain", [])), "p22_harm_dom"))
show("phase22_regional_harm.png")
"""))

# 013 ---------------------------------------------------------------------- #
cells.append(md("""
## 13. Prediction-derived ROI diagnostic (§18) — the deployable-shaped variant

The ROI comes from the **model's own thresholded prediction**, never the ground truth. It
inherits every failure of the global pass; in particular a **total miss yields no ROI at
all**, so the path fails exactly where recovery is most needed. This is a diagnosed
limitation, not a proposed method.
"""))
cells.append(code("""
ROI = load("phase22_prediction_derived_roi.json")
if ROI:
    display(sty(pd.DataFrame([
        {"item": "n total", "value": ROI.get("n_total")},
        {"item": "n with predicted ROI", "value": ROI.get("n_predicted_roi_ok")},
        {"item": "n NO_PREDICTED_ROI", "value": ROI.get("n_no_predicted_roi")},
        {"item": "NO_PREDICTED_ROI rate", "value": ROI.get("no_predicted_roi_rate")},
        {"item": "mean delta Dice (ITT)", "value": ROI.get("mean_predicted_delta_dice_intent_to_treat")},
        {"item": "mean delta Dice (executed)", "value": ROI.get("mean_predicted_delta_dice_on_executed")},
        {"item": "corr(predicted gain, oracle gain)", "value": ROI.get("correlation_predicted_vs_oracle_gain")},
    ]), "p22_roi", value="{!s}"))
    print(ROI.get("interpretation_guard"))
"""))

# 014 ---------------------------------------------------------------------- #
cells.append(md("""
## 14. Uncertainty vs benefit (§19) — is there a cheap deployable signal?

A router needs a signal that predicts where the regional arm would help. These correlations
use the **frozen probability maps only** (no new inference) and are computed **post hoc on
VAL**. They are **descriptive**: no threshold was fitted, no policy selected, no training
performed.

**GT-free and ground-truth-derived signals are separated.** A signal is only *deployable*
if it can be computed **without ground truth**, **before** refinement, and **at inference
time**. The frozen analysis originally ranked `recall` as the best *deployable* signal;
that was **invalid**, because recall requires the ground-truth mask.

**The figure below is generated from the corrected GT-free table**
(`reports/tables/phase22_gt_free_proxy_vs_benefit.csv`). Its **left panel** shows the
deployable (GT-free) ranking only. Where a second panel is present it is explicitly titled
`POST_HOC_GT_AWARE_DIAGNOSTIC` — those associations require ground truth and are **not**
deployable. No ground-truth-derived metric is presented as a routable signal.
"""))
cells.append(code("""
REP = load("phase22_postfreeze_semantic_repair.json")
_gf = TAB / "phase22_gt_free_proxy_vs_benefit.csv"
_ga = TAB / "phase22_gt_aware_posthoc_associations.csv"
# FAIL CLOSED: the GT-free deployable ranking is mandatory. We must never fall
# back to the frozen GT-mixed JSON (phase22_uncertainty_vs_benefit.json,
# ranked_abs_spearman), which mixed ground-truth-derived quantities such as
# `recall` into the "deployable" ranking and presented recall as the winner.
if not REP:
    raise FileNotFoundError(
        "phase22_postfreeze_semantic_repair.json is missing — refusing to fall "
        "back to the GT-mixed phase22_uncertainty_vs_benefit.json ranking")
if not _gf.exists():
    raise FileNotFoundError(f"required GT-free table missing: {_gf}")
print("GT-free deployable ranking (uses_GT = False only):")
display(sty(pd.DataFrame(REP.get("gt_free_deployable_ranking", [])), "p22_unc_gtfree"))
if _ga.exists():
    print("Post-hoc GROUND-TRUTH associations (NOT deployable):")
    display(sty(pd.read_csv(_ga), "p22_unc_gtaware"))
print(REP.get("best_gt_free_signal_interpretation"))
if _gf.exists():
    _gfd = pd.read_csv(_gf)
    assert not bool(_gfd["uses_GT"].astype(str).str.lower().eq("true").any()), \\
        "GT-free table contains GT-derived rows"
    _b = _gfd.reindex(_gfd["abs_spearman"].abs().sort_values(ascending=False).index).iloc[0]
    print(f"Best GT-free signal: {_b['signal']} (|rho|={abs(_b['spearman_r']):.4f}) — "
          "weak magnitude; descriptive only, no threshold fitted, no router selected.")
show("phase22_uncertainty_vs_benefit.png")
"""))

# 015 ---------------------------------------------------------------------- #
cells.append(md("""
## 15. Resource frontier (§17) and conditional-compute envelopes (§24)

The regional pass always costs **one full 512 forward regardless of crop size**, because the
crop is resampled to 512. Conditional compute therefore saves **executions**, not resolution:
a smaller crop does **not** cost less. This is stated explicitly so the frontier is not
over-read.
"""))
cells.append(code("""
ENV = load("phase22_conditional_compute_envelopes.json")
FR = load("phase22_resource_frontier.json")
envf = table("phase22_conditional_compute_envelopes.csv")
if len(envf):
    display(sty(envf, "p22_env"))
if ENV:
    print("global pass MACs @512:", ENV.get("global_pass_macs_at_512"))
    print("regional pass MACs @512:", ENV.get("regional_pass_macs_at_512"))
    print(ENV.get("important_caveat"))
    print(ENV.get("analytical_approximation"))
show("phase22_resource_frontier.png")
show("phase22_resource_envelopes.png")
"""))

# 016 ---------------------------------------------------------------------- #
cells.append(md("""
## 16. Resource gap (§23) — six-model panel and the absolute-cost warning

Cost is a **lower bound**: the analytical count covers closed-form `Conv2d`/`Linear` MACs
only, excluding GroupNorm, SiLU, pooling, bilinear interpolation, FiLM modulation and
sigmoid. Parameters do **not** predict compute — the cost is resolution-driven.
"""))
cells.append(code("""
GAP = load("phase22_resource_gap.json")
if GAP:
    display(sty(pd.DataFrame([
        {"item": "reference parameters", "value": GAP.get("reference_params")},
        {"item": "reference G MACs @512", "value": GAP.get("reference_gmacs_at_512")},
        {"item": "param rank of reference", "value": GAP.get("param_rank_of_reference")},
        {"item": "compute rank of reference", "value": GAP.get("gmacs_rank_of_reference")},
        {"item": "is small in absolute terms", "value": GAP.get("absolute_cost_statement", {}).get("is_small_in_absolute_terms")},
    ]), "p22_gap", value="{!s}"))
    print(GAP.get("absolute_cost_statement", {}).get("note"))
    display(sty(pd.DataFrame(GAP.get("panel", [])), "p22_gap_panel"))
show("phase22_resource_six_model.png")
"""))

# 017 ---------------------------------------------------------------------- #
cells.append(md("## 17. CPU baseline (§25) — measurement, not model"))
cells.append(code("""
CPU = load("phase22_cpu_baseline.json")
if CPU:
    display(sty(pd.DataFrame(CPU.get("rows", [])), "p22_cpu"))
    print("threads:", CPU.get("threads"),
          "| batch:", CPU.get("batch_size"),
          "| AMP:", CPU.get("amp"),
          "| measurement_only:", CPU.get("measurement_only"))
    print(CPU.get("rss_note"))
    print(CPU.get("note"))
"""))

# 018 ---------------------------------------------------------------------- #
cells.append(md("""
## 18. KUB TINY analysis (§26)

The TINY stratum (`component_ratio <= Q25` of the frozen `kub_size_clean_v3_v1` taxonomy) is
the project's central difficulty. TINY was **not** optimised on: no component of the
reference model was specialised for it.

**Reading guard on the stratum figure below.** The bars are *observed* mean Dice per stratum;
TINY shows the lowest observed mean Dice. The figure must **not** be read as establishing a
statistically significant TINY improvement of any kind. The observed TINY oracle regional gain
is `+0.013197` Dice, but its paired 95% CI `[-0.084062, +0.105133]` **includes zero**
(p = 0.763); the TINY effect is therefore **descriptive only**.
"""))
cells.append(code("""
TINY = load("phase22_kub_tiny_analysis.json")
if TINY:
    display(sty(pd.DataFrame([
        {"item": "taxonomy", "value": TINY.get("taxonomy_id")},
        {"item": "stratum definition", "value": TINY.get("stratum_definition")},
        {"item": "TINY optimised on", "value": TINY.get("tiny_optimised_on")},
    ]), "p22_tiny_spec", value="{!s}"))
    if isinstance(TINY.get("strata"), list):
        display(sty(pd.DataFrame(TINY["strata"]), "p22_tiny"))
    if "tiny_stratum_regional_gain" in TINY:
        display(sty(pd.DataFrame([TINY["tiny_stratum_regional_gain"]]), "p22_tiny_gain"))
        _tg = TINY["tiny_stratum_regional_gain"]
        _bt = _tg.get("bootstrap_vs_global") or {}
        print("Required wording (B5): KUB TINY was the only frozen size stratum with a "
              f"positive observed mean oracle regional gain (+{_tg.get('mean_oracle_delta_dice'):.6f} Dice), "
              f"but the paired 95% CI [{_bt.get('ci_low'):.6f}, {_bt.get('ci_high'):.6f}] includes zero "
              f"(p={_bt.get('p_value')}); therefore the TINY effect is descriptive and not "
              "statistically established.")
        print("This does NOT weaken the useful finding: regional benefit is strongly "
              "heterogeneous, and always-on regional processing is harmful in aggregate.")
show("phase22_kub_strata.png")
"""))

# 019 ---------------------------------------------------------------------- #
cells.append(md("""
## 19. Domain preservation (§27) and statistics consolidation (§28)

The reference is frozen, so **no per-domain property of the reference can change** in Phase
22. Domain preservation is therefore a statement about the **diagnostic arms only**.
"""))
cells.append(code("""
DOM = load("phase22_domain_preservation.json")
if DOM:
    display(sty(pd.DataFrame(DOM.get("per_domain", [])), "p22_dom"))
    print("reference unchanged:", DOM.get("reference_unchanged", {}).get("matches_frozen_phase21_values"))
    print(DOM.get("answer_summary"))

ST = load("phase22_statistics.json")
if ST:
    print()
    display(sty(pd.DataFrame([{k: (json.dumps(v) if isinstance(v, (dict, list)) else v)
                               for k, v in c.items()} for c in ST.get("comparisons", {}).values()]),
               "p22_stats"))
    print(ST.get("ci_overlap_rule"))
    print("threshold caveat:", ST.get("threshold_rule_caveat", {}).get("rule"),
          "| residual px:", ST.get("threshold_rule_caveat", {}).get("residual_mismatch_pixels_against_stored_pred"))
"""))

# 020 ---------------------------------------------------------------------- #
cells.append(md("""
## 20. Scale vs regional (§29) — which axis buys more Dice?

A direct comparison of the two candidate axes. It must be read with the guard in view: the
scale axis is a genuine (off-training-distribution) measurement, while the regional-**oracle**
axis is an **upper bound that uses ground truth**. The two are **not** comparable as methods.
"""))
cells.append(code("""
SVR = load("phase22_scale_vs_regional.json")
if SVR:
    rows = []
    for k, v in SVR.get("axes", {}).items():
        rows.append({"axis": k, **{kk: vv for kk, vv in v.items() if not isinstance(vv, dict)}})
    display(sty(pd.DataFrame(rows), "p22_svr"))
    print(SVR.get("verdict_guard"))
show("phase22_scale_vs_regional.png")
"""))

# 021 ---------------------------------------------------------------------- #
cells.append(md("""
## 21. No-new-training audit (§38) and the future benefit-label contract (§30)

Phase 22 is forbidden to train anything. This section is the audit of that prohibition: a
static scan of every Phase-22 code file for training constructs, a check that the Phase-21
experiment and checkpoint directories are byte-unchanged, and a check that every Phase-22
audit declares zero training jobs.
"""))
cells.append(code("""
NT = load("phase22_no_new_training_audit.json")
if NT:
    display(sty(pd.DataFrame(NT.get("checks", [])), "p22_nt"))
    print("Verdict:", NT.get("verdict"))
    print("Total forbidden hits in Phase-22 code:",
          NT.get("static_scan", {}).get("total_forbidden_construct_hits"),
          "over", NT.get("static_scan", {}).get("files_scanned"), "files")
    print("training_jobs_started:", NT.get("training_jobs_started"),
          "| optimizer constructed:", NT.get("optimizer_constructed"),
          "| backward called:", NT.get("backward_called"),
          "| checkpoint written:", NT.get("checkpoint_written"))
    print("TEST reads:", json.dumps(NT.get("test_reads", {})))
"""))

# 022 ---------------------------------------------------------------------- #
cells.append(md("""
## 22. Candidate-method evidence (§31)

The evidence gathered in Phase 22 is *diagnostic*. It supports **the existence of headroom**
and **the difficulty of capturing it without training**; it does **not** support any claim
that a deployable method attains these numbers, and it says nothing about TEST.
"""))
cells.append(code("""
CE = load("phase22_candidate_method_evidence.json")
if CE:
    for c in CE.get("candidates", []):
        print(f"--- {c.get('candidate')}  [{c.get('status')}]")
        for k, v in (c.get("evidence") or {}).items():
            print(f"      {k}: {v}")
        print(f"      supports: {c.get('supports')}")
        print(f"      does_not_support: {c.get('does_not_support')}")
    print()
    print(CE.get("verdict"))
LB = load("phase22_future_benefit_label_contract.json")
if LB:
    print()
    _ld = LB.get("label_definition", {})
    print("future label quantity:", _ld.get("quantity"))
    print("deployable geometry source:",
          _ld.get("geometry_source_required_for_a_DEPLOYABLE_label"))
    print("status:", LB.get("status"), "| is a training artifact:",
          LB.get("is_a_training_artifact"))
"""))

# 023 ---------------------------------------------------------------------- #
cells.append(md("""
## 23. Figure inventory (§32 / §33) and the explicit figure manifest

Every figure is derived deterministically (`Agg`, fixed dpi) from a persisted artifact. The
**manifest** declares the required reviewer figure set (`figure_id, section, semantic_role,
expected_to_embed, source_sha256`); the notebook embeds through it **fail-closed** — a
required figure that cannot be located, decoded or SHA-matched aborts the build rather than
silently printing "figure unavailable".
"""))
cells.append(code("""
inv_csv = pd.read_csv(FIG / "phase22_figure_inventory.csv") \
    if (FIG / "phase22_figure_inventory.csv").exists() else pd.DataFrame()
man_csv = pd.read_csv(FIG / "phase22_figure_manifest.csv") \
    if (FIG / "phase22_figure_manifest.csv").exists() else pd.DataFrame()
if len(inv_csv):
    display(sty(inv_csv, "p22_figs"))
    print(f"{len(inv_csv)} figures listed in the inventory")
else:
    on_disk = sorted(p.name for p in FIG.glob("*.png")) if FIG.exists() else []
    display(sty(pd.DataFrame([{"figure": n} for n in on_disk]), "p22_figs"))
    print(f"{len(on_disk)} figures on disk (inventory not yet written)")
if len(man_csv):
    display(sty(man_csv, "p22_fig_manifest"))
    print(f"{len(man_csv)} figures declared in the manifest | "
          f"{int(man_csv['expected_to_embed'].sum())} required for embedding")
"""))

# 024 ---------------------------------------------------------------------- #
cells.append(md("""
## 24. Final freeze and terminal state

`phase22_final_freeze.json` is written by the canonical pipeline **after** this notebook, so a
pre-freeze build falls back to the declared static guard rather than weakening it. Once the
freeze exists it is authoritative.
"""))
cells.append(code("""
FF = load("phase22_final_freeze.json")
display(sty(pd.DataFrame([
    {"item": "freeze verified", "value": FF.get("freeze_verified")},
    {"item": "checks passed", "value": f"{FF.get('n_passed')}/{FF.get('n_checks')}"},
    {"item": "validation problems", "value": json.dumps(FF.get("validation_problems", []))},
    {"item": "terminal state", "value": FF.get("terminal_state")},
    {"item": "phase 23 started", "value": FF.get("governance", {}).get("phase23_started")},
    {"item": "training jobs started", "value": FF.get("governance", {}).get("training_jobs_started")},
    {"item": "architecture modified", "value": FF.get("governance", {}).get("architecture_modified")},
    {"item": "benefit predictor trained", "value": FF.get("governance", {}).get("benefit_predictor_trained")},
    {"item": "TEST reads", "value": json.dumps(FF.get("governance", {}).get("test_locks", {}))},
    {"item": "reference checkpoint unchanged", "value": FF.get("reference", {}).get("checkpoint_unchanged")},
]), "p22_freeze", value="{!s}"))

if FF:
    cs = FF.get("checks", [])
    if cs:
        display(sty(pd.DataFrame(cs)[[c for c in ["check", "pass", "observed", "expected"]
                                     if c in pd.DataFrame(cs).columns]], "p22_freeze_checks"))
    ss = FF.get("science_summary", {})
    if ss:
        print("science summary keys:", list(ss.keys()))
        print(json.dumps(ss, indent=1)[:2000])
"""))

# 025 ---------------------------------------------------------------------- #
cells.append(md("""
## 25. Reproduction

```bash
# 1. freeze the diagnostic protocol (refuses to overwrite a differing frozen protocol)
./.venv/Scripts/python.exe scripts/analysis/run_phase22_freeze_protocol.py

# 2. bind every Phase-22 identity to the frozen Phase-21 reference (fail-closed)
./.venv/Scripts/python.exe scripts/analysis/run_phase22_reference_binding.py

# 3. audit the decision rule (float16 prob vs uint8 pred)
./.venv/Scripts/python.exe scripts/analysis/run_phase22_threshold_audit.py

# 4. global failure atlas (persisted metrics only)
./.venv/Scripts/python.exe -m src.analysis.phase22_failure_atlas

# 5. scale probe — 256/768/1024 vs the 512 canonical reference
./.venv/Scripts/python.exe src/analysis/phase22_scale.py --device cuda

# 6. regional intervention — oracle + prediction-derived
./.venv/Scripts/python.exe src/analysis/phase22_regional.py --device cuda

# 7. benefit / harm / regret  (consumes the regional table)
./.venv/Scripts/python.exe -m src.analysis.phase22_benefit

# 8. resource gap / frontier / envelopes / CPU baseline
./.venv/Scripts/python.exe -m src.analysis.phase22_resource

# 9. KUB TINY / domain preservation / statistics / scale-vs-regional
./.venv/Scripts/python.exe -m src.analysis.phase22_kub_domain

# 10. figures + inventories
./.venv/Scripts/python.exe -m src.analysis.phase22_figures

# 11. no-new-training audit + label contract + candidate evidence
./.venv/Scripts/python.exe scripts/analysis/run_phase22_no_training_audit.py

# 12. freeze + report
./.venv/Scripts/python.exe scripts/analysis/run_phase22_pipeline.py
```

**TEST is never read at any step. Then STOP — Phase 23 is not started.**
"""))

# write + execute ----------------------------------------------------------- #
nb = nbformat.v4.new_notebook(cells=cells)
for _i, _c in enumerate(nb.cells):
    _c["id"] = f"p22{_i:03d}"
nbformat.write(nb, str(NB_PATH))
print(f"Wrote {NB_PATH} ({len(nb.cells)} cells)")
print("Executing ...")
client = NotebookClient(nb, kernel_name="jup-venv", timeout=7200,
                        resources={"metadata": {"path": str(ROOT)}})
client.execute()

# deterministic post-processing --------------------------------------------- #
for _c in nb.cells:
    if isinstance(_c.get("metadata"), dict):
        _c["metadata"].pop("execution", None)
    _outs = _c.get("outputs")
    if _outs:
        _merged = []
        for _o in _outs:
            if (_o.get("output_type") == "stream" and _merged
                    and _merged[-1].get("output_type") == "stream"
                    and _merged[-1].get("name") == _o.get("name")):
                _p = _merged[-1]
                _pt, _ct = _p.get("text", ""), _o.get("text", "")
                if isinstance(_pt, list):
                    _pt = "".join(_pt)
                if isinstance(_ct, list):
                    _ct = "".join(_ct)
                _p["text"] = _pt + _ct
            else:
                _merged.append(_o)
        _c["outputs"] = _merged

_ADDR = re.compile(r"0x[0-9a-fA-F]{6,}")
for _c in nb.cells:
    for _o in _c.get("outputs", []) or []:
        _d = _o.get("data")
        if isinstance(_d, dict):
            for _k, _v in list(_d.items()):
                if isinstance(_v, str):
                    _d[_k] = _ADDR.sub("0xADDR", _v)
                elif isinstance(_v, list):
                    _d[_k] = [_ADDR.sub("0xADDR", _s) if isinstance(_s, str) else _s
                              for _s in _v]
        _t = _o.get("text")
        if isinstance(_t, str):
            _o["text"] = _ADDR.sub("0xADDR", _t)
        elif isinstance(_t, list):
            _o["text"] = [_ADDR.sub("0xADDR", _s) if isinstance(_s, str) else _s
                          for _s in _t]
nbformat.write(nb, str(NB_PATH))

code_cells = [c for c in nb.cells if c.cell_type == "code"]
errors = sum(1 for c in code_cells for o in c.get("outputs", [])
             if o.get("output_type") == "error")
counts = [c.get("execution_count") for c in code_cells]
monotonic = all(counts[i] == i + 1 for i in range(len(counts)))
pngs = sum(1 for c in code_cells for o in c.get("outputs", [])
           if "image/png" in (o.get("data", {}) or {}))
htmls = sum(1 for c in code_cells for o in c.get("outputs", [])
            if "text/html" in (o.get("data", {}) or {}))
sha_nb = hashlib.sha256(NB_PATH.read_bytes()).hexdigest()
print(f"Cells: {len(nb.cells)} | markdown: "
      f"{sum(1 for c in nb.cells if c.cell_type == 'markdown')} | code: {len(code_cells)}")
print("Zero tracebacks:", "PASS" if errors == 0 else f"FAIL ({errors})")
print(f"Monotonic exec counts (1..{len(code_cells)}): "
      f"{'PASS' if monotonic else 'FAIL'}")
print(f"image/png outputs: {pngs} | html table outputs: {htmls}")
print("Notebook SHA:", sha_nb)
