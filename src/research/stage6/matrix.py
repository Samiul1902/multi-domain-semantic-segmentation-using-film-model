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
import re
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
                            "producer": "src/research/stage6/baseline_real.py (run_real_baseline; CLI stage6_eight_model.py baseline-run)",
                            "multi_seed_producer": "BLOCKED: no baseline launch grant exists (STAGE6_BASELINE_LAUNCH_GRANT_REQUIRED)"}

REAL_EVIDENCE_CLASS = "REAL_VAL808_DEVELOPMENT"
SYNTHETIC_EVIDENCE_CLASS = "SYNTHETIC_TEST_ONLY"
VAL_MANIFEST = ROOT / "manifests" / "phase4_v3" / "val.csv"
# Frozen C1 recipe fields that every controlled single-network cell (G and the five baselines) must share.
EXPECTED_TRAINING_PROTOCOL: dict[str, Any] = {
    "resolution": 512, "channel_policy": "RGB_3CH", "loss": "bce_dice", "bce_weight": 0.5, "dice_weight": 0.5,
    "dice_epsilon": 1e-6, "optimizer": "AdamW", "learning_rate": 1e-4, "weight_decay": 1e-4,
    "scheduler": "CosineAnnealingLR", "T_max": 100, "train_batch_size": 4, "eval_batch_size": 8,
    "max_epochs": 100, "early_stop_patience": 15, "amp": True,
    "sampling_policy": "phase20_domain_balanced_uniform_v1", "threshold": 0.5,
    "selection_rule": "phase20_macro_domain_mean_dice_v1", "tie_break": "lower_val_loss_then_earlier_epoch"}
CONTROLLED_SINGLE_NETWORK = (GLOBAL, *BASELINES)
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
    ckpt, export = c1_manifest.get("checkpoint_sha256"), c1_manifest.get("per_image_export_sha256")
    if not export:
        reasons.append("missing per-image VAL808 export")
    elif not re.fullmatch(r"[0-9a-f]{64}", str(export)) or export == ckpt:
        reasons.append("per_image_export_sha256 must be the SHA-256 of the per-image export file, not the checkpoint hash")
    if ckpt and not re.fullmatch(r"[0-9a-f]{64}", str(ckpt)):
        reasons.append("checkpoint_sha256 is not a SHA-256 digest")
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


_FLOAT_COLUMNS = ("dice", "global_dice", "delta_dice_vs_global", "iou", "precision", "recall")
C1_EXPORT_NAME = "c1t_per_image_export.csv"


def _read_per_image(path: Path) -> dict[str, dict[str, Any]]:
    with Path(path).open(newline="", encoding="utf-8") as f:
        rows = {}
        for row in csv.DictReader(f):
            for key in _FLOAT_COLUMNS:
                if key in row:
                    try:
                        row[key] = float(row[key])
                    except (TypeError, ValueError):
                        row[key] = float("nan")
            rows[row["sample_id"]] = row
    return rows


def recompute_domain_dice(rows: Mapping[str, Mapping[str, Any]]) -> tuple[dict[str, float], float]:
    """Per-domain mean Dice and equal-domain macro-Dice recomputed from per-image rows."""
    per_domain = {d: float(np.mean([r["dice"] for r in rows.values() if r["domain"] == d])) for d in DOMAINS}
    return per_domain, float(np.mean(list(per_domain.values())))


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
    if prov.get("model_key") != model_key:
        reasons.append("provenance model identity mismatch")
    if prov.get("evidence_class") != REAL_EVIDENCE_CLASS:
        reasons.append(f"evidence_class must be {REAL_EVIDENCE_CLASS}")
    if not re.fullmatch(r"[0-9a-f]{64}", str(prov.get("checkpoint_sha256", ""))):
        reasons.append("checkpoint_sha256 is not a SHA-256 digest")
    if model_key in CONTROLLED_SINGLE_NETWORK:
        protocol = prov.get("training_protocol") or {}
        bad = sorted(k for k, v in EXPECTED_TRAINING_PROTOCOL.items() if protocol.get(k) != v)
        if bad:
            reasons.append(f"training protocol incompatible with frozen recipe: {bad}")
        if not prov.get("evaluation_configuration"):
            reasons.append("evaluation_configuration missing")
    per_image = directory / "per_image.csv"
    if not per_image.is_file() or hashlib.sha256(per_image.read_bytes()).hexdigest() != doc.get("per_image_sha256"):
        reasons.append("per-image export missing or hash mismatch")
    else:
        rows = _read_per_image(per_image)
        roster = _roster_reasons(rows)
        reasons.extend(roster)
        if not roster:
            reasons.extend(_recompute_reasons(rows, doc.get("summary", {}).get("per_domain"),
                                              doc.get("summary", {}).get("equal_domain_macro_dice")))
    if model_key == GLOBAL:
        reasons.extend(_c1_reuse_reasons(directory, prov))
    ckpt_path = prov.get("checkpoint_path")
    if ckpt_path is not None:
        ckpt_file = Path(ckpt_path) if Path(ckpt_path).is_absolute() else ROOT / ckpt_path
        if not ckpt_file.is_file():
            reasons.append("checkpoint file missing")
        elif hashlib.sha256(ckpt_file.read_bytes()).hexdigest() != prov.get("checkpoint_sha256"):
            reasons.append("checkpoint file SHA-256 mismatch")
    elif model_key in CONTROLLED_SINGLE_NETWORK:
        reasons.append("checkpoint_path missing")
    summary = doc.get("summary", {})
    macro = summary.get("equal_domain_macro_dice")
    if not isinstance(macro, (int, float)) or not math.isfinite(macro) or not 0.0 <= macro <= 1.0:
        reasons.append("summary equal_domain_macro_dice missing or non-finite")
    if not isinstance(summary.get("parameters"), int) or summary["parameters"] <= 0:
        reasons.append("summary parameters missing")
    return (None if reasons else doc), reasons


def _roster_reasons(rows: Mapping[str, Mapping[str, Any]]) -> list[str]:
    """Roster, task-ID and finiteness checks against the frozen VAL808 manifest (metadata only)."""
    import pandas as pd

    expected = pd.read_csv(VAL_MANIFEST, usecols=["sample_id", "dataset", "task_id"])
    truth = {str(r.sample_id): (str(r.dataset), int(r.task_id)) for r in expected.itertuples()}
    reasons: list[str] = []
    if set(rows) != set(truth):
        reasons.append(f"per-image roster differs from VAL808 (missing {len(set(truth) - set(rows))}, "
                       f"unexpected {len(set(rows) - set(truth))})")
        return reasons
    if any(rows[s]["domain"] != truth[s][0] for s in rows):
        reasons.append("per-image domain does not match VAL808 manifest")
    if any(int(rows[s].get("task_id", -1)) != truth[s][1] or TASK_IDS.get(rows[s]["domain"]) != truth[s][1] for s in rows):
        reasons.append("per-image task_id does not match domain/task mapping")
    present = [k for k in ("dice", "global_dice") if all(k in r for r in rows.values())]
    if "dice" not in present or not all(math.isfinite(rows[s][k]) and 0.0 <= rows[s][k] <= 1.0 + 1e-9
                                        for s in rows for k in present) or not all(
            math.isfinite(float(rows[s][k])) for s in rows for k in ("iou", "precision", "recall")):
        reasons.append("non-finite per-image metrics")
    return reasons


def _recompute_reasons(rows: Mapping[str, Mapping[str, Any]], per_domain: Mapping[str, Any] | None,
                       macro: Any, *, tol: float = 1e-9) -> list[str]:
    """Reported per-domain and equal-domain macro-Dice must equal values recomputed from the per-image export."""
    got_domain, got_macro = recompute_domain_dice(rows)
    reasons = []
    if not isinstance(macro, (int, float)) or abs(got_macro - macro) > tol:
        reasons.append(f"equal_domain_macro_dice {macro!r} != recomputed {got_macro!r}")
    for d in DOMAINS:
        reported = (per_domain or {}).get(d, {})
        reported = reported.get("dice") if isinstance(reported, Mapping) else reported
        if not isinstance(reported, (int, float)) or abs(got_domain[d] - reported) > tol:
            reasons.append(f"per-domain Dice for {d} {reported!r} != recomputed {got_domain[d]!r}")
    return reasons


def _c1_reuse_reasons(directory: Path, prov: Mapping[str, Any]) -> list[str]:
    """GLOBAL cells must carry a verifiable C1-T per-image export whose hash is not the checkpoint hash."""
    if prov.get("reused_artifact") != "C1-T":
        return ["GLOBAL_MEDFILM controlled cell must derive from a validated C1-T run"]
    export_hash, ckpt_hash = prov.get("per_image_export_sha256"), prov.get("checkpoint_sha256")
    path = Path(directory) / C1_EXPORT_NAME
    if not re.fullmatch(r"[0-9a-f]{64}", str(export_hash)) or export_hash == ckpt_hash:
        return ["per_image_export_sha256 missing, malformed, or equal to the checkpoint hash"]
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != export_hash:
        return ["C1-T per-image export missing or hash mismatch"]
    rows = _read_per_image(path)
    reasons = [f"C1-T export: {r}" for r in _roster_reasons({k: {**v, "task_id": TASK_IDS.get(v.get("domain"), -1)}
                                                              for k, v in rows.items()})]
    if not reasons:
        reasons += [f"C1-T export: {r}" for r in _recompute_reasons(
            rows, prov.get("c1_selected_epoch_val_dice"), prov.get("c1_selected_epoch_macro_dice"), tol=1e-6)]
    return reasons


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
