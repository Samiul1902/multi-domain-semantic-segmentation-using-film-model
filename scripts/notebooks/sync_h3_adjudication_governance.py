"""Post-adjudication governance synchronization.

1. Update the H3 master pipeline notebook (step 07 -> COMPLETE / FORMALLY ADJUDICATED).
2. Update the H3 branch README.
3. Update the phasewise master index (H3 branch = gate-resolution branch).
4. Reconcile Phase-15 protocol-vs-execution wording drift.
5. Write reports/audits/h3_post_adjudication_governance_state.json.

No training, no inference, no TEST access, no frozen-gate change.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
H3_DIR = ROOT / "notebooks" / "phasewise" / "post_phase14_h3_proposal_supply"
H3_MASTER = H3_DIR / "post_phase14_h3_proposal_supply_pipeline.ipynb"
H3_README = H3_DIR / "README.md"
INDEX_NB = ROOT / "notebooks" / "phasewise" / "00_PHASEWISE_PROJECT_INDEX.ipynb"
P15_README = ROOT / "notebooks" / "phasewise" / "phase_15_loss_study" / "README.md"
PW_README = ROOT / "notebooks" / "phasewise" / "README.md"
NB07 = H3_DIR / "07_h3_adjudication.ipynb"
GOV = ROOT / "reports" / "audits" / "h3_post_adjudication_governance_state.json"

LABEL = "H3_SUPPLY_REDESIGN_INSUFFICIENT"
WRAPPER = "H3_FORMAL_ADJUDICATION_COMPLETE__TARGET_SUPPORT_INSUFFICIENT__PHASE15_LOCKED"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def strip_timing(nb) -> None:
    """Remove volatile per-cell execution timing so re-execution is content-deterministic.

    nbclient writes `cell.metadata.execution` (iopub/shell timestamps) on every run,
    which makes an otherwise-identical notebook hash differently each time. Removing it
    makes the recorded SHA-256 a stable content address.
    """
    for c in nb.cells:
        if isinstance(c.get("metadata"), dict):
            c["metadata"].pop("execution", None)


def coalesce_streams(nb) -> None:
    """Merge adjacent stream outputs of the same name within each cell.

    The Jupyter ZMQ transport may deliver a single stdout burst as one chunk or split
    into several; merging them removes that transport-level non-determinism so the
    notebook bytes (and therefore the SHA-256) are stable across executions.
    """
    for c in nb.cells:
        outs = c.get("outputs")
        if not outs:
            continue
        merged = []
        for o in outs:
            if (o.get("output_type") == "stream" and merged
                    and merged[-1].get("output_type") == "stream"
                    and merged[-1].get("name") == o.get("name")):
                prev = merged[-1]
                pt, ct = prev.get("text", ""), o.get("text", "")
                if isinstance(pt, list):
                    pt = "".join(pt)
                if isinstance(ct, list):
                    ct = "".join(ct)
                prev["text"] = pt + ct
            else:
                merged.append(o)
        c["outputs"] = merged


def exec_nb(path: Path) -> dict:
    nb = nbformat.read(str(path), as_version=4)
    NotebookClient(nb, kernel_name="jup-venv", timeout=900,
                   resources={"metadata": {"path": str(ROOT)}}).execute()
    strip_timing(nb)
    coalesce_streams(nb)
    nbformat.write(nb, str(path))
    errs = sum(1 for c in nb.cells if c.cell_type == "code"
               for o in c.get("outputs", []) if o.get("output_type") == "error")
    counts = [c.get("execution_count") for c in nb.cells if c.cell_type == "code"]
    mono = all(counts[i] == i + 1 for i in range(len(counts)))
    return {"code_cells": len(counts), "tracebacks": errs, "monotonic": bool(mono)}


def update_h3_master(record: dict) -> None:
    old = sha(H3_MASTER)
    nb = nbformat.read(str(H3_MASTER), as_version=4)
    # cell 2 — the entries/index cell
    c2 = nb.cells[2]
    c2.source = c2.source.replace(
        '("07", "07_h3_adjudication.ipynb", "Formal H3 adjudication", "DEFERRED", "NOT AUTHORIZED / NO RESULTS"),',
        '("07", "07_h3_adjudication.ipynb", "Formal H3 adjudication", "COMPLETE / FORMALLY ADJUDICATED", "H3_SUPPLY_REDESIGN_INSUFFICIENT"),'
    )
    c2.source = c2.source.replace(
        'print("Phase 14 is separate and complete; Phase 15 remains NOT_STARTED_AND_NOT_AUTHORIZED; TEST is CLOSED.")',
        'print("Phase 14 is separate and complete; Phase 15 remains NOT_STARTED_AND_NOT_AUTHORIZED; TEST is CLOSED.")'
    )
    # Append the step-07 adjudication block at the end of cell 2 (idempotent guard)
    if "=== STEP 07 FORMAL H3 ADJUDICATION ===" not in c2.source:
        c2.source = c2.source.rstrip("\n") + '''

print()
print("=== STEP 07 FORMAL H3 ADJUDICATION ===")
adj = load_json("reports/audits/h3_formal_adjudication.json")
cr = adj["criterion_results"]
fbx = adj["failure_boundary"]
adj_rows = [
    ("adjudication artifact", "reports/audits/h3_formal_adjudication.json", adj["status"]),
    ("scientific label", adj["scientific_label"], "FROZEN"),
    ("selected epoch", adj["selected_checkpoint"]["selected_epoch"], adj["checkpoint_selection_replay_verdict"]),
    ("selected checkpoint SHA", adj["selected_checkpoint"]["sha256"], f"matches expected: {adj['selected_checkpoint']['sha256_matches_expected']}"),
    ("Criterion A (TINY<=20/72)", cr["criterion_A"]["observed"], cr["criterion_A"]["result"]),
    ("Criterion B (GT<=35/152)", cr["criterion_B"]["observed"], cr["criterion_B"]["result"]),
    ("combined primary supply", "", cr["combined_primary_supply_result"]),
    ("formal TinyRecall_H3", adj["observed"]["formal_TinyRecall_H3_fraction"], f'{adj["observed"]["formal_TinyRecall_H3"]:.10f}'),
    ("formal R_H3", adj["observed"]["formal_R_H3_fraction"], f'{adj["observed"]["formal_R_H3"]:.10f}'),
    ("R_H3 band", adj["observed"]["R_H3_band"], f"insufficient threshold {adj['observed']['formal_TinyRecall_H3_fraction'] and 0.15}"),
    ("failure clause 1 (TINY>=45/72)", fbx["clause_1"]["observed"], "FIRED" if fbx["clause_1"]["fired"] else "not fired"),
    ("failure clause 2 (R_H3<0.15)", f'{fbx["clause_2"]["observed"]:.10f}', "FIRED" if fbx["clause_2"]["fired"] else "not fired"),
    ("failure boundary overall", "", "FIRED" if fbx["fired"] else "not fired"),
    ("Phase-15 status", adj["governance"]["phase_15_status"], "LOCKED"),
    ("TEST reads", str(adj["governance"]["test_reads"]), "CLOSED"),
]
display(pd.DataFrame(adj_rows, columns=["item", "value", "result"]))
print("Notebook-07 SHA-256:", hashlib.sha256((ROOT / "notebooks/phasewise/post_phase14_h3_proposal_supply" / "07_h3_adjudication.ipynb").read_bytes()).hexdigest())
print("FROZEN H3 LABEL:", adj["scientific_label"])
print("State: H3_FORMAL_ADJUDICATION_COMPLETE__TARGET_SUPPORT_INSUFFICIENT__PHASE15_LOCKED")
'''
    # cell 3 — markdown chain
    c3 = nb.cells[3]
    c3.source = c3.source.replace(
        "07 (formal H3 adjudication) remains intentionally deferred until separate supervisor authorization.",
        "07 is COMPLETE and executed: the formal H3 adjudication applied the prospectively frozen "
        "criteria to the authoritative observed values. Criterion A (zero-proposal TINY <= 20/72) "
        "FAILED at 22/72; Criterion B (zero-proposal GT <= 35/152) PASSED at 27/152; the formal "
        "downstream R_H3 = 2/15 = 0.13333333333333333 < 0.15, so the frozen failure boundary FIRED. "
        "The frozen scientific label is **H3_SUPPLY_REDESIGN_INSUFFICIENT**. The intervention "
        "materially improved proposal supply (zero-proposal GT 79->27, TINY 57->22) but the recovered "
        "supply did not translate into sufficient downstream Tiny-recall gain under the frozen "
        "Stage-4D pipeline. Phase 15 remains NOT_STARTED_AND_NOT_AUTHORIZED; TEST remains CLOSED."
    )
    nbformat.write(nb, str(H3_MASTER))
    res = exec_nb(H3_MASTER)
    record["h3_master_notebook"] = {
        "path": "notebooks/phasewise/post_phase14_h3_proposal_supply/post_phase14_h3_proposal_supply_pipeline.ipynb",
        "old_sha256": old, "new_sha256": sha(H3_MASTER),
        "change": "step 07 marked COMPLETE / FORMALLY ADJUDICATED; adjudication block appended",
        **res,
    }


def _nb_stats(path: Path) -> tuple:
    """Return (total_cells, code_cells, error_outputs) for an executed notebook."""
    nb = nbformat.read(str(path), as_version=4)
    code = [c for c in nb.cells if c.cell_type == "code"]
    errs = sum(1 for c in code for o in c.get("outputs", []) if o.get("output_type") == "error")
    return len(nb.cells), len(code), errs


def _heal_row(text: str, prefix: str, nb_path: Path) -> str:
    """Rewrite a provenance row's SHA and execution column from the on-disk notebook.

    `prefix` is the literal row prefix ending with '|' (e.g. '| `01_x.ipynb` |').
    Rows that do not match are returned unchanged (historical rows stay frozen).
    """
    total, ncode, errs = _nb_stats(nb_path)
    pattern = re.compile(r"^" + re.escape(prefix) + r" `[0-9a-f]{64}` \| [^|]*\|[ \t]*$", re.M)
    if not pattern.search(text):
        return text
    desc = f"{total} cells, {ncode}/{ncode} code cells, {errs} errors"
    return pattern.sub(lambda _m: f"{prefix} `{sha(nb_path)}` | {desc} |", text)


def update_h3_readme(record: dict) -> None:
    old = sha(H3_README)
    text = H3_README.read_text(encoding="utf-8")
    text = text.replace(
        "| 07 | `07_h3_adjudication.ipynb` | Formal H3 adjudication | Deferred | No | No authorized adjudication |",
        "| 07 | `07_h3_adjudication.ipynb` | Formal H3 adjudication | Complete / Formally adjudicated | Yes | `H3_SUPPLY_REDESIGN_INSUFFICIENT` |"
    )
    # Refresh the executed-notebook SHA table rows for the notebooks changed by the sync task
    # (self-healing: current rows are recomputed from disk; historical rows are left untouched)
    replacements = {
        "`01_proposal_root_cause_diagnostic.ipynb` | `b492853bb1abd3a79e3116f817309da6898c7f230d17516c683045a78175b1a8`":
            f"`01_proposal_root_cause_diagnostic.ipynb` | `{sha(H3_DIR / '01_proposal_root_cause_diagnostic.ipynb')}`",
        "`02_h3_axis_priority_diagnostic.ipynb` | `2ecddfe781b621fd3f807c30afb76563b92328645ed3170a747bb2fdaa0e45f7`":
            f"`02_h3_axis_priority_diagnostic.ipynb` | `{sha(H3_DIR / '02_h3_axis_priority_diagnostic.ipynb')}`",
        "`05_h3_supply_axis_evaluation.ipynb` (reconciled, current) | `34f57624497b6132433f36f0243fec5b6295037ee2766f60f06d983184f3bb34`":
            f"`05_h3_supply_axis_evaluation.ipynb` (reconciled, current) | `{sha(H3_DIR / '05_h3_supply_axis_evaluation.ipynb')}`",
        "`06_h3_downstream_evaluation.ipynb` (current) | `09bfe393b35cdede3b2a20b4495fbb3caef8f05b81d44c3c768398d554eabe1c`":
            f"`06_h3_downstream_evaluation.ipynb` (current) | `{sha(H3_DIR / '06_h3_downstream_evaluation.ipynb')}`",
        "`post_phase14_h3_proposal_supply_pipeline.ipynb` (current) | `03579c8cef135ae8c8fbab1070def02417110a79b558971883e095b567f96377`":
            f"`post_phase14_h3_proposal_supply_pipeline.ipynb` (current) | `{sha(H3_MASTER)}`",
    }
    for a, b in replacements.items():
        text = text.replace(a, b)
    # insert the notebook-07 provenance row (SHA table) if it is absent
    if "| `07_h3_adjudication.ipynb` (formal adjudication) |" not in text:
        _t7, _c7, _e7 = _nb_stats(NB07)
        text = text.replace(
            "| `post_phase14_h3_proposal_supply_pipeline.ipynb` (current) |",
            f"| `07_h3_adjudication.ipynb` (formal adjudication) | `{sha(NB07)}` | {_t7} cells, {_c7}/{_c7} code cells, {_e7} errors |\n"
            "| `post_phase14_h3_proposal_supply_pipeline.ipynb` (current) |", 1)
    # self-heal every CURRENT provenance row (SHA + execution column) from disk
    for _prefix, _path in [
        ("| `01_proposal_root_cause_diagnostic.ipynb` |", H3_DIR / "01_proposal_root_cause_diagnostic.ipynb"),
        ("| `02_h3_axis_priority_diagnostic.ipynb` |", H3_DIR / "02_h3_axis_priority_diagnostic.ipynb"),
        ("| `03_h3_design_and_pretraining_binding.ipynb` |", H3_DIR / "03_h3_design_and_pretraining_binding.ipynb"),
        ("| `04_h3_training.ipynb` (executed, final) |", H3_DIR / "04_h3_training.ipynb"),
        ("| `05_h3_supply_axis_evaluation.ipynb` (reconciled, current) |", H3_DIR / "05_h3_supply_axis_evaluation.ipynb"),
        ("| `06_h3_downstream_evaluation.ipynb` (current) |", H3_DIR / "06_h3_downstream_evaluation.ipynb"),
        ("| `07_h3_adjudication.ipynb` (formal adjudication) |", NB07),
        ("| `post_phase14_h3_proposal_supply_pipeline.ipynb` (current) |", H3_MASTER),
    ]:
        text = _heal_row(text, _prefix, _path)
    # reconcile stale step-06 / training-boundary prose that predates adjudication
    text = text.replace(
        "- **Formal adjudication:** NOT performed. Deferred to step 07.",
        "- **Formal adjudication:** performed in step 07 (see *Formal H3 adjudication* below).")
    text = text.replace(
        "COMPLETE; formal adjudication (notebook 07) remains DEFERRED — NOT authorized in this task;",
        "COMPLETE; formal adjudication (notebook 07) is COMPLETE (frozen label `H3_SUPPLY_REDESIGN_INSUFFICIENT`);")
    # Add the formal adjudication section before "## Authoritative artifacts"
    adj_section = f"""## Formal H3 adjudication (step 07)

The formal H3 adjudication applied the prospectively frozen criteria to the authoritative
observed values. It is a **disk-only** adjudication (no training, no inference, no TEST access).

| Clause | Frozen rule | Observed | Result |
|---|---|---|---|
| Supply Criterion A | zero-proposal TINY <= 20/72 | **22/72** | **FAIL** |
| Supply Criterion B | zero-proposal GT <= 35/152 | **27/152** | **PASS** |
| Combined primary supply | A AND B | — | **FAIL** |
| Downstream gate | R_H3 >= 0.30 | **2/15 = 0.1333** | **FAIL** |
| Failure clause 1 | zero-proposal TINY >= 45/72 | 22/72 | not fired |
| Failure clause 2 | R_H3 < 0.15 | 0.1333 | **FIRED** |

- **Formal metric domain:** detection (`component overlap >= 1 px`), matching the frozen Tg/G.
- **Formal TinyRecall_H3:** `59/72 = 0.8194444444444444`; **Tg** `57/72`; **G** `15/72`.
- **Formal R_H3:** `2/15 = 0.13333333333333333` → band `insufficient`.
- **Frozen scientific label:** **`H3_SUPPLY_REDESIGN_INSUFFICIENT`**.
- **Interpretation:** the size-adaptive target-support intervention materially improved proposal
  supply (zero-proposal GT 79→27, TINY 57→22) but the recovered supply did not translate into
  sufficient downstream Tiny-recall gain under the frozen Stage-4D pipeline.
- **Adjudication artifact:** `reports/audits/h3_formal_adjudication.json`.

**H3 did NOT succeed.** The failure boundary fired. The regional hypothesis is NOT erased:
ORACLE_REGIONAL remains a valid diagnostic upper bound; the predicted-localization path still
fails to retain enough practical regional benefit, so the `REVISE_LOCALIZER` problem remains
unresolved. Phase 15 remains `NOT_STARTED_AND_NOT_AUTHORIZED`; TEST and external TEST remain CLOSED.

## Authoritative artifacts"""
    text = text.replace("## Authoritative artifacts", adj_section, 1) if "## Formal H3 adjudication (step 07)" not in text else text
    H3_README.write_text(text, encoding="utf-8")
    record["h3_readme"] = {"path": "notebooks/phasewise/post_phase14_h3_proposal_supply/README.md",
                           "old_sha256": old, "new_sha256": sha(H3_README)}


def update_phasewise_index(record: dict) -> None:
    old = sha(INDEX_NB)
    nb = nbformat.read(str(INDEX_NB), as_version=4)
    marker = "Post-Phase14 / H3 Gate-Resolution Branch"
    if not any(marker in c.source for c in nb.cells):
        nb.cells.append(nbformat.v4.new_markdown_cell(
            "## Post-Phase14 / H3 Gate-Resolution Branch\n\n"
            "The post-Phase14 proposal-supply work is a **gate-resolution branch**, NOT Phase 15.\n"
            "It is complete through formal adjudication.\n\n"
            "- Branch notebooks: `notebooks/phasewise/post_phase14_h3_proposal_supply/` (steps 01–07)\n"
            "- Formal adjudication: `07_h3_adjudication.ipynb`\n"
            "- Adjudication artifact: `reports/audits/h3_formal_adjudication.json`\n"
            "- Frozen scientific label: **`H3_SUPPLY_REDESIGN_INSUFFICIENT`**\n"
            "- Governance state: `H3_FORMAL_ADJUDICATION_COMPLETE__TARGET_SUPPORT_INSUFFICIENT__PHASE15_LOCKED`\n\n"
            "Phase 15 is a separate phase and remains `NOT_STARTED_AND_NOT_AUTHORIZED`.\n"
        ))
        nb.cells.append(nbformat.v4.new_code_cell(
            "import json\n"
            "from pathlib import Path\n"
            "_adj = json.loads((ROOT / 'reports/audits/h3_formal_adjudication.json').read_text(encoding='utf-8'))\n"
            "_h3dir = ROOT / 'notebooks/phasewise/post_phase14_h3_proposal_supply'\n"
            "_rows = [\n"
            "    {'step': '01', 'state': 'COMPLETE', 'terminal': 'F_MIXED_BOTTLENECK'},\n"
            "    {'step': '02', 'state': 'COMPLETE', 'terminal': 'A_PRIORITY'},\n"
            "    {'step': '03', 'state': 'COMPLETE', 'terminal': 'DESIGN_FROZEN'},\n"
            "    {'step': '04', 'state': 'COMPLETE', 'terminal': 'TRAINING_COMPLETE'},\n"
            "    {'step': '05', 'state': 'COMPLETE / RECONCILED', 'terminal': 'SUPPLY_RECONCILED'},\n"
            "    {'step': '06', 'state': 'COMPLETE', 'terminal': 'DOWNSTREAM_COMPLETE'},\n"
            "    {'step': '07', 'state': 'COMPLETE / FORMALLY ADJUDICATED', 'terminal': _adj['scientific_label']},\n"
            "]\n"
            "display(pd.DataFrame(_rows))\n"
            "print('Frozen H3 label   :', _adj['scientific_label'])\n"
            "print('Phase-15 status   :', _adj['governance']['phase_15_status'])\n"
            "print('TEST reads        :', _adj['governance']['test_reads'])\n"
        ))
    nbformat.write(nb, str(INDEX_NB))
    res = exec_nb(INDEX_NB)
    record["phasewise_index"] = {
        "path": "notebooks/phasewise/00_PHASEWISE_PROJECT_INDEX.ipynb",
        "old_sha256": old, "new_sha256": sha(INDEX_NB),
        "change": "added post-Phase14 / H3 gate-resolution branch section", **res,
    }


def reconcile_phase15(record: dict) -> None:
    """Distinguish Phase-15 PROTOCOL (frozen design) from Phase-15 EXECUTION (not started)."""
    note = ("Phase 15 exists as a FROZEN PROTOCOL / DESIGN only. Phase-15 clean-v3 scientific "
            "EXECUTION and TRAINING remain NOT_STARTED_AND_NOT_AUTHORIZED. The two must not be "
            "conflated: a frozen protocol is not an executed phase.")
    record["phase15_reconciliation"] = {
        "distinction": note,
        "protocol_status": "PROTOCOL_FROZEN__DESIGN_ONLY",
        "execution_status": "NOT_STARTED_AND_NOT_AUTHORIZED",
        "training_status": "NOT_STARTED_AND_NOT_AUTHORIZED",
    }
    # 1. Phase-15 folder README
    if P15_README.exists():
        old = sha(P15_README)
        t = P15_README.read_text(encoding="utf-8")
        t = t.replace("- **Current Status:** CURRENT",
                      "- **Current Status:** PROTOCOL FROZEN (design only) / EXECUTION: NOT_STARTED_AND_NOT_AUTHORIZED")
        if "## Phase-15 status reconciliation" not in t:
            t = t.rstrip("\n") + "\n\n## Phase-15 status reconciliation\n\n" + note + "\n"
        P15_README.write_text(t, encoding="utf-8")
        record["phase15_reconciliation"]["phase15_readme"] = {
            "path": "notebooks/phasewise/phase_15_loss_study/README.md",
            "old_sha256": old, "new_sha256": sha(P15_README)}
    # 2. phasewise README roadmap row
    old = sha(PW_README)
    t = PW_README.read_text(encoding="utf-8")
    t = t.replace("| Asymmetric loss functions (L0, L1, L2, L3) to suppress FP | CURRENT (PROTOCOL FROZEN) |",
                  "| Asymmetric loss functions (L0, L1, L2, L3) to suppress FP | PROTOCOL FROZEN (design only); EXECUTION NOT_STARTED_AND_NOT_AUTHORIZED |")
    if "## Phase-15 protocol vs execution" not in t:
        t = t.rstrip("\n") + ("\n\n## Phase-15 protocol vs execution\n\n" + note +
                              "\n\nPhase 15 is a **separate phase** from the post-Phase14 H3 "
                              "gate-resolution branch and is not renumbered.\n")
    PW_README.write_text(t, encoding="utf-8")
    record["phase15_reconciliation"]["phasewise_readme"] = {
        "path": "notebooks/phasewise/README.md",
        "old_sha256": old, "new_sha256": sha(PW_README)}


def main() -> None:
    record = {
        "artifact": "h3_post_adjudication_governance_state",
        "status": WRAPPER,
        "scientific_label": LABEL,
        "generated_by": "scripts/notebooks/sync_h3_adjudication_governance.py",
        "adjudication_artifact": {
            "path": "reports/audits/h3_formal_adjudication.json",
            "sha256": sha(ROOT / "reports" / "audits" / "h3_formal_adjudication.json"),
        },
        "notebook_07": {"path": "notebooks/phasewise/post_phase14_h3_proposal_supply/07_h3_adjudication.ipynb",
                        "sha256": sha(NB07)},
        "governance": {
            "training_performed": False, "inference_performed": False,
            "test_reads": 0, "external_test_reads": 0,
            "checkpoint_changed": False, "threshold_changed": False,
            "frozen_gate_changed": False,
            "h3_adjudication": "PERFORMED",
            "option_b_started": False, "option_c_started": False,
            "phase_15_status": "NOT_STARTED_AND_NOT_AUTHORIZED",
        },
        "synchronized": {},
    }
    update_h3_master(record["synchronized"])
    update_h3_readme(record["synchronized"])
    update_phasewise_index(record["synchronized"])
    reconcile_phase15(record)
    GOV.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print("\n=== GOVERNANCE SYNC SUMMARY ===")
    print(json.dumps(record["synchronized"], indent=2))
    print("Governance artifact:", GOV.relative_to(ROOT), "| sha256:", sha(GOV))


if __name__ == "__main__":
    main()
