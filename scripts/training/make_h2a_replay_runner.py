"""Generate the H2-A-B1 replay runner from the frozen Phase-13 runner.

The replay runner is the Phase-13 runner with a CONFINED diff:
  * experiment identity / config path            (provenance)
  * H2A protocol binding gate replaces the Phase-13 R2C runner-SHA gate (provenance)
  * selection module import + select_epoch call  (SCIENTIFIC: the authorized axis)
  * per-epoch PROPOSAL_PIXEL_ANY_HIT_PRECISION + score diagnostics (evaluation-only, no gradient effect)
  * history row additions                        (reporting)

NO gradient-update code is modified: loss, optimizer, scheduler, AMP, data, augmentation,
seeding, batching and the training loop body are byte-identical.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
SRC = ROOT / "scripts" / "training" / "train_phase13_clean_v3_localizer.py"
DST = ROOT / "scripts" / "training" / "post_phase13_h2a_localizer_replay.py"

H2A_ID = "post_phase13_h2a_kub_localizer_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3"

src_raw = SRC.read_bytes()
crlf = src_raw.count(b"\r\n")
nl = "\r\n" if crlf else "\n"
s = src_raw.decode("utf-8")


def rep(old: str, new: str, label: str) -> None:
    global s
    old_n = old.replace("\n", nl)
    new_n = new.replace("\n", nl)
    if old_n not in s:
        raise SystemExit(f"ANCHOR NOT FOUND [{label}]")
    if s.count(old_n) != 1:
        raise SystemExit(f"ANCHOR NOT UNIQUE [{label}] count={s.count(old_n)}")
    s = s.replace(old_n, new_n)
    print(f"  applied [{label}]")


# ---- A. header note -------------------------------------------------------
rep(
    '"""Clean-v3 safe training runner for the Phase-13 KUB localizer.',
    '"""Clean-v3 safe training runner for the POST-PHASE-13 H2-A-B1 localizer replay.\n'
    '\n'
    'H2-A-B1 = DETERMINISTIC TRAINING REPLAY WITH DEPLOYMENT-BALANCED CHECKPOINT SELECTION.\n'
    'This file is the frozen Phase-13 clean-v3 runner with a CONFINED diff:\n'
    '  * experiment identity / config path                                   (provenance)\n'
    '  * H2A protocol binding gate replaces the Phase-13 R2C runner-SHA gate (provenance)\n'
    '  * selection module import + select_epoch call        (SCIENTIFIC: the ONE authorized axis)\n'
    '  * per-epoch PROPOSAL_PIXEL_ANY_HIT_PRECISION + score diagnostics (evaluation-only)\n'
    '  * history row additions                                               (reporting)\n'
    'NO gradient-update code is modified: loss, optimizer, scheduler, AMP, data, augmentation,\n'
    'seeding, batching and the training-loop body are IDENTICAL to the Phase-13 runner.\n'
    '\n'
    'Original module docstring follows.\n'
    '\n'
    'Clean-v3 safe training runner for the Phase-13 KUB localizer.',
    "header",
)

# ---- B/C. experiment id + config path -------------------------------------
rep(
    'EXPERIMENT_ID = (\n    "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"',
    'EXPERIMENT_ID = (\n    "post_phase13_h2a_kub_localizer_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3"',
    "experiment_id",
)

# ---- D. H2A protocol binding constants -----------------------------------
rep(
    'R2_PROTOCOL_SHA = "ab451e03366c589fae5c303ebf1382e086f4f115b97768eb36d491256a3b5e53"',
    'R2_PROTOCOL_SHA = "ab451e03366c589fae5c303ebf1382e086f4f115b97768eb36d491256a3b5e53"\n'
    '\n'
    '# ---- H2-A-B1 protocol binding (the governing frozen artifact for this run) ----\n'
    'H2A_PROTOCOL_PATH = (\n'
    '    ROOT / "reports" / "audits" / "post_phase13_h2a_protocol_frozen.json"\n'
    ')\n'
    'H2A_PROTOCOL_SHA = "0fafc793b3a814e010e1fdd48f6a2333042985eaef4a44e0382b3991800da96b"\n'
    'H2A_PROTOCOL_REQUIRED_STATUS = "SUPERVISOR_FROZEN_H2A_SELECTION_ONLY_READY_FOR_EXECUTION"\n'
    'H2A_SCORE_PATH_AUDIT_PATH = (\n'
    '    ROOT / "reports" / "audits" / "post_phase13_h2a_localizer_score_path_audit.json"\n'
    ')\n'
    'H2A_SCORE_PATH_AUDIT_SHA = "3d9fea04ba8ca8b603314bd72f84ce2176ad33c5cc0bfed8f5b6dae1e64bec99"\n'
    'H2A_SCORE_PATH_REQUIRED_VERDICT = "SCORE_PATH_IMPLEMENTATION_VALID"',
    "h2a constants",
)

# ---- E. selection import --------------------------------------------------
rep(
    "    from src.training.clean_v3_selection import DIAGNOSTIC_TERM_NAMES, select_epoch",
    "    from src.training.h2a_deployment_balance_selection import (\n"
    "        DIAGNOSTIC_TERM_NAMES,\n"
    "        deployment_balance_hmean,\n"
    "        select_epoch,\n"
    "    )",
    "selection import",
)

# ---- F. SELECTION_TERM_NAMES import --------------------------------------
rep(
    "            from src.training.clean_v3_selection import SELECTION_TERM_NAMES",
    "            from src.training.h2a_deployment_balance_selection import SELECTION_TERM_NAMES",
    "term-names import",
)

# ---- G. R2C gate -> H2A protocol gate -----------------------------------
rep(
    """        r2c = load_r2c_amendment(runner_sha)
        r2c_amendment_sha = r2c["sha"]
        if not r2c["authorized"]:
            raise RuntimeError(
                "R2C coverage-semantics amendment is missing or does not bind the "
                f"executing runner (reason={r2c.get('reason')}, "
                f"checks={r2c.get('checks')}). STOP."
            )""",
    """        r2c = load_r2c_amendment(runner_sha)
        r2c_amendment_sha = r2c["sha"]
        # ---- H2-A-B1 PROVENANCE GATE ------------------------------------------
        # The Phase-13 R2C gate binds the PHASE-13 runner file SHA, so it cannot
        # bind this replay runner. It is therefore retained as PROVENANCE ONLY
        # (r2c_amendment_sha is still recorded), and the GOVERNING binding for
        # this run is the frozen H2A protocol artifact. This is a provenance
        # re-pointing with NO gradient or scientific-semantics effect.
        if not H2A_PROTOCOL_PATH.exists():
            raise RuntimeError(f"H2A protocol artifact missing: {H2A_PROTOCOL_PATH}")
        if sha256_file(H2A_PROTOCOL_PATH) != H2A_PROTOCOL_SHA:
            raise RuntimeError(
                "H2A protocol SHA mismatch: expected "
                f"{H2A_PROTOCOL_SHA}, got {sha256_file(H2A_PROTOCOL_PATH)}. STOP."
            )
        h2a_protocol = json.loads(H2A_PROTOCOL_PATH.read_text(encoding="utf-8"))
        if h2a_protocol.get("status") != H2A_PROTOCOL_REQUIRED_STATUS:
            raise RuntimeError(
                f"H2A protocol status is {h2a_protocol.get('status')!r}, required "
                f"{H2A_PROTOCOL_REQUIRED_STATUS!r}. STOP."
            )
        if h2a_protocol.get("experiment_id") != EXPERIMENT_ID:
            raise RuntimeError(
                f"H2A protocol experiment_id {h2a_protocol.get('experiment_id')!r} != "
                f"{EXPERIMENT_ID!r}. STOP."
            )
        if not H2A_SCORE_PATH_AUDIT_PATH.exists():
            raise RuntimeError(f"H2A score-path audit missing: {H2A_SCORE_PATH_AUDIT_PATH}")
        if sha256_file(H2A_SCORE_PATH_AUDIT_PATH) != H2A_SCORE_PATH_AUDIT_SHA:
            raise RuntimeError("H2A score-path audit SHA mismatch. STOP.")
        h2a_score_audit = json.loads(H2A_SCORE_PATH_AUDIT_PATH.read_text(encoding="utf-8"))
        if h2a_score_audit.get("verdict") != H2A_SCORE_PATH_REQUIRED_VERDICT:
            raise RuntimeError(
                f"H2A score-path verdict is {h2a_score_audit.get('verdict')!r}, required "
                f"{H2A_SCORE_PATH_REQUIRED_VERDICT!r}. STOP."
            )""",
    "h2a gate",
)

# ---- H. config selection tuple ------------------------------------------
rep(
    """                "checkpoint_selection_tuple": [
                    "tiny_recall90",
                    "overall_recall90",
                    "-mean_roi_area_fraction",
                    "-val_loss",
                ],""",
    """                "checkpoint_selection_tuple": [
                    "DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90",
                    "tiny_recall90",
                    "overall_recall90",
                    "PROPOSAL_PIXEL_ANY_HIT_PRECISION",
                    "-mean_roi_area_fraction",
                    "-val_loss",
                ],""",
    "config selection tuple",
)

# ---- I. evaluation counters --------------------------------------------
rep(
    """    component_rows = []       # PRIMARY: historical bbox coverage
    pixel_component_rows = []  # SECONDARY: pixel-mask sensitivity
    covered_samples = set()""",
    """    component_rows = []       # PRIMARY: historical bbox coverage
    pixel_component_rows = []  # SECONDARY: pixel-mask sensitivity
    covered_samples = set()
    # H2A: PROPOSAL_PIXEL_ANY_HIT_PRECISION accounting (primary new quantity).
    proposal_pixel_hit_count = 0
    proposal_total_count = 0
    proposal_bbox_hit_count = 0
    score_hit_pairs = []  # (score, pixel_any_hit) per generated proposal""",
    "eval counters",
)

# ---- J. per-case P accounting ------------------------------------------
rep(
    """                # PRIMARY (R2C): explicit historical bbox coverage.
                bbox_rows = evaluate_historical_bbox_coverage(proposals, components)""",
    """                # ---- H2A: PROPOSAL_PIXEL_ANY_HIT_PRECISION -------------------
                # Proposals were generated GT-FREE above; GT is consulted ONLY now.
                gt_union = np.zeros(original_shape, dtype=bool)
                gt_boxes = []
                for _component in components:
                    _cmask = _component.get("mask")
                    if _cmask is not None:
                        gt_union |= np.asarray(_cmask, dtype=bool)
                    gt_boxes.append((
                        int(_component["min_y"]), int(_component["min_x"]),
                        int(_component["max_y"]), int(_component["max_x"]),
                    ))
                for _proposal in proposals:
                    _geom = _proposal["crop_geometry"]
                    _cy1, _cy2 = int(_geom["clip_y1"]), int(_geom["clip_y2"])
                    _cx1, _cx2 = int(_geom["clip_x1"]), int(_geom["clip_x2"])
                    _hit = bool(gt_union[_cy1:_cy2, _cx1:_cx2].any())
                    proposal_total_count += 1
                    if _hit:
                        proposal_pixel_hit_count += 1
                    _py1, _px1, _py2, _px2 = (int(v) for v in _proposal["proposal_bbox"])
                    if any(not (_py2 < _by1 or _py1 > _by2 or _px2 < _bx1 or _px1 > _bx2)
                           for (_by1, _bx1, _by2, _bx2) in gt_boxes):
                        proposal_bbox_hit_count += 1
                    score_hit_pairs.append((float(_proposal["score"]), _hit))

                # PRIMARY (R2C): explicit historical bbox coverage.
                bbox_rows = evaluate_historical_bbox_coverage(proposals, components)""",
    "per-case P accounting",
)

rep(
    """    from src.inference.clean_v3_metrics import (
        aggregate_clean_v3_metrics,
        multi_component_ids,
    )""",
    """    from src.inference.clean_v3_metrics import (
        aggregate_clean_v3_metrics,
        multi_component_ids,
    )
    # H2A: this module-level function needs its own binding (main()'s lazy import
    # is not in scope here).
    from src.training.h2a_deployment_balance_selection import deployment_balance_hmean""",
    "eval local import",
)

# ---- K. H2A metrics assembly ------------------------------------------
rep(
    """    metrics["coverage_semantics_primary"] = BBOX_SEMANTICS
    metrics["coverage_semantics_secondary"] = PIXEL_SEMANTICS
    metrics["component_contract"] = component_contract
    metrics["covered_samples"] = len(covered_samples)
    return float(total_val_loss / n_batches), metrics""",
    """    metrics["coverage_semantics_primary"] = BBOX_SEMANTICS
    metrics["coverage_semantics_secondary"] = PIXEL_SEMANTICS
    metrics["component_contract"] = component_contract
    metrics["covered_samples"] = len(covered_samples)

    # ---- H2A: PROPOSAL_PIXEL_ANY_HIT_PRECISION + score diagnostics ----------
    metrics["proposal_pixel_hit_count"] = int(proposal_pixel_hit_count)
    metrics["proposal_total_count"] = int(proposal_total_count)
    metrics["proposal_pixel_any_hit_precision"] = (
        float(proposal_pixel_hit_count) / float(proposal_total_count)
        if proposal_total_count > 0 else 0.0
    )
    metrics["proposal_bbox_any_hit_precision"] = (
        float(proposal_bbox_hit_count) / float(proposal_total_count)
        if proposal_total_count > 0 else 0.0
    )
    metrics["proposal_count_per_image"] = (
        float(proposal_total_count) / float(EXPECTED_VAL_CASES)
    )
    _scores = np.asarray([p[0] for p in score_hit_pairs], dtype=float)
    _hits = np.asarray([1 if p[1] else 0 for p in score_hit_pairs], dtype=int)
    if _scores.size:
        _max = float(_scores.max())
        metrics["proposal_score_mean"] = float(_scores.mean())
        metrics["proposal_score_median"] = float(np.median(_scores))
        metrics["proposal_score_q25"] = float(np.percentile(_scores, 25))
        metrics["proposal_score_q75"] = float(np.percentile(_scores, 75))
        metrics["proposal_score_max"] = _max
        metrics["proposal_score_iqr"] = float(
            np.percentile(_scores, 75) - np.percentile(_scores, 25)
        )
        metrics["fraction_proposals_exactly_at_epoch_max_score"] = float(
            np.mean(_scores >= _max - 1e-12)
        )
        metrics["hit_proposal_score_mean"] = (
            float(_scores[_hits == 1].mean()) if int(_hits.sum()) else float("nan")
        )
        metrics["miss_proposal_score_mean"] = (
            float(_scores[_hits == 0].mean()) if int((_hits == 0).sum()) else float("nan")
        )
        metrics["proposal_roc_auc_score_to_pixel_any_hit"] = _roc_auc(_scores, _hits)
        metrics["proposal_pr_auc_score_to_pixel_any_hit"] = _pr_auc(_scores, _hits)
    else:
        for _name in ("proposal_score_mean", "proposal_score_median", "proposal_score_q25",
                      "proposal_score_q75", "proposal_score_max", "proposal_score_iqr",
                      "fraction_proposals_exactly_at_epoch_max_score",
                      "hit_proposal_score_mean", "miss_proposal_score_mean",
                      "proposal_roc_auc_score_to_pixel_any_hit",
                      "proposal_pr_auc_score_to_pixel_any_hit"):
            metrics[_name] = float("nan")
    metrics["deployment_balance_hmean"] = deployment_balance_hmean(
        metrics["proposal_pixel_any_hit_precision"],
        metrics["tiny_recall90"],
        metrics["overall_recall90"],
    )
    return float(total_val_loss / n_batches), metrics""",
    "h2a metrics",
)

# ---- L. select_epoch call ----------------------------------------------
rep(
    """            # 4. 4-term score
            outcome = select_epoch(
                tiny_recall90=metrics["tiny_recall90"],
                overall_recall90=metrics["overall_recall90"],
                mean_roi_area_fraction=metrics["mean_roi_area_fraction"],
                val_loss=val_loss,""",
    """            # 4. H2-A-B1 6-term deployment-balanced score
            outcome = select_epoch(
                deployment_balance_hmean=metrics["deployment_balance_hmean"],
                tiny_recall90=metrics["tiny_recall90"],
                overall_recall90=metrics["overall_recall90"],
                proposal_pixel_any_hit_precision=metrics["proposal_pixel_any_hit_precision"],
                mean_roi_area_fraction=metrics["mean_roi_area_fraction"],
                val_loss=val_loss,""",
    "select_epoch call",
)

# ---- M. history row additions ------------------------------------------
rep(
    """                "tiny_recall90": metrics["tiny_recall90"],
                "overall_recall90": metrics["overall_recall90"],
                "mean_roi_area_fraction": metrics["mean_roi_area_fraction"],
                **outcome.as_row_fields(),
            }""",
    """                "tiny_recall90": metrics["tiny_recall90"],
                "overall_recall90": metrics["overall_recall90"],
                "mean_roi_area_fraction": metrics["mean_roi_area_fraction"],
                # H2A primary precision term (independently auditable counts).
                "proposal_pixel_hit_count": metrics["proposal_pixel_hit_count"],
                "proposal_total_count": metrics["proposal_total_count"],
                "proposal_pixel_any_hit_precision": metrics["proposal_pixel_any_hit_precision"],
                "proposal_bbox_any_hit_precision": metrics["proposal_bbox_any_hit_precision"],
                "deployment_balance_hmean": metrics["deployment_balance_hmean"],
                "proposal_count_per_image": metrics["proposal_count_per_image"],
                "proposal_score_mean": metrics["proposal_score_mean"],
                "proposal_score_median": metrics["proposal_score_median"],
                "proposal_score_q25": metrics["proposal_score_q25"],
                "proposal_score_q75": metrics["proposal_score_q75"],
                "proposal_score_max": metrics["proposal_score_max"],
                "proposal_score_iqr": metrics["proposal_score_iqr"],
                "fraction_proposals_exactly_at_epoch_max_score": metrics[
                    "fraction_proposals_exactly_at_epoch_max_score"
                ],
                "hit_proposal_score_mean": metrics["hit_proposal_score_mean"],
                "miss_proposal_score_mean": metrics["miss_proposal_score_mean"],
                "proposal_roc_auc_score_to_pixel_any_hit": metrics[
                    "proposal_roc_auc_score_to_pixel_any_hit"
                ],
                "proposal_pr_auc_score_to_pixel_any_hit": metrics[
                    "proposal_pr_auc_score_to_pixel_any_hit"
                ],
                **outcome.as_row_fields(),
            }""",
    "history row",
)

# ---- N. AUC helpers (module level, inserted before main) ---------------
rep(
    "def main(argv=None) -> int:",
    '''def _roc_auc(scores, hits) -> float:
    """ROC-AUC of score -> binary hit, tie-aware. Diagnostic only."""
    import numpy as np

    scores = np.asarray(scores, dtype=float)
    hits = np.asarray(hits, dtype=int)
    n1 = int(hits.sum()); n0 = int(len(hits) - n1)
    if n0 == 0 or n1 == 0:
        return float("nan")
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=float)
    ranks[order] = np.arange(1, len(scores) + 1)
    import pandas as pd

    ranks = pd.Series(ranks).groupby(pd.Series(scores)).transform("mean").to_numpy()
    return float((ranks[hits == 1].sum() - n1 * (n1 + 1) / 2) / (n0 * n1))


def _pr_auc(scores, hits) -> float:
    """PR-AUC (trapezoidal) of score -> binary hit. Diagnostic only."""
    import numpy as np

    scores = np.asarray(scores, dtype=float)
    hits = np.asarray(hits, dtype=int)
    order = np.argsort(-scores, kind="mergesort")
    ys = hits[order]
    tp = np.cumsum(ys)
    fp = np.cumsum(1 - ys)
    precision = tp / np.maximum(tp + fp, 1)
    recall = tp / max(int(tp[-1]), 1)
    trap = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    return float(trap(precision, recall))


def main(argv=None) -> int:''',
    "auc helpers",
)

DST.write_bytes(s.encode("utf-8"))
print("wrote", DST)
print("newline style:", "CRLF" if crlf else "LF")
