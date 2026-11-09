# Phase 04 — Canonical Manifest & Split Integrity Audit

- **Audit Status:** `PASS`
- **Authoritative Total Population:** 8,441 paired cases
- **Split Distribution:** TRAIN: 5,913 (70.05%) | VAL: 845 (10.01%) | TEST: 1,683 (19.94%)
- **Manifest Guard Integration:** PASS (`src/utils/manifest_guard.py`)
- **Sample Disjointness:** TRAIN ∩ VAL = 0 | TRAIN ∩ TEST = 0 | VAL ∩ TEST = 0
- **KUB Patient Disjointness:** 318 TRAIN | 111 VAL | 282 TEST (0 patient-level overlap)
- **patient-00360 Audit:** 24 cases, strictly TRAIN
- **Governance:** TEST metadata read allowed; TEST image/mask content reads = 0.
