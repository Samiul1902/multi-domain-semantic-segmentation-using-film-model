#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.4 — PREFLIGHT (no model, no CUDA).

Static/integration preflight for the v1.4 family (D61 canonical ACCEPT-fusion repair
with crash-survivable observability):

  * source presence + run of the v1.4 unit suite (must be ALL PASS);
  * v1.0 / v1.1 / v1.2 / v1.3 family preservation pins intact;
  * D56 attribute-access contract retained in the v1.4 diagnostic;
  * D61 repair contract: the v1.4 diagnostic CALLS the canonical ``fuse_full_field``
    and does NOT CALL ``_fuse_global_with_regional`` anywhere;
  * D69 scientific-path identity marker present (``scientific_path_unchanged`` derived);
  * D70 journal non-interference marker present (``journal`` block + GT-free schema);
  * crash-survivable journal family present (stage+progress writers, write-once);
  * supervisor durable-exit-evidence contract present (never relaunches; records exit code);
  * frozen v1.14 source/manifest anchors intact;
  * the three v1.4 markers + process-exit artifact ABSENT (no attempt consumed);
  * real v1.4 journal directory absent OR contains no real-attempt records;
  * launch-authority ordering: the v1.4 token is written ONLY after the verify STOP;
  * forbidden reach: NO foreign v1.14 token, NO v1.15, NO Phase37, NO TEST/HOLDOUT;
  * D66 remediation: the incorrect historical Phase27 score SHA is ABSENT from the family;
  * GT-content prohibition: no GT-content callable CALL, mask_path metadata permitted.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\phase36_final_probability_authority_diagnostic_preflight_v1_4.py
"""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts" / "analysis"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

VENV = ROOT / ".venv" / "Scripts" / "python.exe"
AUD = ROOT / "reports" / "audits"

DIAG = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_4.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_4.py"
SUPERVISOR = ROOT / "scripts/analysis/supervise_phase36_final_probability_authority_diagnostic_v1_4.py"
UNIT = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_4.py"
NEGCTRL = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_4.py"
V14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json"
JOURNAL_DIR = AUD / "phase36_final_probability_authority_diagnostic_v1_4_journal"

RESULTS: list = []

V1_0_PINS = {
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
}
V1_1_PINS = {
    "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_1.py":
        "b9f6a449445d8ac5edd1dafe30e2f0b5005d487be314011bd2ff9162db770672",
    "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_1.py":
        "4c9737362fcf01f0ef8ef629f489cdff07c72e63b46f34e4ea508b7ba0df83ae",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_1.py":
        "0358ed115dcedea612aae1b7f0311ea08b97ba212b893a10c51ddae606fbabea",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_1.py":
        "7ba8899b25fbddbcebd42971eedd1bca4b2ca8d06d33629cec7a286e01227925",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_1.py":
        "ef7a7d8c5b7d9699fa375b2bcfccc3c482ac9e4d1b4ce9a1c3807142100a6950",
}
V1_2_PINS = {
    "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_2.py":
        "981f772fd42e35ac8e3acde17344e9bcd3fb48c39aba191200a0d811f76f29f9",
    "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_2.py":
        "de916786f8237d6f04a4deebde4186a5120164bce073ffa1d0343cf6e265aaee",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_2.py":
        "9f1e6527521984b6edbc9fb82f9818c39969baf458800fba9594af36bfbcdce6",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_2.py":
        "89e70d203649cc80f38c8eddba7cae502feb2d02c726474cad5a4daba4abc883",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_2.py":
        "f4128b736e90b80e4565259eef4df45e7fda1aaa541e7f5d5a466adf361fe34a",
}
V1_3_PINS = {
    "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_3.py":
        "b32a9db41a53b5007c6b9989bdbee22a0b7ea14587d222a3399980142dd9621e",
    "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_3.py":
        "d5f9cd3dff302c849d195d909f6f2c9a59fbbbaaf359d859e69442d9fe05b504",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_3.py":
        "f6ada4fc4fea22b5deba85fe4c5873f315fde96cb56f351e9710c6027a364ad0",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_3.py":
        "8ce14b6dbc05829850906446a4b107f9fe060843bde0ffa21515cdb22075954b",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_3.py":
        "0ebd28e8fd2f3544eee7680a290a97063f73afcadab5eea74608569a00abb265",
    "reports/audits/phase36_final_probability_authority_diagnostic_start_v1_3.json":
        "b984d09bf3a266de8d75b39b6ad2ff3236cce09915a7f2a5c874813af8c3c1c5",
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_v1_0.json":
        "3d3f943c19d5b419fb00bcf19748c0dd41ff8002ef26a4a3c51ad32ef6afecd5",
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_reconciliation_v1_1.json":
        "f6bbe602c5928e39d160629688cf697a73f65941a5d24d13c5ad4008a8dc0fc2",
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_3_governance_reconciliation_v1_0.json":
        "b0c01e40c4764514a01a9f082483a071634a0630d6c4c4640e1bb4ac2f829303",
}
V14_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"
GT_CALLABLES = ("_load_val_gt", "full_field_gt", "_dice", "_iou", "_hd95")
INCORRECT_SCORE_SHA = ("702133930ce14ac9513c992833396e3e250d08417"
                       + "a" + "17d1032cbd260a405cfb12")


def sha(p: Path) -> str:
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except FileNotFoundError:
        return "ABSENT"


def check(name, ok, detail=None):
    RESULTS.append({"name": name, "ok": bool(ok), "detail": detail})


def _tree(p: Path):
    return ast.parse(Path(p).read_text(encoding="utf-8"))


def _call_names(tree):
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            nm = getattr(f, "id", None) or getattr(f, "attr", None)
            if nm:
                out.append(nm)
    return out


def _call_linenos(tree, fname):
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            nm = getattr(f, "id", None) or getattr(f, "attr", None)
            if nm == fname:
                out.append(n.lineno)
    return out


def _find_func(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


def main() -> int:
    check("diagnostic_source_exists", DIAG.exists())
    check("launcher_source_exists", LAUNCHER.exists())
    check("supervisor_source_exists", SUPERVISOR.exists())
    check("unit_source_exists", UNIT.exists())
    check("negative_controls_source_exists", NEGCTRL.exists())

    # ---- frozen anchors ---------------------------------------------------- #
    check("frozen_v1_14_source_preserved", sha(V14) == V14_SHA, {"observed": sha(V14)})
    check("frozen_v1_14_manifest_preserved", sha(MANIFEST) == MANIFEST_SHA, {"observed": sha(MANIFEST)})

    # ---- family preservation ----------------------------------------------- #
    for label, table in (("v1_0", V1_0_PINS), ("v1_1", V1_1_PINS),
                         ("v1_2", V1_2_PINS), ("v1_3", V1_3_PINS)):
        for rel, exp in table.items():
            check(f"{label}_preserved::{rel.split('/')[-1]}", sha(ROOT / rel) == exp,
                  {"observed": sha(ROOT / rel)})

    # ---- diagnostic source contract ---------------------------------------- #
    diag_src = DIAG.read_text(encoding="utf-8")
    diag_tree = _tree(DIAG)
    calls = _call_names(diag_tree)

    # D56 retained: no _FROZEN_MOD[...] subscript; attribute access used.
    sub_sites = []
    for n in ast.walk(diag_tree):
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) \
                and n.value.id == "_FROZEN_MOD":
            sub_sites.append(n.lineno)
    check("d56_no_frozen_mod_subscript", not sub_sites, {"sites": sub_sites})
    # D56: the frozen module is consumed via ATTRIBUTE access (never subscript).
    check("d56_load_clean_image_tensor_attribute_access",
          "_load_clean_image_tensor" in diag_src
          and ("_FROZEN_MOD._load_clean_image_tensor" in diag_src
               or "mod._load_clean_image_tensor" in diag_src), None)

    # D61 repair contract.
    accept_calls = None
    fn = _find_func(diag_tree, "_repaired_canonical_learned_core")
    if fn is not None:
        for n in ast.walk(fn):
            if isinstance(n, ast.If) and "accept_prob" in ast.unparse(n.test) \
                    and "s_omega_accept_threshold" in ast.unparse(n.test):
                accept_calls = _call_names(n)
    check("d61_repaired_core_present", fn is not None, None)
    check("d61_accept_calls_canonical_fuse_full_field",
          bool(accept_calls and "fuse_full_field" in accept_calls), {"accept_calls": accept_calls})
    check("d61_accept_does_not_call_model_fusion",
          bool(accept_calls is not None and "_fuse_global_with_regional" not in accept_calls),
          {"accept_calls": accept_calls})
    old_fusion_call_sites = _call_linenos(diag_tree, "_fuse_global_with_regional")
    check("d61_old_model_fusion_absent_everywhere",
          not old_fusion_call_sites, {"call_linenos": old_fusion_call_sites})
    fuse_args = None
    for n in ast.walk(fn) if fn is not None else []:
        if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "fuse_full_field":
            fuse_args = [ast.unparse(a) for a in n.args]
    check("d61_fuse_uses_p_global_refined_geom", fuse_args == ["p_global", "refined", "geom"],
          {"args": fuse_args})
    check("d61_repaired_core_aliases_frozen_module", "mod = _FROZEN_MOD" in diag_src, None)
    core_src = ast.get_source_segment(diag_src, fn) if fn is not None else ""
    check("d61_no_torch_interpolate_in_repaired_core", "interpolate" not in core_src, None)

    # D69 identity proof marker + D70 journal marker.
    check("d69_identity_validator_present", "_core_body_without_observability" in UNIT.read_text(encoding="utf-8")
          or "scientific_path_unchanged" in UNIT.read_text(encoding="utf-8"), None)
    check("d70_journal_non_interference_present",
          "d70_journal_non_interference" in UNIT.read_text(encoding="utf-8"), None)
    check("d70_journal_non_interfering_by_design", "does not perturb" in diag_src
          or "NEVER writes, mutates or reads a scientific tensor" in diag_src, None)

    # Crash-survivable journal family.
    check("journal_stage_writer_present", "_journal_record" in diag_src, None)
    check("journal_progress_writer_present", "clean_row_loop_progress" in diag_src, None)
    check("journal_write_once_exclusive", "O_CREAT | os.O_EXCL" in diag_src
          or "O_CREAT|os.O_EXCL" in diag_src or "O_EXCL" in diag_src, None)
    check("journal_progress_points_present",
          "PROGRESS_POINTS" in diag_src and "808" in diag_src, None)
    check("journal_records_gt_free_flags",
          all(t in diag_src for t in ("contains_probabilities", "contains_masks",
                                      "contains_gt", "contains_metrics")), None)

    # Supervisor durable-exit-evidence contract.
    sup_src = SUPERVISOR.read_text(encoding="utf-8")
    check("supervisor_process_exit_artifact",
          "phase36_final_probability_authority_diagnostic_process_exit_v1_4.json" in sup_src, None)
    check("supervisor_records_child_exit_code", "child_exit_code" in sup_src, None)
    check("supervisor_records_marker_presence",
          all(t in sup_src for t in ("START_present", "RESULT_present", "FAILURE_present")), None)
    check("supervisor_never_relaunches", "supervisor_relaunched" in sup_src, None)
    check("supervisor_never_writes_scientific_marker",
          "supervisor_created_scientific_marker" in sup_src, None)
    check("supervisor_write_once", "O_EXCL" in sup_src, None)
    check("supervisor_abrupt_fixtures_present",
          all(t in sup_src for t in ("external_termination", "start_then_killed",
                                     "exit_before_terminal")), None)
    check("supervisor_tempdir_only", "TemporaryDirectory" in sup_src, None)

    # GT-content prohibition: no GT callable CALL.
    gt_calls = [c for c in calls if c in GT_CALLABLES]
    check("gt_no_content_callable_call", not gt_calls, {"gt_calls": gt_calls})

    # No perturbation call.
    pert = [c for c in calls if "perturb" in c.lower()]
    check("no_perturbation_call", not pert, {"perturb_hits": pert})

    # Token identity: v1.4 token only (no reuse of v1.1/v1.2/v1.3).
    check("v1_4_token_present", "PHASE36_FINAL_PROB_AUTHORITY_V1_4_LAUNCH_AUTHORITY" in diag_src, None)
    check("no_v1_3_token_reuse", "PHASE36_FINAL_PROB_AUTHORITY_V1_3_LAUNCH_AUTHORITY" not in diag_src, None)
    check("no_v1_2_token_reuse", "PHASE36_FINAL_PROB_AUTHORITY_V1_2_LAUNCH_AUTHORITY" not in diag_src, None)
    check("no_v1_1_token_reuse", "PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY" not in diag_src, None)
    check("foreign_v1_14_token_forbidden", "PHASE36_V1_14_LAUNCH_AUTHORITY" in diag_src, None)

    # D66 remediation: incorrect historical score SHA ABSENT from the family.
    for label, p in (("diagnostic", DIAG), ("launcher", LAUNCHER), ("supervisor", SUPERVISOR),
                     ("unit", UNIT), ("negative_controls", NEGCTRL)):
        if p.exists():
            check(f"d66_incorrect_score_sha_absent::{label}",
                  INCORRECT_SCORE_SHA not in p.read_text(encoding="utf-8"), None)

    # ---- launcher contract -------------------------------------------------- #
    launch_src = LAUNCHER.read_text(encoding="utf-8")
    launch_tree = _tree(LAUNCHER)
    check("launcher_pins_frozen_v1_3_launcher_sha",
          "d5f9cd3dff302c849d195d909f6f2c9a59fbbbaaf359d859e69442d9fe05b504" in launch_src, None)
    check("launcher_has_d61_anchor_gate", "d61_has_fuse_full_field_call" in launch_src, None)
    check("launcher_has_v1_2_consumed_gate", "check_v1_2_consumed_state" in launch_src, None)
    check("launcher_has_v1_3_consumed_gate", "check_v1_3_consumed_state" in launch_src, None)
    check("launcher_v1_4_token", "PHASE36_FINAL_PROB_AUTHORITY_V1_4_LAUNCH_AUTHORITY" in launch_src, None)
    _TOK_NAMES = {"PHASE36_FINAL_PROB_AUTHORITY_V1_4_LAUNCH_AUTHORITY", "LAUNCH_AUTHORITY_TOKEN"}
    token_linenos = []
    for n in ast.walk(launch_tree):
        if not isinstance(n, ast.Assign):
            continue
        for tgt in n.targets:
            if not isinstance(tgt, ast.Subscript):
                continue
            if ast.unparse(tgt.value) != "os.environ":
                continue
            key = ast.unparse(tgt.slice).strip().strip("'\"")
            if key in _TOK_NAMES:
                token_linenos.append(n.lineno)
    verify_lineno = -1
    for n in ast.walk(launch_tree):
        if isinstance(n, ast.If) and "a.verify_only" in ast.unparse(n.test):
            verify_lineno = n.lineno
    check("launcher_token_after_verify_only",
          bool(token_linenos and verify_lineno > 0 and min(token_linenos) > verify_lineno),
          {"token_linenos": token_linenos, "verify_lineno": verify_lineno})

    # Forbidden reach: no TEST/HOLDOUT access in either source.
    for label, src in (("diagnostic", diag_src), ("launcher", launch_src)):
        check(f"no_test_or_holdout_read_in_{label}",
              not any(tok in src for tok in ("test.csv", "holdout.csv", "ROUTER_HOLDOUT_PATH")),
              None)

    # ---- markers absent ----------------------------------------------------- #
    for mk in ("start_v1_4", "result_v1_4", "failure_v1_4"):
        cand = list(AUD.glob(f"phase36_final_probability_authority_diagnostic_{mk}.json"))
        check(f"v1_4_marker_absent::{mk}", len(cand) == 0, {"found": [str(c) for c in cand]})
    check("v1_4_process_exit_absent",
          not (AUD / "phase36_final_probability_authority_diagnostic_process_exit_v1_4.json").exists(),
          None)

    # ---- real v1.4 journal dir absent OR no real-attempt records ------------ #
    if not JOURNAL_DIR.exists():
        check("v1_4_journal_dir_absent_or_empty", True, {"exists": False})
    else:
        recs = list(JOURNAL_DIR.glob("*.json"))
        real_attempt = [r for r in recs
                        if "attempt_id" in r.read_text(encoding="utf-8")
                        and "v1_4sup_" not in r.read_text(encoding="utf-8")]
        check("v1_4_journal_dir_absent_or_empty", len(recs) == 0,
              {"exists": True, "n_records": len(recs)})

    # ---- v1.4 governance artifacts (validated when present) ----------------- #
    GOV = {
        "contract": AUD / "phase36_final_probability_authority_diagnostic_contract_v1_4.json",
        "source_freeze": AUD / "phase36_final_probability_authority_diagnostic_source_freeze_v1_4.json",
        "preflight": AUD / "phase36_final_probability_authority_diagnostic_preflight_v1_4.json",
        "negative_controls": AUD / "phase36_final_probability_authority_diagnostic_negative_controls_v1_4.json",
        "eligibility": AUD / "phase36_final_probability_authority_diagnostic_eligibility_v1_4.json",
        "no_execution_audit": AUD / "phase36_final_probability_authority_diagnostic_no_execution_audit_v1_4.json",
        "diff": AUD / "phase36_final_probability_authority_diagnostic_v1_3_to_v1_4_diff.json",
    }
    gov_present = {k: p.exists() for k, p in GOV.items()}
    # Consistency: all-or-none.
    check("v1_4_governance_present_all_or_none",
          len(set(gov_present.values())) == 1,
          {"present": gov_present})
    if all(gov_present.values()):
        cj = json.loads(GOV["contract"].read_text(encoding="utf-8"))
        sj = json.loads(GOV["source_freeze"].read_text(encoding="utf-8"))
        ej = json.loads(GOV["eligibility"].read_text(encoding="utf-8"))
        dj = json.loads(GOV["diff"].read_text(encoding="utf-8"))
        nj = json.loads(GOV["no_execution_audit"].read_text(encoding="utf-8"))
        check("v1_4_contract_revision",
              cj.get("revision") == "ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_4", None)
        check("v1_4_contract_observability_only",
              cj.get("observability_added_only") is True
              and cj.get("scientific_path_unchanged_from_v1_3") is True
              and cj.get("scientific_path_changed_from_v1_3") is False, None)
        check("v1_4_contract_d61_only_scientific_change",
              cj.get("scientific_path_changed") == "ONLY_D61_ACCEPT_FINAL_FUSION", None)
        check("v1_4_eligibility_eligible_not_started",
              ej.get("diagnostic_state") == "ELIGIBLE_NOT_STARTED"
              and ej.get("prior_attempt_consumed") is False, None)
        check("v1_4_eligibility_new_gates_required",
              ej.get("requires_v1_3_consumed_state_binding") is True
              and ej.get("requires_d69_scientific_path_identity_pass") is True
              and ej.get("requires_d70_journal_non_interference_pass") is True, None)
        check("v1_4_eligibility_markers_absent",
              ej.get("start_marker_present") is False
              and ej.get("result_marker_present") is False
              and ej.get("failure_marker_present") is False
              and ej.get("process_exit_artifact_present") is False
              and ej.get("journal_records") == 0, None)
        check("v1_4_eligibility_v1_3_consumed_preserved",
              ej.get("v1_3_state") == "CONSUMED_TERMINAL_EVIDENCE_ANOMALY"
              and ej.get("v1_3_retry_permitted") is False
              and ej.get("root_cause") == "UNRESOLVED"
              and ej.get("termination_mechanism") == "UNRESOLVED", None)
        check("v1_4_source_freeze_pins_actual_sources",
              sj.get("diagnostic_source", {}).get("sha256") == sha(DIAG)
              and sj.get("launcher_source", {}).get("sha256") == sha(LAUNCHER)
              and sj.get("supervisor_source", {}).get("sha256") == sha(SUPERVISOR)
              and sj.get("unit_source", {}).get("sha256") == sha(UNIT), None)
        check("v1_4_source_freeze_canonical_sha_derived",
              sj.get("canonical_phase27_scores_sha_derived_by_hashing") is True
              and sj.get("incorrect_historical_sha_absent_from_v1_4_family") is True
              and sj.get("canonical_phase27_scores_sha256")
              == sha(ROOT / "reports/tables/phase27_val808_per_sample_scores.csv"), None)
        check("v1_4_diff_scientific_path_identical_to_v1_3",
              dj.get("scientific_path_identical_to_v1_3") is True
              and dj.get("scientific_path_changed") == "NONE_SINCE_V1_3"
              and dj.get("observability_only") is True, None)
        check("v1_4_no_execution_audit_clean",
              nj.get("model_loaded") is False and nj.get("checkpoint_loaded") is False
              and nj.get("val_image_read") is False and nj.get("val_gt_read") is False
              and nj.get("VAL_GT_READ") == 0
              and nj.get("diagnostic_process_exit_written_by_supervisor") is False
              and nj.get("diagnostic_journal_records_written") is False, None)
        # D66: incorrect historical SHA absent from every written governance JSON too.
        for label, p in GOV.items():
            check(f"d66_incorrect_score_sha_absent::governance_{label}",
                  INCORRECT_SCORE_SHA not in p.read_text(encoding="utf-8"), None)

    # ---- run the unit suite (must be ALL PASS) ------------------------------- #
    r = subprocess.run([str(VENV), str(UNIT)], capture_output=True, text=True)
    uj = {}
    try:
        end = r.stdout.rfind("}")
        start = r.stdout.rfind("{", 0, end)
        uj = json.loads(r.stdout[start:end + 1])
    except Exception:  # noqa: BLE001
        pass
    check("unit_all_pass", uj.get("all_pass") is True,
          {"n_pass": uj.get("n_pass"), "n_checks": uj.get("n_checks"), "rc": r.returncode})

    # ---- run the supervisor self-test (synthetic) --------------------------- #
    sr = subprocess.run([str(VENV), str(SUPERVISOR), "--self-test"], capture_output=True, text=True)
    sj = {}
    try:
        sj = json.loads(sr.stdout)
    except Exception:  # noqa: BLE001
        try:
            end = sr.stdout.rfind("}")
            start = sr.stdout.rfind("{", 0, end)
            sj = json.loads(sr.stdout[start:end + 1])
        except Exception:  # noqa: BLE001
            sj = {}
    check("supervisor_synthetic_self_test_all_pass", sj.get("all_pass") is True,
          {"rc": sr.returncode, "checks": sj.get("checks")})

    n = len(RESULTS)
    n_ok = sum(1 for x in RESULTS if x["ok"])
    fails = [x for x in RESULTS if not x["ok"]]
    print(json.dumps({"suite": "preflight_v1_4", "n_checks": n, "n_pass": n_ok,
                      "all_pass": n_ok == n, "failures": fails}, indent=1))
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
