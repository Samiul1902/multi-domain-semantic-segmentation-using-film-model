"""Phase 25C -- OOF prediction determinism (§19).

Do NOT rerun all 4957 samples. Choose a deterministic 64-sample subset
(16/domain, independent of outcomes) and replay each selected sample inside its
ORIGINAL canonical Phase25C inference batch (the fold-filtered contiguous chunk
of 8 within the domain), NOT re-batched alone.

Compares: candidate probability, candidate mask, candidate Dice, DeltaDice.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
CODE = ROOT / "notebooks" / "phasewise" / "phase_25c_paired_gain_labels" / "code"
sys.path.insert(0, str(CODE))
import phase25c_common as C  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402
from PIL import Image, ImageOps  # noqa: E402

from src.models.barr.regional_refiner import BARRRegionalRefinerV1  # noqa: E402
from src.data.barr_roi import roi_geometry  # noqa: E402
from src.metrics.evaluation_metrics import binary_confusion_counts, dice as dice_fn  # noqa: E402

AUD = ROOT / "reports" / "audits"
TRAIN_MANIFEST = ROOT / "manifests" / "phase4_v3" / "train.csv"
UTC = "2026-09-30T17:15:00+00:00"
SEG = C.SEGMENTATION_OUTPUT_THRESHOLD
SUB_PER_DOMAIN = 16


def full_field_gt(mask_path, size=512):
    img = Image.open(mask_path).convert("L")
    w, h = img.size
    scale = min(size / w, size / h)
    rw, rh = max(1, round(w * scale)), max(1, round(h * scale))
    img = img.resize((rw, rh), Image.Resampling.NEAREST)
    left, top = (size - rw) // 2, (size - rh) // 2
    img = ImageOps.expand(img, (left, top, size - rw - left, size - rh - top))
    return (np.asarray(img) > 0).astype(np.uint8)


def main() -> int:
    lab = pd.read_csv(C.LABEL_CSV)
    lab_lookup = {str(s): row for s, row in
                  zip(lab["sample_id"].astype(str), lab.to_dict("records"))}
    assign = C.load_outer_fold_assignment()
    man = pd.read_csv(TRAIN_MANIFEST).set_index("sample_id", drop=False)
    domains = sorted(lab["domain"].unique())

    models = {}
    for k in C.OUTER_FOLDS:
        m = BARRRegionalRefinerV1()
        st = torch.load(C.FOLD_CKPT[k], map_location="cpu", weights_only=False)
        m.load_state_dict(st["model_state"])
        m.eval()
        models[k] = m

    # ---- deterministic subset: 16/domain, evenly spaced by sorted sample_id -- #
    subset = {}
    for d in domains:
        ids = sorted(lab[lab["domain"] == d]["sample_id"].astype(str).tolist())
        pick = [ids[round(i * (len(ids) - 1) / (SUB_PER_DOMAIN - 1))]
                for i in range(SUB_PER_DOMAIN)]
        subset[d] = pick
    subset_flat = [(d, s) for d in domains for s in subset[d]]

    results = []
    prob_tol = 1e-6
    metric_tol = 1e-12
    max_prob_diff = 0.0
    max_metric_diff = 0.0
    max_delta_diff = 0.0
    mask_mismatches = 0

    for d in domains:
        dc = C.DomainCache(d)
        ids_all = dc.meta["sample_id"].astype(str).tolist()
        caches = {k: [i for i, s in enumerate(ids_all) if assign.get(s) == k]
                  for k in C.OUTER_FOLDS}
        pickset = set(subset[d])
        for k in C.OUTER_FOLDS:
            idxs = caches[k]
            model = models[k]
            # replay the CANONICAL contiguous batch partition of the fold list
            for start in range(0, len(idxs), C.INFERENCE_BATCH):
                chunk = idxs[start:start + C.INFERENCE_BATCH]
                hit = [(j, gi) for j, gi in enumerate(chunk) if ids_all[gi] in pickset]
                if not hit:
                    continue
                inp = np.stack([C.build_refiner_input(dc.rgb_crop[i], dc.prob_crop[i])
                                for i in chunk], axis=0)
                x = torch.from_numpy(np.ascontiguousarray(inp, dtype=np.float32))
                with torch.inference_mode():
                    logits = model(x)
                    probs = torch.sigmoid(logits.float())[:, 0].cpu().numpy()
                for j, gi in hit:
                    sid = ids_all[gi]
                    p512 = np.asarray(dc.prob512[gi], dtype=np.float32)
                    geom = roi_geometry(p512, C.ROI_PROPOSAL_THRESHOLD)
                    refined = probs[j]
                    p_cand, valid = C.fuse_full_field(p512, refined, geom)
                    m_cand = (p_cand >= SEG).astype(np.uint8)
                    m_glob = (p512 >= SEG).astype(np.uint8)
                    gt = full_field_gt(str(man.loc[sid, "mask_path"]))
                    dg = dice_fn(binary_confusion_counts(m_glob, gt))
                    dcand = dice_fn(binary_confusion_counts(m_cand, gt))
                    delta = dcand - dg
                    frozen = lab_lookup[sid]
                    max_metric_diff = max(max_metric_diff,
                                          abs(dcand - frozen["candidate_refined_dice"]))
                    max_delta_diff = max(max_delta_diff, abs(delta - frozen["delta_dice"]))
                    # mask must be identical (bit-exact)
                    if C.sha256_array(m_cand) != frozen["candidate_mask_sha256"]:
                        mask_mismatches += 1
                    results.append({
                        "domain": d, "sample_id": sid, "outer_fold": k,
                        "replay_candidate_dice": dcand,
                        "frozen_candidate_dice": frozen["candidate_refined_dice"],
                        "replay_delta_dice": delta,
                        "frozen_delta_dice": frozen["delta_dice"],
                        "mask_identical": C.sha256_array(m_cand) == frozen["candidate_mask_sha256"],
                    })

    sub = pd.DataFrame(results)
    pd.DataFrame([{"domain": d, "sample_id": s} for d, s in subset_flat]).to_csv(
        ROOT / "reports/tables/phase25c_determinism_subset.csv", index=False)

    all_ok = (mask_mismatches == 0 and max_metric_diff <= metric_tol
              and max_delta_diff <= metric_tol and len(sub) == 64)

    C.jdump({
        "artifact": "phase25c_oof_determinism",
        "phase": "25C",
        "method": C.METHOD,
        "subset_size": len(sub),
        "subset_per_domain": SUB_PER_DOMAIN,
        "subset_selection": "evenly spaced by sorted sample_id, outcome-independent",
        "replay_method": "replayed inside the ORIGINAL canonical fold-filtered batch of 8",
        "prob_tolerance": prob_tol,
        "metric_tolerance": metric_tol,
        "max_candidate_dice_diff": max_metric_diff,
        "max_delta_dice_diff": max_delta_diff,
        "candidate_mask_mismatches": mask_mismatches,
        "n_all_identical": int(sub["mask_identical"].sum()),
        "all_pass": bool(all_ok),
        "verdict": ("PHASE25C_OOF_DETERMINISM_PASS" if all_ok
                    else "PHASE25C_BLOCKED__PAIRED_GAIN_CONTRACT_VIOLATION"),
        "test_reads": 0,
        "generated_utc": UTC,
    }, AUD / "phase25c_oof_determinism.json")

    print(f"subset={len(sub)} mask_mismatches={mask_mismatches} "
          f"max_dice_diff={max_metric_diff:.2e} max_delta_diff={max_delta_diff:.2e}")
    print("verdict:", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
