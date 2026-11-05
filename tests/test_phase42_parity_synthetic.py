"""Phase 42 coding verification — synthetic compatible fixtures, deterministic inputs.

Direct vs packaged inference parity is compared across output shapes, probability
maps, binary masks, task conditioning, routing decisions and safety decisions.

PRECISION FINDING (verified below, not assumed):
  * ``validation.assert_exact`` uses ``torch.equal`` / ``np.array_equal`` and has
    NO numerical tolerance (no allclose/isclose/atol/rtol anywhere in its body).
  * Exact equality is therefore REQUIRED, but it is NOT guaranteed by the
    implementation in general. It holds only when both arms share identical
    weights, dtype, device and deterministic execution order.
  * ``FullPackageRuntime`` does not reimplement inference: it reuses the canonical
    ``FamilyBundle.load`` + ``build_gtfree`` code path, which is the architectural
    reason parity is expected for byte-identical checkpoint families.
  * Any real precision divergence (CPU vs CUDA, TF32/AMP, float16 serialisation,
    differing reduction order) is REJECTED with ``ArtifactError`` rather than
    quantified by a tolerance. No such divergence occurs in this synthetic batch;
    a 1e-6 perturbation and a float16 round-trip are both rejected below.

No trained checkpoint, no real segmentation accuracy and no deployment artifact
for a real model is produced.
"""
from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import pytest
import torch

from src.research.deployment import artifacts as A
from src.research.deployment import runtime as RT
from src.research.deployment.validation import assert_exact, validate_control_batch

SYNTHETIC = "SYNTHETIC_TEST_ONLY"
SIDE = 8


# --------------------------------------------------------------------------- #
# Deterministic synthetic compatible model fixture
# --------------------------------------------------------------------------- #
def _record(image: torch.Tensor, task_id: int, bias: float) -> dict:
    """Deterministic full inference record; no data, no GT, no tuning."""
    logit = image.float().mean(dim=1, keepdim=True) + 0.25 * task_id + bias
    prob = torch.sigmoid(logit)
    binary = (prob >= 0.50).to(torch.uint8)
    router = float(prob.mean().item()) + 0.01 * task_id
    safety = float(1.0 - prob.mean().item())
    state = "EXECUTE_THEN_ACCEPT" if router >= 0.5 else "SKIP_GLOBAL"
    return {
        "final_probability": prob,                 # (1,1,H,W) float32
        "final_binary": binary,                   # (1,1,H,W) uint8
        "task_id": task_id,
        "router_score": router,
        "safety_probability": safety,
        "state": state,
        "routing_decision": ("ROUTE_TO_REFINER" if state == "EXECUTE_THEN_ACCEPT"
                             else "KEEP_GLOBAL"),
        "safety_decision": "ACCEPT" if safety >= 0.5 else "REJECT",
        "shape": list(prob.shape),
        "evidence_class": SYNTHETIC,
    }


def _bias_from_family(shas: dict) -> float:
    """Family identity deterministically fixes the synthetic weights."""
    ordered = [shas[f"components/{c}.pt"] for c in "GRBS"]
    return sum(int(h[:8], 16) for h in ordered) / 1e12


def _components(tmp_path, tag: str):
    files = {}
    for name in "GRBS":
        p = tmp_path / f"{tag}-{name}.bin"
        p.write_bytes(f"SYNTHETIC_TEST_ONLY_{tag}_{name}".encode())
        files[name] = p
    return files, {k: A.digest(v) for k, v in files.items()}


def _config() -> dict:
    return dict(family="FULL", seed=42, protocol_sha256="a" * 64,
                source_sha256="b" * 64,
                preprocessing=dict(channels=3, resolution=512,
                                   implementation_sha256="c" * 64,
                                   contract_id="synthetic_fixture_v1"),
                roi_threshold=.30, segmentation_threshold=.50, safety_threshold=.50,
                router_numeric_dim=202, task_embedding_dim=16, router_total_dim=218,
                evidence_class=SYNTHETIC)


class PackagedSyntheticRuntime:
    """A package-loaded arm: verifies the package, then uses the SAME computation."""

    def __init__(self, root: Path, sha: str):
        self.manifest = A.verify(root, sha)  # package loading / corruption gate
        self.component_shas = {k: v["sha256"] for k, v in self.manifest["members"].items()
                               if k.startswith("components/")}
        assert set(self.component_shas) == {f"components/{c}.pt" for c in "GRBS"}
        self.bias = _bias_from_family(self.component_shas)
        self.calls = 0

    def __call__(self, image: torch.Tensor, task_id: int) -> dict:
        self.calls += 1
        return _record(image, task_id, self.bias)


class DirectSyntheticRuntime:
    def __init__(self, shas: dict):
        self.bias = _bias_from_family({f"components/{c}.pt": shas[c] for c in "GRBS"})

    def __call__(self, image: torch.Tensor, task_id: int) -> dict:
        return _record(image, task_id, self.bias)


@pytest.fixture
def arms(tmp_path):
    files, shas = _components(tmp_path, "A")
    root = tmp_path / "package"
    sha = A.package(root, files, shas, _config())
    return DirectSyntheticRuntime(shas), PackagedSyntheticRuntime(root, sha), (tmp_path, shas)


def _controls():
    torch.manual_seed(42)
    return [(torch.rand(1, 3, SIDE, SIDE), task) for task in range(4)]


# --------------------------------------------------------------------------- #
# Direct vs packaged parity across the full output contract
# --------------------------------------------------------------------------- #
def test_direct_vs_packaged_parity_on_all_output_contracts(arms):
    direct, packaged, _ = arms
    controls = _controls()
    result = validate_control_batch(direct, packaged, controls,
                                    device="cpu", warmup=1, repeats=3)
    assert result["parity"] == "BIT_EXACT"
    assert result["control_count"] == 4
    assert result["evidence_class"] == SYNTHETIC
    assert result["scientific_validation"] is False
    assert result["analytical_macs"] is None
    assert result["latency_seconds_mean"] > 0.0
    assert result["throughput_samples_per_second"] > 0.0
    assert result["peak_allocated_bytes"] is None  # CPU control batch

    for image, task in controls:
        a = direct(image.clone(), task)
        b = packaged(image.clone(), task)
        assert_exact(a, b)
        # shapes
        assert a["shape"] == [1, 1, SIDE, SIDE] == b["shape"]
        assert tuple(a["final_probability"].shape) == (1, 1, SIDE, SIDE)
        assert tuple(b["final_binary"].shape) == (1, 1, SIDE, SIDE)
        # probability maps
        assert torch.equal(a["final_probability"], b["final_probability"])
        assert torch.isfinite(a["final_probability"]).all()
        assert 0.0 <= float(a["final_probability"].min()) <= float(a["final_probability"].max()) <= 1.0
        # binary masks and the frozen 0.50 decision rule
        assert torch.equal(a["final_binary"], b["final_binary"])
        assert torch.equal(a["final_binary"],
                           (a["final_probability"] >= 0.50).to(torch.uint8))
        assert set(torch.unique(a["final_binary"]).tolist()) <= {0, 1}
        # task conditioning
        assert a["task_id"] == task == b["task_id"]
        # routing and safety decisions
        assert a["state"] == b["state"]
        assert a["routing_decision"] == b["routing_decision"]
        assert a["safety_decision"] == b["safety_decision"]
        assert a["router_score"] == b["router_score"]
        assert a["safety_probability"] == b["safety_probability"]


def test_task_conditioning_changes_outputs_but_parity_holds(arms):
    direct, packaged, _ = arms
    torch.manual_seed(7)
    image = torch.rand(1, 3, SIDE, SIDE)
    per_task = []
    for task in range(4):
        a = direct(image.clone(), task)
        b = packaged(image.clone(), task)
        assert_exact(a, b)
        per_task.append(a["final_probability"].clone())
        assert a["task_id"] == task
    assert not torch.equal(per_task[0], per_task[1])
    assert not torch.equal(per_task[1], per_task[2])
    assert not torch.equal(per_task[2], per_task[3])


def test_incompatible_family_breaks_parity_and_is_rejected(arms, tmp_path):
    direct, _, _ = arms
    files, shas = _components(tmp_path, "B")  # different synthetic family bytes
    root = tmp_path / "package_b"
    sha = A.package(root, files, shas, _config())
    other = PackagedSyntheticRuntime(root, sha)
    image = torch.zeros(1, 3, SIDE, SIDE)
    with pytest.raises(A.ArtifactError, match="tensor parity failure"):
        assert_exact(direct(image.clone(), 0), other(image.clone(), 0))
    with pytest.raises(A.ArtifactError):
        validate_control_batch(direct, other, [(image, 0)], warmup=0, repeats=1)


# --------------------------------------------------------------------------- #
# Is exact equality actually guaranteed?  NO — it is required, not guaranteed.
# --------------------------------------------------------------------------- #
def test_exact_equality_is_required_with_zero_numerical_tolerance():
    source = inspect.getsource(assert_exact)
    assert "torch.equal" in source and "np.array_equal" in source
    assert not any(token in source for token in ("allclose", "isclose", "atol", "rtol", "tol="))

    x = torch.linspace(0.0, 1.0, 16, dtype=torch.float32).reshape(1, 1, 4, 4)
    assert_exact({"prob": x}, {"prob": x.clone()})

    with pytest.raises(A.ArtifactError, match="tensor parity failure"):
        assert_exact({"prob": x}, {"prob": x + 1e-6})       # tiny precision drift
    with pytest.raises(A.ArtifactError, match="tensor parity failure"):
        assert_exact({"prob": x}, {"prob": x.half().float()})  # float16 round-trip
    with pytest.raises(A.ArtifactError, match="tensor type/dtype mismatch"):
        assert_exact({"prob": x}, {"prob": x.double()})
    with pytest.raises(A.ArtifactError, match="tensor parity failure"):
        assert_exact({"prob": x}, {"prob": x.reshape(1, 1, 2, 8)})
    with pytest.raises(A.ArtifactError, match="tensor parity failure"):
        assert_exact({"prob": x}, {"prob": x * float("nan")})
    with pytest.raises(A.ArtifactError, match="output keys differ"):
        assert_exact({"prob": x}, {"prob": x, "extra": 1.0})
    with pytest.raises(A.ArtifactError, match="scalar/decision mismatch"):
        assert_exact({"state": "ACCEPT"}, {"state": "REJECT"})
    with pytest.raises(A.ArtifactError, match="array parity failure"):
        assert_exact({"p": np.array([1.0], dtype=np.float32)},
                     {"p": np.array([1.000001], dtype=np.float32)})


def test_packaged_runtime_reuses_canonical_loader_not_a_reimplementation():
    source = inspect.getsource(RT.FullPackageRuntime)
    assert "FamilyBundle.load" in source
    assert "build_gtfree" in source
    assert "verify(root, expected_manifest_sha256)" in source
    # No separate inference implementation: the engine is the canonical one.
    assert "def infer" in source and "self.engine.infer" in source
    assert "torch.nn" not in source and "def forward" not in source
    # The package is byte-preserving, so both arms see identical weights.
    artifacts_source = inspect.getsource(A.package)
    assert "shutil.copyfileobj" in artifacts_source
    assert "source changed while packaging" in artifacts_source


def test_bit_exact_label_is_an_observation_not_a_guarantee(arms):
    direct, packaged, _ = arms
    result = validate_control_batch(direct, packaged, _controls()[:1],
                                    warmup=0, repeats=1)
    assert result["parity"] == "BIT_EXACT"
    assert result["scientific_validation"] is False
    # The label is emitted unconditionally on the observed control batch.
    batch_source = inspect.getsource(validate_control_batch)
    assert '"parity": "BIT_EXACT"' in batch_source
    assert "scientific_validation" in batch_source
    with pytest.raises(A.ArtifactError, match="nonempty controls"):
        validate_control_batch(direct, packaged, [])
    with pytest.raises(A.ArtifactError, match="invalid control image/task"):
        validate_control_batch(direct, packaged, [(torch.zeros(1, 3, SIDE, SIDE), 9)])


# --------------------------------------------------------------------------- #
# Real packaged runtime input contract (stubbed engine, no checkpoint loading)
# --------------------------------------------------------------------------- #
class _StubEngine:
    def infer(self, image, task_id):
        return _record(image, task_id, 0.0)


def _runtime_stub():
    obj = RT.FullPackageRuntime.__new__(RT.FullPackageRuntime)
    obj.engine = _StubEngine()
    return obj


def test_full_package_runtime_input_contract_is_fail_closed():
    runtime = _runtime_stub()
    good = torch.zeros(1, 3, 512, 512)
    record = runtime.infer(good, 0)
    assert tuple(record["final_probability"].shape) == (1, 1, 512, 512)

    with pytest.raises(A.ArtifactError, match="expected one RGB 512"):
        runtime.infer(torch.zeros(1, 3, SIDE, SIDE), 0)
    with pytest.raises(A.ArtifactError, match="expected one RGB 512"):
        runtime.infer(good, 4)
    with pytest.raises(A.ArtifactError, match="expected one RGB 512"):
        runtime.infer(good, True)       # bool is not an int task id
    with pytest.raises(A.ArtifactError, match="invalid image values"):
        runtime.infer(good * float("nan"), 0)
    with pytest.raises(A.ArtifactError, match="invalid image values"):
        runtime.infer(good + 2.0, 0)


def test_no_real_segmentation_accuracy_or_deployment_artifact_is_claimed(arms):
    _, packaged, (tmp_path, _) = arms
    assert packaged.manifest["deployment_authorized"] is False
    assert packaged.manifest["config"]["evidence_class"] == SYNTHETIC
    for name in "GRBS":
        assert (tmp_path / "package" / "components" / f"{name}.pt").read_bytes().startswith(
            b"SYNTHETIC_TEST_ONLY_")
    # No dice / accuracy key exists anywhere in the synthetic inference record.
    record = _record(torch.zeros(1, 3, SIDE, SIDE), 0, 0.0)
    assert not any(k in record for k in ("dice", "accuracy", "iou", "ground_truth", "mask_gt"))
