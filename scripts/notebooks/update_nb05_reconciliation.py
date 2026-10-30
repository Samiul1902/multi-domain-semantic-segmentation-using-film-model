"""Additively update Notebook 05 with the metric-domain reconciliation section.

- Relabels the proposal-level R_H3 as LOCALIZER-ONLY PROXY.
- Inserts a clearly visible 'Post-evaluation metric-domain reconciliation' section.
- Preserves all original supply measurements, tables and figures.
- Re-executes the notebook fully.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import nbformat
from nbformat.v4 import new_markdown_cell, new_code_cell
from nbclient import NotebookClient

ROOT = Path("D:/Softfors/jup")
NB_PATH = ROOT / "notebooks/phasewise/post_phase14_h3_proposal_supply/05_h3_supply_axis_evaluation.ipynb"

nb = nbformat.read(str(NB_PATH), as_version=4)

# ── 1. Relabel section 18 (R_H3 Calculation) header ─────────────────────────
for i, c in enumerate(nb.cells):
    if c.cell_type == "markdown" and c.source.strip().startswith("## 18. R_H3 Calculation"):
        c.source = """## 18. R_H3 Calculation (LOCALIZER-ONLY PROXY — NOT FORMAL DOWNSTREAM R_H3)

> **METRIC-DOMAIN WARNING (see §18b).** The quantity computed in this cell is
> `H3_PROPOSAL_TINY_COVERAGE90` — a **localizer/proposal** metric. Substituting it
> into the frozen R_H3 formula produces a **PROXY** value that **MUST NOT** be used
> as the formal downstream H3 adjudication value. The frozen prospective design
> defines formal R_H3 only after the frozen Phase-14 regional refiner.
>
> Frozen formula: `R_H3 = (TinyRecall_H3 - Tg) / G`
>
> where:
> - `TinyRecall_H3` = H3 localizer's TINY covered90 recall (from proposals)  ← PROPOSAL DOMAIN
> - `Tg = 0.7916666666666666` (GLOBAL/PREDICTED baseline TINY recall)
> - `G = 0.20833333333333337` (gap to oracle, 1.0 - Tg)
"""
        break

# ── 2. Annotate the R_H3 code cell with an explicit proxy banner ────────────
for i, c in enumerate(nb.cells):
    if c.cell_type == "code" and "r_h3_info = eval_artifact['r_h3']" in c.source:
        c.source = (
            "# ── LOCALIZER-ONLY PROXY COMPUTATION (NOT FORMAL DOWNSTREAM R_H3) ──────────\n"
            "# This value is retained verbatim from the original supply-axis evaluation.\n"
            "# It is a PROPOSAL-DOMAIN proxy. The formal downstream R_H3 is computed in\n"
            "# Notebook 06 from the post-refiner downstream TINY Recall@0.90.\n"
            "print('=== LOCALIZER-ONLY PROXY (NOT FORMAL DOWNSTREAM R_H3) ===')\n"
            + c.source
        )
        break

# ── 3. Insert the reconciliation section right after the R_H3 code cell ─────
insert_at = None
for i, c in enumerate(nb.cells):
    if c.cell_type == "code" and "LOCALIZER-ONLY PROXY COMPUTATION" in c.source:
        insert_at = i + 1
        break
assert insert_at is not None, "R_H3 code cell not found"

recon_md = new_markdown_cell("""## 18b. Post-evaluation metric-domain reconciliation

**Status:** `H3_SUPPLY_METRIC_DOMAIN_RECONCILED__DOWNSTREAM_R_H3_PENDING`

**This section is ADDITIVE.** It does not modify, delete, or reinterpret any
underlying supply measurement. All supply tables and figures above remain valid
as **LOCALIZER / PROPOSAL SUPPLY** evidence.

### Why this reconciliation exists

The original supply-axis evaluation correctly measured localizer/proposal supply,
but it also substituted a **proposal-level** quantity into the **formal downstream**
R_H3 formula and displayed the result as though it were the adjudicative
downstream R_H3.

The frozen prospective H3 design does **not** define formal R_H3 at the
localizer-only proposal level. It explicitly defines:

```
H3 localizer
  -> frozen Stage-4D proposal policy
  -> frozen Phase-14 regional refiner epoch 56
  -> segmentation
  -> downstream TINY Recall
  -> formal R_H3 = (TinyRecall_H3 - Tg) / G
```

### Reconciliation statements (mandatory)

1. `proposal TINY coverage90 = 0.6666666666666666` is a **proposal/localizer** metric
   (`H3_PROPOSAL_TINY_COVERAGE90`).
2. It is **NOT** the formal downstream `TinyRecall_H3`.
3. The displayed proxy value `-0.5999999999999999` **MUST NOT** be used for formal
   H3 adjudication. It is relabelled **LOCALIZER-ONLY PROXY — NOT FORMAL DOWNSTREAM R_H3**.
4. The **zero-proposal supply gates remain valid and unchanged**:
   Criterion A `22 > 20` = FAIL; Criterion B `27 <= 35` = PASS; combined = FAIL.
5. Formal downstream R_H3 requires the frozen Stage-4D pipeline
   (H3 localizer + Phase-14 refiner + fusion) and is computed in Notebook 06.

### Provenance of the reconciliation

- Additive governance artifact: `reports/audits/h3_supply_axis_metric_domain_reconciliation.json`
- No new inference was performed to produce this correction.
- The original supply artifact (`reports/audits/h3_supply_axis_evaluation.json`) is
  preserved, not overwritten.
""")

recon_code = new_code_cell("""# ── Metric-domain reconciliation (additive) ─────────────────────────────────
import json as _json

recon = _json.loads((ROOT / 'reports/audits/h3_supply_axis_metric_domain_reconciliation.json').read_text())

print("Reconciliation status:", recon['status'])
print()
print("Misused quantity:")
print(f"  original term in NB05      : {recon['misused_quantity']['original_term_in_notebook_05']}")
print(f"  corrected proposal term    : {recon['misused_quantity']['corrected_proposal_domain_term']}")
print(f"  proposal-level value       : {recon['misused_quantity']['proposal_level_value']}")
print(f"  previously reported proxy  : {recon['misused_quantity']['previously_reported_proxy_R_H3']}")
print(f"  formal-use status          : {recon['misused_quantity']['formal_use_status']}")
print()
print("Preserved supply gates (unchanged):")
ps = recon['preserved_supply_results']
print(f"  zero-proposal GT   : {ps['h3_zero_proposal_gt']} (baseline {ps['pre_h3_zero_proposal_gt']})")
print(f"  zero-proposal TINY : {ps['h3_zero_proposal_tiny']} (baseline {ps['pre_h3_zero_proposal_tiny']})")
print(f"  Criterion A        : {ps['primary_supply_criterion_A']['result']}")
print(f"  Criterion B        : {ps['primary_supply_criterion_B']['result']}")
print(f"  combined           : {ps['combined_primary_supply_criteria']}")
print()
print("Corrected terminology:")
for term, info in recon['corrected_terminology'].items():
    print(f"  {term}: value={info['value']} domain={info['domain']}")
print()
print("No new inference performed for the correction:", recon['reconciliation_actions']['no_new_inference_for_correction'])
print("Original supply counts unchanged              :", recon['reconciliation_actions']['original_supply_counts_unchanged'])
print("Formal downstream R_H3 status                 :", recon['reconciliation_actions']['formal_downstream_R_H3_status'])

# ── Reconciliation assertions ───────────────────────────────────────────────
assert recon['misused_quantity']['proposal_level_value'] == 0.6666666666666666
assert recon['misused_quantity']['previously_reported_proxy_R_H3'] == -0.5999999999999999
assert recon['misused_quantity']['formal_use_status'] == 'INVALID_FOR_FORMAL_ADJUDICATION__PROPOSAL_DOMAIN_ONLY'
assert recon['reconciliation_actions']['no_new_inference_for_correction'] is True
assert recon['reconciliation_actions']['original_supply_counts_unchanged'] is True
assert recon['preserved_supply_results']['h3_zero_proposal_tiny'] == '22/72'
assert recon['preserved_supply_results']['primary_supply_criterion_A']['result'] == 'FAIL'
assert recon['preserved_supply_results']['primary_supply_criterion_B']['result'] == 'PASS'
print("\\n✓ Reconciliation assertions passed.")
""")

nb.cells.insert(insert_at, recon_code)
nb.cells.insert(insert_at, recon_md)

# ── 4. Relabel Figure H's R_H3 panel as proxy ───────────────────────────────
for i, c in enumerate(nb.cells):
    if c.cell_type == "markdown" and "Figure H — Primary Success/Failure Gates" in c.source:
        c.source = """### Figure H — Primary Success/Failure Gates with Thresholds

> **NOTE:** the third panel shows the **LOCALIZER-ONLY PROXY** for R_H3
> (`H3_PROPOSAL_TINY_COVERAGE90` substituted into the frozen formula). It is
> **NOT** the formal downstream R_H3 (see §18b). Panels 1–2 (supply gates) remain
> valid and unchanged.
"""
        break

for i, c in enumerate(nb.cells):
    if c.cell_type == "code" and "ax.set_title(f'R_H3 = {r_val:.4f}" in c.source:
        c.source = c.source.replace(
            "ax.set_title(f'R_H3 = {r_val:.4f}\\n(insufficient)')",
            "ax.set_title(f'PROXY R_H3 = {r_val:.4f}\\n(LOCALIZER-ONLY — NOT FORMAL DOWNSTREAM)')",
        )
        c.source = c.source.replace(
            "ax.set_xlabel('R_H3')",
            "ax.set_xlabel('PROXY R_H3 (proposal domain)')",
        )
        break

# ── 5. Suppress formal failure-boundary interpretation wording ──────────────
for i, c in enumerate(nb.cells):
    if c.cell_type == "markdown" and c.source.strip().startswith("## 20. Failure-Boundary Table"):
        c.source = """## 20. Failure-Boundary Table (PROXY-CONDITIONAL)

> **METRIC-DOMAIN NOTE (see §18b).** The `R_H3 < 0.15` failure clause below was
> evaluated with the **LOCALIZER-ONLY PROXY** R_H3, not the formal downstream
> R_H3. The historical proxy value is preserved here verbatim, but the formal
> failure-boundary interpretation is **DEFERRED** until the frozen downstream
> R_H3 is available (Notebook 06). The supply-side clause
> (`zero_proposal_TINY >= 45/72`) is a genuine supply-domain condition and is
> unaffected.
"""
        break

for i, c in enumerate(nb.cells):
    if c.cell_type == "code" and "fb = eval_artifact['failure_boundary']" in c.source:
        c.source = (
            "# NOTE: the R_H3 clause below uses the LOCALIZER-ONLY PROXY (see §18b).\n"
            "# Formal failure-boundary interpretation is DEFERRED to Notebook 06.\n"
            + c.source
            + "\nprint('\\n[metric-domain note] The R_H3-based clause above is a PROXY condition.')\n"
            "print('Formal downstream failure-boundary interpretation is DEFERRED to Notebook 06.')"
        )
        break

# ── 6. Extend the assertions cell ───────────────────────────────────────────
for i, c in enumerate(nb.cells):
    if c.cell_type == "code" and "Governance assertions" in c.source:
        c.source = c.source.replace(
            "print(\"\\n✓ All assertions passed.\")",
            """# ── Metric-domain reconciliation assertions ──────────────────────────────
assert recon['status'] == 'H3_SUPPLY_METRIC_DOMAIN_RECONCILED__DOWNSTREAM_R_H3_PENDING'
assert recon['misused_quantity']['formal_use_status'] == 'INVALID_FOR_FORMAL_ADJUDICATION__PROPOSAL_DOMAIN_ONLY'
print("✓ Metric-domain reconciliation present and asserted.")

print("\\n✓ All assertions passed.")""",
        )
        break

nbformat.write(nb, str(NB_PATH))
print(f"Notebook 05 updated additively: {NB_PATH}")
print(f"Cells now: {len(nb.cells)}")

# ── Re-execute ──────────────────────────────────────────────────────────────
print("Re-executing Notebook 05...")
client = NotebookClient(
    nb, kernel_name="jup-venv", timeout=600,
    resources={"metadata": {"path": str(ROOT)}},
)
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
sha = hashlib.sha256(NB_PATH.read_bytes()).hexdigest()
print(f"New Notebook 05 SHA: {sha}")
