"""Phase 25C -- prospective refiner inference execution binding (§9).

No authoritative Phase24/Phase25A inference-precision/batch contract exists
(Phase25A trained with AMP; no OOF/eval precision was ever frozen). Therefore a
contract is frozen prospectively HERE, before any DeltaDice is inspected.

Classification: PRE_EXECUTION_OPERATIONAL_BINDING
    selected_before_oof_outcomes = true
    result_driven = false
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
CODE = ROOT / "notebooks" / "phasewise" / "phase_25c_paired_gain_labels" / "code"
sys.path.insert(0, str(CODE))
import phase25c_common as C  # noqa: E402

AUD = ROOT / "reports" / "audits"
UTC = "2026-09-30T16:58:00+00:00"


def main() -> int:
    # search for an existing authoritative inference precision/batch contract
    found = []
    for p in sorted(AUD.glob("phase24*.json")) + sorted(AUD.glob("phase25a*.json")):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if ("inference_precision" in txt or "inference_batch" in txt
                or "oof_inference" in txt):
            found.append(p.name)
    preexisting = bool(found)

    out = {
        "artifact": "phase25c_refiner_inference_execution_binding",
        "phase": "25C",
        "method": C.METHOD,
        "classification": "PRE_EXECUTION_OPERATIONAL_BINDING",
        "preexisting_frozen_inference_contract_found": preexisting,
        "preexisting_contract_artifacts": found,
        "rationale": (
            "No authoritative Phase24/Phase25A inference precision/batch contract is "
            "explicitly frozen (Phase25A trained with AMP but never froze an OOF/eval "
            "precision). A contract is therefore frozen prospectively here, BEFORE any "
            "DeltaDice is inspected, to avoid any outcome-driven choice."
        ),
        "selected_before_oof_outcomes": True,
        "result_driven": False,
        "binding": {
            "inference_precision": "float32",
            "autocast_enabled": False,
            "amp_enabled": False,
            "amp_rationale": (
                "AMP kernel selection depends on batch MEMBERSHIP; FP32 removes that "
                "non-determinism so OOF inference is a pure function of the sample."
            ),
            "model_mode": "eval",
            "inference_context": "torch.inference_mode()",
            "grad_enabled": False,
            "tta": False,
            "stochastic_augmentation": False,
            "dropout_behavior": "inactive (model.eval(); architecture has no dropout)",
            "checkpoint_ensemble": False,
            "checkpoint_averaging": False,
            "best_of_multiple_predictions": False,
            "sample_order": "deterministic: sort by dataset/domain then sample_id",
            "batch_size": C.INFERENCE_BATCH,
            "drop_last": False,
            "refiner_input_channels": 4,
            "refiner_input_resolution": C.REGIONAL_INPUT_RESOLUTION,
            "refiner_input_construction": (
                "[R,G,B] = rgb_crop(uint8)/255.0 float32 ; [p_global_crop] = "
                "prob_crop float16 -> float32  (exact BARRRefinerCropDataset train=False path)"
            ),
            "logit_to_probability": "sigmoid(logits.float())",
            "one_primary_forward_per_sample": True,
            "repeat_or_best_of_forbidden": True,
        },
        "folds_use": {f"fold{k}": "fold-specific best.pt only" for k in C.OUTER_FOLDS},
        "phase25a_final_refiner_used_for_oof": False,
        "verdict": "PHASE25C_REFINER_INFERENCE_BINDING_FROZEN",
        "test_reads": 0,
        "generated_utc": UTC,
    }
    C.jdump(out, AUD / "phase25c_refiner_inference_execution_binding.json")
    print("inference execution binding frozen (FP32, eval, inference_mode, batch 8).")
    print("  preexisting contract found:", preexisting, found)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
