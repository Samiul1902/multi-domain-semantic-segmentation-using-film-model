"""Deterministic artificial fixtures and JSON report; no dataset access."""
from __future__ import annotations
import hashlib
import json
import numpy as np
from . import DOMAINS, SCHEMA_VERSION, VERSION, code_identity
from .artifacts import array_sha256
from .aggregation import evaluate, grouped_summary, equal_domain_macro, failure_breakdown, class_summary, pooled_pixel_summary, surface_summary
from .statistics import paired_bootstrap, run_accounting, subgroup_effects, budget_quality
from .ontology import load_ontology


def fixture():
    records = []
    for i, domain in enumerate(DOMAINS):
        p = np.zeros((3, 3), dtype=np.float32)
        g = np.zeros((3, 3), dtype=np.uint8)
        g[1, 1] = 1
        if i < 3:
            p[1, 1] = 0.9
        if i == 1:
            p[1, 2] = 0.9
        m = {"experiment_id": "SYNTHETIC_TEST_ONLY", "model_id": "synthetic-model", "checkpoint_sha256": "0" * 64,
             "seed": 42, "dataset_id": "synthetic-four-domain", "split": "SYNTHETIC", "sample_id": f"synthetic-{i}",
             "domain_id": domain, "class_schema_version": SCHEMA_VERSION, "probability_shape": [3, 3],
             "ground_truth_encoding": "binary_0_1", "threshold": 0.5, "spacing": None,
             "evaluation_code_version": VERSION, "probability_sha256": array_sha256(p), "ground_truth_sha256": array_sha256(g),
             "patient_id": "synthetic-patient" if domain == "KUB" else None, "subgroup": None,
             "release_id": "synthetic-release", "dataset_version": "artificial_fixture_v1",
             "split_sha256": hashlib.sha256(b"synthetic-0,synthetic-1,synthetic-2,synthetic-3").hexdigest(),
             "evaluation_code_sha256": code_identity()}
        m["metadata_sha256"] = hashlib.sha256(json.dumps(m, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        records.append({"metadata": m, "probability": p, "ground_truth": g})
    return records


def report():
    records = fixture()
    images = evaluate(records)
    rows = [{"domain": d, "sample_id": f"synthetic-{i}", "seed": s, "treatment": 0.6 + i * 0.05,
             "control": 0.5, "patient_id": "synthetic-patient" if d == "KUB" else None}
            for i, d in enumerate(DOMAINS) for s in (42, 123, 3407)]
    comparison = paired_bootstrap(rows, seeds=(42, 123, 3407), n_boot=200, rng_seed=7)
    comparison.update({"population": "fabricated-scalars", "split": "SYNTHETIC", "metric": "fabricated Dice-scale scalar",
                       "metric_version": VERSION, "aggregation_unit": "equal_domain_equal_seed_paired_case_means",
                       "model_id": {"treatment": "synthetic-T", "control": "synthetic-C"},
                       "prediction_artifact_identity": "fabricated scalar formula; not image prediction scores",
                       "threshold": "NOT_APPLICABLE_SCALARS", "spacing_convention": "NOT_APPLICABLE",
                       "note": "200 generic demonstration resamples; not a C1 primary analysis"})
    return {"label": "SYNTHETIC_TEST_ONLY", "artifact_contract": "harmonized_binary_v1",
            "per_image": images, "per_class": class_summary(images),
            "per_patient": grouped_summary(images, "patient_id"), "per_subgroup": grouped_summary(images, "subgroup"),
            "per_source": grouped_summary(images, "source_id"),
            "per_domain": grouped_summary(images, "domain"), "equal_domain_macro": equal_domain_macro(images),
            "pooled_pixels": pooled_pixel_summary(images), "per_domain_surfaces": surface_summary(images),
            "comparison": comparison,
            "run_accounting_example": run_accounting([{"arm": "synthetic-T", "seed": 42, "status": "FAILED"}],
                                                     arms=("synthetic-T", "synthetic-C"), seeds=(42, 123, 3407)),
            "subgroup_effect_example": subgroup_effects(rows),
            "budget_quality_example": budget_quality([{"model": "synthetic-model", "budget": 1,
                                                        "budget_unit": "artificial_cost_units", "quality": 0.5,
                                                        "quality_metric": "fabricated_scalar"}]),
            "undefined_surface_count": sum(not r["surface"]["valid"] for r in images),
            "undefined_counts": {section: {metric: sum(r[section][metric] is None for r in images)
                                            for metric in images[0][section] if metric != "undefined_reason"}
                                 for section in ("foreground", "background", "surface")},
            "failure_breakdown": {"counts": failure_breakdown(images), "sample_count": len(images),
                                  "population": "synthetic-four-domain", "split": "SYNTHETIC", "metric_version": VERSION},
            "ontology_schema": load_ontology()["schema_version"],
            "source_identity": "fabricated arrays in src/research/evaluation_r1/synthetic.py; no real source"}


def report_bytes():
    return (json.dumps(report(), sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def write_examples(directory):
    """Write reproducible synthetic-only examples; refuse differing existing files."""
    import csv
    import io
    from pathlib import Path
    output = Path(directory)
    output.mkdir(parents=True, exist_ok=True)
    content = report_bytes()
    result = json.loads(content)
    table = io.StringIO(newline="")
    writer = csv.writer(table, lineterminator="\n")
    writer.writerow(["label", "population", "split", "domain", "sample_count", "metric", "value", "n_missing", "metric_version"])
    for r in result["per_domain"]:
        writer.writerow(["SYNTHETIC_TEST_ONLY", r["population"], r["split"], r["group"], r["sample_count"], "foreground_dice", r["mean"], r["n_missing"], VERSION])
    payloads = {"synthetic_results.json": content, "synthetic_example_table.csv": table.getvalue().encode()}
    for name, data in payloads.items():
        p = output / name
        if p.exists() and p.read_bytes() != data:
            raise ValueError("refuse overwrite of differing output: " + str(p))
    for name, data in payloads.items():
        p = output / name
        if not p.exists():
            p.write_bytes(data)
    return {name: hashlib.sha256(data).hexdigest() for name, data in payloads.items()}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SYNTHETIC_TEST_ONLY example generator; no data loader")
    parser.add_argument("--output", required=True, help="new or byte-identical synthetic report directory")
    args = parser.parse_args()
    print(json.dumps(write_examples(args.output), sort_keys=True))
