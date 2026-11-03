"""One evaluation interface for all eight models.

Every adapter exposes exactly the same three things:

``predict(image, task_id) -> Prediction``
    Ground-truth-free.  The signature contains no mask, label, Dice, patient or
    oracle argument, and :func:`audit_gt_free` re-checks that on the live
    signatures rather than trusting the docstring.
``parameter_count()``
    Unique inference parameters (shared tensors counted once).
``identity()``
    The provenance block a result must carry.

The three adapter kinds are genuinely different and are not flattened into one:

``ROUTED`` (FULL, Lite)
    Invokes the complete G/R/B/S graph through the canonical
    :class:`~src.research.stage6.end_to_end.GTFreeBARRInference` state machine.
    The four states — ``FORCED_SKIP``, ``SKIP_GLOBAL``, ``EXECUTE_THEN_ACCEPT``,
    ``EXECUTE_THEN_REJECT`` — are produced by that shared implementation, so the
    evaluator cannot disagree with the system it is measuring.
``TASK_CONDITIONED`` (GlobalMedFiLM)
    The real task-conditioned model, called with its task id.
``PLAIN`` (five baselines)
    A single segmentation network with **no task input**.  Feeding one a task id
    would be a protocol change, not a fairness correction, so it is not done.

Weight policy
-------------
A ``REAL`` adapter loads a genuine checkpoint and refuses to run without one.
A ``SYNTHETIC`` adapter instantiates the real architecture with a deterministic
seed and stamps ``SYNTHETIC_TEST_ONLY``; it exists to exercise the plumbing and
can never be published as a research cell.
"""
from __future__ import annotations

import hashlib
import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

import numpy as np
import torch
from torch import nn

from src.models.barr.phase25_models import BARRBenefitRouterV1, BARRPostSafetyV1
from src.models.barr.ra_medfilm_barr import TAU_C8_FINAL_FLOAT
from src.models.barr.regional_refiner import BARRRegionalRefinerV1
from src.models.film.global_medfilm import GlobalMedFiLM
from src.models.lite.ra_medfilm_barr_lite import (LiteGlobalMedFiLM,
                                                  LiteRegionalRefiner)
from src.research.c3_baselines import experiment as C3
from src.research.full_pipeline import recipe as R
from src.research.stage6.end_to_end import GTFreeBARRInference

from . import protocol as P
from . import registry as REG

FORBIDDEN_ARGUMENTS = ("gt", "mask", "label", "target", "dice", "patient", "oracle", "truth")
ROUTER_SCALAR_WIDTH = 8      # len(ROUTER_SCALAR_IDX) in end_to_end
SAFETY_FEATURE_WIDTH = 16


class AdapterError(RuntimeError):
    pass


class AdapterUnavailable(AdapterError):
    """Raised when a real checkpoint family is absent or incomplete."""


class CheckpointIdentityError(AdapterError):
    """Raised when a checkpoint does not match the declared model/seed/architecture."""


@dataclass
class Prediction:
    """One image's inference output.  Produced without any ground truth."""

    probability: np.ndarray                 # float32 [H, W] in [0, 1]
    global_probability: np.ndarray          # float32 [H, W] in [0, 1]
    state: str = "NOT_APPLICABLE"
    router_score: Optional[float] = None
    safety_probability: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def binary(self, threshold: float = P.SEGMENTATION_OUTPUT_THRESHOLD) -> np.ndarray:
        return (self.probability >= float(threshold)).astype(np.uint8)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


_POPULATION_CACHE: list = []


def _canonical_population():
    """The canonical population, loaded once.

    ``load_canonical_population`` reads the ROUTER split manifest and the TRAIN
    manifest only.  It never opens TEST, which is what makes it usable here.
    """
    if not _POPULATION_CACHE:
        from src.research.full_pipeline.population import load_canonical_population
        _POPULATION_CACHE.append(load_canonical_population())
    return _POPULATION_CACHE[0]


def _unique_parameters(modules) -> int:
    seen: set = set()
    total = 0
    for module in modules:
        for p in module.parameters():
            if id(p) not in seen:
                seen.add(id(p))
                total += int(p.numel())
    return total


def _validate_image(image: torch.Tensor) -> torch.Tensor:
    if not isinstance(image, torch.Tensor):
        raise AdapterError(f"image must be a torch.Tensor, got {type(image).__name__}")
    if image.ndim != 4 or image.shape[0] != 1 or image.shape[1] != 3:
        raise AdapterError(f"image must be [1,3,H,W], got {tuple(image.shape)}")
    if not torch.isfinite(image).all():
        raise AdapterError("image contains NaN or Inf")
    if float(image.min()) < 0.0 or float(image.max()) > 1.0:
        raise AdapterError("image must be scaled to [0, 1]")
    return image


# --------------------------------------------------------------------------- #
# Base
# --------------------------------------------------------------------------- #
class ModelAdapter:
    """Common surface.  Subclasses implement ``_predict`` and ``identity``."""

    kind = "ABSTRACT"
    evidence_class = P.REAL_VAL_EVIDENCE
    source = "real"

    def __init__(self, model_key: str, seed: int, *, device: str = "cpu") -> None:
        self.spec = REG.spec(model_key)
        self.model_key, self.seed = model_key, int(seed)
        self.device = torch.device(device)
        self._loaded = False

    # -- lifecycle ------------------------------------------------------- #
    def load(self) -> "ModelAdapter":
        raise NotImplementedError

    def close(self) -> None:
        self._loaded = False

    # -- evaluation surface ---------------------------------------------- #
    def predict(self, image: torch.Tensor, task_id: int) -> Prediction:
        if not self._loaded:
            raise AdapterError(f"{self.model_key}: load() must succeed before predict()")
        image = _validate_image(image)
        if isinstance(task_id, bool) or int(task_id) != task_id or int(task_id) not in range(4):
            raise AdapterError(f"task_id {task_id!r} is not an integer in 0..3")
        return self._predict(image, int(task_id))

    def _predict(self, image: torch.Tensor, task_id: int) -> Prediction:
        raise NotImplementedError

    def parameter_count(self) -> int:
        raise NotImplementedError

    def identity(self) -> Dict[str, Any]:
        raise NotImplementedError

    # -- helpers --------------------------------------------------------- #
    def __enter__(self) -> "ModelAdapter":
        return self.load()

    def __exit__(self, *exc: Any) -> None:
        self.close()


# --------------------------------------------------------------------------- #
# Routed: FULL and Lite
# --------------------------------------------------------------------------- #
class RoutedAdapter(ModelAdapter):
    """FULL or Lite, driven by the canonical GT-free state machine."""

    kind = "ROUTED"

    def __init__(self, model_key: str, seed: int, *, device: str = "cpu",
                 system: Optional[GTFreeBARRInference] = None,
                 component_sha256: Optional[Mapping[str, str]] = None,
                 architecture_id: Optional[str] = None,
                 run_root: Optional[Path] = None) -> None:
        super().__init__(model_key, seed, device=device)
        self._system = system
        self._component_sha256 = dict(component_sha256 or {})
        self._architecture_id = architecture_id
        self._run_root = run_root

    # -- real loading ---------------------------------------------------- #
    @classmethod
    def load_real(cls, model_key: str, seed: int, *, run_root: Path,
                  device: str = "cpu") -> "RoutedAdapter":
        """Load one real seed family from ``run_root``; refuse a partial family."""
        adapter = cls(model_key, seed, device=device, run_root=Path(run_root))
        adapter._load_family()
        return adapter

    def _load_family(self) -> None:
        if self._run_root is None:
            raise AdapterUnavailable(
                f"{self.model_key} seed {self.seed}: no checkpoint root was supplied; "
                "a randomly initialised model may not produce a research score")
        root = Path(self._run_root)
        if not root.is_dir():
            raise AdapterUnavailable(
                f"{self.model_key} seed {self.seed}: checkpoint root {root} does not exist")
        if self.model_key == REG.FULL:
            from src.research.full_pipeline.context import RunContext
            from src.research.full_pipeline.inference import FamilyBundle
            from src.research.full_pipeline.seeds import SeedFamily

            ctx = RunContext(family=SeedFamily(self.seed, label=f"seed{self.seed}"),
                             root=root, bounds=R.OperationalBounds(),
                             population=_canonical_population())
            bundle = FamilyBundle.load(ctx, device="cpu")
            self._system = bundle.build_gtfree(device=str(self.device))
            self._component_sha256 = dict(bundle.shas)
            self._architecture_id = "full_family_g"
        elif self.model_key == REG.LITE:
            from src.research.lite_pipeline.context import make_lite_context
            from src.research.lite_pipeline.inference import LiteBundle

            ctx = make_lite_context(self.seed, root=root,
                                    population=_canonical_population())
            bundle = LiteBundle.load(ctx, device="cpu")
            self._system = bundle.build_gtfree(device=str(self.device))
            self._component_sha256 = dict(bundle.shas)
            self._architecture_id = bundle.variant_id
        else:  # pragma: no cover - guarded by the registry
            raise AdapterError(f"{self.model_key} is not a routed model")
        self._loaded = True

    def load(self) -> "RoutedAdapter":
        if self._system is None:
            if self.source == "synthetic":
                raise AdapterError("synthetic routed adapters are built by build_synthetic")
            self._load_family()
        else:
            self._loaded = True
        return self

    def _predict(self, image: torch.Tensor, task_id: int) -> Prediction:
        out = self._system.infer(image, task_id)
        prob = np.asarray(out["final_probability"], dtype=np.float32)
        glob = np.asarray(out["global_probability"], dtype=np.float32)
        if prob.shape != glob.shape:
            raise AdapterError(f"final {prob.shape} and global {glob.shape} maps differ")
        return Prediction(probability=prob, global_probability=glob,
                          state=str(out["state"]),
                          router_score=(None if out.get("router_score") is None
                                        else float(out["router_score"])),
                          safety_probability=(None if out.get("safety_probability") is None
                                              else float(out["safety_probability"])))

    def parameter_count(self) -> int:
        if self._system is None:
            raise AdapterError("adapter not loaded")
        return int(self._system.unique_parameters())

    def identity(self) -> Dict[str, Any]:
        if not self._component_sha256:
            raise AdapterError("routed adapter has no component provenance")
        return {"model_key": self.model_key, "seed": self.seed,
                "adapter_kind": self.kind, "architecture_id": self._architecture_id,
                "component_sha256": dict(self._component_sha256),
                "component_chain": list(self.spec.chain),
                "evidence_class": self.evidence_class,
                "thresholds": {"roi_proposal": P.ROI_PROPOSAL_THRESHOLD,
                               "segmentation_output": P.SEGMENTATION_OUTPUT_THRESHOLD,
                               "safety_accept": P.SOMEGA_ACCEPT_THRESHOLD},
                "roi_rule": {"expansion": P.ROI_EXPANSION_FACTOR,
                             "fractional_margin": P.ROI_FRACTIONAL_MARGIN},
                "synthetic_fixture_priming": getattr(self, "_synthetic_priming", None)}


# --------------------------------------------------------------------------- #
# Task-conditioned: GlobalMedFiLM
# --------------------------------------------------------------------------- #
class TaskConditionedAdapter(ModelAdapter):
    """The real GlobalMedFiLM, called with its task id."""

    kind = "TASK_CONDITIONED"

    def __init__(self, model_key: str, seed: int, *, device: str = "cpu",
                 model: Optional[nn.Module] = None,
                 checkpoint_path: Optional[Path] = None,
                 checkpoint_sha256: Optional[str] = None) -> None:
        super().__init__(model_key, seed, device=device)
        self._model = model
        self._checkpoint_path = Path(checkpoint_path) if checkpoint_path else None
        self._checkpoint_sha256 = checkpoint_sha256

    def load(self) -> "TaskConditionedAdapter":
        if self._model is None:
            if self._checkpoint_path is None:
                raise AdapterUnavailable(
                    f"{self.model_key} seed {self.seed}: no checkpoint supplied; "
                    "a randomly initialised model may not produce a research score")
            if not self._checkpoint_path.is_file():
                raise AdapterUnavailable(f"missing checkpoint {self._checkpoint_path}")
            model = GlobalMedFiLM(task_count=4, in_channels=3, out_channels=1)
            state = torch.load(self._checkpoint_path, map_location="cpu", weights_only=False)
            weights = state.get("model_state", state) if isinstance(state, dict) else state
            model.load_state_dict(weights)
            self._model = model
            self._checkpoint_sha256 = _sha256_file(self._checkpoint_path)
        self._model.eval().requires_grad_(False).to(self.device)
        self._loaded = True
        return self

    @torch.inference_mode()
    def _predict(self, image: torch.Tensor, task_id: int) -> Prediction:
        logits = self._model(image.to(self.device), torch.tensor([task_id], device=self.device))
        prob = torch.sigmoid(logits.float())[0, 0].cpu().numpy().astype(np.float32)
        if not np.isfinite(prob).all():
            raise AdapterError(f"{self.model_key}: non-finite probability map")
        return Prediction(probability=prob, global_probability=prob)

    def parameter_count(self) -> int:
        if self._model is None:
            raise AdapterError("adapter not loaded")
        return _unique_parameters([self._model])

    def identity(self) -> Dict[str, Any]:
        return {"model_key": self.model_key, "seed": self.seed,
                "adapter_kind": self.kind,
                "architecture_id": "global_medfilm_film_5_sites",
                "checkpoint_sha256": self._checkpoint_sha256,
                "checkpoint_path": str(self._checkpoint_path) if self._checkpoint_path else None,
                "evidence_class": self.evidence_class,
                "thresholds": {"segmentation_output": P.SEGMENTATION_OUTPUT_THRESHOLD},
                "takes_task_id": True,
                "synthetic_fixture_priming": getattr(self, "_synthetic_priming", None)}


# --------------------------------------------------------------------------- #
# Plain: the five external baselines
# --------------------------------------------------------------------------- #
class PlainAdapter(ModelAdapter):
    """A single segmentation network with no task input."""

    kind = "PLAIN"

    def __init__(self, model_key: str, seed: int, *, device: str = "cpu",
                 model: Optional[nn.Module] = None,
                 checkpoint_path: Optional[Path] = None,
                 checkpoint_sha256: Optional[str] = None) -> None:
        super().__init__(model_key, seed, device=device)
        self._model = model
        self._checkpoint_path = Path(checkpoint_path) if checkpoint_path else None
        self._checkpoint_sha256 = checkpoint_sha256

    def load(self) -> "PlainAdapter":
        if self._model is None:
            if self._checkpoint_path is None:
                raise AdapterUnavailable(
                    f"{self.model_key} seed {self.seed}: no checkpoint supplied; "
                    "a randomly initialised model may not produce a research score")
            if not self._checkpoint_path.is_file():
                raise AdapterUnavailable(f"missing checkpoint {self._checkpoint_path}")
            model = C3.build_model(REG.C3_ARCHITECTURE_KEY[self.model_key])
            state = torch.load(self._checkpoint_path, map_location="cpu", weights_only=False)
            weights = state.get("model_state", state) if isinstance(state, dict) else state
            model.load_state_dict(weights)
            self._model = model
            self._checkpoint_sha256 = _sha256_file(self._checkpoint_path)
        self._model.eval().requires_grad_(False).to(self.device)
        self._loaded = True
        return self

    @torch.inference_mode()
    def _predict(self, image: torch.Tensor, task_id: int) -> Prediction:
        logits = self._model(image.to(self.device))
        prob = torch.sigmoid(logits.float())[0, 0].cpu().numpy().astype(np.float32)
        if not np.isfinite(prob).all():
            raise AdapterError(f"{self.model_key}: non-finite probability map")
        return Prediction(probability=prob, global_probability=prob)

    def parameter_count(self) -> int:
        if self._model is None:
            raise AdapterError("adapter not loaded")
        return _unique_parameters([self._model])

    def identity(self) -> Dict[str, Any]:
        arch = REG.architecture_identity(self.model_key)
        return {"model_key": self.model_key, "seed": self.seed,
                "adapter_kind": self.kind, "architecture": arch["architecture"],
                "checkpoint_sha256": self._checkpoint_sha256,
                "checkpoint_path": str(self._checkpoint_path) if self._checkpoint_path else None,
                "evidence_class": self.evidence_class,
                "thresholds": {"segmentation_output": P.SEGMENTATION_OUTPUT_THRESHOLD},
                "takes_task_id": False,
                "synthetic_fixture_priming": getattr(self, "_synthetic_priming", None)}


# --------------------------------------------------------------------------- #
# Synthetic construction
# --------------------------------------------------------------------------- #
def _seeded(seed: int) -> None:
    torch.manual_seed(int(seed) & 0x7FFFFFFF)
    np.random.seed(int(seed) & 0x7FFFFFFF)


def _final_conv(model: nn.Module) -> Optional[nn.Conv2d]:
    last = None
    for module in model.modules():
        if isinstance(module, nn.Conv2d) and module.out_channels == 1:
            last = module
    return last


def _prime_output_bias(model: nn.Module, forward, *, target_logit: float = 0.3) -> Dict[str, Any]:
    """Shift the final 1x1 bias so an untrained fixture is not degenerate.

    A freshly initialised network emits a near-constant probability map, which
    would make every synthetic cell score the same value and would never open an
    ROI.  This is a **fixture construction**, not training: it changes one bias
    scalar, it is recorded in the adapter identity, and the resulting numbers are
    still stamped ``SYNTHETIC_TEST_ONLY``.
    """
    last = _final_conv(model)
    if last is None or last.bias is None:
        return {"primed": False, "reason": "no final 1-channel conv with a bias"}
    was_training = model.training
    model.eval()
    try:
        with torch.no_grad():
            mean = float(forward().float().mean())
            last.bias.add_(float(target_logit) - mean)
    finally:
        model.train(was_training)
    return {"primed": True, "delta": float(target_logit) - mean,
            "target_logit": float(target_logit)}


def _synthetic_normaliser(width: int, seed: int) -> Dict[str, torch.Tensor]:
    gen = torch.Generator().manual_seed(int(seed) & 0x7FFFFFFF)
    return {"normalizer_mu": torch.zeros(width),
            "normalizer_sigma": torch.ones(width),
            "normalizer_constant_mask": torch.zeros(width, dtype=torch.bool),
            "_generator_state": gen.get_state()}


def build_synthetic(model_key: str, seed: int, *, device: str = "cpu",
                    variant: str = "depthwise_compact") -> ModelAdapter:
    """Instantiate the real architecture with a deterministic seed.

    This exists only to exercise the evaluation plumbing.  Every artifact it
    produces is stamped ``SYNTHETIC_TEST_ONLY`` and can never complete a research
    cell.
    """
    _seeded(seed + 1000 * (REG.DISPLAY_ORDER.index(model_key) + 1))
    if model_key in (REG.FULL, REG.LITE):
        if model_key == REG.FULL:
            g = GlobalMedFiLM(task_count=4, in_channels=3, out_channels=1)
            r = BARRRegionalRefinerV1()
            adapter_cls = RoutedAdapter
            arch_id = "full_family_g_synthetic"
        else:
            from src.research.lite_pipeline import recipe as L
            spec = L.spec(variant)
            g = LiteGlobalMedFiLM(spec, task_count=4)
            r = LiteRegionalRefiner(spec)
            adapter_cls = RoutedAdapter
            arch_id = spec.variant_id
        b, s = BARRBenefitRouterV1(), BARRPostSafetyV1()
        probe = torch.full((1, 3, P.RESOLUTION, P.RESOLUTION), 0.5)
        priming = _prime_output_bias(
            g, lambda: g(probe, torch.zeros(1, dtype=torch.long)))
        extra = {"feature_builder": _lite_builder()} if model_key == REG.LITE else {}
        system = GTFreeBARRInference(
            global_model=g, refiner=r, router=b, safety=s,
            router_state=_synthetic_normaliser(ROUTER_SCALAR_WIDTH, seed),
            safety_state=_synthetic_normaliser(SAFETY_FEATURE_WIDTH, seed + 1),
            tau_c8=TAU_C8_FINAL_FLOAT,
            accept_threshold=P.SOMEGA_ACCEPT_THRESHOLD,
            roi_threshold=P.ROI_PROPOSAL_THRESHOLD,
            roi_margin=P.ROI_FRACTIONAL_MARGIN,
            device=device,
            uses_tap_forward=(model_key == REG.LITE),
            **extra,
        )
        adapter = adapter_cls(model_key, seed, device=device, system=system,
                              component_sha256={c: f"SYNTHETIC::{c}::{seed}"
                                                for c in ("G", "R", "B", "S")},
                              architecture_id=arch_id)
        adapter.source, adapter.evidence_class = "synthetic", P.SYNTHETIC_EVIDENCE
        adapter._synthetic_priming = priming
        adapter._loaded = True
        return adapter

    if model_key == REG.GLOBAL:
        model = GlobalMedFiLM(task_count=4, in_channels=3, out_channels=1)
        probe = torch.full((1, 3, P.RESOLUTION, P.RESOLUTION), 0.5)
        priming = _prime_output_bias(model, lambda: model(probe, torch.zeros(1, dtype=torch.long)))
        adapter = TaskConditionedAdapter(model_key, seed, device=device, model=model)
        adapter.source, adapter.evidence_class = "synthetic", P.SYNTHETIC_EVIDENCE
        adapter._checkpoint_sha256 = f"SYNTHETIC::GLOBAL::{seed}"
        adapter._synthetic_priming = priming
        return adapter.load()

    model = C3.build_model(REG.C3_ARCHITECTURE_KEY[model_key])
    probe = torch.full((1, 3, P.RESOLUTION, P.RESOLUTION), 0.5)
    priming = _prime_output_bias(model, lambda: model(probe))
    adapter = PlainAdapter(model_key, seed, device=device, model=model)
    adapter.source, adapter.evidence_class = "synthetic", P.SYNTHETIC_EVIDENCE
    adapter._checkpoint_sha256 = f"SYNTHETIC::{model_key}::{seed}"
    adapter._synthetic_priming = priming
    return adapter.load()


def _lite_builder():
    from src.research.lite_pipeline.features import lite_feature_builder
    return lite_feature_builder


def build_adapter(model_key: str, seed: int, *, device: str = "cpu",
                  source: str = "real", **kwargs: Any) -> ModelAdapter:
    """Factory used by the runner.

    ``source="real"`` returns an *unloaded* adapter whose ``load()`` fails closed
    when the checkpoint family is absent — that is how a cell becomes MISSING
    instead of silently becoming a random-weight number.
    """
    if source == "synthetic":
        return build_synthetic(model_key, seed, device=device,
                               variant=kwargs.get("variant", "depthwise_compact"))
    kind = REG.ADAPTER_KINDS[model_key]
    if kind == "ROUTED":
        return RoutedAdapter(model_key, seed, device=device,
                             run_root=kwargs.get("run_root"))
    if kind == "TASK_CONDITIONED":
        return TaskConditionedAdapter(model_key, seed, device=device,
                                      checkpoint_path=kwargs.get("checkpoint_path"))
    return PlainAdapter(model_key, seed, device=device,
                        checkpoint_path=kwargs.get("checkpoint_path"))


# --------------------------------------------------------------------------- #
# GT-free audit
# --------------------------------------------------------------------------- #
def audit_gt_free() -> Dict[str, Any]:
    """Re-check the GT-free property on the live adapter signatures."""
    audited = {
        "ModelAdapter.predict": ModelAdapter.predict,
        "RoutedAdapter._predict": RoutedAdapter._predict,
        "TaskConditionedAdapter._predict": TaskConditionedAdapter._predict,
        "PlainAdapter._predict": PlainAdapter._predict,
        "build_adapter": build_adapter,
        "build_synthetic": build_synthetic,
    }
    signatures: Dict[str, list] = {}
    findings = []
    for name, fn in audited.items():
        params = [p for p in inspect.signature(fn).parameters if p != "self"]
        signatures[name] = params
        findings += [f"{name}:{p}" for p in params
                     if any(f in p.lower() for f in FORBIDDEN_ARGUMENTS)]
    return {"audited_signatures": signatures, "gt_like_parameters": findings,
            "gt_free": not findings}


__all__ = ["AdapterError", "AdapterUnavailable", "CheckpointIdentityError",
           "ModelAdapter", "PlainAdapter", "Prediction", "RoutedAdapter",
           "TaskConditionedAdapter", "audit_gt_free", "build_adapter",
           "build_synthetic"]
