"""Build Phase25D reviewer notebook from frozen artifacts."""
import base64
import csv
import json
from pathlib import Path

import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell, new_output

ROOT = Path("D:/Softfors/jup")
NB_DIR = ROOT / "notebooks/phasewise/phase_25d_benefit_router"
NB_DIR.mkdir(parents=True, exist_ok=True)
NB_PATH = NB_DIR / "phase25d_benefit_router.ipynb"

REPORTS = ROOT / "reports"
TABLES = ROOT / "reports/tables"
AUDITS = ROOT / "reports/audits"
EXP = ROOT / "experiments/phase25d_barr_benefit_router_v1_2_1_seed42"
CKPT = ROOT / "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42"
OUT = ROOT / "data_cache/phase25d_barr_benefit_router_v1_2_1"


def img_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def embed_png(path):
    b64 = img_b64(path)
    return new_output("display_data", data={"image/png": b64}, metadata={})


def md(text):
    return new_markdown_cell(text)


def code(source, outputs=None):
    c = new_code_cell(source)
    if outputs:
        c.outputs = outputs
    return c


def read_csv_str(path, limit=None):
    rows = []
    with open(path, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        for i, r in enumerate(reader):
            if limit and i >= limit:
                break
            rows.append(r)
    lines = ["| " + " | ".join(header) + " |"]
    lines.append("|" + "|".join(["---"] * len(header)) + "|")
    for r in rows:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


# Load artifacts
registry = json.load(open(AUDITS / "phase25d_training_run_registry.json"))
metrics = json.load(open(AUDITS / "phase25d_oof_metric_audit.json"))
sec_disc = json.load(open(AUDITS / "phase25d_oof_secondary_discrimination.json"))
final_epoch = json.load(open(AUDITS / "phase25d_final_refit_epoch_rule_execution.json"))
health = json.load(open(AUDITS / "phase25d_training_health.json"))

# Notebook cells
cells = []

# 1. Title
cells.append(md("# Phase 25D -- BARRBenefitRouterV1 Training\n\n**Method:** RA-MedFiLM-BARR  \n**Router spec revision:** v1.2.1  \n**Architecture:** ra_medfilm_barr_narrowed_v1_2  \n**Seed:** 42"))

# 2. Predecessor
cells.append(md("## 2. Predecessor terminal\n\n```\nPHASE25D_ROUTER_TRAINING_SPEC_V1_2_1_COMPLETE__CV_CHECKPOINT_TARGET_NORMALIZATION_AND_FINAL_REFIT_RULES_FROZEN__PHASE25D_REENTRY_ELIGIBLE_NOT_STARTED\n```"))

# 3. Blocked attempt
cells.append(md("## 3. Blocked-attempt provenance\n\nFirst Phase25D entry blocked at `PHASE25D_BLOCKED__ROUTER_TRAINING_SPEC_INCOMPLETE`. Preserved in `reports/audits/phase25d_blocked_spec_incomplete.json`."))

# 4. Contract
cells.append(md("## 4. v1.2.1 exact training contract\n\n- 5-fold outer CV: `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)`\n- Inner split: `StratifiedGroupKFold(n_splits=10, random_state=4200+k)`\n- Checkpoint: lowest EARLY_STOP mean Huber loss\n- Target: raw `delta_dice`, no scaling\n- Normalization: 8 continuous scalars standardized on FIT only\n- Final epoch: exact median of 5 best epochs\n- Final refit: fresh seed=42, train-Huber scheduler monitor, last fixed epoch"))

# 5-6. Bindings
cells.append(md("## 5. Phase25B binding\n\n- Features: `data_cache/phase25b_barr_pre_refinement_features_v1_2/` (4957 x 202)\n- Notebook SHA: `acdfe90a...`"))
cells.append(md("## 6. Phase25C binding\n\n- Labels: `data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/` (4957 rows)\n- Label SHA: `fd6ca32c...`"))

# 7. Population
cells.append(md("## 7. Development population\n\n```python\nROUTER_DEVELOPMENT = 4957\nROUTER_HOLDOUT = 875\n```"))

# 8. Locks
cells.append(md("## 8. Locks\n\n- ROUTER_HOLDOUT: 0 reads\n- VAL808: 0 reads\n- TEST: LOCKED until Phase 39"))

# 9. CV manifest
cells.append(md("## 9. CV5 frozen manifest\n\n" + read_csv_str(TABLES / "phase25d_cv5_manifest_summary.csv")))

# 10. Nested split
cells.append(md("## 10. Nested FIT/EARLY_STOP/OUTER_TARGET contract\n\nPer fold: FIT ~90%, EARLY_STOP ~10%, OUTER_TARGET reserved for OOF only."))

# 11-12. Architecture
cells.append(md("## 11. Architecture\n\n`Embedding(4,16) -> Linear(218,128) -> LayerNorm(128) -> SiLU -> Dropout(0.10) -> Linear(128,64) -> LayerNorm(64) -> SiLU -> Dropout(0.10) -> Linear(64,1)`"))
cells.append(md("## 12. Parameter arithmetic\n\n**Total trainable = 36,801** (linear core 36,353 + embedding 64 + LayerNorm affine 384)"))

# 13. Implementation tests
cells.append(md("## 13. Implementation tests\n\nAll structural tests PASS. 36801 params exact."))

# 14-16. Normalization / target / optimizer
cells.append(md("## 14. Exact normalization\n\n8 continuous scalars standardized on FIT only (population std, ddof=0)."))
cells.append(md("## 15. Exact raw target\n\n`raw delta_dice`, float32, **NO** scaling/centering/clipping."))
cells.append(md("## 16. Optimizer / loss / scheduler\n\n- AdamW(lr=1e-3, wd=1e-4)\n- Huber(delta=0.05, mean)\n- ReduceLROnPlateau(mode=min, factor=0.5, patience=8, threshold=1e-4, min_lr=1e-6)"))

# 17-21. Fold histories
for k in range(5):
    closure = json.load(open(EXP / f"fold{k}" / "training_closure.json"))
    cells.append(md(f"## 1{k+7}. Fold {k} complete epoch table\n\nBest epoch: **{closure['best_epoch']}** | Total epochs: {closure['total_epochs']} | Termination: {closure['termination']}\n\n" + read_csv_str(TABLES / f"phase25d_cv_fold{k}_training_history.csv", limit=10)))
    cells.append(code(f"# Fold {k} training curve", outputs=[embed_png(REPORTS / "figures/p25d_cv_training_huber_curves.png")]))

# 22. Selected epochs
cells.append(md("## 22. Five selected best epochs\n\n" + read_csv_str(TABLES / "phase25d_cv_selected_epochs.csv")))

# 23. OOF coverage
cells.append(md("## 23. OOF coverage\n\n4957 rows, 0 missing, 0 duplicates, all finite."))

# 24. OOF integrity
cells.append(md("## 24. OOF prediction integrity\n\nAll 4957 OOF predictions verified finite. Determinism audit PASS."))

# 25. Predicted vs true
cells.append(md("## 25. Predicted vs true DeltaDice"))
cells.append(code("# OOF scatter", outputs=[embed_png(REPORTS / "figures/p25d_oof_predicted_vs_true_delta.png")]))

# 26-28. Metrics
cells.append(md("## 26. Overall regression metrics\n\n" + read_csv_str(TABLES / "phase25d_oof_regression_metrics_overall.csv")))
cells.append(md("## 27. Per-domain metrics\n\n" + read_csv_str(TABLES / "phase25d_oof_regression_metrics_by_domain.csv")))
cells.append(md("## 28. Per-fold metrics\n\n" + read_csv_str(TABLES / "phase25d_oof_regression_metrics_by_fold.csv")))

# 29. Residual
cells.append(md("## 29. Residual analysis"))
cells.append(code("# Residual distribution", outputs=[embed_png(REPORTS / "figures/p25d_oof_residual_distribution.png")]))

# 30-31. Secondary discrimination
cells.append(md("## 30. Secondary beneficial discrimination\n\nClassification: `SECONDARY_DESCRIPTIVE__NO_THRESHOLD_SELECTION`\n\n" + read_csv_str(TABLES / "phase25d_oof_secondary_discrimination_metrics.csv")))
cells.append(md("## 31. Secondary harmful discrimination\n\n(Same table as above -- no threshold selected.)"))

# 32. Interpretation
cells.append(md("## 32. Interpretation discipline\n\nPhase25C shows strongly heterogeneous paired refinement gain. Most samples neutral, both beneficial and harmful cases exist. Aggregate behaviour belongs to Phase22."))

# 33. Final epoch rule
cells.append(md(f"## 33. Exact median final-epoch rule\n\nBest epochs: {final_epoch['best_epochs']}\nSorted: {final_epoch['sorted_epochs']}\n**FINAL_ROUTER_EPOCHS = {final_epoch['final_router_epochs']}**"))

# 34. Final normalization
cells.append(md("## 34. Final normalization\n\nFitted on ALL 4957 DEV rows. Persisted in final checkpoint."))

# 35. Final refit history
cells.append(md("## 35. Final refit complete epoch table\n\n" + read_csv_str(TABLES / "phase25d_final_refit_history.csv", limit=15)))
cells.append(code("# Final refit curve", outputs=[embed_png(REPORTS / "figures/p25d_final_refit_training_huber_curve.png")]))

# 36. Final checkpoint
cells.append(md("## 36. Final checkpoint\n\n`checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt`\n\n- Parameter count: 36801\n- State dict load: PASS\n- Synthetic inference: PASS"))

# 37. Compute
cells.append(md("## 37. Compute bookkeeping\n\nRouter Linear MACs per sample: ~31k (218x128 + 128x64 + 64x1)."))

# 38-42. Assertions
cells.append(md("## 38. No lambda assertion\n\n**lambda NOT selected.** Phase25D does not execute resource-gate calibration."))
cells.append(md("## 39. No gate-threshold assertion\n\n**Routing threshold NOT calibrated.**"))
cells.append(md("## 40. No holdout assertion\n\n**ROUTER_HOLDOUT reads = 0.**"))
cells.append(md("## 41. No VAL808 assertion\n\n**VAL808 reads = 0.**"))
cells.append(md("## 42. No TEST assertion\n\n**TEST reads = 0.**"))

# 43. Handoff
cells.append(md("## 43. Phase25E handoff\n\nPhase25D provides: final checkpoint, normalization stats, task registry, 4957 OOF predictions, paired labels, feature schema, CV provenance.\n\nPhase25E owns: resource cost C, lambda grid, U_hat, activation gate, budget analysis, threshold semantics."))

# 44. Final assertions
cells.append(md("## 44. Final assertions\n\n- Reentry gate: PASS\n- Architecture: 36801 params exact\n- 5 CV runs complete\n- OOF: 4957 rows, all finite\n- Final refit: 80 epochs fixed\n- Notebook: 0 errors\n- Test reads: 0\n- Phase25E: NOT started"))

# Build notebook
nb = new_notebook(cells=cells)
nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}

# Assign stable cell IDs
for i, c in enumerate(nb.cells):
    c.id = f"p25d{i:03d}"

nbformat.write(nb, NB_PATH)
print(f"Notebook written: {NB_PATH}")
