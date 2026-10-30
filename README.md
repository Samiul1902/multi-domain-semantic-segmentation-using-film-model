# RA-MedFiLM-Seg++

Medical image segmentation research project.

## H3 Supply-Axis Evaluation (Post-Phase14)

| Item | Value |
|------|-------|
| Notebook 05 | `notebooks/phasewise/post_phase14_h3_proposal_supply/05_h3_supply_axis_evaluation.ipynb` |
| Notebook 05 SHA-256 | `fe69339ceddca6cd7d4a949f81d59154ccd19057b4d9bd24158d8ff825e9b1b0` |
| Evaluation artifact | `reports/audits/h3_supply_axis_evaluation.json` |
| Evaluation artifact SHA-256 | `00e6f41351d725817810eba13b738b2631c5b0cc023af192b1479af7321b9687` |
| Per-component table | `reports/tables/h3_supply_eval_per_component.csv` (152 rows) |
| Per-image table | `reports/tables/h3_supply_eval_per_image.csv` (103 rows) |
| Evaluation state | `H3_SUPPLY_AXIS_EVALUATION_COMPLETE__FORMAL_ADJUDICATION_PENDING` |
| Selected epoch | 54 |
| Checkpoint SHA-256 | `d875cac7d09bbc3d32232191f0af2c138e5a74682fc63e4d6e01f30345eca75e` |
| VAL population | 103 images, 152 GT components (TINY=72, SMALL=28, MEDIUM=36, LARGE=16) |
| Frozen decode | threshold=0.10, margin=0.20, top_k=5, nms_iou=0.30 |
| Zero-proposal GT | 27/152 (baseline 79, recovered 52) |
| Zero-proposal TINY | 22/72 (baseline 57, recovered 35) |
| R_H3 | -0.60 (insufficient) |
| Criterion A (TINY<=20/72) | FAIL (22 > 20) |
| Criterion B (GT<=35/152) | PASS (27 <= 35) |
| Failure boundary | FIRED (R_H3 < 0.15) |
| TEST reads | 0 |
| Phase 15 | NOT_STARTED_AND_NOT_AUTHORIZED |

Formal H3 adjudication (Notebook 06) requires separate supervisor authorization.

<!-- BEGIN PROJECT-EVALUATION-METRICS-AUDIT -->
## Project-Wide Evaluation-Metrics Audit (Post-H3-Downstream)

Audit + standardization + descriptive backfill of the completed KUB research
line (Phases 09-14 and the post-Phase14 H3 training / supply / downstream
steps). This is **not** a new hypothesis test: no frozen gate, threshold or
checkpoint is changed, and the frozen H3 formal metric domain (detection =
component overlap >= 1 px; `TinyRecall_H3 = 59/72`, `R_H3 = 2/15`) is
unchanged.

| Item | Value |
|------|-------|
| Audit notebook | `notebooks/evaluation/project_evaluation_metrics_audit.ipynb` |
| Audit notebook SHA-256 | `ed4814d135b5beee0771d7ba9d0ce631036a800525f2a6f64b7c6c71171d151e` |
| Reusable metric module | `src/metrics/evaluation_metrics.py` |
| Metric module SHA-256 | `6c515f6f1a495315c79238292c385a082ae8347489130ad5bff34d74c4f181f6` |
| Metric registry | `reports/audits/project_metric_registry.json` (35 metrics) |
| Metric registry SHA-256 | `08647ec9d33fcfa68f74ef299a47308cbbf8d6ef3a4904452e940445d0d2de54` |
| Project metric inventory | `reports/audits/project_evaluation_metrics_inventory.json` / `.csv` (12 rows) |
| Inventory JSON SHA-256 | `af4f573578df106f89bde25f30bd95e688b337505b70d81cadd83bbe43aea549` |
| Inventory CSV SHA-256 | `7443531450a0f33d5d3a0dc28b4068df57765c62884f1813a76dace9887580ed` |
| Descriptive backfill artifact | `reports/audits/project_evaluation_metrics_backfill.json` |
| Descriptive backfill SHA-256 | `a79e531a231a03252331ff24a5bb11c2fec7d857f100c0676edf1c3410ef6b54` |
| Proposal backfill artifact | `reports/audits/project_evaluation_proposal_metrics_backfill.json` |
| Proposal backfill SHA-256 | `3f4d4d2599586185b7837ddf23779a1ad1cf5ff8ecdd713d958b199c765c1583` |
| Safe-replay verdict | `REPLAY_PERFORMED_LAWFULLY` (8/8 conditions) |
| Reproduction gate | 4/4 arms exact (GLOBAL / ORACLE / PREDICTED / H3) |
| Boundary units | pixels (no pixel-spacing metadata; never mm) |
| New-metric label | `DESCRIPTIVE_SUPPORTING_METRIC__NOT_PROSPECTIVE_GATE` |
| H3-specific label | `DESCRIPTIVE_SUPPORTING_METRIC__NOT_H3_GATE` |
| TEST reads | 0 |
| Frozen gates changed | False |
| Terminal state | `PROJECT_EVALUATION_METRICS_AUDIT_COMPLETE__H3_ADJUDICATION_PENDING` |

Formal H3 adjudication (Notebook 07) remains **PENDING** and requires separate
supervisor authorization.
<!-- END PROJECT-EVALUATION-METRICS-AUDIT -->
