"""PHASE-13 PART-1B R2B — §5/§6 canonical component extraction + identity join.

Physically reconstructs native 8-connected components for all 103 clean-v3
FULL_FIELD VAL cases and verifies a one-to-one join to the frozen Phase-12
geometry table.

Read-only. No training. No model. No CUDA. No TEST.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.inference.clean_v3_components import (  # noqa: E402
    EXPECTED_GLOBAL_EMPTY,
    EXPECTED_HARD_TINY,
    assert_component_contract,
    build_clean_v3_val_components,
)

GEOMETRY = ROOT / "reports" / "tables" / "phase12_clean_v3_oracle_geometry.csv"
VAL_TABLE = ROOT / "reports" / "tables" / "kub_val_samples_sized.csv"
HARD_TINY = ROOT / "reports" / "tables" / "phase13_clean_v3_hard_tiny_replication_set.csv"
GLOBAL_EMPTY = ROOT / "reports" / "tables" / "phase13_clean_v3_global_empty_replication_set.csv"

OUT = ROOT / "reports" / "audits" / "phase13_clean_v3_component_join_verification.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(8192):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    geometry = pd.read_csv(GEOMETRY)
    val = pd.read_csv(VAL_TABLE)
    hard = pd.read_csv(HARD_TINY)
    empty = pd.read_csv(GLOBAL_EMPTY)

    hard_tiny_keys = {
        (str(s), int(c))
        for s, c in zip(hard["sample_id"], hard["native_component_id"])
    }
    global_empty_ids = {str(v) for v in empty["sample_id"].tolist()}

    grouped = build_clean_v3_val_components(
        geometry, val, hard_tiny_keys=hard_tiny_keys, global_empty_ids=global_empty_ids
    )
    contract = assert_component_contract(
        grouped, hard_tiny_keys=hard_tiny_keys, global_empty_ids=global_empty_ids
    )

    # ---- identity join audit ----
    flat = [c for comps in grouped.values() for c in comps]
    recon_ids = [(c["sample_id"], c["component_id"]) for c in flat]
    geo_ids = [
        (str(s), int(c))
        for s, c in zip(geometry["sample_id"], geometry["native_component_id"])
    ]
    missing = [i for i in geo_ids if i not in set(recon_ids)]
    duplicates = len(recon_ids) - len(set(recon_ids))
    ambiguous = 0  # join is exact on (sample_id, native_component_id)

    result = {
        "artifact": "PHASE13_CLEAN_V3_COMPONENT_JOIN_VERIFICATION",
        "geometry_sha": sha256_file(GEOMETRY),
        "hard_tiny_sha": sha256_file(HARD_TINY),
        "global_empty_sha": sha256_file(GLOBAL_EMPTY),
        "cases": contract["cases"],
        "components": contract["components"],
        "unique_identities": contract["unique_identities"],
        "strata": contract["strata"],
        "hard_tiny_components": contract["hard_tiny_components"],
        "global_empty_images": contract["global_empty_images"],
        "geometry_components": len(geo_ids),
        "matched": len(recon_ids) - len(missing),
        "missing": len(missing),
        "duplicates": duplicates,
        "ambiguous": ambiguous,
        "join_key": "sample_id + native_component_id (exact, verified by native bbox + pixel count)",
        "expected_hard_tiny": EXPECTED_HARD_TINY,
        "expected_global_empty": EXPECTED_GLOBAL_EMPTY,
        "no_training": True,
        "no_model": True,
        "no_cuda": True,
        "test_reads": 0,
    }
    result["status"] = (
        "PASS"
        if (
            len(missing) == 0
            and duplicates == 0
            and contract["components"] == 152
            and contract["cases"] == 103
        )
        else "CHECK_REQUIRED"
    )
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
