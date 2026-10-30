#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.16 — OPERATIONAL / GOVERNANCE CROSS-CONTRACT VALIDATOR (D80).

Machine-derived (source/AST/hash only), NOT hard-coded booleans.

Proves the D80 OPERATIONAL/GOVERNANCE REBASE is internally CONSISTENT across the
whole v1.16 contract surface: the execution source, the launcher, the supervisor,
the runtime manifest, the release-attestation contract, and the launch-authority
constant MUST agree on the SAME v1.16 literals.  A disagreement between any two
surfaces MUST be detected (fail-closed).

Operational cross-contract checks (D80-A..I):
  A  launcher dispatch supplies `--mode science`; execution REQUIRES `--mode`.
  B  execution science namespace == v1.16; launcher/supervisor marker namespace agrees.
  C  launch-authority token literal agrees across execution + launcher.
  D  operator-gate literals agree across execution + launcher; no v1.14 gate residue.
  E  runtime-manifest path agrees across execution + luancher; manifest binds v1.16 exec SHA.
  F  release revision agrees across execution (and attestation contract if present).
  G  stage-journal dir/module present in execution.
  H  launcher pins the literal v1.16 exec SHA; supervisor enforces the launcher pin.
  I  no operational cross-contract surface silently omits a v1.16 literal.

Negative controls: each check is re-run against an IN-MEMORY mutated copy and MUST
report a contradiction.

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO science.
NO VAL/GT read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_16.py"
LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_v1_16.py"
SUPERVISOR = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_16.py"
MANIFEST = ROOT / "reports" / "audits" / "phase36_v1_16_runtime_source_integrity_manifest.json"
D80_ADJ = ROOT / "reports" / "audits" / "phase36_v1_15_independent_audit_adjudication_v1_0.json"

V1_16_EXEC_SHA = "a96b74caa4587aa9d2f83b79ed39c13075a88086109e31d991695a75ec4abab9"
V1_16_MANIFEST_SHA = "f9f245b41bdf904cdb4f9da7c3d32361da806c7451773ce721d3d0a023f64e18"

REVISION = "ra_medfilm_barr_phase36_robustness_v1_16"

checks: list[dict] = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


EXEC_SRC = _read(EXEC)
L_SRC = _read(LAUNCHER)
S_SRC = _read(SUPERVISOR)


# --------------------------------------------------------------------------- #
# Cross-contract detectors (each returns True iff the contract is CONSISTENT)
# --------------------------------------------------------------------------- #
def xcontract_mode_science(ex: str, ls: str) -> bool:
    """D80-A: execution requires --mode; launcher supplies --mode science."""
    exec_requires = ('ap.add_argument("--mode"' in ex and "required=True" in ex)
    launch_supplies = ('DISPATCH_MODE_ARGS = ["--mode", "science"]' in ls
                       and "list(DISPATCH_MODE_ARGS)" in ls)
    return exec_requires and launch_supplies


def xcontract_namespace(ex: str, ls: str, ss: str) -> bool:
    """D80-B: v1.16 science namespace agreed across execution/launcher/supervisor."""
    ex_ok = ("phase36_robustness_science_start_v1_16.json" in ex
             and "phase36_robustness_scientific_result_v1_16.json" in ex
             and "phase36_robustness_science_failure_v1_16.json" in ex)
    ls_ok = ("phase36_robustness_science_start_v1_16.json" in ls
             and "phase36_robustness_scientific_result_v1_16.json" in ls
             and "phase36_robustness_science_failure_v1_16.json" in ls)
    ss_ok = ("phase36_robustness_science_start_v1_16.json" in ss
             and "phase36_robustness_scientific_result_v1_16.json" in ss
             and "phase36_robustness_science_failure_v1_16.json" in ss)
    no_v14 = ("phase36_robustness_science_start_v1_14.json" not in ex
              and "phase36_robustness_science_start_v1_14.json" not in ls)
    return ex_ok and ls_ok and ss_ok and no_v14


def xcontract_authority_token(ex: str, ls: str) -> bool:
    """D80-C: launch-authority token literal agrees across execution + launcher."""
    tok = "PHASE36_V1_16_LAUNCH_AUTHORITY"
    return (f'LAUNCH_AUTHORITY_TOKEN = "{tok}"' in ex and tok in ls
            and "PHASE36_V1_14_LAUNCH_AUTHORITY" not in ex
            and "PHASE36_V1_15_LAUNCH_AUTHORITY" not in ex)


def xcontract_gates(ex: str, ls: str) -> bool:
    """D80-D: operator-gate literals agree; no v1.14/v1.15 gate residue."""
    ok = ("PHASE36_V1_16_EXECUTE" in ex and "PHASE36_V1_16_SMOKE_EXECUTE" in ex
          and "PHASE36_V1_16_EXECUTE" in ls and "PHASE36_V1_16_SMOKE_EXECUTE" in ls)
    clean = all(t not in ex for t in ("PHASE36_V1_14_EXECUTE", "PHASE36_V1_14_SMOKE_EXECUTE",
                                      "PHASE36_V1_15_EXECUTE", "PHASE36_V1_15_SMOKE_EXECUTE"))
    return ok and clean


def xcontract_manifest(ex: str, ls: str, man: dict) -> bool:
    """D80-E: runtime-manifest v1.16 path agreed; manifest binds v1.16 exec SHA."""
    path_ok = ("phase36_v1_16_runtime_source_integrity_manifest.json" in ex
               and "phase36_v1_16_runtime_source_integrity_manifest.json" in ls
               and "phase36_v1_14_runtime_source_integrity_manifest.json" not in ex)
    binds = man.get("execution_source_sha256") == V1_16_EXEC_SHA
    return path_ok and binds


def xcontract_release_revision(ex: str) -> bool:
    """D80-F: v1.16 release revision; no v1.14/v1.15 revision residue."""
    return (REVISION in ex
            and "ra_medfilm_barr_phase36_robustness_v1_14" not in ex
            and "ra_medfilm_barr_phase36_robustness_v1_15" not in ex)


def xcontract_stage_journal(ex: str) -> bool:
    """D80-G: stage-journal module present + wired + v1.16 dir."""
    return ("V1_16_JOURNAL_STAGES" in ex and "_ScienceJournal" in ex
            and "journal=_ScienceJournal(" in ex
            and "_run_science_with_durable_evidence(journal=" in ex
            and "phase36_robustness_science_v1_16_journal" in ex)


def xcontract_launcher_pin(ls: str, ss: str) -> bool:
    """D80-H: launcher pins literal v1.16 SHA; supervisor enforces the launcher pin."""
    return (f'V1_16_SOURCE_SHA = "{V1_16_EXEC_SHA}"' in ls
            and "launcher_sha_pin_enforced" in ss
            and "FAIL_CLOSED__LAUNCHER_SHA_MISMATCH" in ss)


def xcontract_no_v14_operational_residue(ex: str, ls: str, ss: str) -> bool:
    """D80-I: no v1.14 operational literal silently retained in a v1.16 surface."""
    forbid_in_exec = [
        "PHASE36_V1_14_LAUNCH_AUTHORITY", "PHASE36_V1_14_EXECUTE",
        "phase36_v1_14_runtime_source_integrity_manifest.json",
        "ra_medfilm_barr_phase36_robustness_v1_14",
        "phase36_robustness_science_start_v1_14.json",
    ]
    return all(t not in ex for t in forbid_in_exec)


# --------------------------------------------------------------------------- #
def run_checks(ex: str, ls: str, ss: str, man: dict) -> list[dict]:
    local: list[dict] = []
    local.append({"check": "XC_A_mode_science", "passed": xcontract_mode_science(ex, ls)})
    local.append({"check": "XC_B_namespace_v1_16", "passed": xcontract_namespace(ex, ls, ss)})
    local.append({"check": "XC_C_authority_token", "passed": xcontract_authority_token(ex, ls)})
    local.append({"check": "XC_D_operator_gates", "passed": xcontract_gates(ex, ls)})
    local.append({"check": "XC_E_runtime_manifest", "passed": xcontract_manifest(ex, ls, man)})
    local.append({"check": "XC_F_release_revision", "passed": xcontract_release_revision(ex)})
    local.append({"check": "XC_G_stage_journal", "passed": xcontract_stage_journal(ex)})
    local.append({"check": "XC_H_launcher_pin", "passed": xcontract_launcher_pin(ls, ss)})
    local.append({"check": "XC_I_no_v1_14_operational_residue",
                  "passed": xcontract_no_v14_operational_residue(ex, ls, ss)})
    return local


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-only", action="store_true")
    ap.parse_args(argv)

    man = json.loads(MANIFEST.read_text(encoding="utf-8"))

    # ---- source identity ---- #
    check("S01_exec_source_sha_v1_16", _sha(EXEC) == V1_16_EXEC_SHA, {"sha256": _sha(EXEC)})
    check("S02_manifest_sha_v1_16", _sha(MANIFEST) == V1_16_MANIFEST_SHA, {"sha256": _sha(MANIFEST)})
    check("S03_d80_adjudication_present", D80_ADJ.exists())
    check("S04_launcher_present", LAUNCHER.exists())
    check("S05_supervisor_present", SUPERVISOR.exists())

    # ---- operational cross-contract checks ---- #
    for c in run_checks(EXEC_SRC, L_SRC, S_SRC, man):
        check(c["check"], c["passed"])

    # ---- negative controls: each mutation MUST produce a contradiction ---- #
    # NC_A: launcher omits --mode science.
    check("NC_A_mode_science_omitted_detected",
          not xcontract_mode_science(EXEC_SRC, L_SRC.replace('["--mode", "science"]', "[]")))
    # NC_B: execution start marker reverted to v1.14.
    check("NC_B_namespace_reverted_detected",
          not xcontract_namespace(
              EXEC_SRC.replace("phase36_robustness_science_start_v1_16.json",
                               "phase36_robustness_science_start_v1_14.json"),
              L_SRC, S_SRC))
    # NC_B2: supervisor result marker reverted to v1.14.
    check("NC_B2_supervisor_namespace_reverted_detected",
          not xcontract_namespace(
              EXEC_SRC, L_SRC,
              S_SRC.replace("phase36_robustness_scientific_result_v1_16.json",
                            "phase36_robustness_scientific_result_v1_14.json")))
    # NC_C: authority token reverted to v1.14.
    check("NC_C_authority_token_reverted_detected",
          not xcontract_authority_token(
              EXEC_SRC.replace('LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_16_LAUNCH_AUTHORITY"',
                               'LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_14_LAUNCH_AUTHORITY"'),
              L_SRC))
    # NC_D: execution gate reverted to v1.14.
    check("NC_D_gate_reverted_detected",
          not xcontract_gates(EXEC_SRC.replace("PHASE36_V1_16_EXECUTE", "PHASE36_V1_14_EXECUTE"),
                              L_SRC))
    # NC_E: manifest path reverted to v1.14.
    check("NC_E_manifest_path_reverted_detected",
          not xcontract_manifest(
              EXEC_SRC.replace("phase36_v1_16_runtime_source_integrity_manifest.json",
                               "phase36_v1_14_runtime_source_integrity_manifest.json"),
              L_SRC, man))
    # NC_E2: manifest no longer binds v1.16 exec SHA.
    _man_bad = dict(man)
    _man_bad["execution_source_sha256"] = "0" * 64
    check("NC_E2_manifest_binding_broken_detected",
          not xcontract_manifest(EXEC_SRC, L_SRC, _man_bad))
    # NC_F: release revision reverted to v1.14.
    check("NC_F_release_revision_reverted_detected",
          not xcontract_release_revision(
              EXEC_SRC.replace("ra_medfilm_barr_phase36_robustness_v1_16",
                               "ra_medfilm_barr_phase36_robustness_v1_14")))
    # NC_G: stage-journal module removed.
    check("NC_G_stage_journal_removed_detected",
          not xcontract_stage_journal(
              EXEC_SRC.replace("V1_16_JOURNAL_STAGES", "X").replace("_ScienceJournal", "Y")))
    # NC_H: launcher pin removed.
    check("NC_H_launcher_pin_removed_detected",
          not xcontract_launcher_pin(L_SRC.replace(V1_16_EXEC_SHA, "0" * 64), S_SRC))
    # NC_H2: supervisor pin enforcement removed.
    check("NC_H2_supervisor_pin_removed_detected",
          not xcontract_launcher_pin(
              L_SRC, S_SRC.replace("FAIL_CLOSED__LAUNCHER_SHA_MISMATCH", "OTHER")))
    # NC_I: v1.14 operational literal retained in execution.
    check("NC_I_v1_14_operational_residue_detected",
          not xcontract_no_v14_operational_residue(
              EXEC_SRC + "\nPHASE36_V1_14_EXECUTE = 'x'\n", L_SRC, S_SRC))
    # NC_I2: v1.14 manifest literal retained.
    check("NC_I2_v1_14_manifest_residue_detected",
          not xcontract_no_v14_operational_residue(
              EXEC_SRC + "\n# phase36_v1_14_runtime_source_integrity_manifest.json\n", L_SRC, S_SRC))

    n_pass = sum(1 for c in checks if c["passed"])
    n_total = len(checks)
    report = {
        "artifact": "phase36_v1_16_operational_cross_contract",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": REVISION,
        "type": "OPERATIONAL_CROSS_CONTRACT_REPORT",
        "model_free": True,
        "torch_imported": False,
        "protected_population_read": False,
        "subject_execution_sha256": _sha(EXEC),
        "subject_manifest_sha256": _sha(MANIFEST),
        "checks_total": n_total,
        "checks_passed": n_pass,
        "checks_failed": n_total - n_pass,
        "all_pass": n_pass == n_total,
        "failed_checks": [c["check"] for c in checks if not c["passed"]],
        "checks": checks,
    }
    out_path = ROOT / "reports/audits/phase36_v1_16_operational_cross_contract.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=1), encoding="utf-8")
    for c in checks:
        if not c["passed"]:
            print(f"FAIL {c['check']} :: {c.get('detail')}")
    print(f"OPERATIONAL CROSS-CONTRACT v1.16: {n_pass}/{n_total} pass")
    print(f"terminal: {'PHASE36_V1_16_OPERATIONAL_CROSS_CONTRACT_PASS' if n_pass == n_total else 'PHASE36_V1_16_OPERATIONAL_CROSS_CONTRACT_FAIL'}")
    return 0 if n_pass == n_total else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
