"""Independent verification of the frozen C1 launch release candidate.

Deliberately does NOT import ``src.research.c1_film_launch``. It re-implements the
published canonicalisation and digest rule from ``RELEASE_DIGEST.txt`` so that a
second party can confirm the release without trusting the release's own code.

Checks
------
1. manifest file-byte digest matches the published value
2. every bound source re-hashes to its recorded digest
3. all eight C1 modules and both C1 test files are present (coverage asserted here,
   independently of the manifest's own claims)
4. frozen protocol and architecture digests match
5. recipe digest recomputes from the frozen protocol
6. dependency lock digest matches
7. release digest recomputes from the canonical manifest

Exit code 0 = verified, 1 = mismatch, 2 = missing artifact.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "src/research/c1_film_launch/manifest_v2.json"
DIGEST_FILE = ROOT / "src/research/c1_film_launch/RELEASE_DIGEST.txt"
PROTOCOL = ROOT / "reports/planning/c1_film_attribution_v1/protocol.json"
ARCHITECTURE = ROOT / "src/models/film/global_medfilm.py"

C1_MODULES = (
    "src/research/c1_film/__init__.py",
    "src/research/c1_film/control.py",
    "src/research/c1_film/integration_contract.py",
    "src/research/c1_film/readiness.py",
    "src/research/c1_film/recovery_store.py",
    "src/research/c1_film/synthetic_fixture.py",
    "src/research/c1_film/train_driver.py",
    "src/research/c1_film/training_engine.py",
)
C1_TESTS = (
    "tests/test_c1_film_preparation.py",
    "tests/test_c1_training_integration.py",
)
LAUNCH_SOURCES = (
    "src/research/c1_film_launch/__init__.py",
    "src/research/c1_film_launch/launch_driver.py",
    "src/research/c1_film_launch/launch_gate.py",
    "src/research/c1_film_launch/release_identity.py",
)


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    failures: list[str] = []

    for path in (MANIFEST, DIGEST_FILE, PROTOCOL, ARCHITECTURE):
        if not path.is_file():
            print(f"MISSING_ARTIFACT {path}")
            return 2

    published = {}
    for line in DIGEST_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition("=")
            published[key.strip()] = value.strip()

    manifest_raw = MANIFEST.read_bytes()
    if sha(manifest_raw) != published.get("manifest_sha256"):
        failures.append("MANIFEST_FILE_SHA_MISMATCH")

    manifest = json.loads(manifest_raw.decode("utf-8"))
    bound = {e["path"]: e["sha256"] for e in manifest["bound_sources"]}

    for path in C1_MODULES + C1_TESTS + LAUNCH_SOURCES:
        if path not in bound:
            failures.append(f"COVERAGE_MISSING:{path}")

    for path, expected in sorted(bound.items()):
        absolute = ROOT / path
        if not absolute.is_file():
            failures.append(f"SOURCE_MISSING:{path}")
            continue
        actual = sha(absolute.read_bytes())
        if actual != expected:
            failures.append(f"SOURCE_DRIFT:{path}")

    if sha(PROTOCOL.read_bytes()) != published.get("protocol_sha256"):
        failures.append("PROTOCOL_DRIFT")
    if sha(ARCHITECTURE.read_bytes()) != published.get("architecture_sha256"):
        failures.append("ARCHITECTURE_DRIFT")

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8-sig"))
    if sha(canonical(protocol["recipe"])) != published.get("recipe_digest"):
        failures.append("RECIPE_DRIFT")

    lock = ROOT / manifest["dependency_lock"]["path"]
    if not lock.is_file():
        failures.append("DEPENDENCY_LOCK_MISSING")
    elif sha(lock.read_bytes()) != published.get("dependency_lock_sha256"):
        failures.append("DEPENDENCY_LOCK_DRIFT")

    recomputed = sha(canonical(manifest))
    if recomputed != published.get("release_digest"):
        failures.append("RELEASE_DIGEST_MISMATCH")

    print(f"manifest_file_sha256={sha(manifest_raw)}")
    print(f"release_digest_recomputed={recomputed}")
    print(f"release_digest_published={published.get('release_digest')}")
    print(f"bound_source_count={len(bound)}")
    print(f"c1_modules_present={sum(1 for p in C1_MODULES if p in bound)}/8")
    print(f"launch_sources_present={sum(1 for p in LAUNCH_SOURCES if p in bound)}/4")

    if failures:
        print("VERIFICATION_FAILED")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print("VERIFICATION_PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
