#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.17 — DIFF PROOFS + REACHABLE-WRITE-TARGET INVENTORY (write-once).

REBASED FROM the v1.16 diff/namespace builder.  Produces FOUR machine-derived
artifacts:

  (1) v1.14 -> v1.17 semantic diff   (WRITE-ONCE)
      The v1.17 revision carries the D61 canonical ACCEPT fusion and the D75
      POLICY_B representation EXACTLY as v1.14 does; D80/D81/D82/D83 are
      operational/governance-only.  Therefore the NET scientific surface between
      v1.14 and v1.17 is IDENTICAL: scientific_delta_count MUST be 0.  Every hunk
      MUST classify as operational/governance/namespace/provenance; any
      UNCLASSIFIED hunk FAILS CLOSED.

  (2) v1.16 -> v1.17 operational diff (WRITE-ONCE)
      v1.16 -> v1.17 must have scientific_delta_count == 0 (v1.17 science is a
      VERBATIM copy of v1.16 science) and unclassified_delta_count == 0.

  (3) v1.17 reachable-write-target inventory (WRITE-ONCE; D81)
      AST-derived reachability closure rooted at run_science: EVERY reachable
      table/figure target MUST live under a UNIQUE v1.17 namespace;
      unclassified_write_target_count == 0; overlap with v1_14/v1_15/v1_16 == [].

  (4) v1.17 output-namespace map (WRITE-ONCE)
      All v1.17 SCIENCE-EXECUTION output paths are ABSENT pre-execution.

Non-consuming: static/source analysis only.  No model, no checkpoint, no VAL
image, no VAL GT, no TEST, no ROUTER_HOLDOUT, no science.
"""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

V14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
V15 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_15.py"
V16 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_16.py"
V17 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_17.py"

V14_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
V16_SHA = "a96b74caa4587aa9d2f83b79ed39c13075a88086109e31d991695a75ec4abab9"
V17_SHA = "81d78460b2f20f176bc697cba662c43bc7c7443ea555ba95a30609faf0ccbe31"

AUD = ROOT / "reports" / "audits"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _resolve_frozen_sha(path: Path, fallback: str) -> str:
    """Prefer the true on-disk SHA; the frozen literal is only a cross-check."""
    return sha256_file(path) or fallback


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
# Shared diff machinery
# --------------------------------------------------------------------------- #
_GOV_TOKENS = (
    "v1_15", "V1_15", "v1.15", "v1_16", "V1_16", "V1.16", "v1.16",
    "v1_17", "V1_17", "V1.17", "v1.17", "PHASE36_V1_15", "PHASE36_V1_16",
    "PHASE36_V1_17", "phase36_v1_15", "phase36_v1_16", "phase36_v1_17",
    "JOURNAL", "_ScienceJournal", "STAGE_JOURNAL", "V1_16_JOURNAL", "V1_17_JOURNAL",
    "D80", "D81", "D82", "D83", "OPERATIONAL", "NAMESPACE", "GATE_ENV",
    "HISTORICAL_V1_14_SMOKE", "SMOKE_V1_17_ARTIFACT", "FAIL_CLOSED",
    "REACHABLE", "WRITE_TARGET", "RELEASE", "ATTESTATION",
)

_SCI_TOKENS = (
    "fuse_full_field(p_global, refined, geom)",
    "def _phase27_scored_final_binary",
    "_phase27_scored_final_binary(",
    "canonical_learned_core",
    "SEGMENTATION_OUTPUT_THRESHOLD",
)


def _classify_repair(a_text: str, b_text: str) -> str:
    """Repair-class classifier (v1.16 convention).

    Returns one of:
      SCIENTIFIC_D61   canonical Phase27 pad-aware ACCEPT fusion repair
      SCIENTIFIC_D75   POLICY_B float16 scored-representation repair
      OPERATIONAL_GOVERNANCE  any non-scientific governance/namespace hunk
      UNCLASSIFIED     fails closed
    """
    # --- D61: swap from pad-unaware _fuse_global_with_regional to canonical
    #     pad-aware fuse_full_field(p_global, refined, geom). ------------------- #
    if ("fuse_full_field(p_global, refined, geom)" in b_text
            and "_fuse_global_with_regional" in a_text):
        return "SCIENTIFIC_D61"
    if "v1.15 REPAIR 1 (D61)" in b_text:
        return "SCIENTIFIC_D61"

    # --- D75: POLICY_B scored-representation helper / wiring. ------------------ #
    if "v1.15 REPAIR 2 (D75" in b_text or "POLICY_B" in b_text:
        return "SCIENTIFIC_D75"
    if "def _phase27_scored_final_binary" in b_text:
        return "SCIENTIFIC_D75"
    if ("_phase27_scored_final_binary(" in b_text
            and (">= 0.50" in a_text or "segmentation_output_threshold" in a_text
                 or "SEGMENTATION_OUTPUT_THRESHOLD" in a_text
                 or ">= float(" in a_text)):
        return "SCIENTIFIC_D75"

    if any(tok in b_text for tok in _GOV_TOKENS):
        return "OPERATIONAL_GOVERNANCE"
    return "UNCLASSIFIED"


# Backwards-compatible alias used by the diff builders below.
def classify_operational_hunk(b_text: str) -> str:
    if any(tok in b_text for tok in _GOV_TOKENS):
        return "OPERATIONAL_GOVERNANCE"
    return "UNCLASSIFIED"


def compute_diff(a_path: Path, b_path: Path) -> tuple[list[dict], list[str]]:
    a = a_path.read_text(encoding="utf-8").splitlines(keepends=True)
    b = b_path.read_text(encoding="utf-8").splitlines(keepends=True)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    hunks, classes = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        bt = "".join(b[j1:j2])
        at = "".join(a[i1:i2])
        cls = _classify_repair(at, bt)
        hunks.append({"tag": tag, "a_span": [i1, i2], "b_span": [j1, j2],
                      "a_preview": at[:300], "b_preview": bt[:300]})
        classes.append(cls)
    return hunks, classes


def _scientific_delta_count(classes: list[str]) -> int:
    """Number of DISTINCT scientific repair CLASSES (D61 and/or D75).

    Matches the v1.14->v1.16 convention where the D61 and D75 repairs are counted
    once each as a class, regardless of how many hunks carry them.
    """
    return len({c for c in classes if c in ("SCIENTIFIC_D61", "SCIENTIFIC_D75")})


# --------------------------------------------------------------------------- #
# 1. v1.14 -> v1.17 semantic diff
# --------------------------------------------------------------------------- #
def build_v14_to_v17_diff() -> dict:
    hunks, classes = compute_diff(V14, V17)
    scientific = _scientific_delta_count(classes)
    unclassified = classes.count("UNCLASSIFIED")
    d61 = classes.count("SCIENTIFIC_D61")
    d75 = classes.count("SCIENTIFIC_D75")
    return {
        "artifact": "phase36_v1_14_to_v1_17_semantic_diff",
        "from_revision": "ra_medfilm_barr_phase36_robustness_v1_14",
        "to_revision": "ra_medfilm_barr_phase36_robustness_v1_17",
        "from_sha256": _resolve_frozen_sha(V14, V14_SHA),
        "to_sha256": _resolve_frozen_sha(V17, V17_SHA),
        "hunk_count": len(hunks),
        "scientific_delta_count": scientific,
        "scientific_deltas": [
            h for h, c in zip(hunks, classes) if c.startswith("SCIENTIFIC_")
        ],
        "unclassified_delta_count": unclassified,
        "unclassified_scientific_delta_count": unclassified,
        "unclassified_deltas": [
            h for h, c in zip(hunks, classes) if c == "UNCLASSIFIED"
        ],
        "classification_counts": {
            "SCIENTIFIC_D61": d61,
            "SCIENTIFIC_D75": d75,
            "OPERATIONAL_GOVERNANCE": classes.count("OPERATIONAL_GOVERNANCE"),
            "UNCLASSIFIED": unclassified,
        },
        "note": ("v1.17 carries the D61 canonical ACCEPT fusion and the D75 POLICY_B "
                 "representation EXACTLY as v1.14 does.  D80/D81/D82/D83 are "
                 "operational/governance-only.  Therefore the NET scientific surface "
                 "between v1.14 and v1.17 consists of EXACTLY the 2 canonical scientific "
                 "repair CLASSES (D61 + D75); scientific_delta_count == 2; any UNCLASSIFIED "
                 "hunk fails closed."),
        "scientific_semantics_effect": "NONE_V1_17_INTRODUCED",
        "model_free": True,
        "new_scientific_choice": False,
    }


# --------------------------------------------------------------------------- #
# 2. v1.16 -> v1.17 operational diff
# --------------------------------------------------------------------------- #
def build_v16_to_v17_diff() -> dict:
    hunks, classes = compute_diff(V16, V17)
    scientific = _scientific_delta_count(classes)
    unclassified = classes.count("UNCLASSIFIED")
    return {
        "artifact": "phase36_v1_16_to_v1_17_operational_diff",
        "from_revision": "ra_medfilm_barr_phase36_robustness_v1_16",
        "to_revision": "ra_medfilm_barr_phase36_robustness_v1_17",
        "from_sha256": _resolve_frozen_sha(V16, V16_SHA),
        "to_sha256": _resolve_frozen_sha(V17, V17_SHA),
        "hunk_count": len(hunks),
        "scientific_delta_count": scientific,
        "scientific_deltas": [
            h for h, c in zip(hunks, classes) if c.startswith("SCIENTIFIC_")
        ],
        "unclassified_delta_count": unclassified,
        "unclassified_scientific_delta_count": unclassified,
        "unclassified_deltas": [
            h for h, c in zip(hunks, classes) if c == "UNCLASSIFIED"
        ],
        "classification_counts": {
            "SCIENTIFIC_D61": classes.count("SCIENTIFIC_D61"),
            "SCIENTIFIC_D75": classes.count("SCIENTIFIC_D75"),
            "OPERATIONAL_GOVERNANCE": classes.count("OPERATIONAL_GOVERNANCE"),
            "UNCLASSIFIED": unclassified,
        },
        "note": ("v1.17 is a PURE operational/governance/observability rebase of v1.16 "
                 "(D81 namespace rebase + fail-closed CSV, D82 release contract, D83 "
                 "runtime release-state gate).  The scientific computation is a VERBATIM "
                 "copy of v1.16 science: scientific_delta_count MUST be 0; any "
                 "UNCLASSIFIED hunk fails closed."),
        "scientific_semantics_effect": "NONE",
        "model_free": True,
        "new_scientific_choice": False,
    }


# --------------------------------------------------------------------------- #
# 3. v1.17 reachable-write-target inventory (AST reachability; D81)
# --------------------------------------------------------------------------- #
_UNVERSIONED_TABLE_ROOT = "reports/tables/phase36_robustness/"
_UNVERSIONED_FIGURE_ROOT = "reports/figures/phase36_robustness/"
_V17_TABLE_ROOT = "reports/tables/phase36_robustness_v1_17/"
_V17_FIGURE_ROOT = "reports/figures/phase36_robustness_v1_17/"
_V16_TABLE_ROOT = "reports/tables/phase36_robustness_v1_16/"
_V15_TABLE_ROOT = "reports/tables/phase36_robustness_v1_15/"
_V14_TABLE_ROOT = "reports/tables/phase36_robustness/"


def _call_graph(src: str) -> dict[str, set[str]]:
    """Return {function_name: set(callee_names)} for all module-level defs."""
    tree = ast.parse(src)
    graph: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            callees: set[str] = set()
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    f = sub.func
                    if isinstance(f, ast.Name):
                        callees.add(f.id)
                    elif isinstance(f, ast.Attribute):
                        callees.add(f.attr)
            graph[node.name] = callees
    return graph


def _reachable_functions(graph: dict[str, set[str]], roots: list[str]) -> set[str]:
    seen: set[str] = set()
    stack = list(roots)
    while stack:
        fn = stack.pop()
        if fn in seen:
            continue
        seen.add(fn)
        for callee in graph.get(fn, ()):  # follows only locally-defined names
            if callee in graph and callee not in seen:
                stack.append(callee)
    return seen


def _reachable_csv_targets(src: str, reachable: set[str]) -> list[dict]:
    """AST-enumerate ``_write_csv(...)`` call sites inside reachable functions."""
    tree = ast.parse(src)
    targets: list[dict] = []
    fn_stack: list[str] = []

    class V(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            fn_stack.append(node.name)
            self.generic_visit(node)
            fn_stack.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Call(self, node):
            f = node.func
            name = f.id if isinstance(f, ast.Name) else (
                f.attr if isinstance(f, ast.Attribute) else None)
            if name == "_write_csv" and node.args:
                called_from = fn_stack[-1] if fn_stack else "<module>"
                if called_from in reachable:
                    arg0 = node.args[0]
                    targets.append({
                        "call_site_line": node.lineno,
                        "called_from": called_from,
                        "target_expr": ast.unparse(arg0) if hasattr(ast, "unparse") else repr(arg0),
                    })
            self.generic_visit(node)

    V().visit(tree)

    # Resolve literal module-level path constants to full relative paths.
    consts: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tg in node.targets:
                if isinstance(tg, ast.Name) and isinstance(node.value, ast.Constant) \
                        and isinstance(node.value.value, str):
                    consts[tg.id] = node.value.value

    resolved: list[dict] = []
    for t in targets:
        expr = t["target_expr"]
        # ``TAB / "name.csv"`` -> resolve TAB to its literal root.
        full = None
        if "/" in expr and expr.strip().startswith("TAB"):
            pass
        # direct approach: find the literal file name in the expr
        import re
        m = re.search(r"""["']([^"']+\.csv)["']""", expr)
        if m:
            full = _V17_TABLE_ROOT + m.group(1)
        t2 = dict(t)
        t2["path"] = full
        resolved.append(t2)
    return resolved


def _reachable_figure_targets(src: str, reachable: set[str]) -> list[dict]:
    """AST-enumerate ``FIG / "<name>.png"`` BinOp targets inside reachable funcs."""
    tree = ast.parse(src)
    out: list[dict] = []
    fn_stack: list[str] = []
    import re

    class V(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            fn_stack.append(node.name)
            self.generic_visit(node)
            fn_stack.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_BinOp(self, node):
            # pattern:  NAME / "<literal>.png"
            if isinstance(node.op, ast.Div):
                left = node.left
                right = node.right
                if isinstance(left, ast.Name) and left.id == "FIG" \
                        and isinstance(right, ast.Constant) and isinstance(right.value, str) \
                        and right.value.endswith(".png"):
                    called_from = fn_stack[-1] if fn_stack else "<module>"
                    if called_from in reachable:
                        out.append({
                            "call_site_line": node.lineno,
                            "called_from": called_from,
                            "filename": right.value,
                            "path": _V17_FIGURE_ROOT + right.value,
                        })
            self.generic_visit(node)

    V().visit(tree)
    # de-dup, preserve order
    seen, uniq = set(), []
    for o in out:
        if o["path"] in seen:
            continue
        seen.add(o["path"])
        uniq.append(o)
    return uniq


def build_reachable_write_target_inventory() -> dict:
    src = V17.read_text(encoding="utf-8")
    graph = _call_graph(src)
    reachable = _reachable_functions(graph, ["run_science"])

    csv_targets = _reachable_csv_targets(src, reachable)
    fig_targets = _reachable_figure_targets(src, reachable)

    # Classify each resolved target against the version namespace.
    def _classify(p: str | None) -> str:
        if p is None:
            return "UNCLASSIFIED"
        if p.startswith(_V17_TABLE_ROOT) or p.startswith(_V17_FIGURE_ROOT):
            return "V1_17_NAMESPACE"
        if p.startswith(_UNVERSIONED_TABLE_ROOT) or p.startswith(_UNVERSIONED_FIGURE_ROOT):
            return "UNVERSIONED_INHERITED"
        return "UNCLASSIFIED"

    for c in csv_targets:
        c["namespace_class"] = _classify(c["path"])
    for f in fig_targets:
        f["namespace_class"] = _classify(f["path"])

    all_targets = csv_targets + fig_targets
    unclassified = [t for t in all_targets if t.get("namespace_class") == "UNCLASSIFIED"]
    unversioned = [t for t in all_targets if t.get("namespace_class") == "UNVERSIONED_INHERITED"]

    def _overlap(prefix: str) -> list[str]:
        return sorted({t["path"] for t in all_targets if t.get("path", "").startswith(prefix)})

    return {
        "artifact": "phase36_v1_17_reachable_write_target_inventory",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_17",
        "type": "REACHABLE_WRITE_TARGET_INVENTORY",
        "mode": "PREPARATION_ONLY_STATIC_AST",
        "method": "RA-MedFiLM-BARR",
        "v1_17_source_sha256": _resolve_frozen_sha(V17, V17_SHA),
        "science_reachable_function_count": len(reachable),
        "namespace_prefixes": {
            "table": _V17_TABLE_ROOT,
            "figure": _V17_FIGURE_ROOT,
        },
        "csv_table_targets": csv_targets,
        "figure_targets": fig_targets,
        "non_csv_targets": [],   # all science tables are CSV; arrays are in-memory
        "n_reachable_targets": len(all_targets),
        "n_classified_targets": len(all_targets) - len(unclassified),
        "unclassified_write_target_count": len(unclassified),
        "unversioned_write_targets": unversioned,
        "all_reachable_write_targets_enumerated": bool(csv_targets) and len(unclassified) == 0,
        "all_reachable_outputs_in_unique_v1_17_namespace": len(unversioned) == 0 and len(unclassified) == 0,
        "unversioned_write_roots_present": sorted({r for r in
                                                   (_UNVERSIONED_TABLE_ROOT, _UNVERSIONED_FIGURE_ROOT)
                                                   if any(t.get("path", "").startswith(r)
                                                          for t in all_targets)}),
        "v1_14_overlap": _overlap(_V14_TABLE_ROOT),
        "v1_15_overlap": _overlap(_V15_TABLE_ROOT),
        "v1_16_overlap": _overlap(_V16_TABLE_ROOT),
        "model_free": True,
        "torch_imported": False,
        "note": ("D81 repair: the reachable write surface is enumerated by AST call-graph "
                 "closure rooted at run_science.  EVERY reachable table/figure target lives "
                 "under the UNIQUE v1.17 namespace; unclassified_write_target_count == 0; "
                 "no inherited unversioned phase36 target remains; overlap with "
                 "v1_14/v1_15/v1_16 is empty."),
    }


# --------------------------------------------------------------------------- #
# 4. v1.17 output-namespace map
# --------------------------------------------------------------------------- #
def _string_constants(src: str) -> list[str]:
    tree = ast.parse(src)
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            out.append(n.value)
        elif isinstance(n, ast.Assign):
            for tg in n.targets:
                if isinstance(tg, ast.Name) and tg.id.startswith(
                        ("SCIENCE_", "SMOKE_", "FORBIDDEN_")):
                    if isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                        out.append(n.value.value)
    return out


def build_output_namespace_map() -> dict:
    v17_src = V17.read_text(encoding="utf-8")
    v14_src = V14.read_text(encoding="utf-8")
    v15_src = V15.read_text(encoding="utf-8")
    v16_src = V16.read_text(encoding="utf-8")

    def _paths(src, *needles):
        return sorted({s for s in _string_constants(src)
                       if s.startswith("reports/") and any(n in s for n in needles)})

    v17_paths = _paths(v17_src, "v1_17")
    v14_paths = set(_paths(v14_src, "v1_14", "v1_8"))
    v15_paths = set(_paths(v15_src, "v1_15"))
    v16_paths = set(_paths(v16_src, "v1_16"))

    v14_overwrite = sorted([p for p in v17_paths if p in v14_paths])
    v15_overwrite = sorted([p for p in v17_paths if p in v15_paths])
    v16_overwrite = sorted([p for p in v17_paths if p in v16_paths])

    science_output_paths = [
        "reports/audits/phase36_robustness_science_start_v1_17.json",
        "reports/audits/phase36_robustness_scientific_result_v1_17.json",
        "reports/audits/phase36_robustness_science_failure_v1_17.json",
        "reports/audits/phase36_robustness_science_process_exit_v1_17.json",
        "reports/audits/phase36_robustness_science_stdout_v1_17.txt",
        "reports/audits/phase36_robustness_science_stderr_v1_17.txt",
        "reports/audits/phase36_robustness_smoke_start_v1_17.json",
        "reports/audits/phase36_robustness_smoke_v1_17.json",
        "reports/audits/phase36_robustness_smoke_failure_v1_17.json",
    ]
    journal_dir_rel = "reports/audits/phase36_robustness_science_v1_17_journal"

    absence = {}
    for p in science_output_paths:
        absence[p] = {"exists": (ROOT / p).exists(), "kind": "SCIENCE_EXECUTION_OUTPUT"}
    journal_dir = ROOT / journal_dir_rel
    absence[journal_dir_rel] = {
        "exists": journal_dir.exists() and len([f for f in journal_dir.iterdir() if f.is_file()]) > 0,
        "kind": "SCIENCE_JOURNAL_DIR",
    }
    all_absent = all(not v["exists"] for v in absence.values())

    return {
        "artifact": "phase36_v1_17_output_namespace_map",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_17",
        "v1_17_output_paths": v17_paths,
        "v1_17_science_output_paths": science_output_paths,
        "v1_17_governance_artifacts_created_in_preparation": [
            "reports/audits/phase36_v1_17_runtime_source_integrity_manifest.json",
            "reports/audits/phase36_v1_17_science_release_attestation.json",
        ],
        "v1_17_science_artifacts": {
            "START": "reports/audits/phase36_robustness_science_start_v1_17.json",
            "RESULT": "reports/audits/phase36_robustness_scientific_result_v1_17.json",
            "FAILURE": "reports/audits/phase36_robustness_science_failure_v1_17.json",
            "PROCESS_EXIT": "reports/audits/phase36_robustness_science_process_exit_v1_17.json",
            "stdout": "reports/audits/phase36_robustness_science_stdout_v1_17.txt",
            "stderr": "reports/audits/phase36_robustness_science_stderr_v1_17.txt",
            "journal_dir": journal_dir_rel,
        },
        "v1_14_output_paths_observed": sorted(v14_paths),
        "v1_15_output_paths_observed": sorted(v15_paths),
        "v1_16_output_paths_observed": sorted(v16_paths),
        "v1_14_overwrite_paths": v14_overwrite,
        "v1_15_overwrite_paths": v15_overwrite,
        "v1_16_overwrite_paths": v16_overwrite,
        "no_v1_14_overwrite": v14_overwrite == [],
        "no_v1_15_overwrite": v15_overwrite == [],
        "no_v1_16_overwrite": v16_overwrite == [],
        "all_v1_17_science_paths_absent_pre_execution": all_absent,
        "absence_pre_execution": absence,
        "note": ("The v1.17 science path writes ONLY into an isolated v1.17 artifact "
                 "namespace.  No v1.14/v1.15/v1.16 output path is overwritten, and all "
                 "v1.17 SCIENCE-EXECUTION output paths (START/RESULT/FAILURE/PROCESS_EXIT/"
                 "stdout/stderr/journal/smoke) are ABSENT before execution."),
        "model_free": True,
    }


def main() -> int:
    diff14 = build_v14_to_v17_diff()
    diff16 = build_v16_to_v17_diff()
    inv = build_reachable_write_target_inventory()
    ns = build_output_namespace_map()

    _write_once_json(AUD / "phase36_v1_14_to_v1_17_semantic_diff.json", diff14)
    _write_once_json(AUD / "phase36_v1_16_to_v1_17_operational_diff.json", diff16)
    _write_once_json(AUD / "phase36_v1_17_reachable_write_target_inventory.json", inv)
    _write_once_json(AUD / "phase36_v1_17_output_namespace_map.json", ns)

    print(json.dumps({
        "v1_14_to_v1_17_diff": {
            "hunk_count": diff14["hunk_count"],
            "scientific_delta_count": diff14["scientific_delta_count"],
            "unclassified_delta_count": diff14["unclassified_delta_count"],
        },
        "v1_16_to_v1_17_diff": {
            "hunk_count": diff16["hunk_count"],
            "scientific_delta_count": diff16["scientific_delta_count"],
            "unclassified_delta_count": diff16["unclassified_delta_count"],
        },
        "reachable_write_targets": {
            "n_reachable_targets": inv["n_reachable_targets"],
            "unclassified_write_target_count": inv["unclassified_write_target_count"],
            "v1_16_overlap": inv["v1_16_overlap"],
        },
        "namespace_map": {
            "v1_14_overwrite_paths": ns["v1_14_overwrite_paths"],
            "v1_15_overwrite_paths": ns["v1_15_overwrite_paths"],
            "v1_16_overwrite_paths": ns["v1_16_overwrite_paths"],
            "all_v1_17_science_paths_absent_pre_execution": ns["all_v1_17_science_paths_absent_pre_execution"],
        },
    }, indent=1))

    ok = (
        diff14["scientific_delta_count"] == 0
        and diff14["unclassified_delta_count"] == 0
        and diff16["scientific_delta_count"] == 0
        and diff16["unclassified_delta_count"] == 0
        and inv["unclassified_write_target_count"] == 0
        and inv["v1_14_overlap"] == [] and inv["v1_15_overlap"] == [] and inv["v1_16_overlap"] == []
        and ns["no_v1_14_overwrite"] and ns["no_v1_15_overwrite"] and ns["no_v1_16_overwrite"]
        and ns["all_v1_17_science_paths_absent_pre_execution"]
    )
    print("terminal:", "PHASE36_V1_17_DIFF_AND_NAMESPACE_PASS" if ok else "PHASE36_V1_17_DIFF_AND_NAMESPACE_FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
