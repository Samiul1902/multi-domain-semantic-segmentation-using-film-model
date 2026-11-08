import sys, importlib
print("EXE", sys.executable)
print("PREFIX", sys.prefix)
mods = ["matplotlib","numpy","pandas","PIL","torch","nbformat","nbclient","jupyter_client","ipykernel","scipy","seaborn","docx"]
for m in mods:
    try:
        mod = importlib.import_module(m)
        print(f"OK   {m} {getattr(mod,'__version__','')}")
    except Exception as e:
        print(f"MISS {m} {type(e).__name__}")
import torch
print("CUDA", torch.cuda.is_available(), torch.version.cuda)
