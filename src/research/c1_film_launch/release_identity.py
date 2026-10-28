"""C1 launch release identity: canonical, non-circular, independently verifiable.

Design invariants
-----------------
1. ``manifest_v2.json`` binds every executable source by explicit path -> sha256.
   The manifest never contains its own digest, so there is no circular hashing.
2. The release digest is ``sha256(canonical_json(manifest))`` with a fully
   specified canonicalisation, so a third party can recompute it from the
   manifest bytes alone without running this module.
3. Required coverage is declared **in code**, not in the manifest. A manifest
   that silently omits a module therefore fails ``C1_RELEASE_COVERAGE_INCOMPLETE``
   rather than appearing complete.
4. ``RELEASE_DIGEST.txt`` publishes the digest, the manifest file-byte digest and
   the exact canonicalisation rule. File-byte identity and semantic identity are
   both published and independently checkable.

The frozen preparation package (``package_identities.json``) and the frozen
protocol are read-only inputs here and are never rewritten.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE_DIR = ROOT / "src/research/c1_film_launch"
MANIFEST_PATH = PACKAGE_DIR / "manifest_v2.json"
DIGEST_PATH = PACKAGE_DIR / "RELEASE_DIGEST.txt"

STUDY_ID = "C1_FILM_ATTRIBUTION_V1"
PROTOCOL_PATH = ROOT / "reports/planning/c1_film_attribution_v1/protocol.json"
PROTOCOL_SHA256 = "531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61"
ARCHITECTURE_PATH = ROOT / "src/models/film/global_medfilm.py"
ARCHITECTURE_SHA256 = "a04ff3e61b4d900ff47c2f390da4a999e73bd6047b28a19e41b05115e431d11f"
DEPENDENCY_LOCK_PATH = ROOT / "reports/planning/c1_launch_release_v1/c1_dependency_lock.json"

CANONICALISATION = "json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')"
DIGEST_RULE = "sha256(canonical_json(manifest))"

# --- Required coverage, declared independently of the manifest ---------------
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
RESULT_AFFECTING_SOURCES = (
    "src/models/film/global_medfilm.py",
    "src/models/film/__init__.py",
    "src/data/domain_balanced_sampler.py",
    "src/data/loaders.py",
    "src/data/multidomain_dataset.py",
    "src/data/transforms.py",
    "src/losses/segmentation.py",
    "src/training/phase20_selection.py",
    "src/utils/reproducibility.py",
    "src/utils/run_lock.py",
    "scripts/training/phase21_common.py",
)
REQUIRED_COVERAGE = C1_MODULES + C1_TESTS + LAUNCH_SOURCES + RESULT_AFFECTING_SOURCES

SELF_EXCLUDED = (
    "src/research/c1_film_launch/manifest_v2.json",
    "src/research/c1_film_launch/RELEASE_DIGEST.txt",
)


class ReleaseIdentityError(RuntimeError):
    pass


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def compute_release_digest(manifest: dict) -> str:
    """sha256 over the canonical JSON of the manifest. No self-reference."""
    return sha256_bytes(canonical_json(manifest))


def recipe_digest(protocol: dict) -> str:
    return sha256_bytes(canonical_json(protocol["recipe"]))


def build_manifest(paths) -> dict:
    """Construct a manifest from an explicit path iterable. Used by the freezer."""
    entries = []
    for path in sorted(set(paths)):
        absolute = ROOT / path
        if not absolute.is_file():
            raise ReleaseIdentityError(f"C1_RELEASE_SOURCE_MISSING:{path}")
        entries.append({"path": path, "sha256": sha256_file(absolute),
                        "bytes": absolute.stat().st_size})
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8-sig"))
    return {
        "schema": 2,
        "study_id": STUDY_ID,
        "protocol": {"path": "reports/planning/c1_film_attribution_v1/protocol.json",
                     "sha256": sha256_file(PROTOCOL_PATH)},
        "architecture": {"path": "src/models/film/global_medfilm.py",
                         "sha256": sha256_file(ARCHITECTURE_PATH)},
        "recipe_digest": recipe_digest(protocol),
        "dependency_lock": {
            "path": "reports/planning/c1_launch_release_v1/c1_dependency_lock.json",
            "sha256": sha256_file(DEPENDENCY_LOCK_PATH),
        },
        "canonicalisation": CANONICALISATION,
        "digest_rule": DIGEST_RULE,
        "self_excluded": list(SELF_EXCLUDED),
        "bound_sources": entries,
    }


def published_digest() -> dict:
    if not DIGEST_PATH.is_file():
        raise ReleaseIdentityError("C1_RELEASE_DIGEST_UNPUBLISHED")
    fields = {}
    for line in DIGEST_PATH.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition("=")
            fields[key.strip()] = value.strip()
    if "release_digest" not in fields:
        raise ReleaseIdentityError("C1_RELEASE_DIGEST_UNPUBLISHED")
    return fields


def verify_release(*, require_published: bool = True) -> dict:
    """Recompute everything from disk. Raises on any divergence.

    Returns a report describing the verified identity.
    """
    if not MANIFEST_PATH.is_file():
        raise ReleaseIdentityError("C1_RELEASE_MANIFEST_MISSING")
    manifest_raw = MANIFEST_PATH.read_bytes()
    try:
        manifest = json.loads(manifest_raw.decode("utf-8"))
    except ValueError as exc:
        raise ReleaseIdentityError("C1_RELEASE_MANIFEST_UNREADABLE") from exc

    if manifest.get("schema") != 2 or manifest.get("study_id") != STUDY_ID:
        raise ReleaseIdentityError("C1_RELEASE_MANIFEST_SCHEMA")

    bound = {e["path"]: e for e in manifest.get("bound_sources", [])}
    if len(bound) != len(manifest.get("bound_sources", [])):
        raise ReleaseIdentityError("C1_RELEASE_MANIFEST_DUPLICATE_PATH")

    # 1. Self-exclusion invariant: the manifest must not bind itself.
    for excluded in SELF_EXCLUDED:
        if excluded in bound:
            raise ReleaseIdentityError("C1_RELEASE_SELF_BINDING")

    # 2. Required coverage is asserted from code, not from the manifest.
    missing = [p for p in REQUIRED_COVERAGE if p not in bound]
    if missing:
        raise ReleaseIdentityError("C1_RELEASE_COVERAGE_INCOMPLETE:" + ",".join(missing))

    # 3. Every bound file must match its recorded digest.
    for path, entry in sorted(bound.items()):
        absolute = ROOT / path
        if not absolute.is_file():
            raise ReleaseIdentityError(f"C1_RELEASE_SOURCE_MISSING:{path}")
        actual = sha256_file(absolute)
        if actual != entry["sha256"]:
            raise ReleaseIdentityError(f"C1_RELEASE_SOURCE_DRIFT:{path}")

    # 4. Frozen protocol and architecture identity.
    if sha256_file(PROTOCOL_PATH) != PROTOCOL_SHA256:
        raise ReleaseIdentityError("C1_PROTOCOL_DIGEST_DRIFT")
    if manifest["protocol"]["sha256"] != PROTOCOL_SHA256:
        raise ReleaseIdentityError("C1_RELEASE_PROTOCOL_BINDING_MISMATCH")
    if sha256_file(ARCHITECTURE_PATH) != ARCHITECTURE_SHA256:
        raise ReleaseIdentityError("C1_ARCHITECTURE_SOURCE_DRIFT")
    if manifest["architecture"]["sha256"] != ARCHITECTURE_SHA256:
        raise ReleaseIdentityError("C1_RELEASE_ARCHITECTURE_BINDING_MISMATCH")

    # 5. Recipe and dependency-lock identity.
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8-sig"))
    if manifest["recipe_digest"] != recipe_digest(protocol):
        raise ReleaseIdentityError("C1_RELEASE_RECIPE_BINDING_MISMATCH")
    lock_path = ROOT / manifest["dependency_lock"]["path"]
    if not lock_path.is_file():
        raise ReleaseIdentityError("C1_DEPENDENCY_LOCK_MISSING")
    if sha256_file(lock_path) != manifest["dependency_lock"]["sha256"]:
        raise ReleaseIdentityError("C1_DEPENDENCY_LOCK_DRIFT")

    # 6. Canonicalisation and rule must be the documented ones.
    if manifest.get("canonicalisation") != CANONICALISATION:
        raise ReleaseIdentityError("C1_RELEASE_CANONICALISATION_DRIFT")
    if manifest.get("digest_rule") != DIGEST_RULE:
        raise ReleaseIdentityError("C1_RELEASE_DIGEST_RULE_DRIFT")

    digest = compute_release_digest(manifest)
    report = {
        "study_id": STUDY_ID,
        "release_digest": digest,
        "manifest_path": "src/research/c1_film_launch/manifest_v2.json",
        "manifest_file_sha256": sha256_bytes(manifest_raw),
        "bound_source_count": len(bound),
        "c1_module_count": sum(1 for p in bound if p.startswith("src/research/c1_film/")),
        "launch_source_count": sum(1 for p in bound if p.startswith("src/research/c1_film_launch/")),
        "protocol_sha256": PROTOCOL_SHA256,
        "architecture_sha256": ARCHITECTURE_SHA256,
        "recipe_digest": manifest["recipe_digest"],
        "dependency_lock_sha256": manifest["dependency_lock"]["sha256"],
        "canonicalisation": CANONICALISATION,
        "digest_rule": DIGEST_RULE,
    }

    if require_published:
        published = published_digest()
        if published["release_digest"] != digest:
            raise ReleaseIdentityError("C1_RELEASE_DIGEST_STALE")
        if published.get("manifest_sha256") != report["manifest_file_sha256"]:
            raise ReleaseIdentityError("C1_RELEASE_MANIFEST_FILE_STALE")
        report["published_digest_matches"] = True
    else:
        report["published_digest_matches"] = None
    return report
