# Phase 35 v1.0d - Grad-CAM Target-Mask Rank-Safety Amendment

**Revision:** `ra_medfilm_barr_phase35_interpretability_v1_0d`
**Classification:** `PRE_EXECUTION_GRADCAM_TARGET_RANK_SAFETY_IMPLEMENTATION_AMENDMENT__NO_SCIENTIFIC_PROTOCOL_CHANGE`
**Method:** RA-MedFiLM-BARR

## 1. Defect repaired
`PHASE35_V1_0B_GRADCAM_TARGET_MASK_RANK_INCOMPATIBILITY` (prospectively disclosed in v1.0c). The frozen `gradcam_target_scalar` performed
`logits[mask]`: rank-2 Boolean indexing against rank-4 logits. Canonical G logits are
`[1,1,512,512]`; the canonical scientific mask `build_target_mask(p_global >= 0.50)` is rank-2
`[512,512]`. PyTorch requires the mask to match the indexed tensor's leading dimensions, so the
scientific Grad-CAM target scalar raised `IndexError` deterministically.

**Reproduced** in this revision (model-free, CPU): `D1_frozen_v1_0b_logits_mask_indexing_reproduced`
-> `IndexError`.

## 2. Frozen scientific intent (unchanged)
```
M_pred = persisted p_global >= 0.50
if M_pred non-empty:  T = mean(foreground logits under M_pred)
else:                 T = mean(foreground logits over the full field)
```

## 3. Prospective target-scalar contract (frozen by this revision)
| item | contract |
|---|---|
| logits rank | 4 |
| logits shape | `[1,1,H,W]` |
| batch | 1 |
| output channels | 1 |
| mask rank | 2 |
| mask shape | `[H,W]` |
| mask dtype | Boolean |

The rank-2 mask is the canonical representation. It is **never** broadcast, expanded to unrelated
batch/channel dimensions, created from the current forward, replaced by the ROI-0.30 mask, replaced
by GT, or replaced by a sigmoid probability target.

## 4. Repaired implementation
`gradcam_target_scalar_rank_safe(logits, mask)` in `scripts/analysis/phase35_interpretability_execution_v1_0d.py`:

```
logits_f = validate_logits(logits)      # rank 4, batch 1, channels 1
mask_t   = validate_mask(logits_f, mask)  # rank 2, shape == (H,W), dtype bool
foreground_logits = logits_f[0, 0]
if bool(mask_t.any()):
    return foreground_logits[mask_t].mean()
return foreground_logits.mean()
```

Explicit `raise` is used rather than `assert` so the fail-closed property survives `python -O`;
the semantics are identical to the specified assert-based contract.

`gradcam_gradient_enabled_rank_safe` is the frozen v1.0b per-sample gradient path with the **single**
target-scalar call rebound. Hooks, `torch.enable_grad()`, autocast fp16, `torch.autograd.grad`,
`alpha`/ReLU/bilinear/`align_corners`, and `cam_normalize` are unchanged.

## 5. Call-graph binding (static evidence)
| mode | reaches repaired helper |
|---|---|
| `mode_gradcam` | YES (`mode_gradcam` -> `gradcam_path_contract` -> `gradcam_target_scalar_rank_safe`) |
| `mode_science` | YES (`mode_science` -> `gradcam_path_contract` -> repaired helper) |
| `mode_smoke` | YES (`mode_smoke` -> `smoke_gradcam` -> `gradcam_gradient_enabled_rank_safe` -> repaired helper) |
| frozen defective `logits[mask]` path | UNREACHABLE from v1.0d |

`film` and `router` remain bound verbatim to `V0B.mode_film` / `V0B.mode_router`.

## 6. Smoke now validates the SCIENTIFIC rank contract
The v1.0c rank-4 synthetic-mask workaround is **removed**. The v1.0d smoke builds a rank-2
`[512,512]` Boolean mask (centred square rows 192:320, columns 192:320) and consumes it through the
**same** repaired helper that scientific Grad-CAM uses. All other smoke counters are unchanged.

## 7. Static preflight (zero execution)
`scripts/analysis/phase35_execution_preflight_v1_0d.py` -> `reports/audits/phase35_execution_source_static_preflight_v1_0d.json`:
**96 checks, 0 failed**
(54 original + 22 v1.0d amendment + 20 rank-safety),
with 34 predecessors verified byte-identical.

## 8. Model-free unit tests
`scripts/analysis/phase35_gradcam_target_rank_unit_v1_0d.py` -> `reports/audits/phase35_gradcam_target_rank_unit_v1_0d.json`: **11 tests, 0 failed**, CPU-only,
no model, no checkpoint, no data.

## 9. Locks
Phase35 scientific execution `NOT_STARTED`; Phase36 `NOT_STARTED`; TEST `LOCKED_UNTIL_PHASE39`;
ROUTER_HOLDOUT `OPENED_AND_FROZEN`. Scientific Grad-CAM remains **not authorized** pending a
successful v1.0d synthetic smoke.
