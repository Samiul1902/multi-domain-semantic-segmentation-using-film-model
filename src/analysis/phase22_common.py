"""Phase 22 — shared, frozen input contract for DIAGNOSTIC-ONLY inference.

Phase 22 performs **no training**. Its only inference is diagnostic and is
strictly bound to the frozen Phase-21 Global MedFiLM reference checkpoint.

This module pins, in code, the exact spatial pre-processing used by the frozen
Phase-19 harmonization contract so that a diagnostic probe (scale sweep, oracle
regional intervention) reproduces the canonical pipeline bit-for-bit:

    scale      = min(size / width, size / height)
    rw, rh     = max(1, round(width * scale)), max(1, round(height * scale))
    image      -> PIL resize (rw, rh), Resampling.BILINEAR
    mask       -> PIL resize (rw, rh), Resampling.NEAREST
    padding    -> centred; left, top = (size - rw) // 2, (size - rh) // 2
    intensity  -> divide by 255.0 -> [0, 1]

The functions here are byte-equivalent to
``src.data.transforms.SegmentationTransform`` for the deterministic
(``train=False``) path. They are re-implemented rather than imported because the
Phase-22 probes operate on **cropped** PIL images and on **binary masks**, both
of which the training transform does not accept.

Nothing in this module reads TEST data. Nothing in this module trains.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]

# --------------------------------------------------------------------------- #
# Frozen identities (must match the Phase-21 bindings exactly)
# --------------------------------------------------------------------------- #
PHASE = 22
EXPERIMENT_ID = "phase21_global_medfilm_fourdomain_seed42_clean_v3"
MANIFEST_VERSION = "phase4_v3"
MANIFEST_DIR = ROOT / "manifests" / MANIFEST_VERSION

PROTOCOL_PATH = "reports/audits/phase20_shared_global_baseline_protocol.json"
PROTOCOL_SHA256 = "b74f1f9f429adbce374f0306180943b9f373f872e1e69e115b7d17e81414283c"

PHASE21_FREEZE = ROOT / "reports/audits/phase21_final_freeze.json"
PHASE21_BEST_CKPT = ROOT / "checkpoints" / EXPERIMENT_ID / "best.pt"

ARCHITECTURE_ID = "global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1"

CANONICAL_SIZE = 512
THRESHOLD = 0.5
CHANNEL_POLICY = "RGB_3CH"
SUPPORTED_SIZES = (256, 512, 768, 1024)
SCALE_PROBE_SIZES = (256, 768, 1024)      # relative to the canonical 512 reference
DIAGNOSTIC_SIZE = 512                     # regional / ROI probes are re-run at 512

TASK_ID = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}
TASK_ID_TO_NAME = {v: k for k, v in TASK_ID.items()}
DATASET_ORDER = ["ISIC", "BUSI", "KVASIR", "KUB"]

ORACLE_ROI_MARGIN = 0.25                  # 1.5x bbox width AND height => 0.25 each side
PRED_ROI_MARGIN = 0.25

PREDICTION_ROOT = ROOT / "reports/predictions" / EXPERIMENT_ID / "val"

# Output locations
AUDITS = ROOT / "reports/audits"
TABLES = ROOT / "reports/tables"
FIGURES = ROOT / "reports/figures/phase22_resource_gap"
PHASE22_PRED_ROOT = ROOT / "reports/predictions/phase22_diagnostic"


# --------------------------------------------------------------------------- #
def sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def write_json(path, payload: dict) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=_json_default),
                    encoding="utf-8")
    return path


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, Path):
        return str(o)
    raise TypeError(f"not JSON serialisable: {type(o)}")


def load_json(path) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"required artifact missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Pinned preprocessing (byte-equivalent to the frozen deterministic path)
# --------------------------------------------------------------------------- #
def aspect_resize_pad(image: Image.Image, mask: Image.Image | None,
                      size: int, image_mode: str = "RGB"):
    """Aspect-preserving resize + centred pad onto a ``size`` x ``size`` canvas.

    Returns ``(image_tensor (C,H,W) float32 in [0,1], mask_tensor (1,H,W) float32
    in {0,1} or None, geometry)``.

    ``geometry`` is a dict with the fields required to invert the mapping:
        scale, resized_h, resized_w, pad_left, pad_top, size
    """
    if size not in SUPPORTED_SIZES:
        raise ValueError(f"size must be one of {SUPPORTED_SIZES}")
    image = image.convert(image_mode)
    mask = mask.convert("L") if mask is not None else None

    width, height = image.size
    scale = min(size / width, size / height)
    rw, rh = max(1, round(width * scale)), max(1, round(height * scale))
    image = image.resize((rw, rh), Image.Resampling.BILINEAR)
    if mask is not None:
        mask = mask.resize((rw, rh), Image.Resampling.NEAREST)
    left, top = (size - rw) // 2, (size - rh) // 2
    right, bottom = size - rw - left, size - rh - top
    padding = (left, top, right, bottom)
    image = ImageOps.expand(image, padding)
    if mask is not None:
        mask = ImageOps.expand(mask, padding)

    image_arr = np.asarray(image, dtype=np.float32).copy()
    if image_arr.ndim == 2:
        image_t = torch.from_numpy(image_arr).unsqueeze(0) / 255.0
    else:
        image_t = torch.from_numpy(image_arr).permute(2, 0, 1) / 255.0
    mask_t = None
    if mask is not None:
        mask_t = torch.from_numpy(
            (np.asarray(mask).copy() > 0).astype(np.float32)).unsqueeze(0)

    geometry = {
        "scale": float(scale),
        "resized_h": int(rh), "resized_w": int(rw),
        "pad_left": int(left), "pad_top": int(top),
        "pad_right": int(right), "pad_bottom": int(bottom),
        "size": int(size),
        "source_hw": (int(height), int(width)),
    }
    return image_t, mask_t, geometry


def unmap_probability_to_source(prob_sq: np.ndarray, geom: dict) -> np.ndarray:
    """Invert :func:`aspect_resize_pad` on a square probability map.

    ``prob_sq`` is (size, size). The result is (source_h, source_w) float32,
    obtained by (1) discarding the centred pad, (2) resizing the valid window
    back to ``(resized_h, resized_w)`` with BILINEAR, (3) resizing that to the
    native ``(source_h, source_w)`` with BILINEAR.

    Pad pixels carry probability 0 by construction, so discarding them before
    resizing is the exact inverse of the forward padding step.
    """
    size = geom["size"]
    rh, rw = geom["resized_h"], geom["resized_w"]
    pl, pt = geom["pad_left"], geom["pad_top"]
    oh, ow = geom["source_hw"]

    valid = prob_sq[pt:pt + rh, pl:pl + rw].astype(np.float32)
    if valid.shape != (rh, rw):
        raise ValueError(f"pad slice mismatch: {valid.shape} != {(rh, rw)}")
    window = np.asarray(
        Image.fromarray(valid).resize((rw, rh), Image.Resampling.BILINEAR),
        dtype=np.float32)
    native = np.asarray(
        Image.fromarray(window).resize((ow, oh), Image.Resampling.BILINEAR),
        dtype=np.float32)
    return np.clip(native, 0.0, 1.0)


def map_source_to_square_probability(prob_native: np.ndarray, geom: dict) -> np.ndarray:
    """Forward map: native (h,w) float probability -> (size, size) square canvas.

    Exact inverse of :func:`unmap_probability_to_source` at the sampling level:
    resize native -> (resized_h, resized_w), then centre-pad with 0.
    """
    size = geom["size"]
    rh, rw = geom["resized_h"], geom["resized_w"]
    pl, pt = geom["pad_left"], geom["pad_top"]
    window = np.asarray(
        Image.fromarray(prob_native.astype(np.float32)).resize(
            (rw, rh), Image.Resampling.BILINEAR), dtype=np.float32)
    out = np.zeros((size, size), dtype=np.float32)
    out[pt:pt + rh, pl:pl + rw] = window
    return out


# --------------------------------------------------------------------------- #
# Geometry helpers (native image space)
# --------------------------------------------------------------------------- #
def bbox_of(binary: np.ndarray) -> dict | None:
    """Tight bounding box of a binary mask (native space). ``None`` if empty."""
    ys, xs = np.where(binary > 0)
    if ys.size == 0:
        return None
    return {"min_y": int(ys.min()), "max_y": int(ys.max()),
            "min_x": int(xs.min()), "max_x": int(xs.max()),
            "bbox_h": int(ys.max() - ys.min() + 1),
            "bbox_w": int(xs.max() - xs.min() + 1)}


def expanded_roi_box(bbox: dict, image_shape, margin: float = ORACLE_ROI_MARGIN) -> dict:
    """Centre-preserving, boundary-clipped context box around a tight bbox.

    ``margin`` is applied to BOTH sides along each axis, so a margin of 0.25
    yields an expanded extent of 1.5 x bbox width and 1.5 x bbox height.

    The expansion is clipped to the source image and the ROI centre is PRESERVED
    (the clipped box is not re-centred).
    """
    h_img, w_img = image_shape
    m_y = round(margin * bbox["bbox_h"])
    m_x = round(margin * bbox["bbox_w"])
    ey0, ey1 = bbox["min_y"] - m_y, bbox["max_y"] + m_y
    ex0, ex1 = bbox["min_x"] - m_x, bbox["max_x"] + m_x
    y0, y1 = max(0, ey0), min(h_img - 1, ey1)
    x0, x1 = max(0, ex0), min(w_img - 1, ex1)
    return {
        "y0": int(y0), "y1": int(y1), "x0": int(x0), "x1": int(x1),
        "roi_h": int(y1 - y0 + 1), "roi_w": int(x1 - x0 + 1),
        "requested_y0": int(ey0), "requested_y1": int(ey1),
        "requested_x0": int(ex0), "requested_x1": int(ex1),
        "clipped": bool((y0 != ey0) or (y1 != ey1) or (x0 != ex0) or (x1 != ex1)),
        "margin": float(margin),
        "expanded_h": int(ey1 - ey0 + 1), "expanded_w": int(ex1 - ex0 + 1),
        "expansion_factor": (
            round(float((ey1 - ey0 + 1) / bbox["bbox_h"]), 6),
            round(float((ex1 - ex0 + 1) / bbox["bbox_w"]), 6)),
    }


def square_pad_box(roi_box: dict, image_shape) -> dict:
    """Square-pad a clipped ROI box about its own centre, staying in-bounds.

    Required so the ROI crop is a true square before the aspect-preserving
    resize (which is then a plain square->square resample, preserving the ROI
    centre exactly).
    """
    h_img, w_img = image_shape
    y0, y1, x0, x1 = roi_box["y0"], roi_box["y1"], roi_box["x0"], roi_box["x1"]
    h, w = y1 - y0 + 1, x1 - x0 + 1
    # A square of side S can only fit inside the image if S <= min(H, W). Clamping
    # here is what keeps the box SQUARE after the in-bounds shift below; without it
    # a small image (e.g. a 197-px-wide ROI-regime scan) would force ny0/nx0 negative
    # and silently shrink the box on one axis, producing a non-square crop.
    side = int(min(max(h, w), h_img, w_img))
    cy = (y0 + y1) / 2.0
    cx = (x0 + x1) / 2.0
    ny0 = int(round(cy - side / 2.0))
    nx0 = int(round(cx - side / 2.0))
    # keep the square fully inside the image, preserving the requested size exactly
    ny0 = max(0, min(ny0, h_img - side))
    nx0 = max(0, min(nx0, w_img - side))
    ny1, nx1 = ny0 + side - 1, nx0 + side - 1
    sy0, sx0 = int(round(cy - side / 2.0)), int(round(cx - side / 2.0))
    return {
        "y0": int(ny0), "y1": int(ny1), "x0": int(nx0), "x1": int(nx1),
        "side": int(side),
        "shift_y": int(ny0 - sy0), "shift_x": int(nx0 - sx0),
        "fully_in_bounds": bool(ny0 >= 0 and nx0 >= 0
                                and ny1 <= h_img - 1 and nx1 <= w_img - 1),
        "clamped_to_image_min_side": bool(side == min(h_img, w_img)),
    }


def threshold_probability(prob: np.ndarray, threshold: float = THRESHOLD) -> np.ndarray:
    """Reproduce the canonical Phase-21 binary decision from a probability map.

    IMPORTANT — the persisted ``pred`` arrays are NOT recoverable from the
    persisted ``prob`` arrays, and Phase 22 must not pretend otherwise.

    The canonical Phase-21 pass computed ``pred`` from the **float32** sigmoid
    output. It then persisted ``prob`` as ``float16``. ``float16`` is much coarser
    than ``float32`` near 0.5, so a band of float32 probabilities that were
    strictly below 0.5 rounds UP to exactly 0.5, and a band that was at or above
    0.5 also lands on 0.5. The two bands become indistinguishable on disk.

    Exhaustive audit over all 808 canonical VAL maps quantifies this exactly:

      * 2284 pixels store ``prob16 == 0.5`` with ``pred == 1``
      * 1078 pixels store ``prob16 == 0.5`` with ``pred == 0``

    That is only consistent with the decision having been taken in float32 and the
    tied pixels coming from both sides of the boundary. Consequently:

      * ``prob16 >= 0.5`` reproduces the stored ``pred`` on 435/808 maps and
        mislabels 1078 pixels in total (~1.3 pixels per image, 0.0005 % of the
        pixel population).
      * ``prob16 > 0.5`` reproduces the stored ``pred`` on 348/808 maps and
        mislabels 2284 pixels in total.

    Neither is bit-exact, and no function of the stored float16 map can be.

    Phase 22 therefore adopts a **single, declared, reproducible** rule applied
    identically to the reference maps and to every diagnostic probe:

        pred = (float32(prob) >= 0.5)

    This is the canonical float32 rule, evaluated on the best available
    representation. It is lower-inclusive, matching ``torch.sigmoid(y).ge(0.5)``
    in the frozen evaluation code. Its unavoidable error against the persisted
    ``pred`` (1078 pixels over 808 images — 211.7 M pixel positions) is therefore
    smaller than the alternative, and, critically, it is **identical in form** on
    the reference and on every probe, so all Phase-22 comparisons are internally
    consistent, and the measured disagreement with the canonical maps is bounded
    and reported rather than hidden.
    """
    p = np.asarray(prob)
    return (p.astype(np.float32) >= np.float32(threshold)).astype(np.uint8)


# --------------------------------------------------------------------------- #
# Model loading (diagnostic inference ONLY; never training)
# --------------------------------------------------------------------------- #
def load_frozen_medfilm(device: torch.device):
    """Load ``best.pt`` for the frozen Phase-21 reference. Fail-closed on SHA.

    Returns ``(model, provenance)``. Raises if the checkpoint SHA disagrees with
    the Phase-21 final freeze, if the freeze is not verified, or if the
    checkpoint is not byte-identical to the Phase-21 binding.
    """
    from src.models.film import GlobalMedFiLM
    from scripts.training.phase21_common import CONFIG

    freeze = load_json(PHASE21_FREEZE)
    if freeze.get("freeze_verified") is not True:
        raise RuntimeError("Phase-21 freeze is not verified")
    if freeze.get("phase22_started") is True:
        raise RuntimeError("freeze says Phase 22 already started (unexpected)")
    expected = freeze["training"]["best_checkpoint_sha256"]
    observed = sha256_file(PHASE21_BEST_CKPT)
    if observed != expected:
        raise RuntimeError(f"best.pt SHA drift: {observed} != {expected}")

    ck = torch.load(PHASE21_BEST_CKPT, map_location=device, weights_only=False)
    m = CONFIG["model"]
    model = GlobalMedFiLM(
        task_count=m["task_count"], in_channels=m["in_channels"],
        out_channels=m["out_channels"], channels=tuple(m["channels"]),
        task_embedding_dim=m["task_embedding_dim"],
        film_hidden_dim=m["film_hidden_dim"],
    ).to(device)
    model.load_state_dict(ck["model_state"])
    model.eval()
    n_params = int(sum(p.numel() for p in model.parameters() if p.requires_grad))
    if n_params != freeze["training"]["model_params"]:
        raise RuntimeError(f"param count drift: {n_params} != {freeze['training']['model_params']}")

    prov = {
        "experiment_id": EXPERIMENT_ID,
        "architecture_id": ARCHITECTURE_ID,
        "checkpoint_path": str(PHASE21_BEST_CKPT.relative_to(ROOT)).replace("\\", "/"),
        "checkpoint_sha256": observed,
        "checkpoint_epoch": int(ck.get("epoch", -1)),
        "param_count": n_params,
        "phase21_freeze_sha256": sha256_file(PHASE21_FREEZE),
        "training_performed_in_phase22": False,
    }
    return model, prov


# --------------------------------------------------------------------------- #
# Prediction persistence (diagnostic product, clearly separated from Phase 21)
# --------------------------------------------------------------------------- #
def save_diagnostic_npz(kind: str, size: int, sample_id: str,
                        prob: np.ndarray, threshold: float = THRESHOLD) -> Path:
    out = PHASE22_PRED_ROOT / kind / f"sz{size}" / f"{sample_id}.npz"
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out,
        prob=prob.astype(np.float16),
        pred=(prob >= threshold).astype(np.uint8),
    )
    return out


# --------------------------------------------------------------------------- #
# TEST lock
# --------------------------------------------------------------------------- #
def verify_no_test_access() -> dict:
    """Confirm the TEST lock is intact and no TEST artifact is referenced."""
    from src.utils.test_lock import verify_test_lock
    verify_test_lock(str(ROOT))
    return {"test_image_reads": 0, "test_mask_reads": 0,
            "test_inference": 0, "test_visualization": 0}


def assert_no_test_path(path_like) -> None:
    s = str(path_like).lower().replace("\\", "/")
    for needle in ("external_test_ds", "/test/", "phase4_v3/test"):
        if needle in s:
            raise RuntimeError(f"refusing to touch a TEST-resembling path: {path_like}")


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #
def paired_domain_stratified_bootstrap(values_a: np.ndarray, values_b: np.ndarray,
                                       domains: np.ndarray, n_boot: int = 2000,
                                       seed: int = 42, alpha: float = 0.05) -> dict:
    """Paired, domain-stratified percentile bootstrap of mean(a) - mean(b).

    Draws a SINGLE resampled index set per bootstrap replicate and applies it to
    BOTH arms (paired), stratified by domain so each domain's VAL share is held
    fixed. Returns the point estimate, the CI, and the two-sided p-value.
    """
    rng = np.random.default_rng(seed)
    a = np.asarray(values_a, dtype=np.float64)
    b = np.asarray(values_b, dtype=np.float64)
    d = np.asarray(domains)
    if not (a.shape == b.shape == d.shape):
        raise ValueError("paired bootstrap requires identically shaped arrays")

    point = float(a.mean() - b.mean())
    strata = [np.where(d == name)[0] for name in sorted(set(d.tolist()))]
    deltas = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        idx = np.concatenate([rng.choice(s, size=s.size, replace=True) for s in strata])
        deltas[i] = a[idx].mean() - b[idx].mean()
    lo = float(np.percentile(deltas, 100 * alpha / 2))
    hi = float(np.percentile(deltas, 100 * (1 - alpha / 2)))
    # two-sided p: fraction of the bootstrap distribution on the wrong side of 0
    p = float(2 * min((deltas <= 0).mean(), (deltas >= 0).mean()))
    return {
        "delta": point, "ci_low": lo, "ci_high": hi, "p_value": min(p, 1.0),
        "ci_excludes_zero": bool(lo > 0 or hi < 0),
        "n_boot": int(n_boot), "seed": int(seed), "alpha": float(alpha),
        "unit": "image", "paired": True, "domain_stratified": True,
        "n_strata": len(strata),
    }


def macro_domain_dice(rows: list[dict]) -> tuple[float, dict]:
    """Unweighted mean of the four per-domain mean per-image Dice values."""
    per = {}
    for name in DATASET_ORDER:
        vals = [r["dice"] for r in rows if r["dataset"] == name]
        if vals:
            per[name] = float(np.mean(vals))
    if not per:
        return float("nan"), {}
    return float(np.mean(list(per.values()))), per
