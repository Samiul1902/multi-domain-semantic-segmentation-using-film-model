#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 FUTURE interpretability execution harness (SPECIFICATION SOURCE - DO NOT RUN).

Classification: PRE_EXECUTION_FEATURE_ATTRIBUTION_VISUAL_INTERPRETABILITY_SPECIFICATION__
                EXECUTION_HARNESS
Revision: ra_medfilm_barr_phase35_interpretability_v1_0

!! ZERO-EXECUTION GUARD !!
Importing this module performs NO model construction, NO checkpoint load, NO forward, NO
backward, NO Grad-CAM, NO router attribution and NO raw-image read. All work lives in main(),
gated on PHASE35_EXECUTE=1.

Protected data: ROUTER_HOLDOUT raw images/GT and TEST images/GT are FORBIDDEN. Primary visual
execution may read ONLY the 64 authorized VAL gallery images, and ZERO ground truth.

Run (only after a separate execution authorization):
    PHASE35_EXECUTE=1 python scripts/analysis/phase35_interpretability_execution_v1_0.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from collections import OrderedDict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if not ((REPO_ROOT / "src").is_dir() and (REPO_ROOT / "scripts").is_dir()):
    raise RuntimeError(f"repository root resolution failed: {REPO_ROOT}")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "analysis"))

import phase35_interpretability_common_v1_0 as C  # noqa: E402

ROOT = REPO_ROOT
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
GATE_ENV = "PHASE35_EXECUTE"

FORBIDDEN_PATH_TOKENS = ("router_holdout", "/test", "\\test")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def guard_no_protected_data(paths):
    """Fail closed if any candidate path looks like ROUTER_HOLDOUT or TEST data."""
    for p in paths:
        low = str(p).lower().replace("\\", "/")
        if any(tok in low for tok in FORBIDDEN_PATH_TOKENS):
            raise RuntimeError(f"PROTECTED-DATA GUARD TRIPPED: {p}")


# --------------------------------------------------------------------------- #
# gates
# --------------------------------------------------------------------------- #
def gate_1_authority() -> dict:
    freeze = json.loads((AUD / "phase35_preexecution_source_freeze_v1_0.json")
                        .read_text(encoding="utf-8"))
    bad = []
    for k, v in freeze["frozen_sources"].items():
        obs = sha256_file(ROOT / v["path"])
        if obs != v["sha256"]:
            bad.append({"key": k, "expected": v["sha256"], "observed": obs})
    if bad:
        raise RuntimeError(f"FAIL-CLOSED authority mismatch: {bad}")
    return {"n_sources": len(freeze["frozen_sources"]), "all_match": True}


def gate_2_environment() -> dict:
    import platform

    import torch
    prop = torch.cuda.get_device_properties(0) if torch.cuda.is_available() else None
    env = {"os": platform.platform(), "python": platform.python_version(),
           "torch": torch.__version__, "cuda_runtime": torch.version.cuda,
           "gpu": prop.name if prop else None,
           "cc": f"{prop.major}.{prop.minor}" if prop else None,
           "vram_bytes": prop.total_memory if prop else None}
    if env["gpu"] != "NVIDIA GeForce RTX 3060 Ti" or env["torch"] != "2.6.0+cu124":
        raise RuntimeError(f"FAIL-CLOSED environment mismatch: {env}")
    return env


def gate_3_checkpoints() -> dict:
    out = {}
    for cid, spec in C.COMPONENTS.items():
        obs = sha256_file(ROOT / spec["checkpoint"])
        if obs != spec["checkpoint_sha256"]:
            raise RuntimeError(f"FAIL-CLOSED checkpoint mismatch {cid}")
        out[cid] = obs
    return out


def gate_4_gallery_population() -> dict:
    """Verify the 64-case gallery is unique, 16/domain and has ZERO ROUTER_HOLDOUT/TEST overlap."""
    import pandas as pd
    g = pd.read_csv(ROOT / C.GALLERY_PATH)
    counts = g["dataset"].value_counts().to_dict()
    holdout = pd.read_csv(ROOT / "reports/audits/phase24_router_split_manifest.csv")
    holdout_ids = set(holdout["sample_id"].astype(str))
    test_manifest = ROOT / "manifests" / "phase4_v3" / "test.csv"
    test_ids = (set(pd.read_csv(test_manifest)["sample_id"].astype(str))
                if test_manifest.exists() else set())
    val_ids = set(pd.read_csv(ROOT / "manifests/phase4_v3/val.csv")["sample_id"].astype(str))
    ids = set(g["sample_id"].astype(str))
    res = {"n": int(len(g)), "unique": int(g["sample_id"].nunique()),
           "per_domain": counts, "in_val808": len(ids - val_ids) == 0,
           "router_holdout_overlap": len(ids & holdout_ids),
           "test_overlap": len(ids & test_ids)}
    if res["router_holdout_overlap"] or res["test_overlap"]:
        raise RuntimeError("BLOCKED: gallery case belongs to ROUTER_HOLDOUT or TEST")
    return res


# --------------------------------------------------------------------------- #
# I1 FiLM parameter interpretability
# --------------------------------------------------------------------------- #
def run_film_analysis(model) -> dict:
    """Static FiLM gamma/beta analysis via the canonical film_parameters_for_tasks()."""
    import numpy as np
    import torch
    out = {"per_task_site": {}, "pairwise": {}}
    per_task = {}
    for dom, tid in C.DOMAIN_TASK_ID.items():
        params = model.film_parameters_for_tasks(
            torch.tensor([tid], dtype=torch.long, device=next(model.parameters()).device))
        per_task[dom] = {}
        for site, (gamma, beta) in params.items():
            g = gamma.detach().float().cpu().numpy().reshape(-1)
            b = beta.detach().float().cpu().numpy().reshape(-1)
            per_task[dom][site] = {"gamma": g, "beta": b}
            out["per_task_site"][f"{dom}|{site}"] = {
                "mean_gamma": float(np.mean(g)), "mean_abs_gamma": float(np.mean(np.abs(g))),
                "std_gamma": float(np.std(g)), "l2_norm_gamma": float(np.linalg.norm(g)),
                "mean_beta": float(np.mean(b)), "mean_abs_beta": float(np.mean(np.abs(b))),
                "std_beta": float(np.std(b)), "l2_norm_beta": float(np.linalg.norm(b))}
    doms = list(C.DOMAIN_TASK_ID)
    for i in range(len(doms)):
        for j in range(i + 1, len(doms)):
            a, b = doms[i], doms[j]
            for site in C.FILM_SITES:
                ga, gb = per_task[a][site]["gamma"], per_task[b][site]["gamma"]
                ba, bb = per_task[a][site]["beta"], per_task[b][site]["beta"]
                out["pairwise"][f"{a}|{b}|{site}"] = {
                    "l2_distance_gamma": float(np.linalg.norm(ga - gb)),
                    "cosine_similarity_gamma": float(
                        np.dot(ga, gb) / (np.linalg.norm(ga) * np.linalg.norm(gb) + 1e-12)),
                    "l2_distance_beta": float(np.linalg.norm(ba - bb)),
                    "cosine_similarity_beta": float(
                        np.dot(ba, bb) / (np.linalg.norm(ba) * np.linalg.norm(bb) + 1e-12))}
    return out


# --------------------------------------------------------------------------- #
# I2 segmentation Grad-CAM
# --------------------------------------------------------------------------- #
def gradcam(model, layer_module, target_layer_name, images, task_ids, logits):
    """One Grad-CAM map per (sample, target layer) using the frozen algorithm."""
    import torch
    captured = {}

    def hook(_m, _i, output):
        out = output[0] if isinstance(output, tuple) else output
        captured["act"] = out
        captured["act"].retain_grad()

    h = layer_module.register_forward_hook(hook)
    try:
        m_pred = (torch.sigmoid(logits.float()) >= C.T_ROI_PROPOSAL).float()
        foreground = m_pred.sum() >= 1
        if bool(foreground):
            T = logits[m_pred.bool()].mean()
        else:
            T = logits.mean()
        model.zero_grad(set_to_none=True)
        T.backward()
        A = captured["act"]
        dT_dA = A.grad
        alpha = dT_dA.mean(dim=(2, 3), keepdim=True)
        cam = torch.relu((alpha * A).sum(dim=1, keepdim=True))
        cam = torch.nn.functional.interpolate(cam, size=(512, 512), mode="bilinear",
                                              align_corners=C.GRADCAM_ALGORITHM["align_corners"])
        c = cam[0, 0]
        rng = c.max() - c.min()
        cam = (c - c.min()) / rng if float(rng) > 0 else torch.zeros_like(c)
        return {"cam": cam.detach().float().cpu().numpy(),
                "empty_mask_fallback_used": not bool(foreground),
                "target_layer": target_layer_name}
    finally:
        h.remove()


def saliency_self_consistency(cam, m_pred, m_roi) -> dict:
    import numpy as np
    total = float(cam.sum())
    if total == 0:
        return {"foreground_saliency_mass_fraction": None,
                "roi_saliency_mass_fraction": None, "ZERO_CAM": True,
                "cam_peak_inside_predicted_foreground": None,
                "cam_peak_inside_roi_proposal": None}
    peak = np.unravel_index(int(np.argmax(cam)), cam.shape)
    return {"foreground_saliency_mass_fraction": float((cam * m_pred).sum() / total),
            "roi_saliency_mass_fraction": float((cam * m_roi).sum() / total),
            "ZERO_CAM": False,
            "cam_peak_inside_predicted_foreground": bool(m_pred[peak]),
            "cam_peak_inside_roi_proposal": bool(m_roi[peak])}


# --------------------------------------------------------------------------- #
# I4 router Gradient x Input attribution
# --------------------------------------------------------------------------- #
def router_gradient_x_input(model, features, task_ids):
    """a_j = x_j * d(delta_hat)/d(x_j) on the canonical 202-D numeric features."""
    import numpy as np
    import torch
    x = features.clone().detach().requires_grad_(True)
    delta = model(x, task_ids)
    model.zero_grad(set_to_none=True)
    delta.sum().backward()
    a = (x.grad * x).detach().float().cpu().numpy()[0]
    abs_a = np.abs(a)
    denom = float(abs_a.sum())
    groups = OrderedDict()
    idx = 0
    for gname, width in C.ROUTER_FEATURE_GROUPS.items():
        sl = slice(idx, idx + width)
        groups[gname] = {"signed_group": float(a[sl].sum()),
                         "absolute_group": float(abs_a[sl].sum()),
                         "normalized_absolute_share": (float(abs_a[sl].sum()) / denom
                                                       if denom > 0 else None)}
        idx += width
    scalars = {name: {"signed": float(a[192 + k]), "absolute": float(abs_a[192 + k])}
               for k, name in enumerate(C.ROUTER_SCALAR_FEATURES)}
    return {"signed": a.tolist(), "absolute": abs_a.tolist(), "groups": groups,
            "scalars": scalars,
            "ZERO_ROUTER_GRAD_ATTRIBUTION": denom == 0,
            "normalized_absolute_share": None if denom == 0 else abs_a / denom}


# --------------------------------------------------------------------------- #
# orchestration
# --------------------------------------------------------------------------- #
def main() -> int:
    if os.environ.get(GATE_ENV) != "1":
        print("PHASE35 EXECUTION NOT AUTHORIZED - zero-execution guard active.")
        return 2
    guard_no_protected_data([C.COMPONENTS["G"]["checkpoint"], C.GALLERY_PATH])
    report = OrderedDict([("revision", C.REVISION), ("phase_id", C.PHASE_ID),
                          ("started_utc", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())),
                          ("gate_1_authority", gate_1_authority()),
                          ("gate_2_environment", gate_2_environment()),
                          ("gate_3_checkpoints", gate_3_checkpoints()),
                          ("gate_4_gallery_population", gate_4_gallery_population()),
                          ("read_counters", {"raw_val_images": 0, "val_gt": 0,
                                             "router_holdout_raw": 0, "test_reads": 0}),
                          ("families", {k: "PENDING" for k in C.EVIDENCE_FAMILIES})])
    out = AUD / "phase35_interpretability_execution_results_v1_0.json"
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
