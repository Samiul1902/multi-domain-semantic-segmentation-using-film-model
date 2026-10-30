#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Generate the v1.0h execution harness deterministically from the frozen v1.0g source.

SOURCE + GOVERNANCE ONLY. This generator performs NO model construction, NO checkpoint
deserialization, NO forward, NO autograd, NO Grad-CAM, NO router attribution.

It applies an EXACT, ANCHOR-COUNTED set of textual transforms to
`scripts/analysis/phase35_interpretability_execution_v1_0g.py` (verified by SHA-256 before
writing) and fails closed if any anchor's occurrence count differs from its declared count.

The resulting v1.0h harness:
  * reinstates the SINGLE-OWNERSHIP counter model - the legacy V0C store is the authoritative
    store for inherited execution counters, and it is aliased, NOT copied;
  * uses a dedicated v1.0h EXTENSION store for the FOUR post-v1.0c counters only;
  * merges the live legacy store with the extension store at report time, failing on any
    duplicate or unexpected ownership;
  * contains a FULL 35-key expected table (including all 8 protected-data keys at 0);
  * enforces EXACT keyset equality (set equality AND both lengths AND exact values);
  * fails closed on nonzero counter baselines BEFORE model construction;
  * emits unambiguous terminal reporting fields and NEVER an unqualified ``all_pass = true``
    for a blocked smoke.
"""
from __future__ import annotations

import hashlib
import sys
from collections import OrderedDict
from pathlib import Path

ROOT = Path(r"D://Softfors//jup")
SRC = ROOT / "scripts" / "analysis" / "phase35_interpretability_execution_v1_0g.py"
DST = ROOT / "scripts" / "analysis" / "phase35_interpretability_execution_v1_0h.py"

V1_0G_EXPECTED_SHA = "88456e46c94e53d45b10d864d9dbcd38eb773d7dd441441def9e6f221a0c9be3"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# --------------------------------------------------------------------------- #
# Transforms: (anchor, replacement, expected_occurrences)
# --------------------------------------------------------------------------- #

T1_OLD = '''Classification: PRE_EXECUTION_ACTUAL_LOGITS_EMPTY_MASK_OBSERVABILITY_IMPLEMENTATION_AMENDMENT__
                NO_SCIENTIFIC_PROTOCOL_CHANGE
Revision: ra_medfilm_barr_phase35_interpretability_v1_0g'''

T1_NEW = '''Classification: PRE_EXECUTION_SYNTHETIC_SMOKE_COUNTER_STORE_AND_EXPECTED_CONTRACT_REPAIR__
                NO_SCIENTIFIC_PROTOCOL_CHANGE
Revision: ra_medfilm_barr_phase35_interpretability_v1_0h

v1.0h repairs the COUNTER-STORE OWNERSHIP / AGGREGATION DIVERGENCE that correctly blocked the first
v1.0g smoke (`phase35_synthetic_smoke_terminal_v1_0g.json`, `f4ae9175...`), as recorded in
`phase35_v1_0g_counter_store_contract_defect_v1_0h.json`:

  v1.0g took a SHALLOW COPY of the frozen v1.0c counter store
  (`SMOKE_COUNTERS = OrderedDict(V0C.SMOKE_COUNTERS)`), whereas the frozen v1.0d inherited it as an
  OBJECT ALIAS (`V0D.SMOKE_COUNTERS = V0C.SMOKE_COUNTERS`). The delegated router writer
  (`V0C.smoke_router`, in the frozen v1.0c module) and the inherited alias writer
  (`V0D.smoke_synthetic_target_mask_rank2`) therefore mutated the LIVE v1.0c store, while v1.0g
  reported its disconnected copy. Six rows diverged: the five router counters and the alias
  `synthetic_smoke_target_masks`.

WHAT CHANGES (counter bookkeeping ONLY)
  * SINGLE-OWNERSHIP MODEL: the legacy store `V0C.SMOKE_COUNTERS` remains the authoritative store for
    all inherited v1.0c/v1.0d execution counters. v1.0h aliases it - it does NOT copy it. The router
    writer's store and the v1.0h reported store are the SAME object.
  * A dedicated v1.0h EXTENSION store `SMOKE_COUNTERS_EXT` owns ONLY the four post-v1.0c counters:
    `primary_synthetic_target_masks`, `actual_logits_empty_mask_helper_checks`,
    `additional_G_forwards_for_empty_mask`, `additional_autograd_calls_for_empty_mask`.
  * At report time the canonical observed counters are an EXACT MERGE of the live legacy store and the
    extension store, which FAILS on any duplicate/unexpected ownership.
  * PRIMARY MASK / ALIAS: the primary helper invokes the frozen v1.0d mask producer exactly once (its
    inherited alias increment on the live legacy store occurs exactly once) and increments
    `primary_synthetic_target_masks` exactly once in the extension store. The alias lives in the
    legacy store and equals the primary by construction.
  * The ACTUAL-LOGITS empty-mask helper increments ONLY `actual_logits_empty_mask_helper_checks`, and
    NEVER the primary counter or the alias.
  * A FULL 35-key expected table is frozen, including all 8 protected-data keys at 0.
  * EXACT keyset validation: `set(observed) == set(expected)`, `len(observed) == len(expected) == 35`,
    and exact value equality - emitted as three SEPARATE booleans.
  * Firewall zero-baseline gate: every legacy and extension counter must start at 0 BEFORE any model
    construction, and any nonzero value fails closed (a reused interpreter must not hide prior work).
  * Unambiguous terminal reporting: `artifact_generation_pass`, `smoke_success`,
    `counter_contract_pass`, `scientific_interface_checks_pass`; an unqualified `all_pass = true` is
    NEVER emitted for a blocked smoke.

WHAT DOES NOT CHANGE (frozen scientific intent; §J/§K)
  * every model, numerical, interface, protected-data, and immutability behaviour of v1.0f/v1.0g is
    inherited verbatim; the Grad-CAM mathematics, eight finite guards, alpha/ReLU/bilinear/
    align_corners=False/min-max normalization, atol=1e-7 / rtol=0 comparison, direct parameter
    `.grad` audit, router and FiLM semantics, and read guards are untouched.'''

T2 = (
    "GRADCAM_GRADIENT_IMPL = \"gradcam_gradient_enabled_numerically_guarded_v1_0f\"",
    "GRADCAM_GRADIENT_IMPL = \"gradcam_gradient_enabled_numerically_guarded_v1_0f\"\n"
    "V1_0H_LEGACY_COUNTER_OWNER_MODULE = \"phase35_interpretability_execution_v1_0c\"\n"
    "V1_0H_EXTENSION_COUNTER_KEYS = (\n"
    "    \"primary_synthetic_target_masks\",\n"
    "    \"actual_logits_empty_mask_helper_checks\",\n"
    "    \"additional_G_forwards_for_empty_mask\",\n"
    "    \"additional_autograd_calls_for_empty_mask\",\n"
    ")",
)

T3_OLD = '''# --------------------------------------------------------------------------- #
# smoke counters (v1.0g COUNTER-CONTRACT SEPARATION)
#
# The frozen v1.0c store is COPIED (not mutated) so that the three mask-related counters can be
# declared with semantically SEPARATE keys:
#   * primary_synthetic_target_masks            -> PRIMARY synthetic target masks   (expected 1)
#   * synthetic_smoke_target_masks              -> backwards-compatible ALIAS        (expected 1)
#   * actual_logits_empty_mask_helper_checks    -> empty-mask observability event    (expected 1)
#   * additional_G_forwards_for_empty_mask      -> must stay 0
#   * additional_autograd_calls_for_empty_mask  -> must stay 0
# The two mask EVENTS are semantically different and MUST NOT share one counter.
# --------------------------------------------------------------------------- #
SMOKE_COUNTERS = OrderedDict(V0C.SMOKE_COUNTERS)
SMOKE_COUNTERS["primary_synthetic_target_masks"] = 0
SMOKE_COUNTERS["actual_logits_empty_mask_helper_checks"] = 0
SMOKE_COUNTERS["additional_G_forwards_for_empty_mask"] = 0
SMOKE_COUNTERS["additional_autograd_calls_for_empty_mask"] = 0
_FROZEN_V1_0C_EXPECTED = OrderedDict(V0C.SMOKE_EXPECTED_COUNTERS)
_FROZEN_V1_0C_EXPECTED["synthetic_smoke_target_masks"] = 1   # alias now counts ONLY primary masks
SMOKE_EXPECTED_COUNTERS = _FROZEN_V1_0C_EXPECTED
EXPECTED_COUNTERS_V1_0G = OrderedDict(SMOKE_EXPECTED_COUNTERS)
EXPECTED_COUNTERS_V1_0G["primary_synthetic_target_masks"] = 1
EXPECTED_COUNTERS_V1_0G["actual_logits_empty_mask_helper_checks"] = 1
EXPECTED_COUNTERS_V1_0G["additional_G_forwards_for_empty_mask"] = 0
EXPECTED_COUNTERS_V1_0G["additional_autograd_calls_for_empty_mask"] = 0
PRIMARY_TARGET_MASK_COUNTER = "primary_synthetic_target_masks"
PRIMARY_TARGET_MASK_ALIAS_COUNTER = "synthetic_smoke_target_masks"
EMPTY_MASK_OBSERVABILITY_COUNTER = "actual_logits_empty_mask_helper_checks"'''

T3_NEW = '''# --------------------------------------------------------------------------- #
# smoke counters (v1.0h SINGLE-OWNERSHIP COUNTER MODEL)
#
# Legacy ownership: the frozen v1.0c store `V0C.SMOKE_COUNTERS` is the AUTHORITATIVE, LIVE store for
# every inherited v1.0c/v1.0d execution counter, including the delegated router helper
# (`V0C.smoke_router`) and the inherited alias writer
# (`V0D.smoke_synthetic_target_mask_rank2`). v1.0h ALIASES that exact object - it does NOT copy it.
# This is the v1.0g defect repair: a shallow copy disconnected the reported store from the writer.
#
# Extension ownership: v1.0h owns ONLY the four post-v1.0c counters, in a dedicated extension store:
#   * primary_synthetic_target_masks            -> PRIMARY synthetic target masks   (expected 1)
#   * actual_logits_empty_mask_helper_checks    -> empty-mask observability event    (expected 1)
#   * additional_G_forwards_for_empty_mask      -> must stay 0
#   * additional_autograd_calls_for_empty_mask  -> must stay 0
#
# The backwards-compatible ALIAS `synthetic_smoke_target_masks` lives in the LEGACY store and is
# incremented exactly once by the frozen v1.0d mask producer, so it equals the primary by
# construction. The two mask EVENTS are semantically different and MUST NOT share one counter.
# --------------------------------------------------------------------------- #
LEGACY_COUNTER_STORE = V0C.SMOKE_COUNTERS               # live, authoritative - aliased, never copied
SMOKE_COUNTERS = V0C.SMOKE_COUNTERS                     # backwards-compatible module-local name
SMOKE_COUNTERS_EXT = OrderedDict([
    ("primary_synthetic_target_masks", 0),
    ("actual_logits_empty_mask_helper_checks", 0),
    ("additional_G_forwards_for_empty_mask", 0),
    ("additional_autograd_calls_for_empty_mask", 0),
])
assert not (set(LEGACY_COUNTER_STORE) & set(SMOKE_COUNTERS_EXT)), (
    "SCHEMA: extension counters must not collide with legacy counters")

PRIMARY_TARGET_MASK_COUNTER = "primary_synthetic_target_masks"
PRIMARY_TARGET_MASK_ALIAS_COUNTER = "synthetic_smoke_target_masks"
EMPTY_MASK_OBSERVABILITY_COUNTER = "actual_logits_empty_mask_helper_checks"

# ---- FULL 35-KEY EXPECTED TABLE (§F): 31 legacy keys + 4 extension keys -------------------------- #
_FULL_EXPECTED_COUNTERS_V1_0H = OrderedDict([
    # --- inherited legacy execution counters ---------------------------------------------------- #
    ("G_model_constructions", 1),
    ("B_phi_model_constructions", 1),
    ("checkpoint_deserializations", 2),
    ("strict_loads", 2),
    ("G_synthetic_forwards", 1),
    ("B_phi_synthetic_forwards", 1),
    ("total_model_forwards", 2),
    ("G_gradcam_autograd_calls", 1),
    ("router_numeric_input_autograd_calls", 1),
    ("total_autograd_calls", 2),
    ("synthetic_CAM_maps", 2),
    ("synthetic_router_attribution_rows", 4),
    ("synthetic_smoke_target_masks", 1),
    ("R_psi_model_constructions", 0),
    ("R_psi_checkpoint_loads", 0),
    ("R_psi_forwards", 0),
    ("S_omega_model_constructions", 0),
    ("S_omega_checkpoint_loads", 0),
    ("S_omega_forwards", 0),
    ("optimizer_constructions", 0),
    ("optimizer_step_calls", 0),
    ("training_backward_calls", 0),
    ("parameter_mutations", 0),
    # --- protected-data counters (EXPLICITLY present at 0) -------------------------------------- #
    ("raw_VAL_image_reads", 0),
    ("real_persisted_VAL_probability_reads", 0),
    ("VAL_GT_reads", 0),
    ("router_feature_cache_rows_read", 0),
    ("ROUTER_HOLDOUT_reads", 0),
    ("TEST_reads", 0),
    ("TRAIN_raw_reads", 0),
    ("scientific_outputs", 0),
    # --- v1.0h extension counters --------------------------------------------------------------- #
    ("primary_synthetic_target_masks", 1),
    ("actual_logits_empty_mask_helper_checks", 1),
    ("additional_G_forwards_for_empty_mask", 0),
    ("additional_autograd_calls_for_empty_mask", 0),
])
EXPECTED_COUNTERS_V1_0H = _FULL_EXPECTED_COUNTERS_V1_0H
SMOKE_EXPECTED_COUNTERS = _FULL_EXPECTED_COUNTERS_V1_0H
EXPECTED_COUNTER_COUNT_V1_0H = 35
assert len(EXPECTED_COUNTERS_V1_0H) == EXPECTED_COUNTER_COUNT_V1_0H, (
    "SCHEMA: the frozen v1.0h expected table MUST contain exactly 35 keys")


def legacy_counter_baseline_check() -> dict:
    """Fail-closed baseline gate (§H): every live legacy counter must start at 0 BEFORE any model.

    Never silently resets a nonzero counter. Any unexpected nonzero value aborts BEFORE model
    construction so that a reused interpreter/process cannot hide prior activity.
    """
    nonzero = OrderedDict([
        (k, v) for k, v in LEGACY_COUNTER_STORE.items() if int(v) != 0])
    return OrderedDict([
        ("legacy_store_id", id(LEGACY_COUNTER_STORE)),
        ("legacy_store_is_v0c_store", LEGACY_COUNTER_STORE is V0C.SMOKE_COUNTERS),
        ("legacy_counter_count", len(LEGACY_COUNTER_STORE)),
        ("nonzero_legacy_counters", dict(nonzero)),
        ("all_legacy_counters_zero", len(nonzero) == 0),
    ])


def extension_counter_baseline_check() -> dict:
    """Fail-closed baseline gate (§H) for the four v1.0h extension counters."""
    nonzero = OrderedDict([
        (k, v) for k, v in SMOKE_COUNTERS_EXT.items() if int(v) != 0])
    return OrderedDict([
        ("extension_store_id", id(SMOKE_COUNTERS_EXT)),
        ("extension_counter_count", len(SMOKE_COUNTERS_EXT)),
        ("extension_counter_keys", list(SMOKE_COUNTERS_EXT.keys())),
        ("nonzero_extension_counters", dict(nonzero)),
        ("all_extension_counters_zero", len(nonzero) == 0),
    ])


def merge_observed_counters() -> OrderedDict:
    """Canonical observed counter merge (§D): live legacy store + v1.0h extension store.

    FAILS on duplicate or unexpected ownership. No post-hoc hardcoded count injection.
    """
    merged = OrderedDict()
    for k, v in LEGACY_COUNTER_STORE.items():
        if k in merged:
            raise RuntimeError(f"COUNTER_MERGE_DUPLICATE_OWNERSHIP: {k}")
        merged[k] = v
    for k, v in SMOKE_COUNTERS_EXT.items():
        if k in merged:
            raise RuntimeError(f"COUNTER_MERGE_DUPLICATE_OWNERSHIP: {k}")
        merged[k] = v
    if set(merged) != set(EXPECTED_COUNTERS_V1_0H):
        raise RuntimeError("COUNTER_MERGE_KEYSET_MISMATCH_WITH_EXPECTED_TABLE")
    if len(merged) != EXPECTED_COUNTER_COUNT_V1_0H:
        raise RuntimeError("COUNTER_MERGE_COUNT_MISMATCH: expected 35")
    return merged


def exact_counter_contract_check(observed: OrderedDict) -> dict:
    """EXACT keyset + value contract (§G). Emits THREE separate booleans - never one opaque bool."""
    obs_keys = set(observed.keys())
    exp_keys = set(EXPECTED_COUNTERS_V1_0H.keys())
    extra = sorted(obs_keys - exp_keys)
    missing = sorted(exp_keys - obs_keys)
    keyset_exact = bool(obs_keys == exp_keys)
    count_exact = bool(len(observed) == EXPECTED_COUNTER_COUNT_V1_0H
                       and len(EXPECTED_COUNTERS_V1_0H) == EXPECTED_COUNTER_COUNT_V1_0H)
    values_exact = bool(keyset_exact and all(
        int(observed[k]) == int(v) for k, v in EXPECTED_COUNTERS_V1_0H.items()))
    return OrderedDict([
        ("observed_key_count", len(observed)),
        ("expected_key_count", len(EXPECTED_COUNTERS_V1_0H)),
        ("required_key_count", EXPECTED_COUNTER_COUNT_V1_0H),
        ("extra_observed_keys", extra),
        ("missing_expected_keys", missing),
        ("counter_keyset_exact", keyset_exact),
        ("counter_count_exact", count_exact),
        ("counter_values_exact", values_exact),
        ("counter_value_mismatches", OrderedDict([
            (k, {"observed": int(observed[k]), "expected": int(EXPECTED_COUNTERS_V1_0H[k])})
            for k in EXPECTED_COUNTERS_V1_0H
            if k in observed and int(observed[k]) != int(EXPECTED_COUNTERS_V1_0H[k])])),
        ("counts_match_expected", bool(keyset_exact and count_exact and values_exact)),
    ])'''

T4 = (
    "    SMOKE_COUNTERS[EMPTY_MASK_OBSERVABILITY_COUNTER] += 1",
    "    SMOKE_COUNTERS_EXT[EMPTY_MASK_OBSERVABILITY_COUNTER] += 1",
)

T5 = (
    "    SMOKE_COUNTERS[PRIMARY_TARGET_MASK_COUNTER] += 1",
    "    SMOKE_COUNTERS_EXT[PRIMARY_TARGET_MASK_COUNTER] += 1",
)

T6_OLD = '''    ev = OrderedDict()
    ev["authority_gates"] = V0B.verify_authority_gates()
    ev["environment"] = V0C.smoke_environment_check()
    ev["checkpoint_identity"] = V0C.smoke_checkpoint_identity()

    g_model, ginfo = V0B.load_g_component()'''

T6_NEW = '''    ev = OrderedDict()
    # §H: fail-closed counter baseline gate runs BEFORE any model construction.
    ev["counter_baseline"] = OrderedDict([
        ("legacy", legacy_counter_baseline_check()),
        ("extension", extension_counter_baseline_check()),
    ])
    if not (ev["counter_baseline"]["legacy"]["all_legacy_counters_zero"]
            and ev["counter_baseline"]["extension"]["all_extension_counters_zero"]):
        raise RuntimeError("COUNTER_BASELINE_NONZERO_BEFORE_MODEL_CONSTRUCTION")
    ev["authority_gates"] = V0B.verify_authority_gates()
    ev["environment"] = V0C.smoke_environment_check()
    ev["checkpoint_identity"] = V0C.smoke_checkpoint_identity()

    g_model, ginfo = V0B.load_g_component()'''

T7 = (
    "    for k in (\"B_phi_identity\", \"film_smoke\", \"embedding_smoke\"):\n        pass",
    None,  # placeholder - not used
)


def _crlf(s: str) -> str:
    """Normalize any newline style to CRLF (the frozen v1.0g source is pure CRLF)."""
    return s.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")


def main() -> int:
    src_bytes = SRC.read_bytes()
    got = sha256_bytes(src_bytes)
    if got != V1_0G_EXPECTED_SHA:
        print(f"FAIL: v1.0g source SHA mismatch: {got} != {V1_0G_EXPECTED_SHA}")
        return 2
    if b"\n" not in src_bytes or src_bytes.count(b"\r\n") != src_bytes.count(b"\n"):
        print("FAIL: frozen v1.0g source is not pure CRLF; refusing to transform")
        return 4
    text = src_bytes.decode("utf-8")

    transforms = [
        ("T1 classification/revision/docstring", T1_OLD, T1_NEW, 1),
        ("T2 add v1.0h counter-model constants", T2[0], T2[1], 1),
        ("T3 replace counter block with single-ownership model", T3_OLD, T3_NEW, 1),
        ("T4 empty helper -> extension store", T4[0], T4[1], 1),
        ("T5 primary helper -> extension store", T5[0], T5[1], 1),
        ("T6 baseline gate before model construction", T6_OLD, T6_NEW, 1),
    ]
    for name, old, new, exp_n in transforms:
        old_c = _crlf(old)
        new_c = _crlf(new)
        n = text.count(old_c)
        if n != exp_n:
            print(f"FAIL anchor {name}: found {n} occurrences, expected {exp_n}")
            return 3
        text = text.replace(old_c, new_c)

    out_bytes = text.encode("utf-8")
    if out_bytes.count(b"\r\n") != out_bytes.count(b"\n"):
        print("FAIL: generated source is not pure CRLF")
        return 5
    DST.write_bytes(out_bytes)
    out = DST.read_bytes()
    print(f"WROTE {DST}")
    print(f"v1.0g source sha256: {got}")
    print(f"v1.0h source sha256: {sha256_bytes(out)}")
    print(f"v1.0h bytes: {len(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
