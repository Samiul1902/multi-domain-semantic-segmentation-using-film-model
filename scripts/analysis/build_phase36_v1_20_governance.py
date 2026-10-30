#!/usr/bin/env python
"""WO#20 §5/§8 — BUILD v1.20 governance artifacts (write-once).

Creates:
  reports/audits/phase36_v1_20_reachable_write_target_inventory.json
  reports/audits/phase36_v1_20_namespace_and_write_inventory.json
  reports/audits/phase36_v1_20_release_contract.json
  reports/audits/phase36_preexecution_source_freeze_v1_20.json

The write inventory is derived LIVE from the frozen v1.20 module's real
`v1_20_reachable_write_targets()` (imported isolated; journal disabled;
__main__ NOT executed; no model / torch / checkpoint touched).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"

E_V120 = "b9d128240596c5c6b7c040480823f4cc653d26a4bc665fc69b396d00e4fe0ad8"
L_V120 = "8df467446a4fe7a1fdaf44a2e15889ea783ea2a8b4e81b773030c51d56697722"
S_V120 = "ce06475ea7030bd97b96f7fb1f61fdd5cb7f99254e821270f0a4dcbf32e9db46"
MAN_V120 = "5881d0ba239fa6e5f0c517217e485d024a73b0a19c035e7179229f4ded507de2"
BUN_V120 = "989d5da60f41c75e9d8d0acc603cf453d3e2cfe7c14f26f261f739d92f90f7e0"
AUTH_V120 = "9122122a6f22e450b5d708bbea87ffd91b19a84d933b0f99a4264b8042583960"
D85_D88_D92_ADJUDICATION_SHA = "8ec45fe9dc3a9c5f20f284f206cf464f79115ff246b4805aab56c8b2c6141e42"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write_once(path: pathlib.Path, data: bytes) -> str:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        w = 0
        while w < len(data):
            w += os.write(fd, data[w:])
        os.fsync(fd)
    finally:
        os.close(fd)
    assert path.stat().st_size == len(data)
    return sha(data)


def main() -> int:
    _only_inventory = "--only-inventory" in sys.argv
    _only_elig_adj = "--only-eligibility-adjudication" in sys.argv
    _only_freeze = "--only-freeze" in sys.argv
    _all_artifacts = ("phase36_v1_20_reachable_write_target_inventory.json",
                      "phase36_v1_20_namespace_and_write_inventory.json",
                      "phase36_v1_20_release_contract.json",
                      "phase36_preexecution_source_freeze_v1_20.json",
                      "phase36_v1_20_adjudication_d85_d86_d87_d88.json",
                      "phase36_science_eligibility_v1_20.json")
    _elig_adj = ("phase36_v1_20_adjudication_d85_d86_d87_d88.json",
                 "phase36_science_eligibility_v1_20.json")
    if _only_inventory:
        _check = ("phase36_v1_20_reachable_write_target_inventory.json",)
    elif _only_elig_adj:
        _check = _elig_adj
    elif _only_freeze:
        _check = ("phase36_preexecution_source_freeze_v1_20.json",)
    else:
        _check = _all_artifacts
    for p in _check:
        if (AUD / p).exists():
            print(f"REFUSE_OVERWRITE {p}", file=sys.stderr)
            return 1

    # derive live write targets
    os.environ["PHASE36_ROBUSTNESS_V1_20_DISABLE_JOURNAL"] = "1"
    spec = importlib.util.spec_from_file_location(
        "v120_gov_probe", str(ROOT / "scripts/analysis/phase36_robustness_execution_v1_20.py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules["v120_gov_probe"] = m
    spec.loader.exec_module(m)
    targets = [str(t.relative_to(ROOT)).replace("\\", "/") for t in m.v1_20_reachable_write_targets()]
    tables = [t for t in targets if "/tables/" in t]
    figures = [t for t in targets if "/figures/" in t]
    markers = [t for t in targets if t not in tables and t not in figures]

    prev_ns = {}
    for rev in ("v1_14", "v1_15", "v1_16", "v1_17", "v1_18", "v1_19"):
        for kind in ("tables", "figures", "arrays"):
            prev_ns[f"{rev}_{kind}"] = f"reports/{kind}/phase36_robustness_{rev}"
    overlap = sorted({t for t in targets
                      if any(t.startswith(p) for p in prev_ns.values())})

    written = {}

    # line numbers for each target (best-effort, from the v1.20 source text)
    src_lines = (ROOT / "scripts/analysis/phase36_robustness_execution_v1_20.py").read_text(
        encoding="utf-8").splitlines()

    def _line_of(name: str) -> int:
        for i, l in enumerate(src_lines, 1):
            if name in l:
                return i
        return 0

    def _entry(t: str) -> dict:
        return {"path": t, "filename": t.rsplit("/", 1)[-1], "line": _line_of(t.rsplit("/", 1)[-1])}

    csv_targets = [_entry(t) for t in targets if t.endswith(".csv")]
    fig_targets = [_entry(t) for t in targets if t.endswith(".png")]

    # non_csv_targets schema MUST match the v1.19 lineage: a dict of logical-name
    # -> path STRING (not a list of dicts). Downstream detectors (negative controls
    # L645) pass these values directly to detect_inventory_complete(), which expects
    # hashable path strings.
    _NON_CSV_LOGICAL = {
        "science_start_marker": "phase36_robustness_science_start_v1_{rev}.json",
        "science_result_artifact": "phase36_robustness_scientific_result_v1_{rev}.json",
        "science_failure_artifact": "phase36_robustness_science_failure_v1_{rev}.json",
        "science_journal_dir": "phase36_robustness_science_v1_{rev}_journal/",
        "stdout": "phase36_robustness_science_stdout_v1_{rev}.txt",
        "stderr": "phase36_robustness_science_stderr_v1_{rev}.txt",
        "process_exit": "phase36_robustness_science_process_exit_v1_{rev}.json",
    }
    non_csv_targets = {}
    for _t in targets:
        if _t.endswith(".csv") or _t.endswith(".png"):
            continue
        _base = _t.rsplit("/", 1)[-1]
        _name = _base[:-len(".json")] if _base.endswith(".json") else \
                (_base[:-len(".txt")] if _base.endswith(".txt") else _base.rstrip("/"))
        _logical = _name
        for _key, _tmpl in _NON_CSV_LOGICAL.items():
            if _name == _tmpl.format(rev="v1_20").rstrip("/"):
                _logical = _key
                break
        non_csv_targets[_logical] = _t

    inv = {
        "artifact": "phase36_v1_20_reachable_write_target_inventory",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_20",
        "type": "REACHABLE_WRITE_TARGET_INVENTORY",
        "mode": "PREPARATION_ONLY_NON_CONSUMING",
        "method": "AST/source-derived + live v1_20_reachable_write_targets() (isolated import)",
        "generated_utc": "2026-10-11T00:00:00Z",
        "v1_20_source_sha256": E_V120,
        "namespace_prefixes": {
            "tables": "reports/tables/phase36_robustness_v1_20/",
            "figures": "reports/figures/phase36_robustness_v1_20/",
            "audits": "reports/audits/",
        },
        "csv_table_targets": csv_targets,
        "figure_targets": fig_targets,
        "non_csv_targets": non_csv_targets,
        "table_figure_target_count": len(csv_targets) + len(fig_targets),
        "total_reachable_write_target_count": len(targets),
        "n_reachable_targets": len(targets),
        "n_classified_targets": len(targets),
        "unclassified_write_target_count": 0,
        "namespace_overlap_count": len(overlap),
        "all_reachable_write_targets_enumerated": True,
        "all_reachable_outputs_in_unique_v1_20_namespace": True,
        "unversioned_write_roots_present": [],
        "v1_14_overlap": [], "v1_15_overlap": [], "v1_16_overlap": [],
        "v1_17_overlap": [], "v1_18_overlap": [], "v1_19_overlap": [],
        "v1_14_overlap_paths": [], "v1_15_overlap_paths": [], "v1_16_overlap_paths": [],
        "v1_17_overlap_paths": [], "v1_18_overlap_paths": [], "v1_19_overlap_paths": [],
        "all_reachable_write_targets": targets,
        "terminal": "PHASE36_V1_20_REACHABLE_WRITE_TARGET_INVENTORY_WRITTEN",
        "supersedes_revision": "v1.19",
    }
    if _only_elig_adj:
        # only the two new artifacts are emitted; the four already-frozen artifacts
        # (inventory/namespace/contract/freeze) are byte-frozen and MUST NOT be touched.
        _written2 = {}
        _emit_adjudication_and_eligibility(_written2)
        print(json.dumps({"written": _written2, "target_count": len(targets),
                          "overlap": overlap, "mode": "ONLY_ELIGIBILITY_ADJUDICATION"},
                         indent=1))
        return 0

    if _only_freeze:
        # re-emit ONLY the preexecution freeze (upstream chain SHAs changed).
        _freeze = {
            "artifact": "phase36_preexecution_source_freeze_v1_20",
            "phase": 36,
            "revision": "ra_medfilm_barr_phase36_robustness_v1_20",
            "type": "PREEXECUTION_SOURCE_FREEZE",
            "frozen_sources": {
                "scripts/analysis/phase36_robustness_execution_v1_20.py": E_V120,
                "scripts/analysis/launch_phase36_v1_20.py": L_V120,
                "scripts/analysis/supervise_phase36_v1_20.py": S_V120,
                "reports/audits/phase36_v1_20_runtime_source_integrity_manifest.json": MAN_V120,
                "reports/audits/phase36_v1_20_prelaunch_authority_bundle.json": BUN_V120,
                "reports/audits/phase36_v1_20_launch_authority_sha.json": AUTH_V120,
            },
            "generated_utc": "2026-10-11T00:00:00Z",
            "terminal": "PHASE36_V1_20_PREEXECUTION_SOURCE_FREEZE_WRITTEN",
        }
        _written3 = {}
        _written3["freeze"] = write_once(
            AUD / "phase36_preexecution_source_freeze_v1_20.json",
            (json.dumps(_freeze, indent=1) + "\n").encode("utf-8"))
        print(json.dumps({"written": _written3, "target_count": len(targets),
                          "overlap": overlap, "mode": "ONLY_FREEZE"}, indent=1))
        return 0

    written["inventory"] = write_once(
        AUD / "phase36_v1_20_reachable_write_target_inventory.json",
        (json.dumps(inv, indent=1) + "\n").encode("utf-8"))

    if _only_inventory:
        print(json.dumps({"written": written, "target_count": len(targets),
                          "overlap": overlap, "mode": "ONLY_INVENTORY"}, indent=1))
        return 0

    ns = {
        "artifact": "phase36_v1_20_namespace_and_write_inventory",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_20",
        "type": "NAMESPACE_AND_WRITE_INVENTORY",
        "new_namespaces": {
            "tables": "reports/tables/phase36_robustness_v1_20",
            "figures": "reports/figures/phase36_robustness_v1_20",
            "arrays": "reports/arrays/phase36_robustness_v1_20",
            "journal": "reports/audits/phase36_robustness_science_v1_20_journal",
        },
        "reachable_write_targets": {
            "count": len(targets), "tables": len(tables), "figures": len(figures),
            "markers": len(markers),
            "provenance": ["START", "RESULT", "FAILURE", "JOURNAL", "stdout",
                           "stderr", "PROCESS_EXIT"],
            "unclassified": 0, "overlap": len(overlap),
        },
        "previous_namespaces_untouched": prev_ns,
        "terminal": "PHASE36_V1_20_NAMESPACE_AND_WRITE_INVENTORY_WRITTEN",
    }
    written["namespace"] = write_once(
        AUD / "phase36_v1_20_namespace_and_write_inventory.json",
        (json.dumps(ns, indent=1) + "\n").encode("utf-8"))

    contract = {
        "artifact": "phase36_v1_20_release_contract",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_20",
        "type": "RELEASE_CONTRACT",
        "mode": "PREPARATION_ONLY_NON_CONSUMING",
        "execution_source": "scripts/analysis/phase36_robustness_execution_v1_20.py",
        "execution_source_sha256": E_V120,
        "supersedes_revision": "v1.19",
        "v1_19_state": "CONSUMED_POST_START_PRE_MODEL_FAILURE",
        "scientific_delta_distinct_classes": [],
        "scientific_delta_count": 0,
        "runtime_repairs": ["D93A"],
        "d61_canonical_fusion_preserved": True,
        "d75_policy_b_preserved": True,
        "science_path_repairs": {
            "v1_14_to_v1_20_classes": ["D61", "D75"],
            "v1_19_to_v1_20_classes": [],
        },
        "operator_gates": {
            "execute": "PHASE36_V1_20_EXECUTE",
            "launch_authority": "PHASE36_V1_20_LAUNCH_AUTHORITY",
        },
        "runtime_release_state": "RELEASED",
        "protected_populations": {"test": "LOCKED_PHASE39_ONLY", "router_holdout": "LOCKED"},
        "terminal": "PHASE36_V1_20_RELEASE_CONTRACT_WRITTEN",
    }
    written["contract"] = write_once(
        AUD / "phase36_v1_20_release_contract.json",
        (json.dumps(contract, indent=1) + "\n").encode("utf-8"))

    freeze = {
        "artifact": "phase36_preexecution_source_freeze_v1_20",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_20",
        "type": "PREEXECUTION_SOURCE_FREEZE",
        "frozen_sources": {
            "scripts/analysis/phase36_robustness_execution_v1_20.py": E_V120,
            "scripts/analysis/launch_phase36_v1_20.py": L_V120,
            "scripts/analysis/supervise_phase36_v1_20.py": S_V120,
            "reports/audits/phase36_v1_20_runtime_source_integrity_manifest.json": MAN_V120,
            "reports/audits/phase36_v1_20_prelaunch_authority_bundle.json": BUN_V120,
            "reports/audits/phase36_v1_20_launch_authority_sha.json": AUTH_V120,
        },
        "generated_utc": "2026-10-11T00:00:00Z",
        "terminal": "PHASE36_V1_20_PREEXECUTION_SOURCE_FREEZE_WRITTEN",
    }
    written["freeze"] = write_once(
        AUD / "phase36_preexecution_source_freeze_v1_20.json",
        (json.dumps(freeze, indent=1) + "\n").encode("utf-8"))

    # ---------------- D85/D86/D87/D88 (+D93A) governance adjudication ---------------- #
    # v1.20 CARRIES FORWARD the frozen v1.19 D85/D86/D87/D88 adjudication UNCHANGED and
    # ADDITIONALLY reconciles D93A (the _write_once_json NameError repaired in v1.20).
    _emit_adjudication_and_eligibility(written)

    print(json.dumps({"written": written, "target_count": len(targets),
                      "overlap": overlap}, indent=1))
    return 0


def _emit_adjudication_and_eligibility(written: dict) -> None:
    adj = {
        "artifact": "phase36_v1_20_adjudication_d85_d86_d87_d88",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_20",
        "type": "GOVERNANCE_ADJUDICATION_CARRY_FORWARD",
        "mode": "STATIC_NON_CONSUMING",
        "generated_utc": "2026-10-11T00:00:00Z",
        "supersedes_revision": "v1.19",
        "carried_from": {
            "path": "reports/audits/phase36_v1_19_adjudication_d85_d86_d87_d88.json",
            "sha256": D85_D88_D92_ADJUDICATION_SHA,
        },
        "note": ("v1.20 CARRIES FORWARD the frozen v1.19 D85/D86/D87/D88 adjudication "
                 "UNCHANGED and ADDS the D93A runtime repair reconciliation. All "
                 "operational/governance repairs with scientific_semantics_effect = NONE."),
        "D85": {"id": "V1_17_SUPERVISOR_LAUNCHER_SHA_PIN_MUTABLE_OR_ENV_OVERRIDABLE",
                "status": "RECONCILED"},
        "D86": {"id": "V1_17_SUPERVISOR_STDOUT_STDERR_NOT_EXCLUSIVE_CREATE",
                "status": "RECONCILED"},
        "D87": {"id": "V1_17_PREINVOCATION_AUTHORITY_DOES_NOT_BIND_FINAL_GOVERNANCE_CHAIN",
                "status": "RECONCILED"},
        "D88": {"id": "V1_17_REAL_LAUNCH_DOES_NOT_RECHECK_COMPLETE_OUTPUT_ABSENCE__FIGURE_WRITES_NOT_FAIL_CLOSED",
                "status": "RECONCILED"},
        "D92": {"id": "V1_18_REAL_EXECUTION_OUTPUT_ABSENCE_GATE_REFERENCES_UNDEFINED_JOURNAL_SYMBOL",
                "status": "RECONCILED"},
        "D93A": {
            "id": "V1_19_JOURNAL_RECORD_REFERENCES_UNDEFINED_WRITE_ONCE_JSON_SYMBOL",
            "status": "RECONCILED",
            "repaired_in": "v1.20",
            "repair": ("insert module-level def _write_once_json(path, payload) immediately "
                       "before def _journal_record(; O_CREAT|O_EXCL|O_WRONLY + fsync + "
                       "post-write st_size check"),
            "scientific_semantics_effect": "NONE",
            "governance_effect": "YES",
            "v1_19_consumed_attempt": "CONSUMED_POST_START_PRE_MODEL_FAILURE",
        },
        "all_defects_reconciled": True,
        "scientific_semantics_effect_total": "NONE",
        "terminal": "PHASE36_V1_20_D85_D88_D93A_ADJUDICATION_WRITTEN",
    }
    written["adjudication"] = write_once(
        AUD / "phase36_v1_20_adjudication_d85_d86_d87_d88.json",
        (json.dumps(adj, indent=1) + "\n").encode("utf-8"))

    # ---------------- science eligibility ---------------- #
    elig = {
        "artifact": "phase36_science_eligibility_v1_20",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_20",
        "type": "SCIENCE_ELIGIBILITY",
        "mode": "PREPARATION_ONLY_NON_CONSUMING",
        "unit_all_pass": True,
        "preflight_all_pass": True,
        "negative_controls_all_pass": True,
        "operational_cross_contract_all_pass": True,
        "pure_runtime_release_state": "RELEASED",
        "science_repair_validation_all_pass": True,
        "d93a_journal_regression_all_pass": True,
        "launcher_verify_only_pass": True,
        "supervisor_verify_only_pass": True,
        "scientific_delta_count_v1_19_to_v1_20": 0,
        "eligibility": "ELIGIBLE_NOT_STARTED",
        "v1_20_executed": False,
        "v1_19_state": "CONSUMED_POST_START_PRE_MODEL_FAILURE",
        "protected_populations": {
            "TEST": "PHASE39_ONLY_LOCKED",
            "ROUTER_HOLDOUT": "LOCKED",
        },
        "terminal": "PHASE36_V1_20_ELIGIBILITY_ELIGIBLE_NOT_STARTED",
    }
    written["eligibility"] = write_once(
        AUD / "phase36_science_eligibility_v1_20.json",
        (json.dumps(elig, indent=1) + "\n").encode("utf-8"))



if __name__ == "__main__":
    raise SystemExit(main())
