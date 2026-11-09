# Phase 12 — CLEAN-v3 Oracle Protocol Candidate

- Created: 2026-09-21T00:02:00.193786+00:00
- Manifest `phase4_v3` · taxonomy `kub_size_clean_v3_v1`
- Primary population: **KUB FULL_FIELD VAL 103**
- Model scope: UNet, Attention U-Net, UNet++, DeepLabV3+
- Reference model selected: **False**

## Candidate oracle geometry

- Unit: PER_COMPONENT_BBOX (carried forward from historical design) · connectivity 8 · bbox space ORIGINAL_NATIVE
- Margin: round(margin * bbox_dim); primary 0.25 predeclared · shape SQUARE · resolution 512
- Map-back: restore in FLOAT (no uint8 quantisation); strip pad; place at clip coords
- Fusion: pixelwise MAX of restored component probabilities, threshold after
- Global outside crop: retain global outside crop; report crop-only AND global-retained
- Multi-component: one square crop per native GT component

## Supervisor decisions required (material changes)

| Field | Historical v2 | Proposed clean-v3 | Reason |
|---|---|---|---|
| mapping_back_rule | restore prob to (side,side) bilinear; strip pad; place at clip coords | restore prob to (side,side) bilinear in FLOAT (no uint8 quantisation); strip pad; place at clip coords | removes an undocumented precision loss; improves reproducibility |
| global_outside_crop_rule | zeros outside crop (global prediction NOT retained) | PROPOSE: retain global prediction outside crop (regional-only inside), reported BOTH ways | historical zeros outside crop makes oracle mask crop-only; clean-v3 should separate the regional effect from the global baseline it is compared against |
| model_scope | UNet++ only | ALL FOUR clean-v3 baselines | SR-1 requires architecture-general test |

- New post-hoc thresholds: **0**
- Component correspondence: **DEFINED**
- Regional integration gate candidate: **CREATED**
- Clean oracle inference passes: **0**
- TEST reads: **0** · Phase 13 started: **False**

## Status: READY_FOR_SUPERVISOR_ORACLE_PROTOCOL_FREEZE