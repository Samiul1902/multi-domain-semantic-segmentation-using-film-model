# Retrospective Notebook Visualization Inventory

**Audit Date:** 2026-09-19  
**Standard Version:** NV-1  
**Project Root:** `D:\Softfors\jup`  
**Governing Principle:** Canonical frozen notebooks are strictly preserved; their accepted SHA-256 hashes are immutable. Visual companions are planned as read-only, non-destructive companions.

---

## 1. Project Notebook Visualization Audit

| Notebook Filename | Phase | Status | Total Cells | Executed Cells | Rendered Image Outputs | Companion Needed? | Companion Rationale |
|---|---|---|:---:|:---:|:---:|:---:|---|
| `00_project_initialization.ipynb` | Phase 0 | CANONICAL_FROZEN | 2 | 1 | 0 | **NO** | Administrative setup and directory structure certification. |
| `01_environment_and_data_audit.ipynb` | Phase 1 | CANONICAL_FROZEN | 2 | 1 | 0 | **NO** | Hardware and software environment certification. |
| `02_dataset_discovery.ipynb` | Phase 2 | CANONICAL_FROZEN | 2 | 1 | 0 | **NO** | Catalog discovery and filesystem manifest integrity. |
| `03_kub_forensic_audit.ipynb` | Phase 3 | CANONICAL_FROZEN | 1 | 0 | 0 | **NO** | Forensic file hash verification. |
| `03_leakage_and_split_audit.ipynb` | Phase 3 | CANONICAL_FROZEN | 3 | 1 | 0 | **NO** | Patient-level leak detection audit. |
| `04_kub_characterization.ipynb` | Phase 4 | CANONICAL_FROZEN | 8 | 4 | 7 | **YES** | Dataset characterization & representative KUB radiograph panels. |
| `05_kub_object_size_taxonomy.ipynb` | Phase 5 | CANONICAL_FROZEN | 11 | 5 | 9 | **YES** | Object size distribution & stone component taxonomy visuals. |
| `06_kub_baseline_infrastructure.ipynb` | Phase 8 | CANONICAL_FROZEN | 11 | 8 | 2 | **NO** | Smoke test infrastructure validation. |
| `07_kub_unet_baseline_training.ipynb` | Phase 9 | CANONICAL_FROZEN | 22 | 10 | 9 | **YES** | UNet baseline training curves & 16-case prediction visual companion. |
| `08_kub_baseline_comparison.ipynb` | Phase 10 | CANONICAL_FROZEN | 24 | 11 | 10 | **YES** | Multi-architecture comparison (UNet, AttnUNet, UNet++, DeepLabV3+) predictions. |
| `09_kub_failure_analysis.ipynb` | Phase 11 | CANONICAL_FROZEN | 28 | 13 | 14 | **YES** | Failure case visual gallery & error taxonomy panel. |
| `09b_kub_manual_prediction_demo.ipynb` | Phase 11B | CANONICAL_FROZEN | 7 | 3 | 1 | **NO** | Single interactive demo notebook. |
| `10_kub_oracle_roi_upper_bound.ipynb` | Phase 12 | CANONICAL_FROZEN | 19 | 8 | 9 | **YES** | Oracle ROI zoom & boundary recovery prediction panels. |
| `11_kub_predicted_roi_localizer.ipynb` | Phase 13 | CANONICAL_FROZEN | 18 | 8 | 10 | **YES** | Learned localizer heatmaps & proposal grid visualizations. |
| `11b_kub_learned_localizer.ipynb` | Phase 13B | CANONICAL_FROZEN | 30 | 14 | 2 | **YES** | Compact CenterNet localizer training & heatmap visualizations. |
| `11c_kub_final_localizer_redesign.ipynb` | Phase 13B | CANONICAL_FROZEN | 46 | 18 | 8 | **YES** | Final Stage-4D localizer heatmaps & 494 canonical proposals. |
| `12_phase14_15_gate_closure.ipynb` | Phase 14/15 Admin | SUPERSEDED_ADMIN | 18 | 8 | 0 | **NO** | Historical administrative gate evaluation (superseded by executed branch). |
| `13_phase14_regional_refiner_diagnostic.ipynb` | Phase 14 | CANONICAL_FROZEN | 47 | 21 | 10 | **YES** | Phase 14 16-case deep regional refinement visual companion. |

---

## 2. Priority Retrospective Visual Companions

To be housed in `notebooks/retrospective/`:
1. `04_kub_characterization_visual_companion.ipynb` (Phase 4)
2. `05_kub_object_size_taxonomy_visual_companion.ipynb` (Phase 5)
3. `07_kub_unet_baseline_training_visual_companion.ipynb` (Phase 9)
4. `08_kub_baseline_comparison_visual_companion.ipynb` (Phase 10)
5. `09_kub_failure_analysis_visual_companion.ipynb` (Phase 11)
6. `10_kub_oracle_roi_upper_bound_visual_companion.ipynb` (Phase 12)
7. `11c_kub_stage4d_localizer_visual_companion.ipynb` (Phase 13B)
8. `13_phase14_regional_refiner_diagnostic_visual_companion.ipynb` (Phase 14)

