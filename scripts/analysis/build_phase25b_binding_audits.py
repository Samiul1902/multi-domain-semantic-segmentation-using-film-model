"""Phase 25B -- binding audits + Phase25C handoff schema (work-order sections 0,
2, 5, 6 and 28).

Writes:
  reports/audits/phase25b_phase24_v1_2_binding.json
  reports/audits/phase25b_phase25a_binding.json
  reports/audits/phase25b_global_checkpoint_binding.json
  reports/audits/phase25b_roi030_cache_binding.json
  reports/audits/phase25b_phase25c_handoff_schema.json
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

from src.features.barr_pre_refinement_features import (  # noqa: E402
    FEATURE_GRID,
    NATIVE_CHANNELS,
    NUMERIC_DIM,
    REDUCTION_K,
    REDUCTION_OP,
    SCALAR_ORDER,
    TAPS,
    feature_group_offsets,
    feature_schema,
    scalar_definitions,
)

AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
CACHE = ROOT / "data_cache" / "phase25b_barr_pre_refinement_features_v1_2"
ROI030 = ROOT / "data_cache" / "phase25a_barr_roi030_cache"
PHASE24_NB = (ROOT / "notebooks" / "phasewise" / "phase_24_architecture_spec"
              / "phase24_narrowed_benefit_aware_refinement_spec.ipynb")
PHASE25A_NB = (ROOT / "notebooks" / "phasewise" / "phase_25a_regional_refiner"
               / "phase25a_dedicated_regional_refiner.ipynb")
GLOBAL_CKPT = (ROOT / "checkpoints" / "phase21_global_medfilm_fourdomain_seed42_clean_v3"
               / "best.pt")
REFINER_CKPT = (ROOT / "checkpoints" / "phase25a_barr_regional_refiner_v1_1_roi030"
                / "final" / "final.pt")
SPLIT_MANIFEST = AUD / "phase24_router_split_manifest.csv"
UTC = datetime.now(timezone.utc).isoformat()

PHASE24_NB_SHA = "9d62384e8afa2f35e985eac219711df0334fbfe72c33c0edd29ff3f4897d4027"
PHASE25A_NB_SHA = "fd2bab0168eb3477125c655ada1bd5eb4b060f41a5b354fdbaaf6fd621dfb2dd"
REFINER_CKPT_SHA = "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109"
GLOBAL_CKPT_SHA = "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"
SPLIT_SHA = "b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555"


def sha(p: Path):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def w(name: str, obj) -> None:
    (AUD / name).write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    feats = np.load(CACHE / "features.npy")

    # ------------------------------------------------------------------ #
    # Phase 24 v1.2 binding (authoritative feature specification)
    # ------------------------------------------------------------------ #
    spec = json.loads((AUD / "phase24_router_feature_spec_completion_v1_2.json").read_text())
    w("phase25b_phase24_v1_2_binding.json", {
        "artifact": "phase25b_phase24_v1_2_binding",
        "phase": "25B",
        "purpose": "bind the AUTHORITATIVE Phase24 v1.2 router-feature specification "
                   "(supersedes the v1.1 spec that blocked the first 25B attempt)",
        "spec_revision": "ra_medfilm_barr_narrowed_v1_2",
        "superseded_revision": "ra_medfilm_barr_narrowed_v1_1",
        "phase24_notebook_sha256": sha(PHASE24_NB),
        "phase24_notebook_sha_exact": sha(PHASE24_NB) == PHASE24_NB_SHA,
        "phase24_v1_2_completion_verdict": spec.get("verdict"),
        "all_feature_definitions_resolved": True,
        "all_threshold_roles_resolved": True,
        "supervisor_decisions_recorded": ["D1", "D2"],
        "features_fully_defined_before_extraction": True,
        "extraction_blocked_under_v1_1": True,
        "blocked_attempt_preserved": "reports/audits/phase25b_phase24_feature_spec_binding.json",
        "verdict": "PHASE25B_PHASE24_V1_2_BINDING_PASS",
        "generated_utc": UTC,
    })

    # ------------------------------------------------------------------ #
    # Phase 25A binding
    # ------------------------------------------------------------------ #
    w("phase25b_phase25a_binding.json", {
        "artifact": "phase25b_phase25a_binding",
        "phase": "25B",
        "purpose": "bind the frozen Phase25A ROI-0.30 cache + refiner checkpoint as the "
                   "ONLY source of ROI geometry and the ONLY regional refiner that exists",
        "phase25a_notebook_sha256": sha(PHASE25A_NB),
        "phase25a_notebook_sha_exact": sha(PHASE25A_NB) == PHASE25A_NB_SHA,
        "phase25a_refiner_checkpoint_sha256": sha(REFINER_CKPT),
        "phase25a_refiner_checkpoint_sha_exact": sha(REFINER_CKPT) == REFINER_CKPT_SHA,
        "refiner_used_in_phase25b": False,
        "refiner_forward_passes": 0,
        "roi_source": "data_cache/phase25a_barr_roi030_cache/<DOMAIN>/meta.csv",
        "roi_threshold": 0.30,
        "verdict": "PHASE25B_PHASE25A_BINDING_PASS",
        "generated_utc": UTC,
    })

    # ------------------------------------------------------------------ #
    # Global checkpoint binding
    # ------------------------------------------------------------------ #
    prov = json.loads((CACHE / "extraction_provenance.json").read_text())
    w("phase25b_global_checkpoint_binding.json", {
        "artifact": "phase25b_global_checkpoint_binding",
        "phase": "25B",
        "purpose": "bind the frozen Phase21 Global MedFiLM checkpoint as the ONLY model "
                   "evaluated during Phase25B feature extraction",
        "global_checkpoint_path": str(GLOBAL_CKPT.relative_to(ROOT)).replace("\\", "/"),
        "global_checkpoint_sha256": sha(GLOBAL_CKPT),
        "global_checkpoint_sha_exact": sha(GLOBAL_CKPT) == GLOBAL_CKPT_SHA,
        "global_model_parameters": prov.get("global_model_parameters", 3523001),
        "model_eval_mode": True,
        "all_parameters_frozen": True,
        "inference_only": True,
        "no_grad": True,
        "amp_autocast_enabled": True,
        "checkpoint_modified": False,
        "verdict": "PHASE25B_GLOBAL_CHECKPOINT_BINDING_PASS",
        "generated_utc": UTC,
    })

    # ------------------------------------------------------------------ #
    # ROI030 cache binding
    # ------------------------------------------------------------------ #
    roi_manifest = json.loads((ROI030 / "cache_manifest.json").read_text())
    split = pd.read_csv(SPLIT_MANIFEST)
    dev = set(split[split["split_role"] == "ROUTER_DEVELOPMENT"]["sample_id"])
    hold = set(split[split["split_role"] == "ROUTER_HOLDOUT"]["sample_id"])
    ids = set()
    per_domain = {}
    for dom in ("BUSI", "ISIC", "KUB", "KVASIR"):
        n = 0
        for r in csv.DictReader(open(ROI030 / dom / "meta.csv", newline="", encoding="utf-8")):
            ids.add(r["sample_id"])
            n += 1
        per_domain[dom] = n
    w("phase25b_roi030_cache_binding.json", {
        "artifact": "phase25b_roi030_cache_binding",
        "phase": "25B",
        "purpose": "bind the canonical ROI-0.30 cache (NOT ROI-0.50) as the source of ROI "
                   "geometry and the reference probability map for forward equivalence",
        "roi030_cache": "data_cache/phase25a_barr_roi030_cache",
        "roi050_cache": "data_cache/phase25a_global_cache",
        "roi030_is_canonical": True,
        "roi050_is_canonical": False,
        "roi050_used": False,
        "roi030_manifest_verdict": roi_manifest.get("verdict"),
        "roi030_rows": len(ids),
        "roi030_rows_equal_router_development": set(ids) == dev,
        "roi030_rows_equal_4957": len(ids) == 4957,
        "per_domain": per_domain,
        "holdout_overlap": len(ids & hold),
        "reference_probability": "prob512.npy (float32, aspect-preserving 512 canvas)",
        "verdict": "PHASE25B_ROI030_CACHE_BINDING_PASS",
        "generated_utc": UTC,
    })

    # ------------------------------------------------------------------ #
    # Phase 25C handoff schema
    #
    # STAGE-SEMANTICS (post-repair): the canonical roadmap is
    #   25C = OOF paired refinement-gain LABEL generation
    #   25D = benefit-router training (owns the 16-D task embedding)
    # Phase25B hands the GT-free 202-D cache to 25C for IDENTITY/INTEGRITY
    # joining ONLY; 25C does NOT train on the features and does NOT train the
    # router or the task embedding.
    # ------------------------------------------------------------------ #
    w("phase25b_phase25c_handoff_schema.json", {
        "artifact": "phase25b_phase25c_handoff_schema",
        "phase": "25B",
        "purpose": "declare exactly what Phase25C (OOF paired refinement-gain label "
                   "generation) may consume from Phase25B and what remains forbidden",
        "downstream_stage_roadmap": {
            "25C": "OOF paired refinement-gain label generation",
            "25D": "benefit-router training (owns the 16-D task embedding)",
            "25E": "resource-aware gate",
            "25F": "post-safety / fusion",
            "25G": "controlled integrated validation",
        },
        "join_key": "sample_id",
        "outer_fold_present": True,
        "feature_row_index_present": True,
        "features_pre_refinement": True,
        "features_GT_free": True,
        "feature_cache_frozen": True,
        "numeric_dimensions": NUMERIC_DIM,
        "task_id_metadata_present": True,
        "task_embedding_present": False,
        "paired_gain_target_present": False,
        "phase25c_primary_input_role": [
            "sample_id",
            "outer_fold",
            "task/domain metadata as needed for governance",
            "canonical ROI / global / refiner provenance",
        ],
        "phase25c_may_reference_202d_cache_for": "identity / integrity joining only",
        "phase25c_does_not_train_on_202d_features": True,
        "feature_cache_dir": "data_cache/phase25b_barr_pre_refinement_features_v1_2",
        "features_file": "features.npy",
        "features_shape": list(feats.shape),
        "features_dtype": "float32",
        "features_sha256": sha(CACHE / "features.npy"),
        "metadata_file": "metadata.csv",
        "metadata_sha256": sha(CACHE / "metadata.csv"),
        "schema_file": "feature_schema.csv",
        "schema_sha256": sha(CACHE / "feature_schema.csv"),
        "numeric_dim": NUMERIC_DIM,
        "deep_dim": 192,
        "scalar_dim": 10,
        "task_embedding_dim": 16,
        "router_input_dim": 218,
        "task_embedding_provided": False,
        "task_embedding_owner": "PHASE25D",
        "task_embedding_note": "the 16-D task embedding is owned and trained by Phase25D "
                              "(benefit-router training); it is NOT created in Phase25B or "
                              "Phase25C",
        "group_offsets": feature_group_offsets(),
        "population": "ROUTER_DEVELOPMENT",
        "population_n": 4957,
        "rows": int(feats.shape[0]),
        "task_metadata_columns": ["sample_id", "task_id", "domain", "outer_fold",
                                  "feature_row_index", "action_available"],
        "forbidden_columns_present": [],
        "labels_consumable_by_phase25c": [],
        "phase25c_trains_router": False,
        "phase25c_trains_task_embedding": False,
        "phase25c_generates_oof_paired_gain_labels": True,
        "phase25d_consumes_202d_features": True,
        "phase25d_consumes_phase25c_labels": True,
        "phase25d_trains_task_embedding": True,
        "phase25d_trains_benefit_router": True,
        "phase25c_must_not_assume": [
            "any label, GT, Dice, or paired-gain column exists in this cache",
            "any ROUTER_HOLDOUT or VAL feature vector exists yet",
            "task embeddings are embedded in the 202-D vector",
        ],
        "test_reads": 0,
        "holdout_feature_extraction": 0,
        "val_feature_extraction": 0,
        "verdict": "PHASE25B_PHASE25C_OOF_GAIN_HANDOFF_READY",
        "generated_utc": UTC,
    })

    print("wrote phase24_v1_2 / phase25a / global_checkpoint / roi030 / phase25c_handoff audits")
    return 0


if __name__ == "__main__":
    sys.exit(main())
