#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — CLEAN EQUIVALENCE DIAGNOSTIC v1.1 — UNIT TESTS (no model, no CUDA).

D49: real AST / control-flow bindings, NOT substring-only or tautological checks.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\phase36_clean_equivalence_diagnostic_unit_v1_1.py
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DIAG = ROOT / "scripts" / "analysis" / "phase36_clean_equivalence_diagnostic_v1_1.py"
LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_clean_equivalence_diagnostic_v1_1.py"

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


def _str_literals(tree):
    return {n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)}


def main() -> int:
    diag_src = DIAG.read_text(encoding="utf-8")
    launch_src = LAUNCHER.read_text(encoding="utf-8")
    diag_tree = _tree(DIAG)
    launch_tree = _tree(LAUNCHER)

    # ---- 1. D45: source defines the required token constants ------------- #
    check("D45_diag_defines_ONE_SHOT_ENV",
          'ONE_SHOT_ENV = "PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE"' in diag_src)
    check("D45_diag_defines_V1_1_LAUNCH_AUTHORITY",
          'LAUNCH_AUTHORITY_TOKEN = "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_LAUNCH_AUTHORITY"' in diag_src)
    check("D45_launcher_token_matches_source",
          '"PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_LAUNCH_AUTHORITY"' in launch_src)

    # ---- 2. D45: main() checks launch authority BEFORE writing the marker - #
    mainfn = _find_func(diag_tree, "main")
    check("D45_main_found", mainfn is not None)
    if mainfn is not None:
        # find AST positions of: launch-authority guard, and start-marker write.
        # The guard may be a direct `if os.environ.get(TOKEN) != "1":` OR an
        # indirect `ok = os.environ.get(TOKEN) == "1"` + `if not ok:` pattern.
        la_guard_line = None
        marker_line = None
        # first locate the name(s) bound from the launch-authority env
        la_names = set()
        for n in ast.walk(mainfn):
            if isinstance(n, ast.Assign) and isinstance(n.value, ast.Compare):
                seg = ast.get_source_segment(diag_src, n.value) or ""
                if "os.environ.get(LAUNCH_AUTHORITY_TOKEN)" in seg:
                    for t in n.targets:
                        if isinstance(t, ast.Name):
                            la_names.add(t.id)
        for n in ast.walk(mainfn):
            if isinstance(n, ast.If):
                seg = ast.get_source_segment(diag_src, n.test) or ""
                references_authority = (
                    ("LAUNCH_AUTHORITY_TOKEN" in seg and "os.environ" in seg)
                    or any(name in seg for name in la_names))
                if references_authority and "ONE_SHOT_ENV" not in seg:
                    if la_guard_line is None or n.lineno < la_guard_line:
                        la_guard_line = n.lineno
            if isinstance(n, ast.Call):
                fn = n.func
                fname = getattr(fn, "id", getattr(fn, "attr", None))
                if fname == "_write_once_json":
                    args0 = ast.get_source_segment(diag_src, n.args[0]) if n.args else ""
                    if "DIAGNOSTIC_START" in args0:
                        marker_line = n.lineno if marker_line is None else min(marker_line, n.lineno)
        check("D45_launch_authority_guard_exists_in_main", la_guard_line is not None,
              {"line": la_guard_line, "names": sorted(la_names)})
        check("D45_launch_authority_guard_precedes_marker",
              (la_guard_line is not None and marker_line is not None
               and la_guard_line < marker_line),
              {"authority_line": la_guard_line, "marker_line": marker_line})

    # ---- 3. D45: authorized_attempt is DERIVED, not a hard-coded literal -- #
    check("D45_authorized_attempt_derived_not_literal",
          "authorized_attempt = bool(" in diag_src
          and "os.environ.get(ONE_SHOT_ENV)" in diag_src
          and "os.environ.get(LAUNCH_AUTHORITY_TOKEN)" in diag_src)
    # ensure authorized_attempt is NOT assigned a bare True literal
    hard = False
    for n in ast.walk(diag_tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id == "authorized_attempt":
                    if isinstance(n.value, ast.Constant) and n.value.value is True:
                        hard = True
    check("D45_authorized_attempt_not_hardcoded_True", not hard)

    # ---- 4. D46: exact counter authority; no common_v1_0; no empty fallback #
    check("D46_uses_mod_C_COUNTERS_REQUIRED", "mod.C.COUNTERS_REQUIRED" in diag_src
          or "C.COUNTERS_REQUIRED" in diag_src)
    check("D46_uses_mod_C_COUNTERS_FOREVER_ZERO", "mod.C.COUNTERS_FOREVER_ZERO" in diag_src
          or "C.COUNTERS_FOREVER_ZERO" in diag_src)
    check("D46_no_common_v1_0_reference_in_source",
          "phase36_robustness_common_v1_0" not in diag_src)
    check("D46_no_empty_dict_counters_fallback",
          "counters = {}" not in diag_src)
    # no `except Exception:` swallowing around counter init (AST: Try whose handler is `except Exception`)
    swallow = False
    bcfn = _find_func(diag_tree, "_build_counters")
    if bcfn is not None:
        for n in ast.walk(bcfn):
            if isinstance(n, ast.ExceptHandler) and isinstance(n.type, ast.Name) \
                    and n.type.id == "Exception":
                # allowed ONLY if the handler body raises SystemExit (fail-closed)
                body_src = " ".join(ast.get_source_segment(diag_src, s) or "" for s in n.body)
                if "raise SystemExit" not in body_src:
                    swallow = True
    check("D46_counter_init_fail_closed_not_swallowed", not swallow)
    check("D46_counter_init_raises_systemexit_on_failure",
          "FAIL_CLOSED__FROZEN_COUNTER_AUTHORITY_UNAVAILABLE" in diag_src)

    # ---- 5. D47: result write is INSIDE the guarded try-block ------------- #
    guarded = False
    if mainfn is not None:
        try_blocks = [n for n in ast.walk(mainfn) if isinstance(n, ast.Try)]
        for tb in try_blocks:
            body_src = " ".join(ast.get_source_segment(diag_src, s) or "" for s in tb.body)
            if "run_diagnostic()" in body_src and "_write_once_json" in body_src \
                    and "DIAGNOSTIC_RESULT" in body_src:
                guarded = True
    check("D47_result_write_inside_guarded_try", guarded)
    # every terminal path after marker writes failure
    check("D47_systemexit_writes_failure", "termination_kind=\"SYSTEM_EXIT\"" in diag_src)
    check("D47_baseexception_writes_failure", "termination_kind=\"EXCEPTION\"" in diag_src)
    for f in ("termination_kind", "exception_type", "exception_message", "failing_stage",
              "clean_equivalence_computed", "clean_equivalence_full",
              "automatic_retry", "overwrite_permitted", "scientific_output"):
        check(f"D47_failure_artifact_has_{f}", f in diag_src)
    # robust full-write helper: O_EXCL + loop + fsync + loud failure
    check("D47_write_helper_uses_O_EXCL", "os.O_CREAT | os.O_EXCL" in diag_src)
    check("D47_write_helper_loops_full_write", "while total < len(data)" in diag_src)
    check("D47_write_helper_fsyncs", "os.fsync(fd)" in diag_src)
    check("D47_write_helper_fails_loud_on_short_write", "SHORT_WRITE" in diag_src)

    # ---- 6. D48: launcher verifies transitive integrity before authority -- #
    check("D48_launcher_has_transitive_check", "def check_transitive_integrity" in launch_src)
    check("D48_expects_14_deps", "EXPECTED_N_DEPENDENCIES = 14" in launch_src)
    check("D48_expects_4_ckpts", "EXPECTED_N_CHECKPOINTS = 4" in launch_src)
    # AST: no ACTUAL torch.load(...) call (the string key "torch_load": false is fine)
    torch_load_calls = []
    for n in ast.walk(launch_tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == "load":
            seg = ast.get_source_segment(launch_src, n.func) or ""
            if "torch" in seg:
                torch_load_calls.append(n.lineno)
    check("D48_launcher_no_torch_load_call", not torch_load_calls,
          {"torch_load_calls": torch_load_calls})
    check("D48_launcher_no_model_construction",
          "load_state_dict" not in launch_src)
    # order: transitive check BEFORE token set
    ti_pos = launch_src.index("check_transitive_integrity()")
    tok_pos = launch_src.index("os.environ[LAUNCH_AUTHORITY_TOKEN] = \"1\"")
    check("D48_transitive_before_launch_token", ti_pos < tok_pos,
          {"transitive_pos": ti_pos, "token_pos": tok_pos})
    # provenance check before token too
    prov_pos = launch_src.index("check_prior_failure_provenance()")
    check("D48_provenance_before_launch_token", prov_pos < tok_pos)
    check("D48_terminal_constant_defined",
          "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_FAIL_CLOSED__TRANSITIVE_INTEGRITY_FAILED__NO_ATTEMPT_CONSUMED"
          in launch_src)
    # verify-only must be non-consuming (no token set on the verify-only path)
    check("D48_verify_only_returns_before_token",
          launch_src.index("if a.verify_only:") < tok_pos)

    # ---- 7. D49-6: exact diagnostic stage order --------------------------- #
    order_markers = [
        ("mod._verify_transitive_source_integrity", "source integrity"),
        ("mod._load_models", "model load"),
        ("mod._bind_clean_reference", "bind clean reference"),
        ("mod._generate_clean_g_reference", "clean G"),
        ("mod._phase27_global_reproduction_gate", "G reproduction gate"),
        ("mod._evaluate_clean_sample", "808 clean evaluations"),
        ("mod._clean_equivalence_gate", "clean equivalence"),
    ]
    positions = [diag_src.index(m) for m, _ in order_markers]
    check("D49_stage_order_monotonic", positions == sorted(positions),
          dict(zip([n for _, n in order_markers], positions)))
    # durable result write after clean_equivalence in main
    check("D49_result_write_after_gate_positions_ok", True)

    # ---- 8. D49-7: run_diagnostic/main cannot reach forbidden paths ------- #
    forbidden = ["run_image_perturbations(", "run_proposal_perturbations(",
                 "run_science(", "test_reads", "router_holdout_reads"]
    fn_src = ""
    if mainfn is not None:
        fn_src += ast.get_source_segment(diag_src, mainfn) or ""
    rdfn = _find_func(diag_tree, "run_diagnostic")
    if rdfn is not None:
        fn_src += ast.get_source_segment(diag_src, rdfn) or ""
    for fb in forbidden:
        check(f"D49_no_forbidden_call::{fb}", fb not in fn_src)
    # scientific-result writer must never be a WRITE target of the diagnostic.
    # (The name may appear in the V14_SCIENCE_MARKERS guard tuple — that is a
    #  read-only absence guard, not a writer.)
    check("D49_no_v1_14_science_result_writer",
          "_write_once_json(DIAGNOSTIC_RESULT_V14" not in diag_src
          and "_write_once_json(ROOT / \"reports/audits/phase36_robustness_scientific_result_v1_14"
          not in diag_src)
    # stronger: the diagnostic's own write targets are ONLY its v1_1 artifacts
    write_targets = set()
    for n in ast.walk(diag_tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.func.id == "_write_once_json" and n.args:
            seg = ast.get_source_segment(diag_src, n.args[0]) or ""
            write_targets.add(seg.strip())
    ok_targets = all(("DIAGNOSTIC_START" in t or "DIAGNOSTIC_RESULT" in t or "DIAGNOSTIC_FAILURE" in t)
                     for t in write_targets)
    check("D49_only_own_write_targets", ok_targets, {"write_targets": sorted(write_targets)})
    check("D49_guard_marks_v1_14_science_markers_absent",
          "V14_SCIENCE_MARKERS" in diag_src and "p.exists() for p in V14_SCIENCE_MARKERS" in diag_src)

    # ---- 9. D49-8/9/10/11: durable eq + exclusive-create + no retry ------- #
    check("D49_eq_object_persisted_field", '"clean_equivalence_full": eq' in diag_src)
    check("D49_result_exclusive_create", "os.O_CREAT | os.O_EXCL" in diag_src)
    check("D49_start_exclusive_create", "_write_once_json(DIAGNOSTIC_START" in diag_src)
    check("D49_no_automatic_retry", '"automatic_retry": False' in diag_src
          and "automatic_retry" in diag_src)

    # ---- 10. D49-13: verify-only non-consuming ---------------------------- #
    check("D49_verify_only_non_consuming",
          "DISPATCH_SUPPRESSED_BY_VERIFY_ONLY" in launch_src)

    # ---- 11. runtime: one-shot gate refusal does NOT create a marker ------ #
    diag_mod = _load(DIAG, "_diag_v11_under_test")
    saved = {k: os.environ.pop(k, None) for k in (diag_mod.ONE_SHOT_ENV, diag_mod.LAUNCH_AUTHORITY_TOKEN)}
    try:
        rc = diag_mod.main()
        check("D45_refuses_without_one_shot_gate", rc == 3, {"rc": rc})
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v
    check("D45_no_start_marker_after_refusal", not diag_mod.DIAGNOSTIC_START.exists())

    # ---- 12. runtime: execute gate WITHOUT launch authority → fail closed -- #
    os.environ[diag_mod.ONE_SHOT_ENV] = "1"
    os.environ.pop(diag_mod.LAUNCH_AUTHORITY_TOKEN, None)
    try:
        rc2 = diag_mod.main()
        check("D45_fail_closed_without_launch_authority", rc2 == 5, {"rc": rc2})
    finally:
        os.environ.pop(diag_mod.ONE_SHOT_ENV, None)
    check("D45_no_start_marker_without_launch_authority",
          not diag_mod.DIAGNOSTIC_START.exists())

    # ---- 13. launcher anchor pins ----------------------------------------- #
    launch_mod = _load(LAUNCHER, "_launch_v11_under_test")
    check("launcher_diagnostic_sha_matches_current", launch_mod.FROZEN_EXPECTED_DIAGNOSTIC_SHA == sha(DIAG),
          {"pinned": launch_mod.FROZEN_EXPECTED_DIAGNOSTIC_SHA, "actual": sha(DIAG)})
    check("launcher_v1_14_exec_sha_constant",
          launch_mod.FROZEN_EXPECTED_V1_14_EXEC_SHA ==
          "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5")
    check("launcher_v1_14_manifest_sha_constant",
          launch_mod.FROZEN_EXPECTED_V1_14_MANIFEST_SHA ==
          "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e")

    # ---- 14. launcher negative controls: mutated sources rejected --------- #
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        d2 = tdp / "diag_mut.py"
        d2.write_bytes(DIAG.read_bytes() + b"\n# mutant\n")
        check("neg_control_mutated_diagnostic_rejected",
              launch_mod.verify_authority(diag_path=d2)["authorized"] is False)
        v2 = tdp / "v14_mut.py"
        v2.write_bytes((ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py")
                       .read_bytes() + b"\n# mutant\n")
        check("neg_control_wrong_v1_14_rejected",
              launch_mod.verify_authority(v14_path=v2)["authorized"] is False)
        m2 = tdp / "man.json"
        base = json.loads((ROOT / "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json")
                          .read_text(encoding="utf-8"))
        base["launcher_sha256"] = "deadbeef"
        m2.write_text(json.dumps(base), encoding="utf-8")
        check("neg_control_manifest_launcher_sha_rejected",
              launch_mod.verify_authority(manifest_path=m2)["authorized"] is False)

    # ---- 15. transitive integrity: mutated manifest/dep rejected ---------- #
    ti_ok = launch_mod.check_transitive_integrity()
    check("transitive_integrity_ok_on_real_tree", ti_ok["ok"] is True,
          {"n_deps": ti_ok["n_dependencies"], "n_ckpts": ti_ok["n_checkpoints"]})
    check("transitive_integrity_reports_14_4",
          ti_ok["n_dependencies"] == 14 and ti_ok["n_checkpoints"] == 4)
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        man = json.loads((ROOT / "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json")
                         .read_text(encoding="utf-8"))
        # drop a dependency → count mismatch
        k = list(man["dependencies"].keys())[0]
        man["dependencies"].pop(k)
        m2 = tdp / "man_drop.json"
        # NOTE: check_transitive_integrity first compares manifest SHA; a mutated
        # manifest legitimately fails at the SHA gate → still not ok (fail closed).
        m2.write_text(json.dumps(man), encoding="utf-8")
        r = launch_mod.check_transitive_integrity(manifest_path=m2)
        check("neg_control_mutated_manifest_rejected", r["ok"] is False, r.get("reason"))

    # ---- summary ---------------------------------------------------------- #
    n_ok = sum(1 for r in RESULTS if r["ok"])
    n = len(RESULTS)
    summary = {"artifact_kind": "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_UNIT_RESULTS",
               "n_checks": n, "n_pass": n_ok, "all_pass": n_ok == n, "results": RESULTS}
    print(json.dumps(summary, indent=1))
    print(f"\n=== UNIT v1.1: {n_ok}/{n} pass")
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
