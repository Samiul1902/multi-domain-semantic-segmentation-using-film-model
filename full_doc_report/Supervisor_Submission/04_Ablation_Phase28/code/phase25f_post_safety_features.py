"""Phase 25F — frozen S_omega (BARRPostSafetyV1) input-feature definitions.

Single source of truth for the exact 20-D GT-free input vector frozen by
supervisor ruling F3 (§7 of the repair work order):

    indices 0..15   sixteen numeric post-refinement features
    indices 16..19  four fixed one-hot task indicators

This module performs NO model construction / training / forward pass. It only
turns two 256x256 probability crops plus two frozen Phase25B geometry scalars
into the 16 numeric features (pure numpy/scipy array arithmetic).

Thresholds used here:
    t_seg = 0.50 is the already-frozen SEGMENTATION OUTPUT threshold.
    It is NOT the S_omega accept threshold (which is a separate 0.50).
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

T_SEG = 0.50
EPS = 1e-7
N_PIX = 256 * 256
STRUCT8 = np.ones((3, 3), dtype=bool)          # 8-connectivity / 3x3 all-ones

# --------------------------------------------------------------------------- #
# exact numeric feature order (frozen; do not reorder)
# --------------------------------------------------------------------------- #
NUMERIC_FEATURES = [
    (0, "global_prob_mean",
     "mean(P_g)",
     "P_g (canonical global probability crop)",
     "dimensionless probability in [0,1]", "STANDARDIZED_FIT_ONLY_DDOF0"),
    (1, "refined_prob_mean",
     "mean(P_r)",
     "P_r (canonical OOF refined probability crop)",
     "dimensionless probability in [0,1]", "STANDARDIZED_FIT_ONLY_DDOF0"),
    (2, "mean_abs_prob_change",
     "mean(abs(P_r - P_g))",
     "P_g, P_r",
     "dimensionless probability in [0,1]", "STANDARDIZED_FIT_ONLY_DDOF0"),
    (3, "max_abs_prob_change",
     "max(abs(P_r - P_g))",
     "P_g, P_r",
     "dimensionless probability in [0,1]", "STANDARDIZED_FIT_ONLY_DDOF0"),
    (4, "frac_abs_prob_change_ge_0p10",
     "mean(abs(P_r - P_g) >= 0.10)",
     "P_g, P_r",
     "fraction in [0,1]", "STANDARDIZED_FIT_ONLY_DDOF0"),
    (5, "global_entropy_mean",
     "mean(H(P_g)); H(p) = -[p_c*log2(p_c) + (1-p_c)*log2(1-p_c)], "
     "p_c = clip(p, 1e-7, 1-1e-7)",
     "P_g",
     "bits in [0,1]", "STANDARDIZED_FIT_ONLY_DDOF0"),
    (6, "refined_entropy_mean",
     "mean(H(P_r)); H(p) = -[p_c*log2(p_c) + (1-p_c)*log2(1-p_c)], "
     "p_c = clip(p, 1e-7, 1-1e-7)",
     "P_r",
     "bits in [0,1]", "STANDARDIZED_FIT_ONLY_DDOF0"),
    (7, "global_foreground_fraction",
     "mean(B_g); B_g(x) = 1[P_g(x) >= 0.50]",
     "P_g",
     "fraction in [0,1]", "STANDARDIZED_FIT_ONLY_DDOF0"),
    (8, "refined_foreground_fraction",
     "mean(B_r); B_r(x) = 1[P_r(x) >= 0.50]",
     "P_r",
     "fraction in [0,1]", "STANDARDIZED_FIT_ONLY_DDOF0"),
    (9, "binary_xor_fraction",
     "mean(B_g XOR B_r)",
     "P_g, P_r",
     "fraction in [0,1]", "STANDARDIZED_FIT_ONLY_DDOF0"),
    (10, "global_component_count",
     "number of 8-connected components in B_g (3x3 all-ones structuring element)",
     "P_g",
     "count (cast to float32)", "STANDARDIZED_FIT_ONLY_DDOF0"),
    (11, "refined_component_count",
     "number of 8-connected components in B_r (3x3 all-ones structuring element)",
     "P_r",
     "count (cast to float32)", "STANDARDIZED_FIT_ONLY_DDOF0"),
    (12, "global_boundary_fraction",
     "boundary_fraction(B_g); E = binary_erosion(B, 3x3 ones, border_value=0); "
     "boundary = B AND NOT E; boundary_fraction = sum(boundary)/(256*256)",
     "P_g",
     "fraction in [0,1]", "STANDARDIZED_FIT_ONLY_DDOF0"),
    (13, "refined_boundary_fraction",
     "boundary_fraction(B_r); E = binary_erosion(B, 3x3 ones, border_value=0); "
     "boundary = B AND NOT E; boundary_fraction = sum(boundary)/(256*256)",
     "P_r",
     "fraction in [0,1]", "STANDARDIZED_FIT_ONLY_DDOF0"),
    (14, "predicted_roi_area_fraction",
     "frozen Phase25B corrected in-canvas ROI area / 512^2, "
     "area = max(0,min(512,x2)-max(0,x1)) * max(0,min(512,y2)-max(0,y1))",
     "data_cache/phase25b_barr_pre_refinement_features_v1_2 (scalar index 200)",
     "fraction in [0,1]", "STANDARDIZED_FIT_ONLY_DDOF0"),
    (15, "predicted_roi_side_normalized",
     "predicted_roi_side / 512.0",
     "data_cache/phase25b_barr_pre_refinement_features_v1_2 (scalar index 201)",
     "dimensionless in [0,1.5]", "STANDARDIZED_FIT_ONLY_DDOF0"),
]

ONEHOT_FEATURES = [
    (16, "task_0_ISIC", "1 if task_id == 0 (ISIC) else 0"),
    (17, "task_1_BUSI", "1 if task_id == 1 (BUSI) else 0"),
    (18, "task_2_KVASIR", "1 if task_id == 2 (KVASIR) else 0"),
    (19, "task_3_KUB", "1 if task_id == 3 (KUB) else 0"),
]

EXCLUDED_INPUTS = [
    "GT mask", "DeltaDice", "gain_category", "global_dice",
    "candidate_refined_dice", "BENEFICIAL/HARMFUL/NEUTRAL label", "patient_id",
    "group_id", "mask path", "GT object size", "benefit-router delta_hat",
    "resource lambda", "budget", "routing threshold", "refiner hidden feature maps",
    "new image encoder features",
]


# --------------------------------------------------------------------------- #
# feature equations
# --------------------------------------------------------------------------- #
def entropy_map(p: np.ndarray) -> np.ndarray:
    """Per-pixel Shannon entropy in bits: H(p) = -[p_c log2 p_c + (1-p_c) log2(1-p_c)]."""
    pc = np.clip(p.astype(np.float64), EPS, 1.0 - EPS)
    h = -(pc * np.log2(pc) + (1.0 - pc) * np.log2(1.0 - pc))
    return h


def component_count(binary: np.ndarray) -> int:
    """Number of 8-connected components (3x3 all-ones structuring element)."""
    _, n = ndi.label(binary.astype(bool), structure=STRUCT8)
    return int(n)


def boundary_fraction(binary: np.ndarray) -> float:
    """boundary = B AND NOT erosion(B); fraction of the 256x256 crop."""
    b = binary.astype(bool)
    eroded = ndi.binary_erosion(b, structure=STRUCT8, border_value=0)
    boundary = np.logical_and(b, np.logical_not(eroded))
    return float(boundary.sum()) / float(N_PIX)


def compute_numeric_features(p_g: np.ndarray, p_r: np.ndarray,
                             predicted_roi_area_fraction: float,
                             predicted_roi_side: float) -> np.ndarray:
    """Return the frozen 16-D numeric feature vector (float32)."""
    pg = np.asarray(p_g, dtype=np.float32)
    pr = np.asarray(p_r, dtype=np.float32)
    diff = np.abs(pr - pg)
    b_g = (pg >= np.float32(T_SEG))
    b_r = (pr >= np.float32(T_SEG))

    f = np.empty(16, dtype=np.float32)
    f[0] = np.float32(pg.mean())
    f[1] = np.float32(pr.mean())
    f[2] = np.float32(diff.mean())
    f[3] = np.float32(diff.max())
    f[4] = np.float32(np.mean(diff >= np.float32(0.10)))
    f[5] = np.float32(entropy_map(pg).mean())
    f[6] = np.float32(entropy_map(pr).mean())
    f[7] = np.float32(b_g.mean())
    f[8] = np.float32(b_r.mean())
    f[9] = np.float32(np.mean(np.logical_xor(b_g, b_r)))
    f[10] = np.float32(component_count(b_g))
    f[11] = np.float32(component_count(b_r))
    f[12] = np.float32(boundary_fraction(b_g))
    f[13] = np.float32(boundary_fraction(b_r))
    f[14] = np.float32(predicted_roi_area_fraction)
    f[15] = np.float32(float(predicted_roi_side) / 512.0)
    return f


def onehot(task_id: int) -> np.ndarray:
    """4-D fixed one-hot over the frozen task mapping ISIC=0, BUSI=1, KVASIR=2, KUB=3."""
    v = np.zeros(4, dtype=np.float32)
    v[int(task_id)] = 1.0
    return v


def build_input_vector(p_g: np.ndarray, p_r: np.ndarray,
                       predicted_roi_area_fraction: float, predicted_roi_side: float,
                       task_id: int) -> np.ndarray:
    """Full 20-D GT-free S_omega input vector (float32)."""
    return np.concatenate([
        compute_numeric_features(p_g, p_r, predicted_roi_area_fraction, predicted_roi_side),
        onehot(task_id),
    ]).astype(np.float32)
