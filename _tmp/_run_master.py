import subprocess, os
env = {**os.environ, "PYTHONPATH": r"D:/Softfors/jup/full_doc_report/Scripts"}
p = subprocess.run([r"D:/Softfors/jup/.venv/Scripts/python.exe",
                    r"D:/Softfors/jup/full_doc_report/Scripts/build_complete_master.py"],
                   cwd=r"D:/Softfors/jup", capture_output=True, text=True, env=env)
print(p.stdout)
if p.stderr.strip(): print("STDERR:", p.stderr[-1500:])
print("RC", p.returncode)
