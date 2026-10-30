"""Build the H2C-B2 downstream reviewer notebook (READ-ONLY on rerun)."""
from pathlib import Path

import nbformat

ROOT = Path(r"D:\Softfors\jup")
NB = (ROOT / "notebooks/phasewise/phase_13_predicted_roi_localization"
      / "post_phase13_h2c_downstream_analysis.ipynb")
EID = ("post_phase13_h2c_kub_localizer_spatialhead3x3relu_r512_h128_sigmaeq075_"
       "centernetfocal_deploymentbalance_seed42_clean_v3")


def md(t):
    return nbformat.v4.new_markdown_cell(t)


def code(s):
    return nbformat.v4.new_code_cell(s)


cells = []

cells.append(md("""# POST-PHASE13 H2C-B2 — Downstream Regional Segmentation Analysis

## 1. Governance / Branch Identity

READ-ONLY on rerun. No training, no localizer inference, no hidden segmentation inference.

Branch: Phase 13 `REVISE_LOCALIZER` → H1 `CLOSED__PARTIAL_MITIGATION_INSUFFICIENT` →
H2A `CLOSED__SELECTION_REDESIGN_PARTIAL` → H2B `CLOSED__OBJECTIVE_REDESIGN_INSUFFICIENT` →
**H2C head redesign**.

Run id: `post_phase13_h2c_downstream_best_native_policy`.
"""))

cells.append(code("""
import hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["figure.dpi"] = 100
plt.rcParams["figure.figsize"] = (10, 5)

ROOT = Path(r"D:\\Softfors\\jup")
AUDITS = ROOT / "reports" / "audits"
TABLES = ROOT / "reports" / "tables"
EID = ("post_phase13_h2c_kub_localizer_spatialhead3x3relu_r512_h128_sigmaeq075_"
       "centernetfocal_deploymentbalance_seed42_clean_v3")

def sha(p):
    p = Path(p)
    if not p.is_absolute():
        p = ROOT / p
    return hashlib.sha256(p.read_bytes()).hexdigest()

integ = json.loads((AUDITS / "post_phase13_h2c_b2_downstream_integrity.json").read_text("utf-8"))
adj = json.loads((AUDITS / "post_phase13_h2c_b2_outcome_adjudication.json").read_text("utf-8"))
fm = json.loads((AUDITS / "post_phase13_h2c_b2_freeze_manifest.json").read_text("utf-8"))
case = pd.read_csv(TABLES / "post_phase13_h2c_downstream_case_model_metrics.csv")
comp = pd.read_csv(TABLES / "post_phase13_h2c_downstream_component_model_metrics.csv")
summary = pd.read_csv(TABLES / "post_phase13_h2c_downstream_model_summary.csv")
cross = pd.read_csv(TABLES / "post_phase13_h2c_downstream_cross_architecture_summary.csv")
link = pd.read_csv(TABLES / "post_phase13_h2c_localizer_to_downstream_comparison.csv")
print("Environment OK | case rows:", len(case), "| component rows:", len(comp))
"""))

cells.append(md("""## 2. H2C Hypothesis and the Single Changed Axis

Can a HEAD-ONLY spatial representation redesign improve heatmap discrimination and proposal
precision while preserving object coverage, holding everything else fixed?

Changed axis (exactly one): `LOCALIZER_PREDICTION_HEAD_ARCHITECTURE` (`CHANGE_H2C_001`),
including its frozen initialization. H2C branches from **H2A** and retains the H2A
`CenterNetFocalLoss(alpha=2.0, beta=4.0)` objective.
"""))

cells.append(md("## 3. B1 → B2 Chain Provenance"))
cells.append(code("""
b1 = json.loads((AUDITS / "post_phase13_h2c_b1_training_evaluation.json").read_text("utf-8"))
print("H2C protocol SHA:", sha(AUDITS / "post_phase13_h2c_protocol_frozen.json"))
print("H2C-B1 best epoch:", b1["termination"]["best_epoch"], "| completed:", b1["termination"]["completed_epochs"])
print("H2C-B1 best.pt SHA:", b1["bindings"]["best_pt_sha"])
print("B2 freeze manifest best.pt SHA:", fm["h2c_b1_best_checkpoint_sha256"])
print("best.pt SHA consistent across B1 audit and B2 manifest:",
      b1["bindings"]["best_pt_sha"] == fm["h2c_b1_best_checkpoint_sha256"])
print("selected epoch:", fm["selected_epoch"], "| head:", fm["head_identity"])
"""))

cells.append(md("""## 4. Reporting-Defect Disclosure

The completed H2C-B1 runner inherited Phase-13 audit payload identity strings. The persisted
defective payloads described the run with Phase-13 identity (`R2 + R2A_LOSS_BINDING`,
`scientific_changes = 0`). Corrected **additively**; the checkpoint itself is correct.
"""))
cells.append(code("""
corr = json.loads((AUDITS / "post_phase13_h2c_b1_audit_identity_correction.json").read_text("utf-8"))
print("classification:", corr["classification"])
print("scope:", corr["defect"]["severity_scope"][:160], "...")
print("scientific impact:", corr["scientific_impact"])
print("training restarted:", corr["repair_applied"]["training_restarted"])
print("original defective audits rewritten:", corr["repair_applied"]["original_defective_audits_rewritten"])
"""))

cells.append(md("## 5. Frozen B2 Configuration"))
cells.append(code("""
for k, v in adj["dimension_A_localizer_proposal_quality"].items():
    pass
print("architectures:", integ["segmentation_checkpoint_shas"])
print("proposal policy: threshold 0.10 / margin 0.20 / top_k 5 / NMS 0.30")
print("fusion variant: PREDICTED_REGION_FLOAT_GLOBAL_RETAINED ; segmentation threshold 0.5")
print("global cache manifest SHA:", integ["global_cache_manifest_sha"])
print("global reproduction:", integ["global_reproduction"])
print("proposal count:", integ["proposal_count"], "| regional crops:", integ["regional_crop_evaluations"])
"""))

cells.append(md("## 6. Model Summary"))
cells.append(code("""
pd.set_option("display.max_columns", None); pd.set_option("display.width", 0)
print(summary.to_string(index=False))
"""))

cells.append(md("## 7. H2C vs GLOBAL / Phase13 / H2A / ORACLE (Dice)"))
cells.append(code("""
cols = ["model_display", "global_macro_dice", "phase13_predicted_macro_dice",
        "h2a_predicted_macro_dice", "h2c_predicted_macro_dice", "oracle_macro_dice",
        "DELTA_H2C_GLOBAL_DICE", "DELTA_H2C_PHASE13_DICE", "DELTA_H2C_H2A_DICE",
        "H2C_ORACLE_BENEFIT_RETENTION", "H2C_ORACLE_GAP"]
print(summary[cols].to_string(index=False))
"""))

cells.append(md("## 8. Dice / IoU / Precision / Recall"))
cells.append(code("""
fig, axes = plt.subplots(2, 2, figsize=(14, 8))
for ax, m in zip(axes.flat, ["dice", "iou", "precision", "recall"]):
    x = np.arange(len(summary)); w = 0.2
    ax.bar(x - w, summary[f"global_macro_{m}"], w, label="GLOBAL")
    ax.bar(x, summary[f"phase13_predicted_macro_{m}"], w, label="Phase13")
    ax.bar(x + w, summary[f"h2a_predicted_macro_{m}"], w, label="H2A")
    ax.bar(x + 2*w, summary[f"h2c_predicted_macro_{m}"], w, label="H2C")
    ax.set_xticks(x); ax.set_xticklabels(summary["model_display"], rotation=15, ha="right")
    ax.set_title(m.capitalize()); ax.legend()
plt.tight_layout(); plt.show()
"""))

cells.append(md("## 9. FP / FN"))
cells.append(code("""
print(summary[["model_display", "mean_global_fp", "mean_h2c_fp", "fp_delta_vs_global",
               "mean_global_fn", "mean_h2c_fn"]].to_string(index=False))
"""))

cells.append(md("## 10. Component Recoveries / Losses"))
cells.append(code("""
cols = ["model_display", "component_recoveries_vs_global", "component_losses_vs_global",
        "component_recoveries_vs_h2a", "component_losses_vs_h2a"]
print(summary[cols].to_string(index=False))
print()
print(cross.to_string(index=False))
"""))

cells.append(md("## 11. Size Strata"))
cells.append(code("""
st = comp.groupby(["model", "size_stratum"]).agg(
    n=("native_component_id", "count"), global_detected=("global_detected", "sum"),
    h2c_detected=("h2c_predicted_detected", "sum"), h2a_detected=("h2a_predicted_detected", "sum"),
    recoveries=("GLOBAL_TO_H2C_RECOVERY", "sum"), losses=("GLOBAL_TO_H2C_LOSS", "sum")).reset_index()
print(st.to_string(index=False))
"""))

cells.append(md("""## 12. Frozen Difficult Cohorts

Global-empty is reported as `GLOBAL_EMPTY_COMPONENTS_WITHIN_5_FROZEN_IMAGES`.
"""))
cells.append(code("""
ht = comp[comp["hard_tiny"]].groupby("model").agg(n=("native_component_id", "count"),
      global_detected=("global_detected", "sum"), h2c_detected=("h2c_predicted_detected", "sum"),
      recoveries=("GLOBAL_TO_H2C_RECOVERY", "sum"), losses=("GLOBAL_TO_H2C_LOSS", "sum"))
ge = comp[comp["global_empty_image"]].groupby("model").agg(n=("native_component_id", "count"),
      global_detected=("global_detected", "sum"), h2c_detected=("h2c_predicted_detected", "sum"),
      recoveries=("GLOBAL_TO_H2C_RECOVERY", "sum"), losses=("GLOBAL_TO_H2C_LOSS", "sum"))
mc = comp[comp["multi_component_image"]].groupby("model").agg(n=("native_component_id", "count"),
      global_detected=("global_detected", "sum"), h2c_detected=("h2c_predicted_detected", "sum"),
      recoveries=("GLOBAL_TO_H2C_RECOVERY", "sum"), losses=("GLOBAL_TO_H2C_LOSS", "sum"))
print("--- hard_tiny ---"); print(ht)
print("--- GLOBAL_EMPTY_COMPONENTS_WITHIN_5_FROZEN_IMAGES ---"); print(ge)
print("--- multi_component ---"); print(mc)
"""))

cells.append(md("## 13. Localizer → Downstream Translation"))
cells.append(code("""
pd.set_option("display.max_columns", None); pd.set_option("display.width", 0)
print(link.to_string(index=False))
"""))

cells.append(md("""## 14. Adjudication (frozen rule applied)

**No criterion was created after observing results.** The frozen H2C outcome definitions from the
H2C protocol were applied verbatim.
"""))
cells.append(code("""
print("OUTCOME:", adj["h2c_outcome"])
print("frozen rule source:", adj["frozen_rule_source"])
print("clause applied:", adj["outcome_clause_applied"])
print()
print("reasoning:", adj["reasoning"])
print()
print("--- countervailing evidence (disclosed) ---")
print(adj["countervailing_evidence_disclosed"]["note"])
print()
print("Phase-14 eligibility:", adj["phase14_eligibility"]["status"])
"""))

cells.append(md("## 15. B2 Counters"))
cells.append(code("""
ex = json.loads((AUDITS / "post_phase13_h2c_b2_execution_audit.json").read_text("utf-8"))
for k, v in ex["counters"].items():
    print(f"  {k}: {v}")
print()
for k, v in ex["counter_explanations"].items():
    print(f"  [{k}] {v}")
"""))

cells.append(md("""## 16. Limitations

1. Single-seed adaptive VAL-development evidence.
2. H2C localizer train/val losses are not comparable in scale to H2A's (frozen zero-terminal
   initialization; identical initial logits and initial loss 19.119539).
3. The H2C-B1 runner's inherited audit-payload identity strings were corrected additively; the
   checkpoint was always correct. The checkpoint records the pre-correction runner SHA.
4. Descriptive comparison only — no winner, no superiority claim, no significance testing.
5. No threshold search, no proposal grid, no head-family/hidden-width search.
6. TEST remains untouched.
"""))

cells.append(md("""## 17. Explicit Phase-14 Stop Boundary

**H2C-B2 does not start Phase 14.**

Phase 14 is ELIGIBLE_NOT_STARTED and requires separate supervisor authorization.
"""))

cells.append(md("## 18. Artifact SHA Registry"))
cells.append(code("""
artifacts = [
    "reports/audits/post_phase13_h2c_protocol_frozen.json",
    "reports/audits/post_phase13_h2c_b1_training_evaluation.json",
    "reports/audits/post_phase13_h2c_b1_audit_identity_correction.json",
    "reports/audits/post_phase13_h2c_b2_freeze_manifest.json",
    "reports/audits/post_phase13_h2c_b2_downstream_integrity.json",
    "reports/audits/post_phase13_h2c_b2_outcome_adjudication.json",
    "reports/audits/post_phase13_h2c_b2_execution_audit.json",
    "reports/audits/post_h2c_chain_closure_report.json",
    "reports/tables/post_phase13_h2c_downstream_case_model_metrics.csv",
    "reports/tables/post_phase13_h2c_downstream_component_model_metrics.csv",
    "reports/tables/post_phase13_h2c_downstream_model_summary.csv",
    "reports/tables/post_phase13_h2c_downstream_cross_architecture_summary.csv",
    "reports/tables/post_phase13_h2c_localizer_to_downstream_comparison.csv",
    "reports/tables/post_phase13_h2c_vs_h2a_vs_phase13_localizer_comparison.csv",
    "checkpoints/" + EID + "/best.pt",
]
for a in artifacts:
    p = ROOT / a
    print(f"{sha(p) if p.exists() else 'MISSING':64s}  {Path(a).name}")
"""))

cells.append(md("""## 19. Mandatory Complete Tables (Untruncated)
"""))
cells.append(code("""
_pd = pd
_pd.set_option("display.max_rows", None); _pd.set_option("display.max_columns", None)
_pd.set_option("display.width", 0); _pd.set_option("display.max_colwidth", None)
print("=" * 100); print(f"MODEL SUMMARY — {len(summary)} / 4 rows"); print("=" * 100)
print(summary.to_string(index=False)); print()
assert len(summary) == 4
"""))
cells.append(code("""
print("=" * 100); print(f"CASE-MODEL METRICS — {len(case)} / 412 rows"); print("=" * 100)
print(case.to_string(index=False)); print()
assert len(case) == 412
print(f"CONFIRMED: {len(case)} rows | {case['sample_id'].nunique()} cases | {case['model'].nunique()} models")
"""))
cells.append(code("""
print("=" * 100); print(f"COMPONENT-MODEL METRICS — {len(comp)} / 608 rows"); print("=" * 100)
print(comp.to_string(index=False)); print()
assert len(comp) == 608
print(f"CONFIRMED: {len(comp)} rows | {comp['model'].nunique()} models")
"""))

nb = nbformat.v4.new_notebook(cells=cells)
for _i, _c in enumerate(nb.cells):
    _c["id"] = f"h2cb2{_i:03d}"
nbformat.write(nb, str(NB))
print(f"wrote {len(cells)} cells -> {NB}")
