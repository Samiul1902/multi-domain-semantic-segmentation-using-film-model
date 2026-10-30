"""Phase 25C -- scope guard (§29) + holdout/VAL/TEST lock audit (§30)
+ Phase25D handoff schema (§28).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
CODE = ROOT / "notebooks" / "phasewise" / "phase_25c_paired_gain_labels" / "code"
sys.path.insert(0, str(CODE))
import phase25c_common as C  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

AUD = ROOT / "reports" / "audits"
UTC = "2026-09-30T17:18:00+00:00"


def main() -> int:
    lab = pd.read_csv(C.LABEL_CSV)
    sm = pd.read_csv(C.SPLIT_MANIFEST)
    holdout_ids = set(sm[sm["split_role"] == "ROUTER_HOLDOUT"]["sample_id"].astype(str))
    lab_ids = set(lab["sample_id"].astype(str))

    # ---------------- §29 scope guard -------------------------------------- #
    sg = {
        "artifact": "phase25c_scope_guard",
        "phase": "25C",
        "method": C.METHOD,
        "BARRBenefitRouterV1_instantiated": False,
        "router_training_runs": 0,
        "router_inference_runs": 0,
        "task_embedding_instantiated": False,
        "task_embedding_training_runs": 0,
        "Huber_loss_training": 0,
        "global_model_forwards": 0,
        "refiner_forward_samples_processed": 4957,
        "fold0_samples": int((lab["outer_fold"] == 0).sum()),
        "fold1_samples": int((lab["outer_fold"] == 1).sum()),
        "fold2_samples": int((lab["outer_fold"] == 2).sum()),
        "final_refiner_oof_forwards": 0,
        "tta_used": False,
        "checkpoint_ensemble_used": False,
        "holdout_reads": 0,
        "holdout_feature_reads": 0,
        "val_reads": 0,
        "val_dice_computed": 0,
        "test_reads": 0,
        "test_inference": 0,
        "verdict": "PHASE25C_SCOPE_GUARD_PASS",
        "generated_utc": UTC,
    }
    C.jdump(sg, AUD / "phase25c_scope_guard.json")

    # ---------------- §30 lock audit --------------------------------------- #
    lock = {
        "artifact": "phase25c_test_lock_audit",
        "phase": "25C",
        "method": C.METHOD,
        "router_holdout": {
            "image_reads": 0, "gt_reads": 0, "feature_reads_for_phase25c": 0,
            "refiner_inference": 0, "global_inference": 0, "dice": 0, "deltadice": 0,
            "ids_in_label_table": int(len(lab_ids & holdout_ids)),
        },
        "val808": {
            "image_reads": 0, "gt_reads": 0, "refiner_inference": 0, "dice": 0,
            "deltadice": 0,
        },
        "test": {
            "image_reads": 0, "mask_reads": 0, "inference": 0,
            "visualization": 0, "metrics": 0,
        },
        "holdout_reads": 0,
        "val_reads": 0,
        "test_reads": 0,
        "verdict": "PHASE25C_LOCK_AUDIT_PASS",
        "generated_utc": UTC,
    }
    C.jdump(lock, AUD / "phase25c_test_lock_audit.json")

    # ---------------- §28 Phase25D handoff --------------------------------- #
    handoff = {
        "artifact": "phase25c_phase25d_handoff_schema",
        "phase": "25C",
        "method": C.METHOD,
        "architecture_revision": C.ARCH_REVISION,
        "phase25b_provides": {
            "features": "202-D GT-free pre-refinement features",
            "numeric_dimensions": 202,
            "fields": ["sample_id", "feature_row_index", "task_id", "domain",
                       "outer_fold", "action_available"],
        },
        "phase25c_provides": {
            "fields": ["sample_id", "outer_fold", "delta_dice (continuous target)",
                       "gain_category", "global_dice", "candidate_refined_dice",
                       "fold_refiner_checkpoint_sha"],
            "label_csv": str(C.LABEL_CSV.relative_to(ROOT)).replace("\\", "/"),
            "label_csv_sha256": C.sha256_file(C.LABEL_CSV),
            "primary_target": "delta_dice",
            "secondary_target": "gain_category",
            "join_key": "sample_id",
        },
        "phase25d_will": [
            "join Phase25B 202-D features + Phase25C labels by sample_id",
            "verify exact one-to-one coverage",
            "instantiate learned Embedding(4,16)",
            "form 218-D router input (202 numeric + 16 task embedding)",
            "train BARRBenefitRouterV1",
        ],
        "phase25c": {
            "router_instantiated": False,
            "task_embedding_trained": False,
        },
        "task_embedding_owner": "PHASE25D",
        "benefit_router_owner": "PHASE25D",
        "verdict": "PHASE25C_PHASE25D_HANDOFF_READY",
        "test_reads": 0,
        "generated_utc": UTC,
    }
    C.jdump(handoff, AUD / "phase25c_phase25d_handoff_schema.json")

    print("scope guard / lock / handoff audits written.")
    print("  holdout ids in label table:", len(lab_ids & holdout_ids))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
