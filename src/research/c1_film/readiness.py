"""Preparation-only fail-closed C1 scope and approval contract.

Does not load manifests/images, import a trainer, or run scientific work.
No cryptographic trust system is introduced. Real approval must be authenticated
through the institution's existing channel; structured data alone is not proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROTOCOL = ROOT / "reports/planning/c1_film_attribution_v1/protocol.json"
PROTOCOL_SHA256 = "531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61"
STUDY_ID = "C1_FILM_ATTRIBUTION_V1"
DATASET_ID = "MULTI_DOMAIN_ISIC_BUSI_KVASIR_KUB"
TASK_IDS = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}
POPULATIONS = {
    "TRAIN": {"path": "manifests/phase4_v3/train.csv", "n": 5832,
              "sha256": "28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6"},
    "VAL": {"path": "manifests/phase4_v3/val.csv", "n": 808,
            "sha256": "082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315"},
}
EXCLUSIONS = {"TEST", "ROUTER_HOLDOUT", "EXTERNAL", "QUARANTINE",
              "BARR-M1", "C2", "C3"}


class ReadinessError(RuntimeError):
    pass


def validate_dataset_contract(dataset: dict) -> None:
    expected = {
        "dataset_id": DATASET_ID, "manifest_version": "phase4_v3",
        "task_ids": TASK_IDS, "populations": POPULATIONS,
        "prohibited": ["TEST", "ROUTER_HOLDOUT", "EXTERNAL", "QUARANTINE"],
    }
    if dataset != expected:
        raise ReadinessError("C1_DATASET_SCOPE_DRIFT")


def validate_population_request(dataset: dict, split: str, path: str, n: int,
                                digest: str) -> None:
    """Validate supplied metadata only; never open a manifest or pixel path."""
    validate_dataset_contract(dataset)
    if split not in POPULATIONS:
        raise ReadinessError("C1_PROHIBITED_SPLIT")
    if {"path": path, "n": n, "sha256": digest} != POPULATIONS[split]:
        raise ReadinessError("C1_POPULATION_IDENTITY_MISMATCH")


def load_protocol() -> dict:
    raw = PROTOCOL.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PROTOCOL_SHA256:
        raise ReadinessError("C1_PROTOCOL_DIGEST_DRIFT")
    protocol = json.loads(raw)
    validate_dataset_contract(protocol["dataset"])
    if protocol["study_id"] != STUDY_ID or protocol["seeds"] != [42, 123, 3407]:
        raise ReadinessError("C1_PROTOCOL_IDENTITY_DRIFT")
    return protocol


def assert_launch_allowed(protocol: dict, approval: dict | None = None,
                          launch: dict | None = None) -> None:
    """Never enables this preparation build, even with self-asserted approval.

    Checks make future integration requirements explicit. This package contains
    no real-data trainer. BARR-M1 approval cannot satisfy C1 scope.
    """
    validate_dataset_contract(protocol["dataset"])
    if approval is None:
        raise ReadinessError("C1_AUTHORIZATION_REQUIRED")
    required = ("authorization_id", "authorized_by", "institutional_role",
                "decision_record", "authorized_at", "scope", "protocol_sha256")
    if any(not isinstance(approval.get(k), str) or not approval[k].strip()
           for k in required):
        raise ReadinessError("C1_AUTHORIZATION_INCOMPLETE")
    if approval["scope"] != STUDY_ID or approval["protocol_sha256"] != PROTOCOL_SHA256:
        raise ReadinessError("C1_AUTHORIZATION_SCOPE_MISMATCH")
    if set(approval.get("arms", [])) != {"C1-T", "C1-C"}:
        raise ReadinessError("C1_AUTHORIZATION_ARMS_MISMATCH")
    if approval.get("seeds") != [42, 123, 3407]:
        raise ReadinessError("C1_AUTHORIZATION_SEEDS_MISMATCH")
    if not EXCLUSIONS.issubset(set(approval.get("exclusions", []))):
        raise ReadinessError("C1_AUTHORIZATION_EXCLUSIONS_MISSING")
    if not launch or launch.get("authorization_id") != approval["authorization_id"]:
        raise ReadinessError("C1_SEPARATE_LAUNCH_REQUIRED")
    # Hard stop: an untrusted dict or preparation protocol cannot grant execution.
    raise ReadinessError("C1_PREPARATION_ONLY_NO_REAL_DATA_DRIVER")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="C1 preparation status only; no scientific execution")
    parser.parse_args(argv)
    protocol = load_protocol()
    print(json.dumps({"study_id": protocol["study_id"],
                      "implementation": "CONTROL_AND_SCOPE_PRIMITIVES_ONLY",
                      "protocol": "READY_FOR_APPROVAL",
                      "authorization": "PENDING",
                      "scientific_execution": "NOT_STARTED",
                      "real_data_driver": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
