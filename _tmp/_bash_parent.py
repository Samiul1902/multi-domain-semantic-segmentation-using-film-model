import subprocess, sys
BASH = r"C:/Program Files/Git/bin/bash.exe"
cmd = r'cd /d/Softfors/jup && ./.venv/Scripts/python.exe -c pass'
p = subprocess.run([BASH, '-c', cmd], capture_output=True)
print("bash_as_parent_returncode =", p.returncode, hex(p.returncode & 0xFFFFFFFF))
print("stderr_tail =", p.stderr.decode('utf-8','replace').strip()[-200:])
# control: native parent direct
p2 = subprocess.run([r"D:/Softfors/jup/.venv/Scripts/python.exe", "-c", "pass"])
print("native_parent_returncode =", p2.returncode)
