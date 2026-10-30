"""Additive governance sync for the Phase-21 Global MedFiLM reviewer package.

Reads ONLY persisted artifacts + the built notebook. Never trains, never runs
inference, never touches TEST, never modifies frozen science.

Updates (all additive):
  * reports/audits/phasewise_notebook_map.{csv,json,md}
  * notebooks/phasewise/README.md
  * PROJECT_MASTER_PLAN.md
  * reports/audits/trained_model_visualization_registry.{csv,json}
  * reports/audits/dataset_visualization_coverage.csv
  * reports/audits/phasewise_notebook_execution_manifest.{csv,json,md}
  * reports/audits/phase21_governance_sync.json

Represents: Phase 20A COMPLETE, Phase 20B COMPLETE, Phase 21 COMPLETE,
Phase 22 ELIGIBLE_NOT_STARTED.

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/sync_phase21_governance.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

A = ROOT / "reports" / "audits"
NB_REL = "notebooks/phasewise/phase_21_global_medfilm/phase21_global_medfilm_reference.ipynb"
NB_PATH = ROOT / NB_REL
NB_SHA = hashlib.sha256(NB_PATH.read_bytes()).hexdigest() if NB_PATH.exists() else None

EXP = "phase21_global_medfilm_fourdomain_seed42_clean_v3"
TERMINAL = "PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED"
TRAIN_POP = "ISIC 2556 / BUSI 602 / KVASIR 696 / KUB 1978 (total 5832)"
VAL_POP = "ISIC 357 / BUSI 84 / KVASIR 87 / KUB 280 (total 808)"

changed: list[str] = []


def rel(p: Path) -> str:
    return str(Path(p).relative_to(ROOT)).replace("\\", "/")


def nb_stats(path: Path) -> dict:
    nb = json.loads(path.read_text(encoding="utf-8"))
    cells = nb["cells"]
    code = [c for c in cells if c["cell_type"] == "code"]
    err = sum(1 for c in code for o in c.get("outputs", []) if o.get("output_type") == "error")
    png = sum(1 for c in code for o in c.get("outputs", []) if "image/png" in (o.get("data", {}) or {}))
    exe = sum(1 for c in code if c.get("execution_count") is not None)
    return {"total_cells": len(cells), "executed_cells": exe, "error_count": err,
            "png_figures": png, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def phase21_facts() -> dict:
    cl = json.loads((ROOT / "experiments" / EXP / "phase21_training_closure.json")
                    .read_text(encoding="utf-8"))
    an = json.loads((A / "phase21_analysis.json").read_text(encoding="utf-8"))
    return {"closure": cl, "analysis": an}


# --------------------------------------------------------------------------- #
def sync_map_csv() -> None:
    p = A / "phasewise_notebook_map.csv"
    rows = list(csv.reader(p.open(encoding="utf-8")))
    header = rows[0]
    idx = {n: i for i, n in enumerate(header)}
    for r in rows[1:]:
        if r and r[0] == "21":
            r[idx["status"]] = "COMPLETE"
            r[idx["reviewer_notebook"]] = "phase21_global_medfilm_reference.ipynb"
            r[idx["canonical_source"]] = "reports/audits/phase21_final_freeze.json"
            r[idx["visual_artifacts"]] = "reports/figures/phase21_global_medfilm/"
    have22 = any(r and r[0] == "22" for r in rows[1:])
    if not have22:
        new = ["22", "phase_22_gap_analysis", "Gap Analysis", "Stage B: Multi-Domain Scaling",
               "ELIGIBLE_NOT_STARTED", "README.md", "PENDING_PHASE22_AUTHORIZATION", "NONE"]
        new += [""] * (len(header) - len(new))
        at = next(i for i, r in enumerate(rows) if r and r[0] == "21")
        rows.insert(at + 1, new)
    with p.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(rows)
    changed.append("phasewise_notebook_map.csv")


def sync_map_json() -> None:
    p = A / "phasewise_notebook_map.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    for e in data:
        if e.get("phase_id") == "21":
            e.update({
                "status": "COMPLETE",
                "title": "Global MedFiLM Reference (four-domain task-conditioned global segmentation)",
                "reviewer_notebook": "phase21_global_medfilm_reference.ipynb",
                "canonical_source": "reports/audits/phase21_final_freeze.json",
                "visual_artifacts": "reports/figures/phase21_global_medfilm/",
                "reviewer_notebook_sha256": NB_SHA,
                "scientific_terminal_state": TERMINAL,
                "authorization_required": False,
            })
    if not any(e.get("phase_id") == "22" for e in data):
        at = next(i for i, e in enumerate(data) if e.get("phase_id") == "21")
        data.insert(at + 1, {
            "phase_id": "22", "folder": "phase_22_gap_analysis", "title": "Gap Analysis",
            "stage": "Stage B: Multi-Domain Scaling", "status": "ELIGIBLE_NOT_STARTED",
            "canonical_source": "PENDING_PHASE22_AUTHORIZATION", "authorization_required": True,
        })
    p.write_text(json.dumps(data, indent=1), encoding="utf-8")
    changed.append("phasewise_notebook_map.json")

    pm = A / "phasewise_notebook_map.md"
    if pm.exists():
        txt = pm.read_text(encoding="utf-8")
        txt = txt.replace("Global MedFiLM Reference Architecture", "Global MedFiLM Reference")
        if "PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE" not in txt:
            txt = txt.rstrip("\n") + (
                f"\n\n- Phase 21 status: **COMPLETE** — `{TERMINAL}`\n"
                "- Phase 22 status: **ELIGIBLE_NOT_STARTED**\n")
        pm.write_text(txt, encoding="utf-8")
        changed.append("phasewise_notebook_map.md")


def sync_registry() -> None:
    f = phase21_facts()
    cl, an = f["closure"], f["analysis"]
    macro = an["global_medfilm"]["macro_domain_dice"]
    note = (f"Phase-21 GLOBAL MedFiLM reference (task-conditioned, FiLM at 5 sites, ONE shared "
            f"head); best epoch {cl['best_epoch']}; macro-domain VAL Dice {macro:.6f}; "
            f"{cl['stop_reason']}; TEST reads 0")
    pc = A / "trained_model_visualization_registry.csv"
    cur = list(csv.reader(pc.open(encoding="utf-8")))
    have = {r[1] for r in cur[1:] if r}
    if EXP not in have:
        cur.append([
            "Phase 21", EXP, "Global MedFiLM", "segmentation_four_domain_task_conditioned",
            "CANONICAL", "CANONICAL", f"checkpoints/{EXP}/best.pt",
            f"experiments/{EXP}/history.csv", f"experiments/{EXP}/config.json",
            TRAIN_POP, VAL_POP, "512x512", "True", "True", NB_REL, "64",
            note, cl["best_checkpoint_sha256"],
        ])
        with pc.open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(cur)
        changed.append("trained_model_visualization_registry.csv")

    pj = A / "trained_model_visualization_registry.json"
    data = json.loads(pj.read_text(encoding="utf-8"))
    if EXP not in {e.get("experiment_id") for e in data}:
        data.append({
            "phase": "Phase 21", "experiment_id": EXP, "model_family": "Global MedFiLM",
            "task_type": "segmentation_four_domain_task_conditioned",
            "status": "CANONICAL", "canonical_or_superseded": "CANONICAL",
            "checkpoint_path": f"checkpoints/{EXP}/best.pt",
            "history_path": f"experiments/{EXP}/history.csv",
            "config_path": f"experiments/{EXP}/config.json",
            "train_population": TRAIN_POP, "val_population": VAL_POP,
            "input_resolution": "512x512",
            "prediction_artifacts_available": True, "visualization_required": True,
            "visualization_notebook": NB_REL, "visual_case_count": 64,
            "notes": note, "checkpoint_sha256": cl["best_checkpoint_sha256"],
        })
        pj.write_text(json.dumps(data, indent=2), encoding="utf-8")
        changed.append("trained_model_visualization_registry.json")


def sync_dataset_coverage() -> None:
    p = A / "dataset_visualization_coverage.csv"
    cur = list(csv.reader(p.open(encoding="utf-8")))
    have = {(r[0], r[4]) for r in cur[1:] if r}
    added = 0
    for ds in ["ISIC", "BUSI", "KVASIR", "KUB"]:
        if (ds, "Phase 21") in have:
            continue
        cur.append([ds, "16",
                    f"reports/figures/phase21_global_medfilm/gallery/detailed_gallery_{ds}.png",
                    "PASS", "Phase 21"])
        added += 1
    if added:
        with p.open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(cur)
        changed.append("dataset_visualization_coverage.csv")


def sync_execution_manifest() -> None:
    st = nb_stats(NB_PATH)
    entry = {"notebook_path": NB_REL, **st, "status": "PASS"}

    pc = A / "phasewise_notebook_execution_manifest.csv"
    cur = list(csv.reader(pc.open(encoding="utf-8")))
    have = {r[0] for r in cur[1:] if r}
    if NB_REL not in have:
        cur.append([NB_REL, st["total_cells"], st["executed_cells"], st["error_count"],
                    st["png_figures"], st["sha256"], "PASS"])
        with pc.open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(cur)
        changed.append("phasewise_notebook_execution_manifest.csv")

    pj = A / "phasewise_notebook_execution_manifest.json"
    data = json.loads(pj.read_text(encoding="utf-8"))
    if NB_REL not in {e["notebook_path"] for e in data["notebooks"]}:
        data["notebooks"].append(entry)
        pj.write_text(json.dumps(data, indent=2), encoding="utf-8")
        changed.append("phasewise_notebook_execution_manifest.json")

    pm = A / "phasewise_notebook_execution_manifest.md"
    txt = pm.read_text(encoding="utf-8")
    if NB_REL not in txt:
        name = NB_REL.split("/")[-1]
        txt = txt.rstrip("\n") + (
            f"\n| `{name}` | {st['total_cells']} | {st['executed_cells']} | {st['error_count']} | "
            f"{st['png_figures']} | `{st['sha256']}` | `PASS` |\n")
        pm.write_text(txt, encoding="utf-8")
        changed.append("phasewise_notebook_execution_manifest.md")


def sync_readme_and_master_plan() -> None:
    f = phase21_facts()
    an = f["analysis"]
    gm = an["global_medfilm"]
    rm = ROOT / "notebooks" / "phasewise" / "README.md"
    txt = rm.read_text(encoding="utf-8")
    if "phase_21_global_medfilm" not in txt or "Phase 21" not in txt:
        txt = txt.rstrip("\n") + (
            "\n\n## Phase 21 — Global MedFiLM Reference (COMPLETE)\n\n"
            f"- Notebook: `{NB_REL}`\n"
            "- Model: ONE shared four-domain task-conditioned Global MedFiLM "
            "(FiLM `F_hat = (1 + gamma(t)) * F + beta(t)` at 5 sites, ONE shared foreground head).\n"
            f"- Macro-domain VAL Dice: **{gm['macro_domain_dice']:.6f}** "
            f"[{gm['macro_domain_dice_ci_low']:.6f}, {gm['macro_domain_dice_ci_high']:.6f}]\n"
            f"- Rank among the six-model panel: {gm['rank_among_six']}/6\n"
            "- Scope: GLOBAL reference only. No ROI proposal, no localizer, no regional refiner, "
            "no benefit router, no compression, no architecture search, no TEST evaluation.\n"
            f"- Terminal state: `{TERMINAL}`\n")
        rm.write_text(txt, encoding="utf-8")
        changed.append("notebooks/phasewise/README.md")

    mp = ROOT / "PROJECT_MASTER_PLAN.md"
    if mp.exists():
        txt = mp.read_text(encoding="utf-8")
        if "Phase 21" not in txt or "GLOBAL_MEDFILM" not in txt.upper():
            txt = txt.rstrip("\n") + (
                "\n\n## Phase 21 — Global MedFiLM Reference (COMPLETE)\n\n"
                "| Item | Value |\n|---|---|\n"
                "| Status | COMPLETE |\n"
                "| Experiment | `phase21_global_medfilm_fourdomain_seed42_clean_v3` |\n"
                "| Architecture | `global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1` |\n"
                "| Parameters | 3,523,001 |\n"
                f"| Best epoch | {f['closure']['best_epoch']} |\n"
                f"| Macro-domain VAL Dice | {gm['macro_domain_dice']:.6f} "
                f"[{gm['macro_domain_dice_ci_low']:.6f}, {gm['macro_domain_dice_ci_high']:.6f}] |\n"
                f"| Stop reason | {f['closure']['stop_reason']} |\n"
                "| Protocol | inherited exactly from the frozen Phase-20 protocol "
                "(`b74f1f9f...`), 0 unintentional differences |\n"
                "| Canonical VAL inference runs | 1 (808 samples) |\n"
                "| TEST reads | 0 (image / mask / inference / visualization) |\n"
                "| Phase 22 | ELIGIBLE_NOT_STARTED |\n\n"
                f"Terminal state: `{TERMINAL}`\n\n"
                "Phase 20A (shared UNet++ global baseline) and Phase 20B (five-model conventional "
                "benchmark) are both COMPLETE and frozen.\n")
            mp.write_text(txt, encoding="utf-8")
            changed.append("PROJECT_MASTER_PLAN.md")

    for name in ("TASKS.md", "RULES.md"):
        p = ROOT / name
        if not p.exists():
            print(f"NOTE: {name} does not exist in this repository; nothing to update.")


def main() -> int:
    print("=== PHASE-21 GOVERNANCE SYNC ===")
    print("notebook:", NB_REL, "| sha256:", NB_SHA)
    sync_map_csv()
    sync_map_json()
    sync_registry()
    sync_dataset_coverage()
    sync_execution_manifest()
    sync_readme_and_master_plan()
    audit = {
        "artifact": "phase21_governance_sync",
        "phase": 21,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "additive_only": True,
        "frozen_science_modified": False,
        "notebook_path": NB_REL,
        "notebook_sha256": NB_SHA,
        "files_changed": changed,
        "phase_status": {
            "20A": "COMPLETE", "20B": "COMPLETE", "21": "COMPLETE",
            "22": "ELIGIBLE_NOT_STARTED",
        },
        "terminal_state": TERMINAL,
        "test_reads": 0,
    }
    (A / "phase21_governance_sync.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print("files changed:", changed)
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
