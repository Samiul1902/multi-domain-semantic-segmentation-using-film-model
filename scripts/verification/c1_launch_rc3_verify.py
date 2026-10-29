"""Independent RC3 release verifier.

Deliberately imports nothing from src.research.c1_film_launch_rc3.
Also verifies that RC1 and RC2 are still byte-identical.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MANIFEST = ROOT / "src/research/c1_film_launch_rc3/manifest_rc3.json"
DIGEST = ROOT / "src/research/c1_film_launch_rc3/RELEASE_DIGEST_RC3.txt"
RC1_MANIFEST = ROOT / "src/research/c1_film_launch/manifest_v2.json"
RC2_MANIFEST = ROOT / "src/research/c1_film_launch_rc2/manifest_rc2.json"

EXPECTED_RELEASE_ID = "C1_FILM_ATTRIBUTION_V1_LAUNCH_RC3"
EXPECTED_STUDY_ID = "C1_FILM_ATTRIBUTION_V1"
EXPECTED_CANONICALISATION = (
    "json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,"
    "allow_nan=False).encode('utf-8')")
EXPECTED_DIGEST_RULE = "sha256(canonical_json(manifest))"
RC1_RELEASE_DIGEST = "1aec5e17ee79eb8845ea36808d5a087ea99c091be798ec5a41b4e412f93ff9c1"
RC1_MANIFEST_SHA256 = "0e3f171983ceb53b966dd1eb14547f39729a228d644e47642f67375b61736cfe"
RC2_RELEASE_DIGEST = "54794efc6d99d94fae9eaebd992e01e4e9923b5055d024ea1d5f02a8a5e737ed"
RC2_MANIFEST_SHA256 = "f5169cedce9896da5eeb78866dd36571f81fc11822b64e718235e438b397f71c"

REQUIRED_COVERAGE = (
    "src/research/c1_film_launch_rc3/__init__.py",
    "src/research/c1_film_launch_rc3/release_identity_rc3.py",
    "src/research/c1_film_launch_rc3/time_status_rc3.py",
    "src/research/c1_film_launch_rc3/rc3_gate.py",
    "src/research/c1_film_launch_rc3/launch_driver_rc3.py",
    "tests/test_c1_launch_rc3.py",
    "scripts/verification/c1_launch_rc3_freeze.py",
    "scripts/verification/c1_launch_rc3_verify.py",
)


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def verify_standalone() -> dict:
    if not MANIFEST.is_file():
        raise RuntimeError("C1_RC3_MANIFEST_MISSING")
    raw = MANIFEST.read_bytes()
    manifest_sha = sha256_bytes(raw)
    data = json.loads(raw.decode("utf-8"))

    if data.get("release_id") != EXPECTED_RELEASE_ID:
        raise RuntimeError("C1_RC3_RELEASE_ID_DRIFT")
    if data.get("study_id") != EXPECTED_STUDY_ID:
        raise RuntimeError("C1_RC3_STUDY_ID_DRIFT")
    if data.get("canonicalisation") != EXPECTED_CANONICALISATION:
        raise RuntimeError("C1_RC3_CANONICALISATION_DRIFT")
    if data.get("digest_rule") != EXPECTED_DIGEST_RULE:
        raise RuntimeError("C1_RC3_DIGEST_RULE_DRIFT")

    # Verify predecessors
    rc1_sha = sha256_bytes(RC1_MANIFEST.read_bytes())
    if rc1_sha != RC1_MANIFEST_SHA256:
        raise RuntimeError("C1_RC3_PREDECESSOR_RC1_DRIFT")

    rc2_sha = sha256_bytes(RC2_MANIFEST.read_bytes())
    if rc2_sha != RC2_MANIFEST_SHA256:
        raise RuntimeError("C1_RC3_PREDECESSOR_RC2_DRIFT")

    # Verify bound sources
    bound = {entry["path"]: entry for entry in data.get("bound_sources", [])}
    missing = set(REQUIRED_COVERAGE) - set(bound.keys())
    if missing:
        raise RuntimeError(f"C1_RC3_COVERAGE_MISSING:{sorted(missing)}")

    for rel_path, entry in bound.items():
        p = ROOT / rel_path
        if not p.is_file():
            raise RuntimeError(f"C1_RC3_SOURCE_MISSING:{rel_path}")
        source_bytes = p.read_bytes()
        if sha256_bytes(source_bytes) != entry["sha256"]:
            raise RuntimeError(f"C1_RC3_SOURCE_TAMPERED:{rel_path}")
        if len(source_bytes) != entry["bytes"]:
            raise RuntimeError(f"C1_RC3_SOURCE_LENGTH_MISMATCH:{rel_path}")

    computed_digest = sha256_bytes(canonical(data))
    pub_lines = {}
    for line in DIGEST.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, _, v = line.partition("=")
            pub_lines[k.strip()] = v.strip()

    if pub_lines.get("release_digest") != computed_digest:
        raise RuntimeError("C1_RC3_DIGEST_FILE_STALE")
    if pub_lines.get("manifest_sha256") != manifest_sha:
        raise RuntimeError("C1_RC3_MANIFEST_SHA_MISMATCH")

    return {
        "release_id": EXPECTED_RELEASE_ID,
        "release_digest": computed_digest,
        "manifest_sha256": manifest_sha,
        "bound_count": len(bound),
        "rc1_digest": RC1_RELEASE_DIGEST,
        "rc2_digest": RC2_RELEASE_DIGEST,
        "predecessors_verified": True,
    }


def main() -> int:
    try:
        report = verify_standalone()
        print("Independent C1 RC3 verification PASS:")
        print(f"  Release digest: {report['release_digest']}")
        print(f"  Manifest SHA:   {report['manifest_sha256']}")
        print(f"  Bound files:    {report['bound_count']}")
        return 0
    except Exception as exc:
        print(f"Independent C1 RC3 verification FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

