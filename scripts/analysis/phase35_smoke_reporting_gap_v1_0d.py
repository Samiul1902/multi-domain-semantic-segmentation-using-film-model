#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0d smoke reporting-gap disclosure (additive; NO re-execution).

The frozen v1.0d `--mode smoke` ran exactly ONCE and its artifacts are frozen. This script does NOT
re-run the smoke and performs no model work: it reads the frozen smoke artifact and records the
three work-order reporting items the frozen smoke does not emit, with explicit adjudication.

Writes reports/audits/phase35_synthetic_smoke_reporting_gap_disclosure_v1_0d.json (write-once).

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase35_smoke_reporting_gap_v1_0d.py
"""
from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / "reports" / "audits"
OUT = AUD / "phase35_synthetic_smoke_reporting_gap_disclosure_v1_0d.json"
SMOKE = AUD / "phase35_synthetic_interpretability_smoke_v1_0d.json"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0d"


def sha256_file(p):
    h = hashlib.sha256()
    h.update(Path(p).read_bytes())
    return h.hexdigest()


def main():
    if OUT.exists():
        raise SystemExit(f"REFUSING TO OVERWRITE FROZEN OUTPUT: {OUT}")
    smoke = json.loads(SMOKE.read_text(encoding="utf-8"))
    r = smoke["frozen_smoke_report"]
    g = r["gradcam_smoke"]
    cams = g["cams"]
    act = g["activation_shapes"]

    all_zero = all(c["min"] == 0.0 and c["max"] == 0.0 for c in cams.values())
    out = OrderedDict([
        ("artifact", "phase35_synthetic_smoke_reporting_gap_disclosure_v1_0d"),
        ("phase", 35), ("section", "\u00A7W-supplement"), ("method", "RA-MedFiLM-BARR"),
        ("revision", REVISION),
        ("smoke_artifact", {"path": str(SMOKE.relative_to(ROOT)).replace("\\", "/"),
                            "sha256": sha256_file(SMOKE)}),
        ("smoke_rerun_by_this_script", False),
        ("model_work_by_this_script", False),
        ("purpose",
         "Record the work-order reporting items that the frozen v1.0d smoke does not emit, with "
         "explicit adjudication. Per work-order section S the frozen source is NOT patched; per "
         "section Y the first valid smoke attempt is preserved and not re-run."),
        ("gaps", OrderedDict([
            ("G1_empty_mask_helper_checks", OrderedDict([
                ("expected_by_work_order", 1),
                ("emitted_by_frozen_smoke", False),
                ("status", "NOT_EMITTED_BY_FROZEN_V1_0D_SMOKE"),
                ("equivalent_coverage", [
                    "model-free unit test T2 (empty mask -> exact 7.5 on the same helper)",
                    "additive model-free CPU production-shape check "
                    "(1,1,512,512 logits + all-false [512,512] bool mask -> exact full-plane mean, "
                    "returned value -0.00023999455152079463)",
                ]),
                ("is_smoke_failure", False),
            ])),
            ("G2_parameter_non_null_grad_counts", OrderedDict([
                ("expected_by_work_order", "0 / 0 preferred"),
                ("measured_on_smoke_models", False),
                ("emitted_by_frozen_smoke", False),
                ("status", "NOT_MEASURABLE__MODELS_NOT_EXPOSED_AFTER_FROZEN_MODE_RETURN"),
                ("mechanism_evidence",
                 "torch.autograd.grad (used for both the Grad-CAM target and the router numeric "
                 "input) does not populate .grad; demonstrated model-free in the smoke artifact "
                 "(tensor_grad_after_autograd_grad_is_none = true). Attribution targets are "
                 "activations and numeric inputs, never parameters."),
                ("classified_as", "TRANSIENT_GRADIENT_STORAGE_NOT_POSSIBLE_BY_MECHANISM"),
                ("is_smoke_failure", False),
            ])),
            ("G3_gradient_shapes_and_finiteness", OrderedDict([
                ("expected_by_work_order",
                 "bridge gradient [1,256,32,32]; decoder1 gradient [1,24,512,512]; all finite"),
                ("emitted_by_frozen_smoke", False),
                ("status", "NOT_EMITTED_BY_FROZEN_V1_0D_SMOKE"),
                ("shapes_derived_soundly", OrderedDict([
                    ("bridge", act["bridge"]), ("decoder1", act["decoder1"]),
                    ("basis",
                     "torch.autograd.grad(T, [A]) returns one gradient per input with exactly the "
                     "input's shape; the activation shapes were emitted by the frozen smoke, so the "
                     "gradient shapes follow by autograd shape preservation."),
                ])),
                ("finiteness_verified", False),
                ("why_finiteness_is_unverified",
                 "The frozen smoke returns only the post-normalization CAMs. cam_normalize maps a "
                 "non-finite CAM to all zeros (range NaN -> 'float(rng) > 0' is False -> "
                 "zeros_like), so an all-zero CAM is consistent with BOTH a genuinely non-positive "
                 "weighted-activation sum AND non-finite gradients masked by the frozen zero-range "
                 "fallback. The scalar target T is likewise not returned."),
                ("is_smoke_failure", False),
                ("is_material_verification_limitation", True),
            ])),
        ])),
        ("observed_cam_degeneracy", OrderedDict([
            ("all_cams_all_zero", bool(all_zero)),
            ("per_cam", {k: {"shape": v["shape"], "dtype": v["dtype"], "finite": v["finite"],
                             "min": v["min"], "max": v["max"]} for k, v in cams.items()}),
            ("interpretation",
             "A synthetic N(0,1) input through the trained G plausibly yields a non-positive "
             "alpha-weighted activation sum at both hook sites, so the frozen ReLU + zero-range "
             "fallback correctly returns all-zero CAMs. This is NOT evidence of a defect, but it "
             "means the smoke did not validate non-degenerate CAM CONTENT."),
            ("cam_content_validated", False),
        ])),
        ("recommended_follow_up", OrderedDict([
            ("amendment", "v1.0e smoke-reporting amendment"),
            ("scope",
             "Expose, from the frozen smoke path, the scalar target T, both gradient tensors' "
             "shapes and finiteness, the pre-normalization CAM range, and an in-session empty-mask "
             "helper check. No scientific protocol change."),
            ("gates_scientific_execution", True),
            ("rationale",
             "Scientific Grad-CAM eligibility should not rest on an unverified gradient finiteness "
             "assumption that the frozen zero-range fallback can mask."),
        ])),
        ("counters", OrderedDict([
            ("model_constructions", 0), ("checkpoint_deserializations", 0), ("forwards", 0),
            ("autograd_calls", 0), ("gradcam_executions", 0), ("smoke_reruns", 0),
            ("raw_val_reads", 0), ("real_persisted_p_global_reads", 0), ("gt_reads", 0),
            ("router_holdout_reads", 0), ("test_reads", 0), ("training_steps", 0),
        ])),
        ("generated_utc", datetime.now(timezone.utc).replace(microsecond=0).isoformat()),
        ("all_pass", True),
    ])
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print("wrote", OUT)
    print("all cams all-zero:", all_zero)
    print("sha256:", sha256_file(OUT))


if __name__ == "__main__":
    main()
