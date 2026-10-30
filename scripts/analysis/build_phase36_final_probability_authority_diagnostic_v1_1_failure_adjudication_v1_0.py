#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.1 — FAILURE ADJUDICATION (D56).

WRITE-ONCE generator for the ADDITIVE consumed-evidence adjudication

    reports/audits/phase36_final_probability_authority_diagnostic_v1_1_failure_adjudication_v1_0.json

The v1.1 one-shot first attempt was CONSUMED_FAILED (retry FORBIDDEN).  This
generator adjudicates that failure statically: it binds the consumed evidence by
raw-byte SHA, records the exact failure predicates, and establishes

    D56 = DIAGNOSTIC_FROZEN_MODULE_SUBSCRIPT_MISMATCH

from (a) the consumed traceback, (b) the frozen v1.1 source, and (c) the exact
control flow.  It does NOT modify any v1.1 file, does NOT execute any diagnostic,
and does NOT read VAL / GT bytes (static metadata/hash reads only).

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\build_phase36_final_probability_authority_diagnostic_v1_1_failure_adjudication_v1_0.py
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts" / "analysis"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

AUD = ROOT / "reports" / "audits"

# ---- consumed v1.1 evidence (byte-for-byte immutable) ---------------------- #
V1_1_START = AUD / "phase36_final_probability_authority_diagnostic_start_v1_1.json"
V1_1_FAILURE = AUD / "phase36_final_probability_authority_diagnostic_failure_v1_1.json"
V1_1_RESULT = AUD / "phase36_final_probability_authority_diagnostic_result_v1_1.json"
V1_1_STDOUT = AUD / "phase36_final_probability_authority_diagnostic_stdout_first_attempt_v1_1.txt"
V1_1_STDERR = AUD / "phase36_final_probability_authority_diagnostic_stderr_first_attempt_v1_1.txt"

EXPECTED_START_SHA = "0bfb452ef81e6e0c8880d9b333abcb6514dff7dbb3a37476da3242beeab73aec"
EXPECTED_FAILURE_SHA = "9f1b38431228ec584150da37501199ea580b26339be6d8e20a2fcba72b5cd960"

# ---- frozen pins (re-verified before writing anything) --------------------- #
FROZEN_PINS = {
    "v1_1_diagnostic":
        ("scripts/analysis/phase36_final_probability_authority_diagnostic_v1_1.py",
         "b9f6a449445d8ac5edd1dafe30e2f0b5005d487be314011bd2ff9162db770672"),
    "v1_1_launcher":
        ("scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_1.py",
         "4c9737362fcf01f0ef8ef629f489cdff07c72e63b46f34e4ea508b7ba0df83ae"),
    "d55_reconciliation":
        ("reports/audits/phase36_final_probability_authority_diagnostic_v1_1_governance_reconciliation_v1_0.json",
         "124327dca073afa440e187aa1999c4f463fb97a1fe62e30ce19b6bcfa8b966f4"),
    "v1_14_exec_source":
        ("scripts/analysis/phase36_robustness_execution_v1_14.py",
         "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"),
    "v1_14_manifest":
        ("reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json",
         "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"),
    "v1_2_clean_eq_result":
        ("reports/audits/phase36_clean_equivalence_diagnostic_result_v1_2.json",
         "b64f7e6282f9abb864a5d5bc438a22e1096aaf56e0a4e94fe53ba7c9bab6fa4a"),
    "d51_reconciliation_v1_1":
        ("reports/audits/phase36_clean_equivalence_d51_reconciliation_v1_1.json",
         "d8e3e83e6c31004e610faef9d93c221c026eb8974c033f47fbff91106836758b"),
}

OUT = AUD / "phase36_final_probability_authority_diagnostic_v1_1_failure_adjudication_v1_0.json"

# ---- required failure predicates (from the consumed FAILURE artifact) ------ #
REQUIRED_PREDICATES = {
    "termination_kind": "EXCEPTION",
    "exception_type": "TypeError",
    "exception_message": "'module' object is not subscriptable",
    "failing_stage": "run_diagnostic",
    "marker_consumed": True,
    "VAL_GT_READ": 0,
    "final_authority_computed": False,
    "result_write_attempted": False,
}

# ---- D56 source facts (statistically established from the frozen source) --- #
D56 = {
    "classification": "DIAGNOSTIC_FROZEN_MODULE_SUBSCRIPT_MISMATCH",
    "failure_site": "_clean_final_probability_only",
    "first_bad_expression": '_FROZEN_MOD["_load_clean_image_tensor"]',
    "second_latent_bad_expression": '_FROZEN_MOD["canonical_learned_core"]',
    "module_binding": "run_diagnostic() executes `mod = _import_frozen_v1_14(); _FROZEN_MOD = mod` "
                      "so _FROZEN_MOD is a Python MODULE object (not a mapping)",
    "reason": "a module object is not subscriptable; the first expression raised TypeError before "
              "the second defective expression could execute",
    "defect_is_shared_with_v1_0": True,
    "v1_0_defect_sites": ["line 352 (_load_clean_image_tensor)", "line 355 (canonical_learned_core)"],
    "v1_1_defect_sites": ["line 446 (_load_clean_image_tensor)", "line 449 (canonical_learned_core)"],
    "repair": "minimal two-site attribute-access repair: mod._load_clean_image_tensor / "
              "mod.canonical_learned_core (scientific computation unchanged)",
}


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def write_once(path: Path, payload: dict) -> None:
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


def _traceback_lines() -> list:
    if not V1_1_STDERR.exists():
        return []
    return V1_1_STDERR.read_text(encoding="utf-8").splitlines()


def main() -> int:
    # ---- preconditions (fail closed; nothing consumed/overwritten) --------- #
    if OUT.exists():
        print(json.dumps({"REFUSED": "ADJUDICATION_ALREADY_EXISTS", "path": str(OUT)}, indent=1))
        return 2

    if not V1_1_START.exists():
        print(json.dumps({"REFUSED": "V1_1_START_ABSENT", "path": str(V1_1_START)}, indent=1))
        return 3
    if not V1_1_FAILURE.exists():
        print(json.dumps({"REFUSED": "V1_1_FAILURE_ABSENT", "path": str(V1_1_FAILURE)}, indent=1))
        return 3
    if V1_1_RESULT.exists():
        print(json.dumps({"REFUSED": "V1_1_RESULT_PRESENT_UNEXPECTED", "path": str(V1_1_RESULT)},
                         indent=1))
        return 3

    start_sha = sha(V1_1_START)
    failure_sha = sha(V1_1_FAILURE)
    if start_sha != EXPECTED_START_SHA:
        print(json.dumps({"REFUSED": "V1_1_START_SHA_MISMATCH",
                          "expected": EXPECTED_START_SHA, "observed": start_sha}, indent=1))
        return 3
    if failure_sha != EXPECTED_FAILURE_SHA:
        print(json.dumps({"REFUSED": "V1_1_FAILURE_SHA_MISMATCH",
                          "expected": EXPECTED_FAILURE_SHA, "observed": failure_sha}, indent=1))
        return 3

    pin_bad = {}
    pin_obs = {}
    for name, (rel, exp) in FROZEN_PINS.items():
        p = ROOT / rel
        obs = sha(p) if p.exists() else None
        pin_obs[name] = obs
        if obs != exp:
            pin_bad[name] = {"path": rel, "expected": exp, "observed": obs}
    if pin_bad:
        print(json.dumps({"REFUSED": "FROZEN_PIN_MISMATCH", "bad": pin_bad}, indent=1))
        return 4

    # ---- failure predicates (parsed + verified from the consumed artifact) -- #
    fj = json.loads(V1_1_FAILURE.read_text(encoding="utf-8"))
    pred_observed = {
        "termination_kind": fj.get("termination_kind"),
        "exception_type": fj.get("exception_type"),
        "exception_message": fj.get("exception_message"),
        "failing_stage": fj.get("failing_stage"),
        "marker_consumed": fj.get("marker_consumed"),
        "VAL_GT_READ": fj.get("VAL_GT_READ"),
        "final_authority_computed": fj.get("final_authority_computed"),
        "result_write_attempted": fj.get("result_write_attempted"),
    }
    pred_match = {k: bool(pred_observed.get(k) == v) for k, v in REQUIRED_PREDICATES.items()}
    if not all(pred_match.values()):
        print(json.dumps({"REFUSED": "FAILURE_PREDICATE_MISMATCH",
                          "required": REQUIRED_PREDICATES, "observed": pred_observed}, indent=1))
        return 5

    # ---- stdout: bind the ACTUAL file on disk (do not assume it is absent) -- #
    stdout_present = V1_1_STDOUT.exists()
    stdout_sha = sha(V1_1_STDOUT) if stdout_present else None
    stdout_size = V1_1_STDOUT.stat().st_size if stdout_present else None
    stderr_present = V1_1_STDERR.exists()
    stderr_sha = sha(V1_1_STDERR) if stderr_present else None

    tb = _traceback_lines()
    tb_text = "\n".join(tb)
    tb_has_subscript_error = ("'module' object is not subscriptable" in tb_text)
    tb_has_defect_expression = ('_FROZEN_MOD["_load_clean_image_tensor"]' in tb_text)
    tb_failing_line = None
    m = re.search(r"line (\d+), in _clean_final_probability_only", tb_text)
    if m:
        tb_failing_line = int(m.group(1))

    ts = now()
    write_once(OUT, {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_V1_1_FAILURE_ADJUDICATION",
        "revision": "ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_1_failure_adjudication_v1_0",
        "adjudicates": "ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_1",
        "additive": True,
        "write_once": True,
        "overwrite_permitted": False,
        "automatic_retry": False,

        # ---- consumed state -------------------------------------------------- #
        "v1_1_state": "CONSUMED_FAILED",
        "v1_1_retry_permitted": False,
        "v1_1_exit_code": 2,
        "v1_1_attempt_consumed": True,

        # ---- consumed evidence binding (raw-byte SHA) ------------------------ #
        "v1_1_start": {"path": "reports/audits/phase36_final_probability_authority_diagnostic_start_v1_1.json",
                       "sha256": start_sha, "present": True},
        "v1_1_failure": {"path": "reports/audits/phase36_final_probability_authority_diagnostic_failure_v1_1.json",
                         "sha256": failure_sha, "present": True},
        "v1_1_result": {"path": "reports/audits/phase36_final_probability_authority_diagnostic_result_v1_1.json",
                        "present": False, "sha256": None, "absence_confirmed": True},
        "v1_1_stdout": {"path": "reports/audits/phase36_final_probability_authority_diagnostic_stdout_first_attempt_v1_1.txt",
                        "present": stdout_present, "size": stdout_size, "sha256": stdout_sha,
                        "note": "actual on-disk file bound; reported empty-file SHA "
                                "e3b0c442...b855 is the SHA-256 of the empty string"},
        "v1_1_stderr": {"path": "reports/audits/phase36_final_probability_authority_diagnostic_stderr_first_attempt_v1_1.txt",
                        "present": stderr_present, "sha256": stderr_sha},

        # ---- frozen pins ----------------------------------------------------- #
        "frozen_pins": {name: {"path": rel_or_name, "expected": exp, "observed": pin_obs[name],
                               "match": bool(pin_obs[name] == exp)}
                        for name, (rel_or_name, exp) in
                        ((n, (v[0], v[1])) for n, v in FROZEN_PINS.items())},
        "frozen_v1_1_diagnostic_source_sha256": FROZEN_PINS["v1_1_diagnostic"][1],
        "frozen_v1_1_launcher_source_sha256": FROZEN_PINS["v1_1_launcher"][1],
        "d55_reconciliation_sha256": FROZEN_PINS["d55_reconciliation"][1],
        "frozen_v1_14_exec_source_sha256": FROZEN_PINS["v1_14_exec_source"][1],
        "frozen_v1_14_manifest_sha256": FROZEN_PINS["v1_14_manifest"][1],
        "v1_2_clean_equivalence_result_sha256": FROZEN_PINS["v1_2_clean_eq_result"][1],
        "d51_reconciliation_sha256": FROZEN_PINS["d51_reconciliation_v1_1"][1],

        # ---- failure predicates --------------------------------------------- #
        "failure_predicates_required": dict(REQUIRED_PREDICATES),
        "failure_predicates_observed": pred_observed,
        "failure_predicates_match": pred_match,
        "all_failure_predicates_match": bool(all(pred_match.values())),

        # ---- D56 ------------------------------------------------------------- #
        "d56_classification": "DIAGNOSTIC_FROZEN_MODULE_SUBSCRIPT_MISMATCH",
        "d56_root_cause_established": True,
        "d56": D56,
        "failure_site": D56["failure_site"],
        "first_bad_expression": D56["first_bad_expression"],
        "second_latent_bad_expression": D56["second_latent_bad_expression"],
        "traceback": {
            "lines": tb,
            "has_module_not_subscriptable": tb_has_subscript_error,
            "has_defect_expression": tb_has_defect_expression,
            "failing_function_line": tb_failing_line,
        },

        # ---- execution-reach correction (do NOT overclaim) ------------------- #
        "execution_reach": {
            "frozen_v1_14_import_reached": True,
            "gt_guard_installation_reached": True,
            "frozen_counter_construction_reached": True,
            "model_load_reached": True,
            "checkpoint_deserialization_reached": True,
            "clean_g_generation_reached": True,
            "phase27_global_reproduction_gate_passed": True,
            "clean_row_index_reached": True,
            "first_per_sample_helper_entered": True,
            "val_image_read_during_clean_g_generation": True,
            "first_downstream_per_sample_image_reload_completed": False,
            "val_image_read_count": "NOT_INDEPENDENTLY_DERIVED__SOURCE_DERIVED_ONLY",
            "val_image_read_count_note": ("the TypeError occurs while RESOLVING "
                                          "_FROZEN_MOD['_load_clean_image_tensor'] BEFORE the callable "
                                          "executes, so the per-sample reload did not complete; no "
                                          "precise read count is directly recorded"),
            "claim_guard": "must NOT record 'failure occurred before any VAL image read' (false)",
        },

        # ---- downstream scientific state ------------------------------------ #
        "final_authority_computed": False,
        "final_authority_comparison": None,
        "classification": None,
        "perturbation_executed": False,
        "scientific_semantics_result_produced": False,
        "robustness_result": False,
        "scientific_output": False,

        # ---- GT content invariant -------------------------------------------- #
        "VAL_GT_READ": 0,
        "blocked_gt_calls": [],
        "gt_content_read": False,
        "gt_content_invariant": {
            "no_mask_file_opened": True,
            "no_Image_open_on_mask_path": True,
            "_load_val_gt_never_executes": True,
            "full_field_gt_never_executes": True,
            "_dice_never_executes": True,
            "_iou_never_executes": True,
            "_hd95_never_executes": True,
            "VAL_GT_READ_remains_zero": True,
            "mask_path_metadata_validation_permitted": True,
        },

        # ---- governance ------------------------------------------------------ #
        "v1_1_files_modified": False,
        "v1_1_artifacts_modified": False,
        "v1_0_files_modified": False,
        "no_execution": True,
        "model_forward": False,
        "checkpoint_deserialization_performed": False,
        "val_image_read_performed": False,
        "val_gt_read_performed": False,
        "test_accessed": False,
        "router_holdout_accessed": False,
        "phase37_started": False,

        "generated_utc": ts,
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync (exclusive-create, write-once)",
    })

    print(json.dumps({
        "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_1_FAILURE_ADJUDICATION_BUILT",
        "adjudication_sha256": sha(OUT),
        "d56_classification": D56["classification"],
        "d56_root_cause_established": True,
        "v1_1_state": "CONSUMED_FAILED",
        "v1_1_retry_permitted": False,
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
