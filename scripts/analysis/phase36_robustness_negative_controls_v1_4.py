#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.4 — negative controls NC15-NC24 (model-free, static/unit).

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_4

Each control proves a KNOWN-BAD pattern is BOTH (a) demonstrably present in the
frozen v1.3 source bytes / v1.3 call graph and (b) ABSENT from / correctly
repaired by the v1.4 source bytes / v1.4 call graph.  A control PASSES only when
v1.3 FAILS it and v1.4 PASSES it — i.e. the repair is genuinely load-bearing.

  NC15 proposal smoke that only changes geometry but never calls the proposal
       evaluator.
  NC16 empty-proposal smoke that only checks a constant / None geometry.
  NC17 R_psi forward reachable before the B_phi / A8-C9 decision.
  NC18 G path lacking the canonical autocast-fp16 context.
  NC19 G clean path using batch size 1 instead of the frozen batch-8 membership.
  NC20 CPU task-ID tensor passed to a CUDA G.
  NC21 clean route comparison reduced to global-vs-nonglobal.
  NC22 router_decision assigned from the final state.
  NC23 KUB report without subgroup metadata.
  NC24 missing R1-R5 scientific figure call graph.

NO torch. NO model. NO protected-data read.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

import scripts.analysis.phase36_robustness_execution_v1_4 as E  # noqa: E402

V13 = (ROOT / "scripts/analysis/phase36_robustness_execution_v1_3.py").read_text(encoding="utf-8")
V14 = (ROOT / "scripts/analysis/phase36_robustness_execution_v1_4.py").read_text(encoding="utf-8")
T13 = ast.parse(V13)
T14 = ast.parse(V14)
F13 = {n.name: n for n in ast.walk(T13) if isinstance(n, ast.FunctionDef)}
F14 = {n.name: n for n in ast.walk(T14) if isinstance(n, ast.FunctionDef)}

results = []


def record(name, v13_fails, v14_passes, note, evidence=None):
    results.append({
        "control": name,
        "v1_3_fails_control": bool(v13_fails),
        "v1_4_passes_control": bool(v14_passes),
        "pass": bool(v13_fails and v14_passes),
        "note": note,
        "evidence": evidence or {},
    })


def _calls(funcs, fn_name):
    node = funcs.get(fn_name)
    if node is None:
        return set()
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            out.add(f.id if isinstance(f, ast.Name)
                    else (f.attr if isinstance(f, ast.Attribute) else None))
    return out


def _reachable(funcs, fn_name, target, seen=None):
    seen = set() if seen is None else seen
    if fn_name in seen:
        return False
    seen.add(fn_name)
    cs = _calls(funcs, fn_name)
    if target in cs:
        return True
    return any(_reachable(funcs, c, target, seen) for c in cs if c in funcs)


def _line(funcs, fn_name, pred):
    node = funcs.get(fn_name)
    if node is None:
        return None
    hits = [n.lineno for n in ast.walk(node) if pred(n)]
    return min(hits) if hits else None


def _rpsi_line(funcs, fn_name):
    """First line inside ``fn_name`` that actually CALLS the refiner."""
    node = funcs.get(fn_name)
    if node is None:
        return None
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Subscript):
            seg = ast.unparse(n.func)
            if "r_psi" in seg:
                return n.lineno
    return None


def _forward_inference_line(funcs, fn_name):
    node = funcs.get(fn_name)
    if node is None:
        return None
    hits = [n.lineno for n in ast.walk(node)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "forward_inference"]
    return min(hits) if hits else None


def _funcs_referencing(src, funcs, token):
    return sorted(name for name, node in funcs.items()
                  if token in ast.get_source_segment(src, node))


# --------------------------------------------------------------------------- #
# NC15 — proposal smoke that only changes geometry, never calls the evaluator
# --------------------------------------------------------------------------- #
v13_calls = _calls(F13, "run_smoke")
v14_calls = _calls(F14, "run_smoke")
record(
    "NC15_proposal_smoke_geometry_only_no_evaluator",
    ("_evaluate_frozen_system_proposal" not in v13_calls
     and "apply_proposal_condition" in v13_calls),
    (_reachable(F14, "run_smoke", "proposal_core_adapter")
     and "geometry_only_apply_counts_as_proposal_smoke" in V14),
    "v1.3 smoke perturbed geometry via apply_proposal_condition but never reached the "
    "real proposal evaluator; v1.4 smoke reaches proposal_core_adapter (the same adapter "
    "science uses) and explicitly refuses to count geometry-only mutation as coverage.",
    {"v1_3_run_smoke_direct_calls": sorted(c for c in v13_calls if c in F13),
     "v1_4_run_smoke_direct_calls": sorted(c for c in v14_calls if c in F14)})

# --------------------------------------------------------------------------- #
# NC16 — empty-proposal smoke that only checks a constant / None geometry
# --------------------------------------------------------------------------- #
v13_empty_constant_only = ("_roi_geometry_from_prob(np.zeros((512, 512), dtype=np.float32))"
                           in V13
                           and "empty_proposal_geometry_is_none" in V13
                           and not _reachable(F13, "run_smoke",
                                              "_evaluate_frozen_system_proposal"))
record(
    "NC16_empty_proposal_smoke_constant_check_only",
    v13_empty_constant_only,
    (_reachable(F14, "smoke_empty_proposal_pipeline", "proposal_core_adapter")
     and "proposal_geometry=None" in V14
     and "no_replacement_geometry_generated" in V14
     and "no_R_psi_forward" in V14),
    "v1.3 asserted the empty-proposal contract from a constant geometry check; v1.4 calls "
    "the real adapter with proposal_geometry=None and programmatically verifies "
    "NOT_APPLICABLE_EMPTY_PROPOSAL, zero R_psi forwards, zero S_omega forwards and no "
    "replacement geometry.",
    {"v1_3_had_empty_constant_check": "empty_proposal_geometry_is_none" in V13})

# --------------------------------------------------------------------------- #
# NC17 — R_psi forward reachable before the B_phi / A8-C9 decision
# --------------------------------------------------------------------------- #
pre13 = {}
for fn in ("_evaluate_clean_sample", "_evaluate_frozen_system",
           "_evaluate_frozen_system_proposal"):
    r = _rpsi_line(F13, fn)
    f = _forward_inference_line(F13, fn)
    pre13[fn] = {"r_psi_line": r, "forward_inference_line": f,
                 "r_psi_precedes_decision": bool(r is not None and f is not None and r < f)}
v13_pre = all(v["r_psi_precedes_decision"] for v in pre13.values()) and bool(pre13)

dec14 = _line(F14, "canonical_learned_core",
              lambda n: isinstance(n, ast.Compare)
              and isinstance(n.comparators[0], ast.Name)
              and n.comparators[0].id == "TAU_C8_FINAL_FLOAT")
r14 = _rpsi_line(F14, "canonical_learned_core")
s14 = _line(F14, "canonical_learned_core",
            lambda n: isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and n.func.attr == "post_safety")
record(
    "NC17_r_psi_reachable_before_decision",
    v13_pre,
    (dec14 is not None and r14 is not None and dec14 < r14
     and s14 is not None and dec14 < s14),
    "v1.3 executed R_psi before forward_inference (which contains the B_phi/A8-C9 "
    "decision) in all three evaluators; v1.4's shared core runs R_psi and S_omega only "
    "after the canonical utility comparison.",
    {"v1_3": pre13, "v1_4": {"decision_line": dec14, "r_psi_line": r14,
                             "s_omega_line": s14}})

# --------------------------------------------------------------------------- #
# NC18 — G path lacking the canonical autocast-fp16 context
# --------------------------------------------------------------------------- #
record(
    "NC18_g_path_missing_autocast_fp16",
    ("autocast" not in V13 and "inference_mode" not in V13),
    ("CANONICAL_G_AUTOCAST_ENABLED = True" in V14
     and 'CANONICAL_G_AUTOCAST_DTYPE = "float16"' in V14
     and "CANONICAL_G_INFERENCE_MODE = False" in V14
     and 'canonical_autocast(ctx["device"])' in V14
     and "def canonical_autocast" in V14),
    "v1.3 had no autocast context at all (and no inference_mode declaration); v1.4 binds "
    "the frozen Phase27 AMP contract (autocast fp16 enabled, inference_mode false) and "
    "uses it on every canonical G forward.",
    {"v1_3_autocast_mentions": V13.count("autocast"),
     "v1_4_autocast_mentions": V14.count("autocast")})

# --------------------------------------------------------------------------- #
# NC19 — G clean path using batch size 1 instead of frozen batch-8 membership
# --------------------------------------------------------------------------- #
v13_single = (V13.count('ctx["g"](image_b, torch.tensor([task_id]))') >= 1
              or V13.count('ctx["g"](img_b, torch.tensor([int(task_id)]))') >= 1)
v14_batched = ("CANONICAL_G_BATCH_SIZE = 8" in V14
               and "def canonical_batch_partition" in V14
               and "canonical_batch_partition(rows)" in V14
               and "canonical_g_forward_batched" in _calls(F14, "run_image_perturbations")
               and E.CANONICAL_BATCH_FORWARDS_TOTAL == 102)
audit = E.canonical_batch_plan_audit()
record(
    "NC19_g_clean_path_batch_size_1_not_batch_8",
    v13_single,
    (v14_batched and audit["matches_phase27_exact_partition"] is True),
    "v1.3 ran G strictly sample-by-sample (batch size 1); v1.4 partitions VAL808 into the "
    "frozen Phase27 domain-local contiguous batches of 8 and reproduces the exact "
    "partition (102 batches; 11/45/35/11; last 4/5/8/7).",
    {"v1_4_partition_audit": audit})

# --------------------------------------------------------------------------- #
# NC20 — CPU task-ID tensor passed to a CUDA G
# --------------------------------------------------------------------------- #
bare13 = re.findall(r"torch\.tensor\(\[[^\]]*task_id[^\]]*\]\s*\)", V13)
bound13 = re.findall(r"torch\.tensor\(\[[^\]]*task_id[^\]]*\]\s*,\s*dtype=torch\.long\s*,"
                     r"\s*device=device\)", V13)
bare14 = re.findall(r"torch\.tensor\(\[[^\]]*task_id[^\]]*\]\s*\)", V14)
bound14 = re.findall(r"torch\.tensor\(\[[^\]]*task_id[^\]]*\]\s*,\s*dtype=torch\.long\s*,"
                     r"\s*device=device\)", V14)
record(
    "NC20_cpu_task_id_tensor_to_cuda_g",
    (len(bare13) > 0 and len(bound13) == 0),
    (len(bare14) == 0 and len(bound14) >= 2
     and "CANONICAL_G_TASK_ID_DEVICE_MISMATCH" in V14),
    "v1.3 constructed unbound CPU task-id tensors at 4 G call sites and had zero "
    "device-bound sites; v1.4 has zero unbound sites, binds every task-id tensor with "
    "device=device, and fails closed on a device mismatch.",
    {"v1_3": {"bare": len(bare13), "device_bound": len(bound13)},
     "v1_4": {"bare": len(bare14), "device_bound": len(bound14)}})

# --------------------------------------------------------------------------- #
# NC21 — clean route comparison reduced to global-vs-nonglobal
# --------------------------------------------------------------------------- #
record(
    "NC21_clean_route_comparison_global_vs_nonglobal",
    ("gen_global != bound_global" in V13 and "route_mismatches" in V13
     and "n_state_machine_branch_comparisons" not in V13),
    ("gen_global != bound_global" not in V14
     and "n_state_machine_branch_comparisons_808" in V14
     and "route_branch_mismatches_zero" in V14
     and "accept_reject_collapse_prohibited" in V14
     and 'grec.get("state_machine_branch") != bound_branch' in V14),
    "v1.3 collapsed SKIP vs non-SKIP only; v1.4 compares the EXACT state_machine_branch "
    "for all 808 samples and explicitly prohibits collapsing ACCEPT and REJECT.",
    {"v1_3_collapse_expression": "gen_global != bound_global" in V13})

# --------------------------------------------------------------------------- #
# NC22 — router_decision assigned from the final state
# --------------------------------------------------------------------------- #
record(
    "NC22_router_decision_assigned_from_final_state",
    ('clean_store.setdefault("router_decision", {})[sid] = out.get("state")' in V13
     and 'pert_decision = out.get("state")' in V13),
    ('router_decision"] = out.get("state")' not in V14
     and 'router_decision"] = out["state"]' not in V14
     and 'ROUTER_DECISIONS = ("SKIP", "EXECUTE")' in V14
     and "ROUTER_DECISION_NOT_CANONICAL" in V14),
    "v1.3 populated router_decision from the final state in both the clean and perturbed "
    "paths; v1.4 separates router_decision in {SKIP, EXECUTE} from final_state in "
    "{FORCED_SKIP, SKIP_GLOBAL, EXECUTE_THEN_ACCEPT, EXECUTE_THEN_REJECT} and the row "
    "builder rejects a final state passed as a router decision.",
    {"v1_3_clean_assignment_present":
     'clean_store.setdefault("router_decision", {})[sid] = out.get("state")' in V13})

# --------------------------------------------------------------------------- #
# NC23 — KUB report without subgroup metadata
# --------------------------------------------------------------------------- #
v13_kub_no_subgroup = ("Kidney_Stone" not in V13 and "Bladder_Stone" not in V13
                       and "Ureteric_Stone" not in V13
                       and '"category"' not in V13 and "'category'" not in V13)
sub = E.kub_subgroup_map()
sub_counts = {k: list(sub.values()).count(k) for k in sorted(set(sub.values()))}
record(
    "NC23_kub_report_without_subgroup_metadata",
    v13_kub_no_subgroup,
    ("def kub_subgroup_map" in V14
     and 'KUB_SUBGROUP_AUTHORITY["label_column"]' in V14
     and '"kub_subgroup"' in V14
     and len(sub) == 280
     and sub_counts == {"Bladder_Stone": 144, "Kidney_Stone": 112, "Ureteric_Stone": 24}),
    "v1.3 emitted KUB rows with no subgroup label and never read the frozen category "
    "column; v1.4 binds the frozen KUB subgroup metadata authority (280 KUB rows; "
    "144/112/24) and emits real subgroup labels plus per-subgroup robustness summaries "
    "(reporting only — never classes, task ids or model inputs).",
    {"v1_4_subgroup_counts": sub_counts})

# --------------------------------------------------------------------------- #
# NC24 — missing R1-R5 scientific figure call graph
# --------------------------------------------------------------------------- #
v13_no_figs = (not any(f"def figure_R{i}" in V13 for i in range(1, 6))
               and "generate_all_figures" not in _calls(F13, "run_science")
               and "FIGURE_REGISTRY" not in V13)
record(
    "NC24_missing_r1_r5_scientific_figure_call_graph",
    v13_no_figs,
    (all(f"def figure_R{i}" in V14 for i in range(1, 6))
     and "FIGURE_REGISTRY = C.FIGURES" in V14
     and "generate_all_figures" in _calls(F14, "run_science")
     and "FIGURE_REGISTRY_MISMATCH" in V14),
    "v1.3 had no figure builders and no figure call graph in the science path; v1.4 "
    "implements the frozen R1-R5 registry and reaches it only after successful scientific "
    "execution, asserting the emitted set equals the frozen registry.",
    {"v1_3_figure_builders": [i for i in range(1, 6) if f"def figure_R{i}" in V13]})

# --------------------------------------------------------------------------- #
passed = sum(1 for r in results if r["pass"])
report = {
    "artifact": "phase36_robustness_negative_controls_v1_4",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_4",
    "model_free": True,
    "torch_imported": "torch" in sys.modules,
    "subject_v1_3_sha256":
        "a3290c640f9632499905b974606d4c7e7e7be89886ef1f8507a9007814da297c",
    "controls": results,
    "passed": passed,
    "total": len(results),
    "all_pass": passed == len(results),
    "nc_range": "NC15-NC24",
    "each_control_requires": "v1_3_fails_control AND v1_4_passes_control",
}
out = ROOT / "reports/audits/phase36_v1_4_negative_controls.json"
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": len(results),
                  "all_pass": passed == len(results)}, indent=1))
for r in results:
    if not r["pass"]:
        print("FAIL:", r["control"], json.dumps(r, default=str))
raise SystemExit(0 if passed == len(results) else 1)
