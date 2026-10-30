"""Update master notebook post_phase14_h3_proposal_supply_pipeline.ipynb.

Marks Step 05 COMPLETE and adds supply-axis evaluation summary.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

import nbformat
from nbformat.v4 import new_markdown_cell, new_code_cell
from nbclient import NotebookClient

ROOT = Path("D:/Softfors/jup")
MASTER_NB = ROOT / "notebooks/phasewise/post_phase14_h3_proposal_supply/post_phase14_h3_proposal_supply_pipeline.ipynb"

nb = nbformat.read(str(MASTER_NB), as_version=4)

# ── Cell 2: Update Step 05 status and add supply-axis summary ──────────────
# Find the code cell with entries
for i, cell in enumerate(nb.cells):
    if cell.cell_type == "code" and "entries" in cell.source and "05" in cell.source:
        # Replace Step 05 entry
        old_05 = '("05", "05_h3_supply_axis_evaluation.ipynb", "H3 supply-axis evaluation", "DEFERRED", "NOT AUTHORIZED / NO CLOSURE"),'
        new_05 = '("05", "05_h3_supply_axis_evaluation.ipynb", "H3 supply-axis evaluation", "COMPLETE", "H3_SUPPLY_AXIS_EVALUATION_COMPLETE__FORMAL_ADJUDICATION_PENDING"),'
        cell.source = cell.source.replace(old_05, new_05)

        # Add supply-axis evaluation summary after the training closure print
        old_tail = 'print("Supply-axis evaluation remains PENDING and NOT AUTHORIZED in this task. Phase 15 remains NOT_STARTED_AND_NOT_AUTHORIZED. TEST is CLOSED.")'
        new_tail = '''print("=== STEP 05 SUPPLY-AXIS EVALUATION ===")
eval_art = load_json("reports/audits/h3_supply_axis_evaluation.json")
criteria = load_json("reports/audits/h3_proposal_supply_success_failure_criteria.json")

h3m = eval_art["h3_metrics"]
r_h3 = eval_art["r_h3"]
prim = eval_art["primary_criteria"]
fb = eval_art["failure_boundary"]

eval_rows = [
    ("evaluation artifact", "reports/audits/h3_supply_axis_evaluation.json", eval_art["status"]),
    ("selected epoch", eval_art["selected_epoch"], eval_art["checkpoint_selection_replay_verdict"]),
    ("VAL images / components", f'{eval_art["val_population"]["images"]} / {eval_art["val_population"]["components"]}', f'TINY={eval_art["val_population"]["tiny"]} SMALL={eval_art["val_population"]["small"]} MEDIUM={eval_art["val_population"]["medium"]} LARGE={eval_art["val_population"]["large"]}'),
    ("frozen decode", f'thr={eval_art["frozen_decode"]["threshold"]} margin={eval_art["frozen_decode"]["margin"]} top_k={eval_art["frozen_decode"]["top_k"]} nms={eval_art["frozen_decode"]["nms_iou"]}', "exactly 1 policy"),
    ("total proposals", h3m["proposal_counts"]["total_proposals"], f'{h3m["proposal_counts"]["proposals_per_image"]:.4f}/image'),
    ("zero-proposal GT", f'{h3m["proposal_counts"]["zero_proposal_gt"]}/152', f'baseline 79/152 -> {79-h3m["proposal_counts"]["zero_proposal_gt"]} recovered'),
    ("zero-proposal TINY", f'{h3m["zero_proposal_by_size"]["TINY"]}/72', f'baseline 57/72 -> {57-h3m["zero_proposal_by_size"]["TINY"]} recovered'),
    ("any-overlap recall TINY", f'{h3m["supply_recall"]["any_overlap_tiny"]:.10f}', f'baseline {15/72:.10f}'),
    ("coverage90 overall", f'{h3m["coverage"]["coverage90_overall"]:.10f}', ""),
    ("R_H3", f'{r_h3["R_H3"]:.10f}', f'band: {r_h3["interpretation_band"]}'),
    ("Criterion A (TINY<=20/72)", f'{prim["criterion_a"]["value"]}/72', "PASS" if prim["criterion_a"]["passed"] else "FAIL"),
    ("Criterion B (GT<=35/152)", f'{prim["criterion_b"]["value"]}/152', "PASS" if prim["criterion_b"]["passed"] else "FAIL"),
    ("primary A AND B", "", "PASS" if prim["combined_primary_passed"] else "FAIL"),
    ("failure boundary fired", str(fb["fired"]), fb["label"]),
    ("precision (descriptive)", f'{eval_art["contamination_descriptive"]["proposal_precision"]:.6f}', "OBSERVATIONAL_ONLY"),
    ("TEST reads", str(eval_art["test_reads"]), "CLOSED"),
]
display(pd.DataFrame(eval_rows, columns=["metric", "value", "detail"]))
print("Notebook-05 SHA-256:", hashlib.sha256((ROOT / "notebooks/phasewise/post_phase14_h3_proposal_supply" / "05_h3_supply_axis_evaluation.ipynb").read_bytes()).hexdigest())
print("Formal H3 adjudication remains PENDING (Notebook 06, not authorized). Phase 15 remains NOT_STARTED_AND_NOT_AUTHORIZED. TEST is CLOSED.")'''
        cell.source = cell.source.replace(old_tail, new_tail)
        break

# ── Cell 3: Update authoritative chain ──────────────────────────────────────
for i, cell in enumerate(nb.cells):
    if cell.cell_type == "markdown" and "Authoritative chain" in cell.source:
        cell.source = """## Authoritative chain

01 reads `phase14_diag_root_cause.json` and saved diagnostic tables.  
02 reads `post_phase14_h3_axis_priority_results.json` and saved A/C tables.  
03 reads the H3 design/correction/final-binding artifacts and calibration tables.  
04 is COMPLETE and executed: 69 epochs (early stopping, patience 15), best epoch 54 by the frozen (val_localization_recall, -val_loss) tuple, replay verdict H3_CHECKPOINT_SELECTION_REPLAY_PASS; authoritative artifacts `reports/audits/h3_proposal_supply_training_closure.json` and `reports/audits/h3_checkpoint_selection_replay.json`; best checkpoint `checkpoints/h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3/best.pt` (SHA d875cac7d09bbc3d32232191f0af2c138e5a74682fc63e4d6e01f30345eca75e).  
05 is COMPLETE and executed: supply-axis evaluation of the selected H3 checkpoint (epoch 54) on canonical clean-v3 FULL_FIELD VAL (103 images, 152 GT components) under frozen decode (threshold=0.10, margin=0.20, top_k=5, nms_iou=0.30); zero-proposal GT 79->27, zero-proposal TINY 57->22, R_H3=-0.60 (insufficient), Criterion A FAIL (22>20), Criterion B PASS (27<=35), failure boundary FIRED (R_H3<0.15); evaluation state `H3_SUPPLY_AXIS_EVALUATION_COMPLETE__FORMAL_ADJUDICATION_PENDING`; authoritative artifact `reports/audits/h3_supply_axis_evaluation.json`.  
06 remains intentionally deferred until separate supervisor authorization.

H3 is post-Phase14 work. It is not Phase 15 and does not authorize Phase 15.
"""
        break

# Save updated master notebook
nbformat.write(nb, str(MASTER_NB))
print(f"Master notebook updated: {MASTER_NB}")

# Execute the master notebook
print("Executing master notebook...")
client = NotebookClient(
    nb,
    kernel_name="jup-venv",
    timeout=120,
    resources={"metadata": {"path": str(ROOT)}},
)
client.execute()
nbformat.write(nb, str(MASTER_NB))
print("Master notebook executed and saved.")

# Verify
errors = 0
for i, cell in enumerate(nb.cells):
    if cell.cell_type == "code":
        for out in cell.get("outputs", []):
            if out.get("output_type") == "error":
                errors += 1
                print(f"  ERROR in cell {i}: {out.get('ename')}: {out.get('evalue')}")
if errors == 0:
    print("Zero tracebacks: PASS")

sha = hashlib.sha256(MASTER_NB.read_bytes()).hexdigest()
print(f"Master notebook SHA: {sha}")
