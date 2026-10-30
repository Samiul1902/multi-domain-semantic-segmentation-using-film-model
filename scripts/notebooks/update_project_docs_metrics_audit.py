"""Additively synchronize master documentation with the project-wide
evaluation-metrics audit.

Targets (all additive, idempotent via markers):
  - README.md
  - PROJECT_MASTER_PLAN.md
  - notebooks/phasewise/00_PHASEWISE_PROJECT_INDEX.ipynb

Records old/new SHAs in reports/audits/project_evaluation_notebook_sha_updates.json
(shared with the notebook-update scripts).

No frozen metric, gate, threshold, or checkpoint is changed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import nbformat

ROOT = Path(r"D:/Softfors/jup")
README = ROOT / "README.md"
PLAN = ROOT / "PROJECT_MASTER_PLAN.md"
INDEX_NB = ROOT / "notebooks" / "phasewise" / "00_PHASEWISE_PROJECT_INDEX.ipynb"
REC = ROOT / "reports" / "audits" / "project_evaluation_notebook_sha_updates.json"

BEGIN = "<!-- BEGIN PROJECT-EVALUATION-METRICS-AUDIT -->"
END = "<!-- END PROJECT-EVALUATION-METRICS-AUDIT -->"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def upsert_block(text: str, block: str) -> str:
    """Replace an existing marker block, else append it."""
    if BEGIN in text and END in text:
        pre = text[: text.index(BEGIN)]
        post = text[text.index(END) + len(END):]
        return pre + block + post
    sep = "" if text.endswith("\n") else "\n"
    return text + sep + "\n" + block + "\n"


def build_block() -> str:
    audit_nb = ROOT / "notebooks" / "evaluation" / "project_evaluation_metrics_audit.ipynb"
    module = ROOT / "src" / "metrics" / "evaluation_metrics.py"
    backfill = ROOT / "reports" / "audits" / "project_evaluation_metrics_backfill.json"
    registry = ROOT / "reports" / "audits" / "project_metric_registry.json"
    inv_j = ROOT / "reports" / "audits" / "project_evaluation_metrics_inventory.json"
    inv_c = ROOT / "reports" / "tables" / "project_evaluation_metrics_inventory.csv"
    prop = ROOT / "reports" / "audits" / "project_evaluation_proposal_metrics_backfill.json"

    rows = [
        ("Audit notebook", "`notebooks/evaluation/project_evaluation_metrics_audit.ipynb`"),
        ("Audit notebook SHA-256", f"`{sha(audit_nb)}`"),
        ("Reusable metric module", "`src/metrics/evaluation_metrics.py`"),
        ("Metric module SHA-256", f"`{sha(module)}`"),
        ("Metric registry", "`reports/audits/project_metric_registry.json` (35 metrics)"),
        ("Metric registry SHA-256", f"`{sha(registry)}`"),
        ("Project metric inventory", "`reports/audits/project_evaluation_metrics_inventory.json` / `.csv` (12 rows)"),
        ("Inventory JSON SHA-256", f"`{sha(inv_j)}`"),
        ("Inventory CSV SHA-256", f"`{sha(inv_c)}`"),
        ("Descriptive backfill artifact", "`reports/audits/project_evaluation_metrics_backfill.json`"),
        ("Descriptive backfill SHA-256", f"`{sha(backfill)}`"),
        ("Proposal backfill artifact", "`reports/audits/project_evaluation_proposal_metrics_backfill.json`"),
        ("Proposal backfill SHA-256", f"`{sha(prop)}`"),
        ("Safe-replay verdict", "`REPLAY_PERFORMED_LAWFULLY` (8/8 conditions)"),
        ("Reproduction gate", "4/4 arms exact (GLOBAL / ORACLE / PREDICTED / H3)"),
        ("Boundary units", "pixels (no pixel-spacing metadata; never mm)"),
        ("New-metric label", "`DESCRIPTIVE_SUPPORTING_METRIC__NOT_PROSPECTIVE_GATE`"),
        ("H3-specific label", "`DESCRIPTIVE_SUPPORTING_METRIC__NOT_H3_GATE`"),
        ("TEST reads", "0"),
        ("Frozen gates changed", "False"),
        ("Terminal state", "`PROJECT_EVALUATION_METRICS_AUDIT_COMPLETE__H3_ADJUDICATION_PENDING`"),
    ]
    table = "| Item | Value |\n|------|-------|\n" + "\n".join(f"| {k} | {v} |" for k, v in rows)
    return (
        f"{BEGIN}\n"
        "## Project-Wide Evaluation-Metrics Audit (Post-H3-Downstream)\n\n"
        "Audit + standardization + descriptive backfill of the completed KUB research\n"
        "line (Phases 09-14 and the post-Phase14 H3 training / supply / downstream\n"
        "steps). This is **not** a new hypothesis test: no frozen gate, threshold or\n"
        "checkpoint is changed, and the frozen H3 formal metric domain (detection =\n"
        "component overlap >= 1 px; `TinyRecall_H3 = 59/72`, `R_H3 = 2/15`) is\n"
        "unchanged.\n\n"
        f"{table}\n\n"
        "Formal H3 adjudication (Notebook 07) remains **PENDING** and requires separate\n"
        "supervisor authorization.\n"
        f"{END}"
    )


def main() -> None:
    block = build_block()
    record = {"readme": {}, "master_plan": {}, "index_notebook": {}}

    # ── README ──────────────────────────────────────────────────────────────
    old = sha(README)
    README.write_text(upsert_block(README.read_text(encoding="utf-8"), block), encoding="utf-8")
    record["readme"] = {"path": "README.md", "old_sha256": old, "new_sha256": sha(README)}

    # ── Master plan ─────────────────────────────────────────────────────────
    old = sha(PLAN)
    plan_block = (
        f"{BEGIN}\n"
        "## Project-Wide Evaluation-Metrics Audit (audit record)\n\n"
        "A project-wide evaluation-metrics audit, standardization and descriptive\n"
        "backfill was completed across the finished KUB research line. It produced a\n"
        "reusable metric module (`src/metrics/evaluation_metrics.py`), a metric registry\n"
        "(`reports/audits/project_metric_registry.json`), a project metric inventory, and\n"
        "a single logged deterministic VAL-only replay that backfilled previously\n"
        "unpersisted pixel / boundary / calibration / uncertainty metrics.\n\n"
        "All new metrics are labelled `DESCRIPTIVE_SUPPORTING_METRIC__NOT_PROSPECTIVE_GATE`\n"
        "and are **not** promoted into any frozen gate. The H3 formal adjudication remains\n"
        "pending; Phase 15 remains NOT_STARTED_AND_NOT_AUTHORIZED.\n\n"
        "See `notebooks/evaluation/project_evaluation_metrics_audit.ipynb`.\n"
        f"{END}"
    )
    PLAN.write_text(upsert_block(PLAN.read_text(encoding="utf-8"), plan_block), encoding="utf-8")
    record["master_plan"] = {"path": "PROJECT_MASTER_PLAN.md", "old_sha256": old, "new_sha256": sha(PLAN)}

    # ── Master index notebook (additive cells) ──────────────────────────────
    old = sha(INDEX_NB)
    nb = nbformat.read(str(INDEX_NB), as_version=4)
    marker = "Project-Wide Evaluation-Metrics Audit"
    if not any(marker in c.source for c in nb.cells):
        nb.cells.append(nbformat.v4.new_markdown_cell(
            "## Project-Wide Evaluation-Metrics Audit\n\n"
            "Audit + standardization + descriptive backfill of the completed KUB research\n"
            "line. Terminal state `PROJECT_EVALUATION_METRICS_AUDIT_COMPLETE__H3_ADJUDICATION_PENDING`.\n\n"
            "- Notebook: `notebooks/evaluation/project_evaluation_metrics_audit.ipynb`\n"
            "- Metric module: `src/metrics/evaluation_metrics.py`\n"
            "- Registry: `reports/audits/project_metric_registry.json`\n"
            "- All new metrics: `DESCRIPTIVE_SUPPORTING_METRIC__NOT_PROSPECTIVE_GATE`"
        ))
        nb.cells.append(nbformat.v4.new_code_cell(
            "import json as _json\n"
            "from pathlib import Path as _Path\n"
            "_ROOT = _Path('D:/Softfors/jup')\n"
            "_bf = _json.loads((_ROOT / 'reports/audits/project_evaluation_metrics_backfill.json').read_text(encoding='utf-8'))\n"
            "print('backfill status :', _bf['status'])\n"
            "print('safe replay     :', _bf['safe_replay_rule']['verdict'])\n"
            "print('reproduction    :', {a: (r['match'] and r['tiny_match']) for a, r in _bf['reproduction_gate'].items()})\n"
            "print('TEST reads      :', _bf['governance']['test_reads'])\n"
            "print('terminal state  : PROJECT_EVALUATION_METRICS_AUDIT_COMPLETE__H3_ADJUDICATION_PENDING')"
        ))
        nbformat.write(nb, str(INDEX_NB))
    record["index_notebook"] = {
        "path": "notebooks/phasewise/00_PHASEWISE_PROJECT_INDEX.ipynb",
        "old_sha256": old, "new_sha256": sha(INDEX_NB),
        "change": "appended project-wide evaluation-metrics audit pointer section",
    }

    # ── Record ──────────────────────────────────────────────────────────────
    rec = json.loads(REC.read_text(encoding="utf-8")) if REC.exists() else {
        "artifact": "project_evaluation_notebook_sha_updates",
        "status": "NOTEBOOK_SHA_TRANSITIONS_RECORDED",
        "note": "Additive notebook updates performed by the project-wide evaluation-metrics audit.",
        "transitions": [],
    }
    for key in ("readme", "master_plan", "index_notebook"):
        entry = dict(record[key])
        entry["frozen_metrics_changed"] = False
        entry["kind"] = "documentation" if key != "index_notebook" else "notebook"
        rec["transitions"] = [t for t in rec["transitions"] if t.get("path") != entry["path"]] + [entry]
    REC.write_text(json.dumps(rec, indent=2), encoding="utf-8")

    print("Documentation synchronized.")
    for key in ("readme", "master_plan", "index_notebook"):
        r = record[key]
        print(f"  {r['path']}: {r['old_sha256'][:16]} -> {r['new_sha256'][:16]}")
    print("Record:", REC.relative_to(ROOT))


if __name__ == "__main__":
    main()
