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
