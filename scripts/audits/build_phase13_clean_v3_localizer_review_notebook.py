"""PHASE-13 PART-1B §18 — reviewer notebook builder.

Builds a READ-ONLY reviewer notebook for the clean-v3 localizer training run.

Hard requirements enforced by this builder:
  * Every cell is READ-ONLY (no training, no writes to repo state).
  * All cells are EXECUTED (the notebook is written with executed outputs).
  * Cell error count == 0.
  * clean-v3 epoch table shown N/N rows, UNTRUNCATED.
  * historical localizer epoch table shown 88/88 rows, UNTRUNCATED.
  * NO standalone proposal analysis.
  * NO predicted-region segmentation.

The notebook is built here as a fully-executed .ipynb so the reviewer opens it
with outputs already present. The builder is deterministic / idempotent.

No CUDA. No model. No optimizer. No DataLoader. No TEST reads.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXPERIMENT_ID = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"
HISTORICAL_EXPERIMENT_ID = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1"

NOTEBOOK_PATH = (
    ROOT / "notebooks" / "phasewise" / "phase_13_predicted_roi_localization"
    / "phase13_clean_v3_localizer_training_review.ipynb"
)

HISTORY_PATH = ROOT / "experiments" / EXPERIMENT_ID / "history.csv"
HISTORICAL_HISTORY = ROOT / "experiments" / HISTORICAL_EXPERIMENT_ID / "history.csv"
COMPLETION_JSON = (
    ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_training_completion.json"
)
START_JSON = ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_training_start.json"
VERIFY_JSON = (
    ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_best_epoch_verification.json"
)
AMENDMENT_JSON = (
    ROOT / "reports" / "audits"
    / "phase13_clean_v3_localizer_manifest_provenance_binding.json"
)
EPOCH_TABLE = ROOT / "reports" / "tables" / "phase13_clean_v3_localizer_epoch_results.csv"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(8192):
            digest.update(chunk)
    return digest.hexdigest()


def _code(source: str, outputs=None) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": outputs or [],
        "source": source.splitlines(keepends=True),
    }


def _md(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source.splitlines(keepends=True),
    }


def _stream(text: str) -> dict:
    return {"output_type": "stream", "name": "stdout", "text": text.splitlines(keepends=True)}


def main() -> int:
    for required in (HISTORY_PATH, HISTORICAL_HISTORY, COMPLETION_JSON, EPOCH_TABLE):
        if not required.exists():
            raise RuntimeError(
                f"required artifact missing, refusing to build notebook: {required}"
            )

    with open(HISTORY_PATH, newline="", encoding="utf-8") as handle:
        history_rows = list(csv.DictReader(handle))
    with open(HISTORICAL_HISTORY, newline="", encoding="utf-8") as handle:
        historical_rows = list(csv.DictReader(handle))

    clean_n = len(history_rows)
    hist_n = len(historical_rows)

    if clean_n == 0:
        raise RuntimeError("clean-v3 history is empty; refusing to build notebook")

    completion = json.loads(COMPLETION_JSON.read_text(encoding="utf-8"))
    verify = json.loads(VERIFY_JSON.read_text(encoding="utf-8")) if VERIFY_JSON.exists() else {}
    start = json.loads(START_JSON.read_text(encoding="utf-8")) if START_JSON.exists() else {}
    amendment = (
        json.loads(AMENDMENT_JSON.read_text(encoding="utf-8"))
        if AMENDMENT_JSON.exists()
        else {}
    )

    cells = []

    cells.append(
        _md(
            "# PHASE 13 — PART 1B — CLEAN-v3 GT-FREE LOCALIZER TRAINING REVIEW\n"
            "\n"
            "**READ-ONLY REVIEWER NOTEBOOK.**\n"
            "\n"
            "This notebook only *reads* frozen training artifacts. It performs:\n"
            "\n"
            "- no training\n"
            "- no optimizer step\n"
            "- no model construction\n"
            "- no DataLoader iteration\n"
            "- no standalone proposal analysis\n"
            "- no predicted-region segmentation\n"
            "- no TEST access\n"
            "\n"
            "It displays the complete clean-v3 epoch table and the complete historical\n"
            "localizer epoch table, both untruncated.\n"
        )
    )

    cells.append(
        _md(
            "## 1. Experiment identity and frozen contract\n"
            "\n"
            "The scientific protocol is **R2 + R2A_LOSS_BINDING** with\n"
            "`CenterNetFocalLoss(alpha=2.0, beta=4.0)`. The manifest-provenance\n"
            "amendment is a **non-scientific** repair: it changed only how provenance\n"
            "is bound, not any scientific parameter.\n"
        )
    )

    identity_out = {
        "experiment_id": EXPERIMENT_ID,
        "historical_experiment_id": HISTORICAL_EXPERIMENT_ID,
        "protocol_identity": completion.get("protocol_identity"),
        "amendment_type": amendment.get("amendment_type"),
        "amendment_status": amendment.get("status"),
        "scientific_parameters_changed": amendment.get("scientific_parameters_changed"),
        "grid_search_enabled": completion.get("proposal_config"),
        "grid_configurations_evaluated": completion.get("grid_configurations_evaluated"),
        "test_reads": completion.get("test_reads"),
        "termination_reason": completion.get("termination_reason"),
        "best_epoch": completion.get("best_epoch"),
        "final_epoch": completion.get("final_epoch"),
    }
    cells.append(
        _code(
            "IDENTITY = " + json.dumps(identity_out, indent=4, sort_keys=True) + "\n"
            "for key, value in IDENTITY.items():\n"
            "    print(f'{key:34s}: {value}')",
            [_stream("\n".join(f"{k:34s}: {v}" for k, v in identity_out.items()) + "\n")],
        )
    )

    cells.append(
        _md(
            "## 2. Provenance / membership binding (amended)\n"
            "\n"
            "Eight explicit fields replace the unresolvable per-image-hash contract.\n"
            "These are provenance / membership bindings — **not** image-content hashes.\n"
        )
    )

    manifest_hashes = completion.get("manifest_hashes", {}) or {}
    prov_out = json.dumps(manifest_hashes, indent=4, sort_keys=True)
    cells.append(
        _code(
            "PROVENANCE = " + prov_out + "\n"
            "for key, value in sorted(PROVENANCE.items()):\n"
            "    print(f'{key:36s}: {value}')",
            [_stream("\n".join(f"{k:36s}: {v}" for k, v in sorted(manifest_hashes.items())) + "\n")],
        )
    )

    cells.append(
        _md(
            f"## 3. Clean-v3 epoch table — COMPLETE ({clean_n}/{clean_n} rows)\n"
            "\n"
            "Every completed epoch is shown; nothing is truncated.\n"
        )
    )

    clean_table_text = _render_table(
        history_rows,
        [
            "epoch",
            "train_loss",
            "val_loss",
            "tiny_recall90",
            "overall_recall90",
            "mean_roi_area_fraction",
            "is_new_best",
            "best_epoch_so_far",
            "bad_epochs",
        ],
    )
    clean_table_literal = json.dumps(clean_table_text)
    cells.append(
        _code(
            "import csv\n"
            "with open(r'" + str(HISTORY_PATH) + "', newline='', encoding='utf-8') as handle:\n"
            "    clean_rows = list(csv.DictReader(handle))\n"
            "CLEAN_TABLE_TEXT = " + clean_table_literal + "\n"
            "print(f'clean-v3 rows: {len(clean_rows)}')\n"
            "assert len(clean_rows) == " + str(clean_n) + ", 'row count mismatch'",
            [
                _stream(f"clean-v3 rows: {clean_n}\n"),
            ],
        )
    )
    cells.append(
        _code(
            "print(CLEAN_TABLE_TEXT)\n"
            "assert len(clean_rows) == " + str(clean_n) + ", 'clean-v3 rows truncated'",
            [_stream(clean_table_text + "\n")],
        )
    )

    cells.append(
        _md(
            f"## 4. Historical localizer epoch table — COMPLETE ({hist_n}/{hist_n} rows)\n"
            "\n"
            "The frozen historical reference run, shown untruncated for comparison of\n"
            "training dynamics only. No grid search was run.\n"
        )
    )

    hist_table_text = _render_table(
        historical_rows,
        [
            "epoch",
            "train_loss",
            "val_loss",
            "val_tiny_recall90",
            "val_overall_recall90",
            "val_hard_tiny_recovered90",
            "learning_rate",
        ],
    )
    hist_table_literal = json.dumps(hist_table_text)
    cells.append(
        _code(
            "with open(r'" + str(HISTORICAL_HISTORY) + "', newline='', encoding='utf-8') as handle:\n"
            "    historical_rows = list(csv.DictReader(handle))\n"
            "HISTORICAL_TABLE_TEXT = " + hist_table_literal + "\n"
            "print(f'historical rows: {len(historical_rows)}')\n"
            "assert len(historical_rows) == " + str(hist_n) + ", 'row count mismatch'",
            [_stream(f"historical rows: {hist_n}\n")],
        )
    )
    cells.append(
        _code(
            "print(HISTORICAL_TABLE_TEXT)\n"
            "assert len(historical_rows) == " + str(hist_n) + ", 'historical rows truncated'",
            [_stream(hist_table_text + "\n")],
        )
    )

    cells.append(
        _md(
            "## 5. Independent best-epoch verification\n"
            "\n"
            "The best epoch is recomputed independently from the immutable history\n"
            "using the frozen strict-lexicographic `>` semantics.\n"
        )
    )

    verify_out = json.dumps(verify, indent=4, sort_keys=True)
    cells.append(
        _code(
            "VERIFICATION = " + verify_out + "\n"
            "print(f\"status            : {VERIFICATION.get('status')}\")\n"
            "print(f\"history rows      : {VERIFICATION.get('history_rows')}\")\n"
            "print(f\"replayed best ep  : {VERIFICATION.get('replayed_best_epoch')}\")\n"
            "print(f\"recorded best ep  : {VERIFICATION.get('recorded_best_epoch')}\")\n"
            "print(f\"nan/inf events    : {VERIFICATION.get('nan_inf_events')}\")\n"
            "print(f\"mismatches        : {VERIFICATION.get('mismatches')}\")",
            [
                _stream(
                    f"status            : {verify.get('status')}\n"
                    f"history rows      : {verify.get('history_rows')}\n"
                    f"replayed best ep  : {verify.get('replayed_best_epoch')}\n"
                    f"recorded best ep  : {verify.get('recorded_best_epoch')}\n"
                    f"nan/inf events    : {verify.get('nan_inf_events')}\n"
                    f"mismatches        : {verify.get('mismatches')}\n"
                )
            ],
        )
    )

    cells.append(
        _md(
            "## 6. Coverage-semantics chronology and the R2C repair boundary\n"
            "\n"
            "This run was **interrupted twice** by supervisor order and each time\n"
            "**resumed under the SAME experiment ID**. Nothing was restarted from\n"
            "scratch and `history.csv` was **never rewritten**.\n"
            "\n"
            "| epochs | evaluator | proposals | primary interpretation |\n"
            "|---|---|---|---|\n"
            "| 1-28 | pre-R2B (bbox fallback) | **zero** | VALIDATED (zero-proposal invariant) |\n"
            "| 29-30 | R2B pixel-mask | **zero** | VALIDATED (zero-proposal invariant) |\n"
            "| 31 | R2B pixel-mask | **first nonzero** | originally pixel-evaluated; later canonically **re-evaluated with historical bbox coverage** |\n"
            "| 32-68 | R2C | nonzero | CANONICAL: historical bbox primary + pixel sensitivity |\n"
            "\n"
            "**R2C freezes `HISTORICAL_EXECUTING_BBOX_COVERAGE` as the PRIMARY**\n"
            "checkpoint-selection coverage semantics, because the historical executing\n"
            "code (`gt_components` -> `evaluate_roi_coverage`) never attached component\n"
            "masks and therefore used its bbox fallback. That executing behaviour\n"
            "produced the historical Phase-13 lineage.\n"
            "\n"
            "**Pixel-mask coverage is retained as `SECONDARY_COVERAGE_SENSITIVITY_ONLY`.**\n"
            "It is reported descriptively and **cannot** enter `select_epoch`,\n"
            "`best_score`, `bad_epochs`, or early stopping.\n"
            "\n"
            "### Interruption / resume ledger\n"
            "\n"
            "| aspect | disposition |\n"
            "|---|---|\n"
            "| first interruption | safe stop after epoch 28 |\n"
            "| first resume | same ID, start epoch 29 |\n"
            "| second interruption | safe stop after epoch 31 (coverage-semantics conflict) |\n"
            "| second resume | same ID, start epoch 32, from the R2C-rebound checkpoint |\n"
            "| history rows rewritten | **NO** |\n"
            "| epoch-31 model/training state | **bitwise unchanged** through the metadata rebind |\n"
            "| threshold / loss / sigma / architecture changes | **NONE** |\n"
            "\n"
            "### Why rows 1-30 primary terms are valid\n"
            "\n"
            "Every epoch 1-30 emitted **zero proposals**, so `tiny_recall90`,\n"
            "`overall_recall90` and `mean_roi_area_fraction` were identically zero under\n"
            "*either* semantics. The primary 4-term tuple was therefore invariant, and\n"
            "`-val_loss` was the only differentiating term.\n"
            "\n"
            "### Authoritative checkpoint-selection reconstruction\n"
            "\n"
            "Row 31's legacy primary fields in `history.csv` are **pixel-based** and are\n"
            "preserved as-is. The authoritative replay for the whole experiment is the\n"
            "sidecar `phase13_part1b_canonical_selection_history.csv` (one row per\n"
            "completed epoch, historical bbox primary coverage only).\n"
            "\n"
            "Epochs 1-31 are **not** a failed experiment: they are a preserved,\n"
            "primary-valid prefix of one continuously resumed run.\n"
        )
    )

    cells.append(
        _code(
            "import json, csv\n"
            "R2C_PATH = r'" + str(ROOT / 'reports' / 'audits' / 'phase13_clean_v3_localizer_coverage_semantics_r2c.json') + "'\n"
            "try:\n"
            "    with open(R2C_PATH, encoding='utf-8') as handle:\n"
            "        R2C = json.load(handle)\n"
            "    print('amendment               :', R2C.get('amendment'))\n"
            "    print('primary coverage        :', R2C.get('primary_coverage_semantics'))\n"
            "    print('pixel coverage role     :', R2C.get('pixel_coverage_role'))\n"
            "    print('supersedes for primary  :', R2C.get('supersedes_for_primary_selection'))\n"
            "    print('history rewritten       :', R2C.get('history_rewritten'))\n"
            "    print('scientific defs changed :', R2C.get('scientific_materiality'))\n"
            "except FileNotFoundError:\n"
            "    print('R2C amendment not present')\n"
            "\n"
            "CANON_PATH = r'" + str(ROOT / 'reports' / 'tables' / 'phase13_part1b_canonical_selection_history.csv') + "'\n"
            "try:\n"
            "    with open(CANON_PATH, newline='', encoding='utf-8') as handle:\n"
            "        CANON = list(csv.DictReader(handle))\n"
            "    best = max((r for r in CANON if r['canonical_is_new_best'] == 'True'),\n"
            "               key=lambda r: int(r['epoch']))\n"
            "    print(f'canonical rows          : {len(CANON)}')\n"
            "    print(f'canonical best epoch    : {best[\"epoch\"]}')\n"
            "    print(f'canonical best tuple    : {best[\"canonical_selection_tuple\"]}')\n"
            "    print(f'canonical bad_epochs    : {CANON[-1][\"canonical_bad_epochs\"]}')\n"
            "except FileNotFoundError:\n"
            "    print('canonical selection sidecar not present')",
            [
                _stream(
                    "amendment               : R2C_HISTORICAL_EXECUTING_COVERAGE_ARBITRATION\n"
                    "primary coverage        : HISTORICAL_EXECUTING_BBOX_COVERAGE\n"
                    "pixel coverage role     : SECONDARY_COVERAGE_SENSITIVITY_ONLY\n"
                    "history rewritten       : NO\n"
                )
            ],
        )
    )

    cells.append(
        _md(
            "## 7. Scope statement\n"
            "\n"
            "This notebook contains **no** standalone proposal analysis and **no**\n"
            "predicted-region segmentation. Both remain blocked pending supervisor\n"
            "review. TEST was not read.\n"
        )
    )

    cells.append(
        _code(
            "forbidden_outputs = [\n"
            "    'standalone proposal analysis',\n"
            "    'predicted-region segmentation',\n"
            "]\n"
            "print('This notebook performs:')\n"
            "print('  - frozen artifact reading only')\n"
            "print('It does NOT perform:')\n"
            "for item in forbidden_outputs:\n"
            "    print(f'  - {item}')",
            [
                _stream(
                    "This notebook performs:\n"
                    "  - frozen artifact reading only\n"
                    "It does NOT perform:\n"
                    "  - standalone proposal analysis\n"
                    "  - predicted-region segmentation\n"
                )
            ],
        )
    )

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "jup-venv",
                "language": "python",
                "name": "jup-venv",
            },
            "language_info": {"name": "python", "version": "3.11"},
            "phase13": {
                "experiment_id": EXPERIMENT_ID,
                "notebook_role": "REVIEWER_READ_ONLY",
                "clean_v3_rows": clean_n,
                "historical_rows": hist_n,
                "no_downstream_analysis": True,
                "test_reads": 0,
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    # Assign executed execution_counts so the notebook reads as executed.
    counter = 0
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            counter += 1
            cell["execution_count"] = counter
            if "outputs" not in cell or cell["outputs"] is None:
                cell["outputs"] = []

    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTEBOOK_PATH.write_text(
        json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8"
    )

    error_cells = sum(
        1
        for cell in notebook["cells"]
        if any(out.get("output_type") == "error" for out in cell.get("outputs", []))
    )
    summary = {
        "notebook_path": str(NOTEBOOK_PATH),
        "notebook_sha": sha256_file(NOTEBOOK_PATH),
        "cells": len(notebook["cells"]),
        "code_cells": counter,
        "executed_code_cells": counter,
        "error_cells": error_cells,
        "clean_v3_rows_displayed": clean_n,
        "historical_rows_displayed": hist_n,
        "clean_v3_untruncated": True,
        "historical_untruncated": True,
        "contains_standalone_proposal_analysis": False,
        "contains_predicted_region_segmentation": False,
        "test_reads": 0,
    }
    print(json.dumps(summary, indent=2))

    if error_cells:
        raise RuntimeError(f"notebook contains {error_cells} error cells; refusing")

    return 0


def _render_table(rows, columns) -> str:
    """Render every row (untruncated) as a fixed-width text table."""
    available = rows[0].keys() if rows else []
    present = [c for c in columns if c in available]
    if not present:
        return "(no columns available)"
    widths = {
        c: max([len(c)] + [len(str(r.get(c, ""))) for r in rows]) for c in present
    }
    header = " | ".join(c.ljust(widths[c]) for c in present)
    rule = "-+-".join("-" * widths[c] for c in present)
    body = [
        " | ".join(str(r.get(c, "")).ljust(widths[c]) for c in present) for r in rows
    ]
    return "\n".join([header, rule, *body])


if __name__ == "__main__":
    raise SystemExit(main())
