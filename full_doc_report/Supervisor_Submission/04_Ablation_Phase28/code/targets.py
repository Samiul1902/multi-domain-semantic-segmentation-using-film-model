"""
Canonical binary segmentation target contract (Phase 08 Part 1A).

The single authoritative definition of the foreground target for KUB (and the
other domains) is:

    BACKGROUND : mask == 0
    FOREGROUND : mask > 0

Native KUB masks use a heterogeneous, category-correlated nonzero label
vocabulary: {0,255}, {0,1}, {0,2}, {0,3}, and {0,1,2} all occur. Every nonzero
value is foreground. Code must NEVER test ``mask == 1``.

This module exists so the rule is defined once and reused, rather than
re-implemented inline at each call site.
"""
from __future__ import annotations

import numpy as np

FOREGROUND_RULE = "mask > 0"
BACKGROUND_RULE = "mask == 0"


def binarize_mask(mask, dtype=np.float32):
    """
    Convert a native mask to the canonical binary foreground target.

    Parameters
    ----------
    mask : array-like or PIL.Image
        Native mask whose nonzero values (1, 2, 3, 255, ...) are all foreground.
    dtype : numpy dtype
        Output dtype. Defaults to float32, matching the training pipeline.

    Returns
    -------
    numpy.ndarray
        Array with values in {0, 1}. Foreground is ``(mask > 0)``.

    Notes
    -----
    - A 3-dimensional (H, W, C) mask is reduced to its first channel.
    - No rounding, thresholding, or label remapping is applied beyond ``> 0``.
    """
    array = np.asarray(mask)
    if array.ndim == 3:
        array = array[..., 0]
    return (array > 0).astype(dtype)


def binarize_mask_bool(mask) -> np.ndarray:
    """Same contract as :func:`binarize_mask` but returns a boolean array."""
    array = np.asarray(mask)
    if array.ndim == 3:
        array = array[..., 0]
    return array > 0


def foreground_label_signature(mask) -> str:
    """
    Return the sorted unique-label signature of a native mask, e.g. ``"0|2|255"``.

    Used for auditing the raw label vocabulary; not a target conversion.
    """
    array = np.asarray(mask)
    if array.ndim == 3:
        array = array[..., 0]
    return "|".join(str(int(v)) for v in sorted(set(int(x) for x in np.unique(array))))


def is_binary(array) -> bool:
    """True when every value is exactly 0 or 1."""
    values = np.unique(np.asarray(array))
    return bool(np.all(np.isin(values, [0, 1])))
