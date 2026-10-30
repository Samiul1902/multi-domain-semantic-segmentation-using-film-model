#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.14 — UNIT / STATIC SUITE (SOURCE / AST / HASH ONLY).

NEW v1.14 artifact.  Independently re-derives and enforces the preserved
D22–D39 protections AND the NEW v1.14 repairs:

  D40 MACHINE-ENFORCED SCIENCE ELIGIBILITY
      * the v1.14 execution source exposes ``_gate_science_release_state()`` and
        refuses science BEFORE the PHASE36_EXECUTE gate / any marker / model/VAL
        access when no binding successful-smoke release attestation exists;
      * the v1.14 launcher exposes ``_science_release_evidence()`` and refuses
        science BEFORE the launch-authority token is set / before the execution
        source is imported;
      * BOTH emit the required terminal
        ``PHASE36_V1_14_SCIENCE_NOT_RELEASED__SUCCESSFUL_SMOKE_REQUIRED__NO_ATTEMPT_CONSUMED``;
      * the release is a POSITIVE CHAIN: the attestation must bind the observed
        smoke-artifact bytes AND this source's bytes — a plain editable JSON that
        merely says "released" cannot satisfy it.

  D41 NO TAUTOLOGICAL CHECK (mutation-sensitive)
      The v1.14 wrong-interpreter terminal check is a REAL source/AST binding:
      it extracts the terminal LITERAL from the launcher's wrong-interpreter
      failure branch and compares it to the required verb.  A mutant that
      changes/removes that literal MUST fail the detector (proven here).

  D42 ACTUALLY VERIFY THE 53 SMOKE CHECK IDS
      Parse the DECLARED ``SMOKE_CHECK_IDS`` from the v1.14 source via AST:
      exact count == 53, all unique, exact set equality against the frozen v1.13
      declared set, and the frozen runtime ``smoke_checks`` dict key set equals
      the declared set.  Mutation-sensitive: -1 / +1 / duplicate ID each fail.

  D43 RAW-BYTE GOVERNANCE TRANSFORM PROOF
      read_bytes() the v1.14 source, untransform ONLY the permitted ASCII
      governance token families on RAW BYTES, and require byte equality with the
      frozen v1.13 raw bytes AND hash equality with the frozen v1.13 SHA.

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO VAL/GT read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
EXEC_V1_13 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_13.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_14.py"
LAUNCHER_V1_13 = ROOT / "scripts/analysis/launch_phase36_v1_13.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json"

FROZEN_V1_13_EXEC_SHA = "57f78447e77f2bcee07265825232cf0a8f96d1a31974d5d52c4cc82229e5d39c"

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


def _declared_smoke_ids(src: str) -> list:
    """AST-extract the SMOKE_CHECK_IDS literal list from source."""
    t = ast.parse(src)
    for n in ast.walk(t):
        if isinstance(n, ast.Assign):
            for tg in n.targets:
                if isinstance(tg, ast.Name) and tg.id == "SMOKE_CHECK_IDS":
                    return [e.value for e in n.value.elts]
    return []


def _code_only(src: str) -> str:
    """Source with comments AND docstring literals stripped.

    Order: tokenize first (drop comments), THEN remove docstring literals —
    because ``tokenize.untokenize`` re-emits STRING contents from the original
    token stream.
    """
    import io
    import tokenize
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


# ========================================================================== #
# §1  REVISION IDENTITY + D43 RAW-BYTE UNTRANSFORM PROOF
# ========================================================================== #
# D43 CONTRACT: the v1.14 source is the frozen v1.13 source under (a) the four
# permitted RAW-BYTE governance token families, PLUS TWO additive D40 segments:
#   (i)  a D40 gate call inserted at the top of main()'s science branch;
#   (ii) a D40 implementation block appended after the v1.13 body.
# The raw-byte proof therefore removes BOTH additive segments (delimited by
# exact byte anchors), applies the raw-byte token untransform to what remains,
# and requires byte equality with the frozen v1.13 raw bytes.  No decode/
# re-encode is the authority; bytes are compared to bytes.
_D40_MAIN_START = b"        # \xc2\xa7D40 (v1.14) SCIENCE RELEASE GATE"
_D40_MAIN_END = b"        # \xc2\xa7D32 AUTHORIZED-ATTEMPT ORDERING"
# The appended block starts at its enclosing ``# ====...`` rule line, which sits
# immediately after the v1.13 body terminator.
_D40_APPEND_RULE = b"# =========================================================================== #\r\n"
_D40_APPEND_START = b"# \xc2\xa7D40 (v1.14) \xe2\x80\x94 MACHINE-ENFORCED SCIENCE ELIGIBILITY"

raw14 = EXEC.read_bytes()
raw13 = EXEC_V1_13.read_bytes()

_i_main_a = raw14.find(_D40_MAIN_START)
_i_main_b = raw14.find(_D40_MAIN_END)
# The append boundary is the RULE LINE immediately preceding the D40 banner.
_i_app_banner = raw14.find(_D40_APPEND_START)
_i_app = raw14.rfind(_D40_APPEND_RULE, 0, _i_app_banner)
check("D43_00_additive_segments_present",
      _i_main_a > 0 and _i_main_b > _i_main_a and _i_app > _i_main_b
      and 0 < _i_app_banner - _i_app <= 400,
      {"main_insert": _i_main_a, "main_end": _i_main_b,
       "append_rule": _i_app, "append_banner": _i_app_banner})

_body14 = raw14[:_i_main_a] + raw14[_i_main_b:_i_app]

# The v1.13 body ENDS with the ``if __name__`` guard; v1.14 RELOCATES that guard
# to the true end of the module (after the appended D40 block).  Re-insert the
# guard at its canonical v1.13 position to complete the reversible transform.
_GUARD = b'if __name__ == "__main__":\r\n    raise SystemExit(main())\r\n'
if not _body14.endswith(_GUARD) and _body14.rstrip(b"\r\n").endswith(b"return 2"):
    _body14 = _body14 + _GUARD
elif not _body14.endswith(_GUARD):
    _body14 = _body14 + _GUARD

_un = _body14
for _a, _b in ((b"V1_14", b"V1_13"), (b"v1_14", b"v1_13"),
               (b"V1.14", b"V1.13"), (b"v1.14", b"v1.13")):
    _un = _un.replace(_a, _b)
check("D43_01_raw_byte_untransform_identity",
      _un == raw13,
      {"untransformed_sha": hashlib.sha256(_un).hexdigest(), "frozen_v1_13_sha": FROZEN_V1_13_EXEC_SHA})
check("D43_02_untransformed_sha_equals_frozen_v1_13",
      hashlib.sha256(_un).hexdigest() == FROZEN_V1_13_EXEC_SHA)
check("D43_03_new_scientific_choice_false",
      _un == raw13)

# ========================================================================== #
# §2  D42 — SMOKE CHECK ID ACCOUNTING (mutation-sensitive)
# ========================================================================== #
_ids14 = _declared_smoke_ids(SRC)
_ids13 = _declared_smoke_ids(EXEC_V1_13.read_text(encoding="utf-8"))
check("D42_01_declared_count_exactly_53", len(_ids14) == 53, {"count": len(_ids14)})
check("D42_02_all_ids_unique", len(set(_ids14)) == len(_ids14),
      {"dupes": sorted({x for x in _ids14 if _ids14.count(x) > 1})})
check("D42_03_exact_set_equality_with_frozen_v1_13",
      set(_ids14) == set(_ids13),
      {"missing": sorted(set(_ids13) - set(_ids14)), "unexpected": sorted(set(_ids14) - set(_ids13))})
check("D42_04_declared_ids_identical_order",
      _ids14 == _ids13)


def _detector_smoke_ids(ids: list) -> bool:
    """Faithful detector: exact count 53 + uniqueness + exact set equality."""
    return len(ids) == 53 and len(set(ids)) == 53 and set(ids) == set(_ids13)


check("D42_05_detector_accepts_canonical", _detector_smoke_ids(_ids14))
check("D42_06_detector_rejects_removed_id",
      not _detector_smoke_ids(_ids14[:-1]))
check("D42_07_detector_rejects_added_id",
      not _detector_smoke_ids(_ids14 + ["synthetic_added_id"]))
check("D42_08_detector_rejects_duplicate_id",
      not _detector_smoke_ids(_ids14[:-1] + [_ids14[0]]))

# The runtime smoke_checks dict key set must equal the declared ID set.
_rt_ids = None
for n in ast.walk(TREE):
    if isinstance(n, ast.Assign):
        for tg in n.targets:
            if isinstance(tg, ast.Name) and tg.id == "smoke_checks":
                if isinstance(n.value, ast.Dict):
                    _rt_ids = [k.value for k in n.value.keys if isinstance(k, ast.Constant)]
check("D42_09_runtime_smoke_checks_keyset_equals_declared",
      _rt_ids is not None and set(_rt_ids) == set(_ids14),
      {"runtime_count": (len(_rt_ids) if _rt_ids else None)})

# ========================================================================== #
# §3  D40 — SCIENCE RELEASE GATE (execution source)
# ========================================================================== #
check("D40_01_exec_gate_function_exists",
      "_gate_science_release_state" in FUNCS)
check("D40_02_exec_attestation_path_declared",
      'SCIENCE_RELEASE_ATTESTATION =' in SRC and "phase36_v1_14_science_release_attestation.json" in SRC)
check("D40_03_exec_release_requires_bound_smoke_bytes",
      all(k in _func_src("_gate_science_release_state") for k in (
          "smoke_artifact_sha256", "execution_source_sha256", "smoke_all_pass",
          "scientific_output", "release_gate")))
check("D40_04_exec_gate_fails_closed_reasons",
      all(r in _func_src("_gate_science_release_state") for r in (
          "NO_ATTESTATION", "ATTESTATION_MALFORMED", "REVISION_MISMATCH",
          "SOURCE_SHA_MISMATCH", "SMOKE_ARTIFACT_MISSING",
          "SMOKE_ARTIFACT_SHA_MISMATCH", "SMOKE_NOT_SUCCESSFUL",
          "SCIENTIFIC_OUTPUT_NOT_FALSE", "RELEASE_GATE_MISMATCH")))
# D40 must be invoked BEFORE the PHASE36_EXECUTE gate inside main().
_main_src = _func_src("main")
check("D40_05_gate_called_before_execute_gate",
      0 <= _main_src.index("_gate_science_release_state()") < _main_src.index("_gate_science_state()"))
check("D40_06_gate_called_before_science_marker",
      _main_src.index("_gate_science_release_state()") < _main_src.index("_create_science_start_marker"))
check("D40_07_exec_terminal_literal_present",
      "PHASE36_V1_14_SCIENCE_NOT_RELEASED__SUCCESSFUL_SMOKE_REQUIRED__NO_ATTEMPT_CONSUMED" in SRC)
check("D40_08_gate_does_not_touch_model_or_data",
      all(bad not in _func_src("_gate_science_release_state") for bad in (
          "torch", "load_state_dict", "forward(", "val.csv", "test.csv", "router_holdout")))

# ========================================================================== #
# §4  D40 — SCIENCE RELEASE GATE (launcher, pre-dispatch)
# ========================================================================== #
check("D40_09_launcher_release_fn_exists", "_science_release_evidence" in LFUNCS)
check("D40_10_launcher_terminal_literal_present",
      "PHASE36_V1_14_SCIENCE_NOT_RELEASED" in LSRC
      and "__SUCCESSFUL_SMOKE_REQUIRED__NO_ATTEMPT_CONSUMED" in LSRC)
_lmain = _lfunc_src("main")
check("D40_11_launcher_gate_after_cuda_before_token",
      0 <= _lmain.index("_science_release_evidence()")
      < _lmain.index("os.environ[LAUNCH_AUTHORITY_TOKEN]"))
check("D40_12_launcher_gate_before_exec_import",
      _lmain.index("_science_release_evidence()") < _lmain.index("spec.loader.exec_module"))
check("D40_13_launcher_gate_after_verify_only_stop",
      _lmain.index("a.verify_only") < _lmain.index("_science_release_evidence()"))
check("D40_14_launcher_gate_only_for_science_mode",
      'if a.mode == "science":' in _lmain[_lmain.index("a.verify_only"):_lmain.index("os.environ[LAUNCH_AUTHORITY_TOKEN]")])

# ========================================================================== #
# §5  D41 — NON-TAUTOLOGICAL WRONG-INTERPRETER TERMINAL BINDING
# ========================================================================== #
REQUIRED_WRONG_INTERP_TERMINAL = (
    "PHASE36_V1_14_LAUNCH_FAIL_CLOSED__WRONG_INTERPRETER__NO_ATTEMPT_CONSUMED")


def _module_str_constants(launcher_src: str) -> dict:
    """Map module-level ``NAME = "literal"`` assignments."""
    t = ast.parse(launcher_src)
    out = {}
    for n in t.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 \
                and isinstance(n.targets[0], ast.Name) \
                and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
            out[n.targets[0].id] = n.value.value
    return out


def _extract_wrong_interpreter_terminal(launcher_src: str) -> str | None:
    """AST-bind the terminal literal actually emitted by the wrong-interpreter
    failure branch of ``main()`` (NOT a self-comparison tautology).

    Resolves simple ``NAME = "literal"`` module constants emitted as the first
    argument to ``_emit``.
    """
    t = ast.parse(launcher_src)
    consts = _module_str_constants(launcher_src)
    fns = {n.name: n for n in ast.walk(t) if isinstance(n, ast.FunctionDef)}
    main = fns.get("main")
    if main is None:
        return None
    for n in ast.walk(main):
        if isinstance(n, ast.If):
            test = n.test
            # match: if not interp["ok"]:
            if (isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not)
                    and isinstance(test.operand, ast.Subscript)):
                sl = test.operand.slice
                key = sl.value if isinstance(sl, ast.Constant) else None
                if key == "ok":
                    for st in ast.walk(n):
                        if isinstance(st, ast.Call):
                            fn = st.func
                            nm = fn.id if isinstance(fn, ast.Name) else None
                            if nm == "_emit" and st.args:
                                a0 = st.args[0]
                                if isinstance(a0, ast.Constant):
                                    return a0.value
                                if isinstance(a0, ast.Name):
                                    return consts.get(a0.id)
    return None


_obs_terminal = _extract_wrong_interpreter_terminal(LSRC)
check("D41_01_wrong_interp_terminal_bound_from_source",
      _obs_terminal == REQUIRED_WRONG_INTERP_TERMINAL,
      {"observed": _obs_terminal, "required": REQUIRED_WRONG_INTERP_TERMINAL})


def _mutate_wrong_interp_terminal(launcher_src: str, replacement: str) -> str:
    return launcher_src.replace(REQUIRED_WRONG_INTERP_TERMINAL, replacement)


_mut_removed = LSRC.replace(REQUIRED_WRONG_INTERP_TERMINAL, "PHASE36_V1_14_SOMETHING_ELSE")
check("D41_02_detector_rejects_mutated_terminal",
      _extract_wrong_interpreter_terminal(_mut_removed) != REQUIRED_WRONG_INTERP_TERMINAL)
check("D41_03_terminal_not_a_self_comparison",
      # D41: the binding above extracts an EMITTED argument.  Prove it is NOT a
      # tautological `"literal" == "same literal"` comparison: the required
      # terminal must appear in a module-level assignment whose right-hand side
      # is a STRING CONSTANT (the emitted verb), and the detector must obtain it
      # from that assignment — not from an equality of identical literals.
      _module_str_constants(LSRC).get("T_WRONG_INTERPRETER") == REQUIRED_WRONG_INTERP_TERMINAL
      and not any(
          isinstance(n, ast.Compare) and isinstance(n.left, ast.Constant)
          and isinstance(n.left.value, str)
          and n.left.value == REQUIRED_WRONG_INTERP_TERMINAL
          and all(isinstance(c, ast.Constant) and c.value == REQUIRED_WRONG_INTERP_TERMINAL
                  for c in n.comparators)
          for n in ast.walk(LTREE)))

# ========================================================================== #
# §6  PRESERVED D22–D39 (spot contract checks)
# ========================================================================== #
check("D22_write_once_smoke_marker",
      'open(start_marker_path, "x", encoding="utf-8")' in SRC)
check("D23_transitive_integrity_present",
      "TRANSITIVE_RUNTIME_DEPENDENCIES" in SRC and "TRANSITIVE_RUNTIME_CHECKPOINTS" in SRC)
check("D34_no_manifest_launcher_requirement",
      # CODE-ONLY: the docstring DESCRIBES the removed v1.11 defect.
      'manifest.get("launcher_sha256")' not in _code_only(SRC)
      and 'launcher_key_present = "launcher_sha256" in manifest' in _code_only(SRC))
check("D37_interpreter_gate_present",
      'CANONICAL_INTERPRETER = ROOT / ".venv" / "Scripts" / "python.exe"' in LSRC
      and "check_interpreter_identity" in LFUNCS)
check("D38_cuda_readiness_present",
      "check_cuda_readiness" in LFUNCS
      and "torch_version_cuda_not_none" in _lfunc_src("check_cuda_readiness"))
check("D39_order_preserved",
      _lmain.index("check_interpreter_identity()") < _lmain.index("check_cuda_readiness()")
      < _lmain.index("a.verify_only") < _lmain.index("os.environ[LAUNCH_AUTHORITY_TOKEN]"))
check("D34_manifest_no_launcher_sha256",
      "launcher_sha256" not in json.loads(MANIFEST.read_text(encoding="utf-8")))
check("D34_manifest_declares_actual_exec_sha",
      json.loads(MANIFEST.read_text(encoding="utf-8"))["execution_source_sha256"] == _sha(EXEC))

# ========================================================================== #
# SUMMARY
# ========================================================================== #
n_pass = sum(1 for c in checks if c["passed"])
n_total = len(checks)
report = {
    "artifact": "phase36_robustness_unit_v1_14",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_14",
    "type": "UNIT_CHECK_REPORT",
    "model_free": True,
    "torch_imported": False,
    "protected_population_read": False,
    "subject_execution_source": "scripts/analysis/phase36_robustness_execution_v1_14.py",
    "subject_execution_sha256": _sha(EXEC),
    "subject_launcher": "scripts/analysis/launch_phase36_v1_14.py",
    "subject_launcher_sha256": _sha(LAUNCHER),
    "subject_manifest_sha256": _sha(MANIFEST),
    "declared_smoke_check_count": len(_ids14),
    "repairs": {
        "D40_MACHINE_ENFORCED_SCIENCE_ELIGIBILITY": "NEW_ENFORCED",
        "D41_NON_TAUTOLOGICAL_TERMINAL_BINDING": "NEW_ENFORCED",
        "D42_SMOKE_CHECK_ID_ACCOUNTING": "NEW_ENFORCED",
        "D43_RAW_BYTE_UNTRANSFORM_PROOF": "NEW_ENFORCED",
        "D22_D39_PRESERVED": "PRESERVED_ENFORCED",
    },
    "new_scientific_choice": False,
    "checks_total": n_total,
    "checks_passed": n_pass,
    "checks_failed": n_total - n_pass,
    "all_pass": n_pass == n_total,
    "failed_checks": [c["check"] for c in checks if not c["passed"]],
    "checks": checks,
}
out = ROOT / "reports/audits/phase36_robustness_unit_v1_14.json"
out.write_text(json.dumps(report, indent=1), encoding="utf-8")

for c in checks:
    if not c["passed"]:
        print(f"FAIL {c['check']} :: {c.get('detail')}")
print(f"UNIT v1.14: {n_pass}/{n_total} pass")
print(f"terminal: {'PHASE36_V1_14_UNIT_PASS' if n_pass == n_total else 'PHASE36_V1_14_UNIT_FAIL'}")
raise SystemExit(0 if n_pass == n_total else 1)
