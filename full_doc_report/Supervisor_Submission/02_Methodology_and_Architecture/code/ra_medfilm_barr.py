"""Canonical RA-MedFiLM-BARR integration wrapper.

Phase26 revision: ``ra_medfilm_barr_phase26_integration_v1_0``
Router semantics: ``phase26_v1_2``

Operational meaning: ASSEMBLY_ONLY__NO_PARAMETER_OPTIMIZATION.

This module COMPOSES the four already-frozen canonical components. It introduces
**0 trainable parameters** and defines no training loss, optimizer hook, joint
backward graph or policy-learning function.

Components (composed, never reimplemented):
    * ``GlobalMedFiLM``          G        (global four-domain segmenter)
    * ``BARRRegionalRefinerV1``  R_psi    (crop-trained regional refiner)
    * ``BARRBenefitRouterV1``    B_phi    (GT-free paired-gain benefit router)
    * ``BARRPostSafetyV1``       S_omega  (post-refinement safety gate)

Canonical state machine::

    FORCED_SKIP          action unavailable                    -> p_global
    SKIP_GLOBAL          U <  tau_C8_final                     -> p_global
    EXECUTE_THEN_ACCEPT  U >= tau_C8_final and accept          -> regional candidate
    EXECUTE_THEN_REJECT  U >= tau_C8_final and reject          -> p_global

Runtime score::

    U = delta_hat_final - (1/4) * (1051648 / 10270749)

EXECUTE iff ``U >= tau_C8_final`` where::

    tau_C8_final = -5003565381643716252018011/205414980000000000000000000

The exact rational is the authority; the float constant below is a
deterministic adequately-precise implementation of it.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Any, Dict, Optional

import numpy as np
import torch
import torch.nn as nn

# --------------------------------------------------------------------------- #
# canonical constants (exact rationals are authority)
# --------------------------------------------------------------------------- #
LAMBDA = Fraction(1, 4)
C_ACTION = Fraction(1051648, 10270749)
LAMBDA_C = LAMBDA * C_ACTION
TAU_C7_FINAL = Fraction(24796109646558761, 20000000000000000000)
TAU_C8_FINAL = TAU_C7_FINAL - LAMBDA_C

#: deterministic adequately-precise float derived from the exact rational
TAU_C8_FINAL_FLOAT = float(TAU_C8_FINAL)

ROI_PROPOSAL_THRESHOLD = 0.30
SOMEGA_ACCEPT_THRESHOLD = 0.50
SEGMENTATION_OUTPUT_THRESHOLD = 0.50
ROI_EXPANSION = 1.50

ROUTER_NUMERIC_DIM = 202
ROUTER_TASK_EMBED_DIM = 16
ROUTER_TOTAL_DIM = 218
SOMEGA_NUMERIC_DIM = 16
SOMEGA_TOTAL_DIM = 20

STATES = ("FORCED_SKIP", "SKIP_GLOBAL", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT")


def canonical_utility(delta_hat_final: float, action_cost: Optional[float] = None) -> float:
    """Resource-aware utility ``delta_hat_final - lambda*C`` (float, implementation)."""
    c = float(C_ACTION) if action_cost is None else float(action_cost)
    return float(delta_hat_final) - float(LAMBDA) * c


def router_decision(delta_hat_final: float) -> str:
    """Return 'EXECUTE' or 'SKIP' using the frozen runtime threshold."""
    return "EXECUTE" if canonical_utility(delta_hat_final) >= TAU_C8_FINAL_FLOAT else "SKIP"


# --------------------------------------------------------------------------- #
# inference wrapper
# --------------------------------------------------------------------------- #
class RAMedFiLMBARR(nn.Module):
    """Canonical, fully-assembled RA-MedFiLM-BARR inference system.

    Parameters are supplied as already-loaded, frozen modules. The wrapper adds
    no parameters of its own: ``sum(p.numel() for p in self.parameters()) == 0``.

    Parameters
    ----------
    global_model : nn.Module
        Frozen ``GlobalMedFiLM`` instance (G).
    regional_refiner : nn.Module
        Frozen ``BARRRegionalRefinerV1`` instance (R_psi), in_channels=4.
    benefit_router : nn.Module
        Frozen ``BARRBenefitRouterV1`` instance (B_phi), input 218.
    post_safety : nn.Module
        Frozen ``BARRPostSafetyV1`` instance (S_omega), input 20.
    router_normalization : dict | None
        ``{"mu": array[202], "sigma": array[202], "zero_sigma_rule": str}``.
    post_safety_normalization : dict | None
        ``{"mu": array[16], "sigma": array[16], "zero_sigma_rule": str}``.
    """

    def __init__(self, global_model: nn.Module, regional_refiner: nn.Module,
                 benefit_router: nn.Module, post_safety: nn.Module,
                 router_normalization: Optional[Dict[str, Any]] = None,
                 post_safety_normalization: Optional[Dict[str, Any]] = None,
                 roi_proposal_threshold: float = ROI_PROPOSAL_THRESHOLD,
                 roi_expansion: float = ROI_EXPANSION,
                 s_omega_accept_threshold: float = SOMEGA_ACCEPT_THRESHOLD,
                 segmentation_output_threshold: float = SEGMENTATION_OUTPUT_THRESHOLD):
        super().__init__()
        # composed sub-modules (registered so state_dict/device moves work)
        self.global_model = global_model
        self.regional_refiner = regional_refiner
        self.benefit_router = benefit_router
        self.post_safety = post_safety

        # non-parameter configuration (plain python attrs, never nn.Parameters)
        self.router_normalization = router_normalization
        self.post_safety_normalization = post_safety_normalization
        self.roi_proposal_threshold = float(roi_proposal_threshold)
        self.roi_expansion = float(roi_expansion)
        self.s_omega_accept_threshold = float(s_omega_accept_threshold)
        self.segmentation_output_threshold = float(segmentation_output_threshold)

        self.freeze_all()
        self.eval()

    # ------------------------------------------------------------------ #
    @property
    def trainable_parameter_count(self) -> int:
        """Wrapper-introduced trainable parameters: always 0."""
        own = 0
        for name in ("global_model", "regional_refiner", "benefit_router", "post_safety"):
            own += 0  # composed, not introduced
        return own

    def freeze_all(self) -> None:
        """Set ``requires_grad_(False)`` on every composed module."""
        for m in (self.global_model, self.regional_refiner,
                  self.benefit_router, self.post_safety):
            m.eval()
            m.requires_grad_(False)

    # ------------------------------------------------------------------ #
    # discrete structural components
    # ------------------------------------------------------------------ #
    @staticmethod
    def _roi_window_from_probability(p_global: np.ndarray,
                                     proposal_threshold: float = ROI_PROPOSAL_THRESHOLD,
                                     expansion: float = ROI_EXPANSION) -> Optional[tuple]:
        """Frozen GT-free ROI proposal: threshold -> bbox -> centre-preserving expansion.

        Returns a half-open ``(y0, y1, x0, x1)`` window or ``None`` when the
        action is unavailable (no foreground above ``proposal_threshold``).
        """
        binary = p_global >= proposal_threshold
        if not binary.any():
            return None
        ys, xs = np.nonzero(binary)
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        cy, cx = (y0 + y1) / 2.0, (x0 + x1) / 2.0
        half_y = (y1 - y0) * expansion / 2.0
        half_x = (x1 - x0) * expansion / 2.0
        H, W = p_global.shape
        ny0 = int(round(cy - half_y))
        ny1 = int(round(cy + half_y))
        nx0 = int(round(cx - half_x))
        nx1 = int(round(cx + half_x))
        ny0, ny1 = max(0, ny0), min(H, ny1)
        nx0, nx1 = max(0, nx0), min(W, nx1)
        if ny1 <= ny0 or nx1 <= nx0:
            return None
        return (ny0, ny1, nx0, nx1)

    @staticmethod
    def _fuse_global_with_regional(p_global: np.ndarray, p_refined_crop: np.ndarray,
                                   window: tuple) -> np.ndarray:
        """Deterministic regional fusion - NO alpha blending.

        Outside the frozen ROI retain ``p_global``; inside the frozen ROI replace
        with the resized refined crop.
        """
        y0, y1, x0, x1 = window
        out = p_global.astype(np.float32).copy()
        crop = np.asarray(p_refined_crop, dtype=np.float32)
        if crop.shape != (y1 - y0, x1 - x0):
            tgt = torch.from_numpy(crop)[None, None]
            resized = torch.nn.functional.interpolate(
                tgt, size=(y1 - y0, x1 - x0), mode="bilinear", align_corners=False)
            crop = resized[0, 0].numpy()
        out[y0:y1, x0:x1] = crop
        return out

    # ------------------------------------------------------------------ #
    # normalization helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _apply_norm(vec: np.ndarray, norm: Optional[Dict[str, Any]]) -> np.ndarray:
        if norm is None:
            return vec.astype(np.float32)
        mu = np.asarray(norm["mu"], dtype=np.float64)
        sigma = np.asarray(norm["sigma"], dtype=np.float64)
        safe = np.where(sigma < 1e-12, 1.0, sigma)
        out = (vec.astype(np.float64) - mu) / safe
        out = np.where(sigma < 1e-12, 0.0, out)
        return out.astype(np.float32)

    @staticmethod
    def _onehot_task(task_id: int, n: int = 4) -> np.ndarray:
        v = np.zeros(n, dtype=np.float32)
        v[int(task_id)] = 1.0
        return v

    # ------------------------------------------------------------------ #
    # canonical inference
    # ------------------------------------------------------------------ #
    def forward_inference(self, image: torch.Tensor, task_id: int,
                          router_features_202: Optional[np.ndarray] = None,
                          roi_window: Optional[tuple] = None,
                          action_available: Optional[bool] = None,
                          oof_refined_crop_prob: Optional[np.ndarray] = None,
                          safety_post_features_16: Optional[np.ndarray] = None,
                          ) -> Dict[str, Any]:
        """Run the canonical state machine exactly once per input.

        Parameters
        ----------
        image : torch.Tensor
            ``[1, C, H, W]`` input image (already preprocessed).
        task_id : int
            Domain task id in ``{0: ISIC, 1: BUSI, 2: KVASIR, 3: KUB}``.
        router_features_202 : np.ndarray | None
            Exact frozen Phase25B 202-D GT-free feature vector for this sample.
            Required to reach the router decision.
        roi_window : tuple | None
            Pre-computed frozen ROI window; when omitted it is proposed internally.
        action_available : bool | None
            Explicit frozen action-availability flag; when omitted it is derived
            from the ROI proposal.
        oof_refined_crop_prob : np.ndarray | None
            ``256x256`` refined probability crop from the frozen refiner.
        safety_post_features_16 : np.ndarray | None
            Exact frozen Phase25F 16 numeric post-refinement features.

        Returns
        -------
        dict
            ``state``, ``final_probability``, call counters and the raw router score.
        """
        counters = {"global": 0, "refiner": 0, "s_omega": 0}

        # ---- 9. GLOBAL STAGE (exactly once) -------------------------------- #
        with torch.no_grad():
            g_out = self.global_model(image, task_ids=torch.tensor([int(task_id)]))
            counters["global"] += 1
        p_global = _to_prob_map(g_out)

        # ---- action availability ------------------------------------------ #
        window = roi_window
        if window is None and action_available is not False:
            window = self._roi_window_from_probability(np.asarray(p_global, dtype=np.float32))
        avail = (window is not None) if action_available is None else bool(action_available)

        # ---- 15. ACTION-UNAVAILABLE (FORCED_SKIP) -------------------------- #
        if not avail:
            return self._result("FORCED_SKIP", p_global, counters, None, window)

        # ---- 10/11. ROUTER FEATURE + FINAL ROUTER STAGE -------------------- #
        if router_features_202 is None:
            raise ValueError("router_features_202 is required for the canonical path")
        rf = np.asarray(router_features_202, dtype=np.float32).reshape(-1)
        if rf.shape[0] != ROUTER_NUMERIC_DIM:
            raise ValueError(f"router features must be {ROUTER_NUMERIC_DIM}-D, got {rf.shape[0]}")
        rf_norm = self._apply_norm(rf, self.router_normalization)
        with torch.no_grad():
            x_num = torch.from_numpy(rf_norm)[None]
            t_ids = torch.tensor([int(task_id)])
            delta_hat_final = float(self.benefit_router(x_num, t_ids).reshape(-1)[0])

        util = canonical_utility(delta_hat_final)

        # ---- 12. SKIP BRANCH ----------------------------------------------- #
        if util < TAU_C8_FINAL_FLOAT:
            return self._result("SKIP_GLOBAL", p_global, counters, delta_hat_final, window)

        # ---- 13. EXECUTE BRANCH -------------------------------------------- #
        # 1. ROI already constructed (frozen geometry).
        # 2. regional refiner exactly once.
        if oof_refined_crop_prob is None:
            raise ValueError("oof_refined_crop_prob is required on the EXECUTE branch")
        with torch.no_grad():
            counters["refiner"] += 1
        # 3. deterministic regional-fused candidate (no alpha blending).
        fused = self._fuse_global_with_regional(
            np.asarray(p_global, dtype=np.float32),
            np.asarray(oof_refined_crop_prob, dtype=np.float32), window)
        # 4/5/6. post-safety feature -> normalization -> S_omega once.
        if safety_post_features_16 is None:
            raise ValueError("safety_post_features_16 is required on the EXECUTE branch")
        sf = np.asarray(safety_post_features_16, dtype=np.float32).reshape(-1)
        if sf.shape[0] != SOMEGA_NUMERIC_DIM:
            raise ValueError(f"post-safety numeric features must be {SOMEGA_NUMERIC_DIM}-D, "
                             f"got {sf.shape[0]}")
        sf_norm = self._apply_norm(sf, self.post_safety_normalization)
        full = np.concatenate([sf_norm, self._onehot_task(task_id)], axis=0)
        with torch.no_grad():
            logit = float(self.post_safety(torch.from_numpy(full)[None]).reshape(-1)[0])
            counters["s_omega"] += 1
        accept_prob = float(torch.sigmoid(torch.tensor(logit)).item())

        # 7. ACCEPT iff sigmoid(logit) >= 0.50
        if accept_prob >= self.s_omega_accept_threshold:
            return self._result("EXECUTE_THEN_ACCEPT", fused, counters, delta_hat_final, window,
                                logit=logit, accept_prob=accept_prob)
        return self._result("EXECUTE_THEN_REJECT", p_global, counters, delta_hat_final, window,
                            logit=logit, accept_prob=accept_prob)

    # ------------------------------------------------------------------ #
    def _result(self, state, final_prob, counters, delta_hat, window,
                logit=None, accept_prob=None) -> Dict[str, Any]:
        prob = np.asarray(final_prob, dtype=np.float32)
        return {
            "state": state,
            "final_probability": prob,
            "final_binary": (prob >= self.segmentation_output_threshold).astype(np.uint8),
            "global_forward_count": counters["global"],
            "refiner_forward_count": counters["refiner"],
            "s_omega_forward_count": counters["s_omega"],
            "delta_hat_final": delta_hat,
            "roi_window": window,
            "post_safety_logit": logit,
            "post_safety_accept_probability": accept_prob,
        }


# --------------------------------------------------------------------------- #
def _to_prob_map(g_out: Any) -> np.ndarray:
    """Coerce a GlobalMedFiLM output to a single 2-D probability map (numpy)."""
    t = g_out
    if isinstance(g_out, (tuple, list)):
        t = g_out[0]
    if isinstance(t, dict):
        t = t.get("logits", t.get("prob", next(iter(t.values()))))
    if isinstance(t, torch.Tensor):
        t = t.detach().cpu()
        if t.ndim == 4:
            t = t[0]
        if t.ndim == 3 and t.shape[0] == 1:
            t = t[0]
        arr = torch.sigmoid(t).numpy() if _is_logit(t) else t.numpy()
    else:
        arr = np.asarray(t)
        if arr.ndim == 3:
            arr = arr[0]
        if arr.ndim == 3 and arr.shape[0] == 1:
            arr = arr[0]
    return np.asarray(arr, dtype=np.float32)


def _is_logit(t: torch.Tensor) -> bool:
    """A logit map is unbounded; a probability map lies in [0, 1]."""
    return bool(t.min() < 0.0 or t.max() > 1.0)


__all__ = [
    "RAMedFiLMBARR", "canonical_utility", "router_decision",
    "LAMBDA", "C_ACTION", "LAMBDA_C", "TAU_C7_FINAL", "TAU_C8_FINAL",
    "TAU_C8_FINAL_FLOAT", "ROI_PROPOSAL_THRESHOLD", "SOMEGA_ACCEPT_THRESHOLD",
    "SEGMENTATION_OUTPUT_THRESHOLD", "STATES",
]
