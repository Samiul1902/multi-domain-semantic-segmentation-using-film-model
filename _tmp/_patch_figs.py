import pathlib

p = pathlib.Path(r"D:\Softfors\jup\full_doc_report\Scripts\build_figures.py")
s = p.read_text(encoding="utf-8")

s = s.replace(
    '    six_g = jload(ROOT / "reports/tables/phase21_six_model_compute.csv")',
    '    six_g = load_csv(ROOT / "reports/tables/phase21_six_model_compute.csv")')

old_block = '''    pc = load_csv(ROOT / "reports/tables/phase28_table_07_matched_paired_contrasts.csv")
    cols = list(pc[0].keys())
    print("    paired contrast cols:", cols)
    ckey = next((c for c in cols if "contrast" in c.lower() or c.lower() in ("comparison", "pair")), cols[0])
    pkey = next((c for c in cols if "mean_diff" in c.lower() or c.lower() == "point"), None)
    lo = next((c for c in cols if "ci_low" in c.lower() or c.lower().endswith("low")), None)
    hi = next((c for c in cols if "ci_high" in c.lower() or c.lower().endswith("high")), None)'''

new_block = '''    pc = load_csv(ROOT / "reports/tables/phase28_table_07_matched_paired_contrasts.csv")
    bs = {r["contrast"]: r for r in load_csv(
        ROOT / "reports/tables/phase28_table_08_bootstrap_statistics.csv")}
    for r in pc:
        b = bs.get(r["contrast"], {})
        r["ci_low"] = b.get("ci95_low", "")
        r["ci_high"] = b.get("ci95_high", "")
    cols = list(pc[0].keys())
    print("    paired contrast cols:", cols)
    ckey = "contrast"
    pkey = "paired_mean_difference"
    lo = "ci_low"
    hi = "ci_high"'''

assert old_block in s, "contrast block not found"
s = s.replace(old_block, new_block)
p.write_text(s, encoding="utf-8")
print("PATCHED")
