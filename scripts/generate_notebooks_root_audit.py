import hashlib
import csv
from pathlib import Path

def compute_sha256(p: Path) -> str:
    if p.is_dir():
        return "DIRECTORY"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

root = Path("notebooks")
items = sorted(list(root.iterdir()))

# Definitive classifications
classifications = {
    "00_project_initialization.ipynb": {
        "scientific_phase": "01",
        "canonical_status": "PROVENANCE_ORIGINAL",
        "action": "KEEP_PROVENANCE",
        "phasewise_exists": "YES (phase_01)",
        "reason": "Original foundational initialization notebook from Phase 01 development."
    },
    "00_project_visual_index.ipynb": {
        "scientific_phase": "PROJECT_WIDE",
        "canonical_status": "REVIEWER_INDEX_LEGACY",
        "action": "KEEP_REVIEWER",
        "phasewise_exists": "YES (00_PHASEWISE_PROJECT_INDEX.ipynb)",
        "reason": "Executed top-level project visual navigation index from NV-2."
    },
    "01_environment_and_data_audit.ipynb": {
        "scientific_phase": "02",
        "canonical_status": "PROVENANCE_ORIGINAL",
        "action": "KEEP_PROVENANCE",
        "phasewise_exists": "PENDING (phase_02)",
        "reason": "Original Phase 02 CUDA and environment certification notebook."
    },
    "01_trained_model_results_visual_scorecard.ipynb": {
        "scientific_phase": "PROJECT_WIDE",
        "canonical_status": "REVIEWER_SCORECARD_LEGACY",
        "action": "KEEP_REVIEWER",
        "phasewise_exists": "NO",
        "reason": "Executed trained model visual scorecard across all historical phases."
    },
    "02_dataset_discovery.ipynb": {
        "scientific_phase": "03",
        "canonical_status": "PROVENANCE_ORIGINAL",
        "action": "KEEP_PROVENANCE",
        "phasewise_exists": "PENDING (phase_03)",
        "reason": "Original Phase 03 dataset discovery and multi-domain inventory notebook."
    },
    "03_kub_forensic_audit.ipynb": {
        "scientific_phase": "05",
        "canonical_status": "PROVENANCE_ORIGINAL",
        "action": "KEEP_PROVENANCE",
        "phasewise_exists": "PENDING (phase_05)",
        "reason": "Original Phase 05 KUB forensic duplicate and leakage audit notebook."
    },
    "03_leakage_and_split_audit.ipynb": {
        "scientific_phase": "04",
        "canonical_status": "PROVENANCE_ORIGINAL",
        "action": "KEEP_PROVENANCE",
        "phasewise_exists": "PENDING (phase_04)",
        "reason": "Original Phase 04 split manifest and patient leakage audit notebook."
    },
    "04_kub_characterization.ipynb": {
        "scientific_phase": "06",
        "canonical_status": "PROVENANCE_ORIGINAL",
        "action": "KEEP_PROVENANCE",
        "phasewise_exists": "PENDING (phase_06)",
        "reason": "Original Phase 06 KUB clinical and FOV characterization notebook."
    },
    "05_kub_object_size_taxonomy.ipynb": {
        "scientific_phase": "07",
        "canonical_status": "PROVENANCE_ORIGINAL",
        "action": "KEEP_PROVENANCE",
        "phasewise_exists": "PENDING (phase_07)",
        "reason": "Original Phase 07 stone object size taxonomy and quartiles notebook."
    },
    "06_kub_baseline_infrastructure.ipynb": {
        "scientific_phase": "08",
        "canonical_status": "PROVENANCE_ORIGINAL",
        "action": "KEEP_PROVENANCE",
        "phasewise_exists": "PENDING (phase_08)",
        "reason": "Original Phase 08 baseline model factory and smoke-test harness notebook."
    },
    "07_kub_unet_baseline_training.ipynb": {
        "scientific_phase": "09",
        "canonical_status": "PROVENANCE_ORIGINAL",
        "action": "KEEP_PROVENANCE",
        "phasewise_exists": "YES (phase_09)",
        "reason": "Original Phase 09 U-Net baseline training and validation notebook."
    },
    "08_kub_baseline_comparison.ipynb": {
        "scientific_phase": "10",
        "canonical_status": "PROVENANCE_ORIGINAL",
        "action": "KEEP_PROVENANCE",
        "phasewise_exists": "YES (phase_10)",
        "reason": "Original Phase 10 baseline comparison (UNet vs UNet++ vs SegNet) notebook."
    },
    "09_kub_failure_analysis.ipynb": {
        "scientific_phase": "11",
        "canonical_status": "PROVENANCE_ORIGINAL",
        "action": "KEEP_PROVENANCE",
        "phasewise_exists": "YES (phase_11)",
        "reason": "Original Phase 11 KUB baseline failure analysis notebook."
    },
    "09b_kub_manual_prediction_demo.ipynb": {
        "scientific_phase": "11",
        "canonical_status": "PROVENANCE_DEMO",
        "action": "KEEP_PROVENANCE",
        "phasewise_exists": "NO",
        "reason": "Phase 11 manual prediction demonstration on baseline models."
    },
    "10_kub_oracle_roi_upper_bound.ipynb": {
        "scientific_phase": "12",
        "canonical_status": "PROVENANCE_ORIGINAL",
        "action": "KEEP_PROVENANCE",
        "phasewise_exists": "YES (phase_12)",
        "reason": "Original Phase 12 Oracle ROI upper bound analysis notebook."
    },
    "11_kub_predicted_roi_localizer.ipynb": {
        "scientific_phase": "13",
        "canonical_status": "PROVENANCE_ORIGINAL",
        "action": "KEEP_PROVENANCE",
        "phasewise_exists": "YES (phase_13)",
        "reason": "Original Phase 13 predicted ROI localizer exploration notebook."
    },
    "11b_kub_learned_localizer.ipynb": {
        "scientific_phase": "13",
        "canonical_status": "PROVENANCE_EXPLORATORY",
        "action": "KEEP_PROVENANCE",
        "phasewise_exists": "YES (phase_13)",
        "reason": "Phase 13 learned localizer (CenterNet pilot) intermediate notebook."
    },
    "11c_kub_final_localizer_redesign.ipynb": {
        "scientific_phase": "13",
        "canonical_status": "PROVENANCE_STAGE4D",
        "action": "KEEP_PROVENANCE",
        "phasewise_exists": "YES (phase_13)",
        "reason": "Phase 13 Stage 4D final localizer redesign and tuning notebook."
    },
    "12_phase14_15_gate_closure.ipynb": {
        "scientific_phase": "14/15",
        "canonical_status": "PROVENANCE_GATE",
        "action": "KEEP_PROVENANCE",
        "phasewise_exists": "NO",
        "reason": "Historical Phase 14/15 closure gate audit and transition notebook."
    },
    "13_phase14_regional_refiner_diagnostic.ipynb": {
        "scientific_phase": "14",
        "canonical_status": "CANONICAL_FROZEN",
        "action": "KEEP_CANONICAL",
        "phasewise_exists": "YES (phase_14)",
        "reason": "Authoritative frozen Phase 14 regional refiner diagnostic provenance notebook."
    },
    "phasewise": {
        "scientific_phase": "PHASES_00_TO_40",
        "canonical_status": "REVIEWER_PRIMARY_LAYER",
        "action": "KEEP_REVIEWER",
        "phasewise_exists": "N/A (IS_PHASEWISE)",
        "reason": "Authoritative 41-phase reviewer navigation tree and executed companion notebooks."
    },
    "reports": {
        "scientific_phase": "ARTIFACT_OUTPUTS",
        "canonical_status": "REDUNDANT_OUTPUT_DIR",
        "action": "SAFE_ARCHIVE_CANDIDATE",
        "phasewise_exists": "N/A",
        "reason": "Contains duplicate generated figure outputs created during earlier notebook executions; retain as archive candidate."
    },
    "retrospective": {
        "scientific_phase": "PHASES_09_10",
        "canonical_status": "REVIEWER_COMPANION",
        "action": "KEEP_REVIEWER",
        "phasewise_exists": "YES (phase_09, phase_10)",
        "reason": "Executed visual companion notebook for baseline models from NV-2."
    }
}

records = []
for item in items:
    name = item.name
    t = "DIR" if item.is_dir() else "FILE"
    sha = compute_sha256(item)
    meta = classifications.get(name, {
        "scientific_phase": "UNKNOWN",
        "canonical_status": "UNKNOWN",
        "action": "UNKNOWN",
        "phasewise_exists": "UNKNOWN",
        "reason": "Unclassified item."
    })
    
    records.append({
        "name": name,
        "type": t,
        "scientific_phase": meta["scientific_phase"],
        "canonical_status": meta["canonical_status"],
        "sha256": sha,
        "phasewise_exists": meta["phasewise_exists"],
        "action": meta["action"],
        "reason": meta["reason"]
    })

# Write CSV
out_csv = Path("reports/audits/notebooks_root_cleanup_audit.csv")
out_csv.parent.mkdir(parents=True, exist_ok=True)
with open(out_csv, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "type", "scientific_phase", "canonical_status", "sha256", "phasewise_exists", "action", "reason"])
    writer.writeheader()
    writer.writerows(records)

# Write Markdown
out_md = Path("reports/audits/notebooks_root_cleanup_audit.md")
md_lines = [
    "# Notebooks Root Directory Cleanup & Provenance Audit",
    "",
    f"- **Total Cataloged Items in `notebooks/`:** {len(records)}",
    "- **Generated At:** 2026-09-19",
    "- **Preservation Principle:** No scientific notebooks or figures are deleted. Legacy notebooks are preserved as scientific provenance.",
    "",
    "## 1. Classification Summary",
    ""
]

from collections import Counter
counts = Counter([r["action"] for r in records])
for act, cnt in counts.most_common():
    md_lines.append(f"- **{act}:** {cnt}")

md_lines.extend([
    "",
    "## 2. Immediate Directory Items Audit Table",
    "",
    "| Name | Type | Phase | Action | Canonical Status | Phasewise Exists | Reason |",
    "| :--- | :---: | :---: | :--- | :--- | :---: | :--- |"
])

for r in records:
    sha_disp = f"`{r['sha256'][:12]}...`" if r['sha256'] != "DIRECTORY" else "DIR"
    md_lines.append(f"| `{r['name']}` | {r['type']} | {r['scientific_phase']} | **{r['action']}** | {r['canonical_status']} | {r['phasewise_exists']} | {r['reason']} |")

out_md.write_text("\n".join(md_lines), encoding="utf-8")
print("Notebooks root cleanup audit generated successfully!")

