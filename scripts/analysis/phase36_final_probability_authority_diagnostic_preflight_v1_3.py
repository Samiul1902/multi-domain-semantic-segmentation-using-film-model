#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.3 — PREFLIGHT (no model, no CUDA).

Static/integration preflight for the v1.3 family (D61 canonical ACCEPT-fusion repair):

  * source presence + run of the v1.3 unit suite (must be ALL PASS);
  * v1.0 / v1.1 / v1.2 family preservation pins intact;
  * D56 attribute-access contract retained in the v1.3 diagnostic;
  * D61 repair contract: the v1.3 diagnostic calls the canonical ``fuse_full_field``
    and does NOT call ``_fuse_global_with_regional`` anywhere;
  * frozen v1.14 source/manifest anchors intact;
  * the three v1.3 markers ABSENT (no attempt consumed);
  * launch-authority ordering: the v1.3 token is written ONLY after the verify STOP;
  * forbidden reach: NO foreign v1.14 token, NO v1.15, NO Phase37, NO TEST/HOLDOUT;
  * GT-content prohibition: no GT-content callable CALL, mask_path metadata permitted.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\phase36_final_probability_authority_diagnostic_preflight_v1_3.py
"""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts" / "analysis"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

VENV = ROOT / ".venv" / "Scripts" / "python.exe"
AUD = ROOT / "reports" / "audits"

DIAG = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_3.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_3.py"
UNIT = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_3.py"
NEGCTRL = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_3.py"
V14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json"

RESULTS: list = []

V1_0_PINS = {
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
}
V1_1_PINS = {
    "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_1.py":
        "b9f6a449445d8ac5edd1dafe30e2f0b5005d487be314011bd2ff9162db770672",
    "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_1.py":
        "4c9737362fcf01f0ef8ef629f489cdff07c72e63b46f34e4ea508b7ba0df83ae",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_1.py":
        "0358ed115dcedea612aae1b7f0311ea08b97ba212b893a10c51ddae606fbabea",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_1.py":
        "7ba8899b25fbddbcebd42971eedd1bca4b2ca8d06d33629cec7a286e01227925",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_1.py":
        "ef7a7d8c5b7d9699fa375b2bcfccc3c482ac9e4d1b4ce9a1c3807142100a6950",
}
V1_2_PINS = {
    "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_2.py":
        "981f772fd42e35ac8e3acde17344e9bcd3fb48c39aba191200a0d811f76f29f9",
    "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_2.py":
        "de916786f8237d6f04a4deebde4186a5120164bce073ffa1d0343cf6e265aaee",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_2.py":
        "9f1e6527521984b6edbc9fb82f9818c39969baf458800fba9594af36bfbcdce6",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_2.py":
        "89e70d203649cc80f38c8eddba7cae502feb2d02c726474cad5a4daba4abc883",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_2.py":
        "f4128b736e90b80e4565259eef4df45e7fda1aaa541e7f5d5a466adf361fe34a",
}
V14_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"
GT_CALLABLES = ("_load_val_gt", "full_field_gt", "_dice", "_iou", "_hd95")


def sha(p: Path) -> str:
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except FileNotFoundError:
        return "ABSENT"


def check(name, ok, detail=None):
    RESULTS.append({"name": name, "ok": bool(ok), "detail": detail})


def _tree(p: Path):
    return ast.parse(Path(p).read_text(encoding="utf-8"))


def _call_names(tree):
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            nm = getattr(f, "id", None) or getattr(f, "attr", None)
            if nm:
                out.append(nm)
    return out


def _call_linenos(tree, fname):
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            nm = getattr(f, "id", None) or getattr(f, "attr", None)
            if nm == fname:
                out.append(n.lineno)
    return out


def _find_func(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


def main() -> int:
    check("diagnostic_source_exists", DIAG.exists())
    check("launcher_source_exists", LAUNCHER.exists())
    check("unit_source_exists", UNIT.exists())
    check("negative_controls_source_exists", NEGCTRL.exists())

    # ---- frozen anchors ---------------------------------------------------- #
    check("frozen_v1_14_source_preserved", sha(V14) == V14_SHA, {"observed": sha(V14)})
    check("frozen_v1_14_manifest_preserved", sha(MANIFEST) == MANIFEST_SHA, {"observed": sha(MANIFEST)})

    # ---- family preservation ----------------------------------------------- #
    for rel, exp in V1_0_PINS.items():
        check(f"v1_0_preserved::{rel.split('/')[-1]}", sha(ROOT / rel) == exp, {"observed": sha(ROOT / rel)})
    for rel, exp in V1_1_PINS.items():
        check(f"v1_1_preserved::{rel.split('/')[-1]}", sha(ROOT / rel) == exp, {"observed": sha(ROOT / rel)})
    for rel, exp in V1_2_PINS.items():
        check(f"v1_2_preserved::{rel.split('/')[-1]}", sha(ROOT / rel) == exp, {"observed": sha(ROOT / rel)})

    # ---- diagnostic source contract ---------------------------------------- #
    diag_src = DIAG.read_text(encoding="utf-8")
    diag_tree = _tree(DIAG)
    calls = _call_names(diag_tree)

    # D56 retained: no _FROZEN_MOD[...] subscript; attribute access used.
    sub_sites = []
    for n in ast.walk(diag_tree):
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) \
                and n.value.id == "_FROZEN_MOD":
            sub_sites.append(n.lineno)
    check("d56_no_frozen_mod_subscript", not sub_sites, {"sites": sub_sites})
    check("d56_load_clean_image_tensor_attribute_access",
          "mod._load_clean_image_tensor" in diag_src, None)

    # D61 repair contract.
    accept_calls = None
    fn = _find_func(diag_tree, "_repaired_canonical_learned_core")
    if fn is not None:
        for n in ast.walk(fn):
            if isinstance(n, ast.If) and "accept_prob" in ast.unparse(n.test) \
                    and "s_omega_accept_threshold" in ast.unparse(n.test):
                accept_calls = _call_names(n)
    check("d61_repaired_core_present", fn is not None, None)
    check("d61_accept_calls_canonical_fuse_full_field",
          bool(accept_calls and "fuse_full_field" in accept_calls), {"accept_calls": accept_calls})
    check("d61_accept_does_not_call_model_fusion",
          bool(accept_calls is not None and "_fuse_global_with_regional" not in accept_calls),
          {"accept_calls": accept_calls})
    # The old model fusion must be ABSENT as a CALL from the WHOLE diagnostic.
    # NOTE: the literal text "_fuse_global_with_regional" is legitimately present
    # as the D61 provenance constant (D61_OLD_ACCEPT_CALL) and in the repair
    # comment — so we must assert NO actual Call node targets it, not merely
    # that the substring is absent.
    old_fusion_call_sites = _call_linenos(diag_tree, "_fuse_global_with_regional")
    check("d61_old_model_fusion_absent_everywhere",
          not old_fusion_call_sites, {"call_linenos": old_fusion_call_sites})
    # The repair uses the SAME geom object (no re-derivation): the call args.
    fuse_args = None
    for n in ast.walk(fn) if fn is not None else []:
        if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "fuse_full_field":
            fuse_args = [ast.unparse(a) for a in n.args]
    check("d61_fuse_uses_p_global_refined_geom", fuse_args == ["p_global", "refined", "geom"],
          {"args": fuse_args})
    check("d61_repaired_core_aliases_frozen_module", "mod = _FROZEN_MOD" in diag_src, None)
    # No torch interpolation inside the repaired core (canonical uses PIL BILINEAR).
    core_src = ast.get_source_segment(diag_src, fn) if fn is not None else ""
    check("d61_no_torch_interpolate_in_repaired_core",
          "interpolate" not in core_src, None)

    # GT-content prohibition: no GT callable CALL.
    gt_calls = [c for c in calls if c in GT_CALLABLES]
    check("gt_no_content_callable_call", not gt_calls, {"gt_calls": gt_calls})

    # No perturbation call.
    pert = [c for c in calls if "perturb" in c.lower()]
    check("no_perturbation_call", not pert, {"perturb_hits": pert})

    # Token identity: v1.3 token only (no reuse of v1.1/v1.2).
    check("v1_3_token_present", "PHASE36_FINAL_PROB_AUTHORITY_V1_3_LAUNCH_AUTHORITY" in diag_src, None)
    check("no_v1_2_token_reuse", "PHASE36_FINAL_PROB_AUTHORITY_V1_2_LAUNCH_AUTHORITY" not in diag_src, None)
    check("no_v1_1_token_reuse", "PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY" not in diag_src, None)
    check("foreign_v1_14_token_forbidden", "PHASE36_V1_14_LAUNCH_AUTHORITY" in diag_src, None)

    # ---- launcher contract -------------------------------------------------- #
    launch_src = LAUNCHER.read_text(encoding="utf-8")
    launch_tree = _tree(LAUNCHER)
    check("launcher_pins_frozen_v1_2_launcher_sha",
          "de916786f8237d6f04a4deebde4186a5120164bce073ffa1d0343cf6e265aaee" in launch_src, None)
    check("launcher_has_d61_anchor_gate", "d61_has_fuse_full_field_call" in launch_src, None)
    check("launcher_has_v1_2_consumed_gate", "check_v1_2_consumed_state" in launch_src, None)
    check("launcher_v1_3_token", "PHASE36_FINAL_PROB_AUTHORITY_V1_3_LAUNCH_AUTHORITY" in launch_src, None)
    # Token write ordering: the token-assignment lineno must come AFTER the verify-only STOP.
    # The launcher writes ``os.environ[LAUNCH_AUTHORITY_TOKEN] = "1"`` where the
    # subscript slice is a NAME (the module constant), not a string literal — so we
    # accept either the literal text or the constant's identifier.
    _TOK_NAMES = {"PHASE36_FINAL_PROB_AUTHORITY_V1_3_LAUNCH_AUTHORITY", "LAUNCH_AUTHORITY_TOKEN"}
    token_linenos = []
    for n in ast.walk(launch_tree):
        if not isinstance(n, ast.Assign):
            continue
        for tgt in n.targets:
            if not isinstance(tgt, ast.Subscript):
                continue
            if ast.unparse(tgt.value) != "os.environ":
                continue
            sl = tgt.slice
            key = ast.unparse(sl).strip().strip("'\"")
            if key in _TOK_NAMES:
                token_linenos.append(n.lineno)
    verify_lineno = -1
    for n in ast.walk(launch_tree):
        if isinstance(n, ast.If) and "a.verify_only" in ast.unparse(n.test):
            verify_lineno = n.lineno
    check("launcher_token_after_verify_only",
          bool(token_linenos and verify_lineno > 0 and min(token_linenos) > verify_lineno),
          {"token_linenos": token_linenos, "verify_lineno": verify_lineno})

    # Forbidden reach: no TEST/HOLDOUT access in either source.
    for label, src in (("diagnostic", diag_src), ("launcher", launch_src)):
        check(f"no_test_or_holdout_read_in_{label}",
              not any(tok in src for tok in ("test.csv", "holdout.csv", "ROUTER_HOLDOUT_PATH")),
              None)

    # ---- markers absent ----------------------------------------------------- #
    for mk in ("start_v1_3", "result_v1_3", "failure_v1_3"):
        cand = list(AUD.glob(f"phase36_final_probability_authority_diagnostic_{mk}.json"))
        check(f"v1_3_marker_absent::{mk}", len(cand) == 0, {"found": [str(c) for c in cand]})

    # ---- run the unit suite (must be ALL PASS) ------------------------------- #
    r = subprocess.run([str(VENV), str(UNIT)], capture_output=True, text=True)
    uj = {}
    try:
        end = r.stdout.rfind("}")
        start = r.stdout.rfind("{", 0, end)
        uj = json.loads(r.stdout[start:end + 1])
    except Exception:  # noqa: BLE001
        pass
    check("unit_all_pass", uj.get("all_pass") is True,
          {"n_pass": uj.get("n_pass"), "n_checks": uj.get("n_checks"), "rc": r.returncode})

    n = len(RESULTS)
    n_ok = sum(1 for x in RESULTS if x["ok"])
    fails = [x for x in RESULTS if not x["ok"]]
    print(json.dumps({"suite": "preflight_v1_3", "n_checks": n, "n_pass": n_ok,
                      "all_pass": n_ok == n, "failures": fails}, indent=1))
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
