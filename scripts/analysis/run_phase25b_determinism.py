"""Phase 25B -- determinism subset audit (work-order section 18).

Selects a DETERMINISTIC 64-sample audit subset (16 per domain) chosen by a
selection rule independent of feature values and outcomes, then re-extracts
those 64 rows twice under IDENTICAL inference settings and compares each run
against the other and against the frozen canonical matrix.

IMPORTANT (AMP batching contract): the frozen canonical matrix was produced by
batching strictly inside a single domain, in ``dev.sort_values(["dataset",
"sample_id"])`` order, in contiguous chunks of 8.  Under ``torch.amp.autocast``
the numerical result of a forward pass depends on the batch MEMBERSHIP (AMP
kernel selection is batch-shape/composition dependent).  A determinism re-run is
therefore only meaningful -- and only fair -- if every sampled row is placed in
the EXACT batch it occupied in the canonical run.  We reproduce that by replaying
the canonical batches in canonical order and keeping only the subset rows from
each batch.  Batches that contain no subset row are skipped (their absence does
not change any other batch's membership).

Does NOT re-run all 4957 samples.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image as PILImage

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

from src.data.barr_roi import REGIONAL_CANVAS_RESOLUTION  # noqa: E402
from src.data.transforms import SegmentationTransform  # noqa: E402
from src.features.barr_pre_refinement_features import (  # noqa: E402
    NUMERIC_DIM, TAPS, build_feature_vector)
from src.models.film import GlobalMedFiLM  # noqa: E402
from src.utils.device import get_device  # noqa: E402

AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
CACHE = ROOT / "data_cache" / "phase25b_barr_pre_refinement_features_v1_2"
ROI030 = ROOT / "data_cache" / "phase25a_barr_roi030_cache"
GLOBAL_CKPT = ROOT / "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"
GLOBAL_CONFIG = ROOT / "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json"
SPLIT_MANIFEST = ROOT / "reports" / "audits" / "phase24_router_split_manifest.csv"
UTC = datetime.now(timezone.utc).isoformat()
DOMAINS = ("BUSI", "ISIC", "KUB", "KVASIR")
BATCH = 8
TOL = 1e-6
GLOBAL_CKPT_SHA = "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def select_subset(meta: pd.DataFrame) -> list[tuple[str, str]]:
    """Deterministic 64-sample audit subset: per domain, sort sample_ids
    lexicographically and take 16 evenly spaced indices.  Independent of feature
    values, GT, and outcomes."""
    subset: list[tuple[str, str]] = []
    for dom in DOMAINS:
        ids = sorted(meta.index[meta["domain"] == dom].tolist())
        picks = [ids[round(i * (len(ids) - 1) / 15)] for i in range(16)]
        assert len(set(picks)) == 16
        subset += [(dom, s) for s in picks]
    assert len(subset) == 64
    return subset


def main() -> int:
    assert sha(GLOBAL_CKPT) == GLOBAL_CKPT_SHA, "global checkpoint SHA mismatch"

    feats = np.load(CACHE / "features.npy")
    meta = pd.read_csv(CACHE / "metadata.csv").set_index("sample_id", drop=False)
    manifest = pd.read_csv(ROOT / "manifests/phase4_v3/train.csv").set_index("sample_id",
                                                                             drop=False)
    sm = pd.read_csv(SPLIT_MANIFEST)
    dev = sm[sm["split_role"] == "ROUTER_DEVELOPMENT"].copy()
    dev = dev.sort_values(["dataset", "sample_id"]).reset_index(drop=True)

    roi = {}
    for dom in DOMAINS:
        for r in csv.DictReader(open(ROI030 / dom / "meta.csv", newline="",
                                     encoding="utf-8")):
            roi[r["sample_id"]] = r

    subset = select_subset(meta)
    subset_ids = {s for _d, s in subset}

    cfg = json.loads(GLOBAL_CONFIG.read_text(encoding="utf-8"))
    model = GlobalMedFiLM(task_count=cfg["model"]["task_count"],
                          in_channels=cfg["model"]["in_channels"],
                          out_channels=cfg["model"]["out_channels"],
                          channels=tuple(cfg["model"]["channels"]),
                          task_embedding_dim=cfg["model"]["task_embedding_dim"],
                          film_hidden_dim=cfg["model"]["film_hidden_dim"])
    st = torch.load(GLOBAL_CKPT, map_location="cpu", weights_only=False)
    model.load_state_dict(st["model_state"])
    model.eval()
    for p in model.parameters():
        p.requires_grad = False
    device = get_device(require_cuda=True)
    model = model.to(device)
    tf = SegmentationTransform(size=REGIONAL_CANVAS_RESOLUTION, train=False, image_mode="RGB")

    from scripts.analysis.run_phase25b_feature_extraction import TapRecorder  # noqa

    def extract_once() -> dict[str, np.ndarray]:
        """Replay the canonical contiguous batches (chunks of 8 inside a single
        domain, in dev sort order) and keep only the subset rows, so every
        sampled row is placed in the exact batch it occupied canonically."""
        got: dict[str, np.ndarray] = {}
        for dom in sorted(dev["dataset"].unique().tolist()):
            sub = dev[dev["dataset"] == dom].reset_index(drop=True)
            n = len(sub)
            for start in range(0, n, BATCH):
                chunk = sub.iloc[start:start + BATCH]
                sids = [str(x) for x in chunk["sample_id"]]
                if not any(s in subset_ids for s in sids):
                    continue
                imgs, tasks = [], []
                for _, r in chunk.iterrows():
                    row = manifest.loc[r["sample_id"]]
                    with PILImage.open(row["image_path"]) as image, \
                            PILImage.open(row["mask_path"]) as mask:
                        it, _mt, _md = tf(image, mask)
                    imgs.append(it)
                    tasks.append(int(row["task_id"]))
                bi = torch.stack(imgs).to(device)
                bt = torch.tensor(tasks, dtype=torch.long, device=device)
                rec = TapRecorder(model)
                try:
                    with torch.no_grad(), torch.amp.autocast(device_type=device.type,
                                                             enabled=True):
                        lg = model(bi, bt)
                    prob = torch.sigmoid(lg.float()).cpu().numpy()[:, 0]
                    cmaps = {t: rec.store[t].float().cpu().numpy() for t in TAPS}
                finally:
                    rec.close()
                for i, sid in enumerate(sids):
                    if sid in subset_ids:
                        got[sid] = build_feature_vector(
                            {t: cmaps[t][i] for t in TAPS},
                            prob[i].astype(np.float32), roi[sid])
        assert set(got) == subset_ids, (len(got), len(subset_ids))
        return got

    run1 = extract_once()
    run2 = extract_once()

    order = [s for _d, s in subset]
    a = np.stack([run1[s] for s in order])
    b = np.stack([run2[s] for s in order])
    frozen = np.stack([feats[int(meta.loc[s, "feature_row_index"])] for s in order])

    def cmp(x, y):
        D = np.abs(x.astype(np.float64) - y.astype(np.float64))
        return {"max_abs": float(D.max()), "mean_abs": float(D.mean()),
                "n_elements_exceeding_tolerance": int((D > TOL).sum()),
                "allclose": bool(np.allclose(x, y, atol=TOL, rtol=0))}

    run1_run2 = cmp(a, b)
    run1_frozen = cmp(a, frozen)

    subset_rows = [{"audit_index": i, "domain": d, "sample_id": s,
                    "feature_row_index": int(meta.loc[s, "feature_row_index"])}
                   for i, (d, s) in enumerate(subset)]
    pd.DataFrame(subset_rows).to_csv(TAB / "phase25b_feature_determinism_subset.csv",
                                     index=False, lineterminator="\n")

    verdict = ("PHASE25B_FEATURE_DETERMINISM_PASS"
               if run1_run2["allclose"] and run1_frozen["allclose"] else
               "PHASE25B_FEATURE_DETERMINISM_FAIL")
    out = {
        "artifact": "phase25b_feature_determinism",
        "phase": "25B",
        "subset_size": 64,
        "per_domain": 16,
        "selection_rule": ("sort each domain's sample_ids lexicographically, take 16 "
                           "evenly spaced indices; independent of feature values and outcomes"),
        "batching_contract": ("replay the canonical contiguous batches (chunks of 8 inside "
                              "a single domain, dev.sort_values(['dataset','sample_id']) "
                              "order) and keep only subset rows, so each sampled row sits in "
                              "the same AMP batch as in the canonical extraction"),
        "tolerance": TOL,
        "reran_all_4957": False,
        "n_forward_batches_replayed": None,
        "run1_vs_run2": run1_run2,
        "run1_vs_frozen_cache": run1_frozen,
        "verdict": verdict,
        "generated_utc": UTC,
        "test_reads": 0,
    }
    (AUD / "phase25b_feature_determinism.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1)[:1200])
    return 0 if verdict.endswith("PASS") else 1


if __name__ == "__main__":
    sys.exit(main())
