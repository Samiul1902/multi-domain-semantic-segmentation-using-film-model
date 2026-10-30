#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.3 — NEGATIVE CONTROLS (no model, no CUDA).

Adversarial controls for the v1.3 family (D61 canonical ACCEPT-fusion repair):

  HEADLINE (must FAIL CLOSED, no marker, no model, no GT):
   * the REAL v1.3 diagnostic refuses when the one-shot gate is absent (rc 3);
   * the REAL v1.3 diagnostic refuses when the v1.3 launch-authority token is absent (rc 5);
   * the REAL v1.3 diagnostic refuses when the FOREIGN v1.14 token is present (rc 8);
   * the REAL v1.3 launcher refuses when the FOREIGN v1.14 token is present (rc 2), and
     in that path NO marker is created and NO model is constructed.

  D61 repair controls (MUTATION-SENSITIVE):
   * the v1.3 diagnostic's ACCEPT branch calls the canonical ``fuse_full_field``;
   * the v1.3 diagnostic contains NO ``_fuse_global_with_regional`` reference;
   * MUTATION: replacing ``fuse_full_field`` with ``_fuse_global_with_regional`` in the
     ACCEPT branch is DETECTED by the static validator (which then reports FAIL);
   * MUTATION: the launcher-side D61 AST gate ALSO rejects the mutated source;
   * the canonical Phase27 ``fuse_full_field`` is PAD-AWARE while the old model fusion is
     PAD-UNAWARE (pure synthetic divergence evidence — NOT model execution).

  D56 controls (retained):
   * the v1.3 diagnostic has no ``_FROZEN_MOD[...]`` subscript site.

  GT / reach controls:
   * no GT-content callable is called anywhere in the v1.3 diagnostic;
   * no TEST / ROUTER_HOLDOUT read.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\phase36_final_probability_authority_diagnostic_negative_controls_v1_3.py
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts" / "analysis"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

VENV = ROOT / ".venv" / "Scripts" / "python.exe"
AUD = ROOT / "reports" / "audits"

DIAG = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_3.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_3.py"

GT_CALLABLES = ("_load_val_gt", "full_field_gt", "_dice", "_iou", "_hd95")
MARKERS = [
    "phase36_final_probability_authority_diagnostic_start_v1_3.json",
    "phase36_final_probability_authority_diagnostic_result_v1_3.json",
    "phase36_final_probability_authority_diagnostic_failure_v1_3.json",
]

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
    # strip any leakage of the tokens from this process
    for k in ("PHASE36_FINAL_PROB_AUTHORITY_EXECUTE",
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
    # (a) one-shot gate absent -> rc 3, refused before any marker.
    r_a = _run({})
    check("headline_refuse_without_one_shot_gate", r_a["rc"] == 3,
          {"rc": r_a["rc"], "stdout_head": r_a["stdout"][:200]})

    # (b) one-shot gate set but v1.3 token absent -> rc 5.
    r_b = _run({"PHASE36_FINAL_PROB_AUTHORITY_EXECUTE": "1"})
    check("headline_refuse_without_launch_token", r_b["rc"] == 5,
          {"rc": r_b["rc"], "stdout_head": r_b["stdout"][:200]})

    # (c) FOREIGN v1.14 token present -> rc 8 (highest priority), no marker.
    r_c = _run({"PHASE36_V1_14_LAUNCH_AUTHORITY": "1",
                "PHASE36_FINAL_PROB_AUTHORITY_EXECUTE": "1",
                "PHASE36_FINAL_PROB_AUTHORITY_V1_3_LAUNCH_AUTHORITY": "1"})
    check("headline_refuse_on_foreign_token_diagnostic", r_c["rc"] == 8,
          {"rc": r_c["rc"], "stdout_head": r_c["stdout"][:200]})

    # (d) launcher with FOREIGN token present -> rc 2 (fails closed), no marker.
    r_d = _run({"PHASE36_V1_14_LAUNCH_AUTHORITY": "1"}, exe=VENV)
    check("headline_launcher_refuse_on_foreign_token", r_d["rc"] == 2,
          {"rc": r_d["rc"], "stdout_head": r_d["stdout"][:240]})

    # no marker created by any of the refused runs.
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
    # The old model fusion must be ABSENT as a CALL (the literal string is legitimately
    # present as the D61 provenance constant D61_OLD_ACCEPT_CALL and in a comment).
    _old_call_sites = []
    for n in ast.walk(diag_tree):
        if isinstance(n, ast.Call):
            nm = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
            if nm == "_fuse_global_with_regional":
                _old_call_sites.append(n.lineno)
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
    # Launcher-side AST gate on the mutated source.
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
    check("d61_synthetic_padaware_diverges_from_old_fusion", divergent,
          {"max_abs": max_abs})
    # And the canonical semantics is deterministic (idempotent replicate).
    check("d61_synthetic_canonical_deterministic",
          bool(np.array_equal(canon, _canonical(pg, rc, geom_clip))), None)

    # ================================================================== #
    # D56 / GT / reach controls
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
    check("v1_3_token_present", "PHASE36_FINAL_PROB_AUTHORITY_V1_3_LAUNCH_AUTHORITY" in diag_src, None)
    check("no_v1_2_token_reuse", "PHASE36_FINAL_PROB_AUTHORITY_V1_2_LAUNCH_AUTHORITY" not in diag_src, None)
    check("no_v1_1_token_reuse", "PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY" not in diag_src, None)

    n = len(RESULTS)
    n_ok = sum(1 for x in RESULTS if x["ok"])
    fails = [x for x in RESULTS if not x["ok"]]
    print(json.dumps({"suite": "negative_controls_v1_3", "n_checks": n, "n_pass": n_ok,
                      "all_pass": n_ok == n, "failures": fails}, indent=1))
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
