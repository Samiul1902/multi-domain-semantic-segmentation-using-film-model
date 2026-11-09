# Phase 13 Part 1A — Clean-v3 Localizer Protocol Candidate

- Status: **PROSPECTIVE_FREEZE_CANDIDATE_AWAITING_SUPERVISOR**
- Manifest `phase4_v3` · taxonomy `kub_size_clean_v3_v1`

## Candidate population (clean-v3)

- TRAIN FULL_FIELD: 770 images / 1161 components
- VAL FULL_FIELD: 103 images / 152 components · strata {'TINY': 72, 'SMALL': 28, 'MEDIUM': 36, 'LARGE': 16}
- ROI acquisitions: excluded (ROI_NOT_PRIMARY_BINNED)

## Retention arithmetic

- historical v2: {'T_g': 0.780822, 'T_o': 1.0, 'T_p': 0.890411, 'G': 0.219178, 'R': 0.5}
- clean-v3: NOT_YET_COMPUTED — must be recomputed on 103/152

## Supervisor decisions required

- Re-derivation of the clean-v3 hard sets (do NOT reuse the v2 16 Tiny / 7 global-empty sets).
- Approval of the clean-v3 localizer architecture/resolution/sigma candidate (KUBLocalizer, 128 output, sigma 0.75).
- Approval of the inference output-resolution contract that fixes the heatmap_resolution omission defect.
- Fixing (or explicitly declining to fix) the train/inference proposal-distribution mismatch for any future regional integration.
- Whether to freeze numeric thresholds for gate dimension B, or keep B descriptive for the Phase-13 decision.

## Explicitly not done

- No localizer training.
- No localizer inference.
- No proposal generation.
- No Phase-14 execution.
- No TEST access.
- No winner declared; no reference architecture selected.
- No regional-mechanism promotion; gate remains NOT_DECIDED.

## Governance

- TEST reads **0** · training **0** · inference **0** · proposals **0**
- No winner declared · no reference model selected · gate NOT_DECIDED

**Conclusion.** A prospective clean-v3 localizer/proposal protocol candidate is frozen for supervisor review. Nothing has been executed.
