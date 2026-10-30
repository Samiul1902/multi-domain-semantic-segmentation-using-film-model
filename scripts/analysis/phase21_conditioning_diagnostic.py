"""Phase 21 — task-conditioning diagnostic + FiLM parameter sanity.

Two questions, both answered on PERSISTED artifacts and the frozen 64-case
gallery (no new canonical VAL pass, no TEST):

1. Does the conditioning actually DO anything? Re-run inference on the frozen 64
   gallery cases with the CORRECT task ID and with each INCORRECT task ID, and
   measure the per-image Dice change. This is a *diagnostic*, not a tuned
   evaluation: the canonical VAL result is never recomputed or replaced.
2. What did FiLM learn? For every task and every FiLM site, summarise gamma/beta
   (mean / std / min / max / L2 norm over channels).

If the measured conditioning effect is small the artifact is explicitly flagged
``CONDITIONING_EFFECT_WEAK`` — reported honestly, never hidden.

Writes
------
reports/tables/phase21_task_conditioning_diagnostic.csv
reports/tables/phase21_task_conditioning_per_case.csv
reports/tables/phase21_film_parameter_summary.csv
reports/audits/phase21_task_conditioning_diagnostic.json

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/phase21_conditioning_diagnostic.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.training.phase21_common import (  # noqa: E402
    CKPT_DIR,
    CONFIG,
    EXPERIMENT_ID,
    EXP_DIR,
    MANIFEST_DIR,
    sha256_file,
)
from src.data.multidomain_dataset import MultiDomainDataset, harmonized_collate
from src.data.loaders import create_loader
from src.metrics.evaluation_metrics import segmentation_metrics
from src.models.film import GlobalMedFiLM
from src.utils.device import get_device
from src.utils.test_lock import verify_test_lock

TABLE_DIR = ROOT / "reports" / "tables"
AUDIT_DIR = ROOT / "reports" / "audits"
TASK_NAMES = {0: "ISIC", 1: "BUSI", 2: "KVASIR", 3: "KUB"}
WEAK_THRESHOLD = 0.005  # mean |Dice change| below this => CONDITIONING_EFFECT_WEAK


def main() -> int:
    verify_test_lock(str(ROOT))
    closure = json.loads((EXP_DIR / "phase21_training_closure.json").read_text(encoding="utf-8"))
    best_path = CKPT_DIR / "best.pt"
    best_sha = sha256_file(best_path)
    assert best_sha == closure["best_checkpoint_sha256"], "best.pt SHA mismatch"

    device = get_device(require_cuda=True)
    ck = torch.load(best_path, map_location=device, weights_only=False)
    model = GlobalMedFiLM(
        task_count=CONFIG["model"]["task_count"],
        in_channels=CONFIG["model"]["in_channels"],
        out_channels=CONFIG["model"]["out_channels"],
        channels=tuple(CONFIG["model"]["channels"]),
        task_embedding_dim=CONFIG["model"]["task_embedding_dim"],
        film_hidden_dim=CONFIG["model"]["film_hidden_dim"],
    ).to(device)
    model.load_state_dict(ck["model_state"])
    model.eval()

    # ---------- 1. FiLM parameter summary (task x site) -------------------- #
    film_rows = []
    with torch.no_grad():
        for tid in range(4):
            params = model.film_parameters_for_tasks(torch.tensor([tid], device=device))
            for site, (gamma, beta) in params.items():
                g = gamma[0].float().cpu().numpy()
                b = beta[0].float().cpu().numpy()
                for kind, v in (("gamma", g), ("beta", b)):
                    film_rows.append({
                        "task_id": tid, "task": TASK_NAMES[tid], "film_site": site,
                        "parameter": kind, "n_channels": int(v.size),
                        "mean": float(v.mean()), "std": float(v.std()),
                        "min": float(v.min()), "max": float(v.max()),
                        "l2_norm": float(np.linalg.norm(v)),
                        "mean_abs": float(np.abs(v).mean()),
                    })
    film_df = pd.DataFrame(film_rows)
    film_df.to_csv(TABLE_DIR / "phase21_film_parameter_summary.csv", index=False)

    # ---------- 2. conditioning diagnostic on the frozen 64 gallery cases -- #
    gallery = pd.read_csv(TABLE_DIR / "phase21_gallery_selection_64.csv")
    gallery_ids = set(gallery["sample_id"].astype(str))

    ds_val = MultiDomainDataset(MANIFEST_DIR / "val.csv", "VAL",
                                size=CONFIG["input_resolution"], train=False,
                                channel_policy=CONFIG["input_channel_policy"])
    keep = [i for i in range(len(ds_val)) if str(ds_val[i].sample_id) in gallery_ids]
    assert len(keep) == 64, f"gallery selection resolved to {len(keep)} cases, expected 64"
    subset = torch.utils.data.Subset(ds_val, keep)
    loader = create_loader(subset, batch_size=8, shuffle=False, seed=42, num_workers=2,
                           collate_fn=harmonized_collate)

    per_case = []
    with torch.no_grad():
        for batch in loader:
            images = batch["image"].to(device, non_blocking=True)
            masks = batch["mask"].to(device, non_blocking=True)
            true_ids = batch["task_id"].to(device, non_blocking=True)
            sample_ids = batch["sample_id"]
            datasets = batch["dataset"]
            with torch.amp.autocast(device_type=device.type, enabled=True):
                logits_correct = model(images, true_ids)
            probs = torch.sigmoid(logits_correct.float()).cpu().numpy()
            preds = (probs >= 0.5).astype(np.uint8)

            # All four task IDs are evaluated for every batch so each case can be
            # compared against every INCORRECT task (cheap: 4 extra forwards/batch).
            alt_logits = {}
            for alt in range(4):
                with torch.amp.autocast(device_type=device.type, enabled=True):
                    alt_logits[alt] = model(images, torch.full_like(true_ids, alt))

            for i, sid in enumerate(sample_ids):
                gt = (masks[i, 0].cpu().numpy() > 0)
                true_tid = int(true_ids[i])
                d_correct = float(segmentation_metrics(preds[i, 0], gt)["dice"])
                rec = {"sample_id": str(sid), "dataset": str(datasets[i]),
                       "true_task_id": true_tid, "true_task": TASK_NAMES[true_tid],
                       "dice_correct_task": d_correct}
                drops = []
                for alt in range(4):
                    if alt == true_tid:
                        continue
                    ap = torch.sigmoid(alt_logits[alt][i].float()).cpu().numpy()
                    apred = (ap[0] >= 0.5).astype(np.uint8)
                    d_alt = float(segmentation_metrics(apred, gt)["dice"])
                    rec[f"dice_task_{TASK_NAMES[alt]}"] = d_alt
                    rec[f"delta_dice_{TASK_NAMES[alt]}"] = d_correct - d_alt
                    drops.append(d_correct - d_alt)
                rec["mean_abs_delta_dice_wrong_task"] = float(np.mean(np.abs(drops)))
                rec["max_abs_delta_dice_wrong_task"] = float(np.max(np.abs(drops)))
                per_case.append(rec)

    per_case_df = pd.DataFrame(per_case)
    per_case_df.to_csv(TABLE_DIR / "phase21_task_conditioning_per_case.csv", index=False)

    rows = []
    for dsname, grp in per_case_df.groupby("dataset"):
        delta_cols = [c for c in grp.columns if c.startswith("delta_dice_")]
        rows.append({
            "scope": dsname, "n": int(len(grp)),
            "mean_dice_correct_task": float(grp["dice_correct_task"].mean()),
            "mean_abs_delta_dice_wrong_task": float(grp["mean_abs_delta_dice_wrong_task"].mean()),
            "max_abs_delta_dice_wrong_task": float(grp["max_abs_delta_dice_wrong_task"].max()),
            "mean_signed_delta_all_wrong": float(
                grp[delta_cols].to_numpy().mean()),
            "n_improved_by_wrong_task": int((grp[delta_cols].to_numpy() < 0).sum()),
            "n_degraded_by_wrong_task": int((grp[delta_cols].to_numpy() > 0).sum()),
        })
    all_delta = [c for c in per_case_df.columns if c.startswith("delta_dice_")]
    rows.append({
        "scope": "ALL_GALLERY_64", "n": int(len(per_case_df)),
        "mean_dice_correct_task": float(per_case_df["dice_correct_task"].mean()),
        "mean_abs_delta_dice_wrong_task": float(
            per_case_df["mean_abs_delta_dice_wrong_task"].mean()),
        "max_abs_delta_dice_wrong_task": float(
            per_case_df["max_abs_delta_dice_wrong_task"].max()),
        "mean_signed_delta_all_wrong": float(per_case_df[all_delta].to_numpy().mean()),
        "n_improved_by_wrong_task": int((per_case_df[all_delta].to_numpy() < 0).sum()),
        "n_degraded_by_wrong_task": int((per_case_df[all_delta].to_numpy() > 0).sum()),
    })
    diag_df = pd.DataFrame(rows)
    diag_df.to_csv(TABLE_DIR / "phase21_task_conditioning_diagnostic.csv", index=False)

    overall = float(per_case_df["mean_abs_delta_dice_wrong_task"].mean())
    weak = overall < WEAK_THRESHOLD

    audit = {
        "artifact": "phase21_task_conditioning_diagnostic",
        "phase": 21,
        "experiment_id": EXPERIMENT_ID,
        "checkpoint_sha256": best_sha,
        "checkpoint_epoch": int(ck["epoch"]),
        "scope": "frozen 64-case gallery (16 per domain), reused UNCHANGED",
        "n_cases": int(len(per_case_df)),
        "design": (
            "Per-case inference with the CORRECT task ID vs each INCORRECT task ID. The canonical "
            "VAL result is NOT recomputed and NOT replaced; this is a diagnostic only."
        ),
        "threshold_frozen_before_reading": WEAK_THRESHOLD,
        "mean_abs_delta_dice_wrong_task": overall,
        "max_abs_delta_dice_wrong_task": float(
            per_case_df["max_abs_delta_dice_wrong_task"].max()),
        "mean_dice_correct_task": float(per_case_df["dice_correct_task"].mean()),
        "flag": "CONDITIONING_EFFECT_WEAK" if weak else "CONDITIONING_EFFECT_PRESENT",
        "flag_rule": f"CONDITIONING_EFFECT_WEAK when mean|delta Dice| < {WEAK_THRESHOLD}",
        "honesty_note": (
            "A weak effect is a legitimate scientific finding about this reference model and is "
            "reported as-is. It is NOT evidence that task conditioning is useless in general, and "
            "a strong effect here would NOT by itself prove that FiLM caused the benchmark gap "
            "(no architecture-matched control exists)."
        ),
        "film_parameter_summary": {
            "rows": int(len(film_df)),
            "tasks": 4, "sites": 5, "parameters": ["gamma", "beta"],
            "table": "reports/tables/phase21_film_parameter_summary.csv",
        },
        "test_reads": {"test_image_reads": 0, "test_mask_reads": 0,
                       "test_inference": 0, "test_visualization": 0},
    }
    (AUDIT_DIR / "phase21_task_conditioning_diagnostic.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8")

    print(f"mean |delta Dice| with wrong task = {overall:.6f} -> {audit['flag']}")
    print(f"FiLM parameter rows = {len(film_df)}")
    print(diag_df.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
