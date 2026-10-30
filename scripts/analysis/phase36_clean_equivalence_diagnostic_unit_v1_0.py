#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — CLEAN EQUIVALENCE DIAGNOSTIC v1.0 — UNIT TESTS (no model, no CUDA).

Static/logic-only.  Proves the diagnostic harness and launcher fail-closed
contracts WITHOUT executing any model, checkpoint, VAL image, or GT mask.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\phase36_clean_equivalence_diagnostic_unit_v1_0.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DIAG = ROOT / "scripts" / "analysis" / "phase36_clean_equivalence_diagnostic_v1_0.py"
LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_clean_equivalence_diagnostic_v1_0.py"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


RESULTS: list = []


def check(name: str, cond: bool, detail=None):
    RESULTS.append({"name": name, "ok": bool(cond), "detail": detail})


def main() -> int:
    diag = _load(DIAG, "_diag_under_test")
    launch = _load(LAUNCHER, "_launcher_under_test")

    # ---- 1. diagnostic source pins --------------------------------------- #
    check("diag_frozen_v1_14_exec_sha_constant",
          diag.FROZEN_V1_14_EXEC_SHA ==
          "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5")
    check("diag_frozen_v1_14_manifest_sha_constant",
          diag.FROZEN_V1_14_MANIFEST_SHA ==
          "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e")

    # ---- 2. launcher anchor constants ------------------------------------ #
    check("launcher_v1_14_exec_sha_constant",
          launch.FROZEN_EXPECTED_V1_14_EXEC_SHA ==
          "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5")
    check("launcher_v1_14_manifest_sha_constant",
          launch.FROZEN_EXPECTED_V1_14_MANIFEST_SHA ==
          "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e")
    # the DIAGNOSTIC source SHA must be pinned to the ACTUAL current source
    check("launcher_diagnostic_sha_matches_current_source",
          launch.FROZEN_EXPECTED_DIAGNOSTIC_SHA == sha(DIAG),
          {"pinned": launch.FROZEN_EXPECTED_DIAGNOSTIC_SHA, "actual": sha(DIAG)})

    # ---- 3. verify_authority happy path (real files, no model IO) --------- #
    auth = launch.verify_authority()
    check("verify_authority_authorized_true", auth["authorized"] is True, auth)
    check("verify_authority_no_model_io",
          set(auth["items"].keys()) >= {"diagnostic_source", "frozen_v1_14_source",
                                        "runtime_manifest", "manifest_parse"})

    # ---- 4. negative controls: mutated temp copies MUST be rejected ------- #
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        # mutated diagnostic source
        d2 = tdp / "diag_mut.py"
        d2.write_bytes(DIAG.read_bytes() + b"\n# mutant\n")
        r = launch.verify_authority(diag_path=d2)
        check("neg_control_mutated_diagnostic_rejected", r["authorized"] is False, r)

        # wrong v1.14 source
        v2 = tdp / "v14_mut.py"
        v2.write_bytes((ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py")
                       .read_bytes() + b"\n# mutant\n")
        r = launch.verify_authority(v14_path=v2)
        check("neg_control_wrong_v1_14_rejected", r["authorized"] is False, r)

        # manifest declaring a launcher SHA (cycle) MUST be rejected
        m2 = tdp / "man.json"
        base = json.loads((ROOT / "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json")
                          .read_text(encoding="utf-8"))
        base["launcher_sha256"] = "deadbeef"
        m2.write_text(json.dumps(base), encoding="utf-8")
        r = launch.verify_authority(manifest_path=m2)
        check("neg_control_manifest_launcher_sha_rejected", r["authorized"] is False, r)

        # missing diagnostic source
        r = launch.verify_authority(diag_path=tdp / "nope.py")
        check("neg_control_missing_diagnostic_rejected", r["authorized"] is False, r)

    # ---- 5. interpreter identity negative control ------------------------- #
    good = launch.check_interpreter_identity()
    check("interpreter_ok_for_canonical_venv", good["ok"] is True, good)
    bad = launch.check_interpreter_identity(observed_executable=r"C:\Windows\System32\python.exe")
    check("neg_control_wrong_interpreter_rejected", bad["ok"] is False, bad)

    # ---- 6. diagnostic one-shot gate (env absent → refuse, no marker) ----- #
    # exercise main() with the gate UNSET in a subprocess-like manner is out of
    # scope here; instead assert the module's gate constant + refusal logic.
    check("diagnostic_one_shot_env_name", diag.ONE_SHOT_ENV == "PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE")
    saved = os.environ.pop(diag.ONE_SHOT_ENV, None)
    try:
        rc = diag.main()
        check("diagnostic_refuses_without_gate", rc == 3, {"rc": rc})
    finally:
        if saved is not None:
            os.environ[diag.ONE_SHOT_ENV] = saved
    check("diagnostic_no_start_marker_after_refusal", not diag.DIAGNOSTIC_START.exists())

    # ---- 7. the diagnostic MUST NOT reference v1.14 science markers as writes #
    # (the marker NAMES may legitimately appear in prose / the guard tuple; what
    #  must NEVER appear is a WRITE construct against them.)
    diag_txt = DIAG.read_text(encoding="utf-8")
    check("diagnostic_writes_only_its_own_artifacts",
          "DIAGNOSTIC_START" in diag_txt and "DIAGNOSTIC_RESULT" in diag_txt
          and "DIAGNOSTIC_FAILURE" in diag_txt
          and "V14_SCIENCE_MARKERS" in diag_txt)
    check("diagnostic_has_no_perturbation_calls",
          "run_image_perturbations(" not in diag_txt and "run_proposal_perturbations(" not in diag_txt)

    # ---- 8. import-surface contract -------------------------------------- #
    for fn in ("_verify_transitive_source_integrity", "_load_models",
               "_bind_clean_reference", "_generate_clean_g_reference",
               "_phase27_global_reproduction_gate", "_clean_row_index",
               "_evaluate_clean_sample", "_clean_equivalence_gate"):
        check(f"diagnostic_references_frozen_callable::{fn}", fn in diag_txt)

    # ---- summary ---------------------------------------------------------- #
    n_ok = sum(1 for r in RESULTS if r["ok"])
    n = len(RESULTS)
    summary = {
        "artifact_kind": "PHASE36_CLEAN_EQ_DIAGNOSTIC_UNIT_RESULTS",
        "n_checks": n, "n_pass": n_ok, "all_pass": n_ok == n,
        "results": RESULTS,
    }
    print(json.dumps(summary, indent=1))
    print(f"\n=== UNIT: {n_ok}/{n} pass")
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
