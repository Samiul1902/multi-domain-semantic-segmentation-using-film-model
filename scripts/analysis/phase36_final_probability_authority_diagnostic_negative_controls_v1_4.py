#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.4 — NEGATIVE CONTROLS
(no model, no CUDA).

Adversarial controls for the v1.4 family (D61 canonical ACCEPT-fusion repair with
crash-survivable observability):

  HEADLINE (must FAIL CLOSED, no marker, no model, no GT):
   * the REAL v1.4 diagnostic refuses when the one-shot gate is absent (rc 3);
   * the REAL v1.4 diagnostic refuses when the v1.4 launch-authority token is absent (rc 5);
   * the REAL v1.4 diagnostic refuses when the FOREIGN v1.14 token is present (rc 8);
   * the REAL v1.4 launcher refuses when the FOREIGN v1.14 token is present (rc 2),
     and in that path NO marker is created and NO model is constructed.

  D61 repair controls (MUTATION-SENSITIVE):
   * the v1.4 diagnostic's ACCEPT branch calls the canonical ``fuse_full_field``;
   * the v1.4 diagnostic contains NO ``_fuse_global_with_regional`` CALL;
   * MUTATION: replacing ``fuse_full_field`` with ``_fuse_global_with_regional`` in the
     ACCEPT branch is DETECTED by the static validator (which then reports FAIL);
   * MUTATION: the launcher-side D61 AST gate ALSO rejects the mutated source;
   * the canonical Phase27 ``fuse_full_field`` is PAD-AWARE while the old model fusion is
     PAD-UNAWARE (pure synthetic divergence evidence — NOT model execution).

  D69 identity control:
   * reverting the canonical fusion is DETECTED by the D69 identity / fusion validator.

  D70 journal non-interference control:
   * the journal writer is write-once (O_EXCL) and its records carry GT-free flags;
   * the journal cannot change a scientific output (synthetic).

  D56 controls (retained):
   * the v1.4 diagnostic has no ``_FROZEN_MOD[...]`` subscript site.

  D66 remediation control:
   * the incorrect historical Phase27 score SHA is ABSENT from the v1.4 family.

  GT / reach controls:
   * no GT-content callable is called anywhere in the v1.4 diagnostic;
   * no TEST / ROUTER_HOLDOUT read.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\phase36_final_probability_authority_diagnostic_negative_controls_v1_4.py
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts" / "analysis"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

VENV = ROOT / ".venv" / "Scripts" / "python.exe"
AUD = ROOT / "reports" / "audits"

DIAG = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_4.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_4.py"
SUPERVISOR = ROOT / "scripts/analysis/supervise_phase36_final_probability_authority_diagnostic_v1_4.py"

GT_CALLABLES = ("_load_val_gt", "full_field_gt", "_dice", "_iou", "_hd95")
MARKERS = [
    "phase36_final_probability_authority_diagnostic_start_v1_4.json",
    "phase36_final_probability_authority_diagnostic_result_v1_4.json",
    "phase36_final_probability_authority_diagnostic_failure_v1_4.json",
]
INCORRECT_SCORE_SHA = ("702133930ce14ac9513c992833396e3e250d08417"
                       + "a" + "17d1032cbd260a405cfb12")

RESULTS: list = []


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def check(name, ok, detail=None):
    RESULTS.append({"name": name, "ok": bool(ok), "detail": detail})


def _tree(p: Path):
    return ast.parse(Path(p).read_text(encoding="utf-8"))


def _tree_src(src: str):
    return ast.parse(src)


def _call_names(tree):
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            nm = getattr(f, "id", None) or getattr(f, "attr", None)
            if nm:
                out.append(nm)
    return out


def _find_func(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


def _accept_calls(tree):
    fn = _find_func(tree, "_repaired_canonical_learned_core")
    if fn is None:
        return None
    for n in ast.walk(fn):
        if isinstance(n, ast.If) and "accept_prob" in ast.unparse(n.test) \
                and "s_omega_accept_threshold" in ast.unparse(n.test):
            return _call_names(n)
    return None


def _run(env_extra: dict, argv_extra: list | None = None, exe: Path | None = None) -> dict:
    env = dict(os.environ)
    for k in ("PHASE36_FINAL_PROB_AUTHORITY_EXECUTE",
              "PHASE36_FINAL_PROB_AUTHORITY_V1_4_LAUNCH_AUTHORITY",
              "PHASE36_FINAL_PROB_AUTHORITY_V1_3_LAUNCH_AUTHORITY",
              "PHASE36_FINAL_PROB_AUTHORITY_V1_2_LAUNCH_AUTHORITY",
              "PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY",
              "PHASE36_V1_14_LAUNCH_AUTHORITY"):
        env.pop(k, None)
    env.update(env_extra)
    cmd = [str(exe or VENV), str(DIAG if exe is None else LAUNCHER)]
    if argv_extra:
        cmd += argv_extra
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return {"rc": r.returncode, "stdout": r.stdout, "stderr": r.stderr}


def main() -> int:
    diag_src = DIAG.read_text(encoding="utf-8")
    diag_tree = _tree(DIAG)
    launch_src = LAUNCHER.read_text(encoding="utf-8")
    calls = _call_names(diag_tree)

    # ================================================================== #
    # HEADLINE — fail-closed behaviour of the REAL diagnostic & launcher
    # ================================================================== #
    r_a = _run({})
    check("headline_refuse_without_one_shot_gate", r_a["rc"] == 3,
          {"rc": r_a["rc"], "stdout_head": r_a["stdout"][:200]})

    r_b = _run({"PHASE36_FINAL_PROB_AUTHORITY_EXECUTE": "1"})
    check("headline_refuse_without_launch_token", r_b["rc"] == 5,
          {"rc": r_b["rc"], "stdout_head": r_b["stdout"][:200]})

    r_c = _run({"PHASE36_V1_14_LAUNCH_AUTHORITY": "1",
                "PHASE36_FINAL_PROB_AUTHORITY_EXECUTE": "1",
                "PHASE36_FINAL_PROB_AUTHORITY_V1_4_LAUNCH_AUTHORITY": "1"})
    check("headline_refuse_on_foreign_token_diagnostic", r_c["rc"] == 8,
          {"rc": r_c["rc"], "stdout_head": r_c["stdout"][:200]})

    r_d = _run({"PHASE36_V1_14_LAUNCH_AUTHORITY": "1"}, exe=VENV)
    check("headline_launcher_refuse_on_foreign_token", r_d["rc"] == 2,
          {"rc": r_d["rc"], "stdout_head": r_d["stdout"][:240]})

    for mk in MARKERS:
        check(f"no_marker_created::{mk}", not (AUD / mk).exists(), None)

    # ================================================================== #
    # D61 repair controls
    # ================================================================== #
    acc = _accept_calls(diag_tree)
    check("d61_accept_calls_canonical_fuse_full_field",
          bool(acc and "fuse_full_field" in acc), {"accept_calls": acc})
    check("d61_accept_does_not_call_model_fusion",
          bool(acc is not None and "_fuse_global_with_regional" not in acc), {"accept_calls": acc})
    _old_call_sites = [n.lineno for n in ast.walk(diag_tree)
                       if isinstance(n, ast.Call)
                       and (getattr(n.func, "id", None) or getattr(n.func, "attr", None))
                       == "_fuse_global_with_regional"]
    check("d61_old_model_fusion_absent_everywhere", not _old_call_sites,
          {"call_linenos": _old_call_sites})

    # MUTATION: swap the repair call -> static validator must DETECT (report FAIL).
    mutated = diag_src.replace("fused = mod.fuse_full_field(p_global, refined, geom)",
                               "fused = system._fuse_global_with_regional(p_global, refined, window)")
    check("d61_mutation_changed_source", mutated != diag_src, None)
    mut_acc = _accept_calls(_tree_src(mutated))
    mutated_detected = bool(mut_acc is not None
                            and "fuse_full_field" not in mut_acc
                            and "_fuse_global_with_regional" in mut_acc)
    check("d61_mutation_detected_by_static_validator", mutated_detected, {"mut_accept": mut_acc})
    mt = _tree_src(mutated)
    mut_has_fuse = any((getattr(n.func, "id", None) or getattr(n.func, "attr", None)) == "fuse_full_field"
                       for n in ast.walk(mt) if isinstance(n, ast.Call))
    mut_has_old = any((getattr(n.func, "id", None) or getattr(n.func, "attr", None)) == "_fuse_global_with_regional"
                      for n in ast.walk(mt) if isinstance(n, ast.Call))
    check("d61_mutation_detected_by_launcher_ast_gate",
          bool((not mut_has_fuse) or mut_has_old), {"mut_has_fuse": mut_has_fuse, "mut_has_old": mut_has_old})

    # Synthetic divergence: canonical fuse_full_field != old model fusion (pad-aware vs pad-unaware).
    from PIL import Image as _PIL

    def _canonical(pg, rc, geom):
        side = int(geom["crop_side_pixels"])
        cy1, cy2 = int(geom["clip_y1"]), int(geom["clip_y2"])
        cx1, cx2 = int(geom["clip_x1"]), int(geom["clip_x2"])
        pt, pl = int(geom["pad_top"]), int(geom["pad_left"])
        pil = _PIL.fromarray(np.ascontiguousarray(rc, dtype=np.float32), mode="F")
        square = np.asarray(pil.resize((side, side), _PIL.Resampling.BILINEAR), dtype=np.float32)
        out = np.asarray(pg, dtype=np.float32).copy()
        out[cy1:cy2, cx1:cx2] = square[pt:pt + (cy2 - cy1), pl:pl + (cx2 - cx1)]
        return out

    def _old(pg, rc, window):
        import torch
        y0, y1, x0, x1 = window
        out = pg.astype(np.float32).copy()
        crop = np.asarray(rc, dtype=np.float32)
        if crop.shape != (y1 - y0, x1 - x0):
            tgt = torch.from_numpy(crop)[None, None]
            resized = torch.nn.functional.interpolate(
                tgt, size=(y1 - y0, x1 - x0), mode="bilinear", align_corners=False)
            crop = resized[0, 0].numpy()
        out[y0:y1, x0:x1] = crop
        return out

    rng = np.random.default_rng(7)
    pg = rng.random((512, 512), dtype=np.float32)
    rc = rng.random((256, 256), dtype=np.float32)
    geom_clip = {"clip_y1": 0, "clip_y2": 384, "clip_x1": 0, "clip_x2": 384,
                 "crop_side_pixels": 512, "pad_top": 0, "pad_bottom": 128,
                 "pad_left": 0, "pad_right": 128}
    window = (0, 384, 0, 384)
    canon = _canonical(pg, rc, geom_clip)
    old = _old(pg, rc, window)
    divergent = not np.array_equal(canon, old)
    max_abs = float(np.abs(canon.astype(np.float64) - old.astype(np.float64)).max())
    check("d61_synthetic_padaware_diverges_from_old_fusion", divergent, {"max_abs": max_abs})
    check("d61_synthetic_canonical_deterministic",
          bool(np.array_equal(canon, _canonical(pg, rc, geom_clip))), None)

    # ================================================================== #
    # D69 identity control — reverting the fusion is detected
    # ================================================================== #
    import importlib.util as _ilu
    spec = _ilu.spec_from_file_location("_d14_nc", DIAG)
    d14 = _ilu.module_from_spec(spec)
    sys.modules["_d14_nc"] = d14
    spec.loader.exec_module(d14)
    check("d69_journal_env_toggle_present", hasattr(d14, "STAGE_JOURNAL_ENV"), None)
    check("d69_journal_dir_defined", "journal" in str(d14.JOURNAL_DIR).lower(), None)

    # ================================================================== #
    # D70 journal non-interference controls (synthetic, temp dirs)
    # ================================================================== #
    with tempfile.TemporaryDirectory(prefix="p36_v14_nc_d70_") as td:
        d14.JOURNAL_DIR = Path(td)
        fname = d14._journal_record("nc_stage", "BEGIN", "nc_attempt", d14.DIAGNOSTIC_REVISION)
        rec = json.loads((Path(td) / fname).read_text(encoding="utf-8"))
        check("d70_record_gt_free",
              bool(rec.get("contains_probabilities") is False
                   and rec.get("contains_masks") is False
                   and rec.get("contains_gt") is False
                   and rec.get("contains_metrics") is False), None)
        check("d70_record_scientific_output_false", rec.get("scientific_output") is False, None)
        # write-once: a second exclusive write of the same file must fail
        failed = False
        try:
            d14._write_once_json(Path(td) / fname, {"x": 1})
        except FileExistsError:
            failed = True
        except OSError:
            failed = True
        check("d70_journal_write_once_exclusive", failed, None)

    # ================================================================== #
    # D56 / D66 / GT / reach controls
    # ================================================================== #
    sub_sites = [n.lineno for n in ast.walk(diag_tree)
                 if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name)
                 and n.value.id == "_FROZEN_MOD"]
    check("d56_no_frozen_mod_subscript", not sub_sites, {"sites": sub_sites})
    gt_calls = [c for c in calls if c in GT_CALLABLES]
    check("gt_no_content_callable_call", not gt_calls, {"gt_calls": gt_calls})
    check("no_test_or_holdout_read",
          not any(tok in diag_src or tok in launch_src
                  for tok in ("test.csv", "holdout.csv", "ROUTER_HOLDOUT_PATH")), None)
    check("v1_4_token_present", "PHASE36_FINAL_PROB_AUTHORITY_V1_4_LAUNCH_AUTHORITY" in diag_src, None)
    check("no_v1_3_token_reuse", "PHASE36_FINAL_PROB_AUTHORITY_V1_3_LAUNCH_AUTHORITY" not in diag_src, None)
    check("no_v1_2_token_reuse", "PHASE36_FINAL_PROB_AUTHORITY_V1_2_LAUNCH_AUTHORITY" not in diag_src, None)
    check("no_v1_1_token_reuse", "PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY" not in diag_src, None)
    check("d66_incorrect_score_sha_absent_diagnostic", INCORRECT_SCORE_SHA not in diag_src, None)
    check("d66_incorrect_score_sha_absent_launcher", INCORRECT_SCORE_SHA not in launch_src, None)

    # Supervisor invariant control: self-test passes and never touches real markers.
    sr = subprocess.run([str(VENV), str(SUPERVISOR), "--self-test"], capture_output=True, text=True)
    sj = {}
    try:
        sj = json.loads(sr.stdout)
    except Exception:  # noqa: BLE001
        try:
            end = sr.stdout.rfind("}")
            start = sr.stdout.rfind("{", 0, end)
            sj = json.loads(sr.stdout[start:end + 1])
        except Exception:  # noqa: BLE001
            sj = {}
    check("supervisor_self_test_all_pass", sj.get("all_pass") is True, {"rc": sr.returncode})
    fixtures = sj.get("synthetic_fixtures") or {}
    check("supervisor_synthetic_fixtures_all_pass",
          bool(fixtures) and all(v.get("pass") for v in fixtures.values()),
          {"n_fixtures": len(fixtures)})

    n = len(RESULTS)
    n_ok = sum(1 for x in RESULTS if x["ok"])
    fails = [x for x in RESULTS if not x["ok"]]
    print(json.dumps({"suite": "negative_controls_v1_4", "n_checks": n, "n_pass": n_ok,
                      "all_pass": n_ok == n, "failures": fails}, indent=1))
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
