"""Stage 6 baseline real-data producer tests. Synthetic fixtures live in tmp dirs; real-data checks read TRAIN rows only."""
import copy
import functools
import hashlib
import json
import shutil
import sys
import tempfile
import types
from pathlib import Path

import numpy as np
import pandas as pd
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
    run, scratch = _tmp() / "run", _tmp()
    T.run_synthetic("C1-T", 42, run)
    with pytest.raises(Exception, match="SYNTHETIC_RUN_REJECTED"):
        B.global_manifest_from_c1(run, 42, scratch)
    manifest, _ = B.global_manifest_from_c1(run, 42, scratch, allow_synthetic=True)
    # The export hash is that of the real per-image file and is never the checkpoint hash.
    export = Path(manifest["per_image_export_path"])
    assert manifest["per_image_export_sha256"] == hashlib.sha256(export.read_bytes()).hexdigest()
    assert manifest["per_image_export_sha256"] != manifest["checkpoint_sha256"]
    assert manifest["checkpoint_sha256"] == hashlib.sha256(Path(manifest["checkpoint_path"]).read_bytes()).hexdigest()
    assert manifest["mode"] == "SYNTHETIC_ONLY"
    with pytest.raises(B.BaselineExecutionError, match="synthetic"):
        B.export_global_cell_from_c1(run, 42, _tmp(), iter(()), device=DEV, allow_synthetic=True)
    with pytest.raises(Exception):
        B.export_global_cell_from_c1(run, 42, _tmp(), iter(()), device=DEV)


def test_c1t_manifest_rejects_checkpoint_hash_as_export_hash():
    base = {"arm": "C1-T", "model_identity": "GlobalMedFiLM", "protocol_sha256": M.PROTOCOL_SHA256, "train_n": 5832,
            "val_n": 808, "resolution": 512, "channel_policy": "RGB_3CH", "selection_rule": "phase20_macro_domain_mean_dice_v1",
            "threshold": 0.5, "seed": 42, "checkpoint_sha256": "a" * 64, "per_image_export_sha256": "b" * 64}
    assert M.c1t_can_populate_global(base) == (True, [])
    assert not M.c1t_can_populate_global({**base, "per_image_export_sha256": "a" * 64})[0]
    assert not M.c1t_can_populate_global({**base, "per_image_export_sha256": "xyz"})[0]


# --------------------------------------------------------------------------- mock GLOBAL artifacts (metadata roster only)
@functools.lru_cache(maxsize=1)
def _mock_records():
    rows = pd.read_csv(M.VAL_MANIFEST, usecols=["sample_id", "dataset", "task_id"])
    out = []
    for seed in (1, 2):
        rng, recs = np.random.default_rng(seed), []
        for r in rows.itertuples():
            gt = rng.random((8, 8)) > 0.5
            prob = np.where(rng.random((8, 8)) < 0.3, ~gt, gt).astype(float)
            recs.append(M.per_image_record(sample_id=str(r.sample_id), domain=str(r.dataset), final_prob=prob,
                                           global_prob=prob, mask=gt))
        out.append(recs)
    return out


def _mock_global(tmp: Path) -> dict:
    cell_recs, c1_recs = copy.deepcopy(_mock_records())
    for r, s in zip(cell_recs, pd.read_csv(M.VAL_MANIFEST, usecols=["task_id"]).itertuples()):
        r["task_id"] = int(s.task_id)
    summary = M.summarize_records(cell_recs, latency_ms=[1.0], peak_memory_mib=1.0, parameters=10)
    ckpt = tmp / "mock_c1t_epoch.pt"
    ckpt.write_bytes(b"mock checkpoint bytes - validator fixture, not a model")
    export = tmp / "scratch" / M.C1_EXPORT_NAME
    export_sha = B.write_c1_per_image_export(c1_recs, export)
    rows = M._read_per_image(export)
    dom, macro = M.recompute_domain_dice(rows)
    prov = {"model_key": M.GLOBAL, "seed": 42, "synthetic": False, "training_performed": True,
            "evidence_class": M.REAL_EVIDENCE_CLASS, "protocol_sha256": M.PROTOCOL_SHA256, "protected_splits_accessed": [],
            "val_manifest_sha256": hashlib.sha256(M.VAL_MANIFEST.read_bytes()).hexdigest(),
            "checkpoint_sha256": hashlib.sha256(ckpt.read_bytes()).hexdigest(), "checkpoint_path": str(ckpt),
            "evaluation_hardware": {"device": "mock"}, "evaluation_configuration": B.EVALUATION_CONFIGURATION,
            "training_protocol": copy.deepcopy(M.EXPECTED_TRAINING_PROTOCOL), "reused_artifact": "C1-T",
            "per_image_export_sha256": export_sha, "c1_selected_epoch_val_dice": dom, "c1_selected_epoch_macro_dice": macro}
    return {"records": cell_recs, "summary": summary, "prov": prov, "export": export, "ckpt": ckpt, "dir": tmp / "cell"}


def _write_mock(m: dict) -> Path:
    M.write_cell_result(m["dir"], model_key=M.GLOBAL, seed=42, records=m["records"], summary=m["summary"], provenance=m["prov"])
    shutil.copy2(m["export"], m["dir"] / M.C1_EXPORT_NAME)
    return m["dir"]


def _reasons(d: Path) -> list[str]:
    return M.validate_cell(d, M.GLOBAL, 42)[1]


def test_mock_global_cell_accepted_only_when_every_check_passes():
    d = _write_mock(_mock_global(_tmp()))
    assert _reasons(d) == []


def _tamper_export(m, d):
    with open(d / M.C1_EXPORT_NAME, "ab") as f:
        f.write(b"x")


def _delete_export(m, d):
    (d / M.C1_EXPORT_NAME).unlink()


def _hash_is_checkpoint(m, d):
    doc = json.loads((d / "cell_result.json").read_text())
    doc["provenance"]["per_image_export_sha256"] = doc["provenance"]["checkpoint_sha256"]
    (d / "cell_result.json").write_text(json.dumps(doc))


def _tamper_checkpoint(m, d):
    m["ckpt"].write_bytes(b"corrupted")


def _delete_checkpoint(m, d):
    m["ckpt"].unlink()


def _wrong_macro(m, d):
    doc = json.loads((d / "cell_result.json").read_text())
    doc["summary"]["equal_domain_macro_dice"] = min(1.0, doc["summary"]["equal_domain_macro_dice"] + 0.01)
    (d / "cell_result.json").write_text(json.dumps(doc))


def _wrong_domain_dice(m, d):
    doc = json.loads((d / "cell_result.json").read_text())
    doc["summary"]["per_domain"]["KUB"]["dice"] += 0.01
    (d / "cell_result.json").write_text(json.dumps(doc))


def _edited_rows_with_rehash(m, d):
    # An attacker rewrites a per-image Dice and re-hashes the CSV; the summary no longer matches.
    path = d / "per_image.csv"
    lines = path.read_text().splitlines()
    head = lines[0].split(",")
    cells = lines[1].split(",")
    cells[head.index("dice")] = "0.0" if float(cells[head.index("dice")]) > 0.5 else "1.0"
    lines[1] = ",".join(cells)
    path.write_text("\n".join(lines) + "\n")
    doc = json.loads((d / "cell_result.json").read_text())
    doc["per_image_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (d / "cell_result.json").write_text(json.dumps(doc))


def _incomplete_c1_roster(m, d):
    lines = (d / M.C1_EXPORT_NAME).read_text().splitlines()
    (d / M.C1_EXPORT_NAME).write_text("\n".join(lines[:-1]) + "\n")
    doc = json.loads((d / "cell_result.json").read_text())
    doc["provenance"]["per_image_export_sha256"] = hashlib.sha256((d / M.C1_EXPORT_NAME).read_bytes()).hexdigest()
    (d / "cell_result.json").write_text(json.dumps(doc))


def _synthetic_flag(m, d):
    doc = json.loads((d / "cell_result.json").read_text())
    doc["provenance"]["synthetic"] = True
    (d / "cell_result.json").write_text(json.dumps(doc))


def _not_c1(m, d):
    doc = json.loads((d / "cell_result.json").read_text())
    doc["provenance"]["reused_artifact"] = "historical"
    (d / "cell_result.json").write_text(json.dumps(doc))


@pytest.mark.parametrize("mutation", [_tamper_export, _delete_export, _hash_is_checkpoint, _tamper_checkpoint,
                                      _delete_checkpoint, _wrong_macro, _wrong_domain_dice, _edited_rows_with_rehash,
                                      _incomplete_c1_roster, _synthetic_flag, _not_c1])
def test_mock_global_cell_rejects_each_integrity_defect(mutation):
    m = _mock_global(_tmp())
    d = _write_mock(m)
    mutation(m, d)
    assert _reasons(d), mutation.__name__


def test_staged_publication_writes_nothing_unless_all_checks_pass():
    m = _mock_global(_tmp())
    cell = m["dir"]
    bad_prov = {**m["prov"], "per_image_export_sha256": m["prov"]["checkpoint_sha256"]}
    with pytest.raises(B.BaselineExecutionError, match="rejected before publication"):
        B._publish_validated(cell, M.GLOBAL, 42, m["records"], m["summary"], bad_prov, {M.C1_EXPORT_NAME: m["export"]})
    assert not (cell / "cell_result.json").exists() and not (cell.parent / f".{cell.name}.staging").exists()
    B._publish_validated(cell, M.GLOBAL, 42, m["records"], m["summary"], m["prov"], {M.C1_EXPORT_NAME: m["export"]})
    assert M.validate_cell(cell, M.GLOBAL, 42)[1] == []
    with pytest.raises(B.BaselineExecutionError, match="never overwritten"):
        B._publish_validated(cell, M.GLOBAL, 42, m["records"], m["summary"], m["prov"], {M.C1_EXPORT_NAME: m["export"]})


def test_c1_export_reload_detects_corruption_and_metric_disagreement():
    c1_recs = _mock_records()[1]
    path = _tmp() / M.C1_EXPORT_NAME
    sha = B.write_c1_per_image_export(c1_recs, path)
    assert sha == hashlib.sha256(path.read_bytes()).hexdigest()
    dom, macro = M.recompute_domain_dice(M._read_per_image(path))
    row = {**{f"val_dice_{d}": v for d, v in dom.items()}, "macro_domain_dice": macro}
    B.verify_c1_per_image_export(path, sha, row, check_roster=True)
    with pytest.raises(B.BaselineExecutionError, match="disagrees"):
        B.verify_c1_per_image_export(path, sha, {**row, "macro_domain_dice": macro + 0.01}, check_roster=True)
    with pytest.raises(B.BaselineExecutionError, match="hash mismatch"):
        B.verify_c1_per_image_export(path, "0" * 64, row, check_roster=True)
    path.write_bytes(path.read_bytes() + b"x\n")
    with pytest.raises(B.BaselineExecutionError):
        B.verify_c1_per_image_export(path, sha, row, check_roster=True)


# --------------------------------------------------------------------------- baseline CLI grant path
def _cli(args):
    import importlib.util
    spec = importlib.util.spec_from_file_location("stage6_cli", M.ROOT / "scripts" / "analysis" / "stage6_eight_model.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.main(args)


def _provider(monkeypatch, grant, name="stage6_fixture_gate"):
    mod = types.ModuleType(name)
    mod.provider = lambda: grant
    monkeypatch.setitem(sys.modules, name, mod)
    return f"{name}:provider"


class _FixtureGrant:
    def __init__(self, refuse=False):
        self.refuse, self.seen = refuse, []

    def authorize_baseline(self, contract):
        if self.refuse:
            raise RuntimeError("fixture grant refuses")
        self.seen.append(contract)


def test_cli_fails_closed_without_or_with_invalid_grant(monkeypatch, capsys):
    base = ["baseline-run", "--model", "UNET", "--seed", "42"]
    assert _cli(base) == 2 and "STAGE6_BASELINE_LAUNCH_GRANT_REQUIRED" in capsys.readouterr().err
    assert _cli([*base, "--grant-provider", "not_a_module_xyz:provider"]) == 2
    assert "UNRESOLVABLE" in capsys.readouterr().err
    assert _cli([*base, "--grant-provider", "malformed"]) == 2
    assert _cli([*base, "--grant-provider", _provider(monkeypatch, object())]) == 2
    assert "GRANT_INVALID" in capsys.readouterr().err
    assert _cli([*base, "--grant-provider", _provider(monkeypatch, _FixtureGrant(refuse=True))]) == 2
    assert "fixture grant refuses" in capsys.readouterr().err
    assert not (M.RUN_ROOT / "UNET" / "seed42").exists()


def _install_fixture_data(monkeypatch, tmp):
    """Redirect loaders, roster and run root to a tiny synthetic fixture; never touches real data or the real run root."""
    monkeypatch.setattr(B, "REAL_ROOT", tmp / "fixture_real_root")
    monkeypatch.setattr(M, "EXPECTED_TRAINING_PROTOCOL", {**M.EXPECTED_TRAINING_PROTOCOL, "max_epochs": 2})
    monkeypatch.setattr(B, "build_real_loaders", lambda seed, **kw: C3.make_synthetic_loaders(seed))
    samples = []
    for i, d in enumerate(B.DOMAIN_ORDER):
        g = torch.Generator().manual_seed(i)
        samples.append({"image": torch.rand(1, 3, 64, 64, generator=g), "mask": (torch.rand(64, 64, generator=g) > 0.5).float(),
                        "sample_id": f"FIXTURE:{d}", "domain": d, "task_id": i})
    roster = tmp / "fixture_val.csv"
    pd.DataFrame({"sample_id": [s["sample_id"] for s in samples], "dataset": [s["domain"] for s in samples],
                  "task_id": [s["task_id"] for s in samples]}).to_csv(roster, index=False)
    monkeypatch.setattr(M, "VAL_MANIFEST", roster)
    monkeypatch.setattr(B, "iter_real_val_samples", lambda: iter(samples))


@requires_cuda
def test_cli_with_approved_fixture_grant_reaches_trainer_checkpoints_and_resume(monkeypatch, capsys):
    tmp = _tmp()
    _install_fixture_data(monkeypatch, tmp)
    grant = _FixtureGrant()
    args = ["baseline-run", "--model", "UNET", "--seed", "42", "--grant-provider", _provider(monkeypatch, grant)]
    real_export = B.export_trained_baseline
    monkeypatch.setattr(B, "export_trained_baseline", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("interrupted")))
    assert _cli(args) == 2
    assert grant.seen and grant.seen[0]["model_key"] == "UNET" and grant.seen[0]["seed"] == 42
    run = tmp / "fixture_real_root" / "UNET" / "seed42" / "training"
    assert (run / "best.pt").is_file() and (run / "latest.pt").is_file() and (run / "run_manifest.json").is_file()
    assert _cli(args) == 2 and "existing run state found" in capsys.readouterr().err
    monkeypatch.setattr(B, "export_trained_baseline", real_export)
    assert _cli([*args, "--resume"]) == 0
    cell = tmp / "fixture_real_root" / "UNET" / "seed42"
    doc, reasons = M.validate_cell(cell, "UNET", 42)
    assert reasons == [] and doc["provenance"]["checkpoint_sha256"] == hashlib.sha256((run / "best.pt").read_bytes()).hexdigest()
    assert not (M.RUN_ROOT / "UNET" / "seed42").exists()


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
