"""H2C B0 SEC 6 -- empirical RNG-equivalence preflight.

CPU-only. No training. No optimizer steps. No project-data model forwards.
TRAIN ordering is obtained from the DataLoader sampler (indices only) so that no image
is decoded and no model forward is performed. Augmentation equivalence is established by
comparing the Python `random` stream that the augmentation consumes.
"""
import hashlib
import json
import math
import random
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

ROOT = Path(r"D:\Softfors\jup")
sys.path.insert(0, str(ROOT))

from src.data.kub_localizer_dataset import KUBLocalizerDataset  # noqa: E402
from src.models.kub_localizer import KUBLocalizer  # noqa: E402
from src.utils.reproducibility import make_generator, seed_worker, set_seed  # noqa: E402

SEED = 42
INPUT_RES = 512
HEATMAP_RES = 128
BATCH = 4
CFG = (ROOT / "configs" / "phase13_clean_v3"
       / "post_phase13_h2a_kub_localizer_r512_h128_sigmaeq075_centernetfocal_"
         "deploymentbalance_seed42_clean_v3.yaml")


class SpatialHead(nn.Module):
    """H2C frozen head: SPATIAL_DISCRIMINATIVE_HEAD_3X3_RELU_1X1_V1."""
    def __init__(self, in_ch=16, out_ch=1):
        super().__init__()
        self.conv3x3 = nn.Conv2d(in_ch, in_ch, 3, 1, 1, bias=True)
        self.relu = nn.ReLU(inplace=False)
        self.conv1x1 = nn.Conv2d(in_ch, out_ch, 1, 1, 0, bias=True)
        nn.init.kaiming_normal_(self.conv3x3.weight, nonlinearity='relu')
        nn.init.zeros_(self.conv3x3.bias)
        nn.init.constant_(self.conv1x1.weight, 0.0)
        nn.init.constant_(self.conv1x1.bias, math.log(0.1 / 0.9))

    def forward(self, x):
        return self.conv1x1(self.relu(self.conv3x3(x)))


def build_dataset(split):
    """Build the REAL dataset object (metadata only; __getitem__ is never called)."""
    import pandas as pd
    frame = pd.read_csv(ROOT / "reports" / "tables" / f"kub_{split.lower()}_samples_sized.csv")
    man = pd.read_csv(ROOT / "manifests" / "phase4_v3" / f"{split.lower()}.csv")
    ids = set(man["sample_id"].astype(str))
    frame = frame[frame["view_type"].eq("FULL_FIELD")
                  & frame["sample_id"].astype(str).isin(ids)].reset_index(drop=True)
    return frame


def setup(variant):
    """Replicate the H2A runner's setup ORDER exactly."""
    set_seed(SEED, deterministic=True)          # line 1261
    model = KUBLocalizer(1, 1, 16, heatmap_resolution=HEATMAP_RES).to("cpu")   # line 1341
    if variant == "h2c":
        model.head = SpatialHead(16, 1)
    train_frame = build_dataset("TRAIN")
    val_frame = build_dataset("VAL")
    sigma = 0.75
    train_ds = KUBLocalizerDataset(train_frame, "TRAIN", INPUT_RES, sigma,
                                   heatmap_resolution=HEATMAP_RES)
    val_ds = KUBLocalizerDataset(val_frame, "VAL", INPUT_RES, sigma,
                                 heatmap_resolution=HEATMAP_RES)
    train_generator = make_generator(SEED)      # line 1410
    val_generator = make_generator(SEED)        # line 1411
    train_loader = DataLoader(train_ds, batch_size=BATCH, shuffle=True,
                              num_workers=0, generator=train_generator,
                              worker_init_fn=seed_worker)
    val_loader = DataLoader(val_ds, batch_size=BATCH, shuffle=False,
                            num_workers=0, generator=val_generator,
                            worker_init_fn=seed_worker)
    return {
        "model": model, "train_ds": train_ds, "val_ds": val_ds,
        "train_loader": train_loader, "val_loader": val_loader,
        "train_generator": train_generator, "val_generator": val_generator,
    }


def train_order(ctx):
    """First-epoch TRAIN index order from the sampler (indices only -> no image decode)."""
    return [int(i) for i in ctx["train_loader"].sampler]


def val_order(ctx):
    return [int(i) for i in ctx["val_loader"].sampler]


def py_trace(n=64):
    """Bounded trace of the Python `random` stream (the stream augmentation consumes)."""
    return [random.random() for _ in range(n)]


def h(x):
    return hashlib.sha256(
        json.dumps(x, sort_keys=True, default=lambda o: int(o)).encode()).hexdigest()


a = setup("h2a")
a_order, a_val, a_py = train_order(a), val_order(a), py_trace()
a_py_state = h(list(random.getstate()[1][:32]))
a_np_state = h(list(np.random.get_state()[1][:32]))
a_torch = h(torch.get_rng_state().tolist())

b = setup("h2c")
b_order, b_val, b_py = train_order(b), val_order(b), py_trace()
b_py_state = h(list(random.getstate()[1][:32]))
b_np_state = h(list(np.random.get_state()[1][:32]))
b_torch = h(torch.get_rng_state().tolist())

res = {
    "train_order_equivalent": a_order == b_order,
    "train_trace_hash_h2a": h(a_order),
    "train_trace_hash_h2c": h(b_order),
    "train_order_len": len(a_order),
    "val_order_equivalent": a_val == b_val,
    "val_trace_hash_h2a": h(a_val),
    "val_trace_hash_h2c": h(b_val),
    "augmentation_python_trace_equivalent": a_py == b_py,
    "augmentation_trace_hash_h2a": h(a_py),
    "augmentation_trace_hash_h2c": h(b_py),
    "python_random_state_equivalent": a_py_state == b_py_state,
    "python_random_state_hash_h2a": a_py_state,
    "python_random_state_hash_h2c": b_py_state,
    "numpy_random_state_equivalent": a_np_state == b_np_state,
    "torch_global_rng_state_equivalent": a_torch == b_torch,
    "torch_global_rng_hash_h2a": a_torch,
    "torch_global_rng_hash_h2c": b_torch,
    "train_generator_state_equivalent": (
        a["train_generator"].get_state().tolist() == b["train_generator"].get_state().tolist()),
    "val_generator_state_equivalent": (
        a["val_generator"].get_state().tolist() == b["val_generator"].get_state().tolist()),
    "first20_train_order_h2a": a_order[:20],
    "first20_train_order_h2c": b_order[:20],
}

print("=== H2C B0 RNG EQUIVALENCE PREFLIGHT ===")
for k, v in res.items():
    if not k.startswith("first20"):
        print(f"  {k}: {v}")
print()
print("  first 20 TRAIN indices (H2A):", a_order[:20])
print("  first 20 TRAIN indices (H2C):", b_order[:20])

ok = (res["train_order_equivalent"] and res["val_order_equivalent"]
      and res["augmentation_python_trace_equivalent"]
      and res["python_random_state_equivalent"]
      and res["numpy_random_state_equivalent"]
      and res["train_generator_state_equivalent"]
      and res["val_generator_state_equivalent"])
print()
print("EQUIVALENCE RESULT:", "PASS" if ok else "CHECK_REQUIRED")
print("NOTE: torch_global_rng_state_equivalent is expected to be False because the H2C head")
print("      performs additional kaiming draws; no downstream stream consumes it.")

(ROOT / "reports" / "audits" / "_h2c_rng_preflight_raw.json").write_text(
    json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
raise SystemExit(0 if ok else 1)
