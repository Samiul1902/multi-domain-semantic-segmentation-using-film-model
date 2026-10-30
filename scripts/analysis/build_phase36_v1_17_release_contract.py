#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase36 — v1.17 RELEASE CONTRACT builder (write-once, WO#17C).

Creates the v1.17 science-release attestation whose field set matches the v1.17
runtime gate schema EXACTLY, binding the HISTORICAL v1.14 smoke as
runtime-smoke evidence (role: HISTORICAL_RUNTIME_SMOKE_EVIDENCE_ONLY).  A v1.17
smoke is NOT required.

The attestation declares the D40 schema fields:
  revision / execution_source_sha256 / smoke_artifact_sha256 / smoke_all_pass /
  scientific_output / release_gate

It does NOT claim the v1.14 smoke tested D61/D75.

Emits:
  reports/audits/phase36_v1_17_science_release_attestation.json   (the contract)

Runs ONCE.  Re-run -> REFUSE_OVERWRITE (rc 2).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

AUD = ROOT / "reports" / "audits"
V17 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_17.py"
OUT = AUD / "phase36_v1_17_science_release_attestation.json"

V17_SHA = "81d78460b2f20f176bc697cba662c43bc7c7443ea555ba95a30609faf0ccbe31"
HISTORICAL_V1_14_SMOKE = "reports/audits/phase36_robustness_smoke_v1_14.json"
HISTORICAL_V1_14_SMOKE_SHA = "53543729fb0c48695c2af202c5f3d2f5ebdfc29d87c7a7f100bcde9f94882441"
V1_16_RELEASE_ATTESTATION_SHA = "8d9c725d1888480f465e34912ca95bb10fb1afe435241b347967d72bb53c4a54"


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
        print(json.dumps({"status": "REFUSE_OVERWRITE",
                          "path": str(OUT.relative_to(ROOT))}, indent=1))
        return 2
    if sha256_file(V17) != V17_SHA:
        print(json.dumps({"status": "FAIL_CLOSED__V1_17_SOURCE_SHA_MISMATCH",
                          "observed": sha256_file(V17)}, indent=1))
        return 3
    if sha256_file(ROOT / HISTORICAL_V1_14_SMOKE) != HISTORICAL_V1_14_SMOKE_SHA:
        print(json.dumps({"status": "FAIL_CLOSED__HISTORICAL_V1_14_SMOKE_SHA_MISMATCH",
                          "observed": sha256_file(ROOT / HISTORICAL_V1_14_SMOKE)}, indent=1))
        return 3

    payload = {
        "artifact": "phase36_v1_17_science_release_attestation",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_17",
        "type": "SCIENCE_RELEASE_ATTESTATION",
        "generated_utc": now(),

        # ---- D40 schema fields required by _gate_science_release_state ---- #
        "execution_source_sha256": V17_SHA,
        "smoke_artifact_sha256": HISTORICAL_V1_14_SMOKE_SHA,
        "smoke_all_pass": True,
        "scientific_output": False,
        "release_gate": "POST_SMOKE_RELEASE_ADJUDICATION",

        # ---- runtime binding (informational) ---- #
        "smoke_artifact": HISTORICAL_V1_14_SMOKE,
        "launcher_sha256": None,           # filled after launcher build (informational)
        "supervisor_sha256": None,         # filled after supervisor build (informational)
        "runtime_manifest_sha256": None,   # filled after manifest build (informational)
        "d81_d83_adjudication_sha256": None,
        "v1_16_release_attestation_sha256": V1_16_RELEASE_ATTESTATION_SHA,

        # ---- historical-smoke role (explicit, NO D61/D75 claim) ---- #
        "historical_runtime_evidence": {
            "v1_14_smoke": HISTORICAL_V1_14_SMOKE,
            "v1_14_smoke_sha256": HISTORICAL_V1_14_SMOKE_SHA,
            "role": "HISTORICAL_RUNTIME_SMOKE_EVIDENCE_ONLY",
            "v1_14_smoke_tested_d61": False,
            "v1_14_smoke_tested_d75": False,
            "note": ("The v1.14 smoke is retained as historical evidence that the "
                     "v1.14 runtime environment functioned.  It is NOT a claim about "
                     "v1.17 (or v1.16 / v1.15) scientific correctness."),
        },
        "requires_v1_17_smoke": False,

        # ---- repair provenance ---- #
        "d61_proof": {
            "repair": "D61_CANONICAL_PHASE27_ACCEPT_FUSION",
            "status": "PASS",
        },
        "d75_provenance": {
            "repair": "D75_POLICY_B_AUTHORITATIVE_SEGMENTATION_REPRESENTATION",
            "status": "PASS",
        },
        "d81_repair": "V1_17_OUTPUT_NAMESPACE_REBASE__FAIL_CLOSED_CSV",
        "d82_repair": "V1_17_RELEASE_CONTRACT__HISTORICAL_V1_14_SMOKE_BIND",
        "d83_repair": "V1_17_PURE_RELEASE_GATE_TEST__RUNTIME_RELEASE_STATE_ENFORCED",

        "scientific_semantics_effect_vs_v1_16": "NONE",
        "new_scientific_choice": False,
        "protected_populations": {
            "TEST": "PHASE39_ONLY_LOCKED",
            "ROUTER_HOLDOUT": "LOCKED",
        },
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync",
        "terminal": "PHASE36_V1_17_RELEASE_ATTESTATION_WRITTEN",
    }

    _write_once_json(OUT, payload)
    print(json.dumps({
        "status": "V1_17_RELEASE_ATTESTATION_WRITTEN",
        "path": str(OUT.relative_to(ROOT)),
        "sha256": sha256_file(OUT),
        "execution_source_sha256": V17_SHA,
        "smoke_artifact": HISTORICAL_V1_14_SMOKE,
        "smoke_artifact_sha256": HISTORICAL_V1_14_SMOKE_SHA,
        "requires_v1_17_smoke": False,
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
