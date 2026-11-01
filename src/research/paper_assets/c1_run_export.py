"""Standalone, read-only validation and export of C1 run artifacts.

Consumes only what the frozen trainer persists (epoch-*.pt, latest.json,
lifecycle.json). Nothing here modifies a run directory or frozen training code.
Synthetic runs are accepted only with allow_synthetic=True and are stamped so.

Quantities the frozen producer does NOT persist (reported, never invented):
  - predicted masks and HD95/ASSD (only per-image Dice/IoU/precision/recall of the
    selected epoch are stored),
  - per-image metrics for non-selected epochs,
  - explicit resume events / interruption timestamps,
  - per-epoch wall-clock, GPU peak memory, release identity of the launching code.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path

import torch

from src.training.phase20_selection import DOMAIN_ORDER, select_best_epoch

VAL808_COUNTS = {"ISIC": 357, "BUSI": 84, "KVASIR": 87, "KUB": 280}
ARMS = ("C1-T", "C1-C")
SEEDS = (42, 123, 3407)
PRODUCER_GAPS = (
    "predicted masks and surface metrics (HD95/ASSD) are not persisted",
    "per-image metrics exist only for the selected best epoch",
    "explicit resume/interruption events are not recorded (continuity is inferred from epoch files)",
    "per-epoch wall-clock and GPU peak memory are not recorded (only cumulative active_seconds)",
    "launching release identity is not stored in the checkpoint",
)
MINIMUM_FUTURE_AMENDMENT = (
    "append-only events.jsonl written by the launcher/driver (epoch start/end, resume, "
    "release digest, GPU peak memory) without changing the trainer's scientific path"
)


class RunArtifactError(ValueError):
    pass


def _fail(code: str):
    raise RunArtifactError(code)


def state_dict_sha256(sd: dict) -> str:
    h = hashlib.sha256()
    for name in sorted(sd):
        t = sd[name].detach().cpu().contiguous()
        h.update(name.encode()); h.update(str(t.dtype).encode()); h.update(str(tuple(t.shape)).encode())
        h.update(t.numpy().tobytes())
    return h.hexdigest()


def _load(path: Path):
    raw = path.read_bytes()
    return raw, torch.load(io.BytesIO(raw), map_location="cpu", weights_only=True)


def validate_run(run_dir, *, expected_arm=None, expected_seed=None, allow_synthetic=False,
                 check_continuity=True) -> dict:
    run_dir = Path(run_dir)
    if not run_dir.is_dir():
        _fail("RUN_DIR_MISSING")
    try:
        life = json.loads((run_dir / "lifecycle.json").read_text(encoding="utf-8"))
        ptr = json.loads((run_dir / "latest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        _fail("LIFECYCLE_OR_POINTER_UNREADABLE")
    if life.get("state") != "COMPLETE":
        _fail(f"RUN_NOT_COMPLETE:{life.get('state')}")
    name = ptr.get("file")
    if not isinstance(name, str) or Path(name).name != name or not name.startswith("epoch-"):
        _fail("POINTER_FILE_INVALID")
    path = run_dir / name
    if not path.is_file():
        _fail("POINTED_CHECKPOINT_MISSING")
    try:
        raw, st = _load(path)
    except Exception:
        _fail("CHECKPOINT_UNREADABLE")
    sha = hashlib.sha256(raw).hexdigest()
    if sha != ptr.get("sha256"):
        _fail("CHECKPOINT_SHA256_MISMATCH")
    if not (st.get("identity") == ptr.get("identity") == life.get("identity")):
        _fail("IDENTITY_MISMATCH")
    c = st["contract"]
    synthetic = c.get("mode") == "SYNTHETIC_ONLY"
    if synthetic and not allow_synthetic:
        _fail("SYNTHETIC_RUN_REJECTED")
    if c.get("study_id") != "C1_FILM_ATTRIBUTION_V1" or c.get("arm") not in ARMS or c.get("seed") not in SEEDS:
        _fail("CONTRACT_NOT_C1_FROZEN")
    if expected_arm and c["arm"] != expected_arm or expected_seed and c["seed"] != expected_seed:
        _fail("ARM_OR_SEED_MISMATCH")
    if c.get("protocol_sha256") != "531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61":
        _fail("PROTOCOL_DIGEST_MISMATCH")
    hist = st["history"]
    if not hist or [r["epoch"] for r in hist] != list(range(1, len(hist) + 1)) or st["epoch"] != len(hist):
        _fail("HISTORY_DISCONTIGUOUS")
    for r in hist:
        vals = [r["train_loss"], r["val_loss"], r["macro_domain_dice"], r["learning_rate"]] + [r[f"val_dice_{d}"] for d in DOMAIN_ORDER]
        if not all(isinstance(v, float) and math.isfinite(v) for v in vals):
            _fail("HISTORY_NONFINITE")
        if r["macro_domain_dice"] != sum(r[f"val_dice_{d}"] for d in DOMAIN_ORDER) / 4:
            _fail("HISTORY_MACRO_MISMATCH")
    replay = select_best_epoch(hist)
    if replay["selected_epoch"] != st["best_epoch"]:
        _fail("BEST_EPOCH_REPLAY_MISMATCH")
    rec = c["recipe"]
    full = c["fixture"]["epochs"] if c.get("fixture") else rec["max_epochs"]
    if not (len(hist) >= full or st["bad_epochs"] >= rec["early_stop_patience"]):
        _fail("STOPPING_CRITERION_NOT_REACHED")
    if len(hist) - st["best_epoch"] != st["bad_epochs"]:
        _fail("BAD_EPOCH_COUNT_MISMATCH")
    if not st.get("best_model"):
        _fail("BEST_MODEL_MISSING")
    recs = st["best_records"]
    ids = [r["sample_id"] for r in recs]
    if len(set(ids)) != len(ids):
        _fail("DUPLICATE_SAMPLE_ID")
    cnt = {d: sum(r["domain"] == d for r in recs) for d in DOMAIN_ORDER}
    if set(r["domain"] for r in recs) - set(DOMAIN_ORDER) or 0 in cnt.values():
        _fail("DOMAIN_COVERAGE_INVALID")
    if not synthetic and cnt != VAL808_COUNTS:
        _fail(f"VAL808_COUNT_MISMATCH:{cnt}")
    for r in recs:
        if not all(math.isfinite(r[k]) and 0.0 <= r[k] <= 1.0 for k in ("dice", "iou", "precision", "recall")):
            _fail("PER_IMAGE_METRIC_INVALID")
    cont = _continuity(run_dir, st, hist) if check_continuity else None
    return {"run_dir": str(run_dir), "arm": c["arm"], "seed": c["seed"], "mode": c["mode"],
            "synthetic": synthetic, "identity": st["identity"], "checkpoint_file": name,
            "checkpoint_sha256": sha, "best_epoch": st["best_epoch"], "epochs_completed": len(hist),
            "stopped_by": "max_epochs" if len(hist) >= full else "early_stopping",
            "initial_sha256": st["initial_sha256"], "parameter_counts": st["counts"],
            "best_model_state_sha256": state_dict_sha256(st["best_model"]),
            "best_model_source": f"{name}::best_model (epoch {st['best_epoch']})",
            "architecture": "GlobalMedFiLM (frozen canonical)", "active_seconds": st["active_seconds"],
            "protocol_sha256": c["protocol_sha256"], "dataset_manifest": c["dataset"]["manifest_version"],
            "domain_counts": cnt, "resume_continuity": cont, "producer_gaps": list(PRODUCER_GAPS),
            "_history": hist, "_records": recs}


def _continuity(run_dir: Path, final: dict, final_hist: list) -> dict:
    files = sorted(run_dir.glob("epoch-*.pt"))
    by_epoch = {}
    for f in files:
        by_epoch.setdefault(int(f.name.split("-")[1]), []).append(f)
    expected = list(range(1, len(final_hist) + 1))
    if sorted(by_epoch) != expected:
        _fail("EPOCH_CHECKPOINT_SEQUENCE_INCOMPLETE")
    repeats = {e: len(v) for e, v in by_epoch.items() if len(v) > 1}
    for e, fs in by_epoch.items():
        for f in fs:
            try:
                _, s = _load(f)
            except Exception:
                _fail("EPOCH_CHECKPOINT_UNREADABLE")
            if s["identity"] != final["identity"] or s["initial_sha256"] != final["initial_sha256"]:
                _fail("EPOCH_CHECKPOINT_IDENTITY_DRIFT")
            if s["history"] != final_hist[:e]:
                _fail("EPOCH_HISTORY_NOT_PREFIX_OF_FINAL")
    return {"epoch_files": len(files), "epochs_covered": len(by_epoch), "history_prefix_consistent": True,
            "epochs_with_multiple_commits": repeats,
            "note": "repeated commits of one epoch indicate a replay after interruption; explicit resume events are not recorded"}


def _write(path: Path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(header); w.writerows(rows)


def export_run(run_dir, out_dir, **kw) -> dict:
    rep = validate_run(run_dir, **kw)
    out = Path(out_dir)
    tag = f"seed{rep['seed']}_{rep['arm']}"
    hist, recs = rep.pop("_history"), rep.pop("_records")
    mark = "SYNTHETIC" if rep["synthetic"] else "REAL"
    hdr = ["epoch", "train_loss", "val_loss", "macro_domain_dice", "learning_rate"] + [f"val_dice_{d}" for d in DOMAIN_ORDER] + ["is_best_so_far", "selected_epoch"]
    _write(out / f"{tag}_learning_curve.csv", hdr,
           [[r["epoch"], r["train_loss"], r["val_loss"], r["macro_domain_dice"], r["learning_rate"]] + [r[f"val_dice_{d}"] for d in DOMAIN_ORDER]
            + [r["improved"], r["epoch"] == rep["best_epoch"]] for r in hist])
    dom = []
    for d in DOMAIN_ORDER:
        rr = [r for r in recs if r["domain"] == d]
        dom.append([d, len(rr)] + [sum(r[k] for r in rr) / len(rr) for k in ("dice", "iou", "precision", "recall")])
    _write(out / f"{tag}_per_domain.csv", ["domain", "n", "dice", "iou", "precision", "recall"], dom)
    _write(out / f"{tag}_per_image.csv", ["sample_id", "domain", "dice", "iou", "precision", "recall"],
           [[r["sample_id"], r["domain"], r["dice"], r["iou"], r["precision"], r["recall"]] for r in sorted(recs, key=lambda r: r["sample_id"])])
    rep.update({"data_authenticity": mark, "population": "VAL808 at selected epoch (selection-consumed)" if not rep["synthetic"] else "SYNTHETIC fixture",
                "metric_definition": "per-image Dice/IoU/precision/recall, threshold 0.5, frozen phase21 definition",
                "minimum_compatible_future_amendment": MINIMUM_FUTURE_AMENDMENT,
                "exports": [f"{tag}_learning_curve.csv", f"{tag}_per_domain.csv", f"{tag}_per_image.csv"]})
    (out / f"{tag}_provenance.json").write_text(json.dumps(rep, indent=2, sort_keys=True), encoding="utf-8")
    return rep
