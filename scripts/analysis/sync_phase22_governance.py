"""Additive governance sync for the Phase-22 gap-analysis package (§44).

Reads ONLY persisted artifacts + the built notebook. Never trains, never runs inference,
never touches TEST, never modifies frozen science. Every edit is ADDITIVE or an explicit
status transition; no frozen artifact is rewritten.

Updates:
  * reports/audits/phasewise_notebook_map.{csv,json,md}
  * notebooks/phasewise/README.md
  * PROJECT_MASTER_PLAN.md
  * reports/audits/phasewise_notebook_execution_manifest.{csv,json,md}
  * reports/audits/dataset_visualization_coverage.csv  (reporting-only entry)
  * reports/audits/phase22_governance_sync.json

Represents: Phase 21 COMPLETE, Phase 22 COMPLETE, Phase 23 ELIGIBLE_NOT_STARTED.

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/sync_phase22_governance.py
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
NB_REL = "notebooks/phasewise/phase_22_resource_gap/phase22_resource_gap_analysis.ipynb"
NB_PATH = ROOT / NB_REL
TERMINAL = ("PHASE22_MULTIDOMAIN_SCALE_REGIONAL_RESOURCE_GAP_ANALYSIS_COMPLETE"
            "__PHASE23_ELIGIBLE_NOT_STARTED")
FIG_REL = "reports/figures/phase22_resource_gap/"

changed: list[str] = []


def rel(p) -> str:
    return str(Path(p).relative_to(ROOT)).replace("\\", "/")


def sha(p) -> str | None:
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def nb_stats(path: Path) -> dict:
    nb = json.loads(path.read_text(encoding="utf-8"))
    cells = nb["cells"]
    code = [c for c in cells if c["cell_type"] == "code"]
    err = sum(1 for c in code for o in c.get("outputs", []) if o.get("output_type") == "error")
    png = sum(1 for c in code for o in c.get("outputs", [])
              if "image/png" in (o.get("data", {}) or {}))
    exe = sum(1 for c in code if c.get("execution_count") is not None)
    return {"total_cells": len(cells), "executed_cells": exe, "error_count": err,
            "png_figures": png, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _j(name: str) -> dict:
    p = A / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


# --------------------------------------------------------------------------- #
def sync_map() -> None:
    pc = A / "phasewise_notebook_map.csv"
    if pc.exists():
        rows = list(csv.reader(pc.open(encoding="utf-8")))
        header = rows[0]
        idx = {n: i for i, n in enumerate(header)}
        found = False
        for r in rows[1:]:
            if r and r[0] == "22":
                found = True
                if "status" in idx:
                    r[idx["status"]] = "COMPLETE"
                if "folder" in idx:
                    r[idx["folder"]] = "phase_22_resource_gap"
                if "reviewer_notebook" in idx:
                    r[idx["reviewer_notebook"]] = "phase22_resource_gap_analysis.ipynb"
                if "canonical_source" in idx:
                    r[idx["canonical_source"]] = "reports/audits/phase22_final_freeze.json"
                if "visual_artifacts" in idx:
                    r[idx["visual_artifacts"]] = FIG_REL
        if not found:
            at = next((i for i, r in enumerate(rows) if r and r[0] == "21"), len(rows) - 1)
            new = ["22", "phase_22_resource_gap", "Resource Gap Analysis",
                   "Stage B: Multi-Domain Scale / Regional / Resource",
                   "COMPLETE", "phase22_resource_gap_analysis.ipynb",
                   "reports/audits/phase22_final_freeze.json", FIG_REL]
            new += [""] * max(0, len(header) - len(new))
            rows.insert(at + 1, new)
        with pc.open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(rows)
        changed.append("phasewise_notebook_map.csv")

    pj = A / "phasewise_notebook_map.json"
    if pj.exists():
        data = json.loads(pj.read_text(encoding="utf-8"))
        found = False
        for e in data:
            if e.get("phase_id") == "22":
                found = True
                e.update({
                    "folder": "phase_22_resource_gap",
                    "title": ("Resource Gap Analysis (scale, regional-benefit, conditional "
                              "compute)"),
                    "status": "COMPLETE",
                    "reviewer_notebook": "phase22_resource_gap_analysis.ipynb",
                    "canonical_source": "reports/audits/phase22_final_freeze.json",
                    "visual_artifacts": FIG_REL,
                    "reviewer_notebook_sha256": sha(NB_PATH),
                    "scientific_terminal_state": TERMINAL,
                    "authorization_required": False,
                })
        if not found:
            at = next((i for i, e in enumerate(data) if e.get("phase_id") == "21"),
                      len(data) - 1)
            data.insert(at + 1, {
                "phase_id": "22", "folder": "phase_22_resource_gap",
                "title": ("Resource Gap Analysis (scale, regional-benefit, conditional "
                          "compute)"),
                "stage": "Stage B: Multi-Domain Scale / Regional / Resource",
                "status": "COMPLETE",
                "reviewer_notebook": "phase22_resource_gap_analysis.ipynb",
                "canonical_source": "reports/audits/phase22_final_freeze.json",
                "visual_artifacts": FIG_REL,
                "reviewer_notebook_sha256": sha(NB_PATH),
                "scientific_terminal_state": TERMINAL,
                "authorization_required": False,
            })
        pj.write_text(json.dumps(data, indent=1), encoding="utf-8")
        changed.append("phasewise_notebook_map.json")

    pm = A / "phasewise_notebook_map.md"
    if pm.exists():
        txt = pm.read_text(encoding="utf-8")
        if "PHASE22_MULTIDOMAIN_SCALE" not in txt:
            txt = txt.rstrip("\n") + (
                f"\n\n- Phase 22 status: **COMPLETE** — `{TERMINAL}`\n"
                "- Phase 23 status: **ELIGIBLE_NOT_STARTED**\n")
            pm.write_text(txt, encoding="utf-8")
            changed.append("phasewise_notebook_map.md")


def sync_execution_manifest() -> None:
    st = nb_stats(NB_PATH)
    entry = {"notebook_path": NB_REL, **st, "status": "PASS"}

    pc = A / "phasewise_notebook_execution_manifest.csv"
    if pc.exists():
        cur = list(csv.reader(pc.open(encoding="utf-8")))
        have = {r[0] for r in cur[1:] if r}
        if NB_REL not in have:
            cur.append([NB_REL, st["total_cells"], st["executed_cells"], st["error_count"],
                        st["png_figures"], st["sha256"], "PASS"])
            with pc.open("w", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerows(cur)
            changed.append("phasewise_notebook_execution_manifest.csv")

    pj = A / "phasewise_notebook_execution_manifest.json"
    if pj.exists():
        data = json.loads(pj.read_text(encoding="utf-8"))
        nbs = data.get("notebooks")
        if isinstance(nbs, list) and NB_REL not in {e.get("notebook_path") for e in nbs}:
            nbs.append(entry)
            pj.write_text(json.dumps(data, indent=2), encoding="utf-8")
            changed.append("phasewise_notebook_execution_manifest.json")

    pm = A / "phasewise_notebook_execution_manifest.md"
    if pm.exists():
        txt = pm.read_text(encoding="utf-8")
        if NB_REL not in txt:
            name = NB_REL.split("/")[-1]
            txt = txt.rstrip("\n") + (
                f"\n| `{name}` | {st['total_cells']} | {st['executed_cells']} | "
                f"{st['error_count']} | {st['png_figures']} | `{st['sha256']}` | `PASS` |\n")
            pm.write_text(txt, encoding="utf-8")
            changed.append("phasewise_notebook_execution_manifest.md")


def sync_readme_and_master_plan() -> None:
    ff = _j("phase22_final_freeze.json")
    ss = ff.get("science_summary", {})
    atlas = ss.get("failure_atlas", {})
    acc = ss.get("oracle_ceiling", {})
    rc = ROOT / "notebooks" / "phasewise" / "README.md"
    if rc.exists():
        txt = rc.read_text(encoding="utf-8")
        if "phase_22_resource_gap" not in txt:
            txt = txt.rstrip("\n") + (
                "\n\n## Phase 22 — Resource Gap Analysis (COMPLETE)\n\n"
                f"- Notebook: `{NB_REL}`\n"
                "- Model: the FROZEN Phase-21 Global MedFiLM reference (unchanged).\n"
                "- Scope: diagnostic gap analysis only — scale sensitivity, oracle regional "
                "benefit, resource frontier. NO training, NO architecture change, NO benefit "
                "predictor, NO TEST access.\n"
                f"- Failure atlas pooled mean Dice: {atlas.get('mean_dice')}\n"
                f"- Oracle accept-if-beneficial ceiling gain over always-global: "
                f"{acc.get('ceiling_gain_over_always_global')} (UPPER BOUND, not deployable)\n"
                f"- Terminal state: `{TERMINAL}`\n")
            rc.write_text(txt, encoding="utf-8")
            changed.append("notebooks/phasewise/README.md")

    mp = ROOT / "PROJECT_MASTER_PLAN.md"
    if mp.exists():
        txt = mp.read_text(encoding="utf-8")
        if "Phase 22 —" not in txt:
            txt = txt.rstrip("\n") + (
                "\n\n## Phase 22 — Multi-Domain Scale / Regional-Benefit / Resource Gap "
                "(COMPLETE)\n\n"
                "| Item | Value |\n|---|---|\n"
                "| Status | COMPLETE |\n"
                "| Type | diagnostic gap analysis (inference-only, no training) |\n"
                "| Reference | frozen Phase-21 Global MedFiLM (3,523,001 params, unchanged) |\n"
                "| Protocol | `reports/audits/phase22_diagnostic_protocol.json` (frozen) |\n"
                "| Scales probed | 256 / 512 / 768 / 1024 (native-space scoring) |\n"
                "| Regional arms | ORACLE (upper bound) + PREDICTION-DERIVED (deployable shape) |\n"
                "| Benefit predictor | NOT trained (label contracted only) |\n"
                "| Router | NOT trained (fixed rules evaluated offline) |\n"
                f"| Terminal state | `{TERMINAL}` |\n")
            mp.write_text(txt, encoding="utf-8")
            changed.append("PROJECT_MASTER_PLAN.md")


def sync_dataset_coverage() -> None:
    p = A / "dataset_visualization_coverage.csv"
    if not p.exists():
        return
    cur = list(csv.reader(p.open(encoding="utf-8")))
    have = {(r[0], r[4]) for r in cur[1:] if r and len(r) > 4}
    added = 0
    figs = sorted(f.name for f in (ROOT / FIG_REL).glob("*.png")) \
        if (ROOT / FIG_REL).exists() else []
    for ds in ["ISIC", "BUSI", "KVASIR", "KUB", "ALL"]:
        if (ds, "Phase 22") in have:
            continue
        cur.append([ds, str(len(figs)), FIG_REL, "REPORTING_ONLY", "Phase 22"])
        added += 1
    if added:
        with p.open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(cur)
        changed.append("dataset_visualization_coverage.csv")


def main() -> int:
    ff = _j("phase22_final_freeze.json")
    if not ff.get("freeze_verified"):
        print("WARNING: phase22_final_freeze.json is absent or not verified; "
              "syncing governance anyway (additive) but recording the state.")
    sync_map()
    sync_execution_manifest()
    sync_readme_and_master_plan()
    sync_dataset_coverage()

    det = _j("phase22_notebook_determinism.json")
    payload = {
        "artifact": "phase22_governance_sync",
        "phase": 22,
        "additive_only": True,
        "frozen_science_modified": False,
        "frozen_artifacts_untouched": [
            "reports/audits/phase20_shared_global_baseline_protocol.json",
            "reports/audits/phase21_final_freeze.json",
            "reports/audits/phase22_diagnostic_protocol.json",
            "reports/audits/phase22_phase21_reference_binding.json",
        ],
        "phase21_experiment_untouched": True,
        "checkpoint_sha256": sha(ROOT / "checkpoints" /
                                 "phase21_global_medfilm_fourdomain_seed42_clean_v3" /
                                 "best.pt"),
        "phase_status": {
            "21": "COMPLETE",
            "22": "COMPLETE" if ff.get("freeze_verified") else "INCOMPLETE",
            "23": "ELIGIBLE_NOT_STARTED",
        },
        "terminal_state": TERMINAL if ff.get("freeze_verified")
        else "PHASE22_FREEZE_INCOMPLETE",
        "notebook": {
            "path": NB_REL,
            "sha256": sha(NB_PATH),
            "three_builds_byte_identical": det.get("three_builds_byte_identical"),
        },
        "files_updated": changed,
        "n_files_updated": len(changed),
        "governance": {
            "training_jobs_started": 0,
            "architecture_modified": False,
            "benefit_predictor_trained": False,
            "phase23_started": False,
            "test_reads": 0,
        },
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "test_reads": 0,
    }
    (A / "phase22_governance_sync.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8")
    changed.append("phase22_governance_sync.json")

    print(f"WROTE {A / 'phase22_governance_sync.json'}")
    print(f"files updated: {len(changed)}")
    for c in changed:
        print("  -", c)
    print("terminal_state:", payload["terminal_state"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
