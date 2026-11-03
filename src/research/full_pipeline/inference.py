"""Per-seed family loading and genuine end-to-end inference.

The inference path is the verified Stage-6 GT-free adapter
(:class:`src.research.stage6.end_to_end.GTFreeBARRInference`), driven by the four
checkpoints of ONE seed family::

    image + task_id
      -> GlobalMedFiLM                      (G, exactly once)
      -> ROI proposal from p_global          (0.30, expansion 1.50)
      -> 202-D pre-refinement features       (three frozen taps + scalars)
      -> Benefit Router                      (B, utility vs tau_C8_final)
      -> Regional Refiner                    (R, only when selected)
      -> deterministic regional fusion       (replace inside ROI, no blending)
      -> Post-Refinement Safety              (S, accept iff sigmoid >= 0.50)
      -> final probability map -> binary mask (0.50)

Four deterministic states are reachable: ``FORCED_SKIP``, ``SKIP_GLOBAL``,
``EXECUTE_THEN_ACCEPT`` and ``EXECUTE_THEN_REJECT``.

Nothing in this module accepts a mask, a Dice value, a gain label or a patient
identifier.  :func:`audit_ground_truth_free` re-checks that property on the live
signatures every time it is called.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

import numpy as np
import torch
from torch import nn

from . import recipe as R
from .context import RunContext
from .provenance import (FamilyCompatibilityError, load_checkpoint, sha256_file)
from src.models.barr.ra_medfilm_barr import (RAMedFiLMBARR, TAU_C8_FINAL_FLOAT,
                                             canonical_utility)
from src.models.barr.regional_refiner import BARRRegionalRefinerV1
from src.models.film import GlobalMedFiLM
from src.research.stage6.end_to_end import GTFreeBARRInference, audit_ground_truth_free
from .stages.router_stage import BARRBenefitRouterV1
from .stages.safety_stage import BARRPostSafetyV1

STATES = ("FORCED_SKIP", "SKIP_GLOBAL", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT")


# --------------------------------------------------------------------------- #
def _build_g(model_cfg: Mapping[str, Any]) -> GlobalMedFiLM:
    return GlobalMedFiLM(task_count=model_cfg["task_count"],
                         in_channels=model_cfg["in_channels"],
                         out_channels=model_cfg["out_channels"],
                         channels=tuple(model_cfg["channels"]),
                         task_embedding_dim=model_cfg["task_embedding_dim"],
                         film_hidden_dim=model_cfg["film_hidden_dim"])


@dataclass
class FamilyBundle:
    """The four frozen modules of one seed family, plus their provenance."""

    seed: int
    g: nn.Module
    r: nn.Module
    b: nn.Module
    s: nn.Module
    router_state: Mapping[str, Any]
    safety_state: Mapping[str, Any]
    shas: Dict[str, str]

    @classmethod
    def load(cls, ctx: RunContext, *, device: str = "cpu") -> "FamilyBundle":
        g_path = ctx.g_dir / "best.pt"
        r_path = ctx.r_dir / "final" / "final.pt"
        b_path = ctx.b_dir / "final" / "final.pt"
        s_path = ctx.s_dir / "final" / "final.pt"
        for p in (g_path, r_path, b_path, s_path):
            if not p.exists():
                raise FileNotFoundError(f"{ctx.tag}: missing component checkpoint {p}")

        g_sha = sha256_file(g_path)
        r_sha = sha256_file(r_path)

        g_ck = load_checkpoint(g_path, map_location="cpu", component="G", seed=ctx.seed)
        r_ck = load_checkpoint(r_path, map_location="cpu", component="R", seed=ctx.seed,
                               upstream={"G": g_sha})
        b_ck = load_checkpoint(b_path, map_location="cpu", component="B", seed=ctx.seed,
                               upstream={"G": g_sha, "R": r_sha})
        s_ck = load_checkpoint(s_path, map_location="cpu", component="S", seed=ctx.seed,
                               upstream={"G": g_sha, "R": r_sha})

        g = _build_g(g_ck["recipe"]["g"]["model"])
        g.load_state_dict(g_ck["model_state"])
        r = BARRRegionalRefinerV1()
        r.load_state_dict(r_ck["model_state"])
        b = BARRBenefitRouterV1()
        b.load_state_dict(b_ck["model_state"])
        s = BARRPostSafetyV1()
        s.load_state_dict(s_ck["model_state"])

        return cls(seed=ctx.seed, g=g, r=r, b=b, s=s,
                   router_state={"normalizer_mu": b_ck["normalizer_mu"],
                                 "normalizer_sigma": b_ck["normalizer_sigma"],
                                 "normalizer_constant_mask": b_ck["normalizer_constant_mask"]},
                   safety_state={"normalizer_mu": s_ck["normalizer_mu"],
                                 "normalizer_sigma": s_ck["normalizer_sigma"],
                                 "normalizer_constant_mask": s_ck["normalizer_constant_mask"]},
                   shas={"G": g_sha, "R": r_sha,
                         "B": sha256_file(b_path), "S": sha256_file(s_path)})

    # ------------------------------------------------------------------ #
    def build_gtfree(self, device: str = "cpu", trace: bool = False) -> GTFreeBARRInference:
        return GTFreeBARRInference(global_model=self.g, refiner=self.r, router=self.b,
                                   safety=self.s, router_state=self.router_state,
                                   safety_state=self.safety_state, tau_c8=TAU_C8_FINAL_FLOAT,
                                   accept_threshold=R.SOMEGA_ACCEPT_THRESHOLD,
                                   roi_threshold=R.ROI_PROPOSAL_THRESHOLD,
                                   roi_margin=R.ROI_FRACTIONAL_MARGIN, device=device,
                                   trace=trace)

    def infer(self, image: torch.Tensor, task_id: int, *, device: str = "cpu",
              trace: bool = False) -> dict:
        engine = self.build_gtfree(device=device, trace=trace)
        return engine.infer(image, task_id)


# --------------------------------------------------------------------------- #
# controlled branch harness
# --------------------------------------------------------------------------- #
class _ConstTaps(nn.Module):
    """Deterministic stand-in for a feature tap: a constant map of fixed shape."""

    def __init__(self, channels: int, side: int, value: float) -> None:
        super().__init__()
        self.channels, self.side, self.value = int(channels), int(side), float(value)
        self.dummy = nn.Parameter(torch.zeros(1), requires_grad=False)

    def forward(self, x: Optional[torch.Tensor] = None) -> torch.Tensor:
        return torch.full((1, self.channels, self.side, self.side), self.value)


class _StubGlobal(nn.Module):
    """Global model whose probability map is a controlled constant."""

    def __init__(self, logit: float) -> None:
        super().__init__()
        self.logit = float(logit)
        self.bridge = _ConstTaps(256, 32, 0.0)
        self.decoder2 = _ConstTaps(48, 256, 0.0)
        self.decoder1 = _ConstTaps(24, 512, 0.0)

    def forward(self, images, task_ids=None):
        b, _, h, w = images.shape
        return torch.full((b, 1, h, w), self.logit)


class _StubRefiner(nn.Module):
    def __init__(self, logit: float = 4.0) -> None:
        super().__init__()
        self.logit = float(logit)

    def forward(self, x):
        b, _, h, w = x.shape
        return torch.full((b, 1, h, w), self.logit)


class _StubRouter(nn.Module):
    def __init__(self, score: float) -> None:
        super().__init__()
        self.score = float(score)

    def forward(self, x_numeric, task_ids=None):
        return torch.full((x_numeric.shape[0],), self.score)


class _StubSafety(nn.Module):
    def __init__(self, logit: float) -> None:
        super().__init__()
        self.logit = float(logit)

    def forward(self, x):
        return torch.full((x.shape[0],), self.logit)


def _window_from_probability(p: np.ndarray) -> Optional[tuple]:
    return RAMedFiLMBARR._roi_window_from_probability(p, R.ROI_PROPOSAL_THRESHOLD,
                                                      R.ROI_EXPANSION_FACTOR)


def verify_all_branches(*, image_size: int = 64) -> dict:
    """Exercise the canonical state machine with controlled inputs.

    Four cases are constructed so that each state is reached deterministically:

    ====================  ==================  ==============  ====================
    case                  p_global            router utility  expected state
    ====================  ==================  ==============  ====================
    forced_skip           all below 0.30      n/a             FORCED_SKIP
    skip_global           above 0.30          below tau       SKIP_GLOBAL
    execute_accept        above 0.30          above tau       EXECUTE_THEN_ACCEPT
    execute_reject        above 0.30          above tau       EXECUTE_THEN_REJECT
    ====================  ==================  ==============  ====================

    The refiner and safety outputs are the only knobs that separate accept from
    reject, so the accept threshold is genuinely exercised rather than assumed.
    """
    tau = TAU_C8_FINAL_FLOAT
    img = torch.rand(1, 3, image_size, image_size)
    # a router score comfortably above / below the frozen utility threshold
    above = tau + 1.0 + float(R.C_ACTION) * 0.25
    below = tau - 1.0
    cases = {
        "forced_skip": dict(logit=-8.0, score=above, safety=8.0, expected="FORCED_SKIP"),
        "skip_global": dict(logit=2.0, score=below, safety=8.0, expected="SKIP_GLOBAL"),
        "execute_accept": dict(logit=2.0, score=above, safety=8.0,
                               expected="EXECUTE_THEN_ACCEPT"),
        "execute_reject": dict(logit=2.0, score=above, safety=-8.0,
                               expected="EXECUTE_THEN_REJECT"),
    }
    out: Dict[str, dict] = {}
    for name, c in cases.items():
        wrapper = RAMedFiLMBARR(global_model=_StubGlobal(c["logit"]),
                                regional_refiner=_StubRefiner(),
                                benefit_router=_StubRouter(c["score"]),
                                post_safety=_StubSafety(c["safety"]),
                                router_normalization=None,
                                post_safety_normalization=None)
        p_global = torch.sigmoid(torch.tensor(c["logit"])).item()
        window = _window_from_probability(np.full((image_size, image_size), p_global,
                                                  dtype=np.float32))
        result = wrapper.forward_inference(
            img, 0,
            router_features_202=np.zeros(R.B_NUMERIC_DIM, dtype=np.float32),
            roi_window=window,
            action_available=window is not None,
            oof_refined_crop_prob=np.full((256, 256), 0.9, dtype=np.float32),
            safety_post_features_16=np.zeros(R.S_NUMERIC_DIM, dtype=np.float32),
        )
        if result["state"] != c["expected"]:
            raise AssertionError(f"branch {name}: got {result['state']}, "
                                 f"expected {c['expected']}")
        out[name] = {"state": result["state"],
                     "global_forward_count": result["global_forward_count"],
                     "refiner_forward_count": result["refiner_forward_count"],
                     "s_omega_forward_count": result["s_omega_forward_count"],
                     "final_probability_mean": float(np.asarray(result["final_probability"]).mean()),
                     "delta_hat_final": result["delta_hat_final"]}

    # compute accounting: the refiner must not run on skip branches
    if out["forced_skip"]["refiner_forward_count"] != 0:
        raise AssertionError("FORCED_SKIP executed the refiner")
    if out["skip_global"]["refiner_forward_count"] != 0:
        raise AssertionError("SKIP_GLOBAL executed the refiner")
    for k in ("execute_accept", "execute_reject"):
        if out[k]["refiner_forward_count"] != 1:
            raise AssertionError(f"{k} did not execute the refiner exactly once")
        if out[k]["s_omega_forward_count"] != 1:
            raise AssertionError(f"{k} did not execute S_omega exactly once")

    # the accept branch must return the refined map, the reject branch the global map
    if abs(out["execute_accept"]["final_probability_mean"] - 0.9) > 1e-6:
        raise AssertionError("EXECUTE_THEN_ACCEPT did not return the refined map")
    if abs(out["execute_reject"]["final_probability_mean"] - p_global) > 1e-6:
        raise AssertionError("EXECUTE_THEN_REJECT did not fall back to the global map")

    return {"states": out, "all_four_states_reached": True,
            "verdict": "ALL_INFERENCE_BRANCHES_VERIFIED"}


def verify_gtfree_adapter(bundle: FamilyBundle, *, device: str = "cuda",
                          image_size: int = 512) -> dict:
    """Run the real adapter end-to-end on a synthetic image (no dataset access)."""
    engine = bundle.build_gtfree(device=device, trace=True)
    img = torch.rand(1, 3, image_size, image_size)
    res = engine.infer(img, 0)
    if res["state"] not in STATES:
        raise AssertionError(f"unexpected state {res['state']}")
    prob = np.asarray(res["final_probability"])
    if prob.shape != (image_size, image_size):
        raise AssertionError(f"final probability shape {prob.shape}")
    if not np.isfinite(prob).all():
        raise AssertionError("final probability is not finite")
    return {"state": res["state"], "shape": list(prob.shape),
            "router_score": res["router_score"],
            "safety_probability": res["safety_probability"],
            "counters": dict(engine.counters),
            "unique_parameters": engine.unique_parameters(),
            "verdict": "GT_FREE_ADAPTER_EXECUTED"}


def export_prediction(bundle: FamilyBundle, image: torch.Tensor, task_id: int, *,
                      device: str = "cpu") -> dict:
    """Deterministic, hash-stable prediction record (no timestamps, no paths)."""
    import hashlib

    res = bundle.infer(image, task_id, device=device)
    prob = np.asarray(res["final_probability"], dtype=np.float32)
    binary = (prob >= R.SEGMENTATION_OUTPUT_THRESHOLD).astype(np.uint8)
    return {"seed": bundle.seed, "task_id": int(task_id), "state": res["state"],
            "router_score": (None if res["router_score"] is None
                             else float(res["router_score"])),
            "safety_probability": (None if res["safety_probability"] is None
                                   else float(res["safety_probability"])),
            "final_probability": prob, "final_binary": binary,
            "probability_sha256": hashlib.sha256(
                np.ascontiguousarray(prob).tobytes()).hexdigest(),
            "binary_sha256": hashlib.sha256(
                np.ascontiguousarray(binary).tobytes()).hexdigest(),
            "component_sha256": dict(bundle.shas)}


def audit_gt_free() -> dict:
    """Re-check the GT-free property on the live inference signatures."""
    base = audit_ground_truth_free()
    extra = {}
    findings = list(base["gt_like_parameters"])
    for name, fn in (("FamilyBundle.infer", FamilyBundle.infer),
                     ("export_prediction", export_prediction)):
        params = [p for p in __import__("inspect").signature(fn).parameters if p != "self"]
        extra[name] = params
        findings += [f"{name}:{p}" for p in params
                     if any(f in p.lower() for f in
                            ("gt", "mask", "label", "target", "dice", "patient", "oracle"))]
    return {"audited_signatures": {**base["audited_signatures"], **extra},
            "gt_like_parameters": findings, "gt_free": not findings,
            "infer_inputs": base["infer_inputs"]}
