import subprocess
for s in ("build_tables_extra.py",):
    p = subprocess.run([r"D:/Softfors/jup/.venv/Scripts/python.exe",
                        rf"D:/Softfors/jup/full_doc_report/Scripts/{s}"],
                       cwd=r"D:/Softfors/jup", capture_output=True, text=True)
    print(p.stdout)
    if p.stderr.strip(): print("STDERR:", p.stderr[-2000:])
    print("RC", p.returncode)
