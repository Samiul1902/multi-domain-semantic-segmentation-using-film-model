from __future__ import annotations

import numpy as np
import pytest
import torch
import torch.nn.functional as F

from scripts.analysis.phase25f_post_safety_features import compute_numeric_features
from src.models.barr.ra_medfilm_barr import RAMedFiLMBARR
from src.features.barr_lite_router_features import build_lite_feature_vector
from src.models.lite.ra_medfilm_barr_lite import (
    CANDIDATE_SPECS,
    DistillationLossWeights,
    LiteGlobalMedFiLM,
    LiteRegionalRefiner,
    MODEL_COMPARISON_MATRIX,
    atomic_save_lite_checkpoint,
    binary_distillation_loss,
    count_unique_parameters,
    lite_distillation_training_step,
    load_lite_checkpoint,
    parameter_inventory,
    seed_lite_training,
    teacher_bundle_sha256,
)
from src.research.c3_baselines.full_system_smoke import _class_from_source


ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _deterministic_cpu():
    torch.manual_seed(42)
    torch.set_num_threads(1)


def _build_system(variant: str):
    spec = CANDIDATE_SPECS[variant]
    global_model = LiteGlobalMedFiLM(spec)
    refiner = LiteRegionalRefiner(spec)
    router_class = _class_from_source(
        ROOT / "scripts" / "analysis" / "train_phase25d_router.py",
        "BARRBenefitRouterV1",
        {},
    )
    safety_class = _class_from_source(
        ROOT / "scripts" / "analysis" / "phase25f_execution_common.py",
        "BARRPostSafetyV1",
        {"FEATURE_DIM": 20, "HIDDEN": (32, 16)},
    )
    router = router_class()
    safety = safety_class()
    system = RAMedFiLMBARR(global_model, refiner, router, safety)
    return system, {
        "G": global_model,
        "R_psi": refiner,
        "B_phi": router,
        "S_omega": safety,
    }


@pytest.mark.parametrize("variant", tuple(CANDIDATE_SPECS))
def test_four_domain_logits_and_film_are_task_conditioned(variant):
    spec = CANDIDATE_SPECS[variant]
    model = LiteGlobalMedFiLM(spec).eval()
    images = torch.rand(4, 3, 64, 64)
    task_ids = torch.arange(4)
    with torch.inference_mode():
        logits = model(images, task_ids)
    assert logits.shape == (4, 1, 64, 64)
    assert torch.isfinite(logits).all()

    layer = model.film_layers["bridge"]
    with torch.no_grad():
        layer.output.weight.normal_(mean=0.0, std=0.1)
    shared = torch.rand(1, 3, 64, 64)
    with torch.inference_mode():
        task_logits = torch.cat([
            model(shared, torch.tensor([task_id])) for task_id in range(4)
        ])
    assert not torch.allclose(task_logits[0], task_logits[1])
    with pytest.raises(ValueError, match="finite"):
        model(torch.full_like(shared, float("inf")), torch.tensor([0]))
    with pytest.raises(ValueError, match="IDs in"):
        model(shared, torch.tensor([4]))
    with pytest.raises(ValueError, match="integer tensor dtype"):
        model(shared, torch.tensor([1.0]))


@pytest.mark.parametrize("variant", tuple(CANDIDATE_SPECS))
def test_refiner_output_and_bad_inputs(variant):
    model = LiteRegionalRefiner(CANDIDATE_SPECS[variant]).eval()
    with torch.inference_mode():
        output = model(torch.rand(1, 4, 64, 64))
    assert output.shape == (1, 1, 64, 64)
    with pytest.raises(ValueError, match="4, H, W"):
        model(torch.rand(1, 3, 64, 64))
    with pytest.raises(ValueError, match="at least 32"):
        model(torch.rand(1, 4, 16, 16))
    with pytest.raises(ValueError, match="finite"):
        model(torch.full((1, 4, 32, 32), float("nan")))


def test_lite_backbone_emits_compatible_width_agnostic_router_features():
    model = LiteGlobalMedFiLM(CANDIDATE_SPECS["depthwise_compact"]).eval()
    image = torch.rand(1, 3, 512, 512)
    with torch.inference_mode():
        logits, taps = model.forward_with_features(image, torch.tensor([1]))
        regular_logits = model(image, torch.tensor([1]))
    assert torch.equal(logits, regular_logits)
    assert {name: tuple(value.shape[-2:]) for name, value in taps.items()} == {
        "bridge": (32, 32),
        "decoder2": (256, 256),
        "decoder1": (512, 512),
    }
    roi = {
        "clip_x1": 64,
        "clip_y1": 64,
        "clip_x2": 448,
        "clip_y2": 448,
        "crop_side_pixels": 384,
    }
    features = build_lite_feature_vector(
        {name: value[0].numpy() for name, value in taps.items()},
        torch.sigmoid(logits)[0, 0].numpy(),
        roi,
    )
    assert features.shape == (202,)
    assert np.isfinite(features).all()


def test_full_lite_wrapper_executes_accept_skip_reject_and_preserves_global():
    system, components = _build_system("depthwise_compact")
    system.eval()
    image = torch.rand(1, 3, 64, 64)

    def run(router_selects: bool, safety_accepts: bool):
        with torch.inference_mode():
            global_logits = components["G"](image, torch.tensor([2]))
            global_probability = torch.sigmoid(global_logits)[0, 0].cpu().numpy()
        window = system._roi_window_from_probability(global_probability)
        assert window is not None
        with torch.no_grad():
            components["B_phi"].net[-1].weight.zero_()
            components["B_phi"].net[-1].bias.fill_(20.0 if router_selects else -20.0)
            components["S_omega"].fc3.weight.zero_()
            components["S_omega"].fc3.bias.fill_(20.0 if safety_accepts else -20.0)

        refined = None
        safety_features = None
        if router_selects:
            y0, y1, x0, x1 = window
            image_crop = image[:, :, y0:y1, x0:x1]
            global_crop = torch.from_numpy(
                global_probability[y0:y1, x0:x1]
            )[None, None]
            image_256 = F.interpolate(image_crop, size=(256, 256), mode="bilinear",
                                      align_corners=False)
            global_256 = F.interpolate(global_crop, size=(256, 256), mode="bilinear",
                                       align_corners=False)
            refiner_input = torch.cat((image_256, global_256), dim=1)
            with torch.inference_mode():
                refined = torch.sigmoid(components["R_psi"](refiner_input))[0, 0].numpy()
            area_fraction = ((y1 - y0) * (x1 - x0)) / 4096.0
            side_512 = max(y1 - y0, x1 - x0) * 8.0
            safety_features = compute_numeric_features(
                global_256[0, 0].numpy(), refined, area_fraction, side_512
            )

        return system.forward_inference(
            image,
            2,
            router_features_202=np.zeros(202, dtype=np.float32),
            roi_window=window,
            action_available=True,
            oof_refined_crop_prob=refined,
            safety_post_features_16=safety_features,
        ), global_probability

    accepted, _ = run(True, True)
    assert accepted["state"] == "EXECUTE_THEN_ACCEPT"
    assert accepted["refiner_forward_count"] == 1
    assert accepted["s_omega_forward_count"] == 1
    assert accepted["final_probability"].shape == (64, 64)
    assert np.array_equal(
        accepted["final_binary"],
        (accepted["final_probability"] >= system.segmentation_output_threshold).astype(np.uint8),
    )

    skipped, skipped_global = run(False, True)
    assert skipped["state"] == "SKIP_GLOBAL"
    assert skipped["refiner_forward_count"] == 0
    assert np.array_equal(skipped["final_probability"], skipped_global)

    rejected, rejected_global = run(True, False)
    assert rejected["state"] == "EXECUTE_THEN_REJECT"
    assert rejected["refiner_forward_count"] == 1
    assert rejected["s_omega_forward_count"] == 1
    assert np.array_equal(rejected["final_probability"], rejected_global)
    with torch.inference_mode():
        forced = system.forward_inference(
            image,
            2,
            action_available=False,
            router_features_202=None,
        )
    assert forced["state"] == "FORCED_SKIP"
    assert forced["refiner_forward_count"] == 0
    assert forced["s_omega_forward_count"] == 0
    assert forced["final_probability"].shape == (64, 64)


def test_parameters_are_unique_bounded_and_report_trainable_frozen():
    expected = {
        "width_compact": 1_240_280,
        "depthwise_compact": 272_601,
        "ultralite_depthwise_add": 82_029,
    }
    for candidate, spec in CANDIDATE_SPECS.items():
        global_model = LiteGlobalMedFiLM(spec)
        refiner = LiteRegionalRefiner(spec)
        shared = torch.nn.Linear(2, 2)
        modules = {
            "G": global_model,
            "R_psi": refiner,
            "shared_a": shared,
            "shared_b": shared,
        }
        inventory = parameter_inventory(modules)
        assert inventory["unique_parameters"] == count_unique_parameters(*modules.values())
        assert inventory["by_component"]["shared_a"]["unique_parameters"] == 6
        assert inventory["by_component"]["shared_b"]["unique_parameters"] == 6
        assert inventory["trainable_parameters"] == inventory["unique_parameters"]

        total = count_unique_parameters(global_model, refiner) + 36_801 + 1_217
        assert total == expected[candidate]
        assert total < 2_000_000
    assert sum(row["key"] == "ra_medfilm_barr_full" for row in MODEL_COMPARISON_MATRIX) == 1
    assert any(row["key"] == "fast_scnn" and "no matched local score" in row["evidence_status"]
               for row in MODEL_COMPARISON_MATRIX)


def test_distillation_loss_contract_and_nonfinite_rejection():
    student = torch.zeros(2, 1, 16, 16, requires_grad=True)
    teacher = torch.ones_like(student)
    targets = torch.zeros_like(student)
    total, parts = binary_distillation_loss(
        student, targets, teacher_logits=teacher,
        weights=DistillationLossWeights(teacher_soft_mask=0.5),
    )
    assert total.isfinite()
    assert all(value.isfinite() for value in parts.values())
    total.backward()
    assert student.grad is not None

    with pytest.raises(ValueError, match="finite"):
        binary_distillation_loss(
            torch.full_like(student, float("nan")), targets,
            teacher_logits=teacher,
        )
    with pytest.raises(ValueError, match="matching intermediate"):
        binary_distillation_loss(
            torch.zeros_like(student), targets, teacher_logits=teacher,
            student_features=torch.zeros(1, 4),
            teacher_features=torch.zeros(1, 5),
            weights=DistillationLossWeights(intermediate_feature=1.0),
        )

def test_distillation_training_step_updates_only_lite_student_parameters():
    student = LiteGlobalMedFiLM(CANDIDATE_SPECS["ultralite_depthwise_add"])
    optimizer = torch.optim.AdamW(student.parameters(), lr=1e-4)
    images = torch.rand(1, 3, 64, 64)
    targets = torch.zeros(1, 1, 64, 64)
    teacher_logits = torch.rand_like(targets)
    with torch.inference_mode():
        _, teacher_taps = student.forward_with_features(images, torch.tensor([3]))
    before = student.head.weight.detach().clone()
    losses = lite_distillation_training_step(
        student,
        optimizer,
        images,
        torch.tensor([3]),
        targets,
        teacher_logits=teacher_logits,
        teacher_features=teacher_taps["decoder2"],
        weights=DistillationLossWeights(intermediate_feature=0.1),
    )
    assert set(losses) == {
        "total", "supervised_bce", "supervised_dice",
        "teacher_soft_mask", "intermediate_feature",
    }
    assert all(np.isfinite(value) for value in losses.values())
    assert not torch.equal(before, student.head.weight.detach())


def test_lite_checkpoint_round_trip_and_family_provenance(tmp_path):
    spec = CANDIDATE_SPECS["depthwise_compact"]
    original, _ = _build_system("depthwise_compact")
    path = tmp_path / "lite.pt"
    teacher_hashes = {
        "G": "a" * 64,
        "R_psi": "b" * 64,
        "B_phi": "c" * 64,
        "S_omega": "d" * 64,
    }
    teacher_hash = teacher_bundle_sha256(teacher_hashes)
    atomic_save_lite_checkpoint(
        path,
        model=original,
        spec=spec,
        seed=42,
        teacher_checkpoint_sha256=teacher_hash,
        teacher_component_sha256=teacher_hashes,
        run_id="lite-depthwise-seed42",
        training_protocol_id="synthetic-unit-test-only",
    )
    reloaded, _ = _build_system("depthwise_compact")
    payload = load_lite_checkpoint(
        path,
        model=reloaded,
        spec=spec,
        expected_teacher_checkpoint_sha256=teacher_hash,
        expected_seed=42,
        expected_run_id="lite-depthwise-seed42",
        expected_training_protocol_id="synthetic-unit-test-only",
        expected_teacher_component_sha256=teacher_hashes,
    )
    assert payload["seed"] == 42
    assert all(torch.equal(value, reloaded.state_dict()[key])
               for key, value in original.state_dict().items())
    with pytest.raises(ValueError, match="teacher provenance"):
        load_lite_checkpoint(
            path, model=LiteGlobalMedFiLM(spec), spec=spec,
            expected_teacher_checkpoint_sha256="f" * 64,
            expected_seed=42, expected_run_id="lite-depthwise-seed42",
            expected_training_protocol_id="synthetic-unit-test-only",
        )
    with pytest.raises(ValueError, match="architecture ID"):
        load_lite_checkpoint(
            path,
            model=LiteGlobalMedFiLM(CANDIDATE_SPECS["ultralite_depthwise_add"]),
            spec=CANDIDATE_SPECS["ultralite_depthwise_add"],
            expected_teacher_checkpoint_sha256="a" * 64,
            expected_seed=42, expected_run_id="lite-depthwise-seed42",
            expected_training_protocol_id="synthetic-unit-test-only",
        )
    with pytest.raises(ValueError, match="run/seed"):
        load_lite_checkpoint(
            path, model=LiteGlobalMedFiLM(spec), spec=spec,
            expected_teacher_checkpoint_sha256=teacher_hash,
            expected_seed=123, expected_run_id="lite-depthwise-seed42",
            expected_training_protocol_id="synthetic-unit-test-only",
            expected_teacher_component_sha256=teacher_hashes,
        )


def test_training_seed_is_reproducible():
    seed_lite_training(123)
    first = (torch.rand(1).item(), np.random.rand(), __import__("random").random())
    seed_lite_training(123)
    second = (torch.rand(1).item(), np.random.rand(), __import__("random").random())
    assert first == second
    with pytest.raises(ValueError, match="nonnegative"):
        seed_lite_training(-1)
