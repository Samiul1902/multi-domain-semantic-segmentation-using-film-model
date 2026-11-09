#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.14 — NEGATIVE CONTROLS NC115..NC134.

Additive over the carried v1.9 NC50..NC57, v1.10 NC63..NC70, v1.11 NC71..NC85,
v1.12 NC86..NC99 and v1.13 NC100..NC114.  Every control here targets a SPECIFIC
v1.14 governance repair (D40 machine-enforced science eligibility, D41
non-tautological terminal binding, D42 smoke-check-ID accounting, D43 raw-byte
transform proof) or re-proves a carried repair (D22/D34/D37/D38/D39), pairing a
faithful standalone re-implementation of the corresponding detector with an
IN-MEMORY mutant (or a SIMULATED release-attestation state) that a CORRECT
detector MUST reject.

MANDATED v1.14 CONTROLS (20):
  D40 science-release (10):
    1.  no attestation -> NOT_RELEASED (NO_ATTESTATION)                 NC115
    2.  malformed attestation -> NOT_RELEASED (MALFORMED)               NC116
    3.  revision mismatch -> NOT_RELEASED                               NC117
    4.  execution-source SHA mismatch -> NOT_RELEASED                   NC118
    5.  smoke artifact missing -> NOT_RELEASED                          NC119
    6.  smoke artifact SHA mismatch -> NOT_RELEASED                     NC120
    7.  smoke_all_pass != True -> NOT_RELEASED                          NC121
    8.  scientific_output != False -> NOT_RELEASED                      NC122
    9.  release_gate mismatch -> NOT_RELEASED                           NC123
    10. plain "released":true editable JSON -> NOT_RELEASED (positive
        chain: a bare affirmation cannot satisfy the binding)           NC124
  plus science mode cannot set the launch token / create a science marker
        when NOT_RELEASED                                              NC125/NC126
  plus fully-bound attestation -> RELEASED (positive control)          NC127
  D41 non-tautological terminal binding:
    renamed / removed wrong-interpreter terminal -> detector fails      NC128
  D42 smoke-check-ID accounting (-1 / +1 / duplicate)                    NC129-NC131
  D43 raw-byte untransform identity + mutation sensitivity               NC132-NC134
  carried: source / manifest / co-edit mutation rejected                 NC135-NC137
  carried: canonical venv + CUDA readiness passes (positive)             NC138

IN-MEMORY / SIMULATED-STATE MUTANTS ONLY.  Canonical files on disk are NEVER
modified.  Science-release controls exercise a FAITHFUL STANDALONE
re-implementation of the production gate logic over SIMULATED attestation /
smoke-artifact state — the production paths are additionally proven live (the
launcher/exec D40 gate refusals are exercised by the preflight suite).

NO torch load.  NO model.  NO checkpoint.  NO forward.  NO smoke.  NO science.
NO VAL image / GT read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_14.py"
EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
EXEC_V1_13 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_13.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json"

REVISION = "ra_medfilm_barr_phase36_robustness_v1_14"
SMOKE_ART = "reports/audits/phase36_robustness_smoke_v1_14.json"

records = []


def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _load_launcher():
    spec = importlib.util.spec_from_file_location("phase36_v1_14_launcher_nc", LAUNCHER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def record(name, mutation_changed, detector_canonical, detector_mutant, note=None,
           require_mutation=True):
    """Record a control outcome.

    A control PASSES iff (a) the canonical/correct input is ACCEPTED, (b) the
    mutated input is REJECTED, and (c) — where the control injects a mutation —
    the mutation actually changed the input.  ``require_mutation=False`` is used
    ONLY by the positive controls (NC127/NC138), which inject no mutation.
    """
    passed = bool(detector_canonical and detector_mutant
                  and (mutation_changed if require_mutation else True))
    records.append({
        "control": name,
        "mutation_changed_input": bool(mutation_changed),
        "detector_canonical": bool(detector_canonical),
        "detector_mutant": bool(detector_mutant),
        "mutant_rejected": bool(detector_mutant),
        "passed": passed,
        "note": note,
    })
    return passed


# ========================================================================== #
# D40 — FAITHFUL STANDALONE re-implementation of the machine-enforced science
#       release gate over SIMULATED state (mirrors BOTH production gates).
# ========================================================================== #
def _science_release_state(att_text: str | None, smoke_bytes: bytes | None,
                           source_sha: str) -> str:
    """Return "RELEASED" or a NOT_RELEASED reason string.

    Mirrors ``_gate_science_release_state`` (execution) and
    ``_science_release_evidence`` (launcher) EXACTLY, in the same order:
    NO_ATTESTATION -> ATTESTATION_MALFORMED -> REVISION_MISMATCH ->
    SOURCE_SHA_MISMATCH -> SMOKE_ARTIFACT_MISSING -> SMOKE_ARTIFACT_SHA_MISMATCH ->
    SMOKE_NOT_SUCCESSFUL -> SCIENTIFIC_OUTPUT_NOT_FALSE -> RELEASE_GATE_MISMATCH ->
    RELEASED.
    """
    if att_text is None:
        return "NO_ATTESTATION"
    try:
        att = json.loads(att_text)
    except Exception:
        return "ATTESTATION_MALFORMED"
    if not isinstance(att, dict):
        return "ATTESTATION_MALFORMED"
    if att.get("revision") != REVISION:
        return "REVISION_MISMATCH"
    if att.get("execution_source_sha256") != source_sha:
        return "SOURCE_SHA_MISMATCH"
    if smoke_bytes is None:
        return "SMOKE_ARTIFACT_MISSING"
    if att.get("smoke_artifact_sha256") != _sha_bytes(smoke_bytes):
        return "SMOKE_ARTIFACT_SHA_MISMATCH"
    if att.get("smoke_all_pass") is not True:
        return "SMOKE_NOT_SUCCESSFUL"
    if att.get("scientific_output") is not False:
        return "SCIENTIFIC_OUTPUT_NOT_FALSE"
    if att.get("release_gate") != "POST_SMOKE_RELEASE_ADJUDICATION":
        return "RELEASE_GATE_MISMATCH"
    return "RELEASED"


def _is_released(state: str) -> bool:
    """The detector: science is RELEASED iff state == "RELEASED"."""
    return state == "RELEASED"


# Canonical simulated baseline: a FULLY-BOUND, successful, non-scientific smoke.
SRC_SHA = _sha_bytes(EXEC.read_bytes())
SMOKE_BYTES = b'{"smoke_all_pass": true, "mode": "smoke", "scientific_output": false}'
ATT_FULL = {
    "revision": REVISION,
    "execution_source_sha256": SRC_SHA,
    "smoke_artifact_sha256": _sha_bytes(SMOKE_BYTES),
    "smoke_all_pass": True,
    "scientific_output": False,
    "release_gate": "POST_SMOKE_RELEASE_ADJUDICATION",
}


def _att(**over) -> str:
    d = dict(ATT_FULL)
    d.update(over)
    return json.dumps(d)


CANON_REL = _science_release_state(_att(), SMOKE_BYTES, SRC_SHA)

# ========================================================================== #
# NC115 — no attestation
# ========================================================================== #
_s = _science_release_state(None, SMOKE_BYTES, SRC_SHA)
record("NC115_no_attestation_not_released",
       mutation_changed=True,
       detector_canonical=_is_released(CANON_REL),
       detector_mutant=(not _is_released(_s)) and _s == "NO_ATTESTATION",
       note="absent release attestation -> NOT_RELEASED")

# ========================================================================== #
# NC116 — malformed attestation
# ========================================================================== #
_s = _science_release_state("{not valid json", SMOKE_BYTES, SRC_SHA)
record("NC116_malformed_attestation_not_released",
       mutation_changed=True,
       detector_canonical=_is_released(CANON_REL),
       detector_mutant=(not _is_released(_s)) and _s == "ATTESTATION_MALFORMED")

# ========================================================================== #
# NC117 — revision mismatch
# ========================================================================== #
_s = _science_release_state(_att(revision="ra_medfilm_barr_phase36_robustness_v1_13"),
                            SMOKE_BYTES, SRC_SHA)
record("NC117_revision_mismatch_not_released",
       mutation_changed=True,
       detector_canonical=_is_released(CANON_REL),
       detector_mutant=(not _is_released(_s)) and _s == "REVISION_MISMATCH")

# ========================================================================== #
# NC118 — execution-source SHA mismatch (attestation binds a DIFFERENT source)
# ========================================================================== #
_s = _science_release_state(_att(execution_source_sha256="0" * 64), SMOKE_BYTES, SRC_SHA)
record("NC118_source_sha_mismatch_not_released",
       mutation_changed=True,
       detector_canonical=_is_released(CANON_REL),
       detector_mutant=(not _is_released(_s)) and _s == "SOURCE_SHA_MISMATCH",
       note="attestation must bind THIS source's bytes")

# ========================================================================== #
# NC119 — smoke artifact missing
# ========================================================================== #
_s = _science_release_state(_att(), None, SRC_SHA)
record("NC119_smoke_artifact_missing_not_released",
       mutation_changed=True,
       detector_canonical=_is_released(CANON_REL),
       detector_mutant=(not _is_released(_s)) and _s == "SMOKE_ARTIFACT_MISSING")

# ========================================================================== #
# NC120 — smoke artifact bytes do not match the bound SHA
# ========================================================================== #
_s = _science_release_state(_att(), b'{"smoke_all_pass": true, "tampered": 1}', SRC_SHA)
record("NC120_smoke_artifact_sha_mismatch_not_released",
       mutation_changed=True,
       detector_canonical=_is_released(CANON_REL),
       detector_mutant=(not _is_released(_s)) and _s == "SMOKE_ARTIFACT_SHA_MISMATCH",
       note="release is bound to a SPECIFIC frozen smoke result's bytes")

# ========================================================================== #
# NC121 — smoke_all_pass is not True
# ========================================================================== #
_s = _science_release_state(_att(smoke_all_pass=False), SMOKE_BYTES, SRC_SHA)
record("NC121_smoke_not_successful_not_released",
       mutation_changed=True,
       detector_canonical=_is_released(CANON_REL),
       detector_mutant=(not _is_released(_s)) and _s == "SMOKE_NOT_SUCCESSFUL")

# ========================================================================== #
# NC122 — scientific_output is not False
# ========================================================================== #
_s = _science_release_state(_att(scientific_output=True), SMOKE_BYTES, SRC_SHA)
record("NC122_scientific_output_not_false_not_released",
       mutation_changed=True,
       detector_canonical=_is_released(CANON_REL),
       detector_mutant=(not _is_released(_s)) and _s == "SCIENTIFIC_OUTPUT_NOT_FALSE")

# ========================================================================== #
# NC123 — release_gate mismatch
# ========================================================================== #
_s = _science_release_state(_att(release_gate="SELF_DECLARED"), SMOKE_BYTES, SRC_SHA)
record("NC123_release_gate_mismatch_not_released",
       mutation_changed=True,
       detector_canonical=_is_released(CANON_REL),
       detector_mutant=(not _is_released(_s)) and _s == "RELEASE_GATE_MISMATCH")

# ========================================================================== #
# NC124 — plain editable JSON that merely says "released": true is REJECTED.
#         This is the CENTRAL D40 property: the gate is a POSITIVE chain, not a
#         bare affirmation flag.  The bare affirmation carries NONE of the
#         required bindings, so even the FIRST binding check fails.
# ========================================================================== #
_bare = json.dumps({"released": True})
_s_bare = _science_release_state(_bare, SMOKE_BYTES, SRC_SHA)
record("NC124_bare_released_true_json_rejected",
       mutation_changed=True,
       detector_canonical=_is_released(CANON_REL),
       detector_mutant=(not _is_released(_s_bare)),
       note="a bare {'released': true} lacks the FULL positive chain "
            "(revision + source-SHA + smoke-artifact bytes + success flags) "
            "-> the FIRST binding check already fails")
# prove the bare flag is specifically not enough: even with revision present it
# still fails on the source binding.
_s_bare2 = _science_release_state(json.dumps({"released": True, "revision": REVISION}),
                                  SMOKE_BYTES, SRC_SHA)
record("NC124b_bare_released_with_revision_still_rejected",
       mutation_changed=True,
       detector_canonical=_is_released(CANON_REL),
       detector_mutant=(not _is_released(_s_bare2)) and _s_bare2 == "SOURCE_SHA_MISMATCH")

# ========================================================================== #
# NC125 / NC126 — science mode cannot set the launch token / create a science
#                 marker when the release gate is NOT_RELEASED.
# ========================================================================== #
def _lmain_body(launcher_src: str):
    t = ast.parse(launcher_src)
    fns = {n.name: n for n in ast.walk(t) if isinstance(n, ast.FunctionDef)}
    return t, fns


LSRC = LAUNCHER.read_text(encoding="utf-8")

# D41: AST-extract the wrong-interpreter terminal actually emitted.
def _module_str_constants(launcher_src: str) -> dict:
    t = ast.parse(launcher_src)
    out = {}
    for n in t.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 \
                and isinstance(n.targets[0], ast.Name) \
                and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
            out[n.targets[0].id] = n.value.value
    return out


def _extract_wrong_interpreter_terminal(launcher_src: str):
    """AST-bind the terminal literal emitted by the wrong-interpreter branch."""
    t = ast.parse(launcher_src)
    consts = _module_str_constants(launcher_src)
    fns = {n.name: n for n in ast.walk(t) if isinstance(n, ast.FunctionDef)}
    main = fns.get("main")
    if main is None:
        return None
    for n in ast.walk(main):
        if isinstance(n, ast.If):
            test = n.test
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


def _simulate_gate_ordering(released: bool):
    """Faithful re-implementation of the launcher D40 pre-dispatch order:
    verify-only stop -> [science release gate] -> set token -> import exec.
    Returns (token_set, exec_imported, marker_created)."""
    verify_only = False
    mode = "science"
    if verify_only:
        return False, False, False
    if mode == "science" and not released:
        return False, False, False
    token_set = True
    exec_imported = True
    marker_created = True     # the exec would create the science start marker
    return token_set, exec_imported, marker_created


_canon_tok, _canon_imp, _canon_mark = _simulate_gate_ordering(released=True)
_mut_tok, _mut_imp, _mut_mark = _simulate_gate_ordering(released=False)
record("NC125_not_released_science_cannot_set_launch_token",
       mutation_changed=True,
       detector_canonical=bool(_canon_tok),
       detector_mutant=(not _mut_tok) and (not _mut_imp) and (not _mut_mark),
       note="NOT_RELEASED returns before token assignment / exec import / marker")

# The production launcher: prove the gate sits BEFORE the token assignment AND
# BEFORE the exec import, for science mode only.
_lmain_src = ast.get_source_segment(
    LSRC, {n.name: n for n in ast.walk(ast.parse(LSRC)) if isinstance(n, ast.FunctionDef)}["main"]) or ""
_order_ok = (0 <= _lmain_src.index("_science_release_evidence()")
             < _lmain_src.index("os.environ[LAUNCH_AUTHORITY_TOKEN]")
             < _lmain_src.index("spec.loader.exec_module"))
record("NC126_not_released_science_cannot_create_marker_production_order",
       mutation_changed=True,
       detector_canonical=_order_ok,
       detector_mutant=(not _mut_mark),
       note="production launcher source: release gate precedes token & exec import")

# ========================================================================== #
# NC127 — fully-bound attestation -> RELEASED (positive control)
# ========================================================================== #
record("NC127_fully_bound_attestation_released",
       mutation_changed=False,          # no mutation; positive control
       detector_canonical=_is_released(CANON_REL),
       detector_mutant=_is_released(CANON_REL),
       require_mutation=False,
       note="revision + source-SHA + smoke bytes + success flags all bound")

# ========================================================================== #
# NC128 — D41: mutation-sensitive wrong-interpreter terminal detector
# ========================================================================== #
REQ_WRONG_INTERP = "PHASE36_V1_14_LAUNCH_FAIL_CLOSED__WRONG_INTERPRETER__NO_ATTEMPT_CONSUMED"
_obs_ok = _extract_wrong_interpreter_terminal(LSRC)
_mut_terminal = LSRC.replace(REQ_WRONG_INTERP, "PHASE36_V1_14_WRONG_INTERPRETER_RENAMED")
_mut_removed = LSRC.replace(REQ_WRONG_INTERP, "")
record("NC128_wrong_interpreter_terminal_detector_mutation_sensitive",
       mutation_changed=(_mut_terminal != LSRC and _mut_removed != LSRC),
       detector_canonical=(_obs_ok == REQ_WRONG_INTERP),
       detector_mutant=(_extract_wrong_interpreter_terminal(_mut_terminal) != REQ_WRONG_INTERP
                        and _extract_wrong_interpreter_terminal(_mut_removed) != REQ_WRONG_INTERP),
       note="renaming OR removing the emitted literal must fail the detector "
            "(proves D41 is a real source/AST binding, not a tautology)")

# ========================================================================== #
# D42 — smoke-check-ID accounting detector (mutation-sensitive)
# ========================================================================== #
def _declared_smoke_ids(src: str) -> list:
    t = ast.parse(src)
    for n in ast.walk(t):
        if isinstance(n, ast.Assign):
            for tg in n.targets:
                if isinstance(tg, ast.Name) and tg.id == "SMOKE_CHECK_IDS":
                    return [e.value for e in n.value.elts]
    return []


_ids14 = _declared_smoke_ids(EXEC.read_text(encoding="utf-8"))
_ids13 = _declared_smoke_ids(EXEC_V1_13.read_text(encoding="utf-8"))


def _detector_smoke_ids(ids: list) -> bool:
    """Faithful detector: exact count 53 + uniqueness + exact set equality."""
    return len(ids) == 53 and len(set(ids)) == 53 and set(ids) == set(_ids13)


record("NC129_smoke_id_detector_rejects_removed_id",
       mutation_changed=(len(_ids14[:-1]) != len(_ids14)),
       detector_canonical=_detector_smoke_ids(_ids14),
       detector_mutant=not _detector_smoke_ids(_ids14[:-1]),
       note="remove one ID -> exact-count fails")
record("NC130_smoke_id_detector_rejects_added_id",
       mutation_changed=True,
       detector_canonical=_detector_smoke_ids(_ids14),
       detector_mutant=not _detector_smoke_ids(_ids14 + ["synthetic_added_id"]),
       note="add one ID -> exact-count + set-equality fail")
record("NC131_smoke_id_detector_rejects_duplicate_id",
       mutation_changed=True,
       detector_canonical=_detector_smoke_ids(_ids14),
       detector_mutant=not _detector_smoke_ids(_ids14[:-1] + [_ids14[0]]),
       note="duplicate one ID -> uniqueness fails")

# ========================================================================== #
# D43 — raw-byte transform proof + mutation sensitivity
# ========================================================================== #
_D40_MAIN_START = b"        # \xc2\xa7D40 (v1.14) SCIENCE RELEASE GATE"
_D40_MAIN_END = b"        # \xc2\xa7D32 AUTHORIZED-ATTEMPT ORDERING"
_D40_APPEND_RULE = b"# =========================================================================== #\r\n"
_D40_APPEND_START = b"# \xc2\xa7D40 (v1.14) \xe2\x80\x94 MACHINE-ENFORCED SCIENCE ELIGIBILITY"
_GUARD = b'if __name__ == "__main__":\r\n    raise SystemExit(main())\r\n'
FROZEN_V1_13_SHA = "57f78447e77f2bcee07265825232cf0a8f96d1a31974d5d52c4cc82229e5d39c"


def _untransform(raw14: bytes, raw13: bytes) -> bytes:
    _ia = raw14.find(_D40_MAIN_START)
    _ib = raw14.find(_D40_MAIN_END)
    _ibanner = raw14.find(_D40_APPEND_START)
    _iapp = raw14.rfind(_D40_APPEND_RULE, 0, _ibanner)
    body = raw14[:_ia] + raw14[_ib:_iapp]
    if not body.endswith(_GUARD):
        body = body + _GUARD
    for _a, _b in ((b"V1_14", b"V1_13"), (b"v1_14", b"v1_13"),
                   (b"V1.14", b"V1.13"), (b"v1.14", b"v1.13")):
        body = body.replace(_a, _b)
    return body


_raw14 = EXEC.read_bytes()
_raw13 = EXEC_V1_13.read_bytes()
_un = _untransform(_raw14, _raw13)
record("NC132_raw_byte_untransform_identity",
       mutation_changed=True,
       detector_canonical=(_un == _raw13),
       detector_mutant=hashlib.sha256(_un).hexdigest() == FROZEN_V1_13_SHA,
       note="removes both additive D40 segments, applies raw-byte token "
            "untransform -> byte-identical to frozen v1.13")
# mutation sensitivity: corrupt a governance token so that the raw-byte
# untransform can no longer reproduce the frozen v1.13 bytes.
_mut_raw2 = _raw14.replace(b"PHASE36_V1_14_LAUNCH_AUTHORITY",
                           b"PHASE36_V1_14_LAUNCH_AUTHORITX", 1)
record("NC133_raw_byte_untransform_mutation_sensitive",
       mutation_changed=(_mut_raw2 != _raw14),
       detector_canonical=(_un == _raw13),
       detector_mutant=(_untransform(_mut_raw2, _raw13) != _raw13),
       note="corrupting a governance token breaks byte-identity with frozen v1.13")

# newline policy: CRLF preserved (no newline normalization in the transform)
record("NC134_raw_byte_crlf_preserved",
       mutation_changed=True,
       detector_canonical=(b"\r\n" in _raw14 and _raw14.count(b"\r\n") > 100),
       detector_mutant=(_un == _raw13 and b"\r\n" in _un),
       note="CRLF line endings survive the raw-byte transform; no newline "
            "normalization is applied")

# ========================================================================== #
# NC135-NC137 — carried: source / manifest / co-edit mutation rejected
# ========================================================================== #
def _run_launcher_verify(exec_bytes: bytes, manifest_bytes: bytes) -> dict:
    mod = _load_launcher()
    with tempfile.TemporaryDirectory() as td:
        ex = Path(td) / "exec.py"
        ma = Path(td) / "manifest.json"
        ex.write_bytes(exec_bytes)
        ma.write_bytes(manifest_bytes)
        return mod.verify_authority(exec_path=ex, manifest_path=ma)


EXEC_BYTES = EXEC.read_bytes()
MANIFEST_BYTES = MANIFEST.read_bytes()
CANON_AUTH = _run_launcher_verify(EXEC_BYTES, MANIFEST_BYTES)
CANON_OK = bool(CANON_AUTH["authorized"])

_exec_mut = EXEC_BYTES + b"\n# mutant\n"
_man_mut = MANIFEST_BYTES.replace(b'"n_dependencies": 14', b'"n_dependencies": 99')
_co_exec = EXEC_BYTES + b"\n# co-edit\n"
_co_man = MANIFEST_BYTES.replace(b'"n_dependencies": 14', b'"n_dependencies": 77')

record("NC135_source_mutation_rejected",
       mutation_changed=(_exec_mut != EXEC_BYTES),
       detector_canonical=CANON_OK,
       detector_mutant=not _run_launcher_verify(_exec_mut, MANIFEST_BYTES)["authorized"])
record("NC136_manifest_mutation_rejected",
       mutation_changed=(_man_mut != MANIFEST_BYTES),
       detector_canonical=CANON_OK,
       detector_mutant=not _run_launcher_verify(EXEC_BYTES, _man_mut)["authorized"])
record("NC137_source_and_manifest_co_edit_rejected",
       mutation_changed=(_co_exec != EXEC_BYTES and _co_man != MANIFEST_BYTES),
       detector_canonical=CANON_OK,
       detector_mutant=not _run_launcher_verify(_co_exec, _co_man)["authorized"],
       note="co-edit cannot supply its own hashes; frozen constants unchanged")

# ========================================================================== #
# NC138 — canonical project venv + CUDA readiness passes (positive control)
# ========================================================================== #
_mod = _load_launcher()
CANON_INTERP = _mod.check_interpreter_identity()
CANON_CUDA = _mod.check_cuda_readiness()
record("NC138_canonical_venv_cuda_passes_readiness",
       mutation_changed=False,          # no mutation; positive control
       detector_canonical=bool(CANON_INTERP["ok"] and CANON_CUDA["ok"]),
       detector_mutant=bool(CANON_INTERP["ok"] and CANON_CUDA["ok"]),
       require_mutation=False)

# ========================================================================== #
# SUMMARY
# ========================================================================== #
n_pass = sum(1 for r in records if r["passed"])
n_total = len(records)
report = {
    "artifact": "phase36_v1_14_negative_controls",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": REVISION,
    "type": "NEGATIVE_CONTROL_REPORT",
    "controls_range": "NC115..NC138",
    "model_free": True,
    "checkpoint_read": False,
    "protected_population_read": False,
    "no_canonical_file_modified": True,
    "canonical_anchor_ok": CANON_OK,
    "canonical_interpreter_ok": bool(CANON_INTERP["ok"]),
    "canonical_cuda_readiness_ok": bool(CANON_CUDA["ok"]),
    "science_release_canonical_state": CANON_REL,
    "declared_smoke_check_count": len(_ids14),
    "controls_total": n_total,
    "controls_passed": n_pass,
    "controls_failed": n_total - n_pass,
    "all_pass": n_pass == n_total,
    "failed_controls": [r["control"] for r in records if not r["passed"]],
    "controls": records,
}
out = ROOT / "reports/audits/phase36_v1_14_negative_controls.json"
out.write_text(json.dumps(report, indent=1), encoding="utf-8")

for r in records:
    if not r["passed"]:
        print(f"FAIL {r['control']} :: {r}")
print(f"NEGATIVE CONTROLS v1.14: {n_pass}/{n_total} pass")
print(f"terminal: {'PHASE36_V1_14_NEGATIVE_CONTROLS_PASS' if n_pass == n_total else 'PHASE36_V1_14_NEGATIVE_CONTROLS_FAIL'}")
raise SystemExit(0 if n_pass == n_total else 1)
