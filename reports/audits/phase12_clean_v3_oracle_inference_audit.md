# Phase 12 Part 1B — CLEAN-v3 Oracle Inference Audit

- Created: 2026-09-21T01:01:21.006917+00:00
- Protocol-frozen SHA: `f5227bdd67ec780ccd4c520a9bf1576601164939d2ff4132680885bc35124a48`
- README restored SHA: `5f8db1300364a45cf37997fcb3c3094ba875782f539b32a361bfc987780d0990`

## Population

- FULL_FIELD cases: **103** · native GT components: **152**
- Models: 4 · crop inferences/model: {'UNet': 152, 'Attention U-Net': 152, 'UNet++': 152, 'DeepLabV3+': 152}
- Reference model selected: **False**

## Global reproduction gate (EVALUATION_512 vs Phase-11)

| Model | max abs Dice diff | pass 1e-4 |
|---|---|---|
| UNet | 1.110e-16 | PASS |
| Attention U-Net | 1.110e-16 | PASS |
| UNet++ | 1.110e-16 | PASS |
| DeepLabV3+ | 1.110e-16 | PASS |

## Native-space macro Dice by variant

| Model | GLOBAL_NATIVE | FLOAT_GLOBAL_RETAINED (primary) | FLOAT_CROP_ONLY (secondary) | LEGACY_UINT8_CROP_ONLY |
|---|---|---|---|---|
| UNet | 0.594180 | 0.724722 | 0.793230 | 0.795107 |
| Attention U-Net | 0.629805 | 0.699595 | 0.773615 | 0.774814 |
| UNet++ | 0.640516 | 0.726679 | 0.773039 | 0.772996 |
| DeepLabV3+ | 0.560251 | 0.750372 | 0.797875 | 0.797986 |

## Native object recall by variant

| Model | GLOBAL | PRIMARY | CROP_ONLY | LEGACY |
|---|---|---|---|---|
| UNet | 0.786408 | 0.995146 | 0.995146 | 0.995146 |
| Attention U-Net | 0.854369 | 0.995146 | 0.995146 | 0.995146 |
| UNet++ | 0.839806 | 0.995146 | 0.995146 | 0.995146 |
| DeepLabV3+ | 0.762136 | 1.000000 | 1.000000 | 1.000000 |

## Float-vs-legacy map-back sensitivity

| Model | mean abs Dice diff | max abs Dice diff |
|---|---|---|
| Attention U-Net | 2.683e-03 | 1.370e-02 |
| DeepLabV3+ | 8.631e-04 | 5.205e-03 |
| UNet | 2.828e-03 | 1.852e-02 |
| UNet++ | 2.256e-03 | 1.755e-02 |

> The float-vs-legacy difference conflates (a) uint8 quantisation and (b) the PIL-vs-torch
> bilinear resample convention. It is a `HISTORICAL_NUMERICAL_SENSITIVITY_ONLY` diagnostic.

## Governance

- TEST reads: **0** · training epochs: **0** · optimizer steps: **0**
- Scientific parameter changes after freeze: **0**
- Unauthorized variants created: **0**
- Statistical testing: **False** · Phase 13 started: **False**

> **No final Phase-12 mechanism conclusion is issued in Part 1B.** Raw evidence only.

## Status: PASS