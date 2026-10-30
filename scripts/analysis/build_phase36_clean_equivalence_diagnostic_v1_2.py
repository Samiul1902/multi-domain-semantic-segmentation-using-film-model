#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the Phase36 CLEAN EQUIVALENCE DIAGNOSTIC v1.2 D50 governance artifacts.

NO EXECUTION of the diagnostic.  This builder only
(a) hashes source files,
(b) runs the UNIT / PREFLIGHT / NEGATIVE-CONTROL validators (all no-model),
(c) runs the launcher ``--verify-only`` (non-consuming),
(d) binds the CONSUMED v1.1 failure evidence and the adjudication of D50,
(e) writes the governance artifacts with write-once semantics.

Artifacts (all under reports/audits/):
    phase36_clean_equivalence_diagnostic_contract_v1_2.json
    phase36_clean_equivalence_diagnostic_source_freeze_v1_2.json
    phase36_clean_equivalence_diagnostic_preflight_v1_2.json
    phase36_clean_equivalence_diagnostic_negative_controls_v1_2.json
    phase36_clean_equivalence_diagnostic_eligibility_v1_2.json
    phase36_clean_equivalence_diagnostic_no_execution_audit_v1_2.json
    phase36_clean_equivalence_diagnostic_v1_1_failure_adjudication.json
    phase36_clean_equivalence_diagnostic_v1_1_to_v1_2_diff.json
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
VENV = ROOT / ".venv" / "Scripts" / "python.exe"
AUD = ROOT / "reports" / "audits"

DIAG = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_2.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_2.py"
UNIT = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_2.py"
PREFLIGHT = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_preflight_v1_2.py"
NEGCTRL = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_negative_controls_v1_2.py"

DIAG_V10 = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_0.py"
LAUNCHER_V10 = ROOT / "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_0.py"
UNIT_V10 = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_0.py"
PREFLIGHT_V10 = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_preflight_v1_0.py"

DIAG_V11 = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_1.py"
LAUNCHER_V11 = ROOT / "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_1.py"
UNIT_V11 = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_1.py"
PREFLIGHT_V11 = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_preflight_v1_1.py"
NEGCTRL_V11 = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_negative_controls_v1_1.py"

V14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json"
STATIC_AUDIT = AUD / "phase36_clean_equivalence_targeted_static_audit_v1_0.json"
RECON_V2 = AUD / "phase36_v1_14_science_failure_forensic_reconciliation_v2.json"

V14_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

V10_SHAS = {
    "diagnostic": "7cc51cceacfa314d7f84acb8a6dc482a2b46ea81de0ec695c0c8f0ca8b0b50f7",
    "launcher": "a34923faf6c27dd741ee1a1a1b4d1cbef1233664c2b02825e53b42c22c75b228",
    "unit": "33e72386699aa0100c314846ffe2592f740ca7fb76e926a704cf4d46fbf78bf5",
    "preflight": "92c2d855e931d037e965d862a2ce0feb091d53e1bff0f91020f85729842e6653",
}

V11_SHAS = {
    "diagnostic": "04fa6252ff2533464553fb1a6c1f55ae009ee7ff00c1dbf89c1f901b089c839e",
    "launcher": "205dd4b877d8b6505c9479de9979087f19c341769ba2c5157a25701c212d14f6",
    "unit": "89190b297e7bc4e2868f7bb52fc46d836e6866317403523e8bbf0d167bc50aee",
    "preflight": "3634a3f4314fb5712d958cda2effc3b3027257663692b51b3b4176b258fab529",
    "negative_controls": "b43649898d5be2fb96737f683aa208ea84d55a66ab807ac0d06e0fba4a7b3ee1",
}

# CONSUMED v1.1 failure evidence (write-once, byte-preserved)
V11_EVIDENCE = {
    "start": ("reports/audits/phase36_clean_equivalence_diagnostic_start_v1_1.json",
              "59b29875838ed6117a8441f422a17fa7bdae5088fc74b2b33a38f9c92e15fa68", 3046),
    "failure": ("reports/audits/phase36_clean_equivalence_diagnostic_failure_v1_1.json",
                "ef6cf75f5d8432e69b89ddbef437c24b409cb325105a11f78a4c0f0004a57343", 5955),
    "stdout": ("reports/audits/phase36_clean_equivalence_diagnostic_stdout_first_attempt_v1_1.txt",
               "af71235b6cbc6237ce1c1e2246342e261c38765a702b78eaf3d84b7793f44b04", 10278),
    "stderr": ("reports/audits/phase36_clean_equivalence_diagnostic_stderr_first_attempt_v1_1.txt",
               "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", 0),
    "post_run_evidence": ("reports/audits/phase36_clean_equivalence_diagnostic_v1_1_post_run_evidence.json",
                          "a33066434cf569b77563a8028e842aefeac9a360e8e9479a3852bf9f401204af", 2397),
}

PRIOR_PINS = {
    "v1_14_science_start": ("reports/audits/phase36_robustness_science_start_v1_14.json",
                            "e2c42b05f4fd0450022d7bcde091c0bea13638788b4f83a123016ab894630e0a"),
    "v1_14_science_failure": ("reports/audits/phase36_robustness_science_failure_v1_14.json",
                              "0fcc3c211d7bcd53b4f8e53d7b09f518fd83a929e8a979c7174762958fff754b"),
    "v1_14_forensic_adjudication": ("reports/audits/phase36_v1_14_science_failure_forensic_adjudication.json",
                                    "f1d4712ae7b3f0b333a22c852f99d6b3812218ffb258f8f58ddba62c7193c17e"),
    "forensic_reconciliation_v2": ("reports/audits/phase36_v1_14_science_failure_forensic_reconciliation_v2.json",
                                   "cc9a3b502f59e3855c395b9d6afa2f5616f513d60af4756e4477a9370889cc3c"),
    "targeted_static_audit": ("reports/audits/phase36_clean_equivalence_targeted_static_audit_v1_0.json",
                              "8def086c44a7e80461c729f41ab61c0be347ef1589c94d6884a082adbde64ed4"),
}
REQUIRED_STATIC_AUDIT_VERDICT = "STATIC_ROOT_CAUSE_NOT_ESTABLISHED"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def write_once(path: Path, payload: dict) -> str:
    if path.exists():
        raise SystemExit(f"REFUSE_OVERWRITE::{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=1, ensure_ascii=False, default=str).encode("utf-8")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    fd = os.open(str(path), flags, 0o644)
    try:
        total = 0
        while total < len(data):
            n = os.write(fd, data[total:])
            if not n:
                raise OSError("SHORT_WRITE")
            total += n
        os.fsync(fd)
    finally:
        os.close(fd)
    return sha(path)


def _extract_summary(txt: str, kind: str) -> dict:
    marker = f'"artifact_kind": "{kind}"'
    i = txt.find(marker)
    if i < 0:
        return {}
    i = txt.rfind("{", 0, i)
    dec = json.JSONDecoder()
    try:
        obj, _ = dec.raw_decode(txt[i:])
        return obj
    except Exception:
        return {}


def run_summary(script: Path, kind: str, extra_env=None) -> dict:
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    out = subprocess.run([str(VENV), str(script)], capture_output=True, text=True, env=env)
    return {"returncode": out.returncode,
            "summary": _extract_summary(out.stdout, kind),
            "stderr_tail": out.stderr[-800:]}


# --------------------------------------------------------------------------- #
# Hash sources
# --------------------------------------------------------------------------- #
diag_sha = sha(DIAG)
launcher_sha = sha(LAUNCHER)
unit_sha = sha(UNIT)
preflight_sha = sha(PREFLIGHT)
negctrl_sha = sha(NEGCTRL)

v10_preserved = {
    "diagnostic": sha(DIAG_V10) == V10_SHAS["diagnostic"],
    "launcher": sha(LAUNCHER_V10) == V10_SHAS["launcher"],
    "unit": sha(UNIT_V10) == V10_SHAS["unit"],
    "preflight": sha(PREFLIGHT_V10) == V10_SHAS["preflight"],
}
assert all(v10_preserved.values()), f"v1.0 NOT preserved: {v10_preserved}"

v11_preserved = {
    "diagnostic": sha(DIAG_V11) == V11_SHAS["diagnostic"],
    "launcher": sha(LAUNCHER_V11) == V11_SHAS["launcher"],
    "unit": sha(UNIT_V11) == V11_SHAS["unit"],
    "preflight": sha(PREFLIGHT_V11) == V11_SHAS["preflight"],
    "negative_controls": sha(NEGCTRL_V11) == V11_SHAS["negative_controls"],
}
assert all(v11_preserved.values()), f"v1.1 NOT preserved: {v11_preserved}"

# launcher pins must equal the actual SHAs
_launcher_src = LAUNCHER.read_text(encoding="utf-8")
_diag_pin_ok = f'FROZEN_EXPECTED_DIAGNOSTIC_SHA = "{diag_sha}"' in _launcher_src
_v14_pin_ok = f'FROZEN_EXPECTED_V1_14_EXEC_SHA = "{V14_SHA}"' in _launcher_src
_manifest_pin_ok = f'FROZEN_EXPECTED_V1_14_MANIFEST_SHA = "{MANIFEST_SHA}"' in _launcher_src
assert _diag_pin_ok, "launcher diagnostic SHA pin != actual diagnostic SHA"
assert _v14_pin_ok, "launcher v1.14 exec SHA pin != expected"
assert _manifest_pin_ok, "launcher manifest SHA pin != expected"

# --------------------------------------------------------------------------- #
# v1.1 CONSUMED failure evidence binding
# --------------------------------------------------------------------------- #
v11_evidence = {}
for name, (rel, exp_sha, exp_len) in V11_EVIDENCE.items():
    p = ROOT / rel
    present = p.exists()
    obs_sha = sha(p) if present else None
    v11_evidence[name] = {
        "path": rel, "present": present, "expected_sha256": exp_sha,
        "observed_sha256": obs_sha, "expected_bytes": exp_len,
        "observed_bytes": (p.stat().st_size if present else None),
        "match": bool(present and obs_sha == exp_sha),
    }
assert all(v["match"] for v in v11_evidence.values()), f"v1.1 evidence NOT intact: {v11_evidence}"

v11_result_absent = not (AUD / "phase36_clean_equivalence_diagnostic_result_v1_1.json").exists()
assert v11_result_absent, "v1.1 RESULT artifact unexpectedly PRESENT"

_v11_fail = json.loads((ROOT / V11_EVIDENCE["failure"][0]).read_text(encoding="utf-8"))
v11_failure_facts = {
    "terminal_artifact": "FAILURE",
    "artifact_kind": _v11_fail.get("artifact_kind"),
    "termination_kind": _v11_fail.get("termination_kind"),
    "exception_type": _v11_fail.get("exception_type"),
    "failing_stage": _v11_fail.get("failing_stage"),
    "marker_consumed": _v11_fail.get("marker_consumed"),
    "clean_equivalence_computed": _v11_fail.get("clean_equivalence_computed"),
    "clean_equivalence_full_is_none": _v11_fail.get("clean_equivalence_full") is None,
    "automatic_retry": _v11_fail.get("automatic_retry"),
    "overwrite_permitted": _v11_fail.get("overwrite_permitted"),
    "robustness_result": _v11_fail.get("robustness_result"),
    "perturbation_executed": _v11_fail.get("perturbation_executed"),
    "scientific_output": _v11_fail.get("scientific_output"),
    # derived prohibitions. The durable v1.1 failure artifact asserts the
    # POSITIVE absence facts: no robustness result, no perturbation, no science.
    # `model_loaded`, `checkpoint_deserialized` and `val_image_or_gt_read` are
    # therefore FALSE (not performed before the pre-model governance failure).
    "model_loaded": False,
    "checkpoint_deserialized": False,
    "val_image_or_gt_read": False,
    "retry_forbidden": _v11_fail.get("automatic_retry") is False,
}
assert v11_failure_facts["artifact_kind"] == "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_FAILURE", v11_failure_facts
assert v11_failure_facts["termination_kind"] == "SYSTEM_EXIT", v11_failure_facts
assert v11_failure_facts["marker_consumed"] is True, v11_failure_facts
assert v11_failure_facts["clean_equivalence_computed"] is False, v11_failure_facts
assert v11_failure_facts["clean_equivalence_full_is_none"] is True, v11_failure_facts
assert v11_failure_facts["robustness_result"] is False, v11_failure_facts
assert v11_failure_facts["perturbation_executed"] is False, v11_failure_facts
assert v11_failure_facts["scientific_output"] is False, v11_failure_facts
assert v11_failure_facts["automatic_retry"] is False, v11_failure_facts
assert v11_failure_facts["model_loaded"] is False, v11_failure_facts
assert v11_failure_facts["checkpoint_deserialized"] is False, v11_failure_facts
assert v11_failure_facts["val_image_or_gt_read"] is False, v11_failure_facts
assert v11_failure_facts["retry_forbidden"] is True, v11_failure_facts

# v1.2 attempt artifacts must be ABSENT
v12_markers = {
    "start": (AUD / "phase36_clean_equivalence_diagnostic_start_v1_2.json").exists(),
    "result": (AUD / "phase36_clean_equivalence_diagnostic_result_v1_2.json").exists(),
    "failure": (AUD / "phase36_clean_equivalence_diagnostic_failure_v1_2.json").exists(),
}
assert not any(v12_markers.values()), f"v1.2 DIAGNOSTIC MARKERS PRESENT: {v12_markers}"

# --------------------------------------------------------------------------- #
# Run the validators (no model) + launcher verify-only (non-consuming)
# --------------------------------------------------------------------------- #
unit_run = run_summary(UNIT, "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_UNIT_RESULTS")
pf_run = run_summary(PREFLIGHT, "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_PREFLIGHT_RESULTS")
nc_run = run_summary(NEGCTRL, "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_NEGATIVE_CONTROL_RESULTS")

_v = subprocess.run([str(VENV), str(LAUNCHER), "--verify-only"], capture_output=True, text=True)
try:
    verify_res = json.loads(_v.stdout[_v.stdout.index("{"):_v.stdout.rindex("}") + 1])
except Exception:
    verify_res = {"raw_tail": _v.stdout[-800:], "returncode": _v.returncode}

unit_res = unit_run.get("summary", {})
pf_res = pf_run.get("summary", {})
nc_res = nc_run.get("summary", {})

assert unit_res.get("all_pass") is True, f"unit not all_pass: {unit_res}"
assert pf_res.get("all_pass") is True, f"preflight not all_pass: {pf_res}"
assert nc_res.get("all_pass") is True, f"negative controls not all_pass: {nc_res}"
assert verify_res.get("authorized") is True, f"verify-only not authorized: {verify_res}"
assert verify_res.get("foreign_v1_14_token_absent_pass") is True, verify_res
assert verify_res.get("source_manifest_transitive_authority_exact_match") is True, verify_res

prior_state = {}
for name, (rel, exp) in PRIOR_PINS.items():
    p = ROOT / rel
    prior_state[name] = {"path": rel, "present": p.exists(),
                         "expected": exp, "observed": (sha(p) if p.exists() else None),
                         "match": bool(p.exists() and sha(p) == exp)}
static_verdict = json.loads(STATIC_AUDIT.read_text(encoding="utf-8")).get("root_cause_static_verdict")

D50_REASON = "FROZEN_V1_14_GATE_CONTAINS_FOREIGN_LAUNCH_AUTHORITY_SEMANTICS"

# --------------------------------------------------------------------------- #
# CONTRACT
# --------------------------------------------------------------------------- #
contract = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_CONTRACT",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_2",
    "supersedes": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_1",
    "additive_revision": True,
    "v1_0_preserved_byte_for_byte": all(v10_preserved.values()),
    "v1_1_preserved_byte_for_byte": all(v11_preserved.values()),
    "purpose": (
        "ADDITIVE D50 repair of the durable clean-equivalence diagnostic. v1.1 was "
        "CONSUMED/FAILED because the frozen v1.14 _verify_transitive_source_integrity() "
        "requires the FOREIGN launch-authority token PHASE36_V1_14_LAUNCH_AUTHORITY=1. "
        "v1.2 performs the exact PRE-CONSUMPTION byte-integrity proof ITSELF (including "
        "exact set+SHA equality against the frozen v1.14 DECLARED authority maps), NEVER "
        "masquerades as the v1.14 launcher, and calls ONLY the clean-equivalence steps "
        "(omitting the frozen foreign-token gate)."),
    "repaired_defects": {
        "D50": {
            "title": D50_REASON,
            "detail": ("the frozen v1.14 gate couples diagnostic execution to a v1.14 "
                       "launch-authority token; v1.2 removes the coupling by (A) doing the "
                       "transitive integrity proof itself pre-consumption, (B) forbidding the "
                       "foreign token in both launcher and source, (C) using a diagnostic-native "
                       "authority pair, (D) invoking only the clean steps, (E) preserving all "
                       "eq fields."),
            "sub_repairs": {
                "D50-A": "launcher performs the exact pre-consumption byte-integrity proof "
                         "(frozen v1.14 exec SHA, manifest SHA, execution_source_sha256 == "
                         "frozen v1.14 source SHA, launcher_sha256 ABSENT, exactly 14 deps, "
                         "exactly 4 ckpts, every dep/ckpt raw-byte SHA, and EXACT set+SHA "
                         "equality between the frozen v1.14 DECLARED maps and the pinned "
                         "manifest) BEFORE launch authority / start marker; NO torch.load / "
                         "model construction / ckpt deserialization / VAL/GT.",
                "D50-B": "neither launcher nor source may EVER set "
                         "PHASE36_V1_14_LAUNCH_AUTHORITY; both REQUIRE it absent before "
                         "dispatch, else FAIL CLOSED.",
                "D50-C": "diagnostic-native authority ONLY: "
                         "PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE=1 AND "
                         "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_LAUNCH_AUTHORITY=1; order: execute "
                         "gate -> prior-attempt absence -> v1.2 launch authority -> prior-failure "
                         "provenance -> consumed-v1.1 binding -> start marker -> clean computation.",
                "D50-D": "after the marker, import frozen v1.14 by exact SHA and call ONLY "
                         "_load_models / _bind_clean_reference / _generate_clean_g_reference / "
                         "_phase27_global_reproduction_gate / _clean_row_index / "
                         "808 x _evaluate_clean_sample / _clean_equivalence_gate; NEVER "
                         "_verify_transitive_source_integrity.",
                "D50-E": "preserve D47 durable full-eq write with ALL original fields plus "
                         "d50_foreign_gate_call_omitted / d50_reason / "
                         "foreign_v1_14_launch_token_present=false / "
                         "preconsumption_transitive_integrity_pass=true / "
                         "source_manifest_transitive_authority_exact_match=true.",
            },
            "status": "REPAIRED",
        },
    },
    "one_shot_gate_env": "PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE=1",
    "launch_authority_token_env": "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_LAUNCH_AUTHORITY=1",
    "forbidden_foreign_token_env": "PHASE36_V1_14_LAUNCH_AUTHORITY",
    "d50_foreign_gate_call_omitted": True,
    "d50_reason": D50_REASON,
    "required_authorization_order": [
        "(0) foreign v1.14 launch-authority token ABSENT (fail closed if present)",
        "(1) one-shot execute gate",
        "(2) prior-attempt absence (start/result/failure v1.2)",
        "(3) diagnostic-native v1.2 launch-authority token",
        "(4) preserved prior-failure provenance gate",
        "(5) consumed-v1.1 failure binding",
        "(6) start marker (authorized_attempt DERIVED)",
        "(7) guarded execution + durable result (D47/D50-E)",
    ],
    "execution_scope": "CLEAN_ONLY__STEPS_1_THROUGH_7__NO_PERTURBATION",
    "diagnostic_steps": [
        "STEP1 _build_counters (mod.C.COUNTERS_REQUIRED / COUNTERS_FOREVER_ZERO)",
        "STEP2 _load_models (CUDA fail-closed, no CPU fallback)",
        "STEP3 _bind_clean_reference (authority bind)",
        "STEP4 _generate_clean_g_reference (canonical batched CLEAN G pass)",
        "STEP5 _phase27_global_reproduction_gate (STOP on fail)",
        "STEP6 808 x _evaluate_clean_sample (clean system eval)",
        "STEP7 eq = _clean_equivalence_gate (DURABLE full-eq write)",
        "STEP8 write result artifact (write-once, INSIDE guarded region)",
        "STEP9 terminate (no perturbation)",
        "OMITTED _verify_transitive_source_integrity (D50-D: foreign-token coupled)",
    ],
    "imports_frozen_callables_from": "scripts/analysis/phase36_robustness_execution_v1_14.py",
    "frozen_v1_14_exec_source_sha256": V14_SHA,
    "frozen_v1_14_runtime_manifest_sha256": MANIFEST_SHA,
    "artifacts_written": [
        "reports/audits/phase36_clean_equivalence_diagnostic_start_v1_2.json",
        "reports/audits/phase36_clean_equivalence_diagnostic_result_v1_2.json",
        "reports/audits/phase36_clean_equivalence_diagnostic_failure_v1_2.json",
    ],
    "artifacts_never_written": [
        "reports/audits/phase36_robustness_science_start_v1_14.json",
        "reports/audits/phase36_robustness_scientific_result_v1_14.json",
        "reports/audits/phase36_robustness_science_failure_v1_14.json",
    ],
    "result_artifact_required_eq_fields": [
        "all_pass", "checks", "n_generated", "n_bound", "n_dice_comparisons",
        "n_state_machine_branch_comparisons", "n_router_decision_comparisons",
        "missing_generated_dice", "missing_bound_dice", "dice_mismatches",
        "route_branch_mismatches", "router_decision_mismatches",
        "max_abs_dice_deviation", "dice_comparator", "branch_comparator",
        "router_decision_comparator", "accept_reject_collapse_prohibited",
        "fail_closed_on_missing_data",
    ],
    "result_artifact_required_d50_fields": [
        "d50_foreign_gate_call_omitted", "d50_reason",
        "foreign_v1_14_launch_token_present",
        "preconsumption_transitive_integrity_pass",
        "source_manifest_transitive_authority_exact_match",
    ],
    "failure_artifact_required_fields": [
        "termination_kind", "exception_type", "exception_message", "failing_stage",
        "clean_equivalence_computed", "clean_equivalence_full",
        "automatic_retry", "overwrite_permitted", "scientific_output",
    ],
    "consumed_v1_1_binding_required": {
        "terminal_artifact": "FAILURE",
        "clean_equivalence_computed": False,
        "model_loaded": False,
        "checkpoint_deserialized": False,
        "val_image_or_gt_read": False,
        "retry_forbidden": True,
    },
    "prior_failure_provenance_required_verdict": REQUIRED_STATIC_AUDIT_VERDICT,
    "prior_failure_provenance_pins": {k: v[1] for k, v in PRIOR_PINS.items()},
    "prohibitions": [
        "no v1.15", "no v1.14 modification", "no Phase37", "no TEST", "no ROUTER_HOLDOUT",
        "no VAL808 re-consumption beyond the diagnostic's frozen clean reproduction",
        "no perturbation execution", "no automatic retry", "scientific_output=false",
        "no checkpoint deserialization at launcher",
        "no PHASE36_V1_14_LAUNCH_AUTHORITY write by launcher or source",
        "no _verify_transitive_source_integrity call by launcher or source",
    ],
    "source_sha256": {
        "diagnostic": diag_sha,
        "launcher": launcher_sha,
        "unit": unit_sha,
        "preflight": preflight_sha,
        "negative_controls": negctrl_sha,
    },
    "v1_0_source_sha256": V10_SHAS,
    "v1_1_source_sha256": V11_SHAS,
    "scientific_output": False,
    "generated_utc": now(),
}

# --------------------------------------------------------------------------- #
# SOURCE FREEZE
# --------------------------------------------------------------------------- #
freeze = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_SOURCE_FREEZE",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_2",
    "diagnostic_source": {"path": str(DIAG.relative_to(ROOT)), "sha256": diag_sha},
    "launcher_source": {"path": str(LAUNCHER.relative_to(ROOT)), "sha256": launcher_sha},
    "unit_source": {"path": str(UNIT.relative_to(ROOT)), "sha256": unit_sha},
    "preflight_source": {"path": str(PREFLIGHT.relative_to(ROOT)), "sha256": preflight_sha},
    "negative_controls_source": {"path": str(NEGCTRL.relative_to(ROOT)), "sha256": negctrl_sha},
    "v1_0_preservation": {
        "diagnostic": {"path": str(DIAG_V10.relative_to(ROOT)), "expected": V10_SHAS["diagnostic"],
                       "observed": sha(DIAG_V10), "preserved": v10_preserved["diagnostic"]},
        "launcher": {"path": str(LAUNCHER_V10.relative_to(ROOT)), "expected": V10_SHAS["launcher"],
                     "observed": sha(LAUNCHER_V10), "preserved": v10_preserved["launcher"]},
        "unit": {"path": str(UNIT_V10.relative_to(ROOT)), "expected": V10_SHAS["unit"],
                 "observed": sha(UNIT_V10), "preserved": v10_preserved["unit"]},
        "preflight": {"path": str(PREFLIGHT_V10.relative_to(ROOT)), "expected": V10_SHAS["preflight"],
                      "observed": sha(PREFLIGHT_V10), "preserved": v10_preserved["preflight"]},
    },
    "v1_1_preservation": {
        "diagnostic": {"path": str(DIAG_V11.relative_to(ROOT)), "expected": V11_SHAS["diagnostic"],
                       "observed": sha(DIAG_V11), "preserved": v11_preserved["diagnostic"]},
        "launcher": {"path": str(LAUNCHER_V11.relative_to(ROOT)), "expected": V11_SHAS["launcher"],
                     "observed": sha(LAUNCHER_V11), "preserved": v11_preserved["launcher"]},
        "unit": {"path": str(UNIT_V11.relative_to(ROOT)), "expected": V11_SHAS["unit"],
                 "observed": sha(UNIT_V11), "preserved": v11_preserved["unit"]},
        "preflight": {"path": str(PREFLIGHT_V11.relative_to(ROOT)), "expected": V11_SHAS["preflight"],
                      "observed": sha(PREFLIGHT_V11), "preserved": v11_preserved["preflight"]},
        "negative_controls": {"path": str(NEGCTRL_V11.relative_to(ROOT)),
                              "expected": V11_SHAS["negative_controls"],
                              "observed": sha(NEGCTRL_V11),
                              "preserved": v11_preserved["negative_controls"]},
    },
    "frozen_ancestors": {
        "v1_14_execution": {"path": str(V14.relative_to(ROOT)), "sha256": sha(V14), "expected": V14_SHA},
        "v1_14_runtime_manifest": {"path": str(MANIFEST.relative_to(ROOT)), "sha256": sha(MANIFEST),
                                   "expected": MANIFEST_SHA},
    },
    "launcher_pinned_diagnostic_sha": diag_sha,
    "launcher_pinned_v1_14_exec_sha": V14_SHA,
    "launcher_pinned_v1_14_manifest_sha": MANIFEST_SHA,
    "launcher_pin_matches_actual_diagnostic": _diag_pin_ok,
    "launcher_pin_matches_v1_14_exec": _v14_pin_ok,
    "launcher_pin_matches_v1_14_manifest": _manifest_pin_ok,
    "non_circularity": ("launcher pins diagnostic + v1.14 exec + manifest; manifest declares "
                        "v1.14 exec only; no launcher_sha256 in manifest"),
    "scientific_output": False,
    "generated_utc": now(),
}

# --------------------------------------------------------------------------- #
# PREFLIGHT
# --------------------------------------------------------------------------- #
preflight = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_PREFLIGHT",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_2",
    "unit_run": {"returncode": unit_run.get("returncode"),
                 "n_checks": unit_res.get("n_checks"), "n_pass": unit_res.get("n_pass"),
                 "all_pass": unit_res.get("all_pass")},
    "preflight_run": {"returncode": pf_run.get("returncode"),
                      "n_checks": pf_res.get("n_checks"), "n_pass": pf_res.get("n_pass"),
                      "all_pass": pf_res.get("all_pass")},
    "negative_controls_run": {"returncode": nc_run.get("returncode"),
                              "n_checks": nc_res.get("n_checks"), "n_pass": nc_res.get("n_pass"),
                              "all_pass": nc_res.get("all_pass")},
    "launcher_verify_only": {
        "terminal": verify_res.get("terminal"),
        "authorized": verify_res.get("authorized"),
        "interpreter_pass": verify_res.get("interpreter_pass"),
        "cuda_readiness_pass": verify_res.get("cuda_readiness_pass"),
        "foreign_v1_14_token_absent_pass": verify_res.get("foreign_v1_14_token_absent_pass"),
        "prior_failure_provenance_pass": verify_res.get("prior_failure_provenance_pass"),
        "consumed_v1_1_failure_binding_pass": verify_res.get("consumed_v1_1_failure_binding_pass"),
        "transitive_integrity_pass": verify_res.get("transitive_integrity_pass"),
        "source_manifest_transitive_authority_exact_match":
            verify_res.get("source_manifest_transitive_authority_exact_match"),
        "n_dependencies_verified": verify_res.get("n_dependencies_verified"),
        "n_checkpoints_verified": verify_res.get("n_checkpoints_verified"),
        "dispatch_suppressed": bool(str(verify_res.get("terminal", "")).endswith(
            "DISPATCH_SUPPRESSED_BY_VERIFY_ONLY")),
        "one_shot_gate_set_during_verify": verify_res.get("one_shot_gate_set"),
    },
    "frozen_v1_14_anchors_intact": {
        "v1_14_exec": sha(V14) == V14_SHA,
        "v1_14_manifest": sha(MANIFEST) == MANIFEST_SHA,
    },
    "prior_failure_provenance": prior_state,
    "static_audit_verdict": static_verdict,
    "static_audit_verdict_matches_required": static_verdict == REQUIRED_STATIC_AUDIT_VERDICT,
    "prior_diagnostic_attempt": any(v12_markers.values()),
    "v1_0_preserved": v10_preserved,
    "v1_1_preserved": v11_preserved,
    "scientific_output": False,
    "generated_utc": now(),
}

# --------------------------------------------------------------------------- #
# NEGATIVE CONTROLS (summary artifact)
# --------------------------------------------------------------------------- #
negctrl = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_NEGATIVE_CONTROLS",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_2",
    "source": {"path": str(NEGCTRL.relative_to(ROOT)), "sha256": negctrl_sha},
    "headline_control": {
        "statement": ("direct invocation with PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE=1 but "
                      "WITHOUT the diagnostic-native v1.2 launch-authority token fails CLOSED; "
                      "and PRESENCE of the foreign PHASE36_V1_14_LAUNCH_AUTHORITY token also "
                      "fails CLOSED without consuming the attempt"),
        "exit_code_expected_no_launch_authority": 5,
        "exit_code_expected_foreign_token_present": 8,
        "control_names": [
            "HEADLINE_launcher_foreign_gate_refuses",
            "HEADLINE_launcher_refuses_with_foreign_token",
            "HEADLINE_launcher_terminal_foreign_fail_closed",
            "HEADLINE_no_marker_after_launcher_foreign_refusal",
            "HEADLINE_diagnostic_refuses_with_foreign_token",
            "HEADLINE_no_marker_after_diagnostic_foreign_refusal",
        ],
    },
    "d50_mutation_sensitive_controls": [
        "REQ1_no_forbidden_gate_call_diag",
        "REQ1_no_forbidden_gate_call_launch",
        "REQ2_diag_no_foreign_token_write",
        "REQ2_launch_no_foreign_token_write",
        "REQ2_mutant_foreign_token_write_detected",
        "REQ3_gate_ok_when_absent",
        "REQ3_gate_refuses_when_present",
        "REQ4_exact_authority_match",
        "REQ4_set_equal_deps",
        "REQ4_set_equal_ckpts",
        "REQ5_dep_removal_detected",
        "REQ6_ckpt_removal_detected",
        "REQ7_dep_sha_mutation_detected",
        "REQ8_ckpt_sha_mutation_detected",
        "REQ9_launcher_sha_key_detected",
        "REQ10_source_mutation_detected",
        "REQ10a_source_map_tamper_detected_via_exact_match",
        "REQ11_v1_1_binding_ok_on_real_tree",
        "REQ11_v1_1_failure_mutation_detected",
        "REQ11_prior_failure_mutation_detected",
        "REQ12_no_execute_gate_rc3",
        "REQ12_no_launch_authority_rc5",
        "REQ12_no_marker_after_refusals",
        "REQ13_result_write_guarded",
        "REQ14_full_eq_written",
    ],
    "n_checks": nc_res.get("n_checks"), "n_pass": nc_res.get("n_pass"),
    "all_pass": nc_res.get("all_pass"),
    "results": nc_res.get("results"),
    "scientific_output": False,
    "generated_utc": now(),
}

# --------------------------------------------------------------------------- #
# ELIGIBILITY
# --------------------------------------------------------------------------- #
eligibility = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_ELIGIBILITY",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_2",
    "diagnostic_state": "ELIGIBLE_NOT_STARTED",
    "one_shot": True,
    "automatic_retry": False,
    "requires_env": "PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE=1",
    "requires_launch_authority": True,
    "launch_authority_token_env": "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_LAUNCH_AUTHORITY",
    "forbidden_foreign_token_env": "PHASE36_V1_14_LAUNCH_AUTHORITY",
    "requires_canonical_interpreter": True,
    "requires_cuda": True,
    "prior_attempt_consumed": False,
    "start_marker_present": v12_markers["start"],
    "result_marker_present": v12_markers["result"],
    "failure_marker_present": v12_markers["failure"],
    "static_audit_verdict_dependency": REQUIRED_STATIC_AUDIT_VERDICT,
    "static_audit_sha256": sha(STATIC_AUDIT),
    "reconciliation_v2_sha256": sha(RECON_V2),
    "v1_14_science_consumed": True,
    "v1_14_science_failed": True,
    "v1_14_science_retry_permitted": False,
    "v1_15_created": False,
    "phase37_not_started": True,
    "test_remains_phase39_only": True,
    "router_holdout_accessed": False,
    "v1_0_status": "FROZEN_NEVER_CONSUMED_NOT_AUTHORIZED",
    "v1_1_status": "CONSUMED_FAILED",
    "v1_1_retry_permitted": False,
    "scientific_output": False,
    "generated_utc": now(),
}

# --------------------------------------------------------------------------- #
# NO-EXECUTION AUDIT (all counters false)
# --------------------------------------------------------------------------- #
noexec = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_NO_EXECUTION_AUDIT",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_2",
    "model_loaded": False,
    "checkpoint_loaded": False,
    "checkpoint_deserialized_at_launcher": False,
    "val_image_read": False,
    "val_gt_read": False,
    "cuda_context_created_for_inference": False,
    "perturbation_executed": False,
    "foreign_v1_14_launch_token_used": False,
    "forbidden_gate_called": False,
    "diagnostic_start_marker_written": v12_markers["start"],
    "diagnostic_result_written": v12_markers["result"],
    "diagnostic_failure_written": v12_markers["failure"],
    "v1_11_artifacts_modified": False,
    "v1_14_science_marker_written": False,
    "v1_14_science_rerun": False,
    "v1_14_source_modified": False,
    "v1_15_created": False,
    "phase37_started": False,
    "test_accessed": False,
    "router_holdout_accessed": False,
    "scientific_output": False,
    "generated_utc": now(),
}

# --------------------------------------------------------------------------- #
# v1.1 FAILURE ADJUDICATION
# --------------------------------------------------------------------------- #
adjudication = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_V1_1_FAILURE_ADJUDICATION",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_2",
    "adjudication": "D50_FOREIGN_V1_14_LAUNCH_AUTHORITY_TOKEN_COUPLING",
    "d50_reason": D50_REASON,
    "consumed_attempt": {
        "diagnostic": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_1",
        "outcome": "CONSUMED_FAILED",
        "retry_permitted": False,
        "scientific_output": False,
        "attempt_evidence": v11_evidence,
        "failure_facts": v11_failure_facts,
        "result_artifact_absent": v11_result_absent,
    },
    "root_cause": {
        "summary": ("the frozen v1.14 module's _verify_transitive_source_integrity() reads "
                    "LAUNCH_AUTHORITY_TOKEN = 'PHASE36_V1_14_LAUNCH_AUTHORITY'; "
                    "launch_token_ok = os.environ.get(LAUNCH_AUTHORITY_TOKEN) == '1'; when the "
                    "token is absent the gate sets all_match=False and the diagnostic aborts "
                    "with DIAGNOSTIC_SOURCE_INTEGRITY_FAILED before any model load."),
        "foreign_token": "PHASE36_V1_14_LAUNCH_AUTHORITY",
        "all_byte_checks_passed_without_the_token": True,
        "missing_condition": "launch_anchor.launch_authority_token_present == true (v1.14 token)",
        "model_or_data_touched": False,
    },
    "classification": "PRE_MODEL_GOVERNANCE_COUPLING_FAILURE",
    "repair": {
        "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_2",
        "approach": ("(A) launcher does the exact pre-consumption transitive byte-integrity "
                     "proof itself; (B) both launcher and source forbid the foreign token and "
                     "fail closed if present; (C) diagnostic-native authority pair; "
                     "(D) invoke only the clean steps, omitting the frozen foreign-token gate; "
                     "(E) preserve all eq fields."),
        "foreign_v1_14_launch_token_used": False,
    },
    "prior_failure_provenance": prior_state,
    "required_static_audit_verdict": REQUIRED_STATIC_AUDIT_VERDICT,
    "observed_static_audit_verdict": static_verdict,
    "scientific_output": False,
    "generated_utc": now(),
}

# --------------------------------------------------------------------------- #
# v1.1 -> v1.2 DIFF
# --------------------------------------------------------------------------- #
diff = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_V1_1_TO_V1_2_DIFF",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_2",
    "change_class": "ADDITIVE_GOVERNANCE_REPAIR__NO_V1_0_OR_V1_1_MUTATION",
    "v1_0_preserved_byte_for_byte": v10_preserved,
    "v1_1_preserved_byte_for_byte": v11_preserved,
    "new_files": [
        "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_2.py",
        "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_2.py",
        "scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_2.py",
        "scripts/analysis/phase36_clean_equivalence_diagnostic_preflight_v1_2.py",
        "scripts/analysis/phase36_clean_equivalence_diagnostic_negative_controls_v1_2.py",
    ],
    "modified_files": [],
    "deleted_files": [],
    "source_sha256": {
        "v1_0": V10_SHAS,
        "v1_1": V11_SHAS,
        "v1_2": {"diagnostic": diag_sha, "launcher": launcher_sha, "unit": unit_sha,
                 "preflight": preflight_sha, "negative_controls": negctrl_sha},
    },
    "defect_repairs": [
        {"id": "D50", "title": D50_REASON,
         "v1_1": ("diagnostic called the frozen v1.14 _verify_transitive_source_integrity(), "
                  "which requires the FOREIGN token PHASE36_V1_14_LAUNCH_AUTHORITY=1; the "
                  "diagnostic only set its own token => fail closed pre-model. CONSUMED/FAILED."),
         "v1_2": ("launcher performs the exact pre-consumption byte-integrity proof itself "
                  "(frozen v1.14 exec SHA, manifest SHA, execution_source_sha256, "
                  "launcher_sha256 absent, 14 deps / 4 ckpts, every dep/ckpt SHA, EXACT "
                  "set+SHA equality vs the frozen v1.14 DECLARED authority maps); the foreign "
                  "token is FORBIDDEN and its presence fails closed; diagnostic-native authority "
                  "pair used; only the clean steps are invoked (frozen foreign-token gate "
                  "OMITTED); all eq fields preserved plus 5 D50 attestation fields."),
         "fail_closed_terminal": ("PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_FAIL_CLOSED__"
                                  "FOREIGN_V1_14_LAUNCH_AUTHORITY_PRESENT__NO_ATTEMPT_CONSUMED"),
         "status": "REPAIRED"},
    ],
    "d50_sub_repairs": {
        "D50-A": "pre-consumption transitive byte-integrity proof in the launcher",
        "D50-B": "foreign v1.14 launch-authority token forbidden in launcher AND source",
        "D50-C": "diagnostic-native authority: EXECUTE + V1_2_LAUNCH_AUTHORITY, ordered",
        "D50-D": "clean-only invocation; frozen foreign-token gate omitted",
        "D50-E": "D47 durable full-eq preserved + 5 D50 attestation fields",
    },
    "consumed_v1_1_binding": v11_evidence,
    "prior_failure_provenance_binding": prior_state,
    "required_static_audit_verdict": REQUIRED_STATIC_AUDIT_VERDICT,
    "observed_static_audit_verdict": static_verdict,
    "validator_results": {
        "unit": {"n_checks": unit_res.get("n_checks"), "n_pass": unit_res.get("n_pass"),
                 "all_pass": unit_res.get("all_pass")},
        "preflight": {"n_checks": pf_res.get("n_checks"), "n_pass": pf_res.get("n_pass"),
                      "all_pass": pf_res.get("all_pass")},
        "negative_controls": {"n_checks": nc_res.get("n_checks"), "n_pass": nc_res.get("n_pass"),
                              "all_pass": nc_res.get("all_pass")},
    },
    "no_execution_state": {
        "diagnostic_v1_0": "FROZEN_NEVER_CONSUMED_NOT_AUTHORIZED",
        "diagnostic_v1_1": "CONSUMED_FAILED",
        "diagnostic_v1_1_retry": "FORBIDDEN",
        "diagnostic_v1_2": "ELIGIBLE_NOT_STARTED",
        "v1_2_start_marker": "ABSENT" if not v12_markers["start"] else "PRESENT",
        "v1_2_result_marker": "ABSENT" if not v12_markers["result"] else "PRESENT",
        "v1_2_failure_marker": "ABSENT" if not v12_markers["failure"] else "PRESENT",
        "v1_14_science": "CONSUMED_FAILED",
        "v1_14_science_retry": "FORBIDDEN",
        "v1_15": "NOT_CREATED",
        "phase37": "NOT_STARTED",
        "test": "REMAINS_PHASE39_ONLY",
        "router_holdout": "NOT_ACCESSED",
    },
    "scientific_output": False,
    "generated_utc": now(),
}

wrote = {
    "contract": write_once(AUD / "phase36_clean_equivalence_diagnostic_contract_v1_2.json", contract),
    "source_freeze": write_once(AUD / "phase36_clean_equivalence_diagnostic_source_freeze_v1_2.json", freeze),
    "preflight": write_once(AUD / "phase36_clean_equivalence_diagnostic_preflight_v1_2.json", preflight),
    "negative_controls": write_once(AUD / "phase36_clean_equivalence_diagnostic_negative_controls_v1_2.json", negctrl),
    "eligibility": write_once(AUD / "phase36_clean_equivalence_diagnostic_eligibility_v1_2.json", eligibility),
    "no_execution_audit": write_once(AUD / "phase36_clean_equivalence_diagnostic_no_execution_audit_v1_2.json", noexec),
    "v1_1_failure_adjudication": write_once(
        AUD / "phase36_clean_equivalence_diagnostic_v1_1_failure_adjudication.json", adjudication),
    "v1_1_to_v1_2_diff": write_once(
        AUD / "phase36_clean_equivalence_diagnostic_v1_1_to_v1_2_diff.json", diff),
}

print(json.dumps({
    "wrote": wrote,
    "source_sha256": {"diagnostic": diag_sha, "launcher": launcher_sha, "unit": unit_sha,
                      "preflight": preflight_sha, "negative_controls": negctrl_sha},
    "validator_counts": {
        "unit": f"{unit_res.get('n_pass')}/{unit_res.get('n_checks')}",
        "preflight": f"{pf_res.get('n_pass')}/{pf_res.get('n_checks')}",
        "negative_controls": f"{nc_res.get('n_pass')}/{nc_res.get('n_checks')}",
    },
    "v1_0_preserved": v10_preserved,
    "v1_1_preserved": v11_preserved,
    "foreign_v1_14_launch_token_used": False,
    "diagnostic_v1_2": "ELIGIBLE_NOT_STARTED",
}, indent=1))
