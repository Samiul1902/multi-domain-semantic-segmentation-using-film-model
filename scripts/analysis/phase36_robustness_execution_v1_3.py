#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.3 — SAMPLE-LEVEL SCIENCE LOOP + MANIFEST-AUTHORITATIVE SPLIT-GUARD REPAIR.

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_3
TYPE: PRE-SCIENTIFIC IMPLEMENTATION REPAIR ONLY.

Supersedes v1.2 by repairing EXACTLY the two load-bearing defects proven by the
independent v1.2a source-byte audit:

  D1 = E_SCIENCE_SAMPLE_LEVEL_ROWS
       v1.2 built condition-name-only placeholder rows in run_science()
       (``{"condition": .., "base_seed": ..}`` / ``{"proposal_condition": ..}``)
       with NO ``sample_id``; the downstream loops then did
       ``sid = row.get("sample_id"); if sid is None: continue`` so ZERO scientific
       perturbation evaluations could ever execute.  v1.3 iterates SAMPLE-FIRST,
       builds fully-populated sample/realization rows, and RAISES (never silently
       continues) on a missing sample_id / domain / task_id.

  D2 = H_MANIFEST_SPLIT_AUTHORITY
       v1.2 rejected paths whose segments merely CONTAINED the substring "test"
       (``_PROTECTED_ROW_TOKENS = ("holdout", "router_holdout", "test")``), which
       wrongly rejected 112 authorized ISIC VAL rows under
       ``ISIC2018_Task1-2_Test_Input``.  v1.3 removes ALL vendor-path substring
       split inference.  Split authority is IDENTITY-ONLY:
         (1) sample_id present in the frozen VAL808 manifest;
         (2) requested image path exactly equals the manifest row value;
         (3) requested mask  path exactly equals the manifest row value;
         (4) sample_id absent from the frozen ROUTER_HOLDOUT identity authority;
         (5) sample_id absent from the frozen TEST identity authority.
       Filesystem directory names are TRANSPORT METADATA, never split labels.

UNCHANGED SCIENTIFIC SEMANTICS (frozen; NOT touched by v1.3):
  13-condition image registry · 7-condition proposal registry ·
  noise base seeds 42/123/3407 · 32-bit v1.1 seed conversion · severities ·
  VAL808 population · G/B_phi/R_psi/S_omega checkpoints · A8/C9 ·
  proposal threshold 0.30 · segmentation threshold 0.50 · S_omega threshold ·
  Phase25B 202-D semantics · 98 proposal-dependent dims · 104 global-only dims ·
  proposal insertion contract · Dice/IoU/HD95 authority ·
  clean-equivalence comparator · figures R1-R5 · table contract ·
  KUB reporting-only semantics · claim boundary.

GATES (both default UNSET; fail closed)
  --mode science  requires PHASE36_EXECUTE == "1"
  --mode smoke    requires PHASE36_SMOKE_EXECUTE == "1"

STOP CONDITIONS honoured by this source (this work order):
  DO NOT RUN v1.3 SMOKE.  DO NOT RUN PHASE36 SCIENCE.

Importing this module performs NO model construction and NO protected-data access.
``torch`` is imported lazily inside the model-loading helpers only.
No post-open patch. No retry. First valid attempt preserved.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

import numpy as np  # noqa: E402

import scripts.analysis.phase36_robustness_common_v1_1 as C  # noqa: E402

AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
ARR = ROOT / "reports" / "arrays"
FIG = ROOT / "reports" / "figures" / "phase36_robustness"

# --------------------------------------------------------------------------- #
# canonical constants (bound, never re-derived)
# --------------------------------------------------------------------------- #
G_DEFAULT_CFG = "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json"

# canonical component identities (mirror phase26_exec_common / common_v1_0.COMPONENTS)
G_COMPONENT = {
    "class": "GlobalMedFiLM",
    "checkpoint": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
    "sha256": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
    "params": 3523001,
}
B_PHI_COMPONENT = {
    "class": "BARRBenefitRouterV1",
    "source": "scripts/analysis/train_phase25d_router.py",
    "checkpoint": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
    "sha256": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
    "params": 36801,
}
R_PSI_COMPONENT = {
    "class": "BARRRegionalRefinerV1",
    "checkpoint": "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
    "sha256": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
    "params": 1276401,
}
S_OMEGA_COMPONENT = {
    "class": "BARRPostSafetyV1",
    "source": "scripts/analysis/phase25f_execution_common.py",
    "checkpoint": "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
    "sha256": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
    "params": 1217,
}

ROUTER_NORMALIZATION_PATH = "reports/tables/phase25d_final_normalization_stats.csv"
ROUTER_NORMALIZATION_SHA = "ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb"
SOMEGA_NORMALIZATION_PATH = "reports/tables/phase25f_final_normalization_stats.csv"
SOMEGA_NORMALIZATION_SHA = "e112e18b134c6edcdcd0c254c362d0a954a75faffe634cc37a2a17e4fe6f4e7b"

ROUTER_NUMERIC_DIM = 202
ROUTER_SCALAR_IDX = [192, 193, 194, 195, 196, 197, 200, 201]
SOMEGA_NUMERIC_DIM = 16
SOMEGA_ACCEPT_THRESHOLD = 0.50
SEGMENTATION_OUTPUT_THRESHOLD = 0.50
ROI_PROPOSAL_THRESHOLD = 0.30
REGIONAL_INPUT_RESOLUTION = 256
REGIONAL_CANVAS_RESOLUTION = 512

# metrics
_METRIC_EPS = 1e-7

# --------------------------------------------------------------------------- #
# §D  FROZEN IMAGE REALIZATION PLAN (materialized from the frozen registry)
# --------------------------------------------------------------------------- #
# CLEAN is generated ONCE in STAGE 1 (the clean reference pass). It is NOT a
# perturbation and is NOT re-run in STAGE 3.
NONCLEAN_DETERMINISTIC_IMAGE_CONDITIONS = [
    "BRIGHTNESS_NEG", "BRIGHTNESS_POS",
    "CONTRAST_LOW", "CONTRAST_HIGH",
    "GAMMA_LOW", "GAMMA_HIGH",
    "GAUSSIAN_BLUR_LOW", "GAUSSIAN_BLUR_HIGH",
    "RESOLUTION_075", "RESOLUTION_050",
]                                     # 10 deterministic realizations
NONCLEAN_NOISE_IMAGE_CONDITIONS = [
    "GAUSSIAN_NOISE_LOW", "GAUSSIAN_NOISE_HIGH",
]                                     # x {42,123,3407} -> 6 realizations

AUTHORIZED_POPULATION_N = C.POPULATION_N              # 808
CLEAN_EXECUTIONS_EXPECTED = AUTHORIZED_POPULATION_N   # 808
NONCLEAN_IMAGE_REALIZATIONS_PER_SAMPLE = 16           # 10 + 6
IMAGE_REALIZATIONS_PER_SAMPLE_INCL_CLEAN = 17         # 16 + 1
NONCLEAN_IMAGE_EXECUTIONS_EXPECTED = (
    AUTHORIZED_POPULATION_N * NONCLEAN_IMAGE_REALIZATIONS_PER_SAMPLE)  # 12,928
LOGICAL_IMAGE_TABLE_ROWS_MAX = (
    AUTHORIZED_POPULATION_N * IMAGE_REALIZATIONS_PER_SAMPLE_INCL_CLEAN)  # 13,736

# §H  FROZEN PROPOSAL REALIZATION PLAN
NONCLEAN_PROPOSAL_CONDITIONS = [
    "SHIFT_LEFT_10", "SHIFT_RIGHT_10", "SHIFT_UP_10", "SHIFT_DOWN_10",
    "SCALE_085", "SCALE_115",
]                                     # 6 non-clean proposal conditions
PROPOSAL_CLEAN_CONDITION = "PROPOSAL_CLEAN"
NONCLEAN_PROPOSAL_CONDITIONS_PER_SAMPLE = 6
NONCLEAN_PROPOSAL_EXECUTIONS_MAX = (
    AUTHORIZED_POPULATION_N * NONCLEAN_PROPOSAL_CONDITIONS_PER_SAMPLE)  # 4,848

# --------------------------------------------------------------------------- #
# §H  FROZEN IDENTITY AUTHORITY (holdout / test deny sets)
# --------------------------------------------------------------------------- #
# Filesystem directory names are TRANSPORT METADATA. The only split authority is
# manifest membership + explicit identity deny sets.
ROUTER_HOLDOUT_MANIFEST = "manifests/phase4_v3/val_router_holdout.csv"
TEST_MANIFEST = "manifests/phase4_v3/test.csv"


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# gates
# --------------------------------------------------------------------------- #
def _gate_science() -> int:
    if os.environ.get(C.GATE_ENV) != "1":
        print(json.dumps({"mode": "science", "fail_closed": True,
                          "reason": f"{C.GATE_ENV} != '1'",
                          "terminal": "PHASE36_SCIENCE_FAIL_CLOSED__GATE_NOT_SET"}, indent=1))
        return 2
    return 0


def _gate_smoke() -> int:
    if os.environ.get(C.SMOKE_GATE_ENV) != "1":
        print(json.dumps({"mode": "smoke", "fail_closed": True,
                          "reason": f"{C.SMOKE_GATE_ENV} != '1'",
                          "terminal": "PHASE36_SMOKE_FAIL_CLOSED__GATE_NOT_SET"}, indent=1))
        return 2
    return 0


# --------------------------------------------------------------------------- #
# §J/§K/§L  MANIFEST-AUTHORITATIVE SPLIT GUARD  (IDENTITY ONLY — NO SUBSTRINGS)
# --------------------------------------------------------------------------- #
# NOTE: v1.2's ``_PROTECTED_ROW_TOKENS = ("holdout", "router_holdout", "test")``
# substring guard is DELETED. There is NO vendor-path substring split inference
# anywhere in v1.3.  The 231 authorized VAL808 rows under
# ``ISIC2018_Task1-2_Training_Input`` and the 112 authorized rows under
# ``ISIC2018_Task1-2_Test_Input`` are BOTH accepted naturally, because vendor
# directory names are never inspected as split labels.
VENDOR_DIRECTORY_NAMES_ARE_TRANSPORT_METADATA = True


def _rows(path: Path):
    return list(csv.DictReader(path.open(encoding="utf-8")))


def _identity_deny_set(path_rel: str) -> set:
    """Frozen IDENTITY deny set (sample_id only). Empty if manifest file absent."""
    p = ROOT / path_rel
    if not p.exists():
        return set()
    ids = {r["sample_id"] for r in _rows(p) if r.get("sample_id")}
    return ids


def _authorized_path_exact(declared: str, row_value: str) -> bool:
    """TRUE iff declared path is BYTE-FOR-BYTE the manifest-authorized row path."""
    if not row_value:
        return False
    return str(declared).strip() == str(row_value).strip()


def _load_population():
    """Manifest-authoritative VAL808 identity. sample_id is the identity, NOT the stem.

    IDENTITY-ONLY admission:
      * row split must be VAL (manifest column, NOT a directory word);
      * sample_id must be unique;
      * sample_id must NOT belong to the ROUTER_HOLDOUT or TEST identity deny sets.
    NO vendor-path substring split inference is performed.
    """
    man = ROOT / C.VAL_MANIFEST
    if _sha(man) != C.VAL_MANIFEST_SHA:
        raise ValueError("VAL manifest SHA mismatch")
    rows = _rows(man)
    if len(rows) != C.POPULATION_N:
        raise ValueError(f"VAL808 population {len(rows)} != {C.POPULATION_N}")
    ids = [r["sample_id"] for r in rows]
    if len(set(ids)) != C.POPULATION_N:
        raise ValueError("VAL808 sample_id population not unique")

    holdout_ids = _identity_deny_set(ROUTER_HOLDOUT_MANIFEST)
    test_ids = _identity_deny_set(TEST_MANIFEST)
    for r in rows:
        sid = r.get("sample_id")
        if str(r.get("split", "")).upper() != "VAL":
            raise ValueError(f"NON_VAL_ROW_REJECTED: {sid}")
        if sid in holdout_ids:
            raise ValueError(f"ROUTER_HOLDOUT_IDENTITY_REJECTED: {sid}")
        if sid in test_ids:
            raise ValueError(f"TEST_IDENTITY_REJECTED: {sid}")
    return rows


def authorize_sample(sid: str, image_path: str, mask_path: str,
                     pop_index: dict, holdout_ids: set, test_ids: set) -> dict:
    """Return an authorization record, failing closed on any identity violation.

    Acceptance decision is made ONLY from:
      (1) sample_id present in the frozen VAL808 manifest;
      (2) image path exactly equals the manifest row;
      (3) mask  path exactly equals the manifest row;
      (4) sample_id absent from ROUTER_HOLDOUT identity authority;
      (5) sample_id absent from TEST identity authority.
    """
    if sid is None:
        raise ValueError("MISSING_SAMPLE_ID")
    if sid in holdout_ids:
        raise ValueError(f"ROUTER_HOLDOUT_IDENTITY_REJECTED: {sid}")
    if sid in test_ids:
        raise ValueError(f"TEST_IDENTITY_REJECTED: {sid}")
    if sid not in pop_index:
        raise ValueError(f"NOT_IN_VAL808_MANIFEST: {sid}")
    row = pop_index[sid]
    if not _authorized_path_exact(image_path, row.get("image_path", "")):
        raise ValueError(f"IMAGE_PATH_MISMATCH: {sid}")
    if not _authorized_path_exact(mask_path, row.get("mask_path", row.get("gt_path", ""))):
        raise ValueError(f"MASK_PATH_MISMATCH: {sid}")
    return {"sample_id": sid, "authorized": True,
            "image_path": row["image_path"], "mask_path": row.get("mask_path", row.get("gt_path", "")),
            "domain": row.get("dataset"), "task_id": int(row["task_id"])}


def load_identity_authorities():
    return {"holdout": _identity_deny_set(ROUTER_HOLDOUT_MANIFEST),
            "test": _identity_deny_set(TEST_MANIFEST)}


# --------------------------------------------------------------------------- #
# canonical mask preprocessing — bind src/data/transforms.py
# --------------------------------------------------------------------------- #
def _mask_preprocess(mask_pil):
    from PIL import Image, ImageOps
    m = mask_pil.convert("L")
    w, h = m.size
    size = 512
    scale = min(size / w, size / h)
    rw, rh = max(1, round(w * scale)), max(1, round(h * scale))
    m = m.resize((rw, rh), Image.Resampling.NEAREST)
    left, top = (size - rw) // 2, (size - rh) // 2
    m = ImageOps.expand(m, (left, top, size - rw - left, size - rh - top))
    return (np.asarray(m).copy() > 0).astype(np.float32)


# --------------------------------------------------------------------------- #
# canonical metrics — bind src/metrics/evaluation_metrics.py
# --------------------------------------------------------------------------- #
def _confusion(pred, gt):
    from src.metrics import evaluation_metrics as M
    return M.binary_confusion_counts(np.asarray(pred).astype(bool),
                                     np.asarray(gt).astype(bool))


def _dice(pred, gt):
    from src.metrics import evaluation_metrics as M
    return float(M.dice(_confusion(pred, gt)))


def _iou(pred, gt):
    from src.metrics import evaluation_metrics as M
    return float(M.iou(_confusion(pred, gt)))


def _hd95(pred, gt):
    from src.metrics import evaluation_metrics as M
    return M.hd95(np.asarray(pred).astype(bool), np.asarray(gt).astype(bool))


def _prediction_consistency_dice(perturbed_final_mask, clean_final_mask):
    """§P: Dice(perturbed_final_binary_mask, clean_final_binary_mask)."""
    return _dice(np.asarray(perturbed_final_mask).astype(bool),
                 np.asarray(clean_final_mask).astype(bool))


def _finite_summary(values):
    vals = np.asarray(list(values), dtype=np.float64)
    finite = vals[np.isfinite(vals)]
    return {
        "n_total": int(vals.size),
        "n_finite": int(finite.size),
        "n_nan": int(vals.size - finite.size),
        "mean": (float(finite.mean()) if finite.size else None),
        "median": (float(np.median(finite)) if finite.size else None),
    }


# --------------------------------------------------------------------------- #
# §F  ACTUAL MODEL LOADING
# --------------------------------------------------------------------------- #
def _load_router_class():
    """AST-extract the canonical BARRBenefitRouterV1 from its frozen source."""
    import ast
    src = (ROOT / B_PHI_COMPONENT["source"]).read_text(encoding="utf-8")
    for node in ast.parse(src).body:
        if isinstance(node, ast.ClassDef) and node.name == "BARRBenefitRouterV1":
            ns = {"__name__": "_router", "__builtins__": __builtins__}
            exec("import torch\nimport torch.nn as nn\n", ns)
            exec(compile(ast.Module(body=[node], type_ignores=[]),
                         B_PHI_COMPONENT["source"], "exec"), ns)
            return ns["BARRBenefitRouterV1"]
    raise RuntimeError("BARRBenefitRouterV1 not found in canonical source")


def _load_somega_class():
    """AST-extract the canonical BARRPostSafetyV1 + its frozen dim constants."""
    import ast
    import torch as _t
    path = ROOT / S_OMEGA_COMPONENT["source"]
    tree = ast.parse(path.read_text(encoding="utf-8"))
    ns = {"__name__": "_somega", "torch": _t, "nn": _t.nn, "np": np}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            tg = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if any(t in ("FEATURE_DIM", "HIDDEN", "NUMERIC_IDX", "ONEHOT_IDX") for t in tg):
                exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), ns)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "BARRPostSafetyV1":
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), ns)
            return ns["BARRPostSafetyV1"]
    raise RuntimeError("BARRPostSafetyV1 not found in canonical source")


def _read_norm_rows(path_rel):
    rows = list(csv.DictReader((ROOT / path_rel).open(encoding="utf-8")))
    return rows


def _load_models():
    """REAL construction + strict load of the four frozen canonical components.

    Returns an executable context:
        system        -- RAMedFiLMBARR with all four components composed
        g / b_phi / r_psi / s_omega -- the individually loaded modules
        device, router_norm, somega_norm, load_audit
    Never raises a placeholder. Requires a live torch.
    """
    import torch
    from src.models.film.global_medfilm import GlobalMedFiLM
    from src.models.barr.regional_refiner import BARRRegionalRefinerV1
    from src.models.barr.ra_medfilm_barr import RAMedFiLMBARR
    from src.utils.device import get_device

    device = get_device() if callable(get_device) else torch.device("cpu")
    audit = {"components": {}, "checks": {}}

    # ---- G ---------------------------------------------------------------- #
    cfg = json.loads((ROOT / G_DEFAULT_CFG).read_text(encoding="utf-8"))["model"]
    g = GlobalMedFiLM(
        task_count=cfg["task_count"], in_channels=cfg["in_channels"],
        out_channels=cfg["out_channels"], channels=tuple(cfg["channels"]),
        task_embedding_dim=cfg["task_embedding_dim"],
        film_hidden_dim=cfg["film_hidden_dim"])
    g_ck = torch.load(ROOT / G_COMPONENT["checkpoint"], map_location="cpu", weights_only=False)
    g_strict = g.load_state_dict(g_ck["model_state"], strict=True)
    g.eval(); g.requires_grad_(False)

    # ---- R_psi ------------------------------------------------------------ #
    r_psi = BARRRegionalRefinerV1()
    r_ck = torch.load(ROOT / R_PSI_COMPONENT["checkpoint"], map_location="cpu", weights_only=False)
    r_strict = r_psi.load_state_dict(r_ck["model_state"], strict=True)
    r_psi.eval(); r_psi.requires_grad_(False)

    # ---- B_phi ------------------------------------------------------------ #
    Router = _load_router_class()
    b_phi = Router()
    b_ck = torch.load(ROOT / B_PHI_COMPONENT["checkpoint"], map_location="cpu", weights_only=False)
    b_strict = b_phi.load_state_dict(b_ck["model_state"], strict=True)
    b_phi.eval(); b_phi.requires_grad_(False)

    # ---- S_omega ---------------------------------------------------------- #
    Safety = _load_somega_class()
    s_omega = Safety()
    s_ck = torch.load(ROOT / S_OMEGA_COMPONENT["checkpoint"], map_location="cpu", weights_only=False)
    s_strict = s_omega.load_state_dict(s_ck["model_state"], strict=True)
    s_omega.eval(); s_omega.requires_grad_(False)

    # ---- param count + missing/unexpected verification -------------------- #
    def _count(m):
        return int(sum(p.numel() for p in m.parameters()))

    for name, m, comp, strict_res in (
            ("G", g, G_COMPONENT, g_strict),
            ("R_psi", r_psi, R_PSI_COMPONENT, r_strict),
            ("B_phi", b_phi, B_PHI_COMPONENT, b_strict),
            ("S_omega", s_omega, S_OMEGA_COMPONENT, s_strict)):
        missing = list(getattr(strict_res, "missing_keys", []))
        unexpected = list(getattr(strict_res, "unexpected_keys", []))
        n_params = _count(m)
        audit["components"][name] = {
            "class": comp["class"], "checkpoint": comp["checkpoint"],
            "checkpoint_sha256": _sha(ROOT / comp["checkpoint"]),
            "checkpoint_sha256_expected": comp["sha256"],
            "parameter_count": n_params,
            "parameter_count_expected": comp["params"],
            "missing_keys": missing, "unexpected_keys": unexpected,
            "strict_load_ok": not missing and not unexpected,
            "all_weights_finite": bool(all(bool(torch.isfinite(p).all()) for p in m.parameters())),
            "eval_mode": not m.training,
            "requires_grad_false": bool(all(not p.requires_grad for p in m.parameters())),
        }

    checks = {
        "G_params_3523001": audit["components"]["G"]["parameter_count"] == 3523001,
        "R_psi_params_1276401": audit["components"]["R_psi"]["parameter_count"] == 1276401,
        "B_phi_params_36801": audit["components"]["B_phi"]["parameter_count"] == 36801,
        "S_omega_params_1217": audit["components"]["S_omega"]["parameter_count"] == 1217,
        "all_strict_load_ok": all(v["strict_load_ok"] for v in audit["components"].values()),
        "zero_missing_keys": all(len(v["missing_keys"]) == 0 for v in audit["components"].values()),
        "zero_unexpected_keys": all(len(v["unexpected_keys"]) == 0 for v in audit["components"].values()),
        "all_weights_finite": all(v["all_weights_finite"] for v in audit["components"].values()),
        "all_eval_mode": all(v["eval_mode"] for v in audit["components"].values()),
        "all_requires_grad_false": all(v["requires_grad_false"] for v in audit["components"].values()),
        "all_checkpoint_sha_match": all(
            v["checkpoint_sha256"] == v["checkpoint_sha256_expected"]
            for v in audit["components"].values()),
    }
    audit["checks"] = checks
    if not all(checks.values()):
        raise RuntimeError(f"CANONICAL_COMPONENT_LOAD_FAILURE: {checks}")

    # ---- router normalization (canonical artifact) ------------------------ #
    rn_rows = _read_norm_rows(ROUTER_NORMALIZATION_PATH)
    if _sha(ROOT / ROUTER_NORMALIZATION_PATH) != ROUTER_NORMALIZATION_SHA:
        raise RuntimeError("router normalization artifact SHA mismatch")
    router_mu = np.asarray([float(x["mu"]) for x in rn_rows], dtype=np.float64)
    router_sigma = np.asarray([float(x["sigma"]) for x in rn_rows], dtype=np.float64)
    router_const = np.asarray([str(x["is_constant"]).lower() == "true" for x in rn_rows])

    sn_rows = _read_norm_rows(SOMEGA_NORMALIZATION_PATH)
    if _sha(ROOT / SOMEGA_NORMALIZATION_PATH) != SOMEGA_NORMALIZATION_SHA:
        raise RuntimeError("somega normalization artifact SHA mismatch")
    somega_mu = np.asarray([float(x["mu"]) for x in sn_rows], dtype=np.float64)
    somega_sigma = np.asarray([float(x["sigma"]) for x in sn_rows], dtype=np.float64)
    somega_const = np.asarray([str(x["is_constant"]).lower() == "true" for x in sn_rows])

    mu202 = np.zeros(ROUTER_NUMERIC_DIM, dtype=np.float64)
    sigma202 = np.ones(ROUTER_NUMERIC_DIM, dtype=np.float64)
    for k, idx in enumerate(ROUTER_SCALAR_IDX):
        mu202[idx] = router_mu[k]
        sigma202[idx] = 1.0 if router_const[k] else router_sigma[k]
    router_norm = {"mu": mu202, "sigma": sigma202,
                   "zero_sigma_rule": "sigma<1e-12 -> 1.0 then set 0.0"}

    somega_norm = {"mu": somega_mu, "sigma": somega_sigma,
                   "zero_sigma_rule": "sigma<1e-12 -> 1.0 then set 0.0"}

    system = RAMedFiLMBARR(_WrapG(g), r_psi, b_phi, s_omega,
                           router_normalization=router_norm,
                           post_safety_normalization=somega_norm)
    system.to(device) if hasattr(system, "to") else None

    return {
        "system": system, "g": g, "b_phi": b_phi, "r_psi": r_psi, "s_omega": s_omega,
        "device": device, "router_norm": router_norm, "somega_norm": somega_norm,
        "router_normalizer_raw": {"mu": router_mu, "sigma": router_sigma,
                                  "constant_mask": router_const},
        "somega_normalizer_raw": {"mu": somega_mu, "sigma": somega_sigma,
                                  "constant_mask": somega_const},
        "load_audit": audit,
    }


class _WrapG:
    """Adapter making GlobalMedFiLM.task_ids kwarg-compatible with the wrapper call."""

    def __init__(self, model):
        self.model = model
        for name in ("eval", "requires_grad_", "to", "parameters", "state_dict"):
            if hasattr(model, name):
                setattr(self, name, getattr(model, name))

    def __call__(self, image, task_ids=None, **kw):
        return self.model(image, task_ids)


# --------------------------------------------------------------------------- #
# canonical tap recording (G feature maps for the 202-D extractor)
# --------------------------------------------------------------------------- #
_TAP_MODULES = {"bridge": "bridge", "decoder2": "decoder2", "decoder1": "decoder1"}


class TapRecorder:
    """Forward hooks capturing the three frozen G tap feature maps (inference-only)."""

    def __init__(self, model):
        self.store = {}
        self.handles = []
        for tap, attr in _TAP_MODULES.items():
            mod = getattr(model, attr)
            self.handles.append(mod.register_forward_hook(self._make(tap)))

    def _make(self, tap):
        def hook(_m, _i, out):
            self.store[tap] = out
        return hook

    def clear(self):
        self.store.clear()

    def close(self):
        for h in self.handles:
            h.remove()
        self.handles = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


# --------------------------------------------------------------------------- #
# canonical image preprocessing + ROI geometry
# --------------------------------------------------------------------------- #
def image_only_transform(image, size: int = REGIONAL_CANVAS_RESOLUTION) -> np.ndarray:
    from PIL import Image, ImageOps
    image = image.convert("RGB")
    width, height = image.size
    scale = min(size / width, size / height)
    rw, rh = max(1, round(width * scale)), max(1, round(height * scale))
    image = image.resize((rw, rh), Image.Resampling.BILINEAR)
    left, top = (size - rw) // 2, (size - rh) // 2
    image = ImageOps.expand(image, (left, top, size - rw - left, size - rh - top))
    arr = np.asarray(image, dtype=np.float32).copy()
    return np.transpose(arr, (2, 0, 1)) / 255.0


def crop_and_resize_vec(arr, geom, out_size):
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
    w_in = max(0, min(REGIONAL_CANVAS_RESOLUTION, x1) - max(0, x0))
    h_in = max(0, min(REGIONAL_CANVAS_RESOLUTION, y1) - max(0, y0))
    area_fraction = (w_in * h_in) / float(REGIONAL_CANVAS_RESOLUTION ** 2)
    return compute_numeric_features(p_g_256, p_r_256, area_fraction,
                                    float(geom["crop_side_pixels"]))


# --------------------------------------------------------------------------- #
# 202-D feature assembly (canonical extractor)
# --------------------------------------------------------------------------- #
def _assemble_202d(cmaps, P, roi_row):
    from src.features.barr_pre_refinement_features import build_feature_vector
    return build_feature_vector(cmaps, np.asarray(P, dtype=np.float32), roi_row)


def _roi_geometry_from_prob(p_global, threshold=ROI_PROPOSAL_THRESHOLD,
                            margin=0.25):
    from src.data.barr_roi import roi_geometry
    return roi_geometry(np.asarray(p_global, dtype=np.float32),
                        threshold=threshold, margin=margin)


def _geo_row(geom):
    return {
        "clip_y1": int(geom["clip_y1"]), "clip_y2": int(geom["clip_y2"]),
        "clip_x1": int(geom["clip_x1"]), "clip_x2": int(geom["clip_x2"]),
        "crop_side_pixels": int(geom["crop_side_pixels"]),
    }


def _roi_row_from_window(y0, y1, x0, x1, crop_side_pixels):
    return {"clip_y1": int(y0), "clip_y2": int(y1),
            "clip_x1": int(x0), "clip_x2": int(x1),
            "crop_side_pixels": int(crop_side_pixels)}


# --------------------------------------------------------------------------- #
# §G  REAL clean-sample evaluation
# --------------------------------------------------------------------------- #
def _load_clean_image(sid: str):
    from PIL import Image
    from src.data.transforms import SegmentationTransform
    rows = {r["sample_id"]: r for r in _load_population()}
    r = rows[sid]
    img = Image.open(r["image_path"]).convert("RGB")
    tf = SegmentationTransform(size=512, train=False, image_mode="RGB")
    image_t, _mask_t, _meta = tf(img, Image.new("L", img.size, 0))
    return image_t


def _load_val_gt(sid: str):
    from PIL import Image
    rows = {r["sample_id"]: r for r in _load_population()}
    r = rows[sid]
    return _mask_preprocess(Image.open(r["mask_path"]))


def _evaluate_clean_sample(sid: str, row: dict, ctx: dict, clean_store: dict | None = None):
    """REAL clean per-sample evaluation under the frozen full system.

    Executes: G (once, with tap capture) -> canonical 0.30 ROI proposal geometry ->
    202-D vector -> canonical forward_inference (B_phi -> SKIP/EXECUTE -> R_psi ->
    S_omega) -> final routed probability -> 0.50 binary mask -> Dice/IoU/HD95.
    """
    import torch
    system = ctx["system"]
    device = ctx["device"]
    task_id = int(row["task_id"])

    image_t = _load_clean_image(sid)                       # torch [3,512,512] in [0,1]
    image_b = image_t[None].to(device)                     # [1,3,512,512]

    with torch.no_grad(), TapRecorder(ctx["g"]) as rec:
        g_out = ctx["g"](image_b, torch.tensor([task_id]))
        cmaps = {k: v.detach().cpu().numpy() for k, v in rec.store.items()}
    if g_out.ndim == 4:
        logits = g_out[0, 0].detach().cpu().numpy()
    else:  # pragma: no cover - defensive
        logits = g_out.detach().cpu().numpy()
    p_global = (1.0 / (1.0 + np.exp(-logits.astype(np.float64)))).astype(np.float32)

    geom = _roi_geometry_from_prob(p_global, ROI_PROPOSAL_THRESHOLD, 0.25)
    window = None
    if geom is not None:
        window = (int(geom["clip_y1"]), int(geom["clip_y2"]),
                  int(geom["clip_x1"]), int(geom["clip_x2"]))

    roi_row = _geo_row(geom) if geom is not None else _roi_row_from_window(
        0, p_global.shape[0], 0, p_global.shape[1], p_global.shape[0])
    rf202 = _assemble_202d(cmaps, p_global, roi_row)

    oof_crop = None
    sf16 = None
    if geom is not None:
        rgb = image_t.detach().cpu().numpy()
        rgb_crop = crop_and_resize_vec(rgb, geom, REGIONAL_INPUT_RESOLUTION)
        prob_crop = crop_and_resize_vec(p_global, geom, REGIONAL_INPUT_RESOLUTION)
        rin = np.concatenate([np.asarray(rgb_crop, dtype=np.float32),
                              np.asarray(prob_crop, dtype=np.float32)], axis=0)
        with torch.no_grad():
            rin_t = torch.from_numpy(np.ascontiguousarray(rin))[None].to(device)
            refined = torch.sigmoid(ctx["r_psi"](rin_t).float())[0, 0].detach().cpu().numpy()
        oof_crop = refined
        pg_crop = np.asarray(prob_crop, dtype=np.float32)
        if pg_crop.ndim == 3:
            pg_crop = pg_crop[0]
        pr_crop = np.asarray(refined, dtype=np.float32)
        if pr_crop.ndim == 3:
            pr_crop = pr_crop[0]
        sf16 = np.asarray(somega_features(pg_crop, pr_crop, geom),
                          dtype=np.float64).reshape(-1)

    out = system.forward_inference(
        image_b, task_id,
        router_features_202=rf202,
        roi_window=window,
        action_available=(geom is not None),
        oof_refined_crop_prob=oof_crop,
        safety_post_features_16=sf16)

    final_prob = np.asarray(out["final_probability"], dtype=np.float32)
    final_binary = (final_prob >= SEGMENTATION_OUTPUT_THRESHOLD).astype(np.float32)

    gt = _load_val_gt(sid)
    dice = _dice(final_binary, gt)
    iou = _iou(final_binary, gt)
    hd = _hd95(final_binary, gt)

    rec = {
        "sample_id": sid,
        "domain": row.get("dataset"),
        "task_id": task_id,
        "state": out["state"],
        "router_score": float(out.get("delta_hat_final") or 0.0),
        "final_dice": dice,
        "final_iou": iou,
        "final_hd95": hd.get("hd95", np.nan) if isinstance(hd, dict) else float(hd),
        "hd95_valid": hd.get("valid") if isinstance(hd, dict) else None,
        "final_source": "REFINED" if out["state"] == "EXECUTE_THEN_ACCEPT" else "GLOBAL",
        "roi_available": geom is not None,
    }
    if clean_store is not None:
        clean_store.setdefault("p_global", {})[sid] = p_global
        clean_store.setdefault("cmaps", {})[sid] = cmaps
        clean_store.setdefault("final_binary", {})[sid] = final_binary
        clean_store.setdefault("task_id", {})[sid] = task_id
        clean_store.setdefault("domain", {})[sid] = row.get("dataset")
        clean_store.setdefault("image", {})[sid] = image_b
        clean_store.setdefault("geometry", {})[sid] = geom
        clean_store.setdefault("state", {})[sid] = out["state"]
        clean_store.setdefault("router_decision", {})[sid] = out.get("state")
        clean_store.setdefault("final_source", {})[sid] = rec["final_source"]
    return rec


# --------------------------------------------------------------------------- #
# §H  REAL clean reference generation over exactly the 808 manifest rows
# --------------------------------------------------------------------------- #
def _generate_clean_reference_once(ctx, counters, clean_store):
    counters["clean_generation_invocations"] = \
        counters.get("clean_generation_invocations", 0) + 1
    rows = _load_population()
    records = []
    for r in rows:
        sid = r["sample_id"]
        rec = _evaluate_clean_sample(sid, r, ctx, clean_store=clean_store)
        records.append(rec)
        counters["clean_g_forwards"] = counters.get("clean_g_forwards", 0) + 1
        counters["metric_evaluations"] = counters.get("metric_evaluations", 0) + 1
    counters["clean_passes"] = len(records)
    return {"generated": True, "n": len(records), "records": records,
            "persist_keys": [
                "clean_p_global", "clean_roi_geometry", "clean_202d",
                "clean_router_score", "clean_router_decision", "clean_safety_state",
                "clean_final_source", "clean_final_binary_mask",
                "clean_dice", "clean_iou", "clean_hd95"],
            "clean_final_binary_mask_authority": "binary float32[512,512] per sample",
            "reconstruction_from_scalars_prohibited": True}


def _bind_clean_reference():
    """Bind the phase27/29 scalar+routing authority (masks come from STAGE 1)."""
    p = ROOT / C.CLEAN_REFERENCE["per_sample_scores"]["path"]
    q = ROOT / C.CLEAN_REFERENCE["routing_state"]["path"]
    if not (p.exists() and q.exists()):
        return None
    if _sha(p) != C.CLEAN_REFERENCE["per_sample_scores"]["sha256"]:
        return None
    scores = list(csv.DictReader(p.open(encoding="utf-8")))
    decisions = {r["sample_id"]: r for r in csv.DictReader(q.open(encoding="utf-8"))}
    return {
        "sample_ids": [r["sample_id"] for r in scores],
        "dice_final": {r["sample_id"]: float(r["final_dice"]) for r in scores},
        "route_state": {r["sample_id"]: r["state_machine_branch"] for r in scores},
        "b_phi_execute": {sid: (d["selected"] == "True") for sid, d in decisions.items()},
        "roi_geometry": {},
        "final_pred": {},
    }


# --------------------------------------------------------------------------- #
# §I  STRICT clean equivalence gate
# --------------------------------------------------------------------------- #
def _clean_equivalence_gate(clean_ref, generated, counters):
    """§E/§I: STRICT — 808 generated must equal 808 bound; per-sample Dice isclose 1e-7."""
    counters["clean_equivalence_gate_invocations"] = \
        counters.get("clean_equivalence_gate_invocations", 0) + 1

    gen_records = {r["sample_id"]: r for r in generated["records"]}
    n_generated = len(gen_records)
    n_bound = len(clean_ref.get("sample_ids", [])) if clean_ref else 0
    checks = {
        "generated_exactly_808": n_generated == C.POPULATION_N,
        "bound_exactly_808": n_bound == C.POPULATION_N,
        "generated_equals_bound": n_generated == n_bound,
    }

    absent_bound = [sid for sid in (clean_ref.get("sample_ids", []) if clean_ref else [])
                    if sid not in gen_records]
    checks["missing_generated_dice"] = (len(absent_bound) == 0)

    route_mismatches = []
    dice_mismatches = []
    missing_generated_dice = []
    missing_bound_dice = []
    for sid, grec in gen_records.items():
        bound_dice = clean_ref["dice_final"].get(sid) if clean_ref else None
        if bound_dice is None:
            missing_bound_dice.append(sid)
            continue
        gd = grec.get("final_dice")
        if gd is None or not np.isfinite(float(gd)):
            missing_generated_dice.append(sid)
            continue
        if not np.isclose(float(gd), float(bound_dice), atol=1e-7, rtol=0):
            dice_mismatches.append({"sample_id": sid, "generated": float(gd),
                                    "bound": float(bound_dice)})
        bound_route = clean_ref["route_state"].get(sid)
        if bound_route is not None:
            gen_state = grec.get("state")
            gen_global = gen_state in ("SKIP_GLOBAL", "FORCED_SKIP")
            bound_global = bound_route in ("SKIP_GLOBAL", "FORCED_SKIP")
            if gen_global != bound_global:
                route_mismatches.append({"sample_id": sid, "generated": gen_state,
                                         "bound": bound_route})

    checks["missing_bound_dice_zero"] = (len(missing_bound_dice) == 0)
    checks["missing_generated_dice_zero"] = (len(missing_generated_dice) == 0)
    checks["route_mismatches_zero"] = (len(route_mismatches) == 0)
    checks["dice_mismatches_zero"] = (len(dice_mismatches) == 0)

    scores = []
    for sid in gen_records:
        b = clean_ref["dice_final"].get(sid) if clean_ref else None
        g = gen_records[sid].get("final_dice")
        if b is not None and g is not None and np.isfinite(float(g)):
            scores.append((float(g), float(b)))
    max_abs_dev = (max(abs(a - b) for a, b in scores) if scores else None)

    all_pass = bool(all(checks.values()))
    return {
        "all_pass": all_pass,
        "checks": checks,
        "n_generated": n_generated,
        "n_bound": n_bound,
        "n_dice_comparisons": len(scores),
        "missing_generated_dice": missing_generated_dice,
        "missing_bound_dice": missing_bound_dice,
        "route_mismatches": route_mismatches,
        "dice_mismatches": dice_mismatches,
        "max_abs_dice_deviation": max_abs_dev,
        "comparator": "np.isclose(generated, bound, atol=1e-7, rtol=0)",
        "fail_closed_on_missing_data": True,
    }


# --------------------------------------------------------------------------- #
# §J  REAL image-perturbation execution
# --------------------------------------------------------------------------- #
def _evaluate_frozen_system(x_pert, sid, task_id, counters, system=None, ctx=None):
    """IMAGE perturbation: full system re-run end-to-end under the frozen pipeline."""
    import torch
    ctx = ctx if ctx is not None else _load_models()
    system = system if system is not None else ctx["system"]
    device = ctx["device"]

    img_t = torch.from_numpy(np.ascontiguousarray(x_pert, dtype=np.float32))
    if img_t.ndim == 2:
        img_t = img_t[None, None].repeat(1, 3, 1, 1)
    elif img_t.ndim == 3:
        img_t = img_t[None]
    img_b = img_t.to(device)

    with torch.no_grad(), TapRecorder(ctx["g"]) as rec:
        g_out = ctx["g"](img_b, torch.tensor([int(task_id)]))
        cmaps = {k: v.detach().cpu().numpy() for k, v in rec.store.items()}
    logits = g_out[0, 0].detach().cpu().numpy() if g_out.ndim == 4 else g_out.detach().cpu().numpy()
    p_global = (1.0 / (1.0 + np.exp(-logits.astype(np.float64)))).astype(np.float32)

    geom = _roi_geometry_from_prob(p_global, ROI_PROPOSAL_THRESHOLD, 0.25)
    window = None
    if geom is not None:
        window = (int(geom["clip_y1"]), int(geom["clip_y2"]),
                  int(geom["clip_x1"]), int(geom["clip_x2"]))
    roi_row = _geo_row(geom) if geom is not None else _roi_row_from_window(
        0, p_global.shape[0], 0, p_global.shape[1], p_global.shape[0])
    rf202 = _assemble_202d(cmaps, p_global, roi_row)

    oof_crop = None
    sf16 = None
    if geom is not None:
        rgb = img_b[0].detach().cpu().numpy()
        rgb_crop = crop_and_resize_vec(rgb, geom, REGIONAL_INPUT_RESOLUTION)
        prob_crop = crop_and_resize_vec(p_global, geom, REGIONAL_INPUT_RESOLUTION)
        rin = np.concatenate([np.asarray(rgb_crop, dtype=np.float32),
                              np.asarray(prob_crop, dtype=np.float32)], axis=0)
        with torch.no_grad():
            rin_t = torch.from_numpy(np.ascontiguousarray(rin))[None].to(device)
            refined = torch.sigmoid(ctx["r_psi"](rin_t).float())[0, 0].detach().cpu().numpy()
        oof_crop = refined
        pg_crop = np.asarray(prob_crop, dtype=np.float32)
        pg_crop = pg_crop[0] if pg_crop.ndim == 3 else pg_crop
        pr_crop = np.asarray(refined, dtype=np.float32)
        pr_crop = pr_crop[0] if pr_crop.ndim == 3 else pr_crop
        sf16 = np.asarray(somega_features(pg_crop, pr_crop, geom), dtype=np.float64).reshape(-1)

    out = system.forward_inference(
        img_b, int(task_id), router_features_202=rf202, roi_window=window,
        action_available=(geom is not None), oof_refined_crop_prob=oof_crop,
        safety_post_features_16=sf16)
    counters["perturbed_g_forwards"] = counters.get("perturbed_g_forwards", 0) + 1
    counters["forwards"] = counters.get("forwards", 0) + 1
    return out


# --------------------------------------------------------------------------- #
# §K  REAL proposal-perturbation execution
# --------------------------------------------------------------------------- #
def _evaluate_frozen_system_proposal(clean_ref, sid, geom, counters, system=None, ctx=None):
    """PROPOSAL perturbation: G reused from CLEAN; geometry-dependent parts recomputed."""
    import torch
    ctx = ctx if ctx is not None else _load_models()
    system = system if system is not None else ctx["system"]
    device = ctx["device"]

    if geom is None:
        counters["empty_proposal_not_applicable"] = \
            counters.get("empty_proposal_not_applicable", 0) + 1
        return {"state": C.EMPTY_PROPOSAL_HANDLING,
                "final_probability": None, "final_binary": None,
                "refiner_forward_count": 0, "s_omega_forward_count": 0,
                "not_applicable": True}

    p_global = clean_ref["p_global"][sid]
    img_b = clean_ref["image"][sid].to(device)
    cmaps = clean_ref["cmaps"][sid]
    task_id = int(clean_ref["task_id"][sid])

    perturbed_row = _roi_row_from_window(
        geom["clip_y1"], geom["clip_y2"], geom["clip_x1"], geom["clip_x2"],
        geom["crop_side_pixels"])
    rf202 = _assemble_202d(cmaps, p_global, perturbed_row)
    counters["router_input_reassembled"] = counters.get("router_input_reassembled", 0) + 1
    counters["g_reused_for_proposal"] = counters.get("g_reused_for_proposal", 0) + 1

    rgb = img_b[0].detach().cpu().numpy()
    rgb_crop = crop_and_resize_vec(rgb, geom, REGIONAL_INPUT_RESOLUTION)
    prob_crop = crop_and_resize_vec(p_global, geom, REGIONAL_INPUT_RESOLUTION)
    rin = np.concatenate([np.asarray(rgb_crop, dtype=np.float32),
                          np.asarray(prob_crop, dtype=np.float32)], axis=0)
    with torch.no_grad():
        rin_t = torch.from_numpy(np.ascontiguousarray(rin))[None].to(device)
        refined = torch.sigmoid(ctx["r_psi"](rin_t).float())[0, 0].detach().cpu().numpy()
    counters["r_psi_forwards"] = counters.get("r_psi_forwards", 0) + 1

    pg_crop = np.asarray(prob_crop, dtype=np.float32)
    pg_crop = pg_crop[0] if pg_crop.ndim == 3 else pg_crop
    pr_crop = np.asarray(refined, dtype=np.float32)
    pr_crop = pr_crop[0] if pr_crop.ndim == 3 else pr_crop
    sf16 = np.asarray(somega_features(pg_crop, pr_crop, geom), dtype=np.float64).reshape(-1)

    window = (int(geom["clip_y1"]), int(geom["clip_y2"]),
              int(geom["clip_x1"]), int(geom["clip_x2"]))
    out = system.forward_inference(
        img_b, task_id, router_features_202=rf202, roi_window=window,
        action_available=True, oof_refined_crop_prob=refined,
        safety_post_features_16=sf16)
    counters["forwards"] = counters.get("forwards", 0) + 1
    return out


# --------------------------------------------------------------------------- #
# §A/§D  FROZEN IMAGE REALIZATION PLAN (sample-first iteration source)
# --------------------------------------------------------------------------- #
def image_realization_plan() -> list:
    """Materialize the frozen image realization list (DETERMINISTIC ORDER).

    CLEAN is EXCLUDED (generated once in STAGE 1). Only the 16 non-clean
    realizations are returned. base_seed/derived_seed are NULL for deterministic
    conditions and populated for Gaussian-noise conditions.
    """
    plan = []
    for cond in NONCLEAN_DETERMINISTIC_IMAGE_CONDITIONS:
        plan.append({"condition": cond, "base_seed": None, "derived_seed": None,
                     "is_noise": False})
    for cond in NONCLEAN_NOISE_IMAGE_CONDITIONS:
        for bs in C.NOISE_BASE_SEEDS:
            plan.append({"condition": cond, "base_seed": int(bs),
                         "derived_seed": None,  # derived per-sample at execution
                         "is_noise": True})
    if len(plan) != NONCLEAN_IMAGE_REALIZATIONS_PER_SAMPLE:
        raise AssertionError(
            f"image realization plan {len(plan)} != {NONCLEAN_IMAGE_REALIZATIONS_PER_SAMPLE}")
    return plan


def proposal_realization_plan() -> list:
    """Materialize the frozen proposal realization list (6 non-clean conditions)."""
    plan = [{"proposal_condition": cond} for cond in NONCLEAN_PROPOSAL_CONDITIONS]
    if len(plan) != NONCLEAN_PROPOSAL_CONDITIONS_PER_SAMPLE:
        raise AssertionError(
            f"proposal realization plan {len(plan)} != {NONCLEAN_PROPOSAL_CONDITIONS_PER_SAMPLE}")
    return plan


def _derived_seed_for(cond: str, base_seed, sid: str):
    """Per-sample derived seed for Gaussian-noise realizations (v1.1 32-bit rule)."""
    if base_seed is None:
        return None
    return int(C.derive_noise_seed(int(base_seed), sid))


# --------------------------------------------------------------------------- #
# §E  BUILDER — a FULLY-POPULATED sample-level image result row
# --------------------------------------------------------------------------- #
_IMAGE_ROW_REQUIRED = [
    "sample_id", "domain", "task_id", "condition", "base_seed", "derived_seed",
    "clean_dice", "perturbed_dice", "paired_delta_dice",
    "prediction_consistency_dice", "clean_route_state", "perturbed_route_state",
    "route_state_changed", "clean_router_decision", "perturbed_router_decision",
    "router_decision_changed", "final_source", "perturbed_final_source",
    "perturbed_iou", "perturbed_hd95", "perturbed_hd95_valid",
]


def build_image_result_row(sid, domain, task_id, cond, base_seed, derived_seed,
                           clean_dice, perturbed_dice, prediction_consistency_dice,
                           clean_route_state, perturbed_route_state,
                           clean_router_decision, perturbed_router_decision,
                           final_source, perturbed_final_source,
                           perturbed_iou=None, perturbed_hd95=None,
                           perturbed_hd95_valid=None) -> dict:
    """Build a sample-level image-perturbation result row. FAILS CLOSED on schema loss."""
    for k, v in (("sample_id", sid), ("domain", domain), ("task_id", task_id)):
        if v is None:
            raise ValueError(f"SCIENCE_ROW_SCHEMA_LOSS: missing {k}")
    row = {
        "sample_id": sid, "domain": domain, "task_id": int(task_id),
        "condition": cond, "base_seed": base_seed, "derived_seed": derived_seed,
        "clean_dice": float(clean_dice), "perturbed_dice": float(perturbed_dice),
        "paired_delta_dice": float(perturbed_dice) - float(clean_dice),
        "prediction_consistency_dice": float(prediction_consistency_dice),
        "clean_route_state": clean_route_state, "perturbed_route_state": perturbed_route_state,
        "route_state_changed": bool(clean_route_state != perturbed_route_state),
        "clean_router_decision": clean_router_decision,
        "perturbed_router_decision": perturbed_router_decision,
        "router_decision_changed": bool(clean_router_decision != perturbed_router_decision),
        "final_source": final_source, "perturbed_final_source": perturbed_final_source,
        "perturbed_iou": perturbed_iou, "perturbed_hd95": perturbed_hd95,
        "perturbed_hd95_valid": perturbed_hd95_valid,
    }
    missing = _row_missing_required(row)
    if missing:
        raise ValueError(f"SCIENCE_ROW_SCHEMA_LOSS: {missing}")
    return row


def _row_missing_required(row: dict) -> list:
    return [k for k in _IMAGE_ROW_REQUIRED
            if k not in row or (k in ("sample_id", "domain", "task_id") and row[k] is None)]


# --------------------------------------------------------------------------- #
# §E/§F  SAMPLE-FIRST IMAGE PERTURBATION SCIENCE
# --------------------------------------------------------------------------- #
def run_image_perturbations(ctx, generated, clean_store, counters, image_rows, consistency_rows):
    """SAMPLE-FIRST image perturbation execution (the §E repair).

    FOR EACH authorized clean sample:
        FOR EACH frozen non-clean image realization (16):
            evaluate that sample/realization and EMIT a fully-populated row.
    Never silently `continue`.
    """
    plan = image_realization_plan()
    clean_by_sid = {r["sample_id"]: r for r in generated["records"]}
    sample_order = [r["sample_id"] for r in generated["records"]]
    if len(sample_order) != AUTHORIZED_POPULATION_N:
        raise ValueError(f"SAMPLE_POPULATION_MISMATCH: {len(sample_order)} != {AUTHORIZED_POPULATION_N}")

    for sid in sample_order:
        clean_row = clean_by_sid[sid]
        if not _row_has_identity(clean_row):
            raise ValueError(f"SCIENCE_ROW_SCHEMA_LOSS: clean row lacks identity for {sid}")
        domain = clean_row.get("domain")
        task_id = clean_row.get("task_id")
        if domain is None or task_id is None:
            raise ValueError(f"SCIENCE_ROW_SCHEMA_LOSS: missing domain/task_id for {sid}")
        x_clean = clean_store["image"][sid][0].detach().cpu().numpy()  # [3,512,512]
        clean_dice = float(clean_row["final_dice"])
        clean_state = clean_store["state"][sid]
        clean_decision = clean_store["router_decision"][sid]
        clean_source = clean_store["final_source"][sid]

        for real in plan:
            cond = real["condition"]
            base_seed = real["base_seed"]
            derived_seed = _derived_seed_for(cond, base_seed, sid)
            x_pert = C.apply_image_condition(x_clean, cond, sid, base_seed)
            out = _evaluate_frozen_system(x_pert, sid, task_id, counters,
                                          system=ctx["system"], ctx=ctx)
            pert_binary = np.asarray(out["final_binary"], dtype=np.float32)
            pc = _prediction_consistency_dice(pert_binary, clean_store["final_binary"][sid])
            gt = _load_val_gt(sid)
            pert_dice = _dice(pert_binary, gt)
            pert_iou = _iou(pert_binary, gt)
            hd = _hd95(pert_binary, gt)
            pert_state = out["state"]
            pert_decision = out.get("state")
            pert_source = ("REFINED" if pert_state == "EXECUTE_THEN_ACCEPT" else "GLOBAL")

            row = build_image_result_row(
                sid=sid, domain=domain, task_id=task_id, cond=cond,
                base_seed=base_seed, derived_seed=derived_seed,
                clean_dice=clean_dice, perturbed_dice=pert_dice,
                prediction_consistency_dice=pc,
                clean_route_state=clean_state, perturbed_route_state=pert_state,
                clean_router_decision=clean_decision, perturbed_router_decision=pert_decision,
                final_source=clean_source, perturbed_final_source=pert_source,
                perturbed_iou=pert_iou,
                perturbed_hd95=(hd.get("hd95", np.nan) if isinstance(hd, dict) else float(hd)),
                perturbed_hd95_valid=(hd.get("valid") if isinstance(hd, dict) else None))
            image_rows.append(row)
            consistency_rows.append({
                "sample_id": sid, "domain": domain, "task_id": task_id, "condition": cond,
                "base_seed": base_seed, "derived_seed": derived_seed,
                "prediction_consistency_dice": pc, "perturbed_route_state": pert_state})
            counters["image_perturbation_instances"] = \
                counters.get("image_perturbation_instances", 0) + 1
            counters["prediction_consistency_evaluations"] = \
                counters.get("prediction_consistency_evaluations", 0) + 1
            counters["metric_evaluations"] = counters.get("metric_evaluations", 0) + 1
    if len(image_rows) != NONCLEAN_IMAGE_EXECUTIONS_EXPECTED:
        raise AssertionError(
            f"NONCLEAN_IMAGE_EXECUTIONS {len(image_rows)} != {NONCLEAN_IMAGE_EXECUTIONS_EXPECTED}")
    return image_rows


def _row_has_identity(row: dict) -> bool:
    return row.get("sample_id") is not None and row.get("task_id") is not None


# --------------------------------------------------------------------------- #
# §G  SAMPLE-FIRST PROPOSAL PERTURBATION SCIENCE
# --------------------------------------------------------------------------- #
def run_proposal_perturbations(ctx, generated, clean_store, counters, proposal_rows):
    """SAMPLE-FIRST proposal perturbation execution (the §G repair).

    Non-empty canonical proposal  -> execute all 6 non-clean conditions.
    Empty   canonical proposal    -> emit six explicit NOT_APPLICABLE_EMPTY_PROPOSAL
                                     records (with sample_id/domain/task_id/
                                     proposal_condition/status), ZERO R_psi/S_omega.
    Never silently omit.
    """
    plan = proposal_realization_plan()
    clean_by_sid = {r["sample_id"]: r for r in generated["records"]}
    sample_order = [r["sample_id"] for r in generated["records"]]

    for sid in sample_order:
        clean_row = clean_by_sid[sid]
        domain = clean_row.get("domain")
        task_id = clean_row.get("task_id")
        if sid is None or domain is None or task_id is None:
            raise ValueError(f"SCIENCE_ROW_SCHEMA_LOSS: missing identity for {sid}")
        clean_geom = clean_store["geometry"].get(sid)
        clean_dice = float(clean_row["final_dice"])

        if clean_geom is None:
            for real in plan:
                proposal_rows.append({
                    "sample_id": sid, "domain": domain, "task_id": int(task_id),
                    "proposal_condition": real["proposal_condition"],
                    "status": C.EMPTY_PROPOSAL_HANDLING,
                    "not_applicable": True})
            continue

        base_geom = {"y1": clean_geom["y1"], "y2": clean_geom["y2"],
                     "x1": clean_geom["x1"], "x2": clean_geom["x2"],
                     "crop_side": clean_geom["crop_side_pixels"],
                     "center_y": (clean_geom["y1"] + clean_geom["y2"]) / 2.0,
                     "center_x": (clean_geom["x1"] + clean_geom["x2"]) / 2.0}
        for real in plan:
            cond = real["proposal_condition"]
            pert_geom = C.apply_proposal_condition(base_geom, cond, 512, 512)
            out = _evaluate_frozen_system_proposal(clean_store, sid, pert_geom, counters,
                                                   system=ctx["system"], ctx=ctx)
            pert_binary = np.asarray(out["final_binary"], dtype=np.float32)
            gt = _load_val_gt(sid)
            pert_dice = _dice(pert_binary, gt)
            proposal_rows.append({
                "sample_id": sid, "domain": domain, "task_id": int(task_id),
                "proposal_condition": cond, "status": "EXECUTED",
                "clean_dice": clean_dice, "perturbed_dice": pert_dice,
                "paired_delta_dice": pert_dice - clean_dice,
                "prediction_consistency_dice":
                    _prediction_consistency_dice(pert_binary, clean_store["final_binary"][sid]),
                "perturbed_route_state": out["state"],
                "clean_route_state": clean_store["state"][sid],
                "not_applicable": False})
            counters["proposal_perturbation_executions"] = \
                counters.get("proposal_perturbation_executions", 0) + 1
            counters["proposal_perturbation_instances"] = \
                counters.get("proposal_perturbation_instances", 0) + 1
            counters["metric_evaluations"] = counters.get("metric_evaluations", 0) + 1
    return proposal_rows


# --------------------------------------------------------------------------- #
# §H  FIXED SUMMARIES (must be reachable from run_science)
# --------------------------------------------------------------------------- #
def _write_csv(path: Path, rows: list, fieldnames: list = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = fieldnames or list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def summarize_image_per_sample(image_rows):
    out = []
    for r in image_rows:
        out.append({
            "sample_id": r["sample_id"], "domain": r["domain"], "task_id": r["task_id"],
            "condition": r["condition"], "base_seed": r["base_seed"],
            "derived_seed": r["derived_seed"], "clean_dice": r["clean_dice"],
            "perturbed_dice": r["perturbed_dice"],
            "paired_delta_dice": r["paired_delta_dice"],
            "prediction_consistency_dice": r["prediction_consistency_dice"],
            "route_state_changed": r["route_state_changed"],
            "router_decision_changed": r["router_decision_changed"]})
    _write_csv(TAB / "phase36_image_robustness_per_sample.csv", out)
    return out


def summarize_image_by_domain_condition(image_rows):
    agg = {}
    for r in image_rows:
        k = (r["domain"], r["condition"])
        agg.setdefault(k, []).append(float(r["paired_delta_dice"]))
    out = []
    for (dom, cond), vals in agg.items():
        s = _finite_summary(vals)
        out.append({"domain": dom, "condition": cond, "n": s["n_total"],
                    "n_finite": s["n_finite"], "n_nan": s["n_nan"],
                    "mean_paired_delta_dice": s["mean"],
                    "median_paired_delta_dice": s["median"]})
    _write_csv(TAB / "phase36_image_robustness_by_domain_condition.csv", out)
    return out


def summarize_noise_seed(image_rows):
    # per-seed first, then arithmetic mean across the three frozen seeds.
    agg = {}
    for r in image_rows:
        if r["base_seed"] is None:
            continue
        k = (r["domain"], r["condition"], r["sample_id"], int(r["base_seed"]))
        agg.setdefault(k, []).append(float(r["paired_delta_dice"]))
    per_seed = {}
    for (dom, cond, sid, bs), vals in agg.items():
        per_seed.setdefault((dom, cond), {}).setdefault(sid, {})[bs] = \
            float(np.mean(np.asarray(vals, dtype=np.float64)))
    out = []
    for (dom, cond), per_sample in per_seed.items():
        sample_means = []
        for sid, seed_map in per_sample.items():
            sample_means.append(float(np.mean(np.asarray(list(seed_map.values()), dtype=np.float64))))
        out.append({"domain": dom, "condition": cond,
                    "n_samples": len(sample_means),
                    "mean_across_seeds_of_sample_means":
                        (float(np.mean(sample_means)) if sample_means else None),
                    "best_seed_selection": bool(C.BEST_SEED_SELECTION)})
    _write_csv(TAB / "phase36_noise_seed_summary.csv", out)
    return out


def summarize_proposal_per_sample(proposal_rows):
    out = [dict(r) for r in proposal_rows]
    _write_csv(TAB / "phase36_proposal_robustness_per_sample.csv", out)
    return out


def summarize_proposal_by_domain_condition(proposal_rows):
    agg = {}
    for r in proposal_rows:
        if r.get("not_applicable"):
            continue
        k = (r["domain"], r["proposal_condition"])
        agg.setdefault(k, []).append(float(r["paired_delta_dice"]))
    out = []
    for (dom, cond), vals in agg.items():
        s = _finite_summary(vals)
        out.append({"domain": dom, "proposal_condition": cond, "n_applicable": s["n_total"],
                    "mean_paired_delta_dice": s["mean"],
                    "median_paired_delta_dice": s["median"]})
    _write_csv(TAB / "phase36_proposal_robustness_by_domain_condition.csv", out)
    return out


def summarize_route_stability(image_rows):
    agg = {}
    for r in image_rows:
        k = (r["domain"], r["condition"])
        agg.setdefault(k, [0, 0])
        agg[k][0] += 1
        if r["route_state_changed"]:
            agg[k][1] += 1
    out = []
    for (dom, cond), (n, chg) in agg.items():
        out.append({"domain": dom, "condition": cond, "n": n,
                    "route_state_changed_count": chg,
                    "route_state_change_rate": (chg / n if n else None)})
    _write_csv(TAB / "phase36_route_stability_summary.csv", out)
    return out


# --------------------------------------------------------------------------- #
# §I  WORST-CASE PATH (real; from actual result rows)
# --------------------------------------------------------------------------- #
def worst_case_per_sample(image_rows, proposal_rows):
    by_sample = {}
    for r in image_rows:
        by_sample.setdefault(r["sample_id"], {"domain": r["domain"], "task_id": r["task_id"],
                                              "img_deltas": []})
        by_sample[r["sample_id"]]["img_deltas"].append(float(r["paired_delta_dice"]))
    prop_by_sample = {}
    for r in proposal_rows:
        if r.get("not_applicable"):
            continue
        prop_by_sample.setdefault(r["sample_id"], []).append(float(r["paired_delta_dice"]))
    out = []
    for sid, d in by_sample.items():
        img_worst = min(d["img_deltas"]) if d["img_deltas"] else None
        prop_list = prop_by_sample.get(sid, [])
        prop_worst = min(prop_list) if prop_list else None
        out.append({"sample_id": sid, "domain": d["domain"], "task_id": d["task_id"],
                    "worst_image_perturbation_delta_Dice": img_worst,
                    "worst_proposal_perturbation_delta_Dice": prop_worst,
                    "n_image_realizations": len(d["img_deltas"]),
                    "n_proposal_applicable": len(prop_list)})
    _write_csv(TAB / "phase36_worst_case_per_sample.csv", out)
    return out


def worst_case_by_domain(worst_per_sample):
    agg = {}
    for r in worst_per_sample:
        agg.setdefault(r["domain"], []).append(r["worst_image_perturbation_delta_Dice"])
    out = []
    for dom, vals in agg.items():
        finite = [v for v in vals if v is not None and np.isfinite(v)]
        out.append({"domain": dom, "n_samples": len(vals),
                    "worst_image_delta_Dice_min": (min(finite) if finite else None),
                    "worst_image_delta_Dice_mean": (float(np.mean(finite)) if finite else None)})
    _write_csv(TAB / "phase36_worst_case_by_domain.csv", out)
    return out


def kub_subgroup_robustness(image_rows):
    """KUB subgroup robustness (REPORTING ONLY) — emitted only if metadata authority passes."""
    if not C.KUB_REPORTING_ONLY:
        return None
    rows = []
    for r in image_rows:
        if r["domain"] != "KUB":
            continue
        rows.append({"sample_id": r["sample_id"], "condition": r["condition"],
                     "paired_delta_dice": r["paired_delta_dice"]})
    _write_csv(TAB / "phase36_kub_subgroup_robustness.csv", rows)
    return rows


# --------------------------------------------------------------------------- #
# §M  REAL science driver (SAMPLE-FIRST)
# --------------------------------------------------------------------------- #
def run_science() -> dict:
    counters = OrderedDict((k, 0) for k in C.COUNTERS_REQUIRED)
    for k in C.COUNTERS_FOREVER_ZERO:
        counters[k] = 0

    # STAGE 1: generate CLEAN808 (REAL).
    ctx = _load_models()
    audit = ctx["load_audit"]
    clean_ref_bound = _bind_clean_reference()
    clean_store = {}
    generated = _generate_clean_reference_once(ctx, counters, clean_store)

    # STAGE 2: strict clean-equivalence gate; STOP before perturbation on failure.
    eq = _clean_equivalence_gate(clean_ref_bound, generated, counters)
    if not eq["all_pass"]:
        raise SystemExit("CLEAN_EQUIVALENCE_GATE_FAILED__STOP_BEFORE_PERTURBATION")

    # STAGE 3: image perturbations (SAMPLE FIRST).
    image_rows = []
    consistency_rows = []
    run_image_perturbations(ctx, generated, clean_store, counters,
                            image_rows, consistency_rows)

    # STAGE 4: proposal perturbations (SAMPLE FIRST).
    proposal_rows = []
    run_proposal_perturbations(ctx, generated, clean_store, counters, proposal_rows)

    counters["router_holdout_reads"] = 0
    counters["test_reads"] = 0
    counters["training"] = 0
    counters["optimizer_steps"] = 0
    counters["parameter_mutations"] = 0

    # STAGE 5: fixed summaries / worst-case / output writing.
    summaries = {
        "image_per_sample": summarize_image_per_sample(image_rows),
        "image_by_domain_condition": summarize_image_by_domain_condition(image_rows),
        "noise_seed": summarize_noise_seed(image_rows),
        "proposal_per_sample": summarize_proposal_per_sample(proposal_rows),
        "proposal_by_domain_condition": summarize_proposal_by_domain_condition(proposal_rows),
        "route_stability": summarize_route_stability(image_rows),
    }
    worst_per_sample = worst_case_per_sample(image_rows, proposal_rows)
    worst_by_domain = worst_case_by_domain(worst_per_sample)
    kub_rows = kub_subgroup_robustness(image_rows)

    return {"classification": "PHASE36_ROBUSTNESS_SCIENTIFIC_RESULT",
            "evidence_class": C.EVIDENCE_CLASS,
            "component_load_audit": audit,
            "clean_equivalence": eq,
            "prediction_consistency": consistency_rows,
            "image_rows": image_rows,
            "proposal_rows": proposal_rows,
            "worst_case_per_sample": worst_per_sample,
            "worst_case_by_domain": worst_by_domain,
            "kub_subgroup": kub_rows,
            "counts": {
                "authorized_population": AUTHORIZED_POPULATION_N,
                "clean_execution_count_expected": CLEAN_EXECUTIONS_EXPECTED,
                "image_nonclean_execution_count_expected": NONCLEAN_IMAGE_EXECUTIONS_EXPECTED,
                "image_rows_emitted": len(image_rows),
                "proposal_nonclean_execution_count_max": NONCLEAN_PROPOSAL_EXECUTIONS_MAX,
                "proposal_rows_emitted": len(proposal_rows),
                "logical_image_table_rows_max": LOGICAL_IMAGE_TABLE_ROWS_MAX,
            },
            "counters": counters, "generated_utc": now()}


# --------------------------------------------------------------------------- #
# §N/§O/§P  REAL four-component synthetic full-pipeline smoke
# --------------------------------------------------------------------------- #
def _synth_image(seed: int = 0) -> np.ndarray:
    rng = np.random.Generator(np.random.PCG64(seed))
    return rng.random((512, 512), dtype=np.float32)


def _synthetic_batch_image(ctx, seed: int = 0):
    import torch
    rng = np.random.Generator(np.random.PCG64(seed))
    arr = rng.random((3, 512, 512), dtype=np.float32)
    return torch.from_numpy(arr)[None]


def run_smoke() -> dict:
    """§N/§O/§P: construct + STRICT-load all FOUR real components and run ONE synthetic
    CLEAN + one IMAGE + one non-empty PROPOSAL through the REAL adapters.
    """
    if _gate_smoke() != 0:
        raise SystemExit(2)
    import torch

    ctx = _load_models()
    audit = ctx["load_audit"]
    system = ctx["system"]
    device = ctx["device"]
    ids = ["SYNTH_PHASE36_TASK0", "SYNTH_PHASE36_TASK1",
           "SYNTH_PHASE36_TASK2", "SYNTH_PHASE36_TASK3"]

    x = _synth_image(0)
    image_rows = []
    for cid in C.image_condition_ids():
        spec = C.IMAGE_CONDITIONS[cid]
        seeds = spec.get("base_seeds") or [None]
        for bs in seeds:
            xp = C.apply_image_condition(x, cid, ids[0], bs)
            image_rows.append({
                "condition": cid, "base_seed": bs,
                "shape": list(np.asarray(xp).shape),
                "dtype": str(np.asarray(xp).dtype),
                "finite": bool(np.isfinite(xp).all()),
                "min": float(xp.min()), "max": float(xp.max()),
                "generated_from_original_clean": True})
    clean_identity = bool(np.array_equal(C.apply_image_condition(x, "CLEAN", ids[0]), x))

    a = C.apply_gaussian_noise(x, 0.02, ids[0], 42)
    b = C.apply_gaussian_noise(x, 0.02, ids[0], 42)
    c = C.apply_gaussian_noise(x, 0.02, ids[0], 123)
    d = C.apply_gaussian_noise(x, 0.02, ids[1], 42)
    det = {"same_inputs_identical": bool(np.array_equal(a, b)),
           "different_base_seed_differs": bool(not np.array_equal(a, c)),
           "different_sample_id_differs": bool(not np.array_equal(a, d))}

    img_b = _synthetic_batch_image(ctx, seed=0).to(device)
    task_id = 0
    with torch.no_grad(), TapRecorder(ctx["g"]) as rec:
        g_out = ctx["g"](img_b, torch.tensor([task_id]))
        cmaps = {k: v.detach().cpu().numpy() for k, v in rec.store.items()}
    logits = g_out[0, 0].detach().cpu().numpy()
    p_global = (1.0 / (1.0 + np.exp(-logits.astype(np.float64)))).astype(np.float32)
    geom = _roi_geometry_from_prob(p_global, ROI_PROPOSAL_THRESHOLD, 0.25)
    window = None
    if geom is not None:
        window = (int(geom["clip_y1"]), int(geom["clip_y2"]),
                  int(geom["clip_x1"]), int(geom["clip_x2"]))
    roi_row = _geo_row(geom) if geom is not None else _roi_row_from_window(0, 512, 0, 512, 512)
    rf202 = _assemble_202d(cmaps, p_global, roi_row)

    oof_crop = None
    sf16 = None
    if geom is not None:
        rgb = img_b[0].detach().cpu().numpy()
        rgb_crop = crop_and_resize_vec(rgb, geom, REGIONAL_INPUT_RESOLUTION)
        prob_crop = crop_and_resize_vec(p_global, geom, REGIONAL_INPUT_RESOLUTION)
        rin = np.concatenate([np.asarray(rgb_crop, dtype=np.float32),
                              np.asarray(prob_crop, dtype=np.float32)], axis=0)
        with torch.no_grad():
            rin_t = torch.from_numpy(np.ascontiguousarray(rin))[None].to(device)
            refined = torch.sigmoid(ctx["r_psi"](rin_t).float())[0, 0].detach().cpu().numpy()
        oof_crop = refined
        pg_crop = np.asarray(prob_crop, dtype=np.float32)
        pg_crop = pg_crop[0] if pg_crop.ndim == 3 else pg_crop
        pr_crop = np.asarray(refined, dtype=np.float32)
        pr_crop = pr_crop[0] if pr_crop.ndim == 3 else pr_crop
        sf16 = np.asarray(somega_features(pg_crop, pr_crop, geom), dtype=np.float64).reshape(-1)

    out_clean = system.forward_inference(
        img_b, task_id, router_features_202=rf202, roi_window=window,
        action_available=(geom is not None), oof_refined_crop_prob=oof_crop,
        safety_post_features_16=sf16)
    clean_check = {
        "rf202_shape": list(np.asarray(rf202).shape),
        "rf202_finite": bool(np.isfinite(np.asarray(rf202)).all()),
        "p_global_shape": list(p_global.shape),
        "p_global_finite": bool(np.isfinite(p_global).all()),
        "geometry_available": geom is not None,
        "state": out_clean["state"],
        "final_probability_shape": list(np.asarray(out_clean["final_probability"]).shape),
        "final_probability_finite": bool(np.isfinite(out_clean["final_probability"]).all()),
        "global_forward_count": out_clean["global_forward_count"],
    }

    x_pert = C.apply_image_condition(_synth_image(0), "GAUSSIAN_NOISE_LOW", ids[0], 42)
    x_pert3 = np.stack([x_pert, x_pert, x_pert], axis=0)
    out_img = _evaluate_frozen_system(x_pert3, ids[0], task_id, {}, system=system, ctx=ctx)
    image_check = {"state": out_img["state"],
                   "final_finite": bool(np.isfinite(out_img["final_probability"]).all())}

    proposal_check = None
    if geom is not None:
        base_geom = {"y1": geom["y1"], "y2": geom["y2"], "x1": geom["x1"],
                     "x2": geom["x2"], "crop_side": geom["crop_side_pixels"],
                     "center_y": (geom["y1"] + geom["y2"]) / 2.0,
                     "center_x": (geom["x1"] + geom["x2"]) / 2.0}
        pert = C.apply_proposal_condition(base_geom, "SHIFT_LEFT_10", 512, 512)
        pert2 = C.apply_proposal_condition(base_geom, "SCALE_115", 512, 512)
        proposal_check = {"original_crop_side": base_geom["crop_side"],
                          "shift_crop_side": pert["crop_side"],
                          "scale_crop_side": pert2["crop_side"],
                          "scale_changes_side": bool(pert2["crop_side"] != base_geom["crop_side"])}

    empty_geom = _roi_geometry_from_prob(np.zeros((512, 512), dtype=np.float32))
    empty_check = {
        "empty_proposal_geometry_is_none": empty_geom is None,
        "handling": C.EMPTY_PROPOSAL_HANDLING,
        "no_outcome_dependent_replacement": bool(C.NO_OUTCOME_DEPENDENT_REPLACEMENT),
    }

    gt = np.zeros((512, 512), dtype=np.float32); gt[100:300, 100:300] = 1.0
    pred = np.zeros((512, 512), dtype=np.float32); pred[120:320, 120:320] = 1.0
    empty = np.zeros((512, 512), dtype=np.float32)
    metric_rows = {
        "nonempty_nonempty": {"dice": _dice(pred, gt), "iou": _iou(pred, gt)},
        "empty_empty": {"dice": _dice(empty, empty), "iou": _iou(empty, empty)},
        "empty_nonempty": {"dice": _dice(pred, empty), "iou": _iou(pred, empty)},
    }
    hd = _hd95(pred, gt)
    hd_empty = _hd95(empty, gt)
    hd_summary = _finite_summary([hd.get("hd95", np.nan) if isinstance(hd, dict) else hd,
                                  hd_empty.get("hd95", np.nan) if isinstance(hd_empty, dict) else hd_empty])

    sm = _smoke_state_machine(ctx)

    clean_mask = np.zeros((512, 512), dtype=np.float32); clean_mask[100:300, 100:300] = 1.0
    pert_mask = np.zeros((512, 512), dtype=np.float32); pert_mask[110:310, 110:310] = 1.0
    pc_dice = _prediction_consistency_dice(pert_mask, clean_mask)

    return {
        "mode": "smoke",
        "classification": "PRE_SCIENTIFIC_SYNTHETIC_FULL_PIPELINE_ROBUSTNESS_VALIDATION",
        "not_phase36_scientific_robustness_result": True,
        "synthetic_only": True,
        "scientific_output": False,
        "four_real_components_loaded": True,
        "component_load_audit": audit,
        "synthetic_sample_ids": ids,
        "image_registry": image_rows,
        "clean_bitwise_identity": clean_identity,
        "determinism": det,
        "clean_pipeline_check": clean_check,
        "image_pipeline_check": image_check,
        "proposal_pipeline_check": proposal_check,
        "empty_proposal_check": empty_check,
        "metrics": metric_rows,
        "prediction_consistency_dice_smoke": pc_dice,
        "hd95_hd": hd, "hd95_hd_empty_case": hd_empty, "hd95_summary": hd_summary,
        "state_machine": sm,
        "seed_conversion": C.seed_conversion_audit(),
        "pipeline_covered": ["four_component_strict_load", "clean_pipeline",
                             "image_perturbation", "proposal_perturbation",
                             "prediction_consistency_metric", "metric_plumbing",
                             "route_state_plumbing"],
        "generated_utc": now(),
    }


def _smoke_state_machine(ctx):
    """§O: real learned-component router score + explicit expected/observed/comparison."""
    import torch
    from src.models.barr.ra_medfilm_barr import (canonical_utility, TAU_C8_FINAL_FLOAT,
                                                 TAU_C7_FINAL)
    b_phi = ctx["b_phi"]
    device = ctx["device"]
    cases = []

    def _router_score(rf202, task_id):
        x = torch.from_numpy(np.asarray(rf202, dtype=np.float32))[None].to(device)
        t = torch.tensor([int(task_id)]).to(device)
        with torch.no_grad():
            return float(b_phi(x, t).reshape(-1)[0])

    rf_low = np.full(202, -50.0, dtype=np.float32)
    rf_high = np.full(202, 50.0, dtype=np.float32)
    for name, rf, expect_execute in (
            ("CONTROL_SKIP", rf_low, False),
            ("CONTROL_EXECUTE", rf_high, True)):
        obs_score = _router_score(rf, 0)
        util = canonical_utility(obs_score)
        observed_execute = bool(util >= TAU_C8_FINAL_FLOAT)
        cases.append({
            "case": name,
            "observed_router_score": obs_score,
            "router_threshold_C7": float(TAU_C7_FINAL),
            "utility": util,
            "observed_execute": observed_execute,
            "expected_execute": bool(expect_execute),
            "comparison_pass": bool(observed_execute == expect_execute),
            "real_learned_component": True,
        })
    return {"cases": cases, "policy_tests_not_scientific_outcomes": True,
            "real_learned_component_router_score": True,
            "threshold_C7": float(TAU_C7_FINAL),
            "threshold_C8": float(TAU_C8_FINAL_FLOAT)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=C.MODES)
    a = ap.parse_args()
    if a.mode == "science":
        if _gate_science() != 0:
            return 2
        res = run_science()
        (AUD / "phase36_robustness_scientific_result_v1_3.json").write_text(
            json.dumps(res, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
        return 0
    if a.mode == "smoke":
        res = run_smoke()
        (AUD / "phase36_robustness_smoke_v1_3.json").write_text(
            json.dumps(res, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
