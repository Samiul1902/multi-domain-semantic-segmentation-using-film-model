#!/usr/bin/env python
"""EXT-03 v1.2 manifest builder — FAIL-CLOSED, write-once.

Emits `reports/audits/ext03_disposition_v1_2/ext03_sha256_manifest_v1_2.json`.

Design rules enforced here
--------------------------
R1  Every artifact the manifest references MUST exist on disk. A reference to a
    missing file aborts the build (E_REFERENCED_ABSENT). The manifest never
    records a hash for a file it could not read.
R2  Registry checkpoint digests are read from the single key `checkpoint_sha`.
    There is NO alias fallback. Absent, empty, non-string or malformed => abort.
R3  Every v1.0 / v1.1 artifact is re-hashed now and compared to the value
    recorded in the prior manifest. Any drift aborts (E_SHA_MISMATCH).
    This is the PRE == POST guarantee.
R4  Both outputs are write-once (O_CREAT|O_EXCL). A second build aborts.
R5  Timestamps are genuinely timezone-aware (`datetime.now().astimezone()`),
    never literals, and carry an explicit uncertainty label because the host
    clock is not synchronised.

Why R2 exists
-------------
The v1.1 manifest's Section C reported `registry_sha256 = null` with
`match = true` for all 15 checkpoints. Cause: the builder resolved the reference
with `r.get("best_sha256") or r.get("checkpoint_sha256")`; the registry's real
key is `checkpoint_sha`; both lookups returned None; and the comparison
`ok = (exp is None) or (actual == exp)` then evaluated True unconditionally.
A fail-open comparison of exactly the shape the v1.0 generator was faulted for.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

BUILDER_VERSION = "1.2"

REGISTRY = "reports/baselines/ext03_run_registry.json"
V1_1_MANIFEST = "reports/audits/ext03_disposition_v1_1/ext03_sha256_manifest_v1_1.json"
V1_1_PROVENANCE = "reports/audits/ext03_disposition_v1_1/ext03_evidence_provenance_reconciliation_v1_1.json"
ATTESTATION_V1_2 = "reports/audits/ext03_disposition_v1_2/ext03_checkpoint_attestation_v1_2.json"

# Task A-D deliverables of this work package.
V1_2_ARTIFACTS = [
    ("scripts/analysis/ext03_v1_2_checkpoint_attestation_verifier.py", "task_A_verifier"),
    ("reports/audits/ext03_disposition_v1_2/ext03_checkpoint_attestation_v1_2.json", "task_A_attestation"),
    ("scripts/analysis/ext03_v1_2_chronology_reconciliation.py", "task_B_generator"),
    ("reports/audits/ext03_disposition_v1_2/ext03_chronology_reconciliation_v1_2.md", "task_B_chronology"),
    ("reports/audits/ext03_disposition_v1_2/ext03_chronology_reconciliation_v1_2.json", "task_B_chronology"),
    ("reports/audits/ext03_disposition_v1_2/ext03_supervisor_memorandum_addendum_v1_2.md", "task_C_addendum"),
    ("reports/audits/ext03_disposition_v1_2/ext03_supervisor_memorandum_addendum_v1_2.json", "task_C_addendum"),
    ("reports/audits/ext03_disposition_v1_2/ext03_study_identifier_namespace_reconciliation_v1_2.md", "task_D_namespace"),
    ("reports/audits/ext03_disposition_v1_2/ext03_study_identifier_namespace_reconciliation_v1_2.json", "task_D_namespace"),
]

CHECKPOINT_SHA_KEY = "checkpoint_sha"
CHECKPOINT_PATH_KEY = "checkpoint_path"
EXPECTED_ARCHS = ("unet", "attention_unet", "unetpp", "deeplabv3plus", "segformer_b0")
EXPECTED_SEEDS = (42, 123, 3407)
EXPECTED_RUNS = frozenset(f"{a}_seed{s}" for a in EXPECTED_ARCHS for s in EXPECTED_SEEDS)

import re

HEX64 = re.compile(r"^[0-9a-f]{64}$")


class BuildAbort(RuntimeError):
    def __init__(self, code: str, detail: str = ""):
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)


def raw_byte_sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require_artifact(path, role: str) -> Path:
    """R1 — the file must exist and be a regular file."""
    p = Path(path)
    if not p.exists():
        raise BuildAbort("E_REFERENCED_ABSENT", f"{role}: {path}")
    if not p.is_file():
        raise BuildAbort("E_REFERENCED_NOT_A_FILE", f"{role}: {path}")
    return p


def require_reference_sha(value, what: str) -> str:
    """R2 — a validated 64-hex digest, or abort. Never returns None."""
    if value is None:
        raise BuildAbort("E_REGISTRY_SHA_ABSENT", f"{what}: key absent (None)")
    if isinstance(value, str) and not value.strip():
        raise BuildAbort("E_REGISTRY_SHA_ABSENT", f"{what}: empty string")
    if not isinstance(value, str):
        raise BuildAbort("E_REGISTRY_SHA_MALFORMED", f"{what}: not a string")
    if not HEX64.match(value):
        raise BuildAbort("E_REGISTRY_SHA_MALFORMED", f"{what}: not 64 lowercase hex")
    return value


def require_sha_match(recorded: str, actual: str, what: str) -> None:
    """R3 — PRE == POST, or abort."""
    if recorded != actual:
        raise BuildAbort("E_SHA_MISMATCH", f"{what}: recorded={recorded} actual={actual}")


def require_run_set(present, expected=EXPECTED_RUNS) -> None:
    """The registry must contain exactly the expected runs. Never attests a subset."""
    present = frozenset(present)
    missing = expected - present
    unexpected = present - expected
    if missing:
        raise BuildAbort("E_RUN_MISSING", f"{len(missing)}: {sorted(missing)}")
    if unexpected:
        raise BuildAbort("E_RUN_UNEXPECTED", f"{len(unexpected)}: {sorted(unexpected)}")


def write_once(path: Path, payload: bytes) -> None:
    """R4 — write-once, full-write loop, fsync, post-write size check."""
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    try:
        fd = os.open(str(path), flags, 0o644)
    except FileExistsError as exc:
        raise BuildAbort("E_OUTPUT_EXISTS", str(path)) from exc
    try:
        w = 0
        while w < len(payload):
            w += os.write(fd, payload[w:])
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(payload):
        raise BuildAbort("E_WRITE_INCOMPLETE", f"{path}: {path.stat().st_size} != {len(payload)}")


def build_manifest(repo: Path) -> dict:
    repo = Path(repo)

    # ---------- Section A: new v1.2 artifacts ----------
    section_a = []
    for rel, role in V1_2_ARTIFACTS:
        p = require_artifact(repo / rel, role)
        section_a.append({"path": rel, "role": role,
                          "sha256": raw_byte_sha256(p), "bytes": p.stat().st_size})

    # ---------- Section B: v1.1 artifacts, PRE == POST ----------
    v11p = require_artifact(repo / V1_1_MANIFEST, "v1.1 manifest")
    v11 = json.loads(v11p.read_text(encoding="utf-8"))
    v11_records = v11["section_A_new_v1_1_artifacts"]["artifacts"]
    section_b, b_bad = [], []
    for rec in v11_records:
        p = repo / rec["path"]
        if not p.exists():
            b_bad.append({"path": rec["path"], "issue": "ABSENT"})
            continue
        actual = raw_byte_sha256(p)
        try:
            require_sha_match(rec["sha256"], actual, rec["path"])
            ok = True
        except BuildAbort:
            ok = False
            b_bad.append({"path": rec["path"], "issue": "SHA_MISMATCH",
                          "recorded": rec["sha256"], "actual": actual})
        section_b.append({"path": rec["path"], "recorded_sha256": rec["sha256"],
                          "actual_sha256": actual, "pre_equals_post": ok,
                          "recorded_bytes": rec.get("bytes"),
                          "actual_bytes": p.stat().st_size})
    if b_bad:
        raise BuildAbort("E_V1_1_DRIFT", json.dumps(b_bad))

    # ---------- Section C: v1.0 + authority artifacts, PRE == POST ----------
    provp = require_artifact(repo / V1_1_PROVENANCE, "v1.1 provenance")
    prov = json.loads(provp.read_text(encoding="utf-8"))
    prov_records = prov["hash_freeze"]["artifacts"]
    section_c, c_bad = [], []
    for rel, meta in prov_records.items():
        p = repo / rel
        if not p.exists():
            c_bad.append({"path": rel, "issue": "ABSENT"})
            continue
        actual = raw_byte_sha256(p)
        try:
            require_sha_match(meta["sha256"], actual, rel)
            ok = True
        except BuildAbort:
            ok = False
            c_bad.append({"path": rel, "issue": "SHA_MISMATCH",
                          "recorded": meta["sha256"], "actual": actual})
        section_c.append({"path": rel, "role": meta.get("role"),
                          "recorded_sha256": meta["sha256"], "actual_sha256": actual,
                          "pre_equals_post": ok, "actual_bytes": p.stat().st_size})
    if c_bad:
        raise BuildAbort("E_FROZEN_DRIFT", json.dumps(c_bad))

    # ---------- Section D: checkpoint attestation, re-derived from the registry ----------
    regp = require_artifact(repo / REGISTRY, "registry")
    registry = json.loads(regp.read_text(encoding="utf-8"))
    runs = registry.get("runs")
    if not isinstance(runs, dict):
        raise BuildAbort("E_REGISTRY_SHAPE", "'runs' missing or not an object")

    present = frozenset(runs)
    require_run_set(present)

    section_d = []
    for rid in sorted(runs):
        entry = runs[rid]
        reference = require_reference_sha(entry.get(CHECKPOINT_SHA_KEY), f"{rid}.{CHECKPOINT_SHA_KEY}")
        ck = entry.get(CHECKPOINT_PATH_KEY)
        if not isinstance(ck, str) or not ck.strip():
            raise BuildAbort("E_CHECKPOINT_PATH_ABSENT", rid)
        ckp = repo / Path(ck.replace("\\", "/"))
        if not ckp.exists():
            raise BuildAbort("E_CHECKPOINT_ABSENT", f"{rid}: {ck}")
        actual = raw_byte_sha256(ckp)
        require_sha_match(reference, actual, f"{rid} checkpoint")
        section_d.append({
            "run": rid,
            "checkpoint_path": ck,
            "registry_sha256": reference,
            "actual_sha256": actual,
            "match": True,
            "bytes": ckp.stat().st_size,
        })

    # Cross-check against the independently produced Task A attestation.
    attp = require_artifact(repo / ATTESTATION_V1_2, "v1.2 attestation")
    att = json.loads(attp.read_text(encoding="utf-8"))
    att_by_run = {e["run"]: e for e in att["entries"]}
    xcheck = []
    for e in section_d:
        a = att_by_run.get(e["run"])
        agree = bool(a) and a["reference_sha256"] == e["registry_sha256"] and a["actual_sha256"] == e["actual_sha256"]
        if not agree:
            raise BuildAbort("E_ATTESTATION_DISAGREEMENT", e["run"])
        xcheck.append({"run": e["run"], "attestation_agrees": True})

    # ---------- Section E: provenance of inputs and generators ----------
    now_local = datetime.now().astimezone()
    now_utc = datetime.now(timezone.utc)
    section_e = {
        "inputs": [
            {"path": REGISTRY, "sha256": raw_byte_sha256(repo / REGISTRY)},
            {"path": V1_1_MANIFEST, "sha256": raw_byte_sha256(repo / V1_1_MANIFEST)},
            {"path": V1_1_PROVENANCE, "sha256": raw_byte_sha256(repo / V1_1_PROVENANCE)},
            {"path": ATTESTATION_V1_2, "sha256": raw_byte_sha256(repo / ATTESTATION_V1_2)},
        ],
        "generators": [
            {"path": "scripts/analysis/ext03_v1_2_manifest_builder.py",
             "sha256": raw_byte_sha256(repo / "scripts/analysis/ext03_v1_2_manifest_builder.py"),
             "version": BUILDER_VERSION},
            {"path": "scripts/analysis/ext03_v1_2_checkpoint_attestation_verifier.py",
             "sha256": raw_byte_sha256(repo / "scripts/analysis/ext03_v1_2_checkpoint_attestation_verifier.py")},
            {"path": "scripts/analysis/ext03_v1_2_chronology_reconciliation.py",
             "sha256": raw_byte_sha256(repo / "scripts/analysis/ext03_v1_2_chronology_reconciliation.py")},
        ],
    }

    return {
        "artifact": "ext03_sha256_manifest",
        "version": "1.2",
        "classification": "EXT03_DELIVERABLE_SHA256_MANIFEST",
        "builder": "scripts/analysis/ext03_v1_2_manifest_builder.py",
        "builder_version": BUILDER_VERSION,
        "generated_local": now_local.isoformat(timespec="seconds"),
        "generated_utc": now_utc.isoformat(timespec="seconds"),
        "generated_local_tz_aware": now_local.tzinfo is not None,
        "timestamp_source": "datetime.now().astimezone() — computed at write, never a literal",
        "mode": "ADDITIVE_GOVERNANCE_ONLY",
        "hash_method": "raw-byte SHA-256 via Path(p).read_bytes()",

        "training_performed": False,
        "inference_performed": False,
        "frozen_artifacts_modified": False,
        "test_accessed": False,
        "router_holdout_accessed": False,
        "authorization_granted": False,
        "as08_status": "UNRESOLVED",
        "as08_marked_complete": False,
        "scientific_evidence_relabelled": False,

        "self_exclusion_note": "A manifest cannot contain its own digest. Integrity is established by recomputation from disk at any later time.",

        "defect_repair_record": {
            "v1_1_defect": "Section C reported registry_sha256=null with match=true for all 15 checkpoints",
            "root_cause": "reference digest resolved via r.get('best_sha256') or r.get('checkpoint_sha256'); the registry key is 'checkpoint_sha'; both returned None; the comparison `ok = (exp is None) or (actual == exp)` then evaluated True unconditionally",
            "failure_shape": "FAIL_OPEN_ON_ABSENT_REFERENCE",
            "same_shape_as": "the v1.0 generator defect `if recorded and actual != recorded:`",
            "repair": "single accepted key, mandatory non-empty 64-hex reference, absent reference aborts",
            "alias_fallback_permitted": False,
            "v1_1_manifest_bytes_modified": False,
            "v1_1_conclusion_was_correct_but_not_established_by_its_own_check": True,
        },

        "section_A_new_v1_2_artifacts": {"n": len(section_a), "artifacts": section_a},
        "section_B_v1_1_pre_equals_post": {
            "n": len(section_b), "n_mismatch": len(b_bad), "artifacts": section_b,
        },
        "section_C_v1_0_and_authority_pre_equals_post": {
            "n": len(section_c), "n_mismatch": len(c_bad), "artifacts": section_c,
        },
        "section_D_checkpoint_attestation": {
            "n": len(section_d), "n_mismatch": 0,
            "reference_key": CHECKPOINT_SHA_KEY,
            "cross_checked_against": ATTESTATION_V1_2,
            "cross_check_all_agree": all(x["attestation_agrees"] for x in xcheck),
            "checkpoints": section_d,
        },
        "section_E_provenance": section_e,

        "section_F_uncertainty_labels": [
            "HOST_CLOCK_NOT_SYNCHRONIZED__ABSOLUTE_UTC_CORRESPONDENCE_UNVERIFIED",
            "TIMESTAMP_IS_TIMEZONE_AWARE_AND_COMPUTED_AT_WRITE_BUT_INHERITS_HOST_CLOCK_OFFSET",
            "CHECKPOINT_DIGESTS_MEASURED_NOW_FROM_RAW_BYTES",
            "PARAMETER_COUNTS_IN_ADDENDUM_ARE_STATE_DICT_METADATA_NOT_INFERENCE",
            "NO_SAFETY_METRIC_EXISTS_IN_THE_EVALUATION_PIPELINE",
            "MANIFEST_CANNOT_HASH_ITSELF",
        ],

        "terminal_outcome": "EXT03_V1_2_GOVERNANCE_VERIFIED__SCIENTIFIC_AUTHORIZATION_STILL_PENDING",
    }


# --------------------------------------------------------------------------- #
# Negative controls
# --------------------------------------------------------------------------- #

def self_test() -> int:
    """Every case MUST fail closed. A pass-through is a defect."""
    import tempfile

    print("self-test: fail-closed negative controls")
    cases = []

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        # 1. referenced artifact absent
        try:
            require_artifact(tmp / "nope.json", "test")
        except BuildAbort as e:
            cases.append(("referenced_artifact_absent", e.code, "E_REFERENCED_ABSENT"))
        else:
            cases.append(("referenced_artifact_absent", "<NO ABORT>", "E_REFERENCED_ABSENT"))

        # 2-6. reference sha validation
        for name, val, expect in [
            ("registry_sha_absent", None, "E_REGISTRY_SHA_ABSENT"),
            ("registry_sha_empty", "   ", "E_REGISTRY_SHA_ABSENT"),
            ("registry_sha_not_string", 123, "E_REGISTRY_SHA_MALFORMED"),
            ("registry_sha_short", "a" * 63, "E_REGISTRY_SHA_MALFORMED"),
            ("registry_sha_uppercase", "A" * 64, "E_REGISTRY_SHA_MALFORMED"),
        ]:
            try:
                require_reference_sha(val, name)
            except BuildAbort as e:
                cases.append((name, e.code, expect))
            else:
                cases.append((name, "<NO ABORT>", expect))

        # 7. valid digest must pass (positive control)
        try:
            require_reference_sha("a" * 64, "valid")
            cases.append(("registry_sha_valid_accepted", "ACCEPTED", "ACCEPTED"))
        except BuildAbort as e:
            cases.append(("registry_sha_valid_accepted", e.code, "ACCEPTED"))

        # 8. sha mismatch
        try:
            require_sha_match("a" * 64, "b" * 64, "test")
        except BuildAbort as e:
            cases.append(("sha_mismatch_detected", e.code, "E_SHA_MISMATCH"))
        else:
            cases.append(("sha_mismatch_detected", "<NO ABORT>", "E_SHA_MISMATCH"))

        # 9. sha match must not abort
        try:
            require_sha_match("a" * 64, "a" * 64, "test")
            cases.append(("sha_match_accepted", "ACCEPTED", "ACCEPTED"))
        except BuildAbort as e:
            cases.append(("sha_match_accepted", e.code, "ACCEPTED"))

        # 10. write-once
        p = tmp / "once.json"
        write_once(p, b"x")
        try:
            write_once(p, b"y")
        except BuildAbort as e:
            cases.append(("write_once_refuses_second_write", e.code, "E_OUTPUT_EXISTS"))
        else:
            cases.append(("write_once_refuses_second_write", "<NO ABORT>", "E_OUTPUT_EXISTS"))

        # 11. the v1.1 defect: alias key must not be accepted
        fake_run = {"best_sha256": "a" * 64, "checkpoint_sha256": "a" * 64}
        try:
            require_reference_sha(fake_run.get(CHECKPOINT_SHA_KEY), "alias")
        except BuildAbort as e:
            cases.append(("v1_1_defect_alias_key_rejected", e.code, "E_REGISTRY_SHA_ABSENT"))
        else:
            cases.append(("v1_1_defect_alias_key_rejected", "<NO ABORT>", "E_REGISTRY_SHA_ABSENT"))

        # 12. run-set guards: empty / partial / extra must all be rejected
        for name, present, expect in [
            ("empty_registry_rejected", frozenset(), "E_RUN_MISSING"),
            ("partial_registry_rejected", frozenset(list(sorted(EXPECTED_RUNS))[:14]), "E_RUN_MISSING"),
            ("extra_run_rejected", frozenset(EXPECTED_RUNS | {"mystery_seed42"}), "E_RUN_UNEXPECTED"),
        ]:
            try:
                require_run_set(present)
            except BuildAbort as e:
                cases.append((name, e.code, expect))
            else:
                cases.append((name, "<NO ABORT>", expect))

        # 13. exact run set must be accepted (positive control)
        try:
            require_run_set(EXPECTED_RUNS)
            cases.append(("exact_run_set_accepted", "ACCEPTED", "ACCEPTED"))
        except BuildAbort as e:
            cases.append(("exact_run_set_accepted", e.code, "ACCEPTED"))

    passed = failed = 0
    for name, got, expect in cases:
        ok = got == expect
        print(f"  {'PASS' if ok else 'FAIL'}  {name:36} got={got:26} expected={expect}")
        passed += ok
        failed += (not ok)

    print(f"\n{passed}/{passed + failed} cases passed")
    return 0 if failed == 0 else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--out", default="reports/audits/ext03_disposition_v1_2/ext03_sha256_manifest_v1_2.json")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    repo = Path(args.repo_root).resolve()
    out = Path(args.out)
    if not out.is_absolute():
        out = repo / out

    try:
        manifest = build_manifest(repo)
    except BuildAbort as exc:
        print(f"BUILD_FAILED {exc.code}", file=sys.stderr)
        if exc.detail:
            print(f"  {exc.detail}", file=sys.stderr)
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8")
    try:
        write_once(out, payload)
    except BuildAbort as exc:
        print(f"BUILD_FAILED {exc.code}: {exc.detail}", file=sys.stderr)
        return 1

    print(f"generated_local : {manifest['generated_local']}")
    print(f"generated_utc   : {manifest['generated_utc']}")
    print(f"section A (new v1.2)        : {manifest['section_A_new_v1_2_artifacts']['n']}")
    print(f"section B (v1.1 PRE==POST)  : {manifest['section_B_v1_1_pre_equals_post']['n']} "
          f"mismatch={manifest['section_B_v1_1_pre_equals_post']['n_mismatch']}")
    print(f"section C (v1.0 PRE==POST)  : {manifest['section_C_v1_0_and_authority_pre_equals_post']['n']} "
          f"mismatch={manifest['section_C_v1_0_and_authority_pre_equals_post']['n_mismatch']}")
    print(f"section D (checkpoints)     : {manifest['section_D_checkpoint_attestation']['n']} "
          f"mismatch={manifest['section_D_checkpoint_attestation']['n_mismatch']}")
    print(f"WROTE {out} ({out.stat().st_size} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
