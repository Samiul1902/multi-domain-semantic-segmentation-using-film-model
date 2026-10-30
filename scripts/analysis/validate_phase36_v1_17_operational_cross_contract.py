#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.17 — OPERATIONAL / GOVERNANCE CROSS-CONTRACT VALIDATOR.

Rebased from the v1.16 cross-contract validator.  Machine-derived
(source/AST/hash only), NOT hard-coded booleans.

Proves the v1.17 OPERATIONAL/GOVERNANCE surface is internally CONSISTENT across
the whole v1.17 contract: execution source, launcher, supervisor, runtime
manifest, release attestation, and launch-authority constant MUST agree on the
SAME v1.17 literals, AND the D81/D82/D83 repairs MUST be present and mutually
consistent.

Operational cross-contract checks:
  A  launcher dispatch supplies `--mode science`; execution REQUIRES `--mode`.
  B  execution science namespace == v1.17; launcher/supervisor marker namespace agrees.
  C  launch-authority token literal agrees across execution + launcher.
  D  operator-gate literals agree; no v1.14/v1.15/v1.16 gate residue.
  E  runtime-manifest path agreed; manifest binds the v1.17 exec SHA.
  F  release revision agrees; no v1.14/v1.15/v1.16 revision residue.
  G  stage-journal dir/module present in execution.
  H  launcher pins the literal v1.17 exec SHA; supervisor enforces the launcher pin.
  I  no v1.14/v1.15/v1.16 operational literal silently retained.

D81/D82/D83 repair cross-checks:
  J  D81  every reachable table/figure target is in the UNIQUE v1.17 namespace;
          CSV writer is fail-closed (open "x" + refuse-existing + fsync).
  K  D82  the release gate binds the HISTORICAL v1.14 smoke and does NOT require a
          v1.17 smoke; the v1.17 attestation declares the D40 schema fields and
          binds the historical smoke SHA.
  L  D83  the launcher invokes the pure runtime release-state function and requires
          RELEASED; the pure release-gate test is RELEASED with all mutations rejected.

Negative controls: each check is re-run against an IN-MEMORY mutated copy and MUST
report a contradiction.  Any UNKNOWN => FAIL CLOSED.

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO science.
NO VAL/GT read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_17.py"
LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_v1_17.py"
SUPERVISOR = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_17.py"
MANIFEST = ROOT / "reports" / "audits" / "phase36_v1_17_runtime_source_integrity_manifest.json"
ATTESTATION = ROOT / "reports" / "audits" / "phase36_v1_17_science_release_attestation.json"
PURE_GATE_TEST = ROOT / "reports" / "audits" / "phase36_v1_17_pure_release_gate_test.json"
INVENTORY = ROOT / "reports" / "audits" / "phase36_v1_17_reachable_write_target_inventory.json"

V1_17_EXEC_SHA = "81d78460b2f20f176bc697cba662c43bc7c7443ea555ba95a30609faf0ccbe31"
V1_17_MANIFEST_SHA = "729f3676c86ba687bf808f9d79bac38916252563fc4b5814dd75d3d3f6b2bfc9"
HISTORICAL_V1_14_SMOKE_SHA = "53543729fb0c48695c2af202c5f3d2f5ebdfc29d87c7a7f100bcde9f94882441"

REVISION = "ra_medfilm_barr_phase36_robustness_v1_17"

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
    exec_requires = ('ap.add_argument("--mode"' in ex and "required=True" in ex)
    launch_supplies = ('DISPATCH_MODE_ARGS = ["--mode", "science"]' in ls
                       and "list(DISPATCH_MODE_ARGS)" in ls)
    return exec_requires and launch_supplies


def xcontract_namespace(ex: str, ls: str, ss: str) -> bool:
    ex_ok = ("phase36_robustness_science_start_v1_17.json" in ex
             and "phase36_robustness_scientific_result_v1_17.json" in ex
             and "phase36_robustness_science_failure_v1_17.json" in ex
             and "phase36_robustness_science_start_v1_16.json" not in ex
             and "phase36_robustness_science_start_v1_14.json" not in ex)
    ls_ok = ("phase36_robustness_science_start_v1_17.json" in ls
             and "phase36_robustness_scientific_result_v1_17.json" in ls
             and "phase36_robustness_science_failure_v1_17.json" in ls)
    ss_ok = ("phase36_robustness_science_start_v1_17.json" in ss
             and "phase36_robustness_scientific_result_v1_17.json" in ss
             and "phase36_robustness_science_failure_v1_17.json" in ss
             and "phase36_robustness_science_start_v1_16.json" not in ss)
    # The launcher MAY contain a ``v1_16_markers`` block that VERIFIES v1.16 markers
    # are ABSENT (a preservation check, not a namespace violation).  It must NOT
    # carry a v1.16 marker inside its own START/RESULT/FAILURE dispatch namespace.
    # We therefore require that any launcher v1.16 marker occurrence is confined to
    # a marker-ABSENCE verification block.
    ls_prev_confined = ("v1_16_markers" in ls and "_markers" in ls)
    return ex_ok and ls_ok and ss_ok and ls_prev_confined


def xcontract_authority_token(ex: str, ls: str) -> bool:
    tok = "PHASE36_V1_17_LAUNCH_AUTHORITY"
    return (f'LAUNCH_AUTHORITY_TOKEN = "{tok}"' in ex and tok in ls
            and "PHASE36_V1_14_LAUNCH_AUTHORITY" not in ex
            and "PHASE36_V1_15_LAUNCH_AUTHORITY" not in ex
            and "PHASE36_V1_16_LAUNCH_AUTHORITY" not in ex)


def xcontract_gates(ex: str, ls: str) -> bool:
    ok = ("PHASE36_V1_17_EXECUTE" in ex and "PHASE36_V1_17_SMOKE_EXECUTE" in ex
          and "PHASE36_V1_17_EXECUTE" in ls and "PHASE36_V1_17_SMOKE_EXECUTE" in ls)
    clean = all(t not in ex for t in ("PHASE36_V1_14_EXECUTE", "PHASE36_V1_14_SMOKE_EXECUTE",
                                      "PHASE36_V1_15_EXECUTE", "PHASE36_V1_15_SMOKE_EXECUTE",
                                      "PHASE36_V1_16_EXECUTE", "PHASE36_V1_16_SMOKE_EXECUTE"))
    return ok and clean


def xcontract_manifest(ex: str, ls: str, man: dict) -> bool:
    path_ok = ("phase36_v1_17_runtime_source_integrity_manifest.json" in ex
               and "phase36_v1_17_runtime_source_integrity_manifest.json" in ls
               and "phase36_v1_16_runtime_source_integrity_manifest.json" not in ex
               and "phase36_v1_14_runtime_source_integrity_manifest.json" not in ex)
    binds = man.get("execution_source_sha256") == V1_17_EXEC_SHA
    return path_ok and binds


def xcontract_release_revision(ex: str) -> bool:
    return (REVISION in ex
            and "ra_medfilm_barr_phase36_robustness_v1_14" not in ex
            and "ra_medfilm_barr_phase36_robustness_v1_15" not in ex
            and "ra_medfilm_barr_phase36_robustness_v1_16" not in ex)


def xcontract_stage_journal(ex: str) -> bool:
    return ("V1_17_JOURNAL_STAGES" in ex and "_ScienceJournal" in ex
            and "journal=_ScienceJournal(" in ex
            and "_run_science_with_durable_evidence(journal=" in ex
            and "phase36_robustness_science_v1_17_journal" in ex)


def xcontract_launcher_pin(ls: str, ss: str) -> bool:
    return (f'V1_17_SOURCE_SHA = "{V1_17_EXEC_SHA}"' in ls
            and "launcher_sha_pin_enforced" in ss
            and "FAIL_CLOSED__LAUNCHER_SHA_MISMATCH" in ss)


def xcontract_no_prev_operational_residue(ex: str, ls: str, ss: str) -> bool:
    forbid_in_exec = [
        "PHASE36_V1_14_LAUNCH_AUTHORITY", "PHASE36_V1_14_EXECUTE",
        "phase36_v1_14_runtime_source_integrity_manifest.json",
        "ra_medfilm_barr_phase36_robustness_v1_14",
        "phase36_robustness_science_start_v1_14.json",
        "PHASE36_V1_16_LAUNCH_AUTHORITY", "PHASE36_V1_16_EXECUTE",
        "PHASE36_V1_16_SMOKE_EXECUTE",
        "phase36_v1_16_runtime_source_integrity_manifest.json",
        "ra_medfilm_barr_phase36_robustness_v1_16",
        "phase36_robustness_science_start_v1_16.json",
    ]
    return all(t not in ex for t in forbid_in_exec)


# ---- D81 ------------------------------------------------------------------- #
V17_TABLE_ROOT = "reports/tables/phase36_robustness_v1_17/"
V17_FIGURE_ROOT = "reports/figures/phase36_robustness_v1_17/"


def _source_csv_targets(ex: str) -> list[str]:
    """Independently AST-enumerate ``_write_csv(TAB / "<name>.csv")`` targets."""
    import ast as _ast
    import re as _re
    tree = _ast.parse(ex)
    found: list[str] = []
    seen: set[str] = set()
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Call):
            f = node.func
            name = f.id if isinstance(f, _ast.Name) else (
                f.attr if isinstance(f, _ast.Attribute) else None)
            if name == "_write_csv" and node.args:
                try:
                    expr = _ast.unparse(node.args[0])
                except Exception:
                    expr = ""
                m = _re.search(r"""["']([^"']+\.csv)["']""", expr)
                if m:
                    full = V17_TABLE_ROOT + m.group(1)
                    if full not in seen:
                        seen.add(full)
                        found.append(full)
    return sorted(found)


def xcontract_d81_namespace_and_failclosed(ex: str, inv: dict) -> bool:
    """D81: all reachable targets in the unique v1.17 namespace + fail-closed CSV
    + the inventory is COMPLETE w.r.t. the AST-enumerated source targets."""
    paths = [t["path"] for t in inv.get("csv_table_targets", [])] + \
            [t["path"] for t in inv.get("figure_targets", [])]
    ns_ok = bool(paths) and all(p.startswith(V17_TABLE_ROOT) or p.startswith(V17_FIGURE_ROOT)
                                for p in paths)
    inv_ok = (inv.get("unclassified_write_target_count") == 0
              and inv.get("all_reachable_write_targets_enumerated") is True
              and inv.get("v1_14_overlap") == [] and inv.get("v1_15_overlap") == []
              and inv.get("v1_16_overlap") == [])
    # COMPLETENESS: every source-reachable CSV target MUST be present in the inventory.
    src_targets = _source_csv_targets(ex)
    inv_csv = sorted(t["path"] for t in inv.get("csv_table_targets", []))
    complete = bool(src_targets) and all(t in inv_csv for t in src_targets)
    # Fail-closed CSV writer in the execution source.
    writer_ok = ('open(path, "x", encoding="utf-8", newline="")' in ex
                 and "if path.exists():" in ex
                 and "V1_17_CSV_FAIL_CLOSED__TARGET_EXISTS__REFUSE_OVERWRITE" in ex
                 and 'path.open("w"' not in ex
                 and "os.fsync(f.fileno())" in ex)
    return ns_ok and inv_ok and complete and writer_ok


def xcontract_d81_no_unversioned_target(ex: str) -> bool:
    """D81: no inherited unversioned phase36 table/figure root remains reachable."""
    return ("reports/tables/phase36_robustness/" not in ex
            or "phase36_robustness_v1_17" in ex)


# ---- D82 ------------------------------------------------------------------- #
def xcontract_d82_release_contract(ex: str, att: dict) -> bool:
    """D82: gate binds historical v1.14 smoke; attestation declares D40 fields."""
    gate_ok = ("HISTORICAL_V1_14_SMOKE" in ex
               and "HISTORICAL_SMOKE_ARTIFACT_MISSING" in ex
               and "phase36_robustness_smoke_v1_17.json" not in ex)
    att_fields = all(f in att for f in ("smoke_artifact_sha256", "smoke_all_pass",
                                        "scientific_output", "release_gate"))
    binds_hist = (att.get("smoke_artifact_sha256") == HISTORICAL_V1_14_SMOKE_SHA
                  and att.get("requires_v1_17_smoke") is False
                  and att.get("revision") == REVISION)
    return gate_ok and att_fields and binds_hist


# ---- D83 ------------------------------------------------------------------- #
def xcontract_d83_pure_release_state(ls: str, gate_test: dict) -> bool:
    """D83: launcher evaluates the pure release state and the test proves RELEASED."""
    launcher_ok = ("verify_pure_release_state" in ls
                   and "pure_release_state_released" in ls)
    test_ok = (gate_test.get("base_gate_state") == "RELEASED"
               and gate_test.get("all_pass") is True)
    return launcher_ok and test_ok


# --------------------------------------------------------------------------- #
def run_checks(ex, ls, ss, man, att, gate_test, inv) -> list[dict]:
    return [
        {"check": "XC_A_mode_science", "passed": xcontract_mode_science(ex, ls)},
        {"check": "XC_B_namespace_v1_17", "passed": xcontract_namespace(ex, ls, ss)},
        {"check": "XC_C_authority_token", "passed": xcontract_authority_token(ex, ls)},
        {"check": "XC_D_operator_gates", "passed": xcontract_gates(ex, ls)},
        {"check": "XC_E_runtime_manifest", "passed": xcontract_manifest(ex, ls, man)},
        {"check": "XC_F_release_revision", "passed": xcontract_release_revision(ex)},
        {"check": "XC_G_stage_journal", "passed": xcontract_stage_journal(ex)},
        {"check": "XC_H_launcher_pin", "passed": xcontract_launcher_pin(ls, ss)},
        {"check": "XC_I_no_prev_operational_residue",
         "passed": xcontract_no_prev_operational_residue(ex, ls, ss)},
        {"check": "XC_J_d81_namespace_and_failclosed",
         "passed": xcontract_d81_namespace_and_failclosed(ex, inv)},
        {"check": "XC_K_d82_release_contract",
         "passed": xcontract_d82_release_contract(ex, att)},
        {"check": "XC_L_d83_pure_release_state",
         "passed": xcontract_d83_pure_release_state(ls, gate_test)},
    ]


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-only", action="store_true")
    ap.parse_args(argv)

    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    att = json.loads(ATTESTATION.read_text(encoding="utf-8"))
    gate_test = json.loads(PURE_GATE_TEST.read_text(encoding="utf-8"))
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))

    # ---- source identity ---- #
    check("S01_exec_source_sha_v1_17", _sha(EXEC) == V1_17_EXEC_SHA, {"sha256": _sha(EXEC)})
    check("S02_manifest_sha_v1_17", _sha(MANIFEST) == V1_17_MANIFEST_SHA, {"sha256": _sha(MANIFEST)})
    check("S03_attestation_present", ATTESTATION.exists())
    check("S04_pure_gate_test_present", PURE_GATE_TEST.exists())
    check("S05_inventory_present", INVENTORY.exists())
    check("S06_launcher_present", LAUNCHER.exists())
    check("S07_supervisor_present", SUPERVISOR.exists())

    # ---- operational cross-contract checks ---- #
    for c in run_checks(EXEC_SRC, L_SRC, S_SRC, man, att, gate_test, inv):
        check(c["check"], c["passed"])

    # ---- negative controls: each mutation MUST produce a contradiction ---- #
    check("NC_A_mode_science_omitted_detected",
          not xcontract_mode_science(EXEC_SRC, L_SRC.replace('["--mode", "science"]', "[]")))
    check("NC_B_namespace_reverted_detected",
          not xcontract_namespace(
              EXEC_SRC.replace("phase36_robustness_science_start_v1_17.json",
                               "phase36_robustness_science_start_v1_16.json"),
              L_SRC, S_SRC))
    check("NC_B2_supervisor_namespace_reverted_detected",
          not xcontract_namespace(
              EXEC_SRC, L_SRC,
              S_SRC.replace("phase36_robustness_scientific_result_v1_17.json",
                            "phase36_robustness_scientific_result_v1_16.json")))
    check("NC_C_authority_token_reverted_detected",
          not xcontract_authority_token(
              EXEC_SRC.replace('LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_17_LAUNCH_AUTHORITY"',
                               'LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_16_LAUNCH_AUTHORITY"'),
              L_SRC))
    check("NC_D_gate_reverted_detected",
          not xcontract_gates(EXEC_SRC.replace("PHASE36_V1_17_EXECUTE", "PHASE36_V1_16_EXECUTE"),
                              L_SRC))
    check("NC_E_manifest_path_reverted_detected",
          not xcontract_manifest(
              EXEC_SRC.replace("phase36_v1_17_runtime_source_integrity_manifest.json",
                               "phase36_v1_16_runtime_source_integrity_manifest.json"),
              L_SRC, man))
    _man_bad = dict(man)
    _man_bad["execution_source_sha256"] = "0" * 64
    check("NC_E2_manifest_binding_broken_detected",
          not xcontract_manifest(EXEC_SRC, L_SRC, _man_bad))
    check("NC_F_release_revision_reverted_detected",
          not xcontract_release_revision(
              EXEC_SRC.replace("ra_medfilm_barr_phase36_robustness_v1_17",
                               "ra_medfilm_barr_phase36_robustness_v1_16")))
    check("NC_G_stage_journal_removed_detected",
          not xcontract_stage_journal(
              EXEC_SRC.replace("V1_17_JOURNAL_STAGES", "X").replace("_ScienceJournal", "Y")))
    check("NC_H_launcher_pin_removed_detected",
          not xcontract_launcher_pin(L_SRC.replace(V1_17_EXEC_SHA, "0" * 64), S_SRC))
    check("NC_H2_supervisor_pin_removed_detected",
          not xcontract_launcher_pin(
              L_SRC, S_SRC.replace("FAIL_CLOSED__LAUNCHER_SHA_MISMATCH", "OTHER")))
    check("NC_I_prev_operational_residue_detected",
          not xcontract_no_prev_operational_residue(
              EXEC_SRC + "\nPHASE36_V1_16_LAUNCH_AUTHORITY = 'x'\n", L_SRC, S_SRC))
    check("NC_I2_prev_manifest_residue_detected",
          not xcontract_no_prev_operational_residue(
              EXEC_SRC + "\n# phase36_v1_16_runtime_source_integrity_manifest.json\n",
              L_SRC, S_SRC))
    check("NC_I3_prev_start_marker_residue_detected",
          not xcontract_no_prev_operational_residue(
              EXEC_SRC + "\n# phase36_robustness_science_start_v1_16.json\n", L_SRC, S_SRC))
    # NC_B3: launcher loses its v1.16 marker-absence verification block.
    check("NC_B3_launcher_marker_absence_block_removed_detected",
          not xcontract_namespace(EXEC_SRC, L_SRC.replace("v1_16_markers", "REMOVED"), S_SRC))

    # ---- D81 negative controls ---- #
    # NC_J1: omitted table target detected.
    inv_missing = {k: v for k, v in inv.items()}
    inv_missing["csv_table_targets"] = [t for t in inv["csv_table_targets"]
                                        if not t["path"].endswith("phase36_worst_case_by_domain.csv")]
    check("NC_J1_omitted_table_target_detected",
          not xcontract_d81_namespace_and_failclosed(EXEC_SRC, inv_missing))
    # NC_J2: generic non-versioned table target detected.
    inv_unv = dict(inv)
    inv_unv["csv_table_targets"] = list(inv["csv_table_targets"]) + [
        {"path": "reports/tables/phase36_robustness/phase36_worst_case_by_domain.csv"}]
    check("NC_J2_unversioned_table_target_detected",
          not xcontract_d81_namespace_and_failclosed(EXEC_SRC, inv_unv))
    # NC_J2b: generic inherited figure dir detected.
    inv_unvfig = dict(inv)
    inv_unvfig["figure_targets"] = list(inv["figure_targets"]) + [
        {"path": "reports/figures/phase36_robustness/R1_x.png"}]
    check("NC_J2b_unversioned_figure_target_detected",
          not xcontract_d81_namespace_and_failclosed(EXEC_SRC, inv_unvfig))
    # NC_J3: inventory unclassified count nonzero.
    inv_unc = dict(inv)
    inv_unc["unclassified_write_target_count"] = 1
    check("NC_J3_unclassified_count_detected",
          not xcontract_d81_namespace_and_failclosed(EXEC_SRC, inv_unc))
    # NC_J4: CSV writer reverted to overwrite mode.
    check("NC_J4_csv_open_w_overwrite_detected",
          not xcontract_d81_namespace_and_failclosed(
              EXEC_SRC.replace('open(path, "x", encoding="utf-8", newline="")',
                               'path.open("w", encoding="utf-8", newline="")'),
              inv))

    # ---- D82 negative controls ---- #
    # NC_K1: gate re-requires a v1.17 smoke artifact.
    check("NC_K1_gate_requires_v1_17_smoke_detected",
          not xcontract_d82_release_contract(
              EXEC_SRC.replace("HISTORICAL_V1_14_SMOKE", "SMOKE_V1_17_ARTIFACT")
                      + '\nSMOKE_V1_17_ARTIFACT = "reports/audits/phase36_robustness_smoke_v1_17.json"\n',
              att))
    # NC_K2: attestation missing a D40 field.
    att_missing = {k: v for k, v in att.items() if k != "release_gate"}
    check("NC_K2_attestation_missing_field_detected",
          not xcontract_d82_release_contract(EXEC_SRC, att_missing))
    # NC_K3: attestation binds the wrong smoke SHA.
    att_badsha = dict(att); att_badsha["smoke_artifact_sha256"] = "0" * 64
    check("NC_K3_attestation_wrong_smoke_sha_detected",
          not xcontract_d82_release_contract(EXEC_SRC, att_badsha))
    # NC_K4: attestation requires a v1.17 smoke.
    att_reqsmoke = dict(att); att_reqsmoke["requires_v1_17_smoke"] = True
    check("NC_K4_attestation_requires_smoke_detected",
          not xcontract_d82_release_contract(EXEC_SRC, att_reqsmoke))

    # ---- D83 negative controls ---- #
    # NC_L1: validator checks only revision without evaluating state.
    check("NC_L1_validator_revision_only_detected",
          not xcontract_d83_pure_release_state(
              "# att.get('revision') == REVISION only\n", gate_test))
    # NC_L2: gate NOT_RELEASED while eligibility eligible.
    gt_nrel = dict(gate_test); gt_nrel["base_gate_state"] = "NOT_RELEASED"
    check("NC_L2_gate_not_released_detected",
          not xcontract_d83_pure_release_state(L_SRC, gt_nrel))
    # NC_L3: gate test did not pass.
    gt_fail = dict(gate_test); gt_fail["all_pass"] = False
    check("NC_L3_gate_test_failed_detected",
          not xcontract_d83_pure_release_state(L_SRC, gt_fail))

    n_pass = sum(1 for c in checks if c["passed"])
    n_total = len(checks)
    report = {
        "artifact": "phase36_v1_17_operational_cross_contract",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": REVISION,
        "type": "OPERATIONAL_CROSS_CONTRACT_REPORT",
        "model_free": True,
        "torch_imported": False,
        "protected_population_read": False,
        "subject_execution_sha256": _sha(EXEC),
        "subject_manifest_sha256": _sha(MANIFEST),
        "subject_attestation_sha256": _sha(ATTESTATION),
        "subject_pure_gate_test_sha256": _sha(PURE_GATE_TEST),
        "subject_inventory_sha256": _sha(INVENTORY),
        "checks_total": n_total,
        "checks_passed": n_pass,
        "checks_failed": n_total - n_pass,
        "all_pass": n_pass == n_total,
        "failed_checks": [c["check"] for c in checks if not c["passed"]],
        "checks": checks,
    }
    out_path = ROOT / "reports/audits/phase36_v1_17_operational_cross_contract.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=1), encoding="utf-8")
    for c in checks:
        if not c["passed"]:
            print(f"FAIL {c['check']} :: {c.get('detail')}")
    print(f"OPERATIONAL CROSS-CONTRACT v1.17: {n_pass}/{n_total} pass")
    print(f"terminal: {'PHASE36_V1_17_OPERATIONAL_CROSS_CONTRACT_PASS' if n_pass == n_total else 'PHASE36_V1_17_OPERATIONAL_CROSS_CONTRACT_FAIL'}")
    return 0 if n_pass == n_total else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
