import subprocess
import sys
from pathlib import Path

configs = [
    (512, 3), (512, 5), (512, 7),
    (768, 3), (768, 5), (768, 7)
]

python_exe = r"D:\Softfors\jup\.venv\Scripts\python.exe"
script = r"D:\Softfors\jup\scripts\training\train_phase13b_localizer.py"

for res, sig in configs:
    success = False
    for batch, accum in [(4, 1), (2, 2), (1, 4)]:
        print(f"==================================================")
        print(f"Running r{res} s{sig} batch={batch} accum={accum}")
        print(f"==================================================")
        
        cmd = [python_exe, script, "--resolution", str(res), "--sigma", str(sig), "--batch", str(batch), "--accum", str(accum)]
        
        # Run process and wait
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            print(result.stdout)
            if result.returncode == 0:
                print(f"Success r{res} s{sig}")
                success = True
                break
            elif "CUDA out of memory" in result.stderr or "CUDA error: out of memory" in result.stderr:
                print(f"OOM on r{res} s{sig} batch={batch}. Falling back...")
            else:
                print(f"Failed with unknown error on r{res} s{sig}:")
                print(result.stderr)
                break
        except Exception as e:
            print(f"Exception: {e}")
            break
            
    if not success:
        print(f"Failed completely on r{res} s{sig}. Moving to next.")
        
print("Finished all candidates.")

