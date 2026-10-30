"""Phase-20 throughput feasibility probe (EXECUTION MECHANISM ONLY).

Measures (a) pure GPU step cost on cached tensors and (b) loader-only throughput
for several num_workers. It does NOT compare any scientific metric and does not
influence any result; it only informs the operational resolution/batch/worker
freeze recorded in the Phase-20 protocol.
"""
import sys, time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.models.unetpp import UNetPlusPlus
from src.losses.segmentation import BCEDiceLoss
from src.data.multidomain_dataset import MultiDomainDataset, harmonized_collate
from src.data.loaders import create_loader
from src.utils.device import get_device


def main() -> int:
    dev = get_device(require_cuda=True)
    size, bs = 512, 4
    n_train = 5832
    n_batches = int(np.ceil(n_train / bs))

    # (a) pure GPU step cost on cached tensors -----------------------------
    model = UNetPlusPlus(in_channels=3, out_channels=1, base_channels=32).to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    scaler = torch.amp.GradScaler("cuda")
    crit = BCEDiceLoss(0.5, 0.5, 1e-6)
    img = torch.rand(bs, 3, size, size, device=dev)
    msk = (torch.rand(bs, 1, size, size, device=dev) > 0.9).float()
    for _ in range(5):
        with torch.amp.autocast("cuda", enabled=True):
            loss = crit(model(img), msk)
        scaler.scale(loss).backward(); scaler.step(opt); scaler.update(); opt.zero_grad(set_to_none=True)
    torch.cuda.synchronize(); t0 = time.perf_counter(); N = 40
    for _ in range(N):
        with torch.amp.autocast("cuda", enabled=True):
            loss = crit(model(img), msk)
        scaler.scale(loss).backward(); scaler.step(opt); scaler.update(); opt.zero_grad(set_to_none=True)
    torch.cuda.synchronize()
    gpu_ms = (time.perf_counter() - t0) / N * 1000
    print(f"[GPU-ONLY] {gpu_ms:7.1f} ms/step | est epoch={gpu_ms*n_batches/1000/60:6.2f} min | peakVRAM={torch.cuda.max_memory_allocated()/1024**3:.2f}GB")
    del model, opt, scaler; torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats()

    # (b) loader-only throughput ------------------------------------------
    for nw in (0, 2, 4):
        ds = MultiDomainDataset(ROOT / "manifests/phase4_v3/train.csv", "TRAIN",
                                size=size, train=True, channel_policy="RGB_3CH")
        ld = create_loader(ds, batch_size=bs, shuffle=True, seed=42, num_workers=nw,
                           collate_fn=harmonized_collate, persistent_workers=(nw > 0))
        it = iter(ld)
        for _ in range(5):
            next(it)
        t0 = time.perf_counter(); M = 25
        for _ in range(M):
            next(it)
        dt = (time.perf_counter() - t0) / M
        print(f"[LOADER nw={nw}] {dt*1000:7.1f} ms/batch | est epoch={dt*n_batches/60:6.2f} min")
        del ld, ds, it
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
