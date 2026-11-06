"""Native-parent harness: spawn the canonical venv interpreter and stream results."""
import subprocess, sys
VENV = r"D:\Softfors\jup\.venv\Scripts\python.exe"
print("harness_parent_executable:", sys.executable)
print("=" * 70)
p = subprocess.run([VENV, r"D:\Softfors\jup\_tmp\_canonical_payload.py"],
                   cwd=r"D:\Softfors\jup", capture_output=True, text=True)
print(p.stdout)
if p.stderr.strip():
    print("STDERR:", p.stderr.strip()[:1500])
print("payload_returncode =", p.returncode)
print("=" * 70)
t = subprocess.run([VENV, "-m", "pytest",
                    "tests/test_phase22_scale_regional_synthetic.py",
                    "tests/test_phase42_parity_synthetic.py", "-q"],
                   cwd=r"D:\Softfors\jup", capture_output=True, text=True)
print(t.stdout[-1500:])
if t.stderr.strip():
    print("PYTEST_STDERR:", t.stderr.strip()[:800])
print("pytest_returncode =", t.returncode)
sys.exit(0 if (p.returncode == 0 and t.returncode == 0) else 1)
