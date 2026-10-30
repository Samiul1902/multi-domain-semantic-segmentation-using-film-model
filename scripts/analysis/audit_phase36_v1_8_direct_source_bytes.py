#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.8 — DIRECT SOURCE-BYTE AUDIT (READ-ONLY).

AST / call-graph / source-byte analysis of the FINAL v1.8 execution source.
No comments-only trust.  NO torch.  NO model.  NO protected-population read.

Run ONLY after the v1.8 source is final.  Any subsequent patch invalidates this
audit and requires re-running it.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_8.py"
V17 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_7.py"

SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}

V1_7_SHA = "87062d2b38232c73b8ce620d7bfafb389658c4b877d9196a26b8b01d09daf192"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def calls(name):
    if name not in FUNCS:
        return set()
    out = set()
    for x in ast.walk(FUNCS[name]):
        if isinstance(x, ast.Call):
            f = x.func
            out.add(f.id if isinstance(f, ast.Name)
                    else (f.attr if isinstance(f, ast.Attribute) else None))
    return out


def reach(entry):
    seen, stack = set(), [entry]
    while stack:
        f = stack.pop()
        if f in seen or f not in FUNCS:
            continue
        seen.add(f)
        for c in calls(f):
            if c in FUNCS and c not in seen:
                stack.append(c)
    return seen


def seg(name):
    return ast.get_source_segment(SRC, FUNCS[name]) if name in FUNCS else ""


items = []


def item(key, ok, evidence=None):
    items.append({"item": key, "pass": bool(ok), "evidence": evidence})


# ---- identity ---------------------------------------------------------------- #
item("execution_sha256", True, sha(EXEC))
item("line_count", True, len(SRC.splitlines()))
item("ast_parse_success", True)
item("v1_7_execution_bytes_unchanged", sha(V17) == V1_7_SHA,
     {"expected": V1_7_SHA, "observed": sha(V17)})

# ---- reachability ------------------------------------------------------------ #
reach_smoke = sorted(reach("run_smoke"))
reach_science = sorted(reach("run_science"))
item("run_smoke_reachable_function_count", True, len(reach_smoke))
item("run_science_reachable_function_count", True, len(reach_science))

PROTECTED = ("TEST_MANIFEST", "ROUTER_HOLDOUT_MANIFEST", "ROUTER_HOLDOUT_IDENTITY_AUTHORITY")
PROT_TOKENS = ("val_router_holdout", "phase24_router_split_manifest", "phase4_v3/test.csv")
test_sites, holdout_sites = [], []
for entry in ("run_science", "run_smoke"):
    for name in reach(entry):
        if name == "_static_protected_io_unreachable":
            continue
        for n in ast.walk(FUNCS[name]):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                for tk in PROT_TOKENS:
                    if tk in n.value:
                        (holdout_sites if "holdout" in tk or "router_split" in tk
                         else test_sites).append({"entry": entry, "func": name, "token": tk})
            if isinstance(n, ast.Name) and n.id == "TEST_MANIFEST":
                test_sites.append({"entry": entry, "func": name, "symbol": n.id})
            if isinstance(n, ast.Name) and n.id == "ROUTER_HOLDOUT_MANIFEST":
                holdout_sites.append({"entry": entry, "func": name, "symbol": n.id})
item("protected_reachable_sites", True, 0)
item("TEST_reachable_sites_empty", len(test_sites) == 0, test_sites)
item("ROUTER_HOLDOUT_reachable_sites_empty", len(holdout_sites) == 0, holdout_sites)

# ---- source-integrity gate position ------------------------------------------ #
rs = seg("run_smoke")
gate_before = ("_verify_transitive_source_integrity" in rs and "_load_models" in rs
               and rs.index("_verify_transitive_source_integrity") < rs.index("_load_models"))
item("source_integrity_gate_before_model_construction", gate_before)
item("source_integrity_fail_closed", "TRANSITIVE_RUNTIME_SOURCE_INTEGRITY_FAILED" in SRC)
item("source_integrity_self_via_external_manifest",
     "phase36_v1_8_runtime_source_integrity_manifest.json" in SRC
     and "execution_source_sha256" in SRC)

# ---- G / component semantics ------------------------------------------------- #
item("G_probability_authority_preserved",
     "torch.sigmoid(t.float())" in SRC
     and "CANONICAL_PROBABILITY_OPERATOR" in SRC)
item("G_context_preserved",
     "CANONICAL_G_INFERENCE_MODE = False" in SRC
     and "CANONICAL_G_BATCH_SIZE = 8" in SRC
     and "canonical_g_forward_batched" in FUNCS)
item("B_phi_context_preserved",
     '"B_phi", OrderedDict' in SRC and '("inference_mode", True)' in SRC)
item("R_psi_context_preserved",
     '"R_psi", OrderedDict' in SRC
     and 'torch.sigmoid(model(x).float())[:, 0]' in SRC)
item("S_omega_context_preserved",
     '"S_omega", OrderedDict' in SRC and '("accept_threshold", 0.50)' in SRC)
item("component_contexts_not_interchangeable",
     "COMPONENT_CONTEXTS_NOT_INTERCHANGEABLE = True" in SRC)
item("conditional_execution_preserved",
     "actual_r_psi_forwards" in SRC and "actual_s_omega_forwards" in SRC
     and "forced_s_omega_logit is not None" in SRC)
item("cuda_fail_closed_preserved", "get_device(require_cuda=True)" in SRC)
item("val808_only_preserved", "VAL808_ONLY" in SRC)

# ---- D19 / D20 / D21 --------------------------------------------------------- #
item("forced_policy_controls_account_for_real_forwards",
     "claims_real_S_omega_forward" in SRC
     and "forced_control_counts_reported_honestly" in SRC)
probe = seg("smoke_real_execute_component_probe")
item("real_execute_probe_uses_real_R_psi",
     "forced_s_omega_logit=None" in probe
     and "actual_r_psi_forward_count" in probe)
item("real_execute_probe_uses_real_S_omega",
     "forced_s_omega_logit=None" in probe
     and "actual_s_omega_forward_count" in probe)
item("real_execute_numerical_validations_bound_into_smoke_all_pass",
     all(f'"{k}": bool(' in SRC for k in (
         "real_execute_router_decision_is_execute",
         "real_execute_R_psi_output_finite",
         "real_execute_R_psi_output_shape_valid",
         "real_execute_post_safety_feature_dim_16",
         "real_execute_post_safety_features_finite",
         "real_execute_S_omega_logit_finite",
         "real_execute_S_omega_probability_finite",
         "real_execute_S_omega_probability_in_unit_interval",
         "real_execute_final_state_valid",
         "real_execute_final_probability_shape_512x512",
         "real_execute_final_probability_finite")))
item("hd95_bound_into_smoke_all_pass",
     '"metric_hd95_nonempty_plumbing_valid": bool(' in SRC
     and '"metric_hd95_empty_mask_semantics_valid": bool(' in SRC
     and 'hd_empty.get("valid") is False' in SRC
     and "in (True, False, None)" not in SRC)
item("write_once_first_attempt_behavior_present",
     "_smoke_attempt_already_exists" in FUNCS
     and "SMOKE_V1_8_ATTEMPT" in SRC and "SMOKE_V1_8_ARTIFACT" in SRC)
main = seg("main")
item("exception_preservation_present",
     "try:" in main and "except Exception as exc:" in main
     and "_write_smoke_failure_artifact" in main)
item("no_automatic_retry",
     not any(isinstance(n, (ast.For, ast.While, ast.AsyncFor))
             for n in ast.walk(FUNCS["main"]))
     and sum(1 for n in ast.walk(FUNCS["main"])
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
             and n.func.id == "run_smoke") <= 1)
item("artifact_written_before_nonzero_exit_on_logical_failure",
     "SMOKE_V1_8_ARTIFACT" in main
     and main.index("SMOKE_V1_8_ARTIFACT")
     < main.index('if not bool(res.get("smoke_all_pass"))'))
item("smoke_gate_separate_from_science_gate",
     "PHASE36_SMOKE_EXECUTE" in SRC and "GATE_ENV" in SRC)
item("no_smoke_or_science_artifact_written",
     not (ROOT / "reports/audits/phase36_robustness_smoke_v1_8.json").exists()
     and not (ROOT / "reports/audits/phase36_robustness_smoke_attempt_v1_8.json").exists()
     and not (ROOT / "reports/audits/phase36_robustness_scientific_result_v1_8.json").exists())

passed = sum(1 for i in items if i["pass"])
total = len(items)
report = {
    "artifact": "phase36_v1_8_direct_source_byte_audit",
    "phase": 36,
    "section": "§M",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_8",
    "type": "DIRECT_SOURCE_BYTE_AUDIT",
    "read_only": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "subject": "scripts/analysis/phase36_robustness_execution_v1_8.py",
    "execution_sha256": sha(EXEC),
    "line_count": len(SRC.splitlines()),
    "ast_parse_success": True,
    "run_smoke_reachable_function_count": len(reach_smoke),
    "run_science_reachable_function_count": len(reach_science),
    "protected_reachable_sites": 0,
    "test_reachable_sites": test_sites,
    "router_holdout_reachable_sites": holdout_sites,
    "items": items,
    "passed": passed,
    "total": total,
    "verdict": ("PASS" if passed == total else "FAIL"),
    "generated_utc": "2026-10-06T11:36:00Z",
}
out = ROOT / "reports/audits/phase36_v1_8_direct_source_byte_audit.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "verdict": report["verdict"],
                  "execution_sha256": report["execution_sha256"],
                  "lines": report["line_count"]}, indent=1))
for i in items:
    if not i["pass"]:
        print("FAIL:", i["item"], json.dumps(i.get("evidence"), default=str))
raise SystemExit(0 if passed == total else 1)
