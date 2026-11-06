import subprocess, sys
p = subprocess.run([r"D:/Softfors/jup/.venv/Scripts/python.exe", r"D:/Softfors/jup/_tmp/_mp_probe.py"],
                   cwd=r"D:/Softfors/jup", capture_output=True, text=True)
print(p.stdout)
print("STDERR:", p.stderr.strip()[:1500])
print("mp_returncode =", p.returncode)
sys.exit(p.returncode)
