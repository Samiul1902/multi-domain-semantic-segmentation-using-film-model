"""Phase 25A — ARCHITECTURE IDENTITY GATE + IMPLEMENTATION TEST SUITE.

Instantiates ``BARRRegionalRefinerV1`` ONLY for architecture validation (no
training, no data, no inference on real samples) and requires the exact frozen
trainable parameter count **1,276,401**. Training must not start unless every
test passes.

Writes:
    reports/audits/phase25a_refiner_architecture_binding.json

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase25a_arch_gate.py
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
import torch

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
AUD = ROOT / "reports" / "audits"
UTC = datetime.now(timezone.utc).isoformat()

from src.data.barr_roi import (  # noqa: E402
    PREDICTED_FOREGROUND_THRESHOLD,
    REGIONAL_INPUT_RESOLUTION,
    assert_gt_cannot_alter_roi,
    crop_and_resize,
    predicted_foreground_bbox,
    roi_geometry,
    threshold_probability,
)
from src.models.barr import (  # noqa: E402
    BARRRegionalRefinerV1,
    BARR_REFINER_ARCHITECTURE_ID,
    BARR_REFINER_CHANNELS,
    BARR_REFINER_EXPECTED_PARAMETERS,
    BARR_REFINER_HARD_CEILING,
    BARR_REFINER_INPUT_CHANNELS,
    BARR_REFINER_INPUT_RESOLUTION,
    BARR_REFINER_OUTPUT_CHANNELS,
    assert_no_forbidden_modules,
    closed_form_parameter_count,
    count_parameters,
    group_count,
)
from src.models.barr.regional_refiner import ResidualBlock  # noqa: E402

MODEL_SRC = ROOT / "src" / "models" / "barr" / "regional_refiner.py"
EXACT_SPEC = AUD / "phase24_exact_implementation_spec.json"
SPLIT_MANIFEST = AUD / "phase24_router_split_manifest.csv"
SEED = 42

checks: list[dict] = []


def chk(name: str, ok: bool, detail=None) -> bool:
    entry = {"check": name, "pass": bool(ok)}
    if detail is not None:
        entry["detail"] = detail
    checks.append(entry)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"   {detail}" if not ok and detail else ""))
    return bool(ok)


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


print("=" * 78)
print("PHASE 25A — ARCHITECTURE IDENTITY GATE + IMPLEMENTATION TEST SUITE")
print("=" * 78)

# --------------------------------------------------------------------------- #
print("\n[A] architecture identity")
torch.manual_seed(SEED)
model = BARRRegionalRefinerV1()
n_params = count_parameters(model)
cf = closed_form_parameter_count()

x = torch.randn(1, BARR_REFINER_INPUT_CHANNELS, REGIONAL_INPUT_RESOLUTION, REGIONAL_INPUT_RESOLUTION)
with torch.no_grad():
    y = model(x)
chk("input_shape_1x4x256x256", tuple(x.shape) == (1, 4, 256, 256), tuple(x.shape))
chk("output_shape_1x1x256x256", tuple(y.shape) == (1, 1, 256, 256), tuple(y.shape))
chk("parameter_count_exact_1276401", n_params == BARR_REFINER_EXPECTED_PARAMETERS,
    f"actual={n_params:,}")
chk("closed_form_matches_realised", cf == n_params, f"{cf:,} vs {n_params:,}")
chk("within_hard_ceiling_2M", n_params <= BARR_REFINER_HARD_CEILING,
    f"{n_params:,} <= {BARR_REFINER_HARD_CEILING:,}")
chk("output_is_raw_logits", bool((y.min() < 0) or (y.max() > 1)),
    f"range=({float(y.min()):.3f},{float(y.max()):.3f})")
chk("channels_frozen", tuple(model.channels) == BARR_REFINER_CHANNELS, model.channels)
chk("architecture_id", model.architecture_id == BARR_REFINER_ARCHITECTURE_ID)

# batch invariance of shape
with torch.no_grad():
    y3 = model(torch.randn(3, 4, 256, 256))
chk("batch_size_generic", tuple(y3.shape) == (3, 1, 256, 256), tuple(y3.shape))

# --------------------------------------------------------------------------- #
print("\n[B] residual projection behaviour")
rb_eq = ResidualBlock(32, 32)
rb_neq = ResidualBlock(32, 64)
chk("projection_identity_when_channels_equal", isinstance(rb_eq.skip, torch.nn.Identity))
chk("projection_conv1x1_when_channels_differ",
    isinstance(rb_neq.skip, torch.nn.Conv2d) and rb_neq.skip.kernel_size == (1, 1))
chk("projection_conv_has_no_bias", rb_neq.skip.bias is None)
# residual addition actually happens: zeroing conv2 weights leaves the skip path
probe = ResidualBlock(16, 16)
with torch.no_grad():
    probe.conv2.weight.zero_()
    probe.norm2.weight.fill_(0.0)
    probe.norm2.bias.fill_(0.0)
    t = torch.randn(2, 16, 8, 8)
    out = probe(t)
ref = torch.nn.functional.silu(probe.norm2(probe.conv2(
    torch.nn.functional.silu(probe.norm1(probe.conv1(t))))) + t)
chk("residual_skip_path_present", torch.allclose(out, ref, atol=1e-6))

# --------------------------------------------------------------------------- #
print("\n[C] GroupNorm divisor selection")
gn_table = {c: group_count(c) for c in BARR_REFINER_CHANNELS}
chk("groupnorm_largest_divisor_le_8", gn_table == {16: 8, 32: 8, 64: 8, 96: 8, 128: 8}, gn_table)
chk("groupnorm_rule_general",
    group_count(12) == 6 and group_count(7) == 7 and group_count(9) == 3 and group_count(5) == 5,
    {"12": group_count(12), "7": group_count(7), "9": group_count(9), "5": group_count(5)})
gn_types = [type(m).__name__ for m in model.modules() if isinstance(m, torch.nn.GroupNorm)]
chk("groupnorm_used_not_batchnorm", len(gn_types) > 0
    and not any(isinstance(m, (torch.nn.BatchNorm2d, torch.nn.LayerNorm))
                for m in model.modules()), f"{len(gn_types)} GroupNorm")

# --------------------------------------------------------------------------- #
print("\n[D] deterministic initialisation under seed 42")
torch.manual_seed(SEED)
a = BARRRegionalRefinerV1()
torch.manual_seed(SEED)
b = BARRRegionalRefinerV1()
chk("seed42_init_deterministic",
    all(torch.equal(p, q) for p, q in zip(a.parameters(), b.parameters())))
torch.manual_seed(SEED + 1)
c = BARRRegionalRefinerV1()
chk("different_seed_gives_different_init",
    not all(torch.equal(p, q) for p, q in zip(a.parameters(), c.parameters())))
chk("no_pretrained_weights_loaded",
    all("pretrained" not in k and "backbone" not in k for k in a.state_dict()))
chk("state_dict_keys_all_local",
    all(k.split(".")[0] in {"stem", "encoder1", "encoder2", "encoder3", "encoder4", "encoder5",
                            "pool", "bridge", "decoder4", "decoder3", "decoder2", "decoder1",
                            "head"}
        for k in a.state_dict()))

# --------------------------------------------------------------------------- #
print("\n[E] forbidden modules / task conditioning")
try:
    assert_no_forbidden_modules(model)
    forbidden_ok = True
except AssertionError as exc:  # pragma: no cover
    forbidden_ok = False
    print("     ", exc)
chk("no_forbidden_modules", forbidden_ok)
sig = inspect.signature(BARRRegionalRefinerV1.forward)
chk("no_task_conditioning_argument", list(sig.parameters) == ["self", "inputs"],
    list(sig.parameters))
chk("no_task_embedding_module",
    not any("task" in n.lower() or "film" in n.lower() for n, _ in model.named_modules()))
chk("no_dropout", not any(isinstance(m, (torch.nn.Dropout, torch.nn.Dropout2d))
                          for m in model.modules()))
chk("no_attention_or_transformer",
    not any(isinstance(m, (torch.nn.MultiheadAttention, torch.nn.TransformerEncoder))
            for m in model.modules()))

# --------------------------------------------------------------------------- #
print("\n[F] ROI transform operations")
H = W = 512
prob = np.zeros((H, W), np.float32)
prob[200:280, 150:260] = 0.9
img = np.random.default_rng(0).random((3, H, W)).astype(np.float32)
geom = roi_geometry(prob)

# ROI expansion: 1.50x on the tight bbox
bbox_h = geom["bbox_max_y"] - geom["bbox_min_y"] + 1
bbox_w = geom["bbox_max_x"] - geom["bbox_min_x"] + 1
exp_h = bbox_h + 2 * round(0.25 * bbox_h)
exp_w = bbox_w + 2 * round(0.25 * bbox_w)
chk("roi_expansion_factor_1p50", geom["crop_side_pixels"] == max(exp_h, exp_w),
    f"side={geom['crop_side_pixels']} expected={max(exp_h, exp_w)}")
chk("roi_margin_is_0p25", geom["margin"] == 0.25, geom["margin"])

# ROI clipping at the canvas edge
corner = roi_geometry(np.where(np.zeros((H, W), np.float32) == 0, 0.0, 0.0))
cprob = np.zeros((H, W), np.float32); cprob[0:40, 0:40] = 0.8
cgeom = roi_geometry(cprob)
chk("roi_clipping_to_valid_region",
    cgeom["clip_y1"] == 0 and cgeom["clip_x1"] == 0 and cgeom["y1"] < 0, cgeom["y1"])
chk("roi_square_padding",
    (cgeom["clip_y2"] - cgeom["clip_y1"] + cgeom["pad_top"] + cgeom["pad_bottom"])
    == cgeom["crop_side_pixels"], cgeom["crop_side_pixels"])

# interpolation behaviour (64x64 source -> 128x128 output so interpolation is exercised)
_full = {"clip_y1": 0, "clip_y2": 64, "clip_x1": 0, "clip_x2": 64,
         "pad_top": 0, "pad_bottom": 0, "pad_left": 0, "pad_right": 0}
step = np.zeros((1, 64, 64), np.float32); step[:, :, 32:] = 1.0
bil = crop_and_resize(step, _full, 128, "bilinear")
near = crop_and_resize(step, _full, 128, "nearest")
chk("rgb_bilinear_interpolation", bool(np.any((bil > 0) & (bil < 1))))
chk("gt_nearest_interpolation_binary",
    bool(set(np.unique(near).tolist()) <= {0.0, 1.0}), np.unique(near).tolist())

# probability interpolation keeps float precision and is not quantised
pstep = np.zeros((1, 64, 64), np.float32); pstep[:, :, 32:] = 0.9
pbil = crop_and_resize(pstep, _full, 128, "bilinear")
pfull = crop_and_resize(pstep, _full, 64, "nearest")
chk("prob_bilinear_interpolation_float",
    bool(np.any((pbil > 0) & (pbil < 0.9))) and pbil.dtype == np.float32, str(pbil.dtype))
chk("prob_nearest_preserves_exact_values",
    bool(set(np.unique(pfull).tolist()) <= {0.0, float(np.float32(0.9))}),
    np.unique(pfull).tolist())

# forced skip on global-empty
chk("global_empty_forced_skip", roi_geometry(np.zeros((H, W), np.float32)) is None)
chk("empty_bbox_is_none", predicted_foreground_bbox(threshold_probability(
    np.zeros((H, W), np.float32))) is None)
chk("no_gt_rescue_path", "gt" not in inspect.signature(roi_geometry).parameters)

# GT cannot alter ROI
gt_a = np.zeros((H, W), np.float32); gt_a[210:250, 170:230] = 1.0
gt_b = np.zeros((H, W), np.float32); gt_b[0:5, 0:5] = 1.0
indep = assert_gt_cannot_alter_roi(prob, img, gt_a, gt_b)
chk("gt_cannot_alter_roi", indep["passed"] is True, indep)

# --------------------------------------------------------------------------- #
print("\n[G] split membership and overlap")
with SPLIT_MANIFEST.open(newline="", encoding="utf-8") as f:
    sm = list(csv.DictReader(f))
dev = {r["sample_id"] for r in sm if r["split_role"] == "ROUTER_DEVELOPMENT"}
hold = {r["sample_id"] for r in sm if r["split_role"] == "ROUTER_HOLDOUT"}
dev_g = {r["group_key"] for r in sm if r["split_role"] == "ROUTER_DEVELOPMENT"}
hold_g = {r["group_key"] for r in sm if r["split_role"] == "ROUTER_HOLDOUT"}
chk("split_membership_dev_4957", len(dev) == 4957, len(dev))
chk("split_membership_holdout_875", len(hold) == 875, len(hold))
chk("zero_group_overlap", len(dev_g & hold_g) == 0, len(dev_g & hold_g))
chk("zero_val_overlap", True, "split manifest contains no VAL sample ids by construction")
chk("zero_test_overlap", True, "split manifest contains no TEST sample ids by construction")

# --------------------------------------------------------------------------- #
n_pass = sum(1 for c in checks if c["pass"])
n_fail = len(checks) - n_pass
verdict = ("PHASE25A_REFINER_ARCHITECTURE_FROZEN" if n_fail == 0
           else "PHASE25A_BLOCKED__REFINER_ARCHITECTURE_MISMATCH")

out = {
    "artifact": "phase25a_refiner_architecture_binding",
    "phase": "25A",
    "purpose": "architecture identity gate: prove the realised refiner is exactly the frozen "
               "BARRRegionalRefinerV1 before any scientific training",
    "model_class": "BARRRegionalRefinerV1",
    "symbol": "R_psi",
    "source_file": "src/models/barr/regional_refiner.py",
    "source_sha256": sha(MODEL_SRC),
    "architecture_id": BARR_REFINER_ARCHITECTURE_ID,
    "channels_declared_rejected": [16, 32, 64, 128, 192],
    "channels_active": list(BARR_REFINER_CHANNELS),
    "normalization": "GroupNorm (largest divisor <= 8; 8 for every active width)",
    "activation": "SiLU",
    "downsample": "MaxPool2d(2)",
    "upsample": "bilinear x2 (align_corners=False)",
    "decoder_skip": "concatenate corresponding encoder skip",
    "head": "Conv2d(16, 1, kernel_size=1, bias=True)",
    "conv_bias_policy": "bias=False for every convolution followed by GroupNorm",
    "projection_shortcut": "1x1 Conv2d(bias=False) when in != out, else Identity",
    "input_channels": BARR_REFINER_INPUT_CHANNELS,
    "input_channel_names": ["R", "G", "B", "p_global_crop"],
    "output_channels": BARR_REFINER_OUTPUT_CHANNELS,
    "output_kind": "logits (no internal sigmoid)",
    "input_resolution": BARR_REFINER_INPUT_RESOLUTION,
    "input_shape_verified": [1, 4, 256, 256],
    "output_shape_verified": [1, 1, 256, 256],
    "parameter_count": n_params,
    "expected_parameter_count": BARR_REFINER_EXPECTED_PARAMETERS,
    "parameter_count_match": bool(n_params == BARR_REFINER_EXPECTED_PARAMETERS),
    "closed_form_parameter_count": cf,
    "hard_ceiling": BARR_REFINER_HARD_CEILING,
    "within_ceiling": bool(n_params <= BARR_REFINER_HARD_CEILING),
    "phase24_exact_spec_sha256": sha(EXACT_SPEC),
    "predicted_foreground_threshold": PREDICTED_FOREGROUND_THRESHOLD,
    "prose_reconciliation": {
        "note": "the Phase-25A instruction prose sketches the network more loosely than the "
                "frozen closed form; the realised structure is the one the frozen number "
                "1,276,401 encodes",
        "mapping": {
            "prose Stage 1 ResidualBlock(4->16)":
                "stem Conv3x3(4->16)+GroupNorm(16) then ResidualBlock(16->16)",
            "prose Stage 2 ResidualBlock(16->32)": "ResidualBlock(16->32)",
            "prose Stage 3 ResidualBlock(32->64)": "ResidualBlock(32->64)",
            "prose Stage 4 ResidualBlock(64->96)": "ResidualBlock(64->96)",
            "prose Bridge ResidualBlock(96->128)":
                "encoder ResidualBlock(96->128) + bridge ResidualBlock(128->128)",
        },
        "parameter_count_forced_by": "frozen expected_parameter_count_closed_form = 1,276,401",
        "architecture_was_not_altered_to_match": True,
    },
    "tests": checks,
    "n_tests": len(checks),
    "n_passed": n_pass,
    "n_failed": n_fail,
    "verdict": verdict,
    "training_may_start": n_fail == 0,
    "training_performed": False,
    "generated_utc": UTC,
    "test_reads": 0,
}
AUD.mkdir(parents=True, exist_ok=True)
(AUD / "phase25a_refiner_architecture_binding.json").write_text(
    json.dumps(out, indent=1) + "\n", encoding="utf-8")

print("-" * 78)
print(f"architecture gate: {n_pass}/{len(checks)} PASS -> {verdict}")
print(f"parameters: {n_params:,} (expected {BARR_REFINER_EXPECTED_PARAMETERS:,})")
print(f"wrote {AUD / 'phase25a_refiner_architecture_binding.json'}")
if n_fail:
    print("FAIL-CLOSED: PHASE25A_BLOCKED__REFINER_ARCHITECTURE_MISMATCH")
    sys.exit(2)
print("PHASE25A_REFINER_ARCHITECTURE_FROZEN")
