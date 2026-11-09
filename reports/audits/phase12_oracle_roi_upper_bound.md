# Phase 12 — KUB Oracle ROI / Zoom Upper-Bound Study

**Status: PASS**

Frozen UNet++; FULL_FIELD VAL only; component-wise GT-localized Oracle; primary margin 25%; threshold 0.5. GT is not model input.

Global macro Dice `0.652776413200` → Oracle25 `0.775736153740`. TINY recall `0.780821917808` → `0.986301369863`; 15/16 global TINY misses recovered. Empty predictions 7 → 0.

Oracle FP is constrained by GT-derived crops and is not a fair deployable FP comparison. Phase-13 gate: **YES**, while no claim is made that predicted ROI will reproduce the Oracle result. TEST reads: 0; external: false; training: false; Phase 13 not executed.

Notebook SHA-256: `2b0205bac81fe11ee9d33965e000b461419487aaf8147c1fa95b16ef6f6c0b42`
