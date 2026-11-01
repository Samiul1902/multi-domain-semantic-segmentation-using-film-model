"""RC4 release identity.

Identity binds: release id, a code digest over the bound sources, the frozen
scientific protocol digest, the architecture, the recipe digest, the dependency
lock, and the pinned RC1/RC2/RC3 predecessor digests (which are re-verified live).

Hashing scheme (non-self-referential): ``release_digest = sha256(canonical_json(
manifest))``. The manifest and the published digest file are not members of
``bound_sources`` and the manifest never contains its own digest. ``code_digest``
is sha256 over the canonical sorted ``[path, sha256]`` pairs of the bound sources.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[3]
PACKAGE_REL = "src/research/c1_film_launch_rc4"
MANIFEST_NAME = "manifest_rc4.json"
DIGEST_NAME = "RELEASE_DIGEST_RC4.txt"
MANIFEST_PATH = ROOT / PACKAGE_REL / MANIFEST_NAME
DIGEST_PATH = ROOT / PACKAGE_REL / DIGEST_NAME

RELEASE_ID = "C1_FILM_ATTRIBUTION_V1_LAUNCH_RC4"
STUDY_ID = "C1_FILM_ATTRIBUTION_V1"
SCHEMA = 5

PROTOCOL_REL = "reports/planning/c1_film_attribution_v1/protocol.json"
ARCHITECTURE_REL = "src/models/film/global_medfilm.py"
DEPENDENCY_LOCK_REL = "reports/planning/c1_launch_release_v1/c1_dependency_lock.json"
PROTOCOL_PATH = ROOT / PROTOCOL_REL
ARCHITECTURE_PATH = ROOT / ARCHITECTURE_REL
DEPENDENCY_LOCK_PATH = ROOT / DEPENDENCY_LOCK_REL
PROTOCOL_SHA256 = "531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61"
ARCHITECTURE_SHA256 = "a04ff3e61b4d900ff47c2f390da4a999e73bd6047b28a19e41b05115e431d11f"

# Predecessors are pinned here and re-verified live; they are never substitutes.
PREDECESSORS = {
    "rc1": {
        "release_id": "C1_FILM_ATTRIBUTION_V1_LAUNCH_RC1",
        "release_digest": "1aec5e17ee79eb8845ea36808d5a087ea99c091be798ec5a41b4e412f93ff9c1",
        "manifest_path": "src/research/c1_film_launch/manifest_v2.json",
        "manifest_sha256": "0e3f171983ceb53b966dd1eb14547f39729a228d644e47642f67375b61736cfe",
    },
    "rc2": {
        "release_id": "C1_FILM_ATTRIBUTION_V1_LAUNCH_RC2",
        "release_digest": "54794efc6d99d94fae9eaebd992e01e4e9923b5055d024ea1d5f02a8a5e737ed",
        "manifest_path": "src/research/c1_film_launch_rc2/manifest_rc2.json",
        "manifest_sha256": "f5169cedce9896da5eeb78866dd36571f81fc11822b64e718235e438b397f71c",
    },
    "rc3": {
        "release_id": "C1_FILM_ATTRIBUTION_V1_LAUNCH_RC3",
        "release_digest": "54d1273a53db7dae58118a4bb69c2a96ba2e474a72512a9dccb4c98c9513549f",
        "manifest_path": "src/research/c1_film_launch_rc3/manifest_rc3.json",
        "manifest_sha256": "6cf2ffbdd6c3ea00118fbff74e5712bb24b8e903c1473386b0df4565da945c01",
    },
}
PREDECESSOR_DIGESTS = frozenset(p["release_digest"] for p in PREDECESSORS.values())
PREDECESSOR_IDS = frozenset(p["release_id"] for p in PREDECESSORS.values())

CANONICALISATION = ("json.dumps(obj,sort_keys=True,separators=(',',':'),"
                    "ensure_ascii=False,allow_nan=False).encode('utf-8')")
DIGEST_RULE = "sha256(canonical_json(manifest))"
CODE_DIGEST_RULE = "sha256(canonical_json(sorted([path, sha256] for bound_sources)))"

RC4_SOURCES = (
    PACKAGE_REL + "/__init__.py",
    PACKAGE_REL + "/release_identity_rc4.py",
    PACKAGE_REL + "/trust_rc4.py",
    PACKAGE_REL + "/rc4_gate.py",
    PACKAGE_REL + "/launch_driver_rc4.py",
)
RC4_TESTS = ("tests/test_c1_launch_rc4.py",)
RC4_SCRIPTS = ("scripts/verification/c1_launch_rc4_freeze.py",)
REQUIRED_COVERAGE = RC4_SOURCES + RC4_TESTS + RC4_SCRIPTS
SELF_EXCLUDED = (PACKAGE_REL + "/" + MANIFEST_NAME, PACKAGE_REL + "/" + DIGEST_NAME)


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


def compute_code_digest(entries) -> str:
    return sha256_bytes(canonical_json(sorted([e["path"], e["sha256"]] for e in entries)))


def recipe_digest(protocol: dict) -> str:
    return sha256_bytes(canonical_json(protocol["recipe"]))


def build_manifest(paths) -> dict:
    entries = []
    for path in sorted(set(paths)):
        absolute = ROOT / path
        if not absolute.is_file():
            raise ReleaseIdentityError(f"C1_RC4_SOURCE_MISSING:{path}")
        entries.append({"path": path, "sha256": sha256_file(absolute),
                        "bytes": absolute.stat().st_size})
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8-sig"))
    return {
        "schema": SCHEMA,
        "release_id": RELEASE_ID,
        "study_id": STUDY_ID,
        "supersedes": {k: dict(v) for k, v in PREDECESSORS.items()},
        "protocol": {"path": PROTOCOL_REL, "sha256": sha256_file(PROTOCOL_PATH)},
        "architecture": {"path": ARCHITECTURE_REL, "sha256": sha256_file(ARCHITECTURE_PATH)},
        "recipe_digest": recipe_digest(protocol),
        "dependency_lock": {"path": DEPENDENCY_LOCK_REL,
                            "sha256": sha256_file(DEPENDENCY_LOCK_PATH)},
        "code_digest": compute_code_digest(entries),
        "trust_model": {
            "decision": "DECISION_I",
            "production_root": "OS_SCOPE_RC4_DEFAULT",
            "inside_release": False,
            "anchors_shipped": 0,
            "legacy_rc2_rc3_root_accepted": False,
        },
        "canonicalisation": CANONICALISATION,
        "digest_rule": DIGEST_RULE,
        "code_digest_rule": CODE_DIGEST_RULE,
        "self_excluded": list(SELF_EXCLUDED),
        "bound_sources": entries,
    }


def _safe_relative(root: Path, rel: str) -> Path:
    posix = PurePosixPath(rel)
    if posix.is_absolute() or ".." in posix.parts or "\\" in rel or ":" in rel:
        raise ReleaseIdentityError(f"C1_RC4_BOUND_PATH_INVALID:{rel}")
    return root / Path(*posix.parts)


def published_digest(root=None) -> dict:
    root = Path(root) if root is not None else ROOT
    path = root / PACKAGE_REL / DIGEST_NAME
    if not path.is_file():
        raise ReleaseIdentityError("C1_RC4_RELEASE_DIGEST_UNPUBLISHED")
    fields = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition("=")
            fields[key.strip()] = value.strip()
    return fields


def _verify_predecessors(root: Path) -> None:
    from ..c1_film_launch import release_identity as rc1
    from ..c1_film_launch_rc2 import release_identity_rc2 as rc2
    from ..c1_film_launch_rc3 import release_identity_rc3 as rc3

    live = {"rc1": rc1.verify_release(), "rc2": rc2.verify_release(),
            "rc3": rc3.verify_release_rc3(require_published=True)}
    for name, pin in PREDECESSORS.items():
        if live[name]["release_digest"] != pin["release_digest"]:
            raise ReleaseIdentityError(f"C1_RC4_{name.upper()}_DRIFT")
        manifest = root / pin["manifest_path"]
        if not manifest.is_file() or sha256_file(manifest) != pin["manifest_sha256"]:
            raise ReleaseIdentityError(f"C1_RC4_{name.upper()}_DRIFT")


def verify_release_rc4(manifest_path=None, *, require_published: bool = True,
                       root=None) -> dict:
    root = Path(root) if root is not None else ROOT
    mpath = (Path(manifest_path) if manifest_path is not None
             else root / PACKAGE_REL / MANIFEST_NAME)
    if not mpath.is_file():
        raise ReleaseIdentityError("C1_RC4_MANIFEST_UNPUBLISHED")
    manifest_raw = mpath.read_bytes()
    try:
        manifest = json.loads(manifest_raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ReleaseIdentityError("C1_RC4_MANIFEST_MALFORMED") from exc
    if not isinstance(manifest, dict):
        raise ReleaseIdentityError("C1_RC4_MANIFEST_MALFORMED")

    if (manifest.get("schema") != SCHEMA or manifest.get("release_id") != RELEASE_ID
            or manifest.get("study_id") != STUDY_ID):
        raise ReleaseIdentityError("C1_RC4_IDENTITY_HEADER_DRIFT")

    protocol_file = root / PROTOCOL_REL
    if (sha256_file(protocol_file) != PROTOCOL_SHA256
            or manifest.get("protocol") != {"path": PROTOCOL_REL, "sha256": PROTOCOL_SHA256}):
        raise ReleaseIdentityError("C1_RC4_PROTOCOL_BINDING_MISMATCH")
    if (sha256_file(root / ARCHITECTURE_REL) != ARCHITECTURE_SHA256
            or manifest.get("architecture") != {"path": ARCHITECTURE_REL,
                                                "sha256": ARCHITECTURE_SHA256}):
        raise ReleaseIdentityError("C1_RC4_ARCHITECTURE_BINDING_MISMATCH")
    protocol = json.loads(protocol_file.read_text(encoding="utf-8-sig"))
    if manifest.get("recipe_digest") != recipe_digest(protocol):
        raise ReleaseIdentityError("C1_RC4_RECIPE_BINDING_MISMATCH")
    lock = manifest.get("dependency_lock") or {}
    if (lock.get("path") != DEPENDENCY_LOCK_REL
            or lock.get("sha256") != sha256_file(root / DEPENDENCY_LOCK_REL)):
        raise ReleaseIdentityError("C1_RC4_DEPENDENCY_LOCK_MISMATCH")
    if manifest.get("supersedes") != PREDECESSORS:
        raise ReleaseIdentityError("C1_RC4_PREDECESSOR_PIN_MISMATCH")

    entries = manifest.get("bound_sources")
    if not isinstance(entries, list) or any(not isinstance(e, dict) for e in entries):
        raise ReleaseIdentityError("C1_RC4_MANIFEST_MALFORMED")
    bound = {e.get("path"): e for e in entries}
    missing = set(REQUIRED_COVERAGE) - set(bound)
    if missing:
        raise ReleaseIdentityError(f"C1_RC4_COVERAGE_INCOMPLETE:{sorted(missing)}")
    for rel, entry in bound.items():
        if not isinstance(rel, str):
            raise ReleaseIdentityError("C1_RC4_MANIFEST_MALFORMED")
        path = _safe_relative(root, rel)
        if not path.is_file():
            raise ReleaseIdentityError(f"C1_RC4_SOURCE_MISSING:{rel}")
        raw = path.read_bytes()
        if sha256_bytes(raw) != entry.get("sha256"):
            raise ReleaseIdentityError(f"C1_RC4_SOURCE_MODIFIED:{rel}")
        if len(raw) != entry.get("bytes"):
            raise ReleaseIdentityError(f"C1_RC4_SOURCE_BYTE_COUNT_CHANGED:{rel}")
    if manifest.get("code_digest") != compute_code_digest(entries):
        raise ReleaseIdentityError("C1_RC4_CODE_DIGEST_MISMATCH")

    _verify_predecessors(root)

    digest = compute_release_digest(manifest)
    if digest in PREDECESSOR_DIGESTS:
        raise ReleaseIdentityError("C1_RC4_PREDECESSOR_IDENTITY_REJECTED")
    manifest_sha = sha256_bytes(manifest_raw)
    report = {
        "release_id": RELEASE_ID,
        "study_id": STUDY_ID,
        "release_digest": digest,
        "code_digest": manifest["code_digest"],
        "manifest_file_sha256": manifest_sha,
        "bound_source_count": len(bound),
        "protocol_sha256": PROTOCOL_SHA256,
        "architecture_sha256": ARCHITECTURE_SHA256,
        "supersedes": {k: v["release_digest"] for k, v in PREDECESSORS.items()},
    }
    if require_published:
        pub = published_digest(root)
        if (pub.get("release_digest") != digest or pub.get("manifest_sha256") != manifest_sha
                or pub.get("code_digest") != manifest["code_digest"]
                or pub.get("release_id") != RELEASE_ID):
            raise ReleaseIdentityError("C1_RC4_RELEASE_DIGEST_STALE")
        report["published_digest_matches"] = True
    return report
