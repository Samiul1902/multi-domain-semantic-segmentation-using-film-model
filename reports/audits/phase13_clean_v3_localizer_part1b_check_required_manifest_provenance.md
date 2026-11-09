# PHASE-13 PART-1B — CHECK_REQUIRED — MANIFEST PROVENANCE BINDING

- **experiment_id**: `phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3`
- **document_type**: `TRAINING_BLOCKED_PRE_EPOCH_1`
- **status**: `CHECK_REQUIRED`
- **created_utc**: 2026-09-21T04:55:46.439044+00:00
- **checkpoint selection label**: `EXECUTING_HISTORICAL_4TERM_FIXED_CONFIG_SELECTION`

## Failure

```
ValueError: manifest hash 'train_table_sha256' resolved empty; refusing empty hashes
  raised at scripts/training/train_phase13_clean_v3_localizer.py:330
  called from scripts/training/train_phase13_clean_v3_localizer.py:978 (main)
```

stdout log: `reports/audits/phase13_clean_v3_localizer_training_stdout.log` SHA `632f03e558424291e4c83b1c99c48f617025958e55fc3b5d252e8f6eb9e8f8a2`

## Root cause

compute_manifest_hashes() attempts to build an authoritative per-sample provenance digest from a column literally named 'image_sha256' on the filtered TRAIN and VAL frames. _shas_of() returns "" when the column is absent (line 303-304), and the non-empty guard (line 328-330) then fails loudly.

- `image_sha256` present in the sample tables: **False**
- Sample tables inspected: `reports/tables/kub_train_samples_sized.csv`, `reports/tables/kub_val_samples_sized.csv`
- Repo-wide: **no `image_sha256` column exists anywhere** in `reports/tables` or `manifests/`.

**Why the unit-test gate did not catch this:** Gate test N (tests/test_phase13_part1b_r0r1_gates.py) constructs a synthetic DataFrame that DOES contain an 'image_sha256' column, so _shas_of() returns a non-empty digest and the test passes. The real sample tables carry no such column, so the real call site fails. The tested input shape does not match the production input shape.

## Why STOP and not repair

1. The blocker is in executable provenance code (a scientific-artifact guard), not in a docs/state file.
2. There is no authorized source for an 'image_sha256' value for the 770 TRAIN / 103 VAL KUB samples; fabricating per-sample digests would create non-physical provenance.
3. Substituting a different column (e.g. a path or sample_id digest) would silently change the meaning of 'train_table_sha256', i.e. a scientific/provenance contract change that the task specification does not authorize.
4. Part 1B §0 authorizes proceeding only when the two pre-CUDA gates pass; an unrelated executable blocker discovered during training must be escalated, not worked around.
5. The run console shows an unrelated safe-delete FAIL_CLOSED warning for the (already released) lock path; it did not affect the failure and no lock file remains.

## Side effects / state

| field | value |
|---|---|
| CUDA initialized | True |
| model constructed | False |
| optimizer created | False |
| forward passes | 0 |
| optimizer steps | 0 |
| training epochs | 0 |
| history rows written | 0 |
| best.pt written | False |
| latest.pt written | False |
| training-start audit written | False |
| training-completion audit written | False |
| proposals generated | 0 |
| grid configurations evaluated | 0 |
| TEST content reads | 0 |
| experiment dir contents | `[]` |
| checkpoint dir contents | `[]` |
| lock file present | False |
| historical artifacts modified | False |

## Gates completed BEFORE the blocker (all PASS)

- **pre_cuda_gate_A_r2a_sha_provenance**: PASS
- **pre_cuda_gate_B_synthetic_metric_contract**: PASS (45/45 combined suite)
- **section_4_immutability**: PASS (17/17)
- **section_5_population**: PASS (770/1161 TRAIN, 103/152 VAL, overlap 0, ROI excluded)
- **section_6_val_component_source**: PASS (103 cases / 152 components; strata 72/28/36/16)
- **section_7_loss**: PASS (CenterNetFocalLoss alpha=2.0 beta=4.0, no Dice)
- **section_8_heatmap_contract**: PASS (512->128, explicit, fail-loud)
- **section_9_training_core**: PASS (AdamW 1e-4/1e-4, CosineAnnealingLR T_max=100, seed 42, batch 4, accum 1, AMP, 100 epochs, patience 15)
- **section_10_proposal_config**: PASS (exactly one: 0.10/0.20/5/0.30, grid disabled)
- **section_11_checkpoint_selection**: PASS (4-term strict lexicographic, ties=BAD_EPOCH, patience 15)
- **section_12_device_and_lock**: PASS (RTX 3060 Ti, sm_86, 8.59 GB, CUDA required enforced, no concurrent lock)

## Requested decision

Supervisor must either (a) authorize adding/producing an authoritative per-sample image-provenance column ('image_sha256' or an explicitly named equivalent) for the 770 TRAIN / 103 VAL KUB samples, or (b) authorize an amendment to compute_manifest_hashes() that binds provenance to sources that actually exist (e.g. the phase4_v3 manifest file SHAs, which already compute successfully, plus the sample-table file SHA), with the change recorded as a provenance-binding amendment. Neither is authorized by the current task text.

**Recommended option**: (b) provenance-binding amendment — the manifest file SHAs and sample-table file SHAs already resolve non-empty; only the per-sample rolling digest lacks a source.

---

STOP. DO NOT RUN THE 20-CONFIG GRID. DO NOT RETUNE PROPOSAL PARAMETERS. DO NOT RUN STANDALONE
BEST-CHECKPOINT PROPOSAL ANALYSIS. DO NOT RUN PREDICTED-REGION SEGMENTATION. DO NOT ISSUE GO /
REVISE_LOCALIZER / NO_GO. DO NOT START PHASE 14. DO NOT TOUCH TEST. WAIT FOR SUPERVISOR REVIEW.
