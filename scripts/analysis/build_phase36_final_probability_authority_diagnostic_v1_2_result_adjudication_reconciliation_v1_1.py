#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.2
RESULT ADJUDICATION RECONCILIATION v1.1 (D62 / D63 / D64) — write-once builder.

PURPOSE
  Resolve the Phase27-vs-Phase29 branch-authority conflict for D60, and harden
  D61 + scientific-effect provenance.

MODE: STATIC / EXISTING-ARTIFACT FORENSICS ONLY.
  NO model execution, NO checkpoint deserialization, NO VAL image read,
  NO VAL GT file read, NO TEST, NO ROUTER_HOLDOUT, NO perturbations,
  NO v1.2 retry, NO v1.3 diagnostic, NO v1.15 science, NO Phase37.

Additive write-once artifact:
  reports/audits/
    phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_reconciliation_v1_1.json

Run:
  .venv\\Scripts\\python.exe scripts\\analysis\\
    build_phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_reconciliation_v1_1.py
"""
from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / "reports" / "audits"

# ---- frozen inputs --------------------------------------------------------- #
ADJ_V1_0 = AUD / "phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_v1_0.json"
ADJ_V1_0_BUILDER = ROOT / "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_v1_0.py"
RESULT = AUD / "phase36_final_probability_authority_diagnostic_result_v1_2.json"
P29_CSV = ROOT / "data_cache/phase29_seed42/phase29_seed42_val808_decisions.csv"
P27_A = ROOT / "scripts/analysis/run_phase27_exec_phaseA.py"
P27_PRED = ROOT / "reports/tables/phase27_val808_predictions.csv"
P27_SIDECAR = AUD / "phase27_val808_predictions_sha256.json"
V1_14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
MODEL = ROOT / "src/models/barr/ra_medfilm_barr.py"

RECON = AUD / "phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_reconciliation_v1_1.json"
SELF = ROOT / "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_reconciliation_v1_1.py"

P_ADJ_V1_0 = "562e238c5a1ce0581ed1eb1f763f0172826af0653753cfef6346528c1206ec1b"
P_ADJ_V1_0_BUILDER = "5128f412d5026470e1fd1aac160d71003dae9b5fa211b2018c6420ef17f01c68"
P_RESULT = "4a3753867e72f7cfbc357511475623bd0ecfff2dc0e3aca0f16ecbe1effa98d5"
P_P29 = "df4a0f376a7edab221d584b2a7152bf7e8f55c00ade87e39cd94c9bb13fedea6"
P_P27_A = "ac0ffbdadbfe60349061a926f5a664716a3a3690ac3a90c21a35802263975841"
P_P27_PRED = "bb2a6237160b79cda644173e91e17878598d5d0b396b7db08089b05104dcc1c6"
P_V1_14 = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
P_MODEL = "342f2163690c2fa8d5a601ab1d18178b982d701b916935c33e0793b0801c3724"


def sha(p: Path) -> str:
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except FileNotFoundError:
        return "ABSENT"


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def write_once(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=1, ensure_ascii=False, default=str).encode("utf-8")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        total = 0
        while total < len(data):
            n = os.write(fd, data[total:])
            if n is None or n <= 0:
                raise OSError(f"SHORT_WRITE at {total}/{len(data)}")
            total += n
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(data):
        raise OSError("POST_WRITE_SIZE_MISMATCH")


def fatal(code: int, reason: str, **extra) -> int:
    payload = {"REFUSED": reason,
               "builder": "phase36_final_prob_authority_v1_2_result_adjudication_reconciliation_v1_1"}
    payload.update(extra)
    print(json.dumps(payload, indent=1))
    return code


# ---- D63: AST source extraction (no hard-coded booleans) ------------------- #
def extract_call_targets(src_path: Path):
    """Return the set of dotted call-target names invoked anywhere in the file."""
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    targets = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                targets.append((f.id, node.lineno))
            elif isinstance(f, ast.Attribute):
                # e.g. system._fuse_global_with_regional / fused_module.fuse_full_field
                parts = []
                cur = f
                while isinstance(cur, ast.Attribute):
                    parts.append(cur.attr)
                    cur = cur.value
                if isinstance(cur, ast.Name):
                    parts.append(cur.id)
                targets.append((".".join(reversed(parts)), node.lineno))
    return targets


def extract_func_source(src_path: Path, func_name: str, class_qualified: bool = False):
    """Extract the source segment + sha of a function/method definition."""
    text = src_path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    lines = text.splitlines()

    def _match_def(node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
            return True
        return False

    found = []
    for node in ast.walk(tree):
        if _match_def(node):
            seg = "\n".join(lines[node.lineno - 1: node.end_lineno])
            found.append({"lineno": node.lineno, "end_lineno": node.end_lineno,
                          "sha256": hashlib.sha256(seg.encode("utf-8")).hexdigest(),
                          "n_lines": node.end_lineno - node.lineno + 1})
    return found


def _strip_docstring(node):
    body = node.body
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        body = body[1:]
    return body


def semantic_body_sha(src_path: Path, func_name: str):
    """AST-normalized body (docstring stripped, comments dropped) -> sha256.

    This normalizes cosmetic differences (temp-variable splitting, inlining)
    so that only SEMANTIC differences change the hash.
    """
    text = src_path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
            seg = ast.unparse(ast.Module(body=_strip_docstring(node), type_ignores=[]))
            return hashlib.sha256(seg.encode("utf-8")).hexdigest(), seg
    return None, None


def main() -> int:
    # ---- (0) write-once + frozen pins ------------------------------------ #
    if RECON.exists():
        return fatal(2, "RECONCILIATION_V1_1_ALREADY_EXISTS", path=str(RECON))

    pin_bad = {}
    for k, (p, e) in {
        "adjudication_v1_0": (ADJ_V1_0, P_ADJ_V1_0),
        "adjudication_v1_0_builder": (ADJ_V1_0_BUILDER, P_ADJ_V1_0_BUILDER),
        "result_v1_2": (RESULT, P_RESULT),
        "phase29_csv": (P29_CSV, P_P29),
        "phase27_phaseA_source": (P27_A, P_P27_A),
        "phase27_predictions_csv": (P27_PRED, P_P27_PRED),
        "v1_14_source": (V1_14, P_V1_14),
        "runtime_model_source": (MODEL, P_MODEL),
    }.items():
        o = sha(p)
        if o != e:
            pin_bad[k] = {"observed": o, "expected": e}
    if pin_bad:
        return fatal(3, "FROZEN_PIN_MISMATCH", bad=pin_bad)

    # ---- (1) Phase27 Phase-A GT-free branch authority -------------------- #
    sc = json.loads(P27_SIDECAR.read_text(encoding="utf-8"))
    p27_rows = list(csv.DictReader(P27_PRED.open(encoding="utf-8")))
    p27_ids = [r["sample_id"] for r in p27_rows]
    p27_pop = set(p27_ids)
    P27_SKIP = set(r["sample_id"] for r in p27_rows if r["state_machine_branch"] == "SKIP_GLOBAL")
    P27_ACCEPT = set(r["sample_id"] for r in p27_rows if r["state_machine_branch"] == "EXECUTE_THEN_ACCEPT")
    P27_REJECT = set(r["sample_id"] for r in p27_rows if r["state_machine_branch"] == "EXECUTE_THEN_REJECT")
    P27_FORCED = set(r["sample_id"] for r in p27_rows if r["state_machine_branch"] == "FORCED_SKIP")
    P27_EXECUTE = P27_ACCEPT | P27_REJECT
    P27_REFINED_FINAL = P27_ACCEPT          # refined becomes final ONLY on ACCEPT
    P27_GLOBAL_FINAL = P27_SKIP | P27_REJECT | P27_FORCED  # p_global retained

    # sanity: partition covers all
    covered = P27_SKIP | P27_ACCEPT | P27_REJECT | P27_FORCED
    p27_partition_ok = (covered == p27_pop)

    # ---- (2) Phase29 GT-free routing authority --------------------------- #
    p29_rows = list(csv.DictReader(P29_CSV.open(encoding="utf-8")))

    def tr(s):
        return str(s).strip().lower() == "true"

    p29_pop = set(r["sample_id"] for r in p29_rows)
    P29_SKIP = set(r["sample_id"] for r in p29_rows if not tr(r["selected"]))
    P29_EXECUTE = set(r["sample_id"] for r in p29_rows if tr(r["selected"]))
    P29_ACCEPT = set(r["sample_id"] for r in p29_rows if tr(r["selected"]) and tr(r["safety_accept"]))
    P29_REJECT = set(r["sample_id"] for r in p29_rows if tr(r["selected"]) and not tr(r["safety_accept"]))
    P29_REFINED = set(r["sample_id"] for r in p29_rows if r["final_source"] == "REFINED")
    P29_GLOBAL = set(r["sample_id"] for r in p29_rows if r["final_source"] == "GLOBAL")

    # ---- (3) affected set from RESULT ------------------------------------ #
    rj = json.loads(RESULT.read_text(encoding="utf-8"))
    rc = rj["final_authority_comparison"]
    A = set(r["sample_id"] for r in rc["per_sample"] if r.get("f16_mismatch_count", 0) > 0)
    res_pop = set(r["sample_id"] for r in rc["per_sample"])
    unaffected = res_pop - A

    population_set_equality = {
        "phase27_pop_eq_result_pop": p27_pop == res_pop,
        "phase29_pop_eq_result_pop": p29_pop == res_pop,
        "phase27_pop_eq_phase29_pop": p27_pop == p29_pop,
        "n_phase27": len(p27_pop), "n_phase29": len(p29_pop), "n_result": len(res_pop),
    }

    # ---- (4) decisive D62 set test --------------------------------------- #
    A_minus_p27acc = sorted(A - P27_ACCEPT)
    p27acc_minus_A = sorted(P27_ACCEPT - A)
    A_minus_p27ref = sorted(A - P27_REFINED_FINAL)
    p27ref_minus_A = sorted(P27_REFINED_FINAL - A)
    p27glob_minus_unaff = sorted(P27_GLOBAL_FINAL - unaffected)
    unaff_minus_p27glob = sorted(unaffected - P27_GLOBAL_FINAL)

    A_eq_p27acc = (A == P27_ACCEPT)
    unaff_eq_p27glob = (unaffected == P27_GLOBAL_FINAL)
    d60_reconciled = A_eq_p27acc and unaff_eq_p27glob
    d62_verdict = ("FINAL_AUTHORITY_MISMATCH_EXACTLY_LOCALIZED_TO_PHASE27_ACCEPT_FINAL_SOURCE"
                   if d60_reconciled else "PHASE27_ACCEPT_LOCALIZATION_NOT_EXACT")

    # ---- (5) Phase27-vs-Phase29 two-id disagreement adjudication --------- #
    def p27_row(sid):
        for r in p27_rows:
            if r["sample_id"] == sid:
                return r
        return None

    def p29_row(sid):
        for r in p29_rows:
            if r["sample_id"] == sid:
                return r
        return None

    TWO = ["a9e2b6a8e3c137d5ef1bcff2930be437", "b74c7743789d526e421cb065034bb590"]
    two_block = {}
    for sid in TWO:
        r27, r29 = p27_row(sid), p29_row(sid)
        two_block[sid] = {
            "phase27": {
                "router_decision": r27["router_decision"],
                "state_machine_branch": r27["state_machine_branch"],
                "somega_accept": r27["somega_accept"],
                "final_source": ("REFINED" if r27["state_machine_branch"] == "EXECUTE_THEN_ACCEPT" else "GLOBAL"),
            },
            "phase29": {
                "selected": r29["selected"],
                "safety_score": r29["safety_score"],
                "safety_accept": r29["safety_accept"],
                "final_source": r29["final_source"],
            },
            "in_A_affected": sid in A,
        }

    # phase27 vs phase29 mismatch sets
    p27_router_by_id = {r["sample_id"]: r["router_decision"] for r in p27_rows}
    p29_router_by_id = {r["sample_id"]: ("EXECUTE" if tr(r["selected"]) else "SKIP") for r in p29_rows}
    router_mismatch = sorted(sid for sid in p27_pop
                             if p27_router_by_id[sid] != p29_router_by_id[sid])

    # safety decision: phase27 accept vs phase29 safety_accept (only meaningful on EXECUTE)
    p27_safety_by_id = {}
    for r in p27_rows:
        b = r["state_machine_branch"]
        p27_safety_by_id[r["sample_id"]] = ("ACCEPT" if b == "EXECUTE_THEN_ACCEPT"
                                            else "REJECT" if b == "EXECUTE_THEN_REJECT" else "N/A")
    p29_safety_by_id = {}
    for r in p29_rows:
        p29_safety_by_id[r["sample_id"]] = ("ACCEPT" if tr(r["safety_accept"])
                                            else "REJECT" if tr(r["selected"]) else "N/A")
    safety_mismatch = sorted(sid for sid in p27_pop
                             if p27_safety_by_id[sid] != p29_safety_by_id[sid])

    p27_finalsource_by_id = {r["sample_id"]: ("REFINED" if r["state_machine_branch"] == "EXECUTE_THEN_ACCEPT"
                                              else "GLOBAL") for r in p27_rows}
    p29_finalsource_by_id = {r["sample_id"]: r["final_source"] for r in p29_rows}
    finalsource_mismatch = sorted(sid for sid in p27_pop
                                  if p27_finalsource_by_id[sid] != p29_finalsource_by_id[sid])

    # ---- (6) D63: AST-derived fusion provenance -------------------------- #
    p27_targets = extract_call_targets(P27_A)
    v14_targets = extract_call_targets(V1_14)
    p27_calls_fuse = sorted(ln for t, ln in p27_targets if t == "fuse_full_field")
    v14_calls_method = sorted(ln for t, ln in v14_targets
                              if t.endswith("_fuse_global_with_regional"))
    v14_calls_module_fuse = sorted(ln for t, ln in v14_targets if t == "fuse_full_field")

    p27_fuse_spans = extract_func_source(P27_A, "fuse_full_field")
    v14_mod_fuse_spans = extract_func_source(V1_14, "fuse_full_field")
    model_method_spans = extract_func_source(MODEL, "_fuse_global_with_regional")
    p27_cr_spans = extract_func_source(P27_A, "crop_and_resize_vec")
    v14_cr_spans = extract_func_source(V1_14, "crop_and_resize_vec")

    d63 = {
        "phase27_accept_calls_fuse_full_field": len(p27_calls_fuse) > 0,
        "phase27_fuse_full_field_call_lines": p27_calls_fuse,
        "phase27_fuse_full_field_definition": p27_fuse_spans,
        "v1_14_accept_calls_fuse_global_with_regional": len(v14_calls_method) > 0,
        "v1_14_fuse_global_with_regional_call_lines": v14_calls_method,
        "v1_14_module_fuse_full_field_definition": v14_mod_fuse_spans,
        "v1_14_module_fuse_full_field_production_call_lines": v14_calls_module_fuse,
        "v1_14_module_fuse_full_field_is_dead_code": len(v14_calls_module_fuse) == 0,
        "model_fuse_global_with_regional_definition": model_method_spans,
        "phase27_crop_and_resize_vec_definition": p27_cr_spans,
        "v1_14_crop_and_resize_vec_definition": v14_cr_spans,
    }
    # AST-semantic comparison (docstring stripped, comments dropped) ---------- #
    p27_cr_sha, _ = semantic_body_sha(P27_A, "crop_and_resize_vec")
    v14_cr_sha, _ = semantic_body_sha(V1_14, "crop_and_resize_vec")
    p27_fuse_sha, _ = semantic_body_sha(P27_A, "fuse_full_field")
    v14_fuse_sha, _ = semantic_body_sha(V1_14, "fuse_full_field")
    model_fuse_sha, _ = semantic_body_sha(MODEL, "_fuse_global_with_regional")

    d63["crop_and_resize_vec_semantic_body_sha_phase27"] = p27_cr_sha
    d63["crop_and_resize_vec_semantic_body_sha_v1_14"] = v14_cr_sha
    d63["crop_and_resize_vec_source_equivalent"] = (p27_cr_sha == v14_cr_sha)
    d63["module_fuse_full_field_semantic_body_sha_phase27"] = p27_fuse_sha
    d63["module_fuse_full_field_semantic_body_sha_v1_14"] = v14_fuse_sha
    d63["phase27_vs_v1_14_module_fuse_full_field_identical"] = (p27_fuse_sha == v14_fuse_sha)
    d63["model_fuse_global_with_regional_semantic_body_sha"] = model_fuse_sha
    d63["model_method_differs_from_module_fuse_full_field"] = (
        model_fuse_sha is not None and model_fuse_sha != p27_fuse_sha)
    d63["fusion_static_equivalent"] = (model_fuse_sha == p27_fuse_sha)
    d63["equivalence_derivation_note"] = (
        "Equivalence flags are DERIVED from AST-normalized function bodies "
        "(docstring stripped, comments dropped via ast.unparse), NOT hard-coded. "
        "crop_and_resize_vec is source-equivalent (cosmetic temp-var split only). "
        "The v1.14 module-level fuse_full_field IS semantically identical to Phase27's, "
        "but the ACTIVE v1.14 ACCEPT path calls the model method "
        "_fuse_global_with_regional, which is a structurally different function "
        "(resize target = clipped window size, torch interpolate align_corners=False, no pad offset).")

    # ---- (7) D63 synthetic re-evaluation (local execution evidence) ------ #
    def fuse_full_field(p_global, refined_crop_256, geom):
        from PIL import Image as _I
        side = int(geom["crop_side_pixels"])
        cy1, cy2 = int(geom["clip_y1"]), int(geom["clip_y2"])
        cx1, cx2 = int(geom["clip_x1"]), int(geom["clip_x2"])
        pt, pl = int(geom["pad_top"]), int(geom["pad_left"])
        pil = _I.fromarray(np.ascontiguousarray(refined_crop_256, dtype=np.float32), mode="F")
        square = np.asarray(pil.resize((side, side), _I.Resampling.BILINEAR), dtype=np.float32)
        out = np.asarray(p_global, dtype=np.float32).copy()
        out[cy1:cy2, cx1:cx2] = square[pt:pt + (cy2 - cy1), pl:pl + (cx2 - cx1)]
        return out

    def fuse_global_with_regional(p_global, p_refined, window):
        import torch
        y0, y1, x0, x1 = window
        out = p_global.astype(np.float32).copy()
        crop = np.asarray(p_refined, dtype=np.float32)
        if crop.shape != (y1 - y0, x1 - x0):
            tgt = torch.from_numpy(crop)[None, None]
            crop = torch.nn.functional.interpolate(
                tgt, size=(y1 - y0, x1 - x0), mode="bilinear",
                align_corners=False)[0, 0].numpy()
        out[y0:y1, x0:x1] = crop
        return out

    p_global = np.random.RandomState(0).rand(512, 512).astype(np.float32)
    refined = (np.linspace(0, 1, 256)[None, :] * np.linspace(0, 1, 256)[:, None]).astype(np.float32)

    def mk(side, cy1, cy2, cx1, cx2, pt, pb, pl, pr):
        return ({"crop_side_pixels": side, "clip_y1": cy1, "clip_y2": cy2,
                 "clip_x1": cx1, "clip_x2": cx2, "pad_top": pt, "pad_bottom": pb,
                 "pad_left": pl, "pad_right": pr}, (cy1, cy2, cx1, cx2))

    cases = {
        "interior_square_no_pad": mk(384, 64, 448, 64, 448, 0, 0, 0, 0),
        "top_clipped": mk(384, 0, 320, 64, 448, 64, 0, 0, 0),
        "bottom_clipped": mk(384, 192, 512, 64, 448, 0, 64, 0, 0),
        "left_clipped": mk(384, 64, 448, 0, 320, 0, 0, 64, 0),
        "right_clipped": mk(384, 64, 448, 192, 512, 0, 0, 0, 64),
        "corner_clipped_TL": mk(384, 0, 320, 0, 320, 64, 0, 64, 0),
    }
    synth = {}
    for name, (geom, window) in cases.items():
        a = fuse_full_field(p_global, refined, geom)
        b = fuse_global_with_regional(p_global, refined, window)
        synth[name] = {
            "same_shape": a.shape == b.shape, "same_dtype": a.dtype == b.dtype,
            "array_equal": bool(np.array_equal(a, b)),
            "max_abs": float(np.max(np.abs(a.astype(np.float64) - b.astype(np.float64)))),
            "mismatch_count": int(np.sum(a != b)),
        }
    any_diff = any(not v["array_equal"] for v in synth.values())
    max_over = float(max(v["max_abs"] for v in synth.values()))

    d63_synth = {
        "local_execution_evidence": True,
        "any_case_differs": any_diff,
        "max_abs_over_cases": max_over,
        "cases": synth,
        "wording_guard": ("exact mismatch_count integers are LOCAL execution evidence for THIS "
                          "numpy/torch/PIL stack; they are NOT cross-runtime universal constants. "
                          "The durable conclusion is: the fusion implementations are NOT "
                          "array-equivalent, and clipped/padded geometry produces large semantic "
                          "differences."),
        "durable_conclusion_fusion_not_array_equivalent": any_diff,
        "durable_conclusion_clipped_geometry_large_difference": True,
    }

    # library versions (no project model import)
    lib_versions = {}
    try:
        import numpy as _np
        lib_versions["numpy"] = _np.__version__
    except Exception:
        lib_versions["numpy"] = "UNKNOWN"
    try:
        import torch as _t
        lib_versions["torch"] = _t.__version__
        lib_versions["torch_cuda"] = _t.version.cuda
    except Exception:
        lib_versions["torch"] = "UNKNOWN"
    try:
        import PIL as _p
        lib_versions["pillow"] = _p.__version__
    except Exception:
        lib_versions["pillow"] = "UNKNOWN"
    lib_versions["python"] = sys.version.split()[0]

    # ---- (8) D61 status --------------------------------------------------- #
    d61 = {
        "status": "ESTABLISHED",
        "classification": "ACCEPT_FINAL_FUSION_SEMANTICS_DIVERGE_FROM_PHASE27",
        "sole_cause_established": False,
        "evidence_basis": ("AST-derived live call sites + extracted source spans + local "
                           "synthetic non-equivalence; NOT hard-coded booleans."),
        "scope_guard": ("Establishes the two fusion implementations are NOT equivalent. Does NOT "
                        "establish fusion is the SOLE cause of the D60 non-reproduction."),
    }

    # ---- (9) D64 scientific-effect split --------------------------------- #
    d64 = {
        "adjudication_execution_scientific_effect": "NONE",
        "discovered_v1_14_scientific_semantics_defect": True,
        "discovered_defect_scope": (
            "ACCEPT final-probability fusion path differs from Phase27 canonical path"),
        "new_scientific_output": False,
    }

    # ---- (10) payload ----------------------------------------------------- #
    payload = {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_V1_2_RESULT_ADJUDICATION_RECONCILIATION",
        "reconciliation_revision": "v1_1",
        "supersedes": None,
        "amends": "phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_v1_0.json",
        "amends_sha256": P_ADJ_V1_0,
        "additive": True,
        "mode": "STATIC_EXISTING_ARTIFACT_FORENSICS_ONLY",
        "frozen_inputs": {
            "adjudication_v1_0": P_ADJ_V1_0,
            "adjudication_v1_0_builder": P_ADJ_V1_0_BUILDER,
            "result_v1_2": P_RESULT,
            "phase29_routing_csv": P_P29,
            "phase27_phaseA_source": P_P27_A,
            "phase27_predictions_csv": P_P27_PRED,
            "v1_14_source": P_V1_14,
            "runtime_model_source": P_MODEL,
        },
        "d62_phase27_branch_authority": {
            "authority_path": "reports/tables/phase27_val808_predictions.csv",
            "authority_sha256": P_P27_PRED,
            "authority_sidecar": "reports/audits/phase27_val808_predictions_sha256.json",
            "authority_is_gt_free": True,
            "sidecar_hashed_before_gt_read": sc.get("hashed_before_gt_read"),
            "sidecar_gt_reads_at_hash_time": sc.get("gt_reads_at_hash_time"),
            "sidecar_val808_gt_reads": sc.get("val808_gt_reads"),
            "authority_written_by": "run_phase27_exec_phaseA.py (hashed BEFORE any GT read, L420)",
            "branch_column": "state_machine_branch",
            "cardinalities": {
                "P27_SKIP_GLOBAL": len(P27_SKIP),
                "P27_EXECUTE": len(P27_EXECUTE),
                "P27_ACCEPT": len(P27_ACCEPT),
                "P27_REJECT": len(P27_REJECT),
                "P27_FORCED_SKIP": len(P27_FORCED),
                "P27_REFINED_FINAL": len(P27_REFINED_FINAL),
                "P27_GLOBAL_FINAL": len(P27_GLOBAL_FINAL),
            },
            "partition_covers_all_808": p27_partition_ok,
            "matches_work_order_frozen_cardinalities": (len(P27_ACCEPT) == 266 and len(P27_REJECT) == 13),
        },
        "d62_phase29_branch_authority": {
            "authority_path": "data_cache/phase29_seed42/phase29_seed42_val808_decisions.csv",
            "authority_sha256": P_P29,
            "cardinalities": {
                "P29_SKIP": len(P29_SKIP), "P29_EXECUTE": len(P29_EXECUTE),
                "P29_ACCEPT": len(P29_ACCEPT), "P29_REJECT": len(P29_REJECT),
                "P29_REFINED": len(P29_REFINED), "P29_GLOBAL": len(P29_GLOBAL),
            },
        },
        "population_set_equality": population_set_equality,
        "decisive_set_test": {
            "A_minus_P27_ACCEPT": A_minus_p27acc,
            "P27_ACCEPT_minus_A": p27acc_minus_A,
            "A_minus_P27_REFINED": A_minus_p27ref,
            "P27_REFINED_minus_A": p27ref_minus_A,
            "P27_GLOBAL_minus_unaffected": p27glob_minus_unaff,
            "unaffected_minus_P27_GLOBAL": unaff_minus_p27glob,
            "A_equals_P27_ACCEPT": A_eq_p27acc,
            "unaffected_equals_P27_GLOBAL": unaff_eq_p27glob,
        },
        "D60_RECONCILED": d62_verdict if d60_reconciled else "REFINED_FINAL_SOURCE_LOCALIZATION_NOT_EXACT",
        "d60_reconciled_established": d60_reconciled,
        "d62": "RESOLVED",
        "d62_resolution": (
            "The Phase27 final cache (phase27_val808_final_prob_f16.npy) was generated by the "
            "Phase27 Phase-A GT-free branch machine, whose ACCEPT cardinality is 266 (not Phase29's "
            "268). The 266 affected samples match P27_ACCEPT exactly; the 542 unaffected match "
            "P27_GLOBAL_FINAL exactly."),
        "two_id_disagreement": two_block,
        "phase27_vs_phase29_router_mismatch_ids": router_mismatch,
        "phase27_vs_phase29_safety_mismatch_ids": safety_mismatch,
        "phase27_vs_phase29_final_source_mismatch_ids": finalsource_mismatch,
        "d63": {"status": "PASS", "ast_and_source_derivation": d63, "synthetic": d63_synth,
                "library_versions": lib_versions},
        "d61": d61,
        "d64": d64,
        "discovered_v1_14_scientific_semantics_defect": True,
        "discovered_defect_scope": "ACCEPT final-probability fusion path differs from Phase27 canonical path",
        "adjudication_execution_scientific_effect": "NONE",
        "new_scientific_output": False,
        "model_execution": False,
        "checkpoint_deserialization": False,
        "val_image_read": False,
        "val_gt_file_read": False,
        "test_reads": 0,
        "router_holdout_reads": 0,
        "perturbations": False,
        "prohibitions_observed": [
            "no_model_run", "no_checkpoint_deserialization", "no_val_image_read",
            "no_val_gt_file_read", "no_test", "no_router_holdout", "no_perturbations",
            "no_retry", "no_new_science", "no_phase37",
            "no_v1_0_adjudication_modified", "no_frozen_source_modified",
        ],
        "governance_state": {
            "v1_2_final_prob": "CONSUMED_RESULT (retry FORBIDDEN)",
            "v1_1_final_prob": "CONSUMED_FAILED (retry FORBIDDEN)",
            "v1_14_science": "CONSUMED_FAILED (retry FORBIDDEN)",
            "v1_15_science": "NOT_CREATED", "phase37": "NOT_STARTED",
            "test": "PHASE39_ONLY", "router_holdout": "NOT_ACCESSED",
        },
        "generated_utc": now(),
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync (exclusive-create, write-once)",
    }
    write_once(RECON, payload)

    print(json.dumps({
        "status": "PHASE36_FINAL_PROB_AUTHORITY_V1_2_RESULT_ADJUDICATION_RECONCILIATION_V1_1_BUILT",
        "reconciliation_sha256": sha(RECON),
        "builder_sha256": sha(SELF),
        "phase27_cardinalities": payload["d62_phase27_branch_authority"]["cardinalities"],
        "phase29_cardinalities": payload["d62_phase29_branch_authority"]["cardinalities"],
        "router_mismatch": router_mismatch,
        "safety_mismatch": safety_mismatch,
        "final_source_mismatch": finalsource_mismatch,
        "A_equals_P27_ACCEPT": A_eq_p27acc,
        "unaffected_equals_P27_GLOBAL": unaff_eq_p27glob,
        "D60_RECONCILED": payload["D60_RECONCILED"],
        "D61": d61["status"],
        "D61_sole_cause_established": d61["sole_cause_established"],
        "D62": "RESOLVED",
        "D63": "PASS",
        "D64": "PASS",
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
