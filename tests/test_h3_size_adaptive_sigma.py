"""Unit tests for the H3 (A_TARGET_SUPPORT_REDESIGN) size-adaptive sigma change.

Pure / fabricated only. No real data, no model, no CUDA, no forward pass.
These tests lock the backward-compatibility and non-degeneracy contracts that the
H3 pre-execution design repair requires.

Frozen mapping under test:
    sigma_i = clip(0.35 + 0.40 * sqrt(A128_i / A_ref), 0.35, 0.75),  A_ref = 14.0
"""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.inference.heatmap_targets import (
    heatmap_space_component_areas,
    make_gaussian_heatmap,
)
from src.data.kub_localizer_dataset import KUBLocalizerDataset
from src.training.clean_v3_selection import (
    H3_SUPPLY_TERM_NAMES,
    build_h3_supply_selection_tuple,
    select_h3_supply_epoch,
)

A_REF = 14.0
SIGMA_MIN = 0.35
SIGMA_MAX = 0.75


def _sigma_for(area):
    s = SIGMA_MIN + (SIGMA_MAX - SIGMA_MIN) * math.sqrt(max(area, 0.0) / A_REF)
    return min(SIGMA_MAX, max(SIGMA_MIN, s))


# ---------------------------------------------------------------------------
# 1. Backward compatibility: fixed-sigma behaviour is byte-identical.
# ---------------------------------------------------------------------------
def test_backward_compat_fixed_sigma_unchanged():
    centroids = [(10, 20), (40, 45)]
    a = make_gaussian_heatmap(64, centroids, 5)
    b = make_gaussian_heatmap(64, centroids, 5, component_areas=None)
    assert np.array_equal(a, b)
    assert a[10, 20] == 1.0 and a[40, 45] == 1.0
    assert (a >= 0.0).all() and (a <= 1.0).all()


def test_size_adaptive_large_area_caps_at_sigma_max_like_fixed():
    # A huge component area -> sigma saturates at sigma_max == historical fixed behaviour.
    centroids = [(32, 32)]
    h_adapt = make_gaussian_heatmap(64, centroids, 0.75, component_areas=[1e9], A_ref=A_REF)
    h_fixed = make_gaussian_heatmap(64, centroids, 0.75)
    assert np.allclose(h_adapt, h_fixed)


# ---------------------------------------------------------------------------
# 2. H3 branch: smaller components get a sharper (smaller-sigma) peak.
# ---------------------------------------------------------------------------
def test_size_adaptive_smaller_area_gives_sharper_peak():
    centroids = [(32, 16), (32, 48)]
    h_fixed = make_gaussian_heatmap(64, centroids, 0.75)
    h_adapt = make_gaussian_heatmap(
        64, centroids, 0.75, component_areas=[1, 100], A_ref=A_REF,
        sigma_min=SIGMA_MIN, sigma_max=SIGMA_MAX,
    )
    # Tiny component (area 1) -> sigma ~0.457 -> much sharper than fixed sigma 0.75.
    # At (32, 19) (3 px from the tiny centre) the fixed Gaussian is still ~3e-4,
    # the adaptive one is ~1e-10.
    assert h_adapt[32, 19] < h_fixed[32, 19]
    # Large component (area 100) -> capped at 0.75 -> matches fixed there.
    assert np.allclose(h_adapt[32, 48], h_fixed[32, 48])


# ---------------------------------------------------------------------------
# 3. Non-degeneracy of the frozen mapping (unit-level).
# ---------------------------------------------------------------------------
def test_formula_spread_monotonic_bounded():
    areas = [1, 2, 5, 14, 40, 100, 278]
    sigmas = [_sigma_for(a) for a in areas]
    assert len({round(s, 6) for s in sigmas}) > 1          # spread, not a single value
    assert all(SIGMA_MIN <= s <= SIGMA_MAX for s in sigmas)  # bounded by ceiling/floor
    assert sigmas == sorted(sigmas)                         # monotonic in area
    assert sigmas[0] < sigmas[-1]                           # tiny < large
    assert not all(abs(s - SIGMA_MAX) < 1e-9 for s in sigmas)  # not all at ceiling


def test_formula_floor_and_ceiling_reachable():
    assert _sigma_for(0.0) == SIGMA_MIN                       # floor reachable
    assert _sigma_for(1e9) == SIGMA_MAX                       # ceiling reachable


# ---------------------------------------------------------------------------
# 4. heatmap_space_component_areas counts foreground in heatmap space.
# ---------------------------------------------------------------------------
def test_heatmap_space_component_areas_two_isolated_pixels():
    # 12x12 padded mask, factor = 12 // 3 = 4 -> 3x3 heatmap.
    # Place two pixels that are NOT 8-adjacent (separated by an empty centre cell).
    padded = np.zeros((12, 12), dtype=bool)
    padded[0, 0] = True
    padded[8, 8] = True
    label_map, areas = heatmap_space_component_areas(padded, 12, 3)
    assert label_map.shape == (3, 3)
    assert int(areas.sum()) == 2          # two foreground pixels
    assert len(areas) == 3                # [background, comp1, comp2]


def test_heatmap_space_component_areas_connected_blob():
    padded = np.zeros((4, 4), dtype=bool)
    padded[0, 0] = True
    padded[0, 2] = True                   # same heatmap row, adjacent -> one component
    label_map, areas = heatmap_space_component_areas(padded, 4, 2)
    assert int(areas.max()) == 2          # one component with 2 foreground pixels
    assert int(areas.sum()) == 2


# ---------------------------------------------------------------------------
# 5. Dataset opt-in flag is additive (default False => Phase-13B behaviour).
# ---------------------------------------------------------------------------
def test_dataset_accepts_size_adaptive_flag_default_false():
    df = pd.DataFrame(columns=[
        "view_type", "image_path", "mask_path", "sample_id",
        "patient_id", "category", "width", "height",
    ])
    ds_off = KUBLocalizerDataset(df, "TRAIN", 512, 0.75, size_adaptive_sigma=False)
    assert ds_off.size_adaptive_sigma is False
    ds_on = KUBLocalizerDataset(
        df, "TRAIN", 512, 0.75, size_adaptive_sigma=True, A_ref=A_REF,
        sigma_min=SIGMA_MIN, sigma_max=SIGMA_MAX,
    )
    assert ds_on.size_adaptive_sigma is True
    assert ds_on.A_ref == A_REF


# ---------------------------------------------------------------------------
# 6. Frozen H3 supply-axis checkpoint selection (2-term rule).
# ---------------------------------------------------------------------------
def test_h3_supply_tuple_order_and_names():
    assert build_h3_supply_selection_tuple(0.80, 1.0) == (0.80, -1.0)
    assert H3_SUPPLY_TERM_NAMES == ("val_localization_recall", "negative_val_loss")


def test_h3_supply_higher_recall_wins():
    better = select_h3_supply_epoch(0.80, 2.0, best_score=None, epoch=1)
    assert better.is_new_best is True
    worse = select_h3_supply_epoch(
        0.70, 2.0, best_score=better.best_score, best_epoch=1, bad_epochs=0, epoch=2,
    )
    assert worse.is_new_best is False
    assert worse.bad_epochs == 1
    assert worse.best_epoch == 1


def test_h3_supply_loss_breaks_tie():
    first = select_h3_supply_epoch(0.80, 1.0, best_score=None, epoch=1)
    tied_recall_higher_loss = select_h3_supply_epoch(
        0.80, 2.0, best_score=first.best_score, best_epoch=1, bad_epochs=0, epoch=2,
    )
    assert tied_recall_higher_loss.is_new_best is False  # same recall, worse loss
    better_loss = select_h3_supply_epoch(
        0.80, 0.5, best_score=first.best_score, best_epoch=1, bad_epochs=0, epoch=3,
    )
    assert better_loss.is_new_best is True               # same recall, better loss


def test_h3_supply_stops_after_patience():
    best = select_h3_supply_epoch(0.90, 1.0, best_score=None, epoch=1)
    out = select_h3_supply_epoch(
        0.10, 9.0, best_score=best.best_score, best_epoch=1, bad_epochs=14, epoch=16,
    )
    assert out.is_new_best is False
    assert out.bad_epochs == 15
    assert out.stopped is True
