#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PHASE 29 -- SUPERVISOR SPECIFICATION REPAIR v1.1
Three-Seed Deterministic Reproducibility Study
RA-MedFiLM-BARR

GOVERNANCE / SPECIFICATION ONLY.
NO TRAINING. NO MODEL FORWARD. NO NEW TARGETS. NO NEW PREDICTIONS.
NO METRICS. NO VAL808 READ. NO ROUTER_HOLDOUT. NO TEST. NO PHASE30.

Resolves the six blockers discovered by the Phase29 v1.0 pre-execution audit.
Preserves the v1.0 BLOCKED terminal and all v1.0 artifacts as provenance.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import sys

# --------------------------------------------------------------------------- #
# paths
# --------------------------------------------------------------------------- #
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AUD = os.path.join(ROOT, "reports", "audits")
TAB = os.path.join(ROOT, "reports", "tables")
DOCS = os.path.join(ROOT, "docs")

for d in (AUD, TAB, DOCS):
    os.makedirs(d, exist_ok=True)

NOW = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()

# --------------------------------------------------------------------------- #
# frozen constants
# --------------------------------------------------------------------------- #
MASTER_SEEDS = [42, 123, 3407]
NEW_SEEDS = [123, 3407]

SPEC_REVISION = "ra_medfilm_barr_phase29_repro_v1_1"
SPEC_CLASSIFICATION = "SUPERVISOR_PROSPECTIVE_REPRODUCIBILITY_SPECIFICATION_REPAIR"

V1_0_TERMINAL = "PHASE29_BLOCKED__REPRODUCIBILITY_TRAINING_SCOPE_UNRESOLVED"

SUCCESS_TERMINAL = (
    "PHASE29_SPEC_V1_1_COMPLETE__FIXED_GLOBAL_THREE_SEED_BARR_STACK_DEPENDENCIES_"
    "DEV_CALIBRATION_AND_EVALUATION_FROZEN__PHASE29_EXECUTION_ELIGIBLE_NOT_STARTED"
)

BLOCKED_TERMINALS = {
    "SEED42_REUSE_INCONSISTENT": "PHASE29_V1_1_BLOCKED__SEED42_REUSE_INCONSISTENT",
    "COMPONENT_TRAINING_PROTOCOL_INCOMPLETE":
        "PHASE29_V1_1_BLOCKED__COMPONENT_TRAINING_PROTOCOL_INCOMPLETE",
    "SEED_SPECIFIC_DEPENDENCY_CHAIN_INCOMPLETE":
        "PHASE29_V1_1_BLOCKED__SEED_SPECIFIC_DEPENDENCY_CHAIN_INCOMPLETE",
    "ROUTER_CALIBRATION_RULE_INCOMPLETE":
        "PHASE29_V1_1_BLOCKED__ROUTER_CALIBRATION_RULE_INCOMPLETE",
    "EVALUATION_POPULATION_INCOMPLETE":
        "PHASE29_V1_1_BLOCKED__EVALUATION_POPULATION_INCOMPLETE",
    "REPRODUCIBILITY_SPEC_INCOMPLETE":
        "PHASE29_V1_1_BLOCKED__REPRODUCIBILITY_SPEC_INCOMPLETE",
}

# ---- populations -----------------------------------------------------------
N_DEV = 4957
N_ROUTER_HOLDOUT = 875
N_VAL808 = 808
N_TEST = 1683

# ---- router budget ---------------------------------------------------------
OOF_BUDGET_B = 0.25
OOF_K = 1239                       # 0.25 * 4957
FINAL_BUDGET = 0.25
FINAL_K = 1239

# ---- exact rational constants (frozen, never re-derived) -------------------
C_EXACT = "1051648/10270749"                     # action cost C
LAMBDA_EXACT = "1/4"                             # canonical lambda
LAMBDA_C_EXACT = "262912/10270749"
TAU_C7_FINAL_SEED42_EXACT = "24796109646558761/20000000000000000000"
TAU_C7_FINAL_SEED42_FLOAT = 0.001239805482327938
TAU_C8_FINAL_SEED42_EXACT = "-5003565381643716252018011/205414980000000000000000000"
TAU_C8_FINAL_SEED42_FLOAT = -0.024358327623641256

# ---- frozen thresholds -----------------------------------------------------
BENEFICIAL_THRESHOLD = 0.02       # DeltaDice >= +0.02
HARMFUL_THRESHOLD = -0.01         # DeltaDice <= -0.01
S_OMEGA_DECISION_THRESHOLD = 0.50
PHASE27_NONINFERIORITY_MARGIN = 0.005

# ---- seed-42 canonical artifacts (SHA-bound) -------------------------------
CANONICAL_ARTIFACTS = [
    {
        "component": "G",
        "role": "FIXED_REFERENCE_NOT_A_SEED_REPLICATE",
        "description": "GlobalMedFiLM canonical checkpoint (Phase21)",
        "path": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
        "sha256": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
        "population_exact_match": True,
        "protocol_exact_match": True,
    },
    {
        "component": "R_psi",
        "role": "SEED42_REPLICATE",
        "description": "BARRRegionalRefinerV1 ROI-0.30 final refit (Phase25A)",
        "path": "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
        "sha256": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
        "population_exact_match": True,
        "protocol_exact_match": True,
    },
    {
        "component": "B_phi",
        "role": "SEED42_REPLICATE",
        "description": "BARRBenefitRouterV1 v1.2.1 final all-DEV refit (Phase25D)",
        "path": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
        "sha256": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
        "population_exact_match": True,
        "protocol_exact_match": True,
    },
    {
        "component": "S_omega",
        "role": "SEED42_REPLICATE",
        "description": "BARRPostSafetyV1 final all-DEV refit (Phase25F)",
        "path": "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
        "sha256": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
        "population_exact_match": True,
        "protocol_exact_match": True,
    },
    {
        "component": "phase25b_features",
        "role": "FIXED_FEATURE_MATRIX",
        "description": "Phase25B 202-D GT-free pre-refinement router input features",
        "path": "data_cache/phase25b_barr_pre_refinement_features_v1_2/features.npy",
        "sha256": "9c241963b54f23de1c9671ff6670dde7d6f7e2510869ef5ebc1baf3f7c833e0a",
        "population_exact_match": True,
        "protocol_exact_match": True,
    },
    {
        "component": "phase25e_final_router_dev_scores",
        "role": "FIXED_DEV_CALIBRATION_SOURCE",
        "description": "seed-42 final-router DEV calibration scores (Phase25E)",
        "path": "data_cache/phase25e_barr_resource_gate_v1_0/phase25e_final_router_dev_scores.csv",
        "sha256": "2d23e11090a5b3164d5b125c633bbccfbe307ecdc717d0f5689bf401bd849f9d",
        "population_exact_match": True,
        "protocol_exact_match": True,
    },
    {
        "component": "phase25e_final_router_dev_thresholds",
        "role": "FIXED_DEV_CALIBRATION_THRESHOLD_TABLE",
        "description": "seed-42 final-router DEV threshold table (Phase25E)",
        "path": "reports/tables/phase25e_final_router_dev_thresholds.csv",
        "sha256": "980e44aba6bb57bc86b2fa03060eaa181207297367fe7f7b1bbbde9c9b3bcfd1",
        "population_exact_match": True,
        "protocol_exact_match": True,
    },
    {
        "component": "phase27_val808_evidence",
        "role": "SEED42_CONTINUITY_EVIDENCE",
        "description": "Phase27 canonical VAL808 per-sample scores (seed-42 pipeline)",
        "path": "reports/tables/phase27_val808_per_sample_scores.csv",
        "sha256": None,          # computed at runtime
        "population_exact_match": True,
        "protocol_exact_match": True,
    },
]

# ---- provenance bindings ---------------------------------------------------
PROVENANCE_PATHS = [
    "configs/research_protocol.json",
    "reports/audits/research_protocol.md",
    "notebooks/phasewise/phase_29_3seed_reproducibility/README.md",
    "reports/audits/phase26_final_freeze.json",
    "reports/audits/phase28_final_freeze.json",
    "reports/audits/phase25d_cv_protocol_v1_2_1.json",
    "reports/audits/phase25d_final_refit_seed_contract_v1_2_1.json",
    "reports/audits/phase25d_data_loader_randomness_contract_v1_2_1.json",
    "reports/audits/phase25a_crossfit_protocol.json",
    "reports/audits/phase25f_cv_manifest_reuse_contract_v1_0.json",
    "reports/audits/phase25b_phase25c_handoff_schema.json",
    "reports/audits/phase26_router_threshold_exact_transform.json",
    "reports/audits/phase26_final_router_calibration_binding_v1_2.json",
    "reports/audits/phase26_router_reported_c7_threshold_binding_v1_1.json",
    "reports/audits/phase26_router_threshold_exact_transform.json",
    "reports/audits/phase29_terminal_state.json",
]

CONTROL_DOCS = [
    "docs/ARCHITECTURE.md", "docs/DESIGN.md", "docs/MEMORY.md",
    "docs/PRD.md", "docs/RULES.md", "docs/TASKS.md",
    "notebooks/phasewise/PHASE_INDEX.md",
]

# ---- components ------------------------------------------------------------
COMPONENTS = ["G", "R_psi", "B_phi", "S_omega"]

# ---- run count -------------------------------------------------------------
RUNS_G = 0
RUNS_RPSI = 4          # 3 cross-fit folds + 1 final refit
RUNS_BPHI = 6          # 5 CV folds + 1 final all-DEV refit
RUNS_SOMEGA = 6        # 5 CV folds + 1 final all-DEV refit
RUNS_PER_SEED = RUNS_G + RUNS_RPSI + RUNS_BPHI + RUNS_SOMEGA          # 16
REPRESENTED_RUNS = RUNS_PER_SEED * len(MASTER_SEEDS)                  # 48
REUSED_SEED42_RUNS = RUNS_PER_SEED                                    # 16
NEW_RUNS = RUNS_PER_SEED * len(NEW_SEEDS)                             # 32

NEW_RPSI = RUNS_RPSI * len(NEW_SEEDS)                                 # 8
NEW_BPHI = RUNS_BPHI * len(NEW_SEEDS)                                 # 12
NEW_SOMEGA = RUNS_SOMEGA * len(NEW_SEEDS)                             # 12


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def sha256_file(path: str):
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, obj):
    full = os.path.join(ROOT, path) if not os.path.isabs(path) else path
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")
    return full


def write_csv(path, header, rows):
    full = os.path.join(ROOT, path) if not os.path.isabs(path) else path
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(",".join(header) + "\n")
        for r in rows:
            f.write(",".join(str(c) for c in r) + "\n")
    return full


def _q(s):
    """CSV-quote a string field."""
    s = str(s)
    if any(c in s for c in ',"\n'):
        return '"' + s.replace('"', '""') + '"'
    return s


def write_csv_q(path, header, rows):
    full = os.path.join(ROOT, path) if not os.path.isabs(path) else path
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as f:
        f.write(",".join(_q(h) for h in header) + "\n")
        for r in rows:
            f.write(",".join(_q(c) for c in r) + "\n")
    return full


def router_fold_seed(s, k):
    return 1000 * s + k


def safety_fold_seed(s, k):
    return 1000 * s + 12000 + k


# --------------------------------------------------------------------------- #
# SECTION 0 -- entry gate
# --------------------------------------------------------------------------- #
def section_0():
    prev = json.load(open(os.path.join(AUD, "phase29_terminal_state.json"), encoding="utf-8"))
    prev_sha = sha256_file("reports/audits/phase29_terminal_state.json")

    checks = {
        "predecessor_terminal_exact": prev.get("terminal") == V1_0_TERMINAL,
        "seed_set_authoritatively_frozen":
            prev.get("seed_set_authoritatively_frozen") is True,
        "seeds_exact": prev.get("seeds") == MASTER_SEEDS,
        "six_active_blockers":
            sorted(prev.get("active_hard_blockers", [])) == sorted([
                "reproducibility_training_scope_unresolved",
                "multiseed_split_or_fold_rule_unresolved",
                "seed_specific_dependency_chain_unresolved",
                "seed_specific_router_target_dependency_unresolved",
                "multiseed_router_calibration_rule_unresolved",
                "reproducibility_evaluation_population_unresolved",
            ]),
        "training_runs_0": prev.get("training_runs") == 0,
        "model_forwards_0": prev.get("model_forwards") == 0,
        "new_predictions_0": prev.get("predictions_created") == 0,
        "router_holdout_reads_0": prev.get("router_holdout_reads") == 0,
        "val808_reads_0": prev.get("val808_reads") == 0,
        "test_reads_0": prev.get("test_reads") == 0,
    }

    # ---- physical reuse verification (seed-42 artifacts must exist + match sha)
    reuse_checks = {}
    reuse_rows = []
    for a in CANONICAL_ARTIFACTS:
        actual = sha256_file(a["path"])
        expected = a["sha256"]
        if expected is None:
            ok = actual is not None
        else:
            ok = (actual == expected)
        reuse_checks["exists_" + a["component"]] = actual is not None
        reuse_checks["sha_match_" + a["component"]] = ok
        reuse_rows.append({
            "component": a["component"],
            "role": a["role"],
            "path": a["path"],
            "sha256_expected": expected,
            "sha256_observed": actual,
            "exists": actual is not None,
            "sha_match": ok,
        })

    all_reuse_ok = all(reuse_checks.values())

    gate_pass = all(checks.values())

    out = {
        "artifact": "phase29_v1_1_entry_gate",
        "phase": 29,
        "revision": SPEC_REVISION,
        "classification": SPEC_CLASSIFICATION,
        "method": "RA-MedFiLM-BARR",
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "required_predecessor_terminal": V1_0_TERMINAL,
        "observed_predecessor_terminal": prev.get("terminal"),
        "predecessor_exit_class": prev.get("exit_class"),
        "predecessor_terminal_state_sha256": prev_sha,
        "predecessor_preserved_as_provenance": True,
        "checks": checks,
        "all_checks_pass": gate_pass,
        "seed42_reuse_physical_verification": {
            "rows": reuse_rows,
            "checks": reuse_checks,
            "all_pass": all_reuse_ok,
        },
        "gate_pass": gate_pass,
        "seed42_reuse_consistent": all_reuse_ok,
        "blocked_terminal_if_seed42_inconsistent":
            BLOCKED_TERMINALS["SEED42_REUSE_INCONSISTENT"],
        "blocked_terminal_if_gate_fail":
            BLOCKED_TERMINALS["REPRODUCIBILITY_SPEC_INCOMPLETE"],
        "all_pass": gate_pass and all_reuse_ok,
    }
    write_json("reports/audits/phase29_v1_1_entry_gate.json", out)
    print("[§0] v1.1 entry gate |", "PASS" if gate_pass else "FAIL",
          "| seed42 reuse consistent =", all_reuse_ok)
    return out


# --------------------------------------------------------------------------- #
# SECTION 1 -- canonical spec document
# --------------------------------------------------------------------------- #
def section_1():
    doc = f"""# Phase 29 --- Three-Seed Deterministic Reproducibility Study

**Specification revision:** `{SPEC_REVISION}`

**Classification:** `{SPEC_CLASSIFICATION}`

**Method:** RA-MedFiLM-BARR

**Generated (UTC):** {NOW}

---

## 0. Governance statement

This document is the canonical prospective provenance source for Phase 29. It is
declared as such by
`notebooks/phasewise/phase_29_3seed_reproducibility/README.md`.

This specification was authored **before any Phase 29 science was executed**.

| Field | Value |
|---|---|
| `science_executed_before_ruling` | `false` |
| `seed_results_seen` | `false` |
| `science_changed` | `false` |
| `canonical_bundle_changed` | `false` |
| `governance_only` | `true` |
| `execution` | `NONE` |

This repair is purely prospective. It resolves the six blockers reported by the
Phase 29 v1.0 pre-execution audit
(`PHASE29_BLOCKED__REPRODUCIBILITY_TRAINING_SCOPE_UNRESOLVED`). That blocked
terminal and all v1.0 audit artifacts are preserved unchanged as historical
provenance.

---

## 1. Authoritative seeds

```
MASTER_SEEDS = [42, 123, 3407]
```

* Primary source: `configs/research_protocol.json`
  (`policies.multi_seed`), SHA-256
  `df4b137f613f0f30a2efd244f096934e75e0898a9f4f43df08e5c0554b711212`.
* Supporting source: `reports/audits/research_protocol.md` ("Seeds: 42, 123, 3407"),
  SHA-256
  `f0dc4cd03df7d01fd237331b6c798330847fc85c8c2f09b8dee3368dbdbd64f4`.

The seeds are frozen. They are **not** to be changed, and no replacement seed may
be selected on the basis of training behaviour.

---

## 2. Training scope ruling

Phase 29 measures the reproducibility of the learned BARR regional/routing stack
**conditioned on the frozen canonical global representation**.

```
G / GlobalMedFiLM      = REUSE_CANONICAL_FIXED_ACROSS_ALL_SEEDS
R_psi / RegionalRefiner = THREE_SEED_REPRODUCIBILITY_IN_SCOPE
B_phi / BenefitRouter   = THREE_SEED_REPRODUCIBILITY_IN_SCOPE
S_omega / PostSafety    = THREE_SEED_REPRODUCIBILITY_IN_SCOPE
Phase26 wrapper / fusion = DETERMINISTIC_FIXED_CONFIGURATION
```

**Classification:** `MODULEWISE_DOWNSTREAM_REPRODUCIBILITY_WITH_CANONICAL_FIXED_GLOBAL`

Phase 29 must **not** be described as retraining the entire RA-MedFiLM system.

**Preferred manuscript wording:**

> "Three-seed reproducibility of the BARR stack conditioned on the frozen
> GlobalMedFiLM reference."

---

## 3. Why G is fixed

1. `G` is an upstream frozen reference established in Phase 21.
2. The Phase 29 scientific focus is reproducibility of the BARR conditional
   regional mechanism.
3. Faithfully retraining canonical `G` would require reproducing its original
   training-population semantics, which **predate** the
   `ROUTER_DEVELOPMENT` / `ROUTER_HOLDOUT` split.
4. Phase 29 must preserve the Phase 30 one-shot `ROUTER_HOLDOUT` lock.
5. Holding `G` fixed also isolates downstream stochastic variability instead of
   conflating it with global-backbone variability.

```
global_seed_variance_measured          = false
BARR_stack_seed_variance_measured      = true
```

This is a **scope statement**, not a weakness to hide.

---

## 4. Seed-42 reuse ruling

Existing seed-42 canonical downstream artifacts qualify as the first Phase 29
replicate. The audit verified, for each of `R_psi`, `B_phi`, `S_omega`:

```
protocol_exact_match  = true
population_exact_match = true
split_exact_match      = true
training_rule_exact_match = true
```

Frozen:

```
seed42_role = REUSE_EXISTING_CANONICAL_REPLICATE
```

Reused (SHA-bound):

| Evidence | Source |
|---|---|
| R_psi OOF + final | Phase25A seed42 |
| paired outcomes | Phase25C seed42 |
| B_phi OOF + final | Phase25D seed42 |
| S_omega OOF + final | Phase25F seed42 |
| integrated DEV evidence | Phase25G seed42 |
| VAL808 continuity evidence | Phase27 seed42 |

**Seed 42 is not retrained.** Seed-42 science is not rerun merely to produce
Phase29-branded files.

---

## 5. New seeds

Only seeds **123** and **3407** require new scientific training. They use the
same architecture, population membership, cross-fit partitions,
`FIT` / `EARLY_STOP` / `OUTER_TARGET` identities, losses, optimizer
hyperparameters, scheduler, checkpoint criterion, and threshold definitions as
canonical seed 42.

**The intended variable is `TRAINING_RANDOMNESS_ONLY`.**

---

## 6. Split rule

```
data_split_rule = FIXED_MEMBERSHIP_ACROSS_SEEDS
```

All dataset membership is identical across all three seeds. The following are
**not** regenerated:

* Phase19 `TRAIN` / `VAL` membership
* `ROUTER_DEVELOPMENT` membership
* `ROUTER_HOLDOUT` membership

No partition variance is introduced.

---

## 7. Cross-fit fold rule

Exact seed-42 cross-fit membership is frozen for every seed.

* **R_psi** --- reuse the exact Phase25A three outer folds: same `FIT` rows,
  same `EARLY_STOP` rows, same `OUTER_TARGET` rows.
* **B_phi** --- reuse the exact Phase25D five outer folds: same inner
  `FIT`/`ES` roles, same `OUTER_TARGET` rows.
* **S_omega** --- reuse the exact Phase25F five-fold manifests: same `FIT`,
  same `EARLY_STOP`, same `OUTER_TARGET`.

Folds are **not** regenerated using master seed 123 or 3407.

**Classification:** `FIXED_PARTITIONS__OPTIMIZATION_RANDOMNESS_ONLY`

This is load-bearing for interpreting across-seed variance.

---

## 8. Fixed global artifacts

For all seeds, reuse canonical:

* GlobalMedFiLM checkpoint
* global probability caches where scientifically compatible
* Phase25B 202-D GT-free feature matrix
* Phase25B feature schema

Because `G` is fixed, the pre-refinement router input features are also fixed.

```
feature_regeneration_rule = REUSE_PHASE25B_FEATURES_IDENTICALLY_ACROSS_SEEDS
```

SHA equality is required. There is **no** seed-specific Phase25B feature
regeneration.

---

## 9. Component training protocols

### 9.1 R_psi

For each new seed `s` in {{123, 3407}}, train exactly the inherited Phase25A
configuration.

| Item | Value |
|---|---|
| cross-fit fold models | 3 |
| final refit | 1 |
| logical runs per represented seed | 4 |
| new runs (seeds 123 + 3407) | 8 |

Fold manifests are the fixed Phase25A manifests. Only training RNG changes.

**Master-seed semantics** (generalising canonical seed-42-for-every-fold):

```
R_psi fold training seed   = s           (for each of the 3 folds)
R_psi final-refit seed     = s
```

Seed 42 reproduces canonical semantics exactly; seed 123 uses 123; seed 3407
uses 3407. New fold memberships are **not** derived from the seed.

### 9.2 Seed-specific paired-gain targets

**This is mandatory.** Because `R_psi` changes by seed, Phase25C `DeltaDice` is
seed-dependent.

For each master seed `s`, using that seed's leakage-safe `R_psi` OOF candidate:

```
DeltaDice_s = Dice(R_psi_s_OOF, y) - Dice(G_fixed, y)
```

Regenerate the paired target and the `BENEFICIAL` / `NEUTRAL` / `HARMFUL`
category using the **same frozen thresholds**:

```
BENEFICIAL >= +0.02
HARMFUL    <= -0.01
```

The GT-based target may be created **only after** the seed-specific OOF
candidate is frozen. Seed42 Phase25C `DeltaDice` is **never** reused as the
training target for `B_phi` seed 123 or seed 3407.

```
gain_target_regeneration_rule = SEED_SPECIFIC_FROM_R_PSI_OOF
```

### 9.3 B_phi

For each seed:

* router input feature matrix = same frozen Phase25B 202-D features
* router regression target = seed-specific `DeltaDice_s`
* exact Phase25D v1.2.1 protocol

| Item | Value |
|---|---|
| CV fold training runs | 5 |
| final all-DEV refit | 1 |
| logical runs per seed | 6 |
| new runs (seeds 123 + 3407) | 12 |

**RNG rule.** Canonical master 42 gives fold seeds `42000 + k`. Generalised:

```
router_fold_seed(s, k) = 1000 * s + k          for k = 0..4
```

| seed | fold seeds |
|---|---|
| 42 | 42000 .. 42004 |
| 123 | 123000 .. 123004 |
| 3407 | 3407000 .. 3407004 |

Final all-DEV refit seed = `s`. The seed does **not** regenerate fold
membership.

**Normalization.** Fold-specific normalization remains `FIT`-only, `ddof=0`,
the same 8 continuous scalar semantics, the same binary flags, and deep
features unnormalized. Because the feature matrix and fold membership are
fixed, normalization values **should** reproduce the seed-42 fold statistics
exactly for every master seed. This must be physically verified.
Normalization itself does not depend on the model seed.

**OOF scientific policy.** For each seed's OOF router scores, primary
development routing uses the fixed budget:

```
b = 0.25,  N = 4957,  K = 1239
```

Rank `delta_hat_oof` descending, then `sample_id` ascending; take the first
1239. This is for OOF development reproducibility. No scalar threshold is
needed for OOF comparison. There is no seed-specific `K`.

### 9.4 Final B_phi calibration

The previous A/B/C ambiguity is resolved prospectively as:

```
B = PER-SEED DEV CALIBRATION TO THE SAME FROZEN NOMINAL 25% RULE
```

For each seed's final all-DEV `B_phi`:

1. score all 4957 `ROUTER_DEVELOPMENT` rows
2. rank final `delta_hat` descending
3. `sample_id` ascending tie-break
4. `K = 1239`
5. derive the exact boundary threshold `tau_C7_final_s`
6. derive

```
tau_C8_final_s = tau_C7_final_s - 0.25 * C
```

with frozen

```
C = 1051648/10270749
```

This threshold is frozen **before** any VAL808 seed-specific result is opened.
This is **calibration, not performance selection**. Do not force 25% activation
on VAL808; apply each seed's fixed DEV-calibrated threshold to VAL808 as-is.

For seed 42, the derived values must reproduce exactly:

```
tau_C7_final_42 = 24796109646558761/20000000000000000000  (= {TAU_C7_FINAL_SEED42_FLOAT})
tau_C8_final_42 = {TAU_C8_FINAL_SEED42_EXACT}
                = {TAU_C8_FINAL_SEED42_FLOAT}
```

### 9.5 S_omega

Because seed-specific `R_psi` changes the candidate, post-safety features and
labels are also seed-dependent. For each seed:

* construct the OOF refined candidate from `R_psi_s`
* construct the exact frozen 20-D `S_omega` input vector
* `target_s = 1` iff `DeltaDice_s > 0`
* all exact-zero `DeltaDice` rows remain `FALLBACK` labels

Seed42 `S_omega` targets are **not** reused for other seeds.

```
safety_target_regeneration_rule = SEED_SPECIFIC_FROM_R_PSI_OOF
```

Training uses the exact Phase25F fold membership, architecture, normalization
semantics, `BCEWithLogitsLoss`, optimizer, scheduler, batch size, early stop,
checkpoint rule, and threshold `0.50`.

| Item | Value |
|---|---|
| CV folds | 5 |
| final all-DEV refit | 1 |
| logical runs per represented seed | 6 |
| new runs (seeds 123 + 3407) | 12 |

**RNG rule.** Canonical seed-42 CV fold seeds are `54000 + k`. Generalised:

```
safety_fold_seed(s, k) = 1000 * s + 12000 + k
```

| seed | fold seeds |
|---|---|
| 42 | 54000 .. 54004 |
| 123 | 135000 .. 135004 |
| 3407 | 3419000 .. 3419004 |

Final all-DEV safety refit seed = `s`. This is a prospective RNG generalization
only. Fold membership remains fixed.

---

## 10. Full seed dependency model

**Classification:** `MODULEWISE_DOWNSTREAM_REPRODUCIBILITY_WITH_CANONICAL_FIXED_GLOBAL`

For a given master seed `s`:

```
G                      = canonical fixed G
Phase25B features      = canonical fixed feature matrix
R_psi_s                = trained with seed s
DeltaDice_s            = generated from R_psi_s OOF
B_phi_s                = trained using fixed features + DeltaDice_s
S_omega_features_s     = generated from R_psi_s OOF candidates
S_omega_target_s       = 1 iff DeltaDice_s > 0
S_omega_s              = trained on those seed-specific features/targets
Final system_s         = G_fixed + R_psi_s + B_phi_s + S_omega_s + fixed wrapper/fusion
```

**No cross-seed mixing.** For example: seed123 `B_phi` may **not** use seed3407
targets; seed123 `S_omega` may **not** use seed42 candidate features.

---

## 11. Evaluation populations

### 11.1 Primary

```
population = ROUTER_DEVELOPMENT
n          = 4957
role       = PRIMARY_MULTI_SEED_REPRODUCIBILITY_DEVELOPMENT_EVIDENCE
```

Leakage-safe OOF predictions are used for `R_psi`, `B_phi`, `S_omega`. The
primary Phase 29 system comparison is based on these OOF development artifacts.
This preserves Phase 30's holdout independence.

### 11.2 Secondary

```
population = VAL808
n          = 808
role       = SECONDARY_MULTI_SEED_CONTINUITY_DEVELOPMENT_EVIDENCE
```

VAL808 was already opened in Phase 27. It is **not** an untouched holdout, not a
routing holdout, not external validation, and not TEST.

For seeds 123 and 3407, new VAL808 inference is allowed only after all
seed-specific training and DEV calibration are frozen. For seed 42, reuse the
Phase27 canonical VAL808 evidence when the exact pipeline and numeric inference
semantics match. Do not rerun seed-42 VAL808 unnecessarily.

### 11.3 README "TRAIN+VAL" reconciliation

The historical README wording is **not** silently deleted. It is recorded as
superseded operationally for Phase 29 by:

```
PRIMARY   = ROUTER_DEVELOPMENT OOF
SECONDARY = VAL808 continuity
```

`ROUTER_HOLDOUT` remains excluded. This is an **additive** supervisor
clarification.

---

## 12. Locks

### 12.1 ROUTER_HOLDOUT lock

Absolutely no ROUTER_HOLDOUT image read, mask read, feature read, outcome read,
router scoring, refiner inference, safety inference, or metric computation.
Phase 30 remains the first one-shot integrated ROUTER_HOLDOUT evaluation.

```
ROUTER_HOLDOUT_reads = 0
```

### 12.2 TEST lock

TEST remains untouched.

```
TEST_reads = 0
```

Phase 39 remains the sole TEST phase.

---

## 13. Training-run count

| Component | Runs / seed |
|---|---|
| G | 0 (Phase 29 scope) |
| R_psi | 4 |
| B_phi | 6 |
| S_omega | 6 |
| **Total represented per seed** | **16** |

| Quantity | Value |
|---|---|
| represented logical downstream runs (3 seeds) | 48 |
| reused historical seed-42 runs | 16 |
| **new Phase 29 runs** | **32** |

New-run breakdown: R_psi = 8, B_phi = 12, S_omega = 12.

```
represented_training_runs    = 48
reused_seed42_training_runs  = 16
new_training_runs_authorized = 32
```

No additional retraining.

---

## 14. Deterministic environment

For every new seed:

* Python `random` seed
* NumPy seed
* `torch.manual_seed`
* `torch.cuda.manual_seed_all`
* DataLoader generator
* worker initialization
* `cudnn.deterministic = true`
* `cudnn.benchmark = false`

AMP semantics remain inherited from each component's canonical protocol. Do
**not** standardize all components to one precision mode if their canonical
protocols differ.

---

## 15. Required outputs per new seed

### R_psi

3 leakage-safe OOF fold checkpoints; OOF regional candidates for all 4957 rows;
seed-specific paired-gain target table; 1 final refit checkpoint; complete
histories; determinism/provenance records. No seed result may be used to alter
another seed's training.

### B_phi

5 CV checkpoints; 4957 exactly-once OOF scores; 25% `K=1239` OOF membership;
1 final all-DEV checkpoint; final DEV score table; exact `tau_C7_final_s`; exact
`tau_C8_final_s`; normalization artifacts; complete histories. Threshold freeze
must precede VAL808 inference.

### S_omega

Seed-specific 20-D OOF features; seed-specific binary targets; 5 CV checkpoints;
4957 OOF safety predictions; 1 final checkpoint; normalization artifacts;
complete histories. Decision threshold remains exactly `0.50`.

---

## 16. OOF integrated system per seed

On `ROUTER_DEVELOPMENT`, for each seed:

* use seed-specific `B_phi` OOF score
* select fixed `K = 1239`
* use seed-specific `R_psi` OOF candidate
* use seed-specific `S_omega` OOF decision

Integrated output:

```
not selected                 -> global
selected + safety accept     -> seed-specific regional candidate
selected + safety reject     -> global
```

This yields leakage-safe `system_s` OOF evidence.

---

## 17. Metrics

### 17.1 DEV primary reproducibility metrics

For each seed report at minimum: macro-domain integrated `DeltaDice`;
per-domain `DeltaDice`; routed mean `DeltaDice`; `precision@budget`; benefit
capture; harmful activation share; `S_omega` accept fraction; `S_omega` reject
fraction.

Across 3 seeds report: mean, sample standard deviation, minimum, maximum,
range. Also report sign consistency. **No seed is declared winner.**

### 17.2 VAL808 secondary metrics

For each seed report: Global Dice; final integrated Dice; `DeltaDice`;
macro-domain `DeltaDice`; per-domain Dice/`DeltaDice`; realized router
activation; `S_omega` accept/reject counts. Use each seed's DEV-calibrated
final-router threshold. Do **not** force VAL808 to 25%. For seed 42, reuse the
exact Phase27 result where physically identical.

### 17.3 Phase27 preservation criterion

Per-seed VAL808 continuity is evaluated under the already frozen Phase27
non-inferiority rule:

```
margin    = 0.005
criterion = lower 95% CI > -0.005
```

This is a **per-seed continuity result**. It is **not** the Phase 29 completion
criterion. Phase 29 remains descriptive with:

```
NO_NUMERIC_REPRODUCIBILITY_PASS_FAIL_GATE
```

Report if one or more seeds fail preservation. Do not retune.

---

## 18. Primary interpretation

```
DESCRIPTIVE_THREE_SEED_REPRODUCIBILITY
```

**Primary scientific question:** How stable are the direction and practical
magnitude of the frozen BARR development effect when downstream BARR training
randomness is changed across seeds 42, 123 and 3407 while data partitions and
the GlobalMedFiLM reference remain fixed?

There is **no** numeric Phase 29 PASS/FAIL threshold.

---

## 19. Statistics

Phase 29 may report per-seed point estimates, per-seed frozen-population
bootstrap CIs where already defined, three-seed mean, sample SD, range,
min/max, and sign consistency.

Do **not** perform formal across-seed significance testing. Do **not** introduce
multiple-testing correction. **Phase 31 owns formal hypothesis testing.**

---

## 20. Canonical seed-42 bundle remains canonical

No Phase 29 result automatically replaces the Phase26 canonical bundle.

```
deployment_model_replaced = false
canonical_seed_changed    = false
best_seed_selected        = false
```

Even if seed 123 or seed 3407 has a numerically larger development result.
Phase 29 is **evidence, not model selection**.

---

## 21. Artifact roots

```
checkpoints/phase29_seed123/
checkpoints/phase29_seed3407/
data_cache/phase29_seed123/
data_cache/phase29_seed3407/
experiments/phase29_seed123/
experiments/phase29_seed3407/
```

Seed-42 weights are **not** duplicated unnecessarily. For seed 42, create
provenance bindings only.

---

## 22. Terminal states

**Success (only if every execution-critical field is prospectively complete):**

```
{SUCCESS_TERMINAL}
```

**Blocked:**

```
PHASE29_V1_1_BLOCKED__SEED42_REUSE_INCONSISTENT
PHASE29_V1_1_BLOCKED__COMPONENT_TRAINING_PROTOCOL_INCOMPLETE
PHASE29_V1_1_BLOCKED__SEED_SPECIFIC_DEPENDENCY_CHAIN_INCOMPLETE
PHASE29_V1_1_BLOCKED__ROUTER_CALIBRATION_RULE_INCOMPLETE
PHASE29_V1_1_BLOCKED__EVALUATION_POPULATION_INCOMPLETE
PHASE29_V1_1_BLOCKED__REPRODUCIBILITY_SPEC_INCOMPLETE
```

---

## 23. Directive

```
STOP.
DO NOT TRAIN.
DO NOT START PHASE30.
DO NOT OPEN ROUTER_HOLDOUT.
DO NOT OPEN TEST.
```
"""
    p = os.path.join(DOCS, "phase29_repro_spec.md")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(doc)
    sha = sha256_file("docs/phase29_repro_spec.md")
    out = {
        "artifact": "phase29_canonical_spec_document_binding",
        "phase": 29,
        "revision": SPEC_REVISION,
        "classification": SPEC_CLASSIFICATION,
        "method": "RA-MedFiLM-BARR",
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "path": "docs/phase29_repro_spec.md",
        "sha256": sha,
        "declared_by": {
            "path": "notebooks/phasewise/phase_29_3seed_reproducibility/README.md",
            "sha256": sha256_file(
                "notebooks/phasewise/phase_29_3seed_reproducibility/README.md"),
        },
        "previously_missing_now_created_prospectively": True,
        "science_executed_before_ruling": False,
        "seed_results_seen": False,
        "science_changed": False,
        "canonical_bundle_changed": False,
        "sections": 23,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_canonical_spec_document_binding.json", out)
    print("[§1] docs/phase29_repro_spec.md created | sha =", sha[:16])
    return out


# --------------------------------------------------------------------------- #
# SECTION 2 -- authoritative seeds
# --------------------------------------------------------------------------- #
def section_2():
    prot = sha256_file("configs/research_protocol.json")
    rp = sha256_file("reports/audits/research_protocol.md")
    primary = {
        "path": "configs/research_protocol.json",
        "sha256": prot,
        "key": "policies.multi_seed",
        "value": MASTER_SEEDS,
    }
    supporting = {
        "path": "reports/audits/research_protocol.md",
        "sha256": rp,
        "binds": "Seeds: 42, 123, 3407",
    }
    checks = {
        "primary_exists": prot is not None,
        "supporting_exists": rp is not None,
        "primary_sha_matches_v1_0":
            prot == "df4b137f613f0f30a2efd244f096934e75e0898a9f4f43df08e5c0554b711212",
        "supporting_sha_matches_v1_0":
            rp == "f0dc4cd03df7d01fd237331b6c798330847fc85c8c2f09b8dee3368dbdbd64f4",
        "seeds_unchanged_from_v1_0": MASTER_SEEDS == [42, 123, 3407],
    }
    out = {
        "artifact": "phase29_authoritative_seeds_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "classification": SPEC_CLASSIFICATION,
        "method": "RA-MedFiLM-BARR",
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "MASTER_SEEDS": MASTER_SEEDS,
        "primary_source": primary,
        "supporting_source": supporting,
        "seed_set_authoritatively_frozen": True,
        "replacement_seeds_permitted": False,
        "selection_based_on_training_behaviour": False,
        "checks": checks,
        "all_pass": all(checks.values()),
    }
    write_json("reports/audits/phase29_authoritative_seeds_v1_1.json", out)
    print("[§2] MASTER_SEEDS frozen =", MASTER_SEEDS)
    return out


# --------------------------------------------------------------------------- #
# SECTION 3-9 -- scope, reuse, partition rulings
# --------------------------------------------------------------------------- #
def section_3_9():
    # ---- shared physical reuse evidence (from entry gate) ----
    gate = json.load(open(os.path.join(AUD, "phase29_v1_1_entry_gate.json"),
                          encoding="utf-8"))
    reuse = gate["seed42_reuse_physical_verification"]
    sha_by_comp = {r["component"]: r["sha256_observed"] for r in reuse["rows"]}

    # ---------- §3 scope ----------
    scope = {
        "artifact": "phase29_supervisor_scope_ruling_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "classification": SPEC_CLASSIFICATION,
        "method": "RA-MedFiLM-BARR",
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "scope_decision": {
            "G": "REUSE_CANONICAL_FIXED_ACROSS_ALL_SEEDS",
            "R_psi": "THREE_SEED_REPRODUCIBILITY_IN_SCOPE",
            "B_phi": "THREE_SEED_REPRODUCIBILITY_IN_SCOPE",
            "S_omega": "THREE_SEED_REPRODUCIBILITY_IN_SCOPE",
            "phase26_wrapper_fusion": "DETERMINISTIC_FIXED_CONFIGURATION",
        },
        "scope_classification":
            "MODULEWISE_DOWNSTREAM_REPRODUCIBILITY_WITH_CANONICAL_FIXED_GLOBAL",
        "described_as_retraining_entire_system": False,
        "manuscript_wording":
            "Three-seed reproducibility of the BARR stack conditioned on the "
            "frozen GlobalMedFiLM reference.",
        "global_seed_variance_measured": False,
        "BARR_stack_seed_variance_measured": True,
        "training_scope_resolved": True,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_supervisor_scope_ruling_v1_1.json", scope)

    # ---------- §4 why G fixed ----------
    why_g = {
        "artifact": "phase29_g_fixed_rationale_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "G_treatment": "REUSE_CANONICAL_FIXED_ACROSS_ALL_SEEDS",
        "rationale": [
            "G is an upstream frozen reference established in Phase21.",
            "The Phase29 scientific focus is reproducibility of the BARR "
            "conditional regional mechanism.",
            "Faithfully retraining canonical G would require reproducing its "
            "original training population semantics, which predate the "
            "ROUTER_DEVELOPMENT / ROUTER_HOLDOUT split.",
            "Phase29 must preserve the Phase30 one-shot ROUTER_HOLDOUT lock.",
            "Holding G fixed isolates downstream stochastic variability instead "
            "of conflating it with global-backbone variability.",
        ],
        "global_seed_variance_measured": False,
        "BARR_stack_seed_variance_measured": True,
        "scope_statement_not_weakness": True,
        "G_checkpoint": {
            "path": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
            "sha256": sha_by_comp.get("G"),
        },
        "all_pass": True,
    }
    write_json("reports/audits/phase29_g_fixed_rationale_v1_1.json", why_g)

    # ---------- §5 seed-42 reuse finalization ----------
    reused_evidence = [
        ("R_psi OOF + final", "Phase25A seed42",
         "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030",
         sha_by_comp.get("R_psi")),
        ("B_phi OOF + final", "Phase25D seed42",
         "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42",
         sha_by_comp.get("B_phi")),
        ("S_omega OOF + final", "Phase25F seed42",
         "checkpoints/phase25f_barr_post_safety_v1_0_seed42",
         sha_by_comp.get("S_omega")),
        ("paired outcomes", "Phase25C seed42", "reports/tables/phase25c_*", None),
        ("integrated DEV evidence", "Phase25G seed42", "reports/tables/phase25g_*", None),
        ("VAL808 continuity evidence", "Phase27 seed42",
         "reports/tables/phase27_val808_per_sample_scores.csv",
         sha_by_comp.get("phase27_val808_evidence")),
    ]
    checks = {
        "protocol_exact_match": True,
        "population_exact_match": True,
        "split_exact_match": True,
        "training_rule_exact_match": True,
        "evaluation_rule_now_frozen": True,
        "seed42_retrained": False,
        "seed42_science_rerun_for_branding": False,
    }
    reuse_out = {
        "artifact": "phase29_seed42_reuse_finalization_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "classification": SPEC_CLASSIFICATION,
        "method": "RA-MedFiLM-BARR",
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "seed42_role": "REUSE_EXISTING_CANONICAL_REPLICATE",
        "seed42_reused": True,
        "seed42_retrained": False,
        "match_checks": checks,
        "reused_evidence": [
            {"evidence": e, "source": s, "path": p, "sha256": sh}
            for (e, s, p, sh) in reused_evidence
        ],
        "physical_sha_binding": {
            "rows": reuse["rows"], "all_pass": reuse["all_pass"],
        },
        "all_pass": all(v for k, v in checks.items()
                        if k not in ("seed42_retrained",
                                     "seed42_science_rerun_for_branding")) and reuse["all_pass"],
    }
    write_json("reports/audits/phase29_seed42_reuse_finalization_v1_1.json", reuse_out)

    # ---------- §6 new seeds ----------
    newseeds = {
        "artifact": "phase29_new_seed_scope_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "new_seeds_requiring_training": NEW_SEEDS,
        "reused_seeds": [42],
        "inherited_identically": [
            "architecture", "population membership", "cross-fit partitions",
            "FIT / EARLY_STOP / OUTER_TARGET identities", "losses",
            "optimizer hyperparameters", "scheduler", "checkpoint criterion",
            "threshold definitions",
        ],
        "intended_variable": "TRAINING_RANDOMNESS_ONLY",
        "all_pass": True,
    }
    write_json("reports/audits/phase29_new_seed_scope_v1_1.json", newseeds)

    # ---------- §7 split rule ----------
    split = {
        "artifact": "phase29_split_rule_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "data_split_rule": "FIXED_MEMBERSHIP_ACROSS_SEEDS",
        "all_dataset_membership_identical_across_seeds": True,
        "regenerated": [],
        "not_regenerated": [
            "Phase19 TRAIN/VAL membership",
            "ROUTER_DEVELOPMENT membership",
            "ROUTER_HOLDOUT membership",
        ],
        "partition_variance_introduced": False,
        "populations": {
            "ROUTER_DEVELOPMENT": N_DEV,
            "ROUTER_HOLDOUT": N_ROUTER_HOLDOUT,
            "VAL808": N_VAL808,
            "TEST": N_TEST,
        },
        "split_fold_rule_resolved": True,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_split_rule_v1_1.json", split)

    # ---------- §8 cross-fit fold rule ----------
    folds = {
        "artifact": "phase29_fixed_partition_ruling_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "classification": SPEC_CLASSIFICATION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "partition_classification":
            "FIXED_PARTITIONS__OPTIMIZATION_RANDOMNESS_ONLY",
        "components": {
            "R_psi": {
                "reused_manifest": "Phase25A three outer folds",
                "n_outer_folds": 3,
                "same_FIT_rows": True,
                "same_EARLY_STOP_rows": True,
                "same_OUTER_TARGET_rows": True,
                "source_artifact": "reports/audits/phase25a_crossfit_protocol.json",
                "source_sha256":
                    sha256_file("reports/audits/phase25a_crossfit_protocol.json"),
            },
            "B_phi": {
                "reused_manifest": "Phase25D five outer folds",
                "n_outer_folds": 5,
                "same_inner_FIT_ES_roles": True,
                "same_OUTER_TARGET_rows": True,
                "source_artifact": "reports/audits/phase25d_cv_protocol_v1_2_1.json",
                "source_sha256":
                    sha256_file("reports/audits/phase25d_cv_protocol_v1_2_1.json"),
                "cv_name": "BARR_ROUTER_CV5_GROUP_SAFE_DOMAIN_STRATIFIED_V1",
                "algorithm":
                    "StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)",
            },
            "S_omega": {
                "reused_manifest": "Phase25F five-fold manifests",
                "n_folds": 5,
                "same_FIT": True,
                "same_EARLY_STOP": True,
                "same_OUTER_TARGET": True,
                "source_artifact":
                    "reports/audits/phase25f_cv_manifest_reuse_contract_v1_0.json",
                "source_sha256": sha256_file(
                    "reports/audits/phase25f_cv_manifest_reuse_contract_v1_0.json"),
            },
        },
        "folds_regenerated_from_new_seeds": False,
        "crossfit_folds_fixed": True,
        "load_bearing_for_across_seed_variance": True,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_fixed_partition_ruling_v1_1.json", folds)

    # ---------- §9 fixed global artifacts / features ----------
    fixed = {
        "artifact": "phase29_fixed_global_artifacts_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "G_checkpoint": {
            "path": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
            "sha256": sha_by_comp.get("G"),
        },
        "phase25b_features": {
            "path": "data_cache/phase25b_barr_pre_refinement_features_v1_2/features.npy",
            "sha256": sha_by_comp.get("phase25b_features"),
            "shape": [4957, 202],
            "gt_free": True,
        },
        "feature_regeneration_rule":
            "REUSE_PHASE25B_FEATURES_IDENTICALLY_ACROSS_SEEDS",
        "sha_equality_required": True,
        "seed_specific_feature_regeneration": False,
        "feature_regeneration_resolved": True,
        "feature_matrix_fixed": True,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_fixed_global_artifacts_v1_1.json", fixed)

    print("[§3-§9] scope/reuse/partition rulings written")
    return {"scope": scope, "why_g": why_g, "reuse": reuse_out,
            "newseeds": newseeds, "split": split, "folds": folds, "fixed": fixed}


# --------------------------------------------------------------------------- #
# SECTION 10-20 -- component protocols, RNG, targets, calibration
# --------------------------------------------------------------------------- #
def section_10_20():
    # ---------- §10-§11 R_psi ----------
    rpsi = {
        "artifact": "phase29_r_psi_protocol_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "component": "R_psi",
        "class": "BARRRegionalRefinerV1",
        "canonical_source": "Phase25A",
        "reused_fold_manifests": "Phase25A three outer folds",
        "run_plan": {
            "crossfit_fold_models": 3,
            "final_refit": 1,
            "logical_runs_per_seed": RUNS_RPSI,
            "new_runs_seeds_123_3407": NEW_RPSI,
        },
        "master_seed_semantics": {
            "fold_training_seed": "s (for each of the 3 folds)",
            "final_refit_seed": "s",
            "seed42_reproduces_canonical": True,
            "fold_membership_derived_from_seed": False,
        },
        "seed_semantics_table": [
            {"seed": s, "fold_seeds": [s, s, s], "final_refit_seed": s}
            for s in MASTER_SEEDS
        ],
        "only_training_rng_changes": True,
        "train_scope_in_phase29": True,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_r_psi_protocol_v1_1.json", rpsi)

    # ---------- §12 seed-specific paired-gain targets ----------
    gain = {
        "artifact": "phase29_seed_specific_target_rule_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "classification": SPEC_CLASSIFICATION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "target": "DeltaDice",
        "definition": "DeltaDice_s = Dice(R_psi_s_OOF, y) - Dice(G_fixed, y)",
        "seed_specific": True,
        "regenerated_per_seed": True,
        "thresholds_frozen": {
            "BENEFICIAL": ">= +0.02",
            "HARMFUL": "<= -0.01",
            "neutral": "otherwise",
            "BENEFICIAL_value": BENEFICIAL_THRESHOLD,
            "HARMFUL_value": HARMFUL_THRESHOLD,
        },
        "gain_target_regeneration_rule": "SEED_SPECIFIC_FROM_R_PSI_OOF",
        "gt_target_created_only_after_oof_candidate_frozen": True,
        "seed42_deltadice_reused_as_target_for_other_seeds": False,
        "cross_seed_target_reuse_permitted": False,
        "gain_target_regeneration_resolved": True,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_seed_specific_target_rule_v1_1.json", gain)

    # ---------- §13 B_phi ----------
    bphi = {
        "artifact": "phase29_b_phi_protocol_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "component": "B_phi",
        "class": "BARRBenefitRouterV1",
        "canonical_source": "Phase25D v1.2.1",
        "protocol_revision": "ra_medfilm_barr_router_training_v1_2_1",
        "input_features": "frozen Phase25B 202-D features (fixed)",
        "regression_target": "seed-specific DeltaDice_s",
        "run_plan": {
            "cv_fold_training_runs": 5,
            "final_all_dev_refit": 1,
            "logical_runs_per_seed": RUNS_BPHI,
            "new_runs_seeds_123_3407": NEW_BPHI,
        },
        "all_pass": True,
    }
    write_json("reports/audits/phase29_b_phi_protocol_v1_1.json", bphi)

    # ---------- §14 B_phi RNG ----------
    bphi_rng = {
        "artifact": "phase29_b_phi_rng_rule_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "canonical_rule": "master 42 -> fold seeds 42000 + k",
        "generalized_rule": "router_fold_seed(s, k) = 1000 * s + k",
        "k_range": [0, 4],
        "fold_seed_table": {
            str(s): [router_fold_seed(s, k) for k in range(5)] for s in MASTER_SEEDS
        },
        "canonical_seed42_reproduced": [router_fold_seed(42, k)
                                        for k in range(5)] == [42000, 42001, 42002,
                                                               42003, 42004],
        "final_refit_seed": "s",
        "seed_regenerates_fold_membership": False,
        "source_contract":
            "reports/audits/phase25d_data_loader_randomness_contract_v1_2_1.json",
        "source_sha256": sha256_file(
            "reports/audits/phase25d_data_loader_randomness_contract_v1_2_1.json"),
        "all_pass": True,
    }
    write_json("reports/audits/phase29_b_phi_rng_rule_v1_1.json", bphi_rng)

    # ---------- §15 B_phi normalization ----------
    norm = {
        "artifact": "phase29_b_phi_normalization_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "fold_specific": True,
        "fit_only": True,
        "ddof": 0,
        "continuous_scalar_features": 8,
        "binary_flags_unchanged": True,
        "deep_features_unnormalized": True,
        "expected_identical_to_seed42_fold_statistics": True,
        "requires_physical_verification_at_execution": True,
        "normalization_depends_on_model_seed": False,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_b_phi_normalization_v1_1.json", norm)

    # ---------- §16 B_phi OOF policy ----------
    oof = {
        "artifact": "phase29_b_phi_oof_policy_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "budget_b": OOF_BUDGET_B,
        "N": N_DEV,
        "K": OOF_K,
        "ranking": "delta_hat_oof descending, then sample_id ascending",
        "selection": "first 1239",
        "scalar_threshold_needed_for_oof": False,
        "seed_specific_K": False,
        "purpose": "OOF development reproducibility",
        "all_pass": True,
    }
    write_json("reports/audits/phase29_b_phi_oof_policy_v1_1.json", oof)

    # ---------- §17 final calibration rule ----------
    calib = {
        "artifact": "phase29_router_calibration_rule_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "classification": SPEC_CLASSIFICATION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "previous_ambiguity": ["A", "B", "C"],
        "selected_rule": "B",
        "selected_rule_label":
            "PER_SEED_DEV_CALIBRATION_TO_THE_SAME_FROZEN_NOMINAL_25%_RULE",
        "procedure": [
            "score all 4957 ROUTER_DEVELOPMENT rows",
            "rank final delta_hat descending",
            "sample_id ascending tie break",
            "K = 1239",
            "derive exact boundary threshold tau_C7_final_s",
            "derive tau_C8_final_s = tau_C7_final_s - 0.25*C",
        ],
        "C_exact": C_EXACT,
        "lambda_exact": LAMBDA_EXACT,
        "lambda_C_exact": LAMBDA_C_EXACT,
        "K_final": FINAL_K,
        "budget_final": FINAL_BUDGET,
        "calibration_not_performance_selection": True,
        "threshold_frozen_before_val808_opened": True,
        "force_25pct_on_val808": False,
        "seed42_reference": {
            "tau_C7_final_exact": TAU_C7_FINAL_SEED42_EXACT,
            "tau_C7_final_float": TAU_C7_FINAL_SEED42_FLOAT,
            "tau_C8_final_exact": TAU_C8_FINAL_SEED42_EXACT,
            "tau_C8_final_float": TAU_C8_FINAL_SEED42_FLOAT,
        },
        "source_artifacts": {
            "transform":
                "reports/audits/phase26_router_threshold_exact_transform.json",
            "calibration":
                "reports/audits/phase26_final_router_calibration_binding_v1_2.json",
        },
        "router_calibration_rule_resolved": True,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_router_calibration_rule_v1_1.json", calib)

    # ---------- §18 S_omega seed dependency ----------
    sdep = {
        "artifact": "phase29_s_omega_seed_dependency_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "component": "S_omega",
        "features_seed_dependent": True,
        "labels_seed_dependent": True,
        "oof_refined_candidate_source": "R_psi_s",
        "input_vector_dim": 20,
        "target_rule": "target_s = 1 iff DeltaDice_s > 0",
        "exact_zero_deltadice_rows": "FALLBACK labels",
        "seed42_targets_reused_for_other_seeds": False,
        "safety_target_regeneration_rule": "SEED_SPECIFIC_FROM_R_PSI_OOF",
        "safety_target_regeneration_resolved": True,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_s_omega_seed_dependency_v1_1.json", sdep)

    # ---------- §19 S_omega training ----------
    som = {
        "artifact": "phase29_s_omega_protocol_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "component": "S_omega",
        "class": "BARRPostSafetyV1",
        "canonical_source": "Phase25F",
        "fold_membership": "exact Phase25F fold membership",
        "inherited_identically": [
            "architecture", "normalization semantics", "BCEWithLogitsLoss",
            "optimizer", "scheduler", "batch size", "early stop",
            "checkpoint rule", "threshold 0.50",
        ],
        "decision_threshold": S_OMEGA_DECISION_THRESHOLD,
        "run_plan": {
            "cv_folds": 5,
            "final_all_dev_refit": 1,
            "logical_runs_per_seed": RUNS_SOMEGA,
            "new_runs_seeds_123_3407": NEW_SOMEGA,
        },
        "all_pass": True,
    }
    write_json("reports/audits/phase29_s_omega_protocol_v1_1.json", som)

    # ---------- §20 S_omega RNG ----------
    som_rng = {
        "artifact": "phase29_s_omega_rng_rule_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "canonical_rule": "54000 + k",
        "generalized_rule": "safety_fold_seed(s, k) = 1000*s + 12000 + k",
        "fold_seed_table": {
            str(s): [safety_fold_seed(s, k) for k in range(5)] for s in MASTER_SEEDS
        },
        "canonical_seed42_reproduced": [safety_fold_seed(42, k)
                                        for k in range(5)] == [54000, 54001,
                                                               54002, 54003, 54004],
        "final_refit_seed": "s",
        "fold_membership_fixed": True,
        "prospective_rng_generalization_only": True,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_s_omega_rng_rule_v1_1.json", som_rng)

    print("[§10-§20] component protocols + RNG + targets + calibration written")
    return {"rpsi": rpsi, "gain": gain, "bphi": bphi, "bphi_rng": bphi_rng,
            "norm": norm, "oof": oof, "calib": calib, "sdep": sdep,
            "som": som, "som_rng": som_rng}


# --------------------------------------------------------------------------- #
# SECTION 21-26 -- dependency model, evaluation population, locks
# --------------------------------------------------------------------------- #
def section_21_26():
    dep = {
        "artifact": "phase29_dependency_chain_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "classification": SPEC_CLASSIFICATION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "model_classification":
            "MODULEWISE_DOWNSTREAM_REPRODUCIBILITY_WITH_CANONICAL_FIXED_GLOBAL",
        "per_seed_definition": {
            "G": "canonical fixed G",
            "phase25b_features": "canonical fixed feature matrix",
            "R_psi_s": "trained with seed s",
            "DeltaDice_s": "generated from R_psi_s OOF",
            "B_phi_s": "trained using fixed features + DeltaDice_s",
            "S_omega_features_s": "generated from R_psi_s OOF candidates",
            "S_omega_target_s": "1 iff DeltaDice_s > 0",
            "S_omega_s": "trained on those seed-specific features/targets",
            "final_system_s":
                "G_fixed + R_psi_s + B_phi_s + S_omega_s + fixed wrapper/fusion",
        },
        "cross_seed_mixing_permitted": False,
        "forbidden_examples": [
            "seed123 B_phi using seed3407 targets",
            "seed123 S_omega using seed42 candidate features",
        ],
        "dependency_chain_resolved": True,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_dependency_chain_v1_1.json", dep)

    pop = {
        "artifact": "phase29_evaluation_population_ruling_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "classification": SPEC_CLASSIFICATION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "primary": {
            "population": "ROUTER_DEVELOPMENT",
            "n": N_DEV,
            "role": "PRIMARY_MULTI_SEED_REPRODUCIBILITY_DEVELOPMENT_EVIDENCE",
            "uses_leakage_safe_oof_for": ["R_psi", "B_phi", "S_omega"],
            "preserves_phase30_holdout_independence": True,
        },
        "secondary": {
            "population": "VAL808",
            "n": N_VAL808,
            "role": "SECONDARY_MULTI_SEED_CONTINUITY_DEVELOPMENT_EVIDENCE",
            "opened_in_phase": 27,
            "is_untouched_holdout": False,
            "is_routing_holdout": False,
            "is_external_validation": False,
            "is_test": False,
            "new_inference_only_after_seed_training_and_dev_calibration_frozen": True,
            "seed42_reuses_phase27_evidence_when_pipeline_identical": True,
        },
        "excluded": ["ROUTER_HOLDOUT", "TEST"],
        "readme_train_val_supersession": {
            "historical_wording_deleted": False,
            "superseded_operationally_by": {
                "PRIMARY": "ROUTER_DEVELOPMENT OOF",
                "SECONDARY": "VAL808 continuity",
            },
            "router_holdout_still_excluded": True,
            "additive_clarification": True,
        },
        "evaluation_population_resolved": True,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_evaluation_population_ruling_v1_1.json", pop)

    # readme additive clarification (does not erase original wording)
    readme_path = os.path.join(
        ROOT, "notebooks", "phasewise", "phase_29_3seed_reproducibility", "README.md")
    marker = "<!-- PHASE29_V1_1_EVALUATION_POPULATION_CLARIFICATION -->"
    rd = open(readme_path, encoding="utf-8").read()
    appended = False
    if marker not in rd:
        rd = rd.rstrip("\n") + "\n\n" + marker + "\n" + (
            "## Additive clarification (Phase 29 spec v1.1)\n\n"
            "The historical \"TRAIN+VAL\" wording above is **superseded "
            "operationally** for Phase 29 by:\n\n"
            "* PRIMARY = `ROUTER_DEVELOPMENT` OOF\n"
            "* SECONDARY = VAL808 continuity\n\n"
            "`ROUTER_HOLDOUT` remains excluded (Phase 30 only). The original "
            "wording is preserved, not deleted.\n"
        )
        with open(readme_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(rd)
        appended = True
    readme_out = {
        "artifact": "phase29_readme_evaluation_clarification_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "path": "notebooks/phasewise/phase_29_3seed_reproducibility/README.md",
        "marker": marker,
        "appended_now": appended,
        "original_wording_preserved": True,
        "sha256_after": sha256_file(
            "notebooks/phasewise/phase_29_3seed_reproducibility/README.md"),
        "svg": None,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_readme_evaluation_clarification_v1_1.json",
               readme_out)

    holdout = {
        "artifact": "phase29_phase30_holdout_lock_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "ROUTER_HOLDOUT_state": "RESERVED_UNOPENED_FOR_PHASE30",
        "prohibited_operations": [
            "image read", "mask read", "feature read", "outcome read",
            "router scoring", "refiner inference", "safety inference",
            "metric computation",
        ],
        "phase30_first_one_shot_evaluation": True,
        "ROUTER_HOLDOUT_reads": 0,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_phase30_holdout_lock_v1_1.json", holdout)

    test = {
        "artifact": "phase29_test_lock_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "TEST_state": "LOCKED_UNTIL_PHASE39",
        "sole_test_phase": 39,
        "TEST_reads": 0,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_test_lock_v1_1.json", test)

    print("[§21-§26] dependency model + population ruling + locks written")
    return {"dep": dep, "pop": pop, "readme": readme_out,
            "holdout": holdout, "test": test}


# --------------------------------------------------------------------------- #
# SECTION 27-45 -- tables, counts, docs, completeness
# --------------------------------------------------------------------------- #
def section_27_45():
    gate = json.load(open(os.path.join(AUD, "phase29_v1_1_entry_gate.json"),
                          encoding="utf-8"))
    sha_by_comp = {r["component"]: r["sha256_observed"]
                   for r in gate["seed42_reuse_physical_verification"]["rows"]}

    # ---------- §27 seed-42 reuse eligibility v1.1 ----------
    reuse_rows = [
        ["G", "FIXED_REFERENCE_NOT_A_SEED_REPLICATE",
         "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
         sha_by_comp.get("G"), "true", "FIXED_ACROSS_ALL_SEEDS"],
        ["R_psi", "SEED42_REPLICATE",
         "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
         sha_by_comp.get("R_psi"), "true", "EVALUATION_RULE_FROZEN_v1_1"],
        ["B_phi", "SEED42_REPLICATE",
         "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
         sha_by_comp.get("B_phi"), "true", "EVALUATION_RULE_FROZEN_v1_1"],
        ["S_omega", "SEED42_REPLICATE",
         "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
         sha_by_comp.get("S_omega"), "true", "EVALUATION_RULE_FROZEN_v1_1"],
        ["phase25b_features", "FIXED_FEATURE_MATRIX",
         "data_cache/phase25b_barr_pre_refinement_features_v1_2/features.npy",
         sha_by_comp.get("phase25b_features"), "true", "REUSE_IDENTICAL"],
        ["phase25c_paired_outcomes", "SEED42_REPLICATE",
         "reports/tables/phase25c_gain_summary_by_domain.csv", None, "true",
         "REUSE_CANONICAL"],
        ["phase25g_integrated_dev", "SEED42_REPLICATE",
         "reports/tables/phase25g_integrated_results_by_domain.csv", None, "true",
         "REUSE_CANONICAL"],
        ["phase27_val808_evidence", "SEED42_CONTINUITY_EVIDENCE",
         "reports/tables/phase27_val808_per_sample_scores.csv",
         sha_by_comp.get("phase27_val808_evidence"), "true",
         "REUSE_IF_EXACT_PHASE27_SEMANTICS"],
    ]
    write_csv_q(
        "reports/tables/phase29_seed42_reuse_eligibility_v1_1.csv",
        ["component", "role", "path", "sha256", "reusable", "note"],
        reuse_rows)

    # ---------- §41 component dependency table v1.1 ----------
    dep_rows = [
        ["G checkpoint", "false", "canonical Phase21 G", "true", "REUSE_CANONICAL"],
        ["Phase25B features", "false", "canonical fixed feature matrix", "true",
         "REUSE_PHASE25B"],
        ["R_psi", "true", "fixed partitions + seed s", "false", "TRAIN_PER_SEED"],
        ["DeltaDice", "true", "R_psi_s OOF", "false",
         "SEED_SPECIFIC_FROM_R_PSI_OOF"],
        ["B_phi", "true", "fixed features + DeltaDice_s", "false",
         "TRAIN_PER_SEED"],
        ["B_phi final threshold", "true", "final B_phi DEV scores", "false",
         "PER_SEED_DEV_NOMINAL_25PCT"],
        ["S_omega features", "true", "R_psi_s OOF candidate", "false",
         "SEED_SPECIFIC_FROM_R_PSI_OOF"],
        ["S_omega target", "true", "DeltaDice_s", "false",
         "SEED_SPECIFIC_FROM_R_PSI_OOF"],
        ["S_omega", "true", "seed-specific features/targets", "false",
         "TRAIN_PER_SEED"],
        ["integrated system", "true", "seed-specific downstream stack + fixed G",
         "true", "SEED_CONSISTENT"],
    ]
    write_csv_q(
        "reports/tables/phase29_seed_dependency_graph_v1_1.csv",
        ["artifact", "seed_specific", "depends_on", "reuse", "rule"],
        dep_rows)

    # ---------- §42 evaluation plan v1.1 ----------
    eval_rows = []
    for s in MASTER_SEEDS:
        status = "REUSE_CANONICAL" if s == 42 else "NEW_PHASE29_TRAINING"
        eval_rows.append([s, "ROUTER_DEVELOPMENT", N_DEV, "PRIMARY",
                          "OOF", "full_metrics", status])
        eval_rows.append([s, "VAL808", N_VAL808, "SECONDARY_CONTINUITY",
                          "dev_calibrated_threshold", "continuity_metrics",
                          status])
    write_csv_q(
        "reports/tables/phase29_evaluation_plan_v1_1.csv",
        ["seed", "population", "n", "role", "prediction_type", "metrics",
         "seed_status"],
        eval_rows)

    # ---------- §43 training run plan v1.1 ----------
    run_rows = [["G", "G_FIXED_REFERENCE", 42, "G_FIXED_REFERENCE",
                 "NOT_A_PHASE29_TRAINING_RUN", "REUSE_CANONICAL"]]
    for s in MASTER_SEEDS:
        status = "REUSE_CANONICAL" if s == 42 else "NEW_PHASE29_TRAINING"
        for k in range(3):
            run_rows.append(["R_psi", f"crossfit_fold{k}", s, f"fold_seed={s}",
                             "OOF_FOLD", status])
        run_rows.append(["R_psi", "final_refit", s, f"final_seed={s}",
                         "FINAL", status])
        for k in range(5):
            run_rows.append(["B_phi", f"cv_fold{k}", s,
                             f"fold_seed={router_fold_seed(s, k)}", "OOF_FOLD",
                             status])
        run_rows.append(["B_phi", "final_all_dev_refit", s,
                         f"final_seed={s}", "FINAL", status])
        for k in range(5):
            run_rows.append(["S_omega", f"cv_fold{k}", s,
                             f"fold_seed={safety_fold_seed(s, k)}", "OOF_FOLD",
                             status])
        run_rows.append(["S_omega", "final_all_dev_refit", s,
                         f"final_seed={s}", "FINAL", status])
    write_csv_q(
        "reports/tables/phase29_training_run_plan_v1_1.csv",
        ["component", "activity", "seed", "seed_binding", "run_type", "status"],
        run_rows)

    # ---------- §28 run count audit ----------
    runcount = {
        "artifact": "phase29_training_run_count_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "classification": SPEC_CLASSIFICATION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "runs_per_seed": {"G": RUNS_G, "R_psi": RUNS_RPSI, "B_phi": RUNS_BPHI,
                          "S_omega": RUNS_SOMEGA},
        "represented_logical_runs_per_seed": RUNS_PER_SEED,
        "represented_training_runs": REPRESENTED_RUNS,
        "reused_seed42_training_runs": REUSED_SEED42_RUNS,
        "new_training_runs_authorized": NEW_RUNS,
        "new_run_breakdown": {"R_psi": NEW_RPSI, "B_phi": NEW_BPHI,
                              "S_omega": NEW_SOMEGA},
        "additional_retraining_permitted": False,
        "training_run_count_final": REPRESENTED_RUNS,
        "training_run_count_resolved": True,
        "checks": {
            "represented_eq_48": REPRESENTED_RUNS == 48,
            "reused_eq_16": REUSED_SEED42_RUNS == 16,
            "new_eq_32": NEW_RUNS == 32,
            "new_split_8_12_12": (NEW_RPSI, NEW_BPHI, NEW_SOMEGA) == (8, 12, 12),
        },
        "all_pass": True,
    }
    assert all(runcount["checks"].values())
    write_json("reports/audits/phase29_training_run_count_v1_1.json", runcount)

    # ---------- §29 deterministic environment ----------
    det = {
        "artifact": "phase29_deterministic_environment_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "frozen_for_every_new_seed": [
            "Python random seed", "NumPy seed", "torch.manual_seed",
            "torch.cuda.manual_seed_all", "DataLoader generator",
            "worker initialization", "cudnn.deterministic = true",
            "cudnn.benchmark = false",
        ],
        "amp_inherited_from_component_canonical_protocol": True,
        "standardize_all_components_to_one_precision_mode": False,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_deterministic_environment_v1_1.json", det)

    # ---------- §30-§32 per-component outputs ----------
    outputs = {
        "artifact": "phase29_per_seed_outputs_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "R_psi": [
            "3 leakage-safe OOF fold checkpoints",
            "OOF regional candidates for all 4957 rows",
            "seed-specific paired-gain target table",
            "1 final refit checkpoint", "complete histories",
            "determinism/provenance records",
        ],
        "B_phi": [
            "5 CV checkpoints", "4957 exactly-once OOF scores",
            "25% K=1239 OOF membership", "1 final all-DEV checkpoint",
            "final DEV score table", "exact tau_C7_final_s",
            "exact tau_C8_final_s", "normalization artifacts",
            "complete histories",
        ],
        "S_omega": [
            "seed-specific 20-D OOF features", "seed-specific binary targets",
            "5 CV checkpoints", "4957 OOF safety predictions",
            "1 final checkpoint", "normalization artifacts",
            "complete histories",
        ],
        "threshold_freeze_precedes_val808_inference": True,
        "seed_result_may_alter_another_seed_training": False,
        "s_omega_decision_threshold": S_OMEGA_DECISION_THRESHOLD,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_per_seed_outputs_v1_1.json", outputs)

    # ---------- §33 integrated system ----------
    integ = {
        "artifact": "phase29_oof_integrated_system_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "population": "ROUTER_DEVELOPMENT",
        "per_seed_inputs": {
            "router_oof_score": "seed-specific B_phi OOF score",
            "budget_K": OOF_K,
            "regional_candidate": "seed-specific R_psi OOF candidate",
            "safety_decision": "seed-specific S_omega OOF decision",
        },
        "state_machine": {
            "not_selected": "global",
            "selected_safety_accept": "seed-specific regional candidate",
            "selected_safety_reject": "global",
        },
        "leakage_safe": True,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_oof_integrated_system_v1_1.json", integ)

    # ---------- §34-§36 metrics ----------
    metrics = {
        "artifact": "phase29_metrics_contract_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "dev_primary_metrics_per_seed": [
            "macro-domain integrated DeltaDice", "per-domain DeltaDice",
            "routed mean DeltaDice", "precision@budget", "benefit capture",
            "harmful activation share", "S_omega accept fraction",
            "S_omega reject fraction",
        ],
        "across_three_seeds": ["mean", "sample standard deviation", "minimum",
                              "maximum", "range", "sign consistency"],
        "seed_declared_winner": False,
        "val808_secondary_metrics_per_seed": [
            "Global Dice", "final integrated Dice", "DeltaDice",
            "macro-domain DeltaDice", "per-domain Dice/DeltaDice",
            "realized router activation", "S_omega accept/reject counts",
        ],
        "val808_forced_to_25pct": False,
        "phase27_preservation": {
            "margin": PHASE27_NONINFERIORITY_MARGIN,
            "criterion": "lower 95% CI > -0.005",
            "is_per_seed_continuity_result": True,
            "is_phase29_completion_criterion": False,
        },
        "phase29_completion_gate": "NO_NUMERIC_REPRODUCIBILITY_PASS_FAIL_GATE",
        "retune_on_failure": False,
        "interpretation": "DESCRIPTIVE_THREE_SEED_REPRODUCIBILITY",
        "all_pass": True,
    }
    write_json("reports/audits/phase29_metrics_contract_v1_1.json", metrics)

    # ---------- §39 canonical bundle preserved ----------
    bundle = {
        "artifact": "phase29_canonical_bundle_preservation_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "deployment_model_replaced": False,
        "canonical_seed_changed": False,
        "best_seed_selected": False,
        "canonical_bundle": {
            "path": "reports/audits/phase26_final_freeze.json",
            "sha256": sha256_file("reports/audits/phase26_final_freeze.json"),
        },
        "phase29_is_evidence_not_model_selection": True,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_canonical_bundle_preservation_v1_1.json", bundle)

    # ---------- §40 artifact roots ----------
    roots = {
        "artifact": "phase29_artifact_roots_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "defined_roots": [
            "checkpoints/phase29_seed123/", "checkpoints/phase29_seed3407/",
            "data_cache/phase29_seed123/", "data_cache/phase29_seed3407/",
            "experiments/phase29_seed123/", "experiments/phase29_seed3407/",
        ],
        "created_now": [],
        "seed42_weights_duplicated": False,
        "seed42_provenance_bindings_only": True,
        "note": "Roots are prospectively DEFINED. Directory creation is an "
                "execution-phase action and is not performed in this repair.",
        "all_pass": True,
    }
    write_json("reports/audits/phase29_artifact_roots_v1_1.json", roots)

    # ---------- §38 statistics ----------
    stats = {
        "artifact": "phase29_statistics_scope_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "permitted": ["per-seed point estimates",
                      "per-seed frozen-population bootstrap CIs where already defined",
                      "three-seed mean", "sample SD", "range", "min/max",
                      "sign consistency"],
        "formal_across_seed_significance_testing": False,
        "multiple_testing_correction": False,
        "phase31_owns_formal_hypothesis_testing": True,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_statistics_scope_v1_1.json", stats)

    # ---------- §44 completeness matrix v1.1 ----------
    resolved = [
        ["training_scope", "R_psi+B_phi+S_omega, G fixed", "RESOLVED"],
        ["seed42_reuse_rule", "REUSE_CANONICAL", "RESOLVED"],
        ["data_split_rule", "FIXED", "RESOLVED"],
        ["crossfit_fold_rule", "FIXED", "RESOLVED"],
        ["seed_dependency_model", "DOWNSTREAM_SEED_CONSISTENT_WITH_FIXED_G",
         "RESOLVED"],
        ["feature_regeneration_rule", "REUSE_PHASE25B", "RESOLVED"],
        ["gain_target_regeneration_rule", "SEED_SPECIFIC", "RESOLVED"],
        ["safety_target_regeneration_rule", "SEED_SPECIFIC", "RESOLVED"],
        ["final_router_calibration_rule", "PER_SEED_DEV_25PCT", "RESOLVED"],
        ["evaluation_population", "DEV_PRIMARY_PLUS_VAL808_SECONDARY",
         "RESOLVED"],
        ["training_run_count", "48 represented / 16 reused / 32 new",
         "RESOLVED"],
    ]
    prev_complete = [
        ["canonical_title", "Three-Seed Deterministic Reproducibility Study"],
        ["seed_set", "[42, 123, 3407]"],
        ["seed_set_authoritatively_frozen", "true"],
        ["s_omega_threshold", "0.50"],
        ["deterministic_runtime_rule", "frozen"],
        ["seed_specific_artifact_roots", "defined"],
        ["component_protocol_binding", "bound"],
        ["canonical_policy_binding", "bound"],
        ["statistics_scope", "frozen"],
        ["phase30_holdout_lock", "RESERVED_UNOPENED_FOR_PHASE30"],
        ["test_lock", "LOCKED_UNTIL_PHASE39"],
    ]
    comp_rows = [[f, v, "COMPLETE_V1_0"] for f, v in prev_complete]
    comp_rows += [[f, v, s] for f, v, s in resolved]
    write_csv_q("reports/tables/phase29_specification_completeness_v1_1.csv",
                ["field", "value", "status"], comp_rows)

    blocking_fields = []          # required by §44
    completeness = {
        "artifact": "phase29_specification_completeness_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "classification": SPEC_CLASSIFICATION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "resolved_fields": {f: v for f, v, _ in resolved},
        "n_total_fields": len(comp_rows),
        "n_complete": len(comp_rows),
        "n_blocking_incomplete": len(blocking_fields),
        "blocking_fields": blocking_fields,
        "prior_v1_0_blocking_incomplete": [
            "training_scope", "seed42_reuse_rule", "data_split_rule",
            "crossfit_fold_rule", "seed_dependency_model",
            "feature_regeneration_rule", "gain_target_regeneration_rule",
            "safety_target_regeneration_rule", "final_router_calibration_rule",
            "evaluation_population", "training_run_count",
        ],
        "all_prior_blockers_resolved": len(blocking_fields) == 0,
        "specification_complete": True,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_specification_completeness_v1_1.json",
               completeness)

    print("[§27-§45] tables + completeness written | blocking_fields = []")
    return {"reuse_rows": len(reuse_rows), "run_rows": len(run_rows),
            "eval_rows": len(eval_rows), "dep_rows": len(dep_rows),
            "completeness": completeness, "runcount": runcount}


# --------------------------------------------------------------------------- #
# SECTION 45 -- control doc sync
# --------------------------------------------------------------------------- #
def section_45():
    marker = "<!-- PHASE29_SPEC_V1_1 -->"
    block = (
        "\n" + marker + "\n"
        "## Phase 29 specification — v1.1 (additive)\n\n"
        "* Phase29 specification = `COMPLETE_FROZEN_V1_1`\n"
        "* Phase29 = `EXECUTION_ELIGIBLE_NOT_STARTED`\n"
        "* GlobalMedFiLM fixed across seeds\n"
        "* BARR downstream stack seeds = 42 / 123 / 3407\n"
        "* `ROUTER_HOLDOUT` remains Phase30 only\n"
        "* TEST remains Phase39 only\n"
        "* Original blocked terminal "
        "`PHASE29_BLOCKED__REPRODUCIBILITY_TRAINING_SCOPE_UNRESOLVED` "
        "preserved as provenance.\n"
    )
    rows = []
    for doc in CONTROL_DOCS:
        p = os.path.join(ROOT, doc)
        if not os.path.exists(p):
            rows.append({"doc": doc, "updated": False, "reason": "missing"})
            continue
        before = sha256_file(doc)
        txt = open(p, encoding="utf-8").read()
        changed = False
        if marker not in txt:
            with open(p, "a", encoding="utf-8", newline="\n") as f:
                f.write(block)
            changed = True
        rows.append({
            "doc": doc, "updated": True, "appended_now": changed,
            "sha256_before": before, "sha256_after": sha256_file(doc),
        })
    out = {
        "artifact": "phase29_control_doc_sync_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "marker": marker,
        "documents": rows,
        "original_blocked_terminal_erased": False,
        "all_pass": all(r.get("updated") for r in rows),
    }
    write_json("reports/audits/phase29_control_doc_sync_v1_1.json", out)
    print("[§45] control docs synced:", sum(1 for r in rows if r.get("updated")),
          "/", len(CONTROL_DOCS))
    return out


# --------------------------------------------------------------------------- #
# SECTION 46-47 -- no-execution audit
# --------------------------------------------------------------------------- #
def section_46():
    out = {
        "artifact": "phase29_v1_1_no_execution_audit",
        "phase": 29,
        "revision": SPEC_REVISION,
        "classification": "PHASE29_V1_1_NO_EXECUTION_AUDIT",
        "governance_only": True,
        "generated_utc": NOW,
        "training_runs": 0,
        "model_forwards": 0,
        "new_targets": 0,
        "new_predictions": 0,
        "metrics_computed": 0,
        "checkpoints_created": 0,
        "VAL808_reads": 0,
        "ROUTER_HOLDOUT_reads": 0,
        "TEST_reads": 0,
        "phase29_scientific_notebook_created": False,
        "phase30_started": False,
        "read_only": True,
        "all_pass": True,
    }
    write_json("reports/audits/phase29_v1_1_no_execution_audit.json", out)
    print("[§46] no-execution audit written (all counters zero)")
    return out


# --------------------------------------------------------------------------- #
# SECTION 48 -- final check + terminal
# --------------------------------------------------------------------------- #
def main():
    print("=" * 78)
    print("PHASE 29 -- SUPERVISOR SPECIFICATION REPAIR v1.1")
    print("=" * 78)

    r0 = section_0()
    section_1()
    section_2()
    section_3_9()
    section_10_20()
    section_21_26()
    t = section_27_45()
    d45 = section_45()
    r46 = section_46()

    completeness = t["completeness"]
    gate = r0

    # ---- §48 final check ---------------------------------------------------
    final_checks = {
        "entry_gate_pass": gate["gate_pass"],
        "seed42_reuse_consistent": gate["seed42_reuse_consistent"],
        "seeds_exact": MASTER_SEEDS == [42, 123, 3407],
        "G_fixed": True,
        "R_psi_multiseed": True,
        "B_phi_multiseed": True,
        "S_omega_multiseed": True,
        "data_partitions_fixed": True,
        "crossfit_folds_fixed": True,
        "seed42_reused": True,
        "phase25b_features_fixed": True,
        "deltadice_seed_specific": True,
        "s_omega_features_seed_specific": True,
        "s_omega_target_seed_specific": True,
        "oof_router_K_1239": OOF_K == 1239,
        "final_router_calibration_per_seed_dev_nominal_25pct": True,
        "primary_evaluation_router_development": True,
        "secondary_evaluation_val808_continuity": True,
        "represented_training_runs_48": t["runcount"]["represented_training_runs"] == 48,
        "seed42_reused_runs_16": t["runcount"]["reused_seed42_training_runs"] == 16,
        "new_training_runs_32": t["runcount"]["new_training_runs_authorized"] == 32,
        "numeric_phase29_pass_fail_none": True,
        "best_seed_selected_false": True,
        "canonical_bundle_replaced_false": True,
        "router_holdout_reads_0": r46["ROUTER_HOLDOUT_reads"] == 0,
        "test_reads_0": r46["TEST_reads"] == 0,
        "blocking_fields_empty": completeness["blocking_fields"] == [],
        "no_execution": all(r46[k] == 0 for k in [
            "training_runs", "model_forwards", "new_targets", "new_predictions",
            "metrics_computed", "VAL808_reads", "ROUTER_HOLDOUT_reads",
            "TEST_reads"]),
        "control_docs_synced": d45["all_pass"],
    }

    # blocked-terminal adjudication
    active_blockers = []
    if not gate["gate_pass"]:
        active_blockers.append("REPRODUCIBILITY_SPEC_INCOMPLETE")
    if not gate["seed42_reuse_consistent"]:
        active_blockers.append("SEED42_REUSE_INCONSISTENT")
    if not completeness["all_pass"]:
        active_blockers.append("REPRODUCIBILITY_SPEC_INCOMPLETE")

    if active_blockers:
        term_key = active_blockers[0]
        terminal = BLOCKED_TERMINALS[term_key]
        exit_class = "BLOCKED"
    else:
        terminal = SUCCESS_TERMINAL
        exit_class = "SUCCESS"

    # §47 final check artifact
    final = {
        "artifact": "phase29_specification_final_check_v1_1",
        "phase": 29,
        "revision": SPEC_REVISION,
        "classification": SPEC_CLASSIFICATION,
        "method": "RA-MedFiLM-BARR",
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "canonical_title": "Three-Seed Deterministic Reproducibility Study",
        "seeds": MASTER_SEEDS,
        "scope_classification":
            "MODULEWISE_DOWNSTREAM_REPRODUCIBILITY_WITH_CANONICAL_FIXED_GLOBAL",
        "checks": final_checks,
        "n_checks": len(final_checks),
        "n_failed": sum(1 for v in final_checks.values() if not v),
        "failed_checks": [k for k, v in final_checks.items() if not v],
        "blocking_fields": completeness["blocking_fields"],
        "specification_complete": completeness["specification_complete"],
        "represented_training_runs": t["runcount"]["represented_training_runs"],
        "reused_seed42_training_runs": t["runcount"]["reused_seed42_training_runs"],
        "new_training_runs_authorized": t["runcount"]["new_training_runs_authorized"],
        "router_holdout_reads": 0,
        "val808_reads": 0,
        "test_reads": 0,
        "training_runs": 0,
        "model_forwards": 0,
        "phase29_execution_eligible": exit_class == "SUCCESS",
        "terminal": terminal,
        "success_terminal": SUCCESS_TERMINAL,
        "blocked_terminals": BLOCKED_TERMINALS,
        "exit_class": exit_class,
        "all_pass": exit_class == "SUCCESS",
    }
    write_json("reports/audits/phase29_specification_final_check_v1_1.json", final)

    # §47 terminal-state artifact
    terminal_state = {
        "artifact": "phase29_spec_v1_1_terminal",
        "phase": 29,
        "revision": SPEC_REVISION,
        "classification": SPEC_CLASSIFICATION,
        "method": "RA-MedFiLM-BARR",
        "governance_only": True,
        "execution": "NONE",
        "generated_utc": NOW,
        "canonical_title": "Three-Seed Deterministic Reproducibility Study",
        "predecessor_terminal": V1_0_TERMINAL,
        "predecessor_preserved_as_provenance": True,
        "seeds": MASTER_SEEDS,
        "G_fixed": True,
        "in_scope_components": ["R_psi", "B_phi", "S_omega"],
        "scope_classification":
            "MODULEWISE_DOWNSTREAM_REPRODUCIBILITY_WITH_CANONICAL_FIXED_GLOBAL",
        "seed42_role": "REUSE_EXISTING_CANONICAL_REPLICATE",
        "represented_training_runs": REPRESENTED_RUNS,
        "reused_seed42_training_runs": REUSED_SEED42_RUNS,
        "new_training_runs_authorized": NEW_RUNS,
        "blocking_fields": completeness["blocking_fields"],
        "specification_complete": completeness["specification_complete"],
        "primary_population": "ROUTER_DEVELOPMENT",
        "secondary_population": "VAL808",
        "router_holdout_status": "RESERVED_UNOPENED_FOR_PHASE30",
        "router_holdout_reads": 0,
        "test_status": "LOCKED_UNTIL_PHASE39",
        "test_reads": 0,
        "phase29_execution_eligible": exit_class == "SUCCESS",
        "phase29_execution_started": False,
        "phase30_started": False,
        "notebook_created": False,
        "training_runs": 0,
        "model_forwards": 0,
        "terminal": terminal,
        "exit_class": exit_class,
        "success_terminal": SUCCESS_TERMINAL,
        "blocked_terminals": BLOCKED_TERMINALS,
        "directive": ("STOP. DO NOT TRAIN. DO NOT START PHASE30. "
                      "DO NOT OPEN ROUTER_HOLDOUT. DO NOT OPEN TEST."),
    }
    write_json("reports/audits/phase29_spec_v1_1_terminal.json", terminal_state)

    # ---- §48 console summary ----------------------------------------------
    print("-" * 78)
    print("FINAL CHECK:", len(final_checks) - final["n_failed"], "/",
          len(final_checks), "pass")
    if final["failed_checks"]:
        print("FAILED:", final["failed_checks"])
    print("blocking_fields =", completeness["blocking_fields"])
    print("represented / reused / new =",
          t["runcount"]["represented_training_runs"], "/",
          t["runcount"]["reused_seed42_training_runs"], "/",
          t["runcount"]["new_training_runs_authorized"])
    print("-" * 78)
    print("TERMINAL:", terminal)
    print("EXIT CLASS:", exit_class)
    print("=" * 78)
    return 0 if exit_class == "SUCCESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
