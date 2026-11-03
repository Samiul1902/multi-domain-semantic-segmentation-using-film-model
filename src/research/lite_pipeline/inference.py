"""Genuine GT-free end-to-end inference for one Lite seed family.

The inference path is the verified Stage-6 adapter
(:class:`src.research.stage6.end_to_end.GTFreeBARRInference`), which already
supports the Lite backbone through ``uses_tap_forward`` (call the model's own
``forward_with_features`` instead of installing forward hooks) and an injectable
``feature_builder``.  Nothing about the state machine is re-implemented::

    image + task_id
      -> G_Lite                              (exactly once)
      -> ROI proposal from p_global           (0.30, expansion 1.50)
      -> Lite 202-D pre-refinement features   (bridge/decoder2/decoder1 + scalars)
      -> B_phi                                (canonical router, utility vs tau_C8)
      -> R_Lite                               (only when selected)
      -> deterministic regional fusion        (replace inside ROI, no blending)
      -> S_omega                              (canonical safety, accept iff sigmoid >= 0.50)
      -> final probability map -> binary mask (0.50)

Four deterministic states are reachable: ``FORCED_SKIP``, ``SKIP_GLOBAL``,
``EXECUTE_THEN_ACCEPT`` and ``EXECUTE_THEN_REJECT``.

Normalisers
-----------
The router and safety normalisers are read from **this family's** checkpoints.
They were fitted FIT-only on Lite data inside the B and S producers, so no FULL
statistic is ever applied to a Lite feature vector -- which matters because the
Lite tap widths change the feature distribution.

Nothing here accepts a mask, a Dice value, a gain label or a patient identifier.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

import numpy as np
import torch
from torch import nn

from src.models.barr.phase25_models import (BARRBenefitRouterV1, BARRPostSafetyV1)
from src.models.barr.ra_medfilm_barr import TAU_C8_FINAL_FLOAT
from src.models.lite.ra_medfilm_barr_lite import (CANDIDATE_SPECS,
                                                  LiteGlobalMedFiLM,
                                                  LiteRegionalRefiner)
from src.research.full_pipeline import recipe as R
from src.research.full_pipeline.context import RunContext
from src.research.full_pipeline.provenance import (FamilyCompatibilityError,
                                                   load_checkpoint, sha256_file)
from src.research.stage6.end_to_end import GTFreeBARRInference

from . import recipe as L
from .features import lite_feature_builder

STATES = ("FORCED_SKIP", "SKIP_GLOBAL", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT")

__all__ = ["LiteBundle", "STATES", "export_prediction", "verify_all_branches",
           "audit_lite_gt_free"]


def _spec_for(variant_id: str):
    for spec in CANDIDATE_SPECS.values():
        if spec.variant_id == variant_id:
            return spec
    raise FamilyCompatibilityError(f"unknown Lite architecture id {variant_id!r}")


@dataclass
class LiteBundle:
    """The four modules of one Lite seed family, plus their provenance."""

    seed: int
    variant_id: str
    g: nn.Module
    r: nn.Module
    b: nn.Module
    s: nn.Module
    router_state: Mapping[str, Any]
    safety_state: Mapping[str, Any]
    shas: Dict[str, str]

    @classmethod
    def load(cls, ctx: RunContext, *, device: str = "cpu") -> "LiteBundle":
        g_path = ctx.g_dir / "best.pt"
        r_path = ctx.r_dir / "final" / "final.pt"
        b_path = ctx.b_dir / "final" / "final.pt"
        s_path = ctx.s_dir / "final" / "final.pt"
        for p in (g_path, r_path, b_path, s_path):
            if not p.exists():
                raise FileNotFoundError(f"{ctx.tag}: missing component checkpoint {p}")

        g_sha = sha256_file(g_path)
        r_sha = sha256_file(r_path)

        g_ck = load_checkpoint(g_path, map_location="cpu", component="G", seed=ctx.seed,
                               family="LITE")
        r_ck = load_checkpoint(r_path, map_location="cpu", component="R", seed=ctx.seed,
                               family="LITE", upstream={"G": g_sha})
        b_ck = load_checkpoint(b_path, map_location="cpu", component="B", seed=ctx.seed,
                               family="LITE", upstream={"G": g_sha, "R": r_sha})
        s_ck = load_checkpoint(s_path, map_location="cpu", component="S", seed=ctx.seed,
                               family="LITE", upstream={"G": g_sha, "R": r_sha})

        # the architecture is identified by the digest, not by a filename
        variant_id = g_ck.get("architecture_id")
        if not isinstance(variant_id, str) or not variant_id.endswith("::global"):
            raise FamilyCompatibilityError(
                f"Lite G checkpoint carries an unexpected architecture id {variant_id!r}")
        spec = _spec_for(variant_id[: -len("::global")])
        stamped = L.checkpoint_architecture_sha256(g_ck, block="g")
        if stamped != spec.sha256():
            raise FamilyCompatibilityError(
                f"Lite G checkpoint architecture digest {stamped} does not match any "
                "frozen spec")

        g = LiteGlobalMedFiLM(spec)
        g.load_state_dict(g_ck["model_state"])
        r = LiteRegionalRefiner(spec)
        r.load_state_dict(r_ck["model_state"])
        b = BARRBenefitRouterV1()
        b.load_state_dict(b_ck["model_state"])
        s = BARRPostSafetyV1()
        s.load_state_dict(s_ck["model_state"])

        for name, ck in (("B", b_ck), ("S", s_ck)):
            if "normalizer_mu" not in ck:
                raise FamilyCompatibilityError(
                    f"Lite {name} checkpoint carries no FIT-only normaliser statistics")

        return cls(seed=ctx.seed, variant_id=spec.variant_id, g=g, r=r, b=b, s=s,
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
        return GTFreeBARRInference(
            global_model=self.g, refiner=self.r, router=self.b, safety=self.s,
            router_state=self.router_state, safety_state=self.safety_state,
            tau_c8=TAU_C8_FINAL_FLOAT,
            accept_threshold=R.SOMEGA_ACCEPT_THRESHOLD,
            roi_threshold=R.ROI_PROPOSAL_THRESHOLD,
            roi_margin=R.ROI_FRACTIONAL_MARGIN,
            device=device,
            feature_builder=lite_feature_builder,
            uses_tap_forward=True,
            trace=trace,
        )

    def infer(self, image: torch.Tensor, task_id: int, *, device: str = "cpu",
              trace: bool = False) -> dict:
        return self.build_gtfree(device=device, trace=trace).infer(image, task_id)

    def unique_parameters(self) -> int:
        seen: set = set()
        total = 0
        for module in (self.g, self.r, self.b, self.s):
            for p in module.parameters():
                if id(p) not in seen:
                    seen.add(id(p))
                    total += p.numel()
        return total


# --------------------------------------------------------------------------- #
def verify_all_branches() -> dict:
    """Exercise the canonical state machine.

    The four-state harness in :mod:`src.research.full_pipeline.inference` feeds the
    router features and the ROI window explicitly, so it is model-agnostic: it
    tests the shared state machine, not a backbone.  Imported rather than
    duplicated, so a change to the state machine cannot make one family's branch
    proof disagree with the other's.
    """
    from src.research.full_pipeline.inference import verify_all_branches as _verify

    out = _verify()
    out["family"] = "LITE"
    return out


def export_prediction(bundle: LiteBundle, image: torch.Tensor, task_id: int, *,
                      device: str = "cpu") -> dict:
    """Deterministic, hash-stable prediction record (no timestamps, no paths)."""
    res = bundle.infer(image, task_id, device=device)
    prob = np.asarray(res["final_probability"], dtype=np.float32)
    binary = (prob >= R.SEGMENTATION_OUTPUT_THRESHOLD).astype(np.uint8)
    return {"seed": bundle.seed, "variant_id": bundle.variant_id,
            "task_id": int(task_id), "state": res["state"],
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


def audit_lite_gt_free() -> dict:
    """Re-check the GT-free property on the Lite inference surface."""
    import inspect

    from src.research.stage6.end_to_end import audit_ground_truth_free

    forbidden = ("gt", "mask", "label", "target", "dice", "patient", "oracle", "truth")
    base = audit_ground_truth_free()
    findings = list(base["gt_like_parameters"])
    extra: Dict[str, list] = {}
    for name, fn in (("LiteBundle.infer", LiteBundle.infer),
                     ("export_prediction", export_prediction),
                     ("LiteBundle.build_gtfree", LiteBundle.build_gtfree)):
        params = [p for p in inspect.signature(fn).parameters if p != "self"]
        extra[name] = params
        findings += [f"{name}:{p}" for p in params
                     if any(f in p.lower() for f in forbidden)]
    return {"audited_signatures": {**base["audited_signatures"], **extra},
            "gt_like_parameters": findings, "gt_free": not findings,
            "infer_inputs": base["infer_inputs"],
            "family": "LITE"}
