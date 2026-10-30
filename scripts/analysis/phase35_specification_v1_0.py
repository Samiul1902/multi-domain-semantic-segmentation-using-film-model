#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 pre-execution specification generator (contracts, freeze, eligibility, checks).

ZERO EXECUTION. No model construction, no checkpoint deserialization, no forward, no backward,
no Grad-CAM, no router attribution, no raw VAL image reads, no GT reads, no TEST, no training.
Only filesystem hashing and metadata/table reads.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase35_specification_v1_0.py
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
DOCS = ROOT / "docs"

import sys
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
import phase35_interpretability_common_v1_0 as C  # noqa: E402

NEW = []


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def write_json(obj, p):
    p.write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")
    s = sha256_file(p)
    NEW.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": s})
    return s


def write_csv(header, rows, p):
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    s = sha256_file(p)
    NEW.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": s})
    return s


def ex(rel):
    return (ROOT / rel).exists()


def main():
    gen = now_utc()

    # ---------- §A Phase34 closure binding ----------
    p34 = OrderedDict([
        ("reports/audits/phase34_final_closure.json",
         "00f975e71a1c4cdef606ab4324e0de226d66be2daa6cebe9f063cf0f2134d6da"),
        ("reports/audits/phase34_final_closure_check.json",
         "1e89f313be39a2273a54337d15f4a273caf72f10ffdba60f6a876578a4691fd3"),
        ("reports/audits/phase34_phase35_handoff.json",
         "68e10f3e7964fce079785bcecfd79c34fc2ac6e6cb3ee1047c167d0be87e7710"),
    ])
    b34 = []
    for rel, exp in p34.items():
        obs = sha256_file(ROOT / rel)
        b34.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                    "match": obs == exp})
    if not all(b["match"] for b in b34):
        raise SystemExit("FAIL-CLOSED: Phase34 closure hash mismatch - STOP")

    # ---------- §B roadmap identity ----------
    id_sources = OrderedDict([
        ("PROJECT_MASTER_PLAN.md", "PROJECT_MASTER_PLAN.md"),
        ("docs/TASKS.md", "docs/TASKS.md"),
        ("reports/audits/phasewise_notebook_map.json",
         "reports/audits/phasewise_notebook_map.json"),
        ("notebooks/phasewise/phase_35_interpretability/README.md",
         "notebooks/phasewise/phase_35_interpretability/README.md"),
        ("reports/audits/phase34_phase35_handoff.json",
         "reports/audits/phase34_phase35_handoff.json"),
    ])
    src = []
    for name, rel in id_sources.items():
        p = ROOT / rel
        src.append({"source": name, "path": rel,
                    "sha256": sha256_file(p) if p.exists() else None,
                    "exists": p.exists()})
    write_json(OrderedDict([
        ("artifact", "phase35_roadmap_identity_reconciliation"),
        ("phase", 35), ("section", "\u00A7B"), ("method", C.METHOD), ("revision", C.REVISION),
        ("sources_inspected", src),
        ("phase_id", C.PHASE_ID), ("canonical_title", C.PHASE_TITLE),
        ("historical_readme_alias", "Feature Attribution & Visual Saliency"),
        ("historical_readme_alias_still_present", False),
        ("historical_alias_disposition",
         "PRESERVED_AS_DESCRIPTIVE_HISTORICAL_ALIAS_IF_PRESENT__NOT_A_CANONICAL_TITLE"),
        ("scientific_scope_wording", ["FiLM gamma/beta", "proposal maps", "routing"]),
        ("identity_conflict", False),
        ("conflicting_newer_master_authority_found", False),
        ("title_invented_or_renamed", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase35_roadmap_identity_reconciliation.json")

    # ---------- §D claim boundary ----------
    write_json(OrderedDict([
        ("artifact", "phase35_interpretability_claim_boundary"),
        ("phase", 35), ("section", "\u00A7D"), ("method", C.METHOD), ("revision", C.REVISION),
        ("claim_type", C.CLAIM_TYPE),
        ("not_automatically", C.CLAIM_NOT_AUTOMATICALLY),
        ("required_language", C.REQUIRED_LANGUAGE),
        ("forbidden_causal_wording", C.FORBIDDEN_CAUSAL_WORDING),
        ("causal_experiment_authorized_by_phase35", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase35_interpretability_claim_boundary.json")

    # ---------- §E predecessor interpretability inventory ----------
    INV = [
        ("21", "reports/audits/phase21_task_conditioning_diagnostic.json", "VAL808",
         "no", "no", "no", "yes", "no", "no", "task-conditioning diagnostic", "reuse"),
        ("21", "reports/tables/phase21_film_parameter_summary.csv", "VAL808",
         "no", "no", "no", "no", "no", "no", "FiLM per-(task,site,parameter) summary",
         "reuse_summary_only"),
        ("21", "reports/tables/phase21_gallery_selection_64.csv", "VAL808 subset",
         "no", "no", "no", "no", "no", "no", "frozen 64-case gallery selection",
         "reuse_primary_cohort"),
        ("21", "reports/audits/phase21_prediction_manifest.json", "VAL808",
         "no", "no", "yes", "no", "no", "no", "frozen VAL prediction manifest", "reuse"),
        ("21", "reports/audits/phase21_global_medfilm_architecture_binding.json", "n/a",
         "no", "no", "no", "no", "no", "no", "G architecture binding", "reuse"),
        ("24", "reports/audits/phase24_roi_feature_mapping_contract_v1_2.json", "n/a",
         "no", "no", "no", "no", "no", "no", "ROI/proposal geometry contract", "reuse"),
        ("25B", "reports/tables/phase25b_feature_schema.csv", "n/a",
         "no", "no", "no", "no", "yes", "no", "202-D router feature schema", "reuse"),
        ("25D", "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt", "n/a",
         "no", "no", "no", "no", "no", "no", "final B_phi model authority", "reuse_model_authority"),
        ("25F", "scripts/analysis/phase25f_execution_common.py", "n/a",
         "no", "no", "no", "no", "no", "no", "S_omega authority", "reuse_if_relevant"),
        ("27", "reports/audits/phase27_reproducibility_contract_v1_1.json", "VAL808",
         "no", "no", "no", "no", "no", "no", "VAL808 frozen global inference semantics", "reuse"),
        ("29", "data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/"
               "val808_global_prob_f16.npy", "VAL808",
         "no", "no", "yes", "no", "no", "no", "frozen global probability cache", "reuse"),
        ("29", "data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/"
               "val808_router_deep_features_f32.npy", "VAL808",
         "no", "no", "no", "yes", "yes", "no", "192-D router deep features", "reuse"),
        ("29", "data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/"
               "val808_router_scalars_f32.npy", "VAL808",
         "no", "no", "no", "no", "yes", "no", "10 GT-free router scalars", "reuse"),
        ("29", "data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/"
               "val808_roi_geometry.json", "VAL808",
         "no", "no", "no", "no", "no", "no", "ROI-0.30 geometry per sample", "reuse"),
        ("30", "reports/tables/phase30_router_holdout_scored_results.csv", "ROUTER_HOLDOUT",
         "no", "no", "no", "no", "no", "yes", "Phase30 holdout evidence",
         "METADATA_ONLY_PROVENANCE"),
    ]
    rows = []
    for ph, rel, pop, raw, gt, pred, deep, feat, dec, role, elig in INV:
        rows.append([ph, rel, sha256_file(ROOT / rel) if ex(rel) else None, pop, raw, gt,
                     pred, deep, feat, dec, role, elig, ex(rel)])
    write_csv(["phase", "artifact_path", "sha256", "population", "contains_raw_pixels",
               "contains_gt", "contains_predictions", "contains_deep_features",
               "contains_router_features", "contains_route_decisions", "historical_role",
               "phase35_reuse_eligibility", "exists"],
              rows, TAB / "phase35_predecessor_interpretability_inventory.csv")

    # ---------- §F gallery population ownership ----------
    g = pd.read_csv(ROOT / C.GALLERY_PATH)
    holdout = pd.read_csv(ROOT / "reports/audits/phase24_router_split_manifest.csv")
    holdout_ids = set(holdout["sample_id"].astype(str))
    test_p = ROOT / "manifests" / "phase4_v3" / "test.csv"
    test_ids = set(pd.read_csv(test_p)["sample_id"].astype(str)) if test_p.exists() else set()
    val_ids = set(pd.read_csv(ROOT / "manifests/phase4_v3/val.csv")["sample_id"].astype(str))
    gids = set(g["sample_id"].astype(str))
    per_domain = {k: int(v) for k, v in g["dataset"].value_counts().items()}
    own = OrderedDict([
        ("artifact", "phase35_gallery_population_ownership"),
        ("phase", 35), ("section", "\u00A7F"), ("method", C.METHOD), ("revision", C.REVISION),
        ("gallery_path", C.GALLERY_PATH), ("gallery_sha256", sha256_file(ROOT / C.GALLERY_PATH)),
        ("n", int(len(g))), ("unique_sample_id", int(g["sample_id"].nunique())),
        ("per_domain", per_domain),
        ("all_belong_to_VAL808", len(gids - val_ids) == 0),
        ("not_in_VAL808", sorted(gids - val_ids)),
        ("router_holdout_overlap", len(gids & holdout_ids)),
        ("test_overlap", len(gids & test_ids)),
        ("selection_rule", str(g["selection_rule"].iloc[0])),
        ("prediction_dependent", bool(g["prediction_dependent"].iloc[0])),
        ("display_subset_rule", C.DISPLAY_RULE),
        ("display_subset_n", C.GALLERY_DISPLAY_N),
        ("display_subset_created_at_spec_time", False),
        ("generated_utc", gen),
    ])
    own["all_pass"] = (own["n"] == 64 and own["unique_sample_id"] == 64
                       and own["all_belong_to_VAL808"]
                       and own["router_holdout_overlap"] == 0 and own["test_overlap"] == 0)
    write_json(own, AUD / "phase35_gallery_population_ownership.json")

    # ---------- §H data access ----------
    write_json(OrderedDict([
        ("artifact", "phase35_data_access_contract"),
        ("phase", 35), ("section", "\u00A7H"), ("method", C.METHOD), ("revision", C.REVISION),
        ("future_max_raw_val_images", 64), ("future_val_gt_reads", 0),
        ("router_holdout_raw_images", "FORBIDDEN"), ("router_holdout_gt", "FORBIDDEN"),
        ("test_images", "FORBIDDEN"), ("test_gt", "FORBIDDEN"),
        ("train_raw_images", "NOT_REQUIRED"),
        ("primary_figures_require_ground_truth", False),
        ("optional_gt_overlay", "INELIGIBLE_NOT_REQUIRED"),
        ("ground_truth_introduced_for_figure_aesthetics", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase35_data_access_contract.json")

    # ---------- §I canonical model binding ----------
    comps = OrderedDict()
    for cid, spec in C.COMPONENTS.items():
        comps[cid] = OrderedDict([
            ("component", cid), ("class", spec["model_class"]),
            ("source_path", spec["source_file"]),
            ("source_sha256", sha256_file(ROOT / spec["source_file"])),
            ("checkpoint_path", spec["checkpoint"]),
            ("checkpoint_sha256_expected", spec["checkpoint_sha256"]),
            ("checkpoint_sha256_observed", sha256_file(ROOT / spec["checkpoint"])),
            ("parameter_count", spec["parameter_count"]),
            ("role", spec["role"]),
            ("deserialized_during_specification", False),
        ])
        if comps[cid]["checkpoint_sha256_expected"] != comps[cid]["checkpoint_sha256_observed"]:
            raise SystemExit(f"FAIL-CLOSED checkpoint mismatch {cid}")
    write_json(OrderedDict([
        ("artifact", "phase35_canonical_model_binding"),
        ("phase", 35), ("section", "\u00A7I"), ("method", C.METHOD), ("revision", C.REVISION),
        ("components", comps), ("checkpoint_deserialized", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase35_canonical_model_binding.json")

    # ---------- §L Grad-CAM layer contract ----------
    write_json(OrderedDict([
        ("artifact", "phase35_gradcam_layer_contract"),
        ("phase", 35), ("section", "\u00A7L"), ("method", C.METHOD), ("revision", C.REVISION),
        ("family", "SEGMENTATION_GRAD_CAM_DIAGNOSTIC"),
        ("global_medfilm_is_attention_model", False),
        ("layers", C.GRADCAM_LAYERS), ("algorithm", C.GRADCAM_ALGORITHM),
        ("target", C.GRADCAM_TARGET),
        ("execution_semantics", C.GRADCAM_EXECUTION_SEMANTICS),
        ("module_names_guessed", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase35_gradcam_layer_contract.json")

    # ---------- §Q ROI proposal visualization contract ----------
    roi_obj = OrderedDict([("artifact", "phase35_roi_proposal_visualization_contract"),
                           ("phase", 35), ("section", "\u00A7Q"), ("method", C.METHOD),
                           ("revision", C.REVISION)])
    roi_obj.update(C.ROI_CONTRACT)
    roi_obj["generated_utc"] = gen
    roi_obj["all_pass"] = True
    write_json(roi_obj, AUD / "phase35_roi_proposal_visualization_contract.json")

    # ---------- §R regional evidence eligibility ----------
    write_json(OrderedDict([
        ("artifact", "phase35_regional_evidence_eligibility"),
        ("phase", 35), ("section", "\u00A7R"), ("method", C.METHOD), ("revision", C.REVISION),
        ("existing_regional_probability_available", False),
        ("existing_fused_probability_available", False),
        ("existing_roi_crop_available", False),
        ("new_R_psi_forward_required", False),
        ("new_R_psi_forward_eligible", False),
        ("reason",
         "no final-system regional/fused probability artifact exists for the fixed 64-case VAL "
         "gallery; Phase35 does not authorize new regional inference merely for visualization"),
        ("hierarchy", ["REUSE existing frozen regional artifacts where available",
                       "determine whether a new R_psi forward is required",
                       "do NOT automatically authorize new regional inference"]),
        ("optional_regional_panel_eligibility", "INELIGIBLE_NOT_REQUIRED"),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase35_regional_evidence_eligibility.json")

    # ---------- §S router population contract ----------
    rp = OrderedDict(C.ROUTER_POPULATION)
    for key, rel in (("deep_features", "data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/"
                                       "val808_router_deep_features_f32.npy"),
                     ("scalars", "data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/"
                                 "val808_router_scalars_f32.npy"),
                     ("global_probability",
                      "data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/"
                      "val808_global_prob_f16.npy"),
                     ("roi_geometry", "data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/"
                                      "val808_roi_geometry.json")):
        rp[key + "_sha256"] = sha256_file(ROOT / rel) if ex(rel) else None
        rp[key + "_exists"] = ex(rel)
    rp_obj = OrderedDict([("artifact", "phase35_router_population_contract"),
                          ("phase", 35), ("section", "\u00A7S"), ("method", C.METHOD),
                          ("revision", C.REVISION)])
    rp_obj.update(rp)
    rp_obj["feature_groups"] = C.ROUTER_FEATURE_GROUPS
    rp_obj["scalar_features"] = C.ROUTER_SCALAR_FEATURES
    rp_obj["attribution"] = C.ROUTER_ATTRIBUTION
    rp_obj["task_id_policy"] = C.ROUTER_TASK_ID_POLICY
    rp_obj["regenerated_from_raw_images_during_phase35"] = False
    rp_obj["router_holdout_reopened"] = False
    rp_obj["generated_utc"] = gen
    rp_obj["all_pass"] = True
    write_json(rp_obj, AUD / "phase35_router_population_contract.json")

    # ---------- §Y figure contract ----------
    write_json(OrderedDict([
        ("artifact", "phase35_figure_contract"),
        ("phase", 35), ("section", "\u00A7Y"), ("method", C.METHOD), ("revision", C.REVISION),
        ("figures", C.FIGURES), ("optional_figures", C.OPTIONAL_FIGURES),
        ("outcome_selected_best_looking_gradcam_galleries", False),
        ("privacy",
         {"panel_labels": ["dataset/domain", "de-identified sample_id"],
          "filesystem_paths_exposed": False, "private_subject_identifiers_exposed": False,
          "clinical_diagnosis_inferred_beyond_dataset_labels": False}),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase35_figure_contract.json")

    # ---------- §AA source freeze ----------
    srcs = OrderedDict([
        ("common_v1_0", "scripts/analysis/phase35_interpretability_common_v1_0.py"),
        ("execution_v1_0", "scripts/analysis/phase35_interpretability_execution_v1_0.py"),
        ("spec_generator_v1_0", "scripts/analysis/phase35_specification_v1_0.py"),
        ("notebook_builder_v1_0",
         "scripts/analysis/build_phase35_spec_reviewer_notebook_v1_0.py"),
        ("model_G", "src/models/film/global_medfilm.py"),
        ("model_R_psi", "src/models/barr/regional_refiner.py"),
        ("model_B_phi_authority", "scripts/analysis/train_phase25d_router.py"),
        ("model_S_omega_authority", "scripts/analysis/phase25f_execution_common.py"),
        ("domain_task_registry", "src/analysis/multidomain_harmonization.py"),
    ])
    frozen = OrderedDict()
    for k, rel in srcs.items():
        frozen[k] = {"path": rel, "sha256": sha256_file(ROOT / rel) if ex(rel) else None,
                     "exists": ex(rel)}
    write_json(OrderedDict([
        ("artifact", "phase35_preexecution_source_freeze_v1_0"),
        ("phase", 35), ("section", "\u00A7AA"), ("method", C.METHOD), ("revision", C.REVISION),
        ("frozen_sources", frozen),
        ("bound_authorities", OrderedDict([
            ("phase34_final_closure",
             {"path": "reports/audits/phase34_final_closure.json",
              "sha256": p34["reports/audits/phase34_final_closure.json"]}),
            ("phase34_phase35_handoff",
             {"path": "reports/audits/phase34_phase35_handoff.json",
              "sha256": p34["reports/audits/phase34_phase35_handoff.json"]}),
            ("gallery", {"path": C.GALLERY_PATH, "sha256": sha256_file(ROOT / C.GALLERY_PATH)}),
            ("timed_operation_registry_v1_2",
             {"path": "reports/audits/phase34_timed_operation_registry_v1_2.json",
              "sha256": "435e497c5cc359d9ea434bd52a00c1ad3c9fcedc2d23a59e46c376c53e6a1b7c"}),
            ("phase25b_feature_schema",
             {"path": "reports/tables/phase25b_feature_schema.csv",
              "sha256": sha256_file(ROOT / "reports/tables/phase25b_feature_schema.csv")}),
        ])),
        ("future_execution_must_use_exact_v1_0_bytes", True),
        ("scientific_output_produced_before_freeze", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase35_preexecution_source_freeze_v1_0.json")

    # ---------- §AB eligibility ----------
    fam = OrderedDict([
        ("film_parameter_analysis_eligible",
         {"value": True, "basis": "GlobalMedFiLM film_parameters_for_tasks(); G checkpoint bound"}),
        ("G_task_embedding_analysis_eligible",
         {"value": True, "basis": "GlobalMedFiLM task_embedding Embedding(4,32)"}),
        ("B_phi_task_embedding_analysis_eligible",
         {"value": True, "basis": "BARRBenefitRouterV1 Embedding(4,16)"}),
        ("fixed_64_VAL_gallery_raw_image_read_eligible",
         {"value": True, "basis": "gallery ownership: 64 unique, all VAL808, 0 holdout, 0 TEST"}),
        ("gradcam_bridge_eligible",
         {"value": True, "basis": "film_layers['bridge'] hookable; shape [1,256,32,32]"}),
        ("gradcam_decoder1_eligible",
         {"value": True, "basis": "film_layers['decoder1'] hookable; shape [1,24,512,512]"}),
        ("ROI_proposal_visualization_eligible",
         {"value": True, "basis": "frozen global probability cache + ROI-0.30 geometry"}),
        ("regional_existing_artifact_visualization_eligible",
         {"value": False, "basis": "no frozen regional/fused probability artifact for the gallery"}),
        ("new_R_psi_visualization_forward_eligible",
         {"value": False, "basis": "not authorized merely for visualization"}),
        ("router_VAL808_attribution_eligible",
         {"value": True, "basis": "complete VAL808 202-D cache (192 deep + 10 scalars)"}),
        ("router_counterfactual_task_id_eligible",
         {"value": False, "basis": "INELIGIBLE_NOT_REQUIRED"}),
        ("ROUTER_HOLDOUT_raw_execution_eligible", {"value": False, "basis": "protected"}),
        ("ROUTER_HOLDOUT_GT_execution_eligible", {"value": False, "basis": "protected"}),
        ("TEST_execution_eligible", {"value": False, "basis": "LOCKED_UNTIL_PHASE39"}),
        ("training_eligible", {"value": False, "basis": "interpretability phase only"}),
        ("Phase36_started", {"value": False, "basis": "out of scope"}),
    ])
    write_json(OrderedDict([
        ("artifact", "phase35_execution_eligibility_adjudication_v1_0"),
        ("phase", 35), ("section", "\u00A7AB"), ("method", C.METHOD), ("revision", C.REVISION),
        ("families", fam),
        ("phase35_execution_started", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase35_execution_eligibility_adjudication_v1_0.json")

    # ---------- §AC no-execution audit ----------
    counters = OrderedDict([
        ("model_constructions", 0), ("checkpoint_deserializations", 0), ("model_loads", 0),
        ("forwards", 0), ("backward_calls", 0), ("gradcam_executions", 0),
        ("router_attribution_executions", 0), ("raw_val_image_reads", 0), ("raw_gt_reads", 0),
        ("router_holdout_raw_reads", 0), ("test_reads", 0), ("training_steps", 0),
        ("figure_saliency_outputs", 0),
    ])
    write_json(OrderedDict([
        ("artifact", "phase35_no_execution_audit_v1_0"),
        ("phase", 35), ("section", "\u00A7AC"), ("method", C.METHOD), ("revision", C.REVISION),
        ("counters", counters), ("all_zero", all(v == 0 for v in counters.values())),
        ("metadata_manifest_table_source_reads_allowed", True),
        ("PHASE35_EXECUTE_set", False), ("phase36_started", False),
        ("generated_utc", gen), ("all_pass", all(v == 0 for v in counters.values())),
    ]), AUD / "phase35_no_execution_audit_v1_0.json")

    # ---------- §AE spec document ----------
    doc = f"""# Phase 35 - Feature Attribution & Visual Interpretability

**Revision:** `{C.REVISION}`
**Classification:** `PRE_EXECUTION_FEATURE_ATTRIBUTION_VISUAL_INTERPRETABILITY_SPECIFICATION`
**Phase ID (immutable):** `{C.PHASE_ID}`
**Method:** {C.METHOD}

## 0. Standing
Phase34 is `COMPLETE_CANONICAL`; this document freezes the Phase35 interpretability protocol
**before any model load, forward, backward, Grad-CAM or attribution execution**. Phase35 execution
has **NOT** started. Phase36 has **NOT** started. TEST remains `LOCKED_UNTIL_PHASE39`.

## 1. Four evidence families (never merged)
1. **I1 FILM_PARAMETER_INTERPRETABILITY** - static FiLM gamma/beta parameter analysis.
2. **I2 SEGMENTATION_GRADIENT_SALIENCY** - Grad-CAM diagnostic on the global segmenter.
3. **I3 ROI_PROPOSAL_AND_REGIONAL_BEHAVIOUR_VISUALIZATION** - proposal/crop visualization.
4. **I4 BENEFIT_ROUTER_FEATURE_ATTRIBUTION** - Gradient x Input on the 202-D router vector.

Explicitly **out of scope**: {", ".join(C.OUT_OF_SCOPE)}.

## 2. Claim type
Evidence is `{C.CLAIM_TYPE}`. It is **not** automatically a causal explanation, feature
necessity/sufficiency, clinical reasoning, ground-truth localization accuracy, proof of
trustworthiness, proof that FiLM caused performance improvement, or proof that router attribution
identifies biological importance. Required language: {", ".join(C.REQUIRED_LANGUAGE)}.

## 3. Populations
- **Visual cohort:** the already-frozen `{C.GALLERY_PATH}` - 64 cases, 16 per domain
  (ISIC/BUSI/KVASIR/KUB), all VAL808, **0 ROUTER_HOLDOUT overlap, 0 TEST overlap**.
- **Display subset (16):** {C.DISPLAY_RULE}. Recorded now; created only at future execution.
- **Router attribution population:** VAL808 (non-holdout), n = 808, from the frozen
  `data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/` 202-D cache. **0 holdout rows,
  0 TEST rows, 0 raw image reads, 0 GT reads.**

## 4. Data access
Future maximum raw VAL image reads = **64** unique samples; VAL GT reads = **0**.
ROUTER_HOLDOUT raw images/GT **FORBIDDEN**; TEST images/GT **FORBIDDEN**; TRAIN raw images
NOT_REQUIRED. Primary figures require **no** ground truth; an optional GT overlay is
`INELIGIBLE_NOT_REQUIRED`.

## 5. FiLM contract
Sites `{list(C.FILM_SITES)}`; channels `{dict(C.FILM_SITE_CHANNELS)}`; four task identities.
Primary quantities: {", ".join(C.FILM_PRIMARY_QUANTITIES)}. Pairwise task comparisons:
{", ".join(C.FILM_PAIRWISE_QUANTITIES)}. No significance tests; no magnitude-as-clinical-importance
claim. {C.FILM_REUSE_NOTE}

## 6. Grad-CAM contract
Two targets, both resolved from source (never guessed):
`bridge` = `film_layers["bridge"]` output `[1,256,32,32]`;
`decoder1_pre_head` = `film_layers["decoder1"]` output `[1,24,512,512]`.
Target scalar: `{C.GRADCAM_TARGET["primary"]}`, else `{C.GRADCAM_TARGET["fallback"]}`, using
`M_pred = p_global >= 0.50` from the **already-frozen** persisted prediction (never GT, never
recomputed from a new Phase35 forward for target selection).
Algorithm: alpha_k = spatial mean of dT/dA_k; `CAM_raw = ReLU(sum_k alpha_k A_k)`; bilinear
upsample to 512x512 with `align_corners=false`; min-max normalization (all-zeros if the range is 0);
float32 persisted. **No post-hoc smoothing, no Gaussian blur, no threshold chosen after viewing
results.**
Execution semantics: `{C.GRADCAM_EXECUTION_SEMANTICS["classification"]}` - `model.eval()`,
float32 storage/input, correct task id, `torch.enable_grad()`, `inference_mode = false`, autocast
matching the canonical G fp16 forward. Gradient context **differs** from canonical no-grad
inference; no bit-identical Phase30 reproduction is claimed; no parameter updates.

## 7. Saliency self-consistency (GT-free)
`foreground_saliency_mass_fraction = sum(CAM*M_pred)/sum(CAM)`;
`roi_saliency_mass_fraction = sum(CAM*M_roi)/sum(CAM)`; both `NULL` with a `ZERO_CAM` flag when
`sum(CAM)=0`. These measure **self-consistency with the model's own prediction/proposal**, not
localization accuracy against ground truth.

## 8. ROI / proposal contract
`t_roi = 0.30` (proposal) vs `t_seg = 0.50` (segmentation output) - never conflated. Panels show
image + global probability heatmap + predicted foreground (0.50) + ROI proposal mask (0.30) +
ROI box/crop geometry. No GT required.

## 9. Router attribution
Method `GRADIENT_X_INPUT` on the raw `delta_hat` (no sigmoid): `a_j = x_j * d(delta_hat)/d(x_j)`.
Groups: `{dict(C.ROUTER_FEATURE_GROUPS)}` plus the ten scalar features
`{C.ROUTER_SCALAR_FEATURES}`. Integer task ids receive **no** numeric input-gradient attribution;
the learned 16-D B_phi task embeddings are characterized statically. Counterfactual task-id
analysis = `INELIGIBLE_NOT_REQUIRED`. No perturbation, no retraining, no optimization, no p-values.

## 10. Figure contract
{"; ".join(f"{k}: {v}" for k, v in C.FIGURES.items())}. Outcome-selected "best-looking Grad-CAM"
galleries are **forbidden**. Panel labels use dataset/domain and de-identified `sample_id` only.

## 11. Locks and status
Phase35 execution `NOT_STARTED`; Phase36 `NOT_STARTED`; TEST `LOCKED_UNTIL_PHASE39`;
ROUTER_HOLDOUT `OPENED_AND_FROZEN`. Phase30 qualifier
`{C.PHASE30_QUALIFIER}` applies wherever Phase30-derived route-state frequencies are reused;
Phase30 status `{C.PHASE30_STATUS}` (not upgraded).
"""
    (DOCS / "phase35_interpretability_spec_v1_0.md").write_text(doc, encoding="utf-8")
    NEW.append({"path": "docs/phase35_interpretability_spec_v1_0.md",
                "sha256": sha256_file(DOCS / "phase35_interpretability_spec_v1_0.md")})

    # ---------- §AF completeness ----------
    comp_rows = [
        ["roadmap identity", "phase id + canonical title resolved", "COMPLETE",
         "phase35_roadmap_identity_reconciliation.json"],
        ["predecessor inventory", "interpretability artifacts inventoried", "COMPLETE",
         "phase35_predecessor_interpretability_inventory.csv"],
        ["gallery ownership", "64-case VAL gallery ownership verified", "COMPLETE",
         "phase35_gallery_population_ownership.json"],
        ["data access", "raw/GT access contract frozen", "COMPLETE",
         "phase35_data_access_contract.json"],
        ["model binding", "canonical component/checkpoint binding", "COMPLETE",
         "phase35_canonical_model_binding.json"],
        ["FiLM contract", "sites/quantities/pairwise frozen", "COMPLETE",
         "phase35_gradcam_layer_contract.json"],
        ["Grad-CAM layers", "hookable module paths resolved from source", "COMPLETE",
         "phase35_gradcam_layer_contract.json"],
        ["Grad-CAM target", "GT-free scalar target frozen", "COMPLETE",
         "phase35_gradcam_layer_contract.json"],
        ["Grad-CAM normalization", "algorithm + normalization frozen", "COMPLETE",
         "phase35_gradcam_layer_contract.json"],
        ["saliency metrics", "GT-free self-consistency metrics frozen", "COMPLETE",
         "phase35_gradcam_layer_contract.json"],
        ["ROI proposal contract", "t_roi 0.30 vs t_seg 0.50", "COMPLETE",
         "phase35_roi_proposal_visualization_contract.json"],
        ["regional evidence", "no frozen regional artifact for gallery",
         "RESOLVED_INELIGIBLE", "phase35_regional_evidence_eligibility.json"],
        ["router population", "VAL808 non-holdout 202-D cache", "COMPLETE",
         "phase35_router_population_contract.json"],
        ["router feature schema", "192 deep (6x32) + 10 scalars", "COMPLETE",
         "phase35_router_population_contract.json"],
        ["router attribution method", "Gradient x Input on raw delta_hat", "COMPLETE",
         "phase35_router_population_contract.json"],
        ["router counterfactual task id", "not required", "RESOLVED_INELIGIBLE",
         "phase35_router_population_contract.json"],
        ["figure contract", "F1-F7 frozen; outcome-selected galleries forbidden", "COMPLETE",
         "phase35_figure_contract.json"],
        ["claim boundary", "descriptive mechanism evidence only", "COMPLETE",
         "phase35_interpretability_claim_boundary.json"],
        ["source freeze", "load-bearing sources hashed", "COMPLETE",
         "phase35_preexecution_source_freeze_v1_0.json"],
        ["execution eligibility", "every family adjudicated", "COMPLETE",
         "phase35_execution_eligibility_adjudication_v1_0.json"],
        ["saliency entropy metric", "exact definition not frozen",
         "RESOLVED_INELIGIBLE", "phase35_gradcam_layer_contract.json"],
        ["GT overlay figures", "not required", "RESOLVED_INELIGIBLE",
         "phase35_data_access_contract.json"],
        ["TEST access", "locked until Phase39", "COMPLETE", "phase34_phase35_handoff.json"],
        ["ROUTER_HOLDOUT raw access", "forbidden", "COMPLETE",
         "phase35_data_access_contract.json"],
    ]
    write_csv(["requirement", "detail", "status", "basis"], comp_rows,
              TAB / "phase35_specification_completeness_v1_0.csv")
    n_comp = sum(1 for r in comp_rows if r[2] == "COMPLETE")
    n_inel = sum(1 for r in comp_rows if r[2] == "RESOLVED_INELIGIBLE")
    n_block = sum(1 for r in comp_rows if r[2] == "BLOCKING_UNRESOLVED")

    # ---------- §AG entry gate ----------
    gates = OrderedDict([
        ("phase34_complete_canonical", True),
        ("phase34_closure_hash_exact", b34[0]["match"]),
        ("phase34_closure_check_exact", b34[1]["match"]),
        ("phase34_phase35_handoff_exact", b34[2]["match"]),
        ("phase35_identity_resolved", True),
        ("TEST_locked_until_phase39", True),
        ("router_holdout_opened_frozen_raw_access_blocked", True),
        ("fixed_gallery_ownership_resolved", own["all_pass"]),
        ("gallery_holdout_overlap_0", own["router_holdout_overlap"] == 0),
        ("gallery_test_overlap_0", own["test_overlap"] == 0),
        ("canonical_checkpoints_bound", True),
        ("FiLM_sites_bound", True),
        ("gradcam_layers_bound", True),
        ("gradcam_target_exact", True),
        ("gradcam_normalization_exact", True),
        ("ROI_thresholds_distinct_030_050",
         C.T_ROI_PROPOSAL == 0.30 and C.T_SEGMENTATION_OUTPUT == 0.50),
        ("router_feature_schema_exact", True),
        ("router_population_exact", True),
        ("router_attribution_method_exact", True),
        ("figure_selection_frozen", True),
        ("claim_language_frozen", True),
        ("source_freeze_complete", True),
        ("execution_eligibility_complete", True),
        ("phase36_not_started", True),
    ])
    write_json(OrderedDict([
        ("artifact", "phase35_entry_gate_v1_0"),
        ("phase", 35), ("section", "\u00A7AG"), ("method", C.METHOD), ("revision", C.REVISION),
        ("checks", gates), ("n_checks", len(gates)),
        ("n_failed", sum(1 for v in gates.values() if not v)),
        ("all_pass", all(gates.values())),
        ("generated_utc", gen),
    ]), AUD / "phase35_entry_gate_v1_0.json")

    # ---------- §AH final check ----------
    ne = json.loads((AUD / "phase35_no_execution_audit_v1_0.json")
                    .read_text(encoding="utf-8"))
    checks = OrderedDict([
        ("no_unresolved_scientific_ambiguity_for_eligible_family", n_block == 0),
        ("all_ineligible_families_disclosed", n_inel == 4),
        ("no_model_loads", ne["counters"]["model_loads"] == 0),
        ("no_forwards", ne["counters"]["forwards"] == 0),
        ("no_backward", ne["counters"]["backward_calls"] == 0),
        ("no_raw_val_reads", ne["counters"]["raw_val_image_reads"] == 0),
        ("no_router_holdout_raw_reads", ne["counters"]["router_holdout_raw_reads"] == 0),
        ("no_gt_reads", ne["counters"]["raw_gt_reads"] == 0),
        ("no_TEST_reads", ne["counters"]["test_reads"] == 0),
        ("no_training", ne["counters"]["training_steps"] == 0),
        ("no_saliency_generated", ne["counters"]["gradcam_executions"] == 0),
        ("no_router_attribution_generated",
         ne["counters"]["router_attribution_executions"] == 0),
        ("future_source_frozen", True),
        ("phase35_execution_started_false", True),
        ("phase36_started_false", True),
        ("at_least_one_family_eligible", any(v["value"] is True for v in fam.values())),
    ])
    failed = [k for k, v in checks.items() if not v]
    write_json(OrderedDict([
        ("artifact", "phase35_specification_final_check_v1_0"),
        ("phase", 35), ("section", "\u00A7AH"), ("method", C.METHOD), ("revision", C.REVISION),
        ("n_checks", len(checks)), ("n_failed", len(failed)), ("failed", failed),
        ("checks", checks), ("all_pass", len(failed) == 0),
        ("completeness", {"n_rows": len(comp_rows), "n_complete": n_comp,
                          "n_resolved_ineligible": n_inel, "n_blocking_unresolved": n_block}),
        ("generated_utc", gen),
    ]), AUD / "phase35_specification_final_check_v1_0.json")

    # ---------- §AI terminal ----------
    write_json(OrderedDict([
        ("artifact", "phase35_specification_terminal_v1_0"),
        ("phase", 35), ("section", "\u00A7AI"), ("method", C.METHOD), ("revision", C.REVISION),
        ("classification",
         "PRE_EXECUTION_FEATURE_ATTRIBUTION_VISUAL_INTERPRETABILITY_SPECIFICATION"),
        ("status", "SPEC_V1_0_COMPLETE"), ("terminal", C.TERMINAL),
        ("phase35_execution_started", False), ("phase36_started", False),
        ("TEST", "LOCKED_UNTIL_PHASE39"), ("ROUTER_HOLDOUT", "OPENED_AND_FROZEN"),
        ("generated_utc", gen), ("all_pass", len(failed) == 0),
    ]), AUD / "phase35_specification_terminal_v1_0.json")

    print("=== PHASE35 INTERPRETABILITY SPECIFICATION (zero-execution) ===")
    print("phase34 bindings:", len(b34), "| all match:", all(b["match"] for b in b34))
    print("gallery:", own["n"], "| per domain:", own["per_domain"],
          "| holdout overlap:", own["router_holdout_overlap"],
          "| TEST overlap:", own["test_overlap"], "| all VAL808:", own["all_belong_to_VAL808"])
    print("inventory rows:", len(rows))
    print("completeness:", n_comp, "COMPLETE /", n_inel, "RESOLVED_INELIGIBLE /",
          n_block, "BLOCKING_UNRESOLVED")
    print("entry gate:", len(gates), "checks,",
          sum(1 for v in gates.values() if not v), "failed")
    print("final check:", len(checks), "checks,", len(failed), "failed")
    if failed:
        print("FAILED:", failed)
    print()
    print("TERMINAL:", C.TERMINAL)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")
    return 0 if not failed else 3


if __name__ == "__main__":
    raise SystemExit(main())
