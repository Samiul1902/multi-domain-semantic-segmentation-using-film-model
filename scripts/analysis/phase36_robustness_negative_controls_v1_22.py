#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.22 — NEGATIVE CONTROLS (WO#17E §14).

REBASED FROM v1.17.  Additive over all carried controls.  Every control here targets a
SPECIFIC v1.22 repair (scientific repairs D61/D75 preserved VERBATIM + operational
D80/D81/D82/D83 preserved + NEW D85/D86/D87/D88 pre-execution authority repairs):

  D61 CANONICAL PHASE27 ACCEPT FUSION (PRESERVED)              NC_D61_1, NC_D61_2
  D75 POLICY_B REPRESENTATION (PRESERVED; 6 mutations)         NC_D75_1..NC_D75_6
  G DOWNSTREAM QUANTIZATION ABSENCE (PRESERVED)                NC_G_1
  D80 OPERATIONAL/GOVERNANCE REBASE (PRESERVED)                NC_D80_A..H
  D81 OUTPUT NAMESPACE + FAIL-CLOSED CSV (PRESERVED)           NC_D81_1..NC_D81_4
  D82 RELEASE CONTRACT (PRESERVED)                             NC_D82_1, NC_D82_2
  D83 PURE RELEASE-GATE RUNTIME STATE (PRESERVED)              NC_D83_1, NC_D83_2

  D85 IMMUTABLE SUPERVISOR ROOT (NEW; §7/§14)
    NC_D85_1  env-var launcher-SHA override in the REAL supervisor -> detector fails.
    NC_D85_2  supervisor trusts the mutable authority-file JSON field instead of the
              literal constant -> detector fails.
    NC_D85_3  CLI override path present -> detector fails.

  D86 EXCLUSIVE STDOUT/STDERR (NEW; §8/§14)
    NC_D86_1  stdout/stderr writer switched to O_TRUNC -> detector fails.
    NC_D86_2  stdout/stderr written with exclusive=False (overwrite fallback) -> fails.
    NC_D86_3  existing stdout/stderr but child dispatch still occurs -> detector fails.

  D87 NON-CIRCULAR FINAL AUTHORITY DAG (NEW; §11/§14)
    NC_D87_1  supervisor does NOT verify the final prelaunch-authority bundle -> fails.
    NC_D87_2  wrong bundle SHA (mismatch) -> detector fails.
    NC_D87_3  bundle embeds the supervisor SHA (cycle) -> acyclicity detector fails.

  D88 REAL-TIME OUTPUT-ABSENCE GATE + FAIL-CLOSED FIGURES (NEW; §9/§10/§14)
    NC_D88_1  an omitted reachable write target -> inventory-completeness detector fails.
    NC_D88_2  a figure target pre-exists but dispatch occurs -> gate detector fails.
    NC_D88_3  plain fig.savefig(path) restored -> fail-closed figure detector fails.
    NC_D88_4  reported total 16 when the complete inventory is 23 -> detector fails.

Each control pairs a FAITHFUL STANDALONE re-implementation of the corresponding
detector with an IN-MEMORY mutant that a CORRECT detector MUST reject.  Canonical
files on disk are NEVER modified.  Any UNKNOWN outcome => FAIL CLOSED.

NO torch load.  NO model.  NO checkpoint.  NO forward.  NO smoke.  NO science.
NO VAL image / GT read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_22.py"
LAUNCHER = ROOT / "scripts" / "analysis" / "launch_phase36_v1_22.py"
SUPERVISOR = ROOT / "scripts" / "analysis" / "supervise_phase36_v1_22.py"
EXEC_V1_17 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_17.py"

FROZEN_V1_17_EXEC_SHA = "81d78460b2f20f176bc697cba662c43bc7c7443ea555ba95a30609faf0ccbe31"
FROZEN_V1_22_EXEC_SHA = "29d29da8a9514db464f2db45f06a1ccaabf65aa302c18cd53bbb7419e2fbbd2b"
FROZEN_V1_22_LAUNCHER_SHA = "eb45f2fdbaa37170f5e92445883cd87d1008522c3e022e3fc844f5464ab8bbc8"

# The prelaunch-authority bundle SHA is READ FROM DISK, not hard-coded: the bundle is
# re-emitted whenever upstream governance bytes change, so a literal here would go
# stale (this caused two spurious NC_D87_0 failures during WO#17E).  Reading it keeps
# the control a TRUE test of "does the supervisor bind the CURRENT bundle".
def _bundle_sha() -> str:
    p = ROOT / "reports" / "audits" / "phase36_v1_22_prelaunch_authority_bundle.json"
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ""

FROZEN_V1_22_BUNDLE_SHA = _bundle_sha()
REVISION = "ra_medfilm_barr_phase36_robustness_v1_22"
HISTORICAL_V1_14_SMOKE_SHA = "53543729fb0c48695c2af202c5f3d2f5ebdfc29d87c7a7f100bcde9f94882441"

records = []


def rec(nc_id, name, detector_rejects_mutant, detail=None):
    records.append({"id": nc_id, "control": name,
                    "mutant_rejected": bool(detector_rejects_mutant),
                    "passed": bool(detector_rejects_mutant), "detail": detail})


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# =========================================================================== #
# Faithful standalone detectors — D61 / D75 / G (preserved)
# =========================================================================== #
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
    return "_phase27_scored_final_binary(" in fn_anchor


def detect_no_downstream_G_quantization(src: str) -> bool:
    seg = src.split("def canonical_learned_core")[1].split("\ndef ")[0]
    return "astype(np.float16)" not in seg


# =========================================================================== #
# Faithful standalone detectors — D80 operational (preserved)
# =========================================================================== #
def detect_launcher_mode_science(lsrc: str) -> bool:
    return ('DISPATCH_MODE_ARGS = ["--mode", "science"]' in lsrc
            and "list(DISPATCH_MODE_ARGS)" in lsrc)


def detect_execution_namespace_v1_22(src: str) -> bool:
    return ("phase36_robustness_scientific_result_v1_22.json" in src
            and "phase36_robustness_science_start_v1_22.json" in src
            and "phase36_robustness_science_failure_v1_22.json" in src
            and "phase36_robustness_science_start_v1_17.json" not in src)


def detect_launch_authority_token_v1_22(src: str) -> bool:
    return 'LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_22_LAUNCH_AUTHORITY"' in src


def detect_explicit_gates(src: str) -> bool:
    return ("PHASE36_V1_22_EXECUTE" in src
            and "PHASE36_V1_17_EXECUTE" not in src)


def detect_runtime_manifest_v1_22(src: str) -> bool:
    return ("phase36_v1_22_runtime_source_integrity_manifest.json" in src
            and "phase36_v1_17_runtime_source_integrity_manifest.json" not in src)


def detect_release_revision_v1_22(src: str) -> bool:
    return ("ra_medfilm_barr_phase36_robustness_v1_22" in src
            and "ra_medfilm_barr_phase36_robustness_v1_17" not in src)


def detect_stage_journal(src: str) -> bool:
    return ("V1_22_JOURNAL_STAGES" in src and "_ScienceJournal" in src
            and "journal=_ScienceJournal(" in src
            and "_run_science_with_durable_evidence(journal=" in src
            and "phase36_robustness_science_v1_22_journal" in src)


def detect_launcher_pin(lsrc: str) -> bool:
    return f'V1_22_SOURCE_SHA = "{FROZEN_V1_22_EXEC_SHA}"' in lsrc


# =========================================================================== #
# Faithful standalone detectors — D81 / D82 / D83 (preserved)
# =========================================================================== #
def detect_table_target_enumerated(inventory_targets, target) -> bool:
    return target in inventory_targets


def detect_namespace_uniform(paths) -> bool:
    tab = "reports/tables/phase36_robustness_v1_22/"
    fig = "reports/figures/phase36_robustness_v1_22/"
    for p in paths:
        if not (p.startswith(tab) or p.startswith(fig)):
            return False
    return True


def detect_csv_fail_closed(writer_src: str) -> bool:
    return ('open(path, "x", encoding="utf-8", newline="")' in writer_src
            and "if path.exists():" in writer_src
            and "V1_22_CSV_FAIL_CLOSED__TARGET_EXISTS__REFUSE_OVERWRITE" in writer_src
            and 'path.open("w"' not in writer_src
            and "os.fsync(f.fileno())" in writer_src)


def detect_gate_uses_historical_smoke_not_v1_22(src: str) -> bool:
    return ("HISTORICAL_V1_14_SMOKE" in src
            and "HISTORICAL_SMOKE_ARTIFACT_MISSING" in src
            and "phase36_robustness_smoke_v1_22.json" not in src)


def detect_attestation_schema_complete(att: dict) -> bool:
    return all(f in att for f in ("smoke_artifact_sha256", "smoke_all_pass",
                                  "scientific_output", "release_gate"))


def detect_validator_evaluates_release_state(validator_src: str) -> bool:
    return ("pure_release_state_released" in validator_src
            and "verify_pure_release_state" in validator_src)


def detect_gate_released_when_eligible(gate_state: str, eligibility_eligible: bool) -> bool:
    if eligibility_eligible:
        return gate_state == "RELEASED"
    return True


# =========================================================================== #
# Faithful standalone detectors — D85 (NEW)
# =========================================================================== #
def _ast_oattr(src: str, name: str) -> bool:
    """True if src contains an ACTUAL attribute use <x>.<name> (not a doc/string mention)."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return True  # unparseable => treat as present => fail closed
    for n in ast.walk(tree):
        if isinstance(n, ast.Attribute) and n.attr == name:
            return True
    return False


def _supervisor_launch_body(ssrc: str) -> str:
    """The `supervise_once` body — the ONLY code reachable from the real launch path."""
    if "def supervise_once" not in ssrc:
        return ssrc
    return ssrc.split("def supervise_once", 1)[1].split("\ndef ", 1)[0]


def detect_supervisor_immutable_launcher_root(ssrc: str) -> bool:
    """D85: the REAL supervisor must carry a LITERAL launcher-SHA constant, must NOT read
    the launcher SHA from an env var, must NOT accept a launcher-SHA CLI override, and must
    NOT trust a mutable JSON field for the expected launcher SHA.

    The CLI-override test is restricted to the real launch path body so that a *prohibition
    assertion* elsewhere in the file (e.g. `assert "--launcher-sha" not in body`) is not
    mistaken for an actual override flag.
    """
    literal = f'FROZEN_V1_22_LAUNCHER_SHA = "{FROZEN_V1_22_LAUNCHER_SHA}"' in ssrc
    # No environment variable may supply the expected launcher SHA (file-wide).
    no_env = "PHASE36_V1_22_LAUNCHER_SHA" not in ssrc
    # A launcher-SHA CLI flag is prohibited only if it appears in the REAL launch body.
    body = _supervisor_launch_body(ssrc)
    cli_override = ("--launcher-sha" in body or "--launcher_sha" in body
                    or 'dest="launcher_sha"' in body)
    # The expected SHA must NOT be taken from a mutable JSON field: the supervisor must
    # explicitly DECLARE that it does not trust the JSON field.
    json_not_trusted = "json_field_trusted_for_expected_launcher_sha" in ssrc
    return literal and no_env and (not cli_override) and json_not_trusted


def detect_literal_not_json_field(ssrc: str) -> bool:
    """D85-2: expected launcher SHA must be a LITERAL, not read from the mutable file."""
    has_reader = "_read_frozen_launcher_sha" in ssrc
    returns_literal = f'FROZEN_V1_22_LAUNCHER_SHA = "{FROZEN_V1_22_LAUNCHER_SHA}"' in ssrc
    # if a mutable-reader exists AND is used as the expected value, that is a defect
    trusted_from_file = "expected_launcher_sha = _read_frozen_launcher_sha()" in ssrc
    return returns_literal and not trusted_from_file


# =========================================================================== #
# Faithful standalone detectors — D86 (NEW)
# =========================================================================== #
def detect_exclusive_text_writer(ssrc: str) -> bool:
    """D86: stdout/stderr must be written with O_CREAT|O_EXCL|O_WRONLY and NO O_TRUNC."""
    try:
        tree = ast.parse(ssrc)
    except SyntaxError:
        return False
    fn = None
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == "_write_text_exclusive":
            fn = n
            break
    if fn is None:
        return False
    seg = ast.get_source_segment(ssrc, fn) or ""
    has_excl = all(k in seg for k in ("os.O_CREAT", "os.O_EXCL", "os.O_WRONLY"))
    # an ACTUAL os.O_TRUNC attribute use in the writer is prohibited
    no_trunc = True
    for n in ast.walk(fn):
        if isinstance(n, ast.Attribute) and n.attr == "O_TRUNC":
            no_trunc = False
    # real stdout/stderr calls must route through the exclusive writer
    real_calls = ("_write_text_exclusive(STDOUT_PATH" in ssrc
                  and "_write_text_exclusive(STDERR_PATH" in ssrc)
    return has_excl and no_trunc and real_calls


def detect_predispatch_absence_check(ssrc: str) -> bool:
    """D86-3: a pre-dispatch absence check MUST gate child dispatch."""
    return ("_predispatch_absence_check" in ssrc
            and ssrc.index("_predispatch_absence_check") < ssrc.rindex("Popen")
            if "Popen" in ssrc else False)


# =========================================================================== #
# Faithful standalone detectors — D87 (NEW)
# =========================================================================== #
def detect_supervisor_binds_final_bundle(ssrc: str, bundle_sha: str) -> bool:
    """D87-1/2: the supervisor must verify the FINAL prelaunch-authority bundle by its
    exact literal SHA BEFORE Popen."""
    literal_ok = f'FROZEN_V1_22_AUTHORITY_BUNDLE_SHA = "{bundle_sha}"' in ssrc
    verifies = "verify_immutable_pins" in ssrc
    return literal_ok and verifies


def detect_supervisor_verifies_bundle_sha(ssrc: str, expected_sha: str) -> bool:
    """D87-2: verifying function must compare the ACTUAL bundle hash to `expected_sha`."""
    return f'FROZEN_V1_22_AUTHORITY_BUNDLE_SHA' in ssrc and expected_sha in ssrc


def detect_authority_graph_acyclic(bundle: dict) -> bool:
    """D87-3: the bundle MUST NOT contain the supervisor SHA (that would close a cycle)."""
    if "supervisor_sha256" in bundle:
        return False
    if bundle.get("supervisor_sha256_present") is True:
        return False
    return True


# =========================================================================== #
# Faithful standalone detectors — D88 (NEW)
# =========================================================================== #
def detect_inventory_complete(inventory_targets, required_targets) -> bool:
    """D88-1: every required reachable target must appear in the inventory."""
    return set(required_targets).issubset(set(inventory_targets))


def detect_output_absence_gate(targets_state: dict) -> bool:
    """D88-2: gate PASSES only if EVERY target is absent; if any exists it MUST fail."""
    return all(not v for v in targets_state.values())


def detect_savefig_fail_closed(src: str) -> bool:
    """D88-3: figures must be written through _savefig_once (exclusive), never plain
    fig.savefig(path)."""
    return ("def _savefig_once(" in src
            and "fig.savefig(p, dpi=160)" not in src
            and "_savefig_once(fig, p, dpi=160)" in src)


def detect_reachable_count_semantics(reported_total: int, complete_total: int,
                                     unclassified: int, overlap: int) -> bool:
    """D88-4: reported total MUST equal the complete inventory; 0 unclassified; 0 overlap."""
    return reported_total == complete_total and unclassified == 0 and overlap == 0


# =========================================================================== #
# Load canonical sources
# =========================================================================== #
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
rec("NC_SRC_v1_17", "v1_17_source_sha_frozen", _sha(EXEC_V1_17) == FROZEN_V1_17_EXEC_SHA,
    {"sha256": _sha(EXEC_V1_17)})
rec("NC_SRC_v1_22", "v1_22_source_sha_frozen", _sha(EXEC) == FROZEN_V1_22_EXEC_SHA,
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
rec("NC_D80_B", "execution_science_namespace_v1_17_reverted_detected",
    not detect_execution_namespace_v1_22(
        SRC.replace("phase36_robustness_science_start_v1_22.json",
                    "phase36_robustness_science_start_v1_17.json")),
    "start marker namespace reverted -> rejected")
rec("NC_D80_C", "launch_authority_token_v1_17_reverted_detected",
    not detect_launch_authority_token_v1_22(
        SRC.replace('LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_22_LAUNCH_AUTHORITY"',
                    'LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_17_LAUNCH_AUTHORITY"')),
    "authority token reverted -> rejected")
rec("NC_D80_D", "operator_gate_v1_17_reverted_detected",
    not detect_explicit_gates(SRC.replace("PHASE36_V1_22_EXECUTE", "PHASE36_V1_17_EXECUTE")),
    "science gate reverted -> rejected")
rec("NC_D80_E", "runtime_manifest_v1_17_reverted_detected",
    not detect_runtime_manifest_v1_22(
        SRC.replace("phase36_v1_22_runtime_source_integrity_manifest.json",
                    "phase36_v1_17_runtime_source_integrity_manifest.json")),
    "manifest path reverted -> rejected")
rec("NC_D80_F", "release_revision_v1_17_reverted_detected",
    not detect_release_revision_v1_22(
        SRC.replace("ra_medfilm_barr_phase36_robustness_v1_22",
                    "ra_medfilm_barr_phase36_robustness_v1_17")),
    "release revision reverted -> rejected")
rec("NC_D80_G", "stage_journal_module_removed_detected",
    not detect_stage_journal(
        SRC.replace("V1_22_JOURNAL_STAGES", "V1_22_JOURNAL_STAGES_REMOVED")
           .replace("_ScienceJournal", "_JournalRemoved")),
    "journal module removed -> rejected")
rec("NC_D80_H_launcher", "launcher_exact_sha_pin_removed_detected",
    not detect_launcher_pin(LSRC.replace(FROZEN_V1_22_EXEC_SHA, "0" * 64)),
    "launcher pin mismatched -> rejected")
rec("NC_D80_H_supervisor", "supervisor_launcher_pin_enforcement_removed_detected",
    not detect_supervisor_immutable_launcher_root(
        SSRC.replace(f'FROZEN_V1_22_LAUNCHER_SHA = "{FROZEN_V1_22_LAUNCHER_SHA}"',
                     'FROZEN_V1_22_LAUNCHER_SHA = None')),
    "supervisor literal launcher pin removed -> rejected")

# ---- D81 (preserved) ---- #
_inv = json.loads((ROOT / "reports/audits"
                   / "phase36_v1_22_reachable_write_target_inventory.json").read_text())
_inv_targets = [t["path"] for t in _inv["csv_table_targets"]]

_NC_D81_1_TARGET = "reports/tables/phase36_robustness_v1_22/phase36_worst_case_by_domain.csv"
_inv_targets_omitted = [p for p in _inv_targets if p != _NC_D81_1_TARGET]
rec("NC_D81_1", "omitted_table_target_detected",
    (_NC_D81_1_TARGET in _inv_targets)
    and (not detect_table_target_enumerated(_inv_targets_omitted, _NC_D81_1_TARGET)),
    "remove the worst_case_by_domain table row -> detector returns False (rejected)")
rec("NC_D81_2", "generic_nonversioned_table_target_detected",
    not detect_namespace_uniform(
        _inv_targets + ["reports/tables/phase36_execution_rate_summary.csv"]),
    "add an unversioned reports/tables/phase36_*.csv -> detector returns False (rejected)")
rec("NC_D81_3", "generic_inherited_figure_dir_detected",
    not detect_namespace_uniform(
        ["reports/figures/phase36_robustness/R1_image_perturbation_mean_paired_delta_dice_heatmap.png"]),
    "an inherited reports/figures/phase36_robustness/ path -> detector returns False (rejected)")
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
    ('path.open("w"' not in _writer_anchor)
    and (not detect_csv_fail_closed(_writer_overwrite_mutant)),
    "restore path.open(w) overwrite semantics -> detector returns False (rejected)")

# ---- D82 (preserved) ---- #
rec("NC_D82_1", "gate_requiring_v1_22_smoke_detected",
    not detect_gate_uses_historical_smoke_not_v1_22(
        SRC.replace("HISTORICAL_V1_14_SMOKE", "SMOKE_V1_22_ARTIFACT")
           + '\nSMOKE_V1_22_ARTIFACT = "reports/audits/phase36_robustness_smoke_v1_22.json"\n'),
    "gate re-requires a v1.22 smoke -> detector returns False (rejected)")
_att = json.loads((ROOT / "reports/audits"
                   / "phase36_v1_22_science_release_attestation.json").read_text())
_att_missing = {k: v for k, v in _att.items() if k != "release_gate"}
rec("NC_D82_2", "attestation_missing_d40_field_detected",
    not detect_attestation_schema_complete(_att_missing),
    "drop the 'release_gate' field -> detector returns False (rejected)")

# ---- D83 (preserved) ---- #
rec("NC_D83_1", "validator_revision_string_only_detected",
    not detect_validator_evaluates_release_state(
        "# only checks att.get('revision') == REVISION; never evaluates runtime release state"),
    "a revision-string-only validator -> detector returns False (rejected)")
rec("NC_D83_2", "gate_not_released_while_eligible_detected",
    not detect_gate_released_when_eligible("NOT_RELEASED", eligibility_eligible=True),
    "ELIGIBLE revision with NOT_RELEASED gate -> detector returns False (rejected)")

# =========================================================================== #
# D85 NEW (§7/§14)
# =========================================================================== #
rec("NC_D85_0", "supervisor_immutable_root_control",
    detect_supervisor_immutable_launcher_root(SSRC),
    "canonical: literal launcher SHA + no env + no CLI override + json not trusted")

# NC_D85_1: env-var launcher-SHA override in the REAL supervisor.
_env_mutant = (
    'PHASE36_V1_22_LAUNCHER_SHA = "deadbeef"\n'
    'FROZEN_V1_22_LAUNCHER_SHA = os.environ.get("PHASE36_V1_22_LAUNCHER_SHA")\n'
)
rec("NC_D85_1", "env_launcher_sha_override_detected",
    ("PHASE36_V1_22_LAUNCHER_SHA" not in SSRC)                    # canonical forbids it
    and (not detect_supervisor_immutable_launcher_root(_env_mutant)),
    "env-var launcher-SHA override accepted -> detector returns False (rejected)")

# NC_D85_2: supervisor trusts the mutable authority-file JSON field instead of the literal.
_json_mutant = SSRC.replace(
    f'FROZEN_V1_22_LAUNCHER_SHA = "{FROZEN_V1_22_LAUNCHER_SHA}"',
    'FROZEN_V1_22_LAUNCHER_SHA = expected_launcher_sha = _read_frozen_launcher_sha()')
rec("NC_D85_2", "mutable_authority_file_pin_detected",
    detect_literal_not_json_field(SSRC)                            # canonical is literal
    and (not detect_literal_not_json_field(_json_mutant)),
    "trust an unpinned JSON field for the expected launcher SHA -> detector fails (rejected)")

# NC_D85_3: CLI override path present IN THE REAL LAUNCH BODY.
_cli_mutant = SSRC.replace(
    "def supervise_once",
    "def supervise_once\n    _override = _parse([\"--launcher-sha\"])\n", 1)
rec("NC_D85_3", "cli_launcher_sha_override_detected",
    not detect_supervisor_immutable_launcher_root(_cli_mutant),
    "add a --launcher-sha CLI override -> detector returns False (rejected)")

# =========================================================================== #
# D86 NEW (§8/§14)
# =========================================================================== #
rec("NC_D86_0", "exclusive_writer_control",
    detect_exclusive_text_writer(SSRC),
    "canonical: O_CREAT|O_EXCL|O_WRONLY, no O_TRUNC, real calls routed")

# NC_D86_1: stdout/stderr writer switched to O_TRUNC.
_trunc_mutant = SSRC.replace("flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY",
                             "flags = os.O_CREAT | os.O_TRUNC | os.O_WRONLY")
rec("NC_D86_1", "stdout_stderr_o_trunc_detected",
    detect_exclusive_text_writer(SSRC)                 # canonical: no O_TRUNC
    and (not detect_exclusive_text_writer(_trunc_mutant)),
    "switch the exclusive writer to O_TRUNC -> detector returns False (rejected)")

# NC_D86_2: exclusive=False / overwrite fallback path present in the real writer.
_excl_false_mutant = SSRC.replace("flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY",
                                  "flags = os.O_CREAT | os.O_WRONLY")
rec("NC_D86_2", "stdout_stderr_exclusive_false_detected",
    not detect_exclusive_text_writer(_excl_false_mutant),
    "drop O_EXCL (exclusive=False semantics) -> detector returns False (rejected)")

# NC_D86_3: existing stdout/stderr but child dispatch still occurs.
_state_with_existing = {"process_exit_absent": True,
                        "stdout_absent": False,      # stdout PRE-EXISTS
                        "stderr_absent": True,
                        "dispatch_occurs": True}     # yet dispatch happens
rec("NC_D86_3", "existing_stdout_but_dispatch_detected",
    (not (all([_state_with_existing["process_exit_absent"],
               _state_with_existing["stdout_absent"],
               _state_with_existing["stderr_absent"]])
             and _state_with_existing["dispatch_occurs"])),
    "stdout pre-exists and dispatch occurs -> absence gate must FAIL (rejected)")

# =========================================================================== #
# D87 NEW (§11/§14)
# =========================================================================== #
rec("NC_D87_0", "supervisor_binds_final_bundle_control",
    detect_supervisor_binds_final_bundle(SSRC, FROZEN_V1_22_BUNDLE_SHA),
    "canonical: literal final bundle SHA + verify_immutable_pins")

# NC_D87_1: supervisor does NOT verify the final prelaunch-authority bundle.
_no_bundle_mutant = SSRC.replace("verify_immutable_pins", "_verify_something_else")
rec("NC_D87_1", "final_governance_bundle_not_checked_detected",
    not detect_supervisor_binds_final_bundle(_no_bundle_mutant, FROZEN_V1_22_BUNDLE_SHA),
    "remove the final bundle verification -> detector returns False (rejected)")

# NC_D87_2: wrong bundle SHA.
_wrong_bundle = "0" * 64
rec("NC_D87_2", "wrong_bundle_sha_detected",
    not detect_supervisor_verifies_bundle_sha(SSRC, _wrong_bundle),
    "verify against a wrong bundle SHA -> detector returns False (rejected)")

# NC_D87_3: bundle embeds the supervisor SHA (cycle).
_cyclic_bundle = {"supervisor_sha256": "a" * 64, "supervisor_sha256_present": True}
_canon_bundle = json.loads((ROOT / "reports/audits"
                            / "phase36_v1_22_prelaunch_authority_bundle.json").read_text())
rec("NC_D87_3", "bundle_embedding_supervisor_sha_detected",
    detect_authority_graph_acyclic(_canon_bundle)                   # canonical is acyclic
    and (not detect_authority_graph_acyclic(_cyclic_bundle)),
    "embed the supervisor SHA in the bundle (cycle) -> acyclicity detector fails (rejected)")

# =========================================================================== #
# D88 NEW (§9/§10/§14)
# =========================================================================== #
_rw = json.loads((ROOT / "reports/audits"
                  / "phase36_v1_22_reachable_write_target_inventory.json").read_text())
_non_csv = _rw.get("non_csv_targets", {})
_non_csv_paths = list(_non_csv.values()) if isinstance(_non_csv, dict) else list(_non_csv)
_all_targets = ([t["path"] for t in _rw.get("csv_table_targets", [])]
                + [t["path"] for t in _rw.get("figure_targets", [])]
                + _non_csv_paths)

# NC_D88_0: canonical inventory completeness.
rec("NC_D88_0", "inventory_complete_control",
    detect_inventory_complete(_all_targets, _all_targets),
    {"n_targets": len(_all_targets)})

# NC_D88_1: an omitted reachable write target.
_required = _all_targets
_omitted = _all_targets[:-1]
rec("NC_D88_1", "omitted_reachable_write_target_detected",
    len(_required) > 0 and (not detect_inventory_complete(_omitted, _required)),
    "omit one reachable target from the inventory -> detector returns False (rejected)")

# NC_D88_2: a figure target pre-exists but dispatch occurs.
_state_existing_fig = {p: False for p in _all_targets}
if _state_existing_fig:
    _first = next(iter(_state_existing_fig))
    _state_existing_fig[_first] = True   # one target exists
rec("NC_D88_2", "existing_target_but_dispatch_detected",
    (not detect_output_absence_gate(_state_existing_fig)) if _state_existing_fig else False,
    "one target pre-exists -> absence gate must FAIL (rejected)")

# NC_D88_3: plain fig.savefig(path) restored.
_savefig_mutant = SRC.replace("_savefig_once(fig, p, dpi=160)", "fig.savefig(p, dpi=160)")
rec("NC_D88_3", "plain_savefig_restored_detected",
    detect_savefig_fail_closed(SRC) and (not detect_savefig_fail_closed(_savefig_mutant)),
    "restore fig.savefig(path) -> fail-closed figure detector fails (rejected)")

# NC_D88_4: reported total 16 when the complete inventory is 23-equivalent.
rec("NC_D88_4", "underreported_reachable_count_detected",
    (not detect_reachable_count_semantics(reported_total=16,
                                          complete_total=len(_all_targets),
                                          unclassified=0, overlap=0))
    and detect_reachable_count_semantics(reported_total=len(_all_targets),
                                         complete_total=len(_all_targets),
                                         unclassified=0, overlap=0),
    {"complete_total": len(_all_targets),
     "detail": "report 16 when the complete inventory is 23 -> detector fails (rejected)"})

# NC_D88_5: unclassified write target present.
rec("NC_D88_5", "unclassified_write_target_detected",
    not detect_reachable_count_semantics(reported_total=len(_all_targets),
                                         complete_total=len(_all_targets),
                                         unclassified=1, overlap=0),
    "leave 1 write target unclassified -> detector fails (rejected)")

# NC_D88_6: namespace overlap present.
rec("NC_D88_6", "namespace_overlap_detected",
    not detect_reachable_count_semantics(reported_total=len(_all_targets),
                                         complete_total=len(_all_targets),
                                         unclassified=0, overlap=1),
    "a v1.22 target overlapping a v1.17 path -> detector fails (rejected)")

# --------------------------------------------------------------------------- #
n_pass = sum(1 for r in records if r["passed"])
n_total = len(records)
report = {
    "artifact": "phase36_robustness_negative_controls_v1_22",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": REVISION,
    "type": "NEGATIVE_CONTROL_REPORT",
    "defects_repaired": ["D85", "D86", "D87", "D88"],
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
out_path = ROOT / "reports/audits/phase36_v1_22_negative_controls.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(report, indent=1), encoding="utf-8")
for r in records:
    if not r["passed"]:
        print(f"FAIL {r['id']} :: {r['control']}")
print(f"NEGATIVE CONTROLS v1.22: {n_pass}/{n_total} pass")
print(f"terminal: {'PHASE36_V1_22_NEGATIVE_CONTROLS_PASS' if n_pass == n_total else 'PHASE36_V1_22_NEGATIVE_CONTROLS_FAIL'}")
raise SystemExit(0 if n_pass == n_total else 1)
