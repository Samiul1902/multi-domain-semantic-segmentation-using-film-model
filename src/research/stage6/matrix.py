"""Eight-model x three-seed (24-cell) matrix, per-image exporters and paired aggregation.

Missing cells stay MISSING.  Nothing here fabricates or imputes a result, and a cell is
accepted only when its provenance proves a real, protocol-compatible VAL808 evaluation.
All VAL808 numbers are development-selection-consumed, never independent confirmation.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from src.metrics.segmentation import hd95 as binary_hd95

ROOT = Path(__file__).resolve().parents[3]
SEEDS = (42, 123, 3407)
DOMAINS = ("ISIC", "BUSI", "KVASIR", "KUB")
TASK_IDS = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}
PROTOCOL_SHA256 = "531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61"
VAL_MANIFEST_SHA256_PREFIX = "082c80b2"
VAL_N = 808
RUN_ROOT = ROOT / "experiments" / "stage6_eight_model"

FULL, LITE, GLOBAL = "RA_MEDFILM_BARR_FULL", "RA_MEDFILM_BARR_LITE_DEPTHWISE", "GLOBAL_MEDFILM"
BASELINES = ("UNET", "ATTENTION_UNET", "UNETPP", "DEEPLABV3PLUS", "TRANSFORMER_MIT_UNET")
MODEL_KEYS = (FULL, LITE, GLOBAL, *BASELINES)

# Existing producers are named only where the file exists in the repository.
MODEL_REGISTRY: dict[str, dict[str, Any]] = {
    FULL: {"role": "PRIMARY_PROPOSED", "c3_key": "ra_medfilm_barr_full", "chain": ("G", "R_psi", "B_phi", "S_omega"),
           "producer": "scripts/training/train_phase21_global_medfilm.py -> train_phase25a_refiner.py -> "
                       "scripts/analysis/train_phase25d_router.py -> phase25f_execution_common.py",
           "multi_seed_producer": "MISSING: no automated multi-seed G->R->B->S pipeline"},
    LITE: {"role": "SECONDARY_PROPOSED", "chain": ("G", "R_psi", "B_phi", "S_omega"),
           "producer": "src/research/stage6/lite_chain.py (G/R_psi/B_phi/S_omega trainers, synthetic-gated)",
           "multi_seed_producer": "BLOCKED: needs Lite cross-fitted OOF labels + real-data release"},
    GLOBAL: {"role": "INTERNAL_BACKBONE_REFERENCE", "chain": ("G",),
             "producer": "scripts/analysis/run_c1_campaign_launch.py (C1-T) / train_phase21_global_medfilm.py",
             "multi_seed_producer": "C1 six-run campaign (execution not authorized)"},
}
for _key in BASELINES:
    MODEL_REGISTRY[_key] = {"role": "EXTERNAL_ARCHITECTURE_BASELINE", "c3_key": _key.lower(), "chain": (),
                            "producer": "src/research/c3_baselines/experiment.py (train_run)",
                            "multi_seed_producer": "BLOCKED: run-real raises pending separate authorization"}

EVIDENCE_LABEL = "VAL808_DEVELOPMENT_SELECTION_CONSUMED__NOT_INDEPENDENT_CONFIRMATION"
HISTORICAL_BASELINE_LABEL = "PROTOCOL_INCOMPARABLE"


class Stage6Error(RuntimeError):
    pass


def build_cells() -> list[dict[str, Any]]:
    return [{"model_key": m, "seed": s, "role": MODEL_REGISTRY[m]["role"], "status": "MISSING"}
            for m in MODEL_KEYS for s in SEEDS]


def cell_dir(root: Path, model: str, seed: int) -> Path:
    return Path(root) / model / f"seed{seed}"


def c1t_can_populate_global(c1_manifest: Mapping[str, Any]) -> tuple[bool, list[str]]:
    """Reuse C1-T output for GLOBAL_MEDFILM only when every compatibility fact is proven."""
    reasons: list[str] = []
    required = {
        "arm": "C1-T",
        "model_identity": "GlobalMedFiLM",
        "protocol_sha256": PROTOCOL_SHA256,
        "train_n": 5832,
        "val_n": VAL_N,
        "resolution": 512,
        "channel_policy": "RGB_3CH",
        "selection_rule": "phase20_macro_domain_mean_dice_v1",
        "threshold": 0.5,
    }
    for key, expected in required.items():
        if c1_manifest.get(key) != expected:
            reasons.append(f"{key}: expected {expected!r}, got {c1_manifest.get(key)!r}")
    if c1_manifest.get("seed") not in SEEDS:
        reasons.append("seed not in 42/123/3407")
    if not c1_manifest.get("checkpoint_sha256"):
        reasons.append("missing checkpoint_sha256 provenance")
    if not c1_manifest.get("per_image_export_sha256"):
        reasons.append("missing per-image VAL808 export")
    if c1_manifest.get("protected_splits_accessed"):
        reasons.append("protected split accessed")
    return not reasons, reasons


def per_image_record(*, sample_id: str, domain: str, final_prob: np.ndarray, global_prob: np.ndarray,
                     mask: np.ndarray, state: str = "NOT_APPLICABLE", threshold: float = 0.5) -> dict[str, Any]:
    """Metrics for one image.  ``mask`` is used only here, after inference has finished."""
    gt = np.asarray(mask).astype(bool)

    def conf(prob: np.ndarray) -> dict[str, float]:
        pred = np.asarray(prob) >= threshold
        tp, fp, fn = int((pred & gt).sum()), int((pred & ~gt).sum()), int((~pred & gt).sum())
        eps = 1e-7
        return {"dice": (2 * tp + eps) / (2 * tp + fp + fn + eps), "iou": (tp + eps) / (tp + fp + fn + eps),
                "precision": (tp + eps) / (tp + fp + eps), "recall": (tp + eps) / (tp + fn + eps),
                "pred_empty": not pred.any()}

    final, glob = conf(final_prob), conf(global_prob)
    hd = binary_hd95(np.asarray(final_prob) >= threshold, gt)
    executed = state in ("EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT")
    accepted = state == "EXECUTE_THEN_ACCEPT"
    return {
        "sample_id": sample_id, "domain": domain, "state": state,
        "dice": final["dice"], "iou": final["iou"], "precision": final["precision"], "recall": final["recall"],
        "hd95": hd["hd95"] if hd["hd95_valid"] else None,
        "hd95_undefined_reason": None if hd["hd95_valid"] else hd["invalid_reason"],
        "gt_empty": not gt.any(), "pred_empty": final["pred_empty"],
        "empty_gt_false_positive": bool((not gt.any()) and (not final["pred_empty"])),
        "global_dice": glob["dice"], "delta_dice_vs_global": final["dice"] - glob["dice"],
        "refiner_executed": executed, "accepted": accepted,
        "harmful_accepted": bool(accepted and final["dice"] < glob["dice"] - 1e-9),
    }


def _pct(values: Sequence[float], q: float) -> float:
    return float(np.percentile(np.asarray(values, dtype=np.float64), q)) if values else float("nan")


def summarize_records(records: Sequence[Mapping[str, Any]], *, latency_ms: Sequence[float] = (),
                      peak_memory_mib: float | None = None, parameters: int | None = None,
                      macs: float | None = None, has_routing: bool = False) -> dict[str, Any]:
    if not records:
        raise Stage6Error("no per-image records")
    per_domain: dict[str, dict[str, Any]] = {}
    for dom in DOMAINS:
        rows = [r for r in records if r["domain"] == dom]
        if not rows:
            continue
        hd = [r["hd95"] for r in rows if r["hd95"] is not None]
        per_domain[dom] = {
            "n": len(rows), **{k: float(np.mean([r[k] for r in rows])) for k in ("dice", "iou", "precision", "recall")},
            "hd95_mean": float(np.mean(hd)) if hd else None, "hd95_defined_n": len(hd),
            "empty_gt_n": sum(r["gt_empty"] for r in rows),
            "empty_gt_false_positives": sum(r["empty_gt_false_positive"] for r in rows)}
    if set(per_domain) != set(DOMAINS):
        raise Stage6Error("records must cover all four domains")
    empty = [r for r in records if r["gt_empty"]]
    out = {
        "n_images": len(records), "per_domain": per_domain,
        "equal_domain_macro_dice": float(np.mean([per_domain[d]["dice"] for d in DOMAINS])),
        "empty_mask_false_positive_rate": (sum(r["empty_gt_false_positive"] for r in empty) / len(empty)) if empty else None,
        "parameters": parameters, "macs": macs, "peak_memory_mib": peak_memory_mib,
        "latency_ms_p50": _pct(latency_ms, 50) if latency_ms else None,
        "latency_ms_p95": _pct(latency_ms, 95) if latency_ms else None,
    }
    if has_routing:
        executed = [r for r in records if r["refiner_executed"]]
        out.update({
            "router_execution_fraction": len(executed) / len(records),
            "safety_accept_fraction_of_executed": (sum(r["accepted"] for r in executed) / len(executed)) if executed else None,
            "safety_reject_fraction_of_executed": (sum(not r["accepted"] for r in executed) / len(executed)) if executed else None,
            "harmful_accepted_refinements": sum(r["harmful_accepted"] for r in records),
        })
    return out


def write_cell_result(directory: Path, *, model_key: str, seed: int, records: Sequence[Mapping[str, Any]],
                      summary: Mapping[str, Any], provenance: Mapping[str, Any]) -> dict[str, Any]:
    """Persist per-image CSV + cell_result.json.  Provenance is mandatory and is verified on load."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    csv_path = directory / "per_image.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    doc = {"model_key": model_key, "seed": seed, "per_image_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
           "summary": dict(summary), "provenance": dict(provenance), "evidence_label": EVIDENCE_LABEL}
    (directory / "cell_result.json").write_text(json.dumps(doc, indent=2, allow_nan=False, default=_json_default), encoding="utf-8")
    return doc


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, np.bool_):
        return bool(value)
    raise TypeError(type(value))


def _read_per_image(path: Path) -> dict[str, dict[str, Any]]:
    with Path(path).open(newline="", encoding="utf-8") as f:
        rows = {}
        for row in csv.DictReader(f):
            for key in ("dice", "global_dice", "delta_dice_vs_global"):
                row[key] = float(row[key])
            rows[row["sample_id"]] = row
    return rows


def validate_cell(directory: Path, model_key: str, seed: int) -> tuple[dict[str, Any] | None, list[str]]:
    """Return (cell, reasons).  A cell with any reason is rejected, never repaired."""
    directory = Path(directory)
    result_path = directory / "cell_result.json"
    if not result_path.is_file():
        return None, ["cell_result.json absent"]
    doc = json.loads(result_path.read_text(encoding="utf-8"))
    prov, reasons = doc.get("provenance", {}), []
    if doc.get("model_key") != model_key or doc.get("seed") != seed:
        reasons.append("model/seed identity mismatch")
    if prov.get("synthetic") is not False or prov.get("training_performed") is not True:
        reasons.append("not a real trained run")
    if prov.get("protocol_sha256") != PROTOCOL_SHA256:
        reasons.append("frozen protocol hash mismatch")
    if not str(prov.get("val_manifest_sha256", "")).startswith(VAL_MANIFEST_SHA256_PREFIX):
        reasons.append("VAL808 manifest hash mismatch")
    if prov.get("protected_splits_accessed"):
        reasons.append("protected split accessed")
    if not prov.get("checkpoint_sha256") or not prov.get("evaluation_hardware"):
        reasons.append("missing checkpoint or hardware provenance")
    if model_key in (FULL, LITE) and not prov.get("component_chain_sha256"):
        reasons.append("missing component chain provenance")
    if model_key == FULL and prov.get("global_only_substituted"):
        reasons.append("GlobalMedFiLM substituted for FULL")
    per_image = directory / "per_image.csv"
    if not per_image.is_file() or hashlib.sha256(per_image.read_bytes()).hexdigest() != doc.get("per_image_sha256"):
        reasons.append("per-image export missing or hash mismatch")
    elif len(_read_per_image(per_image)) != VAL_N:
        reasons.append(f"per-image export does not contain {VAL_N} unique images")
    return (None if reasons else doc), reasons


def _mean_sd(values: Sequence[float]) -> dict[str, Any]:
    arr = np.asarray(values, dtype=np.float64)
    return {"n_seeds": len(arr), "mean": float(arr.mean()),
            "sd": float(arr.std(ddof=1)) if len(arr) > 1 else None}


def _paired(root: Path, accepted: Mapping[tuple[str, int], Mapping[str, Any]], a: str, b: str) -> dict[str, Any]:
    """Paired (a - b) per-seed on identical sample IDs; descriptive only."""
    seeds = [s for s in SEEDS if (a, s) in accepted and (b, s) in accepted]
    if not seeds:
        return {"status": "NOT_AVAILABLE", "reason": "no seed has both cells"}
    per_seed = []
    for s in seeds:
        ra, rb = (_read_per_image(cell_dir(root, m, s) / "per_image.csv") for m in (a, b))
        if set(ra) != set(rb):
            return {"status": "REJECTED", "reason": f"sample IDs differ at seed {s}"}
        diffs = np.asarray([ra[i]["dice"] - rb[i]["dice"] for i in sorted(ra)])
        sa, sb = accepted[(a, s)]["summary"], accepted[(b, s)]["summary"]
        cost = {k: (sa[k] - sb[k]) if sa.get(k) is not None and sb.get(k) is not None else None
                for k in ("parameters", "macs", "latency_ms_p50", "latency_ms_p95", "peak_memory_mib")}
        per_seed.append({"seed": s, "mean_paired_dice_difference": float(diffs.mean()),
                         "macro_dice_difference": sa["equal_domain_macro_dice"] - sb["equal_domain_macro_dice"],
                         "n_paired_images": len(diffs), "cost_difference": cost})
    return {"status": "DESCRIPTIVE", "comparison": f"{a} minus {b}", "seeds": seeds, "per_seed": per_seed,
            "seed_variability_sd_of_macro_difference": (
                float(np.std([p["macro_dice_difference"] for p in per_seed], ddof=1)) if len(per_seed) > 1 else None),
            "note": "Seeds 123/3407 reuse the seed-42 G for FULL downstream; not independent end-to-end seeds."
                    if FULL in (a, b) else ""}


def aggregate_stage6(runs_root: Path = RUN_ROOT, out: Path | None = None) -> dict[str, Any]:
    """Aggregate whatever validated cells exist; every absent cell is reported as MISSING."""
    runs_root = Path(runs_root)
    cells, accepted = [], {}
    for model in MODEL_KEYS:
        for seed in SEEDS:
            doc, reasons = validate_cell(cell_dir(runs_root, model, seed), model, seed)
            if doc is not None:
                accepted[(model, seed)] = doc
            status = "COMPLETED_VALIDATED" if doc is not None else (
                "MISSING" if reasons == ["cell_result.json absent"] else "REJECTED")
            cells.append({"model_key": model, "seed": seed, "role": MODEL_REGISTRY[model]["role"],
                          "status": status, "rejection_reasons": [] if doc is not None else reasons})
    per_model = {}
    for model in MODEL_KEYS:
        docs = [accepted[(model, s)] for s in SEEDS if (model, s) in accepted]
        if docs:
            per_model[model] = {"cells_present": len(docs),
                                "equal_domain_macro_dice": _mean_sd([d["summary"]["equal_domain_macro_dice"] for d in docs]),
                                "parameters": docs[0]["summary"].get("parameters")}
    complete = len(accepted) == len(MODEL_KEYS) * len(SEEDS)
    result = {
        "schema": "stage6_eight_model_24_cell_v1",
        "status": "COMPLETE_24_OF_24_DESCRIPTIVE" if complete else f"INCOMPLETE_{len(accepted)}_OF_24",
        "evidence_label": EVIDENCE_LABEL,
        "baseline_protocol_label": HISTORICAL_BASELINE_LABEL + " (historical EXT-03 matrix only; this matrix is the controlled replacement)",
        "primary_model": FULL, "cells": cells, "missing_cells": sum(c["status"] == "MISSING" for c in cells),
        "rejected_cells": sum(c["status"] == "REJECTED" for c in cells),
        "per_model": per_model,
        "paired_full_vs_global": _paired(runs_root, accepted, FULL, GLOBAL),
        "paired_lite_vs_full": _paired(runs_root, accepted, LITE, FULL),
        "paired_full_vs_baselines": {b: _paired(runs_root, accepted, FULL, b) for b in BASELINES},
        "superiority_claim_allowed": False,
        "claims_note": "Descriptive VAL808 development comparisons; no inferential or generalization claim.",
    }
    if out is not None:
        out = Path(out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, allow_nan=False, default=_json_default), encoding="utf-8")
    return result
