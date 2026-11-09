# Phase 05 — Forensic Data Leakage & Duplicate Audit Report

- **Audit Status:** `PASS`
- **Sample-ID Overlap:** TRAIN ∩ VAL = 0 | TRAIN ∩ TEST = 0 | VAL ∩ TEST = 0
- **KUB Patient Overlap:** TRAIN ∩ VAL = 0 | TRAIN ∩ TEST = 0 | VAL ∩ TEST = 0 (N=711 unique patients)
- **patient-00360 Allocation:** 24 cases, strictly TRAIN
- **Exact TRAIN <-> VAL Image Duplicates:** 1 raw KUB image file collision (patient-00273 vs patient-00320)
- **Exact TRAIN <-> VAL Mask Duplicates:** 0
- **Perceptual Near-Duplicates (TRAIN <-> VAL):** 64 candidates under 64-bit DCT pHash (Hamming $\le$ 6)
- **TEST Content Governance:** Recomputed = NO | TEST image reads = 0 | TEST mask reads = 0 | TEST visualizations = 0
- **Pre-Lock TEST Evidence:** 157 TRAIN-TEST and 18 VAL-TEST candidate pairs preserved from historical diagnostic audit.
