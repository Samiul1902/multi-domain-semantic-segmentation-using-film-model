"""Ensure the exact required table filenames exist with correct content,
and build the Evidence/ index."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"
TABLES = OUT / "tables"
EVID = OUT / "Evidence"


def read(p: Path) -> list[dict]:
    with p.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write(p: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    fields = fields or list(rows[0].keys())
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows({k: r.get(k, "") for k in fields} for r in rows)
    print(f"  {p.name}: {len(rows)} rows, {len(fields)} cols")


def main() -> None:
    print("REQUIRED TABLES")

    # 1. registry — same content as TRAINING_RUN_REGISTRY.csv under the required name
    reg = read(TABLES / "TRAINING_RUN_REGISTRY.csv")
    write(TABLES / "REMEDFILM_TRAINING_RUN_REGISTRY.csv", reg)

    # 2. epoch history already exists
    h = read(TABLES / "REMEDFILM_EPOCH_HISTORY.csv")
    print(f"  REMEDFILM_EPOCH_HISTORY.csv: {len(h)} rows (existing)")

    # 3. internal evaluation
    internal = read(TABLES / "REMEDFILM_INTERNAL_METRICS.csv")
    write(TABLES / "REMEDFILM_INTERNAL_EVALUATION.csv", internal)

    # 4. external evaluation
    ext = read(TABLES / "REMEDFILM_EXTERNAL_METRICS.csv")
    write(TABLES / "REMEDFILM_EXTERNAL_EVALUATION.csv", ext)

    # 5/6. ablation + progression already exist
    print()
    print('ROOT MIRRORS (required deliverable list)')
    print(f"  REMEDFILM_ABLATION_RESULTS.csv: {len(read(TABLES / 'REMEDFILM_ABLATION_RESULTS.csv'))} rows (existing)")
    print(f"  REMEDFILM_PROGRESSION_RESULTS.csv: {len(read(TABLES / 'REMEDFILM_PROGRESSION_RESULTS.csv'))} rows (existing)")

    # mirror the six required tables to the report root
    for name in ("REMEDFILM_TRAINING_RUN_REGISTRY.csv", "REMEDFILM_EPOCH_HISTORY.csv",
                 "REMEDFILM_INTERNAL_EVALUATION.csv", "REMEDFILM_EXTERNAL_EVALUATION.csv",
                 "REMEDFILM_ABLATION_RESULTS.csv", "REMEDFILM_PROGRESSION_RESULTS.csv"):
        src = TABLES / name
        if src.exists():
            shutil.copyfile(src, OUT / name)
            print(f"  {name} -> report root")

    # ------------------------------------------------ Evidence index --------
    EVID.mkdir(parents=True, exist_ok=True)
    key = [
        ("phase21_six_model_comparison",
         "reports/tables/phase21_six_model_comparison.csv",
         "Six-model VAL808 benchmark"),
        ("phase27_preservation_result",
         "reports/audits/phase27_preservation_result.json",
         "Backbone vs FULL paired preservation on VAL808"),
        ("phase28_arm_primary_metrics",
         "reports/tables/phase28_table_02_arm_primary_metrics.csv",
         "13-arm ablation primary metrics"),
        ("phase28_bootstrap_statistics",
         "reports/tables/phase28_table_08_bootstrap_statistics.csv",
         "Paired contrasts with 95% CIs"),
        ("phase29_three_seed_summary",
         "reports/audits/phase29_phase_d_three_seed_descriptive_summary.json",
         "Three downstream seeds, descriptive"),
        ("phase30_noninferiority",
         "reports/audits/phase30_primary_noninferiority_result.json",
         "ROUTER_HOLDOUT 875 evaluation"),
        ("phase34_efficiency",
         "reports/audits/phase34_efficiency_result_v1_4.json",
         "Parameters, analytical GMACs, measured latency"),
        ("phase36_robustness",
         "reports/audits/phase36_robustness_scientific_result_v1_23.json",
         "12,928 perturbation instances"),
        ("phase39_test_descriptive",
         "reports/audits/phase39_final_test_v1_2_scientific_result.json",
         "Historical one-shot TEST descriptive result"),
        ("c2_compute_contract",
         "reports/tables/c2_barr/c2_barr_aggregate.json",
         "Conditional GMACs for the FULL assembly"),
        ("external_stress_summary",
         "reports/tables/c1_external_stress_summary.csv",
         "884-case retrospective external evidence"),
        ("global_medfilm_closure",
         "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/closure.json",
         "Backbone training closure and checkpoint hash"),
    ]
    index = []
    for name, rel, desc in key:
        p = ROOT / rel
        if not p.exists():
            index.append({"id": name, "path": rel, "description": desc,
                          "status": "MISSING"})
            continue
        sha = hashlib.sha256(p.read_bytes()).hexdigest()
        index.append({"id": name, "path": rel, "description": desc,
                      "bytes": p.stat().st_size, "sha256": sha,
                      "status": "PRESENT"})
        # keep a small copy for offline audit (all are < 2 MB)
        if p.stat().st_size < 2_000_000:
            dst = EVID / p.name
            shutil.copyfile(p, dst)

    (EVID / "EVIDENCE_INDEX.json").write_text(json.dumps({
        "artifact": "evidence_index",
        "policy": ("Headline frozen artifacts are indexed and, where small, copied "
                   "here for offline audit. Large datasets and checkpoints are "
                   "referenced by path only and never duplicated."),
        "n_entries": len(index),
        "entries": index,
    }, indent=2), encoding="utf-8")
    present = sum(1 for e in index if e["status"] == "PRESENT")
    print(f"\nEVIDENCE {present}/{len(index)} indexed, "
          f"{len(list(EVID.glob('*')))} files in Evidence/")

    (EVID / "README.md").write_text(
        "# Evidence directory\n\n"
        "Frozen artifacts that every claim in the notebook family traces back to.\n"
        "`EVIDENCE_INDEX.json` records the source path and SHA-256 of each.\n\n"
        "Small JSON/CSV files are copied here for offline audit. Datasets and\n"
        "checkpoints are referenced by path only and are never duplicated.\n\n"
        "Nothing in this directory is generated by the notebooks; it is a read-only\n"
        "snapshot of research evidence.\n",
        encoding="utf-8")


if __name__ == "__main__":
    main()
