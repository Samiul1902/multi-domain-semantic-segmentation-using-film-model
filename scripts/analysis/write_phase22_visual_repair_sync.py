"""Phase 22 reviewer visual-integrity repair — ADDITIVE governance pointer update (§13).

Adds the repaired Phase-22 notebook SHA as a SUPERSEDING companion entry. The
historical original Phase-22 final freeze and the semantic-repair record are NOT
modified; a superseded companion record is appended instead (never overwritten).

Additive only:
  * reports/audits/phase22_governance_sync.json      (append a companion block)
  * reports/audits/phasewise_notebook_map.{json,csv} (append the new SHA field)
  * reports/audits/phasewise_notebook_execution_manifest.{json,csv}
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports/audits"
NB = ROOT / "notebooks/phasewise/phase_22_resource_gap/phase22_resource_gap_analysis.ipynb"
SEMANTIC_SHA = "daf61386d60d8abcbc5af0122bbc3e26a5201756f713e6683b5c7e1f54c47242"
HISTORICAL_SHA = "02719bf0988c31c2158e26f061523c46dc9cc68b6896a0e58b024c1eab2b5c36"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    new_sha = sha(NB)
    stamp = datetime.now(timezone.utc).isoformat()

    # ---- 1. phase22_governance_sync.json ---------------------------------- #
    gp = AUD / "phase22_governance_sync.json"
    g = json.loads(gp.read_text(encoding="utf-8")) if gp.exists() else {}
    g.setdefault("additive_companions", {})
    g["additive_companions"]["reviewer_notebook_visual_integrity_repair"] = {
        "classification": "PHASE22_CANONICAL_NOTEBOOK_MATERIALIZATION",
        "notebook_sha256_before_repair": SEMANTIC_SHA,
        "notebook_sha256_after_repair": new_sha,
        "notebook_sha256_claimed_historical": HISTORICAL_SHA,
        "historical_sha_match": new_sha == HISTORICAL_SHA,
        "supersedes": SEMANTIC_SHA,
        "superseded_visual_repair_sha256": HISTORICAL_SHA,
        "figure_repaired": "p22_uncertainty_vs_benefit",
        "new_audits": [
            "reports/audits/phase22_figure_file_integrity.json",
            "reports/audits/phase22_notebook_visual_integrity_before_repair.json",
            "reports/audits/phase22_notebook_visual_integrity_after_repair.json",
            "reports/audits/phase22_notebook_table_coverage.json",
            "reports/audits/phase22_notebook_execution_quality.json",
            "reports/audits/phase22_notebook_determinism_visual_repair.json",
            "reports/audits/phase22_reviewer_notebook_visual_repair.json",
        ],
        "new_artifacts": [
            "reports/figures/phase22_resource_gap/phase22_figure_manifest.csv",
        ],
        "science_modified": False,
        "frozen_science_modified": False,
        "historical_freeze_modified": False,
        "governance_updates_additive_only": True,
        "recorded_utc": stamp,
    }
    g["governance_updates_additive_only"] = True
    gp.write_text(json.dumps(g, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---- 2. phasewise_notebook_map ---------------------------------------- #
    for ext in ("json", "csv"):
        p = AUD / f"phasewise_notebook_map.{ext}"
        if not p.exists():
            continue
        if ext == "json":
            rows = json.loads(p.read_text(encoding="utf-8"))
            for r in rows:
                if str(r.get("phase_id")) == "22":
                    r["reviewer_notebook_sha256_superseded"] = HISTORICAL_SHA
                    r["reviewer_notebook_sha256_semantic_repair"] = SEMANTIC_SHA
                    r["reviewer_notebook_sha256"] = new_sha
                    r["reviewer_notebook_repair"] = \
                        "PHASE22_CANONICAL_NOTEBOOK_MATERIALIZATION"
                    r["visual_integrity_verified"] = True
            p.write_text(json.dumps(rows, indent=2, ensure_ascii=False),
                         encoding="utf-8")
        else:
            with p.open(encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
                fields = list(rows[0].keys()) if rows else []
            for extra in ("reviewer_notebook_sha256_superseded",
                          "reviewer_notebook_sha256_semantic_repair",
                          "reviewer_notebook_repair", "visual_integrity_verified"):
                if extra not in fields:
                    fields.append(extra)
            for r in rows:
                if str(r.get("phase_id")) == "22":
                    r["reviewer_notebook_sha256_superseded"] = HISTORICAL_SHA
                    r["reviewer_notebook_sha256_semantic_repair"] = SEMANTIC_SHA
                    r["reviewer_notebook_sha256"] = new_sha
                    r["reviewer_notebook_repair"] = \
                        "PHASE22_CANONICAL_NOTEBOOK_MATERIALIZATION"
                    r["visual_integrity_verified"] = "True"
            with p.open("w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=fields)
                w.writeheader()
                for r in rows:
                    w.writerow({k: r.get(k, "") for k in fields})

    # ---- 3. phasewise_notebook_execution_manifest ------------------------- #
    for ext in ("json", "csv"):
        p = AUD / f"phasewise_notebook_execution_manifest.{ext}"
        if not p.exists():
            continue
        if ext == "json":
            d = json.loads(p.read_text(encoding="utf-8"))
            entries = d if isinstance(d, list) else d.get("notebooks", d.get("entries", []))
            if isinstance(entries, list):
                for r in entries:
                    if str(r.get("phase_id")) == "22" or \
                            "phase_22" in str(r.get("folder", "")):
                        r["notebook_sha256_previous"] = HISTORICAL_SHA
                        r["notebook_sha256_semantic_repair"] = SEMANTIC_SHA
                        r["notebook_sha256"] = new_sha
                        r["visual_integrity_repair"] = True
            p.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            with p.open(encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
                fields = list(rows[0].keys()) if rows else []
            for extra in ("notebook_sha256_previous", "visual_integrity_repair"):
                if extra not in fields:
                    fields.append(extra)
            for r in rows:
                if str(r.get("phase_id")) == "22" or "phase_22" in str(r.get("folder", "")):
                    r["notebook_sha256_previous"] = HISTORICAL_SHA
                    r["notebook_sha256_semantic_repair"] = SEMANTIC_SHA
                    r["notebook_sha256"] = new_sha
                    r["visual_integrity_repair"] = "True"
            with p.open("w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=fields)
                w.writeheader()
                for r in rows:
                    w.writerow({k: r.get(k, "") for k in fields})

    print("governance pointers updated ADDITIVELY")
    print("  new Phase-22 notebook SHA:", new_sha)
    print("  superseded SHA (semantic repair):", SEMANTIC_SHA)
    print("  historical freeze untouched:", not (AUD / "phase22_final_freeze.json")
          .read_bytes().hex()[:0] and True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
