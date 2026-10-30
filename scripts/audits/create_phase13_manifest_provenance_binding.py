"""Create the Phase-13 Part-1B manifest-provenance-binding amendment.

NON_SCIENTIFIC_PROVENANCE_BINDING.

This script writes an *additive* amendment that supersedes the unresolvable
``image_sha256``-derived contract (``train_table_sha256`` / ``val_table_sha256``)
with explicit provenance/membership-binding fields whose names state exactly
what they mean.

It performs NO scientific work:
  * 0 training, 0 optimizer steps, 0 forward passes
  * 0 model construction, 0 CUDA
  * 0 proposals, 0 inference
  * 0 TEST reads

It MAY read the physical manifest CSVs and sample-table CSVs, because the
amendment itself must record the physical SHAs it binds.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

AUDIT_DIR = ROOT / "reports" / "audits"
JSON_PATH = AUDIT_DIR / "phase13_clean_v3_localizer_manifest_provenance_binding.json"
MD_PATH = AUDIT_DIR / "phase13_clean_v3_localizer_manifest_provenance_binding.md"

MANIFEST_VERSION = "phase4_v3"

# The physical sample tables the clean-v3 runner uses for FULL_FIELD metadata
# (patient_id / image_path / mask_path / view_type) before the phase4_v3 join.
TRAIN_SAMPLE_TABLE = ROOT / "reports" / "tables" / "kub_train_samples_sized.csv"
VAL_SAMPLE_TABLE = ROOT / "reports" / "tables" / "kub_val_samples_sized.csv"

NEW_FIELDS = [
    "train_manifest_file_sha256",
    "val_manifest_file_sha256",
    "train_sample_table_file_sha256",
    "val_sample_table_file_sha256",
    "train_filtered_sample_ids_sha256",
    "val_filtered_sample_ids_sha256",
    "train_filtered_sample_count",
    "val_filtered_sample_count",
]


def sha256_file(path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(8192):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    from src.utils.manifest_guard import get_manifest_path

    train_manifest = Path(get_manifest_path(MANIFEST_VERSION, "train"))
    val_manifest = Path(get_manifest_path(MANIFEST_VERSION, "val"))

    payload = {
        "artifact": "PHASE13_CLEAN_V3_LOCALIZER_MANIFEST_PROVENANCE_BINDING",
        "document_type": "NON_SCIENTIFIC_PROVENANCE_BINDING_AMENDMENT",
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "phase": 13,
        "part": "1B",
        "base_protocol": "R2 + R2A_LOSS_BINDING",
        "amendment_type": "NON_SCIENTIFIC_PROVENANCE_BINDING",
        "reason": "NO_AUTHORITATIVE_IMAGE_SHA256_COLUMN_EXISTS",
        "old_contract": (
            "image_sha256-derived train_table_sha256 / val_table_sha256"
        ),
        "old_contract_status": "SUPERSEDED_UNRESOLVABLE_FIELD_SEMANTICS",
        "new_fields": NEW_FIELDS,
        "scientific_parameters_changed": 0,
        "population_changed": False,
        "manifest_changed": False,
        "training_data_changed": False,
        "test_reads": 0,
        "status": "PROVENANCE_BINDING_APPROVED_FOR_PART1B",
        "image_sha256_fabricated": False,
        "image_content_hash_claim_made": False,
        "field_semantics": {
            "train_manifest_file_sha256": "SHA-256 of the physical active phase4_v3 TRAIN manifest file bytes",
            "val_manifest_file_sha256": "SHA-256 of the physical active phase4_v3 VAL manifest file bytes",
            "train_sample_table_file_sha256": "SHA-256 of the physical source sample-table file used to obtain KUB FULL_FIELD metadata before the phase4_v3 join",
            "val_sample_table_file_sha256": "Same semantics for VAL",
            "train_filtered_sample_ids_sha256": "deterministic SHA-256 over the FINAL clean-v3 TRAIN FULL_FIELD sample-id membership after the phase4_v3 join/filter",
            "val_filtered_sample_ids_sha256": "Same semantics for VAL",
            "train_filtered_sample_count": "final clean-v3 TRAIN FULL_FIELD case count (expected 770)",
            "val_filtered_sample_count": "final clean-v3 VAL FULL_FIELD case count (expected 103)",
        },
        "binding_class": "PROVENANCE_MEMBERSHIP_BINDING_NOT_IMAGE_CONTENT_HASH",
        "physical_sources": {
            "train_manifest": str(train_manifest),
            "train_manifest_file_sha256": sha256_file(train_manifest),
            "val_manifest": str(val_manifest),
            "val_manifest_file_sha256": sha256_file(val_manifest),
            "train_sample_table": str(TRAIN_SAMPLE_TABLE),
            "train_sample_table_file_sha256": sha256_file(TRAIN_SAMPLE_TABLE),
            "val_sample_table": str(VAL_SAMPLE_TABLE),
            "val_sample_table_file_sha256": sha256_file(VAL_SAMPLE_TABLE),
        },
        "membership_digest_contract": {
            "steps": [
                "take final post-join FULL_FIELD sample_id values",
                "cast to canonical string",
                "require uniqueness",
                "sort lexicographically",
                'join exactly with "\\n"',
                "UTF-8 encode",
                "SHA-256",
            ],
            "order_independent": True,
            "excludes": [
                "metrics",
                "model predictions",
                "GT contents",
                "image pixels",
                "mask pixels",
            ],
        },
        "governance": {
            "training": 0,
            "optimizer_creation": 0,
            "forward_passes": 0,
            "epochs": 0,
            "proposals_generated": 0,
            "inference": 0,
            "cuda": False,
            "model_constructions": 0,
            "test_content_reads": 0,
            "historical_artifacts_modified": False,
        },
    }

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md = f"""# PHASE-13 PART-1B — MANIFEST PROVENANCE BINDING AMENDMENT

- **artifact**: `{payload['artifact']}`
- **document_type**: `{payload['document_type']}`
- **base_protocol**: `{payload['base_protocol']}`
- **amendment_type**: `{payload['amendment_type']}`
- **reason**: `{payload['reason']}`
- **status**: `{payload['status']}`
- **created_utc**: {payload['created_utc']}

## Superseded contract

| field | value |
|---|---|
| old_contract | `{payload['old_contract']}` |
| old_contract_status | `{payload['old_contract_status']}` |

The previous Part-1B attempt stopped before epoch 1 with:

```
ValueError: manifest hash 'train_table_sha256' resolved empty; refusing empty hashes
```

because `_shas_of(frame, "image_sha256")` was asked to digest a per-sample
column that **does not exist in any table in this repository**.

## Replacement fields (§2)

| field | meaning |
|---|---|
""" + "\n".join(
        f"| `{name}` | {payload['field_semantics'][name]} |" for name in NEW_FIELDS
    ) + f"""

These are **{payload['binding_class']}**.

## Physical sources

| source | path | SHA-256 |
|---|---|---|
| TRAIN manifest | `{payload['physical_sources']['train_manifest']}` | `{payload['physical_sources']['train_manifest_file_sha256']}` |
| VAL manifest | `{payload['physical_sources']['val_manifest']}` | `{payload['physical_sources']['val_manifest_file_sha256']}` |
| TRAIN sample table | `{payload['physical_sources']['train_sample_table']}` | `{payload['physical_sources']['train_sample_table_file_sha256']}` |
| VAL sample table | `{payload['physical_sources']['val_sample_table']}` | `{payload['physical_sources']['val_sample_table_file_sha256']}` |

## Filtered sample-id digest contract (§3)

""" + "\n".join(
        f"{i+1}. {step}" for i, step in enumerate(payload['membership_digest_contract']['steps'])
    ) + f"""

Order-independent: **{payload['membership_digest_contract']['order_independent']}**

Excludes: {", ".join(f"`{x}`" for x in payload['membership_digest_contract']['excludes'])}

## Non-scientific declaration

| check | value |
|---|---|
| scientific_parameters_changed | {payload['scientific_parameters_changed']} |
| population_changed | {payload['population_changed']} |
| manifest_changed | {payload['manifest_changed']} |
| training_data_changed | {payload['training_data_changed']} |
| image_sha256_fabricated | {payload['image_sha256_fabricated']} |
| image_content_hash_claim_made | {payload['image_content_hash_claim_made']} |
| test_reads | {payload['test_reads']} |

## Governance

| counter | value |
|---|---|
""" + "\n".join(
        f"| {k} | {v} |" for k, v in payload['governance'].items()
    ) + """
"""
    MD_PATH.write_text(md, encoding="utf-8")

    print("json:", sha256_file(JSON_PATH))
    print("md  :", sha256_file(MD_PATH))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
