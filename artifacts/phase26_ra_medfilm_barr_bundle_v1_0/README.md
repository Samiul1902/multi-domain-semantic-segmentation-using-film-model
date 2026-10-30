# Phase26 canonical bundle - RA-MedFiLM-BARR

Bundle revision: `ra_medfilm_barr_bundle_v1_0`
Phase26 revision: `ra_medfilm_barr_phase26_integration_v1_0`
Router semantics revision: `phase26_v1_2`

## Operational meaning
ASSEMBLY_ONLY__NO_PARAMETER_OPTIMIZATION. This bundle contains NO weights;
the canonical checkpoint files remain authoritative at their original paths.

## Canonical operating point
- variant: A8_C9
- nominal budget: 0.25
- lambda representative: 0.25 (membership-equivalent serialization; NOT performance-selected)

## Runtime policy
score = delta_hat_final - 0.25*C; EXECUTE iff score >= tau_C8_final.
tau_C8_final = -5003565381643716252018011/205414980000000000000000000
tau_C7_final = 24796109646558761/20000000000000000000
C = 1051648/10270749

## Future-cohort rule
FIXED_DEV_CALIBRATED_THRESHOLD. Never force 25% / never rank / never top-K /
never recalibrate. Report nominal budget AND realized activation fraction.

## Locks
ROUTER_HOLDOUT: RESERVED_UNOPENED_FOR_PHASE30
VAL808: UNOPENED
TEST: LOCKED_UNTIL_PHASE39
