#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.9 — build the RUNTIME SOURCE INTEGRITY MANIFEST (READ-ONLY source).

Extracts TRANSITIVE_RUNTIME_DEPENDENCIES + TRANSITIVE_RUNTIME_CHECKPOINTS from
the FINAL v1.9 execution source, verifies each against the on-disk bytes, and
writes the external non-circular manifest carrying the FINAL execution SHA-256.

NO torch.  NO model.  NO protected-population read.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_9.py"
SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def getconst(name):
    for n in ast.walk(TREE):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if getattr(t, "id", None) == name:
                    return ast.literal_eval(n.value)
    return None


deps = getconst("TRANSITIVE_RUNTIME_DEPENDENCIES") or {}
ckpt = getconst("TRANSITIVE_RUNTIME_CHECKPOINTS") or {}

dep_verification = {}
dep_all_ok = True
for rel, expected in deps.items():
    p = ROOT / rel
    observed = sha(p) if p.exists() else "FILE_MISSING"
    ok = observed == expected
    dep_all_ok = dep_all_ok and ok
    dep_verification[rel] = {"expected": expected, "observed": observed, "match": ok}

ckpt_verification = {}
ckpt_all_ok = True
for rel, expected in ckpt.items():
    p = ROOT / rel
    observed = sha(p) if p.exists() else "FILE_MISSING"
    ok = observed == expected
    ckpt_all_ok = ckpt_all_ok and ok
    ckpt_verification[rel] = {"expected": expected, "observed": observed, "match": ok}

manifest = {
    "artifact": "phase36_v1_9_runtime_source_integrity_manifest",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_9",
    "type": "RUNTIME_SOURCE_INTEGRITY_MANIFEST",
    "execution_source": "scripts/analysis/phase36_robustness_execution_v1_9.py",
    "execution_source_sha256": sha(EXEC),
    "self_hash_pattern": "EXTERNAL_MANIFEST_RESOLVED_AT_RUNTIME__NO_CIRCULAR_SELF_HASH",
    "history_preserved_sha256": {
        "v1_8_execution": "c95ff9884ec05a859b39ce7976376bf40e4543b1a8d8a19830e5893120039f4d",
        "v1_8_direct_byte_audit": "97687c2e2d77db0b94518e873378d29cf8d9de1413449c85684f68d42dfe1491",
        "v1_8_source_freeze": "c9439a0176100391ac88048c7c6e11b16e12756463833d0eb6dd0c46ca518fec",
        "v1_7_execution": "87062d2b38232c73b8ce620d7bfafb389658c4b877d9196a26b8b01d09daf192",
    },
    "verified_by": "_verify_transitive_source_integrity() called BEFORE model construction",
    "gate_position": "PRE_MODEL_CONSTRUCTION__FAIL_CLOSED_ON_MISMATCH",
    "fail_closed_semantics": {
        "missing_manifest": "FAIL",
        "malformed_manifest": "FAIL",
        "missing_execution_source_sha256_field": "FAIL",
        "any_dependency_mismatch": "FAIL",
        "any_checkpoint_mismatch": "FAIL",
        "self_hash_mismatch": "FAIL",
        "self_check_skipped_bypass": "REMOVED_IN_V1_9",
    },
    "n_dependencies": len(deps),
    "n_checkpoints": len(ckpt),
    "dependencies": {k: v for k, v in deps.items()},
    "checkpoints": {k: v for k, v in ckpt.items()},
    "dependency_verification": dep_verification,
    "checkpoint_verification": ckpt_verification,
    "all_dependencies_match": dep_all_ok,
    "all_checkpoints_match": ckpt_all_ok,
}
out = ROOT / "reports/audits/phase36_v1_9_runtime_source_integrity_manifest.json"
out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({
    "execution_source_sha256": manifest["execution_source_sha256"],
    "n_dependencies": len(deps),
    "n_checkpoints": len(ckpt),
    "all_dependencies_match": dep_all_ok,
    "all_checkpoints_match": ckpt_all_ok,
}, indent=1))
raise SystemExit(0 if (dep_all_ok and ckpt_all_ok) else 1)
