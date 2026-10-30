"""Deterministic FOV-aware KUB object-size analysis utilities."""
from pathlib import Path
import numpy as np
import pandas as pd

VIEW_TYPES = ("FULL_FIELD", "ROI_CROP", "UNRESOLVED")
STRATA = ("TINY", "SMALL", "MEDIUM", "LARGE")
TAXONOMY_VERSION = "kub_size_v1"


def classify_view_type(image_path):
    """Classify from explicit directory semantics, never dimensions."""
    parts = {part.casefold() for part in Path(str(image_path)).parts}
    if "roi" in parts:
        return "ROI_CROP"
    if "images" in parts:
        return "FULL_FIELD"
    return "UNRESOLVED"


def add_view_types(samples):
    result = samples.copy()
    result["view_type"] = result["image_path"].map(classify_view_type)
    return result


def join_component_view_types(components, samples):
    mapping = samples[["sample_id", "view_type"]].drop_duplicates()
    result = components.drop(columns=["view_type"], errors="ignore").merge(
        mapping, on="sample_id", how="left", validate="many_to_one"
    )
    if result["view_type"].isna().any():
        raise ValueError("Components lack a sample-level FOV assignment")
    return result


def compute_size_thresholds(components):
    full_field = components[components["view_type"] == "FULL_FIELD"]
    values = full_field["component_ratio"].to_numpy(dtype=float)
    q25, q50, q75 = np.quantile(values, [0.25, 0.50, 0.75])
    validate_thresholds(q25, q50, q75, len(values))
    return {
        "Q25": float(q25), "Q50": float(q50), "Q75": float(q75),
        "full_field_component_count": int(len(values)),
    }


def validate_thresholds(q25, q50, q75, component_count):
    if component_count < 4:
        raise ValueError("Insufficient FULL_FIELD components")
    if not (np.isfinite([q25, q50, q75]).all() and q25 < q50 < q75):
        raise ValueError("Invalid or collapsed quartile thresholds")


def stratum_for_ratio(value, thresholds):
    if value <= thresholds["Q25"]:
        return "TINY"
    if value <= thresholds["Q50"]:
        return "SMALL"
    if value <= thresholds["Q75"]:
        return "MEDIUM"
    return "LARGE"


def assign_component_strata(components, thresholds):
    result = components.copy()
    reference = result["component_ratio"].map(
        lambda value: stratum_for_ratio(value, thresholds)
    )
    result["size_stratum"] = np.where(
        result["view_type"].eq("FULL_FIELD"),
        reference,
        "ROI_NOT_PRIMARY_BINNED",
    )
    result["fullfield_reference_stratum"] = reference
    result["threshold_version"] = TAXONOMY_VERSION
    result["threshold_source"] = "TRAIN_ONLY"
    return result


def assign_sample_strata(samples, sized_components, thresholds):
    result = samples.copy()
    grouped = sized_components.groupby("sample_id")
    records = []
    for _, row in result.iterrows():
        components = grouped.get_group(row["sample_id"])
        if row["view_type"] == "FULL_FIELD":
            values = set(components["size_stratum"])
            flags = {name: name in values for name in STRATA}
            dominant = stratum_for_ratio(row["largest_component_ratio"], thresholds)
        else:
            flags = {name: False for name in STRATA}
            dominant = "ROI_NOT_PRIMARY_BINNED"
        records.append({
            "sample_id": row["sample_id"],
            **{f"contains_{name.lower()}_object": flags[name] for name in STRATA},
            "dominant_object_stratum": dominant,
            "threshold_source": "TRAIN_ONLY",
        })
    return result.merge(pd.DataFrame(records), on="sample_id", validate="one_to_one")


def summarize_size_distribution(components):
    counts = components["size_stratum"].value_counts().reindex(STRATA, fill_value=0)
    return pd.DataFrame({
        "stratum": counts.index,
        "components": counts.values,
        "percent": counts.values / counts.sum() * 100,
    })




def load_phase7_artifacts(project_root):
    """Load finalized Phase-7 artifacts without regenerating manifests or taxonomy."""
    root = Path(project_root)
    tables = root / "reports" / "tables"
    audits = root / "reports" / "audits"
    artifacts = {
        "fov_samples": pd.read_csv(tables / "kub_fov_sample_summary_v2.csv"),
        "fov_components": pd.read_csv(tables / "kub_fov_component_summary_v2.csv"),
        "fov_sample_category": pd.read_csv(tables / "kub_fov_category_sample_summary_v2.csv"),
        "fov_component_category": pd.read_csv(tables / "kub_fov_category_component_summary_v2.csv"),
        "fov_characteristics": pd.read_csv(tables / "kub_fov_characteristics_v2.csv"),
        "thresholds": pd.read_csv(tables / "kub_size_thresholds_v2.csv"),
        "category_size": pd.read_csv(tables / "kub_size_distribution_by_category_v2.csv"),
        "train_val_size": pd.read_csv(tables / "kub_size_distribution_train_val_v2.csv"),
        "patient_summary": pd.read_csv(tables / "kub_patient_size_summary_v3.csv"),
        "patients_per_stratum": pd.read_csv(tables / "kub_patients_per_stratum_v3.csv"),
        "multicomponent": pd.read_csv(tables / "kub_multicomponent_size_summary_v2.csv"),
        "provenance": pd.Series(json_load(audits / "kub_object_size_provenance.json")),
    }
    return artifacts


def json_load(path):
    import json
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_phase7_artifacts(artifacts):
    """Validate finalized sample/component units and frozen taxonomy invariants."""
    fov_samples = artifacts["fov_samples"]
    fov_components = artifacts["fov_components"]
    category_size = artifacts["category_size"]
    train_val = artifacts["train_val_size"]
    provenance = artifacts["provenance"]
    assert int(fov_samples.query("split == 'TRAIN'")["samples"].sum()) == 1979
    assert int(fov_samples.query("split == 'VAL'")["samples"].sum()) == 283
    assert int(fov_components.query("split == 'TRAIN'")["components"].sum()) == 2376
    assert int(category_size["TOTAL"].sum()) == 1162
    assert int(train_val.query("split == 'TRAIN'")["components"].sum()) == 1162
    assert int(train_val.query("split == 'VAL'")["components"].sum()) == 156
    assert int(provenance["test_mask_reads"]) == 0
    return True


def compute_patient_stratum_summary(sized_components):
    """Summarize distinct FULL_FIELD component strata per patient."""
    full_field = sized_components[sized_components["view_type"] == "FULL_FIELD"]
    exposure = full_field[["patient_id", "size_stratum"]].drop_duplicates()
    distinct = exposure.groupby("patient_id")["size_stratum"].nunique()
    distribution = distinct.value_counts().reindex([1, 2, 3, 4], fill_value=0)
    summary = pd.DataFrame({
        "metric": ["full_field_patients", "exactly_1_stratum", "exactly_2_strata",
                   "exactly_3_strata", "all_4_strata", "at_least_2_strata"],
        "value": [len(distinct), distribution[1], distribution[2], distribution[3],
                  distribution[4], int(distinct.ge(2).sum())],
    })
    per_stratum = pd.DataFrame({
        "stratum": list(STRATA),
        "patients": [exposure.loc[exposure["size_stratum"].eq(name), "patient_id"].nunique()
                     for name in STRATA],
    })
    return summary, per_stratum


# ===========================================================================
# VERSIONED TAXONOMY REGISTRY (Phase 07 Part 1B)
# ---------------------------------------------------------------------------
# kub_size_v1            : historical, FROZEN, IMMUTABLE. Unchanged above.
# kub_size_clean_v3_v1   : clean-v3, derived from phase4_v3 TRAIN FULL_FIELD.
#
# The historical taxonomy behaviour above is preserved exactly. The clean-v3
# taxonomy is a SEPARATE, explicitly versioned entry. There is no silent
# semantic replacement: callers must name the taxonomy they want.
# ===========================================================================

CLEAN_V3_TAXONOMY_ID = "kub_size_clean_v3_v1"
HISTORICAL_TAXONOMY_ID = TAXONOMY_VERSION          # "kub_size_v1"
ROI_NOT_PRIMARY_BINNED = "ROI_NOT_PRIMARY_BINNED"

# Historical kub_size_v1 thresholds — FROZEN, never recomputed, never edited.
KUB_SIZE_V1_THRESHOLDS = {
    "Q25": 0.0001499766777599,
    "Q50": 0.00033976472454305,
    "Q75": 0.0008266496069636999,
}

# Clean-v3 thresholds are populated by load_clean_v3_taxonomy() from the frozen
# artifact written by Phase 07 Part 1B. They are NOT hardcoded here.
_CLEAN_V3_THRESHOLDS_CACHE = None
CLEAN_V3_THRESHOLD_ARTIFACT = (
    Path(r"D:\Softfors\jup") / "reports" / "audits" / "kub_size_clean_v3_v1_thresholds.json"
)


def load_clean_v3_taxonomy(path=None):
    """Load the frozen kub_size_clean_v3_v1 thresholds from the freeze artifact."""
    global _CLEAN_V3_THRESHOLDS_CACHE
    if _CLEAN_V3_THRESHOLDS_CACHE is not None and path is None:
        return _CLEAN_V3_THRESHOLDS_CACHE
    p = Path(path) if path is not None else CLEAN_V3_THRESHOLD_ARTIFACT
    if not p.exists():
        raise FileNotFoundError(
            f"Frozen clean-v3 taxonomy artifact not found: {p}. "
            "Run Phase 07 Part 1B derivation before using kub_size_clean_v3_v1."
        )
    import json
    payload = json.loads(Path(p).read_text(encoding="utf-8"))
    if payload.get("status") != "FROZEN":
        raise ValueError("clean-v3 taxonomy artifact is not marked FROZEN")
    thresholds = {
        "Q25": float(payload["Q25"]),
        "Q50": float(payload["Q50"]),
        "Q75": float(payload["Q75"]),
    }
    if not (thresholds["Q25"] < thresholds["Q50"] < thresholds["Q75"]):
        raise ValueError("Invalid or collapsed clean-v3 quartile thresholds")
    if path is None:
        _CLEAN_V3_THRESHOLDS_CACHE = thresholds
    return thresholds


def get_kub_size_taxonomy(taxonomy_id):
    """
    Return the threshold dict for an explicit taxonomy id.

    Raises ValueError on an unknown id. There is no default: the caller must
    state which taxonomy it means, so historical and clean results can never be
    silently conflated.
    """
    if taxonomy_id == HISTORICAL_TAXONOMY_ID:
        return dict(KUB_SIZE_V1_THRESHOLDS)
    if taxonomy_id == CLEAN_V3_TAXONOMY_ID:
        return dict(load_clean_v3_taxonomy())
    raise ValueError(
        f"Unknown taxonomy_id '{taxonomy_id}'. "
        f"Valid: ['{HISTORICAL_TAXONOMY_ID}', '{CLEAN_V3_TAXONOMY_ID}']"
    )


def classify_component_ratio(value, thresholds):
    """
    Classify a component_ratio using the frozen boundary semantics.

    TINY   : x <= Q25
    SMALL  : Q25 < x <= Q50
    MEDIUM : Q50 < x <= Q75
    LARGE  : x > Q75

    The value is NOT rounded before classification. Boundary values fall into
    the LOWER bin.
    """
    if value <= thresholds["Q25"]:
        return "TINY"
    if value <= thresholds["Q50"]:
        return "SMALL"
    if value <= thresholds["Q75"]:
        return "MEDIUM"
    return "LARGE"


def assign_versioned_strata(components, taxonomy_id):
    """
    Assign size strata to components under an explicit taxonomy id.

    Only FULL_FIELD components are primary-binned; ROI components receive
    ROI_NOT_PRIMARY_BINNED. Adds taxonomy provenance columns.
    """
    thresholds = get_kub_size_taxonomy(taxonomy_id)
    result = components.copy()
    reference = result["component_ratio"].map(
        lambda v: classify_component_ratio(v, thresholds))
    result["size_stratum"] = np.where(
        result["view_type"].eq("FULL_FIELD"),
        reference,
        ROI_NOT_PRIMARY_BINNED,
    )
    result["fullfield_reference_stratum"] = reference
    result["taxonomy_id"] = taxonomy_id
    result["threshold_source"] = (
        "TRAIN_ONLY" if taxonomy_id == HISTORICAL_TAXONOMY_ID else "CLEAN_V3_TRAIN_ONLY")
    return result


def derive_quartiles(values):
    """
    The historical quantile algorithm, applied verbatim.

    Implementation : numpy.quantile
    Method         : default 'linear' interpolation
    Sort / NaN     : numpy handles ordering internally; no NaN expected
    Precision      : float64
    """
    arr = np.asarray(values, dtype=float)
    if not np.isfinite(arr).all():
        raise ValueError("Non-finite value encountered in quantile input")
    q25, q50, q75 = np.quantile(arr, [0.25, 0.50, 0.75])
    if not (q25 < q50 < q75):
        raise ValueError("Invalid or collapsed quartile thresholds")
    return float(q25), float(q50), float(q75)
