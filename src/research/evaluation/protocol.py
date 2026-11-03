"""Frozen evaluation protocol: populations, protected splits, evidence classes.

Every number in this module is read from the repository's own frozen constants or
from the manifest on disk.  Nothing here is a new scientific parameter: the
thresholds, the ROI rule and the population sizes are imported from
:mod:`src.research.full_pipeline.recipe`, which is the single frozen source.

The one thing this module *adds* is enforcement.  A protected split cannot be
opened through this package at all: :func:`assert_split_readable` raises for
``TEST`` and :class:`ProtectedSplitGuard` makes the refusal testable.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from src.research.full_pipeline import recipe as R

ROOT = Path(__file__).resolve().parents[3]

# --------------------------------------------------------------------------- #
# Populations (frozen; never re-derived here)
# --------------------------------------------------------------------------- #
TRAIN_N = R.TRAIN_N          # 5832
VAL_N = R.VAL_N              # 808
TEST_N = R.TEST_N            # 1683
QUARANTINED_N = 118
ALL_PAIRED_N = TRAIN_N + VAL_N + TEST_N + QUARANTINED_N   # 8441
ROUTER_DEVELOPMENT_N = 4957
ROUTER_HOLDOUT_N = 875
RETROSPECTIVE_EXTERNAL_N = 884
assert ROUTER_DEVELOPMENT_N + ROUTER_HOLDOUT_N == TRAIN_N

DATASET_ORDER = R.DATASET_ORDER                      # ISIC, BUSI, KVASIR, KUB
TASK_ID = dict(R.TASK_ID)
DOMAINS = tuple(DATASET_ORDER)

#: Threshold roles.  These are three *different* thresholds and conflating them
#: is the single most common way to misreport this system.
ROI_PROPOSAL_THRESHOLD = R.ROI_PROPOSAL_THRESHOLD            # 0.30 bbox/action only
SEGMENTATION_OUTPUT_THRESHOLD = R.SEGMENTATION_OUTPUT_THRESHOLD  # 0.50 mask/Dice
SOMEGA_ACCEPT_THRESHOLD = R.SOMEGA_ACCEPT_THRESHOLD          # 0.50 safety accept
ROI_EXPANSION_FACTOR = R.ROI_EXPANSION_FACTOR                # 1.50
ROI_FRACTIONAL_MARGIN = R.ROI_FRACTIONAL_MARGIN              # 0.25
RESOLUTION = 512
CHANNEL_POLICY = "RGB_3CH"

# --------------------------------------------------------------------------- #
# Splits
# --------------------------------------------------------------------------- #
SPLIT_TRAIN = "TRAIN"
SPLIT_VAL = "VAL"
SPLIT_TEST = "TEST"
SPLIT_ROUTER_HOLDOUT = "ROUTER_HOLDOUT"
SPLIT_EXTERNAL = "EXTERNAL_RETROSPECTIVE"

#: ``TEST`` is protected.  Phase C must never load its images or its masks.
PROTECTED_SPLITS = frozenset({SPLIT_TEST})

#: How each split may be described.  ``VAL`` was consumed by model selection, so
#: it can never be presented as a fresh independent test.
SPLIT_SEMANTICS: Dict[str, Dict[str, Any]] = {
    SPLIT_TRAIN: {"n": TRAIN_N, "readable": True, "independent": False,
                  "label": "TRAIN5832 — model fitting population"},
    SPLIT_VAL: {"n": VAL_N, "readable": True, "independent": False,
                "label": "VAL808 — development/selection-consumed, NOT independent"},
    SPLIT_TEST: {"n": TEST_N, "readable": False, "independent": False,
                 "label": "TEST1683 — PROTECTED, must not be read in Phase C"},
    SPLIT_ROUTER_HOLDOUT: {"n": ROUTER_HOLDOUT_N, "readable": True, "independent": False,
                           "label": "ROUTER_HOLDOUT875 — prior development exposure"},
    SPLIT_EXTERNAL: {"n": RETROSPECTIVE_EXTERNAL_N, "readable": True, "independent": False,
                     "label": "Retrospective external 884 — not for parameter tuning"},
}

VAL_EVIDENCE_LABEL = "VAL808_DEVELOPMENT_SELECTION_CONSUMED__NOT_INDEPENDENT_CONFIRMATION"

MANIFEST_DIR = ROOT / "manifests" / "phase4_v3"
MANIFEST_FILES = {SPLIT_TRAIN: MANIFEST_DIR / "train.csv",
                  SPLIT_VAL: MANIFEST_DIR / "val.csv",
                  SPLIT_TEST: MANIFEST_DIR / "test.csv"}


class ProtectedSplitError(RuntimeError):
    """Raised when anything tries to open a protected split."""


def assert_split_readable(split: str) -> None:
    if split in PROTECTED_SPLITS:
        raise ProtectedSplitError(
            f"{split} is a protected split ({SPLIT_SEMANTICS[split]['label']}); "
            "Phase C may not read its images or masks")
    if split not in SPLIT_SEMANTICS:
        raise ProtectedSplitError(f"unknown split {split!r}")


@dataclass
class ProtectedSplitGuard:
    """Records every attempted split read so a test can assert zero TEST access."""

    def __post_init__(self) -> None:
        self.reads: Dict[str, int] = {s: 0 for s in SPLIT_SEMANTICS}
        self.refusals: Dict[str, int] = {s: 0 for s in SPLIT_SEMANTICS}

    def open(self, split: str) -> None:
        try:
            assert_split_readable(split)
        except ProtectedSplitError:
            self.refusals[split] += 1
            raise
        self.reads[split] += 1

    def report(self) -> Dict[str, Any]:
        return {"reads": dict(self.reads), "refusals": dict(self.refusals),
                "test_reads": self.reads[SPLIT_TEST],
                "test_refusals": self.refusals[SPLIT_TEST],
                "protected_untouched": self.reads[SPLIT_TEST] == 0}


# --------------------------------------------------------------------------- #
# Evidence classes — the taxonomy that keeps synthetic and real apart
# --------------------------------------------------------------------------- #
REAL_VAL_EVIDENCE = "REAL_VAL808_DEVELOPMENT"
SYNTHETIC_EVIDENCE = "SYNTHETIC_TEST_ONLY"
HISTORICAL_EVIDENCE = "HISTORICAL_PROTOCOL_INCOMPARABLE"
RETROSPECTIVE_EVIDENCE = "RETROSPECTIVE_EXTERNAL"
FUTURE_EVIDENCE = "FUTURE_CONTROLLED"

EVIDENCE_CLASSES = (REAL_VAL_EVIDENCE, SYNTHETIC_EVIDENCE, HISTORICAL_EVIDENCE,
                    RETROSPECTIVE_EVIDENCE, FUTURE_EVIDENCE)

#: A cell may only be published as completed research evidence in this class.
RESEARCH_EVIDENCE_CLASSES = frozenset({REAL_VAL_EVIDENCE})

EVIDENCE_LABEL: Dict[str, str] = {
    REAL_VAL_EVIDENCE: "Real VAL808 evaluation; development/selection-consumed.",
    SYNTHETIC_EVIDENCE: "SYNTHETIC_TEST: a deterministic fixture, not a research result.",
    HISTORICAL_EVIDENCE: "Historical EXT-03 matrix; reduced protocol, protocol-incomparable.",
    RETROSPECTIVE_EVIDENCE: "Retrospective external data; never used for tuning.",
    FUTURE_EVIDENCE: "Future controlled evidence; does not exist yet.",
}


def evidence_label(evidence_class: str) -> str:
    if evidence_class not in EVIDENCE_LABEL:
        raise ValueError(f"unknown evidence class {evidence_class!r}")
    return EVIDENCE_LABEL[evidence_class]


# --------------------------------------------------------------------------- #
# Preprocessing identity
# --------------------------------------------------------------------------- #
PREPROCESSING_ID = "phase4_v3_resizepad_512_rgb_bilinear_mask_nearest_v1"
PREPROCESSING_SPEC: Dict[str, Any] = {
    "resolution": RESOLUTION, "channel_policy": CHANNEL_POLICY,
    "image_resample": "BILINEAR", "mask_resample": "NEAREST",
    "resize": "aspect_ratio_preserving_centre_pad", "scale_range": [0.0, 1.0],
    "identifier": PREPROCESSING_ID,
}


def preprocessing_sha256() -> str:
    payload = repr(sorted(PREPROCESSING_SPEC.items())).encode()
    return hashlib.sha256(payload).hexdigest()


# --------------------------------------------------------------------------- #
# Metric implementation version
# --------------------------------------------------------------------------- #
METRIC_IMPLEMENTATION_VERSION = "phase_c_metric_engine_v1"
METRIC_DEFINITIONS: Dict[str, Dict[str, str]] = {
    "dice": {"formula": "(2*TP + eps) / (2*TP + FP + FN + eps)", "range": "[0, 1]",
             "eps": "1e-7", "empty_rule": "both empty -> 1.0; one empty -> 0.0"},
    "iou": {"formula": "(TP + eps) / (TP + FP + FN + eps)", "range": "[0, 1]",
            "eps": "1e-7", "empty_rule": "both empty -> 1.0; one empty -> 0.0"},
    "precision": {"formula": "(TP + eps) / (TP + FP + eps)", "range": "[0, 1]",
                  "eps": "1e-7", "empty_rule": "empty prediction -> undefined (NaN)"},
    "recall": {"formula": "(TP + eps) / (TP + FN + eps)", "range": "[0, 1]",
               "eps": "1e-7", "empty_rule": "empty ground truth -> undefined (NaN)"},
    "hd95": {"formula": "95th percentile of the pooled symmetric surface distances",
             "unit": "pixel (no physical spacing is recorded in this corpus)",
             "empty_rule": "any empty mask -> undefined (NaN); never 0"},
    "assd": {"formula": "0.5 * (mean d(pred->gt) + mean d(gt->pred))", "unit": "pixel",
             "empty_rule": "any empty mask -> undefined (NaN)"},
    "equal_domain_macro_dice": {
        "formula": "unweighted mean of the four per-domain mean Dice values",
        "note": "equal-domain weighting, NOT pixel-pooled and NOT image-weighted"},
}


def population_audit() -> Dict[str, Any]:
    """Re-read the manifests and confirm the frozen populations still hold."""
    import pandas as pd

    rows: Dict[str, Any] = {}
    for split, path in MANIFEST_FILES.items():
        frame = pd.read_csv(path, usecols=["sample_id", "dataset", "task_id"])
        rows[split] = {"path": str(path.relative_to(ROOT)),
                       "n": int(len(frame)),
                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                       "per_domain": {d: int((frame["dataset"] == d).sum()) for d in DOMAINS},
                       "readable": split not in PROTECTED_SPLITS}
    expected = {SPLIT_TRAIN: TRAIN_N, SPLIT_VAL: VAL_N, SPLIT_TEST: TEST_N}
    problems = [f"{s}: manifest {rows[s]['n']} != frozen {n}"
                for s, n in expected.items() if rows[s]["n"] != n]
    return {"populations": rows, "expected": expected, "problems": problems,
            "consistent": not problems,
            "note": "TEST1683 is audited by row count only; its images and masks are never opened."}


def manifest_sha256(split: str) -> str:
    path = MANIFEST_FILES.get(split)
    if path is None or not path.is_file():
        raise ProtectedSplitError(f"no manifest for split {split!r}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def domain_weights(records: Iterable[Mapping[str, Any]]) -> Dict[str, int]:
    counts = {d: 0 for d in DOMAINS}
    for record in records:
        counts[str(record["domain"])] = counts.get(str(record["domain"]), 0) + 1
    return counts
