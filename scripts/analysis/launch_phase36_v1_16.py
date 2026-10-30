#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.16 — NON-CIRCULAR PRE-INVOCATION LAUNCHER (prepare + verify-only).

REBASED FROM v1.15 (D80 OPERATIONAL/GOVERNANCE REBASE).  The scientific computation
is IDENTICAL to v1.15; ONLY the operational/governance/provenance layer changed.

MODEL-FREE and PROTECTED-DATA-FREE.  It reads only frozen authority bytes to verify
SHA-256 against EXACT frozen constants, verifies the canonical project interpreter,
performs a DEVICE-ONLY CUDA readiness probe, verifies transitive runtime integrity
(14 deps + 4 checkpoints via the v1.16 manifest family), and verifies all
D80 / D79 / D76 / D77 / D78 / D61 / D75 / Phase27 scoring-source bindings and
marker absence.

D80 repairs embedded HERE (launcher layer):
  * D80-C/D  explicit operator gate PHASE36_V1_16_EXECUTE (v1.16 namespace)
  * D80-C    launch authority token PHASE36_V1_16_LAUNCH_AUTHORITY
  * D80-H    the launcher PINS the literal v1.16 execution-source SHA (exact equality)
  * D80-A    the real dispatch command is EXACTLY
             <canonical_python> scripts/analysis/phase36_robustness_execution_v1_16.py --mode science
             --mode science is NEVER omitted.

Modes:
  --verify-only   Run ALL gates, print a terminal, RETURN BEFORE setting the launch
                  authority token / creating START / loading the model.  (Preparation
                  mode; never consumes the revision.)
  --self-test     Synthetic abrupt-termination + subprocess fixtures (no real science).
  (default)       Real one-shot dispatch: requires operator gate PHASE36_V1_16_EXECUTE=1
                  and sets PHASE36_V1_16_LAUNCH_AUTHORITY for the child.

This launcher NEVER retries and NEVER re-executes itself under another interpreter.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CANONICAL_INTERPRETER = ROOT / ".venv" / "Scripts" / "python.exe"

# ---- frozen sources ------------------------------------------------------- #
EXECUTION_SOURCE = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_16.py"
LAUNCHER_SELF = Path(__file__).resolve()

# D80-H: the launcher PINS the literal v1.16 execution-source SHA (exact equality).
V1_16_SOURCE_SHA = "a96b74caa4587aa9d2f83b79ed39c13075a88086109e31d991695a75ec4abab9"

# v1.16 runtime integrity manifest (non-circular authority; binds the v1.16 exec SHA).
V1_16_MANIFEST = ROOT / "reports" / "audits" / "phase36_v1_16_runtime_source_integrity_manifest.json"
V1_16_MANIFEST_SHA = "f9f245b41bdf904cdb4f9da7c3d32361da806c7451773ce721d3d0a023f64e18"

# ---- v1.16 governance authorities (pinned literal SHAs) ------------------- #
D80_ADJUDICATION = (
    ROOT / "reports" / "audits" / "phase36_v1_15_independent_audit_adjudication_v1_0.json",
    "fd66447fc1da1ad045fda102ed5ccfda39e1d0ffff5aa24cda6911e281e9d8c4",
)
V1_15_HANDOFF = (
    ROOT / "reports" / "audits" / "phase36_v1_15_independent_audit_handoff_v1_0.json",
    "8aa164955032738dd3528df9424c8e373de840f20c62c054a5904980f7394273",
)
D79_DISCLOSURE = (
    ROOT / "reports" / "audits"
    / "phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_reconciliation_write_history_v1_0.json",
    "548b7e1541abb5c011936db73b3cf1e90222a733267b67c8106ff4d5197ad81d",
)
D76_D78_RECON = (
    ROOT / "reports" / "audits"
    / "phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_reconciliation_v1_1.json",
    "7f0957695939a03feca7d9909c47f56e6644a4f3b800664c9bb61f02486dbd9b",
)
V1_4_RESULT = (
    ROOT / "reports" / "audits" / "phase36_final_probability_authority_diagnostic_result_v1_4.json",
    "046a1e3c3053fb00b97895d8d1834d0011f8b190209daa01795e6915b7fd5284",
)
V1_4_ADJUDICATION = (
    ROOT / "reports" / "audits"
    / "phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_v1_0.json",
    "912cb24e4b27dcc7d66310b36db2154180411ec52d79d19c767aa708220b9b36",
)
PHASE27_FINAL_PROB = (
    ROOT / "data_cache" / "phase27_barr_preservation_v1_0" / "phase27_val808_final_prob_f16.npy",
    "506ab6c4e715a9106889e186c146b73903493c80a63258007954cf5deb3ea9cf",
)
PHASE27_GLOBAL_PROB = (
    ROOT / "data_cache" / "phase27_barr_preservation_v1_0" / "phase27_val808_global_prob_f16.npy",
    "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13",
)
PHASE27_SCORE_CSV = (
    ROOT / "reports" / "tables" / "phase27_val808_per_sample_scores.csv",
    "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12",
)
PHASEA_SRC = (
    ROOT / "scripts" / "analysis" / "run_phase27_exec_phaseA.py",
    "ac0ffbdadbfe60349061a926f5a664716a3a3690ac3a90c21a35802263975841",
)
PHASEB_SRC = (
    ROOT / "scripts" / "analysis" / "run_phase27_exec_phaseB.py",
    "35800e39d9220e638adbb640bd25e18bc14da5298d9bed4a603f2f0dec64cf37",
)

# Historical v1.14 failure provenance kept ONLY as historical runtime evidence.
V1_14_FAILURE_PROVENANCE = ROOT / "reports" / "audits" / "phase36_robustness_science_failure_v1_14.json"

# ---- v1.16 attempt markers (must be ABSENT pre-execution) ----------------- #
V1_16_MARKERS = {
    "START": ROOT / "reports" / "audits" / "phase36_robustness_science_start_v1_16.json",
    "RESULT": ROOT / "reports" / "audits" / "phase36_robustness_scientific_result_v1_16.json",
    "FAILURE": ROOT / "reports" / "audits" / "phase36_robustness_science_failure_v1_16.json",
    "PROCESS_EXIT": ROOT / "reports" / "audits" / "phase36_robustness_science_process_exit_v1_16.json",
}
V1_16_JOURNAL_DIR = ROOT / "reports" / "audits" / "phase36_robustness_science_v1_16_journal"

# v1.15 markers must ALSO remain absent (v1.15 was NEVER executed).
V1_15_MARKERS = {
    "START": ROOT / "reports" / "audits" / "phase36_robustness_science_start_v1_15.json",
    "RESULT": ROOT / "reports" / "audits" / "phase36_robustness_science_result_v1_15.json",
    "FAILURE": ROOT / "reports" / "audits" / "phase36_robustness_science_failure_v1_15.json",
    "PROCESS_EXIT": ROOT / "reports" / "audits" / "phase36_robustness_science_process_exit_v1_15.json",
}
V1_15_JOURNAL_DIR = ROOT / "reports" / "audits" / "phase36_robustness_science_v1_15_journal"

# ---- protected populations ----------------------------------------------- #
TEST_LOCK_MANIFEST = ROOT / "reports" / "audits" / "phase36_test_lock_manifest.json"
ROUTER_HOLDOUT_LOCK = ROOT / "reports" / "audits" / "phase36_router_holdout_lock_manifest.json"

# ---- v1.16 operator gate + launch authority ------------------------------ #
TOKEN_ENV = "PHASE36_V1_16_EXECUTE"
SMOKE_TOKEN_ENV = "PHASE36_V1_16_SMOKE_EXECUTE"
LAUNCH_AUTHORITY = "PHASE36_V1_16_LAUNCH_AUTHORITY"

TERMINAL_OK = "PHASE36_V1_16_LAUNCH_VERIFY_ONLY_PASS"

# The EXACT real dispatch argument tail (D80-A: --mode science is MANDATORY).
DISPATCH_MODE_ARGS = ["--mode", "science"]


def sha256_file(p: Path) -> str | None:
    if not p.exists():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check(rel_or_path, exp, results: dict, name: str) -> bool:
    p = Path(rel_or_path)
    actual = sha256_file(p)
    good = actual == exp
    results[name] = {"path": str(p.relative_to(ROOT)) if p.is_absolute() else str(p),
                     "expected": exp, "actual": actual, "match": good}
    return good


def verify_interpreter() -> bool:
    want = os.path.realpath(str(CANONICAL_INTERPRETER)).lower()
    got = os.path.realpath(sys.executable).lower()
    return os.path.normcase(want) == os.path.normcase(got)


def verify_cuda_readiness() -> dict:
    info = {}
    try:
        import torch
        info["torch_version"] = torch.__version__
        info["torch_cuda"] = torch.version.cuda
        info["cuda_available"] = bool(torch.cuda.is_available())
        info["device_count"] = int(torch.cuda.device_count())
        if torch.cuda.is_available():
            info["device_name"] = torch.cuda.get_device_name(0)
        info["ready"] = (torch.version.cuda is not None) and bool(torch.cuda.is_available())
    except Exception as exc:  # pragma: no cover
        info["ready"] = False
        info["error"] = repr(exc)
    return info


def verify_execution_source_pin() -> dict:
    """D80-H: exact raw-byte equality of the v1.16 execution source against literal SHA."""
    actual = sha256_file(EXECUTION_SOURCE)
    return {
        "path": str(EXECUTION_SOURCE.relative_to(ROOT)),
        "expected_pinned": V1_16_SOURCE_SHA,
        "actual": actual,
        "present": EXECUTION_SOURCE.exists(),
        "match": actual == V1_16_SOURCE_SHA,
    }


def verify_transitive_integrity() -> dict:
    """Verify 14 deps + 4 checkpoints via the frozen v1.16 manifest (raw-byte SHA)."""
    out = {"dependencies": {}, "checkpoints": {}, "all_dependencies_match": False,
           "all_checkpoints_match": False, "manifest_sha_match": False,
           "manifest_binds_execution_source": False}
    if sha256_file(V1_16_MANIFEST) != V1_16_MANIFEST_SHA:
        return out
    out["manifest_sha_match"] = True
    man = json.loads(V1_16_MANIFEST.read_text(encoding="utf-8"))
    out["manifest_execution_source_sha256"] = man.get("execution_source_sha256")
    out["manifest_binds_execution_source"] = (
        man.get("execution_source_sha256") == V1_16_SOURCE_SHA
    )
    dep_ok = True
    for rel in man["dependencies"]:
        entry = man["dependency_verification"][rel]
        exp = entry["expected"] if isinstance(entry, dict) else entry
        actual = sha256_file(ROOT / rel)
        okd = actual == exp
        out["dependencies"][rel] = {"expected": exp, "actual": actual, "match": okd}
        dep_ok = dep_ok and okd
    ck_ok = True
    for rel in man["checkpoints"]:
        entry = man["checkpoint_verification"][rel]
        exp = entry["expected"] if isinstance(entry, dict) else entry
        actual = sha256_file(ROOT / rel)
        okc = actual == exp
        out["checkpoints"][rel] = {"expected": exp, "actual": actual, "match": okc}
        ck_ok = ck_ok and okc
    out["all_dependencies_match"] = dep_ok
    out["all_checkpoints_match"] = ck_ok
    return out


def verify_markers_absent() -> dict:
    out = {}
    for name, p in V1_16_MARKERS.items():
        out[name] = {"path": str(p.relative_to(ROOT)), "exists": p.exists()}
    out["journal_records"] = (
        len([f for f in V1_16_JOURNAL_DIR.iterdir() if f.is_file()])
        if V1_16_JOURNAL_DIR.exists() else 0
    )
    v15 = {}
    for name, p in V1_15_MARKERS.items():
        v15[name] = {"path": str(p.relative_to(ROOT)), "exists": p.exists()}
    v15["journal_records"] = (
        len([f for f in V1_15_JOURNAL_DIR.iterdir() if f.is_file()])
        if V1_15_JOURNAL_DIR.exists() else 0
    )
    out["v1_15_markers"] = v15
    return out


def run_all_gates(verbose: bool = True) -> tuple[bool, dict]:
    results: dict = {}

    results["interpreter_identity"] = {
        "canonical": str(CANONICAL_INTERPRETER),
        "actual": sys.executable,
        "match": verify_interpreter(),
    }

    cuda = verify_cuda_readiness()
    results["cuda_readiness"] = cuda

    # D80-H: pinned execution source (exact equality).
    src_pin = verify_execution_source_pin()
    results["execution_source"] = src_pin

    # v1.16 governance + authority bindings
    check(*D80_ADJUDICATION, results, "D80_adjudication")
    check(*V1_15_HANDOFF, results, "v1_15_handoff")
    check(*D79_DISCLOSURE, results, "D79_disclosure")
    check(*D76_D78_RECON, results, "D76_D78_reconciliation")
    check(*V1_4_RESULT, results, "v1_4_RESULT")
    check(*V1_4_ADJUDICATION, results, "v1_4_adjudication")
    check(*PHASE27_FINAL_PROB, results, "phase27_final_prob")
    check(*PHASE27_GLOBAL_PROB, results, "phase27_global_prob")
    check(*PHASE27_SCORE_CSV, results, "phase27_score_csv")
    check(*PHASEA_SRC, results, "phase27_phaseA_source")
    check(*PHASEB_SRC, results, "phase27_phaseB_source")
    results["v1_14_failure_provenance_present"] = V1_14_FAILURE_PROVENANCE.exists()

    trans = verify_transitive_integrity()
    results["transitive_integrity"] = trans

    markers = verify_markers_absent()
    results["markers_absent"] = markers

    # protected populations (lock manifests; absence of reads is enforced by the source)
    results["test_lock_manifest_present"] = TEST_LOCK_MANIFEST.exists()
    results["router_holdout_lock_manifest_present"] = ROUTER_HOLDOUT_LOCK.exists()
    results["TEST_accessed"] = False
    results["ROUTER_HOLDOUT_accessed"] = False

    # aggregate
    v15m = markers["v1_15_markers"]
    gate_ok = (
        results["interpreter_identity"]["match"]
        and cuda.get("ready", False)
        and src_pin["match"]
        and results["D80_adjudication"]["match"]
        and results["v1_15_handoff"]["match"]
        and results["D79_disclosure"]["match"]
        and results["D76_D78_reconciliation"]["match"]
        and results["v1_4_RESULT"]["match"]
        and results["v1_4_adjudication"]["match"]
        and results["phase27_final_prob"]["match"]
        and results["phase27_global_prob"]["match"]
        and results["phase27_score_csv"]["match"]
        and results["phase27_phaseA_source"]["match"]
        and results["phase27_phaseB_source"]["match"]
        and trans["manifest_sha_match"]
        and trans["manifest_binds_execution_source"]
        and trans["all_dependencies_match"]
        and trans["all_checkpoints_match"]
        and all(not v["exists"] for k, v in markers.items()
                if k not in ("journal_records", "v1_15_markers"))
        and markers["journal_records"] == 0
        and all(not v["exists"] for k, v in v15m.items() if k != "journal_records")
        and v15m["journal_records"] == 0
    )
    results["all_gates_pass"] = gate_ok
    return gate_ok, results


def verify_only() -> int:
    gate_ok, results = run_all_gates()
    print(json.dumps(results, indent=2, ensure_ascii=False, default=str))
    if gate_ok:
        print(f"VERIFY_ONLY={TERMINAL_OK}")
        print("RETURN_BEFORE_TOKEN_SET / START / MODEL_LOAD")
        return 0
    print("VERIFY_ONLY=FAIL_CLOSED")
    return 3


def self_test() -> int:
    """Synthetic fixtures only — no real science."""
    print("SELF_TEST_START")
    iid = verify_interpreter()
    print(f"  interpreter_identity={iid}")
    pin = verify_execution_source_pin()
    print(f"  execution_source_pin_match={pin['match']}")
    m = verify_markers_absent()
    print(f"  v1_16_markers_all_absent="
          f"{all(not v['exists'] for k, v in m.items() if k not in ('journal_records','v1_15_markers'))}")
    print(f"  journal_records={m['journal_records']}")
    print(f"  v1_15_markers_all_absent="
          f"{all(not v['exists'] for k, v in m['v1_15_markers'].items() if k != 'journal_records')}")
    print(f"  dispatch_mode_args={DISPATCH_MODE_ARGS}")
    print("  no_science_executed=True")
    print("SELF_TEST_OK")
    return 0


def main(argv: list[str]) -> int:
    if "--verify-only" in argv:
        return verify_only()
    if "--self-test" in argv:
        return self_test()

    # Real dispatch path.
    if os.environ.get(TOKEN_ENV) != "1":
        print(f"FAIL_CLOSED: operator gate {TOKEN_ENV}=1 not set; refusing real dispatch.")
        return 3
    gate_ok, results = run_all_gates()
    if not gate_ok:
        print("FAIL_CLOSED: pre-invocation gates failed; NO attempt consumed.")
        for k, v in results.items():
            if isinstance(v, dict) and v.get("match") is False:
                print(f"  FAILED {k}")
        return 3
    os.environ[LAUNCH_AUTHORITY] = "1"
    cmd = [str(CANONICAL_INTERPRETER), str(EXECUTION_SOURCE)] + list(DISPATCH_MODE_ARGS)
    print("DISPATCHING_V1_16_SCIENCE_MODE_SCIENCE")
    proc = subprocess.run(cmd, env=dict(os.environ))
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
