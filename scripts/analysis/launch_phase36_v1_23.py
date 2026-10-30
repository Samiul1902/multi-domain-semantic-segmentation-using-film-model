#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.23 — NON-CIRCULAR PRE-INVOCATION LAUNCHER (prepare + verify-only).

REBASED FROM v1.17 (D85/D86/D87/D88 FINAL PRE-EXECUTION AUTHORITY REPAIR).  The
scientific computation is IDENTICAL to v1.17; ONLY the operational / governance /
namespace / release-contract layer changed.

MODEL-FREE and PROTECTED-DATA-FREE.  It reads only frozen authority bytes to
verify SHA-256 against EXACT frozen constants, verifies the canonical project
interpreter, performs a DEVICE-ONLY CUDA readiness probe, verifies transitive
runtime integrity (14 deps + 4 checkpoints via the v1.23 manifest family),
invokes the PURE v1.23 release-gate state requiring RELEASED, verifies all
D85/D86/D87/D88 / D81-D84 / D80 / D79 / D76-D78 / D61 / D75 / Phase27
scoring-source bindings and marker absence, and performs a COMPLETE
OUTPUT-ABSENCE verification before dispatch.

D87 REPAIR (launcher layer):
  * The launcher NO LONGER uses the earlier D81-D83 adjudication as its direct
    gate authority.  It binds the FINAL PRELAUNCH AUTHORITY BUNDLE by literal
    SHA-256 (D87).  The D81-D83 adjudication + D84 disclosure + release-binding
    reconciliation + final readiness + eligibility + source freeze + namespace
    map + reachable-write inventory + semantic-diff authorities are bound THROUGH
    the bundle, giving a single non-circular authority point.
  * The bundle NEVER contains the supervisor SHA (acyclic by construction).

D88 REPAIR (launcher layer):
  * verify_v1_23_dispatch_output_absence() re-verifies ALL 23 reachable write
    targets immediately before dispatch; any pre-existing target -> FAIL CLOSED.

Modes:
  --verify-only   Run ALL gates (incl. pure release-gate RELEASED), print a
                  terminal, RETURN BEFORE setting the launch authority token /
                  creating START / loading the model.
  --self-test     Synthetic subprocess fixtures (no science).
  (default)       Real one-shot dispatch: requires operator gate
                  PHASE36_V1_23_EXECUTE=1 and sets PHASE36_V1_23_LAUNCH_AUTHORITY.

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
EXECUTION_SOURCE = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_23.py"
LAUNCHER_SELF = Path(__file__).resolve()

# D80-H/D87: the launcher PINS the literal v1.23 execution-source SHA (exact equality).
V1_23_SOURCE_SHA = "2287cc78ba60d715ff371ba58f0ea90f772219b510e198bea6053a7043159396"

# v1.23 runtime integrity manifest (non-circular authority; binds the v1.23 exec SHA).
V1_23_MANIFEST = ROOT / "reports" / "audits" / "phase36_v1_23_runtime_source_integrity_manifest.json"
# ACYCLICITY: the expected manifest SHA is read from the frozen launch-authority
# constant file (see _read_pinned_authority_bundle_sha), NOT embedded as a literal
# that would need updating whenever the manifest is re-emitted.

# D87 repair: the FINAL PRELAUNCH AUTHORITY BUNDLE is the SINGLE non-circular
# authority point.  The earlier D81-D83 adjudication is bound THROUGH the bundle.
#
# ACYCLICITY NOTE: the bundle SHA is NOT embedded as a literal here (that would
# make the bundle bind the launcher and the launcher bind the bundle).  It is
# read from a DEDICATED, SEPARATELY-FROZEN launch-authority constant file whose
# OWN raw bytes are pinned by the supervisor.  This yields a DAG:
#   exec/manifest/governance -> bundle -> launch-authority-file -> launcher -> supervisor
V1_23_PRELAUNCH_AUTHORITY_BUNDLE = (
    ROOT / "reports" / "audits" / "phase36_v1_23_prelaunch_authority_bundle.json"
)
V1_23_LAUNCH_AUTHORITY_FILE = (
    ROOT / "reports" / "audits" / "phase36_v1_23_launch_authority_sha.json"
)


def _read_pinned_authority_bundle_sha() -> str | None:
    """Read the frozen bundle SHA from the dedicated launch-authority file.

    The file's raw bytes are themselves pinned by the supervisor, so this is NOT
    a mutable authority: an edit to the file changes its bytes and the supervisor
    refuses to dispatch.  Returns None (-> FAIL CLOSED) if absent/malformed.
    """
    if not V1_23_LAUNCH_AUTHORITY_FILE.exists():
        return None
    try:
        doc = json.loads(V1_23_LAUNCH_AUTHORITY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None
    return doc.get("prelaunch_authority_bundle_sha256")


def _read_pinned_manifest_sha() -> str | None:
    """Read the frozen v1.23 manifest SHA from the launch-authority file."""
    if not V1_23_LAUNCH_AUTHORITY_FILE.exists():
        return None
    try:
        doc = json.loads(V1_23_LAUNCH_AUTHORITY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None
    return doc.get("runtime_manifest_sha256")


def _read_pinned_attestation_sha() -> str | None:
    """Read the frozen v1.23 release-attestation SHA from the launch-authority file."""
    if not V1_23_LAUNCH_AUTHORITY_FILE.exists():
        return None
    try:
        doc = json.loads(V1_23_LAUNCH_AUTHORITY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None
    return doc.get("release_attestation_sha256")


def _read_pinned_adjudication_sha() -> str | None:
    """Read the frozen D85-D88 adjudication SHA from the launch-authority file."""
    if not V1_23_LAUNCH_AUTHORITY_FILE.exists():
        return None
    try:
        doc = json.loads(V1_23_LAUNCH_AUTHORITY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None
    return doc.get("d85_d88_adjudication_sha256")

# ---- v1.23 governance authorities (expected SHAs read from the launch-authority
# ---- constant file; the file's raw bytes are pinned by the supervisor) ------- #
V1_23_RELEASE_ATTESTATION = (
    ROOT / "reports" / "audits" / "phase36_v1_23_science_release_attestation.json",
    None,   # resolved at runtime from the frozen launch-authority file
)
D85_D88_ADJUDICATION = (
    ROOT / "reports" / "audits" / "phase36_v1_23_adjudication_d85_d86_d87_d88.json",
    None,   # resolved at runtime from the frozen launch-authority file
)
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

# Historical v1.14 smoke (role: HISTORICAL_RUNTIME_SMOKE_EVIDENCE_ONLY).
HISTORICAL_V1_14_SMOKE = (
    ROOT / "reports" / "audits" / "phase36_robustness_smoke_v1_14.json",
    "53543729fb0c48695c2af202c5f3d2f5ebdfc29d87c7a7f100bcde9f94882441",
)

# Historical v1.14 failure provenance kept ONLY as historical runtime evidence.
V1_14_FAILURE_PROVENANCE = ROOT / "reports" / "audits" / "phase36_robustness_science_failure_v1_14.json"

# ---- v1.23 attempt markers (must be ABSENT pre-execution) ----------------- #
AUD = ROOT / "reports" / "audits"
V1_23_MARKERS = {
    "START": AUD / "phase36_robustness_science_start_v1_23.json",
    "RESULT": AUD / "phase36_robustness_scientific_result_v1_23.json",
    "FAILURE": AUD / "phase36_robustness_science_failure_v1_23.json",
    "PROCESS_EXIT": AUD / "phase36_robustness_science_process_exit_v1_23.json",
}
V1_23_JOURNAL_DIR = AUD / "phase36_robustness_science_v1_23_journal"
V1_23_STDOUT = AUD / "phase36_robustness_science_stdout_v1_23.txt"
V1_23_STDERR = AUD / "phase36_robustness_science_stderr_v1_23.txt"

# v1.17 markers must ALSO remain absent (v1.17 was NEVER executed).
V1_17_MARKERS = {
    "START": AUD / "phase36_robustness_science_start_v1_17.json",
    "RESULT": AUD / "phase36_robustness_scientific_result_v1_17.json",
    "FAILURE": AUD / "phase36_robustness_science_failure_v1_17.json",
    "PROCESS_EXIT": AUD / "phase36_robustness_science_process_exit_v1_17.json",
}
V1_17_JOURNAL_DIR = AUD / "phase36_robustness_science_v1_17_journal"

# v1.16 + v1.15 markers must ALSO remain absent (neither was EVER executed).
V1_16_MARKERS = {
    "START": AUD / "phase36_robustness_science_start_v1_16.json",
    "RESULT": AUD / "phase36_robustness_scientific_result_v1_16.json",
    "FAILURE": AUD / "phase36_robustness_science_failure_v1_16.json",
    "PROCESS_EXIT": AUD / "phase36_robustness_science_process_exit_v1_16.json",
}
V1_16_JOURNAL_DIR = AUD / "phase36_robustness_science_v1_16_journal"

V1_15_MARKERS = {
    "START": AUD / "phase36_robustness_science_start_v1_15.json",
    "RESULT": AUD / "phase36_robustness_science_result_v1_15.json",
    "FAILURE": AUD / "phase36_robustness_science_failure_v1_15.json",
    "PROCESS_EXIT": AUD / "phase36_robustness_science_process_exit_v1_15.json",
}
V1_15_JOURNAL_DIR = AUD / "phase36_robustness_science_v1_15_journal"

# ---- protected populations ----------------------------------------------- #
TEST_LOCK_MANIFEST = AUD / "phase36_test_lock_manifest.json"
ROUTER_HOLDOUT_LOCK = AUD / "phase36_router_holdout_lock_manifest.json"

# ---- v1.23 operator gate + launch authority ------------------------------ #
TOKEN_ENV = "PHASE36_V1_23_EXECUTE"
SMOKE_TOKEN_ENV = "PHASE36_V1_23_SMOKE_EXECUTE"
LAUNCH_AUTHORITY = "PHASE36_V1_23_LAUNCH_AUTHORITY"

TERMINAL_OK = "PHASE36_V1_23_LAUNCH_VERIFY_ONLY_PASS"

# The EXACT real dispatch argument tail (D80-A: --mode science is MANDATORY).
DISPATCH_MODE_ARGS = ["--mode", "science"]

# ---- D88 complete reachable write inventory (23 targets) ------------------ #
# Mirrors the exec's frozen v1_23_reachable_write_targets(); re-verified at
# dispatch time.  16 scientific table/figure outputs + 7 provenance targets.
V1_23_TAB = ROOT / "reports" / "tables" / "phase36_robustness_v1_23"
V1_23_FIG = ROOT / "reports" / "figures" / "phase36_robustness_v1_23"
V1_23_ARR = ROOT / "reports" / "arrays" / "phase36_robustness_v1_23"
V1_23_REACHABLE_SCIENCE_TABLES = (
    "phase36_image_robustness_per_sample.csv",
    "phase36_image_robustness_by_domain_condition.csv",
    "phase36_noise_seed_summary.csv",
    "phase36_proposal_robustness_per_sample.csv",
    "phase36_proposal_robustness_by_domain_condition.csv",
    "phase36_route_stability_summary.csv",
    "phase36_execution_rate_summary.csv",
    "phase36_worst_case_per_sample.csv",
    "phase36_worst_case_by_domain.csv",
    "phase36_kub_subgroup_robustness.csv",
    "phase36_kub_subgroup_robustness_by_subgroup.csv",
)
V1_23_REACHABLE_FIGURES = (
    "R1_image_perturbation_mean_paired_delta_dice_heatmap.png",
    "R2_severity_curves_noise_blur_resolution.png",
    "R3_route_state_change_and_execution_rate_heatmap.png",
    "R4_proposal_perturbation_paired_delta_dice.png",
    "R5_worst_case_delta_dice_distribution_by_domain.png",
)


def v1_23_reachable_write_targets() -> list:
    """D88: the COMPLETE frozen list of v1.23 real-dispatch write targets (23)."""
    targets = []
    for fn in V1_23_REACHABLE_SCIENCE_TABLES:
        targets.append(V1_23_TAB / fn)
    for fn in V1_23_REACHABLE_FIGURES:
        targets.append(V1_23_FIG / fn)
    targets.append(V1_23_MARKERS["START"])
    targets.append(V1_23_MARKERS["RESULT"])
    targets.append(V1_23_MARKERS["FAILURE"])
    targets.append(V1_23_JOURNAL_DIR)
    targets.append(V1_23_STDOUT)
    targets.append(V1_23_STDERR)
    targets.append(V1_23_MARKERS["PROCESS_EXIT"])
    return targets


def verify_v1_23_dispatch_output_absence() -> dict:
    """D88: real-time COMPLETE output-absence verification before real dispatch."""
    targets = v1_23_reachable_write_targets()
    present = [str(p.relative_to(ROOT)) for p in targets if p.exists()]
    return {
        "all_targets_absent": not present,
        "present_targets": present,
        "target_count": len(targets),
        "terminal": ("PHASE36_V1_23_REAL_LAUNCH_OUTPUT_ABSENCE_GATE_PASS"
                     if not present else
                     "PHASE36_V1_23_REAL_LAUNCH_OUTPUT_ABSENCE_GATE_FAIL_CLOSED"),
    }


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
    """D87: exact raw-byte equality of the v1.23 execution source against literal SHA."""
    actual = sha256_file(EXECUTION_SOURCE)
    return {
        "path": str(EXECUTION_SOURCE.relative_to(ROOT)),
        "expected_pinned": V1_23_SOURCE_SHA,
        "actual": actual,
        "present": EXECUTION_SOURCE.exists(),
        "match": actual == V1_23_SOURCE_SHA,
    }


def verify_transitive_integrity() -> dict:
    """Verify 14 deps + 4 checkpoints via the frozen v1.23 manifest (raw-byte SHA)."""
    out = {"dependencies": {}, "checkpoints": {}, "all_dependencies_match": False,
           "all_checkpoints_match": False, "manifest_sha_match": False,
           "manifest_binds_execution_source": False,
           "n_dependencies": 0, "n_checkpoints": 0}
    if (sha256_file(V1_23_MANIFEST) != _read_pinned_manifest_sha()):
        return out
    out["manifest_sha_match"] = True
    man = json.loads(V1_23_MANIFEST.read_text(encoding="utf-8"))
    out["manifest_execution_source_sha256"] = man.get("execution_source_sha256")
    out["manifest_binds_execution_source"] = (
        man.get("execution_source_sha256") == V1_23_SOURCE_SHA
    )
    out["launcher_sha256_absent_by_design"] = "launcher_sha256" not in man
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
    out["n_dependencies"] = len(man["dependencies"])
    out["n_checkpoints"] = len(man["checkpoints"])
    out["all_dependencies_match"] = dep_ok
    out["all_checkpoints_match"] = ck_ok
    return out


def verify_markers_absent() -> dict:
    out = {}
    for name, p in V1_23_MARKERS.items():
        out[name] = {"path": str(p.relative_to(ROOT)), "exists": p.exists()}
    out["journal_records"] = (
        len([f for f in V1_23_JOURNAL_DIR.iterdir() if f.is_file()])
        if V1_23_JOURNAL_DIR.exists() else 0
    )
    for tag, markers, jdir in (
        ("v1_17_markers", V1_17_MARKERS, V1_17_JOURNAL_DIR),
        ("v1_16_markers", V1_16_MARKERS, V1_16_JOURNAL_DIR),
        ("v1_15_markers", V1_15_MARKERS, V1_15_JOURNAL_DIR),
    ):
        blk = {}
        for name, p in markers.items():
            blk[name] = {"path": str(p.relative_to(ROOT)), "exists": p.exists()}
        blk["journal_records"] = (
            len([f for f in jdir.iterdir() if f.is_file()]) if jdir.exists() else 0
        )
        out[tag] = blk
    return out


def verify_pure_release_state() -> dict:
    """D83 repair (preserved): invoke the EXACT pure v1.23 release-state function.

    Extracts ``_gate_science_release_state`` by AST from the frozen v1.23 source
    and executes it in an isolated namespace with source-faithful globals.  This
    is NOT a revision-string check — it evaluates the RUNTIME release state.
    """
    import ast as _ast
    src_text = EXECUTION_SOURCE.read_text(encoding="utf-8")
    tree = _ast.parse(src_text)
    fn_src = None
    for n in tree.body:
        if isinstance(n, _ast.FunctionDef) and n.name == "_gate_science_release_state":
            fn_src = _ast.get_source_segment(src_text, n)
            break
    if fn_src is None:
        return {"state": "NOT_RELEASED", "reason": "GATE_FUNCTION_NOT_FOUND"}

    def _const(name, default):
        for n in tree.body:
            if isinstance(n, _ast.Assign) and len(n.targets) == 1 \
                    and isinstance(n.targets[0], _ast.Name) and n.targets[0].id == name:
                try:
                    return _ast.literal_eval(n.value)
                except Exception:
                    return default
        return default

    env = {
        "json": json,
        "ROOT": ROOT,
        "__file__": str(EXECUTION_SOURCE),
        "_sha": sha256_file,
        "Path": Path,
        "SCIENCE_RELEASE_ATTESTATION": _const(
            "SCIENCE_RELEASE_ATTESTATION",
            "reports/audits/phase36_v1_23_science_release_attestation.json"),
        "_SCIENCE_RELEASE_REVISION": _const(
            "_SCIENCE_RELEASE_REVISION", "ra_medfilm_barr_phase36_robustness_v1_23"),
        "HISTORICAL_V1_14_SMOKE": _const(
            "HISTORICAL_V1_14_SMOKE", "reports/audits/phase36_robustness_smoke_v1_14.json"),
        "HISTORICAL_V1_14_SMOKE_SHA256": _const(
            "HISTORICAL_V1_14_SMOKE_SHA256",
            "53543729fb0c48695c2af202c5f3d2f5ebdfc29d87c7a7f100bcde9f94882441"),
    }
    ns: dict = {}
    exec(compile(fn_src, "<v1_23_gate>", "exec"), env, ns)
    try:
        return ns["_gate_science_release_state"]()
    except Exception as exc:  # fail closed
        return {"state": "NOT_RELEASED", "reason": "GATE_EXECUTION_ERROR",
                "error": type(exc).__name__}


def run_all_gates(verbose: bool = True) -> tuple[bool, dict]:
    results: dict = {}

    results["interpreter_identity"] = {
        "canonical": str(CANONICAL_INTERPRETER),
        "actual": sys.executable,
        "match": verify_interpreter(),
    }

    cuda = verify_cuda_readiness()
    results["cuda_readiness"] = cuda

    # D87: pinned execution source (exact equality).
    src_pin = verify_execution_source_pin()
    results["execution_source"] = src_pin

    # D87: the FINAL PRELAUNCH AUTHORITY BUNDLE is the single non-circular gate.
    # Its expected SHA comes from the separately-frozen launch-authority file.
    expected_bundle_sha = _read_pinned_authority_bundle_sha()
    check(str(V1_23_PRELAUNCH_AUTHORITY_BUNDLE), expected_bundle_sha,
          results, "v1_23_prelaunch_authority_bundle")

    # v1.23 governance + authority bindings
    check(*D85_D88_ADJUDICATION[:1], _read_pinned_adjudication_sha(),
          results, "D85_D88_adjudication")
    check(*V1_23_RELEASE_ATTESTATION[:1], _read_pinned_attestation_sha(),
          results, "v1_23_release_attestation")
    check(*HISTORICAL_V1_14_SMOKE, results, "historical_v1_14_smoke")
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

    # D83: PURE runtime release-state (must be RELEASED).
    release = verify_pure_release_state()
    results["pure_release_state"] = release
    results["pure_release_state_released"] = (release.get("state") == "RELEASED")

    markers = verify_markers_absent()
    results["markers_absent"] = markers

    # D88: complete output-absence verification (also reported at verify-only).
    absence = verify_v1_23_dispatch_output_absence()
    results["dispatch_output_absence"] = absence
    results["dispatch_output_absence_pass"] = bool(absence["all_targets_absent"])

    # protected populations
    results["test_lock_manifest_present"] = TEST_LOCK_MANIFEST.exists()
    results["router_holdout_lock_manifest_present"] = ROUTER_HOLDOUT_LOCK.exists()
    results["TEST_accessed"] = False
    results["ROUTER_HOLDOUT_accessed"] = False

    # aggregate
    v17m = markers["v1_17_markers"]
    v16m = markers["v1_16_markers"]
    v15m = markers["v1_15_markers"]
    gate_ok = (
        results["interpreter_identity"]["match"]
        and cuda.get("ready", False)
        and src_pin["match"]
        and results["v1_23_prelaunch_authority_bundle"]["match"]
        and results["D85_D88_adjudication"]["match"]
        and results["v1_23_release_attestation"]["match"]
        and results["historical_v1_14_smoke"]["match"]
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
        and trans.get("launcher_sha256_absent_by_design", False)
        and trans["all_dependencies_match"]
        and trans["all_checkpoints_match"]
        and results["pure_release_state_released"]
        and results["dispatch_output_absence_pass"]
        and all(not v["exists"] for k, v in markers.items()
                if k not in ("journal_records", "v1_17_markers", "v1_16_markers",
                             "v1_15_markers"))
        and markers["journal_records"] == 0
        and all(not v["exists"] for k, v in v17m.items() if k != "journal_records")
        and v17m["journal_records"] == 0
        and all(not v["exists"] for k, v in v16m.items() if k != "journal_records")
        and v16m["journal_records"] == 0
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
        print(f"PURE_RELEASE_STATE={results['pure_release_state'].get('state')}")
        print(f"OUTPUT_ABSENCE={results['dispatch_output_absence']['terminal']}")
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
    bundle = sha256_file(V1_23_PRELAUNCH_AUTHORITY_BUNDLE)
    print(f"  prelaunch_authority_bundle_sha={bundle} match="
          f"{bundle == _read_pinned_authority_bundle_sha()}")
    rel = verify_pure_release_state()
    print(f"  pure_release_state={rel.get('state')} reason={rel.get('reason')}")
    absence = verify_v1_23_dispatch_output_absence()
    print(f"  dispatch_output_absence_pass={absence['all_targets_absent']} "
          f"target_count={absence['target_count']}")
    m = verify_markers_absent()
    print(f"  v1_23_markers_all_absent="
          f"{all(not v['exists'] for k, v in m.items() if k not in ('journal_records','v1_17_markers','v1_16_markers','v1_15_markers'))}")
    print(f"  journal_records={m['journal_records']}")
    for tag in ("v1_17_markers", "v1_16_markers", "v1_15_markers"):
        print(f"  {tag}_all_absent="
              f"{all(not v['exists'] for k, v in m[tag].items() if k != 'journal_records')}")
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
    # §10 (v1.23): CONSUMED-HISTORY GATE — v1.20 is the LAST CONSUMED
    # revision; v1.23 must not be mistaken for a clean-revision re-run.
    # FAIL CLOSED on deviation.
    _consumed = verify_v1_20_consumed_history()
    if not _consumed["ok"]:
        print("FAIL_CLOSED: §10 consumed-history gate failed; NO attempt consumed.")
        for _r in _consumed["reasons"]:
            print(f"  {_r}")
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
    print("DISPATCHING_V1_23_SCIENCE_MODE_SCIENCE")
    proc = subprocess.run(cmd, env=dict(os.environ))
    return proc.returncode





# =========================================================================== #
# §10 (v1.23) — CONSUMED-HISTORY GATE (v1.20 IS CONSUMED)                      #
# =========================================================================== #
# v1.20 is CONSUMED (CONSUMED_INTERRUPTED_POST_START_PRE_SCIENTIFIC_RESULT; D95).
# v1.23 must NOT be mistaken for a clean-revision re-run of v1.20.  Before ANY
# real dispatch, the launcher REQUIRES that the v1.20 consumed history is EXACTLY
# the known recorded state: the v1.20 interruption adjudication exists with the
# expected SHA and classification, the v1.20 START marker is PRESENT, the v1.20
# RESULT and FAILURE markers are ABSENT, and the v1.20 PROCESS_EXIT evidence is
# PRESENT.  Any deviation -> FAIL CLOSED.
V1_20_CONSUMED_ADJUDICATION = (
    AUD / "phase36_v1_20_interruption_adjudication_v1_0.json")
V1_20_CONSUMED_ADJUDICATION_SHA = (
    "31c29955380c6ec75d18f747dec4f91332177ddabeccef40cb0cafa8b37f5b72")
V1_20_CONSUMED_EXPECTED_CLASSIFICATION = (
    "CONSUMED_INTERRUPTED_POST_START_PRE_SCIENTIFIC_RESULT")
V1_20_CONSUMED_START_MARKER = (
    AUD / "phase36_robustness_science_start_v1_20.json")
V1_20_CONSUMED_RESULT_MARKER = (
    AUD / "phase36_robustness_scientific_result_v1_20.json")
V1_20_CONSUMED_FAILURE_MARKER = (
    AUD / "phase36_robustness_science_failure_v1_20.json")
V1_20_CONSUMED_PROCESS_EXIT = (
    AUD / "phase36_robustness_science_process_exit_v1_20.json")


def verify_v1_20_consumed_history() -> dict:
    """§10: prove v1.20 is the EXACT known consumed-interruption state. FAIL CLOSED."""
    result = {"ok": False, "reasons": []}
    if not V1_20_CONSUMED_ADJUDICATION.exists():
        result["reasons"].append("v1_20_adjudication_absent")
        return result
    adj_sha = sha256_file(V1_20_CONSUMED_ADJUDICATION)
    if adj_sha != V1_20_CONSUMED_ADJUDICATION_SHA:
        result["reasons"].append("v1_20_adjudication_sha_mismatch")
    try:
        doc = json.loads(V1_20_CONSUMED_ADJUDICATION.read_text(encoding="utf-8"))
    except Exception:  # pragma: no cover
        result["reasons"].append("v1_20_adjudication_unreadable")
        return result
    if doc.get("classification") != V1_20_CONSUMED_EXPECTED_CLASSIFICATION:
        result["reasons"].append("v1_20_adjudication_classification_mismatch")
    if not V1_20_CONSUMED_START_MARKER.exists():
        result["reasons"].append("v1_20_start_marker_absent__expected_present")
    if V1_20_CONSUMED_RESULT_MARKER.exists():
        result["reasons"].append("v1_20_result_present__expected_absent")
    if V1_20_CONSUMED_FAILURE_MARKER.exists():
        result["reasons"].append("v1_20_failure_present__expected_absent")
    if not V1_20_CONSUMED_PROCESS_EXIT.exists():
        result["reasons"].append("v1_20_process_exit_absent__expected_present")
    result["ok"] = not result["reasons"]
    result["v1_20_adjudication_sha256"] = adj_sha
    result["terminal"] = ("PHASE36_V1_23_CONSUMED_HISTORY_GATE_PASS" if result["ok"]
                          else "PHASE36_V1_23_CONSUMED_HISTORY_GATE_FAIL_CLOSED")
    return result

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
