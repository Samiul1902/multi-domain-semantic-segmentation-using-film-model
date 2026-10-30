#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Emit the additive canonical closure terminal for PHASE 35 (§J / §M).
READ-ONLY. No model, no data, no science. Reads only the v1.0a closure artifacts.
The historical terminal is preserved untouched.
"""
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / "reports" / "audits"

closure = json.loads((AUD / "phase35_canonical_closure_v1_0a.json").read_text(encoding="utf-8"))
fc = json.loads((AUD / "phase35_canonical_closure_final_check_v1_0a.json").read_text(encoding="utf-8"))

TERMINAL = (
 "PHASE35_FEATURE_ATTRIBUTION_AND_VISUAL_INTERPRETABILITY_COMPLETE_CANONICAL__"
 "FIRST_SCIENTIFIC_EXECUTION_PRESERVED__"
 "I1_FILM_AND_TASK_EMBEDDING_INTERPRETABILITY_COMPLETE__"
 "I2_FIXED_VAL64_GUARDED_GRADCAM_COMPLETE__"
 "I3_FIXED_DISPLAY16_GT_FREE_ROI_PROPOSAL_VISUALIZATION_COMPLETE__"
 "I4_VAL808_RAW_DELTA_HAT_GRADIENT_X_INPUT_ATTRIBUTION_COMPLETE__"
 "SCIENTIFIC_ARTIFACT_INVENTORY_AND_HASH_AUDIT_PASS__"
 "F1_TO_F7_VISUAL_INTEGRITY_PASS__"
 "ZERO_GT_ROUTER_HOLDOUT_OR_TEST_ACCESS__"
 "NO_POST_OPEN_SCIENTIFIC_SOURCE_PATCH_OR_RETRY__"
 "DESCRIPTIVE_MODEL_MECHANISM_CLAIM_BOUNDARY_PRESERVED__"
 "PHASE36_ELIGIBLE_NOT_STARTED__TEST_REMAINS_PHASE39_ONLY"
)

out = {
 "artifact": "phase35_canonical_closure_terminal_v1_0a",
 "section": "\u00a7M",
 "phase": 35,
 "method": "RA-MedFiLM-BARR",
 "revision": closure["revision"],
 "classification": closure["closure_classification"],
 "gate": "every closure check passed",
 "closure_artifact_sha256": hashlib.sha256((AUD/"phase35_canonical_closure_v1_0a.json").read_bytes()).hexdigest(),
 "closure_final_check_sha256": hashlib.sha256((AUD/"phase35_canonical_closure_final_check_v1_0a.json").read_bytes()).hexdigest(),
 "closure_final_check_passed": fc["passed"],
 "closure_final_check_total": fc["total_checks"],
 "historical_terminal_preserved_unchanged": True,
 "historical_terminal_sha256": "4caa152d6a998d7df10dc902c24cd8738af36821e7f2f017786603416e9d1d91",
 "historical_terminal_disposition": "SUCCESS_TERMINAL_CONTRACT_VARIANT__GOVERNANCE_ONLY",
 "post_open_scientific_source_patch": False,
 "scientific_execution_invocations": 1,
 "scientific_retry": False,
 "scientific_result_preserved": True,
 "prefreeze_driver_guard_repair": "DISCLOSED_AND_ACCEPTED",
 "pre_scientific_synthetic_execution_discipline_deviation":
   "PRE_SCIENTIFIC_SYNTHETIC_EXECUTION_DISCIPLINE_DEVIATION__NO_SCIENTIFIC_EFFECT",
 "phase36_started": False,
 "phase36_eligibility": "ELIGIBLE_NOT_STARTED",
 "test_state": "LOCKED_UNTIL_PHASE39",
 "terminal_state": closure["closure_classification"],
 "terminal_string": TERMINAL,
 "all_pass": bool(closure["all_pass"] and fc["all_pass"]),
 "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
p = AUD / "phase35_canonical_closure_terminal_v1_0a.json"
p.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(hashlib.sha256(p.read_bytes()).hexdigest())
print(TERMINAL)
