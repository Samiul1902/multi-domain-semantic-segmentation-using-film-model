# Phase 13 — KUB Predicted ROI Proposal / Localizer Development

**Status: PASS**

Selected GT-free configuration: threshold `0.5`, margin `0.15`, Top-K `3`, NMS `0.3`. Recall90 `0.743590`; TINY recall90 `0.684932`; mean proposals/image `1.556604`; mean ROI area fraction `0.003091`.

Phase-14 gate: **WEAK**. No globally missed TINY component (0/16) and no global-empty case (0/7) was usefully localized. GT was used only after GT-free proposal generation for evaluation. No refiner was trained. TEST reads: 0; Phase 14 not executed.

Notebook SHA-256: `e5a6ddc16695523e89b876060b70ada3bf23ab37726281ea39eba66e3608d62a`
