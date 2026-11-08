"""Build a corrected component-parameter table.

`reports/tables/phase26_component_inventory.csv` has a data defect: the `parameters`
value for G is 31,551,740,928, which is G's total MACs (from
`phase21_analytical_mac_count.json`), not its parameter count (3,523,001).
The table is not modified — a corrected derived table is produced instead and the
defect is recorded.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"
TABLES = OUT / "tables"


def main() -> None:
    inv = {r["symbol"]: r for r in csv.DictReader(
        (ROOT / "reports/tables/phase26_component_inventory.csv").open(encoding="utf-8"))}
    contract = json.loads((ROOT / "reports/audits/phase34_parameter_count_contract.json")
                          .read_text(encoding="utf-8"))
    hist = contract["historical_parameter_counts"]
    total = int(hist["sum_total_resident"])
    closure = json.loads((ROOT / "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/closure.json")
                         .read_text(encoding="utf-8"))
    g_params = int(hist["G"])

    rows = []
    for sym, src_note in (("G", "phase34 historical_parameter_counts.G (inventory field holds MACs)"),
                          ("R_psi", "phase34 historical_parameter_counts / phase26 inventory"),
                          ("B_phi", "phase34 historical_parameter_counts / phase26 inventory"),
                          ("S_omega", "phase34 historical_parameter_counts / phase26 inventory")):
        rec = inv[sym]
        params = int(hist[sym])
        rows.append({
            "symbol": sym,
            "model_class": rec["model_class"],
            "role": rec["role"],
            "conditional": rec["conditional"],
            "parameters": params,
            "parameter_source": src_note,
            "checkpoint": rec["checkpoint"],
            "checkpoint_sha256": rec["sha256"],
        })
    s = sum(r["parameters"] for r in rows)
    rows.append({
        "symbol": "FULL", "model_class": "assembled", "role": "PROPOSED_SYSTEM",
        "conditional": "True", "parameters": total,
        "parameter_source": "phase34_parameter_count_contract.json TOTAL_RESIDENT_PARAMETERS",
        "checkpoint": "bundle of the four component checkpoints", "checkpoint_sha256": "",
    })

    with (TABLES / "REMEDFILM_COMPONENT_PARAMETERS.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print("component sum:", s, "| contract total:", total, "| match:", s == total)
    assert s == total

    # record the defect
    p = OUT / "SCIENTIFIC_CORRECTIONS.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d.setdefault("data_defects", []).append({
        "id": "DEFECT-01",
        "artifact": "reports/tables/phase26_component_inventory.csv",
        "column": "parameters",
        "row": "G",
        "observed_value": 31551740928,
        "correct_value": g_params,
        "diagnosis": ("The stored value equals G's total MACs "
                      "(phase21_analytical_mac_count.json total_macs = 31,551,740,928), "
                      "not its parameter count. The column mixes units for one row."),
        "impact": ("Any sum of the `parameters` column overstates the system by "
                   "~31.5 billion and cannot reconcile to 4,837,420."),
        "resolution": ("The frozen table is NOT modified. A corrected derived table, "
                       "tables/REMEDFILM_COMPONENT_PARAMETERS.csv, is used by the "
                       "notebooks, and every notebook validates the arithmetic against "
                       "phase34_parameter_count_contract.json."),
        "detected_by": "full_doc_report/Scripts/build_required_tables.py",
    })
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")
    print("DEFECT-01 recorded")


if __name__ == "__main__":
    main()
