#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — CLEAN EQUIVALENCE DIAGNOSTIC v1.2 — NEGATIVE CONTROLS (no model, no CUDA).

MUTATION-SENSITIVE controls for the D50 governance repair.  Every control FAILS if
the corresponding repair is absent or weakened.  The headline control proves the
diagnostic does NOT masquerade as the v1.14 launcher:

  * inherited FOREIGN v1.14 token (PHASE36_V1_14_LAUNCH_AUTHORITY=1)
    => launcher refuses before diagnostic dispatch => no marker
    => diagnostic main() also refuses (rc 8) => no marker

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\phase36_clean_equivalence_diagnostic_negative_controls_v1_2.py
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts" / "analysis"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

VENV = ROOT / ".venv" / "Scripts" / "python.exe"
AUD = ROOT / "reports" / "audits"
DIAG = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_2.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_2.py"
V14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
MANIFEST = AUD / "phase36_v1_14_runtime_source_integrity_manifest.json"

RESULTS: list = []


def sha(p: Path) -> str:
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except FileNotFoundError:
        return "ABSENT"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def check(name, ok, detail=None):
    RESULTS.append({"name": name, "ok": bool(ok), "detail": detail})


def _tree(p: Path):
    return ast.parse(Path(p).read_text(encoding="utf-8"))


def _calls(tree, fname):
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            nm = getattr(f, "id", None) or getattr(f, "attr", None)
            if nm == fname:
                out.append(n.lineno)
    return out


def main() -> int:
    diag_mod = _load(DIAG, "_diag_v12_nc")
    launch_mod = _load(LAUNCHER, "_launch_v12_nc")
    FOREIGN = launch_mod.FOREIGN_V1_14_LAUNCH_TOKEN

    # ======================================================================= #
    # HEADLINE: foreign v1.14 token set => launcher refuses before dispatch,
    # no marker; diagnostic main() also refuses (rc 8), no marker.
    # ======================================================================= #
    assert not (AUD / "phase36_clean_equivalence_diagnostic_start_v1_2.json").exists()

    # launcher gate (pure function)
    fg = launch_mod.check_foreign_v1_14_token_absent({FOREIGN: "1"})
    check("HEADLINE_launcher_foreign_gate_refuses", fg["ok"] is False,
          {"foreign_token_present": fg["foreign_token_present"]})
    # launcher end-to-end: foreign token set -> refuses (rc 2) without dispatch
    saved_env = {k: os.environ.pop(k, None)
                 for k in (FOREIGN, diag_mod.ONE_SHOT_ENV, diag_mod.LAUNCH_AUTHORITY_TOKEN)}
    os.environ[FOREIGN] = "1"
    try:
        p = subprocess.run([str(VENV), str(LAUNCHER)], capture_output=True, text=True,
                           env=dict(os.environ))
        launcher_rc = p.returncode
        launcher_out = p.stdout
    finally:
        os.environ.pop(FOREIGN, None)
    check("HEADLINE_launcher_refuses_with_foreign_token", launcher_rc == 2, {"rc": launcher_rc})
    check("HEADLINE_launcher_terminal_foreign_fail_closed",
          "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_FAIL_CLOSED__FOREIGN_V1_14_LAUNCH_AUTHORITY_PRESENT__NO_ATTEMPT_CONSUMED"
          in launcher_out)
    check("HEADLINE_no_marker_after_launcher_foreign_refusal",
          not (AUD / "phase36_clean_equivalence_diagnostic_start_v1_2.json").exists())

    # diagnostic main() with foreign token set (and everything else authorized)
    os.environ[diag_mod.ONE_SHOT_ENV] = "1"
    os.environ[diag_mod.LAUNCH_AUTHORITY_TOKEN] = "1"
    os.environ[FOREIGN] = "1"
    try:
        rc_foreign = diag_mod.main()
    finally:
        os.environ.pop(FOREIGN, None)
        os.environ.pop(diag_mod.ONE_SHOT_ENV, None)
        os.environ.pop(diag_mod.LAUNCH_AUTHORITY_TOKEN, None)
    check("HEADLINE_diagnostic_refuses_with_foreign_token", rc_foreign == 8, {"rc": rc_foreign})
    check("HEADLINE_no_marker_after_diagnostic_foreign_refusal",
          not (AUD / "phase36_clean_equivalence_diagnostic_start_v1_2.json").exists())
    for k, v in saved_env.items():
        if v is not None:
            os.environ[k] = v

    # ======================================================================= #
    # REQ1/2 — static: no forbidden call, no foreign-token write
    # ======================================================================= #
    check("REQ1_no_forbidden_gate_call_diag", not _calls(_tree(DIAG), "_verify_transitive_source_integrity"))
    check("REQ1_no_forbidden_gate_call_launch", not _calls(_tree(LAUNCHER), "_verify_transitive_source_integrity"))
    diag_src = DIAG.read_text(encoding="utf-8")
    launch_src = LAUNCHER.read_text(encoding="utf-8")
    check("REQ2_diag_no_foreign_token_write",
          f'os.environ["{FOREIGN}"]' not in diag_src and f"os.environ['{FOREIGN}']" not in diag_src)
    check("REQ2_launch_no_foreign_token_write",
          f'os.environ["{FOREIGN}"]' not in launch_src and f"os.environ['{FOREIGN}']" not in launch_src)

    # mutation-sensitive: a mutant that DOES set the foreign token must be detectable
    mutant_set = diag_src.replace(
        "    # ---- D50-C (1) one-shot execute gate",
        f'    os.environ["{FOREIGN}"] = "1"\n    # ---- D50-C (1) one-shot execute gate', 1)
    detected = (f'os.environ["{FOREIGN}"]' in mutant_set) and (mutant_set != diag_src)
    check("REQ2_mutant_foreign_token_write_detected", detected)

    # ======================================================================= #
    # REQ3 — foreign token inheritance path (launcher pure gate + end-to-end)
    # ======================================================================= #
    check("REQ3_gate_ok_when_absent", launch_mod.check_foreign_v1_14_token_absent({})["ok"] is True)
    check("REQ3_gate_refuses_when_present",
          launch_mod.check_foreign_v1_14_token_absent({FOREIGN: "1"})["ok"] is False)

    # ======================================================================= #
    # REQ4 — source transitive maps exactly equal manifest (real tree)
    # ======================================================================= #
    ti = launch_mod.check_transitive_integrity()
    check("REQ4_real_tree_ok", ti["ok"] is True, {"reason": ti.get("reason")})
    check("REQ4_exact_authority_match", ti["source_manifest_transitive_authority_exact_match"] is True)
    check("REQ4_set_equal_deps", ti["authority_set_equal"]["dependencies"] is True)
    check("REQ4_set_equal_ckpts", ti["authority_set_equal"]["checkpoints"] is True)
    check("REQ4_sha_equal_deps", ti["authority_sha_equal"]["dependencies"] is True)
    check("REQ4_sha_equal_ckpts", ti["authority_sha_equal"]["checkpoints"] is True)

    # ======================================================================= #
    # REQ5..REQ10 — mutation-sensitive (pin-patched manifest / mutant v1.14)
    # ======================================================================= #
    real_man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    orig_man_sha = launch_mod.FROZEN_EXPECTED_V1_14_MANIFEST_SHA

    def run_mut(mut):
        with tempfile.TemporaryDirectory() as td:
            mp = Path(td) / "m.json"
            mp.write_text(json.dumps(mut), encoding="utf-8")
            try:
                launch_mod.FROZEN_EXPECTED_V1_14_MANIFEST_SHA = launch_mod.sha(mp)
                return launch_mod.check_transitive_integrity(manifest_path=mp)
            finally:
                launch_mod.FROZEN_EXPECTED_V1_14_MANIFEST_SHA = orig_man_sha

    m = json.loads(json.dumps(real_man)); m["dependencies"].pop(list(m["dependencies"].keys())[0])
    r = run_mut(m); check("REQ5_dep_removal_detected", r["ok"] is False, {"reason": r.get("reason")})
    m = json.loads(json.dumps(real_man)); m["checkpoints"].pop(list(m["checkpoints"].keys())[0])
    r = run_mut(m); check("REQ6_ckpt_removal_detected", r["ok"] is False, {"reason": r.get("reason")})
    m = json.loads(json.dumps(real_man)); m["dependencies"][list(m["dependencies"].keys())[0]] = "0" * 64
    r = run_mut(m); check("REQ7_dep_sha_mutation_detected", r["ok"] is False, {"reason": r.get("reason")})
    m = json.loads(json.dumps(real_man)); m["checkpoints"][list(m["checkpoints"].keys())[0]] = "0" * 64
    r = run_mut(m); check("REQ8_ckpt_sha_mutation_detected", r["ok"] is False, {"reason": r.get("reason")})
    m = json.loads(json.dumps(real_man)); m["launcher_sha256"] = "deadbeef"
    r = run_mut(m); check("REQ9_launcher_sha_key_detected", r["ok"] is False,
                          {"launcher_sha256_absent": r.get("launcher_sha256_absent")})
    # REQ10 — exact v1.14 source mutation
    with tempfile.TemporaryDirectory() as td:
        v_mut = Path(td) / "v14_mut.py"
        v_mut.write_bytes(V14.read_bytes() + b"\n# mutant\n")
        ti_mut = launch_mod.check_transitive_integrity(v14_path=v_mut)
        check("REQ10_source_mutation_detected", ti_mut["ok"] is False, {"reason": ti_mut.get("reason")})
        # source-map literal tamper (change one SHA inside the map) -> exact-match fails
        src_bytes = V14.read_bytes()
        # flip a digit inside a known dependency SHA token
        needle = b"edcdd33d22ae996b2f7ef60e8242a89f3cebab8c6992406508fec23cb068710c"
        if needle in src_bytes:
            tampered = src_bytes.replace(needle, b"feddd33d22ae996b2f7ef60e8242a89f3cebab8c6992406508fec23cb068710c", 1)
            v_tam = Path(td) / "v14_tam.py"
            v_tam.write_bytes(tampered)
            # pin the source SHA to the tampered file's SHA so the source-SHA gate passes
            # and the SOURCE<->MANIFEST equality check is what fires.
            orig_exec_sha = launch_mod.FROZEN_EXPECTED_V1_14_EXEC_SHA
            try:
                launch_mod.FROZEN_EXPECTED_V1_14_EXEC_SHA = launch_mod.sha(v_tam)
                ti_tam = launch_mod.check_transitive_integrity(v14_path=v_tam)
            finally:
                launch_mod.FROZEN_EXPECTED_V1_14_EXEC_SHA = orig_exec_sha
            check("REQ10a_source_map_tamper_detected_via_exact_match", ti_tam["ok"] is False,
                  {"reason": ti_tam.get("reason"),
                   "exact_match": ti_tam.get("source_manifest_transitive_authority_exact_match")})
        else:
            check("REQ10a_source_map_tamper_detected_via_exact_match", False,
                  {"note": "needle SHA not found"})

    # ======================================================================= #
    # REQ11 — v1.1 failure provenance mutation detected
    # ======================================================================= #
    v11 = launch_mod.check_consumed_v1_1_failure()
    check("REQ11_v1_1_binding_ok_on_real_tree", v11["ok"] is True)
    orig = dict(launch_mod.CONSUMED_V1_1_PROVENANCE)
    mut = dict(orig); mut["v1_1_failure"] = (orig["v1_1_failure"][0], "0" * 64)
    launch_mod.CONSUMED_V1_1_PROVENANCE = mut
    try:
        v11_bad = launch_mod.check_consumed_v1_1_failure()
    finally:
        launch_mod.CONSUMED_V1_1_PROVENANCE = orig
    check("REQ11_v1_1_failure_mutation_detected", v11_bad["ok"] is False)
    # provenance mutation via SHA
    orig_p = dict(launch_mod.PRIOR_FAILURE_PROVENANCE)
    mutp = dict(orig_p); mutp["v1_14_science_failure"] = (orig_p["v1_14_science_failure"][0], "0" * 64)
    launch_mod.PRIOR_FAILURE_PROVENANCE = mutp
    try:
        p_bad = launch_mod.check_prior_failure_provenance()
    finally:
        launch_mod.PRIOR_FAILURE_PROVENANCE = orig_p
    check("REQ11_prior_failure_mutation_detected", p_bad["ok"] is False)

    # ======================================================================= #
    # REQ12 — launch authority required before marker (runtime rc)
    # ======================================================================= #
    # execute gate ABSENT -> rc 3
    os.environ.pop(diag_mod.ONE_SHOT_ENV, None)
    os.environ.pop(diag_mod.LAUNCH_AUTHORITY_TOKEN, None)
    os.environ.pop(FOREIGN, None)
    rc3 = diag_mod.main(); check("REQ12_no_execute_gate_rc3", rc3 == 3, {"rc": rc3})
    # execute gate SET, authority ABSENT -> rc 5
    os.environ[diag_mod.ONE_SHOT_ENV] = "1"
    try:
        rc5 = diag_mod.main()
    finally:
        os.environ.pop(diag_mod.ONE_SHOT_ENV, None)
    check("REQ12_no_launch_authority_rc5", rc5 == 5, {"rc": rc5})
    check("REQ12_no_marker_after_refusals",
          not (AUD / "phase36_clean_equivalence_diagnostic_start_v1_2.json").exists())

    # ======================================================================= #
    # REQ13/14/15 — guarded write, eq persistence, forbidden reachability
    # ======================================================================= #
    t = _tree(DIAG)
    mainfn = None
    for n in ast.walk(t):
        if isinstance(n, ast.FunctionDef) and n.name == "main":
            mainfn = n
    guarded = False
    for tb in [n for n in ast.walk(mainfn) if isinstance(n, ast.Try)]:
        body = " ".join(ast.get_source_segment(diag_src, s) or "" for s in tb.body)
        if "run_diagnostic()" in body and "_write_once_json" in body and "DIAGNOSTIC_RESULT" in body:
            guarded = True
    check("REQ13_result_write_guarded", guarded)
    check("REQ14_full_eq_written", '"clean_equivalence_full": eq,' in diag_src)
    for fb in ("run_image_perturbations", "run_proposal_perturbations", "run_science", "run_smoke"):
        check(f"REQ15_no_reach::{fb}", fb not in diag_src)

    # ======================================================================= #
    # REQ16 — v1.0/v1.1 preserved
    # ======================================================================= #
    preserved = {
        "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_0.py":
            "7cc51cceacfa314d7f84acb8a6dc482a2b46ea81de0ec695c0c8f0ca8b0b50f7",
        "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_0.py":
            "a34923faf6c27dd741ee1a1a1b4d1cbef1233664c2b02825e53b42c22c75b228",
        "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_1.py":
            "04fa6252ff2533464553fb1a6c1f55ae009ee7ff00c1dbf89c1f901b089c839e",
        "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_1.py":
            "205dd4b877d8b6505c9479de9979087f19c341769ba2c5157a25701c212d14f6",
        "reports/audits/phase36_clean_equivalence_diagnostic_start_v1_1.json":
            "59b29875838ed6117a8441f422a17fa7bdae5088fc74b2b33a38f9c92e15fa68",
        "reports/audits/phase36_clean_equivalence_diagnostic_failure_v1_1.json":
            "ef6cf75f5d8432e69b89ddbef437c24b409cb325105a11f78a4c0f0004a57343",
        "reports/audits/phase36_clean_equivalence_diagnostic_v1_1_post_run_evidence.json":
            "a33066434cf569b77563a8028e842aefeac9a360e8e9479a3852bf9f401204af",
    }
    for p, exp in preserved.items():
        check(f"REQ16_preserved::{Path(p).name}", sha(ROOT / p) == exp)

    n_ok = sum(1 for r in RESULTS if r["ok"])
    n = len(RESULTS)
    print(json.dumps({"artifact_kind": "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_NEGATIVE_CONTROL_RESULTS",
                      "n_checks": n, "n_pass": n_ok, "all_pass": n_ok == n,
                      "results": RESULTS}, indent=1))
    print(f"\n=== NEGATIVE CONTROLS v1.2: {n_ok}/{n} pass")
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
