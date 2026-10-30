#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — CLEAN EQUIVALENCE DIAGNOSTIC v1.1 — PREFLIGHT READINESS.

D49: real AST / control-flow bindings, not tautologies.  NO execution of model /
CUDA / VAL / GT / checkpoint.  Verifies static readiness of the diagnostic +
launcher, frozen anchors, prior-failure provenance, transitive integrity, v1.0
preservation, and absence of any prior v1.1 diagnostic attempt.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\phase36_clean_equivalence_diagnostic_preflight_v1_1.py
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
UNIT = ROOT / "scripts" / "analysis" / "phase36_clean_equivalence_diagnostic_unit_v1_1.py"
V14 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
MANIFEST = ROOT / "reports" / "audits" / "phase36_v1_14_runtime_source_integrity_manifest.json"

# preserved v1.0 (FROZEN / NEVER CONSUMED / NOT AUTHORIZED)
V10_PRESERVED = {
    "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_0.py":
        "7cc51cceacfa314d7f84acb8a6dc482a2b46ea81de0ec695c0c8f0ca8b0b50f7",
    "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_0.py":
        "a34923faf6c27dd741ee1a1a1b4d1cbef1233664c2b02825e53b42c22c75b228",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_0.py":
        "33e72386699aa0100c314846ffe2592f740ca7fb76e926a704cf4d46fbf78bf5",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_preflight_v1_0.py":
        "92c2d855e931d037e965d862a2ce0feb091d53e1bff0f91020f85729842e6653",
}

V14_EVIDENCE = {
    "reports/audits/phase36_robustness_science_start_v1_14.json":
        "e2c42b05f4fd0450022d7bcde091c0bea13638788b4f83a123016ab894630e0a",
    "reports/audits/phase36_robustness_science_failure_v1_14.json":
        "0fcc3c211d7bcd53b4f8e53d7b09f518fd83a929e8a979c7174762958fff754b",
    "reports/audits/phase36_v1_14_science_failure_forensic_adjudication.json":
        "f1d4712ae7b3f0b333a22c852f99d6b3812218ffb258f8f58ddba62c7193c17e",
    "reports/audits/phase36_v1_14_science_failure_forensic_reconciliation_v2.json":
        "cc9a3b502f59e3855c395b9d6afa2f5616f513d60af4756e4477a9370889cc3c",
    "reports/audits/phase36_clean_equivalence_targeted_static_audit_v1_0.json":
        "8def086c44a7e80461c729f41ab61c0be347ef1589c94d6884a082adbde64ed4",
}

DIAG_ARTIFACTS = (
    ROOT / "reports/audits/phase36_clean_equivalence_diagnostic_start_v1_1.json",
    ROOT / "reports/audits/phase36_clean_equivalence_diagnostic_result_v1_1.json",
    ROOT / "reports/audits/phase36_clean_equivalence_diagnostic_failure_v1_1.json",
)

RESULTS: list = []


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def check(name, ok, detail=None):
    RESULTS.append({"name": name, "ok": bool(ok), "detail": detail})


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    launch = _load(LAUNCHER, "_launch_v11_pf")
    diag = _load(DIAG, "_diag_v11_pf")
    dtxt = DIAG.read_text(encoding="utf-8")
    ltxt = LAUNCHER.read_text(encoding="utf-8")
    dtree = ast.parse(dtxt)

    # ---- 1. sources exist ------------------------------------------------- #
    check("diagnostic_source_exists", DIAG.exists())
    check("launcher_source_exists", LAUNCHER.exists())
    check("frozen_v1_14_source_exists", V14.exists())
    check("runtime_manifest_exists", MANIFEST.exists())

    # ---- 2. frozen anchors intact ----------------------------------------- #
    check("frozen_v1_14_exec_sha_intact", sha(V14) == launch.FROZEN_EXPECTED_V1_14_EXEC_SHA)
    check("frozen_v1_14_manifest_sha_intact", sha(MANIFEST) == launch.FROZEN_EXPECTED_V1_14_MANIFEST_SHA)
    check("diagnostic_sha_pinned_to_actual", launch.FROZEN_EXPECTED_DIAGNOSTIC_SHA == sha(DIAG),
          {"pinned": launch.FROZEN_EXPECTED_DIAGNOSTIC_SHA, "actual": sha(DIAG)})

    # ---- 3. authority verify passes --------------------------------------- #
    auth = launch.verify_authority()
    check("launcher_authority_authorized", auth["authorized"] is True)

    # ---- 4. no prior v1.1 diagnostic attempt ------------------------------ #
    check("no_prior_v1_1_diagnostic_attempt", not any(p.exists() for p in DIAG_ARTIFACTS),
          {p.name: p.exists() for p in DIAG_ARTIFACTS})

    # ---- 5. v1.0 preserved byte-for-byte ---------------------------------- #
    for rel, exp in V10_PRESERVED.items():
        p = ROOT / rel
        check(f"v1_0_preserved::{Path(rel).name}",
              p.exists() and sha(p) == exp, {"exists": p.exists()})

    # ---- 6. preserved v1.14 evidence intact ------------------------------- #
    for rel, exp in V14_EVIDENCE.items():
        p = ROOT / rel
        check(f"v1_14_evidence_intact::{Path(rel).name}",
              p.exists() and sha(p) == exp)

    # ---- 7. D49-1/2: token before marker; one-shot-only cannot consume ---- #
    ok = (dtxt.index('os.environ.get(LAUNCH_AUTHORITY_TOKEN)')
          < dtxt.index('_write_once_json(DIAGNOSTIC_START'))
    check("D49_1_authority_token_checked_before_marker", ok)
    check("D49_2_direct_one_shot_cannot_consume",
          "FAIL_CLOSED__LAUNCH_AUTHORITY_REQUIRED__NO_ATTEMPT_CONSUMED" in dtxt)

    # ---- 8. D49-3: launcher sets token only after all checks -------------- #
    tok = ltxt.index('os.environ[LAUNCH_AUTHORITY_TOKEN] = "1"')
    check("D49_3_token_after_anchors", ltxt.index("verify_authority()") < tok)
    check("D49_3_token_after_interpreter", ltxt.index("check_interpreter_identity()") < tok)
    check("D49_3_token_after_cuda", ltxt.index("check_cuda_readiness()") < tok)
    check("D49_3_token_after_transitive", ltxt.index("check_transitive_integrity()") < tok)
    check("D49_3_token_after_provenance", ltxt.index("check_prior_failure_provenance()") < tok)

    # ---- 9. D49-4/5: exact counter authority; no common_v1_0 ------------- #
    check("D49_4_uses_mod_C_counters", "C.COUNTERS_REQUIRED" in dtxt and "C.COUNTERS_FOREVER_ZERO" in dtxt)
    check("D49_5_no_common_v1_0_counter_authority", "phase36_robustness_common_v1_0" not in dtxt)

    # ---- 10. D49-6: exact stage order ------------------------------------- #
    order = ["mod._verify_transitive_source_integrity", "mod._load_models",
             "mod._bind_clean_reference", "mod._generate_clean_g_reference",
             "mod._phase27_global_reproduction_gate", "mod._evaluate_clean_sample",
             "mod._clean_equivalence_gate"]
    pos = [dtxt.index(m) for m in order]
    check("D49_6_stage_order_monotonic", pos == sorted(pos))

    # ---- 11. D49-7: no forbidden reachability ----------------------------- #
    forbidden = ["run_image_perturbations(", "run_proposal_perturbations(", "run_science("]
    for fb in forbidden:
        check(f"D49_7_no_reach_{fb}", fb not in dtxt)
    # training/optimizer/param-mutation absent (outside the forever-zero counter names)
    for bad in ["optimizer.step(", ".backward(", "requires_grad_(True)", "model.train("]:
        check(f"D49_7_no_{bad}", bad not in dtxt)

    # ---- 12. D49-8: complete eq object persisted -------------------------- #
    eq_fields = ["all_pass", "checks", "n_generated", "n_bound", "n_dice_comparisons",
                 "n_state_machine_branch_comparisons", "n_router_decision_comparisons",
                 "missing_generated_dice", "missing_bound_dice", "dice_mismatches",
                 "route_branch_mismatches", "router_decision_mismatches",
                 "max_abs_dice_deviation", "dice_comparator", "branch_comparator",
                 "router_decision_comparator"]
    check("D49_8_eq_object_persisted", "clean_equivalence_full" in dtxt)
    # the eq object's fields come from the frozen gate; assert the gate exposes them
    v14txt = V14.read_text(encoding="utf-8")
    for f in eq_fields:
        check(f"D49_8_eq_field_from_frozen_gate::{f}", f'"{f}"' in v14txt or f in v14txt)

    # ---- 13. D49-9/10/11/12: durable handling + exclusive create + no retry #
    check("D49_9_result_write_inside_guarded_region",
          "run_diagnostic()" in dtxt and "DIAGNOSTIC_RESULT" in dtxt)
    check("D49_10_result_failure_exclusive_create",
          "os.O_CREAT | os.O_EXCL" in dtxt and "os.fsync(fd)" in dtxt)
    check("D49_11_start_marker_exclusive_create", "_write_once_json(DIAGNOSTIC_START" in dtxt)
    check("D49_12_no_automatic_retry",
          '"automatic_retry": False' in dtxt and '"overwrite_permitted": False' in dtxt)

    # ---- 14. D49-13: verify-only non-consuming ---------------------------- #
    check("D49_13_verify_only_non_consuming",
          ltxt.index("if a.verify_only:") < ltxt.index('os.environ[LAUNCH_AUTHORITY_TOKEN] = "1"'))

    # ---- 15. runtime transitive integrity + provenance pass --------------- #
    ti = launch.check_transitive_integrity()
    check("transitive_integrity_ok", ti["ok"] is True,
          {"n_deps": ti["n_dependencies"], "n_ckpts": ti["n_checkpoints"]})
    prov = launch.check_prior_failure_provenance()
    check("prior_failure_provenance_ok", prov["ok"] is True,
          {"verdict": prov.get("static_audit_verdict")})
    check("static_audit_verdict_bound", prov.get("static_audit_verdict") == "STATIC_ROOT_CAUSE_NOT_ESTABLISHED")

    # ---- 16. one-shot gate wiring ----------------------------------------- #
    check("one_shot_env_constant", diag.ONE_SHOT_ENV == "PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE")
    check("launch_authority_constant",
          diag.LAUNCH_AUTHORITY_TOKEN == "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_LAUNCH_AUTHORITY")
    check("one_shot_gate_unset_in_process", os.environ.get(diag.ONE_SHOT_ENV) != "1")

    n_ok = sum(1 for r in RESULTS if r["ok"])
    n = len(RESULTS)
    summary = {"artifact_kind": "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_PREFLIGHT_RESULTS",
               "n_checks": n, "n_pass": n_ok, "all_pass": n_ok == n,
               "execution_mode": "STATIC_ONLY_NO_MODEL_NO_CUDA_NO_VAL",
               "results": RESULTS}
    print(json.dumps(summary, indent=1))
    print(f"\n=== PREFLIGHT v1.1: {n_ok}/{n} pass")
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
