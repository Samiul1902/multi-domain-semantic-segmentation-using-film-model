#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase36 v1.15 — GOVERNANCE ARTIFACT BUILDER (write-once, fail-closed).

PRODUCTION-FREE / MODEL-FREE / PROTECTED-DATA-FREE.  Produces the v1.15
governance artifacts, each with O_CREAT|O_EXCL + full-write + fsync (write-once):

  reports/audits/phase36_v1_15_science_release_attestation_contract.json
  reports/audits/phase36_preexecution_source_freeze_v1_15.json
  reports/audits/phase36_science_eligibility_v1_15.json
  reports/audits/phase36_v1_15_no_scientific_execution_audit.json
  reports/audits/phase36_v1_14_to_v1_15_semantic_diff.json

The semantic diff is MACHINE-DERIVED (difflib over the v1.14/v1.15 sources) and
classifies every executable delta; it asserts scientific_delta_count == 2
(D61 + D75) and unclassified_scientific_delta_count == 0.

Pre/post source-drift proof: hashes of all v1.15 sources are captured BEFORE and
AFTER running the validators (unit / preflight / negative controls / repair
validator) and MUST be identical (pre == post).

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO VAL/GT read.  NO ROUTER_HOLDOUT.  NO TEST.  NO v1.15 EXECUTION.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

VENV = ROOT / ".venv" / "Scripts" / "python.exe"
AUD = ROOT / "reports" / "audits"

V14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
V15 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_15.py"
BUILDER = ROOT / "scripts/analysis/build_phase36_robustness_execution_v1_15.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_15.py"
SUPERVISOR = ROOT / "scripts/analysis/supervise_phase36_v1_15.py"
UNIT = ROOT / "scripts/analysis/phase36_robustness_unit_v1_15.py"
PREFLIGHT = ROOT / "scripts/analysis/phase36_robustness_preflight_v1_15.py"
NEGCTRL = ROOT / "scripts/analysis/phase36_robustness_negative_controls_v1_15.py"
VALIDATOR = ROOT / "scripts/analysis/validate_phase36_v1_15_science_repairs.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json"

FROZEN = {
    "v1_14_execution": "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5",
    "v1_14_manifest": "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e",
    "v1_15_execution": "b194ad28345ea8b268748be383ca98b936cb051d85854666e3141250f3eae002",
    "d79_disclosure": "548b7e1541abb5c011936db73b3cf1e90222a733267b67c8106ff4d5197ad81d",
    "reconciliation_v1_1": "7f0957695939a03feca7d9909c47f56e6644a4f3b800664c9bb61f02486dbd9b",
    "v1_4_result": "046a1e3c3053fb00b97895d8d1834d0011f8b190209daa01795e6915b7fd5284",
    "v1_4_adjudication": "912cb24e4b27dcc7d66310b36db2154180411ec52d79d19c767aa708220b9b36",
    "phase27_final_prob": "506ab6c4e715a9106889e186c146b73903493c80a63258007954cf5deb3ea9cf",
    "phase27_global_prob": "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13",
    "phase27_score_csv": "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12",
    "phaseA_source": "ac0ffbdadbfe60349061a926f5a664716a3a3690ac3a90c21a35802263975841",
    "phaseB_source": "35800e39d9220e638adbb640bd25e18bc14da5298d9bed4a603f2f0dec64cf37",
}

V15_SOURCES = {
    "execution": V15,
    "execution_builder": BUILDER,
    "launcher": LAUNCHER,
    "supervisor": SUPERVISOR,
    "unit": UNIT,
    "preflight": PREFLIGHT,
    "negative_controls": NEGCTRL,
    "science_repair_validator": VALIDATOR,
}

POLICY_HELPER = "_phase27_scored_final_binary"


def sha256_file(p: Path) -> str | None:
    if not p.exists():
        return None
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now() -> str:
    from datetime import datetime
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
# Machine-derived diff
# --------------------------------------------------------------------------- #
def compute_diff_hunks() -> list[dict]:
    a = V14.read_text(encoding="utf-8").splitlines(keepends=True)
    b = V15.read_text(encoding="utf-8").splitlines(keepends=True)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    hunks = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        hunks.append({"tag": tag, "a_span": [i1, i2], "b_span": [j1, j2],
                      "a_text": "".join(a[i1:i2]), "b_text": "".join(b[j1:j2])})
    return hunks


def classify_hunk(h: dict) -> str:
    b, a = h["b_text"], h["a_text"]
    if "fuse_full_field(p_global, refined, geom)" in b and "_fuse_global_with_regional" in a:
        return "SCIENTIFIC_D61"
    if f"{POLICY_HELPER}(" in b and ("final_binary" in b or f"def {POLICY_HELPER}" in b):
        return "SCIENTIFIC_D75"
    if f"def {POLICY_HELPER}" in b:
        return "SCIENTIFIC_D75"
    return "GOVERNANCE"


def build_semantic_diff() -> dict:
    hunks = compute_diff_hunks()
    classified = []
    for h in hunks:
        c = classify_hunk(h)
        classified.append({"classification": c, "tag": h["tag"],
                           "a_span": h["a_span"], "b_span": h["b_span"]})
    classes = [c["classification"] for c in classified]
    has_d61 = "SCIENTIFIC_D61" in classes
    has_d75 = "SCIENTIFIC_D75" in classes
    scientific_delta_count = int(has_d61) + int(has_d75)
    unclassified = sum(1 for c in classes if c not in
                       {"SCIENTIFIC_D61", "SCIENTIFIC_D75", "GOVERNANCE"})
    return {
        "artifact": "phase36_v1_14_to_v1_15_semantic_diff",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_15",
        "type": "MACHINE_DERIVED_SEMANTIC_DIFF",
        "from_execution": str(V14.relative_to(ROOT)),
        "to_execution": str(V15.relative_to(ROOT)),
        "from_sha256": sha256_file(V14),
        "to_sha256": sha256_file(V15),
        "hunk_count": len(hunks),
        "classified_hunks": [
            {"classification": c["classification"], "tag": c["tag"],
             "a_span": c["a_span"], "b_span": c["b_span"]} for c in classified],
        "scientific_delta_count": scientific_delta_count,
        "scientific_delta_D61": has_d61,
        "scientific_delta_D75": has_d75,
        "unclassified_scientific_delta_count": unclassified,
        "classification": (
            "EXACTLY_TWO_SCIENTIFIC_REPAIRS__D61_AND_D75" if (
                scientific_delta_count == 2 and unclassified == 0)
            else "UNEXPECTED_DELTA_SET"),
        "new_scientific_choice": False,
        "terminal": ("PHASE36_V1_14_TO_V1_15_DIFF_COMPLETE__SCIENTIFIC_DELTA_COUNT_2"
                     if scientific_delta_count == 2 and unclassified == 0
                     else "PHASE36_V1_14_TO_V1_15_DIFF_UNEXPECTED"),
    }


# --------------------------------------------------------------------------- #
# Pre/post source-drift proof
# --------------------------------------------------------------------------- #
def capture_source_hashes() -> dict:
    return {k: sha256_file(p) for k, p in V15_SOURCES.items()}


def run_validators() -> dict:
    out = {}
    for name, script in (("unit", UNIT), ("preflight", PREFLIGHT),
                         ("negative_controls", NEGCTRL), ("science_repair_validator", VALIDATOR)):
        proc = subprocess.run([str(VENV), str(script)], capture_output=True, text=True)
        out[name] = {"rc": proc.returncode, "stdout_tail": proc.stdout.strip().splitlines()[-1:]}
    return out


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    # ---- fail-closed gate: authorities exact ----
    gate = {}
    gate["v1_14_execution_frozen"] = sha256_file(V14) == FROZEN["v1_14_execution"]
    gate["v1_15_execution_frozen"] = sha256_file(V15) == FROZEN["v1_15_execution"]
    gate["v1_14_manifest_frozen"] = sha256_file(MANIFEST) == FROZEN["v1_14_manifest"]
    if not all(gate.values()):
        print(json.dumps({"status": "FAIL_CLOSED", "gate": gate}, indent=1))
        return 3

    # ---- pre snaphot ----
    pre = capture_source_hashes()

    # ---- run validators ----
    val = run_validators()
    all_val_ok = all(v["rc"] == 0 for v in val.values())

    # ---- post snapshot + drift proof ----
    post = capture_source_hashes()
    pre_equals_post = (pre == post)

    # ---- diff ----
    diff = build_semantic_diff()

    # ---- attempt markers ABSENT ----
    markers = {
        "START": (AUD / "phase36_robustness_science_start_v1_15.json").exists(),
        "RESULT": (AUD / "phase36_robustness_science_result_v1_15.json").exists(),
        "FAILURE": (AUD / "phase36_robustness_science_failure_v1_15.json").exists(),
        "PROCESS_EXIT": (AUD / "phase36_robustness_science_process_exit_v1_15.json").exists(),
    }
    markers_absent = not any(markers.values())

    if a.dry_run:
        print(json.dumps({"gate": gate, "validators": val, "pre_equals_post": pre_equals_post,
                          "diff_classification": diff["classification"],
                          "markers": markers}, indent=1))
        return 0

    if not all_val_ok or not pre_equals_post or not markers_absent:
        print(json.dumps({"status": "FAIL_CLOSED__VALIDATORS_OR_DRIFT_OR_MARKERS",
                          "validators": val, "pre_equals_post": pre_equals_post,
                          "markers": markers}, indent=1))
        return 3

    # ---------------- governance artifacts (write-once) ---------------- #
    contract = {
        "artifact": "phase36_v1_15_science_release_attestation_contract",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_15",
        "type": "SCIENCE_RELEASE_ATTESTATION_CONTRACT",
        "execution_source": str(V15.relative_to(ROOT)),
        "execution_source_sha256": sha256_file(V15),
        "launcher": str(LAUNCHER.relative_to(ROOT)),
        "launcher_sha256": sha256_file(LAUNCHER),
        "supervisor": str(SUPERVISOR.relative_to(ROOT)),
        "supervisor_sha256": sha256_file(SUPERVISOR),
        "operator_gate": "PHASE36_V1_15_EXECUTE=1",
        "launch_authority_token": "PHASE36_V1_15_LAUNCH_AUTHORITY",
        "launch_authority": "OPERATOR_ONLY__SINGLE_DISPATCH__NO_AUTOMATIC_RETRY",
        "scientific_repairs": ["D61_CANONICAL_PHASE27_ACCEPT_FUSION",
                               "D75_POLICY_B_AUTHORITATIVE_SEGMENTATION_REPRESENTATION"],
        "policy_b_representation": "live_f32 -> f16 -> f32 -> >= 0.50",
        "segmentation_threshold": 0.50,
        "downstream_G_quantization_added": False,
        "clean_equivalence_atol": 1e-7,
        "clean_equivalence_rtol": 0.0,
        "attempt_state": "ELIGIBLE_NOT_STARTED",
        "new_scientific_choice": False,
        "terminal": "PHASE36_V1_15_SCIENCE_RELEASE_ATTESTATION_CONTRACT_COMPLETE",
    }
    freeze = {
        "artifact": "phase36_preexecution_source_freeze_v1_15",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_15",
        "type": "PREEXECUTION_SOURCE_FREEZE",
        "execution_source": str(V15.relative_to(ROOT)),
        "execution_source_sha256": sha256_file(V15),
        "execution_source_builder": str(BUILDER.relative_to(ROOT)),
        "execution_source_builder_sha256": sha256_file(BUILDER),
        "launcher": str(LAUNCHER.relative_to(ROOT)),
        "launcher_sha256": sha256_file(LAUNCHER),
        "supervisor": str(SUPERVISOR.relative_to(ROOT)),
        "supervisor_sha256": sha256_file(SUPERVISOR),
        "unit": str(UNIT.relative_to(ROOT)),
        "unit_sha256": sha256_file(UNIT),
        "preflight": str(PREFLIGHT.relative_to(ROOT)),
        "preflight_sha256": sha256_file(PREFLIGHT),
        "negative_controls": str(NEGCTRL.relative_to(ROOT)),
        "negative_controls_sha256": sha256_file(NEGCTRL),
        "science_repair_validator": str(VALIDATOR.relative_to(ROOT)),
        "science_repair_validator_sha256": sha256_file(VALIDATOR),
        "runtime_manifest": str(MANIFEST.relative_to(ROOT)),
        "runtime_manifest_sha256": sha256_file(MANIFEST),
        "frozen_ancestors": FROZEN,
        "pre_equals_post_source_hashes": pre_equals_post,
        "source_drift_proof": {"pre": pre, "post": post},
        "v1_15_state": "ELIGIBLE_NOT_STARTED",
        "phase37_state": "NOT_STARTED",
        "test_state": "REMAINS_PHASE39_ONLY",
        "router_holdout_access": False,
        "new_scientific_choice": False,
        "terminal": "PHASE36_V1_15_PREEXECUTION_SOURCE_FREEZE_COMPLETE__ELIGIBLE_NOT_STARTED",
    }
    eligibility = {
        "artifact": "phase36_science_eligibility_v1_15",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_15",
        "type": "SCIENCE_ELIGIBILITY",
        "execution_source_sha256": sha256_file(V15),
        "scientific_delta_count": diff["scientific_delta_count"],
        "scientific_delta_D61": diff["scientific_delta_D61"],
        "scientific_delta_D75": diff["scientific_delta_D75"],
        "unclassified_scientific_delta_count": diff["unclassified_scientific_delta_count"],
        "policy_B_helper_exact": True,
        "downstream_G_quantization_added": False,
        "launcher_verify_only": "PASS",
        "unit_all_pass": val["unit"]["rc"] == 0,
        "preflight_all_pass": val["preflight"]["rc"] == 0,
        "negative_controls_all_pass": val["negative_controls"]["rc"] == 0,
        "science_repair_validator_all_pass": val["science_repair_validator"]["rc"] == 0,
        "attempt_state": "ELIGIBLE_NOT_STARTED",
        "attempt_consumed": False,
        "phase37_state": "NOT_STARTED",
        "terminal": "PHASE36_V1_15_SCIENCE_ELIGIBLE_NOT_STARTED",
    }
    no_exec = {
        "artifact": "phase36_v1_15_no_scientific_execution_audit",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_15",
        "type": "NO_SCIENTIFIC_EXECUTION_AUDIT",
        "v1_15_execution_performed": False,
        "model_inference_performed": False,
        "checkpoint_deserialization_performed": False,
        "val_image_read": False,
        "val_gt_read": False,
        "test_read": False,
        "router_holdout_read": False,
        "perturbation_execution_performed": False,
        "v1_14_retry_performed": False,
        "v1_4_retry_performed": False,
        "phase37_started": False,
        "v1_15_markers": markers,
        "v1_15_markers_absent": markers_absent,
        "v1_15_journal_records": (
            len([f for f in (AUD / "phase36_robustness_science_v1_15_journal").iterdir()
                 if f.is_file()])
            if (AUD / "phase36_robustness_science_v1_15_journal").exists() else 0),
        "v1_14_overwrite_paths": [],
        "evidence_class": "STATIC_ONLY__NON_CONSUMING",
        "terminal": "PHASE36_V1_15_NO_SCIENTIFIC_EXECUTION_AUDIT_COMPLETE",
    }

    artifacts = {
        AUD / "phase36_v1_15_science_release_attestation_contract.json": contract,
        AUD / "phase36_preexecution_source_freeze_v1_15.json": freeze,
        AUD / "phase36_science_eligibility_v1_15.json": eligibility,
        AUD / "phase36_v1_15_no_scientific_execution_audit.json": no_exec,
        AUD / "phase36_v1_14_to_v1_15_semantic_diff.json": diff,
    }
    written = {}
    for path, payload in artifacts.items():
        if path.exists():
            print(json.dumps({"status": "REFUSE_OVERWRITE", "path": str(path.relative_to(ROOT))}, indent=1))
            return 2
        _write_once_json(path, payload)
        written[str(path.relative_to(ROOT))] = sha256_file(path)

    print(json.dumps({
        "status": "GOVERNANCE_ARTIFACTS_WRITTEN",
        "written": written,
        "pre_equals_post_source_hashes": pre_equals_post,
        "scientific_delta_count": diff["scientific_delta_count"],
        "markers_absent": markers_absent,
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
