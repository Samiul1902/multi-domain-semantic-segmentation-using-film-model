import subprocess, sys
p = subprocess.run([r"D:/Softfors/jup/.venv/Scripts/python.exe", r"D:/Softfors/jup/_tmp/_toolcheck.py"],
                   cwd=r"D:/Softfors/jup", capture_output=True, text=True)
print(p.stdout); print("STDERR", p.stderr[-800:]); print("RC", p.returncode)
