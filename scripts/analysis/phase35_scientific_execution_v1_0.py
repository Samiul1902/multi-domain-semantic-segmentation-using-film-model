#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 35 v1.0 SCIENTIFIC EXECUTION DRIVER (prospective orchestrator).

Classification: PHASE35_PROSPECTIVE_SCIENTIFIC_EXECUTION_ORCHESTRATOR

This driver AUTHORED BEFORE any real-data read. It:
  * IMPORTS the frozen v1.0b commons (`phase35_interpretability_common_v1_0b`) and the frozen
    v1.0b scientific functions (`phase35_interpretability_execution_v1_0b`) and CALLS them;
  * IMPORTS the frozen v1.0h guarded/rank-safe Grad-CAM path and the frozen v1.0c smoke helpers
    where a strictly-numerical helper is required;
  * does NOT alter any scientific mathematics: every threshold, hook target, target scalar,
    normalization rule, gradient mechanism, router attribution definition and claim boundary is
    taken BY REFERENCE from the frozen modules.

Four evidence families, separately identifiable and NEVER merged:
  I1 FILM_PARAMETER_INTERPRETABILITY
  I2 SEGMENTATION_GRADIENT_SALIENCY
  I3 ROI_PROPOSAL_AND_REGIONAL_BEHAVIOUR_VISUALIZATION
  I4 BENEFIT_ROUTER_FEATURE_ATTRIBUTION

GATE
  Scientific execution requires PHASE35_EXECUTE=1.  Without it the driver refuses (exit 2) and
  performs ZERO model construction, ZERO checkpoint deserialization, ZERO raw-VAL image read,
  ZERO persisted p_global read, ZERO VAL808 cache read, ZERO forward and ZERO autograd.

PROTECTED DATA
  ROUTER_HOLDOUT raw images/GT and TEST images/GT are FORBIDDEN. Primary execution reads ONLY the
  64 authorized VAL gallery images and ZERO ground truth. The router attribution path reads ONLY
  the frozen GT-free VAL808 cache (0 raw image reads, 0 GT reads).

EXECUTION DISCIPLINE
  Exactly ONE invocation of this driver is authorized for the first Phase35 scientific execution.
  No retry. No post-open patch. The first attempt is preserved.
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

import phase35_interpretability_common_v1_0b as C          # noqa: E402  (frozen contracts)
import phase35_interpretability_execution_v1_0b as V0B      # noqa: E402  (frozen science)
import phase35_interpretability_execution_v1_0c as V0C      # noqa: E402  (frozen smoke helpers)
import phase35_interpretability_execution_v1_0d as V0D      # noqa: E402  (frozen rank-safe target)
import phase35_interpretability_execution_v1_0e as V0E      # noqa: E402  (frozen finite guards)

ROOT = REPO_ROOT
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0"
CLASSIFICATION = "PHASE35_PROSPECTIVE_SCIENTIFIC_EXECUTION_ORCHESTRATOR"
GATE_ENV = C.GATE_ENV                                        # "PHASE35_EXECUTE"

AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
ARR = ROOT / "reports" / "arrays"
FIG = ROOT / "reports" / "figures" / "phase35_interpretability"

FAMILY_OF = OrderedDict(C.EVIDENCE_FAMILIES)

# --------------------------------------------------------------------------- #
# frozen path bindings (no new authority is created here)
# --------------------------------------------------------------------------- #
GRADCAM_LAYERS = V0D.GRADCAM_LAYERS                          # ("bridge", "decoder1")
GRADCAM_IMPL = "gradcam_gradient_enabled_numerically_guarded_v1_0f"
TARGET_SCALAR_IMPL = V0D.TARGET_SCALAR_IMPL
NORMALIZE_IMPL = "cam_normalize_guarded"
EMPTY_MASK_IMPL = "empty_mask_helper_check_insession_actual_logits"

SCI_IMAGE_SHAPE = (1, 3, 512, 512)

# per-family read counters (never conflated with the frozen 35-key smoke contract)
FAMILY_COUNTERS = OrderedDict([
    ("I1_model_constructions", 0), ("I1_checkpoint_deserializations", 0), ("I1_forwards", 0),
    ("I2_raw_val_image_reads", 0), ("I2_persisted_probability_reads", 0),
    ("I2_gradcam_forwards", 0), ("I2_gradcam_autograd_calls", 0), ("I2_cam_maps", 0),
    ("I3_display_panels", 0), ("I3_roi_masks", 0),
    ("I4_router_rows", 0), ("I4_router_forwards", 0), ("I4_router_autograd_calls", 0),
    ("gt_reads", 0), ("router_holdout_reads", 0), ("test_reads", 0), ("train_raw_reads", 0),
    ("R_psi_constructions", 0), ("S_omega_constructions", 0),
    ("optimizer_constructions", 0), ("optimizer_step_calls", 0), ("training_backward_calls", 0),
    ("parameter_mutations", 0),
])


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_json(path: Path, doc) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False, default=str),
                    encoding="utf-8", newline="\n")
    return sha256_file(path)


# --------------------------------------------------------------------------- #
# canonical image preprocessing — re-implemented ONLY as a REUSE of the frozen
# phase29 canonical transform contract. No mathematics is changed: RGB convert,
# aspect-preserving bilinear resize to fit 512, centre pad, /255.0, CHW float32.
# The mask is NEVER opened.
# --------------------------------------------------------------------------- #
def canonical_image_only_transform(path: Path):
    """Canonical VAL image -> (1,3,512,512) float32 tensor. Mask NEVER opened."""
    import numpy as np
    import torch
    from PIL import Image, ImageOps

    size = 512
    with Image.open(path) as im:
        im = im.convert("RGB")
        w, h = im.size
        scale = size / float(max(w, h))
        nw, nh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
        im = im.resize((nw, nh), Image.Resampling.BILINEAR)
        pad_l = (size - nw) // 2
        pad_t = (size - nh) // 2
        pad_r = size - nw - pad_l
        pad_b = size - nh - pad_t
        im = ImageOps.expand(im, border=(pad_l, pad_t, pad_r, pad_b), fill=0)
        arr = np.asarray(im, dtype=np.float32).copy()
    chw = torch.from_numpy(arr).permute(2, 0, 1) / 255.0
    return chw.unsqueeze(0).contiguous()


# --------------------------------------------------------------------------- #
# §H  I1 — FILM_PARAMETER_INTERPRETABILITY (static; no image forward)
# --------------------------------------------------------------------------- #
def run_i1_film(g_model, bphi_model) -> dict:
    """I1: FiLM gamma/beta summary + pairwise distances + task-embedding geometry.

    Reuses the frozen V0B accessors VERBATIM. Requires the canonical G checkpoint: the FiLM
    per-channel vectors are NOT persisted in phase21_film_parameter_summary.csv, so pairwise task
    comparisons require `film_parameters_for_tasks()`. NO image forward occurs in I1.
    """
    fam, film = "I1", V0B.extract_film_parameters(g_model)
    emb = V0B.extract_task_embeddings(g_model, bphi_model)
    return {"family": fam, "name": FAMILY_OF[fam], "film": film, "embeddings": emb,
            "image_forwards_used": 0, "significance_tests_performed": False,
            "read_counts": {"model_constructions": 1, "checkpoint_deserializations": 1}}


# --------------------------------------------------------------------------- #
# §J  I2 — SEGMENTATION_GRADIENT_SALIENCY
# --------------------------------------------------------------------------- #
def run_i2_gradcam(g_model, gallery, allow) -> dict:
    """I2: 64-case Grad-CAM. Persisted p_global target mask; GT-free; no mask ever opened."""
    import numpy as np
    from PIL import Image

    display = V0B.resolve_display_subset(gallery)            # resolved BEFORE any saliency exists

    records = OrderedDict()
    bridge_maps = np.zeros((C.GALLERY_N, 512, 512), dtype=np.float32)
    decoder1_maps = np.zeros((C.GALLERY_N, 512, 512), dtype=np.float32)

    g_order = gallery.sort_values(["dataset", "rank", "sample_id"]).reset_index(drop=True)
    for gi, row in g_order.iterrows():
        sid, dom = str(row["sample_id"]), str(row["dataset"])
        tid = int(C.DOMAIN_TASK_ID[dom])

        # image_path comes from the frozen Phase4 val manifest (already SHA-frozen authority)
        _assert_allowlisted(sid, allow)
        ipath = resolve_val_image_path(sid)
        _assert_not_protected_path(ipath)
        img_t = canonical_image_only_transform(ipath)
        FAMILY_COUNTERS["I2_raw_val_image_reads"] += 1

        p_global = V0B.load_persisted_p_global(sid, dom)     # ONLY the `prob` key
        FAMILY_COUNTERS["I2_persisted_probability_reads"] += 1
        m_pred = V0B.build_target_mask(p_global)             # persisted >= 0.50
        m_roi = V0B.build_roi_mask(p_global)                 # persisted >= 0.30

        img_t = img_t.to(next(g_model.parameters()).device)
        import torch
        tid_t = torch.tensor([tid], dtype=torch.long, device=img_t.device)
        res = V0E.gradcam_gradient_enabled_numerically_guarded(
            g_model, img_t, tid_t, m_pred, layers=GRADCAM_LAYERS)
        FAMILY_COUNTERS["I2_gradcam_forwards"] += 1
        FAMILY_COUNTERS["I2_gradcam_autograd_calls"] += 1

        cam_b = res["cams"]["bridge"].numpy()
        cam_d = res["cams"]["decoder1"].numpy()
        bridge_maps[gi] = cam_b.astype(np.float32)
        decoder1_maps[gi] = cam_d.astype(np.float32)
        FAMILY_COUNTERS["I2_cam_maps"] += 2

        sc_b = V0B.saliency_self_consistency(cam_b, m_pred, m_roi)
        sc_d = V0B.saliency_self_consistency(cam_d, m_pred, m_roi)
        records[sid] = OrderedDict([
            ("index", int(gi)), ("dataset", dom), ("task_id", tid),
            ("in_display_subset", sid in display),
            ("M_pred_foreground_pixels", int(m_pred.sum())),
            ("M_roi_pixels", int(m_roi.sum())),
            ("T", float(res["T"])),
            ("target_scalar_finite", bool(res["target_scalar_finite"])),
            ("empty_prediction_fallback_used", bool(res["empty_prediction_fallback_used"])),
            ("bridge_self_consistency", sc_b),
            ("decoder1_self_consistency", sc_d),
            ("bridge_cam_range", float(res["cam_diagnostics"]["bridge"]
                                       ["upsampled_prenorm_cam_range"])),
            ("decoder1_cam_range", float(res["cam_diagnostics"]["decoder1"]
                                         ["upsampled_prenorm_cam_range"])),
        ])

    ARR.mkdir(parents=True, exist_ok=True)
    np.save(ARR / "phase35_gradcam_bridge_val64_float32.npy", bridge_maps)
    np.save(ARR / "phase35_gradcam_decoder1_val64_float32.npy", decoder1_maps)

    return {"family": "I2", "name": FAMILY_OF["I2"], "n_cases": int(C.GALLERY_N),
            "records": records, "display_subset": display,
            "display_subset_resolved_before_saliency": True,
            "gradcam_impl": GRADCAM_IMPL, "target_scalar_impl": TARGET_SCALAR_IMPL,
            "normalization_impl": NORMALIZE_IMPL, "empty_mask_impl": EMPTY_MASK_IMPL,
            "array_bridge": "reports/arrays/phase35_gradcam_bridge_val64_float32.npy",
            "array_decoder1": "reports/arrays/phase35_gradcam_decoder1_val64_float32.npy",
            "array_shape": [int(C.GALLERY_N), 512, 512], "array_dtype": "float32",
            "gt_reads": 0, "mask_files_opened": 0,
            "read_counts": {"raw_val_image_reads": int(C.GALLERY_N),
                            "persisted_probability_reads": int(C.GALLERY_N),
                            "gradcam_forwards": int(C.GALLERY_N),
                            "gradcam_autograd_calls": int(C.GALLERY_N),
                            "cam_maps": 2 * int(C.GALLERY_N)}}


def _assert_allowlisted(sample_id: str, allow) -> None:
    """Fail closed if a sample_id is not in the frozen 64-sample gallery allow-list.

    NOTE: image filenames are NOT the sample_id (sample_id is a content hash), so path-stem
    inference is never used as an allow-list check. The allow-list is enforced directly on
    sample_id, and the resolved path is separately validated against PROTECTED-DATA tokens
    (ROUTER_HOLDOUT / TEST) by `_assert_not_protected_path`.
    """
    if str(sample_id) not in allow:
        raise RuntimeError(
            f"PROTECTED-DATA GUARD: sample_id outside the 64 allow-list: {sample_id}")


def _assert_not_protected_path(path: Path) -> None:
    """Fail closed on ROUTER_HOLDOUT / TEST / GT-image tokens in a resolved path.

    Applied in place of the stem-based check because sample_id is a content hash rather than a
    filename. The GT directory token `groundtruth` is deliberately EXCLUDED because the authorized
    ISIC image source directory is named `..._Training_Input` while the GT directory is named
    `..._Training_GroundTruth`; only the GT path (never opened) would be rejected.
    """
    low = str(path).lower().replace("\\", "/")
    if "router_holdout" in low:
        raise RuntimeError(f"PROTECTED-DATA GUARD: ROUTER_HOLDOUT path forbidden: {path}")
    if "/test/" in low or low.endswith("/test.csv"):
        raise RuntimeError(f"PROTECTED-DATA GUARD: TEST path forbidden: {path}")
    if "groundtruth" in low or "_segmentation" in low or "/masks/" in low:
        raise RuntimeError(f"PROTECTED-DATA GUARD: GT/mask authority forbidden: {path}")


def resolve_val_image_path(sid: str) -> Path:
    """Resolve an authorized VAL image path from the frozen val manifest (never TEST/holdout)."""
    import pandas as pd
    val = pd.read_csv(ROOT / "manifests" / "phase4_v3" / "val.csv")
    hits = val[val["sample_id"].astype(str) == str(sid)]
    if len(hits) != 1:
        raise RuntimeError(f"val manifest does not uniquely resolve sample_id={sid}")
    p = ROOT / str(hits.iloc[0]["image_path"])
    if not p.exists():
        raise RuntimeError(f"resolved VAL image does not exist: {p}")
    _assert_not_protected_path(p)
    return p


# --------------------------------------------------------------------------- #
# §K  I3 — ROI_PROPOSAL_AND_REGIONAL_BEHAVIOUR_VISUALIZATION (GT-free)
# --------------------------------------------------------------------------- #
def run_i3_roi(gallery, allow, i2_records) -> dict:
    """I3: display-16 panels. image + p_global heatmap + M_pred(0.50) + M_roi(0.30) + ROI geometry."""
    import numpy as np
    from PIL import Image

    display = V0B.resolve_display_subset(gallery)
    panels = OrderedDict()
    for sid in display:
        row = gallery[gallery["sample_id"].astype(str) == sid].iloc[0]
        dom = str(row["dataset"])
        _assert_allowlisted(sid, allow)
        ipath = resolve_val_image_path(sid)
        _assert_not_protected_path(ipath)
        with Image.open(ipath) as im:
            rgb = np.asarray(im.convert("RGB"), dtype=np.uint8).copy()
        p_global = V0B.load_persisted_p_global(sid, dom)
        m_pred = V0B.build_target_mask(p_global)
        m_roi = V0B.build_roi_mask(p_global)

        from src.data.barr_roi import roi_geometry
        geom = roi_geometry(np.asarray(p_global), float(C.T_ROI_PROPOSAL))
        FAMILY_COUNTERS["I3_display_panels"] += 1
        FAMILY_COUNTERS["I3_roi_masks"] += 1
        panels[sid] = OrderedDict([
            ("dataset", dom), ("rgb_shape", list(rgb.shape)),
            ("M_pred_pixels", int(m_pred.sum())), ("M_roi_pixels", int(m_roi.sum())),
            ("roi_geometry_available", geom is not None),
            ("roi_geometry", ({k: geom[k] for k in ("y1", "y2", "x1", "x2", "clip_y1", "clip_y2",
                                                    "clip_x1", "clip_x2", "crop_side_pixels",
                                                    "effective_magnification", "margin")}
                              if geom is not None else None)),
            ("gt_used", False),
        ])
    return {"family": "I3", "name": FAMILY_OF["I3"], "n_panels": int(C.DISPLAY_N),
            "panels": panels, "gt_used": False,
            "thresholds": {"M_pred": C.T_SEGMENTATION_OUTPUT, "M_roi": C.T_ROI_PROPOSAL},
            "read_counts": {"display_panels": int(C.DISPLAY_N),
                            "persisted_probability_reads": int(C.DISPLAY_N),
                            "gt_reads": 0}}


# --------------------------------------------------------------------------- #
# §L  I4 — BENEFIT_ROUTER_FEATURE_ATTRIBUTION (VAL808, GT-free, 0 raw image reads)
# --------------------------------------------------------------------------- #
def run_i4_router(bphi_model, bphi_state) -> dict:
    """I4: Gradient x Input on the frozen VAL808 202-D cache. NO sigmoid. NO epsilon."""
    import numpy as np
    import pandas as pd

    pop = V0B.router_population_verify()                  # BEFORE any attribution
    root = ROOT / C.ROUTER_CACHE_ROOT
    deep = np.load(root / C.ROUTER_FILES["deep_features"])
    scal = np.load(root / C.ROUTER_FILES["scalars"])
    FAMILY_COUNTERS["I4_router_rows"] = int(deep.shape[0])

    geom = json.loads((root / C.ROUTER_FILES["roi_geometry"]).read_text(encoding="utf-8"))
    sample_ids = [str(s) for s in geom["sample_id_order"]]
    assert len(sample_ids) == C.ROUTER_POPULATION_N

    xn = V0B.router_normalized_features(deep, scal, bphi_state)
    val = pd.read_csv(ROOT / "manifests" / "phase4_v3" / "val.csv")
    tid_by_sid = {str(r["sample_id"]): int(r["task_id"])
                  for _, r in val.iterrows()}
    task_ids = np.array([tid_by_sid[s] for s in sample_ids], dtype=np.int64)

    res = V0B.router_gradient_x_input(bphi_model, xn, task_ids)
    FAMILY_COUNTERS["I4_router_forwards"] += 1
    FAMILY_COUNTERS["I4_router_autograd_calls"] += 1

    signed, absolute = res["signed"], res["absolute"]
    per_row = OrderedDict()
    group_abs = OrderedDict((g, 0.0) for g in C.ROUTER_FEATURE_GROUPS)
    scalar_abs = OrderedDict((s, 0.0) for s in C.ROUTER_SCALAR_FEATURES)
    zero_rows = 0
    for i, sid in enumerate(sample_ids):
        att = V0B.router_group_attribution(absolute[i])
        if att["ZERO_ROUTER_GRAD_ATTRIBUTION"]:
            zero_rows += 1
        per_row[sid] = OrderedDict([
            ("index", i), ("task_id", int(task_ids[i])),
            ("delta_hat", float(res["delta_hat"][i])),
            ("denominator", att["denominator"]),
            ("ZERO_ROUTER_GRAD_ATTRIBUTION", att["ZERO_ROUTER_GRAD_ATTRIBUTION"]),
            ("groups", {g: v["normalized_absolute_share_group"]
                        for g, v in att["groups"].items()}),
            ("scalars", att["scalars"]),
        ])
        for g in C.ROUTER_FEATURE_GROUPS:
            group_abs[g] += att["groups"][g]["absolute_group"]
        for s in C.ROUTER_SCALAR_FEATURES:
            scalar_abs[s] += abs(att["scalars"][s])

    ARR.mkdir(parents=True, exist_ok=True)
    np.save(ARR / "phase35_router_attribution_signed_val808_float32.npy",
            signed.astype(np.float32))
    np.save(ARR / "phase35_router_attribution_absolute_val808_float32.npy",
            absolute.astype(np.float32))
    with open(TAB / "phase35_router_attribution_per_sample.csv", "w", newline="",
              encoding="utf-8") as f:
        import csv
        wr = csv.writer(f)
        wr.writerow(["sample_id", "task_id", "delta_hat", "denominator",
                     "ZERO_ROUTER_GRAD_ATTRIBUTION"]
                    + [f"group_share_{g}" for g in C.ROUTER_FEATURE_GROUPS]
                    + [f"scalar_abs_{s}" for s in C.ROUTER_SCALAR_FEATURES])
        for sid in sample_ids:
            r = per_row[sid]
            wr.writerow([sid, r["task_id"], r["delta_hat"], r["denominator"],
                         r["ZERO_ROUTER_GRAD_ATTRIBUTION"]]
                        + [r["groups"][g] for g in C.ROUTER_FEATURE_GROUPS]
                        + [r["scalars"][s] for s in C.ROUTER_SCALAR_FEATURES])

    return {"family": "I4", "name": FAMILY_OF["I4"], "population": pop,
            "per_row": per_row, "sample_id_order": sample_ids,
            "group_absolute_totals": {g: float(v) for g, v in group_abs.items()},
            "scalar_absolute_totals": {s: float(v) for s, v in scalar_abs.items()},
            "zero_attribution_rows": zero_rows,
            "sigmoid_applied": False, "epsilon_added": False, "renormalization": False,
            "feature_perturbation": False, "retraining": False, "optimization": False,
            "counterfactual_task_id_analysis": C.ROUTER_COUNTERFACTUAL_TASK_ID,
            "arrays": ["reports/arrays/phase35_router_attribution_signed_val808_float32.npy",
                       "reports/arrays/phase35_router_attribution_absolute_val808_float32.npy"],
            "read_counts": {"router_rows": int(deep.shape[0]),
                            "router_forwards": 1, "router_autograd_calls": 1,
                            "raw_image_reads": 0, "gt_reads": 0}}


# --------------------------------------------------------------------------- #
# §M  figures F1-F7 (PNG + PDF). F8 is NOT implemented (resolved ineligible).
# --------------------------------------------------------------------------- #
def build_figures(i1, i2, i3, i4) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    FIG.mkdir(parents=True, exist_ok=True)
    written = OrderedDict()

    def _save(fig, stem):
        png, pdf = FIG / f"{stem}.png", FIG / f"{stem}.pdf"
        fig.savefig(png, dpi=140, bbox_inches="tight")
        fig.savefig(pdf, bbox_inches="tight")
        plt.close(fig)
        written[stem] = {"png": str(png.relative_to(ROOT)), "pdf": str(pdf.relative_to(ROOT))}

    sites = list(C.FILM_SITES)
    doms = list(C.DOMAIN_TASK_ID)

    # F1 / F2: FiLM gamma / beta heatmaps by task x site (channel mean)
    for tag, key in (("F1", "gamma"), ("F2", "beta")):
        M = np.array([[i1["film"]["per_task_site"][f"{d}|{s}"]["mean" if key == "gamma"
                                                   else "beta_mean"]
                       for s in sites] for d in doms], dtype=float)
        fig, ax = plt.subplots(figsize=(6.4, 3.0))
        im = ax.imshow(M, aspect="auto", cmap="coolwarm")
        ax.set_xticks(range(len(sites)), sites, rotation=20)
        ax.set_yticks(range(len(doms)), doms)
        for a in range(len(doms)):
            for b in range(len(sites)):
                ax.text(b, a, f"{M[a, b]:.3f}", ha="center", va="center", fontsize=7)
        ax.set_title(f"{tag} FiLM {key} mean (task x site; channel-mean summary)")
        fig.colorbar(im, ax=ax, shrink=0.85)
        _save(fig, f"phase35_{tag.lower()}_film_{key}_heatmap")

    # F3: task-embedding geometry (G cosine + B_phi cosine)
    Gc = np.array(i1["embeddings"]["G_geometry"]["cosine"], dtype=float)
    Bc = np.array(i1["embeddings"]["B_phi_geometry"]["cosine"], dtype=float)
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.2))
    for ax, Mx, title in ((axes[0], Gc, "G task embedding cosine"),
                          (axes[1], Bc, "B_phi task embedding cosine")):
        im = ax.imshow(Mx, vmin=-1, vmax=1, cmap="viridis")
        ax.set_xticks(range(len(doms)), doms, rotation=20)
        ax.set_yticks(range(len(doms)), doms)
        for a in range(len(doms)):
            for b in range(len(doms)):
                ax.text(b, a, f"{Mx[a, b]:.2f}", ha="center", va="center", fontsize=7,
                        color="white")
        ax.set_title(title)
    fig.colorbar(im, ax=axes, shrink=0.8)
    _save(fig, "phase35_f3_task_embedding_geometry")

    # F4: fixed 16-case panel (image + M_pred + M_roi + bridge CAM + decoder1 CAM)
    display = list(i2["display_subset"])
    idx_of = {sid: i2["records"][sid]["index"] for sid in i2["records"]}
    bridge_maps = np.load(ROOT / i2["array_bridge"])
    dec1_maps = np.load(ROOT / i2["array_decoder1"])
    from PIL import Image as _I
    n = len(display)
    fig, axes = plt.subplots(5, n, figsize=(1.9 * n, 9.6))
    for j, sid in enumerate(display):
        rec = i2["records"][sid]
        dom = rec["dataset"]
        _assert_allowlisted(sid, frozenset(i2["records"]))
        ip = resolve_val_image_path(sid)
        with _I.open(ip) as im:
            rgb = np.asarray(im.convert("RGB"))
        from src.data.barr_roi import roi_geometry
        p = V0B.load_persisted_p_global(sid, dom)
        m_pred = V0B.build_target_mask(p)
        m_roi = V0B.build_roi_mask(p)
        gi = idx_of[sid]
        axes[0, j].imshow(rgb, cmap=None if rgb.ndim == 3 else "gray")
        axes[0, j].set_title(f"{dom}\n{sid[:8]}", fontsize=6)
        axes[1, j].imshow(np.asarray(p, dtype=np.float32), cmap="magma", vmin=0, vmax=1)
        axes[2, j].imshow(m_pred, cmap="gray")
        axes[3, j].imshow(bridge_maps[gi], cmap="jet", vmin=0, vmax=1)
        axes[4, j].imshow(dec1_maps[gi], cmap="jet", vmin=0, vmax=1)
        for r, lab in enumerate(["image", "p_global", "M_pred 0.50", "bridge CAM",
                                 "decoder1 CAM"]):
            axes[r, j].set_xticks([])
            axes[r, j].set_yticks([])
            if j == 0:
                axes[r, j].set_ylabel(lab, fontsize=6)
    fig.suptitle("F4 fixed 16-case panel (display subset resolved before saliency)", fontsize=9)
    _save(fig, "phase35_f4_display16_panel")

    # F5: saliency self-consistency summary by domain/layer
    dom_of = {sid: i2["records"][sid]["dataset"] for sid in i2["records"]}
    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.2))
    for ax, lay in zip(axes, ("bridge", "decoder1")):
        vals, labs = [], []
        for d in doms:
            v = [i2["records"][s][f"{lay}_self_consistency"]["foreground_saliency_mass_fraction"]
                 for s in i2["records"] if dom_of[s] == d]
            v = [x for x in v if x is not None]
            vals.append(v)
            labs.append(f"{d}\nn={len(v)}")
        ax.boxplot(vals, tick_labels=labs)
        ax.set_title(f"F5 {lay}: foreground saliency mass fraction (GT-free)")
        ax.set_ylim(0, 1)
    _save(fig, "phase35_f5_saliency_self_consistency")

    # F6: router attribution group summary
    groups = list(C.ROUTER_FEATURE_GROUPS)
    gtot = np.array([i4["group_absolute_totals"][g] for g in groups], dtype=float)
    shares = gtot / gtot.sum() if gtot.sum() > 0 else gtot
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    ax.bar(range(len(groups)), shares, color="#4472c4")
    ax.set_xticks(range(len(groups)), groups, rotation=25, ha="right")
    ax.set_ylabel("share of absolute attribution")
    ax.set_title("F6 router attribution group summary (Gradient x Input, raw delta_hat)")
    _save(fig, "phase35_f6_router_group_attribution")

    # F7: router scalar-feature attribution summary
    sc = np.array([i4["scalar_absolute_totals"][s] for s in C.ROUTER_SCALAR_FEATURES],
                  dtype=float)
    fig, ax = plt.subplots(figsize=(7.4, 3.2))
    ax.barh(range(len(sc)), sc, color="#ed7d31")
    ax.set_yticks(range(len(sc)), C.ROUTER_SCALAR_FEATURES, fontsize=7)
    ax.set_xlabel("sum |a_j| over VAL808")
    ax.set_title("F7 router scalar-feature attribution summary")
    _save(fig, "phase35_f7_router_scalar_attribution")

    return {"figures": written, "F8_regional_implemented": False,
            "number_of_figures": len(written)}


# --------------------------------------------------------------------------- #
# §N  tables / arrays manifest
# --------------------------------------------------------------------------- #
def write_tables(i1, i2, i3, i4) -> dict:
    import csv
    TAB.mkdir(parents=True, exist_ok=True)
    out = OrderedDict()

    p1 = TAB / "phase35_film_parameter_summary_v1_0.csv"
    with open(p1, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["task", "site", "gamma_mean", "gamma_mean_abs", "gamma_std",
                    "gamma_l2_norm", "beta_mean", "beta_mean_abs", "beta_std", "beta_l2_norm"])
        for k, v in i1["film"]["per_task_site"].items():
            task, site = k.split("|")
            w.writerow([task, site, v["mean"], v["mean_abs"], v["std"], v["l2_norm"],
                        v["beta_mean"], v["beta_mean_abs"], v["beta_std"], v["beta_l2_norm"]])
    out["film_summary"] = str(p1.relative_to(ROOT))

    p2 = TAB / "phase35_film_pairwise_task_v1_0.csv"
    with open(p2, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["task_a", "task_b", "site"] + list(C.FILM_PAIRWISE_QUANTITIES))
        for k, v in i1["film"]["pairwise"].items():
            a, b, site = k.split("|")
            w.writerow([a, b, site] + [v[q] for q in C.FILM_PAIRWISE_QUANTITIES])
    out["film_pairwise"] = str(p2.relative_to(ROOT))

    p3 = TAB / "phase35_task_embedding_geometry_v1_0.csv"
    with open(p3, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "task_a", "task_b", "euclidean", "cosine", "norm_a", "norm_b"])
        doms = list(C.DOMAIN_TASK_ID)
        for tag, kk in (("G", "G_geometry"), ("B_phi", "B_phi_geometry")):
            g = i1["embeddings"][kk]
            for a in range(len(doms)):
                for b in range(len(doms)):
                    w.writerow([tag, doms[a], doms[b], g["euclidean"][a][b], g["cosine"][a][b],
                                g["norms"][a], g["norms"][b]])
    out["task_embeddings"] = str(p3.relative_to(ROOT))

    p4 = TAB / "phase35_gradcam_index_val64_v1_0.csv"
    with open(p4, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["index", "sample_id", "dataset", "task_id", "in_display_subset", "T",
                    "bridge_fg_mass_fraction", "bridge_roi_mass_fraction", "bridge_ZERO_CAM",
                    "decoder1_fg_mass_fraction", "decoder1_roi_mass_fraction",
                    "decoder1_ZERO_CAM", "M_pred_pixels", "M_roi_pixels"])
        for sid, r in sorted(i2["records"].items(), key=lambda kv: kv[1]["index"]):
            b, d = r["bridge_self_consistency"], r["decoder1_self_consistency"]
            w.writerow([r["index"], sid, r["dataset"], r["task_id"], r["in_display_subset"],
                        r["T"], b["foreground_saliency_mass_fraction"],
                        b["roi_saliency_mass_fraction"], b["ZERO_CAM"],
                        d["foreground_saliency_mass_fraction"],
                        d["roi_saliency_mass_fraction"], d["ZERO_CAM"],
                        r["M_pred_foreground_pixels"], r["M_roi_pixels"]])
    out["gradcam_index"] = str(p4.relative_to(ROOT))

    p5 = TAB / "phase35_saliency_self_consistency_summary_v1_0.csv"
    with open(p5, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["layer", "domain", "n", "mean_fg_mass_fraction", "median_fg_mass_fraction",
                    "zero_cam_count", "peak_in_M_pred_count"])
        import numpy as np
        for lay in ("bridge", "decoder1"):
            for dom in C.DOMAIN_TASK_ID:
                vals, zero, peak = [], 0, 0
                for sid, r in i2["records"].items():
                    if r["dataset"] != dom:
                        continue
                    sc = r[f"{lay}_self_consistency"]
                    if sc["ZERO_CAM"]:
                        zero += 1
                        continue
                    vals.append(sc["foreground_saliency_mass_fraction"])
                    peak += int(bool(sc["cam_peak_inside_M_pred"]))
                w.writerow([lay, dom, len(vals),
                            float(np.mean(vals)) if vals else "",
                            float(np.median(vals)) if vals else "", zero, peak])
    out["saliency_summary"] = str(p5.relative_to(ROOT))

    p6 = TAB / "phase35_display16_roi_panel_index_v1_0.csv"
    with open(p6, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sample_id", "dataset", "M_pred_pixels", "M_roi_pixels",
                    "roi_geometry_available", "crop_side_pixels", "effective_magnification"])
        for sid, p in i3["panels"].items():
            g = p["roi_geometry"] or {}
            w.writerow([sid, p["dataset"], p["M_pred_pixels"], p["M_roi_pixels"],
                        p["roi_geometry_available"], g.get("crop_side_pixels", ""),
                        g.get("effective_magnification", "")])
    out["display16_index"] = str(p6.relative_to(ROOT))

    p7 = TAB / "phase35_router_group_attribution_v1_0.csv"
    with open(p7, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["group", "absolute_total", "share_of_total"])
        tot = sum(i4["group_absolute_totals"].values())
        for g, v in i4["group_absolute_totals"].items():
            w.writerow([g, v, (v / tot if tot > 0 else "")])
    out["router_group"] = str(p7.relative_to(ROOT))

    p8 = TAB / "phase35_router_scalar_attribution_v1_0.csv"
    with open(p8, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["scalar_feature", "absolute_total"])
        for s, v in i4["scalar_absolute_totals"].items():
            w.writerow([s, v])
    out["router_scalar"] = str(p8.relative_to(ROOT))

    out["router_per_sample"] = "reports/tables/phase35_router_attribution_per_sample.csv"
    return {"tables": out, "table_count": len(out)}


# --------------------------------------------------------------------------- #
# §O  scientific result artifact
# --------------------------------------------------------------------------- #
def write_scientific_result(ev) -> dict:
    doc = OrderedDict([
        ("artifact", "phase35_interpretability_scientific_result_v1_0"),
        ("section", "§V"), ("phase", 35), ("method", C.METHOD), ("revision", REVISION),
        ("classification", "PHASE35_FIRST_SCIENTIFIC_EXECUTION_RESULT"),
        ("claim_type", C.CLAIM_TYPE),
        ("evidence_families", OrderedDict(C.EVIDENCE_FAMILIES)),
        ("families_never_merged", True),
        ("figures", ev["figures"]["figures"]),
        ("tables", ev["tables"]["tables"]),
        ("arrays", {
            "bridge_gradcam": "reports/arrays/phase35_gradcam_bridge_val64_float32.npy",
            "decoder1_gradcam": "reports/arrays/phase35_gradcam_decoder1_val64_float32.npy",
            "router_signed": "reports/arrays/phase35_router_attribution_signed_val808_float32.npy",
            "router_absolute":
                "reports/arrays/phase35_router_attribution_absolute_val808_float32.npy",
        }),
        ("generated_utc", _now()),
    ])
    return {"path": "reports/audits/phase35_interpretability_scientific_result_v1_0.json",
            "sha256": _write_json(AUD / "phase35_interpretability_scientific_result_v1_0.json",
                                  doc), "document": doc}


# --------------------------------------------------------------------------- #
# top-level scientific execution
# --------------------------------------------------------------------------- #
def run_science() -> dict:
    ev = OrderedDict()
    ev["authority_gates"] = V0B.verify_authority_gates()
    ev["freeze_read_utc"] = json.loads(
        (AUD / "phase35_scientific_execution_source_freeze_v1_0.json").read_text(
            encoding="utf-8"))["source_freeze_utc"]
    ev["first_scientific_read_utc"] = _now()

    gallery, allow = V0B.load_gallery_allowlist()
    ev["gallery_n"] = int(len(allow))

    g_model, ginfo = V0B.load_g_component(device="cuda")
    bphi_model, bphi_state, binfo = V0B.load_bphi_component(device="cuda")
    FAMILY_COUNTERS["I1_model_constructions"] = 2
    FAMILY_COUNTERS["I1_checkpoint_deserializations"] = 2
    ev["model_binding"] = {"G": ginfo, "B_phi": binfo}

    before = {"G": V0C.state_dict_identity(g_model), "B_phi": V0C.state_dict_identity(bphi_model)}

    ev["I1"] = run_i1_film(g_model, bphi_model)
    ev["I2"] = run_i2_gradcam(g_model, gallery, allow)
    ev["I3"] = run_i3_roi(gallery, allow, ev["I2"]["records"])
    ev["I4"] = run_i4_router(bphi_model, bphi_state)

    ev["figures"] = build_figures(ev["I1"], ev["I2"], ev["I3"], ev["I4"])
    ev["tables"] = write_tables(ev["I1"], ev["I2"], ev["I3"], ev["I4"])

    grad_audit = V0E.parameter_grad_state_audit_insession(
        {"G": g_model, "B_phi": bphi_model})
    after = {"G": V0C.state_dict_identity(g_model), "B_phi": V0C.state_dict_identity(bphi_model)}
    FAMILY_COUNTERS["parameter_mutations"] = 0 if before == after else 1
    ev["parameter_grad_state_audit"] = grad_audit
    ev["parameter_immutability"] = {
        "G_state_unchanged": before["G"] == after["G"],
        "B_phi_state_unchanged": before["B_phi"] == after["B_phi"],
        "MODEL_PARAMETERS_UNCHANGED": before == after}
    ev["family_counters"] = dict(FAMILY_COUNTERS)
    ev["scientific_result"] = write_scientific_result(ev)
    return ev


# --------------------------------------------------------------------------- #
def mode_science_preview() -> dict:
    """Static, non-executing description of the scientific composition."""
    return {"mode": "science", "families": list(C.EVIDENCE_FAMILIES),
            "F8_regional_implemented": False,
            "gradcam_impl": GRADCAM_IMPL, "target_scalar_impl": TARGET_SCALAR_IMPL,
            "normalization_impl": NORMALIZE_IMPL, "empty_mask_impl": EMPTY_MASK_IMPL,
            "thresholds": {"M_pred": C.T_SEGMENTATION_OUTPUT, "M_roi": C.T_ROI_PROPOSAL}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True,
                    choices=["preview", "science"])
    a = ap.parse_args()

    if a.mode == "science":
        if os.environ.get(GATE_ENV) != "1":
            print(f"PHASE35 EXECUTION NOT AUTHORIZED - scientific execution requires {GATE_ENV}=1.")
            return 2
        report = OrderedDict([("revision", REVISION), ("classification", CLASSIFICATION),
                              ("mode", a.mode), ("started_utc", _now())])
        report.update(run_science())
        print(json.dumps(report, indent=1, default=str))
        return 0

    print(json.dumps(OrderedDict([("revision", REVISION), ("classification", CLASSIFICATION),
                                  ("mode", a.mode)] + list(mode_science_preview().items())),
                     indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
