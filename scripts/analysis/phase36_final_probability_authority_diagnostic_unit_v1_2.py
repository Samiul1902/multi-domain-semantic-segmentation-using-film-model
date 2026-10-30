#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.2 — UNIT TESTS (no model, no CUDA).

Mutation-sensitive validator suite for the v1.2 family (D56 repair):

  D56 (NEW — this suite's headline):
   0a. REAL runtime test of ``_clean_final_probability_only`` using a
       ``types.ModuleType`` (NOT a dict) carrying callable attributes
       ``_load_clean_image_tensor`` / ``canonical_learned_core``.  Proves:
       no TypeError, each callable called exactly once, the expected task_id /
       p_global_override / g_taps / router_features_202_override / roi_window /
       action_available are received, a finite final_probability is stored, and
       NO GT / file IO / model / checkpoint / CUDA is required.
   0b. AST: there is NO ``_FROZEN_MOD[...]`` Subscript node; the two callables are
       reached by ATTRIBUTE access.
   0c. mutation A: reverting ``_load_clean_image_tensor`` to subscripting is
       detected; mutation B: reverting ``canonical_learned_core`` is detected.

  D50 (from v1.0/v1.1):
   1. no call to mod._verify_transitive_source_integrity (diag + launcher)
   2. no source/launcher assignment to PHASE36_V1_14_LAUNCH_AUTHORITY
   3. inherited foreign v1.14 token => fail closed BEFORE marker
   4. source transitive maps exactly equal manifest maps
   ... dep/ckpt removal + SHA mutation + unexpected launcher_sha256 + v1.14 mutation
  D52: final authority present + SHA + header shape + dtype + sample-order (real tree)
  D53: guard mutates shared state; failure records ACTUAL VAL_GT_READ
  D54: computed evidence survives a result-write failure
  finite: NaN/+inf/-inf rejected & preserved
  GT wording/content, launch authority ordering, forbidden reach, consumed
  evidence, v1.0 + v1.1 preservation.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\phase36_final_probability_authority_diagnostic_unit_v1_2.py
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

DIAG = ROOT / "scripts" / "analysis" / "phase36_final_probability_authority_diagnostic_v1_2.py"
LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_final_probability_authority_diagnostic_v1_2.py"
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


def _frozen_mod_subscript_sites(tree):
    sites = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) \
                and n.value.id == "_FROZEN_MOD":
            sl = n.slice
            key = sl.value if isinstance(sl, ast.Constant) else "<expr>"
            sites.append({"line": n.lineno, "key": key})
    return sites


def _frozen_mod_attr_names(tree):
    names = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) \
                and n.value.id == "_FROZEN_MOD":
            names.add(n.attr)
    return names


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

V1_1_PINS = {
    "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_1.py":
        "b9f6a449445d8ac5edd1dafe30e2f0b5005d487be314011bd2ff9162db770672",
    "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_1.py":
        "4c9737362fcf01f0ef8ef629f489cdff07c72e63b46f34e4ea508b7ba0df83ae",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_1.py":
        "0358ed115dcedea612aae1b7f0311ea08b97ba212b893a10c51ddae606fbabea",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_1.py":
        "7ba8899b25fbddbcebd42971eedd1bca4b2ca8d06d33629cec7a286e01227925",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_1.py":
        "ef7a7d8c5b7d9699fa375b2bcfccc3c482ac9e4d1b4ce9a1c3807142100a6950",
}

GT_CALLABLES = ("_load_val_gt", "full_field_gt", "_dice", "_iou", "_hd95")


def _save(mod, *names):
    return {n: getattr(mod, n) for n in names}


def _restore(mod, saved):
    for n, v in saved.items():
        setattr(mod, n, v)


# --------------------------------------------------------------------------- #
# D56 — REAL ModuleType runtime harness (no model / CUDA / IO / GT)
# --------------------------------------------------------------------------- #
class _FakeCtx(dict):
    """The frozen path indexes ctx as a DICT (``ctx["device"]`` / ``ctx["system"]``)."""
    def __init__(self):
        super().__init__(device="cpu", system={"task_id_order": [0, 1, 2, 3]})


class _FakeImageT:
    """No-IO fake that supports ``image_t[None].to(device)``."""
    def __getitem__(self, key):
        assert key is None
        return self

    def to(self, device):
        return self


def _build_fake_frozen_module(record: dict) -> types.ModuleType:
    """Build a REAL ``types.ModuleType`` with callable ATTRIBUTES (NOT a dict)."""
    m = types.ModuleType("fake_frozen_v1_14_for_d56")

    def _load_clean_image_tensor(row):
        record["load_calls"] += 1
        record["load_row"] = row
        return _FakeImageT()

    def canonical_learned_core(ctx, image_b, task_id, *, p_global_override=None,
                               g_taps=None, router_features_202_override=None,
                               roi_window=None, action_available=None, counters=None,
                               **kwargs):
        record["core_calls"] += 1
        record["core_ctx"] = ctx
        record["core_image_b"] = image_b
        record["core_task_id"] = int(task_id)
        record["p_global_override"] = p_global_override
        record["g_taps"] = g_taps
        record["rf202"] = router_features_202_override
        record["roi_window"] = roi_window
        record["action_available"] = action_available
        return {
            "final_probability": np.full((4, 4), 0.7, dtype=np.float32),
            "state": "CANONICAL_FUSED",
            "router_decision": "EXECUTE",
            "roi_available": True,
        }

    m._load_clean_image_tensor = _load_clean_image_tensor
    m.canonical_learned_core = canonical_learned_core
    return m


def main() -> int:
    diag_src = DIAG.read_text(encoding="utf-8")
    launch_src = LAUNCHER.read_text(encoding="utf-8")
    diag_tree = _tree(DIAG)
    launch_tree = _tree(LAUNCHER)

    diag_mod = _load(DIAG, "_diag_fpa_v12_ut")
    launch_mod = _load(LAUNCHER, "_launch_fpa_v12_ut")
    FOREIGN = launch_mod.FOREIGN_V1_14_LAUNCH_TOKEN

    # ================= D56 (0a) REAL ModuleType runtime test ================== #
    saved_frozen = diag_mod._FROZEN_MOD
    try:
        rec = {"load_calls": 0, "core_calls": 0, "load_row": None}
        fake = _build_fake_frozen_module(rec)
        check("REQ0a0_fake_is_real_module", isinstance(fake, types.ModuleType))

        diag_mod._FROZEN_MOD = fake   # attribute access must work; subscript would raise
        sid, row = "S1", {"sample_id": "S1", "task_id": 2, "image_path": "/dev/null", "mask_path": "X"}
        ctx = _FakeCtx()
        generated = {"p_global": {"S1": np.full((4, 4), 0.6, dtype=np.float32)},
                     "geometry": {"S1": {"clip_y1": 0, "clip_y2": 2, "clip_x1": 0, "clip_x2": 2}},
                     "rf202": {"S1": np.zeros(202, dtype=np.float32)}}
        counters = {}
        store = {}
        rs = diag_mod._new_runtime_state()

        raised = None
        result = None
        try:
            result = diag_mod._clean_final_probability_only(
                sid, row, ctx, generated, counters, store, rs)
        except BaseException as exc:  # noqa: BLE001
            raised = f"{type(exc).__name__}: {exc}"

        check("REQ0a1_no_exception_from_real_helper", raised is None, {"raised": raised})
        check("REQ0a2_load_clean_image_tensor_called_once", rec["load_calls"] == 1,
              {"n": rec["load_calls"]})
        check("REQ0a3_canonical_learned_core_called_once", rec["core_calls"] == 1,
              {"n": rec["core_calls"]})
        check("REQ0a4_task_id_received", rec["core_task_id"] == 2, {"task_id": rec["core_task_id"]})
        check("REQ0a5_p_global_override_passthrough",
              rec["p_global_override"] is generated["p_global"]["S1"])
        check("REQ0a6_g_taps_none", rec["g_taps"] is None)
        check("REQ0a7_router_features_202_passthrough",
              rec["rf202"] is generated["rf202"]["S1"])
        check("REQ0a8_roi_window_none", rec["roi_window"] is None)
        check("REQ0a9_action_available_true_for_geom", rec["action_available"] is True,
              {"action_available": rec["action_available"]})
        check("REQ0a10_final_probability_stored",
              isinstance(store.get("S1"), np.ndarray) and store["S1"].shape == (4, 4))
        check("REQ0a11_finite_flag_true",
              isinstance(result, dict) and result.get("final_probability_finite") is True,
              {"result": result})
        check("REQ0a12_final_probability_value",
              bool(np.allclose(store["S1"], np.float32(0.7))))
        check("REQ0a13_no_gt_call", rs["VAL_GT_READ"] == 0 and rs["blocked_gt_calls"] == [])
        check("REQ0a14_counters_passthrough_used",
              counters.get("final_probability_passes") == 1, {"counters": counters})

        # action_available False when geom is None
        rec2 = {"load_calls": 0, "core_calls": 0, "load_row": None}
        diag_mod._FROZEN_MOD = _build_fake_frozen_module(rec2)
        generated2 = {"p_global": {"S2": np.full((4, 4), 0.6, dtype=np.float32)},
                      "geometry": {"S2": None},
                      "rf202": {"S2": np.zeros(202, dtype=np.float32)}}
        diag_mod._clean_final_probability_only("S2", {"sample_id": "S2", "task_id": 0},
                                                ctx, generated2, {}, {}, diag_mod._new_runtime_state())
        check("REQ0a15_action_available_false_when_geom_none", rec2["action_available"] is False,
              {"action_available": rec2["action_available"]})
    finally:
        diag_mod._FROZEN_MOD = saved_frozen

    # ================= D56 (0b) AST: attribute access, no subscript ========== #
    sub_sites = _frozen_mod_subscript_sites(diag_tree)
    attr_names = _frozen_mod_attr_names(diag_tree)
    check("REQ0b1_no_frozen_mod_subscript", not sub_sites, {"sites": sub_sites})
    check("REQ0b2_load_clean_image_tensor_attribute_access",
          "_load_clean_image_tensor" in attr_names, {"attrs": sorted(attr_names)})
    check("REQ0b3_canonical_learned_core_attribute_access",
          "canonical_learned_core" in attr_names, {"attrs": sorted(attr_names)})

    # launcher-side D56 control on the real tree
    d56 = launch_mod.check_d56_module_interface()
    check("REQ0b4_launcher_d56_control_pass", d56["ok"] is True, {"d56": d56})

    # ================= D56 (0c) MUTATION CONTROLS ============================ #
    for tag, old, new, req in (
        ("A", "_FROZEN_MOD._load_clean_image_tensor(row)",
         '_FROZEN_MOD["_load_clean_image_tensor"](row)',
         "REQ0c1_load_clean_image_tensor"),
        ("B", "_FROZEN_MOD.canonical_learned_core(",
         '_FROZEN_MOD["canonical_learned_core"](',
         "REQ0c2_canonical_learned_core"),
    ):
        with tempfile.TemporaryDirectory() as td:
            mutant = Path(td) / "diag_mut.py"
            mutated_src = diag_src.replace(old, new, 1)
            check(f"{req}_mutation_applied", mutated_src != diag_src)
            mutant.write_text(mutated_src, encoding="utf-8")
            mtree = _tree(mutant)
            msites = _frozen_mod_subscript_sites(mtree)
            # the launcher-side AST control must FAIL on the mutant
            lctrl = launch_mod.check_d56_module_interface(mutant)
            check(f"{req}_subscript_mutation_detected_by_ast", bool(msites), {"sites": msites})
            check(f"{req}_launcher_control_rejects_mutant", lctrl["ok"] is False, {"lctrl": lctrl})

    # ================= D50 (1) no forbidden gate call ======================== #
    check("REQ1_no_forbidden_gate_call_in_diagnostic",
          not _has_actual_call(diag_tree, "_verify_transitive_source_integrity"))
    check("REQ1_no_forbidden_gate_call_in_launcher",
          not _has_actual_call(launch_tree, "_verify_transitive_source_integrity"))
    check("REQ1_diagnostic_marks_omission", "d50_foreign_gate_call_omitted" in diag_src)

    # ================= D50 (2) no foreign-token write ======================== #
    check("REQ2_diagnostic_no_foreign_token_write", FOREIGN not in _env_subscript_writes(diag_tree))
    check("REQ2_launcher_no_foreign_token_write", FOREIGN not in _env_subscript_writes(launch_tree))

    # ================= D50 (3) foreign token => fail closed ================== #
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

    # ================= D50 (4) source transitive maps == manifest ============ #
    ti = launch_mod.check_transitive_integrity()
    check("REQ4_real_tree_transitive_ok", ti["ok"] is True, {"reason": ti.get("reason")})
    check("REQ4_real_source_manifest_authority_exact_match",
          ti["source_manifest_transitive_authority_exact_match"] is True)
    check("REQ4_real_tree_is_14_4", ti["n_dependencies"] == 14 and ti["n_checkpoints"] == 4)

    # ================= D50 (5-9) mutation-sensitive manifest ================= #
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

    # ================= D50 (10) v1.14 source mutation ======================== #
    with tempfile.TemporaryDirectory() as td:
        v_mut = Path(td) / "v14_mut.py"
        v_mut.write_bytes(V14.read_bytes() + b"\n# mutant\n")
        check("REQ10_v1_14_source_mutation_detected",
              launch_mod.check_transitive_integrity(v14_path=v_mut)["ok"] is False)

    # ================= D52 — final-authority pre-consumption gate ============ #
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
            r = launch_mod.check_final_authority_preconsumption(authority_path=tdp / "nope.npy")
            check("REQ12_authority_missing_detected",
                  r["final_authority_preconsumption_pass"] is False and r["reason"] == "FINAL_AUTHORITY_ABSENT",
                  {"reason": r.get("reason")})
            bad = tdp / "bad.npy"
            bad.write_bytes(b"not-an-npy")
            r = launch_mod.check_final_authority_preconsumption(authority_path=bad)
            check("REQ13_authority_sha_mutation_detected",
                  r["final_authority_preconsumption_pass"] is False and r["reason"] == "FINAL_AUTHORITY_SHA_MISMATCH",
                  {"reason": r.get("reason")})
            shp = tdp / "shp.npy"
            np.save(shp, np.zeros((2, 3), dtype=np.float16))
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_SHA = launch_mod.sha(shp)
            r = launch_mod.check_final_authority_preconsumption(authority_path=shp)
            check("REQ14_wrong_shape_detected",
                  r["final_authority_preconsumption_pass"] is False and r["reason"] == "FINAL_AUTHORITY_SHAPE_MISMATCH",
                  {"reason": r.get("reason")})
            dt = tdp / "dt.npy"
            np.save(dt, np.zeros((2, 3), dtype=np.float32))
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_SHA = launch_mod.sha(dt)
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_SHAPE = (2, 3)
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_DTYPE = "float16"
            r = launch_mod.check_final_authority_preconsumption(authority_path=dt)
            check("REQ15_wrong_dtype_detected",
                  r["final_authority_preconsumption_pass"] is False and r["reason"] == "FINAL_AUTHORITY_DTYPE_MISMATCH",
                  {"reason": r.get("reason")})
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_SHA = saved_fa["PHASE27_FINAL_PROB_AUTHORITY_SHA"]
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_SHAPE = saved_fa["PHASE27_FINAL_PROB_AUTHORITY_SHAPE"]
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_DTYPE = saved_fa["PHASE27_FINAL_PROB_AUTHORITY_DTYPE"]

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

            real_man_rows = list(_csv.DictReader((ROOT / launch_mod.VAL_MANIFEST).open(encoding="utf-8", newline="")))
            rman = tdp / "val_rev.csv"
            with rman.open("w", encoding="utf-8", newline="") as fh:
                w = _csv.DictWriter(fh, fieldnames=list(real_man_rows[0].keys()))
                w.writeheader()
                w.writerows(list(reversed(real_man_rows)))
            launch_mod.VAL_MANIFEST = str(rman)
            r = launch_mod.check_final_authority_preconsumption()
            check("REQ16b_reordered_manifest_detected_by_sha",
                  r["final_authority_preconsumption_pass"] is False
                  and r["reason"] == "VAL_MANIFEST_SHA_MISMATCH",
                  {"reason": r.get("reason")})
            launch_mod.VAL_MANIFEST = saved_fa["VAL_MANIFEST"]
            launch_mod.VAL_MANIFEST_SHA = saved_fa["VAL_MANIFEST_SHA"]

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

    check("REQ11_17_no_marker_from_final_authority_gate", not diag_mod.DIAGNOSTIC_START.exists())

    # ================= v1.1 CONSUMED-state binding (D56) ===================== #
    v11 = launch_mod.check_v1_1_consumed_state()
    check("REQ18_v1_1_consumed_state_ok", v11["ok"] is True, {"items": v11["items"]})
    check("REQ18_v1_1_result_absent", v11["result_absent"] is True)
    check("REQ18_d56_classification_bound",
          v11.get("d56_classification") == "DIAGNOSTIC_FROZEN_MODULE_SUBSCRIPT_MISMATCH")
    check("REQ18_d56_root_cause_established", v11.get("d56_root_cause_established") is True)
    check("REQ18_v1_1_predicates_match",
          all(v11.get("predicates_match", {}).values()), {"pred": v11.get("predicates_match")})

    # mutation: wrong v1.1 START SHA
    orig_v11 = launch_mod.V1_1_START_SHA
    launch_mod.V1_1_START_SHA = "0" * 64
    try:
        v11_bad = launch_mod.check_v1_1_consumed_state()
    finally:
        launch_mod.V1_1_START_SHA = orig_v11
    check("REQ18_v1_1_start_sha_mutation_detected", v11_bad["ok"] is False)
    # mutation: wrong D56 adjudication SHA
    orig_adj = launch_mod.D56_FAILURE_ADJUDICATION_SHA
    launch_mod.D56_FAILURE_ADJUDICATION_SHA = "0" * 64
    try:
        v11_bad2 = launch_mod.check_v1_1_consumed_state()
    finally:
        launch_mod.D56_FAILURE_ADJUDICATION_SHA = orig_adj
    check("REQ18_d56_adjudication_sha_mutation_detected", v11_bad2["ok"] is False)

    # ================= D53 — GT counter survives failure ===================== #
    rs = diag_mod._new_runtime_state()
    fake_gt = types.SimpleNamespace(
        _load_val_gt=lambda *a, **k: "GT",
        _dice=lambda *a, **k: 1.0,
        _iou=lambda *a, **k: 1.0,
        _hd95=lambda *a, **k: 1.0,
        canonical_learned_core=lambda *a, **k: {"ok": True},
    )
    g = diag_mod._install_gt_guards(fake_gt, rs)
    check("REQ19_guard_installed", {"_load_val_gt", "_dice", "_iou", "_hd95"} <= set(g["installed"]))
    raised = 0
    for nm in ("_load_val_gt", "_dice", "_iou", "_hd95"):
        try:
            getattr(fake_gt, nm)()
        except SystemExit:
            raised += 1
    check("REQ19_guards_raise", raised == 4, {"raised": raised})
    check("REQ19_runtime_state_val_gt_read_incremented", rs["VAL_GT_READ"] == 4, {"VAL_GT_READ": rs["VAL_GT_READ"]})
    check("REQ19_runtime_state_blocked_calls_recorded",
          set(rs["blocked_gt_calls"]) == {"_load_val_gt", "_dice", "_iou", "_hd95"},
          {"blocked": rs["blocked_gt_calls"]})
    check("REQ19_non_gt_untouched", fake_gt.canonical_learned_core() == {"ok": True})

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
    check("REQ20_failure_records_actual_val_gt_read", fj["VAL_GT_READ"] == 4, {"VAL_GT_READ": fj.get("VAL_GT_READ")})
    check("REQ20_failure_not_hardcoded_zero", fj["VAL_GT_READ"] != 0)
    check("REQ20_failure_blocked_calls_contains_callable", "_dice" in fj["blocked_gt_calls"])
    check("REQ20_failure_runtime_state_mirrors", fj["runtime_state"]["VAL_GT_READ"] == 4)

    # ================= D54 — computed evidence survives result-write failure == #
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        saved_paths = _save(diag_mod, "DIAGNOSTIC_START", "DIAGNOSTIC_RESULT", "DIAGNOSTIC_FAILURE")
        saved_fn = diag_mod._write_once_json
        saved_run = diag_mod.run_diagnostic
        diag_mod.DIAGNOSTIC_START = tdp / "start.json"
        diag_mod.DIAGNOSTIC_RESULT = tdp / "result.json"
        diag_mod.DIAGNOSTIC_FAILURE = tdp / "failure.json"

        synthetic_cmp = {
            "pass": True, "n_samples": 2, "final_f16_bit_identical_all": False,
            "total_f16_element_mismatch_count": 7, "max_abs_f16_difference": 0.5,
            "classification": "D51_END_TO_END_FINAL_AUTHORITY_NOT_REPRODUCED",
            "gt_read": False, "dice_iou_hd95_computed": False,
        }

        def fake_run(runtime_state):
            runtime_state["final_authority_computed"] = True
            runtime_state["final_authority_comparison"] = synthetic_cmp
            runtime_state["classification"] = synthetic_cmp["classification"]
            return {"artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_RESULT",
                    "revision": diag_mod.DIAGNOSTIC_REVISION,
                    "final_authority_comparison": synthetic_cmp,
                    "classification": synthetic_cmp["classification"], "VAL_GT_READ": 0}

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
        check("REQ21_result_write_failure_rc3", rc_d54 == 3, {"rc": rc_d54})
        check("REQ21_failure_artifact_written", fail_p.exists())
        fj2 = json.loads(fail_p.read_text(encoding="utf-8")) if fail_p.exists() else {}
        check("REQ21_final_authority_computed_true", fj2.get("final_authority_computed") is True)
        check("REQ21_comparison_preserved", fj2.get("final_authority_comparison") == synthetic_cmp)
        check("REQ21_classification_preserved",
              fj2.get("classification") == "D51_END_TO_END_FINAL_AUTHORITY_NOT_REPRODUCED")
        check("REQ21_result_write_attempted_true", fj2.get("result_write_attempted") is True)
        check("REQ21_result_write_completed_false", fj2.get("result_write_completed") is False)
        check("REQ21_terminal_classification",
              fj2.get("terminal_classification") == diag_mod.TERMINAL_RESULT_WRITE_FAILED)
        check("REQ21_no_partial_result_file", not (tdp / "result.json").exists())

    # ================= finite-probability hardening ========================== #
    check("REQ22_finite_ok", diag_mod._finite_check(np.array([0.1, 0.5, 0.9], dtype=np.float32)) is True)
    check("REQ22_nan_rejected", diag_mod._finite_check(np.array([0.1, np.nan], dtype=np.float32)) is False)
    check("REQ22_posinf_rejected", diag_mod._finite_check(np.array([np.inf], dtype=np.float32)) is False)
    check("REQ22_neginf_rejected", diag_mod._finite_check(np.array([-np.inf], dtype=np.float32)) is False)
    rs2 = diag_mod._new_runtime_state()
    n_rec = diag_mod._record_nonfinite(rs2, "sX", np.array([np.nan, np.inf, -np.inf, 0.5], dtype=np.float32))
    check("REQ22_record_nonfinite_count", n_rec == 3, {"n": n_rec})
    check("REQ22_record_nonfinite_ids", rs2["nonfinite_samples"] == {"sX": 3})
    check("REQ22_record_nonfinite_flag", rs2["nonfinite_final_probability"] is True)
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
    check("REQ23_failure_preserves_nonfinite_samples", fj3.get("nonfinite_samples") == {"sX": 3})
    check("REQ23_failure_preserves_nonfinite_flag", fj3.get("nonfinite_final_probability") is True)
    check("REQ23_source_fails_closed_on_nonfinite", diag_mod.TERMINAL_NONFINITE in diag_src
          and 'runtime_state.get("nonfinite_final_probability")' in diag_src)

    # ================= GT wording / content ================================== #
    for gtc in GT_CALLABLES:
        check(f"REQ24_no_actual_call::{gtc}", not _has_actual_call(diag_tree, gtc))
    check("REQ24_no_mask_path_subscript_read", "mask_path" not in _subscript_read_keys(diag_tree),
          {"subscript_keys": sorted(_subscript_read_keys(diag_tree))})
    check("REQ25_gt_content_invariant_metadata_permitted",
          "mask_path_metadata_validation_permitted" in diag_src
          and diag_mod.GT_CONTENT_INVARIANT.get("mask_path_metadata_validation_permitted") is True)
    check("REQ25_gt_content_invariant_declares_content_rules",
          diag_mod.GT_CONTENT_INVARIANT.get("no_Image_open_on_mask_path") is True
          and diag_mod.GT_CONTENT_INVARIANT.get("_load_val_gt_never_executes") is True)

    # ================= launch authority / guarded write / ordering =========== #
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
    check("REQ26_launch_authority_precedes_marker",
          la_line is not None and mk_line is not None and la_line < mk_line,
          {"authority_line": la_line, "marker_line": mk_line})
    guarded = False
    for tb in [n for n in ast.walk(mainfn) if isinstance(n, ast.Try)]:
        body_src = " ".join(ast.get_source_segment(diag_src, s) or "" for s in tb.body)
        handlers_src = " ".join(ast.get_source_segment(diag_src, h) or "" for h in tb.handlers)
        if "run_diagnostic(" in body_src and "_write_failure" in handlers_src:
            guarded = True
    check("REQ26_computation_guarded", guarded)
    check("REQ26_write_helper_O_EXCL", "os.O_CREAT | os.O_EXCL" in diag_src)
    check("REQ26_write_helper_fsync", "os.fsync(fd)" in diag_src)
    check("REQ26_result_write_guarded_for_D54",
          "RESULT_WRITE_FAILURE" in diag_src and "TERMINAL_EVIDENCE_ANOMALY__RESULT_WRITE_FAILED_AFTER_COMPUTATION" in diag_src)
    tl = []
    for n in ast.walk(launch_tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "load":
            seg = ast.get_source_segment(launch_src, n.func) or ""
            if "torch" in seg:
                tl.append(n.lineno)
    check("REQ26_launcher_no_torch_load", not tl, {"lines": tl})

    # ================= forbidden science/perturbation ======================== #
    for fb in ("run_image_perturbations", "run_proposal_perturbations", "run_science", "run_smoke"):
        check(f"REQ27_no_reach::{fb}", fb not in diag_src)
    targets = set()
    for n in ast.walk(diag_tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.func.id == "_write_once_json" and n.args:
            targets.add((ast.get_source_segment(diag_src, n.args[0]) or "").strip())
    check("REQ27_only_own_write_targets",
          bool(targets) and all(("DIAGNOSTIC_START" in t or "DIAGNOSTIC_RESULT" in t
                                 or "DIAGNOSTIC_FAILURE" in t) for t in targets),
          {"targets": sorted(targets)})

    # ================= consumed-evidence mutation =========================== #
    ce = launch_mod.check_consumed_evidence()
    check("REQ28_consumed_evidence_ok", ce["ok"] is True, {"predicates": ce["predicates"]})
    orig = dict(launch_mod.CONSUMED_EVIDENCE_PROVENANCE)
    mut = dict(orig); mut["v1_2_result"] = (orig["v1_2_result"][0], "0" * 64)
    launch_mod.CONSUMED_EVIDENCE_PROVENANCE = mut
    try:
        ce_bad = launch_mod.check_consumed_evidence()
    finally:
        launch_mod.CONSUMED_EVIDENCE_PROVENANCE = orig
    check("REQ28_consumed_evidence_mutation_detected", ce_bad["ok"] is False)
    orig_verdict = launch_mod.REQUIRED_D51_RECONCILIATION_VERDICT
    launch_mod.REQUIRED_D51_RECONCILIATION_VERDICT = "OTHER"
    try:
        ce_pred = launch_mod.check_consumed_evidence()
    finally:
        launch_mod.REQUIRED_D51_RECONCILIATION_VERDICT = orig_verdict
    check("REQ28_consumed_evidence_predicate_mutation_detected", ce_pred["ok"] is False)

    # ================= v1.0 + v1.1 preservation ============================= #
    for p, exp in V1_0_PINS.items():
        check(f"REQ29_v1_0_preserved::{Path(p).name}", sha(ROOT / p) == exp, {"observed": sha(ROOT / p)})
    for p, exp in V1_1_PINS.items():
        check(f"REQ30_v1_1_preserved::{Path(p).name}", sha(ROOT / p) == exp, {"observed": sha(ROOT / p)})
    check("REQ30_launcher_pins_v1_0", all(sha(ROOT / p) == e for p, e in launch_mod.V1_0_PINS.items()))
    check("REQ30_launcher_pins_v1_1", all(sha(ROOT / p) == e for p, e in launch_mod.V1_1_PINS.items()))

    # ================= launcher pins ========================================= #
    check("REQ31_launcher_pin_matches_actual_diagnostic",
          launch_mod.FROZEN_EXPECTED_DIAGNOSTIC_SHA == sha(DIAG),
          {"pinned": launch_mod.FROZEN_EXPECTED_DIAGNOSTIC_SHA, "actual": sha(DIAG)})
    check("REQ31_launcher_v1_2_token_constant",
          launch_mod.LAUNCH_AUTHORITY_TOKEN == "PHASE36_FINAL_PROB_AUTHORITY_V1_2_LAUNCH_AUTHORITY")
    check("REQ31_launcher_one_shot_env",
          launch_mod.ONE_SHOT_ENV == "PHASE36_FINAL_PROB_AUTHORITY_EXECUTE")
    check("REQ31_no_v1_1_token_reuse",
          "PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY" not in launch_src
          or launch_mod.LAUNCH_AUTHORITY_TOKEN != "PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY")
    tok_pos = launch_src.index('os.environ[LAUNCH_AUTHORITY_TOKEN] = "1"')
    check("REQ31_final_authority_gate_before_token",
          launch_src.index("check_final_authority_preconsumption()") < tok_pos)
    check("REQ31_v1_1_consumed_gate_before_token",
          launch_src.index("check_v1_1_consumed_state()") < tok_pos)
    check("REQ31_verify_only_before_token", launch_src.index("if a.verify_only:") < tok_pos)

    # ================= no v1.2 markers created by this suite ================== #
    for m in ("start", "result", "failure"):
        p = ROOT / "reports" / "audits" / f"phase36_final_probability_authority_diagnostic_{m}_v1_2.json"
        check(f"REQ32_v1_2_{m}_marker_absent", not p.exists())

    n_ok = sum(1 for r in RESULTS if r["ok"])
    n = len(RESULTS)
    print(json.dumps({"artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_V1_2_UNIT_RESULTS",
                      "n_checks": n, "n_pass": n_ok, "all_pass": n_ok == n,
                      "results": RESULTS}, indent=1))
    print(f"\n=== UNIT v1.2 (final-prob authority, D56): {n_ok}/{n} pass")
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
