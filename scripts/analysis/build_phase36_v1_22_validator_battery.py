#!/usr/bin/env python
"""WO#21A §7 — REBASE the v1.21 validator battery into v1.22 (write-once).

MODE: PREPARATION-ONLY / NON-CONSUMING.

For each v1.21 validator S, produce a v1.22 sibling:
    scripts/analysis/<name>_v1_22.py

Transformation (strict):
  * mechanical version rebase (v1_21->v1_22, V1_21->V1_22, v1.21->v1.22,
    V1.21->V1.22)
  * update the pinned version-specific SHAs the validator asserts about
    (v1.21 exec SHA -> v1.22 exec SHA; v1.21 launcher SHA -> v1.22 launcher SHA)
  * re-admit the v1_21 token family into the recognizer tuples so the family
    sets keep BOTH v1_21 and v1_22

Does NOT run the validators (separate step).
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
SA = ROOT / "scripts" / "analysis"

E_V121_SHA = "312886c68f056375adc3f091766777da9e1caa47c1d422673de67751e8df7b97"
E_V122_SHA = "29d29da8a9514db464f2db45f06a1ccaabf65aa302c18cd53bbb7419e2fbbd2b"
L_V121_SHA = "0711fd79ca117dedaf8eae1eb024d0754033e0417c506bd748577fec73402208"
L_V122_SHA = "eb45f2fdbaa37170f5e92445883cd87d1008522c3e022e3fc844f5464ab8bbc8"

PAIRS = [
    ("validate_phase36_v1_21_science_repairs.py",
     "validate_phase36_v1_22_science_repairs.py"),
    ("phase36_robustness_negative_controls_v1_21.py",
     "phase36_robustness_negative_controls_v1_22.py"),
    ("validate_phase36_v1_21_operational_cross_contract.py",
     "validate_phase36_v1_22_operational_cross_contract.py"),
    ("validate_phase36_v1_21_pure_release_gate.py",
     "validate_phase36_v1_22_pure_release_gate.py"),
    ("verify_phase36_v1_21_governance_coherence_readonly.py",
     "verify_phase36_v1_22_governance_coherence_readonly.py"),
    ("verify_phase36_v1_21_pure_release_gate_readonly.py",
     "verify_phase36_v1_22_pure_release_gate_readonly.py"),
]

# Token-family extensions: keep the v1_21 family alongside v1_22.
TOKEN_EXTENSIONS = [
    ('"V1.20", "v1_22", "V1_22", "V1.22",',
     '"V1.20", "v1_21", "V1_21", "V1.21", "v1_22", "V1_22", "V1.22",'),
    ('"PHASE36_V1_20", "PHASE36_V1_22",',
     '"PHASE36_V1_20", "PHASE36_V1_21", "PHASE36_V1_22",'),
    ('"phase36_v1_20", "phase36_v1_22",',
     '"phase36_v1_20", "phase36_v1_21", "phase36_v1_22",'),
    ('"v1_22", "v1_20", "v1_17"',
     '"v1_22", "v1_21", "v1_20", "v1_17"'),
    ('"V1_22", "V1_20", "V1_17"',
     '"V1_22", "V1_21", "V1_20", "V1_17"'),
    ('"v1.22", "v1.20", "v1.17"',
     '"v1.22", "v1.21", "v1.20", "v1.17"'),
    ('"V1.22", "V1.20", "V1.17"',
     '"V1.22", "V1.21", "V1.20", "V1.17"'),
    ('"phase36_robustness_v1_22", "phase36_robustness_v1_20"',
     '"phase36_robustness_v1_22", "phase36_robustness_v1_21", "phase36_robustness_v1_20"'),
]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write_once(path: Path, data: bytes) -> str:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        w = 0
        while w < len(data):
            w += os.write(fd, data[w:])
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(data):
        raise OSError(f"POST_WRITE_SIZE_MISMATCH: {path}")
    return sha(data)


def rebase(s: str) -> str:
    s = s.replace("v1.21", "v1.22")
    s = s.replace("V1.21", "V1.22")
    s = s.replace("v1_21", "v1_22")
    s = s.replace("V1_21", "V1_22")
    return s


def main() -> int:
    out = {"rebaselined": [], "skipped": []}
    for src_name, dst_name in PAIRS:
        src = SA / src_name
        dst = SA / dst_name
        if not src.exists():
            out["skipped"].append({"src": src_name, "reason": "missing"})
            continue
        if dst.exists():
            out["skipped"].append({"dst": dst_name, "reason": "already_exists"})
            continue
        text = src.read_text(encoding="utf-8")
        reb = rebase(text)
        reb = reb.replace(E_V121_SHA, E_V122_SHA)
        reb = reb.replace(L_V121_SHA, L_V122_SHA)
        for old, new in TOKEN_EXTENSIONS:
            if old in reb:
                reb = reb.replace(old, new)

        data = reb.encode("utf-8")
        sha_out = write_once(dst, data)

        a = text.splitlines()
        b = reb.splitlines()
        changed = sum(1 for l in difflib.unified_diff(a, b, lineterm="")
                      if l.startswith(("+", "-")) and not l.startswith(("+++", "---")))
        out["rebaselined"].append({
            "src": src_name, "dst": dst_name,
            "dst_sha256": sha_out,
            "changed_lines": changed,
        })
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
