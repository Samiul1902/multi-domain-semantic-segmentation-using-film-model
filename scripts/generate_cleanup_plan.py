import csv
from pathlib import Path

# The cleanup plan categorizes files for long-term organization without deleting anything now.
# Actions: KEEP, ARCHIVE_CANDIDATE, DELETE_AFTER_SUPERVISOR_APPROVAL

cleanup_items = [
    {
        "pattern": "reports/audits/*_console.log",
        "category": "log",
        "action": "ARCHIVE_CANDIDATE",
        "rationale": "Historical execution stdout/stderr logs; preserve in archive folder for audit trail."
    },
    {
        "pattern": "reports/audits/*_error.log",
        "category": "log",
        "action": "ARCHIVE_CANDIDATE",
        "rationale": "Historical execution error logs; preserve in archive folder."
    },
    {
        "pattern": "reports/audits/stage4d_geometry_output*.json",
        "category": "intermediate_data",
        "action": "KEEP",
        "rationale": "Intermediate geometry outputs supporting Stage-4D localizer tuning."
    },
    {
        "pattern": "reports/audits/phase13b_stage4c_r2_audit.txt",
        "category": "audit_note",
        "action": "KEEP",
        "rationale": "Historical supervisor audit note for Stage-4C component mapping."
    },
    {
        "pattern": "notebooks/retrospective/*",
        "category": "notebook",
        "action": "KEEP",
        "rationale": "Reviewer companion visual notebooks; keep accessible to external reviewers."
    },
    {
        "pattern": "notebooks/phasewise/*",
        "category": "notebook",
        "action": "KEEP",
        "rationale": "Authoritative 41-phase reviewer navigation tree."
    },
    {
        "pattern": "notebooks/13_phase14_regional_refiner_diagnostic.ipynb",
        "category": "canonical_notebook",
        "action": "KEEP_STRICTLY_IMMUTABLE",
        "rationale": "Canonical Phase-14 frozen provenance notebook (SHA: b5b329d1...)."
    },
    {
        "pattern": "checkpoints/*",
        "category": "weights",
        "action": "KEEP",
        "rationale": "Trained baseline, localizer, and refiner weights required for verification."
    },
    {
        "pattern": "manifests/*",
        "category": "data_manifest",
        "action": "KEEP_STRICTLY_IMMUTABLE",
        "rationale": "Authoritative train/val/test split manifests."
    }
]

out_csv = Path("reports/audits/project_cleanup_plan.csv")
with open(out_csv, "w", encoding="utf-8", newline="") as cf:
    writer = csv.DictWriter(cf, fieldnames=["pattern", "category", "action", "rationale"])
    writer.writeheader()
    writer.writerows(cleanup_items)

out_md = Path("reports/audits/project_cleanup_plan.md")
md_lines = [
    "# Project Cleanup & Archive Plan (Non-Destructive)",
    "",
    "## 1. Principles",
    "- **Zero Deletion Guarantee:** No files are deleted during automated cleanup. All operational files are categorized as `KEEP` or `ARCHIVE_CANDIDATE`.",
    "- **Canonical Immutability:** Historical notebooks and split manifests are permanently protected.",
    "- **Auditability:** Any prospective archival requires supervisor approval.",
    "",
    "## 2. File Action Categories",
    "",
    "| Pattern | Category | Action | Rationale |",
    "| :--- | :--- | :--- | :--- |"
]

for item in cleanup_items:
    md_lines.append(f"| `{item['pattern']}` | {item['category']} | **{item['action']}** | {item['rationale']} |")

out_md.write_text("\n".join(md_lines), encoding="utf-8")
print("Project cleanup plan generated successfully!")

