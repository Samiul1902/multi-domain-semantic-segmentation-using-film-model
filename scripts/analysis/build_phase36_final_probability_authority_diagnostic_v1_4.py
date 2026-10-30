#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.4 — GOVERNANCE BUILDER.

Write-once generator for the 7 governance artifacts of the ADDITIVE v1.4 family
``ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_4``:

    reports/audits/phase36_final_probability_authority_diagnostic_contract_v1_4.json
    reports/audits/phase36_final_probability_authority_diagnostic_source_freeze_v1_4.json
    reports/audits/phase36_final_probability_authority_diagnostic_preflight_v1_4.json
    reports/audits/phase36_final_probability_authority_diagnostic_negative_controls_v1_4.json
    reports/audits/phase36_final_probability_authority_diagnostic_eligibility_v1_4.json
    reports/audits/phase36_final_probability_authority_diagnostic_no_execution_audit_v1_4.json
    reports/audits/phase36_final_probability_authority_diagnostic_v1_3_to_v1_4_diff.json

================================================================================
v1.4 IS AN OBSERVABILITY-ONLY ADDITIVE REPLAY OF v1.3.  THE SCIENTIFIC PATH IS
UNCHANGED FROM v1.3 (which itself changed ONLY the D61 ACCEPT final-fusion call).
================================================================================

The v1.4 family exists to prove — with crash-SURVIVABLE, durable evidence — that
the D61 canonical ACCEPT-fusion repair reproduces the frozen Phase27 authority
bit-identically.  It carries over v1.3's single scientific-path change:

    D61 = ACCEPT_FINAL_FUSION_SEMANTICS_DIVERGE_FROM_PHASE27

...and adds ONLY observability instrumentation:

  * D69 — scientific-path identity proof (AST comparison of the v1.4 repaired
          core vs the v1.3 repaired core after removing observability statements;
          ``scientific_path_unchanged`` is DERIVED, never hard-coded).
  * (c)  crash-survivable write-once stage journal
         (reports/audits/phase36_final_probability_authority_diagnostic_v1_4_journal/).
  * (d)  GT-free progress checkpoints during the 808 clean-row loop.
  * (e)  D70 — journal non-interference proof (identical outputs with the journal
         enabled vs disabled).
  * (f)  a durable supervisor process/exit artifact
         (reports/audits/phase36_final_probability_authority_diagnostic_process_exit_v1_4.json).
  * (g)  synthetic abrupt-termination fixtures (temporary dirs ONLY).

The v1.4 diagnostic SHARES the v1.3 single scientific change and adds NO other
scientific change: G, router, router normalization, router threshold, ROI
proposal, ROI geometry, rf202, R_psi, R_psi checkpoint, R_psi preprocessing,
S_omega, S_omega normalization, S_omega threshold, task IDs, sample order, final
threshold, float32->float16 authority comparison, GT handling, and metrics are
ALL unchanged.

D67/D68 ARE PRESERVED (NOT reinterpreted): the consumed v1.3 attempt remains
``CONSUMED_TERMINAL_EVIDENCE_ANOMALY`` with ``retry_permitted=false``,
``root_cause=UNRESOLVED`` and ``termination_mechanism=UNRESOLVED``.

================================================================================
D55/D57/D66/D59 REMEDIATION (STRUCTURAL)
================================================================================
Historically the Phase27 per-sample scores SHA was RETYPED into each governance
builder, and the single-hex transcription error was re-introduced FOUR times
(D55 -> v1.1, D57 -> v1.2, D66 -> v1.3, D59 -> v1.2 reconciliation).  This builder
does NOT retype it: it DERIVES the canonical value by hashing the authority file
PROGRAMMATICALLY (``_derive_phase27_scores_sha``), and it asserts that the
incorrect historical literal appears NOWHERE in the v1.4 runtime/governance family.

It runs the unit / preflight / negative-control suites + the launcher
``--verify-only`` + the supervisor synthetic self-test (all NON-consuming) and
embeds their results.

NO model, NO CUDA, NO checkpoint, NO VAL/GT.  Nothing is consumed.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\build_phase36_final_probability_authority_diagnostic_v1_4.py
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts" / "analysis"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

VENV = ROOT / ".venv" / "Scripts" / "python.exe"
AUD = ROOT / "reports" / "audits"

REVISION = "ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_4"
SUPERSEDES_NOTE = ("v1.0/v1.1/v1.2/v1.3 remain byte-for-byte frozen; v1.3 is CONSUMED "
                   "(TERMINAL_EVIDENCE_ANOMALY; retry FORBIDDEN).  v1.4 is an observability-only "
                   "additive replay of v1.3: scientific path UNCHANGED (D61 ACCEPT fusion only).")

DIAG = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_4.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_4.py"
SUPERVISOR = ROOT / "scripts/analysis/supervise_phase36_final_probability_authority_diagnostic_v1_4.py"
UNIT = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_4.py"
PREFLIGHT = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_4.py"
NEGCTRL = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_4.py"

V14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
MANIFEST = AUD / "phase36_v1_14_runtime_source_integrity_manifest.json"

# Frozen pins (LITERAL — verified before writing anything).
DIAG_SHA = "778af67fe41e44cec0717365b2c3427bcfd43442145af09a7aca2abe1f4a3eab"
LAUNCH_SHA = "221a15a1f2dd341c59a65d9f8c0f57f4e339ff5a66f8bece6c7b2a5d8ad10a0a"
SUPERVISOR_SHA = "792302085ccde4f09bfc7d3ca6534f411a9b776b54cbca5b83e8a7ad02277c2b"
UNIT_SHA = "a4f1ddb854847435388e1dd9984812bc0b295c42443f63c76ac5d55c01b34738"
PREFLIGHT_SHA = "bb14fca6f9344459f9c812d61de6c1abf90fd5fe7d8a966d46a6ca10fbadc1ec"
NEGCTRL_SHA = "492c03fd231969dc80347713c3106c7970854d060d2d5780e285ffbac8372256"
V14_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

ONE_SHOT_ENV = "PHASE36_FINAL_PROB_AUTHORITY_EXECUTE"
LAUNCH_AUTHORITY_TOKEN = "PHASE36_FINAL_PROB_AUTHORITY_V1_4_LAUNCH_AUTHORITY"
FOREIGN_TOKEN = "PHASE36_V1_14_LAUNCH_AUTHORITY"

# ---- D55/D57/D66/D59 remediation: DERIVE, never retype -------------------- #
PHASE27_SCORES_CSV = "reports/tables/phase27_val808_per_sample_scores.csv"
# The historical single-hex transcription error.  Stored ASSEMBLED FROM PARTS so the
# incorrect literal can NEVER appear verbatim in this source file (and the self-check
# below asserts its absence from the whole v1.4 family).
_INCORRECT_HEAD = "702133930ce14ac9513c992833396e3e250d08417"
_INCORRECT_TAIL = "a17d1032cbd260a405cfb12"
INCORRECT_HISTORICAL_SHA_ASSEMBLED = _INCORRECT_HEAD + _INCORRECT_TAIL
# The canonical value is DERIVED by hashing the authority file (never retyped).
CANONICAL_PHASE27_SCORES_SHA = hashlib.sha256(
    (ROOT / PHASE27_SCORES_CSV).read_bytes()).hexdigest() if (ROOT / PHASE27_SCORES_CSV).exists() else "ABSENT"

# v1.0 family MUST remain byte-for-byte frozen.
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

# v1.1 family MUST remain byte-for-byte frozen (CONSUMED_FAILED; RETRY FORBIDDEN).
V1_1_PRESERVED = {
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
    "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_1.py":
        "498c7460c3e588317f3741da8fbcbf4886a660aec5ba0aa880422f8d7f6200f8",
    "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_1_governance_reconciliation_v1_0.py":
        "9518a0ceef65bb3a4ce97d4e2fa6fe89f881b03674e49b1ea593e429ec5d9309",
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_1_governance_reconciliation_v1_0.json":
        "124327dca073afa440e187aa1999c4f463fb97a1fe62e30ce19b6bcfa8b966f4",
    "reports/audits/phase36_final_probability_authority_diagnostic_contract_v1_1.json":
        "84398af09ad814c8d1d326bac20aaee9ee1400e09d1a18baf12b8448b543967c",
    "reports/audits/phase36_final_probability_authority_diagnostic_source_freeze_v1_1.json":
        "a93a9aaa7e22b96d42c80a64d08f2576fcdfcf08e947643c7272d593ab967b0b",
    "reports/audits/phase36_final_probability_authority_diagnostic_preflight_v1_1.json":
        "0bfc783b342a5c9f9e1ae7473240c80b442a27e85ed4a0b61af3c80652c42819",
    "reports/audits/phase36_final_probability_authority_diagnostic_negative_controls_v1_1.json":
        "a8ff8347fc0a54ebfb4ffefadfe8d94163f8026186c4c51224dee24f2aa7fb34",
    "reports/audits/phase36_final_probability_authority_diagnostic_eligibility_v1_1.json":
        "bd2fd129f59848faaaed9fa7c400eca0ce693d2d3cb25beaa18d8c0488210aac",
    "reports/audits/phase36_final_probability_authority_diagnostic_no_execution_audit_v1_1.json":
        "6394c88552ef9a1ebd57de2e023466a256596f09affd20582b95db8b119e2a29",
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_0_to_v1_1_diff.json":
        "3c88a2173854774f9d8bba242ce84d83d4984c66eb4f34f5ec7b26cfbfc37a17",
}

# v1.2 family MUST remain byte-for-byte frozen (CONSUMED/RESULT; RETRY FORBIDDEN).
V1_2_PRESERVED = {
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
    "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_2.py":
        "6a0f1ab604611cb1d5338e919a46929804cca521d5f64a8b6f18e7f24db87a25",
    "reports/audits/phase36_final_probability_authority_diagnostic_contract_v1_2.json":
        "2410f96a6547c3af5826a83ad1b728e9e7d676630d23b0d2f5b82d25370056a1",
    "reports/audits/phase36_final_probability_authority_diagnostic_source_freeze_v1_2.json":
        "b0ff5c4e5df4f8193e4e0b64af160cccdab9a8901e3cefcf5ad33137fed5375f",
    "reports/audits/phase36_final_probability_authority_diagnostic_preflight_v1_2.json":
        "cedef4a4b478aa8e5632953849cff8b420e4a38bc8ec1ce19b9b2ecbd647f3a7",
    "reports/audits/phase36_final_probability_authority_diagnostic_negative_controls_v1_2.json":
        "e1636a6ebcdf9fa48b4765dee6486605162bac773323dbd26e2996afcab8aec1",
    "reports/audits/phase36_final_probability_authority_diagnostic_eligibility_v1_2.json":
        "d18cfa6fd4a0747cec1d6262694731690dcaf5ceb5eae939804e46b298aefa7e",
    "reports/audits/phase36_final_probability_authority_diagnostic_no_execution_audit_v1_2.json":
        "dd89f3c1408613c243bfbe86088c9dc1f66042305c1d2819de24d01da063c474",
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_1_to_v1_2_diff.json":
        "691e06693cae678de9fda96b770643206d780a63bfa231cbc4a7624fb2150064",
    "reports/audits/phase36_final_probability_authority_diagnostic_start_v1_2.json":
        "88723028df230a8b1e2c98c8c248d2de44e73bcb95669efd9bd8d44cff4a69be",
    "reports/audits/phase36_final_probability_authority_diagnostic_result_v1_2.json":
        "4a3753867e72f7cfbc357511475623bd0ecfff2dc0e3aca0f16ecbe1effa98d5",
    "reports/audits/phase36_final_probability_authority_diagnostic_stdout_first_attempt_v1_2.txt":
        "5444cab5d19fcba310b4af06f5c91eeb969ede872e05069f75d672cb5b8afd72",
    "reports/audits/phase36_final_probability_authority_diagnostic_stderr_first_attempt_v1_2.txt":
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_v1_0.json":
        "562e238c5a1ce0581ed1eb1f763f0172826af0653753cfef6346528c1206ec1b",
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_reconciliation_v1_1.json":
        "a85aaf4a0668effaecb148c3ada7a8f25c1bcd0216740e0c009df2115a3833bb",
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_reconciliation_v1_1_d63_addendum_v1_0.json":
        "7e073a03d2a7659e143873816f41ab62e762796033b0877612d19b2c0fb87103",
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_reconciliation_v1_1_d63_runtime_equivalence_addendum_v1_1.json":
        "1c3bd5a591f4cbf2c9e3eb45038dc80730757cc1a5beba64508b8a16ab621355",
}

# v1.3 family MUST remain byte-for-byte frozen (CONSUMED_TERMINAL_EVIDENCE_ANOMALY;
# RETRY FORBIDDEN; D67/D68 preserved).
V1_3_PRESERVED = {
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
    "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_3.py":
        "058371ecf367348dcb1bb9ed11e683d1c0c564da90b4aab47d976ac8ba4416fa",
    "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_3_governance_reconciliation_v1_0.py":
        "82eb91d560a078868d6acd21a2a55c2c7f8a4757799c1237996ce14b74bf9ca5",
    "reports/audits/phase36_final_probability_authority_diagnostic_contract_v1_3.json":
        "8023962b59e6ffdeab75823315fa195025dac163777e24bff335038c3e138518",
    "reports/audits/phase36_final_probability_authority_diagnostic_source_freeze_v1_3.json":
        "73bf1f6e881c5df31c48ba13b6633b7c4d7b1c9a8cf86da9ada21e823a937584",
    "reports/audits/phase36_final_probability_authority_diagnostic_preflight_v1_3.json":
        "a192b1af5891d962e9ecde23b1265a6c7fbc4c03732634cd390dcac1e368fa6a",
    "reports/audits/phase36_final_probability_authority_diagnostic_negative_controls_v1_3.json":
        "a00b6c7abdc29460a33a442b3666a14e677df464c6e21bc336a5433fc7da7e98",
    "reports/audits/phase36_final_probability_authority_diagnostic_eligibility_v1_3.json":
        "30c666cfea5fb414aec5e8c003d431c9874477e1dfb83c574fa0a3ccb2e70618",
    "reports/audits/phase36_final_probability_authority_diagnostic_no_execution_audit_v1_3.json":
        "81c185dc9624c1bb27fef3d9372f5dae603ee9edc54f5541b49c322985442305",
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_2_to_v1_3_diff.json":
        "97d142d41add34ac2e1c5021abf032d3a537cac7ed97f34a86c7a77ffd0ff762",
    # v1.3 CONSUMED evidence (immutable): START present; RESULT/FAILURE ABSENT.
    "reports/audits/phase36_final_probability_authority_diagnostic_start_v1_3.json":
        "b984d09bf3a266de8d75b39b6ad2ff3236cce09915a7f2a5c874813af8c3c1c5",
    # D67 adjudication + D68 reconciliation + D66 governance reconciliation.
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_v1_0.json":
        "3d3f943c19d5b419fb00bcf19748c0dd41ff8002ef26a4a3c51ad32ef6afecd5",
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_reconciliation_v1_1.json":
        "f6bbe602c5928e39d160629688cf697a73f65941a5d24d13c5ad4008a8dc0fc2",
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_3_governance_reconciliation_v1_0.json":
        "b0c01e40c4764514a01a9f082483a071634a0630d6c4c4640e1bb4ac2f829303",
}

# Prior-failure provenance (v1.14 science + clean-equivalence chain; immutable).
PRIOR_FAILURE_PROVENANCE = {
    "v1_14_science_start":
        ("reports/audits/phase36_robustness_science_start_v1_14.json",
         "e2c42b05f4fd0450022d7bcde091c0bea13638788b4f83a123016ab894630e0a"),
    "v1_14_science_failure":
        ("reports/audits/phase36_robustness_science_failure_v1_14.json",
         "0fcc3c211d7bcd53b4f8e53d7b09f518fd83a929e8a979c7174762958fff754b"),
    "v1_14_forensic_adjudication":
        ("reports/audits/phase36_v1_14_science_failure_forensic_adjudication.json",
         "f1d4712ae7b3f0b333a22c852f99d6b3812218ffb258f8f58ddba62c7193c17e"),
    "forensic_reconciliation_v2":
        ("reports/audits/phase36_v1_14_science_failure_forensic_reconciliation_v2.json",
         "cc9a3b502f59e3855c395b9d6afa2f5616f513d60af4756e4477a9370889cc3c"),
    "targeted_static_audit":
        ("reports/audits/phase36_clean_equivalence_targeted_static_audit_v1_0.json",
         "8def086c44a7e80461c729f41ab61c0be347ef1589c94d6884a082adbde64ed4"),
}
REQUIRED_STATIC_AUDIT_VERDICT = "STATIC_ROOT_CAUSE_NOT_ESTABLISHED"

# v1.2 clean-equivalence CONSUMED evidence (immutable).
CONSUMED_EVIDENCE = {
    "v1_2_clean_eq_start_marker":
        ("reports/audits/phase36_clean_equivalence_diagnostic_start_v1_2.json",
         "be93d494b1aa2aad3c900f442c16efe55bcbf0bd508a72df8f8b83e72cd7d2d3"),
    "v1_2_clean_eq_result":
        ("reports/audits/phase36_clean_equivalence_diagnostic_result_v1_2.json",
         "b64f7e6282f9abb864a5d5bc438a22e1096aaf56e0a4e94fe53ba7c9bab6fa4a"),
    "d51_adjudication_v1_0":
        ("reports/audits/phase36_clean_equivalence_d51_numerical_authority_adjudication_v1_0.json",
         "27ac7ada4ee39190d8823b8b1ff7e6e2beb304e2e7fc5778542883ac7eacc53a"),
    "d51_reconciliation_v1_1":
        ("reports/audits/phase36_clean_equivalence_d51_reconciliation_v1_1.json",
         "d8e3e83e6c31004e610faef9d93c221c026eb8974c033f47fbff91106836758b"),
}

# v1.1 CONSUMED evidence (immutable) + the D56 failure adjudication.
V1_1_CONSUMED_EVIDENCE = {
    "v1_1_start_marker":
        ("reports/audits/phase36_final_probability_authority_diagnostic_start_v1_1.json",
         "0bfb452ef81e6e0c8880d9b333abcb6514dff7dbb3a37476da3242beeab73aec"),
    "v1_1_failure_marker":
        ("reports/audits/phase36_final_probability_authority_diagnostic_failure_v1_1.json",
         "9f1b38431228ec584150da37501199ea580b26339be6d8e20a2fcba72b5cd960"),
    "d56_failure_adjudication_v1_0":
        ("reports/audits/phase36_final_probability_authority_diagnostic_v1_1_failure_adjudication_v1_0.json",
         "b796cc8d49df32513d2c6a4c5700a253d66a49e171def1772e1617ff4855fc80"),
}

# v1.2 final-probability AUTHORITY (RESULT) evidence the v1.4 launcher binds.
V1_2_FINAL_PROB_EVIDENCE = {
    "v1_2_final_prob_start":
        ("reports/audits/phase36_final_probability_authority_diagnostic_start_v1_2.json",
         "88723028df230a8b1e2c98c8c248d2de44e73bcb95669efd9bd8d44cff4a69be"),
    "v1_2_final_prob_result":
        ("reports/audits/phase36_final_probability_authority_diagnostic_result_v1_2.json",
         "4a3753867e72f7cfbc357511475623bd0ecfff2dc0e3aca0f16ecbe1effa98d5"),
    "v1_2_result_adjudication_v1_0":
        ("reports/audits/phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_v1_0.json",
         "562e238c5a1ce0581ed1eb1f763f0172826af0653753cfef6346528c1206ec1b"),
    "v1_2_result_adjudication_reconciliation_v1_1":
        ("reports/audits/phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_reconciliation_v1_1.json",
         "a85aaf4a0668effaecb148c3ada7a8f25c1bcd0216740e0c009df2115a3833bb"),
}

# v1.3 CONSUMED (TERMINAL_EVIDENCE_ANOMALY) evidence the v1.4 launcher/diagnostic bind.
V1_3_CONSUMED_EVIDENCE = {
    "v1_3_start":
        ("reports/audits/phase36_final_probability_authority_diagnostic_start_v1_3.json",
         "b984d09bf3a266de8d75b39b6ad2ff3236cce09915a7f2a5c874813af8c3c1c5"),
    "d67_terminal_anomaly_adjudication_v1_0":
        ("reports/audits/phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_v1_0.json",
         "3d3f943c19d5b419fb00bcf19748c0dd41ff8002ef26a4a3c51ad32ef6afecd5"),
    "d68_terminal_anomaly_reconciliation_v1_1":
        ("reports/audits/phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_reconciliation_v1_1.json",
         "f6bbe602c5928e39d160629688cf697a73f65941a5d24d13c5ad4008a8dc0fc2"),
    "d66_governance_reconciliation_v1_0":
        ("reports/audits/phase36_final_probability_authority_diagnostic_v1_3_governance_reconciliation_v1_0.json",
         "b0c01e40c4764514a01a9f082483a071634a0630d6c4c4640e1bb4ac2f829303"),
}

PHASE27_FINAL_PROB_AUTHORITY = {
    "path": "data_cache/phase27_barr_preservation_v1_0/phase27_val808_final_prob_f16.npy",
    "sha256": "506ab6c4e715a9106889e186c146b73903493c80a63258007954cf5deb3ea9cf",
    "shape": [808, 512, 512], "dtype": "float16",
}
PHASE27_SAMPLE_ORDER_AUTHORITY = {
    "val_manifest": "manifests/phase4_v3/val.csv",
    "val_manifest_sha256": "082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315",
    "phase27_scores_csv": PHASE27_SCORES_CSV,
    "phase27_scores_csv_sha256": CANONICAL_PHASE27_SCORES_SHA,
    "phase27_scores_csv_sha256_derived_by_hashing": True,
    "canonical_order": "dataset asc, sample_id asc (808 rows)",
    "binding": "(authority[i] >= 0.5).sum(axis=(1,2)) == scores_csv.final_fg_pixels[i]",
}

OUT = {
    "contract": AUD / "phase36_final_probability_authority_diagnostic_contract_v1_4.json",
    "source_freeze": AUD / "phase36_final_probability_authority_diagnostic_source_freeze_v1_4.json",
    "preflight": AUD / "phase36_final_probability_authority_diagnostic_preflight_v1_4.json",
    "negative_controls": AUD / "phase36_final_probability_authority_diagnostic_negative_controls_v1_4.json",
    "eligibility": AUD / "phase36_final_probability_authority_diagnostic_eligibility_v1_4.json",
    "no_execution_audit": AUD / "phase36_final_probability_authority_diagnostic_no_execution_audit_v1_4.json",
    "diff": AUD / "phase36_final_probability_authority_diagnostic_v1_3_to_v1_4_diff.json",
}

NEW_MARKERS = [
    AUD / "phase36_final_probability_authority_diagnostic_start_v1_4.json",
    AUD / "phase36_final_probability_authority_diagnostic_result_v1_4.json",
    AUD / "phase36_final_probability_authority_diagnostic_failure_v1_4.json",
]
V1_4_PROCESS_EXIT = AUD / "phase36_final_probability_authority_diagnostic_process_exit_v1_4.json"
V1_4_JOURNAL_DIR = AUD / "phase36_final_probability_authority_diagnostic_v1_4_journal"
V1_0_MARKERS = [
    AUD / "phase36_final_probability_authority_diagnostic_start_v1_0.json",
    AUD / "phase36_final_probability_authority_diagnostic_result_v1_0.json",
    AUD / "phase36_final_probability_authority_diagnostic_failure_v1_0.json",
]

# v1.4 runtime/governance sources that must NOT contain the incorrect historical SHA.
V1_4_FAMILY_FILES = [
    DIAG, LAUNCHER, SUPERVISOR, UNIT, PREFLIGHT, NEGCTRL,
    ROOT / "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_4.py",
]

SELF = ROOT / "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_4.py"


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


def _last_json(stdout: str) -> dict:
    end = stdout.rfind("}")
    depth = 0
    start = -1
    for i in range(end, -1, -1):
        c = stdout[i]
        if c == "}":
            depth += 1
        elif c == "{":
            depth -= 1
            if depth == 0:
                start = i
                break
    try:
        return json.loads(stdout[start:end + 1])
    except Exception:  # noqa: BLE001
        return {}


def run_suite(path: Path) -> dict:
    r = subprocess.run([str(VENV), str(path)], capture_output=True, text=True)
    j = _last_json(r.stdout)
    return {"returncode": r.returncode, "n_checks": j.get("n_checks"),
            "n_pass": j.get("n_pass"), "all_pass": j.get("all_pass")}


def verify_pins() -> dict:
    got = {
        "diagnostic": (sha(DIAG), DIAG_SHA),
        "launcher": (sha(LAUNCHER), LAUNCH_SHA),
        "supervisor": (sha(SUPERVISOR), SUPERVISOR_SHA),
        "unit": (sha(UNIT), UNIT_SHA),
        "preflight": (sha(PREFLIGHT), PREFLIGHT_SHA),
        "negative_controls": (sha(NEGCTRL), NEGCTRL_SHA),
        "v1_14_exec": (sha(V14), V14_SHA),
        "v1_14_manifest": (sha(MANIFEST), MANIFEST_SHA),
    }
    bad = {k: v for k, v in got.items() if v[0] != v[1]}
    return {"ok": not bad, "bad": bad, "observed": {k: v[0] for k, v in got.items()}}


def incorrect_sha_occurrences(root: Path) -> dict:
    """The incorrect historical SHA must be ABSENT from the whole v1.4 family.

    The needle is ASSEMBLED at runtime so this check can never self-match.
    """
    needle = _INCORRECT_HEAD + _INCORRECT_TAIL
    out = {}
    for p in V1_4_FAMILY_FILES:
        if not p.exists():
            out[str(p.relative_to(ROOT))] = {"exists": False, "occurrences": 0}
            continue
        n = p.read_text(encoding="utf-8").count(needle)
        out[str(p.relative_to(ROOT))] = {"exists": True, "occurrences": n}
    return out


def main() -> int:
    # ---- preconditions --------------------------------------------------- #
    for m in NEW_MARKERS:
        if m.exists():
            print(json.dumps({"REFUSED": "NEW_FAMILY_MARKER_PRESENT", "path": str(m)}, indent=1))
            return 2
    if V1_4_PROCESS_EXIT.exists():
        print(json.dumps({"REFUSED": "NEW_FAMILY_PROCESS_EXIT_PRESENT",
                          "path": str(V1_4_PROCESS_EXIT)}, indent=1))
        return 2
    if V1_4_JOURNAL_DIR.exists() and any(V1_4_JOURNAL_DIR.iterdir()):
        print(json.dumps({"REFUSED": "NEW_FAMILY_JOURNAL_NOT_EMPTY",
                          "path": str(V1_4_JOURNAL_DIR)}, indent=1))
        return 2
    for m in V1_0_MARKERS:
        if m.exists():
            print(json.dumps({"REFUSED": "V1_0_MARKER_PRESENT_UNEXPECTED", "path": str(m)}, indent=1))
            return 2
    for name, p in OUT.items():
        if p.exists():
            print(json.dumps({"REFUSED": "GOVERNANCE_JSON_ALREADY_EXISTS", "which": name,
                              "path": str(p)}, indent=1))
            return 2

    pins = verify_pins()
    if not pins["ok"]:
        print(json.dumps({"REFUSED": "PIN_MISMATCH", "bad": pins["bad"]}, indent=1))
        return 3

    for label, table in (("V1_0", V1_0_PRESERVED), ("V1_1", V1_1_PRESERVED),
                         ("V1_2", V1_2_PRESERVED), ("V1_3", V1_3_PRESERVED)):
        bad = {p: sha(ROOT / p) for p, e in table.items() if sha(ROOT / p) != e}
        if bad:
            print(json.dumps({"REFUSED": f"{label}_PRESERVED_MISMATCH", "bad": bad}, indent=1))
            return 3

    # ---- D55/D57/D66/D59 remediation (STRUCTURAL) ------------------------ #
    # (a) canonical Phase27 scores SHA is DERIVED by hashing the authority file.
    csv_actual = sha(ROOT / PHASE27_SCORES_CSV)
    if CANONICAL_PHASE27_SCORES_SHA != csv_actual:
        print(json.dumps({"REFUSED": "DERIVED_PHASE27_SCORES_SHA_MISMATCH",
                          "derived": CANONICAL_PHASE27_SCORES_SHA, "actual": csv_actual}, indent=1))
        return 3
    # (b) the incorrect historical literal must appear NOWHERE in the v1.4 family.
    occ = incorrect_sha_occurrences(ROOT)
    offenders = {k: v for k, v in occ.items() if v.get("occurrences", 0) > 0}
    if offenders:
        print(json.dumps({"REFUSED": "INCORRECT_D55_SHA_PRESENT_IN_V1_4_FAMILY",
                          "offenders": offenders}, indent=1))
        return 3
    incorrect_sha_absent_from_v1_4 = not offenders

    # ---- run non-consuming suites ---------------------------------------- #
    unit_run = run_suite(UNIT)
    preflight_run = run_suite(PREFLIGHT)
    nc_run = run_suite(NEGCTRL)
    vo = subprocess.run([str(VENV), str(LAUNCHER), "--verify-only"], capture_output=True, text=True)
    vj = _last_json(vo.stdout)
    sup = subprocess.run([str(VENV), str(SUPERVISOR), "--self-test"], capture_output=True, text=True)
    sup_j = _last_json(sup.stdout)
    sup_all_pass = bool(sup_j.get("all_pass"))
    sup_scen = sup_j.get("synthetic_fixtures")
    if isinstance(sup_scen, dict):
        n_synthetic_scenarios = len(sup_scen)
        synthetic_scenarios_all_pass = all(bool(v.get("pass")) for v in sup_scen.values()
                                           if isinstance(v, dict))
    else:
        n_synthetic_scenarios = None
        synthetic_scenarios_all_pass = False

    for m in NEW_MARKERS:
        if m.exists():
            print(json.dumps({"REFUSED": "MARKER_CREATED_DURING_BUILD", "path": str(m)}, indent=1))
            return 4
    if V1_4_PROCESS_EXIT.exists():
        print(json.dumps({"REFUSED": "PROCESS_EXIT_CREATED_DURING_BUILD",
                          "path": str(V1_4_PROCESS_EXIT)}, indent=1))
        return 4

    if not (unit_run.get("all_pass") and preflight_run.get("all_pass") and nc_run.get("all_pass")):
        print(json.dumps({"REFUSED": "SUITE_NOT_ALL_PASS", "unit": unit_run,
                          "preflight": preflight_run, "negative_controls": nc_run}, indent=1))
        return 5
    if not (vo.returncode == 0 and str(vj.get("terminal", "")).endswith(
            "DISPATCH_SUPPRESSED_BY_VERIFY_ONLY")):
        print(json.dumps({"REFUSED": "LAUNCHER_VERIFY_ONLY_NOT_READY",
                          "returncode": vo.returncode, "terminal": vj.get("terminal")}, indent=1))
        return 5
    if not sup_all_pass:
        print(json.dumps({"REFUSED": "SUPERVISOR_SELF_TEST_NOT_ALL_PASS",
                          "supervisor": sup_j}, indent=1))
        return 5

    # ---- D59 remediation: NON-TAUTOLOGICAL post-validator source-drift check --- #
    # The v1.2 reconciliation's drift check was tautological (it compared constants to
    # themselves).  Here we RE-READ every v1.4 runtime source from disk AFTER the
    # validators ran and require byte-identity with the frozen expectations.  This can
    # genuinely fail if any validator mutated a source file.
    post_pins = {
        "diagnostic": (sha(DIAG), DIAG_SHA),
        "launcher": (sha(LAUNCHER), LAUNCH_SHA),
        "supervisor": (sha(SUPERVISOR), SUPERVISOR_SHA),
        "unit": (sha(UNIT), UNIT_SHA),
        "preflight": (sha(PREFLIGHT), PREFLIGHT_SHA),
        "negative_controls": (sha(NEGCTRL), NEGCTRL_SHA),
    }
    post_drift = {k: {"observed": v[0], "expected": v[1]}
                  for k, v in post_pins.items() if v[0] != v[1]}
    if post_drift:
        print(json.dumps({"REFUSED": "POST_VALIDATOR_SOURCE_DRIFT_DETECTED",
                          "drift": post_drift}, indent=1))
        return 6
    post_validator_source_drift_absent = not post_drift

    ts = now()

    # ---- 1. contract ----------------------------------------------------- #
    write_once(OUT["contract"], {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_CONTRACT",
        "revision": REVISION,
        "supersedes": None,
        "additive_new_family": True,
        "amends_family": "ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_3",
        "v1_0_state": "FROZEN_NEVER_CONSUMED_NOT_AUTHORIZED",
        "v1_0_must_remain_byte_frozen": True,
        "v1_1_state": "CONSUMED_FAILED",
        "v1_1_retry_permitted": False,
        "v1_1_must_remain_byte_frozen": True,
        "v1_2_state": "CONSUMED_RESULT",
        "v1_2_retry_permitted": False,
        "v1_2_must_remain_byte_frozen": True,
        "v1_3_state": "CONSUMED_TERMINAL_EVIDENCE_ANOMALY",
        "v1_3_retry_permitted": False,
        "v1_3_must_remain_byte_frozen": True,
        "purpose": ("GT-FREE determination, with CRASH-SURVIVABLE durable evidence, of whether "
                    "replacing the v1.14 ACCEPT fusion implementation with the canonical Phase27 "
                    "``fuse_full_field`` semantics reproduces the frozen Phase27 "
                    "``phase27_val808_final_prob_f16.npy`` authority bit-identically.  "
                    "SCIENTIFIC PATH IDENTICAL TO v1.3; ONLY observability is added."),
        "scientific_path_changed_from_v1_3": False,
        "scientific_path_unchanged_from_v1_3": True,
        "observability_added_only": True,
        "repairs_exactly_one_defect": {
            "D61": {
                "classification": "ACCEPT_FINAL_FUSION_SEMANTICS_DIVERGE_FROM_PHASE27",
                "established_by": [
                    "reports/audits/phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_v1_0.json",
                    "reports/audits/phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_reconciliation_v1_1.json",
                ],
                "old_v1_14_accept_call": "system._fuse_global_with_regional(p_global, refined, window)",
                "old_semantics": ("PAD-UNAWARE: resize refined256 -> clipped window "
                                  "(y1-y0, x1-x0) via torch.nn.functional.interpolate("
                                  "mode='bilinear', align_corners=False); NO pad offset."),
                "canonical_phase27_accept_call": "fuse_full_field(p_global, refined, geom)",
                "canonical_semantics": ("PAD-AWARE: resize refined256 -> geom['crop_side_pixels'] "
                                        "via PIL BILINEAR, then slice at pad_top/pad_left."),
                "repair": ("The (diagnostic-local) repaired canonical core's ACCEPT branch calls "
                           "_FROZEN_MOD.fuse_full_field(p_global, refined, geom) with the SAME "
                           "``geom`` object produced by the canonical ROI path.  No approximation, "
                           "no alternate resize implementation, no torch interpolation."),
            },
        },
        "observability_additions": {
            "D69": "scientific-path identity proof (AST vs v1.3 core; derived, not hard-coded)",
            "D70": "journal non-interference proof (identical outputs with journal on/off)",
            "stage_journal": ("crash-survivable write-once per-stage-event records under "
                              "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_journal/"),
            "progress_journal": ("GT-free progress checkpoints at rows "
                                 "1,25,50,100,200,300,400,500,600,700,808"),
            "process_exit_evidence": ("durable supervisor process/exit artifact "
                                      "reports/audits/phase36_final_probability_authority_diagnostic_process_exit_v1_4.json"),
            "abrupt_termination_fixtures": ("6 synthetic subprocess scenarios in temporary "
                                            "directories ONLY"),
        },
        "retained_repairs_from_v1_1": {
            "D52": "FINAL_AUTHORITY_NOT_BOUND_PRECONSUMPTION (bound before token/dispatch).",
            "D53": "GT_GUARD_COUNTER_NOT_PROPAGATED_TO_FAILURE_ARTIFACT.",
            "D54": "POSTCOMPUTATION_RESULT_WRITE_FAILURE_LOSES_COMPUTED_EVIDENCE.",
            "FINITE": "Non-finite final probability FAILS CLOSED before f32->f16 conversion.",
            "GT_WORDING": "content-only invariant (no mask FILE opened/dereferenced).",
            "D50": "FOREIGN_V1_14_LAUNCH_AUTHORITY_TOKEN_COUPLING (foreign token forbidden).",
            "D56": "DIAGNOSTIC_FROZEN_MODULE_SUBSCRIPT_MISMATCH (attribute access only).",
            "D55": "GOVERNANCE_BUILDER_PHASE27_SCORE_SHA_TRANSCRIPTION_ERROR (SHA DERIVED).",
            "D57": "v1.2 governance re-introduction of the same transcription error.",
            "D66": "v1.3 governance re-introduction of the same transcription error.",
            "D59": "v1.2 reconciliation tautological post-validation drift check.",
        },
        "d55_d57_d66_d59_remediation": {
            "canonical_phase27_scores_sha256": CANONICAL_PHASE27_SCORES_SHA,
            "canonical_sha_derived_by_hashing": True,
            "canonical_sha_source": PHASE27_SCORES_CSV,
            "incorrect_historical_sha_assembled_from_parts": True,
            "incorrect_historical_sha_absent_from_v1_4_family": incorrect_sha_absent_from_v1_4,
            "remediation_method": ("the canonical value is DERIVED by hashing the authority file "
                                   "at build time; the incorrect literal cannot appear verbatim "
                                   "because it is assembled from parts only for the absence check."),
            "d59_remediation_post_validator_drift_check": ("NON-TAUTOLOGICAL: every v1.4 runtime "
                                                           "source is re-hashed from disk AFTER the "
                                                           "validators run and must be byte-identical"),
            "post_validator_source_drift_absent": post_validator_source_drift_absent,
        },
        "scientific_path_changed": "ONLY_D61_ACCEPT_FINAL_FUSION",
        "scientific_path_unchanged_components": [
            "G", "router", "router_normalization", "router_threshold",
            "ROI_proposal", "ROI_geometry", "rf202",
            "R_psi", "R_psi_checkpoint", "R_psi_input_preprocessing",
            "S_omega", "S_omega_normalization", "S_omega_threshold",
            "task_ids", "sample_order", "final_threshold",
            "float32_to_float16_authority_comparison", "GT_handling", "metrics",
        ],
        "one_shot_gate_env": f"{ONE_SHOT_ENV}=1",
        "launch_authority_token_env": LAUNCH_AUTHORITY_TOKEN,
        "forbidden_foreign_token_env": FOREIGN_TOKEN,
        "forbidden_v1_1_token_reuse": "PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY",
        "forbidden_v1_2_token_reuse": "PHASE36_FINAL_PROB_AUTHORITY_V1_2_LAUNCH_AUTHORITY",
        "forbidden_v1_3_token_reuse": "PHASE36_FINAL_PROB_AUTHORITY_V1_3_LAUNCH_AUTHORITY",
        "d50_foreign_gate_call_omitted": True,
        "d50_reason": "FROZEN_V1_14_GATE_CONTAINS_FOREIGN_LAUNCH_AUTHORITY_SEMANTICS",
        "required_authorization_order": [
            "parse_args",
            "immutable_anchors(diagnostic_source+frozen_v1_14_exec+manifest)",
            "exact_project_interpreter_identity",
            "cuda_readiness",
            "foreign_v1_14_token_absent(fail_closed_if_present)",
            "prior_failure_provenance_binding",
            "consumed_evidence_binding(v1_2_clean_eq_start+result+d51_adjudication+reconciliation)",
            "v1_0_source_and_governance_preservation",
            "v1_1_source_and_governance_preservation",
            "preconsumption_transitive_integrity(14_deps/4_ckpts+exact_source_manifest_equality)",
            "D52_final_authority_preconsumption(exists+sha+header_shape+header_dtype+sample_order)",
            "v1_1_consumed_state_binding",
            "v1_2_consumed_state_binding",
            "D56_module_interface_control(no_subscript+attribute_access)",
            "v1_3_consumed_state_binding(v1_3_start_sha+d67_adjudication+d68_reconciliation+d66)",
            "verify_only_stop(non_consuming)",
            "set_diagnostic_v1_4_launch_authority_token",
            "dispatch_diagnostic_module_only",
        ],
        "execution_scope": "CLEAN_ONLY__NO_GT__NO_DICE__NO_PERTURBATION",
        "diagnostic_steps": [
            "source/provenance/transitive-integrity gates",
            "load exact frozen components",
            "generate canonical clean G (ORIGINAL LIVE FLOAT32 downstream; NO quantization)",
            "retain Phase27 GLOBAL f16 reproduction gate",
            "for each of 808 clean samples: D61-repaired canonical downstream, STOP at out['final_probability']",
            "D56: frozen module accessed by ATTRIBUTE (not subscript)",
            "D61: ACCEPT branch calls _FROZEN_MOD.fuse_full_field(p_global, refined, geom)",
            "FINITE GATE: np.isfinite(final_probability).all() else FAIL CLOSED",
            "generated_final_f16 = asarray(final_probability, float32).astype(float16)",
            "compare against phase27_val808_final_prob_f16.npy row",
            "persist complete diagnostic evidence",
            "STOP (no perturbations)",
        ],
        "imports_frozen_callables_from": "scripts/analysis/phase36_robustness_execution_v1_14.py",
        "frozen_v1_14_exec_source_sha256": V14_SHA,
        "frozen_v1_14_runtime_manifest_sha256": MANIFEST_SHA,
        "phase27_final_prob_authority": PHASE27_FINAL_PROB_AUTHORITY,
        "phase27_sample_order_authority": PHASE27_SAMPLE_ORDER_AUTHORITY,
        "artifacts_written": [
            "reports/audits/phase36_final_probability_authority_diagnostic_start_v1_4.json",
            "reports/audits/phase36_final_probability_authority_diagnostic_result_v1_4.json",
            "reports/audits/phase36_final_probability_authority_diagnostic_failure_v1_4.json",
            "reports/audits/phase36_final_probability_authority_diagnostic_process_exit_v1_4.json",
            "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_journal/",
        ],
        "artifacts_never_written": [
            "any v1.14 science/smoke marker",
            "any v1.3/v1.2/v1.1 clean-equivalence marker (DIFFERENT family)",
            "any perturbation / robustness artifact",
            "any v1.0/v1.1/v1.2/v1.3 final-probability-authority marker",
        ],
        "launcher_output_required_fields": [
            "final_authority_preconsumption_pass", "final_authority_sha256",
            "final_authority_shape", "final_authority_dtype",
            "final_authority_sample_order_pass",
            "v1_3_consumed_state_binding_pass", "v1_3_result_absent", "v1_3_failure_absent",
            "v1_1_consumed_state_binding_pass", "v1_1_result_absent",
            "v1_2_consumed_state_binding_pass", "v1_2_result_present",
            "d56_classification_bound", "d56_module_interface_pass", "d56_subscript_free",
            "d61_has_fuse_full_field_call", "d61_absent_model_fusion_call",
        ],
        "failure_artifact_required_fields": [
            "artifact_kind", "revision", "automatic_retry", "overwrite_permitted",
            "termination_kind", "terminal_classification", "exception", "exception_type",
            "exception_message", "failing_stage", "marker_consumed",
            "final_authority_computed", "final_authority_comparison", "classification",
            "VAL_GT_READ", "blocked_gt_calls", "runtime_state",
            "nonfinite_samples", "nonfinite_final_probability",
            "result_write_attempted", "result_write_completed",
            "partial_result_present", "partial_result_size", "partial_result_sha256",
            "journal_last_durable_stage", "journal_last_complete_stage",
            "journal_first_started_not_completed_stage", "journal_records_written",
            "journal_dir",
            "d50_foreign_gate_call_omitted", "d50_reason",
            "foreign_v1_14_launch_token_present", "gt_content_invariant",
            "d61_repair_classification", "scientific_output", "robustness_result",
            "perturbation_executed", "generated_utc", "write_semantics",
        ],
        "consumed_evidence_binding_required": {
            "v1_2_clean_eq_start_artifact_kind": "PHASE36_CLEAN_EQ_DIAGNOSTIC_START",
            "v1_2_clean_eq_result_artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_RESULT",
            "v1_2_clean_eq_all_pass": False,
            "v1_2_clean_eq_dice_mismatches_n": 390,
            "v1_2_clean_eq_max_abs_dice_deviation": 0.3810357118803769,
            "d51_adjudication_verdict": "D51_ROOT_CAUSE_ESTABLISHED__BOTH_BOUNDARIES",
            "d51_reconciliation_verdict":
                "D51_ROOT_CAUSE_PARTIALLY_ESTABLISHED__FINAL_SCORE_BOUNDARY_CONFIRMED__G_HANDOFF_CAUSALITY_UNPROVEN",
            "d51_g_repair_status": "WITHDRAWN",
        },
        "v1_3_consumed_evidence_binding_required": {
            "v1_3_start_sha256": V1_3_CONSUMED_EVIDENCE["v1_3_start"][1],
            "v1_3_result_absent": True,
            "v1_3_failure_absent": True,
            "d67_classification": "POST_START_TERMINAL_EVIDENCE_ANOMALY",
            "d67_attempt_state": "CONSUMED_TERMINAL_EVIDENCE_ANOMALY",
            "d67_root_cause": "UNRESOLVED",
            "d67_termination_mechanism": "UNRESOLVED",
            "d68_classification": "D67_TERMINAL_WRITE_REACH_OVERCLAIM",
            "d68_status": "RECONCILED",
            "d67_adjudication_sha256": V1_3_CONSUMED_EVIDENCE["d67_terminal_anomaly_adjudication_v1_0"][1],
            "d68_reconciliation_sha256":
                V1_3_CONSUMED_EVIDENCE["d68_terminal_anomaly_reconciliation_v1_1"][1],
            "d66_governance_reconciliation_sha256":
                V1_3_CONSUMED_EVIDENCE["d66_governance_reconciliation_v1_0"][1],
        },
        "v1_1_consumed_evidence_binding_required": {
            "v1_1_start_sha256": V1_1_CONSUMED_EVIDENCE["v1_1_start_marker"][1],
            "v1_1_failure_sha256": V1_1_CONSUMED_EVIDENCE["v1_1_failure_marker"][1],
            "v1_1_result_absent": True,
            "d56_classification": "DIAGNOSTIC_FROZEN_MODULE_SUBSCRIPT_MISMATCH",
        },
        "v1_2_consumed_evidence_binding_required": {
            "v1_2_final_prob_start_sha256": V1_2_FINAL_PROB_EVIDENCE["v1_2_final_prob_start"][1],
            "v1_2_final_prob_result_sha256": V1_2_FINAL_PROB_EVIDENCE["v1_2_final_prob_result"][1],
            "v1_2_final_prob_result_present": True,
            "d61_classification": "ACCEPT_FINAL_FUSION_SEMANTICS_DIVERGE_FROM_PHASE27",
            "d61_established": True,
            "d61_repair_proposed_by_this_family": True,
        },
        "d61_repair_contract": {
            "classification": "D61_CANONICAL_ACCEPT_FUSION_REPAIR",
            "canonical_call": "fuse_full_field(p_global, refined, geom)",
            "replaced_call": "system._fuse_global_with_regional(p_global, refined, window)",
            "same_geom_from_canonical_roi_path": True,
            "same_refined_from_canonical_r_psi": True,
            "no_approximation": True,
            "no_alternate_resize": True,
            "no_torch_interpolation": True,
            "repaired_core_is_diagnostic_local": True,
            "frozen_v1_14_modified": False,
            "src_models_barr_ra_medfilm_barr_modified": False,
        },
        "d67_d68_preservation": {
            "D67": "POST_START_TERMINAL_EVIDENCE_ANOMALY",
            "D68": "RECONCILED",
            "v1_3_state": "CONSUMED_TERMINAL_EVIDENCE_ANOMALY",
            "v1_3_retry_permitted": False,
            "root_cause": "UNRESOLVED",
            "termination_mechanism": "UNRESOLVED",
            "reinterpreted": False,
        },
        "gt_prohibition": {
            "static": "no GT callable actually called; no mask FILE opened/dereferenced",
            "runtime": "GT-bearing callables replaced by raising proxies in memory only",
            "result_contract": "VAL_GT_READ == 0",
            "mask_path_metadata_validation_permitted": True,
            "gt_callables_forbidden": ["_load_val_gt", "full_field_gt", "_dice", "_iou", "_hd95"],
        },
        "prior_failure_provenance_required_verdict": REQUIRED_STATIC_AUDIT_VERDICT,
        "prior_failure_provenance_pins": {k: v[1] for k, v in PRIOR_FAILURE_PROVENANCE.items()},
        "prohibitions": [
            "v1_0_retry_forbidden", "v1_0_must_remain_byte_frozen",
            "v1_1_retry_forbidden", "v1_1_must_remain_byte_frozen",
            "v1_2_retry_forbidden", "v1_2_must_remain_byte_frozen",
            "v1_3_retry_forbidden", "v1_3_must_remain_byte_frozen",
            "v1_14_science_retry_forbidden",
            "v1_15_not_created", "phase37_not_started", "test_remains_phase39_only",
            "router_holdout_not_accessed", "no_g_downstream_quantization",
            "no_threshold_change", "no_feature_change", "no_model_weight_change",
            "no_gt_read", "no_v1_1_token_reuse", "no_v1_2_token_reuse", "no_v1_3_token_reuse",
        ],
        "source_sha256": {
            "diagnostic": DIAG_SHA, "launcher": LAUNCH_SHA, "supervisor": SUPERVISOR_SHA,
            "unit": UNIT_SHA, "preflight": PREFLIGHT_SHA, "negative_controls": NEGCTRL_SHA,
        },
        "scientific_output": False,
        "generated_utc": ts,
    })

    # ---- 2. source_freeze ------------------------------------------------ #
    write_once(OUT["source_freeze"], {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_SOURCE_FREEZE",
        "revision": REVISION,
        "diagnostic_source": {"path": str(DIAG.relative_to(ROOT)).replace("\\", "/"),
                              "sha256": DIAG_SHA},
        "launcher_source": {"path": str(LAUNCHER.relative_to(ROOT)).replace("\\", "/"),
                            "sha256": LAUNCH_SHA},
        "supervisor_source": {"path": str(SUPERVISOR.relative_to(ROOT)).replace("\\", "/"),
                              "sha256": SUPERVISOR_SHA},
        "unit_source": {"path": str(UNIT.relative_to(ROOT)).replace("\\", "/"),
                        "sha256": UNIT_SHA},
        "preflight_source": {"path": str(PREFLIGHT.relative_to(ROOT)).replace("\\", "/"),
                             "sha256": PREFLIGHT_SHA},
        "negative_controls_source": {"path": str(NEGCTRL.relative_to(ROOT)).replace("\\", "/"),
                                     "sha256": NEGCTRL_SHA},
        "frozen_ancestors": {
            "v1_14_execution": {"path": "scripts/analysis/phase36_robustness_execution_v1_14.py",
                                "sha256": V14_SHA},
            "v1_14_runtime_manifest": {"path": "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json",
                                       "sha256": MANIFEST_SHA},
        },
        "preserved_v1_0_family": {p: e for p, e in V1_0_PRESERVED.items()},
        "preserved_v1_1_family": {p: e for p, e in V1_1_PRESERVED.items()},
        "preserved_v1_2_family": {p: e for p, e in V1_2_PRESERVED.items()},
        "preserved_v1_3_family": {p: e for p, e in V1_3_PRESERVED.items()},
        "v1_1_consumed_evidence": {k: v[1] for k, v in V1_1_CONSUMED_EVIDENCE.items()},
        "v1_2_final_prob_evidence": {k: v[1] for k, v in V1_2_FINAL_PROB_EVIDENCE.items()},
        "v1_3_consumed_evidence": {k: v[1] for k, v in V1_3_CONSUMED_EVIDENCE.items()},
        "launcher_pinned_frozen_v1_3_launcher_sha":
            V1_3_PRESERVED["scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_3.py"],
        "launcher_pinned_diagnostic_sha": DIAG_SHA,
        "launcher_pinned_v1_14_exec_sha": V14_SHA,
        "launcher_pinned_v1_14_manifest_sha": MANIFEST_SHA,
        "launcher_pinned_phase27_final_authority_sha": PHASE27_FINAL_PROB_AUTHORITY["sha256"],
        "launcher_pin_matches_actual_diagnostic": True,
        "launcher_pin_matches_v1_14_exec": True,
        "launcher_pin_matches_v1_14_manifest": True,
        "non_circularity": ("launcher pins frozen v1.3 launcher SHA (literal) + v1.14 exec + "
                            "manifest; manifest declares v1.14 exec only; no launcher_sha256 in manifest"),
        "canonical_phase27_scores_sha256": CANONICAL_PHASE27_SCORES_SHA,
        "canonical_phase27_scores_sha_derived_by_hashing": True,
        "incorrect_historical_sha_absent_from_v1_4_family": incorrect_sha_absent_from_v1_4,
        "incorrect_sha_occurrences": occ,
        "post_validator_source_drift_absent": post_validator_source_drift_absent,
        "scientific_output": False,
        "generated_utc": ts,
    })

    # ---- 3. preflight ---------------------------------------------------- #
    write_once(OUT["preflight"], {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_PREFLIGHT",
        "revision": REVISION,
        "unit_run": unit_run,
        "preflight_run": preflight_run,
        "negative_controls_run": nc_run,
        "supervisor_self_test": {"all_pass": sup_all_pass,
                                 "n_synthetic_scenarios": n_synthetic_scenarios,
                                 "synthetic_scenarios_all_pass": synthetic_scenarios_all_pass},
        "launcher_verify_only": {
            "terminal": vj.get("terminal"),
            "authorized": vj.get("authorized"),
            "interpreter_pass": vj.get("interpreter_pass"),
            "cuda_readiness_pass": vj.get("cuda_readiness_pass"),
            "foreign_v1_14_token_absent_pass": vj.get("foreign_v1_14_token_absent_pass"),
            "prior_failure_provenance_pass": vj.get("prior_failure_provenance_pass"),
            "consumed_evidence_binding_pass": vj.get("consumed_evidence_binding_pass"),
            "v1_0_preservation_pass": vj.get("v1_0_preservation_pass"),
            "v1_1_preservation_pass": vj.get("v1_1_preservation_pass"),
            "transitive_integrity_pass": vj.get("transitive_integrity_pass"),
            "source_manifest_transitive_authority_exact_match":
                vj.get("source_manifest_transitive_authority_exact_match"),
            "n_dependencies_verified": vj.get("n_dependencies_verified"),
            "n_checkpoints_verified": vj.get("n_checkpoints_verified"),
            "final_authority_preconsumption_pass": vj.get("final_authority_preconsumption_pass"),
            "final_authority_sha256": vj.get("final_authority_sha256"),
            "final_authority_shape": vj.get("final_authority_shape"),
            "final_authority_dtype": vj.get("final_authority_dtype"),
            "final_authority_sample_order_pass": vj.get("final_authority_sample_order_pass"),
            "v1_1_consumed_state_binding_pass": vj.get("v1_1_consumed_state_binding_pass"),
            "v1_1_result_absent": vj.get("v1_1_result_absent"),
            "v1_2_consumed_state_binding_pass": vj.get("v1_2_consumed_state_binding_pass"),
            "v1_2_failure_absent": vj.get("v1_2_failure_absent"),
            "v1_3_consumed_state_binding_pass": vj.get("v1_3_consumed_state_binding_pass"),
            "v1_3_result_absent": vj.get("v1_3_result_absent"),
            "v1_3_failure_absent": vj.get("v1_3_failure_absent"),
            "d56_module_interface_pass": vj.get("d56_module_interface_pass"),
            "d56_subscript_free": vj.get("d56_subscript_free"),
            "d61_has_fuse_full_field_call": vj.get("d61_has_fuse_full_field_call"),
            "d61_absent_model_fusion_call": vj.get("d61_absent_model_fusion_call"),
            "dispatch_suppressed": str(vj.get("terminal", "")).endswith("DISPATCH_SUPPRESSED_BY_VERIFY_ONLY"),
            "one_shot_gate_set_during_verify": vj.get("one_shot_gate_set"),
        },
        "frozen_v1_14_anchors_intact": {"v1_14_exec": V14_SHA, "v1_14_manifest": MANIFEST_SHA},
        "prior_failure_provenance": {k: v[1] for k, v in PRIOR_FAILURE_PROVENANCE.items()},
        "consumed_evidence": {k: v[1] for k, v in CONSUMED_EVIDENCE.items()},
        "v1_1_consumed_evidence": {k: v[1] for k, v in V1_1_CONSUMED_EVIDENCE.items()},
        "v1_2_final_prob_evidence": {k: v[1] for k, v in V1_2_FINAL_PROB_EVIDENCE.items()},
        "v1_3_consumed_evidence": {k: v[1] for k, v in V1_3_CONSUMED_EVIDENCE.items()},
        "static_audit_verdict": REQUIRED_STATIC_AUDIT_VERDICT,
        "static_audit_verdict_matches_required": True,
        "prior_diagnostic_attempt": True,
        "prior_diagnostic_attempt_consumed_failed": True,
        "prior_diagnostic_attempt_retry_permitted": False,
        "v1_2_attempt_consumed_result": True,
        "v1_2_retry_permitted": False,
        "v1_3_attempt_consumed_terminal_evidence_anomaly": True,
        "v1_3_retry_permitted": False,
        "v1_0_markers_absent": True,
        "v1_1_markers_present_consumed": True,
        "v1_1_result_marker_absent": True,
        "v1_2_markers_present_consumed": True,
        "v1_2_result_marker_present": True,
        "v1_3_start_present_consumed": True,
        "v1_3_result_failure_absent": True,
        "new_family_markers_absent": True,
        "v1_4_process_exit_absent": True,
        "v1_4_journal_absent_or_empty": True,
        "gt_static_prohibition_pass": True,
        "d61_repair_static_pass": True,
        "d69_scientific_path_identity_pass": True,
        "d70_journal_non_interference_pass": True,
        "scientific_output": False,
        "generated_utc": ts,
    })

    # ---- 4. negative_controls -------------------------------------------- #
    write_once(OUT["negative_controls"], {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_NEGATIVE_CONTROLS",
        "revision": REVISION,
        "source": {"path": str(NEGCTRL.relative_to(ROOT)).replace("\\", "/"),
                   "sha256": NEGCTRL_SHA},
        "headline_control": {
            "statement": ("inherited foreign v1.14 token => launcher refuses (rc 2) before dispatch; "
                          "diagnostic main() refuses (rc 8); no marker; any GT access fails closed"),
            "exit_code_expected_no_one_shot_gate": 3,
            "exit_code_expected_no_launch_authority": 5,
            "exit_code_expected_foreign_token_present": 8,
            "exit_code_expected_launcher_foreign_token": 2,
        },
        "d61_controls": [
            "v1.4 diagnostic ACCEPT branch calls canonical fuse_full_field",
            "v1.4 diagnostic ACCEPT branch does NOT call _fuse_global_with_regional",
            "v1.4 diagnostic contains NO _fuse_global_with_regional CALL anywhere",
            "MUTATION: swap `fused = mod.fuse_full_field(...)` -> "
            "`fused = system._fuse_global_with_regional(...)` is DETECTED",
            "canonical pad-aware fuse_full_field DIVERGES from the old pad-unaware model fusion",
            "canonical fuse_full_field is deterministic (idempotent replicate)",
        ],
        "d69_controls": [
            "v1.4 core scientific-path identity vs v1.3 core: DERIVED (not hard-coded)",
            "observability-only statements are journal/stage-only",
            "MUTATION: reverting the canonical fusion call FAILS the validator",
        ],
        "d70_controls": [
            "journal disabled vs enabled => np.array_equal identical outputs, max_abs == 0.0",
            "journal records are GT-free (no probabilities/masks/metrics)",
            "journal writes are write-once (O_CREAT|O_EXCL)",
        ],
        "d56_controls": [
            "real types.ModuleType is NOT subscriptable (TypeError reproduced)",
            "real v1.4 diagnostic contains NO _FROZEN_MOD[...] subscript site",
            "_FROZEN_MOD._load_clean_image_tensor present as ATTRIBUTE access",
            "launcher check_d56_module_interface() passes on the real diagnostic",
        ],
        "d52_controls": [
            "FINAL_AUTHORITY_ABSENT", "FINAL_AUTHORITY_SHA_MISMATCH",
            "FINAL_AUTHORITY_SHAPE_MISMATCH", "FINAL_AUTHORITY_DTYPE_MISMATCH",
            "FINAL_AUTHORITY_SAMPLE_ORDER_MISMATCH",
        ],
        "supervisor_controls": [
            "6 synthetic abrupt-termination fixtures (temporary dirs ONLY)",
            "supervisor writes durable process/exit evidence (write-once + fsync)",
            "supervisor NEVER creates/alters scientific START/RESULT/FAILURE",
            "supervisor NEVER relaunches",
        ],
        "run": nc_run,
        "scientific_output": False,
        "generated_utc": ts,
    })

    # ---- 5. eligibility -------------------------------------------------- #
    write_once(OUT["eligibility"], {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_ELIGIBILITY",
        "revision": REVISION,
        "diagnostic_state": "ELIGIBLE_NOT_STARTED",
        "one_shot": True,
        "automatic_retry": False,
        "requires_env": f"{ONE_SHOT_ENV}=1",
        "requires_launch_authority": True,
        "launch_authority_token_env": LAUNCH_AUTHORITY_TOKEN,
        "forbidden_foreign_token_env": FOREIGN_TOKEN,
        "forbidden_v1_1_token_reuse": "PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY",
        "forbidden_v1_2_token_reuse": "PHASE36_FINAL_PROB_AUTHORITY_V1_2_LAUNCH_AUTHORITY",
        "forbidden_v1_3_token_reuse": "PHASE36_FINAL_PROB_AUTHORITY_V1_3_LAUNCH_AUTHORITY",
        "requires_canonical_interpreter": True,
        "requires_cuda": True,
        "requires_final_authority_preconsumption_pass": True,
        "requires_v1_1_consumed_state_binding": True,
        "requires_v1_2_consumed_state_binding": True,
        "requires_v1_3_consumed_state_binding": True,
        "requires_d56_module_interface_pass": True,
        "requires_d61_repair_static_pass": True,
        "requires_d69_scientific_path_identity_pass": True,
        "requires_d70_journal_non_interference_pass": True,
        "prior_attempt_consumed": False,
        "start_marker_present": False,
        "result_marker_present": False,
        "failure_marker_present": False,
        "process_exit_artifact_present": False,
        "journal_records": 0,
        "static_audit_verdict_dependency": REQUIRED_STATIC_AUDIT_VERDICT,
        "static_audit_sha256": "8def086c44a7e80461c729f41ab61c0be347ef1589c94d6884a082adbde64ed4",
        "reconciliation_v2_sha256": "cc9a3b502f59e3855c395b9d6afa2f5616f513d60af4756e4477a9370889cc3c",
        "consumed_evidence_bound": {k: v[1] for k, v in CONSUMED_EVIDENCE.items()},
        "v1_1_consumed_evidence_bound": {k: v[1] for k, v in V1_1_CONSUMED_EVIDENCE.items()},
        "v1_2_final_prob_evidence_bound": {k: v[1] for k, v in V1_2_FINAL_PROB_EVIDENCE.items()},
        "v1_3_consumed_evidence_bound": {k: v[1] for k, v in V1_3_CONSUMED_EVIDENCE.items()},
        "phase27_final_prob_authority": PHASE27_FINAL_PROB_AUTHORITY,
        "phase27_sample_order_authority": PHASE27_SAMPLE_ORDER_AUTHORITY,
        "v1_0_state": "FROZEN_NEVER_CONSUMED_NOT_AUTHORIZED",
        "v1_0_retry_permitted": False,
        "v1_1_state": "CONSUMED_FAILED",
        "v1_1_retry_permitted": False,
        "v1_2_state": "CONSUMED_RESULT",
        "v1_2_retry_permitted": False,
        "v1_3_state": "CONSUMED_TERMINAL_EVIDENCE_ANOMALY",
        "v1_3_retry_permitted": False,
        "v1_14_science_consumed": True,
        "v1_14_science_failed": True,
        "v1_14_science_retry_permitted": False,
        "v1_2_clean_eq_status": "CONSUMED_RESULT",
        "v1_2_clean_eq_retry_permitted": False,
        "d56_status": "REPAIRED",
        "d56_classification": "DIAGNOSTIC_FROZEN_MODULE_SUBSCRIPT_MISMATCH",
        "d61_status": "REPAIR_PROPOSED_BY_THIS_FAMILY",
        "d61_classification": "ACCEPT_FINAL_FUSION_SEMANTICS_DIVERGE_FROM_PHASE27",
        "d67_classification": "POST_START_TERMINAL_EVIDENCE_ANOMALY",
        "d68_status": "RECONCILED",
        "root_cause": "UNRESOLVED",
        "termination_mechanism": "UNRESOLVED",
        "d51_overall_status":
            "D51_ROOT_CAUSE_PARTIALLY_ESTABLISHED__FINAL_SCORE_BOUNDARY_CONFIRMED__G_HANDOFF_CAUSALITY_UNPROVEN",
        "g_quantization_repair": "WITHDRAWN",
        "v1_15_created": False,
        "phase37_not_started": True,
        "test_remains_phase39_only": True,
        "router_holdout_accessed": False,
        "scientific_output": False,
        "generated_utc": ts,
    })

    # ---- 6. no_execution_audit ------------------------------------------- #
    write_once(OUT["no_execution_audit"], {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_NO_EXECUTION_AUDIT",
        "revision": REVISION,
        "model_loaded": False,
        "checkpoint_loaded": False,
        "checkpoint_deserialized_at_launcher": False,
        "val_image_read": False,
        "val_gt_read": False,
        "VAL_GT_READ": 0,
        "cuda_context_created_for_inference": False,
        "perturbation_executed": False,
        "foreign_v1_14_launch_token_used": False,
        "forbidden_gate_called": False,
        "diagnostic_start_marker_written": False,
        "diagnostic_result_written": False,
        "diagnostic_failure_written": False,
        "diagnostic_process_exit_written_by_supervisor": False,
        "diagnostic_journal_records_written": False,
        "v1_0_artifacts_modified": False,
        "v1_0_markers_written": False,
        "v1_1_artifacts_modified": False,
        "v1_1_markers_written": False,
        "v1_2_artifacts_modified": False,
        "v1_2_markers_written": False,
        "v1_3_artifacts_modified": False,
        "v1_3_markers_written": False,
        "v1_3_start_modified": False,
        "v1_3_d67_d68_d66_modified": False,
        "v1_14_science_marker_written": False,
        "v1_14_science_rerun": False,
        "v1_14_source_modified": False,
        "src_models_barr_ra_medfilm_barr_modified": False,
        "v1_15_created": False,
        "phase37_started": False,
        "test_accessed": False,
        "router_holdout_accessed": False,
        "scientific_output": False,
        "generated_utc": ts,
    })

    # ---- 7. diff (v1.3 -> v1.4) ------------------------------------------ #
    write_once(OUT["diff"], {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_V1_3_TO_V1_4_DIFF",
        "revision": REVISION,
        "from_revision": "ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_3",
        "to_revision": REVISION,
        "additive": True,
        "observability_only": True,
        "v1_0_state": "FROZEN_NEVER_CONSUMED_NOT_AUTHORIZED",
        "v1_0_modified": False,
        "v1_1_state": "CONSUMED_FAILED",
        "v1_1_modified": False,
        "v1_2_state": "CONSUMED_RESULT",
        "v1_2_modified": False,
        "v1_3_state": "CONSUMED_TERMINAL_EVIDENCE_ANOMALY",
        "v1_3_modified": False,
        "scientific_path_changed": "NONE_SINCE_V1_3",
        "scientific_path_identical_to_v1_3": True,
        "scientific_path_changed_v1_3_vs_v1_2": "ONLY_D61_ACCEPT_FINAL_FUSION",
        "changes": {
            "SCIENTIFIC_PATH": {
                "v1_3": "single D61 ACCEPT-fusion repair (canonical fuse_full_field)",
                "v1_4": "IDENTICAL_TO_V1_3 (D69 proves the repaired core is byte-identical "
                        "once observability statements are removed)",
            },
            "OBSERVABILITY": {
                "v1_3": "none (terminal-evidence anomaly was not crash-survivable)",
                "v1_4": ("write-once stage journal + GT-free progress checkpoints + durable "
                         "supervisor process/exit evidence + synthetic abrupt-termination fixtures"),
            },
            "AUTHORITY_TOKEN": {
                "v1_3": "PHASE36_FINAL_PROB_AUTHORITY_V1_3_LAUNCH_AUTHORITY",
                "v1_4": "PHASE36_FINAL_PROB_AUTHORITY_V1_4_LAUNCH_AUTHORITY",
            },
            "MARKERS": {
                "v1_3": ["..._start_v1_3.json", "..._result_v1_3.json", "..._failure_v1_3.json"],
                "v1_4": ["..._start_v1_4.json", "..._result_v1_4.json", "..._failure_v1_4.json",
                         "..._process_exit_v1_4.json", "..._v1_4_journal/"],
            },
            "NEW_PRECONSUMPTION_GATE": {
                "v1_3": "v1.2 consumed-state binding",
                "v1_4": ("ADDITIONALLY binds the v1.3 consumed state (v1.3 START sha + D67 "
                         "adjudication + D68 reconciliation + D66) ordered AFTER the v1.2 "
                         "consumed-state gate and BEFORE the verify-only STOP / token set"),
            },
            "GATE_REUSE": {
                "v1_3": "reuses the frozen v1.2 launcher gates verbatim",
                "v1_4": ("reuses the frozen v1.3 launcher gates verbatim (which themselves reuse "
                         "the frozen v1.2 gates), so gate semantics cannot drift"),
            },
        },
        "preserved_unchanged": [
            "frozen v1.14 exec + manifest",
            "v1.2 clean-equivalence consumed evidence",
            "v1.2 final-probability authority consumed evidence",
            "v1.3 CONSUMED_TERMINAL_EVIDENCE_ANOMALY evidence + D67/D68 preservation",
            "prior-failure provenance",
            "one-shot env gate PHASE36_FINAL_PROB_AUTHORITY_EXECUTE",
            "forbidden foreign token PHASE36_V1_14_LAUNCH_AUTHORITY",
            "the D52 final-authority pre-consumption gate",
            "the D53 shared GT runtime-evidence state",
            "the D54 computed-evidence preservation on result-write failure",
            "the D56 module-interface AST control",
            "the finite-probability fail-closed hardening",
            "G / router / ROI / rf202 / R_psi / S_omega / task IDs / sample order / final threshold "
            "(scientific path EXCEPT the single D61 ACCEPT fusion)",
        ],
        "source_sha256": {
            "v1_3_diagnostic": V1_3_PRESERVED["scripts/analysis/phase36_final_probability_authority_diagnostic_v1_3.py"],
            "v1_4_diagnostic": DIAG_SHA,
            "v1_3_launcher": V1_3_PRESERVED["scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_3.py"],
            "v1_4_launcher": LAUNCH_SHA,
            "v1_4_supervisor": SUPERVISOR_SHA,
        },
        "scientific_output": False,
        "generated_utc": ts,
    })

    out_sha = {name: sha(p) for name, p in OUT.items()}
    print(json.dumps({
        "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_GOVERNANCE_BUILT",
        "unit_run": unit_run,
        "preflight_run": preflight_run,
        "negative_controls_run": nc_run,
        "supervisor_self_test": {"all_pass": sup_all_pass,
                                 "n_synthetic_scenarios": n_synthetic_scenarios,
                                 "synthetic_scenarios_all_pass": synthetic_scenarios_all_pass},
        "launcher_verify_only_terminal": vj.get("terminal"),
        "canonical_phase27_scores_sha256": CANONICAL_PHASE27_SCORES_SHA,
        "canonical_sha_derived_by_hashing": True,
        "incorrect_historical_sha_absent_from_v1_4_family": incorrect_sha_absent_from_v1_4,
        "post_validator_source_drift_absent": post_validator_source_drift_absent,
        "governance_sha256": out_sha,
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
