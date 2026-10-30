#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.11 — DIRECT SOURCE-BYTE AUDIT (READ-ONLY).

The v1.11 revision DOES change the execution subject (D30/D31/D32/D33), so this
audit does not assert byte-identity with v1.9.  Instead it inspects the ACTUAL
bytes of the v1.11 execution source and proves, from those bytes:

  1. the frozen v1.9/v1.10 history is BYTE-PRESERVED (unchanged SHAs);
  2. the preserved D22–D28 invariants are still present in the actual bytes
     (derived provenance, exclusive-create, exact 14-path dep set, four hd95
     call sites with exact semantics);
  3. the NEW D30/D31/D32/D33 invariants are present in the actual bytes
     (science pre-model integrity gate, unique v1.11 science paths, write-once
     science START/failure/success artifacts, launcher authority token);
  4. the v1.11 unit suite reads exactly the v1.11 execution source, and the
     non-circular launcher verifies the exact frozen exec + manifest SHAs;
  5. nothing has been executed (no smoke / science artifact, marker, or failure
     artifact exists, for any revision).

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO VAL image / GT read.  NO protected-population read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_11.py"
UNIT = ROOT / "scripts/analysis/phase36_robustness_unit_v1_11.py"
NC = ROOT / "scripts/analysis/phase36_robustness_negative_controls_v1_11.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_11.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_11_runtime_source_integrity_manifest.json"

FROZEN_V1_9_EXEC_SHA = "433bad87b4ef77fd6997c77f688eb295e526bfa3e88dece4ec5d3d550255cbd0"
FROZEN_V1_9_UNIT_SHA = "c39edd7764a0e9733cc5905e5e54935b1bcd9cc62c345189f618b0c6f4ea690e"
FROZEN_V1_10_UNIT_SHA = "9b880c92469e7daca8f6563e64bf2e2e712d4eb8ac304298fbb52f89ab87c329"
FROZEN_V1_8_EXEC_SHA = "c95ff9884ec05a859b39ce7976376bf40e4543b1a8d8a19830e5893120039f4d"
FROZEN_V1_7_EXEC_SHA = "87062d2b38232c73b8ce620d7bfafb389658c4b877d9196a26b8b01d09daf192"

SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def seg(name):
    return ast.get_source_segment(SRC, FUNCS[name]) if name in FUNCS else ""


items = []


def item(key, ok, evidence=None):
    items.append({"item": key, "pass": bool(ok), "evidence": evidence})


# ---- identity / history preservation ----------------------------------------- #
item("v1_9_execution_history_byte_preserved",
     sha(ROOT / "scripts/analysis/phase36_robustness_execution_v1_9.py") == FROZEN_V1_9_EXEC_SHA)
item("v1_9_unit_history_byte_preserved",
     sha(ROOT / "scripts/analysis/phase36_robustness_unit_v1_9.py") == FROZEN_V1_9_UNIT_SHA)
item("v1_10_unit_history_byte_preserved",
     sha(ROOT / "scripts/analysis/phase36_robustness_unit_v1_10.py") == FROZEN_V1_10_UNIT_SHA)
item("v1_8_execution_history_byte_preserved",
     sha(ROOT / "scripts/analysis/phase36_robustness_execution_v1_8.py") == FROZEN_V1_8_EXEC_SHA)
item("v1_7_execution_history_byte_preserved",
     sha(ROOT / "scripts/analysis/phase36_robustness_execution_v1_7.py") == FROZEN_V1_7_EXEC_SHA)
item("v1_11_execution_subject_sha256", True, sha(EXEC))
item("ast_parse_success", True)
item("line_count", True, len(SRC.splitlines()))

# ---- D26 invariants present in the ACTUAL bytes ------------------------------ #
prov = None
for n in ast.walk(FUNCS["run_smoke"]) if "run_smoke" in FUNCS else []:
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name) and t.id == "attempt_provenance" \
                    and isinstance(n.value, ast.Dict):
                prov = n.value
prov_val = None
if prov is not None:
    for k, v in zip(prov.keys, prov.values):
        if isinstance(k, ast.Constant) and k.value == "is_first_write_once":
            prov_val = v
prov_names = {x.id for x in ast.walk(prov_val) if isinstance(x, ast.Name)} \
    if prov_val is not None else set()
item("D26_provenance_is_derived_bool_call",
     isinstance(prov_val, ast.Call) and isinstance(prov_val.func, ast.Name)
     and prov_val.func.id == "bool"
     and {"_marker_exists", "_marker_sole_and_trueseal"} <= prov_names,
     {"observed_names": sorted(prov_names)})
item("D26_exclusive_create_open_x_present",
     'open(start_marker_path, "x"' in seg("run_smoke"))
item("D26_write_once_flag_not_literal_true",
     '"is_first_write_once": True' not in SRC)
item("D26_binding_consumes_derived",
     'bool(attempt_provenance["is_first_write_once"])' in SRC)

# ---- D27 invariants: exact 14-path dependency set ----------------------------- #
deps = None
for n in ast.walk(TREE):
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name) and t.id == "TRANSITIVE_RUNTIME_DEPENDENCIES" \
                    and isinstance(n.value, ast.Dict):
                deps = n.value
dep_paths = {k.value for k in deps.keys} if deps is not None else set()
item("D27_exact_14_transitive_dependencies", len(dep_paths) == 14,
     {"observed": len(dep_paths)})
item("D27_expected_14_paths_exact_match",
     dep_paths == {
         "scripts/analysis/phase36_robustness_common_v1_1.py",
         "scripts/analysis/train_phase25d_router.py",
         "scripts/analysis/phase25f_execution_common.py",
         "scripts/analysis/phase25f_post_safety_features.py",
         "src/features/barr_pre_refinement_features.py",
         "src/data/barr_roi.py",
         "src/models/film/global_medfilm.py",
         "src/models/barr/regional_refiner.py",
         "src/models/barr/ra_medfilm_barr.py",
         "src/utils/device.py",
         "src/metrics/evaluation_metrics.py",
         "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json",
         "reports/tables/phase25d_final_normalization_stats.csv",
         "reports/tables/phase25f_final_normalization_stats.csv",
     }, {"observed": sorted(dep_paths)})
n_ckpt = 0
for n in ast.walk(TREE):
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name) and t.id == "TRANSITIVE_RUNTIME_CHECKPOINTS" \
                    and isinstance(n.value, ast.Dict):
                n_ckpt = len(n.value.keys)
item("D23_four_checkpoints", n_ckpt == 4, {"n": n_ckpt})

# ---- D28 invariants: four ACTUAL hd95 call sites ----------------------------- #
hd_calls = [n for n in ast.walk(FUNCS["run_smoke"])
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id == "_hd95_case_exact"]
item("D28_four_actual_hd95_call_sites", len(hd_calls) == 4, {"n": len(hd_calls)})


def _exp(call):
    ref = None
    if call.args and isinstance(call.args[0], ast.Subscript) \
            and isinstance(call.args[0].slice, ast.Constant):
        ref = call.args[0].slice.value
    ev = er = None
    for kw in call.keywords:
        if kw.arg == "expect_valid" and isinstance(kw.value, ast.Constant):
            ev = kw.value.value
        if kw.arg == "expect_reason" and isinstance(kw.value, ast.Constant):
            er = kw.value.value
    return ref, ev, er


observed = {_exp(c) for c in hd_calls}
item("D28_four_hd95_call_semantics_exact",
     observed == {("nonempty_nonempty", True, ""),
                 ("empty_prediction_nonempty_gt", False, "empty_prediction"),
                 ("nonempty_prediction_empty_gt", False, "empty_ground_truth"),
                 ("empty_empty", False, "both_empty")},
     {"observed": sorted(str(x) for x in observed)})

# ---- D30 invariants: science integrity gate BEFORE _load_models --------------- #
def _body_calls_in_order(fname):
    fn = FUNCS.get(fname)
    if fn is None:
        return []
    out = []
    for stmt in fn.body:
        for n in ast.walk(stmt):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                out.append((n.lineno, n.func.id))
    return sorted(out)


sci = _body_calls_in_order("run_science")
names = [nm for _, nm in sci]
gate_before = False
if "_verify_transitive_source_integrity" in names and "_load_models" in names:
    gate_before = (next(ln for ln, nm in sci if nm == "_verify_transitive_source_integrity")
                   < next(ln for ln, nm in sci if nm == "_load_models"))
item("D30_science_integrity_gate_before_load_models", gate_before,
     {"science_calls": names})
item("D30_science_fail_closed_terminal",
     "D30_SCIENCE_TRANSITIVE_RUNTIME_SOURCE_INTEGRITY_FAILED__STOP_BEFORE_MODEL_CONSTRUCTION"
     in SRC)
item("D30_smoke_also_gates_integrity",
     "_verify_transitive_source_integrity" in [nm for _, nm in
                                               _body_calls_in_order("run_smoke")])

# ---- D31 invariants: unique v1.11 science paths, no v1.8 aliasing ------------- #
item("D31_science_result_v1_11_path", "phase36_robustness_scientific_result_v1_11.json" in SRC)
item("D31_science_start_v1_11_path", "phase36_robustness_science_start_v1_11.json" in SRC)
item("D31_science_failure_v1_11_path", "phase36_robustness_science_failure_v1_11.json" in SRC)
# Structural: remove (a) docstring literals, (b) comments, and (c) every assigned
# string constant, then the v1.8/v1.9 science literal must be absent from any
# executable position (a declared sentinel is not a write target).
import io as _io
import tokenize as _tok

_struct = SRC
for _n in ast.walk(TREE):
    if isinstance(_n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        _b = getattr(_n, "body", [])
        if _b and isinstance(_b[0], ast.Expr) and isinstance(_b[0].value, ast.Constant) \
                and isinstance(_b[0].value.value, str):
            _struct = _struct.replace(_b[0].value.value, "")
_kept = []
for _t in _tok.generate_tokens(_io.StringIO(_struct).readline):
    if _t.type == _tok.COMMENT:
        continue
    _kept.append(_t)
try:
    _struct = _tok.untokenize(_kept)
except Exception:
    pass
for _n in ast.walk(TREE):
    if isinstance(_n, ast.Assign) and isinstance(_n.value, ast.Constant) \
            and isinstance(_n.value.value, str) and _n.value.value:
        _struct = _struct.replace(_n.value.value, "None")
item("D31_no_v1_8_science_write_target",
     "scientific_result_v1_8.json" not in _struct)
item("D31_no_v1_9_science_write_target",
     "scientific_result_v1_9.json" not in _struct)
item("D31_forbidden_sentinel_declared",
     "FORBIDDEN_SCIENCE_RESULT_V1_8" in SRC)

# ---- D32 invariants: science first-attempt write-once + durable evidence ------ #
item("D32_science_start_marker_helper", "_create_science_start_marker" in FUNCS)
item("D32_science_start_marker_os_excl",
     "O_CREAT" in seg("_create_science_start_marker")
     and "O_EXCL" in seg("_create_science_start_marker"))
item("D32_science_attempt_existence_guard", "_science_attempt_already_exists" in FUNCS)
item("D32_science_durable_evidence_wrapper",
     "_run_science_with_durable_evidence" in FUNCS)
item("D32_wrapper_records_systemexit", "except SystemExit" in seg("_run_science_with_durable_evidence"))
item("D32_wrapper_records_exception", "except Exception" in seg("_run_science_with_durable_evidence"))
item("D32_wrapper_records_logical_failure",
     "LOGICAL_FAILURE" in seg("_run_science_with_durable_evidence"))
item("D32_success_writer_exclusive_create",
     'open(path, "x"' in seg("_write_science_success_artifact"))
item("D32_failure_writer_exclusive_create",
     'open(path, "x"' in seg("_write_science_failure_artifact"))
item("D32_main_gate_before_marker",
     seg("main").find("_gate_science_state()") < seg("main").find("_create_science_start_marker")
     if "_gate_science_state()" in seg("main") else False)

# ---- D33 invariants: external non-circular launcher anchor -------------------- #
lsrc = LAUNCHER.read_text(encoding="utf-8")
item("D33_launcher_present", LAUNCHER.exists())
item("D33_launcher_freezes_exec_sha", "FROZEN_EXPECTED_EXEC_SHA" in lsrc)
item("D33_launcher_freezes_manifest_sha", "FROZEN_EXPECTED_MANIFEST_SHA" in lsrc)
item("D33_source_requires_launch_token",
     "PHASE36_V1_11_LAUNCH_AUTHORITY" in SRC
     and "LAUNCH_AUTHORITY_TOKEN" in seg("_verify_transitive_source_integrity"))
man = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
item("D33_manifest_declares_exec_sha", man.get("execution_source_sha256") == sha(EXEC),
     {"declared": man.get("execution_source_sha256"), "observed": sha(EXEC)})
item("D33_manifest_no_launcher_sha_cycle", "launcher_sha256" not in man)
item("D33_co_edit_negative_control_passed",
     json.loads((ROOT / "reports/audits/phase36_v1_11_launcher_co_edit_negative_control.json")
                .read_text(encoding="utf-8"))["passed"]
     if (ROOT / "reports/audits/phase36_v1_11_launcher_co_edit_negative_control.json").exists()
     else False)

# ---- gate reports bind the v1.11 subject ------------------------------------- #
u_src = UNIT.read_text(encoding="utf-8")
item("unit_reads_v1_11_execution_source",
     "phase36_robustness_execution_v1_11.py" in u_src)
item("unit_report_exists_and_passes",
     json.loads((ROOT / "reports/audits/phase36_robustness_unit_v1_11.json").read_text(
         encoding="utf-8"))["all_pass"])
item("negative_controls_report_exists_and_passes",
     json.loads((ROOT / "reports/audits/phase36_v1_11_negative_controls.json").read_text(
         encoding="utf-8"))["all_pass"])
item("preflight_report_exists_and_passes",
     json.loads((ROOT / "reports/audits/phase36_robustness_preflight_v1_11.json").read_text(
         encoding="utf-8"))["all_pass"])

# ---- nothing executed (any revision) ----------------------------------------- #
AUD = ROOT / "reports/audits"
_forbidden_artifacts = [
    "phase36_robustness_smoke_v1_11.json",
    "phase36_robustness_smoke_start_v1_11.json",
    "phase36_robustness_smoke_failure_v1_11.json",
    "phase36_robustness_scientific_result_v1_11.json",
    "phase36_robustness_science_start_v1_11.json",
    "phase36_robustness_science_failure_v1_11.json",
    "phase36_robustness_smoke_v1_10.json",
    "phase36_robustness_scientific_result_v1_10.json",
    "phase36_robustness_smoke_v1_9.json",
    "phase36_robustness_smoke_start_v1_9.json",
    "phase36_robustness_smoke_failure_v1_9.json",
    "phase36_robustness_scientific_result_v1_9.json",
    "phase36_robustness_scientific_result_v1_8.json",
]
present = [f for f in _forbidden_artifacts if (AUD / f).exists()]
item("no_smoke_or_science_artifact_any_revision", not present,
     {"present": present})

passed = sum(1 for i in items if i["pass"])
total = len(items)
report = {
    "artifact": "phase36_v1_11_direct_source_byte_audit",
    "phase": 36,
    "section": "§M",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_11",
    "type": "DIRECT_SOURCE_BYTE_AUDIT",
    "read_only": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "subject": "scripts/analysis/phase36_robustness_execution_v1_11.py",
    "execution_sha256": sha(EXEC),
    "items": items,
    "passed": passed,
    "total": total,
    "verdict": ("PASS" if passed == total else "FAIL"),
}
out = ROOT / "reports/audits/phase36_v1_11_direct_source_byte_audit.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "verdict": report["verdict"],
                  "execution_sha256": report["execution_sha256"]}, indent=1))
for i in items:
    if not i["pass"]:
        print("FAIL:", i["item"], json.dumps(i.get("evidence"), default=str))
raise SystemExit(0 if passed == total else 1)
