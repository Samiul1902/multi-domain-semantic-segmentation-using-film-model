#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.1 — NEGATIVE CONTROLS (no model, no CUDA).

MUTATION-SENSITIVE controls for the ADDITIVE v1.1 repair of D52/D53/D54.  Every
control FAILS if the corresponding governance repair / GT prohibition is absent
or weakened.

  * HEADLINE: inherited FOREIGN v1.14 token => launcher refuses (rc 2) before
    dispatch; diagnostic main() refuses (rc 8); no marker.
  * D52: the launcher final-authority pre-consumption gate detects
    authority-missing / SHA-mutation / wrong-shape / wrong-dtype /
    sample-order-mismatch (CSV order + fg-pixel row binding) BEFORE any marker.
  * D53: a guarded GT callable mutates a SHARED runtime-evidence state and the
    failure artifact records the ACTUAL ``VAL_GT_READ`` (never a hardcoded 0).
  * D54: a forced result-write failure AFTER a completed comparison preserves the
    computed evidence in the failure artifact and emits the evidence-anomaly terminal.
  * finite hardening: NaN / +inf / -inf are rejected and preserved.

NO model, NO CUDA, NO checkpoint, NO real VAL/GT bytes.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\phase36_final_probability_authority_diagnostic_negative_controls_v1_1.py
"""
from __future__ import annotations

import ast
import csv as _csv
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import types
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts" / "analysis"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

VENV = ROOT / ".venv" / "Scripts" / "python.exe"
AUD = ROOT / "reports" / "audits"
DIAG = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_1.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_1.py"
V14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
MANIFEST = AUD / "phase36_v1_14_runtime_source_integrity_manifest.json"

RESULTS: list = []

# v1.0 family MUST remain byte-for-byte frozen.
V1_0_PRESERVED = {
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
    "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_0.py":
        "148f997b6aed291c093b7d2ecced82a7b4086c229d1da5ef4afa676a6f5cb712",
    "reports/audits/phase36_final_probability_authority_diagnostic_contract_v1_0.json":
        "378afe99342f95f47ff0cc9e06bc509190dc6b86750f5d9499be35fa1c547fe3",
    "reports/audits/phase36_final_probability_authority_diagnostic_source_freeze_v1_0.json":
        "4789b1f7499ff59318bb160757f85f7262d1014a80ba7eb208f98a1ca985d9eb",
    "reports/audits/phase36_final_probability_authority_diagnostic_preflight_v1_0.json":
        "0d47aa167775503aac3baba61052d2bcd2be76149006376fca21694ecea9f3be",
    "reports/audits/phase36_final_probability_authority_diagnostic_negative_controls_v1_0.json":
        "003fe8203004761360401e8843e2a1ba8f2869b7b0391b8a3234ceb6a8aab1b9",
    "reports/audits/phase36_final_probability_authority_diagnostic_eligibility_v1_0.json":
        "a9dd6960b3fdee3fa586bb4935f3808684ffd07e027329fb74b0513cd7ed5242",
    "reports/audits/phase36_final_probability_authority_diagnostic_no_execution_audit_v1_0.json":
        "dfa784fe050c98391dd1a47360960fb8f70063a3b5e33aee6bbf2a8a479e1a4d",
}

# v1.2 / D51 provenance MUST remain frozen.
PROVENANCE_PRESERVED = {
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


def _save(mod, *names):
    return {n: getattr(mod, n) for n in names}


def _restore(mod, saved):
    for n, v in saved.items():
        setattr(mod, n, v)


def main() -> int:
    diag_mod = _load(DIAG, "_diag_fpa_nc11")
    launch_mod = _load(LAUNCHER, "_launch_fpa_nc11")
    FOREIGN = launch_mod.FOREIGN_V1_14_LAUNCH_TOKEN

    START_V1_1 = AUD / "phase36_final_probability_authority_diagnostic_start_v1_1.json"

    # ======================================================================= #
    # HEADLINE: foreign v1.14 token set => launcher refuses before dispatch,
    # no marker; diagnostic main() also refuses (rc 8), no marker.
    # ======================================================================= #
    assert not START_V1_1.exists()

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
          "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_1_FAIL_CLOSED__"
          "FOREIGN_V1_14_LAUNCH_AUTHORITY_PRESENT__NO_ATTEMPT_CONSUMED" in launcher_out)
    check("HEADLINE_no_marker_after_launcher_foreign_refusal", not START_V1_1.exists())

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
    check("HEADLINE_no_marker_after_diagnostic_foreign_refusal", not START_V1_1.exists())
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
            tampered = src_bytes.replace(
                needle, b"feddd33d22ae996b2f7ef60e8242a89f3cebab8c6992406508fec23cb068710c", 1)
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
    # D52 — final-authority pre-consumption gate is mutation-sensitive
    # ======================================================================= #
    fa = launch_mod.check_final_authority_preconsumption()
    check("D52_real_tree_pass", fa["final_authority_preconsumption_pass"] is True, {"reason": fa.get("reason")})
    check("D52_real_tree_sha", fa["final_authority_sha256"] == launch_mod.PHASE27_FINAL_PROB_AUTHORITY_SHA)
    check("D52_real_tree_shape", fa["final_authority_shape"] == [808, 512, 512])
    check("D52_real_tree_dtype", fa["final_authority_dtype"] == "float16")
    check("D52_real_tree_sample_order", fa["final_authority_sample_order_pass"] is True)

    saved_fa = _save(launch_mod, "PHASE27_FINAL_PROB_AUTHORITY_SHA",
                     "PHASE27_FINAL_PROB_AUTHORITY_SHAPE", "PHASE27_FINAL_PROB_AUTHORITY_DTYPE",
                     "VAL_MANIFEST", "VAL_MANIFEST_SHA", "PHASE27_SCORES_CSV", "PHASE27_SCORES_CSV_SHA")
    try:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            # (a) authority missing
            r = launch_mod.check_final_authority_preconsumption(authority_path=tdp / "nope.npy")
            check("D52_authority_missing_detected",
                  r["final_authority_preconsumption_pass"] is False
                  and r["reason"] == "FINAL_AUTHORITY_ABSENT", {"reason": r.get("reason")})
            # (b) authority SHA mutation
            bad = tdp / "bad.npy"
            bad.write_bytes(b"not-an-npy")
            r = launch_mod.check_final_authority_preconsumption(authority_path=bad)
            check("D52_authority_sha_mutation_detected",
                  r["final_authority_preconsumption_pass"] is False
                  and r["reason"] == "FINAL_AUTHORITY_SHA_MISMATCH", {"reason": r.get("reason")})
            # (c) wrong shape
            shp = tdp / "shp.npy"
            np.save(shp, np.zeros((2, 3), dtype=np.float16))
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_SHA = launch_mod.sha(shp)
            r = launch_mod.check_final_authority_preconsumption(authority_path=shp)
            check("D52_wrong_shape_detected",
                  r["final_authority_preconsumption_pass"] is False
                  and r["reason"] == "FINAL_AUTHORITY_SHAPE_MISMATCH", {"reason": r.get("reason")})
            # (d) wrong dtype
            dt = tdp / "dt.npy"
            np.save(dt, np.zeros((2, 3), dtype=np.float32))
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_SHA = launch_mod.sha(dt)
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_SHAPE = (2, 3)
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_DTYPE = "float16"
            r = launch_mod.check_final_authority_preconsumption(authority_path=dt)
            check("D52_wrong_dtype_detected",
                  r["final_authority_preconsumption_pass"] is False
                  and r["reason"] == "FINAL_AUTHORITY_DTYPE_MISMATCH", {"reason": r.get("reason")})
            # restore real pins before the order tests
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_SHA = saved_fa["PHASE27_FINAL_PROB_AUTHORITY_SHA"]
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_SHAPE = saved_fa["PHASE27_FINAL_PROB_AUTHORITY_SHAPE"]
            launch_mod.PHASE27_FINAL_PROB_AUTHORITY_DTYPE = saved_fa["PHASE27_FINAL_PROB_AUTHORITY_DTYPE"]
            # (e) sample-order mismatch via a REORDERED scores CSV (SHA pin patched)
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
            check("D52_sample_order_mismatch_detected_csv_order",
                  r["final_authority_preconsumption_pass"] is False
                  and r["reason"] == "FINAL_AUTHORITY_SAMPLE_ORDER_MISMATCH", {"reason": r.get("reason")})
            launch_mod.PHASE27_SCORES_CSV = saved_fa["PHASE27_SCORES_CSV"]
            launch_mod.PHASE27_SCORES_CSV_SHA = saved_fa["PHASE27_SCORES_CSV_SHA"]
            # (f) sample-order mismatch via fg-pixel row binding
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
            check("D52_sample_order_mismatch_detected_row_binding",
                  r["final_authority_preconsumption_pass"] is False
                  and r["reason"] == "FINAL_AUTHORITY_SAMPLE_ORDER_MISMATCH"
                  and r.get("sample_order_detail") == "FG_PIXEL_ROW_BINDING_MISMATCH",
                  {"reason": r.get("reason"), "detail": r.get("sample_order_detail")})
            launch_mod.PHASE27_SCORES_CSV = saved_fa["PHASE27_SCORES_CSV"]
            launch_mod.PHASE27_SCORES_CSV_SHA = saved_fa["PHASE27_SCORES_CSV_SHA"]
            # (g) reordered manifest caught by the pinned manifest SHA
            real_man_rows = list(_csv.DictReader((ROOT / launch_mod.VAL_MANIFEST).open(encoding="utf-8", newline="")))
            rman = tdp / "val_rev.csv"
            with rman.open("w", encoding="utf-8", newline="") as fh:
                w = _csv.DictWriter(fh, fieldnames=list(real_man_rows[0].keys()))
                w.writeheader()
                w.writerows(list(reversed(real_man_rows)))
            launch_mod.VAL_MANIFEST = str(rman)  # real SHA pin left in place
            r = launch_mod.check_final_authority_preconsumption()
            check("D52_reordered_manifest_detected_by_sha",
                  r["final_authority_preconsumption_pass"] is False
                  and r["reason"] == "VAL_MANIFEST_SHA_MISMATCH", {"reason": r.get("reason")})
            launch_mod.VAL_MANIFEST = saved_fa["VAL_MANIFEST"]
            launch_mod.VAL_MANIFEST_SHA = saved_fa["VAL_MANIFEST_SHA"]
    finally:
        _restore(launch_mod, saved_fa)

    # D52 gate is a pure function: no marker written by any failure
    check("D52_no_marker_from_final_authority_gate", not START_V1_1.exists())

    # ======================================================================= #
    # D53 — GT guard counter propagates to the failure artifact
    # ======================================================================= #
    # (a) single guarded callable => VAL_GT_READ == 1 (the work-order control)
    rs1 = diag_mod._new_runtime_state()
    fake1 = types.SimpleNamespace(_dice=lambda *a, **k: 1.0,
                                  canonical_learned_core=lambda *a, **k: {"ok": True})
    diag_mod._install_gt_guards(fake1, rs1)
    raised1 = 0
    try:
        fake1._dice()
    except SystemExit:
        raised1 += 1
    check("D53_single_callable_raises", raised1 == 1, {"raised": raised1})
    check("D53_single_callable_val_gt_read_1", rs1["VAL_GT_READ"] == 1, {"VAL_GT_READ": rs1["VAL_GT_READ"]})
    check("D53_single_callable_blocked_contains", "_dice" in rs1["blocked_gt_calls"])
    check("D53_non_gt_untouched", fake1.canonical_learned_core() == {"ok": True})

    # (b) all four guarded callables => shared state accumulates; failure artifact mirrors
    rs = diag_mod._new_runtime_state()
    fake = types.SimpleNamespace(
        _load_val_gt=lambda *a, **k: "GT",
        _dice=lambda *a, **k: 1.0,
        _iou=lambda *a, **k: 1.0,
        _hd95=lambda *a, **k: 1.0,
        canonical_learned_core=lambda *a, **k: {"ok": True},
    )
    g = diag_mod._install_gt_guards(fake, rs)
    raised = 0
    for nm in ("_load_val_gt", "_dice", "_iou", "_hd95"):
        try:
            getattr(fake, nm)()
        except SystemExit:
            raised += 1
    check("D53_gt_guards_fail_closed", raised == 4, {"raised": raised})
    check("D53_shared_state_val_gt_read", rs["VAL_GT_READ"] == 4, {"VAL_GT_READ": rs["VAL_GT_READ"]})
    check("D53_shared_state_blocked_calls",
          set(rs["blocked_gt_calls"]) == {"_load_val_gt", "_dice", "_iou", "_hd95"},
          {"blocked": rs["blocked_gt_calls"]})
    check("D53_install_reports_installed",
          set(g["installed"]) == {"_load_val_gt", "_dice", "_iou", "_hd95"}, {"installed": g["installed"]})

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
    check("D53_failure_records_actual_val_gt_read", fj["VAL_GT_READ"] == 4, {"VAL_GT_READ": fj.get("VAL_GT_READ")})
    check("D53_failure_not_hardcoded_zero", fj["VAL_GT_READ"] != 0)
    check("D53_failure_blocked_calls_contains_callable", "_dice" in fj["blocked_gt_calls"])
    check("D53_failure_runtime_state_mirrors", fj["runtime_state"]["VAL_GT_READ"] == 4)

    # ======================================================================= #
    # D54 — computed evidence survives a result-write failure
    # ======================================================================= #
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
        check("D54_result_write_failure_rc3", rc_d54 == 3, {"rc": rc_d54})
        check("D54_failure_artifact_written", fail_p.exists())
        fj2 = json.loads(fail_p.read_text(encoding="utf-8")) if fail_p.exists() else {}
        check("D54_final_authority_computed_true", fj2.get("final_authority_computed") is True)
        check("D54_comparison_preserved", fj2.get("final_authority_comparison") == synthetic_cmp)
        check("D54_classification_preserved",
              fj2.get("classification") == "D51_END_TO_END_FINAL_AUTHORITY_NOT_REPRODUCED")
        check("D54_result_write_attempted_true", fj2.get("result_write_attempted") is True)
        check("D54_result_write_completed_false", fj2.get("result_write_completed") is False)
        check("D54_terminal_classification",
              fj2.get("terminal_classification") == diag_mod.TERMINAL_RESULT_WRITE_FAILED)
        check("D54_no_partial_result_file", not (tdp / "result.json").exists())

    # ======================================================================= #
    # FINITE — NaN / +inf / -inf rejected and preserved
    # ======================================================================= #
    check("FINITE_ok", diag_mod._finite_check(np.array([0.1, 0.5, 0.9], dtype=np.float32)) is True)
    check("FINITE_nan_rejected", diag_mod._finite_check(np.array([0.1, np.nan], dtype=np.float32)) is False)
    check("FINITE_posinf_rejected", diag_mod._finite_check(np.array([np.inf], dtype=np.float32)) is False)
    check("FINITE_neginf_rejected", diag_mod._finite_check(np.array([-np.inf], dtype=np.float32)) is False)
    rs3 = diag_mod._new_runtime_state()
    n_rec = diag_mod._record_nonfinite(rs3, "sX", np.array([np.nan, np.inf, -np.inf, 0.5], dtype=np.float32))
    check("FINITE_record_count", n_rec == 3, {"n": n_rec})
    check("FINITE_record_ids", rs3["nonfinite_samples"] == {"sX": 3})
    check("FINITE_record_flag", rs3["nonfinite_final_probability"] is True)

    # ======================================================================= #
    # REQ13 — launch authority required before marker (runtime rc)
    # ======================================================================= #
    os.environ.pop(diag_mod.ONE_SHOT_ENV, None)
    os.environ.pop(diag_mod.LAUNCH_AUTHORITY_TOKEN, None)
    os.environ.pop(FOREIGN, None)
    rc3 = diag_mod.main(); check("REQ13_no_execute_gate_rc3", rc3 == 3, {"rc": rc3})
    os.environ[diag_mod.ONE_SHOT_ENV] = "1"
    try:
        rc5 = diag_mod.main()
    finally:
        os.environ.pop(diag_mod.ONE_SHOT_ENV, None)
    check("REQ13_no_launch_authority_rc5", rc5 == 5, {"rc": rc5})
    check("REQ13_no_marker_after_refusals", not START_V1_1.exists())

    # ======================================================================= #
    # REQ14/15 — guarded result write, comparison persistence, forbidden reachability
    # ======================================================================= #
    t = _tree(DIAG)
    mainfn = None
    for n in ast.walk(t):
        if isinstance(n, ast.FunctionDef) and n.name == "main":
            mainfn = n
    guarded = False
    for tb in [n for n in ast.walk(mainfn) if isinstance(n, ast.Try)]:
        body = " ".join(ast.get_source_segment(diag_src, s) or "" for s in tb.body)
        handlers = " ".join(ast.get_source_segment(diag_src, h) or "" for h in tb.handlers)
        if "run_diagnostic(" in body and "_write_failure" in handlers:
            guarded = True
    check("REQ14_computation_guarded", guarded)
    check("REQ14_final_comparison_written", '"final_authority_comparison": cmp_,' in diag_src)
    for fb in ("run_image_perturbations", "run_proposal_perturbations", "run_science", "run_smoke"):
        check(f"REQ15_no_reach::{fb}", fb not in diag_src)

    # ======================================================================= #
    # REQ17 — static GT prohibition
    # ======================================================================= #
    for gtc in ("_load_val_gt", "full_field_gt", "_dice", "_iou", "_hd95"):
        check(f"REQ17_gt_static_no_call::{gtc}", not _calls(t, gtc))

    # ======================================================================= #
    # REQ18 — GT contract wording (metadata permitted; content forbidden)
    # ======================================================================= #
    check("REQ18_metadata_access_permitted", "mask_path_metadata_validation_permitted" in diag_src)
    check("REQ18_content_prohibition_declared",
          "no_Image_open_on_mask_path" in diag_src and "_load_val_gt_never_executes" in diag_src)

    # ======================================================================= #
    # REQ16 — v1.0 family + provenance preserved byte-for-byte
    # ======================================================================= #
    for p, exp in V1_0_PRESERVED.items():
        check(f"REQ16_v1_0_preserved::{Path(p).name}", sha(ROOT / p) == exp, {"observed": sha(ROOT / p)})
    for p, exp in PROVENANCE_PRESERVED.items():
        check(f"REQ16_provenance_preserved::{Path(p).name}", sha(ROOT / p) == exp)

    n_ok = sum(1 for r in RESULTS if r["ok"])
    n = len(RESULTS)
    print(json.dumps({"artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_V1_1_NEGATIVE_CONTROL_RESULTS",
                      "n_checks": n, "n_pass": n_ok, "all_pass": n_ok == n,
                      "results": RESULTS}, indent=1))
    print(f"\n=== NEGATIVE CONTROLS v1.1 (final-prob authority): {n_ok}/{n} pass")
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
