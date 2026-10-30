#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase36 — v1.18 EXECUTION SOURCE GENERATOR (deterministic, WO#17E).

Derives scripts/analysis/phase36_robustness_execution_v1_18.py from the frozen
v1.17 source by applying ONLY the D88 operational repairs (real-time complete
output-absence gate + fail-closed figure writer).  ALL scientific computation is
preserved byte-for-byte: D61 canonical fusion and the D75 POLICY_B helper are
untouched, as are router / ROI / rf202 / R_psi / S_omega / safety / geometry /
perturbations / seeds / metrics / thresholds / tolerances / ordering / batches /
fold-splits / the live-f32 G / VAL808 / KUB reporting semantics.

Transformations (ordered, exact-token):
  V1  version namespace: V1_17 -> V1_18, v1_17 -> v1_18, V1.17 -> V1.18
  V2  revision literal:  ra_medfilm_barr_phase36_robustness_v1_17 -> ..._v1_18
  V3  science/smoke artifact namespace: *_v1_17.json -> *_v1_18.json
  V4  launch authority token: PHASE36_V1_17_LAUNCH_AUTHORITY -> PHASE36_V1_18_LAUNCH_AUTHORITY
  V5  operator gates: PHASE36_V1_18_EXECUTE / PHASE36_V1_18_SMOKE_EXECUTE
  V6  runtime manifest path: phase36_v1_17_runtime_... -> phase36_v1_18_runtime_...
  V7  D88: PATH REBASE of TAB/ARR/FIG into a unique v1.18 sub-namespace
  V8  D88: FAIL-CLOSED FIGURE WRITER (_savefig_once) wired through R1-R5
  V9  D88: COMPLETE REAL-TIME OUTPUT-ABSENCE GATE (23 reachable targets)
  V10 header provenance note: v1.17 -> v1.18

Fail-closed post-conditions: no residual v1_17/V1_17 token in the emitted
source except the intentional historical-reference sentinels enumerated below.

Runs ONCE.  Re-run -> REFUSE_OVERWRITE (rc 2).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_17.py"
OUT = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_18.py"

V17_SHA = "81d78460b2f20f176bc697cba662c43bc7c7443ea555ba95a30609faf0ccbe31"

# Historical-reference sentinels that MUST retain the literal v1_17 token
# (they document the forbidden/aliased historical paths and D84 provenance).
ALLOWED_V1_17_RESIDUE = [
    "FORBIDDEN_SCIENCE_RESULT_V1_8",                       # sentinel name
    "phase36_robustness_scientific_result_v1_8.json",      # historical forbidden
    "HISTORICAL_V1_14_SMOKE",                              # historical smoke bind
    "phase36_robustness_smoke_v1_14.json",                 # historical smoke path
]


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    if OUT.exists():
        print(json.dumps({"status": "REFUSE_OVERWRITE",
                          "path": str(OUT.relative_to(ROOT))}, indent=1))
        return 2
    if sha256_file(SRC) != V17_SHA:
        print(json.dumps({"status": "FAIL_CLOSED__V1_17_SOURCE_SHA_MISMATCH",
                          "observed": sha256_file(SRC)}, indent=1))
        return 3

    s = SRC.read_text(encoding="utf-8")

    # ------------------------------------------------------------------ #
    # V1 version namespace (token families)
    # ------------------------------------------------------------------ #
    s = s.replace("V1_17", "V1_18")
    s = s.replace("v1_17", "v1_18")
    s = s.replace("V1.17", "V1.18")
    s = s.replace("v1.17", "v1.18")

    # ------------------------------------------------------------------ #
    # V7 D88: rebase TAB/ARR/FIG into a unique v1.18 sub-namespace
    # ------------------------------------------------------------------ #
    old_paths = (
        '# v1.18 (D81): ALL reachable scientific tabular/figure/array outputs are\n'
        '# routed into a UNIQUE v1.18 namespace.  NEVER write an unversioned\n'
        '# reports/tables, reports/arrays, or reports/figures/phase36_robustness path.\n'
        'TAB = ROOT / "reports" / "tables" / "phase36_robustness_v1_18"\n'
        'ARR = ROOT / "reports" / "arrays" / "phase36_robustness_v1_18"\n'
        'FIG = ROOT / "reports" / "figures" / "phase36_robustness_v1_18"'
    )
    new_paths = (
        '# v1.18 (D88): ALL reachable scientific tabular/figure/array outputs are\n'
        '# routed into a UNIQUE v1.18 namespace.  NEVER write an unversioned\n'
        '# reports/tables, reports/arrays, or reports/figures/phase36_robustness path.\n'
        'TAB = ROOT / "reports" / "tables" / "phase36_robustness_v1_18"\n'
        'ARR = ROOT / "reports" / "arrays" / "phase36_robustness_v1_18"\n'
        'FIG = ROOT / "reports" / "figures" / "phase36_robustness_v1_18"'
    )
    assert old_paths in s, "TAB/ARR/FIG block anchor missing"
    s = s.replace(old_paths, new_paths, 1)

    # ------------------------------------------------------------------ #
    # V8 D88: fail-closed figure writer, wired through R1-R5
    # ------------------------------------------------------------------ #
    # 1) Insert the write-once helper immediately before figure_R1.
    anchor_r1 = "def figure_R1(image_rows):"
    assert anchor_r1 in s, "figure_R1 anchor missing"
    helper_src = (
        'def _savefig_once(fig, path: Path, **kwargs):\n'
        '    """v1.18 (D88): FAIL-CLOSED, WRITE-ONCE figure writer.\n\n'
        '    Refuses to write to an EXISTING target (raises FileExistsError).\n'
        '    Opens the target in EXCLUSIVE binary-create mode, saves the figure\n'
        '    through the file handle, then flush + fsync + close.  There is NO\n'
        '    overwrite path: ``fig.savefig(path, ...)`` NEVER writes a v1.18\n'
        '    scientific figure.\n'
        '    """\n'
        '    path = Path(path)\n'
        '    path.parent.mkdir(parents=True, exist_ok=True)\n'
        '    if path.exists():\n'
        '        raise FileExistsError(\n'
        '            f"V1_18_FIGURE_FAIL_CLOSED__TARGET_EXISTS__REFUSE_OVERWRITE: {path}")\n'
        '    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY\n'
        '    if hasattr(os, "O_BINARY"):\n'
        '        flags |= os.O_BINARY\n'
        '    fd = os.open(str(path), flags, 0o644)\n'
        '    try:\n'
        '        with os.fdopen(fd, "wb") as fh:\n'
        '            fig.savefig(fh, format="png", **kwargs)\n'
        '            fh.flush()\n'
        '            os.fsync(fh.fileno())\n'
        '    finally:\n'
        '        try:\n'
        '            os.close(fd)\n'
        '        except OSError:\n'
        '            pass\n'
        '    return str(path)\n\n\n'
    )
    s = s.replace(anchor_r1, helper_src + anchor_r1, 1)

    # 2) Replace each of the five plain-savefig call sites with the helper.
    #    The five sites are byte-identical, so replace ALL occurrences.
    old_save = '    fig.savefig(p, dpi=160); plt.close(fig)\n    return str(p)'
    new_save = ('    _savefig_once(fig, p, dpi=160); plt.close(fig)\n'
                '    return str(p)')
    assert s.count(old_save) == 5, f"expected 5 savefig sites, found {s.count(old_save)}"
    s = s.replace(old_save, new_save)

    # ------------------------------------------------------------------ #
    # V9 D88: complete real-time output-absence gate (23 reachable targets)
    # ------------------------------------------------------------------ #
    # Insert the reachable-target enumerator + gate helper just before the
    # science release-gate section header so it is importable and testable.
    gate_anchor = (
        '# =========================================================================== #\n'
        '# §D40 (v1.18) — MACHINE-ENFORCED SCIENCE ELIGIBILITY                       #\n'
        '# =========================================================================== #'
    )
    assert gate_anchor in s, "D40 section anchor missing"
    gate_src = (
        '# =========================================================================== #\n'
        '# §D88 (v1.18) — COMPLETE REAL-TIME OUTPUT-ABSENCE GATE                     #\n'
        '# =========================================================================== #\n'
        '# DEFECT (proven from the frozen v1.17 chain):\n'
        '#   v1.17 enumerated the reachable write targets statically, but the REAL\n'
        '#   dispatch path never re-verified their ABSENCE immediately before\n'
        '#   dispatch, and figures used plain ``fig.savefig(path)`` overwrite\n'
        '#   semantics.  A pre-existing table or figure could therefore be silently\n'
        '#   overwritten by a real attempt.\n'
        '#\n'
        '# REPAIR (v1.18): the complete reachable-write inventory is frozen as data\n'
        '#   and RE-VERIFIED at dispatch time.  If ANY target exists the dispatch\n'
        '#   FAILS CLOSED *BEFORE* the START marker is created.\n'
        'V1_18_REACHABLE_SCIENCE_TABLES = (\n'
        '    "phase36_image_robustness_per_sample.csv",\n'
        '    "phase36_image_robustness_by_domain_condition.csv",\n'
        '    "phase36_noise_seed_summary.csv",\n'
        '    "phase36_proposal_robustness_per_sample.csv",\n'
        '    "phase36_proposal_robustness_by_domain_condition.csv",\n'
        '    "phase36_route_stability_summary.csv",\n'
        '    "phase36_execution_rate_summary.csv",\n'
        '    "phase36_worst_case_per_sample.csv",\n'
        '    "phase36_worst_case_by_domain.csv",\n'
        '    "phase36_kub_subgroup_robustness.csv",\n'
        '    "phase36_kub_subgroup_robustness_by_subgroup.csv",\n'
        ')\n\n'
        'V1_18_REACHABLE_FIGURES = (\n'
        '    "R1_image_perturbation_mean_paired_delta_dice_heatmap.png",\n'
        '    "R2_severity_curves_noise_blur_resolution.png",\n'
        '    "R3_route_state_change_and_execution_rate_heatmap.png",\n'
        '    "R4_proposal_perturbation_paired_delta_dice.png",\n'
        '    "R5_worst_case_delta_dice_distribution_by_domain.png",\n'
        ')\n\n\n'
        'def v1_18_reachable_write_targets() -> list:\n'
        '    """§D88: the COMPLETE frozen list of v1.18 real-dispatch write targets.\n\n'
        '    = 16 scientific table/figure outputs (11 CSV + 5 figures)\n'
        '      + START + RESULT + FAILURE + JOURNAL + stdout + stderr + PROCESS_EXIT\n'
        '    = 23 targets.  Any target not in this list is UNCLASSIFIED and makes\n'
        '    the inventory contract FAIL CLOSED.\n'
        '    """\n'
        '    targets = []\n'
        '    for fn in V1_18_REACHABLE_SCIENCE_TABLES:\n'
        '        targets.append(TAB / fn)\n'
        '    for fn in V1_18_REACHABLE_FIGURES:\n'
        '        targets.append(FIG / fn)\n'
        '    targets.append(ROOT / SCIENCE_V1_18_START_MARKER)\n'
        '    targets.append(ROOT / SCIENCE_V1_18_ARTIFACT)\n'
        '    targets.append(ROOT / SCIENCE_V1_18_FAILURE_ARTIFACT)\n'
        '    targets.append(ROOT / SCIENCE_V1_18_JOURNAL_DIR)\n'
        '    targets.append(ROOT / "reports" / "audits"\n'
        '                   / "phase36_robustness_science_stdout_v1_18.txt")\n'
        '    targets.append(ROOT / "reports" / "audits"\n'
        '                   / "phase36_robustness_science_stderr_v1_18.txt")\n'
        '    targets.append(ROOT / "reports" / "audits"\n'
        '                   / "phase36_robustness_science_process_exit_v1_18.json")\n'
        '    return targets\n\n\n'
        'def verify_v1_18_output_absence() -> dict:\n'
        '    """§D88: real-time COMPLETE output-absence verification.\n\n'
        '    Called on the REAL dispatch path immediately before the START marker\n'
        '    is created.  FAILS CLOSED if ANY frozen reachable target exists.\n'
        '    """\n'
        '    present = []\n'
        '    for p in v1_18_reachable_write_targets():\n'
        '        if p.exists():\n'
        '            present.append(str(p.relative_to(ROOT)))\n'
        '    return {\n'
        '        "all_targets_absent": not present,\n'
        '        "present_targets": present,\n'
        '        "target_count": len(v1_18_reachable_write_targets()),\n'
        '        "terminal": ("PHASE36_V1_18_REAL_LAUNCH_OUTPUT_ABSENCE_GATE_PASS"\n'
        '                     if not present else\n'
        '                     "PHASE36_V1_18_REAL_LAUNCH_OUTPUT_ABSENCE_GATE_FAIL_CLOSED"),\n'
        '    }\n\n\n'
    )
    s = s.replace(gate_anchor, gate_src + gate_anchor, 1)

    # Wire the gate into the real dispatch path, immediately BEFORE the
    # exclusive-create of the START marker.
    old_dispatch = (
        '        try:\n'
        '            _create_science_start_marker(\n'
        '                source_sha=_sha(Path(__file__)),\n'
        '                science_gate_state="GATE_AUTHORIZED__MARKER_CREATED_PRE_MODEL_CONSTRUCTION")'
    )
    new_dispatch = (
        '        # §D88 (v1.18): REAL-TIME COMPLETE OUTPUT-ABSENCE GATE.\n'
        '        #   Runs AFTER authorization and BEFORE the START marker is created.\n'
        '        #   Any pre-existing reachable target -> FAIL CLOSED, no attempt.\n'
        '        _absence = verify_v1_18_output_absence()\n'
        '        if not _absence["all_targets_absent"]:\n'
        '            print(json.dumps({\n'
        '                "mode": "science",\n'
        '                "output_absence": _absence,\n'
        '                "terminal": ("PHASE36_V1_18_REAL_LAUNCH_OUTPUT_ABSENCE_GATE_FAIL_CLOSED"\n'
        '                             "__NO_ATTEMPT_CONSUMED"),\n'
        '                "marker_created": False,\n'
        '                "automatic_retry": False,\n'
        '                "overwrite_permitted": False,\n'
        '            }, indent=1))\n'
        '            return 2\n'
        '        try:\n'
        '            _create_science_start_marker(\n'
        '                source_sha=_sha(Path(__file__)),\n'
        '                science_gate_state="GATE_AUTHORIZED__MARKER_CREATED_PRE_MODEL_CONSTRUCTION")'
    )
    assert old_dispatch in s, "real-dispatch START-marker anchor missing"
    s = s.replace(old_dispatch, new_dispatch, 1)

    # ------------------------------------------------------------------ #
    # V10 header provenance note
    # ------------------------------------------------------------------ #
    s = s.replace(
        "#   v1.17 FINAL OPERATIONAL REPAIR over frozen v1.16 (D81/D82/D83).",
        "#   v1.18 FINAL PRE-EXECUTION AUTHORITY REPAIR over frozen v1.17 (D85/D86/D87/D88).",
        1)
    if "v1.18 FINAL PRE-EXECUTION AUTHORITY REPAIR" not in s:
        s = s.replace(
            "REVISION: ra_medfilm_barr_phase36_robustness_v1_18",
            "REVISION: ra_medfilm_barr_phase36_robustness_v1_18\n"
            "#   v1.18 FINAL PRE-EXECUTION AUTHORITY REPAIR over frozen v1.17\n"
            "#   (D85/D86/D87/D88).\n"
            "#   Scientific computation is IDENTICAL to v1.17 (and hence v1.16/v1.15):\n"
            "#   D61 canonical fusion + D75 POLICY_B.  NO new scientific choice.",
            1)

    # ------------------------------------------------------------------ #
    # Fail-closed post-conditions
    # ------------------------------------------------------------------ #
    assert "C.GATE_ENV" not in s, "residual C.GATE_ENV"
    assert 'V1_18_SCIENCE_GATE_ENV = "PHASE36_V1_18_EXECUTE"' in s
    assert 'PHASE36_V1_18_LAUNCH_AUTHORITY' in s
    # v1.18 namespace present; v1.17 science/smoke namespace absent
    assert "phase36_robustness_science_start_v1_18.json" in s
    assert "phase36_robustness_science_start_v1_17.json" not in s
    assert "phase36_robustness_scientific_result_v1_17.json" not in s
    assert "phase36_v1_17_runtime_source_integrity_manifest.json" not in s
    assert "phase36_v1_18_runtime_source_integrity_manifest.json" in s
    # D88 namespace rebase
    assert 'TAB = ROOT / "reports" / "tables" / "phase36_robustness_v1_18"' in s
    assert 'ARR = ROOT / "reports" / "arrays" / "phase36_robustness_v1_18"' in s
    assert 'FIG = ROOT / "reports" / "figures" / "phase36_robustness_v1_18"' in s
    # inherited D81 fail-closed CSV writer preserved
    assert 'open(path, "x", encoding="utf-8", newline="")' in s
    assert 'V1_18_CSV_FAIL_CLOSED__TARGET_EXISTS__REFUSE_OVERWRITE' in s
    assert 'path.open("w", encoding="utf-8", newline="")' not in s
    # D88 fail-closed figure writer
    assert "def _savefig_once(" in s
    assert 'V1_18_FIGURE_FAIL_CLOSED__TARGET_EXISTS__REFUSE_OVERWRITE' in s
    assert "fig.savefig(p, dpi=160)" not in s
    assert s.count("_savefig_once(fig, p, dpi=160)") == 5
    # D88 real-time output absence gate
    assert "def v1_18_reachable_write_targets(" in s
    assert "def verify_v1_18_output_absence(" in s
    assert "PHASE36_V1_18_REAL_LAUNCH_OUTPUT_ABSENCE_GATE_PASS" in s
    assert "_absence = verify_v1_18_output_absence()" in s
    # D82 historical smoke bind preserved
    assert "HISTORICAL_V1_14_SMOKE" in s
    assert "53543729fb0c48695c2af202c5f3d2f5ebdfc29d87c7a7f100bcde9f94882441" in s
    # scientific repairs preserved (IDENTICAL to v1.17)
    assert "fuse_full_field(p_global, refined, geom)" in s
    assert "system._fuse_global_with_regional(p_global, refined, window)" not in s
    assert s.count("_phase27_scored_final_binary(") == 3
    assert "SEGMENTATION_OUTPUT_THRESHOLD = 0.50" in s
    assert "PHASE36_ROBUSTNESS_SCIENCE_V1_18_STAGE_JOURNAL" in s
    assert "_ScienceJournal(" in s
    # only allowed v1_17 residue remains
    residue_lines = [ln for ln in s.splitlines() if ("v1_17" in ln or "V1_17" in ln)]
    for ln in residue_lines:
        assert any(tok in ln for tok in ALLOWED_V1_17_RESIDUE), \
            f"unexpected v1_17 residue: {ln!r}"

    OUT.write_text(s, encoding="utf-8")
    compile(s, str(OUT), "exec")

    print(json.dumps({
        "status": "V1_18_GENERATED",
        "path": str(OUT.relative_to(ROOT)),
        "sha256": sha256_file(OUT),
        "bytes": OUT.stat().st_size,
        "v1_17_residue_lines": residue_lines,
        "namespace_rebased": True,
        "csv_fail_closed": True,
        "figure_fail_closed": True,
        "realtime_output_absence_gate": True,
        "historical_smoke_bound": True,
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
