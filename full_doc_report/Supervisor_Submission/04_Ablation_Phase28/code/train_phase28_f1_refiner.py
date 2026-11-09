"""Phase 28 -- F1 refiner training: trained refiner WITHOUT the ``p_global`` input channel.

Frozen by ``docs/phase28_ablation_execution_spec_v1_2.md`` §18-§21 and the work
order §20-§31.

Scientific factor manipulated
-----------------------------
``REFINER_INPUT_P_GLOBAL_CHANNEL`` -- presence/absence of ``p_global`` as a
refiner input channel. ROI geometry, fusion, GT scorer and target mask remain
CANONICAL (spec v1.2 §19).

Everything else inherits the exact leakage-safe Phase25A / Phase25C protocol::

    3 folds (cross-fit) | FIT 0.9 / EARLY_STOP 0.1 | seed 42
    loss 0.5*BCEWithLogits + 0.5*soft Dice(eps=1e-6)
    AdamW(lr=1e-4, wd=1e-4) | CosineAnnealingLR(T_max=100)
    batch 8 | max 100 epochs | patience 15 | AMP on CUDA
    checkpoint = minimum EARLY_STOP total loss | cudnn.deterministic

OOF requirement (spec v1.2 §21): every ROUTER_DEVELOPMENT sample's F1 candidate
must come from the fold model whose OUTER_TARGET contains it. No final F1 refiner.

Usage:
    ./.venv/Scripts/python.exe scripts/training/train_phase28_f1_refiner.py --fold 0
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import sys
import time
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402

from src.data.barr_refiner_dataset import barr_refiner_collate  # noqa: E402
from src.models.barr.router_variants import (  # noqa: E402
    REFINER_F1_EXPECTED_PARAMETERS,
    build_refiner_f1,
    count_params,
)
from src.utils.device import get_device  # noqa: E402

AUD = ROOT / "reports" / "audits"
CACHE = ROOT / "data_cache" / "phase25a_barr_roi030_cache"
CKPT_ROOT = ROOT / "checkpoints" / "phase28_refiner_F1_no_pglobal"
EXP_ROOT = ROOT / "experiments" / "phase28_refiner_F1_no_pglobal"
OUT_CACHE = ROOT / "data_cache" / "phase28_f1_refiner_v1_2"

SEED = 42
BATCH = 8
LR = 1e-4
WEIGHT_DECAY = 1e-4
MAX_EPOCHS = 100
PATIENCE = 15
T_MAX = 100
AMP_ENABLED = True
SELECTION_RULE = "minimum EARLY_STOP total loss"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def _atomic_torch_save(obj, path: Path) -> None:
    tmp = path.with_name(path.name + ".tmp")
    torch.save(obj, tmp)
    os.replace(tmp, path)


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


# =====================================================================
# F1 RGB-only crop dataset (reuses the frozen ROI-0.30 cache, drops p_global)
# =====================================================================
class F1RefinerCropDataset(torch.utils.data.Dataset):
    """Same frozen ROI-0.30 cache and same augmentation as Phase25A.

    Difference: ``inputs`` are the RGB crop ONLY -> ``(3, 256, 256)``.
    The ``p_global`` channel is never materialised (spec v1.2 §18).
    """

    def __init__(self, manifest_csv: Path, cache_root: Path = CACHE, train: bool = True,
                 base_seed: int = 42, out_size: int = 256, epoch: int = 0):
        from src.data.barr_refiner_dataset import derive_sample_seed
        import src.data.barr_refiner_dataset as _brd

        self._derive_sample_seed = derive_sample_seed
        self._augment_fn = None
        self.train = bool(train)
        self.base_seed = int(base_seed)
        self.epoch = int(epoch)
        self.out_size = int(out_size)
        self.cache_root = Path(cache_root)

        frame = pd.read_csv(manifest_csv)
        self._arrays: dict[str, dict] = {}
        self._index: dict[str, tuple[str, int]] = {}
        kept: list[dict] = []
        for domain in sorted(frame["dataset"].unique()):
            ddir = self.cache_root / domain
            meta = pd.read_csv(ddir / "meta.csv")
            pos = {str(s): i for i, s in enumerate(meta["sample_id"].astype(str))}
            self._arrays[domain] = {
                "rgb_crop": np.load(ddir / "rgb_crop.npy", mmap_mode="r"),
                "action": np.load(ddir / "action.npy"),
                "meta": meta,
            }
            for _, row in frame[frame["dataset"] == domain].iterrows():
                sid = str(row["sample_id"])
                if sid not in pos:
                    continue
                idx = pos[sid]
                if int(self._arrays[domain]["action"][idx]) != 1:
                    continue
                self._index[sid] = (domain, idx)
                kept.append({"sample_id": sid, "dataset": domain, "task_id": int(row["task_id"])})
        self.samples = pd.DataFrame(kept).reset_index(drop=True)
        self.split = "TRAIN"

        if self.train:
            # exact Phase25A augmentation (RGB only): H-flip p=0.5, rot +-5deg,
            # brightness/contrast 0.9-1.1 -- reimplemented on the RGB tensor.
            pass

    def class_distribution(self) -> dict:
        return dict(self.samples["dataset"].value_counts().to_dict())

    def __len__(self) -> int:
        return len(self.samples)

    @staticmethod
    def _augment_rgb(rgb_chw: np.ndarray, rng: random.Random) -> np.ndarray:
        """RGB-only augmentation matching Phase25A `SegmentationTransform`.

        Input/output layout is CHW (the frozen cache layout).
        """
        from PIL import Image
        hwc = np.asarray(rgb_chw, dtype=np.float32).transpose(1, 2, 0)   # (H,W,3)
        img = Image.fromarray((np.clip(hwc, 0, 1) * 255.0).astype(np.uint8))
        if rng.random() < 0.5:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        if rng.random() < 0.5:
            angle = rng.uniform(-5.0, 5.0)
            img = img.rotate(angle, resample=Image.BILINEAR, fillcolor=(0, 0, 0))
        b = rng.uniform(0.9, 1.1)
        c = rng.uniform(0.9, 1.1)
        arr = np.asarray(img, dtype=np.float32) / 255.0
        mean = float(arr.mean())
        arr = (arr - mean) * c + mean
        arr = arr * b
        return np.clip(arr, 0.0, 1.0).transpose(2, 0, 1)                 # (3,H,W)

    def __getitem__(self, index: int) -> dict:
        row = self.samples.iloc[index]
        sid = str(row["sample_id"])
        domain, idx = self._index[sid]
        arrs = self._arrays[domain]

        # frozen cache layout is CHW uint8
        rgb = np.asarray(arrs["rgb_crop"][idx], dtype=np.float32) / 255.0   # (3,H,W)
        if self.train:
            rng = random.Random(self._derive_sample_seed(self.base_seed, self.epoch, sid))
            rgb = self._augment_rgb(rgb, rng)

        return {
            "rgb_only": torch.from_numpy(np.array(rgb, dtype=np.float32, order="C", copy=True)),
            "sample_id": sid,
            "dataset": domain,
            "task_id": int(row["task_id"]),
        }


# =====================================================================
# F1 dataset variant that ALSO returns the canonical GT crop.
# =====================================================================
class F1RefinerCropDatasetWithGT(F1RefinerCropDataset):
    """F1 RGB-only inputs + canonical 256x256 GT crop target."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        # lazily attach gt_crop arrays
        for domain in list(self._arrays.keys()):
            ddir = self.cache_root / domain
            self._arrays[domain]["gt_crop"] = np.load(ddir / "gt_crop.npy", mmap_mode="r")

    def __getitem__(self, index: int) -> dict:
        row = self.samples.iloc[index]
        sid = str(row["sample_id"])
        domain, idx = self._index[sid]
        arrs = self._arrays[domain]

        rgb = np.asarray(arrs["rgb_crop"][idx], dtype=np.float32) / 255.0   # (3,H,W)
        gt = (np.asarray(arrs["gt_crop"][idx], dtype=np.float32) > 0.5).astype(np.float32)  # (1,H,W)
        if self.train:
            rng = random.Random(self._derive_sample_seed(self.base_seed, self.epoch, sid))
            rgb = self._augment_rgb(rgb, rng)

        return {
            "input": torch.from_numpy(np.array(rgb, dtype=np.float32, order="C", copy=True)),
            "target": torch.from_numpy(np.array(gt, dtype=np.float32, order="C", copy=True)),
            "sample_id": sid,
            "dataset": domain,
            "task_id": int(row["task_id"]),
        }


def f1_collate(batch):
    return {
        "input": torch.stack([b["input"] for b in batch], dim=0),
        "target": torch.stack([b["target"] for b in batch], dim=0),
        "sample_id": [b["sample_id"] for b in batch],
        "dataset": [b["dataset"] for b in batch],
        "task_id": torch.tensor([b["task_id"] for b in batch], dtype=torch.long),
    }


def build_loader(manifest_csv: Path, train: bool, seed: int, epoch: int, shuffle: bool):
    ds = F1RefinerCropDatasetWithGT(manifest_csv, cache_root=CACHE, train=train,
                                    base_seed=seed, epoch=epoch)
    gen = torch.Generator()
    gen.manual_seed(seed + epoch)
    loader = torch.utils.data.DataLoader(
        ds, batch_size=BATCH, shuffle=shuffle, num_workers=0, pin_memory=True,
        drop_last=False, generator=gen, collate_fn=f1_collate)
    return ds, loader


def dice_score_from_logits(logits, targets, threshold=0.5, eps=1e-6) -> float:
    pred = torch.sigmoid(logits).ge(threshold)
    tgt = targets.bool()
    dims = tuple(range(1, tgt.ndim))
    tp = (pred & tgt).sum(dims).float()
    fp = (pred & ~tgt).sum(dims).float()
    fn = (~pred & tgt).sum(dims).float()
    return float(((2 * tp + eps) / (2 * tp + fp + fn + eps)).mean().item())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold", type=int, required=True, choices=[0, 1, 2])
    ap.add_argument("--max-epochs", type=int, default=None,
                    help="operational bound only; scientific protocol unchanged")
    args = ap.parse_args()
    k = args.fold
    epochs_target = args.max_epochs or MAX_EPOCHS

    CKPT_ROOT.mkdir(parents=True, exist_ok=True)
    OUT_CACHE.mkdir(parents=True, exist_ok=True)
    ckpt_dir = CKPT_ROOT / f"fold{k}"
    exp_dir = EXP_ROOT / f"fold{k}"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    exp_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Phase28 F1 refiner fold{k} ===")
    seed = SEED
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    device = get_device(require_cuda=True)
    amp = AMP_ENABLED and device.type == "cuda"
    print(f"device={device} amp={amp} torch={torch.__version__}")

    manifest_csv = CACHE / "folds" / f"fold{k}_fit.csv"
    es_csv = CACHE / "folds" / f"fold{k}_early_stop.csv"
    ot_csv = CACHE / "folds" / f"fold{k}_outer_target.csv"
    fit_manifest_sha = sha(manifest_csv)
    es_manifest_sha = sha(es_csv)
    ot_manifest_sha = sha(ot_csv)

    ds_train, train_loader = build_loader(manifest_csv, True, seed, 0, shuffle=True)
    ds_es, es_loader = build_loader(es_csv, False, seed, 0, shuffle=False)
    print(f"FIT n={len(ds_train)} domains={ds_train.class_distribution()}")
    print(f"EARLY_STOP n={len(ds_es)} domains={ds_es.class_distribution()}")

    model = build_refiner_f1().to(device)
    n_params = count_params(model)
    if n_params != REFINER_F1_EXPECTED_PARAMETERS:
        print(f"FAIL-CLOSED: parameter mismatch {n_params} != {REFINER_F1_EXPECTED_PARAMETERS}")
        return 2
    print(f"model=BARRRegionalRefinerF1NoPGlobal params={n_params:,} (frozen, RGB-only stem)")

    bce = torch.nn.BCEWithLogitsLoss()
    from src.losses.segmentation import DiceLoss
    dice_loss_fn = DiceLoss(1e-6)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=T_MAX)
    scaler = torch.amp.GradScaler("cuda", enabled=amp)

    history = []
    best_loss = float("inf")
    best_epoch = -1
    bad_epochs = 0
    stop_reason = ""
    t0 = time.time()

    for epoch in range(1, epochs_target + 1):
        model.train()
        train_losses = []
        for batch in train_loader:
            inputs = batch["input"].to(device, non_blocking=True)
            targets = batch["target"].to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast(device_type=device.type, enabled=amp):
                logits = model(inputs)
                loss = 0.5 * bce(logits.float(), targets) + 0.5 * dice_loss_fn(logits.float(), targets)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            train_losses.append(float(loss.item()))
        train_loss = float(np.mean(train_losses))
        scheduler.step()

        model.eval()
        tot = 0.0
        n_es = 0
        dice_accum = []
        with torch.no_grad():
            for batch in es_loader:
                inputs = batch["input"].to(device, non_blocking=True)
                targets = batch["target"].to(device, non_blocking=True)
                with torch.amp.autocast(device_type=device.type, enabled=amp):
                    logits = model(inputs)
                    l = 0.5 * bce(logits.float(), targets) + 0.5 * dice_loss_fn(logits.float(), targets)
                tot += float(l.item()) * inputs.shape[0]
                n_es += inputs.shape[0]
                dice_accum.append(dice_score_from_logits(logits.float(), targets))
        es_loss = tot / max(n_es, 1)
        es_dice = float(np.mean(dice_accum)) if dice_accum else float("nan")

        is_best = False
        if es_loss < best_loss - 1e-12:
            best_loss = es_loss
            best_epoch = epoch
            bad_epochs = 0
            is_best = True
        else:
            bad_epochs += 1

        history.append({
            "epoch": epoch, "train_loss": train_loss, "early_stop_loss": es_loss,
            "early_stop_dice": es_dice, "lr": float(optimizer.param_groups[0]["lr"]),
            "is_best": is_best, "bad_epochs": bad_epochs,
        })
        if is_best:
            _atomic_torch_save({
                "model_state": model.state_dict(),
                "epoch": epoch, "es_loss": es_loss, "es_dice": es_dice,
                "variant": "F1", "fold": k, "seed": seed, "param_count": n_params,
            }, ckpt_dir / "best.pt")

        if epoch % 5 == 0 or epoch == 1:
            print(f"  fold{k} ep{epoch} train={train_loss:.6f} es={es_loss:.6f} "
                  f"es_dice={es_dice:.6f} best_ep={best_epoch} bad={bad_epochs}")

        if bad_epochs >= PATIENCE:
            stop_reason = f"EARLY_STOP_PATIENCE_{PATIENCE}"
            break
    else:
        stop_reason = f"MAX_EPOCHS_{epochs_target}"

    # OOF inference on OUTER_TARGET rows (spec v1.2 §21): FP32, inference_mode,
    # model.eval(), NO autocast -- canonical Phase25C item-8 semantics.
    # The canonical Phase25C driver loads the refiner on CPU and runs FP32 there;
    # we mirror that exactly (no autocast, no CUDA transfer) for OOF inference.
    state = torch.load(ckpt_dir / "best.pt", map_location="cpu", weights_only=False)
    inf_model = build_refiner_f1()
    inf_model.load_state_dict(state["model_state"])
    inf_model.eval()
    ds_ot = F1RefinerCropDatasetWithGT(ot_csv, cache_root=CACHE, train=False,
                                       base_seed=seed, epoch=0)
    print(f"OUTER_TARGET n={len(ds_ot)} domains={ds_ot.class_distribution()}")

    refined_store = {}
    for domain in list(ds_ot._arrays.keys()):
        refined_store[domain] = np.zeros((len(ds_ot._arrays[domain]["meta"]), 256, 256), dtype=np.float32)

    # chunk per domain in index order, batch 8
    import collections
    by_dom = collections.defaultdict(list)
    for i in range(len(ds_ot)):
        sid = str(ds_ot.samples.iloc[i]["sample_id"])
        dom, idx = ds_ot._index[sid]
        by_dom[dom].append((i, idx))
    INF_BATCH = 8
    processed = 0
    for domain, items in by_dom.items():
        arrs = ds_ot._arrays[domain]
        items_sorted = sorted(items, key=lambda t: t[1])
        for s in range(0, len(items_sorted), INF_BATCH):
            chunk = items_sorted[s:s + INF_BATCH]
            rgb = np.stack([np.asarray(arrs["rgb_crop"][gi], dtype=np.float32) / 255.0 for _, gi in chunk], axis=0)
            x = torch.from_numpy(np.ascontiguousarray(rgb, dtype=np.float32))   # CPU, FP32
            with torch.inference_mode():
                logits = inf_model(x)                     # FP32, no autocast
                probs = torch.sigmoid(logits.float())[:, 0].cpu().numpy()
            for j, (_, gi) in enumerate(chunk):
                refined_store[domain][gi] = probs[j]
                processed += 1
    print(f"F1 OOF refined crops written: {processed}")

    # persist the per-domain refined crops keyed by sample_id
    recs = []
    for i in range(len(ds_ot)):
        sid = str(ds_ot.samples.iloc[i]["sample_id"])
        dom, idx = ds_ot._index[sid]
        p = refined_store[dom][idx]
        out_npy = OUT_CACHE / f"fold{k}_refined_crop_{sid}.npy"
        np.save(out_npy, p.astype(np.float32))
        recs.append({"sample_id": sid, "dataset": dom, "outer_fold": k,
                     "task_id": int(ds_ot.samples.iloc[i]["task_id"]),
                     "refined_crop_path": str(out_npy.relative_to(ROOT))})
    recs_path = OUT_CACHE / f"fold{k}_refined_crop_index.csv"
    with open(recs_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(recs[0].keys()))
        w.writeheader(); w.writerows(recs)

    with open(exp_dir / "history.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(history[0].keys()))
        w.writeheader(); w.writerows(history)

    closure = {
        "artifact": f"phase28_f1_refiner_fold{k}_completion",
        "variant": "F1", "fold": k, "seed": seed, "param_count": n_params,
        "input_channels": 3, "stem": "Conv2d(3,16,3,padding=1,bias=False)",
        "n_fit": len(ds_train), "n_early_stop": len(ds_es), "n_outer_target": len(ds_ot),
        "n_epochs_run": len(history), "best_epoch": best_epoch,
        "best_early_stop_loss": best_loss, "stop_reason": stop_reason,
        "epochs_contiguous": [h["epoch"] for h in history] == list(range(1, len(history) + 1)),
        "all_finite": all(np.isfinite([h["train_loss"], h["early_stop_loss"]]).all() for h in history),
        "fit_manifest_sha256": fit_manifest_sha,
        "early_stop_manifest_sha256": es_manifest_sha,
        "outer_target_manifest_sha256": ot_manifest_sha,
        "inference_semantics": "eval + inference_mode + FP32 + no autocast (canonical Phase25C)",
        "elapsed_sec": round(time.time() - t0, 2), "device": str(device),
    }
    save_json(ckpt_dir / "completion.json", closure)
    print(f"DONE fold{k} best_ep={best_epoch} best_es_loss={best_loss:.6f} "
          f"epochs={len(history)} elapsed={closure['elapsed_sec']}s stop={stop_reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
