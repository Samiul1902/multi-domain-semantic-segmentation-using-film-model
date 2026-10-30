#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase36 — v1.17 EXECUTION SOURCE GENERATOR (deterministic, WO#17C).

Derives scripts/analysis/phase36_robustness_execution_v1_17.py from the frozen
v1.16 source by applying ONLY the D81/D82/D83 operational repairs.  ALL
scientific computation is preserved byte-for-byte: D61 canonical fusion and the
D75 POLICY_B helper are untouched, as are router / ROI / rf202 / R_psi /
S_omega / safety / geometry / perturbations / seeds / metrics / thresholds /
tolerances / ordering / batches / fold-splits / the live-f32 G / VAL808 / KUB.

Transformations (ordered, exact-token):
  U1  version namespace: V1_16 -> V1_17, v1_16 -> v1_17, V1.16 -> V1.17
  U2  revision literal:  ra_medfilm_barr_phase36_robustness_v1_16 -> ..._v1_17
  U3  science/smoke artifact namespace: *_v1_16.json -> *_v1_17.json
  U4  launch authority token: PHASE36_V1_16_LAUNCH_AUTHORITY -> PHASE36_V1_17_LAUNCH_AUTHORITY
  U5  operator gates: PHASE36_V1_17_EXECUTE / PHASE36_V1_17_SMOKE_EXECUTE
  U6  runtime manifest path: phase36_v1_16_runtime_... -> phase36_v1_17_runtime_...
  U7  D81: PATH REBASE of TAB/ARR/FIG into a unique v1.17 sub-namespace
  U8  D81: FAIL-CLOSED CSV writer (refuse an existing target; never open("w"))
  U9  D82: NEW release contract — bind HISTORICAL v1.14 smoke (path+SHA),
      do NOT require a v1.17 smoke, and require the D40 schema fields
  U10 header provenance note: v1.16 -> v1.17

Fail-closed post-conditions: no residual v1_16/V1_16 token in the emitted
source except the intentional historical-reference sentinels enumerated below.

Runs ONCE.  Re-run -> REFUSE_OVERWRITE (rc 2).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_16.py"
OUT = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_17.py"

V16_SHA = "a96b74caa4587aa9d2f83b79ed39c13075a88086109e31d991695a75ec4abab9"

# Historical-reference sentinels that MUST retain the literal v1_16 token
# (they document the forbidden/aliased historical paths and D31 provenance).
ALLOWED_V1_16_RESIDUE = [
    "FORBIDDEN_SCIENCE_RESULT_V1_8",                       # sentinel name
    "phase36_robustness_scientific_result_v1_8.json",      # historical forbidden
    "HISTORICAL_V1_14_SMOKE",                              # historical smoke bind (new)
    "phase36_robustness_smoke_v1_14.json",                 # historical smoke path (new)
]


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    if OUT.exists():
        print(json.dumps({"status": "REFUSE_OVERWRITE", "path": str(OUT.relative_to(ROOT))}, indent=1))
        return 2
    if sha256_file(SRC) != V16_SHA:
        print(json.dumps({"status": "FAIL_CLOSED__V1_16_SOURCE_SHA_MISMATCH",
                          "observed": sha256_file(SRC)}, indent=1))
        return 3

    s = SRC.read_text(encoding="utf-8")
    orig = s

    # ------------------------------------------------------------------ #
    # U1 version namespace (token families)
    # ------------------------------------------------------------------ #
    s = s.replace("V1_16", "V1_17")
    s = s.replace("v1_16", "v1_17")
    s = s.replace("V1.16", "V1.17")
    s = s.replace("v1.16", "v1.17")

    # ------------------------------------------------------------------ #
    # U7 D81: rebase TAB/ARR/FIG into a unique v1.17 sub-namespace
    # ------------------------------------------------------------------ #
    old_paths = (
        'TAB = ROOT / "reports" / "tables"\n'
        'ARR = ROOT / "reports" / "arrays"\n'
        'FIG = ROOT / "reports" / "figures" / "phase36_robustness"'
    )
    new_paths = (
        '# v1.17 (D81): ALL reachable scientific tabular/figure/array outputs are\n'
        '# routed into a UNIQUE v1.17 namespace.  NEVER write an unversioned\n'
        '# reports/tables, reports/arrays, or reports/figures/phase36_robustness path.\n'
        'TAB = ROOT / "reports" / "tables" / "phase36_robustness_v1_17"\n'
        'ARR = ROOT / "reports" / "arrays" / "phase36_robustness_v1_17"\n'
        'FIG = ROOT / "reports" / "figures" / "phase36_robustness_v1_17"'
    )
    assert old_paths in s, "TAB/ARR/FIG block anchor missing"
    s = s.replace(old_paths, new_paths, 1)

    # ------------------------------------------------------------------ #
    # U8 D81: fail-closed CSV writer (never open("w"); refuse existing target)
    # ------------------------------------------------------------------ #
    old_writer = (
        'def _write_csv(path: Path, rows: list, fieldnames: list = None):\n'
        '    path.parent.mkdir(parents=True, exist_ok=True)\n'
        '    if not rows:\n'
        '        path.write_text("", encoding="utf-8")\n'
        '        return\n'
        '    fields = fieldnames or list(rows[0].keys())\n'
        '    with path.open("w", encoding="utf-8", newline="") as f:\n'
        '        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")\n'
        '        w.writeheader()\n'
        '        for r in rows:\n'
        '            w.writerow(r)\n'
    )
    new_writer = (
        'def _write_csv(path: Path, rows: list, fieldnames: list = None):\n'
        '    """v1.17 (D81): FAIL-CLOSED, WRITE-ONCE table writer.\n\n'
        '    Refuses to write to an EXISTING target (raises FileExistsError).\n'
        '    Uses EXCLUSIVE-CREATE (``open(..., "x")``) + full-write + fsync so a\n'
        '    scientific table can NEVER be silently overwritten.  The inherited v1.16\n'
        '    ``open(..., "w")`` overwrite semantics are INCOMPATIBLE with the final\n'
        '    one-shot provenance contract and are removed.\n'
        '    """\n'
        '    path.parent.mkdir(parents=True, exist_ok=True)\n'
        '    if path.exists():\n'
        '        raise FileExistsError(\n'
        '            f"V1_17_CSV_FAIL_CLOSED__TARGET_EXISTS__REFUSE_OVERWRITE: {path}")\n'
        '    fields = fieldnames or (list(rows[0].keys()) if rows else [])\n'
        '    # Exclusive-create, write-once; no overwrite path exists.\n'
        '    f = open(path, "x", encoding="utf-8", newline="")  # exclusive-create\n'
        '    try:\n'
        '        if rows:\n'
        '            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")\n'
        '            w.writeheader()\n'
        '            for r in rows:\n'
        '                w.writerow(r)\n'
        '        f.flush()\n'
        '        os.fsync(f.fileno())\n'
        '    finally:\n'
        '        f.close()\n'
    )
    assert old_writer in s, "_write_csv anchor missing"
    s = s.replace(old_writer, new_writer, 1)

    # ------------------------------------------------------------------ #
    # U9 D82: NEW v1.17 release contract (historical v1.14 smoke; no v1.17 smoke)
    # ------------------------------------------------------------------ #
    # Replace the SMOKE_V1_17_ARTIFACT constant meaning with the HISTORICAL smoke.
    old_smoke_const = 'SMOKE_V1_17_ARTIFACT = "reports/audits/phase36_robustness_smoke_v1_17.json"'
    new_smoke_const = (
        '# v1.17 (D82): the runtime release gate binds the HISTORICAL v1.14 smoke as\n'
        '# RUNTIME_SMOKE_EVIDENCE_ONLY.  A v1.17 smoke is NOT required and MUST NOT be\n'
        '# demanded by the gate.  The historical smoke is NOT a claim about D61/D75.\n'
        'HISTORICAL_V1_14_SMOKE = "reports/audits/phase36_robustness_smoke_v1_14.json"\n'
        'HISTORICAL_V1_14_SMOKE_SHA256 = "53543729fb0c48695c2af202c5f3d2f5ebdfc29d87c7a7f100bcde9f94882441"\n'
        'SMOKE_V1_17_ARTIFACT = HISTORICAL_V1_14_SMOKE  # role: HISTORICAL_RUNTIME_SMOKE_EVIDENCE_ONLY'
    )
    assert old_smoke_const in s, "SMOKE_V1_17_ARTIFACT anchor missing"
    s = s.replace(old_smoke_const, new_smoke_const, 1)

    # Replace the smoke-artifact-missing gate branch with the historical-smoke bind.
    old_gate_block = (
        '    smoke_path = ROOT / SMOKE_V1_17_ARTIFACT\n'
        '    if not smoke_path.exists():\n'
        '        ev["reason"] = "SMOKE_ARTIFACT_MISSING"\n'
        '        ev["smoke_artifact"] = SMOKE_V1_17_ARTIFACT\n'
        '        return {"state": "NOT_RELEASED", **ev}'
    )
    assert old_gate_block in s, "smoke-missing gate block anchor missing"
    new_gate_block = (
        '    # v1.17 (D82): bind the HISTORICAL v1.14 smoke as runtime evidence.\n'
        '    # It is present and its raw SHA is pinned; NO v1.17 smoke is required.\n'
        '    smoke_path = ROOT / HISTORICAL_V1_14_SMOKE\n'
        '    if not smoke_path.exists():\n'
        '        ev["reason"] = "HISTORICAL_SMOKE_ARTIFACT_MISSING"\n'
        '        ev["smoke_artifact"] = HISTORICAL_V1_14_SMOKE\n'
        '        return {"state": "NOT_RELEASED", **ev}'
    )
    s = s.replace(old_gate_block, new_gate_block, 1)

    # Replace the smoke-sha mismatch branch to compare against the pinned
    # historical SHA AND the declared attestation field consistently.
    old_sha_block = (
        '    smoke_sha = _sha(smoke_path)\n'
        '    if att.get("smoke_artifact_sha256") != smoke_sha:\n'
        '        ev["reason"] = "SMOKE_ARTIFACT_SHA_MISMATCH"\n'
        '        ev["declared_smoke_artifact_sha256"] = att.get("smoke_artifact_sha256")\n'
        '        ev["observed_smoke_artifact_sha256"] = smoke_sha\n'
        '        return {"state": "NOT_RELEASED", **ev}'
    )
    assert old_sha_block in s, "smoke-sha gate block anchor missing"
    new_sha_block = (
        '    smoke_sha = _sha(smoke_path)\n'
        '    if smoke_sha != HISTORICAL_V1_14_SMOKE_SHA256:\n'
        '        ev["reason"] = "HISTORICAL_SMOKE_SHA_MISMATCH"\n'
        '        ev["observed_smoke_artifact_sha256"] = smoke_sha\n'
        '        ev["expected_smoke_artifact_sha256"] = HISTORICAL_V1_14_SMOKE_SHA256\n'
        '        return {"state": "NOT_RELEASED", **ev}\n'
        '    if att.get("smoke_artifact_sha256") != smoke_sha:\n'
        '        ev["reason"] = "SMOKE_ARTIFACT_SHA_MISMATCH"\n'
        '        ev["declared_smoke_artifact_sha256"] = att.get("smoke_artifact_sha256")\n'
        '        ev["observed_smoke_artifact_sha256"] = smoke_sha\n'
        '        return {"state": "NOT_RELEASED", **ev}'
    )
    s = s.replace(old_sha_block, new_sha_block, 1)

    # ------------------------------------------------------------------ #
    # U10 header provenance note
    # ------------------------------------------------------------------ #
    s = s.replace(
        "#   v1.17 OPERATIONAL/GOVERNANCE REBASE over frozen v1.15 (D80-A..H).",
        "#   v1.17 FINAL OPERATIONAL REPAIR over frozen v1.16 (D81/D82/D83).", 1)
    if "v1.17 FINAL OPERATIONAL REPAIR" not in s:
        s = s.replace(
            "REVISION: ra_medfilm_barr_phase36_robustness_v1_17",
            "REVISION: ra_medfilm_barr_phase36_robustness_v1_17\n"
            "#   v1.17 FINAL OPERATIONAL REPAIR over frozen v1.16 (D81/D82/D83).\n"
            "#   Scientific computation is IDENTICAL to v1.16 (and hence v1.15):\n"
            "#   D61 canonical fusion + D75 POLICY_B.  NO new scientific choice.",
            1)

    # ------------------------------------------------------------------ #
    # Fail-closed post-conditions
    # ------------------------------------------------------------------ #
    assert "C.GATE_ENV" not in s, "residual C.GATE_ENV"
    assert 'V1_17_SCIENCE_GATE_ENV = "PHASE36_V1_17_EXECUTE"' in s
    assert 'PHASE36_V1_17_LAUNCH_AUTHORITY' in s
    # v1.17 namespace present; v1.16 science/smoke namespace absent
    assert "phase36_robustness_science_start_v1_17.json" in s
    assert "phase36_robustness_science_start_v1_16.json" not in s
    assert "phase36_robustness_scientific_result_v1_16.json" not in s
    assert "phase36_v1_16_runtime_source_integrity_manifest.json" not in s
    assert "phase36_v1_17_runtime_source_integrity_manifest.json" in s
    # D81 namespace rebase
    assert 'TAB = ROOT / "reports" / "tables" / "phase36_robustness_v1_17"' in s
    assert 'ARR = ROOT / "reports" / "arrays" / "phase36_robustness_v1_17"' in s
    assert 'FIG = ROOT / "reports" / "figures" / "phase36_robustness_v1_17"' in s
    # D81 fail-closed CSV writer
    assert 'open(path, "x", encoding="utf-8", newline="")' in s
    assert 'V1_17_CSV_FAIL_CLOSED__TARGET_EXISTS__REFUSE_OVERWRITE' in s
    assert 'path.open("w", encoding="utf-8", newline="")' not in s
    # D82 historical smoke bind
    assert "HISTORICAL_V1_14_SMOKE" in s
    assert "53543729fb0c48695c2af202c5f3d2f5ebdfc29d87c7a7f100bcde9f94882441" in s
    assert "HISTORICAL_SMOKE_ARTIFACT_MISSING" in s
    # scientific repairs preserved (IDENTICAL to v1.16)
    assert "fuse_full_field(p_global, refined, geom)" in s
    assert "system._fuse_global_with_regional(p_global, refined, window)" not in s
    assert s.count("_phase27_scored_final_binary(") == 3
    assert "SEGMENTATION_OUTPUT_THRESHOLD = 0.50" in s
    assert "PHASE36_ROBUSTNESS_SCIENCE_V1_17_STAGE_JOURNAL" in s
    assert "_ScienceJournal(" in s
    # only allowed v1_16 residue remains
    residue_lines = [ln for ln in s.splitlines() if ("v1_16" in ln or "V1_16" in ln)]
    for ln in residue_lines:
        assert any(tok in ln for tok in ALLOWED_V1_16_RESIDUE), f"unexpected v1_16 residue: {ln!r}"

    OUT.write_text(s, encoding="utf-8")
    compile(s, str(OUT), "exec")

    print(json.dumps({
        "status": "V1_17_GENERATED",
        "path": str(OUT.relative_to(ROOT)),
        "sha256": sha256_file(OUT),
        "bytes": OUT.stat().st_size,
        "v1_16_residue_lines": residue_lines,
        "namespace_rebased": True,
        "csv_fail_closed": True,
        "historical_smoke_bound": True,
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
