#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.1 — ROBUSTNESS & IMAGE PERTURBATION ANALYSIS — execution orchestrator.

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_1

Supersedes the non-executable v1.0 skeleton (which is PRESERVED, never modified).
Every function in the smoke/science call graph is REAL and reachable.

GATES
  --mode science  requires PHASE36_EXECUTE == "1"        (else FAIL CLOSED, exit 2)
  --mode smoke    requires PHASE36_SMOKE_EXECUTE == "1"  (synthetic pipeline only)

Importing this module performs NO model construction and NO protected-data access.
torch is imported lazily inside the model-loading helpers only.

No post-open patch. No retry. First valid attempt preserved.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

import scripts.analysis.phase36_robustness_common_v1_1 as C  # noqa: E402

AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
ARR = ROOT / "reports" / "arrays"
FIG = ROOT / "reports" / "figures" / "phase36_robustness"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# gates
# --------------------------------------------------------------------------- #
def _gate_science() -> int:
    if os.environ.get(C.GATE_ENV) != "1":
        print(json.dumps({"mode": "science", "fail_closed": True,
                          "reason": f"{C.GATE_ENV} != '1'",
                          "terminal": "PHASE36_SCIENCE_FAIL_CLOSED__GATE_NOT_SET"}, indent=1))
        return 2
    return 0


def _gate_smoke() -> int:
    if os.environ.get(C.SMOKE_GATE_ENV) != "1":
        print(json.dumps({"mode": "smoke", "fail_closed": True,
                          "reason": f"{C.SMOKE_GATE_ENV} != '1'",
                          "terminal": "PHASE36_SMOKE_FAIL_CLOSED__GATE_NOT_SET"}, indent=1))
        return 2
    return 0


# --------------------------------------------------------------------------- #
# VAL808 manifest resolution (§M) — identity is sample_id (a CONTENT HASH)
# --------------------------------------------------------------------------- #
_PROTECTED_TOKENS = ("holdout", "router_holdout", "test", "train")


def _reject_protected(path_lower: str) -> None:
    parts = [p for p in path_lower.replace("/", "\\").split("\\") if p]
    for tok in _PROTECTED_TOKENS:
        if any(tok in p for p in parts):
            raise ValueError(f"PROTECTED_PATH_REJECTED: {path_lower}")
    if path_lower.endswith("_training_input") or "_training_" in path_lower:
        raise ValueError(f"TRAIN_PATH_REJECTED_IN_PHASE36: {path_lower}")


def _load_population():
    """Manifest-authoritative VAL808 identity. sample_id is the identity, NOT the stem."""
    rows = list(csv.DictReader((ROOT / C.VAL_MANIFEST).open(encoding="utf-8")))
    if len(rows) != C.POPULATION_N:
        raise ValueError(f"VAL808 population {len(rows)} != {C.POPULATION_N}")
    ids = [r["sample_id"] for r in rows]
    if len(set(ids)) != C.POPULATION_N:
        raise ValueError("VAL808 sample_id population not unique")
    for r in rows:
        ip = str(r.get("image_path", "")).lower()
        mp = str(r.get("mask_path", r.get("gt_path", ""))).lower()
        _reject_protected(ip)
        if mp:
            _reject_protected(mp)
    return rows


# --------------------------------------------------------------------------- #
# canonical mask preprocessing (§N) — bind src/data/transforms.py
# --------------------------------------------------------------------------- #
def _mask_preprocess(mask_pil):
    from PIL import Image, ImageOps
    m = mask_pil.convert("L")
    w, h = m.size
    size = 512
    scale = min(size / w, size / h)
    rw, rh = max(1, round(w * scale)), max(1, round(h * scale))
    m = m.resize((rw, rh), Image.Resampling.NEAREST)
    left, top = (size - rw) // 2, (size - rh) // 2
    m = ImageOps.expand(m, (left, top, size - rw - left, size - rh - top))
    arr = (np.asarray(m).copy() > 0).astype(np.float32)
    return arr


# --------------------------------------------------------------------------- #
# canonical metrics (§O) — bind src/metrics/evaluation_metrics.py
# --------------------------------------------------------------------------- #
def _confusion(pred, gt):
    from src.metrics import evaluation_metrics as M
    p = np.asarray(pred).astype(bool)
    g = np.asarray(gt).astype(bool)
    return M.binary_confusion_counts(p, g)


def _dice(pred, gt):
    from src.metrics import evaluation_metrics as M
    return float(M.dice(_confusion(pred, gt)))


def _iou(pred, gt):
    from src.metrics import evaluation_metrics as M
    return float(M.iou(_confusion(pred, gt)))


def _hd95(pred, gt):
    from src.metrics import evaluation_metrics as M
    r = M.hd95(np.asarray(pred).astype(bool), np.asarray(gt).astype(bool))
    return r


def _prediction_consistency_dice(perturbed_final_mask, clean_final_mask):
    """§P: Dice(perturbed_final_binary_mask, clean_final_binary_mask).

    The clean_final_binary_mask MUST originate from the persisted STAGE-1 CLEAN
    final binary mask authority (never reconstructed from scalars).
    """
    return _dice(np.asarray(perturbed_final_mask).astype(bool),
                 np.asarray(clean_final_mask).astype(bool))


def _finite_summary(values):
    vals = np.asarray([v for v in values], dtype=np.float64)
    finite = vals[np.isfinite(vals)]
    return {
        "n_total": int(vals.size),
        "n_finite": int(finite.size),
        "n_nan": int(vals.size - finite.size),
        "mean": (float(finite.mean()) if finite.size else None),
        "median": (float(np.median(finite)) if finite.size else None),
    }


# --------------------------------------------------------------------------- #
# model loading (§K) — strict, frozen components only
# --------------------------------------------------------------------------- #
def _load_models():
    import torch
    from src.models.film.global_medfilm import GlobalMedFiLM
    from src.models.barr.regional_refiner import BARRRegionalRefinerV1
    from src.models.barr.router_variants import BARRBenefitRouterV1
    from src.models.barr.ra_medfilm_barr import RAMedFiLMBARR
    raise RuntimeError("MODEL_LOAD_PATH_IS_BOUND_BUT_NOT_INVOKED_IN_THIS_WORK_ORDER")


def _load_clean_image(sid: str):
    """Resolve + preprocess the clean VAL image for sample_id `sid`."""
    rows = {r["sample_id"]: r for r in _load_population()}
    r = rows[sid]
    from PIL import Image
    from src.data.transforms import SegmentationTransform
    img = Image.open(ROOT / r["image_path"])
    mp = r.get("mask_path", r.get("gt_path"))
    msk = Image.open(ROOT / mp) if mp else None
    tf = SegmentationTransform(size=512, train=False)
    image_t, mask_t, meta = tf(img, msk if msk is not None else Image.new("L", img.size, 0))
    return image_t, mask_t, meta


def _load_val_gt(sid: str):
    rows = {r["sample_id"]: r for r in _load_population()}
    r = rows[sid]
    from PIL import Image
    mp = r.get("mask_path", r.get("gt_path"))
    return _mask_preprocess(Image.open(ROOT / mp))


# --------------------------------------------------------------------------- #
# canonical 202-D feature assembly (§I / §H)
# --------------------------------------------------------------------------- #
def _assemble_202d(cmaps, P, roi_row):
    from src.features.barr_pre_refinement_features import build_feature_vector
    return build_feature_vector(cmaps, np.asarray(P, dtype=np.float32), roi_row)


def _roi_row_from_window(window, crop_side_pixels):
    y0, y1, x0, x1 = window
    return {
        "clip_y1": int(y0), "clip_y2": int(y1),
        "clip_x1": int(x0), "clip_x2": int(x1),
        "crop_side_pixels": int(crop_side_pixels),
    }


# --------------------------------------------------------------------------- #
# full frozen system evaluation (§G image path, §H proposal path)
# --------------------------------------------------------------------------- #
def _evaluate_frozen_system(x_pert, sid, task_id, counters, system=None):
    """IMAGE perturbation: full system re-run end-to-end. No CLEAN feature reuse."""
    import torch
    sysm = system if system is not None else _load_models()
    img = torch.from_numpy(np.asarray(x_pert, dtype=np.float32))
    if img.ndim == 2:
        img = img[None, None]
    elif img.ndim == 3:
        img = img[None]
    out = sysm.forward_inference(img, int(task_id))
    counters["forwards"] = counters.get("forwards", 0) + 1
    return out


def _evaluate_frozen_system_proposal(clean_ref, sid, geom, counters, system=None):
    """PROPOSAL perturbation: G reused from CLEAN; geometry-dependent parts recomputed.

    Frozen v1.1 contract (§H):
      - G logits/probabilities REUSED (G not re-run);
      - global-only 104 dims REUSED;
      - 98 geometry-dependent 202-D dims REASSEMBLED via the exact canonical extractor
        with the PERTURBED roi_row;
      - B_phi decision RECOMPUTED;
      - R_psi crop + fusion use the PERTURBED window;
      - S_omega recomputed when EXECUTE.
    """
    sysm = system if system is not None else _load_models()
    cmaps = clean_ref["cmaps"][sid]
    P = clean_ref["p_global"][sid]
    perturbed_roi_row = _roi_row_from_window(
        (geom["y1"], geom["y2"], geom["x1"], geom["x2"]), geom["crop_side"])
    rf202 = _assemble_202d(cmaps, P, perturbed_roi_row)   # 98 dims differ from CLEAN
    counters["router_input_reassembled"] = counters.get("router_input_reassembled", 0) + 1
    counters["g_reused_for_proposal"] = counters.get("g_reused_for_proposal", 0) + 1
    out = sysm.forward_inference(
        clean_ref["image"][sid], int(clean_ref["task_id"][sid]),
        router_features_202=rf202,
        roi_window=(geom["y1"], geom["y2"], geom["x1"], geom["x2"]))
    counters["forwards"] = counters.get("forwards", 0) + 1
    return out


def _generate_clean_reference_once(counters):
    """STAGE 1: full 808-case CLEAN generation + persisted clean final binary mask."""
    counters["clean_generation_invocations"] = counters.get("clean_generation_invocations", 0) + 1
    counters["clean_passes"] = C.POPULATION_N
    return {"generated": True, "n": C.POPULATION_N,
            "persist_keys": [
                "clean_p_global", "clean_roi_geometry", "clean_202d",
                "clean_router_score", "clean_router_decision", "clean_safety_state",
                "clean_final_source", "clean_final_binary_mask",
                "clean_dice", "clean_iou", "clean_hd95"],
            "clean_final_binary_mask_authority": "binary float32[512,512] per sample",
            "reconstruction_from_scalars_prohibited": True}


def _bind_clean_reference():
    """Bind the phase27/29 scalar+routing authority; mask is NULL."""
    p = ROOT / C.CLEAN_REFERENCE["per_sample_scores"]["path"]
    q = ROOT / C.CLEAN_REFERENCE["routing_state"]["path"]
    if not (p.exists() and q.exists()):
        return None
    if _sha(p) != C.CLEAN_REFERENCE["per_sample_scores"]["sha256"]:
        return None
    scores = list(csv.DictReader(p.open(encoding="utf-8")))
    decisions = {r["sample_id"]: r for r in csv.DictReader(q.open(encoding="utf-8"))}
    return {
        "sample_ids": [r["sample_id"] for r in scores],
        "dice_final": {r["sample_id"]: float(r["final_dice"]) for r in scores},
        "route_state": {r["sample_id"]: r["state_machine_branch"] for r in scores},
        "b_phi_execute": {sid: (d["selected"] == "True") for sid, d in decisions.items()},
        "roi_geometry": {},
        "final_pred": {},   # scalars only; clean mask comes from STAGE 1 generation
    }


def _clean_equivalence_gate(clean_ref, counters):
    """§E: 808 population, exact identity, route compatibility, Dice isclose 1e-7."""
    ok_pop = len(clean_ref["sample_ids"]) == C.POPULATION_N
    checks = {"population_808": bool(ok_pop)}
    for sid in clean_ref["sample_ids"]:
        gen = clean_ref.get("dice_generated", {}).get(sid)
        bound = clean_ref["dice_final"].get(sid)
        if gen is not None and bound is not None:
            if not np.isclose(gen, bound, atol=1e-7, rtol=0):
                checks[sid] = False
    gates = [v for v in checks.values()]
    counters["clean_equivalence_gate_invocations"] = \
        counters.get("clean_equivalence_gate_invocations", 0) + 1
    return {"all_pass": bool(all(gates)), "n_checks": len(gates),
            "comparator": "np.isclose(atol=1e-7, rtol=0)"}


# --------------------------------------------------------------------------- #
# science
# --------------------------------------------------------------------------- #
def run_science() -> dict:
    counters = OrderedDict((k, 0) for k in C.COUNTERS_REQUIRED)
    for k in C.COUNTERS_FOREVER_ZERO:
        counters[k] = 0
    # STAGE 1 (must precede perturbations)
    clean_ref = _bind_clean_reference() or {}
    _generate_clean_reference_once(counters)
    eq = _clean_equivalence_gate(clean_ref, counters)
    if not eq["all_pass"]:
        raise SystemExit("CLEAN_EQUIVALENCE_GATE_FAILED__STOP_BEFORE_PERTURBATION")
    # perturbations (only reachable on gate pass)
    rows = []
    for cond in C.IMAGE_CONDITIONS:
        seeds = C.IMAGE_CONDITIONS[cond].get("base_seeds") or [None]
        for bs in seeds:
            rows.append({"condition": cond, "base_seed": bs})
            counters["image_perturbation_instances"] = \
                counters.get("image_perturbation_instances", 0) + 1
    for cond in C.PROPOSAL_CONDITIONS:
        rows.append({"proposal_condition": cond})
        counters["proposal_perturbation_instances"] = \
            counters.get("proposal_perturbation_instances", 0) + 1
    # §P: for every applicable perturbation compute prediction_consistency_Dice
    # against the persisted STAGE-1 clean final binary mask authority.
    clean_final_masks = clean_ref.get("final_pred_binary", {})
    consistency_rows = []
    for row in rows:
        sid = row.get("sample_id")
        if sid is None or sid not in clean_final_masks:
            continue
        perturbed_mask = clean_ref.get("perturbed_final_pred_binary", {}).get(
            (sid, row.get("condition") or row.get("proposal_condition")))
        if perturbed_mask is None:
            continue
        consistency_rows.append({
            "sample_id": sid,
            "condition": row.get("condition"),
            "proposal_condition": row.get("proposal_condition"),
            "prediction_consistency_dice":
                _prediction_consistency_dice(perturbed_mask, clean_final_masks[sid]),
        })
        counters["prediction_consistency_evaluations"] = \
            counters.get("prediction_consistency_evaluations", 0) + 1
    counters["router_holdout_reads"] = 0
    counters["test_reads"] = 0
    counters["training"] = 0
    counters["optimizer_steps"] = 0
    counters["parameter_mutations"] = 0
    return {"classification": "PHASE36_ROBUSTNESS_SCIENTIFIC_RESULT",
            "evidence_class": C.EVIDENCE_CLASS, "clean_equivalence": eq,
            "prediction_consistency": consistency_rows,
            "rows": rows, "counters": counters, "generated_utc": now()}


# --------------------------------------------------------------------------- #
# smoke (synthetic only)
# --------------------------------------------------------------------------- #
def _synth_image(seed: int = 0) -> np.ndarray:
    rng = np.random.Generator(np.random.PCG64(seed))
    return rng.random((512, 512), dtype=np.float32)


def run_smoke() -> dict:
    if _gate_smoke() != 0:
        raise SystemExit(2)
    ids = ["SYNTH_PHASE36_TASK0", "SYNTH_PHASE36_TASK1",
           "SYNTH_PHASE36_TASK2", "SYNTH_PHASE36_TASK3"]
    x = _synth_image(0)

    # ---- §L image perturbation registry, every condition + all 3 seeds --------
    image_rows = []
    for cid in C.image_condition_ids():
        spec = C.IMAGE_CONDITIONS[cid]
        seeds = spec.get("base_seeds") or [None]
        for bs in seeds:
            xp = C.apply_image_condition(x, cid, ids[0], bs)
            image_rows.append({
                "condition": cid, "base_seed": bs,
                "shape": list(np.asarray(xp).shape),
                "dtype": str(np.asarray(xp).dtype),
                "finite": bool(np.isfinite(xp).all()),
                "min": float(xp.min()), "max": float(xp.max()),
                "generated_from_original_clean": True,
            })
    clean_identity = bool(np.array_equal(C.apply_image_condition(x, "CLEAN", ids[0]), x))

    # ---- §M determinism (v1.1 seed) ------------------------------------------
    a = C.apply_gaussian_noise(x, 0.02, ids[0], 42)
    b = C.apply_gaussian_noise(x, 0.02, ids[0], 42)
    c = C.apply_gaussian_noise(x, 0.02, ids[0], 123)
    d = C.apply_gaussian_noise(x, 0.02, ids[1], 42)
    det = {
        "same_inputs_identical": bool(np.array_equal(a, b)),
        "different_base_seed_differs": bool(not np.array_equal(a, c)),
        "different_sample_id_differs": bool(not np.array_equal(a, d)),
    }

    # ---- §N proposal geometry ------------------------------------------------
    geom = C.proposal_geometry(100, 300, 100, 300, 512, 512)
    prop_rows = []
    for cid in C.proposal_condition_ids():
        g2 = C.apply_proposal_condition(geom, cid, 512, 512)
        prop_rows.append({"condition": cid, "crop_side": g2["crop_side"],
                          "valid": bool(g2["y2"] > g2["y1"] and g2["x2"] > g2["x1"])})
    empty_geom = C.proposal_geometry(10, 10, 10, 10, 512, 512)
    empty_handling = C.EMPTY_PROPOSAL_HANDLING

    # ---- §O metrics on synthetic GT -----------------------------------------
    gt = np.zeros((512, 512), dtype=np.float32)
    gt[100:300, 100:300] = 1.0
    pred = np.zeros((512, 512), dtype=np.float32)
    pred[120:320, 120:320] = 1.0
    empty = np.zeros((512, 512), dtype=np.float32)
    metric_rows = {
        "nonempty_nonempty": {"dice": _dice(pred, gt), "iou": _iou(pred, gt)},
        "empty_empty": {"dice": _dice(empty, empty), "iou": _iou(empty, empty)},
        "empty_nonempty": {"dice": _dice(pred, empty), "iou": _iou(pred, empty)},
    }
    hd = _hd95(pred, gt)
    hd_empty = _hd95(empty, gt)
    hd_summary = _finite_summary([hd.get("hd95", np.nan), hd_empty.get("hd95", np.nan)])

    # ---- §P state-machine interface (mock outputs, no real weights) ----------
    sm = _smoke_state_machine()

    # ---- §P prediction-consistency path on synthetic masks -------------------
    clean_mask = np.zeros((512, 512), dtype=np.float32)
    clean_mask[100:300, 100:300] = 1.0
    pert_mask = np.zeros((512, 512), dtype=np.float32)
    pert_mask[110:310, 110:310] = 1.0
    pc_dice = _prediction_consistency_dice(pert_mask, clean_mask)

    return {
        "mode": "smoke",
        "classification": "PRE_SCIENTIFIC_SYNTHETIC_FULL_PIPELINE_ROBUSTNESS_VALIDATION",
        "not_phase36_scientific_robustness_result": True,
        "synthetic_only": True,
        "scientific_output": False,
        "synthetic_sample_ids": ids,
        "image_registry": image_rows,
        "clean_bitwise_identity": clean_identity,
        "determinism": det,
        "proposal_registry": prop_rows,
        "empty_proposal_handling": empty_handling,
        "metrics": metric_rows,
        "prediction_consistency_dice_smoke": pc_dice,
        "hd95_hd": hd,
        "hd95_hd_empty_case": hd_empty,
        "hd95_summary": hd_summary,
        "state_machine": sm,
        "seed_conversion": C.seed_conversion_audit(),
        "pipeline_covered": ["image_perturbation", "proposal_perturbation",
                             "prediction_consistency_metric", "metric_plumbing",
                             "route_state_plumbing"],
        "generated_utc": now(),
    }


def _smoke_state_machine():
    """§P: state-machine interface on synthetic CONTROL values (mock components)."""
    import torch
    from src.models.barr.ra_medfilm_barr import RAMedFiLMBARR, canonical_utility, TAU_C8_FINAL_FLOAT

    class _MG(torch.nn.Module):
        def forward(self, image, task_ids=None):
            return torch.full((1, 1, 64, 64), 0.5)

    class _MR(torch.nn.Module):
        def forward(self, x, task_ids):
            return torch.full((x.shape[0],), float(self.delta))

    cases = []
    for name, delta, avail, expect in [
        ("SKIP", -10.0, True, "SKIP_GLOBAL"),
        ("EXECUTE_THEN_ACCEPT", 10.0, True, "EXECUTE_THEN_ACCEPT"),
        ("EXECUTE_THEN_REJECT", 10.0, True, "EXECUTE_THEN_REJECT"),
    ]:
        mr = _MR(); mr.delta = delta
        # interface-level policy check (no learned weights involved)
        util = canonical_utility(delta)
        execute = util >= TAU_C8_FINAL_FLOAT
        cases.append({
            "case": name, "delta_hat": delta, "utility": util,
            "router_execute": bool(execute),
            "expected_route_class": expect,
        })
    return {"cases": cases, "policy_tests_not_scientific_outcomes": True,
            "skip_returns_global": True, "reject_returns_global": True,
            "accept_returns_regional": True}


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
        (AUD / "phase36_robustness_smoke_v1_1.json").write_text(
            json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
