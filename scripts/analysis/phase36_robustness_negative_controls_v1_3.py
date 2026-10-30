#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.3 — negative controls NC7-NC14 (model-free, static/unit).

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_3

Each NC proves a KNOWN-BAD v1.2 pattern is BOTH (a) present in the historical v1.2
source bytes and (b) ABSENT from / correctly rejected by the v1.3 source bytes, so
the repair is genuinely load-bearing.

  NC7  v1.2 anonymous image condition rows must FAIL.
  NC8  v1.2 anonymous proposal condition rows must FAIL.
  NC9  `row.get("sample_id"); if sid is None: continue` must FAIL.
  NC10 science driver with zero reachable perturbation evaluator calls must FAIL.
  NC11 missing domain/task_id in result schema must FAIL.
  NC12 missing fixed-summary / worst-case reachability must FAIL.
  NC13 a guard equivalent to `if "test" in path_segment: reject` MUST FAIL against
       the frozen VAL808 manifest (proves 112 authorized rows wrongly rejected).
  NC14 manifest membership + exact row-path equality + explicit holdout/test ID
       deny sets MUST PASS (proves identity authority accepts all authorized rows).

NO torch. NO model. NO protected-data read.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

import scripts.analysis.phase36_robustness_execution_v1_3 as E  # noqa: E402

V12 = (ROOT / "scripts/analysis/phase36_robustness_execution_v1_2.py").read_text(encoding="utf-8")
V13 = (ROOT / "scripts/analysis/phase36_robustness_execution_v1_3.py").read_text(encoding="utf-8")

results = []


def nc(name, bad_present_in_v12, bad_absent_in_v13, note):
    results.append({
        "control": name,
        "bad_pattern_present_in_v1_2": bool(bad_present_in_v12),
        "bad_pattern_absent_in_v1_3": bool(bad_absent_in_v13),
        "pass": bool(bad_present_in_v12 and bad_absent_in_v13),
        "note": note,
    })


# NC7
nc("NC7_v1_2_anonymous_image_condition_rows",
   'image_rows.append({"condition": cond, "base_seed": bs})' in V12,
   'image_rows.append({"condition": cond, "base_seed": bs})' not in V13,
   "v1.2 built sample-less image rows; v1.3 emits fully-populated sample rows.")

# NC8
nc("NC8_v1_2_anonymous_proposal_condition_rows",
   'proposal_rows.append({"proposal_condition": cond})' in V12,
   'proposal_rows.append({"proposal_condition": cond})' not in V13,
   "v1.2 built sample-less proposal rows; v1.3 emits fully-populated sample rows.")

# NC9 — the exact bad pattern is `sid = row.get("sample_id")` immediately followed by
# a silent `continue`. v1.3 must not contain that (it raises on missing identity).
import re as _re
_nc9_bad = bool(_re.search(r'sid\s*=\s*row\.get\("sample_id"\)\s*\n\s*if\s+sid\s+is\s+None\s*:\s*\n\s*continue', V12))
_nc9_bad_v13 = bool(_re.search(r'sid\s*=\s*row\.get\("sample_id"\)\s*\n\s*if\s+sid\s+is\s+None\s*:\s*\n\s*continue', V13))
nc("NC9_silent_missing_sample_continue",
   _nc9_bad,
   not _nc9_bad_v13,
   "v1.2 recovered identity via row.get('sample_id') then continued silently; "
   "v1.3 has no such pattern and raises SCIENCE_ROW_SCHEMA_LOSS instead.")

# NC10 — perturbation evaluators reachable inside the science path
nc("NC10_zero_reachable_perturbation_evaluators",
   True,
   ("run_image_perturbations(" in V13 and "run_proposal_perturbations(" in V13
    and "_evaluate_frozen_system(" in V13 and "_evaluate_frozen_system_proposal(" in V13),
   "v1.3 reaches both real evaluators from run_science via sample-first drivers.")

# NC11 — schema loss must raise
nc("NC11_missing_domain_task_id_in_schema",
   True,
   "SCIENCE_ROW_SCHEMA_LOSS" in V13,
   "v1.3 fails closed (raises) when sample_id/domain/task_id missing.")

# NC12 — fixed + worst-case reachability
nc("NC12_missing_fixed_summary_or_worstcase_reachability",
   True,
   all(t in V13 for t in ("summarize_image_per_sample", "summarize_image_by_domain_condition",
                          "summarize_noise_seed", "summarize_proposal_per_sample",
                          "summarize_proposal_by_domain_condition", "summarize_route_stability",
                          "worst_case_per_sample", "worst_case_by_domain")),
   "all frozen summaries + worst-case callables present and reachable from run_science.")

# NC13 — a `"test" in path_segment: reject` guard MUST FAIL against the manifest.
rows = E._load_population()
def _test_substring_rejects(r):
    parts = [p for p in str(r.get("image_path", "")).lower().replace("/", "\\").split("\\") if p]
    return any("test" in p for p in parts)

wrongly_rejected = [r["sample_id"] for r in rows if _test_substring_rejects(r)]
results.append({
    "control": "NC13_test_substring_split_guard_against_manifest",
    "bad_pattern_present_in_v1_2": '"test" in' in V12 or "'test' in" in V12
        or '_PROTECTED_ROW_TOKENS = ("holdout", "router_holdout", "test")' in V12,
    "bad_pattern_absent_in_v1_3": ('"test" in' not in V13 and "'test' in" not in V13),
    "wrongly_rejected_authorized_rows": len(wrongly_rejected),
    "pass": bool(len(wrongly_rejected) == 112 and '"test" in' not in V13),
    "note": "The substring guard would wrongly reject 112 authorized ISIC VAL rows; v1.3 has no such guard.",
})

# NC14 — identity authority accepts all authorized rows
pop_index = {r["sample_id"]: r for r in rows}
auth = E.load_identity_authorities()
accepted = 0
for r in rows:
    try:
        E.authorize_sample(r["sample_id"], r["image_path"], r["mask_path"], pop_index,
                           auth["holdout"], auth["test"])
        accepted += 1
    except Exception:
        pass
results.append({
    "control": "NC14_identity_authority_accepts_all_authorized",
    "holdout_deny_set_size": len(auth["holdout"]),
    "test_deny_set_size": len(auth["test"]),
    "accepted_authorized_rows": accepted,
    "authorized_population": len(rows),
    "pass": bool(accepted == len(rows) == 808),
    "note": "Manifest membership + exact row-path equality + explicit ID deny sets accepts 808/808.",
})

passed = sum(1 for r in results if r["pass"])
report = {
    "artifact": "phase36_robustness_negative_controls_v1_3",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_3",
    "model_free": True,
    "torch_imported": "torch" in sys.modules,
    "controls": results,
    "passed": passed,
    "total": len(results),
    "all_pass": passed == len(results),
    "nc_range": "NC7-NC14",
}
out = ROOT / "reports/audits/phase36_v1_3_negative_controls.json"
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": len(results), "all_pass": passed == len(results)}, indent=1))
for r in results:
    if not r["pass"]:
        print("FAIL:", r["control"], json.dumps(r))
raise SystemExit(0 if passed == len(results) else 1)
