#!/usr/bin/env python
"""WO#19 §4/§5 — BUILD v1.19 EXECUTION SOURCE from FROZEN v1.18 (write-once).

MODE: NEW-REVISION PREPARATION ONLY.  NON-CONSUMING.

Creates EXACTLY ONE new artifact:

    scripts/analysis/phase36_robustness_execution_v1_19.py

It does NOT modify the frozen v1.18 source (SHA 2259ce22...).  v1.18 is
CONSUMED; v1.19 is a NEW artifact built additively.

TRANSFORMATION
--------------
1. Mechanical version rebase:  v1_18 -> v1_19 ,  V1_18 -> V1_19 ,
   v1.18 -> v1.19 , V1.18 -> V1.19  (paths, revision strings, tokens,
   identifiers).  This is the ONLY textual change permitted to the frozen
   scientific core.
2. SCIENTIFIC-PATH REPAIR D92 (the single functional change):
       OLD: targets.append(ROOT / SCIENCE_V1_18_JOURNAL_DIR)
       NEW: targets.append(V1_19_JOURNAL_DIR)
   Rationale: V1_19_JOURNAL_DIR is ALREADY an absolute pathlib.Path
   (ROOT / "reports" / "audits" / "phase36_robustness_science_v1_19_journal")
   and is the canonical journal-path authority used by _journal_record().
   Re-joining it with ROOT is BOTH undefined (the old symbol never existed)
   AND semantically wrong (ROOT / <absolute Path> discards ROOT).  Using the
   authority directly is the canonical, correct repair.

SCIENTIFIC DELTA
----------------
The set of DISTINCT repair CLASSES applied to the scientific path is exactly
{D92}.  D61 (canonical ACCEPT fuse_full_field) and D75 (POLICY_B float16
round-trip >= 0.50) are carried over UNCHANGED from v1.18.  No new scientific
choice is introduced (scientific_semantics_effect = NONE).
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")

SRC_V118 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_18.py"
OUT_V119 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_19.py"

FROZEN_V118_SHA = "2259ce22e75ba9a3a8943769dc1e0ed5724f94902f5e8955976cd6ebeb8ce63e"


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
    assert path.stat().st_size == len(data)
    return sha256_bytes(data)


# --------------------------------------------------------------------------- #
# 0) Verify the frozen v1.18 source is byte-identical to its known SHA.         #
# --------------------------------------------------------------------------- #
frozen_bytes = SRC_V118.read_bytes()
frozen_sha = sha256_bytes(frozen_bytes)
if frozen_sha != FROZEN_V118_SHA:
    print(f"FAIL_CLOSED: frozen v1.18 SHA mismatch {frozen_sha}", file=sys.stderr)
    sys.exit(3)

text = frozen_bytes.decode("utf-8")

# --------------------------------------------------------------------------- #
# 1) Mechanical version rebase (longest-first so V1_18 before v1_18 etc).       #
# --------------------------------------------------------------------------- #
# Order matters: handle dotted first won't collide; use word-boundary aware.
def rebase(s: str) -> str:
    s = s.replace("v1.18", "v1.19")
    s = s.replace("V1.18", "V1.19")
    # identifier / path-token forms: v1_18, V1_18 (and embedded: _v1_18_)
    s = s.replace("v1_18", "v1_19")
    s = s.replace("V1_18", "V1_19")
    return s


rebased = rebase(text)

# --------------------------------------------------------------------------- #
# 2) D92 repair — the single scientific-path change.                            #
# --------------------------------------------------------------------------- #
OLD_LINE = "    targets.append(ROOT / SCIENCE_V1_18_JOURNAL_DIR)"
# after rebase this became:
OLD_LINE_REBASED = "    targets.append(ROOT / SCIENCE_V1_19_JOURNAL_DIR)"
NEW_LINE = "    targets.append(V1_19_JOURNAL_DIR)"

if OLD_LINE_REBASED not in rebased:
    print("FAIL_CLOSED: expected D92 line not found after rebase", file=sys.stderr)
    sys.exit(4)
if rebased.count(OLD_LINE_REBASED) != 1:
    print("FAIL_CLOSED: D92 line not unique", file=sys.stderr)
    sys.exit(4)

repaired = rebased.replace(OLD_LINE_REBASED, NEW_LINE)

# --------------------------------------------------------------------------- #
# 3) Post-conditions.                                                          #
# --------------------------------------------------------------------------- #
# 3a) The undefined symbol must be GONE entirely.
if "SCIENCE_V1_19_JOURNAL_DIR" in repaired:
    print("FAIL_CLOSED: undefined symbol still present", file=sys.stderr)
    sys.exit(5)

# 3b) No residual v1_18 / V1_18 tokens.
leftovers = re.findall(r'v1_18|V1_18|v1\.18|V1\.18', repaired)
if leftovers:
    print(f"FAIL_CLOSED: residual v1.18 tokens: {set(leftovers)}", file=sys.stderr)
    sys.exit(6)

# 3c) File must parse.
try:
    tree = ast.parse(repaired, filename="phase36_robustness_execution_v1_19.py")
except SyntaxError as e:
    print(f"FAIL_CLOSED: v1.19 does not parse: {e}", file=sys.stderr)
    sys.exit(7)

# 3d) V1_19_JOURNAL_DIR must be defined at module scope AND used at the repair.
mod_defined = set()
for node in tree.body:
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name):
                mod_defined.add(t.id)
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        mod_defined.add(node.target.id)
if "V1_19_JOURNAL_DIR" not in mod_defined:
    print("FAIL_CLOSED: V1_19_JOURNAL_DIR not defined", file=sys.stderr)
    sys.exit(8)

# 3e) Name-resolution: every global Name load in the absence-gate functions
#     must resolve to a module-level binding (imports included).
import builtins  # noqa: F401
module_names = set(mod_defined)
for node in tree.body:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        for a in node.names:
            module_names.add((a.asname or a.name).split(".")[0])
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        module_names.add(node.name)

BUILTINS = set(dir(builtins))


def collect_global_loads(fn_name: str) -> list:
    loads: dict[str, list[int]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == fn_name:
            local = set()
            for a in ast.walk(node):
                if isinstance(a, ast.arg):
                    local.add(a.arg)
                if isinstance(a, ast.Name) and isinstance(a.ctx, ast.Store):
                    local.add(a.id)
            for a in ast.walk(node):
                if isinstance(a, ast.Name) and isinstance(a.ctx, ast.Load):
                    if a.id in local or a.id in BUILTINS:
                        continue
                    loads.setdefault(a.id, []).append(a.lineno)
    return sorted(loads.keys())


failing_fn = "v1_19_reachable_write_targets"
caller_fn = "v1_19_output_absence"  # verify_v1_19_output_absence
caller_fn = "verify_v1_19_output_absence"

unresolved = {}
for fn in (failing_fn, caller_fn):
    for name in collect_global_loads(fn):
        if name not in module_names:
            unresolved.setdefault(fn, []).append(name)

if unresolved:
    print(f"FAIL_CLOSED: unresolved globals: {unresolved}", file=sys.stderr)
    sys.exit(9)

# 3f) Confirm the repaired line exists exactly once.
if repaired.count(NEW_LINE) != 1:
    print("FAIL_CLOSED: repaired line count != 1", file=sys.stderr)
    sys.exit(10)

# --------------------------------------------------------------------------- #
# 4) Scientific-delta proof: the diff vs v1.18 is ONLY version tokens + D92.    #
# --------------------------------------------------------------------------- #
# Compute a line-level diff; classify every changed line pair.
import difflib
orig_lines = text.splitlines()
new_lines = repaired.splitlines()
sm = difflib.SequenceMatcher(a=orig_lines, b=new_lines, autojunk=False)
changed_pairs = []
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        continue
    for k in range(max(i2 - i1, j2 - j1)):
        o = orig_lines[i1 + k] if i1 + k < i2 else ""
        n = new_lines[j1 + k] if j1 + k < j2 else ""
        changed_pairs.append((o, n, tag))

non_version = []
version_only = 0
for o, n, tag in changed_pairs:
    if rebase(o) == n:
        version_only += 1
    else:
        non_version.append((o, n, tag))

# The ONLY non-version change must be the D92 repair.
d92_pair = (OLD_LINE, NEW_LINE)
non_version_effective = [p for p in non_version if p[0] != OLD_LINE or p[1] != NEW_LINE]
if non_version_effective:
    print("FAIL_CLOSED: unexpected non-version changes:", file=sys.stderr)
    for p in non_version_effective[:10]:
        print("  ", p, file=sys.stderr)
    sys.exit(11)

# --------------------------------------------------------------------------- #
# 5) Write the v1.19 source (write-once).                                       #
# --------------------------------------------------------------------------- #
OUT_V119.parent.mkdir(parents=True, exist_ok=True)
out_bytes = repaired.encode("utf-8")
out_sha = write_once(OUT_V119, out_bytes)

print(json.dumps({
    "written": str(OUT_V119.relative_to(ROOT)).replace("\\", "/"),
    "sha256": out_sha,
    "size_bytes": OUT_V119.stat().st_size,
    "frozen_v1_18_sha256": frozen_sha,
    "d92_repair": {
        "old": OLD_LINE.strip(),
        "new": NEW_LINE.strip(),
        "old_was_undefined_symbol": True,
        "new_uses_canonical_authority": "V1_19_JOURNAL_DIR",
    },
    "diff_summary": {
        "total_changed_lines": len(changed_pairs),
        "version_token_only_changes": version_only,
        "non_version_changes": non_version,
        "scientific_delta_distinct_classes": ["D92"],
    },
    "scientific_checks": {
        "undefined_symbol_absent": True,
        "residual_v1_18_tokens": 0,
        "parses": True,
        "v1_19_journal_dir_defined": True,
        "unresolved_globals": {},
    },
}, indent=2, default=str))
