#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.0 — NEGATIVE CONTROLS (no model, no CUDA).

MUTATION-SENSITIVE controls for the new diagnostic family.  Every control FAILS if
the corresponding governance repair / GT prohibition is absent or weakened.

Headline: the diagnostic does NOT masquerade as the v1.14 launcher, and it NEVER
reads ground truth.
  * inherited FOREIGN v1.14 token (PHASE36_V1_14_LAUNCH_AUTHORITY=1)
    => launcher refuses before dispatch => no marker
    => diagnostic main() also refuses (rc 8) => no marker
  * GT runtime guard: any GT callable invocation fails closed and increments VAL_GT_READ

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\phase36_final_probability_authority_diagnostic_negative_controls_v1_0.py
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
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts" / "analysis"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

VENV = ROOT / ".venv" / "Scripts" / "python.exe"
AUD = ROOT / "reports" / "audits"
DIAG = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_0.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_0.py"
V14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
MANIFEST = AUD / "phase36_v1_14_runtime_source_integrity_manifest.json"

RESULTS: list = []

PRESERVED = {
    "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_0.py":
        "7cc51cceacfa314d7f84acb8a6dc482a2b46ea81de0ec695c0c8f0ca8b0b50f7",
    "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_0.py":
        "a34923faf6c27dd741ee1a1a1b4d1cbef1233664c2b02825e53b42c22c75b228",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_1.py":
        "04fa6252ff2533464553fb1a6c1f55ae009ee7ff00c1dbf89c1f901b089c839e",
    "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_1.py":
        "205dd4b877d8b6505c9479de9979087f19c341769ba2c5157a25701c212d14f6",
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
    "reports/audits/phase36_clean_equivalence_diagnostic_start_v1_1.json":
        "59b29875838ed6117a8441f422a17fa7bdae5088fc74b2b33a38f9c92e15fa68",
    "reports/audits/phase36_clean_equivalence_diagnostic_failure_v1_1.json":
        "ef6cf75f5d8432e69b89ddbef437c24b409cb325105a11f78a4c0f0004a57343",
    "reports/audits/phase36_clean_equivalence_diagnostic_v1_1_post_run_evidence.json":
        "a33066434cf569b77563a8028e842aefeac9a360e8e9479a3852bf9f401204af",
    "scripts/analysis/build_phase36_clean_equivalence_d51_adjudication_v1_0.py":
        "bc88a21d27b0466de8efe791f681494df08002b33deba40606724c86335aaee0",
    "scripts/analysis/build_phase36_clean_equivalence_d51_reconciliation_v1_1.py":
        "b89609d6b2f56c8d6e92c3852938d6002f6060ec75c472799d827c8d35ab1d5c",
    "reports/audits/phase36_clean_equivalence_d51_numerical_authority_adjudication_v1_0.json":
        "27ac7ada4ee39190d8823b8b1ff7e6e2beb304e2e7fc5778542883ac7eacc53a",
    "reports/audits/phase36_clean_equivalence_d51_reconciliation_v1_1.json":
        "d8e3e83e6c31004e610faef9d93c221c026eb8974c033f47fbff91106836758b",
}


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
    diag_mod = _load(DIAG, "_diag_fpa_nc")
    launch_mod = _load(LAUNCHER, "_launch_fpa_nc")
    FOREIGN = launch_mod.FOREIGN_V1_14_LAUNCH_TOKEN

    START = AUD / "phase36_final_probability_authority_diagnostic_start_v1_0.json"

    # ======================================================================= #
    # HEADLINE: foreign v1.14 token set => launcher refuses before dispatch,
    # no marker; diagnostic main() also refuses (rc 8), no marker.
    # ======================================================================= #
    assert not START.exists()

    fg = launch_mod.check_foreign_v1_14_token_absent({FOREIGN: "1"})
    check("HEADLINE_launcher_foreign_gate_refuses", fg["ok"] is False,
          {"foreign_token_present": fg["foreign_token_present"]})

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
          "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_FAIL_CLOSED__FOREIGN_V1_14_LAUNCH_AUTHORITY_PRESENT__NO_ATTEMPT_CONSUMED"
          in launcher_out)
    check("HEADLINE_no_marker_after_launcher_foreign_refusal", not START.exists())

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
    check("HEADLINE_no_marker_after_diagnostic_foreign_refusal", not START.exists())
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
    mutant_set = diag_src.replace(
        "    # ---- (1) one-shot execute gate",
        f'    os.environ["{FOREIGN}"] = "1"\n    # ---- (1) one-shot execute gate', 1)
    check("REQ2_mutant_foreign_token_write_detected",
          (f'os.environ["{FOREIGN}"]' in mutant_set) and (mutant_set != diag_src))

    # ======================================================================= #
    # REQ3 — foreign token inheritance path
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
    with tempfile.TemporaryDirectory() as td:
        v_mut = Path(td) / "v14_mut.py"
        v_mut.write_bytes(V14.read_bytes() + b"\n# mutant\n")
        ti_mut = launch_mod.check_transitive_integrity(v14_path=v_mut)
        check("REQ10_source_mutation_detected", ti_mut["ok"] is False, {"reason": ti_mut.get("reason")})
        src_bytes = V14.read_bytes()
        needle = b"edcdd33d22ae996b2f7ef60e8242a89f3cebab8c6992406508fec23cb068710c"
        if needle in src_bytes:
            tampered = src_bytes.replace(needle, b"feddd33d22ae996b2f7ef60e8242a89f3cebab8c6992406508fec23cb068710c", 1)
            v_tam = Path(td) / "v14_tam.py"
            v_tam.write_bytes(tampered)
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
    # REQ11 — consumed-evidence binding mutation detected
    # ======================================================================= #
    ce = launch_mod.check_consumed_evidence()
    check("REQ11_consumed_evidence_binding_ok_on_real_tree", ce["ok"] is True)
    orig = dict(launch_mod.CONSUMED_EVIDENCE_PROVENANCE)
    mut = dict(orig); mut["v1_2_result"] = (orig["v1_2_result"][0], "0" * 64)
    launch_mod.CONSUMED_EVIDENCE_PROVENANCE = mut
    try:
        ce_bad = launch_mod.check_consumed_evidence()
    finally:
        launch_mod.CONSUMED_EVIDENCE_PROVENANCE = orig
    check("REQ11_consumed_evidence_mutation_detected", ce_bad["ok"] is False)
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
    os.environ.pop(diag_mod.ONE_SHOT_ENV, None)
    os.environ.pop(diag_mod.LAUNCH_AUTHORITY_TOKEN, None)
    os.environ.pop(FOREIGN, None)
    rc3 = diag_mod.main(); check("REQ12_no_execute_gate_rc3", rc3 == 3, {"rc": rc3})
    os.environ[diag_mod.ONE_SHOT_ENV] = "1"
    try:
        rc5 = diag_mod.main()
    finally:
        os.environ.pop(diag_mod.ONE_SHOT_ENV, None)
    check("REQ12_no_launch_authority_rc5", rc5 == 5, {"rc": rc5})
    check("REQ12_no_marker_after_refusals", not START.exists())

    # ======================================================================= #
    # REQ13/14/15 — guarded write, comparison persistence, forbidden reachability
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
    check("REQ14_final_comparison_written", '"final_authority_comparison": cmp_,' in diag_src)
    for fb in ("run_image_perturbations", "run_proposal_perturbations", "run_science", "run_smoke"):
        check(f"REQ15_no_reach::{fb}", fb not in diag_src)

    # ======================================================================= #
    # REQ17 — static GT prohibition
    # ======================================================================= #
    for gtc in ("_load_val_gt", "full_field_gt", "_dice", "_iou", "_hd95"):
        check(f"REQ17_gt_static_no_call::{gtc}", not _calls(t, gtc))

    # ======================================================================= #
    # REQ18 — runtime GT guard fail-closed (fake module; no real model import)
    # ======================================================================= #
    fake = types.SimpleNamespace(
        _load_val_gt=lambda *a, **k: "GT",
        _dice=lambda *a, **k: 1.0,
        _iou=lambda *a, **k: 1.0,
        _hd95=lambda *a, **k: 1.0,
        canonical_learned_core=lambda *a, **k: {"ok": True},
    )
    g = diag_mod._install_gt_guards(fake)
    raised = 0
    for nm in ("_load_val_gt", "_dice", "_iou", "_hd95"):
        try:
            getattr(fake, nm)()
        except SystemExit:
            raised += 1
    check("REQ18_gt_guards_fail_closed", raised == 4, {"raised": raised})
    check("REQ18_gt_read_counter_incremented", g["VAL_GT_READ"] == 4, {"VAL_GT_READ": g["VAL_GT_READ"]})
    check("REQ18_non_gt_untouched", fake.canonical_learned_core() == {"ok": True})

    # ======================================================================= #
    # REQ19 — VAL_GT_READ == 0 contract enforced + recorded
    # ======================================================================= #
    check("REQ19_fail_closed_on_gt_read",
          "GT_READ_NONZERO" in diag_src and 'gt_guard["VAL_GT_READ"] != 0' in diag_src)
    check("REQ19_result_records_val_gt_read", '"VAL_GT_READ": int(gt_guard["VAL_GT_READ"])' in diag_src)

    # ======================================================================= #
    # REQ16 — preserved
    # ======================================================================= #
    for p, exp in PRESERVED.items():
        check(f"REQ16_preserved::{Path(p).name}", sha(ROOT / p) == exp)

    n_ok = sum(1 for r in RESULTS if r["ok"])
    n = len(RESULTS)
    print(json.dumps({"artifact_kind": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_0_NEGATIVE_CONTROL_RESULTS",
                      "n_checks": n, "n_pass": n_ok, "all_pass": n_ok == n,
                      "results": RESULTS}, indent=1))
    print(f"\n=== NEGATIVE CONTROLS v1.0 (final-prob authority): {n_ok}/{n} pass")
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
