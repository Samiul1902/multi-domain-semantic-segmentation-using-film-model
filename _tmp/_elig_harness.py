import subprocess, sys
VENV = r"D:/Softfors/jup/.venv/Scripts/python.exe"
p = subprocess.run([VENV, r"D:/Softfors/jup/_tmp/_eligibility.py"], cwd=r"D:/Softfors/jup",
                   capture_output=True, text=True)
print(p.stdout)
if p.stderr.strip():
    print("STDERR:", p.stderr.strip()[:3000])
print("eligibility_returncode =", p.returncode)
sys.exit(p.returncode)
