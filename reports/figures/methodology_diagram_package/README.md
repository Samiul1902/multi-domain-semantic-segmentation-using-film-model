# RA-MedFiLM-BARR — Methodology Figure Evidence Package

**Purpose:** a compact, self-contained evidence package you can hand to another AI to
generate a **publication-quality methodology diagram** that is scientifically faithful to
the CURRENT frozen methodology. Nothing here is a new scientific result: it is a
**documentation / visualization extraction** from existing frozen sources.

**Governance (this package):**

```
NEW MODEL INFERENCE = NO
SMOKE               = NOT RUN
SCIENCE             = NOT RUN
TEST                = NOT ACCESSED
ROUTER_HOLDOUT      = NOT ACCESSED
```

Panels 04 (global probability) and 07 (final segmentation) reuse **existing frozen
caches**; panel 05 (ROI proposal) draws **existing frozen GT-free ROI geometry**. Panel 06
(regional refinement) is omitted because it would require a new model forward.

---

## 1. The four domains and the task-ID mapping (VERIFIED)

> **Important correction:** the task-ID order is **ISIC=0, BUSI=1, KVASIR=2, KUB=3**, not the
> alphabetical order. This is the frozen authoritative mapping
> (`src/data/multidomain_dataset.py:TASK_ID`).

| task_id | domain | dataset | modality | segmentation target |
|---|---|---|---|---|
| 0 | ISIC | ISIC 2018 (Task 1 skin lesion) | dermoscopy (RGB) | skin lesion |
| 1 | BUSI | BUSI-WHU Breast Cancer Ultrasound | ultrasound (L→RGB) | breast lesion |
| 2 | KVASIR | Kvasir-SEG | endoscopy (RGB) | colorectal polyp |
| 3 | KUB | KUB-Stone (X-ray) | radiograph (L/RGB) | kidney/bladder/ureteric stone |

**Every domain is binary foreground/background** (foreground = binarized `mask > 0`). The
domain/task id is **NOT** a segmentation class. Do **not** draw "Class 0/1/2/3" heads.

## 2. Subclasses / categories (VERIFIED)

| domain | authoritative subclasses | status |
|---|---|---|
| ISIC | **NONE_AUTHORIZED_FOR_METHODOLOGY_FIGURE** | category = NOT_AVAILABLE |
| BUSI | **NONE_AUTHORIZED_FOR_METHODOLOGY_FIGURE** | category = NOT_AVAILABLE |
| KVASIR | **NONE_AUTHORIZED_FOR_METHODOLOGY_FIGURE** | category = NOT_AVAILABLE |
| KUB | Kidney_Stone / Bladder_Stone / Ureteric_Stone | **REPORTING METADATA ONLY** |

KUB's three stone categories are **reporting metadata only** — never a segmentation class
or task id. Do not imply separate segmentation heads for them.

## 3. Recommended final methodology figure (PANEL A–D)

- **PANEL A — Multi-domain inputs**
  `BUSI | ISIC | KUB | KVASIR`, each labelled with task_id, modality, segmentation target.
  Use `four_domain_input_montage.png` (and `four_domain_input_gt_montage.png` for GT).
- **PANEL B — Shared Global MedFiLM (G)**
  Multi-task, task-conditioned U-Net with **5 FiLM sites**, **one shared output head**
  (no per-domain heads). Use `existing_visual_references/global_medfilm_structure.png`
  and `existing_visual_references/p24_full_system_architecture.png`.
- **PANEL C — BARR conditional refinement**
  `ROI (0.30) → 202-D → B_phi → SKIP/EXECUTE`; on **EXECUTE**: `R_psi → 16-D + 4-D one-hot
  = 20-D → S_omega → ACCEPT/REJECT`; both branches produce the final segmentation.
  Use `existing_visual_references/p26_canonical_inference_state_machine.png` plus the
  `pre_refinement_202d_feature_breakdown.png` and `post_safety_20d_breakdown.png` schematics.
- **PANEL D — Phase36 robustness evaluation**
  Image perturbations (13) + proposal perturbations (7), seeds 42/123/3407 → metrics.
  **Figures are NOT available** (Phase36 science NOT_STARTED); describe the design from
  `robustness_protocol.json`.

> If the column is narrow, merge PANELS B and C — the state machine figure already spans both.

## 4. Key numbers to respect

- G parameters **3,523,001** · B_phi **36,801** · R_psi **1,276,401** · S_omega **1,217** ·
  wrapper **0 trainable**.
- Thresholds: segmentation **0.50**, ROI proposal **0.30**, ROI margin **0.25** (expansion 1.5),
  S_omega accept **0.50**. Router runtime threshold is the exact rational
  `-5003565381643716252018011/205414980000000000000000000` on `U = delta_hat_final − 0.25·C`.
- Dimensions: input 3×512×512 · 202-D (192 deep + 10 scalars) · B_phi 218→1 · R_psi 4×256×256→1×256×256 ·
  16-D + 4-D = 20-D → S_omega.

## 5. What NOT to invent

- Do not add segmentation classes beyond binary fg/bg.
- Do not draw per-domain output heads.
- Do not add subclasses for ISIC/BUSI/KVASIR (none are authorized).
- Do not label KUB stone types as classes.
- Do not conflate `router_decision` (SKIP/EXECUTE) with the four-state final state.
- Do not show performance numbers on the input montage.
- Do not imply JPG/rotation/crop-style augmentations in the robustness panel —
  the frozen perturbation set is exactly the 13 + 7 listed in `robustness_protocol.json`.

## 6. Files

See `FILE_INDEX.md` (upload-first list) and `methodology_diagram_manifest.json` (full detail).
Verified/source hashes: `source_provenance.json`.
