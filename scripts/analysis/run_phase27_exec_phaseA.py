"""Phase27 EXECUTION - PHASE A: VAL808 IMAGE-ONLY INFERENCE.

First time the VAL808 images are opened.  GT masks are NEVER read here.

For each VAL808 sample in the frozen canonical order (dataset asc, sample_id asc),
contiguous chunks of 8 inside a single domain:

    1. run the frozen GlobalMedFiLM G in the canonical AMP(fp16) batched path
       -> p_global (float32) -> the GLOBAL reference prediction
    2. propose the frozen ROI (0.30) -> action availability
    3. if action available: run the frozen BARRBenefitRouterV1 B_phi on the exact
       202-D GT-free feature vector, apply the frozen runtime threshold
       U = delta_hat_final - 0.25*C, EXECUTE iff U >= tau_C8_final
    4. if EXECUTE: run the frozen regional refiner R_psi per-sample (hidden-free
       ROI crop), fuse deterministically (no alpha blending), compute the 16-D
       post-refinement features, run S_omega once, accept iff sigmoid(logit) >= 0.50
    5. persist the FINAL (A8) probability/binary and the GLOBAL probability/binary

Binary decisions are taken in float32 BEFORE any float16 storage cast.

Writes:
    reports/figures/phase27_preservation/masks/<sid>_global.png
    reports/figures/phase27_preservation/masks/<sid>_final.png
    reports/tables/phase27_val808_predictions.csv
    reports/audits/phase27_val808_predictions_sha256.json
    data_cache/phase27_barr_preservation_v1_0/phase27_val808_global_prob_f16.npy
    data_cache/phase27_barr_preservation_v1_0/phase27_val808_final_prob_f16.npy

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/run_phase27_exec_phaseA.py
"""
from __future__ import annotations

import sys
import time
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase27_exec_common as E  # noqa: E402
import phase27_spec_common as S  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402
from PIL import Image, ImageOps  # noqa: E402

from src.data.barr_roi import (  # noqa: E402
    REGIONAL_CANVAS_RESOLUTION,
    REGIONAL_INPUT_RESOLUTION,
    roi_geometry,
    threshold_probability,
)
from src.features.barr_pre_refinement_features import build_feature_vector  # noqa: E402
from src.models.film.global_medfilm import GlobalMedFiLM  # noqa: E402
from src.models.barr.regional_refiner import BARRRegionalRefinerV1  # noqa: E402
from src.utils.device import get_device  # noqa: E402
from src.utils.test_lock import verify_test_lock  # noqa: E402

say = print

TAPS = ("bridge", "decoder2", "decoder1")
TAP_MODULES = {"bridge": "bridge", "decoder2": "decoder2", "decoder1": "decoder1"}


# --------------------------------------------------------------------------- #
class TapRecorder:
    """Inference-only forward hooks on the three G taps (read outputs)."""

    def __init__(self, model: torch.nn.Module):
        self.store = {}
        self.handles = []
        for tap in TAPS:
            module = getattr(model, TAP_MODULES[tap])
            self.handles.append(module.register_forward_hook(self._make(tap)))

    def _make(self, tap):
        def hook(_m, _i, out):
            self.store[tap] = out
        return hook

    def close(self):
        for h in self.handles:
            h.remove()
        self.handles.clear()


def image_only_transform(image, size: int = REGIONAL_CANVAS_RESOLUTION) -> torch.Tensor:
    """Image-side of SegmentationTransform(train=False, image_mode='RGB').

    Reproduces EXACTLY the canonical image path (aspect-preserving bilinear resize
    + centre pad + permute(2,0,1) / 255.0) WITHOUT ever opening the paired mask.
    The paired transform's mask argument is intentionally not required, so Phase A
    performs ZERO GT/mask-file reads.
    """
    image = image.convert("RGB")
    width, height = image.size
    scale = min(size / width, size / height)
    rw, rh = max(1, round(width * scale)), max(1, round(height * scale))
    image = image.resize((rw, rh), Image.Resampling.BILINEAR)
    left, top = (size - rw) // 2, (size - rh) // 2
    right, bottom = size - rw - left, size - rh - top
    image = ImageOps.expand(image, (left, top, right, bottom))
    arr = np.asarray(image, dtype=np.float32).copy()
    return torch.from_numpy(arr).permute(2, 0, 1) / 255.0


# --------------------------------------------------------------------------- #
def full_field_binary_from_prob(prob512: np.ndarray) -> np.ndarray:
    return threshold_probability(prob512, E.SEGMENTATION_OUTPUT_THRESHOLD)


# --------------------------------------------------------------------------- #
def load_components(device):
    cfg = E.jload(E.ROOT / "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json")
    g = GlobalMedFiLM(
        task_count=cfg["model"]["task_count"],
        in_channels=cfg["model"]["in_channels"],
        out_channels=cfg["model"]["out_channels"],
        channels=tuple(cfg["model"]["channels"]),
        task_embedding_dim=cfg["model"]["task_embedding_dim"],
        film_hidden_dim=cfg["model"]["film_hidden_dim"],
    )
    g.load_state_dict(torch.load(E.ROOT / E.COMPONENT_PATHS["global_medfilm"],
                                map_location="cpu", weights_only=False)["model_state"])

    r = BARRRegionalRefinerV1()
    r.load_state_dict(torch.load(E.ROOT / E.COMPONENT_PATHS["regional_refiner"],
                                 map_location="cpu", weights_only=False)["model_state"])

    # B_phi / S_omega classes are extracted WITHOUT executing their training
    # module bodies (import-time side effects).  See phase27_model_import_shim.
    import phase27_model_import_shim as shim
    BARRBenefitRouterV1 = shim.get_benefit_router()
    BARRPostSafetyV1 = shim.get_post_safety()

    b = BARRBenefitRouterV1()
    b.load_state_dict(torch.load(E.ROOT / E.COMPONENT_PATHS["benefit_router"],
                                 map_location="cpu", weights_only=False)["model_state"])
    s = BARRPostSafetyV1()
    s.load_state_dict(torch.load(E.ROOT / E.COMPONENT_PATHS["post_safety"],
                                 map_location="cpu", weights_only=False)["model_state"])

    for m in (g, r, b, s):
        m.eval()
        m.requires_grad_(False)
        m.to(device)

    counts = {
        "global_medfilm": sum(p.numel() for p in g.parameters()),
        "regional_refiner": sum(p.numel() for p in r.parameters()),
        "benefit_router": sum(p.numel() for p in b.parameters()),
        "post_safety": sum(p.numel() for p in s.parameters()),
    }
    assert counts == E.COMPONENT_PARAM_COUNTS, counts
    return g, r, b, s, counts


# --------------------------------------------------------------------------- #
def load_router_norm():
    rows = list(pd.read_csv(E.ROOT / E.NORMALIZATION_PATHS["router_normalization"])
                .itertuples(index=False))
    idx = [int(r.scalar_index) for r in rows]
    mu = np.array([float(r.mu) for r in rows], dtype=np.float64)
    sigma = np.array([float(r.sigma) for r in rows], dtype=np.float64)
    const = np.array([str(r.is_constant) == "True" for r in rows])
    return {"idx": idx, "mu": mu, "sigma": sigma, "const": const}


def norm_router(feats202: np.ndarray, rn) -> np.ndarray:
    out = feats202.astype(np.float32).copy()
    idx = np.asarray(rn["idx"])
    safe = np.where(rn["sigma"] < 1e-12, 1.0, rn["sigma"])
    z = (feats202[idx].astype(np.float64) - rn["mu"]) / safe
    z = np.where(rn["const"], 0.0, z)
    out[idx] = z.astype(np.float32)
    return out


def load_somega_norm():
    rows = list(pd.read_csv(E.ROOT / E.NORMALIZATION_PATHS["post_safety_normalization"])
                .itertuples(index=False))
    mu = np.array([float(r.mu) for r in rows], dtype=np.float64)
    sigma = np.array([float(r.sigma) for r in rows], dtype=np.float64)
    const = np.array([str(r.is_constant) == "True" for r in rows])
    return {"mu": mu, "sigma": sigma, "const": const}


def norm_somega(feat16: np.ndarray, sn) -> np.ndarray:
    safe = np.where(sn["sigma"] < 1e-12, 1.0, sn["sigma"])
    z = (feat16.astype(np.float64) - sn["mu"]) / safe
    z = np.where(sn["const"], 0.0, z)
    return z.astype(np.float32)


# --------------------------------------------------------------------------- #
def main() -> int:
    t0 = time.time()
    verify_test_lock(str(E.ROOT))
    say("TEST lock verified")

    assert abs(E.ROI_PROPOSAL_THRESHOLD - 0.30) < 1e-12
    assert abs(E.SOMEGA_ACCEPT_THRESHOLD - 0.50) < 1e-12
    assert abs(E.SEGMENTATION_OUTPUT_THRESHOLD - 0.50) < 1e-12

    # ---- predecessor + bundle immutability (re-verify inside execution) --- #
    for rel, sh in [
        (E.PREDECESSOR_TERMINAL_PATH, None),
        (E.BUNDLE_MANIFEST, E.BUNDLE_MANIFEST_SHA),
        (E.NOTEBOOK26_PATH, E.NOTEBOOK26_SHA),
        (E.FREEZE26_PATH, E.FREEZE26_SHA),
        (E.WRAPPER_PATH, E.WRAPPER_SHA),
        (E.VAL808_MANIFEST, E.VAL808_MANIFEST_SHA),
    ]:
        b = E.bind(rel, sh)
        assert b["match"], f"immutability failure: {rel} -> {b['sha256']}"
    for k, p in E.COMPONENT_PATHS.items():
        assert E.bind(p, E.COMPONENT_SHAS[k])["match"], f"component drift: {k}"
    say("predecessor + bundle immutability re-verified")

    device = get_device(require_cuda=E.CANONICAL_REQUIRES_CUDA)
    assert str(device).startswith("cuda"), device
    say(f"device={device} torch={torch.__version__} cuda={torch.version.cuda}")

    g, r, b_phi, s_omega, counts = load_components(device)
    say(f"components loaded: {counts}")

    rn = load_router_norm()
    sn = load_somega_norm()

    # ---- population ---------------------------------------------------------- #
    rows = S.val808_rows()
    df = pd.DataFrame(rows)
    df = df.sort_values(["dataset", "sample_id"]).reset_index(drop=True)
    assert len(df) == E.VAL808_N, len(df)
    sample_ids = df["sample_id"].astype(str).tolist()

    E.CACHE27.mkdir(parents=True, exist_ok=True)
    mask_dir = E.ROOT / E.MASK_DIR
    mask_dir.mkdir(parents=True, exist_ok=True)

    global_prob_f16 = np.lib.format.open_memmap(
        E.CACHE27 / "phase27_val808_global_prob_f16.npy", mode="w+", dtype=np.float16,
        shape=(len(df), REGIONAL_CANVAS_RESOLUTION, REGIONAL_CANVAS_RESOLUTION))
    final_prob_f16 = np.lib.format.open_memmap(
        E.CACHE27 / "phase27_val808_final_prob_f16.npy", mode="w+", dtype=np.float16,
        shape=(len(df), REGIONAL_CANVAS_RESOLUTION, REGIONAL_CANVAS_RESOLUTION))

    pred_rows = []
    counts_by_state = {"FORCED_SKIP": 0, "SKIP_GLOBAL": 0,
                       "EXECUTE_THEN_ACCEPT": 0, "EXECUTE_THEN_REJECT": 0}
    global_forwards = 0
    refiner_forwards = 0
    somega_forwards = 0
    n_action_unavailable = 0

    TAU = float(Fraction(E.TAU_C8_FINAL_EXACT))
    LAMBDA_C = float(S.LAMBDA_C)

    pos = {sid: i for i, sid in enumerate(sample_ids)}

    domains = sorted(df["dataset"].unique().tolist())
    global_idx = 0
    for dom in domains:
        sub = df[df["dataset"] == dom].reset_index(drop=True)
        n = len(sub)
        say(f"\n[{dom}] n={n}")
        for start in range(0, n, E.BATCH_SIZE):
            chunk = sub.iloc[start:start + E.BATCH_SIZE]
            imgs, tasks = [], []
            for _, row in chunk.iterrows():
                # IMAGE ONLY.  The mask path is never opened in Phase A.
                with Image.open(row["image_path"]) as image:
                    it = image_only_transform(image, REGIONAL_CANVAS_RESOLUTION)
                imgs.append(it)
                tasks.append(int(row["task_id"]))
            batch_img = torch.stack(imgs).to(device)
            batch_task = torch.tensor(tasks, dtype=torch.long, device=device)

            rec = TapRecorder(g)
            try:
                with torch.no_grad(), torch.amp.autocast(device_type=device.type, enabled=True):
                    logits = g(batch_img, batch_task)
                prob = torch.sigmoid(logits.float()).cpu().numpy()[:, 0]
                cmaps_batch = {t: rec.store[t].float().cpu().numpy() for t in TAPS}
            finally:
                rec.close()
            global_forwards += int(batch_img.shape[0])

            for i in range(batch_img.shape[0]):
                row = chunk.iloc[i]
                sid = str(row["sample_id"])
                gi = pos[sid]
                task_id = int(row["task_id"])
                p_global = prob[i].astype(np.float32)

                # ---- persist global (float32 binary decision FIRST) ---------- #
                gbin = full_field_binary_from_prob(p_global)
                Image.fromarray((gbin * 255).astype(np.uint8), mode="L").save(
                    mask_dir / f"{sid}_global.png")
                global_prob_f16[gi] = p_global.astype(np.float16)

                P_g = p_global  # alias for S_omega 256-crop features below

                # ---- action availability (ROI proposal @0.30) ---------------- #
                geom = roi_geometry(p_global, E.ROI_PROPOSAL_THRESHOLD)
                if geom is None:
                    n_action_unavailable += 1
                    state = "FORCED_SKIP"
                    router_utility = ""
                    delta_hat = ""
                    somega_logit = ""
                    somega_accept = ""
                    p_final = p_global
                else:
                    # ---- router features (202-D, GT-free) -------------------- #
                    cmaps = {t: cmaps_batch[t][i] for t in TAPS}
                    feats202 = build_feature_vector(cmaps, p_global, geom)
                    feats_norm = norm_router(feats202, rn)
                    with torch.no_grad():
                        x_num = torch.from_numpy(feats_norm)[None].to(device)
                        t_ids = torch.tensor([task_id], dtype=torch.long, device=device)
                        delta_hat_final = float(b_phi(x_num, t_ids).reshape(-1)[0])
                    util = delta_hat_final - LAMBDA_C
                    router_utility = util
                    delta_hat = delta_hat_final

                    if util < TAU:
                        state = "SKIP_GLOBAL"
                        somega_logit = ""
                        somega_accept = ""
                        p_final = p_global
                    else:
                        # ---- regional refiner (per-sample, EXECUTE branch) --- #
                        # GT-FREE crop extraction: RGB (bilinear) + p_global (bilinear)
                        # only.  The GT crop is NEVER extracted in Phase A.
                        rgb_crop = crop_and_resize_vec(
                            batch_img[i].cpu().numpy(), geom, REGIONAL_INPUT_RESOLUTION)
                        prob_crop = crop_and_resize_vec(
                            p_global, geom, REGIONAL_INPUT_RESOLUTION)
                        rin = np.concatenate(
                            [np.asarray(rgb_crop, dtype=np.float32),
                             np.asarray(prob_crop, dtype=np.float32)], axis=0)
                        with torch.no_grad():
                            rin_t = torch.from_numpy(np.ascontiguousarray(rin))[None].to(device)
                            r_logits = r(rin_t)
                            refined = torch.sigmoid(r_logits.float())[0, 0].cpu().numpy()
                        refiner_forwards += 1
                        p_final = fuse_full_field(p_global, refined, geom)

                        # ---- S_omega 16 numeric features -------------------- #
                        # Canonical Phase25F crops: P_g = p_global resized onto the
                        # 256 crop support (== prob_crop); P_r = the RAW refined 256
                        # crop output (no inverse resize).  See
                        # run_phase25f_oof_source_promotion.py §5.
                        # Canonical cache stores both as 2-D 256x256 float32.
                        pg_crop = np.asarray(prob_crop, dtype=np.float32)
                        if pg_crop.ndim == 3:
                            pg_crop = pg_crop[0]
                        pr_crop = np.asarray(refined, dtype=np.float32)
                        if pr_crop.ndim == 3:
                            pr_crop = pr_crop[0]
                        feat16 = somega_features(pg_crop, pr_crop, geom)
                        feat16n = norm_somega(feat16, sn)
                        onehot = np.zeros(4, dtype=np.float32)
                        onehot[task_id] = 1.0
                        full = np.concatenate([feat16n, onehot]).astype(np.float32)
                        with torch.no_grad():
                            slogit = float(s_omega(torch.from_numpy(full)[None].to(device))
                                           .reshape(-1)[0])
                        somega_forwards += 1
                        acc = float(torch.sigmoid(torch.tensor(slogit)).item())
                        somega_logit = slogit
                        somega_accept = acc
                        if acc >= E.SOMEGA_ACCEPT_THRESHOLD:
                            state = "EXECUTE_THEN_ACCEPT"
                        else:
                            state = "EXECUTE_THEN_REJECT"
                            p_final = p_global

                counts_by_state[state] += 1
                fbin = full_field_binary_from_prob(np.asarray(p_final, dtype=np.float32))
                Image.fromarray((fbin * 255).astype(np.uint8), mode="L").save(
                    mask_dir / f"{sid}_final.png")
                final_prob_f16[gi] = np.asarray(p_final, dtype=np.float32).astype(np.float16)

                pred_rows.append({
                    "sample_id": sid,
                    "dataset": dom,
                    "task_id": task_id,
                    "group_key": S.metadata_group_key(row.to_dict()),
                    "router_utility": "" if router_utility == "" else repr(float(router_utility)),
                    "router_decision": ("EXECUTE" if state in
                                        ("EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT")
                                        else ("SKIP" if state == "SKIP_GLOBAL" else "FORCED_SKIP")),
                    "state_machine_branch": state,
                    "somega_logit": "" if somega_logit == "" else repr(float(somega_logit)),
                    "somega_accept": "" if somega_accept == "" else repr(float(somega_accept)),
                    "global_mask_path": f"{E.MASK_DIR}/{sid}_global.png",
                    "final_mask_path": f"{E.MASK_DIR}/{sid}_final.png",
                })
                global_idx += 1

            say(f"   {start + batch_img.shape[0]:4d}/{n}  "
                f"global_fwd={global_forwards} refine={refiner_forwards} "
                f"somega={somega_forwards} elapsed={time.time()-t0:.0f}s")

    global_prob_f16.flush()
    final_prob_f16.flush()

    # ---- canonical order check ----------------------------------------------- #
    pred_df = pd.DataFrame(pred_rows)
    pred_df = pred_df.sort_values(["dataset", "sample_id"]).reset_index(drop=True)
    assert pred_df["sample_id"].tolist() == sample_ids, "prediction order mismatch"
    E.write_csv(E.ROOT / E.PREDICTIONS_CSV, pred_rows,
                ["sample_id", "dataset", "task_id", "group_key", "router_utility",
                 "router_decision", "state_machine_branch", "somega_logit",
                 "somega_accept", "global_mask_path", "final_mask_path"])

    # ---- hash the prediction artifact BEFORE any GT read --------------------- #
    pred_sha = E.sha256_file(E.ROOT / E.PREDICTIONS_CSV)
    mask_shas = {}
    for sid in sample_ids:
        for tag in ("global", "final"):
            p = mask_dir / f"{sid}_{tag}.png"
            mask_shas[f"{sid}_{tag}"] = E.sha256_file(p)
    gp_sha = E.sha256_file(E.CACHE27 / "phase27_val808_global_prob_f16.npy")
    fp_sha = E.sha256_file(E.CACHE27 / "phase27_val808_final_prob_f16.npy")

    side = {
        "artifact": "phase27_val808_predictions_sha256",
        "phase": "27",
        "classification": E.CLASSIFICATION,
        "method": E.METHOD,
        "execution_phase": "PHASE_A",
        "phase": "27",
        "predictions_csv": E.PREDICTIONS_CSV,
        "predictions_csv_sha256": pred_sha,
        "predictions_row_count": len(pred_rows),
        "global_prob_npy_sha256": gp_sha,
        "final_prob_npy_sha256": fp_sha,
        "mask_count": len(mask_shas),
        "mask_shas_combined_sha256": S.ids_sha([f"{k}:{v}" for k, v in mask_shas.items()]),
        "mask_shas": mask_shas,
        "hashed_before_gt_read": True,
        "gt_reads_at_hash_time": 0,
        "val808_images_read": len(sample_ids),
        "val808_gt_reads": 0,
    }
    E.write_json(E.ROOT / E.PREDICTIONS_CSV_SHA_SIDECAR, side)

    summary = {
        "artifact": "phase27_phaseA_inference_summary",
        "phase": "27",
        "classification": E.CLASSIFICATION,
        "method": E.METHOD,
        "execution_phase": "PHASE_A",
        "population_n": len(sample_ids),
        "val808_images_read": len(sample_ids),
        "val808_gt_reads": 0,
        "global_forwards": global_forwards,
        "refiner_forwards": refiner_forwards,
        "somega_forwards": somega_forwards,
        "action_unavailable": n_action_unavailable,
        "state_counts": counts_by_state,
        "device": str(device),
        "autocast_enabled": True,
        "autocast_dtype": "float16",
        "batch_size": E.BATCH_SIZE,
        "predictions_csv_sha256": pred_sha,
        "elapsed_seconds": round(time.time() - t0, 1),
        "binary_decision_dtype": "float32 (persisted before float16 cast)",
        "gt_never_read_in_phase_a": True,
        "all_pass": True,
    }
    E.write_json(E.AUD / "phase27_phaseA_inference_summary.json", summary)

    say("")
    say("=" * 74)
    say(f"PHASE A COMPLETE  n={len(sample_ids)}  global_forwards={global_forwards}")
    say(f"state counts: {counts_by_state}")
    say(f"refiner_forwards={refiner_forwards} somega_forwards={somega_forwards}")
    say(f"predictions sha256: {pred_sha}")
    say(f"elapsed={time.time()-t0:.0f}s")
    say("=" * 74)
    say("PHASE27_PHASE_A_COMPLETE__PREDICTIONS_HASHED__GT_NOT_READ")
    return 0


# --------------------------------------------------------------------------- #
# helpers that need the refiner geometry
# --------------------------------------------------------------------------- #
def crop_and_resize_vec(arr: np.ndarray, geom: dict, out_size: int) -> np.ndarray:
    """Exact replica of src.data.barr_roi.crop_and_resize (BILINEAR) for one array.

    Crop the clipped window, constant-zero pad to the square side, then bilinear
    resize each channel through PIL mode='F'.  Identical arithmetic to the frozen
    canonical helper; duplicated here so Phase A imports no GT-bearing path.
    """
    from PIL import Image as _I
    cy1, cy2 = int(geom["clip_y1"]), int(geom["clip_y2"])
    cx1, cx2 = int(geom["clip_x1"]), int(geom["clip_x2"])
    window = np.asarray(arr)[..., cy1:cy2, cx1:cx2]
    pads = [(0, 0)] * (window.ndim - 2) + [
        (int(geom["pad_top"]), int(geom["pad_bottom"])),
        (int(geom["pad_left"]), int(geom["pad_right"])),
    ]
    window = np.pad(window, pads, mode="constant", constant_values=0)
    if window.ndim == 2:
        window = window[None, ...]
    channels = []
    for ch in window:
        pil = _I.fromarray(np.ascontiguousarray(ch, dtype=np.float32), mode="F")
        resized = pil.resize((out_size, out_size), _I.Resampling.BILINEAR)
        channels.append(np.asarray(resized, dtype=np.float32))
    return np.stack(channels, axis=0)


def somega_features(p_g_256: np.ndarray, p_r_256: np.ndarray, geom: dict) -> np.ndarray:
    """16-D GT-free post-refinement numeric features (frozen Phase25F definitions)."""
    sys.path.insert(0, str(E.ROOT / "scripts" / "analysis"))
    from phase25f_post_safety_features import compute_numeric_features
    # predicted_roi_area_fraction / predicted_roi_side per frozen Phase25B corrected rule
    x0, x1 = int(geom["clip_x1"]), int(geom["clip_x2"])
    y0, y1 = int(geom["clip_y1"]), int(geom["clip_y2"])
    w_in = max(0, min(REGIONAL_CANVAS_RESOLUTION, x1) - max(0, x0))
    h_in = max(0, min(REGIONAL_CANVAS_RESOLUTION, y1) - max(0, y0))
    area_fraction = (w_in * h_in) / float(REGIONAL_CANVAS_RESOLUTION ** 2)
    side = float(geom["crop_side_pixels"])
    return compute_numeric_features(p_g_256, p_r_256, area_fraction, side)


def fuse_full_field(p_global: np.ndarray, refined_crop_256: np.ndarray,
                    geom: dict):
    """Frozen deterministic fusion: replace inside the valid ROI, keep p_global outside."""
    from PIL import Image as _I
    side = int(geom["crop_side_pixels"])
    clip_y1, clip_y2 = int(geom["clip_y1"]), int(geom["clip_y2"])
    clip_x1, clip_x2 = int(geom["clip_x1"]), int(geom["clip_x2"])
    pad_top, pad_left = int(geom["pad_top"]), int(geom["pad_left"])

    pil = _I.fromarray(np.ascontiguousarray(refined_crop_256, dtype=np.float32), mode="F")
    square = np.asarray(pil.resize((side, side), _I.Resampling.BILINEAR), dtype=np.float32)

    out = np.asarray(p_global, dtype=np.float32).copy()
    wy1, wy2 = pad_top, pad_top + (clip_y2 - clip_y1)
    wx1, wx2 = pad_left, pad_left + (clip_x2 - clip_x1)
    window = square[wy1:wy2, wx1:wx2]
    out[clip_y1:clip_y2, clip_x1:clip_x2] = window
    return out


if __name__ == "__main__":
    raise SystemExit(main())
