# Project Cleanup & Archive Plan (Non-Destructive)

## 1. Principles
- **Zero Deletion Guarantee:** No files are deleted during automated cleanup. All operational files are categorized as `KEEP` or `ARCHIVE_CANDIDATE`.
- **Canonical Immutability:** Historical notebooks and split manifests are permanently protected.
- **Auditability:** Any prospective archival requires supervisor approval.

## 2. File Action Categories

| Pattern | Category | Action | Rationale |
| :--- | :--- | :--- | :--- |
| `reports/audits/*_console.log` | log | **ARCHIVE_CANDIDATE** | Historical execution stdout/stderr logs; preserve in archive folder for audit trail. |
| `reports/audits/*_error.log` | log | **ARCHIVE_CANDIDATE** | Historical execution error logs; preserve in archive folder. |
| `reports/audits/stage4d_geometry_output*.json` | intermediate_data | **KEEP** | Intermediate geometry outputs supporting Stage-4D localizer tuning. |
| `reports/audits/phase13b_stage4c_r2_audit.txt` | audit_note | **KEEP** | Historical supervisor audit note for Stage-4C component mapping. |
| `notebooks/retrospective/*` | notebook | **KEEP** | Reviewer companion visual notebooks; keep accessible to external reviewers. |
| `notebooks/phasewise/*` | notebook | **KEEP** | Authoritative 41-phase reviewer navigation tree. |
| `notebooks/13_phase14_regional_refiner_diagnostic.ipynb` | canonical_notebook | **KEEP_STRICTLY_IMMUTABLE** | Canonical Phase-14 frozen provenance notebook (SHA: b5b329d1...). |
| `checkpoints/*` | weights | **KEEP** | Trained baseline, localizer, and refiner weights required for verification. |
| `manifests/*` | data_manifest | **KEEP_STRICTLY_IMMUTABLE** | Authoritative train/val/test split manifests. |