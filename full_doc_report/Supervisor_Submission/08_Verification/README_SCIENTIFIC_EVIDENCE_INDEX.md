# README Scientific Evidence Index

Every quantitative claim in [`README.md`](../README.md) and
[`RESEARCH_VISUAL_GALLERY.md`](RESEARCH_VISUAL_GALLERY.md), traced to the artifact it comes
from.

If a number is not in this table, it should not appear in the README.

---

## 1. Architecture and parameter counts

| Claim | Value | Source artifact | Evidence class |
|---|---|---|---|
| Backbone G parameters | 3,523,001 | [`REMEDFILM_FULL_COMPONENT_REGISTRY.json`](../full_doc_report/REMEDFILM_FULL_COMPONENT_REGISTRY.json) | state-dict re-derivation |
| Router B<sub>φ</sub> | 36,801 | same | same |
| Refiner R<sub>ψ</sub> | 1,276,401 | same | same |
| Safety gate S<sub>ω</sub> | 1,217 | same | same |
| FULL assembly | 4,837,420 | same | same (sum of the four) |
| FiLM + embedding share | 90,768 (2.58 %) | same | same |
| Three outcomes on VAL808 | 529 skip · 266 accept · 13 reject | [`phase27_val808_predictions.csv`](../reports/tables/phase27_val808_predictions.csv) | counted from `state_machine_branch` |

> `529 + 266 + 13 = 808`. The identity
> `266 accepted = 97 harmful + 169 beneficial` and `542 unchanged = 529 skipped + 13 rejected`
> also holds exactly.

---

## 2. Internal validation (VAL808, seed 42)

| Claim | Value | Source artifact |
|---|---|---|
| Macro Dice, backbone | 0.8351 | [`REMEDFILM_INTERNAL_EVALUATION.csv`](../full_doc_report/REMEDFILM_INTERNAL_EVALUATION.csv) `MACRO_DOMAIN_EQUAL_WEIGHT` |
| Macro Dice, FULL | 0.8373 | same |
| Paired Δ | +0.002210 | same (`delta_dice`) |
| 95 % CI | [+0.001147, +0.003292] | [`REMEDFILM_FULL_VAL808_METRICS.csv`](../full_doc_report/REMEDFILM_FULL_VAL808_METRICS.csv) / reconciliation record |
| ISIC | 357 · 0.8972 → 0.8981 | same |
| BUSI | 84 · 0.8588 → 0.8589 | same |
| Kvasir | 87 · 0.8202 → 0.8207 | same |
| KUB | 280 · 0.7641 → 0.7715 | same |
| Harmful / beneficial / unchanged | 97 / 169 / 542 | same |

---

## 3. Seven-model comparison

| Model | Parameters | Macro Dice | Source |
|---|---|---|---|
| U-Net | 7,763,041 | 0.7878 | [`phase21_six_model_comparison.csv`](../full_doc_report/Evidence/phase21_six_model_comparison.csv) |
| Attention U-Net | 7,851,285 | 0.7890 | same |
| U-Net++ | 9,159,681 | 0.7920 | same |
| Transformer / MiT-style U-Net | 16,347,777 | 0.8224 | same |
| DeepLabV3+ | 40,347,041 | 0.8277 | same |
| GlobalMedFiLM | 3,523,001 | 0.8351 | Dice from the six-model table; parameters from the component registry |
| ReMedFiLM FULL | 4,837,420 | 0.8373 | [`REMEDFILM_INTERNAL_EVALUATION.csv`](../full_doc_report/REMEDFILM_INTERNAL_EVALUATION.csv) |

> **Evidence class: historical single-seed benchmark, NOT C3.** C3 is 0/24 cells executed.
> Baseline arms were trained under the reduced protocol. The comparison is descriptive and
> the README says so twice.

---

## 4. The two circulating FULL values

| Claim | Value | Source |
|---|---|---|
| Reproducible FULL macro Dice | **0.837290** | [`REMEDFILM_FULL_RESULT_RECONCILIATION.md`](../full_doc_report/REMEDFILM_FULL_RESULT_RECONCILIATION.md) |
| Reproducibility tolerance | 1.8 × 10⁻⁷ vs Phase 27 and Phase 29 | `build_metrics.py` check |
| Rejected value | 0.837862 — appears in no frozen artifact | same reconciliation record |
| Rejected compute | 34.72 GMACs = *always-refine*, not deployed | [`phase34_analytical_compute_summary_v1_3.csv`](../reports/tables/phase34_analytical_compute_summary_v1_3.csv) |

---

## 5. External evaluation (884 cases)

| Claim | Value | Source |
|---|---|---|
| CVC-ClinicDB | 612 · 0.6866 → 0.6897 | [`REMEDFILM_FULL_EXTERNAL_METRICS.csv`](../full_doc_report/REMEDFILM_FULL_EXTERNAL_METRICS.csv) |
| BrEaST-Lesions-USG | 252 · 0.7078 → 0.7081 | same |
| Stones cohort-level | 20 · 0.0808 → 0.0821 | same (zero-fills empty GT) |
| Stones stone-positive | 6 · 0.2695 → 0.2738 | computed from [`c1_external_stress_per_case.csv`](../reports/tables/c1_external_stress_per_case.csv), `gt_empty == False` |
| Stones stone-free | 14 · Dice undefined | same, `gt_empty == True` |
| Stone-free false positives | 14 / 14, specificity 0.0 | [`c2_barr_aggregate.json`](../full_doc_report/Evidence/c2_barr_aggregate.json) `stone_free_failure` |
| HD95 Stones | 166.9 → 169.9 px (n = 6 defined) | external metrics, `n_defined = 6` |
| HD95 CVC | 109.6 → 108.5 px | same |
| HD95 BrEaST | 74.0 → 73.3 px | same |

---

## 6. Ablation (13 arms, ROUTER_DEVELOPMENT 4,957)

| Claim | Value | Source |
|---|---|---|
| A1 unconditional harmful share | 42.67 % | [`REMEDFILM_ABLATION_RESULTS.csv`](../full_doc_report/REMEDFILM_ABLATION_RESULTS.csv) |
| A1 mean Δ Dice | +0.0017 | same |
| A8 (FULL) harmful share | 32.37 % | same |
| A8 mean Δ Dice | +0.0075 | same |
| F1 mean Δ Dice | −0.0326 | same |
| A8 vs A7 | +1.57 × 10⁻⁵, 95 % CI [−1.43 × 10⁻⁵, +5.11 × 10⁻⁵] | [`phase28_table_08_bootstrap_statistics.csv`](../full_doc_report/Evidence/phase28_table_08_bootstrap_statistics.csv) |
| A8 vs A7 verdict | **CI includes zero — inconclusive** | same |

---

## 7. Compute and latency

| Claim | Value | Source |
|---|---|---|
| G analytical compute | 31.55 GMACs | [`phase34_analytical_compute_summary_v1_3.csv`](../reports/tables/phase34_analytical_compute_summary_v1_3.csv) `LITERAL_GLOBAL_ONLY_C1` |
| FULL expected conditional | 32.4379 GMACs | same, `FINAL_A8_C9_EXPECTED_CONDITIONAL` |
| Always-refine | 34.78 GMACs | same, `LITERAL_ALWAYS_REFINE_C2` |
| Routing rate | 24.31 % | same (1205 / 4957) |
| Latency: backbone / refiner / router / gate | 15.77 / 4.53 / 0.37 / 0.25 ms | [`phase34_efficiency_result_v1_4.json`](../full_doc_report/Evidence/phase34_efficiency_result_v1_4.json) |
| Total resident parameters | 4,837,420 | same |

**Analytical ≠ expected conditional.** Analytical GMACs count every multiply-add once for a
fixed graph. Expected conditional GMACs weight the refiner by the measured probability that a
case is routed. The README states this and refuses the Pareto framing.

---

## 8. Robustness

| Claim | Value | Source |
|---|---|---|
| Perturbations × instances | 12 × 12,928 | [`EVIDENCE_INDEX.json`](../full_doc_report/Evidence/EVIDENCE_INDEX.json) |
| Figures | `ROB01`–`ROB03` | [`Robustness/`](../full_doc_report/figures/Robustness/) |

---

## 9. Dataset and split provenance

| Claim | Value | Source |
|---|---|---|
| Split sizes | TRAIN 5,832 · VAL 808 · TEST 1,683 | [`manifests/phase4_v3/`](../manifests/phase4_v3/) |
| Router split | DEV 4,957 + HOLDOUT 875 = 5,832 | same |
| Disjointness | 0 shared image paths or sample IDs across train/val/test | verified against the three manifests |
| KUB units | 873 full-field + 1,385 ROI patches (dataset); 103 + 177 in VAL808 | [`D03_kub_unit_of_analysis`](../full_doc_report/figures/Statistics/D03_kub_unit_of_analysis.png) / manifest paths |

> **Split provenance — read this before quoting a number.** TRAIN/VAL/TEST are the
> project's own partitions of the pooled four-domain pool, **not the official challenge
> splits**. For ISIC 2018 the 357 validation images comprise 231 from the official training
> partition, 14 from the official validation partition and 112 from the official test
> partition. The three project partitions are strictly disjoint. "ISIC validation" in this
> repository therefore means *the project's* validation partition, not the official ISIC
> validation set.

---

## 10. Status claims

| Claim | Source |
|---|---|
| C1: 0 / 6 runs | [`PENDING_CONTROLLED_EXPERIMENTS.md`](../full_doc_report/PENDING_CONTROLLED_EXPERIMENTS.md) |
| C2: not established | `A8 vs A7` CI includes zero (above) |
| C3: 0 / 24 cells | same pending-experiments record |
| TEST1683 access consumed | same |
| Three seeds share one frozen backbone, SD ≈ 1.4 × 10⁻¹⁶ | [`STAT01_seedwise_macro_metrics`](../full_doc_report/figures/Statistics/STAT01_seedwise_macro_metrics.png) |

---

## 11. Claims deliberately **not** made

| Not claimed | Why |
|---|---|
| Causal FiLM attribution | C1 never executed |
| Causal component attribution | C2 not established; A8 vs A7 CI includes zero |
| Independent multi-seed benchmark | C3 0/24; seeds share one backbone |
| Confirmed Pareto frontier | compute is analytical, accuracy protocol unmatched |
| Clinical or safety utility | no prospective cohort, 14/14 stone-free false positives |
| Publication status | no paper, no DOI |
| Interpretability | no saliency/attention analysis exists |

---

## 12. Re-verifying this index

```powershell
# every README link and image resolves
.\.venv\Scripts\python.exe assets\figures\readme\verify_readme_links.py

# the frozen metrics reproduce from masks
.\.venv\Scripts\python.exe full_doc_report\Scripts\build_metrics.py

# the full report QA
.\.venv\Scripts\python.exe full_doc_report\Scripts\verify_verified.py
```
