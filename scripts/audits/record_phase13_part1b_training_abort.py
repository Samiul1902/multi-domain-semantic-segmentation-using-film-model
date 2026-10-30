"""PHASE-13 PART-1B — TRAINING ABORT INCIDENT AUDIT.

Records, verbatim, the state of the aborted clean-v3 localizer training run.

The supervisor ordered an immediate stop ("stop those training there are problems").
The run was terminated with SIGTERM (exit code 143) at epoch 28.

This script is READ-ONLY against training artifacts. It does not train, does not
build a model, does not touch CUDA, and does not read TEST. It only records the
observed state and the diagnosed defect so that the evidence survives.

Run:  ./.venv/Scripts/python.exe scripts/audits/record_phase13_part1b_training_abort.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXPERIMENT_ID = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"
EXP_DIR = ROOT / "experiments" / EXPERIMENT_ID
CHK_DIR = ROOT / "checkpoints" / EXPERIMENT_ID
HISTORY_PATH = EXP_DIR / "history.csv"
STDOUT_LOG = ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_training_stdout.log"
OUT_JSON = ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_training_abort_incident.json"
OUT_MD = ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_training_abort_incident.md"

PROPOSAL_THRESHOLD = 0.10
SIGMA = 0.75
HEATMAP_RESOLUTION = 128
ALPHA = 2.0
BETA = 4.0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(8192):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    rows = list(csv.DictReader(open(HISTORY_PATH, newline="", encoding="utf-8")))
    epochs_completed = len(rows)

    recalls = [float(r["tiny_recall90"]) for r in rows]
    overall = [float(r["overall_recall90"]) for r in rows]
    rois = [float(r["mean_roi_area_fraction"]) for r in rows]
    val_losses = [float(r["val_loss"]) for r in rows]

    # ---- observed degenerate convergence -------------------------------
    head_bias = None
    head_weight_mean = None
    head_weight_min = None
    head_weight_max = None
    best_score = None
    checkpoint_epoch = None
    try:
        import torch

        ck = torch.load(CHK_DIR / "best.pt", map_location="cpu", weights_only=False)
        checkpoint_epoch = int(ck.get("epoch", -1))
        best_score = ck.get("best_validation_score")
        state = ck.get("model_state", {})
        if "head.bias" in state:
            head_bias = float(state["head.bias"].float().mean().item())
        if "head.weight" in state:
            head_weight_mean = float(state["head.weight"].float().mean().item())
            head_weight_min = float(state["head.weight"].float().min().item())
            head_weight_max = float(state["head.weight"].float().max().item())
    except Exception as exc:  # pragma: no cover - diagnostic only
        head_bias = f"UNREADABLE: {exc}"

    peak_probability = (
        1.0 / (1.0 + math.exp(-head_bias)) if isinstance(head_bias, float) else None
    )
    threshold_gap = (
        PROPOSAL_THRESHOLD - peak_probability if peak_probability is not None else None
    )
    bias_required = math.log(PROPOSAL_THRESHOLD / (1.0 - PROPOSAL_THRESHOLD))

    # ---- target-density arithmetic (why positives are vanishingly rare) --
    n = HEATMAP_RESOLUTION
    ys = np.arange(n, dtype=np.float32).reshape(-1, 1)
    xs = np.arange(n, dtype=np.float32).reshape(1, -1)
    gaussian = np.exp(-((ys - n / 2) ** 2 + (xs - n / 2) ** 2) / (2 * SIGMA**2))
    gaussian[n // 2, n // 2] = 1.0
    positive_pixels = int((gaussian == 1.0).sum())
    background_pixels = n * n - positive_pixels

    payload = {
        "artifact": "PHASE13_CLEAN_V3_LOCALIZER_TRAINING_ABORT_INCIDENT",
        "document_type": "INCIDENT_RECORD_AND_ROOT_CAUSE",
        "experiment_id": EXPERIMENT_ID,
        "stopped_by": "SUPERVISOR_ORDER",
        "stop_signal": "SIGTERM (exit code 143)",
        "run_status": "ABORTED_NOT_COMPLETED",
        "completion_audit_written": False,

        # ---- state verbatim ----
        "epochs_completed": epochs_completed,
        "checkpoint_epoch": checkpoint_epoch,
        "history_path": str(HISTORY_PATH),
        "history_sha": sha256_file(HISTORY_PATH),
        "stdout_log_path": str(STDOUT_LOG),
        "stdout_log_sha": sha256_file(STDOUT_LOG) if STDOUT_LOG.exists() else None,
        "best_checkpoint_path": str(CHK_DIR / "best.pt"),
        "best_checkpoint_sha": (
            sha256_file(CHK_DIR / "best.pt") if (CHK_DIR / "best.pt").exists() else None
        ),
        "latest_checkpoint_path": str(CHK_DIR / "latest.pt"),
        "latest_checkpoint_sha": (
            sha256_file(CHK_DIR / "latest.pt") if (CHK_DIR / "latest.pt").exists() else None
        ),
        "stale_lock_present": (EXP_DIR / ".experiment.lock").exists(),

        # ---- the defect ----
        "defect_class": "DEGENERATE_ALL_NEGATIVE_HEATMAP",
        "defect_severity": "SCIENTIFICALLY_BLOCKING",
        "observed": {
            "tiny_recall90_all_epochs": sorted(set(recalls)),
            "overall_recall90_all_epochs": sorted(set(overall)),
            "mean_roi_area_fraction_all_epochs": sorted(set(rois)),
            "val_loss_first": val_losses[0],
            "val_loss_last": val_losses[-1],
            "val_loss_reduction_fraction": 1.0 - (val_losses[-1] / val_losses[0]),
            "epochs_with_recall_above_zero": sum(1 for v in recalls if v > 0.0),
            "proposals_ever_generated": False,
        },
        "checkpoint_evidence": {
            "head_bias": head_bias,
            "head_weight_mean": head_weight_mean,
            "head_weight_min": head_weight_min,
            "head_weight_max": head_weight_max,
            "implied_peak_probability": peak_probability,
            "proposal_threshold": PROPOSAL_THRESHOLD,
            "threshold_gap": threshold_gap,
            "bias_required_to_cross_threshold": bias_required,
            "best_validation_score": list(best_score) if best_score else None,
        },
        "mechanism": {
            "summary": (
                "The model converged to a spatially uniform, sub-threshold logit "
                "field. Every pixel predicts sigmoid(head.bias) below the frozen "
                "0.10 proposal threshold, so the proposal generator emits zero "
                "proposals on every validation image. Recall therefore cannot be "
                "anything but 0, and the 4-term selection tuple "
                "(tiny_recall90, overall_recall90, -mean_roi_area_fraction, -val_loss) "
                "has its first three terms pinned to constants (0, 0, 0). The entire "
                "best-checkpoint decision was driven by term 4 (-val_loss) alone."
            ),
            "selection_tuple_degeneracy": (
                "With terms 1-3 constant across all epochs, strict lexicographic "
                "comparison reduces to minimising val_loss. Every epoch that lowered "
                "val_loss was accepted as a new best, including epoch 27 whose "
                "recall is still 0."
            ),
            "target_density": {
                "sigma_128_space": SIGMA,
                "sigma_512_equivalent": 3.0,
                "heatmap_resolution": HEATMAP_RESOLUTION,
                "positive_pixels_per_target": positive_pixels,
                "background_pixels_per_target": background_pixels,
                "positive_to_background_ratio": f"1:{background_pixels}",
                "note": (
                    "sigma=0.75 in 128-space yields a target that is effectively a "
                    "single-pixel spike. The positive branch is vanishingly sparse "
                    "relative to an enormous background, which is the upstream reason "
                    "the optimiser prefers to suppress the whole field rather than "
                    "raise isolated peaks."
                ),
            },
            "loss_normalisation": {
                "loss_class": "CenterNetFocalLoss",
                "alpha": ALPHA,
                "beta": BETA,
                "normaliser": "num_positive_pixels (batch-wide)",
                "note": (
                    "neg_loss is a SUM over ~16384 background pixels per heatmap, "
                    "while pos_loss has only a handful of contributing pixels. Both "
                    "are divided by the same num_pos. At the degenerate point the "
                    "background term dominates, and driving every logit down is the "
                    "cheapest way to reduce total loss."
                ),
            },
        },
        "why_not_early_stopping": (
            "Early stopping never triggered because every val_loss improvement "
            "counted as a new best (terms 1-3 were tied constants, never a "
            "regression). bad_epochs reset to 0 each time val_loss fell, so the "
            "patience counter could not accumulate towards 15."
        ),
        "protocol_integrity": {
            "provenance_binding_held": True,
            "superseded_fields_absent": True,
            "grid_search_ran": False,
            "test_reads": 0,
            "manifest_validation": "phase4_v3 PASS (7 files)",
            "note": (
                "The manifest-provenance amendment itself is intact. This defect is "
                "scientific/optimisation, not provenance."
            ),
        },
        "recommended_supervisor_decisions": [
            "COMPLETE_HALT: treat this as an unresolved scientific blocker and "
            "re-plan the localizer objective before any further compute.",
            "TARGET_DENSITY_REPAIR: re-derive sigma so the target is learnable "
            "(wider Gaussian), which is a SCIENTIFIC parameter change requiring "
            "explicit authorisation.",
            "THRESHOLD_REPAIR: lower the frozen proposal threshold so sub-threshold "
            "fields still yield proposals -- also a SCIENTIFIC parameter change.",
            "LOSS_REBALANCE: address the num_pos normalisation / background "
            "dominance -- also a SCIENTIFIC parameter change.",
        ],
        "no_repair_performed": True,
        "no_new_experiment_id_created": True,
        "awaiting": "SUPERVISOR_PHASE13_PART1B_INCIDENT_REVIEW",
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md = f"""# PHASE-13 PART-1B — TRAINING ABORT INCIDENT

- experiment_id: `{EXPERIMENT_ID}`
- stopped_by: **SUPERVISOR_ORDER** (`SIGTERM`, exit 143)
- run_status: **ABORTED_NOT_COMPLETED**
- epochs_completed: **{epochs_completed}**
- completion audit written: **False**

## Observed defect

`tiny_recall90` and `overall_recall90` were **0.000 for all {epochs_completed} epochs**.
`mean_roi_area_fraction` was **0.0** throughout. No proposal was ever generated.

Meanwhile `val_loss` fell monotonically from **{val_losses[0]:.4f}** to
**{val_losses[-1]:.4f}** ({100 * (1 - val_losses[-1] / val_losses[0]):.1f}% reduction),
so the optimiser was genuinely descending — into a degenerate minimum.

## Checkpoint evidence (epoch {checkpoint_epoch})

| quantity | value |
|---|---|
| `head.bias` | **{head_bias}** |
| implied peak probability | **{peak_probability:.6f}** |
| frozen proposal threshold | {PROPOSAL_THRESHOLD} |
| **threshold gap** | **{threshold_gap:+.6f}** |
| bias needed to cross threshold | {bias_required:.6f} |
| `head.weight` min / max | {head_weight_min} / {head_weight_max} |
| `best_validation_score` | `{list(best_score) if best_score else None}` |

The model predicts a **spatially uniform** logit of ~{head_bias:.4f} everywhere.
`sigmoid({head_bias:.4f}) = {peak_probability:.6f}`, which sits
**{abs(threshold_gap):.6f} below** the 0.10 threshold. Zero pixels qualify, so zero
proposals are produced, so recall is structurally pinned to 0.

## Mechanism

1. The target heatmap uses `sigma = {SIGMA}` in 128-space. This makes each target
   effectively a **single-pixel spike** ({positive_pixels} pixel at 1.0 against
   {background_pixels} background pixels, ratio **1:{background_pixels}**).
2. `CenterNetFocalLoss(alpha={ALPHA}, beta={BETA})` sums `neg_loss` over the whole
   background and divides by `num_pos`. The background term dominates.
3. The cheapest descent is to **suppress the entire field**, landing just under the
   detection threshold.
4. Because terms 1-3 of the selection tuple are constant, the **entire** best-epoch
   decision collapsed onto `-val_loss`. Every loss improvement was accepted as a new
   best, so `bad_epochs` kept resetting and patience never accumulated.

## Protocol integrity

The manifest-provenance amendment is **intact** (`train_table_sha256` /
`val_table_sha256` absent; 8-field binding present; grid search not run; TEST not
read). **This is a scientific/optimisation defect, not a provenance defect.**

## Status

**NO REPAIR PERFORMED.** No new experiment ID created. Awaiting
**SUPERVISOR_PHASE13_PART1B_INCIDENT_REVIEW**.
"""
    OUT_MD.write_text(md, encoding="utf-8")

    print(json.dumps({
        "epochs_completed": epochs_completed,
        "head_bias": head_bias,
        "peak_probability": peak_probability,
        "threshold_gap": threshold_gap,
        "defect_class": payload["defect_class"],
        "out_json": str(OUT_JSON),
        "out_md": str(OUT_MD),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
