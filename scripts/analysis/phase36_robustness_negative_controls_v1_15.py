#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.15 — NEGATIVE CONTROLS.

Additive over all carried controls.  Every control here targets a SPECIFIC v1.15
scientific repair:

  D61 CANONICAL PHASE27 ACCEPT FUSION
    NC_D61_1  restore the old pad-unaware ``system._fuse_global_with_regional``
              call -> canonical-call detector MUST fail.
    NC_D61_2  change the fusion geometry source (window instead of geom) ->
              same-geometry detector MUST fail.

  D75 POLICY_B AUTHORITATIVE SEGMENTATION REPRESENTATION (6 mandated mutations)
    NC_D75_1  helper thresholds LIVE f32 directly (no f16 round-trip).
    NC_D75_2  helper drops the f16 cast entirely.
    NC_D75_3  helper drops the f16->f32 cast-back.
    NC_D75_4  helper threshold changed (0.51).
    NC_D75_5  helper omitted from the core binary producer.
    NC_D75_6  helper omitted from the clean binary producer.

  G DOWNSTREAM QUANTIZATION ABSENCE
    NC_G_1    introduce an f16 cast into canonical_learned_core -> detector fails.

Each control pairs a FAITHFUL STANDALONE re-implementation of the corresponding
detector with an IN-MEMORY mutant that a CORRECT detector MUST reject.  Canonical
files on disk are NEVER modified.

NO torch load.  NO model.  NO checkpoint.  NO forward.  NO smoke.  NO science.
NO VAL image / GT read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_15.py"
FROZEN_V1_15_EXEC_SHA = "b194ad28345ea8b268748be383ca98b936cb051d85854666e3141250f3eae002"

REVISION = "ra_medfilm_barr_phase36_robustness_v1_15"

records = []


def rec(nc_id, name, detector_rejects_mutant, detail=None):
    records.append({"id": nc_id, "control": name,
                    "mutant_rejected": bool(detector_rejects_mutant),
                    "passed": bool(detector_rejects_mutant), "detail": detail})


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# Faithful standalone detectors
# --------------------------------------------------------------------------- #
def detect_canonical_fusion(src: str) -> bool:
    """True iff the canonical pad-aware fusion call is present AND the old
    pad-unaware call is absent."""
    return ("fuse_full_field(p_global, refined, geom)" in src
            and "system._fuse_global_with_regional(p_global, refined, window)" not in src)


def detect_fusion_geom_source(src: str) -> bool:
    return "fuse_full_field(p_global, refined, geom)" in src


def policy_b_reference(p_live):
    p = np.asarray(p_live, dtype=np.float32)
    return (p.astype(np.float16).astype(np.float32) >= np.float32(0.50)).astype(np.float32)


def detect_policy_b_helper(helper_src: str, probe: np.ndarray) -> bool:
    """True iff the helper implements the EXACT f32->f16->f32->>=0.50 policy.

    Two independent requirements:
      (1) VALUE exactness on the probe (bit-for-bit against the reference), AND
      (2) STRUCTURAL exactness of the representation pipeline: the helper must
          contain an ``astype(np.float16)`` AND a subsequent ``astype(np.float32)``
          cast-back, and threshold at ``np.float32(SEGMENTATION_OUTPUT_THRESHOLD)``.
    Requirement (2) is what makes the dropped-cast-back mutant detectable, since
    value equality alone is insensitive to it on finite probes.
    """
    # (2) structural exactness (source analysis)
    structurally_ok = (
        "astype(np.float16)" in helper_src
        and helper_src.count("astype(np.float32)") >= 2
        and "np.float32(SEGMENTATION_OUTPUT_THRESHOLD)" in helper_src
    )
    if not structurally_ok:
        return False
    # (1) value exactness
    ns = {"np": np, "SEGMENTATION_OUTPUT_THRESHOLD": 0.50}
    try:
        exec(helper_src, ns)
    except Exception:
        return False
    fn = ns.get("_phase27_scored_final_binary")
    if fn is None:
        return False
    try:
        got = fn(probe)
    except Exception:
        return False
    return np.array_equal(got, policy_b_reference(probe))


def detect_helper_wired(src: str, fn_anchor: str) -> bool:
    return f"_phase27_scored_final_binary(" in fn_anchor


def detect_no_downstream_G_quantization(src: str) -> bool:
    """core learned path must not cast to float16."""
    # crude: no astype(np.float16) between canonical_learned_core def and next def
    seg = src.split("def canonical_learned_core")[1].split("\ndef ")[0]
    return "astype(np.float16)" not in seg


# --------------------------------------------------------------------------- #
# Load canonical source + helper source
# --------------------------------------------------------------------------- #
SRC = EXEC.read_text(encoding="utf-8")
HELPER_SRC = (
    "def _phase27_scored_final_binary(p_final_live):\n"
    "    p = np.asarray(p_final_live, dtype=np.float32)\n"
    "    p_f16 = p.astype(np.float16)\n"
    "    p_scored = p_f16.astype(np.float32)\n"
    "    return (p_scored >= np.float32(SEGMENTATION_OUTPUT_THRESHOLD)).astype(np.float32)\n"
)
probe = np.array([0.0, 0.49, 0.49999, 0.5, 0.50001, 0.5001, 1.0], dtype=np.float32)

# ---- source identity ---- #
rec("NC_SRC", "v1_15_source_sha_frozen", _sha(EXEC) == FROZEN_V1_15_EXEC_SHA,
    {"sha256": _sha(EXEC)})

# ---- D61 ---- #
rec("NC_D61_1", "restore_old_pad_unaware_fusion_detected",
    not detect_canonical_fusion(
        SRC.replace("fuse_full_field(p_global, refined, geom)",
                    "system._fuse_global_with_regional(p_global, refined, window)")),
    "old call restored -> detector returns False (rejected)")

rec("NC_D61_2", "change_fusion_geom_source_detected",
    not detect_fusion_geom_source(
        SRC.replace("fuse_full_field(p_global, refined, geom)",
                    "fuse_full_field(p_global, refined, window)")),
    "geom replaced by window -> detector returns False (rejected)")

# ---- D75 (6) ---- #
nc_d75_1 = HELPER_SRC.replace(
    "    p_f16 = p.astype(np.float16)\n    p_scored = p_f16.astype(np.float32)\n",
    "    p_scored = p\n")
rec("NC_D75_1", "helper_thresholds_live_f32_detected",
    not detect_policy_b_helper(nc_d75_1, probe), "no f16 round-trip -> rejected")

nc_d75_2 = HELPER_SRC.replace("    p_f16 = p.astype(np.float16)\n", "    p_f16 = p\n")
rec("NC_D75_2", "helper_drops_f16_cast_detected",
    not detect_policy_b_helper(nc_d75_2, probe), "f16 cast removed -> rejected")

nc_d75_3 = HELPER_SRC.replace("    p_scored = p_f16.astype(np.float32)\n", "    p_scored = p_f16\n")
rec("NC_D75_3", "helper_drops_cast_back_detected",
    not detect_policy_b_helper(nc_d75_3, probe), "f16->f32 cast-back removed -> rejected")

nc_d75_4 = HELPER_SRC.replace("np.float32(SEGMENTATION_OUTPUT_THRESHOLD)", "np.float32(0.51)")
rec("NC_D75_4", "helper_threshold_change_detected",
    not detect_policy_b_helper(nc_d75_4, probe), "threshold 0.51 -> rejected")

# omit helper from core producer
core_anchor = SRC.split("def _core_result")[1].split("\ndef ")[0]
core_missing = core_anchor.replace("_phase27_scored_final_binary(prob)", "prob >= 0.50")
rec("NC_D75_5", "helper_omitted_from_core_detected",
    not detect_helper_wired(SRC, core_missing), "core wiring removed -> rejected")

clean_anchor = SRC.split("def _evaluate_clean_sample")[1].split("\ndef ")[0]
clean_missing = clean_anchor.replace("_phase27_scored_final_binary(final_prob)", "final_prob >= 0.50")
rec("NC_D75_6", "helper_omitted_from_clean_detected",
    not detect_helper_wired(SRC, clean_missing), "clean wiring removed -> rejected")

# ---- G downstream quantization absence ---- #
g_mutant = SRC.replace(
    "def canonical_learned_core(ctx, image_b, task_id, *,",
    "def canonical_learned_core(ctx, image_b, task_id, *,\n    _mutant=np.float32(1.0).astype(np.float16),")
rec("NC_G_1", "downstream_G_quantization_introduced_detected",
    not detect_no_downstream_G_quantization(g_mutant), "f16 cast injected -> rejected")

# --------------------------------------------------------------------------- #
n_pass = sum(1 for r in records if r["passed"])
n_total = len(records)
report = {
    "artifact": "phase36_robustness_negative_controls_v1_15",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": REVISION,
    "type": "NEGATIVE_CONTROL_REPORT",
    "in_memory_mutants_only": True,
    "canonical_files_modified": False,
    "torch_imported": False,
    "protected_population_read": False,
    "subject_execution_sha256": _sha(EXEC),
    "controls_total": n_total,
    "controls_passed": n_pass,
    "controls_failed": n_total - n_pass,
    "all_pass": n_pass == n_total,
    "records": records,
}
out_path = ROOT / "reports/audits/phase36_v1_15_negative_controls.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(report, indent=1), encoding="utf-8")
for r in records:
    if not r["passed"]:
        print(f"FAIL {r['id']} :: {r['control']}")
print(f"NEGATIVE CONTROLS v1.15: {n_pass}/{n_total} pass")
print(f"terminal: {'PHASE36_V1_15_NEGATIVE_CONTROLS_PASS' if n_pass == n_total else 'PHASE36_V1_15_NEGATIVE_CONTROLS_FAIL'}")
raise SystemExit(0 if n_pass == n_total else 1)
