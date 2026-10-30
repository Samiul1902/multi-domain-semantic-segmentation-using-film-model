#!/usr/bin/env python
"""BUILD the v1.23 EXECUTION SOURCE from FROZEN v1.22 (write-once).

MODE: NEW-REVISION PREPARATION ONLY.  NON-CONSUMING.

Creates EXACTLY ONE new artifact:

    scripts/analysis/phase36_robustness_execution_v1_23.py

It does NOT modify the frozen v1.22 source (SHA 29d29da8...).  v1.22 is
CONSUMED (D97 Stage-5 summary runtime defect); v1.23 is a NEW revision
built additively.

TRANSFORMATION
--------------
1. Mechanical version-token rebase (v1.22 -> v1.23) of the frozen v1.22
   bytes -- the same class of change applied at every prior revision.
2. D97 REPAIR (reporting/runtime ONLY; scientific delta = 0):
     * Bind the two frozen v1.0 REPORTING flags that the v1.1 additive
       common layer failed to re-export as LOCAL module-level frozen
       constants with provenance:
         BEST_SEED_SELECTION = False   (common_v1_0.py:282)
         KUB_REPORTING_ONLY   = True   (common_v1_0.py:78)
     * Repair the two call sites:
         "best_seed_selection": bool(C.BEST_SEED_SELECTION)
             -> "best_seed_selection": bool(BEST_SEED_SELECTION)
         if not C.KUB_REPORTING_ONLY:
             -> if not KUB_REPORTING_ONLY:
   The frozen common_v1_1 module is NOT mutated.  No seed computation,
   averaging, selection or aggregation semantics change.

PROOF
-----
ROUND-TRIP: undoing the rebase and the D97 repair on the v1.23 bytes
reproduces the frozen v1.22 bytes EXACTLY.  Any non-rebase / non-D97
change -> FAIL CLOSED.  The repaired source must ALSO pass the COMPLETE
C.<attribute> resolution audit against phase36_robustness_common_v1_1
(zero missing symbols).
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")

SRC_V122 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_22.py"
OUT_V123 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_23.py"
COMMON_V11 = ROOT / "scripts" / "analysis" / "phase36_robustness_common_v1_1.py"

FROZEN_V122_SHA = "29d29da8a9514db464f2db45f06a1ccaabf65aa302c18cd53bbb7419e2fbbd2b"

D97_HEADER_ANCHOR = (
    "DEFECTS REPAIRED IN V1.23 (proven from the frozen v1.11 bytes)"
)
D97_CONST_ANCHOR = (
    "import scripts.analysis.phase36_robustness_common_v1_1 as C  # noqa: E402\n"
)

OLD_BEST = '"best_seed_selection": bool(C.BEST_SEED_SELECTION)'
NEW_BEST = '"best_seed_selection": bool(BEST_SEED_SELECTION)'
OLD_KUB = "    if not C.KUB_REPORTING_ONLY:"
NEW_KUB = "    if not KUB_REPORTING_ONLY:"

D97_HEADER_BLOCK = """# =========================================================================== #
# DEFECT REPAIRED IN V1.23 (D97 -- Stage-5 summary name-resolution defect)  #
# =========================================================================== #
#   D97_V1_22_SUMMARY_REFERENCES_UNDEFINED_COMMON_BEST_SEED_SELECTION
#       The v1.22 execution source (SHA 29d29da8...) referenced
#       C.BEST_SEED_SELECTION and C.KUB_REPORTING_ONLY, where
#       C = scripts.analysis.phase36_robustness_common_v1_1.  The v1.1
#       additive common layer re-exports the frozen v1.0 contract surface
#       but did NOT re-export these two frozen v1.0 REPORTING flags, so the
#       single consumed v1.22 attempt failed at Stage 5 (summarize_noise_seed,
#       AFTER canonical G generation, the Phase27 G reproduction gate, clean
#       system evaluation, the clean-equivalence gate and the complete
#       image/proposal perturbation execution) with:
#         AttributeError: module 'scripts.analysis.phase36_robustness_common_v1_1'
#         has no attribute 'BEST_SEED_SELECTION'
#       CLASSIFICATION: POST_PERTURBATION__STAGE5_SUMMARY_RUNTIME_DEFECT
#       (late reporting/runtime defect; NOT a scientific model failure).
#       AUTHORITY: scripts/analysis/phase36_robustness_common_v1_0.py
#         line 282:  BEST_SEED_SELECTION = False
#         line 78:   KUB_REPORTING_ONLY = True
#       v1.23 binds BOTH flags as LOCAL module-level frozen reporting
#       constants (values identical to the frozen v1.0 contract) and repairs
#       the two call sites.  The frozen common_v1_1 module is NOT mutated.
#       SCIENTIFIC DELTA v1.22 -> v1.23 = 0 (reporting/runtime repair only).
"""

D97_CONST_BLOCK = """
# =========================================================================== #
# D97 (v1.23): FROZEN REPORTING CONSTANTS -- LOCAL BINDING, PROVENANCE-     #
# BOUND.  The frozen v1.0 contract (phase36_robustness_common_v1_0.py)      #
# declares BOTH flags; the v1.1 additive common layer                       #
# (phase36_robustness_common_v1_1.py) re-exports the frozen v1.0 surface    #
# but does NOT re-export these two flags.  The v1.22 execution source       #
# referenced them as C.BEST_SEED_SELECTION / C.KUB_REPORTING_ONLY and       #
# failed at Stage 5 (D97).  v1.23 binds them HERE as local frozen           #
# constants with values IDENTICAL to the frozen v1.0 contract.  The frozen  #
# common_v1_1 module is NOT mutated.  No seed computation, averaging,       #
# selection or aggregation semantics change.                                #
#                                                                           #
# PROVENANCE (frozen v1.0 contract raw bytes):                              #
#   phase36_robustness_common_v1_0.py:282  BEST_SEED_SELECTION = False      #
#     The frozen experiment uses ALL prescribed Gaussian-noise base seeds   #
#     (NOISE_BASE_SEEDS = [42, 123, 3407]) and summarizes across seeds     #
#     (mean_across_seeds_of_sample_means).  It NEVER outcome-selects a      #
#     best seed (NO_OUTCOME_DEPENDENT_REPLACEMENT = True).                  #
#   phase36_robustness_common_v1_0.py:78   KUB_REPORTING_ONLY = True        #
#     KUB subgroup robustness is REPORTING ONLY: never classes, never       #
#     task ids, never model inputs (KUB_SUBGROUP_AUTHORITY below).          #
BEST_SEED_SELECTION = False
KUB_REPORTING_ONLY = True
"""


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
    return sha(Path(p).read_bytes())


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
    s = s.replace("v1.22", "v1.23")
    s = s.replace("V1.22", "V1.23")
    s = s.replace("v1_22", "v1_23")
    s = s.replace("V1_22", "V1_23")
    return s


def unbase(s: str) -> str:
    s = s.replace("v1.23", "v1.22")
    s = s.replace("V1.23", "V1.22")
    s = s.replace("v1_23", "v1_22")
    s = s.replace("V1_23", "V1_22")
    return s


# ---- sanity: frozen v1.22 input unchanged -------------------------------- #
assert sha_file(SRC_V122) == FROZEN_V122_SHA, "frozen v1.22 exec SHA drift"
assert not OUT_V123.exists(), "v1.23 execution source already exists"

src = SRC_V122.read_text(encoding="utf-8")

# ---- 1) mechanical rebase ------------------------------------------------ #
t = rebase(src)

# ---- 2) D97 header block ------------------------------------------------- #
assert D97_HEADER_ANCHOR in t, "D97 header anchor missing"
assert t.count(D97_HEADER_ANCHOR) == 1, "D97 header anchor not unique"
t = t.replace(D97_HEADER_ANCHOR, D97_HEADER_BLOCK + D97_HEADER_ANCHOR)

# ---- 3) D97 local frozen constants --------------------------------------- #
assert D97_CONST_ANCHOR in t, "D97 constant anchor missing"
assert t.count(D97_CONST_ANCHOR) == 1, "D97 constant anchor not unique"
t = t.replace(D97_CONST_ANCHOR, D97_CONST_ANCHOR + D97_CONST_BLOCK)

# ---- 4) D97 call-site repairs -------------------------------------------- #
assert t.count(OLD_BEST) == 1, "D97 BEST_SEED call site not unique"
t = t.replace(OLD_BEST, NEW_BEST)
assert t.count(OLD_KUB) == 1, "D97 KUB_REPORTING call site not unique"
t = t.replace(OLD_KUB, NEW_KUB)

# ---- post-conditions (AST-based: no CODE may access the stale attrs) -- #
_tree0 = ast.parse(t)
_stale = sorted({n.attr for n in ast.walk(_tree0)
                 if isinstance(n, ast.Attribute)
                 and isinstance(n.value, ast.Name) and n.value.id == "C"
                 and n.attr in ("BEST_SEED_SELECTION", "KUB_REPORTING_ONLY")})
assert not _stale, f"D97: stale C.<attr> ACCESS remains: {_stale}"
assert "BEST_SEED_SELECTION = False" in t
assert "KUB_REPORTING_ONLY = True" in t

# ---- ROUND-TRIP PROOF: strip D97, undo rebase == frozen v1.22 bytes -- #
back = t
assert (D97_HEADER_BLOCK + D97_HEADER_ANCHOR) in back
back = back.replace(D97_HEADER_BLOCK + D97_HEADER_ANCHOR,
                    D97_HEADER_ANCHOR)
assert (D97_CONST_ANCHOR + D97_CONST_BLOCK) in back
back = back.replace(D97_CONST_ANCHOR + D97_CONST_BLOCK, D97_CONST_ANCHOR)
assert back.count(NEW_BEST) == 1
back = back.replace(NEW_BEST, OLD_BEST)
assert back.count(NEW_KUB) == 1
back = back.replace(NEW_KUB, OLD_KUB)
back = unbase(back)
if back != src:
    print("FAIL_CLOSED: round-trip mismatch (non-rebase/non-D97 change)",
          file=sys.stderr)
    import difflib
    for i, (a, b) in enumerate(zip(back.splitlines(), src.splitlines()), 1):
        if a != b:
            print(f"  line {i}:\n    got: {a!r}\n    want: {b!r}",
                  file=sys.stderr)
    sys.exit(3)

# ---- COMPLETE C.<attribute> resolution audit against common_v1_1 --------- #
tree = ast.parse(t)
c_attrs = sorted({n.attr for n in ast.walk(tree)
                  if isinstance(n, ast.Attribute)
                  and isinstance(n.value, ast.Name) and n.value.id == "C"})
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("p36_common_v1_1_audit",
                                              COMMON_V11)
common = importlib.util.module_from_spec(spec)
sys.modules["p36_common_v1_1_audit"] = common
spec.loader.exec_module(common)
exported = {k for k in vars(common) if not k.startswith("__")}
missing = [a for a in c_attrs if a not in exported]
if missing:
    print("FAIL_CLOSED: v1.23 C.<attribute> resolution audit FAILED:",
          missing, file=sys.stderr)
    sys.exit(3)

# ---- the local D97 constants must equal the frozen v1.0 contract values -- #
spec0 = importlib.util.spec_from_file_location("p36_common_v1_0_audit",
                                               ROOT / "scripts" / "analysis"
                                               / "phase36_robustness_common_v1_0.py")
common0 = importlib.util.module_from_spec(spec0)
sys.modules["p36_common_v1_0_audit"] = common0
spec0.loader.exec_module(common0)
assert common0.BEST_SEED_SELECTION is False, "frozen v1.0 BEST_SEED_SELECTION drift"
assert common0.KUB_REPORTING_ONLY is True, "frozen v1.0 KUB_REPORTING_ONLY drift"
sys.path.pop(0)

out_sha = write_once(OUT_V123, t.encode("utf-8"))
print(json.dumps({
    "built": str(OUT_V123.relative_to(ROOT)),
    "sha256": out_sha,
    "frozen_v1_22_sha256": FROZEN_V122_SHA,
    "round_trip_proof": "undo(rebase)+undo(D97) == frozen v1.22 bytes EXACTLY",
    "d97_repair": {
        "local_constants_bound": ["BEST_SEED_SELECTION = False",
                                  "KUB_REPORTING_ONLY = True"],
        "call_sites_repaired": 2,
        "common_v1_1_mutated": False,
        "scientific_delta": 0,
        "provenance": {
            "BEST_SEED_SELECTION": "phase36_robustness_common_v1_0.py:282",
            "KUB_REPORTING_ONLY": "phase36_robustness_common_v1_0.py:78",
        },
    },
    "c_attribute_audit": {
        "referenced": c_attrs,
        "n_referenced": len(c_attrs),
        "n_exported_by_common_v1_1": len(exported),
        "missing": [],
        "pass": True,
    },
    "terminal": "PHASE36_V1_23_EXECUTION_SOURCE_BUILT",
}, indent=1))
