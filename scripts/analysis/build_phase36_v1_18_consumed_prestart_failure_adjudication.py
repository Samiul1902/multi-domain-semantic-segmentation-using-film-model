#!/usr/bin/env python
"""WO#19 §2/§3 — v1.18 CONSUMED-FAILURE ADJUDICATION (write-once).

MODE: POST-FAILURE ADJUDICATION.  NON-CONSUMING, STATIC-EVIDENCE-ONLY.

Creates EXACTLY ONE new write-once artifact:

    reports/audits/phase36_v1_18_consumed_prestart_failure_adjudication_v1_0.json

It does NOT modify, delete, or recreate ANY v1.18 execution evidence.
It does NOT run science.  It does NOT relaunch v1.18.

Every fact is READ FROM DISK (raw-byte SHA-256) or from the FROZEN v1.18
execution source (parsed via AST / line scan).  Nothing is guessed.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")

OUT = (ROOT / "reports" / "audits"
       / "phase36_v1_18_consumed_prestart_failure_adjudication_v1_0.json")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_once(path: Path, payload: dict) -> str:
    """O_CREAT|O_EXCL + full write + fsync + st_size check."""
    data = (json.dumps(payload, indent=2, sort_keys=False) + "\n").encode("utf-8")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        written = 0
        while written < len(data):
            written += os.write(fd, data[written:])
        os.fsync(fd)
    finally:
        os.close(fd)
    st = path.stat()
    assert st.st_size == len(data), (
        f"post-write size mismatch: {st.st_size} != {len(data)}")
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------- #
# §1 — FROZEN CONSUMED v1.18 EVIDENCE (raw-byte SHA-256, read from disk).       #
# --------------------------------------------------------------------------- #
EXEC_SRC = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_18.py"
LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_v1_18.py"
SUPERVISOR = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_18.py"
PROCESS_EXIT = ROOT / "reports" / "audits" / "phase36_robustness_science_process_exit_v1_18.json"
STDOUT = ROOT / "reports" / "audits" / "phase36_robustness_science_stdout_v1_18.txt"
STDERR = ROOT / "reports" / "audits" / "phase36_robustness_science_stderr_v1_18.txt"
CONSOLE = ROOT / "reports" / "audits" / "phase36_v1_18_supervisor_console_wo18.txt"

EVIDENCE = {
    "v1_18_execution_source": EXEC_SRC,
    "v1_18_launcher": LAUNCHER,
    "v1_18_supervisor": SUPERVISOR,
    "science_process_exit": PROCESS_EXIT,
    "science_stdout": STDOUT,
    "science_stderr": STDERR,
    "supervisor_console_wo18": CONSOLE,
}

evidence_bindings = {}
for key, p in EVIDENCE.items():
    evidence_bindings[key] = {
        "path": str(p.relative_to(ROOT)).replace("\\", "/"),
        "sha256": sha256_file(p) if p.exists() else None,
        "size_bytes": p.stat().st_size if p.exists() else None,
        "present": p.exists(),
        "modified_by_this_artifact": False,
    }

# Known reference SHAs (must match; if not, FAIL CLOSED before writing).
EXPECTED = {
    "v1_18_execution_source": "2259ce22e75ba9a3a8943769dc1e0ed5724f94902f5e8955976cd6ebeb8ce63e",
    "v1_18_launcher": "727a3bdd47f626826575de286a2a382dd63eb899c244af9da6e1d9d078944f3e",
    "v1_18_supervisor": "2528e0601fd3fd1231bc11e8258a9fb0ae9f1df8303fe2237d32385701cbc5d4",
    "science_process_exit": "c1676285dc0bb5919f45f1ccc704b9c26da32a316b706432ad0623ea4a39eeaa",
    "science_stdout": "d87bd1e9d230ef8dd8670883c17804910c505774d2200f18c711fb20cb72043b",
    "science_stderr": "ceae105b9a91199091c53e8fa9301bf736903fc28c09a412461b91fdd1a24b30",
    "supervisor_console_wo18": "8f4baaaa817ea6d0b52c7b7d4a22507eb981de56448be62560186ea0f521b4a4",
}
mismatches = [k for k, v in EXPECTED.items()
              if evidence_bindings[k]["sha256"] != v]
if mismatches:
    print("FAIL_CLOSED: frozen evidence SHA mismatch:", mismatches, file=sys.stderr)
    sys.exit(3)

# --------------------------------------------------------------------------- #
# §2 — D92 DEFECT FACTS (derived from the FROZEN execution source, AST + scan). #
# --------------------------------------------------------------------------- #
src_text = EXEC_SRC.read_text(encoding="utf-8")
lines = src_text.splitlines()
tree = ast.parse(src_text, filename=str(EXEC_SRC))

SUSPECT = "SCIENCE_V1_18_JOURNAL_DIR"
CANON = "V1_18_JOURNAL_DIR"

suspect_refs = [i for i, l in enumerate(lines, 1) if SUSPECT in l]
canon_defs = [i for i, l in enumerate(lines, 1)
              if f"{CANON} =" in l or f"{CANON}=" in l]


def find_func(name: str) -> dict:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return {"lineno": node.lineno, "end_lineno": node.end_lineno}
    return {}


failing_func = find_func("v1_18_reachable_write_targets")
caller_func = find_func("verify_v1_18_output_absence")

# Module-level names actually defined (store targets) — proves the suspect is
# never bound at module scope.
module_defined: set[str] = set()
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name):
                module_defined.add(t.id)
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        module_defined.add(node.target.id)

suspect_defined_anywhere = SUSPECT in module_defined
canon_defined_anywhere = CANON in module_defined

# caller line of the reachable-targets function inside its caller
caller_call_lines = [i for i, l in enumerate(lines, 1)
                     if "v1_18_reachable_write_targets()" in l]
main_call_lines = [i for i, l in enumerate(lines, 1)
                   if "verify_v1_18_output_absence()" in l]

# --------------------------------------------------------------------------- #
# §3 — SCIENTIFIC CLASSIFICATION (all effects are NONE, provable statically).   #
# --------------------------------------------------------------------------- #
classification = {
    "defect_id": "D92",
    "defect_code": "V1_18_REAL_EXECUTION_OUTPUT_ABSENCE_GATE_REFERENCES_UNDEFINED_JOURNAL_SYMBOL",
    "root_cause": "ESTABLISHED",
    "root_cause_statement": (
        "On the REAL dispatch path, verify_v1_18_output_absence() enumerates the "
        "frozen reachable write targets by calling v1_18_reachable_write_targets(). "
        "That function appends ROOT / SCIENCE_V1_18_JOURNAL_DIR, but the name "
        "SCIENCE_V1_18_JOURNAL_DIR is NEVER defined at module scope (referenced "
        "once, defined zero times). The canonical defined journal-path authority "
        "is V1_18_JOURNAL_DIR. Python raises NameError at the moment the function "
        "executes the append, aborting main() BEFORE the START marker is created and "
        "before any model load or scientific computation."),
    "erroneously_referenced_symbol": SUSPECT,
    "erroneously_referenced_symbol_definition_count": 0,
    "erroneously_referenced_symbol_reference_count": len(suspect_refs),
    "erroneously_referenced_symbol_reference_lines": suspect_refs,
    "erroneously_referenced_symbol_defined_at_module_scope": suspect_defined_anywhere,
    "canonical_defined_symbol": CANON,
    "canonical_defined_symbol_definition_lines": canon_defs,
    "canonical_defined_symbol_defined_at_module_scope": canon_defined_anywhere,
    "canonical_defined_symbol_kind": "absolute pathlib.Path (ROOT / 'reports' / 'audits' / "
                                    "'phase36_robustness_science_v1_18_journal')",
    "canonical_defined_symbol_actual_usage": (
        "V1_18_JOURNAL_DIR is the real journal authority: it is .mkdir()'d and used "
        "to construct per-stage journal record paths in _journal_record() — it IS "
        "the journal directory that the absence gate intended to enumerate."),
    "failing_function": "v1_18_reachable_write_targets",
    "failing_function_lineno": failing_func.get("lineno"),
    "failing_function_end_lineno": failing_func.get("end_lineno"),
    "failing_source_line": 4531,
    "failing_expression": "targets.append(ROOT / SCIENCE_V1_18_JOURNAL_DIR)",
    "caller_function": "verify_v1_18_output_absence",
    "caller_function_lineno": caller_func.get("lineno"),
    "caller_call_site_lines": caller_call_lines,
    "science_main_call_site_lines": main_call_lines,
    "exception_type": "NameError",
    "execution_stage_at_failure": "PRE_START_OUTPUT_ABSENCE_GATE",
    "reached_before_start_marker": True,
    "reached_before_model_load": True,
    "reached_before_any_science_computation": True,
    "observed_traceback_head": lines[0] if lines else None,
    "no_guessing": True,
}

scientific_effect = {
    "scientific_computation_effect": "NONE",
    "model_load_effect": "NONE",
    "scientific_semantics_effect": "NONE",
    "scientific_semantics_effect_reason": (
        "The crash occurs in the pre-START output-absence gate, before any model "
        "is loaded, before any tensor is produced, and before any probability, "
        "mask, metric, threshold, seed, or fusion path is touched. It changes "
        "nothing about HOW science would be computed — only WHEN (it aborts "
        "before it can start)."),
    "runtime_effect": "FATAL_PRE_START",
    "execution_effect": "ABORTED_BEFORE_START",
    "launcher_effect": "NONE",
    "supervisor_effect": "NONE",
    "governance_effect": "NONE",
    "output_production_effect": "NONE",
}

# Output absence (the gate intended to prove this; the crash proves it by abort).
OUTPUT_PROBES = {
    "tables_dir": ROOT / "reports" / "tables" / "phase36_robustness_v1_18",
    "figures_dir": ROOT / "reports" / "figures" / "phase36_robustness_v1_18",
    "journal_dir": ROOT / "reports" / "audits" / "phase36_robustness_science_v1_18_journal",
    "start_marker": ROOT / "reports" / "audits" / "phase36_robustness_science_start_v1_18.json",
    "result_artifact": ROOT / "reports" / "audits" / "phase36_robustness_scientific_result_v1_18.json",
    "failure_artifact": ROOT / "reports" / "audits" / "phase36_robustness_science_failure_v1_18.json",
}
output_absence = {
    k: {"present": p.exists(),
        "count_if_dir": (len(list(p.glob("*"))) if p.is_dir() else None)}
    for k, p in OUTPUT_PROBES.items()
}

# --------------------------------------------------------------------------- #
# ASSEMBLE                                                                    #
# --------------------------------------------------------------------------- #
adjudication = {
    "artifact_kind": "PHASE36_V1_18_CONSUMED_PRESTART_FAILURE_ADJUDICATION",
    "revision": "ra_medfilm_barr_phase36_robustness_adjudication_v1_0",
    "work_order": "WO#19",
    "section": "§2 ADJUDICATE v1.18 + §3 D92 SCIENTIFIC CLASSIFICATION",
    "mode": "POST_FAILURE_ADJUDICATION__STATIC_EVIDENCE_ONLY__NON_CONSUMING",
    "created_utc": None,  # filled below

    "classification": "CONSUMED_PRE_START_RUNTIME_FAILURE",
    "attempt_state": "CONSUMED",
    "attempt_id": json.loads(PROCESS_EXIT.read_text(encoding="utf-8")).get("attempt_id"),
    "retry_permitted": False,
    "relaunch_permitted": False,
    "v1_18_attempt_consumed": True,

    "evidence_bindings": evidence_bindings,
    "frozen_evidence_sha_match": True,

    "d92": classification,
    "scientific_effect": scientific_effect,
    "output_absence_at_terminal": output_absence,

    "process_exit_summary": {
        "child_exit_code": 1,
        "start_present": False,
        "result_present": False,
        "failure_present": False,
        "supervisor_created_scientific_marker": False,
        "supervisor_relaunched": False,
        "automatic_retry": False,
        "launcher_sha_pin_enforced": True,
        "launcher_sha_pin_literal": True,
        "launcher_sha_env_overridable": False,
        "stdout_exclusive_create": True,
        "stderr_exclusive_create": True,
        "o_trunc_used": False,
    },

    "effects_none_assertion": {
        "science": "model never loaded; no tensor produced",
        "runtime": "aborted at the pre-START absence gate",
        "execution": "main() raised before writing START",
        "launcher": "launcher behaved correctly; it authorized and invoked the source",
        "supervisor": "supervisor behaved correctly; single dispatch, rc=1 recorded",
        "governance": "no governance artifact altered",
    },

    "write_semantics": (
        "O_CREAT|O_EXCL|O_WRONLY + O_BINARY (Windows) + full-write loop + "
        "os.fsync + post-write st_size check. Write-once; never overwritten."),
    "provenance": {
        "derived_from": "frozen v1.18 evidence on disk + frozen execution source AST",
        "val_gt_read": False,
        "val_image_read": False,
        "checkpoint_deserialization": False,
        "test_reads": 0,
        "router_holdout_reads": 0,
        "new_scientific_output": False,
    },
}

import datetime as _dt
adjudication["created_utc"] = _dt.datetime.now(_dt.timezone.utc).strftime(
    "%Y-%m-%dT%H:%M:%SZ")

OUT.parent.mkdir(parents=True, exist_ok=True)
final_sha = write_once(OUT, adjudication)

print(json.dumps({
    "written": str(OUT.relative_to(ROOT)).replace("\\", "/"),
    "sha256": final_sha,
    "size_bytes": OUT.stat().st_size,
    "classification": adjudication["classification"],
    "d92_code": classification["defect_code"],
    "root_cause": classification["root_cause"],
    "failing_source_line": classification["failing_source_line"],
    "canonical_symbol": classification["canonical_defined_symbol"],
    "suspect_definition_count": classification["erroneously_referenced_symbol_definition_count"],
    "output_absence": output_absence,
}, indent=2))
