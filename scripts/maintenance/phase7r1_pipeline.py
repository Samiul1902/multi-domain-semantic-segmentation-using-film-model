"""Phase 7-R1 FOV/sample/component reconciliation. Never reads TEST masks."""
import hashlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from PIL import Image

from src.analysis.kub_object_size import (
    STRATA, add_view_types, assign_component_strata, assign_sample_strata,
    compute_size_thresholds, join_component_view_types, summarize_size_distribution,
)
from src.utils.manifest_guard import verify_manifests

ROOT = Path(r"D:\Softfors\jup")
TABLES = ROOT / "reports" / "tables"
AUDITS = ROOT / "reports" / "audits"
FIGURES = ROOT / "reports" / "figures" / "kub_object_size"
QUALITATIVE = ROOT / "reports" / "qualitative" / "kub_size_taxonomy"
MANIFESTS = ROOT / "manifests"
for directory in (TABLES, AUDITS, FIGURES, QUALITATIVE):
    directory.mkdir(parents=True, exist_ok=True)

verify_manifests()
train_samples = add_view_types(pd.read_csv(TABLES / "kub_train_sample_characteristics_v2.csv"))
val_samples = add_view_types(pd.read_csv(TABLES / "kub_val_sample_characteristics_v2.csv"))
train_components = join_component_view_types(
    pd.read_csv(TABLES / "kub_train_components_v2.csv"), train_samples
)
assert len(train_samples) == 1979 and len(val_samples) == 283
assert len(train_components) == 2376
assert not train_samples["view_type"].eq("UNRESOLVED").any()

# Reconstruct VAL components using TRAIN/VAL only and the Phase-6 implementation.
from src.analysis.kub_characterization import analyze_kub_mask_v2
val_component_rows, val_enriched_rows = [], []
for row in val_samples.to_dict("records"):
    analysis = analyze_kub_mask_v2(row["mask_path"], connectivity=8)
    components = analysis.pop("components")
    areas = [component["component_pixels"] for component in components]
    row.update(analysis)
    row["largest_component_pixels"] = max(areas)
    row["largest_component_ratio"] = max(areas) / (row["width"] * row["height"])
    row["smallest_component_pixels"] = min(areas)
    row["smallest_component_ratio"] = min(areas) / (row["width"] * row["height"])
    val_enriched_rows.append(row)
    for component in components:
        val_component_rows.append({
            "sample_id": row["sample_id"], "patient_id": row["patient_id"],
            "category": row["category"], **component,
        })
val_samples = pd.DataFrame(val_enriched_rows)
val_components = join_component_view_types(pd.DataFrame(val_component_rows), val_samples)
assert len(val_components) == int(val_samples["component_count"].sum()) == 333

VIEW_TYPES = ["FULL_FIELD", "ROI_CROP", "UNRESOLVED"]
CATEGORIES = ["Kidney_Stone", "Bladder_Stone", "Ureteric_Stone"]

def summary_stats(series):
    return {
        "min": series.min(), "q1": series.quantile(.25), "median": series.median(),
        "mean": series.mean(), "q3": series.quantile(.75), "max": series.max(),
    }

def sample_fov_summary(samples, split):
    rows = []
    for view_type in VIEW_TYPES:
        group = samples[samples["view_type"] == view_type]
        rows.append({"split": split, "view_type": view_type, "samples": len(group),
                     "patients": group["patient_id"].nunique(),
                     "percent": 100 * len(group) / len(samples)})
    return pd.DataFrame(rows)

def component_fov_summary(components, split):
    rows = []
    for view_type in VIEW_TYPES:
        group = components[components["view_type"] == view_type]
        rows.append({"split": split, "view_type": view_type, "components": len(group),
                     "samples": group["sample_id"].nunique(),
                     "median_component_ratio": group["component_ratio"].median() if len(group) else np.nan})
    return pd.DataFrame(rows)

def category_table(frame, unit):
    table = pd.crosstab(frame["category"], frame["view_type"]).reindex(
        index=CATEGORIES, columns=VIEW_TYPES, fill_value=0
    ).reset_index()
    table.columns = ["category", "full_field", "roi_crop", "unresolved"]
    table[f"total_{unit}"] = table[["full_field", "roi_crop", "unresolved"]].sum(axis=1)
    return table

sample_summary = pd.concat([sample_fov_summary(train_samples, "TRAIN"),
                            sample_fov_summary(val_samples, "VAL")], ignore_index=True)
component_summary = pd.concat([component_fov_summary(train_components, "TRAIN"),
                               component_fov_summary(val_components, "VAL")], ignore_index=True)
train_sample_category = category_table(train_samples, "samples")
train_component_category = category_table(train_components, "components")

sample_summary.to_csv(TABLES / "kub_fov_sample_summary_v2.csv", index=False)
component_summary.to_csv(TABLES / "kub_fov_component_summary_v2.csv", index=False)
train_sample_category.to_csv(TABLES / "kub_fov_category_sample_summary_v2.csv", index=False)
train_component_category.to_csv(TABLES / "kub_fov_category_component_summary_v2.csv", index=False)
assert sample_summary.query("split == 'TRAIN'")["samples"].sum() == 1979
assert component_summary.query("split == 'TRAIN'")["components"].sum() == 2376


# FOV characteristics, patient overlap, and exact threshold verification.
fov_characteristic_rows = []
for view_type in ("FULL_FIELD", "ROI_CROP"):
    samples = train_samples[train_samples["view_type"] == view_type].copy()
    samples["image_area"] = samples["width"] * samples["height"]
    components = train_components[train_components["view_type"] == view_type]
    for metric in ("width", "height", "image_area", "foreground_pixels", "foreground_ratio"):
        fov_characteristic_rows.append({"view_type": view_type, "unit": "sample", "metric": metric,
                                        **summary_stats(samples[metric])})
    fov_characteristic_rows.append({"view_type": view_type, "unit": "component",
                                    "metric": "component_ratio", **summary_stats(components["component_ratio"])})
fov_characteristics = pd.DataFrame(fov_characteristic_rows)
fov_characteristics.to_csv(TABLES / "kub_fov_characteristics_v2.csv", index=False)

ff_samples = train_samples.query("view_type == 'FULL_FIELD'")
roi_samples = train_samples.query("view_type == 'ROI_CROP'")
ff_components = train_components.query("view_type == 'FULL_FIELD'")
roi_components = train_components.query("view_type == 'ROI_CROP'")
assert len(ff_samples) == 771 and len(roi_samples) == 1208
assert len(ff_components) == 1162 and len(roi_components) == 1214
assert len(ff_components) >= len(ff_samples)
component_distribution = ff_samples["component_count"].value_counts().sort_index()
assert int(component_distribution.sum()) == 771
fullfield_multicomponent = int((ff_samples["component_count"] > 1).sum())
assert fullfield_multicomponent == 206

ff_patients = set(ff_samples["patient_id"])
roi_patients = set(roi_samples["patient_id"])
patient_fov = pd.DataFrame([
    {"group": "FULL_FIELD", "patients": len(ff_patients)},
    {"group": "ROI_CROP", "patients": len(roi_patients)},
    {"group": "BOTH", "patients": len(ff_patients & roi_patients)},
    {"group": "UNION", "patients": len(ff_patients | roi_patients)},
])
patient_fov.to_csv(TABLES / "kub_fov_patient_summary_v2.csv", index=False)
assert len(ff_patients | roi_patients) == 318

thresholds = compute_size_thresholds(train_components)
expected_thresholds = {"Q25": 0.0001499766777599, "Q50": 0.00033976472454305,
                       "Q75": 0.0008266496069636999}
for name, expected in expected_thresholds.items():
    assert abs(thresholds[name] - expected) < 1e-15
train_sized_components = assign_component_strata(train_components, thresholds)
val_sized_components = assign_component_strata(val_components, thresholds)
train_sized_samples = assign_sample_strata(train_samples, train_sized_components, thresholds)
val_sized_samples = assign_sample_strata(val_samples, val_sized_components, thresholds)

train_sized_components.to_csv(TABLES / "kub_train_components_sized.csv", index=False)
train_sized_samples.to_csv(TABLES / "kub_train_samples_sized.csv", index=False)
val_sized_components.to_csv(TABLES / "kub_val_components_sized.csv", index=False)
val_sized_samples.to_csv(TABLES / "kub_val_samples_sized.csv", index=False)

train_size = summarize_size_distribution(train_sized_components.query("view_type == 'FULL_FIELD'"))
val_size = summarize_size_distribution(val_sized_components.query("view_type == 'FULL_FIELD'"))
train_size["split"] = "TRAIN"
val_size["split"] = "VAL"
size_train_val = pd.concat([train_size, val_size], ignore_index=True)
size_train_val.to_csv(TABLES / "kub_size_distribution_train_val_v2.csv", index=False)
assert train_size["components"].sum() == 1162
assert val_size["components"].sum() == 156

category_size = pd.crosstab(
    train_sized_components.query("view_type == 'FULL_FIELD'")["category"],
    train_sized_components.query("view_type == 'FULL_FIELD'")["size_stratum"],
).reindex(index=CATEGORIES, columns=STRATA, fill_value=0)
category_size["TOTAL"] = category_size.sum(axis=1)
category_size.reset_index().to_csv(TABLES / "kub_size_distribution_by_category_v2.csv", index=False)
assert category_size["TOTAL"].to_dict() == {
    "Kidney_Stone": 709, "Bladder_Stone": 344, "Ureteric_Stone": 109,
}


# Multi-component and patient-size summaries.
multicomponent_rows = []
for sample in ff_samples.query("component_count > 1").to_dict("records"):
    components = train_sized_components[train_sized_components["sample_id"] == sample["sample_id"]]
    strata = set(components["size_stratum"])
    ratios = components["component_ratio"]
    multicomponent_rows.append({
        "sample_id": sample["sample_id"], "patient_id": sample["patient_id"],
        "category": sample["category"], "component_count": sample["component_count"],
        "mixed_strata": len(strata) > 1,
        "tiny_plus_larger": "TINY" in strata and bool(strata - {"TINY"}),
        "smallest_largest_ratio": ratios.min() / ratios.max(),
    })
multicomponent = pd.DataFrame(multicomponent_rows)
multicomponent.to_csv(TABLES / "kub_multicomponent_size_summary_v2.csv", index=False)
assert len(multicomponent) == 206

# Patient stratum exposure is component-level; do not infer it from image dominant strata.
from src.analysis.kub_object_size import compute_patient_stratum_summary
patient_summary_v3, patients_per_stratum_v3 = compute_patient_stratum_summary(train_sized_components)
patient_summary_v3.to_csv(TABLES / "kub_patient_size_summary_v3.csv", index=False)
patients_per_stratum_v3.to_csv(TABLES / "kub_patients_per_stratum_v3.csv", index=False)

threshold_table = pd.DataFrame([
    {"boundary": "Q25", "value": thresholds["Q25"], "definition": "TINY: ratio <= Q25"},
    {"boundary": "Q50", "value": thresholds["Q50"], "definition": "SMALL: Q25 < ratio <= Q50"},
    {"boundary": "Q75", "value": thresholds["Q75"], "definition": "MEDIUM: Q50 < ratio <= Q75; LARGE: ratio > Q75"},
])
threshold_table.to_csv(TABLES / "kub_size_thresholds_v2.csv", index=False)

# Publication-ready Markdown and LaTeX tables.
def save_paper_table(frame, stem):
    headers = [str(column) for column in frame.columns]
    rows = [headers] + [[str(value) for value in row] for row in frame.itertuples(index=False, name=None)]
    markdown = ["| " + " | ".join(rows[0]) + " |",
                "| " + " | ".join(["---"] * len(headers)) + " |"]
    markdown.extend("| " + " | ".join(row) + " |" for row in rows[1:])
    (TABLES / f"{stem}.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    (TABLES / f"{stem}.tex").write_text(frame.to_latex(index=False), encoding="utf-8")

save_paper_table(sample_summary, "kub_fov_sample_summary_v2")
save_paper_table(component_summary, "kub_fov_component_summary_v2")
save_paper_table(train_sample_category, "kub_fov_category_sample_summary_v2")
save_paper_table(train_component_category, "kub_fov_category_component_summary_v2")
save_paper_table(threshold_table, "kub_size_thresholds_v2")
save_paper_table(category_size.reset_index(), "kub_size_distribution_by_category_v2")
save_paper_table(patient_summary_v3, "kub_patient_size_summary_v3")
save_paper_table(patients_per_stratum_v3, "kub_patients_per_stratum_v3")



# Figures: all annotations derive from corrected tables/dataframes.
sns.set_theme(style="whitegrid", context="paper")
PALETTE = {"FULL_FIELD": "#0072B2", "ROI_CROP": "#E69F00", "UNRESOLVED": "#999999"}
STRATUM_PALETTE = {"TINY": "#CC79A7", "SMALL": "#E69F00", "MEDIUM": "#56B4E9", "LARGE": "#009E73"}

def save_figure(fig, stem):
    for extension in ("png", "svg", "pdf"):
        fig.savefig(FIGURES / f"{stem}.{extension}", dpi=320, bbox_inches="tight")
    plt.close(fig)

fig, ax = plt.subplots(figsize=(7, 4.5))
plot_data = sample_summary.query("split == 'TRAIN' and samples > 0")
sns.barplot(plot_data, x="view_type", y="samples", hue="view_type", palette=PALETTE, legend=False, ax=ax)
for patch, value in zip(ax.patches, plot_data["samples"]):
    ax.annotate(str(int(value)), (patch.get_x()+patch.get_width()/2, patch.get_height()), ha="center", va="bottom")
ax.set(title="KUB TRAIN Samples by Field of View", xlabel="Field-of-view type", ylabel="Samples")
save_figure(fig, "kub_fov_composition_v2")

fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
dimension_data = train_samples.melt(id_vars="view_type", value_vars=["width", "height"],
                                    var_name="dimension", value_name="pixels")
sns.boxplot(dimension_data, x="view_type", y="pixels", hue="dimension", ax=axes[0])
axes[0].set_yscale("log"); axes[0].set(title="Image Dimensions by Field of View", xlabel="FOV", ylabel="Pixels (log scale)")
area_data = train_samples.assign(image_area=train_samples.width*train_samples.height)
sns.boxplot(area_data, x="view_type", y="image_area", hue="view_type", palette=PALETTE, legend=False, ax=axes[1])
axes[1].set_yscale("log"); axes[1].set(title="Image Area by Field of View", xlabel="FOV", ylabel="Pixels² (log scale)")
save_figure(fig, "kub_fov_dimension_distribution_v2")

fig, ax = plt.subplots(figsize=(8, 4.5))
log_ratio = np.log10(ff_components["component_ratio"].to_numpy())
ax.hist(log_ratio, bins=40, color="#0072B2", alpha=.8)
for name, color in zip(("Q25", "Q50", "Q75"), ("#CC79A7", "#E69F00", "#009E73")):
    value = thresholds[name]
    ax.axvline(np.log10(value), color=color, linestyle="--", label=f"{name}={value:.10f}")
ax.set(title=f"FULL_FIELD TRAIN Component Ratios (n={len(ff_components)})",
       xlabel="log10(component area / image area)", ylabel="Components")
ax.legend(); save_figure(fig, "kub_fullfield_object_size_thresholds_v2")

fig, ax = plt.subplots(figsize=(8, 4.5))
category_long = category_size[list(STRATA)].reset_index().melt(
    id_vars="category", var_name="stratum", value_name="components")
sns.barplot(category_long, x="category", y="components", hue="stratum", palette=STRATUM_PALETTE, ax=ax)
ax.set(title="FULL_FIELD TRAIN Object Size by Category", xlabel="Category", ylabel="Components")
save_figure(fig, "kub_object_size_by_category_v2")

fig, ax = plt.subplots(figsize=(8, 4.5))
sns.barplot(size_train_val, x="stratum", y="percent", hue="split", palette=["#0072B2", "#E69F00"], ax=ax)
ax.set(title="Frozen TRAIN Size Taxonomy Applied to Validation", xlabel="Dataset-relative stratum", ylabel="Components (%)")
save_figure(fig, "kub_object_size_train_val_v2")

fig, ax = plt.subplots(figsize=(8, 4.5))
ratio_data = train_components.query("view_type != 'UNRESOLVED'").copy()
ratio_data["log10_component_ratio"] = np.log10(ratio_data["component_ratio"])
sns.histplot(ratio_data, x="log10_component_ratio", hue="view_type", element="step", stat="density",
             common_norm=False, palette=PALETTE, ax=ax)
ax.set(title="Component Ratio by Field of View", xlabel="log10(component area / image area)", ylabel="Density")
save_figure(fig, "kub_roi_vs_fullfield_object_ratio_v2")

fig, ax = plt.subplots(figsize=(7, 4.5))
combination_counts = multicomponent["mixed_strata"].map({False:"Single stratum", True:"Mixed strata"}).value_counts().rename_axis("combination").reset_index(name="images")
sns.barplot(combination_counts, x="combination", y="images", hue="combination", palette=["#0072B2", "#D55E00"], legend=False, ax=ax)
ax.set(title=f"FULL_FIELD Multi-component Size Combinations (n={len(multicomponent)})", xlabel="Component-stratum pattern", ylabel="Images")
save_figure(fig, "kub_multicomponent_size_combinations_v2")


# Deterministic qualitative source selections and panels.
def overlay(image_path, mask_path):
    image = np.asarray(Image.open(image_path).convert("RGB")).copy()
    mask = np.asarray(Image.open(mask_path).convert("L")) > 0
    image[mask, 0] = np.maximum(image[mask, 0], 220)
    image[mask, 1:] = (image[mask, 1:] * .45).astype(np.uint8)
    return image, mask

fullfield_selection = []
for stratum in STRATA:
    group = train_sized_samples.query(
        "view_type == 'FULL_FIELD' and dominant_object_stratum == @stratum"
    ).sort_values(["largest_component_ratio", "sample_id"])
    median = group["largest_component_ratio"].median()
    selected = group.assign(distance=(group["largest_component_ratio"]-median).abs()).sort_values(
        ["distance", "sample_id"]
    ).head(2)
    fullfield_selection.append(selected)
fullfield_selection = pd.concat(fullfield_selection, ignore_index=True)
assert len(fullfield_selection) == 8 and fullfield_selection["view_type"].eq("FULL_FIELD").all()
fullfield_selection.to_csv(TABLES / "kub_size_strata_qualitative_selection_v2.csv", index=False)

fig, axes = plt.subplots(2, 4, figsize=(16, 8))
for ax, row in zip(axes.flat, fullfield_selection.to_dict("records")):
    image, mask = overlay(row["image_path"], row["mask_path"])
    ax.imshow(image); ax.contour(mask, levels=[.5], colors=["yellow"], linewidths=.8)
    ax.set_title(f"{row['dominant_object_stratum']} | {row['category']}\n{row['patient_id']} | ratio={row['largest_component_ratio']:.8f}", fontsize=8)
    ax.axis("off")
fig.suptitle("KUB TRAIN FULL_FIELD Dataset-relative Size Strata")
for extension in ("png", "svg", "pdf"):
    fig.savefig(QUALITATIVE / f"kub_size_strata_examples_v2.{extension}", dpi=320, bbox_inches="tight")
plt.close(fig)

roi_order = roi_samples.assign(distance=(roi_samples["foreground_ratio"]-roi_samples["foreground_ratio"].median()).abs()).sort_values(["distance", "sample_id"]).head(4)
assert len(roi_order) == 4 and roi_order["view_type"].eq("ROI_CROP").all()
roi_order.to_csv(TABLES / "kub_roi_qualitative_selection_v2.csv", index=False)
fig, axes = plt.subplots(1, 4, figsize=(14, 4))
for ax, row in zip(axes.flat, roi_order.to_dict("records")):
    image, mask = overlay(row["image_path"], row["mask_path"])
    ax.imshow(image); ax.contour(mask, levels=[.5], colors=["yellow"], linewidths=.8)
    ax.set_title(f"ROI_CROP | {row['category']}\n{row['patient_id']} | FG ratio={row['foreground_ratio']:.4f}", fontsize=8)
    ax.axis("off")
fig.suptitle("KUB TRAIN ROI Crops (Separate from Primary Taxonomy)")
for extension in ("png", "svg", "pdf"):
    fig.savefig(QUALITATIVE / f"kub_roi_examples_v2.{extension}", dpi=320, bbox_inches="tight")
plt.close(fig)

# Threshold and provenance artifacts.
def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        while block := stream.read(65536):
            digest.update(block)
    return digest.hexdigest()

manifest_metadata = json.loads((MANIFESTS / "manifest_metadata.json").read_text(encoding="utf-8"))
source_files = ["kub_view_type_inventory.csv", "kub_train_components_sized.csv",
                "kub_train_samples_sized.csv", "kub_val_components_sized.csv",
                "kub_val_samples_sized.csv"]
source_hashes = {name: sha256(TABLES / name) for name in source_files}
threshold_artifact = {
    "taxonomy_version": "kub_size_v1", "manifest_version": "phase4_v2",
    "source_split": "TRAIN", "source_view_type": "FULL_FIELD",
    "source_full_field_sample_count": 771, "source_full_field_component_count": 1162,
    "connectivity": 8, "size_measure": "component_ratio",
    "Q25": thresholds["Q25"], "Q50": thresholds["Q50"], "Q75": thresholds["Q75"],
    "intervals": {"TINY":"component_ratio <= Q25", "SMALL":"Q25 < component_ratio <= Q50",
                  "MEDIUM":"Q50 < component_ratio <= Q75", "LARGE":"component_ratio > Q75"},
    "thresholds_validated_unchanged": True, "test_mask_reads": 0,
    "clinical_interpretation": "NONE",
}
(AUDITS / "kub_object_size_thresholds.json").write_text(json.dumps(threshold_artifact, indent=2), encoding="utf-8")
threshold_hash = sha256(AUDITS / "kub_object_size_thresholds.json")


provenance = {
    "phase": "7-R1", "manifest_version": "phase4_v2",
    "manifest_hashes": manifest_metadata["hashes"],
    "train_samples": 1979, "val_samples": 283,
    "fov_sample_counts_train": {"FULL_FIELD":771,"ROI_CROP":1208,"UNRESOLVED":0},
    "fov_component_counts_train": {"FULL_FIELD":1162,"ROI_CROP":1214,"UNRESOLVED":0},
    "source_component_count": 1162, "thresholds": thresholds,
    "source_table_hashes": source_hashes,
    "threshold_json_sha256": threshold_hash,
    "notebook_path": "notebooks/05_kub_object_size_taxonomy.ipynb",
    "code_module": "src/analysis/kub_object_size.py",
    "test_mask_reads": 0, "external_data_accessed": False,
}
(AUDITS / "kub_object_size_provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")

reconciliation = {
    **provenance,
    "full_field_mean_components_per_image": len(ff_components)/len(ff_samples),
    "roi_mean_components_per_image": len(roi_components)/len(roi_samples),
    "full_field_component_count_distribution": {str(k):int(v) for k,v in component_distribution.items()},
    "full_field_multicomponent_images": fullfield_multicomponent,
    "patient_fov": {row["group"]:int(row["patients"]) for row in patient_fov.to_dict("records")},
    "val_full_field_samples": int(val_samples["view_type"].eq("FULL_FIELD").sum()),
    "val_full_field_components": int(val_components["view_type"].eq("FULL_FIELD").sum()),
    "val_size_counts": {row["stratum"]:int(row["components"]) for row in val_size.to_dict("records")},
    "multicomponent_mixed_strata": int(multicomponent["mixed_strata"].sum()),
    "multicomponent_tiny_plus_larger": int(multicomponent["tiny_plus_larger"].sum()),
    "taxonomy_validated_unchanged": True,
}
(AUDITS / "kub_fov_reconciliation.json").write_text(json.dumps(reconciliation, indent=2), encoding="utf-8")

methodology = f"""# KUB Object-Size Taxonomy: Reconciled Methodology

The FOV rule uses explicit path components: `Images` is FULL_FIELD, `ROI` is ROI_CROP,
and anything else is UNRESOLVED. Dimensions are supporting evidence only.

Sample counts and component counts are separate:
- TRAIN samples: FULL_FIELD 771; ROI_CROP 1208; UNRESOLVED 0; total 1979.
- TRAIN components: FULL_FIELD 1162; ROI_CROP 1214; UNRESOLVED 0; total 2376.

`kub_size_v1` is unchanged. It uses 8-connected FULL_FIELD TRAIN components only:
- Q25 = {thresholds['Q25']:.15f}
- Q50 = {thresholds['Q50']:.15f}
- Q75 = {thresholds['Q75']:.15f}

VAL receives these frozen TRAIN thresholds. TEST masks and external data are not accessed.
The strata are dataset-relative and have no physical/mm clinical interpretation.
"""
(AUDITS / "kub_object_size_thresholds.md").write_text(methodology, encoding="utf-8")

readme = """# SUPERSEDED Phase 7 Assets

These pre-R1 assets are preserved for provenance. They contained reporting that conflated
sample-level and component-level FOV counts. **DO NOT USE** them for scientific claims.
Use corrected `_v2` tables and figures plus `kub_object_size_provenance.json`.
"""
(ROOT / "reports" / "superseded" / "phase7_pre_r1" / "README.md").write_text(readme, encoding="utf-8")
print(json.dumps(reconciliation, indent=2))
