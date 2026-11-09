# Phase 24 — Router Input Contract v1.2 Repair: Closure Report

**Classification:** `SPECIFICATION_COMPLETENESS_AND_GOVERNANCE_SYNC` · `science_changed = false` ·
`method_changed = false` · `is_new_method = false`
**Method name:** RA-MedFiLM-BARR — unchanged
**Revision created (additive):** `ra_medfilm_barr_narrowed_v1_2` (supersedes v1.1 router-feature spec only)

## Terminal

```
PHASE24_ROUTER_FEATURE_SPEC_V1_2_COMPLETE__RF1_RF2_RF3_RESOLVED__PHASE25B_REENTRY_ELIGIBLE_NOT_STARTED
```

The two inconsistencies reported in the first pass (`D1`, `D2`) were closed by **supervisor ruling**.
No defect remains open; the router-feature specification v1.2 is complete. Phase 25B is
**re-entry eligible** but is **NOT** resumed here. Phase 25C / 25D are **NOT** started.

## What was fixed (no blocked items invented)

| Blocker | Status | Evidence |
|---|---|---|
| **RF-1** — declared 32-dim output but no defined C→32 reduction | **RESOLVED** (14/14 checks) | `phase24_router_feature_reduction_contract_v1_2.json` |
| **RF-2** — ROI→feature-grid mapping undefined | **RESOLVED** (13/13 checks) | `phase24_roi_feature_mapping_contract_v1_2.json` |
| **RF-3** — ten scalar definitions / threshold roles ambiguous | **FULLY RESOLVED** (11/11 checks, 0 unresolved roles) | `phase24_scalar_feature_contract_v1_2.json` |
| **D1** — `predicted_roi_area_fraction` not internally consistent | **RESOLVED** (9/9 checks) | `phase24_predicted_roi_area_fraction_adjudication.json` |
| **D2** — router parameter-count mismatch | **RESOLVED** (12/12 checks) | `phase24_router_parameter_count_adjudication.json` |

- **RF-1 operation frozen:** `DETERMINISTIC_CHANNEL_ADAPTIVE_AVG_POOL_1D_V1`.
  For `j in 0..31`: `start_j = floor(j*C/32)`, `end_j = ceil((j+1)*C/32)`,
  `z[j] = mean(v[start_j:end_j])`. Native widths C ∈ {256 (bridge), 48 (decoder2), 24 (decoder1)}.
  No trainable projection introduced (`trainable_feature_projection = false`).
- **RF-2 mapping frozen:** half-open `[x0,x1)`, `fx0=floor(x0*Wf/512)`, `fy0=floor(y0*Hf/512)`,
  `fx1=ceil(x1*Wf/512)`, `fy1=ceil(y1*Hf/512)`, clipped; verified on 4957/4957 manifest rows.
- **RF-3 threshold semantics:** `entropy_proxy_mean` THRESHOLD_FREE; boundary stats use
  `t_seg = 0.50`; `pred_*` ROI scalars use `t_roi = 0.30`.

## Defects REPORTED in pass 1, then RESOLVED by ruling

### D1 — `predicted_roi_area_fraction`
- **Reported:** declared unit *"fraction of native square canvas"* ⇒ natural range `[0,1]`, but
  `side²/512²` spanned `[1.53e-05, 2.25]` — **exceeded 1.0 in 1257 / 4957 rows (25.4%)**.
- **Ruling:** redefine as the **clipped in-canvas area fraction** (resolution **C3**):
  `w_in = max(0, min(512, x2) - max(0, x1))`, `h_in = max(0, min(512, y2) - max(0, y1))`,
  `predicted_roi_area_fraction = w_in * h_in / 512²`. External crop padding contributes nothing.
- **Status:** new range `[1.53e-05, 1.0]`, **0 rows > 1.0**. Old formula marked
  `SUPERSEDED_PRE_EXECUTION_SPEC_FORMULA__NOT_USED_FOR_PHASE25B`; the old value is **not** clipped
  retroactively.

### D2 — router parameter count
- **Reported:** declared `expected_parameter_count_closed_form = 36353`; recomputed **36801**
  (LayerNorm affine ON), delta **448**.
- **Ruling:** architecture **UNCHANGED**. `36353` is exactly the **linear-layer MLP core**
  (three `Linear` layers, no embedding, no LayerNorm affine params). Canonical total trainable
  parameter count is frozen at **36801** = 36353 + 64 (embedding) + 384 (2 × LayerNorm affine).
- **Status:** no hidden width silently modified.

## Section 12 — notebook supervisor-closure addendum

The Phase24 reviewer notebook was extended **additively** with the section
**"Router Feature Specification v1.2 — Supervisor Closure"** recording the D1/D2 rulings, the exact
frozen replacements, and a final status block: `RF1 PASS / RF2 PASS / RF3 PASS / D1 PASS / D2 PASS`.
No experimental plot was added.

## Section 13 — notebook execution + 3× determinism

- Notebook: `notebooks/phasewise/phase_24_architecture_spec/phase24_narrowed_benefit_aware_refinement_spec.ipynb`
- Final executed SHA-256: **`9d62384e8afa2f35e985eac219711df0334fbfe72c33c0edd29ff3f4897d4027`**
- **Pre-supervisor-closure provenance SHA-256:** `97f0efd99a9be662b2c5ba2338132b70131e07ddb01eec58eac2b80295adddff`
- `byte_identical_three_builds = true` · `nbformat_valid = true`
- `code cells executed = 62/62` · `errors = 0` · `experimental_result_figures_added = 0` · `model_forwards = 0`
- SHA verified stable **across separate invocations**, not only within one run.

### Determinism normalisation applied (no scientific content altered)
1. `metadata.execution` per-cell wall-clock timestamps (nbclient).
2. Object memory addresses in reprs (`0x…` → `0xADDR`).
3. **ipykernel arbitrary stdout/stderr chunk boundaries** — consecutive stream outputs of the
   same name are merged before normalisation, because the same text arrives split differently
   run-to-run.
4. Stable cell ids `p24v12{i:03d}` replace random uuid4; stray `outputs` keys dropped from
   non-code cells (nbformat `additionalProperties` violation).

## Preserved (unchanged)

| Artifact | SHA-256 |
|---|---|
| Phase 25A canonical notebook | `fd2bab01…21dfb2dd` (matches canonical ✓) |
| Phase 24 notebook v1.1 provenance copy | `612d7170…6ec78caef` (matches pre-repair original ✓) |
| `phase24_exact_implementation_spec.json` | `6b1a71d5…6af271dd` |
| `phase24_router_input_contract.csv` | `2aef05c8…ba9a335a` |
| `phase24_router_primary_feature_set.csv` | `7a030b0f…f1d231947d` |

Pass-1 blocked-state audits are retained as `BLOCKED_ATTEMPT_PROVENANCE` — a valid fail-closed stop,
not failed science.

## Lock counters

`model_instantiations = 0` · `forward_passes = 0` · `training_runs = 0` ·
`feature_rows_extracted = 0` · `holdout_reads = 0` · `VAL_reads = 0` · **`TEST_reads = 0`**

## Re-entry condition

Phase 25B is **re-entry eligible**. A supervisor approval is still required before Phase 25B
actually begins. Phase 25C / 25D remain blocked.
