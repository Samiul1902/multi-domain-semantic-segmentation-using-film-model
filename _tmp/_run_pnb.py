import subprocess
p = subprocess.run([r"D:/Softfors/jup/.venv/Scripts/python.exe",
                    r"D:/Softfors/jup/full_doc_report/Scripts/build_phase_notebooks.py"],
                   cwd=r"D:/Softfors/jup", capture_output=True, text=True,
                   env={**__import__('os').environ, "PYTHONPATH": r"D:/Softfors/jup/full_doc_report/Scripts"})
print(p.stdout)
if p.stderr.strip(): print("STDERR:", p.stderr[-2500:])
print("RC", p.returncode)
