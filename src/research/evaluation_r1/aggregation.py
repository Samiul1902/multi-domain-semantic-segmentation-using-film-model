"""Explicit per-image and grouped summaries with missingness accounting."""
from __future__ import annotations

from collections import Counter
import numpy as np
from . import DOMAINS, VERSION
from .artifacts import freeze_artifacts
from .metrics import binary_metrics, surface_metrics, multiclass_metrics
from .statistics import describe
from .ontology import domain_schema


def _context(images):
    if not images:
        raise ValueError("no evaluated images")
    keys = ("population", "split", "metric_version", "threshold", "model_id", "checkpoint_sha256",
            "release_id", "dataset_version", "split_sha256", "evaluation_code_sha256")
    first = images[0]
    if any(any(r[k] != first[k] for k in keys) for r in images):
        raise ValueError("cannot aggregate mixed evaluation identities")
    return {k: first[k] for k in keys}


def evaluate(records, *, tolerance=1.0):
    snapshots = freeze_artifacts(records)
    images = []
    for snapshot in snapshots:
        r = snapshot.record()
        m = r["metadata"]
        pred = (np.asarray(r["probability"]) >= m["threshold"]).astype(np.uint8)
        truth = np.asarray(r["ground_truth"])
        fg, bg = binary_metrics(pred, truth), binary_metrics(1 - pred, 1 - truth)
        boundary = surface_metrics(pred, truth, m["spacing"], tolerance)
        images.append({"population": m["dataset_id"], "split": m["split"], "metric_version": VERSION,
                       "aggregation_unit": "image", "domain": m["domain_id"], "sample_id": m["sample_id"],
                       "patient_id": m.get("patient_id"), "subgroup": m.get("subgroup"), "source_id": m.get("source_id"),
                       "annotated_subclass": "NOT_AVAILABLE", "sample_count": 1,
                       "class_schema": domain_schema(m["domain_id"]),
                       "threshold": m["threshold"], "spacing_convention": boundary["unit"],
                       "area": {"unit": "mm2" if m["spacing"] is not None else "pixel2",
                                "reference": fg["reference_area_pixels"] * (float(np.prod(m["spacing"])) if m["spacing"] is not None else 1),
                                "predicted": fg["predicted_area_pixels"] * (float(np.prod(m["spacing"])) if m["spacing"] is not None else 1),
                                "signed_error": fg["area_error_pixels"] * (float(np.prod(m["spacing"])) if m["spacing"] is not None else 1)},
                       "model_id": m["model_id"], "checkpoint_sha256": m["checkpoint_sha256"],
                       "release_id": m["release_id"], "dataset_version": m["dataset_version"],
                       "split_sha256": m["split_sha256"], "evaluation_code_sha256": m["evaluation_code_sha256"],
                       "prediction_artifact_sha256": m["probability_sha256"],
                       "ground_truth_sha256": m["ground_truth_sha256"], "metadata_sha256": m["metadata_sha256"],
                       "class_overlap": multiclass_metrics(pred, truth, [0, 1]),
                       "n_undefined": {"foreground": sum(v is None for v in fg.values()),
                                       "background": sum(v is None for v in bg.values()),
                                       "surface": sum(v is None for k, v in boundary.items() if k not in {"undefined_reason"})},
                       "foreground": fg, "background": bg, "surface": boundary,
                       "failure_category": fg["empty_case"] if fg["empty_case"] != "both_nonempty" else ("false_positive_and_negative" if fg["fp"] and fg["fn"] else "false_positive" if fg["fp"] else "false_negative" if fg["fn"] else "perfect")})
    return images


def grouped_summary(images, key, metric="dice"):
    if key not in ("domain", "patient_id", "subgroup", "source_id", "failure_category"):
        raise ValueError("unsupported aggregation unit")
    result = []
    if not images:
        return []
    _context(images)
    groups = sorted({(r["domain"] if key != "domain" else "ALL", str(r.get(key) or "NOT_AVAILABLE")) for r in images})
    for domain, value in groups:
        selected = [r for r in images if str(r.get(key) or "NOT_AVAILABLE") == value and (domain == "ALL" or r["domain"] == domain)]
        if metric not in selected[0]["foreground"] or not isinstance(selected[0]["foreground"][metric], (int, float, type(None))):
            raise ValueError("unknown numeric foreground metric")
        values = [r["foreground"][metric] for r in selected]
        desc = describe([float(v) if v is not None else np.nan for v in values])
        grouping_missing = key in {"patient_id", "source_id", "subgroup"} and value == "NOT_AVAILABLE"
        if grouping_missing:
            desc.update({k: None for k in ("mean", "median", "sample_sd", "minimum", "maximum")})
        first = selected[0]
        result.append({**_context(selected), "n_missing_group_ids": len(selected) if grouping_missing else 0, "population": first["population"], "split": first["split"], "metric_version": VERSION,
                       "aggregation_unit": key, "domain": domain if domain != "ALL" else value,
                       "group": value, "status": "NOT_AVAILABLE" if key in {"patient_id", "source_id", "subgroup"} and value == "NOT_AVAILABLE" else "OBSERVED",
                       "class": "foreground", "metric": metric,
                       "sample_count": len(selected), "threshold": first["threshold"],
                       "spacing_convention": sorted({r["spacing_convention"] for r in selected}),
                       "model_id": first["model_id"], "checkpoint_sha256": first["checkpoint_sha256"],
                       "prediction_artifact_sha256": sorted(r["prediction_artifact_sha256"] for r in selected), **desc})
    return result


def equal_domain_macro(images, metric="dice"):
    summaries = grouped_summary(images, "domain", metric)
    lookup = {r["group"]: r for r in summaries}
    if set(lookup) != set(DOMAINS) or any(lookup[d]["n_missing"] or lookup[d]["mean"] is None for d in DOMAINS):
        raise ValueError("all four complete domains required")
    means = {d: lookup[d]["mean"] for d in DOMAINS}
    _context(images)
    first = images[0]
    return {**_context(images), "population": first["population"], "split": first["split"], "metric_version": VERSION,
            "aggregation_unit": "equal_domain_macro_of_image_means", "metric": metric, "class": "foreground",
            "threshold": first["threshold"], "spacing_convention": sorted({r["spacing_convention"] for r in images}),
            "model_id": first["model_id"], "checkpoint_sha256": first["checkpoint_sha256"],
            "prediction_artifact_sha256": sorted(r["prediction_artifact_sha256"] for r in images),
            "value": float(np.mean(list(means.values()))), "domain_means": means,
            "worst_domain": min(means, key=means.get), "worst_domain_value": min(means.values()),
            "sample_count": len(images), "n_missing": 0}


def pooled_pixel_summary(images, class_name="foreground"):
    """Pixel-pooled confusion metrics, explicitly NOT image/domain macro."""
    context = _context(images)
    if class_name not in {"foreground", "background"}:
        raise ValueError("unknown binary class")
    counts = {k: sum(r[class_name][k] for r in images) for k in ("tp", "fp", "tn", "fn")}
    tp, fp, tn, fn = (counts[k] for k in ("tp", "fp", "tn", "fn"))
    return {**context, "class": class_name, "domain": "POOLED_ALL_DOMAINS", "aggregation_unit": "pooled_pixels",
            "sample_count": len(images), "pixel_count": tp + fp + tn + fn, "n_missing": 0,
            "threshold": images[0]["threshold"], "spacing_convention": "not_applicable_to_pixel_counts",
            "prediction_artifact_sha256": sorted(r["prediction_artifact_sha256"] for r in images), **counts,
            "dice": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 1.0,
            "iou": tp / (tp + fp + fn) if tp + fp + fn else 1.0}


def surface_summary(images):
    """Per-domain image-macro geometry, refusing incompatible spacing units."""
    _context(images)
    result = []
    for domain in DOMAINS:
        selected = [r for r in images if r["domain"] == domain]
        if not selected:
            continue
        definitions = {(r["surface"]["unit"], r["surface"]["tolerance"], r["surface"]["weighting"]) for r in selected}
        if len(definitions) != 1:
            raise ValueError("incompatible surface units/tolerance/definitions")
        for metric in ("hd95", "hausdorff", "assd", "surface_dice", "surface_precision", "surface_recall"):
            context = grouped_summary(selected, "domain")[0]
            context.update({"metric": metric, "unit": selected[0]["surface"]["unit"],
                            "tolerance": selected[0]["surface"]["tolerance"],
                            **describe([r["surface"][metric] for r in selected])})
            result.append(context)
    return result


def class_summary(images):
    """Image-macro class summaries; binary classes remain domain-specific."""
    result = []
    for domain in DOMAINS:
        selected = [r for r in images if r["domain"] == domain]
        if not selected:
            continue
        for class_name in ("foreground", "background"):
            for metric in ("dice", "iou"):
                context = grouped_summary(selected, "domain", metric)[0]
                context.update({"class": class_name, "metric": metric,
                                **describe([r[class_name][metric] for r in selected])})
                result.append(context)
    return result


def failure_breakdown(images):
    return dict(sorted(Counter(r["failure_category"] for r in images).items()))
