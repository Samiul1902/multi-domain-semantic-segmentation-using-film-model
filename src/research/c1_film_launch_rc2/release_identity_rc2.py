"""C1 launch release identity — RC2.

RC2 is additive. It never rewrites RC1: the RC1 manifest and every RC1 bound
source stay byte-identical, and RC2 *pins* the RC1 identity so that any drift in
the historical release is detected as a failure of RC2 rather than silently
tolerated.

Design invariants (same non-circular scheme as RC1)
--------------------------------------------------
1. ``manifest_rc2.json`` binds every RC2 source by explicit path -> sha256.
   The manifest never contains its own digest.
2. The RC2 release digest is ``sha256(canonical_json(manifest_rc2))`` with a
   fully specified canonicalisation, so a third party can recompute it from the
   manifest bytes alone.
3. Required coverage is declared **in code**. A manifest that omits a module
   fails ``C1_RC2_COVERAGE_INCOMPLETE`` instead of appearing complete.
4. ``RELEASE_DIGEST_RC2.txt`` publishes the semantic digest, the manifest
   file-byte digest, the canonicalisation and the pinned RC1 identity.
5. ``trust_root.production_policy_authority_sha256`` lives in the manifest as
   **data**, not as a Python constant. Provisioning a production trust authority
   is therefore a data + re-freeze operation and never a code edit.

Honest limitation
-----------------
Binding a value in a manifest does not defend against an attacker who can
execute arbitrary code inside this process. RC2 makes the trust decision depend
on a *signed external artifact* and removes the accidental mutability of a
module global; it does not, and does not claim to, defeat in-process code
execution. The defence boundary is the process.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACKAGE_DIR = ROOT / "src/research/c1_film_launch_rc2"
MANIFEST_NAME = "manifest_rc2.json"
DIGEST_NAME = "RELEASE_DIGEST_RC2.txt"
MANIFEST_PATH = PACKAGE_DIR / MANIFEST_NAME
DIGEST_PATH = PACKAGE_DIR / DIGEST_NAME

RELEASE_ID = "C1_FILM_ATTRIBUTION_V1_LAUNCH_RC2"
STUDY_ID = "C1_FILM_ATTRIBUTION_V1"

PROTOCOL_PATH = ROOT / "reports/planning/c1_film_attribution_v1/protocol.json"
PROTOCOL_SHA256 = "531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61"
ARCHITECTURE_PATH = ROOT / "src/models/film/global_medfilm.py"
ARCHITECTURE_SHA256 = "a04ff3e61b4d900ff47c2f390da4a999e73bd6047b28a19e41b05115e431d11f"
DEPENDENCY_LOCK_PATH = ROOT / "reports/planning/c1_launch_release_v1/c1_dependency_lock.json"

# The RC1 release this package supersedes. Pinned, never recomputed from RC2.
RC1_RELEASE_ID = "C1_FILM_ATTRIBUTION_V1_LAUNCH_RC1"
RC1_MANIFEST_PATH = ROOT / "src/research/c1_film_launch/manifest_v2.json"
RC1_DIGEST_PATH = ROOT / "src/research/c1_film_launch/RELEASE_DIGEST.txt"
RC1_RELEASE_DIGEST = "1aec5e17ee79eb8845ea36808d5a087ea99c091be798ec5a41b4e412f93ff9c1"
RC1_MANIFEST_SHA256 = "0e3f171983ceb53b966dd1eb14547f39729a228d644e47642f67375b61736cfe"

CANONICALISATION = "json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')"
DIGEST_RULE = "sha256(canonical_json(manifest))"

# --- Required coverage, declared independently of the manifest ---------------
RC2_SOURCES = (
    "src/research/c1_film_launch_rc2/__init__.py",
    "src/research/c1_film_launch_rc2/release_identity_rc2.py",
    "src/research/c1_film_launch_rc2/trust_policy.py",
    "src/research/c1_film_launch_rc2/time_status.py",
    "src/research/c1_film_launch_rc2/rc2_gate.py",
    "src/research/c1_film_launch_rc2/launch_driver_rc2.py",
)
RC2_TESTS = ("tests/test_c1_launch_rc2.py",)
RC2_SCRIPTS = (
    "scripts/verification/c1_launch_rc2_freeze.py",
    "scripts/verification/c1_launch_rc2_verify.py",
)
REQUIRED_COVERAGE = RC2_SOURCES + RC2_TESTS + RC2_SCRIPTS

SELF_EXCLUDED = (
    "src/research/c1_film_launch_rc2/" + MANIFEST_NAME,
    "src/research/c1_film_launch_rc2/" + DIGEST_NAME,
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
    """sha256 over the canonical JSON of the manifest. No self-reference."""
    return sha256_bytes(canonical_json(manifest))


def recipe_digest(protocol: dict) -> str:
    return sha256_bytes(canonical_json(protocol["recipe"]))


def build_manifest(paths) -> dict:
    """Construct an RC2 manifest from an explicit path iterable (used by the freezer)."""
    entries = []
    for path in sorted(set(paths)):
        absolute = ROOT / path
        if not absolute.is_file():
            raise ReleaseIdentityError(f"C1_RC2_SOURCE_MISSING:{path}")
        entries.append({"path": path, "sha256": sha256_file(absolute),
                        "bytes": absolute.stat().st_size})
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8-sig"))
    return {
        "schema": 3,
        "release_id": RELEASE_ID,
        "study_id": STUDY_ID,
        "supersedes": {
            "release_id": RC1_RELEASE_ID,
            "release_digest": RC1_RELEASE_DIGEST,
            "manifest_sha256": RC1_MANIFEST_SHA256,
            "manifest_path": "src/research/c1_film_launch/manifest_v2.json",
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
        # Trust is external and institutional. This release ships no trust keys and
        # no trust policy; their absence is the expected production state.
        "trust_store": {
            "production_root": "OS_SCOPE_DEFAULT",
            "inside_release": False,
            "provisioned": False,
            "provisioning": "INSTITUTIONAL_EXTERNAL_NO_RELEASE_REVISION",
            "anchors_shipped": 0,
        },
        # Preserved blocking requirement: host time is not independently verified.
        "host_clock": {
            "required": True,
            "trust": "NOT_ESTABLISHED",
            "verification": "EXTERNAL_O8_REQUIRED",
        },
        "canonicalisation": CANONICALISATION,
        "digest_rule": DIGEST_RULE,
        "self_excluded": list(SELF_EXCLUDED),
        "bound_sources": entries,
    }


def _load_manifest(root: Path, manifest_path=None) -> tuple[dict, bytes]:
    path = Path(manifest_path) if manifest_path is not None else root / "src/research/c1_film_launch_rc2" / MANIFEST_NAME
    if not path.is_file():
        raise ReleaseIdentityError("C1_RC2_MANIFEST_MISSING")
    raw = path.read_bytes()
    try:
        return json.loads(raw.decode("utf-8")), raw
    except ValueError as exc:
        raise ReleaseIdentityError("C1_RC2_MANIFEST_UNREADABLE") from exc


def verify_release_rc2(*, require_published: bool = True, root=None,
                       manifest_path=None) -> dict:
    """Recompute the RC2 identity from disk. Raises on any divergence."""
    root = Path(root) if root is not None else ROOT
    manifest, manifest_raw = _load_manifest(root, manifest_path)

    if manifest.get("schema") != 3:
        raise ReleaseIdentityError("C1_RC2_MANIFEST_SCHEMA")
    if manifest.get("release_id") != RELEASE_ID or manifest.get("study_id") != STUDY_ID:
        raise ReleaseIdentityError("C1_RC2_MANIFEST_IDENTITY")

    bound = {e["path"]: e for e in manifest.get("bound_sources", [])}
    if len(bound) != len(manifest.get("bound_sources", [])):
        raise ReleaseIdentityError("C1_RC2_MANIFEST_DUPLICATE_PATH")

    # 1. Self-exclusion invariant.
    for excluded in SELF_EXCLUDED:
        if excluded in bound:
            raise ReleaseIdentityError("C1_RC2_SELF_BINDING")

    # 2. Coverage asserted from code.
    missing = [p for p in REQUIRED_COVERAGE if p not in bound]
    if missing:
        raise ReleaseIdentityError("C1_RC2_COVERAGE_INCOMPLETE:" + ",".join(missing))

    # 3. Every bound file must match its recorded digest.
    for path, entry in sorted(bound.items()):
        absolute = root / path
        if not absolute.is_file():
            raise ReleaseIdentityError(f"C1_RC2_SOURCE_MISSING:{path}")
        if sha256_file(absolute) != entry["sha256"]:
            raise ReleaseIdentityError(f"C1_RC2_SOURCE_DRIFT:{path}")

    # 4. Frozen protocol / architecture identity.
    if sha256_file(root / "reports/planning/c1_film_attribution_v1/protocol.json") != PROTOCOL_SHA256:
        raise ReleaseIdentityError("C1_PROTOCOL_DIGEST_DRIFT")
    if manifest["protocol"]["sha256"] != PROTOCOL_SHA256:
        raise ReleaseIdentityError("C1_RC2_PROTOCOL_BINDING_MISMATCH")
    if sha256_file(root / "src/models/film/global_medfilm.py") != ARCHITECTURE_SHA256:
        raise ReleaseIdentityError("C1_ARCHITECTURE_SOURCE_DRIFT")
    if manifest["architecture"]["sha256"] != ARCHITECTURE_SHA256:
        raise ReleaseIdentityError("C1_RC2_ARCHITECTURE_BINDING_MISMATCH")

    # 5. Recipe + dependency lock.
    protocol = json.loads((root / "reports/planning/c1_film_attribution_v1/protocol.json")
                          .read_text(encoding="utf-8-sig"))
    if manifest["recipe_digest"] != recipe_digest(protocol):
        raise ReleaseIdentityError("C1_RC2_RECIPE_BINDING_MISMATCH")
    lock_path = root / manifest["dependency_lock"]["path"]
    if not lock_path.is_file():
        raise ReleaseIdentityError("C1_DEPENDENCY_LOCK_MISSING")
    if sha256_file(lock_path) != manifest["dependency_lock"]["sha256"]:
        raise ReleaseIdentityError("C1_DEPENDENCY_LOCK_DRIFT")

    # 6. RC1 must remain byte-identical — RC2 pins it as historical evidence.
    rc1_manifest = root / "src/research/c1_film_launch/manifest_v2.json"
    if not rc1_manifest.is_file():
        raise ReleaseIdentityError("C1_RC2_RC1_MANIFEST_MISSING")
    rc1_raw = rc1_manifest.read_bytes()
    if sha256_bytes(rc1_raw) != RC1_MANIFEST_SHA256:
        raise ReleaseIdentityError("C1_RC2_RC1_MANIFEST_DRIFT")
    rc1_digest = compute_release_digest(json.loads(rc1_raw.decode("utf-8")))
    if rc1_digest != RC1_RELEASE_DIGEST:
        raise ReleaseIdentityError("C1_RC2_RC1_DIGEST_DRIFT")
    if manifest["supersedes"]["release_digest"] != RC1_RELEASE_DIGEST:
        raise ReleaseIdentityError("C1_RC2_RC1_BINDING_MISMATCH")
    if manifest["supersedes"]["manifest_sha256"] != RC1_MANIFEST_SHA256:
        raise ReleaseIdentityError("C1_RC2_RC1_BINDING_MISMATCH")

    # Pinning the manifest bytes is not enough: an RC1 *source* could drift while
    # the manifest stayed intact. Verify RC1's own identity so RC2 fails if the
    # historical release is no longer reproducible.
    try:
        from ..c1_film_launch import release_identity as rc1_identity
        rc1_report = rc1_identity.verify_release()
    except Exception as exc:  # noqa: BLE001 - any RC1 failure is an RC2 failure
        raise ReleaseIdentityError("C1_RC2_RC1_SOURCE_DRIFT") from exc
    if rc1_report["release_digest"] != RC1_RELEASE_DIGEST:
        raise ReleaseIdentityError("C1_RC2_RC1_SOURCE_DRIFT")

    # 7. Trust-store declaration is well-formed, external, and ships nothing.
    trust_store = manifest.get("trust_store")
    if not isinstance(trust_store, dict):
        raise ReleaseIdentityError("C1_RC2_TRUST_STORE_DECLARATION_MALFORMED")
    if trust_store.get("inside_release") is not False:
        raise ReleaseIdentityError("C1_RC2_TRUST_STORE_DECLARATION_MALFORMED")
    if trust_store.get("anchors_shipped") != 0:
        raise ReleaseIdentityError("C1_RC2_TRUST_STORE_SHIPS_ANCHORS")
    if trust_store.get("production_root") != "OS_SCOPE_DEFAULT":
        raise ReleaseIdentityError("C1_RC2_TRUST_STORE_DECLARATION_MALFORMED")

    # 8. Canonicalisation and rule must be the documented ones.
    if manifest.get("canonicalisation") != CANONICALISATION:
        raise ReleaseIdentityError("C1_RC2_CANONICALISATION_DRIFT")
    if manifest.get("digest_rule") != DIGEST_RULE:
        raise ReleaseIdentityError("C1_RC2_DIGEST_RULE_DRIFT")

    digest = compute_release_digest(manifest)
    report = {
        "release_id": RELEASE_ID,
        "study_id": STUDY_ID,
        "release_digest": digest,
        "manifest_path": "src/research/c1_film_launch_rc2/" + MANIFEST_NAME,
        "manifest_file_sha256": sha256_bytes(manifest_raw),
        "bound_source_count": len(bound),
        "rc2_source_count": sum(1 for p in bound if p.startswith("src/research/c1_film_launch_rc2/")),
        "protocol_sha256": PROTOCOL_SHA256,
        "architecture_sha256": ARCHITECTURE_SHA256,
        "recipe_digest": manifest["recipe_digest"],
        "dependency_lock_sha256": manifest["dependency_lock"]["sha256"],
        "supersedes": dict(manifest["supersedes"]),
        "rc1_release_digest": rc1_digest,
        "trust_store": dict(trust_store),
        "trust_provisioned": False,
        "host_clock": dict(manifest.get("host_clock", {})),
        "canonicalisation": CANONICALISATION,
        "digest_rule": DIGEST_RULE,
    }

    if require_published:
        published = published_digest(root)
        if published["release_digest"] != digest:
            raise ReleaseIdentityError("C1_RC2_RELEASE_DIGEST_STALE")
        if published.get("manifest_sha256") != report["manifest_file_sha256"]:
            raise ReleaseIdentityError("C1_RC2_MANIFEST_FILE_STALE")
        if published.get("supersedes_release_digest") != RC1_RELEASE_DIGEST:
            raise ReleaseIdentityError("C1_RC2_SUPERSEDES_STALE")
        report["published_digest_matches"] = True
    else:
        report["published_digest_matches"] = None
    return report


def published_digest(root=None) -> dict:
    root = Path(root) if root is not None else ROOT
    path = root / "src/research/c1_film_launch_rc2" / DIGEST_NAME
    if not path.is_file():
        raise ReleaseIdentityError("C1_RC2_RELEASE_DIGEST_UNPUBLISHED")
    fields = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition("=")
            fields[key.strip()] = value.strip()
    if "release_digest" not in fields:
        raise ReleaseIdentityError("C1_RC2_RELEASE_DIGEST_UNPUBLISHED")
    return fields


def verify_release(manifest_path=None, digest_path=None, *, require_published=True,
                   root=None) -> dict:
    """Convenience wrapper used by the gate and the independent verifier.

    ``digest_path`` is accepted for call-site symmetry; the published digest is
    always read from the canonical location under ``root`` so that a caller cannot
    pair a manifest with an unrelated digest file.
    """
    return verify_release_rc2(require_published=require_published, root=root,
                              manifest_path=manifest_path)
