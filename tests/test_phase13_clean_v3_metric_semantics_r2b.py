"""PHASE-13 PART-1B R2B — metric-semantics implementation-correction tests.

Sub-cases A–N per supervisor §15. Production-shape: reads the REAL clean-v3
geometry table and the REAL VAL masks. No pixels are fabricated to satisfy a
schema, and no TEST file is opened.
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.inference.clean_v3_components import (  # noqa: E402
    EXPECTED_VAL_CASES,
    EXPECTED_VAL_COMPONENTS,
    EXPECTED_VAL_STRATA,
    assert_component_contract,
    build_clean_v3_val_components,
    reconstruct_components_for_case,
)
from src.inference.clean_v3_metrics import (  # noqa: E402
    aggregate_clean_v3_metrics,
    multi_component_ids,
)
from src.inference.predicted_roi import evaluate_roi_coverage  # noqa: E402

GEOMETRY = ROOT / "reports" / "tables" / "phase12_clean_v3_oracle_geometry.csv"
VAL_TABLE = ROOT / "reports" / "tables" / "kub_val_samples_sized.csv"
HARD_TINY = ROOT / "reports" / "tables" / "phase13_clean_v3_hard_tiny_replication_set.csv"
GLOBAL_EMPTY = ROOT / "reports" / "tables" / "phase13_clean_v3_global_empty_replication_set.csv"


@pytest.fixture(scope="module")
def cohorts():
    hard = pd.read_csv(HARD_TINY)
    empty = pd.read_csv(GLOBAL_EMPTY)
    keys = {(str(s), int(c)) for s, c in zip(hard["sample_id"], hard["native_component_id"])}
    ids = {str(v) for v in empty["sample_id"].tolist()}
    return keys, ids


@pytest.fixture(scope="module")
def built(cohorts):
    keys, ids = cohorts
    geometry = pd.read_csv(GEOMETRY)
    val = pd.read_csv(VAL_TABLE)
    grouped = build_clean_v3_val_components(
        geometry, val, hard_tiny_keys=keys, global_empty_ids=ids
    )
    return grouped, geometry, keys, ids


# ---- A: all 103 VAL masks reconstruct without error -----------------------
def test_A_all_103_val_masks_reconstruct(built):
    grouped, _, _, _ = built
    assert len(grouped) == EXPECTED_VAL_CASES


# ---- B: 152/152 component identity match ----------------------------------
def test_B_identity_join_is_exact(built):
    grouped, geometry, _, _ = built
    recon = {(c["sample_id"], c["component_id"]) for comps in grouped.values() for c in comps}
    declared = {
        (str(s), int(c)) for s, c in zip(geometry["sample_id"], geometry["native_component_id"])
    }
    assert len(recon) == EXPECTED_VAL_COMPONENTS
    assert recon == declared


# ---- C: strata preserved --------------------------------------------------
def test_C_strata_preserved(built):
    grouped, _, _, _ = built
    strata = {}
    for comps in grouped.values():
        for c in comps:
            strata[c["size_stratum"]] = strata.get(c["size_stratum"], 0) + 1
    assert strata == EXPECTED_VAL_STRATA


# ---- D: every component has a full native mask ----------------------------
def test_D_every_component_has_full_native_mask(built):
    grouped, _, _, _ = built
    for comps in grouped.values():
        for c in comps:
            mask = c["mask"]
            assert mask is not None
            assert mask.dtype == np.bool_
            assert mask.shape == (c["native_H"], c["native_W"])
            assert int(mask.sum()) > 0


# ---- E: pixel coverage differs from bbox coverage -------------------------
def test_E_pixel_coverage_differs_from_bbox_coverage():
    # Fabricated non-rectangular (L-shaped) component: a bbox proposal covering
    # the whole bbox yields bbox-coverage 1.0 but pixel-coverage < 1.0.
    side = 40
    mask = np.zeros((side, side), dtype=bool)
    mask[0:4, 0:40] = True     # thin horizontal arm
    mask[0:40, 0:4] = True     # thin vertical arm
    pixels = int(mask.sum())
    assert pixels == 160 + 160 - 16  # the two arms overlap in the 4x4 corner

    component = {
        "component_id": 1,
        "min_y": 0, "min_x": 0, "max_y": 39, "max_x": 39,
        "mask": mask,
    }
    geometry = {"clip_y1": 0, "clip_y2": 40, "clip_x1": 0, "clip_x2": 40}
    proposal = {"rank": 1, "score": 1.0, "crop_geometry": geometry}

    with_mask = evaluate_roi_coverage([proposal], [component])[0]
    without_mask = evaluate_roi_coverage(
        [proposal], [{k: v for k, v in component.items() if k != "mask"}]
    )[0]

    assert with_mask["coverage_fraction"] == pytest.approx(1.0)
    assert without_mask["coverage_fraction"] == pytest.approx(1.0)

    # Now a proposal covering only the top-left corner: pixel coverage uses the
    # TRUE pixel count, so the two definitions must diverge.
    corner = {"clip_y1": 0, "clip_y2": 4, "clip_x1": 0, "clip_x2": 4}
    proposal2 = {"rank": 1, "score": 1.0, "crop_geometry": corner}
    pixel_cov = evaluate_roi_coverage([proposal2], [component])[0]["coverage_fraction"]
    bbox_cov = evaluate_roi_coverage(
        [proposal2], [{k: v for k, v in component.items() if k != "mask"}]
    )[0]["coverage_fraction"]

    assert pixel_cov == pytest.approx(16 / pixels)
    assert bbox_cov == pytest.approx(16 / (40 * 40))
    assert pixel_cov != pytest.approx(bbox_cov)


def _rows(**overrides):
    base = {
        "sample_id": "s1", "component_id": 1, "size_stratum": "TINY",
        "hard_tiny": False, "global_empty_image": False,
        "coverage_fraction": 0.0, "covered90": False,
        "covered50": False, "any_overlap": False,
    }
    base.update(overrides)
    return base


# ---- F: hard-Tiny returns an INTEGER COUNT over denominator 15 ------------
def test_F_hard_tiny_is_integer_count_over_15(built):
    _, _, keys, ids = built
    rows = []
    for i, key in enumerate(sorted(keys)):
        rows.append(_rows(
            sample_id=key[0], component_id=key[1], hard_tiny=True,
            covered90=(i < 3), coverage_fraction=0.95 if i < 3 else 0.0,
        ))
    # one extra non-hard row so totals differ from the hard denominator
    rows.append(_rows(sample_id="zz", component_id=99, covered90=True))
    metrics = aggregate_clean_v3_metrics(rows, [0], [0.0], multi_ids=set())
    assert isinstance(metrics["hard_tiny_recovered90"], int)
    assert metrics["hard_tiny_recovered90"] == 3
    assert metrics["hard_tiny_total"] == 15


# ---- G: hard-Tiny membership is COMPONENT-level, not sample-level ---------
def test_G_hard_tiny_membership_is_component_level(built):
    grouped, _, keys, _ = built
    # A sample with several hard-Tiny components must count EACH component.
    per_sample = {}
    for sid, cid in keys:
        per_sample[sid] = per_sample.get(sid, 0) + 1
    multi = {s: n for s, n in per_sample.items() if n > 1}
    assert multi, "expected at least one sample with >1 hard-Tiny component"

    sid = sorted(multi)[0]
    expected = multi[sid]
    rows = [
        _rows(sample_id=s, component_id=c, hard_tiny=True, covered90=True)
        for s, c in sorted(keys) if s == sid
    ]
    metrics = aggregate_clean_v3_metrics(rows, [0], [0.0], multi_ids=set())
    # sample-level would yield 1; component-level yields the component count
    assert metrics["hard_tiny_recovered90"] == expected
    assert expected > 1


# ---- H: global-empty returns an INTEGER COUNT over denominator 5 ----------
def test_H_global_empty_is_integer_count_over_5(built):
    _, _, _, ids = built
    rows = []
    for i, sid in enumerate(sorted(ids)):
        rows.append(_rows(sample_id=sid, component_id=1, global_empty_image=True,
                          covered90=(i < 2), coverage_fraction=0.95 if i < 2 else 0.0))
    metrics = aggregate_clean_v3_metrics(rows, [0], [0.0], multi_ids=set())
    assert isinstance(metrics["global_empty_images_covered90"], int)
    assert metrics["global_empty_images_covered90"] == 2
    assert metrics["global_empty_total"] == 5


# ---- I: global-empty images ARE evaluated despite having GT components ----
def test_I_global_empty_images_have_gt_components(built):
    grouped, _, _, ids = built
    with_components = [sid for sid in ids if grouped.get(sid)]
    assert len(with_components) == len(ids), (
        "every global-empty image must still carry GT components; the cohort must "
        "never be reduced to a 'no components' branch"
    )


# ---- J: multi-component uses COMPONENT-level mean ------------------------
def test_J_multi_component_is_component_level_mean():
    rows = [
        _rows(sample_id="m1", component_id=1, covered90=True),
        _rows(sample_id="m1", component_id=2, covered90=True),
        _rows(sample_id="m1", component_id=3, covered90=False),
        _rows(sample_id="single", component_id=1, covered90=True),
    ]
    multi = multi_component_ids(rows)
    assert multi == {"m1"}
    metrics = aggregate_clean_v3_metrics(rows, [0], [0.0], multi_ids=multi)
    # component-level mean = 2/3; case-complete would give 0.0
    assert metrics["multi_component_recall90"] == pytest.approx(2 / 3)


# ---- K: empty proposal list yields all zeros -----------------------------
def test_K_empty_proposals_yield_all_zeros():
    side = 8
    mask = np.zeros((side, side), dtype=bool)
    mask[2:4, 2:4] = True
    component = {"component_id": 1, "min_y": 2, "min_x": 2, "max_y": 3, "max_x": 3,
                 "mask": mask, "size_stratum": "TINY", "hard_tiny": True,
                 "global_empty_image": True, "sample_id": "s", "native_H": side,
                 "native_W": side}
    coverage = evaluate_roi_coverage([], [component])[0]
    assert coverage["coverage_fraction"] == 0.0
    rows = [_rows(sample_id="s", component_id=1, size_stratum="TINY",
                  hard_tiny=True, global_empty_image=True,
                  coverage_fraction=float(coverage["coverage_fraction"]),
                  covered90=bool(coverage["covered90"]))]
    metrics = aggregate_clean_v3_metrics(rows, [0], [0.0], multi_ids=set())
    assert metrics["tiny_recall90"] == 0.0
    assert metrics["overall_recall90"] == 0.0
    assert metrics["mean_roi_area_fraction"] == 0.0
    assert metrics["hard_tiny_recovered90"] == 0
    assert metrics["global_empty_images_covered90"] == 0
    assert metrics["multi_component_recall90"] == 0.0
    assert metrics["mean_proposals_per_image"] == 0.0


# ---- L: secondary diagnostics absent from select_epoch signature ----------
def test_L_secondary_diagnostics_absent_from_selection():
    from src.training import clean_v3_selection as sel

    source = inspect.getsource(sel.select_epoch)
    for term in ("hard_tiny_recovered90", "global_empty_images_covered90",
                 "multi_component_recall90", "mean_proposals_per_image"):
        assert term not in source, f"{term} must not appear in select_epoch"
    assert list(sel.SELECTION_TERM_NAMES) == [
        "tiny_recall90", "overall_recall90",
        "negative_mean_roi_area_fraction", "negative_val_loss",
    ]


# ---- M: exactly one fixed proposal configuration -------------------------
def test_M_single_fixed_proposal_configuration():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "runner", ROOT / "scripts" / "training" / "train_phase13_clean_v3_localizer.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.PROPOSAL_CONFIGURATION_COUNT == 1
    assert (module.PROPOSAL_THRESHOLD, module.PROPOSAL_MARGIN,
            module.PROPOSAL_TOP_K, module.PROPOSAL_NMS_IOU) == (0.10, 0.20, 5, 0.30)


# ---- N: the 20-config grid remains disabled ------------------------------
def test_N_grid_search_remains_disabled():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "runner2", ROOT / "scripts" / "training" / "train_phase13_clean_v3_localizer.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.GRID_SEARCH_ENABLED is False


# ---- contract guard ------------------------------------------------------
def test_contract_assertion_holds(built):
    _, _, keys, ids = built
    grouped, _, _, _ = built
    contract = assert_component_contract(grouped, hard_tiny_keys=keys, global_empty_ids=ids)
    assert contract["components"] == EXPECTED_VAL_COMPONENTS
    assert contract["unique_identities"] == EXPECTED_VAL_COMPONENTS
    assert contract["hard_tiny_components"] == 15
    assert contract["global_empty_images"] == 5
