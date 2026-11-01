"""Stage 6 baseline real-data producer tests. Synthetic fixtures live in tmp dirs; real-data checks read TRAIN rows only."""
import copy
import hashlib
import json
import tempfile
from pathlib import Path

import pytest
import torch

from src.research.c3_baselines import experiment as C3
from src.research.stage6 import baseline_real as B
from src.research.stage6 import matrix as M

CUDA = torch.cuda.is_available()
requires_cuda = pytest.mark.skipif(not CUDA, reason="CUDA required")
DEV = "cuda" if CUDA else "cpu"


def _tmp():
    # Synthetic outputs must be outside the real run root.
    return Path(tempfile.mkdtemp(prefix="stage6_bl_"))


def _fit(model_key="UNET", seed=42, epochs=2, run_dir=None, resume=False):
    contract = B.make_contract(model_key, seed, device=DEV)
    train, val = C3.make_synthetic_loaders(seed)
    return contract, B.fit_baseline(contract, train, val, run_dir or _tmp(), real=False, device=DEV, resume=resume,
                                    max_epochs=epochs, base_channels=4)


def test_five_contracts_and_protocol_match_frozen_recipe():
    proto = json.loads((M.ROOT / "reports/planning/c1_film_attribution_v1/protocol.json").read_text())
    assert hashlib.sha256((M.ROOT / "reports/planning/c1_film_attribution_v1/protocol.json").read_bytes()).hexdigest() \
        .startswith("531e3eb2")
    assert proto
    for key in M.BASELINES:
        c = B.make_contract(key, 42, device=DEV)
        assert c["training_protocol"] == M.EXPECTED_TRAINING_PROTOCOL
        assert c["model_key"] == key and c["seed"] == 42
        assert len(c["contract_sha256"]) == 64 and c["evaluation_configuration"]


def test_real_run_fails_closed_without_grant():
    for grant in (None, object()):
        with pytest.raises(B.BaselineExecutionError):
            B.run_real_baseline("UNET", 42, grant=grant, device=DEV)


def test_synthetic_run_refused_under_real_root_and_real_override_refused():
    contract = B.make_contract("UNET", 42, device=DEV)
    train, val = C3.make_synthetic_loaders(42)
    with pytest.raises(B.BaselineExecutionError):
        B.fit_baseline(contract, train, val, M.RUN_ROOT / "pytest_forbidden", real=False, device=DEV, max_epochs=1)
    assert not (M.RUN_ROOT / "pytest_forbidden").exists()
    with pytest.raises(B.BaselineExecutionError):
        B.fit_baseline(contract, train, val, _tmp(), real=True, device=DEV, max_epochs=1)


@requires_cuda
@pytest.mark.parametrize("key", list(M.BASELINES))
def test_synthetic_cuda_one_step_each_baseline(key):
    _, manifest = _fit(key, epochs=1)
    assert manifest["real"] is False and manifest["completed_epochs"] == 1


@requires_cuda
def test_checkpoint_resume_is_exact():
    full_dir = _tmp()
    contract, _ = _fit("UNET", epochs=2, run_dir=full_dir)
    run = _tmp()
    _fit("UNET", epochs=1, run_dir=run)
    train, val = C3.make_synthetic_loaders(42)
    resumed = B.fit_baseline(contract, train, val, run, real=False, device=DEV, resume=True, max_epochs=2, base_channels=4)
    assert resumed["completed_epochs"] == 2
    load = lambda p: [json.loads(x) for x in (p / "history.jsonl").read_text().splitlines()]
    a, f = load(run), load(full_dir)
    assert [r["epoch"] for r in a] == [1, 2]
    assert a[1]["macro_domain_dice"] == pytest.approx(f[1]["macro_domain_dice"], abs=1e-4)
    assert a[1]["val_loss"] == pytest.approx(f[1]["val_loss"], rel=1e-3)


@requires_cuda
def test_resume_rejects_mismatches_and_unflagged_restart():
    run = _tmp()
    _fit("UNET", epochs=1, run_dir=run)
    train, val = C3.make_synthetic_loaders(42)
    with pytest.raises(B.BaselineExecutionError):
        B.fit_baseline(B.make_contract("UNET", 42, device=DEV), train, val, run, real=False, device=DEV, max_epochs=2)
    with pytest.raises(B.BaselineExecutionError):
        B.fit_baseline(B.make_contract("UNET", 123, device=DEV), train, val, run, real=False, device=DEV, resume=True,
                       max_epochs=2)
    with pytest.raises(B.BaselineExecutionError):
        B.fit_baseline(B.make_contract("UNETPP", 42, device=DEV), train, val, run, real=False, device=DEV, resume=True,
                       max_epochs=2)


def test_validator_rejects_synthetic_and_missing_cells():
    doc, reasons = M.validate_cell(_tmp(), "UNET", 42)
    assert doc is None and reasons


@requires_cuda
def test_synthetic_export_is_written_but_rejected_by_validator():
    contract, _ = _fit("UNET", epochs=1)
    model = C3.build_model("unet", base_channels=4).to(DEV).eval()
    samples = []
    for i, d in enumerate(B.DOMAIN_ORDER):
        samples.append({"image": torch.rand(1, 3, 64, 64), "mask": (torch.rand(64, 64) > 0.5).float(), "sample_id": f"SYN:{i}",
                        "domain": d, "task_id": i})
    out = _tmp()
    prov = {"model_key": "UNET", "seed": 42, "checkpoint_sha256": "0" * 64}
    B.export_cell(model, samples, out, model_key="UNET", seed=42, real=False, device=DEV, provenance=prov)
    doc, reasons = M.validate_cell(out, "UNET", 42)
    assert doc is None and reasons


def test_global_c1t_adapter_rejects_incomplete_manifest_and_synthetic_runs():
    ok, reasons = M.c1t_can_populate_global({"arm": "C1-T", "model_identity": "GlobalMedFiLM"})
    assert not ok and reasons
    from src.research.c1_film import train_driver as T
    run = _tmp() / "run"
    T.run_synthetic("C1-T", 42, run)
    with pytest.raises(Exception, match="SYNTHETIC_RUN_REJECTED"):
        B.global_manifest_from_c1(run, 42)
    manifest, _ = B.global_manifest_from_c1(run, 42, allow_synthetic=True)
    assert M.c1t_can_populate_global(manifest)[0]
    with pytest.raises(Exception):
        B.export_global_cell_from_c1(run, 42, _tmp(), iter(()), device=DEV)


def test_expected_protocol_equals_frozen_c1_recipe_fields():
    p = M.EXPECTED_TRAINING_PROTOCOL
    assert p["learning_rate"] == 1e-4 and p["weight_decay"] == 1e-4 and p["max_epochs"] == 100
    assert p["early_stop_patience"] == 15 and p["threshold"] == 0.5 and p["amp"] is True


@requires_cuda
@pytest.mark.parametrize("key", list(M.BASELINES))
def test_real_train_loader_forward_backward(key):
    r = B.loader_forward_backward_check(key, device=DEV)
    assert r["domains"] == ["ISIC", "BUSI", "KVASIR", "KUB"] and r["task_ids"] == [0, 1, 2, 3]
    assert r["image_shape"][1:] == [3, 512, 512] and r["mask_unique_values"] == [0.0, 1.0]
    assert r["finite_gradients"] and r["protected_splits_accessed"] == []
    assert not r["optimizer_step_taken"] and not r["checkpoint_written"]
