import hashlib
import json
from pathlib import Path


def verify_test_lock(project_root=r"D:\Softfors\jup"):
    root=Path(project_root); lock=json.loads((root/"reports/audits/test_lock.json").read_text(encoding="utf-8"))
    test_path=root/"manifests/test.csv"; digest=hashlib.sha256(test_path.read_bytes()).hexdigest()
    if lock["manifest_version"]!="phase4_v2" or lock["test_sample_count"]!=1683 or digest!=lock["full_test_sha256"]:
        raise RuntimeError("Frozen test-lock verification failed")
    if "must not be used" not in lock["protocol_statement"]:
        raise RuntimeError("Test-lock protocol statement is missing")
    return lock
