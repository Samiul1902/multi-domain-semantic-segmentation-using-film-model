"""RA-MedFiLM-BARR-Lite three-seed pipeline -- Phase B verification suite.

Covers the fourteen mandatory checks:

 1. the complete Lite graph instantiates at exactly 272,601 parameters
 2. G/R/B/S instantiate at the correct Lite / canonical architectures
 3. the three seed families are independent checkpoint families
 4. no trained weight is shared across seeds
 5. the refiner's fold isolation is real (and the OOF pass used the fold model)
 6. the router and safety labels are derived from this family's OOF labels
 7. the backbone-in-sample limitation is reported in machine-readable metadata
 8. checkpoint loading and dependency validation fail closed
 9. checkpoint resume is exact
10. every GT-free inference branch executes
11. CUDA forward/backward works and the peak memory is measured
12. synthetic prediction export is reproducible
13. missing / corrupt checkpoints behave as declared
14. unapproved real training remains blocked

Everything runs on a tiny synthetic population.  No real training happens, and a
synthetic artifact is never presented as a research result.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch

from src.models.barr.phase25_models import BARRBenefitRouterV1, BARRPostSafetyV1
from src.models.lite.ra_medfilm_barr_lite import (CANDIDATE_SPECS, LiteGlobalMedFiLM,
                                                  LiteRegionalRefiner,
                                                  count_unique_parameters)
from src.research.full_pipeline import recipe as R
from src.research.full_pipeline.provenance import (CHECKPOINT_SCHEMA,
                                                   FamilyCompatibilityError,
                                                   assert_compatible, load_checkpoint,
                                                   sha256_file)
from src.research.full_pipeline.seeds import SeedFamily, derived_seed
from src.research.lite_pipeline import recipe as L
from src.research.lite_pipeline import strict_oof
from src.research.lite_pipeline.cli import make_context
from src.research.lite_pipeline.context import LiteRunContext, lite_seed_family
from src.research.lite_pipeline.features import (LiteFeatureContractError,
                                                 assert_lite_tap_contract,
                                                 lite_feature_builder,
                                                 lite_feature_schema)
from src.research.lite_pipeline.inference import (STATES, LiteBundle, audit_lite_gt_free,
                                                  export_prediction, verify_all_branches)
from src.research.lite_pipeline.orchestrator import (AuthorizationRequired, DEPENDENCIES,
                                                     STAGE_ORDER,
                                                     assert_lite_families_isolated,
                                                     family_contract, plan, run_family,
                                                     verify_family)

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")

#: session-unique root: the pipeline treats an existing stage directory as
#: already-complete, so a shared root would silently skip stages on a re-run.
SYNTH_ROOT = R.ROOT / "runs" / f"lite_synthetic_test_{os.getpid()}"
TINY = dict(per_domain_dev=6, per_domain_val=3, per_domain_holdout=3)


# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def families() -> dict:
    """All three Lite seed families, fully trained on a synthetic population."""
    out = {}
    for seed in L.LITE_SEEDS:
        ctx = make_context(seed, root=SYNTH_ROOT / "runs", synthetic=True,
                           synth_root=SYNTH_ROOT, bounds=R.OperationalBounds.synthetic(),
                           **TINY)
        result = run_family(ctx, resume=False, log=lambda m: None)
        assert all(v["status"] == "COMPLETE" for v in result["stages"].values()), \
            f"seed {seed}: {result['stages']}"
        out[seed] = ctx
    return out


@pytest.fixture(scope="module")
def ctx42(families) -> LiteRunContext:
    return families[42]


# --------------------------------------------------------------------------- #
# 1. parameter identity
# --------------------------------------------------------------------------- #
def test_complete_graph_has_the_frozen_parameter_count():
    """272,601 unique parameters -- the number the whole claim rests on."""
    spec = CANDIDATE_SPECS[L.DEFAULT_VARIANT]
    total = count_unique_parameters(LiteGlobalMedFiLM(spec), LiteRegionalRefiner(spec),
                                    BARRBenefitRouterV1(), BARRPostSafetyV1())
    assert total == 272_601
    assert total == L.TOTAL_EXPECTED_PARAMETERS
    # the value that has no provenance anywhere in the repository
    assert total != 1_586_817


def test_component_counts_and_reduction_denominator():
    ident = L.parameter_identity()
    assert ident["components"] == {"G": 176_454, "R_psi": 58_129,
                                   "B_phi": 36_801, "S_omega": 1_217}
    # the reduction denominator is the FULL G+R+B+S family, not the FULL G alone
    assert ident["full_family_total_parameters"] == 4_837_420
    assert ident["full_global_only_parameters"] == 3_523_001
    assert abs(ident["reduction_percent_vs_full_family"] - 94.3647) < 1e-4
    assert abs(L.reduction_percent() - 94.3647) < 1e-4
    # the wrong denominator would give ~92.26%; guard against that regression
    wrong = 100.0 * (1 - 272_601 / 3_523_001)
    assert abs(wrong - 92.2620) < 1e-3
    assert abs(L.reduction_percent() - wrong) > 2.0


def test_variant_is_depthwise_compact_and_not_a_sibling():
    spec = L.spec()
    assert L.DEFAULT_VARIANT == "depthwise_compact"
    assert spec.variant_id == "ra_medfilm_barr_lite_depthwise_compact_v1"
    assert spec.block_kind == "depthwise"
    assert spec.global_channels == (12, 24, 48, 96, 128)
    # the two siblings must not be silently substituted
    assert count_unique_parameters(
        LiteGlobalMedFiLM(CANDIDATE_SPECS["width_compact"])) != 176_454
    assert count_unique_parameters(
        LiteGlobalMedFiLM(CANDIDATE_SPECS["ultralite_depthwise_add"])) != 176_454


# --------------------------------------------------------------------------- #
# 2. architectures
# --------------------------------------------------------------------------- #
def test_global_architecture_is_the_lite_backbone():
    model = LiteGlobalMedFiLM(L.spec())
    assert count_unique_parameters(model) == L.G_EXPECTED_PARAMETERS
    names = {n for n, _ in model.named_modules()}
    for tap in L.FEATURE_TAPS:
        assert tap in names, f"missing tap module {tap}"
    assert hasattr(model, "forward_with_features")
    # a global backbone must not embed the regional / routing machinery
    forbidden = ("localizer", "proposal", "roi", "regional", "refiner", "router")
    assert not [n for n in names if any(k in n.lower() for k in forbidden)]


def test_refiner_architecture_is_the_lite_refiner():
    model = LiteRegionalRefiner(L.spec())
    assert count_unique_parameters(model) == L.R_EXPECTED_PARAMETERS
    stem_conv = model.stem[0]
    assert stem_conv.in_channels == R.R_INPUT_CHANNELS == 4
    out = model(torch.zeros(2, 4, 256, 256))
    assert tuple(out.shape) == (2, 1, 256, 256)


def test_router_and_safety_are_the_canonical_phase25_models():
    """B_phi and S_omega must be the shared definitions, not Lite copies."""
    from src.research.full_pipeline.stages import router_stage, safety_stage
    assert router_stage.BARRBenefitRouterV1 is BARRBenefitRouterV1
    assert safety_stage.BARRPostSafetyV1 is BARRPostSafetyV1
    assert sum(p.numel() for p in BARRBenefitRouterV1().parameters()) == 36_801
    assert sum(p.numel() for p in BARRPostSafetyV1().parameters()) == 1_217


def test_lite_and_full_global_are_different_architectures():
    """A Lite G must never be constructible as, or confused with, a FULL G."""
    lite = LiteGlobalMedFiLM(L.spec())
    assert count_unique_parameters(lite) == 176_454
    assert R.G_EXPECTED_PARAMETERS == 3_523_001
    # the tap widths differ, which is why the FULL feature extractor refuses Lite
    with torch.no_grad():
        _, taps = lite.forward_with_features(torch.zeros(1, 3, 512, 512), torch.tensor([0]))
    assert taps["bridge"].shape[1] == L.LITE_NATIVE_CHANNELS["bridge"] == 128
    assert taps["decoder2"].shape[1] == L.LITE_NATIVE_CHANNELS["decoder2"] == 24
    assert taps["decoder1"].shape[1] == L.LITE_NATIVE_CHANNELS["decoder1"] == 12
    # grid sides match FULL, so the ROI->grid mapping is unchanged
    assert taps["bridge"].shape[-1] == L.LITE_FEATURE_GRID["bridge"] == 32
    assert taps["decoder2"].shape[-1] == L.LITE_FEATURE_GRID["decoder2"] == 256
    assert taps["decoder1"].shape[-1] == L.LITE_FEATURE_GRID["decoder1"] == 512


# --------------------------------------------------------------------------- #
# 3 + 4. seed families are independent
# --------------------------------------------------------------------------- #
def test_three_seed_families_are_isolated(families):
    out = assert_lite_families_isolated([families[s] for s in L.LITE_SEEDS])
    assert out["verdict"] == "LITE_SEED_FAMILIES_INDEPENDENT"
    assert out["n_families"] == 3
    assert out["collisions"] == []


def test_no_cross_seed_weight_sharing(families):
    digests = {}
    for seed in L.LITE_SEEDS:
        ctx = families[seed]
        digests[seed] = {
            "G": sha256_file(ctx.g_dir / "best.pt"),
            "R": sha256_file(ctx.r_dir / "final" / "final.pt"),
            "B": sha256_file(ctx.b_dir / "final" / "final.pt"),
            "S": sha256_file(ctx.s_dir / "final" / "final.pt"),
        }
    for component in ("G", "R", "B", "S"):
        values = [digests[s][component] for s in L.LITE_SEEDS]
        assert len(set(values)) == 3, f"{component} checkpoint reused across seeds"

    # initial weights must also differ: the seed namespace, not just the data,
    # separates the families
    states = []
    for seed in L.LITE_SEEDS:
        ck = load_checkpoint(families[seed].g_dir / "best.pt", component="G", seed=seed,
                             family="LITE")
        states.append(ck["model_state"])
    first = next(iter(states[0]))
    assert not torch.equal(states[0][first], states[1][first])


def test_lite_seed_streams_do_not_collide_with_full():
    for seed in L.LITE_SEEDS:
        for component in ("G", "CACHE", "R", "L", "B", "S"):
            lite = lite_seed_family(seed).run_seed(component, "main")
            full = SeedFamily(seed).run_seed(component, "main")
            assert lite != full, f"{component}/{seed}: Lite and FULL share a seed stream"
            assert lite == derived_seed(seed, component, "main", namespace="LITE")


def test_family_identity_is_stamped_into_every_checkpoint(families):
    ctx = families[42]
    for path, component in ((ctx.g_dir / "best.pt", "G"),
                            (ctx.r_dir / "final" / "final.pt", "R"),
                            (ctx.b_dir / "final" / "final.pt", "B"),
                            (ctx.s_dir / "final" / "final.pt", "S")):
        ck = torch.load(path, map_location="cpu", weights_only=False)
        assert ck["schema"] == CHECKPOINT_SCHEMA
        assert ck["family"] == "LITE"
        assert ck["component"] == component
        assert ck["seed"] == 42
        assert ck["test_reads"] == 0
        assert ck["router_holdout_reads"] == 0


def test_architecture_identity_is_stamped_into_g_and_r(families):
    ctx = families[42]
    g = load_checkpoint(ctx.g_dir / "best.pt", component="G", seed=42, family="LITE")
    assert g["architecture_id"] == ctx.g_architecture_id()
    assert L.checkpoint_architecture_sha256(g, block="g") == L.spec().sha256()
    r = load_checkpoint(ctx.r_dir / "final" / "final.pt", component="R", seed=42,
                        family="LITE")
    assert r["architecture_id"] == ctx.r_architecture_id()
    assert L.checkpoint_architecture_sha256(r, block="r") == L.spec().sha256()


# --------------------------------------------------------------------------- #
# 5. refiner fold isolation
# --------------------------------------------------------------------------- #
def test_refiner_fold_membership_is_disjoint_and_complete(ctx42):
    dev = set(ctx42.population.development_ids)
    seen = set()
    for k in R.R_OUTER_FOLDS:
        fit = set(pd.read_csv(ctx42.cache_dir / "folds" / f"fold{k}_fit.csv")["sample_id"].astype(str))
        es = set(pd.read_csv(ctx42.cache_dir / "folds" / f"fold{k}_early_stop.csv")["sample_id"].astype(str))
        ot = set(pd.read_csv(ctx42.cache_dir / "folds" / f"fold{k}_outer_target.csv")["sample_id"].astype(str))
        assert not (fit & es), f"fold{k}: fit and early_stop overlap"
        assert not (fit & ot), f"fold{k}: fit touches outer_target"
        assert not (es & ot), f"fold{k}: early_stop touches outer_target"
        assert (fit | es | ot) == dev, f"fold{k}: roles do not cover the population"
        assert not (ot & seen), f"fold{k}: outer targets overlap a previous fold"
        seen |= ot
    assert seen == dev


def test_oof_labels_were_produced_by_the_fold_specific_refiner(ctx42):
    """The label for a fold-k sample must carry fold-k's refiner digest."""
    labels = pd.read_csv(ctx42.l_dir / "labels.csv")
    labels["sample_id"] = labels["sample_id"].astype(str)
    fold_sha = {k: sha256_file(ctx42.r_dir / f"fold{k}" / "best.pt") for k in R.R_OUTER_FOLDS}
    assert len(set(fold_sha.values())) == 3, "the three fold refiners must be distinct"
    for k, expected in fold_sha.items():
        ot = set(pd.read_csv(ctx42.cache_dir / "folds" / f"fold{k}_outer_target.csv")
                 ["sample_id"].astype(str))
        rows = labels[labels["sample_id"].isin(ot)]
        assert len(rows) == len(ot)
        assert set(rows["fold_refiner_checkpoint_sha"]) == {expected}, \
            f"fold{k} labels were not produced by fold{k}'s refiner"
        assert set(rows["outer_fold"]) == {k}


def test_label_population_equals_router_development(ctx42):
    labels = pd.read_csv(ctx42.l_dir / "labels.csv")
    assert len(labels) == len(ctx42.population.development_ids)
    assert set(labels["sample_id"].astype(str)) == set(ctx42.population.development_ids)
    assert not labels["sample_id"].duplicated().any()
    # VAL and ROUTER_HOLDOUT must never be labelled
    assert not (set(labels["sample_id"].astype(str)) & set(ctx42.population.holdout_ids))


# --------------------------------------------------------------------------- #
# 6. router / safety labels
# --------------------------------------------------------------------------- #
def test_paired_gain_labels_follow_the_frozen_rule(ctx42):
    labels = pd.read_csv(ctx42.l_dir / "labels.csv")
    residual = np.abs(labels["delta_dice"]
                      - (labels["candidate_refined_dice"] - labels["global_dice"]))
    assert float(residual.max()) < 1e-9
    assert (labels["safety_target"].to_numpy()
            == (labels["delta_dice"] > 0).astype(int)).all()
    expected = np.where(labels["delta_dice"] >= R.LABEL_BENEFICIAL_DELTA, "BENEFICIAL",
                        np.where(labels["delta_dice"] <= R.LABEL_HARMFUL_DELTA,
                                 "HARMFUL", "NEUTRAL"))
    assert (labels["gain_category"].to_numpy() == expected).all()
    # forced-skip rows carry delta 0 by construction, not by imputation
    skipped = labels[~labels["action_available"].astype(bool)]
    assert (skipped["delta_dice"].abs() < 1e-12).all()


def test_router_features_are_202d_and_finite(ctx42):
    for domain in R.DATASET_ORDER:
        feats = np.load(ctx42.cache_dir / domain / "router_features.npy")
        assert feats.shape[1] == R.B_NUMERIC_DIM == 202
        meta = pd.read_csv(ctx42.cache_dir / domain / "meta.csv")
        available = meta["action_available"].astype(bool).to_numpy()
        if available.any():
            assert np.isfinite(feats[available]).all()
        # a forced-skip row is NaN, never a zero vector that could pass as real
        if (~available).any():
            assert np.isnan(feats[~available]).all()


def test_router_training_used_this_family_s_labels(ctx42):
    labels = pd.read_csv(ctx42.l_dir / "labels.csv")
    oof = pd.read_csv(ctx42.b_dir / "oof_predictions.csv")
    assert len(oof) == int(labels["action_available"].astype(bool).sum())
    assert np.isfinite(oof["delta_hat_oof"]).all()
    merged = oof.merge(labels[["sample_id", "delta_dice"]], on="sample_id",
                       suffixes=("", "_label"))
    assert np.allclose(merged["delta_dice"], merged["delta_dice_label"], atol=1e-12)
    record = json.loads((ctx42.b_dir / "run.json").read_text())
    assert record["final_checkpoint_sha256"] == sha256_file(ctx42.b_dir / "final" / "final.pt")
    assert record["artifact"] == "lite_barr_stage_B"


def test_safety_labels_and_features_are_family_derived(ctx42):
    feats = np.load(ctx42.l_dir / "safety_features.npy")
    meta = pd.read_csv(ctx42.l_dir / "safety_features_meta.csv")
    assert feats.shape == (len(meta), R.S_NUMERIC_DIM) == (len(meta), 16)
    assert np.isfinite(feats).all()
    labels = pd.read_csv(ctx42.l_dir / "labels.csv").set_index("sample_id")
    assert (meta["safety_target"].to_numpy()
            == labels.loc[meta["sample_id"], "safety_target"].to_numpy()).all()
    oof = pd.read_csv(ctx42.s_dir / "oof_safety_predictions.csv")
    assert np.isfinite(oof["safety_logit_oof"]).all()
    recomputed = 1.0 / (1.0 + np.exp(-oof["safety_logit_oof"].to_numpy()))
    assert np.allclose(recomputed, oof["safety_probability_oof"].to_numpy(), atol=1e-6)


def test_router_normalisation_is_fitted_per_lite_family(families):
    """No FULL statistic may be inherited; each family fits its own."""
    mus = {}
    for seed in (42, 123):
        ck = load_checkpoint(families[seed].b_dir / "final" / "final.pt", component="B",
                             seed=seed, family="LITE")
        mu = np.asarray(ck["normalizer_mu"], dtype=np.float64).reshape(-1)
        sigma = np.asarray(ck["normalizer_sigma"], dtype=np.float64).reshape(-1)
        assert mu.shape == (len(R.B_NORMALIZE_IDX),) == (8,)
        assert np.isfinite(mu).all() and np.isfinite(sigma).all()
        assert np.abs(mu).sum() > 0.0, "a zero normaliser would mean it was never fitted"
        assert list(ck["normalizer_index"]) == list(R.B_NORMALIZE_IDX)
        mus[seed] = mu
    # different backbones produce different feature distributions, so the fitted
    # statistics must differ -- reusing one family's normaliser would show up here
    assert not np.allclose(mus[42], mus[123], atol=1e-9)


# --------------------------------------------------------------------------- #
# 7. the OOF contract
# --------------------------------------------------------------------------- #
def test_oof_contract_declares_the_backbone_is_in_sample(ctx42):
    contract = json.loads((ctx42.l_dir / "manifest.json").read_text())["oof_contract"]
    assert contract["refiner_out_of_fold"] is True
    assert contract["router_out_of_fold"] is True
    assert contract["safety_out_of_fold"] is True
    assert contract["backbone_out_of_fold"] is False
    assert contract["backbone_sees_target_sample"] is True
    assert contract["not_fully_oof"] is True
    assert contract["family"] == "LITE"
    assert contract["label_generation_population"] == "ROUTER_DEVELOPMENT"
    assert contract["backbone_training_population"] == "TRAIN"
    assert contract["backbone_training_n"] == 5_832
    assert contract["validation_population_used_for_labels"] is False
    assert contract["test_population_reads"] == 0
    assert contract["outer_target_union_equals_label_population"] is True
    assert contract["group_keys_respect_outer_fold_boundary"] is True
    assert contract["straddling_group_keys"] == []
    assert contract["experimental_protocol_version"] == R.EXPERIMENTAL_PROTOCOL_VERSION
    assert contract["contract_version"] == "ra_medfilm_barr_oof_contract_v2"
    # the limitation must be stated, not merely implied by a boolean
    assert "optimistic" in contract["consequence"]
    assert "held-out" in contract["consequence"]


def test_oof_contract_records_fold_and_upstream_identity(ctx42):
    contract = json.loads((ctx42.l_dir / "manifest.json").read_text())["oof_contract"]
    assert contract["refiner_cross_fit_folds"] == 3
    assert contract["router_cross_fit_folds"] == 5
    upstream = contract["upstream_checkpoint_identity"]
    assert upstream["G"]["sha256"] == sha256_file(ctx42.g_dir / "best.pt")
    assert set(upstream["R_fold"]) == {"fold0", "fold1", "fold2"}
    for k, digest in upstream["R_fold"].items():
        assert digest == sha256_file(ctx42.r_dir / k / "best.pt")


def test_strict_oof_contract_is_declared_not_primary():
    contract = strict_oof.strict_oof_contract()
    assert contract["is_primary_construction"] is False
    assert contract["replaces_primary_construction"] is False
    assert contract["must_not_silently_replace_primary"] is True
    assert contract["protocol_version"] != R.EXPERIMENTAL_PROTOCOL_VERSION
    assert contract["real_training_performed"] is False
    assert contract["strict_oof_metric_available"] is False
    # and the primary contract says the same thing from its side
    assert contract["primary_construction_protocol_version"] == R.EXPERIMENTAL_PROTOCOL_VERSION


# --------------------------------------------------------------------------- #
# 8. dependency validation
# --------------------------------------------------------------------------- #
def test_dependency_graph_is_the_declared_dag():
    assert STAGE_ORDER == ("G", "CACHE", "R", "L", "B", "S")
    assert DEPENDENCIES == {"G": (), "CACHE": ("G",), "R": ("CACHE",),
                            "L": ("R", "CACHE"), "B": ("L",), "S": ("L", "R")}
    seen = []
    for stage in STAGE_ORDER:
        for dep in DEPENDENCIES[stage]:
            assert dep in seen, f"{stage} depends on {dep} which runs later"
        seen.append(stage)


def test_plan_reports_every_stage_complete(families):
    rows = plan(families[42])
    assert [r.name for r in rows] == list(STAGE_ORDER)
    assert all(r.status == "COMPLETE" for r in rows), [r.as_dict() for r in rows]


def test_full_family_chain_verifies(families):
    out = verify_family(families[42])
    assert out["verdict"] == "LITE_FAMILY_CHAIN_VERIFIED"
    assert out["family"] == "LITE"
    assert out["components"]["G"]["sha256"] == sha256_file(families[42].g_dir / "best.pt")
    assert out["components"]["L"]["backbone_out_of_fold"] is False
    assert out["components"]["R"]["upstream"] == {"G": out["components"]["G"]["sha256"]}


def test_lite_checkpoint_cannot_be_loaded_as_full(ctx42):
    ck = load_checkpoint(ctx42.g_dir / "best.pt", component="G", seed=42, family="LITE")
    with pytest.raises(FamilyCompatibilityError):
        assert_compatible(ck, component="G", seed=42, family="FULL")
    with pytest.raises(FamilyCompatibilityError):
        assert_compatible(ck, component="G", seed=123, family="LITE")
    with pytest.raises(FamilyCompatibilityError):
        assert_compatible(ck, component="R", seed=42, family="LITE")
    with pytest.raises(FamilyCompatibilityError):
        load_checkpoint(ctx42.g_dir / "best.pt", component="G", seed=42, family="FULL")


def test_router_cannot_consume_another_seed_s_refiner(families):
    ctx = families[123]
    r_sha = sha256_file(ctx.r_dir / "final" / "final.pt")
    ck = load_checkpoint(ctx.b_dir / "final" / "final.pt", component="B", seed=123,
                         family="LITE")
    other_r = sha256_file(families[42].r_dir / "final" / "final.pt")
    with pytest.raises(FamilyCompatibilityError):
        assert_compatible(ck, component="B", seed=123, family="LITE",
                          upstream={"G": ctx.g_sha(), "R": other_r})
    assert_compatible(ck, component="B", seed=123, family="LITE",
                      upstream={"G": ctx.g_sha(), "R": r_sha})


# --------------------------------------------------------------------------- #
# 9. exact resume
# --------------------------------------------------------------------------- #
def test_router_resume_is_exact(tmp_path, ctx42):
    """1 epoch + resume of 2 must equal 3 epochs straight through."""
    from src.research.full_pipeline.stages import router_stage

    merged = router_stage.load_family_inputs(ctx42)
    X = merged.attrs["vectors"]
    y = merged["delta_dice"].to_numpy(dtype=np.float32)
    t = merged["task_id"].to_numpy(dtype=np.int64)
    idx = np.arange(len(merged))

    straight_dir = tmp_path / "straight"
    split_dir = tmp_path / "split"

    straight = router_stage._train_one(
        ctx42, run_id="resume/straight", ckpt_dir=straight_dir, exp_dir=straight_dir,
        seed=7, fit_idx=idx, es_idx=idx[: max(1, len(idx) // 4)],
        ot_idx=idx[:1], X=X, y=y, t=t, epochs_target=3, early_stopping=True,
        resume=False, log=lambda m: None)

    first = router_stage._train_one(
        ctx42, run_id="resume/split", ckpt_dir=split_dir, exp_dir=split_dir,
        seed=7, fit_idx=idx, es_idx=idx[: max(1, len(idx) // 4)],
        ot_idx=idx[:1], X=X, y=y, t=t, epochs_target=1, early_stopping=True,
        resume=False, log=lambda m: None)
    resumed = router_stage._train_one(
        ctx42, run_id="resume/split", ckpt_dir=split_dir, exp_dir=split_dir,
        seed=7, fit_idx=idx, es_idx=idx[: max(1, len(idx) // 4)],
        ot_idx=idx[:1], X=X, y=y, t=t, epochs_target=3, early_stopping=True,
        resume=True, log=lambda m: None)

    assert first["record"]["epochs_completed"] == 1
    assert resumed["record"]["epochs_completed"] == 3
    assert straight["record"]["epochs_completed"] == 3

    def _hist(d):
        frame = pd.read_csv(Path(d) / "history.csv")
        # ``run`` is the run label, ``elapsed_seconds`` is wall-clock and
        # ``resume_count`` counts how often the run was interrupted; none of them
        # is part of the deterministic optimisation state
        return frame.drop(columns=["run", "elapsed_seconds", "resume_count"]
                          ).reset_index(drop=True)

    pd.testing.assert_frame_equal(_hist(straight_dir), _hist(split_dir),
                                  check_exact=False, rtol=1e-12, atol=1e-12)
    ck = load_checkpoint(split_dir / "latest.pt", component="B", seed=42, family="LITE")
    assert ck["selection"]["resume_count"] == 1
    assert ck["epoch"] == 3


# --------------------------------------------------------------------------- #
# 10. GT-free inference
# --------------------------------------------------------------------------- #
def test_all_four_inference_branches_execute():
    out = verify_all_branches()
    assert out["all_four_states_reached"] is True
    assert set(out["states"]) == {"forced_skip", "skip_global",
                                 "execute_accept", "execute_reject"}
    assert out["family"] == "LITE"


def test_lite_bundle_runs_gt_free_inference(ctx42):
    bundle = LiteBundle.load(ctx42, device="cpu")
    assert bundle.unique_parameters() == 272_601
    assert bundle.variant_id == L.spec().variant_id
    torch.manual_seed(0)
    image = torch.rand(1, 3, 512, 512)
    for task_id in range(4):
        res = bundle.infer(image, task_id, device="cpu")
        assert res["state"] in STATES
        prob = np.asarray(res["final_probability"])
        assert prob.shape == (512, 512)
        assert np.isfinite(prob).all()
        assert 0.0 <= float(prob.min()) and float(prob.max()) <= 1.0


def test_inference_uses_only_image_and_task_id():
    audit = audit_lite_gt_free()
    assert audit["gt_free"] is True, audit["gt_like_parameters"]
    assert audit["gt_like_parameters"] == []
    assert audit["infer_inputs"] == ["image", "task_id"]


def test_lite_inference_reads_its_own_normalisers(ctx42):
    """The router normaliser applied at inference must be this family's."""
    bundle = LiteBundle.load(ctx42, device="cpu")
    ck = load_checkpoint(ctx42.b_dir / "final" / "final.pt", component="B", seed=42,
                         family="LITE")
    assert np.allclose(np.asarray(bundle.router_state["normalizer_mu"]).reshape(-1),
                       np.asarray(ck["normalizer_mu"]).reshape(-1))
    engine = bundle.build_gtfree(device="cpu")
    assert engine.uses_tap_forward is True
    assert engine.feature_builder is lite_feature_builder


# --------------------------------------------------------------------------- #
# 11. CUDA forward / backward and memory
# --------------------------------------------------------------------------- #
@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA device unavailable")
def test_cuda_forward_backward_and_peak_memory():
    device = "cuda"
    spec = L.spec()
    report = {}

    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    g = LiteGlobalMedFiLM(spec).to(device)
    g.train()
    images = torch.rand(2, 3, 512, 512, device=device)
    tasks = torch.tensor([0, 1], device=device)
    logits, taps = g.forward_with_features(images, tasks)
    assert tuple(logits.shape) == (2, 1, 512, 512)
    loss = torch.nn.functional.binary_cross_entropy_with_logits(
        logits, (torch.rand_like(logits) > 0.5).float())
    loss.backward()
    grads = [p.grad for p in g.parameters() if p.grad is not None]
    assert grads and all(torch.isfinite(x).all() for x in grads)
    report["g_backbone_mib"] = torch.cuda.max_memory_allocated() / 2 ** 20
    del g, logits, taps, loss, grads
    torch.cuda.empty_cache()

    torch.cuda.reset_peak_memory_stats()
    r = LiteRegionalRefiner(spec).to(device)
    r.train()
    crops = torch.rand(2, 4, 256, 256, device=device)
    out = r(crops)
    torch.nn.functional.binary_cross_entropy_with_logits(
        out, (torch.rand_like(out) > 0.5).float()).backward()
    assert all(p.grad is None or torch.isfinite(p.grad).all() for p in r.parameters())
    report["r_refiner_mib"] = torch.cuda.max_memory_allocated() / 2 ** 20
    del r, out
    torch.cuda.empty_cache()

    props = torch.cuda.get_device_properties(0)
    report["device"] = props.name
    report["total_mib"] = props.total_memory / 2 ** 20
    report["torch"] = torch.__version__
    for key in ("g_backbone_mib", "r_refiner_mib"):
        assert report[key] > 0
        assert report[key] < report["total_mib"]
    print(f"\nCUDA peak memory: {report}")
    out_path = SYNTH_ROOT / "cuda_memory_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({k: (v if isinstance(v, str) else float(v))
                                    for k, v in report.items()}, indent=1),
                        encoding="utf-8")


def test_cuda_and_cpu_agree_within_tolerance(ctx42):
    """CPU and CUDA must agree on the *decision*, and closely on the map.

    The two paths are not bit-identical and cannot be: CUDA uses cuDNN kernels and
    the default CUDA path additionally runs the backbone under fp16 autocast
    (mirroring how the canonical caches were built).  Measured on this device the
    disagreement is ~8e-5 mean / ~2e-3 max without autocast and ~5e-4 mean /
    ~2e-2 max with it, with >= 99.8% of the binary mask identical.

    The gate is therefore placed on what the pipeline actually decides -- the
    four-state branch and the 0.50 binary mask -- plus the mean probability drift.
    A max-absolute gate is deliberately *not* used: the max is a thin tail of a
    few pixels sitting near the decision threshold, where a 1-ULP kernel
    difference is amplified, and it says nothing about the segmentation.
    """
    if not torch.cuda.is_available():
        pytest.skip("CUDA device unavailable")

    bundle = LiteBundle.load(ctx42, device="cpu")
    measured = {}
    for task_id in range(4):
        torch.manual_seed(task_id)
        image = torch.rand(1, 3, 512, 512)
        cpu = bundle.infer(image, task_id, device="cpu")

        engine = bundle.build_gtfree(device="cuda")
        engine.amp_global = False           # isolate device arithmetic from precision
        strict = engine.infer(image, task_id)
        amp = bundle.infer(image, task_id, device="cuda")

        p_cpu = np.asarray(cpu["final_probability"], dtype=np.float64)
        for name, other in (("cuda_fp32", strict), ("cuda_autocast", amp)):
            p_other = np.asarray(other["final_probability"], dtype=np.float64)
            delta = np.abs(p_cpu - p_other)
            agree = float(((p_cpu >= R.SEGMENTATION_OUTPUT_THRESHOLD)
                           == (p_other >= R.SEGMENTATION_OUTPUT_THRESHOLD)).mean())
            measured[f"task{task_id}/{name}"] = {
                "state_match": other["state"] == cpu["state"],
                "binary_agreement": agree,
                "mean_abs_delta": float(delta.mean()),
                "max_abs_delta": float(delta.max()),
            }
            assert other["state"] == cpu["state"], \
                f"task {task_id}: {name} reached {other['state']}, CPU reached {cpu['state']}"
            assert agree > 0.99, f"task {task_id}/{name}: binary agreement {agree:.4f}"
            assert float(delta.mean()) < 2e-3, \
                f"task {task_id}/{name}: mean |delta| {float(delta.mean()):.2e}"
        # the router must agree far more tightly than the pixel map
        assert abs(float(strict["router_score"]) - float(cpu["router_score"])) < 1e-3

    report = SYNTH_ROOT / "cpu_cuda_agreement.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(measured, indent=1), encoding="utf-8")
    print(f"\nCPU/CUDA agreement: {measured['task0/cuda_fp32']}")


# --------------------------------------------------------------------------- #
# 12. reproducible export
# --------------------------------------------------------------------------- #
def test_synthetic_export_is_reproducible(ctx42):
    bundle = LiteBundle.load(ctx42, device="cpu")
    torch.manual_seed(0)
    image = torch.rand(1, 3, 512, 512)
    first = export_prediction(bundle, image, 1, device="cpu")
    second = export_prediction(bundle, image, 1, device="cpu")
    assert first["probability_sha256"] == second["probability_sha256"]
    assert first["binary_sha256"] == second["binary_sha256"]
    assert first["state"] == second["state"]
    binary = first["final_binary"]
    expected = (np.asarray(first["final_probability"]) >= R.SEGMENTATION_OUTPUT_THRESHOLD)
    assert (binary.astype(bool) == expected).all()
    assert set(first["component_sha256"]) == {"G", "R", "B", "S"}
    # a different task id is a different prediction
    third = export_prediction(bundle, image, 3, device="cpu")
    assert third["task_id"] == 3


def test_export_record_carries_no_timestamp_or_path(ctx42):
    bundle = LiteBundle.load(ctx42, device="cpu")
    torch.manual_seed(0)
    record = export_prediction(bundle, torch.rand(1, 3, 512, 512), 0, device="cpu")
    forbidden = ("time", "date", "path", "created", "utc")
    assert not [k for k in record if any(f in k.lower() for f in forbidden)]


# --------------------------------------------------------------------------- #
# 13. missing / corrupt checkpoints
# --------------------------------------------------------------------------- #
def test_missing_checkpoint_raises(tmp_path):
    ctx = make_context(42, root=tmp_path / "absent", synthetic=True,
                       synth_root=SYNTH_ROOT, bounds=R.OperationalBounds.synthetic(),
                       **TINY)
    with pytest.raises(FileNotFoundError):
        LiteBundle.load(ctx, device="cpu")
    with pytest.raises(FileNotFoundError):
        ctx.g_sha()


def test_corrupt_checkpoint_raises(tmp_path, ctx42):
    corrupt = tmp_path / "corrupt.pt"
    corrupt.write_bytes(b"not a checkpoint at all")
    with pytest.raises(Exception) as excinfo:
        load_checkpoint(corrupt, component="G", seed=42, family="LITE")
    assert excinfo.type is not None

    truncated = tmp_path / "truncated.pt"
    truncated.write_bytes((ctx42.g_dir / "best.pt").read_bytes()[:512])
    with pytest.raises(Exception):
        load_checkpoint(truncated, component="G", seed=42, family="LITE")


def test_wrong_architecture_checkpoint_is_refused(tmp_path, ctx42):
    """A checkpoint whose stamped architecture is not this variant must be refused."""
    from src.research.lite_pipeline.stages import cache_lite

    ck = torch.load(ctx42.g_dir / "best.pt", map_location="cpu", weights_only=False)
    ck = dict(ck)
    ck["architecture_id"] = "ra_medfilm_barr_lite_ultralite_depthwise_add_v1::global"
    tampered = tmp_path / "G" / "best.pt"
    tampered.parent.mkdir(parents=True, exist_ok=True)
    torch.save(ck, tampered)

    ctx = make_context(42, root=tmp_path / "fake", synthetic=True,
                       synth_root=SYNTH_ROOT, bounds=R.OperationalBounds.synthetic(),
                       **TINY)
    ctx.g_dir.mkdir(parents=True, exist_ok=True)
    tampered.replace(ctx.g_dir / "best.pt")
    with pytest.raises(ValueError):
        cache_lite.load_lite_global(ctx, "cpu")


# --------------------------------------------------------------------------- #
# 14. real training stays blocked
# --------------------------------------------------------------------------- #
def test_real_training_without_a_grant_is_refused(tmp_path):
    from src.research.full_pipeline.population import load_canonical_population
    from src.research.lite_pipeline.context import make_lite_context

    ctx = make_lite_context(42, root=tmp_path / "real", bounds=R.OperationalBounds(),
                            population=load_canonical_population(), synthetic=False)
    with pytest.raises(AuthorizationRequired):
        run_family(ctx, grant=None, log=lambda m: None)
    # and the refusal must precede any training artifact
    assert not (ctx.g_dir / "best.pt").exists()


def test_grant_without_the_authorize_method_is_refused(tmp_path):
    from src.research.full_pipeline.population import load_canonical_population
    from src.research.lite_pipeline.context import make_lite_context

    class Useless:
        pass

    ctx = make_lite_context(42, root=tmp_path / "real2", bounds=R.OperationalBounds(),
                            population=load_canonical_population(), synthetic=False)
    with pytest.raises(AuthorizationRequired):
        run_family(ctx, grant=Useless(), log=lambda m: None)


def test_lite_real_contract_reuses_the_existing_grant_surface(tmp_path):
    from src.research.full_pipeline.population import load_canonical_population
    from src.research.lite_pipeline.context import make_lite_context

    seen = {}

    class Grant:
        def authorize_full_training(self, contract):
            seen.update(contract)

    ctx = make_lite_context(42, root=tmp_path / "real3", bounds=R.OperationalBounds(),
                            population=load_canonical_population(), synthetic=False)
    contract = family_contract(ctx)
    assert contract["family"] == "LITE"
    assert contract["real_training"] is True
    assert contract["synthetic"] is False
    # no new gate is invented: the same operator method is the one called
    Grant().authorize_full_training(dict(contract))
    assert seen["family"] == "LITE"


def test_synthetic_runs_are_stamped_and_not_evidence(families):
    manifest = json.loads((families[42].run_root / "manifest.json").read_text())
    assert manifest["synthetic"] is True
    assert manifest["protocol_faithful"] is False
    assert manifest["family"] == "LITE"
    assert manifest["model_identity"] == "RA-MedFiLM-BARR-Lite"
    assert manifest["real_training_started"] is False
    assert manifest["parameter_identity"]["total_unique_parameters"] == 272_601


# --------------------------------------------------------------------------- #
# feature interface
# --------------------------------------------------------------------------- #
def test_lite_feature_builder_produces_202d_from_real_taps(ctx42):
    g = LiteGlobalMedFiLM(L.spec()).eval()
    with torch.no_grad():
        _, taps = g.forward_with_features(torch.zeros(1, 3, 512, 512), torch.tensor([0]))
    cmaps = {k: v[0].numpy() for k, v in taps.items()}
    roi = {"clip_x1": 64, "clip_y1": 64, "clip_x2": 448, "clip_y2": 448,
           "crop_side_pixels": 384}
    p512 = np.full((512, 512), 0.6, dtype=np.float32)
    vec = lite_feature_builder(cmaps, p512, roi)
    assert vec.shape == (202,) and vec.dtype == np.float32
    assert np.isfinite(vec).all()
    schema = lite_feature_schema()
    assert schema["numeric_dim"] == 202
    assert schema["normalize_idx"] == list(R.B_NORMALIZE_IDX)
    assert schema["lite_native_channels"] == L.LITE_NATIVE_CHANNELS


def test_lite_feature_contract_rejects_full_width_taps():
    full_taps = {k: np.zeros((v, 32 if k == "bridge" else (256 if k == "decoder2" else 512),
                              32 if k == "bridge" else (256 if k == "decoder2" else 512)),
                             dtype=np.float32)
                 for k, v in L.FULL_NATIVE_CHANNELS.items()}
    with pytest.raises(LiteFeatureContractError):
        assert_lite_tap_contract(full_taps)
    lite_taps = {k: np.zeros((v, L.LITE_FEATURE_GRID[k], L.LITE_FEATURE_GRID[k]),
                             dtype=np.float32)
                 for k, v in L.LITE_NATIVE_CHANNELS.items()}
    assert_lite_tap_contract(lite_taps)          # must not raise


def test_frozen_full_feature_extractor_still_refuses_lite_taps():
    """The canonical extractor's width guard must not have been relaxed."""
    from src.features.barr_pre_refinement_features import extract_tap_features

    lite_taps = {k: np.zeros((v, L.LITE_FEATURE_GRID[k], L.LITE_FEATURE_GRID[k]),
                             dtype=np.float32)
                 for k, v in L.LITE_NATIVE_CHANNELS.items()}
    with pytest.raises(ValueError):
        extract_tap_features(lite_taps, (0, 0, 512, 512))


# --------------------------------------------------------------------------- #
# strict-OOF interface
# --------------------------------------------------------------------------- #
def test_strict_oof_folds_exclude_the_target_from_the_backbone(ctx42):
    folds = strict_oof.build_strict_folds(ctx42.population, seed=42,
                                          allow_derived=True)
    assert len(folds) == 3
    population = set(ctx42.population.development_ids)
    covered = set()
    for k, record in folds.items():
        assert not (set(record.target) & set(record.backbone_fit))
        assert set(record.refiner_fit) <= set(record.backbone_fit)
        assert set(record.refiner_early_stop) <= set(record.backbone_fit)
        assert set(record.target) | set(record.backbone_fit) == population
        assert record.backbone_checkpoint_sha256 is None
        covered |= set(record.target)
    assert covered == population


def test_strict_oof_rejects_a_leaky_assignment():
    with pytest.raises(strict_oof.StrictOOFError):
        strict_oof.StrictFoldRecord(
            fold=0, target=("a", "b"), backbone_fit=("b", "c"),
            refiner_fit=("c",), refiner_early_stop=("d",))
    # refiner training on something the backbone never saw is also refused
    with pytest.raises(strict_oof.StrictOOFError):
        strict_oof.StrictFoldRecord(
            fold=0, target=("a",), backbone_fit=("b", "c"),
            refiner_fit=("b", "z"), refiner_early_stop=("c",))
    # and an empty role is refused rather than silently accepted
    with pytest.raises(strict_oof.StrictOOFError):
        strict_oof.StrictFoldRecord(
            fold=0, target=("a",), backbone_fit=("b",),
            refiner_fit=("b",), refiner_early_stop=())


def test_strict_oof_requires_checkpoint_provenance():
    record = strict_oof.StrictFoldRecord(
        fold=1, target=("a",), backbone_fit=("b", "c"),
        refiner_fit=("b",), refiner_early_stop=("c",))
    with pytest.raises(strict_oof.StrictOOFError):
        strict_oof.assert_strict_checkpoint_provenance({"family": "LITE"}, record)
    good = {"strict_oof_protocol_version": strict_oof.STRICT_OOF_PROTOCOL_VERSION,
            "strict_oof_fold": 1,
            "strict_oof_backbone_fit_sha256": record.backbone_fit_sha256}
    assert strict_oof.assert_strict_checkpoint_provenance(
        good, record)["verdict"] == "STRICT_CHECKPOINT_PROVENANCE_PASS"
    wrong_population = dict(good)
    wrong_population["strict_oof_backbone_fit_sha256"] = "0" * 64
    with pytest.raises(strict_oof.StrictOOFError):
        strict_oof.assert_strict_checkpoint_provenance(wrong_population, record)
    wrong_fold = dict(good)
    wrong_fold["strict_oof_fold"] = 0
    with pytest.raises(strict_oof.StrictOOFError):
        strict_oof.assert_strict_checkpoint_provenance(wrong_fold, record)


def test_strict_oof_future_requirement_is_explicit():
    req = strict_oof.future_requirement()
    assert req["additional_backbone_trainings"] == 3 * len(L.LITE_SEEDS) == 9
    assert req["not_required_for_phase_b"] is True
    assert req["blocking_requirements"]


# --------------------------------------------------------------------------- #
# Stage 6 registry
# --------------------------------------------------------------------------- #
def test_stage6_registry_keeps_all_24_cells_missing():
    from src.research.stage6 import matrix as M

    assert M.LITE == "RA_MEDFILM_BARR_LITE_DEPTHWISE"
    assert len(M.MODEL_KEYS) == 8
    assert M.LITE in M.MODEL_KEYS
    cells = M.build_cells()
    assert len(cells) == 24
    assert all(c["status"] == "MISSING" for c in cells)
    assert sum(1 for c in cells if c["model_key"] == M.LITE) == 3
    # the Lite producer must be named, and must not claim a completed result
    entry = M.MODEL_REGISTRY[M.LITE]
    assert "lite_pipeline" in entry["producer"]
    assert "NOT_EXECUTED" in entry["multi_seed_producer"]
    assert entry["role"] == "SECONDARY_PROPOSED"
    assert entry["expected_parameters"] == 272_601
    assert M.MODEL_REGISTRY[M.FULL]["role"] == "PRIMARY_PROPOSED"
    # FULL and GLOBAL entries must be untouched by the Lite registration
    assert M.MODEL_REGISTRY[M.GLOBAL]["role"] == "INTERNAL_BACKBONE_REFERENCE"


def test_stage6_aggregate_reports_no_completed_lite_cell(tmp_path):
    from src.research.stage6 import matrix as M

    out = M.aggregate_stage6(runs_root=tmp_path, out=tmp_path / "agg.json")
    assert out["status"].startswith("INCOMPLETE_0_OF_24")
    lite_cells = [c for c in out["cells"] if c["model_key"] == M.LITE]
    assert len(lite_cells) == 3
    assert all(c["status"] == "MISSING" for c in lite_cells)
    assert out["superiority_claim_allowed"] is False
