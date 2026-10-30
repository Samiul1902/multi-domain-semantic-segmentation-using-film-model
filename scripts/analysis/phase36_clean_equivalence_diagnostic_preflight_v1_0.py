#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — CLEAN EQUIVALENCE DIAGNOSTIC v1.0 — PREFLIGHT READINESS.

NO EXECUTION of model / CUDA / VAL / GT / checkpoint.  Verifies static readiness
of the diagnostic + launcher: source hashes, frozen anchors, preserved v1.14
evidence, one-shot gate wiring, absence of any prior diagnostic attempt, and
that the frozen v1.14 science evidence is byte-unchanged.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\phase36_clean_equivalence_diagnostic_preflight_v1_0.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DIAG = ROOT / "scripts" / "analysis" / "phase36_clean_equivalence_diagnostic_v1_0.py"
LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_clean_equivalence_diagnostic_v1_0.py"
V14 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
MANIFEST = ROOT / "reports" / "audits" / "phase36_v1_14_runtime_source_integrity_manifest.json"

# preserved v1.14 evidence that MUST remain byte-identical
V14_EVIDENCE = {
    "reports/audits/phase36_robustness_science_start_v1_14.json":
        "e2c42b05f4fd0450022d7bcde091c0bea13638788b4f83a123016ab894630e0a",
    "reports/audits/phase36_robustness_science_failure_v1_14.json":
        "0fcc3c211d7bcd53b4f8e53d7b09f518fd83a929e8a979c7174762958fff754b",
    "reports/audits/phase36_v1_14_science_release_attestation.json":
        "1045123ad03f953aca5da530c1de303b4db32c4412c5ea92749f11d6f1bb5682",
    "reports/audits/phase36_v1_14_science_failure_forensic_adjudication.json":
        "f1d4712ae7b3f0b333a22c852f99d6b3812218ffb258f8f58ddba62c7193c17e",
    "reports/audits/phase36_v1_14_science_failure_forensic_reconciliation_v2.json":
        "cc9a3b502f59e3855c395b9d6afa2f5616f513d60af4756e4477a9370889cc3c",
}

DIAG_ARTIFACTS = (
    ROOT / "reports" / "audits" / "phase36_clean_equivalence_diagnostic_start_v1_0.json",
    ROOT / "reports" / "audits" / "phase36_clean_equivalence_diagnostic_result_v1_0.json",
    ROOT / "reports" / "audits" / "phase36_clean_equivalence_diagnostic_failure_v1_0.json",
)

RESULTS: list = []


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check(name, ok, detail=None):
    RESULTS.append({"name": name, "ok": bool(ok), "detail": detail})


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    launch = _load(LAUNCHER, "_launch_pf")
    diag = _load(DIAG, "_diag_pf")

    # ---- 1. sources exist and hashes known -------------------------------- #
    check("diagnostic_source_exists", DIAG.exists())
    check("launcher_source_exists", LAUNCHER.exists())
    check("frozen_v1_14_source_exists", V14.exists())
    check("runtime_manifest_exists", MANIFEST.exists())

    # ---- 2. frozen v1.14 anchors intact ----------------------------------- #
    check("frozen_v1_14_exec_sha_intact", sha(V14) == launch.FROZEN_EXPECTED_V1_14_EXEC_SHA,
          {"observed": sha(V14)})
    check("frozen_v1_14_manifest_sha_intact",
          sha(MANIFEST) == launch.FROZEN_EXPECTED_V1_14_MANIFEST_SHA,
          {"observed": sha(MANIFEST)})
    check("diagnostic_sha_pinned_to_actual",
          launch.FROZEN_EXPECTED_DIAGNOSTIC_SHA == sha(DIAG),
          {"pinned": launch.FROZEN_EXPECTED_DIAGNOSTIC_SHA, "actual": sha(DIAG)})

    # ---- 3. authority verify passes (no model IO) ------------------------- #
    auth = launch.verify_authority()
    check("launcher_authority_authorized", auth["authorized"] is True, auth)

    # ---- 4. no prior diagnostic attempt ----------------------------------- #
    check("no_prior_diagnostic_attempt", not any(p.exists() for p in DIAG_ARTIFACTS),
          {p.name: p.exists() for p in DIAG_ARTIFACTS})

    # ---- 5. preserved v1.14 evidence byte-unchanged ----------------------- #
    for rel, exp in V14_EVIDENCE.items():
        p = ROOT / rel
        check(f"v1_14_evidence_intact::{Path(rel).name}",
              p.exists() and sha(p) == exp,
              {"exists": p.exists(), "observed": (sha(p) if p.exists() else None)})

    # ---- 6. one-shot gate wiring ------------------------------------------ #
    check("one_shot_env_constant", diag.ONE_SHOT_ENV == "PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE")
    check("one_shot_gate_unset_in_process", os.environ.get(diag.ONE_SHOT_ENV) != "1",
          {"value": os.environ.get(diag.ONE_SHOT_ENV)})

    # ---- 7. diagnostic references only frozen callables ------------------- #
    dtxt = DIAG.read_text(encoding="utf-8")
    for fn in ("_verify_transitive_source_integrity", "_load_models", "_bind_clean_reference",
               "_generate_clean_g_reference", "_phase27_global_reproduction_gate",
               "_clean_row_index", "_evaluate_clean_sample", "_clean_equivalence_gate"):
        check(f"diag_imports_{fn}", fn in dtxt)
    check("diag_does_not_reimplement_dice", "def _dice(" not in dtxt)
    check("diag_does_not_reimplement_gate", "def _clean_equivalence_gate(" not in dtxt)

    # ---- 8. launcher is non-dispatching under --verify-only (static proof)  #
    ltxt = LAUNCHER.read_text(encoding="utf-8")
    check("launcher_has_verify_only", "--verify-only" in ltxt)
    check("launcher_no_science_mode", '"--mode"' not in ltxt)
    check("launcher_sets_token_only_after_checks",
          ltxt.index("LAUNCH_AUTHORITY_TOKEN] = \"1\"") > ltxt.index("cuda_readiness"))

    n_ok = sum(1 for r in RESULTS if r["ok"])
    n = len(RESULTS)
    summary = {
        "artifact_kind": "PHASE36_CLEAN_EQ_DIAGNOSTIC_PREFLIGHT_RESULTS",
        "n_checks": n, "n_pass": n_ok, "all_pass": n_ok == n,
        "execution_mode": "STATIC_ONLY_NO_MODEL_NO_CUDA_NO_VAL",
        "results": RESULTS,
    }
    print(json.dumps(summary, indent=1))
    print(f"\n=== PREFLIGHT: {n_ok}/{n} pass")
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
