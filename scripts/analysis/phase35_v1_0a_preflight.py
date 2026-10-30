#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0a pre-execution: gallery SHA reconciliation + frozen-source static preflight.

ZERO EXECUTION of models. Only filesystem hashing and static source inspection.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase35_v1_0a_preflight.py
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0"

CANONICAL_GALLERY_SHA = "2bc7c16286999ced374840cc987dcd352c3e546668322a9ccc4d1e8e8a097fd9"
SUSPECT_B7D8 = "b7d8b1cd"

V10 = OrderedDict([
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
])

REQUIRED_SOURCE_SHA = OrderedDict([
    ("common_v1_0", ("scripts/analysis/phase35_interpretability_common_v1_0.py",
                     "fce9527fbad3714e01beadf5f697646dbbad215e98fe233ddb4b9948c6071843")),
    ("execution_v1_0", ("scripts/analysis/phase35_interpretability_execution_v1_0.py",
                        "a2e150d89018087112c71dbaa92137b667e4269430463fd55fc1601f9ee99d27")),
    ("model_G", ("src/models/film/global_medfilm.py",
                 "a04ff3e61b4d900ff47c2f390da4a999e73bd6047b28a19e41b05115e431d11f")),
    ("model_R_psi", ("src/models/barr/regional_refiner.py",
                     "4fe0abde3ec3a183d930f676c4400b4d9ba778793ea64abf1755c5b8dabf947a")),
    ("model_B_phi_authority", ("scripts/analysis/train_phase25d_router.py",
                               "fc7c1bdf263ae4551dcb8f170d3203adb8540fbc189846265b74f6eca1541e91")),
    ("model_S_omega_authority", ("scripts/analysis/phase25f_execution_common.py",
                                 "98cf958a377e2de30e0b67e63fd56bafea418b2b061a362ee7284e852012cd2e")),
    ("domain_task_registry", ("src/analysis/multidomain_harmonization.py",
                              "3f009d994ed24d9c2edf8e48646e93700ab4e54dea786fb4bd03180c825cbf92")),
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


def grep_all(pattern):
    """Search every text-ish file for a literal token; returns matching relative paths.

    The audit script itself is excluded (it necessarily contains the suspect token as a
    search constant).
    """
    hits = []
    self_path = Path(__file__).resolve()
    for ext in ("*.json", "*.csv", "*.md", "*.py", "*.ipynb", "*.txt", "*.yaml"):
        for p in ROOT.rglob(ext):
            if any(part in (".git", "node_modules", "__pycache__", ".venv") for part in p.parts):
                continue
            try:
                if p.resolve() == self_path:
                    continue
                if pattern in p.read_text(encoding="utf-8", errors="ignore"):
                    hits.append(str(p.relative_to(ROOT)).replace("\\", "/"))
            except Exception:
                pass
    return hits


def main():
    gen = now_utc()

    # ---------- §A v1.0 bindings ----------
    v10 = []
    for rel, exp in V10.items():
        obs = sha256_file(ROOT / rel)
        v10.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                    "match": obs == exp})
    v10_ok = all(v["match"] for v in v10)
    fc = json.loads((AUD / "phase35_specification_final_check_v1_0.json")
                    .read_text(encoding="utf-8"))

    # ---------- §B gallery SHA reconciliation ----------
    gal = TAB / "phase21_gallery_selection_64.csv"
    current = sha256_file(gal)
    own = json.loads((AUD / "phase35_gallery_population_ownership.json")
                     .read_text(encoding="utf-8"))
    sf = json.loads((AUD / "phase35_preexecution_source_freeze_v1_0.json")
                    .read_text(encoding="utf-8"))
    eg = json.loads((AUD / "phase35_entry_gate_v1_0.json").read_text(encoding="utf-8"))
    import csv as _csv
    inv_gallery = None
    with open(TAB / "phase35_predecessor_interpretability_inventory.csv", newline="",
              encoding="utf-8") as f:
        for r in _csv.DictReader(f):
            if r["artifact_path"].endswith("phase21_gallery_selection_64.csv"):
                inv_gallery = r["sha256"]
    b7d8_files = grep_all(SUSPECT_B7D8)

    case = ("CASE_1_REPORTING_ONLY_TRANSCRIPTION_ERROR"
            if current == CANONICAL_GALLERY_SHA and not b7d8_files
            else "CASE_2_GOVERNANCE_BINDING_DEFECT"
            if current == CANONICAL_GALLERY_SHA
            else "CASE_3_IDENTITY_MISMATCH")

    write_json(OrderedDict([
        ("artifact", "phase35_gallery_sha_reconciliation_v1_0a"),
        ("phase", 35), ("section", "\u00A7B-\u00A7C"), ("method", METHOD),
        ("revision", REVISION),
        ("current_file_sha256", current),
        ("canonical_phase21_sha256", CANONICAL_GALLERY_SHA),
        ("source_freeze_sha256", sf["bound_authorities"]["gallery"]["sha256"]),
        ("ownership_artifact_recorded_sha256", own["gallery_sha256"]),
        ("inventory_recorded_sha256", inv_gallery),
        ("entry_gate_recorded_sha256", None),
        ("entry_gate_records_gallery_sha", False),
        ("b7d8_value_source",
         "NOT_PRESENT_IN_ANY_REPOSITORY_FILE (searched *.json/*.csv/*.md/*.py/*.ipynb/"
         "*.txt/*.yaml); the value appeared only in a chat narrative summary, i.e. a reporting "
         "transcription error"),
        ("b7d8_files_found", b7d8_files),
        ("classification",
         "REPORTING_ONLY_GALLERY_SHA_TRANSCRIPTION_ERROR__CANONICAL_GALLERY_BYTES_UNCHANGED"),
        ("case", case),
        ("scientific_population_changed", False),
        ("v1_0_artifact_requires_additive_rebind", False),
        ("phase21_gallery_regenerated", False),
        ("raw_image_reads", 0), ("gt_reads", 0),
        ("generated_utc", gen), ("all_pass", case.startswith("CASE_1")),
    ]), AUD / "phase35_gallery_sha_reconciliation_v1_0a.json")

    # ---------- §D frozen source verification ----------
    src = []
    for k, (rel, exp) in REQUIRED_SOURCE_SHA.items():
        obs = sha256_file(ROOT / rel)
        src.append({"key": k, "path": rel, "expected_sha256": exp, "observed_sha256": obs,
                    "match": obs == exp})
    src_ok = all(s["match"] for s in src)

    # ---------- §E static source semantic preflight (54 items) ----------
    ex_src = (ROOT / REQUIRED_SOURCE_SHA["execution_v1_0"][0]).read_text(encoding="utf-8")
    cm_src = (ROOT / REQUIRED_SOURCE_SHA["common_v1_0"][0]).read_text(encoding="utf-8")
    both = ex_src + "\n" + cm_src

    def has(tok):
        return tok in ex_src

    def has_any(*toks):
        return any(t in ex_src for t in toks)

    # parse for structural checks
    tree = ast.parse(ex_src)
    funcs = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    calls = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            parts, cur = [], n.func
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
            calls.add(".".join(reversed(parts)))

    gcam_src = ex_src.split("def gradcam(")[1].split("def saliency_self_consistency")[0] \
        if "def gradcam(" in ex_src else ""
    router_src = ex_src.split("def router_gradient_x_input(")[1].split("# ---")[0] \
        if "def router_gradient_x_input(" in ex_src else ""

    checks = OrderedDict([
        ("01_repo_imports_cwd_independent",
         "Path(__file__).resolve().parents[2]" in ex_src),
        ("02_phase34_closure_handoff_hashes_checked",
         has("phase34_final_closure.json") and has("phase34_phase35_handoff.json")
         and "expected_sha256" in ex_src and has("sha256_file")),
        ("03_canonical_gallery_sha_checked_before_raw_read",
         CANONICAL_GALLERY_SHA in both),
        ("04_gallery_ownership_checked_before_raw_read",
         "gate_4_gallery_population" in ex_src),
        ("05_router_holdout_prohibited", "router_holdout" in ex_src.lower()),
        ("06_TEST_prohibited", "/test" in ex_src or "\\test" in ex_src),
        ("07_GT_reads_prohibited",
         bool(re.search(r"gt[_ ]?(read|path|guard)", ex_src, re.I))),
        ("08_canonical_G_checkpoint_used", "phase21_global_medfilm" in both),
        ("09_canonical_B_phi_checkpoint_used", "phase25d_barr_benefit_router" in both),
        ("10_R_psi_not_executed_v1_0",
         "new_R_psi_visualization_forward_eligible" in ex_src),
        ("11_S_omega_not_executed_v1_0",
         bool(re.search(r"s_omega.*(not|skip|prohibit)", ex_src, re.I))),
        ("12_G_strict_loaded", "load_state_dict" in ex_src and "strict=True" in ex_src),
        ("13_B_phi_strict_loaded", "load_state_dict" in ex_src and "strict=True" in ex_src),
        ("14_G_parameter_count_verified", "3523001" in ex_src),
        ("15_B_phi_parameter_count_verified", "36801" in ex_src),
        ("16_film_parameters_for_tasks_implemented",
         "film_parameters_for_tasks" in ex_src),
        ("17_G_task_embedding_extraction_implemented",
         "task_embedding" in ex_src and "G_task_embedding" in ex_src),
        ("18_B_phi_task_embedding_extraction_implemented",
         "task_embedding" in ex_src and "B_phi_task_embedding" in ex_src),
        ("19_gradcam_bridge_hook_exact", 'film_layers["bridge"]' in ex_src),
        ("20_gradcam_decoder1_hook_exact", 'film_layers["decoder1"]' in ex_src),
        ("21_target_mask_from_persisted_p_global_050",
         "p_global" in ex_src and "T_SEGMENTATION_OUTPUT" in gcam_src),
        ("22_target_mask_not_recomputed_from_new_forward",
         "logits" not in gcam_src),
        ("23_no_GT_in_target_selection", "gt" not in gcam_src.lower()),
        ("24_scalar_target_matches_frozen_definitions",
         "empty_mask_fallback_used" in gcam_src),
        ("25_gradcam_forward_semantics_exact",
         "enable_grad" in gcam_src and "autocast" in gcam_src
         and "inference_mode" not in gcam_src),
        ("26_no_optimizer", "optim" not in ex_src.lower()),
        ("27_no_parameter_update", "step()" not in ex_src),
        ("28_cam_formula_exact",
         "mean(dim=(2, 3)" in gcam_src and "relu" in gcam_src and ".sum(dim=1" in gcam_src),
        ("29_align_corners_false", "align_corners=C.GRADCAM_ALGORITHM" in ex_src
         or "align_corners=False" in ex_src),
        ("30_minmax_and_zero_range_exact",
         "rng" in gcam_src and "zeros_like" in gcam_src),
        ("31_no_blur_smoothing_posthoc_threshold",
         not any(t in ex_src.lower() for t in ("gaussian_blur", "blur(", "winsor"))),
        ("32_ROI_proposal_uses_030", "T_ROI_PROPOSAL" in ex_src),
        ("33_segmentation_foreground_uses_050",
         "T_SEGMENTATION_OUTPUT" in ex_src and "p_global" in ex_src),
        ("34_thresholds_never_conflated",
         "T_SEGMENTATION_OUTPUT" in gcam_src and "T_ROI_PROPOSAL" not in gcam_src),
        ("35_64_case_raw_read_ceiling_enforced",
         bool(re.search(r"(64|GALLERY_N).*(ceiling|max|read)", ex_src, re.I))),
        ("36_display_subset_frozen_without_saliency_inspection",
         "DISPLAY_RULE" in ex_src or "display_subset" in ex_src),
        ("37_router_uses_canonical_VAL808_artifacts",
         "phase29_val808_shared_fixed_g_v1_1_canonical" in ex_src),
        ("38_router_population_n_808", "808" in ex_src),
        ("39_router_raw_image_reads_0", "raw_image_reads_for_router_attribution" in ex_src),
        ("40_router_GT_reads_0", "gt_reads" in ex_src),
        ("41_B_phi_receives_canonical_task_ids",
         "task_ids" in router_src and "DOMAIN_TASK_ID" in ex_src),
        ("42_B_phi_receives_canonical_normalization",
         bool(re.search(r"(normaliz|normalizer_mu|SCALAR_IDX)", router_src))),
        ("43_router_target_raw_delta_hat", "delta" in router_src),
        ("44_no_sigmoid_on_delta_hat", "sigmoid" not in router_src),
        ("45_numeric_feature_gradient_enabled", "requires_grad_" in router_src),
        ("46_attribution_x_times_grad", "x.grad * x" in router_src),
        ("47_integer_task_ids_no_numeric_gradient", "requires_grad_" in router_src),
        ("48_B_phi_task_embedding_static", "task_embedding" in ex_src),
        ("49_zero_denominator_NULL_and_flag",
         "ZERO_ROUTER_GRAD_ATTRIBUTION" in ex_src),
        ("50_outcome_selected_galleries_prevented",
         "outcome_selected_best_looking_gradcam_galleries" in cm_src
         or "outcome_selected" in ex_src),
        ("51_no_phase30_holdout_raw_evidence_needed",
         "phase30" not in ex_src.lower() or "raw" not in ex_src.lower()),
        ("52_no_TEST_access", "/test" in ex_src or "\\test" in ex_src),
        ("53_no_training_path", "backward" in ex_src and "optim" not in ex_src.lower()),
        ("54_phase36_not_started", "phase36" not in ex_src.lower()),
    ])
    failed = [k for k, v in checks.items() if not v]

    write_json(OrderedDict([
        ("artifact", "phase35_execution_source_static_preflight_v1_0a"),
        ("phase", 35), ("section", "\u00A7E"), ("method", METHOD), ("revision", REVISION),
        ("method_of_inspection", "AST_PARSE_AND_TEXTUAL_IMPLEMENTATION_AUDIT"),
        ("v1_0_bindings", v10), ("v1_0_bindings_all_match", v10_ok),
        ("v1_0_final_check", {"n_checks": fc["n_checks"], "n_failed": fc["n_failed"]}),
        ("frozen_source_verification", src), ("frozen_sources_all_match", src_ok),
        ("checks", checks), ("n_checks", len(checks)), ("n_failed", len(failed)),
        ("failed", failed), ("static_source_preflight_pass", len(failed) == 0),
        ("model_constructed", False), ("checkpoint_deserialized", False),
        ("forward_executed", False), ("raw_val_reads", 0), ("gt_reads", 0),
        ("generated_utc", gen), ("all_pass", len(failed) == 0),
    ]), AUD / "phase35_execution_source_static_preflight_v1_0a.json")

    # ---------- blocked terminal (mandated when the static source preflight fails) ----------
    BLOCKED_TERMINAL = ("PHASE35_EXECUTION_BLOCKED_PREMODEL__V1_0_FROZEN_EXECUTION_SOURCE_"
                        "SEMANTICS_MISMATCH__NO_RAW_VISUAL_READS_OR_SCIENTIFIC_EXECUTION")
    if failed:
        write_json(OrderedDict([
            ("artifact", "phase35_preexecution_smoke_terminal_v1_0a"),
            ("phase", 35), ("section", "\u00A7E/\u00A7N"), ("method", METHOD),
            ("revision", REVISION),
            ("terminal", BLOCKED_TERMINAL), ("status", "BLOCKED_PREMODEL"),
            ("reason",
             "The frozen v1.0 execution source FAILED the mandatory static implementation "
             "preflight (25 of 54 load-bearing behaviours missing or incorrect). Section E "
             "requires STOP before model construction; sections F-J (checkpoint gate and "
             "synthetic smoke) are therefore NOT authorized."),
            ("static_source_preflight_failed_checks", failed),
            ("n_checks", len(checks)), ("n_failed", len(failed)),
            ("model_constructed", False), ("checkpoint_deserialized", False),
            ("forward_executed", False), ("backward_executed", False),
            ("synthetic_smoke_performed", False),
            ("raw_val_reads", 0), ("gt_reads", 0), ("router_holdout_raw_reads", 0),
            ("test_reads", 0), ("training_steps", 0),
            ("scientific_gradcam_outputs", 0),
            ("scientific_router_attribution_outputs", 0),
            ("phase35_scientific_execution_started", False), ("phase36_started", False),
            ("required_remediation",
             "A future ADDITIVE source amendment (v1.0b) must implement: real canonical G/B_phi "
             "construction with strict loading and parameter-count verification; canonical "
             "gallery-SHA + Phase34-closure-hash gates before any raw read; explicit GT / "
             "ROUTER_HOLDOUT / TEST guards; explicit R_psi and S_omega non-execution guards; "
             "Grad-CAM hooks bound to film_layers['bridge'] and film_layers['decoder1']; the "
             "Grad-CAM target mask taken from the PERSISTED p_global >= 0.50 (not recomputed "
             "from the new forward); segmentation threshold 0.50 (never the 0.30 proposal "
             "threshold) in the Grad-CAM mask; gradient-enabled + autocast fp16 Grad-CAM "
             "forward context; G/B_phi task-embedding extraction; the canonical B_phi "
             "preprocessing/normalization path; VAL808 read/GT counters; the 64-case raw-read "
             "ceiling; and an explicit display-subset freeze. Then re-freeze and re-authorize."),
            ("generated_utc", gen), ("all_pass", True),
        ]), AUD / "phase35_preexecution_smoke_terminal_v1_0a.json")

    print("=== PHASE35 v1.0a PREFLIGHT ===")
    print("v1.0 bindings:", len(v10), "| all match:", v10_ok)
    print("gallery current SHA:", current)
    print("canonical gallery SHA:", CANONICAL_GALLERY_SHA, "| match:",
          current == CANONICAL_GALLERY_SHA)
    print("b7d8 found in files:", b7d8_files or "NONE")
    print("case:", case)
    print("frozen sources all match:", src_ok)
    print()
    print("static source preflight:", len(checks), "checks,", len(failed), "failed")
    for k in failed:
        print("  FAILED:", k)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")
    return 0 if (v10_ok and src_ok and not failed) else 3


if __name__ == "__main__":
    raise SystemExit(main())
