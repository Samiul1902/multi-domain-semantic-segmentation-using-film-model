"""Synthetic-only execution checks for the canonical full RA-MedFiLM-BARR graph.

The production wrapper intentionally consumes versioned GT-free feature artifacts.
This module supplies only deterministic synthetic features for component-path tests;
it cannot load checkpoints, read datasets, train, or emit research results.
"""
from __future__ import annotations

import ast
import random
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

from scripts.analysis.phase25f_post_safety_features import compute_numeric_features
from src.models.barr.ra_medfilm_barr import RAMedFiLMBARR, _to_prob_map
from src.models.barr.regional_refiner import BARRRegionalRefinerV1
from src.models.film.global_medfilm import GlobalMedFiLM

FULL_MODEL_IDENTITY = "RA-MedFiLM-BARR (FULL)"
EXPECTED_COMPONENT_PARAMETERS = {
    "G": 3_523_001,
    "R_psi": 1_276_401,
    "B_phi": 36_801,
    "S_omega": 1_217,
}


def _class_from_source(path: Path, class_name: str, namespace: dict[str, Any]) -> type[nn.Module]:
    """Compile only a canonical class definition, never its training module."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    nodes = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name]
    if len(nodes) != 1:
        raise RuntimeError(f"Expected one {class_name} definition in {path}")
    scope = {"torch": torch, "nn": nn, "np": np, **namespace}
    code = compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec")
    exec(code, scope)
    model_class = scope[class_name]
    if not issubclass(model_class, nn.Module):
        raise TypeError(f"{class_name} is not a torch module")
    return model_class


def build_synthetic_full_system() -> tuple[RAMedFiLMBARR, dict[str, nn.Module]]:
    """Instantiate actual component architectures with fresh synthetic weights."""
    root = Path(__file__).resolve().parents[3]
    router_class = _class_from_source(
        root / "scripts" / "analysis" / "train_phase25d_router.py",
        "BARRBenefitRouterV1",
        {},
    )
    safety_class = _class_from_source(
        root / "scripts" / "analysis" / "phase25f_execution_common.py",
        "BARRPostSafetyV1",
        {"FEATURE_DIM": 20, "HIDDEN": (32, 16)},
    )
    components: dict[str, nn.Module] = {
        "G": GlobalMedFiLM(),
        "R_psi": BARRRegionalRefinerV1(),
        "B_phi": router_class(),
        "S_omega": safety_class(),
    }
    counts = {key: sum(parameter.numel() for parameter in model.parameters())
              for key, model in components.items()}
    if counts != EXPECTED_COMPONENT_PARAMETERS:
        raise RuntimeError(f"canonical component parameter counts differ: {counts}")
    system = RAMedFiLMBARR(
        global_model=components["G"],
        regional_refiner=components["R_psi"],
        benefit_router=components["B_phi"],
        post_safety=components["S_omega"],
    )
    return system, components


def _make_candidate(
    system: RAMedFiLMBARR,
    components: dict[str, nn.Module],
    image: torch.Tensor,
    task_id: int,
    *,
    router_selects: bool,
    safety_accepts: bool,
) -> dict[str, Any]:
    """Build the real refiner/safety inputs from synthetic images and probabilities."""
    global_model = components["G"]
    with torch.inference_mode():
        logits = global_model(image, task_ids=torch.tensor([task_id]))
        p_global = _to_prob_map(logits)
    window = system._roi_window_from_probability(p_global)
    if window is None:
        raise RuntimeError("synthetic smoke image did not yield an ROI")

    router = components["B_phi"]
    with torch.no_grad():
        final_router = router.net[-1]
        final_router.weight.zero_()
        final_router.bias.fill_(20.0 if router_selects else -20.0)
        final_safety = components["S_omega"].fc3
        final_safety.weight.zero_()
        final_safety.bias.fill_(20.0 if safety_accepts else -20.0)

    y0, y1, x0, x1 = window
    refined = None
    safety_features = None
    if router_selects:
        image_crop = image[:, :, y0:y1, x0:x1]
        global_crop = torch.from_numpy(p_global[y0:y1, x0:x1])[None, None]
        crop_image_256 = F.interpolate(image_crop, size=(256, 256), mode="bilinear",
                                       align_corners=False)
        crop_global_256 = F.interpolate(global_crop, size=(256, 256), mode="bilinear",
                                        align_corners=False)
        refiner_input = torch.cat([crop_image_256, crop_global_256], dim=1)
        with torch.inference_mode():
            refined = torch.sigmoid(components["R_psi"](refiner_input))[0, 0].numpy()
        height, width = p_global.shape
        area_fraction = ((y1 - y0) * (x1 - x0)) / float(height * width)
        side_512 = max(y1 - y0, x1 - x0) * 512.0 / max(height, width)
        safety_features = compute_numeric_features(
            crop_global_256[0, 0].numpy(), refined, area_fraction, side_512
        )
    result = system.forward_inference(
        image,
        task_id,
        router_features_202=np.zeros(202, dtype=np.float32),
        roi_window=window,
        action_available=True,
        oof_refined_crop_prob=refined,
        safety_post_features_16=safety_features,
    )
    result["synthetic_global_probability_reference"] = p_global
    if refined is not None:
        result["synthetic_expected_fused_probability"] = system._fuse_global_with_regional(
            p_global, refined, window
        )
    return result


def run_synthetic_full_system_smoke(*, device: str = "cpu", image_size: int = 64) -> dict[str, Any]:
    """Exercise all four tasks and router/safety branches without producing results."""
    if image_size < 32 or image_size % 32:
        raise ValueError("image_size must be >=32 and divisible by 32")
    device_t = torch.device(device)
    if device_t.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested for synthetic full-system smoke but unavailable")
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(42)

    system, components = build_synthetic_full_system()
    if device_t.type != "cpu":
        # The frozen inference wrapper constructs its task/feature tensors on CPU.
        # Keep this smoke on CPU instead of masking that pre-existing device contract.
        raise RuntimeError("canonical wrapper synthetic smoke currently requires CPU")
    system.eval()
    outcomes = []
    for task_id in range(4):
        image = torch.rand((1, 3, image_size, image_size))
        accepted = _make_candidate(
            system, components, image, task_id, router_selects=True, safety_accepts=True
        )
        if accepted["state"] != "EXECUTE_THEN_ACCEPT":
            raise RuntimeError(f"task {task_id} did not reach safety-accepted path: {accepted['state']}")
        if accepted["final_binary"].shape != (image_size, image_size):
            raise RuntimeError("full-system final mask shape mismatch")
        expected = accepted.get("synthetic_expected_fused_probability")
        if expected is None or not np.array_equal(accepted["final_probability"], expected):
            raise RuntimeError("accepted path did not return the fused full-system probability")
        if not np.array_equal(
                accepted["final_binary"],
                (accepted["final_probability"] >= system.segmentation_output_threshold).astype(np.uint8)):
            raise RuntimeError("final binary mask does not match the canonical threshold")
        outcomes.append({"task_id": task_id, "state": accepted["state"]})

    image = torch.rand((1, 3, image_size, image_size))
    skipped = _make_candidate(
        system, components, image, 0, router_selects=False, safety_accepts=True
    )
    if skipped["state"] != "SKIP_GLOBAL" or skipped["refiner_forward_count"] != 0:
        raise RuntimeError("router-skipped path did not preserve global prediction")
    if not np.array_equal(skipped["final_probability"], skipped["synthetic_global_probability_reference"]):
        raise RuntimeError("router-skipped path changed the global prediction")
    outcomes.append({"task_id": 0, "state": skipped["state"]})

    rejected = _make_candidate(
        system, components, image, 0, router_selects=True, safety_accepts=False
    )
    if rejected["state"] != "EXECUTE_THEN_REJECT" or rejected["s_omega_forward_count"] != 1:
        raise RuntimeError("safety-rejected path did not preserve global prediction")
    if not np.array_equal(rejected["final_probability"], rejected["synthetic_global_probability_reference"]):
        raise RuntimeError("safety-rejected path changed the global prediction")
    outcomes.append({"task_id": 0, "state": rejected["state"]})

    return {
        "status": "SYNTHETIC_TEST_ONLY",
        "training_performed": False,
        "inference_on_research_data": False,
        "model_identity": FULL_MODEL_IDENTITY,
        "device": str(device_t),
        "image_size": image_size,
        "component_parameter_counts": EXPECTED_COMPONENT_PARAMETERS,
        "total_parameter_count": sum(EXPECTED_COMPONENT_PARAMETERS.values()),
        "cases": outcomes,
        "outputs_are_research_evidence": False,
    }
