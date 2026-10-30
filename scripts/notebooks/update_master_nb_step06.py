"""Additively update the master pipeline notebook: 05 RECONCILED, 06 COMPLETE, 07 PENDING.

Reads nothing new; adds a STEP-06 summary block and refreshes the index/chain.
No training, no inference.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
NB_PATH = ROOT / "notebooks" / "phasewise" / "post_phase14_h3_proposal_supply" / "post_phase14_h3_proposal_supply_pipeline.ipynb"

nb = nbformat.read(str(NB_PATH), as_version=4)
print("Master notebook cells before:", len(nb.cells))

NEW_CELL2 = r'''
import hashlib
entries = [
    ("01", "01_proposal_root_cause_diagnostic.ipynb", "proposal/localizer root-cause diagnostic", "COMPLETE", "F_MIXED_BOTTLENECK"),
    ("02", "02_h3_axis_priority_diagnostic.ipynb", "A-only vs C-only causal priority", "COMPLETE", "H3_DESIGN_ELIGIBLE__AXIS_PROPOSAL_SUPPLY_RECALL"),
    ("03", "03_h3_design_and_pretraining_binding.ipynb", "H3 design, corrections, calibration, binding", "COMPLETE", "H3_FINAL_PRETRAINING_BINDING_COMPLETE__AWAITING_TRAINING_AUTHORIZATION"),
    ("04", "04_h3_training.ipynb", "H3 training record", "COMPLETE", "H3_TRAINING_COMPLETE__CHECKPOINT_SELECTION_REPLAY_PASS__SUPPLY_EVALUATION_PENDING"),
    ("05", "05_h3_supply_axis_evaluation.ipynb", "H3 supply-axis evaluation (metric-domain RECONCILED)", "COMPLETE / RECONCILED", "H3_SUPPLY_METRIC_DOMAIN_RECONCILED__DOWNSTREAM_R_H3_PENDING"),
    ("06", "06_h3_downstream_evaluation.ipynb", "H3 frozen downstream evaluation", "COMPLETE", "H3_DOWNSTREAM_EVALUATION_COMPLETE__FORMAL_ADJUDICATION_PENDING"),
    ("07", "07_h3_adjudication.ipynb", "Formal H3 adjudication", "DEFERRED", "NOT AUTHORIZED / NO RESULTS"),
]
index = pd.DataFrame(entries, columns=["step", "notebook", "purpose", "status", "scientific state"])
index["notebook SHA-256"] = [
    hashlib.sha256((ROOT / "notebooks/phasewise/post_phase14_h3_proposal_supply" / name).read_bytes()).hexdigest()
    if (ROOT / "notebooks/phasewise/post_phase14_h3_proposal_supply" / name).exists() else "PENDING"
    for _, name, *_ in entries
]
display(index)
print("Phase 14 is separate and complete; Phase 15 remains NOT_STARTED_AND_NOT_AUTHORIZED; TEST is CLOSED.")
print()
print("=== STEP 04 AUTHORITATIVE TRAINING CLOSURE ===")
closure = load_json("reports/audits/h3_proposal_supply_training_closure.json")
replay = load_json("reports/audits/h3_checkpoint_selection_replay.json")
ckpt = closure["checkpoint_integrity"]["best_pt"]
summary_rows = [
    ("training closure", "reports/audits/h3_proposal_supply_training_closure.json", closure["status"]),
    ("checkpoint-selection replay", "reports/audits/h3_checkpoint_selection_replay.json", replay["verdict"]),
    ("total completed epochs", closure["total_epochs"], closure["stop_reason"]),
    ("best epoch (frozen tuple)", closure["best_epoch"], closure["selection_rule"]),
    ("best val_localization_recall", closure["best_val_localization_recall"], ""),
    ("best val_loss", closure["best_val_loss"], ""),
    ("best checkpoint", ckpt["path"], ckpt["sha256"]),
]
display(pd.DataFrame(summary_rows, columns=["item", "value", "detail"]))
print("Notebook-04 executed SHA-256:", index.loc[index["step"] == "04", "notebook SHA-256"].iloc[0])

print()
print("=== STEP 05 SUPPLY-AXIS EVALUATION (RECONCILED) ===")
eval_art = load_json("reports/audits/h3_supply_axis_evaluation.json")
criteria = load_json("reports/audits/h3_proposal_supply_success_failure_criteria.json")
recon = load_json("reports/audits/h3_supply_axis_metric_domain_reconciliation.json")

h3m = eval_art["h3_metrics"]
r_h3_proxy = eval_art["r_h3"]
prim = eval_art["primary_criteria"]
fb = eval_art["failure_boundary"]

eval_rows = [
    ("evaluation artifact", "reports/audits/h3_supply_axis_evaluation.json", eval_art["status"]),
    ("metric-domain reconciliation", "reports/audits/h3_supply_axis_metric_domain_reconciliation.json", recon["status"]),
    ("selected epoch", eval_art["selected_epoch"], eval_art["checkpoint_selection_replay_verdict"]),
    ("VAL images / components", f'{eval_art["val_population"]["images"]} / {eval_art["val_population"]["components"]}', f'TINY={eval_art["val_population"]["tiny"]} SMALL={eval_art["val_population"]["small"]} MEDIUM={eval_art["val_population"]["medium"]} LARGE={eval_art["val_population"]["large"]}'),
    ("frozen decode", f'thr={eval_art["frozen_decode"]["threshold"]} margin={eval_art["frozen_decode"]["margin"]} top_k={eval_art["frozen_decode"]["top_k"]} nms={eval_art["frozen_decode"]["nms_iou"]}', "exactly 1 policy"),
    ("total proposals", h3m["proposal_counts"]["total_proposals"], f'{h3m["proposal_counts"]["proposals_per_image"]:.4f}/image'),
    ("zero-proposal GT", f'{h3m["proposal_counts"]["zero_proposal_gt"]}/152', f'baseline 79/152 -> {79-h3m["proposal_counts"]["zero_proposal_gt"]} recovered'),
    ("zero-proposal TINY", f'{h3m["zero_proposal_by_size"]["TINY"]}/72', f'baseline 57/72'),
    ("R_H3 (LOCALIZER-ONLY PROXY)", f'{r_h3_proxy["R_H3"]:.10f}', "NOT FORMAL (proposal domain) - see reconciliation"),
    ("Criterion A (TINY<=20/72)", f'{prim["criterion_a"]["value"]}/72', "PASS" if prim["criterion_a"]["passed"] else "FAIL"),
    ("Criterion B (GT<=35/152)", f'{prim["criterion_b"]["value"]}/152', "PASS" if prim["criterion_b"]["passed"] else "FAIL"),
    ("primary A AND B", "", "PASS" if prim["combined_primary_passed"] else "FAIL"),
    ("TEST reads", str(eval_art["test_reads"]), "CLOSED"),
]
display(pd.DataFrame(eval_rows, columns=["metric", "value", "detail"]))
print("Notebook-05 SHA-256:", hashlib.sha256((ROOT / "notebooks/phasewise/post_phase14_h3_proposal_supply" / "05_h3_supply_axis_evaluation.ipynb").read_bytes()).hexdigest())

print()
print("=== STEP 06 H3 FROZEN DOWNSTREAM EVALUATION ===")
down = load_json("reports/audits/h3_downstream_evaluation.json")
corr = load_json("reports/audits/h3_downstream_metric_domain_correction.json")
fd = down["formal_downstream"]
m = down["h3_downstream_metrics"]
ct = down["contrast_table"]
down_rows = [
    ("evaluation artifact", "reports/audits/h3_downstream_evaluation.json", down["status"]),
    ("metric-domain correction", "reports/audits/h3_downstream_metric_domain_correction.json", corr["status"]),
    ("selected epoch", down["selected_h3_checkpoint"]["selected_epoch"], f'heatmap_resolution={down["selected_h3_checkpoint"]["heatmap_resolution"]}'),
    ("frozen proposal policy", f'{down["frozen_proposal_policy"]}', "exactly 1 policy"),
    ("population", f'{down["population"]["val_images"]} images / {down["population"]["components"]} components', str(down["population"]["size_strata"])),
    ("TINY recall@90 (detection)", f'{fd["TinyRecall_H3_fraction"]} = {fd["TinyRecall_H3"]:.10f}', "formal frozen domain"),
    ("TinyRecall_H3 (cov90 sensitivity)", f'{m["descriptive_strict_cov90"]["tiny_cov90"]:.10f}', "descriptive only"),
    ("Tg / G", f'{fd["Tg"]} / {fd["G"]}', "frozen references"),
    ("R_H3 (FORMAL)", f'{fd["R_H3"]:.10f}', f'band: {fd["interpretation_band"]}'),
    ("R_H3 (cov90 sensitivity)", f'{fd["sensitivity_strict_cov90"]["R_H3_cov90"]:.10f}', "NOT formal"),
    ("overall recall@90 (detection)", f'{m["overall_recall90_det"]:.10f}', "frozen domain"),
    ("mean Dice", f'{m["mean_dice"]:.6f}', f'GLOBAL {ct["GLOBAL"]["mean_dice"]:.6f} / PREDICTED {ct["PREDICTED"]["mean_dice"]:.6f}'),
    ("hard-Tiny recovered", f'{m["hard_tiny_recovered"]}/15', f'cov90: {m["descriptive_strict_cov90"]["hard_tiny_recovered_cov90"]}/15'),
    ("global-empty recovered", f'{m["global_empty_recovered"]}/5', f'cov90: {m["descriptive_strict_cov90"]["global_empty_recovered_cov90"]}/5'),
    ("formal adjudication", str(down["formal_adjudication_performed"]), "NOT PERFORMED (Notebook 07 deferred)"),
    ("TEST reads", str(down["test_reads"]), "CLOSED"),
]
display(pd.DataFrame(down_rows, columns=["metric", "value", "detail"]))
print("Notebook-06 SHA-256:", hashlib.sha256((ROOT / "notebooks/phasewise/post_phase14_h3_proposal_supply" / "06_h3_downstream_evaluation.ipynb").read_bytes()).hexdigest())
print("Formal H3 adjudication remains PENDING (Notebook 07, not authorized). Phase 15 remains NOT_STARTED_AND_NOT_AUTHORIZED. TEST is CLOSED.")
'''

NEW_CELL3 = r'''
## Authoritative chain

01 reads `phase14_diag_root_cause.json` and saved diagnostic tables.  
02 reads `post_phase14_h3_axis_priority_results.json` and saved A/C tables.  
03 reads the H3 design/correction/final-binding artifacts and calibration tables.  
04 is COMPLETE and executed: 69 epochs (early stopping, patience 15), best epoch 54 by the frozen (val_localization_recall, -val_loss) tuple, replay verdict H3_CHECKPOINT_SELECTION_REPLAY_PASS; best checkpoint `checkpoints/h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3/best.pt` (SHA d875cac7d09bbc3d32232191f0af2c138e5a74682fc63e4d6e01f30345eca75e).  
05 is COMPLETE and RECONCILED: the supply-axis evaluation measured localizer/proposal supply (zero-proposal GT 79->27, zero-proposal TINY 57->22). A post-evaluation metric-domain reconciliation (`reports/audits/h3_supply_axis_metric_domain_reconciliation.json`) relabelled the earlier proposal-domain substitution as a LOCALIZER-ONLY PROXY and marked it INVALID_FOR_FORMAL_ADJUDICATION__PROPOSAL_DOMAIN_ONLY. State `H3_SUPPLY_METRIC_DOMAIN_RECONCILED__DOWNSTREAM_R_H3_PENDING`.  
06 is COMPLETE and executed: the single frozen H3 downstream evaluation (H3 localizer epoch 54 -> frozen Stage-4D proposal policy -> frozen Phase-14 refiner epoch 56 -> fusion -> segmentation). In the frozen detection domain (`>=1px overlap`, matching the frozen Tg), TinyRecall_H3 = 59/72 = 0.8194444444444444 and the formal R_H3 = (TinyRecall_H3 - Tg)/G = 2/15 = 0.13333333333333333 (insufficient). A metric-layer correction (`reports/audits/h3_downstream_metric_domain_correction.json`) aligned the aggregate to the frozen detection domain; the as-run cov90 artifact is preserved (`reports/audits/h3_downstream_evaluation_v1_asrun.json`). State `H3_DOWNSTREAM_EVALUATION_COMPLETE__FORMAL_ADJUDICATION_PENDING`.  
07 (formal H3 adjudication) remains intentionally deferred until separate supervisor authorization.

H3 is post-Phase14 work. It is not Phase 15 and does not authorize Phase 15.
'''

# Replace cell 2 (code index/summary) and cell 3 (markdown chain)
nb.cells[2] = nbformat.v4.new_code_cell(NEW_CELL2.strip("\n"))
nb.cells[3] = nbformat.v4.new_markdown_cell(NEW_CELL3.strip("\n"))

nbformat.write(nb, str(NB_PATH))
print("Master notebook updated. Cells:", len(nb.cells))

print("Re-executing master notebook...")
client = NotebookClient(nb, kernel_name="jup-venv", timeout=600,
                        resources={"metadata": {"path": str(ROOT)}})
client.execute()
nbformat.write(nb, str(NB_PATH))

errors = 0
for i, cell in enumerate(nb.cells):
    if cell.cell_type == "code":
        for out in cell.get("outputs", []):
            if out.get("output_type") == "error":
                errors += 1
                print(f"  ERROR cell {i}: {out.get('ename')}: {out.get('evalue')}")
counts = [c.get("execution_count") for c in nb.cells if c.cell_type == "code"]
monotonic = all(counts[i] == i + 1 for i in range(len(counts)))
print(f"Zero tracebacks: {'PASS' if errors == 0 else 'FAIL'}")
print(f"Monotonic exec counts (1..{len(counts)}): {'PASS' if monotonic else 'CHECK'}")
print("Master notebook SHA:", hashlib.sha256(NB_PATH.read_bytes()).hexdigest())
