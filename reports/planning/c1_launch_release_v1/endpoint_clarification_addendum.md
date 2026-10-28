# C1 Primary Endpoint — Additive Clarification (no estimand change)

Applies to: `C1_FILM_ATTRIBUTION_V1`, frozen protocol `531e3eb2…087a61`
Status: `ADDITIVE_CLARIFICATION__ESTIMAND_UNCHANGED__NO_SUPERVISOR_ESCALATION_REQUIRED`
This document does **not** modify `protocol.json`. The frozen protocol remains
byte-identical. It resolves an *implementation reading* question, not a scientific
definition question.

---

## 1. The frozen endpoint string

```
seed_average_of_paired_equal_domain_macro_Dice_T_minus_C_on_selected_VAL
```

## 2. The ambiguity

"selected_VAL" does not state which artifact supplies the selected-epoch metrics:

- **(a) stored `best_records`** — the per-sample VAL records captured during the
  epoch that won selection, or
- **(b) a recomputed VAL pass** from the selected checkpoint `best_model`.

## 3. What the implementation actually does

`Trainer.evaluate` returns `(val_loss, by_domain, records)`. On an improving epoch
`Trainer.run` writes, in the same branch and in one statement group:

```
self.best_model   = {name: p.detach().cpu().clone() for name, p in self.model.state_dict().items()}
self.best_records = records
```

Both artifacts are captured from the **same** epoch and the **same** VAL pass.
`best_records` are the records produced by that pass; `best_model` is the weight
snapshot taken immediately after that epoch's optimizer steps and immediately
before `evaluate` was called for that epoch. No training step occurs between them,
and nothing after selection mutates either artifact.

Consequently (a) and (b) are the *same numbers*, not two estimates:

- the VAL loader is deterministic (fixed order, `shuffle=False`, seeded generator);
- forward evaluation is deterministic on CPU and — as measured in the readiness
  assessment — bit-identical on CUDA (`cudnn.deterministic=True`,
  `benchmark=False`; repeated forward on identical input gave `torch.equal`);
- no augmentation is applied on VAL.

Empirical confirmation is asserted in
`tests/test_c1_launch_release.py::EndpointClarificationTests::test_best_records_agree_with_recomputed_selected_checkpoint_pass`,
which loads `best_model` into a fresh pass and requires per-sample Dice and
per-domain means to agree with `best_records` to 1e-6.

## 4. Clarification adopted

> The primary endpoint is computed from the **stored `best_records`** of the
> selected epoch. A recomputed VAL pass from the selected checkpoint `best_model`
> must reproduce those records to within 1e-6 per sample; a larger divergence is
> treated as an integrity failure of the run, not as a scientific result.

Rationale for preferring (a): `best_records` is bound into the committed epoch
payload and therefore covered by the checkpoint SHA-256 and the recovery identity
chain. Reading it requires no inference, so the endpoint cannot drift through a
re-evaluation bug. The recomputed pass (b) is retained as a *verification* of (a),
never as a substitute.

## 5. Why this is not a protocol change

| Property | Preserved |
|---|---|
| Population | VAL808 only (`082c80b2…`) |
| Metric | per-image Dice, `(2TP+ε)/(2TP+FP+FN+ε)`, ε=1e-7, threshold 0.5 |
| Weighting | per-image mean within domain, then **unweighted** mean of four domains |
| Pairing | same seed, `C1-T` − `C1-C` |
| Seeds | three fixed seeds `[42, 123, 3407]`, averaged |
| Selection | frozen `phase20_macro_domain_mean_dice_v1`, tolerance 1e-12 |
| Interpretation | descriptive across three seeds; no population-level seed inference |
| Evidence class | development / selection-consumed VAL808 |

The clarification fixes **which stored artifact is read**, not what is estimated.
The estimand is unchanged, so no supervisor decision is required for the estimand.

## 6. Limitations that remain (carried forward, unchanged)

1. **Selection-consumed.** The endpoint is measured on the same VAL808 used to
   choose the epoch. It is the selection objective evaluated in-sample, carries
   optimistic selection bias, and supports no independent-generalization claim.
   This matches the frozen `claim_boundary`.
2. **Three seeds.** Sample SD on 2 degrees of freedom; descriptive dispersion of
   three downstream-retraining replicates only.
3. **Patient clustering only where identifiers exist.** Real `patient_id` exists
   only for KUB (267). ISIC/BUSI/KVASIR cluster on images, so uncertainty is
   understated where images share an unobserved patient. Must be disclosed.
4. **No C2/C3 inference.** This endpoint says nothing about safety, clinical
   utility, or the BARR router.

## 7. Disposition

`ENDPOINT_AMBIGUITY_RESOLVED_ADDITIVELY__ESTIMAND_UNCHANGED`

A future protocol revision may absorb this wording. Editing `protocol.json` now
is prohibited (it would change the frozen digest and void the release identity
chain), so the clarification lives here as a bound release artifact.
