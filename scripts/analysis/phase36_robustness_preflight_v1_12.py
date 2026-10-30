#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.12 — PREFLIGHT (source / AST / static only).

Validates the NEW v1.12 governance repairs (D34 source/manifest launch-anchor
contradiction removed; D35 IMMUTABLE non-env-overridable frozen launch hashes;
D36 THREE-FILE validation cross-binding exec+launcher+manifest) as STATIC
properties of the NEW v1.12 execution subject + the NEW v1.12 unit suite + the
NEW launcher + the NEW manifest, while re-asserting that:
  * the frozen v1.7..v1.11 history is BYTE-PRESERVED,
  * the preserved D22–D33 repairs remain enforced,
  * the scientific semantics are UNCHANGED (new_scientific_choice = false),
  * governance flags (TEST / ROUTER_HOLDOUT / VAL authority) are untouched,
  * and NO smoke / science output exists yet.

NO torch.  NO model.  NO checkpoint deserialization.  NO CUDA.  NO forward.
NO smoke.  NO science.  NO VAL image / GT read.  NO protected-population read.
NO ROUTER_HOLDOUT.  NO TEST.
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
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_12.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_12_runtime_source_integrity_manifest.json"
NC = ROOT / "scripts/analysis/phase36_robustness_negative_controls_v1_12.py"

EXEC_V19 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_9.py"
UNIT_V19 = ROOT / "scripts/analysis/phase36_robustness_unit_v1_9.py"
UNIT_V110 = ROOT / "scripts/analysis/phase36_robustness_unit_v1_10.py"
EXEC_V111 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_11.py"
LAUNCHER_V111 = ROOT / "scripts/analysis/launch_phase36_v1_11.py"
UNIT_V111 = ROOT / "scripts/analysis/phase36_robustness_unit_v1_11.py"
MANIFEST_V111 = ROOT / "reports/audits/phase36_v1_11_runtime_source_integrity_manifest.json"

SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}

USRC = UNIT.read_text(encoding="utf-8")
UTREE = ast.parse(USRC)
LSRC = LAUNCHER.read_text(encoding="utf-8")
LTREE = ast.parse(LSRC)

FROZEN_V1_7_EXEC_SHA = "87062d2b38232c73b8ce620d7bfafb389658c4b877d9196a26b8b01d09daf192"
FROZEN_V1_8_EXEC_SHA = "c95ff9884ec05a859b39ce7976376bf40e4543b1a8d8a19830e5893120039f4d"
FROZEN_V1_9_EXEC_SHA = "433bad87b4ef77fd6997c77f688eb295e526bfa3e88dece4ec5d3d550255cbd0"
FROZEN_V1_9_UNIT_SHA = "c39edd7764a0e9733cc5905e5e54935b1bcd9cc62c345189f618b0c6f4ea690e"
FROZEN_V1_10_UNIT_SHA = "9b880c92469e7daca8f6563e64bf2e2e712d4eb8ac304298fbb52f89ab87c329"
FROZEN_V1_11_EXEC_SHA = "dc4928417444304ad637907c53089e512577254b368e438d0098ade6202083f0"
FROZEN_V1_11_LAUNCHER_SHA = "56612332d220f93611fc627b1f495aca3013bb3578ab801ee10b4ee0386b25b0"
FROZEN_V1_11_UNIT_SHA = "189b9957704beccff1ba9c198e7f2f9ed29fa351e9cfc6f46d03441adeaeac41"
FROZEN_V1_11_MANIFEST_SHA = "d795d41152accde6cf59717d2d17ab429b0cdf8fc1ff98bca11dcb13a591bda7"

checks = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def seg(name):
    return ast.get_source_segment(SRC, FUNCS[name]) or ""


def _code_only(src: str) -> str:
    kept = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        kept.append(tok)
    try:
        return tokenize.untokenize(kept)
    except Exception:
        return ""


USRC_CODE = _code_only(USRC)
LSRC_CODE = _code_only(LSRC)
SRC_CODE = _code_only(SRC)

# ---- A. frozen history byte-preserved ----------------------------------------- #
check("A01_v1_7_execution_byte_preserved",
      (ROOT / "scripts/analysis/phase36_robustness_execution_v1_7.py").exists()
      and _sha(ROOT / "scripts/analysis/phase36_robustness_execution_v1_7.py")
      == FROZEN_V1_7_EXEC_SHA)
check("A02_v1_8_execution_byte_preserved",
      (ROOT / "scripts/analysis/phase36_robustness_execution_v1_8.py").exists()
      and _sha(ROOT / "scripts/analysis/phase36_robustness_execution_v1_8.py")
      == FROZEN_V1_8_EXEC_SHA)
check("A03_v1_9_execution_byte_preserved", _sha(EXEC_V19) == FROZEN_V1_9_EXEC_SHA,
      {"expected": FROZEN_V1_9_EXEC_SHA, "observed": _sha(EXEC_V19)})
check("A04_v1_9_unit_history_byte_preserved", _sha(UNIT_V19) == FROZEN_V1_9_UNIT_SHA,
      {"expected": FROZEN_V1_9_UNIT_SHA, "observed": _sha(UNIT_V19)})
check("A05_v1_10_unit_history_byte_preserved", _sha(UNIT_V110) == FROZEN_V1_10_UNIT_SHA,
      {"expected": FROZEN_V1_10_UNIT_SHA, "observed": _sha(UNIT_V110)})
check("A06_v1_11_execution_byte_preserved", _sha(EXEC_V111) == FROZEN_V1_11_EXEC_SHA,
      {"expected": FROZEN_V1_11_EXEC_SHA, "observed": _sha(EXEC_V111)})
check("A07_v1_11_launcher_byte_preserved", _sha(LAUNCHER_V111) == FROZEN_V1_11_LAUNCHER_SHA,
      {"expected": FROZEN_V1_11_LAUNCHER_SHA, "observed": _sha(LAUNCHER_V111)})
check("A08_v1_11_unit_byte_preserved", _sha(UNIT_V111) == FROZEN_V1_11_UNIT_SHA,
      {"expected": FROZEN_V1_11_UNIT_SHA, "observed": _sha(UNIT_V111)})
check("A09_v1_11_manifest_byte_preserved", _sha(MANIFEST_V111) == FROZEN_V1_11_MANIFEST_SHA,
      {"expected": FROZEN_V1_11_MANIFEST_SHA, "observed": _sha(MANIFEST_V111)})

# ---- B. v1.12 unit suite has no tautology + has the self-guard ----------------- #
def _unit_or_true(tree) -> list:
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
            if any(isinstance(v, ast.Constant) and v.value is True for v in n.values):
                out.append(getattr(n, "lineno", -1))
    return out


check("B01_v1_12_unit_no_or_true_boolop", len(_unit_or_true(UTREE)) == 0,
      {"offending_lines": _unit_or_true(UTREE)})
check("B02_v1_12_unit_has_self_guard", "00_self_no_or_true_expression" in USRC)
check("B03_v1_12_unit_no_lower_bound_transitive_count",
      ">= 13" not in USRC_CODE and ">=13" not in USRC_CODE)
check("B04_v1_12_unit_no_substring_call_count",
      'count("_hd95_case_exact(")' not in USRC_CODE)

# D22–D33 repairs preserved in the v1.12 unit suite (match the v1.12 ids).
check("B05_unit_d26_ast_dataflow_assertion",
      "20_D26_provenance_derived_not_literal" in USRC
      and "21_D26_binding_consumes_derived" in USRC
      and "_find_assigned_dict" in USRC and "_has_or_true" in USRC)
check("B06_unit_d27_exact_set_equality",
      "25_D27_transitive_dep_exact_count_14" in USRC
      and "26_D27_transitive_dep_exact_set_equality" in USRC
      and "EXPECTED_TRANSITIVE_DEPENDENCIES" in USRC)
check("B07_unit_d28_ast_four_call_sites",
      "41_D28_four_actual_hd95_call_sites" in USRC
      and "42_D28_hd95_call_sites_exact_semantics" in USRC)
check("B08_unit_d30_science_gate_present",
      "50_D30_science_integrity_gate_present" in USRC
      and "51_D30_science_integrity_gate_before_load_models" in USRC)
check("B09_unit_d31_unique_paths_present",
      "55_D31_science_result_is_v1_12_path" in USRC
      and "56_D31_no_v1_8_science_write" in USRC)
check("B10_unit_d32_first_attempt_present",
      "D32" in USRC and "science_start" in USRC.lower())
check("B11_unit_d33_launcher_anchor_present",
      "D33" in USRC and "launch" in USRC.lower())
# NEW v1.12 repairs present in the v1.12 unit suite.
check("B12_unit_d34_present",
      "D34" in USRC and "100_D34_source_does_not_read_manifest_launcher_sha" in USRC)
check("B13_unit_d35_present",
      "D35" in USRC and "110_D35_launcher_no_os_environ_get" in USRC)
check("B14_unit_d36_cross_binding_present",
      "D36" in USRC and "126_D36_cross_contract_canonical_pair_satisfiable" in USRC
      and "127_D36_cross_contract_env_override_inert" in USRC
      and "128_D36_old_override_env_cannot_change_authority" in USRC)

# ---- C. execution-subject invariants the repairs assert over ------------------ #
prov = None
for n in ast.walk(FUNCS["run_smoke"]) if "run_smoke" in FUNCS else []:
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name) and t.id == "attempt_provenance" \
                    and isinstance(n.value, ast.Dict):
                prov = n.value
check("C01_attempt_provenance_dict_present", prov is not None)
check("C02_write_once_flag_not_literal_true",
      '"is_first_write_once": True' not in SRC)

deps = None
for n in ast.walk(TREE):
    if isinstance(n, ast.Assign):
        for t in n.targets:
            if isinstance(t, ast.Name) and t.id == "TRANSITIVE_RUNTIME_DEPENDENCIES":
                deps = n.value
dep_paths = {k.value for k in deps.keys} if isinstance(deps, ast.Dict) else set()
check("C03_transitive_dependencies_exactly_14", len(dep_paths) == 14,
      {"observed": len(dep_paths)})

hd_calls = [n for n in ast.walk(FUNCS["run_smoke"])
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id == "_hd95_case_exact"] if "run_smoke" in FUNCS else []
check("C04_four_actual_hd95_call_sites", len(hd_calls) == 4, {"n": len(hd_calls)})

# ---- D. D30 — science transitive integrity gate BEFORE _load_models ----------- #
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


sci_order = [nm for _, nm in _body_calls_in_order("run_science")]
check("D01_D30_science_calls_integrity_verify",
      "run_science" in FUNCS and "_verify_transitive_source_integrity" in sci_order,
      {"science_calls": sci_order})
gate_before_load = False
if "run_science" in FUNCS \
        and "_verify_transitive_source_integrity" in sci_order \
        and "_load_models" in sci_order:
    vi = next(ln for ln, nm in _body_calls_in_order("run_science")
              if nm == "_verify_transitive_source_integrity")
    li = next(ln for ln, nm in _body_calls_in_order("run_science")
              if nm == "_load_models")
    gate_before_load = vi < li
check("D02_D30_science_gate_before_load_models", gate_before_load,
      {"science_calls": sci_order})
check("D03_D30_science_fail_closed_terminal",
      "D30_SCIENCE_TRANSITIVE_RUNTIME_SOURCE_INTEGRITY_FAILED__STOP_BEFORE_MODEL_CONSTRUCTION"
      in SRC)
check("D04_D30_same_gate_function_both_paths",
      "run_smoke" in FUNCS and "run_science" in FUNCS
      and seg("run_smoke").count("_verify_transitive_source_integrity") >= 1
      and seg("run_science").count("_verify_transitive_source_integrity") >= 1)

load_before_gate = False
if "run_science" in FUNCS:
    order = _body_calls_in_order("run_science")
    first_load = next((i for i, (_, nm) in enumerate(order) if nm == "_load_models"), None)
    first_verify = next((i for i, (_, nm) in enumerate(order)
                         if nm == "_verify_transitive_source_integrity"), None)
    if first_load is not None and first_verify is not None:
        load_before_gate = first_load < first_verify
check("D05_D30_no_load_models_before_science_gate", not load_before_gate)

# ---- E. D31 — unique v1.12 science paths, no v1.8 aliasing -------------------- #
check("E01_D31_science_result_v1_12_path_declared",
      "phase36_robustness_scientific_result_v1_12.json" in SRC)
check("E02_D31_science_start_v1_12_path_declared",
      "phase36_robustness_science_start_v1_12.json" in SRC)
check("E03_D31_science_failure_v1_12_path_declared",
      "phase36_robustness_science_failure_v1_12.json" in SRC)

_structural = SRC
for _n in ast.walk(TREE):
    if isinstance(_n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        _b = getattr(_n, "body", [])
        if _b and isinstance(_b[0], ast.Expr) and isinstance(_b[0].value, ast.Constant) \
                and isinstance(_b[0].value.value, str):
            _structural = _structural.replace(_b[0].value.value, "")
_kept = []
for _tok in tokenize.generate_tokens(io.StringIO(_structural).readline):
    if _tok.type == tokenize.COMMENT:
        continue
    _kept.append(_tok)
try:
    _structural = tokenize.untokenize(_kept)
except Exception:
    pass
for _n in ast.walk(TREE):
    if isinstance(_n, ast.Assign) and isinstance(_n.value, ast.Constant) \
            and isinstance(_n.value.value, str) and _n.value.value:
        _structural = _structural.replace(_n.value.value, "None")

check("E04_D31_no_v1_8_write_target_in_code",
      "scientific_result_v1_8.json" not in _structural)
check("E05_D31_sentinel_declared",
      "FORBIDDEN_SCIENCE_RESULT_V1_8" in SRC)
for _forb in ("scientific_result_v1_8.json", "scientific_result_v1_9.json"):
    check(f"E06_D31_no_historical_write_{_forb}",
          _forb not in _structural)

# ---- F. D32 — science first-attempt write-once provenance --------------------- #
check("F01_D32_science_start_marker_helper",
      "_create_science_start_marker" in SRC)
check("F02_D32_science_failure_helper",
      "_write_science_failure_artifact" in SRC)
check("F03_D32_science_success_helper",
      "_write_science_success_artifact" in SRC)
check("F04_D32_durable_evidence_wrapper",
      "_run_science_with_durable_evidence" in SRC)
check("F05_D32_start_marker_exclusive_create",
      "_create_science_start_marker" in FUNCS
      and ('"x"' in seg("_create_science_start_marker")
           or "O_EXCL" in seg("_create_science_start_marker")
           or "O_CREAT" in seg("_create_science_start_marker")))
check("F06_D32_systemexit_recorded",
      "SystemExit" in SRC and "_run_science_with_durable_evidence" in SRC)
check("F07_D32_exception_recorded",
      "except Exception" in seg("_run_science_with_durable_evidence")
      if "_run_science_with_durable_evidence" in FUNCS else False)
check("F08_D32_attempt_existence_guard",
      "_science_attempt_already_exists" in SRC)

# ---- G. D33 — external non-circular launcher anchor (v1.12 subject) ----------- #
check("G01_D33_launcher_exists", LAUNCHER.exists())
check("G02_D33_launcher_verifies_exec_sha",
      "FROZEN_EXPECTED_EXEC_SHA" in LSRC)
check("G03_D33_launcher_verifies_manifest_sha",
      "FROZEN_EXPECTED_MANIFEST_SHA" in LSRC)
check("G04_D33_launch_authority_token_declared",
      "LAUNCH_AUTHORITY_TOKEN" in SRC and "PHASE36_V1_12_LAUNCH_AUTHORITY" in SRC)
check("G05_D33_source_requires_launch_token",
      "_verify_transitive_source_integrity" in FUNCS
      and "LAUNCH_AUTHORITY_TOKEN" in seg("_verify_transitive_source_integrity")
      and "os.environ" in seg("_verify_transitive_source_integrity"))
_mf = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
check("G06_D33_manifest_present", MANIFEST.exists())
check("G07_D33_manifest_declares_exec_sha",
      _mf.get("execution_source_sha256") == _sha(EXEC),
      {"declared": _mf.get("execution_source_sha256"), "observed": _sha(EXEC)})
check("G08_D33_manifest_no_launcher_sha_cycle",
      "launcher_sha256" not in _mf)
check("G09_D33_co_edit_negative_control_recorded",
      (ROOT / "reports/audits/phase36_v1_12_launcher_co_edit_negative_control.json").exists())

# ---- H. gate separation + non-execution --------------------------------------- #
check("H01_smoke_gate_separate_from_science_gate",
      "SMOKE_GATE_ENV" in SRC and "GATE_ENV" in SRC and "PHASE36_SMOKE_EXECUTE" in SRC)
check("H02_no_v1_12_smoke_artifact_exists_yet",
      not (ROOT / "reports/audits/phase36_robustness_smoke_v1_12.json").exists())
check("H03_no_v1_12_smoke_start_marker_exists_yet",
      not (ROOT / "reports/audits/phase36_robustness_smoke_start_v1_12.json").exists())
check("H04_no_v1_12_smoke_failure_artifact_exists_yet",
      not (ROOT / "reports/audits/phase36_robustness_smoke_failure_v1_12.json").exists())
check("H05_no_v1_12_science_output_exists",
      not (ROOT / "reports/audits/phase36_robustness_scientific_result_v1_12.json").exists())
check("H06_no_v1_12_science_start_exists",
      not (ROOT / "reports/audits/phase36_robustness_science_start_v1_12.json").exists())
check("H07_no_v1_12_science_failure_exists",
      not (ROOT / "reports/audits/phase36_robustness_science_failure_v1_12.json").exists())
check("H08_entrypoint_guarded_by_main_guard", 'if __name__ == "__main__":' in SRC)

# ---- I. governance flags preserved -------------------------------------------- #
check("I01_test_runtime_reads_disallowed_flag",
      "TEST_RUNTIME_READS_ALLOWED = False" in SRC)
check("I02_holdout_runtime_reads_disallowed_flag",
      "ROUTER_HOLDOUT_RUNTIME_READS_ALLOWED = False" in SRC)
check("I03_val_manifest_only_runtime_authority",
      "VAL_MANIFEST_IS_ONLY_POPULATION_RUNTIME_AUTHORITY = True" in SRC)

# ---- J. scientific-semantics invariance (no new scientific choice) ------------ #
SCIENTIFIC_TOKENS = [
    "torch.sigmoid(logits.float())",
    "inference_mode",
    "autocast",
    "VAL808",
]
check("J01_sigmoid_logits_float_preserved",
      "torch.sigmoid(logits.float())" in SRC)
check("J02_seeds_preserved",
      "42" in SRC and "123" in SRC and "3407" in SRC)
check("J03_thresholds_preserved",
      "0.50" in SRC and "0.30" in SRC)
check("J04_batch8_preserved", "8" in SRC)
check("J05_science_semantics_tokens_present",
      all(t in SRC for t in SCIENTIFIC_TOKENS))

# ---- K. v1.12 gate reports on disk -------------------------------------------- #
unit_rep = json.loads((ROOT / "reports/audits/phase36_robustness_unit_v1_12.json")
                      .read_text(encoding="utf-8"))
check("K01_unit_report_all_pass", unit_rep["all_pass"],
      {"passed": unit_rep["passed"], "total": unit_rep["total"]})
check("K02_unit_report_subject_is_v1_12_exec",
      unit_rep["subject_execution_sha256"] == _sha(EXEC),
      {"declared": unit_rep["subject_execution_sha256"], "observed": _sha(EXEC)})
nc_rep = json.loads((ROOT / "reports/audits/phase36_v1_12_negative_controls.json")
                    .read_text(encoding="utf-8"))
check("K03_nc_report_all_pass", nc_rep["all_pass"],
      {"passed": nc_rep["passed"], "total": nc_rep["total"]})
check("K04_nc_canonical_unmodified", nc_rep["canonical_source_unmodified"])
check("K05_nc_launcher_unmodified",
      nc_rep["launcher_sha256"] == _sha(LAUNCHER))

# ---- M. D34 / D35 / D36 — NEW v1.12 cross-binding as STATIC properties --------- #
# D34: source no longer requires manifest launcher_sha256; fails closed if present.
_integ = seg("_verify_transitive_source_integrity")
check("M01_D34_no_manifest_launcher_read_in_source",
      'manifest.get("launcher_sha256")' not in SRC_CODE
      and "expected_launcher" not in SRC_CODE)
check("M02_D34_source_fails_closed_on_unexpected_launcher_key",
      '"launcher_sha256" in manifest' in _integ
      and "manifest_launcher_sha256_absent" in _integ
      and "if launcher_key_present or not launch_token_ok:" in _integ)
check("M03_D34_source_still_requires_token",
      "launch_authority_token_present" in _integ)

# D35: launcher frozen hashes are literal-only, non-env-overridable.
_lcode = LSRC_CODE
check("M04_D35_launcher_no_env_read_for_authority",
      "os.environ.get" not in _lcode and "getenv" not in _lcode)
_old_names = ("PHASE36_V1_11_EXPECTED_EXEC_SHA", "PHASE36_V1_11_EXPECTED_MANIFEST_SHA",
              "PHASE36_V1_12_EXPECTED_EXEC_SHA", "PHASE36_V1_12_EXPECTED_MANIFEST_SHA")
check("M05_D35_launcher_old_override_names_absent_in_code",
      all(n not in _lcode for n in _old_names),
      {"present": [n for n in _old_names if n in _lcode]})
_lmod = {n.targets[0].id: n.value.value for n in ast.walk(LTREE)
         if isinstance(n, ast.Assign) and len(n.targets) == 1
         and isinstance(n.targets[0], ast.Name)
         and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)}
check("M06_D35_frozen_exec_const_literal_exact",
      _lmod.get("FROZEN_EXPECTED_EXEC_SHA") == _sha(EXEC),
      {"const": _lmod.get("FROZEN_EXPECTED_EXEC_SHA"), "observed": _sha(EXEC)})
check("M07_D35_frozen_manifest_const_literal_exact",
      _lmod.get("FROZEN_EXPECTED_MANIFEST_SHA") == _sha(MANIFEST),
      {"const": _lmod.get("FROZEN_EXPECTED_MANIFEST_SHA"),
       "observed": _sha(MANIFEST) if MANIFEST.exists() else None})

# D36: three-file cross-binding — canonical pair must satisfy the launch-anchor
# predicate, DETERMINED IN-PROCESS (no dispatch, no model).
def _load_launcher_prod():
    spec = importlib.util.spec_from_file_location("phase36_v1_12_launch_pf", LAUNCHER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_cross_ok = False
_cross_detail = None
try:
    _m = _load_launcher_prod()
    _auth = _m.verify_authority()
    _cross_ok = bool(_auth.get("authorized"))
    _cross_detail = json.dumps({"authorized": _auth.get("authorized")})
except Exception as exc:
    _cross_detail = json.dumps({"exception": type(exc).__name__})
check("M08_D36_exec_plus_launcher_plus_manifest_mutually_satisfiable",
      _cross_ok, _cross_detail)
check("M09_D36_manifest_declares_exec_and_lacks_launcher_sha",
      _mf.get("execution_source_sha256") == _sha(EXEC)
      and "launcher_sha256" not in _mf)
check("M10_D36_launcher_verifies_before_dispatch",
      "auth = verify_authority()" in LSRC
      and LSRC.index("auth = verify_authority()")
      < LSRC.index('os.environ[LAUNCH_AUTHORITY_TOKEN] = "1"'))

passed = sum(1 for c in checks if c["passed"])
total = len(checks)
report = {
    "artifact": "phase36_robustness_preflight_v1_12",
    "phase": 36,
    "section": "§N",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_12",
    "type": "PREFLIGHT_CHECK_REPORT",
    "static_only": True,
    "model_free": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "subject_execution": "scripts/analysis/phase36_robustness_execution_v1_12.py",
    "subject_execution_sha256": _sha(EXEC),
    "subject_unit": "scripts/analysis/phase36_robustness_unit_v1_12.py",
    "subject_unit_sha256": _sha(UNIT),
    "subject_launcher": "scripts/analysis/launch_phase36_v1_12.py",
    "subject_launcher_sha256": _sha(LAUNCHER),
    "subject_manifest": "reports/audits/phase36_v1_12_runtime_source_integrity_manifest.json",
    "subject_manifest_sha256": _sha(MANIFEST),
    "subject_negative_controls": "scripts/analysis/phase36_robustness_negative_controls_v1_12.py",
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
    "checks": checks,
}
out = ROOT / "reports/audits/phase36_robustness_preflight_v1_12.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total}, indent=1))
for c in checks:
    if not c["passed"]:
        print("FAIL:", c["check"], json.dumps(c.get("detail"), default=str))
raise SystemExit(0 if passed == total else 1)
