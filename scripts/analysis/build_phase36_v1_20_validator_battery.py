#!/usr/bin/env python
"""WO#20 §8 — REBASE the v1.19 validator battery into v1.20 (write-once).

MODE: PREPARATION-ONLY / NON-CONSUMING.

For each v1.19 validator S, produce a v1.20 sibling:
    scripts/analysis/<name>_v1_20.py

Transformation (strict):
  * mechanical version rebase (v1_19->v1_20, V1_19->V1_20, v1.19->v1.20,
    V1.19->V1.20)
  * extend the recognizer token TUPLES so v1_20 tokens join the family sets
  * update the pinned version-specific exec SHA the validator asserts about
    (v1.19 exec SHA -> v1.20 exec SHA)

Does NOT run the validators (separate step).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
SA = ROOT / "scripts" / "analysis"

E_V120_SHA = "b9d128240596c5c6b7c040480823f4cc653d26a4bc665fc69b396d00e4fe0ad8"
E_V119_SHA = "3ec5ea920af2b6d66864b3bbc7e5362f0756777512c29be70d3e5453e18693cd"

PAIRS = [
    ("validate_phase36_v1_19_science_repairs.py",
     "validate_phase36_v1_20_science_repairs.py"),
    ("phase36_robustness_negative_controls_v1_19.py",
     "phase36_robustness_negative_controls_v1_20.py"),
    ("validate_phase36_v1_19_operational_cross_contract.py",
     "validate_phase36_v1_20_operational_cross_contract.py"),
    ("validate_phase36_v1_19_pure_release_gate.py",
     "validate_phase36_v1_20_pure_release_gate.py"),
    ("verify_phase36_v1_19_governance_coherence_readonly.py",
     "verify_phase36_v1_20_governance_coherence_readonly.py"),
    ("verify_phase36_v1_19_pure_release_gate_readonly.py",
     "verify_phase36_v1_20_pure_release_gate_readonly.py"),
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
    assert path.stat().st_size == len(data)
    return sha(data)


def rebase(s: str) -> str:
    s = s.replace("v1.19", "v1.20")
    s = s.replace("V1.19", "V1.20")
    s = s.replace("v1_19", "v1_20")
    s = s.replace("V1_19", "V1_20")
    return s


def extend_token_tuples(s: str) -> str:
    for needle in ('"V1.17", "V1.18",', '"V1.17", "V1.20",'):
        if needle in s:
            s = s.replace(needle, '"V1.17", "V1.18", "V1.20",')
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
        reb = reb.replace(E_V119_SHA, E_V120_SHA)
        reb = extend_token_tuples(reb)

        data = reb.encode("utf-8")
        sha_out = write_once(dst, data)

        import difflib
        a = text.splitlines()
        b = reb.splitlines()
        changed = sum(1 for l in difflib.unified_diff(a, b, lineterm="")
                      if l.startswith(("+", "-")) and not l.startswith(("+++", "---")))
        out["rebaselined"].append({
            "src": src_name, "dst": dst_name,
            "src_sha256": sha(text.encode("utf-8")),
            "dst_sha256": sha_out,
            "changed_lines": changed,
        })
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
