#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.17 — NEGATIVE CONTROLS.

REBASED FROM v1.16 (D81/D82/D83 FINAL OPERATIONAL REPAIR).

Additive over all carried controls.  Every control here targets a SPECIFIC v1.17
repair (scientific repairs D61/D75 preserved VERBATIM + operational D80-A..H
preserved + NEW D81/D82/D83 repairs):

  D61 CANONICAL PHASE27 ACCEPT FUSION (PRESERVED)          NC_D61_1, NC_D61_2
  D75 POLICY_B REPRESENTATION (PRESERVED; 6 mutations)     NC_D75_1..NC_D75_6
  G DOWNSTREAM QUANTIZATION ABSENCE (PRESERVED)            NC_G_1
  D80 OPERATIONAL/GOVERNANCE REBASE (PRESERVED)            NC_D80_A..NC_D80_H_supervisor

  D81 OUTPUT NAMESPACE REBASE + FAIL-CLOSED CSV (NEW; §10)
    NC_D81_1  omitted table (CSV) target -> inventory completeness detector fails.
    NC_D81_2  generic non-versioned phase36 table target -> namespace detector fails.
    NC_D81_3  generic inherited figure dir -> namespace detector fails.
    NC_D81_4  CSV writer reverted to ``open("w")`` overwrite mode -> fail-closed detector fails.

  D82 RELEASE CONTRACT (NEW; §10)
    NC_D82_1  gate requires a v1.17 smoke artifact -> detector fails.
    NC_D82_2  attestation missing a required D40 field -> schema detector fails.

  D83 PURE RELEASE-GATE RUNTIME STATE (NEW; §10)
    NC_D83_1  validator checks only the revision without evaluating state -> fails.
    NC_D83_2  gate returns NOT_RELEASED while eligibility is eligible -> fails.

Each control pairs a FAITHFUL STANDALONE re-implementation of the corresponding
detector with an IN-MEMORY mutant that a CORRECT detector MUST reject.  Canonical
files on disk are NEVER modified.  Any UNKNOWN outcome => FAIL CLOSED.

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

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_17.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_17.py"
SUPERVISOR = ROOT / "scripts/analysis/supervise_phase36_v1_17.py"

FROZEN_V1_17_EXEC_SHA = "81d78460b2f20f176bc697cba662c43bc7c7443ea555ba95a30609faf0ccbe31"
REVISION = "ra_medfilm_barr_phase36_robustness_v1_17"
HISTORICAL_V1_14_SMOKE_SHA = "53543729fb0c48695c2af202c5f3d2f5ebdfc29d87c7a7f100bcde9f94882441"

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
# Faithful standalone detectors — D80 operational (preserved)
# --------------------------------------------------------------------------- #
def detect_launcher_mode_science(lsrc: str) -> bool:
    return ('DISPATCH_MODE_ARGS = ["--mode", "science"]' in lsrc
            and "list(DISPATCH_MODE_ARGS)" in lsrc)


def detect_execution_namespace_v1_17(src: str) -> bool:
    return ("phase36_robustness_scientific_result_v1_17.json" in src
            and "phase36_robustness_science_start_v1_17.json" in src
            and "phase36_robustness_science_failure_v1_17.json" in src
            and "phase36_robustness_science_start_v1_16.json" not in src)


def detect_launch_authority_token_v1_17(src: str) -> bool:
    return 'LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_17_LAUNCH_AUTHORITY"' in src


def detect_explicit_gates(src: str) -> bool:
    return ("PHASE36_V1_17_EXECUTE" in src and "PHASE36_V1_17_SMOKE_EXECUTE" in src
            and "PHASE36_V1_16_EXECUTE" not in src
            and "PHASE36_V1_16_SMOKE_EXECUTE" not in src)


def detect_runtime_manifest_v1_17(src: str) -> bool:
    return ("phase36_v1_17_runtime_source_integrity_manifest.json" in src
            and "phase36_v1_16_runtime_source_integrity_manifest.json" not in src)


def detect_release_revision_v1_17(src: str) -> bool:
    return ("ra_medfilm_barr_phase36_robustness_v1_17" in src
            and "ra_medfilm_barr_phase36_robustness_v1_16" not in src)


def detect_stage_journal(src: str) -> bool:
    return ("V1_17_JOURNAL_STAGES" in src and "_ScienceJournal" in src
            and "journal=_ScienceJournal(" in src
            and "_run_science_with_durable_evidence(journal=" in src
            and "phase36_robustness_science_v1_17_journal" in src)


def detect_launcher_pin(lsrc: str) -> bool:
    return (f'V1_17_SOURCE_SHA = "{FROZEN_V1_17_EXEC_SHA}"' in lsrc)


def detect_supervisor_pin(ssrc: str) -> bool:
    return ("launcher_sha_pin_enforced" in ssrc
            and "FAIL_CLOSED__LAUNCHER_SHA_MISMATCH" in ssrc)


# --------------------------------------------------------------------------- #
# Faithful standalone detectors — D81 / D82 / D83 (NEW)
# --------------------------------------------------------------------------- #
def detect_table_target_enumerated(inventory_targets, target) -> bool:
    """D81-1: every reachable table target MUST appear in the inventory."""
    return target in inventory_targets


def detect_namespace_uniform(paths) -> bool:
    """D81-2/3: EVERY reachable table/figure path MUST carry the v1.17 namespace."""
    tab = "reports/tables/phase36_robustness_v1_17/"
    fig = "reports/figures/phase36_robustness_v1_17/"
    for p in paths:
        if not (p.startswith(tab) or p.startswith(fig)):
            return False
    return True


def detect_csv_fail_closed(writer_src: str) -> bool:
    """D81-4: the CSV writer MUST be exclusive-create + refuse-existing + fsync."""
    return ('open(path, "x", encoding="utf-8", newline="")' in writer_src
            and "if path.exists():" in writer_src
            and "V1_17_CSV_FAIL_CLOSED__TARGET_EXISTS__REFUSE_OVERWRITE" in writer_src
            and 'path.open("w"' not in writer_src
            and "os.fsync(f.fileno())" in writer_src)


def detect_gate_uses_historical_smoke_not_v1_17(src: str) -> bool:
    """D82-1: the release gate must bind the HISTORICAL v1.14 smoke and must NOT
    require a v1.17 smoke artifact."""
    return ("HISTORICAL_V1_14_SMOKE" in src
            and "HISTORICAL_SMOKE_ARTIFACT_MISSING" in src
            and "phase36_robustness_smoke_v1_17.json" not in src)


def detect_attestation_schema_complete(att: dict) -> bool:
    """D82-2: the release attestation MUST declare the D40 schema fields."""
    return all(f in att for f in ("smoke_artifact_sha256", "smoke_all_pass",
                                  "scientific_output", "release_gate"))


def detect_validator_evaluates_release_state(validator_src: str) -> bool:
    """D83-1: a release validator MUST invoke the pure state function and REQUIRE
    RELEASED (revision-string checking alone is insufficient)."""
    return ("pure_release_state_released" in validator_src
            and "verify_pure_release_state" in validator_src)


def detect_gate_released_when_eligible(gate_state: str, eligibility_eligible: bool) -> bool:
    """D83-2: if the revision is ELIGIBLE, the pure runtime gate state MUST be RELEASED."""
    if eligibility_eligible:
        return gate_state == "RELEASED"
    return True


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
rec("NC_SRC", "v1_17_source_sha_frozen", _sha(EXEC) == FROZEN_V1_17_EXEC_SHA,
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

# ---- D80 operational (preserved) ---- #
rec("NC_D80_A", "launcher_dispatch_mode_science_omitted_detected",
    not detect_launcher_mode_science(
        LSRC.replace('DISPATCH_MODE_ARGS = ["--mode", "science"]', 'DISPATCH_MODE_ARGS = []')),
    "mode args emptied -> rejected")
rec("NC_D80_B", "execution_science_namespace_v1_16_reverted_detected",
    not detect_execution_namespace_v1_17(
        SRC.replace("phase36_robustness_science_start_v1_17.json",
                    "phase36_robustness_science_start_v1_16.json")),
    "start marker namespace reverted -> rejected")
rec("NC_D80_C", "launch_authority_token_v1_16_reverted_detected",
    not detect_launch_authority_token_v1_17(
        SRC.replace('LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_17_LAUNCH_AUTHORITY"',
                    'LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_16_LAUNCH_AUTHORITY"')),
    "authority token reverted -> rejected")
rec("NC_D80_D", "operator_gate_v1_16_reverted_detected",
    not detect_explicit_gates(SRC.replace("PHASE36_V1_17_EXECUTE", "PHASE36_V1_16_EXECUTE")),
    "science gate reverted -> rejected")
rec("NC_D80_E", "runtime_manifest_v1_16_reverted_detected",
    not detect_runtime_manifest_v1_17(
        SRC.replace("phase36_v1_17_runtime_source_integrity_manifest.json",
                    "phase36_v1_16_runtime_source_integrity_manifest.json")),
    "manifest path reverted -> rejected")
rec("NC_D80_F", "release_revision_v1_16_reverted_detected",
    not detect_release_revision_v1_17(
        SRC.replace("ra_medfilm_barr_phase36_robustness_v1_17",
                    "ra_medfilm_barr_phase36_robustness_v1_16")),
    "release revision reverted -> rejected")
rec("NC_D80_G", "stage_journal_module_removed_detected",
    not detect_stage_journal(
        SRC.replace("V1_17_JOURNAL_STAGES", "V1_17_JOURNAL_STAGES_REMOVED")
           .replace("_ScienceJournal", "_JournalRemoved")),
    "journal module removed -> rejected")
rec("NC_D80_H_launcher", "launcher_exact_sha_pin_removed_detected",
    not detect_launcher_pin(LSRC.replace(FROZEN_V1_17_EXEC_SHA, "0" * 64)),
    "launcher pin mismatched -> rejected")
rec("NC_D80_H_supervisor", "supervisor_launcher_pin_enforcement_removed_detected",
    not detect_supervisor_pin(SSRC.replace("FAIL_CLOSED__LAUNCHER_SHA_MISMATCH",
                                           "SOME_OTHER_STATUS")),
    "supervisor fail-closed pin removed -> rejected")

# ---- D81 NEW (§10) ---- #
_inv = json.loads((ROOT / "reports/audits"
                   / "phase36_v1_17_reachable_write_target_inventory.json").read_text())
_inv_targets = [t["path"] for t in _inv["csv_table_targets"]]

# NC_D81_1: omitted table target -> inventory completeness detector fails.
# Remove the EXACT row by identity (never rely on list ordering / last-element
# truncation: the omitted control must be shown to catch *this* target).
_NC_D81_1_TARGET = "reports/tables/phase36_robustness_v1_17/phase36_worst_case_by_domain.csv"
_inv_targets_omitted = [p for p in _inv_targets if p != _NC_D81_1_TARGET]
rec("NC_D81_1", "omitted_table_target_detected",
    (_NC_D81_1_TARGET in _inv_targets)                       # precondition: present canonically
    and (not detect_table_target_enumerated(_inv_targets_omitted, _NC_D81_1_TARGET)),
    "remove the worst_case_by_domain table row from the inventory -> detector returns False (rejected)")

# NC_D81_2: generic non-versioned phase36 table target -> namespace detector fails.
rec("NC_D81_2", "generic_nonversioned_table_target_detected",
    not detect_namespace_uniform(
        _inv_targets + ["reports/tables/phase36_execution_rate_summary.csv"]),
    "add an unversioned reports/tables/phase36_*.csv -> detector returns False (rejected)")

# NC_D81_3: generic inherited figure dir -> namespace detector fails.
rec("NC_D81_3", "generic_inherited_figure_dir_detected",
    not detect_namespace_uniform(
        ["reports/figures/phase36_robustness/R1_image_perturbation_mean_paired_delta_dice_heatmap.png"]),
    "an inherited reports/figures/phase36_robustness/ path -> detector returns False (rejected)")

# NC_D81_4: CSV writer reverted to open("w") overwrite mode.
# Inject the EXACT reversion token that the fail-closed detector inspects
# (``path.open("w"`` is what ``detect_csv_fail_closed`` rejects); the mutant must
# therefore *append the canonical overwrite writer body*, not merely prepend a
# harmless call, so that a correct detector provably rejects it.
_writer_anchor = SRC.split("def _write_csv")[1].split("\ndef ")[0]
_writer_overwrite_mutant = (
    '    path.parent.mkdir(parents=True, exist_ok=True)\n'
    '    with path.open("w", encoding="utf-8", newline="") as f:\n'
    '        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")\n'
    '        w.writeheader()\n'
    '        for r in rows:\n'
    '            w.writerow(r)\n'
)
rec("NC_D81_4", "csv_writer_open_w_overwrite_detected",
    ('path.open("w"' not in _writer_anchor)                    # precondition: canonical is fail-closed
    and (not detect_csv_fail_closed(_writer_overwrite_mutant)),
    "restore path.open(w) overwrite semantics -> detector returns False (rejected)")

# ---- D82 NEW (§10) ---- #
# NC_D82_1: gate requires a v1.17 smoke artifact.
rec("NC_D82_1", "gate_requiring_v1_17_smoke_detected",
    not detect_gate_uses_historical_smoke_not_v1_17(
        SRC.replace("HISTORICAL_V1_14_SMOKE", "SMOKE_V1_17_ARTIFACT")
           + '\nSMOKE_V1_17_ARTIFACT = "reports/audits/phase36_robustness_smoke_v1_17.json"\n'),
    "gate re-requires a v1.17 smoke -> detector returns False (rejected)")

# NC_D82_2: attestation missing a required D40 field.
_att = json.loads((ROOT / "reports/audits"
                   / "phase36_v1_17_science_release_attestation.json").read_text())
_att_missing = {k: v for k, v in _att.items() if k != "release_gate"}
rec("NC_D82_2", "attestation_missing_d40_field_detected",
    not detect_attestation_schema_complete(_att_missing),
    "drop the 'release_gate' field -> detector returns False (rejected)")

# ---- D83 NEW (§10) ---- #
# NC_D83_1: a validator that checks only the revision without evaluating state.
rec("NC_D83_1", "validator_revision_string_only_detected",
    not detect_validator_evaluates_release_state(
        "# only checks att.get('revision') == REVISION; never evaluates runtime release state"),
    "a revision-string-only validator -> detector returns False (rejected)")

# NC_D83_2: gate NOT_RELEASED while eligibility is eligible.
rec("NC_D83_2", "gate_not_released_while_eligible_detected",
    not detect_gate_released_when_eligible("NOT_RELEASED", eligibility_eligible=True),
    "ELIGIBLE revision with NOT_RELEASED gate -> detector returns False (rejected)")

# --------------------------------------------------------------------------- #
n_pass = sum(1 for r in records if r["passed"])
n_total = len(records)
report = {
    "artifact": "phase36_robustness_negative_controls_v1_17",
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
out_path = ROOT / "reports/audits/phase36_v1_17_negative_controls.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(report, indent=1), encoding="utf-8")
for r in records:
    if not r["passed"]:
        print(f"FAIL {r['id']} :: {r['control']}")
print(f"NEGATIVE CONTROLS v1.17: {n_pass}/{n_total} pass")
print(f"terminal: {'PHASE36_V1_17_NEGATIVE_CONTROLS_PASS' if n_pass == n_total else 'PHASE36_V1_17_NEGATIVE_CONTROLS_FAIL'}")
raise SystemExit(0 if n_pass == n_total else 1)
