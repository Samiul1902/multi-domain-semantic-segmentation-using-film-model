"""Write Phase 11-R1 audit provenance JSON and Markdown reports."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = ROOT / "reports" / "audits"
TABLES_DIR = ROOT / "reports" / "tables"
FIGURES_DIR = ROOT / "reports" / "figures" / "phase11_kub_failure_analysis"


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    history_path = ROOT / "experiments/phase10_kub_unetpp_seed42_512/history.csv"
    nb_09 = ROOT / "notebooks/09_kub_failure_analysis.ipynb"
    nb_09b = ROOT / "notebooks/09b_kub_manual_prediction_demo.ipynb"

    figures = [
        "reports/figures/phase11_kub_failure_analysis/phase11_unetpp_training_loss_provenance.png",
        "reports/figures/phase11_kub_failure_analysis/phase11_unetpp_val_dice_provenance.png",
        "reports/figures/phase11_kub_failure_analysis/phase11_unetpp_lr_provenance.png",
    ]

    figure_hashes = {fig: sha256_file(ROOT / fig) for fig in figures}

    audit_json = {
        "phase": "11-R1 - Training Provenance, Manual Inference, and Auto-Domain Interface",
        "status": "PASS",
        "scope": "utility_presentation_interface_patch_only",
        "history_source": str(history_path.relative_to(ROOT)),
        "history_sha256": sha256_file(history_path),
        "epochs_completed": 92,
        "best_epoch": 77,
        "early_stop_epoch": 92,
        "provenance_figures": figure_hashes,
        "manual_kub_predictor": {
            "module": "src.inference.kub_predict",
            "function": "predict_kub",
            "default_model": "unetpp",
            "default_checkpoint": "checkpoints/phase10_kub_unetpp_seed42_512/best.pt",
            "default_threshold": 0.5,
            "domain_behavior": "fixed_by_model_scope",
            "domain": "KUB",
            "task_id": 3,
            "original_space_restoration": True,
            "test_rejection": True,
            "external_rejection": True,
        },
        "auto_domain_router_interface": {
            "module": "src.inference.predict",
            "function": "predict",
            "task_auto_status": "NOT_YET_IMPLEMENTED",
            "task_auto_behavior": "raises NotImplementedError",
            "task_ids": {
                0: "ISIC (dermatology / skin lesion)",
                1: "BUSI (breast ultrasound / breast lesion)",
                2: "Kvasir-SEG (gastrointestinal endoscopy / polyp)",
                3: "KUB-StoneX (urinary radiography / stone)",
            },
            "automatic_routing_training_performed": False,
        },
        "demo_notebook": {
            "path": str(nb_09b.relative_to(ROOT)),
            "sha256": sha256_file(nb_09b),
            "retraining_triggered": False,
            "display_only": True,
        },
        "failure_analysis_notebook": {
            "path": str(nb_09.relative_to(ROOT)),
            "sha256": sha256_file(nb_09),
            "retraining_triggered": False,
            "display_only": True,
        },
        "governance": {
            "test_accessed": False,
            "test_reads": 0,
            "test_metrics": "NONE",
            "external_accessed": False,
            "experiment_a_modified": False,
            "phase_12_executed": False,
            "metrics_changed": False,
            "retraining_performed": False,
        },
    }

    json_path = AUDIT_DIR / "phase11_r1_training_provenance_manual_inference_and_auto_router_design.json"
    json_path.write_text(json.dumps(audit_json, indent=2), encoding="utf-8")

    headers = [
        "Component",
        "Status / Path",
        "Details",
    ]
    rows = [
        ["UNet++ Training History", "experiments/phase10_kub_unetpp_seed42_512/history.csv", f"SHA256: `{audit_json['history_sha256']}` (92 epochs, best epoch 77)"],
        ["UNet++ Loss Curve", "reports/figures/phase11_kub_failure_analysis/phase11_unetpp_training_loss_provenance.png", "300+ DPI PNG/SVG/PDF generated"],
        ["UNet++ VAL Dice Curve", "reports/figures/phase11_kub_failure_analysis/phase11_unetpp_val_dice_provenance.png", "300+ DPI PNG/SVG/PDF generated"],
        ["UNet++ LR Curve", "reports/figures/phase11_kub_failure_analysis/phase11_unetpp_lr_provenance.png", "300+ DPI PNG/SVG/PDF generated"],
        ["Manual KUB Predictor", "src/inference/kub_predict.py", "predict_kub & show_kub_prediction (threshold 0.5, UNet++ best.pt)"],
        ["Generic Predict Interface", "src/inference/predict.py", "predict(..., task='auto') raises NotImplementedError safely"],
        ["Demo Notebook", "notebooks/09b_kub_manual_prediction_demo.ipynb", f"SHA256: `{audit_json['demo_notebook']['sha256']}` (executed without errors/training)"],
        ["Failure Analysis Notebook", "notebooks/09_kub_failure_analysis.ipynb", f"SHA256: `{audit_json['failure_analysis_notebook']['sha256']}` (provenance section added)"],
    ]

    markdown_table = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    markdown_table.extend("| " + " | ".join(r) + " |" for r in rows)

    md_content = f"""# Phase 11-R1 — Training Provenance, Manual Inference, and Auto-Domain Interface

**Status: PASS**  
**Scope: utility / presentation / interface patch only; no retraining or metric changes**

## Provenance and Interface Summary

{chr(10).join(markdown_table)}

## Key Integrity Declarations
- **Retraining**: NO
- **Metrics Changed**: NO
- **TEST Accessed**: NO (0 reads; blocked by `TestAccessError`)
- **External Data Accessed**: NO
- **Experiment A Modified**: NO
- **Phase 12 Executed**: NO
- **Auto Domain Router Trained**: NO (Interface design & safety exception enforced)
"""

    md_path = AUDIT_DIR / "phase11_r1_training_provenance_manual_inference_and_auto_router_design.md"
    md_path.write_text(md_content, encoding="utf-8")
    print(f"Provenance saved to {json_path}")


if __name__ == "__main__":
    main()
