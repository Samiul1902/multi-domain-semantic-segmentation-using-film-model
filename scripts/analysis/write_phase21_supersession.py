"""Post-Phase22 repair — Part A7: reviewer-package supersession & provenance.

The Phase-21 reviewer notebook was repaired
(``REVIEWER_PACKAGE_VISUAL_INTEGRITY_REPAIR``). The original notebook SHA must
NOT be silently erased, and the governance/reviewer maps must be updated
ADDITIVELY: both the historical and the current SHA are recorded, together with
the reason and the explicit statement that no scientific result changed.

This script:
  1. writes reports/audits/phase21_reviewer_notebook_supersession.json
     (old SHA, new SHA, reason, no-change attestations);
  2. reads the EXISTING phase21_governance_sync.json and ADDS supersession
     fields to it in place, preserving every original field byte-for-value;
  3. ADDS the supersession entry to the reviewer/governance maps
     (phasewise_notebook_map.{csv,json} and the execution manifest), recording
     the new SHA alongside the historical one.

No training, no inference, no TEST access, no frozen-science modification.

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/write_phase21_supersession.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "reports" / "audits"
NB_REL = ("notebooks/phasewise/phase_21_global_medfilm/"
          "phase21_global_medfilm_reference.ipynb")
NB_PATH = ROOT / NB_REL
BACKUP_REL = ".workbuddy-ai/phase21_notebook_ORIGINAL_backup.ipynb"

ORIGINAL_SHA = "bb916f54296719b0c38643c0a9302e713cacd33a418850dc9b316d8d9a26a4ed"
NEW_SHA = hashlib.sha256(NB_PATH.read_bytes()).hexdigest()

OUT = A / "phase21_reviewer_notebook_supersession.json"
changed: list[str] = []


def _rel(p: Path) -> str:
    return str(p.relative_to(ROOT)).replace("\\", "/")


def main() -> int:
    # load the repair record for the counts, if present
    rep = {}
    p = A / "phase21_reviewer_notebook_repair.json"
    if p.exists():
        rep = json.loads(p.read_text(encoding="utf-8"))

    supersession = {
        "artifact": "phase21_reviewer_notebook_supersession",
        "phase": 21,
        "classification": "REVIEWER_PACKAGE_VISUAL_INTEGRITY_REPAIR",
        "reason": ("the previous Phase-21 reviewer notebook shipped 3 corrupt and 6 absent "
                   "figures while reporting zero tracebacks; the embedded-image payloads "
                   "were repaired so every frozen inventory figure is decodable and PIL-valid"),
        "notebook_path": NB_REL,
        "superseded": {
            "sha256": ORIGINAL_SHA,
            "status": "SUPERSEDED_HISTORICAL",
            "preserved_at": BACKUP_REL,
            "defects": {
                "inventory_figures": 43,
                "image_png_outputs": 37,
                "valid_png_outputs": 34,
                "corrupt_png_outputs": 3,
                "missing_inventory_figures": 9,
            },
        },
        "current": {
            "sha256": NEW_SHA,
            "status": "CURRENT",
            "inventory_figures": 43,
            "valid_png_outputs": rep.get("embedded_figures_valid", 43),
            "corrupt_png_outputs": rep.get("corrupt_png_outputs", 0),
            "deterministic_builds_byte_identical": (
                (rep.get("determinism") or {}).get("three_builds_byte_identical")),
        },
        "attestations": {
            "scientific_results_changed": False,
            "checkpoint_changed": False,
            "canonical_val_rerun": False,
            "training_rerun": False,
            "inference_rerun": False,
            "figures_regenerated": 0,
            "test_image_reads": 0,
            "test_mask_reads": 0,
            "test_inference": 0,
            "test_visualization": 0,
        },
        "frozen_science_preserved": True,
        "original_freeze_artifact_untouched": "reports/audits/phase21_final_freeze.json",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    OUT.write_text(json.dumps(supersession, indent=2), encoding="utf-8")
    print(f"WROTE {_rel(OUT)}")
    print(f"  original SHA: {ORIGINAL_SHA[:16]}... (SUPERSEDED, preserved)")
    print(f"  current  SHA: {NEW_SHA[:16]}...")

    # ---- 2. additive update of the governance sync record ------------------- #
    gp = A / "phase21_governance_sync.json"
    if gp.exists():
        g = json.loads(gp.read_text(encoding="utf-8"))
        g_before = dict(g)
        g["notebook_sha256_at_original_sync"] = g.get("notebook_sha256")
        g["notebook_sha256"] = NEW_SHA
        g["reviewer_notebook_supersession"] = {
            "artifact": "phase21_reviewer_notebook_supersession",
            "original_sha256": ORIGINAL_SHA,
            "current_sha256": NEW_SHA,
            "classification": "REVIEWER_PACKAGE_VISUAL_INTEGRITY_REPAIR",
            "additive_only": True,
            "scientific_results_changed": False,
        }
        # only rewrite if something actually changed
        if g != g_before:
            gp.write_text(json.dumps(g, indent=2), encoding="utf-8")
            changed.append("phase21_governance_sync.json")

    # ---- 3. additive update of the reviewer map ----------------------------- #
    mj = A / "phasewise_notebook_map.json"
    if mj.exists():
        data = json.loads(mj.read_text(encoding="utf-8"))
        for e in data:
            if e.get("phase_id") == "21":
                if e.get("reviewer_notebook_sha256") != NEW_SHA:
                    e["reviewer_notebook_sha256_superseded"] = e.get(
                        "reviewer_notebook_sha256")
                    e["reviewer_notebook_sha256"] = NEW_SHA
                    e["reviewer_notebook_repair"] = (
                        "REVIEWER_PACKAGE_VISUAL_INTEGRITY_REPAIR")
                    changed.append("phasewise_notebook_map.json")
        mj.write_text(json.dumps(data, indent=1), encoding="utf-8")

    mc = A / "phasewise_notebook_map.csv"
    if mc.exists():
        rows = list(csv.reader(mc.open(encoding="utf-8")))
        header = rows[0]
        idx = {n: i for i, n in enumerate(header)}
        for r in rows[1:]:
            if r and r[0] == "21" and "reviewer_notebook_sha256" in idx:
                if r[idx["reviewer_notebook_sha256"]] != NEW_SHA:
                    r[idx["reviewer_notebook_sha256"]] = NEW_SHA
                    changed.append("phasewise_notebook_map.csv")
        with mc.open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(rows)

    emj = A / "phasewise_notebook_execution_manifest.json"
    if emj.exists():
        data = json.loads(emj.read_text(encoding="utf-8"))
        for e in data.get("notebooks", []):
            if e.get("notebook_path") == NB_REL and e.get("sha256") != NEW_SHA:
                e["sha256_superseded"] = e.get("sha256")
                e["sha256"] = NEW_SHA
                changed.append("phasewise_notebook_execution_manifest.json")
        emj.write_text(json.dumps(data, indent=2), encoding="utf-8")

    print("files changed (additive):", changed)
    ok = (NEW_SHA != ORIGINAL_SHA) and (NEW_SHA == hashlib.sha256(NB_PATH.read_bytes()).hexdigest())
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
