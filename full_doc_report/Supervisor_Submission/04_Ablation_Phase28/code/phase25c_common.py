"""Phase 25C -- canonical shared module for leakage-safe OOF paired-gain labels.

Single source of truth for:
    * the frozen constants (thresholds, categories, folds, population)
    * loading the frozen Phase25A ROI-0.30 cache (GA-free p_global, crops, geometry)
    * the fold-specific refiner OOF inference (FP32, eval, deterministic order)
    * the frozen inverse-crop full-field reconstruction + deterministic fusion rule
    * the canonical Dice metric (imported from src.metrics.evaluation_metrics)
    * label computation and integrity checks

Phase 25C creates LABELS only. It does NOT train the router, does NOT train the
16-D task embedding, does NOT read ROUTER_HOLDOUT / VAL / TEST.

Nothing in this module inspects DeltaDice before the inference binding is frozen.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

ROOT = Path(r"D:/Softfors/jup")

# --------------------------------------------------------------------------- #
# Frozen constants
# --------------------------------------------------------------------------- #
METHOD = "RA-MedFiLM-BARR"
ARCH_REVISION = "ra_medfilm_barr_narrowed_v1_2"
SEED = 42

ROI_PROPOSAL_THRESHOLD = 0.30        # ROI_PROPOSAL role only
SEGMENTATION_OUTPUT_THRESHOLD = 0.50 # SEGMENTATION_OUTPUT role (Dice masks)
REGIONAL_INPUT_RESOLUTION = 256
REGIONAL_CANVAS_RESOLUTION = 512
CONTEXT_EXPANSION_FACTOR = 1.50

# Phase-24 frozen categories (boundary inclusion exact)
BENEFICIAL_DELTA = 0.02   # DeltaDice >= +0.02
HARMFUL_DELTA = -0.01     # DeltaDice <= -0.01
# NEUTRAL otherwise

ROUTER_DEVELOPMENT_N = 4957
ROUTER_HOLDOUT_N = 875
ACTION_AVAILABLE_N = 4957
ACTION_UNAVAILABLE_N = 0
OUTER_FOLDS = (0, 1, 2)

# canonical batch semantics (contiguous chunks in canonical order)
INFERENCE_BATCH = 8

# ---- frozen hashes -------------------------------------------------------- #
EXPECTED = {
    "predecessor_terminal": (
        "PHASE25B_HANDOFF_SEMANTICS_REPAIRED__PHASE25C_OOF_PAIRED_GAIN_LABEL_"
        "GENERATION_ELIGIBLE_NOT_STARTED"
    ),
    "phase24_notebook_sha256": "9d62384e8afa2f35e985eac219711df0334fbfe72c33c0edd29ff3f4897d4027",
    "phase25a_notebook_sha256": "fd2bab0168eb3477125c655ada1bd5eb4b060f41a5b354fdbaaf6fd621dfb2dd",
    "phase25b_notebook_sha256": "acdfe90a5042ef364c5ab28ec67ecd3fe3146b30e1e5715a2631a36deb4dc38a",
    "phase25b_matrix_sha256": "9c241963b54f23de1c9671ff6670dde7d6f7e2510869ef5ebc1baf3f7c833e0a",
    "phase25b_metadata_sha256": "ee8c304350d28d907c053a355da1f878ff7f9dd137761034283459aeed071093",
    "phase25b_schema_sha256": "da76aa34f14006146f46ca799f173378274d8c9d0792dc18edb30711a2486dd4",
    "phase21_global_sha256": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
    "phase25a_final_refiner_sha256": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
    "split_manifest_sha256": "b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555",
    "fold0_checkpoint_sha256": "40b7573a4a15483f895fece8b9624f4f23b1ee040e294b7594ed3cdf8438fc1c",
    "fold1_checkpoint_sha256": "512cc116b2a1baa5368711f438dfd0b2aabff1448d02fbc0c369b91da8ffc1ce",
    "fold2_checkpoint_sha256": "1259e2d938a7e6e81ad9ddce4bfc25189e20858e8f201d167663c26c72c269ec",
    "roi_proposal_threshold": ROI_PROPOSAL_THRESHOLD,
    "segmentation_output_threshold": SEGMENTATION_OUTPUT_THRESHOLD,
    "router_development_n": ROUTER_DEVELOPMENT_N,
    "router_holdout_n": ROUTER_HOLDOUT_N,
}

# paths
SPLIT_MANIFEST = ROOT / "reports" / "audits" / "phase24_router_split_manifest.csv"
ROI030_CACHE = ROOT / "data_cache" / "phase25a_barr_roi030_cache"
ROI030_FOLDS = ROI030_CACHE / "folds"
ROI030_MANIFEST = ROI030_CACHE / "cache_manifest.json"
CKPT_DIR = ROOT / "checkpoints" / "phase25a_barr_regional_refiner_v1_1_roi030"
FOLD_CKPT = {
    0: CKPT_DIR / "fold0" / "best.pt",
    1: CKPT_DIR / "fold1" / "best.pt",
    2: CKPT_DIR / "fold2" / "best.pt",
}
PHASE25A_FINAL_CKPT = CKPT_DIR / "final" / "final.pt"

PHASE25B_CACHE = ROOT / "data_cache" / "phase25b_barr_pre_refinement_features_v1_2"
PHASE25B_METADATA = PHASE25B_CACHE / "metadata.csv"

LABEL_DIR = ROOT / "data_cache" / "phase25c_barr_oof_paired_gain_labels_v1_2"
LABEL_CSV = LABEL_DIR / "phase25c_oof_paired_gain_labels.csv"
LABEL_MANIFEST = LABEL_DIR / "label_manifest.json"

# label table columns (canonical §16)
LABEL_COLUMNS = [
    "sample_id", "feature_row_index", "task_id", "domain", "outer_fold",
    "action_available", "fold_refiner_checkpoint_sha", "global_dice",
    "candidate_refined_dice", "delta_dice", "gain_category",
    "roi_proposal_threshold", "segmentation_output_threshold",
]
LABEL_PROVENANCE_COLUMNS = [
    "crop_side_pixels", "predicted_roi_area_fraction", "candidate_mask_sha256",
]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_array(a: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def jload(p: Path) -> dict:
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def jdump(obj, p: Path) -> None:
    Path(p).write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Population / folds
# --------------------------------------------------------------------------- #
def load_development() -> pd.DataFrame:
    """Canonical ROUTER_DEVELOPMENT frame in canonical (domain, sample_id) order."""
    sm = pd.read_csv(SPLIT_MANIFEST)
    dev = sm[sm["split_role"] == "ROUTER_DEVELOPMENT"].copy()
    dev = dev.sort_values(["dataset", "sample_id"]).reset_index(drop=True)
    return dev


def load_outer_fold_assignment() -> Dict[str, int]:
    """sample_id -> outer_fold from the frozen fold manifests (union of outer targets)."""
    assign: Dict[str, int] = {}
    for k in OUTER_FOLDS:
        f = pd.read_csv(ROI030_FOLDS / f"fold{k}_outer_target.csv")
        for sid in f["sample_id"].astype(str):
            if sid in assign and assign[sid] != k:
                raise AssertionError(f"sample {sid} in two outer targets")
            assign[sid] = k
    return assign


def load_fold_sets() -> Dict[str, set]:
    out: Dict[str, set] = {}
    for k in OUTER_FOLDS:
        for role in ("outer_target", "fit", "early_stop"):
            f = pd.read_csv(ROI030_FOLDS / f"fold{k}_{role}.csv")
            out[f"fold{k}_{role}"] = set(f["sample_id"].astype(str))
    out["final_all_development"] = set(
        pd.read_csv(ROI030_FOLDS / "final_all_development.csv")["sample_id"].astype(str)
    )
    return out


# --------------------------------------------------------------------------- #
# Cache access (read-only, hash-verified)
# --------------------------------------------------------------------------- #
class DomainCache:
    """Read-only mmap access to one domain's canonical ROI-0.30 cache."""

    def __init__(self, domain: str):
        d = ROI030_CACHE / domain
        self.domain = domain
        self.prob512 = np.load(d / "prob512.npy", mmap_mode="r")      # (n,512,512) f32
        self.rgb_crop = np.load(d / "rgb_crop.npy", mmap_mode="r")    # (n,3,256,256) u8
        self.prob_crop = np.load(d / "prob_crop.npy", mmap_mode="r")  # (n,1,256,256) f16
        self.gt_crop = np.load(d / "gt_crop.npy", mmap_mode="r")      # (n,1,256,256) u8
        self.action = np.load(d / "action.npy")                        # (n,) u8
        self.meta = pd.read_csv(d / "meta.csv")
        self.pos = {str(s): i for i, s in enumerate(self.meta["sample_id"].astype(str))}

    def index(self, sample_id: str) -> int:
        return self.pos[str(sample_id)]


# --------------------------------------------------------------------------- #
# Refiner input / inverse transform
# --------------------------------------------------------------------------- #
def build_refiner_input(rgb_crop_u8: np.ndarray, prob_crop_f16: np.ndarray) -> np.ndarray:
    """Exact canonical 4x256x256 refiner input `[R,G,B,p_global_crop]`.

    Matches ``BARRRefinerCropDataset.__getitem__`` with ``train=False``:
        rgb  = uint8 / 255.0 (float32)
        prob = float16 -> float32
    """
    rgb = np.asarray(rgb_crop_u8, dtype=np.float32) / 255.0
    prob = np.asarray(prob_crop_f16, dtype=np.float32)
    return np.concatenate([rgb, prob], axis=0)          # (4,256,256)


def inverse_crop_to_canvas(refined_crop_256: np.ndarray, geom: dict,
                           canvas: int = REGIONAL_CANVAS_RESOLUTION
                           ) -> Tuple[np.ndarray, np.ndarray]:
    """Inverse of the frozen Phase25A crop: 256x256 crop probability -> canvas.

    Returns ``(crop_on_canvas, valid_mask)``:
      * ``crop_on_canvas``  : float32 (canvas, canvas), the refined probability
        resized back to the square ``crop_side_pixels`` support and placed at
        ``(y1, x1)``; zero outside.
      * ``valid_mask``      : bool (canvas, canvas), True where a real canvas
        pixel was written (i.e. inside the clipped window and inside the canvas).
    """
    from PIL import Image
    side = int(geom["crop_side_pixels"])
    y1, x1 = int(geom["y1"]), int(geom["x1"])
    pad_top, pad_left = int(geom["pad_top"]), int(geom["pad_left"])
    clip_y1, clip_y2 = int(geom["clip_y1"]), int(geom["clip_y2"])
    clip_x1, clip_x2 = int(geom["clip_x1"]), int(geom["clip_x2"])

    pil = Image.fromarray(np.ascontiguousarray(refined_crop_256, dtype=np.float32), mode="F")
    square = np.asarray(pil.resize((side, side), Image.Resampling.BILINEAR), dtype=np.float32)

    # out pixel (r,c) of the padded square maps to canvas
    # (y1 - pad_top + r, x1 - pad_left + c) == (clip_y1 + r, clip_x1 + c)
    # so clip_y1 = y1 + pad_top  (equivalently y1 = clip_y1 - pad_top).
    crop_on_canvas = np.zeros((canvas, canvas), dtype=np.float32)
    valid = np.zeros((canvas, canvas), dtype=bool)

    # square is side x side; the clipped window sits at offset (pad_top, pad_left)
    wy1, wy2 = pad_top, pad_top + (clip_y2 - clip_y1)
    wx1, wx2 = pad_left, pad_left + (clip_x2 - clip_x1)
    window = square[wy1:wy2, wx1:wx2]
    crop_on_canvas[clip_y1:clip_y2, clip_x1:clip_x2] = window
    valid[clip_y1:clip_y2, clip_x1:clip_x2] = True

    # sanity: y1 + pad_top == clip_y1  and  x1 + pad_left == clip_x1
    assert y1 + pad_top == clip_y1, (y1, pad_top, clip_y1)
    assert x1 + pad_left == clip_x1, (x1, pad_left, clip_x1)
    return crop_on_canvas, valid


def fuse_full_field(p_global: np.ndarray, refined_crop_256: np.ndarray,
                    geom: dict) -> Tuple[np.ndarray, np.ndarray]:
    """Frozen deterministic fusion: replace inside valid ROI, keep p_global outside.

    Returns ``(p_candidate_full, valid_mask)``.
    """
    crop_on_canvas, valid = inverse_crop_to_canvas(refined_crop_256, geom)
    p_candidate = np.array(p_global, dtype=np.float32, copy=True)
    p_candidate[valid] = crop_on_canvas[valid]
    return p_candidate, valid
