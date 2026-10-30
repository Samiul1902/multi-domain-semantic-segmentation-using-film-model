"""EXT-03 Stage B executable same-protocol baseline trainer (resumable).

Frozen protocol: 3x512x512 input, BCEWithLogitsLoss, Adam(1e-3, wd 1e-4),
cosine LR, AMP, equal-domain macro development-validation Dice checkpoint
selection, patience-15 early stopping, 100-epoch ceiling. Canonical
preprocessing semantics: aspect-preserving resize (min(512/w,512/h)),
symmetric pad to 512, image BILINEAR, mask NEAREST, mask binarized (>0).

D99 EXCEPTION (2026-10-25): segformer_b0 uses lr=1e-4 instead of 1e-3.
SegFormer-B0 is built from SegformerConfig with NO pretrained weights
(src/models/segformer_b0.py), and at lr=1e-3 under AMP autocast its decode-head
BatchNorm running statistics overflowed to inf/nan by epoch 5, driving the
training loss to NaN and permanently poisoning the checkpoint. 1e-4 is the
project's frozen internal-baseline learning rate (configs/phase09_clean_v3,
configs/phase10_clean_v3), so this is a correction TOWARD the frozen authority,
not an invention. All other architectures, and every other hyperparameter, are
unchanged. See reports/audits/
ext03_segformer_divergence_and_interruption_adjudication_v1_0.json
"""
import argparse
import csv
import hashlib
import json
import os
import random
import sys
import time
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
sys.path.insert(0, str(ROOT))
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

B = ROOT / "reports" / "baselines"
RUNS = B / "runs"
REG = B / "ext03_run_registry.json"
TRAIN_CSV = ROOT / "manifests" / "phase4_v3" / "train.csv"
VAL_CSV = ROOT / "manifests" / "phase4_v3" / "val.csv"
ARCHS = ["unet", "attention_unet", "unetpp", "deeplabv3plus", "segformer_b0"]
KW = {"unet": dict(in_channels=3, out_channels=1), "attention_unet": dict(in_channels=3, out_channels=1),
      "unetpp": dict(in_channels=3, out_channels=1), "deeplabv3plus": dict(in_channels=3, out_channels=1),
      "segformer_b0": dict()}
PARAMS = {"unet": 7763041, "attention_unet": 7851285, "unetpp": 9159681, "deeplabv3plus": 40347041, "segformer_b0": 3714401}
SEEDS = [42, 123, 3407]
SIZE = 512
BATCH = 4
LR = 1e-3
# D99: per-architecture learning-rate override. segformer_b0 is trained from scratch
# (no pretrained weights) and diverges to NaN within 5 epochs at 1e-3 under AMP;
# 1e-4 is the frozen internal-baseline LR. No other architecture is overridden.
LR_OVERRIDE = {"segformer_b0": 1e-4}
WD = 1e-4
MAX_EPOCHS = 100
PATIENCE = 15
DOMAINS = ["ISIC", "BUSI", "KVASIR", "KUB"]
DOMAIN_TASK = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_registry():
    return json.loads(REG.read_text(encoding="utf-8"))


def save_registry(reg):
    tmp = REG.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, REG)


def set_seed(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)


def load_pair(img_path, msk_path):
    im = Image.open(img_path).convert("RGB")
    ms = Image.open(msk_path).convert("L")
    w, h = im.size
    s = min(SIZE / w, SIZE / h)
    nw, nh = max(1, round(w * s)), max(1, round(h * s))
    im = im.resize((nw, nh), Image.BILINEAR)
    ms = ms.resize((nw, nh), Image.NEAREST)
    canvas_i = Image.new("RGB", (SIZE, SIZE), 0)
    canvas_m = Image.new("L", (SIZE, SIZE), 0)
    ow, oh = (SIZE - nw) // 2, (SIZE - nh) // 2
    canvas_i.paste(im, (ow, oh)); canvas_m.paste(ms, (ow, oh))
    x = torch.from_numpy(np.asarray(canvas_i, dtype=np.float32) / 255.0).permute(2, 0, 1)
    y = (torch.from_numpy(np.asarray(canvas_m, dtype=np.float32)) > 0).float().unsqueeze(0)
    return x, y


def dice(pred_bin, gt_bin, eps=1e-7):
    inter = (pred_bin * gt_bin).sum().item()
    return (2 * inter + eps) / (pred_bin.sum().item() + gt_bin.sum().item() + eps)


def eval_val(model, val_rows, device):
    model.eval()
    per = {d: [] for d in DOMAINS}
    with torch.no_grad():
        for bi in range(0, len(val_rows), BATCH):
            chunk = val_rows[bi:bi + BATCH]
            xs, ys, ds = [], [], []
            for r in chunk:
                x, y = load_pair(ROOT / r["image_path"], ROOT / r["mask_path"])
                xs.append(x); ys.append(y); ds.append(r["dataset"])
            x = torch.stack(xs).to(device)
            out = model(x); out = out[0] if isinstance(out, (tuple, list)) else out
            p = (torch.sigmoid(out.float()).cpu() > 0.5).float()
            for j, d in enumerate(ds):
                if d in per:
                    per[d].append(dice(p[j], ys[j]))
    dom = {d: (sum(v) / len(v) if v else float("nan")) for d, v in per.items()}
    present = [v for v in dom.values() if not np.isnan(v)]
    macro = sum(present) / len(present) if present else float("nan")
    return macro, dom


def run_one(reg, run, train_rows, val_rows, device, max_epochs, max_steps=None):
    rid = run["run_id"]; a = run["architecture"]; seed = run["seed"]
    rdir = RUNS / rid; rdir.mkdir(parents=True, exist_ok=True)
    ckpt = rdir / "latest.pt"; best_p = rdir / "best.pt"
    from src.models.factory import create_model
    model = create_model(a, **KW[a]).to(device)
    if sum(p.numel() for p in model.parameters()) != PARAMS[a]:
        raise RuntimeError(f"PARAMETER_DRIFT:{a}")
    lr_used = LR_OVERRIDE.get(a, LR)
    opt = torch.optim.Adam(model.parameters(), lr=lr_used, weight_decay=WD)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max_epochs)
    scaler = torch.cuda.amp.GradScaler(enabled=(device == "cuda"))
    reg["runs"][rid]["lr_used"] = lr_used
    reg["runs"][rid]["lr_source"] = ("D99_OVERRIDE" if a in LR_OVERRIDE else "SHARED_PROTOCOL")
    save_registry(reg)
    start_epoch, best, best_epoch, bad = 0, -1.0, -1, 0
    if ckpt.exists():
        st = torch.load(ckpt, map_location=device, weights_only=False)
        model.load_state_dict(st["model"]); opt.load_state_dict(st["opt"]); sched.load_state_dict(st["sched"])
        if st.get("scaler"): scaler.load_state_dict(st["scaler"])
        start_epoch, best, best_epoch, bad = st["epoch"], st["best"], st["best_epoch"], st["bad"]
        # RNG state restore is best-effort: it never gates scientific correctness.
        try:
            if st.get("py_rng") is not None:
                random.setstate(st["py_rng"])
        except Exception:
            pass
        try:
            if st.get("np_rng") is not None:
                np.random.set_state(st["np_rng"])
        except Exception:
            pass
        try:
            tr = st.get("torch_rng")
            if tr is not None:
                if not torch.is_tensor(tr):
                    tr = torch.tensor(list(tr), dtype=torch.uint8)
                torch.set_rng_state(tr.to(dtype=torch.uint8, device="cpu"))
        except Exception:
            pass
        try:
            if device == "cuda" and st.get("cuda_rng") is not None:
                torch.cuda.set_rng_state_all(st["cuda_rng"])
        except Exception:
            pass
        reg["runs"][rid]["resume_count"] += 1
        save_registry(reg)
    for ep in range(start_epoch, max_epochs):
        model.train(); t0 = time.time(); tl = 0.0; nb = 0
        order = list(range(len(train_rows)))
        random.Random(seed * 100000 + ep).shuffle(order)
        for bi in range(0, len(order), BATCH):
            chunk = order[bi:bi + BATCH]
            xs, ys = [], []
            for i in chunk:
                r = train_rows[i]
                xi, yi = load_pair(ROOT / r["image_path"], ROOT / r["mask_path"])
                xs.append(xi); ys.append(yi)
            x = torch.stack(xs).to(device); y = torch.stack(ys).to(device)
            opt.zero_grad(set_to_none=True)
            with torch.cuda.amp.autocast(enabled=(device == "cuda")):
                out = model(x); out = out[0] if isinstance(out, (tuple, list)) else out
                loss = F.binary_cross_entropy_with_logits(out.float(), y)
            # D99 observability guard: a non-finite loss means the run is already dead.
            # Previously it was written into the checkpoint and NaN was logged for every
            # remaining epoch, silently poisoning latest.pt and the selection state.
            # Raising here converts silent corruption into a recorded TECHNICAL_FAILURE
            # and leaves the last finite checkpoint on disk, so resume stays possible.
            if not bool(torch.isfinite(loss).item()):
                raise RuntimeError(f"NON_FINITE_LOSS:{rid}:ep{ep+1}:step{nb+1}")
            scaler.scale(loss).backward(); scaler.step(opt); scaler.update()
            tl += loss.item(); nb += 1
            if max_steps and nb >= max_steps:
                break
        sched.step()
        macro = float("nan"); dom = {}
        if not max_steps:
            macro, dom = eval_val(model, val_rows, device)
        # Selection state is updated BEFORE the resume checkpoint is written, so latest.pt
        # describes the true post-epoch state (previously it lagged one epoch, which made a
        # resume understate `best` and restore a stale early-stopping counter).
        if not np.isnan(macro) and macro > best:
            best, best_epoch, bad = macro, ep + 1, 0
            torch.save({"model": model.state_dict(), "epoch": ep + 1, "macro": macro}, best_p)
        elif not max_steps:
            bad += 1
        state = {"model": model.state_dict(), "opt": opt.state_dict(), "sched": sched.state_dict(),
                 "scaler": scaler.state_dict(), "epoch": ep + 1, "best": best, "best_epoch": best_epoch,
                 "bad": bad, "py_rng": random.getstate(), "np_rng": np.random.get_state(),
                 "torch_rng": torch.get_rng_state(),
                 "cuda_rng": (torch.cuda.get_rng_state_all() if device == "cuda" else None)}
        tmp = ckpt.with_suffix(".pt.tmp"); torch.save(state, tmp); os.replace(tmp, ckpt)
        reg["runs"][rid].update({"current_epoch": ep + 1, "best_epoch": best_epoch or None,
                                 "best_metric": (None if best < 0 else best),
                                 "checkpoint_path": str((rdir / "best.pt").relative_to(ROOT)),
                                 "last_resume_time": time.strftime("%Y-%m-%dT%H:%M:%S")})
        save_registry(reg)
        print(f"  {rid} ep{ep+1} loss={tl/max(nb,1):.4f} macro={macro:.4f} best={best:.4f} bad={bad}", flush=True)
        if max_steps:
            break
        if bad >= PATIENCE:
            break
    return best, best_epoch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--max-steps", type=int, default=None)
    ap.add_argument("--max-epochs", type=int, default=MAX_EPOCHS)
    args = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    train_rows = list(csv.DictReader(open(TRAIN_CSV, encoding="utf-8")))
    val_rows = list(csv.DictReader(open(VAL_CSV, encoding="utf-8")))
    print(f"TRAIN={len(train_rows)} VAL={len(val_rows)} device={device}", flush=True)
    reg = load_registry()
    for run in reg["matrix"]:
        info = reg["runs"][run["run_id"]]
        if info["status"] == "COMPLETE":
            continue
        set_seed(run["seed"])
        info["status"] = "RUNNING"; info["start_time"] = info["start_time"] or time.strftime("%Y-%m-%dT%H:%M:%S")
        save_registry(reg)
        try:
            best, be = run_one(reg, run, train_rows, val_rows, device, args.max_epochs, args.max_steps)
            if args.selftest or args.max_steps:
                info["status"] = "NOT_STARTED" if args.selftest else "INTERRUPTED_RESUMABLE"
            else:
                info["status"] = "COMPLETE"; info["completion_time"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                info["checkpoint_sha"] = sha(RUNS / run["run_id"] / "best.pt")
            save_registry(reg)
        except Exception as e:
            info["status"] = "TECHNICAL_FAILURE"; info["technical_failure_reason"] = str(e)[:300]; save_registry(reg)
            print("TECHNICAL_FAILURE", run["run_id"], e, flush=True)
        if args.selftest or args.max_steps:
            break
    print("matrix pass complete", flush=True)


if __name__ == "__main__":
    main()
