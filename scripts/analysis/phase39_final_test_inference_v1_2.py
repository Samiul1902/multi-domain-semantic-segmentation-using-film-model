"""Phase39 v1.2 canonical-reuse inference (D99 + inference-contract repair).

Per-sample inference DELEGATES to the frozen canonical Phase36 v1.23 functions
(hash-bound). No independent reimplementation of the learned core.
"""
from __future__ import annotations

import numpy as np

import scripts.analysis.phase39_final_test_common_v1_2 as C


def _p36():
    import scripts.analysis.phase36_robustness_execution_v1_23 as P36
    return P36


# --------------------------------------------------------------------------- #
# D99 — canonical manifest-schema parsing
# --------------------------------------------------------------------------- #
def parse_population_row(row: dict):
    """Return (domain, task_id, ok, reason) using the CANONICAL Phase4-v3 schema.

    Domain source = `dataset`; task source = `task_id`. No outcome-dependent fallback.
    """
    domain = str(row.get(C.DOMAIN_FIELD, "")).strip()
    tid_raw = row.get(C.TASK_FIELD, None)
    if not domain:
        return domain, None, False, f"missing {C.DOMAIN_FIELD}"
    if tid_raw is None or str(tid_raw).strip() == "":
        return domain, None, False, f"missing {C.TASK_FIELD}"
    try:
        task_id = int(tid_raw)
    except (TypeError, ValueError):
        return domain, None, False, f"non-integer {C.TASK_FIELD}={tid_raw!r}"
    if domain not in C.TASKS_REV:
        return domain, task_id, False, f"unknown {C.DOMAIN_FIELD}={domain!r}"
    if task_id not in C.TASKS:
        return domain, task_id, False, f"unknown {C.TASK_FIELD}={task_id}"
    if C.TASKS[task_id] != domain:
        return domain, task_id, False, f"dataset/task_id mismatch: {domain} vs {C.TASKS[task_id]}"
    return domain, task_id, True, "ok"


def validate_population(rows):
    """Canonical-schema validation of the whole population. Returns (ok, errors)."""
    errors = []
    for i, r in enumerate(rows):
        domain, task_id, ok, reason = parse_population_row(r)
        if not ok:
            errors.append({"row": i, "reason": reason})
            if len(errors) >= 20:
                break
    return (len(errors) == 0), errors


# --------------------------------------------------------------------------- #
# Canonical batching (dataset ascending, sample_id ascending; chunks of 8/domain)
# --------------------------------------------------------------------------- #
def canonical_test_batches(rows):
    ordered = sorted(rows, key=lambda r: (str(r.get(C.DOMAIN_FIELD, "")), str(r.get("sample_id", ""))))
    batches = []
    cur, cur_dom = [], None
    for r in ordered:
        d = str(r.get(C.DOMAIN_FIELD, ""))
        if d != cur_dom:
            if cur:
                batches.extend(_chunks(cur))
            cur, cur_dom = [], d
        cur.append(r)
    if cur:
        batches.extend(_chunks(cur))
    return batches


def _chunks(xs, n=8):
    return [xs[i:i + n] for i in range(0, len(xs), n)]


# --------------------------------------------------------------------------- #
# Batched G -> per-sample clean artifacts (canonical functions reused)
# --------------------------------------------------------------------------- #
def generate_g_artifacts(ctx, rows, counters):
    P36 = _p36()
    p_global_store, geom_store, rf202_store = {}, {}, {}
    for batch in canonical_test_batches(rows):
        images = np.stack([np.asarray(P36._load_clean_image_tensor(r).numpy(), dtype=np.float32)
                           for r in batch])
        x = P36.canonical_images_tensor(ctx, images)
        t = P36.canonical_task_ids_tensor(ctx, [int(r[C.TASK_FIELD]) for r in batch])
        out = P36.canonical_g_forward_batched(ctx, x, t)
        counters["clean_g_forwards"] = counters.get("clean_g_forwards", 0) + len(batch)
        counters["clean_g_batch_forwards"] = counters.get("clean_g_batch_forwards", 0) + 1
        for bi, r in enumerate(batch):
            p_global = np.asarray(out["probability"][bi], dtype=np.float32)
            taps = {k: np.asarray(v[bi]) for k, v in out["taps"].items()}
            geom = P36._roi_geometry_from_prob(p_global, C.ROI_P_GLOBAL_THRESHOLD, C.ROI_MARGIN)
            roi_row = (P36._geo_row(geom) if geom is not None
                       else P36._roi_row_from_window(0, p_global.shape[0], 0, p_global.shape[1], p_global.shape[0]))
            rf202 = P36._assemble_202d(taps, p_global, roi_row)
            sid = r["sample_id"]
            p_global_store[sid] = p_global
            geom_store[sid] = geom
            rf202_store[sid] = rf202
    return {"p_global": p_global_store, "geometry": geom_store, "rf202": rf202_store}


# --------------------------------------------------------------------------- #
# Per-sample evaluation (delegates to canonical_learned_core + D75 + metrics)
# --------------------------------------------------------------------------- #
def evaluate_population(ctx, rows, generated, counters, observability):
    P36 = _p36()
    records = []
    obs = observability
    for r in rows:
        sid = r["sample_id"]
        domain, task_id, ok, reason = parse_population_row(r)
        if not ok:
            raise ValueError(f"PHASE39_MANIFEST_ROW_INVALID: {sid}: {reason}")
        p_global = generated["p_global"][sid]
        geom = generated["geometry"][sid]
        rf202 = generated["rf202"][sid]
        obs["test_image_access_started"] = True
        image_t = P36._load_clean_image_tensor(r)
        image_b = image_t[None].to(ctx["device"])
        obs["model_forward_started"] = True
        out = P36.canonical_learned_core(
            ctx, image_b, task_id,
            p_global_override=p_global, g_taps=None,
            router_features_202_override=rf202, roi_window=None,
            action_available=(geom is not None), counters=counters)
        obs["metric_evaluation_started"] = True
        final_prob = np.asarray(out["final_probability"], dtype=np.float32)
        final_binary = P36._phase27_scored_final_binary(final_prob)   # D75/POLICY_B
        gt = P36._load_val_gt(r)
        dice = P36._dice(final_binary, gt)
        iou = P36._iou(final_binary, gt)
        hd = P36._hd95(final_binary, gt)
        counters["metric_evaluations"] = counters.get("metric_evaluations", 0) + 1
        counters["test_image_reads"] = counters.get("test_image_reads", 0) + 1
        counters["test_gt_reads"] = counters.get("test_gt_reads", 0) + 1
        records.append({
            "sample_id": sid, "domain": domain, "task_id": task_id,
            "state_machine_branch": out["state"], "router_decision": out["router_decision"],
            "final_source": P36._final_source_of(out["state"]),
            "roi_available": out["roi_available"],
            "dice": float(dice), "iou": float(iou),
            "hd95": float(hd.get("hd95", np.nan)) if isinstance(hd, dict) else float(hd),
            "hd95_valid": hd.get("valid") if isinstance(hd, dict) else None,
        })
    return records
