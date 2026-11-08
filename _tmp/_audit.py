import csv, json, pathlib, re
OUT = pathlib.Path(r"D:/Softfors/jup/full_doc_report")
qa = (OUT/"REMEDFILM_FINAL_SCIENTIFIC_QA.md").read_text(encoding="utf-8")

def rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))

qa_checks = json.loads((OUT/"REMEDFILM_FINAL_QA_CHECKS.json").read_text(encoding="utf-8"))
ex = json.loads((OUT/"REMEDFILM_NOTEBOOK_EXECUTION_REPORT.json").read_text(encoding="utf-8"))
reg = json.loads((OUT/"figure_registry.json").read_text(encoding="utf-8"))
comp = rows(OUT/"tables/REMEDFILM_COMPONENT_TRAINING_HISTORY.csv")
vis = rows(OUT/"tables/REMEDFILM_FULL_VISUAL_EVIDENCE_INDEX.csv")
ap = rows(OUT/"tables/REMEDFILM_ABLATION_AND_PROGRESSION.csv")
rec = json.loads((OUT/"REMEDFILM_FULL_RESULT_RECONCILIATION.json").read_text(encoding="utf-8"))
regc = json.loads((OUT/"REMEDFILM_FULL_COMPONENT_REGISTRY.json").read_text(encoding="utf-8"))
pm = json.loads((OUT/"Original_Phasewise_Notebooks/PRESERVATION_MANIFEST.json").read_text(encoding="utf-8"))
mp = rows(OUT/"REPORT_NOTEBOOK_FIGURE_MAPPING.csv")

facts = [
    ("checks passed",       f"{qa_checks['n_passed']} / {qa_checks['n_checks']}", "38 / 38"),
    ("notebooks executed",  str(ex["n_notebooks"]), "22 / 22"),
    ("cells executed",      f"{ex['total_executed_cells']} / {ex['total_code_cells']}", "292 / 292"),
    ("figures",             str(len(reg)), "49"),
    ("figure mapping rows", str(len(mp)), "49"),
    ("component records",   f"{len(comp):,}", "16,679"),
    ("visual panels",       str(len(vis)), "22"),
    ("ablation+prog rows",  str(len(ap)), "19"),
    ("components verified", str(len(regc["components"])), "4"),
    ("param total",         f"{regc['verified_total_parameters']:,}", "4,837,420"),
    ("canonical dice",      f"{rec['canonical_macro_dice']:.6f}", "0.837290"),
    ("reconciliation",      rec["verdict"], "REPORTING_INCONSISTENCY"),
    ("preserved notebooks", str(pm["n_verified"]), "108"),
]
print(f"{'FACT':24s} {'ACTUAL':22s} {'IN QA':22s} OK")
ok = True
for name, actual, expected in facts:
    good = actual == expected
    ok &= good
    print(f"{name:24s} {actual:22s} {expected:22s} {'yes' if good else 'NO'}")

# claims that must appear in the QA text
claims = ["38 / 38", "292 / 292", "4,837,420", "0.837290", "16,679", "22 panels",
          "49 / 49", "108 / 108", "REPORTING_INCONSISTENCY", "14/14"]
missing = [c for c in claims if c not in qa]
print("\nQA text missing claims:", missing or "none")
print("ALL CONSISTENT:", ok and not missing)
