"""Frozen scientific recipe for the FULL RA-MedFiLM-BARR three-seed pipeline.

Every constant below is INHERITED.  The provenance of each block is stated
explicitly so that no value can drift from the phase that froze it:

G (GlobalMedFiLM)
    ``scripts/training/phase21_common.py::CONFIG`` -- Phase-20 frozen protocol
    ``reports/audits/phase20_shared_global_baseline_protocol.json``
    (SHA-256 ``b74f1f9f...4283c``).

R_psi (Regional Refiner)
    ``scripts/training/train_phase25a_refiner.py`` -- Phase-24 v1.1 ``refiner``
    block, Phase-25A sections 14-21.

Labels (OOF paired gain)
    ``notebooks/phasewise/phase_25c_paired_gain_labels/code/phase25c_common.py``
    -- Phase-24 frozen categories (``BENEFICIAL >= +0.02``, ``HARMFUL <= -0.01``).

B_phi (Benefit Router)
    ``scripts/analysis/train_phase25d_router.py`` -- Phase-25D v1.2.1 contract.

S_omega (Post-Refinement Safety)
    ``scripts/analysis/phase25f_execution_common.py`` -- Phase-25F v1.0 spec.

What this module ADDS
---------------------
Only the *seed-parameterisation* of the above.  The canonical producers are
single-seed (42) or fixed-global; they accept no seed argument.  The values they
hard-code are re-declared here as data so that a per-seed family can be produced
without editing a frozen historical implementation.

Operational overrides (``max_epochs``, device, batch size for synthetic runs) are
kept in a separate object, :class:`OperationalBounds`, so that a reduced run can
never be mistaken for a protocol-faithful one.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Tuple

ROOT = Path(__file__).resolve().parents[3]

# --------------------------------------------------------------------------- #
# populations / splits  (immutable)
# --------------------------------------------------------------------------- #
TRAIN_N = 5832
VAL_N = 808
TEST_N = 1683
ROUTER_DEVELOPMENT_N = 4957
ROUTER_HOLDOUT_N = 875

DATASET_ORDER: Tuple[str, ...] = ("ISIC", "BUSI", "KVASIR", "KUB")
TASK_ID: Dict[str, int] = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}
TASK_ID_TO_NAME: Dict[int, str] = {v: k for k, v in TASK_ID.items()}

MANIFEST_DIR = ROOT / "manifests" / "phase4_v3"
TRAIN_MANIFEST = MANIFEST_DIR / "train.csv"
VAL_MANIFEST = MANIFEST_DIR / "val.csv"
TEST_MANIFEST = MANIFEST_DIR / "test.csv"
ROUTER_SPLIT_MANIFEST = ROOT / "reports" / "audits" / "phase24_router_split_manifest.csv"

# --------------------------------------------------------------------------- #
# thresholds -- TWO DISTINCT ROLES, NEVER CONFLATED
# --------------------------------------------------------------------------- #
ROI_PROPOSAL_THRESHOLD = 0.30          # bbox / action availability only
SEGMENTATION_OUTPUT_THRESHOLD = 0.50   # final binary mask / Dice only
SOMEGA_ACCEPT_THRESHOLD = 0.50         # S_omega accept (sigmoid probability)
ROI_EXPANSION_FACTOR = 1.50            # == 1 + 2 * ROI_FRACTIONAL_MARGIN
ROI_FRACTIONAL_MARGIN = 0.25
REGIONAL_CANVAS_RESOLUTION = 512
REGIONAL_INPUT_RESOLUTION = 256

# --------------------------------------------------------------------------- #
# G -- GlobalMedFiLM
# --------------------------------------------------------------------------- #
G_ARCHITECTURE_ID = "global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1"
G_MODEL = {
    "name": "GlobalMedFiLM",
    "task_count": 4,
    "in_channels": 3,
    "out_channels": 1,
    "channels": (24, 48, 96, 192, 256),
    "task_embedding_dim": 32,
    "film_hidden_dim": 64,
    "film_sites": ("bridge", "decoder4", "decoder3", "decoder2", "decoder1"),
}
G_INPUT_RESOLUTION = 512
G_INPUT_CHANNEL_POLICY = "RGB_3CH"
G_LOSS = {"name": "bce_dice", "bce_weight": 0.5, "dice_weight": 0.5, "dice_epsilon": 1e-6}
G_OPTIMIZER = {"name": "AdamW", "learning_rate": 1e-4, "weight_decay": 1e-4}
G_SCHEDULER = {"name": "CosineAnnealingLR", "T_max": 100}
G_TRAINING = {
    "batch_size": 4,
    "eval_batch_size": 8,
    "num_workers": 4,
    "persistent_workers": False,
    "max_epochs": 100,
    "early_stopping_patience": 15,
    "amp": True,
    "threshold": 0.50,
    "sampling_policy": "phase20_domain_balanced_uniform_v1",
    "checkpoint_metric": "phase20_macro_domain_mean_dice_v1",
    "tie_break": "lower validation loss",
}
G_SELECTION_RULE_ID = "phase20_macro_domain_mean_dice_v1"
G_EXPECTED_PARAMETERS = 3_523_001

# --------------------------------------------------------------------------- #
# crop cache -- G forward over ROUTER_DEVELOPMENT, frozen ROI rule
# --------------------------------------------------------------------------- #
CACHE_FEATURE_TAPS = ("bridge", "decoder2", "decoder1")
CACHE_NATIVE_CHANNELS = {"bridge": 256, "decoder2": 48, "decoder1": 24}

# --------------------------------------------------------------------------- #
# R_psi -- Regional Refiner
# --------------------------------------------------------------------------- #
R_ARCHITECTURE_ID = "barr_regional_refiner_v1_narrowed_channels"
R_CHANNELS = (16, 32, 64, 96, 128)
R_INPUT_CHANNELS = 4          # [R, G, B, p_global_crop]
R_EXPECTED_PARAMETERS = 1_276_401
R_LOSS = {"name": "bce_dice", "bce_weight": 0.5, "dice_weight": 0.5, "dice_epsilon": 1e-6}
R_OPTIMIZER = {"name": "AdamW", "learning_rate": 1e-4, "weight_decay": 1e-4}
R_SCHEDULER = {"name": "CosineAnnealingLR", "T_max": 100}
R_BATCH_SIZE = 8
R_MAX_EPOCHS = 100
R_PATIENCE = 15
R_SELECTION = "minimum EARLY_STOP total loss"
R_OUTER_FOLDS = (0, 1, 2)
R_INNER_FIT_FRACTION = 0.90
R_INNER_EARLY_STOP_FRACTION = 0.10

# --------------------------------------------------------------------------- #
# OOF paired-gain labels (Phase 25C)
# --------------------------------------------------------------------------- #
#: versioned identity of the *label construction* used by the primary pipeline.
#: The primary construction is the one matched to the frozen Phase-25D/25F labels:
#: refiner-OOF, router-OOF, safety-OOF but backbone-IN-SAMPLE.  A different
#: construction (e.g. the optional strict backbone-OOF extension) MUST carry a
#: different version string so the two can never be conflated.
EXPERIMENTAL_PROTOCOL_VERSION = "ra_medfilm_barr_matched_full_oof_v1"

LABEL_BENEFICIAL_DELTA = 0.02
LABEL_HARMFUL_DELTA = -0.01
LABEL_SAFETY_TARGET_RULE = "1 iff OOF refinement gain (delta_dice) > 0"

# --------------------------------------------------------------------------- #
# B_phi -- Benefit Router
# --------------------------------------------------------------------------- #
B_ARCHITECTURE_ID = "barr_benefit_router_v1_218x128x64x1"
B_NUMERIC_DIM = 202
B_TASK_EMBED_DIM = 16
B_TOTAL_DIM = B_NUMERIC_DIM + B_TASK_EMBED_DIM
B_HIDDEN = (128, 64)
B_DROPOUT = 0.10
B_EXPECTED_PARAMETERS = 36_801
B_LOSS = {"name": "HuberLoss", "delta": 0.05, "reduction": "mean"}
B_OPTIMIZER = {"name": "AdamW", "learning_rate": 1e-3, "weight_decay": 1e-4}
B_SCHEDULER = {
    "name": "ReduceLROnPlateau", "mode": "min", "factor": 0.5, "patience": 8,
    "threshold": 1e-4, "threshold_mode": "rel", "cooldown": 0, "min_lr": 1e-6, "eps": 1e-8,
}
B_BATCH_SIZE = 128
B_MAX_EPOCHS = 200
B_PATIENCE = 20
B_CV_FOLDS = 5
B_FOLD_SEED_BASE = 42_000
B_FINAL_SEED = 42
#: the eight scalars that receive FIT-only standardisation (indices into the 202-D vector)
B_NORMALIZE_IDX = (192, 193, 194, 195, 196, 197, 200, 201)
B_FINAL_EPOCH_RULE = "median of the 5 CV best epochs"

# --------------------------------------------------------------------------- #
# S_omega -- Post-Refinement Safety
# --------------------------------------------------------------------------- #
S_ARCHITECTURE_ID = "barr_post_safety_v1_20x32x16x1"
S_FEATURE_DIM = 20
S_NUMERIC_DIM = 16
S_ONEHOT_DIM = 4
S_HIDDEN = (32, 16)
S_EXPECTED_PARAMETERS = 1_217
S_LOSS = {"name": "BCEWithLogitsLoss", "reduction": "mean"}
S_OPTIMIZER = {"name": "AdamW", "learning_rate": 1e-3, "weight_decay": 1e-4}
S_SCHEDULER = dict(B_SCHEDULER)
S_BATCH_SIZE = 128
S_MAX_EPOCHS = 200
S_PATIENCE = 20
S_CV_FOLDS = 5
S_FOLD_SEED_BASE = 54_000
S_FINAL_SEED = 42
S_IMPROVEMENT_EPS = 1e-12

# --------------------------------------------------------------------------- #
# runtime routing constants (assembly, not training)
# --------------------------------------------------------------------------- #
from fractions import Fraction  # noqa: E402

LAMBDA = Fraction(1, 4)
C_ACTION = Fraction(1051648, 10270749)
TAU_C7_FINAL = Fraction(24796109646558761, 20000000000000000000)
TAU_C8_FINAL = TAU_C7_FINAL - LAMBDA * C_ACTION
TAU_C8_FINAL_FLOAT = float(TAU_C8_FINAL)

STATES = ("FORCED_SKIP", "SKIP_GLOBAL", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT")


# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class OperationalBounds:
    """Execution-mechanism bounds.  They NEVER change the scientific protocol.

    Any non-default value is recorded in every produced artifact as
    ``operational_override`` so a reduced run cannot be cited as protocol-faithful.
    """

    g_max_epochs: int = G_TRAINING["max_epochs"]
    g_batch_size: int = G_TRAINING["batch_size"]
    g_eval_batch_size: int = G_TRAINING["eval_batch_size"]
    g_num_workers: int = G_TRAINING["num_workers"]
    g_amp: bool = G_TRAINING["amp"]
    r_max_epochs: int = R_MAX_EPOCHS
    r_batch_size: int = R_BATCH_SIZE
    b_max_epochs: int = B_MAX_EPOCHS
    b_batch_size: int = B_BATCH_SIZE
    s_max_epochs: int = S_MAX_EPOCHS
    s_batch_size: int = S_BATCH_SIZE
    device: str = "cuda"
    amp: bool = True

    def overrides(self) -> dict:
        """Non-default fields, for provenance stamping."""
        d = {}
        if self.g_max_epochs != G_TRAINING["max_epochs"]:
            d["g_max_epochs"] = self.g_max_epochs
        if self.g_batch_size != G_TRAINING["batch_size"]:
            d["g_batch_size"] = self.g_batch_size
        if self.g_eval_batch_size != G_TRAINING["eval_batch_size"]:
            d["g_eval_batch_size"] = self.g_eval_batch_size
        if self.g_num_workers != G_TRAINING["num_workers"]:
            d["g_num_workers"] = self.g_num_workers
        if self.g_amp != G_TRAINING["amp"]:
            d["g_amp"] = self.g_amp
        if self.r_max_epochs != R_MAX_EPOCHS:
            d["r_max_epochs"] = self.r_max_epochs
        if self.r_batch_size != R_BATCH_SIZE:
            d["r_batch_size"] = self.r_batch_size
        if self.b_max_epochs != B_MAX_EPOCHS:
            d["b_max_epochs"] = self.b_max_epochs
        if self.b_batch_size != B_BATCH_SIZE:
            d["b_batch_size"] = self.b_batch_size
        if self.s_max_epochs != S_MAX_EPOCHS:
            d["s_max_epochs"] = self.s_max_epochs
        if self.s_batch_size != S_BATCH_SIZE:
            d["s_batch_size"] = self.s_batch_size
        return d

    @property
    def is_protocol_faithful(self) -> bool:
        return not self.overrides()

    @classmethod
    def synthetic(cls, **kw) -> "OperationalBounds":
        """Tiny, fast bounds for integration testing.  NEVER protocol-faithful."""
        base = dict(g_max_epochs=2, g_batch_size=2, g_eval_batch_size=2, g_num_workers=0,
                    g_amp=False, r_max_epochs=2, r_batch_size=2, b_max_epochs=3,
                    b_batch_size=8, s_max_epochs=3, s_batch_size=8, device="cuda", amp=False)
        base.update(kw)
        return cls(**base)


@dataclass(frozen=True)
class Recipe:
    """All frozen values in one object, for checkpoint stamping."""

    g: dict = field(default_factory=lambda: {
        "architecture_id": G_ARCHITECTURE_ID, "model": G_MODEL,
        "input_resolution": G_INPUT_RESOLUTION, "input_channel_policy": G_INPUT_CHANNEL_POLICY,
        "loss": G_LOSS, "optimizer": G_OPTIMIZER, "scheduler": G_SCHEDULER,
        "training": G_TRAINING, "selection_rule_id": G_SELECTION_RULE_ID,
    })
    r: dict = field(default_factory=lambda: {
        "architecture_id": R_ARCHITECTURE_ID, "channels": list(R_CHANNELS),
        "input_channels": R_INPUT_CHANNELS, "loss": R_LOSS, "optimizer": R_OPTIMIZER,
        "scheduler": R_SCHEDULER, "batch_size": R_BATCH_SIZE, "max_epochs": R_MAX_EPOCHS,
        "patience": R_PATIENCE, "selection": R_SELECTION, "outer_folds": list(R_OUTER_FOLDS),
        "inner_fit_fraction": R_INNER_FIT_FRACTION,
        "inner_early_stop_fraction": R_INNER_EARLY_STOP_FRACTION,
    })
    b: dict = field(default_factory=lambda: {
        "architecture_id": B_ARCHITECTURE_ID, "numeric_dim": B_NUMERIC_DIM,
        "task_embed_dim": B_TASK_EMBED_DIM, "hidden": list(B_HIDDEN), "dropout": B_DROPOUT,
        "loss": B_LOSS, "optimizer": B_OPTIMIZER, "scheduler": B_SCHEDULER,
        "batch_size": B_BATCH_SIZE, "max_epochs": B_MAX_EPOCHS, "patience": B_PATIENCE,
        "cv_folds": B_CV_FOLDS, "fold_seed_base": B_FOLD_SEED_BASE,
        "normalize_idx": list(B_NORMALIZE_IDX), "final_epoch_rule": B_FINAL_EPOCH_RULE,
    })
    s: dict = field(default_factory=lambda: {
        "architecture_id": S_ARCHITECTURE_ID, "feature_dim": S_FEATURE_DIM,
        "numeric_dim": S_NUMERIC_DIM, "onehot_dim": S_ONEHOT_DIM, "hidden": list(S_HIDDEN),
        "loss": S_LOSS, "optimizer": S_OPTIMIZER, "scheduler": S_SCHEDULER,
        "batch_size": S_BATCH_SIZE, "max_epochs": S_MAX_EPOCHS, "patience": S_PATIENCE,
        "cv_folds": S_CV_FOLDS, "fold_seed_base": S_FOLD_SEED_BASE,
        "accept_threshold": SOMEGA_ACCEPT_THRESHOLD,
    })
    thresholds: dict = field(default_factory=lambda: {
        "roi_proposal": ROI_PROPOSAL_THRESHOLD,
        "segmentation_output": SEGMENTATION_OUTPUT_THRESHOLD,
        "somega_accept": SOMEGA_ACCEPT_THRESHOLD,
        "roi_expansion": ROI_EXPANSION_FACTOR,
    })
    populations: dict = field(default_factory=lambda: {
        "TRAIN": TRAIN_N, "VAL": VAL_N, "TEST": TEST_N,
        "ROUTER_DEVELOPMENT": ROUTER_DEVELOPMENT_N, "ROUTER_HOLDOUT": ROUTER_HOLDOUT_N,
    })

    def as_dict(self) -> dict:
        return {"g": self.g, "r": self.r, "b": self.b, "s": self.s,
                "thresholds": self.thresholds, "populations": self.populations}
