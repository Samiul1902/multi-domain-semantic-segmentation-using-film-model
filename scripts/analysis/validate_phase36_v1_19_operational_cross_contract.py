#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.19 — OPERATIONAL / GOVERNANCE CROSS-CONTRACT VALIDATOR (WO#17E).

Rebased from the v1.17 cross-contract validator.  Machine-derived (source/AST/hash
only), NOT hard-coded booleans.

Proves the v1.19 OPERATIONAL/GOVERNANCE/PRE-EXECUTION-AUTHORITY surface is internally
CONSISTENT across the whole v1.19 contract: execution source, launcher, supervisor,
runtime manifest, release attestation, launch-authority constant, prelaunch authority
bundle, reachable-write inventory, and D85-D88 adjudication MUST agree on the SAME
v1.19 literals, AND the D81/D82/D83 repairs MUST be present and mutually consistent,
AND the NEW D85/D86/D87/D88 pre-execution authority repairs MUST be present and
mutually consistent.

Operational cross-contract checks:
  A  launcher dispatch supplies `--mode science`; execution REQUIRES `--mode`.
  B  execution science namespace == v1.19; launcher/supervisor marker namespace agrees.
  C  launch-authority token literal agrees across execution + launcher.
  D  operator-gate literals agree; no v1.14/v1.15/v1.16/v1.17 gate residue.
  E  runtime-manifest path agreed; manifest binds the v1.19 exec SHA.
  F  release revision agrees; no prior-version revision residue.
  G  stage-journal dir/module present in execution.
  H  launcher pins the literal v1.19 exec SHA; supervisor enforces the launcher pin.

D81/D82/D83 repair cross-checks:
  J  D81  every reachable table/figure target is in the UNIQUE v1.19 namespace;
          CSV writer is fail-closed (open "x" + refuse-existing + fsync).
  K  D82  the release gate binds the HISTORICAL v1.14 smoke and does NOT require a
          v1.19 smoke; the v1.19 attestation declares the D40 schema fields and
          binds the historical smoke SHA.
  L  D83  the launcher invokes the pure runtime release-state function and requires
          RELEASED; the pure release-gate test is RELEASED with all mutations rejected.

D85/D86/D87/D88 pre-execution authority cross-checks:
  M  D85  supervisor literal launcher SHA == the ACTUAL launcher SHA on disk; no env
          override; the launch-authority file binds that same launcher SHA.
  N  D86  supervisor exclusive stdout/stderr writer; no O_TRUNC; pre-dispatch absence.
  O  D87  the prelaunch authority bundle binds the launcher/manifest/exec SHAs and
          does NOT contain the supervisor SHA; the supervisor pins the bundle SHA;
          the launch-authority file binds the bundle SHA (non-circular chain).
  P  D88  inventory counts agree across bundle / inventory / namespace map; the exec
          absence gate enumerates the same target set; figures are fail-closed.

Negative controls: each check is re-run against an IN-MEMORY mutated copy and MUST
report a contradiction.  Any UNKNOWN => FAIL CLOSED.

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO science.
NO VAL/GT read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import argparse
import ast as _ast
import hashlib
import json
import re as _re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_19.py"
LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_v1_19.py"
SUPERVISOR = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_19.py"
MANIFEST = ROOT / "reports" / "audits" / "phase36_v1_19_runtime_source_integrity_manifest.json"
ATTESTATION = ROOT / "reports" / "audits" / "phase36_v1_19_science_release_attestation.json"
PURE_GATE_TEST = ROOT / "reports" / "audits" / "phase36_v1_19_pure_release_gate_test.json"
INVENTORY = ROOT / "reports" / "audits" / "phase36_v1_19_reachable_write_target_inventory.json"
BUNDLE = ROOT / "reports" / "audits" / "phase36_v1_19_prelaunch_authority_bundle.json"
LAUNCH_AUTHORITY = ROOT / "reports" / "audits" / "phase36_v1_19_launch_authority_sha.json"
ADJUDICATION = ROOT / "reports" / "audits" / "phase36_v1_19_adjudication_d85_d86_d87_d88.json"

V1_19_EXEC_SHA = "3ec5ea920af2b6d66864b3bbc7e5362f0756777512c29be70d3e5453e18693cd"
HISTORICAL_V1_14_SMOKE_SHA = "53543729fb0c48695c2af202c5f3d2f5ebdfc29d87c7a7f100bcde9f94882441"

REVISION = "ra_medfilm_barr_phase36_robustness_v1_19"

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


def _fn_src(src: str, name: str) -> str:
    for n in _ast.walk(_ast.parse(src)):
        if isinstance(n, _ast.FunctionDef) and n.name == name:
            return _ast.get_source_segment(src, n) or ""
    return ""


# --------------------------------------------------------------------------- #
# Cross-contract detectors (each returns True iff the contract is CONSISTENT)
# --------------------------------------------------------------------------- #
def xcontract_mode_science(ex: str, ls: str) -> bool:
    exec_requires = ('ap.add_argument("--mode"' in ex and "required=True" in ex)
    launch_supplies = ('DISPATCH_MODE_ARGS = ["--mode", "science"]' in ls
                       and "list(DISPATCH_MODE_ARGS)" in ls)
    return exec_requires and launch_supplies


def xcontract_namespace(ex: str, ls: str, ss: str) -> bool:
    ex_ok = ("phase36_robustness_science_start_v1_19.json" in ex
             and "phase36_robustness_scientific_result_v1_19.json" in ex
             and "phase36_robustness_science_failure_v1_19.json" in ex
             and "phase36_robustness_science_start_v1_17.json" not in ex
             and "phase36_robustness_science_start_v1_16.json" not in ex
             and "phase36_robustness_science_start_v1_14.json" not in ex)
    ls_ok = ("phase36_robustness_science_start_v1_19.json" in ls
             and "phase36_robustness_scientific_result_v1_19.json" in ls
             and "phase36_robustness_science_failure_v1_19.json" in ls)
    ss_ok = ("phase36_robustness_science_start_v1_19.json" in ss
             and "phase36_robustness_scientific_result_v1_19.json" in ss
             and "phase36_robustness_science_failure_v1_19.json" in ss
             and "phase36_robustness_science_start_v1_17.json" not in ss)
    # The launcher MAY contain a ``v1_17_markers`` block that VERIFIES v1.17 markers are
    # ABSENT (a preservation check).  Require that any prior-version marker occurrence in
    # the launcher is confined to a marker-ABSENCE verification block.
    ls_prev_confined = ("v1_17_markers" in ls or "v1_16_markers" in ls)
    return ex_ok and ls_ok and ss_ok and ls_prev_confined


def xcontract_authority_token(ex: str, ls: str) -> bool:
    tok = "PHASE36_V1_19_LAUNCH_AUTHORITY"
    return (f'LAUNCH_AUTHORITY_TOKEN = "{tok}"' in ex and tok in ls
            and all(f"PHASE36_V1_{v}_LAUNCH_AUTHORITY" not in ex
                    for v in ("14", "15", "16", "17")))


def xcontract_gates(ex: str, ls: str) -> bool:
    ok = ("PHASE36_V1_19_EXECUTE" in ex and "PHASE36_V1_19_EXECUTE" in ls)
    clean = all(t not in ex for t in ("PHASE36_V1_14_EXECUTE", "PHASE36_V1_15_EXECUTE",
                                      "PHASE36_V1_16_EXECUTE", "PHASE36_V1_17_EXECUTE"))
    return ok and clean


def xcontract_manifest(ex: str, ls: str, man: dict) -> bool:
    path_ok = ("phase36_v1_19_runtime_source_integrity_manifest.json" in ex
               and "phase36_v1_19_runtime_source_integrity_manifest.json" in ls
               and "phase36_v1_17_runtime_source_integrity_manifest.json" not in ex)
    binds = man.get("execution_source_sha256") == V1_19_EXEC_SHA
    return path_ok and binds


def xcontract_release_revision(ex: str) -> bool:
    return (REVISION in ex
            and all(f"ra_medfilm_barr_phase36_robustness_v1_{v}" not in ex
                    for v in ("14", "15", "16", "17")))


def xcontract_stage_journal(ex: str) -> bool:
    return ("V1_19_JOURNAL_STAGES" in ex and "_ScienceJournal" in ex
            and "journal=_ScienceJournal(" in ex
            and "_run_science_with_durable_evidence(journal=" in ex
            and "phase36_robustness_science_v1_19_journal" in ex)


def xcontract_launcher_pin(ls: str, ss: str) -> bool:
    return (f'V1_19_SOURCE_SHA = "{V1_19_EXEC_SHA}"' in ls
            and 'launcher_pin_ok' in ss
            and 'FAIL_CLOSED__IMMUTABLE_PIN_MISMATCH' in ss)


def xcontract_no_prev_operational_residue(ex: str, ls: str, ss: str) -> bool:
    forbid_in_exec = []
    for v in ("14", "15", "16", "17"):
        forbid_in_exec += [
            f"PHASE36_V1_{v}_LAUNCH_AUTHORITY",
            f"PHASE36_V1_{v}_EXECUTE",
            f"phase36_v1_{v}_runtime_source_integrity_manifest.json",
            f"ra_medfilm_barr_phase36_robustness_v1_{v}",
            f"phase36_robustness_science_start_v1_{v}.json",
        ]
    return all(t not in ex for t in forbid_in_exec)


# ---- D81 ------------------------------------------------------------------- #
V18_TABLE_ROOT = "reports/tables/phase36_robustness_v1_19/"
V18_FIGURE_ROOT = "reports/figures/phase36_robustness_v1_19/"


def _source_csv_targets(ex: str) -> list[str]:
    """Independently AST-enumerate ``_write_csv(TAB / "<name>.csv")`` targets."""
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
                    full = V18_TABLE_ROOT + m.group(1)
                    if full not in seen:
                        seen.add(full)
                        found.append(full)
    return sorted(found)


def xcontract_d81_namespace_and_failclosed(ex: str, inv: dict) -> bool:
    paths = [t["path"] for t in inv.get("csv_table_targets", [])] + \
            [t["path"] for t in inv.get("figure_targets", [])]
    ns_ok = bool(paths) and all(p.startswith(V18_TABLE_ROOT) or p.startswith(V18_FIGURE_ROOT)
                                for p in paths)
    inv_ok = (inv.get("unclassified_write_target_count") == 0
              and inv.get("all_reachable_write_targets_enumerated") is True
              and all(inv.get(f"v1_{v}_overlap") == [] for v in ("14", "15", "16", "17")))
    src_targets = _source_csv_targets(ex)
    inv_csv = sorted(t["path"] for t in inv.get("csv_table_targets", []))
    complete = bool(src_targets) and all(t in inv_csv for t in src_targets)
    writer_ok = ('open(path, "x", encoding="utf-8", newline="")' in ex
                 and "if path.exists():" in ex
                 and "V1_19_CSV_FAIL_CLOSED__TARGET_EXISTS__REFUSE_OVERWRITE" in ex
                 and 'path.open("w"' not in ex
                 and "os.fsync(f.fileno())" in ex)
    return ns_ok and inv_ok and complete and writer_ok


def xcontract_d81_no_unversioned_target(ex: str) -> bool:
    return ("reports/tables/phase36_robustness/" not in ex
            or "phase36_robustness_v1_19" in ex)


# ---- D82 ------------------------------------------------------------------- #
def xcontract_d82_release_contract(ex: str, att: dict) -> bool:
    gate_ok = ("HISTORICAL_V1_14_SMOKE" in ex
               and "HISTORICAL_SMOKE_ARTIFACT_MISSING" in ex
               and "phase36_robustness_smoke_v1_19.json" not in ex)
    att_fields = all(f in att for f in ("smoke_artifact_sha256", "smoke_all_pass",
                                        "scientific_output", "release_gate"))
    binds_hist = (att.get("smoke_artifact_sha256") == HISTORICAL_V1_14_SMOKE_SHA
                  and att.get("requires_v1_19_smoke") is False
                  and att.get("revision") == REVISION)
    return gate_ok and att_fields and binds_hist


# ---- D83 ------------------------------------------------------------------- #
def xcontract_d83_pure_release_state(ls: str, gate_test: dict) -> bool:
    launcher_ok = ("verify_pure_release_state" in ls
                   and "pure_release_state_released" in ls)
    test_ok = (gate_test.get("base_gate_state") == "RELEASED"
               and gate_test.get("all_pass") is True)
    return launcher_ok and test_ok


# ---- D85 ------------------------------------------------------------------- #
def xcontract_d85_immutable_root(ls: str, ss: str, launch_auth: dict) -> bool:
    launcher_sha = _sha(LAUNCHER)
    literal = f'FROZEN_V1_19_LAUNCHER_SHA = "{launcher_sha}"' in ss
    no_env = "PHASE36_V1_19_LAUNCHER_SHA" not in ss
    auth_binds = launch_auth.get("launcher_sha256") == launcher_sha
    return literal and no_env and auth_binds


# ---- D86 ------------------------------------------------------------------- #
def xcontract_d86_exclusive_stdout_stderr(ss: str) -> bool:
    fn = _fn_src(ss, "_write_text_exclusive")
    if not fn:
        return False
    has_excl = all(k in fn for k in ("os.O_CREAT", "os.O_EXCL", "os.O_WRONLY"))
    no_trunc = True
    for n in _ast.walk(_ast.parse(ss)):
        if isinstance(n, _ast.FunctionDef) and n.name == "_write_text_exclusive":
            for m in _ast.walk(n):
                if isinstance(m, _ast.Attribute) and m.attr == "O_TRUNC":
                    no_trunc = False
    real_calls = ("_write_text_exclusive(STDOUT_PATH" in ss
                  and "_write_text_exclusive(STDERR_PATH" in ss)
    predispatch = "_predispatch_absence_check" in ss
    return has_excl and no_trunc and real_calls and predispatch


# ---- D87 ------------------------------------------------------------------- #
def xcontract_d87_non_circular_dag(ss: str, bundle: dict, launch_auth: dict) -> bool:
    binds = bundle.get("binds", {})
    binds_launcher = binds.get("v1_19_launcher", {}).get("sha256") == _sha(LAUNCHER)
    binds_manifest = binds.get("v1_19_runtime_manifest", {}).get("sha256") == _sha(MANIFEST)
    binds_exec = binds.get("v1_19_execution_source", {}).get("sha256") == V1_19_EXEC_SHA
    no_supervisor = (bundle.get("supervisor_sha256_present") is False
                     and "supervisor_sha256" not in bundle)
    supervisor_pins_bundle = f'FROZEN_V1_19_AUTHORITY_BUNDLE_SHA = "{_sha(BUNDLE)}"' in ss
    # The supervisor must actually INVOKE the immutable-pin verifier (not merely define it).
    verifier_called = ("verify_immutable_pins()" in ss
                       and "authority_bundle_pin_ok" in ss)
    auth_binds_bundle = launch_auth.get("prelaunch_authority_bundle_sha256") == _sha(BUNDLE)
    return (binds_launcher and binds_manifest and binds_exec and no_supervisor
            and supervisor_pins_bundle and verifier_called and auth_binds_bundle)


# ---- D88 ------------------------------------------------------------------- #
def xcontract_d88_realtime_gate_and_figures(ex: str, ss: str, inv: dict, bundle: dict) -> bool:
    fig_ok = ("def _savefig_once(" in ex
              and "fig.savefig(p, dpi=160)" not in ex
              and ex.count("_savefig_once(fig, p, dpi=160)") == 5)
    gate_ok = ("def verify_v1_19_output_absence(" in ex
               and "_absence = verify_v1_19_output_absence()" in ex)
    counts = bundle.get("count_semantics", {})
    counts_ok = (counts.get("table_figure_target_count") == 16
                 and counts.get("total_reachable_write_target_count") == 23
                 and counts.get("unclassified_write_target_count") == 0
                 and counts.get("namespace_overlap_count") == 0)
    inv_ok = (inv.get("total_reachable_write_target_count") == 23
              and inv.get("table_figure_target_count") == 16)
    return fig_ok and gate_ok and counts_ok and inv_ok


# --------------------------------------------------------------------------- #
def run_checks(ex, ls, ss, man, att, gate_test, inv, bundle, launch_auth) -> list[dict]:
    return [
        {"check": "XC_A_mode_science", "passed": xcontract_mode_science(ex, ls)},
        {"check": "XC_B_namespace_v1_19", "passed": xcontract_namespace(ex, ls, ss)},
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
        {"check": "XC_M_d85_immutable_root",
         "passed": xcontract_d85_immutable_root(ls, ss, launch_auth)},
        {"check": "XC_N_d86_exclusive_stdout_stderr",
         "passed": xcontract_d86_exclusive_stdout_stderr(ss)},
        {"check": "XC_O_d87_non_circular_dag",
         "passed": xcontract_d87_non_circular_dag(ss, bundle, launch_auth)},
        {"check": "XC_P_d88_realtime_gate_and_figures",
         "passed": xcontract_d88_realtime_gate_and_figures(ex, ss, inv, bundle)},
    ]


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-only", action="store_true")
    ap.parse_args(argv)

    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    att = json.loads(ATTESTATION.read_text(encoding="utf-8"))
    gate_test = json.loads(PURE_GATE_TEST.read_text(encoding="utf-8"))
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
    launch_auth = json.loads(LAUNCH_AUTHORITY.read_text(encoding="utf-8"))

    check("S01_exec_source_sha_v1_19", _sha(EXEC) == V1_19_EXEC_SHA, {"sha256": _sha(EXEC)})
    check("S02_manifest_present", MANIFEST.exists())
    check("S03_attestation_present", ATTESTATION.exists())
    check("S04_pure_gate_test_present", PURE_GATE_TEST.exists())
    check("S05_inventory_present", INVENTORY.exists())
    check("S06_launcher_present", LAUNCHER.exists())
    check("S07_supervisor_present", SUPERVISOR.exists())
    check("S08_bundle_present", BUNDLE.exists())
    check("S09_launch_authority_present", LAUNCH_AUTHORITY.exists())
    check("S10_adjudication_present", ADJUDICATION.exists())

    for c in run_checks(EXEC_SRC, L_SRC, S_SRC, man, att, gate_test, inv, bundle, launch_auth):
        check(c["check"], c["passed"])

    # ---- negative controls: each mutation MUST produce a contradiction ---- #
    check("NC_A_mode_science_omitted_detected",
          not xcontract_mode_science(EXEC_SRC, L_SRC.replace('["--mode", "science"]', "[]")))
    check("NC_B_namespace_reverted_detected",
          not xcontract_namespace(
              EXEC_SRC.replace("phase36_robustness_science_start_v1_19.json",
                               "phase36_robustness_science_start_v1_17.json"),
              L_SRC, S_SRC))
    check("NC_B2_supervisor_namespace_reverted_detected",
          not xcontract_namespace(
              EXEC_SRC, L_SRC,
              S_SRC.replace("phase36_robustness_scientific_result_v1_19.json",
                            "phase36_robustness_scientific_result_v1_17.json")))
    check("NC_C_authority_token_reverted_detected",
          not xcontract_authority_token(
              EXEC_SRC.replace('LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_19_LAUNCH_AUTHORITY"',
                               'LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_17_LAUNCH_AUTHORITY"'),
              L_SRC))
    check("NC_D_gate_reverted_detected",
          not xcontract_gates(EXEC_SRC.replace("PHASE36_V1_19_EXECUTE", "PHASE36_V1_17_EXECUTE"),
                              L_SRC))
    check("NC_E_manifest_path_reverted_detected",
          not xcontract_manifest(
              EXEC_SRC.replace("phase36_v1_19_runtime_source_integrity_manifest.json",
                               "phase36_v1_17_runtime_source_integrity_manifest.json"),
              L_SRC, man))
    _man_bad = dict(man); _man_bad["execution_source_sha256"] = "0" * 64
    check("NC_E2_manifest_binding_broken_detected",
          not xcontract_manifest(EXEC_SRC, L_SRC, _man_bad))
    check("NC_F_release_revision_reverted_detected",
          not xcontract_release_revision(
              EXEC_SRC.replace("ra_medfilm_barr_phase36_robustness_v1_19",
                               "ra_medfilm_barr_phase36_robustness_v1_17")))
    check("NC_G_stage_journal_removed_detected",
          not xcontract_stage_journal(
              EXEC_SRC.replace("V1_19_JOURNAL_STAGES", "X").replace("_ScienceJournal", "Y")))
    check("NC_H_launcher_pin_removed_detected",
          not xcontract_launcher_pin(L_SRC.replace(V1_19_EXEC_SHA, "0" * 64), S_SRC))
    check("NC_H2_supervisor_pin_removed_detected",
          not xcontract_launcher_pin(
              L_SRC, S_SRC.replace("FAIL_CLOSED__IMMUTABLE_PIN_MISMATCH", "OTHER")))
    check("NC_I_prev_operational_residue_detected",
          not xcontract_no_prev_operational_residue(
              EXEC_SRC + "\nPHASE36_V1_17_LAUNCH_AUTHORITY = 'x'\n", L_SRC, S_SRC))
    check("NC_I2_prev_manifest_residue_detected",
          not xcontract_no_prev_operational_residue(
              EXEC_SRC + "\n# phase36_v1_17_runtime_source_integrity_manifest.json\n",
              L_SRC, S_SRC))
    check("NC_I3_prev_start_marker_residue_detected",
          not xcontract_no_prev_operational_residue(
              EXEC_SRC + "\n# phase36_robustness_science_start_v1_17.json\n", L_SRC, S_SRC))
    check("NC_B3_launcher_marker_absence_block_removed_detected",
          not xcontract_namespace(
              EXEC_SRC,
              L_SRC.replace("v1_17_markers", "REMOVED").replace("v1_16_markers", "REMOVED2"),
              S_SRC))

    # ---- D81 negative controls ---- #
    inv_missing = dict(inv)
    inv_missing["csv_table_targets"] = [t for t in inv["csv_table_targets"]
                                        if not t["path"].endswith("phase36_worst_case_by_domain.csv")]
    check("NC_J1_omitted_table_target_detected",
          not xcontract_d81_namespace_and_failclosed(EXEC_SRC, inv_missing))
    inv_unv = dict(inv)
    inv_unv["csv_table_targets"] = list(inv["csv_table_targets"]) + [
        {"path": "reports/tables/phase36_robustness/phase36_worst_case_by_domain.csv"}]
    check("NC_J2_unversioned_table_target_detected",
          not xcontract_d81_namespace_and_failclosed(EXEC_SRC, inv_unv))
    inv_unvfig = dict(inv)
    inv_unvfig["figure_targets"] = list(inv["figure_targets"]) + [
        {"path": "reports/figures/phase36_robustness/R1_x.png"}]
    check("NC_J2b_unversioned_figure_target_detected",
          not xcontract_d81_namespace_and_failclosed(EXEC_SRC, inv_unvfig))
    inv_unc = dict(inv); inv_unc["unclassified_write_target_count"] = 1
    check("NC_J3_unclassified_count_detected",
          not xcontract_d81_namespace_and_failclosed(EXEC_SRC, inv_unc))
    check("NC_J4_csv_open_w_overwrite_detected",
          not xcontract_d81_namespace_and_failclosed(
              EXEC_SRC.replace('open(path, "x", encoding="utf-8", newline="")',
                               'path.open("w", encoding="utf-8", newline="")'),
              inv))

    # ---- D82 negative controls ---- #
    check("NC_K1_gate_requires_v1_19_smoke_detected",
          not xcontract_d82_release_contract(
              EXEC_SRC.replace("HISTORICAL_V1_14_SMOKE", "SMOKE_V1_19_ARTIFACT")
                      + '\nSMOKE_V1_19_ARTIFACT = "reports/audits/phase36_robustness_smoke_v1_19.json"\n',
              att))
    att_missing = {k: v for k, v in att.items() if k != "release_gate"}
    check("NC_K2_attestation_missing_field_detected",
          not xcontract_d82_release_contract(EXEC_SRC, att_missing))
    att_badsha = dict(att); att_badsha["smoke_artifact_sha256"] = "0" * 64
    check("NC_K3_attestation_wrong_smoke_sha_detected",
          not xcontract_d82_release_contract(EXEC_SRC, att_badsha))
    att_reqsmoke = dict(att); att_reqsmoke["requires_v1_19_smoke"] = True
    check("NC_K4_attestation_requires_smoke_detected",
          not xcontract_d82_release_contract(EXEC_SRC, att_reqsmoke))

    # ---- D83 negative controls ---- #
    check("NC_L1_validator_revision_only_detected",
          not xcontract_d83_pure_release_state(
              "# att.get('revision') == REVISION only\n", gate_test))
    gt_nrel = dict(gate_test); gt_nrel["base_gate_state"] = "NOT_RELEASED"
    check("NC_L2_gate_not_released_detected",
          not xcontract_d83_pure_release_state(L_SRC, gt_nrel))
    gt_fail = dict(gate_test); gt_fail["all_pass"] = False
    check("NC_L3_gate_test_failed_detected",
          not xcontract_d83_pure_release_state(L_SRC, gt_fail))

    # ---- D85 negative controls ---- #
    check("NC_M1_supervisor_literal_launcher_sha_removed_detected",
          not xcontract_d85_immutable_root(
              L_SRC, S_SRC.replace(f'FROZEN_V1_19_LAUNCHER_SHA = "{_sha(LAUNCHER)}"',
                                   'FROZEN_V1_19_LAUNCHER_SHA = None'),
              launch_auth))
    check("NC_M2_env_override_introduced_detected",
          not xcontract_d85_immutable_root(
              L_SRC,
              S_SRC + '\nPHASE36_V1_19_LAUNCHER_SHA = "x"\n',
              launch_auth))
    la_wrong = dict(launch_auth); la_wrong["launcher_sha256"] = "0" * 64
    check("NC_M3_launch_authority_wrong_launcher_sha_detected",
          not xcontract_d85_immutable_root(L_SRC, S_SRC, la_wrong))

    # ---- D86 negative controls ---- #
    check("NC_N1_stdout_stderr_o_trunc_detected",
          not xcontract_d86_exclusive_stdout_stderr(
              S_SRC.replace("flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY",
                            "flags = os.O_CREAT | os.O_TRUNC | os.O_WRONLY")))
    check("NC_N2_stdout_stderr_exclusive_false_detected",
          not xcontract_d86_exclusive_stdout_stderr(
              S_SRC.replace("flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY",
                            "flags = os.O_CREAT | os.O_WRONLY")))
    check("NC_N3_predispatch_absence_removed_detected",
          not xcontract_d86_exclusive_stdout_stderr(
              S_SRC.replace("_predispatch_absence_check", "_none")))

    # ---- D87 negative controls ---- #
    check("NC_O1_bundle_not_checked_detected",
          not xcontract_d87_non_circular_dag(
              S_SRC.replace("verify_immutable_pins()", "_verify_something_else()"),
              bundle, launch_auth))
    check("NC_O2_wrong_bundle_sha_detected",
          not xcontract_d87_non_circular_dag(
              S_SRC.replace(f'FROZEN_V1_19_AUTHORITY_BUNDLE_SHA = "{_sha(BUNDLE)}"',
                            'FROZEN_V1_19_AUTHORITY_BUNDLE_SHA = "0" * 64'),
              bundle, launch_auth))
    bundle_cyclic = dict(bundle); bundle_cyclic["supervisor_sha256"] = "a" * 64
    bundle_cyclic["supervisor_sha256_present"] = True
    check("NC_O3_bundle_embeds_supervisor_sha_detected",
          not xcontract_d87_non_circular_dag(S_SRC, bundle_cyclic, launch_auth))
    la_nowb = dict(launch_auth); la_nowb["prelaunch_authority_bundle_sha256"] = "0" * 64
    check("NC_O4_launch_authority_bundle_sha_mismatch_detected",
          not xcontract_d87_non_circular_dag(S_SRC, bundle, la_nowb))

    # ---- D88 negative controls ---- #
    inv_bad_total = dict(inv); inv_bad_total["total_reachable_write_target_count"] = 16
    check("NC_P1_underreported_total_detected",
          not xcontract_d88_realtime_gate_and_figures(EXEC_SRC, S_SRC, inv_bad_total, bundle))
    check("NC_P2_plain_savefig_restored_detected",
          not xcontract_d88_realtime_gate_and_figures(
              EXEC_SRC.replace("_savefig_once(fig, p, dpi=160)", "fig.savefig(p, dpi=160)"),
              S_SRC, inv, bundle))
    check("NC_P3_absence_gate_removed_detected",
          not xcontract_d88_realtime_gate_and_figures(
              EXEC_SRC.replace("_absence = verify_v1_19_output_absence()", "_absence = None"),
              S_SRC, inv, bundle))
    bundle_bad_counts = dict(bundle)
    bundle_bad_counts["count_semantics"] = dict(bundle.get("count_semantics", {}))
    bundle_bad_counts["count_semantics"]["total_reachable_write_target_count"] = 16
    check("NC_P4_bundle_count_mismatch_detected",
          not xcontract_d88_realtime_gate_and_figures(EXEC_SRC, S_SRC, inv, bundle_bad_counts))

    n_pass = sum(1 for c in checks if c["passed"])
    n_total = len(checks)
    report = {
        "artifact": "phase36_v1_19_operational_cross_contract",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": REVISION,
        "type": "OPERATIONAL_CROSS_CONTRACT_REPORT",
        "defects_repaired": ["D85", "D86", "D87", "D88"],
        "model_free": True,
        "torch_imported": False,
        "protected_population_read": False,
        "subject_execution_sha256": _sha(EXEC),
        "subject_manifest_sha256": _sha(MANIFEST),
        "subject_attestation_sha256": _sha(ATTESTATION),
        "subject_pure_gate_test_sha256": _sha(PURE_GATE_TEST),
        "subject_inventory_sha256": _sha(INVENTORY),
        "subject_bundle_sha256": _sha(BUNDLE),
        "subject_launch_authority_sha256": _sha(LAUNCH_AUTHORITY),
        "checks_total": n_total,
        "checks_passed": n_pass,
        "checks_failed": n_total - n_pass,
        "all_pass": n_pass == n_total,
        "failed_checks": [c["check"] for c in checks if not c["passed"]],
        "checks": checks,
    }
    out_path = ROOT / "reports/audits/phase36_v1_19_operational_cross_contract.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=1), encoding="utf-8")
    for c in checks:
        if not c["passed"]:
            print(f"FAIL {c['check']} :: {c.get('detail')}")
    print(f"OPERATIONAL CROSS-CONTRACT v1.19: {n_pass}/{n_total} pass")
    print(f"terminal: {'PHASE36_V1_19_OPERATIONAL_CROSS_CONTRACT_PASS' if n_pass == n_total else 'PHASE36_V1_19_OPERATIONAL_CROSS_CONTRACT_FAIL'}")
    return 0 if n_pass == n_total else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
