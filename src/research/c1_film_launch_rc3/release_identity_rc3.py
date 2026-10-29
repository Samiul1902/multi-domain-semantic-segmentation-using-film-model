"""C1 launch release identity — RC3.

RC3 is additive to RC2 and RC1. It never rewrites RC1 or RC2: both historical
manifests and their bound sources stay byte-identical. RC3 pins both RC1 and RC2
identities.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE_DIR = ROOT / "src/research/c1_film_launch_rc3"
MANIFEST_NAME = "manifest_rc3.json"
DIGEST_NAME = "RELEASE_DIGEST_RC3.txt"
MANIFEST_PATH = PACKAGE_DIR / MANIFEST_NAME
DIGEST_PATH = PACKAGE_DIR / DIGEST_NAME

RELEASE_ID = "C1_FILM_ATTRIBUTION_V1_LAUNCH_RC3"
STUDY_ID = "C1_FILM_ATTRIBUTION_V1"

PROTOCOL_PATH = ROOT / "reports/planning/c1_film_attribution_v1/protocol.json"
PROTOCOL_SHA256 = "531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61"
ARCHITECTURE_PATH = ROOT / "src/models/film/global_medfilm.py"
ARCHITECTURE_SHA256 = "a04ff3e61b4d900ff47c2f390da4a999e73bd6047b28a19e41b05115e431d11f"
DEPENDENCY_LOCK_PATH = ROOT / "reports/planning/c1_launch_release_v1/c1_dependency_lock.json"

# Pinned predecessor releases
RC1_RELEASE_ID = "C1_FILM_ATTRIBUTION_V1_LAUNCH_RC1"
RC1_MANIFEST_PATH = ROOT / "src/research/c1_film_launch/manifest_v2.json"
RC1_RELEASE_DIGEST = "1aec5e17ee79eb8845ea36808d5a087ea99c091be798ec5a41b4e412f93ff9c1"
RC1_MANIFEST_SHA256 = "0e3f171983ceb53b966dd1eb14547f39729a228d644e47642f67375b61736cfe"

RC2_RELEASE_ID = "C1_FILM_ATTRIBUTION_V1_LAUNCH_RC2"
RC2_MANIFEST_PATH = ROOT / "src/research/c1_film_launch_rc2/manifest_rc2.json"
RC2_RELEASE_DIGEST = "54794efc6d99d94fae9eaebd992e01e4e9923b5055d024ea1d5f02a8a5e737ed"
RC2_MANIFEST_SHA256 = "f5169cedce9896da5eeb78866dd36571f81fc11822b64e718235e438b397f71c"

CANONICALISATION = "json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')"
DIGEST_RULE = "sha256(canonical_json(manifest))"

RC3_SOURCES = (
    "src/research/c1_film_launch_rc3/__init__.py",
    "src/research/c1_film_launch_rc3/release_identity_rc3.py",
    "src/research/c1_film_launch_rc3/time_status_rc3.py",
    "src/research/c1_film_launch_rc3/rc3_gate.py",
    "src/research/c1_film_launch_rc3/launch_driver_rc3.py",
)
RC3_TESTS = ("tests/test_c1_launch_rc3.py",)
RC3_SCRIPTS = (
    "scripts/verification/c1_launch_rc3_freeze.py",
    "scripts/verification/c1_launch_rc3_verify.py",
)
REQUIRED_COVERAGE = RC3_SOURCES + RC3_TESTS + RC3_SCRIPTS

SELF_EXCLUDED = (
    "src/research/c1_film_launch_rc3/" + MANIFEST_NAME,
    "src/research/c1_film_launch_rc3/" + DIGEST_NAME,
)


class ReleaseIdentityError(RuntimeError):
    pass


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def compute_release_digest(manifest: dict) -> str:
    return sha256_bytes(canonical_json(manifest))


def recipe_digest(protocol: dict) -> str:
    return sha256_bytes(canonical_json(protocol["recipe"]))


def build_manifest(paths) -> dict:
    entries = []
    for path in sorted(set(paths)):
        absolute = ROOT / path
        if not absolute.is_file():
            raise ReleaseIdentityError(f"C1_RC3_SOURCE_MISSING:{path}")
        entries.append({"path": path, "sha256": sha256_file(absolute),
                        "bytes": absolute.stat().st_size})
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8-sig"))
    return {
        "schema": 4,
        "release_id": RELEASE_ID,
        "study_id": STUDY_ID,
        "supersedes": {
            "rc1": {
                "release_id": RC1_RELEASE_ID,
                "release_digest": RC1_RELEASE_DIGEST,
                "manifest_sha256": RC1_MANIFEST_SHA256,
                "manifest_path": "src/research/c1_film_launch/manifest_v2.json",
            },
            "rc2": {
                "release_id": RC2_RELEASE_ID,
                "release_digest": RC2_RELEASE_DIGEST,
                "manifest_sha256": RC2_MANIFEST_SHA256,
                "manifest_path": "src/research/c1_film_launch_rc2/manifest_rc2.json",
            }
        },
        "protocol": {"path": "reports/planning/c1_film_attribution_v1/protocol.json",
                     "sha256": sha256_file(PROTOCOL_PATH)},
        "architecture": {"path": "src/models/film/global_medfilm.py",
                         "sha256": sha256_file(ARCHITECTURE_PATH)},
        "recipe_digest": recipe_digest(protocol),
        "dependency_lock": {
            "path": "reports/planning/c1_launch_release_v1/c1_dependency_lock.json",
            "sha256": sha256_file(DEPENDENCY_LOCK_PATH),
        },
        "trust_store": {
            "production_root": "OS_SCOPE_DEFAULT",
            "inside_release": False,
            "anchors_shipped": 0,
        },
        "host_clock": {
            "verification_mechanism": "SIGNED_NTP_ATTESTATION_VIA_TIME_AUTHORITY",
            "attestation_type": "C1_RC3_HOST_CLOCK_ATTESTATION",
            "default_trust_level": "NOT_ESTABLISHED",
            "verified_trust_level": "VERIFIED",
        },
        "canonicalisation": CANONICALISATION,
        "digest_rule": DIGEST_RULE,
        "bound_sources": entries,
    }


def verify_release_rc3(manifest_path=None, *, require_published=True, root=None) -> dict:
    root = Path(root) if root is not None else ROOT
    mpath = Path(manifest_path) if manifest_path is not None else root / "src/research/c1_film_launch_rc3" / MANIFEST_NAME
    if not mpath.is_file():
        raise ReleaseIdentityError("C1_RC3_MANIFEST_UNPUBLISHED")

    manifest_raw = mpath.read_bytes()
    try:
        manifest = json.loads(manifest_raw.decode("utf-8"))
    except Exception as exc:
        raise ReleaseIdentityError("C1_RC3_MANIFEST_MALFORMED") from exc

    if manifest.get("release_id") != RELEASE_ID or manifest.get("study_id") != STUDY_ID:
        raise ReleaseIdentityError("C1_RC3_IDENTITY_HEADER_DRIFT")

    bound = {entry["path"]: entry for entry in manifest.get("bound_sources", [])}
    missing = set(REQUIRED_COVERAGE) - set(bound.keys())
    if missing:
        raise ReleaseIdentityError(f"C1_RC3_COVERAGE_INCOMPLETE:{sorted(missing)}")

    for rel_path, entry in bound.items():
        p = root / rel_path
        if not p.is_file():
            raise ReleaseIdentityError(f"C1_RC3_SOURCE_MISSING:{rel_path}")
        raw = p.read_bytes()
        if sha256_bytes(raw) != entry["sha256"]:
            raise ReleaseIdentityError(f"C1_RC3_SOURCE_MODIFIED:{rel_path}")
        if len(raw) != entry["bytes"]:
            raise ReleaseIdentityError(f"C1_RC3_SOURCE_BYTE_COUNT_CHANGED:{rel_path}")

    # Check predecessors
    from ..c1_film_launch import release_identity as rc1_identity
    from ..c1_film_launch_rc2 import release_identity_rc2 as rc2_identity

    rc1_rep = rc1_identity.verify_release()
    if rc1_rep["release_digest"] != RC1_RELEASE_DIGEST:
        raise ReleaseIdentityError("C1_RC3_RC1_DRIFT")

    rc2_rep = rc2_identity.verify_release()
    if rc2_rep["release_digest"] != RC2_RELEASE_DIGEST:
        raise ReleaseIdentityError("C1_RC3_RC2_DRIFT")

    digest = compute_release_digest(manifest)
    manifest_sha = sha256_bytes(manifest_raw)

    report = {
        "release_id": RELEASE_ID,
        "study_id": STUDY_ID,
        "release_digest": digest,
        "manifest_path": "src/research/c1_film_launch_rc3/" + MANIFEST_NAME,
        "manifest_file_sha256": manifest_sha,
        "bound_source_count": len(bound),
        "protocol_sha256": PROTOCOL_SHA256,
        "architecture_sha256": ARCHITECTURE_SHA256,
        "rc1_release_digest": RC1_RELEASE_DIGEST,
        "rc2_release_digest": RC2_RELEASE_DIGEST,
    }

    if require_published:
        pub = published_digest(root)
        if pub["release_digest"] != digest or pub.get("manifest_sha256") != manifest_sha:
            raise ReleaseIdentityError("C1_RC3_RELEASE_DIGEST_STALE")
        report["published_digest_matches"] = True

    return report


def published_digest(root=None) -> dict:
    root = Path(root) if root is not None else ROOT
    path = root / "src/research/c1_film_launch_rc3" / DIGEST_NAME
    if not path.is_file():
        raise ReleaseIdentityError("C1_RC3_RELEASE_DIGEST_UNPUBLISHED")
    fields = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, _, v = line.partition("=")
            fields[k.strip()] = v.strip()
    return fields


def verify_release(manifest_path=None, *, require_published=True, root=None) -> dict:
    return verify_release_rc3(manifest_path=manifest_path, require_published=require_published, root=root)

