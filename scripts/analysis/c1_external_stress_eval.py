"""External stress-test inference driver -- RA-MedFiLM-BARR.

Runs the frozen Global MedFiLM, and (optionally) the frozen four-component BARR
assembly, over the three external cohorts frozen in
``reports/audits/c1_external_stress_v1_0/EXTERNAL_STRESS_TEST_PLAN.md``.

Design constraints, all of which are enforced in code rather than by convention:

  * every component hash is verified against the plan's binding before any forward;
  * ``strict=True`` state-dict loading, no partial reload;
  * ONE preprocessing convention (the canonical aspect-preserving pad transform);
  * ONE threshold (0.5), no per-cohort tuning;
  * batch size 1, fp32, ``torch.inference_mode()``, no autocast;
  * no access to the internal TEST split or ROUTER_HOLDOUT.

Nothing here trains, tunes or modifies a frozen source.  The BARR path imports the
frozen feature extractors and the frozen class definitions verbatim; it supplies
only the population and the per-case bookkeeping.

Usage
-----
    python scripts/analysis/c1_external_stress_eval.py --stage verify
    python scripts/analysis/c1_external_stress_eval.py --stage all
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image, ImageDraw

ROOT = Path(r"D:\Softfors\jup")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

from src.data.barr_roi import (  # noqa: E402
    REGIONAL_CANVAS_RESOLUTION,
    REGIONAL_INPUT_RESOLUTION,
    roi_geometry,
)
from src.data.transforms import SegmentationTransform  # noqa: E402
from src.features.barr_pre_refinement_features import (  # noqa: E402
    NUMERIC_DIM,
    TAPS,
    build_feature_vector,
)
from src.models.barr.regional_refiner import BARRRegionalRefinerV1  # noqa: E402
from src.models.film import GlobalMedFiLM  # noqa: E402
from src.utils.test_lock import verify_test_lock  # noqa: E402

AUD = ROOT / "reports" / "audits" / "c1_external_stress_v1_0"
CACHE = ROOT / "data_cache" / "c1_external_stress_v1_0"
MANI = ROOT / "reports" / "external_extension" / "manifests"

# --------------------------------------------------------------------------- #
# frozen identities -- every digest is re-computed from disk at run time
# --------------------------------------------------------------------------- #
G_CKPT = ROOT / "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"
G_SHA = "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"
R_CKPT = ROOT / "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt"
R_SHA = "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109"
B_CKPT = ROOT / "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt"
B_SHA = "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b"
S_CKPT = ROOT / "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt"
S_SHA = "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e"

ROUTER_CLASS_SRC = ROOT / "scripts/analysis/train_phase25d_router.py"
ROUTER_CLASS_SHA = "fc7c1bdf263ae4551dcb8f170d3203adb8540fbc189846265b74f6eca1541e91"
SAFETY_CLASS_SRC = ROOT / "scripts/analysis/phase25f_execution_common.py"
SAFETY_CLASS_SHA = "98cf958a377e2de30e0b67e63fd56bafea418b2b061a362ee7284e852012cd2e"

# frozen decision constants (seed 42)
TAU_C7 = (24796109646558761, 20000000000000000000)
TAU_C8 = (-5003565381643716252018011, 205414980000000000000000000)
C_ACTION = (1051648, 10270749)
LAMBDA = (1, 4)

ROI_PROPOSAL_THRESHOLD = 0.30
ROI_MARGIN = 0.25
SEG_THRESHOLD = 0.5
SOMEGA_ACCEPT_THRESHOLD = 0.5
ROUTER_SCALAR_IDX = [192, 193, 194, 195, 196, 197, 200, 201]

COHORTS = [
    {"name": "CVC-ClinicDB", "key": "cvc", "task_id": 2,
     "manifest": MANI / "ext02_cvc_clinicdb_manifest.csv", "split": None},
    {"name": "BrEaST-Lesions-USG", "key": "breast", "task_id": 1,
     "manifest": MANI / "ext02_breast_us_manifest.csv", "split": None},
    {"name": "Stones_where_are_you", "key": "stones", "task_id": 3,
     "manifest": MANI / "ext02_1_stones_manifest_reconciled.csv", "split": "test"},
]

STONES_COCO = (ROOT.parent / "final" / "external_test_ds" /
               "Stones_where_are_you-.v3i.coco-segmentation" / "test" /
               "_annotations.coco.json")

STATES = ("NOT_ATTEMPTED", "ROUTED", "EXECUTED", "ACCEPTED",
          "REJECTED", "FALLBACK_TO_GLOBAL", "FAILED")


# --------------------------------------------------------------------------- #
# identity
# --------------------------------------------------------------------------- #
def sha256_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify_identities() -> dict:
    """Recompute every bound digest; abort on any mismatch."""
    checks = {
        "global_checkpoint": (G_CKPT, G_SHA),
        "refiner_checkpoint": (R_CKPT, R_SHA),
        "router_checkpoint": (B_CKPT, B_SHA),
        "safety_checkpoint": (S_CKPT, S_SHA),
        "router_class_source": (ROUTER_CLASS_SRC, ROUTER_CLASS_SHA),
        "safety_class_source": (SAFETY_CLASS_SRC, SAFETY_CLASS_SHA),
    }
    out = {}
    bad = {}
    for name, (path, expect) in checks.items():
        if not path.is_file():
            bad[name] = {"error": "missing", "path": str(path)}
            continue
        actual = sha256_file(path)
        out[name] = {"path": str(path.relative_to(ROOT)).replace("\\", "/"),
                     "sha256": actual, "matches_plan": actual == expect}
        if actual != expect:
            bad[name] = {"expected": expect, "actual": actual}
    if bad:
        raise SystemExit(f"ABORT: identity mismatch -> {json.dumps(bad, indent=2)}")
    return out


# --------------------------------------------------------------------------- #
# cohort construction
# --------------------------------------------------------------------------- #
def load_stones_coco() -> dict:
    """image_id -> list of polygon annotations with category_id == 7 ('stone')."""
    doc = json.loads(STONES_COCO.read_text(encoding="utf-8"))
    by_image = {}
    for ann in doc["annotations"]:
        by_image.setdefault(ann["image_id"], []).append(ann)
    return {"doc": doc, "by_image": by_image}


def build_cohorts() -> dict:
    """Return {key: {"meta":..., "cases":[{...}]}} in frozen manifest order."""
    out = {}
    coco = load_stones_coco()
    coco_by_name = {im["file_name"]: im for im in coco["doc"]["images"]}

    for spec in COHORTS:
        df = pd.read_csv(spec["manifest"])
        if spec["split"] is not None:
            df = df[df["original_split"] == spec["split"]]
        df = df[df["evaluable"] == True]  # noqa: E712 - explicit boolean column
        df = df.reset_index(drop=True)

        cases = []
        for _, r in df.iterrows():
            img_path = Path(r["image_path"])
            gt_field = str(r["gt_path_or_annotation_id"])
            case = {
                "sample_id": str(r["external_sample_id"]),
                "cohort": spec["name"],
                "cohort_key": spec["key"],
                "task_id": int(spec["task_id"]),
                "image_path": str(img_path),
                "gt_kind": "coco" if gt_field.startswith("coco:") else "file",
                "gt_ref": gt_field,
                "cluster_id": str(r.get("sequence_id") if spec["key"] == "cvc"
                                  else (r.get("case_id") if spec["key"] == "breast"
                                        else r["external_sample_id"])),
            }
            if case["gt_kind"] == "coco":
                ann_id = gt_field.split(":")[-1]
                case["coco_image_id"] = int(ann_id)
            else:
                case["gt_path"] = gt_field

            # resolve + validate
            if not img_path.is_file():
                raise SystemExit(f"ABORT: missing image {img_path}")
            if case["gt_kind"] == "file" and not Path(case["gt_path"]).is_file():
                raise SystemExit(f"ABORT: missing mask {case['gt_path']}")
            cases.append(case)

        if spec["key"] == "stones":
            # bind COCO file_name -> image_id for rasterisation
            for c in cases:
                im = coco["doc"]["images"][c["coco_image_id"]]
                c["coco_file_name"] = im["file_name"]
                stone_anns = [a for a in coco["by_image"].get(im["id"], [])
                              if a["category_id"] == 7]
                c["has_stone_annotation"] = len(stone_anns) > 0
                c["n_stone_annotations"] = len(stone_anns)

        out[spec["key"]] = {"name": spec["name"], "task_id": spec["task_id"],
                            "manifest": str(spec["manifest"].relative_to(ROOT)).replace("\\", "/"),
                            "n": len(cases), "cases": cases}
    return out


def rasterise_coco_mask(case: dict, coco: dict) -> np.ndarray:
    """Native-resolution binary mask for category_id == 7 only."""
    im = coco["doc"]["images"][case["coco_image_id"]]
    w, h = int(im["width"]), int(im["height"])
    canvas = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(canvas)
    for ann in coco["by_image"].get(im["id"], []):
        if ann["category_id"] != 7:
            continue
        seg = ann["segmentation"]
        polys = seg if isinstance(seg, list) else [seg]
        for poly in polys:
            pts = [(float(poly[i]), float(poly[i + 1])) for i in range(0, len(poly) - 1, 2)]
            if len(pts) >= 3:
                draw.polygon(pts, fill=1)
    return np.asarray(canvas, dtype=np.uint8) > 0


def load_pair(case: dict, coco: dict, transform: SegmentationTransform):
    """Return (image_tensor[3,512,512], gt_bool[512,512], native_gt_bool)."""
    img = Image.open(case["image_path"])
    if case["gt_kind"] == "coco":
        native = rasterise_coco_mask(case, coco)
        gt_pil = Image.fromarray((native.astype(np.uint8) * 255), mode="L")
    else:
        gt_pil = Image.open(case["gt_path"])
        native = np.asarray(gt_pil.convert("L")) > 0
    img_t, gt_t, _meta = transform(img, gt_pil)
    return img_t, (gt_t[0].numpy() > 0), native


# --------------------------------------------------------------------------- #
# frozen model assembly
# --------------------------------------------------------------------------- #
def load_class_from_ast(path: Path, name: str, prelude: str):
    """Extract one class definition from a frozen source without importing it.

    Used for BARRBenefitRouterV1 and BARRPostSafetyV1 so that the exact frozen
    class body is executed, not a copy.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    ns = {"__name__": "_frozen", "__builtins__": __builtins__}
    exec(prelude, ns)  # noqa: S102 - frozen source, reviewed
    # replay the scalar constants the class body needs
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if any(t in ("FEATURE_DIM", "HIDDEN", "NUMERIC_IDX", "ONEHOT_IDX") for t in targets):
                exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), ns)  # noqa: S102
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), ns)  # noqa: S102
            return ns[name]
    raise RuntimeError(f"{name} not found in {path}")


class TapRecorder:
    """Read-only forward hooks on the three frozen feature taps.

    The hook is attached to the *module*, so it captures the pre-FiLM output --
    exactly the convention Phase 25B used. It does not alter the graph.
    """

    def __init__(self, model: torch.nn.Module, taps=TAPS):
        self.store: dict[str, torch.Tensor] = {}
        self.handles = []
        for tap in taps:
            mod = getattr(model, tap)
            self.handles.append(mod.register_forward_hook(self._make(tap)))

    def _make(self, name: str):
        def hook(_module, _inp, out):
            self.store[name] = out.detach()
        return hook

    def close(self):
        for h in self.handles:
            h.remove()
        self.handles = []


def load_components(device: torch.device) -> dict:
    g = GlobalMedFiLM()
    g.load_state_dict(torch.load(G_CKPT, map_location="cpu", weights_only=False)["model_state"],
                      strict=True)
    g.eval().requires_grad_(False).to(device)
    assert sum(p.numel() for p in g.parameters()) == 3523001

    r = BARRRegionalRefinerV1()
    r.load_state_dict(torch.load(R_CKPT, map_location="cpu", weights_only=False)["model_state"],
                      strict=True)
    r.eval().requires_grad_(False).to(device)
    assert sum(p.numel() for p in r.parameters()) == 1276401

    Router = load_class_from_ast(ROUTER_CLASS_SRC, "BARRBenefitRouterV1",
                                "import torch\nimport torch.nn as nn\n")
    b_st = torch.load(B_CKPT, map_location="cpu", weights_only=False)
    b = Router()
    b.load_state_dict(b_st["model_state"], strict=True)
    b.eval().requires_grad_(False).to(device)
    assert sum(p.numel() for p in b.parameters()) == 36801

    Safety = load_class_from_ast(SAFETY_CLASS_SRC, "BARRPostSafetyV1",
                                 "import torch\nimport torch.nn as nn\nimport numpy as np\n")
    s_st = torch.load(S_CKPT, map_location="cpu", weights_only=False)
    s = Safety()
    s.load_state_dict(s_st["model_state"], strict=True)
    s.eval().requires_grad_(False).to(device)
    assert sum(p.numel() for p in s.parameters()) == 1217

    return {"global": g, "refiner": r, "router": b, "safety": s,
            "router_ckpt": b_st, "safety_ckpt": s_st}


# --------------------------------------------------------------------------- #
# BARR helpers (verbatim semantics from the frozen Phase 29 path)
# --------------------------------------------------------------------------- #
def crop_and_resize_vec(arr: np.ndarray, geom: dict, out_size: int) -> np.ndarray:
    cy1, cy2 = int(geom["clip_y1"]), int(geom["clip_y2"])
    cx1, cx2 = int(geom["clip_x1"]), int(geom["clip_x2"])
    window = np.asarray(arr)[..., cy1:cy2, cx1:cx2]
    pads = [(0, 0)] * (window.ndim - 2) + [
        (int(geom["pad_top"]), int(geom["pad_bottom"])),
        (int(geom["pad_left"]), int(geom["pad_right"]))]
    window = np.pad(window, pads, mode="constant", constant_values=0)
    if window.ndim == 2:
        window = window[None, ...]
    channels = []
    for ch in window:
        pil = Image.fromarray(np.ascontiguousarray(ch, dtype=np.float32), mode="F")
        channels.append(np.asarray(pil.resize((out_size, out_size),
                                              Image.Resampling.BILINEAR), dtype=np.float32))
    return np.stack(channels, axis=0)


def fuse_full_field(p_global: np.ndarray, refined_crop_256: np.ndarray, geom: dict) -> np.ndarray:
    side = int(geom["crop_side_pixels"])
    cy1, cy2 = int(geom["clip_y1"]), int(geom["clip_y2"])
    cx1, cx2 = int(geom["clip_x1"]), int(geom["clip_x2"])
    pad_top, pad_left = int(geom["pad_top"]), int(geom["pad_left"])
    pil = Image.fromarray(np.ascontiguousarray(refined_crop_256, dtype=np.float32), mode="F")
    square = np.asarray(pil.resize((side, side), Image.Resampling.BILINEAR), dtype=np.float32)
    out = np.asarray(p_global, dtype=np.float32).copy()
    out[cy1:cy2, cx1:cx2] = square[pad_top:pad_top + (cy2 - cy1),
                                   pad_left:pad_left + (cx2 - cx1)]
    return out


def somega_features_16(pg_crop: np.ndarray, pr_crop: np.ndarray, geom: dict) -> np.ndarray:
    from phase25f_post_safety_features import compute_numeric_features
    x0, x1 = int(geom["clip_x1"]), int(geom["clip_x2"])
    y0, y1 = int(geom["clip_y1"]), int(geom["clip_y2"])
    w_in = max(0, min(REGIONAL_CANVAS_RESOLUTION, x1) - max(0, x0))
    h_in = max(0, min(REGIONAL_CANVAS_RESOLUTION, y1) - max(0, y0))
    area_fraction = (w_in * h_in) / float(REGIONAL_CANVAS_RESOLUTION ** 2)
    return compute_numeric_features(pg_crop, pr_crop, area_fraction,
                                    float(geom["crop_side_pixels"]))


def apply_norm_8(vec202: np.ndarray, ckpt: dict) -> np.ndarray:
    """Standardise ONLY the 8 frozen scalar indices, using the checkpoint's own stats."""
    out = np.asarray(vec202, dtype=np.float32).copy()
    mu = np.asarray(ckpt["normalizer_mu"], dtype=np.float64).reshape(-1)
    sg = np.asarray(ckpt["normalizer_sigma"], dtype=np.float64).reshape(-1)
    const = np.asarray(ckpt["normalizer_constant_mask"]).reshape(-1)
    assert mu.shape == (8,) and sg.shape == (8,) and const.shape == (8,)
    sig_safe = np.where(sg < 1e-12, 1.0, sg)
    vals = (out[ROUTER_SCALAR_IDX].astype(np.float64) - mu) / sig_safe
    vals = np.where(const, 0.0, vals)
    out[ROUTER_SCALAR_IDX] = vals.astype(np.float32)
    return out


def apply_norm_16(feat16: np.ndarray, ckpt: dict) -> np.ndarray:
    mu = np.asarray(ckpt["normalizer_mu"], dtype=np.float64).reshape(-1)
    sg = np.asarray(ckpt["normalizer_sigma"], dtype=np.float64).reshape(-1)
    const = np.asarray(ckpt["normalizer_constant_mask"]).reshape(-1)
    assert mu.shape == (16,) and sg.shape == (16,) and const.shape == (16,)
    sig_safe = np.where(sg < 1e-12, 1.0, sg)
    vals = (np.asarray(feat16, dtype=np.float64) - mu) / sig_safe
    return np.where(const, 0.0, vals).astype(np.float32)


# --------------------------------------------------------------------------- #
# main inference
# --------------------------------------------------------------------------- #
def run(device: torch.device, do_barr: bool, only: tuple = (), limit: int = 0,
        tag: str = "") -> dict:
    ids = verify_identities()
    verify_test_lock(str(ROOT))

    coco = load_stones_coco()
    cohorts = build_cohorts()
    if only:
        cohorts = {k: v for k, v in cohorts.items() if k in only}
    if limit:
        for v in cohorts.values():
            v["cases"] = v["cases"][:limit]
            v["n"] = len(v["cases"])
    comp = load_components(device)
    transform = SegmentationTransform(size=REGIONAL_CANVAS_RESOLUTION, train=False,
                                      image_mode="RGB")

    tau_c7 = TAU_C7[0] / TAU_C7[1]
    tau_c8 = TAU_C8[0] / TAU_C8[1]
    lam_c = (LAMBDA[0] / LAMBDA[1]) * (C_ACTION[0] / C_ACTION[1])
    assert abs((tau_c8 + lam_c) - tau_c7) < 1e-15

    # ---- warm-up: never counted in latency --------------------------------- #
    with torch.inference_mode():
        _w = torch.zeros(1, 3, 512, 512, device=device)
        for _ in range(3):
            comp["global"](_w, torch.zeros(1, dtype=torch.long, device=device))
        comp["refiner"](torch.zeros(1, 4, 256, 256, device=device))
        comp["router"](torch.zeros(1, NUMERIC_DIM, device=device),
                       torch.zeros(1, dtype=torch.long, device=device))
        comp["safety"](torch.zeros(1, 20, device=device))
    if device.type == "cuda":
        torch.cuda.synchronize()

    summary = {
        "artifact": "c1_external_stress_inference",
        "identities": ids,
        "numeric_mode": "FP32 eval, torch.inference_mode(), no autocast, batch size 1",
        "device": str(device),
        "torch": torch.__version__,
        "thresholds": {"roi_proposal": ROI_PROPOSAL_THRESHOLD, "roi_margin": ROI_MARGIN,
                       "segmentation_output": SEG_THRESHOLD,
                       "somega_accept": SOMEGA_ACCEPT_THRESHOLD,
                       "tau_c7": tau_c7, "tau_c8": tau_c8, "lambda_c": lam_c},
        "barr_enabled": bool(do_barr),
        "cohorts": {},
    }

    for key, co in cohorts.items():
        n = co["n"]
        out_dir = CACHE / (key + tag)
        out_dir.mkdir(parents=True, exist_ok=True)

        prob_g = np.zeros((n, 512, 512), dtype=np.float32)
        gt_all = np.zeros((n, 512, 512), dtype=np.uint8)
        prob_b = np.zeros((n, 512, 512), dtype=np.float32) if do_barr else None

        rows = []
        lat_g, lat_b = [], []
        counts = {s: 0 for s in STATES}
        stage = {"router_forwards": 0, "refiner_forwards": 0, "somega_forwards": 0,
                 "roi_absent": 0}

        for i, case in enumerate(co["cases"]):
            img_t, gt_bool, native_gt = load_pair(case, coco, transform)
            gt_all[i] = gt_bool.astype(np.uint8)

            x = img_t[None].to(device)
            t_id = torch.tensor([case["task_id"]], dtype=torch.long, device=device)

            rec = TapRecorder(comp["global"]) if do_barr else None
            try:
                if device.type == "cuda":
                    torch.cuda.synchronize()
                t0 = time.perf_counter()
                with torch.inference_mode():
                    logits = comp["global"](x, t_id)
                    p = torch.sigmoid(logits.float())[0, 0].cpu().numpy()
                if device.type == "cuda":
                    torch.cuda.synchronize()
                lat_g.append(time.perf_counter() - t0)
                cmaps = ({k: v[0].float().cpu().numpy() for k, v in rec.store.items()}
                         if rec is not None else None)
            finally:
                if rec is not None:
                    rec.close()

            p = np.asarray(p, dtype=np.float32)
            prob_g[i] = p

            row = {
                "sample_id": case["sample_id"], "cohort": co["name"],
                "task_id": case["task_id"], "index": i,
                "gt_pixels": int(gt_bool.sum()),
                "pred_pixels": int((p >= SEG_THRESHOLD).sum()),
                "has_stone_annotation": case.get("has_stone_annotation", ""),
                "n_stone_annotations": case.get("n_stone_annotations", ""),
                "state": "NOT_ATTEMPTED", "router_score": "", "selected": False,
                "safety_prob": "", "accepted": False, "roi_present": False,
                "latency_global_s": lat_g[-1], "latency_barr_s": "",
            }

            if do_barr:
                try:
                    tb0 = time.perf_counter()
                    geom = roi_geometry(p, threshold=ROI_PROPOSAL_THRESHOLD,
                                        margin=ROI_MARGIN)
                    row["roi_present"] = geom is not None
                    if geom is None:
                        stage["roi_absent"] += 1
                        row["state"] = "NOT_ATTEMPTED"
                        prob_b[i] = p
                    else:
                        vec = build_feature_vector(cmaps, p, geom)
                        assert vec.shape == (NUMERIC_DIM,), vec.shape
                        xr = apply_norm_8(vec, comp["router_ckpt"])[None]
                        with torch.inference_mode():
                            delta_hat = float(comp["router"](
                                torch.from_numpy(xr).to(device), t_id).reshape(-1)[0])
                        stage["router_forwards"] += 1
                        row["router_score"] = delta_hat
                        util = delta_hat - lam_c
                        sel_a = delta_hat >= tau_c7
                        sel_b = util >= tau_c8
                        if sel_a != sel_b:
                            raise RuntimeError(
                                f"decision forms disagree on {case['sample_id']}: "
                                f"{delta_hat!r} tau_c7={tau_c7!r} tau_c8={tau_c8!r}")
                        row["selected"] = bool(sel_a)

                        if not sel_a:
                            row["state"] = "NOT_ATTEMPTED"
                            prob_b[i] = p
                        else:
                            row["state"] = "ROUTED"
                            rgb = np.asarray(img_t.numpy(), dtype=np.float32)
                            rgb_crop = crop_and_resize_vec(rgb, geom, REGIONAL_INPUT_RESOLUTION)
                            prob_crop = crop_and_resize_vec(p, geom, REGIONAL_INPUT_RESOLUTION)
                            rin = np.concatenate([rgb_crop, prob_crop], axis=0)
                            with torch.inference_mode():
                                refined = torch.sigmoid(
                                    comp["refiner"](torch.from_numpy(
                                        np.ascontiguousarray(rin))[None].to(device)
                                    ).float())[0, 0].cpu().numpy()
                            stage["refiner_forwards"] += 1
                            row["state"] = "EXECUTED"

                            pg_crop = np.asarray(prob_crop[0], dtype=np.float32)
                            pr_crop = np.asarray(refined, dtype=np.float32)
                            f16 = somega_features_16(pg_crop, pr_crop, geom)
                            f16n = apply_norm_16(f16, comp["safety_ckpt"])
                            onehot = np.zeros(4, dtype=np.float32)
                            onehot[case["task_id"]] = 1.0
                            full = np.concatenate([f16n, onehot]).astype(np.float32)
                            with torch.inference_mode():
                                slogit = float(comp["safety"](
                                    torch.from_numpy(full)[None].to(device)).reshape(-1)[0])
                            stage["somega_forwards"] += 1
                            sp = float(torch.sigmoid(torch.tensor(slogit)).item())
                            row["safety_prob"] = sp
                            acc = sp >= SOMEGA_ACCEPT_THRESHOLD
                            row["accepted"] = bool(acc)
                            if acc:
                                row["state"] = "ACCEPTED"
                                prob_b[i] = fuse_full_field(p, refined, geom)
                            else:
                                row["state"] = "REJECTED"
                                prob_b[i] = p
                    lat_b.append(time.perf_counter() - tb0)
                    row["latency_barr_s"] = lat_b[-1]
                except Exception as exc:  # noqa: BLE001 - recorded, never swallowed
                    row["state"] = "FAILED"
                    row["error"] = f"{type(exc).__name__}: {exc}"
                    prob_b[i] = p
                    summary.setdefault("failures", []).append(
                        {"sample_id": case["sample_id"],
                         "traceback": traceback.format_exc()})

            counts[row["state"]] = counts.get(row["state"], 0) + 1
            rows.append(row)

            if (i + 1) % 100 == 0 or i == n - 1:
                print(f"  [{key}] {i + 1}/{n}  states={ {k: v for k, v in counts.items() if v} }")

        np.save(out_dir / "prob_global.npy", prob_g)
        np.save(out_dir / "pred_global.npy", (prob_g >= SEG_THRESHOLD).astype(np.uint8))
        np.save(out_dir / "gt.npy", gt_all)
        (out_dir / "sample_ids.json").write_text(json.dumps(
            [c["sample_id"] for c in co["cases"]], indent=1) + "\n", encoding="utf-8")
        (out_dir / "meta.json").write_text(json.dumps(
            {"cohort": co["name"], "task_id": co["task_id"], "n": n,
             "manifest": co["manifest"]}, indent=2) + "\n", encoding="utf-8")

        if do_barr:
            np.save(out_dir / "prob_barr.npy", prob_b)
            np.save(out_dir / "pred_barr.npy", (prob_b >= SEG_THRESHOLD).astype(np.uint8))
            pd.DataFrame(rows).to_csv(out_dir / "barr_states.csv", index=False)
        else:
            pd.DataFrame(rows).to_csv(out_dir / "cases.csv", index=False)

        summary["cohorts"][key] = {
            "name": co["name"], "n": n, "task_id": co["task_id"],
            "states": counts,
            "stage_counts": stage,
            "n_roi_absent": int(stage["roi_absent"]),
            "latency_global_median_s": float(np.median(lat_g)),
            "latency_global_iqr_s": [float(np.percentile(lat_g, 25)),
                                     float(np.percentile(lat_g, 75))],
            "latency_barr_median_s": (float(np.median(lat_b)) if lat_b else None),
            "latency_barr_iqr_s": ([float(np.percentile(lat_b, 25)),
                                    float(np.percentile(lat_b, 75))] if lat_b else None),
            "sha256": {
                "prob_global.npy": sha256_file(out_dir / "prob_global.npy"),
                "pred_global.npy": sha256_file(out_dir / "pred_global.npy"),
                "gt.npy": sha256_file(out_dir / "gt.npy"),
                **({"prob_barr.npy": sha256_file(out_dir / "prob_barr.npy"),
                    "pred_barr.npy": sha256_file(out_dir / "pred_barr.npy")}
                   if do_barr else {}),
            },
            "n_stone_positive": int(sum(1 for c in co["cases"]
                                        if c.get("has_stone_annotation") is True)),
        }

    (AUD / (("barr_execution" if do_barr else "global_inference") + tag + ".json")).write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v["states"] for k, v in summary["cohorts"].items()}, indent=2))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all",
                    choices=["verify", "global", "barr", "all"])
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--cohorts", default="", help="comma separated: cvc,breast,stones")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--tag", default="", help="suffix for output paths (smoke tests)")
    args = ap.parse_args()

    if args.stage == "verify":
        ids = verify_identities()
        verify_test_lock(str(ROOT))
        print(json.dumps(ids, indent=2))
        print("IDENTITIES_OK")
        return 0

    device = torch.device(args.device if (args.device == "cpu" or torch.cuda.is_available())
                          else "cpu")
    only = tuple(x.strip() for x in args.cohorts.split(",") if x.strip())
    print(f"device={device} cohorts={only or 'ALL'} limit={args.limit or 'none'}")
    run(device, do_barr=(args.stage in ("barr", "all")), only=only,
        limit=args.limit, tag=args.tag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
