#!/usr/bin/env python
"""WO#21A §2 — BUILD the v1.22 EXECUTION SOURCE from FROZEN v1.21 (write-once).

MODE: NEW-REVISION PREPARATION ONLY.  NON-CONSUMING.

Creates EXACTLY ONE new artifact:

    scripts/analysis/phase36_robustness_execution_v1_22.py

It does NOT modify the frozen v1.21 source (SHA 312886c6...).  v1.21 is
NOT_EXECUTED__PRELAUNCH_REAL_PATH_DEFECT (never a consumed attempt); v1.22 is a
NEW revision built additively.

TRANSFORMATION
--------------
Mechanical version-token rebase (the ONLY textual change permitted):
    v1.21 -> v1.22 ,  V1.21 -> V1.22 ,  v1_21 -> v1_22 ,  V1_21 -> V1_22

SCIENTIFIC DELTA
----------------
The set of DISTINCT scientific repair CLASSES applied is exactly {} — the
v1.21 -> v1.22 SCIENTIFIC delta is 0.  D61, D75 POLICY_B, D93A journal repair,
D95 interruption-safe supervisor semantics, router, ROI, refiner, post-safety,
thresholds, perturbations, seeds, VAL808 identities/order, metrics, KUB
reporting-only subgroup semantics and the runtime precision policy are carried
over UNCHANGED.  The v1.22 repair is LAUNCHER-REAL-DISPATCH-CALL-ONLY (D96),
which does NOT touch this scientific execution source at all.

PROOF
-----
Every diff line vs v1.21 must satisfy rebase(old) == new (version-token only).
ANY non-version change -> FAIL CLOSED (we must not silently change science).
"""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")

SRC_V121 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_21.py"
OUT_V122 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_22.py"

FROZEN_V121_SHA = "312886c68f056375adc3f091766777da9e1caa47c1d422673de67751e8df7b97"


def sha256_bytes(b: bytes) -> str:
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
    return sha256_bytes(data)


def rebase(s: str) -> str:
    s = s.replace("v1.21", "v1.22")
    s = s.replace("V1.21", "V1.22")
    s = s.replace("v1_21", "v1_22")
    s = s.replace("V1_21", "V1_22")
    return s


def main() -> int:
    if OUT_V122.exists():
        print(f"REFUSE_OVERWRITE {OUT_V122.name}", file=sys.stderr)
        return 1

    frozen_bytes = SRC_V121.read_bytes()
    frozen_sha = sha256_bytes(frozen_bytes)
    if frozen_sha != FROZEN_V121_SHA:
        print(f"FAIL_CLOSED: frozen v1.21 SHA mismatch {frozen_sha}", file=sys.stderr)
        return 3

    text = frozen_bytes.decode("utf-8")
    rebased = rebase(text)

    # ---- post-conditions -------------------------------------------------- #
    leftovers = re.findall(r'v1_21|V1_21|v1\.21|V1\.21', rebased)
    if leftovers:
        print(f"FAIL_CLOSED: residual v1.21 tokens: {set(leftovers)}", file=sys.stderr)
        return 6

    try:
        ast.parse(rebased, filename="phase36_robustness_execution_v1_22.py")
    except SyntaxError as e:
        print(f"FAIL_CLOSED: v1.22 does not parse: {e}", file=sys.stderr)
        return 7

    # D61 / D75 POLICY_B / D93A / D95 markers preserved verbatim.
    for marker in ("fuse_full_field(p_global, refined, geom)",
                   "def _phase27_scored_final_binary(p_final_live):",
                   "p_f16 = p.astype(np.float16)",
                   "p_scored = p_f16.astype(np.float32)",
                   "SEGMENTATION_OUTPUT_THRESHOLD",
                   "def _write_once_json("):
        if marker not in rebased:
            print(f"FAIL_CLOSED: marker {marker!r} missing", file=sys.stderr)
            return 11

    # ---- scientific-delta proof: EVERY diff line must be version-only ----- #
    orig_lines = text.splitlines()
    new_lines = rebased.splitlines()
    sm = difflib.SequenceMatcher(a=orig_lines, b=new_lines, autojunk=False)
    changed_pairs = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        for k in range(max(i2 - i1, j2 - j1)):
            o = orig_lines[i1 + k] if i1 + k < i2 else ""
            n = new_lines[j1 + k] if j1 + k < j2 else ""
            changed_pairs.append((o, n, tag))

    version_only = 0
    non_version = []
    for o, n, tag in changed_pairs:
        if rebase(o) == n:
            version_only += 1
        else:
            non_version.append((o, n, tag))

    if non_version:
        print("FAIL_CLOSED: unexpected non-version changes (science must be unchanged):",
              file=sys.stderr)
        for p in non_version[:20]:
            print("  ", p, file=sys.stderr)
        return 12

    # ---- write ------------------------------------------------------------ #
    out_bytes = rebased.encode("utf-8")
    out_sha = write_once(OUT_V122, out_bytes)

    print(json.dumps({
        "written": str(OUT_V122.relative_to(ROOT)).replace("\\", "/"),
        "sha256": out_sha,
        "size_bytes": OUT_V122.stat().st_size,
        "frozen_v1_21_sha256": frozen_sha,
        "diff_summary": {
            "total_changed_lines": len(changed_pairs),
            "version_token_only_changes": version_only,
            "non_version_changes": len(non_version),
            "scientific_delta_distinct_classes": [],
            "scientific_delta_count_v1_21_to_v1_22": 0,
        },
        "scientific_checks": {
            "residual_v1_21_tokens": 0,
            "parses": True,
            "d61_marker_present": True,
            "d75_policy_b_marker_present": True,
            "d93a_helper_present": True,
            "d95_supervisor_semantics_untouched": True,
        },
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
