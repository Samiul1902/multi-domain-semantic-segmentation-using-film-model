# Repository Script Inventory

Phase 7-R2 consolidated all one-off root scripts under `scripts/`. Reusable scientific logic remains under `src/`; notebooks import from `src/analysis/kub_object_size.py` rather than executing root helpers.

| Path | Classification | Purpose / safety status |
| :--- | :--- | :--- |
| `scripts/audit/audit_script.py`, `audit_v2.py`, `audit_v3.py` | AUDIT_HELPER | Historical dataset-discovery helpers |
| `scripts/audit/find_dup_images.py`, `leakage_audit.py`, `phase5_audit_script.py` | AUDIT_HELPER | Historical leakage audit helpers |
| `scripts/audit/phash_audit_execution.py`, `run_phash_fast.py` | AUDIT_HELPER | Perceptual duplicate audit helpers |
| `scripts/audit/reconcile_kub_patients.py` | AUDIT_HELPER | KUB patient-ID reconciliation helper |
| `scripts/maintenance/phase7r1_pipeline.py` | ACTIVE | Reconciled Phase-7 asset/provenance orchestration; no manifest writes |
| `scripts/maintenance/build_notebook_05.py` | ACTIVE | Builds the finalized Phase-7 notebook |
| `scripts/maintenance/build_notebook_04.py`, `run_phase6r2_analysis.py` | MAINTENANCE | Prior-phase reproducibility helpers |
| `scripts/legacy/build_phase5_artifacts.py`, `build_phase5r1_artifacts.py` | LEGACY | Superseded reporting generators |
| `scripts/legacy/freeze_audit_execution.py` | LEGACY | Historical metadata/freeze helper; not active |
| `scripts/legacy/run_phase6_part1.py`, `run_phase6_part2.py`, `run_phase6_part3.py` | SUPERSEDED | Superseded Phase-6 implementations |
| `scripts/legacy/run_phase7_analysis.py` | SUPERSEDED | Superseded Phase-7 implementation |
| `scripts/legacy/manifest/build_phase4_v2_manifests.py` | DO_NOT_RUN_AFTER_FREEZE | Can rewrite manifests |
| `scripts/legacy/manifest/manifest_builder_final.py` | DO_NOT_RUN_AFTER_FREEZE | Can rewrite manifests |
| `scripts/legacy/manifest/manifest_builder_final_v2.py` | DO_NOT_RUN_AFTER_FREEZE | Historical manifest builder |
| `scripts/legacy/manifest/manifest_rebuilder.py` | DO_NOT_RUN_AFTER_FREEZE | Historical manifest rebuilder |

See `scripts/README.md` and `scripts/legacy/manifest/README.md`. No manifest-changing script is part of the active notebook or source workflow.
