#!/usr/bin/env python
"""WO#19 §11 — REBASE the v1.18 validator battery into v1.19 (write-once).

MODE: PREPARATION-ONLY / NON-CONSUMING.

For each v1.18 validator S, produce a v1.19 sibling:
    scripts/analysis/<name>_v1_19.py

Transformation (strict):
  * mechanical version rebase (v1_18->v1_19, V1_18->V1_19, v1.18->v1.19,
    V1.18->V1.19)
  * extend the recognizer token TUPLES so v1_19 / v1.19 / V1_19 join the
    version-family sets (so the v1.18->v1.19 diff is correctly classified as
    version-token-only)
  * update the pinned version-specific SHAs the validator asserts about (the
    v1.18 source SHA -> v1.19 source SHA, output report paths -> v1_19)
  * KEEP references to SHARED / unchanged governance artifacts byte-identical

The driver reports a per-file diff summary so the operator can audit exactly
what changed.  It does NOT run the validators (that is a separate step).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
SA = ROOT / "scripts" / "analysis"

E_V119_SHA = "3ec5ea920af2b6d66864b3bbc7e5362f0756777512c29be70d3e5453e18693cd"
E_V118_SHA = "2259ce22e75ba9a3a8943769dc1e0ed5724f94902f5e8955976cd6ebeb8ce63e"

# sripts to rebase: (v1_18 name, v1_19 name)
PAIRS = [
    ("validate_phase36_v1_18_science_repairs.py",
     "validate_phase36_v1_19_science_repairs.py"),
    ("phase36_robustness_negative_controls_v1_18.py",
     "phase36_robustness_negative_controls_v1_19.py"),
    ("validate_phase36_v1_18_operational_cross_contract.py",
     "validate_phase36_v1_19_operational_cross_contract.py"),
    ("validate_phase36_v1_18_pure_release_gate.py",
     "validate_phase36_v1_19_pure_release_gate.py"),
    ("verify_phase36_v1_18_governance_coherence_readonly.py",
     "verify_phase36_v1_19_governance_coherence_readonly.py"),
    ("verify_phase36_v1_18_pure_release_gate_readonly.py",
     "verify_phase36_v1_19_pure_release_gate_readonly.py"),
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
    s = s.replace("v1.18", "v1.19")
    s = s.replace("V1.18", "V1.19")
    s = s.replace("v1_18", "v1_19")
    s = s.replace("V1_18", "V1_19")
    return s


def extend_token_tuples(s: str) -> str:
    """Add v1_19 family tokens to the recognizer tuples.

    In the v1.18 validators the version-family tuples list v1_14..v1_18. After
    the rebase they read v1_14..v1_19, but the tuple members must ALSO include
    the *root* v1_19 spelling that the rebase produced in the compared sources.
    We append the v1_19 members right before the closing paren of the named
    tuples to keep the recognizer complete.
    """
    # Append v1_19 tokens to each version-token tuple.
    additions = {
        '"v1_19", "V1_19", "V1.19",':
            '        "v1_19", "V1_19", "v1.19", "V1.19",\n',
    }
    # Simpler + robust: ensure these literal members exist inside the tuple
    # definitions by inserting them after the v1_19 already present (rebased).
    for needle in ('"V1.17", "V1.18",', '"V1.17", "V1.19",'):
        if needle in s:
            s = s.replace(needle, '"V1.17", "V1.18", "V1.19",')
    # Ensure the JOURNAL/exec-fn tokens reference v1_19 names (already rebased).
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

        # Update the pinned v1.18 exec SHA references to the v1.19 exec SHA
        # ONLY where they refer to the execution source being validated.
        reb = reb.replace(E_V118_SHA, E_V119_SHA)

        reb = extend_token_tuples(reb)

        # Replace the literal j ournal/exec function names in recognizer tokens
        # (already rebased by rebase()); nothing more needed.

        data = reb.encode("utf-8")
        sha_out = write_once(dst, data)

        # diff summary vs source
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
