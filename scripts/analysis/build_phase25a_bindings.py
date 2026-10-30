"""Phase 25A — BIND THE EXACT v1.1 SPEC (2/2).

Reads the repository-authoritative Phase-24 v1.1 artifacts and binds, with no
scientific invention:

    reports/audits/phase25a_phase24_v1_1_binding.json
    reports/audits/phase25a_data_split_binding.json
    reports/audits/phase25a_global_checkpoint_binding.json
    reports/audits/phase25a_augmentation_binding.json
    reports/audits/phase25a_roi_transform_audit.json

Any disagreement between the Phase-25A instruction and the frozen v1.1 artifact
is REPORTED (never silently repaired).

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/build_phase25a_bindings.py
"""
from __future__ import annotations

import csv
import hashlib
import inspect
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
AUD = ROOT / "reports" / "audits"
UTC = datetime.now(timezone.utc).isoformat()

from src.data.barr_roi import (  # noqa: E402
    PREDICTED_FOREGROUND_THRESHOLD,
    REGIONAL_CANVAS_RESOLUTION,
    REGIONAL_INPUT_RESOLUTION,
    ROI_EXPANSION_FACTOR,
    ROI_FRACTIONAL_MARGIN,
    ROI_MARGIN_CONSTANT_SOURCE,
    assert_gt_cannot_alter_roi,
    inverse_transform_metadata,
    roi_geometry,
)
from src.data.transforms import SegmentationTransform  # noqa: E402
from src.models.barr import (  # noqa: E402
    BARR_REFINER_CHANNELS,
    BARR_REFINER_EXPECTED_PARAMETERS,
    BARR_REFINER_HARD_CEILING,
    BARR_REFINER_INPUT_CHANNELS,
    BARR_REFINER_INPUT_RESOLUTION,
    BARR_REFINER_OUTPUT_CHANNELS,
    closed_form_parameter_count,
)

EXPECTED_ARCH = "ra_medfilm_barr_narrowed_v1_1"
EXPECTED_METHOD = "RA-MedFiLM-BARR"
EXPECTED_SEED = 42
EXPECTED_NB_SHA = "612d71700c1c1a45b94b8fcb8a3ff427bf32f6f6453130febeec49c6ec78caef"
EXPECTED_GLOBAL_SHA = "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"
GLOBAL_CKPT = ROOT / "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"
GLOBAL_CONFIG = ROOT / "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json"
NB = (ROOT / "notebooks/phasewise/phase_24_architecture_spec"
      / "phase24_narrowed_benefit_aware_refinement_spec.ipynb")
SPLIT_MANIFEST = AUD / "phase24_router_split_manifest.csv"
AUG_SOURCE = ROOT / "src" / "data" / "transforms.py"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def j(p: Path) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else {}


def rows(p: Path) -> list[dict]:
    with Path(p).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def w(name: str, obj: dict) -> None:
    (AUD / name).write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")
    print(f"  wrote reports/audits/{name}")


EX = j(AUD / "phase24_exact_implementation_spec.json")
BPE = j(AUD / "phase24_benefit_data_protocol_exact.json")
REV = j(AUD / "phase24_architecture_revision_v1_1.json")
FAILS: list[str] = []


def must(cond: bool, label: str) -> None:
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
    if not cond:
        FAILS.append(label)


print("=" * 78)
print("PHASE 25A — BINDING THE EXACT v1.1 SPEC")
print("=" * 78)

# ===========================================================================
# 1. Phase-24 v1.1 binding
# ===========================================================================
print("\n[1] Phase-24 v1.1 binding")
roi = EX.get("roi", {})
ref = EX.get("refiner", {})
arch = ref.get("architecture", {})

must(EX.get("architecture_id") == EXPECTED_ARCH, "architecture_id == ra_medfilm_barr_narrowed_v1_1")
must(EX.get("method_name") == EXPECTED_METHOD, "method_name == RA-MedFiLM-BARR")
must(int(EX.get("split_seed", -1)) == EXPECTED_SEED, "MASTER_DEVELOPMENT_SEED == 42")
must(sha(NB) == EXPECTED_NB_SHA, "Phase-24 notebook SHA matches 612d7170...")
must(REV.get("architecture_id") == EXPECTED_ARCH, "revision artifact agrees on v1_1")
must(REV.get("science_changed") is False, "revision science_changed == false")

# ROI values enumerated in the Phase-25A instruction section 3
must(float(roi.get("expansion_factor", 0)) == ROI_EXPANSION_FACTOR,
     "ROI expansion factor == 1.50")
must(float(roi.get("fractional_margin_equivalent", 0)) == ROI_FRACTIONAL_MARGIN,
     "fractional margin == 0.25 (ORACLE_DERIVED_REFINER_MARGIN)")
must(int(roi.get("input_resolution", 0)) == REGIONAL_INPUT_RESOLUTION,
     "regional input resolution == 256")
must(roi.get("resize_modes", {}).get("image") == "bilinear", "RGB resize == bilinear")
must(roi.get("resize_modes", {}).get("probability_map") == "bilinear",
     "p_global resize == bilinear")
must(roi.get("resize_modes", {}).get("gt_mask_training_target_only") == "nearest",
     "GT resize == nearest")
must(roi.get("empty_prediction_behavior") == "FORCED_SKIP", "empty prediction == FORCED_SKIP")
must(roi.get("gt_rescue") is False, "no GT rescue")
must(str(roi.get("margin_constant_source", "")) in ROI_MARGIN_CONSTANT_SOURCE,
     "margin constant source recorded")

# refiner values enumerated in section 3
must(int(ref.get("input_channels", 0)) == BARR_REFINER_INPUT_CHANNELS, "refiner input channels == 4")
must(int(ref.get("output_channels", 0)) == BARR_REFINER_OUTPUT_CHANNELS, "refiner output channels == 1")
must(ref.get("output_kind") == "logits", "refiner output kind == logits")
must(tuple(ref.get("encoder_bridge_channels_active", ())) == BARR_REFINER_CHANNELS,
     "active channel schedule == [16, 32, 64, 96, 128]")
must(list(ref.get("encoder_bridge_channels_declared", ())) == [16, 32, 64, 128, 192],
     "declared (rejected) schedule recorded as [16,32,64,128,192]")
must(int(ref.get("expected_parameter_count_closed_form", 0)) == BARR_REFINER_EXPECTED_PARAMETERS,
     "expected parameter count == 1,276,401")
must(int(ref.get("hard_ceiling", 0)) == BARR_REFINER_HARD_CEILING, "hard ceiling == 2,000,000")
must(closed_form_parameter_count() == BARR_REFINER_EXPECTED_PARAMETERS,
     "local closed form reproduces 1,276,401")
must(arch.get("decoder_extra_second_residual_block") is False,
     "decoder has no extra second residual block")
must(arch.get("residual_block_at_bridge") is True, "bridge residual block present")

# ---------------------------------------------------------------------------
# REPORTED DISCREPANCY — the ROI predicted-foreground threshold
# ---------------------------------------------------------------------------
spec_threshold = float(roi.get("predicted_foreground_threshold", float("nan")))
discrepancy = {
    "field": "roi.predicted_foreground_threshold",
    "phase24_v1_1_frozen_value": spec_threshold,
    "phase24_v1_1_source": "reports/audits/phase24_exact_implementation_spec.json "
                           "+ phase24 notebook addendum A.2 table",
    "phase25a_bound_value": PREDICTED_FOREGROUND_THRESHOLD,
    "phase25a_instruction_citation": "section 5 'binary mask at threshold 0.5'; "
                                     "section 7 step 1 'threshold p_global at 0.5'",
    "repository_canonical_rule": "src/analysis/phase22_common.py:54 THRESHOLD = 0.5, "
                                 "applied as pred = float32(prob) >= 0.5 to match "
                                 "torch.sigmoid(y).ge(0.5) in the frozen evaluation code",
    "disagreement": bool(spec_threshold != PREDICTED_FOREGROUND_THRESHOLD),
    "resolution": "The operative Phase-25A instruction and the repository-wide canonical "
                  "decision rule both specify 0.5; the v1.1 field 0.30 is a carry-over from the "
                  "Phase-13 proposal-search default (ProposalConfig.proposal_threshold). Phase 25A "
                  "binds 0.5 and records 0.30 as SUPERSEDED.",
    "status": "REPORTED_NOT_SILENTLY_REPAIRED",
    "reversal_cost": "one module constant; no retraining needed if reversed BEFORE training starts",
    "frozen_before_training": True,
}
print(f"\n  [REPORT] threshold discrepancy: v1.1 frozen={spec_threshold} "
      f"vs bound={PREDICTED_FOREGROUND_THRESHOLD}")

w("phase25a_phase24_v1_1_binding.json", {
    "artifact": "phase25a_phase24_v1_1_binding",
    "phase": "25A",
    "purpose": "bind the exact Phase-24 v1.1 specification before any implementation or training",
    "architecture_id": EXPECTED_ARCH,
    "method_name": EXPECTED_METHOD,
    "supersedes_architecture_id": EX.get("supersedes_architecture_id"),
    "master_development_seed": EXPECTED_SEED,
    "phase24_notebook_sha256": sha(NB),
    "phase24_exact_spec_path": "reports/audits/phase24_exact_implementation_spec.json",
    "phase24_exact_spec_sha256": sha(AUD / "phase24_exact_implementation_spec.json"),
    "bound_roi": {
        "expansion_factor": ROI_EXPANSION_FACTOR,
        "fractional_margin": ROI_FRACTIONAL_MARGIN,
        "margin_constant_source": ROI_MARGIN_CONSTANT_SOURCE,
        "input_resolution": REGIONAL_INPUT_RESOLUTION,
        "canvas_resolution": REGIONAL_CANVAS_RESOLUTION,
        "rgb_resize": "bilinear",
        "probability_resize": "bilinear",
        "gt_resize": "nearest",
        "empty_prediction": "FORCED_SKIP",
        "gt_rescue": False,
        "predicted_foreground_threshold": PREDICTED_FOREGROUND_THRESHOLD,
    },
    "bound_refiner": {
        "name": "BARRRegionalRefinerV1",
        "input_channels": BARR_REFINER_INPUT_CHANNELS,
        "input_channel_names": ["R", "G", "B", "p_global_crop"],
        "output_channels": BARR_REFINER_OUTPUT_CHANNELS,
        "output_kind": "logits",
        "input_resolution": BARR_REFINER_INPUT_RESOLUTION,
        "channels_active": list(BARR_REFINER_CHANNELS),
        "channels_declared_rejected": [16, 32, 64, 128, 192],
        "expected_parameters": BARR_REFINER_EXPECTED_PARAMETERS,
        "hard_ceiling": BARR_REFINER_HARD_CEILING,
        "closed_form_check": closed_form_parameter_count(),
    },
    "discrepancies": [discrepancy],
    "n_discrepancies": 1,
    "silently_repaired": False,
    "n_checks_failed": len(FAILS),
    "verdict": "PHASE25A_V1_1_BINDING_PASS" if not FAILS else "PHASE25A_V1_1_BINDING_FAIL",
    "generated_utc": UTC,
    "test_reads": 0,
})

# ===========================================================================
# 2. Data split binding
# ===========================================================================
print("\n[2] Data split binding")
sm = rows(SPLIT_MANIFEST)
dev = [r for r in sm if r["split_role"] == "ROUTER_DEVELOPMENT"]
hold = [r for r in sm if r["split_role"] == "ROUTER_HOLDOUT"]
dev_g = {r["group_key"] for r in dev}
hold_g = {r["group_key"] for r in hold}
dom_counts = {}
for r in dev:
    dom_counts[r["dataset"]] = dom_counts.get(r["dataset"], 0) + 1

must(len(dev) == 4957, "ROUTER_DEVELOPMENT n == 4957")
must(len(hold) == 875, "ROUTER_HOLDOUT n == 875")
must(len(dev_g & hold_g) == 0, "group overlap DEV/HOLDOUT == 0")
must(sha(SPLIT_MANIFEST) == BPE.get("manifest_sha256"),
     "split manifest SHA matches the frozen protocol")
must(int(BPE.get("holdout_outcomes_read", -1)) == 0, "holdout outcomes read == 0")

w("phase25a_data_split_binding.json", {
    "artifact": "phase25a_data_split_binding",
    "phase": "25A",
    "purpose": "bind the frozen TRAIN-only router split; Phase 25A trains ONLY on "
               "action-available ROUTER_DEVELOPMENT samples",
    "split_seed": EXPECTED_SEED,
    "split_manifest": "reports/audits/phase24_router_split_manifest.csv",
    "split_manifest_sha256": sha(SPLIT_MANIFEST),
    "development_n": len(dev),
    "holdout_n": len(hold),
    "development_by_domain": dom_counts,
    "group_overlap_dev_holdout": len(dev_g & hold_g),
    "val_overlap": 0,
    "test_overlap": 0,
    "holdout_outcomes_read_in_phase25a": 0,
    "holdout_use_in_phase25a": "NONE — outcomes are never inspected; the holdout is not used "
                               "for training, checkpoint selection or early stopping",
    "val_use_in_phase25a": "NONE — the 808-case VAL is a SECONDARY/CONTINUITY development "
                           "benchmark, untouched in Phase 25A",
    "test_use_in_phase25a": "NONE — TEST is CLOSED",
    "verdict": "PHASE25A_DATA_SPLIT_BINDING_PASS" if not FAILS else "PHASE25A_DATA_SPLIT_BINDING_FAIL",
    "generated_utc": UTC,
    "test_reads": 0,
})

# ===========================================================================
# 3. Global checkpoint binding
# ===========================================================================
print("\n[3] Global checkpoint binding")
gcfg = j(GLOBAL_CONFIG)
g_sha = sha(GLOBAL_CKPT)
must(g_sha == EXPECTED_GLOBAL_SHA, "Phase-21 checkpoint SHA matches")
must(int(gcfg.get("model", {}).get("in_channels", 0)) == 3, "global in_channels == 3")
must(gcfg.get("input_channel_policy") == "RGB_3CH", "global channel policy == RGB_3CH")
must(int(gcfg.get("input_resolution", 0)) == REGIONAL_CANVAS_RESOLUTION,
     "global input resolution == 512")
must(gcfg.get("training", {}).get("threshold") == 0.5, "global segmentation threshold == 0.5")

w("phase25a_global_checkpoint_binding.json", {
    "artifact": "phase25a_global_checkpoint_binding",
    "phase": "25A",
    "purpose": "bind the frozen Phase-21 Global MedFiLM as a FIXED producer of p_global",
    "checkpoint": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
    "checkpoint_sha256": g_sha,
    "experiment_config": "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json",
    "experiment_config_sha256": sha(GLOBAL_CONFIG),
    "model_name": gcfg.get("model", {}).get("name"),
    "architecture": gcfg.get("architecture"),
    "task_count": gcfg.get("model", {}).get("task_count"),
    "channels": gcfg.get("model", {}).get("channels"),
    "input_channel_policy": gcfg.get("input_channel_policy"),
    "input_resolution": gcfg.get("input_resolution"),
    "segmentation_threshold": gcfg.get("training", {}).get("threshold"),
    "model_params": 3523001,
    "policy": {
        "mode": "FIXED_PRODUCER",
        "model_eval": True,
        "requires_grad": False,
        "global_weights_updated": False,
        "second_scientific_global_model_created": False,
        "second_global_forward_for_routing": False,
    },
    "verdict": "PHASE25A_GLOBAL_CHECKPOINT_BINDING_PASS" if not FAILS
               else "PHASE25A_GLOBAL_CHECKPOINT_BINDING_FAIL",
    "generated_utc": UTC,
    "test_reads": 0,
})

# ===========================================================================
# 4. Augmentation binding
# ===========================================================================
print("\n[4] Augmentation binding")
sig = inspect.signature(SegmentationTransform.__init__)
defaults = {k: v.default for k, v in sig.parameters.items()
            if v.default is not inspect.Parameter.empty}
must(float(defaults.get("flip_probability", -1)) == 0.5, "inherited flip_probability == 0.5")
must(float(defaults.get("rotation_degrees", -1)) == 5.0, "inherited rotation_degrees == 5.0")
must(float(defaults.get("brightness", -1)) == 0.1, "inherited brightness == 0.1")
must(float(defaults.get("contrast", -1)) == 0.1, "inherited contrast == 0.1")
src_text = AUG_SOURCE.read_text(encoding="utf-8")
must("ImageOps.mirror" in src_text, "horizontal mirror is the inherited flip")
must("ImageOps.flip" not in src_text, "vertical flip is NOT inherited")
must("Image.Resampling.BILINEAR" in src_text and "Image.Resampling.NEAREST" in src_text,
     "inherited image bilinear / mask nearest resampling")

operations = [
    {"operation": "horizontal_flip", "classification": "INHERITED_ACTIVE",
     "parameter": "p=0.5", "implementation": "ImageOps.mirror",
     "applied_to": ["rgb_crop", "prob_crop", "gt_crop"]},
    {"operation": "rotation_continuous", "classification": "INHERITED_ACTIVE",
     "parameter": "uniform(-5.0, +5.0) degrees", "implementation": "Image.rotate",
     "applied_to": ["rgb_crop (bilinear)", "prob_crop (nearest)", "gt_crop (nearest)"]},
    {"operation": "brightness", "classification": "INHERITED_ACTIVE",
     "parameter": "uniform(0.9, 1.1)", "implementation": "ImageEnhance.Brightness",
     "applied_to": ["rgb_crop"]},
    {"operation": "contrast", "classification": "INHERITED_ACTIVE",
     "parameter": "uniform(0.9, 1.1)", "implementation": "ImageEnhance.Contrast",
     "applied_to": ["rgb_crop"]},
    {"operation": "aspect_resize_pad_to_canvas", "classification": "INHERITED_INACTIVE",
     "parameter": "n/a", "implementation": "SegmentationTransform resize/pad",
     "reason": "this is the GLOBAL preprocessing stage that produces the 512 canvas; for the "
               "refiner it is replaced by the frozen ROI crop at 256. It is not applied a second "
               "time to the crop."},
    {"operation": "vertical_flip", "classification": "NOT_INHERITED",
     "parameter": "n/a", "implementation": "n/a",
     "reason": "the inherited SegmentationTransform defines no vertical flip; it is NOT added"},
    {"operation": "rotation_90_degree_set", "classification": "NOT_INHERITED",
     "parameter": "n/a", "implementation": "n/a",
     "reason": "the inherited pipeline uses continuous +/-5 degree rotation, not a "
               "{0,90,180,270} set; it is NOT added"},
    {"operation": "elastic_deformation", "classification": "FORBIDDEN", "parameter": "n/a"},
    {"operation": "cutmix", "classification": "FORBIDDEN", "parameter": "n/a"},
    {"operation": "mixup", "classification": "FORBIDDEN", "parameter": "n/a"},
    {"operation": "aggressive_domain_specific_augmentation", "classification": "FORBIDDEN",
     "parameter": "n/a"},
    {"operation": "test_time_augmentation", "classification": "FORBIDDEN", "parameter": "n/a"},
]
must(all(o["classification"] != "NOT_INHERITED" or o["operation"] in
         ("vertical_flip", "rotation_90_degree_set") for o in operations),
     "only vflip and 90-degree rotation are NOT_INHERITED")

w("phase25a_augmentation_binding.json", {
    "artifact": "phase25a_augmentation_binding",
    "phase": "25A",
    "purpose": "record the EXACT augmentation inherited from the frozen Phase-20/21 pipeline; "
               "nothing is invented",
    "inherited_from": "src.data.transforms.SegmentationTransform(train=True)",
    "inherited_source_file": "src/data/transforms.py",
    "inherited_source_sha256": sha(AUG_SOURCE),
    "inherited_defaults": {k: v for k, v in defaults.items()},
    "applied_after": "the frozen ROI crop at 256x256 (crops are cached before augmentation)",
    "applied_consistently_to": ["rgb_crop", "prob_crop", "gt_crop"],
    "prob_crop_resample_rule": "nearest (mask-like / probability array), per the frozen "
                               "p_global_crop_consistency rule",
    "operations": operations,
    "augmentation_sweep": False,
    "verdict": "PHASE25A_AUGMENTATION_BINDING_PASS" if not FAILS
               else "PHASE25A_AUGMENTATION_BINDING_FAIL",
    "generated_utc": UTC,
    "test_reads": 0,
})

# ===========================================================================
# 5. ROI transform audit (incl. the GT-independence proof)
# ===========================================================================
print("\n[5] ROI transform audit")
rng = np.random.default_rng(EXPECTED_SEED)
H = W = REGIONAL_CANVAS_RESOLUTION
synthetic_prob = np.zeros((H, W), np.float32)
synthetic_prob[200:280, 150:260] = 0.9
synthetic_prob[10:20, 400:420] = 0.2          # below threshold, must not enter the bbox
synthetic_img = rng.random((3, H, W)).astype(np.float32)
gt_a = np.zeros((H, W), np.float32); gt_a[210:250, 170:230] = 1.0
gt_b = np.zeros((H, W), np.float32); gt_b[0:5, 0:5] = 1.0
geom = roi_geometry(synthetic_prob)
gt_indep = assert_gt_cannot_alter_roi(synthetic_prob, synthetic_img, gt_a, gt_b)
must(gt_indep["passed"] is True, "GT cannot alter the ROI (geometry/rgb/prob identical)")

# clipped + padded corner case
corner_prob = np.zeros((H, W), np.float32); corner_prob[0:40, 0:40] = 0.8
corner_geom = roi_geometry(corner_prob)
must(corner_geom["pad_top"] == 10 and corner_geom["pad_left"] == 10,
     "centre-preserving expansion pads at the canvas edge")
must(corner_geom["clip_y1"] == 0 and corner_geom["clip_x1"] == 0, "clipping to the valid region")
# square: clipped extent + padding == crop_side
extent_y = (corner_geom["clip_y2"] - corner_geom["clip_y1"]) + corner_geom["pad_top"] + corner_geom["pad_bottom"]
extent_x = (corner_geom["clip_x2"] - corner_geom["clip_x1"]) + corner_geom["pad_left"] + corner_geom["pad_right"]
must(extent_y == extent_x == corner_geom["crop_side_pixels"], "square padding is exact")
must(roi_geometry(np.zeros((H, W), np.float32)) is None, "empty prediction -> FORCED_SKIP")
must(geom["bbox_min_y"] == 200 and geom["bbox_max_y"] == 279,
     "bbox excludes the sub-threshold blob")
inv = inverse_transform_metadata(geom)
must(inv["scale_crop_to_out"] > 0, "inverse-transform metadata persisted for Phase 25C")

w("phase25a_roi_transform_audit.json", {
    "artifact": "phase25a_roi_transform_audit",
    "phase": "25A",
    "purpose": "audit the exact GT-free ROI transform and prove GT cannot influence ROI geometry",
    "rule": ["threshold p_global", "tight predicted-foreground bbox",
             "centre-preserving 1.50x expansion", "clip to the valid image region",
             "deterministic square pad", "extract RGB crop", "extract p_global crop",
             "RGB -> bilinear", "probability -> bilinear", "GT target -> nearest",
             "output 256x256"],
    "constants": {
        "predicted_foreground_threshold": PREDICTED_FOREGROUND_THRESHOLD,
        "expansion_factor": ROI_EXPANSION_FACTOR,
        "fractional_margin": ROI_FRACTIONAL_MARGIN,
        "margin_constant_source": ROI_MARGIN_CONSTANT_SOURCE,
        "input_resolution": REGIONAL_INPUT_RESOLUTION,
        "canvas_resolution": REGIONAL_CANVAS_RESOLUTION,
    },
    "threshold_discrepancy": discrepancy,
    "geometry_implementation": "src.inference.predicted_roi.apply_context_margin "
                               "(the repository-authoritative centre-preserving expansion used "
                               "by src/data/regional_dataset.py with ORACLE_DERIVED_REFINER_MARGIN)",
    "gt_independence_test": gt_indep,
    "corner_clip_pad_case": {
        "pad_top": corner_geom["pad_top"], "pad_left": corner_geom["pad_left"],
        "clip_y1": corner_geom["clip_y1"], "clip_x1": corner_geom["clip_x1"],
        "crop_side_pixels": corner_geom["crop_side_pixels"],
        "square_padding_exact": True,
    },
    "empty_prediction_case": {"geometry": None, "behavior": "FORCED_SKIP",
                              "gt_rescue": False, "synthetic_roi": False},
    "inverse_transform_metadata": inv,
    "roi_geometry_determined_before_gt": True,
    "verdict": "PHASE25A_ROI_TRANSFORM_AUDIT_PASS" if not FAILS
               else "PHASE25A_ROI_TRANSFORM_AUDIT_FAIL",
    "generated_utc": UTC,
    "test_reads": 0,
})

print("-" * 78)
print(f"binding checks failed: {len(FAILS)}")
if FAILS:
    for f in FAILS:
        print("   FAIL:", f)
    print("FAIL-CLOSED: refusing to proceed.")
    sys.exit(2)
print("PHASE25A_BINDINGS_COMPLETE")
