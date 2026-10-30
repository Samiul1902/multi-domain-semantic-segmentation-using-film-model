#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.11 — PRE-SMOKE GOVERNANCE CONVERGENCE:
SCIENCE TRANSITIVE-INTEGRITY PRE-MODEL GATE + SCIENCE OUTPUT PROVENANCE
VERSION CORRECTION + SCIENCE FIRST-ATTEMPT WRITE-ONCE (EXCEPTION AND
SystemExit EVIDENCE PRESERVED) + EXTERNAL NON-CIRCULAR LAUNCH ANCHOR.

ADDITIVE over v1.9.  The v1.9 execution source is byte-preserved; v1.11 is a NEW
artifact.  NO scientific semantics changed (new_scientific_choice = false).

REVISION: ra_medfilm_barr_phase36_robustness_v1_11
TYPE: PRE-SCIENTIFIC SMOKE/SCIENCE GOVERNANCE REPAIR ONLY.

=========================================================================== #
DEFECTS REPAIRED IN V1.11 (proven from the frozen v1.9 bytes)              #
=========================================================================== #
  D30_SCIENCE_TRANSITIVE_INTEGRITY_GATE_MISSING
      v1.9 ``run_science()`` called ``_load_models()`` WITHOUT first running
      ``_verify_transitive_source_integrity()``; only the smoke path gated
      integrity before model construction.  v1.11 inserts the SAME (not a
      different) integrity gate BEFORE ``_load_models()`` in BOTH paths.
  D31_SCIENCE_RESULT_PATH_MISBOUND_TO_V1_8
      v1.9 ``main()`` wrote science output to
      ``phase36_robustness_scientific_result_v1_8.json`` — forbidden provenance
      aliasing, overwrite semantics via ``write_text``).  v1.11 uses unique
      v1.11 science provenance paths with EXCLUSIVE-CREATE semantics.  The
      historical filename appears ONLY in the constant below
      (``FORBIDDEN_SCIENCE_RESULT_V1_8``), which is a declared sentinel and is
      never used as a write target.
  D32_SCIENCE_FIRST_ATTEMPT_PROVENANCE_MISSING
      v1.9 wrote the science result only AFTER ``run_science()`` returned, so a
      ``SystemExit`` (e.g. CLEAN_GLOBAL_REPRODUCTION_GATE_FAILED /
      CLEAN_EQUIVALENCE_GATE_FAILED) left NO durable evidence.  v1.11 adds an
      authorization-first + exclusive science START marker + distinct failure
      artifact, and durably records Exception, SystemExit and logical failure.
  D33_EXTERNAL_NON_CIRCULAR_EXECUTION_ANCHOR_MISSING
      v1.9 relied on the manifest ``execution_source_sha256`` self-comparison,
      which a source+manifest co-edit defeats.  v1.11 adds a real
      PRE-INVOCATION launcher authority (``scripts/analysis/launch_phase36_v1_11.py``)
      that verifies exact frozen SHAs of BOTH the v1.11 execution source AND the
      v1.11 runtime manifest before authorizing dispatch.  The release chain is
      anchored by the external launcher + a frozen supervisor pin, NOT by a
      circular source<->manifest<->launcher dependency.

=========================================================================== #
HISTORY PRESERVED (never rewritten)                                        #
=========================================================================== #
  v1.10 unit source      9b880c92469e7daca8f6563e64bf2e2e712d4eb8ac304298fbb52f89ab87c329
      (POST-FREEZE AVAILABILITY NOTE: recorded PRESENT and SHA-verified on disk
       at the time of the v1.11 freeze; see the v1.10 availability record.  The
       v1.10 unit source is NOT reconstructed or rewritten by v1.11.)
  v1.9 execution source  433bad87b4ef77fd6997c77f688eb295e526bfa3e88dece4ec5d3d550255cbd0
  v1.9 unit source       c39edd7764a0e9733cc5905e5e54935b1bcd9cc62c345189f618b0c6f4ea690e
  v1.8 execution source  c95ff9884ec05a859b39ce7976376bf40e4543b1a8d8a19830e5893120039f4d
  v1.7 execution source  87062d2b38232c73b8ce620d7bfafb389658c4b877d9196a26b8b01d09daf192
  v1.6 / v1.5 / v1.4 / v1.3 / v1.2 / v1.1 / v1.0 history retained verbatim.
  No historical PASS/BLOCK terminal or audit is rewritten.

=========================================================================== #
v1.9 — AUTHORIZED-ATTEMPT ORDER + TRUE WRITE-ONCE + COMPLETE
TRANSITIVE SOURCE & CHECKPOINT INTEGRITY + R_psi/S_omega INPUT VALIDATION +
HD95 EXACT EMPTY-CASE SEMANTICS + CHECK-MATRIX RECONCILIATION.
(v1.9 header retained verbatim below.)

(Supersedes v1.8 ADDITIVELY; the v1.8 header text is retained verbatim below.)

v1.8 — EXCEPTION-SAFE WRITE-ONCE SMOKE PROVENANCE +
REAL EXECUTE NUMERICAL VALIDATION + HD95 BINDING + TRANSITIVE RUNTIME
SOURCE INTEGRITY.

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_11
TYPE: PRE-SCIENTIFIC SMOKE/SCIENCE GOVERNANCE REPAIR ONLY.

=========================================================================== #
HISTORY PRESERVED (never rewritten)                                        #
=========================================================================== #
  v1.8 execution source   c95ff9884ec05a859b39ce7976376bf40e4543b1a8d8a19830e5893120039f4d
  v1.8 direct byte audit  97687c2e2d77db0b94518e873378d29cf8d9de1413449c85684f68d42dfe1491
  v1.8 source freeze      c9439a0176100391ac88048c7c6e11b16e12756463833d0eb6dd0c46ca518fec
  v1.7 execution source   87062d2b38232c73b8ce620d7bfafb389658c4b877d9196a26b8b01d09daf192
  v1.7 direct byte audit  3a7a11d13b683b223c967ee86ddb1e5df6e5f90469d4a1e112cee1b774bca43e
  v1.7 source freeze      e4e86cd9a3e297d8b4f0a52591be6b88d27cef9897b933d427aa9c15f15fa62f
  v1.6 / v1.5 / v1.4 / v1.3 / v1.2 / v1.1 / v1.0 history retained verbatim.
  No historical PASS/BLOCK terminal or audit is rewritten.
  The v1.6 protected-population repair remains VALID HISTORICAL PREEXECUTION EVIDENCE.

=========================================================================== #
DEFECTS REPAIRED (proven from the frozen v1.7 bytes; see                    #
reports/audits/phase36_v1_7_pre_smoke_contract_defects_v1_8.json)          #
=========================================================================== #
  D19_EXCEPTION_PATH_FIRST_SMOKE_EVIDENCE_NOT_FAIL_CLOSED_PRESERVED
      v1.7 ``main()`` called ``run_smoke()`` BEFORE writing the canonical
      smoke artifact.  If ``run_smoke()`` raised (CUDA failure, checkpoint
      load failure, 202-D violation, non-finite vector, R_psi failure,
      S_omega failure, metric failure, etc.), the first attempt terminated
      WITHOUT producing durable evidence.  Also, ``Path.write_text()``
      permits overwrite on manual re-run.
      Classification: PRE_SCIENTIFIC_SMOKE_PROVENANCE_AND_FAIL_CLOSED_GOVERNANCE_DEFECT.
      Scientific effect: NONE.

  D20_REAL_EXECUTE_NUMERICAL_FINITE_PROPERTIES_NOT_BOUND_TO_SMOKE_ALL_PASS
      v1.7 smoke_all_pass bound only actual forward counts.  It did NOT
      require: router_decision==EXECUTE, R_psi output finite/shape-valid,
      post-safety 16-D features finite/dimension-correct, S_omega logit finite,
      accept_probability finite and in [0,1], final_probability shape [512,512],
      final_probability finite, router_vector_dim==202, router_vector_finite.
      A non-finite S_omega output could pass smoke merely because count==1.
      Classification: PRE_SCIENTIFIC_SMOKE_NUMERICAL_VALIDATION_DEFECT.
      Scientific effect: NONE.

  D21_HD95_EXECUTED_BUT_NOT_BOUND_TO_SMOKE_SUCCESS_CONTRACT
      v1.7 evaluated HD95 plumbing during smoke but did not bind HD95
      validity/semantics into smoke_all_pass.  The frozen canonical metric
      authority requires Dice/IoU/HD95 plumbing.
      Classification: PRE_SCIENTIFIC_SMOKE_METRIC_VALIDATION_DEFECT.
      Scientific effect: NONE.

=========================================================================== #
DEFECTS REPAIRED IN v1.9 (additive; proven from the frozen v1.8 bytes)     #
=========================================================================== #
  D22_TRUE_WRITE_ONCE_AND_AUTHORIZED_ATTEMPT_ORDER
      v1.8 `_write_smoke_failure_artifact()` used `Path.write_text()`
      (overwrite semantics), and `main()` created the attempt marker BEFORE
      `_gate_smoke()` ran inside `run_smoke()`.  A gate failure raises
      `SystemExit(2)`, which `except Exception` does NOT catch, so an
      UNAUTHORIZED invocation could consume the one-shot revision.
      v1.9: the smoke authorization gate is checked in `main()` BEFORE any
      marker exists; the start marker is created with EXCLUSIVE-create
      semantics (`open(..., "x")`) and is NEVER overwritten; a DISTINCT
      immutable failure artifact carries later exception detail; a second
      authorized attempt fails before model construction; and
      `smoke_attempt_is_first_write_once` is DERIVED from provenance state.
      Classification: PRE_SCIENTIFIC_WRITE_ONCE_AND_GOVERNANCE_ORDER_DEFECT.
      Scientific effect: NONE.

  D23_TRANSITIVE_INTEGRITY_GATE_INCOMPLETE
      v1.8's pre-model integrity table omitted load-bearing sources and did
      NOT hash the four checkpoints before `torch.load()`; it also allowed
      `MANIFEST_NOT_FOUND__SELF_CHECK_SKIPPED` with all_match=true.
      v1.9 binds the B_phi / R_psi / S_omega / post-safety-feature / 202-D
      pre-refinement / ROI sources and the common authority, and hashes ALL
      FOUR checkpoints BEFORE any `torch.load()`; the manifest is
      fail-closed (missing / malformed / missing field / mismatch => FAIL).
      Classification: PRE_SCIENTIFIC_SOURCE_INTEGRITY_COMPLETENESS_DEFECT.
      Scientific effect: NONE.

  D24_D20_NUMERICAL_CONTRACT_INCOMPLETE
      v1.8 bound R_psi `len(shape)==2` only (not the EXACT shape) and did
      not assert the sigmoid-probability RANGE, nor expose the actual
      normalized / one-hot final S_omega input.  v1.9 adds explicit checks:
      R_psi exact shape, R_psi range in [0,1], final S_omega input exact
      dimension == frozen schema, final S_omega input finite.
      Classification: PRE_SCIENTIFIC_SMOKE_NUMERICAL_VALIDATION_DEFECT.
      Scientific effect: NONE.

  D25_HD95_EMPTY_CASE_SEMANTICS_TOO_PERMISSIVE
      v1.8 accepted ANY of {both_empty, empty_prediction, empty_ground_truth}
      for a KNOWN empty-prediction / nonempty-GT input.  v1.9 binds the
      EXACT frozen reason for each of the four synthetic HD95 cases.
      Classification: PRE_SCIENTIFIC_SMOKE_METRIC_VALIDATION_DEFECT.
      Scientific effect: NONE.

  CHECK-MATRIX RECONCILIATION
      v1.8's header claimed 50 checks while the frozen list had 47.  v1.9
      makes header / declared IDs / dict bindings / reported count agree,
      enforced by `set(SMOKE_CHECK_IDS) == set(smoke_checks)` + count.

=========================================================================== #
WHAT THIS FILE DOES NOT DO                                                  #
=========================================================================== #
  NO MODEL EXECUTION · NO CHECKPOINT DESERIALIZATION · NO FORWARD ·
  NO AUTOGRAD · NO VAL IMAGE READ · NO VAL GT READ · NO VAL808 SCIENTIFIC
  EXECUTION · NO ROUTER_HOLDOUT READ · NO TEST READ · NO SMOKE · NO SCIENCE ·
  NO TRAINING.
  Importing this module performs NO model construction and NO protected-data
  access.  ``torch`` is imported lazily inside the execution helpers only.
  No post-open patch.  No retry.  First valid attempt preserved.

=========================================================================== #
ACTUAL FORWARD-COUNT SEMANTICS (v1.7 / v1.8)                                #
=========================================================================== #
  Every field named ``*_forward_count`` represents an ACTUAL invocation of that
  learned component.  Control injection NEVER increments or implies an actual
  forward.  ``canonical_learned_core`` tracks ``actual_r_psi_forwards`` and
  ``actual_s_omega_forwards`` locally, incrementing each ONLY immediately after
  a real ``ctx["r_psi"](...)`` / ``system.post_safety(...)`` call.  When
  ``forced_s_omega_logit is not None`` the S_omega actual count REMAINS 0.
  For normal science (no forced control arguments) EXECUTE still yields
  R_psi = 1 and S_omega = 1 actual forwards.  No scientific behaviour changes.

  POLICY CONTROLS (forced router score / forced safety logit) are reported with
  ``policy_control = true``, ``forced_router_score``, ``forced_safety_logit`` and
  MUST NOT claim a real S_omega forward when S_omega was bypassed.

=========================================================================== #
FAIL-CLOSED SMOKE SUCCESS CONTRACT (v1.8)                                   #
=========================================================================== #
  ``smoke_checks`` is a frozen mapping of 50 check IDs.
  ``smoke_all_pass = all(smoke_checks.values())``.
  Write-once attempt provenance: BEFORE model construction the v1.8 smoke
  checks whether a canonical attempt artifact already exists; if so, it
  FAILS CLOSED.  The smoke execution is wrapped so that EXCEPTIONS produce
  a canonical FAILED artifact (attempted=true, completed=false,
  smoke_all_pass=false, exception=true) before exiting nonzero.
  Logical failures also write the artifact first, then exit nonzero.
  NO automatic retry, overwrite or deletion.

  Transitive runtime source integrity (v1.8):
      BEFORE torch model construction / checkpoint loading / CUDA allocation,
      all execution-critical dynamically-loaded source/config authorities are
      SHA-256 verified against frozen expected values.  Fail closed on mismatch.

GATES (both default UNSET; fail closed)
  --mode science  requires PHASE36_EXECUTE == "1"
  --mode smoke    requires PHASE36_SMOKE_EXECUTE == "1"

STOP CONDITIONS honoured by this source (this work order):
  DO NOT RUN v1.8 SMOKE.  DO NOT RUN PHASE36 SCIENCE.
  DO NOT START PHASE37.  DO NOT ACCESS TEST.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

import numpy as np  # noqa: E402

import scripts.analysis.phase36_robustness_common_v1_1 as C  # noqa: E402

AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
ARR = ROOT / "reports" / "arrays"
FIG = ROOT / "reports" / "figures" / "phase36_robustness"

# --------------------------------------------------------------------------- #
# canonical constants (bound, never re-derived)
# --------------------------------------------------------------------------- #
G_DEFAULT_CFG = "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json"

G_COMPONENT = {
    "class": "GlobalMedFiLM",
    "checkpoint": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
    "sha256": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
    "params": 3523001,
}
B_PHI_COMPONENT = {
    "class": "BARRBenefitRouterV1",
    "source": "scripts/analysis/train_phase25d_router.py",
    "checkpoint": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
    "sha256": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
    "params": 36801,
}
R_PSI_COMPONENT = {
    "class": "BARRRegionalRefinerV1",
    "checkpoint": "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
    "sha256": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
    "params": 1276401,
}
S_OMEGA_COMPONENT = {
    "class": "BARRPostSafetyV1",
    "source": "scripts/analysis/phase25f_execution_common.py",
    "checkpoint": "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
    "sha256": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
    "params": 1217,
}

ROUTER_NORMALIZATION_PATH = "reports/tables/phase25d_final_normalization_stats.csv"
ROUTER_NORMALIZATION_SHA = "ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb"
SOMEGA_NORMALIZATION_PATH = "reports/tables/phase25f_final_normalization_stats.csv"
SOMEGA_NORMALIZATION_SHA = "e112e18b134c6edcdcd0c254c362d0a954a75faffe634cc37a2a17e4fe6f4e7b"

ROUTER_NUMERIC_DIM = 202
ROUTER_SCALAR_IDX = [192, 193, 194, 195, 196, 197, 200, 201]
SOMEGA_NUMERIC_DIM = 16
# D24: exact frozen final S_omega input width.
#   Frozen source of truth (scripts/analysis/phase25f_execution_common.py):
#     FEATURE_DIM = 20 = NUMERIC_IDX [0..15] (16 numeric, post _apply_norm)
#                        + ONEHOT_IDX [16..19] (4-way task one-hot, raw)
#   and src/models/barr/ra_medfilm_barr.py::forward_inference builds
#     full = np.concatenate([sf_norm, self._onehot_task(task_id)], axis=0)
#   so the final S_omega input vector is exactly 16 + 4 = 20 wide.
SOMEGA_ONEHOT_DIM = 4
SOMEGA_FINAL_INPUT_DIM = SOMEGA_NUMERIC_DIM + SOMEGA_ONEHOT_DIM
assert SOMEGA_FINAL_INPUT_DIM == 20, "frozen S_omega input schema must be 20-D"
SOMEGA_ACCEPT_THRESHOLD = 0.50
SEGMENTATION_OUTPUT_THRESHOLD = 0.50
ROI_PROPOSAL_THRESHOLD = 0.30
ROI_FRACTIONAL_MARGIN = 0.25
REGIONAL_INPUT_RESOLUTION = 256
REGIONAL_CANVAS_RESOLUTION = 512

_METRIC_EPS = 1e-7

ROUTE_STATES_FULL = ("FORCED_SKIP", "SKIP_GLOBAL",
                     "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT")
ROUTER_DECISIONS = ("SKIP", "EXECUTE")

# --------------------------------------------------------------------------- #
# §G TRANSITIVE RUNTIME SOURCE INTEGRITY (frozen expected SHAs)
# --------------------------------------------------------------------------- #
TRANSITIVE_RUNTIME_DEPENDENCIES = {
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
        "4b1015275e4e31f9cc2b662a290c18f988eaea65cec64082cea217fad9aba9d6",
    "src/models/film/global_medfilm.py":
        "a04ff3e61b4d900ff47c2f390da4a999e73bd6047b28a19e41b05115e431d11f",
    "src/models/barr/regional_refiner.py":
        "4fe0abde3ec3a183d930f676c4400b4d9ba778793ea64abf1755c5b8dabf947a",
    "src/models/barr/ra_medfilm_barr.py":
        "342f2163690c2fa8d5a601ab1d18178b982d701b916935c33e0793b0801c3724",
    "src/utils/device.py":
        "9adabfbd145a5952275aa25b0ec99aab8a5114bb41aa443ecde52ce19a8448b6",
    "src/metrics/evaluation_metrics.py":
        "6c515f6f1a495315c79238292c385a082ae8347489130ad5bff34d74c4f181f6",
    "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json":
        "66ec701aeac503cbeceff75aa070e30b46146c9069e46594cbd484f6816260f5",
    "reports/tables/phase25d_final_normalization_stats.csv":
        "ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb",
    "reports/tables/phase25f_final_normalization_stats.csv":
        "e112e18b134c6edcdcd0c254c362d0a954a75faffe634cc37a2a17e4fe6f4e7b",
}

# --------------------------------------------------------------------------- #
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
# §D SMOKE ARTIFACT PATHS (v1.11 canonical paths — unique, never aliasing v1.8/v1.9)
# --------------------------------------------------------------------------- #
SMOKE_V1_11_ARTIFACT = "reports/audits/phase36_robustness_smoke_v1_11.json"
SMOKE_V1_11_START_MARKER = "reports/audits/phase36_robustness_smoke_start_v1_11.json"
SMOKE_V1_11_FAILURE_ARTIFACT = "reports/audits/phase36_robustness_smoke_failure_v1_11.json"

# --------------------------------------------------------------------------- #
# §D32 SCIENCE ARTIFACT PATHS (v1.11 canonical paths — D31 provenance correction).
# NEVER the historical v1.8/v1.9 science path.  Distinct from the smoke paths.
# --------------------------------------------------------------------------- #
SCIENCE_V1_11_ARTIFACT = "reports/audits/phase36_robustness_scientific_result_v1_11.json"
SCIENCE_V1_11_START_MARKER = "reports/audits/phase36_robustness_science_start_v1_11.json"
SCIENCE_V1_11_FAILURE_ARTIFACT = "reports/audits/phase36_robustness_science_failure_v1_11.json"
# The historical (FORBIDDEN) aliased science path retained ONLY as a negative
# sentinel so a repair regression can be detected; it is NEVER written.
FORBIDDEN_SCIENCE_RESULT_V1_8 = "reports/audits/phase36_robustness_scientific_result_v1_8.json"

# --------------------------------------------------------------------------- #
# §D33 EXTERNAL NON-CIRCULAR LAUNCH ANCHOR.
# The EXACT frozen expected SHAs are held by the external launcher
# (scripts/analysis/launch_phase36_v1_11.py), which verifies them BEFORE
# authorizing dispatch.  The source only REQUIRES that the launcher authorized
# this dispatch (token + manifest-declared launcher SHA).  There is NO
# source<->manifest<->launcher circular hash dependency: the launcher SHA is
# bound by the v1.11 source freeze and pinned externally by the supervisor.
# --------------------------------------------------------------------------- #
V1_11_RUNTIME_MANIFEST = "reports/audits/phase36_v1_11_runtime_source_integrity_manifest.json"
LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_11_LAUNCH_AUTHORITY"

# --------------------------------------------------------------------------- #
# §D  FROZEN PHASE27 CANONICAL NUMERICAL AUTHORITY (GLOBAL G EXTRACTION)
# --------------------------------------------------------------------------- #
# Bound from reports/audits/phase27_canonical_numeric_mode_execution.json,
# reports/audits/phase27_batch_semantics_audit.json,
# reports/audits/phase27_exact_batch_partition.json,
# reports/audits/phase27_conditional_branch_batch_semantics.json and
# reports/audits/phase29_val808_shared_global_cache_contract_v1_2.json.
CANONICAL_G_DEVICE = "cuda"
CANONICAL_G_REQUIRES_CUDA = True
CANONICAL_G_MODEL_DTYPE = "float32"
CANONICAL_G_INPUT_DTYPE = "float32"
CANONICAL_G_MODEL_EVAL = True
CANONICAL_G_AUTOCAST_ENABLED = True
CANONICAL_G_AUTOCAST_DTYPE = "float16"
CANONICAL_G_NO_GRAD = True
CANONICAL_G_INFERENCE_MODE = False            # torch.inference_mode must be OFF
CANONICAL_G_BATCH_SIZE = 8
CANONICAL_SAMPLE_ORDER = "(dataset ascending, sample_id ascending)"
CANONICAL_BATCH_PARTITION = "contiguous chunks of 8 inside a single domain"
CANONICAL_LAST_PARTIAL_BATCH = "trailing chunk of size n mod 8 (never padded)"
CANONICAL_PROBABILITY_COMPUTATION = "sigmoid(logits.float()) -> float32"
CANONICAL_PROBABILITY_STORAGE_DTYPE = "float16"
CANONICAL_DOMAIN_ORDER = ("BUSI", "ISIC", "KUB", "KVASIR")   # dataset ascending
CANONICAL_BATCH_FORWARDS_BY_DOMAIN = OrderedDict(
    [("BUSI", 11), ("ISIC", 45), ("KUB", 35), ("KVASIR", 11)])   # 102 total
CANONICAL_BATCH_FORWARDS_TOTAL = 102
CANONICAL_LAST_BATCH_SIZE_BY_DOMAIN = OrderedDict(
    [("BUSI", 4), ("ISIC", 5), ("KUB", 8), ("KVASIR", 7)])

# §E  frozen Phase27 global probability authority (the clean-G reproduction target)
PHASE27_GLOBAL_PROB_AUTHORITY = OrderedDict([
    ("path", "data_cache/phase27_barr_preservation_v1_0/phase27_val808_global_prob_f16.npy"),
    ("sha256", "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13"),
    ("shape", [808, 512, 512]),
    ("dtype", "float16"),
    ("sample_order", "frozen VAL808 population order (dataset asc, sample_id asc)"),
    ("byte_identical_twin", "data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/val808_global_prob_f16.npy"),
    ("role", "Phase27 frozen global probability cache (authoritative reproduction target)"),
])
CLEAN_G_REPRODUCTION_GATE = OrderedDict([
    ("preferred", "BIT_IDENTICAL_FLOAT16_PERSISTED_GLOBAL_PROBABILITY"),
    ("on_non_identical",
     "record max_abs, mismatch_count, affected sample IDs and affected batch IDs, "
     "then STOP before downstream Phase36 perturbation execution"),
    ("silent_acceptance_of_changed_G_numeric_path", "FORBIDDEN"),
])

# --------------------------------------------------------------------------- #
# §C/§D/§E  v1.5 CANONICAL G PROBABILITY OPERATOR (the ONE central authority)
# --------------------------------------------------------------------------- #
CANONICAL_PROBABILITY_OPERATOR = OrderedDict([
    ("id", "CANONICAL_G_LOGITS_TO_PROBABILITY_V1_5"),
    ("expression", "torch.sigmoid(logits.float()).cpu().numpy()"),
    ("output_dtype", "float32"),
    ("persistence_dtype_where_frozen_cache_requires", "float16"),
    ("authority",
     "scripts/analysis/build_phase25a_global_cache.py L172: "
     "prob = torch.sigmoid(logits.float()).cpu().numpy()[:, 0]"),
    ("bound_in", [
        "reports/audits/phase29_phase_d_component_inference_semantics_contract_v1_1.json",
        "reports/audits/phase30_component_inference_semantics_contract_v1_1.json",
        "reports/audits/phase27_canonical_numeric_mode_execution.json",
    ]),
    ("forbidden", [
        "numpy.exp", "manual logistic", "scipy.special.expit",
        "float64 sigmoid intermediates", "duplicate probability reconstruction",
    ]),
    ("central_site_count_required", 1),
])
MANUAL_SIGMOID_FORBIDDEN = True

# --------------------------------------------------------------------------- #
# §G  v1.5 CUDA FAIL-CLOSED DEVICE POLICY
# --------------------------------------------------------------------------- #
CANONICAL_DEVICE_CONTRACT = OrderedDict([
    ("call", "get_device(require_cuda=True)"),
    ("required_device_type", "cuda"),
    ("cpu_scientific_fallback_permitted", False),
    ("fail_closed_if_cuda_unavailable", True),
    ("authority", "src/utils/device.py CANONICAL_REQUIRES_CUDA = True"),
    ("applies_to", ["science", "smoke"]),
])

# --------------------------------------------------------------------------- #
# §I  v1.5 COMPONENT-SPECIFIC INFERENCE CONTEXTS (frozen; NOT interchangeable)
# --------------------------------------------------------------------------- #
COMPONENT_INFERENCE_CONTEXTS = OrderedDict([
    ("G", OrderedDict([
        ("eval", True), ("model_dtype", "float32"), ("input_dtype", "float32"),
        ("autocast_enabled", True), ("autocast_dtype", "float16"),
        ("grad_context", "torch.no_grad()"), ("inference_mode", False),
        ("batch_size", 8),
        ("probability_computation", "torch.sigmoid(logits.float()).cpu().numpy()"),
    ])),
    ("B_phi", OrderedDict([
        ("eval", True), ("model_dtype", "float32"), ("input_dtype", "float32"),
        ("autocast_enabled", False), ("grad_context", "torch.inference_mode()"),
        ("inference_mode", True),
        ("batch_size", "PER_SAMPLE_SINGLE_FORWARD"),
        ("score", "raw logit delta_hat (no sigmoid)"),
    ])),
    ("R_psi", OrderedDict([
        ("eval", True), ("model_dtype", "float32"), ("input_dtype", "float32"),
        ("autocast_enabled", False), ("grad_context", "torch.inference_mode()"),
        ("inference_mode", True),
        ("batch_size", "PER_SAMPLE_SINGLE_FORWARD"),
        ("probability_computation", "torch.sigmoid(model(x).float())[:, 0]"),
    ])),
    ("S_omega", OrderedDict([
        ("eval", True), ("model_dtype", "float32"), ("input_dtype", "float32"),
        ("autocast_enabled", False), ("grad_context", "torch.inference_mode()"),
        ("inference_mode", True),
        ("batch_size", "PER_SAMPLE_SINGLE_FORWARD"),
        ("accept_threshold", 0.50),
    ])),
])
COMPONENT_CONTEXTS_NOT_INTERCHANGEABLE = True

# Batch-size adjudication (checked against the existing Phase29/30 contract):
# the Phase29/30 offline calibration batch constants (R_psi 8 / B_phi full-matrix /
# S_omega 128) apply to the OFFLINE calibration + cache paths.  The conditional
# components are membership-independent, and the Phase27 runtime contract freezes
# per-sample conditional evaluation ("no_cross_sample_batching_of_conditional_components").
# Phase36 v1.5 therefore preserves per-sample conditional evaluation and does NOT
# introduce a new batch-size scientific choice.
COMPONENT_BATCH_SIZE_ADJUDICATION = OrderedDict([
    ("phase27_runtime_contract",
     "reports/audits/phase27_conditional_branch_batch_semantics.json"),
    ("phase29_offline_contract",
     "reports/audits/phase29_phase_d_component_inference_semantics_contract_v1_1.json"),
    ("conditional_components_membership_sensitive", False),
    ("runtime_batching", "PER_SAMPLE_SINGLE_FORWARD"),
    ("new_batch_size_scientific_choice_introduced", False),
    ("classification", "CHECKED_AND_ADJUDICATED__NOT_A_NEW_SCIENTIFIC_DEFECT"),
])

# --------------------------------------------------------------------------- #
# §D  FROZEN IMAGE REALIZATION PLAN (materialized from the frozen registry)
# --------------------------------------------------------------------------- #
NONCLEAN_DETERMINISTIC_IMAGE_CONDITIONS = [
    "BRIGHTNESS_NEG", "BRIGHTNESS_POS",
    "CONTRAST_LOW", "CONTRAST_HIGH",
    "GAMMA_LOW", "GAMMA_HIGH",
    "GAUSSIAN_BLUR_LOW", "GAUSSIAN_BLUR_HIGH",
    "RESOLUTION_075", "RESOLUTION_050",
]                                     # 10 deterministic realizations
NONCLEAN_NOISE_IMAGE_CONDITIONS = [
    "GAUSSIAN_NOISE_LOW", "GAUSSIAN_NOISE_HIGH",
]                                     # x {42,123,3407} -> 6 realizations

AUTHORIZED_POPULATION_N = C.POPULATION_N              # 808
CLEAN_EXECUTIONS_EXPECTED = AUTHORIZED_POPULATION_N   # 808
NONCLEAN_IMAGE_REALIZATIONS_PER_SAMPLE = 16           # 10 + 6
IMAGE_REALIZATIONS_PER_SAMPLE_INCL_CLEAN = 17         # 16 + 1
NONCLEAN_IMAGE_EXECUTIONS_EXPECTED = (
    AUTHORIZED_POPULATION_N * NONCLEAN_IMAGE_REALIZATIONS_PER_SAMPLE)  # 12,928
LOGICAL_IMAGE_TABLE_ROWS_MAX = (
    AUTHORIZED_POPULATION_N * IMAGE_REALIZATIONS_PER_SAMPLE_INCL_CLEAN)  # 13,736

NONCLEAN_PROPOSAL_CONDITIONS = [
    "SHIFT_LEFT_10", "SHIFT_RIGHT_10", "SHIFT_UP_10", "SHIFT_DOWN_10",
    "SCALE_085", "SCALE_115",
]                                     # 6 non-clean proposal conditions
PROPOSAL_CLEAN_CONDITION = "PROPOSAL_CLEAN"
NONCLEAN_PROPOSAL_CONDITIONS_PER_SAMPLE = 6
NONCLEAN_PROPOSAL_EXECUTIONS_MAX = (
    AUTHORIZED_POPULATION_N * NONCLEAN_PROPOSAL_CONDITIONS_PER_SAMPLE)  # 4,848

# --------------------------------------------------------------------------- #
# §C  FROZEN VAL808-ONLY RUNTIME POPULATION AUTHORITY (v1.6)
# --------------------------------------------------------------------------- #
# The frozen VAL808 manifest is the COMPLETE Phase36 runtime admission authority.
# There is NO runtime deny-set IO against any protected population.
#
# HISTORICAL CONTEXT ONLY (not executable): earlier revisions additionally read
#   "manifests/phase4_v3/val_router_holdout.csv"
#   "reports/audits/phase24_router_split_manifest.csv"
#   "manifests/phase4_v3/test.csv"
# as defense-in-depth identity deny sets.  Those runtime reads are REMOVED in
# v1.6; no TEST / ROUTER_HOLDOUT sample IDs or paths are materialized at runtime.
PROTECTED_RUNTIME_POPULATION = "VAL808_ONLY"
ROUTER_HOLDOUT_RUNTIME_READS_ALLOWED = False
TEST_RUNTIME_READS_ALLOWED = False
VAL_MANIFEST_IS_ONLY_POPULATION_RUNTIME_AUTHORITY = True

#: frozen expected VAL808 row count (bound to the frozen common contract)
VAL_RUNTIME_EXPECTED_N = C.POPULATION_N
if VAL_RUNTIME_EXPECTED_N != 808:
    raise AssertionError(
        f"VAL_RUNTIME_EXPECTED_N {VAL_RUNTIME_EXPECTED_N} != 808 (frozen)")

VAL_RUNTIME_AUTHORITY = OrderedDict([
    ("path", C.VAL_MANIFEST),
    ("sha256", C.VAL_MANIFEST_SHA),
    ("expected_n", C.POPULATION_N),
    ("require_unique_sample_id", True),
    ("require_split_value", "VAL"),
    ("image_path_source", "AUTHORIZED_VAL_MANIFEST_ROW"),
    ("mask_path_source", "AUTHORIZED_VAL_MANIFEST_ROW"),
    ("filename_stem_identity_inference", False),
    ("vendor_directory_substring_split_inference", False),
    ("protected_deny_set_io", False),
])

PROTECTED_COUNTERS = ("router_holdout_reads", "test_reads")

VENDOR_DIRECTORY_NAMES_ARE_TRANSPORT_METADATA = True

# --------------------------------------------------------------------------- #
# §L  FROZEN KUB SUBGROUP METADATA AUTHORITY (REPORTING ONLY)
# --------------------------------------------------------------------------- #
KUB_SUBGROUP_AUTHORITY = OrderedDict([
    ("path", "manifests/phase4_v3/val.csv"),
    ("sha256", C.VAL_MANIFEST_SHA),
    ("selector", "dataset == 'KUB'"),
    ("label_column", "category"),
    ("subgroups", ["Kidney_Stone", "Bladder_Stone", "Ureteric_Stone"]),
    ("expected_counts", OrderedDict(
        [("Bladder_Stone", 144), ("Kidney_Stone", 112), ("Ureteric_Stone", 24)])),
    ("reporting_only", True),
    ("never_classes", True),
    ("never_task_ids", True),
    ("never_model_inputs", True),
])

# --------------------------------------------------------------------------- #
# §M  FROZEN FIGURE REGISTRY R1-R5 (selection frozen; builders implemented here)
# --------------------------------------------------------------------------- #
FIGURE_REGISTRY = C.FIGURES      # R1..R5, frozen upstream; never re-selected

# --------------------------------------------------------------------------- #
# §H  FROZEN TOP-LEVEL SMOKE SUCCESS CONTRACT (declared BEFORE running smoke)
# --------------------------------------------------------------------------- #
# Each id is an OBSERVED EXECUTION PROPERTY except the two explicitly marked
# classification fields, which are immutable by construction.
SMOKE_CHECK_IDS = [
    "transitive_runtime_source_integrity_pass",
    "four_component_checkpoint_loads_strict",
    "four_parameter_counts_exact",
    "all_component_weights_finite",
    "four_components_on_canonical_cuda_device",
    "canonical_G_probability_dtype_float32",
    "canonical_G_output_finite",
    "router_vector_dim_exactly_202",
    "router_vector_finite",
    "real_B_phi_forward_proven",
    "real_R_psi_forward_proven",
    "real_S_omega_forward_proven",
    "real_execute_router_decision_is_execute",
    "real_execute_R_psi_output_finite",
    "real_execute_R_psi_output_shape_valid",
    "real_execute_post_safety_feature_dim_16",
    "real_execute_post_safety_features_finite",
    "real_execute_S_omega_logit_finite",
    "real_execute_S_omega_probability_finite",
    "real_execute_S_omega_probability_in_unit_interval",
    "real_execute_final_state_valid",
    "real_execute_final_probability_shape_512x512",
    "real_execute_final_probability_finite",
    "clean_synthetic_final_probability_finite",
    "image_synthetic_final_probability_finite",
    "nonempty_proposal_adapter_called",
    "empty_proposal_adapter_called",
    "empty_proposal_R_psi_zero",
    "empty_proposal_S_omega_zero",
    "empty_proposal_no_replacement_geometry",
    "skip_policy_control_exact",
    "accept_policy_control_exact",
    "reject_policy_control_exact",
    "forced_control_counts_reported_honestly",
    "perturbation_registry_outputs_finite",
    "clean_perturbation_bitwise_identity",
    "gaussian_noise_same_input_determinism",
    "different_seed_changes_realization",
    "different_synthetic_sample_id_changes_realization",
    "metric_dice_iou_plumbing_valid",
    "metric_hd95_nonempty_plumbing_valid",
    "metric_hd95_empty_mask_semantics_valid",
    # §D25 (v1.9): two ADDITIONAL exact HD95 cases bound to their EXACT reason.
    "metric_hd95_nonempty_prediction_empty_gt_exact",
    "metric_hd95_empty_empty_exact",
    # §D24 (v1.9): R_psi exact shape + range, final S_omega input exact dim+finite.
    "real_execute_R_psi_output_exact_shape",
    "real_execute_R_psi_output_in_unit_interval",
    "real_execute_final_S_omega_input_exact_dim",
    "real_execute_final_S_omega_input_finite",
    "prediction_consistency_metric_finite",
    "protected_test_holdout_runtime_io_statically_unreachable",
    "smoke_attempt_is_first_write_once",
    "scientific_output_false",
    "synthetic_only_true",
]
SMOKE_CLASSIFICATION_ONLY_CHECKS = [
    "scientific_output_false",
    "synthetic_only_true",
]
SMOKE_SUCCESS_CONTRACT = OrderedDict([
    ("ids", list(SMOKE_CHECK_IDS)),
    ("n_checks", len(SMOKE_CHECK_IDS)),
    ("aggregation", "smoke_all_pass = all(smoke_checks.values())"),
    ("declared_before_execution", True),
    ("classification_only_ids", list(SMOKE_CLASSIFICATION_ONLY_CHECKS)),
    ("artifact_written_even_when_failed", True),
    ("automatic_retry", False),
    ("exit_nonzero_when_failed", True),
])


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _rows(path: Path):
    return list(csv.DictReader(path.open(encoding="utf-8")))


def _verify_transitive_source_integrity() -> dict:
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

    manifest_path = AUD / "phase36_v1_11_runtime_source_integrity_manifest.json"
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

    # §D33 (v1.11): the manifest self-check ALONE does not defeat a source+manifest
    # co-edit.  The real non-circular anchor is the EXTERNAL launcher
    # (scripts/analysis/launch_phase36_v1_11.py), which verifies the exact frozen
    # SHAs of THIS source and THIS manifest BEFORE dispatching.  We therefore also
    # require the launch-authority token to be present in the environment AND the
    # manifest to declare the frozen launcher SHA.  This is NOT a circular
    # dependency: the launcher SHA is bound by the v1.11 source freeze and pinned
    # by the external supervisor; the source does not hash the launcher, it only
    # REQUIRES the launcher to have authorized the dispatch.
    expected_launcher = manifest.get("launcher_sha256")
    launch_token_ok = os.environ.get(LAUNCH_AUTHORITY_TOKEN) == "1"
    audit["launch_anchor"] = {
        "launcher_sha256_declared": expected_launcher,
        "launch_authority_token_present": bool(launch_token_ok),
        "token_name": LAUNCH_AUTHORITY_TOKEN,
        "note": "EXTERNAL_PRE_INVOCATION_LAUNCHER_REQUIRED",
    }
    if not expected_launcher or not launch_token_ok:
        audit["all_match"] = False
    return audit


def _static_protected_io_unreachable() -> bool:
    """§H: STATIC proof that no protected-population IO is reachable from either
    entrypoint.  Source/AST reasoning only — no protected artifact is inspected.

    Returns True iff neither ``run_science`` nor ``run_smoke`` can transitively
    reach an executable reference to a protected identity symbol or path literal.
    """
    import ast as _ast
    src = Path(__file__).read_text(encoding="utf-8")
    tree = _ast.parse(src)
    funcs = {n.name: n for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef)}
    protected_symbols = ("TEST_MANIFEST", "ROUTER_HOLDOUT_MANIFEST",
                         "ROUTER_HOLDOUT_IDENTITY_AUTHORITY")
    protected_tokens = ("val_router_holdout", "phase24_router_split_manifest",
                        "phase4_v3/test.csv")

    def _calls(name):
        node = funcs.get(name)
        if node is None:
            return set()
        out = set()
        for x in _ast.walk(node):
            if isinstance(x, _ast.Call):
                f = x.func
                out.add(f.id if isinstance(f, _ast.Name)
                        else (f.attr if isinstance(f, _ast.Attribute) else None))
        return out

    def _reach(entry):
        seen, stack = set(), [entry]
        while stack:
            f = stack.pop()
            if f in seen or f not in funcs:
                continue
            seen.add(f)
            for c in _calls(f):
                if c in funcs and c not in seen:
                    stack.append(c)
        return seen

    for entry in ("run_science", "run_smoke"):
        for name in _reach(entry):
            # This detector's OWN pattern constants are self-referential string
            # literals, not runtime IO.  They are excluded explicitly.
            if name == "_static_protected_io_unreachable":
                continue
            for x in _ast.walk(funcs[name]):
                if isinstance(x, _ast.Name) and x.id in protected_symbols:
                    return False
                if isinstance(x, _ast.Constant) and isinstance(x.value, str):
                    for t in protected_tokens:
                        if t in x.value:
                            return False
    return True


# --------------------------------------------------------------------------- #
# gates
# --------------------------------------------------------------------------- #
def _gate_science() -> int:
    if os.environ.get(C.GATE_ENV) != "1":
        print(json.dumps({"mode": "science", "fail_closed": True,
                          "reason": f"{C.GATE_ENV} != '1'",
                          "terminal": "PHASE36_SCIENCE_FAIL_CLOSED__GATE_NOT_SET"}, indent=1))
        return 2
    return 0


def _gate_smoke() -> int:
    if os.environ.get(C.SMOKE_GATE_ENV) != "1":
        print(json.dumps({"mode": "smoke", "fail_closed": True,
                          "reason": f"{C.SMOKE_GATE_ENV} != '1'",
                          "terminal": "PHASE36_SMOKE_FAIL_CLOSED__GATE_NOT_SET"}, indent=1))
        return 2
    return 0


def _gate_smoke_state() -> str:
    """§D22: pure authorization state — 'AUTHORIZED' iff the smoke gate is held.

    NOTE: this function performs NO I/O and creates NO marker; it only reports
    whether the explicit PHASE36_SMOKE_EXECUTE gate is currently held, so that
    the authorized-attempt ordering (gate FIRST, marker SECOND) is enforceable.
    """
    return "AUTHORIZED" if os.environ.get(C.SMOKE_GATE_ENV) == "1" else "NOT_AUTHORIZED"


def _gate_science_state() -> str:
    """§D32: pure authorization state — 'AUTHORIZED' iff the science gate is held.

    No I/O, no marker creation.  Reports whether the explicit PHASE36_EXECUTE
    gate is currently held, enforcing gate-FIRST / marker-SECOND ordering on the
    science path exactly as on the smoke path.
    """
    return "AUTHORIZED" if os.environ.get(C.GATE_ENV) == "1" else "NOT_AUTHORIZED"


# --------------------------------------------------------------------------- #
# §C/§D  VAL808-ONLY RUNTIME POPULATION ADMISSION (NO PROTECTED DENY-SET IO)
# --------------------------------------------------------------------------- #
def _authorized_path_exact(declared: str, row_value: str) -> bool:
    """TRUE iff declared path is BYTE-FOR-BYTE the manifest-authorized row path."""
    if not row_value:
        return False
    return str(declared).strip() == str(row_value).strip()


def _load_population():
    """Manifest-authoritative VAL808 runtime population (§C/§E).

    The ONLY authority is the frozen VAL808 manifest:

      1. exact ``C.VAL_MANIFEST_SHA`` verification BEFORE use;
      2. exactly 808 rows;
      3. exactly 808 unique ``sample_id`` values;
      4. every admitted row has ``split == "VAL"``;
      5. ``image_path`` / ``mask_path`` are the authorized manifest row values.

    NO protected deny-set IO.  NO ``load_identity_authorities()``.
    NO vendor-folder substring inference.  A protected population is never
    opened merely to prove that a VAL row is not in it.
    """
    man = ROOT / C.VAL_MANIFEST
    if _sha(man) != C.VAL_MANIFEST_SHA:
        raise ValueError("VAL_MANIFEST_SHA_MISMATCH")
    rows = _rows(man)
    if len(rows) != VAL_RUNTIME_EXPECTED_N:
        raise ValueError(f"VAL808_POPULATION_SIZE_MISMATCH: {len(rows)} != "
                         f"{VAL_RUNTIME_EXPECTED_N}")
    ids = [r.get("sample_id") for r in rows]
    if any(not s for s in ids):
        raise ValueError("VAL808_MISSING_SAMPLE_ID")
    if len(set(ids)) != VAL_RUNTIME_EXPECTED_N:
        raise ValueError("VAL808_SAMPLE_ID_NOT_UNIQUE")

    for r in rows:
        sid = r.get("sample_id")
        if str(r.get("split", "")).upper() != "VAL":
            raise ValueError(f"NON_VAL_ROW_REJECTED: {sid}")
        if not str(r.get("image_path", "")).strip():
            raise ValueError(f"VAL808_MISSING_IMAGE_PATH: {sid}")
        if not str(r.get("mask_path", r.get("gt_path", ""))).strip():
            raise ValueError(f"VAL808_MISSING_MASK_PATH: {sid}")
    return rows


def authorize_sample(sid: str, image_path: str, mask_path: str,
                     pop_index: dict) -> dict:
    """Return an authorization record, failing closed on any identity violation (§F).

    The ONLY authority is:
      (1) ``sample_id`` present in the frozen VAL808 ``pop_index``;
      (2) image path exactly equals the authorized VAL manifest row;
      (3) mask  path exactly equals the authorized VAL manifest row.

    No protected population is consulted; no ``holdout_ids`` / ``test_ids``
    parameters exist.
    """
    if sid is None:
        raise ValueError("MISSING_SAMPLE_ID")
    if sid not in pop_index:
        raise ValueError(f"NOT_IN_VAL808_MANIFEST: {sid}")
    row = pop_index[sid]
    if not _authorized_path_exact(image_path, row.get("image_path", "")):
        raise ValueError(f"IMAGE_PATH_MISMATCH: {sid}")
    if not _authorized_path_exact(mask_path, row.get("mask_path", row.get("gt_path", ""))):
        raise ValueError(f"MASK_PATH_MISMATCH: {sid}")
    return {"sample_id": sid, "authorized": True,
            "image_path": row["image_path"],
            "mask_path": row.get("mask_path", row.get("gt_path", "")),
            "domain": row.get("dataset"), "task_id": int(row["task_id"])}


def val_runtime_authority_audit() -> dict:
    """Non-protected, VAL-only runtime authority self-description."""
    rows = _load_population()
    return {
        "protected_runtime_population": PROTECTED_RUNTIME_POPULATION,
        "val_manifest": C.VAL_MANIFEST,
        "val_manifest_sha256": C.VAL_MANIFEST_SHA,
        "val_manifest_sha_guard_present": True,
        "n_rows": len(rows),
        "expected_n": VAL_RUNTIME_EXPECTED_N,
        "n_unique_sample_id": len({r["sample_id"] for r in rows}),
        "all_split_val": all(str(r.get("split", "")).upper() == "VAL" for r in rows),
        "router_holdout_runtime_reads_allowed": ROUTER_HOLDOUT_RUNTIME_READS_ALLOWED,
        "test_runtime_reads_allowed": TEST_RUNTIME_READS_ALLOWED,
        "protected_deny_set_io": False,
        "vendor_directory_substring_split_inference": False,
    }


# --------------------------------------------------------------------------- #
# §D  CANONICAL SAMPLE ORDER + BATCH PARTITION
# --------------------------------------------------------------------------- #
def canonical_population_rows():
    """VAL808 rows in the frozen canonical order: (dataset asc, sample_id asc)."""
    rows = _load_population()
    return sorted(rows, key=lambda r: (str(r.get("dataset", "")), str(r["sample_id"])))


def canonical_batch_partition(rows=None):
    """Contiguous domain-local chunks of 8, domains in dataset-ascending order."""
    rows = canonical_population_rows() if rows is None else rows
    out = []
    for dom in CANONICAL_DOMAIN_ORDER:
        dom_rows = [r for r in rows if str(r.get("dataset")) == dom]
        dom_rows.sort(key=lambda r: str(r["sample_id"]))
        for i in range(0, len(dom_rows), CANONICAL_G_BATCH_SIZE):
            out.append((dom, [r["sample_id"] for r in dom_rows[i:i + CANONICAL_G_BATCH_SIZE]]))
    return out


def canonical_batch_plan_audit() -> dict:
    """Reproduce the frozen Phase27 exact batch partition (102 batches / 808 samples)."""
    plan = canonical_batch_partition()
    by_domain = OrderedDict((d, 0) for d in CANONICAL_DOMAIN_ORDER)
    last_size = {}
    for dom, sids in plan:
        by_domain[dom] += 1
        last_size[dom] = len(sids)
    return {
        "batch_size": CANONICAL_G_BATCH_SIZE,
        "total_batches": len(plan),
        "total_sample_forwards": sum(len(s) for _, s in plan),
        "batches_by_domain": dict(by_domain),
        "last_batch_size_by_domain": last_size,
        "expected_total_batches": CANONICAL_BATCH_FORWARDS_TOTAL,
        "expected_batches_by_domain": dict(CANONICAL_BATCH_FORWARDS_BY_DOMAIN),
        "matches_phase27_exact_partition": bool(
            len(plan) == CANONICAL_BATCH_FORWARDS_TOTAL
            and dict(by_domain) == dict(CANONICAL_BATCH_FORWARDS_BY_DOMAIN)
            and last_size == dict(CANONICAL_LAST_BATCH_SIZE_BY_DOMAIN)),
        "last_partial_batch_rule": CANONICAL_LAST_PARTIAL_BATCH,
    }


def _chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


# --------------------------------------------------------------------------- #
# canonical mask preprocessing — bind src/data/transforms.py
# --------------------------------------------------------------------------- #
def _mask_preprocess(mask_pil):
    from PIL import Image, ImageOps
    m = mask_pil.convert("L")
    w, h = m.size
    size = 512
    scale = min(size / w, size / h)
    rw, rh = max(1, round(w * scale)), max(1, round(h * scale))
    m = m.resize((rw, rh), Image.Resampling.NEAREST)
    left, top = (size - rw) // 2, (size - rh) // 2
    m = ImageOps.expand(m, (left, top, size - rw - left, size - rh - top))
    return (np.asarray(m).copy() > 0).astype(np.float32)


# --------------------------------------------------------------------------- #
# canonical metrics — bind src/metrics/evaluation_metrics.py
# --------------------------------------------------------------------------- #
def _confusion(pred, gt):
    from src.metrics import evaluation_metrics as M
    return M.binary_confusion_counts(np.asarray(pred).astype(bool),
                                     np.asarray(gt).astype(bool))


def _dice(pred, gt):
    from src.metrics import evaluation_metrics as M
    return float(M.dice(_confusion(pred, gt)))


def _iou(pred, gt):
    from src.metrics import evaluation_metrics as M
    return float(M.iou(_confusion(pred, gt)))


def _hd95(pred, gt):
    from src.metrics import evaluation_metrics as M
    return M.hd95(np.asarray(pred).astype(bool), np.asarray(gt).astype(bool))


def _prediction_consistency_dice(perturbed_final_mask, clean_final_mask):
    """§P: Dice(perturbed_final_binary_mask, clean_final_binary_mask)."""
    return _dice(np.asarray(perturbed_final_mask).astype(bool),
                 np.asarray(clean_final_mask).astype(bool))


def _finite_summary(values):
    vals = np.asarray(list(values), dtype=np.float64)
    finite = vals[np.isfinite(vals)]
    return {
        "n_total": int(vals.size),
        "n_finite": int(finite.size),
        "n_nan": int(vals.size - finite.size),
        "mean": (float(finite.mean()) if finite.size else None),
        "median": (float(np.median(finite)) if finite.size else None),
    }


# --------------------------------------------------------------------------- #
# §F  ACTUAL MODEL LOADING
# --------------------------------------------------------------------------- #
def _load_router_class():
    """AST-extract the canonical BARRBenefitRouterV1 from its frozen source."""
    import ast
    src = (ROOT / B_PHI_COMPONENT["source"]).read_text(encoding="utf-8")
    for node in ast.parse(src).body:
        if isinstance(node, ast.ClassDef) and node.name == "BARRBenefitRouterV1":
            ns = {"__name__": "_router", "__builtins__": __builtins__}
            exec("import torch\nimport torch.nn as nn\n", ns)
            exec(compile(ast.Module(body=[node], type_ignores=[]),
                         B_PHI_COMPONENT["source"], "exec"), ns)
            return ns["BARRBenefitRouterV1"]
    raise RuntimeError("BARRBenefitRouterV1 not found in canonical source")


def _load_somega_class():
    """AST-extract the canonical BARRPostSafetyV1 + its frozen dim constants."""
    import ast
    import torch as _t
    path = ROOT / S_OMEGA_COMPONENT["source"]
    tree = ast.parse(path.read_text(encoding="utf-8"))
    ns = {"__name__": "_somega", "torch": _t, "nn": _t.nn, "np": np}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            tg = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if any(t in ("FEATURE_DIM", "HIDDEN", "NUMERIC_IDX", "ONEHOT_IDX") for t in tg):
                exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), ns)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "BARRPostSafetyV1":
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), ns)
            return ns["BARRPostSafetyV1"]
    raise RuntimeError("BARRPostSafetyV1 not found in canonical source")


def _read_norm_rows(path_rel):
    return list(csv.DictReader((ROOT / path_rel).open(encoding="utf-8")))


class _WrapG:
    """Adapter making GlobalMedFiLM.task_ids kwarg-compatible with the wrapper call."""

    def __init__(self, model):
        self.model = model
        for name in ("eval", "requires_grad_", "to", "parameters", "state_dict"):
            if hasattr(model, name):
                setattr(self, name, getattr(model, name))

    def __call__(self, image, task_ids=None, **kw):
        return self.model(image, task_ids)


def _load_models():
    """REAL construction + strict load of the four frozen canonical components.

    Returns an executable context:
        system        -- RAMedFiLMBARR with all four components composed
        g / b_phi / r_psi / s_omega -- the individually loaded modules
        device, router_norm, somega_norm, load_audit
    Never raises a placeholder.  Requires a live torch.

    §G: the canonical device is resolved with the FROZEN fail-closed contract
    ``get_device(require_cuda=True)`` and ``device.type`` MUST be ``"cuda"``.
    There is NO CPU fallback for Phase36 v1.5 scientific or smoke execution.
    """
    import torch
    from src.models.film.global_medfilm import GlobalMedFiLM
    from src.models.barr.regional_refiner import BARRRegionalRefinerV1
    from src.models.barr.ra_medfilm_barr import RAMedFiLMBARR
    from src.utils.device import get_device

    # ---- §G CUDA fail-closed device resolution ---------------------------- #
    device = get_device(require_cuda=True)
    if getattr(device, "type", str(device)) != CANONICAL_DEVICE_CONTRACT["required_device_type"]:
        raise RuntimeError(
            f"PHASE36_V1_5_CUDA_FAIL_CLOSED__DEVICE_TYPE={getattr(device, 'type', device)!r} "
            f"!= {CANONICAL_DEVICE_CONTRACT['required_device_type']!r}")
    audit = {"components": {}, "checks": {},
             "device_contract": {
                 "call": CANONICAL_DEVICE_CONTRACT["call"],
                 "resolved_device": str(device),
                 "resolved_device_type": str(getattr(device, "type", device)),
                 "cpu_scientific_fallback_permitted":
                     CANONICAL_DEVICE_CONTRACT["cpu_scientific_fallback_permitted"],
                 "fail_closed": True}}

    # ---- G ---------------------------------------------------------------- #
    cfg = json.loads((ROOT / G_DEFAULT_CFG).read_text(encoding="utf-8"))["model"]
    g = GlobalMedFiLM(
        task_count=cfg["task_count"], in_channels=cfg["in_channels"],
        out_channels=cfg["out_channels"], channels=tuple(cfg["channels"]),
        task_embedding_dim=cfg["task_embedding_dim"],
        film_hidden_dim=cfg["film_hidden_dim"])
    g_ck = torch.load(ROOT / G_COMPONENT["checkpoint"], map_location="cpu", weights_only=False)
    g_strict = g.load_state_dict(g_ck["model_state"], strict=True)
    g.eval(); g.requires_grad_(False)

    # ---- R_psi ------------------------------------------------------------ #
    r_psi = BARRRegionalRefinerV1()
    r_ck = torch.load(ROOT / R_PSI_COMPONENT["checkpoint"], map_location="cpu", weights_only=False)
    r_strict = r_psi.load_state_dict(r_ck["model_state"], strict=True)
    r_psi.eval(); r_psi.requires_grad_(False)

    # ---- B_phi ------------------------------------------------------------ #
    Router = _load_router_class()
    b_phi = Router()
    b_ck = torch.load(ROOT / B_PHI_COMPONENT["checkpoint"], map_location="cpu", weights_only=False)
    b_strict = b_phi.load_state_dict(b_ck["model_state"], strict=True)
    b_phi.eval(); b_phi.requires_grad_(False)

    # ---- S_omega ---------------------------------------------------------- #
    Safety = _load_somega_class()
    s_omega = Safety()
    s_ck = torch.load(ROOT / S_OMEGA_COMPONENT["checkpoint"], map_location="cpu", weights_only=False)
    s_strict = s_omega.load_state_dict(s_ck["model_state"], strict=True)
    s_omega.eval(); s_omega.requires_grad_(False)

    def _count(m):
        return int(sum(p.numel() for p in m.parameters()))

    for name, m, comp, strict_res in (
            ("G", g, G_COMPONENT, g_strict),
            ("R_psi", r_psi, R_PSI_COMPONENT, r_strict),
            ("B_phi", b_phi, B_PHI_COMPONENT, b_strict),
            ("S_omega", s_omega, S_OMEGA_COMPONENT, s_strict)):
        missing = list(getattr(strict_res, "missing_keys", []))
        unexpected = list(getattr(strict_res, "unexpected_keys", []))
        audit["components"][name] = {
            "class": comp["class"], "checkpoint": comp["checkpoint"],
            "checkpoint_sha256": _sha(ROOT / comp["checkpoint"]),
            "checkpoint_sha256_expected": comp["sha256"],
            "parameter_count": _count(m),
            "parameter_count_expected": comp["params"],
            "missing_keys": missing, "unexpected_keys": unexpected,
            "strict_load_ok": not missing and not unexpected,
            "all_weights_finite": bool(all(bool(torch.isfinite(p).all()) for p in m.parameters())),
            "eval_mode": not m.training,
            "requires_grad_false": bool(all(not p.requires_grad for p in m.parameters())),
        }

    checks = {
        "G_params_3523001": audit["components"]["G"]["parameter_count"] == 3523001,
        "R_psi_params_1276401": audit["components"]["R_psi"]["parameter_count"] == 1276401,
        "B_phi_params_36801": audit["components"]["B_phi"]["parameter_count"] == 36801,
        "S_omega_params_1217": audit["components"]["S_omega"]["parameter_count"] == 1217,
        "all_strict_load_ok": all(v["strict_load_ok"] for v in audit["components"].values()),
        "zero_missing_keys": all(len(v["missing_keys"]) == 0 for v in audit["components"].values()),
        "zero_unexpected_keys": all(len(v["unexpected_keys"]) == 0 for v in audit["components"].values()),
        "all_weights_finite": all(v["all_weights_finite"] for v in audit["components"].values()),
        "all_eval_mode": all(v["eval_mode"] for v in audit["components"].values()),
        "all_requires_grad_false": all(v["requires_grad_false"] for v in audit["components"].values()),
        "all_checkpoint_sha_match": all(
            v["checkpoint_sha256"] == v["checkpoint_sha256_expected"]
            for v in audit["components"].values()),
    }
    audit["checks"] = checks
    if not all(checks.values()):
        raise RuntimeError(f"CANONICAL_COMPONENT_LOAD_FAILURE: {checks}")

    rn_rows = _read_norm_rows(ROUTER_NORMALIZATION_PATH)
    if _sha(ROOT / ROUTER_NORMALIZATION_PATH) != ROUTER_NORMALIZATION_SHA:
        raise RuntimeError("router normalization artifact SHA mismatch")
    router_mu = np.asarray([float(x["mu"]) for x in rn_rows], dtype=np.float64)
    router_sigma = np.asarray([float(x["sigma"]) for x in rn_rows], dtype=np.float64)
    router_const = np.asarray([str(x["is_constant"]).lower() == "true" for x in rn_rows])

    sn_rows = _read_norm_rows(SOMEGA_NORMALIZATION_PATH)
    if _sha(ROOT / SOMEGA_NORMALIZATION_PATH) != SOMEGA_NORMALIZATION_SHA:
        raise RuntimeError("somega normalization artifact SHA mismatch")
    somega_mu = np.asarray([float(x["mu"]) for x in sn_rows], dtype=np.float64)
    somega_sigma = np.asarray([float(x["sigma"]) for x in sn_rows], dtype=np.float64)
    somega_const = np.asarray([str(x["is_constant"]).lower() == "true" for x in sn_rows])

    mu202 = np.zeros(ROUTER_NUMERIC_DIM, dtype=np.float64)
    sigma202 = np.ones(ROUTER_NUMERIC_DIM, dtype=np.float64)
    for k, idx in enumerate(ROUTER_SCALAR_IDX):
        mu202[idx] = router_mu[k]
        sigma202[idx] = 1.0 if router_const[k] else router_sigma[k]
    router_norm = {"mu": mu202, "sigma": sigma202,
                   "zero_sigma_rule": "sigma<1e-12 -> 1.0 then set 0.0"}
    somega_norm = {"mu": somega_mu, "sigma": somega_sigma,
                   "zero_sigma_rule": "sigma<1e-12 -> 1.0 then set 0.0"}

    # ---- §H EXPLICIT four-component device binding ------------------------ #
    # ``_WrapG`` is plain Python, NOT an ``nn.Module``, so ``system.to(device)``
    # cannot move the underlying G.  Each component is therefore moved and
    # VERIFIED explicitly on the canonical CUDA device.
    g.to(device)
    b_phi.to(device)
    r_psi.to(device)
    s_omega.to(device)

    def _param_device(m):
        devs = {str(p.device) for p in m.parameters()}
        if len(devs) != 1:
            raise RuntimeError(f"COMPONENT_PARAMETER_DEVICE_AMBIGUOUS: {sorted(devs)}")
        return devs.pop()

    component_device_binding = {}
    for name, m in (("G", g), ("B_phi", b_phi), ("R_psi", r_psi), ("S_omega", s_omega)):
        pd = _param_device(m)
        component_device_binding[name] = {
            "explicit_to_device_call": True,
            "parameter_device": pd,
            "on_canonical_device": bool(pd == str(device)),
        }
    if not all(v["on_canonical_device"] for v in component_device_binding.values()):
        raise RuntimeError(f"COMPONENT_DEVICE_BINDING_FAILED: {component_device_binding}")

    system = RAMedFiLMBARR(_WrapG(g), r_psi, b_phi, s_omega,
                           router_normalization=router_norm,
                           post_safety_normalization=somega_norm)
    system.to(device) if hasattr(system, "to") else None

    audit["component_device_binding"] = component_device_binding
    audit["component_inference_contexts"] = {
        k: dict(v) for k, v in COMPONENT_INFERENCE_CONTEXTS.items()}
    audit["component_contexts_not_interchangeable"] = COMPONENT_CONTEXTS_NOT_INTERCHANGEABLE
    audit["canonical_probability_operator"] = CANONICAL_PROBABILITY_OPERATOR["expression"]

    return {
        "system": system, "g": g, "b_phi": b_phi, "r_psi": r_psi, "s_omega": s_omega,
        "device": device, "router_norm": router_norm, "somega_norm": somega_norm,
        "router_normalizer_raw": {"mu": router_mu, "sigma": router_sigma,
                                  "constant_mask": router_const},
        "somega_normalizer_raw": {"mu": somega_mu, "sigma": somega_sigma,
                                  "constant_mask": somega_const},
        "component_device_binding": component_device_binding,
        "load_audit": audit,
    }


# --------------------------------------------------------------------------- #
# canonical tap recording (G feature maps for the 202-D extractor)
# --------------------------------------------------------------------------- #
_TAP_MODULES = {"bridge": "bridge", "decoder2": "decoder2", "decoder1": "decoder1"}


class TapRecorder:
    """Forward hooks capturing the three frozen G tap feature maps (inference-only)."""

    def __init__(self, model):
        self.store = {}
        self.handles = []
        for tap, attr in _TAP_MODULES.items():
            mod = getattr(model, attr)
            self.handles.append(mod.register_forward_hook(self._make(tap)))

    def _make(self, tap):
        def hook(_m, _i, out):
            self.store[tap] = out
        return hook

    def clear(self):
        self.store.clear()

    def close(self):
        for h in self.handles:
            h.remove()
        self.handles = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


# --------------------------------------------------------------------------- #
# canonical image preprocessing + ROI geometry
# --------------------------------------------------------------------------- #
def image_only_transform(image, size: int = REGIONAL_CANVAS_RESOLUTION) -> np.ndarray:
    from PIL import Image, ImageOps
    image = image.convert("RGB")
    width, height = image.size
    scale = min(size / width, size / height)
    rw, rh = max(1, round(width * scale)), max(1, round(height * scale))
    image = image.resize((rw, rh), Image.Resampling.BILINEAR)
    left, top = (size - rw) // 2, (size - rh) // 2
    image = ImageOps.expand(image, (left, top, size - rw - left, size - rh - top))
    arr = np.asarray(image, dtype=np.float32).copy()
    return np.transpose(arr, (2, 0, 1)) / 255.0


def crop_and_resize_vec(arr, geom, out_size):
    from PIL import Image as _I
    cy1, cy2 = int(geom["clip_y1"]), int(geom["clip_y2"])
    cx1, cx2 = int(geom["clip_x1"]), int(geom["clip_x2"])
    window = np.asarray(arr)[..., cy1:cy2, cx1:cx2]
    pads = [(0, 0)] * (window.ndim - 2) + [
        (int(geom["pad_top"]), int(geom["pad_bottom"])),
        (int(geom["pad_left"]), int(geom["pad_right"]))]
    window = np.pad(window, pads, mode="constant", constant_values=0)
    if window.ndim == 2:
        window = window[None, ...]
    channels = []
    for ch in window:
        pil = _I.fromarray(np.ascontiguousarray(ch, dtype=np.float32), mode="F")
        channels.append(np.asarray(pil.resize((out_size, out_size),
                                              _I.Resampling.BILINEAR), dtype=np.float32))
    return np.stack(channels, axis=0)


def fuse_full_field(p_global, refined_crop_256, geom):
    from PIL import Image as _I
    side = int(geom["crop_side_pixels"])
    clip_y1, clip_y2 = int(geom["clip_y1"]), int(geom["clip_y2"])
    clip_x1, clip_x2 = int(geom["clip_x1"]), int(geom["clip_x2"])
    pad_top, pad_left = int(geom["pad_top"]), int(geom["pad_left"])
    pil = _I.fromarray(np.ascontiguousarray(refined_crop_256, dtype=np.float32), mode="F")
    square = np.asarray(pil.resize((side, side), _I.Resampling.BILINEAR), dtype=np.float32)
    out = np.asarray(p_global, dtype=np.float32).copy()
    out[clip_y1:clip_y2, clip_x1:clip_x2] = square[pad_top:pad_top + (clip_y2 - clip_y1),
                                                   pad_left:pad_left + (clip_x2 - clip_x1)]
    return out


def somega_features(p_g_256, p_r_256, geom):
    from phase25f_post_safety_features import compute_numeric_features
    x0, x1 = int(geom["clip_x1"]), int(geom["clip_x2"])
    y0, y1 = int(geom["clip_y1"]), int(geom["clip_y2"])
    w_in = max(0, min(REGIONAL_CANVAS_RESOLUTION, x1) - max(0, x0))
    h_in = max(0, min(REGIONAL_CANVAS_RESOLUTION, y1) - max(0, y0))
    area_fraction = (w_in * h_in) / float(REGIONAL_CANVAS_RESOLUTION ** 2)
    return compute_numeric_features(p_g_256, p_r_256, area_fraction,
                                    float(geom["crop_side_pixels"]))


# --------------------------------------------------------------------------- #
# 202-D feature assembly (canonical extractor)
# --------------------------------------------------------------------------- #
def _assemble_202d(cmaps, P, roi_row):
    from src.features.barr_pre_refinement_features import build_feature_vector
    return build_feature_vector(cmaps, np.asarray(P, dtype=np.float32), roi_row)


def _roi_geometry_from_prob(p_global, threshold=ROI_PROPOSAL_THRESHOLD,
                            margin=ROI_FRACTIONAL_MARGIN):
    from src.data.barr_roi import roi_geometry
    return roi_geometry(np.asarray(p_global, dtype=np.float32),
                        threshold=threshold, margin=margin)


def _geo_row(geom):
    return {
        "clip_y1": int(geom["clip_y1"]), "clip_y2": int(geom["clip_y2"]),
        "clip_x1": int(geom["clip_x1"]), "clip_x2": int(geom["clip_x2"]),
        "crop_side_pixels": int(geom["crop_side_pixels"]),
    }


def _roi_row_from_window(y0, y1, x0, x1, crop_side_pixels):
    return {"clip_y1": int(y0), "clip_y2": int(y1),
            "clip_x1": int(x0), "clip_x2": int(x1),
            "crop_side_pixels": int(crop_side_pixels)}


def geom_from_proposal_row(pert_row, canvas: int = REGIONAL_CANVAS_RESOLUTION) -> dict:
    """Add the canonical clip/pad keys to a proposal-geometry row (pure geometry)."""
    y1, y2 = int(pert_row["y1"]), int(pert_row["y2"])
    x1, x2 = int(pert_row["x1"]), int(pert_row["x2"])
    return {
        "y1": y1, "y2": y2, "x1": x1, "x2": x2,
        "clip_y1": max(0, y1), "clip_y2": min(canvas, y2),
        "clip_x1": max(0, x1), "clip_x2": min(canvas, x2),
        "pad_top": max(0, -y1), "pad_bottom": max(0, y2 - canvas),
        "pad_left": max(0, -x1), "pad_right": max(0, x2 - canvas),
        "crop_side_pixels": int(pert_row["crop_side"]),
        "effective_magnification": canvas / float(max(1, int(pert_row["crop_side"]))),
        "margin": ROI_FRACTIONAL_MARGIN,
    }


def _synthetic_geometry(p_global) -> dict:
    """Deterministic geometry for synthetic smoke tensors (never used for science)."""
    g = _roi_geometry_from_prob(p_global, ROI_PROPOSAL_THRESHOLD, ROI_FRACTIONAL_MARGIN)
    if g is not None:
        return g
    return {
        "y1": 64, "y2": 448, "x1": 64, "x2": 448,
        "clip_y1": 64, "clip_y2": 448, "clip_x1": 64, "clip_x2": 448,
        "pad_top": 0, "pad_bottom": 0, "pad_left": 0, "pad_right": 0,
        "crop_side_pixels": 384, "effective_magnification": 512.0 / 384.0,
        "margin": ROI_FRACTIONAL_MARGIN,
    }


# --------------------------------------------------------------------------- #
# §D  CANONICAL G NUMERICAL EXECUTION (autocast fp16 / no_grad / device-bound)
# --------------------------------------------------------------------------- #
def canonical_autocast(device):
    """The frozen Phase27 AMP context: ``torch.amp.autocast(fp16), enabled``.

    Bound from reports/audits/phase27_autocast_rule_resolution.json (CASE_A) and
    reports/audits/phase29_val808_shared_global_cache_contract_v1_2.json.
    ``torch.inference_mode`` is deliberately NOT used (canonical value: false).
    """
    import torch
    dev_type = getattr(device, "type", None) or str(device).split(":")[0]
    return torch.amp.autocast(device_type=dev_type,
                              enabled=CANONICAL_G_AUTOCAST_ENABLED,
                              dtype=torch.float16)


def _assert_not_inference_mode():
    import torch
    if torch.is_inference_mode_enabled():
        raise RuntimeError("CANONICAL_G_NUMERICAL_VIOLATION__INFERENCE_MODE_ENABLED")


def component_inference_context(component: str):
    """The frozen per-component inference context (§I).

    G        : ``torch.no_grad()`` (autocast fp16 supplied separately)
    B_phi    : ``torch.inference_mode()`` with autocast DISABLED
    R_psi    : ``torch.inference_mode()`` with autocast DISABLED
    S_omega  : ``torch.inference_mode()`` with autocast DISABLED

    R_psi / B_phi / S_omega are NEVER placed under G's autocast context: autocast
    is a thread-local context manager and is simply not entered for them.
    """
    import torch
    if component == "G":
        return torch.no_grad()
    if component in ("B_phi", "R_psi", "S_omega"):
        return torch.inference_mode()
    raise KeyError(f"UNKNOWN_COMPONENT_INFERENCE_CONTEXT: {component}")


def component_autocast_disabled(component: str):
    """Explicit 'autocast disabled' context for the non-G components (§I)."""
    import torch
    if component == "G":
        raise ValueError("G_AUTOCAST_IS_ENABLED__DO_NOT_DISABLE")
    return torch.amp.autocast(device_type="cuda", enabled=False)


# --------------------------------------------------------------------------- #
# §C/§D/§E  THE ONE CANONICAL G-LOGITS-TO-PROBABILITY IMPLEMENTATION
# --------------------------------------------------------------------------- #
def canonical_probability_from_logits(logits):
    """THE canonical G probability operator (single central authority, §C/§E).

    Exactly the frozen predecessor expression::

        torch.sigmoid(logits.float()).cpu().numpy()      -> float32

    NumPy ``exp`` / manual logistic / scipy ``expit`` / float64 sigmoid
    intermediates are FORBIDDEN here.  float16 is applied only where the frozen
    cache requires persistence, and always AFTER the float32 result.
    """
    import torch
    t = logits if torch.is_tensor(logits) else torch.from_numpy(
        np.ascontiguousarray(np.asarray(logits, dtype=np.float32)))
    prob = torch.sigmoid(t.float())
    if prob.ndim == 4 and prob.shape[1] == 1:
        prob = prob[:, 0]
    return prob.cpu().numpy().astype(np.float32, copy=False)


def canonical_g_forward_batched(ctx, x, t):
    """ONE canonical batched G forward.

    ``x`` : torch float32 ``[B, 3, 512, 512]`` already on ``ctx['device']``.
    ``t`` : torch long ``[B]`` already on ``ctx['device']`` (DEVICE-BOUND task ids).
    Runs under ``torch.no_grad()`` + ``torch.amp.autocast(fp16)`` with
    ``torch.inference_mode`` OFF, and captures the three frozen taps.

    Returns BOTH the raw ``logits`` AND the canonical ``probability`` computed
    INSIDE the canonical G forward context (§D).  No caller may recompute the
    sigmoid; every downstream path consumes the returned ``probability``.
    """
    import torch
    _assert_not_inference_mode()
    if not torch.is_tensor(x) or not torch.is_tensor(t):
        raise TypeError("CANONICAL_G_REQUIRES_TORCH_TENSORS")
    if x.device != t.device:
        raise RuntimeError("CANONICAL_G_TASK_ID_DEVICE_MISMATCH")
    if x.shape[0] != t.shape[0]:
        raise RuntimeError("CANONICAL_G_BATCH_TASK_ID_LENGTH_MISMATCH")
    if x.shape[0] > CANONICAL_G_BATCH_SIZE:
        raise RuntimeError("CANONICAL_G_BATCH_SIZE_EXCEEDED")
    with torch.no_grad(), canonical_autocast(ctx["device"]), TapRecorder(ctx["g"]) as rec:
        g_out = ctx["g"](x, t)
        # §D: the canonical probability is produced INSIDE the canonical G
        # forward context, directly from the frozen operator.  No other site
        # may convert canonical G logits to probability.
        probability = canonical_probability_from_logits(g_out)
        taps = {k: v.detach().float().cpu().numpy() for k, v in rec.store.items()}
    logits = g_out.detach().float().cpu().numpy() if torch.is_tensor(g_out) else np.asarray(g_out)
    if logits.ndim == 4 and logits.shape[1] == 1:
        logits = logits[:, 0]
    return {"logits": logits,
            "probability": probability,
            "probability_float32_numpy": probability,
            "probability_dtype": str(np.asarray(probability).dtype),
            "probability_operator": CANONICAL_PROBABILITY_OPERATOR["id"],
            "taps": taps,
            "batch_size": int(x.shape[0]),
            "device": str(x.device),
            "autocast_enabled": bool(CANONICAL_G_AUTOCAST_ENABLED),
            "autocast_dtype": CANONICAL_G_AUTOCAST_DTYPE,
            "inference_mode": False}


def canonical_images_tensor(ctx, images_np):
    """Stack a numpy ``[B,3,512,512]`` float32 batch onto the canonical device."""
    import torch
    arr = np.ascontiguousarray(np.asarray(images_np, dtype=np.float32))
    if arr.ndim == 3:
        arr = arr[None]
    return torch.from_numpy(arr).to(ctx["device"])


def canonical_task_ids_tensor(ctx, task_ids):
    """Device-bound long task-id tensor (D6 repair)."""
    import torch
    return torch.tensor([int(v) for v in task_ids], dtype=torch.long, device=ctx["device"])


# --------------------------------------------------------------------------- #
# §F/§H  THE ONE CANONICAL LEARNED-COMPONENT CORE (shared by science and smoke)
# --------------------------------------------------------------------------- #
def _final_source_of(state: str) -> str:
    """Canonical final-source mapping: only EXECUTE_THEN_ACCEPT yields REFINED."""
    return "REFINED" if state == "EXECUTE_THEN_ACCEPT" else "GLOBAL"


def _core_result(system, state, router_decision_value, final_prob, delta_hat, window,
                 actual_r_psi_forwards, actual_s_omega_forwards, global_forwards, geom,
                 router_vector, logit=None, accept_prob=None,
                 policy_control=False, forced_router_score=False,
                 forced_safety_logit=False,
                 refined_output=None, post_safety_features=None,
                 final_s_omega_input=None, post_safety_numeric_normalized=None) -> dict:
    """Assemble the canonical per-sample result.

    Mirrors ``RAMedFiLMBARR._result`` for every shared field, then ADDS the
    strictly separated ``router_decision`` (SKIP/EXECUTE), the ROI geometry, the
    ACTUAL forward counts and the lightweight 202-D router-vector diagnostics.

    §C: ``actual_r_psi_forwards`` / ``actual_s_omega_forwards`` are ACTUAL model
    invocations.  Control injection never increments them, so a forced-safety
    policy control reports ``s_omega_forward_count == 0``.

    ``router_decision`` is NEVER derived from ``state``.
    """
    prob = np.asarray(final_prob, dtype=np.float32)
    res = system._result(state, prob,
                         {"global": int(global_forwards),
                          "refiner": int(actual_r_psi_forwards),
                          "s_omega": int(actual_s_omega_forwards)},
                         delta_hat, window, logit=logit, accept_prob=accept_prob)
    res["router_decision"] = router_decision_value            # SKIP | EXECUTE
    res["final_binary"] = (prob >= float(system.segmentation_output_threshold)).astype(np.float32)
    res["roi_available"] = geom is not None
    res["geometry"] = geom
    # §G: 202-D router-vector diagnostics bound to the ACTUAL rf202.
    if router_vector is None:
        res["router_vector_dim"] = None
        res["router_vector_shape"] = None
        res["router_vector_finite"] = False
        res["router_vector_min"] = None
        res["router_vector_max"] = None
    else:
        rv = np.asarray(router_vector, dtype=np.float32).reshape(-1)
        res["router_vector_dim"] = int(rv.shape[0])
        res["router_vector_shape"] = list(np.asarray(router_vector).shape)
        res["router_vector_finite"] = bool(np.isfinite(rv).all())
        res["router_vector_min"] = (float(rv.min()) if rv.size else None)
        res["router_vector_max"] = (float(rv.max()) if rv.size else None)
    # §E: lightweight synthetic-smoke diagnostics (not scientific evidence).
    if refined_output is not None:
        ro = np.asarray(refined_output, dtype=np.float32)
        res["refined_output_finite"] = bool(np.isfinite(ro).all())
        res["refined_output_shape"] = list(ro.shape)
        # §D24 (v1.9): R_psi output is a sigmoid PROBABILITY map.  Expose the
        # exact shape and value range so they can be BOUND to smoke success.
        res["refined_output_is_probability"] = True
        res["refined_output_in_unit_interval"] = bool(
            ro.size > 0 and float(ro.min()) >= 0.0 and float(ro.max()) <= 1.0)
    else:
        res["refined_output_finite"] = None
        res["refined_output_shape"] = None
        res["refined_output_is_probability"] = None
        res["refined_output_in_unit_interval"] = None
    if post_safety_features is not None:
        ps = np.asarray(post_safety_features, dtype=np.float64).reshape(-1)
        res["post_safety_feature_dim"] = int(ps.shape[0])
        res["post_safety_features_finite"] = bool(np.isfinite(ps).all())
    else:
        res["post_safety_feature_dim"] = None
        res["post_safety_features_finite"] = None
    # §D24 (v1.9): expose the ACTUAL final S_omega input (normalized numeric
    # features + task one-hot) — exact schema dimension and finiteness.
    if final_s_omega_input is not None:
        fsi = np.asarray(final_s_omega_input, dtype=np.float64).reshape(-1)
        res["final_s_omega_input_dim"] = int(fsi.shape[0])
        res["final_s_omega_input_finite"] = bool(np.isfinite(fsi).all())
    else:
        res["final_s_omega_input_dim"] = None
        res["final_s_omega_input_finite"] = None
    if post_safety_numeric_normalized is not None:
        psn = np.asarray(post_safety_numeric_normalized, dtype=np.float64).reshape(-1)
        res["post_safety_numeric_normalized_dim"] = int(psn.shape[0])
        res["post_safety_numeric_normalized_finite"] = bool(np.isfinite(psn).all())
    else:
        res["post_safety_numeric_normalized_dim"] = None
        res["post_safety_numeric_normalized_finite"] = None
    res["actual_r_psi_forward_count"] = int(actual_r_psi_forwards)
    res["actual_s_omega_forward_count"] = int(actual_s_omega_forwards)
    res["policy_control"] = bool(policy_control)
    res["forced_router_score"] = bool(forced_router_score)
    res["forced_safety_logit"] = bool(forced_safety_logit)
    res["not_applicable"] = False
    return res


def canonical_learned_core(ctx, image_b, task_id, *,
                           g_logits=None, g_probability=None, g_taps=None,
                           p_global_override=None,
                           router_features_202_override=None,
                           proposal_geometry=None,
                           roi_window=None,
                           action_available=None,
                           forced_delta_hat_final=None,
                           forced_s_omega_logit=None,
                           counters=None) -> dict:
    """ONE canonical learned-component core.  Used by BOTH science and smoke.

    Accepts already-authorized / preprocessed tensor inputs and an optional
    proposal-geometry override.  Reads NO protected data and performs NO IO.

    RUNTIME ORDER (frozen; non-negotiable — §F):

        G -> p_global -> ROI geometry -> canonical 202-D -> B_phi
          -> A8/C9 utility decision  (router_decision in {SKIP, EXECUTE})
          -> IF SKIP:     R_psi forwards = 0, S_omega forwards = 0, final = global
          -> IF EXECUTE:  R_psi -> post-safety 16-D -> S_omega
                          -> ACCEPT: final = canonical regional/fused output
                          -> REJECT: final = global

    There is NO speculative / pre-decision R_psi forward anywhere.

    ``forced_delta_hat_final`` / ``forced_s_omega_logit`` are CONTROL-ONLY
    injection points used exclusively by the smoke branch controls (§K) to force
    deterministic branch coverage; the decision is still made by the canonical
    ``canonical_utility`` / threshold callables.  They are never used by science.
    """
    import torch
    from src.models.barr.ra_medfilm_barr import (canonical_utility,
                                                 TAU_C8_FINAL_FLOAT)
    system = ctx["system"]
    device = ctx["device"]
    counters = counters if counters is not None else {}
    task_id = int(task_id)
    g_forwards = 0
    # §C: ACTUAL learned-component forward counts.  Incremented ONLY immediately
    # after a real module invocation; control injection never increments these.
    actual_r_psi_forwards = 0
    actual_s_omega_forwards = 0
    policy_control = bool(forced_delta_hat_final is not None
                          or forced_s_omega_logit is not None)
    forced_router_score = bool(forced_delta_hat_final is not None)
    forced_safety_logit = bool(forced_s_omega_logit is not None)

    # ---- STEP 1: GLOBAL STAGE (canonical numerical semantics) -------------- #
    if p_global_override is not None:
        p_global = np.asarray(p_global_override, dtype=np.float32)
        taps = g_taps
    else:
        if g_logits is None:
            x = image_b if torch.is_tensor(image_b) else torch.from_numpy(
                np.ascontiguousarray(np.asarray(image_b, dtype=np.float32)))
            if x.ndim == 3:
                x = x[None]
            x = x.to(device)
            t = torch.tensor([task_id], dtype=torch.long, device=device)
            out = canonical_g_forward_batched(ctx, x, t)
            logits = out["logits"][0]
            # §D: consume the canonical probability produced INSIDE the G context.
            p_global = np.asarray(out["probability"][0], dtype=np.float32)
            taps = {k: v[0] for k, v in out["taps"].items()}
            g_forwards = 1
        else:
            logits = np.asarray(g_logits, dtype=np.float32)
            taps = g_taps
            # The caller supplies the canonical probability whenever it has it;
            # otherwise the ONE central operator produces it.  A manual NumPy
            # logistic is never used here.
            p_global = (np.asarray(g_probability, dtype=np.float32)
                        if g_probability is not None
                        else canonical_probability_from_logits(logits))
    counters["g_forwards"] = counters.get("g_forwards", 0) + g_forwards

    # ---- STEP 2: ROI geometry (GT-free, 0.30 proposal threshold) ----------- #
    if proposal_geometry is not None:
        geom = dict(proposal_geometry)
        window = (int(geom["clip_y1"]), int(geom["clip_y2"]),
                  int(geom["clip_x1"]), int(geom["clip_x2"]))
    else:
        geom = _roi_geometry_from_prob(p_global, ROI_PROPOSAL_THRESHOLD, ROI_FRACTIONAL_MARGIN)
        window = (None if geom is None else
                  (int(geom["clip_y1"]), int(geom["clip_y2"]),
                   int(geom["clip_x1"]), int(geom["clip_x2"])))
    if roi_window is not None:
        window = roi_window
    available = (geom is not None) if action_available is None else bool(action_available)

    # ---- STEP 3: canonical 202-D ------------------------------------------ #
    if router_features_202_override is not None:
        rf202 = np.asarray(router_features_202_override, dtype=np.float32).reshape(-1)
    else:
        if taps is None:
            raise ValueError("CANONICAL_CORE_REQUIRES_202D_OR_G_TAPS")
        roi_row = _geo_row(geom) if geom is not None else _roi_row_from_window(
            0, p_global.shape[0], 0, p_global.shape[1], p_global.shape[0])
        rf202 = _assemble_202d(taps, p_global, roi_row)

    # §G: FAIL CLOSED on the ACTUAL canonical 202-D vector, BEFORE B_phi.
    rf202 = np.asarray(rf202, dtype=np.float32).reshape(-1)
    if rf202.shape != (ROUTER_NUMERIC_DIM,):
        raise ValueError(f"ROUTER_VECTOR_DIM_VIOLATION: {rf202.shape} != ({ROUTER_NUMERIC_DIM},)")
    if not bool(np.isfinite(rf202).all()):
        raise ValueError("ROUTER_VECTOR_NOT_FINITE")

    # ---- STEP 4: ACTION-UNAVAILABLE -> FORCED_SKIP ------------------------- #
    if not available:
        return _core_result(system, "FORCED_SKIP", "SKIP", p_global, None, window,
                            actual_r_psi_forwards=0, actual_s_omega_forwards=0,
                            global_forwards=g_forwards, geom=geom,
                            router_vector=rf202,
                            policy_control=policy_control,
                            forced_router_score=forced_router_score,
                            forced_safety_logit=forced_safety_logit)

    # ---- STEP 5: B_phi -> A8/C9 ROUTER DECISION --------------------------- #
    # §I: B_phi runs under torch.inference_mode() with autocast DISABLED —
    # NEVER under G's autocast context.
    if forced_delta_hat_final is not None:
        delta_hat_final = float(forced_delta_hat_final)
    else:
        rf_norm = system._apply_norm(np.asarray(rf202, dtype=np.float32).reshape(-1),
                                     system.router_normalization)
        with component_inference_context("B_phi"), component_autocast_disabled("B_phi"):
            x_num = torch.from_numpy(np.ascontiguousarray(rf_norm))[None].to(device)
            t_ids = torch.tensor([task_id], dtype=torch.long, device=device)
            delta_hat_final = float(system.benefit_router(x_num, t_ids).reshape(-1)[0])
        counters["b_phi_forwards"] = counters.get("b_phi_forwards", 0) + 1
    util = canonical_utility(delta_hat_final)
    router_decision_value = "EXECUTE" if util >= TAU_C8_FINAL_FLOAT else "SKIP"

    # ---- STEP 6: SKIP BRANCH (R_psi = 0, S_omega = 0, final = global) ----- #
    if router_decision_value == "SKIP":
        return _core_result(system, "SKIP_GLOBAL", "SKIP", p_global, delta_hat_final, window,
                            actual_r_psi_forwards=0, actual_s_omega_forwards=0,
                            global_forwards=g_forwards, geom=geom,
                            router_vector=rf202,
                            policy_control=policy_control,
                            forced_router_score=forced_router_score,
                            forced_safety_logit=forced_safety_logit)

    # ---- STEP 7: EXECUTE BRANCH -> R_psi runs ONLY NOW -------------------- #
    # §I: R_psi runs under torch.inference_mode() with autocast DISABLED.
    rgb = image_b[0].detach().float().cpu().numpy() if torch.is_tensor(image_b) else \
        np.asarray(image_b, dtype=np.float32)[0]
    rgb_crop = crop_and_resize_vec(rgb, geom, REGIONAL_INPUT_RESOLUTION)
    prob_crop = crop_and_resize_vec(p_global, geom, REGIONAL_INPUT_RESOLUTION)
    rin = np.concatenate([np.asarray(rgb_crop, dtype=np.float32),
                          np.asarray(prob_crop, dtype=np.float32)], axis=0)
    with component_inference_context("R_psi"), component_autocast_disabled("R_psi"):
        rin_t = torch.from_numpy(np.ascontiguousarray(rin))[None].to(device)
        refined = torch.sigmoid(ctx["r_psi"](rin_t).float())[0, 0].detach().float().cpu().numpy()
    # §C: increment the ACTUAL R_psi forward count ONLY after the real call above.
    actual_r_psi_forwards += 1
    counters["r_psi_forwards"] = counters.get("r_psi_forwards", 0) + 1

    # ---- STEP 8: post-safety 16-D features -------------------------------- #
    pg_crop = np.asarray(prob_crop, dtype=np.float32)
    pg_crop = pg_crop[0] if pg_crop.ndim == 3 else pg_crop
    pr_crop = np.asarray(refined, dtype=np.float32)
    pr_crop = pr_crop[0] if pr_crop.ndim == 3 else pr_crop
    sf16 = np.asarray(somega_features(pg_crop, pr_crop, geom), dtype=np.float64).reshape(-1)

    # ---- STEP 9: S_omega runs ONLY NOW ------------------------------------ #
    # §I: S_omega runs under torch.inference_mode() with autocast DISABLED.
    # §D24 (v1.9): capture the ACTUAL normalized numeric features and the ACTUAL
    # final S_omega input vector (post-norm + task one-hot) for exact-schema
    # smoke validation.  These remain None on the forced (bypassed) branch.
    final_s_omega_input_capture = None
    post_safety_numeric_normalized_capture = None
    if forced_s_omega_logit is not None:
        # §C/§D: CONTROL INJECTION.  The real S_omega module is BYPASSED, so the
        # ACTUAL S_omega forward count MUST remain 0.
        logit = float(forced_s_omega_logit)
    else:
        sf_norm = system._apply_norm(np.asarray(sf16, dtype=np.float32),
                                     system.post_safety_normalization)
        full = np.concatenate([sf_norm, system._onehot_task(task_id)], axis=0)
        final_s_omega_input_capture = np.asarray(full, dtype=np.float64).reshape(-1)
        post_safety_numeric_normalized_capture = np.asarray(sf_norm,
                                                            dtype=np.float64).reshape(-1)
        with component_inference_context("S_omega"), component_autocast_disabled("S_omega"):
            logit = float(system.post_safety(
                torch.from_numpy(np.ascontiguousarray(full))[None].to(device)).reshape(-1)[0])
        # §C: increment the ACTUAL S_omega forward count ONLY after the real call.
        actual_s_omega_forwards += 1
        counters["s_omega_forwards"] = counters.get("s_omega_forwards", 0) + 1
    accept_prob = float(torch.sigmoid(torch.tensor(float(logit), device=device)).item())

    # ---- STEP 10: ACCEPT / REJECT ----------------------------------------- #
    if accept_prob >= float(system.s_omega_accept_threshold):
        fused = system._fuse_global_with_regional(p_global, refined, window)
        return _core_result(system, "EXECUTE_THEN_ACCEPT", "EXECUTE", fused, delta_hat_final,
                            window,
                            actual_r_psi_forwards=actual_r_psi_forwards,
                            actual_s_omega_forwards=actual_s_omega_forwards,
                            global_forwards=g_forwards, geom=geom, router_vector=rf202,
                            logit=logit, accept_prob=accept_prob,
                            policy_control=policy_control,
                            forced_router_score=forced_router_score,
                            forced_safety_logit=forced_safety_logit,
                            refined_output=refined, post_safety_features=sf16,
                            final_s_omega_input=final_s_omega_input_capture,
                            post_safety_numeric_normalized=post_safety_numeric_normalized_capture)
    return _core_result(system, "EXECUTE_THEN_REJECT", "EXECUTE", p_global, delta_hat_final,
                        window,
                        actual_r_psi_forwards=actual_r_psi_forwards,
                        actual_s_omega_forwards=actual_s_omega_forwards,
                        global_forwards=g_forwards, geom=geom, router_vector=rf202,
                        logit=logit, accept_prob=accept_prob,
                        policy_control=policy_control,
                        forced_router_score=forced_router_score,
                        forced_safety_logit=forced_safety_logit,
                        refined_output=refined, post_safety_features=sf16,
                        final_s_omega_input=final_s_omega_input_capture,
                        post_safety_numeric_normalized=post_safety_numeric_normalized_capture)


def proposal_core_adapter(ctx, image_b, task_id, *, proposal_geometry,
                          g_logits=None, g_probability=None, g_taps=None,
                          p_global_override=None,
                          router_features_202_override=None,
                          counters=None) -> dict:
    """The canonical PROPOSAL adapter — shared by science and smoke (§H).

    Empty / None proposal -> the frozen NOT_APPLICABLE_EMPTY_PROPOSAL record with
    ZERO R_psi forwards, ZERO S_omega forwards and NO replacement geometry.
    Non-empty proposal   -> the SAME canonical core with the perturbed geometry.
    """
    counters = counters if counters is not None else {}
    if proposal_geometry is None:
        counters["empty_proposal_not_applicable"] = \
            counters.get("empty_proposal_not_applicable", 0) + 1
        return {
            "state": C.EMPTY_PROPOSAL_HANDLING,
            "router_decision": None,
            "final_probability": None,
            "final_binary": None,
            "refiner_forward_count": 0,
            "s_omega_forward_count": 0,
            "global_forward_count": 0,
            "delta_hat_final": None,
            "post_safety_logit": None,
            "post_safety_accept_probability": None,
            "roi_window": None,
            "roi_available": False,
            "geometry": None,
            "router_vector_shape": None,
            "not_applicable": True,
            "replacement_geometry_generated": False,
        }
    out = canonical_learned_core(ctx, image_b, task_id, g_logits=g_logits,
                                 g_probability=g_probability, g_taps=g_taps,
                                 p_global_override=p_global_override,
                                 router_features_202_override=router_features_202_override,
                                 proposal_geometry=proposal_geometry,
                                 action_available=True, counters=counters)
    out["replacement_geometry_generated"] = False
    return out


# --------------------------------------------------------------------------- #
# §G  REAL clean-sample evaluation wrapper (science-side IO only)
# --------------------------------------------------------------------------- #
def _clean_row_index():
    rows = canonical_population_rows()
    return rows, {r["sample_id"]: r for r in rows}


def _load_clean_image_tensor(row):
    from PIL import Image
    from src.data.transforms import SegmentationTransform
    img = Image.open(row["image_path"]).convert("RGB")
    tf = SegmentationTransform(size=512, train=False, image_mode="RGB")
    image_t, _mask_t, _meta = tf(img, Image.new("L", img.size, 0))
    return image_t


def _load_val_gt(row):
    from PIL import Image
    return _mask_preprocess(Image.open(row["mask_path"]))


# --------------------------------------------------------------------------- #
# §D  FROZEN REALIZATION PLANS (sample-first iteration source)
# --------------------------------------------------------------------------- #
def image_realization_plan() -> list:
    """The 16 non-clean image realizations (CLEAN is generated once in STAGE 1)."""
    plan = []
    for cond in NONCLEAN_DETERMINISTIC_IMAGE_CONDITIONS:
        plan.append({"condition": cond, "base_seed": None, "derived_seed": None,
                     "is_noise": False})
    for cond in NONCLEAN_NOISE_IMAGE_CONDITIONS:
        for bs in C.NOISE_BASE_SEEDS:
            plan.append({"condition": cond, "base_seed": int(bs),
                         "derived_seed": None, "is_noise": True})
    if len(plan) != NONCLEAN_IMAGE_REALIZATIONS_PER_SAMPLE:
        raise AssertionError(
            f"image realization plan {len(plan)} != {NONCLEAN_IMAGE_REALIZATIONS_PER_SAMPLE}")
    return plan


def proposal_realization_plan() -> list:
    """The 6 non-clean proposal realizations."""
    plan = [{"proposal_condition": cond} for cond in NONCLEAN_PROPOSAL_CONDITIONS]
    if len(plan) != NONCLEAN_PROPOSAL_CONDITIONS_PER_SAMPLE:
        raise AssertionError(
            f"proposal realization plan {len(plan)} != {NONCLEAN_PROPOSAL_CONDITIONS_PER_SAMPLE}")
    return plan


def _derived_seed_for(cond: str, base_seed, sid: str):
    """Per-sample derived seed for Gaussian-noise realizations (v1.1 32-bit rule)."""
    if base_seed is None:
        return None
    return int(C.derive_noise_seed(int(base_seed), sid))


def proposal_geometry_plan(clean_geom):
    """The 6 perturbed proposal geometries derived from the CLEAN geometry.

    PURE GEOMETRY — no model, no G, no learned component.  Precomputed during the
    clean G pass so the proposal stage never re-runs G (frozen contract:
    ``G_recomputed_for_proposal_perturbation = False``).
    """
    if clean_geom is None:
        return None
    base = {"y1": int(clean_geom["y1"]), "y2": int(clean_geom["y2"]),
            "x1": int(clean_geom["x1"]), "x2": int(clean_geom["x2"]),
            "crop_side": int(clean_geom["crop_side_pixels"]),
            "center_y": (int(clean_geom["y1"]) + int(clean_geom["y2"])) / 2.0,
            "center_x": (int(clean_geom["x1"]) + int(clean_geom["x2"])) / 2.0}
    out = OrderedDict()
    for cond in NONCLEAN_PROPOSAL_CONDITIONS:
        pert = C.apply_proposal_condition(base, cond,
                                          REGIONAL_CANVAS_RESOLUTION,
                                          REGIONAL_CANVAS_RESOLUTION)
        out[cond] = geom_from_proposal_row(pert)
    return out


# --------------------------------------------------------------------------- #
# §E/§G  BUILDER — a FULLY-POPULATED sample-level image result row
# --------------------------------------------------------------------------- #
_IMAGE_ROW_REQUIRED = [
    "sample_id", "domain", "task_id", "condition", "base_seed", "derived_seed",
    "clean_dice", "perturbed_dice", "paired_delta_dice",
    "prediction_consistency_dice", "clean_route_state", "perturbed_route_state",
    "route_state_changed", "clean_router_decision", "perturbed_router_decision",
    "router_decision_changed", "final_source", "perturbed_final_source",
    "perturbed_iou", "perturbed_hd95", "perturbed_hd95_valid",
]


def build_image_result_row(sid, domain, task_id, cond, base_seed, derived_seed,
                           clean_dice, perturbed_dice, prediction_consistency_dice,
                           clean_route_state, perturbed_route_state,
                           clean_router_decision, perturbed_router_decision,
                           final_source, perturbed_final_source,
                           perturbed_iou=None, perturbed_hd95=None,
                           perturbed_hd95_valid=None) -> dict:
    """Build a sample-level image-perturbation result row.  FAILS CLOSED on schema loss."""
    for k, v in (("sample_id", sid), ("domain", domain), ("task_id", task_id)):
        if v is None:
            raise ValueError(f"SCIENCE_ROW_SCHEMA_LOSS: missing {k}")
    # §G: router_decision is structurally SEPARATE from final_state.
    for label, v in (("clean_router_decision", clean_router_decision),
                     ("perturbed_router_decision", perturbed_router_decision)):
        if v not in ROUTER_DECISIONS:
            raise ValueError(f"ROUTER_DECISION_NOT_CANONICAL: {label}={v!r}")
    for label, v in (("clean_route_state", clean_route_state),
                     ("perturbed_route_state", perturbed_route_state)):
        if v not in ROUTE_STATES_FULL:
            raise ValueError(f"ROUTE_STATE_NOT_CANONICAL: {label}={v!r}")
    row = {
        "sample_id": sid, "domain": domain, "task_id": int(task_id),
        "condition": cond, "base_seed": base_seed, "derived_seed": derived_seed,
        "clean_dice": float(clean_dice), "perturbed_dice": float(perturbed_dice),
        "paired_delta_dice": float(perturbed_dice) - float(clean_dice),
        "prediction_consistency_dice": float(prediction_consistency_dice),
        "clean_route_state": clean_route_state, "perturbed_route_state": perturbed_route_state,
        "route_state_changed": bool(clean_route_state != perturbed_route_state),
        "clean_router_decision": clean_router_decision,
        "perturbed_router_decision": perturbed_router_decision,
        "router_decision_changed": bool(clean_router_decision != perturbed_router_decision),
        "final_source": final_source, "perturbed_final_source": perturbed_final_source,
        "perturbed_iou": perturbed_iou, "perturbed_hd95": perturbed_hd95,
        "perturbed_hd95_valid": perturbed_hd95_valid,
    }
    missing = _row_missing_required(row)
    if missing:
        raise ValueError(f"SCIENCE_ROW_SCHEMA_LOSS: {missing}")
    return row


def _row_missing_required(row: dict) -> list:
    return [k for k in _IMAGE_ROW_REQUIRED
            if k not in row or (k in ("sample_id", "domain", "task_id") and row[k] is None)]


def _row_has_identity(row: dict) -> bool:
    return row.get("sample_id") is not None and row.get("task_id") is not None


# --------------------------------------------------------------------------- #
# §D/§E  STAGE 1a — CANONICAL BATCHED CLEAN G PASS + PHASE27 REPRODUCTION GATE
# --------------------------------------------------------------------------- #
def _generate_clean_g_reference(ctx, counters):
    """Canonical batched G over VAL808 -> per-sample clean artifacts + f16 cache.

    Produces, in canonical order:
        p_global[sid]        float32 clean global probability
        geometry[sid]        frozen 0.30 ROI geometry (or None)
        rf202[sid]           canonical 202-D vector
        proposal_geometry[sid][cond]  precomputed perturbed geometry (pure geometry)
        proposal_rf202[sid][cond]     precomputed perturbed 202-D vector
        p_global_f16         [808,512,512] float16 (the §E gate target)
    """
    rows, row_index = _clean_row_index()
    sample_order = [r["sample_id"] for r in rows]
    idx_of = {sid: i for i, sid in enumerate(sample_order)}

    p_global_store = {}
    geom_store = {}
    rf202_store = {}
    prop_geom_store = {}
    prop_rf202_store = {}
    p_f16 = np.zeros((len(sample_order), REGIONAL_CANVAS_RESOLUTION,
                      REGIONAL_CANVAS_RESOLUTION), dtype=np.float16)

    for _dom, sids in canonical_batch_partition(rows):
        for batch in _chunks(sids, CANONICAL_G_BATCH_SIZE):
            images = np.stack([np.asarray(_load_clean_image_tensor(row_index[sid]).numpy(),
                                          dtype=np.float32) for sid in batch])
            x = canonical_images_tensor(ctx, images)
            t = canonical_task_ids_tensor(ctx, [int(row_index[sid]["task_id"]) for sid in batch])
            out = canonical_g_forward_batched(ctx, x, t)
            counters["clean_g_forwards"] = counters.get("clean_g_forwards", 0) + len(batch)
            counters["clean_g_batch_forwards"] = counters.get("clean_g_batch_forwards", 0) + 1
            counters["unique_raw_val_images"] = counters.get("unique_raw_val_images", 0) + len(batch)

            for bi, sid in enumerate(batch):
                logits = np.asarray(out["logits"][bi], dtype=np.float32)
                # §D: consume the canonical probability produced INSIDE the G context.
                p_global = np.asarray(out["probability"][bi], dtype=np.float32)
                taps = {k: np.asarray(v[bi]) for k, v in out["taps"].items()}
                # float16 is applied only for the frozen cache persistence, AFTER
                # the float32 canonical result.
                p_f16[idx_of[sid]] = p_global.astype(np.float16)

                geom = _roi_geometry_from_prob(p_global, ROI_PROPOSAL_THRESHOLD,
                                               ROI_FRACTIONAL_MARGIN)
                roi_row = _geo_row(geom) if geom is not None else _roi_row_from_window(
                    0, p_global.shape[0], 0, p_global.shape[1], p_global.shape[0])
                rf202 = _assemble_202d(taps, p_global, roi_row)

                p_global_store[sid] = p_global
                geom_store[sid] = geom
                rf202_store[sid] = rf202

                pgeom = proposal_geometry_plan(geom)
                prop_geom_store[sid] = pgeom
                if pgeom is None:
                    prop_rf202_store[sid] = None
                else:
                    prop_rf202_store[sid] = OrderedDict()
                    for cond, pg in pgeom.items():
                        prop_rf202_store[sid][cond] = _assemble_202d(
                            taps, p_global, _geo_row(pg))

    if len(sample_order) != AUTHORIZED_POPULATION_N:
        raise AssertionError(
            f"CLEAN_G_POPULATION_MISMATCH: {len(sample_order)} != {AUTHORIZED_POPULATION_N}")
    if counters.get("clean_g_batch_forwards", 0) != CANONICAL_BATCH_FORWARDS_TOTAL:
        raise AssertionError(
            f"CLEAN_G_BATCH_COUNT_MISMATCH: {counters.get('clean_g_batch_forwards', 0)} "
            f"!= {CANONICAL_BATCH_FORWARDS_TOTAL}")

    return {
        "generated": True,
        "n": len(sample_order),
        "sample_order": sample_order,
        "p_global": p_global_store,
        "geometry": geom_store,
        "rf202": rf202_store,
        "proposal_geometry": prop_geom_store,
        "proposal_rf202": prop_rf202_store,
        "p_global_f16": p_f16,
        "persist_keys": [
            "clean_p_global", "clean_roi_geometry", "clean_202d",
            "clean_router_score", "clean_router_decision", "clean_safety_state",
            "clean_final_source", "clean_final_binary_mask",
            "clean_dice", "clean_iou", "clean_hd95"],
        "clean_final_binary_mask_authority": "binary float32[512,512] per sample",
        "reconstruction_from_scalars_prohibited": True,
        "g_numerical_semantics": {
            "device": CANONICAL_G_DEVICE,
            "autocast_enabled": CANONICAL_G_AUTOCAST_ENABLED,
            "autocast_dtype": CANONICAL_G_AUTOCAST_DTYPE,
            "no_grad": CANONICAL_G_NO_GRAD,
            "inference_mode": CANONICAL_G_INFERENCE_MODE,
            "batch_size": CANONICAL_G_BATCH_SIZE,
            "sample_order": CANONICAL_SAMPLE_ORDER,
            "batch_partition": CANONICAL_BATCH_PARTITION,
            "batch_forwards": counters.get("clean_g_batch_forwards", 0),
            "sample_forwards": counters.get("clean_g_forwards", 0),
        },
    }


def _phase27_global_reproduction_gate(clean_p_f16, sample_order, counters) -> dict:
    """§E: compare the new clean G f16 cache against the frozen Phase27 authority."""
    counters["clean_g_reproduction_gate_invocations"] = \
        counters.get("clean_g_reproduction_gate_invocations", 0) + 1
    ref_path = ROOT / PHASE27_GLOBAL_PROB_AUTHORITY["path"]
    out = {
        "reference_path": PHASE27_GLOBAL_PROB_AUTHORITY["path"],
        "reference_sha256": (_sha(ref_path) if ref_path.exists() else None),
        "reference_sha256_expected": PHASE27_GLOBAL_PROB_AUTHORITY["sha256"],
        "preferred": CLEAN_G_REPRODUCTION_GATE["preferred"],
    }
    if not ref_path.exists():
        out.update({"pass": False, "bit_identical": False,
                    "reason": "PHASE27_GLOBAL_AUTHORITY_ABSENT"})
        return out
    if out["reference_sha256"] != PHASE27_GLOBAL_PROB_AUTHORITY["sha256"]:
        out.update({"pass": False, "bit_identical": False,
                    "reason": "PHASE27_GLOBAL_AUTHORITY_SHA_MISMATCH"})
        return out

    ref = np.load(ref_path)
    out["reference_shape"] = list(ref.shape)
    out["reference_dtype"] = str(ref.dtype)
    out["generated_shape"] = list(np.asarray(clean_p_f16).shape)
    out["generated_dtype"] = str(np.asarray(clean_p_f16).dtype)
    if np.asarray(clean_p_f16).shape != ref.shape:
        out.update({"pass": False, "bit_identical": False,
                    "reason": "PHASE27_GLOBAL_AUTHORITY_SHAPE_MISMATCH"})
        return out

    identical = bool(np.array_equal(np.asarray(clean_p_f16), ref))
    out["bit_identical"] = identical
    if identical:
        out.update({"pass": True, "mismatch_count": 0, "max_abs": 0.0,
                    "affected_sample_ids": [], "affected_batch_ids": [],
                    "note": "BIT_IDENTICAL_FLOAT16_PERSISTED_GLOBAL_PROBABILITY"})
        return out

    neq = (np.asarray(clean_p_f16) != ref)
    diff = np.abs(np.asarray(clean_p_f16).astype(np.float64) - ref.astype(np.float64))
    per_sample = neq.reshape(neq.shape[0], -1).any(axis=1)
    affected = [sample_order[i] for i in np.nonzero(per_sample)[0]]
    affected_set = set(affected)
    plan = canonical_batch_partition()
    affected_batches = [i for i, (_d, sids) in enumerate(plan)
                        if any(s in affected_set for s in sids)]
    out.update({
        "pass": False,
        "max_abs": float(diff.max()),
        "mismatch_count": int(neq.sum()),
        "affected_sample_count": len(affected),
        "affected_sample_ids": affected,
        "affected_batch_ids": affected_batches,
        "stop_before_downstream_perturbation": True,
        "reason": "CLEAN_G_NOT_BIT_IDENTICAL_TO_PHASE27_AUTHORITY",
    })
    return out


# --------------------------------------------------------------------------- #
# §G  CLEAN SYSTEM EVALUATION (STAGE 1b) + STRICT CLEAN EQUIVALENCE GATE
# --------------------------------------------------------------------------- #
def _bind_clean_reference():
    """Bind the phase27/29 scalar+routing authority (masks come from STAGE 1)."""
    p = ROOT / C.CLEAN_REFERENCE["per_sample_scores"]["path"]
    q = ROOT / C.CLEAN_REFERENCE["routing_state"]["path"]
    if not (p.exists() and q.exists()):
        return None
    if _sha(p) != C.CLEAN_REFERENCE["per_sample_scores"]["sha256"]:
        return None
    scores = list(csv.DictReader(p.open(encoding="utf-8")))
    decisions = {r["sample_id"]: r for r in csv.DictReader(q.open(encoding="utf-8"))}
    return {
        "sample_ids": [r["sample_id"] for r in scores],
        "dice_final": {r["sample_id"]: float(r["final_dice"]) for r in scores},
        "route_state": {r["sample_id"]: r["state_machine_branch"] for r in scores},
        "router_decision": {r["sample_id"]: r["router_decision"] for r in scores},
        "b_phi_execute": {sid: (d["selected"] == "True") for sid, d in decisions.items()},
        "roi_geometry": {},
        "final_pred": {},
    }


def _evaluate_clean_sample(sid, row, ctx, generated, counters, clean_store):
    """§G: clean per-sample system evaluation.  Consumes the STAGE-1a G artifacts.

    G is NOT re-run here (the canonical batched pass already produced p_global,
    geometry and the 202-D vector).  B_phi -> decision -> conditional R_psi /
    S_omega is executed by the shared canonical core.
    """
    import torch
    task_id = int(row["task_id"])
    p_global = generated["p_global"][sid]
    geom = generated["geometry"][sid]
    rf202 = generated["rf202"][sid]

    image_t = _load_clean_image_tensor(row)
    image_b = image_t[None].to(ctx["device"])

    out = canonical_learned_core(ctx, image_b, task_id,
                                 p_global_override=p_global, g_taps=None,
                                 router_features_202_override=rf202,
                                 roi_window=None,
                                 action_available=(geom is not None),
                                 counters=counters)
    final_prob = np.asarray(out["final_probability"], dtype=np.float32)
    final_binary = (final_prob >= SEGMENTATION_OUTPUT_THRESHOLD).astype(np.float32)

    gt = _load_val_gt(row)
    counters["unique_val_gt"] = counters.get("unique_val_gt", 0) + 1
    dice = _dice(final_binary, gt)
    iou = _iou(final_binary, gt)
    hd = _hd95(final_binary, gt)
    counters["metric_evaluations"] = counters.get("metric_evaluations", 0) + 1

    rec = {
        "sample_id": sid,
        "domain": row.get("dataset"),
        "task_id": task_id,
        "state": out["state"],                                 # final_state
        "state_machine_branch": out["state"],                  # exact branch (§G)
        "router_decision": out["router_decision"],             # SKIP | EXECUTE
        "router_score": (float(out["delta_hat_final"])
                         if out["delta_hat_final"] is not None else None),
        "final_dice": dice,
        "final_iou": iou,
        "final_hd95": hd.get("hd95", np.nan) if isinstance(hd, dict) else float(hd),
        "hd95_valid": hd.get("valid") if isinstance(hd, dict) else None,
        "final_source": _final_source_of(out["state"]),
        "roi_available": out["roi_available"],
        "refiner_forward_count": out["refiner_forward_count"],
        "s_omega_forward_count": out["s_omega_forward_count"],
    }
    clean_store.setdefault("p_global", {})[sid] = p_global
    clean_store.setdefault("geometry", {})[sid] = geom
    clean_store.setdefault("final_binary", {})[sid] = final_binary.astype(np.uint8)
    clean_store.setdefault("task_id", {})[sid] = task_id
    clean_store.setdefault("domain", {})[sid] = row.get("dataset")
    clean_store.setdefault("state", {})[sid] = out["state"]
    clean_store.setdefault("router_decision", {})[sid] = out["router_decision"]
    clean_store.setdefault("final_source", {})[sid] = rec["final_source"]
    clean_store.setdefault("clean_dice", {})[sid] = dice
    return rec


def _clean_equivalence_gate(clean_ref, generated, counters):
    """§G: STRICT — 808 exact Dice comparisons AND 808 exact state_machine_branch
    comparisons.  ACCEPT and REJECT are NEVER collapsed into 'non-global'.
    """
    counters["clean_equivalence_gate_invocations"] = \
        counters.get("clean_equivalence_gate_invocations", 0) + 1

    gen_records = {r["sample_id"]: r for r in generated["records"]}
    n_generated = len(gen_records)
    n_bound = len(clean_ref.get("sample_ids", [])) if clean_ref else 0
    checks = {
        "generated_exactly_808": n_generated == C.POPULATION_N,
        "bound_exactly_808": n_bound == C.POPULATION_N,
        "generated_equals_bound": n_generated == n_bound,
    }

    dice_mismatches = []
    route_mismatches = []
    router_decision_mismatches = []
    missing_bound_dice = []
    missing_generated_dice = []
    n_dice_comparisons = 0
    n_branch_comparisons = 0
    n_router_decision_comparisons = 0

    for sid, grec in gen_records.items():
        bound_dice = clean_ref["dice_final"].get(sid) if clean_ref else None
        if bound_dice is None:
            missing_bound_dice.append(sid)
        else:
            gd = grec.get("final_dice")
            if gd is None or not np.isfinite(float(gd)):
                missing_generated_dice.append(sid)
            else:
                n_dice_comparisons += 1
                if not np.isclose(float(gd), float(bound_dice), atol=1e-7, rtol=0):
                    dice_mismatches.append({"sample_id": sid, "generated": float(gd),
                                            "bound": float(bound_dice)})

        bound_branch = clean_ref["route_state"].get(sid) if clean_ref else None
        if bound_branch is not None:
            n_branch_comparisons += 1
            if grec.get("state_machine_branch") != bound_branch:
                route_mismatches.append({"sample_id": sid,
                                         "generated": grec.get("state_machine_branch"),
                                         "bound": bound_branch})

        bound_rd = clean_ref.get("router_decision", {}).get(sid) if clean_ref else None
        if bound_rd is not None:
            n_router_decision_comparisons += 1
            if grec.get("router_decision") != bound_rd:
                router_decision_mismatches.append({"sample_id": sid,
                                                   "generated": grec.get("router_decision"),
                                                   "bound": bound_rd})

    checks["missing_bound_dice_zero"] = (len(missing_bound_dice) == 0)
    checks["missing_generated_dice_zero"] = (len(missing_generated_dice) == 0)
    checks["dice_mismatches_zero"] = (len(dice_mismatches) == 0)
    checks["route_branch_mismatches_zero"] = (len(route_mismatches) == 0)
    checks["router_decision_mismatches_zero"] = (len(router_decision_mismatches) == 0)
    checks["n_dice_comparisons_808"] = (n_dice_comparisons == C.POPULATION_N)
    checks["n_state_machine_branch_comparisons_808"] = (n_branch_comparisons == C.POPULATION_N)
    checks["n_router_decision_comparisons_808"] = (
        n_router_decision_comparisons == C.POPULATION_N)
    checks["accept_and_reject_not_collapsed"] = True

    scores = []
    for sid in gen_records:
        b = clean_ref["dice_final"].get(sid) if clean_ref else None
        g = gen_records[sid].get("final_dice")
        if b is not None and g is not None and np.isfinite(float(g)):
            scores.append((float(g), float(b)))
    max_abs_dev = (max(abs(a - b) for a, b in scores) if scores else None)

    all_pass = bool(all(checks.values()))
    return {
        "all_pass": all_pass,
        "checks": checks,
        "n_generated": n_generated,
        "n_bound": n_bound,
        "n_dice_comparisons": n_dice_comparisons,
        "n_state_machine_branch_comparisons": n_branch_comparisons,
        "n_router_decision_comparisons": n_router_decision_comparisons,
        "missing_generated_dice": missing_generated_dice,
        "missing_bound_dice": missing_bound_dice,
        "dice_mismatches": dice_mismatches,
        "route_branch_mismatches": route_mismatches,
        "router_decision_mismatches": router_decision_mismatches,
        "max_abs_dice_deviation": max_abs_dev,
        "dice_comparator": "np.isclose(generated, bound, atol=1e-7, rtol=0)",
        "branch_comparator": "generated.state_machine_branch == bound.state_machine_branch (EXACT)",
        "router_decision_comparator": "generated.router_decision == bound.router_decision (EXACT)",
        "accept_reject_collapse_prohibited": True,
        "fail_closed_on_missing_data": True,
    }


# --------------------------------------------------------------------------- #
# §D/§F  STAGE 3 — IMAGE PERTURBATIONS (canonical batched G, sample-level rows)
# --------------------------------------------------------------------------- #
def run_image_perturbations(ctx, generated, clean_store, counters, image_rows,
                            consistency_rows):
    """Canonical-batched image perturbation execution.

    G runs in canonical domain-local batches of 8 (never sample-by-sample), while
    every (sample, condition) still EMITS a fully-populated sample-level row.
    Never silently `continue`; identity loss raises.
    """
    rows, row_index = _clean_row_index()
    sample_order = [r["sample_id"] for r in rows]
    clean_by_sid = {r["sample_id"]: r for r in generated["records"]}
    if len(sample_order) != AUTHORIZED_POPULATION_N:
        raise ValueError(
            f"SAMPLE_POPULATION_MISMATCH: {len(sample_order)} != {AUTHORIZED_POPULATION_N}")

    plan = image_realization_plan()
    for real in plan:
        cond = real["condition"]
        base_seed = real["base_seed"]
        for _dom, sids in canonical_batch_partition(rows):
            for batch in _chunks(sids, CANONICAL_G_BATCH_SIZE):
                images = np.stack([
                    np.asarray(C.apply_image_condition(
                        np.asarray(_load_clean_image_tensor(row_index[sid]).numpy(),
                                   dtype=np.float32), cond, sid, base_seed),
                        dtype=np.float32) for sid in batch])
                x = canonical_images_tensor(ctx, images)
                t = canonical_task_ids_tensor(
                    ctx, [int(row_index[sid]["task_id"]) for sid in batch])
                gout = canonical_g_forward_batched(ctx, x, t)
                counters["perturbed_g_forwards"] = \
                    counters.get("perturbed_g_forwards", 0) + len(batch)
                counters["perturbed_g_batch_forwards"] = \
                    counters.get("perturbed_g_batch_forwards", 0) + 1
                counters["forwards"] = counters.get("forwards", 0) + len(batch)

                for bi, sid in enumerate(batch):
                    clean_row = clean_by_sid[sid]
                    if not _row_has_identity(clean_row):
                        raise ValueError(
                            f"SCIENCE_ROW_SCHEMA_LOSS: clean row lacks identity for {sid}")
                    domain = clean_row.get("domain")
                    task_id = clean_row.get("task_id")
                    if domain is None or task_id is None:
                        raise ValueError(
                            f"SCIENCE_ROW_SCHEMA_LOSS: missing domain/task_id for {sid}")
                    derived_seed = _derived_seed_for(cond, base_seed, sid)

                    out = canonical_learned_core(
                        ctx, x[bi:bi + 1], int(task_id),
                        g_logits=gout["logits"][bi],
                        g_probability=np.asarray(gout["probability"][bi], dtype=np.float32),
                        g_taps={k: np.asarray(v[bi]) for k, v in gout["taps"].items()},
                        counters=counters)
                    pert_binary = np.asarray(out["final_binary"], dtype=np.float32)
                    pc = _prediction_consistency_dice(
                        pert_binary, clean_store["final_binary"][sid])
                    gt = _load_val_gt(row_index[sid])
                    counters["unique_val_gt"] = counters.get("unique_val_gt", 0) + 1
                    pert_dice = _dice(pert_binary, gt)
                    pert_iou = _iou(pert_binary, gt)
                    hd = _hd95(pert_binary, gt)
                    counters["metric_evaluations"] = counters.get("metric_evaluations", 0) + 1

                    row = build_image_result_row(
                        sid=sid, domain=domain, task_id=int(task_id), cond=cond,
                        base_seed=base_seed, derived_seed=derived_seed,
                        clean_dice=float(clean_row["final_dice"]),
                        perturbed_dice=pert_dice,
                        prediction_consistency_dice=pc,
                        clean_route_state=clean_store["state"][sid],
                        perturbed_route_state=out["state"],
                        clean_router_decision=clean_store["router_decision"][sid],
                        perturbed_router_decision=out["router_decision"],
                        final_source=clean_store["final_source"][sid],
                        perturbed_final_source=_final_source_of(out["state"]),
                        perturbed_iou=pert_iou,
                        perturbed_hd95=(hd.get("hd95", np.nan)
                                        if isinstance(hd, dict) else float(hd)),
                        perturbed_hd95_valid=(hd.get("valid") if isinstance(hd, dict) else None))
                    image_rows.append(row)
                    consistency_rows.append({
                        "sample_id": sid, "domain": domain, "task_id": int(task_id),
                        "condition": cond, "base_seed": base_seed,
                        "derived_seed": derived_seed,
                        "prediction_consistency_dice": pc,
                        "perturbed_route_state": out["state"]})
                    counters["image_perturbation_instances"] = \
                        counters.get("image_perturbation_instances", 0) + 1
                    counters["prediction_consistency_evaluations"] = \
                        counters.get("prediction_consistency_evaluations", 0) + 1
    if len(image_rows) != NONCLEAN_IMAGE_EXECUTIONS_EXPECTED:
        raise AssertionError(
            f"NONCLEAN_IMAGE_EXECUTIONS {len(image_rows)} != {NONCLEAN_IMAGE_EXECUTIONS_EXPECTED}")
    return image_rows


# --------------------------------------------------------------------------- #
# §F/§H  STAGE 4 — PROPOSAL PERTURBATIONS (G reused; shared proposal adapter)
# --------------------------------------------------------------------------- #
def run_proposal_perturbations(ctx, generated, clean_store, counters, proposal_rows):
    """Sample-first proposal perturbation execution via the shared proposal adapter.

    G is REUSED from the clean pass (frozen contract
    ``G_recomputed_for_proposal_perturbation = False``).  The perturbed 202-D
    vectors and geometries were precomputed during the clean G pass.
    Empty canonical proposal -> six explicit NOT_APPLICABLE_EMPTY_PROPOSAL records.
    """
    rows, row_index = _clean_row_index()
    sample_order = [r["sample_id"] for r in rows]
    clean_by_sid = {r["sample_id"]: r for r in generated["records"]}
    plan = proposal_realization_plan()

    for sid in sample_order:
        clean_row = clean_by_sid[sid]
        domain = clean_row.get("domain")
        task_id = clean_row.get("task_id")
        if sid is None or domain is None or task_id is None:
            raise ValueError(f"SCIENCE_ROW_SCHEMA_LOSS: missing identity for {sid}")
        pgeom = generated["proposal_geometry"].get(sid)
        prf = generated["proposal_rf202"].get(sid)
        clean_dice = float(clean_row["final_dice"])
        p_global = generated["p_global"][sid]

        if pgeom is None:
            for real in plan:
                proposal_rows.append({
                    "sample_id": sid, "domain": domain, "task_id": int(task_id),
                    "proposal_condition": real["proposal_condition"],
                    "status": C.EMPTY_PROPOSAL_HANDLING,
                    "router_decision": None,
                    "perturbed_route_state": C.EMPTY_PROPOSAL_HANDLING,
                    "not_applicable": True,
                    "replacement_geometry_generated": False})
            counters["empty_proposal_not_applicable"] = \
                counters.get("empty_proposal_not_applicable", 0) + len(plan)
            continue

        image_t = _load_clean_image_tensor(row_index[sid])
        image_b = image_t[None].to(ctx["device"])
        for real in plan:
            cond = real["proposal_condition"]
            # The perturbed 202-D was assembled with the PERTURBED roi_row during the
            # clean G pass, so the geometry-dependent dims are provably recomputed.
            out = proposal_core_adapter(
                ctx, image_b, int(task_id),
                proposal_geometry=pgeom[cond],
                g_logits=None, g_taps=None,
                p_global_override=p_global,
                router_features_202_override=prf[cond],
                counters=counters)
            pert_binary = np.asarray(out["final_binary"], dtype=np.float32)
            gt = _load_val_gt(row_index[sid])
            counters["unique_val_gt"] = counters.get("unique_val_gt", 0) + 1
            pert_dice = _dice(pert_binary, gt)
            counters["metric_evaluations"] = counters.get("metric_evaluations", 0) + 1
            proposal_rows.append({
                "sample_id": sid, "domain": domain, "task_id": int(task_id),
                "proposal_condition": cond, "status": "EXECUTED",
                "clean_dice": clean_dice, "perturbed_dice": pert_dice,
                "paired_delta_dice": pert_dice - clean_dice,
                "prediction_consistency_dice": _prediction_consistency_dice(
                    pert_binary, clean_store["final_binary"][sid]),
                "perturbed_route_state": out["state"],
                "perturbed_router_decision": out["router_decision"],
                "clean_route_state": clean_store["state"][sid],
                "clean_router_decision": clean_store["router_decision"][sid],
                "not_applicable": False,
                "replacement_geometry_generated": False})
            counters["proposal_perturbation_executions"] = \
                counters.get("proposal_perturbation_executions", 0) + 1
            counters["proposal_perturbation_instances"] = \
                counters.get("proposal_perturbation_instances", 0) + 1
    return proposal_rows


# --------------------------------------------------------------------------- #
# §H  FIXED SUMMARIES (must be reachable from run_science)
# --------------------------------------------------------------------------- #
def _write_csv(path: Path, rows: list, fieldnames: list = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = fieldnames or list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def summarize_image_per_sample(image_rows):
    out = []
    for r in image_rows:
        out.append({
            "sample_id": r["sample_id"], "domain": r["domain"], "task_id": r["task_id"],
            "condition": r["condition"], "base_seed": r["base_seed"],
            "derived_seed": r["derived_seed"], "clean_dice": r["clean_dice"],
            "perturbed_dice": r["perturbed_dice"],
            "paired_delta_dice": r["paired_delta_dice"],
            "prediction_consistency_dice": r["prediction_consistency_dice"],
            "route_state_changed": r["route_state_changed"],
            "router_decision_changed": r["router_decision_changed"]})
    _write_csv(TAB / "phase36_image_robustness_per_sample.csv", out)
    return out


def summarize_image_by_domain_condition(image_rows):
    agg = {}
    for r in image_rows:
        agg.setdefault((r["domain"], r["condition"]), []).append(float(r["paired_delta_dice"]))
    out = []
    for (dom, cond), vals in agg.items():
        s = _finite_summary(vals)
        out.append({"domain": dom, "condition": cond, "n": s["n_total"],
                    "n_finite": s["n_finite"], "n_nan": s["n_nan"],
                    "mean_paired_delta_dice": s["mean"],
                    "median_paired_delta_dice": s["median"]})
    _write_csv(TAB / "phase36_image_robustness_by_domain_condition.csv", out)
    return out


def summarize_noise_seed(image_rows):
    agg = {}
    for r in image_rows:
        if r["base_seed"] is None:
            continue
        agg.setdefault((r["domain"], r["condition"], r["sample_id"], int(r["base_seed"])),
                       []).append(float(r["paired_delta_dice"]))
    per_seed = {}
    for (dom, cond, sid, bs), vals in agg.items():
        per_seed.setdefault((dom, cond), {}).setdefault(sid, {})[bs] = \
            float(np.mean(np.asarray(vals, dtype=np.float64)))
    out = []
    for (dom, cond), per_sample in per_seed.items():
        sample_means = [float(np.mean(np.asarray(list(m.values()), dtype=np.float64)))
                        for m in per_sample.values()]
        out.append({"domain": dom, "condition": cond,
                    "n_samples": len(sample_means),
                    "mean_across_seeds_of_sample_means":
                        (float(np.mean(sample_means)) if sample_means else None),
                    "best_seed_selection": bool(C.BEST_SEED_SELECTION)})
    _write_csv(TAB / "phase36_noise_seed_summary.csv", out)
    return out


def summarize_proposal_per_sample(proposal_rows):
    out = [dict(r) for r in proposal_rows]
    _write_csv(TAB / "phase36_proposal_robustness_per_sample.csv", out)
    return out


def summarize_proposal_by_domain_condition(proposal_rows):
    agg = {}
    for r in proposal_rows:
        if r.get("not_applicable"):
            continue
        agg.setdefault((r["domain"], r["proposal_condition"]), []).append(
            float(r["paired_delta_dice"]))
    out = []
    for (dom, cond), vals in agg.items():
        s = _finite_summary(vals)
        out.append({"domain": dom, "proposal_condition": cond, "n_applicable": s["n_total"],
                    "mean_paired_delta_dice": s["mean"],
                    "median_paired_delta_dice": s["median"]})
    _write_csv(TAB / "phase36_proposal_robustness_by_domain_condition.csv", out)
    return out


def summarize_route_stability(image_rows):
    agg = {}
    for r in image_rows:
        agg.setdefault((r["domain"], r["condition"]), [0, 0])
        agg[(r["domain"], r["condition"])][0] += 1
        if r["route_state_changed"]:
            agg[(r["domain"], r["condition"])][1] += 1
    out = []
    for (dom, cond), (n, chg) in agg.items():
        out.append({"domain": dom, "condition": cond, "n": n,
                    "route_state_changed_count": chg,
                    "route_state_change_rate": (chg / n if n else None)})
    _write_csv(TAB / "phase36_route_stability_summary.csv", out)
    return out


def summarize_execution_rate(image_rows):
    """Descriptive execution / accept / reject rates by domain x condition."""
    agg = {}
    for r in image_rows:
        k = (r["domain"], r["condition"])
        agg.setdefault(k, {"n": 0, "execute": 0, "accept": 0, "reject": 0})
        agg[k]["n"] += 1
        if r["perturbed_router_decision"] == "EXECUTE":
            agg[k]["execute"] += 1
        if r["perturbed_route_state"] == "EXECUTE_THEN_ACCEPT":
            agg[k]["accept"] += 1
        if r["perturbed_route_state"] == "EXECUTE_THEN_REJECT":
            agg[k]["reject"] += 1
    out = []
    for (dom, cond), d in agg.items():
        n = d["n"]
        out.append({"domain": dom, "condition": cond, "n": n,
                    "execution_rate": (d["execute"] / n if n else None),
                    "accept_rate": (d["accept"] / n if n else None),
                    "reject_rate": (d["reject"] / n if n else None)})
    _write_csv(TAB / "phase36_execution_rate_summary.csv", out)
    return out


# --------------------------------------------------------------------------- #
# §I  WORST-CASE PATH (real; from actual result rows)
# --------------------------------------------------------------------------- #
def worst_case_per_sample(image_rows, proposal_rows):
    by_sample = {}
    for r in image_rows:
        by_sample.setdefault(r["sample_id"], {"domain": r["domain"], "task_id": r["task_id"],
                                              "img_deltas": []})
        by_sample[r["sample_id"]]["img_deltas"].append(float(r["paired_delta_dice"]))
    prop_by_sample = {}
    for r in proposal_rows:
        if r.get("not_applicable"):
            continue
        prop_by_sample.setdefault(r["sample_id"], []).append(float(r["paired_delta_dice"]))
    out = []
    for sid, d in by_sample.items():
        img_worst = min(d["img_deltas"]) if d["img_deltas"] else None
        prop_list = prop_by_sample.get(sid, [])
        prop_worst = min(prop_list) if prop_list else None
        out.append({"sample_id": sid, "domain": d["domain"], "task_id": d["task_id"],
                    "worst_image_perturbation_delta_Dice": img_worst,
                    "worst_proposal_perturbation_delta_Dice": prop_worst,
                    "n_image_realizations": len(d["img_deltas"]),
                    "n_proposal_applicable": len(prop_list)})
    _write_csv(TAB / "phase36_worst_case_per_sample.csv", out)
    return out


def worst_case_by_domain(worst_per_sample):
    agg = {}
    for r in worst_per_sample:
        agg.setdefault(r["domain"], []).append(r["worst_image_perturbation_delta_Dice"])
    out = []
    for dom, vals in agg.items():
        finite = [v for v in vals if v is not None and np.isfinite(v)]
        out.append({"domain": dom, "n_samples": len(vals),
                    "worst_image_delta_Dice_min": (min(finite) if finite else None),
                    "worst_image_delta_Dice_mean": (float(np.mean(finite)) if finite else None)})
    _write_csv(TAB / "phase36_worst_case_by_domain.csv", out)
    return out


# --------------------------------------------------------------------------- #
# §L  KUB SUBGROUP REPORTING (REPORTING ONLY — never classes / task ids / inputs)
# --------------------------------------------------------------------------- #
def kub_subgroup_map() -> dict:
    """Bind the frozen KUB subgroup metadata authority (val.csv :: category, KUB rows)."""
    path = ROOT / KUB_SUBGROUP_AUTHORITY["path"]
    if _sha(path) != KUB_SUBGROUP_AUTHORITY["sha256"]:
        raise ValueError("KUB_SUBGROUP_AUTHORITY_SHA_MISMATCH")
    rows = _rows(path)
    allowed = set(KUB_SUBGROUP_AUTHORITY["subgroups"])
    out = {}
    for r in rows:
        if str(r.get("dataset")) != "KUB":
            continue
        cat = str(r.get("category", "")).strip()
        if cat not in allowed:
            raise ValueError(f"KUB_SUBGROUP_METADATA_MISSING: {r.get('sample_id')}")
        out[r["sample_id"]] = cat
    counts = {}
    for v in out.values():
        counts[v] = counts.get(v, 0) + 1
    if counts != dict(KUB_SUBGROUP_AUTHORITY["expected_counts"]):
        raise ValueError(f"KUB_SUBGROUP_COUNTS_MISMATCH: {counts}")
    return out


def kub_subgroup_robustness(image_rows):
    """KUB subgroup robustness (REPORTING ONLY) with real subgroup labels."""
    if not C.KUB_REPORTING_ONLY:
        return None
    sub = kub_subgroup_map()
    rows = []
    for r in image_rows:
        if r["domain"] != "KUB":
            continue
        rows.append({"sample_id": r["sample_id"],
                     "kub_subgroup": sub[r["sample_id"]],
                     "condition": r["condition"],
                     "base_seed": r["base_seed"],
                     "paired_delta_dice": r["paired_delta_dice"]})
    _write_csv(TAB / "phase36_kub_subgroup_robustness.csv", rows)

    agg = {}
    for r in rows:
        agg.setdefault((r["kub_subgroup"], r["condition"]), []).append(
            float(r["paired_delta_dice"]))
    summary = []
    for (sg, cond), vals in sorted(agg.items()):
        s = _finite_summary(vals)
        summary.append({"kub_subgroup": sg, "condition": cond, "n": s["n_total"],
                        "n_finite": s["n_finite"],
                        "mean_paired_delta_dice": s["mean"],
                        "median_paired_delta_dice": s["median"]})
    _write_csv(TAB / "phase36_kub_subgroup_robustness_by_subgroup.csv", summary)
    return {
        "per_sample_rows": rows,
        "by_subgroup_condition": summary,
        "subgroups": list(KUB_SUBGROUP_AUTHORITY["subgroups"]),
        "subgroup_source": KUB_SUBGROUP_AUTHORITY["path"] + "::" +
                           KUB_SUBGROUP_AUTHORITY["label_column"],
        "reporting_only": True,
        "never_classes": True,
        "never_task_ids": True,
        "never_model_inputs": True,
        "n_kub_rows": len(rows),
    }


# --------------------------------------------------------------------------- #
# §M  R1-R5 FIGURE BUILDERS (frozen registry; reachable only after science)
# --------------------------------------------------------------------------- #
def _fig_ax():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def figure_R1(image_rows):
    """R1: image-perturbation mean paired DeltaDice heatmap (domain x condition)."""
    plt = _fig_ax()
    doms = list(CANONICAL_DOMAIN_ORDER)
    conds = [c for c in C.image_condition_ids() if c != "CLEAN"]
    agg = np.full((len(doms), len(conds)), np.nan, dtype=np.float64)
    for i, dom in enumerate(doms):
        for j, cond in enumerate(conds):
            vals = [float(r["paired_delta_dice"]) for r in image_rows
                    if r["domain"] == dom and r["condition"] == cond]
            if vals:
                agg[i, j] = float(np.mean(vals))
    fig, ax = plt.subplots(figsize=(1.05 * len(conds) + 3, 0.5 * len(doms) + 2.4))
    im = ax.imshow(agg, aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(conds))); ax.set_xticklabels(conds, rotation=60, ha="right", fontsize=8)
    ax.set_yticks(range(len(doms))); ax.set_yticklabels(doms, fontsize=9)
    ax.set_title("R1  mean paired DeltaDice (domain x image condition)", fontsize=10)
    fig.colorbar(im, ax=ax, shrink=0.8, label="mean paired DeltaDice")
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    p = FIG / "R1_image_perturbation_mean_paired_delta_dice_heatmap.png"
    fig.savefig(p, dpi=160); plt.close(fig)
    return str(p)


def figure_R2(image_rows):
    """R2: severity curves for noise / blur / resolution degradation."""
    plt = _fig_ax()
    curves = {
        "noise": [("GAUSSIAN_NOISE_LOW", 0.02), ("GAUSSIAN_NOISE_HIGH", 0.05)],
        "blur": [("GAUSSIAN_BLUR_LOW", 0.5), ("GAUSSIAN_BLUR_HIGH", 1.0)],
        "resolution": [("RESOLUTION_075", 0.75), ("RESOLUTION_050", 0.50)],
    }
    fig, axes = plt.subplots(1, len(curves), figsize=(4.2 * len(curves), 3.2))
    for ax, (fam, members) in zip(np.atleast_1d(axes), curves.items()):
        for dom in CANONICAL_DOMAIN_ORDER:
            xs, ys = [], []
            for cond, sev in members:
                vals = [float(r["paired_delta_dice"]) for r in image_rows
                        if r["domain"] == dom and r["condition"] == cond]
                if vals:
                    xs.append(sev); ys.append(float(np.mean(vals)))
            if xs:
                ax.plot(xs, ys, marker="o", label=dom)
        ax.set_title(f"R2  {fam}", fontsize=10)
        ax.set_xlabel("severity"); ax.set_ylabel("mean paired DeltaDice")
        ax.grid(alpha=0.25)
    np.atleast_1d(axes)[0].legend(fontsize=7)
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    p = FIG / "R2_severity_curves_noise_blur_resolution.png"
    fig.savefig(p, dpi=160); plt.close(fig)
    return str(p)


def figure_R3(image_rows):
    """R3: route-state-change / execution-rate heatmap."""
    plt = _fig_ax()
    doms = list(CANONICAL_DOMAIN_ORDER)
    conds = [c for c in C.image_condition_ids() if c != "CLEAN"]
    chg = np.full((len(doms), len(conds)), np.nan, dtype=np.float64)
    exe = np.full((len(doms), len(conds)), np.nan, dtype=np.float64)
    for i, dom in enumerate(doms):
        for j, cond in enumerate(conds):
            sub = [r for r in image_rows if r["domain"] == dom and r["condition"] == cond]
            if sub:
                chg[i, j] = float(np.mean([bool(r["route_state_changed"]) for r in sub]))
                exe[i, j] = float(np.mean([r["perturbed_router_decision"] == "EXECUTE"
                                           for r in sub]))
    fig, axes = plt.subplots(1, 2, figsize=(2 * (1.05 * len(conds) + 3), 0.5 * len(doms) + 2.6))
    for ax, mat, title in zip(axes, (chg, exe),
                              ("R3a  route-state change rate", "R3b  execution rate")):
        im = ax.imshow(mat, aspect="auto", cmap="magma", vmin=0.0, vmax=1.0)
        ax.set_xticks(range(len(conds)))
        ax.set_xticklabels(conds, rotation=60, ha="right", fontsize=8)
        ax.set_yticks(range(len(doms))); ax.set_yticklabels(doms, fontsize=9)
        ax.set_title(title, fontsize=10)
        fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    p = FIG / "R3_route_state_change_and_execution_rate_heatmap.png"
    fig.savefig(p, dpi=160); plt.close(fig)
    return str(p)


def figure_R4(proposal_rows):
    """R4: proposal perturbation paired DeltaDice summary."""
    plt = _fig_ax()
    conds = list(NONCLEAN_PROPOSAL_CONDITIONS)
    doms = list(CANONICAL_DOMAIN_ORDER)
    fig, ax = plt.subplots(figsize=(1.15 * len(conds) + 3, 3.6))
    width = 0.8 / max(1, len(doms))
    for k, dom in enumerate(doms):
        means = []
        for cond in conds:
            vals = [float(r["paired_delta_dice"]) for r in proposal_rows
                    if r["domain"] == dom and r["proposal_condition"] == cond
                    and not r.get("not_applicable")]
            means.append(float(np.mean(vals)) if vals else 0.0)
        ax.bar(np.arange(len(conds)) + k * width, means, width=width, label=dom)
    ax.set_xticks(np.arange(len(conds)) + 0.4 - width / 2)
    ax.set_xticklabels(conds, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("mean paired DeltaDice")
    ax.set_title("R4  proposal perturbation paired DeltaDice", fontsize=10)
    ax.legend(fontsize=7); ax.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    p = FIG / "R4_proposal_perturbation_paired_delta_dice.png"
    fig.savefig(p, dpi=160); plt.close(fig)
    return str(p)


def figure_R5(worst_per_sample):
    """R5: worst-case image/proposal DeltaDice distribution by domain."""
    plt = _fig_ax()
    doms = list(CANONICAL_DOMAIN_ORDER)
    img = [[r["worst_image_perturbation_delta_Dice"] for r in worst_per_sample
            if r["domain"] == dom and r["worst_image_perturbation_delta_Dice"] is not None]
           for dom in doms]
    prop = [[r["worst_proposal_perturbation_delta_Dice"] for r in worst_per_sample
             if r["domain"] == dom and r["worst_proposal_perturbation_delta_Dice"] is not None]
            for dom in doms]
    fig, ax = plt.subplots(figsize=(1.2 * len(doms) + 3, 3.8))
    pos = np.arange(len(doms))
    ax.boxplot(img, positions=pos - 0.18, widths=0.32, patch_artist=True,
               boxprops=dict(facecolor="#8ecae6"))
    ax.boxplot(prop, positions=pos + 0.18, widths=0.32, patch_artist=True,
               boxprops=dict(facecolor="#ffb703"))
    ax.set_xticks(pos); ax.set_xticklabels(doms)
    ax.set_ylabel("worst paired DeltaDice")
    ax.set_title("R5  worst-case image (blue) vs proposal (orange) DeltaDice by domain",
                 fontsize=10)
    ax.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    FIG.mkdir(parents=True, exist_ok=True)
    p = FIG / "R5_worst_case_delta_dice_distribution_by_domain.png"
    fig.savefig(p, dpi=160); plt.close(fig)
    return str(p)


def generate_all_figures(image_rows, proposal_rows, worst_per_sample) -> dict:
    """Generate exactly the frozen R1-R5 registry.  No new figure selection."""
    out = {
        "R1": figure_R1(image_rows),
        "R2": figure_R2(image_rows),
        "R3": figure_R3(image_rows),
        "R4": figure_R4(proposal_rows),
        "R5": figure_R5(worst_per_sample),
    }
    if sorted(out) != sorted(FIGURE_REGISTRY.keys()):
        raise AssertionError(f"FIGURE_REGISTRY_MISMATCH: {sorted(out)} != {sorted(FIGURE_REGISTRY)}")
    return {"figures": out, "registry": dict(FIGURE_REGISTRY),
            "n_figures": len(out), "new_figure_selection": False}


# --------------------------------------------------------------------------- #
# §A  REAL science driver (canonical batched G, conditional state machine)
# --------------------------------------------------------------------------- #
def run_science() -> dict:
    counters = OrderedDict((k, 0) for k in C.COUNTERS_REQUIRED)
    for k in C.COUNTERS_FOREVER_ZERO:
        counters[k] = 0

    # §D30 (v1.11): TRANSITIVE RUNTIME SOURCE INTEGRITY is verified BEFORE model
    # construction on the SCIENCE path, exactly as on the smoke path.  This is the
    # SAME gate and the SAME frozen authority used by the smoke path — NOT a
    # different scientific hash/authority for science.  Fail CLOSED.
    source_integrity = _verify_transitive_source_integrity()
    if not source_integrity["all_match"]:
        raise SystemExit(
            "D30_SCIENCE_TRANSITIVE_RUNTIME_SOURCE_INTEGRITY_FAILED__STOP_BEFORE_MODEL_CONSTRUCTION: "
            + json.dumps(source_integrity, indent=1, default=str))

    # STAGE 1a: canonical batched CLEAN G pass (autocast fp16 / batch-8 / device-bound).
    ctx = _load_models()
    audit = ctx["load_audit"]
    clean_ref_bound = _bind_clean_reference()
    generated = _generate_clean_g_reference(ctx, counters)

    # STAGE 1a-gate (§E): Phase27 clean global reproduction gate.  STOP on failure,
    # BEFORE any downstream CLEAN system evaluation or perturbation execution.
    g_gate = _phase27_global_reproduction_gate(
        generated["p_global_f16"], generated["sample_order"], counters)
    if not g_gate["pass"]:
        raise SystemExit(
            "CLEAN_GLOBAL_REPRODUCTION_GATE_FAILED__STOP_BEFORE_DOWNSTREAM_PERTURBATION")

    # STAGE 1b: clean system evaluation (B_phi -> conditional R_psi / S_omega).
    clean_store = {}
    clean_records = []
    rows, row_index = _clean_row_index()
    for r in rows:
        sid = r["sample_id"]
        clean_records.append(
            _evaluate_clean_sample(sid, r, ctx, generated, counters, clean_store))
        counters["clean_passes"] = counters.get("clean_passes", 0) + 1
    generated["records"] = clean_records

    # STAGE 2: strict clean-equivalence gate; STOP before perturbation on failure.
    eq = _clean_equivalence_gate(clean_ref_bound, generated, counters)
    if not eq["all_pass"]:
        raise SystemExit("CLEAN_EQUIVALENCE_GATE_FAILED__STOP_BEFORE_PERTURBATION")

    # STAGE 3: image perturbations (canonical batched G, sample-level rows).
    image_rows = []
    consistency_rows = []
    run_image_perturbations(ctx, generated, clean_store, counters,
                            image_rows, consistency_rows)

    # STAGE 4: proposal perturbations (G reused, sample-first).
    proposal_rows = []
    run_proposal_perturbations(ctx, generated, clean_store, counters, proposal_rows)

    # §G  COUNTER INTEGRITY: protected counters were INITIALIZED to zero at run
    # start (via C.COUNTERS_FOREVER_ZERO) and are NEVER force-reset after
    # execution.  Fail closed if any protected-read counter is non-zero.
    # This assertion is DEFENSE-IN-DEPTH only; the PRIMARY proof is the static /
    # runtime call-graph absence of protected file IO.
    for _protected_counter in PROTECTED_COUNTERS:
        if counters.get(_protected_counter, 0) != 0:
            raise SystemExit(
                f"PHASE36_PROTECTED_READ_COUNTER_NONZERO__{_protected_counter}")
    for _forever_zero_counter in ("training", "optimizer_steps", "parameter_mutations"):
        if counters.get(_forever_zero_counter, 0) != 0:
            raise SystemExit(
                f"PHASE36_FOREVER_ZERO_COUNTER_NONZERO__{_forever_zero_counter}")

    # STAGE 5: fixed summaries / worst-case / KUB subgroup / figures.
    summaries = {
        "image_per_sample": summarize_image_per_sample(image_rows),
        "image_by_domain_condition": summarize_image_by_domain_condition(image_rows),
        "noise_seed": summarize_noise_seed(image_rows),
        "proposal_per_sample": summarize_proposal_per_sample(proposal_rows),
        "proposal_by_domain_condition": summarize_proposal_by_domain_condition(proposal_rows),
        "route_stability": summarize_route_stability(image_rows),
        "execution_rate": summarize_execution_rate(image_rows),
    }
    worst_per_sample = worst_case_per_sample(image_rows, proposal_rows)
    worst_by_domain = worst_case_by_domain(worst_per_sample)
    kub_rows = kub_subgroup_robustness(image_rows)
    figures = generate_all_figures(image_rows, proposal_rows, worst_per_sample)

    return {"classification": "PHASE36_ROBUSTNESS_SCIENTIFIC_RESULT",
            "evidence_class": C.EVIDENCE_CLASS,
            "component_load_audit": audit,
            "g_numerical_semantics": generated["g_numerical_semantics"],
            "clean_g_reproduction_gate": g_gate,
            "clean_equivalence": eq,
            "prediction_consistency": consistency_rows,
            "image_rows": image_rows,
            "proposal_rows": proposal_rows,
            "worst_case_per_sample": worst_per_sample,
            "worst_case_by_domain": worst_by_domain,
            "kub_subgroup": kub_rows,
            "figures": figures,
            "counts": {
                "authorized_population": AUTHORIZED_POPULATION_N,
                "clean_execution_count_expected": CLEAN_EXECUTIONS_EXPECTED,
                "image_nonclean_execution_count_expected": NONCLEAN_IMAGE_EXECUTIONS_EXPECTED,
                "image_rows_emitted": len(image_rows),
                "proposal_nonclean_execution_count_max": NONCLEAN_PROPOSAL_EXECUTIONS_MAX,
                "proposal_rows_emitted": len(proposal_rows),
                "logical_image_table_rows_max": LOGICAL_IMAGE_TABLE_ROWS_MAX,
            },
            "counters": counters, "generated_utc": now()}


# --------------------------------------------------------------------------- #
# §I/§J/§K  SMOKE — REAL full-pipeline coverage through the SHARED core
# --------------------------------------------------------------------------- #
def _synth_image(seed: int = 0) -> np.ndarray:
    rng = np.random.Generator(np.random.PCG64(seed))
    return rng.random((512, 512), dtype=np.float32)


def _synthetic_batch_image_np(seed: int = 0) -> np.ndarray:
    rng = np.random.Generator(np.random.PCG64(seed))
    return rng.random((3, 512, 512), dtype=np.float32)


def smoke_real_execute_component_probe(ctx, image_b, task_id, g_logits, g_taps,
                                       p_global) -> dict:
    """§E: ONE GUARANTEED REAL EXECUTE-pipeline probe.

    Forces the ROUTER decision to EXECUTE with a frozen high control score, but
    leaves ``forced_s_omega_logit = None`` so that BOTH the R_psi forward AND the
    S_omega forward are REAL model invocations.  The final state is whatever the
    REAL S_omega result produces — it is NEVER outcome-selected.

    This is synthetic smoke validation only; it is not scientific evidence.
    """
    from src.models.barr.ra_medfilm_barr import canonical_utility, TAU_C8_FINAL_FLOAT
    geom = _synthetic_geometry(p_global)
    control_router_score = +50.0
    counters = {}
    out = canonical_learned_core(ctx, image_b, task_id,
                                 g_logits=g_logits, g_taps=g_taps,
                                 p_global_override=p_global,
                                 proposal_geometry=geom, action_available=True,
                                 forced_delta_hat_final=control_router_score,
                                 forced_s_omega_logit=None,
                                 counters=counters)
    final_prob = out["final_probability"]
    final_prob_arr = None if final_prob is None else np.asarray(final_prob, dtype=np.float32)
    logit = out["post_safety_logit"]
    accept_prob = out["post_safety_accept_probability"]
    accept_prob_val = None if accept_prob is None else float(accept_prob)
    return {
        "probe": "smoke_real_execute_component_probe",
        "policy_control": True,
        "forced_router_score": bool(out["forced_router_score"]),
        "forced_safety_logit": bool(out["forced_safety_logit"]),
        "control_router_score": control_router_score,
        "control_utility": canonical_utility(control_router_score),
        "threshold_C8": float(TAU_C8_FINAL_FLOAT),
        "router_decision": out["router_decision"],
        "observed_state": out["state"],
        "outcome_selected": False,
        "actual_R_psi_forward_count": int(out["actual_r_psi_forward_count"]),
        "actual_S_omega_forward_count": int(out["actual_s_omega_forward_count"]),
        "post_safety_logit": (None if logit is None else float(logit)),
        "post_safety_logit_finite": bool(logit is not None and np.isfinite(float(logit))),
        "post_safety_accept_probability": accept_prob_val,
        "post_safety_accept_probability_finite": bool(
            accept_prob is not None and np.isfinite(float(accept_prob))),
        "post_safety_accept_probability_in_unit_interval": bool(
            accept_prob_val is not None and 0.0 <= accept_prob_val <= 1.0),
        "final_probability_finite": bool(
            final_prob_arr is not None and np.isfinite(final_prob_arr).all()),
        "final_probability_shape": (None if final_prob_arr is None
                                    else list(final_prob_arr.shape)),
        "router_vector_dim": out["router_vector_dim"],
        "router_vector_finite": bool(out["router_vector_finite"]),
        "refined_output_finite": out.get("refined_output_finite"),
        "refined_output_shape": out.get("refined_output_shape"),
        "refined_output_is_probability": out.get("refined_output_is_probability"),
        "refined_output_in_unit_interval": out.get("refined_output_in_unit_interval"),
        "post_safety_feature_dim": out.get("post_safety_feature_dim"),
        "post_safety_features_finite": out.get("post_safety_features_finite"),
        # §D24 (v1.9): actual final S_omega input observability.
        "final_s_omega_input_dim": out.get("final_s_omega_input_dim"),
        "final_s_omega_input_finite": out.get("final_s_omega_input_finite"),
        "post_safety_numeric_normalized_dim": out.get("post_safety_numeric_normalized_dim"),
        "post_safety_numeric_normalized_finite": out.get("post_safety_numeric_normalized_finite"),
        "synthetic_only": True,
        "scientific_output": False,
    }


def smoke_nonempty_proposal_pipeline(ctx, image_b, task_id, g_logits, g_taps,
                                     p_global, counters) -> dict:
    """§I: the REAL non-empty proposal pipeline through the shared proposal adapter."""
    base = _synthetic_geometry(p_global)
    base_geom = {"y1": int(base["y1"]), "y2": int(base["y2"]),
                 "x1": int(base["x1"]), "x2": int(base["x2"]),
                 "crop_side": int(base["crop_side_pixels"]),
                 "center_y": (int(base["y1"]) + int(base["y2"])) / 2.0,
                 "center_x": (int(base["x1"]) + int(base["x2"])) / 2.0}
    pert = C.apply_proposal_condition(base_geom, "SHIFT_LEFT_10",
                                      REGIONAL_CANVAS_RESOLUTION,
                                      REGIONAL_CANVAS_RESOLUTION)
    pert_geom = geom_from_proposal_row(pert)

    before = dict(counters)
    out = proposal_core_adapter(ctx, image_b, task_id, proposal_geometry=pert_geom,
                                g_logits=g_logits, g_taps=g_taps,
                                p_global_override=p_global, counters=counters)
    delta = {k: counters.get(k, 0) - before.get(k, 0) for k in set(counters) | set(before)}
    actual_b_phi = int(delta.get("b_phi_forwards", 0))
    return {
        "proposal_adapter_called": True,
        "proposal_condition": "SHIFT_LEFT_10",
        "base_crop_side": base_geom["crop_side"],
        "perturbed_crop_side": int(pert["crop_side"]),
        "geometry_changed": bool(int(pert["x1"]) != base_geom["x1"]),
        "router_vector_dim": out["router_vector_dim"],
        "router_vector_shape": out["router_vector_shape"],
        "router_vector_finite": bool(out["router_vector_finite"]),
        "router_score_finite": bool(out["delta_hat_final"] is not None
                                    and np.isfinite(out["delta_hat_final"])),
        "final_probability_finite": bool(
            out["final_probability"] is not None
            and np.isfinite(np.asarray(out["final_probability"])).all()),
        "final_probability_shape": (None if out["final_probability"] is None
                                    else list(np.asarray(out["final_probability"]).shape)),
        "state": out["state"],
        "router_decision": out["router_decision"],
        "forced_router_score": bool(out["forced_router_score"]),
        "actual_B_phi_forward_count": actual_b_phi,
        "real_B_phi_forward_proven": bool(actual_b_phi >= 1
                                          and out["forced_router_score"] is False),
        "actual_R_psi_forward_count": int(out["actual_r_psi_forward_count"]),
        "actual_S_omega_forward_count": int(out["actual_s_omega_forward_count"]),
        "g_forwards_during_proposal": delta.get("g_forwards", 0),
        "g_reused_from_clean": bool(delta.get("g_forwards", 0) == 0),
        "geometry_only_apply_counts_as_proposal_smoke": False,
    }


def smoke_empty_proposal_pipeline(ctx, image_b, task_id, g_logits, g_taps,
                                  p_global, counters) -> dict:
    """§J: the REAL empty-proposal path through the same shared proposal adapter."""
    before = dict(counters)
    out = proposal_core_adapter(ctx, image_b, task_id, proposal_geometry=None,
                                g_logits=g_logits, g_taps=g_taps,
                                p_global_override=p_global, counters=counters)
    delta = {k: counters.get(k, 0) - before.get(k, 0) for k in set(counters) | set(before)}
    return {
        "empty_proposal_adapter_called": True,
        "state": out["state"],
        "status_is_not_applicable_empty_proposal":
            bool(out["state"] == C.EMPTY_PROPOSAL_HANDLING),
        "handling": C.EMPTY_PROPOSAL_HANDLING,
        "actual_R_psi_forward_count": int(out["refiner_forward_count"]),
        "actual_S_omega_forward_count": int(out["s_omega_forward_count"]),
        "no_R_psi_forward": bool(out["refiner_forward_count"] == 0),
        "no_S_omega_forward": bool(out["s_omega_forward_count"] == 0),
        "no_replacement_geometry_generated": bool(
            out["replacement_geometry_generated"] is False),
        "no_geometry_returned": bool(out["geometry"] is None),
        "not_applicable": bool(out["not_applicable"]),
        "delta_counters": delta,
    }


def smoke_branch_controls(ctx, image_b, task_id, g_logits, g_taps, p_global) -> dict:
    """§D: POLICY-CONTROL branch coverage through the canonical core.

    Control scores force deterministic branch coverage; the decision itself is
    still produced by the canonical ``canonical_utility`` + frozen thresholds.
    These are POLICY CONTROLS, not scientific evidence, and they report the
    ACTUAL forward counts — a forced safety logit BYPASSES S_omega, so the
    expected actual S_omega forward count is 0.
    """
    from src.models.barr.ra_medfilm_barr import (canonical_utility,
                                                 TAU_C8_FINAL_FLOAT,
                                                 TAU_C7_FINAL)
    geom = _synthetic_geometry(p_global)
    # name, forced router score, forced safety logit, expected state,
    # expected final source, expected ACTUAL R_psi forwards, expected ACTUAL S_omega forwards
    controls = [
        ("CONTROL_SKIP_GLOBAL", -50.0, None, "SKIP_GLOBAL", "GLOBAL", 0, 0),
        ("CONTROL_EXECUTE_THEN_ACCEPT", +50.0, +50.0, "EXECUTE_THEN_ACCEPT", "REFINED", 1, 0),
        ("CONTROL_EXECUTE_THEN_REJECT", +50.0, -50.0, "EXECUTE_THEN_REJECT", "GLOBAL", 1, 0),
    ]
    cases = []
    for name, dh, lg, exp_state, exp_src, exp_r, exp_s in controls:
        counters = {}
        out = canonical_learned_core(ctx, image_b, task_id,
                                     g_logits=g_logits, g_taps=g_taps,
                                     p_global_override=p_global,
                                     proposal_geometry=geom, action_available=True,
                                     forced_delta_hat_final=dh,
                                     forced_s_omega_logit=lg,
                                     counters=counters)
        obs_state = out["state"]
        obs_src = _final_source_of(obs_state)
        actual_r = int(out["actual_r_psi_forward_count"])
        actual_s = int(out["actual_s_omega_forward_count"])
        cases.append({
            "case": name,
            "policy_control": True,
            "forced_router_score": bool(out["forced_router_score"]),
            "forced_safety_logit": bool(out["forced_safety_logit"]),
            "expected_state": exp_state,
            "observed_state": obs_state,
            "comparison_pass": bool(obs_state == exp_state),
            "expected_final_source": exp_src,
            "observed_final_source": obs_src,
            "final_source_comparison_pass": bool(obs_src == exp_src),
            "actual_R_psi_forward_count": actual_r,
            "expected_actual_R_psi_forward_count": exp_r,
            "R_psi_forward_count_pass": bool(actual_r == exp_r),
            "actual_S_omega_forward_count": actual_s,
            "expected_actual_S_omega_forward_count": exp_s,
            "S_omega_forward_count_pass": bool(actual_s == exp_s),
            "claims_real_S_omega_forward": bool(actual_s > 0),
            "router_decision": out["router_decision"],
            "router_decision_is_not_final_state": bool(
                out["router_decision"] in ROUTER_DECISIONS
                and out["router_decision"] != out["state"]),
            "utility": canonical_utility(dh),
            "threshold_C8": float(TAU_C8_FINAL_FLOAT),
            "threshold_C7": float(TAU_C7_FINAL),
            "forced_control_score": True,
        })
    return {"cases": cases,
            "policy_controls_not_scientific_outcomes": True,
            "policy_tests_not_scientific_outcomes": True,
            "forced_safety_controls_report_zero_actual_somega": bool(
                all(c["actual_S_omega_forward_count"] == 0
                    for c in cases if c["forced_safety_logit"])),
            "three_branches_covered": sorted({c["observed_state"] for c in cases}),
            "all_pass": bool(all(c["comparison_pass"] and c["R_psi_forward_count_pass"]
                                 and c["S_omega_forward_count_pass"] for c in cases)),
            "threshold_C7": float(TAU_C7_FINAL),
            "threshold_C8": float(TAU_C8_FINAL_FLOAT)}


def run_smoke() -> dict:
    """§I/§J/§K: construct + STRICT-load all FOUR real components and exercise the
    REAL shared learned-component core with synthetic tensors for the CLEAN, IMAGE,
    NON-EMPTY PROPOSAL and EMPTY PROPOSAL paths plus the three branch controls.
    """
    if _gate_smoke() != 0:
        raise SystemExit(2)
    import torch

    # §D22 (v1.9): DERIVE attempt provenance from actual on-disk state — the start
    # marker is created EXCLUSIVELY by main() (open("x")) BEFORE run_smoke() is
    # entered, so by construction it must exist exactly once and must NOT be
    # openable for exclusive re-creation.  `smoke_attempt_is_first_write_once` is
    # therefore computed from the observed marker state, never hard-coded.
    start_marker_path = ROOT / SMOKE_V1_11_START_MARKER
    _marker_exists = bool(start_marker_path.exists())
    _marker_sole_and_trueseal = False
    try:
        # Exclusive-create MUST now fail: proves the marker is first-write-once
        # and has NOT been overwritten/recreated.
        with open(start_marker_path, "x", encoding="utf-8"):
            pass
    except FileExistsError:
        _marker_sole_and_trueseal = True
    except OSError:
        _marker_sole_and_trueseal = False
    attempt_provenance = {
        "start_marker": SMOKE_V1_11_START_MARKER,
        "start_marker_preexisting_at_run_smoke_entry": _marker_exists,
        "exclusive_recreate_forbidden": _marker_sole_and_trueseal,
        "overwrite_permitted": False,
        "automatic_retry": False,
        "is_first_write_once": bool(_marker_exists and _marker_sole_and_trueseal),
    }
    if not attempt_provenance["is_first_write_once"]:
        raise RuntimeError(
            "D22_SMOKE_ATTEMPT_PROVENANCE_INVALID: "
            + json.dumps(attempt_provenance, default=str))

    # §G: Verify transitive runtime source integrity BEFORE model construction.
    source_integrity = _verify_transitive_source_integrity()
    if not source_integrity["all_match"]:
        raise RuntimeError(
            f"TRANSITIVE_RUNTIME_SOURCE_INTEGRITY_FAILED: "
            f"{json.dumps(source_integrity, indent=1, default=str)}")

    ctx = _load_models()
    audit = ctx["load_audit"]
    device = ctx["device"]
    ids = ["SYNTH_PHASE36_TASK0", "SYNTH_PHASE36_TASK1",
           "SYNTH_PHASE36_TASK2", "SYNTH_PHASE36_TASK3"]

    # ---- retained: image registry + noise determinism ---------------------- #
    x = _synth_image(0)
    image_rows = []
    for cid in C.image_condition_ids():
        spec = C.IMAGE_CONDITIONS[cid]
        seeds = spec.get("base_seeds") or [None]
        for bs in seeds:
            xp = C.apply_image_condition(x, cid, ids[0], bs)
            image_rows.append({
                "condition": cid, "base_seed": bs,
                "shape": list(np.asarray(xp).shape),
                "dtype": str(np.asarray(xp).dtype),
                "finite": bool(np.isfinite(xp).all()),
                "min": float(xp.min()), "max": float(xp.max()),
                "generated_from_original_clean": True})
    clean_identity = bool(np.array_equal(C.apply_image_condition(x, "CLEAN", ids[0]), x))
    a = C.apply_gaussian_noise(x, 0.02, ids[0], 42)
    b = C.apply_gaussian_noise(x, 0.02, ids[0], 42)
    c = C.apply_gaussian_noise(x, 0.02, ids[0], 123)
    d = C.apply_gaussian_noise(x, 0.02, ids[1], 42)
    det = {"same_inputs_identical": bool(np.array_equal(a, b)),
           "different_base_seed_differs": bool(not np.array_equal(a, c)),
           "different_sample_id_differs": bool(not np.array_equal(a, d))}

    # ---- ONE canonical batched G forward on the synthetic image ------------ #
    task_id = 0
    synth_np = np.stack([_synthetic_batch_image_np(0)] * 1, axis=0)
    x_b = canonical_images_tensor(ctx, synth_np)
    t_b = canonical_task_ids_tensor(ctx, [task_id])
    gout = canonical_g_forward_batched(ctx, x_b, t_b)
    g_logits = gout["logits"][0]
    g_probability = np.asarray(gout["probability"][0], dtype=np.float32)
    g_taps = {k: np.asarray(v[0]) for k, v in gout["taps"].items()}
    p_global = g_probability          # §D: the canonical probability from the G context
    g_forward_audit = {k: gout[k] for k in ("batch_size", "device", "autocast_enabled",
                                            "autocast_dtype", "inference_mode",
                                            "probability_operator", "probability_dtype")}

    # ---- REAL clean pipeline through the SHARED core ----------------------- #
    ctr_clean = {}
    out_clean = canonical_learned_core(ctx, x_b, task_id, g_logits=g_logits,
                                       g_probability=g_probability, g_taps=g_taps,
                                       counters=ctr_clean)
    clean_check = {
        "shared_core_called": True,
        "rf202_dim": out_clean["router_vector_dim"],
        "rf202_shape": out_clean["router_vector_shape"],
        # §G: bound to the ACTUAL 202-D router vector, NEVER to final_probability.
        "rf202_finite": bool(out_clean["router_vector_finite"]),
        "rf202_min": out_clean["router_vector_min"],
        "rf202_max": out_clean["router_vector_max"],
        "p_global_shape": list(p_global.shape),
        "p_global_finite": bool(np.isfinite(p_global).all()),
        "geometry_available": bool(out_clean["roi_available"]),
        "state": out_clean["state"],
        "router_decision": out_clean["router_decision"],
        "router_decision_is_not_final_state": bool(
            out_clean["router_decision"] in ROUTER_DECISIONS
            and out_clean["router_decision"] != out_clean["state"]),
        "final_probability_shape": list(np.asarray(out_clean["final_probability"]).shape),
        "final_probability_finite": bool(
            np.isfinite(np.asarray(out_clean["final_probability"])).all()),
        "global_forward_count": out_clean["global_forward_count"],
        "actual_R_psi_forward_count": out_clean["actual_r_psi_forward_count"],
        "actual_S_omega_forward_count": out_clean["actual_s_omega_forward_count"],
    }

    # ---- REAL image pipeline through the SHARED core ----------------------- #
    x_pert = C.apply_image_condition(_synth_image(0), "GAUSSIAN_NOISE_LOW", ids[0], 42)
    x_pert3 = np.stack([x_pert, x_pert, x_pert], axis=0)[None]
    xp_b = canonical_images_tensor(ctx, x_pert3)
    gout_img = canonical_g_forward_batched(ctx, xp_b, canonical_task_ids_tensor(ctx, [task_id]))
    ctr_img = {}
    out_img = canonical_learned_core(ctx, xp_b, task_id,
                                     g_logits=gout_img["logits"][0],
                                     g_probability=np.asarray(gout_img["probability"][0],
                                                              dtype=np.float32),
                                     g_taps={k: np.asarray(v[0]) for k, v in gout_img["taps"].items()},
                                     counters=ctr_img)
    image_check = {
        "shared_core_called": True,
        "state": out_img["state"],
        "router_decision": out_img["router_decision"],
        "final_finite": bool(np.isfinite(np.asarray(out_img["final_probability"])).all()),
        "actual_R_psi_forward_count": out_img["actual_r_psi_forward_count"],
        "actual_S_omega_forward_count": out_img["actual_s_omega_forward_count"],
    }

    # ---- §E GUARANTEED REAL EXECUTE-pipeline probe (R_psi + S_omega real) -- #
    execute_probe = smoke_real_execute_component_probe(
        ctx, x_b, task_id, g_logits, g_taps, p_global)

    # ---- §I/§J REAL proposal pipelines through the SAME shared core -------- #
    ctr_prop = {}
    proposal_check = smoke_nonempty_proposal_pipeline(
        ctx, x_b, task_id, g_logits, g_taps, p_global, ctr_prop)
    empty_check = smoke_empty_proposal_pipeline(
        ctx, x_b, task_id, g_logits, g_taps, p_global, ctr_prop)

    # ---- §K three branch controls ----------------------------------------- #
    sm = smoke_branch_controls(ctx, x_b, task_id, g_logits, g_taps, p_global)

    # ---- retained: metrics / HD95 / prediction consistency ----------------- #
    gt = np.zeros((512, 512), dtype=np.float32); gt[100:300, 100:300] = 1.0
    pred = np.zeros((512, 512), dtype=np.float32); pred[120:320, 120:320] = 1.0
    empty = np.zeros((512, 512), dtype=np.float32)
    metric_rows = {
        "nonempty_nonempty": {"dice": _dice(pred, gt), "iou": _iou(pred, gt)},
        "empty_empty": {"dice": _dice(empty, empty), "iou": _iou(empty, empty)},
        "empty_nonempty": {"dice": _dice(pred, empty), "iou": _iou(pred, empty)},
    }
    # §D25 (v1.9): FOUR explicit synthetic HD95 cases with the EXACT frozen
    # schema/reason/validity/non-finite behaviour bound per case (frozen
    # authority: src/metrics/evaluation_metrics.py::hd95, unchanged).
    hd_cases = {
        # nonempty prediction / nonempty GT -> valid True, finite, reason ""
        "nonempty_nonempty": _hd95(pred, gt),
        # empty prediction / NONEMPTY GT   -> valid False, nan, reason empty_prediction
        "empty_prediction_nonempty_gt": _hd95(empty, gt),
        # NONEMPTY prediction / empty GT   -> valid False, nan, reason empty_ground_truth
        "nonempty_prediction_empty_gt": _hd95(pred, empty),
        # empty / empty                    -> valid False, nan, reason both_empty
        "empty_empty": _hd95(empty, empty),
    }
    hd = hd_cases["nonempty_nonempty"]
    hd_empty = hd_cases["empty_prediction_nonempty_gt"]
    hd_summary = _finite_summary([hd.get("hd95", np.nan) if isinstance(hd, dict) else hd,
                                  hd_empty.get("hd95", np.nan)
                                  if isinstance(hd_empty, dict) else hd_empty])


    def _hd95_case_exact(case: dict, *, expect_valid, expect_reason) -> bool:
        """Exact frozen-schema predicate for ONE HD95 case."""
        if not isinstance(case, dict):
            return False
        if case.get("valid") is not expect_valid:
            return False
        if case.get("unit") != "pixel":
            return False
        if case.get("metric_domain") != "BOUNDARY_DISTANCE":
            return False
        if case.get("reason") != expect_reason:
            return False
        if expect_valid:
            return bool(np.isfinite(case.get("hd95", np.nan)))
        return bool(not np.isfinite(case.get("hd95", np.nan)))


    hd_case_exact = {
        "nonempty_nonempty": _hd95_case_exact(
            hd_cases["nonempty_nonempty"], expect_valid=True, expect_reason=""),
        "empty_prediction_nonempty_gt": _hd95_case_exact(
            hd_cases["empty_prediction_nonempty_gt"], expect_valid=False,
            expect_reason="empty_prediction"),
        "nonempty_prediction_empty_gt": _hd95_case_exact(
            hd_cases["nonempty_prediction_empty_gt"], expect_valid=False,
            expect_reason="empty_ground_truth"),
        "empty_empty": _hd95_case_exact(
            hd_cases["empty_empty"], expect_valid=False, expect_reason="both_empty"),
    }
    clean_mask = np.zeros((512, 512), dtype=np.float32); clean_mask[100:300, 100:300] = 1.0
    pert_mask = np.zeros((512, 512), dtype=np.float32); pert_mask[110:310, 110:310] = 1.0
    pc_dice = _prediction_consistency_dice(pert_mask, clean_mask)

    # ---- §H FROZEN TOP-LEVEL SMOKE SUCCESS CONTRACT ------------------------ #
    comp = audit["components"]
    binding = ctx["component_device_binding"]
    cases_by_name = {c["case"]: c for c in sm["cases"]}
    forced_safety_cases = [c for c in sm["cases"] if c["forced_safety_logit"]]
    smoke_checks = {
        "transitive_runtime_source_integrity_pass": bool(
            source_integrity.get("all_match", False)),
        "four_component_checkpoint_loads_strict": bool(
            all(comp[c]["strict_load_ok"] for c in ("G", "B_phi", "R_psi", "S_omega"))),
        "four_parameter_counts_exact": bool(
            all(comp[c]["parameter_count"] == comp[c]["parameter_count_expected"]
                for c in ("G", "B_phi", "R_psi", "S_omega"))),
        "all_component_weights_finite": bool(
            all(comp[c]["all_weights_finite"] for c in ("G", "B_phi", "R_psi", "S_omega"))),
        "four_components_on_canonical_cuda_device": bool(
            all(binding[c]["on_canonical_device"]
                for c in ("G", "B_phi", "R_psi", "S_omega"))),
        "canonical_G_probability_dtype_float32": bool(
            gout.get("probability_dtype") == "float32"),
        "canonical_G_output_finite": bool(np.isfinite(g_probability).all()),
        "router_vector_dim_exactly_202": bool(clean_check["rf202_dim"] == ROUTER_NUMERIC_DIM),
        "router_vector_finite": bool(clean_check["rf202_finite"] is True),
        "real_B_phi_forward_proven": bool(proposal_check["real_B_phi_forward_proven"]),
        "real_R_psi_forward_proven": bool(
            execute_probe["actual_R_psi_forward_count"] == 1),
        "real_S_omega_forward_proven": bool(
            execute_probe["actual_S_omega_forward_count"] == 1),
        # §E/D20: real execute numerical validation bound to smoke_all_pass
        "real_execute_router_decision_is_execute": bool(
            execute_probe.get("router_decision") == "EXECUTE"),
        "real_execute_R_psi_output_finite": bool(
            execute_probe.get("refined_output_finite") is True),
        "real_execute_R_psi_output_shape_valid": bool(
            execute_probe.get("refined_output_shape") is not None
            and len(execute_probe.get("refined_output_shape", [])) == 2),
        "real_execute_post_safety_feature_dim_16": bool(
            execute_probe.get("post_safety_feature_dim") == SOMEGA_NUMERIC_DIM),
        "real_execute_post_safety_features_finite": bool(
            execute_probe.get("post_safety_features_finite") is True),
        "real_execute_S_omega_logit_finite": bool(
            execute_probe.get("post_safety_logit_finite") is True),
        "real_execute_S_omega_probability_finite": bool(
            execute_probe.get("post_safety_accept_probability_finite") is True),
        "real_execute_S_omega_probability_in_unit_interval": bool(
            execute_probe.get("post_safety_accept_probability_in_unit_interval") is True),
        "real_execute_final_state_valid": bool(
            execute_probe.get("observed_state") in ("EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT")),
        "real_execute_final_probability_shape_512x512": bool(
            execute_probe.get("final_probability_shape") == [512, 512]),
        "real_execute_final_probability_finite": bool(
            execute_probe.get("final_probability_finite") is True),
        "clean_synthetic_final_probability_finite": bool(
            clean_check["final_probability_finite"]),
        "image_synthetic_final_probability_finite": bool(image_check["final_finite"]),
        "nonempty_proposal_adapter_called": bool(proposal_check["proposal_adapter_called"]),
        "empty_proposal_adapter_called": bool(empty_check["empty_proposal_adapter_called"]),
        "empty_proposal_R_psi_zero": bool(empty_check["no_R_psi_forward"]),
        "empty_proposal_S_omega_zero": bool(empty_check["no_S_omega_forward"]),
        "empty_proposal_no_replacement_geometry": bool(
            empty_check["no_replacement_geometry_generated"]),
        "skip_policy_control_exact": bool(
            cases_by_name["CONTROL_SKIP_GLOBAL"]["comparison_pass"]),
        "accept_policy_control_exact": bool(
            cases_by_name["CONTROL_EXECUTE_THEN_ACCEPT"]["comparison_pass"]),
        "reject_policy_control_exact": bool(
            cases_by_name["CONTROL_EXECUTE_THEN_REJECT"]["comparison_pass"]),
        "forced_control_counts_reported_honestly": bool(
            all(c["actual_S_omega_forward_count"] == 0
                and c["claims_real_S_omega_forward"] is False
                for c in forced_safety_cases)),
        "perturbation_registry_outputs_finite": bool(
            all(r["finite"] for r in image_rows)),
        "clean_perturbation_bitwise_identity": bool(clean_identity),
        "gaussian_noise_same_input_determinism": bool(det["same_inputs_identical"]),
        "different_seed_changes_realization": bool(det["different_base_seed_differs"]),
        "different_synthetic_sample_id_changes_realization": bool(
            det["different_sample_id_differs"]),
        # §F/D21/D25: HD95 bound to smoke success contract, using the FROZEN
        # metric authority (src/metrics/evaluation_metrics.py::hd95).  Each of
        # the FOUR synthetic cases is bound to its EXACT frozen reason — the
        # empty-prediction/nonempty-GT case is bound to exactly
        # "empty_prediction", NOT any generic member of the reason set.
        "metric_dice_iou_plumbing_valid": bool(
            all(np.isfinite(v["dice"]) and np.isfinite(v["iou"])
                for v in metric_rows.values())),
        "metric_hd95_nonempty_plumbing_valid": bool(hd_case_exact["nonempty_nonempty"]),
        "metric_hd95_empty_mask_semantics_valid": bool(
            hd_case_exact["empty_prediction_nonempty_gt"]),
        "metric_hd95_nonempty_prediction_empty_gt_exact": bool(
            hd_case_exact["nonempty_prediction_empty_gt"]),
        "metric_hd95_empty_empty_exact": bool(hd_case_exact["empty_empty"]),
        # §D24 (v1.9): R_psi exact shape + sigmoid-probability RANGE.
        "real_execute_R_psi_output_exact_shape": bool(
            execute_probe.get("refined_output_shape") == [REGIONAL_INPUT_RESOLUTION,
                                                          REGIONAL_INPUT_RESOLUTION]),
        "real_execute_R_psi_output_in_unit_interval": bool(
            execute_probe.get("refined_output_is_probability") is True
            and execute_probe.get("refined_output_in_unit_interval") is True),
        # §D24 (v1.9): final S_omega input exact schema dimension + finiteness.
        "real_execute_final_S_omega_input_exact_dim": bool(
            execute_probe.get("final_s_omega_input_dim")
            == SOMEGA_FINAL_INPUT_DIM),
        "real_execute_final_S_omega_input_finite": bool(
            execute_probe.get("final_s_omega_input_finite") is True),
        "prediction_consistency_metric_finite": bool(np.isfinite(pc_dice)),
        "protected_test_holdout_runtime_io_statically_unreachable": bool(
            _static_protected_io_unreachable()),
        # §D22 (v1.9): DERIVED from ACTUAL provenance state (never hard-coded).
        "smoke_attempt_is_first_write_once": bool(attempt_provenance["is_first_write_once"]),
        "scientific_output_false": True,      # immutable classification field
        "synthetic_only_true": True,          # immutable classification field
    }
    # §CHECK-MATRIX RECONCILIATION (v1.9): declared IDs, dict bindings and
    # reported count must agree EXACTLY.
    missing_ids = [k for k in SMOKE_CHECK_IDS if k not in smoke_checks]
    extra_ids = [k for k in smoke_checks if k not in SMOKE_CHECK_IDS]
    if missing_ids or extra_ids:
        raise AssertionError(
            f"SMOKE_CHECK_CONTRACT_MISMATCH: missing={missing_ids} extra={extra_ids}")
    if set(SMOKE_CHECK_IDS) != set(smoke_checks.keys()):
        raise AssertionError("SMOKE_CHECK_CONTRACT_SET_MISMATCH")
    if len(SMOKE_CHECK_IDS) != len(smoke_checks):
        raise AssertionError(
            f"SMOKE_CHECK_CONTRACT_COUNT_MISMATCH: "
            f"{len(SMOKE_CHECK_IDS)} != {len(smoke_checks)}")
    smoke_all_pass = bool(all(smoke_checks.values()))

    return {
        "mode": "smoke",
        "classification": "PRE_SCIENTIFIC_SYNTHETIC_FULL_PIPELINE_ROBUSTNESS_VALIDATION",
        "not_phase36_scientific_robustness_result": True,
        "synthetic_only": True,
        "scientific_output": False,
        "four_real_components_loaded": True,
        "shared_core": "canonical_learned_core",
        "shared_core_used_by_science_and_smoke": True,
        "component_load_audit": audit,
        "g_forward_audit": g_forward_audit,
        "synthetic_sample_ids": ids,
        "image_registry": image_rows,
        "clean_bitwise_identity": clean_identity,
        "determinism": det,
        "clean_pipeline_check": clean_check,
        "image_pipeline_check": image_check,
        "real_execute_component_probe": execute_probe,
        "proposal_pipeline_check": proposal_check,
        "empty_proposal_check": empty_check,
        "state_machine": sm,
        "metrics": metric_rows,
        "prediction_consistency_dice_smoke": pc_dice,
        "hd95_hd": hd, "hd95_hd_empty_case": hd_empty, "hd95_summary": hd_summary,
        "seed_conversion": C.seed_conversion_audit(),
        "smoke_success_contract": dict(SMOKE_SUCCESS_CONTRACT),
        "smoke_checks": smoke_checks,
        "smoke_all_pass": smoke_all_pass,
        "n_smoke_checks": len(smoke_checks),
        "failed_smoke_checks": sorted(k for k, v in smoke_checks.items() if not v),
        "pipeline_covered": ["four_component_strict_load",
                             "canonical_batched_G_autocast_fp16",
                             "clean_pipeline_via_shared_core",
                             "image_perturbation_via_shared_core",
                             "real_execute_component_probe",
                             "nonempty_proposal_via_shared_core",
                             "empty_proposal_via_shared_core",
                             "state_machine_branch_controls",
                             "prediction_consistency_metric", "metric_plumbing",
                             "route_state_plumbing", "router_decision_separation",
                             "actual_forward_count_accounting"],
        "generated_utc": now(),
    }


def _smoke_attempt_already_exists() -> bool:
    """§D22: True if a canonical v1.9 smoke artifact OR start-marker exists.

    Either presence means a first attempt has ALREADY been consumed, so a second
    attempt must be refused (write-once, no retry, no overwrite).
    """
    return ((ROOT / SMOKE_V1_11_ARTIFACT).exists()
            or (ROOT / SMOKE_V1_11_START_MARKER).exists())


def _create_smoke_start_marker(*, source_sha=None, smoke_gate_state=None) -> bool:
    """§D22: EXCLUSIVE-CREATE the smoke start marker (write-once).

    Returns True iff THIS call performed the first write. Uses low-level
    ``os.open(..., O_CREAT | O_EXCL | O_WRONLY)`` so the create is atomic and
    can NEVER overwrite an existing marker. Must be called AFTER the smoke gate
    has been authorized (§D22 authorized-attempt ordering).
    """
    import os
    path = ROOT / SMOKE_V1_11_START_MARKER
    path.parent.mkdir(parents=True, exist_ok=True)
    marker = {
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_11",
        "mode": "smoke",
        "artifact_kind": "SMOKE_START_MARKER",
        "attempted": True,
        "authorized_attempt": True,
        "gate_authorized_before_marker": True,
        "source_sha256": source_sha,
        "smoke_gate_state": smoke_gate_state,
        "automatic_retry": False,
        "overwrite_permitted": False,
        "write_semantics": "O_CREAT|O_EXCL (exclusive-create, write-once)",
        "scientific_output": False,
        "synthetic_only": True,
        "generated_utc": now(),
    }
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        os.write(fd, json.dumps(marker, indent=1, ensure_ascii=False,
                                default=str).encode("utf-8"))
    finally:
        os.close(fd)
    return True


def _write_smoke_failure_artifact(*, exception=False, exc_type=None, exc_msg=None,
                                  failing_stage=None, source_sha=None,
                                  smoke_gate_state=None, synthetic_only=True) -> bool:
    """§D22: Write the DISTINCT FAILED smoke artifact (separate from start marker).

    Uses EXCLUSIVE-CREATE (``open(..., "x")``) so it can NEVER overwrite an
    existing failure artifact — no silent re-write, no retry. Called for BOTH
    exception paths and logical failure paths. Returns True iff it was the first
    write of the failure artifact.
    """
    artifact = {
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_11",
        "mode": "smoke",
        "artifact_kind": "SMOKE_FAILURE_ARTIFACT",
        "attempted": True,
        "completed": False,
        "smoke_all_pass": False,
        "exception": bool(exception),
        "exception_type": exc_type,
        "exception_message": exc_msg,
        "failing_stage": failing_stage,
        "source_sha256": source_sha,
        "smoke_gate_state": smoke_gate_state,
        "automatic_retry": False,
        "overwrite_permitted": False,
        "write_semantics": "open(x) (exclusive-create, write-once)",
        "scientific_output": False,
        "synthetic_only": bool(synthetic_only),
        "generated_utc": now(),
        "terminal": "PHASE36_V1_11_SMOKE_FIRST_ATTEMPT_FAILED__ARTIFACT_PRESERVED__NO_RETRY",
    }
    path = ROOT / SMOKE_V1_11_FAILURE_ARTIFACT
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", encoding="utf-8") as fh:   # exclusive-create, write-once
        fh.write(json.dumps(artifact, indent=1, ensure_ascii=False, default=str))
    return True


def _write_smoke_success_artifact(res: dict, *, source_sha=None) -> bool:
    """§D22: EXCLUSIVE-CREATE the canonical v1.9 smoke success artifact.

    Returns True iff this call performed the first write. Never overwrites.
    """
    path = ROOT / SMOKE_V1_11_ARTIFACT
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(res)
    payload.setdefault("source_sha256", source_sha)
    payload["write_semantics"] = "open(x) (exclusive-create, write-once)"
    with open(path, "x", encoding="utf-8") as fh:   # exclusive-create, write-once
        fh.write(json.dumps(payload, indent=1, ensure_ascii=False, default=str))
    return True


# --------------------------------------------------------------------------- #
# §D28/D31/D32 (v1.11) — SCIENCE ATTEMPT PROVENANCE (write-once, first-attempt)
# --------------------------------------------------------------------------- #
def _science_attempt_already_exists() -> bool:
    """§D32: True if ANY v1.11 science artifact (result OR start-marker) exists.

    A start marker alone means an authorized attempt was consumed (even if the
    run later failed), so a second attempt MUST be refused.  The historical
    v1.8/v1.9 science path is NEVER consulted as provenance.
    """
    return ((ROOT / SCIENCE_V1_11_ARTIFACT).exists()
            or (ROOT / SCIENCE_V1_11_START_MARKER).exists()
            or (ROOT / SCIENCE_V1_11_FAILURE_ARTIFACT).exists())


def _create_science_start_marker(*, source_sha=None, science_gate_state=None) -> bool:
    """§D32: EXCLUSIVE-CREATE the science start marker (write-once).

    Mirrors the smoke start marker.  Must be called AFTER the science gate has
    been authorized AND after the science revision is confirmed unconsumed.
    """
    import os
    path = ROOT / SCIENCE_V1_11_START_MARKER
    path.parent.mkdir(parents=True, exist_ok=True)
    marker = {
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_11",
        "mode": "science",
        "artifact_kind": "SCIENCE_START_MARKER",
        "attempted": True,
        "authorized_attempt": True,
        "gate_authorized_before_marker": True,
        "source_sha256": source_sha,
        "science_gate_state": science_gate_state,
        "automatic_retry": False,
        "overwrite_permitted": False,
        "write_semantics": "O_CREAT|O_EXCL (exclusive-create, write-once)",
        "scientific_output": False,
        "generated_utc": now(),
    }
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        os.write(fd, json.dumps(marker, indent=1, ensure_ascii=False,
                                default=str).encode("utf-8"))
    finally:
        os.close(fd)
    return True


def _write_science_failure_artifact(*, termination_kind=None, exception=False,
                                    exc_type=None, exc_msg=None, exit_code=None,
                                    failing_stage=None, source_sha=None,
                                    science_gate_state=None) -> bool:
    """§D32: Write the DISTINCT FAILED science artifact (exclusive-create).

    ``termination_kind`` is one of: EXCEPTION, SYSTEM_EXIT, LOGICAL_FAILURE.
    Uses EXCLUSIVE-CREATE (``open(..., "x")``) so it can NEVER overwrite.
    """
    artifact = {
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_11",
        "mode": "science",
        "artifact_kind": "SCIENCE_FAILURE_ARTIFACT",
        "attempted": True,
        "completed": False,
        "termination_kind": termination_kind,
        "exception": bool(exception),
        "exception_type": exc_type,
        "exception_message": exc_msg,
        "exit_code": exit_code,
        "failing_stage": failing_stage,
        "source_sha256": source_sha,
        "science_gate_state": science_gate_state,
        "automatic_retry": False,
        "overwrite_permitted": False,
        "write_semantics": "open(x) (exclusive-create, write-once)",
        "scientific_output": False,
        "generated_utc": now(),
        "terminal": "PHASE36_V1_11_SCIENCE_FIRST_ATTEMPT_FAILED__ARTIFACT_PRESERVED__NO_RETRY",
    }
    path = ROOT / SCIENCE_V1_11_FAILURE_ARTIFACT
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", encoding="utf-8") as fh:   # exclusive-create, write-once
        fh.write(json.dumps(artifact, indent=1, ensure_ascii=False, default=str))
    return True


def _write_science_success_artifact(res: dict, *, source_sha=None) -> bool:
    """§D31/D32: EXCLUSIVE-CREATE the canonical v1.11 science result artifact.

    Written to the UNIQUE v1.11 path, never the historical v1.8/v1.9 path.
    """
    path = ROOT / SCIENCE_V1_11_ARTIFACT
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(res)
    payload.setdefault("source_sha256", source_sha)
    payload["write_semantics"] = "open(x) (exclusive-create, write-once)"
    with open(path, "x", encoding="utf-8") as fh:   # exclusive-create, write-once
        fh.write(json.dumps(payload, indent=1, ensure_ascii=False, default=str))
    return True


def _run_science_with_durable_evidence() -> int:
    """§D32: Invoke ``run_science()`` and durably record EVERY termination mode.

    Returns a process exit code.  Guarantees that after an authorized attempt,
    SOME durable evidence (success artifact, failure artifact) survives, whether
    the run terminated normally, by a logical fail-closed SystemExit, or by an
    ordinary Exception.  The start marker (created earlier) is preserved forever.
    """
    try:
        res = run_science()
    except SystemExit as exc:
        _write_science_failure_artifact(
            termination_kind="SYSTEM_EXIT",
            exit_code=(exc.code if isinstance(exc.code, int) else None),
            exc_type="SystemExit",
            exc_msg=(None if exc.code is None else str(exc.code)),
            failing_stage="run_science_system_exit",
            source_sha=_sha(Path(__file__)),
            science_gate_state="SYSTEM_EXIT_DURING_SCIENCE_EXECUTION")
        return 1
    except Exception as exc:
        _write_science_failure_artifact(
            termination_kind="EXCEPTION",
            exception=True,
            exc_type=type(exc).__name__,
            exc_msg=str(exc),
            failing_stage="run_science_exception",
            source_sha=_sha(Path(__file__)),
            science_gate_state="EXCEPTION_DURING_SCIENCE_EXECUTION")
        return 1
    # Normal return: require the scientific result to be well-formed, else durable
    # logical-failure evidence.
    if not bool(res.get("classification") == "PHASE36_ROBUSTNESS_SCIENTIFIC_RESULT"):
        _write_science_failure_artifact(
            termination_kind="LOGICAL_FAILURE",
            failing_stage="science_result_malformed",
            source_sha=_sha(Path(__file__)),
            science_gate_state="SCIENCE_RAN__RESULT_MALFORMED")
        return 1
    _write_science_success_artifact(res, source_sha=_sha(Path(__file__)))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=C.MODES)
    a = ap.parse_args()
    if a.mode == "science":
        # §D32 AUTHORIZED-ATTEMPT ORDERING (v1.11):
        #   (1) authorize the attempt FIRST (PHASE36_EXECUTE);
        #   (2) confirm the v1.11 science revision is UNCONSUMED (fail closed);
        #   (3) atomically EXCLUSIVE-CREATE the science START marker BEFORE any
        #       model construction or VAL808 access;
        #   (4) invoke science with durable Exception / SystemExit / logical
        #       failure evidence; success writes exactly one result artifact;
        #   (5) NEVER create the start marker if the gate is absent.
        gate_state = _gate_science_state()
        if gate_state != "AUTHORIZED":
            print(json.dumps({
                "mode": "science",
                "science_gate_state": gate_state,
                "terminal": "PHASE36_V1_11_SCIENCE_NOT_AUTHORIZED__NO_MARKER_CREATED",
                "marker_created": False,
                "automatic_retry": False,
                "overwrite_permitted": False,
            }, indent=1))
            return 2
        if _science_attempt_already_exists():
            print(json.dumps({
                "mode": "science",
                "terminal": "PHASE36_V1_11_SCIENCE_REEXECUTION_FORBIDDEN__FIRST_ATTEMPT_ALREADY_EXISTS",
                "automatic_retry": False,
                "overwrite_permitted": False,
            }, indent=1))
            return 1
        try:
            _create_science_start_marker(
                source_sha=_sha(Path(__file__)),
                science_gate_state="GATE_AUTHORIZED__MARKER_CREATED_PRE_MODEL_CONSTRUCTION")
        except FileExistsError:
            print(json.dumps({
                "mode": "science",
                "terminal": "PHASE36_V1_11_SCIENCE_START_MARKER_ALREADY_EXISTS__NO_RETRY",
                "automatic_retry": False,
                "overwrite_permitted": False,
            }, indent=1))
            return 1
        return _run_science_with_durable_evidence()

    if a.mode == "smoke":
        # §D22 AUTHORIZED-ATTEMPT ORDERING (v1.9):
        #   (1) authorize the attempt: hold the PHASE36_SMOKE_EXECUTE gate FIRST;
        #   (2) only THEN create the start marker (exclusive-create, write-once);
        #   (3) never create the marker if the gate is absent/failed.
        gate_state = _gate_smoke_state()
        if gate_state != "AUTHORIZED":
            print(json.dumps({
                "mode": "smoke",
                "smoke_all_pass": False,
                "smoke_gate_state": gate_state,
                "terminal": "PHASE36_V1_11_SMOKE_NOT_AUTHORIZED__NO_MARKER_CREATED",
                "marker_created": False,
                "automatic_retry": False,
                "overwrite_permitted": False,
            }, indent=1))
            return 2
        # (1b) fail closed if a first attempt was ALREADY consumed.
        if _smoke_attempt_already_exists():
            print(json.dumps({
                "mode": "smoke",
                "smoke_all_pass": False,
                "terminal": "PHASE36_V1_11_SMOKE_REEXECUTION_FORBIDDEN__FIRST_ATTEMPT_ALREADY_EXISTS",
                "automatic_retry": False,
                "overwrite_permitted": False,
            }, indent=1))
            return 1
        # (2) authorized -> atomically EXCLUSIVE-CREATE the start marker.
        try:
            _create_smoke_start_marker(
                source_sha=_sha(Path(__file__)),
                smoke_gate_state="GATE_AUTHORIZED__MARKER_CREATED_PRE_MODEL_CONSTRUCTION")
        except FileExistsError:
            print(json.dumps({
                "mode": "smoke",
                "smoke_all_pass": False,
                "terminal": "PHASE36_V1_11_SMOKE_START_MARKER_ALREADY_EXISTS__NO_RETRY",
                "automatic_retry": False,
                "overwrite_permitted": False,
            }, indent=1))
            return 1
        # (3) run the smoke; exceptions -> durable DISTINCT failure artifact.
        try:
            res = run_smoke()
        except Exception as exc:
            _write_smoke_failure_artifact(
                exception=True,
                exc_type=type(exc).__name__,
                exc_msg=str(exc),
                failing_stage="run_smoke_exception",
                source_sha=_sha(Path(__file__)),
                smoke_gate_state="EXCEPTION_DURING_SMOKE_EXECUTION")
            print(json.dumps({
                "mode": "smoke",
                "smoke_all_pass": False,
                "exception": True,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "terminal": "PHASE36_V1_11_SMOKE_EXCEPTION__ARTIFACT_PRESERVED__NO_RETRY",
                "automatic_retry": False,
                "overwrite_permitted": False,
            }, indent=1))
            return 1
        # Normal path: durable success artifact (exclusive-create; write to the
        # failure artifact instead when the contract did not hold).
        if not bool(res.get("smoke_all_pass")):
            _write_smoke_failure_artifact(
                exception=False,
                failing_stage="smoke_contract_not_satisfied",
                source_sha=_sha(Path(__file__)),
                smoke_gate_state="SMOKE_RAN__CONTRACT_FAILED")
            print(json.dumps({
                "mode": "smoke",
                "smoke_all_pass": False,
                "failed_smoke_checks": res.get("failed_smoke_checks"),
                "artifact_preserved": SMOKE_V1_11_FAILURE_ARTIFACT,
                "automatic_retry": False,
                "terminal": "PHASE36_V1_11_SMOKE_FAILED__ARTIFACT_PRESERVED__NO_RETRY",
            }, indent=1))
            return 1
        _write_smoke_success_artifact(res, source_sha=_sha(Path(__file__)))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
