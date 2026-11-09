# Phase 28 — Complete 13-Arm Ablation Package: What Is Here and How to Inspect It

**Arms:** `A0, A1, A2, A3, A4, A5, A6, A7, A8, R1, R2, R3, F1`
**Analysis population:** ROUTER_DEVELOPMENT (n = 4,957), the training-side router-development partition
**Protected populations:** `ROUTER_HOLDOUT_875` locked; `TEST1683` never opened
**Package contents:** 42 Python files (`code/`, including the complete local dependency closure), 99 specification/audit/registry files (`configs/`), 23 frozen result tables (`results/`), 8 figures (`figures/`), 1 executed notebook (`notebook/`)

> **No training and no inference were performed to assemble this package.** All copied artifacts are byte-for-byte copies of frozen repository artifacts; the ablation README is newly authored documentation. However, the *underlying evidence* is **hybrid** — see §2. Do not describe the whole 13-arm matrix as "no new training".

---

## 1. File map

| Path | Contents | How to use |
|---|---|---|
| `results/phase28_table_01_arm_definitions.csv` | Canonical 13-arm definitions, roles, primary reference arms, evidence class | Start here for the arm taxonomy |
| `results/phase28_ablation_matrix_13arm.csv` | Full 13-arm matrix with fixed-budget `K` and per-arm endpoints | Master result table |
| `results/phase28_table_02_arm_primary_metrics.csv` | `n_routed`, budget fraction, `sum_true_delta_dice`, benefit capture, harmful share | Primary quantitative comparison |
| `results/phase28_table_03_router_variant_vs_full.csv` | R1/R2/R3 vs canonical A6/A7 | Router-variant contrast |
| `results/phase28_table_04_router_membership_overlap.csv` | Which cases each router selected | Mechanism, not just means |
| `results/phase28_table_05_f1_refiner_level_paired.csv`, `phase28_f1_refiner_level_paired.csv` | F1 refiner-level paired deltas | Refiner ablation |
| `results/phase28_table_06_f1_integrated_secondary.csv`, `phase28_f1_integrated_per_sample.csv` | F1 integrated into the FULL pipeline | System-level consequence of removing `p_global` |
| `results/phase28_table_07_matched_paired_contrasts.csv` | Matched per-sample paired contrasts | Input to bootstrap |
| `results/phase28_table_08_bootstrap_statistics.csv` | 5 paired-bootstrap contrasts, 2,000 replicates, seed 42, 95 % CI | Inferential statistics |
| `results/phase28_table_09_compute_accounting.csv`, `phase28_table_10_execution_counts.csv` | Compute and execution counters | Reproducibility audit |
| `results/phase28_training_run_registry.csv` | 18 historical trained-variant runs with checkpoint/history SHA-256 | Provenance of R1–R3 / F1 |
| `results/phase28_ablation_executability*.csv`, `phase28_specification_completeness*.csv` | v1.0 / v1.1 / v1.2 governance gates | Why some arms are historical vs replayed |
| `results/REMEDFILM_ABLATION_RESULTS.csv` | Report-level consolidated view | Maps to V8 report tables |
| `configs/phase28_ablation_execution_spec_v1_2.md` | **Prospective supervisor operationalization ruling** defining R1–R3/F1 as separately trained variants | Governing semantics |
| `configs/phase24_ablation_plan.csv`, `configs/recipe.py` | Original Phase-24 arm plan and frozen training recipe | Configuration of record |
| `configs/phase28_*.json` (~95 files) | Specification, entry gates, OOF/leakage contracts, no-execution audits, terminal-state freezes | Full governance trail |
| `notebook/phase28_comprehensive_ablation.ipynb` | 92 cells / 45 code cells, **all 45 with saved outputs** | Read-only canonical analysis narrative |
| `code/*phase28*.py` | Matrix build, table/statistics build, figure build, notebook build, spec immutability, registry writers, repair/gate scripts | Regeneration of delivered tables/figures |
| `code/train_phase28_router_variant.py`, `code/train_phase28_f1_refiner.py` | **Historical** training scripts for R1–R3 and F1 | Inspect only; do NOT re-run |
| `code/eval_phase28_f1.py`, `code/eval_phase28_f1_integrated.py` | F1 evaluation scripts | Inspect only |
| `code/phase25c_common.py`, `phase25f_*common.py`, `phase25f_post_safety_features.py` | Shared Phase-25 feature/spec dependencies | Flat-module imports |
| `code/barr_roi.py`, `barr_refiner_dataset.py`, `predicted_roi.py`, `evaluation_metrics.py`, `router_variants.py`, `segmentation.py`, `device.py`, `transforms.py` | Copied `src/` modules required by the above scripts | Flattened dependency set |
| `code/factory.py`, `kub_dataset.py`, `checkpointing.py`, `manifest_guard.py`, `test_lock.py`, `targets.py`, `reproducibility.py`, `unet.py`, `attention_unet.py`, `unetpp.py`, `deeplabv3plus.py`, `kub_localizer.py`, `segformer_b0.py`, `transformer_mit_unet.py` | Complete local import closure for `predicted_roi.py` and the model factory | Makes the shipped dependency graph inspectable; re-execution still needs the original repository on `PYTHONPATH` |
| `code/test_c1_external_evidence.py` | External-evidence regression test | Optional read-only check |
| `figures/p28_fig1…fig8*.png` | 8 frozen ablation figures | Direct viewing |

---

## 2. Evidence class — the single most important caveat

| Arms | Evidence class | What actually happened |
|---|---|---|
| `A0`, `A1` | `ENDPOINT_BY_CONSTRUCTION` | Analytical endpoints (global-only; always-refine). No model was run. |
| `A2`–`A8` | `PRIOR_CANONICAL_EVIDENCE_EXACT` | Reconstructed / replayed from prior canonical frozen artifacts and saved labels; **analysis-only**, no new training. |
| `R1`, `R2`, `R3`, `F1` | `PHASE28_TRAINED_ABLATION_VARIANT` | **Genuinely, separately trained controlled variants.** The Phase-28 run registry records **18 historical training runs**: 15 router folds (R1/R2/R3 × 5 folds, seeds 42000–42004) + 3 F1 refiner folds (seed 42). |

The v1.2 execution spec explicitly rules that "without X" means removing X from the model **during fitting and evaluation**, i.e. training a genuinely different model — **not** inference-time feature zeroing or post-hoc masking. Therefore:

- ✅ Correct: "A0–A8 were reconstructed/replayed from frozen canonical evidence; R1–R3 and F1 come from 18 historically trained controlled variants."
- ❌ Incorrect: "The whole Phase-28 13-arm matrix required no new training."
- ❌ Incorrect: "R1–R3 are feature-ablations of the canonical router at inference time."

`ROUTER_HOLDOUT_875` was locked and `TEST1683` never opened. The v1.2 spec itself is `SPECIFICATION / GOVERNANCE ONLY — no execution performed` with all execution counters zero; the 18 runs are recorded in the separate frozen training-run registry.

---

## 3. Headline frozen results (read directly from `results/`)

| Contrast | Mean paired difference | 95 % CI (2,000-replicate paired bootstrap, seed 42) | Reading |
|---|---:|---|---|
| `R1_vs_A6C7` | −0.000981 | [−0.001278, −0.000697] | Removing deep global features hurts |
| `R2_vs_A6C7` | −0.001514 | [−0.001805, −0.001232] | Removing `task_id` hurts more |
| `R3_vs_A6C7` | −0.001499 | [−0.001813, −0.001213] | Scalar-only features hurt |
| `A8_vs_A7` | **+0.0000157** | **[−0.0000143, +0.0000510]** | **CI includes zero → INCONCLUSIVE; do not claim safety gate improves Dice** |
| `F1_integrated_vs_A8` | −0.009972 | [−0.010842, −0.009178] | Removing the `p_global` channel is clearly harmful |

All five contrasts are labelled `DESCRIPTIVE_NO_POST_HOC_CORRECTION`; no multiplicity correction was applied.

Primary arm endpoints (`phase28_table_02_arm_primary_metrics.csv`), fixed budget `K = 1,239` (25 % of 4,957) for A2–A7/R1–R3/F1:

| Arm | n routed | Budget | Σ true ΔDice | Mean ΔDice (routed) | Harmful activation share |
|---|---:|---:|---:|---:|---:|
| A0 | 0 | 0.000 | 0.000 | 0.000000 | 0.000 |
| A1 | 4,957 | 1.000 | 8.219 | 0.001658 | 0.4267 |
| A2 random | 1,239 | 0.250 | 1.751 | 0.001413 | 0.4439 |
| A3 entropy | 1,239 | 0.250 | 8.903 | 0.007185 | 0.3188 |
| A4 margin | 1,239 | 0.250 | 8.821 | 0.007119 | 0.3196 |
| A5 ROI-size | 1,239 | 0.250 | −0.537 | −0.000433 | 0.4641 |
| A6 learned gain | 1,239 | 0.250 | 8.979 | 0.007247 | 0.3325 |
| A7 + cost | 1,239 | 0.250 | 8.979 | 0.007247 | 0.3325 |
| **A8 + safety (canonical)** | **1,205** | **0.243** | **9.056** | **0.007516** | **0.3237** |
| R1 | 1,239 | 0.250 | 4.114 | 0.003320 | 0.3737 |
| R2 | 1,239 | 0.250 | 1.475 | 0.001191 | 0.4350 |
| R3 | 1,239 | 0.250 | 1.550 | 0.001251 | 0.4229 |
| F1 | 1,239 | 0.250 | −40.373 | −0.032585 | 0.6885 |

**Do not confuse the 32.37 % figure:** `390/1205 = 32.37 %` is a *conditional* harmful-activation share among A8's selected cases; the correct unconditional harmful rate is `42.6670 % → 7.8677 %`. `n_executed` is a **policy property**, not a measured property of a fixed cohort. These are **in-sample** ROUTER_DEVELOPMENT results with **zero GPU** in the reconstruction, and are **not** a causal ablation of a jointly trained network.

---

## 4. How to inspect / regenerate (analysis only — no training)

From the repository root, using the project interpreter (`.venv/Scripts/python.exe`, Python 3.11.9):

```bash
# 1. Verify the frozen tables are internally consistent (reads CSV/JSON only)
.venv/Scripts/python.exe -c "
import csv, json, pathlib
p = pathlib.Path('full_doc_report/Supervisor_Submission/04_Ablation_Phase28/results')
arms = list(csv.DictReader((p/'phase28_table_01_arm_definitions.csv').open(encoding='utf-8')))
m    = list(csv.DictReader((p/'phase28_table_02_arm_primary_metrics.csv').open(encoding='utf-8')))
print('arms defined:', len(arms), [a['arm'] for a in arms])
print('arms with metrics:', len(m))
assert {a['arm'] for a in arms} == {x['arm'] for x in m}
"

# 2. Re-derive the bootstrap table from the frozen matched-paired contrasts
#    (script is supplied in code/; it reads only frozen CSVs)
# 3. Open notebook/phase28_comprehensive_ablation.ipynb in Jupyter and READ
#    the saved outputs. Do not "Run All" — training cells are archived and blocked.
```

**Flat-module convention.** The scripts were copied out of `src/` and `scripts/` into two flat `code/` directories. Imports such as `from src.data.barr_roi import …` therefore require the original repository package layout on `PYTHONPATH`; the equivalent flattened modules (`barr_roi.py`, `predicted_roi.py`, …) are supplied alongside so a supervisor can read the exact implementation without reconstructing the tree. `phase25c_common`, `phase25f_execution_common`, `phase25f_post_safety_features` and `phase25f_spec_repair_common` are imported as top-level flat modules and are present in `code/`.

**To fully re-execute** the historical training or inference you would need the original repository tree, the frozen checkpoints (whose SHA-256 hashes are in `results/phase28_training_run_registry.csv` but whose binaries are deliberately **not** shipped), the ROUTER_DEV/ROUTER_HOLDOUT partitions, and an explicit authorization. That is **outside** this supervisor package and was **not** performed.

---

## 5. Known limitations of this ablation evidence

1. **Hybrid provenance** (§2): reconstructed endpoints + historically trained variants, not one uniform experiment.
2. **In-sample**: all `A*` endpoints and contrasts are computed on ROUTER_DEVELOPMENT (n = 4,957); no independent held-out confirmation.
3. **`A8_vs_A7` is inconclusive** — CI spans zero.
4. **No multiplicity correction** on the five bootstrap contrasts.
5. **`A7` and `A6` are numerically identical** in the primary table (Σ ΔDice 8.9785736244 for both) — the cost term changed selection semantics but not the reconstructed aggregate; this is a property of the replay, not evidence of a cost-aware gain.
6. **Not a causal ablation of a jointly trained FULL network**: the FULL system is four sequentially trained, frozen-then-assembled components.
7. `POLICY_COMPARISON` is not a causal ablation; `n_executed` is a policy property.
8. The notebook contains `TRAINING(1)|INFERENCE(3)|TEST_PATH_REFERENCE` markers per the repository's notebook inventory and is classified `ARCHIVAL_ONLY_TRAINING_CELLS_BLOCKED` / `SOURCE_OF_TRUTH`; it ships with outputs for reading, not for re-execution.
