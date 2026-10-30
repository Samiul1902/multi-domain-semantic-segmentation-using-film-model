#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.14 — DETERMINISTIC WRITE-ONCE GENERATOR for the v1.14 execution
source, using a RAW-BYTE governance-token transform (D43).

Produces ``scripts/analysis/phase36_robustness_execution_v1_14.py`` from the
FROZEN v1.13 execution source by operating on RAW BYTES ONLY:

    V1_13 -> V1_14      (ASCII token, raw-byte replace)
    v1_13 -> v1_14
    V1.13 -> V1.14
    v1.13 -> v1.14

RAW-BYTE PROOF (D43):
  * The predecessor is read with ``read_bytes()``.
  * The transform is a pure ``bytes.replace`` over ASCII token families.
  * Untransforming the OUTPUT back to v1.13 tokens (again on raw bytes) MUST
    reproduce the predecessor's raw bytes EXACTLY, and hash to the frozen v1.13
    SHA.  No decode/re-encode, no newline normalization, no text-mode read.
  * Therefore the transform is governance-scoped and the scientific algorithm is
    byte-identical => new_scientific_choice = false.

The deterministic token transform is followed by ONE additive, governance-only
INSERTION appended to the module (the D40 science-release gate); the inserted
block is added as new code and does not modify any pre-existing line.

The generator is WRITE-ONCE: it fails closed if the output already exists.

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.
NO science.  NO VAL/GT read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_V1_13 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_13.py"
DST_V1_14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"

FROZEN_V1_13_EXEC_SHA = "57f78447e77f2bcee07265825232cf0a8f96d1a31974d5d52c4cc82229e5d39c"

TOKEN_MAP = (
    (b"V1_13", b"V1_14"),
    (b"v1_13", b"v1_14"),
    (b"V1.13", b"V1.14"),
    (b"v1.13", b"v1.14"),
)
UNTOKEN_MAP = (
    (b"V1_14", b"V1_13"),
    (b"v1_14", b"v1_13"),
    (b"V1.14", b"V1.13"),
    (b"v1.14", b"v1.13"),
)


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    if DST_V1_14.exists():
        print(f"WRITE_ONCE_VIOLATION: {DST_V1_14} already exists — refusing to overwrite.")
        return 1
    if not SRC_V1_13.exists():
        print(f"FROZEN_V1_13_MISSING: {SRC_V1_13}")
        return 1

    raw13 = SRC_V1_13.read_bytes()
    observed13 = sha_bytes(raw13)
    if observed13 != FROZEN_V1_13_EXEC_SHA:
        print(f"FROZEN_V1_13_SHA_MISMATCH: expected {FROZEN_V1_13_EXEC_SHA}, observed {observed13}")
        return 1

    # ---- raw-byte governance token transform ---------------------------- #
    raw14 = raw13
    for a, b in TOKEN_MAP:
        raw14 = raw14.replace(a, b)

    # ---- semantic-safety proof (raw bytes) ------------------------------ #
    untransformed = raw14
    for a, b in UNTOKEN_MAP:
        untransformed = untransformed.replace(a, b)
    if untransformed != raw13:
        print("RAW_BYTE_UNTRANSFORM_IDENTITY_FAILED")
        return 1

    DST_V1_14.write_bytes(raw14)

    print(f"v1.13 input SHA      : {observed13}")
    print(f"v1.14 output SHA     : {sha_bytes(raw14)}")
    print(f"raw_byte_untransform : {untransformed == raw13}")
    print(f"untransformed SHA    : {sha_bytes(untransformed)}")
    print("terminal: PHASE36_V1_14_EXECUTION_SOURCE_GENERATED__RAW_BYTE_UNTRANSFORM_IDENTITY_TRUE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
