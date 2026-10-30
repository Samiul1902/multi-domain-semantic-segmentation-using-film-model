#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.11 — build the RUNTIME SOURCE INTEGRITY MANIFEST (READ-ONLY).

The v1.11 manifest declares the exact SHA-256 of the v1.11 execution source, the
14 load-bearing transitive dependencies and the 4 canonical checkpoints.  It is
the FAIL-CLOSED authority consulted by `_verify_transitive_source_integrity()`
on BOTH the smoke and the science paths, always BEFORE model construction.

NON-CIRCULAR: the manifest declares only the execution-source SHA (which the
external launcher independently verifies by exact value).  It does NOT declare
the launcher SHA; the launcher SHA is pinned EXTERNALLY by the supervisor and
bound by the v1.11 source freeze.

NO torch.  NO model.  NO checkpoint deserialization.  NO protected read.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXEC_V1_11 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_11.py"
V19_MANIFEST = ROOT / "reports/audits/phase36_v1_9_runtime_source_integrity_manifest.json"

FROZEN_V1_9_EXEC_SHA = "433bad87b4ef77fd6997c77f688eb295e526bfa3e88dece4ec5d3d550255cbd0"
FROZEN_V1_8_EXEC_SHA = "c95ff9884ec05a859b39ce7976376bf40e4543b1a8d8a19830e5893120039f4d"
FROZEN_V1_7_EXEC_SHA = "87062d2b38232c73b8ce620d7bfafb389658c4b877d9196a26b8b01d09daf192"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    v19 = json.loads(V19_MANIFEST.read_text(encoding="utf-8"))
    deps = dict(v19["dependencies"])
    ckpts = dict(v19["checkpoints"])

    # Re-verify each dependency/checkpoint ACTUALLY present on disk matches the
    # frozen v1.9 expectation (integrity of the frozen inputs).
    dep_ver = {}
    for rel, expected in deps.items():
        p = ROOT / rel
        obs = sha(p) if p.exists() else "FILE_MISSING"
        dep_ver[rel] = {"expected": expected, "observed": obs, "match": obs == expected}
    ckpt_ver = {}
    for rel, expected in ckpts.items():
        p = ROOT / rel
        obs = sha(p) if p.exists() else "FILE_MISSING"
        ckpt_ver[rel] = {"expected": expected, "observed": obs, "match": obs == expected}

    exec_sha = sha(EXEC_V1_11)

    manifest = {
        "artifact": "phase36_v1_11_runtime_source_integrity_manifest",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_11",
        "type": "RUNTIME_SOURCE_INTEGRITY_MANIFEST",
        "execution_source": "scripts/analysis/phase36_robustness_execution_v1_11.py",
        "execution_source_sha256": exec_sha,
        "history_preserved_sha256": {
            "v1_9_execution": FROZEN_V1_9_EXEC_SHA,
            "v1_8_execution": FROZEN_V1_8_EXEC_SHA,
            "v1_7_execution": FROZEN_V1_7_EXEC_SHA,
        },
        "dependencies": deps,
        "checkpoints": ckpts,
        "n_dependencies": len(deps),
        "n_checkpoints": len(ckpts),
        "dependency_verification": dep_ver,
        "checkpoint_verification": ckpt_ver,
        "all_dependencies_match": all(v["match"] for v in dep_ver.values()),
        "all_checkpoints_match": all(v["match"] for v in ckpt_ver.values()),
        "gate_position": "BEFORE_MODEL_CONSTRUCTION__BEFORE_torch.load",
        "fail_closed_semantics": (
            "MANIFEST_NOT_FOUND / MALFORMED / MISSING_EXECUTION_SOURCE_SHA256 / "
            "ANY_DEP_OR_CKPT_MISMATCH / LATEST_LAUNCH_AUTHORITY_TOKEN_ABSENT "
            "-> all_match=false -> STOP before model construction"),
        "self_hash_pattern": "execution_source_sha256 is the source's own SHA; the "
                             "external launcher independently verifies it.",
        "verified_by": "external_launcher_launch_phase36_v1_11.py",
    }
    out = ROOT / "reports/audits/phase36_v1_11_runtime_source_integrity_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "execution_source_sha256": exec_sha,
        "n_dependencies": len(deps),
        "n_checkpoints": len(ckpts),
        "all_dependencies_match": manifest["all_dependencies_match"],
        "all_checkpoints_match": manifest["all_checkpoints_match"],
        "manifest_sha256": sha(out),
    }, indent=1))
    ok = manifest["all_dependencies_match"] and manifest["all_checkpoints_match"]
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    raise SystemExit(main())
