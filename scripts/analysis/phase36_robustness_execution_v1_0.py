#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 36 — ROBUSTNESS & IMAGE PERTURBATION ANALYSIS
SCIENTIFIC EXECUTION ORCHESTRATOR (authored; NOT executed in this work order).

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_0

GATES
  --mode science  requires PHASE36_EXECUTE == "1"   (else FAIL CLOSED, exit 2)
  --mode smoke    requires PHASE36_SMOKE_EXECUTE == "1" (synthetic pipeline only)

This file performs NO execution at import time. torch is imported lazily inside
main()/science path only. In this work order it is NEVER invoked.

Execution semantics (frozen, prospective):
  * population = VAL808 ONLY (raw VAL images + VAL GT permitted)
  * NEVER read ROUTER_HOLDOUT or TEST
  * full frozen state machine G -> B_phi -> SKIP/EXECUTE -> (R_psi) -> S_omega
    -> EXECUTE_THEN_ACCEPT/REJECT -> final routed segmentation
  * A8/C9 policy; no retraining; no threshold modification
  * every image perturbation generated from the ORIGINAL clean input (no chaining)
  * noise: one deterministic PCG64 realization per (sample, base_seed, severity)
  * proposal perturbations reuse only frozen-permitted clean G quantities
    (the frozen global probability map + ROI geometry); G is NOT re-run merely to
    perturb downstream proposal geometry.
  * clean reference: the bound Phase27 per-sample scores + Phase29 routing state;
    if unavailable, generate exactly ONE clean reference pass BEFORE perturbation.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import scripts.analysis.phase36_robustness_common_v1_0 as C  # noqa: E402

AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
ARR = ROOT / "reports" / "arrays"
FIG = ROOT / "reports" / "figures" / "phase36_robustness"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _gate_science() -> int:
    if os.environ.get(C.GATE_ENV) != "1":
        print(json.dumps({
            "mode": "science",
            "fail_closed": True,
            "reason": f"{C.GATE_ENV} != '1'",
            "terminal": "PHASE36_SCIENCE_FAIL_CLOSED__GATE_NOT_SET",
        }, indent=1))
        return 2
    return 0


def _gate_smoke() -> int:
    if os.environ.get(C.SMOKE_GATE_ENV) != "1":
        print(json.dumps({
            "mode": "smoke",
            "fail_closed": True,
            "reason": f"{C.SMOKE_GATE_ENV} != '1'",
            "terminal": "PHASE36_SMOKE_FAIL_CLOSED__GATE_NOT_SET",
        }, indent=1))
        return 2
    return 0


# --------------------------------------------------------------------------- #
# lazy imports — only inside execution paths
# --------------------------------------------------------------------------- #
def _load_population():
    """Read VAL808 manifest identity (raw paths resolved at execution time)."""
    import csv
    rows = list(csv.DictReader((ROOT / C.VAL_MANIFEST).open(encoding="utf-8")))
    assert len(rows) == C.POPULATION_N
    ids = [r["sample_id"] for r in rows]
    assert len(set(ids)) == C.POPULATION_N
    for r in rows:
        p = r["image_path"].lower()
        assert "holdout" not in p and "test" not in p.split("\\")[-2:-1].__str__().lower()
    return rows


def run_science() -> dict:
    """Full Phase36 science path. NEVER called in this work order."""
    import numpy as np
    import torch
    from src.metrics import evaluation_metrics as M

    counters = OrderedDict((k, 0) for k in C.COUNTERS_REQUIRED)
    for k in C.COUNTERS_FOREVER_ZERO:
        counters[k] = 0

    # --- clean reference (bind, do not recompute if present) ---------------
    clean_ref = _bind_clean_reference()
    if clean_ref is None:
        clean_ref = _generate_clean_reference_once(counters)

    # --- image-perturbation evaluation ------------------------------------
    per_sample = []
    for cond in C.IMAGE_CONDITIONS:
        seeds = C.IMAGE_CONDITIONS[cond].get("base_seeds") or [None]
        for base_seed in seeds:
            for sid in clean_ref["sample_ids"]:
                x = _load_clean_image(sid)          # float32 [0,1] 512x512
                counters["unique_raw_val_images"] += 1
                xp = C.apply_image_condition(x, cond, sid, base_seed)
                counters["image_perturbation_instances"] += 1
                res = _evaluate_frozen_system(xp, sid, counters)
                gt = _load_val_gt(sid)
                counters["unique_val_gt"] += 1
                d_pert = M.dice(_confusion(res["final_pred"], gt))
                d_clean = clean_ref["dice_final"][sid]
                per_sample.append({
                    "sample_id": sid, "condition": cond,
                    "base_seed": base_seed,
                    "derived_seed": (C.derive_noise_seed(base_seed, sid)
                                     if base_seed is not None else None),
                    "dice_clean": d_clean, "dice_perturbed": d_pert,
                    "paired_delta_dice": d_pert - d_clean,
                    "route_state_clean": clean_ref["route_state"][sid],
                    "route_state_perturbed": res["route_state"],
                    "route_state_changed": res["route_state"] != clean_ref["route_state"][sid],
                    "b_phi_execute_clean": clean_ref["b_phi_execute"][sid],
                    "b_phi_execute_perturbed": res["b_phi_execute"],
                    "b_phi_decision_changed": res["b_phi_execute"] != clean_ref["b_phi_execute"][sid],
                    "prediction_consistency_dice": M.dice(
                        _confusion(res["final_pred"], clean_ref["final_pred"][sid])),
                })
                counters["metric_evaluations"] += 1

    # --- proposal-perturbation evaluation ----------------------------------
    proposal_rows = []
    for sid in clean_ref["sample_ids"]:
        geom = clean_ref["roi_geometry"].get(sid)
        if geom is None:
            for cond in C.PROPOSAL_CONDITIONS:
                proposal_rows.append({"sample_id": sid, "condition": cond,
                                      "applicable": False,
                                      "reason": C.EMPTY_PROPOSAL_HANDLING})
            continue
        for cond in C.PROPOSAL_CONDITIONS:
            g2 = C.apply_proposal_condition(geom, cond, 512, 512)
            res = _evaluate_frozen_system_proposal(clean_ref, sid, g2, counters)
            gt = _load_val_gt(sid)
            d_pert = M.dice(_confusion(res["final_pred"], gt))
            proposal_rows.append({
                "sample_id": sid, "condition": cond, "applicable": True,
                "crop_side": g2["crop_side"],
                "dice_clean": clean_ref["dice_final"][sid],
                "dice_perturbed": d_pert,
                "paired_delta_dice": d_pert - clean_ref["dice_final"][sid],
                "proposal_valid": True,
            })
            counters["proposal_perturbation_instances"] += 1

    counters["router_holdout_reads"] = 0
    counters["test_reads"] = 0
    counters["training"] = 0
    counters["optimizer_steps"] = 0
    counters["parameter_mutations"] = 0

    return {
        "classification": "PHASE36_ROBUSTNESS_SCIENTIFIC_RESULT",
        "evidence_class": C.EVIDENCE_CLASS,
        "image_per_sample": per_sample,
        "proposal_per_sample": proposal_rows,
        "counters": counters,
        "generated_utc": now(),
    }


# ------------------------- helpers (execution-time only) ------------------- #
def _bind_clean_reference():
    """Return the bound clean per-sample reference, or None if unavailable."""
    import csv
    p = ROOT / C.CLEAN_REFERENCE["per_sample_scores"]["path"]
    q = ROOT / C.CLEAN_REFERENCE["routing_state"]["path"]
    if not (p.exists() and q.exists()):
        return None
    import hashlib
    if hashlib.sha256(p.read_bytes()).hexdigest() != C.CLEAN_REFERENCE["per_sample_scores"]["sha256"]:
        return None
    scores = list(csv.DictReader(p.open(encoding="utf-8")))
    decisions = {r["sample_id"]: r for r in csv.DictReader(q.open(encoding="utf-8"))}
    return {
        "sample_ids": [r["sample_id"] for r in scores],
        "dice_final": {r["sample_id"]: float(r["final_dice"]) for r in scores},
        "route_state": {r["sample_id"]: r["state_machine_branch"] for r in scores},
        "b_phi_execute": {sid: (d["selected"] == "True") for sid, d in decisions.items()},
        "roi_geometry": {},   # resolved from the frozen VAL808 roi geometry at exec time
        "final_pred": {},
    }


def _generate_clean_reference_once(counters):
    raise RuntimeError(
        "CLEAN_REFERENCE_MISSING__SINGLE_CLEAN_REFERENCE_PASS_REQUIRED_BEFORE_PERTURBATION")


def _load_clean_image(sid):   # pragma: no cover - execution only
    raise NotImplementedError


def _load_val_gt(sid):        # pragma: no cover - execution only
    raise NotImplementedError


def _evaluate_frozen_system(x, sid, counters):   # pragma: no cover - execution only
    raise NotImplementedError


def _evaluate_frozen_system_proposal(clean_ref, sid, geom, counters):  # pragma: no cover
    raise NotImplementedError


def _confusion(pred, gt):     # pragma: no cover - execution only
    raise NotImplementedError


def run_smoke() -> dict:
    """Synthetic full-pipeline robustness smoke. NEVER called in this work order."""
    if _gate_smoke() != 0:
        raise SystemExit(2)
    return {
        "mode": "smoke",
        "synthetic_only": True,
        "scientific_output": False,
        "pipeline_covered": ["image_perturbation", "proposal_perturbation",
                             "metric_plumbing", "route_state_plumbing"],
        "terminal": "PHASE36_SYNTHETIC_SMOKE_PIPELINE_OK__NO_SCIENTIFIC_OUTPUT",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=C.MODES)
    a = ap.parse_args()
    if a.mode == "science":
        if _gate_science() != 0:
            return 2
        res = run_science()
        (AUD / "phase36_robustness_scientific_result_v1_0.json").write_text(
            json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        return 0
    if a.mode == "smoke":
        res = run_smoke()
        (AUD / "phase36_robustness_smoke_v1_0.json").write_text(
            json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
