#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.9 — ADDITIVE generator (write-once).

Reads the FROZEN v1.8 execution source and emits v1.9 by applying precise,
anchored, additive transformations for D22 / D23 / D24 / D25 and the
check-matrix reconciliation.  The v1.8 file on disk is NEVER modified.
The v1.9 file = v1.8 transformed.  Pure text/source surgery; NO torch.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

V18 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_8.py"
V19 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_9.py"
V18_SHA = "c95ff9884ec05a859b39ce7976376bf40e4543b1a8d8a19830e5893120039f4d"

src = V18.read_text(encoding="utf-8")
assert hashlib.sha256(V18.read_bytes()).hexdigest() == V18_SHA, "v1.8 SHA mismatch — STOP"


def sub_once(text, old, new, label):
    n = text.count(old)
    assert n == 1, f"ANCHOR NOT UNIQUE ({label}): count={n}"
    return text.replace(old, new, 1)


# =========================================================================== #
# 1. Header / revision / history
# =========================================================================== #
src = sub_once(src,
    '"""Phase 36 v1.8 — EXCEPTION-SAFE WRITE-ONCE SMOKE PROVENANCE +',
    '"""Phase 36 v1.9 — AUTHORIZED-ATTEMPT ORDER + TRUE WRITE-ONCE + COMPLETE\n'
    'TRANSITIVE SOURCE & CHECKPOINT INTEGRITY + R_psi/S_omega INPUT VALIDATION +\n'
    'HD95 EXACT EMPTY-CASE SEMANTICS + CHECK-MATRIX RECONCILIATION.\n'
    '\n'
    '(Supersedes v1.8 ADDITIVELY; the v1.8 header text is retained verbatim below.)\n'
    '\n'
    'v1.8 — EXCEPTION-SAFE WRITE-ONCE SMOKE PROVENANCE +', "header")

src = sub_once(src,
    "REVISION: ra_medfilm_barr_phase36_robustness_v1_8",
    "REVISION: ra_medfilm_barr_phase36_robustness_v1_9", "revision-header")

src = sub_once(src,
    "  v1.7 execution source   87062d2b38232c73b8ce620d7bfafb389658c4b877d9196a26b8b01d09daf192",
    "  v1.8 execution source   c95ff9884ec05a859b39ce7976376bf40e4543b1a8d8a19830e5893120039f4d\n"
    "  v1.8 direct byte audit  97687c2e2d77db0b94518e873378d29cf8d9de1413449c85684f68d42dfe1491\n"
    "  v1.8 source freeze      c9439a0176100391ac88048c7c6e11b16e12756463833d0eb6dd0c46ca518fec\n"
    "  v1.7 execution source   87062d2b38232c73b8ce620d7bfafb389658c4b877d9196a26b8b01d09daf192",
    "history-block")

# =========================================================================== #
# 2. v1.9 defect block
# =========================================================================== #
src = sub_once(src,
    "=========================================================================== #\n"
    "WHAT THIS FILE DOES NOT DO                                                  #",
    "=========================================================================== #\n"
    "DEFECTS REPAIRED IN v1.9 (additive; proven from the frozen v1.8 bytes)     #\n"
    "=========================================================================== #\n"
    "  D22_TRUE_WRITE_ONCE_AND_AUTHORIZED_ATTEMPT_ORDER\n"
    "      v1.8 `_write_smoke_failure_artifact()` used `Path.write_text()`\n"
    "      (overwrite semantics), and `main()` created the attempt marker BEFORE\n"
    "      `_gate_smoke()` ran inside `run_smoke()`.  A gate failure raises\n"
    "      `SystemExit(2)`, which `except Exception` does NOT catch, so an\n"
    "      UNAUTHORIZED invocation could consume the one-shot revision.\n"
    "      v1.9: the smoke authorization gate is checked in `main()` BEFORE any\n"
    "      marker exists; the start marker is created with EXCLUSIVE-create\n"
    "      semantics (`open(..., \"x\")`) and is NEVER overwritten; a DISTINCT\n"
    "      immutable failure artifact carries later exception detail; a second\n"
    "      authorized attempt fails before model construction; and\n"
    "      `smoke_attempt_is_first_write_once` is DERIVED from provenance state.\n"
    "      Classification: PRE_SCIENTIFIC_WRITE_ONCE_AND_GOVERNANCE_ORDER_DEFECT.\n"
    "      Scientific effect: NONE.\n"
    "\n"
    "  D23_TRANSITIVE_INTEGRITY_GATE_INCOMPLETE\n"
    "      v1.8's pre-model integrity table omitted load-bearing sources and did\n"
    "      NOT hash the four checkpoints before `torch.load()`; it also allowed\n"
    "      `MANIFEST_NOT_FOUND__SELF_CHECK_SKIPPED` with all_match=true.\n"
    "      v1.9 binds the B_phi / R_psi / S_omega / post-safety-feature / 202-D\n"
    "      pre-refinement / ROI sources and the common authority, and hashes ALL\n"
    "      FOUR checkpoints BEFORE any `torch.load()`; the manifest is\n"
    "      fail-closed (missing / malformed / missing field / mismatch => FAIL).\n"
    "      Classification: PRE_SCIENTIFIC_SOURCE_INTEGRITY_COMPLETENESS_DEFECT.\n"
    "      Scientific effect: NONE.\n"
    "\n"
    "  D24_D20_NUMERICAL_CONTRACT_INCOMPLETE\n"
    "      v1.8 bound R_psi `len(shape)==2` only (not the EXACT shape) and did\n"
    "      not assert the sigmoid-probability RANGE, nor expose the actual\n"
    "      normalized / one-hot final S_omega input.  v1.9 adds explicit checks:\n"
    "      R_psi exact shape, R_psi range in [0,1], final S_omega input exact\n"
    "      dimension == frozen schema, final S_omega input finite.\n"
    "      Classification: PRE_SCIENTIFIC_SMOKE_NUMERICAL_VALIDATION_DEFECT.\n"
    "      Scientific effect: NONE.\n"
    "\n"
    "  D25_HD95_EMPTY_CASE_SEMANTICS_TOO_PERMISSIVE\n"
    "      v1.8 accepted ANY of {both_empty, empty_prediction, empty_ground_truth}\n"
    "      for a KNOWN empty-prediction / nonempty-GT input.  v1.9 binds the\n"
    "      EXACT frozen reason for each of the four synthetic HD95 cases.\n"
    "      Classification: PRE_SCIENTIFIC_SMOKE_METRIC_VALIDATION_DEFECT.\n"
    "      Scientific effect: NONE.\n"
    "\n"
    "  CHECK-MATRIX RECONCILIATION\n"
    "      v1.8's header claimed 50 checks while the frozen list had 47.  v1.9\n"
    "      makes header / declared IDs / dict bindings / reported count agree,\n"
    "      enforced by `set(SMOKE_CHECK_IDS) == set(smoke_checks)` + count.\n"
    "\n"
    "=========================================================================== #\n"
    "WHAT THIS FILE DOES NOT DO                                                  #",
    "defect-block")

# =========================================================================== #
# 3. D23: extend dependency table + add checkpoint table
# =========================================================================== #
src = sub_once(src,
    '''TRANSITIVE_RUNTIME_DEPENDENCIES = {
    "scripts/analysis/phase36_robustness_common_v1_1.py":
        "edcdd33d22ae996b2f7ef60e8242a89f3cebab8c6992406508fec23cb068710c",''',
    '''TRANSITIVE_RUNTIME_DEPENDENCIES = {
    "scripts/analysis/phase36_robustness_common_v1_1.py":
        "edcdd33d22ae996b2f7ef60e8242a89f3cebab8c6992406508fec23cb068710c",
    # ---- v1.9 (D23): load-bearing sources the smoke actually loads ---------- #
    "scripts/analysis/train_phase25d_router.py":
        "fc7c1bdf263ae4551dcb8f170d3203adb8540fbc189846265b74f6eca1541e91",
    "scripts/analysis/phase25f_execution_common.py":
        "98cf958a377e2de30e0b67e63fd56bafea418b2b061a362ee7284e852012cd2e",
    "scripts/analysis/phase25f_post_safety_features.py":
        "4f4763fa67eea833643dc1870206d5c0b49890fe974122249711e259cddc8bec",
    "src/features/barr_pre_refinement_features.py":
        "f0323e78caa7a3f8c1d24cf68d4321972d86f95d36913a7af795b15acdb26f6a",
    "src/data/barr_roi.py":
        "4b1015275e4e31f9cc2b662a290c18f988eaea65cec64082cea217fad9aba9d6",''',
    "deps-extend")

src = sub_once(src,
    '''# --------------------------------------------------------------------------- #
# §D SMOKE ARTIFACT PATHS (v1.8 canonical paths)
# --------------------------------------------------------------------------- #''',
    '''# --------------------------------------------------------------------------- #
# §G v1.9 (D23): CHECKPOINT INTEGRITY TABLE — hashed BEFORE any torch.load()
# --------------------------------------------------------------------------- #
TRANSITIVE_RUNTIME_CHECKPOINTS = {
    "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt":
        "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
    "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt":
        "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
    "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt":
        "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
    "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt":
        "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
}

# --------------------------------------------------------------------------- #
# §D SMOKE ARTIFACT PATHS (v1.9 canonical paths)
# --------------------------------------------------------------------------- #''',
    "checkpoint-table")

# =========================================================================== #
# 4. D22: v1.9 smoke paths
# =========================================================================== #
src = sub_once(src,
    'SMOKE_V1_8_ARTIFACT = "reports/audits/phase36_robustness_smoke_v1_8.json"\n'
    'SMOKE_V1_8_ATTEMPT = "reports/audits/phase36_robustness_smoke_attempt_v1_8.json"',
    'SMOKE_V1_9_ARTIFACT = "reports/audits/phase36_robustness_smoke_v1_9.json"\n'
    'SMOKE_V1_9_START_MARKER = "reports/audits/phase36_robustness_smoke_start_v1_9.json"\n'
    'SMOKE_V1_9_FAILURE_ARTIFACT = "reports/audits/phase36_robustness_smoke_failure_v1_9.json"',
    "smoke-paths")

# =========================================================================== #
# 5. D23: fail-closed integrity verifier
# =========================================================================== #
old_verify = '''def _verify_transitive_source_integrity() -> dict:
    """§G: PRE-MODEL-CONSTRUCTION runtime source-integrity gate.

    Verifies every execution-critical dynamically-loaded source/config authority
    against frozen expected SHA-256 values.  Also verifies the v1.8 execution
    source itself against the companion manifest.
    Fail closed on any mismatch.
    """
    audit = {"dependencies": {}, "self_check": None, "all_match": True}
    for rel, expected in TRANSITIVE_RUNTIME_DEPENDENCIES.items():
        p = ROOT / rel
        observed = _sha(p) if p.exists() else "FILE_MISSING"
        match = observed == expected
        audit["dependencies"][rel] = {"expected": expected, "observed": observed, "match": match}
        if not match:
            audit["all_match"] = False
    # Self-check via companion manifest (avoids circular self-hash literal)
    manifest_path = AUD / "phase36_v1_8_runtime_source_integrity_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected_self = manifest.get("execution_source_sha256")
        observed_self = _sha(Path(__file__))
        self_match = expected_self == observed_self
        audit["self_check"] = {"expected": expected_self, "observed": observed_self,
                               "match": bool(self_match)}
        if not self_match:
            audit["all_match"] = False
    else:
        audit["self_check"] = {"expected": None, "observed": None,
                               "match": None, "note": "MANIFEST_NOT_FOUND__SELF_CHECK_SKIPPED"}
    return audit'''

new_verify = '''def _verify_transitive_source_integrity() -> dict:
    """§G: PRE-MODEL-CONSTRUCTION runtime source-integrity gate (v1.9 / D23).

    FAIL-CLOSED.  Verifies every execution-critical dynamically-loaded
    source/config authority AND all four canonical checkpoints against frozen
    SHA-256 values, plus the v1.9 execution source itself, BEFORE any
    ``torch.load()``.  A missing/malformed manifest, a missing
    ``execution_source_sha256`` field, or ANY mismatch fails CLOSED.
    """
    audit = {"dependencies": {}, "checkpoints": {}, "self_check": None,
             "manifest": None, "all_match": True}

    for rel, expected in TRANSITIVE_RUNTIME_DEPENDENCIES.items():
        p = ROOT / rel
        observed = _sha(p) if p.exists() else "FILE_MISSING"
        match = observed == expected
        audit["dependencies"][rel] = {"expected": expected, "observed": observed,
                                      "match": match}
        if not match:
            audit["all_match"] = False

    for rel, expected in TRANSITIVE_RUNTIME_CHECKPOINTS.items():
        p = ROOT / rel
        observed = _sha(p) if p.exists() else "FILE_MISSING"
        match = observed == expected
        audit["checkpoints"][rel] = {"expected": expected, "observed": observed,
                                     "match": match}
        if not match:
            audit["all_match"] = False

    manifest_path = AUD / "phase36_v1_9_runtime_source_integrity_manifest.json"
    if not manifest_path.exists():
        audit["self_check"] = {"expected": None, "observed": None, "match": False,
                               "note": "MANIFEST_NOT_FOUND__FAIL_CLOSED"}
        audit["manifest"] = {"present": False, "fail_closed": True}
        audit["all_match"] = False
        return audit
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        audit["self_check"] = {"expected": None, "observed": None, "match": False,
                               "note": f"MANIFEST_MALFORMED__FAIL_CLOSED__{type(exc).__name__}"}
        audit["manifest"] = {"present": True, "malformed": True, "fail_closed": True}
        audit["all_match"] = False
        return audit
    expected_self = manifest.get("execution_source_sha256")
    if not expected_self:
        audit["self_check"] = {"expected": None, "observed": None, "match": False,
                               "note": "MANIFEST_MISSING_EXECUTION_SOURCE_SHA256__FAIL_CLOSED"}
        audit["manifest"] = {"present": True, "missing_field": True, "fail_closed": True}
        audit["all_match"] = False
        return audit
    observed_self = _sha(Path(__file__))
    self_match = expected_self == observed_self
    audit["self_check"] = {"expected": expected_self, "observed": observed_self,
                           "match": bool(self_match),
                           "note": "EXTERNAL_MANIFEST_NON_CIRCULAR_ANCHOR"}
    audit["manifest"] = {"present": True, "malformed": False,
                         "missing_field": False, "fail_closed": True}
    if not self_match:
        audit["all_match"] = False
    return audit'''

src = sub_once(src, old_verify, new_verify, "verify-d23")

V19.write_text(src, encoding="utf-8")
print("STAGE-1 OK", len(src.splitlines()), "lines", hashlib.sha256(V19.read_bytes()).hexdigest())
