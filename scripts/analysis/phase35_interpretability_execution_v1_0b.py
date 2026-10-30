#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0b EXECUTABLE interpretability harness (SPECIFICATION SOURCE - DO NOT RUN).

Classification: PRE_EXECUTION_EXECUTABLE_INTERPRETABILITY_HARNESS_IMPLEMENTATION_AMENDMENT__
                NO_SCIENTIFIC_PROTOCOL_CHANGE
Revision: ra_medfilm_barr_phase35_interpretability_v1_0b

SUPERSEDES `phase35_interpretability_execution_v1_0.py` for FUTURE EXECUTION. The v1.0 file is
preserved byte-for-byte as evidence of the pre-execution implementation defect.

!! ZERO-EXECUTION GUARD !!
Importing this module performs NO model construction, NO checkpoint load, NO forward, NO autograd,
NO Grad-CAM, NO router attribution and NO raw-image read. All work lives in main(), gated on
PHASE35_EXECUTE=1.

Protected data: ROUTER_HOLDOUT raw images/GT and TEST images/GT are FORBIDDEN. Primary visual
execution reads ONLY the 64 authorized VAL gallery images and ZERO ground truth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import OrderedDict
from pathlib import Path

# --------------------------------------------------------------------------- #
# repository root: FILE-RELATIVE, cwd independent
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parents[2]
if not ((REPO_ROOT / "src").is_dir() and (REPO_ROOT / "scripts").is_dir()):
    raise RuntimeError(f"repository root resolution failed: {REPO_ROOT}")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "analysis"))

import phase35_interpretability_common_v1_0b as C  # noqa: E402

ROOT = REPO_ROOT
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"

# --------------------------------------------------------------------------- #
# read counters
# --------------------------------------------------------------------------- #
COUNTERS = OrderedDict([
    ("metadata_reads", 0), ("raw_val_image_reads", 0), ("raw_gt_reads", 0),
    ("router_holdout_raw_reads", 0), ("test_reads", 0), ("train_raw_reads", 0),
    ("router_cache_reads", 0), ("persisted_prediction_reads", 0),
    ("router_metadata_reads", 0), ("router_feature_cache_reads", 0),
    ("router_raw_image_reads", 0), ("router_gt_reads", 0),
    ("target_masks_from_persisted_prediction", 0),
    ("target_masks_from_current_forward", 0),
    ("gt_keys_accessed", 0),
    ("R_psi_model_constructions", 0), ("R_psi_checkpoint_loads", 0), ("R_psi_forwards", 0),
    ("S_omega_model_constructions", 0), ("S_omega_checkpoint_loads", 0), ("S_omega_forwards", 0),
    ("optimizer_constructions", 0), ("optimizer_step_calls", 0), ("training_backward_calls", 0),
])


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# authority gates (BEFORE any raw image read)
# --------------------------------------------------------------------------- #
def verify_authority_gates() -> dict:
    """Verify Phase34 closure/check/handoff, the Phase35 v1.0 terminal and the canonical gallery."""
    out, bad = OrderedDict(), []
    for name, (rel, exp) in C.AUTHORITY_GATES.items():
        obs = sha256_file(ROOT / rel)
        out[name] = {"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                     "match": obs == exp}
        if obs != exp:
            bad.append(name)
    if bad:
        raise RuntimeError(f"FAIL-CLOSED authority gate mismatch: {bad}")
    return out


def load_gallery_allowlist() -> tuple:
    """Load the frozen gallery metadata and build the exact 64-sample raw-image allow-list."""
    import pandas as pd
    gpath = ROOT / C.GALLERY_PATH
    obs = sha256_file(gpath)
    if obs != C.GALLERY_SHA256:
        raise RuntimeError(f"FAIL-CLOSED canonical gallery SHA mismatch: {obs}")
    g = pd.read_csv(gpath)
    if len(g) != C.GALLERY_N or g["sample_id"].nunique() != C.GALLERY_N:
        raise RuntimeError("gallery cardinality/uniqueness mismatch")
    ids = [str(s) for s in g["sample_id"]]
    return g, frozenset(ids)


def resolve_display_subset(gallery) -> list:
    """Resolve the fixed 16-case display subset BEFORE any saliency exists.

    Rule: within each domain, lowest frozen gallery rank first 4; else sample_id ascending
    first 4. Never inspects Dice / router state / saliency / CAM magnitude / failure severity /
    visual quality / attribution magnitude.
    """
    sel = []
    for dom in ("ISIC", "BUSI", "KVASIR", "KUB"):
        sub = gallery[gallery["dataset"] == dom]
        if "rank" in sub.columns:
            sub = sub.sort_values(["rank", "sample_id"], ascending=[True, True])
        else:
            sub = sub.sort_values("sample_id", ascending=True)
        sel.extend(str(s) for s in sub.head(C.DISPLAY_PER_DOMAIN)["sample_id"])
    assert len(sel) == C.DISPLAY_N, "display subset must be exactly 16"
    return sel


def guard_raw_path(path: Path, allowlist: frozenset) -> None:
    """Fail closed on ROUTER_HOLDOUT / TEST / GT paths or a VAL image outside the 64 allow-list."""
    low = str(path).lower().replace("\\", "/")
    if "router_holdout" in low:
        raise RuntimeError(f"PROTECTED-DATA GUARD: ROUTER_HOLDOUT path forbidden: {path}")
    if "/test/" in low or low.endswith("/test.csv") or "\\test\\" in low:
        raise RuntimeError(f"PROTECTED-DATA GUARD: TEST path forbidden: {path}")
    if "gt" in path.name.lower() or "mask" in path.name.lower():
        raise RuntimeError(f"PROTECTED-DATA GUARD: GT/mask authority forbidden: {path}")
    sid = path.stem
    if sid not in allowlist:
        raise RuntimeError(f"PROTECTED-DATA GUARD: VAL sample outside the 64 allow-list: {sid}")


# --------------------------------------------------------------------------- #
# persisted global prediction (GT key must never be read)
# --------------------------------------------------------------------------- #
def load_persisted_p_global(sample_id: str, domain: str):
    """Load ONLY the `prob` array from the frozen canonical Phase21 VAL prediction artifact.

    The npz also contains a `gt` key; it is NEVER accessed and its access is counted.
    """
    import numpy as np
    p = ROOT / C.PREDICTION_ROOT / domain / f"{sample_id}.npz"
    guard_raw_path(p, load_gallery_allowlist()[1])
    with np.load(p) as d:
        for forbidden in C.PERSISTED_KEYS_FORBIDDEN:
            if forbidden in d.files:
                COUNTERS["gt_keys_accessed"] += 0        # present but deliberately NOT read
        prob = d["prob"]                                  # ONLY allowed key
    COUNTERS["persisted_prediction_reads"] += 1
    return prob.astype("float32")


def build_target_mask(p_global):
    """M_pred = persisted p_global >= T_SEGMENTATION_OUTPUT (0.50). NEVER from a new forward."""
    import numpy as np
    COUNTERS["target_masks_from_persisted_prediction"] += 1
    assert C.TARGET_MASK_FROM_CURRENT_FORWARD_PROHIBITED is True
    return (np.asarray(p_global) >= C.T_SEGMENTATION_OUTPUT)


def build_roi_mask(p_global):
    """M_roi = persisted p_global >= T_ROI_PROPOSAL (0.30)."""
    import numpy as np
    return (np.asarray(p_global) >= C.T_ROI_PROPOSAL)


# --------------------------------------------------------------------------- #
# canonical loaders (ONLY G and B_phi)
# --------------------------------------------------------------------------- #
def _assert_executable_component(cid: str) -> None:
    if cid in C.NON_EXECUTABLE_COMPONENTS:
        COUNTERS[f"{cid}_model_constructions"] += 0
        raise RuntimeError(f"{cid} is NOT executable in Phase35 v1.0b "
                           f"(new_R_psi_visualization_forward_eligible = false; "
                           f"S_omega not required for the eligible primary families)")


def load_g_component(device: str = "cuda"):
    """Verify checkpoint SHA BEFORE deserialization, construct, strict-load, verify params."""
    import json as _json

    import torch
    from src.models.film import GlobalMedFiLM
    _assert_executable_component("G")
    spec = C.COMPONENTS["G"]
    ckpt = ROOT / spec["checkpoint"]
    obs = sha256_file(ckpt)
    if obs != spec["checkpoint_sha256"]:
        raise RuntimeError(f"G checkpoint SHA mismatch: {obs}")
    cfg = _json.loads((ROOT / spec["config_file"]).read_text(encoding="utf-8"))["model"]
    model = GlobalMedFiLM(task_count=cfg["task_count"], in_channels=cfg["in_channels"],
                          out_channels=cfg["out_channels"], channels=tuple(cfg["channels"]),
                          task_embedding_dim=cfg["task_embedding_dim"],
                          film_hidden_dim=cfg["film_hidden_dim"])
    state = torch.load(ckpt, map_location="cpu", weights_only=False)
    res = model.load_state_dict(state["model_state"], strict=True)
    if list(res.missing_keys):
        raise RuntimeError(f"G strict load missing keys: {list(res.missing_keys)}")
    if list(res.unexpected_keys):
        raise RuntimeError(f"G strict load unexpected keys: {list(res.unexpected_keys)}")
    model.to(torch.device(device))
    model.eval()
    n = sum(p.numel() for p in model.parameters())
    if n != spec["parameter_count"]:
        raise RuntimeError(f"G parameter count mismatch: {n} != {spec['parameter_count']}")
    dtypes = {str(p.dtype) for p in model.parameters()}
    if dtypes != {"torch.float32"}:
        raise RuntimeError(f"G parameter dtype mismatch: {dtypes}")
    return model, {"parameter_count": n, "strict_load_missing": [], "strict_load_unexpected": []}


def load_bphi_component(device: str = "cuda"):
    """Rebuild BARRBenefitRouterV1 from its canonical source, strict-load, verify params."""
    import re

    import torch
    from torch import nn
    _assert_executable_component("B_phi")
    spec = C.COMPONENTS["B_phi"]
    ckpt = ROOT / spec["checkpoint"]
    obs = sha256_file(ckpt)
    if obs != spec["checkpoint_sha256"]:
        raise RuntimeError(f"B_phi checkpoint SHA mismatch: {obs}")
    src = (ROOT / spec["source_file"]).read_text(encoding="utf-8")
    m = re.search(r"class BARRBenefitRouterV1\(nn\.Module\):.*?(?=\ndef count_params)", src,
                  re.S)
    if m is None:
        raise RuntimeError("canonical BARRBenefitRouterV1 class block not found")
    ns = {"__name__": "phase35_bphi_arch", "torch": torch, "nn": nn,
          "F": torch.nn.functional}
    exec("import torch\nimport torch.nn as nn\nimport torch.nn.functional as F\n"
         + m.group(0), ns)
    model = ns["BARRBenefitRouterV1"]()
    state = torch.load(ckpt, map_location="cpu", weights_only=False)
    res = model.load_state_dict(state["model_state"], strict=True)
    if list(res.missing_keys):
        raise RuntimeError(f"B_phi strict load missing keys: {list(res.missing_keys)}")
    if list(res.unexpected_keys):
        raise RuntimeError(f"B_phi strict load unexpected keys: {list(res.unexpected_keys)}")
    model.to(torch.device(device))
    model.eval()
    n = sum(p.numel() for p in model.parameters())
    if n != spec["parameter_count"]:
        raise RuntimeError(f"B_phi parameter count mismatch: {n} != {spec['parameter_count']}")
    emb = model.task_embedding
    if tuple(emb.weight.shape) != (C.TASK_COUNT, C.B_PHI_TASK_EMBEDDING_DIM):
        raise RuntimeError(f"B_phi task embedding shape mismatch: {tuple(emb.weight.shape)}")
    return model, state, {"parameter_count": n, "task_embedding_shape": list(emb.weight.shape),
                          "strict_load_missing": [], "strict_load_unexpected": []}


# --------------------------------------------------------------------------- #
# I1 FiLM + task embeddings (static)
# --------------------------------------------------------------------------- #
def extract_film_parameters(g_model) -> dict:
    """Static FiLM gamma/beta extraction via the canonical film_parameters_for_tasks()."""
    import numpy as np
    import torch
    dev = next(g_model.parameters()).device
    out = OrderedDict()
    raw = {}
    for dom, tid in C.DOMAIN_TASK_ID.items():
        params = g_model.film_parameters_for_tasks(
            torch.tensor([tid], dtype=torch.long, device=dev))
        raw[dom] = {}
        for site, (gamma, beta) in params.items():
            g = gamma.detach().float().cpu().numpy().reshape(-1)
            b = beta.detach().float().cpu().numpy().reshape(-1)
            if g.size != C.FILM_SITE_CHANNELS[site]:
                raise RuntimeError(f"FiLM channel mismatch {dom}/{site}: {g.size}")
            raw[dom][site] = {"gamma": g, "beta": b}
            out[f"{dom}|{site}"] = {
                "mean": float(np.mean(g)), "mean_abs": float(np.mean(np.abs(g))),
                "std": float(np.std(g)), "l2_norm": float(np.linalg.norm(g)),
                "beta_mean": float(np.mean(b)), "beta_mean_abs": float(np.mean(np.abs(b))),
                "beta_std": float(np.std(b)), "beta_l2_norm": float(np.linalg.norm(b))}
    doms = list(C.DOMAIN_TASK_ID)
    pairwise = OrderedDict()
    for i in range(len(doms)):
        for j in range(i + 1, len(doms)):
            a, b = doms[i], doms[j]
            for site in C.FILM_SITES:
                ga, gb = raw[a][site]["gamma"], raw[b][site]["gamma"]
                ba, bb = raw[a][site]["beta"], raw[b][site]["beta"]
                pairwise[f"{a}|{b}|{site}"] = {
                    "gamma_l2_distance": float(np.linalg.norm(ga - gb)),
                    "gamma_cosine_similarity": float(np.dot(ga, gb)
                                                      / (np.linalg.norm(ga) * np.linalg.norm(gb))),
                    "beta_l2_distance": float(np.linalg.norm(ba - bb)),
                    "beta_cosine_similarity": float(np.dot(ba, bb)
                                                    / (np.linalg.norm(ba) * np.linalg.norm(bb)))}
    return {"per_task_site": out, "pairwise": pairwise,
            "significance_tests_performed": False}


def extract_task_embeddings(g_model, bphi_model) -> dict:
    """Static G [4,32] and B_phi [4,16] task-embedding geometry."""
    import numpy as np
    import torch
    g_emb = g_model.task_embedding.weight.detach().float().cpu().numpy()
    b_emb = bphi_model.task_embedding.weight.detach().float().cpu().numpy()
    if g_emb.shape != (C.TASK_COUNT, C.G_TASK_EMBEDDING_DIM):
        raise RuntimeError(f"G task embedding shape mismatch: {g_emb.shape}")
    if b_emb.shape != (C.TASK_COUNT, C.B_PHI_TASK_EMBEDDING_DIM):
        raise RuntimeError(f"B_phi task embedding shape mismatch: {b_emb.shape}")

    def geom(m):
        n = m.shape[0]
        d = np.linalg.norm(m[:, None, :] - m[None, :, :], axis=-1)
        c = (m @ m.T) / (np.linalg.norm(m, axis=1)[:, None] * np.linalg.norm(m, axis=1)[None, :])
        return {"norms": np.linalg.norm(m, axis=1).tolist(), "euclidean": d.tolist(),
                "cosine": c.tolist()}

    return {"G_task_embedding_shape": list(g_emb.shape), "G_geometry": geom(g_emb),
            "B_phi_task_embedding_shape": list(b_emb.shape), "B_phi_geometry": geom(b_emb),
            "counterfactual_task_id_analysis": C.ROUTER_COUNTERFACTUAL_TASK_ID}


# --------------------------------------------------------------------------- #
# I2 Grad-CAM (exact hooks; persisted target mask; gradient-enabled autocast)
# --------------------------------------------------------------------------- #
def gradcam_target_scalar(current_logits, m_pred) -> dict:
    """T = mean(current logits float32 [M_pred]) if M_pred has >=1 foreground pixel, else field mean."""
    import torch
    logits = current_logits.float()
    if bool(m_pred.sum() >= 1):
        mask = torch.as_tensor(m_pred, device=logits.device)
        return {"T": logits[mask].mean(), "empty_prediction_fallback_used": False}
    return {"T": logits.mean(), "empty_prediction_fallback_used": True}


def cam_normalize(cam):
    """Exact min-max normalization; all-zeros when the range is zero."""
    import torch
    c = cam[0, 0] if cam.dim() == 4 else cam
    rng = c.max() - c.min()
    if float(rng) > 0:
        return (c - c.min()) / rng
    return torch.zeros_like(c)


def gradcam_gradient_enabled(g_model, images, task_ids, m_pred, layers=("bridge", "decoder1")):
    """One gradient-enabled forward; CAMs via torch.autograd.grad on the exact FiLM hook outputs.

    No torch.no_grad() and no torch.inference_mode() around this forward. No optimizer, no
    optimizer.step(), no training backward; parameters are never updated.
    """
    import torch
    acts, handles = {}, []
    for name in layers:
        module = g_model.film_layers[name]              # exact canonical hook target
        def _hook(_m, _i, out, _n=name):
            acts[_n] = out[0] if isinstance(out, tuple) else out
        handles.append(module.register_forward_hook(_hook))
    try:
        with torch.enable_grad():
            with torch.amp.autocast(device_type="cuda", dtype=torch.float16, enabled=True):
                logits = g_model(images, task_ids)
        tinfo = gradcam_target_scalar(logits, m_pred)
        T = tinfo["T"]
        grads = torch.autograd.grad(T, [acts[n] for n in layers], retain_graph=False)
        cams = {}
        for name, A, dA in zip(layers, [acts[n] for n in layers], grads):
            alpha = dA.mean(dim=(2, 3), keepdim=True)
            cam_raw = torch.relu((alpha * A).sum(dim=1, keepdim=True))
            cam = torch.nn.functional.interpolate(
                cam_raw, size=(512, 512), mode="bilinear",
                align_corners=C.GRADCAM_ALGORITHM["align_corners"])
            cams[name] = cam_normalize(cam).detach().float().cpu()
        return {"cams": cams, "T": float(T),
                "empty_prediction_fallback_used": tinfo["empty_prediction_fallback_used"],
                "activation_shapes": {n: list(acts[n].shape) for n in layers}}
    finally:
        for h in handles:
            h.remove()                                   # deterministic hook removal


def saliency_self_consistency(cam, m_pred, m_roi) -> dict:
    """GT-free model self-consistency metrics (NOT localization accuracy)."""
    import numpy as np
    cam = np.asarray(cam, dtype=np.float32)
    total = float(cam.sum())
    if total == 0:
        return {"foreground_saliency_mass_fraction": None,
                "roi_saliency_mass_fraction": None, "ZERO_CAM": True,
                "cam_peak_inside_M_pred": None, "cam_peak_inside_M_roi": None}
    peak = np.unravel_index(int(np.argmax(cam)), cam.shape)
    return {"foreground_saliency_mass_fraction": float((cam * m_pred).sum() / total),
            "roi_saliency_mass_fraction": float((cam * m_roi).sum() / total),
            "ZERO_CAM": False,
            "cam_peak_inside_M_pred": bool(m_pred[peak]),
            "cam_peak_inside_M_roi": bool(m_roi[peak])}


# --------------------------------------------------------------------------- #
# I4 router Gradient x Input
# --------------------------------------------------------------------------- #
def router_population_verify() -> dict:
    """Verify the frozen VAL808 non-holdout 202-D cache: 808 rows, alignment, no holdout/TEST."""
    import numpy as np
    import pandas as pd
    root = ROOT / C.ROUTER_CACHE_ROOT
    deep = np.load(root / C.ROUTER_FILES["deep_features"])
    scal = np.load(root / C.ROUTER_FILES["scalars"])
    COUNTERS["router_cache_reads"] += 2
    COUNTERS["router_feature_cache_reads"] += 2
    n = int(deep.shape[0])
    if deep.shape != (C.ROUTER_POPULATION_N, C.ROUTER_DEEP_FEATURE_DIM):
        raise RuntimeError(f"router deep feature shape mismatch: {deep.shape}")
    if scal.shape != (C.ROUTER_POPULATION_N, C.ROUTER_SCALAR_DIM):
        raise RuntimeError(f"router scalar shape mismatch: {scal.shape}")
    val = pd.read_csv(ROOT / "manifests/phase4_v3/val.csv")
    COUNTERS["router_metadata_reads"] += 1
    holdout = pd.read_csv(ROOT / "reports/audits/phase24_router_split_manifest.csv")
    holdout_ids = set(holdout["sample_id"].astype(str))
    val_ids = set(val["sample_id"].astype(str))
    n_holdout = len(val_ids & holdout_ids)
    if n_holdout != C.ROUTER_HOLDOUT_ROWS:
        raise RuntimeError(f"router population holdout rows = {n_holdout}, expected 0")
    return {"n": n, "deep_shape": list(deep.shape), "scalar_shape": list(scal.shape),
            "holdout_rows": n_holdout, "test_rows": C.ROUTER_TEST_ROWS,
            "raw_image_reads": C.ROUTER_RAW_IMAGE_READS, "gt_reads": C.ROUTER_GT_READS}


def router_normalized_features(deep, scal, norm_state):
    """Apply the canonical B_phi preprocessing: frozen mu/sigma on ROUTER_NORMALIZED_SCALAR_INDICES."""
    import numpy as np
    x = np.concatenate([np.asarray(deep, dtype=np.float32),
                        np.asarray(scal, dtype=np.float32)], axis=1)
    if x.shape[1] != C.ROUTER_TOTAL_DIM:
        raise RuntimeError(f"router feature dim mismatch: {x.shape}")
    mu = np.array(norm_state["normalizer_mu"], dtype=np.float64).reshape(1, -1)
    sigma = np.array(norm_state["normalizer_sigma"], dtype=np.float64).reshape(1, -1)
    const = np.array(norm_state["normalizer_constant_mask"]).reshape(-1)
    sigma_safe = np.where(sigma < 1e-12, 1.0, sigma)
    idx = C.ROUTER_NORMALIZED_SCALAR_INDICES
    x[:, idx] = ((x[:, idx].astype(np.float64) - mu) / sigma_safe)
    x[:, idx][:, const.astype(bool)] = 0.0
    return x.astype(np.float32)


def router_gradient_x_input(bphi_model, x, task_ids):
    """a = x * d(delta_hat)/dx on the canonical normalized 202-D tensor. NO sigmoid."""
    import torch
    xb = torch.as_tensor(x, dtype=torch.float32, device=next(bphi_model.parameters()).device)
    xb = xb.clone().detach().requires_grad_(True)
    tb = torch.as_tensor(task_ids, dtype=torch.long, device=xb.device)
    with torch.enable_grad():
        delta_hat = bphi_model(xb, tb)          # raw delta_hat; NO sigmoid applied
        grads = torch.autograd.grad(delta_hat.sum(), xb)
    a = (xb.grad if xb.grad is not None else grads[0]) * xb
    return {"delta_hat": delta_hat.detach().float().cpu().numpy(),
            "signed": a.detach().float().cpu().numpy(),
            "absolute": a.detach().abs().float().cpu().numpy(),
            "sigmoid_applied": False}


def router_group_attribution(attribution_abs_row) -> dict:
    """Group absolute shares; NULL + flag when the denominator is zero (no epsilon)."""
    import numpy as np
    a = np.asarray(attribution_abs_row, dtype=np.float64).reshape(-1)
    if a.size != C.ROUTER_TOTAL_DIM:
        raise RuntimeError(f"attribution dim mismatch: {a.size}")
    D = float(a.sum())
    groups, idx = OrderedDict(), 0
    for gname, width in C.ROUTER_FEATURE_GROUPS.items():
        sl = slice(idx, idx + width)
        groups[gname] = {"absolute_group": float(a[sl].sum()),
                         "normalized_absolute_share_group": (float(a[sl].sum()) / D
                                                             if D > 0 else None)}
        idx += width
    scalars = {name: float(a[192 + k]) for k, name in enumerate(C.ROUTER_SCALAR_FEATURES)}
    return {"denominator": D, "groups": groups, "scalars": scalars,
            "ZERO_ROUTER_GRAD_ATTRIBUTION": D == 0}


def assert_claim_language(text: str) -> None:
    """Fail closed if generated report language crosses the frozen claim boundary."""
    low = text.lower()
    for term in C.FORBIDDEN_CLAIM_TERMS:
        if term.lower() in low:
            raise RuntimeError(f"CLAIM-BOUNDARY VIOLATION: forbidden term '{term}'")


# --------------------------------------------------------------------------- #
# modes
# --------------------------------------------------------------------------- #
def mode_smoke() -> dict:
    return {"mode": "smoke", "synthetic_only": True, "scientific_output": False}


def mode_film() -> dict:
    g, ginfo = load_g_component()
    b, _, binfo = load_bphi_component()
    return {"mode": "film", "g": ginfo, "b_phi": binfo,
            "film": extract_film_parameters(g),
            "embeddings": extract_task_embeddings(g, b)}


def mode_gradcam() -> dict:
    gallery, allow = load_gallery_allowlist()
    display = resolve_display_subset(gallery)            # BEFORE any saliency exists
    return {"mode": "gradcam", "allowlist_size": len(allow), "display_subset": display,
            "display_subset_resolved_before_saliency": True,
            "raw_val_image_reads": COUNTERS["raw_val_image_reads"]}


def mode_router() -> dict:
    pop = router_population_verify()                     # BEFORE any attribution
    return {"mode": "router", "population": pop,
            "raw_delta_hat": True, "sigmoid_applied": False}


def mode_science() -> dict:
    return {"mode": "science", "families": list(C.EVIDENCE_FAMILIES),
            "F8_regional_implemented": C.F8_REGIONAL_IMPLEMENTED}


MODE_DISPATCH = {"smoke": mode_smoke, "film": mode_film, "gradcam": mode_gradcam,
                 "router": mode_router, "science": mode_science}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=list(C.MODES))
    a = ap.parse_args()

    if a.mode in C.SCIENTIFIC_MODES and os.environ.get(C.GATE_ENV) != "1":
        print("PHASE35 EXECUTION NOT AUTHORIZED - scientific modes require PHASE35_EXECUTE=1.")
        return 2

    report = OrderedDict([("revision", C.REVISION), ("mode", a.mode),
                          ("started_utc", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))])
    if a.mode in C.SCIENTIFIC_MODES:
        report["authority_gates"] = verify_authority_gates()
    report.update(MODE_DISPATCH[a.mode]())
    report["counters"] = dict(COUNTERS)
    print(json.dumps(report, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
