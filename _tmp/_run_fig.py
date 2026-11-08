import subprocess
p = subprocess.run([r"D:/Softfors/jup/.venv/Scripts/python.exe",
                    r"D:/Softfors/jup/assets/figures/generate_methodology.py"],
                   cwd=r"D:/Softfors/jup", capture_output=True, text=True)
print(p.stdout)
if p.stderr.strip(): print("STDERR:", p.stderr[-2000:])
print("RC", p.returncode)
