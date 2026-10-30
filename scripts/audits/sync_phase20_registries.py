"""Synchronize the Phase-20 visualization registries + dataset coverage.

Additive and idempotent: existing rows/entries for earlier phases are preserved
verbatim; only a Phase-20 row/entry is inserted (replacing any prior Phase-20
row so repeated runs converge).

Also renders one 4x4 grid figure per dataset from the 16 deterministically
selected Phase-20 cases, so ``dataset_visualization_coverage.csv`` keeps pointing
at real grid files (its existing schema) while recording the Phase-20 coverage.

Writes
------
reports/audits/trained_model_visualization_registry.csv   (+ Phase 20 row)
reports/audits/trained_model_visualization_registry.json  (+ Phase 20 entry)
reports/audits/dataset_visualization_coverage.csv         (+ phase column, + 4 rows)
reports/figures/phase20_multidomain_baseline/grids/<dataset>_grid_16cases.png
reports/audits/phase20_registry_sync.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.analysis.phase20_baseline import (  # noqa: E402
    DATASET_ORDER,
    EXPERIMENT_ID,
    GALLERY_SEL_PATH,
    MANIFEST_CSV,
    load_prediction,
)
from src.analysis.phase20_gallery import _overlay_contours  # noqa: E402

AUDIT_DIR = ROOT / "reports/audits"
FIG_DIR = ROOT / "reports/figures/phase20_multidomain_baseline"
GRID_DIR = FIG_DIR / "grids"

CSV_REG = AUDIT_DIR / "trained_model_visualization_registry.csv"
JSON_REG = AUDIT_DIR / "trained_model_visualization_registry.json"
COVERAGE = AUDIT_DIR / "dataset_visualization_coverage.csv"

PHASE_LABEL = "Phase 20"
NOTEBOOK = ("notebooks/phasewise/phase_20_multidomain_baselines/"
            "phase20_shared_global_unetpp_baseline.ipynb")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_truth() -> dict:
    closure = json.loads(
        (ROOT / "experiments" / EXPERIMENT_ID / "closure.json").read_text(encoding="utf-8"))
    ev = json.loads((AUDIT_DIR / "phase20_val_evaluation.json").read_text(encoding="utf-8"))
    prot = json.loads((AUDIT_DIR / "phase20_shared_global_baseline_protocol.json")
                      .read_text(encoding="utf-8"))
    return {"closure": closure, "eval": ev, "protocol": prot}


def build_grids() -> dict:
    """One 4x4 grid per dataset from the 16 selected cases. Returns {dataset: path}."""
    GRID_DIR.mkdir(parents=True, exist_ok=True)
    sel = pd.read_csv(GALLERY_SEL_PATH)
    val = pd.read_csv(ROOT / "manifests/phase4_v3/val.csv")
    man = pd.read_csv(MANIFEST_CSV)
    meta = {r["sample_id"]: r for _, r in val.iterrows()}
    npz_of = {r["sample_id"]: r["npz_path"] for _, r in man.iterrows()}
    per_image = pd.read_csv(ROOT / "reports/tables/phase20_per_image_val_metrics.csv")
    dice_of = {r["sample_id"]: float(r["dice"]) for _, r in per_image.iterrows()}

    out = {}
    for d in DATASET_ORDER:
        ids = sel[sel["dataset"] == d].sort_values("rank")["sample_id"].tolist()
        n = len(ids)
        cols = 4
        rows = int(np.ceil(n / cols))
        fig, axes = plt.subplots(rows, cols, figsize=(4.0 * cols, 4.0 * rows))
        axes = np.atleast_1d(axes).ravel()
        for ax, sid in zip(axes, ids):
            z = load_prediction(npz_of[sid])
            gt, pred = z["gt"], z["pred"]
            base = np.asarray(Image.open(meta[sid]["image_path"]).convert("L").resize(
                (gt.shape[1], gt.shape[0])))
            _overlay_contours(ax, base, gt, pred,
                              f"{sid[:8]}…  Dice={dice_of[sid]:.3f}")
        for ax in axes[n:]:
            ax.axis("off")
        fig.suptitle(f"Phase-20 shared UNet++ — {d}: 16 deterministic VAL cases "
                     f"(green = GT contour, red = prediction contour)", fontsize=12)
        fig.tight_layout(rect=(0, 0, 1, 0.97))
        p = GRID_DIR / f"{d.lower()}_grid_16cases.png"
        fig.savefig(p, dpi=110)
        plt.close(fig)
        out[d] = p
    return out


def main() -> int:
    t = load_truth()
    closure, ev, prot = t["closure"], t["eval"], t["protocol"]

    ckpt_rel = f"checkpoints/{EXPERIMENT_ID}/best.pt"
    hist_rel = f"experiments/{EXPERIMENT_ID}/history.csv"
    cfg_rel = f"experiments/{EXPERIMENT_ID}/config.json"
    ckpt_sha = closure["best_checkpoint_sha256"]
    assert sha256_file(ROOT / ckpt_rel) == ckpt_sha, "checkpoint SHA drifted"

    train_pop = " / ".join(f"{d} {prot['dataset_populations']['TRAIN'][d]}" for d in DATASET_ORDER)
    val_pop = " / ".join(f"{d} {prot['dataset_populations']['VAL'][d]}" for d in DATASET_ORDER)
    notes = (f"Shared four-domain global baseline (single frozen UNet++, no FiLM, no regional "
             f"module, no localizer, no ROI); best epoch {closure['best_epoch']}, macro-domain VAL "
             f"Dice {closure['best_macro_domain_dice']:.6f}; early stopped at epoch "
             f"{closure['final_epoch']} (patience {closure['early_stopping_patience']}); "
             f"TEST reads 0")

    row = {
        "phase": PHASE_LABEL,
        "experiment_id": EXPERIMENT_ID,
        "model_family": "UNet++",
        "task_type": "segmentation_four_domain_shared",
        "status": "CANONICAL",
        "canonical_or_superseded": "CANONICAL",
        "checkpoint_path": ckpt_rel,
        "history_path": hist_rel,
        "config_path": cfg_rel,
        "train_population": f"{train_pop} (total 5832)",
        "val_population": f"{val_pop} (total 808)",
        "input_resolution": "512x512",
        "prediction_artifacts_available": True,
        "visualization_required": True,
        "visualization_notebook": NOTEBOOK,
        "visual_case_count": 64,
        "notes": notes,
        "checkpoint_sha256": ckpt_sha,
    }

    # ---- CSV registry -----------------------------------------------------
    csv = pd.read_csv(CSV_REG)
    csv = csv[csv["phase"].astype(str).str.strip() != PHASE_LABEL]
    for k in row:
        if k not in csv.columns:
            csv[k] = pd.NA
    csv = pd.concat([csv, pd.DataFrame([row])], ignore_index=True)
    csv = csv[list(row.keys())]
    csv.to_csv(CSV_REG, index=False)

    # ---- JSON registry ----------------------------------------------------
    js = json.loads(JSON_REG.read_text(encoding="utf-8"))
    js = [e for e in js if str(e.get("phase", "")).strip() != PHASE_LABEL]
    js.append(row)
    JSON_REG.write_text(json.dumps(js, indent=2), encoding="utf-8")

    # ---- dataset coverage -------------------------------------------------
    grids = build_grids()
    cov = pd.read_csv(COVERAGE)
    if "phase" not in cov.columns:
        cov["phase"] = "LEGACY_SAMPLE_GRIDS"
    cov = cov[cov["phase"].astype(str).str.strip() != PHASE_LABEL]
    new_rows = []
    for d in DATASET_ORDER:
        rel = str(grids[d].relative_to(ROOT)).replace("\\", "/")
        new_rows.append({"dataset": d, "sample_count": 16, "grid_path": rel,
                         "status": "PASS", "phase": PHASE_LABEL})
    cov = pd.concat([cov, pd.DataFrame(new_rows)], ignore_index=True)
    cov = cov[["dataset", "sample_count", "grid_path", "status", "phase"]]
    cov.to_csv(COVERAGE, index=False)

    # ---- report -----------------------------------------------------------
    report = {
        "artifact": "phase20_registry_sync",
        "phase": 20,
        "experiment_id": EXPERIMENT_ID,
        "registry_csv": str(CSV_REG.relative_to(ROOT)).replace("\\", "/"),
        "registry_csv_sha256": sha256_file(CSV_REG),
        "registry_json": str(JSON_REG.relative_to(ROOT)).replace("\\", "/"),
        "registry_json_sha256": sha256_file(JSON_REG),
        "coverage_csv": str(COVERAGE.relative_to(ROOT)).replace("\\", "/"),
        "coverage_csv_sha256": sha256_file(COVERAGE),
        "phase20_visual_case_count": 64,
        "per_dataset_grid_cases": {d: 16 for d in DATASET_ORDER},
        "grid_figures": {d: str(grids[d].relative_to(ROOT)).replace("\\", "/")
                         for d in DATASET_ORDER},
        "grid_sha256": {d: sha256_file(grids[d]) for d in DATASET_ORDER},
        "existing_phases_preserved": sorted({str(e["phase"]) for e in js
                                             if str(e["phase"]) != PHASE_LABEL}),
        "idempotent": True,
    }
    (AUDIT_DIR / "phase20_registry_sync.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")

    print("registry CSV rows:", len(csv), "| JSON entries:", len(js))
    print("coverage rows:", len(cov), "| phases:", sorted(set(cov["phase"])))
    for d in DATASET_ORDER:
        print(f"  {d:<7} grid -> {grids[d].relative_to(ROOT)}  {sha256_file(grids[d])[:12]}")
    print("registry CSV sha:", report["registry_csv_sha256"][:16])
    print("coverage  CSV sha:", report["coverage_csv_sha256"][:16])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
