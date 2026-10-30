"""PHASE-13 PART-1D-A — static / synthetic tests (supervisor §24 cases A–R).

All tests are synthetic: no CUDA, no model construction, no image inference,
no proposal generation, no TEST construction.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.inference.phase13_part1d_predicted_region_inference import (  # noqa: E402
    EXPECTED_CASE_MODEL_ROWS,
    EXPECTED_COMPONENT_MODEL_ROWS,
    MODEL_CHECKPOINTS,
    MODELS,
    PRIMARY_VARIANT,
    assert_geometry_invariants,
    binarize,
    fuse_global_retained,
    oracle_gap_dice,
    parse_proposal_geometry,
    prepare_regional_crop_512,
    proposal_support_mask,
    regional_probability_native,
    restore_probability_to_full_native,
    restore_probability_to_native,
    retention_dice,
)

TABLES = ROOT / "reports" / "tables"


def _geom(y1, y2, x1, x2):
    return {"clip_y1": y1, "clip_y2": y2, "clip_x1": x1, "clip_x2": x2}


# ---- A: no proposals -> fused == global ----------------------------------
def test_A_no_proposals_fused_equals_global():
    g = np.full((6, 6), 0.8, dtype=np.float32)
    r = np.zeros((6, 6), dtype=np.float32)
    u = proposal_support_mask([], (6, 6))
    assert not u.any()
    fused = fuse_global_retained(g, r, u)
    assert np.array_equal(fused, g)


# ---- B: one proposal -> regional replaces only inside support ------------
def test_B_one_proposal_replaces_only_inside_support():
    g = np.full((8, 8), 0.9, dtype=np.float32)
    r = np.zeros((8, 8), dtype=np.float32)
    geom = [_geom(2, 5, 2, 5)]
    u = proposal_support_mask(geom, (8, 8))
    r[2:5, 2:5] = 0.1
    fused = fuse_global_retained(g, r, u)
    assert np.allclose(fused[2:5, 2:5], 0.1)
    outside = ~u
    assert np.array_equal(fused[outside], g[outside])


# ---- C: global > regional inside support -> regional STILL replaces ------
def test_C_regional_replaces_even_when_global_larger():
    g = np.full((8, 8), 0.95, dtype=np.float32)
    r = np.zeros((8, 8), dtype=np.float32)
    geom = [_geom(1, 4, 1, 4)]
    u = proposal_support_mask(geom, (8, 8))
    r[1:4, 1:4] = 0.2                      # regional LOWER than global
    fused = fuse_global_retained(g, r, u)
    assert np.allclose(fused[1:4, 1:4], 0.2)          # replacement, not max
    assert not np.allclose(fused[1:4, 1:4], 0.95)     # proves no max(G,R)


# ---- D: two overlapping proposals -> max among REGIONAL only -------------
def test_D_overlapping_regional_takes_max_of_regional():
    probs = [np.full((512, 512), 0.3, dtype=np.float32),
             np.full((512, 512), 0.7, dtype=np.float32)]
    # interior squares: side 4, no padding
    geoms = [_norm(_full_geom(0, 4, 0, 4, 0, 4, 0, 4, 0, 0, 0, 0, 4)),
             _norm(_full_geom(2, 6, 2, 6, 2, 6, 2, 6, 0, 0, 0, 0, 4))]
    r = regional_probability_native(probs, geoms, (8, 8))
    assert np.allclose(r[2:4, 2:4], 0.7)   # overlap -> max(0.3, 0.7)
    assert np.allclose(r[0:2, 0:2], 0.3)
    assert np.allclose(r[4:6, 4:6], 0.7)


# ---- E: outside union support -> global bitwise retained -----------------
def test_E_outside_union_global_bitwise_retained():
    rng = np.random.default_rng(0)
    g = rng.random((10, 10)).astype(np.float32)
    r = rng.random((10, 10)).astype(np.float32)
    u = proposal_support_mask([_geom(3, 6, 3, 6)], (10, 10))
    fused = fuse_global_retained(g, r, u)
    outside = ~u
    assert np.array_equal(fused[outside], g[outside])


# ---- F: FLOAT restore preserves float (no uint8 quantisation) ------------
def test_F_float_restore_no_uint8_quantisation():
    prob = np.linspace(0.0, 1.0, 512 * 512, dtype=np.float32).reshape(512, 512)
    geom = _norm(_full_geom(0, 5, 0, 5, 0, 5, 0, 5, 0, 0, 0, 0, 5))
    restored, _ = restore_probability_to_native(prob, geom, (5, 5))
    assert restored.dtype == np.float32
    assert not np.allclose(restored, np.round(restored * 255.0) / 255.0)


# ---- G: geometry not expanded by a second margin ------------------------
def _full_geom(y1, y2, x1, x2, clip_y1, clip_y2, clip_x1, clip_x2,
               pt, pb, pl, pr, side, margin=0.2):
    return {"y1": y1, "y2": y2, "x1": x1, "x2": x2,
            "clip_y1": clip_y1, "clip_y2": clip_y2,
            "clip_x1": clip_x1, "clip_x2": clip_x2,
            "pad_top": pt, "pad_bottom": pb, "pad_left": pl, "pad_right": pr,
            "crop_side_pixels": side, "effective_magnification": 512.0 / side,
            "margin": margin}


def _norm(raw):
    """Push a RAW frozen geometry record through the real Part-1D parser.

    ``_full_geom`` stores ``crop_side_pixels``; the parser adds the ``crop_side``
    alias and int-casts every coordinate. Every test goes through this path so it
    exercises the same normalisation the Part-1D-B driver will use.
    """
    return parse_proposal_geometry({"proposal_crop_geometry": json.dumps([raw])})[0]


def test_G_no_second_margin_applied():
    geom = _full_geom(10, 30, 30, 50, 10, 30, 30, 50, 0, 0, 0, 0, 20)
    row = {"proposal_crop_geometry": json.dumps([geom])}
    parsed = parse_proposal_geometry(row)
    assert parsed[0]["y1"] == 10 and parsed[0]["y2"] == 30
    assert parsed[0]["crop_side"] == 20
    assert parsed[0]["margin"] == 0.2


# ---- H: threshold applied after fusion ----------------------------------
def test_H_threshold_after_fusion():
    g = np.full((4, 4), 0.6, dtype=np.float32)
    r = np.full((4, 4), 0.4, dtype=np.float32)
    u = proposal_support_mask([_geom(0, 2, 0, 2)], (4, 4))
    fused = fuse_global_retained(g, r, u)
    binary = binarize(fused)
    assert binary[0:2, 0:2].all() is False or binary[0:2, 0:2].sum() == 0  # regional 0.4 -> 0
    assert binary[2:4, 2:4].all()                                           # global 0.6 -> 1


# ---- I: GT is not passed to proposal/fusion functions -------------------
def test_I_gt_not_passed_to_fusion():
    import inspect
    from scripts.inference import phase13_part1d_predicted_region_inference as m

    for fn in (m.proposal_support_mask, m.fuse_global_retained,
               m.regional_probability_native, m.parse_proposal_geometry):
        params = list(inspect.signature(fn).parameters)
        assert not any("gt" in p.lower() or "mask_gt" in p.lower() for p in params)


# ---- J: retention correct for positive oracle gain ---------------------
def test_J_retention_positive_gain():
    assert retention_dice(0.70, 0.80, 0.60) == pytest.approx(0.5)


# ---- K: retention > 1 preserved ----------------------------------------
def test_K_retention_above_one_preserved():
    assert retention_dice(0.90, 0.80, 0.60) == pytest.approx(1.5)


# ---- L: negative retention preserved -----------------------------------
def test_L_negative_retention_preserved():
    assert retention_dice(0.50, 0.80, 0.60) == pytest.approx(-0.5)


# ---- M: zero denominator -> None (not fabricated zero) -----------------
def test_M_zero_denominator_returns_none():
    assert retention_dice(0.60, 0.60, 0.60) is None
    assert retention_dice(0.70, 0.50, 0.60) is None   # negative denominator


# ---- N: four model identities exactly frozen ---------------------------
def test_N_four_frozen_models():
    assert tuple(MODELS) == ("unet", "attention_unet", "unetpp", "deeplabv3plus")
    assert set(MODEL_CHECKPOINTS) == set(MODELS)
    for name, exp in MODEL_CHECKPOINTS.items():
        assert "clean_v3" in exp, name


# ---- O: case-model rows = 412 -----------------------------------------
def test_O_case_model_rows():
    assert EXPECTED_CASE_MODEL_ROWS == 412


# ---- P: component-model rows = 608 ------------------------------------
def test_P_component_model_rows():
    assert EXPECTED_COMPONENT_MODEL_ROWS == 608


# ---- Q: gallery is exactly the Part-1C frozen 16 -----------------------
def test_Q_gallery_matches_part1c():
    g = pd.read_csv(TABLES / "phase13_part1c_gallery_selection.csv")
    assert len(g) == 16
    assert g["label"].eq("DETERMINISTIC_PREDICTION_INDEPENDENT_GALLERY_ONLY").all()


# ---- R: TEST never constructed ----------------------------------------
def test_R_test_never_constructed():
    import inspect

    import scripts.inference.phase13_part1d_predicted_region_inference as m

    src = inspect.getsource(m)
    assert "verify_test_lock" not in src      # no TEST lock interaction at all
    assert "test_split" not in src
    assert PRIMARY_VARIANT == "PREDICTED_REGION_FLOAT_GLOBAL_RETAINED"


def test_oracle_gap_dice_sign():
    assert oracle_gap_dice(0.70, 0.80) == pytest.approx(-0.10)


# ===========================================================================
# R1 — direct Phase-12 equivalence (supervisor cases S–AD)
# ===========================================================================
import importlib.util  # noqa: E402

PHASE12_PATH = ROOT / "notebooks" / "phasewise" / "phase_12_oracle_roi" / "code" / "phase12_oracle_inference.py"


def _phase12():
    spec = importlib.util.spec_from_file_location("p12_ref", PHASE12_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# interior, top-pad, bottom-pad, left-pad, right-pad, top-left corner, bottom-right corner
CASES = {
    "interior": dict(y1=100, y2=140, x1=100, x2=140, clip_y1=100, clip_y2=140,
                     clip_x1=100, clip_x2=140, pad_top=0, pad_bottom=0, pad_left=0,
                     pad_right=0, side=40),
    "top_edge": dict(y1=-10, y2=30, x1=100, x2=140, clip_y1=0, clip_y2=30,
                     clip_x1=100, clip_x2=140, pad_top=10, pad_bottom=0, pad_left=0,
                     pad_right=0, side=40),
    "bottom_edge": dict(y1=200, y2=240, x1=100, x2=140, clip_y1=200, clip_y2=220,
                        clip_x1=100, clip_x2=140, pad_top=0, pad_bottom=20, pad_left=0,
                        pad_right=0, side=40),
    "left_edge": dict(y1=100, y2=140, x1=-10, x2=30, clip_y1=100, clip_y2=140,
                      clip_x1=0, clip_x2=30, pad_top=0, pad_bottom=0, pad_left=10,
                      pad_right=0, side=40),
    "right_edge": dict(y1=100, y2=140, x1=180, x2=220, clip_y1=100, clip_y2=140,
                       clip_x1=180, clip_x2=200, pad_top=0, pad_bottom=0, pad_left=0,
                       pad_right=20, side=40),
    "top_left_corner": dict(y1=-8, y2=32, x1=-8, x2=32, clip_y1=0, clip_y2=32,
                            clip_x1=0, clip_x2=32, pad_top=8, pad_bottom=0, pad_left=8,
                            pad_right=0, side=40),
    "bottom_right_corner": dict(y1=188, y2=228, x1=188, x2=228, clip_y1=188,
                                clip_y2=210, clip_x1=188, clip_x2=210, pad_top=0,
                                pad_bottom=18, pad_left=0, pad_right=18, side=40),
}
NATIVE = (220, 220)


def _p1d(case):
    """Part-1D geometry: the RAW frozen record pushed through the real parser.

    The raw record stores ``crop_side_pixels``; the parser normalises it to the
    ``crop_side`` alias and int-casts every coordinate. Tests therefore exercise
    exactly the path the Part-1D-B driver will use, rather than a hand-built dict.
    """
    c = CASES[case]
    raw = _full_geom(c["y1"], c["y2"], c["x1"], c["x2"], c["clip_y1"], c["clip_y2"],
                     c["clip_x1"], c["clip_x2"], c["pad_top"], c["pad_bottom"],
                     c["pad_left"], c["pad_right"], c["side"])
    return parse_proposal_geometry({"proposal_crop_geometry": json.dumps([raw])})[0]


def _p12_geom(case):
    """Phase-12 reference geometry dict (drops the Part-1D ``crop_side_pixels`` alias)."""
    g = dict(_p1d(case))
    g.pop("crop_side_pixels", None)
    return g


# ---- S: parser preserves all square/pad fields --------------------------
def test_S_parser_preserves_all_geometry_fields():
    row = {"proposal_crop_geometry": json.dumps([_p1d("bottom_edge")])}
    g = parse_proposal_geometry(row)[0]
    for k in ("y1", "y2", "x1", "x2", "clip_y1", "clip_y2", "clip_x1", "clip_x2",
              "pad_top", "pad_bottom", "pad_left", "pad_right", "crop_side",
              "effective_magnification", "margin"):
        assert k in g, k


# ---- T: interior crop equals Phase-12 ----------------------------------
def test_T_interior_crop_matches_phase12(tmp_path):
    p12 = _phase12()
    rng = np.random.default_rng(1)
    img = (rng.random(NATIVE) * 255).astype(np.uint8)
    from PIL import Image
    p = tmp_path / "img.png"
    Image.fromarray(img).save(p)
    ref = p12.crop_tensor(p, _p12_geom("interior")).numpy()
    mine = prepare_regional_crop_512(img, _p1d("interior"))
    assert np.max(np.abs(ref[0, 0] - mine)) <= 1e-7


# ---- U: top-edge padded crop equals Phase-12 ---------------------------
def test_U_top_edge_padded_crop_matches_phase12(tmp_path):
    p12 = _phase12()
    rng = np.random.default_rng(2)
    img = (rng.random(NATIVE) * 255).astype(np.uint8)
    from PIL import Image
    p = tmp_path / "img.png"
    Image.fromarray(img).save(p)
    ref = p12.crop_tensor(p, _p12_geom("top_edge")).numpy()
    mine = prepare_regional_crop_512(img, _p1d("top_edge"))
    assert np.max(np.abs(ref[0, 0] - mine)) <= 1e-7


# ---- V: corner padded crop equals Phase-12 -----------------------------
def test_V_corner_padded_crop_matches_phase12(tmp_path):
    p12 = _phase12()
    rng = np.random.default_rng(3)
    img = (rng.random(NATIVE) * 255).astype(np.uint8)
    from PIL import Image
    p = tmp_path / "img.png"
    Image.fromarray(img).save(p)
    for case in ("top_left_corner", "bottom_right_corner"):
        ref = p12.crop_tensor(p, _p12_geom(case)).numpy()
        mine = prepare_regional_crop_512(img, _p1d(case))
        assert np.max(np.abs(ref[0, 0] - mine)) <= 1e-7, case


def _prob512(seed=7):
    rng = np.random.default_rng(seed)
    return rng.random((512, 512)).astype(np.float32)


# ---- W: interior restore equals Phase-12 restore_float -----------------
def test_W_interior_restore_matches_phase12():
    p12 = _phase12()
    prob = _prob512()
    ref = p12.restore_float(prob, _p12_geom("interior"), NATIVE)
    mine = restore_probability_to_full_native(prob, _p1d("interior"), NATIVE)
    assert mine.shape == NATIVE
    assert np.max(np.abs(ref - mine)) <= 1e-7


# ---- X: edge-padded restore equals Phase-12 ----------------------------
def test_X_edge_padded_restore_matches_phase12():
    p12 = _phase12()
    prob = _prob512()
    for case in ("top_edge", "bottom_edge", "left_edge", "right_edge"):
        ref = p12.restore_float(prob, _p12_geom(case), NATIVE)
        mine = restore_probability_to_full_native(prob, _p1d(case), NATIVE)
        assert np.max(np.abs(ref - mine)) <= 1e-7, case


# ---- Y: corner-padded restore equals Phase-12 --------------------------
def test_Y_corner_padded_restore_matches_phase12():
    p12 = _phase12()
    prob = _prob512()
    for case in ("top_left_corner", "bottom_right_corner"):
        ref = p12.restore_float(prob, _p12_geom(case), NATIVE)
        mine = restore_probability_to_full_native(prob, _p1d(case), NATIVE)
        assert np.max(np.abs(ref - mine)) <= 1e-7, case


# ---- Z: padded square dims equal crop_side -----------------------------
def test_Z_padded_square_dims_equal_crop_side():
    for case in CASES:
        g = _p1d(case)
        side = g["crop_side"]
        h = g["clip_y2"] - g["clip_y1"] + g["pad_top"] + g["pad_bottom"]
        w = g["clip_x2"] - g["clip_x1"] + g["pad_left"] + g["pad_right"]
        assert (h, w) == (side, side), case


# ---- AA: valid restored extent equals clipped native extent ------------
def test_AA_valid_extent_equals_clipped_extent():
    prob = _prob512()
    for case in CASES:
        g = _p1d(case)
        valid, (y1, x1, y2, x2) = restore_probability_to_native(prob, g, NATIVE)
        assert valid.shape == (g["clip_y2"] - g["clip_y1"],
                               g["clip_x2"] - g["clip_x1"]), case
        assert (y1, x1, y2, x2) == (g["clip_y1"], g["clip_x1"],
                                    g["clip_y2"], g["clip_x2"]), case


# ---- AB: support excludes out-of-image padding -------------------------
def test_AB_support_excludes_padding():
    for case in CASES:
        g = _p1d(case)
        u = proposal_support_mask([g], NATIVE)
        assert u.shape == NATIVE, case
        # support must be EXACTLY the clipped native rectangle
        expected = np.zeros(NATIVE, dtype=bool)
        expected[g["clip_y1"]:g["clip_y2"], g["clip_x1"]:g["clip_x2"]] = True
        assert np.array_equal(u, expected), case
        valid_h = g["clip_y2"] - g["clip_y1"]
        valid_w = g["clip_x2"] - g["clip_x1"]
        assert u.sum() == valid_h * valid_w, case
        # the zero-padded part of the square contributes NO support pixels:
        # pad area = full square minus valid rectangle
        pad_pixels = (g["pad_top"] + g["pad_bottom"]) * g["crop_side"] \
            + (g["pad_left"] + g["pad_right"]) * valid_h
        assert g["crop_side"] ** 2 - u.sum() == pad_pixels, case
        # padded rows/cols map OUTSIDE the native image, so they can never be
        # support: the exact-rectangle equality above already proves this.
        assert not u[:max(0, -g["y1"]), :].any() or g["clip_y1"] == 0, case
        assert not u[:, :max(0, -g["x1"])].any() or g["clip_x1"] == 0, case


# ---- AC: no direct 512 -> clipped rectangle shortcut remains -----------
def test_AC_no_direct_512_to_clipped_shortcut():
    import inspect

    import scripts.inference.phase13_part1d_predicted_region_inference as m

    src = inspect.getsource(m.restore_probability_to_native)
    assert "crop_side" in src, "restore must resize to the FULL square side"
    assert "pad_top" in src and "pad_left" in src, "restore must strip padding"
    # the clipped extent must NOT be the interpolation target
    assert "size=(target_h" not in src and "target_h, target_w)" not in src


# ---- AD: all 494 real frozen geometries satisfy invariants -------------
def test_AD_all_494_frozen_geometries_valid():
    case = pd.read_csv(TABLES / "phase13_part1c_best_checkpoint_case_proposals.csv")
    total = 0
    padded = 0
    for r in case.itertuples():
        geoms = parse_proposal_geometry({"proposal_crop_geometry": r.proposal_crop_geometry})
        for g in geoms:
            assert_geometry_invariants(g, (int(r.native_H), int(r.native_W)))
            total += 1
            if g["pad_top"] or g["pad_bottom"] or g["pad_left"] or g["pad_right"]:
                padded += 1
    assert total == 494, total
    assert padded == 2, padded
