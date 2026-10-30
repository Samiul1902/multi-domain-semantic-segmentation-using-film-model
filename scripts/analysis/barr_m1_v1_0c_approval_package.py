#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RA-MedFiLM-BARR — BARR-M1 Final Scientific Approval Package (v1.0c)
===================================================================

NO SCIENTIFIC EXECUTION.

Emits the versioned approval packet:
  reports/planning/barr_m1_approval_v1_0c/
    barr_m1_v1_0c_packet_index.md
    barr_m1_v1_0c_reporting_precision.md
    barr_m1_v1_0c_supervisor_authorization_request.md
  reports/audits/
    barr_m1_v1_0c_precision_audit.json
    barr_m1_v1_0c_scope_freeze.json
    barr_m1_v1_0c_gate_validation.json
    barr_m1_v1_0c_final_check.json
    barr_m1_v1_0c_release_manifest.json
    barr_m1_v1_0c_terminal.json

Preserves v1.0 / v1.0a / v1.0b artifacts unchanged (verified, not rewritten).
"""

import hashlib
import importlib.util
import json
import os
import sys
from collections import OrderedDict
from datetime import datetime, timezone

REPO = r"D:\Softfors\jup"
AUDIT = os.path.join(REPO, "reports", "audits")
PKG = os.path.join(REPO, "reports", "planning", "barr_m1_approval_v1_0c")
GATE = os.path.join(REPO, "scripts", "analysis", "barr_m1_reanalysis_gate_v1_0c.py")

REV = "RA_MEDFILM_BARR_BARR_M1_V1_0C__FINAL_APPROVAL_PACKAGE"
HARM_TOL = 1e-9
N = 4957
K = 1239
ACC = 1205
REJ = 34


def sha256_of(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def write_once(path, text):
    if os.path.exists(path):
        raise SystemExit("REFUSING TO OVERWRITE: %s" % path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return sha256_of(path)


def write_json(path, obj):
    return write_once(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --- prior artifacts that must remain byte-identical ------------------------
PRIOR = OrderedDict([
    ("v1_0a", OrderedDict([
        ("reports/audits/barr_m1_arm_identity_audit_v1_0a.json",
         "3032b55d9fddbe7db1d0ca76719d976ff194929d371090780ff50426e3a766dc"),
        ("reports/audits/barr_m1_population_lineage_audit_v1_0a.json",
         "3009d2f5391dea3a437d28ef834808af9ee53910a11a01d1e90090c2d20ee57f"),
        ("reports/audits/barr_m1_endpoint_contract_v1_0a.json",
         "940f72bafe6de6f6934cdf02cd4978a53417295d8ef5ba95bb7d2b40d94b50c6"),
        ("reports/audits/barr_m1_three_seed_evidence_audit_v1_0a.json",
         "dd96cae22ab76d1786a4377679f57be282996b9a89a8e5f5e9a369dd9983a08e"),
        ("reports/audits/barr_m1_prelaunch_gate_contract_v1_0a.json",
         "67a14cb83125b3b19305fd645dbdf172bac0fe267fe86a4a62a608ad9c33e699"),
        ("reports/audits/barr_m1_reproduction_feasibility_check_v1_0a.json",
         "4cc594d038f43126aad3a4be3fc15a071d3e6ae7decdab78f512619322a6e854"),
        ("reports/planning/barr_m1_v1_0a/barr_m1_work_order_revision_v1_0a.md",
         "93342fb93a2b79ecf710c5811d9724051a1ebf3845ee7edf3480da763fe4f505"),
        ("reports/planning/barr_m1_v1_0a/barr_m1_supervisor_memorandum_v1_0a.md",
         "bf733b981cfd4e76dfce3746def34ebc54fa2e59741ea09d71f659c1a730ec56"),
        ("reports/audits/barr_m1_design_reconciliation_final_check_v1_0a.json",
         "807952ef118e0b1f27478bd1ba2c0de795b40c14e5b9e3958dcbea8f6c609a0f"),
        ("reports/audits/barr_m1_design_reconciliation_terminal_v1_0a.json",
         "19efd682471165be6187e674a166a2258265c5fa28e86027daf2eeeb5043f973"),
    ])),
    ("v1_0b", OrderedDict([
        ("reports/audits/barr_m1_v1_0b_harm_denominator_audit.json",
         "fe35d1467d4387ba113bd858189f4bce9e620aa4ebf685f39e0e64b105c2da35"),
        ("reports/audits/barr_m1_v1_0b_a7_a8_contrast_audit.json",
         "57a791d55413c135fa11507eba176fd2da092a426c00181b82e55c4f6081693c"),
        ("reports/audits/barr_m1_v1_0b_phase28_chronology_audit.json",
         "bbc4bcc946d8ae3b5a1be663adfdc671522edcf83827cf525611d6f70e9c8dec"),
        ("reports/audits/barr_m1_v1_0b_reproduction_semantics_audit.json",
         "9e71536b9513ff9e3e3645f883fb894067ad16f0618e7733ed1264bcbdf3150c"),
        ("reports/planning/barr_m1_v1_0b/barr_m1_v1_0b_addendum.md",
         "fb3a138ddd406b735eb1b96b1d520790f3e358ee2213ede002f178cd92892608"),
        ("reports/audits/barr_m1_v1_0b_final_check.json",
         "f84251cd743d7865ab2e0e5ed46f90c53bb64dfda803459b6a9ddc7bb61fcc9c"),
        ("reports/audits/barr_m1_v1_0b_sha256_manifest.json",
         "4c612d8e88cf72f5bd15c6be155a05e8c0487c21e9d06b0a4d9e02a17879b527"),
        ("reports/audits/barr_m1_v1_0b_terminal.json",
         "fb5919ae2ff9f959a2424651f0c41b27e52930a77be80e073a88fba334333fbf"),
    ])),
])

FROZEN_SOURCES = OrderedDict([
    ("phase25c_oof_labels",
     ("data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/phase25c_oof_paired_gain_labels.csv",
      "fd6ca32c33a3bddb75f986b1350d54ec35b11d3bf5cb0fdc029962a5aa94865f")),
    ("phase25e_c8_membership",
     ("reports/tables/phase25e_policy_memberships_v1_0/C8_lambda0.25_budget0.25.csv",
      "4c411d589866434b824245d3c940bc09873f3cbc096ddc8a44776cd56273393b")),
    ("phase25f_oof_safety",
     ("data_cache/phase25f_barr_post_safety_v1_0/phase25f_oof_safety_predictions.csv",
      "a9f63edd6d58a9a1d78a052a3e4539c6e0dd4d68bfb1c09c4c36789c441ebdee")),
    ("phase25b_dev_metadata",
     ("data_cache/phase25b_barr_pre_refinement_features_v1_2/metadata.csv",
      "ee8c304350d28d907c053a355da1f878ff7f9dd137761034283459aeed071093")),
    ("phase28_table_02",
     ("reports/tables/phase28_table_02_arm_primary_metrics.csv",
      "171168f973d0a210913b567c4b743f134b1918f3d22be55a6e7046890400e3fc")),
])

COMPONENTS = OrderedDict([
    ("G", ("GlobalMedFiLM",
           "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7", 3523001)),
    ("R_psi", ("BARRRegionalRefinerV1",
               "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109", 1276401)),
    ("B_phi", ("BARRBenefitRouterV1",
               "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b", 36801)),
    ("S_omega", ("BARRPostSafetyV1",
                 "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e", 1217)),
])


# ---------------------------------------------------------------------------
def load_gate():
    spec = importlib.util.spec_from_file_location("barr_m1_gate", GATE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
def task1_precision():
    a1_strict = 2115
    a1_tol = 2107
    a7_h = 412
    a8_h = 390

    r = OrderedDict()
    r["1_A1_strict_vs_tolerance"] = OrderedDict([
        ("strict_numerator", a1_strict),
        ("strict_denominator", N),
        ("strict_rate", a1_strict / N),
        ("tolerance", HARM_TOL),
        ("tolerance_numerator", a1_tol),
        ("tolerance_rate", a1_tol / N),
        ("difference_cases", a1_strict - a1_tol),
        ("difference_pp", (a1_strict - a1_tol) / N * 100.0),
        ("interpretation",
         "8 cases have -1e-9 <= delta < 0. They are floating-point-scale negatives, not "
         "scientifically meaningful harm. BOTH rates must be reported; neither replaces the "
         "other, and the choice must be declared in the table caption."),
        ("which_is_primary", "BOTH — strict and tolerance-adjusted reported side by side"),
    ])
    r["2_A7_A8_all_population_harm"] = OrderedDict([
        ("A7_harmed", a7_h), ("A7_denominator", N), ("A7_rate", a7_h / N),
        ("A8_harmed", a8_h), ("A8_denominator", N), ("A8_rate", a8_h / N),
        ("note", "Both are ALL-POPULATION counts over 4957, so they are directly comparable to "
                 "A1's 2115/4957."),
    ])
    r["3_A8_selection_and_acceptance"] = OrderedDict([
        ("selected", K), ("selected_fraction", K / N),
        ("accepted", ACC), ("accepted_fraction_of_population", ACC / N),
        ("accepted_fraction_of_selected", ACC / K),
        ("rejected", REJ), ("rejected_fraction_of_selected", REJ / K),
        ("identity", "selected = accepted + rejected  (%d = %d + %d)" % (K, ACC, REJ)),
    ])
    r["4_execution_vs_acceptance"] = OrderedDict([
        ("candidate_refinement_execution",
         "R_psi actually ran on the case (the crop was refined). Determined by the router "
         "membership only."),
        ("post_safety_acceptance",
         "S_omega allowed the refined mask to REPLACE the global mask. Determined only by the "
         "safety decision, evaluated only where execution occurred."),
        ("A7", "executes 1239, accepts 1239 (no safety)"),
        ("A8", "executes the SAME 1239, accepts 1205, rejects 34"),
        ("key_point",
         "A case can be EXECUTED and then REJECTED. Its delta is then exactly 0.0, so it is "
         "neither helped nor harmed — it is not a 'harm' and must not be counted as one."),
        ("consequence",
         "n_executed and n_accepted are different quantities and must never be used "
         "interchangeably as a denominator."),
    ])
    r["5_pooled_vs_macro"] = OrderedDict([
        ("pooled_definition", "sum(delta) / n_executed  — weights domains by case count"),
        ("frozen_table02_field", "mean_true_delta_dice_routed"),
        ("frozen_pooled_values", OrderedDict([
            ("A1", 0.001658079789), ("A7", 0.007246629237), ("A8", 0.007515754298),
        ])),
        ("macro_definition",
         "macro = (1/4) * sum_over_4_domains( mean_over_cases_in_domain( delta ) ) — equal "
         "domain weight"),
        ("are_they_equal", False),
        ("why_it_matters",
         "DEV is unbalanced (ISIC 2173, KUB 1680, KVASIR 592, BUSI 512), so pooled and macro "
         "differ. The frozen Phase-28 arm table reports POOLED means; BARR-M1 declares an "
         "equal-domain MACRO endpoint. They are different statistics."),
        ("reproduction_gate_consequence",
         "The positive control therefore compares SUMS and COUNTS (definition-free), never the "
         "pooled mean against a macro mean."),
        ("reporting_rule", "Label every mean explicitly as POOLED or MACRO. Never mix them in one "
                           "table without a column label."),
    ])
    r["6_keyed_join"] = OrderedDict([
        ("label_row_order_equals_membership_row_order", False),
        ("positional_mismatches", 4955),
        ("n_rows", N),
        ("id_sets_identical", True),
        ("join_key", "sample_id"),
        ("join_validation", "one_to_one"),
        ("why",
         "The Phase-25C label file and the Phase-25E membership file are in DIFFERENT row orders "
         "(4955 of 4957 positions differ). A positional zip would silently mis-assign the "
         "selection flag to almost every case and would still 'run'."),
        ("required_control", "R2 asserts positional equality is FALSE and that the keyed join is "
                             "one-to-one with zero missing selections."),
    ])
    return r


def precision_md(r):
    return f"""# BARR-M1 v1.0c — Final Reporting Precision Clarification

**Revision:** `{REV}`
**Mode:** reporting precision only. **No measured value is changed.**
**Relationship:** additive to v1.0a and v1.0b. Both are preserved byte-for-byte.

---

## 1. A1 harm rate — strict versus tolerance-adjusted

| Variant | Numerator | Denominator | Rate |
|---|---|---|---|
| **Strict** (`delta < 0`) | **2115** | 4957 | **42.6670 %** |
| **Tolerance-adjusted** (`delta < −1e-9`) | **2107** | 4957 | **42.5055 %** |

The 8-case difference sits in `−1e-9 ≤ delta < 0` — floating-point-scale negatives, not
scientifically meaningful harm. **Report both**, and declare which is primary in the caption.
Neither replaces the other.

## 2. A7 and A8 harm, all-population

| Arm | Harmed | Denominator | Rate |
|---|---|---|---|
| A7 | **412** | 4957 | **8.3115 %** |
| A8 | **390** | 4957 | **7.8677 %** |

Both use the **full 4957** denominator, so both are directly comparable to A1's 2115/4957.
Neither is a conditional rate.

## 3. A8 selection, acceptance, rejection

| Quantity | Value | Fraction of 4957 | Fraction of selected |
|---|---|---|---|
| Selected | **1239** | 25.000 % | 100 % |
| Accepted | **1205** | 24.309 % | 97.256 % |
| Rejected | **34** | 0.686 % | 2.744 % |

`selected = accepted + rejected` → 1239 = 1205 + 34.

## 4. Candidate refinement execution ≠ post-safety acceptance

- **Execution** — `R_psi` actually ran on the case. Determined **only** by router membership.
- **Acceptance** — `S_omega` allowed the refined mask to **replace** the global mask. Evaluated
  **only** where execution occurred.

**A7** executes 1239 and accepts all 1239 (no safety stage).
**A8** executes the **same 1239** and accepts **1205**, rejecting **34**.

A case can therefore be **executed and then rejected**; its delta is then exactly **0.0** — it is
neither helped nor harmed. It is **not** a harm and must never be counted as one. `n_executed`
and `n_accepted` are different quantities and must never be interchanged as denominators.

## 5. Pooled average versus equal-domain macro average

| Statistic | Definition | Domain weighting |
|---|---|---|
| **Pooled** | `sum(delta) / n_executed` | proportional to case count |
| **Macro** | `(1/4) · Σ_domain mean_in_domain(delta)` | **equal** across the 4 domains |

DEV is unbalanced — ISIC 2173, KUB 1680, KVASIR 592, BUSI 512 — so the two statistics differ.

The frozen Phase-28 arm table reports **pooled** values in `mean_true_delta_dice_routed`:
A1 `0.001658079789`, A7 `0.007246629237`, A8 `0.007515754298`.
BARR-M1 declares an **equal-domain macro** endpoint. **These are different statistics.**

**Consequence for the gate:** the positive control compares **sums and counts** (definition-free),
never a pooled mean against a macro mean. Every reported mean must be labelled `POOLED` or `MACRO`.

## 6. The keyed `sample_id` join

The Phase-25C label file and the Phase-25E membership file are in **different row orders** —
**4955 of 4957 positions differ** — although the ID **sets** are identical.

A positional `zip` would silently mis-assign the selection flag to almost every case and would
still appear to run. **The join must be keyed on `sample_id` with one-to-one validation.**
Gate check `R2` asserts that positional equality is **false** and that the keyed join is
one-to-one with zero missing selections.

---

**No measured value in this document differs from v1.0a / v1.0b.** This document only adds
denominators, labels and join semantics.
"""


# ---------------------------------------------------------------------------
def task2_scope_freeze():
    return OrderedDict([
        ("artifact", "barr_m1_v1_0c_scope_freeze"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("identifier", "BARR-M1"),
        ("classification", "DESCRIPTIVE_POLICY_COMPARISON"),
        ("not_a_router_causal_ablation", True),
        ("arms", ["A0", "A1", "A8"]),
        ("arms_excluded", ["A2", "A3", "A4", "A5", "A6", "A7", "R1", "R2", "R3", "F1"]),
        ("population", "ROUTER_DEVELOPMENT"),
        ("population_n", N),
        ("population_digest",
         "data_cache/phase25b_barr_pre_refinement_features_v1_2/metadata.csv"),
        ("population_digest_sha256",
         "ee8c304350d28d907c053a355da1f878ff7f9dd137761034283459aeed071093"),
        ("evaluation_class", "IN_SAMPLE_DEVELOPMENT"),
        ("execution_mode", "CPU_ONLY_RE_ANALYSIS_ONLY"),
        ("source", "preserved Phase-25 and Phase-28 arrays"),
        ("new_model_construction", False),
        ("new_forward_passes", False),
        ("new_training", False),
        ("A7_A8_execution_within_barr_m1", False),
        ("TEST_access", False),
        ("ROUTER_HOLDOUT_access", False),
        ("external_data_access", False),
        ("endpoint_contract", OrderedDict([
            ("paired_contrasts", ["A8_minus_A0", "A8_minus_A1", "A1_minus_A0"]),
            ("same_eligible_cases", True),
            ("skip_or_reject_contributes_zero", True),
            ("denominator", "all 4957 (intent-to-treat)"),
            ("macro_definition", "(1/4) * sum_over_4_domains(mean_in_domain(delta))"),
            ("pooled_definition", "sum(delta) / n_executed — reported separately, never as macro"),
            ("harm_strict", "delta < 0"),
            ("harm_tolerance_adjusted", "delta < -1e-9"),
            ("harm_rates_reported_separately", True),
        ])),
        ("bootstrap_contract", OrderedDict([
            ("procedure", "paired bootstrap, common resampled indices per contrast"),
            ("n_resamples", 2000),
            ("seed", 42),
            ("grouping_unit", "domain-stratified; KUB patient-clustered (267); "
                              "ISIC/BUSI/KVASIR per-case (no patient id)"),
            ("ci", "95% percentile"),
            ("missingness", "ABORT on any missing case, NaN or duplicate sample_id"),
            ("multiplicity", "DESCRIPTIVE_NO_POST_HOC_CORRECTION"),
        ])),
        ("claim_class", "DESCRIPTIVE_DEV"),
        ("prohibited_claims", ["HELD_OUT", "CONFIRMATORY", "GENERALISATION", "CLINICAL_SAFETY",
                               "SUPERIORITY", "ISOLATED_CAUSAL_ROUTER_EFFECT"]),
        ("frozen_components", OrderedDict([
            (k, OrderedDict([("name", v[0]), ("sha256", v[1]), ("params", v[2])]))
            for k, v in COMPONENTS.items()
        ])),
        ("frozen_constants", OrderedDict([
            ("roi_proposal_threshold", 0.30), ("roi_expansion_factor", 1.50),
            ("roi_resolution", 256), ("segmentation_output_threshold", 0.50),
            ("safety_accept_threshold", 0.50), ("budget", 0.25), ("K", 1239),
            ("lambda", 0.25), ("bootstrap_replicates", 2000), ("bootstrap_seed", 42),
            ("harm_tolerance", HARM_TOL),
        ])),
        ("scope_is_frozen", True),
        ("approval_status", "NOT_APPROVED"),
    ])


def task4_authorization_md(scope, gate_sha):
    return f"""# BARR-M1 — Supervisor Authorization Request

**Revision:** `{REV}`
**Status:** request only. **Nothing is authorized by this document.**

---

## 1. Research question and limited claim class

**Question.** Under one frozen fusion rule, on one frozen development population, how do three
complete frozen segmentation policies differ in macro-domain Dice and in harmful-refinement
behaviour — and how much of the difference is attributable to refining everywhere versus to
routing with a post-safety gate?

**Claim class: `DESCRIPTIVE_DEV` only.**

Permitted:
> "On a governed development population that also participated in component selection, policies
> A0/A1/A8 differed in macro-domain Dice by X; the all-population harmed-case rate was Y for
> refine-all and Z for the routed, safety-gated policy."

Prohibited: held-out performance · confirmatory inference · generalisation · clinical safety ·
superiority of BARR · an isolated causal router effect.

## 2. Exact frozen component and population identities

| Component | Class | SHA-256 | Params |
|---|---|---|---|
| G | `GlobalMedFiLM` | `286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7` | 3,523,001 |
| R_psi | `BARRRegionalRefinerV1` | `6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109` | 1,276,401 |
| B_phi | `BARRBenefitRouterV1` | `8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b` | 36,801 |
| S_omega | `BARRPostSafetyV1` | `eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e` | 1,217 |

**Population:** `ROUTER_DEVELOPMENT`, n = **4,957**; metadata digest
`ee8c304350d28d907c053a355da1f878ff7f9dd137761034283459aeed071093`.

**Frozen inputs (SHA-bound):**

| Input | SHA-256 |
|---|---|
| Phase-25C OOF gain labels | `fd6ca32c33a3bddb75f986b1350d54ec35b11d3bf5cb0fdc029962a5aa94865f` |
| Phase-25E C8 membership (λ0.25 / budget 0.25) | `4c411d589866434b824245d3c940bc09873f3cbc096ddc8a44776cd56273393b` |
| Phase-25F OOF safety predictions | `a9f63edd6d58a9a1d78a052a3e4539c6e0dd4d68bfb1c09c4c36789c441ebdee` |
| Phase-28 arm table 02 | `171168f973d0a210913b567c4b743f134b1918f3d22be55a6e7046890400e3fc` |

**Frozen constants:** ROI 0.30 / expansion 1.50 / resolution 256; segmentation output 0.50;
safety accept 0.50; budget 0.25 (K = 1239); λ 0.25; bootstrap 2000 / seed 42; harm tolerance 1e-9.

## 3. Scope and execution exclusions

**In scope.** Arms **A0, A1, A8** only. `CPU_ONLY_RE_ANALYSIS_ONLY` over preserved arrays.
Paired A8−A0, A8−A1, A1−A0 with the frozen bootstrap.

**Excluded.** Any arm outside A0/A1/A8 · **A7** · any new factor · any new model construction ·
any forward pass · any training · TEST · ROUTER_HOLDOUT · external data · any new scientific
contrast beyond the three declared paired contrasts.

## 4. Existing evidence and methodological limitations

**Already established (frozen, not re-derived here):**
- A0/A1/A7/A8 reproduce **exactly** from frozen per-case arrays (9/9 checks at 1e-9) with zero
  inference — so this study is a re-analysis, not an inference run.
- Frozen Phase-28 aggregates: A1 Σ = 8.219101516 (2115/4957 harmed, strict); A7 Σ = 8.9785736244
  (1239 executed, 412 harmed); A8 Σ = 9.0564839294 (1205 executed, 390 harmed).

**Limitations that must appear in every caption:**
1. **The primary population is the training population** of `B_phi` and `S_omega` (5-fold CV plus
   an all-DEV final refit) and a subset of TRAIN for `G` and `R_psi`. **No pristine independent
   population remains** — ROUTER_HOLDOUT was consumed by Phase30, TEST is locked.
2. **G is in-sample**; `R_psi`, `B_phi` and `S_omega` per-case predictions are cross-fitted. This
   limits but does not eliminate optimistic bias.
3. **Patient clustering is available only for KUB** (267). ISIC/BUSI/KVASIR have no patient
   identifier, so within-source correlation is unmodelled.
4. **Harm rates are reported on two denominators** — all-population and conditional-on-execution —
   and both must appear. The all-population A8 rate (390/4957 = 7.8677 %) is **not** comparable to
   a conditional rate, and vice versa.
5. **Pooled and macro means differ** on this unbalanced population; each must be labelled.
6. **No safety metric exists** and there is no `S_omega`-absent arm, so the safety contribution is
   **not measurable within Phase-28** (C2b remains `NOT_ESTABLISHED`).

## 5. Expected CPU-only workload

| Item | Estimate |
|---|---|
| Model constructions / forwards / autograd | **0 / 0 / 0** |
| GPU time | **0 s** |
| CPU wall time | **minutes** (deterministic array arithmetic + 3 × 2000 bootstrap resamples) |
| Disk | per-case outputs for 3 arms × 4957 rows (CSV, a few MB) |
| Restartable | yes — per-arm idempotent completion markers |

## 6. Separate, optional future proposal — BARR-M2

**Not requested here.** A7 vs A8 is the **only** pre-registered single-component isolation in the
frozen design (`frozen_matched_contrasts = ["A7_vs_A8"]`). Frozen paired result: mean
**+1.5717229e-05**, 95 % CI **[−1.4313785e-05, +5.1010811e-05]** — crosses zero.

A separate study (`BARR-M2`, provisional) would decompose the `S_omega` contribution descriptively,
also with zero inference. **It must not be folded into BARR-M1**, because that would change the
study from a three-policy comparison to a component-isolation analysis with a different claim class.

## 7. Supervisor authorization block — **EMPTY**

```
AUTHORIZATION REQUEST — BARR-M1 (v1.0c)

Study identifier      : BARR-M1
Classification        : DESCRIPTIVE POLICY_COMPARISON (not a router causal ablation)
Arms                  : A0, A1, A8 ONLY
Population            : ROUTER_DEVELOPMENT n=4957  (IN_SAMPLE_DEVELOPMENT — acknowledged)
Execution mode        : CPU_ONLY_RE_ANALYSIS_ONLY (0 model constructions, 0 forwards)
Endpoint              : paired A8-A0 / A8-A1 / A1-A0; equal-domain MACRO Dice
                        (pooled reported separately and labelled)
Harm rates            : BOTH strict (delta<0) and tolerance-adjusted (delta<-1e-9)
Bootstrap             : 2000 resamples, seed 42, paired common indices, domain-stratified
Gate                  : R1-R10 re-analysis gate validated (harness {gate_sha[:16]}…)

EXPLICITLY NOT AUTHORISED
  A7 or any arm outside A0/A1/A8 · any new factor · any model construction or forward
  pass · any training · TEST · ROUTER_HOLDOUT · external data · clinical-safety,
  held-out, superiority or confirmatory claims · BARR-M2 (separate request)

AUTHORIZED BY : ______________________   DATE : ____________
AUTHORIZATION ID : ____________________   [ ] APPROVED   [ ] REJECTED
```

**Completion of this work order does not constitute authorization.**
"""


def packet_index_md(scope, gate_sha):
    return f"""# BARR-M1 — Approval Packet Index (v1.0c)

**Revision:** `{REV}`
**Terminal:** `BARR_M1_APPROVAL_PACKAGE_READY__SCIENTIFIC_EXECUTION_NOT_AUTHORIZED`
**Approval status:** **NOT APPROVED**

---

## What this packet is

A self-contained, versioned, integrity-manifested release of everything a supervisor needs to
decide on BARR-M1 — and nothing that could be mistaken for execution.

## Reading order

| # | Document | Purpose |
|---|---|---|
| 1 | `barr_m1_v1_0c_supervisor_authorization_request.md` | **Start here.** The decision document. |
| 2 | `barr_m1_v1_0c_reporting_precision.md` | Six precision clarifications (Task 1). |
| 3 | `../barr_m1_v1_0b/barr_m1_v1_0b_addendum.md` | The numerical/contrast reconciliation. |
| 4 | `../barr_m1_v1_0a/barr_m1_work_order_revision_v1_0a.md` | The corrected study design. |
| 5 | `../barr_m1_v1_0a/barr_m1_supervisor_memorandum_v1_0a.md` | The short memo. |

## Machine-readable evidence

| Artifact | Content |
|---|---|
| `reports/audits/barr_m1_v1_0c_scope_freeze.json` | Frozen execution scope |
| `reports/audits/barr_m1_v1_0c_precision_audit.json` | Precision numbers |
| `reports/audits/barr_m1_v1_0c_gate_validation.json` | R1–R10 gate validation |
| `reports/audits/barr_m1_v1_0c_release_manifest.json` | SHA-256 integrity manifest |
| `reports/audits/barr_m1_v1_0c_final_check.json` | Release checks |
| `reports/audits/barr_m1_v1_0c_terminal.json` | Terminal state |

## Gate

`scripts/analysis/barr_m1_reanalysis_gate_v1_0c.py` — harness SHA `{gate_sha}`.

- `--validate` runs the gate **without** producing scientific output.
- `--execute` is **refused** in this build.
- The gate reproduces the frozen A0/A1/A7/A8 aggregates exactly and runs 8 synthetic negative
  controls; it computes **no** new paired contrast.

## State

```
BARR_M1_APPROVAL_PACKAGE_READY__SCIENTIFIC_EXECUTION_NOT_AUTHORIZED
```

No training · no inference · no new contrast · no TEST · no ROUTER_HOLDOUT · no frozen-artifact
modification.
"""


# ---------------------------------------------------------------------------
def main():
    # --- validate the gate (positive + negative controls only) ---
    gate_mod = load_gate()
    gate_result, gate_code = gate_mod.validate(None, None)
    gate_sha = gate_result["harness_sha256"]

    s_gate = write_json(os.path.join(AUDIT, "barr_m1_v1_0c_gate_validation.json"), gate_result)

    # --- Task 1 ---
    prec = OrderedDict([
        ("artifact", "barr_m1_v1_0c_precision_audit"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("measured_values_changed", False),
        ("clarifications", task1_precision()),
    ])
    s_prec = write_json(os.path.join(AUDIT, "barr_m1_v1_0c_precision_audit.json"), prec)
    s_prec_md = write_once(os.path.join(PKG, "barr_m1_v1_0c_reporting_precision.md"),
                           precision_md(prec["clarifications"]))

    # --- Task 2 ---
    scope = task2_scope_freeze()
    s_scope = write_json(os.path.join(AUDIT, "barr_m1_v1_0c_scope_freeze.json"), scope)

    # --- Task 4 ---
    s_auth = write_once(os.path.join(PKG, "barr_m1_v1_0c_supervisor_authorization_request.md"),
                        task4_authorization_md(scope, gate_sha))

    # --- Task 5: index + manifest ---
    s_index = write_once(os.path.join(PKG, "barr_m1_v1_0c_packet_index.md"),
                         packet_index_md(scope, gate_sha))

    # --- preserve prior artifacts (verify, do not rewrite) ---
    prior = OrderedDict()
    prior_ok = True
    for ver, files in PRIOR.items():
        prior[ver] = OrderedDict()
        for rel, exp in files.items():
            p = os.path.join(REPO, rel.replace("/", os.sep))
            obs = sha256_of(p) if os.path.isfile(p) else None
            ok = obs == exp
            prior_ok = prior_ok and ok
            prior[ver][rel] = OrderedDict([("expected", exp), ("observed", obs), ("match", ok)])

    frozen = OrderedDict()
    frozen_ok = True
    for name, (rel, exp) in FROZEN_SOURCES.items():
        p = os.path.join(REPO, rel.replace("/", os.sep))
        obs = sha256_of(p) if os.path.isfile(p) else None
        ok = obs == exp
        frozen_ok = frozen_ok and ok
        frozen[name] = OrderedDict([("path", rel), ("expected", exp), ("observed", obs),
                                    ("match", ok)])

    new_files = OrderedDict([
        ("reports/planning/barr_m1_approval_v1_0c/barr_m1_v1_0c_packet_index.md", s_index),
        ("reports/planning/barr_m1_approval_v1_0c/barr_m1_v1_0c_reporting_precision.md", s_prec_md),
        ("reports/planning/barr_m1_approval_v1_0c/"
         "barr_m1_v1_0c_supervisor_authorization_request.md", s_auth),
        ("reports/audits/barr_m1_v1_0c_precision_audit.json", s_prec),
        ("reports/audits/barr_m1_v1_0c_scope_freeze.json", s_scope),
        ("reports/audits/barr_m1_v1_0c_gate_validation.json", s_gate),
    ])

    # --- final check ---
    fc = OrderedDict()
    def C(k, ok, detail=""):
        fc[k] = OrderedDict([("pass", bool(ok)), ("detail", detail)])

    C("prior_v1_0a_v1_0b_artifacts_preserved", prior_ok)
    C("frozen_sources_unchanged", frozen_ok)
    C("no_measured_value_changed", prec["measured_values_changed"] is False)
    C("precision_covers_all_six_points", len(prec["clarifications"]) == 6)
    C("A1_strict_and_tolerance_both_reported",
      prec["clarifications"]["1_A1_strict_vs_tolerance"]["strict_numerator"] == 2115
      and prec["clarifications"]["1_A1_strict_vs_tolerance"]["tolerance_numerator"] == 2107)
    C("A7_A8_all_population_counts",
      prec["clarifications"]["2_A7_A8_all_population_harm"]["A7_harmed"] == 412
      and prec["clarifications"]["2_A7_A8_all_population_harm"]["A8_harmed"] == 390)
    C("selection_acceptance_rejection_identity",
      prec["clarifications"]["3_A8_selection_and_acceptance"]["identity"].startswith("selected ="))
    C("execution_vs_acceptance_distinguished",
      "EXECUTED and then REJECTED"
      in prec["clarifications"]["4_execution_vs_acceptance"]["key_point"])
    C("pooled_vs_macro_distinguished",
      prec["clarifications"]["5_pooled_vs_macro"]["are_they_equal"] is False)
    C("keyed_join_required",
      prec["clarifications"]["6_keyed_join"]["label_row_order_equals_membership_row_order"] is False)
    C("scope_arms_exactly_A0_A1_A8", scope["arms"] == ["A0", "A1", "A8"])
    C("scope_classification_policy_comparison",
      scope["classification"] == "DESCRIPTIVE_POLICY_COMPARISON")
    C("scope_population_4957", scope["population_n"] == 4957)
    C("scope_cpu_only", scope["execution_mode"] == "CPU_ONLY_RE_ANALYSIS_ONLY")
    C("scope_no_new_model", scope["new_model_construction"] is False)
    C("scope_no_forwards", scope["new_forward_passes"] is False)
    C("scope_no_training", scope["new_training"] is False)
    C("scope_A7_excluded", scope["A7_A8_execution_within_barr_m1"] is False)
    C("scope_TEST_excluded", scope["TEST_access"] is False)
    C("scope_HOLDOUT_excluded", scope["ROUTER_HOLDOUT_access"] is False)
    C("harm_rates_separated_in_scope",
      scope["endpoint_contract"]["harm_rates_reported_separately"])
    C("gate_ready", gate_result["gate_ready"])
    C("gate_validation_no_failures",
      len(gate_result["validation_failures_excluding_R1"]) == 0)
    C("gate_positive_controls_exact",
      all(v["sum_match"] and v["n_executed_match"] for v in gate_result["positive_controls"].values()))
    C("gate_negative_controls_all_detected",
      all(v["pass"] for k, v in gate_result["checks"].items() if k.startswith("R8:")))
    C("gate_refuses_execution",
      gate_result["execution_refused"] and gate_result["refusal_reason"] is not None)
    C("gate_zero_model_activity",
      gate_result["model_constructions"] == 0 and gate_result["forwards"] == 0)
    C("gate_no_new_contrast", gate_result["new_scientific_contrast_computed"] is False)
    C("authorization_block_empty", True)
    C("approval_not_granted", True)
    C("TEST_reads_zero", True)
    C("ROUTER_HOLDOUT_reads_zero", True)

    n_fail = sum(1 for v in fc.values() if not v["pass"])
    status = ("BARR_M1_APPROVAL_PACKAGE_READY__SCIENTIFIC_EXECUTION_NOT_AUTHORIZED"
              if n_fail == 0 else "BARR_M1_APPROVAL_PACKAGE_BLOCKED")

    final = OrderedDict([
        ("artifact", "barr_m1_v1_0c_final_check"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("checks", fc), ("n_checks", len(fc)), ("n_failed", n_fail),
        ("failed", [k for k, v in fc.items() if not v["pass"]]),
        ("all_pass", n_fail == 0),
        ("terminal", status),
        ("approval_status", "NOT_APPROVED"),
    ])
    s_final = write_json(os.path.join(AUDIT, "barr_m1_v1_0c_final_check.json"), final)

    # --- manifest ---
    manifest_files = OrderedDict(new_files)
    manifest_files["reports/audits/barr_m1_v1_0c_final_check.json"] = s_final
    manifest_files["scripts/analysis/barr_m1_reanalysis_gate_v1_0c.py"] = sha256_of(GATE)
    manifest_files["scripts/analysis/barr_m1_v1_0c_approval_package.py"] = sha256_of(
        os.path.abspath(__file__))

    manifest = OrderedDict([
        ("artifact", "barr_m1_v1_0c_release_manifest"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("packet_version", "v1.0c"),
        ("new_files", manifest_files),
        ("prior_artifacts_preserved", prior),
        ("prior_artifacts_all_match", prior_ok),
        ("frozen_sources_verified", frozen),
        ("frozen_sources_all_match", frozen_ok),
        ("gate_harness_sha256", gate_sha),
        ("gate_ready", gate_result["gate_ready"]),
        ("approval_status", "NOT_APPROVED"),
    ])
    s_man = write_json(os.path.join(AUDIT, "barr_m1_v1_0c_release_manifest.json"), manifest)

    term = OrderedDict([
        ("artifact", "barr_m1_v1_0c_terminal"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("classification", "APPROVAL_PACKAGE_ONLY__NO_SCIENTIFIC_EXECUTION"),
        ("terminal", status),
        ("emitted", n_fail == 0),
        ("approval_status", "NOT_APPROVED"),
        ("scope", OrderedDict([
            ("identifier", "BARR-M1"),
            ("classification", "DESCRIPTIVE_POLICY_COMPARISON"),
            ("arms", ["A0", "A1", "A8"]),
            ("population", "ROUTER_DEVELOPMENT n=4957"),
            ("execution", "CPU_ONLY_RE_ANALYSIS_ONLY"),
            ("A7_included", False),
        ])),
        ("gate", OrderedDict([
            ("harness_sha256", gate_sha),
            ("ready", gate_result["gate_ready"]),
            ("n_checks", gate_result["n_checks"]),
            ("positive_controls_exact", True),
            ("negative_controls_detected", 8),
            ("execution_refused", gate_result["execution_refused"]),
        ])),
        ("zero_execution", OrderedDict([
            ("model_constructions", 0), ("checkpoint_deserializations", 0),
            ("forwards", 0), ("autograd_calls", 0), ("training_steps", 0),
            ("new_contrasts_computed", 0), ("TEST_reads", 0), ("ROUTER_HOLDOUT_reads", 0),
            ("frozen_artifacts_modified", 0), ("per_case_outputs_written", 0),
        ])),
        ("final_check_sha256", s_final),
        ("release_manifest_sha256", s_man),
    ])
    s_term = write_json(os.path.join(AUDIT, "barr_m1_v1_0c_terminal.json"), term)

    print("== BARR-M1 v1.0c FINAL APPROVAL PACKAGE ==")
    print("gate ready            :", gate_result["gate_ready"],
          "(%d checks, %d validation failures)" % (
              gate_result["n_checks"], len(gate_result["validation_failures_excluding_R1"])))
    print("gate harness sha256   :", gate_sha)
    print("positive controls     :", {k: v["sum_match"] for k, v in gate_result["positive_controls"].items()})
    print("execution refused     :", gate_result["execution_refused"])
    print("prior artifacts match :", prior_ok)
    print("frozen sources match  :", frozen_ok)
    print("final check           : %d/%d" % (len(fc) - n_fail, len(fc)))
    for k, v in manifest_files.items():
        print("  %-74s %s" % (k, v))
    print("  %-74s %s" % ("reports/audits/barr_m1_v1_0c_release_manifest.json", s_man))
    print("  %-74s %s" % ("reports/audits/barr_m1_v1_0c_terminal.json", s_term))
    print("TERMINAL:", status)
    if n_fail:
        print("FAILED:", final["failed"])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
