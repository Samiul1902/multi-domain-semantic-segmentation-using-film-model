# PHASE-13 PART-1B — MANIFEST PROVENANCE BINDING AMENDMENT

- **artifact**: `PHASE13_CLEAN_V3_LOCALIZER_MANIFEST_PROVENANCE_BINDING`
- **document_type**: `NON_SCIENTIFIC_PROVENANCE_BINDING_AMENDMENT`
- **base_protocol**: `R2 + R2A_LOSS_BINDING`
- **amendment_type**: `NON_SCIENTIFIC_PROVENANCE_BINDING`
- **reason**: `NO_AUTHORITATIVE_IMAGE_SHA256_COLUMN_EXISTS`
- **status**: `PROVENANCE_BINDING_APPROVED_FOR_PART1B`
- **created_utc**: 2026-09-21T05:39:00.782974+00:00

## Superseded contract

| field | value |
|---|---|
| old_contract | `image_sha256-derived train_table_sha256 / val_table_sha256` |
| old_contract_status | `SUPERSEDED_UNRESOLVABLE_FIELD_SEMANTICS` |

The previous Part-1B attempt stopped before epoch 1 with:

```
ValueError: manifest hash 'train_table_sha256' resolved empty; refusing empty hashes
```

because `_shas_of(frame, "image_sha256")` was asked to digest a per-sample
column that **does not exist in any table in this repository**.

## Replacement fields (§2)

| field | meaning |
|---|---|
| `train_manifest_file_sha256` | SHA-256 of the physical active phase4_v3 TRAIN manifest file bytes |
| `val_manifest_file_sha256` | SHA-256 of the physical active phase4_v3 VAL manifest file bytes |
| `train_sample_table_file_sha256` | SHA-256 of the physical source sample-table file used to obtain KUB FULL_FIELD metadata before the phase4_v3 join |
| `val_sample_table_file_sha256` | Same semantics for VAL |
| `train_filtered_sample_ids_sha256` | deterministic SHA-256 over the FINAL clean-v3 TRAIN FULL_FIELD sample-id membership after the phase4_v3 join/filter |
| `val_filtered_sample_ids_sha256` | Same semantics for VAL |
| `train_filtered_sample_count` | final clean-v3 TRAIN FULL_FIELD case count (expected 770) |
| `val_filtered_sample_count` | final clean-v3 VAL FULL_FIELD case count (expected 103) |

These are **PROVENANCE_MEMBERSHIP_BINDING_NOT_IMAGE_CONTENT_HASH**.

## Physical sources

| source | path | SHA-256 |
|---|---|---|
| TRAIN manifest | `D:\Softfors\jup\manifests\phase4_v3\train.csv` | `28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6` |
| VAL manifest | `D:\Softfors\jup\manifests\phase4_v3\val.csv` | `082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315` |
| TRAIN sample table | `D:\Softfors\jup\reports\tables\kub_train_samples_sized.csv` | `3901e9825c8bad89da8291c0b504197c600d6ecca1d39ddba2b2050d650962cc` |
| VAL sample table | `D:\Softfors\jup\reports\tables\kub_val_samples_sized.csv` | `84ecd5646751363844ab520d8576424ad13870befd46309951e046c17f80d425` |

## Filtered sample-id digest contract (§3)

1. take final post-join FULL_FIELD sample_id values
2. cast to canonical string
3. require uniqueness
4. sort lexicographically
5. join exactly with "\n"
6. UTF-8 encode
7. SHA-256

Order-independent: **True**

Excludes: `metrics`, `model predictions`, `GT contents`, `image pixels`, `mask pixels`

## Non-scientific declaration

| check | value |
|---|---|
| scientific_parameters_changed | 0 |
| population_changed | False |
| manifest_changed | False |
| training_data_changed | False |
| image_sha256_fabricated | False |
| image_content_hash_claim_made | False |
| test_reads | 0 |

## Governance

| counter | value |
|---|---|
| training | 0 |
| optimizer_creation | 0 |
| forward_passes | 0 |
| epochs | 0 |
| proposals_generated | 0 |
| inference | 0 |
| cuda | False |
| model_constructions | 0 |
| test_content_reads | 0 |
| historical_artifacts_modified | False |
