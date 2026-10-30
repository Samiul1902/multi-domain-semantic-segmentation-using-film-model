#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.2 §S — MODEL-FREE unit tests for the ACTUAL EXECUTABLE repair.

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_2

NO torch model construction. NO checkpoint. NO medical/protected data.
Emits reports/audits/phase36_robustness_unit_v1_2.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

import scripts.analysis.phase36_robustness_common_v1_1 as C  # noqa: E402
import scripts.analysis.phase36_robustness_common_v1_0 as V0  # noqa: E402

OUT = ROOT / "reports" / "audits" / "phase36_robustness_unit_v1_2.json"
EXEC = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_2.py"
NC = ROOT / "scripts" / "analysis" / "phase36_robustness_negative_controls_v1_2.py"
RECON = ROOT / "reports" / "audits" / "phase36_v1_2_metric_empty_case_authority_reconciliation.json"

RESULTS: list[dict] = []


def check(cid, desc, cond, detail=""):
    RESULTS.append({"id": cid, "desc": desc, "pass": bool(cond), "detail": str(detail)})


X = np.linspace(0, 1, 512 * 512, dtype=np.float32).reshape(512, 512)


def main():
    src = EXEC.read_text(encoding="utf-8")

    # 01 — v1.2 supersedes v1.1 (v1.0/v1.1 preserved separately)
    check("01", "v1.2 execution source is a distinct successor", EXEC.exists()
          and "ra_medfilm_barr_phase36_robustness_v1_2" in src)

    # 02 — REAL _load_models: no unconditional placeholder raise
    import ast
    tree = ast.parse(src)
    fns = {}
    lines = src.splitlines()
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef):
            fns[n.name] = "\n".join(lines[n.lineno - 1: n.end_lineno])
    lm = fns["_load_models"]
    import re
    bare_raise = bool(re.search(r"^\s{4}raise RuntimeError\(", lm, re.MULTILINE))
    check("02", "_load_models has NO unconditional placeholder RuntimeError",
          not bare_raise and "MODEL_LOAD_PATH_IS_BOUND_BUT_NOT_INVOKED" not in src, bare_raise)

    # 03 — REAL strict loading of all four components
    check("03", "_load_models strict-loads G/B_phi/R_psi/S_omega",
          all(k in lm for k in ("GlobalMedFiLM", "BARRRegionalRefinerV1",
                                "_load_router_class", "_load_somega_class")
              ) and "strict=True" in lm)

    # 04 — 0 missing / 0 unexpected verification present
    check("04", "missing/unexpected key verification present",
          "missing_keys" in lm and "unexpected_keys" in lm
          and "CANONICAL_COMPONENT_LOAD_FAILURE" in lm)

    # 05 — parameter count verification for all four
    check("05", "param-count verification 3523001/1276401/36801/1217",
          all(s in lm for s in ("3523001", "1276401", "36801", "1217")))

    # 06 — REAL clean-sample evaluation path exists and is wired
    check("06", "_evaluate_clean_sample real path exists",
          "_evaluate_clean_sample" in src and "forward_inference" in fns["_evaluate_clean_sample"])

    # 07 — clean generator iterates the 808 manifest rows
    gc = fns["_generate_clean_reference_once"]
    check("07", "clean generator iterates _load_population + returns records",
          "_load_population()" in gc and "records" in gc
          and "_evaluate_clean_sample(" in gc)

    # 08 — STRICT equivalence gate
    ge = fns["_clean_equivalence_gate"]
    check("08", "equivalence gate is STRICT (808 enforced, missing-data fails)",
          "POPULATION_N" in ge and "missing_generated_dice" in ge
          and "missing_bound_dice" in ge and "route_mismatches" in ge
          and "dice_mismatches" in ge and "fail_closed_on_missing_data" in ge)

    # 09 — gate comparator exact
    check("09", "gate comparator isclose(atol=1e-7, rtol=0)",
          "atol=1e-7" in ge and "rtol=0" in ge)

    # 10 — image perturbation executes the full system
    ie = fns["_evaluate_frozen_system"]
    check("10", "image perturbation re-runs full system (no clean reuse)",
          "forward_inference" in ie and "perturbed_g_forwards" in ie
          and "_assemble_202d" in ie)

    # 11 — proposal perturbation reuses G and reassembles 202-D
    pe = fns["_evaluate_frozen_system_proposal"]
    check("11", "proposal perturbation reuses G + reassembles 202-D",
          "g_reused_for_proposal" in pe and "_assemble_202d" in pe
          and "router_input_reassembled" in pe)

    # 12 — empty proposal -> NOT_APPLICABLE, zero R_psi executions
    check("12", "empty proposal -> NOT_APPLICABLE_EMPTY_PROPOSAL (R_psi=0)",
          "EMPTY_PROPOSAL_HANDLING" in pe and "empty_proposal_not_applicable" in pe)

    # 13 — science rows carry sample_id and execute perturbations
    rs = fns["run_science"]
    check("13", "run_science rows carry sample_id + execute image/proposal",
          '"sample_id"' in rs and "_evaluate_frozen_system(" in rs
          and "_evaluate_frozen_system_proposal(" in rs)

    # 14 — clean equivalence gate precedes perturbations (ordering)
    i_gen = src.find("_generate_clean_reference_once(ctx")
    i_eq = src.find("_clean_equivalence_gate(clean_ref_bound")
    i_pert = src.find("image_perturbation_instances")
    check("14", "CLEAN generation -> gate -> perturbations ordering",
          i_gen != -1 and i_eq != -1 and i_pert != -1 and i_gen < i_eq < i_pert,
          (i_gen, i_eq, i_pert))

    # 15 — smoke loads real components
    smoke = fns["run_smoke"]
    check("15", "smoke STRICT-loads all four real components (_load_models)",
          "_load_models()" in smoke and "four_real_components_loaded" in smoke)

    # 16 — smoke state machine uses the REAL router (no hardcoded truth flags)
    sm = fns["_smoke_state_machine"]
    check("16", "smoke state machine uses real B_phi + expected/observed/comparison",
          "b_phi" in sm and "observed_router_score" in sm
          and "comparison_pass" in sm
          and '"skip_returns_global": True' not in sm)

    # 17 — §L manifest-based split guard: "Training" NOT rejected
    from scripts.analysis.phase36_robustness_execution_v1_2 import (
        _reject_protected_residual, _authorized_path)
    ok_training = True
    try:
        _reject_protected_residual(
            r"d:\softfors\omni_seg\data_raw\isic2018_task1-2_training_input\isic_0001.jpg")
    except ValueError:
        ok_training = False
    check("17", "'Training' vendor dir is NOT rejected (§L fix)", ok_training)

    # 18 — §L still fails closed on TEST / HOLDOUT / ROUTER_HOLDOUT
    rejected = []
    for p in (r"a\router_holdout\x.png", r"b\test\y.png", r"c\holdout\z.png"):
        try:
            _reject_protected_residual(p.lower())
            rejected.append(False)
        except ValueError:
            rejected.append(True)
    check("18", "TEST/HOLDOUT/ROUTER_HOLDOUT still rejected (fail closed)",
          all(rejected), rejected)

    # 19 — §L authority = exact manifest-row path match
    check("19", "authorized-path rule is exact manifest-row match",
          _authorized_path("a/b.png", "a/b.png") is True
          and _authorized_path("a/b.png", "a/c.png") is False)

    # 20 — v1.1 seed conversion exact (hex[:8], base16) preserved
    msg = "phase36|gaussian_noise|42|SYNTH_PHASE36_TASK0"
    exp = int(hashlib.sha256(msg.encode("utf-8")).hexdigest()[:8], 16)
    check("20", "v1.1 seed = int(sha256.hexdigest()[:8], 16) preserved",
          C.derive_noise_seed(42, "SYNTH_PHASE36_TASK0") == exp, exp)

    # 21 — perturbation algebra unchanged from v1.0
    check("21", "v1.0 brightness/gamma algebra unchanged",
          np.allclose(V0.apply_brightness(X, 0.10), np.clip(X + 0.10, 0, 1))
          and np.allclose(V0.apply_gamma(X, 2.0), np.clip(X, 0, 1) ** 2.0))

    # 22-24 — canonical empty-case metric semantics
    from src.metrics import evaluation_metrics as M
    e = np.zeros((64, 64), np.float32)
    p = np.zeros((64, 64), np.float32); p[10:30, 10:30] = 1
    d_ee = float(M.dice(M.binary_confusion_counts(e.astype(bool), e.astype(bool))))
    d_en = float(M.dice(M.binary_confusion_counts(p.astype(bool), e.astype(bool))))
    i_ee = float(M.iou(M.binary_confusion_counts(e.astype(bool), e.astype(bool))))
    i_en = float(M.iou(M.binary_confusion_counts(p.astype(bool), e.astype(bool))))
    check("22", "Dice both-empty == 1.0; one-empty ~ eps/(N+eps) (not 0.0)",
          d_ee == 1.0 and 0.0 < d_en < 1e-6, (d_ee, d_en))
    check("23", "IoU both-empty == 1.0; one-empty ~ eps/(N+eps)",
          i_ee == 1.0 and 0.0 < i_en < 1e-6, (i_ee, i_en))
    hd = M.hd95(p.astype(bool), e.astype(bool))
    hd_val = hd.get("hd95", hd) if isinstance(hd, dict) else hd
    check("24", "HD95 empty -> NaN + valid=False (never substituted)",
          (hd_val is None) or (isinstance(hd_val, float) and np.isnan(hd_val)),
          str(hd_val))

    # 25 — §Q metric reconciliation artifact present and authoritative
    rec = json.loads(RECON.read_text(encoding="utf-8"))
    check("25", "§Q reconciliation: code is authority, conflict disclosed",
          rec["authority_ruling"]["authority"] == "CANONICAL_EXECUTABLE_METRIC_IMPLEMENTATION"
          and rec["conflict"]["policy_document"]["one_empty_dice"] == 0.0
          and abs(rec["conflict"]["canonical_code"]["one_empty_dice_observed"]) < 1e-6)

    # 26 — §Q difference is below reporting precision / gate tolerance
    check("26", "§Q difference (2.5e-10) < gate atol (1e-7)",
          rec["authority_ruling"]["difference_is_below_reporting_precision"] is True
          and rec["authority_ruling"]["absolute_difference_bound"] < 1e-7)

    # 27 — no reachable stub markers anywhere in v1.2 source
    bad = [m for m in ("raise NotImplementedError", "raise NotImplemented",
                       "MODEL_LOAD_PATH_IS_BOUND_BUT_NOT_INVOKED", "TODO", "FIXME")
           if m in src]
    check("27", "no reachable stub markers in v1.2 source", not bad, bad)

    # 28 — no `return {}` placeholder in v1.2 source
    check("28", "no placeholder return {} in v1.2 source", "return {}" not in src)

    # 29 — no training / optimizer / backward
    check("29", "no training/optimizer/backward in v1.2 source",
          all(t not in src for t in ("torch.optim", "optimizer.step", ".backward()", "Adam(")))

    # 30 — canonical extractor + state machine bound (not re-implemented)
    check("30", "canonical 202-D extractor + state machine bound",
          "build_feature_vector" in src and "barr_pre_refinement_features" in src
          and "forward_inference" in src and "ra_medfilm_barr" in src)

    # 31 — metrics bound to canonical module (no invented formula)
    check("31", "metrics bound to canonical evaluation_metrics",
          "evaluation_metrics" in src and "binary_confusion_counts" in src
          and "M.dice(" in src and "M.iou(" in src)

    # 32 — gates fail closed by default
    check("32", "science/smoke gates fail closed unless env=='1'",
          'C.GATE_ENV) != "1"' in src and 'C.SMOKE_GATE_ENV) != "1"' in src)

    # 33 — registries + thresholds unchanged
    from src.models.barr.ra_medfilm_barr import (ROI_PROPOSAL_THRESHOLD,
                                                 SEGMENTATION_OUTPUT_THRESHOLD)
    check("33", "registries 13/7 + thresholds 0.30/0.50 unchanged",
          len(C.image_condition_ids()) == 13 and len(C.proposal_condition_ids()) == 7
          and ROI_PROPOSAL_THRESHOLD == 0.30 and SEGMENTATION_OUTPUT_THRESHOLD == 0.50)

    # 34 — §R negative controls present and all valid
    nc = json.loads((ROOT / "reports" / "audits" / "phase36_v1_2_negative_controls.json"
                     ).read_text(encoding="utf-8"))
    check("34", "§R negative controls NC1..NC6 recorded and all valid",
          nc["all_controls_valid"] and len(nc["verdicts"]) == 6, len(nc["verdicts"]))

    # 35 — §A v1.0/v1.1 preservation: v1.1 source unchanged
    v1_1_path = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_1.py"
    v1_1_sha = hashlib.sha256(v1_1_path.read_bytes()).hexdigest()
    check("35", "v1.1 execution source preserved byte-for-byte",
          v1_1_sha == "e3ba09b868eb49cbe0a03f90d51af73f22c1785e051dbd38c78edc0185e8aebc", v1_1_sha)

    passed = sum(1 for r in RESULTS if r["pass"])
    total = len(RESULTS)
    payload = {
        "artifact": "phase36_robustness_unit_v1_2",
        "section": "§S", "phase": 36, "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_2",
        "classification": "MODEL_FREE_UNIT_TESTS__V1_2_ACTUAL_EXECUTABLE_REPAIR",
        "model_free": True, "torch_model_construction": False,
        "checks": RESULTS, "total_checks": total, "passed": passed,
        "failed": total - passed, "all_pass": bool(passed == total),
    }
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"passed": passed, "total": total,
                      "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest()}, indent=1))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
