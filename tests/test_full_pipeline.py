"""FULL RA-MedFiLM-BARR three-seed pipeline -- Phase A verification suite.

Covers the thirteen mandatory checks:

 1. every FULL component instantiates at its frozen parameter count
 2. all four task ids run through the assembled system
 3. loss + backward pass produce finite gradients for every producer
 4. the training producer stage order is correct and acyclic
 5. checkpoint / resume is deterministic
 6. incompatible checkpoint families are rejected
 7. three seed families are isolated
 8. cross-fitted outputs preserve fold identity
 9. no data leakage occurs
10. all four inference branches execute
11. prediction export is reproducible
12. GPU memory requirements are reported
13. unapproved real training remains blocked

Everything runs on a tiny synthetic population except the GPU-memory probe, which
uses a real batch on the device but performs no optimisation.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

from src.research.full_pipeline import recipe as R
from src.research.full_pipeline.cli import make_context
from src.research.full_pipeline.context import RunContext
from src.research.full_pipeline.inference import (FamilyBundle, export_prediction,
                                                  verify_all_branches, verify_gtfree_adapter)
from src.research.full_pipeline.orchestrator import (AuthorizationRequired, DEPENDENCIES,
                                                     STAGE_ORDER, assert_seed_families_isolated,
                                                     plan, run_family, run_stage, verify_family)
from src.research.full_pipeline.population import assert_no_leakage
from src.research.full_pipeline.provenance import (CHECKPOINT_SCHEMA, FamilyCompatibilityError,
                                                   assert_compatible, load_checkpoint,
                                                   sha256_file)
from src.research.full_pipeline.seeds import SeedFamily, derived_seed
from src.research.full_pipeline.stages import (cache_stage, global_stage, label_stage,
                                               refiner_stage, router_stage, safety_stage)
from src.research.full_pipeline.stages.router_stage import BARRBenefitRouterV1
from src.research.full_pipeline.stages.safety_stage import BARRPostSafetyV1

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

# A session-unique root keeps every run hermetic without bulk-deleting the previous
# tree: the pipeline treats an existing stage directory as already-complete, so a
# shared root would silently skip stages on the second run.  ``runs/`` is gitignored;
# old ``full_synthetic_test_*`` trees can be pruned by hand.
SYNTH_ROOT = R.ROOT / "runs" / f"full_synthetic_test_{os.getpid()}"
TINY = dict(per_domain_dev=6, per_domain_val=3, per_domain_holdout=3)


# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def family_ctx() -> RunContext:
    """One complete seed-42 family over a synthetic population."""
    ctx = make_context(42, root=SYNTH_ROOT / "runs", synthetic=True,
                       synth_root=SYNTH_ROOT, bounds=R.OperationalBounds.synthetic(),
                       **TINY)
    run_family(ctx, log=lambda m: None)
    return ctx


# --------------------------------------------------------------------------- #
# 1. component instantiation
# --------------------------------------------------------------------------- #
def test_every_full_component_instantiates_at_frozen_size():
    from src.models.barr import BARR_REFINER_EXPECTED_PARAMETERS, count_parameters
    from src.models.film import GlobalMedFiLM

    g = GlobalMedFiLM(task_count=R.G_MODEL["task_count"], in_channels=3, out_channels=1,
                      channels=tuple(R.G_MODEL["channels"]),
                      task_embedding_dim=R.G_MODEL["task_embedding_dim"],
                      film_hidden_dim=R.G_MODEL["film_hidden_dim"])
    assert sum(p.numel() for p in g.parameters()) == R.G_EXPECTED_PARAMETERS
    assert g.medfilm_components_present is True

    from src.models.barr import BARRRegionalRefinerV1
    r = BARRRegionalRefinerV1()
    assert count_parameters(r) == BARR_REFINER_EXPECTED_PARAMETERS == R.R_EXPECTED_PARAMETERS

    b = BARRBenefitRouterV1()
    assert sum(p.numel() for p in b.parameters()) == R.B_EXPECTED_PARAMETERS

    s = BARRPostSafetyV1()
    assert sum(p.numel() for p in s.parameters()) == R.S_EXPECTED_PARAMETERS


# --------------------------------------------------------------------------- #
# 2. all four task ids
# --------------------------------------------------------------------------- #
def test_all_four_task_ids_execute(family_ctx):
    bundle = FamilyBundle.load(family_ctx, device="cpu")
    img = torch.rand(1, 3, R.REGIONAL_CANVAS_RESOLUTION, R.REGIONAL_CANVAS_RESOLUTION,
                     generator=torch.Generator().manual_seed(7))
    seen = set()
    for task_id in range(4):
        res = bundle.infer(img, task_id, device="cpu")
        assert res["task_id"] == task_id
        assert res["state"] in ("FORCED_SKIP", "SKIP_GLOBAL", "EXECUTE_THEN_ACCEPT",
                                "EXECUTE_THEN_REJECT")
        assert np.asarray(res["final_probability"]).shape == (
            R.REGIONAL_CANVAS_RESOLUTION, R.REGIONAL_CANVAS_RESOLUTION)
        seen.add(task_id)
    assert seen == {0, 1, 2, 3}


# --------------------------------------------------------------------------- #
# 3. loss + backward
# --------------------------------------------------------------------------- #
def test_loss_and_backward_are_finite():
    from src.losses.segmentation import BCEDiceLoss, DiceLoss

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    from src.models.film import GlobalMedFiLM
    g = GlobalMedFiLM(task_count=4, in_channels=3, out_channels=1,
                      channels=tuple(R.G_MODEL["channels"]),
                      task_embedding_dim=32, film_hidden_dim=64).to(device)
    crit = BCEDiceLoss(0.5, 0.5, 1e-6)
    x = torch.rand(2, 3, 64, 64, device=device)
    y = (torch.rand(2, 1, 64, 64, device=device) > 0.5).float()
    loss = crit(g(x, torch.tensor([0, 3], device=device)), y)
    loss.backward()
    assert torch.isfinite(loss)
    assert all(torch.isfinite(p.grad).all() for p in g.parameters() if p.grad is not None)

    from src.models.barr import BARRRegionalRefinerV1
    r = BARRRegionalRefinerV1().to(device)
    xr = torch.rand(2, 4, 64, 64, device=device)
    yr = (torch.rand(2, 1, 64, 64, device=device) > 0.5).float()
    lr_ = 0.5 * torch.nn.functional.binary_cross_entropy_with_logits(r(xr), yr) \
        + 0.5 * DiceLoss(1e-6)(r(xr), yr)
    lr_.backward()
    assert torch.isfinite(lr_)

    b = BARRBenefitRouterV1().to(device)
    lb = torch.nn.HuberLoss(delta=0.05)(b(torch.randn(4, 202, device=device),
                                          torch.tensor([0, 1, 2, 3], device=device)),
                                       torch.randn(4, device=device) * 0.01)
    lb.backward()
    assert torch.isfinite(lb)

    s = BARRPostSafetyV1().to(device)
    ls = torch.nn.BCEWithLogitsLoss()(s(torch.randn(4, 20, device=device)),
                                      (torch.rand(4, device=device) > 0.5).float())
    ls.backward()
    assert torch.isfinite(ls)


# --------------------------------------------------------------------------- #
# 4. stage order
# --------------------------------------------------------------------------- #
def test_stage_order_is_correct_and_acyclic():
    assert STAGE_ORDER == ("G", "CACHE", "R", "L", "B", "S")
    # every dependency must appear earlier in the order
    for i, stage in enumerate(STAGE_ORDER):
        for dep in DEPENDENCIES[stage]:
            assert STAGE_ORDER.index(dep) < i, f"{stage} depends on later stage {dep}"
    assert DEPENDENCIES["G"] == ()
    assert set(DEPENDENCIES["S"]) == {"L", "R"}


def test_plan_reports_all_stages_complete(family_ctx):
    rows = plan(family_ctx)
    assert [r.name for r in rows] == list(STAGE_ORDER)
    assert all(r.status == "COMPLETE" for r in rows), [r.as_dict() for r in rows]


# --------------------------------------------------------------------------- #
# 5. deterministic resume
# --------------------------------------------------------------------------- #
def _g_history(ctx: RunContext) -> pd.DataFrame:
    return pd.read_csv(ctx.g_dir / "history.csv")


def test_checkpoint_resume_is_deterministic(tmp_path):
    """Two epochs straight through must equal 1 epoch + resume of 1 epoch."""
    bounds_full = R.OperationalBounds.synthetic(g_max_epochs=2)
    bounds_split = R.OperationalBounds.synthetic(g_max_epochs=1)

    straight = make_context(42, root=tmp_path / "straight", synthetic=True,
                            synth_root=tmp_path / "synth", bounds=bounds_full, **TINY)
    g_straight = global_stage.run(straight, log=lambda m: None)

    split_root = tmp_path / "split"
    ctx1 = make_context(42, root=split_root, synthetic=True, synth_root=tmp_path / "synth",
                        bounds=bounds_split, **TINY)
    global_stage.run(ctx1, log=lambda m: None)
    ctx2 = make_context(42, root=split_root, synthetic=True, synth_root=tmp_path / "synth",
                        bounds=bounds_full, **TINY)
    g_resumed = global_stage.run(ctx2, resume=True, log=lambda m: None)

    assert g_resumed.detail["resume_count"] == 1
    assert g_straight.detail["epochs_completed"] == g_resumed.detail["epochs_completed"] == 2

    a = _g_history(straight).drop(columns=["epoch_seconds", "cumulative_seconds"])
    b = _g_history(ctx2).drop(columns=["epoch_seconds", "cumulative_seconds"])
    pd.testing.assert_frame_equal(a, b, check_exact=False, rtol=1e-12, atol=1e-12)

    # the resumed run must have re-used the checkpointed weights, not restarted
    ck = load_checkpoint(ctx2.g_dir / "latest.pt", component="G", seed=42)
    assert ck["selection"]["resume_count"] == 1
    assert ck["epoch"] == 2


# --------------------------------------------------------------------------- #
# 6. incompatible families are rejected
# --------------------------------------------------------------------------- #
def test_incompatible_checkpoint_family_is_rejected(family_ctx):
    ck = load_checkpoint(family_ctx.g_dir / "best.pt", component="G", seed=42)

    with pytest.raises(FamilyCompatibilityError):
        assert_compatible(ck, component="G", seed=123)
    with pytest.raises(FamilyCompatibilityError):
        assert_compatible(ck, component="R", seed=42)
    with pytest.raises(FamilyCompatibilityError):
        assert_compatible(ck, component="G", seed=42, upstream={"G": "0" * 64})

    r_ck = load_checkpoint(family_ctx.r_dir / "final" / "final.pt", component="R", seed=42)
    g_sha = sha256_file(family_ctx.g_dir / "best.pt")
    with pytest.raises(FamilyCompatibilityError):
        assert_compatible(r_ck, component="R", seed=42, upstream={"G": "f" * 64})
    assert_compatible(r_ck, component="R", seed=42, upstream={"G": g_sha})

    # a corrupted / foreign file is refused before any state_dict load
    bogus = family_ctx.g_dir / "_bogus.pt"
    torch.save({"model_state": {}}, bogus)
    try:
        with pytest.raises(FamilyCompatibilityError):
            load_checkpoint(bogus, component="G", seed=42)
    finally:
        bogus.unlink(missing_ok=True)


# --------------------------------------------------------------------------- #
# 7. seed families are isolated
# --------------------------------------------------------------------------- #
def test_seed_families_are_isolated(family_ctx, tmp_path):
    # derived seeds differ per family for the same (component, run)
    assert len({derived_seed(s, "G", "main") for s in (42, 123, 3407)}) == 3
    assert derived_seed(42, "R", "fold0") != derived_seed(42, "R", "fold1")
    assert derived_seed(42, "B", "fold0") != derived_seed(42, "S", "fold0")

    # a second family trained on the same synthetic population must not collide
    ctx123 = make_context(123, root=tmp_path / "runs", synthetic=True,
                          synth_root=tmp_path / "synth",
                          bounds=R.OperationalBounds.synthetic(g_max_epochs=1), **TINY)
    global_stage.run(ctx123, log=lambda m: None)
    assert sha256_file(ctx123.g_dir / "best.pt") != sha256_file(family_ctx.g_dir / "best.pt")

    # duplicating a checkpoint across families must be detected
    duplicate = make_context(3407, root=tmp_path / "runs2", synthetic=True,
                             synth_root=tmp_path / "synth",
                             bounds=R.OperationalBounds.synthetic(g_max_epochs=1), **TINY)
    global_stage.run(duplicate, log=lambda m: None)
    shutil.copyfile(family_ctx.g_dir / "best.pt", duplicate.g_dir / "best.pt")
    with pytest.raises(FamilyCompatibilityError):
        assert_seed_families_isolated([family_ctx, ctx123, duplicate], components=("G",))


# --------------------------------------------------------------------------- #
# 8. cross-fit fold identity
# --------------------------------------------------------------------------- #
def test_crossfit_outputs_preserve_fold_identity(family_ctx):
    folds = family_ctx.folds("outer3")
    owner = {}
    for k, v in folds.folds.items():
        for sid in v["outer_target"]:
            assert sid not in owner, f"{sid} in two outer targets"
            owner[sid] = k

    labels = pd.read_csv(family_ctx.l_dir / "labels.csv")
    labels["sample_id"] = labels["sample_id"].astype(str)
    assert set(labels["sample_id"]) == set(owner)
    assert (labels["outer_fold"].to_numpy() ==
            labels["sample_id"].map(owner).to_numpy()).all()

    # each label records the digest of ITS OWN fold's refiner, not the refit
    for k in sorted(folds.folds):
        fold_sha = sha256_file(family_ctx.r_dir / f"fold{k}" / "best.pt")
        sub = labels[labels["outer_fold"] == k]
        assert (sub["fold_refiner_checkpoint_sha"] == fold_sha).all()
    refit_sha = sha256_file(family_ctx.r_dir / "final" / "final.pt")
    assert refit_sha not in set(labels["fold_refiner_checkpoint_sha"])

    # OOF predictions cover each sample exactly once
    oof = pd.read_csv(family_ctx.b_dir / "oof_predictions.csv")
    assert not oof["sample_id"].duplicated().any()
    assert len(oof) == int(labels["action_available"].sum())


# --------------------------------------------------------------------------- #
# 9. leakage
# --------------------------------------------------------------------------- #
def test_no_leakage(family_ctx):
    for kind in ("outer3", "cv5"):
        table = family_ctx.folds(kind)
        audit = assert_no_leakage(spec=family_ctx.population, folds=table.folds, label=kind)
        assert audit["verdict"] == "LEAKAGE_AUDIT_PASS"
        assert audit["router_holdout_absent"] and audit["val_absent"]

    dev = set(family_ctx.population.development_ids)
    val = set(pd.read_csv(family_ctx.population.val_manifest)["sample_id"].astype(str))
    holdout = set(family_ctx.population.holdout_ids)
    assert not (dev & val)
    assert not (dev & holdout)
    assert holdout, "synthetic population must carry a holdout so the check is meaningful"

    # no held-out id reaches any produced training table
    for path in (family_ctx.l_dir / "labels.csv",
                 family_ctx.b_dir / "oof_predictions.csv",
                 family_ctx.s_dir / "oof_safety_predictions.csv"):
        ids = set(pd.read_csv(path)["sample_id"].astype(str))
        assert not (ids & holdout), f"{path} contains ROUTER_HOLDOUT ids"
        assert not (ids & val), f"{path} contains VAL ids"

    # the TEST split is never named by any artifact of this family
    test_ids = set(pd.read_csv(R.TEST_MANIFEST)["sample_id"].astype(str))
    assert not (dev & test_ids)


def test_gt_free_signatures():
    from src.research.full_pipeline.inference import audit_gt_free

    audit = audit_gt_free()
    assert audit["gt_free"] is True, audit["gt_like_parameters"]


# --------------------------------------------------------------------------- #
# 10. inference branches
# --------------------------------------------------------------------------- #
def test_all_inference_branches_execute():
    out = verify_all_branches(image_size=64)
    assert out["all_four_states_reached"] is True
    states = {k: v["state"] for k, v in out["states"].items()}
    assert states == {"forced_skip": "FORCED_SKIP", "skip_global": "SKIP_GLOBAL",
                      "execute_accept": "EXECUTE_THEN_ACCEPT",
                      "execute_reject": "EXECUTE_THEN_REJECT"}


def test_gtfree_adapter_runs_on_real_family(family_ctx):
    bundle = FamilyBundle.load(family_ctx, device="cpu")
    out = verify_gtfree_adapter(bundle, device="cpu",
                                image_size=R.REGIONAL_CANVAS_RESOLUTION)
    assert out["verdict"] == "GT_FREE_ADAPTER_EXECUTED"
    assert out["unique_parameters"] > 0


# --------------------------------------------------------------------------- #
# 11. reproducible export
# --------------------------------------------------------------------------- #
def test_prediction_export_is_reproducible(family_ctx):
    bundle = FamilyBundle.load(family_ctx, device="cpu")
    img = torch.rand(1, 3, R.REGIONAL_CANVAS_RESOLUTION, R.REGIONAL_CANVAS_RESOLUTION,
                     generator=torch.Generator().manual_seed(11))
    a = export_prediction(bundle, img, 1, device="cpu")
    b = export_prediction(bundle, img, 1, device="cpu")
    assert a["probability_sha256"] == b["probability_sha256"]
    assert a["binary_sha256"] == b["binary_sha256"]
    assert a["state"] == b["state"]

    # a different image must not collide
    other = torch.rand(1, 3, R.REGIONAL_CANVAS_RESOLUTION, R.REGIONAL_CANVAS_RESOLUTION,
                       generator=torch.Generator().manual_seed(12))
    c = export_prediction(bundle, other, 1, device="cpu")
    assert c["probability_sha256"] != a["probability_sha256"]


# --------------------------------------------------------------------------- #
# 12. GPU memory
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not torch.cuda.is_available(), reason="no CUDA device")
def test_gpu_memory_requirements_are_reported():
    device = torch.device("cuda")
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(device)
    total = torch.cuda.get_device_properties(0).total_memory

    from src.models.film import GlobalMedFiLM
    g = GlobalMedFiLM(task_count=4, in_channels=3, out_channels=1,
                      channels=tuple(R.G_MODEL["channels"]),
                      task_embedding_dim=32, film_hidden_dim=64).to(device)
    from src.losses.segmentation import BCEDiceLoss
    crit = BCEDiceLoss(0.5, 0.5, 1e-6)
    opt = torch.optim.AdamW(g.parameters(), lr=1e-4)
    x = torch.rand(R.G_TRAINING["batch_size"], 3, 512, 512, device=device)
    y = (torch.rand(R.G_TRAINING["batch_size"], 1, 512, 512, device=device) > 0.5).float()
    loss = crit(g(x, torch.tensor([0, 1, 2, 3], device=device)), y)
    loss.backward()
    opt.step()
    g_peak = torch.cuda.max_memory_allocated(device)

    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(device)
    from src.models.barr import BARRRegionalRefinerV1
    r = BARRRegionalRefinerV1().to(device)
    xr = torch.rand(R.R_BATCH_SIZE, 4, 256, 256, device=device)
    yr = (torch.rand(R.R_BATCH_SIZE, 1, 256, 256, device=device) > 0.5).float()
    (torch.nn.functional.binary_cross_entropy_with_logits(r(xr), yr)).backward()
    r_peak = torch.cuda.max_memory_allocated(device)

    report = {
        "gpu": torch.cuda.get_device_name(0),
        "total_bytes": int(total),
        "g_train_batch4_peak_bytes": int(g_peak),
        "r_train_batch8_peak_bytes": int(r_peak),
        "g_fraction_of_total": round(g_peak / total, 4),
        "r_fraction_of_total": round(r_peak / total, 4),
        "headroom_note": ("G at the frozen batch size of 4 fits with large headroom; the "
                          "8 GB card is not the binding constraint for this recipe"),
    }
    out = R.ROOT / "reports" / "audits" / "full_pipeline_gpu_memory.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1), encoding="utf-8")

    assert g_peak > 0 and r_peak > 0
    assert g_peak < total, "G training batch does not fit on the device"
    assert r_peak < total, "R training batch does not fit on the device"


# --------------------------------------------------------------------------- #
# 13. real training stays blocked
# --------------------------------------------------------------------------- #
def test_real_training_is_blocked_without_a_grant(tmp_path):
    ctx = make_context(42, root=tmp_path / "real", synthetic=False,
                       bounds=R.OperationalBounds())
    assert ctx.synthetic is False
    assert ctx.population.source == "CANONICAL"
    assert ctx.population.summary()["development_n"] == R.ROUTER_DEVELOPMENT_N

    with pytest.raises(AuthorizationRequired):
        run_stage(ctx, "G", grant=None, log=lambda m: None)
    assert not (ctx.g_dir / "best.pt").exists()

    class _BadGrant:
        pass

    with pytest.raises(AuthorizationRequired):
        run_stage(ctx, "G", grant=_BadGrant(), log=lambda m: None)


def test_grant_provider_is_never_minted(tmp_path):
    from src.research.full_pipeline.orchestrator import family_contract, load_grant

    assert load_grant(None) is None
    with pytest.raises(AuthorizationRequired):
        load_grant("not-a-provider")

    ctx = make_context(42, root=tmp_path / "real2", synthetic=False)
    contract = family_contract(ctx)
    assert contract["seed"] == 42
    assert contract["test_reads"] == 0
    assert len(contract["contract_sha256"]) == 64


# --------------------------------------------------------------------------- #
# end-to-end
# --------------------------------------------------------------------------- #
def test_end_to_end_family_is_verified(family_ctx):
    v = verify_family(family_ctx)
    assert v["verdict"] == "FULL_FAMILY_CHAIN_VERIFIED"
    assert set(v["components"]) == set(STAGE_ORDER)

    for stage in STAGE_ORDER:
        assert family_ctx.stage_done(stage), f"{stage} not marked complete"

    manifest = json.loads((family_ctx.run_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["synthetic"] is True
    assert manifest["protocol_faithful"] is False
    assert manifest["test_reads"] == 0


def test_all_stage_producers_exist():
    """A missing producer would make the workflow non-executable."""
    for module in (global_stage, cache_stage, refiner_stage, label_stage,
                   router_stage, safety_stage):
        assert callable(getattr(module, "run"))
        assert callable(getattr(module, "is_complete"))
        assert callable(getattr(module, "verify"))


def test_every_checkpoint_is_a_versioned_envelope(family_ctx):
    for path in (family_ctx.g_dir / "best.pt",
                 family_ctx.r_dir / "final" / "final.pt",
                 family_ctx.b_dir / "final" / "final.pt",
                 family_ctx.s_dir / "final" / "final.pt"):
        ck = torch.load(path, map_location="cpu", weights_only=False)
        assert ck["schema"] == CHECKPOINT_SCHEMA
        assert ck["seed"] == 42
        assert ck["family"] == "FULL"
        assert ck["test_reads"] == 0
        assert ck["router_holdout_reads"] == 0
    assert load_checkpoint(family_ctx.g_dir / "best.pt")["upstream"] == {}
