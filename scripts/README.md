# Project Scripts

Root-level one-off scripts were consolidated here during Phase 7-R2. Scientific source code remains under `src/`; these scripts preserve audit and historical provenance.

- `audit/`: read-only audit helpers.
- `maintenance/`: current maintenance/report orchestration scripts.
- `legacy/`: superseded one-off builders and report generators.
- `legacy/manifest/`: manifest-changing historical scripts. **DO_NOT_RUN_AFTER_PHASE4_FREEZE.**

No script in `legacy/manifest/` is part of the active workflow. The authoritative `phase4_v2` manifests are protected by `src/utils/manifest_guard.py`.
