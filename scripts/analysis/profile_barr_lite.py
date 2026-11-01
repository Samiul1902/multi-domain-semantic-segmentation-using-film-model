"""Synthetic-only parameter, MAC, storage, and latency profile for BARR-Lite."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import platform
import random
import subprocess
import sys
import threading
import time
from typing import Any, Iterator

import numpy as np
import psutil
import torch
from torch import nn
from torch.nn import functional as F

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.analysis.phase25f_post_safety_features import compute_numeric_features
from src.models.barr.ra_medfilm_barr import (
    RAMedFiLMBARR,
    TAU_C8_FINAL_FLOAT,
    canonical_utility,
)
from src.models.barr.regional_refiner import BARRRegionalRefinerV1
from src.models.film.global_medfilm import GlobalMedFiLM
from src.features.barr_lite_router_features import build_lite_feature_vector
from src.features.barr_pre_refinement_features import build_feature_vector
from src.models.lite.ra_medfilm_barr_lite import (
    CANDIDATE_SPECS,
    LiteGlobalMedFiLM,
    LiteRegionalRefiner,
    count_unique_parameters,
    parameter_inventory,
    teacher_bundle_sha256,
)
from src.research.c3_baselines.full_system_smoke import _class_from_source


FULL_CHECKPOINTS = {
    "G": Path("checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"),
    "R_psi": Path(
        "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt"
    ),
    "B_phi": Path(
        "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt"
    ),
    "S_omega": Path(
        "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt"
    ),
}
EXPECTED_FULL_COUNTS = {"G": 3_523_001, "R_psi": 1_276_401,
                        "B_phi": 36_801, "S_omega": 1_217}
EXPECTED_FULL_CHECKPOINT_SHA256 = {
    "G": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
    "R_psi": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
    "B_phi": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
    "S_omega": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
}
_MEASURE = False
_MACS: dict[str, int] = {}
_HOOKS: list[Any] = []


def _safe_load_checkpoint(path: Path) -> dict[str, Any]:
    numpy_types = [
        value for value in vars(np.dtypes).values()
        if isinstance(value, type)
    ]
    safe_types = [
        np._core.multiarray._reconstruct,
        np.ndarray,
        np.dtype,
        torch.torch_version.TorchVersion,
        *numpy_types,
    ]
    with torch.serialization.safe_globals(safe_types):
        payload = torch.load(path, map_location="cpu", weights_only=True)
    if not isinstance(payload, dict) or not isinstance(payload.get("model_state"), dict):
        raise ValueError(f"{path} lacks the expected model_state mapping")
    return payload


def _load_trained_full_components() -> tuple[
    dict[str, nn.Module], dict[str, dict[str, Any]], dict[str, dict[str, Any]]
]:
    modules: dict[str, nn.Module] = {
        "G": GlobalMedFiLM(),
        "R_psi": BARRRegionalRefinerV1(),
    }
    router_class = _class_from_source(
        ROOT / "scripts/analysis/train_phase25d_router.py",
        "BARRBenefitRouterV1",
        {},
    )
    safety_class = _class_from_source(
        ROOT / "scripts/analysis/phase25f_execution_common.py",
        "BARRPostSafetyV1",
        {"FEATURE_DIM": 20, "HIDDEN": (32, 16)},
    )
    modules["B_phi"] = router_class()
    modules["S_omega"] = safety_class()
    provenance: dict[str, dict[str, Any]] = {}
    normalizations: dict[str, dict[str, Any]] = {}
    for name, relative_path in FULL_CHECKPOINTS.items():
        path = ROOT / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"required trained component checkpoint missing: {path}")
        payload = _safe_load_checkpoint(path)
        modules[name].load_state_dict(payload["model_state"], strict=True)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != EXPECTED_FULL_CHECKPOINT_SHA256[name]:
            raise RuntimeError(
                f"canonical FULL checkpoint family changed for {name}: {digest}"
            )
        provenance[name] = {
            "path": relative_path.as_posix(),
            "sha256": digest,
            "bytes": path.stat().st_size,
            "seed": payload.get("seed"),
        }
        if name == "B_phi":
            normalizations["router"] = {
                "indices": [192, 193, 194, 195, 196, 197, 200, 201],
                "mu": payload["normalizer_mu"],
                "sigma": payload["normalizer_sigma"],
                "constant_mask": payload["normalizer_constant_mask"],
            }
        elif name == "S_omega":
            normalizations["safety"] = {
                "indices": list(range(16)),
                "mu": payload["normalizer_mu"],
                "sigma": payload["normalizer_sigma"],
                "constant_mask": payload["normalizer_constant_mask"],
            }
    counts = {name: sum(p.numel() for p in module.parameters())
              for name, module in modules.items()}
    if counts != EXPECTED_FULL_COUNTS:
        raise RuntimeError(f"canonical full component counts mismatch: {counts}")
    for module in modules.values():
        module.eval()
    return modules, provenance, normalizations


def _install_mac_hooks(modules: dict[str, nn.Module]) -> None:
    global _HOOKS
    _remove_mac_hooks()
    for component_name, component in modules.items():
        for module_name, module in component.named_modules():
            if isinstance(module, nn.Conv2d):
                key = f"{component_name}.{module_name}"

                def conv_hook(layer: nn.Conv2d, inputs: tuple[Any, ...],
                              output: Tensor, name: str = key) -> None:
                    if not _MEASURE:
                        return
                    batch, _, height, width = output.shape
                    kh, kw = layer.kernel_size
                    count = batch * height * width * layer.out_channels
                    count *= (layer.in_channels // layer.groups) * kh * kw
                    _MACS[name] = _MACS.get(name, 0) + int(count)

                _HOOKS.append(module.register_forward_hook(conv_hook))
            elif isinstance(module, nn.Linear):
                key = f"{component_name}.{module_name}"

                def linear_hook(layer: nn.Linear, inputs: tuple[Any, ...],
                                output: Tensor, name: str = key) -> None:
                    if _MEASURE:
                        count = output.numel() // layer.out_features
                        _MACS[name] = _MACS.get(name, 0) + int(
                            count * layer.in_features * layer.out_features
                        )

                _HOOKS.append(module.register_forward_hook(linear_hook))


def _remove_mac_hooks() -> None:
    global _HOOKS
    for hook in _HOOKS:
        hook.remove()
    _HOOKS = []


@contextmanager
def _record_macs() -> Iterator[dict[str, int]]:
    global _MEASURE, _MACS
    _MACS = {}
    _MEASURE = True
    try:
        yield _MACS
    finally:
        _MEASURE = False


def _system(modules: dict[str, nn.Module]) -> RAMedFiLMBARR:
    return RAMedFiLMBARR(
        global_model=modules["G"],
        regional_refiner=modules["R_psi"],
        benefit_router=modules["B_phi"],
        post_safety=modules["S_omega"],
    ).eval()


def _force_decisions(modules: dict[str, nn.Module], *, select: bool,
                     accept: bool = True) -> None:
    router = modules["B_phi"]
    safety = modules["S_omega"]
    with torch.no_grad():
        router.net[-1].weight.zero_()
        router.net[-1].bias.fill_(20.0 if select else -20.0)
        safety.fc3.weight.zero_()
        safety.fc3.bias.fill_(20.0 if accept else -20.0)


def _execute_path(
    modules: dict[str, nn.Module],
    system: RAMedFiLMBARR,
    image: Tensor,
    *,
    task_id: int,
    route: bool,
    include_router: bool,
    force_synthetic_roi: bool,
) -> dict[str, Any]:
    with torch.inference_mode():
        synthetic_roi_override_applied = False
        feature_maps: dict[str, np.ndarray] = {}
        if include_router and hasattr(modules["G"], "forward_with_features"):
            logits, tap_tensors = modules["G"].forward_with_features(
                image, torch.tensor([task_id])
            )
            feature_maps = {
                name: value[0].detach().cpu().numpy().astype(np.float32)
                for name, value in tap_tensors.items()
            }
        elif include_router:
            hooks = []

            def capture(name: str):
                def hook(_module: nn.Module, _inputs: tuple[Any, ...], output: Tensor) -> None:
                    feature_maps[name] = output[0].detach().cpu().numpy().astype(np.float32)
                return hook

            for name in ("bridge", "decoder2", "decoder1"):
                hooks.append(modules["G"].get_submodule(name).register_forward_hook(capture(name)))
            try:
                logits = modules["G"](image, torch.tensor([task_id]))
            finally:
                for hook in hooks:
                    hook.remove()
        else:
            logits = modules["G"](image, torch.tensor([task_id]))
        p_global = torch.sigmoid(logits)[0, 0].cpu().numpy().astype(np.float32)
        if not include_router:
            return {"state": "GLOBAL_ONLY", "final": p_global}
        window = system._roi_window_from_probability(p_global)
        if window is None and force_synthetic_roi:
            p_global = np.full_like(p_global, 0.5, dtype=np.float32)
            window = system._roi_window_from_probability(p_global)
            synthetic_roi_override_applied = True
        if window is None:
            return {
                "state": "FORCED_SKIP",
                "final": p_global,
                "synthetic_roi_override_applied": synthetic_roi_override_applied,
            }
        y0, y1, x0, x1 = window
        roi_row = {
            "clip_x1": x0,
            "clip_y1": y0,
            "clip_x2": x1,
            "clip_y2": y1,
            "crop_side_pixels": max(y1 - y0, x1 - x0),
        }
        feature_builder = (
            build_lite_feature_vector
            if hasattr(modules["G"], "forward_with_features")
            else build_feature_vector
        )
        router_features = feature_builder(feature_maps, p_global, roi_row)
        router_normalization = getattr(system, "_profile_router_normalization", None)
        if router_normalization is not None:
            router_features = _apply_fit_normalization(
                router_features, router_normalization
            )
        task_ids = torch.tensor([task_id])
        delta = float(modules["B_phi"](
            torch.from_numpy(router_features)[None], task_ids
        ).item())
        should_route = route and canonical_utility(delta) >= TAU_C8_FINAL_FLOAT
        if not should_route:
            return {
                "state": "SKIP_GLOBAL",
                "final": p_global,
                "synthetic_roi_override_applied": synthetic_roi_override_applied,
            }
        image_crop = image[:, :, y0:y1, x0:x1]
        probability_crop = torch.from_numpy(p_global[y0:y1, x0:x1])[None, None]
        image_256 = F.interpolate(image_crop, size=(256, 256), mode="bilinear",
                                  align_corners=False)
        probability_256 = F.interpolate(probability_crop, size=(256, 256),
                                        mode="bilinear", align_corners=False)
        refiner_input = torch.cat((image_256, probability_256), dim=1)
        refined = torch.sigmoid(modules["R_psi"](refiner_input))[0, 0].cpu().numpy()
        area_fraction = ((y1 - y0) * (x1 - x0)) / float(p_global.size)
        side_512 = max(y1 - y0, x1 - x0) * 512.0 / max(p_global.shape)
        numeric_features = compute_numeric_features(
            probability_256[0, 0].cpu().numpy(), refined, area_fraction, side_512
        )
        safety_features = torch.from_numpy(np.concatenate(
            (numeric_features, np.eye(4, dtype=np.float32)[task_id])
        ))[None]
        safety_normalization = getattr(system, "_profile_safety_normalization", None)
        if safety_normalization is not None:
            normalized = _apply_fit_normalization(
                safety_features[0, :16].numpy(), safety_normalization
            )
            safety_features[0, :16] = torch.from_numpy(normalized)
        safety_logit = float(modules["S_omega"](safety_features).item())
        if safety_logit >= 0.0:
            final = system._fuse_global_with_regional(p_global, refined, window)
            return {
                "state": "EXECUTE_THEN_ACCEPT",
                "final": final,
                "synthetic_roi_override_applied": synthetic_roi_override_applied,
            }
        return {
            "state": "EXECUTE_THEN_REJECT",
            "final": p_global,
            "synthetic_roi_override_applied": synthetic_roi_override_applied,
        }


def _apply_fit_normalization(values: np.ndarray, normalization: dict[str, Any]) -> np.ndarray:
    """Apply the historical fit-only scaler to its frozen scalar indices."""
    result = np.asarray(values, dtype=np.float32).copy()
    indices = np.asarray(normalization["indices"], dtype=np.int64)
    mu = np.asarray(normalization["mu"], dtype=np.float32).reshape(-1)
    sigma = np.asarray(normalization["sigma"], dtype=np.float32).reshape(-1)
    constant = np.asarray(normalization["constant_mask"], dtype=bool).reshape(-1)
    if not (indices.size == mu.size == sigma.size == constant.size):
        raise ValueError("normalization artifact dimensions do not match")
    safe_sigma = np.where(sigma < 1e-12, 1.0, sigma)
    result[indices] = (result[indices] - mu) / safe_sigma
    result[indices[constant]] = 0.0
    return result


def _sampled_peak_rss(run: Any, repetitions: int) -> dict[str, float]:
    process = psutil.Process()
    baseline = process.memory_info().rss
    sampled_peak = baseline
    stop = threading.Event()

    def sample() -> None:
        nonlocal sampled_peak
        while not stop.is_set():
            try:
                sampled_peak = max(sampled_peak, process.memory_info().rss)
            except psutil.Error:
                return
            stop.wait(0.002)

    thread = threading.Thread(target=sample, daemon=True)
    thread.start()
    try:
        for _ in range(repetitions):
            run()
    finally:
        stop.set()
        thread.join()
    return {
        "baseline_process_rss_bytes": baseline,
        "sampled_peak_process_rss_bytes": sampled_peak,
        "sampled_peak_process_rss_mib": sampled_peak / (1024.0**2),
        "sampled_peak_delta_bytes": max(0, sampled_peak - baseline),
        "measurement_note": "sampled process RSS; allocator/native transient peaks may be missed",
    }


def _benchmark(
    modules: dict[str, nn.Module],
    system: RAMedFiLMBARR,
    image: Tensor,
    *,
    route: bool,
    include_router: bool,
    force_synthetic_roi: bool,
    accept: bool,
    warmup: int,
    iterations: int,
) -> dict[str, Any]:
    _force_decisions(modules, select=route, accept=accept)
    call = lambda: _execute_path(
        modules, system, image, task_id=0, route=route, include_router=include_router,
        force_synthetic_roi=force_synthetic_roi,
    )
    for _ in range(warmup):
        call()
    with _record_macs() as counter:
        result = call()
        macs = dict(counter)
    durations = []
    for _ in range(iterations):
        start = time.perf_counter()
        call()
        durations.append((time.perf_counter() - start) * 1000.0)
    rss = _sampled_peak_rss(call, iterations)
    values = np.asarray(durations, dtype=np.float64)
    return {
        "state": result["state"],
        "synthetic_roi_override_enabled": force_synthetic_roi,
        "synthetic_roi_override_applied": result.get(
            "synthetic_roi_override_applied", False
        ),
        "macs": int(sum(macs.values())),
        "flops_approx_2_per_mac": int(2 * sum(macs.values())),
        "macs_by_component": {
            component: sum(value for name, value in macs.items()
                           if name.startswith(f"{component}."))
            for component in modules
        },
        "macs_by_block": _macs_by_block(macs, modules),
        "batch_size": 1,
        "latency_ms_p50": float(np.percentile(values, 50)),
        "latency_ms_p95": float(np.percentile(values, 95)),
        "latency_samples": iterations,
        **rss,
    }


def _top_level_parameters(module: nn.Module) -> dict[str, int]:
    return {
        name: sum(parameter.numel() for parameter in child.parameters())
        for name, child in module.named_children()
    }


def _macs_by_block(macs: dict[str, int], modules: dict[str, nn.Module]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for component in modules:
        component_totals: dict[str, int] = {}
        prefix = f"{component}."
        for name, amount in macs.items():
            if not name.startswith(prefix):
                continue
            parts = name[len(prefix):].split(".")
            if parts[0] == "film_layers" and len(parts) > 1:
                block_name = f"film_layers.{parts[1]}"
            else:
                block_name = parts[0]
            component_totals[block_name] = component_totals.get(block_name, 0) + amount
        result[component] = component_totals
    return result


def _profile_family(
    name: str,
    modules: dict[str, nn.Module],
    *,
    image_size: int,
    warmup: int,
    iterations: int,
    normalizations: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    inventory = parameter_inventory(modules)
    total_unique = count_unique_parameters(*modules.values())
    if inventory["unique_parameters"] != total_unique:
        raise RuntimeError("parameter inventory double-count mismatch")
    system = _system(modules)
    if normalizations is not None:
        system._profile_router_normalization = normalizations.get("router")
        system._profile_safety_normalization = normalizations.get("safety")
    _install_mac_hooks(modules)
    image = torch.rand(1, 3, image_size, image_size)
    results = {
        "global_only": _benchmark(
            modules, system, image, route=False, include_router=False,
            force_synthetic_roi=False, accept=True,
            warmup=warmup, iterations=iterations,
        ),
        "router_skip": _benchmark(
            modules, system, image, route=False, include_router=True,
            force_synthetic_roi=True, accept=True,
            warmup=warmup, iterations=iterations,
        ),
        "regional_refinement_accepted": _benchmark(
            modules, system, image, route=True, include_router=True,
            force_synthetic_roi=True, accept=True,
            warmup=warmup, iterations=iterations,
        ),
    }
    _remove_mac_hooks()
    breakdown = {
        name: {
            "parameters": sum(parameter.numel() for parameter in module.parameters()),
            "top_level_blocks": _top_level_parameters(module),
        }
        for name, module in modules.items()
    }
    return {
        "identity": name,
        "synthetic_inputs_only": True,
        "research_data_accessed": False,
        "parameters": inventory,
        "assembled_inference_parameter_inventory": parameter_inventory({"FULL_GRAPH": system}),
        "raw_fp32_weight_bytes": total_unique * 4,
        "parameter_breakdown": breakdown,
        "paths": results,
    }


def _configure_determinism() -> None:
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(42)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    torch.set_num_threads(1)


def _profile_one(
    family: str, *, image_size: int, warmup: int, iterations: int
) -> dict[str, Any]:
    _configure_determinism()
    if family == "full":
        modules, provenance, normalizations = _load_trained_full_components()
        item = _profile_family(
            "RA-MedFiLM-BARR (FULL)", modules,
            image_size=image_size, warmup=warmup, iterations=iterations,
            normalizations=normalizations,
        )
        item["checkpoint_provenance"] = provenance
        item["component_checkpoint_total_bytes"] = sum(
            record["bytes"] for record in provenance.values()
        )
        return item
    if family not in CANDIDATE_SPECS:
        raise ValueError(f"unknown profiling family: {family}")
    spec = CANDIDATE_SPECS[family]
    router_class = _class_from_source(
        ROOT / "scripts/analysis/train_phase25d_router.py",
        "BARRBenefitRouterV1",
        {},
    )
    safety_class = _class_from_source(
        ROOT / "scripts/analysis/phase25f_execution_common.py",
        "BARRPostSafetyV1",
        {"FEATURE_DIM": 20, "HIDDEN": (32, 16)},
    )
    modules: dict[str, nn.Module] = {
        "G": LiteGlobalMedFiLM(spec),
        "R_psi": LiteRegionalRefiner(spec),
        "B_phi": router_class(),
        "S_omega": safety_class(),
    }
    for module in modules.values():
        module.eval()
    item = _profile_family(
        f"RA-MedFiLM-BARR-Lite/{family}", modules,
        image_size=image_size, warmup=warmup, iterations=iterations,
    )
    item["candidate_spec"] = {
        "variant_id": spec.variant_id,
        "architecture_sha256": spec.sha256(),
        "global_channels": spec.global_channels,
        "refiner_channels": spec.refiner_channels,
        "block_kind": spec.block_kind,
        "skip_fusion": spec.skip_fusion,
        "embedding_dim": spec.embedding_dim,
        "film_hidden_dim": spec.film_hidden_dim,
    }
    return item


def profile(*, image_size: int = 512, warmup: int = 2, iterations: int = 7) -> dict[str, Any]:
    if image_size != 512:
        raise ValueError("canonical BARR router profiling requires 512x512 inputs")
    if warmup < 0 or iterations < 2:
        raise ValueError("warmup must be nonnegative and iterations at least two")
    families = ("full", *CANDIDATE_SPECS.keys())
    profiles: dict[str, dict[str, Any]] = {}
    for family in families:
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--worker-family",
            family,
            "--image-size",
            str(image_size),
            "--warmup",
            str(warmup),
            "--iterations",
            str(iterations),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(
                f"isolated profile failed for {family}: "
                f"{completed.stderr[-4000:] or completed.stdout[-4000:]}"
            )
        profiles[family] = json.loads(completed.stdout)
    full_profile = profiles.pop("full")
    full_parameters = int(full_profile["parameters"]["unique_parameters"])
    full_profile["teacher_bundle_sha256"] = teacher_bundle_sha256({
        name: record["sha256"]
        for name, record in full_profile["checkpoint_provenance"].items()
    })
    candidates = profiles
    for candidate in candidates.values():
        candidate["parameter_reduction_vs_full"] = (
            1.0 - candidate["parameters"]["unique_parameters"] / full_parameters
        )
    return {
        "report_kind": "SYNTHETIC_PROFILE_NOT_RESEARCH_RESULTS",
        "device": "cpu",
        "cuda_available": torch.cuda.is_available(),
        "image_size": image_size,
        "batch_size": 1,
        "warmup_iterations": warmup,
        "timed_iterations": iterations,
        "runtime_configuration": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "torch_threads": 1,
        },
        "mac_definition": "one multiply-accumulate; FLOPs approximation = 2 * MACs",
        "mac_count_coverage": (
            "Conv2d and Linear multiply-accumulates only; excludes normalization, "
            "activations, pooling, interpolation, tensor arithmetic, and NumPy router "
            "feature reductions"
        ),
        "excluded_costs": [
            "dataset decoding/normalization",
            "checkpoint loading and model initialization",
        ],
        "included_router_feature_extraction": (
            "202-D full feature pipeline; Lite uses adaptive channel reduction "
            "for its new tap widths"
        ),
        "accuracy_status": "NOT_MEASURED; all model outputs are synthetic profiles only",
        "synthetic_outputs_are_research_evidence": False,
        "lite_trained_checkpoint_status": "NONE; all Lite weights were fresh initialization",
        "full_teacher_bundle_available": True,
        "branch_measurement_note": (
            "The trained router and safety final-layer outputs are deterministically "
            "overridden inside this isolated profiler only to force branch execution. "
            "A constant synthetic ROI is also substituted when the unmodified global "
            "checkpoint produces no proposal. These cases measure path cost, not model "
            "routing frequency, acceptance, segmentation, or accuracy."
        ),
        "full_model": full_profile,
        "lite_candidates": candidates,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-size", type=int, default=512)
    parser.add_argument("--warmup", type=int, default=2)
    parser.add_argument("--iterations", type=int, default=7)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--worker-family", choices=("full", *CANDIDATE_SPECS.keys()),
                        help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker_family is not None:
        result = _profile_one(
            args.worker_family,
            image_size=args.image_size,
            warmup=args.warmup,
            iterations=args.iterations,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    result = profile(image_size=args.image_size, warmup=args.warmup,
                     iterations=args.iterations)
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(serialized, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.out.with_suffix(args.out.suffix + ".tmp")
        temporary.write_text(serialized, encoding="utf-8")
        temporary.replace(args.out)
        print(f"synthetic-only profile written: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
