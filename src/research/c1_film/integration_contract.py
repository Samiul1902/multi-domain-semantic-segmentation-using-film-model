"""Immutable integration contracts; no dataset content access."""
from __future__ import annotations

import copy
import hashlib
import json
import platform
import tempfile
from pathlib import Path

import torch

from .readiness import PROTOCOL_SHA256, ROOT, ReadinessError, load_protocol


def digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def verify_preparation() -> dict:
    manifest = ROOT / "reports/planning/c1_film_attribution_v1/package_identities.json"
    if hashlib.sha256(manifest.read_bytes()).hexdigest() != (
            "4660034d2b99b0933445fb13b289b0b05208e906d2e0486595ffcd67c802b353"):
        raise ReadinessError("C1_FROZEN_PACKAGE_MANIFEST_DRIFT")
    identities = json.loads(manifest.read_text(encoding="utf-8-sig"))
    for entry in identities["files"] + identities["sources"]:
        path = ROOT / entry["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ReadinessError("C1_FROZEN_PREPARATION_IDENTITY_MISMATCH")
    return load_protocol()


def make_contract(arm: str, seed: int, *, synthetic: bool, device: str = "cpu") -> dict:
    protocol = verify_preparation()
    if arm not in protocol["arms"] or type(seed) is not int or seed not in protocol["seeds"]:
        raise ReadinessError("C1_ARM_SEED_SCOPE_MISMATCH")
    if device not in ("cpu", "cuda") or (not synthetic and device != "cuda"):
        raise ReadinessError("C1_DEVICE_SCOPE_MISMATCH")
    own_dir = Path(__file__).parent
    sources = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(own_dir.glob("*.py"))}
    return {
        "schema": 1, "study_id": protocol["study_id"], "protocol_sha256": PROTOCOL_SHA256,
        "arm": arm, "seed": seed, "dataset": copy.deepcopy(protocol["dataset"]),
        "recipe": copy.deepcopy(protocol["recipe"]), "device": device,
        "mode": "SYNTHETIC_ONLY" if synthetic else "SCIENTIFIC_C1",
        "fixture": {"version": 1, "side": 32, "train_n": 8, "val_n": 8,
                    "epochs": 3, "workers": 0} if synthetic else None,
        "runtime": {"python": platform.python_version(), "torch": str(torch.__version__),
                    "cuda_build": torch.version.cuda, "machine": platform.machine(),
                    "platform": platform.system(), "device_count": 0 if device == "cpu"
                    else torch.cuda.device_count()},
        "integration_sources": sources,
    }


def validate_synthetic_output(root: Path) -> Path:
    root = Path(root).resolve()
    temp = Path(tempfile.gettempdir()).resolve()
    if temp not in root.parents or root == temp or root == ROOT or ROOT in root.parents:
        raise ReadinessError("C1_SYNTHETIC_OUTPUT_MUST_BE_EXTERNAL_TEMP_SUBDIRECTORY")
    return root


def validate_contract(contract: dict) -> None:
    try:
        expected = make_contract(contract["arm"], contract["seed"],
                                 synthetic=contract["mode"] == "SYNTHETIC_ONLY",
                                 device=contract["device"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ReadinessError("C1_CONTRACT_INVALID") from exc
    if contract != expected:
        raise ReadinessError("C1_CONTRACT_CONFIGURATION_DRIFT")
