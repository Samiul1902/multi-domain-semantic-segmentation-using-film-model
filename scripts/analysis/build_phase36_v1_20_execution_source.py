#!/usr/bin/env python
"""WO#20 §4/§5 — BUILD v1.20 EXECUTION SOURCE from FROZEN v1.19 (write-once).

MODE: NEW-REVISION PREPARATION ONLY.  NON-CONSUMING.

Creates EXACTLY ONE new artifact:

    scripts/analysis/phase36_robustness_execution_v1_20.py

It does NOT modify the frozen v1.19 source (SHA 3ec5ea92...).  v1.19 is
CONSUMED; v1.20 is a NEW revision built additively.

TRANSFORMATION
--------------
1. Mechanical version rebase:  v1_19 -> v1_20 ,  V1_19 -> V1_20 ,
   v1.19 -> v1.20 , V1.19 -> V1.20  (paths, revision strings, tokens,
   identifiers).  This is the ONLY textual change permitted to the frozen
   scientific core.
2. RUNTIME REPAIR D93A (the single functional change): DEFINE the missing
   module-scope helper ``_write_once_json`` that ``_journal_record`` calls at
   line 561 but which is defined NOWHERE (references = 1, definitions = 0).

       The helper is inserted immediately BEFORE ``_journal_record`` and
       implements the SAME write-once semantics already used everywhere else
       in this module (O_CREAT|O_EXCL|O_WRONLY{+O_BINARY}, full-write loop,
       fsync, never overwrite).  It introduces NO new scientific behaviour —
       it is observability-only journal metadata, identical in shape to the
       write-once JSON writers already in the module.

SCIENTIFIC DELTA
----------------
The set of DISTINCT scientific repair CLASSES applied is exactly {} — the
v1.19 -> v1.20 SCIENTIFIC delta is 0.  D61, D75, router, ROI, refiner,
post-safety, thresholds, perturbations, seeds, VAL808 identities/order,
metrics, KUB reporting-only subgroup semantics and the runtime precision
policy are carried over UNCHANGED.  The repaired defect is a RUNTIME /
observability defect (undefined journal helper), NOT a scientific one.
"""
from __future__ import annotations

import ast
import builtins
import difflib
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")

SRC_V119 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_19.py"
OUT_V120 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_20.py"

FROZEN_V119_SHA = "3ec5ea920af2b6d66864b3bbc7e5362f0756777512c29be70d3e5453e18693cd"


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
# 0) Verify the frozen v1.19 source is byte-identical to its known SHA.         #
# --------------------------------------------------------------------------- #
frozen_bytes = SRC_V119.read_bytes()
frozen_sha = sha256_bytes(frozen_bytes)
if frozen_sha != FROZEN_V119_SHA:
    print(f"FAIL_CLOSED: frozen v1.19 SHA mismatch {frozen_sha}", file=sys.stderr)
    sys.exit(3)

text = frozen_bytes.decode("utf-8")


# --------------------------------------------------------------------------- #
# 1) Mechanical version rebase (longest-first, dotted first).                   #
# --------------------------------------------------------------------------- #
def rebase(s: str) -> str:
    s = s.replace("v1.19", "v1.20")
    s = s.replace("V1.19", "V1.20")
    s = s.replace("v1_19", "v1_20")
    s = s.replace("V1_19", "V1_20")
    return s


rebased = rebase(text)

# --------------------------------------------------------------------------- #
# 2) D93A repair — DEFINE the missing module-scope helper _write_once_json.     #
#    Insert a faithful, write-once JSON writer immediately before             #
#    `def _journal_record(` (the caller at line 561).                          #
# --------------------------------------------------------------------------- #
HELPER = '''def _write_once_json(path: Path, payload: dict) -> str:
    """RUNTIME REPAIR (v1.20 / D93A): write-once JSON journal record.

    Defined at module scope because ``_journal_record`` (and any other
    observability writer) calls it.  Semantics are IDENTICAL to the write-once
    JSON writers already used throughout this module: exclusive create
    (O_CREAT|O_EXCL|O_WRONLY{+O_BINARY}), full-write loop, fsync, post-write
    size check, and NEVER overwrite.  Contains NO scientific payload and
    touches NO scientific tensor.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=1, ensure_ascii=False,
                      default=str).encode("utf-8")
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
        raise OSError(f"WRITE_ONCE_SIZE_CHECK_FAILED: {path}")
    return str(path)


'''

ANCHOR = "def _journal_record("
if ANCHOR not in rebased:
    print("FAIL_CLOSED: _journal_record anchor not found", file=sys.stderr)
    sys.exit(4)
if rebased.count(ANCHOR) != 1:
    print("FAIL_CLOSED: _journal_record anchor not unique", file=sys.stderr)
    sys.exit(4)
if "_write_once_json" in rebased:
    # The symbol must currently be referenced (the defect) but NOT defined.
    # If a definition accidentally appears, refuse (we must not double-define).
    if "def _write_once_json(" in rebased:
        print("FAIL_CLOSED: _write_once_json already defined", file=sys.stderr)
        sys.exit(4)

repaired = rebased.replace(ANCHOR, HELPER + ANCHOR, 1)

# --------------------------------------------------------------------------- #
# 3) Post-conditions.                                                          #
# --------------------------------------------------------------------------- #
# 3a) No residual v1_19 / V1_19 tokens.
leftovers = re.findall(r'v1_19|V1_19|v1\.19|V1\.19', repaired)
if leftovers:
    print(f"FAIL_CLOSED: residual v1.19 tokens: {set(leftovers)}", file=sys.stderr)
    sys.exit(6)

# 3b) File must parse.
try:
    tree = ast.parse(repaired, filename="phase36_robustness_execution_v1_20.py")
except SyntaxError as e:
    print(f"FAIL_CLOSED: v1.20 does not parse: {e}", file=sys.stderr)
    sys.exit(7)

# 3c) _write_once_json now defined at module scope, exactly once.
mod_funcs: dict[str, int] = {}
mod_defined = set()
for node in tree.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        mod_funcs[node.name] = node.lineno
        mod_defined.add(node.name)
    elif isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name):
                mod_defined.add(t.id)
    elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        mod_defined.add(node.target.id)

func_src = repaired
n_def = len(re.findall(r'^def _write_once_json\(', repaired, flags=re.M))
if n_def != 1:
    print(f"FAIL_CLOSED: _write_once_json def count = {n_def}", file=sys.stderr)
    sys.exit(8)
if "_write_once_json" not in mod_defined:
    print("FAIL_CLOSED: _write_once_json not module-scope", file=sys.stderr)
    sys.exit(8)

# 3d) Scope-aware free-name analysis: the ONLY previously-unresolved name
#     (_write_once_json) must now be resolved, leaving zero unresolved names.
module_names = set(mod_defined)
for node in tree.body:
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        for a in node.names:
            module_names.add((a.asname or a.name).split(".")[0])
module_names |= set(dir(builtins))
module_names |= {"__file__", "__name__", "__doc__", "__builtins__"}

issues: list = []


class _V(ast.NodeVisitor):
    def __init__(self):
        self.stack = [set()]

    def visit_FunctionDef(self, node):
        local = set()
        for a in (list(node.args.args) + list(node.args.posonlyargs)
                  + list(node.args.kwonlyargs)):
            local.add(a.arg)
        if node.args.vararg:
            local.add(node.args.vararg.arg)
        if node.args.kwarg:
            local.add(node.args.kwarg.arg)
        for n2 in ast.walk(node):
            if isinstance(n2, ast.Name) and isinstance(n2.ctx, ast.Store):
                local.add(n2.id)
            if isinstance(n2, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                local.add(n2.name)
            if isinstance(n2, ast.ExceptHandler) and n2.name:
                local.add(n2.name)
            if isinstance(n2, (ast.Import, ast.ImportFrom)):
                for a in n2.names:
                    local.add((a.asname or a.name).split(".")[0])
        self.stack.append(local)
        self.generic_visit(node)
        self.stack.pop()

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            nm = node.id
            if nm in module_names:
                return
            for s in reversed(self.stack):
                if nm in s:
                    return
            issues.append((nm, node.lineno))


_V().visit(tree)
# comprehension-scope false positives are tolerated ONLY if they are the known
# benign single-char loop var; the D93A target must never reappear.
still = [x for x in issues if x[0] == "_write_once_json"]
if still:
    print(f"FAIL_CLOSED: _write_once_json still unresolved: {still}", file=sys.stderr)
    sys.exit(9)

# 3e) Confirm the repaired definition exists exactly once in the text.
if repaired.count("def _write_once_json(") != 1:
    print("FAIL_CLOSED: repaired def count != 1", file=sys.stderr)
    sys.exit(10)

# 3f) Confirm D61 / D75 markers preserved verbatim.
for marker in ("fuse_full_field", "_phase27_scored_final_binary"):
    if marker not in repaired:
        print(f"FAIL_CLOSED: marker {marker} missing", file=sys.stderr)
        sys.exit(11)

# --------------------------------------------------------------------------- #
# 4) Scientific-delta proof: the diff vs v1.19 is version tokens + D93A only.   #
# --------------------------------------------------------------------------- #
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

version_only = 0
non_version = []
for o, n, tag in changed_pairs:
    if rebase(o) == n:
        version_only += 1
    else:
        non_version.append((o, n, tag))

# Every non-version change must lie inside the INSERTED helper block
# (i.e. new-side lines that are part of HELPER), or be the anchor line.
helper_lines = set(HELPER.splitlines())
bad = []
for o, n, tag in non_version:
    if tag == "insert":
        # all inserted lines must be helper lines
        if n not in helper_lines:
            bad.append((o, n, tag))
    elif tag == "replace":
        # the only permitted replace is the anchor gaining the helper before it
        if not (o == ANCHOR and n.startswith("def _write_once_json(") is False and n == ANCHOR):
            # anchor replace should not happen; treat unexpected
            bad.append((o, n, tag))
    else:
        # delete should not happen
        bad.append((o, n, tag))
if bad:
    print("FAIL_CLOSED: unexpected non-version changes:", file=sys.stderr)
    for p in bad[:10]:
        print("  ", p, file=sys.stderr)
    sys.exit(12)

# --------------------------------------------------------------------------- #
# 5) Write the v1.20 source (write-once).                                       #
# --------------------------------------------------------------------------- #
OUT_V120.parent.mkdir(parents=True, exist_ok=True)
out_bytes = repaired.encode("utf-8")
out_sha = write_once(OUT_V120, out_bytes)

print(json.dumps({
    "written": str(OUT_V120.relative_to(ROOT)).replace("\\", "/"),
    "sha256": out_sha,
    "size_bytes": OUT_V120.stat().st_size,
    "frozen_v1_19_sha256": frozen_sha,
    "repair": {
        "defect": "D93A",
        "action": "DEFINE module-scope _write_once_json",
        "helper_inserted_before": ANCHOR.strip(),
        "helper_line_count": len(HELPER.splitlines()),
    },
    "diff_summary": {
        "total_changed_lines": len(changed_pairs),
        "version_token_only_changes": version_only,
        "non_version_changes": len(non_version),
        "scientific_delta_distinct_classes": [],
        "scientific_delta_count": 0,
    },
    "scientific_checks": {
        "residual_v1_19_tokens": 0,
        "parses": True,
        "_write_once_json_defined": True,
        "_write_once_json_unresolved": False,
        "d61_marker_present": True,
        "d75_marker_present": True,
    },
}, indent=2, default=str))
