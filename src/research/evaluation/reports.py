"""Reproducible report and figure tables.

Every table carries an ``evidence_class`` column and every manifest states it in
words, so a synthetic table cannot be mistaken for a research result once it
leaves this module.  Nothing here inserts a number into the manuscript; these
are files under ``reports/tables/phase_c/`` only.

The eight required artefacts:

1. eight-model comparison table
2. per-domain Dice/IoU table
3. seed-wise results
4. paired improvement table
5. accuracy–parameter trade-off
6. accuracy–MAC trade-off
7. accuracy–latency trade-off
8. conditional routing statistics
9. model-specific failure summaries

(Nine files; the mission lists eight generators with the routing and failure
views counted separately.)
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

import numpy as np

from . import efficiency as EF
from . import protocol as P
from . import provenance as PROV
from . import registry as REG
from . import runner as RN
from . import stats as ST

TABLE_FILES = {
    "comparison": "eight_model_comparison.csv",
    "per_domain": "per_domain_dice_iou.csv",
    "seed_wise": "seed_wise_results.csv",
    "paired": "paired_improvement.csv",
    "acc_parameter": "accuracy_parameter_tradeoff.csv",
    "acc_mac": "accuracy_mac_tradeoff.csv",
    "acc_latency": "accuracy_latency_tradeoff.csv",
    "routing": "conditional_routing_statistics.csv",
    "failures": "model_failure_summary.csv",
}

SYNTHETIC_BANNER = ("SYNTHETIC_TEST_ONLY — these numbers come from deterministic fixtures "
                    "with untrained weights. They are not research results and must not "
                    "appear in the manuscript.")
REAL_BANNER = ("REAL_VAL808_DEVELOPMENT — development/selection-consumed. Not an "
               "independent confirmation.")
EMPTY_BANNER = ("NO_EVIDENCE — no cell has been published, so there is nothing here to "
                "read as a result. Absence is not a measurement.")
MIXED_BANNER = "MIXED_EVIDENCE — read the evidence_class column."


def _banner(evidence_classes: Sequence[str]) -> str:
    if not evidence_classes:
        return EMPTY_BANNER
    if list(evidence_classes) == [P.SYNTHETIC_EVIDENCE]:
        return SYNTHETIC_BANNER
    if list(evidence_classes) == [P.REAL_VAL_EVIDENCE]:
        return REAL_BANNER
    return MIXED_BANNER


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return PROV.atomic_write_text(path, "")
    columns: List[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    lines = [",".join(columns)]
    for row in rows:
        lines.append(",".join(_cell(row.get(c)) for c in columns))
    return PROV.atomic_write_text(path, "\n".join(lines) + "\n")


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, float):
        return "nan" if value != value else f"{value:.6f}"
    text = str(value)
    if any(ch in text for ch in ',"\n'):
        return '"' + text.replace('"', '""') + '"'
    return text


# --------------------------------------------------------------------------- #
# Collect
# --------------------------------------------------------------------------- #
def collect_results(root: Path, *, bootstrap_unit: str = "image") -> Dict[str, Any]:
    """Read every published cell and assemble the report inputs."""
    root = Path(root)
    records = RN.records_by_cell(root)
    cells: List[Dict[str, Any]] = []
    for model_key, seed in REG.model_seed_cells():
        directory = root / model_key / f"seed{seed}"
        outcome = PROV.verify_cell(directory)
        entry: Dict[str, Any] = {"model_key": model_key, "seed": seed,
                                 "display_name": REG.DISPLAY_NAME[model_key],
                                 "role": REG.spec(model_key).role,
                                 "status": outcome["status"],
                                 "reasons": outcome["reasons"]}
        if outcome["document"] is not None:
            doc = outcome["document"]
            entry.update({
                "evidence_class": doc["evidence_class"],
                "equal_domain_macro_dice": doc["summary"].get("equal_domain_macro_dice"),
                "per_domain": doc["summary"].get("per_domain"),
                "parameters": doc["summary"].get("parameters")
                              or doc["provenance"].get("adapter_identity", {}).get("parameters"),
                "refiner_invocation_rate": doc["summary"].get("refiner_invocation_rate"),
                "harmful_accepted_refinements": doc["summary"].get("harmful_accepted_refinements"),
                "n_images": doc["n_images"],
                "synthetic": doc["synthetic"],
            })
            profile_path = directory / "efficiency.json"
            if profile_path.is_file():
                entry["efficiency"] = json.loads(profile_path.read_text(encoding="utf-8"))
        cells.append(entry)

    comparisons = ST.build_comparisons(records, unit=bootstrap_unit)
    evidence = sorted({c.get("evidence_class") for c in cells if c.get("evidence_class")})
    return {"schema": "phase_c_results_v1", "root": str(root),
            "evidence_classes": evidence,
            "banner": _banner(evidence),
            "cells": cells, "comparisons": comparisons,
            "research_cells_completed": sum(
                1 for c in cells
                if c["status"] == "COMPLETE_VALIDATED"
                and c.get("evidence_class") in P.RESEARCH_EVIDENCE_CLASSES),
            "synthetic_cells_executed": sum(
                1 for c in cells
                if c["status"] == "COMPLETE_VALIDATED"
                and c.get("evidence_class") == P.SYNTHETIC_EVIDENCE),
            "registry_status": _registry_status(cells)}


def _registry_status(cells: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """The 24-cell registry verdict.  Synthetic success never completes a cell."""
    completed = [c for c in cells
                 if c["status"] == "COMPLETE_VALIDATED"
                 and c.get("evidence_class") in P.RESEARCH_EVIDENCE_CLASSES]
    return {"n_cells": len(cells),
            "research_completed": len(completed),
            "all_cells_not_established": len(completed) == 0,
            "status": ("NOT_ESTABLISHED_0_OF_24" if not completed
                       else f"PARTIAL_{len(completed)}_OF_24"),
            "note": ("A cell is only established by a real, protocol-compliant evaluation. "
                     "Synthetic execution does not count.")}


# --------------------------------------------------------------------------- #
# Tables
# --------------------------------------------------------------------------- #
def _seed_rows(cells: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    return [{"model_key": c["model_key"], "display_name": c["display_name"],
             "role": c["role"], "seed": c["seed"], "status": c["status"],
             "evidence_class": c.get("evidence_class"),
             "equal_domain_macro_dice": c.get("equal_domain_macro_dice"),
             "n_images": c.get("n_images")} for c in cells]


def comparison_rows(cells: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for model_key in REG.DISPLAY_ORDER:
        selected = [c for c in cells if c["model_key"] == model_key
                    and c["status"] == "COMPLETE_VALIDATED"]
        if not selected:
            rows.append({"model_key": model_key, "display_name": REG.DISPLAY_NAME[model_key],
                         "status": "MISSING", "n_seeds": 0})
            continue
        summary = ST.seed_summary([c["equal_domain_macro_dice"] for c in selected],
                                  label=model_key)
        rows.append({"model_key": model_key, "display_name": REG.DISPLAY_NAME[model_key],
                     "role": selected[0]["role"], "status": "COMPLETE_VALIDATED",
                     "n_seeds": summary["n_seeds"], "macro_dice_mean": summary["mean"],
                     "macro_dice_sd": summary["sd"],
                     "evidence_class": selected[0].get("evidence_class"),
                     "note": "seed spread is descriptive, not a standard error"})
    return rows


def per_domain_rows(cells: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for c in cells:
        if c["status"] != "COMPLETE_VALIDATED" or not c.get("per_domain"):
            continue
        for domain in P.DOMAINS:
            block = c["per_domain"].get(domain, {})
            rows.append({"model_key": c["model_key"], "seed": c["seed"], "domain": domain,
                         "n": block.get("n"), "dice": block.get("dice"),
                         "iou": block.get("iou"), "hd95_mean": block.get("hd95_mean"),
                         "hd95_unit": block.get("hd95_unit"),
                         "empty_gt_n": block.get("empty_gt_n"),
                         "evidence_class": c.get("evidence_class")})
    return rows


def paired_rows(comparisons: Mapping[str, Any],
                *, evidence_class: Optional[str] = None) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    def emit(block: Mapping[str, Any]) -> None:
        for seed, result in (block.get("per_seed") or {}).items():
            rows.append({
                "comparison": block.get("comparison"), "seed": seed,
                "status": result.get("status"),
                "n_paired_images": result.get("n_paired_images"),
                "mean_difference": result.get("mean_difference"),
                "ci_low": result.get("ci_low"), "ci_high": result.get("ci_high"),
                "ci_method": result.get("ci_method"),
                "resampling_unit": result.get("resampling_unit"),
                "n_clusters": result.get("n_clusters"),
                "inference_class": result.get("inference_class"),
                "p_value": result.get("p_value"),
                "claim_status": result.get("claim_status"),
                "evidence_class": evidence_class,
                "reason": result.get("reason"),
            })

    emit(comparisons.get("full_vs_global", {}))
    emit(comparisons.get("full_vs_lite", {}))
    for block in (comparisons.get("full_vs_baselines") or {}).values():
        emit(block)
    for block in (comparisons.get("lite_vs_baselines") or {}).values():
        emit(block)
    return rows


def tradeoff_rows(cells: Sequence[Mapping[str, Any]], metric: str) -> List[Dict[str, Any]]:
    rows = []
    for c in cells:
        if c["status"] != "COMPLETE_VALIDATED":
            continue
        eff = c.get("efficiency") or {}
        base = {"model_key": c["model_key"], "seed": c["seed"],
                "equal_domain_macro_dice": c.get("equal_domain_macro_dice"),
                "evidence_class": c.get("evidence_class")}
        if metric == "parameters":
            base.update({"parameters": eff.get("unique_inference_parameters")})
        elif metric == "macs":
            base.update({"macs_conv_linear": eff.get("effective_macs_per_image")
                         if eff.get("effective_macs_per_image") is not None
                         else eff.get("macs_global_only"),
                         "macs_basis": ("conditional_effective"
                                        if eff.get("effective_macs_per_image") is not None
                                        else "unconditional"),
                         "macs_if_always_refine": eff.get("macs_if_always_refine")})
        else:
            base.update({"latency_ms_p50": eff.get("latency_ms_p50"),
                         "latency_ms_p95": eff.get("latency_ms_p95"),
                         "peak_memory_mib": eff.get("peak_allocated_mib")})
        rows.append(base)
    return rows


def routing_rows(cells: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for c in cells:
        if c["status"] != "COMPLETE_VALIDATED":
            continue
        rows.append({"model_key": c["model_key"], "seed": c["seed"],
                     "conditional": c["model_key"] in (REG.FULL, REG.LITE),
                     "refiner_invocation_rate": c.get("refiner_invocation_rate"),
                     "harmful_accepted_refinements": c.get("harmful_accepted_refinements"),
                     "effective_macs_per_image": (c.get("efficiency") or {}).get(
                         "effective_macs_per_image"),
                     "macs_if_always_refine": (c.get("efficiency") or {}).get(
                         "macs_if_always_refine"),
                     "evidence_class": c.get("evidence_class"),
                     "note": ("fewer refiner calls is not by itself a lower total cost; "
                              "compare effective_macs_per_image")})
    return rows


def failure_rows(cells: Sequence[Mapping[str, Any]],
                 records: Optional[Mapping[tuple, Sequence[Mapping[str, Any]]]] = None,
                 *, evidence_class: Optional[str] = None) -> List[Dict[str, Any]]:
    rows = []
    for c in cells:
        cell_evidence = c.get("evidence_class") or evidence_class
        if c["status"] != "COMPLETE_VALIDATED":
            rows.append({"model_key": c["model_key"], "seed": c["seed"],
                         "status": c["status"], "evidence_class": cell_evidence,
                         "reason": "; ".join(c.get("reasons") or [])})
            continue
        rows.append({"model_key": c["model_key"], "seed": c["seed"], "status": c["status"],
                     "evidence_class": cell_evidence,
                     "empty_gt_false_positives": None, "harmful_accepted_refinements":
                         c.get("harmful_accepted_refinements"),
                     "reason": ""})
    return rows


# --------------------------------------------------------------------------- #
# Write everything
# --------------------------------------------------------------------------- #
def _table_evidence(results: Mapping[str, Any]) -> Optional[str]:
    """The single evidence class of a homogeneous result set, else ``MIXED``."""
    evidence = list(results.get("evidence_classes") or [])
    if not evidence:
        return None
    return evidence[0] if len(evidence) == 1 else MIXED_BANNER


def write_tables(root: Path, out_dir: Path, *,
                 bootstrap_unit: str = "image") -> Dict[str, Any]:
    root, out_dir = Path(root), Path(out_dir)
    results = collect_results(root, bootstrap_unit=bootstrap_unit)
    records = RN.records_by_cell(root)
    cells = results["cells"]

    tables = {
        "comparison": comparison_rows(cells),
        "per_domain": per_domain_rows(cells),
        "seed_wise": _seed_rows(cells),
        "paired": paired_rows(results["comparisons"], evidence_class=_table_evidence(results)),
        "acc_parameter": tradeoff_rows(cells, "parameters"),
        "acc_mac": tradeoff_rows(cells, "macs"),
        "acc_latency": tradeoff_rows(cells, "latency"),
        "routing": routing_rows(cells),
        "failures": failure_rows(cells, records, evidence_class=_table_evidence(results)),
    }
    hashes = {key: _write_csv(out_dir / TABLE_FILES[key], rows)
              for key, rows in tables.items()}
    manifest = {
        "schema": "phase_c_report_manifest_v1",
        "banner": results["banner"],
        "evidence_classes": results["evidence_classes"],
        "registry_status": results["registry_status"],
        "research_cells_completed": results["research_cells_completed"],
        "synthetic_cells_executed": results["synthetic_cells_executed"],
        "tables": {key: {"file": TABLE_FILES[key], "sha256": hashes[key],
                         "rows": len(tables[key])} for key in tables},
        "statistics_policy": {
            "inference_class": ST.EXPLORATORY,
            "confirmatory_authorized": ST.CONFIRMATORY_AUTHORIZED,
            "confirmatory_block_reason": ST.CONFIRMATORY_BLOCK_REASON,
            "p_values_generated": 0,
            "claim_status": ST.CLAIM_STATUS},
        "note": ("Generated from published cell artifacts only. A synthetic banner means "
                 "no research result exists."),
    }
    PROV.atomic_write_json(out_dir / "report_manifest.json", manifest)
    results["tables"] = tables
    results["manifest"] = manifest
    return results


__all__ = ["EMPTY_BANNER", "MIXED_BANNER", "REAL_BANNER", "SYNTHETIC_BANNER",
           "TABLE_FILES", "collect_results", "comparison_rows", "failure_rows",
           "paired_rows", "per_domain_rows", "routing_rows", "tradeoff_rows",
           "write_tables"]
