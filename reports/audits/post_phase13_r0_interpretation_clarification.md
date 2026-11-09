# POST-PHASE-13 R0 — INTERPRETATION CLARIFICATION (ADDITIVE ERRATUM)

- classification: **`CAUSAL_LANGUAGE_SCOPE_CLARIFICATION_ONLY`**
- status: **additive erratum — R0 artifacts NOT rewritten, NOT edited, NOT deleted**
- created (UTC): `2026-09-22T06:09:00Z`

## Reason

The persisted R0 artifacts contain **exclusionary** causal language:

> "the failure is an intervention-precision failure, **not a representation failure**"

That phrasing overstates what the R0 decomposition establishes. The decomposition shows the deployable
failure is **dominated** by intervention precision. It does **not** establish that representation failure
is *excluded* as a contributor.

## Locations found

| path | phrase |
|---|---|
| `reports/audits/post_phase13_regional_revision_r0_failure_decomposition.json` | `not a representation failure` |
| `reports/audits/post_phase13_regional_revision_r0_failure_decomposition.md` | `not a representation failure` |
| `docs/TASKS.md` | `not a representation failure` |

## Canonical wording (supersedes the phrasing above)

> The observed Phase-13 deployable failure is dominated by poor intervention precision / off-target
> intervention burden. Existing evidence does not establish that representation failure is the primary
> limitation, but it also does not exclude localizer representation or score calibration as contributors.

## Scope of correction

| item | value |
|---|---|
| H1 ordering changed | **NO** |
| scientific measurements changed | **NO** |
| candidate family changed | **NO** |
| membership changed | **NO** |
| R0 artifacts rewritten | **NO** |
| R0 artifacts deleted or edited | **NO** |

## What remains supported

- 122 GT-hit proposals exist and 27 components are recovered with **0** component losses, so the
  existing localizer does produce usable targets
- the off-target support fraction is the strongest **descriptive associate** of the FP burden
  (Spearman rho 0.5918 – 0.6372, consistent across all four architectures)
- every label-blind marginal floor removes strictly more off-target than GT-hit proposals
- therefore **intervention precision is the dominant contributor** to the deployable failure

## What is NOT established

- that localizer representation quality is **not** a contributing limitation
- that the proposal score is adequately calibrated
- that fixing acceptance alone will recover the oracle benefit
- **any sole-cause attribution**

## Implication for R1

H1 remains the correct **first** experiment because it is the minimum-change test that can falsify the
intervention-precision explanation. **H1 failing would not by itself prove a representation failure** —
it would leave representation and score calibration as live candidates for H2.

## Zero-execution counters

training **0** · optimizer **0** · model constructions **0** · CUDA requests **0** · localizer forwards
**0** · segmentation forwards **0** · regional crop forwards **0** · proposal generation **0** ·
checkpoint writes **0** · TEST reads **0** · external-test reads **0**
