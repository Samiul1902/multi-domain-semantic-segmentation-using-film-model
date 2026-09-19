"""Append Part 3 Full Diagnostic Evaluation cells to 13_phase14_regional_refiner_diagnostic.ipynb."""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "13_phase14_regional_refiner_diagnostic.ipynb"


def make_cell(cell_type, source_text):
    lines = [line + "\n" for line in source_text.split("\n")]
    if lines and lines[-1] == "\n":
        lines[-1] = ""
    cell = {
        "cell_type": cell_type,
        "metadata": {},
        "source": lines,
    }
    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    return cell


def main():
    with open(NOTEBOOK_PATH, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # Check if Part 3 is already appended, if so remove previous Part 3 cells to avoid duplicate appends
    split_idx = len(nb["cells"])
    for i, cell in enumerate(nb["cells"]):
        src = "".join(cell.get("source", []))
        if "PHASE 14 -- PART 3 FULL DIAGNOSTIC EVALUATION" in src or "PHASE 14 — PART 3 FULL DIAGNOSTIC EVALUATION" in src:
            split_idx = i
            break

    nb["cells"] = nb["cells"][:split_idx]

    new_cells = []

    # Cell 1: Header Markdown
    new_cells.append(make_cell("markdown", """---
# PHASE 14 — PART 3 FULL DIAGNOSTIC EVALUATION
**Frozen Validation Evaluation across GLOBAL_ONLY, ORACLE_REGIONAL, and PREDICTED_REGIONAL.**

- **Primary Population:** KUB FULL_FIELD VAL only (106 images, 156 authoritative components: 73 Tiny, 29 Small, 36 Medium, 18 Large).
- **Core Scientific Question:**
  1. Measure regional-refiner potential under ideal ROI localization (Oracle Regional).
  2. Measure performance retention under the frozen predicted proposal system (Stage-4D localizer).
  3. Determine the practical net benefit of the predicted regional cascade.
- **Frozen References:** $D_g = 0.652776$, $T_g = 0.780822$
- **Governance:** TEST split locked (0 reads authorized, 0 metrics), external data = NO, no training / optimizer steps."""))

    # Cell 2: Checkpoint & Configuration Provenance
    new_cells.append(make_cell("code", """import hashlib, json
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

PROJECT_ROOT = Path("..").resolve()
TABLES_DIR = PROJECT_ROOT / "reports" / "tables"
AUDITS_DIR = PROJECT_ROOT / "reports" / "audits"
FIG_DIR = PROJECT_ROOT / "reports" / "figures" / "phase14_diagnostic"
FIG_DIR.mkdir(parents=True, exist_ok=True)

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

ckpts = {
    "Global UNet++ Baseline": PROJECT_ROOT / "checkpoints" / "phase10_kub_unetpp_seed42_512" / "best.pt",
    "Regional Refiner UNet": PROJECT_ROOT / "checkpoints" / "phase14_diag_regional_unet_oracletrain_a3_seed42_v1" / "best.pt",
    "Stage-4D CenterNet Localizer": PROJECT_ROOT / "checkpoints" / "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1" / "best.pt"
}

print("=== CHECKPOINT PROVENANCE & CRYPTOGRAPHIC INTEGRITY ===")
for name, p in ckpts.items():
    sha = sha256_file(p)
    print(f"- {name}:\\n  Path: {p}\\n  SHA-256: {sha}\\n")"""))

    # Cell 3: Mode Summary Table
    new_cells.append(make_cell("markdown", """## 1. Mode Summary Performance
Comparison across the three frozen evaluation modes:
- `GLOBAL_ONLY`: Baseline UNet++ without regional processing.
- `ORACLE_REGIONAL`: Regional refiner evaluated with ground-truth component proposals (0.20 margin).
- `PREDICTED_REGIONAL`: Regional refiner evaluated with frozen Stage-4D localizer proposals (threshold=0.10, margin=0.20, Top-K=5, NMS=0.30)."""))

    new_cells.append(make_cell("code", """mode_summary = pd.read_csv(TABLES_DIR / "phase14_part3_mode_summary.csv")
cols_to_display = [
    "mode", "mean_dice", "median_dice", "overall_recall90", "tiny_recall90",
    "small_recall90", "medium_recall90", "large_recall90", "hard_tiny_recovered",
    "global_empty_recovered", "mean_fp_components_per_image", "mean_roi_area_fraction"
]
print("=== MODE SUMMARY TABLE ===")
display(mode_summary[cols_to_display])"""))

    # Cell 4: Component Stratification by Size
    new_cells.append(make_cell("markdown", """## 2. Component Recall by Size Stratum
Authoritative 156 connected components on FULL_FIELD VAL:
- Tiny: 73 components
- Small: 29 components
- Medium: 36 components
- Large: 18 components"""))

    new_cells.append(make_cell("code", """comp_metrics = pd.read_csv(TABLES_DIR / "phase14_part3_component_metrics.csv")
size_summary = []
for size, grp in comp_metrics.groupby("size_group"):
    size_summary.append({
        "Size Stratum": size,
        "Total Components": len(grp),
        "Global Detected": int(grp["global_recall90_success"].sum()),
        "Global Recall": float(grp["global_recall90_success"].mean()),
        "Oracle Detected": int(grp["oracle_recall90_success"].sum()),
        "Oracle Recall": float(grp["oracle_recall90_success"].mean()),
        "Predicted Detected": int(grp["predicted_recall90_success"].sum()),
        "Predicted Recall": float(grp["predicted_recall90_success"].mean()),
    })
df_size = pd.DataFrame(size_summary).sort_values("Total Components", ascending=False)
display(df_size)"""))

    # Cell 5: Hard Cases Recovery
    new_cells.append(make_cell("markdown", """## 3. Recovery of Hard Failure Cases
- **Hard-Tiny Set (16 components):** components missed by global baseline.
- **Global-Empty Set (7 images):** images where global baseline predicted 0 foreground pixels."""))

    new_cells.append(make_cell("code", """hard_cases = pd.read_csv(TABLES_DIR / "phase14_part3_hardcase_summary.csv")
print("=== HARD-TINY COMPONENT RECOVERY (16 components) ===")
ht = hard_cases[hard_cases["case_type"] == "HARD_TINY_COMPONENT"]
display(ht[["sample_id", "component_id", "pixels", "global_success", "oracle_success", "predicted_success"]])
print(f"Summary: Global={ht['global_success'].sum()}/16, Oracle={ht['oracle_success'].sum()}/16, Predicted={ht['predicted_success'].sum()}/16\\n")

print("=== GLOBAL-EMPTY IMAGE RECOVERY (7 images) ===")
ge = hard_cases[hard_cases["case_type"] == "GLOBAL_EMPTY_IMAGE"]
display(ge[["sample_id", "pixels", "global_success", "oracle_success", "predicted_success", "details"]])
print(f"Summary: Global={ge['global_success'].sum()}/7, Oracle={ge['oracle_success'].sum()}/7, Predicted={ge['predicted_success'].sum()}/7")"""))

    # Cell 6: Proposal and ROI Burden
    new_cells.append(make_cell("markdown", """## 4. ROI & Proposal Burden
Evaluates the spatial localization burden and proposal distribution for Oracle and Predicted regional modes."""))

    new_cells.append(make_cell("code", """roi_burden = pd.read_csv(TABLES_DIR / "phase14_part3_roi_proposal_burden.csv")
display(roi_burden)"""))

    # Cell 7: Inference Latency & Runtime
    new_cells.append(make_cell("markdown", """## 5. Development Runtime & Inference Efficiency
Measured on NVIDIA GeForce RTX 3060 Ti with CUDA synchronization."""))

    new_cells.append(make_cell("code", """runtime_df = pd.read_csv(TABLES_DIR / "phase14_part3_runtime.csv")
display(runtime_df)"""))

    # Cell 8: Diagnostic Contrasts & Decision Gates
    new_cells.append(make_cell("markdown", """## 6. Diagnostic Contrasts & Gate Hierarchy
Mathematical evaluation of the frozen protocol decision gates:
- **Contrast G (Refiner Potential):** $G = T_o - T_g$
- **Contrast R (Retention Fraction):** $R = (T_p - T_g) / G$
- **Step 1:** $G \\ge 0.05$ AND $D_o \\ge 0.632776$
- **Step 2:** $R \\ge 0.50$
- **Step 3:** $T_p \\ge 0.780822$, $D_p \\ge 0.632776$, Hard-Tiny $\\ge 2/16$, Global-Empty $\\ge 1/7$"""))

    new_cells.append(make_cell("code", """with open(AUDITS_DIR / "phase14_part3_diagnostic_evaluation.json", "r") as f:
    audit = json.load(f)

contrasts = audit["diagnostic_contrasts"]
gates = audit["gates"]

print("=== FROZEN DIAGNOSTIC CONTRASTS ===")
print(f"Tg (Frozen Global Tiny Recall):    {contrasts['Tg']:.6f}")
print(f"Dg (Frozen Global FULL_FIELD Dice): {contrasts['Dg']:.6f}")
print(f"To (Oracle Tiny Recall):           {contrasts['To']:.6f}")
print(f"Do (Oracle FULL_FIELD Dice):       {contrasts['Do']:.6f}")
print(f"Tp (Predicted Tiny Recall):        {contrasts['Tp']:.6f}")
print(f"Dp (Predicted FULL_FIELD Dice):    {contrasts['Dp']:.6f}")
print(f"G = To - Tg:                       {contrasts['G']:+.6f}")
print(f"R = (Tp - Tg) / G:                 {contrasts['R_string']}")

print("\\n=== GATE STEP 1: REFINER POTENTIAL ===")
print(f"Condition: G >= 0.05 AND Do >= 0.632776")
print(f"Result:    {'PASS' if gates['step_1']['pass'] else 'FAIL'} (G={gates['step_1']['G']:+.6f}, Do={gates['step_1']['Do']:.6f})")

print("\\n=== GATE STEP 2: PROPOSAL RETENTION ===")
print(f"Condition: R >= 0.50")
print(f"Result:    {gates['step_2']['status']} (R={gates['step_2']['R']})")

print("\\n=== GATE STEP 3: PRACTICAL NET BENEFIT ===")
print(f"Condition: Tp >= 0.780822 AND Dp >= 0.632776 AND Hard-Tiny >= 2/16 AND Global-Empty >= 1/7")
print(f"Result:    {'PASS' if gates['step_3']['pass'] else 'FAIL'} (Tp={gates['step_3']['Tp']:.6f}, Dp={gates['step_3']['Dp']:.6f}, HardTiny={gates['step_3']['hard_tiny_recovered']}/16, GE={gates['step_3']['global_empty_recovered']}/7)")

print("\\n=== FINAL DIAGNOSTIC CLASSIFICATION ===")
print(f"Classification:  {audit['final_classification']}")
print(f"Phase 15 Status: {audit['phase15_status']}")"""))

    # Cell 9: Scientific Figures
    new_cells.append(make_cell("markdown", """## 7. Diagnostic Visualizations"""))

    new_cells.append(make_cell("code", """# Figure A: Mode Dice Comparison
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

img_metrics = pd.read_csv(TABLES_DIR / "phase14_part3_image_metrics.csv")
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Dice Distribution Boxplot
dice_data = [img_metrics["global_dice"], img_metrics["oracle_dice"], img_metrics["predicted_dice"]]
bp = axes[0].boxplot(dice_data, patch_artist=True,
                     boxprops=dict(facecolor="#ccebc5", color="#2b8cbe"),
                     medianprops=dict(color="red", linewidth=2))
axes[0].set_xticks([1, 2, 3])
axes[0].set_xticklabels(["GLOBAL_ONLY", "ORACLE_REGIONAL", "PREDICTED_REGIONAL"])
axes[0].set_ylabel("FULL_FIELD Dice")
axes[0].set_title("Validation FULL_FIELD Dice Distribution (N=106)")
axes[0].grid(True, linestyle="--", alpha=0.5)

# Component Recall by Size Barplot
strata = ["TINY", "SMALL", "MEDIUM", "LARGE"]
x = np.arange(len(strata))
width = 0.25

g_rec = [df_size.loc[df_size["Size Stratum"] == s, "Global Recall"].values[0] for s in strata]
o_rec = [df_size.loc[df_size["Size Stratum"] == s, "Oracle Recall"].values[0] for s in strata]
p_rec = [df_size.loc[df_size["Size Stratum"] == s, "Predicted Recall"].values[0] for s in strata]

axes[1].bar(x - width, g_rec, width, label="GLOBAL_ONLY", color="#41b6c4")
axes[1].bar(x, o_rec, width, label="ORACLE_REGIONAL", color="#225ea8")
axes[1].bar(x + width, p_rec, width, label="PREDICTED_REGIONAL", color="#e7298a")
axes[1].set_xticks(x)
axes[1].set_xticklabels(strata)
axes[1].set_ylabel("Component Recall@90")
axes[1].set_title("Component Recall@90 by Size Stratum")
axes[1].set_ylim(0, 1.1)
axes[1].grid(True, linestyle="--", alpha=0.5)
axes[1].legend()

plt.tight_layout()
fig_path = FIG_DIR / "phase14_part3_diagnostic_summary.png"
plt.savefig(fig_path, dpi=150)
plt.close(fig)
print(f"Saved figure to: {fig_path}")"""))

    # Cell 10: Conclusion Markdown
    new_cells.append(make_cell("markdown", """## 8. Diagnostic Conclusions & Governance
1. **Refiner Potential Validated (Step 1 PASS):**
   - The regional refiner architecture and training design are validated under ideal localization: Oracle FULL_FIELD Dice reaches **0.813166** (+0.160 gain vs baseline), and achieves **100% Tiny recall (73/73)**, recovering **16/16 hard-Tiny components** and **7/7 global-empty cases**.
2. **Proposal Bottleneck Identified (Step 2 FAIL):**
   - When driven by the frozen Stage-4D localizer, retention is only **12.5%** ($R = 0.125000 < 0.50$), and FULL_FIELD Dice drops to **0.349511** due to false-positive off-target proposals that induce regional false positives (FP/image increases to 6.08).
   - Final classification: **`DIAGNOSTIC_PROPOSAL_BOTTLENECK`**.
3. **Governance Locks Preserved:**
   - TEST split reads: 0
   - External data: NO
   - Training executed in notebook: NO
   - Phase 15 status: **`NOT_AUTHORIZED`** (stopped, awaiting supervisor review)."""))

    nb["cells"].extend(new_cells)

    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)

    print(f"[Phase 14 Part 3] Appended Part 3 cells to {NOTEBOOK_PATH}. Total cells now: {len(nb['cells'])}")


if __name__ == "__main__":
    main()

