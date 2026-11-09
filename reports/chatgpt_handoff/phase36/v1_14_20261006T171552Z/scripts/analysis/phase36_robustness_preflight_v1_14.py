#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.14 — STATIC PREFLIGHT (SOURCE / AST / HASH ONLY; NO EXECUTION).

Aggregates the v1.14 static/governance gates and proves, from source bytes and
AST only, that D40–D43 are enforced and D22–D39 are preserved.

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO VAL/GT read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
EXEC_V1_13 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_13.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_14.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json"

checks = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}
LSRC = LAUNCHER.read_text(encoding="utf-8")
LFUNCS = {n.name: n for n in ast.walk(ast.parse(LSRC)) if isinstance(n, ast.FunctionDef)}


def _lfunc(name):
    return ast.get_source_segment(LSRC, LFUNCS[name]) or ""


def _declared_smoke_ids(src):
    t = ast.parse(src)
    for n in ast.walk(t):
        if isinstance(n, ast.Assign):
            for tg in n.targets:
                if isinstance(tg, ast.Name) and tg.id == "SMOKE_CHECK_IDS":
                    return [e.value for e in n.value.elts]
    return []


# ---------------------------------------------------------------- #
# A. D43 raw-byte untransform (independent re-derivation)
# ---------------------------------------------------------------- #
raw14 = EXEC.read_bytes()
raw13 = EXEC_V1_13.read_bytes()
A = b"        # \xc2\xa7D40 (v1.14) SCIENCE RELEASE GATE"
B = b"        # \xc2\xa7D32 AUTHORIZED-ATTEMPT ORDERING"
C = b"# \xc2\xa7D40 (v1.14) \xe2\x80\x94 MACHINE-ENFORCED SCIENCE ELIGIBILITY"
RULE = b"# =========================================================================== #\r\n"
ia, ib, icb = raw14.find(A), raw14.find(B), raw14.find(C)
ic = raw14.rfind(RULE, 0, icb)
GUARD = b'if __name__ == "__main__":\r\n    raise SystemExit(main())\r\n'
body = raw14[:ia] + raw14[ib:ic]
if not body.endswith(GUARD):
    body = body + GUARD
un = body
for a, b in ((b"V1_14", b"V1_13"), (b"v1_14", b"v1_13"), (b"V1.14", b"V1.13"), (b"v1.14", b"v1.13")):
    un = un.replace(a, b)
check("A01_raw_byte_untransform_identity", un == raw13,
      {"untransformed_sha": hashlib.sha256(un).hexdigest()})
check("A02_untransformed_sha_equals_frozen_v1_13",
      hashlib.sha256(un).hexdigest() == _sha(EXEC_V1_13))
check("A03_new_scientific_choice_false", un == raw13)

# ---------------------------------------------------------------- #
# B. D42 smoke check ids
# ---------------------------------------------------------------- #
ids14 = _declared_smoke_ids(SRC)
ids13 = _declared_smoke_ids(EXEC_V1_13.read_text(encoding="utf-8"))
check("B01_smoke_ids_count_53", len(ids14) == 53, {"count": len(ids14)})
check("B02_smoke_ids_unique", len(set(ids14)) == 53)
check("B03_smoke_ids_exact_set_equality", set(ids14) == set(ids13))
check("B04_smoke_ids_order_identical", ids14 == ids13)

# ---------------------------------------------------------------- #
# C. D40 gate presence + ordering
# ---------------------------------------------------------------- #
check("C01_exec_release_gate_fn", "_gate_science_release_state" in FUNCS)
check("C02_launcher_release_fn", "_science_release_evidence" in LFUNCS)
check("C03_science_terminal_literal",
      "PHASE36_V1_14_SCIENCE_NOT_RELEASED" in LSRC
      and "SUCCESSFUL_SMOKE_REQUIRED__NO_ATTEMPT_CONSUMED" in LSRC)
_m = ast.get_source_segment(LSRC, LFUNCS["main"]) or ""
check("C04_launcher_order_anchor_interp_cuda_verifyonly_release_token_import",
      _m.index("verify_authority()") < _m.index("check_interpreter_identity()")
      < _m.index("check_cuda_readiness()") < _m.index("a.verify_only")
      < _m.index("_science_release_evidence()")
      < _m.index("os.environ[LAUNCH_AUTHORITY_TOKEN]")
      < _m.index("spec.loader.exec_module"))
check("C05_launcher_no_marker_or_file_write",
      "start_marker" not in LSRC and "open(" not in LSRC and "write_text" not in LSRC)

# ---------------------------------------------------------------- #
# D. Preserved D37/D38/D39
# ---------------------------------------------------------------- #
check("D01_canonical_interpreter_derived_from_root",
      'CANONICAL_INTERPRETER = ROOT / ".venv" / "Scripts" / "python.exe"' in LSRC)
check("D02_cuda_readiness_conditions",
      all(k in _lfunc("check_cuda_readiness") for k in (
          "torch_version_cuda_not_none", "cuda_is_available_true",
          "device_count_ge_1", "get_device_require_cuda_ok",
          "resolved_device_type_is_cuda")))
check("D03_cuda_probe_device_only",
      all(bad not in _lfunc("check_cuda_readiness") for bad in (
          "torch.load", "load_state_dict", "forward(")))
check("D04_no_auto_relaunch",
      all(k not in LSRC for k in ("subprocess", "os.execv", "os.execve", "Popen")))

# ---------------------------------------------------------------- #
# E. Manifest non-circularity + dependency integrity
# ---------------------------------------------------------------- #
_man = json.loads(MANIFEST.read_text(encoding="utf-8"))
check("E01_manifest_no_launcher_sha256", "launcher_sha256" not in _man)
check("E02_manifest_declares_actual_exec_sha", _man["execution_source_sha256"] == _sha(EXEC))
check("E03_manifest_14_deps_4_ckpts",
      _man["n_dependencies"] == 14 and _man["n_checkpoints"] == 4)
check("E04_all_deps_match", all(_sha(ROOT / r) == e for r, e in _man["dependencies"].items()))
check("E05_all_ckpts_match", all(_sha(ROOT / r) == e for r, e in _man["checkpoints"].items()))

# ---------------------------------------------------------------- #
# F. v1.14 unconsumed; v1.13 unconsumed; v1.12 evidence present
# ---------------------------------------------------------------- #
v14_attempts = [
    "reports/audits/phase36_robustness_smoke_v1_14.json",
    "reports/audits/phase36_robustness_smoke_start_v1_14.json",
    "reports/audits/phase36_robustness_smoke_failure_v1_14.json",
    "reports/audits/phase36_robustness_scientific_result_v1_14.json",
    "reports/audits/phase36_robustness_science_start_v1_14.json",
    "reports/audits/phase36_robustness_science_failure_v1_14.json",
    "reports/audits/phase36_v1_14_science_release_attestation.json",
]
check("F01_v1_14_unconsumed", not any((ROOT / p).exists() for p in v14_attempts))
v13_attempts = [
    "reports/audits/phase36_robustness_smoke_v1_13.json",
    "reports/audits/phase36_robustness_smoke_start_v1_13.json",
    "reports/audits/phase36_robustness_science_start_v1_13.json",
    "reports/audits/phase36_robustness_scientific_result_v1_13.json",
]
check("F02_v1_13_never_consumed", not any((ROOT / p).exists() for p in v13_attempts))
check("F03_v1_12_evidence_present",
      all((ROOT / p).exists() for p in [
          "reports/audits/phase36_robustness_smoke_start_v1_12.json",
          "reports/audits/phase36_robustness_smoke_failure_v1_12.json",
          "reports/audits/phase36_v1_12_smoke_console_first_attempt.txt",
          "reports/audits/phase36_v1_12_cuda_environment_diagnosis.json",
          "reports/audits/phase36_v1_12_failed_smoke_adjudication.json"]))

# ---------------------------------------------------------------- #
n_pass = sum(1 for c in checks if c["passed"])
n_total = len(checks)
report = {
    "artifact": "phase36_robustness_preflight_v1_14",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_14",
    "type": "STATIC_PREFLIGHT_REPORT",
    "model_free": True,
    "torch_imported": False,
    "cuda_initialized": False,
    "protected_population_read": False,
    "subject_execution_sha256": _sha(EXEC),
    "subject_launcher_sha256": _sha(LAUNCHER),
    "subject_manifest_sha256": _sha(MANIFEST),
    "new_scientific_choice": False,
    "checks_total": n_total,
    "checks_passed": n_pass,
    "checks_failed": n_total - n_pass,
    "all_pass": n_pass == n_total,
    "failed_checks": [c["check"] for c in checks if not c["passed"]],
    "checks": checks,
}
(ROOT / "reports/audits/phase36_robustness_preflight_v1_14.json").write_text(
    json.dumps(report, indent=1), encoding="utf-8")
for c in checks:
    if not c["passed"]:
        print(f"FAIL {c['check']} :: {c.get('detail')}")
print(f"PREFLIGHT v1.14: {n_pass}/{n_total} pass")
print(f"terminal: {'PHASE36_V1_14_PREFLIGHT_PASS' if n_pass == n_total else 'PHASE36_V1_14_PREFLIGHT_FAIL'}")
raise SystemExit(0 if n_pass == n_total else 1)
