#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — CLEAN EQUIVALENCE DIAGNOSTIC v1.2 — PREFLIGHT (no model, no CUDA).

Verifies the D50 governance repair is in place, v1.0/v1.1 are preserved
byte-for-byte, frozen anchors are intact, the consumed v1.1 failure is bound, and
the launcher's D50-A/D50-B gates pass.  Non-consuming.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\phase36_clean_equivalence_diagnostic_preflight_v1_2.py
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts" / "analysis"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

VENV = ROOT / ".venv" / "Scripts" / "python.exe"
AUD = ROOT / "reports" / "audits"
DIAG = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_2.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_2.py"
UNIT = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_2.py"
NEGCTRL = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_negative_controls_v1_2.py"
V14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
MANIFEST = AUD / "phase36_v1_14_runtime_source_integrity_manifest.json"

RESULTS: list = []


def sha(p: Path) -> str:
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except FileNotFoundError:
        return "ABSENT"


def check(name, ok, detail=None):
    RESULTS.append({"name": name, "ok": bool(ok), "detail": detail})


def _tree(p: Path):
    return ast.parse(Path(p).read_text(encoding="utf-8"))


def _find_func(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


V14_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

V10 = {
    "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_0.py":
        "7cc51cceacfa314d7f84acb8a6dc482a2b46ea81de0ec695c0c8f0ca8b0b50f7",
    "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_0.py":
        "a34923faf6c27dd741ee1a1a1b4d1cbef1233664c2b02825e53b42c22c75b228",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_0.py":
        "33e72386699aa0100c314846ffe2592f740ca7fb76e926a704cf4d46fbf78bf5",
    "scripts/analysis/phase36_clean_equivalence_diagnostic_preflight_v1_0.py":
        "92c2d855e931d037e965d862a2ce0feb091d53e1bff0f91020f85729842e6653",
}
V11 = {
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


def main() -> int:
    check("diagnostic_source_exists", DIAG.exists())
    check("launcher_source_exists", LAUNCHER.exists())
    check("unit_source_exists", UNIT.exists())
    check("negative_controls_source_exists", NEGCTRL.exists())
    check("frozen_v1_14_source_exists", V14.exists())
    check("runtime_manifest_exists", MANIFEST.exists())

    check("frozen_v1_14_exec_sha_intact", sha(V14) == V14_SHA, {"observed": sha(V14)})
    check("frozen_v1_14_manifest_sha_intact", sha(MANIFEST) == MANIFEST_SHA, {"observed": sha(MANIFEST)})

    # v1.0 / v1.1 preserved byte-for-byte
    for p, exp in V10.items():
        check(f"v1_0_preserved::{Path(p).name}", sha(ROOT / p) == exp, {"observed": sha(ROOT / p)})
    for p, exp in V11.items():
        check(f"v1_1_preserved::{Path(p).name}", sha(ROOT / p) == exp, {"observed": sha(ROOT / p)})

    # v1.2 markers absent
    for m in ["start", "result", "failure"]:
        check(f"v1_2_{m}_marker_absent",
              not (AUD / f"phase36_clean_equivalence_diagnostic_{m}_v1_2.json").exists())
    # v1.1 markers present (consumed)
    check("v1_1_start_present_consumed",
          (AUD / "phase36_clean_equivalence_diagnostic_start_v1_1.json").exists())
    check("v1_1_failure_present_consumed",
          (AUD / "phase36_clean_equivalence_diagnostic_failure_v1_1.json").exists())

    # launcher pin == actual diagnostic SHA
    launch_src = LAUNCHER.read_text(encoding="utf-8")
    check("launcher_pin_matches_actual_diagnostic",
          f'FROZEN_EXPECTED_DIAGNOSTIC_SHA = "{sha(DIAG)}"' in launch_src,
          {"actual": sha(DIAG)})

    # AST: no forbidden call / no foreign token write
    diag_tree = _tree(DIAG)
    launch_tree = _tree(LAUNCHER)

    def _calls(tree, fname):
        out = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                f = n.func
                nm = getattr(f, "id", None) or getattr(f, "attr", None)
                if nm == fname:
                    out.append(n.lineno)
        return out

    check("D50_diagnostic_no_forbidden_gate_call",
          not _calls(diag_tree, "_verify_transitive_source_integrity"))
    check("D50_launcher_no_forbidden_gate_call",
          not _calls(launch_tree, "_verify_transitive_source_integrity"))
    FOREIGN = "PHASE36_V1_14_LAUNCH_AUTHORITY"
    check("D50_diagnostic_no_foreign_token_write",
          f'os.environ["{FOREIGN}"]' not in (DIAG.read_text(encoding="utf-8"))
          and f"os.environ['{FOREIGN}']" not in (DIAG.read_text(encoding="utf-8")))
    check("D50_launcher_no_foreign_token_write",
          f'os.environ["{FOREIGN}"]' not in launch_src
          and f"os.environ['{FOREIGN}']" not in launch_src)
    check("D50_foreign_token_declared_absent_contract",
          f'FOREIGN_V1_14_LAUNCH_TOKEN = "{FOREIGN}"' in launch_src
          and f'FOREIGN_V1_14_LAUNCH_TOKEN = "{FOREIGN}"' in DIAG.read_text(encoding="utf-8"))

    # D50-C: token constants
    check("D50_c_one_shot_env", "PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE" in launch_src)
    check("D50_c_launch_authority_v1_2",
          'LAUNCH_AUTHORITY_TOKEN = "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_LAUNCH_AUTHORITY"' in launch_src)

    # order (D50-C): foreign gate -> provenance -> consumed-v1.1 -> transitive ->
    # verify-only STOP -> token set. Each stage must be reached strictly after the
    # previous one; `token_set` is the LAST write and must follow the verify-only
    # STOP guard (i.e. it is only reachable on the dispatch path).
    def _first_def_lineno(tree, fname):
        for n in ast.walk(tree):
            if isinstance(n, ast.FunctionDef) and n.name == fname:
                return n.lineno
        return -1

    def _first_call_lineno_after(tree, fname, after):
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                f = n.func
                nm = getattr(f, "id", None) or getattr(f, "attr", None)
                if nm == fname and n.lineno > after:
                    return n.lineno
        return -1

    main_def_ln = _first_def_lineno(launch_tree, "main")
    guard_ln = -1
    for n in ast.walk(launch_tree):
        if isinstance(n, ast.If) and ast.get_source_segment(launch_src, n.test) == "a.verify_only":
            guard_ln = n.lineno
            break

    order = [
        ("check_foreign_v1_14_token_absent",
         _first_call_lineno_after(launch_tree, "check_foreign_v1_14_token_absent", main_def_ln)),
        ("check_prior_failure_provenance",
         _first_call_lineno_after(launch_tree, "check_prior_failure_provenance",
                                  _first_call_lineno_after(launch_tree, "check_foreign_v1_14_token_absent", main_def_ln))),
        ("check_consumed_v1_1_failure",
         _first_call_lineno_after(launch_tree, "check_consumed_v1_1_failure",
                                  _first_call_lineno_after(launch_tree, "check_prior_failure_provenance", main_def_ln))),
        ("check_transitive_integrity",
         _first_call_lineno_after(launch_tree, "check_transitive_integrity",
                                  _first_call_lineno_after(launch_tree, "check_consumed_v1_1_failure", main_def_ln))),
        ("verify_only_guard", guard_ln),
        ("token_set", -1),  # replaced below by the AST-located token write
    ]
    # locate the single token write by line via the AST Assign node
    tok_ln = -1
    for n in ast.walk(launch_tree):
        if isinstance(n, ast.Assign):
            tgt = n.targets[0] if n.targets else None
            if (isinstance(tgt, ast.Subscript)
                    and ast.get_source_segment(launch_src, n.value or n) is not None
                    and ast.get_source_segment(launch_src, tgt.value) == "os.environ"
                    and ast.get_source_segment(launch_src, tgt.slice) == "LAUNCH_AUTHORITY_TOKEN"):
                tok_ln = n.lineno
    order[-1] = ("token_set", tok_ln)
    positions = [p for _, p in order]
    check("D50_launcher_stage_order_monotonic",
          all(p != -1 for p in positions) and positions == sorted(positions),
          {k: v for k, v in order})

    # launcher: no torch.load call
    tl = []
    for n in ast.walk(launch_tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "load":
            seg = ast.get_source_segment(launch_src, n.func) or ""
            if "torch" in seg:
                tl.append(n.lineno)
    check("D50_launcher_no_torch_load", not tl, {"lines": tl})

    # runtime: unit + launcher verify-only
    unit_out = subprocess.run([str(VENV), str(UNIT)], capture_output=True, text=True)
    ue = unit_out.stdout.rfind("}")
    depth = 0; start = -1
    for i in range(ue, -1, -1):
        c = unit_out.stdout[i]
        if c == "}": depth += 1
        elif c == "{":
            depth -= 1
            if depth == 0:
                start = i; break
    try:
        uj = json.loads(unit_out.stdout[start:ue + 1])
    except Exception:
        uj = {}
    check("unit_all_pass", uj.get("all_pass") is True,
          {"n_pass": uj.get("n_pass"), "n_checks": uj.get("n_checks")})

    vo = subprocess.run([str(VENV), str(LAUNCHER), "--verify-only"], capture_output=True, text=True)
    try:
        vj = json.loads(vo.stdout[vo.stdout.index("{"):vo.stdout.rindex("}") + 1])
    except Exception:
        vj = {}
    check("launcher_verify_only_ok", vo.returncode == 0, {"rc": vo.returncode})
    check("launcher_verify_only_authorized", vj.get("authorized") is True)
    check("launcher_verify_only_foreign_gate_pass", vj.get("foreign_v1_14_token_absent_pass") is True)
    check("launcher_verify_only_consumed_v1_1_pass", vj.get("consumed_v1_1_failure_binding_pass") is True)
    check("launcher_verify_only_authority_exact_match",
          vj.get("source_manifest_transitive_authority_exact_match") is True)
    check("launcher_verify_only_14_4",
          vj.get("n_dependencies_verified") == 14 and vj.get("n_checkpoints_verified") == 4)
    check("launcher_verify_only_dispatch_suppressed",
          str(vj.get("terminal", "")).endswith("DISPATCH_SUPPRESSED_BY_VERIFY_ONLY"))
    # verify-only did not consume
    for m in ["start", "result", "failure"]:
        check(f"verify_only_non_consuming::{m}",
              not (AUD / f"phase36_clean_equivalence_diagnostic_{m}_v1_2.json").exists())

    # one-shot env not set in this process
    check("one_shot_gate_unset_in_process", os.environ.get("PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE") != "1")
    check("foreign_token_unset_in_process", os.environ.get(FOREIGN) != "1")

    n_ok = sum(1 for r in RESULTS if r["ok"])
    n = len(RESULTS)
    print(json.dumps({"artifact_kind": "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_2_PREFLIGHT_RESULTS",
                      "n_checks": n, "n_pass": n_ok, "all_pass": n_ok == n,
                      "results": RESULTS}, indent=1))
    print(f"\n=== PREFLIGHT v1.2: {n_ok}/{n} pass")
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
