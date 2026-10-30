#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.0 — UNIT TESTS (no model, no CUDA).

Mutation-sensitive validator suite for the NEW diagnostic family
``ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_0``:

 1. no call to mod._verify_transitive_source_integrity (D50) in diag or launcher
 2. no source/launcher assignment to PHASE36_V1_14_LAUNCH_AUTHORITY (D50-B)
 3. inherited foreign v1.14 token causes fail-closed BEFORE marker
 4. source transitive maps exactly equal manifest transitive maps (D50-A item 9)
 5. dependency removal detected
 6. checkpoint removal detected
 7. dependency SHA mutation detected
 8. checkpoint SHA mutation detected
 9. unexpected launcher_sha256 manifest key detected
10. exact v1.14 source mutation detected
11. consumed-evidence (v1.2 + D51) mutation detected
12. launch authority required before marker
13. result/failure write remains guarded (write-once discipline)
14. final-authority comparison persisted verbatim (not projected)
15. forbidden perturbation/science paths remain unreachable; only own write targets
16. preserved artifacts byte-for-byte (v1.0/v1.1/v1.2 + D51 + frozen v1.14)
17. STATIC GT PROHIBITION — no GT callable is actually called; no mask_path read
18. RUNTIME GT PROHIBITION — guard installs raising proxies; VAL_GT_READ increments
19. VAL_GT_READ == 0 contract is enforced (fail-closed) and recorded
20. the clean path STOPS at final_probability (no Dice/IoU/HD95 computation)

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\phase36_final_probability_authority_diagnostic_unit_v1_0.py
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

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts" / "analysis"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

DIAG = ROOT / "scripts" / "analysis" / "phase36_final_probability_authority_diagnostic_v1_0.py"
LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_final_probability_authority_diagnostic_v1_0.py"
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


def _subscript_read_keys(tree):
    """All string literal subscript keys read anywhere (e.g. row['mask_path'])."""
    keys = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Subscript):
            sl = n.slice
            if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                keys.add(sl.value)
    return keys


PRESERVED = {
    # v1.0 clean-equivalence diagnostic family
    "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_0.py":
        "7cc51cceacfa314d7f84acb8a6dc482a2b46ea81de0ec695c0c8f0ca8b0b50f7",
    "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_0.py":
        "a34923faf6c27dd741ee1a1a1b4d1cbef1233664c2b02825e53b42c22c75b228",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_0.py":
        "33e72386699aa0100c314846ffe2592f740ca7fb76e926a704cf4d46fbf78bf5",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_preflight_v1_0.py":
        "92c2d855e931d037e965d862a2ce0feb091d53e1bff0f91020f85729842e6653",
    # v1.1 clean-equivalence diagnostic family + consumed evidence
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
    # v1.2 clean-equivalence diagnostic family + consumed evidence
    "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_2.py":
        "24a638d47ddff164ec33d361ed742523f58c6cf8847d3ee9fbb02658a603d50e",
    "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_2.py":
        "1029c83b019ac76f331e528319fe2472ca5a7baac23b788c51de3297dcf7ff8e",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_2.py":
        "af9b374f89c0cbbf03c0c1f50bd107f39d549dd43289c23defc02815c4ba951f",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_preflight_v1_2.py":
        "bfa97ecf16a42ddaa51ba9f41f60a89bdf5076600d5b7bf0225b59ae5b9c6ddb",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_negative_controls_v1_2.py":
        "3551847a6a8b6d5b8ef5a0cfd0831eb4e0cf59385b146d6eb2af51981297fbbb",
    "reports/audits/phase36_clean_equivalence_diagnostic_start_v1_2.json":
        "be93d494b1aa2aad3c900f442c16efe55bcbf0bd508a72df8f8b83e72cd7d2d3",
    "reports/audits/phase36_clean_equivalence_diagnostic_result_v1_2.json":
        "b64f7e6282f9abb864a5d5bc438a22e1096aaf56e0a4e94fe53ba7c9bab6fa4a",
    "reports/audits/phase36_clean_equivalence_diagnostic_stdout_first_attempt_v1_2.txt":
        "515d56d180a0e8ba277d3f73397cd3297b21e81806c93a18be65cb5f66026380",
    "reports/audits/phase36_clean_equivalence_diagnostic_stderr_first_attempt_v1_2.txt":
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    # D51 adjudication line
    "scripts/analysis/build_phase36_clean_equivalence_d51_adjudication_v1_0.py":
        "bc88a21d27b0466de8efe791f681494df08002b33deba40606724c86335aaee0",
    "scripts/analysis/build_phase36_clean_equivalence_d51_reconciliation_v1_1.py":
        "b89609d6b2f56c8d6e92c3852938d6002f6060ec75c472799d827c8d35ab1d5c",
    "reports/audits/phase36_clean_equivalence_d51_numerical_authority_adjudication_v1_0.json":
        "27ac7ada4ee39190d8823b8b1ff7e6e2beb304e2e7fc5778542883ac7eacc53a",
    "reports/audits/phase36_clean_equivalence_d51_reconciliation_v1_1.json":
        "d8e3e83e6c31004e610faef9d93c221c026eb8974c033f47fbff91106836758b",
    # frozen v1.14 tree
    "scripts/analysis/phase36_robustness_execution_v1_14.py":
        "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5",
    "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json":
        "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e",
}

GT_CALLABLES = ("_load_val_gt", "full_field_gt", "_dice", "_iou", "_hd95")


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
    check("REQ1_diagnostic_marks_omission", "d50_foreign_gate_call_omitted" in diag_src)

    # ---------------- 2. no assignment to the foreign token ------------------- #
    FOREIGN = "PHASE36_V1_14_LAUNCH_AUTHORITY"
    diag_writes = _env_subscript_writes(diag_tree)
    launch_writes = _env_subscript_writes(launch_tree)
    check("REQ2_diagnostic_no_foreign_token_write", FOREIGN not in diag_writes,
          {"env_writes": sorted(diag_writes)})
    check("REQ2_launcher_no_foreign_token_write", FOREIGN not in launch_writes,
          {"env_writes": sorted(launch_writes)})
    check("REQ2_foreign_token_declared_as_constant_only",
          f'FOREIGN_V1_14_LAUNCH_TOKEN = "{FOREIGN}"' in diag_src
          and f'FOREIGN_V1_14_LAUNCH_TOKEN = "{FOREIGN}"' in launch_src)

    # ---------------- 3. inherited foreign token => fail closed, no marker ---- #
    diag_mod = _load(DIAG, "_diag_fpa_ut")
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

    launch_mod = _load(LAUNCHER, "_launch_fpa_ut")
    fg_bad = launch_mod.check_foreign_v1_14_token_absent({FOREIGN: "1"})
    fg_ok = launch_mod.check_foreign_v1_14_token_absent({})
    check("REQ3_launcher_foreign_gate_flags_present", fg_bad["ok"] is False,
          {"foreign_token_present": fg_bad["foreign_token_present"]})
    check("REQ3_launcher_foreign_gate_passes_absent", fg_ok["ok"] is True)

    # ---------------- 4. source transitive maps == manifest maps ------------- #
    ti = launch_mod.check_transitive_integrity()
    check("REQ4_real_tree_transitive_ok", ti["ok"] is True, {"reason": ti.get("reason")})
    check("REQ4_real_source_manifest_authority_exact_match",
          ti["source_manifest_transitive_authority_exact_match"] is True)
    check("REQ4_real_tree_is_14_4",
          ti["n_dependencies"] == 14 and ti["n_checkpoints"] == 4)
    check("REQ4_no_io_flags",
          ti["torch_load"] is False and ti["checkpoint_deserialization"] is False
          and ti["model_construction"] is False and ti["val_or_gt_read"] is False)
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

    # ---------------- 5/6/7/8/9 mutation-sensitive (pin-patched) -------------- #
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
    r = _run_with_manifest(m)
    check("REQ5_dependency_removal_detected", r["ok"] is False,
          {"reason": r.get("reason"), "n_deps": r["n_dependencies"]})
    m = json.loads(json.dumps(real_man)); m["checkpoints"].pop(list(m["checkpoints"].keys())[0])
    r = _run_with_manifest(m)
    check("REQ6_checkpoint_removal_detected", r["ok"] is False,
          {"reason": r.get("reason"), "n_ckpts": r["n_checkpoints"]})
    m = json.loads(json.dumps(real_man)); k = list(m["dependencies"].keys())[0]
    m["dependencies"][k] = "0" * 64
    r = _run_with_manifest(m)
    check("REQ7_dependency_sha_mutation_detected", r["ok"] is False, {"reason": r.get("reason")})
    m = json.loads(json.dumps(real_man)); k = list(m["checkpoints"].keys())[0]
    m["checkpoints"][k] = "0" * 64
    r = _run_with_manifest(m)
    check("REQ8_checkpoint_sha_mutation_detected", r["ok"] is False, {"reason": r.get("reason")})
    m = json.loads(json.dumps(real_man)); m["launcher_sha256"] = "deadbeef"
    r = _run_with_manifest(m)
    check("REQ9_unexpected_launcher_sha_key_detected", r["ok"] is False,
          {"launcher_sha256_absent": r.get("launcher_sha256_absent")})

    # ---------------- 10. exact v1.14 source mutation detected ---------------- #
    with tempfile.TemporaryDirectory() as td:
        v_mut = Path(td) / "v14_mut.py"
        v_mut.write_bytes(V14.read_bytes() + b"\n# mutant\n")
        ti_mut = launch_mod.check_transitive_integrity(v14_path=v_mut)
        check("REQ10_v1_14_source_mutation_detected_in_transitive",
              ti_mut["ok"] is False, {"reason": ti_mut.get("reason")})
        auth_mut = launch_mod.verify_authority(v14_path=v_mut)
        check("REQ10_v1_14_source_mutation_detected_in_anchor",
              auth_mut["authorized"] is False)

    # ---------------- 11. consumed-evidence mutation detected ----------------- #
    m = json.loads(json.dumps(real_man))
    m["dependencies"][list(m["dependencies"].keys())[0]] = "1" * 64
    r = _run_with_manifest(m)
    check("REQ11_authority_inequality_surfaces_as_mismatch",
          r["ok"] is False and r["source_manifest_transitive_authority_exact_match"] is False,
          {"reason": r.get("reason")})
    ce = launch_mod.check_consumed_evidence()
    check("REQ11_consumed_evidence_binding_ok_on_real_tree", ce["ok"] is True,
          {"predicates": ce["predicates"]})
    orig_ce = dict(launch_mod.CONSUMED_EVIDENCE_PROVENANCE)
    mutated = dict(orig_ce)
    mutated["v1_2_result"] = (orig_ce["v1_2_result"][0], "0" * 64)
    launch_mod.CONSUMED_EVIDENCE_PROVENANCE = mutated
    try:
        ce_bad = launch_mod.check_consumed_evidence()
    finally:
        launch_mod.CONSUMED_EVIDENCE_PROVENANCE = orig_ce
    check("REQ11_consumed_evidence_sha_mutation_detected", ce_bad["ok"] is False)
    # predicate-level mutation: wrong D51 reconciliation verdict must fail
    orig_rec = launch_mod.REQUIRED_D51_RECONCILIATION_VERDICT
    launch_mod.REQUIRED_D51_RECONCILIATION_VERDICT = "SOME_OTHER_VERDICT"
    try:
        ce_pred_bad = launch_mod.check_consumed_evidence()
    finally:
        launch_mod.REQUIRED_D51_RECONCILIATION_VERDICT = orig_rec
    check("REQ11_consumed_evidence_predicate_mutation_detected", ce_pred_bad["ok"] is False)

    # ---------------- 12. launch authority required before marker ------------- #
    mainfn = _find_func(diag_tree, "main")
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
    os.environ[diag_mod.LAUNCH_AUTHORITY_TOKEN] = "1"
    try:
        rc_no_gate = diag_mod.main()
    finally:
        os.environ.pop(diag_mod.LAUNCH_AUTHORITY_TOKEN, None)
    check("REQ12_no_execute_gate_rc3", rc_no_gate == 3, {"rc": rc_no_gate})
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

    # ---------------- 14. final-authority comparison persisted verbatim ------- #
    check("REQ14_final_comparison_persisted", '"final_authority_comparison": cmp_' in diag_src)
    rdfn = _find_func(diag_tree, "run_diagnostic")
    cmp_assigned = False
    if rdfn is not None:
        seg = ast.get_source_segment(diag_src, rdfn) or ""
        cmp_assigned = ("_compare_final_authority(" in seg
                        and "cmp_ = _compare_final_authority" in seg)
    check("REQ14_comparison_assigned_from_own_fn", cmp_assigned)
    check("REQ14_phase27_final_authority_declared",
          'PHASE27_FINAL_PROB_AUTHORITY' in diag_src
          and "phase27_val808_final_prob_f16.npy" in diag_src)

    # ---------------- 15. forbidden perturbation/science unreachable ---------- #
    forbidden_calls = ["run_image_perturbations", "run_proposal_perturbations",
                       "run_science", "run_smoke"]
    fn_src = ""
    if mainfn is not None:
        fn_src += ast.get_source_segment(diag_src, mainfn) or ""
    if rdfn is not None:
        fn_src += ast.get_source_segment(diag_src, rdfn) or ""
    for fb in forbidden_calls:
        check(f"REQ15_no_forbidden_call::{fb}", fb not in fn_src)
    targets = set()
    for n in ast.walk(diag_tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.func.id == "_write_once_json" and n.args:
            targets.add((ast.get_source_segment(diag_src, n.args[0]) or "").strip())
    ok_targets = bool(targets) and all(
        ("DIAGNOSTIC_START" in t or "DIAGNOSTIC_RESULT" in t or "DIAGNOSTIC_FAILURE" in t)
        for t in targets)
    check("REQ15_only_own_write_targets", ok_targets, {"targets": sorted(targets)})

    # ---------------- 16. preserved byte-for-byte ----------------------------- #
    for p, exp in PRESERVED.items():
        check(f"REQ16_preserved::{Path(p).name}", sha(ROOT / p) == exp,
              {"observed": sha(ROOT / p)})

    # ---------------- 17. STATIC GT PROHIBITION ------------------------------- #
    for gtc in GT_CALLABLES:
        check(f"REQ17_no_actual_call::{gtc}", not _has_actual_call(diag_tree, gtc),
              {"lines": _has_actual_call(diag_tree, gtc)})
    read_keys = _subscript_read_keys(diag_tree)
    check("REQ17_no_mask_path_subscript_read", "mask_path" not in read_keys,
          {"subscript_keys": sorted(read_keys)})
    check("REQ17_gt_callables_declared_forbidden",
          'GT_FORBIDDEN_CALLABLES' in diag_src and 'GT_FORBIDDEN_ROW_KEYS' in diag_src)

    # ---------------- 18. RUNTIME GT PROHIBITION ------------------------------ #
    fake = types.SimpleNamespace(
        _load_val_gt=lambda *a, **k: "GT",
        _dice=lambda *a, **k: 1.0,
        _iou=lambda *a, **k: 1.0,
        _hd95=lambda *a, **k: 1.0,
        canonical_learned_core=lambda *a, **k: {"ok": True},
        _load_clean_image_tensor=lambda *a, **k: "IMG",
    )
    g = diag_mod._install_gt_guards(fake)
    installed = set(g["installed"])
    check("REQ18_guard_installed_expected_callables",
          {"_load_val_gt", "_dice", "_iou", "_hd95"} <= installed,
          {"installed": sorted(installed)})
    raised = 0
    for nm in ("_load_val_gt", "_dice", "_iou", "_hd95"):
        try:
            getattr(fake, nm)()
        except SystemExit:
            raised += 1
    check("REQ18_all_guards_raise_systemexit", raised == 4, {"raised": raised})
    check("REQ18_val_gt_read_incremented", g["VAL_GT_READ"] == 4,
          {"VAL_GT_READ": g["VAL_GT_READ"]})
    check("REQ18_non_gt_callable_untouched",
          fake.canonical_learned_core() == {"ok": True})

    # ---------------- 19. VAL_GT_READ == 0 contract --------------------------- #
    check("REQ19_fail_closed_on_nonzero_gt_read",
          "GT_READ_NONZERO" in diag_src and 'gt_guard["VAL_GT_READ"] != 0' in diag_src)
    check("REQ19_result_records_val_gt_read", '"VAL_GT_READ": int(gt_guard["VAL_GT_READ"])' in diag_src)
    check("REQ19_failure_records_val_gt_read_zero", '"VAL_GT_READ": 0,' in diag_src)

    # ---------------- 20. clean path STOPS at final_probability --------------- #
    check("REQ20_stops_at_final_probability",
          'np.asarray(out["final_probability"], dtype=np.float32)' in diag_src)
    check("REQ20_no_dice_iou_hd95_call",
          not any(_has_actual_call(diag_tree, nm) for nm in ("_dice", "_iou", "_hd95")))
    check("REQ20_gt_read_false_in_result", '"gt_read": False,' in diag_src)
    check("REQ20_scientific_output_false", '"scientific_output": False' in diag_src)
    check("REQ20_robustness_result_false", '"robustness_result": False' in diag_src)

    # ---------------- launcher anchors / pins --------------------------------- #
    check("launcher_pin_matches_actual_diagnostic",
          launch_mod.FROZEN_EXPECTED_DIAGNOSTIC_SHA == sha(DIAG),
          {"pinned": launch_mod.FROZEN_EXPECTED_DIAGNOSTIC_SHA, "actual": sha(DIAG)})
    check("launcher_v1_0_token_constant",
          launch_mod.LAUNCH_AUTHORITY_TOKEN == "PHASE36_FINAL_PROB_AUTHORITY_V1_0_LAUNCH_AUTHORITY")
    check("launcher_one_shot_env",
          launch_mod.ONE_SHOT_ENV == "PHASE36_FINAL_PROB_AUTHORITY_EXECUTE")
    check("launcher_foreign_constant",
          launch_mod.FOREIGN_V1_14_LAUNCH_TOKEN == "PHASE36_V1_14_LAUNCH_AUTHORITY")
    tl = []
    for n in ast.walk(launch_tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == "load":
            seg = ast.get_source_segment(launch_src, n.func) or ""
            if "torch" in seg:
                tl.append(n.lineno)
    check("launcher_no_torch_load", not tl, {"lines": tl})
    check("launcher_no_load_state_dict", "load_state_dict" not in launch_src)
    tok_pos = launch_src.index('os.environ[LAUNCH_AUTHORITY_TOKEN] = "1"')
    check("launcher_foreign_gate_before_token",
          launch_src.index("check_foreign_v1_14_token_absent()") < tok_pos)
    check("launcher_transitive_before_token",
          launch_src.index("check_transitive_integrity()") < tok_pos)
    check("launcher_consumed_evidence_before_token",
          launch_src.index("check_consumed_evidence()") < tok_pos)
    check("launcher_verify_only_before_token", launch_src.index("if a.verify_only:") < tok_pos)

    n_ok = sum(1 for r in RESULTS if r["ok"])
    n = len(RESULTS)
    print(json.dumps({"artifact_kind": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_UNIT_RESULTS",
                      "n_checks": n, "n_pass": n_ok, "all_pass": n_ok == n,
                      "results": RESULTS}, indent=1))
    print(f"\n=== UNIT v1.0 (final-prob authority): {n_ok}/{n} pass")
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
