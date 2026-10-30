#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the Phase35 v1.0g EXECUTABLE interpretability harness from the frozen v1.0f source.

Classification: PRE_EXECUTION_SYNTHETIC_SMOKE_COUNTER_CONTRACT_REPAIR__NO_SCIENTIFIC_PROTOCOL_CHANGE
Revision: ra_medfilm_barr_phase35_interpretability_v1_0g

This is a SOURCE/GOVERNANCE-ONLY repair generator. It performs NO model execution.

The v1.0f harness correctly FAILED CLOSED on a single bookkeeping defect:
  synthetic_smoke_target_masks observed = 2 (expected 1)
because the empty-mask observability helper incremented the SAME counter used for the PRIMARY
synthetic target mask.

v1.0g separates the two semantically distinct events into two counters while preserving ALL
scientific, numerical, model-interface, protected-data, and immutability behavior byte-for-byte
(method-body-level identity; only counter bookkeeping and the expected-counter declaration change).

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/build_phase35_execution_v1_0g.py
"""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
SRC = ROOT / "scripts" / "analysis"
F = SRC / "phase35_interpretability_execution_v1_0f.py"
G = SRC / "phase35_interpretability_execution_v1_0g.py"

# path-frozen predecessor SHA (verified before writing)
V1_0F_SHA = "6a6097f4a3c346df38ab5ec452dc97717cdb65d789bf8bde8031442cb236e3e5"

# --------------------------------------------------------------------------- #
# exact textual transforms (each must match exactly once)
# --------------------------------------------------------------------------- #
TRANSFORMS = []

# 1) module docstring / header revision
TRANSFORMS.append((
    '"""Phase35 v1.0f EXECUTABLE interpretability harness - ACTUAL-LOGITS empty-mask observability repair.',
    '"""Phase35 v1.0g EXECUTABLE interpretability harness - SMOKE COUNTER-CONTRACT SEPARATION repair.',
))
TRANSFORMS.append((
    "Revision: ra_medfilm_barr_phase35_interpretability_v1_0f",
    "Revision: ra_medfilm_barr_phase35_interpretability_v1_0g",
))

# 2) add the counter-contract explanation to the header prose
TRANSFORMS.append((
    "The frozen v1.0b/common/v1.0c/v1.0d/v1.0e modules are preserved byte-for-byte and are IMPORTED here -\n"
    "never modified. The v1.0d rank-safe target scalar is reused by direct reference.",
    "The frozen v1.0b/common/v1.0c/v1.0d/v1.0e modules are preserved byte-for-byte and are IMPORTED here -\n"
    "never modified. The v1.0d rank-safe target scalar is reused by direct reference.\n"
    "\n"
    "v1.0g repairs the SINGLE bookkeeping defect that correctly blocked the first v1.0f smoke\n"
    "(`phase35_synthetic_smoke_terminal_v1_0f.json`, `728d1535...`): the v1.0f in-scope actual-logits\n"
    "empty-mask observability helper incremented the SAME counter used for the PRIMARY synthetic target\n"
    "mask, so `synthetic_smoke_target_masks` reached 2 against a frozen expected value of 1.\n"
    "\n"
    "WHAT CHANGES (bookkeeping only)\n"
    "  * `primary_synthetic_target_masks` is the canonical counter for PRIMARY synthetic target masks\n"
    "    (frozen expected = 1). It is incremented ONCE, by `smoke_synthetic_target_mask_rank2()`.\n"
    "  * `actual_logits_empty_mask_helper_checks` is a NEW, separate counter for the empty-mask\n"
    "    OBSERVABILITY / FALLBACK-VALIDATION event (frozen expected = 1). The helper still creates one\n"
    "    rank-2 all-False Boolean mask, but that mask is a diagnostic derivative of the SAME primary\n"
    "    mask and is NOT a scientific or primary target mask.\n"
    "  * `synthetic_smoke_target_masks` is retained as a BACKWARDS-COMPATIBLE ALIAS of\n"
    "    `primary_synthetic_target_masks` and therefore MUST equal 1.\n"
    "  * `additional_G_forwards_for_empty_mask` / `additional_autograd_calls_for_empty_mask` are frozen\n"
    "    at 0 (the empty-mask check performs no forward and no autograd).\n"
    "\n"
    "WHAT DOES NOT CHANGE (frozen scientific intent)\n"
    "  * every model, numerical, interface, protected-data, and immutability behavior of v1.0f is\n"
    "    inherited verbatim; the Grad-CAM mathematics, eight finite guards, alpha/ReLU/bilinear/\n"
    "    align_corners=False/min-max normalization, atol=1e-7 / rtol=0 comparison, direct parameter\n"
    "    `.grad` audit, router and FiLM semantics, and read guards are untouched.",
))

# 3) counter store: separate primary target mask from empty-mask observability
TRANSFORMS.append((
    "# --------------------------------------------------------------------------- #\n"
    "# smoke counters: reuse the frozen v1.0c counter store VERBATIM (semantics preserved);\n"
    "# v1.0f adds NO new counters and changes NO expected count.\n"
    "# --------------------------------------------------------------------------- #\n"
    "SMOKE_COUNTERS = V0C.SMOKE_COUNTERS\n"
    "SMOKE_EXPECTED_COUNTERS = V0C.SMOKE_EXPECTED_COUNTERS\n",
    "# --------------------------------------------------------------------------- #\n"
    "# smoke counters (v1.0g COUNTER-CONTRACT SEPARATION)\n"
    "#\n"
    "# The frozen v1.0c store is COPIED (not mutated) so that the three mask-related counters can be\n"
    "# declared with semantically SEPARATE keys:\n"
    "#   * primary_synthetic_target_masks            -> PRIMARY synthetic target masks   (expected 1)\n"
    "#   * synthetic_smoke_target_masks              -> backwards-compatible ALIAS        (expected 1)\n"
    "#   * actual_logits_empty_mask_helper_checks    -> empty-mask observability event    (expected 1)\n"
    "#   * additional_G_forwards_for_empty_mask      -> must stay 0\n"
    "#   * additional_autograd_calls_for_empty_mask  -> must stay 0\n"
    "# The two mask EVENTS are semantically different and MUST NOT share one counter.\n"
    "# --------------------------------------------------------------------------- #\n"
    "SMOKE_COUNTERS = OrderedDict(V0C.SMOKE_COUNTERS)\n"
    "SMOKE_COUNTERS[\"primary_synthetic_target_masks\"] = 0\n"
    "SMOKE_COUNTERS[\"actual_logits_empty_mask_helper_checks\"] = 0\n"
    "SMOKE_COUNTERS[\"additional_G_forwards_for_empty_mask\"] = 0\n"
    "SMOKE_COUNTERS[\"additional_autograd_calls_for_empty_mask\"] = 0\n"
    "_FROZEN_V1_0C_EXPECTED = OrderedDict(V0C.SMOKE_EXPECTED_COUNTERS)\n"
    "_FROZEN_V1_0C_EXPECTED[\"synthetic_smoke_target_masks\"] = 1   # alias now counts ONLY primary masks\n"
    "SMOKE_EXPECTED_COUNTERS = _FROZEN_V1_0C_EXPECTED\n"
    "EXPECTED_COUNTERS_V1_0G = OrderedDict(SMOKE_EXPECTED_COUNTERS)\n"
    "EXPECTED_COUNTERS_V1_0G[\"primary_synthetic_target_masks\"] = 1\n"
    "EXPECTED_COUNTERS_V1_0G[\"actual_logits_empty_mask_helper_checks\"] = 1\n"
    "EXPECTED_COUNTERS_V1_0G[\"additional_G_forwards_for_empty_mask\"] = 0\n"
    "EXPECTED_COUNTERS_V1_0G[\"additional_autograd_calls_for_empty_mask\"] = 0\n"
    "PRIMARY_TARGET_MASK_COUNTER = \"primary_synthetic_target_masks\"\n"
    "PRIMARY_TARGET_MASK_ALIAS_COUNTER = \"synthetic_smoke_target_masks\"\n"
    "EMPTY_MASK_OBSERVABILITY_COUNTER = \"actual_logits_empty_mask_helper_checks\"\n"
))

# 4) primary mask increments the PRIMARY counter (and its alias) exactly once
TRANSFORMS.append((
    "def smoke_synthetic_target_mask_rank2():\n"
    '    """SMOKE_SYNTHETIC_TARGET_MASK_RANK2: deterministic rank-2 centered square (frozen v1.0d)."""\n'
    "    return V0D.smoke_synthetic_target_mask_rank2()\n",
    "def smoke_synthetic_target_mask_rank2():\n"
    '    """SMOKE_SYNTHETIC_TARGET_MASK_RANK2: deterministic rank-2 centered square (frozen v1.0d).\n'
    "\n"
    "    v1.0g: this is THE one and only PRIMARY synthetic target mask. It increments the canonical\n"
    "    PRIMARY counter and its backwards-compatible alias exactly ONCE (V0D already incremented the\n"
    "    alias internally, so the alias is not double-counted here). The empty-mask OBSERVABILITY event\n"
    "    (see `empty_mask_helper_check_insession_actual_logits`) uses a SEPARATE counter.\n"
    '    """\n'
    "    mask = V0D.smoke_synthetic_target_mask_rank2()\n"
    "    # V0D increments the backwards-compatible alias `synthetic_smoke_target_masks` internally;\n"
    "    # v1.0g adds the canonical PRIMARY counter (one event, two views of the same fact).\n"
    "    SMOKE_COUNTERS[PRIMARY_TARGET_MASK_COUNTER] += 1\n"
    "    return mask\n"
))

# 5) empty-mask observability increments its OWN counter (never the primary one)
TRANSFORMS.append((
    '    SMOKE_COUNTERS["synthetic_smoke_target_masks"] += 1\n'
    "    return OrderedDict([\n"
    '        ("same_actual_G_logits_used", True),\n'
    '        ("surrogate_zero_logits_used", False),\n',
    "    # v1.0g: the empty all-False mask is an OBSERVABILITY / FALLBACK-VALIDATION derivative of the\n"
    "    # SAME primary mask, NOT a scientific or primary target mask. It MUST NOT increment the primary\n"
    "    # (or alias) counter; it increments its own dedicated counter exactly once.\n"
    "    SMOKE_COUNTERS[EMPTY_MASK_OBSERVABILITY_COUNTER] += 1\n"
    "    return OrderedDict([\n"
    '        ("same_actual_G_logits_used", True),\n'
    '        ("surrogate_zero_logits_used", False),\n'
))

# 6) the empty-mask result block names its own counter category
TRANSFORMS.append((
    '        ("fusion_mask_source", "actual same-forward synthetic G logits tensor (v1.0f)"),\n',
    '        ("fusion_mask_source", "actual same-forward synthetic G logits tensor (v1.0g)"),\n'
    '        ("counter_category", EMPTY_MASK_OBSERVABILITY_COUNTER),\n'
    '        ("counts_as_primary_target_mask", False),\n'
))

# 7) mode_smoke exposes the v1.0g expected-counter set and the alias identity
TRANSFORMS.append((
    '    ev["counters"] = dict(SMOKE_COUNTERS)\n'
    '    ev["expected_counters"] = dict(SMOKE_EXPECTED_COUNTERS)\n'
    '    ev["counts_match_expected"] = all(\n'
    '        SMOKE_COUNTERS[k] == v for k, v in SMOKE_EXPECTED_COUNTERS.items())\n',
    '    ev["counters"] = dict(SMOKE_COUNTERS)\n'
    '    ev["expected_counters"] = dict(EXPECTED_COUNTERS_V1_0G)\n'
    '    ev["counts_match_expected"] = all(\n'
    '        SMOKE_COUNTERS[k] == v for k, v in EXPECTED_COUNTERS_V1_0G.items())\n'
    '    ev["counter_contract"] = OrderedDict([\n'
    '        ("primary_target_mask_counter", PRIMARY_TARGET_MASK_COUNTER),\n'
    '        ("primary_target_mask_alias_counter", PRIMARY_TARGET_MASK_ALIAS_COUNTER),\n'
    '        ("empty_mask_observability_counter", EMPTY_MASK_OBSERVABILITY_COUNTER),\n'
    '        ("primary_target_mask_count", SMOKE_COUNTERS[PRIMARY_TARGET_MASK_COUNTER]),\n'
    '        ("primary_target_mask_alias_count", SMOKE_COUNTERS[PRIMARY_TARGET_MASK_ALIAS_COUNTER]),\n'
    '        ("empty_mask_helper_check_count", SMOKE_COUNTERS[EMPTY_MASK_OBSERVABILITY_COUNTER]),\n'
    '        ("alias_equals_primary",\n'
    '         SMOKE_COUNTERS[PRIMARY_TARGET_MASK_COUNTER]\n'
    '         == SMOKE_COUNTERS[PRIMARY_TARGET_MASK_ALIAS_COUNTER]),\n'
    '        ("empty_mask_not_counted_as_primary",\n'
    '         SMOKE_COUNTERS[PRIMARY_TARGET_MASK_COUNTER] == 1),\n'
    '        ("additional_G_forwards_for_empty_mask", 0),\n'
    '        ("additional_autograd_calls_for_empty_mask", 0),\n'
    '    ])\n'
))

# 8) the mode_smoke all_pass gate also requires the counter-contract identities
TRANSFORMS.append((
    '    ev["all_pass"] = bool(ev["film_smoke"]["all_pass"]\n',
    '    ev["counter_contract_ok"] = bool(\n'
    '        ev["counter_contract"]["alias_equals_primary"]\n'
    '        and ev["counter_contract"]["empty_mask_not_counted_as_primary"]\n'
    '        and SMOKE_COUNTERS[EMPTY_MASK_OBSERVABILITY_COUNTER] == 1)\n'
    '    ev["all_pass"] = bool(ev["counter_contract_ok"]\n'
    '                          and ev["film_smoke"]["all_pass"]\n'
))

# 9) MODE_DISPATCH / revision constants
TRANSFORMS.append((
    'REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0f"\n'
    'CLASSIFICATION = ("PRE_EXECUTION_ACTUAL_LOGITS_EMPTY_MASK_OBSERVABILITY_IMPLEMENTATION_AMENDMENT"\n'
    '                  "__NO_SCIENTIFIC_PROTOCOL_CHANGE")\n',
    'REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0g"\n'
    'CLASSIFICATION = ("PRE_EXECUTION_SYNTHETIC_SMOKE_COUNTER_CONTRACT_REPAIR"\n'
    '                  "__NO_SCIENTIFIC_PROTOCOL_CHANGE")\n'
    'ONLY_CHANGE = "SMOKE_COUNTER_CATEGORY_SEPARATION"\n'
))


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    obs = sha256_file(F)
    if obs != V1_0F_SHA:
        raise SystemExit(f"FAIL-CLOSED: v1.0f source SHA mismatch: {obs}")
    src = F.read_text(encoding="utf-8")
    changed = 0
    for old, new in TRANSFORMS:
        n = src.count(old)
        if n != 1:
            raise SystemExit(
                f"FAIL-CLOSED: transform anchor count {n} != 1 for:\n{old[:120]!r}")
        src = src.replace(old, new)
        changed += 1
    G.write_text(src, encoding="utf-8")
    print(f"transforms applied: {changed}")
    print(f"{sha256_file(G)}  scripts/analysis/{G.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
