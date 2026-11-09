# Phase 10 DeepLabV3+ Clean-v3 Training Start Audit

- Experiment: `phase10_kub_deeplabv3plus_seed42_512_clean_v3`
- Historical: `phase10_kub_deeplabv3plus_seed42_512` (deeplabv3plus_resnet50_os16)
- Backbone: resnet50, pretrained=**False**, output_stride=16, ASPP(6,12,18), no aux head
- Parameter count: **40,340,769** (proven by instantiation + state-dict match)
- Config SHA: `a5220e3135618513a71e0094197b2cffe0aef9334f7d53e39642c7a00ddd5b57`
- Start UTC: 2026-09-20T17:07:49.662670+00:00
- Gates all pass: True
- TEST reads: 0 | Unauthorized material diffs: 0
