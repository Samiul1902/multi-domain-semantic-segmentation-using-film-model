#!/usr/bin/env python
"""EXT-03 v1.2 checkpoint attestation verifier — FAIL-CLOSED.

Purpose
-------
Repair the defect in `ext03_sha256_manifest_v1_1.json` Section C, where all 15
checkpoint entries carried `registry_sha256 = null` yet reported `match = true`.

Root cause (measured, not inferred)
-----------------------------------
The v1.1 builder resolved the reference digest with

    exp = r.get("best_sha256") or r.get("checkpoint_sha256")

The registry's actual key is `checkpoint_sha`. Both lookups returned None, so
`exp` was None, and the comparison

    ok = (exp is None) or (actual == exp)

evaluated to True unconditionally. The attestation was vacuous: it would have
reported `match = true` for all 15 checkpoints even if every digest on disk were
wrong. This is the same fail-open shape the v1.0 generator was faulted for
(`if recorded and actual != recorded:`), reproduced in the repair tool.

Contract enforced here
----------------------
G1  Every run entry MUST carry a non-empty 64-character lowercase hex
    `checkpoint_sha`. Absent, empty, non-string or malformed => FAIL.
G2  There is NO fallback to an alternative key name. A registry that omits
    `checkpoint_sha` fails, even if some other key looks like a digest.
G3  `checkpoint_path` MUST resolve to an existing file => else FAIL.
G4  The reference digest MUST equal the raw-byte SHA-256 of the checkpoint
    (`Path(p).read_bytes()`) => else FAIL.
G5  The run set MUST be exactly the expected 15 runs => else FAIL.
G6  A missing digest is FAIL, never PASS. There is no code path in which an
    absent reference produces a passing comparison.

Exit codes
----------
0  every run attested
1  attestation failed (AttestAbort; `.code` names the defect)
2  usage / environment error
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

VERIFIER_VERSION = "1.2"

REGISTRY_REL = "reports/baselines/ext03_run_registry.json"

EXPECTED_ARCHS = ("unet", "attention_unet", "unetpp", "deeplabv3plus", "segformer_b0")
EXPECTED_SEEDS = (42, 123, 3407)
EXPECTED_RUNS = frozenset(f"{a}_seed{s}" for a in EXPECTED_ARCHS for s in EXPECTED_SEEDS)

HEX64 = re.compile(r"^[0-9a-f]{64}$")

# The single registry key this verifier accepts. Deliberately a tuple of one:
# adding an alias here would reintroduce the v1.1 fail-open.
CHECKPOINT_SHA_KEY = "checkpoint_sha"
CHECKPOINT_PATH_KEY = "checkpoint_path"


class AttestAbort(RuntimeError):
    """Fail-closed abort. `.code` is a stable machine-readable defect name."""

    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)


def raw_byte_sha256(path: Path) -> str:
    """SHA-256 over the file's raw bytes. No text decoding, no normalisation."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require_reference_sha(value, what: str) -> str:
    """Return a validated 64-hex digest, or abort. Never returns None."""
    if value is None:
        raise AttestAbort("E_REGISTRY_SHA_ABSENT", f"{what}: key absent (None)")
    if isinstance(value, str) and not value.strip():
        raise AttestAbort("E_REGISTRY_SHA_ABSENT", f"{what}: empty string")
    if not isinstance(value, str):
        raise AttestAbort("E_REGISTRY_SHA_MALFORMED", f"{what}: not a string ({type(value).__name__})")
    if not HEX64.match(value):
        raise AttestAbort(
            "E_REGISTRY_SHA_MALFORMED",
            f"{what}: not 64 lowercase hex chars (len={len(value)}, value={value[:24]!r})",
        )
    return value


def resolve_path(ckpt: str, repo_root: Path) -> Path:
    """Registry paths are Windows-style relative; normalise separators."""
    return Path(repo_root) / Path(str(ckpt).replace("\\", "/"))


def load_registry(path: Path) -> dict:
    if not Path(path).exists():
        raise AttestAbort("E_REGISTRY_ABSENT", str(path))
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AttestAbort("E_REGISTRY_UNREADABLE", str(exc)) from exc
    if not isinstance(data, dict):
        raise AttestAbort("E_REGISTRY_SHAPE", "top level is not an object")
    runs = data.get("runs")
    if not isinstance(runs, dict):
        raise AttestAbort("E_REGISTRY_SHAPE", "'runs' missing or not an object")
    return data


def verify(registry_path: Path, repo_root: Path, expected_runs=EXPECTED_RUNS) -> dict:
    """Attest every checkpoint. Raises AttestAbort on the first failure."""
    registry_path = Path(registry_path)
    repo_root = Path(repo_root)

    data = load_registry(registry_path)
    runs = data["runs"]

    # G5 — run-set identity, checked before any digest so a truncated registry
    # cannot silently attest fewer runs.
    present = frozenset(runs)
    missing = sorted(expected_runs - present)
    unexpected = sorted(present - expected_runs)
    if missing:
        raise AttestAbort("E_RUN_MISSING", f"{len(missing)} run(s): {missing}")
    if unexpected:
        raise AttestAbort("E_RUN_UNEXPECTED", f"{len(unexpected)} run(s): {unexpected}")

    entries = []
    for rid in sorted(runs):
        entry = runs[rid]
        if not isinstance(entry, dict):
            raise AttestAbort("E_RUN_SHAPE", f"{rid}: not an object")

        # G1/G2 — reference digest. No alias fallback.
        reference = require_reference_sha(entry.get(CHECKPOINT_SHA_KEY), f"{rid}.{CHECKPOINT_SHA_KEY}")

        # G3 — checkpoint presence.
        ckpt = entry.get(CHECKPOINT_PATH_KEY)
        if not isinstance(ckpt, str) or not ckpt.strip():
            raise AttestAbort("E_CHECKPOINT_PATH_ABSENT", f"{rid}.{CHECKPOINT_PATH_KEY}")
        ckpt_abs = resolve_path(ckpt, repo_root)
        if not ckpt_abs.exists():
            raise AttestAbort("E_CHECKPOINT_ABSENT", f"{rid}: {ckpt}")
        if not ckpt_abs.is_file():
            raise AttestAbort("E_CHECKPOINT_NOT_A_FILE", f"{rid}: {ckpt}")

        # G4 — digest equality. Fail-closed: both sides already known non-empty.
        actual = raw_byte_sha256(ckpt_abs)
        if actual != reference:
            raise AttestAbort(
                "E_CHECKPOINT_SHA_MISMATCH",
                f"{rid}: registry={reference} actual={actual}",
            )

        entries.append(
            {
                "run": rid,
                "architecture": entry.get("architecture"),
                "seed": entry.get("seed"),
                "status": entry.get("status"),
                "checkpoint_path": ckpt,
                "reference_sha256": reference,
                "actual_sha256": actual,
                "match": True,
                "bytes": ckpt_abs.stat().st_size,
            }
        )

    return {
        "verifier": "ext03_v1_2_checkpoint_attestation_verifier",
        "verifier_version": VERIFIER_VERSION,
        "registry_path": str(registry_path),
        "registry_sha256": raw_byte_sha256(registry_path),
        "reference_key": CHECKPOINT_SHA_KEY,
        "alias_fallback_permitted": False,
        "n_expected": len(expected_runs),
        "n_attested": len(entries),
        "all_match": True,
        "entries": entries,
    }


def self_test(repo_root: Path) -> int:
    """Negative controls. Each MUST abort with the named code."""
    import tempfile

    print("self-test: negative controls (every case must FAIL closed)")

    def build(tmp: Path, mutate) -> Path:
        ck = tmp / "ck.pt"
        ck.write_bytes(b"checkpoint-bytes")
        good = hashlib.sha256(b"checkpoint-bytes").hexdigest()
        runs = {}
        for rid in sorted(EXPECTED_RUNS):
            arch, seed = rid.rsplit("_seed", 1)
            runs[rid] = {
                "run_id": rid,
                "architecture": arch,
                "seed": int(seed),
                "status": "COMPLETE",
                CHECKPOINT_PATH_KEY: "ck.pt",
                CHECKPOINT_SHA_KEY: good,
            }
        mutate(runs, good)
        reg = tmp / "registry.json"
        reg.write_text(json.dumps({"runs": runs}), encoding="utf-8")
        return reg

    cases = []

    def case(name, mutate, expect):
        cases.append((name, mutate, expect))

    def _drop_one(runs, good):
        runs["unet_seed42"].pop(CHECKPOINT_SHA_KEY)

    def _null_all(runs, good):
        for r in runs.values():
            r[CHECKPOINT_SHA_KEY] = None

    def _empty_one(runs, good):
        runs["unet_seed42"][CHECKPOINT_SHA_KEY] = ""

    def _wrong_one(runs, good):
        runs["unet_seed42"][CHECKPOINT_SHA_KEY] = "0" * 64

    def _uppercase_one(runs, good):
        runs["unet_seed42"][CHECKPOINT_SHA_KEY] = good.upper()

    def _short_one(runs, good):
        runs["unet_seed42"][CHECKPOINT_SHA_KEY] = good[:63]

    def _int_one(runs, good):
        runs["unet_seed42"][CHECKPOINT_SHA_KEY] = 12345

    def _alias_key(runs, good):
        # THE v1.1 DEFECT: digest present under a different key name.
        for r in runs.values():
            r["best_sha256"] = r.pop(CHECKPOINT_SHA_KEY)

    def _missing_run(runs, good):
        runs.pop("unetpp_seed123")

    def _unexpected_run(runs, good):
        runs["mystery_seed42"] = dict(runs["unet_seed42"])

    def _absent_file(runs, good):
        for r in runs.values():
            r[CHECKPOINT_PATH_KEY] = "does_not_exist.pt"

    def _no_path_key(runs, good):
        for r in runs.values():
            r.pop(CHECKPOINT_PATH_KEY)

    case("reference_sha_absent", _drop_one, "E_REGISTRY_SHA_ABSENT")
    case("reference_sha_all_null", _null_all, "E_REGISTRY_SHA_ABSENT")
    case("reference_sha_empty_string", _empty_one, "E_REGISTRY_SHA_ABSENT")
    case("reference_sha_wrong_digest", _wrong_one, "E_CHECKPOINT_SHA_MISMATCH")
    case("reference_sha_uppercase", _uppercase_one, "E_REGISTRY_SHA_MALFORMED")
    case("reference_sha_short", _short_one, "E_REGISTRY_SHA_MALFORMED")
    case("reference_sha_not_a_string", _int_one, "E_REGISTRY_SHA_MALFORMED")
    case("v1_1_defect_alias_key", _alias_key, "E_REGISTRY_SHA_ABSENT")
    case("run_missing", _missing_run, "E_RUN_MISSING")
    case("run_unexpected", _unexpected_run, "E_RUN_UNEXPECTED")
    case("checkpoint_absent", _absent_file, "E_CHECKPOINT_ABSENT")
    case("checkpoint_path_absent", _no_path_key, "E_CHECKPOINT_PATH_ABSENT")

    passed = failed = 0
    for name, mutate, expect in cases:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            reg = build(tmp, mutate)
            try:
                verify(reg, tmp)
            except AttestAbort as exc:
                ok = exc.code == expect
                print(f"  {'PASS' if ok else 'FAIL'}  {name:30} got={exc.code:28} expected={expect}")
                passed += ok
                failed += (not ok)
            else:
                print(f"  FAIL  {name:30} got=<NO ABORT>  expected={expect}  <-- FAIL-OPEN")
                failed += 1

    # Positive control: an unmutated registry must attest.
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        reg = build(tmp, lambda runs, good: None)
        try:
            res = verify(reg, tmp)
            ok = res["all_match"] and res["n_attested"] == len(EXPECTED_RUNS)
            print(f"  {'PASS' if ok else 'FAIL'}  {'positive_control_all_valid':30} attested={res['n_attested']}")
            passed += ok
            failed += (not ok)
        except AttestAbort as exc:
            print(f"  FAIL  {'positive_control_all_valid':30} aborted={exc.code}")
            failed += 1

    total = passed + failed
    print(f"\n{passed}/{total} cases passed")
    return 0 if failed == 0 else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-root", default=".", help="repository root (default: cwd)")
    ap.add_argument("--registry", default=None, help=f"registry path (default: <repo>/{REGISTRY_REL})")
    ap.add_argument("--out", default=None, help="write attestation JSON here (write-once)")
    ap.add_argument("--verify-only", action="store_true", help="attest and print a summary; write nothing")
    ap.add_argument("--self-test", action="store_true", help="run negative controls")
    args = ap.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()

    if args.self_test:
        return self_test(repo_root)

    registry = Path(args.registry) if args.registry else repo_root / REGISTRY_REL

    try:
        result = verify(registry, repo_root)
    except AttestAbort as exc:
        print(f"ATTESTATION_FAILED {exc.code}", file=sys.stderr)
        if exc.detail:
            print(f"  {exc.detail}", file=sys.stderr)
        return 1

    print(f"ATTESTATION_OK  n={result['n_attested']}  registry_sha256={result['registry_sha256'][:16]}...")
    for e in result["entries"]:
        print(f"  MATCH  {e['run']:26} {e['reference_sha256'][:16]}...  {e['bytes']:>10,} B")

    if args.out and not args.verify_only:
        import os

        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(result, indent=2, ensure_ascii=False).encode("utf-8")
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        if hasattr(os, "O_BINARY"):
            flags |= os.O_BINARY
        try:
            fd = os.open(str(out), flags, 0o644)
        except FileExistsError:
            print(f"E_OUTPUT_EXISTS {out}", file=sys.stderr)
            return 1
        try:
            w = 0
            while w < len(payload):
                w += os.write(fd, payload[w:])
            os.fsync(fd)
        finally:
            os.close(fd)
        if out.stat().st_size != len(payload):
            print(f"E_WRITE_INCOMPLETE {out}", file=sys.stderr)
            return 1
        print(f"\nWROTE {out} ({len(payload)} B)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
