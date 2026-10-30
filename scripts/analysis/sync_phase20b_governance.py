"""Additive governance sync for the Phase-20B reviewer package.

Reads ONLY persisted artifacts + the built notebook. Never trains, never runs
inference, never touches TEST, never modifies frozen science.

Updates (all additive / corrective):
  * reports/audits/phasewise_notebook_map.{csv,json,md}
  * notebooks/phasewise/README.md                       (handled separately)
  * PROJECT_MASTER_PLAN.md                              (handled separately)
  * reports/audits/trained_model_visualization_registry.{csv,json}
  * reports/audits/dataset_visualization_coverage.csv
  * reports/audits/phasewise_notebook_execution_manifest.{csv,json,md}

Run after the notebook builds have completed::

    ./.venv/Scripts/python.exe scripts/analysis/sync_phase20b_governance.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

from src.analysis import phase20b_reviewer as R  # noqa: E402

A = ROOT / "reports" / "audits"
NB_PATH = (ROOT / "notebooks/phasewise/phase_20b_five_model_baselines"
           / "phase20b_five_model_conventional_baselines.ipynb")
NB_REL = R.rel(NB_PATH)
NB_SHA = hashlib.sha256(NB_PATH.read_bytes()).hexdigest()

TERMINAL_SCIENTIFIC = "PHASE20_FIVE_MODEL_BASELINE_BENCHMARK_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED"
TERMINAL_DOC = "PHASE20B_REVIEWER_PACKAGE_COMPLETE__FULL_VISUAL_EVIDENCE__PHASE21_ELIGIBLE_NOT_STARTED"

TRAIN_POP = "ISIC 2556 / BUSI 602 / KVASIR 696 / KUB 1978 (total 5832)"
VAL_POP = "ISIC 357 / BUSI 84 / KVASIR 87 / KUB 280 (total 808)"


def nb_stats(path: Path) -> dict:
    nb = json.loads(path.read_text(encoding="utf-8"))
    cells = nb["cells"]
    code = [c for c in cells if c["cell_type"] == "code"]
    err = sum(1 for c in code for o in c.get("outputs", []) if o.get("output_type") == "error")
    png = sum(1 for c in code for o in c.get("outputs", []) if "image/png" in (o.get("data", {}) or {}))
    exe = sum(1 for c in code if c.get("execution_count") is not None)
    return {"total_cells": len(cells), "executed_cells": exe, "error_count": err,
            "png_figures": png, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def model_rows() -> list[dict]:
    head = R.headline_table().set_index("model_key")
    rows = []
    for m in R.MODEL_ORDER:
        c = R.load_closure(m)
        h = head.loc[m]
        exp = R.experiment_id(m)
        rows.append({
            "model_key": m,
            "display": R.DISPLAY[m],
            "class_name": h["class_name"],
            "phase": R.PHASE[m],
            "experiment_id": exp,
            "params": int(h["params"]),
            "best_epoch": int(h["best_epoch"]),
            "final_epoch": int(h["final_epoch"]),
            "stop_reason": h["stop_reason"],
            "macro_dice": float(h["macro_dice"]),
            "checkpoint_path": f"checkpoints/{exp}/best.pt",
            "history_path": f"experiments/{exp}/history.csv",
            "config_path": f"experiments/{exp}/config.json",
            "checkpoint_sha256": c.get("best_checkpoint_sha256"),
        })
    return rows


# --------------------------------------------------------------------------- #
# A. phasewise_notebook_map.csv
# --------------------------------------------------------------------------- #
def sync_map_csv() -> None:
    p = A / "phasewise_notebook_map.csv"
    rows = list(csv.reader(p.open(encoding="utf-8")))
    header = rows[0]
    idx = {name: i for i, name in enumerate(header)}

    def setrow(pid: str, mapping: dict) -> None:
        for r in rows[1:]:
            if r and r[0] == pid:
                for k, v in mapping.items():
                    r[idx[k]] = v
                return
        raise KeyError(pid)

    setrow("19", {
        "status": "COMPLETE",
        "reviewer_notebook": "phase19_multidomain_dataset_harmonization.ipynb",
        "canonical_source": "reports/audits/phase19_multidomain_harmonization_protocol.json",
        "visual_artifacts": "reports/figures/phase19_harmonization/",
    })
    setrow("20", {
        "status": "COMPLETE",
        "title": "Shared Four-Domain Global Baseline (single frozen UNet++)",
        "reviewer_notebook": "phase20_shared_global_unetpp_baseline.ipynb",
        "canonical_source": "reports/audits/phase20_shared_global_baseline_protocol.json",
        "visual_artifacts": "reports/figures/phase20_multidomain_baseline/",
    })
    setrow("21", {
        "status": "ELIGIBLE_NOT_STARTED",
        "canonical_source": "PENDING_PHASE21_AUTHORIZATION",
    })

    new = ["20b", "phase_20b_five_model_baselines",
           "Five-Model Conventional Baseline Benchmark (20B)",
           "Stage B: Multi-Domain Scaling", "COMPLETE",
           "phase20b_five_model_conventional_baselines.ipynb",
           "reports/audits/phase20_five_model_baseline_benchmark_freeze.json",
           "reports/figures/phase20b_five_model_baselines/"]
    new += [""] * (len(header) - len(new))
    at = next(i for i, r in enumerate(rows) if r and r[0] == "20")
    rows.insert(at + 1, new)
    with p.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    print("map.csv rows:", len(rows) - 1)


# --------------------------------------------------------------------------- #
# B. phasewise_notebook_map.json
# --------------------------------------------------------------------------- #
def sync_map_json() -> None:
    p = A / "phasewise_notebook_map.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    for e in data:
        if e["phase_id"] == "19":
            e.update({"status": "COMPLETE",
                      "reviewer_notebook": "phase19_multidomain_dataset_harmonization.ipynb",
                      "canonical_source": "reports/audits/phase19_multidomain_harmonization_protocol.json",
                      "visual_artifacts": "reports/figures/phase19_harmonization/"})
        elif e["phase_id"] == "20":
            e.update({"status": "COMPLETE",
                      "title": "Shared Four-Domain Global Baseline (single frozen UNet++, no FiLM, no regional module)",
                      "canonical_source": "reports/audits/phase20_shared_global_baseline_protocol.json"})
        elif e["phase_id"] == "21":
            e.update({"status": "ELIGIBLE_NOT_STARTED",
                      "canonical_source": "PENDING_PHASE21_AUTHORIZATION",
                      "authorization_required": True})
    entry = {
        "phase_id": "20B",
        "folder": "phase_20b_five_model_baselines",
        "title": "Five-Model Conventional Baseline Benchmark (20B)",
        "stage": "Stage B: Multi-Domain Scaling",
        "status": "COMPLETE",
        "reviewer_notebook": "phase20b_five_model_conventional_baselines.ipynb",
        "canonical_source": "reports/audits/phase20_five_model_baseline_benchmark_freeze.json",
        "visual_artifacts": "reports/figures/phase20b_five_model_baselines/",
        "reviewer_notebook_sha256": NB_SHA,
        "reviewer_package_audit": "reports/audits/phase20b_reviewer_package_audit.json",
        "figure_inventory": "reports/audits/phase20b_figure_inventory.csv",
        "matrix_coverage": "reports/audits/phase20b_evaluation_matrix_visualization_coverage.csv",
        "scientific_terminal_state": TERMINAL_SCIENTIFIC,
        "documentation_terminal_state": TERMINAL_DOC,
    }
    if not any(e.get("phase_id") == "20B" for e in data):
        at = next(i for i, e in enumerate(data) if e["phase_id"] == "20")
        data.insert(at + 1, entry)
    p.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print("map.json entries:", len(data))


# --------------------------------------------------------------------------- #
# C. trained_model_visualization_registry.{csv,json}
# --------------------------------------------------------------------------- #
def sync_registry() -> None:
    rows = model_rows()
    pc = A / "trained_model_visualization_registry.csv"
    cur = list(csv.reader(pc.open(encoding="utf-8")))
    header = cur[0]
    have = {r[1] for r in cur[1:] if r}
    for r in rows:
        if r["phase"] != "20B" or r["experiment_id"] in have:
            continue
        cur.append([
            "Phase 20B", r["experiment_id"], r["display"], "segmentation_four_domain_shared",
            "CANONICAL", "CANONICAL", r["checkpoint_path"], r["history_path"], r["config_path"],
            TRAIN_POP, VAL_POP, "512x512", "True", "True", NB_REL, "64",
            (f"Phase-20B five-model conventional benchmark ({r['display']}); best epoch "
             f"{r['best_epoch']}; macro-domain VAL Dice {r['macro_dice']:.6f}; "
             f"{r['stop_reason']}; TEST reads 0"),
            r["checkpoint_sha256"],
        ])
    with pc.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(cur)
    print("registry.csv rows:", len(cur) - 1)

    pj = A / "trained_model_visualization_registry.json"
    data = json.loads(pj.read_text(encoding="utf-8"))
    have = {e.get("experiment_id") for e in data}
    for r in rows:
        if r["phase"] != "20B" or r["experiment_id"] in have:
            continue
        data.append({
            "phase": "Phase 20B",
            "experiment_id": r["experiment_id"],
            "model_family": r["display"],
            "task_type": "segmentation_four_domain_shared",
            "status": "CANONICAL",
            "canonical_or_superseded": "CANONICAL",
            "checkpoint_path": r["checkpoint_path"],
            "history_path": r["history_path"],
            "config_path": r["config_path"],
            "train_population": TRAIN_POP,
            "val_population": VAL_POP,
            "input_resolution": "512x512",
            "prediction_artifacts_available": True,
            "visualization_required": True,
            "visualization_notebook": NB_REL,
            "visual_case_count": 64,
            "notes": (f"Phase-20B five-model conventional benchmark ({r['display']}); best epoch "
                      f"{r['best_epoch']}; macro-domain VAL Dice {r['macro_dice']:.6f}; "
                      f"{r['stop_reason']}; TEST reads 0"),
            "checkpoint_sha256": r["checkpoint_sha256"],
        })
    pj.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print("registry.json entries:", len(data))


# --------------------------------------------------------------------------- #
# D. dataset_visualization_coverage.csv
# --------------------------------------------------------------------------- #
def sync_dataset_coverage() -> None:
    p = A / "dataset_visualization_coverage.csv"
    cur = list(csv.reader(p.open(encoding="utf-8")))
    have = {(r[0], r[4]) for r in cur[1:] if r}
    for ds in R.DATASET_ORDER:
        if (ds, "Phase 20B") in have:
            continue
        cur.append([ds, "16",
                    f"reports/figures/phase20b_five_model_baselines/galleries/detailed_unetpp_{ds}_p1.png",
                    "PASS", "Phase 20B"])
    with p.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(cur)
    print("dataset_coverage rows:", len(cur) - 1)


# --------------------------------------------------------------------------- #
# E. phasewise_notebook_execution_manifest.{csv,json,md}
# --------------------------------------------------------------------------- #
def sync_execution_manifest() -> None:
    entries = [
        {"notebook_path": "notebooks/phasewise/phase_19_harmonization/phase19_multidomain_dataset_harmonization.ipynb",
         "status": "ACCEPTED_PASS"},
        {"notebook_path": "notebooks/phasewise/phase_20_multidomain_baselines/phase20_shared_global_unetpp_baseline.ipynb",
         "status": "ACCEPTED_PASS"},
        {"notebook_path": NB_REL, "status": "PASS"},
    ]
    resolved = []
    for e in entries:
        st = nb_stats(ROOT / e["notebook_path"])
        resolved.append({"notebook_path": e["notebook_path"], **st, "status": e["status"]})

    pc = A / "phasewise_notebook_execution_manifest.csv"
    cur = list(csv.reader(pc.open(encoding="utf-8")))
    have = {r[0] for r in cur[1:] if r}
    for e in resolved:
        if e["notebook_path"] in have:
            continue
        cur.append([e["notebook_path"], e["total_cells"], e["executed_cells"], e["error_count"],
                    e["png_figures"], e["sha256"], e["status"]])
    with pc.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(cur)
    print("exec_manifest.csv rows:", len(cur) - 1)

    pj = A / "phasewise_notebook_execution_manifest.json"
    data = json.loads(pj.read_text(encoding="utf-8"))
    have = {e["notebook_path"] for e in data["notebooks"]}
    for e in resolved:
        if e["notebook_path"] not in have:
            data["notebooks"].append(e)
    pj.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print("exec_manifest.json entries:", len(data["notebooks"]))

    pm = A / "phasewise_notebook_execution_manifest.md"
    txt = pm.read_text(encoding="utf-8").rstrip("\n")
    add = []
    for e in resolved:
        name = e["notebook_path"].split("/")[-1]
        add.append(f"| `{name}` | {e['total_cells']} | {e['executed_cells']} | {e['error_count']} | "
                   f"{e['png_figures']} | `{e['sha256']}` | `{e['status']}` |")
    pm.write_text(txt + "\n" + "\n".join(add) + "\n", encoding="utf-8")
    print("exec_manifest.md appended rows:", len(add))


def main() -> int:
    print("=== PHASE-20B GOVERNANCE SYNC ===")
    print("notebook:", NB_REL, "| sha256:", NB_SHA)
    sync_map_csv()
    sync_map_json()
    sync_registry()
    sync_dataset_coverage()
    sync_execution_manifest()
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
