"""PHASE-13 PART-1B §10 — archive provisional R2B checkpoints.

Makes byte-exact archival copies of the current latest.pt / best.pt under a
clearly noncanonical provenance directory, verifying byte-identity.

Label: PROVISIONAL_R2B_PIXEL_SELECTION_CHECKPOINT — NOT FOR DOWNSTREAM USE.

No training. No model. No CUDA. No TEST.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXP = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"
CHK = ROOT / "checkpoints" / EXP
ARCHIVE = CHK / "provenance"
OUT = ROOT / "reports" / "audits" / "phase13_part1b_epoch31_checkpoint_archive.json"

EXPECTED = {
    "latest.pt": "806ce086dc0fa0163029e0fb335ad6ae9605ea6b550b12371a2cb0d5340eb575",
    "best.pt": "1a4863c96484871fda2a70b02678ac602245ceea4bc8c093160a407009ba8ecc",
}
ARCHIVE_NAMES = {
    "latest.pt": "r2b_pixel_epoch31_latest.pt",
    "best.pt": "r2b_pixel_epoch31_best.pt",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(8192):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    entries = {}
    ok = True
    for source_name, expected_sha in EXPECTED.items():
        source = CHK / source_name
        if not source.exists():
            raise FileNotFoundError(f"missing source checkpoint: {source}")
        source_sha = sha256_file(source)
        if source_sha != expected_sha:
            raise ValueError(
                f"{source_name} SHA mismatch: expected {expected_sha}, got {source_sha}. STOP."
            )
        target = ARCHIVE / ARCHIVE_NAMES[source_name]
        shutil.copyfile(source, target)
        target_sha = sha256_file(target)
        byte_identical = target_sha == source_sha
        ok &= byte_identical
        entries[source_name] = {
            "source_path": str(source),
            "source_sha256": source_sha,
            "archive_path": str(target),
            "archive_sha256": target_sha,
            "byte_identical": byte_identical,
            "archive_size_bytes": target.stat().st_size,
        }

    payload = {
        "artifact": "PHASE13_PART1B_EPOCH31_CHECKPOINT_ARCHIVE",
        "document_type": "PROVISIONAL_CHECKPOINT_ARCHIVE",
        "experiment_id": EXP,
        "archive_dir": str(ARCHIVE),
        "label": "PROVISIONAL_R2B_PIXEL_SELECTION_CHECKPOINT",
        "downstream_use": "NOT_FOR_DOWNSTREAM_USE",
        "entries": entries,
        "all_byte_identical": ok,
        "canonical_checkpoints_modified": False,
        "test_reads": 0,
    }
    payload["status"] = "PASS" if ok else "CHECK_REQUIRED"
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    for name, info in entries.items():
        print(f"{name:10s} -> {info['archive_path']}")
        print(f"           src  {info['source_sha256']}")
        print(f"           arch {info['archive_sha256']}  byte_identical={info['byte_identical']}")
    print(f"all byte identical: {ok}")
    print(f"STATUS: {payload['status']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
