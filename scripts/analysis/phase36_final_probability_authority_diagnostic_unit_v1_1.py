#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.1 — UNIT TESTS (no model, no CUDA).

Mutation-sensitive validator suite for the v1.1 family (D52/D53/D54 repairs):

  D50 controls (from v1.0):
   1. no call to mod._verify_transitive_source_integrity (diag + launcher)
   2. no source/launcher assignment to PHASE36_V1_14_LAUNCH_AUTHORITY
   3. inherited foreign v1.14 token => fail closed BEFORE marker
   4. source transitive maps exactly equal manifest maps
   5-9. dependency/checkpoint removal + SHA mutation + unexpected launcher_sha256
   10. exact v1.14 source mutation detected
  D52:
   11. final authority present + SHA + header shape + dtype + sample-order (real tree)
   12. authority missing detected
   13. authority SHA mutation detected
   14. wrong shape detected
   15. wrong dtype detected
   16. sample-order mismatch detected (manifest reorder)
   17. sample-order mismatch detected (fg-pixel row binding)
  D53:
   18. GT guard mutates the shared runtime state (VAL_GT_READ increments)
   19. failure artifact records the ACTUAL VAL_GT_READ + blocked_gt_calls (not hardcoded 0)
  D54:
   20. computed evidence survives a result-write failure
  finite:
   21. _finite_check rejects NaN/+inf/-inf; _record_nonfinite preserves ids+counts
   22. non-finite evidence survives in a failure artifact
  GT wording / content:
   23. no GT-content callable is actually called; no mask_path subscript read
   24. GT_CONTENT_INVARIANT declares metadata access permitted
  other:
   25. launch authority required before marker; guarded write; no torch.load
   26. forbidden science/perturbation unreachable
   27. consumed-evidence (v1.2/D51) mutation detected
   28. v1.0 source preserved byte-for-byte

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\phase36_final_probability_authority_diagnostic_unit_v1_1.py
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import types
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts" / "analysis"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

DIAG = ROOT / "scripts" / "analysis" / "phase36_final_probability_authority_diagnostic_v1_1.py"
LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_final_probability_authority_diagnostic_v1_1.py"
V14 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
MANIFEST = ROOT / "reports" / "audits" / "phase36_v1_14_runtime_source_integrity_manifest.json"

RESULTS: list = []


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def check(name, ok, detail=None):
    RESULTS.append({"name": name, "ok": bool(ok), "detail": detail})


def _tree(path: Path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _find_func(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


def _has_actual_call(tree, fname):
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            nm = getattr(f, "id", None) or getattr(f, "attr", None)
            if nm == fname:
                out.append(n.lineno)
    return out


def _env_subscript_writes(tree):
    writes = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Attribute) \
                        and t.value.attr == "environ":
                    sl = t.slice
                    if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                        writes.add(sl.value)
    return writes


def _subscript_read_keys(tree):
    keys = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Subscript):
            sl = n.slice
            if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                keys.add(sl.value)
    return keys


V1_0_PINS = {
    "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_0.py":
        "89673c6fe6a86d1abe04a5987c0675bc5c5246e24c98979bc7649431b87b319f",
    "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_0.py":
        "f77b9fd4226cc2eb7a71d84b07e06d28719d7f56fc7ef10f842005f7656ccdc6",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_0.py":
        "7cccd24cfaba2ecb243871aa44389c4f8c88b5ce782972e8d41be13e34ba5acf",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_0.py":
        "a7d13d122f8aaeb522ec213968917085aa79804caaafa7aecd835fead74591c3",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_0.py":
        "126d95548179fd5886e2687f84ca1927c60c0c30b75f6e929f211ecd4759df86",
}

GT_CALLABLES = ("_load_val_gt", "full_field_gt", "_dice", "_iou", "_hd95")


def _save(mod, *names):
    return {n: getattr(mod, n) for n in names}


def _restore(mod, saved):
    for n, v in saved.items():
        setattr(mod, n, v)


def main() -> int:
    diag_src = DIAG.read_text(encoding="utf-8")
    launch_src = LAUNCHER.read_text(encoding="utf-8")
    diag_tree = _tree(DIAG)
    launch_tree = _tree(LAUNCHER)

    diag_mod = _load(DIAG, "_diag_fpa_v11_ut")
    launch_mod = _load(LAUNCHER, "_launch_fpa_v11_ut")
    FOREIGN = launch_mod.FOREIGN_V1_14_LAUNCH_TOKEN

    # ---------------- D50 (1) no forbidden gate call -------------------------- #
    check("REQ1_no_forbidden_gate_call_in_diagnostic",
          not _has_actual_call(diag_tree, "_verify_transitive_source_integrity"))
    check("REQ1_no_forbidden_gate_call_in_launcher",
          not _has_actual_call(launch_tree, "_verify_transitive_source_integrity"))
    check("REQ1_diagnostic_marks_omission", "d50_foreign_gate_call_omitted" in diag_src)

    # ---------------- D50 (2) no foreign-token write -------------------------- #
    check("REQ2_diagnostic_no_foreign_token_write", FOREIGN not in _env_subscript_writes(diag_tree))
    check("REQ2_launcher_no_foreign_token_write", FOREIGN not in _env_subscript_writes(launch_tree))

    # ---------------- D50 (3) foreign token => fail closed -------------------- #
    saved_env = {k: os.environ.pop(k, None)
                 for k in (diag_mod.ONE_SHOT_ENV, diag_mod.LAUNCH_AUTHORITY_TOKEN,
                           diag_mod.FOREIGN_V1_14_LAUNCH_TOKEN)}
    os.environ[diag_mod.ONE_SHOT_ENV] = "1"
    os.environ[diag_mod.LAUNCH_AUTHORITY_TOKEN] = "1"
    os.environ[diag_mod.FOREIGN_V1_14_LAUNCH_TOKEN] = "1"
    try:
        rc_foreign = diag_mod.main()
    finally:
        os.environ.pop(diag_mod.FOREIGN_V1_14_LAUNCH_TOKEN, None)
        os.environ.pop(diag_mod.ONE_SHOT_ENV, None)
        os.environ.pop(diag_mod.LAUNCH_AUTHORITY_TOKEN, None)
    check("REQ3_diagnostic_refuses_when_foreign_token_present", rc_foreign == 8, {"rc": rc_foreign})
    check("REQ3_no_marker_when_foreign_token_present", not diag_mod.DIAGNOSTIC_START.exists())
    check("REQ3_launcher_foreign_gate_flags_present",
          launch_mod.check_foreign_v1_14_token_absent({FOREIGN: "1"})["ok"] is False)
    for k, v in saved_env.items():
        if v is not None:
            os.environ[k] = v

    # ---------------- D50 (4) source transitive maps == manifest -------------- #
    ti = launch_mod.check_transitive_integrity()
    check("REQ4_real_tree_transitive_ok", ti["ok"] is True, {"reason": ti.get("reason")})
    check("REQ4_real_source_manifest_authority_exact_match",
          ti["source_manifest_transitive_authority_exact_match"] is True)
    check("REQ4_real_tree_is_14_4", ti["n_dependencies"] == 14 and ti["n_checkpoints"] == 4)

    # ---------------- D50 (5-9) mutation-sensitive manifest ------------------- #
    real_man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    orig_man_sha = launch_mod.FROZEN_EXPECTED_V1_14_MANIFEST_SHA

    def _run_with_manifest(mut: dict):
        with tempfile.TemporaryDirectory() as td:
            mp = Path(td) / "m.json"
            mp.write_text(json.dumps(mut), encoding="utf-8")
            try:
                launch_mod.FROZEN_EXPECTED_V1_14_MANIFEST_SHA = launch_mod.sha(mp)
                return launch_mod.check_transitive_integrity(manifest_path=mp)
            finally:
                launch_mod.FROZEN_EXPECTED_V1_14_MANIFEST_SHA = orig_man_sha

    m = json.loads(json.dumps(real_man)); m["dependencies"].pop(list(m["dependencies"].keys())[0])
    check("REQ5_dependency_removal_detected", _run_with_manifest(m)["ok"] is False)
    m = json.loads(json.dumps(real_man)); m["checkpoints"].pop(list(m["checkpoints"].keys())[0])
    check("REQ6_checkpoint_removal_detected", _run_with_manifest(m)["ok"] is False)
    m = json.loads(json.dumps(real_man)); m["dependencies"][list(m["dependencies"].keys())[0]] = "0" * 64
    check("REQ7_dependency_sha_mutation_detected", _run_with_manifest(m)["ok"] is False)
    m = json.loads(json.dumps(real_man)); m["checkpoints"][list(m["checkpoints"].keys())[0]] = "0" * 64
    check("REQ8_checkpoint_sha_mutation_detected", _run_with_manifest(m)["ok"] is False)
    m = json.loads(json.dumps(real_man)); m["launcher_sha256"] = "deadbeef"
    check("REQ9_unexpected_launcher_sha_key_detected", _run_with_manifest(m)["ok"] is False)

    # ---------------- D50 (10) v1.14 source mutation -------------------------- #
    with tempfile.TemporaryDirectory() as td:
        v_mut = Path(td) / "v14_mut.py"
        v_mut.write_bytes(V14.read_bytes() + b"\n# mutant\n")
        check("REQ10_v1_14_source_mutation_detected",
              launch_mod.check_transitive_integrity(v14_path=v_mut)["ok"] is False)

    # ================= D52 — final-authority pre-consumption gate ============= #
    fa = launch_mod.check_final_authority_preconsumption()
    check("REQ11_final_authority_real_tree_pass", fa["final_authority_preconsumption_pass"] is True,
          {"reason": fa.get("reason")})
    check("REQ11_final_authority_sha", fa["final_authority_sha256"] == launch_mod.PHASE27_FINAL_PROB_AUTHORITY_SHA)
    check("REQ11_final_authority_shape", fa["final_authority_shape"] == [808, 512, 512])
    check("REQ11_final_authority_dtype", fa["final_authority_dtype"] == "float16")
    check("REQ11_final_authority_sample_order_pass", fa["final_authority_sample_order_pass"] is True)

    saved_fa = _save(launch_mod, "PHASE27_FINAL_PROB_AUTHORITY_SHA",
                     "PHASE27_FINAL_PROB_AUTHORITY_SHAPE", "PHASE27_FINAL_PROB_AUTHORITY_DTYPE",
                     "VAL_MANIFEST", "VAL_MANIFEST_SHA", "PHASE27_SCORES_CSV", "PHASE27_SCORES_CSV_SHA")
    try:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            # 12. authority missing
            r = launch_mod.check_final_authority_preconsumption(authority_path=tdp / "nope.npy")
            check("REQ12_authority_missing_detected",
                  r["final_authority_preconsumption_pass"] is False and r["reason"] == "FINAL_AUTHORITY_ABSENT",
                  {"reason": r.get("reason")})
            # 13. authority SHA mutation
            bad = tdp / "bad.npy"
            bad.write_bytes(b"not-an-npy")
            r = launch_mod.check_final_authority_preconsumption(authority_path=bad)
            check("REQ13_authority_sha_mutation_detected",
                  r["final_authority_preconsumption_pass"] is False and r["reason"] == "FINAL_AUTHORITY_SHA_MISMATCH",
                  {"reason": r.get("reason")})
            # 14. wrong shape (SHA pin patched so the header gate fires)
            shp = tdp / "shp.npy"
            np.save(shp, np.zeros((2, 3), dtype=np.float16))
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_SHA = launch_mod.sha(shp)
            r = launch_mod.check_final_authority_preconsumption(authority_path=shp)
            check("REQ14_wrong_shape_detected",
                  r["final_authority_preconsumption_pass"] is False and r["reason"] == "FINAL_AUTHORITY_SHAPE_MISMATCH",
                  {"reason": r.get("reason")})
            # 15. wrong dtype (patch expected shape+dtype so shape passes, dtype fails)
            dt = tdp / "dt.npy"
            np.save(dt, np.zeros((2, 3), dtype=np.float32))
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_SHA = launch_mod.sha(dt)
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_SHAPE = (2, 3)
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_DTYPE = "float16"
            r = launch_mod.check_final_authority_preconsumption(authority_path=dt)
            check("REQ15_wrong_dtype_detected",
                  r["final_authority_preconsumption_pass"] is False and r["reason"] == "FINAL_AUTHORITY_DTYPE_MISMATCH",
                  {"reason": r.get("reason")})
            # restore real pins before the order tests
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_SHA = saved_fa["PHASE27_FINAL_PROB_AUTHORITY_SHA"]
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_SHAPE = saved_fa["PHASE27_FINAL_PROB_AUTHORITY_SHAPE"]
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_DTYPE = saved_fa["PHASE27_FINAL_PROB_AUTHORITY_DTYPE"]

            # 16. sample-order mismatch via a REORDERED scores CSV (SHA pin patched).
            #     The canonical order authority is derived by sorting the frozen manifest,
            #     so the manifest file's own row order is NOT an authority (a manifest
            #     tamper is caught by the pinned VAL_MANIFEST_SHA, exercised below in
            #     REQ16b).  The genuine order authority is check 5c: the Phase27 scores
            #     CSV sample_id order must equal the canonical (dataset,sample_id) order.
            import csv as _csv
            real_sc = list(_csv.DictReader((ROOT / launch_mod.PHASE27_SCORES_CSV).open(encoding="utf-8", newline="")))
            swapped = [dict(r) for r in real_sc]
            swapped[0], swapped[1] = swapped[1], swapped[0]
            osc = tdp / "scores_rev.csv"
            with osc.open("w", encoding="utf-8", newline="") as fh:
                w = _csv.DictWriter(fh, fieldnames=list(real_sc[0].keys()))
                w.writeheader()
                w.writerows(swapped)
            launch_mod.PHASE27_SCORES_CSV = str(osc)
            launch_mod.PHASE27_SCORES_CSV_SHA = launch_mod.sha(osc)
            r = launch_mod.check_final_authority_preconsumption()
            check("REQ16_sample_order_mismatch_detected_csv_order",
                  r["final_authority_preconsumption_pass"] is False
                  and r["reason"] == "FINAL_AUTHORITY_SAMPLE_ORDER_MISMATCH"
                  and r.get("sample_order_detail") == "CSV_SAMPLE_ID_ORDER != CANONICAL_(dataset,sample_id)_ORDER",
                  {"reason": r.get("reason"), "detail": r.get("sample_order_detail")})
            launch_mod.PHASE27_SCORES_CSV = saved_fa["PHASE27_SCORES_CSV"]
            launch_mod.PHASE27_SCORES_CSV_SHA = saved_fa["PHASE27_SCORES_CSV_SHA"]

            # 16b. a REORDERED manifest is caught by the pinned manifest SHA (manifest
            #      row order is not itself an authority; tampering must not slip through).
            real_man_rows = list(_csv.DictReader((ROOT / launch_mod.VAL_MANIFEST).open(encoding="utf-8", newline="")))
            rman = tdp / "val_rev.csv"
            with rman.open("w", encoding="utf-8", newline="") as fh:
                w = _csv.DictWriter(fh, fieldnames=list(real_man_rows[0].keys()))
                w.writeheader()
                w.writerows(list(reversed(real_man_rows)))
            launch_mod.VAL_MANIFEST = str(rman)  # real SHA pin left in place
            r = launch_mod.check_final_authority_preconsumption()
            check("REQ16b_reordered_manifest_detected_by_sha",
                  r["final_authority_preconsumption_pass"] is False
                  and r["reason"] == "VAL_MANIFEST_SHA_MISMATCH",
                  {"reason": r.get("reason")})
            launch_mod.VAL_MANIFEST = saved_fa["VAL_MANIFEST"]
            launch_mod.VAL_MANIFEST_SHA = saved_fa["VAL_MANIFEST_SHA"]

            # 17. sample-order mismatch via fg-pixel row binding (mutated scores CSV)
            real_sc = list(_csv.DictReader((ROOT / launch_mod.PHASE27_SCORES_CSV).open(encoding="utf-8", newline="")))
            mutated = [dict(r) for r in real_sc]
            mutated[0]["final_fg_pixels"] = str(int(mutated[0]["final_fg_pixels"]) + 1)
            msc = tdp / "scores_mut.csv"
            with msc.open("w", encoding="utf-8", newline="") as fh:
                w = _csv.DictWriter(fh, fieldnames=list(real_sc[0].keys()))
                w.writeheader()
                w.writerows(mutated)
            launch_mod.PHASE27_SCORES_CSV = str(msc)
            launch_mod.PHASE27_SCORES_CSV_SHA = launch_mod.sha(msc)
            r = launch_mod.check_final_authority_preconsumption()
            check("REQ17_sample_order_mismatch_detected_row_binding",
                  r["final_authority_preconsumption_pass"] is False
                  and r["reason"] == "FINAL_AUTHORITY_SAMPLE_ORDER_MISMATCH",
                  {"reason": r.get("reason"), "detail": r.get("sample_order_detail")})
    finally:
        _restore(launch_mod, saved_fa)

    # D52 gate is a pure function: no marker written by any failure
    check("REQ11_17_no_marker_from_final_authority_gate", not diag_mod.DIAGNOSTIC_START.exists())

    # ================= D53 — GT counter survives failure ====================== #
    rs = diag_mod._new_runtime_state()
    fake = types.SimpleNamespace(
        _load_val_gt=lambda *a, **k: "GT",
        _dice=lambda *a, **k: 1.0,
        _iou=lambda *a, **k: 1.0,
        _hd95=lambda *a, **k: 1.0,
        canonical_learned_core=lambda *a, **k: {"ok": True},
    )
    g = diag_mod._install_gt_guards(fake, rs)
    check("REQ18_guard_installed", {"_load_val_gt", "_dice", "_iou", "_hd95"} <= set(g["installed"]))
    raised = 0
    for nm in ("_load_val_gt", "_dice", "_iou", "_hd95"):
        try:
            getattr(fake, nm)()
        except SystemExit:
            raised += 1
    check("REQ18_guards_raise", raised == 4, {"raised": raised})
    check("REQ18_runtime_state_val_gt_read_incremented", rs["VAL_GT_READ"] == 4, {"VAL_GT_READ": rs["VAL_GT_READ"]})
    check("REQ18_runtime_state_blocked_calls_recorded",
          set(rs["blocked_gt_calls"]) == {"_load_val_gt", "_dice", "_iou", "_hd95"},
          {"blocked": rs["blocked_gt_calls"]})
    check("REQ18_non_gt_untouched", fake.canonical_learned_core() == {"ok": True})

    with tempfile.TemporaryDirectory() as td:
        orig_fail = diag_mod.DIAGNOSTIC_FAILURE
        diag_mod.DIAGNOSTIC_FAILURE = Path(td) / "failure_d53.json"
        try:
            diag_mod._write_failure(termination_kind="SYSTEM_EXIT", runtime_state=rs,
                                    exc_type="SystemExit", exc_msg="gt-access-forbidden",
                                    failing_stage="run_diagnostic")
            fj = json.loads(diag_mod.DIAGNOSTIC_FAILURE.read_text(encoding="utf-8"))
        finally:
            diag_mod.DIAGNOSTIC_FAILURE = orig_fail
    check("REQ19_failure_records_actual_val_gt_read", fj["VAL_GT_READ"] == 4, {"VAL_GT_READ": fj.get("VAL_GT_READ")})
    check("REQ19_failure_not_hardcoded_zero", fj["VAL_GT_READ"] != 0)
    check("REQ19_failure_blocked_calls_contains_callable", "_dice" in fj["blocked_gt_calls"])
    check("REQ19_failure_runtime_state_mirrors", fj["runtime_state"]["VAL_GT_READ"] == 4)

    # ================= D54 — computed evidence survives result-write failure === #
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        saved_paths = _save(diag_mod, "DIAGNOSTIC_START", "DIAGNOSTIC_RESULT", "DIAGNOSTIC_FAILURE")
        saved_fn = diag_mod._write_once_json
        saved_run = diag_mod.run_diagnostic
        diag_mod.DIAGNOSTIC_START = tdp / "start.json"
        diag_mod.DIAGNOSTIC_RESULT = tdp / "result.json"
        diag_mod.DIAGNOSTIC_FAILURE = tdp / "failure.json"

        synthetic_cmp = {
            "pass": True,
            "n_samples": 2,
            "final_f16_bit_identical_all": False,
            "total_f16_element_mismatch_count": 7,
            "max_abs_f16_difference": 0.5,
            "classification": "D51_END_TO_END_FINAL_AUTHORITY_NOT_REPRODUCED",
            "gt_read": False,
            "dice_iou_hd95_computed": False,
        }

        def fake_run(runtime_state):
            runtime_state["final_authority_computed"] = True
            runtime_state["final_authority_comparison"] = synthetic_cmp
            runtime_state["classification"] = synthetic_cmp["classification"]
            return {"artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_RESULT",
                    "revision": diag_mod.DIAGNOSTIC_REVISION,
                    "final_authority_comparison": synthetic_cmp,
                    "classification": synthetic_cmp["classification"],
                    "VAL_GT_READ": 0}

        def failing_write(path, payload):
            if Path(path) == diag_mod.DIAGNOSTIC_RESULT:
                raise OSError("SYNTHETIC_RESULT_WRITE_FAILURE")
            return saved_fn(path, payload)

        diag_mod.run_diagnostic = fake_run
        diag_mod._write_once_json = failing_write
        env_saved = {k: os.environ.get(k) for k in (diag_mod.ONE_SHOT_ENV, diag_mod.LAUNCH_AUTHORITY_TOKEN)}
        os.environ[diag_mod.ONE_SHOT_ENV] = "1"
        os.environ[diag_mod.LAUNCH_AUTHORITY_TOKEN] = "1"
        os.environ.pop(diag_mod.FOREIGN_V1_14_LAUNCH_TOKEN, None)
        try:
            rc_d54 = diag_mod.main()
        finally:
            _restore(diag_mod, saved_paths)
            diag_mod._write_once_json = saved_fn
            diag_mod.run_diagnostic = saved_run
            for k, v in env_saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        fail_p = tdp / "failure.json"
        check("REQ20_result_write_failure_rc3", rc_d54 == 3, {"rc": rc_d54})
        check("REQ20_failure_artifact_written", fail_p.exists())
        fj2 = json.loads(fail_p.read_text(encoding="utf-8")) if fail_p.exists() else {}
        check("REQ20_final_authority_computed_true", fj2.get("final_authority_computed") is True)
        check("REQ20_comparison_preserved", fj2.get("final_authority_comparison") == synthetic_cmp)
        check("REQ20_classification_preserved",
              fj2.get("classification") == "D51_END_TO_END_FINAL_AUTHORITY_NOT_REPRODUCED")
        check("REQ20_result_write_attempted_true", fj2.get("result_write_attempted") is True)
        check("REQ20_result_write_completed_false", fj2.get("result_write_completed") is False)
        check("REQ20_terminal_classification",
              fj2.get("terminal_classification") == diag_mod.TERMINAL_RESULT_WRITE_FAILED)
        check("REQ20_no_partial_result_file", not (tdp / "result.json").exists())

    # ================= finite-probability hardening =========================== #
    check("REQ21_finite_ok", diag_mod._finite_check(np.array([0.1, 0.5, 0.9], dtype=np.float32)) is True)
    check("REQ21_nan_rejected", diag_mod._finite_check(np.array([0.1, np.nan], dtype=np.float32)) is False)
    check("REQ21_posinf_rejected", diag_mod._finite_check(np.array([np.inf], dtype=np.float32)) is False)
    check("REQ21_neginf_rejected", diag_mod._finite_check(np.array([-np.inf], dtype=np.float32)) is False)
    rs2 = diag_mod._new_runtime_state()
    n_rec = diag_mod._record_nonfinite(rs2, "sX", np.array([np.nan, np.inf, -np.inf, 0.5], dtype=np.float32))
    check("REQ21_record_nonfinite_count", n_rec == 3, {"n": n_rec})
    check("REQ21_record_nonfinite_ids", rs2["nonfinite_samples"] == {"sX": 3})
    check("REQ21_record_nonfinite_flag", rs2["nonfinite_final_probability"] is True)
    with tempfile.TemporaryDirectory() as td:
        orig_fail = diag_mod.DIAGNOSTIC_FAILURE
        diag_mod.DIAGNOSTIC_FAILURE = Path(td) / "failure_nf.json"
        try:
            diag_mod._write_failure(termination_kind="SYSTEM_EXIT", runtime_state=rs2,
                                    exc_type="SystemExit", exc_msg=diag_mod.TERMINAL_NONFINITE,
                                    failing_stage="finite_check")
            fj3 = json.loads(diag_mod.DIAGNOSTIC_FAILURE.read_text(encoding="utf-8"))
        finally:
            diag_mod.DIAGNOSTIC_FAILURE = orig_fail
    check("REQ22_failure_preserves_nonfinite_samples", fj3.get("nonfinite_samples") == {"sX": 3})
    check("REQ22_failure_preserves_nonfinite_flag", fj3.get("nonfinite_final_probability") is True)
    check("REQ22_source_fails_closed_on_nonfinite", diag_mod.TERMINAL_NONFINITE in diag_src
          and 'runtime_state.get("nonfinite_final_probability")' in diag_src)

    # ================= GT wording / content =================================== #
    for gtc in GT_CALLABLES:
        check(f"REQ23_no_actual_call::{gtc}", not _has_actual_call(diag_tree, gtc))
    check("REQ23_no_mask_path_subscript_read", "mask_path" not in _subscript_read_keys(diag_tree),
          {"subscript_keys": sorted(_subscript_read_keys(diag_tree))})
    check("REQ24_gt_content_invariant_metadata_permitted",
          "mask_path_metadata_validation_permitted" in diag_src
          and diag_mod.GT_CONTENT_INVARIANT.get("mask_path_metadata_validation_permitted") is True)
    check("REQ24_gt_content_invariant_declares_content_rules",
          diag_mod.GT_CONTENT_INVARIANT.get("no_Image_open_on_mask_path") is True
          and diag_mod.GT_CONTENT_INVARIANT.get("_load_val_gt_never_executes") is True)

    # ================= launch authority / guarded write / ordering ============ #
    mainfn = _find_func(diag_tree, "main")
    la_line = None
    for n in ast.walk(mainfn):
        if isinstance(n, ast.If):
            seg = ast.get_source_segment(diag_src, n.test) or ""
            if "LAUNCH_AUTHORITY_TOKEN" in seg and "os.environ" in seg:
                la_line = n.lineno if la_line is None else min(la_line, n.lineno)
    mk_line = None
    for n in ast.walk(mainfn):
        if isinstance(n, ast.Call):
            f = n.func
            nm = getattr(f, "id", None) or getattr(f, "attr", None)
            if nm == "_write_once_json" and n.args:
                seg = ast.get_source_segment(diag_src, n.args[0]) or ""
                if "DIAGNOSTIC_START" in seg:
                    mk_line = n.lineno if mk_line is None else min(mk_line, n.lineno)
    check("REQ25_launch_authority_precedes_marker",
          la_line is not None and mk_line is not None and la_line < mk_line,
          {"authority_line": la_line, "marker_line": mk_line})
    guarded = False
    for tb in [n for n in ast.walk(mainfn) if isinstance(n, ast.Try)]:
        body_src = " ".join(ast.get_source_segment(diag_src, s) or "" for s in tb.body)
        handlers_src = " ".join(ast.get_source_segment(diag_src, h) or "" for h in tb.handlers)
        if "run_diagnostic(" in body_src and "_write_failure" in handlers_src:
            guarded = True
    check("REQ25_computation_guarded", guarded)
    check("REQ25_write_helper_O_EXCL", "os.O_CREAT | os.O_EXCL" in diag_src)
    check("REQ25_write_helper_fsync", "os.fsync(fd)" in diag_src)
    check("REQ25_result_write_guarded_for_D54",
          "RESULT_WRITE_FAILURE" in diag_src and "TERMINAL_EVIDENCE_ANOMALY__RESULT_WRITE_FAILED_AFTER_COMPUTATION" in diag_src)
    tl = []
    for n in ast.walk(launch_tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "load":
            seg = ast.get_source_segment(launch_src, n.func) or ""
            if "torch" in seg:
                tl.append(n.lineno)
    check("REQ25_launcher_no_torch_load", not tl, {"lines": tl})

    # ================= forbidden science/perturbation ========================= #
    for fb in ("run_image_perturbations", "run_proposal_perturbations", "run_science", "run_smoke"):
        check(f"REQ26_no_reach::{fb}", fb not in diag_src)
    targets = set()
    for n in ast.walk(diag_tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.func.id == "_write_once_json" and n.args:
            targets.add((ast.get_source_segment(diag_src, n.args[0]) or "").strip())
    check("REQ26_only_own_write_targets",
          bool(targets) and all(("DIAGNOSTIC_START" in t or "DIAGNOSTIC_RESULT" in t
                                 or "DIAGNOSTIC_FAILURE" in t) for t in targets),
          {"targets": sorted(targets)})

    # ================= consumed-evidence mutation ============================= #
    ce = launch_mod.check_consumed_evidence()
    check("REQ27_consumed_evidence_ok", ce["ok"] is True, {"predicates": ce["predicates"]})
    orig = dict(launch_mod.CONSUMED_EVIDENCE_PROVENANCE)
    mut = dict(orig); mut["v1_2_result"] = (orig["v1_2_result"][0], "0" * 64)
    launch_mod.CONSUMED_EVIDENCE_PROVENANCE = mut
    try:
        ce_bad = launch_mod.check_consumed_evidence()
    finally:
        launch_mod.CONSUMED_EVIDENCE_PROVENANCE = orig
    check("REQ27_consumed_evidence_mutation_detected", ce_bad["ok"] is False)
    orig_verdict = launch_mod.REQUIRED_D51_RECONCILIATION_VERDICT
    launch_mod.REQUIRED_D51_RECONCILIATION_VERDICT = "OTHER"
    try:
        ce_pred = launch_mod.check_consumed_evidence()
    finally:
        launch_mod.REQUIRED_D51_RECONCILIATION_VERDICT = orig_verdict
    check("REQ27_consumed_evidence_predicate_mutation_detected", ce_pred["ok"] is False)

    # ================= v1.0 preservation ====================================== #
    for p, exp in V1_0_PINS.items():
        check(f"REQ28_v1_0_preserved::{Path(p).name}", sha(ROOT / p) == exp, {"observed": sha(ROOT / p)})
    check("REQ28_launcher_pins_v1_0", all(sha(ROOT / p) == e for p, e in launch_mod.V1_0_PINS.items()))

    # ================= launcher pins ========================================== #
    check("REQ28_launcher_pin_matches_actual_diagnostic",
          launch_mod.FROZEN_EXPECTED_DIAGNOSTIC_SHA == sha(DIAG),
          {"pinned": launch_mod.FROZEN_EXPECTED_DIAGNOSTIC_SHA, "actual": sha(DIAG)})
    check("REQ28_launcher_v1_1_token_constant",
          launch_mod.LAUNCH_AUTHORITY_TOKEN == "PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY")
    check("REQ28_launcher_one_shot_env",
          launch_mod.ONE_SHOT_ENV == "PHASE36_FINAL_PROB_AUTHORITY_EXECUTE")
    tok_pos = launch_src.index('os.environ[LAUNCH_AUTHORITY_TOKEN] = "1"')
    check("REQ28_final_authority_gate_before_token",
          launch_src.index("check_final_authority_preconsumption()") < tok_pos)
    check("REQ28_verify_only_before_token", launch_src.index("if a.verify_only:") < tok_pos)

    n_ok = sum(1 for r in RESULTS if r["ok"])
    n = len(RESULTS)
    print(json.dumps({"artifact_kind": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_1_UNIT_RESULTS",
                      "n_checks": n, "n_pass": n_ok, "all_pass": n_ok == n,
                      "results": RESULTS}, indent=1))
    print(f"\n=== UNIT v1.1 (final-prob authority): {n_ok}/{n} pass")
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
