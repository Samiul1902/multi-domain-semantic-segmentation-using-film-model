#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.16 — NEGATIVE CONTROLS.

REBASED FROM v1.15 (D80 OPERATIONAL/GOVERNANCE REBASE).

Additive over all carried controls.  Every control here targets a SPECIFIC v1.16
repair (scientific repairs D61/D75 preserved VERBATIM + NEW operational repairs
D80-A..H):

  D61 CANONICAL PHASE27 ACCEPT FUSION (PRESERVED)
    NC_D61_1  restore the old pad-unaware ``system._fuse_global_with_regional``
              call -> canonical-call detector MUST fail.
    NC_D61_2  change the fusion geometry source (window instead of geom) ->
              same-geometry detector MUST fail.

  D75 POLICY_B AUTHORITATIVE SEGMENTATION REPRESENTATION (PRESERVED; 6 mutations)
    NC_D75_1..NC_D75_6  as in v1.15.

  G DOWNSTREAM QUANTIZATION ABSENCE (PRESERVED)
    NC_G_1    introduce an f16 cast into canonical_learned_core.

  D80 OPERATIONAL/GOVERNANCE REBASE (NEW)
    NC_D80_A  launcher dispatch omits ``--mode science`` -> detector MUST fail.
    NC_D80_B  execution science namespace reverted to v1.14 -> detector fails.
    NC_D80_C  launch authority token reverted to v1.14 -> detector fails.
    NC_D80_D  operator gate reverted to C.GATE_ENV (v1.14) -> detector fails.
    NC_D80_E  runtime manifest path reverted to v1.14 -> detector fails.
    NC_D80_F  release revision reverted to v1.14 -> detector fails.
    NC_D80_G  stage-journal module removed -> detector fails.
    NC_D80_H  launcher pin removed / mismatched -> detector fails.

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

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_16.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_16.py"
SUPERVISOR = ROOT / "scripts/analysis/supervise_phase36_v1_16.py"

FROZEN_V1_16_EXEC_SHA = "a96b74caa4587aa9d2f83b79ed39c13075a88086109e31d991695a75ec4abab9"
REVISION = "ra_medfilm_barr_phase36_robustness_v1_16"

records = []


def rec(nc_id, name, detector_rejects_mutant, detail=None):
    records.append({"id": nc_id, "control": name,
                    "mutant_rejected": bool(detector_rejects_mutant),
                    "passed": bool(detector_rejects_mutant), "detail": detail})


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# --------------------------------------------------------------------------- #
# Faithful standalone detectors — D61 / D75 / G (preserved)
# --------------------------------------------------------------------------- #
def detect_canonical_fusion(src: str) -> bool:
    return ("fuse_full_field(p_global, refined, geom)" in src
            and "system._fuse_global_with_regional(p_global, refined, window)" not in src)


def detect_fusion_geom_source(src: str) -> bool:
    return "fuse_full_field(p_global, refined, geom)" in src


def policy_b_reference(p_live):
    p = np.asarray(p_live, dtype=np.float32)
    return (p.astype(np.float16).astype(np.float32) >= np.float32(0.50)).astype(np.float32)


def detect_policy_b_helper(helper_src: str, probe: np.ndarray) -> bool:
    structurally_ok = (
        "astype(np.float16)" in helper_src
        and helper_src.count("astype(np.float32)") >= 2
        and "np.float32(SEGMENTATION_OUTPUT_THRESHOLD)" in helper_src
    )
    if not structurally_ok:
        return False
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
    seg = src.split("def canonical_learned_core")[1].split("\ndef ")[0]
    return "astype(np.float16)" not in seg


# --------------------------------------------------------------------------- #
# Faithful standalone detectors — D80 operational (NEW)
# --------------------------------------------------------------------------- #
def detect_launcher_mode_science(lsrc: str) -> bool:
    """D80-A: the launcher dispatch command MUST include --mode science."""
    return ('DISPATCH_MODE_ARGS = ["--mode", "science"]' in lsrc
            and "list(DISPATCH_MODE_ARGS)" in lsrc)


def detect_execution_namespace_v1_16(src: str) -> bool:
    """D80-B: v1.16 science namespace; no v1.14 science-path reuse."""
    return ("phase36_robustness_scientific_result_v1_16.json" in src
            and "phase36_robustness_science_start_v1_16.json" in src
            and "phase36_robustness_science_failure_v1_16.json" in src
            and "phase36_robustness_science_start_v1_14.json" not in src)


def detect_launch_authority_token_v1_16(src: str) -> bool:
    return 'LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_16_LAUNCH_AUTHORITY"' in src


def detect_explicit_gates(src: str) -> bool:
    """D80-D: explicit v1.16 operator gates; no v1.14 gate residue."""
    return ("PHASE36_V1_16_EXECUTE" in src and "PHASE36_V1_16_SMOKE_EXECUTE" in src
            and "PHASE36_V1_14_EXECUTE" not in src
            and "PHASE36_V1_14_SMOKE_EXECUTE" not in src)


def detect_runtime_manifest_v1_16(src: str) -> bool:
    return ("phase36_v1_16_runtime_source_integrity_manifest.json" in src
            and "phase36_v1_14_runtime_source_integrity_manifest.json" not in src)


def detect_release_revision_v1_16(src: str) -> bool:
    return ("ra_medfilm_barr_phase36_robustness_v1_16" in src
            and "ra_medfilm_barr_phase36_robustness_v1_14" not in src)


def detect_stage_journal(src: str) -> bool:
    return ("V1_16_JOURNAL_STAGES" in src and "_ScienceJournal" in src
            and "journal=_ScienceJournal(" in src
            and "_run_science_with_durable_evidence(journal=" in src
            and "phase36_robustness_science_v1_16_journal" in src)


def detect_launcher_pin(lsrc: str) -> bool:
    return (f'V1_16_SOURCE_SHA = "{FROZEN_V1_16_EXEC_SHA}"' in lsrc)


def detect_supervisor_pin(ssrc: str) -> bool:
    return ("launcher_sha_pin_enforced" in ssrc
            and "FAIL_CLOSED__LAUNCHER_SHA_MISMATCH" in ssrc)


# --------------------------------------------------------------------------- #
# Load canonical sources
# --------------------------------------------------------------------------- #
SRC = EXEC.read_text(encoding="utf-8")
LSRC = LAUNCHER.read_text(encoding="utf-8")
SSRC = SUPERVISOR.read_text(encoding="utf-8")

HELPER_SRC = (
    "def _phase27_scored_final_binary(p_final_live):\n"
    "    p = np.asarray(p_final_live, dtype=np.float32)\n"
    "    p_f16 = p.astype(np.float16)\n"
    "    p_scored = p_f16.astype(np.float32)\n"
    "    return (p_scored >= np.float32(SEGMENTATION_OUTPUT_THRESHOLD)).astype(np.float32)\n"
)
probe = np.array([0.0, 0.49, 0.49999, 0.5, 0.50001, 0.5001, 1.0], dtype=np.float32)

# ---- source identity ---- #
rec("NC_SRC", "v1_16_source_sha_frozen", _sha(EXEC) == FROZEN_V1_16_EXEC_SHA,
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

# ---- D80 operational (NEW) ---- #
# NC_D80_A: launcher dispatch omits --mode science.
rec("NC_D80_A", "launcher_dispatch_mode_science_omitted_detected",
    not detect_launcher_mode_science(
        LSRC.replace('DISPATCH_MODE_ARGS = ["--mode", "science"]',
                     'DISPATCH_MODE_ARGS = []')),
    "mode args emptied -> detector returns False (rejected)")

# NC_D80_B: execution science namespace reverted to v1.14.
rec("NC_D80_B", "execution_science_namespace_v1_14_reverted_detected",
    not detect_execution_namespace_v1_16(
        SRC.replace("phase36_robustness_science_start_v1_16.json",
                    "phase36_robustness_science_start_v1_14.json")),
    "start marker namespace reverted -> detector returns False (rejected)")

# NC_D80_C: launch authority token reverted to v1.14.
rec("NC_D80_C", "launch_authority_token_v1_14_reverted_detected",
    not detect_launch_authority_token_v1_16(
        SRC.replace('LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_16_LAUNCH_AUTHORITY"',
                    'LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_14_LAUNCH_AUTHORITY"')),
    "authority token reverted -> detector returns False (rejected)")

# NC_D80_D: operator gate reverted to a v1.14 literal.
rec("NC_D80_D", "operator_gate_v1_14_reverted_detected",
    not detect_explicit_gates(
        SRC.replace("PHASE36_V1_16_EXECUTE", "PHASE36_V1_14_EXECUTE")),
    "science gate reverted -> detector returns False (rejected)")

# NC_D80_E: runtime manifest path reverted to v1.14.
rec("NC_D80_E", "runtime_manifest_v1_14_reverted_detected",
    not detect_runtime_manifest_v1_16(
        SRC.replace("phase36_v1_16_runtime_source_integrity_manifest.json",
                    "phase36_v1_14_runtime_source_integrity_manifest.json")),
    "manifest path reverted -> detector returns False (rejected)")

# NC_D80_F: release revision reverted to v1.14.
rec("NC_D80_F", "release_revision_v1_14_reverted_detected",
    not detect_release_revision_v1_16(
        SRC.replace("ra_medfilm_barr_phase36_robustness_v1_16",
                    "ra_medfilm_barr_phase36_robustness_v1_14")),
    "release revision reverted -> detector returns False (rejected)")

# NC_D80_G: stage-journal module removed.
rec("NC_D80_G", "stage_journal_module_removed_detected",
    not detect_stage_journal(
        SRC.replace("V1_16_JOURNAL_STAGES", "V1_16_JOURNAL_STAGES_REMOVED")
           .replace("_ScienceJournal", "_JournalRemoved")),
    "journal module removed -> detector returns False (rejected)")

# NC_D80_H: launcher pin removed.
rec("NC_D80_H_launcher", "launcher_exact_sha_pin_removed_detected",
    not detect_launcher_pin(LSRC.replace(FROZEN_V1_16_EXEC_SHA, "0" * 64)),
    "launcher pin mismatched -> detector returns False (rejected)")

rec("NC_D80_H_supervisor", "supervisor_launcher_pin_enforcement_removed_detected",
    not detect_supervisor_pin(SSRC.replace("FAIL_CLOSED__LAUNCHER_SHA_MISMATCH",
                                           "SOME_OTHER_STATUS")),
    "supervisor fail-closed pin removed -> detector returns False (rejected)")

# --------------------------------------------------------------------------- #
n_pass = sum(1 for r in records if r["passed"])
n_total = len(records)
report = {
    "artifact": "phase36_robustness_negative_controls_v1_16",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": REVISION,
    "type": "NEGATIVE_CONTROL_REPORT",
    "in_memory_mutants_only": True,
    "canonical_files_modified": False,
    "torch_imported": False,
    "protected_population_read": False,
    "subject_execution_sha256": _sha(EXEC),
    "subject_launcher_sha256": _sha(LAUNCHER),
    "subject_supervisor_sha256": _sha(SUPERVISOR),
    "controls_total": n_total,
    "controls_passed": n_pass,
    "controls_failed": n_total - n_pass,
    "all_pass": n_pass == n_total,
    "records": records,
}
out_path = ROOT / "reports/audits/phase36_v1_16_negative_controls.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(report, indent=1), encoding="utf-8")
for r in records:
    if not r["passed"]:
        print(f"FAIL {r['id']} :: {r['control']}")
print(f"NEGATIVE CONTROLS v1.16: {n_pass}/{n_total} pass")
print(f"terminal: {'PHASE36_V1_16_NEGATIVE_CONTROLS_PASS' if n_pass == n_total else 'PHASE36_V1_16_NEGATIVE_CONTROLS_FAIL'}")
raise SystemExit(0 if n_pass == n_total else 1)
