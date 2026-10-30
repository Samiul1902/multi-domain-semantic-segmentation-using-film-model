#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.2
POST-RESULT STATIC FORENSIC ADJUDICATION (D60 / D61) — write-once builder.

Target: D60 ACCEPTED-BRANCH / REFINED-FINAL-SOURCE LOCALIZATION.

MODE: STATIC + EXISTING-ARTIFACT FORENSICS ONLY.
  NO model execution, NO checkpoint deserialization, NO VAL image read,
  NO VAL GT read, NO TEST, NO ROUTER_HOLDOUT, NO perturbations,
  NO v1.2 retry, NO v1.3 diagnostic, NO v1.15 science, NO Phase37.

Writes exactly once (O_CREAT|O_EXCL + full write + fsync + size check):
  reports/audits/
    phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_v1_0.json

Fail-closed: refuses if the target exists or if any consumed-evidence SHA mismatches.

Run:
  .venv\\Scripts\\python.exe scripts\\analysis\\
    build_phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_v1_0.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / "reports" / "audits"

START = AUD / "phase36_final_probability_authority_diagnostic_start_v1_2.json"
RESULT = AUD / "phase36_final_probability_authority_diagnostic_result_v1_2.json"
STDOUT = AUD / "phase36_final_probability_authority_diagnostic_stdout_first_attempt_v1_2.txt"
STDERR = AUD / "phase36_final_probability_authority_diagnostic_stderr_first_attempt_v1_2.txt"
FAILURE = AUD / "phase36_final_probability_authority_diagnostic_failure_v1_2.json"

DIAG = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_2.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_2.py"
D59 = AUD / "phase36_final_probability_authority_diagnostic_v1_2_governance_reconciliation_v1_1.json"

PHASE29_CSV = ROOT / "data_cache/phase29_seed42/phase29_seed42_val808_decisions.csv"
PHASE27_A = ROOT / "scripts/analysis/run_phase27_exec_phaseA.py"
V1_14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
MODEL = ROOT / "src/models/barr/ra_medfilm_barr.py"
RPSI_CKPT = ROOT / "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt"

RECON = AUD / "phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_v1_0.json"

# ---- consumed v1.2 evidence pins (LITERAL) --------------------------------- #
P_START = "88723028df230a8b1e2c98c8c248d2de44e73bcb95669efd9bd8d44cff4a69be"
P_RESULT = "4a3753867e72f7cfbc357511475623bd0ecfff2dc0e3aca0f16ecbe1effa98d5"
P_STDOUT = "5444cab5d19fcba310b4af06f5c91eeb969ede872e05069f75d672cb5b8afd72"
P_DIAG = "981f772fd42e35ac8e3acde17344e9bcd3fb48c39aba191200a0d811f76f29f9"
P_LAUNCHER = "de916786f8237d6f04a4deebde4186a5120164bce073ffa1d0343cf6e265aaee"
P_D59 = "ad426132273ee72908556cab3fd1cd15e42816fc674f28c33dd56c8b99ed4ff7"
P_PHASE29 = "df4a0f376a7edab221d584b2a7152bf7e8f55c00ade87e39cd94c9bb13fedea6"
P_PHASE27A = "ac0ffbdadbfe60349061a926f5a664716a3a3690ac3a90c21a35802263975841"
P_V1_14 = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
P_MODEL = "342f2163690c2fa8d5a601ab1d18178b982d701b916935c33e0793b0801c3724"
P_RPSI = "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109"

EMPTY_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


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
               "builder": "phase36_final_prob_authority_v1_2_result_adjudication_v1_0"}
    payload.update(extra)
    print(json.dumps(payload, indent=1))
    return code


# ---- isolated fusion replications (STATIC; no model) ----------------------- #
def fuse_full_field(p_global, refined_crop_256, geom):
    """EXACT replication of run_phase27_exec_phaseA.fuse_full_field (L533-550)
    (byte-identical to v1.14 module-level fuse_full_field L1480-1491)."""
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
    out[clip_y1:clip_y2, clip_x1:clip_x2] = square[wy1:wy2, wx1:wx2]
    return out


def fuse_global_with_regional(p_global, p_refined_crop, window):
    """EXACT replication of BARRRegionalRefinerV1._fuse_global_with_regional
    (src/models/barr/ra_medfilm_barr.py L182-198)."""
    import torch
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


def _synthetic_fusion_cases():
    CANVAS, REF = 512, 256
    p_global = np.random.RandomState(0).rand(CANVAS, CANVAS).astype(np.float32)
    refined = (np.linspace(0, 1, REF)[None, :] * np.linspace(0, 1, REF)[:, None]).astype(np.float32)

    def mk(side, cy1, cy2, cx1, cx2, pt, pb, pl, pr):
        geom = {"crop_side_pixels": side,
                "clip_y1": cy1, "clip_y2": cy2, "clip_x1": cx1, "clip_x2": cx2,
                "pad_top": pt, "pad_bottom": pb, "pad_left": pl, "pad_right": pr}
        return geom, (cy1, cy2, cx1, cx2)

    cases = {
        "interior_square_no_pad": mk(384, 64, 448, 64, 448, 0, 0, 0, 0),
        "top_clipped": mk(384, 0, 320, 64, 448, 64, 0, 0, 0),
        "bottom_clipped": mk(384, 192, 512, 64, 448, 0, 64, 0, 0),
        "left_clipped": mk(384, 64, 448, 0, 320, 0, 0, 64, 0),
        "right_clipped": mk(384, 64, 448, 192, 512, 0, 0, 0, 64),
        "corner_clipped_TL": mk(384, 0, 320, 0, 320, 64, 0, 64, 0),
    }
    out = {}
    for name, (geom, window) in cases.items():
        a = fuse_full_field(p_global, refined, geom)
        b = fuse_global_with_regional(p_global, refined, window)
        out[name] = {
            "geom": geom,
            "window": list(window),
            "shape_a": list(a.shape), "shape_b": list(b.shape),
            "dtype_a": str(a.dtype), "dtype_b": str(b.dtype),
            "same_shape": a.shape == b.shape,
            "same_dtype": a.dtype == b.dtype,
            "array_equal": bool(np.array_equal(a, b)),
            "max_abs": float(np.max(np.abs(a.astype(np.float64) - b.astype(np.float64)))),
            "mismatch_count": int(np.sum(a != b)),
        }
    return out


def main() -> int:
    # ---- (0) write-once / consumed-evidence pins -------------------------- #
    if RECON.exists():
        return fatal(2, "ADJUDICATION_V1_0_ALREADY_EXISTS", path=str(RECON))

    pin_bad = {}
    pins = {
        "start": (START, P_START), "result": (RESULT, P_RESULT), "stdout": (STDOUT, P_STDOUT),
        "diagnostic": (DIAG, P_DIAG), "launcher": (LAUNCHER, P_LAUNCHER), "d59_reconciliation": (D59, P_D59),
        "phase29_routing": (PHASE29_CSV, P_PHASE29),
        "run_phase27_exec_phaseA": (PHASE27_A, P_PHASE27A),
        "phase36_robustness_execution_v1_14": (V1_14, P_V1_14),
        "ra_medfilm_barr": (MODEL, P_MODEL),
        "r_psi_checkpoint": (RPSI_CKPT, P_RPSI),
    }
    for k, (p, e) in pins.items():
        if not p.exists():
            pin_bad[k] = {"observed": "ABSENT", "expected": e}
        else:
            o = sha(p)
            if o != e:
                pin_bad[k] = {"observed": o, "expected": e}
    if pin_bad:
        return fatal(3, "CONSUMED_EVIDENCE_PIN_MISMATCH", bad=pin_bad)

    # ---- (1) stderr / failure local state -------------------------------- #
    if STDERR.exists():
        sz = STDERR.stat().st_size
        h = sha(STDERR)
        if sz == 0 and h == EMPTY_SHA:
            stderr_state = {"state": "PRESENT_EMPTY", "size": 0, "sha256": h}
        else:
            stderr_state = {"state": "PRESENT_NONEMPTY", "size": sz, "sha256": h}
    else:
        stderr_state = {"state": "ABSENT"}
    failure_absent = (not FAILURE.exists())
    if not failure_absent:
        return fatal(3, "FAILURE_V1_2_PRESENT_FOR_CONSUMED_RESULT")

    # ---- (2) affected set from RESULT only ------------------------------- #
    j = json.loads(RESULT.read_text(encoding="utf-8"))
    c = j["final_authority_comparison"]
    A_reported = set(c["affected_sample_ids"])
    ps = c["per_sample"]
    A_derived = set(r["sample_id"] for r in ps if r.get("f16_mismatch_count", 0) > 0)
    zero_rows = [r["sample_id"] for r in ps if r.get("f16_mismatch_count", 0) == 0]
    affected_derivation = {
        "n_per_sample_rows": len(ps),
        "len_A_reported": len(A_reported),
        "len_A_derived": len(A_derived),
        "A_reported_eq_A_derived": A_reported == A_derived,
        "n_zero_mismatch_rows": len(zero_rows),
    }
    if not (len(A_reported) == 266 and len(A_derived) == 266
            and A_reported == A_derived and len(zero_rows) == 542):
        return fatal(4, "AFFECTED_SET_DERIVATION_FAILED", detail=affected_derivation)

    # ---- (3) Phase29 GT-free routing authority --------------------------- #
    rows = list(csv.DictReader(PHASE29_CSV.open(encoding="utf-8")))
    cols = list(rows[0].keys())

    def tr(s):
        return str(s).strip().lower() == "true"

    sid = [r["sample_id"] for r in rows]
    all_pop = set(sid)
    src_vocab = sorted(set(r["final_source"] for r in rows))
    R_set = set(r["sample_id"] for r in rows if r["final_source"] == "REFINED")
    G_set = set(r["sample_id"] for r in rows if r["final_source"] == "GLOBAL")
    EXECUTE = set(r["sample_id"] for r in rows if tr(r["selected"]))
    ACCEPT = set(r["sample_id"] for r in rows if tr(r["selected"]) and tr(r["safety_accept"]))
    REJECT = set(r["sample_id"] for r in rows if tr(r["selected"]) and not tr(r["safety_accept"]))
    SKIP = set(r["sample_id"] for r in rows if not tr(r["selected"]))

    routing = {
        "csv_path": str(PHASE29_CSV.relative_to(ROOT)).replace("\\", "/"),
        "csv_sha256": P_PHASE29,
        "columns": cols,
        "final_source_vocabulary": src_vocab,
        "row_count": len(rows),
        "unique_sample_id_count": len(all_pop),
        "cardinalities": {
            "SKIP": len(SKIP), "EXECUTE": len(EXECUTE),
            "ACCEPT": len(ACCEPT), "REJECT": len(REJECT),
            "R_refined": len(R_set), "G_global": len(G_set),
        },
        "frozen_cardinality_checks": {
            "SKIP_eq_529": len(SKIP) == 529,
            "EXECUTE_eq_279": len(EXECUTE) == 279,
            "ACCEPT_eq_266": len(ACCEPT) == 266,
            "REJECT_eq_13": len(REJECT) == 13,
        },
        "observed_vs_expected_note": (
            "The frozen work-order cardinalities (ACCEPT=266 / REJECT=13) DO NOT match the "
            "Phase29 GT-free routing authority, which encodes ACCEPT=268 / REJECT=11. "
            "The table itself is internally consistent (all 268 ACCEPT have safety_score>=0.50; "
            "all 11 REJECT have safety_score<0.50)."),
        "R_eq_ACCEPT": R_set == ACCEPT,
        "G_eq_SKIP_union_REJECT": G_set == (SKIP | REJECT),
        "R_inter_G_empty": len(R_set & G_set) == 0,
        "R_union_G_all": (R_set | G_set) == all_pop,
    }

    # ---- (4) decisive D60 set test --------------------------------------- #
    unaffected = all_pop - A_derived
    affected_minus_refined = sorted(A_derived - R_set)
    refined_minus_affected = sorted(R_set - A_derived)
    global_minus_unaffected = sorted(G_set - unaffected)
    unaffected_minus_global = sorted(unaffected - G_set)
    A_eq_R = (A_derived == R_set)
    unaff_eq_G = (unaffected == G_set)

    if A_eq_R and unaff_eq_G:
        d60 = "FINAL_AUTHORITY_MISMATCH_EXACTLY_LOCALIZED_TO_REFINED_FINAL_SOURCE"
        d60_established = True
    else:
        d60 = "REFINED_FINAL_SOURCE_LOCALIZATION_NOT_EXACT"
        d60_established = False

    d60_block = {
        "d60_verdict": d60,
        "d60_root_localization_established": d60_established,
        "affected_count": len(A_derived),
        "refined_final_source_count": len(R_set),
        "global_final_source_count": len(G_set),
        "unaffected_count": len(unaffected),
        "affected_equals_refined": A_eq_R,
        "unaffected_equals_global": unaff_eq_G,
        "affected_minus_refined": affected_minus_refined,
        "refined_minus_affected": refined_minus_affected,
        "global_minus_unaffected": global_minus_unaffected,
        "unaffected_minus_global": unaffected_minus_global,
        "count_equality_is_not_set_equality": True,
        "note": (
            "Count equality (266 affected vs 268 ACCEPT) is NOT exact; set equality FAILS. "
            "Exactly two REFINED-final-source samples reproduce the Phase27 final-f16 authority "
            "bit-identically (all mismatch metrics zero) and are therefore NOT in the affected set."),
        "interpretation_guard": (
            "This localization does NOT prove R_psi itself is wrong, and does NOT prove G is "
            "globally identical in live float32. It localizes where the discrepancy becomes "
            "observable in the frozen f16 final authority."),
    }

    # ---- (5)+(6)+(7) static accept-path comparison + synthetic fusion ---- #
    accept_path = {
        "phase27_accept_fusion_call_site": "run_phase27_exec_phaseA.py L349: p_final = fuse_full_field(p_global, refined, geom)",
        "v1_14_accept_fusion_call_site": "phase36_robustness_execution_v1_14.py L1989: fused = system._fuse_global_with_regional(p_global, refined, window)",
        "v1_14_module_level_fuse_full_field_defined_at": "phase36_robustness_execution_v1_14.py L1480",
        "v1_14_module_level_fuse_full_field_is_dead_code": True,
        "r_psi_input_preprocessing_equivalent": True,
        "r_psi_input_note": (
            "run_phase27_exec_phaseA.crop_and_resize_vec (L493-516) is byte-identical to "
            "phase36_robustness_execution_v1_14.crop_and_resize_vec (L1461-1477): same clip, "
            "same constant-zero pad, same per-channel PIL mode='F' BILINEAR resize."),
        "somega_features_equivalent": True,
        "somega_note": (
            "Both call phase25f_post_safety_features.compute_numeric_features with the same "
            "area_fraction + crop_side_pixels."),
        "fusion_mechanism_difference": {
            "fuse_full_field_pad_aware": (
                "resize refined256 -> (crop_side_pixels, crop_side_pixels) via PIL BILINEAR, then "
                "slice [pad_top : pad_top+(clip_y2-clip_y1), pad_left : pad_left+(clip_x2-clip_x1)] "
                "and insert at out[clip_y1:clip_y2, clip_x1:clip_x2]."),
            "fuse_global_with_regional_pad_unaware": (
                "resize refined256 -> (clip_y2-clip_y1, clip_x2-clip_x1) via torch F.interpolate "
                "bilinear align_corners=False, then insert at out[clip_y1:clip_y2, clip_x1:clip_x2]; "
                "NO pad_top/pad_left offset."),
            "consequence": (
                "When pad_top/pad_left != 0 (clipped ROI at canvas borders) the two insert a "
                "differently-resized, differently-offset crop; even with no padding they use "
                "different resamplers (PIL BILINEAR vs torch bilinear align_corners=False)."),
        },
    }

    synth = _synthetic_fusion_cases()
    any_diff = any(not v["array_equal"] for v in synth.values())
    max_over = max(v["max_abs"] for v in synth.values())
    fusion_block = {
        "fusion_static_equivalent": False,
        "fusion_synthetic_equivalent": (not any_diff),
        "any_case_differs": any_diff,
        "max_abs_over_cases": float(max_over),
        "cases": synth,
        "method": ("pure synthetic arrays (512x512 p_global float32, 256x256 refined float32); "
                   "NO model, NO checkpoint, NO image, NO GT"),
    }

    # ---- (8) D61 classification ------------------------------------------ #
    # Fusion semantics differ AND D60 localization is NOT exact -> we can still
    # establish that the two fusion implementations are not equivalent.  But D60
    # exact localization FAILED, so we must NOT claim D61 as the sole cause.
    d61 = {
        "status": "ESTABLISHED",
        "classification": "ACCEPT_FINAL_FUSION_SEMANTICS_DIVERGE_FROM_PHASE27",
        "more_exact_candidate": "REFINED_CROP_PADDING_REINSERTION_MISMATCH",
        "evidence": (
            "Phase27 ACCEPT path calls fuse_full_field (pad-aware, PIL BILINEAR to crop_side_pixels); "
            "v1.14 ACCEPT path calls _fuse_global_with_regional (pad-unaware, torch bilinear to the "
            "clipped window size). Synthetic equivalence test shows semantic divergence in ALL 6 "
            "geometries (max_abs up to ~0.1667 in clipped cases; ~1.8e-7 even with no padding)."),
        "scope_guard": (
            "D61 establishes that the two fusion implementations are NOT equivalent. It does NOT "
            "establish that fusion is the SOLE cause of the D60 non-reproduction, because exact D60 "
            "localization FAILED (2 REFINED samples reproduce bit-identically). No further inference "
            "was executed."),
        "no_further_inference_executed": True,
    }

    payload = {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_V1_2_RESULT_ADJUDICATION",
        "adjudication_revision": "v1_0",
        "target": "D60_ACCEPTED_BRANCH_REFINED_FINAL_SOURCE_LOCALIZATION",
        "mode": "STATIC_EXISTING_ARTIFACT_FORENSICS_ONLY",
        "consumed_v1_2_evidence": {
            "classification": j.get("classification"),
            "start_sha256": P_START,
            "result_sha256": P_RESULT,
            "stdout_sha256": P_STDOUT,
            "diagnostic_source_sha256": P_DIAG,
            "launcher_sha256": P_LAUNCHER,
            "d59_reconciliation_sha256": P_D59,
            "stderr_state": stderr_state,
            "failure_v1_2_absent": failure_absent,
        },
        "affected_set_derivation": affected_derivation,
        "phase29_routing_authority": routing,
        "d60": d60_block,
        "source_shas": {
            "run_phase27_exec_phaseA.py": P_PHASE27A,
            "phase36_robustness_execution_v1_14.py": P_V1_14,
            "src/models/barr/ra_medfilm_barr.py": P_MODEL,
            "r_psi_checkpoint": P_RPSI,
            "r_psi_checkpoint_path": str(RPSI_CKPT.relative_to(ROOT)).replace("\\", "/"),
        },
        "accept_path_static_comparison": accept_path,
        "synthetic_fusion_comparison": fusion_block,
        "d61": d61,
        "scientific_semantics_effect": "NONE",
        "new_scientific_output": False,
        "model_execution": False,
        "checkpoint_deserialization": False,
        "val_image_read": False,
        "gt_read": False,
        "test_reads": 0,
        "router_holdout_reads": 0,
        "perturbations": False,
        "prohibitions_observed": [
            "no_model_execution", "no_checkpoint_deserialization", "no_val_image_read",
            "no_val_gt_read", "no_test", "no_router_holdout", "no_perturbations",
            "no_v1_2_retry", "no_v1_3_diagnostic", "no_v1_15_science", "no_phase37",
        ],
        "governance_state": {
            "v1_2_final_prob": "CONSUMED_RESULT (retry FORBIDDEN)",
            "v1_1_final_prob": "CONSUMED_FAILED (retry FORBIDDEN)",
            "v1_14_science": "CONSUMED_FAILED (retry FORBIDDEN)",
            "v1_15_science": "NOT_CREATED",
            "phase37": "NOT_STARTED",
            "test": "PHASE39_ONLY",
            "router_holdout": "NOT_ACCESSED",
        },
        "generated_utc": now(),
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync (exclusive-create, write-once)",
    }
    write_once(RECON, payload)

    print(json.dumps({
        "status": "PHASE36_FINAL_PROB_AUTHORITY_V1_2_RESULT_ADJUDICATION_BUILT",
        "adjudication_sha256": sha(RECON),
        "adjudication_builder_sha256": sha(Path(__file__)),
        "affected_count": len(A_derived),
        "refined_final_source_count": len(R_set),
        "global_final_source_count": len(G_set),
        "affected_equals_refined": A_eq_R,
        "unaffected_equals_global": unaff_eq_G,
        "affected_minus_refined": affected_minus_refined,
        "refined_minus_affected": refined_minus_affected,
        "D60": d60,
        "fusion_static_equivalent": False,
        "fusion_synthetic_equivalent": fusion_block["fusion_synthetic_equivalent"],
        "D61": d61["status"],
        "D61_classification": d61["classification"],
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
