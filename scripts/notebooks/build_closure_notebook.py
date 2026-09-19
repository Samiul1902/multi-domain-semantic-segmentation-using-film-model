"""Build complete, authoritative Phase 14/15 closure notebook 12_phase14_15_gate_closure.ipynb."""
import json
from pathlib import Path
import nbformat as nbf

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def build_closure_notebook():
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "language_info": {"name": "python", "version": "3.11.9"},
        "kernelspec": {"name": "python3", "display_name": "Python 3"},
    }

    cells = []

    # Section 1: Title & Purpose
    cells.append(nbf.v4.new_markdown_cell("""# Phase 14 & Phase 15 Formal Gate Closure Audit

**Authoritative Governance & Scientific Audit Notebook**  
**Phase Sequence:** Phase 13 $\\rightarrow$ Phase 14 $\\rightarrow$ Phase 15 $\\rightarrow$ Phase 16  
**Status:** COMPLETE / CLOSED WITHOUT EXECUTION  
**Execution Mode:** READ-ONLY AUDIT ONLY (No training, no model execution)

---

## 1. Executive Summary & Purpose
This notebook records the formal closure of **Phase 14** (Regional segmentation / coarse-to-fine refinement) and **Phase 15** (Loss / ROI / fusion / scale / object-size studies) without scientific execution.

Following pre-registered protocol governance:
1. **Phase 14** was prospectively gated on proposal quality. While Phase 13 Stage-4D demonstrated substantial improvements and passed its continuation criteria, it did not meet four of the six stricter Phase-14 entry requirements. Thus, Phase 14 was closed without execution.
2. **Phase 15** was structurally dependent on Phase-14 regional refiner outputs. Because Phase 14 was not executed, Phase 15 could not be entered and was likewise closed without execution.
3. Both phases are marked `COMPLETE_CLOSED_NOT_RUN`. No models were trained, no metrics were fabricated, and **Phase 16** (Multi-domain dataset harmonization) becomes the next eligible scientific phase."""))

    # Section 2: Project Position after Phase 13
    cells.append(nbf.v4.new_markdown_cell("""## 2. Project Position After Phase 13
Phase 13 (Predicted-ROI Proposal Localizer) concluded with the Stage-4D final bounded localizer redesign (`phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1`). 

Under fixed parameter-free stride-4 logit pooling ($128 \\times 128$ grid), the model relieved the dense negative focal penalty by ~16x and passed all 5 pre-registered Stage-4D continuation criteria on validation data."""))

    # Code cell 1: Environment & Artifact Loading
    cells.append(nbf.v4.new_code_cell("""import sys
import os
import json
import hashlib
from pathlib import Path
import pandas as pd
import numpy as np
from IPython.display import display

cwd = Path.cwd().resolve()
if (cwd / 'experiments').is_dir():
    PROJECT_ROOT = cwd
elif (cwd.parent / 'experiments').is_dir():
    PROJECT_ROOT = cwd.parent
else:
    PROJECT_ROOT = Path('D:/Softfors/jup').resolve()

assert (PROJECT_ROOT / 'experiments').is_dir(), f"Cannot locate valid project root: {PROJECT_ROOT}"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
print(f"Authoritative Project Root: {PROJECT_ROOT}")

from src.utils.test_lock import verify_test_lock
from src.utils.manifest_guard import verify_manifests

verify_manifests()
lock = verify_test_lock(PROJECT_ROOT)
print(f"TEST Lock: STRICTLY VERIFIED (0 content reads authorized, manifest {lock['manifest_version']})")
"""))

    # Section 3: Phase-13 Canonical Proposal Result
    cells.append(nbf.v4.new_markdown_cell("""## 3. Phase-13 Canonical Proposal Results
The canonical validation metrics achieved by `best.pt` at epoch 73 under selected configuration (`threshold=0.10, margin=0.20, top_k=5, nms_iou=0.30`):
- **Tiny Recall@90:** $53 / 73 = 72.60\\%$ ($0.726027$)
- **Overall Recall@90:** $100 / 156 = 64.10\\%$ ($0.641026$)
- **Hard Tiny Recovered:** $7 / 16$ ($43.75\\%$)
- **Global-Empty Covered:** $3 / 7$ ($42.86\\%$)
- **Mean ROI Area Fraction:** $0.005899$ ($0.59\\%$ of image area)
- **Mean Proposals per Image:** $4.660377$
- **Best Epoch:** 73
- **Best Checkpoint SHA-256:** `ece906df6c73f2e93c3f873661490bf3cb1a6b82be2d2d93b58c25bc967cbace`"""))

    # Code cell 2: Verification of Phase-13 Canonical Values
    cells.append(nbf.v4.new_code_cell("""# Load Phase-13 completion audit and selected configuration
p13_audit_path = PROJECT_ROOT / 'reports/audits/phase13_final_completion_audit.json'
assert p13_audit_path.exists(), "Phase-13 audit missing!"
with open(p13_audit_path, 'r', encoding='utf-8-sig') as f:
    p13_audit = json.load(f)

sel_cfg_path = PROJECT_ROOT / 'reports/tables/phase13b_stage4d_selected_config.csv'
sel_cfg = pd.read_csv(sel_cfg_path).iloc[0]

# Programmatic verification of canonical values
tiny_rec = sel_cfg['tiny_recall90']
overall_rec = sel_cfg['overall_recall90']
hard_tiny = int(sel_cfg['hard_tiny_recovered90'])
global_empty = int(sel_cfg['global_empty_images_covered90'])
roi_area = sel_cfg['mean_roi_area_fraction']
proposals = sel_cfg['mean_proposals_per_image']

print("Phase-13 Canonical Values Verified from Artifacts:")
print(f"  Tiny Recall@90:       {tiny_rec:.6f} (Expected: 0.726027)")
print(f"  Overall Recall@90:    {overall_rec:.6f} (Expected: 0.641026)")
print(f"  Hard Tiny:            {hard_tiny} / 16 (Expected: 7)")
print(f"  Global-Empty:         {global_empty} / 7 (Expected: 3)")
print(f"  Mean ROI Area:        {roi_area:.6f} (Expected: 0.005899)")
print(f"  Mean Proposals/Img:   {proposals:.6f} (Expected: 4.660377)")

assert abs(tiny_rec - 0.726027397260274) < 1e-5
assert abs(overall_rec - 0.6410256410256411) < 1e-5
assert hard_tiny == 7
assert global_empty == 3
assert abs(roi_area - 0.005898906179948982) < 1e-5
assert abs(proposals - 4.660377358490566) < 1e-5

# Verify checkpoint SHA
best_pt = PROJECT_ROOT / 'checkpoints/phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1/best.pt'
h = hashlib.sha256()
with open(best_pt, 'rb') as f:
    while chunk := f.read(8192):
        h.update(chunk)
assert h.hexdigest() == "ece906df6c73f2e93c3f873661490bf3cb1a6b82be2d2d93b58c25bc967cbace"
print("Phase-13 Checkpoint SHA-256: VERIFIED")
"""))

    # Section 4: Phase-14 Intended Objective & Frozen Entry Gate
    cells.append(nbf.v4.new_markdown_cell("""## 4. Phase-14 Intended Objective: Regional segmentation / coarse-to-fine refinement
Canonical Phase-14 Objective: **Regional segmentation / coarse-to-fine refinement (Requires viable proposals)**.

Phase 14 was designed to train a second-stage patch-refinement segmentation model focused on candidate calculus regions generated by Phase 13.

To avoid training refiners on inadequate localization proposals, Phase 14 enforced a strict 6-condition entry gate:
- **Criterion A:** Hard Tiny Recovered $\ge 8 / 16$
- **Criterion B:** Global-Empty Images Covered $\ge 4 / 7$
- **Criterion C:** Tiny Recall@90 $\ge 0.85$
- **Criterion D:** Overall Recall@90 $\ge 0.85$
- **Criterion E:** Mean Union ROI Area $\le 0.10$
- **Criterion F:** Mean Proposals per Image $\le 5.0$"""))

    # Code cell 3: Programmatic Phase-14 Gate Evaluation
    cells.append(nbf.v4.new_code_cell("""gate_records = [
    {
        "Criterion": "A: Hard Tiny Recovered",
        "Requirement": ">= 8 / 16",
        "Canonical Achieved": f"{hard_tiny} / 16",
        "Numeric Achieved": hard_tiny,
        "Threshold": 8,
        "Passed": hard_tiny >= 8
    },
    {
        "Criterion": "B: Global-Empty Covered",
        "Requirement": ">= 4 / 7",
        "Canonical Achieved": f"{global_empty} / 7",
        "Numeric Achieved": global_empty,
        "Threshold": 4,
        "Passed": global_empty >= 4
    },
    {
        "Criterion": "C: Tiny Recall@90",
        "Requirement": ">= 0.85",
        "Canonical Achieved": f"{tiny_rec:.6f}",
        "Numeric Achieved": tiny_rec,
        "Threshold": 0.85,
        "Passed": tiny_rec >= 0.85
    },
    {
        "Criterion": "D: Overall Recall@90",
        "Requirement": ">= 0.85",
        "Canonical Achieved": f"{overall_rec:.6f}",
        "Numeric Achieved": overall_rec,
        "Threshold": 0.85,
        "Passed": overall_rec >= 0.85
    },
    {
        "Criterion": "E: Mean ROI Area",
        "Requirement": "<= 0.10",
        "Canonical Achieved": f"{roi_area:.6f}",
        "Numeric Achieved": roi_area,
        "Threshold": 0.10,
        "Passed": roi_area <= 0.10
    },
    {
        "Criterion": "F: Mean Proposals/Image",
        "Requirement": "<= 5.0",
        "Canonical Achieved": f"{proposals:.6f}",
        "Numeric Achieved": proposals,
        "Threshold": 5.0,
        "Passed": proposals <= 5.0
    },
]

gate_df = pd.DataFrame(gate_records)
display(gate_df[['Criterion', 'Requirement', 'Canonical Achieved', 'Passed']])

all_passed = gate_df['Passed'].all()
failed_criteria = gate_df[~gate_df['Passed']]['Criterion'].tolist()
print(f"Phase-14 Entry Gate Overall: {'PASSED' if all_passed else 'NOT_PASSED'}")
print(f"Failed Criteria Count: {len(failed_criteria)} / 6 ({failed_criteria})")

assert not all_passed, "Gate unexpectedly passed!"
assert len(failed_criteria) == 4, f"Expected 4 failed criteria, got {len(failed_criteria)}"
"""))

    # Section 5: Phase-14 Closure Decision & Audit Verification
    cells.append(nbf.v4.new_markdown_cell("""## 5. Phase-14 Formal Closure Decision
Because 4 of the 6 pre-registered entry criteria were not met, Phase 14 was **CLOSED WITHOUT EXECUTION**.

**Critical Distinction:** Phase 14 was NOT an executed failed experiment. No Phase-14 model was trained, no optimizer or loss was evaluated, and no model metrics exist. Preserving this distinction maintains scientific integrity."""))

    # Code cell 4: Verify Phase-14 Closure Audit
    cells.append(nbf.v4.new_code_cell("""p14_audit_path = PROJECT_ROOT / 'reports/audits/phase14_final_closure_audit.json'
assert p14_audit_path.exists(), "Phase-14 closure audit missing!"
with open(p14_audit_path, 'r', encoding='utf-8-sig') as f:
    p14_audit = json.load(f)

print("Phase-14 Closure Audit Verification:")
print(f"  Objective:          {p14_audit['objective']}")
print(f"  Closure Status:     {p14_audit['closure_status']}")
print(f"  Training Executed:  {p14_audit['training_executed']}")
print(f"  Closure Reason:     {p14_audit['closure_reason']}")
print(f"  Scientific Result:  {p14_audit['scientific_result']}")

assert p14_audit['closure_status'] == "COMPLETE_CLOSED_NOT_RUN"
assert p14_audit['training_executed'] is False
assert p14_audit['closure_reason'] == "FROZEN_ENTRY_GATE_NOT_MET"
assert p14_audit['scientific_result'] == "NOT_EVALUATED"
print("Phase-14 Audit: PASS")
"""))

    # Section 6: Phase-15 Dependency Closure
    cells.append(nbf.v4.new_markdown_cell("""## 6. Phase-15 Dependency Closure: Loss / ROI / fusion / scale / object-size studies
Canonical Phase-15 Objective: **Loss / ROI / fusion / scale / object-size studies**.

Phase 15 was intended to perform ablation and refinement studies on the Phase-14 regional network.

Because Phase 14 did not meet its entry gate and was not executed, the required upstream architecture and checkpoints do not exist. Consequently, Phase 15 was likewise **CLOSED WITHOUT EXECUTION**."""))

    # Code cell 5: Verify Phase-15 Closure Audit
    cells.append(nbf.v4.new_code_cell("""p15_audit_path = PROJECT_ROOT / 'reports/audits/phase15_final_closure_audit.json'
assert p15_audit_path.exists(), "Phase-15 closure audit missing!"
with open(p15_audit_path, 'r', encoding='utf-8-sig') as f:
    p15_audit = json.load(f)

print("Phase-15 Closure Audit Verification:")
print(f"  Objective:          {p15_audit['objective']}")
print(f"  Closure Status:     {p15_audit['closure_status']}")
print(f"  Training Executed:  {p15_audit['training_executed']}")
print(f"  Closure Reason:     {p15_audit['closure_reason']}")
print(f"  Scientific Result:  {p15_audit['scientific_result']}")

assert p15_audit['closure_status'] == "COMPLETE_CLOSED_NOT_RUN"
assert p15_audit['training_executed'] is False
assert p15_audit['closure_reason'] == "UPSTREAM_PHASE14_NOT_EXECUTED"
assert p15_audit['scientific_result'] == "NOT_EVALUATED"
print("Phase-15 Audit: PASS")

print("Dependency Chain Summary:")
print("  Phase 13 (Learned Localizer): EXECUTED_AND_COMPLETE (Stage-4D Promising on Val)")
print("       |")
print("       v")
print("  Phase 14 Entry Gate: NOT_PASSED (4 / 6 criteria unmet)")
print("       |")
print("       v")
print("  Phase 14 (Regional segmentation / coarse-to-fine refinement): COMPLETE_CLOSED_NOT_RUN (No model trained)")
print("       |")
print("       v")
print("  Phase 15 Upstream Dependency: UNAVAILABLE")
print("       |")
print("       v")
print("  Phase 15 (Loss / ROI / fusion / scale / object-size studies): COMPLETE_CLOSED_NOT_RUN (No model trained)")
print("       |")
print("       v")
print("  Phase 16 (Multi-domain dataset harmonization): NEXT ELIGIBLE PHASE (Independent of Phase 14)")
"""))

    # Section 7: Current Project State Verification
    cells.append(nbf.v4.new_markdown_cell("""## 7. Current Project State Verification
Validating the project's central machine-readable state artifact (`reports/audits/antigravity_current_state.json`)."""))

    # Code cell 6: Verify current state json
    cells.append(nbf.v4.new_code_cell("""state_path = PROJECT_ROOT / 'reports/audits/antigravity_current_state.json'
assert state_path.exists(), "Current state JSON missing!"
with open(state_path, 'r', encoding='utf-8-sig') as f:
    state = json.load(f)

print("Central State Verification:")
print(f"  Current Phase:        {state['current_phase']}")
print(f"  Current Phase Status: {state['current_phase_status']}")
print(f"  Phase 13 Status:      {state['phase13_status']} (Frozen: {state['phase13_frozen']})")
print(f"  Phase 14 Status:      {state['phase14_status']} (Gate: {state['phase14_gate']})")
print(f"  Phase 15 Status:      {state['phase15_status']}")
print(f"  Phase 16 Status:      {state['phase16_status']}")
print(f"  Next Eligible Phase:  {state['next_eligible_phase']} ({state['next_phase_title']})")
print(f"  Active Training:      {state['active_training']}")

assert state['phase13_status'] == "EXECUTED_AND_COMPLETE"
assert state['phase13_frozen'] is True
assert state['phase14_status'] == "COMPLETE_CLOSED_NOT_RUN"
assert state['phase14_gate'] == "NOT_PASSED"
assert state['phase14_authorized'] is False
assert state['phase15_status'] == "COMPLETE_CLOSED_NOT_RUN"
assert state['phase15_executed'] is False
assert state['phase16_status'] == "NOT_STARTED"
assert str(state['next_eligible_phase']) == "16"
assert state['active_training'] == "NONE"
print("Current State Consistency: PASS")
"""))

    # Section 8: Scientific Validity & Governance Locks
    cells.append(nbf.v4.new_markdown_cell("""## 8. Scientific Validity & Governance Locks
Enforcing prospective gate criteria protects scientific validity:
- **No Cascade of Compromised Signals:** Training refiners on sub-optimal proposals produces uninterpretable errors.
- **Zero TEST Contamination:** TEST set remains completely locked with 0 reads.
- **External Dataset Protection:** External data is untouched.
- **Experiment A Reference Frozen:** Reference implementations are unmodified."""))

    # Code cell 7: Verify locks
    cells.append(nbf.v4.new_code_cell("""print("Governance Lock Verification:")
print(f"  TEST Content Reads:   {state['test_content_reads']}")
print(f"  TEST Metrics:         {state['test_metrics']}")
print(f"  External Used:        {state['external_used']}")
print(f"  Experiment A Modified:{state['experiment_a_modified']}")

assert state['test_content_reads'] == 0, "TEST data was accessed!"
assert state['test_metrics'] == "NONE", "TEST metrics were computed!"
assert state['external_used'] is False, "External data was accessed!"
assert state['experiment_a_modified'] is False, "Experiment A was modified!"
print("Governance Locks: STRICTLY ENFORCED")
"""))

    # Section 9: Comprehensive Artifact & Provenance Audit
    cells.append(nbf.v4.new_markdown_cell("""## 9. Comprehensive Artifact & Provenance Audit
Inventory of all key governance, audit, and reproducible notebook artifacts."""))

    # Code cell 8: Build and display artifact table
    cells.append(nbf.v4.new_code_cell("""def compute_sha(p):
    if not p.exists():
        return "MISSING"
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

artifacts = [
    ("reports/audits/phase13_final_completion_audit.json", "Phase 13 Final Audit (JSON)"),
    ("reports/audits/phase13_final_completion_audit.md", "Phase 13 Final Audit (Markdown)"),
    ("reports/audits/phase14_final_closure_audit.json", "Phase 14 Closure Audit (JSON)"),
    ("reports/audits/phase14_final_closure_audit.md", "Phase 14 Closure Audit (Markdown)"),
    ("reports/audits/phase15_final_closure_audit.json", "Phase 15 Closure Audit (JSON)"),
    ("reports/audits/phase15_final_closure_audit.md", "Phase 15 Closure Audit (Markdown)"),
    ("reports/audits/post_phase13_roadmap_transition.json", "Roadmap Transition Audit (JSON)"),
    ("reports/audits/post_phase13_roadmap_transition.md", "Roadmap Transition Audit (Markdown)"),
    ("reports/audits/antigravity_current_state.json", "Central Project State (JSON)"),
    ("notebooks/11c_kub_final_localizer_redesign.ipynb", "Phase 13B Final Localizer Notebook"),
    ("notebooks/12_phase14_15_gate_closure.ipynb", "Phase 14/15 Executable Gate-Closure Audit"),
    ("PROJECT_CONTEXT.md", "Project Context Handoff Document"),
    ("PROJECT_MASTER_PLAN.md", "Master Research Plan & Roadmap"),
]

records = []
for rel_path, purpose in artifacts:
    full_p = PROJECT_ROOT / rel_path
    exists = full_p.exists()
    if rel_path == "notebooks/12_phase14_15_gate_closure.ipynb":
        sha = "RECORDED_POST_RUN_ALL"
    else:
        sha = compute_sha(full_p)[:16] + "..." if exists else "N/A"
    records.append({
        "Artifact": rel_path,
        "Purpose": purpose,
        "Exists": exists,
        "SHA-256 (Prefix)": sha
    })

art_df = pd.DataFrame(records)
display(art_df)

assert len(records) == 13, f"Expected 13 artifacts, got {len(records)}"
assert art_df['Exists'].all(), "One or more required governance artifacts are missing!"

print("Note: Notebook 12 existence is verified in-notebook. Its definitive final SHA-256 is audited externally post-execution to avoid circular metadata self-mutation.")

# Verify frozen 11c SHA
nb11c_path = PROJECT_ROOT / "notebooks/11c_kub_final_localizer_redesign.ipynb"
nb11c_sha = compute_sha(nb11c_path)
print("Notebook 11c SHA-256:", nb11c_sha)
assert nb11c_sha == "6c8e00496c61d1ef5c297a98a6c16d9f1e05e008561350db9960324602ea78ef", "Notebook 11c SHA changed!"
print("Notebook 11c Integrity: STRICTLY PRESERVED")
"""))

    # Section 10: Final Authoritative Status
    cells.append(nbf.v4.new_markdown_cell("""## 10. Final Authoritative Status & Roadmap Boundary

```
PHASE 13:
EXECUTED_AND_COMPLETE

PHASE 14:
COMPLETE_CLOSED_NOT_RUN

PHASE 15:
COMPLETE_CLOSED_NOT_RUN

PHASE 16:
NOT_STARTED

PHASES 13–15:
FORMALLY COMPLETE/CLOSED

NEXT ELIGIBLE PHASE:
16 — Multi-domain dataset harmonization

PHASE16 STARTED:
NO
```"""))

    # Attach cells
    nb.cells = cells

    target_path = PROJECT_ROOT / "notebooks/12_phase14_15_gate_closure.ipynb"
    with open(target_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Authoritative closure notebook generated at: {target_path}")
    print(f"Total cells: {len(nb.cells)} (Markdown: {sum(1 for c in nb.cells if c.cell_type == 'markdown')}, Code: {sum(1 for c in nb.cells if c.cell_type == 'code')})")


if __name__ == "__main__":
    build_closure_notebook()
