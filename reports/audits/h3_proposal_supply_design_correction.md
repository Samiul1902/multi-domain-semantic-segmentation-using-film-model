# H3 Proposal-Supply — Pre-Execution Design Repair / Non-Degeneracy Correction

**Status:** `ADDITIVE_CORRECTION__NON_DEGENERATE_MAPPING_FROZEN`
**Ready state:** `H3_IMPLEMENTATION_BOUND__AWAITING_PROSPECTIVE_TRAINING_AUTHORIZATION`
**Training:** NOT authorized — 0 epochs trained, no H3 checkpoint exists.

---

## 1. Defect found prospectively

The frozen H3 design proposed:

```
sigma_i = clip(scale_ref * sqrt(area_i), 0.35, 0.75)   with scale_ref = 4.0
```

Because `area_i >= 1` for every component, `4.0 * sqrt(area_i) >= 4.0 >= 0.75`, so the
upper clip is always hit. **The mapping degenerates to `sigma_i = 0.75` for every
component** — identical to the historical fixed-sigma baseline. The active H3 branch
would have been a NULL experiment (no supply-diversity signal).

- **Classification:** `PRE_EXECUTION_PARAMETERIZATION_DEFECT__ZERO_TRAINING_IMPACT`
- **Zero training impact:** caught before any training; no checkpoints, no counters.

## 2. What was preserved (not overwritten)

- Scientific axis `A_PROPOSAL_SUPPLY_RECALL_LIMITATION` — unchanged.
- Intervention family `A_TARGET_SUPPORT_REDESIGN` — unchanged.
- All non-H3 axes frozen and SHA-bound (dataset, input, architecture, loss, optimizer,
  proposal policy, refiner, global baseline, eval, TEST). TEST reads = 0.
- Original design protocol and the defective code-change spec are **preserved** (new
  artifacts are additive), per the ruling.

## 3. Wording reassessment

`A_TARGET_SUPPORT_REDESIGN` is reassessed as
**`FIXED_TARGET_SUPPORT_MAY_BE_MISMATCHED_TO_COMPONENT_SCALE`** — the fixed historical
target support (sigma = 0.75) is mismatched to small components, which motivates the
size-adaptive correction.

## 4. TRAIN-only area-distribution audit

- Population: **TRAIN FULL_FIELD only** (771 images). VAL/TEST untouched.
- Method: code-exact 128-space NEAREST subsample of the padded 512 mask
  (`m512[::4,::4]`), 8-connected labeling, per-component foreground pixel count.
- **Frozen `A_ref = 14.0`** = p75 of the TRAIN-only FULL_FIELD 128-space area distribution
  (source: `reports/tables/h3_aref_code_exact.json`).

## 5. Corrected monotonic mapping (frozen)

```
sigma_i = clip(0.35 + 0.40 * sqrt(A128_i / 14.0), 0.35, 0.75)
```

- `A128_i` = per-component foreground pixel count in 128-space heatmap space.
- Small components → smaller sigma → sharper, higher-contrast peak (better tiny-object
  supply). Large components cap at `sigma_max = 0.75` (historical behavior).

## 6. Non-degeneracy verification — PASS

Over TRAIN-only FULL_FIELD components (`reports/tables/h3_code_exact_sigma_distribution.json`):

| Metric | Value |
|---|---|
| n components | 1078 |
| distinct sigma levels | **14** (not 1) |
| fraction at ceiling 0.75 | **0.233** (not 1.0) |
| fraction at floor 0.35 | 0.0 |
| median sigma | 0.589 |
| TINY median sigma | 0.457 |
| non-TINY median sigma | 0.633 |
| TINY < non-TINY | **True** |

**Verdict:** spread of sigma values, not collapsed to 0.75; TINY objects get sharper
support than non-TINY. Non-degenerate.

## 7. Backward-compatibility + H3-branch unit tests

`tests/test_h3_size_adaptive_sigma.py` — **12 passed**. Covers: fixed-sigma byte-identical
when `component_areas=None`; large-area caps at historical behavior; small-area yields a
sharper peak; mapping spreads/monotonic/bounded; `heatmap_space_component_areas` counts
correctly; dataset opt-in flag defaults to Phase-13B behavior; frozen H3 2-term selection.

## 8. Checkpoint-selection implementation audit

- **Finding:** the trainer historically used an in-line grid-search feasible-selection,
  not the frozen `MAX VAL_LOCALIZATION_RECALL` rule.
- **Classification:** `OPERATIONAL_SELECTION_IMPLEMENTATION__NO_NEW_SCIENTIFIC_AXIS`.
- **Minimal impl:** added `select_h3_supply_epoch` / `build_h3_supply_selection_tuple` to
  `src/training/clean_v3_selection.py` and a gated branch in the trainer
  (`--selection_rule max_localization_recall`). **Default behavior unchanged.**

## 9. Dedicated H3 config

`configs/kub/phase13b_localizer_h3_size_adaptive_sigma.yaml` binds the frozen contract:
`size_adaptive_sigma: true`, `heatmap_resolution: 128`, `A_ref: 14.0`, `sigma_min/max:
0.35/0.75`, `checkpoint_selection.rule: max_localization_recall`.

## 10. Implementation bindings (SHA-256)

See `h3_proposal_supply_final_implementation_binding.json`. Key files:
`src/inference/heatmap_targets.py`, `src/data/kub_localizer_dataset.py`,
`src/training/clean_v3_selection.py`, `scripts/training/train_phase13b_localizer.py`,
`tests/test_h3_size_adaptive_sigma.py`, `scripts/audit/h3_calibrate_size_adaptive_sigma.py`,
`configs/kub/phase13b_localizer_h3_size_adaptive_sigma.yaml`,
`reports/tables/h3_code_exact_sigma_distribution.json`.

## 11. Checklist update (additive)

`h3_proposal_supply_pre_execution_checklist.json`: C12 → `PASS__CODE_APPLIED_AND_BC_TESTED`,
added C14 (defect correction + non-degeneracy verification, PASS). C13 remains
`PENDING__NOT_AUTHORIZED`. `current_status` →
`H3_IMPLEMENTATION_BOUND__AWAITING_PROSPECTIVE_TRAINING_AUTHORIZATION`.

## 12. Stop condition

No H3 training launched. Synthetic counters: `epochs_trained = 0`.
**Next action requires supervisor authorization of H3 TRAINING.**
