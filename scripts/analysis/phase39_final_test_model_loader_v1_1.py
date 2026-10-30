"""Phase39 v1.1 frozen model loaders — D98 repair.

D98 defect (v1_0): the AST extraction copied the BARRPostSafetyV1 class WITHOUT
its transitive module-global dependency closure, so `FEATURE_DIM` (and `HIDDEN`)
were undefined at instantiation.

v1.1 repair: mirror the FROZEN canonical Phase36 pattern — exec the module-level
dimension constant assignments (FEATURE_DIM / HIDDEN / NUMERIC_IDX / ONEHOT_IDX)
into the extraction namespace BEFORE the class body.

Scientific delta = 0: this restores the class's frozen dependency closure; it
does not alter architecture, weights, or any scientific semantics.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ROUTER_SOURCE = "scripts/analysis/train_phase25d_router.py"
ROUTER_CLASS = "BARRBenefitRouterV1"
SOMEGA_SOURCE = "scripts/analysis/phase25f_execution_common.py"
SOMEGA_CLASS = "BARRPostSafetyV1"

# Frozen module-global constants required by the extracted classes.
_REQUIRED_CONSTANTS = ("FEATURE_DIM", "HIDDEN", "NUMERIC_IDX", "ONEHOT_IDX")


def _extract_class(source_rel: str, class_name: str, constants=_REQUIRED_CONSTANTS):
    """AST-extract a class along with its required module-global constant closure."""
    import numpy as np
    import torch
    import torch.nn as nn
    src = (ROOT / source_rel).read_text(encoding="utf-8")
    tree = ast.parse(src)
    ns = {"__name__": "_phase39_v1_1_" + class_name, "__builtins__": __builtins__,
          "torch": torch, "nn": nn, "np": np}
    # 1. inject the module-level constant assignments the class depends on
    for node in tree.body:
        if isinstance(node, ast.Assign):
            tg = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if any(t in constants for t in tg):
                exec(compile(ast.Module(body=[node], type_ignores=[]), source_rel, "exec"), ns)
    # 2. inject the class body
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            exec(compile(ast.Module(body=[node], type_ignores=[]), source_rel, "exec"), ns)
            return ns[class_name]
    raise RuntimeError(f"{class_name} not found in frozen source {source_rel}")


def load_router():
    return _extract_class(ROUTER_SOURCE, ROUTER_CLASS)()


def load_somega():
    return _extract_class(SOMEGA_SOURCE, SOMEGA_CLASS)()


# Frozen checkpoint expectations (must equal the Phase38 checkpoint manifest).
CHECKPOINTS = {
    "G": {"path": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
          "sha256": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7", "params": 3523001},
    "B_phi": {"path": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
              "sha256": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b", "params": 36801},
    "R_psi": {"path": "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
              "sha256": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109", "params": 1276401},
    "S_omega": {"path": "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
                "sha256": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e", "params": 1217},
}


def _sha(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def build_all_models(require_cuda: bool = True):
    """Construct + strict-load all four frozen components. Returns (models, device, audit).

    require_cuda=True (science) enforces the frozen CUDA fail-closed contract.
    require_cuda=False (regression only) constructs/strict-loads on CPU; it never
    touches TEST data and never changes architecture or weights.
    """
    import torch
    from src.models.film.global_medfilm import GlobalMedFiLM
    from src.models.barr.regional_refiner import BARRRegionalRefinerV1

    if require_cuda:
        from src.utils.device import get_device
        device = get_device(require_cuda=True)
        if str(getattr(device, "type", device)) != "cuda":
            raise RuntimeError("PHASE39_V1_1_CUDA_FAIL_CLOSED__NOT_CUDA")
    else:
        device = torch.device("cpu")

    g = GlobalMedFiLM()
    r_psi = BARRRegionalRefinerV1()
    b_phi = load_router()
    s_omega = load_somega()

    audit = {}
    for name, m in (("G", g), ("R_psi", r_psi), ("B_phi", b_phi), ("S_omega", s_omega)):
        ck = torch.load(ROOT / CHECKPOINTS[name]["path"], map_location="cpu", weights_only=False)
        res = m.load_state_dict(ck["model_state"], strict=True)
        m.eval()
        m.requires_grad_(False)
        audit[name] = {
            "checkpoint_sha256": _sha(ROOT / CHECKPOINTS[name]["path"]),
            "checkpoint_sha256_expected": CHECKPOINTS[name]["sha256"],
            "parameter_count": int(sum(p.numel() for p in m.parameters())),
            "parameter_count_expected": CHECKPOINTS[name]["params"],
            "missing_keys": list(getattr(res, "missing_keys", [])),
            "unexpected_keys": list(getattr(res, "unexpected_keys", [])),
            "all_weights_finite": bool(all(bool(torch.isfinite(p).all()) for p in m.parameters())),
        }
    ok = (all(v["parameter_count"] == v["parameter_count_expected"] for v in audit.values())
          and all(not v["missing_keys"] and not v["unexpected_keys"] for v in audit.values())
          and all(v["all_weights_finite"] for v in audit.values())
          and all(v["checkpoint_sha256"] == v["checkpoint_sha256_expected"] for v in audit.values()))
    if not ok:
        raise RuntimeError(f"PHASE39_V1_1_COMPONENT_LOAD_FAILURE: {audit}")
    for m in (g, r_psi, b_phi, s_omega):
        m.to(device)
    return {"G": g, "R_psi": r_psi, "B_phi": b_phi, "S_omega": s_omega}, device, audit
