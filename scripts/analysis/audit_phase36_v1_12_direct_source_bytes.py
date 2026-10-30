#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.12 — DIRECT SOURCE-BYTE AUDIT (READ-ONLY).

The v1.12 revision DOES change the execution subject (D34 launch-anchor
contradiction removal; D35/D36 are in the launcher + suites), so this audit does
not assert byte-identity with v1.11.  Instead it inspects the ACTUAL bytes of the
v1.12 execution source and proves, from those bytes:

  1. the frozen v1.7..v1.11 history is BYTE-PRESERVED (unchanged SHAs);
  2. the preserved D22–D33 invariants are still present in the actual bytes;
  3. the NEW D34 invariant is present in the actual bytes (source no longer
     requires ``manifest["launcher_sha256"]``; fails CLOSED if it appears);
  4. the v1.12 unit suite reads exactly the v1.12 execution source, the
     IMMUTABLE launcher pins the exact frozen exec + manifest SHAs as literals,
     and the manifest declares exec + deps but NOT the launcher SHA;
  5. nothing has been executed (no smoke / science artifact, marker, or failure
     artifact exists, for any revision).

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO VAL image / GT read.  NO protected-population read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import io
import json
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_12.py"
UNIT = ROOT / "scripts/analysis/phase36_robustness_unit_v1_12.py"
NC = ROOT / "scripts/analysis/phase36_robustness_negative_controls_v1_12.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_12.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_12_runtime_source_integrity_manifest.json"

FROZEN_V1_7_EXEC_SHA = "87062d2b38232c73b8ce620d7bfafb389658c4b877d9196a26b8b01d09daf192"
FROZEN_V1_8_EXEC_SHA = "c95ff9884ec05a859b39ce7976376bf40e4543b1a8d8a19830e5893120039f4d"
FROZEN_V1_9_EXEC_SHA = "433bad87b4ef77fd6997c77f688eb295e526bfa3e88dece4ec5d3d550255cbd0"
FROZEN_V1_9_UNIT_SHA = "c39edd7764a0e9733cc5905e5e54935b1bcd9cc62c345189f618b0c6f4ea690e"
FROZEN_V1_10_UNIT_SHA = "9b880c92469e7daca8f6563e64bf2e2e712d4eb8ac304298fbb52f89ab87c329"
FROZEN_V1_11_EXEC_SHA = "dc4928417444304ad637907c53089e512577254b368e438d0098ade6202083f0"
FROZEN_V1_11_LAUNCHER_SHA = "56612332d220f93611fc627b1f495aca3013bb3578ab801ee10b4ee0386b25b0"
FROZEN_V1_11_UNIT_SHA = "189b9957704beccff1ba9c198e7f2f9ed29fa351e9cfc6f46d03441adeaeac41"
FROZEN_V1_11_MANIFEST_SHA = "d795d41152accde6cf59717d2d17ab429b0cdf8fc1ff98bca11dcb13a591bda7"

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
item("v1_7_execution_history_byte_preserved",
     sha(ROOT / "scripts/analysis/phase36_robustness_execution_v1_7.py") == FROZEN_V1_7_EXEC_SHA)
item("v1_8_execution_history_byte_preserved",
     sha(ROOT / "scripts/analysis/phase36_robustness_execution_v1_8.py") == FROZEN_V1_8_EXEC_SHA)
item("v1_9_execution_history_byte_preserved",
     sha(ROOT / "scripts/analysis/phase36_robustness_execution_v1_9.py") == FROZEN_V1_9_EXEC_SHA)
item("v1_9_unit_history_byte_preserved",
     sha(ROOT / "scripts/analysis/phase36_robustness_unit_v1_9.py") == FROZEN_V1_9_UNIT_SHA)
item("v1_10_unit_history_byte_preserved",
     sha(ROOT / "scripts/analysis/phase36_robustness_unit_v1_10.py") == FROZEN_V1_10_UNIT_SHA)
item("v1_11_execution_history_byte_preserved",
     sha(ROOT / "scripts/analysis/phase36_robustness_execution_v1_11.py") == FROZEN_V1_11_EXEC_SHA)
item("v1_11_launcher_history_byte_preserved",
     sha(ROOT / "scripts/analysis/launch_phase36_v1_11.py") == FROZEN_V1_11_LAUNCHER_SHA)
item("v1_11_unit_history_byte_preserved",
     sha(ROOT / "scripts/analysis/phase36_robustness_unit_v1_11.py") == FROZEN_V1_11_UNIT_SHA)
item("v1_11_manifest_history_byte_preserved",
     sha(ROOT / "reports/audits/phase36_v1_11_runtime_source_integrity_manifest.json")
     == FROZEN_V1_11_MANIFEST_SHA)
item("v1_12_execution_subject_sha256", True, sha(EXEC))
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
            and n.func.id == "_hd95_case_exact"] if "run_smoke" in FUNCS else []
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

# ---- D31 invariants: unique v1.12 science paths, no v1.8 aliasing ------------- #
item("D31_science_result_v1_12_path", "phase36_robustness_scientific_result_v1_12.json" in SRC)
item("D31_science_start_v1_12_path", "phase36_robustness_science_start_v1_12.json" in SRC)
item("D31_science_failure_v1_12_path", "phase36_robustness_science_failure_v1_12.json" in SRC)

_struct = SRC
for _n in ast.walk(TREE):
    if isinstance(_n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        _b = getattr(_n, "body", [])
        if _b and isinstance(_b[0], ast.Expr) and isinstance(_b[0].value, ast.Constant) \
                and isinstance(_b[0].value.value, str):
            _struct = _struct.replace(_b[0].value.value, "")
_kept = []
for _t in tokenize.generate_tokens(io.StringIO(_struct).readline):
    if _t.type == tokenize.COMMENT:
        continue
    _kept.append(_t)
try:
    _struct = tokenize.untokenize(_kept)
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

# ---- D33 invariants: external non-circular launcher anchor (v1.12 subject) ---- #
lsrc = LAUNCHER.read_text(encoding="utf-8")
item("D33_launcher_present", LAUNCHER.exists())
item("D33_launcher_freezes_exec_sha", "FROZEN_EXPECTED_EXEC_SHA" in lsrc)
item("D33_launcher_freezes_manifest_sha", "FROZEN_EXPECTED_MANIFEST_SHA" in lsrc)
item("D33_source_requires_launch_token",
     "PHASE36_V1_12_LAUNCH_AUTHORITY" in SRC
     and "LAUNCH_AUTHORITY_TOKEN" in seg("_verify_transitive_source_integrity"))

# ---- D34 invariants: source/manifest launch-anchor contradiction REMOVED ------ #
_integ = seg("_verify_transitive_source_integrity")
item("D34_source_does_not_read_manifest_launcher_sha",
     'manifest.get("launcher_sha256")' not in _integ
     and "expected_launcher" not in _integ)
item("D34_source_fails_closed_on_unexpected_launcher_key",
     '"launcher_sha256" in manifest' in _integ
     and "manifest_launcher_sha256_absent" in _integ
     and "if launcher_key_present or not launch_token_ok:" in _integ)
item("D34_source_still_requires_token",
     "launch_authority_token_present" in _integ)

# ---- D35 invariants: IMMUTABLE non-env-overridable frozen launch hashes ------- #
def _launcher_code_only(src: str) -> str:
    t = ast.parse(src)
    out = src
    for n in ast.walk(t):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = getattr(n, "body", [])
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                out = out.replace(b[0].value.value, "")
    kept = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(out).readline):
            if tok.type == tokenize.COMMENT:
                continue
            kept.append(tok)
        out = tokenize.untokenize(kept)
    except Exception:
        pass
    return out


lcode = _launcher_code_only(lsrc)
_old_names = ("PHASE36_V1_11_EXPECTED_EXEC_SHA", "PHASE36_V1_11_EXPECTED_MANIFEST_SHA",
              "PHASE36_V1_12_EXPECTED_EXEC_SHA", "PHASE36_V1_12_EXPECTED_MANIFEST_SHA")
item("D35_launcher_no_env_read_for_authority",
     "os.environ.get" not in lcode and "getenv" not in lcode)
item("D35_launcher_old_override_names_absent_in_code",
     all(n not in lcode for n in _old_names),
     {"present": [n for n in _old_names if n in lcode]})
_lmod = {n.targets[0].id: n.value.value for n in ast.walk(ast.parse(lsrc))
         if isinstance(n, ast.Assign) and len(n.targets) == 1
         and isinstance(n.targets[0], ast.Name)
         and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)}
item("D35_frozen_exec_const_literal_exact",
     _lmod.get("FROZEN_EXPECTED_EXEC_SHA") == sha(EXEC),
     {"const": _lmod.get("FROZEN_EXPECTED_EXEC_SHA"), "observed": sha(EXEC)})
item("D35_frozen_manifest_const_literal_exact",
     _lmod.get("FROZEN_EXPECTED_MANIFEST_SHA") == sha(MANIFEST),
     {"const": _lmod.get("FROZEN_EXPECTED_MANIFEST_SHA"),
      "observed": sha(MANIFEST)})

# ---- D36 invariants: three-file cross-binding -------------------------------- #
def _load_production_launcher():
    spec = importlib.util.spec_from_file_location("phase36_v1_12_launch_audit", LAUNCHER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_cross_ok = False
try:
    _m = _load_production_launcher()
    _auth = _m.verify_authority()
    _cross_ok = bool(_auth.get("authorized"))
except Exception:
    _cross_ok = False
item("D36_exec_plus_launcher_plus_manifest_mutually_satisfiable", _cross_ok)
man = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
item("D33_manifest_declares_exec_sha", man.get("execution_source_sha256") == sha(EXEC),
     {"declared": man.get("execution_source_sha256"), "observed": sha(EXEC)})
item("D33_manifest_no_launcher_sha_cycle", "launcher_sha256" not in man)
item("D36_manifest_declares_exec_and_lacks_launcher_sha",
     man.get("execution_source_sha256") == sha(EXEC) and "launcher_sha256" not in man)
_coedit_path = ROOT / "reports/audits/phase36_v1_12_launcher_co_edit_negative_control.json"
item("D35_co_edit_negative_control_passed",
     json.loads(_coedit_path.read_text(encoding="utf-8"))["all_mutants_rejected"]
     if _coedit_path.exists() else False)

# ---- gate reports bind the v1.12 subject ------------------------------------- #
u_src = UNIT.read_text(encoding="utf-8")
item("unit_reads_v1_12_execution_source",
     "phase36_robustness_execution_v1_12.py" in u_src)
item("unit_report_exists_and_passes",
     json.loads((ROOT / "reports/audits/phase36_robustness_unit_v1_12.json").read_text(
         encoding="utf-8"))["all_pass"])
item("negative_controls_report_exists_and_passes",
     json.loads((ROOT / "reports/audits/phase36_v1_12_negative_controls.json").read_text(
         encoding="utf-8"))["all_pass"])
item("preflight_report_exists_and_passes",
     json.loads((ROOT / "reports/audits/phase36_robustness_preflight_v1_12.json").read_text(
         encoding="utf-8"))["all_pass"])

# ---- nothing executed (any revision) ----------------------------------------- #
AUD = ROOT / "reports/audits"
_forbidden_artifacts = [
    "phase36_robustness_smoke_v1_12.json",
    "phase36_robustness_smoke_start_v1_12.json",
    "phase36_robustness_smoke_failure_v1_12.json",
    "phase36_robustness_scientific_result_v1_12.json",
    "phase36_robustness_science_start_v1_12.json",
    "phase36_robustness_science_failure_v1_12.json",
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
    "artifact": "phase36_v1_12_direct_source_byte_audit",
    "phase": 36,
    "section": "§M",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_12",
    "type": "DIRECT_SOURCE_BYTE_AUDIT",
    "read_only": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "subject": "scripts/analysis/phase36_robustness_execution_v1_12.py",
    "execution_sha256": sha(EXEC),
    "items": items,
    "passed": passed,
    "total": total,
    "verdict": ("PASS" if passed == total else "FAIL"),
}
out = ROOT / "reports/audits/phase36_v1_12_direct_source_byte_audit.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "verdict": report["verdict"],
                  "execution_sha256": report["execution_sha256"]}, indent=1))
for i in items:
    if not i["pass"]:
        print("FAIL:", i["item"], json.dumps(i.get("evidence"), default=str))
raise SystemExit(0 if passed == total else 1)
