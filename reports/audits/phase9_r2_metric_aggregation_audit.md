# Phase 9-R2 — Checkpoint-Selection Metric Aggregation Audit

**Status: PASS**  
**Scope: audit only; no retraining or extra epochs**

## Conclusion

Phase-9 checkpoint selection and early stopping used the scientifically intended **per-image VAL macro Dice**. The implementation does **not** take an equal-weight mean of batch means. It concatenates every image-level Dice value from all batches and then computes one mean across all 283 images.

The small difference between the checkpoint scalar (`0.7455300688743591`) and the later single-image evaluation CSV mean (`0.7455439340960021`) is not a batch-weighting error. The checkpoint scalar was measured with batches of four during AMP/CUDA validation, while the final CSV was generated later with one image per forward pass. Batched and single-image CUDA/AMP execution can produce slightly different logits and threshold outcomes, and the final reductions also use different floating-point paths.

## Validation aggregation implementation

1. `src/metrics/segmentation.py:7-15` computes `dice` with reduction dimensions excluding the batch dimension. Its result therefore contains one Dice value per image: `[Dice_1, ..., Dice_B]`.
2. `src/training/evaluator.py:12` appends that vector for every validation batch.
3. `src/metrics/segmentation.py:18-20` performs:

```python
return {
    key: torch.cat([batch[key] for batch in metric_batches]).mean().item()
    for key in metric_batches[0]
}
```

For 283 images and batch size 4, `torch.cat` creates a 283-element vector even though the 71st batch contains only 3 images. The subsequent mean is:

\[
\mathrm{VAL\ macro\ Dice}=\frac{1}{283}\sum_{i=1}^{283}\mathrm{Dice}_i.
\]

This is sample-weighted and exactly equivalent to true per-image macro Dice. It is not

\[
\frac{1}{71}\sum_{b=1}^{71}\mathrm{mean}(\mathrm{Dice\ in\ batch}_b),
\]

which would incorrectly give the final three-image batch the same weight as each four-image batch.

## Checkpoint selection and early stopping trace

`scripts/training/train_kub_baseline.py:154-155` obtains `val_info` directly from `trainer.validate(val_loader)`.

The same `val_info["dice"]` scalar is then used for all four purposes:

- **History:** lines 163-176 store it as `val_dice`.
- **Best-checkpoint decision:** lines 183-186 compare it with `best_val_dice`.
- **`best.pt`:** lines 198-199 save when that comparison improves.
- **Early stopping/patience:** line 188 passes it to `EarlyStopping.update`; `src/training/trainer.py:7-11` resets or increments the patience counter from that scalar.

There is no intervening or alternative aggregation.

## Exact final per-image result

Recomputed from the unchanged `reports/tables/phase9_unet_val_per_image.csv`:

- Rows: **283**
- Mean of `dice` using float64: **0.7455439340960021**
- Mean after representing the CSV values as torch float32: **0.7455438971519470**
- Checkpoint-selection scalar: **0.7455300688743591**
- Absolute difference (float64 CSV mean minus checkpoint scalar): **0.000013865221642928027**

## Reconstruction using the final CSV order

The existing table was grouped sequentially with batch size 4 and `shuffle=false`; no image or mask content was read.

| Quantity | Value |
|---|---:|
| True mean over 283 image Dice values | 0.7455439340960021 |
| Equal-weight mean of 71 batch means | 0.7458270253168174 |
| Sample-weighted mean of 71 batch means | 0.7455439340960021 |
| Final three-image batch mean | 0.8259418408075968 |
| Checkpoint-selection scalar | 0.7455300688743591 |

The equal-weight batch result differs from the checkpoint scalar by `0.0002969564424583071`; therefore the reported scalar did not arise from unweighted batch means.

The CSV reconstruction cannot reproduce the original checkpoint scalar exactly because the CSV values came from a later **single-image** forward-pass loop (`scripts/training/train_kub_baseline.py:231-248`), not from retained epoch-47 batch outputs. This is an inference-path numerical distinction, not a macro-aggregation convention.

## Available epoch evidence

- `history.csv` records 62 epoch-level Dice scalars. Each is the true sample-level macro produced by the concatenation implementation.
- Individual per-image values or predictions were **not** retained for every epoch.
- All epoch checkpoints were **not** retained; valid scientific checkpoints are `best.pt` (epoch 47) and `latest.pt` (epoch 62).
- Both checkpoints contain the same 62-entry aggregation history where applicable (`best.pt` contains history through epoch 47; `latest.pt` through epoch 62).

Because the recorded epoch scalar itself is protocol-correct, per-epoch predictions are not needed to establish selection correctness:

- Epoch 47 is the maximum recorded true macro Dice epoch.
- Epochs 48 through 62 are 15 consecutive non-improvements under that same true macro scalar.
- Therefore best epoch **47** and stop epoch **62** are both proven correct under the intended aggregation.

## Scientific decision

- Aggregation implementation: **sample-weighted — YES**
- True macro equivalent: **YES**
- Checkpoint selection protocol compliant: **YES**
- Early stopping protocol compliant: **YES**
- Corrective retraining required: **NO**
- Phase 9 remains **PASS**.

## Governance

- TEST content reads: **0**
- TEST metrics: **NONE**
- External data accessed: **NO**
- Experiment A modified: **NO**
- Phase 10 executed: **NO**
- Manifest guard: **PASS**
- Test lock: **PASS**

**STOP. No retraining was performed. Phase 10 was not begun.**
