"""Ground-truth-free end-to-end inference for the FULL RA-MedFiLM-BARR system.

Chain: image -> G (+tap hooks) -> ROI -> 202-D router features -> B_phi
-> R_psi (only when selected) -> fusion -> S_omega -> final mask.

``infer`` takes only an image and a task id; no mask, oracle Dice, label or
patient identifier is reachable.  The composition mirrors the frozen Phase-29
canonical driver, but computes every intermediate from the image instead of
reading a precomputed cache.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[3]
for _p in (ROOT, ROOT / "scripts" / "analysis"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from src.data.barr_roi import roi_geometry  # noqa: E402
from src.features.barr_pre_refinement_features import build_feature_vector  # noqa: E402
from src.models.barr.ra_medfilm_barr import TAU_C8_FINAL_FLOAT, canonical_utility  # noqa: E402

ROUTER_SCALAR_IDX = (192, 193, 194, 195, 196, 197, 200, 201)
TAPS = ("bridge", "decoder2", "decoder1")
REFINER_INPUT = 256
CANVAS = 512
FORBIDDEN_NAMES = ("gt", "mask", "label", "target", "dice", "patient", "oracle", "truth")
STATES = ("FORCED_SKIP", "SKIP_GLOBAL", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT")


class InferenceValidityError(RuntimeError):
    pass


def _resize_planes(arr: np.ndarray, out: int) -> np.ndarray:
    from PIL import Image

    planes = [
        np.asarray(Image.fromarray(np.ascontiguousarray(p, dtype=np.float32), mode="F")
                   .resize((out, out), Image.Resampling.BILINEAR), dtype=np.float32)
        for p in arr
    ]
    return np.stack(planes, axis=0)


def crop_window(arr: np.ndarray, geom: Mapping[str, Any], out: int) -> np.ndarray:
    """Crop the frozen ROI window (zero padded) and resize to ``out``."""
    arr = np.asarray(arr)
    if arr.ndim == 2:
        arr = arr[None]
    window = arr[..., int(geom["clip_y1"]):int(geom["clip_y2"]), int(geom["clip_x1"]):int(geom["clip_x2"])]
    pads = [(0, 0), (int(geom["pad_top"]), int(geom["pad_bottom"])),
            (int(geom["pad_left"]), int(geom["pad_right"]))]
    return _resize_planes(np.pad(window, pads, mode="constant"), out)


def fuse_regional(p_global: np.ndarray, refined_crop: np.ndarray, geom: Mapping[str, Any]) -> np.ndarray:
    """Regional replacement fusion (no blending), as in the frozen Phase-29 driver."""
    from PIL import Image

    side = int(geom["crop_side_pixels"])
    y1, y2, x1, x2 = (int(geom[k]) for k in ("clip_y1", "clip_y2", "clip_x1", "clip_x2"))
    square = np.asarray(
        Image.fromarray(np.ascontiguousarray(refined_crop, dtype=np.float32), mode="F")
        .resize((side, side), Image.Resampling.BILINEAR), dtype=np.float32)
    out = np.asarray(p_global, dtype=np.float32).copy()
    top, left = int(geom["pad_top"]), int(geom["pad_left"])
    out[y1:y2, x1:x2] = square[top:top + (y2 - y1), left:left + (x2 - x1)]
    return out


class _TapRecorder:
    def __init__(self, model: nn.Module):
        self.store: dict[str, torch.Tensor] = {}
        self._handles = [getattr(model, t).register_forward_hook(self._make(t)) for t in TAPS]

    def _make(self, tap: str):
        def hook(_m, _i, out):
            self.store[tap] = out
        return hook

    def close(self) -> None:
        for h in self._handles:
            h.remove()


def _normaliser(state: Mapping[str, Any], width: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mu = np.asarray(state["normalizer_mu"], dtype=np.float64).reshape(1, -1)
    sigma = np.asarray(state["normalizer_sigma"], dtype=np.float64).reshape(1, -1)
    const = np.asarray(state["normalizer_constant_mask"]).reshape(-1).astype(bool)
    if mu.shape[1] != width:
        raise InferenceValidityError(f"normaliser width {mu.shape[1]} != {width}")
    return mu, np.where(sigma < 1e-12, 1.0, sigma), const


class GTFreeBARRInference:
    """Executable FULL system whose inference needs only (image, task_id)."""

    def __init__(self, *, global_model: nn.Module, refiner: nn.Module, router: nn.Module,
                 safety: nn.Module, router_state: Mapping[str, Any], safety_state: Mapping[str, Any],
                 tau_c8: float = TAU_C8_FINAL_FLOAT, accept_threshold: float = 0.5,
                 roi_threshold: float = 0.30, roi_margin: float = 0.25, device: str = "cpu",
                 feature_builder=build_feature_vector, uses_tap_forward: bool = False,
                 amp_global: bool | None = None, trace: bool = False):
        # ``uses_tap_forward`` selects the model's own ``forward_with_features`` (Lite G)
        # instead of forward hooks on the FULL-family modules.
        self.device = torch.device(device)
        self.feature_builder, self.uses_tap_forward = feature_builder, uses_tap_forward
        # Canonical caches were built with an autocast G forward; mirror it on CUDA by default.
        self.amp_global = (self.device.type == "cuda") if amp_global is None else bool(amp_global)
        self.trace, self.last_trace = trace, {}
        self.g, self.r, self.b, self.s = (m.eval().requires_grad_(False).to(self.device)
                                          for m in (global_model, refiner, router, safety))
        self.r_mu, self.r_sig, self.r_const = _normaliser(router_state, len(ROUTER_SCALAR_IDX))
        self.s_mu, self.s_sig, self.s_const = _normaliser(safety_state, 16)
        self.tau_c8, self.accept_threshold = float(tau_c8), float(accept_threshold)
        self.roi_threshold, self.roi_margin = roi_threshold, roi_margin
        self.counters = {"global": 0, "router": 0, "refiner": 0, "safety": 0}

    def unique_parameters(self) -> int:
        seen: set[int] = set()
        total = 0
        for module in (self.g, self.r, self.b, self.s):
            for p in module.parameters():
                if id(p) not in seen:
                    seen.add(id(p))
                    total += p.numel()
        return total

    def _router_vector(self, cmaps, p512, geom) -> np.ndarray:
        vec = self.feature_builder(cmaps, p512, geom).astype(np.float32)
        idx = list(ROUTER_SCALAR_IDX)
        norm = (vec[idx].astype(np.float64)[None] - self.r_mu) / self.r_sig
        norm[:, self.r_const] = 0.0
        vec[idx] = norm[0].astype(np.float32)
        return vec

    def _safety_vector(self, p_crop: np.ndarray, r_crop: np.ndarray, geom, task_id: int) -> np.ndarray:
        from phase25f_post_safety_features import compute_numeric_features

        x0, x1 = int(geom["clip_x1"]), int(geom["clip_x2"])
        y0, y1 = int(geom["clip_y1"]), int(geom["clip_y2"])
        w_in, h_in = max(0, min(CANVAS, x1) - max(0, x0)), max(0, min(CANVAS, y1) - max(0, y0))
        feats = np.asarray(compute_numeric_features(p_crop[0], r_crop, (w_in * h_in) / float(CANVAS ** 2),
                                                    float(geom["crop_side_pixels"])),
                           dtype=np.float64).reshape(1, -1)
        if feats.shape != (1, 16):
            raise InferenceValidityError(f"safety features {feats.shape} != (1, 16)")
        norm = np.where(self.s_const, 0.0, (feats - self.s_mu) / self.s_sig)[0].astype(np.float32)
        onehot = np.zeros(4, dtype=np.float32)
        onehot[int(task_id)] = 1.0
        return np.concatenate([norm, onehot])

    @torch.inference_mode()
    def infer(self, image: torch.Tensor, task_id: int) -> dict[str, Any]:
        """Return the final segmentation for a ``[1,3,512,512]`` image in [0,1]."""
        if image.ndim != 4 or image.shape[0] != 1 or image.shape[1] != 3:
            raise InferenceValidityError(f"image must be [1,3,H,W], got {tuple(image.shape)}")
        if tuple(image.shape[-2:]) != (CANVAS, CANVAS):
            raise InferenceValidityError(f"image must be {CANVAS}x{CANVAS}, got {tuple(image.shape[-2:])}")
        if isinstance(task_id, bool) or int(task_id) != task_id or int(task_id) not in range(4):
            raise InferenceValidityError(f"task_id {task_id!r} not an integer in 0..3")
        if not torch.isfinite(image).all():
            raise InferenceValidityError("image contains NaN or Inf")
        if float(image.min()) < 0.0 or float(image.max()) > 1.0:
            raise InferenceValidityError("image must be scaled to [0, 1]")
        image = image.to(self.device).float()
        task = torch.tensor([int(task_id)], device=self.device)
        trace: dict[str, Any] = {"g_input": image[0].cpu().numpy()} if self.trace else {}
        with torch.amp.autocast(device_type=self.device.type, enabled=self.amp_global):
            if self.uses_tap_forward:
                logits, taps = self.g.forward_with_features(image, task)
                cmaps = {t: taps[t].float().cpu().numpy()[0] for t in TAPS}
            else:
                rec = _TapRecorder(self.g)
                try:
                    logits = self.g(image, task_ids=task)
                    cmaps = {t: rec.store[t].float().cpu().numpy()[0] for t in TAPS}
                finally:
                    rec.close()
        self.counters["global"] += 1
        p512 = torch.sigmoid(logits.float())[0, 0].cpu().numpy().astype(np.float32)
        if not np.isfinite(p512).all():
            raise InferenceValidityError("global probability map is not finite")
        result = {"task_id": int(task_id), "global_probability": p512, "router_score": None,
                  "safety_probability": None, "roi": None}
        if self.trace:
            trace.update({"global_logits": logits.float()[0, 0].cpu().numpy(), "global_probability": p512,
                          "taps": cmaps})
            self.last_trace = trace
        geom = roi_geometry(p512, self.roi_threshold, self.roi_margin)
        if geom is None:
            return {**result, "state": "FORCED_SKIP", "final_probability": p512}
        result["roi"] = geom
        trace["roi"] = dict(geom)

        raw = self.feature_builder(cmaps, p512, geom).astype(np.float32)
        vec = self._router_vector(cmaps, p512, geom)
        score = float(self.b(torch.from_numpy(vec)[None].to(self.device),
                             torch.tensor([int(task_id)], device=self.device)).reshape(-1)[0])
        self.counters["router"] += 1
        result["router_score"] = score
        trace.update({"router_vector_raw": raw, "router_vector_normalized": vec, "router_score": score,
                      "router_utility": canonical_utility(score)})
        if canonical_utility(score) < self.tau_c8:
            return {**result, "state": "SKIP_GLOBAL", "final_probability": p512}

        img_np = image[0].cpu().numpy()
        rin = np.concatenate([crop_window(img_np, geom, REFINER_INPUT),
                              crop_window(p512, geom, REFINER_INPUT)], axis=0)
        refined = torch.sigmoid(self.r(torch.from_numpy(np.ascontiguousarray(rin))[None].to(self.device)).float())
        refined = refined[0, 0].cpu().numpy().astype(np.float32)
        self.counters["refiner"] += 1
        candidate = fuse_regional(p512, refined, geom)
        feat = self._safety_vector(crop_window(p512, geom, REFINER_INPUT), refined, geom, task_id)
        logit = float(self.s(torch.from_numpy(feat)[None].to(self.device)).reshape(-1)[0])
        self.counters["safety"] += 1
        prob = float(torch.sigmoid(torch.tensor(logit)))
        result["safety_probability"] = prob
        trace.update({"refiner_input": rin, "refined_crop": refined, "candidate_probability": candidate,
                      "safety_vector": feat, "safety_logit": logit, "safety_probability": prob})
        if prob >= self.accept_threshold:
            return {**result, "state": "EXECUTE_THEN_ACCEPT", "final_probability": candidate}
        return {**result, "state": "EXECUTE_THEN_REJECT", "final_probability": p512}

    @classmethod
    def from_canonical_seed(cls, seed: int = 42, device: str = "cpu") -> "GTFreeBARRInference":
        """Load the verified canonical component family; never mixes families."""
        import phase29_phase_d_canonical_seed_inference as canon
        import phase29_phase_d_common as D
        from src.models.barr.regional_refiner import BARRRegionalRefinerV1
        from src.models.film.global_medfilm import GlobalMedFiLM

        if seed != 42:
            raise InferenceValidityError("only the seed-42 canonical G family is verified")
        info = D.SEED_INFO[seed]
        paths = {k: ROOT / info[k] for k in ("rpsi_final", "bphi_final", "somega_final")}
        g_path = ROOT / "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"
        cfg_path = ROOT / "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json"
        for p in (*paths.values(), g_path, cfg_path):
            if not p.exists():
                raise InferenceValidityError(f"missing component artifact: {p}")
        m = json.loads(cfg_path.read_text(encoding="utf-8"))["model"]
        g = GlobalMedFiLM(task_count=m["task_count"], in_channels=m["in_channels"],
                          out_channels=m["out_channels"], channels=tuple(m["channels"]),
                          task_embedding_dim=m["task_embedding_dim"], film_hidden_dim=m["film_hidden_dim"])
        g.load_state_dict(torch.load(g_path, map_location="cpu", weights_only=False)["model_state"])
        r = BARRRegionalRefinerV1()
        r.load_state_dict(torch.load(paths["rpsi_final"], map_location="cpu", weights_only=False)["model_state"])
        b_state = torch.load(paths["bphi_final"], map_location="cpu", weights_only=False)
        s_state = torch.load(paths["somega_final"], map_location="cpu", weights_only=False)
        for name, st in (("B_phi", b_state), ("S_omega", s_state)):
            if int(st.get("seed", -1)) != seed:
                raise InferenceValidityError(f"{name} checkpoint seed {st.get('seed')} != {seed}")
        b = canon.load_router_class()()
        b.load_state_dict(b_state["model_state"])
        s = canon.load_somega_class()()
        s.load_state_dict(s_state["model_state"])
        return cls(global_model=g, refiner=r, router=b, safety=s, router_state=b_state,
                   safety_state=s_state, tau_c8=D.tau_float(info["tau_c8_exact"]), device=device)


def audit_ground_truth_free() -> dict[str, Any]:
    """Static audit: no pipeline function accepts a ground-truth-like argument."""
    from phase25f_post_safety_features import compute_numeric_features
    from src.features.barr_pre_refinement_features import scalar_block

    audited = {
        "GTFreeBARRInference.infer": GTFreeBARRInference.infer,
        "roi_geometry": roi_geometry,
        "build_feature_vector": build_feature_vector,
        "scalar_block": scalar_block,
        "compute_numeric_features": compute_numeric_features,
        "crop_window": crop_window,
        "fuse_regional": fuse_regional,
    }
    findings, params = [], {}
    for name, fn in audited.items():
        names = [p for p in inspect.signature(fn).parameters if p != "self"]
        params[name] = names
        findings += [f"{name}:{p}" for p in names if any(f in p.lower() for f in FORBIDDEN_NAMES)]
    return {"audited_signatures": params, "gt_like_parameters": findings,
            "gt_free": not findings, "infer_inputs": params["GTFreeBARRInference.infer"]}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
