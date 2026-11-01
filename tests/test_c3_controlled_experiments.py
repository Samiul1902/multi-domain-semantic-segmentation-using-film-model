from __future__ import annotations

import gc
import json
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image
from torch import nn

from src.data.transforms import SegmentationTransform
from src.research.c3_baselines import experiment as C3


def test_frozen_population_metadata_and_seed_scope():
    result = C3.validate_manifest_contract()
    assert result["train_n"] == 5832
    assert result["val_n"] == 808
    assert result["train_val_overlap"] == 0
    assert set(result["val_domains"]) == {"ISIC", "BUSI", "KVASIR", "KUB"}
    for seed in C3.EXPECTED_SEEDS:
        config = C3.build_experiment_config("unet", seed)
        assert config["seed"] == seed
        assert config["dataset"]["test_access"] is False
        assert config["dataset"]["external_access"] is False
        assert config["protocol"]["sha256"] == C3.EXPECTED_PROTOCOL_SHA256
        assert config["recipe"]["resolution"] == 512
        assert config["recipe"]["channels"] == 3
        full = C3.build_experiment_config(C3.FULL_MODEL_KEY, seed)
        assert full["role"] == "PRIMARY_PROPOSED_METHOD"
        assert full["model"]["display_name"] == "RA-MedFiLM-BARR (FULL)"
        assert full["component_dependencies"]["global_backbone_seed"] == seed
        assert full["existing_phase29_evidence"]["counts_as_end_to_end_c3_cell"] is False
    with pytest.raises(C3.C3ExecutionError):
        C3.build_experiment_config("unet", 7)


def test_real_training_is_hard_blocked_and_test_split_rejected(tmp_path):
    train_factory, val_loader = C3.make_synthetic_loaders(42, image_size=16, samples_per_domain=1)
    with pytest.raises(C3.C3ExecutionError, match="PENDING_SEPARATE_AUTHORIZATION"):
        C3.train_run("unet", 42, train_factory, val_loader, tmp_path, synthetic=False)
    with pytest.raises(C3.C3ExecutionError, match="only supports TRAIN and VAL"):
        C3.SyntheticSegmentationDataset("TEST")
    with pytest.raises(C3.C3ExecutionError, match="PENDING_SEPARATE_AUTHORIZATION"):
        C3.main(["run-real", "--model", "unet", "--seed", "42"])
    with pytest.raises(C3.C3ExecutionError, match="COMPATIBLE_COMPONENT_BUNDLE"):
        C3.main(["run-real", "--model", C3.FULL_MODEL_KEY, "--seed", "42"])


def test_canonical_preprocessing_contract_on_generated_images():
    image = Image.fromarray(np.full((19, 27, 3), 127, dtype=np.uint8), mode="RGB")
    mask_array = np.zeros((19, 27), dtype=np.uint8)
    mask_array[4:13, 7:18] = 255
    mask = Image.fromarray(mask_array, mode="L")
    transform = SegmentationTransform(size=256, train=False, image_mode="RGB")
    image_tensor, mask_tensor, _ = transform(image, mask)
    assert tuple(image_tensor.shape) == (3, 256, 256)
    assert tuple(mask_tensor.shape) == (1, 256, 256)
    assert set(torch.unique(mask_tensor).tolist()).issubset({0.0, 1.0})


def test_domain_macro_metric_is_equal_domain_and_seed_order_is_deterministic():
    _, val_loader = C3.make_synthetic_loaders(42, image_size=16, samples_per_domain=1, batch_size=2)

    class ZeroLogit(nn.Module):
        def forward(self, image):
            return torch.zeros((len(image), 1, image.shape[-2], image.shape[-1]))

    _, domains, records = C3._evaluate(
        ZeroLogit(), val_loader, C3.BCEDiceLoss(0.5, 0.5, 1e-6),
        torch.device("cpu"), 0.5, False, include_hd95=True)
    macro = C3.macro_domain_dice({d: domains[d]["dice"] for d in C3.DOMAIN_ORDER})
    expected = sum(np.mean([r["dice"] for r in records if r["domain"] == d]) for d in C3.DOMAIN_ORDER) / 4
    assert macro == pytest.approx(expected)
    assert len(records) == 4 and len({r["sample_id"] for r in records}) == 4
    assert all(r["task_id"] == C3.TASK_IDS[r["domain"]] and r["split"] == "VAL" for r in records)
    assert all(r["hd95"] is not None and r["hd95_undefined_reason"] is None for r in records)
    assert all(domains[d]["hd95_n_defined"] == 1 for d in C3.DOMAIN_ORDER)
    from src.data.domain_balanced_sampler import build_domain_balanced_sampler
    labels = ["ISIC"] * 4 + ["BUSI"] * 2 + ["KVASIR"] * 2 + ["KUB"] * 4
    order1 = list(build_domain_balanced_sampler(labels, 42, 3))
    order2 = list(build_domain_balanced_sampler(labels, 42, 3))
    assert order1 == order2


def test_hd95_empty_prediction_is_explicitly_undefined():
    _, val_loader = C3.make_synthetic_loaders(42, image_size=16, samples_per_domain=1)

    class EmptyPrediction(nn.Module):
        def forward(self, image):
            return torch.full((len(image), 1, image.shape[-2], image.shape[-1]), -20.0)

    _, domains, records = C3._evaluate(
        EmptyPrediction(), val_loader, C3.BCEDiceLoss(0.5, 0.5, 1e-6),
        torch.device("cpu"), 0.5, False, include_hd95=True)
    assert all(row["hd95"] is None for row in records)
    assert all(row["hd95_undefined_reason"] == "empty_prediction" for row in records)
    assert all(domains[d]["hd95"] is None and domains[d]["hd95_n_defined"] == 0
               for d in C3.DOMAIN_ORDER)


def test_checkpoint_resume_recovers_history_and_rejects_corruption(tmp_path):
    out = tmp_path / "run"
    train_factory, val_loader = C3.make_synthetic_loaders(42, image_size=16, samples_per_domain=1, batch_size=2)
    first = C3.train_run("unet", 42, train_factory, val_loader, out, epochs=1,
                         device="cpu", synthetic=True, base_channels=4)
    assert first["status"] == "SYNTHETIC_TEST_ONLY"
    (out / "history.jsonl").write_text("truncated", encoding="utf-8")
    second = C3.train_run("unet", 42, train_factory, val_loader, out, epochs=2,
                          device="cpu", synthetic=True, resume=True, base_channels=4)
    rows = [json.loads(line) for line in (out / "history.jsonl").read_text(encoding="utf-8").splitlines()]
    assert second["completed_epochs"] == 2
    assert [r["epoch"] for r in rows] == [1, 2]
    uninterrupted = tmp_path / "uninterrupted"
    C3.train_run("unet", 42, train_factory, val_loader, uninterrupted, epochs=2,
                 device="cpu", synthetic=True, base_channels=4)
    resumed_state = torch.load(out / "latest.pt", map_location="cpu", weights_only=False)["model_state"]
    uninterrupted_state = torch.load(uninterrupted / "latest.pt", map_location="cpu", weights_only=False)["model_state"]
    assert all(torch.equal(resumed_state[k], uninterrupted_state[k]) for k in resumed_state)
    (out / "latest.pt").write_bytes(b"corrupt")
    with pytest.raises(C3.C3ExecutionError, match="corrupt or incomplete checkpoint"):
        C3.train_run("unet", 42, train_factory, val_loader, out, epochs=3,
                     device="cpu", synthetic=True, resume=True, base_channels=4)


def test_per_image_and_per_domain_exports_and_synthetic_rejection(tmp_path):
    run_dir = tmp_path / "run"
    train_factory, val_loader = C3.make_synthetic_loaders(42, image_size=16, samples_per_domain=1, batch_size=2)
    C3.train_run("unet", 42, train_factory, val_loader, run_dir, epochs=1,
                 device="cpu", synthetic=True, base_channels=4)
    result = C3.evaluate_best_checkpoint(run_dir)
    assert result["status"] == "SYNTHETIC_TEST_ONLY"
    assert len(result["per_image"]) == 8
    assert len(result["per_domain"]) == 4
    assert (run_dir / "per_image_metrics.csv").is_file()
    assert (run_dir / "per_domain_metrics.csv").is_file()
    run_manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert run_manifest["evaluation_sha256"] == C3.sha256_file(run_dir / "evaluation.json")
    assert run_manifest["per_image_metrics_sha256"] == C3.sha256_file(run_dir / "per_image_metrics.csv")
    assert run_manifest["per_domain_metrics_sha256"] == C3.sha256_file(run_dir / "per_domain_metrics.csv")
    with pytest.raises(C3.C3ExecutionError, match="synthetic fixture rejected"):
        C3.aggregate_controlled_results([run_dir], tmp_path / "aggregate.json")
    with pytest.raises(C3.C3ExecutionError, match="missing result input"):
        C3.evaluate_best_checkpoint(tmp_path / "missing")
    with pytest.raises(C3.C3ExecutionError, match="incomplete/corrupt run artifact"):
        C3.aggregate_controlled_results([tmp_path / "missing"], tmp_path / "aggregate.json")
    run_manifest["synthetic_only"] = False
    run_manifest["status"] = "CONFIRMED_EXECUTED_RESULT"
    run_manifest["training_performed"] = True
    run_manifest["authorization_release_sha256"] = "a" * 64
    run_manifest["protected_splits_accessed"] = []
    (run_dir / "run_manifest.json").write_text(json.dumps(run_manifest), encoding="utf-8")
    (run_dir / "evaluation.json").write_text("{}", encoding="utf-8")
    with pytest.raises(C3.C3ExecutionError, match="hash-mismatched evaluation.json"):
        C3.aggregate_controlled_results([run_dir], tmp_path / "aggregate.json")


def test_empty_results_schema_has_all_missing_cells_no_metrics(tmp_path):
    result = C3.write_empty_results_schema(tmp_path / "results.json")
    assert result["status"] == "NOT_ESTABLISHED"
    assert result["primary_model"] == C3.FULL_MODEL_IDENTITY
    assert result["comparison_direction"] == "RA-MedFiLM-BARR (FULL) minus external baseline"
    assert len(result["expected_runs"]) == 18
    assert len(result["missing_runs"]) == 18
    assert all(row["status"] == "MISSING" for row in result["expected_runs"])
    assert not any("dice" in row for row in result["expected_runs"])
    full_rows = [r for r in result["expected_runs"] if r["model_key"] == C3.FULL_MODEL_KEY]
    assert len(full_rows) == 3
    disk = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    assert disk["protocol_sha256"] == C3.EXPECTED_PROTOCOL_SHA256


def test_result_schema_rejects_mismatched_run_roster(tmp_path):
    result = C3.write_empty_results_schema(tmp_path / "results.json")
    result["missing_runs"].pop()
    with pytest.raises(C3.C3ExecutionError, match="missing-run roster"):
        C3.validate_controlled_results_schema(result)


def test_full_model_bundle_requires_one_compatible_checkpoint_family():
    def item(digest, **bindings):
        return {
            "master_seed": 123,
            "checkpoint_sha256": digest * 64,
            "checkpoint_path": f"components/{digest}.pt",
            **bindings,
        }

    g, r, bphi, somega = "a", "b", "c", "d"
    bundle = {
        "schema": C3.FULL_MODEL_BUNDLE_SCHEMA,
        "model_identity": C3.FULL_MODEL_IDENTITY,
        "master_seed": 123,
        "components": {
            "G": item(g),
            "R_psi": item(r, trained_against_global_sha256=g * 64),
            "B_phi": item(bphi, trained_against_global_sha256=g * 64,
                          trained_against_refiner_sha256=r * 64),
            "S_omega": item(somega, trained_against_global_sha256=g * 64,
                            trained_against_refiner_sha256=r * 64,
                            trained_against_router_sha256=bphi * 64),
            "routing_fusion": {"source_sha256": "e" * 64},
        },
    }
    C3.validate_full_model_bundle(bundle, 123)
    bundle["components"]["R_psi"]["trained_against_global_sha256"] = "f" * 64
    with pytest.raises(C3.C3ExecutionError, match="refiner was not trained"):
        C3.validate_full_model_bundle(bundle, 123)
    bundle["components"]["R_psi"]["trained_against_global_sha256"] = g * 64
    bundle["components"]["R_psi"].pop("checkpoint_path")
    with pytest.raises(C3.C3ExecutionError, match="component path missing"):
        C3.validate_full_model_bundle(bundle, 123)


def test_full_minus_baseline_paired_effect_sign_and_roster_guard():
    full_rows = []
    baseline_rows = []
    for domain in C3.DOMAIN_ORDER:
        for index in range(2):
            sample_id = f"{domain}:{index}"
            full_rows.append({"sample_id": sample_id, "domain": domain,
                              "task_id": C3.TASK_IDS[domain], "split": "VAL", "dice": 0.8})
            baseline_rows.append({"sample_id": sample_id, "domain": domain,
                                  "task_id": C3.TASK_IDS[domain], "split": "VAL", "dice": 0.7})
    accepted = {
        (C3.FULL_MODEL_KEY, 42): {"evaluation": {"per_image": full_rows}},
        ("unet", 42): {"evaluation": {"per_image": baseline_rows}},
    }
    effects = C3.paired_full_vs_baselines(accepted)
    assert len(effects) == 1
    assert effects[0]["direction"] == "full_minus_baseline"
    assert effects[0]["macro_delta"] == pytest.approx(0.1)
    assert all(v["full_minus_baseline"] == pytest.approx(0.1)
               for v in effects[0]["per_domain"].values())
    accepted[("unet", 42)]["evaluation"]["per_image"].pop()
    with pytest.raises(C3.C3ExecutionError, match="sample roster mismatch"):
        C3.paired_full_vs_baselines(accepted)
    accepted[("unet", 42)]["evaluation"]["per_image"] = [
        {"sample_id": f"{domain}:{index}", "domain": domain,
         "task_id": C3.TASK_IDS[domain], "split": "VAL", "dice": 0.7}
        for domain in C3.DOMAIN_ORDER for index in range(2)
    ]
    accepted[("unet", 42)]["evaluation"]["per_image"][0]["domain"] = "BUSI"
    accepted[("unet", 42)]["evaluation"]["per_image"][0]["task_id"] = C3.TASK_IDS["BUSI"]
    with pytest.raises(C3.C3ExecutionError, match="domain/task mismatch"):
        C3.paired_full_vs_baselines(accepted)


def test_full_system_synthetic_execution_paths_and_task_ids():
    from src.research.c3_baselines.full_system_smoke import run_synthetic_full_system_smoke

    result = run_synthetic_full_system_smoke(device="cpu", image_size=32)
    assert result["status"] == "SYNTHETIC_TEST_ONLY"
    assert result["training_performed"] is False
    assert result["inference_on_research_data"] is False
    states = [case["state"] for case in result["cases"]]
    assert states.count("EXECUTE_THEN_ACCEPT") == 4
    assert "SKIP_GLOBAL" in states
    assert "EXECUTE_THEN_REJECT" in states
    assert result["total_parameter_count"] == C3.FULL_MODEL_PARAMETER_COUNT


def test_model_registry_parameter_counts_and_forward_shapes():
    expected = {
        "unet": 7_763_041,
        "attention_unet": 7_851_285,
        "deeplabv3plus": 40_347_041,
        "transformer_mit_unet": 16_347_777,
        "unetpp": 9_159_681,
    }
    for key in C3.ARCHITECTURES:
        model = C3.build_model(key)
        assert C3.parameter_count(model) == expected[key]
        model.eval()
        with torch.no_grad():
            output = model(torch.zeros((1, 3, 64, 64)))
        assert tuple(output.shape) == (1, 1, 64, 64)
        del model, output
        gc.collect()


def test_analytical_compute_is_labeled_lower_bound():
    model = C3.build_model("unet", base_channels=4)
    result = C3.analytical_macs_lower_bound(model, (1, 3, 32, 32))
    assert result["macs_lower_bound"] > 0
    assert result["gmacs_lower_bound"] > 0
    assert "excludes attention" in result["method"]
    assert C3.estimate_optimizer_checkpoint_bytes(100) == 2400
