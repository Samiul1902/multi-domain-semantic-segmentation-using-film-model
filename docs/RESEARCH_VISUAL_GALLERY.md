# ReMedFiLM — Research Visual Gallery

The complete verified figure collection. The root [`README.md`](../README.md) shows only the
strongest panels; everything else lives here.

Every figure below is generated from a frozen artifact and carries an **evidence class**
recording what it is entitled to claim. Nothing in this gallery was produced by a new
forward pass, a new training run, or a reopened TEST1683 evaluation.

**How to read the evidence classes**

| Class | Meaning |
|---|---|
| `CANONICAL_ARCHITECTURE_CONTRACT` | derived from the architecture specification and checkpoint state dicts |
| `DERIVED_FROM_SAVED_PREDICTIONS` | re-scored from masks already on disk |
| `SAVED_PREDICTIONS_VAL808` | the 808-image validation population, frozen predictions |
| `FROZEN_HISTORICAL_TRAINING` | genuine per-epoch logs from completed historical runs |
| `FROZEN_HISTORICAL_ABLATION` | the Phase 28 13-arm ablation, frozen |
| `EXTERNAL_RETROSPECTIVE_SAVED_PREDICTIONS` | separate external cohorts, single retrospective evaluation |
| `FROZEN_ROBUSTNESS_EXECUTION` | the frozen 12-perturbation robustness sweep |
| `MIXED_ANALYTICAL_COMPUTE_AND_FROZEN_ACCURACY` | compute is analytical, accuracy is frozen — **not a matched benchmark** |

Machine-readable registry: [`full_doc_report/figure_registry.json`](../full_doc_report/figure_registry.json)
(49 entries). Per-panel provenance for the README prediction set:
[`README_VISUAL_ASSET_MANIFEST.md`](README_VISUAL_ASSET_MANIFEST.md).

---

## 1. Four-domain segmentation predictions

**Research question.** What does ReMedFiLM FULL actually output, and where does it differ
from its backbone?

| | |
|---|---|
| **Evaluated models** | GlobalMedFiLM (G) and ReMedFiLM FULL, side by side on the same sample |
| **Dataset / split** | ISIC 2018 · BUSI-WHU · Kvasir-SEG · KUB-StoneX — VAL808, single seed 42 |
| **Source** | `reports/figures/phase27_preservation/masks/{sample_id}_{global,final}.png`; routing from `reports/tables/phase27_val808_predictions.csv`; Dice from `full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv` |
| **Interpretation** | FULL differs from G only on accepted refinements (266 / 808). On the 529 skipped cases the two masks are byte-identical by construction. The overlay shows where the difference helps (green) and hurts (red). |
| **Known limitation** | Single seed; validation population only. Example images are embedded for illustration and remain under their source dataset licences. |

| Figure | Content |
|---|---|
| [README Figure 2](../assets/figures/readme/remedfilm_four_domain_predictions.png) | one verified case per domain |
| [ISIC](../assets/figures/readme/prediction_isic.png) · [BUSI](../assets/figures/readme/prediction_busi.png) · [Kvasir](../assets/figures/readme/prediction_kvasir.png) · [KUB](../assets/figures/readme/prediction_kub.png) | six/five/six/six cases per domain |
| [`SEG_ISIC_global_vs_full`](../full_doc_report/figures/Semantic%20segmentation/SEG_ISIC_global_vs_full.png) | worst / median / best Δ Dice, deterministic |
| [`SEG_BUSI_global_vs_full`](../full_doc_report/figures/Semantic%20segmentation/SEG_BUSI_global_vs_full.png) | worst / median / best Δ Dice |
| [`SEG_KVASIR_global_vs_full`](../full_doc_report/figures/Semantic%20segmentation/SEG_KVASIR_global_vs_full.png) | worst / median / best Δ Dice |
| [`SEG_KUB_global_vs_full`](../full_doc_report/figures/Semantic%20segmentation/SEG_KUB_global_vs_full.png) | worst / median / best Δ Dice |
| [`SEG_*_refinement_accepted`](../full_doc_report/figures/Semantic%20segmentation/) | proof that FULL ≠ relabelled G on accepted cases |

> **KUB unit caveat.** 177 of the 280 KUB validation cases are ROI instance patches and 103
> are full-field radiographs. They are different image units; every KUB row states which.
> **No full-field KUB case was ever accepted by the router**, so any accepted-refinement KUB
> example is necessarily an ROI patch.

---

## 2. Internal performance

**Research question.** Does the FULL assembly beat its own backbone, and by how much?

| | |
|---|---|
| **Evaluated models** | GlobalMedFiLM (G) vs ReMedFiLM FULL; plus five conventional baselines |
| **Dataset / split** | VAL808 (357 ISIC · 84 BUSI · 87 Kvasir · 280 KUB) |
| **Source** | `full_doc_report/REMEDFILM_FULL_VAL808_METRICS.csv`, `REMEDFILM_INTERNAL_EVALUATION.csv` |
| **Interpretation** | Macro Dice 0.8351 → 0.8373, paired Δ +0.002210, 95 % CI [+0.001147, +0.003292]. The gain is concentrated in KUB (+0.0075); ISIC, BUSI and Kvasir each move by < 0.001. |
| **Known limitation** | Single seed. The CI excludes zero but the effect is small and not replicated across independent backbones. |

| Figure | Content |
|---|---|
| [README Figure 7](../assets/figures/readme/internal_domain_performance.png) | domain-wise Dice with sample counts |
| [README Figure 8](../assets/figures/readme/historical_model_comparison.png) | seven-model macro Dice — **historical benchmark, not C3** |
| [`I1_domain_metric_comparison`](../full_doc_report/figures/Internal%20validation/I1_domain_metric_comparison.png) | Dice / IoU / precision / recall per domain |
| [`I2_paired_delta_forest`](../full_doc_report/figures/Internal%20validation/I2_paired_delta_forest.png) | per-domain and macro paired Δ with 10,000-replicate bootstrap |
| [`I3_paired_delta_distribution`](../full_doc_report/figures/Internal%20validation/I3_paired_delta_distribution.png) | per-image Δ distribution and beneficial/unchanged/harmful split |
| [`I4_hd95_comparison`](../full_doc_report/figures/Internal%20validation/I4_hd95_comparison.png) | HD95 from saved masks |

---

## 3. External performance and failure

**Research question.** Does any of this survive domain shift?

| | |
|---|---|
| **Evaluated models** | GlobalMedFiLM and ReMedFiLM FULL |
| **Dataset / split** | CVC-ClinicDB (612) · BrEaST-Lesions-USG (252) · Stones-Where-Are-You (20, of which 14 stone-free) — 884 cases total |
| **Source** | `full_doc_report/REMEDFILM_FULL_EXTERNAL_METRICS.csv`; `reports/tables/c1_external_stress_per_case.csv` |
| **Interpretation** | CVC 0.6866 → 0.6897; BrEaST 0.7078 → 0.7081. Stones collapses: 0.2695 → 0.2738 among the six stone-positive cases, and **14/14 stone-free images receive foreground** (case-level specificity 0.0). The gate scores refinement benefit, not lesion presence. |
| **Known limitation** | Single retrospective evaluation. Patient-level independence is not verifiable for BrEaST. The cohort-level Stones Dice of 0.0808 zero-fills empty-GT cases and should not be read as a segmentation score. |

| Figure | Content |
|---|---|
| [README Figure 9](../assets/figures/readme/external_evaluation.png) | Dice with CI + honest stone stratification |
| [`EXT01_external_dice`](../full_doc_report/figures/External%20evaluation/EXT01_external_dice.png) | external Dice per cohort with bootstrap CIs |
| [`EXT02_external_delta`](../full_doc_report/figures/External%20evaluation/EXT02_external_delta.png) | paired Dice difference per cohort |
| [`EXT03_stonefree_false_positive`](../full_doc_report/figures/External%20evaluation/EXT03_stonefree_false_positive.png) | the preserved negative finding |

---

## 4. Epoch-wise training and improvement

**Research question.** Are these genuine learning curves, and what do the components
actually log?

| | |
|---|---|
| **Evaluated models** | G (81 epochs), R<sub>ψ</sub>, B<sub>φ</sub>, S<sub>ω</sub> — four independent stages |
| **Dataset / split** | TRAIN 5,832 / VAL 808 |
| **Source** | `full_doc_report/REMEDFILM_COMPONENT_TRAINING_HISTORY.csv`; `REMEDFILM_TRAINING_RUN_REGISTRY.csv` |
| **Interpretation** | The backbone converges by ~epoch 66 (best macro Dice 0.8351). The downstream components were fitted afterwards against the frozen backbone and logged **training loss only**. |
| **Known limitation** | R<sub>ψ</sub>, B<sub>φ</sub> and S<sub>ω</sub> have **no validation metrics recorded**; those panels are marked `NOT_RECORDED` rather than interpolated. Seeds 42/123/3407 share one frozen backbone, so they are not independent runs. |

| Figure | Content |
|---|---|
| [`training_history.png`](../assets/figures/readme/training_history.png) | four-stage dashboard with unrecorded metrics marked |
| [`T1_train_val_loss`](../full_doc_report/figures/Training%20curves/T1_train_val_loss.png) | epoch-wise BCE+Dice loss |
| [`T2_val_dice_across_epochs`](../full_doc_report/figures/Training%20curves/T2_val_dice_across_epochs.png) | macro Dice with selected checkpoint |
| [`T3_val_iou_across_epochs`](../full_doc_report/figures/Training%20curves/T3_val_iou_across_epochs.png) | per-domain and macro IoU |
| [`T4_per_domain_learning_curves`](../full_doc_report/figures/Training%20curves/T4_per_domain_learning_curves.png) | four domains; KUB lags throughout |
| [`T5_learning_rate_schedule`](../full_doc_report/figures/Training%20curves/T5_learning_rate_schedule.png) | logged LR, no reconstruction |
| [`T6_best_epoch_selection`](../full_doc_report/figures/Training%20curves/T6_best_epoch_selection.png) | checkpoint-selection epochs |
| [`T7_multiseed_histories`](../full_doc_report/figures/Training%20curves/T7_multiseed_histories.png) | downstream runs per seed, separated from the backbone |
| [`T8_training_improvement_summary`](../full_doc_report/figures/Training%20curves/T8_training_improvement_summary.png) | epoch 1 / best / final Dice |

---

## 5. Subgroup performance

**Research question.** Does the model fail in a size- or subtype-dependent way?

| | |
|---|---|
| **Evaluated models** | ReMedFiLM FULL and GlobalMedFiLM |
| **Dataset / split** | KUB subgroup strata within VAL808 |
| **Source** | `reports/tables/phase21_kub_size_stratification.csv` |
| **Interpretation** | Small stones are the weakest stratum, consistent with the KUB gain (+0.0075) being the only domain-level improvement of practical size. |
| **Known limitation** | Subgroup cells are small; no multiplicity correction is applied. |

| Figure | Content |
|---|---|
| [`SG1_kub_stone_subgroups`](../full_doc_report/figures/Internal%20validation/SG1_kub_stone_subgroups.png) | per-subgroup Dice inside KUB |
| [`SG2_kub_size_stratification`](../full_doc_report/figures/Internal%20validation/SG2_kub_size_stratification.png) | Dice against the frozen size taxonomy |

---

## 6. Ablation

**Research question.** Which component actually contributes, and is the safety gate worth
anything?

| | |
|---|---|
| **Evaluated models** | 13 arms: A0–A8, R1–R3, F1 |
| **Dataset / split** | ROUTER_DEVELOPMENT 4,957 |
| **Source** | `full_doc_report/REMEDFILM_ABLATION_RESULTS.csv`; `full_doc_report/Evidence/phase28_table_08_bootstrap_statistics.csv` |
| **Interpretation** | Routing is what matters: unconditional refinement (A1) harms 42.67 % of routed cases for a mean Δ of only +0.0017, while the learned router (A8) cuts harmful share to 32.37 % and lifts mean Δ Dice to +0.0075. Removing the global-probability input (F1) collapses the system to −0.0326. |
| **Known limitation** | **A8 vs A7 is inconclusive**: +1.57 × 10⁻⁵, 95 % CI [−1.43 × 10⁻⁵, +5.11 × 10⁻⁵], includes zero. Component attribution is measured, not causal — that is C2, and it is not established. Budget is a policy property, not an accuracy result. |

| Figure | Content |
|---|---|
| [`complete_ablation.png`](../assets/figures/readme/complete_ablation.png) | all 13 arms with budget and harmful share |
| [`ABL01_arm_mean_delta`](../full_doc_report/figures/Ablation/ABL01_arm_mean_delta.png) | routed mean Δ Dice per arm |
| [`ABL02_paired_contrasts_forest`](../full_doc_report/figures/Ablation/ABL02_paired_contrasts_forest.png) | paired contrasts with 95 % CIs |
| [`ABL03_ablation_diagnostics`](../full_doc_report/figures/Ablation/ABL03_ablation_diagnostics.png) | harmful share, benefit capture, routed volume |

---

## 7. Component progression

**Research question.** What does each assembly stage add, and what does it cost?

| | |
|---|---|
| **Evaluated models** | backbone → unrouted refinement → learned routing → post-safety gate → FULL |
| **Dataset / split** | mixed — see the `DEVELOPMENT_EVIDENCE_MIXED_POPULATION` class |
| **Source** | `reports/tables/phase34_analytical_compute_summary_v1_3.csv`; `REMEDFILM_ABLATION_AND_PROGRESSION.csv` |
| **Interpretation** | Unrouted refinement costs 34.78 GMACs and raises harmful activation; routing brings cost back to 32.44 GMACs and cuts harmful share; the safety gate leaves compute unchanged. |
| **Known limitation** | The stages are not a single controlled sweep — they mix populations, which is why the registry marks the evidence class as mixed. The harmful-share series is conditional on routed cases and is not comparable to the 42.67 % unconditional figure. |

| Figure | Content |
|---|---|
| [`PROG01_stage_compute_and_harm`](../full_doc_report/figures/Progression/PROG01_stage_compute_and_harm.png) | analytical compute and harmful share per stage |
| [`PROG02_benefit_harm_tradeoff`](../full_doc_report/figures/Progression/PROG02_benefit_harm_tradeoff.png) | beneficial vs harmful activation per arm |

---

## 8. Routing and safety

**Research question.** Where does each sample go, and what does each branch deliver?

| | |
|---|---|
| **Evaluated models** | ReMedFiLM FULL routing policy |
| **Dataset / split** | VAL808 |
| **Source** | `reports/tables/phase27_val808_predictions.csv` |
| **Interpretation** | 529 skip · 266 accept · 13 reject. Rejected refinements fall back to the global mask, so their Δ Dice is exactly 0 by construction — a property of the policy, not a lucky result. |
| **Known limitation** | The gate is a benefit classifier, not an abnormality detector; it cannot suppress a confident false positive (see § 3). |

| Figure | Content |
|---|---|
| [`RT01_routing_outcomes`](../full_doc_report/figures/Routing%20and%20safety/RT01_routing_outcomes.png) | branch distribution and Δ Dice per branch |
| [`RT02_stage_flow`](../full_doc_report/figures/Routing%20and%20safety/RT02_stage_flow.png) | counts at every pipeline stage |

---

## 9. Error propagation

**Research question.** When refinement goes wrong, how wrong does it get?

| | |
|---|---|
| **Evaluated models** | ReMedFiLM FULL |
| **Dataset / split** | VAL808 |
| **Source** | `full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv` |
| **Interpretation** | 97 of 808 cases are harmed and 169 helped; 542 are unchanged because the router skipped them. The worst accepted refinement loses −0.0448 Dice — the gate did not catch it. F1 shows what happens when the global probability input is removed: −0.0326 mean Δ. |
| **Known limitation** | The harm rate is conditional on the routing policy; a different budget changes the denominator. |

| Figure | Content |
|---|---|
| [`SEG_failure_cases`](../full_doc_report/figures/Semantic%20segmentation/SEG_failure_cases.png) | the six largest negative Δ Dice cases |
| [`I3_paired_delta_distribution`](../full_doc_report/figures/Internal%20validation/I3_paired_delta_distribution.png) | beneficial / unchanged / harmful split |
| [`ABL01_arm_mean_delta`](../full_doc_report/figures/Ablation/ABL01_arm_mean_delta.png) | the F1 collapse |

---

## 10. Robustness

**Research question.** Does the system degrade gracefully under image corruption?

| | |
|---|---|
| **Evaluated models** | ReMedFiLM FULL vs GlobalMedFiLM |
| **Dataset / split** | 12 perturbations × 12,928 instances |
| **Source** | `ROB01`–`ROB03` in [`Robustness/`](../full_doc_report/figures/Robustness/); execution record in `reports/audits/` |
| **Interpretation** | Resolution loss dominates degradation; KUB degrades most of the four domains. The clean-equivalence gate confirms the robustness sweep reproduces the frozen clean predictions exactly, so the perturbation effect is not confounded by a pipeline change. |
| **Known limitation** | Synthetic perturbations only — no prospective acquisition shift. |

| Figure | Content |
|---|---|
| [`ROB01_perturbation_degradation`](../full_doc_report/figures/Robustness/ROB01_perturbation_degradation.png) | mean paired Δ Dice per perturbation |
| [`ROB02_domain_degradation`](../full_doc_report/figures/Robustness/ROB02_domain_degradation.png) | perturbation families by domain |
| [`ROB03_clean_equivalence_gate`](../full_doc_report/figures/Robustness/ROB03_clean_equivalence_gate.png) | the clean-prediction equivalence check |

---

## 11. Computational efficiency

**Research question.** What does the extra accuracy cost?

| | |
|---|---|
| **Evaluated models** | seven models; G and FULL with verified compute |
| **Dataset / split** | analytical counts at 1×3×512×512; latency measured on one RTX 3060 Ti |
| **Source** | `reports/tables/phase34_analytical_compute_summary_v1_3.csv`; `full_doc_report/Evidence/phase34_efficiency_result_v1_4.json` |
| **Interpretation** | G is 31.55 analytical GMACs; FULL is 32.44 **expected conditional** GMACs because only 24.31 % of cases reach the refiner. Always-refine would cost 34.78. Measured latency: 15.77 ms backbone, 4.53 ms refiner, 0.37 ms router, 0.25 ms gate. |
| **Known limitation** | Compute is analytical, not profiled per layer, and accuracy comes from a different (frozen) protocol. **This is not a confirmed Pareto frontier.** `EFF01` labels the FULL x-position as "analytical", which is imprecise — the value is expected-conditional; README Figure 10 states this explicitly. |

| Figure | Content |
|---|---|
| [README Figure 10](../assets/figures/readme/remedfilm_accuracy_compute.png) | accuracy vs parameters, and vs verified GMACs |
| [`EFF01_accuracy_vs_compute`](../full_doc_report/figures/Efficiency/EFF01_accuracy_vs_compute.png) | accuracy vs analytical compute |
| [`EFF02_latency_breakdown`](../full_doc_report/figures/Efficiency/EFF02_latency_breakdown.png) | measured per-component latency |
| [`EFF03_accuracy_vs_parameters`](../full_doc_report/figures/Efficiency/EFF03_accuracy_vs_parameters.png) | accuracy vs parameter count |

---

## 12. Interpretability

**Research question.** *Why* did the router select this region?

| | |
|---|---|
| **Status** | **Not available.** |
| **Source** | — |
| **Interpretation** | No saliency, attention-rollout, SHAP or occlusion analysis was ever produced for this project. The nearest available evidence is the TP/FP/FN overlay, which shows *where* the masks differ but not *why* the router scored a candidate highly. |
| **Known limitation** | This is a genuine gap, not a missing file. Presenting an overlay as an interpretability method would overstate it. |

**What does exist:** the per-sample router score and safety probability are recorded for
every validation case in `reports/tables/phase27_val808_predictions.csv`, so a
router-score-vs-outcome analysis could be built from frozen data without new inference. It
has not been built.

---

## 13. Dataset and statistics context

| Figure | Content |
|---|---|
| [`D01_domain_and_split_composition`](../full_doc_report/figures/Statistics/D01_domain_and_split_composition.png) | per-domain TRAIN/VAL counts from the phase4_v3 manifest |
| [`D02_foreground_area_distribution`](../full_doc_report/figures/Statistics/D02_foreground_area_distribution.png) | GT lesion area per domain; KUB smallest |
| [`D03_kub_unit_of_analysis`](../full_doc_report/figures/Statistics/D03_kub_unit_of_analysis.png) | full-field vs ROI patch pooling warning |
| [`STAT01_seedwise_macro_metrics`](../full_doc_report/figures/Statistics/STAT01_seedwise_macro_metrics.png) | per-seed macro Dice with across-seed band |
| [`STAT02_bootstrap_distribution`](../full_doc_report/figures/Statistics/STAT02_bootstrap_distribution.png) | bootstrap distribution of the paired macro Δ |
| [`STAT03_seedwise_per_domain`](../full_doc_report/figures/Statistics/STAT03_seedwise_per_domain.png) | per-domain FULL Dice by seed |
| [`STAT04_population_accounting`](../full_doc_report/figures/Statistics/STAT04_population_accounting.png) | cohort accounting; populations are never pooled |

> **Seed caveat.** STAT01 and STAT03 show three seeds, but seeds 42/123/3407 re-fit only the
> downstream components on **one shared frozen backbone** — the backbone score is identical
> across seeds (SD ≈ 1.4 × 10⁻¹⁶). Read these as downstream-variance plots, not independent
> replications.

---

## Coverage summary

| Requested category | Status | Where |
|---|---|---|
| Four-domain segmentation predictions | ✅ | § 1 |
| Internal performance | ✅ | § 2 |
| External performance | ✅ | § 3 |
| Epoch-wise improvement | ✅ | § 4 |
| Subgroup performance | ✅ | § 5 |
| Ablation | ✅ | § 6 |
| Component progression | ✅ | § 7 |
| Routing and safety | ✅ | § 8 |
| Error propagation | ✅ | § 9 |
| Robustness | ✅ | § 10 |
| Computational efficiency | ✅ | § 11 |
| Interpretability | ❌ **not produced** | § 12 |

---

## Rebuilding this gallery

```powershell
# research figure family (49 registered figures)
.\.venv\Scripts\python.exe full_doc_report\Scripts\build_figures.py

# README visual set (11 figures)
.\.venv\Scripts\python.exe assets\figures\readme\build_readme_figures.py

# verify the whole report
.\.venv\Scripts\python.exe full_doc_report\Scripts\verify_verified.py
```

No command above trains a model or runs inference.
