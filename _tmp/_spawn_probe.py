"""Diagnostic only: can a native parent launch the canonical interpreter?"""
import os
import subprocess
import sys

VENV = r"D:\Softfors\jup\.venv\Scripts\python.exe"
BASE = r"C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe"

FLAGS = {
    "default": 0,
    "NEW_CONSOLE": getattr(subprocess, "CREATE_NEW_CONSOLE", 0x00000010),
    "NO_WINDOW": getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000),
    "DETACHED": getattr(subprocess, "DETACHED_PROCESS", 0x00000008),
}


def probe(label, exe, args, **kw):
    try:
        p = subprocess.run([exe] + args, capture_output=True, text=True,
                           timeout=40, **kw)
        out = (p.stdout or "").strip().replace("\n", " ")[:40]
        err = (p.stderr or "").strip().replace("\n", " ")[:60]
        print(f"{label:<44} rc={p.returncode:<12} out={out!r} err={err!r}")
    except Exception as exc:  # noqa: BLE001
        print(f"{label:<44} EXC={type(exc).__name__}: {exc}")


print("parent executable:", sys.executable)
print("parent cwd:", os.getcwd())
for exe, name in ((VENV, "venv"), (BASE, "base")):
    probe(f"{name} default -c pass", exe, ["-c", "pass"])
    probe(f"{name} -c print(1)", exe, ["-c", "print(1)"])
    for flag_name, flag in FLAGS.items():
        if flag_name == "default":
            continue
        probe(f"{name} {flag_name} -c pass", exe, ["-c", "pass"],
              creationflags=flag)
    probe(f"{name} empty env -c pass", exe, ["-c", "pass"], env={})
