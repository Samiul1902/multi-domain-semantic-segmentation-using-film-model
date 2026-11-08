import pathlib
import shutil

# --- 1. classify full_doc_report outputs properly -------------------------
p = pathlib.Path(r"D:\Softfors\jup\full_doc_report\Scripts\build_inventory.py")
s = p.read_text(encoding="utf-8")

old = '''        generated = any(str(p).startswith(str(d)) for d in GENERATED_DIRS)
        if generated:
            eligibility = "GENERATED_BY_CONSOLIDATION"
        elif "TRAINING" in "".join(side):
            eligibility = "ARCHIVAL_ONLY_TRAINING_CELLS_BLOCKED"
        else:
            eligibility = "ANALYSIS_ELIGIBLE"'''

new = '''        in_report = str(p).startswith(str(OUT))
        preserved = str(p).startswith(str(OUT / "notebooks_original"))
        archived = str(p).startswith(str(OUT / "_prior_consolidation_archive"))
        deliverable = in_report and not preserved and not archived

        if archived:
            status = "ARCHIVED_SUPERSEDED"
            eligibility = "NOT_PART_OF_DELIVERABLE"
        elif preserved:
            status = "PRESERVED_SOURCE"
            eligibility = "ARCHIVAL_ONLY_TRAINING_CELLS_BLOCKED"
        elif deliverable:
            status = "DELIVERABLE"
            eligibility = "ANALYSIS_ELIGIBLE"
        elif "TRAINING" in "".join(side):
            status = "SOURCE_OF_TRUTH"
            eligibility = "ARCHIVAL_ONLY_TRAINING_CELLS_BLOCKED"
        else:
            status = "SOURCE_OF_TRUTH"
            eligibility = "ANALYSIS_ELIGIBLE"'''
assert old in s
s = s.replace(old, new)

old2 = '''            "merge_status": "GENERATED" if generated else "SOURCE_OF_TRUTH",'''
new2 = '''            "merge_status": status,'''
assert old2 in s
s = s.replace(old2, new2)

old3 = '''    print(f"GENERATED {sum(1 for r in rows if r['merge_status']=='GENERATED')}")'''
new3 = '''    from collections import Counter as _C
    print("STATUS:", dict(_C(r["merge_status"] for r in rows)))'''
assert old3 in s
s = s.replace(old3, new3)
p.write_text(s, encoding="utf-8")

# --- 2. move the two remaining stale stubs into the archive ---------------
gen = pathlib.Path(r"D:\Softfors\jup\full_doc_report\notebooks_generated")
arch = pathlib.Path(r"D:\Softfors\jup\full_doc_report\_prior_consolidation_archive\notebooks_generated_stubs")
arch.mkdir(parents=True, exist_ok=True)
for name in ("01_remedfilm_training_history_analysis.ipynb",
             "03_remedfilm_external_stress_evaluation.ipynb"):
    src = gen / name
    if src.exists():
        shutil.move(str(src), str(arch / name))
        print("archived stub:", name)

print("PATCHED")
