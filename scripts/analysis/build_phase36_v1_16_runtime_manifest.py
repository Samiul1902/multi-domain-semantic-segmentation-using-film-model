#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase36 — v1.16 RUNTIME SOURCE-INTEGRITY MANIFEST BUILDER (write-once, WO#17B).

D80-E repair: creates a NEW non-circular runtime integrity authority whose
``execution_source_sha256`` is the EXACT frozen v1.16 execution SHA.  The 14
runtime dependency hashes + 4 checkpoint hashes are carried UNCHANGED from the
v1.14 manifest ONLY after RAW-BYTE verification proves they still match.

Non-circular chain (documented):
  SUPERVISOR pins launcher SHA before dispatch
    -> LAUNCHER pins literal v1.16 execution SHA + this manifest SHA + governance
      -> EXECUTION SOURCE reads this manifest, verifies its own bytes against
         ``execution_source_sha256``, and requires the launch-authority token
  The manifest NEVER declares a launcher SHA (no cycle).

Re-run -> REFUSE_OVERWRITE (rc 2).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / "reports" / "audits"
V14_MANIFEST = AUD / "phase36_v1_14_runtime_source_integrity_manifest.json"
V16_EXEC = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_16.py"
OUT = AUD / "phase36_v1_16_runtime_source_integrity_manifest.json"

EXPECTED_V16_EXEC_SHA = None  # set at runtime (derived from the file)


def sha256_file(p: Path) -> str | None:
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_once_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=1, ensure_ascii=False, default=str).encode("utf-8")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        total = 0
        while total < len(data):
            n = os.write(fd, data[total:])
            if n is None or n <= 0:
                raise OSError(f"SHORT_WRITE at {total}/{len(data)} for {path}")
            total += n
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(data):
        raise OSError(f"POST_WRITE_SIZE_MISMATCH for {path}")


def main() -> int:
    if OUT.exists():
        print(json.dumps({"status": "REFUSE_OVERWRITE", "path": str(OUT.relative_to(ROOT))}, indent=1))
        return 2

    v14 = json.loads(V14_MANIFEST.read_text(encoding="utf-8"))
    v16_exec_sha = sha256_file(V16_EXEC)

    # Re-verify (raw-byte) every dependency + checkpoint; carry ONLY if unchanged.
    dep_ver = {}
    dep_all = True
    for rel, entry in v14["dependency_verification"].items():
        exp = entry["expected"] if isinstance(entry, dict) else entry
        obs = sha256_file(ROOT / rel)
        m = obs == exp
        dep_all = dep_all and m
        dep_ver[rel] = {"expected": exp, "observed": obs, "match": m}
    ck_ver = {}
    ck_all = True
    for rel, entry in v14["checkpoint_verification"].items():
        exp = entry["expected"] if isinstance(entry, dict) else entry
        obs = sha256_file(ROOT / rel)
        m = obs == exp
        ck_all = ck_all and m
        ck_ver[rel] = {"expected": exp, "observed": obs, "match": m}

    if not (dep_all and ck_all):
        print(json.dumps({"status": "FAIL_CLOSED__DEP_OR_CKPT_DRIFT",
                          "dependencies_all_match": dep_all,
                          "checkpoints_all_match": ck_all,
                          "dep_mismatch": [k for k, v in dep_ver.items() if not v["match"]],
                          "ckpt_mismatch": [k for k, v in ck_ver.items() if not v["match"]]}, indent=1))
        return 3

    payload = {
        "artifact": "phase36_v1_16_runtime_source_integrity_manifest",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_16",
        "type": "RUNTIME_SOURCE_INTEGRITY_MANIFEST",
        "execution_source": "scripts/analysis/phase36_robustness_execution_v1_16.py",
        "execution_source_sha256": v16_exec_sha,
        "dependencies": v14["dependencies"],
        "checkpoints": v14["checkpoints"],
        "n_dependencies": v14["n_dependencies"],
        "n_checkpoints": v14["n_checkpoints"],
        "dependency_verification": dep_ver,
        "checkpoint_verification": ck_ver,
        "all_dependencies_match": dep_all,
        "all_checkpoints_match": ck_all,
        "carried_from_v1_14": True,
        "carried_from_v1_14_manifest_sha256": sha256_file(V14_MANIFEST),
        "dependencies_unchanged_by_raw_byte_verification": True,
        "checkpoints_unchanged_by_raw_byte_verification": True,
        "gate_position": "PRE_MODEL_CONSTRUCTION__BEFORE_ANY_torch_load",
        "fail_closed_semantics": True,
        "launcher_sha256_absent_by_design": True,
        "launcher_sha256_absent_reason": (
            "NON_CIRCULAR_ARCHITECTURE: the launcher pins this manifest + the exact "
            "execution SHA; the manifest never declares a launcher SHA (no cycle). "
            "The source FAILS CLOSED if launcher_sha256 unexpectedly appears."),
        "non_circular_chain": [
            "SUPERVISOR pins frozen v1.16 launcher SHA before dispatch",
            "LAUNCHER pins literal v1.16 execution SHA + this manifest SHA + governance artifacts",
            "EXECUTION SOURCE reads this manifest, verifies its own bytes vs execution_source_sha256",
            "EXECUTION SOURCE requires the launch-authority token PHASE36_V1_16_LAUNCH_AUTHORITY",
        ],
        "generated_utc": now(),
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync",
    }
    _write_once_json(OUT, payload)
    print(json.dumps({
        "status": "V1_16_MANIFEST_WRITTEN",
        "path": str(OUT.relative_to(ROOT)),
        "sha256": sha256_file(OUT),
        "execution_source_sha256": v16_exec_sha,
        "all_dependencies_match": dep_all,
        "all_checkpoints_match": ck_all,
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
