"""Freeze the C1 launch release candidate: build manifest_v2.json + RELEASE_DIGEST.txt.

Run only after every bound source file is final. Writes exactly two artifacts and
never edits a bound source. No circular hashing: the manifest excludes itself and
the digest file.

Usage:
    python scripts/verification/c1_launch_release_freeze.py [--check]
``--check`` recomputes and reports whether the on-disk release is still current
without rewriting anything.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.research.c1_film_launch import release_identity as rid  # noqa: E402

EXTRA_BOUND = (
    "tests/test_c1_launch_release.py",
    "tests/test_c1_launch_multiprocessing.py",
    "scripts/verification/c1_launch_release_freeze.py",
    "scripts/verification/c1_launch_release_verify.py",
    "scripts/verification/c1_synthetic_cuda_verification.py",
    "scripts/verification/c1_build_dependency_lock.py",
    "reports/planning/c1_launch_release_v1/c1_dependency_lock.json",
    "reports/planning/c1_launch_release_v1/endpoint_clarification_addendum.md",
)

BOUND = tuple(sorted(set(rid.REQUIRED_COVERAGE) | set(EXTRA_BOUND)))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Freeze the C1 launch release candidate")
    parser.add_argument("--check", action="store_true",
                        help="verify the existing release without rewriting it")
    args = parser.parse_args(argv)

    if args.check:
        report = rid.verify_release()
        print(f"release_digest={report['release_digest']}")
        print(f"bound_source_count={report['bound_source_count']}")
        print(f"c1_module_count={report['c1_module_count']}")
        print("RELEASE_CURRENT")
        return 0

    missing = [p for p in BOUND if not (ROOT / p).is_file()]
    if missing:
        print("MISSING BOUND SOURCES:", *missing, sep="\n  ")
        return 2

    manifest = rid.build_manifest(BOUND)
    digest = rid.compute_release_digest(manifest)

    rid.MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    raw = (rid.canonical_json(manifest).decode("utf-8"))
    # Pretty-print for review; the semantic digest is over the canonical form.
    import json
    rid.MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                 encoding="utf-8")
    manifest_file_sha = rid.sha256_file(rid.MANIFEST_PATH)

    lines = [
        "# C1 launch release identity (published before any approval is requested)",
        "schema=2",
        f"study_id={rid.STUDY_ID}",
        f"release_digest={digest}",
        "manifest_path=src/research/c1_film_launch/manifest_v2.json",
        f"manifest_sha256={manifest_file_sha}",
        f"bound_source_count={len(manifest['bound_sources'])}",
        f"protocol_sha256={rid.PROTOCOL_SHA256}",
        f"architecture_sha256={rid.ARCHITECTURE_SHA256}",
        f"recipe_digest={manifest['recipe_digest']}",
        f"dependency_lock_sha256={manifest['dependency_lock']['sha256']}",
        f"canonicalisation={rid.CANONICALISATION}",
        f"digest_rule={rid.DIGEST_RULE}",
        "scientific_execution=NOT_AUTHORIZED",
    ]
    rid.DIGEST_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"wrote {rid.MANIFEST_PATH.relative_to(ROOT)}")
    print(f"wrote {rid.DIGEST_PATH.relative_to(ROOT)}")
    print(f"bound_source_count={len(manifest['bound_sources'])}")
    print(f"release_digest={digest}")
    print(f"manifest_sha256={manifest_file_sha}")
    print(f"canonical_bytes={len(raw.encode('utf-8'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
