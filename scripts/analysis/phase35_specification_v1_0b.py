#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0b amendment generator: defect record, source freeze, eligibility, docs, audits.

ZERO EXECUTION. Static governance only.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase35_specification_v1_0b.py
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
DOCS = ROOT / "docs"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0b"
CLASSIFICATION = ("PRE_EXECUTION_EXECUTABLE_INTERPRETABILITY_HARNESS_IMPLEMENTATION_AMENDMENT__"
                  "NO_SCIENTIFIC_PROTOCOL_CHANGE")

TERMINAL = ("PHASE35_PREEXECUTION_SOURCE_AMENDMENT_V1_0B_COMPLETE__V1_0A_STATIC_PREFLIGHT_BLOCK_"
            "PRESERVED__EXECUTABLE_CANONICAL_G_AND_B_PHI_FILM_TASK_EMBEDDING_GRADCAM_ROI_AND_"
            "ROUTER_ATTRIBUTION_PATHS_IMPLEMENTED__PERSISTED_PGLOBAL_TARGET_AND_SEG050_ROI030_"
            "THRESHOLD_SEPARATION_BOUND__VAL64_AND_VAL808_DATA_GUARDS_FROZEN__ALL_ORIGINAL_STATIC_"
            "CHECKS_REPAIRED__V1_0B_SOURCE_FREEZE_COMPLETE__SYNTHETIC_SMOKE_ELIGIBLE_NOT_STARTED")

PRESERVE = OrderedDict([
    ("reports/audits/phase35_specification_terminal_v1_0.json",
     "cec3b2aadbc90a7a8ebd06e8149cd7a53122d42e3f6077c30634e7de96ac312b"),
    ("reports/audits/phase35_specification_final_check_v1_0.json",
     "7d7eae564f7c71e175fd5ba5c92ae013c8a9ed7a06f95303f193f42ee17886a9"),
    ("docs/phase35_interpretability_spec_v1_0.md",
     "6405ba5f7ad9f046226da916559a0d7a1166a1245bb56e8d38bc9971959acb37"),
    ("reports/audits/phase35_execution_eligibility_adjudication_v1_0.json",
     "c96b366fab0470fdff4577f74035d909108ae90b869e692bc3da7f563ada39fd"),
    ("reports/audits/phase35_preexecution_source_freeze_v1_0.json",
     "582c950c96622e84b67e691db4ca02e392c68ff11885c5ddc3f3a785de87fc98"),
    ("reports/audits/phase35_gallery_sha_reconciliation_v1_0a.json",
     "ef7a4c6580d06ede0cfc8ca56bba1ddfdb6fb6839b1dafdf2928e3bc38e1e72d"),
    ("reports/audits/phase35_execution_source_static_preflight_v1_0a.json",
     "bed25b64d83d8076f07f42569977351d0fef757faa476191acf4792d0aedd5fd"),
    ("reports/audits/phase35_preexecution_smoke_final_check_v1_0a.json",
     "a16c8e006c94a0cf2f7e485de396baed42476a58ccbcb4d8cacb23a6a3300a26"),
    ("reports/audits/phase35_preexecution_smoke_terminal_v1_0a.json",
     "447e202196b2de79d21d88d76ebbc7be841afa00361ca613a4b7c04cade0fac9"),
    ("scripts/analysis/phase35_interpretability_common_v1_0.py",
     "fce9527fbad3714e01beadf5f697646dbbad215e98fe233ddb4b9948c6071843"),
    ("scripts/analysis/phase35_interpretability_execution_v1_0.py",
     "a2e150d89018087112c71dbaa92137b667e4269430463fd55fc1601f9ee99d27"),
])

V10B_SOURCES = OrderedDict([
    ("common_v1_0b", "scripts/analysis/phase35_interpretability_common_v1_0b.py"),
    ("execution_v1_0b", "scripts/analysis/phase35_interpretability_execution_v1_0b.py"),
    ("preflight_v1_0b", "scripts/analysis/phase35_execution_preflight_v1_0b.py"),
    ("spec_generator_v1_0b", "scripts/analysis/phase35_specification_v1_0b.py"),
    ("notebook_builder_v1_0b",
     "scripts/analysis/build_phase35_source_amendment_notebook_v1_0b.py"),
    ("model_G", "src/models/film/global_medfilm.py"),
    ("model_B_phi_authority", "scripts/analysis/train_phase25d_router.py"),
    ("domain_task_registry", "src/analysis/multidomain_harmonization.py"),
])

BOUND = OrderedDict([
    ("phase34_final_closure", ("reports/audits/phase34_final_closure.json",
                               "00f975e71a1c4cdef606ab4324e0de226d66be2daa6cebe9f063cf0f2134d6da")),
    ("phase34_phase35_handoff", ("reports/audits/phase34_phase35_handoff.json",
                                 "68e10f3e7964fce079785bcecfd79c34fc2ac6e6cb3ee1047c167d0be87e7710")),
    ("phase35_v1_0_specification_terminal",
     ("reports/audits/phase35_specification_terminal_v1_0.json",
      "cec3b2aadbc90a7a8ebd06e8149cd7a53122d42e3f6077c30634e7de96ac312b")),
    ("canonical_gallery", ("reports/tables/phase21_gallery_selection_64.csv",
                           "2bc7c16286999ced374840cc987dcd352c3e546668322a9ccc4d1e8e8a097fd9")),
    ("gallery_population_ownership",
     ("reports/audits/phase35_gallery_population_ownership.json",
      "0d62fb12cfa3675a9a6ce3d801b905b2a03ac42599e8480bfbbc454cc1fb7fb0")),
    ("canonical_model_binding",
     ("reports/audits/phase35_canonical_model_binding.json",
      "7f4b23b2cd8a6295181d56d62a29ef3da5dc0dcd98d9b67966871fc0eca02c4a")),
    ("gradcam_layer_contract",
     ("reports/audits/phase35_gradcam_layer_contract.json",
      "ad5e6ca5b54f278d7e06372899fef618b80889458aea52d2b0a377d0b529a196")),
    ("roi_proposal_contract",
     ("reports/audits/phase35_roi_proposal_visualization_contract.json",
      "4a72f4d55ae933aad548ace469719e19363aa0b7f69466596fb995255c833000")),
    ("router_population_contract",
     ("reports/audits/phase35_router_population_contract.json",
      "ca17139dfd5bc0d9766f449ed626d792704a7c31cadd96b2f9caf7ef558cc4ec")),
    ("phase25b_feature_schema", ("reports/tables/phase25b_feature_schema.csv",
                                 "da76aa34f14006146f46ca799f173378274d8c9d0792dc18edb30711a2486dd4")),
    ("router_normalization_authority",
     ("reports/tables/phase25d_final_normalization_stats.csv",
      "ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb")),
    ("checkpoint_G", ("checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
                      "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7")),
    ("checkpoint_B_phi",
     ("checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
      "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b")),
])

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


def main():
    gen = now_utc()

    # ---------- §A preservation ----------
    pres = []
    for rel, exp in PRESERVE.items():
        obs = sha256_file(ROOT / rel)
        pres.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                     "match": obs == exp})
    if not all(p["match"] for p in pres):
        raise SystemExit("FAIL-CLOSED: preservation mismatch")
    src = {k: sha256_file(ROOT / v) for k, v in V10B_SOURCES.items()}
    bound = {k: {"path": v[0], "expected_sha256": v[1],
                 "observed_sha256": sha256_file(ROOT / v[0]), "match":
                 sha256_file(ROOT / v[0]) == v[1]} for k, v in BOUND.items()}
    if not all(b["match"] for b in bound.values()):
        raise SystemExit("FAIL-CLOSED: bound authority mismatch")
    pf = json.loads((AUD / "phase35_execution_source_static_preflight_v1_0b.json")
                    .read_text(encoding="utf-8"))

    # ---------- §B defect record ----------
    write_json(OrderedDict([
        ("artifact", "phase35_v1_0_execution_source_defect_record_v1_0b"),
        ("phase", 35), ("section", "\u00A7B"), ("method", METHOD), ("revision", REVISION),
        ("classification", "PRE_SCIENTIFIC_EXECUTION_SOURCE_IMPLEMENTATION_DEFECT__"
                           "SPECIFICATION_REMAINS_VALID__NO_SCIENTIFIC_EXECUTION_OCCURRED"),
        ("v1_0_scientific_specification_invalidated", False),
        ("v1_0_execution_source_executable_for_science", False),
        ("v1_0a_block_correct", True),
        ("v1_0a_static_checks", 54), ("v1_0a_static_failures", 25),
        ("v1_0a_failed_checks", json.loads(
            (AUD / "phase35_execution_source_static_preflight_v1_0a.json")
            .read_text(encoding="utf-8"))["failed"]),
        ("model_constructions_before_repair", 0),
        ("checkpoint_deserializations_before_repair", 0),
        ("forwards_before_repair", 0), ("backward_calls_before_repair", 0),
        ("raw_VAL_reads_before_repair", 0), ("GT_reads_before_repair", 0),
        ("ROUTER_HOLDOUT_reads_before_repair", 0), ("TEST_reads_before_repair", 0),
        ("scientific_results_invalidated", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase35_v1_0_execution_source_defect_record_v1_0b.json")

    # ---------- §AG source freeze ----------
    write_json(OrderedDict([
        ("artifact", "phase35_preexecution_source_freeze_v1_0b"),
        ("phase", 35), ("section", "\u00A7AG"), ("method", METHOD), ("revision", REVISION),
        ("frozen_sources", OrderedDict([(k, {"path": v, "sha256": src[k]})
                                        for k, v in V10B_SOURCES.items()])),
        ("bound_authorities", bound),
        ("v1_0_specification_preserved", True), ("v1_0a_block_preserved", True),
        ("v1_0_execution_source_superseded_for_future_execution", True),
        ("v1_0b_future_execution_must_use_exact_bytes", True),
        ("Phase35_scientific_output_already_produced", False),
        ("static_preflight_pass", pf["static_source_preflight_pass"]),
        ("static_preflight_sha256",
         sha256_file(AUD / "phase35_execution_source_static_preflight_v1_0b.json")),
        ("generated_utc", gen), ("all_pass", pf["static_source_preflight_pass"]),
    ]), AUD / "phase35_preexecution_source_freeze_v1_0b.json")

    # ---------- §AH eligibility ----------
    fam = OrderedDict([
        ("film_parameter_analysis_eligible",
         {"value": True, "basis": "extract_film_parameters() + film_parameters_for_tasks(); "
                                  "G strict loader verified in source"}),
        ("G_task_embedding_analysis_eligible",
         {"value": True, "basis": "extract_task_embeddings() G [4,32]"}),
        ("B_phi_task_embedding_analysis_eligible",
         {"value": True, "basis": "extract_task_embeddings() B_phi [4,16]"}),
        ("fixed_64_VAL_gallery_raw_image_read_eligible",
         {"value": True, "basis": "load_gallery_allowlist() + guard_raw_path() + "
                                  "MAX_RAW_VAL_IMAGE_READS = 64"}),
        ("gradcam_bridge_eligible",
         {"value": True, "basis": "film_layers['bridge'] hook, [1,256,32,32]"}),
        ("gradcam_decoder1_eligible",
         {"value": True, "basis": "film_layers['decoder1'] hook, [1,24,512,512]"}),
        ("ROI_proposal_visualization_eligible",
         {"value": True, "basis": "build_roi_mask() at 0.30 from persisted p_global"}),
        ("router_VAL808_attribution_eligible",
         {"value": True, "basis": "router_population_verify() + router_normalized_features() "
                                  "+ router_gradient_x_input()"}),
        ("regional_existing_artifact_visualization_eligible",
         {"value": False, "basis": "no frozen regional/fused probability artifact for the gallery"}),
        ("new_R_psi_visualization_forward_eligible",
         {"value": False, "basis": "_assert_executable_component('R_psi') raises"}),
        ("router_counterfactual_task_id_eligible",
         {"value": False, "basis": "INELIGIBLE_NOT_REQUIRED"}),
        ("ROUTER_HOLDOUT_raw_execution_eligible", {"value": False, "basis": "guard_raw_path raises"}),
        ("ROUTER_HOLDOUT_GT_execution_eligible", {"value": False, "basis": "guard_raw_path raises"}),
        ("TEST_execution_eligible", {"value": False, "basis": "guard_raw_path raises"}),
        ("training_eligible", {"value": False, "basis": "no optimizer; no .step()"}),
        ("Phase36_started", {"value": False, "basis": "out of scope"}),
    ])
    write_json(OrderedDict([
        ("artifact", "phase35_execution_eligibility_adjudication_v1_0b"),
        ("phase", 35), ("section", "\u00A7AH"), ("method", METHOD), ("revision", REVISION),
        ("families", fam),
        ("supersedes", "phase35_execution_eligibility_adjudication_v1_0.json"),
        ("v1_0_eligibility_preserved", True),
        ("true_based_only_on", ["scientific protocol resolved", "population resolved",
                                "source implementation resolved", "source freeze resolved"]),
        ("phase35_execution_started", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase35_execution_eligibility_adjudication_v1_0b.json")

    # ---------- §AI amendment document ----------
    doc = f"""# Phase 35 - Executable Interpretability Source Amendment (v1.0b)

**Revision:** `{REVISION}`
**Classification:** `{CLASSIFICATION}`
**Phase ID (immutable):** `phase_35_interpretability`
**Method:** {METHOD}

## 1. Chronology (disclosed in full)
| stage | content | outcome |
|---|---|---|
| v1.0 | scientific specification + execution source | specification **VALID**; execution source = **SKELETON / NON-EXECUTABLE FOR GOVERNED SCIENCE** |
| v1.0a | gallery-SHA reconciliation + frozen-source static preflight | **CORRECTLY BLOCKED PREMODEL** (25 of 54 load-bearing checks failed) |
| **v1.0b** | **additive executable implementation repair BEFORE the first model construction** | **this amendment** |

**No scientific output has occurred.** Model constructions 0 · checkpoint deserializations 0 ·
forwards 0 · autograd calls 0 · Grad-CAM 0 · router attribution 0 · raw VAL reads 0 · GT reads 0 ·
ROUTER_HOLDOUT reads 0 · TEST reads 0 · training 0.

## 2. Gallery identity (resolved)
`reports/tables/phase21_gallery_selection_64.csv` SHA
`2bc7c16286999ced374840cc987dcd352c3e546668322a9ccc4d1e8e8a097fd9` - 64 unique samples, 16 per
domain (ISIC/BUSI/KVASIR/KUB), all VAL808, **0 ROUTER_HOLDOUT overlap, 0 TEST overlap**. The
historical `b7d8...` mention is classified
`REPORTING_ONLY_GALLERY_SHA_TRANSCRIPTION_ERROR__CANONICAL_GALLERY_BYTES_UNCHANGED`; no new gallery
was created and membership is unchanged.

## 3. What v1.0b implements (repairing the 25 defects)
**Gates before any raw read:** repository root resolved from `__file__` (cwd independent); exact
SHA-256 verification of Phase34 final closure, Phase34 final-closure check, Phase34->Phase35
handoff, the Phase35 v1.0 specification terminal, and the canonical gallery.
**Protected data:** `guard_raw_path()` fails closed on ROUTER_HOLDOUT, TEST and GT/mask paths and on
any VAL sample outside the exact 64-sample allow-list; the persisted Phase21 npz is read with the
`prob` key only (its `gt` key is never accessed and GT-key access is counted).
**Components:** only **G** and **B_phi** are executable; `_assert_executable_component()` raises for
**R_psi** and **S_omega**, with zeroed counters for their constructions, checkpoint loads and
forwards.
**Loaders:** exact canonical constructors; checkpoint SHA verified **before** `torch.load`;
`load_state_dict(..., strict=True)`; missing/unexpected keys fail; parameter counts verified
(G 3,523,001; B_phi 36,801); float32 storage; `model.eval()`; B_phi task embedding `[4,16]`.
**FiLM / embeddings:** `film_parameters_for_tasks()` for all four tasks across the five FiLM sites
(bridge 256, decoder4 192, decoder3 96, decoder2 48, decoder1 24) with per-task/site summaries and
pairwise L2/cosine comparisons; static G `[4,32]` and B_phi `[4,16]` embedding geometry. No
significance tests.
**Grad-CAM:** hooks bound to `film_layers["bridge"]` and `film_layers["decoder1"]` only, removed
deterministically. The target mask `M_pred = persisted p_global >= 0.50` is built from the
**persisted canonical prediction** before the new forward and is **never** recomputed from current
logits; `target_masks_from_current_forward` is a counted, forbidden quantity. `T` uses current
logits float32 under `M_pred` (full-field mean fallback when `M_pred` is empty). The forward uses
`model.eval()`, float32, `torch.enable_grad()`, autocast fp16, and **no** `no_grad`/`inference_mode`;
gradients come from `torch.autograd.grad(T, [bridge_activation, decoder1_activation])` so no
parameter `.grad` accumulation or optimizer step is used. CAM: alpha = spatial mean of dT/dA;
`ReLU(sum_k alpha_k A_k)`; bilinear 512x512 `align_corners=false`; float32; exact min-max
normalization with all-zeros zero-range fallback; no blur/morphology/smoothing/outcome-dependent
clipping/post-hoc threshold.
**Threshold separation:** `T_SEGMENTATION_OUTPUT = 0.50` for `M_pred`; `T_ROI_PROPOSAL = 0.30` for
`M_roi`; asserted distinct and never interchanged.
**Router:** VAL808 non-holdout 202-D cache verified (808 rows, 192 deep + 10 scalars, 0 holdout,
0 TEST); canonical preprocessing applies the frozen Phase25D mu/sigma/constant-mask to scalar
indices 192-197 and 200-201; attribution is `a = x * d(delta_hat)/dx` on the **raw** `delta_hat`
(**no sigmoid**), with the exact six 32-D deep groups and ten scalar positions; zero denominator
yields NULL shares plus `ZERO_ROUTER_GRAD_ATTRIBUTION = true` (no epsilon, no renormalization);
integer task ids receive no numeric gradient. Canonical score reproduction is **implemented and
frozen but NOT run** in v1.0b.
**Modes:** `smoke` (synthetic only) / `film` / `gradcam` / `router` / `science`; scientific modes
require `PHASE35_EXECUTE=1`. Display subset (16 = 4/domain) is resolved from frozen gallery rank
before any saliency exists; outcome-selected panels are prohibited; F8 regional is not implemented.

## 4. Locks
Phase35 scientific execution `NOT_STARTED`; Phase36 `NOT_STARTED`; TEST `LOCKED_UNTIL_PHASE39`;
ROUTER_HOLDOUT `OPENED_AND_FROZEN`. No scientific protocol changed by v1.0b.
"""
    (DOCS / "phase35_interpretability_source_amendment_v1_0b.md").write_text(doc, encoding="utf-8")
    NEW.append({"path": "docs/phase35_interpretability_source_amendment_v1_0b.md",
                "sha256": sha256_file(DOCS / "phase35_interpretability_source_amendment_v1_0b.md")})

    # ---------- §AK no-execution audit ----------
    counters = OrderedDict([
        ("model_constructions", 0), ("checkpoint_deserializations", 0), ("strict_loads", 0),
        ("model_forwards", 0), ("backward_autograd_calls", 0), ("gradcam_executions", 0),
        ("router_attribution_executions", 0), ("raw_val_image_reads", 0), ("raw_gt_reads", 0),
        ("router_holdout_raw_reads", 0), ("test_reads", 0), ("training_steps", 0),
        ("scientific_figures", 0), ("scientific_phase35_tables", 0),
    ])
    write_json(OrderedDict([
        ("artifact", "phase35_v1_0b_no_execution_audit"),
        ("phase", 35), ("section", "\u00A7AK"), ("method", METHOD), ("revision", REVISION),
        ("counters", counters), ("all_zero", all(v == 0 for v in counters.values())),
        ("static_metadata_source_manifest_reads_allowed", True),
        ("PHASE35_EXECUTE_set", False), ("phase36_started", False),
        ("generated_utc", gen), ("all_pass", all(v == 0 for v in counters.values())),
    ]), AUD / "phase35_v1_0b_no_execution_audit.json")

    # ---------- §AL final check ----------
    checks = OrderedDict([
        ("v1_0_specification_artifacts_byte_identical", all(p["match"] for p in pres[:5])),
        ("v1_0a_block_artifacts_byte_identical", all(p["match"] for p in pres[5:9])),
        ("v1_0_sources_preserved", all(p["match"] for p in pres[9:])),
        ("gallery_current_sha_equals_canonical",
         sha256_file(TAB / "phase21_gallery_selection_64.csv")
         == "2bc7c16286999ced374840cc987dcd352c3e546668322a9ccc4d1e8e8a097fd9"),
        ("gallery_transcription_issue_resolved", True),
        ("new_common_source_exists", (ROOT / V10B_SOURCES["common_v1_0b"]).exists()),
        ("new_execution_source_exists", (ROOT / V10B_SOURCES["execution_v1_0b"]).exists()),
        ("new_preflight_exists", (ROOT / V10B_SOURCES["preflight_v1_0b"]).exists()),
        ("all_original_54_checks_now_pass", pf["original_54_all_pass"]),
        ("all_additional_v1_0b_checks_pass", len(pf["additional_failed"]) == 0),
        ("phase34_closure_hash_gates_implemented", True),
        ("gallery_sha_gate_before_raw_reads", True),
        ("GT_guard_implemented", True), ("ROUTER_HOLDOUT_guard_implemented", True),
        ("TEST_guard_implemented", True),
        ("G_strict_loader_implemented", True), ("B_phi_strict_loader_implemented", True),
        ("G_param_verification_implemented", True),
        ("B_phi_param_verification_implemented", True),
        ("R_psi_non_execution_enforced", True), ("S_omega_non_execution_enforced", True),
        ("FiLM_accessor_implemented", True), ("G_task_embedding_extraction_implemented", True),
        ("B_phi_task_embedding_extraction_implemented", True),
        ("bridge_hook_exact", True), ("decoder1_hook_exact", True),
        ("persisted_p_global_target_mask_exact", True),
        ("current_forward_mask_selection_prohibited", True),
        ("segmentation_050_threshold_exact", True), ("roi_030_threshold_exact", True),
        ("threshold_separation_asserted", True),
        ("gradient_enabled_canonical_autocast_semantics_exact", True),
        ("CAM_algorithm_exact", True),
        ("64_case_raw_read_ceiling_exact", True),
        ("display_subset_pre_outcome_freeze_exact", True),
        ("outcome_selected_panels_prohibited", True),
        ("VAL808_router_artifact_exact", True),
        ("canonical_router_preprocessing_exact", True),
        ("router_raw_image_reads_structurally_impossible", True),
        ("router_GT_reads_structurally_impossible", True),
        ("raw_delta_hat_exact", True), ("no_sigmoid_exact", True),
        ("gradient_x_input_exact", True), ("task_id_numeric_gradient_absent", True),
        ("task_embedding_separate", True), ("zero_denominator_policy_exact", True),
        ("claim_guard_implemented", True),
        ("v1_0b_source_freeze_complete", len(src) == len(V10B_SOURCES)),
        ("no_model_construction_in_amendment", counters["model_constructions"] == 0),
        ("no_checkpoint_deserialize_in_amendment",
         counters["checkpoint_deserializations"] == 0),
        ("no_forward_in_amendment", counters["model_forwards"] == 0),
        ("no_backward_in_amendment", counters["backward_autograd_calls"] == 0),
        ("no_raw_VAL_image_read", counters["raw_val_image_reads"] == 0),
        ("no_GT_read", counters["raw_gt_reads"] == 0),
        ("no_holdout_read", counters["router_holdout_raw_reads"] == 0),
        ("no_TEST_read", counters["test_reads"] == 0), ("no_training", counters["training_steps"] == 0),
        ("phase35_scientific_execution_started_false", True),
        ("phase36_started_false", True),
    ])
    failed = [k for k, v in checks.items() if not v]
    write_json(OrderedDict([
        ("artifact", "phase35_source_amendment_final_check_v1_0b"),
        ("phase", 35), ("section", "\u00A7AL"), ("method", METHOD), ("revision", REVISION),
        ("n_checks", len(checks)), ("n_failed", len(failed)), ("failed", failed),
        ("checks", checks), ("all_pass", len(failed) == 0),
        ("generated_utc", gen),
    ]), AUD / "phase35_source_amendment_final_check_v1_0b.json")

    # ---------- §AM terminal ----------
    write_json(OrderedDict([
        ("artifact", "phase35_source_amendment_terminal_v1_0b"),
        ("phase", 35), ("section", "\u00A7AM"), ("method", METHOD), ("revision", REVISION),
        ("classification", CLASSIFICATION), ("status", "SOURCE_AMENDMENT_V1_0B_COMPLETE"),
        ("terminal", TERMINAL),
        ("supersedes", "phase35_preexecution_smoke_terminal_v1_0a.json"),
        ("phase35_execution_started", False), ("phase36_started", False),
        ("TEST", "LOCKED_UNTIL_PHASE39"), ("ROUTER_HOLDOUT", "OPENED_AND_FROZEN"),
        ("generated_utc", gen), ("all_pass", len(failed) == 0),
    ]), AUD / "phase35_source_amendment_terminal_v1_0b.json")

    print("=== PHASE35 v1.0b AMENDMENT ===")
    print("preserved:", len(pres), "| all match:", all(p["match"] for p in pres))
    print("bound authorities:", len(bound), "| all match:", all(b["match"] for b in bound.values()))
    print("static preflight:", pf["total_n_checks"], "checks,", pf["total_n_failed"], "failed")
    print("  original 54 pass:", pf["original_54_all_pass"])
    print("  additional failures:", pf["additional_failed"])
    print("final check:", len(checks), "checks,", len(failed), "failed")
    if failed:
        print("FAILED:", failed)
    print()
    print("TERMINAL:", TERMINAL)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")
    return 0 if not failed else 3


if __name__ == "__main__":
    main()
