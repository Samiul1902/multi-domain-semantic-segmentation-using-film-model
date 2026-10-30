"""Sync notebooks/phasewise/00_PHASEWISE_PROJECT_INDEX.ipynb to the current governance state.

Additive + corrective only: updates stale Stage-B status text, refreshes the inline
status rows, and appends a Phase-20B completion section. Re-executes read-only and
re-applies the deterministic post-processing. No training, no inference, no TEST.

    ./.venv/Scripts/python.exe scripts/notebooks/sync_phasewise_index_notebook.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
NB = ROOT / "notebooks/phasewise/00_PHASEWISE_PROJECT_INDEX.ipynb"

nb = nbformat.read(str(NB), as_version=4)

# ---- cell 4: stale "later phases (16+)" status summary --------------------- #
c4 = nb.cells[4]
assert c4.cell_type == "markdown"
c4.source = (
    "## 3. Reviewer Verification & Status Summary\n\n"
    "Stage-A phases 00-14 are COMPLETE; Phases 15-18 are `DEFERRED_CONDITIONAL__NOT_EXECUTED`.\n"
    "Stage B is ACTIVE: **Phase 19 COMPLETE**, **Phase 20 / 20A COMPLETE** (shared four-domain UNet++),\n"
    "**Phase 20B COMPLETE** (five-model conventional benchmark), and **Phase 21 ELIGIBLE / NOT STARTED**\n"
    "(authorization required). Every later phase is cleanly partitioned with structured README\n"
    "specifications and zero synthetic/fake results. The untouched TEST split stays `CLOSED`\n"
    "(`TEST reads = 0`, `TEST visualizations = 0`)."
)

# ---- cell 11: stale "Phase 20+: NOT_STARTED" line -------------------------- #
c11 = nb.cells[11]
assert c11.cell_type == "markdown"
c11.source = c11.source.replace(
    "- Phase 20+: `NOT_STARTED_AND_NOT_AUTHORIZED`; TEST `CLOSED`",
    "- Phase 20 / 20A: COMPLETE · Phase 20B: COMPLETE · Phase 21: `ELIGIBLE_NOT_STARTED`; TEST `CLOSED`",
)

# ---- cell 12: inline status rows ------------------------------------------ #
c12 = nb.cells[12]
assert c12.cell_type == "code"
c12.source = c12.source.replace(
    "    {'phase': '19', 'status': 'CURRENT / AUTHORIZED'},\n"
    "    {'phase': '20', 'status': 'NOT_STARTED'},",
    "    {'phase': '19', 'status': 'COMPLETE'},\n"
    "    {'phase': '20 / 20A', 'status': 'COMPLETE'},\n"
    "    {'phase': '20B', 'status': 'COMPLETE'},\n"
    "    {'phase': '21', 'status': 'ELIGIBLE_NOT_STARTED'},",
)

# ---- append Phase-20B section --------------------------------------------- #
nb.cells.append(nbformat.v4.new_markdown_cell(
    "## Phase-20B Completion — Five-Model Conventional Baseline Benchmark\n\n"
    "**Phase 20B COMPLETE.** Four additional conventional architectures (`unet`, `attention_unet`,\n"
    "`deeplabv3plus`, `transformer_mit_unet`) were trained strictly sequentially under the **same**\n"
    "frozen Phase-19/20 protocol as the Phase-20A UNet++ reference, giving a **five-model** benchmark.\n\n"
    "- Five-model macro-domain VAL Dice: DeepLabV3+ **0.827652** > Transformer/MiT **0.822383** >\n"
    "  UNet++ **0.792010** > Attention U-Net **0.789037** > U-Net **0.787832**\n"
    "- Two tiers separated (p ≈ 0.000); **top-two ordering NOT significant** (Δ ≈ +0.005270, CI crosses zero, p ≈ 0.282)\n"
    "- Reviewer package: 153 figures (114 embedded), **51/51 evaluation matrices visualized (100 %)**\n"
    "- Notebook determinism: **3 consecutive builds → identical SHA-256**\n"
    "- TEST reads: 0\n"
    "- Scientific terminal state: `PHASE20_FIVE_MODEL_BASELINE_BENCHMARK_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED`\n"
    "- Documentation terminal state: `PHASE20B_REVIEWER_PACKAGE_COMPLETE__FULL_VISUAL_EVIDENCE__PHASE21_ELIGIBLE_NOT_STARTED`"
))
nb.cells.append(nbformat.v4.new_code_cell(
    "import json as _j, pandas as _pd\n"
    "_a = _j.loads((ROOT / 'reports/audits/phase20b_reviewer_package_audit.json').read_text(encoding='utf-8'))\n"
    "_f = _j.loads((ROOT / 'reports/audits/phase20b_reviewer_package_freeze.json').read_text(encoding='utf-8'))\n"
    "_rows = [\n"
    "    {'phase': '19', 'status': 'COMPLETE'},\n"
    "    {'phase': '20 / 20A', 'status': 'COMPLETE'},\n"
    "    {'phase': '20B', 'status': 'COMPLETE'},\n"
    "    {'phase': '21', 'status': 'ELIGIBLE / NOT STARTED'},\n"
    "]\n"
    "display(_pd.DataFrame(_rows))\n"
    "display(_pd.DataFrame(_f['ranking_by_macro_domain_dice'])[['model_key', 'phase', 'macro_domain_val_dice', 'best_epoch', 'params']])\n"
    "print('figures total        :', _a['figures']['figures_total'], '| embedded', _a['figures']['embedded_in_notebook'])\n"
    "print('matrix coverage      :', _a['matrix_coverage']['visualized'], '/', _a['matrix_coverage']['matrices_total'])\n"
    "print('notebook deterministic:', _a['notebook']['deterministic_3_builds'])\n"
    "print('top model            :', _f['top_model'], '| top-two significant:', _f['top_two_ranking_significant'])\n"
    "print('TEST reads           :', _a['test_reads'])\n"
    "print('phase21 started      :', _a['phase21_started'])\n"
    "print('SCIENTIFIC TERMINAL  :', _a['scientific_terminal_state'])\n"
    "print('DOC TERMINAL         :', _a['documentation_terminal_state'])"
))

for i, c in enumerate(nb.cells):
    c["id"] = f"idx{i:03d}"

nbformat.write(nb, str(NB))
print(f"Wrote {NB} ({len(nb.cells)} cells); executing ...")

client = NotebookClient(nb, kernel_name="jup-venv", timeout=1800,
                        resources={"metadata": {"path": str(ROOT)}})
client.execute()

for c in nb.cells:
    if isinstance(c.get("metadata"), dict):
        c["metadata"].pop("execution", None)

_ADDR = re.compile(r"0x[0-9a-fA-F]{6,}")
for c in nb.cells:
    for o in c.get("outputs", []) or []:
        d = o.get("data")
        if isinstance(d, dict):
            for k, v in list(d.items()):
                if isinstance(v, str):
                    d[k] = _ADDR.sub("0xADDR", v)
                elif isinstance(v, list):
                    d[k] = [_ADDR.sub("0xADDR", s) if isinstance(s, str) else s for s in v]
nbformat.write(nb, str(NB))

code = [c for c in nb.cells if c.cell_type == "code"]
err = sum(1 for c in code for o in c.get("outputs", []) if o.get("output_type") == "error")
png = sum(1 for c in code for o in c.get("outputs", []) if "image/png" in (o.get("data", {}) or {}))
exe = sum(1 for c in code if c.get("execution_count") is not None)
print(f"cells {len(nb.cells)} | executed {exe} | errors {err} | png {png}")
print("SHA:", hashlib.sha256(NB.read_bytes()).hexdigest())
