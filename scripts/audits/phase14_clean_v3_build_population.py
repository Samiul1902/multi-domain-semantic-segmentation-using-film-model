"""Phase 14 clean-v3 — Prospective population freeze builder (ADDITIVE, governance-only).

Builds the EXECUTABLE clean-v3 diagnostic population tables from the frozen
phase4_v3 manifest intersected with the v2-derived sized tables, and binds them
by SHA-256 + ordered identifiers. The v2-era constants (106/156/73-29-36-18,
hard-tiny 16, global-empty 7) are recorded as PROVENANCE-ONLY, NOT executable.

No training, no inference, no TEST reads. Pure deterministic derivation.
"""
import hashlib
import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TABLES = PROJECT_ROOT / "reports" / "tables"
AUDITS = PROJECT_ROOT / "reports" / "audits"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    # ---- 1. Membership source: frozen phase4_v3 VAL KUB ----
    val_path = PROJECT_ROOT / "manifests" / "phase4_v3" / "val.csv"
    val_sha = sha256_file(val_path)
    val = pd.read_csv(val_path)
    kub_val_ids = set(val[val["dataset"] == "KUB"]["sample_id"])
    assert len(kub_val_ids) == 280, f"expected 280 KUB VAL in phase4_v3, got {len(kub_val_ids)}"

    # ---- 2. v2-sized tables -> clean_v3 executable intersect ----
    samp = pd.read_csv(TABLES / "kub_val_samples_sized.csv")
    samp_ff = samp[samp["view_type"] == "FULL_FIELD"].copy()
    samp_cv3 = samp_ff[samp_ff["sample_id"].isin(kub_val_ids)].reset_index(drop=True)

    comp = pd.read_csv(TABLES / "kub_val_components_sized.csv")
    comp_ff = comp[comp["view_type"] == "FULL_FIELD"].copy()
    comp_cv3 = comp_ff[comp_ff["sample_id"].isin(kub_val_ids)].reset_index(drop=True)

    size_counts = comp_cv3["size_stratum"].value_counts().to_dict()
    for k in ("TINY", "SMALL", "MEDIUM", "LARGE"):
        size_counts.setdefault(k, 0)

    n_samples = len(samp_cv3)
    n_components = len(comp_cv3)
    assert n_samples == 103, f"clean_v3 samples must be 103, got {n_samples}"
    assert n_components == 152, f"clean_v3 components must be 152, got {n_components}"
    assert size_counts["TINY"] == 72, size_counts
    assert size_counts["SMALL"] == 28, size_counts
    assert size_counts["MEDIUM"] == 36, size_counts
    assert size_counts["LARGE"] == 16, size_counts

    # ---- 3. Write executable clean_v3 sized tables ----
    samp_out = TABLES / "kub_val_samples_sized_clean_v3.csv"
    comp_out = TABLES / "kub_val_components_sized_clean_v3.csv"
    samp_cv3.to_csv(samp_out, index=False)
    comp_cv3.to_csv(comp_out, index=False)
    samp_sha = sha256_file(samp_out)
    comp_sha = sha256_file(comp_out)

    # ---- 4. Special sets (frozen replication artifacts) ----
    ht_path = TABLES / "phase13_clean_v3_hard_tiny_replication_set.csv"
    ge_path = TABLES / "phase13_clean_v3_global_empty_replication_set.csv"
    ht = pd.read_csv(ht_path)
    ge = pd.read_csv(ge_path)

    # hard-tiny: (sample_id, native_component_id); must all be in the executable population
    ht_pairs = list(zip(ht["sample_id"], ht["native_component_id"]))
    ht_in_pop = [(s, c) for (s, c) in ht_pairs if s in set(samp_cv3["sample_id"])]
    assert len(ht_in_pop) == len(ht_pairs), "hard-tiny contains sample outside clean_v3 pop"
    n_hard_tiny = len(ht_pairs)
    n_hard_tiny_imgs = ht["sample_id"].nunique()
    assert n_hard_tiny == 15, f"clean_v3 hard-tiny must be 15, got {n_hard_tiny}"
    assert n_hard_tiny_imgs == 13, f"clean_v3 hard-tiny unique images must be 13, got {n_hard_tiny_imgs}"

    # global-empty: sample_id set
    ge_ids = sorted(set(ge["sample_id"]))
    ge_in_pop = [s for s in ge_ids if s in set(samp_cv3["sample_id"])]
    assert len(ge_in_pop) == len(ge_ids), "global-empty contains sample outside clean_v3 pop"
    n_global_empty = len(ge_ids)
    assert n_global_empty == 5, f"clean_v3 global-empty must be 5, got {n_global_empty}"

    ht_sha = sha256_file(ht_path)
    ge_sha = sha256_file(ge_path)

    # ---- 5. Ordered identifiers (binding) ----
    sample_ids_sorted = sorted(samp_cv3["sample_id"].tolist())
    comp_ids_sorted = sorted(
        [(r["sample_id"], int(r["component_id"])) for _, r in comp_cv3.iterrows()]
    )
    ht_sorted = sorted(ht_pairs)
    ge_sorted = ge_ids  # already sorted

    dropped = sorted(set(samp_ff["sample_id"]) - kub_val_ids)

    freeze = {
        "artifact": "phase14_clean_v3_population_freeze",
        "status": "FROZEN_AWAITING_EXECUTION",
        "population_role": "EXECUTABLE_diagnostic_population",
        "view_type": "FULL_FIELD",
        "dataset": "KUB",
        "split": "VAL",
        "manifest_version": "phase4_v3",
        "membership_source": {
            "manifest": "manifests/phase4_v3/val.csv",
            "sha256": val_sha,
            "filter": "dataset == 'KUB' AND sample_id in phase4_v3 VAL KUB (FULL_FIELD view)",
        },
        "executable_counts": {
            "val_samples": n_samples,
            "authoritative_components": n_components,
            "size_strata": {
                "TINY": size_counts["TINY"],
                "SMALL": size_counts["SMALL"],
                "MEDIUM": size_counts["MEDIUM"],
                "LARGE": size_counts["LARGE"],
            },
            "hard_tiny_components": n_hard_tiny,
            "hard_tiny_unique_images": n_hard_tiny_imgs,
            "global_empty_images": n_global_empty,
        },
        "tables": {
            "val_samples_sized": {"path": str(samp_out), "sha256": samp_sha, "rows": n_samples},
            "val_components_sized": {"path": str(comp_out), "sha256": comp_sha, "rows": n_components},
            "hard_tiny_replication_set": {"path": str(ht_path), "sha256": ht_sha, "rows": n_hard_tiny},
            "global_empty_replication_set": {"path": str(ge_path), "sha256": ge_sha, "rows": n_global_empty},
        },
        "ordered_identifiers": {
            "sample_ids_sorted": sample_ids_sorted,
            "component_ids_sorted": comp_ids_sorted,
            "hard_tiny_pairs_sorted": ht_sorted,
            "global_empty_sample_ids_sorted": ge_sorted,
        },
        "v2_era_preserved_for_provenance_NOT_executable": {
            "val_samples": 106,
            "authoritative_components": 156,
            "size_strata": {"TINY": 73, "SMALL": 29, "MEDIUM": 36, "LARGE": 18},
            "hard_tiny_components": 16,
            "global_empty_images": 7,
            "note": (
                "v2-era constants. clean_v3 executable values differ because the clean_v3 GLOBAL "
                "UNet++ checkpoint and kub_size_clean_v3_v1 thresholds redefine the detection/sizing-"
                "based special sets; they are NOT a mere subset of the v2 sets (0 of the 16/7 v2 "
                "special items were among the 3 dropped FULL_FIELD images)."
            ),
        },
        "dropped_images_vs_v2": dropped,
        "governance_note": (
            "Executable population frozen by table SHA-256 and ordered identifiers. Post-freeze "
            "modification of any bound table invalidates this freeze and requires a new supervisor "
            "amendment. v2-era constants are preserved for provenance and MUST NOT be used as the "
            "executable population."
        ),
    }

    out = AUDITS / "phase14_clean_v3_population_freeze.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(freeze, f, indent=2)
    print(f"[build] Wrote {out}")
    print(f"[build] samples={n_samples} components={n_components} strata={size_counts}")
    print(f"[build] hard_tiny={n_hard_tiny} ({n_hard_tiny_imgs} imgs) global_empty={n_global_empty}")
    print(f"[build] table SHAs: samples={samp_sha[:16]} comp={comp_sha[:16]} ht={ht_sha[:16]} ge={ge_sha[:16]}")


if __name__ == "__main__":
    main()
