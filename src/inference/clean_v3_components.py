"""PHASE-13 PART-1B R2B — clean-v3 native GT component reconstruction.

Corrects defect MISSING_NATIVE_COMPONENT_MASK_IN_PRODUCTION_EVALUATOR.

The pre-R2B clean-v3 evaluator passed component records carrying only a bbox.
``evaluate_roi_coverage`` falls back to BBOX-INTERSECTION coverage when
``component["mask"]`` is absent, which silently contradicts the frozen
definition (native PIXEL coverage).

This module reconstructs, per VAL case, the native-space 8-connected components
from the real VAL mask and attaches the FULL native boolean mask. It fails loudly
rather than degrading.

Frozen contract (supervisor §5 / §6 / §14):
  foreground   = mask > 0
  connectivity = 8
  space        = native image space
  103 cases / 152 components / strata 72-28-36-16

No training. No model. No CUDA. No TEST.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from PIL import Image
from scipy.ndimage import label

NATIVE_STRUCTURE = np.ones((3, 3), dtype=int)

EXPECTED_VAL_CASES = 103
EXPECTED_VAL_COMPONENTS = 152
EXPECTED_VAL_STRATA = {"TINY": 72, "SMALL": 28, "MEDIUM": 36, "LARGE": 16}
EXPECTED_HARD_TINY = 15
EXPECTED_GLOBAL_EMPTY = 5

REQUIRED_COMPONENT_KEYS = (
    "sample_id",
    "component_id",
    "min_y",
    "max_y",
    "min_x",
    "max_x",
    "mask",
    "native_H",
    "native_W",
    "size_stratum",
    "hard_tiny",
    "global_empty_image",
)


def load_native_mask(mask_path) -> np.ndarray:
    """Load a native-space boolean foreground mask (``mask > 0``)."""
    with Image.open(mask_path) as handle:
        array = np.asarray(handle.convert("L"))
    return array > 0


def reconstruct_components_for_case(
    mask_path,
    geometry_rows: pd.DataFrame,
    sample_id: str,
    *,
    hard_tiny_keys=frozenset(),
    global_empty_ids=frozenset(),
):
    """Reconstruct native 8-connected components for one VAL case.

    Joins one-to-one to ``geometry_rows`` (the frozen Phase-12 geometry table)
    on ``native_component_id`` and verifies the native bbox correspondence.

    Returns a list of component dicts, each carrying the FULL native mask.
    Fails loudly on any mismatch.
    """
    mask = load_native_mask(mask_path)
    if mask.ndim != 2:
        raise ValueError(f"{sample_id}: native mask is not 2-D (shape={mask.shape})")
    if int(mask.sum()) == 0:
        raise ValueError(f"{sample_id}: native mask is empty; refusing")

    labelled, found = label(mask, structure=NATIVE_STRUCTURE)
    if found == 0:
        raise ValueError(f"{sample_id}: 8-connectivity labelling found 0 components")

    geometry_rows = geometry_rows.sort_values("native_component_id")
    expected_ids = [int(v) for v in geometry_rows["native_component_id"].tolist()]

    if found != len(expected_ids):
        raise ValueError(
            f"{sample_id}: component count mismatch — reconstructed {found} but "
            f"geometry table declares {len(expected_ids)}"
        )
    if sorted(expected_ids) != list(range(1, found + 1)):
        raise ValueError(
            f"{sample_id}: geometry native_component_id are not 1..{found}: {expected_ids}"
        )

    native_h = int(geometry_rows["native_H"].iloc[0])
    native_w = int(geometry_rows["native_W"].iloc[0])
    if mask.shape != (native_h, native_w):
        raise ValueError(
            f"{sample_id}: mask shape {mask.shape} != native (H,W)=({native_h},{native_w})"
        )

    components = []
    for row in geometry_rows.itertuples(index=False):
        cid = int(row.native_component_id)
        component_mask = labelled == cid
        pixel_count = int(component_mask.sum())
        if pixel_count == 0:
            raise ValueError(f"{sample_id}: reconstructed component {cid} is empty")

        ys, xs = np.where(component_mask)
        recon_bbox = (int(ys.min()), int(xs.min()), int(ys.max()), int(xs.max()))
        declared_bbox = (
            int(row.bbox_min_y),
            int(row.bbox_min_x),
            int(row.bbox_max_y),
            int(row.bbox_max_x),
        )
        if recon_bbox != declared_bbox:
            raise ValueError(
                f"{sample_id}: component {cid} bbox mismatch — reconstructed "
                f"{recon_bbox} vs geometry {declared_bbox}"
            )

        declared_pixels = int(row.native_component_pixels)
        if pixel_count != declared_pixels:
            raise ValueError(
                f"{sample_id}: component {cid} pixel mismatch — reconstructed "
                f"{pixel_count} vs geometry {declared_pixels}"
            )

        components.append(
            {
                "sample_id": str(sample_id),
                "component_id": cid,
                "min_y": recon_bbox[0],
                "min_x": recon_bbox[1],
                "max_y": recon_bbox[2],
                "max_x": recon_bbox[3],
                "mask": component_mask,
                "native_H": native_h,
                "native_W": native_w,
                "size_stratum": str(row.size_stratum),
                "hard_tiny": (str(sample_id), cid) in hard_tiny_keys,
                "global_empty_image": str(sample_id) in global_empty_ids,
            }
        )
    return components


def build_clean_v3_val_components(
    geometry_frame: pd.DataFrame,
    val_frame: pd.DataFrame,
    hard_tiny_keys=frozenset(),
    global_empty_ids=frozenset(),
):
    """Build ``{sample_id: [components]}`` for all 103 clean-v3 FULL_FIELD VAL cases."""
    path_by_sample = {
        str(sid): str(mp)
        for sid, mp in zip(val_frame["sample_id"], val_frame["mask_path"])
    }
    grouped = {}
    for sample_id in sorted({str(v) for v in geometry_frame["sample_id"].tolist()}):
        mask_path = path_by_sample.get(sample_id)
        if mask_path is None:
            raise ValueError(
                f"VAL sample table has no mask_path for geometry sample {sample_id}"
            )
        grouped[sample_id] = reconstruct_components_for_case(
            mask_path,
            geometry_frame[geometry_frame["sample_id"].astype(str) == sample_id],
            sample_id,
            hard_tiny_keys=hard_tiny_keys,
            global_empty_ids=global_empty_ids,
        )
    return grouped


def assert_component_contract(
    grouped: dict,
    hard_tiny_keys=frozenset(),
    global_empty_ids=frozenset(),
) -> dict:
    """Fail-loud contract before any coverage evaluation (supervisor §14)."""
    cases = len(grouped)
    flat = [c for comps in grouped.values() for c in comps]
    identities = [(c["sample_id"], c["component_id"]) for c in flat]

    if cases != EXPECTED_VAL_CASES:
        raise AssertionError(f"VAL case count {cases} != {EXPECTED_VAL_CASES}")
    if len(flat) != EXPECTED_VAL_COMPONENTS:
        raise AssertionError(f"VAL component count {len(flat)} != {EXPECTED_VAL_COMPONENTS}")
    if len(set(identities)) != EXPECTED_VAL_COMPONENTS:
        raise AssertionError("VAL component identities are not unique (152 required)")

    strata = {}
    for c in flat:
        strata[c["size_stratum"]] = strata.get(c["size_stratum"], 0) + 1
    if strata != EXPECTED_VAL_STRATA:
        raise AssertionError(f"VAL strata {strata} != {EXPECTED_VAL_STRATA}")

    hard_found = sum(1 for c in flat if c["hard_tiny"])
    if hard_found != EXPECTED_HARD_TINY:
        raise AssertionError(f"hard-Tiny components {hard_found} != {EXPECTED_HARD_TINY}")

    empty_found = len({c["sample_id"] for c in flat if c["global_empty_image"]})
    if empty_found != EXPECTED_GLOBAL_EMPTY:
        raise AssertionError(f"global-empty images {empty_found} != {EXPECTED_GLOBAL_EMPTY}")

    for c in flat:
        mask = c.get("mask")
        if mask is None:
            raise AssertionError(f"{c['sample_id']}/{c['component_id']}: mask missing")
        if getattr(mask, "dtype", None) != np.bool_:
            raise AssertionError(
                f"{c['sample_id']}/{c['component_id']}: mask dtype {mask.dtype} not bool"
            )
        if mask.shape != (c["native_H"], c["native_W"]):
            raise AssertionError(
                f"{c['sample_id']}/{c['component_id']}: mask shape {mask.shape} "
                f"!= native ({c['native_H']},{c['native_W']})"
            )
        if int(mask.sum()) == 0:
            raise AssertionError(f"{c['sample_id']}/{c['component_id']}: mask empty")
        for key in REQUIRED_COMPONENT_KEYS:
            if key not in c:
                raise AssertionError(
                    f"{c['sample_id']}/{c['component_id']}: missing key '{key}'"
                )

    return {
        "cases": cases,
        "components": len(flat),
        "unique_identities": len(set(identities)),
        "strata": strata,
        "hard_tiny_components": hard_found,
        "global_empty_images": empty_found,
    }
