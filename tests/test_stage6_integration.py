from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch
from torch import nn

from src.models.barr.regional_refiner import BARRRegionalRefinerV1
from src.models.lite.ra_medfilm_barr_lite import CANDIDATE_SPECS, LiteGlobalMedFiLM, LiteRegionalRefiner
from src.research.c3_baselines.full_system_smoke import _class_from_source
from src.research.stage6 import lite_chain as chain
from src.research.stage6 import matrix as M
from src.research.stage6.end_to_end import (GTFreeBARRInference, InferenceValidityError,
                                            audit_ground_truth_free)
from src.research.stage6.evaluate import evaluate_routed_system

ROOT = Path(__file__).resolve().parents[1]
SPEC = CANDIDATE_SPECS["depthwise_compact"]


def test_matrix_is_eight_models_by_three_seeds_all_missing(tmp_path):
    cells = M.build_cells()
    assert len(M.MODEL_KEYS) == 8 and len(cells) == 24
    assert M.MODEL_KEYS[0] == M.FULL and M.MODEL_REGISTRY[M.FULL]["role"] == "PRIMARY_PROPOSED"
    assert all(c["status"] == "MISSING" for c in cells)
    result = M.aggregate_stage6(tmp_path / "none", tmp_path / "out.json")
    assert result["status"] == "INCOMPLETE_0_OF_24"
    assert result["missing_cells"] == 24 and result["superiority_claim_allowed"] is False
    assert result["per_model"] == {}
    assert result["paired_full_vs_global"]["status"] == "NOT_AVAILABLE"


def test_c1t_global_reuse_requires_exact_compatibility():
    good = {"arm": "C1-T", "model_identity": "GlobalMedFiLM", "protocol_sha256": M.PROTOCOL_SHA256,
            "train_n": 5832, "val_n": 808, "resolution": 512, "channel_policy": "RGB_3CH",
            "selection_rule": "phase20_macro_domain_mean_dice_v1", "threshold": 0.5, "seed": 42,
            "checkpoint_sha256": "a" * 64, "per_image_export_sha256": "b" * 64}
    assert M.c1t_can_populate_global(good) == (True, [])
    for key in ("per_image_export_sha256", "checkpoint_sha256"):
        bad = {k: v for k, v in good.items() if k != key}
        assert not M.c1t_can_populate_global(bad)[0]
    assert not M.c1t_can_populate_global({**good, "arm": "C1-C"})[0]
    assert not M.c1t_can_populate_global({**good, "protected_splits_accessed": ["TEST1683"]})[0]


def test_inference_signature_is_ground_truth_free():
    audit = audit_ground_truth_free()
    assert audit["gt_free"] and audit["gt_like_parameters"] == []
    assert audit["infer_inputs"] == ["image", "task_id"]


class _StubG(nn.Module):
    """Hook-compatible stand-in so routing logic is exercised without trained weights."""

    def __init__(self, blob: bool):
        super().__init__()
        self.bridge, self.decoder2, self.decoder1 = nn.Conv2d(3, 256, 1), nn.Conv2d(3, 48, 1), nn.Conv2d(3, 24, 1)
        self.blob = blob

    def forward(self, image, task_ids):
        b = self.bridge(nn.functional.avg_pool2d(image, 16))
        self.decoder2(nn.functional.avg_pool2d(image, 4))
        self.decoder1(nn.functional.avg_pool2d(image, 2))
        logits = torch.full((1, 1, 512, 512), -6.0)
        if self.blob:
            logits[:, :, 180:330, 200:340] = 6.0
        return logits + 0 * b.sum()


def _states(blob=True, tau=-1.0, accept=0.0):
    router_cls = _class_from_source(ROOT / "scripts/analysis/train_phase25d_router.py", "BARRBenefitRouterV1", {})
    safety_cls = _class_from_source(ROOT / "scripts/analysis/phase25f_execution_common.py", "BARRPostSafetyV1",
                                    {"FEATURE_DIM": 20, "HIDDEN": (32, 16)})
    rs = {"normalizer_mu": np.zeros(8), "normalizer_sigma": np.ones(8), "normalizer_constant_mask": np.zeros(8, bool)}
    ss = {"normalizer_mu": np.zeros(16), "normalizer_sigma": np.ones(16), "normalizer_constant_mask": np.zeros(16, bool)}
    torch.manual_seed(0)
    return GTFreeBARRInference(global_model=_StubG(blob), refiner=BARRRegionalRefinerV1(), router=router_cls(),
                               safety=safety_cls(), router_state=rs, safety_state=ss, tau_c8=tau,
                               accept_threshold=accept)


def test_all_four_tasks_and_every_routing_state_without_ground_truth():
    image = torch.rand(1, 3, 512, 512)
    for task in range(4):
        out = _states().infer(image, task)
        assert out["state"] == "EXECUTE_THEN_ACCEPT" and out["final_probability"].shape == (512, 512)
    assert _states(blob=False).infer(image, 0)["state"] == "FORCED_SKIP"
    skip = _states(tau=1e9).infer(image, 1)
    assert skip["state"] == "SKIP_GLOBAL" and np.array_equal(skip["final_probability"], skip["global_probability"])
    system = _states(accept=1.1)
    rej = system.infer(image, 2)
    assert rej["state"] == "EXECUTE_THEN_REJECT" and np.array_equal(rej["final_probability"], rej["global_probability"])
    assert system.counters == {"global": 1, "router": 1, "refiner": 1, "safety": 1}
    with pytest.raises(InferenceValidityError):
        system.infer(image, 4)


def test_exporter_metrics_and_missing_cells_stay_missing(tmp_path):
    system = _states()
    rng = np.random.default_rng(0)
    samples = []
    for i, dom in enumerate(M.DOMAINS * 2):
        mask = np.zeros((512, 512), np.uint8)
        if i % 4:
            mask[180:330, 200:340] = 1
        samples.append({"sample_id": f"s{i}", "domain": dom, "task_id": M.TASK_IDS[dom],
                        "image": torch.from_numpy(rng.random((1, 3, 512, 512), dtype=np.float32)), "mask": mask})
    records, summary = evaluate_routed_system(system, samples, parameters=system.unique_parameters(), warmup=1)
    assert len(records) == 8 and summary["parameters"] == system.unique_parameters() > 1_000_000
    assert summary["router_execution_fraction"] == 1.0
    assert summary["latency_ms_p95"] >= summary["latency_ms_p50"] > 0
    empties = [r for r in records if r["gt_empty"]]
    assert all(r["empty_gt_false_positive"] for r in empties)
    assert summary["empty_mask_false_positive_rate"] == 1.0
    doc = M.write_cell_result(tmp_path / M.FULL / "seed42", model_key=M.FULL, seed=42, records=records,
                              summary=summary, provenance={"synthetic": True, "training_performed": False})
    cell, reasons = M.validate_cell(tmp_path / M.FULL / "seed42", M.FULL, 42)
    assert cell is None and "not a real trained run" in reasons and doc["evidence_label"] == M.EVIDENCE_LABEL
    agg = M.aggregate_stage6(tmp_path)
    assert agg["rejected_cells"] == 1 and agg["missing_cells"] == 23 and agg["per_model"] == {}


def test_summary_requires_all_four_domains():
    rec = {"domain": "ISIC", "dice": 1.0, "iou": 1.0, "precision": 1.0, "recall": 1.0, "hd95": None,
           "gt_empty": False, "empty_gt_false_positive": False, "refiner_executed": False,
           "accepted": False, "harmful_accepted": False}
    with pytest.raises(M.Stage6Error):
        M.summarize_records([rec])


def _loaders(spec_task_input):
    def make(epoch):
        g = torch.Generator().manual_seed(epoch)
        return [spec_task_input(g)]
    return make


def test_lite_chain_dependency_order_resume_and_family_rejection(tmp_path):
    torch.manual_seed(0)
    g_model = LiteGlobalMedFiLM(SPEC)

    def g_batch(gen):
        return {"image": torch.rand(2, 3, 64, 64, generator=gen), "task_id": torch.tensor([0, 1]),
                "mask": (torch.rand(2, 1, 64, 64, generator=gen) > 0.5).float(), "domain": ["ISIC", "BUSI"]}

    val = [g_batch(torch.Generator().manual_seed(9))]
    g_dir = tmp_path / "G"
    res = chain.train_segmentation_stage("G", g_model, SPEC, 42, g_dir, _loaders(g_batch), val, epochs=2,
                                         upstream_paths={}, synthetic=True)
    assert res["run_mode"] == "SYNTHETIC_ONLY" and (g_dir / "best.pt").is_file()
    with pytest.raises(chain.LiteChainError, match="BLOCKED"):
        chain.train_segmentation_stage("G", g_model, SPEC, 42, tmp_path / "x", _loaders(g_batch), val, epochs=1,
                                       upstream_paths={}, synthetic=False)

    r_model = LiteRegionalRefiner(SPEC)

    def r_batch(gen):
        return {"input": torch.rand(2, 4, 64, 64, generator=gen), "mask": (torch.rand(2, 1, 64, 64, generator=gen) > 0.5).float(),
                "domain": ["ISIC", "BUSI"]}

    r_dir = tmp_path / "R"
    chain.train_segmentation_stage("R_psi", r_model, SPEC, 42, r_dir, _loaders(r_batch), [r_batch(torch.Generator().manual_seed(3))],
                                   epochs=1, upstream_paths={"G": g_dir / "best.pt"}, synthetic=True)
    resumed = chain.train_segmentation_stage("R_psi", LiteRegionalRefiner(SPEC), SPEC, 42, r_dir, _loaders(r_batch),
                                             [r_batch(torch.Generator().manual_seed(3))], epochs=2,
                                             upstream_paths={"G": g_dir / "best.pt"}, synthetic=True, resume=True)
    assert resumed["epochs_completed"] == 2
    with pytest.raises(chain.LiteChainError, match="resume identity"):
        chain.train_segmentation_stage("R_psi", LiteRegionalRefiner(SPEC), SPEC, 123, r_dir, _loaders(r_batch),
                                       [r_batch(torch.Generator().manual_seed(3))], epochs=3,
                                       upstream_paths={"G": g_dir / "best.pt"}, synthetic=True, resume=True)

    router_cls = _class_from_source(ROOT / "scripts/analysis/train_phase25d_router.py", "BARRBenefitRouterV1", {})
    safety_cls = _class_from_source(ROOT / "scripts/analysis/phase25f_execution_common.py", "BARRPostSafetyV1",
                                    {"FEATURE_DIM": 20, "HIDDEN": (32, 16)})
    rng = np.random.default_rng(0)
    table = lambda n, w, y: {"x": rng.standard_normal((n, w)).astype(np.float32),
                             "task": rng.integers(0, 4, n).astype(np.int64), "y": y(n)}
    up = {"G": g_dir / "best.pt", "R_psi": r_dir / "best.pt"}
    chain.train_head_stage("B_phi", router_cls(), SPEC, 42, tmp_path / "B", fit=table(32, 202, lambda n: rng.normal(0, .05, n).astype(np.float32)),
                           early_stop=table(16, 202, lambda n: rng.normal(0, .05, n).astype(np.float32)),
                           upstream_paths=up, synthetic=True, max_epochs=3)
    up_s = {**up, "B_phi": tmp_path / "B" / "best.pt"}
    chain.train_head_stage("S_omega", safety_cls(), SPEC, 42, tmp_path / "S",
                           fit=table(32, 20, lambda n: (rng.random(n) > .5).astype(np.float32)),
                           early_stop=table(16, 20, lambda n: (rng.random(n) > .5).astype(np.float32)),
                           upstream_paths=up_s, synthetic=True, max_epochs=3)
    paths = {"G": g_dir / "best.pt", "R_psi": r_dir / "best.pt", "B_phi": tmp_path / "B" / "best.pt",
             "S_omega": tmp_path / "S" / "best.pt"}
    assert set(chain.validate_lite_chain(paths, SPEC, 42)) == set(chain.STAGES)

    # A FULL-family checkpoint (or a different upstream) must never load as Lite.
    full_like = tmp_path / "full.pt"
    torch.save({"model_state": LiteGlobalMedFiLM(SPEC).state_dict()}, full_like)
    with pytest.raises(chain.LiteChainError, match="FULL weights"):
        chain.load_stage_checkpoint(full_like, stage="G", model=LiteGlobalMedFiLM(SPEC), spec=SPEC, seed=42, upstream_paths={})
    with pytest.raises(chain.LiteChainError, match="upstream dependency hash"):
        chain.load_stage_checkpoint(r_dir / "best.pt", stage="R_psi", model=LiteRegionalRefiner(SPEC), spec=SPEC,
                                    seed=42, upstream_paths={"G": r_dir / "best.pt"})
    with pytest.raises(chain.LiteChainError):
        chain.save_stage_checkpoint(tmp_path / "bad.pt", stage="S_omega", model=safety_cls(), spec=SPEC, seed=42,
                                    upstream_sha256={"G": "0" * 64})


@pytest.mark.parametrize("device", ["cpu"] + (["cuda"] if torch.cuda.is_available() else []))
def test_lite_complete_graph_runs_end_to_end_without_ground_truth(device):
    from src.features.barr_lite_router_features import build_lite_feature_vector

    torch.manual_seed(0)
    full = _states()
    rs = {"normalizer_mu": np.zeros(8), "normalizer_sigma": np.ones(8), "normalizer_constant_mask": np.zeros(8, bool)}
    ss = {"normalizer_mu": np.zeros(16), "normalizer_sigma": np.ones(16), "normalizer_constant_mask": np.zeros(16, bool)}
    system = GTFreeBARRInference(global_model=LiteGlobalMedFiLM(SPEC), refiner=LiteRegionalRefiner(SPEC),
                                 router=full.b, safety=full.s, router_state=rs, safety_state=ss, tau_c8=-1.0,
                                 accept_threshold=0.0, device=device, feature_builder=build_lite_feature_vector,
                                 uses_tap_forward=True)
    image = torch.rand(1, 3, 512, 512)
    for task in range(4):
        out = system.infer(image, task)
        assert out["state"] == "EXECUTE_THEN_ACCEPT" and out["final_probability"].shape == (512, 512)
    assert system.unique_parameters() < 1_500_000


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA interpreter required")
def test_canonical_seed42_bundle_runs_end_to_end_on_cuda_without_ground_truth():
    try:
        system = GTFreeBARRInference.from_canonical_seed(42, device="cuda")
    except InferenceValidityError as exc:
        pytest.skip(str(exc))
    assert system.unique_parameters() == 4_837_420
    image = torch.rand(1, 3, 512, 512)
    for task in range(4):
        out = system.infer(image, task)
        assert out["state"] in ("FORCED_SKIP", "SKIP_GLOBAL", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT")
        assert out["final_probability"].shape == (512, 512)
    with pytest.raises(InferenceValidityError):
        GTFreeBARRInference.from_canonical_seed(123)
