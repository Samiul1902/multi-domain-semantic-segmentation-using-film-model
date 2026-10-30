"""PHASE-13 PART-1B §11/§12 — controlled R2C checkpoint metadata rebind.

Creates R2C-rebound canonical checkpoints from the epoch-31 state.

MODEL / TRAINING STATE MUST NOT CHANGE. Only authorized metadata fields may
differ. Every tensor/scalar of model, optimizer, scheduler, GradScaler, RNG and
loader generator state must be identical to the archived epoch-31 source.

Authorized metadata changes ONLY:
  best_validation_score -> canonical bbox tuple
  best_epoch            -> 31
  early_stopping best_epoch -> 31
  early_stopping bad_epochs -> 0
  runner identity       -> R2C runner SHA
  coverage semantics    -> HISTORICAL_EXECUTING_BBOX_COVERAGE
  R2C SHA
  canonical selection history identity/SHA
  provenance references to R2B and the original epoch-31 checkpoint SHA

Writes the rebound canonical latest.pt / best.pt (originals archived in §10) and
reports/audits/phase13_part1b_epoch31_checkpoint_metadata_rebind.{json,md}.

No training. No CUDA. No TEST.
"""
from __future__ import annotations

import datetime
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import torch
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXP = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"
CHK = ROOT / "checkpoints" / EXP
ARCHIVE = CHK / "provenance"
OUT_JSON = ROOT / "reports" / "audits" / "phase13_part1b_epoch31_checkpoint_metadata_rebind.json"
OUT_MD = ROOT / "reports" / "audits" / "phase13_part1b_epoch31_checkpoint_metadata_rebind.md"

E31 = ROOT / "reports" / "audits" / "phase13_part1b_epoch31_canonical_bbox_evaluation.json"
CANON = ROOT / "reports" / "tables" / "phase13_part1b_canonical_selection_history.csv"
R2C = ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_coverage_semantics_r2c.json"
R2B = ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_metric_semantics_r2b.json"

ARCHIVE_SRC = {
    "latest.pt": ARCHIVE / "r2b_pixel_epoch31_latest.pt",
    "best.pt": ARCHIVE / "r2b_pixel_epoch31_best.pt",
}
ORIGINAL_SHA = {
    "latest.pt": "806ce086dc0fa0163029e0fb335ad6ae9605ea6b550b12371a2cb0d5340eb575",
    "best.pt": "1a4863c96484871fda2a70b02678ac602245ceea4bc8c093160a407009ba8ecc",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(8192):
            digest.update(chunk)
    return digest.hexdigest()


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "p13_rebind", ROOT / "scripts" / "training" / "train_phase13_clean_v3_localizer.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tensors_equal(a, b, path=""):
    """Recursively compare two state structures; return list of differences."""
    diffs = []
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            diffs.append(f"{path}: key mismatch {set(a.keys()) ^ set(b.keys())}")
            return diffs
        for key in a:
            diffs.extend(_tensors_equal(a[key], b[key], f"{path}.{key}"))
    elif isinstance(a, torch.Tensor) and isinstance(b, torch.Tensor):
        if a.shape != b.shape:
            diffs.append(f"{path}: shape {tuple(a.shape)} != {tuple(b.shape)}")
        elif not torch.equal(a, b):
            diffs.append(f"{path}: tensor values differ")
    elif isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
        if a.shape != b.shape:
            diffs.append(f"{path}: array shape {a.shape} != {b.shape}")
        elif not np.array_equal(a, b):
            diffs.append(f"{path}: array values differ")
    elif isinstance(a, np.generic) and isinstance(b, np.generic):
        if not _scalar_equal(a, b):
            diffs.append(f"{path}: {a!r} != {b!r}")
    elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            diffs.append(f"{path}: length {len(a)} != {len(b)}")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                diffs.extend(_tensors_equal(x, y, f"{path}[{i}]"))
    else:
        if not _scalar_equal(a, b):
            diffs.append(f"{path}: {a!r} != {b!r}")
    return diffs


def _scalar_equal(a, b) -> bool:
    """NaN-aware scalar equality (NaN == NaN is True for state comparison)."""
    try:
        if isinstance(a, float) and isinstance(b, float) and a != a and b != b:
            return True
        return bool(a == b)
    except Exception:
        return False


def main() -> int:
    runner = _load_runner()
    runner_sha = sha256_file(Path(runner.__file__))
    r2c_sha = sha256_file(R2C)
    r2b_sha = sha256_file(R2B)
    canon_sha = sha256_file(CANON)
    e31 = json.loads(E31.read_text(encoding="utf-8"))
    bbox = e31["bbox_primary"]

    canonical_tuple = [
        float(bbox["tiny_recall90"]),
        float(bbox["overall_recall90"]),
        -float(bbox["mean_roi_area_fraction"]),
        -float(e31["val_loss"]),
    ]

    STATE_KEYS = [
        "model_state", "optimizer_state", "scheduler_state", "grad_scaler_state",
        "random_state", "loader_generator_states", "epoch", "global_step",
        "manifest_version", "manifest_hashes", "seed", "input_resolution",
        "model_name", "taxonomy_id", "threshold", "training_history",
    ]

    report = {"entries": {}}
    all_ok = True
    for name in ("latest.pt", "best.pt"):
        source = ARCHIVE_SRC[name]
        if not source.exists():
            raise FileNotFoundError(f"archived source missing: {source}")
        if sha256_file(source) != ORIGINAL_SHA[name]:
            raise ValueError(f"archived {name} SHA mismatch. STOP.")

        original = torch.load(source, map_location="cpu", weights_only=False)
        rebound = {k: v for k, v in original.items()}

        # ---- authorized metadata changes ONLY ----
        rebound["best_validation_score"] = tuple(canonical_tuple)
        early = dict(rebound.get("early_stopping_state") or {})
        early["best_epoch"] = 31
        early["bad_epochs"] = 0
        rebound["early_stopping_state"] = early

        configuration = dict(rebound.get("configuration") or {})
        meta = dict(configuration.get("_phase13_execution_metadata") or {})
        meta["runner_sha"] = runner_sha
        meta["coverage_semantics"] = "HISTORICAL_EXECUTING_BBOX_COVERAGE"
        meta["coverage_semantics_secondary"] = "PIXEL_MASK_COMPONENT_SENSITIVITY_ONLY"
        meta["r2c_amendment"] = runner.R2C_AMENDMENT_NAME
        meta["r2c_amendment_sha"] = r2c_sha
        meta["canonical_selection_history"] = str(CANON)
        meta["canonical_selection_history_sha"] = canon_sha
        meta["canonical_best_epoch"] = 31
        meta["canonical_best_tuple"] = canonical_tuple
        meta["best_epoch"] = 31
        # provenance references retained
        meta["r2b_amendment"] = runner.R2B_AMENDMENT_NAME
        meta["r2b_amendment_sha"] = r2b_sha
        meta["r2b_disposition"] = "SUPERSEDED_FOR_PRIMARY_SELECTION_PRESERVED_AS_PROVENANCE"
        meta["provenance_original_epoch31_checkpoint_sha"] = ORIGINAL_SHA[name]
        meta["provenance_archive_path"] = str(source)
        meta["metadata_rebind"] = "R2C_CONTROLLED_EPOCH31_METADATA_REBIND"
        meta["metadata_rebind_disclosure"] = (
            "The original epoch-31 checkpoint was produced under R2B pixel-mask "
            "primary selection. This rebound checkpoint records the canonical "
            "historical bbox tuple. Only metadata changed; model and training "
            "state are bitwise identical to the archived source."
        )
        configuration["_phase13_execution_metadata"] = meta
        rebound["configuration"] = configuration

        target = CHK / name
        torch.save(rebound, target)

        # ---- §12 state-equality verification ----
        check = torch.load(target, map_location="cpu", weights_only=False)
        diffs = []
        for key in STATE_KEYS:
            diffs.extend(_tensors_equal(original.get(key), check.get(key), key))
        # only authorized metadata fields may differ
        assert check["best_validation_score"] == tuple(canonical_tuple)
        assert int(check["early_stopping_state"]["best_epoch"]) == 31
        assert int(check["early_stopping_state"]["bad_epochs"]) == 0
        assert int(check["epoch"]) == 31
        assert int(check["global_step"]) == 5983

        entry_ok = not diffs
        all_ok &= entry_ok
        report["entries"][name] = {
            "target_path": str(target),
            "rebound_sha256": sha256_file(target),
            "original_sha256": ORIGINAL_SHA[name],
            "state_differences": diffs,
            "model_and_training_state_identical": entry_ok,
            "authorized_metadata_changes": {
                "best_validation_score": canonical_tuple,
                "best_epoch": 31,
                "bad_epochs": 0,
                "runner_sha": runner_sha,
                "coverage_semantics": "HISTORICAL_EXECUTING_BBOX_COVERAGE",
                "r2c_amendment_sha": r2c_sha,
                "canonical_selection_history_sha": canon_sha,
            },
        }

    payload = {
        "artifact": "PHASE13_PART1B_EPOCH31_CHECKPOINT_METADATA_REBIND",
        "document_type": "CONTROLLED_CHECKPOINT_METADATA_REBIND",
        "created_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "experiment_id": EXP,
        "epoch": 31,
        "global_step": 5983,
        "canonical_bbox_tuple": canonical_tuple,
        "runner_sha": runner_sha,
        "r2c_sha": r2c_sha,
        "canonical_selection_history_sha": canon_sha,
        "entries": report["entries"],
        "model_state_bitwise_unchanged": all(
            e["model_and_training_state_identical"] for e in report["entries"].values()
        ),
        "optimizer_state_unchanged": all(
            e["model_and_training_state_identical"] for e in report["entries"].values()
        ),
        "rng_and_loader_state_unchanged": all(
            e["model_and_training_state_identical"] for e in report["entries"].values()
        ),
        "test_reads": 0,
    }
    payload["status"] = (
        "PASS_MODEL_AND_TRAINING_STATE_UNCHANGED" if all_ok else "CHECK_REQUIRED"
    )
    OUT_JSON.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    OUT_MD.write_text(
        "# PHASE-13 PART-1B — EPOCH-31 CHECKPOINT METADATA REBIND\n\n"
        f"- status: **{payload['status']}**\n"
        f"- canonical bbox tuple: `{canonical_tuple}`\n"
        f"- runner SHA: `{runner_sha}`\n"
        f"- R2C SHA: `{r2c_sha}`\n\n"
        + "\n".join(
            f"- `{name}`: state identical = {e['model_and_training_state_identical']} "
            f"(diffs: {len(e['state_differences'])})\n"
            for name, e in report["entries"].items()
        ),
        encoding="utf-8",
    )

    for name, entry in report["entries"].items():
        print(f"{name}: state_identical={entry['model_and_training_state_identical']} "
              f"diffs={len(entry['state_differences'])} sha={entry['rebound_sha256']}")
    print("STATUS:", payload["status"])
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
