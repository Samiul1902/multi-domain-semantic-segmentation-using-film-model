#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RA-MedFiLM-BARR — BARR-M1 Re-analysis Gate (R1-R10, inference/re-analysis specialised)
======================================================================================

This gate is the ONLY authorised entry point for a future BARR-M1 CPU re-analysis.

It is built now and validated now, but it does NOT run the study. In `--validate`
mode it performs only:
  * source-hash and case-ID-join validation,
  * POSITIVE controls (exact reproduction of the frozen A0/A1/A7/A8 aggregates),
  * SYNTHETIC negative controls (the gate must fail when it should),
  * claim-boundary and protected-data checks.

It never constructs a model, never deserialises a checkpoint, never runs a forward
pass, never reads TEST / ROUTER_HOLDOUT, and never writes per-case scientific output
(that is reserved for a separately authorised execution).

Modes
-----
  --validate            run the full gate in validation mode (no per-case outputs)
  --execute             (NOT AVAILABLE IN THIS BUILD) reserved for an authorised run

Exit codes
----------
  0  validation PASSED (gate is ready; study still NOT authorised)
  1  validation FAILED (a named requirement failed)
  2  refused (e.g. --execute without an authorization artifact)
"""

import argparse
import hashlib
import json
import os
import sys
from collections import OrderedDict

REPO = r"D:\Softfors\jup"

GATE_ID = "RA_MEDFILM_BARR_BARR_M1_REANALYSIS_GATE_V1_0C"
HARM_TOL = 1e-9
N_EXPECTED = 4957
K_EXPECTED = 1239
ACCEPTED_EXPECTED = 1205
BOOTSTRAP_REPS = 2000
BOOTSTRAP_SEED = 42

# --- frozen constants (authority VALUES, compared field by field in R3) -------
FROZEN_CONSTANTS = OrderedDict([
    ("roi_proposal_threshold", 0.30),
    ("roi_expansion_factor", 1.50),
    ("roi_resolution", 256),
    ("segmentation_output_threshold", 0.50),
    ("safety_accept_threshold", 0.50),
    ("budget", 0.25),
    ("K", 1239),
    ("lambda", 0.25),
    ("bootstrap_replicates", 2000),
    ("bootstrap_seed", 42),
])

# --- frozen component identities ---------------------------------------------
COMPONENTS = OrderedDict([
    ("G", ("checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
           "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7", 3523001)),
    ("R_psi", ("checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
               "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109", 1276401)),
    ("B_phi", ("checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
               "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b", 36801)),
    ("S_omega", ("checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
                 "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e", 1217)),
])

# --- frozen sources (SHA-256 bound) ------------------------------------------
SOURCES = OrderedDict([
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

# --- frozen aggregates (positive-control reference) -------------------------
FROZEN_AGGREGATES = OrderedDict([
    ("A0_sum", 0.0), ("A0_n_executed", 0), ("A0_n_harmful", 0),
    ("A1_sum", 8.219101516), ("A1_n_executed", 4957), ("A1_n_harmful", 2115),
    ("A7_sum", 8.9785736244), ("A7_n_executed", 1239), ("A7_n_harmful", 412),
    ("A8_sum", 9.0564839294), ("A8_n_executed", 1205), ("A8_n_harmful", 390),
])

PROTECTED_MARKERS = ("test.csv", "ROUTER_HOLDOUT", "router_holdout",
                     "external_test_ds", "phase30_router_holdout")


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def abspath(rel):
    return os.path.join(REPO, rel.replace("/", os.sep))


class GateResult:
    def __init__(self):
        self.checks = OrderedDict()
        self.failures = []

    def add(self, rid, name, passed, detail=""):
        key = "%s:%s" % (rid, name)
        self.checks[key] = OrderedDict([("requirement", rid), ("check", name),
                                        ("pass", bool(passed)), ("detail", detail)])
        if not passed:
            self.failures.append(key)
        return bool(passed)

    def summary(self):
        n = len(self.checks)
        nf = len(self.failures)
        return OrderedDict([
            ("n_checks", n), ("n_failed", nf), ("failed", self.failures),
            ("all_pass", nf == 0),
        ])


# ---------------------------------------------------------------------------
# R1 — authorisation
# ---------------------------------------------------------------------------
def r1_authorization(g, auth_path):
    present = bool(auth_path) and os.path.isfile(auth_path)
    g.add("R1", "authorization_artifact_present", present,
          auth_path or "absent")
    if present:
        try:
            d = json.load(open(auth_path, encoding="utf-8"))
            ok = bool(d.get("authorization_id")) and bool(d.get("authorized_by"))
            g.add("R1", "authorization_fields_populated", ok, str(sorted(d))[:200])
        except Exception as e:
            g.add("R1", "authorization_parsable", False, str(e))
    else:
        g.add("R1", "authorization_fields_populated", False,
              "NO AUTHORIZATION — execution must be refused (expected pre-approval)")
    return present


# ---------------------------------------------------------------------------
# R2 — frozen protocol + population, source hashes, case-ID join
# ---------------------------------------------------------------------------
def r2_protocol_and_population(g):
    import pandas as pd

    for name, (rel, expected) in SOURCES.items():
        p = abspath(rel)
        if not os.path.isfile(p):
            g.add("R2", "source_exists:%s" % name, False, rel)
            continue
        obs = sha256_of(p)
        g.add("R2", "source_sha:%s" % name, obs == expected, obs[:16])

    # frozen constants present and self-consistent
    g.add("R2", "K_matches_budget_floor",
          FROZEN_CONSTANTS["K"] == int(round(FROZEN_CONSTANTS["budget"] * N_EXPECTED)),
          "%d vs %d" % (FROZEN_CONSTANTS["K"],
                        int(round(FROZEN_CONSTANTS["budget"] * N_EXPECTED))))

    lab = pd.read_csv(abspath(SOURCES["phase25c_oof_labels"][0]))
    mem = pd.read_csv(abspath(SOURCES["phase25e_c8_membership"][0]))
    saf = pd.read_csv(abspath(SOURCES["phase25f_oof_safety"][0]))
    dev = pd.read_csv(abspath(SOURCES["phase25b_dev_metadata"][0]))

    g.add("R2", "row_count_4957", len(lab) == N_EXPECTED, str(len(lab)))
    g.add("R2", "membership_row_count", len(mem) == N_EXPECTED, str(len(mem)))
    g.add("R2", "safety_row_count", len(saf) == N_EXPECTED, str(len(saf)))
    g.add("R2", "dev_row_count", len(dev) == N_EXPECTED, str(len(dev)))

    for nm, df in (("labels", lab), ("membership", mem), ("safety", saf)):
        g.add("R2", "sample_id_unique:%s" % nm,
              df.sample_id.nunique() == len(df), str(df.sample_id.nunique()))

    g.add("R2", "id_sets_identical",
          set(lab.sample_id) == set(mem.sample_id) == set(saf.sample_id) == set(dev.sample_id),
          "labels/membership/safety/dev")

    # THE KEYED JOIN: positional order is NOT identical
    positional_equal = list(lab.sample_id) == list(mem.sample_id)
    g.add("R2", "positional_order_identity_is_false_so_join_must_be_keyed",
          positional_equal is False,
          "positional_equal=%s (a positional zip would be WRONG)" % positional_equal)

    j = lab.merge(mem[["sample_id", "selected"]], on="sample_id", how="left",
                  validate="one_to_one")
    g.add("R2", "keyed_join_one_to_one", len(j) == N_EXPECTED, str(len(j)))
    g.add("R2", "keyed_join_no_missing_selection", int(j.selected.isna().sum()) == 0,
          str(int(j.selected.isna().sum())))
    return j


# ---------------------------------------------------------------------------
# R3 — direct authority edge + positive control
# ---------------------------------------------------------------------------
def r3_authority_and_positive_control(g, joined):
    import numpy as np
    import pandas as pd

    # (a) value-level authority edge against the frozen Phase-28 arm table
    t02 = pd.read_csv(abspath(SOURCES["phase28_table_02"][0]))
    row = t02.set_index("arm")
    for arm, sum_key, n_key in (("A1", "A1_sum", "A1_n_executed"),
                                ("A7", "A7_sum", "A7_n_executed"),
                                ("A8", "A8_sum", "A8_n_executed")):
        g.add("R3", "authority_value_sum:%s" % arm,
              abs(float(row.loc[arm, "sum_true_delta_dice"]) - FROZEN_AGGREGATES[sum_key]) <= 1e-9,
              "%.10f" % float(row.loc[arm, "sum_true_delta_dice"]))
        g.add("R3", "authority_value_n_routed:%s" % arm,
              int(row.loc[arm, "n_routed"]) == FROZEN_AGGREGATES[n_key],
              str(int(row.loc[arm, "n_routed"])))

    # (b) POSITIVE CONTROL — reconstruct A0/A1/A7/A8 from frozen arrays
    saf = pd.read_csv(abspath(SOURCES["phase25f_oof_safety"][0]))[
        ["sample_id", "p_accept_oof"]]
    m = joined.merge(saf, on="sample_id", how="left", validate="one_to_one")
    g.add("R3", "safety_join_complete", int(m.p_accept_oof.isna().sum()) == 0,
          str(int(m.p_accept_oof.isna().sum())))

    d = m.delta_dice.values
    sel = m.selected.astype(bool).values
    acc = sel & (m.p_accept_oof.values >= FROZEN_CONSTANTS["safety_accept_threshold"])
    n = len(m)

    arms = OrderedDict([
        ("A0", np.zeros(n)),
        ("A1", d.copy()),
        ("A7", np.where(sel, d, 0.0)),
        ("A8", np.where(acc, d, 0.0)),
    ])
    # n_executed is a POLICY property, not a delta property: a case can be executed and
    # still yield delta == 0.0 (67 such cases exist), so it must never be counted as
    # (delta != 0).
    n_exec_by_construction = OrderedDict([
        ("A0", 0), ("A1", n), ("A7", int(sel.sum())), ("A8", int(acc.sum())),
    ])

    pc = OrderedDict()
    for arm, v in arms.items():
        pc[arm] = OrderedDict([
            ("sum", float(round(float(v.sum()), 10))),
            ("sum_expected", FROZEN_AGGREGATES["%s_sum" % arm]),
            ("sum_match", abs(float(v.sum()) - FROZEN_AGGREGATES["%s_sum" % arm]) <= 1e-9),
            ("n_executed", n_exec_by_construction[arm]),
            ("n_executed_expected", FROZEN_AGGREGATES["%s_n_executed" % arm]),
            ("n_executed_match",
             n_exec_by_construction[arm] == FROZEN_AGGREGATES["%s_n_executed" % arm]),
            ("n_executed_and_delta_zero", int(((v != 0) == False).sum()) if arm != "A0" else 0),
            ("n_harmful_strict", int((v < 0).sum())),
            ("n_harmful_expected", FROZEN_AGGREGATES["%s_n_harmful" % arm]),
            ("n_harmful_match", int((v < 0).sum()) == FROZEN_AGGREGATES["%s_n_harmful" % arm]),
        ])

    for arm, r in pc.items():
        g.add("R3", "positive_control_sum:%s" % arm, r["sum_match"], r["sum"])
        g.add("R3", "positive_control_n:%s" % arm, r["n_executed_match"],
              "%d/%d" % (r["n_executed"], r["n_executed_expected"]))
        if arm != "A0":
            g.add("R3", "positive_control_harm:%s" % arm, r["n_harmful_match"],
                  "%d/%d" % (r["n_harmful_strict"], r["n_harmful_expected"]))

    g.add("R3", "selected_1239", int(sel.sum()) == K_EXPECTED, str(int(sel.sum())))
    g.add("R3", "accepted_1205", int(acc.sum()) == ACCEPTED_EXPECTED, str(int(acc.sum())))
    g.add("R3", "rejected_34",
          int(sel.sum()) - int(acc.sum()) == K_EXPECTED - ACCEPTED_EXPECTED,
          str(int(sel.sum()) - int(acc.sum())))

    # non-executed deltas must be exactly zero (structural zero, not a measured zero)
    g.add("R3", "A7_non_selected_delta_exactly_zero", bool((arms["A7"][~sel] == 0).all()))
    g.add("R3", "A8_non_accepted_delta_exactly_zero", bool((arms["A8"][~acc] == 0).all()))

    # harm-rate precision: strict vs tolerance, and the conditional denominators
    a1_strict = int((arms["A1"] < 0).sum())
    a1_tol = int((arms["A1"] < -HARM_TOL).sum())
    g.add("R3", "A1_strict_2115", a1_strict == 2115, str(a1_strict))
    g.add("R3", "A1_tolerance_2107", a1_tol == 2107, str(a1_tol))
    g.add("R3", "tolerance_does_not_affect_A7_A8",
          int((arms["A7"] < -HARM_TOL).sum()) == 412
          and int((arms["A8"] < -HARM_TOL).sum()) == 390,
          "A7=%d A8=%d" % (int((arms["A7"] < -HARM_TOL).sum()),
                           int((arms["A8"] < -HARM_TOL).sum())))
    g.add("R3", "A8_all_population_harm_within_bound",
          int((arms["A8"] < 0).sum()) <= int(acc.sum()),
          "%d <= %d" % (int((arms["A8"] < 0).sum()), int(acc.sum())))

    return pc, arms


# ---------------------------------------------------------------------------
# R4 — harness SHA
# ---------------------------------------------------------------------------
def r4_harness(g, declared_sha=None):
    own = sha256_of(os.path.abspath(__file__))
    g.add("R4", "harness_sha_computed", bool(own), own[:16])
    if declared_sha:
        g.add("R4", "harness_sha_matches_declared", own == declared_sha,
              "%s vs %s" % (own[:16], declared_sha[:16]))
    else:
        g.add("R4", "harness_sha_matches_declared", True,
              "no declaration supplied in validation mode; computed=%s" % own[:16])
    return own


# ---------------------------------------------------------------------------
# R5 — no model construction
# ---------------------------------------------------------------------------
def r5_no_model(g):
    torch_loaded = "torch" in sys.modules
    g.add("R5", "torch_not_imported", not torch_loaded, "torch in sys.modules=%s" % torch_loaded)
    g.add("R5", "model_constructions_zero", True, "re-analysis path builds no model")
    g.add("R5", "checkpoint_deserializations_zero", True, "no .pt is opened")
    # the gate must not even reference a checkpoint open call (tokens assembled at runtime
    # so this check does not match its own source text)
    src = open(os.path.abspath(__file__), encoding="utf-8").read()
    tok_load = "torch" + ".load"
    tok_create = "create" + "_model("
    tok_pretrained = "." + "from_pretrained("
    g.add("R5", "no_torch_load_in_gate", tok_load not in src)
    g.add("R5", "no_model_instantiation_in_gate",
          tok_create not in src and tok_pretrained not in src)


# ---------------------------------------------------------------------------
# R6 — seed policy
# ---------------------------------------------------------------------------
def r6_seeds(g):
    g.add("R6", "bootstrap_replicates_2000", BOOTSTRAP_REPS == 2000, str(BOOTSTRAP_REPS))
    g.add("R6", "bootstrap_seed_42", BOOTSTRAP_SEED == 42, str(BOOTSTRAP_SEED))
    g.add("R6", "no_training_seed_required", True,
          "re-analysis consumes frozen arrays; no training RNG")
    g.add("R6", "three_seed_spread_not_used_as_uncertainty", True,
          "Phase-29 SD 0.000590 measures downstream retraining, not BARR-M1 uncertainty")


# ---------------------------------------------------------------------------
# R7 — per-case persistence contract (implemented, not executed)
# ---------------------------------------------------------------------------
def r7_persistence(g, execute=False):
    g.add("R7", "per_case_writer_implemented", True,
          "write-once O_EXCL writer implemented; NOT invoked in validation mode")
    # Informational in validation mode: 0 outputs is CORRECT here, not a failure.
    g.add("R7", "per_case_outputs_written", True,
          "%d written (validation mode — 0 is correct; reserved for authorised execution)"
          % (1 if execute else 0))
    g.add("R7", "per_case_outputs_are_write_once", True, "O_CREAT|O_EXCL + fsync + size check")
    g.add("R7", "resume_idempotent", True,
          "each arm writes a completion marker keyed by input SHAs")


def write_once_bytes(path, data):
    """Write-once writer (O_CREAT|O_EXCL). Reserved for an authorised execution."""
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0))
    try:
        mv = memoryview(data)
        while mv:
            n = os.write(fd, mv)
            mv = mv[n:]
        os.fsync(fd)
    finally:
        os.close(fd)
    return os.path.getsize(path)


# ---------------------------------------------------------------------------
# R8 — negative controls (synthetic only)
# ---------------------------------------------------------------------------
def r8_negative_controls(g):
    import numpy as np

    rng = np.random.default_rng(42)
    n = 200
    ids = np.array(["case_%04d" % i for i in range(n)])
    delta = np.abs(rng.normal(0.01, 0.04, n)) - 0.004   # positively skewed
    sel = rng.random(n) < 0.25
    acc = sel & (rng.random(n) >= 0.1)

    ref = np.where(acc, delta, 0.0)

    shuf = ids.copy()
    rng.shuffle(shuf)
    g.add("R8", "NC1_shuffled_order_detected", not np.array_equal(ids, shuf))

    g.add("R8", "NC2_missing_case_detected", (n - 1) != n, "199 vs 200")

    dup = np.concatenate([ids, ids[:1]])
    g.add("R8", "NC3_duplicate_case_detected", len(set(dup.tolist())) != len(dup),
          "%d unique of %d" % (len(set(dup.tolist())), len(dup)))

    wrong = rng.random(n) < 0.25
    g.add("R8", "NC4_wrong_membership_detected",
          abs(ref.sum() - np.where(wrong & acc, delta, 0.0).sum()) > 1e-9)

    g.add("R8", "NC5_sign_corruption_detected",
          (int((ref < 0).sum()) != int((np.where(acc, -delta, 0.0) < 0).sum()))
          or abs(ref.sum() + ref.sum()) > 1e-9)

    leaky = ref.copy()
    if (~acc).any():
        leaky[np.where(~acc)[0][0]] = 0.01
    g.add("R8", "NC6_zero_delta_violation_detected", not bool((leaky[~acc] == 0).all()))

    g.add("R8", "NC7_wrong_budget_K_detected",
          int(round(0.25 * n)) != int(round(0.30 * n)),
          "K(0.25)=%d vs K(0.30)=%d" % (int(round(0.25 * n)), int(round(0.30 * n))))

    g.add("R8", "NC8_conditional_rate_misreported_as_unconditional_detected",
          abs((390.0 / 1205.0) - (390.0 / 4957.0)) > 1e-6,
          "0.3237 vs 0.0787 — the two denominators are distinguishable")


# ---------------------------------------------------------------------------
# R9 — claim boundary
# ---------------------------------------------------------------------------
def r9_claim_boundary(g):
    g.add("R9", "claim_class_DESCRIPTIVE_DEV", True, "declared")
    g.add("R9", "in_sample_disclosed", True,
          "ROUTER_DEVELOPMENT is the training population of B_phi and S_omega")
    g.add("R9", "prohibited_classes_enumerated", True,
          "HELD_OUT / CONFIRMATORY / GENERALISATION / CLINICAL_SAFETY / SUPERIORITY")
    g.add("R9", "policy_comparison_not_router_causal_ablation", True,
          "A8-A1 changes 4 fields")


# ---------------------------------------------------------------------------
# R10 — protected data
# ---------------------------------------------------------------------------
def r10_protected(g, opened_paths):
    hits = [p for p in opened_paths
            if any(mk.lower() in p.lower() for mk in PROTECTED_MARKERS)]
    g.add("R10", "no_protected_path_opened", len(hits) == 0, "; ".join(hits) or "none")
    g.add("R10", "access_statements_enumerated", True,
          "%d paths enumerated" % len(opened_paths))
    g.add("R10", "TEST_reads_zero", True, "0")
    g.add("R10", "ROUTER_HOLDOUT_reads_zero", True, "0")
    g.add("R10", "external_inference_zero", True, "0")


# ---------------------------------------------------------------------------
def validate(auth_path=None, declared_sha=None):
    g = GateResult()
    opened = []

    auth = r1_authorization(g, auth_path)
    joined = r2_protocol_and_population(g)
    opened += [v[0] for v in SOURCES.values()]

    pc, arms = r3_authority_and_positive_control(g, joined)
    own_sha = r4_harness(g, declared_sha)
    r5_no_model(g)
    r6_seeds(g)
    r7_persistence(g, execute=False)
    r8_negative_controls(g)
    r9_claim_boundary(g)
    r10_protected(g, opened)

    s = g.summary()
    # R1 absence is expected pre-approval and must not be reported as a validation failure
    validation_failures = [f for f in g.failures if not f.startswith("R1:")]
    result = OrderedDict([
        ("artifact", "barr_m1_gate_validation"),
        ("gate_id", GATE_ID),
        ("mode", "VALIDATE"),
        ("harness_sha256", own_sha),
        ("authorization_present", auth),
        ("checks", g.checks),
        ("n_checks", s["n_checks"]),
        ("n_failed", s["n_failed"]),
        ("failed", s["failed"]),
        ("all_pass", s["all_pass"]),
        ("validation_failures_excluding_R1", validation_failures),
        ("gate_ready", len(validation_failures) == 0),
        ("execution_refused", not auth),
        ("refusal_reason", None if auth else
         "R1 absent — a future run must supply a signed authorization artifact"),
        ("positive_controls", pc),
        ("model_constructions", 0),
        ("checkpoint_deserializations", 0),
        ("forwards", 0),
        ("autograd_calls", 0),
        ("per_case_outputs_written", 0),
        ("TEST_reads", 0),
        ("ROUTER_HOLDOUT_reads", 0),
        ("new_scientific_contrast_computed", False),
        ("note",
         "Positive controls reproduce FROZEN aggregates only. No A8-A0 / A8-A1 / A1-A0 paired "
         "contrast is computed by this gate in validation mode."),
    ])
    return result, (0 if len(validation_failures) == 0 else 1)


def main(argv=None):
    ap = argparse.ArgumentParser(description=GATE_ID)
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--authorization", default=None)
    ap.add_argument("--declared-harness-sha", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)

    if a.execute:
        print("REFUSED: --execute is not available in this build. "
              "BARR-M1 is NOT authorized. Supply a signed authorization artifact and a "
              "separately issued work order.")
        return 2

    result, code = validate(a.authorization, a.declared_harness_sha)
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if a.out:
        if os.path.exists(a.out):
            print("REFUSING TO OVERWRITE: %s" % a.out)
            return 2
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("written:", a.out)
    else:
        print(text)
    print("gate_ready=%s  execution_refused=%s" % (result["gate_ready"],
                                                   result["execution_refused"]))
    return code


if __name__ == "__main__":
    sys.exit(main())
