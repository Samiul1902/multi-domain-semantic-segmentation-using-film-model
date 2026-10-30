#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase36 — D81/D82/D83 v1.16 OPERATIONAL ADJUDICATION (write-once, WO#17C).

STATIC / NON-CONSUMING.  Adjudicates three operational defects of the frozen
v1.16 family that block the final one-shot provenance contract:

  D81 = V1_16_OUTPUT_NAMESPACE_AUDIT_INCOMPLETE__INHERITED_UNVERSIONED_TABLE_AND_FIGURE_WRITE_TARGETS
  D82 = V1_16_RELEASE_ATTESTATION_RUNTIME_GATE_SCHEMA_INCOMPATIBLE
  D83 = V1_16_READINESS_VALIDATION_DID_NOT_PROVE_RUNTIME_RELEASE_STATE

D81 is established by an AST-derived enumeration of the STATIC reachable write
surface from ``run_science`` — NOT from files present on disk.  Every write
target reachable from ``run_science`` is enumerated (CSV tables, R1-R5 figures,
science START/RESULT/FAILURE markers, stdout/stderr, PROCESS_EXIT, journal
records) and classified.  The inherited ``_write_csv(..., "w")`` overwrite
semantics is classified as INCOMPATIBLE with the one-shot provenance contract.

D82 is established by MECHANICALLY reproducing the frozen pure release-gate
logic (no model, no data) and proving the frozen v1.16 attestation yields
NOT_RELEASED (SMOKE_ARTIFACT_MISSING) and omits the D40 schema fields.

D83 records that the v1.16 readiness validation only checked revision/path
strings and never invoked the pure runtime release-state function.

Every finding is derived from the frozen v1.16 source by STATIC analysis
(no execution).  Re-run -> REFUSE_OVERWRITE (rc 2).  Never delete/recreate.

NO v1.16/v1.17 execution.  NO model.  NO checkpoint.  NO VAL image/GT.
NO TEST.  NO ROUTER_HOLDOUT.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

AUD = ROOT / "reports" / "audits"
V16 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_16.py"
V16_LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_16.py"
V16_READINESS = AUD / "phase36_v1_16_final_readiness_attestation.json"
V16_ATTESTATION = AUD / "phase36_v1_16_science_release_attestation.json"
V16_NAMESPACE_MAP = AUD / "phase36_v1_16_output_namespace_map.json"
OUT = AUD / "phase36_v1_16_operational_adjudication_d81_d83_v1_0.json"

V16_SHA = "a96b74caa4587aa9d2f83b79ed39c13075a88086109e31d991695a75ec4abab9"
V16_LAUNCHER_SHA = "a069345a8d332c549fc25799fc8d9e5e1b4b46e6b878e23f0e83d7a4c011e16c"
V16_MANIFEST_SHA = "f9f245b41bdf904cdb4f9da7c3d32361da806c7451773ce721d3d0a023f64e18"

# Frozen constants as they appear in the v1.16 source (verified by grep).
SMOKE_V1_16_ARTIFACT = "reports/audits/phase36_robustness_smoke_v1_16.json"
SCIENCE_RELEASE_ATTESTATION = "reports/audits/phase36_v1_16_science_release_attestation.json"
_SCIENCE_RELEASE_REVISION = "ra_medfilm_barr_phase36_robustness_v1_16"


def sha256_file(p: Path) -> str | None:
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_once_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=1, ensure_ascii=False, default=str).encode("utf-8")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        total = 0
        while total < len(data):
            n = os.write(fd, data[total:])
            if n is None or n <= 0:
                raise OSError(f"SHORT_WRITE at {total}/{len(data)} for {path}")
            total += n
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(data):
        raise OSError(f"POST_WRITE_SIZE_MISMATCH for {path}")


# --------------------------------------------------------------------------- #
# AST reachable-write-surface enumeration
# --------------------------------------------------------------------------- #
class _ReachableWriteVisitor(ast.NodeVisitor):
    """Collect write-target constructor sites reachable inside a function body.

    Records:
      - ``_write_csv(PATH_EXPR, ...)`` calls (table writers)
      - ``<expr>.savefig(PATH_EXPR, ...)`` calls (figure writers)
      - ``<expr>.write_text("")`` (empty-CSV overwrite path)
      - ``open(PATH_EXPR, "w"/"x")`` calls
    """

    def __init__(self) -> None:
        self.csv_calls: list[dict] = []
        self.savefig_calls: list[dict] = []
        self.write_text_calls: list[dict] = []
        self.open_calls: list[dict] = []

    @staticmethod
    def _render(node: ast.AST) -> str:
        try:
            return ast.unparse(node)
        except Exception:  # pragma: no cover
            return "<unparseable>"

    def visit_Call(self, node: ast.Call) -> None:  # noqa: D401
        fn = node.func
        # _write_csv(...)
        if isinstance(fn, ast.Name) and fn.id == "_write_csv" and node.args:
            self.csv_calls.append({"line": node.lineno, "target": self._render(node.args[0])})
        # <...>.savefig(...)
        if isinstance(fn, ast.Attribute) and fn.attr == "savefig" and node.args:
            self.savefig_calls.append({"line": node.lineno, "target": self._render(node.args[0])})
        # <...>.write_text(...)
        if isinstance(fn, ast.Attribute) and fn.attr == "write_text":
            self.write_text_calls.append({"line": node.lineno, "target": self._render(fn.value)})
        # open(path, mode)
        if isinstance(fn, ast.Name) and fn.id == "open" and node.args:
            mode = None
            if len(node.args) >= 2:
                mode = self._render(node.args[1])
            self.open_calls.append({"line": node.lineno, "target": self._render(node.args[0]),
                                    "mode": mode})
        self.generic_visit(node)


def _enumerate_reachable_write_surface(src_text: str) -> dict:
    """AST-enumerate all write call-sites; then restrict to the science-reachable set."""
    tree = ast.parse(src_text)
    funcs = {}
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs[n.name] = n

    # Compute the transitive call graph closure rooted at run_science.
    def called_names(node):
        out = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                f = sub.func
                if isinstance(f, ast.Name):
                    out.add(f.id)
                elif isinstance(f, ast.Attribute):
                    out.add(f.attr)
        return out

    root = "run_science"
    reachable = set()
    stack = [root]
    while stack:
        name = stack.pop()
        if name in reachable:
            continue
        reachable.add(name)
        fn = funcs.get(name)
        if fn is None:
            continue
        for callee in called_names(fn):
            if callee in funcs and callee not in reachable:
                stack.append(callee)

    # Enumerate write sites in every reachable function.
    csv_sites, fig_sites, wt_sites, open_sites = [], [], [], []
    for name in sorted(reachable):
        fn = funcs.get(name)
        if fn is None:
            continue
        v = _ReachableWriteVisitor()
        v.visit(fn)
        for c in v.csv_calls:
            csv_sites.append({"function": name, **c})
        for c in v.savefig_calls:
            fig_sites.append({"function": name, **c})
        for c in v.write_text_calls:
            wt_sites.append({"function": name, **c})
        for c in v.open_calls:
            open_sites.append({"function": name, **c})

    # Module-level path constants (TAB/ARR/FIG).
    consts = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            consts[n.targets[0].id] = _ReachableWriteVisitor._render(n.value)

    return {
        "science_reachable_functions": sorted(reachable),
        "csv_write_sites": csv_sites,
        "figure_savefig_sites": fig_sites,
        "write_text_sites": wt_sites,
        "open_write_sites": open_sites,
        "module_path_constants": {k: consts.get(k) for k in ("TAB", "ARR", "FIG", "ROOT")},
    }


def main() -> int:
    src = V16.read_text(encoding="utf-8")
    surf = _enumerate_reachable_write_surface(src)

    # ---------------- D81 ---------------- #
    # 1. Inherited unversioned table / figure / array roots.
    tab_expr = surf["module_path_constants"].get("TAB")
    fig_expr = surf["module_path_constants"].get("FIG")
    arr_expr = surf["module_path_constants"].get("ARR")
    tab_unversioned = bool(tab_expr and "reports" in tab_expr and "v1_16" not in tab_expr)
    fig_unversioned = bool(fig_expr and "reports" in fig_expr and "v1_16" not in fig_expr)
    arr_unversioned = bool(arr_expr and "reports" in arr_expr and "v1_16" not in arr_expr)

    # 2. Enumerate concrete CSV table targets reachable from run_science.
    csv_targets = sorted({s["target"].split("/")[-1].strip('"')
                          for s in surf["csv_write_sites"]})
    fig_targets = sorted({s["target"].split("/")[-1].strip('"')
                          for s in surf["figure_savefig_sites"]})
    n_csv_sites = len(surf["csv_write_sites"])
    n_fig_sites = len(surf["figure_savefig_sites"])

    # 3. Overwrite semantics: _write_csv uses open("w") + write_text("") on empty.
    write_csv_def = None
    m = re.search(r"def _write_csv\((.|\n)*?\n\n\n", src)
    if m:
        write_csv_def = m.group(0)
    csv_uses_w = bool(write_csv_def and 'path.open("w"' in write_csv_def)
    csv_uses_write_text = bool(write_csv_def and "path.write_text(" in write_csv_def)
    overwrite_semantics = bool(csv_uses_w and csv_uses_write_text)

    # 4. Science marker/journal targets ARE versioned; table/figure are NOT.
    marker_versioned = ("phase36_robustness_scientific_result_v1_16.json" in src
                        and "phase36_robustness_science_start_v1_16.json" in src)
    namespace_split = bool(marker_versioned and (tab_unversioned or fig_unversioned or arr_unversioned))

    d81 = bool((tab_unversioned or fig_unversioned or arr_unversioned)
               and n_csv_sites > 0 and n_fig_sites > 0 and overwrite_semantics
               and namespace_split)

    # ---------------- D82 ---------------- #
    # Mechanically reproduce the frozen pure release-gate logic (no model/data).
    att = None
    att_path = ROOT / SCIENCE_RELEASE_ATTESTATION
    if att_path.exists():
        att = json.loads(att_path.read_text(encoding="utf-8"))

    def gate_science_release_state() -> dict:
        ev = {"attestation": SCIENCE_RELEASE_ATTESTATION}
        if att is None:
            ev["reason"] = "NO_ATTESTATION"
            return {"state": "NOT_RELEASED", **ev}
        if att.get("revision") != _SCIENCE_RELEASE_REVISION:
            ev["reason"] = "REVISION_MISMATCH"
            return {"state": "NOT_RELEASED", **ev}
        source_sha = sha256_file(V16)
        if att.get("execution_source_sha256") != source_sha:
            ev["reason"] = "SOURCE_SHA_MISMATCH"
            return {"state": "NOT_RELEASED", **ev}
        sp = ROOT / SMOKE_V1_16_ARTIFACT
        if not sp.exists():
            ev["reason"] = "SMOKE_ARTIFACT_MISSING"
            ev["smoke_artifact"] = SMOKE_V1_16_ARTIFACT
            return {"state": "NOT_RELEASED", **ev}
        smoke_sha = sha256_file(sp)
        if att.get("smoke_artifact_sha256") != smoke_sha:
            ev["reason"] = "SMOKE_ARTIFACT_SHA_MISMATCH"
            return {"state": "NOT_RELEASED", **ev}
        if att.get("smoke_all_pass") is not True:
            ev["reason"] = "SMOKE_NOT_SUCCESSFUL"
            return {"state": "NOT_RELEASED", **ev}
        if att.get("scientific_output") is not False:
            ev["reason"] = "SCIENTIFIC_OUTPUT_NOT_FALSE"
            return {"state": "NOT_RELEASED", **ev}
        if att.get("release_gate") != "POST_SMOKE_RELEASE_ADJUDICATION":
            ev["reason"] = "RELEASE_GATE_MISMATCH"
            return {"state": "NOT_RELEASED", **ev}
        ev["reason"] = "SUCCESSFUL_SMOKE_BOUND"
        return {"state": "RELEASED", **ev}

    observed = gate_science_release_state()
    required_d40_fields = ["smoke_artifact_sha256", "smoke_all_pass",
                           "scientific_output", "release_gate"]
    missing_fields = [f for f in required_d40_fields if not (att and f in att)]
    gate_requires_v1_16_smoke = (SMOKE_V1_16_ARTIFACT in src)
    schema_incompatible = bool(observed["state"] != "RELEASED"
                               and len(missing_fields) > 0
                               and gate_requires_v1_16_smoke)
    # Confirm the exec SHA DOES match (so the failure is NOT a source-sha issue,
    # it is specifically the schema/smoke incompatibility).
    exec_sha_matches = (att is not None
                        and att.get("execution_source_sha256") == sha256_file(V16))
    d82 = bool(schema_incompatible and exec_sha_matches)

    # ---------------- D83 ---------------- #
    readiness = None
    if V16_READINESS.exists():
        readiness = json.loads(V16_READINESS.read_text(encoding="utf-8"))
    nmap = None
    if V16_NAMESPACE_MAP.exists():
        nmap = json.loads(V16_NAMESPACE_MAP.read_text(encoding="utf-8"))

    # Did the readiness validator invoke the pure runtime release-state function?
    readiness_blob = json.dumps(readiness, default=str) if readiness else ""
    readiness_mentions_gate = ("release_state" in readiness_blob
                               or "RELEASED" in readiness_blob
                               or "release_gate" in readiness_blob)
    # Namespace map completeness: does it enumerate the table/figure targets?
    nmap_blob = json.dumps(nmap, default=str) if nmap else ""
    nmap_mentions_tables = "phase36_image_robustness_per_sample.csv" in nmap_blob
    nmap_mentions_figures = "R1_image_perturbation_mean_paired_delta_dice_heatmap.png" in nmap_blob
    nmap_complete = bool(nmap_mentions_tables and nmap_mentions_figures)

    d83 = bool(not readiness_mentions_gate and not nmap_complete)

    payload = {
        "artifact": "phase36_v1_16_operational_adjudication_d81_d83_v1_0",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_16",
        "type": "OPERATIONAL_ADJUDICATION",
        "mode": "STATIC_NON_CONSUMING",
        "generated_utc": now(),

        "frozen_v1_16_authorities": {
            "execution_sha256": V16_SHA,
            "launcher_sha256": V16_LAUNCHER_SHA,
            "runtime_manifest_sha256": V16_MANIFEST_SHA,
        },

        "D81": {
            "id": "V1_16_OUTPUT_NAMESPACE_AUDIT_INCOMPLETE__INHERITED_UNVERSIONED_TABLE_AND_FIGURE_WRITE_TARGETS",
            "established": d81,
            "method": "AST-TRANSITIVE-REACHABILITY-FROM-run_science",
            "evidence": {
                "science_reachable_function_count": len(surf["science_reachable_functions"]),
                "module_path_constants": surf["module_path_constants"],
                "table_root_unversioned": tab_unversioned,
                "figure_root_unversioned": fig_unversioned,
                "array_root_unversioned": arr_unversioned,
                "csv_write_site_count": n_csv_sites,
                "figure_savefig_site_count": n_fig_sites,
                "csv_table_targets_enumerated": csv_targets,
                "figure_targets_enumerated": fig_targets,
                "csv_writer_uses_open_w": csv_uses_w,
                "csv_writer_uses_write_text_empty_overwrite": csv_uses_write_text,
                "overwrite_semantics": overwrite_semantics,
                "marker_namespace_versioned": marker_versioned,
                "namespace_split_markers_versioned_but_tables_figures_not": namespace_split,
            },
            "overwrite_semantics_classification":
                "INCOMPATIBLE_WITH_ONE_SHOT_PROVENANCE_CONTRACT",
            "required_repair":
                "v1.17 must route ALL reachable scientific outputs into a unique v1.17 namespace "
                "(TAB reports/tables/phase36_robustness_v1_17/, FIG reports/figures/phase36_robustness_v1_17/, "
                "ARR reports/arrays/phase36_robustness_v1_17/) and make every CSV writer fail-closed "
                "(refuse to write to an existing target) instead of open('w') overwrite.",
        },

        "D82": {
            "id": "V1_16_RELEASE_ATTESTATION_RUNTIME_GATE_SCHEMA_INCOMPATIBLE",
            "established": d82,
            "method": "PURE-RELEASE-GATE-MECHANICAL-REPRODUCTION",
            "evidence": {
                "gate_function": "_gate_science_release_state",
                "gate_requires_v1_16_smoke_artifact": gate_requires_v1_16_smoke,
                "required_smoke_artifact": SMOKE_V1_16_ARTIFACT,
                "required_smoke_artifact_present": (ROOT / SMOKE_V1_16_ARTIFACT).exists(),
                "observed_release_state": observed["state"],
                "observed_reason": observed.get("reason"),
                "attestation_present": att is not None,
                "attestation_required_d40_fields": required_d40_fields,
                "attestation_missing_d40_fields": missing_fields,
                "execution_source_sha_matches": exec_sha_matches,
            },
            "mechanism":
                "The frozen v1.16 release gate requires a v1.16 SMOKE artifact "
                "(phase36_robustness_smoke_v1_16.json) AND four D40 schema fields "
                "(smoke_artifact_sha256 / smoke_all_pass / scientific_output / release_gate). "
                "The frozen v1.16 attestation supplies NONE of these four fields and no v1.16 "
                "smoke artifact exists, so the pure gate deterministically returns NOT_RELEASED.",
            "required_repair":
                "v1.17 must bind a HISTORICAL v1.14 smoke (path+SHA) as runtime-smoke evidence, "
                "NOT require a v1.17 smoke, and emit a v1.17 release attestation whose field set "
                "matches the v1.17 runtime gate schema exactly.",
        },

        "D83": {
            "id": "V1_16_READINESS_VALIDATION_DID_NOT_PROVE_RUNTIME_RELEASE_STATE",
            "established": d83,
            "method": "READINESS-ARTIFACT-STATIC-INSPECTION",
            "evidence": {
                "readiness_artifact": str(V16_READINESS.relative_to(ROOT)),
                "readiness_mentions_release_state_or_gate": readiness_mentions_gate,
                "namespace_map": str(V16_NAMESPACE_MAP.relative_to(ROOT)),
                "namespace_map_mentions_tables": nmap_mentions_tables,
                "namespace_map_mentions_figures": nmap_mentions_figures,
                "namespace_map_complete": nmap_complete,
            },
            "mechanism":
                "The v1.16 readiness validation checked revision/path strings only; it never "
                "invoked the pure runtime release-state function to require state == RELEASED, "
                "and its namespace map did not enumerate the reachable table/figure write targets.",
            "required_repair":
                "The v1.17 next validator MUST invoke the exact pure runtime release-state function "
                "and require state == RELEASED; the v1.17 namespace inventory must enumerate every "
                "reachable write target (unclassified_write_target_count == 0).",
        },

        "v1_16_execution_authorized": False,
        "v1_16_attempt_consumed": False,
        "v1_17_required": True,
        "scientific_semantics_effect": "NONE",
        "classification": "PREEXECUTION_OPERATIONAL_DEFECT__V1_17_FINAL_OPERATIONAL_REPAIR_REQUIRED",

        "v1_16_attempt_absence": {
            "START": (AUD / "phase36_robustness_science_start_v1_16.json").exists(),
            "RESULT": (AUD / "phase36_robustness_scientific_result_v1_16.json").exists(),
            "FAILURE": (AUD / "phase36_robustness_science_failure_v1_16.json").exists(),
            "PROCESS_EXIT": (AUD / "phase36_robustness_science_process_exit_v1_16.json").exists(),
            "stdout": (AUD / "phase36_robustness_science_stdout_v1_16.txt").exists(),
            "stderr": (AUD / "phase36_robustness_science_stderr_v1_16.txt").exists(),
        },

        "preserved": True,
        "v1_16_modified": False,
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync",
        "terminal": "PHASE36_V1_16_OPERATIONAL_ADJUDICATION_D81_D83_COMPLETE",
    }

    if OUT.exists():
        print(json.dumps({"status": "REFUSE_OVERWRITE",
                          "path": str(OUT.relative_to(ROOT))}, indent=1))
        return 2
    _write_once_json(OUT, payload)
    print(json.dumps({
        "status": "D81_D82_D83_ADJUDICATION_WRITTEN",
        "path": str(OUT.relative_to(ROOT)),
        "sha256": sha256_file(OUT),
        "D81_established": d81,
        "D82_established": d82,
        "D83_established": d83,
        "csv_write_sites": n_csv_sites,
        "figure_savefig_sites": n_fig_sites,
        "observed_release_state": observed["state"],
        "observed_reason": observed.get("reason"),
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
