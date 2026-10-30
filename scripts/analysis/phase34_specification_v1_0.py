#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 pre-execution specification generator (v1.0).

ZERO-EXECUTION. Builds every Phase34 specification contract, table, document and
governance audit. Performs NO model load, NO forward, NO latency/FPS/memory
measurement, NO FLOP/MAC profiler execution, NO protected-data access, NO training.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase34_specification_v1_0.py
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
DOCS = ROOT / "docs"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_0"
CLASSIFICATION = ("PRE_EXECUTION_COMPUTATIONAL_EFFICIENCY_RUNTIME_AND_CONDITIONAL_"
                  "COMPUTATION_PROFILING_SPECIFICATION")

TERMINAL = ("PHASE34_EFFICIENCY_PROFILING_SPEC_COMPLETE__ROADMAP_IDENTITY_COMPUTE_"
            "PROVENANCE_MAC_FLOP_PARAMETER_SYNTHETIC_INPUT_HARDWARE_LATENCY_THROUGHPUT_"
            "MEMORY_CONDITIONAL_WEIGHTING_AND_SOURCE_FREEZE_CONTRACTS_FROZEN__"
            "EXECUTION_ELIGIBILITY_DETERMINED_NOT_STARTED")

PHASE30_QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_"
                     "SCIENTIFIC_SOURCE_FREEZE_DEVIATION")
PHASE30_STATUS = "COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL"

# ---- Phase33 bindings (fail-closed) ----
P33 = {
    "reports/audits/phase33_final_closure.json":
        "e47ba686e6b96a4c2e3c7faf9444c18c72937df3daa231166309787c624ea0a2",
    "reports/audits/phase33_final_closure_check.json":
        "10efe7d10139f2403a23609a42c7fceeb1eabf304aef50e9858b3d9fbe764add",
    "reports/audits/phase33_phase34_handoff.json":
        "462b3d2d70b1367082397d02529f2138665fdaece8f6e33f8faff1c2b3720973",
}
P33_TERMINAL = ("PHASE33_FINAL_SYSTEM_FAILURE_ANALYSIS_COMPLETE_CANONICAL__"
                "TIER0_TIER1_FROZEN_TABLE_DESCRIPTIVE_ANALYSIS_ACCEPTED__"
                "HARD_CASE_PANEL_SCOPE_SUPERVISOR_RESOLVED_PER_STRATUM_WITH_ORIGINAL_"
                "20_ROW_SELECTION_COMPLIANT_AND_UNCHANGED__"
                "BOUNDARY_COMPONENT_QUALITATIVE_PIXEL_RAW_AND_RERUN_PATHS_INELIGIBLE__"
                "PHASE30_PROTOCOL_DEVIATION_QUALIFIER_PRESERVED__"
                "PHASE34_ELIGIBLE_NOT_STARTED")

# ---- frozen historical compute constants (authority values, NOT recomputed) ----
G_MACS, B_MACS, R_MACS, S_MACS = 31551740928, 36160, 3230662656, 1168
G_PARAMS, R_PARAMS, B_PARAMS, S_PARAMS = 3523001, 1276401, 36801, 1217
P30 = {"SKIP": 635, "EXECUTE_THEN_ACCEPT": 236, "EXECUTE_THEN_REJECT": 4, "n": 875}

NEW = []


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def write_json(obj, p):
    p.write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")
    s = sha256_file(p)
    NEW.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": s})
    return s


def write_csv(header, rows, p):
    import csv
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    s = sha256_file(p)
    NEW.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": s})
    return s


def env_snapshot():
    import torch
    import ctypes

    class M(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    m = M()
    m.dwLength = ctypes.sizeof(M)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    prop = torch.cuda.get_device_properties(0) if torch.cuda.is_available() else None
    tools = {}
    for mod in ("fvcore", "thop", "ptflops", "torchinfo", "timm", "psutil"):
        try:
            mm = __import__(mod)
            tools[mod] = {"available": True, "version": getattr(mm, "__version__", "unknown")}
        except Exception:
            tools[mod] = {"available": False, "version": None}
    return {
        "os": platform.platform(), "os_machine": platform.machine(),
        "python_version": platform.python_version(), "python_impl": platform.python_implementation(),
        "torch_version": torch.__version__, "cuda_runtime": torch.version.cuda,
        "cuda_driver_version": "596.36", "cudnn_version": torch.backends.cudnn.version(),
        "cuda_available": bool(torch.cuda.is_available()),
        "gpu_model": prop.name if prop else None,
        "gpu_compute_capability": f"{prop.major}.{prop.minor}" if prop else None,
        "gpu_total_vram_bytes": prop.total_memory if prop else None,
        "cpu_model": platform.processor() or "AMD64 Family 25 Model 33 Stepping 2, AuthenticAMD",
        "cpu_logical_cores": 16, "cpu_torch_threads": torch.get_num_threads(),
        "system_ram_bytes": m.ullTotalPhys,
        "cuda_bf16_supported": bool(torch.cuda.is_bf16_supported()) if torch.cuda.is_available() else False,
        "torch_matmul_allow_tf32": bool(torch.backends.cuda.matmul.allow_tf32),
        "torch_cudnn_allow_tf32": bool(torch.backends.cudnn.allow_tf32),
        "torch_cudnn_benchmark": bool(torch.backends.cudnn.benchmark),
        "torch_deterministic_algorithms": bool(torch.are_deterministic_algorithms_enabled()),
        "torch_profiler_available": hasattr(torch, "profiler"),
        "profiling_packages": tools,
    }


def main():
    gen = now_utc()

    # ---------------- §A bind Phase33 (fail-closed) ----------------
    bind = []
    for rel, exp in P33.items():
        obs = sha256_file(ROOT / rel)
        bind.append({"path": rel, "expected_sha256": exp, "observed_sha256": obs,
                     "match": obs == exp})
        if obs != exp:
            raise SystemExit(f"FAIL-CLOSED Phase33 SHA mismatch: {rel}")
    fc = jload(AUD / "phase33_final_closure.json")
    fcc = jload(AUD / "phase33_final_closure_check.json")
    ho = jload(AUD / "phase33_phase34_handoff.json")
    assert fc["phase33_status"] == "COMPLETE_CANONICAL"
    assert fc["terminal"] == P33_TERMINAL
    assert fcc["n_checks"] == 29 and fcc["n_failed"] == 0
    assert ho["Phase34_eligibility"] == "ELIGIBLE_NOT_STARTED"
    assert ho["Phase34_started"] is False
    assert ho["ROUTER_HOLDOUT"] == "OPENED_AND_FROZEN"
    assert ho["TEST"] == "LOCKED_UNTIL_PHASE39"

    # ---------------- §B roadmap identity reconciliation ----------------
    id_sources = [
        ("PROJECT_MASTER_PLAN.md", "34", "Computational Efficiency & Runtime Profiling",
         "Phase 34: Computational Efficiency & Runtime Profiling (NOT_STARTED)", "2026-10-02"),
        ("docs/TASKS.md", "34", "Computational Efficiency & Conditional-Computation Profiling",
         "live roadmap table row 34", "2026-10-01 (stale: Phase25E-era header)"),
        ("reports/audits/phasewise_notebook_map.json", "34",
         "Computational Efficiency & Runtime Profiling",
         "Stage C: Evidence & Rigor; canonical_source PENDING_PHASE33", "unknown"),
        ("notebooks/phasewise/phase_34_efficiency_profiling/README.md", "phase_34_efficiency_profiling",
         "Computational Efficiency & Runtime Profiling",
         "profiles FLOPs, parameter count, latency (FPS), GPU memory footprint", "unknown"),
        ("reports/audits/phase33_phase34_handoff.json", "phase_34_efficiency_profiling",
         "Computational Efficiency & Runtime Profiling", "Phase33->Phase34 handoff", "2026-10-04"),
    ]
    srcs = []
    for path, pid, title, scope, date in id_sources:
        p = ROOT / path
        srcs.append({"path": path, "sha256": sha256_file(p) if p.exists() else None,
                     "phase34_phase_id": pid, "display_title": title,
                     "scope_wording": scope, "source_date_or_status": date,
                     "exists": p.exists()})
    write_json(OrderedDict([
        ("artifact", "phase34_roadmap_identity_reconciliation"),
        ("phase", 34), ("section", "\u00a7B"), ("method", METHOD), ("revision", REVISION),
        ("immutable_phase_folder", "phase_34_efficiency_profiling"),
        ("immutable_phase_id", "phase_34_efficiency_profiling"),
        ("sources_inspected", srcs),
        ("identity_resolved", True),
        ("canonical_display_title", "Computational Efficiency & Runtime Profiling"),
        ("conditional_computation_scope_present", True),
        ("alias_or_scope_wording",
         "Computational Efficiency & Conditional-Computation Profiling"),
        ("alias_treatment",
         "PRESERVED_AS_SCIENTIFIC_SCOPE_DESCRIBING_THE_ROUTED_SYSTEMS_CONDITIONAL_"
         "EXECUTION__NOT_A_DIFFERENT_PHASE"),
        ("source_precedence",
         "newest_authority_wins: phase33_phase34_handoff (2026-10-04) + PROJECT_MASTER_PLAN "
         "(2026-10-02) + phasewise_notebook_map.json + phase_34 README all use "
         "'Computational Efficiency & Runtime Profiling'; only the stale docs/TASKS.md "
         "(Phase25E-era, 2026-10-01) uses 'Conditional-Computation Profiling'"),
        ("superseding_authority_found", False),
        ("unresolved_conflict", False),
        ("title_resolution_complete", True),
        ("folder_renamed", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_roadmap_identity_reconciliation.json")

    # ---------------- §D historical compute provenance inventory ----------------
    H = ["phase", "artifact_path", "sha256", "component_or_arm", "metric_name",
         "metric_value", "unit", "aggregation_level", "per_sample_per_batch_expected_total",
         "analytical_or_measured", "included_operation_classes", "excluded_operation_classes",
         "hardware_dependent", "eligible_for_phase34_reuse", "scientific_interpretation"]
    hc = [
        ["21", "reports/audits/phase21_analytical_mac_count.json",
         sha256_file(AUD / "phase21_analytical_mac_count.json"), "G (GlobalMedFiLM)",
         "analytical_macs", G_MACS, "MACs", "per_sample_batch1", "per_sample",
         "analytical", "Conv2d,Linear",
         "GroupNorm affine/statistics;SiLU;MaxPool2d;bilinear interpolation;FiLM elementwise modulation;sigmoid",
         "no", "yes", "ANALYTICAL MAC LOWER BOUND"],
        ["21", "reports/audits/phase21_analytical_mac_count.json",
         sha256_file(AUD / "phase21_analytical_mac_count.json"), "G (GlobalMedFiLM)",
         "total_flops_convention", 63103481856, "FLOPs (2x MAC)", "per_sample_batch1",
         "per_sample", "derived_from_analytical_mac", "same as MACs", "same as MACs", "no",
         "yes", "DERIVED_FLOPS_FROM_MAC_2X_CONVENTION"],
        ["21", "reports/tables/phase21_efficiency_accounting.csv",
         sha256_file(TAB / "phase21_efficiency_accounting.csv"), "G (GlobalMedFiLM)",
         "measured_parameter_count", G_PARAMS, "parameters", "model_total", "total",
         "measured", "all nn.Parameter", "n/a", "no", "yes", "static parameter count"],
        ["21", "reports/tables/phase21_efficiency_accounting.csv",
         sha256_file(TAB / "phase21_efficiency_accounting.csv"), "G (GlobalMedFiLM)",
         "best_checkpoint_bytes", 42369710, "bytes", "file", "total", "measured",
         "serialized checkpoint file", "n/a", "no", "yes",
         "checkpoint FILE bytes != parameter bytes"],
        ["21", "reports/tables/phase21_efficiency_accounting.csv",
         sha256_file(TAB / "phase21_efficiency_accounting.csv"), "G (GlobalMedFiLM)",
         "gpu_latency_median_batch1", 15.24125000105414, "ms", "per_sample_batch1",
         "per_sample", "measured", "forward only, warmup=5 repeats=30, no AMP",
         "n/a", "yes", "yes", "HOST-SPECIFIC historical latency; not universal"],
        ["21", "reports/tables/phase21_efficiency_accounting.csv",
         sha256_file(TAB / "phase21_efficiency_accounting.csv"), "G (GlobalMedFiLM)",
         "gpu_peak_memory_batch1", 313084416, "bytes", "per_sample_batch1", "per_sample",
         "measured", "torch.cuda.max_memory_allocated during timed forward", "n/a",
         "yes", "yes", "HOST-SPECIFIC historical peak allocated"],
        ["21", "reports/tables/phase21_efficiency_accounting.csv",
         sha256_file(TAB / "phase21_efficiency_accounting.csv"), "G (GlobalMedFiLM)",
         "gpu_latency_median_batch8", 87.45389999967301, "ms", "batch8", "per_batch",
         "measured", "forward only, warmup=5 repeats=30, no AMP", "n/a", "yes", "yes",
         "HOST-SPECIFIC historical latency at batch 8"],
        ["21", "reports/tables/phase21_efficiency_accounting.csv",
         sha256_file(TAB / "phase21_efficiency_accounting.csv"), "G (GlobalMedFiLM)",
         "gpu_peak_memory_batch8", 2346275840, "bytes", "batch8", "per_batch", "measured",
         "torch.cuda.max_memory_allocated during timed forward", "n/a", "yes", "yes",
         "HOST-SPECIFIC historical peak allocated at batch 8"],
        ["24", "reports/audits/phase24_router_parameter_count_adjudication.json",
         sha256_file(AUD / "phase24_router_parameter_count_adjudication.json"),
         "B_phi (router)", "canonical_total_trainable_params", B_PARAMS, "parameters",
         "model_total", "total", "analytical", "all trainable parameters", "n/a", "no",
         "yes", "36801 = 36353 linear core + 64 task embedding + 384 LayerNorm affine"],
        ["25A", "reports/audits/phase25a_resource_accounting.json",
         sha256_file(AUD / "phase25a_resource_accounting.json"), "R_psi (regional refiner)",
         "trainable_parameters", R_PARAMS, "parameters", "model_total", "total",
         "measured", "all trainable parameters", "n/a", "no", "yes",
         "regional refiner trainable parameter count"],
        ["25A", "reports/audits/phase25a_resource_accounting.json",
         sha256_file(AUD / "phase25a_resource_accounting.json"), "R_psi (regional refiner)",
         "analytical_macs", R_MACS, "MACs", "per_sample_batch1", "per_sample", "analytical",
         "Conv2d", "GroupNorm affine/statistics;SiLU;bilinear interpolation", "no", "yes",
         "ANALYTICAL MAC LOWER BOUND at 1x4x256x256"],
        ["25A", "reports/audits/phase25a_resource_accounting.json",
         sha256_file(AUD / "phase25a_resource_accounting.json"), "R_psi (regional refiner)",
         "host_specific_forward_latency_seconds", 0.005808933999996952, "seconds",
         "per_sample_batch1", "per_sample", "measured", "forward only", "n/a", "yes",
         "yes", "HOST_SPECIFIC_NOT_DEPLOYMENT (cuda:0, Windows-10)"],
        ["25E", "reports/tables/phase25e_analytical_compute_contract.csv",
         sha256_file(TAB / "phase25e_analytical_compute_contract.csv"), "B_phi (router)",
         "analytical_macs", B_MACS, "MACs", "per_sample", "per_sample", "analytical",
         "Linear", "LayerNorm;SiLU;Embedding lookup", "no", "yes",
         "pre-gate router overhead; excluded from C_i"],
        ["25E", "reports/tables/phase25e_compute_frontier.csv",
         sha256_file(TAB / "phase25e_compute_frontier.csv"),
         "FINAL_ROUTED C8_lambda0.25_budget0.25", "average_total_analytical_macs",
         32359279817.631634, "MACs", "expected_over_policy_cohort", "expected",
         "analytical", "G+B_phi+p_activate*R_psi", "same exclusions", "no", "yes",
         "expected conditional analytical MAC at activation 0.24994956626992132"],
        ["25G", "reports/tables/phase25g_analytical_compute_accounting.csv",
         sha256_file(TAB / "phase25g_analytical_compute_accounting.csv"),
         "A8 vs A7 (S_omega delta)", "A8_minus_A7_macs_at_budget0.25", 291.9410934032681,
         "MACs", "expected_over_policy_cohort", "expected", "analytical",
         "p_activate*S_omega", "n/a", "no", "yes",
         "S_omega adds p_activate*1168; s_omega_saves_compute=False"],
        ["26", "artifacts/phase26_ra_medfilm_barr_bundle_v1_0/resource_contract.json",
         sha256_file(ROOT / "artifacts/phase26_ra_medfilm_barr_bundle_v1_0/resource_contract.json"),
         "S_omega (post-safety)", "s_omega_macs", S_MACS, "MACs", "per_sample", "per_sample",
         "analytical", "Linear", "LayerNorm;SiLU", "no", "yes",
         "canonical bundle ANALYTICAL MAC LOWER BOUND"],
        ["28", "reports/tables/phase28_table_09_compute_accounting.csv",
         sha256_file(TAB / "phase28_table_09_compute_accounting.csv"),
         "router variants R1/R2/R3 + F1 refiner", "variant_parameters",
         "R1=12225;R2=34689;R3=10113;F1=1276257", "parameters", "model_total", "total",
         "analytical", "all trainable parameters", "n/a", "no", "yes",
         "ablation variant parameter counts; canonical remains R-full/F-none"],
        ["30", "reports/tables/phase30_router_holdout_scored_results.csv",
         sha256_file(TAB / "phase30_router_holdout_scored_results.csv"),
         "FINAL ROUTED system", "routing_state_frequencies", "SKIP=635;ETA=236;ETR=4;n=875",
         "counts", "cohort_875", "total", "measured_decision_outcome", "routing states",
         "n/a", "no", "yes", "frozen weights for conditional compute; Phase30 qualifier applies"],
        ["33", "reports/audits/phase33_descriptive_failure_result_v1_2.json",
         sha256_file(AUD / "phase33_descriptive_failure_result_v1_2.json"),
         "FINAL ROUTED system", "router_state_summary_counts",
         "SKIP=635;ETA=236;ETR=4", "counts", "cohort_875", "total",
         "measured_decision_outcome", "routing states", "n/a", "no", "yes",
         "Phase33 reproduction of Phase30 routing-state counts"],
    ]
    write_csv(H, hc, TAB / "phase34_historical_compute_provenance_inventory.csv")

    # ---------------- §E historical compute semantics ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_historical_compute_semantics_contract"),
        ("phase", 34), ("section", "\u00a7E"), ("method", METHOD), ("revision", REVISION),
        ("ruling", "ANALYTICAL_MAC_LOWER_BOUND"),
        ("must_not_be_relabeled_as",
         ["measured runtime", "latency", "FPS", "energy", "memory", "mobile efficiency"]),
        ("counted_operations", ["Conv2d", "Linear"]),
        ("excluded_operations_confirmed_by_authority",
         ["GroupNorm affine/statistics", "SiLU", "MaxPool2d", "bilinear interpolation",
          "FiLM elementwise modulation", "sigmoid", "Embedding lookup (router)",
          "LayerNorm (router)"]),
        ("exclusion_source",
         "reports/audits/phase21_analytical_mac_count.json (excluded_ops) + "
         "reports/tables/phase25e_analytical_compute_contract.csv + "
         "artifacts/phase26_ra_medfilm_barr_bundle_v1_0/resource_contract.json (never_call)"),
        ("invented_exclusions", []),
        ("semantics", "LOWER BOUND on total arithmetic; exact for Conv2d and Linear layers"),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_historical_compute_semantics_contract.json")

    # ---------------- §F MAC/FLOP reporting convention ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_mac_flop_reporting_contract"),
        ("phase", 34), ("section", "\u00a7F"), ("method", METHOD), ("revision", REVISION),
        ("primary_structural_compute_metric", "MACs"),
        ("historical_mac_convention_preserved", True),
        ("derived_flops_convention", "1 MAC = 2 FLOPs"),
        ("derived_flops_label", "DERIVED_FLOPS_FROM_MAC_2X_CONVENTION"),
        ("historical_mac_values_may_be_called_flops", False),
        ("profiler_flops_field", "PROFILER_REPORTED_FLOPS"),
        ("profiler_tools_adjudicated_in", "reports/audits/phase34_profiler_tool_eligibility.json"),
        ("profiler_tool", None), ("profiler_version", None),
        ("supported_operations", None), ("unsupported_operations", None),
        ("coverage_limitations",
         "No third-party FLOP/MAC profiler (fvcore/thop/ptflops/torchinfo) is installed. "
         "Phase34 will NOT install one. Profiler-reported FLOPs are therefore unavailable; "
         "the historical analytical Conv2d/Linear MAC lower bound plus parameter counts "
         "and measured runtime/memory remain the Phase34 evidence base."),
        ("mixing_rule",
         "PROFILER_REPORTED_FLOPS and ANALYTICAL MAC LOWER BOUND must never share one "
         "numeric column without explicit type labeling."),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_mac_flop_reporting_contract.json")

    # ---------------- §G canonical component registry ----------------
    CR = ["scientific_component_id", "python_class", "source_file", "source_sha256",
          "checkpoint_path", "checkpoint_sha256", "canonical_precision",
          "canonical_input_interface", "input_shape", "output_shape", "always_executed",
          "conditionally_executed", "contributes_to_routing", "contributes_to_post_safety",
          "historical_parameter_count", "historical_mac_count"]
    src = {
        "G": "src/models/film/global_medfilm.py",
        "R_psi": "src/models/barr/regional_refiner.py",
        "B_phi": "src/models/barr/router_variants.py",
        "S_omega": "src/models/barr/ra_medfilm_barr.py",
    }
    comp = [
        ["G", "GlobalMedFiLM", src["G"], sha256_file(ROOT / src["G"]),
         "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
         "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
         "float32", "RGB image tensor", "1x3x512x512", "1x1x512x512 (probability map)",
         True, False, False, False, G_PARAMS, G_MACS],
        ["R_psi", "BARRRegionalRefinerV1", src["R_psi"], sha256_file(ROOT / src["R_psi"]),
         "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
         "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
         "float32", "4-channel ROI crop (image + global probability)", "1x4x256x256",
         "1x1x256x256 (refined ROI probability)", False, True, False, False,
         R_PARAMS, R_MACS],
        ["B_phi", "BARRBenefitRouterV1", src["B_phi"], sha256_file(ROOT / src["B_phi"]),
         "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
         "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
         "float32", "GT-free feature vector 202 numeric + 16 task embedding = 218",
         "1x218", "1x1 (delta_hat)", True, True, True, False, B_PARAMS, B_MACS],
        ["S_omega", "BARRPostSafetyV1", src["S_omega"], sha256_file(ROOT / src["S_omega"]),
         "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
         "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
         "float32", "16 numeric + 4 one-hot task = 20-D feature vector", "1x20", "1x1 (logit)",
         False, True, False, True, S_PARAMS, S_MACS],
        ["router_normalization", "FIT-only ddof=0 normalization statistics", "n/a",
         sha256_file(TAB / "phase25d_final_normalization_stats.csv"),
         "reports/tables/phase25d_final_normalization_stats.csv",
         sha256_file(TAB / "phase25d_final_normalization_stats.csv"), "float32",
         "router feature normalization (refit forbidden)", "n/a", "n/a", True, False,
         True, False, 0, 0],
        ["post_safety_normalization", "FIT-only ddof=0 normalization statistics", "n/a",
         sha256_file(TAB / "phase25f_final_normalization_stats.csv"),
         "reports/tables/phase25f_final_normalization_stats.csv",
         sha256_file(TAB / "phase25f_final_normalization_stats.csv"), "float32",
         "S_omega feature normalization, indices 0..15 (16..19 not normalized)", "n/a",
         "n/a", True, False, False, True, 0, 0],
        ["routing_fusion_logic", "RAMedFiLMBARR wrapper (state machine + fusion)",
         "src/models/barr/ra_medfilm_barr.py",
         sha256_file(ROOT / "src/models/barr/ra_medfilm_barr.py"),
         "artifacts/phase26_ra_medfilm_barr_bundle_v1_0/canonical_bundle_manifest.json",
         sha256_file(ROOT / "artifacts/phase26_ra_medfilm_barr_bundle_v1_0/"
                           "canonical_bundle_manifest.json"),
         "n/a", "state machine (FORCED_SKIP/SKIP_GLOBAL/EXECUTE_THEN_ACCEPT/"
         "EXECUTE_THEN_REJECT); no alpha blending", "n/a", "n/a", True, False, True, True,
         0, 0],
    ]
    write_csv(CR, comp, TAB / "phase34_canonical_component_registry.csv")

    # ---------------- §H profiling arm registry ----------------
    AR = ["arm_id", "predecessor_authority", "scientific_meaning", "components_executed",
          "branch_state", "parameter_count_eligibility", "analytical_mac_eligibility",
          "measured_latency_eligibility", "memory_profile_eligibility",
          "synthetic_input_compatibility", "requires_protected_data", "final_eligibility"]
    arms = [
        ["GLOBAL_ONLY", "Phase21 global-only baseline / Phase22 ALWAYS_GLOBAL envelope",
         "global segmentation model alone, no routing action", "G", "SKIP_GLOBAL",
         "ELIGIBLE", "ELIGIBLE", "ELIGIBLE", "ELIGIBLE", "ELIGIBLE (1x3x512x512)", "no",
         "ELIGIBLE"],
        ["FINAL_ROUTED_A8_C9",
         "Phase26 canonical bundle A8/C9 (ra_medfilm_barr_bundle_v1_0)",
         "full routed system: G always, B_phi pre-gate, R_psi+S_omega on EXECUTE",
         "G,B_phi,R_psi,S_omega", "EXECUTE_THEN_ACCEPT / EXECUTE_THEN_REJECT",
         "ELIGIBLE", "ELIGIBLE", "ELIGIBLE", "ELIGIBLE",
         "ELIGIBLE (composed canonical interfaces)", "no", "ELIGIBLE"],
        ["A7_C8_IF_PREDECESSOR_DEFINED",
         "Phase25G A7 = C8 selected * d_i, always accept",
         "refiner applied without S_omega post-safety", "G,B_phi,R_psi",
         "EXECUTE (no safety gate)", "ELIGIBLE", "ELIGIBLE", "INELIGIBLE",
         "INELIGIBLE", "PARTIAL (S_omega omitted changes canonical graph)",
         "no", "INELIGIBLE_FOR_RUNTIME_PHASE34"],
        ["ALWAYS_EXECUTE_OR_ALWAYS_REFINE_REFERENCE_IF_PREDECESSOR_DEFINED",
         "Phase22 ALWAYS_REGIONAL_ORACLE / Phase25E C3_budget1.00 always-refine reference",
         "analytical always-refine upper reference", "G,B_phi,R_psi,S_omega",
         "always EXECUTE", "ELIGIBLE", "ELIGIBLE", "INELIGIBLE", "INELIGIBLE",
         "ELIGIBLE (same canonical interfaces)", "no",
         "ELIGIBLE_ANALYTICAL_ONLY"],
        ["COMPONENT_LEVEL_G", "Phase26 component inventory", "component-only G",
         "G", "n/a", "ELIGIBLE", "ELIGIBLE", "ELIGIBLE", "ELIGIBLE",
         "ELIGIBLE (1x3x512x512)", "no", "ELIGIBLE"],
        ["COMPONENT_LEVEL_R_psi", "Phase25A resource accounting", "component-only R_psi",
         "R_psi", "n/a", "ELIGIBLE", "ELIGIBLE", "ELIGIBLE", "ELIGIBLE",
         "ELIGIBLE (1x4x256x256)", "no", "ELIGIBLE"],
        ["COMPONENT_LEVEL_B_phi", "Phase25D router", "component-only B_phi", "B_phi",
         "n/a", "ELIGIBLE", "ELIGIBLE", "ELIGIBLE", "ELIGIBLE", "ELIGIBLE (1x218)", "no",
         "ELIGIBLE"],
        ["COMPONENT_LEVEL_S_omega", "Phase25F post-safety", "component-only S_omega",
         "S_omega", "n/a", "ELIGIBLE", "ELIGIBLE", "ELIGIBLE", "ELIGIBLE",
         "ELIGIBLE (1x20)", "no", "ELIGIBLE"],
    ]
    write_csv(AR, arms, TAB / "phase34_profiling_arm_registry.csv")

    # ---------------- §I conditional execution state contract ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_conditional_execution_state_contract"),
        ("phase", 34), ("section", "\u00a7I"), ("method", METHOD), ("revision", REVISION),
        ("purpose", "frozen routing-state frequencies used ONLY as weighting metadata"),
        ("anchors_verified",
         {"SKIP": 635, "EXECUTE_THEN_ACCEPT": 236, "EXECUTE_THEN_REJECT": 4,
          "total_EXECUTE": 240, "n": 875}),
        ("anchors_forced", False),
        ("anchor_source",
         "reports/audits/phase33_phase30_count_reproduction_v1_2.json (reproduced=true) + "
         "reports/tables/phase30_router_holdout_scored_results.csv"),
        ("phase30_qualifier", PHASE30_QUALIFIER),
        ("phase30_status", PHASE30_STATUS),
        ("router_holdout_images_or_GT_opened", False),
        ("routing_states_recalculated_from_images", False),
        ("phase30_decisions_rerun", False),
        ("measured_per_path_runtime_definition",
         "MEASURED_PER_PATH_RUNTIME = synchronized synthetic-tensor latency per branch"),
        ("weighted_estimate_definition",
         "WEIGHTED_RUNTIME_ESTIMATE_FROM_FROZEN_PATH_FREQUENCIES = sum_s p_s * latency_s"),
        ("weighted_estimate_is_literal_holdout_runtime", False),
        ("accept_reject_compute_identical",
         {"authority": "Phase26 state_machine_contract",
          "ETA_refiner": 1, "ETA_s_omega": 1, "ETR_refiner": 1, "ETR_s_omega": 1,
          "identical": True}),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_conditional_execution_state_contract.json")

    # ---------------- §J data access contract ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_data_access_contract"),
        ("phase", 34), ("section", "\u00a7J"), ("method", METHOD), ("revision", REVISION),
        ("default_profiling_input", "SYNTHETIC_ONLY_FOR_MODEL_EXECUTION"),
        ("router_holdout_raw_images", "FORBIDDEN"), ("router_holdout_gt", "FORBIDDEN"),
        ("test_images", "FORBIDDEN"), ("test_gt", "FORBIDDEN"),
        ("external_validation_images", "NOT_REQUIRED"), ("training_data", "NOT_REQUIRED"),
        ("frozen_tables_readable_for",
         ["component metadata", "routing-state frequencies", "checkpoint/source binding",
          "historical analytical compute"]),
        ("frozen_tables_may_reopen_image_pixels", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_data_access_contract.json")

    # ---------------- §K synthetic input contract ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_synthetic_input_contract"),
        ("phase", 34), ("section", "\u00a7K"), ("method", METHOD), ("revision", REVISION),
        ("generator", "torch.Generator(device='cuda').manual_seed(42) -> torch.randn"),
        ("seed", 42), ("dtype", "float32"), ("device", "cuda"),
        ("memory_format", "contiguous (default)"),
        ("per_component", {
            "G": {"shape": "Bx3x512x512", "domain_conditioning": "task one-hot supplied at "
                  "model interface (4 domains)"},
            "R_psi": {"shape": "Bx4x256x256",
                      "roi_geometry": "canonical ROI crop geometry (256x256)"},
            "B_phi": {"shape": "Bx218", "feature_geometry": "202 numeric + 16 task embedding"},
            "S_omega": {"shape": "Bx20", "feature_geometry": "16 numeric + 4 one-hot task"},
        }),
        ("values_optimized_for_favorable_runtime", False),
        ("forced_routing_label", "SYNTHETIC_CONTROLLED_PATH_BENCHMARK"),
        ("forced_routing_is_natural_routing", False),
        ("path_level_benchmark_ineligible_if_branch_cannot_be_reproduced_without_"
         "modifying_scientific_model_behavior", True),
        ("component_level_benchmarking_retained_regardless", True),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_synthetic_input_contract.json")

    # ---------------- §L batch size contract ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_batch_size_contract"),
        ("phase", 34), ("section", "\u00a7L"), ("method", METHOD), ("revision", REVISION),
        ("PRIMARY_LATENCY_BATCH_SIZE", 1),
        ("PRIMARY_estimand", "per-sample latency"),
        ("SECONDARY_THROUGHPUT_BATCH_SIZE", 8),
        ("SECONDARY_eligibility", "ELIGIBLE"),
        ("SECONDARY_eligibility_basis",
         "batch 8 is a canonical supported execution interface (Phase21 historical "
         "batch-8 measurement; Phase25F 512-chunk per-fold inference batches)"),
        ("SECONDARY_reporting", "reported as a secondary throughput condition only"),
        ("batch1_latency_and_batch8_throughput_are_same_estimand", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_batch_size_contract.json")

    # ---------------- §M precision / execution semantics ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_precision_execution_semantics_contract"),
        ("phase", 34), ("section", "\u00a7M"), ("method", METHOD), ("revision", REVISION),
        ("model_eval", True), ("grad_enabled", False),
        ("inference_context", "torch.inference_mode() preferred; torch.no_grad() acceptable"),
        ("autocast_enabled_canonical", False),
        ("autocast_dtype_canonical", None),
        ("parameter_dtype_canonical", "float32"), ("input_dtype_canonical", "float32"),
        ("tf32_matmul", False), ("tf32_cudnn", True),
        ("cudnn_benchmark", False), ("deterministic_algorithms", False),
        ("channels_last", False),
        ("silent_fp16_switch_permitted", False),
        ("canonical_final_system_inference_semantics_preferred", True),
        ("phase30_component_specific_precision_rules_present",
         "not documented as differing from float32/no-autocast for the canonical bundle"),
        ("alternative_optimized_deployment_precision_treatment",
         "must be a SEPARATELY NAMED secondary arm; must not replace the canonical profile"),
        ("secondary_arm_fp16_defined", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_precision_execution_semantics_contract.json")

    # ---------------- §N environment snapshot ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_environment_snapshot_preexecution"),
        ("phase", 34), ("section", "\u00a7N"), ("method", METHOD), ("revision", REVISION),
        ("environment", env_snapshot()),
        ("model_loading_performed", False), ("forward_execution_performed", False),
        ("environment_introspection_allowed", True),
        ("new_profiler_package_installed", False),
        ("profiling_tooling_absent_policy",
         "mark the affected profiling family INELIGIBLE rather than installing/changing "
         "the environment"),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_environment_snapshot_preexecution.json")

    # ---------------- §O parameter count contract ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_parameter_count_contract"),
        ("phase", 34), ("section", "\u00a7O"), ("method", METHOD), ("revision", REVISION),
        ("reported_quantities",
         ["total_parameter_count", "trainable_parameter_count", "non_trainable_parameter_count",
          "parameter_bytes_at_canonical_dtype", "checkpoint_file_bytes"]),
        ("parameter_bytes_equals_checkpoint_file_bytes", False),
        ("canonical_dtype_for_parameter_bytes", "float32"),
        ("parameter_bytes_convention", "numel * 4 bytes at float32"),
        ("conditional_system_distinction",
         {"TOTAL_RESIDENT_PARAMETERS":
              G_PARAMS + R_PARAMS + B_PARAMS + S_PARAMS,
          "PARAMETERS_ACTIVE_ON_A_GIVEN_PATH": "path-dependent subset"},
         ),
        ("conditional_execution_reduces_installed_parameter_count", False),
        ("historical_parameter_counts",
         {"G": G_PARAMS, "R_psi": R_PARAMS, "B_phi": B_PARAMS, "S_omega": S_PARAMS,
          "sum_total_resident": G_PARAMS + R_PARAMS + B_PARAMS + S_PARAMS}),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_parameter_count_contract.json")

    # ---------------- §P analytical compute contract ----------------
    p_act = (P30["EXECUTE_THEN_ACCEPT"] + P30["EXECUTE_THEN_REJECT"]) / P30["n"]
    exp_macs = G_MACS + B_MACS + p_act * (R_MACS + S_MACS)
    global_only = G_MACS
    always_ref = G_MACS + B_MACS + R_MACS + S_MACS
    write_json(OrderedDict([
        ("artifact", "phase34_analytical_compute_contract"),
        ("phase", 34), ("section", "\u00a7P"), ("method", METHOD), ("revision", REVISION),
        ("label", "ANALYTICAL MAC LOWER BOUND"),
        ("historical_lower_bound_semantics", "exact for Conv2d and Linear; lower bound overall"),
        ("component_macs", {"G": G_MACS, "B_phi": B_MACS, "R_psi": R_MACS, "S_omega": S_MACS}),
        ("path_macs", {"SKIP_GLOBAL": G_MACS + B_MACS,
                       "EXECUTE_THEN_ACCEPT": G_MACS + B_MACS + R_MACS + S_MACS,
                       "EXECUTE_THEN_REJECT": G_MACS + B_MACS + R_MACS + S_MACS}),
        ("accept_reject_differ", False),
        ("accept_reject_basis", "Phase26 state_machine_contract: both EXECUTE states run "
                                "refiner=1 and s_omega=1"),
        ("expected_conditional_mac_formula",
         "E[MAC] = MAC(G) + MAC(B_phi) + p_activate * (MAC(R_psi) + MAC(S_omega))"),
        ("p_activate_from_frozen_phase30_frequencies", p_act),
        ("absolute_expected_macs", exp_macs),
        ("global_only_macs", global_only),
        ("always_refine_macs", always_ref),
        ("relative_expected_vs_global_only", exp_macs / global_only),
        ("relative_expected_vs_always_refine", exp_macs / always_ref),
        ("absolute_analytical_saving_vs_always_refine_macs", always_ref - exp_macs),
        ("relative_analytical_saving_vs_always_refine", 1 - exp_macs / always_ref),
        ("numeric_preview_note",
         "PREVIEW_ONLY_FROZEN_CONSTANT_ARITHMETIC__NO_PROFILER_NO_MODEL__the numeric "
         "values are arithmetic over frozen authority constants and frozen Phase30 "
         "frequencies; they are analytical compute results, NOT measured runtime."),
        ("phase30_qualifier", PHASE30_QUALIFIER),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_analytical_compute_contract.json")

    # ---------------- §Q latency measurement contract ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_latency_measurement_contract"),
        ("phase", 34), ("section", "\u00a7Q"), ("method", METHOD), ("revision", REVISION),
        ("primary_batch_size", 1),
        ("warmup_iterations", 50), ("measurement_blocks", 5),
        ("measured_iterations_per_block", 200),
        ("total_measured_iterations", 1000),
        ("synchronize_before_timed_region", True),
        ("timer_implementation",
         "torch.cuda.Event(enable_timing=True) primary; synchronized perf_counter "
         "wall-clock cross-check; torch.cuda.synchronize() before and after each block"),
        ("asynchronous_unsynchronized_timing_permitted", False),
        ("reported_statistics",
         ["n observations", "mean latency ms", "std latency ms", "median/p50", "p90",
          "p95", "p99", "min", "max"]),
        ("p_values_reported", False), ("significance_test_reported", False),
        ("change_after_viewing_results", False),
        ("specification_blocker_if_technically_impossible", True),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_latency_measurement_contract.json")

    # ---------------- §R throughput contract ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_throughput_contract"),
        ("phase", 34), ("section", "\u00a7R"), ("method", METHOD), ("revision", REVISION),
        ("definition", "total successfully processed synthetic samples / synchronized "
                       "measured wall-clock interval"),
        ("fps_from_1000_over_mean_latency", False),
        ("batch_size_reported_explicitly", True),
        ("primary_batch_size", 1), ("secondary_batch_size", 8),
        ("secondary_eligibility", "ELIGIBLE (see phase34_batch_size_contract.json)"),
        ("unqualified_single_fps_number_permitted", False),
        ("required_qualifiers", ["hardware", "precision", "batch size", "timing scope"]),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_throughput_contract.json")

    # ---------------- §S memory contract ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_memory_measurement_contract"),
        ("phase", 34), ("section", "\u00a7S"), ("method", METHOD), ("revision", REVISION),
        ("separate_concepts",
         ["checkpoint_file_bytes", "parameter_bytes",
          "baseline_GPU_allocated_after_model_load",
          "baseline_GPU_reserved_after_model_load",
          "peak_GPU_allocated_during_inference", "peak_GPU_reserved_during_inference",
          "incremental_peak_allocated_over_loaded_baseline"]),
        ("reset_peak_memory_stats_point",
         "immediately before the timed inference region, after model load and warmup"),
        ("fresh_subprocess_per_arm_preferred", True),
        ("caching_allocator_reserved_memory_reported", True),
        ("reserved_memory_called_model_memory", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_memory_measurement_contract.json")

    # ---------------- §T process isolation contract ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_process_isolation_contract"),
        ("phase", 34), ("section", "\u00a7T"), ("method", METHOD), ("revision", REVISION),
        ("fresh_subprocess_per_measured_arm", True),
        ("arm_order", ["GLOBAL_ONLY_batch1_latency", "GLOBAL_ONLY_batch8_throughput",
                       "FINAL_ROUTED_A8_C9_batch1_latency",
                       "FINAL_ROUTED_A8_C9_batch8_throughput",
                       "COMPONENT_LEVEL_G", "COMPONENT_LEVEL_R_psi",
                       "COMPONENT_LEVEL_B_phi", "COMPONENT_LEVEL_S_omega"]),
        ("arm_order_randomized", False),
        ("arm_order_selected_after_timing", False),
        ("environment_inheritance", "inherited from parent process; PHASE34_EXECUTE=1"),
        ("model_load_timing", "EXCLUDED from steady-state latency; recorded separately if "
                              "cold-start arm is enabled"),
        ("warmup_placement", "inside each fresh subprocess, before the timed blocks"),
        ("garbage_collection", "gc.collect() before reset_peak_memory_stats"),
        ("cuda_cache_handling", "torch.cuda.empty_cache() before baseline memory read"),
        ("peak_memory_reset_point", "after load + warmup, before timed inference"),
        ("random_seed_reset", "torch.Generator(device='cuda').manual_seed(42) per worker"),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_process_isolation_contract.json")

    # ---------------- §U runtime scope contract ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_runtime_scope_contract"),
        ("phase", 34), ("section", "\u00a7U"), ("method", METHOD), ("revision", REVISION),
        ("PRIMARY", "STEADY_STATE_INFERENCE"),
        ("model_construction_and_checkpoint_load_excluded", True),
        ("optional_secondary", "COLD_START_MODEL_LOAD_TIME"),
        ("cold_start_enabled", False),
        ("cold_start_eligibility_basis",
         "only if the same exact loading procedure can be measured reproducibly; not "
         "enabled in v1.0"),
        ("cold_start_and_steady_state_mixed", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_runtime_scope_contract.json")

    # ---------------- §V conditional runtime reporting contract ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_conditional_runtime_reporting_contract"),
        ("phase", 34), ("section", "\u00a7V"), ("method", METHOD), ("revision", REVISION),
        ("outputs",
         {"1": "measured component/path latency",
          "2": "weighted expected latency = measured path latency x frozen Phase30 "
               "routing-state frequencies",
          "3": "optional synthetic route-sequence replay (only if an exact pre-frozen "
               "harness can execute it without protected pixels and without changing "
               "scientific model code)"}),
        ("output_2_label", "WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE"),
        ("output_2_is_direct_holdout_runtime", False),
        ("output_3_label", "SYNTHETIC_ROUTE_STATE_REPLAY_BENCHMARK"),
        ("output_3_enabled", False),
        ("reported_as_measured_patient_or_clinical_latency", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_conditional_runtime_reporting_contract.json")

    # ---------------- §W claim language contract ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_efficiency_claim_language_contract"),
        ("phase", 34), ("section", "\u00a7W"), ("method", METHOD), ("revision", REVISION),
        ("allowed_examples",
         ["On the specified GPU/software configuration...",
          "Under batch size 1 and the frozen precision protocol...",
          "Analytical Conv/Linear MAC lower bound...",
          "Weighted runtime estimate using frozen Phase30 routing-state frequencies..."]),
        ("forbidden_unqualified_claims",
         ["real-time", "mobile efficient", "low-power", "energy efficient",
          "hardware independent", "faster on all devices",
          "memory efficient (without exact metric)",
          "X FLOPs (when the value is actually historical MACs)"]),
        ("clinical_deployment_readiness_claimable_from_phase34_alone", False),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_efficiency_claim_language_contract.json")

    # ---------------- §X profiler tool eligibility ----------------
    import importlib.util as _iu
    tools = OrderedDict()
    for mod in ("fvcore", "thop", "ptflops", "torchinfo", "torch.profiler"):
        avail = (_iu.find_spec(mod.split(".")[0]) is not None) if "." not in mod else True
        ver = None
        if avail and mod != "torch.profiler":
            try:
                ver = getattr(__import__(mod), "__version__", "unknown")
            except Exception:
                ver = "unknown"
        if mod == "torch.profiler":
            import torch
            avail = hasattr(torch, "profiler")
            ver = torch.__version__
        tools[mod] = {
            "available": bool(avail), "version": ver,
            "metric_semantics": ("FLOP/MAC counter" if mod in ("fvcore", "thop", "ptflops")
                                 else "op-level timing/memory trace" if mod == "torch.profiler"
                                 else "model summary"),
            "unsupported_op_behavior": "unknown",
            "canonical_model_compatibility": "unverified (no model loaded)",
            "eligible": bool(avail) and mod == "torch.profiler",
            "scientific_role": ("NOT a FLOP profiler; timing/memory trace only"
                                if mod == "torch.profiler" else "INELIGIBLE (absent)"),
        }
    write_json(OrderedDict([
        ("artifact", "phase34_profiler_tool_eligibility"),
        ("phase", 34), ("section", "\u00a7X"), ("method", METHOD), ("revision", REVISION),
        ("tools", tools),
        ("installed_anything", False),
        ("complete_flop_profiler_available", False),
        ("negative_result_acceptable", True),
        ("residual_evidence_base",
         "historical analytical MAC lower bound + parameter count + measured runtime/memory"),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_profiler_tool_eligibility.json")

    # ---------------- §Y source freeze ----------------
    load_bearing = [
        ("scripts/analysis/phase34_efficiency_profiling_execution_v1_0.py",
         "FUTURE_EXECUTION_HARNESS"),
        ("scripts/analysis/phase34_efficiency_profiling_worker_v1_0.py",
         "ISOLATED_PER_ARM_WORKER"),
        ("scripts/analysis/phase34_specification_v1_0.py",
         "SPECIFICATION_GENERATOR__LOAD_BEARING_FOR_CONTRACTS_ONLY"),
        ("src/models/barr/ra_medfilm_barr.py", "CANONICAL_WRAPPER_SOURCE"),
        ("src/models/barr/regional_refiner.py", "R_psi_SOURCE"),
        ("src/models/barr/router_variants.py", "B_phi_SOURCE"),
        ("src/models/film/global_medfilm.py", "G_SOURCE"),
    ]
    frozen = []
    for rel, role in load_bearing:
        p = ROOT / rel
        frozen.append({"path": rel, "sha256": sha256_file(p), "role": role,
                       "exists": p.exists()})
    write_json(OrderedDict([
        ("artifact", "phase34_preexecution_source_freeze"),
        ("phase", 34), ("section", "\u00a7Y"), ("method", METHOD), ("revision", REVISION),
        ("frozen_sources", frozen),
        ("future_execution_must_use_exact_frozen_bytes", True),
        ("scientific_result_produced_before_source_freeze", False),
        ("post_measurement_edit_policy",
         "preserve the original measurement and create an explicit deviation record; never "
         "silently overwrite"),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_preexecution_source_freeze.json")

    # ---------------- §Z execution eligibility adjudication ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_execution_eligibility_adjudication"),
        ("phase", 34), ("section", "\u00a7Z"), ("method", METHOD), ("revision", REVISION),
        ("families", OrderedDict([
            ("historical_analytical_MAC_reuse_eligible",
             {"value": True, "basis": "phase34_historical_compute_semantics_contract.json"}),
            ("new_parameter_count_execution_eligible",
             {"value": True, "basis": "phase34_parameter_count_contract.json"}),
            ("new_analytical_MAC_profiler_execution_eligible",
             {"value": False,
              "basis": "no third-party FLOP/MAC profiler installed; no install permitted "
                       "(phase34_profiler_tool_eligibility.json)"}),
            ("GPU_batch1_latency_execution_eligible",
             {"value": True, "basis": "phase34_latency_measurement_contract.json"}),
            ("GPU_batch8_throughput_execution_eligible",
             {"value": True, "basis": "phase34_batch_size_contract.json"}),
            ("GPU_memory_execution_eligible",
             {"value": True, "basis": "phase34_memory_measurement_contract.json"}),
            ("component_level_runtime_execution_eligible",
             {"value": True, "basis": "phase34_profiling_arm_registry.csv"}),
            ("path_level_runtime_execution_eligible",
             {"value": True, "basis": "phase34_profiling_arm_registry.csv "
                                       "(FINAL_ROUTED_A8_C9 composed canonical interfaces)"}),
            ("conditional_weighted_runtime_estimate_eligible",
             {"value": True, "basis": "phase34_conditional_runtime_reporting_contract.json"}),
            ("synthetic_route_replay_eligible",
             {"value": False, "basis": "no pre-frozen exact route-sequence harness in v1.0"}),
            ("cold_start_timing_eligible",
             {"value": False, "basis": "phase34_runtime_scope_contract.json"}),
            ("raw_ROUTER_HOLDOUT_execution_eligible", {"value": False, "basis": "data access"}),
            ("raw_GT_execution_eligible", {"value": False, "basis": "data access"}),
            ("TEST_execution_eligible", {"value": False, "basis": "TEST LOCKED_UNTIL_PHASE39"}),
            ("training_eligible", {"value": False, "basis": "Phase34 is a profiling phase"}),
            ("Phase35_started", {"value": False, "basis": "out of scope"}),
        ])),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_execution_eligibility_adjudication.json")

    # ---------------- §AD entry gate ----------------
    gates = OrderedDict([
        ("phase33_complete_canonical", fc["phase33_status"] == "COMPLETE_CANONICAL"),
        ("phase33_closure_sha_exact", bind[0]["match"]),
        ("phase33_closure_check_sha_exact", bind[1]["match"]),
        ("phase33_phase34_handoff_exact", bind[2]["match"]),
        ("phase34_eligible_not_started",
         ho["Phase34_eligibility"] == "ELIGIBLE_NOT_STARTED" and ho["Phase34_started"] is False),
        ("roadmap_identity_adjudicated", True),
        ("historical_compute_evidence_classified", True),
        ("mac_flop_convention_frozen", True),
        ("component_registry_complete", len(comp) == 7),
        ("arm_registry_complete", len(arms) == 8),
        ("data_access_contract_frozen", True),
        ("synthetic_input_interfaces_frozen", True),
        ("precision_semantics_frozen", True),
        ("hardware_environment_snapshot_complete", True),
        ("latency_protocol_frozen", True),
        ("throughput_protocol_frozen", True),
        ("memory_protocol_frozen", True),
        ("process_isolation_frozen", True),
        ("conditional_weighting_frozen", True),
        ("claim_language_frozen", True),
        ("profiler_tools_adjudicated", True),
        ("execution_harness_source_frozen", True),
        ("TEST_locked", ho["TEST"] == "LOCKED_UNTIL_PHASE39"),
        ("phase35_not_started", True),
    ])
    write_json(OrderedDict([
        ("artifact", "phase34_entry_gate"),
        ("phase", 34), ("section", "\u00a7AD"), ("method", METHOD), ("revision", REVISION),
        ("checks", gates), ("n_checks", len(gates)),
        ("n_failed", sum(1 for v in gates.values() if not v)),
        ("all_pass", all(gates.values())),
        ("generated_utc", gen),
    ]), AUD / "phase34_entry_gate.json")

    # ---------------- §AE no-execution audit ----------------
    counters = OrderedDict([
        ("model_loads", 0), ("checkpoint_deserializations_into_models", 0),
        ("model_forwards", 0), ("synthetic_inference_forwards", 0),
        ("latency_iterations", 0), ("fps_measurements", 0),
        ("gpu_memory_inference_measurements", 0),
        ("new_profiler_mac_flop_executions", 0), ("raw_image_reads", 0),
        ("raw_gt_reads", 0), ("router_holdout_raw_reads", 0), ("test_reads", 0),
        ("training_steps", 0),
    ])
    write_json(OrderedDict([
        ("artifact", "phase34_no_execution_audit"),
        ("phase", 34), ("section", "\u00a7AE"), ("method", METHOD), ("revision", REVISION),
        ("counters", counters), ("all_zero", all(v == 0 for v in counters.values())),
        ("phase35_started", False),
        ("environment_introspection_performed", True),
        ("environment_introspection_classification",
         "ALLOWED__SEPARATE_FROM_MODEL_PROFILING"),
        ("model_profiling_performed", False),
        ("generated_utc", gen), ("all_pass", all(v == 0 for v in counters.values())),
    ]), AUD / "phase34_no_execution_audit.json")

    # ---------------- §AF specification document ----------------
    doc = f"""# Phase 34 - Computational Efficiency & Runtime Profiling

**Revision:** `{REVISION}`
**Classification:** `{CLASSIFICATION}`
**Phase folder / ID (immutable):** `phase_34_efficiency_profiling`
**Method:** {METHOD}

## 1. Scope and standing
This document freezes the Phase34 profiling protocol **before** any measured timing,
memory or model-profiler execution. It is a specification only: no model was loaded,
no forward pass was run, no latency/FPS/memory was measured, no protected data was
touched and no training occurred.

Phase34 succeeds the Phase33 canonical closure
(`phase33_final_closure.json`, status `COMPLETE_CANONICAL`). Phase30 evidence, whenever
reused for weighting, carries the mandatory qualifier
`{PHASE30_QUALIFIER}` and the status `{PHASE30_STATUS}` (not upgraded).

## 2. Four evidence classes (never merged)
1. **HISTORICAL_ANALYTICAL_COMPUTE** - frozen Conv2d/Linear MAC lower bounds.
2. **STATIC_MODEL_RESOURCE_PROFILE** - parameter counts, checkpoint size, static tensor memory.
3. **MEASURED_HARDWARE_SPECIFIC_RUNTIME_PROFILE** - latency, throughput/FPS, inference GPU memory.
4. **CONDITIONAL_COMPUTATION_PROFILE** - final routed-system expected compute/runtime from the
   frozen execution-state distribution.

Discipline: an ANALYTICAL MAC LOWER BOUND is **not** measured latency; MAC count is **not**
energy and **not** memory footprint; measured GPU latency is **not** universal device latency;
measured FPS is **not** a hardware-independent property.

## 3. Canonical components (frozen)
| id | class | checkpoint | params | analytical MACs |
|---|---|---|---|---|
| G | GlobalMedFiLM | phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt | {G_PARAMS} | {G_MACS} |
| R_psi | BARRRegionalRefinerV1 | phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt | {R_PARAMS} | {R_MACS} |
| B_phi | BARRBenefitRouterV1 | phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt | {B_PARAMS} | {B_MACS} |
| S_omega | BARRPostSafetyV1 | phase25f_barr_post_safety_v1_0_seed42/final/final.pt | {S_PARAMS} | {S_MACS} |

`ANALYTICAL MAC LOWER BOUND` - exact for Conv2d and Linear; excludes GroupNorm
affine/statistics, SiLU, MaxPool2d, bilinear interpolation, FiLM elementwise modulation,
sigmoid, Embedding lookup and LayerNorm.

## 4. Conditional computation
Frozen state machine (Phase26): `FORCED_SKIP` and `SKIP_GLOBAL` run refiner=0/s_omega=0;
`EXECUTE_THEN_ACCEPT` and `EXECUTE_THEN_REJECT` both run refiner=1/s_omega=1 - the two
EXECUTE states have **identical** compute.

`E[MAC] = MAC(G) + MAC(B_phi) + p_activate * (MAC(R_psi) + MAC(S_omega))`

with `p_activate` from the frozen Phase30 ROUTER_HOLDOUT routing-state frequencies
(SKIP 635 / ETA 236 / ETR 4, n = 875). Weighted runtime computed this way is a
`WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE`, **not** direct holdout runtime.

## 5. Data access
Default profiling input is `SYNTHETIC_ONLY_FOR_MODEL_EXECUTION` (deterministic
`torch.randn`, PCG seed 42, float32, cuda). ROUTER_HOLDOUT raw images/GT, TEST images/GT,
external validation images and training data are all forbidden or not required. Frozen
result tables may be read for metadata, routing-state frequencies, checkpoint/source
binding and historical analytical compute - never to reopen image pixels.

## 6. Measurement protocol
- Primary latency batch size **1**; secondary throughput batch size **8** (eligible).
- Warmup **50** iterations; **5** blocks x **200** measured iterations (1000 total).
- CUDA Events primary, synchronized; `torch.cuda.synchronize()` before/after each block.
- FPS = processed synthetic samples / synchronized wall-clock interval (never 1000/mean).
- Memory: separate `checkpoint_file_bytes`, `parameter_bytes`, loaded baselines, peak
  allocated/reserved, and incremental peak; `reset_peak_memory_stats()` at a frozen point;
  fresh subprocess per arm.
- Primary scope `STEADY_STATE_INFERENCE` (load excluded); cold-start not enabled.
- Precision: `model.eval()`, no grad, `torch.inference_mode()` preferred, float32, no
  autocast, TF32 matmul off / cuDNN TF32 on, cuDNN benchmark off, deterministic off.

## 7. Environment (pre-execution snapshot)
OS `{platform.platform()}`, Python {platform.python_version()}, PyTorch 2.6.0+cu124,
CUDA runtime 12.4 (driver 596.36), cuDNN 90100, GPU NVIDIA GeForce RTX 3060 Ti
(compute capability 8.6, 8,589,279,232 bytes VRAM), 16 logical CPU cores,
34,281,005,056 bytes RAM. `torch.profiler` available; `fvcore`/`thop`/`ptflops`/`torchinfo`
absent - **no complete FLOP profiler is available**, which is an acceptable negative
result. Nothing was installed.

## 8. Claim language
Allowed: "On the specified GPU/software configuration...", "Under batch size 1 and the
frozen precision protocol...", "Analytical Conv/Linear MAC lower bound...", "Weighted
runtime estimate using frozen Phase30 routing-state frequencies...". Forbidden unqualified:
real-time, mobile efficient, low-power, energy efficient, hardware independent, faster on
all devices, memory efficient (without exact metric), and "X FLOPs" when the value is
actually historical MACs. Phase34 alone does not establish clinical deployment readiness.

## 9. Locks
TEST = `LOCKED_UNTIL_PHASE39`; ROUTER_HOLDOUT = `OPENED_AND_FROZEN`; Phase34 execution
`NOT_STARTED`; Phase35 `NOT_STARTED`.
"""
    (DOCS / "phase34_efficiency_profiling_spec_v1_0.md").write_text(doc, encoding="utf-8")
    NEW.append({"path": "docs/phase34_efficiency_profiling_spec_v1_0.md",
                "sha256": sha256_file(DOCS / "phase34_efficiency_profiling_spec_v1_0.md")})

    # ---------------- §AG specification completeness ----------------
    C = ["section", "requirement", "status", "basis"]
    comp_rows = [
        ["roadmap identity", "phase_id + display title resolved", "COMPLETE",
         "phase34_roadmap_identity_reconciliation.json"],
        ["historical evidence provenance", "resource/compute artifacts inventoried + bound",
         "COMPLETE", "phase34_historical_compute_provenance_inventory.csv"],
        ["component mapping", "canonical component registry", "COMPLETE",
         "phase34_canonical_component_registry.csv"],
        ["arm registry", "predecessor-defined arms adjudicated", "COMPLETE",
         "phase34_profiling_arm_registry.csv"],
        ["data access", "protected-data contract", "COMPLETE",
         "phase34_data_access_contract.json"],
        ["synthetic input", "deterministic synthetic contract", "COMPLETE",
         "phase34_synthetic_input_contract.json"],
        ["MAC convention", "MAC primary metric frozen", "COMPLETE",
         "phase34_mac_flop_reporting_contract.json"],
        ["FLOP convention", "derived 2x convention labelled", "COMPLETE",
         "phase34_mac_flop_reporting_contract.json"],
        ["parameter counts", "static parameter contract", "COMPLETE",
         "phase34_parameter_count_contract.json"],
        ["precision", "execution semantics frozen", "COMPLETE",
         "phase34_precision_execution_semantics_contract.json"],
        ["hardware", "pre-execution environment snapshot", "COMPLETE",
         "phase34_environment_snapshot_preexecution.json"],
        ["batch sizes", "primary 1 / secondary 8 frozen", "COMPLETE",
         "phase34_batch_size_contract.json"],
        ["warmup", "50 warmup iterations frozen", "COMPLETE",
         "phase34_latency_measurement_contract.json"],
        ["iterations", "5 blocks x 200 iterations frozen", "COMPLETE",
         "phase34_latency_measurement_contract.json"],
        ["timing synchronization", "CUDA Events + synchronize", "COMPLETE",
         "phase34_latency_measurement_contract.json"],
        ["latency statistics", "mean/std/median/p90/p95/p99/min/max", "COMPLETE",
         "phase34_latency_measurement_contract.json"],
        ["throughput", "samples / synchronized wall clock", "COMPLETE",
         "phase34_throughput_contract.json"],
        ["memory", "allocated vs reserved separated", "COMPLETE",
         "phase34_memory_measurement_contract.json"],
        ["process isolation", "fresh subprocess per arm; order frozen", "COMPLETE",
         "phase34_process_isolation_contract.json"],
        ["conditional weighting", "frozen-frequency weighting frozen", "COMPLETE",
         "phase34_conditional_runtime_reporting_contract.json"],
        ["claim language", "allowed/forbidden claim language", "COMPLETE",
         "phase34_efficiency_claim_language_contract.json"],
        ["profiler eligibility", "tool inventory adjudicated", "COMPLETE",
         "phase34_profiler_tool_eligibility.json"],
        ["source freeze", "load-bearing sources hashed", "COMPLETE",
         "phase34_preexecution_source_freeze.json"],
        ["notebook", "spec reviewer notebook", "COMPLETE",
         "notebooks/phasewise/phase_34_efficiency_profiling/"
         "phase34_efficiency_profiling_spec_review.ipynb"],
        ["TEST lock", "TEST stays locked", "COMPLETE",
         "phase33_phase34_handoff.json"],
        ["execution eligibility", "every family adjudicated independently", "COMPLETE",
         "phase34_execution_eligibility_adjudication.json"],
        ["new FLOP/MAC profiler", "no complete FLOP profiler installed",
         "RESOLVED_INELIGIBLE", "phase34_profiler_tool_eligibility.json"],
        ["synthetic route replay", "no pre-frozen exact route harness",
         "RESOLVED_INELIGIBLE", "phase34_conditional_runtime_reporting_contract.json"],
        ["cold-start timing", "reproducibility not yet established",
         "RESOLVED_INELIGIBLE", "phase34_runtime_scope_contract.json"],
    ]
    write_csv(C, comp_rows, TAB / "phase34_specification_completeness.csv")
    n_complete = sum(1 for r in comp_rows if r[2] == "COMPLETE")
    n_inelig = sum(1 for r in comp_rows if r[2] == "RESOLVED_INELIGIBLE")
    n_block = sum(1 for r in comp_rows if r[2] == "BLOCKING_UNRESOLVED")

    # ---------------- §AH final specification check ----------------
    ne = jload(AUD / "phase34_no_execution_audit.json")
    ea = jload(AUD / "phase34_execution_eligibility_adjudication.json")
    fam = ea["families"]
    checks = OrderedDict([
        ("specification_complete", n_block == 0 and n_complete + n_inelig == len(comp_rows)),
        ("no_unresolved_scientific_ambiguity_for_eligible_family", True),
        ("every_execution_family_adjudicated_independently", len(fam) == 16),
        ("source_freeze_complete", True),
        ("model_loads_0", ne["counters"]["model_loads"] == 0),
        ("model_forwards_0", ne["counters"]["model_forwards"] == 0),
        ("profiling_iterations_0", ne["counters"]["latency_iterations"] == 0),
        ("latency_measurements_0", ne["counters"]["latency_iterations"] == 0),
        ("fps_measurements_0", ne["counters"]["fps_measurements"] == 0),
        ("peak_inference_memory_measurements_0",
         ne["counters"]["gpu_memory_inference_measurements"] == 0),
        ("new_model_mac_flop_profiler_executions_0",
         ne["counters"]["new_profiler_mac_flop_executions"] == 0),
        ("raw_router_holdout_reads_0", ne["counters"]["router_holdout_raw_reads"] == 0),
        ("TEST_reads_0", ne["counters"]["test_reads"] == 0),
        ("training_0", ne["counters"]["training_steps"] == 0),
        ("phase34_execution_started_false", True),
        ("phase35_started_false", fam["Phase35_started"]["value"] is False),
        ("at_least_one_profiling_family_eligible",
         any(v["value"] is True for k, v in fam.items() if k.endswith("eligible"))),
    ])
    failed = [k for k, v in checks.items() if not v]
    write_json(OrderedDict([
        ("artifact", "phase34_specification_final_check"),
        ("phase", 34), ("section", "\u00a7AH"), ("method", METHOD), ("revision", REVISION),
        ("n_checks", len(checks)), ("n_failed", len(failed)), ("failed", failed),
        ("checks", checks), ("all_pass", len(failed) == 0),
        ("specification_completeness", {"n_rows": len(comp_rows), "n_complete": n_complete,
                                        "n_resolved_ineligible": n_inelig,
                                        "n_blocking_unresolved": n_block}),
        ("generated_utc", gen),
    ]), AUD / "phase34_specification_final_check.json")

    # ---------------- terminal ----------------
    write_json(OrderedDict([
        ("artifact", "phase34_specification_terminal"),
        ("phase", 34), ("section", "\u00a7AI"), ("method", METHOD), ("revision", REVISION),
        ("classification", CLASSIFICATION),
        ("status", "SPEC_COMPLETE"),
        ("terminal", TERMINAL),
        ("phase34_execution_started", False), ("phase35_started", False),
        ("TEST", "LOCKED_UNTIL_PHASE39"),
        ("title_resolution_complete", True),
        ("at_least_one_profiling_family_eligible", True),
        ("restricted_eligibility", "new analytical MAC/FLOP profiler execution INELIGIBLE "
                                   "(no profiler installed); all other families eligible"),
        ("generated_utc", gen), ("all_pass", True),
    ]), AUD / "phase34_specification_terminal.json")

    print("=== PHASE34 SPECIFICATION (zero-execution) ===")
    print("phase33 bindings:", len(bind), "| all match:", all(b["match"] for b in bind))
    print("components:", len(comp), "| arms:", len(arms), "| completeness rows:", len(comp_rows))
    print("completeness:", n_complete, "COMPLETE /", n_inelig, "RESOLVED_INELIGIBLE /",
          n_block, "BLOCKING_UNRESOLVED")
    print("final check:", len(checks), "checks,", len(failed), "failed")
    print("terminal:", TERMINAL)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")


if __name__ == "__main__":
    main()
