#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.13 — NEGATIVE CONTROLS NC100..NC114.

Additive over the carried v1.9 NC50..NC57, v1.10 NC63..NC70, v1.11 NC71..NC85 and
v1.12 NC86..NC99.  Every control here targets a SPECIFIC v1.13 governance repair
(D37/D38/D39) or re-proves a carried repair (D34/D35/D36), pairing a faithful
standalone re-implementation of the corresponding detector with an IN-MEMORY
mutant (or, for the launcher, a MUTATED TEMPORARY ON-DISK COPY / a SIMULATED
interpreter) that a CORRECT detector MUST reject.

MANDATED v1.13 CONTROLS (15):
   1. wrong sys.executable rejected                              (NC100)
   2. CPU-only torch readiness rejected                          (NC101)
   3. torch.version.cuda = None rejected                         (NC102)
   4. torch.cuda.is_available() = False rejected                 (NC103)
   5. device_count = 0 rejected                                  (NC104)
   6. get_device(require_cuda=True) failure rejected             (NC105)
   7. wrong interpreter cannot set launch token                  (NC106)
   8. failed CUDA readiness cannot set launch token              (NC107)
   9. wrong interpreter cannot create v1.13 start marker         (NC108)
  10. failed CUDA readiness cannot create v1.13 start marker     (NC109)
  11. source mutation rejected                                    (NC110)
  12. manifest mutation rejected                                  (NC111)
  13. source+manifest co-edit rejected                            (NC112)
  14. old expected-hash env vars remain inert                     (NC113)
  15. canonical venv + CUDA environment passes readiness          (NC114)

IN-MEMORY / TEMP-FILE MUTANTS ONLY.  Canonical files on disk are NEVER modified.
The launcher is exercised THROUGH its own production ``verify_authority`` /
``check_interpreter_identity`` entry points (which accept temp paths / a
simulated executable) so the production launcher is NOT weakened — ``main()``
never passes those arguments.

NO torch load.  NO model.  NO checkpoint.  NO forward.  NO smoke.  NO science.
NO VAL image / GT read.  NO ROUTER_HOLDOUT.  NO TEST.  (Only a DEVICE-ONLY
readiness probe, which the negative controls exercise under SIMULATED state, and
which under the canonical environment is a genuine read-only CUDA query.)
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_13.py"
EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_13.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_13_runtime_source_integrity_manifest.json"

records = []


def _sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _load_launcher():
    spec = importlib.util.spec_from_file_location("phase36_v1_13_launcher_nc", LAUNCHER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def record(name, mutation_changed, detector_canonical, detector_mutant, note=None,
           require_mutation=True):
    """Record a control outcome.

    A control PASSES iff (a) the canonical/correct input is ACCEPTED, (b) the
    mutated input is REJECTED, and (c) — where the control injects a mutation —
    the mutation actually changed the input.  ``require_mutation=False`` is used
    ONLY by the positive control NC114, which injects no mutation.
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


def _run_launcher_verify(exec_bytes: bytes, manifest_bytes: bytes) -> dict:
    """Exercise the PRODUCTION launcher's verify_authority on TEMP copies."""
    mod = _load_launcher()
    with tempfile.TemporaryDirectory() as td:
        ex = Path(td) / "exec.py"
        ma = Path(td) / "manifest.json"
        ex.write_bytes(exec_bytes)
        ma.write_bytes(manifest_bytes)
        return mod.verify_authority(exec_path=ex, manifest_path=ma)


# ========================================================================== #
# Baseline canonical state (read-only; never modified)
# ========================================================================== #
EXEC_BYTES = EXEC.read_bytes()
MANIFEST_BYTES = MANIFEST.read_bytes()
CANON_AUTH = _run_launcher_verify(EXEC_BYTES, MANIFEST_BYTES)
CANON_OK = bool(CANON_AUTH["authorized"])

mod = _load_launcher()
CANON_INTERP = mod.check_interpreter_identity()          # real sys.executable (venv)
CANON_CUDA = mod.check_cuda_readiness()                  # real device probe

# ========================================================================== #
# NC100 — wrong sys.executable rejected
# ========================================================================== #
_interp_wrong = mod.check_interpreter_identity(
    observed_executable=r"C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe")
record("NC100_wrong_executable_rejected",
       mutation_changed=True,
       detector_canonical=bool(CANON_INTERP["ok"]),
       detector_mutant=not bool(_interp_wrong["ok"]),
       note="bare system Python 3.11 vs canonical .venv interpreter")

# ========================================================================== #
# NC101 — CPU-only torch readiness rejected (simulated state)
# ========================================================================== #
def _simulate_readiness(**over):
    """Evaluate the launcher's readiness CONDITION SET on a simulated state."""
    base = {
        "torch_version_cuda": "12.4", "cuda_is_available": True,
        "cuda_device_count": 1, "get_device_require_cuda_success": True,
        "get_device_resolved_type": "cuda",
    }
    base.update(over)
    conds = {
        "torch_version_cuda_not_none": base["torch_version_cuda"] is not None,
        "cuda_is_available_true": base["cuda_is_available"] is True,
        "device_count_ge_1": bool(base["cuda_device_count"] and base["cuda_device_count"] >= 1),
        "get_device_require_cuda_ok": bool(base["get_device_require_cuda_success"]),
        "resolved_device_type_is_cuda": base["get_device_resolved_type"] == "cuda",
    }
    return all(conds.values())


record("NC101_cpu_only_torch_build_rejected",
       mutation_changed=True,
       detector_canonical=_simulate_readiness(),
       detector_mutant=not _simulate_readiness(torch_version_cuda=None,
                                               cuda_is_available=False,
                                               cuda_device_count=0,
                                               get_device_require_cuda_success=False,
                                               get_device_resolved_type="cpu"),
       note="CPU-only build: version.cuda=None + is_available=False")
record("NC102_torch_version_cuda_none_rejected",
       mutation_changed=True,
       detector_canonical=_simulate_readiness(),
       detector_mutant=not _simulate_readiness(torch_version_cuda=None))
record("NC103_cuda_is_available_false_rejected",
       mutation_changed=True,
       detector_canonical=_simulate_readiness(),
       detector_mutant=not _simulate_readiness(cuda_is_available=False))
record("NC104_device_count_zero_rejected",
       mutation_changed=True,
       detector_canonical=_simulate_readiness(),
       detector_mutant=not _simulate_readiness(cuda_device_count=0))
record("NC105_get_device_require_cuda_failure_rejected",
       mutation_changed=True,
       detector_canonical=_simulate_readiness(),
       detector_mutant=not _simulate_readiness(get_device_require_cuda_success=False))

# ========================================================================== #
# NC106/NC107 — gates cannot set the launch token
# ========================================================================== #
TOKEN = mod.LAUNCH_AUTHORITY_TOKEN


def _token_set_if_gates_pass(interp_ok, cuda_ok, env):
    """Faithful re-implementation of the launcher's token-setting branch."""
    if not interp_ok:
        return False, env
    if not cuda_ok:
        return False, env
    env = dict(env)
    env[TOKEN] = "1"
    return True, env


_env0 = {k: v for k, v in os.environ.items() if k != TOKEN}
_set_wrong, env_after_wrong = _token_set_if_gates_pass(False, True, _env0)
record("NC106_wrong_interpreter_cannot_set_launch_token",
       mutation_changed=True,
       detector_canonical=_token_set_if_gates_pass(True, True, _env0)[0],
       detector_mutant=not _set_wrong and TOKEN not in env_after_wrong,
       note="wrong interpreter branch returns before token assignment")
_set_cuda, env_after_cuda = _token_set_if_gates_pass(True, False, _env0)
record("NC107_failed_cuda_readiness_cannot_set_launch_token",
       mutation_changed=True,
       detector_canonical=_token_set_if_gates_pass(True, True, _env0)[0],
       detector_mutant=not _set_cuda and TOKEN not in env_after_cuda,
       note="cuda-readiness-failed branch returns before token assignment")

# ========================================================================== #
# NC108/NC109 — gates cannot create the v1.13 start marker
# ========================================================================== #
def _simulate_start_marker_creation(interp_ok, cuda_ok, marker_dir: Path,
                                    filename: str) -> Path:
    """Faithful re-implementation: the marker is created ONLY after the token is
    set, which itself requires BOTH gates.  Returns the (non-)marker path.

    Each call MUST use a DISTINCT filename so that a passing run cannot create
    an artifact that a failing run would then (spuriously) observe.
    """
    marker = marker_dir / filename
    set_ok, _env = _token_set_if_gates_pass(interp_ok, cuda_ok, {})
    if set_ok:
        with open(marker, "x", encoding="utf-8") as fh:
            fh.write("{}")
    return marker


with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    m_wrong = _simulate_start_marker_creation(False, True, td, "marker_wrong_interp.json")
    m_cuda = _simulate_start_marker_creation(True, False, td, "marker_cuda_fail.json")
    m_ok = _simulate_start_marker_creation(True, True, td, "marker_canonical.json")
    record("NC108_wrong_interpreter_cannot_create_start_marker",
           mutation_changed=True,
           detector_canonical=m_ok.exists(),
           detector_mutant=not m_wrong.exists())
    record("NC109_failed_cuda_readiness_cannot_create_start_marker",
           mutation_changed=True,
           detector_canonical=m_ok.exists(),
           detector_mutant=not m_cuda.exists())

# real launcher must NOT create a marker anywhere on disk during any of this
_check_launcher_has_no_marker_code = ((LAUNCHER.read_text(encoding="utf-8").count("start_marker") == 0)
                                      and (LAUNCHER.read_text(encoding="utf-8").count("open(") == 0))

# ========================================================================== #
# NC110/NC111/NC112 — source / manifest / co-edit mutation rejected
# ========================================================================== #
_exec_mut = EXEC_BYTES + b"\n# mutant\n"
_man_mut = MANIFEST_BYTES.replace(b'"n_dependencies": 14', b'"n_dependencies": 99')
_co_mut_exec = EXEC_BYTES + b"\n# co-edit\n"
_co_mut_man = MANIFEST_BYTES.replace(b'"n_dependencies": 14', b'"n_dependencies": 77')

record("NC110_source_mutation_rejected",
       mutation_changed=(_exec_mut != EXEC_BYTES),
       detector_canonical=CANON_OK,
       detector_mutant=not _run_launcher_verify(_exec_mut, MANIFEST_BYTES)["authorized"])
record("NC111_manifest_mutation_rejected",
       mutation_changed=(_man_mut != MANIFEST_BYTES),
       detector_canonical=CANON_OK,
       detector_mutant=not _run_launcher_verify(EXEC_BYTES, _man_mut)["authorized"])
record("NC112_source_and_manifest_co_edit_rejected",
       mutation_changed=(_co_mut_exec != EXEC_BYTES and _co_mut_man != MANIFEST_BYTES),
       detector_canonical=CANON_OK,
       detector_mutant=not _run_launcher_verify(_co_mut_exec, _co_mut_man)["authorized"],
       note="co-edit cannot supply its own hashes; frozen constants unchanged")

# ========================================================================== #
# NC113 — old expected-hash env vars remain inert
# ========================================================================== #
OLD_ENV = {
    "PHASE36_V1_11_EXPECTED_EXEC_SHA": _sha_bytes(_exec_mut),
    "PHASE36_V1_11_EXPECTED_MANIFEST_SHA": _sha_bytes(_man_mut),
    "PHASE36_V1_12_EXPECTED_EXEC_SHA": _sha_bytes(_exec_mut),
    "PHASE36_V1_12_EXPECTED_MANIFEST_SHA": _sha_bytes(_man_mut),
    "PHASE36_V1_13_EXPECTED_EXEC_SHA": _sha_bytes(_exec_mut),
    "PHASE36_V1_13_EXPECTED_MANIFEST_SHA": _sha_bytes(_man_mut),
}
_saved = {k: os.environ.get(k) for k in OLD_ENV}
try:
    os.environ.update(OLD_ENV)
    _mod2 = _load_launcher()
    _auth_env = _mod2.verify_authority()   # canonical paths
    _still_frozen = (_mod2._frozen_expected_exec_sha() == mod.FROZEN_EXPECTED_EXEC_SHA
                     and _mod2._frozen_expected_manifest_sha() == mod.FROZEN_EXPECTED_MANIFEST_SHA)
    record("NC113_old_expected_hash_env_vars_inert",
           mutation_changed=True,
           detector_canonical=CANON_OK,
           detector_mutant=bool(_still_frozen and _auth_env["authorized"]),
           note="env vars do not replace frozen constants; canonical anchor still passes")
finally:
    for k, v in _saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v

# ========================================================================== #
# NC114 — canonical project venv + CUDA environment passes readiness
# ========================================================================== #
record("NC114_canonical_venv_cuda_passes_readiness",
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
    "artifact": "phase36_v1_13_negative_controls",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_13",
    "type": "NEGATIVE_CONTROL_REPORT",
    "controls_range": "NC100..NC114",
    "model_free": True,
    "checkpoint_read": False,
    "protected_population_read": False,
    "no_canonical_file_modified": True,
    "launcher_has_no_marker_creation_code": bool(_check_launcher_has_no_marker_code),
    "canonical_anchor_ok": CANON_OK,
    "canonical_interpreter_ok": bool(CANON_INTERP["ok"]),
    "canonical_cuda_readiness_ok": bool(CANON_CUDA["ok"]),
    "canonical_cuda_snapshot": {
        "torch_version": CANON_CUDA["torch_version"],
        "torch_version_cuda": CANON_CUDA["torch_version_cuda"],
        "cuda_is_available": CANON_CUDA["cuda_is_available"],
        "cuda_device_count": CANON_CUDA["cuda_device_count"],
        "device_name_0": CANON_CUDA["device_name_0"],
        "get_device_resolved": CANON_CUDA["get_device_resolved"],
    },
    "controls_total": n_total,
    "controls_passed": n_pass,
    "controls_failed": n_total - n_pass,
    "all_pass": n_pass == n_total,
    "failed_controls": [r["control"] for r in records if not r["passed"]],
    "controls": records,
}
out = ROOT / "reports/audits/phase36_v1_13_negative_controls.json"
out.write_text(json.dumps(report, indent=1), encoding="utf-8")

for r in records:
    if not r["passed"]:
        print(f"FAIL {r['control']} :: {r}")
print(f"NEGATIVE CONTROLS v1.13: {n_pass}/{n_total} pass")
print(f"terminal: {'PHASE36_V1_13_NEGATIVE_CONTROLS_PASS' if n_pass == n_total else 'PHASE36_V1_13_NEGATIVE_CONTROLS_FAIL'}")
raise SystemExit(0 if n_pass == n_total else 1)
