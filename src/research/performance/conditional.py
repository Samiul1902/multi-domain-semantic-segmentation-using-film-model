"""Conditional-computation benchmarking for the routed FULL and Lite systems.

The four canonical states are produced by the shared state machine, and this
module exercises each one.  Two decisions are scripted — the router's scalar and
the safety logit — and **nothing else is replaced**.  The global backbone, the
tap capture, the ROI geometry, the crop, the regional fusion and the safety
feature vector all run for real, because a stub backbone would replace the very
thing being measured and would make the branch cost meaningless.

Why scripting the decision is legitimate and not threshold tuning
-----------------------------------------------------------------
The frozen thresholds are never touched.  ``ROI_PROPOSAL_THRESHOLD`` (0.30),
``SEGMENTATION_OUTPUT_THRESHOLD`` (0.50) and ``SOMEGA_ACCEPT_THRESHOLD`` (0.50)
keep their values, and ``canonical_utility`` is still the function that decides.
What is scripted is the *model output* that the decision consumes, which is the
only way to reach a branch on demand without a trained model.  Every result here
is therefore a branch **cost** measurement, never a claim that the branch is
taken more or less often by a real model.

A separate warning the mission requires
---------------------------------------
Phase C observed the refiner firing on 100% of images for FULL and 0% for Lite on
its fixtures.  Those are fixture outcomes.  Nothing here infers a routing rate
for a trained model, and no runtime claim is made from a lower refiner count:
``fewer refiner calls is not by itself a lower total cost``, so the effective MAC
figure is reported alongside the branch count.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence

import numpy as np
import torch
from torch import nn

from src.research.evaluation import adapters as A
from src.research.evaluation import efficiency as EF
from src.research.evaluation import protocol as P
from src.research.evaluation import registry as REG
from src.research.full_pipeline import recipe as R
from src.research.stage6 import end_to_end as E

from . import bench as B

EVIDENCE_CLASS = B.EVIDENCE_CLASS

#: ``canonical_utility(s) = s - LAMBDA * C_ACTION`` (both are exact Fractions in
#: the frozen recipe); invert it so a caller can ask for a utility instead of a
#: raw score without hard-coding the constants.
UTILITY_OFFSET = float(R.LAMBDA * R.C_ACTION)

EXECUTE_STATES = ("EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT")


def score_for_utility(utility: float) -> float:
    """The raw router score that yields ``utility`` under ``canonical_utility``."""
    return float(utility) + UTILITY_OFFSET


class ScriptedScalar(nn.Module):
    """Runs the real module, then replaces its scalar output with a fixed value.

    The real module is executed, so its compute cost is still paid; only the
    number the decision consumes is substituted.  That keeps the measured branch
    cost honest while making the branch reachable on demand.
    """

    def __init__(self, inner: nn.Module, target: float) -> None:
        super().__init__()
        self.inner, self.target = inner, float(target)

    def forward(self, *args: Any, **kwargs: Any) -> torch.Tensor:
        out = self.inner(*args, **kwargs)
        return torch.full_like(out, self.target)


class _Scripted:
    """Context manager that scripts the router and/or safety decision, then restores."""

    def __init__(self, system: Any, *, router_score: Optional[float] = None,
                 safety_logit: Optional[float] = None) -> None:
        self.system, self.router_score, self.safety_logit = system, router_score, safety_logit
        self._saved: Dict[str, nn.Module] = {}

    def __enter__(self) -> "_Scripted":
        if self.router_score is not None:
            self._saved["b"] = self.system.b
            self.system.b = ScriptedScalar(self.system.b, self.router_score).to(self.system.device)
        if self.safety_logit is not None:
            self._saved["s"] = self.system.s
            self.system.s = ScriptedScalar(self.system.s, self.safety_logit).to(self.system.device)
        return self

    def __exit__(self, *exc: Any) -> None:
        for name, module in self._saved.items():
            setattr(self.system, name, module)
        self._saved.clear()


@dataclass(frozen=True)
class Scenario:
    """One named branch scenario."""

    name: str
    expected_state: str
    router_utility: Optional[float] = None
    safety_logit: Optional[float] = None
    low_priming: bool = False
    description: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "expected_state": self.expected_state,
                "router_utility": self.router_utility,
                "safety_logit": self.safety_logit,
                "low_priming": self.low_priming, "description": self.description}


#: The six scenarios §3 enumerates.  Utilities are expressed relative to the
#: frozen ``TAU_C8``; the safety logit is expressed as a probability.
SCENARIOS: Sequence[Scenario] = (
    Scenario("forced_skip", "FORCED_SKIP", low_priming=True,
             description="no predicted foreground above the ROI threshold -> no router call"),
    Scenario("router_skip", "SKIP_GLOBAL",
             router_utility=float(E.TAU_C8_FINAL_FLOAT) - 1.0,
             description="router utility below tau_c8 -> global map kept"),
    Scenario("safety_accept", "EXECUTE_THEN_ACCEPT",
             router_utility=float(E.TAU_C8_FINAL_FLOAT) + 1.0, safety_logit=+6.0,
             description="refiner runs, safety accepts the candidate"),
    Scenario("safety_reject", "EXECUTE_THEN_REJECT",
             router_utility=float(E.TAU_C8_FINAL_FLOAT) + 1.0, safety_logit=-6.0,
             description="refiner runs, safety rejects the candidate"),
)


def _suppress_foreground(model: nn.Module, probe: torch.Tensor, *,
                         threshold: float, margin: float,
                         ceiling: float = 0.02, attempts: int = 8) -> Dict[str, Any]:
    """Shift the final bias until **no pixel** on ``probe`` clears the ROI threshold.

    Why not reuse the mean-shifting primer
    --------------------------------------
    ``adapters._prime_output_bias`` centres the *mean* logit, which is the right
    construction for its own purpose (a non-degenerate fixture map).  It is the
    wrong construction for forcing FORCED_SKIP: a random image has a spatial logit
    range, so a centred mean still leaves pixels above the threshold and the router
    runs.  That is exactly how this fixture failed the first time it was run across
    three seeds — the calibration image was constant and the measured image was not.

    So this suppresses the **maximum** logit, on the same tensor the measurement
    uses, and then verifies with the real ``roi_geometry`` that no ROI is proposed.
    ``threshold`` and ``margin`` are the live values the inference path uses; the
    frozen constants are untouched and one bias scalar moves.
    """
    last = A._final_conv(model)
    if last is None or last.bias is None:
        raise RuntimeError("no final 1-channel conv with a bias to suppress")
    target = math.log(ceiling / (1.0 - ceiling))
    was_training = model.training
    model.eval()
    try:
        with torch.no_grad():
            task = torch.zeros(1, dtype=torch.long, device=probe.device)
            for _ in range(int(attempts)):
                logits = model(probe, task).float()
                if float(torch.sigmoid(logits).max()) <= ceiling:
                    break
                last.bias.add_(target - float(logits.max()))
            logits = model(probe, task).float()
            probability = torch.sigmoid(logits)
            geometry = E.roi_geometry(probability[0, 0].cpu().numpy(), threshold, margin)
    finally:
        model.train(was_training)
    if geometry is not None:
        raise RuntimeError(
            "could not suppress foreground below the ROI proposal threshold on the "
            "benchmark probe image; FORCED_SKIP is not reachable with this fixture")
    return {"primed": True, "mode": "max-logit suppression on the benchmark probe",
            "ceiling_probability": float(ceiling),
            "achieved_max_probability": float(probability.max()),
            "roi_proposed": False,
            "threshold_used": float(threshold), "margin_used": float(margin),
            "threshold_unchanged": float(P.ROI_PROPOSAL_THRESHOLD)}


def build_benchmark_adapter(model_key: str, *, seed: int = 42, device: str = "cuda",
                            low_priming: bool = False) -> A.ModelAdapter:
    """A synthetic routed adapter, optionally primed so no ROI can be proposed.

    ``low_priming`` suppresses the foreground on the **same** probe tensor the
    measurement will use, against the system's own threshold and margin, so
    FORCED_SKIP is reachable for every seed.  It is a fixture construction — one
    bias scalar — and it changes no threshold.
    """
    adapter = A.build_synthetic(model_key, seed, device=device)
    if low_priming:
        system = adapter._system
        probe = B.synthetic_image(1, device=adapter.device)
        adapter._synthetic_priming = _suppress_foreground(
            system.g, probe, threshold=float(system.roi_threshold),
            margin=float(system.roi_margin))
    adapter.load()
    return adapter


def run_scenario(model_key: str, scenario: Scenario, *, seed: int = 42,
                 device: str = "cuda", warmup: int = 5, repeats: int = 20) -> Dict[str, Any]:
    """Execute one scenario and verify it produced the state it claims to."""
    adapter = build_benchmark_adapter(model_key, seed=seed, device=device,
                                      low_priming=scenario.low_priming)
    try:
        system = adapter._system
        image = B.synthetic_image(1, device=device)
        task = 3
        script_kwargs: Dict[str, Any] = {}
        if scenario.router_utility is not None:
            script_kwargs["router_score"] = score_for_utility(scenario.router_utility)
        if scenario.safety_logit is not None:
            script_kwargs["safety_logit"] = scenario.safety_logit

        with _Scripted(system, **script_kwargs):
            probe = adapter.predict(image, task)
            if probe.state != scenario.expected_state:
                raise AssertionError(
                    f"{model_key}/{scenario.name}: expected {scenario.expected_state}, "
                    f"got {probe.state} (router_score={probe.router_score}, "
                    f"safety={probe.safety_probability})")
            latency = B.time_call(lambda: adapter.predict(image, task),
                                  warmup=warmup, repeats=repeats, device=device)
            memory = B.measure_peak_memory(lambda: adapter.predict(image, task), device=device)

        counters_before = dict(system.counters)
        with _Scripted(system, **script_kwargs):
            adapter.predict(image, task)
        counters = {k: system.counters[k] - counters_before[k] for k in system.counters}

        return {
            "model_key": model_key, "seed": int(seed), "scenario": scenario.name,
            "expected_state": scenario.expected_state, "observed_state": probe.state,
            "state_matches": probe.state == scenario.expected_state,
            "branch_latency_ms": latency, "memory": memory,
            "component_invocations": counters,
            "refiner_executed": probe.state in EXECUTE_STATES,
            "description": scenario.description,
            "evidence_class": EVIDENCE_CLASS,
        }
    finally:
        adapter.close()


# --------------------------------------------------------------------------- #
# The three-way comparison §3 requires
# --------------------------------------------------------------------------- #
def compare_execution_modes(model_key: str, *, seed: int = 42, device: str = "cuda",
                            warmup: int = 5, repeats: int = 20) -> Dict[str, Any]:
    """Global-only vs always-refine vs conditional, on the same fixture image.

    * ``global_only``      — the G forward alone; no router, no ROI, no refiner.
    * ``always_refine``    — router forced positive and safety forced to accept,
      so the refiner and the safety gate always run.
    * ``conditional``      — the unscripted decision the fixture happens to make.
    """
    adapter = build_benchmark_adapter(model_key, seed=seed, device=device)
    try:
        system = adapter._system
        image = B.synthetic_image(1, device=device)
        task = torch.tensor([3], dtype=torch.long, device=adapter.device)

        global_only = B.time_call(lambda: system.g(image, task_ids=task),
                                  warmup=warmup, repeats=repeats, device=device)

        with _Scripted(system, router_score=score_for_utility(
                float(E.TAU_C8_FINAL_FLOAT) + 1.0), safety_logit=+6.0):
            always_probe = adapter.predict(image, 3)
            always = B.time_call(lambda: adapter.predict(image, 3),
                                 warmup=warmup, repeats=repeats, device=device)
        if always_probe.state != "EXECUTE_THEN_ACCEPT":
            raise AssertionError(f"always-refine did not accept: {always_probe.state}")

        conditional_probe = adapter.predict(image, 3)
        conditional = B.time_call(lambda: adapter.predict(image, 3),
                                  warmup=warmup, repeats=repeats, device=device)

        macs = EF.count_macs(adapter)
        always_macs = None
        if macs.get("macs_global_only") is not None:
            always_macs = int(macs["macs_global_only"] + macs.get("macs_router_per_image", 0)
                              + macs.get("macs_refiner_per_call", 0)
                              + macs.get("macs_safety_per_call", 0))
        rate = 1.0 if conditional_probe.state in EXECUTE_STATES else 0.0
        effective_macs = None
        if always_macs is not None:
            effective_macs = int(macs["macs_global_only"] + macs.get("macs_router_per_image", 0)
                                 + rate * (macs.get("macs_refiner_per_call", 0)
                                           + macs.get("macs_safety_per_call", 0)))

        overhead = None
        if global_only["median"] and always["median"]:
            overhead = always["median"] - global_only["median"]

        return {
            "model_key": model_key, "seed": int(seed),
            "global_only_ms": global_only, "always_refine_ms": always,
            "conditional_ms": conditional,
            "conditional_state": conditional_probe.state,
            "refiner_invocation_rate_observed": rate,
            "non_global_overhead_ms": overhead,
            "macs_global_only": macs.get("macs_global_only"),
            "macs_if_always_refine": always_macs,
            "effective_macs_per_image": effective_macs,
            "evidence_class": EVIDENCE_CLASS,
            "caveat": ("The conditional figure is the fixture's own decision. A lower "
                       "refiner count is not by itself a lower total cost, so the "
                       "effective MAC figure is reported beside it."),
        }
    finally:
        adapter.close()


# --------------------------------------------------------------------------- #
# ROI geometry edge cases (pure function, no model)
# --------------------------------------------------------------------------- #
def _blob(size: int, r0: int, r1: int, c0: int, c1: int, value: float = 0.9) -> np.ndarray:
    map_ = np.zeros((size, size), dtype=np.float32)
    map_[r0:r1, c0:c1] = value
    return map_


def roi_edge_cases(*, size: int = 512) -> List[Dict[str, Any]]:
    """Empty, tiny, centred, border-clipped and full-canvas ROI behaviour.

    ``roi_geometry`` is the function that decides FORCED_SKIP, so its edge cases
    are tested directly rather than inferred from a model's output.  The threshold
    and margin are the frozen ones the inference path is constructed with, and the
    protocol constant is asserted to agree with the data-layer constant so a drift
    between the two cannot go unnoticed.
    """
    from src.data.barr_roi import ROI_FRACTIONAL_MARGIN, ROI_PROPOSAL_THRESHOLD

    if ROI_PROPOSAL_THRESHOLD != P.ROI_PROPOSAL_THRESHOLD:      # pragma: no cover - drift
        raise RuntimeError(
            f"ROI threshold drift: data layer {ROI_PROPOSAL_THRESHOLD} != protocol "
            f"{P.ROI_PROPOSAL_THRESHOLD}")
    threshold, margin = P.ROI_PROPOSAL_THRESHOLD, ROI_FRACTIONAL_MARGIN
    cases = [
        ("empty_map", np.zeros((size, size), np.float32), None),
        ("all_below_threshold", np.full((size, size), 0.10, np.float32), None),
        ("single_pixel", _blob(size, 256, 257, 256, 257), "clipped"),
        ("centred_blob", _blob(size, 200, 300, 200, 300), "clipped"),
        ("border_touching", _blob(size, 0, 64, 0, 64), "clipped"),
        ("full_canvas", np.full((size, size), 0.9, np.float32), "clipped"),
    ]
    out: List[Dict[str, Any]] = []
    for name, prob, expectation in cases:
        geom = E.roi_geometry(prob, threshold, margin)
        if expectation is None:
            if geom is not None:
                raise AssertionError(f"{name}: expected no ROI, got {geom}")
        else:
            if geom is None:
                raise AssertionError(f"{name}: expected an ROI, got None")
            for key in ("clip_y1", "clip_y2", "clip_x1", "clip_x2"):
                if key not in geom:
                    raise AssertionError(f"{name}: geometry missing {key}")
            y1, y2 = int(geom["clip_y1"]), int(geom["clip_y2"])
            x1, x2 = int(geom["clip_x1"]), int(geom["clip_x2"])
            if not (0 <= y1 < y2 <= size and 0 <= x1 < x2 <= size):
                raise AssertionError(f"{name}: geometry out of canvas: {geom}")
            side = float(geom["crop_side_pixels"])
            if not (np.isfinite(side) and side > 0):
                raise AssertionError(f"{name}: non-positive crop side: {geom}")
        out.append({"case": name, "roi": None if geom is None else
                    {k: geom[k] for k in ("clip_y1", "clip_y2", "clip_x1", "clip_x2",
                                          "crop_side_pixels", "effective_magnification",
                                          "predicted_foreground_pixels")},
                    "state": "FORCED_SKIP" if geom is None else "ROI_PROPOSED"})
    return out


def benchmark_all_scenarios(*, device: str = "cuda", seeds: Sequence[int] = (42,),
                            warmup: int = 5, repeats: int = 20) -> Dict[str, Any]:
    """Every routed model × every scenario, plus the three-way comparison."""
    records: List[Dict[str, Any]] = []
    comparisons: List[Dict[str, Any]] = []
    for model_key in (REG.FULL, REG.LITE):
        for seed in seeds:
            for scenario in SCENARIOS:
                records.append(run_scenario(model_key, scenario, seed=seed, device=device,
                                            warmup=warmup, repeats=repeats))
            comparisons.append(compare_execution_modes(model_key, seed=seed, device=device,
                                                       warmup=warmup, repeats=repeats))
    return {"schema": "phase_d_conditional_v1", "evidence_class": EVIDENCE_CLASS,
            "scenarios": [s.as_dict() for s in SCENARIOS],
            "records": records, "comparisons": comparisons,
            "roi_edge_cases": roi_edge_cases(),
            "note": ("Branch costs, not routing rates. Fixture outcomes are not trained-model "
                     "behaviour and no threshold was tuned.")}


__all__ = ["EXECUTE_STATES", "SCENARIOS", "Scenario", "ScriptedScalar", "UTILITY_OFFSET",
           "benchmark_all_scenarios", "build_benchmark_adapter", "compare_execution_modes",
           "roi_edge_cases", "run_scenario", "score_for_utility"]
