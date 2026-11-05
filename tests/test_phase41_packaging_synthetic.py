"""Phase 41 coding verification — SYNTHETIC checkpoint-family bytes only.

No trained checkpoint, no real model state dict and no deployment artifact for a
real model is produced. Every ``G/R/B/S`` component is a short byte string. The
resulting packages live exclusively inside pytest's temporary directory.

Covers: packaging, model identity, dependency record binding, preprocessing
identity, artifact corruption detection, package loading, architecture
compatibility and incompatible-package rejection.
"""
from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path

import pytest

from src.research.deployment import artifacts as A
from src.research.deployment import runtime as RT

SYNTHETIC = "SYNTHETIC_TEST_ONLY"


def _config(family: str = "FULL", seed: int = 42) -> dict:
    return dict(
        family=family, seed=seed,
        protocol_sha256="a" * 64, source_sha256="b" * 64,
        preprocessing=dict(channels=1 if family == "HISTORICAL_PHASE26" else 3,
                           resolution=512, implementation_sha256="c" * 64,
                           contract_id="synthetic_fixture_v1"),
        roi_threshold=.30, segmentation_threshold=.50, safety_threshold=.50,
        router_numeric_dim=202, task_embedding_dim=16, router_total_dim=218,
        evidence_class=SYNTHETIC,
    )


@pytest.fixture
def family(tmp_path):
    files = {}
    for name in "GRBS":
        path = tmp_path / f"fixture-{name}.bin"
        path.write_bytes(f"SYNTHETIC_TEST_ONLY_{name}".encode())
        files[name] = path
    return files, {k: A.digest(v) for k, v in files.items()}, _config()


def _package(tmp_path, family, *, config=None, evidence=None):
    files, shas, default_config = family
    root = tmp_path / "package"
    sha = A.package(root, files, shas, config or default_config, evidence=evidence)
    return root, sha


# --------------------------------------------------------------------------- #
# Packaging / model identity / package loading
# --------------------------------------------------------------------------- #
def test_package_is_byte_preserving_write_once_and_loads(tmp_path, family):
    files, shas, config = family
    root, sha = _package(tmp_path, family)
    payload = A.verify(root, sha)
    assert payload["schema"] == A.SCHEMA
    assert payload["deployment_authorized"] is False
    assert payload["config"] == config
    assert payload["config"]["evidence_class"] == SYNTHETIC
    assert set(payload["members"]) == {f"components/{c}.pt" for c in "GRBS"}
    for name in "GRBS":
        packaged = root / "components" / f"{name}.pt"
        assert packaged.read_bytes() == files[name].read_bytes()
        assert payload["members"][f"components/{name}.pt"]["sha256"] == shas[name]
        assert payload["members"][f"components/{name}.pt"]["bytes"] == packaged.stat().st_size
    # manifest digest is derived from disk, not hard-coded
    assert sha == A.digest(root / "manifest.json")
    # never overwrite an incomplete attempt
    with pytest.raises(FileExistsError):
        A.package(root, files, shas, config)


def test_model_identity_mismatch_refuses_before_publication(tmp_path, family):
    files, shas, config = family
    bad = dict(shas)
    bad["R"] = "0" * 64
    destination = tmp_path / "never_published"
    with pytest.raises(A.ArtifactError, match="checkpoint identity mismatch: R"):
        A.package(destination, files, bad, config)
    assert not destination.exists()

    root, sha = _package(tmp_path, family)
    with pytest.raises(A.ArtifactError, match="manifest identity"):
        A.verify(root, "0" * 64)
    # missing / extra component identities are refused
    with pytest.raises(A.ArtifactError, match="exactly G/R/B/S"):
        A.package(tmp_path / "missing", {"G": files["G"]}, {"G": shas["G"]}, config)


def test_evidence_files_are_bound_and_path_escape_refused(tmp_path, family):
    files, shas, config = family
    evidence_file = tmp_path / "protocol.json"
    evidence_file.write_text('{"synthetic": true}', encoding="utf-8")
    root, sha = _package(tmp_path, family,
                         evidence={"protocol.json": evidence_file})
    payload = A.verify(root, sha)
    assert payload["members"]["evidence/protocol.json"]["sha256"] == A.digest(evidence_file)
    assert (root / "evidence" / "protocol.json").read_bytes() == evidence_file.read_bytes()

    for name in ("../outside", "/outside", "C:/outside", "a\\b", "a/../../b", ""):
        with pytest.raises(A.ArtifactError, match="unsafe package path|package path escapes"):
            A._member(root, name)


# --------------------------------------------------------------------------- #
# Dependency record binding
# --------------------------------------------------------------------------- #
def test_dependency_record_is_present_sorted_and_bound_by_manifest_digest(tmp_path, family):
    root, sha = _package(tmp_path, family)
    payload = A.verify(root, sha)
    env = payload["environment"]
    assert set(env) == {"python", "platform", "dependencies"}
    assert env["dependencies"] == sorted(env["dependencies"])
    assert all("==" in entry for entry in env["dependencies"])
    assert any(entry.lower().startswith("torch==") for entry in env["dependencies"])

    # Dependencies are bound by the MANIFEST SHA-256, not by per-file hashes.
    # Rewriting the record invalidates the original expected digest.
    forged = copy.deepcopy(payload)
    forged["environment"]["dependencies"] = ["forged==0.0"]
    (root / "manifest.json").write_bytes(A._json(forged))
    with pytest.raises(A.ArtifactError, match="manifest identity"):
        A.verify(root, sha)
    # The module explicitly delegates trust of the expected digest to the caller;
    # the release registry is the write-once holder of that digest.
    forged_sha = A.digest(root / "manifest.json")
    assert forged_sha != sha
    assert A.verify(root, forged_sha)["environment"]["dependencies"] == ["forged==0.0"]


# --------------------------------------------------------------------------- #
# Preprocessing identity / architecture compatibility / incompatible rejection
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("field,value", [
    ("roi_threshold", .5), ("segmentation_threshold", .4), ("safety_threshold", .6),
    ("router_numeric_dim", 200), ("task_embedding_dim", 8), ("router_total_dim", 202),
    ("protocol_sha256", "TODO"), ("source_sha256", "ABC"),
    ("seed", True), ("seed", 7), ("family", "UNKNOWN"),
    ("evidence_class", "PRODUCTION_AUTHORIZED"),
])
def test_frozen_config_contract_rejects_drift(family, field, value):
    config = copy.deepcopy(family[2])
    config[field] = value
    with pytest.raises(A.ArtifactError):
        A.validate_config(config)


@pytest.mark.parametrize("change", [
    {"channels": 1}, {"resolution": 256}, {"implementation_sha256": "xyz"},
    {"contract_id": "TODO"}, {"contract_id": ""},
])
def test_preprocessing_identity_is_enforced(family, change):
    config = copy.deepcopy(family[2])
    config["preprocessing"] = {**config["preprocessing"], **change}
    with pytest.raises(A.ArtifactError):
        A.validate_config(config)


def test_exact_field_set_and_family_specific_channel_policy(family):
    config = copy.deepcopy(family[2])
    config["extra_field"] = 1
    with pytest.raises(A.ArtifactError, match="configuration fields differ"):
        A.validate_config(config)
    del config["extra_field"]
    config.pop("safety_threshold")
    with pytest.raises(A.ArtifactError, match="configuration fields differ"):
        A.validate_config(config)

    # HISTORICAL_PHASE26 is the single-channel architecture; RGB is incompatible.
    hist = _config(family="HISTORICAL_PHASE26")
    A.validate_config(hist)
    hist["preprocessing"]["channels"] = 3
    with pytest.raises(A.ArtifactError, match="channel/resolution"):
        A.validate_config(hist)
    for seed in (42, 123, 3407):
        A.validate_config(_config(seed=seed))


def test_runtime_rejects_incompatible_family_and_identity_bindings(tmp_path, family):
    files, shas, _ = family
    hist = _config(family="LITE")
    root = tmp_path / "lite"
    sha = A.package(root, files, shas, hist)
    with pytest.raises(A.ArtifactError, match="requires a FULL package"):
        RT.FullPackageRuntime(root, sha)

    # FULL family, but the preprocessing implementation SHA does not match disk.
    full = _config()
    root2 = tmp_path / "wrong_prep"
    sha2 = A.package(root2, files, shas, full)
    with pytest.raises(A.ArtifactError, match="preprocessing implementation differs"):
        RT.FullPackageRuntime(root2, sha2)

    # Match the real preprocessing source; the loader source SHA must then differ.
    real_prep = A.digest(Path(inspect.getfile(RT.SegmentationTransform)))
    full["preprocessing"]["implementation_sha256"] = real_prep
    root3 = tmp_path / "wrong_loader"
    sha3 = A.package(root3, files, shas, full)
    with pytest.raises(A.ArtifactError, match="loader implementation differs"):
        RT.FullPackageRuntime(root3, sha3)


def test_incompatible_manifest_schema_and_authority_are_rejected(tmp_path, family):
    root, sha = _package(tmp_path, family)
    payload = A.verify(root, sha)

    for mutation in ({"deployment_authorized": True}, {"schema": "unknown_v9"}):
        forged = copy.deepcopy(payload)
        forged.update(mutation)
        (root / "manifest.json").write_bytes(A._json(forged))
        new_sha = A.digest(root / "manifest.json")
        with pytest.raises(A.ArtifactError, match="invalid package schema/authority"):
            A.verify(root, new_sha)

    forged = copy.deepcopy(payload)
    forged["config"]["family"] = "UNKNOWN"
    (root / "manifest.json").write_bytes(A._json(forged))
    with pytest.raises(A.ArtifactError, match="unsupported checkpoint family"):
        A.verify(root, A.digest(root / "manifest.json"))


# --------------------------------------------------------------------------- #
# Corruption detection
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("kind", ["component", "manifest", "unlisted", "removed", "size"])
def test_artifact_corruption_is_detected(tmp_path, family, kind):
    root, sha = _package(tmp_path, family)
    if kind == "component":
        (root / "components" / "G.pt").write_bytes(b"TAMPERED_SYNTHETIC")
        expected = "artifact identity mismatch"
    elif kind == "manifest":
        (root / "manifest.json").write_bytes(b"{}")
        expected = "manifest identity mismatch"
    elif kind == "unlisted":
        (root / "unlisted.bin").write_bytes(b"extra")
        expected = "unlisted package files"
    elif kind == "removed":
        (root / "components" / "S.pt").unlink()
        expected = "artifact identity mismatch"
    else:
        p = root / "components" / "B.pt"
        p.write_bytes(p.read_bytes() + b"x")
        expected = "artifact identity mismatch"
    with pytest.raises(A.ArtifactError, match=expected):
        A.verify(root, sha)


# --------------------------------------------------------------------------- #
# Loading / registry lifecycle (no deployment authorization)
# --------------------------------------------------------------------------- #
def test_registry_rollback_and_monitor_are_write_once_and_recalibration_free(tmp_path, family):
    root, sha = _package(tmp_path, family)
    registry = tmp_path / "registry"
    first = A.register(registry, "1.0.0", root, sha)
    assert json.loads(first.read_text(encoding="utf-8"))["evidence_class"] == SYNTHETIC
    A.register(registry, "1.0.1", root, sha)
    with pytest.raises(FileExistsError):
        A.register(registry, "1.0.0", root, sha)
    with pytest.raises(A.ArtifactError, match="major.minor.patch"):
        A.register(registry, "not-a-version", root, sha)

    event = A.rollback(registry, "1.0.1", "1.0.0", "synthetic-1")
    assert "NOT_AUTHORIZED" in json.loads(event.read_text(encoding="utf-8"))["status"]
    with pytest.raises(FileExistsError):
        A.rollback(registry, "1.0.1", "1.0.0", "synthetic-1")

    ok = A.monitor({"mean": 0.5}, {"mean": (0.0, 1.0)}, output_regression=False)
    assert ok["status"] == "WITHIN_DECLARED_BOUNDS" and ok["recalibration_performed"] is False
    drift = A.monitor({"mean": 2.0}, {"mean": (0.0, 1.0)}, output_regression=False)
    assert drift["status"] == "CHECK_REQUIRED" and drift["input_drift_triggers"] == ["mean"]
    assert A.monitor({"mean": 0.5}, {"mean": (0.0, 1.0)},
                     output_regression=True)["status"] == "CHECK_REQUIRED"
    with pytest.raises(A.ArtifactError, match="nonfinite or inverted"):
        A.monitor({"mean": float("nan")}, {"mean": (0.0, 1.0)}, output_regression=False)


def test_no_genuine_deployment_artifact_is_produced(tmp_path, family):
    root, sha = _package(tmp_path, family)
    payload = A.verify(root, sha)
    assert payload["deployment_authorized"] is False
    assert payload["config"]["evidence_class"] == SYNTHETIC
    # component bytes are synthetic markers, never a trained state dict
    for name in "GRBS":
        assert (root / "components" / f"{name}.pt").read_bytes().startswith(
            b"SYNTHETIC_TEST_ONLY_")
