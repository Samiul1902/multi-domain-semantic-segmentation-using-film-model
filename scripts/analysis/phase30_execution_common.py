#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase30 ONE-SHOT ROUTER_HOLDOUT execution — shared helpers.

Governance constants, deterministic IO, SHA binding, model loading and the
canonical component inference helpers.

This module performs NO image read and NO GT read at import time.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures"
CACHE30 = ROOT / "data_cache" / "phase30_final_dev_validation_v1_0"
ONESHOT = CACHE30 / "canonical_one_shot"

METHOD = "RA-MedFiLM-BARR"
SPEC_REVISION = "ra_medfilm_barr_phase30_final_dev_validation_v1_3"

# ---------------------------------------------------------------- §0 bindings
ENTRY_BINDINGS = [
    ("reports/audits/phase30_specification_terminal_v1_3.json",
     "61f615b8ccab4b4b5ad3bf493dc3ffe7b78b23437b17277aaa0bd2d54c39a074"),
    ("reports/audits/phase30_preexecution_final_check_v1_3.json",
     "aa16a8782196d9434c5e4ba54d1cfad93562d6bee7a5386f4de240d02b67ee5a"),
    ("docs/phase30_final_development_validation_spec_v1_3.md",
     "bcc98c6c2b27290159855e43469e35c3b9575227232c6e3a2620bcef05667a8c"),
    ("reports/audits/phase30_primary_inferential_adjudication_contract_v1_3.json",
     "51a0b23388f3a4c34edd400d3e7c165770c2a5ab8e8dabbd7c7479b5e3844a79"),
    ("reports/audits/phase30_p_value_disposition_v1_3.json",
     "03c81379115a17a919561df97f6993940544a7f81890321b356acffd43eba920"),
    ("reports/audits/phase30_raw_p_value_provenance_v1_3.json",
     "af9b5426615ed5fd0b578e9947374c8776ca923b6ad2871edbaa823799ecccc3"),
    ("reports/audits/phase30_global_batch_membership_contract_v1_1.json",
     "8e10bd0dfe83b7cde67aa90b0069d3aab7b01d787e9f29a1953bc5820300cd89"),
    ("reports/audits/phase30_claim_hierarchy_contract_v1_2.json",
     "2f3ee0113af7271b31f84e40a37706fe0484a75bebe958e3266a8c0465388f89"),
    ("reports/audits/phase30_a7_descriptive_companion_contract_v1_2.json",
     "f6fc503bb3552890c7d73288464a1503199d7c14a70ac0fc021fa3b7cc8c980e"),
]
TERMINAL_V1_3 = (
    "PHASE30_PREEXECUTION_SPEC_V1_3_COMPLETE__PRIMARY_NONINFERIORITY_CI_AND_PVALUE_"
    "PROVENANCE_FROZEN__ONE_SHOT_EXECUTION_ELIGIBLE_NOT_STARTED")

# ------------------------------------------------------------ §2 bundle
BUNDLE_MANIFEST = "artifacts/phase26_ra_medfilm_barr_bundle_v1_0/canonical_bundle_manifest.json"
BUNDLE_MANIFEST_SHA = "f7aebb0f646bcc8de49fa91b70a4c4cc1051c9998ab6b055a8d4d187809cb3d9"
COMPONENT_PATHS = {
    "G": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
    "R_psi": "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
    "B_phi": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
    "S_omega": "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
}
COMPONENT_SHAS = {
    "G": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
    "R_psi": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
    "B_phi": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
    "S_omega": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
}
COMPONENT_PARAMS = {"G": 3523001, "R_psi": 1276401, "B_phi": 36801, "S_omega": 1217}
NORMALIZATIONS = {
    "router": ("reports/tables/phase25d_final_normalization_stats.csv",
               "ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb"),
    "post_safety": ("reports/tables/phase25f_final_normalization_stats.csv",
                    "e112e18b134c6edcdcd0c254c362d0a954a75faffe634cc37a2a17e4fe6f4e7b"),
}
SCHEMAS = {
    "router": ("reports/tables/phase25b_feature_schema.csv",
               "da76aa34f14006146f46ca799f173378274d8c9d0792dc18edb30711a2486dd4"),
    "post_safety": ("reports/tables/phase25f_feature_schema_v1_0.csv",
                    "3e70e20c541b93de752980c34cdfb6fe5af17ebe4c18cbb64397c0bbae465ee5"),
}
G_CONFIG = "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json"

# ------------------------------------------------------------ §3 population
SPLIT_MANIFEST = "reports/audits/phase24_router_split_manifest.csv"
SPLIT_MANIFEST_SHA = "b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555"
G_BATCH_MANIFEST = "reports/tables/phase30_router_holdout_g_batch_manifest.csv"
G_BATCH_MANIFEST_SHA = "fc4c785770c45523fdfd440a464820f78caa6bcedeaa1cbe264e10ce5c4e0088"
BOOTSTRAP_PLAN = "data_cache/phase30_final_dev_validation_v1_0/phase30_router_holdout_bootstrap_plan.npz"
BOOTSTRAP_PLAN_SHA = "59c97ccf6fbea823d38a1fba12d5e81b7e5fb103f31bc7fdfe443fd4971faab1"
HOLDOUT_N = 875
HOLDOUT_GROUPS = 628
DOMAINS = ["BUSI", "ISIC", "KUB", "KVASIR"]
DOMAIN_N = {"BUSI": 90, "ISIC": 383, "KUB": 298, "KVASIR": 104}
TASK_ID = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}

# ------------------------------------------------------------ §4 policy
RUNTIME_SCORE = "delta_hat_final - 0.25*C"
TAU_C8_EXACT = (-5003565381643716252018011, 205414980000000000000000000)
TAU_C7_EXACT = (24796109646558761, 20000000000000000000)
LAMBDA_C_EXACT = (262912, 10270749)
ROI_PROPOSAL_THRESHOLD = 0.30
SEGMENTATION_OUTPUT_THRESHOLD = 0.50
SOMEGA_ACCEPT_THRESHOLD = 0.50

# ------------------------------------------------------------ §5 numerics
BATCH_SIZE = 8
SOMEGA_BATCH = 128
CANVAS = 512
CROP = 256
BENEFICIAL_DELTA = 0.02
HARMFUL_DELTA = -0.01
NONINFERIORITY_MARGIN = 0.005
N_BOOT = 2000
BOOTSTRAP_SEED = 42

# ------------------------------------------------------------ §21 compute
MAC = {"global": 31551740928, "benefit_router": 36160, "regional_refiner": 3230662656,
       "s_omega": 1168}
COMPUTE_LABEL = "ANALYTICAL MAC LOWER BOUND"


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def sha256_ids(ids) -> str:
    return hashlib.sha256(("\n".join(str(i) for i in ids) + "\n").encode("utf-8")).hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(obj, path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, indent=1) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def write_csv(path, header, rows) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(path) + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(r)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows_of(p):
    with open(ROOT / p, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def bind(rel, exp=None):
    p = ROOT / rel
    ex = p.exists()
    a = sha256_file(p) if ex else None
    return {"path": rel, "exists": ex, "sha256": a, "expected_sha256": exp,
            "match": bool(ex and (exp is None or a == exp))}


def tau_float(pair) -> float:
    from fractions import Fraction
    return float(Fraction(int(pair[0]), int(pair[1])))


# ------------------------------------------------------------ model loading
def load_g(device):
    import torch
    from src.models.film.global_medfilm import GlobalMedFiLM
    cfg = read_json(ROOT / G_CONFIG)
    g = GlobalMedFiLM(
        task_count=cfg["model"]["task_count"], in_channels=cfg["model"]["in_channels"],
        out_channels=cfg["model"]["out_channels"], channels=tuple(cfg["model"]["channels"]),
        task_embedding_dim=cfg["model"]["task_embedding_dim"],
        film_hidden_dim=cfg["model"]["film_hidden_dim"])
    g.load_state_dict(torch.load(ROOT / COMPONENT_PATHS["G"], map_location="cpu",
                                 weights_only=False)["model_state"])
    g.eval(); g.requires_grad_(False); g.to(device)
    assert sum(p.numel() for p in g.parameters()) == COMPONENT_PARAMS["G"]
    return g


def load_rpsi(device):
    import torch
    from src.models.barr.regional_refiner import BARRRegionalRefinerV1
    r = BARRRegionalRefinerV1()
    r.load_state_dict(torch.load(ROOT / COMPONENT_PATHS["R_psi"], map_location="cpu",
                                 weights_only=False)["model_state"])
    r.eval(); r.requires_grad_(False); r.to(device)
    assert sum(p.numel() for p in r.parameters()) == COMPONENT_PARAMS["R_psi"]
    return r


def load_router_class():
    import ast
    import torch
    src = (ROOT / "scripts/analysis/train_phase25d_router.py").read_text(encoding="utf-8")
    for node in ast.parse(src).body:
        if isinstance(node, ast.ClassDef) and node.name == "BARRBenefitRouterV1":
            ns = {"__name__": "_p30_router", "__builtins__": __builtins__}
            exec("import torch\nimport torch.nn as nn\n", ns)
            exec(compile(ast.Module(body=[node], type_ignores=[]),
                         "train_phase25d_router.py", "exec"), ns)
            return ns["BARRBenefitRouterV1"]
    raise RuntimeError("BARRBenefitRouterV1 not found")


def load_somega_class():
    import ast
    import numpy as np
    import torch
    path = ROOT / "scripts/analysis/phase25f_execution_common.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    ns = {"__name__": "_p30_somega", "torch": torch, "nn": torch.nn, "np": np}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            tg = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if any(t in ("FEATURE_DIM", "HIDDEN", "NUMERIC_IDX", "ONEHOT_IDX") for t in tg):
                exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), ns)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "BARRPostSafetyV1":
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), ns)
            return ns["BARRPostSafetyV1"]
    raise RuntimeError("BARRPostSafetyV1 not found")


def load_bphi(device):
    import torch
    st = torch.load(ROOT / COMPONENT_PATHS["B_phi"], map_location="cpu", weights_only=False)
    assert int(st.get("seed", -1)) == 42, st.get("seed")
    m = load_router_class()()
    m.load_state_dict(st["model_state"])
    m.eval(); m.requires_grad_(False); m.to(device)
    assert sum(p.numel() for p in m.parameters()) == COMPONENT_PARAMS["B_phi"]
    return m, st


def load_somega(device):
    import torch
    st = torch.load(ROOT / COMPONENT_PATHS["S_omega"], map_location="cpu", weights_only=False)
    assert int(st.get("seed", -1)) == 42, st.get("seed")
    m = load_somega_class()()
    m.load_state_dict(st["model_state"])
    m.eval(); m.requires_grad_(False); m.to(device)
    assert sum(p.numel() for p in m.parameters()) == COMPONENT_PARAMS["S_omega"]
    return m, st


# ------------------------------------------------------------ transforms
def image_only_transform(image, size=CANVAS):
    """Image-only canonical path (aspect-preserving bilinear resize + centre pad)."""
    import numpy as np
    import torch
    from PIL import Image, ImageOps
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


def crop_and_resize_vec(arr, geom, out_size):
    import numpy as np
    from PIL import Image as _I
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
        pil = _I.fromarray(np.ascontiguousarray(ch, dtype=np.float32), mode="F")
        channels.append(np.asarray(pil.resize((out_size, out_size),
                                              _I.Resampling.BILINEAR), dtype=np.float32))
    return np.stack(channels, axis=0)


def fuse_full_field(p_global, refined_crop_256, geom):
    import numpy as np
    from PIL import Image as _I
    side = int(geom["crop_side_pixels"])
    clip_y1, clip_y2 = int(geom["clip_y1"]), int(geom["clip_y2"])
    clip_x1, clip_x2 = int(geom["clip_x1"]), int(geom["clip_x2"])
    pad_top, pad_left = int(geom["pad_top"]), int(geom["pad_left"])
    pil = _I.fromarray(np.ascontiguousarray(refined_crop_256, dtype=np.float32), mode="F")
    square = np.asarray(pil.resize((side, side), _I.Resampling.BILINEAR), dtype=np.float32)
    out = np.asarray(p_global, dtype=np.float32).copy()
    out[clip_y1:clip_y2, clip_x1:clip_x2] = square[pad_top:pad_top + (clip_y2 - clip_y1),
                                                   pad_left:pad_left + (clip_x2 - clip_x1)]
    return out


def somega_features(p_g_256, p_r_256, geom):
    from phase25f_post_safety_features import compute_numeric_features
    x0, x1 = int(geom["clip_x1"]), int(geom["clip_x2"])
    y0, y1 = int(geom["clip_y1"]), int(geom["clip_y2"])
    w_in = max(0, min(CANVAS, x1) - max(0, x0))
    h_in = max(0, min(CANVAS, y1) - max(0, y0))
    area_fraction = (w_in * h_in) / float(CANVAS ** 2)
    return compute_numeric_features(p_g_256, p_r_256, area_fraction,
                                    float(geom["crop_side_pixels"]))


def full_field_gt(mask_path, size=CANVAS):
    import numpy as np
    from PIL import Image, ImageOps
    img = Image.open(mask_path).convert("L")
    w, h = img.size
    scale = min(size / w, size / h)
    rw, rh = max(1, round(w * scale)), max(1, round(h * scale))
    img = img.resize((rw, rh), Image.Resampling.NEAREST)
    left, top = (size - rw) // 2, (size - rh) // 2
    img = ImageOps.expand(img, (left, top, size - rw - left, size - rh - top))
    return (np.asarray(img) > 0).astype(np.uint8)


def canon_dice(pred_bin, gt_bin):
    from src.metrics.evaluation_metrics import binary_confusion_counts, dice as dice_fn
    return float(dice_fn(binary_confusion_counts(pred_bin, gt_bin)))
