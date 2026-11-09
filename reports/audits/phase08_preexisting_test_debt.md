# Phase 08 — Pre-existing Test Debt

These are **unrelated** historical Phase-13/14 issues. They were **not** repaired in
Phase 08 Part 1B because they do not block Phase-09 baseline infrastructure.

| Test file | Observed | Affected phase | Module | Required by Phase 09 | Module modified | Disposition |
|---|---|---|---|---|---|---|
| `tests/test_phase14_part1.py` | HANGS (never completes) | Phase 14 | `Phase-14 regional/refiner work` | False | None | DEFER_TO_AFFECTED_CLEAN_RERUN_PHASE |
| `tests/test_predicted_roi.py` | 3 failures | Phase 13 | `src/inference/predicted_roi.py` | False | False | DEFER_TO_AFFECTED_CLEAN_RERUN_PHASE |
| `tests/test_kub_localizer.py` | 1 failure | Phase 13 | `src/models/kub_localizer.py` | False | False | DEFER_TO_AFFECTED_CLEAN_RERUN_PHASE |

> **Note:** the full repository suite does **not** pass. `pytest tests/` never
> completes because `tests/test_phase14_part1.py` hangs. Run scoped test files instead.
