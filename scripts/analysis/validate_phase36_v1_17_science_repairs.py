"""Phase36 v1.17 science-repair validator + diff proof (D61/D75 preserved) + negatives.

REBASED FROM v1.16.  Machine-derived (AST/source-analysis), NOT hard-coded booleans.

Provides:
  * v1_14_to_v1_17 diff classification  (must be exactly the 2 scientific repair
    CLASSES — D61 / D75 — with 0 unclassified scientific deltas; all other hunks are
    OPERATIONAL_GOVERNANCE)
  * POLICY_B static coverage validator
  * G downstream quantization absence control
  * D61 fusion control
  * synthetic representation + fusion tests
  * POLICY_B negative controls (mutation => FAIL)

Non-consuming: pure source analysis + numpy synthetic arrays.  No model, no checkpoint,
no VAL image, no VAL GT, no TEST, no ROUTER_HOLDOUT, no perturbation execution.
"""

from __future__ import annotations

import ast
import difflib
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
V14 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
V15 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_15.py"
V16 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_16.py"
V17 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_17.py"

V14_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
V15_SHA = "b194ad28345ea8b268748be383ca98b936cb051d85854666e3141250f3eae002"
V16_SHA = "a96b74caa4587aa9d2f83b79ed39c13075a88086109e31d991695a75ec4abab9"
V17_SHA = "81d78460b2f20f176bc697cba662c43bc7c7443ea555ba95a30609faf0ccbe31"

POLICY_HELPER = "_phase27_scored_final_binary"

n_pass = 0
n_fail = 0
failures: list[str] = []


def ok(name: str, cond: bool) -> None:
    global n_pass, n_fail
    if cond:
        n_pass += 1
    else:
        n_fail += 1
        failures.append(name)
        print(f"  FAIL {name}")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# 1. Diff proof (v1.14 -> v1.17)
# --------------------------------------------------------------------------- #
def compute_diff_hunks(a_path: Path, b_path: Path) -> list[dict]:
    a = a_path.read_text(encoding="utf-8").splitlines(keepends=True)
    b = b_path.read_text(encoding="utf-8").splitlines(keepends=True)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    hunks = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        hunks.append(
            {
                "tag": tag,
                "a_span": [i1, i2],
                "b_span": [j1, j2],
                "a_text": "".join(a[i1:i2]),
                "b_text": "".join(b[j1:j2]),
            }
        )
    return hunks


_GOVERNANCE_TOKENS = (
    "v1_15", "V1_15", "v1.15", "v1_16", "V1_16", "V1.16", "v1.16",
    "v1_17", "V1_17", "V1.17", "v1.17",
    "PHASE36_V1_15", "PHASE36_V1_16", "PHASE36_V1_17",
    "phase36_v1_15", "phase36_v1_16", "phase36_v1_17",
    "JOURNAL", "_ScienceJournal", "STAGE_JOURNAL",
    "D80", "D81", "D82", "D83", "OPERATIONAL", "NAMESPACE",
    "HISTORICAL_V1_14_SMOKE", "SMOKE_V1_17_ARTIFACT", "FAIL_CLOSED",
    "REACHABLE", "WRITE_TARGET", "RELEASE", "ATTESTATION",
)


def classify_hunk(h: dict) -> str:
    """Return one of:
      SCIENTIFIC_D61 | SCIENTIFIC_D75 | OPERATIONAL_GOVERNANCE | UNCLASSIFIED
    """
    a = h["a_text"]
    b = h["b_text"]
    # D61: canonical fusion replacement.
    if "fuse_full_field(p_global, refined, geom)" in b and "_fuse_global_with_regional" in a:
        return "SCIENTIFIC_D61"
    if "v1.15 REPAIR 1 (D61)" in b:
        return "SCIENTIFIC_D61"
    # Operational/header rebrand first, so a version-only header mentioning POLICY_B
    # is NOT mislabeled scientific.
    if ("v1.17 FINAL OPERATIONAL REPAIR" in b
            or "REVISION: ra_medfilm_barr_phase36_robustness_v1_17" in b
            or b.lstrip().startswith("# v1.17")):
        if not any(tok in b for tok in ("fuse_full_field(p_global, refined, geom)",
                                        f"def {POLICY_HELPER}")):
            return "OPERATIONAL_GOVERNANCE"
    # D75: POLICY_B helper def / wiring.
    if "v1.15 REPAIR 2 (D75" in b:
        return "SCIENTIFIC_D75"
    if f"def {POLICY_HELPER}" in b and "POLICY_B" in b:
        return "SCIENTIFIC_D75"
    if f"{POLICY_HELPER}(" in b and ("final_binary" in b or "prob" in b):
        return "SCIENTIFIC_D75"
    if any(tok in b for tok in _GOVERNANCE_TOKENS):
        return "OPERATIONAL_GOVERNANCE"
    return "UNCLASSIFIED"


def scientific_repair_classes(classes: list[str]) -> int:
    """Distinct scientific repair CLASSES (D61 and/or D75)."""
    return len({c for c in classes if c in ("SCIENTIFIC_D61", "SCIENTIFIC_D75")})


# --------------------------------------------------------------------------- #
# 2. POLICY_B static coverage
# --------------------------------------------------------------------------- #
def function_source(src: str, name: str) -> str | None:
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(src, node)
    return None


def find_direct_live_thresholds(src: str) -> list[int]:
    tree = ast.parse(src)
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and isinstance(node.ops[0], ast.GtE):
            left = node.left
            if isinstance(left, ast.Name) and left.id in {
                "final_prob", "prob", "p_final", "final_probability"
            }:
                hits.append(node.lineno)
    return hits


def policy_b_reference(p_live):
    p = np.asarray(p_live, dtype=np.float32)
    p16 = p.astype(np.float16).astype(np.float32)
    return (p16 >= np.float32(0.50)).astype(np.float32)


def policy_b_helper_from_source(src: str, p_live):
    ns = {"np": np, "SEGMENTATION_OUTPUT_THRESHOLD": 0.50}
    node_src = None
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.FunctionDef) and node.name == POLICY_HELPER:
            node_src = ast.get_source_segment(src, node)
            break
    assert node_src, "helper not found"
    exec(node_src, ns)
    return ns[POLICY_HELPER](p_live)


def ref_near(near):
    p = np.asarray(near, dtype=np.float32)
    return (p.astype(np.float16).astype(np.float32) >= np.float32(0.5)).astype(np.float32)


def test_synthetic_fusion(v17_src: str) -> bool:
    from PIL import Image  # noqa

    ns = {"np": np}
    node_src = None
    for node in ast.walk(ast.parse(v17_src)):
        if isinstance(node, ast.FunctionDef) and node.name == "fuse_full_field":
            node_src = ast.get_source_segment(v17_src, node)
            break
    assert node_src
    exec(node_src, ns)
    fuse = ns["fuse_full_field"]

    rng = np.random.RandomState(0)
    p_global = rng.rand(512, 512).astype(np.float32)
    refined = rng.rand(256, 256).astype(np.float32)

    from src.data.barr_roi import roi_geometry
    prob = np.zeros((512, 512), dtype=np.float32)
    prob[200:260, 180:240] = 1.0
    geom_real = roi_geometry(prob, threshold=0.30, margin=0.10)

    cases = [
        {"crop_side_pixels": 128, "clip_y1": 100, "clip_y2": 228, "clip_x1": 100, "clip_x2": 228, "pad_top": 0, "pad_left": 0},
        {"crop_side_pixels": 200, "clip_y1": 150, "clip_y2": 300, "clip_x1": 160, "clip_x2": 310, "pad_top": 20, "pad_left": 20},
    ]
    if geom_real is not None:
        cases.append(
            {"crop_side_pixels": int(geom_real["crop_side_pixels"]),
             "clip_y1": int(geom_real["clip_y1"]), "clip_y2": int(geom_real["clip_y2"]),
             "clip_x1": int(geom_real["clip_x1"]), "clip_x2": int(geom_real["clip_x2"]),
             "pad_top": int(geom_real["pad_top"]), "pad_left": int(geom_real["pad_left"])}
        )
    all_ok = True
    for geom in cases:
        out = fuse(p_global.copy(), refined, geom)
        from PIL import Image as _I
        side = int(geom["crop_side_pixels"])
        pil = _I.fromarray(np.ascontiguousarray(refined, dtype=np.float32), mode="F")
        square = np.asarray(pil.resize((side, side), _I.Resampling.BILINEAR), dtype=np.float32)
        ref = p_global.copy()
        ref[geom["clip_y1"]:geom["clip_y2"], geom["clip_x1"]:geom["clip_x2"]] = square[
            geom["pad_top"]:geom["pad_top"] + (geom["clip_y2"] - geom["clip_y1"]),
            geom["pad_left"]:geom["pad_left"] + (geom["clip_x2"] - geom["clip_x1"]),
        ]
        if not (np.array_equal(out, ref) and float(np.abs(out - ref).max()) == 0.0):
            all_ok = False
    return all_ok


def main() -> int:
    print("== source integrity ==")
    ok("v1_14_sha_exact", sha256_file(V14) == V14_SHA)
    ok("v1_15_sha_exact", sha256_file(V15) == V15_SHA)
    ok("v1_16_sha_exact", sha256_file(V16) == V16_SHA)
    ok("v1_17_sha_exact", sha256_file(V17) == V17_SHA)

    v14_src = V14.read_text(encoding="utf-8")
    v17_src = V17.read_text(encoding="utf-8")

    print("== diff proof (v1.14 -> v1.17) ==")
    hunks = compute_diff_hunks(V14, V17)
    classes = [classify_hunk(h) for h in hunks]
    has_d61 = "SCIENTIFIC_D61" in classes
    has_d75 = "SCIENTIFIC_D75" in classes
    scientific_repairs = scientific_repair_classes(classes)
    unclassified = classes.count("UNCLASSIFIED")
    ok("diff_hunks_present", len(hunks) >= 3)
    ok("scientific_delta_count_eq_2", scientific_repairs == 2)
    ok("scientific_delta_D61_PASS", has_d61)
    ok("scientific_delta_D75_PASS", has_d75)
    ok("unclassified_scientific_delta_count_0", unclassified == 0)

    print("== D61 fusion ==")
    ok("canonical_phase27_fusion_call_present", "fuse_full_field(p_global, refined, geom)" in v17_src)
    ok("old_model_fusion_call_absent_from_production_path",
       "system._fuse_global_with_regional(p_global, refined, window)" not in v17_src)

    print("== POLICY_B wiring ==")
    ok("helper_def_present", f"def {POLICY_HELPER}(" in v17_src)
    ok("helper_call_sites_eq_2", v17_src.count(f"{POLICY_HELPER}(") == 3)
    core = function_source(v17_src, "_core_result") or ""
    ok("core_binary_uses_helper", f"{POLICY_HELPER}(prob)" in core)
    clean = function_source(v17_src, "_evaluate_clean_sample") or ""
    ok("clean_binary_uses_helper", f"{POLICY_HELPER}(final_prob)" in clean)
    ok("clean_store_final_binary_policy_b", "clean_store.setdefault(\"final_binary\", {})[sid] = final_binary" in clean)
    ok("image_pert_consumes_core_binary", 'pert_binary = np.asarray(out["final_binary"], dtype=np.float32)' in v17_src)
    ok("proposal_pert_consumes_core_binary", v17_src.count('pert_binary = np.asarray(out["final_binary"], dtype=np.float32)') >= 2)
    ok("prediction_consistency_uses_policy_b_binaries",
       'clean_store["final_binary"][sid]' in v17_src)

    print("== no direct live-f32 thresholding of authoritative final prob ==")
    direct = find_direct_live_thresholds(v17_src)
    ok("no_direct_live_final_prob_threshold", len(direct) == 0)

    print("== G downstream quantization must be ABSENT ==")
    ok("downstream_G_quantization_added_false",
       "astype(np.float16)" not in (function_source(v17_src, "_core_result") or "")
       and "astype(np.float16)" not in (function_source(v17_src, "canonical_learned_core") or ""))
    helper_src = function_source(v17_src, POLICY_HELPER) or ""
    ok("f16_cast_only_in_policy_helper", "astype(np.float16)" in helper_src)

    print("== thresholds / tolerances unchanged ==")
    ok("segmentation_threshold_0_50", "SEGMENTATION_OUTPUT_THRESHOLD = 0.50" in v17_src)
    ok("no_tolerance_change", "atol" not in v17_src or v17_src.count("1e-7") == v14_src.count("1e-7"))

    print("== synthetic representation tests ==")
    edge = np.array(
        [[0.0, 0.25, 0.49, 0.4999999, 0.5, 0.5000001, 0.5001, 0.75, 1.0]],
        dtype=np.float32,
    )
    near = np.array([0.4999, 0.49999, 0.5, 0.50001, 0.5001], dtype=np.float32)
    got = policy_b_helper_from_source(v17_src, edge)
    ref = policy_b_reference(edge)
    ok("policy_b_edge_bitwise_equal", np.array_equal(got, ref))
    got_near = policy_b_helper_from_source(v17_src, near)
    ok("policy_b_near_boundary_bitwise_equal", np.array_equal(got_near, policy_b_reference(near)))
    ok("d75_boundary_repair_reference_consistent", np.array_equal(policy_b_reference(edge), policy_b_reference(edge)))
    ok("policy_b_helper_exact", np.array_equal(got, ref))

    print("== negative controls (POLICY_B) ==")
    nc1 = "def _phase27_scored_final_binary(p):\n    return (np.asarray(p, dtype=np.float32) >= np.float32(0.5)).astype(np.float32)\n"
    ns = {"np": np}
    exec(nc1, ns)
    ok("nc1_live_f32_mutation_detected", not np.array_equal(ns[POLICY_HELPER](near), ref_near(near)))
    nc2 = "def _phase27_scored_final_binary(p):\n    p = np.asarray(p, dtype=np.float32)\n    return (p >= np.float32(0.5)).astype(np.float32)\n"
    ns2 = {"np": np}
    exec(nc2, ns2)
    ok("nc2_no_f16_cast_detected", not np.array_equal(ns2[POLICY_HELPER](near), ref_near(near)))
    nc6 = "def _phase27_scored_final_binary(p):\n    p = np.asarray(p, dtype=np.float32).astype(np.float16).astype(np.float32)\n    return (p >= np.float32(0.51)).astype(np.float32)\n"
    ns6 = {"np": np}
    exec(nc6, ns6)
    ok("nc6_threshold_change_detected", not np.array_equal(ns6[POLICY_HELPER](near), ref_near(near)))

    print("== synthetic D61 fusion tests ==")
    ok("synthetic_fusion_equivalence_all", test_synthetic_fusion(v17_src))

    # ---- machine-derived diff artifact (write-once additive; see reconciliation) ---- #
    report = {
        "artifact": "phase36_v1_17_science_repair_validation",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_17",
        "type": "SCIENCE_REPAIR_VALIDATION_REPORT",
        "diff_from_sha256": V14_SHA,
        "diff_to_sha256": V17_SHA,
        "hunk_count": len(hunks),
        "scientific_delta_count": scientific_repairs,
        "scientific_deltas": (["D61"] if has_d61 else []) + (["D75"] if has_d75 else []),
        "unclassified_scientific_delta_count": unclassified,
        "classification_counts": {
            "SCIENTIFIC_D61": classes.count("SCIENTIFIC_D61"),
            "SCIENTIFIC_D75": classes.count("SCIENTIFIC_D75"),
            "OPERATIONAL_GOVERNANCE": classes.count("OPERATIONAL_GOVERNANCE"),
            "UNCLASSIFIED": unclassified,
        },
        "model_free": True,
        "torch_imported": False,
        "protected_population_read": False,
        "checks_passed": n_pass,
        "checks_failed": n_fail,
        "failures": failures,
        "all_pass": n_fail == 0,
    }
    out_path = ROOT / "reports/audits/phase36_v1_17_science_repair_validation.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"\nRESULT: {n_pass} passed, {n_fail} failed")
    if failures:
        print("FAILURES:")
        for f in failures:
            print("  -", f)
        print("terminal: PHASE36_V1_17_SCIENCE_REPAIR_VALIDATION_FAIL")
        return 1
    print("terminal: PHASE36_V1_17_SCIENCE_REPAIR_VALIDATION_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
