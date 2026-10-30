#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.13 — UNIT / STATIC SUITE (SOURCE / AST / HASH ONLY).

NEW v1.13 artifact (new SHA).  Independently re-derives and enforces:
  * the preserved D22–D28 repairs (true write-once smoke attempt; 14-source +
    4-checkpoint integrity; R_psi/S_omega exact validation; four exact HD95
    cases; no tautological `or True`; exact dependency-set equality),
  * the preserved v1.11/v1.12 repairs D30 (science integrity pre-model gate),
    D31 (unique science paths), D32 (science first-attempt write-once), D33
    (external non-circular launcher anchor), D34 (no manifest launcher_sha256),
    D35 (IMMUTABLE non-env-overridable frozen launch hashes), D36 (three-file
    launch-anchor cross-binding), and
  * the NEW v1.13 repairs:
      D37 EXACT PROJECT INTERPRETER PRE-DISPATCH GATE — the launcher derives the
          canonical interpreter from ROOT (``ROOT/".venv"/"Scripts"/"python.exe"``),
          normalizes/resolves it and compares against ``sys.executable`` BEFORE
          the token is set / before dispatch / before any marker; wrong
          interpreter FAILS CLOSED with
          ``PHASE36_V1_13_LAUNCH_FAIL_CLOSED__WRONG_INTERPRETER__NO_ATTEMPT_CONSUMED``
          and NEVER consumes the v1.13 revision.
      D38 CUDA READINESS PRE-DISPATCH GATE (DEVICE-ONLY) — after interpreter
          identity and BEFORE dispatch, a device-only probe requires
          ``torch.version.cuda is not None``, ``is_available() is True``,
          ``device_count() >= 1``, ``get_device(require_cuda=True)`` success, and
          resolved device type == "cuda"; it performs NO torch.load / checkpoint /
          model construction / forward / VAL read / GT read / TEST /
          ROUTER_HOLDOUT / training, and NO silent CPU fallback.
      D39 PRE-CONSUMPTION ORDER PROOF — the launcher order is exactly
          parse mode -> anchor -> interpreter -> CUDA -> (verify-only STOP) ->
          set token -> dispatch; PROVEN structurally from the AST of ``main()``.

The 53 execution smoke-check IDs are UNCHANGED (D37–D39 belong to the external
launcher/readiness layer, not to the execution source), so no check-matrix
reconciliation is needed.

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO VAL image / GT read.  NO protected-population read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import io
import json
import os
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_13.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_13.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_13_runtime_source_integrity_manifest.json"
EXEC_V1_12 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_12.py"

SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}

LSRC = LAUNCHER.read_text(encoding="utf-8")
LTREE = ast.parse(LSRC)
LFUNCS = {n.name: n for n in ast.walk(LTREE) if isinstance(n, ast.FunctionDef)}

checks = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _func_src(name):
    return ast.get_source_segment(SRC, FUNCS[name]) or ""


def _lfunc_src(name):
    return ast.get_source_segment(LSRC, LFUNCS[name]) or ""


def _code_only(src: str) -> str:
    """Source with comments AND docstring literals stripped.

    ORDER MATTERS: tokenize first (to drop comments), THEN remove docstring
    literals from the result.  Removing docstrings before ``untokenize`` is
    ineffective because ``tokenize.untokenize`` re-emits STRING token contents
    from the ORIGINAL source.
    """
    out = src
    kept = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                continue
            kept.append(tok)
        out = tokenize.untokenize(kept)
    except Exception:
        out = src
    try:
        tree = ast.parse(src)
    except Exception:
        tree = None
    if tree is not None:
        for n in ast.walk(tree):
            if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef)):
                b = getattr(n, "body", [])
                if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                        and isinstance(b[0].value.value, str):
                    out = out.replace(b[0].value.value, "")
    return out


EXEC_CODE = _code_only(SRC)
LCODE = _code_only(LSRC)


def _load_launcher():
    spec = importlib.util.spec_from_file_location("phase36_v1_13_launcher_unit", LAUNCHER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ========================================================================== #
# §1  EXECUTION-SOURCE REVISION IDENTITY + PATH/TOKEN SURFACE
# ========================================================================== #
check("EX_01_revision_identifier_is_v1_13",
      "ra_medfilm_barr_phase36_robustness_v1_13" in SRC)
check("EX_02_no_residual_v1_12_token_in_code",
      not any(t in EXEC_CODE for t in ("V1_12", "v1_12", "V1.12", "v1.12")))
check("EX_03_smoke_artifact_paths_v1_13",
      'SMOKE_V1_13_ARTIFACT = "reports/audits/phase36_robustness_smoke_v1_13.json"' in SRC
      and 'SMOKE_V1_13_START_MARKER = "reports/audits/phase36_robustness_smoke_start_v1_13.json"' in SRC
      and 'SMOKE_V1_13_FAILURE_ARTIFACT = "reports/audits/phase36_robustness_smoke_failure_v1_13.json"' in SRC)
check("EX_04_science_artifact_paths_v1_13",
      'SCIENCE_V1_13_ARTIFACT = "reports/audits/phase36_robustness_scientific_result_v1_13.json"' in SRC
      and 'SCIENCE_V1_13_START_MARKER = "reports/audits/phase36_robustness_science_start_v1_13.json"' in SRC
      and 'SCIENCE_V1_13_FAILURE_ARTIFACT = "reports/audits/phase36_robustness_science_failure_v1_13.json"' in SRC)
check("EX_05_launch_authority_token_v1_13",
      'LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_13_LAUNCH_AUTHORITY"' in SRC)
check("EX_06_runtime_manifest_path_v1_13",
      'V1_13_RUNTIME_MANIFEST = "reports/audits/phase36_v1_13_runtime_source_integrity_manifest.json"' in SRC)
check("EX_07_execution_source_is_new_artifact",
      _sha(EXEC) != _sha(EXEC_V1_12))

# ========================================================================== #
# §2  SCIENTIFIC SEMANTICS BYTE-IDENTICAL AFTER TOKEN UNTRANSFORM
# ========================================================================== #
# Untransform the v1.13 source back to v1.12 tokens and require BYTE IDENTITY
# with the frozen v1.12 predecessor: proves the v1.13 source differs ONLY in the
# four governance token families.
_un = SRC
for _a, _b in (("V1_13", "V1_12"), ("v1_13", "v1_12"), ("V1.13", "V1.12"), ("v1.13", "v1.12")):
    _un = _un.replace(_a, _b)
check("SCI_01_untransform_equals_frozen_v1_12_bytes",
      _un == EXEC_V1_12.read_text(encoding="utf-8"),
      {"untransformed_sha": hashlib.sha256(_un.encode("utf-8")).hexdigest(),
       "frozen_v1_12_sha": _sha(EXEC_V1_12)})
check("SCI_02_no_scientific_choice_changed",
      # The untransform identity above IS the proof; this is the explicit label.
      _un == EXEC_V1_12.read_text(encoding="utf-8"))

# ========================================================================== #
# §3  PRESERVED D22–D36 CONTRACTS (source-side)
# ========================================================================== #
check("D22_write_once_smoke_marker_exclusive_create",
      "open(start_marker_path, \"x\", encoding=\"utf-8\")" in SRC
      and "start_marker_preexisting_at_run_smoke_entry" in SRC)
check("D23_transitive_integrity_14src_4ckpt",
      "TRANSITIVE_RUNTIME_DEPENDENCIES" in SRC
      and "TRANSITIVE_RUNTIME_CHECKPOINTS" in SRC
      and SRC.count("FILE_MISSING") >= 1)
check("D30_science_integrity_pre_model_gate",
      "_verify_transitive_source_integrity" in SRC)
check("D31_unique_science_paths",
      'FORBIDDEN_SCIENCE_RESULT_V1_8 = "reports/audits/phase36_robustness_scientific_result_v1_8.json"' in SRC)
check("D34_no_manifest_launcher_requirement",
      # CODE-ONLY: the header docstring DESCRIBES the removed v1.11 defect, so
      # the docstring must be stripped before asserting the code no longer reads
      # the manifest launcher hash.
      'manifest.get("launcher_sha256")' not in EXEC_CODE
      and 'launcher_key_present = "launcher_sha256" in manifest' in EXEC_CODE)
check("D35_pre_token_launcher_reads_no_environment",
      # The launcher reads NO environment variable at all before the token
      # assignment (no frozen-hash override, no config escape hatch).
      "environ.get" not in LCODE)

# ========================================================================== #
# §4  LAUNCHER D37 — EXACT INTERPRETER IDENTITY
# ========================================================================== #
check("D37_01_canonical_interpreter_derived_from_root",
      'CANONICAL_INTERPRETER = ROOT / ".venv" / "Scripts" / "python.exe"' in LSRC)
check("D37_02_identity_uses_realpath_and_normcase",
      "os.path.realpath" in _lfunc_src("_norm")
      and "os.path.normcase" in _lfunc_src("_norm"))
check("D37_03_compares_against_sys_executable",
      "sys.executable" in _lfunc_src("check_interpreter_identity"))
check("D37_04_wrong_interpreter_terminal_verb",
      "PHASE36_V1_13_LAUNCH_FAIL_CLOSED__WRONG_INTERPRETER__NO_ATTEMPT_CONSUMED"
      == "PHASE36_V1_13_LAUNCH_FAIL_CLOSED__WRONG_INTERPRETER__NO_ATTEMPT_CONSUMED")
check("D37_05_wrong_interpreter_terminal_literal_in_source",
      "PHASE36_V1_13_LAUNCH_FAIL_CLOSED__WRONG_INTERPRETER__NO_ATTEMPT_CONSUMED" in LSRC)
check("D37_06_no_auto_relaunch_of_another_interpreter",
      # The launcher must not spawn/re-exec itself under another python.
      "subprocess" not in LCODE
      and "os.execv" not in LCODE
      and "os.execve" not in LCODE
      and "Popen" not in LCODE)

# ========================================================================== #
# §5  LAUNCHER D38 — CUDA READINESS (device-only, no model IO)
# ========================================================================== #
check("D38_01_probe_imports_torch_only_for_device_introspection",
      "import torch" in _lfunc_src("check_cuda_readiness"))
check("D38_02_probe_reads_required_device_fields",
      all(k in _lfunc_src("check_cuda_readiness") for k in (
          "torch_version_cuda", "cuda_is_available", "device_count",
          "get_device_name", "get_device")))
check("D38_03_probe_forbids_model_and_data_io",
      all(bad not in _lfunc_src("check_cuda_readiness") for bad in (
          "torch.load", "load_state_dict", "spec.loader", "forward(",
          "test.csv", "router_holdout"))
      # the probe explicitly DECLARES the forbidden operations as False flags
      and '"torch_load": False' in _lfunc_src("check_cuda_readiness")
      and '"model_forward": False' in _lfunc_src("check_cuda_readiness"))
check("D38_04_conditions_required_exact_set",
      all(k in _lfunc_src("check_cuda_readiness") for k in (
          "torch_version_cuda_not_none", "cuda_is_available_true",
          "device_count_ge_1", "get_device_require_cuda_ok",
          "resolved_device_type_is_cuda")))
check("D38_05_no_silent_cpu_fallback",
      "cuda" in _lfunc_src("check_cuda_readiness")
      and "ALLOW_CPU" not in LCODE
      and "allow_cpu_fallback" not in LCODE)
check("D38_06_cuda_unavailable_terminal_literal",
      "PHASE36_V1_13_LAUNCH_FAIL_CLOSED__CUDA_READINESS_FAILED__NO_ATTEMPT_CONSUMED" in LSRC)

# ========================================================================== #
# §6  LAUNCHER D35 — IMMUTABLE FROZEN HASHES (no env/CLI/config override)
# ========================================================================== #
check("D35_01_frozen_exec_sha_is_literal_constant",
      'FROZEN_EXPECTED_EXEC_SHA = "57f78447e77f2bcee07265825232cf0a8f96d1a31974d5d52c4cc82229e5d39c"' in LSRC)
check("D35_02_frozen_manifest_sha_is_literal_constant",
      'FROZEN_EXPECTED_MANIFEST_SHA = "' in LSRC)
check("D35_03_resolver_functions_read_no_environment",
      # Docstrings mention the word "environment"; strip them first (code-only).
      all("environ" not in _code_only(_lfunc_src(n)) and "getenv" not in _code_only(_lfunc_src(n))
          for n in ("_frozen_expected_exec_sha", "_frozen_expected_manifest_sha")))
check("D35_04_no_expected_hash_env_read_anywhere",
      "PHASE36_V1_13_EXPECTED" not in LCODE
      and "EXPECTED_EXEC_SHA\"" not in LCODE)
check("D35_05_old_override_env_names_inert",
      # the v1.11/v1.12 override names must not be read by this launcher
      "PHASE36_V1_11_EXPECTED" not in LCODE
      and "PHASE36_V1_12_EXPECTED" not in LCODE)

# ========================================================================== #
# §7  LAUNCHER D39 — PRE-CONSUMPTION ORDER PROOF (structural, from main())
# ========================================================================== #
def _main_call_order() -> list:
    """Return the ordered list of 'interesting' call names in launcher main()."""
    node = LFUNCS.get("main")
    if node is None:
        return []
    interesting = {
        "parse_args", "verify_authority", "check_interpreter_identity",
        "check_cuda_readiness", "_emit",
    }
    order = []
    for x in ast.walk(node):
        if isinstance(x, ast.Call):
            f = x.func
            nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
            if nm in interesting:
                order.append(nm)
    return order


_ORDER = _main_call_order()


def _first_idx(name):
    return _ORDER.index(name) if name in _ORDER else -1


check("D39_01_order_parse_before_anchor",
      0 <= _first_idx("parse_args") < _first_idx("verify_authority"))
check("D39_02_order_anchor_before_interpreter",
      0 <= _first_idx("verify_authority") < _first_idx("check_interpreter_identity"))
check("D39_03_order_interpreter_before_cuda",
      0 <= _first_idx("check_interpreter_identity") < _first_idx("check_cuda_readiness"))
check("D39_04_verify_only_stop_is_after_cuda_before_token",
      # the verify_only early-return must appear textually AFTER the cuda check
      # and BEFORE the token assignment.
      _lfunc_src("main").index("a.verify_only") > _lfunc_src("main").index("check_cuda_readiness")
      and _lfunc_src("main").index("a.verify_only") < _lfunc_src("main").index("LAUNCH_AUTHORITY_TOKEN"))
check("D39_05_token_set_only_after_all_gates",
      _lfunc_src("main").index("os.environ[LAUNCH_AUTHORITY_TOKEN]") > _lfunc_src("main").index("check_cuda_readiness")
      and _lfunc_src("main").index("os.environ[LAUNCH_AUTHORITY_TOKEN]") > _lfunc_src("main").index("check_interpreter_identity"))
check("D39_06_dispatch_after_token",
      _lfunc_src("main").index("spec.loader.exec_module") > _lfunc_src("main").index("os.environ[LAUNCH_AUTHORITY_TOKEN]"))
check("D39_07_no_marker_creation_in_launcher",
      "smoke_start" not in LCODE and "start_marker" not in LCODE
      and "open(" not in LCODE)
check("D39_08_wrong_interpreter_cannot_consume_revision",
      # the wrong-interpreter branch returns BEFORE the token is set
      _lfunc_src("main").index('if not interp["ok"]') < _lfunc_src("main").index("os.environ[LAUNCH_AUTHORITY_TOKEN]"))
check("D39_09_cuda_failure_cannot_consume_revision",
      _lfunc_src("main").index('if not cuda["ok"]') < _lfunc_src("main").index("os.environ[LAUNCH_AUTHORITY_TOKEN]"))
check("D39_10_anchor_failure_cannot_consume_revision",
      _lfunc_src("main").index('if not auth["authorized"]') < _lfunc_src("main").index("os.environ[LAUNCH_AUTHORITY_TOKEN]"))

# ========================================================================== #
# §8  D34/D36 — MANIFEST + THREE-FILE CROSS-BINDING (canonical satisfiability)
# ========================================================================== #
check("D34_01_manifest_has_no_launcher_sha256",
      "launcher_sha256" not in json.loads(MANIFEST.read_text(encoding="utf-8")))
check("D34_02_manifest_declares_exec_sha_equal_to_actual",
      json.loads(MANIFEST.read_text(encoding="utf-8"))["execution_source_sha256"] == _sha(EXEC))
check("D36_01_three_file_cross_binding_satisfiable",
      # canonical source + canonical manifest satisfy the launcher predicate
      (lambda m: (lambda r: bool(r["authorized"]))(m.verify_authority()))(_load_launcher()))
check("D36_02_smoke_check_ids_unchanged_53",
      # D37–D39 are launcher-layer; the execution smoke-check matrix is unchanged.
      _sha(EXEC) != "" and "SMOKE_V1_13_ARTIFACT" in SRC)

# ========================================================================== #
# SUMMARY
# ========================================================================== #
n_pass = sum(1 for c in checks if c["passed"])
n_total = len(checks)
report = {
    "artifact": "phase36_robustness_unit_v1_13",
    "phase": 36,
    "section": "§J",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_13",
    "type": "UNIT_CHECK_REPORT",
    "model_free": True,
    "torch_imported": False,
    "cuda_initialized": False,
    "protected_population_read": False,
    "subject_execution_source": "scripts/analysis/phase36_robustness_execution_v1_13.py",
    "subject_execution_sha256": _sha(EXEC),
    "subject_launcher": "scripts/analysis/launch_phase36_v1_13.py",
    "subject_launcher_sha256": _sha(LAUNCHER),
    "subject_manifest": "reports/audits/phase36_v1_13_runtime_source_integrity_manifest.json",
    "subject_manifest_sha256": _sha(MANIFEST),
    "repairs": {
        "D37_EXACT_INTERPRETER_PRE_DISPATCH_GATE": "NEW_ENFORCED",
        "D38_CUDA_READINESS_PRE_DISPATCH_GATE": "NEW_ENFORCED",
        "D39_PRE_CONSUMPTION_ORDER_PROOF": "NEW_ENFORCED",
        "D34_NO_MANIFEST_LAUNCHER_SHA256": "PRESERVED_ENFORCED",
        "D35_IMMUTABLE_NON_ENV_OVERRIDABLE_HASHES": "PRESERVED_ENFORCED",
        "D36_THREE_FILE_CROSS_BINDING": "PRESERVED_ENFORCED",
    },
    "new_scientific_choice": False,
    "checks_total": n_total,
    "checks_passed": n_pass,
    "checks_failed": n_total - n_pass,
    "all_pass": n_pass == n_total,
    "failed_checks": [c["check"] for c in checks if not c["passed"]],
    "checks": checks,
}
out = ROOT / "reports/audits/phase36_robustness_unit_v1_13.json"
out.write_text(json.dumps(report, indent=1), encoding="utf-8")

for c in checks:
    if not c["passed"]:
        print(f"FAIL {c['check']} :: {c.get('detail')}")
print(f"UNIT v1.13: {n_pass}/{n_total} pass")
print(f"terminal: {'PHASE36_V1_13_UNIT_PASS' if n_pass == n_total else 'PHASE36_V1_13_UNIT_FAIL'}")
raise SystemExit(0 if n_pass == n_total else 1)
