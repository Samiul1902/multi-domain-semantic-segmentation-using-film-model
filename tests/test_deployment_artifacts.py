"""Synthetic bytes only: these fixtures are not model checkpoints or credentials."""
import copy
import json

import numpy as np
import pytest
import torch

from src.research.deployment import artifacts as A
from src.research.deployment.validation import assert_exact, validate_control_batch


@pytest.fixture
def fixture(tmp_path):
    files = {}
    for c in "GRBS":
        p = tmp_path / f"fixture-{c}.bin"
        p.write_bytes(f"SYNTHETIC_TEST_ONLY_{c}".encode())
        files[c] = p
    config = dict(family="FULL", seed=42, protocol_sha256="a" * 64,
                  source_sha256="b" * 64, preprocessing=dict(channels=3, resolution=512,
                  implementation_sha256="c" * 64, contract_id="synthetic_fixture_v1"),
                  roi_threshold=.3, segmentation_threshold=.5, safety_threshold=.5,
                  router_numeric_dim=202, task_embedding_dim=16, router_total_dim=218,
                  evidence_class="SYNTHETIC_TEST_ONLY")
    return files, {c: A.digest(p) for c, p in files.items()}, config


def test_package_roundtrip_and_write_once(tmp_path, fixture):
    files, shas, config = fixture
    root = tmp_path / "package"
    sha = A.package(root, files, shas, config)
    assert A.verify(root, sha)["config"] == config
    for c in files:
        assert (root / "components" / f"{c}.pt").read_bytes() == files[c].read_bytes()
    with pytest.raises(FileExistsError):
        A.package(root, files, shas, config)
    with pytest.raises(A.ArtifactError, match="manifest identity"):
        A.verify(root, "0" * 64)
    (root / "components/G.pt").write_bytes(b"tampered")
    with pytest.raises(A.ArtifactError, match="artifact identity"):
        A.verify(root, sha)


def test_wrong_checkpoint_hash_does_not_publish(tmp_path, fixture):
    files, shas, config = fixture
    shas["R"] = "0" * 64
    with pytest.raises(A.ArtifactError):
        A.package(tmp_path / "bad", files, shas, config)
    assert not (tmp_path / "bad").exists()


@pytest.mark.parametrize("field,value", [("roi_threshold", .5), ("router_total_dim", 202),
    ("protocol_sha256", "TODO"), ("seed", True), ("family", "UNKNOWN")])
def test_config_rejects_drift(fixture, field, value):
    config = copy.deepcopy(fixture[2])
    config[field] = value
    with pytest.raises(A.ArtifactError):
        A.validate_config(config)


@pytest.mark.parametrize("name", ["../outside", "/outside", "C:/outside", "a\\b"])
def test_path_escape_refused(tmp_path, name):
    with pytest.raises(A.ArtifactError):
        A._member(tmp_path, name)


def test_unlisted_file_rejected(tmp_path, fixture):
    root = tmp_path / "package"
    sha = A.package(root, *fixture)
    (root / "unlisted").write_text("extra")
    with pytest.raises(A.ArtifactError, match="unlisted"):
        A.verify(root, sha)


def test_registry_and_rollback_verify_bytes(tmp_path, fixture):
    root = tmp_path / "package"
    sha = A.package(root, *fixture)
    registry = tmp_path / "registry"
    A.register(registry, "1.0.0", root, sha)
    A.register(registry, "1.0.1", root, sha)
    with pytest.raises(FileExistsError):
        A.register(registry, "1.0.0", root, sha)
    event = A.rollback(registry, "1.0.1", "1.0.0", "synthetic-1")
    assert "NOT_AUTHORIZED" in json.loads(event.read_text())["status"]
    with pytest.raises(FileExistsError):
        A.rollback(registry, "1.0.1", "1.0.0", "synthetic-1")


def test_monitor_no_recalibration():
    assert A.monitor({"mean": .5}, {"mean": (0., 1.)}, output_regression=False)["status"] == "WITHIN_DECLARED_BOUNDS"
    r = A.monitor({"mean": 2.}, {"mean": (0., 1.)}, output_regression=False)
    assert r["status"] == "CHECK_REQUIRED" and not r["recalibration_performed"]
    assert A.monitor({"mean": .5}, {"mean": (0., 1.)}, output_regression=True)["status"] == "CHECK_REQUIRED"
    with pytest.raises(A.ArtifactError):
        A.monitor({"mean": float("nan")}, {"mean": (0., 1.)}, output_regression=False)


@pytest.mark.parametrize("candidate", [np.array([1.000001], dtype=np.float32),
    np.array([1.], dtype=np.float64), np.array([np.nan], dtype=np.float32)])
def test_exact_parity_rejects_drift(candidate):
    with pytest.raises(A.ArtifactError):
        assert_exact({"p": np.array([1.], dtype=np.float32)}, {"p": candidate})


def test_control_batch_cost_and_decisions():
    def model(x, t):
        return {"prob": torch.sigmoid(x), "task": t, "state": "SKIP_GLOBAL"}
    result = validate_control_batch(model, model, [(torch.zeros(1, 3, 8, 8), t) for t in range(4)])
    assert result["parity"] == "BIT_EXACT" and result["control_count"] == 4
    assert result["latency_seconds_mean"] > 0 and not result["scientific_validation"]
    with pytest.raises(A.ArtifactError):
        validate_control_batch(model, model, [])
    with pytest.raises(A.ArtifactError):
        assert_exact({"state": "SKIP"}, {"state": "ACCEPT"})
