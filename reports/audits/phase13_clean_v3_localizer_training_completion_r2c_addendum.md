# PHASE-13 PART-1B — TRAINING-COMPLETION R2C ADDENDUM

**Provenance synthesis only.** The original completion audit is **not overwritten**.

- original completion audit: `reports/audits/phase13_clean_v3_localizer_training_completion.json`
- original SHA: `4e48afe5e9c4f81db975d31ba60bcf130a48d016073766f56241973b77eabcd8`
- original reported protocol: `R2 + R2A_LOSS_BINDING` (emitted by the runner before R2C existed)

## Final effective protocol lineage

```
R2
+ R2A_LOSS_BINDING
+ NON_SCIENTIFIC_PROVENANCE_BINDING
+ R2B  (provenance; superseded for primary selection)
+ R2C_HISTORICAL_EXECUTING_COVERAGE_ARBITRATION   <-- canonical for PRIMARY selection
```

- primary coverage semantics: `HISTORICAL_EXECUTING_BBOX_COVERAGE`
- pixel coverage role: `SECONDARY_COVERAGE_SENSITIVITY_ONLY`

## Training outcome

| item | value |
|---|---|
| best epoch | **53** |
| final epoch | **68** |
| early-stop patience | 15 |
| termination | `EARLY_STOPPING_PATIENCE` |
| final bad_epochs | **15** |
| canonical best tuple | `(0.6805555555555556, 0.5986842105263158, -0.004846047236646169, -1.9175469095890338)` |

### Canonical bbox metrics at best epoch

| metric | value |
|---|---|
| tiny_recall90 | 0.6805555555555556 |
| overall_recall90 | 0.5986842105263158 |
| mean_roi_area_fraction | 0.004846047236646169 |
| val_loss | 1.9175469095890338 |

### Canonical secondary bbox diagnostics

| metric | value |
|---|---|
| hard_tiny_recovered90 | 4 / 15 |
| global_empty_images_covered90 | 1 / 5 |
| multi_component_recall90 | 0.5714285714285714 |
| mean_proposals_per_image | 4.796116504854369 |

### Pixel sensitivity (NEVER selection metrics)

| metric | value |
|---|---|
| tiny_recall90 | 0.6944444444444444 |
| overall_recall90 | 0.6644736842105263 |

## Artifact bindings

| artifact | SHA-256 |
|---|---|
| canonical selection sidecar | `77449ec3c49264c1f76958efc3eae95c343727f856399ad86cf07f7d5552266e` |
| best-epoch verification | `c48592f5013b5b84b7524535fd4ccd55bd9690ab56bf51c07aed345f2e975db5` |
| canonical replay verification | `c4b13aaf9909edb08e3e29bee8fba00f276dbc2111a9703044fe24367b65172c` |
| final-best integrity | `6a4c5748ccded2758e6d7c530758d5fb2382de4c71fa7e7cd57e393f4ec6507e` |
| executing runner | `00ff82447f1f83935c042ea4fa19ad4f05956c48a80c474eaa98fc643bf79913` |
| best.pt | `7673c34a2f2c86eca2e45c1bc6abe77842d17cd09f122f2da0f2d414ca492273` |
| latest.pt | `791abe027cb63ea81d9fcaea1e7081536d80382553e1e5129d7f80e89eae307c` |
| history.csv | `344cfc016fd88e7e697c6afa0ffbf839b3d3b3c16b54024dc3537586528d4c5b` |
| config | `922ff26916c1f7ebea0ea526fbaa6adbb9a7419f1f08b16d33ed5df049c4c8bf` |
| R2 / R2A / provenance | `ab451e03…` / `f3aececf…` / `436831db…` |
| R2B / R2C | `5574cd60…` / `aa0f1baf…` |

## Side-effect counts

| counter | value |
|---|---|
| grid configurations evaluated | **0** |
| TEST reads | **0** |
| scientific hyperparameter changes during training | **0** |

## History governance

Rows 1–31 preserved unmodified. Row 31's legacy primary fields remain **pixel-based
and raw**. The authoritative checkpoint-selection reconstruction is the sidecar
`reports/tables/phase13_part1b_canonical_selection_history.csv`.

No training. No inference. No proposal generation.
