"""Independent RC2 release verifier.

Deliberately imports **nothing** from ``src.research.c1_film_launch_rc2``. The
canonicalisation, the digest rule and the manifest schema are re-implemented here
from the published description, so agreement between this script and the package
is evidence rather than tautology.

Also verifies that RC1 is still byte-identical, so RC2 cannot be "current" while
the historical release it supersedes has moved.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MANIFEST = ROOT / "src/research/c1_film_launch_rc2/manifest_rc2.json"
DIGEST = ROOT / "src/research/c1_film_launch_rc2/RELEASE_DIGEST_RC2.txt"
RC1_MANIFEST = ROOT / "src/research/c1_film_launch/manifest_v2.json"

EXPECTED_RELEASE_ID = "C1_FILM_ATTRIBUTION_V1_LAUNCH_RC2"
EXPECTED_STUDY_ID = "C1_FILM_ATTRIBUTION_V1"
EXPECTED_CANONICALISATION = (
    "json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,"
    "allow_nan=False).encode('utf-8')")
EXPECTED_DIGEST_RULE = "sha256(canonical_json(manifest))"
RC1_RELEASE_DIGEST = "1aec5e17ee79eb8845ea36808d5a087ea99c091be798ec5a41b4e412f93ff9c1"
RC1_MANIFEST_SHA256 = "0e3f171983ceb53b966dd1eb14547f39729a228d644e47642f67375b61736cfe"

REQUIRED_COVERAGE = (
    "src/research/c1_film_launch_rc2/__init__.py",
    "src/research/c1_film_launch_rc2/release_identity_rc2.py",
    "src/research/c1_film_launch_rc2/trust_policy.py",
    "src/research/c1_film_launch_rc2/time_status.py",
    "src/research/c1_film_launch_rc2/rc2_gate.py",
    "src/research/c1_film_launch_rc2/launch_driver_rc2.py",
    "tests/test_c1_launch_rc2.py",
    "scripts/verification/c1_launch_rc2_freeze.py",
    "scripts/verification/c1_launch_rc2_verify.py",
)


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def read_published() -> dict:
    fields = {}
    for line in DIGEST.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition("=")
            fields[key.strip()] = value.strip()
    return fields


def main() -> int:
    failures = []

    if not MANIFEST.is_file():
        print("FAIL manifest missing")
        return 1
    raw = MANIFEST.read_bytes()
    manifest = json.loads(raw.decode("utf-8"))

    if manifest.get("schema") != 3:
        failures.append("schema")
    if manifest.get("release_id") != EXPECTED_RELEASE_ID:
        failures.append("release_id")
    if manifest.get("study_id") != EXPECTED_STUDY_ID:
        failures.append("study_id")
    if manifest.get("canonicalisation") != EXPECTED_CANONICALISATION:
        failures.append("canonicalisation")
    if manifest.get("digest_rule") != EXPECTED_DIGEST_RULE:
        failures.append("digest_rule")

    bound = {e["path"]: e["sha256"] for e in manifest.get("bound_sources", [])}
    for path in REQUIRED_COVERAGE:
        if path not in bound:
            failures.append(f"coverage:{path}")
    for path, expected in sorted(bound.items()):
        target = ROOT / path
        if not target.is_file():
            failures.append(f"missing:{path}")
        elif sha256_bytes(target.read_bytes()) != expected:
            failures.append(f"drift:{path}")

    # RC1 must remain frozen.
    if not RC1_MANIFEST.is_file():
        failures.append("rc1_manifest_missing")
    else:
        rc1_raw = RC1_MANIFEST.read_bytes()
        if sha256_bytes(rc1_raw) != RC1_MANIFEST_SHA256:
            failures.append("rc1_manifest_drift")
        if sha256_bytes(canonical(json.loads(rc1_raw.decode("utf-8")))) != RC1_RELEASE_DIGEST:
            failures.append("rc1_digest_drift")

    digest = sha256_bytes(canonical(manifest))
    published = read_published() if DIGEST.is_file() else {}
    if published.get("release_digest") != digest:
        failures.append("published_digest_stale")
    if published.get("manifest_sha256") != sha256_bytes(raw):
        failures.append("published_manifest_stale")
    if published.get("supersedes_release_digest") != RC1_RELEASE_DIGEST:
        failures.append("supersedes_stale")

    print(f"release_id={manifest.get('release_id')}")
    print(f"manifest_file_sha256={sha256_bytes(raw)}")
    print(f"release_digest_recomputed={digest}")
    print(f"release_digest_published={published.get('release_digest')}")
    print(f"bound_source_count={len(bound)}")
    print(f"supersedes_release_digest={published.get('supersedes_release_digest')}")
    print(f"rc1_manifest_sha256={sha256_bytes(RC1_MANIFEST.read_bytes()) if RC1_MANIFEST.is_file() else 'MISSING'}")

    if failures:
        print("VERIFICATION_FAILED")
        for item in failures:
            print(f"  {item}")
        return 1
    print("VERIFICATION_PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
