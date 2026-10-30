#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.1 — PREFLIGHT (no model, no CUDA).

Governance preflight for the ADDITIVE v1.1 repair of D52/D53/D54.  Verifies the
v1.1 family is governed and inert BEFORE any execution, and that the v1.0 source
and governance are preserved byte-for-byte:

  * frozen v1.14 tree + manifest byte-intact;
  * v1.0 diagnostic family (5 scripts + 6 governance JSONs) preserved byte-for-byte;
  * v1.1/v1.2 clean-equivalence families + D51 adjudication/reconciliation preserved;
  * v1.0 markers ABSENT and v1.1 start/result/failure markers ABSENT (never consumed);
  * launcher pin == actual diagnostic SHA;
  * D52: launcher exposes the final-authority pre-consumption gate, ordered AFTER
    transitive integrity and BEFORE the verify-only STOP / token set;
  * D53: the GT guard mutates a SHARED runtime-evidence state; the failure artifact
    records the ACTUAL VAL_GT_READ (never a hardcoded 0);
  * D54: the RESULT write is guarded and the computed-evidence terminal exists;
  * finite-probability hardening present (isfinite gate + non-finite preservation);
  * GT-content invariant wording corrected (metadata access permitted; content forbidden);
  * runtime: unit suite all-pass; launcher --verify-only authorized + non-consuming.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\phase36_final_probability_authority_diagnostic_preflight_v1_1.py
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts" / "analysis"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

VENV = ROOT / ".venv" / "Scripts" / "python.exe"
AUD = ROOT / "reports" / "audits"
DIAG = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_1.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_1.py"
UNIT = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_1.py"
NEGCTRL = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_1.py"
V14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
MANIFEST = AUD / "phase36_v1_14_runtime_source_integrity_manifest.json"

RESULTS: list = []

V14_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

# ---- v1.0 final-probability-authority family (MUST remain byte-for-byte frozen) #
V1_0_PRESERVED = {
    "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_0.py":
        "89673c6fe6a86d1abe04a5987c0675bc5c5246e24c98979bc7649431b87b319f",
    "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_0.py":
        "f77b9fd4226cc2eb7a71d84b07e06d28719d7f56fc7ef10f842005f7656ccdc6",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_0.py":
        "7cccd24cfaba2ecb243871aa44389c4f8c88b5ce782972e8d41be13e34ba5acf",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_0.py":
        "a7d13d122f8aaeb522ec213968917085aa79804caaafa7aecd835fead74591c3",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_0.py":
        "126d95548179fd5886e2687f84ca1927c60c0c30b75f6e929f211ecd4759df86",
    "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_0.py":
        "148f997b6aed291c093b7d2ecced82a7b4086c229d1da5ef4afa676a6f5cb712",
    "reports/audits/phase36_final_probability_authority_diagnostic_contract_v1_0.json":
        "378afe99342f95f47ff0cc9e06bc509190dc6b86750f5d9499be35fa1c547fe3",
    "reports/audits/phase36_final_probability_authority_diagnostic_source_freeze_v1_0.json":
        "4789b1f7499ff59318bb160757f85f7262d1014a80ba7eb208f98a1ca985d9eb",
    "reports/audits/phase36_final_probability_authority_diagnostic_preflight_v1_0.json":
        "0d47aa167775503aac3baba61052d2bcd2be76149006376fca21694ecea9f3be",
    "reports/audits/phase36_final_probability_authority_diagnostic_negative_controls_v1_0.json":
        "003fe8203004761360401e8843e2a1ba8f2869b7b0391b8a3234ceb6a8aab1b9",
    "reports/audits/phase36_final_probability_authority_diagnostic_eligibility_v1_0.json":
        "a9dd6960b3fdee3fa586bb4935f3808684ffd07e027329fb74b0513cd7ed5242",
    "reports/audits/phase36_final_probability_authority_diagnostic_no_execution_audit_v1_0.json":
        "dfa784fe050c98391dd1a47360960fb8f70063a3b5e33aee6bbf2a8a479e1a4d",
}

# ---- v1.2 / D51 provenance (consumed evidence lineage — MUST remain frozen) --- #
PROVENANCE_PRESERVED = {
    "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_0.py":
        "7cc51cceacfa314d7f84acb8a6dc482a2b46ea81de0ec695c0c8f0ca8b0b50f7",
    "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_0.py":
        "a34923faf6c27dd741ee1a1a1b4d1cbef1233664c2b02825e53b42c22c75b228",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_1.py":
        "04fa6252ff2533464553fb1a6c1f55ae009ee7ff00c1dbf89c1f901b089c839e",
    "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_1.py":
        "205dd4b877d8b6505c9479de9979087f19c341769ba2c5157a25701c212d14f6",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_negative_controls_v1_1.py":
        "b43649898d5be2fb96737f683aa208ea84d55a66ab807ac0d06e0fba4a7b3ee1",
    "reports/audits/phase36_clean_equivalence_diagnostic_start_v1_1.json":
        "59b29875838ed6117a8441f422a17fa7bdae5088fc74b2b33a38f9c92e15fa68",
    "reports/audits/phase36_clean_equivalence_diagnostic_failure_v1_1.json":
        "ef6cf75f5d8432e69b89ddbef437c24b409cb325105a11f78a4c0f0004a57343",
    "reports/audits/phase36_clean_equivalence_diagnostic_v1_1_post_run_evidence.json":
        "a33066434cf569b77563a8028e842aefeac9a360e8e9479a3852bf9f401204af",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_2.py":
        "24a638d47ddff164ec33d361ed742523f58c6cf8847d3ee9fbb02658a603d50e",
    "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_2.py":
        "1029c83b019ac76f331e528319fe2472ca5a7baac23b788c51de3297dcf7ff8e",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_2.py":
        "af9b374f89c0cbbf03c0c1f50bd107f39d549dd43289c23defc02815c4ba951f",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_preflight_v1_2.py":
        "bfa97ecf16a42ddaa51ba9f41f60a89bdf5076600d5b7bf0225b59ae5b9c6ddb",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_negative_controls_v1_2.py":
        "3551847a6a8b6d5b8ef5a0cfd0831eb4e0cf59385b146d6eb2af51981297fbbb",
    "reports/audits/phase36_clean_equivalence_diagnostic_start_v1_2.json":
        "be93d494b1aa2aad3c900f442c16efe55bcbf0bd508a72df8f8b83e72cd7d2d3",
    "reports/audits/phase36_clean_equivalence_diagnostic_result_v1_2.json":
        "b64f7e6282f9abb864a5d5bc438a22e1096aaf56e0a4e94fe53ba7c9bab6fa4a",
    "reports/audits/phase36_clean_equivalence_diagnostic_stdout_first_attempt_v1_2.txt":
        "515d56d180a0e8ba277d3f73397cd3297b21e81806c93a18be65cb5f66026380",
    "reports/audits/phase36_clean_equivalence_diagnostic_stderr_first_attempt_v1_2.txt":
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "scripts/analysis/build_phase36_clean_equivalence_d51_adjudication_v1_0.py":
        "bc88a21d27b0466de8efe791f681494df08002b33deba40606724c86335aaee0",
    "scripts/analysis/build_phase36_clean_equivalence_d51_reconciliation_v1_1.py":
        "b89609d6b2f56c8d6e92c3852938d6002f6060ec75c472799d827c8d35ab1d5c",
    "reports/audits/phase36_clean_equivalence_d51_numerical_authority_adjudication_v1_0.json":
        "27ac7ada4ee39190d8823b8b1ff7e6e2beb304e2e7fc5778542883ac7eacc53a",
    "reports/audits/phase36_clean_equivalence_d51_reconciliation_v1_1.json":
        "d8e3e83e6c31004e610faef9d93c221c026eb8974c033f47fbff91106836758b",
}

FOREIGN = "PHASE36_V1_14_LAUNCH_AUTHORITY"
GT_CALLABLES = ("_load_val_gt", "full_field_gt", "_dice", "_iou", "_hd95")
TERMINAL_RESULT_WRITE_FAILED = "TERMINAL_EVIDENCE_ANOMALY__RESULT_WRITE_FAILED_AFTER_COMPUTATION"


def sha(p: Path) -> str:
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except FileNotFoundError:
        return "ABSENT"


def check(name, ok, detail=None):
    RESULTS.append({"name": name, "ok": bool(ok), "detail": detail})


def _tree(p: Path):
    return ast.parse(Path(p).read_text(encoding="utf-8"))


def _calls(tree, fname):
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            nm = getattr(f, "id", None) or getattr(f, "attr", None)
            if nm == fname:
                out.append(n.lineno)
    return out


def _first_def_lineno(tree, fname):
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == fname:
            return n.lineno
    return -1


def _first_call_lineno_after(tree, fname, after):
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            nm = getattr(f, "id", None) or getattr(f, "attr", None)
            if nm == fname and n.lineno > after:
                return n.lineno
    return -1


def _subscript_read_keys(tree):
    keys = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Subscript):
            sl = n.slice
            if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                keys.add(sl.value)
    return keys


def main() -> int:
    check("diagnostic_source_exists", DIAG.exists())
    check("launcher_source_exists", LAUNCHER.exists())
    check("unit_source_exists", UNIT.exists())
    check("negative_controls_source_exists", NEGCTRL.exists())
    check("frozen_v1_14_source_exists", V14.exists())
    check("runtime_manifest_exists", MANIFEST.exists())

    check("frozen_v1_14_exec_sha_intact", sha(V14) == V14_SHA, {"observed": sha(V14)})
    check("frozen_v1_14_manifest_sha_intact", sha(MANIFEST) == MANIFEST_SHA, {"observed": sha(MANIFEST)})

    for p, exp in V1_0_PRESERVED.items():
        check(f"v1_0_preserved::{Path(p).name}", sha(ROOT / p) == exp, {"observed": sha(ROOT / p)})
    for p, exp in PROVENANCE_PRESERVED.items():
        check(f"provenance_preserved::{Path(p).name}", sha(ROOT / p) == exp, {"observed": sha(ROOT / p)})

    # v1.0 family markers ABSENT (never consumed)
    for m in ["start", "result", "failure"]:
        check(f"v1_0_{m}_marker_absent",
              not (AUD / f"phase36_final_probability_authority_diagnostic_{m}_v1_0.json").exists())
    # v1.1 markers ABSENT (never consumed)
    for m in ["start", "result", "failure"]:
        check(f"v1_1_{m}_marker_absent",
              not (AUD / f"phase36_final_probability_authority_diagnostic_{m}_v1_1.json").exists())

    launch_src = LAUNCHER.read_text(encoding="utf-8")
    diag_src = DIAG.read_text(encoding="utf-8")
    diag_tree = _tree(DIAG)
    launch_tree = _tree(LAUNCHER)

    # launcher pin == actual diagnostic SHA
    check("launcher_pin_matches_actual_diagnostic",
          f'FROZEN_EXPECTED_DIAGNOSTIC_SHA = "{sha(DIAG)}"' in launch_src,
          {"actual": sha(DIAG)})

    # D50: no forbidden gate call / no foreign token write
    check("D50_diagnostic_no_forbidden_gate_call",
          not _calls(diag_tree, "_verify_transitive_source_integrity"))
    check("D50_launcher_no_forbidden_gate_call",
          not _calls(launch_tree, "_verify_transitive_source_integrity"))
    check("D50_diagnostic_no_foreign_token_write",
          f'os.environ["{FOREIGN}"]' not in diag_src
          and f"os.environ['{FOREIGN}']" not in diag_src)
    check("D50_launcher_no_foreign_token_write",
          f'os.environ["{FOREIGN}"]' not in launch_src
          and f"os.environ['{FOREIGN}']" not in launch_src)
    check("D50_foreign_token_declared_absent_contract",
          f'FOREIGN_V1_14_LAUNCH_TOKEN = "{FOREIGN}"' in launch_src
          and f'FOREIGN_V1_14_LAUNCH_TOKEN = "{FOREIGN}"' in diag_src)

    # D50-C: token constants
    check("D50_c_one_shot_env", "PHASE36_FINAL_PROB_AUTHORITY_EXECUTE" in launch_src)
    check("D50_c_launch_authority_v1_1",
          'LAUNCH_AUTHORITY_TOKEN = "PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY"' in launch_src)
    check("D50_c_launch_authority_v1_1_in_diag",
          'LAUNCH_AUTHORITY_TOKEN = "PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY"' in diag_src)

    # ---- D52 — final-authority pre-consumption gate ----------------------- #
    check("D52_launcher_defines_final_authority_gate",
          _first_def_lineno(launch_tree, "check_final_authority_preconsumption") != -1)
    check("D52_launcher_reads_npy_header_only",
          "_read_npy_header" in launch_src and "mmap_mode" in launch_src)
    check("D52_launcher_pins_authority_sha",
          "PHASE27_FINAL_PROB_AUTHORITY_SHA" in launch_src)
    check("D52_launcher_pins_authority_shape_dtype",
          "PHASE27_FINAL_PROB_AUTHORITY_SHAPE" in launch_src
          and "PHASE27_FINAL_PROB_AUTHORITY_DTYPE" in launch_src)
    check("D52_launcher_pins_sample_order_authority",
          "VAL_MANIFEST_SHA" in launch_src and "PHASE27_SCORES_CSV_SHA" in launch_src
          and "final_authority_sample_order_pass" in launch_src)
    check("D52_launcher_verify_only_reports_final_authority",
          "final_authority_preconsumption_pass" in launch_src)

    # D52 stage order: transitive < final_authority < verify_only_guard < token_set
    main_def_ln = _first_def_lineno(launch_tree, "main")
    guard_ln = -1
    for n in ast.walk(launch_tree):
        if isinstance(n, ast.If) and ast.get_source_segment(launch_src, n.test) == "a.verify_only":
            guard_ln = n.lineno
            break
    ti_ln = _first_call_lineno_after(launch_tree, "check_transitive_integrity", main_def_ln)
    fa_ln = _first_call_lineno_after(launch_tree, "check_final_authority_preconsumption", main_def_ln)
    tok_ln = -1
    for n in ast.walk(launch_tree):
        if isinstance(n, ast.Assign):
            tgt = n.targets[0] if n.targets else None
            if (isinstance(tgt, ast.Subscript)
                    and ast.get_source_segment(launch_src, tgt.value) == "os.environ"
                    and ast.get_source_segment(launch_src, tgt.slice) == "LAUNCH_AUTHORITY_TOKEN"):
                tok_ln = n.lineno
    order = {"transitive": ti_ln, "final_authority": fa_ln,
             "verify_only_guard": guard_ln, "token_set": tok_ln}
    positions = [ti_ln, fa_ln, guard_ln, tok_ln]
    check("D52_stage_order_transitive_before_final_authority",
          ti_ln != -1 and fa_ln != -1 and ti_ln < fa_ln, order)
    check("D52_stage_order_final_authority_before_verify_stop",
          fa_ln != -1 and guard_ln != -1 and fa_ln < guard_ln, order)
    check("D52_stage_order_token_after_verify_stop",
          guard_ln != -1 and tok_ln != -1 and guard_ln < tok_ln, order)

    # launcher: no torch.load call
    tl = []
    for n in ast.walk(launch_tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "load":
            seg = ast.get_source_segment(launch_src, n.func) or ""
            if "torch" in seg:
                tl.append(n.lineno)
    check("D50_launcher_no_torch_load", not tl, {"lines": tl})

    # ---- D53 — shared runtime-evidence state ------------------------------ #
    gs = _first_def_lineno(diag_tree, "_install_gt_guards")
    gs_args = []
    if gs != -1:
        for n in ast.walk(diag_tree):
            if isinstance(n, ast.FunctionDef) and n.name == "_install_gt_guards":
                gs_args = [a.arg for a in n.args.args]
    check("D53_guard_takes_shared_state",
          gs != -1 and len(gs_args) >= 2 and gs_args[1] == "runtime_state", {"args": gs_args})
    check("D53_failure_reads_runtime_state_val_gt_read",
          'int(rs.get("VAL_GT_READ", 0))' in diag_src)
    check("D53_failure_records_blocked_calls",
          'list(rs.get("blocked_gt_calls", []))' in diag_src)
    # The failure payload must DERIVE VAL_GT_READ from the runtime state, never
    # hardcode a literal 0.  (A literal 0 in _new_runtime_state() is legitimate
    # as the initial counter, so scope the check to the _write_failure body.)
    _wf_seg = ""
    for n in ast.walk(diag_tree):
        if isinstance(n, ast.FunctionDef) and n.name == "_write_failure":
            _wf_seg = ast.get_source_segment(diag_src, n) or ""
    check("D53_failure_body_present", bool(_wf_seg))
    check("D53_no_hardcoded_zero_val_gt_read_in_failure",
          bool(_wf_seg) and '"VAL_GT_READ": 0' not in _wf_seg)

    # ---- D54 — computed evidence survives result-write failure ------------ #
    check("D54_terminal_defined", TERMINAL_RESULT_WRITE_FAILED in diag_src)
    check("D54_result_write_guarded",
          "result_write_attempted" in diag_src and "result_write_completed" in diag_src)
    check("D54_failure_preserves_final_authority_comparison",
          '"final_authority_comparison": rs.get("final_authority_comparison")' in diag_src)
    check("D54_failure_records_partial_result",
          "partial_result_present" in diag_src and "partial_result_sha256" in diag_src)
    check("D54_failure_does_not_delete_partial_result",
          "DIAGNOSTIC_RESULT.unlink" not in diag_src and "os.remove(str(DIAGNOSTIC_RESULT))" not in diag_src)

    # ---- finite-probability hardening ------------------------------------- #
    check("finite_helper_isfinite", "np.isfinite" in diag_src)
    check("finite_terminal_defined", "TERMINAL_NONFINITE_FINAL_PROBABILITY__FAIL_CLOSED" in diag_src)
    check("finite_records_nonfinite_samples",
          "nonfinite_samples" in diag_src and "nonfinite_final_probability" in diag_src)

    # ---- GT contract wording correction ----------------------------------- #
    check("gt_invariant_metadata_permitted",
          "mask_path_metadata_validation_permitted" in diag_src)
    check("gt_invariant_declares_content_prohibition",
          "no_Image_open_on_mask_path" in diag_src and "_load_val_gt_never_executes" in diag_src)

    # static GT prohibition
    for gtc in GT_CALLABLES:
        check(f"GT_static_no_call::{gtc}", not _calls(diag_tree, gtc))
    check("GT_static_no_mask_path_read", "mask_path" not in _subscript_read_keys(diag_tree))

    # runtime: unit + launcher verify-only
    unit_out = subprocess.run([str(VENV), str(UNIT)], capture_output=True, text=True)
    # the unit suite prints refusal JSON blocks before its results JSON; take the
    # LAST complete JSON object via a backward brace-matching scan.
    _s = unit_out.stdout
    _end = _s.rfind("}")
    _depth = 0
    _start = -1
    for _i in range(_end, -1, -1):
        _c = _s[_i]
        if _c == "}":
            _depth += 1
        elif _c == "{":
            _depth -= 1
            if _depth == 0:
                _start = _i
                break
    try:
        uj = json.loads(_s[_start:_end + 1])
    except Exception:
        uj = {}
    check("unit_all_pass", uj.get("all_pass") is True,
          {"n_pass": uj.get("n_pass"), "n_checks": uj.get("n_checks")})

    vo = subprocess.run([str(VENV), str(LAUNCHER), "--verify-only"], capture_output=True, text=True)
    try:
        vj = json.loads(vo.stdout[vo.stdout.index("{"):vo.stdout.rindex("}") + 1])
    except Exception:
        vj = {}
    check("launcher_verify_only_ok", vo.returncode == 0, {"rc": vo.returncode})
    check("launcher_verify_only_authorized", vj.get("authorized") is True)
    check("launcher_verify_only_foreign_gate_pass", vj.get("foreign_v1_14_token_absent_pass") is True)
    check("launcher_verify_only_consumed_evidence_pass", vj.get("consumed_evidence_binding_pass") is True)
    check("launcher_verify_only_v1_0_preservation_pass", vj.get("v1_0_preservation_pass") is True)
    check("launcher_verify_only_authority_exact_match",
          vj.get("source_manifest_transitive_authority_exact_match") is True)
    check("launcher_verify_only_14_4",
          vj.get("n_dependencies_verified") == 14 and vj.get("n_checkpoints_verified") == 4)
    check("launcher_verify_only_final_authority_pass",
          vj.get("final_authority_preconsumption_pass") is True)
    check("launcher_verify_only_final_authority_sha",
          vj.get("final_authority_sha256")
          == "506ab6c4e715a9106889e186c146b73903493c80a63258007954cf5deb3ea9cf")
    check("launcher_verify_only_final_authority_shape",
          vj.get("final_authority_shape") == [808, 512, 512])
    check("launcher_verify_only_final_authority_dtype",
          vj.get("final_authority_dtype") == "float16")
    check("launcher_verify_only_final_authority_sample_order",
          vj.get("final_authority_sample_order_pass") is True)
    check("launcher_verify_only_dispatch_suppressed",
          str(vj.get("terminal", "")).endswith("DISPATCH_SUPPRESSED_BY_VERIFY_ONLY"))
    for m in ["start", "result", "failure"]:
        check(f"verify_only_non_consuming::{m}",
              not (AUD / f"phase36_final_probability_authority_diagnostic_{m}_v1_1.json").exists())

    check("one_shot_gate_unset_in_process", os.environ.get("PHASE36_FINAL_PROB_AUTHORITY_EXECUTE") != "1")
    check("foreign_token_unset_in_process", os.environ.get(FOREIGN) != "1")

    n_ok = sum(1 for r in RESULTS if r["ok"])
    n = len(RESULTS)
    print(json.dumps({"artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_V1_1_PREFLIGHT_RESULTS",
                      "n_checks": n, "n_pass": n_ok, "all_pass": n_ok == n,
                      "results": RESULTS}, indent=1))
    print(f"\n=== PREFLIGHT v1.1 (final-prob authority): {n_ok}/{n} pass")
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
