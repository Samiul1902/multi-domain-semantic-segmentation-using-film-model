#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — CLEAN EQUIVALENCE DIAGNOSTIC v1.2 — UNIT TESTS (no model, no CUDA).

Covers the 16 mutation-sensitive validator requirements of the D50 work order:
 1. no call to mod._verify_transitive_source_integrity in v1.2
 2. no source/launcher assignment to PHASE36_V1_14_LAUNCH_AUTHORITY
 3. inherited foreign v1.14 token causes fail-closed before marker
 4. source transitive maps exactly equal manifest transitive maps
 5. dependency removal detected
 6. checkpoint removal detected
 7. dependency SHA mutation detected
 8. checkpoint SHA mutation detected
 9. unexpected launcher_sha256 manifest key detected
10. exact v1.14 source mutation detected
11. v1.1 failure provenance mutation detected
12. launch authority required before marker
13. result/failure write remains guarded
14. full eq persistence remains intact
15. forbidden perturbation/science paths remain unreachable
16. v1.0 and v1.1 preserved byte-for-byte

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\phase36_clean_equivalence_diagnostic_unit_v1_2.py
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts" / "analysis"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

DIAG = ROOT / "scripts" / "analysis" / "phase36_clean_equivalence_diagnostic_v1_2.py"
LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_clean_equivalence_diagnostic_v1_2.py"
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


def _assigned_names(tree):
    """All names that appear as an assignment target (or named arg-free store)."""
    names = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
    return names


def _env_subscript_writes(tree):
    """Detect os.environ['X'] = ... / os.environ.setdefault('X', ...) writes."""
    writes = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Attribute) \
                        and t.value.attr == "environ":
                    sl = t.slice
                    if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                        writes.add(sl.value)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr in ("setdefault", "putenv") and n.args:
            a0 = n.args[0]
            if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                writes.add(a0.value)
    return writes


def main() -> int:
    diag_src = DIAG.read_text(encoding="utf-8")
    launch_src = LAUNCHER.read_text(encoding="utf-8")
    diag_tree = _tree(DIAG)
    launch_tree = _tree(LAUNCHER)

    # ---------------- 1. no call to _verify_transitive_source_integrity ------- #
    calls_diag = _has_actual_call(diag_tree, "_verify_transitive_source_integrity")
    calls_launch = _has_actual_call(launch_tree, "_verify_transitive_source_integrity")
    check("REQ1_no_forbidden_gate_call_in_diagnostic", not calls_diag, {"lines": calls_diag})
    check("REQ1_no_forbidden_gate_call_in_launcher", not calls_launch, {"lines": calls_launch})
    check("REQ1_diagnostic_marks_omission",
          "d50_foreign_gate_call_omitted" in diag_src)

    # ---------------- 2. no assignment to the foreign token ------------------- #
    FOREIGN = "PHASE36_V1_14_LAUNCH_AUTHORITY"
    diag_writes = _env_subscript_writes(diag_tree)
    launch_writes = _env_subscript_writes(launch_tree)
    check("REQ2_diagnostic_no_foreign_token_write", FOREIGN not in diag_writes,
          {"env_writes": sorted(diag_writes)})
    check("REQ2_launcher_no_foreign_token_write", FOREIGN not in launch_writes,
          {"env_writes": sorted(launch_writes)})
    # the literal token string must only appear as a constant comparison / constant def,
    # never as an assignment target of a string literal variable
    check("REQ2_foreign_token_declared_as_constant_only",
          f'FOREIGN_V1_14_LAUNCH_TOKEN = "{FOREIGN}"' in diag_src
          and f'FOREIGN_V1_14_LAUNCH_TOKEN = "{FOREIGN}"' in launch_src)

    # ---------------- 3. inherited foreign token => fail closed, no marker ---- #
    diag_mod = _load(DIAG, "_diag_v12_ut")
    saved = {k: os.environ.pop(k, None)
             for k in (diag_mod.ONE_SHOT_ENV, diag_mod.LAUNCH_AUTHORITY_TOKEN,
                       diag_mod.FOREIGN_V1_14_LAUNCH_TOKEN)}
    assert not diag_mod.DIAGNOSTIC_START.exists()
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

    # launcher-side foreign gate: refuses before dispatch
    launch_mod = _load(LAUNCHER, "_launch_v12_ut")
    fg_bad = launch_mod.check_foreign_v1_14_token_absent({FOREIGN: "1"})
    fg_ok = launch_mod.check_foreign_v1_14_token_absent({})
    check("REQ3_launcher_foreign_gate_flags_present", fg_bad["ok"] is False,
          {"foreign_token_present": fg_bad["foreign_token_present"]})
    check("REQ3_launcher_foreign_gate_passes_absent", fg_ok["ok"] is True)

    # ---------------- 4. source transitive maps == manifest maps (real tree) -- #
    ti = launch_mod.check_transitive_integrity()
    check("REQ4_real_tree_transitive_ok", ti["ok"] is True, {"reason": ti.get("reason")})
    check("REQ4_real_source_manifest_authority_exact_match",
          ti["source_manifest_transitive_authority_exact_match"] is True)
    check("REQ4_real_tree_is_14_4",
          ti["n_dependencies"] == 14 and ti["n_checkpoints"] == 4)
    check("REQ4_no_io_flags",
          ti["torch_load"] is False and ti["checkpoint_deserialization"] is False
          and ti["model_construction"] is False and ti["val_or_gt_read"] is False)
    # direct check: parse the v1.14 source maps and compare to manifest
    maps = launch_mod._load_frozen_v1_14_authority_maps(V14)
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    check("REQ4_source_maps_parsed", maps.get("ok") is True)
    if maps.get("ok"):
        check("REQ4_source_deps_set_eq_manifest",
              set(maps["deps"].keys()) == set(man["dependencies"].keys()))
        check("REQ4_source_deps_sha_eq_manifest",
              all(maps["deps"][k] == man["dependencies"][k] for k in maps["deps"]))
        check("REQ4_source_ckpts_set_eq_manifest",
              set(maps["ckpts"].keys()) == set(man["checkpoints"].keys()))
        check("REQ4_source_ckpts_sha_eq_manifest",
              all(maps["ckpts"][k] == man["checkpoints"][k] for k in maps["ckpts"]))

    # ---------------- 5/6/7/8/9/10 mutation-sensitive (pin-patched) ----------- #
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

    # 5. dependency removal
    m = json.loads(json.dumps(real_man)); m["dependencies"].pop(list(m["dependencies"].keys())[0])
    r = _run_with_manifest(m)
    check("REQ5_dependency_removal_detected", r["ok"] is False,
          {"reason": r.get("reason"), "n_deps": r["n_dependencies"]})
    # 6. checkpoint removal
    m = json.loads(json.dumps(real_man)); m["checkpoints"].pop(list(m["checkpoints"].keys())[0])
    r = _run_with_manifest(m)
    check("REQ6_checkpoint_removal_detected", r["ok"] is False,
          {"reason": r.get("reason"), "n_ckpts": r["n_checkpoints"]})
    # 7. dependency SHA mutation
    m = json.loads(json.dumps(real_man)); k = list(m["dependencies"].keys())[0]
    m["dependencies"][k] = "0" * 64
    r = _run_with_manifest(m)
    check("REQ7_dependency_sha_mutation_detected", r["ok"] is False,
          {"reason": r.get("reason")})
    # 8. checkpoint SHA mutation
    m = json.loads(json.dumps(real_man)); k = list(m["checkpoints"].keys())[0]
    m["checkpoints"][k] = "0" * 64
    r = _run_with_manifest(m)
    check("REQ8_checkpoint_sha_mutation_detected", r["ok"] is False,
          {"reason": r.get("reason")})
    # 9. unexpected launcher_sha256 key
    m = json.loads(json.dumps(real_man)); m["launcher_sha256"] = "deadbeef"
    r = _run_with_manifest(m)
    check("REQ9_unexpected_launcher_sha_key_detected", r["ok"] is False,
          {"launcher_sha256_absent": r.get("launcher_sha256_absent")})

    # 10. exact v1.14 source mutation detected
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        v_mut = tdp / "v14_mut.py"
        v_mut.write_bytes(V14.read_bytes() + b"\n# mutant\n")
        ti_mut = launch_mod.check_transitive_integrity(v14_path=v_mut)
        check("REQ10_v1_14_source_mutation_detected_in_transitive",
              ti_mut["ok"] is False, {"reason": ti_mut.get("reason")})
        auth_mut = launch_mod.verify_authority(v14_path=v_mut)
        check("REQ10_v1_14_source_mutation_detected_in_anchor",
              auth_mut["authorized"] is False)

    # 11. v1.1 failure provenance mutation detected
    m = json.loads(json.dumps(real_man))
    # mutate the source-map authority by tampering a dependency SHA -> also breaks
    # exact equality (source vs manifest) since source map is read from the real v1.14
    m["dependencies"][list(m["dependencies"].keys())[0]] = "1" * 64
    r = _run_with_manifest(m)
    check("REQ11_authority_inequality_surfaces_as_mismatch",
          r["ok"] is False and r["source_manifest_transitive_authority_exact_match"] is False,
          {"reason": r.get("reason")})
    # and the consumed-v1.1 binding fails when the failure artifact SHA is wrong
    orig_v11 = dict(launch_mod.CONSUMED_V1_1_PROVENANCE)
    mutated = dict(orig_v11)
    mutated["v1_1_failure"] = (orig_v11["v1_1_failure"][0], "0" * 64)
    launch_mod.CONSUMED_V1_1_PROVENANCE = mutated
    try:
        v11_bad = launch_mod.check_consumed_v1_1_failure()
    finally:
        launch_mod.CONSUMED_V1_1_PROVENANCE = orig_v11
    check("REQ11_v1_1_failure_provenance_mutation_detected", v11_bad["ok"] is False)

    # ---------------- 12. launch authority required before marker ------------- #
    mainfn = _find_func(diag_tree, "main")
    # locate guard line for the v1.2 launch authority and the start marker line
    la_names = set()
    for n in ast.walk(mainfn):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Compare):
            seg = ast.get_source_segment(diag_src, n.value) or ""
            if "os.environ.get(LAUNCH_AUTHORITY_TOKEN)" in seg:
                for t in n.targets:
                    if isinstance(t, ast.Name):
                        la_names.add(t.id)
    la_line = None
    for n in ast.walk(mainfn):
        if isinstance(n, ast.If):
            seg = ast.get_source_segment(diag_src, n.test) or ""
            refs = (("LAUNCH_AUTHORITY_TOKEN" in seg and "os.environ" in seg)
                    or any(nm in seg for nm in la_names))
            if refs and "ONE_SHOT_ENV" not in seg and "FOREIGN" not in seg:
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
    check("REQ12_launch_authority_guard_exists", la_line is not None, {"line": la_line})
    check("REQ12_launch_authority_guard_precedes_marker",
          la_line is not None and mk_line is not None and la_line < mk_line,
          {"authority_line": la_line, "marker_line": mk_line})
    # runtime: authority SET, execute gate ABSENT -> rc 3
    os.environ[diag_mod.LAUNCH_AUTHORITY_TOKEN] = "1"
    try:
        rc_no_gate = diag_mod.main()
    finally:
        os.environ.pop(diag_mod.LAUNCH_AUTHORITY_TOKEN, None)
    check("REQ12_no_execute_gate_rc3", rc_no_gate == 3, {"rc": rc_no_gate})
    # runtime: execute gate SET, authority ABSENT (foreign absent) -> rc 5
    os.environ[diag_mod.ONE_SHOT_ENV] = "1"
    try:
        rc_no_auth = diag_mod.main()
    finally:
        os.environ.pop(diag_mod.ONE_SHOT_ENV, None)
    check("REQ12_no_launch_authority_rc5", rc_no_auth == 5, {"rc": rc_no_auth})
    check("REQ12_no_marker_after_refusals", not diag_mod.DIAGNOSTIC_START.exists())

    # ---------------- 13. result/failure write remains guarded ---------------- #
    guarded = False
    for tb in [n for n in ast.walk(mainfn) if isinstance(n, ast.Try)]:
        body_src = " ".join(ast.get_source_segment(diag_src, s) or "" for s in tb.body)
        if ("run_diagnostic()" in body_src and "_write_once_json" in body_src
                and "DIAGNOSTIC_RESULT" in body_src):
            guarded = True
    check("REQ13_result_write_inside_guarded_try", guarded)
    check("REQ13_systemexit_writes_failure", 'termination_kind="SYSTEM_EXIT"' in diag_src)
    check("REQ13_baseexception_writes_failure", 'termination_kind="EXCEPTION"' in diag_src)
    check("REQ13_write_helper_O_EXCL", "os.O_CREAT | os.O_EXCL" in diag_src)
    check("REQ13_write_helper_full_loop", "while total < len(data)" in diag_src)
    check("REQ13_write_helper_fsync", "os.fsync(fd)" in diag_src)
    check("REQ13_write_helper_loud", "SHORT_WRITE" in diag_src)

    # ---------------- 14. full eq persistence intact -------------------------- #
    check("REQ14_eq_object_persisted", '"clean_equivalence_full": eq' in diag_src)
    # The full eq is produced by the frozen gate and written verbatim; the diagnostic
    # must NOT project / drop / whitelist eq fields before writing.  Prove the write
    # site writes the whole `eq` object (not a subset) and that the frozen gate still
    # produces the required field set.
    rdfn = _find_func(diag_tree, "run_diagnostic")
    eq_assigned_from_gate = False
    if rdfn is not None:
        seg = ast.get_source_segment(diag_src, rdfn) or ""
        eq_assigned_from_gate = ("_clean_equivalence_gate(" in seg and "eq = mod._clean_equivalence_gate" in seg)
    check("REQ14_eq_assigned_from_frozen_gate", eq_assigned_from_gate)
    check("REQ14_full_eq_written_not_projected",
          '"clean_equivalence_full": eq,' in diag_src)
    # frozen v1.14 gate still declares every required eq field
    v14_src = V14.read_text(encoding="utf-8")
    gate_fn = _find_func(_tree(V14), "_clean_equivalence_gate")
    gate_src = ast.get_source_segment(v14_src, gate_fn) or "" if gate_fn else ""
    for fld in ("all_pass", "checks", "n_generated", "n_bound", "n_dice_comparisons",
                "n_state_machine_branch_comparisons", "n_router_decision_comparisons",
                "missing_generated_dice", "missing_bound_dice", "dice_mismatches",
                "route_branch_mismatches", "router_decision_mismatches",
                "max_abs_dice_deviation"):
        check(f"REQ14_frozen_gate_emits::{fld}", f'"{fld}"' in gate_src)

    # ---------------- 15. forbidden perturbation/science unreachable ---------- #
    forbidden_calls = ["run_image_perturbations", "run_proposal_perturbations",
                       "run_science", "run_smoke"]
    fn_src = ""
    if mainfn is not None:
        fn_src += ast.get_source_segment(diag_src, mainfn) or ""
    rdfn = _find_func(diag_tree, "run_diagnostic")
    if rdfn is not None:
        fn_src += ast.get_source_segment(diag_src, rdfn) or ""
    for fb in forbidden_calls:
        check(f"REQ15_no_forbidden_call::{fb}", fb not in fn_src)
    # write targets are ONLY the diagnostic's own v1_2 artifacts
    targets = set()
    for n in ast.walk(diag_tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.func.id == "_write_once_json" and n.args:
            targets.add((ast.get_source_segment(diag_src, n.args[0]) or "").strip())
    ok_targets = bool(targets) and all(
        ("DIAGNOSTIC_START" in t or "DIAGNOSTIC_RESULT" in t or "DIAGNOSTIC_FAILURE" in t)
        for t in targets)
    check("REQ15_only_own_write_targets", ok_targets, {"targets": sorted(targets)})

    # ---------------- 16. v1.0 and v1.1 preserved byte-for-byte --------------- #
    v10 = {
        "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_0.py":
            "7cc51cceacfa314d7f84acb8a6dc482a2b46ea81de0ec695c0c8f0ca8b0b50f7",
        "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_0.py":
            "a34923faf6c27dd741ee1a1a1b4d1cbef1233664c2b02825e53b42c22c75b228",
        "scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_0.py":
            "33e72386699aa0100c314846ffe2592f740ca7fb76e926a704cf4d46fbf78bf5",
        "scripts/analysis/phase36_clean_equivalence_diagnostic_preflight_v1_0.py":
            "92c2d855e931d037e965d862a2ce0feb091d53e1bff0f91020f85729842e6653",
    }
    v11 = {
        "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_1.py":
            "04fa6252ff2533464553fb1a6c1f55ae009ee7ff00c1dbf89c1f901b089c839e",
        "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_1.py":
            "205dd4b877d8b6505c9479de9979087f19c341769ba2c5157a25701c212d14f6",
        "scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_1.py":
            "89190b297e7bc4e2868f7bb52fc46d836e6866317403523e8bbf0d167bc50aee",
        "scripts/analysis/phase36_clean_equivalence_diagnostic_preflight_v1_1.py":
            "3634a3f4314fb5712d958cda2effc3b3027257663692b51b3b4176b258fab529",
        "scripts/analysis/phase36_clean_equivalence_diagnostic_negative_controls_v1_1.py":
            "b43649898d5be2fb96737f683aa208ea84d55a66ab807ac0d06e0fba4a7b3ee1",
        "reports/audits/phase36_clean_equivalence_diagnostic_start_v1_1.json":
            "59b29875838ed6117a8441f422a17fa7bdae5088fc74b2b33a38f9c92e15fa68",
        "reports/audits/phase36_clean_equivalence_diagnostic_failure_v1_1.json":
            "ef6cf75f5d8432e69b89ddbef437c24b409cb325105a11f78a4c0f0004a57343",
        "reports/audits/phase36_clean_equivalence_diagnostic_v1_1_post_run_evidence.json":
            "a33066434cf569b77563a8028e842aefeac9a360e8e9479a3852bf9f401204af",
    }
    for p, exp in {**v10, **v11}.items():
        check(f"REQ16_preserved::{Path(p).name}", sha(ROOT / p) == exp)

    # ---------------- launcher anchors / pins --------------------------------- #
    check("launcher_pin_matches_actual_diagnostic",
          launch_mod.FROZEN_EXPECTED_DIAGNOSTIC_SHA == sha(DIAG),
          {"pinned": launch_mod.FROZEN_EXPECTED_DIAGNOSTIC_SHA, "actual": sha(DIAG)})
    check("launcher_v1_2_token_constant",
          launch_mod.LAUNCH_AUTHORITY_TOKEN == "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_LAUNCH_AUTHORITY")
    check("launcher_foreign_constant",
          launch_mod.FOREIGN_V1_14_LAUNCH_TOKEN == "PHASE36_V1_14_LAUNCH_AUTHORITY")
    # launcher AST: no torch.load call
    tl = []
    for n in ast.walk(launch_tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == "load":
            seg = ast.get_source_segment(launch_src, n.func) or ""
            if "torch" in seg:
                tl.append(n.lineno)
    check("launcher_no_torch_load", not tl, {"lines": tl})
    check("launcher_no_load_state_dict", "load_state_dict" not in launch_src)
    # ordering: foreign gate BEFORE token set; transitive BEFORE token set
    tok_pos = launch_src.index("os.environ[LAUNCH_AUTHORITY_TOKEN] = \"1\"")
    check("launcher_foreign_gate_before_token",
          launch_src.index("check_foreign_v1_14_token_absent()") < tok_pos)
    check("launcher_transitive_before_token",
          launch_src.index("check_transitive_integrity()") < tok_pos)
    check("launcher_consumed_v1_1_before_token",
          launch_src.index("check_consumed_v1_1_failure()") < tok_pos)
    check("launcher_verify_only_before_token", launch_src.index("if a.verify_only:") < tok_pos)

    n_ok = sum(1 for r in RESULTS if r["ok"])
    n = len(RESULTS)
    print(json.dumps({"artifact_kind": "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_UNIT_RESULTS",
                      "n_checks": n, "n_pass": n_ok, "all_pass": n_ok == n,
                      "results": RESULTS}, indent=1))
    print(f"\n=== UNIT v1.2: {n_ok}/{n} pass")
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
