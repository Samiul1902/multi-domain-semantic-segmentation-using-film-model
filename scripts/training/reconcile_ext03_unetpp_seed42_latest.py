"""One-time reconciliation of unetpp_seed42/latest.pt after the D97 ordering repair.

Restores the selection fields that the pre-repair ordering left one epoch stale:
    best       0.5753722339294982 -> 0.5817102846133125   (epoch-29 model, from best.pt)
    best_epoch 25                 -> 29                   (from registry + best.pt)
    bad        3                  -> 0                    (epoch 29 improved -> patience reset)

Every value is taken from evidence already on disk (best.pt + registry); nothing is invented.
Model / optimizer / scheduler / AMP-scaler / RNG tensors are NOT touched and are hash-verified
identical before and after.

Refuses to run unless the input file is byte-identical to the recorded pre-reconcile SHA.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import torch

ROOT = Path(r"D:\Softfors\jup")
RUN = ROOT / "reports" / "baselines" / "runs" / "unetpp_seed42"
LATEST = RUN / "latest.pt"
BEST = RUN / "best.pt"
REG = ROOT / "reports" / "baselines" / "ext03_run_registry.json"
EVIDENCE = ROOT / "reports" / "baselines" / "recovery_evidence"

PRE_SHA = "5bf5a986bdd0594b71b6c227c3cb8c581e917fbe4d1bc64eb60c762373bcb491"
NEW_BEST = 0.5817102846133125
NEW_BEST_EPOCH = 29
NEW_BAD = 0


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def tensor_fingerprint(obj) -> dict:
    """Stable hash of every tensor reachable from a checkpoint field."""
    out = {}

    def walk(o, path):
        if torch.is_tensor(o):
            out[path] = hashlib.sha256(
                o.detach().to("cpu").contiguous().numpy().tobytes()
            ).hexdigest() + f":{tuple(o.shape)}:{o.dtype}"
        elif isinstance(o, dict):
            for k, v in o.items():
                walk(v, f"{path}.{k}")
        elif isinstance(o, (list, tuple)):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}]")

    walk(obj, "")
    return out


def atomic_save(obj, path: Path) -> None:
    tmp = path.with_name(path.name + ".tmp")
    torch.save(obj, tmp)
    with open(tmp, "rb+") as fh:          # rb+ so fsync is legal on Windows
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def main() -> int:
    if sha(LATEST) != PRE_SHA:
        print(f"REFUSE: latest.pt is not the recorded pre-reconcile state ({sha(LATEST)})")
        return 1

    reg = json.loads(REG.read_text(encoding="utf-8"))["runs"]["unetpp_seed42"]
    best_pt = torch.load(BEST, map_location="cpu", weights_only=False)

    # evidence agreement gate
    assert abs(best_pt["macro"] - NEW_BEST) < 1e-12, "best.pt macro disagrees with NEW_BEST"
    assert best_pt["epoch"] == NEW_BEST_EPOCH, "best.pt epoch disagrees with NEW_BEST_EPOCH"
    assert abs(reg["best_metric"] - NEW_BEST) < 1e-12, "registry best_metric disagrees"
    assert reg["best_epoch"] == NEW_BEST_EPOCH, "registry best_epoch disagrees"

    st = torch.load(LATEST, map_location="cpu", weights_only=False)
    before_fields = {k: st[k] for k in ("epoch", "best", "best_epoch", "bad")}
    before_fp = {k: tensor_fingerprint(st[k]) for k in ("model", "opt", "sched", "scaler")}
    before_rng = {k: tensor_fingerprint(st.get(k)) for k in ("py_rng", "np_rng", "torch_rng", "cuda_rng")}

    st["best"] = NEW_BEST
    st["best_epoch"] = NEW_BEST_EPOCH
    st["bad"] = NEW_BAD

    atomic_save(st, LATEST)

    chk = torch.load(LATEST, map_location="cpu", weights_only=False)
    after_fp = {k: tensor_fingerprint(chk[k]) for k in ("model", "opt", "sched", "scaler")}
    after_rng = {k: tensor_fingerprint(chk.get(k)) for k in ("py_rng", "np_rng", "torch_rng", "cuda_rng")}

    print("=== RECONCILIATION ===")
    print("  before:", before_fields)
    print("  after :", {k: chk[k] for k in ("epoch", "best", "best_epoch", "bad")})
    print("  model/opt/sched/scaler tensors unchanged:", before_fp == after_fp)
    print("  rng state unchanged                        :", before_rng == after_rng)
    print("  new latest.pt sha:", sha(LATEST), "bytes:", LATEST.stat().st_size)

    ok = (before_fp == after_fp) and (before_rng == after_rng) and chk["best"] == NEW_BEST \
        and chk["best_epoch"] == NEW_BEST_EPOCH and chk["bad"] == NEW_BAD and chk["epoch"] == 29
    print("  RECONCILE_OK:", ok)
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
