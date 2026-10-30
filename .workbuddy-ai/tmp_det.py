import hashlib, subprocess, sys, json
from pathlib import Path
ROOT = Path(r"D:/Softfors/jup")
NB = ROOT / "notebooks/phasewise/phase_22_resource_gap/phase22_resource_gap_analysis.ipynb"
shas=[]
for i in range(3):
    print(f"=== build {i+1} ===", flush=True)
    r = subprocess.run([str(ROOT/".venv/Scripts/python.exe"),
                        str(ROOT/"scripts/notebooks/build_phase22_notebook.py")],
                       cwd=str(ROOT), capture_output=True, text=True)
    tail=[l for l in r.stdout.splitlines() if any(k in l for k in
          ("Notebook SHA","tracebacks","image/png","Monotonic","Cells:"))]
    print("\n".join(tail), flush=True)
    if r.returncode!=0:
        print("BUILD FAILED rc=",r.returncode,r.stderr[-3000:],flush=True); sys.exit(1)
    s=hashlib.sha256(NB.read_bytes()).hexdigest(); shas.append(s)
    print("   sha:", s, flush=True)
print("ALL IDENTICAL:", len(set(shas))==1)
Path(ROOT/".workbuddy-ai/phase22_nb_shas.json").write_text(json.dumps(shas), encoding="utf-8")
