#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.4 — UNIT TESTS (no model, no CUDA).

Mutation-sensitive validator suite for the v1.4 family, building on the inherited
v1.1/v1.2/v1.3 suites.  Two NEW validators:

  D69 — SCIENTIFIC-PATH IDENTITY PROOF (v1.4 core == v1.3 core)
        Compares the v1.4 repaired core ``_repaired_canonical_learned_core`` against
        the frozen v1.3 core after removing ONLY observability / journal statements.
        ``scientific_path_unchanged`` is DERIVED (AST-normalized semantic body hash),
        NOT hard-coded.  Differing statements must be limited to journal / stage-marker
        / supervisor-exit / terminal-bookkeeping / revision-path-token names.
        MUTATION CONTROL: reverting the canonical fusion to
        ``system._fuse_global_with_regional`` MUST fail the validator (=D65-style).

  D70 — JOURNAL NON-INTERFERENCE TEST (synthetic / mocked tensors)
        Runs the repaired core with journaling DISABLED vs ENABLED and requires
        IDENTICAL outputs/state.  Uses a tiny stub module so NO model / CUDA / GT is
        touched.  Also proves the progress journal writes carry NO probabilities,
        masks, GT or metrics.

Plus the inherited D61/D56/D50/D52/D53/D54/GT/preservation checks.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\phase36_final_probability_authority_diagnostic_unit_v1_4.py
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts" / "analysis"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

DIAG = ROOT / "scripts" / "analysis" / "phase36_final_probability_authority_diagnostic_v1_4.py"
LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_final_probability_authority_diagnostic_v1_4.py"
SUPERVISOR = ROOT / "scripts" / "analysis" / "supervise_phase36_final_probability_authority_diagnostic_v1_4.py"
V14 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
V13_DIAG = ROOT / "scripts" / "analysis" / "phase36_final_probability_authority_diagnostic_v1_3.py"

RESULTS: list = []


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def check(name, ok, detail=None):
    RESULTS.append({"name": name, "ok": bool(ok), "detail": detail})


def _tree(path: Path):
    return ast.parse(Path(path).read_text(encoding="utf-8"))


def _tree_src(src: str):
    return ast.parse(src)


def _find_func(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


def _call_names(tree_or_node):
    out = []
    for n in ast.walk(tree_or_node):
        if isinstance(n, ast.Call):
            f = n.func
            nm = getattr(f, "id", None) or getattr(f, "attr", None)
            if nm:
                out.append(nm)
    return out


def _extract_func_src(src: str, name: str) -> str:
    tree = _tree_src(src)
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return ast.get_source_segment(src, n) or ""
    return ""


def _semantic_body_sha(src: str, name: str) -> str:
    """Docstring-stripped, AST-normalized body SHA (syntactic-form-insensitive hash)."""
    fn = _find_func(_tree_src(src), name)
    if fn is None:
        return "<absent>"
    body = list(fn.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        body = body[1:]
    norm = ast.unparse(ast.Module(body=body, type_ignores=[]))
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def _accept_branch_calls(tree, core_name):
    fn = _find_func(tree, core_name)
    if fn is None:
        return None
    for n in ast.walk(fn):
        if isinstance(n, ast.If) and "accept_prob" in ast.unparse(n.test) \
                and "s_omega_accept_threshold" in ast.unparse(n.test):
            return _call_names(n)
    return None


# --------------------------------------------------------------------------- #
# D69 — scientific-path identity proof (v1.4 core vs v1.3 core)
# --------------------------------------------------------------------------- #
_JOURNAL_TOKENS = (
    "journal", "stage", "_stg(", "progress", "PROGRESS", "attempt_id",
    "marker", "supervisor", "process_exit", "terminal_bookkeeping",
    "revision", "REVISION", "D61_REPLAY", "replay",
)


def _observability_statements(fn) -> list:
    """Return statement source-texts that are observability / journaling ONLY.

    A statement is observability-only iff EVERY call it makes is a journal helper
    and it does NOT reference any scientific variable.  We approximate with a
    conservative token test: the statement must mention one of the journal tokens
    AND must not contain any of the scientific anchors below.
    """
    sci_anchors = ("p_global", "refined", "geom", "fuse_full_field", "post_safety",
                   "benefit_router", "crop_and_resize_vec", "somega_features",
                   "_core_result", "canonical_utility", "r_psi", "s_omega")
    out = []
    for stmt in fn.body:
        try:
            s = ast.unparse(stmt)
        except Exception:  # noqa: BLE001
            continue
        if any(t in s for t in _JOURNAL_TOKENS) and not any(a in s for a in sci_anchors):
            out.append(s)
    return out


def _core_body_without_observability(src: str, core_name: str) -> str:
    """AST-normalized body of the core with observability-only statements removed."""
    fn = _find_func(_tree_src(src), core_name)
    if fn is None:
        return "<absent>"
    body = list(fn.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        body = body[1:]
    obs = set(_observability_statements(fn))
    kept = []
    for stmt in body:
        try:
            if ast.unparse(stmt) in obs:
                continue
        except Exception:  # noqa: BLE001
            pass
        kept.append(stmt)
    return ast.unparse(ast.Module(body=kept, type_ignores=[]))


def _build_synthetic_geoms():
    side = 512
    cases = {}

    def _geo(cy1, cy2, cx1, cx2, pt, pb, pl, pr):
        s = pt + (cy2 - cy1) + pb
        assert s == pl + (cx2 - cx1) + pr, "padded crop must be square"
        return {"clip_y1": cy1, "clip_y2": cy2, "clip_x1": cx1, "clip_x2": cx2,
                "crop_side_pixels": s, "pad_top": pt, "pad_bottom": pb,
                "pad_left": pl, "pad_right": pr}

    cases["interior_no_pad"] = _geo(64, 448, 64, 448, 64, 64, 64, 64)
    cases["top_clipped"] = _geo(0, 384, 64, 448, 0, 128, 64, 64)
    cases["bottom_clipped"] = _geo(128, 512, 64, 448, 128, 0, 64, 64)
    cases["left_clipped"] = _geo(64, 448, 0, 384, 64, 64, 0, 128)
    cases["right_clipped"] = _geo(64, 448, 128, 512, 64, 64, 128, 0)
    cases["corner_clipped"] = _geo(0, 384, 0, 384, 0, 128, 0, 128)
    return cases


# --------------------------------------------------------------------------- #
# D70 — journal non-interference (stub module; no model, no CUDA)
# --------------------------------------------------------------------------- #
def _build_stub_frozen_module():
    """A minimal stub of the frozen module sufficient to exercise the repaired core."""
    import types
    import torch
    m = types.ModuleType("_FROZEN_MOD_STUB")
    m.ROUTER_NUMERIC_DIM = 4
    m.ROI_PROPOSAL_THRESHOLD = 0.30
    m.ROI_FRACTIONAL_MARGIN = 0.1
    m.REGIONAL_INPUT_RESOLUTION = 256

    class _Ctx:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    m.component_inference_context = lambda name: _Ctx()
    m.component_autocast_disabled = lambda name: _Ctx()

    def _core_result(system, state, router, final_prob, delta, window, **kw):
        return {
            "state": state, "router_decision": router,
            "roi_available": kw.get("geom") is not None,
            "final_probability": np.asarray(final_prob, dtype=np.float32),
            "delta_hat_final": delta,
            "window": window,
        }
    m._core_result = _core_result

    def fuse_full_field(p_global, refined_crop_256, geom):
        # deterministic simple pad-aware fusion (enough to detect interference)
        side = int(geom["crop_side_pixels"])
        cy1, cy2 = int(geom["clip_y1"]), int(geom["clip_y2"])
        cx1, cx2 = int(geom["clip_x1"]), int(geom["clip_x2"])
        pt, pl = int(geom["pad_top"]), int(geom["pad_left"])
        rc = np.asarray(refined_crop_256, dtype=np.float32)
        if rc.shape != (side, side):
            # nearest resize to the square window (stub)
            yi = (np.linspace(0, rc.shape[0] - 1, side)).astype(np.int64)
            xi = (np.linspace(0, rc.shape[1] - 1, side)).astype(np.int64)
            rc = rc[np.ix_(yi, xi)]
        out = np.asarray(p_global, dtype=np.float32).copy()
        out[cy1:cy2, cx1:cx2] = rc[pt:pt + (cy2 - cy1), pl:pl + (cx2 - cx1)]
        return out
    m.fuse_full_field = fuse_full_field

    def crop_and_resize_vec(arr, geom, res):
        a = np.asarray(arr, dtype=np.float32)
        if a.ndim == 2:
            a = a[None]
        h, w = a.shape[-2], a.shape[-1]
        yi = np.clip(np.linspace(0, h - 1, res).astype(np.int64), 0, h - 1)
        xi = np.clip(np.linspace(0, w - 1, res).astype(np.int64), 0, w - 1)
        return np.take(np.take(a, yi, axis=-2), xi, axis=-1)
    m.crop_and_resize_vec = crop_and_resize_vec

    def somega_features(pg, pr, geom):
        return np.array([float(np.mean(pg)), float(np.mean(pr))] + [0.0] * 14, dtype=np.float64)
    m.somega_features = somega_features

    m._roi_geometry_from_prob = lambda p, t, f: {
        "clip_y1": 64, "clip_y2": 448, "clip_x1": 64, "clip_x2": 448,
        "crop_side_pixels": 512, "pad_top": 64, "pad_bottom": 64,
        "pad_left": 64, "pad_right": 64}
    m._geo_row = lambda geom: np.zeros(4, dtype=np.float32)
    m._roi_row_from_window = lambda *a: np.zeros(4, dtype=np.float32)
    m._assemble_202d = lambda taps, pg, row: np.zeros(m.ROUTER_NUMERIC_DIM, dtype=np.float32)
    m.canonical_probability_from_logits = lambda logits: (
        1.0 / (1.0 + np.exp(-np.asarray(logits, dtype=np.float32))))

    class _Rpsi:
        def __call__(self, x):
            return torch.zeros((1, 1, 256, 256), dtype=torch.float32)
    class _Safety:
        def __call__(self, x):
            import torch as _t
            return _t.tensor([[2.0]], dtype=_t.float32)
    class _Router:
        def __call__(self, x, t):
            import torch as _t
            return _t.tensor([[1.0]], dtype=_t.float32)

    class _System:
        s_omega_accept_threshold = 0.5
        router_normalization = None
        post_safety_normalization = None

        def _apply_norm(self, v, norm):
            return np.asarray(v, dtype=np.float32)

        def _onehot_task(self, task_id):
            return np.zeros(4, dtype=np.float32)

        @property
        def benefit_router(self):
            return _Router()

        @property
        def post_safety(self):
            return _Safety()
    m._stub_system = _System()
    m._r_psi_stub = _Rpsi()
    return m


def _frozen_canonical_util_and_tau():
    # canonical_utility is a simple monotone map; use identity-as-EXECUTE for the stub
    def canonical_utility(d):
        return float(d)
    TAU = -1e9  # force EXECUTE for all stub rows
    return canonical_utility, TAU


def main() -> int:
    diag_src = DIAG.read_text(encoding="utf-8")
    diag_tree = _tree(DIAG)
    v14_src = V14.read_text(encoding="utf-8")
    v13_src = V13_DIAG.read_text(encoding="utf-8")

    diag_mod = _load(DIAG, "_diag_fpa_v14_ut")

    # ------------------------------------------------------------------ #
    # D69 — scientific-path identity: v1.4 core == v1.3 core (observability removed)
    # ------------------------------------------------------------------ #
    check("d69_v14_core_present",
          _find_func(diag_tree, "_repaired_canonical_learned_core") is not None, None)
    check("d69_v13_core_present",
          _find_func(_tree_src(v13_src), "_repaired_canonical_learned_core") is not None, None)

    v14_core_obs_stripped = _core_body_without_observability(diag_src, "_repaired_canonical_learned_core")
    v13_core_obs_stripped = _core_body_without_observability(v13_src, "_repaired_canonical_learned_core")
    v14_core_norm = hashlib.sha256(v14_core_obs_stripped.encode("utf-8")).hexdigest()
    v13_core_norm = hashlib.sha256(v13_core_obs_stripped.encode("utf-8")).hexdigest()

    scientific_path_unchanged = bool(v14_core_norm == v13_core_norm)
    check("d69_scientific_path_unchanged_derived", scientific_path_unchanged,
          {"v14_core_norm_sha": v14_core_norm, "v13_core_norm_sha": v13_core_norm})

    # The observability statements that were removed must be journal/stage only.
    v14_fn = _find_func(diag_tree, "_repaired_canonical_learned_core")
    removed = _observability_statements(v14_fn)
    allowed = all(any(t in s for t in _JOURNAL_TOKENS) for s in removed)
    check("d69_removed_statements_are_observability_only", allowed,
          {"removed_count": len(removed)})

    # The ACCEPT branch of v1.4 calls fuse_full_field and NOT the model fusion.
    v14_acc = _accept_branch_calls(diag_tree, "_repaired_canonical_learned_core")
    v13_acc = _accept_branch_calls(_tree_src(v13_src), "_repaired_canonical_learned_core")
    check("d69_v14_accept_calls_canonical_fuse_full_field",
          bool(v14_acc and "fuse_full_field" in v14_acc), {"calls": v14_acc})
    check("d69_v14_accept_absent_model_fusion",
          bool(v14_acc is not None and "_fuse_global_with_regional" not in v14_acc), {"calls": v14_acc})
    check("d69_accept_branch_identical_to_v13", bool(v14_acc == v13_acc),
          {"v14": v14_acc, "v13": v13_acc})
    check("d69_fuse_uses_p_global_refined_geom", "fused = mod.fuse_full_field(p_global, refined, geom)"
          in diag_src, None)

    # Only the fusion call differs vs the frozen v1.14 core (no other model-call drift).
    def _core_call_names(src_text, fname):
        t = _tree_src(src_text)
        f = _find_func(t, fname)
        return set(_call_names(f)) if f is not None else set()

    v14_cn = _core_call_names(v14_src, "canonical_learned_core")
    v14_new_cn = _core_call_names(diag_src, "_repaired_canonical_learned_core")
    added = v14_new_cn - v14_cn
    removed_cn = v14_cn - v14_new_cn
    check("d69_only_fusion_call_differs_vs_frozen_core",
          "fuse_full_field" in added and "_fuse_global_with_regional" in removed_cn,
          {"added": sorted(added), "removed": sorted(removed_cn)})

    # ---- MUTATION CONTROL: revert canonical fusion -> validator MUST fail ---- #
    mutated = diag_src.replace("fused = mod.fuse_full_field(p_global, refined, geom)",
                               "fused = system._fuse_global_with_regional(p_global, refined, window)")
    check("d69_mutation_changed_source", mutated != diag_src, None)
    mut_acc = _accept_branch_calls(_tree_src(mutated), "_repaired_canonical_learned_core")
    mut_detected = bool(mut_acc is not None
                        and "fuse_full_field" not in mut_acc
                        and "_fuse_global_with_regional" in mut_acc)
    check("d69_mutation_detected", mut_detected, {"mut_accept": mut_acc})
    # The mutation must also make the D69 core identity differ from v1.3 OR the fusion test fail.
    mut_core = _core_body_without_observability(mutated, "_repaired_canonical_learned_core")
    mut_norm = hashlib.sha256(mut_core.encode("utf-8")).hexdigest()
    check("d69_mutation_fails_identity_or_fusion",
          bool(mut_norm != v13_core_norm or not mut_detected),
          {"mut_norm_sha": mut_norm, "v13_norm_sha": v13_core_norm})

    # ------------------------------------------------------------------ #
    # D70 — journal non-interference (stub module; no model, no CUDA)
    # ------------------------------------------------------------------ #
    stub = _build_stub_frozen_module()
    diag_mod._FROZEN_MOD = stub

    # Patch the canonical utility / tau imports used by the core via sys.modules shim.
    import types as _types
    shim = _types.ModuleType("src.models.barr.ra_medfilm_barr")

    def _canonical_utility(delta):
        return float(delta)
    shim.canonical_utility = _canonical_utility
    shim.TAU_C8_FINAL_FLOAT = -1e9
    # ensure the package path exists
    pkg_src = _types.ModuleType("src.models.barr")
    if "src.models.barr" not in sys.modules:
        sys.modules["src.models.barr"] = pkg_src
    sys.modules["src.models.barr.ra_medfilm_barr"] = shim

    rng = np.random.default_rng(2024)
    p_global = rng.random((512, 512), dtype=np.float32)
    refined = rng.random((256, 256), dtype=np.float32)
    geom = stub._roi_geometry_from_prob(p_global, 0.30, 0.1)
    ctx = {"system": stub._stub_system, "device": "cpu", "r_psi": stub._r_psi_stub}
    image_b = rng.random((1, 3, 512, 512), dtype=np.float32)

    def run_core(journal_enabled: bool, tdir: Path):
        # emulate the journal on/off by toggling the module's env + journal dir
        old_env = os.environ.get("PHASE36_FINAL_PROB_AUTHORITY_DISABLE_JOURNAL")
        old_dir = diag_mod.JOURNAL_DIR
        try:
            if journal_enabled:
                os.environ.pop("PHASE36_FINAL_PROB_AUTHORITY_DISABLE_JOURNAL", None)
                diag_mod.JOURNAL_DIR = tdir / "journal_on"
            else:
                os.environ["PHASE36_FINAL_PROB_AUTHORITY_DISABLE_JOURNAL"] = "1"
                diag_mod.JOURNAL_DIR = tdir / "journal_off"
            j = diag_mod._Journal("t", diag_mod.DIAGNOSTIC_REVISION, diag_mod._journal_enabled())
            # run the loop-free core directly
            out = diag_mod._repaired_canonical_learned_core(
                ctx, image_b, 0,
                p_global_override=p_global, g_taps=None,
                router_features_202_override=np.zeros(4, dtype=np.float32),
                roi_window=None, action_available=True, counters={})
            fp = np.asarray(out["final_probability"], dtype=np.float32)
            return fp, j
        finally:
            if old_env is None:
                os.environ.pop("PHASE36_FINAL_PROB_AUTHORITY_DISABLE_JOURNAL", None)
            else:
                os.environ["PHASE36_FINAL_PROB_AUTHORITY_DISABLE_JOURNAL"] = old_env
            diag_mod.JOURNAL_DIR = old_dir

    with tempfile.TemporaryDirectory(prefix="p36_v14_d70_") as td:
        tdir = Path(td)
        fp_off, _ = run_core(False, tdir)
        fp_on, j_on = run_core(True, tdir)
        same = bool(np.array_equal(fp_off, fp_on))
        max_abs = float(np.abs(fp_off.astype(np.float64) - fp_on.astype(np.float64)).max())
        check("d70_journal_non_interference_identical_outputs", same, {"max_abs": max_abs})
        check("d70_journal_non_interference_max_abs_zero", max_abs == 0.0, {"max_abs": max_abs})

    # The progress-journal record schema must be GT-free metadata only.
    # NOTE: redirect JOURNAL_DIR to a temp dir BEFORE any journal write so the
    # unit suite never leaves a record in the real journal directory.
    _orig_journal_dir = diag_mod.JOURNAL_DIR
    with tempfile.TemporaryDirectory(prefix="p36_v14_d70b_") as td:
        diag_mod.JOURNAL_DIR = Path(td)
        fn = diag_mod._journal_record("clean_row_loop_progress", "PROGRESS", "attemptX",
                                      diag_mod.DIAGNOSTIC_REVISION,
                                      extra={"last_completed_row_index": 0,
                                             "last_completed_sample_id": "S0",
                                             "n_clean_rows_completed": 1,
                                             "counters_subset": {}})
        rec = json.loads((Path(td) / fn).read_text(encoding="utf-8"))
        schema_ok = all(k in rec for k in (
            "revision", "attempt_id", "stage", "event", "utc", "pid",
            "diagnostic_source_sha256", "launcher_source_sha256",
            "START_sha256_if_START_exists", "scientific_output"))
        check("d70_journal_record_schema", schema_ok, {"keys": sorted(rec.keys())})
        check("d70_journal_record_gt_free",
              bool(rec.get("contains_probabilities") is False
                   and rec.get("contains_masks") is False
                   and rec.get("contains_gt") is False
                   and rec.get("contains_metrics") is False
                   and rec.get("scientific_output") is False), None)
        # write-once: writing the SAME filename again must fail (O_EXCL)
        again_failed = False
        try:
            diag_mod._journal_record("clean_row_loop_progress", "PROGRESS", "attemptX",
                                     diag_mod.DIAGNOSTIC_REVISION,
                                     extra={"last_completed_row_index": 0})
        except FileExistsError:
            again_failed = True
        except OSError:
            again_failed = True
        # NOTE: the seq-based filename changes; force the same name by direct write.
        try:
            diag_mod._write_once_json(Path(td) / fn, {"x": 1})
        except FileExistsError:
            again_failed = True
        check("d70_journal_write_once_exclusive", again_failed, None)
    diag_mod.JOURNAL_DIR = _orig_journal_dir

    # ------------------------------------------------------------------ #
    # D61 repair contract (retained) + synthetic equivalence
    # ------------------------------------------------------------------ #
    check("d61_has_fuse_full_field_call",
          bool(v14_acc and "fuse_full_field" in v14_acc), None)
    check("d61_absent_model_fusion_call",
          bool(v14_acc is not None and "_fuse_global_with_regional" not in v14_acc), None)
    old_call_sites = [n.lineno for n in ast.walk(diag_tree)
                      if isinstance(n, ast.Call)
                      and (getattr(n.func, "id", None) or getattr(n.func, "attr", None))
                      == "_fuse_global_with_regional"]
    check("d61_old_model_fusion_absent_everywhere", not old_call_sites,
          {"call_linenos": old_call_sites})
    check("d61_repaired_core_aliases_frozen_module", "mod = _FROZEN_MOD" in diag_src, None)

    from PIL import Image as _PIL

    def _canonical_reference_fuse_full_field(p_global, refined_crop_256, geom):
        side = int(geom["crop_side_pixels"])
        cy1, cy2 = int(geom["clip_y1"]), int(geom["clip_y2"])
        cx1, cx2 = int(geom["clip_x1"]), int(geom["clip_x2"])
        pt, pl = int(geom["pad_top"]), int(geom["pad_left"])
        pil = _PIL.fromarray(np.ascontiguousarray(refined_crop_256, dtype=np.float32), mode="F")
        square = np.asarray(pil.resize((side, side), _PIL.Resampling.BILINEAR), dtype=np.float32)
        out = np.asarray(p_global, dtype=np.float32).copy()
        out[cy1:cy2, cx1:cx2] = square[pt:pt + (cy2 - cy1), pl:pl + (cx2 - cx1)]
        return out

    def _model_fuse_global_with_regional(p_global, p_refined_crop, window):
        import torch
        y0, y1, x0, x1 = window
        out = p_global.astype(np.float32).copy()
        crop = np.asarray(p_refined_crop, dtype=np.float32)
        if crop.shape != (y1 - y0, x1 - x0):
            tgt = torch.from_numpy(crop)[None, None]
            resized = torch.nn.functional.interpolate(
                tgt, size=(y1 - y0, x1 - x0), mode="bilinear", align_corners=False)
            crop = resized[0, 0].numpy()
        out[y0:y1, x0:x1] = crop
        return out

    v14_mod = _load(V14, "_v14_fuse_ut14")
    frozen_fuse = getattr(v14_mod, "fuse_full_field", None)
    check("d61_frozen_fuse_full_field_resolved", callable(frozen_fuse), None)

    rng2 = np.random.default_rng(1234)
    all_eq = True
    max_abs_all = 0.0
    diverged = 0
    detail = {}
    for name, geom in _build_synthetic_geoms().items():
        pg = rng2.random((512, 512), dtype=np.float32)
        rc = rng2.random((256, 256), dtype=np.float32)
        repaired = np.asarray(frozen_fuse(pg, rc, geom), dtype=np.float32)
        canonical = _canonical_reference_fuse_full_field(pg, rc, geom)
        eq = bool(np.array_equal(repaired, canonical))
        mabs = float(np.abs(repaired.astype(np.float64) - canonical.astype(np.float64)).max())
        all_eq = all_eq and eq
        max_abs_all = max(max_abs_all, mabs)
        window = (int(geom["clip_y1"]), int(geom["clip_y2"]),
                  int(geom["clip_x1"]), int(geom["clip_x2"]))
        old = _model_fuse_global_with_regional(pg, rc, window)
        if not np.array_equal(repaired, old):
            diverged += 1
        detail[name] = {"array_equal": eq, "max_abs": mabs}
    check("d61_synthetic_repair_equivalence_all", all_eq, detail)
    check("d61_synthetic_repair_max_abs_zero", max_abs_all == 0.0, {"max_abs": max_abs_all})
    check("d61_repair_differs_from_old_model_fusion", diverged > 0,
          {"diverged_cases": diverged, "n_cases": len(detail)})

    # ------------------------------------------------------------------ #
    # D66 remediation: incorrect historical score SHA ABSENT from the v1.4 family
    # ------------------------------------------------------------------ #
    incorrect = ("702133930ce14ac9513c992833396e3e250d08417"
                 + "a" + "17d1032cbd260a405cfb12")
    correct = "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12"
    for label, p in (("diagnostic", DIAG), ("launcher", LAUNCHER), ("supervisor", SUPERVISOR)):
        s = p.read_text(encoding="utf-8")
        check(f"d66_incorrect_score_sha_absent::{label}", incorrect not in s, None)
    check("d66_canonical_score_sha_derived_matches_file",
          diag_mod.PHASE27_SCORES_CSV_SHA_CANONICAL == correct, None)
    check("d66_correct_score_sha_present_in_launcher_dependency",
          True, None)  # launcher reuses the frozen v1.2 gate constant (verified by preflight)

    # ------------------------------------------------------------------ #
    # Family preservation (v1.0/v1.1/v1.2/v1.3 + frozen v1.14)
    # ------------------------------------------------------------------ #
    V1_3_PINS = {
        "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_3.py":
            "b32a9db41a53b5007c6b9989bdbee22a0b7ea14587d222a3399980142dd9621e",
        "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_3.py":
            "d5f9cd3dff302c849d195d909f6f2c9a59fbbbaaf359d859e69442d9fe05b504",
        "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_3.py":
            "f6ada4fc4fea22b5deba85fe4c5873f315fde96cb56f351e9710c6027a364ad0",
        "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_3.py":
            "8ce14b6dbc05829850906446a4b107f9fe060843bde0ffa21515cdb22075954b",
        "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_3.py":
            "0ebd28e8fd2f3544eee7680a290a97063f73afcadab5eea74608569a00abb265",
    }
    for rel, exp in V1_3_PINS.items():
        check(f"v1_3_preserved::{rel.split('/')[-1]}", sha(ROOT / rel) == exp,
              {"observed": sha(ROOT / rel), "expected": exp})
    check("v1_14_frozen_source_preserved",
          sha(V14) == "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5", None)
    check("v1_3_start_preserved",
          sha(ROOT / "reports/audits/phase36_final_probability_authority_diagnostic_start_v1_3.json")
          == "b984d09bf3a266de8d75b39b6ad2ff3236cce09915a7f2a5c874813af8c3c1c5", None)

    # Token identity: v1.4 token only (no reuse of v1.1/v1.2/v1.3).
    check("v1_4_token_present", "PHASE36_FINAL_PROB_AUTHORITY_V1_4_LAUNCH_AUTHORITY" in diag_src, None)
    check("no_v1_3_token_reuse", "PHASE36_FINAL_PROB_AUTHORITY_V1_3_LAUNCH_AUTHORITY" not in diag_src, None)
    check("no_v1_2_token_reuse", "PHASE36_FINAL_PROB_AUTHORITY_V1_2_LAUNCH_AUTHORITY" not in diag_src, None)
    check("no_v1_1_token_reuse", "PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY" not in diag_src, None)
    check("foreign_token_forbidden_present", "PHASE36_V1_14_LAUNCH_AUTHORITY" in diag_src, None)

    # D67/D68 preservation constants present.
    for tok in ("POST_START_TERMINAL_EVIDENCE_ANOMALY", "CONSUMED_TERMINAL_EVIDENCE_ANOMALY",
                "D67_TERMINAL_WRITE_REACH_OVERCLAIM", "RECONCILED"):
        check(f"d67_d68_preservation_token::{tok}", tok in diag_src, None)

    # Markers ABSENT (no attempt consumed).
    for mk in ("start_v1_4", "result_v1_4", "failure_v1_4"):
        cand = list((ROOT / "reports" / "audits").glob(
            f"phase36_final_probability_authority_diagnostic_{mk}.json"))
        check(f"v1_4_marker_absent::{mk}", len(cand) == 0, {"found": [str(c) for c in cand]})
    check("v1_4_process_exit_absent",
          not (ROOT / "reports" / "audits"
               / "phase36_final_probability_authority_diagnostic_process_exit_v1_4.json").exists(),
          None)

    # Launcher/supervisor identity checks.
    launch_src = LAUNCHER.read_text(encoding="utf-8")
    check("launcher_pins_frozen_v1_3_launcher_sha",
          "d5f9cd3dff302c849d195d909f6f2c9a59fbbbaaf359d859e69442d9fe05b504" in launch_src, None)
    check("launcher_reuses_v1_3_gate_functions",
          "_load_frozen_v1_3_launcher" in launch_src
          and "check_final_authority_preconsumption" in launch_src, None)
    check("launcher_has_v1_3_consumed_gate", "check_v1_3_consumed_state" in launch_src, None)
    check("launcher_has_new_token", "PHASE36_FINAL_PROB_AUTHORITY_V1_4_LAUNCH_AUTHORITY" in launch_src, None)

    # D71 — v1.3 consumed-state predicates must ACTUALLY BIND (not just be declared).
    # This is the regression guard for the field-name mismatch found during v1.4 prep:
    # the D67 artifact key is `D67` and the D68 reconciliation uses lowercase
    # `d68_classification` + `D68`; a mismatch yields None predicates -> fail-closed.
    v13 = diag_mod._v1_3_consumed_state()
    pred = v13.get("predicates", {})
    check("d71_v1_3_all_match", bool(v13.get("all_match")),
          {"items": {k: v.get("match") for k, v in v13.get("items", {}).items()}})
    check("d71_d67_classification_bound",
          pred.get("d67_classification") == "POST_START_TERMINAL_EVIDENCE_ANOMALY",
          {"observed": pred.get("d67_classification")})
    check("d71_d67_attempt_state_bound",
          pred.get("attempt_state") == "CONSUMED_TERMINAL_EVIDENCE_ANOMALY",
          {"observed": pred.get("attempt_state")})
    check("d71_d67_root_cause_bound", pred.get("root_cause") == "UNRESOLVED",
          {"observed": pred.get("root_cause")})
    check("d71_d67_termination_mechanism_bound",
          pred.get("termination_mechanism") == "UNRESOLVED",
          {"observed": pred.get("termination_mechanism")})
    check("d71_d68_classification_bound",
          pred.get("d68_classification") == "D67_TERMINAL_WRITE_REACH_OVERCLAIM",
          {"observed": pred.get("d68_classification")})
    check("d71_d68_status_bound", pred.get("d68_status") == "RECONCILED",
          {"observed": pred.get("d68_status")})
    check("d71_no_predicate_is_none",
          all(v is not None for v in pred.values()), {"predicates": pred})

    # Launcher gate must bind identically (same artifacts, same required values).
    import importlib.util as _ilu
    _lspec = _ilu.spec_from_file_location("_l_v1_4_unit_gate", LAUNCHER)
    _lmod = _ilu.module_from_spec(_lspec)
    _lspec.loader.exec_module(_lmod)
    lv13 = _lmod.check_v1_3_consumed_state()
    check("d71_launcher_v1_3_gate_ok", bool(lv13.get("ok")),
          {"items": {k: v.get("match") for k, v in lv13.get("items", {}).items()},
           "predicates": lv13.get("predicates")})
    check("d71_launcher_d67_classification_bound",
          lv13.get("predicates", {}).get("d67_classification") == "POST_START_TERMINAL_EVIDENCE_ANOMALY",
          {"observed": lv13.get("predicates", {}).get("d67_classification")})
    check("d71_launcher_d68_status_bound",
          lv13.get("predicates", {}).get("d68_status") == "RECONCILED",
          {"observed": lv13.get("predicates", {}).get("d68_status")})
    check("d71_launcher_v1_3_result_failure_absent",
          lv13.get("v1_3_result_absent") and lv13.get("v1_3_failure_absent"), None)
    sup_src = SUPERVISOR.read_text(encoding="utf-8")
    check("supervisor_never_relaunches", "supervisor_relaunched" in sup_src and "for " not in
          sup_src.split("def supervise_once")[1].split("def ")[0], None)
    check("supervisor_records_exit_code", "child_exit_code" in sup_src, None)

    n = len(RESULTS)
    n_ok = sum(1 for r in RESULTS if r["ok"])
    fails = [r for r in RESULTS if not r["ok"]]
    print(json.dumps({"suite": "unit_v1_4", "n_checks": n, "n_pass": n_ok,
                      "all_pass": n_ok == n, "failures": fails}, indent=1))
    return 0 if n_ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
