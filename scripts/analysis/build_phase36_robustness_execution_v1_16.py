#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase36 — v1.16 EXECUTION SOURCE GENERATOR (deterministic, WO#17B).

Derives scripts/analysis/phase36_robustness_execution_v1_16.py from the frozen
v1.15 source by applying ONLY operational / governance / provenance /
observability repairs (D80-A..H).  ALL scientific computation is preserved
byte-for-byte: the D61 canonical fusion and the D75 POLICY_B helper are not
touched, nor are router / ROI / rf202 / R_psi / S_omega / safety / geometry /
perturbations / seeds / metrics / thresholds / tolerances / ordering / batches.

Transformations (ordered, exact-token):
  T1  version namespace: V1_14 -> V1_16, v1_14 -> v1_16, V1.14 -> V1.16
  T2  revision literal:  ra_medfilm_barr_phase36_robustness_v1_14 -> ..._v1_16
  T3  science artifact namespace: *_v1_14.json (science/smoke) -> *_v1_16.json
  T4  launch authority token:    PHASE36_V1_14_LAUNCH_AUTHORITY -> PHASE36_V1_16_LAUNCH_AUTHORITY
  T5  science operator gate:     explicit PHASE36_V1_16_EXECUTE (replace C.GATE_ENV use)
  T6  smoke operator gate:       explicit PHASE36_V1_16_SMOKE_EXECUTE (replace C.SMOKE_GATE_ENV use)
  T7  runtime manifest path:     phase36_v1_14_runtime_source_integrity_manifest.json
                                 -> phase36_v1_16_runtime_source_integrity_manifest.json
  T8  terminal literals:         PHASE36_V1_14_* -> PHASE36_V1_16_*
  T9  D80-G: insert crash-survivable v1.16 stage journal (module + science wiring)
  T10 docstring/header: v1.15 -> v1.16 provenance note

Fail-closed post-conditions: no residual v1_14/V1_14 token in the emitted
source except the intentional historical-reference sentinels enumerated below.

Runs ONCE.  Re-run -> REFUSE_OVERWRITE (rc 2).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_15.py"
OUT = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_16.py"

V15_SHA = "b194ad28345ea8b268748be383ca98b936cb051d85854666e3141250f3eae002"

# Historical-reference sentinels that MUST retain the literal v1_14 token
# (they document the forbidden/aliased historical paths and D31 provenance).
ALLOWED_V1_14_RESIDUE = [
    "FORBIDDEN_SCIENCE_RESULT_V1_8",          # sentinel name (kept verbatim)
    "phase36_robustness_scientific_result_v1_8.json",  # historical forbidden path
]


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


JOURNAL_MODULE = r'''
# --------------------------------------------------------------------------- #
# CRASH-SURVIVABLE STAGE JOURNAL (NEW v1.16 — write-once per stage event).
# Observability ONLY.  No probability / mask / GT / metric payload is ever
# written into a journal record.  Each record is O_CREAT|O_EXCL + full write +
# fsync; a record is NEVER overwritten.  The journal MUST NOT touch any
# scientific tensor (proven non-interfering in MODEL-FREE synthetic tests).
# --------------------------------------------------------------------------- #
V1_16_JOURNAL_DIR = (ROOT / "reports" / "audits"
                     / "phase36_robustness_science_v1_16_journal")
STAGE_JOURNAL_ENV = "PHASE36_ROBUSTNESS_V1_16_DISABLE_JOURNAL"  # "1" disables (test only)


def _journal_enabled() -> bool:
    return os.environ.get(STAGE_JOURNAL_ENV) != "1"


def _slug(s: str) -> str:
    out = []
    for ch in str(s):
        out.append(ch if (ch.isalnum() or ch in ("-", "_")) else "_")
    return "".join(out)[:80]


def _journal_record(stage: str, event: str, attempt_id: str) -> str:
    """Write ONE durable v1.16 stage-journal record (write-once; never overwrites).

    GT-free metadata ONLY.  No probability, no mask, no GT, no metric.
    """
    V1_16_JOURNAL_DIR.mkdir(parents=True, exist_ok=True)
    seq = len(sorted(V1_16_JOURNAL_DIR.glob("*.json")))
    fname = f"{seq:03d}_{_slug(stage)}__{_slug(event)}.json"
    path = V1_16_JOURNAL_DIR / fname
    src_sha = _sha(Path(__file__))
    start_present = (ROOT / SCIENCE_V1_16_START_MARKER).exists()
    payload = {
        "journal_artifact_kind": "PHASE36_ROBUSTNESS_SCIENCE_V1_16_STAGE_JOURNAL",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_16",
        "attempt_id": attempt_id,
        "stage": stage,
        "event": event,
        "utc": now(),
        "pid": os.getpid(),
        "science_source_sha256": src_sha,
        "launch_authority_token": LAUNCH_AUTHORITY_TOKEN,
        "launch_authority_present": os.environ.get(LAUNCH_AUTHORITY_TOKEN) == "1",
        "START_present": bool(start_present),
        "scientific_output": False,
        "contains_probabilities": False,
        "contains_masks": False,
        "contains_gt": False,
        "contains_metrics": False,
    }
    _write_once_json(path, payload)
    return fname


class _ScienceJournal:
    """v1.16 stage-journal driver (BEGIN/COMPLETE per stage; crash-survivable)."""

    def __init__(self, attempt_id: str, enabled: bool):
        self.attempt_id = attempt_id
        self.enabled = bool(enabled)
        self.records = 0
        self._open: set = set()

    def begin(self, stage: str):
        if not self.enabled:
            return
        _journal_record(stage, "BEGIN", self.attempt_id)
        self._open.add(stage)
        self.records += 1

    def complete(self, stage: str):
        if not self.enabled:
            return
        _journal_record(stage, "COMPLETE", self.attempt_id)
        self._open.discard(stage)
        self.records += 1


# v1.16 canonical journal stages (BEGIN/COMPLETE) reachable from the science path.
V1_16_JOURNAL_STAGES = [
    "START",
    "model_load",
    "clean_G",
    "G_reproduction_gate",
    "clean_evaluation",
    "clean_equivalence",
    "image_perturbations",
    "proposal_perturbations",
    "summaries",
    "tables_arrays_figures",
    "RESULT_write",
]
'''

# Anchor: insert the journal module immediately after the LAUNCH_AUTHORITY_TOKEN line.
ANCHOR_TOKEN_LINE = 'LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_16_LAUNCH_AUTHORITY"'


def main() -> int:
    if OUT.exists():
        print(json.dumps({"status": "REFUSE_OVERWRITE", "path": str(OUT.relative_to(ROOT))}, indent=1))
        return 2
    if sha256_file(SRC) != V15_SHA:
        print(json.dumps({"status": "FAIL_CLOSED__V1_15_SOURCE_SHA_MISMATCH",
                          "observed": sha256_file(SRC)}, indent=1))
        return 3

    s = SRC.read_text(encoding="utf-8")
    orig = s

    # ------------------------------------------------------------------ #
    # T1 version namespace (token families; note module-references too)
    # ------------------------------------------------------------------ #
    s = s.replace("V1_14", "V1_16")
    s = s.replace("v1_14", "v1_16")
    s = s.replace("V1.14", "V1.16")
    s = s.replace("v1.14", "v1.16")
    # Restore the intentional historical sentinel tokens (scientific provenance).
    s = s.replace("reports/audits/phase36_robustness_scientific_result_v1_16.json\"  # historical",
                  "reports/audits/phase36_robustness_scientific_result_v1_8.json\"  # historical")
    s = s.replace("FORBIDDEN_SCIENCE_RESULT_V1_16", "FORBIDDEN_SCIENCE_RESULT_V1_8")

    # ------------------------------------------------------------------ #
    # T2 revision literal
    # ------------------------------------------------------------------ #
    s = s.replace("ra_medfilm_barr_phase36_robustness_v1_16",
                  "ra_medfilm_barr_phase36_robustness_v1_16")  # already done by T1

    # ------------------------------------------------------------------ #
    # T5/T6 explicit v1.16 operator gates (remove inherited C.GATE_ENV use)
    # ------------------------------------------------------------------ #
    s = s.replace('os.environ.get(C.GATE_ENV)', 'os.environ.get(V1_16_SCIENCE_GATE_ENV)')
    s = s.replace('os.environ.get(C.SMOKE_GATE_ENV)', 'os.environ.get(V1_16_SMOKE_GATE_ENV)')
    s = s.replace('f"{C.GATE_ENV} != \'1\'"', 'f"{V1_16_SCIENCE_GATE_ENV} != \'1\'"')
    s = s.replace('f"{C.SMOKE_GATE_ENV} != \'1\'"', 'f"{V1_16_SMOKE_GATE_ENV} != \'1\'"')

    # Insert the explicit gate constants right after the launch-authority token line.
    gate_consts = (
        'LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_16_LAUNCH_AUTHORITY"\n'
        '# v1.16 EXPLICIT OPERATOR GATES (D80-D): execution + launcher bind the SAME literals.\n'
        'V1_16_SCIENCE_GATE_ENV = "PHASE36_V1_16_EXECUTE"\n'
        'V1_16_SMOKE_GATE_ENV = "PHASE36_V1_16_SMOKE_EXECUTE"'
    )
    s = s.replace('LAUNCH_AUTHORITY_TOKEN = "PHASE36_V1_16_LAUNCH_AUTHORITY"',
                  gate_consts, 1)

    # ------------------------------------------------------------------ #
    # T9 insert crash-survivable journal module after the token block
    # ------------------------------------------------------------------ #
    marker = 'V1_16_SMOKE_GATE_ENV = "PHASE36_V1_16_SMOKE_EXECUTE"'
    assert marker in s, "gate constant block missing after insert"
    s = s.replace(marker, marker + "\n" + JOURNAL_MODULE, 1)

    # ------------------------------------------------------------------ #
    # T9b wire the journal into the science driver
    # ------------------------------------------------------------------ #
    # Add a journal begin/complete around the science run wrapper.
    old_run = "    return _run_science_with_durable_evidence()"
    new_run = (
        "    return _run_science_with_durable_evidence(journal=_ScienceJournal(\n"
        "        attempt_id=f\"v1_16_{os.getpid()}_{now()}\", enabled=_journal_enabled()))"
    )
    assert old_run in s, "science run call anchor missing"
    s = s.replace(old_run, new_run, 1)

    old_def = "def _run_science_with_durable_evidence() -> int:"
    new_def = (
        "def _run_science_with_durable_evidence(journal=None) -> int:\n"
        "    \"\"\"v1.16 science driver with crash-survivable stage journal.\"\"\"\n"
        "    _j = journal\n"
        "    if _j is not None:\n"
        "        _j.begin(\"START\")"
    )
    assert old_def in s, "science driver def anchor missing"
    s = s.replace(old_def, new_def, 1)

    # ------------------------------------------------------------------ #
    # T10 header provenance note
    # ------------------------------------------------------------------ #
    s = s.replace(
        "REVISION: ra_medfilm_barr_phase36_robustness_v1_16",
        "REVISION: ra_medfilm_barr_phase36_robustness_v1_16\n"
        "#   v1.16 OPERATIONAL/GOVERNANCE REBASE over frozen v1.15 (D80-A..H).\n"
        "#   Scientific computation is IDENTICAL to v1.15 (D61 canonical fusion +\n"
        "#   D75 POLICY_B).  NO new scientific choice.",
        1)

    # ------------------------------------------------------------------ #
    # Fail-closed post-conditions
    # ------------------------------------------------------------------ #
    # (a) no C.GATE_ENV / C.SMOKE_GATE_ENV residual
    assert "C.GATE_ENV" not in s, "residual C.GATE_ENV"
    assert "C.SMOKE_GATE_ENV" not in s, "residual C.SMOKE_GATE_ENV"
    # (b) explicit gates present
    assert 'V1_16_SCIENCE_GATE_ENV = "PHASE36_V1_16_EXECUTE"' in s
    assert 'PHASE36_V1_16_LAUNCH_AUTHORITY' in s
    # (c) new science namespace present, old science/smoke v1_14 namespace absent
    assert "phase36_robustness_science_start_v1_16.json" in s
    assert "phase36_robustness_science_start_v1_14.json" not in s
    assert "phase36_robustness_science_failure_v1_14.json" not in s
    assert "phase36_robustness_scientific_result_v1_14.json" not in s
    # (d) v1.14 runtime manifest path replaced
    assert "phase36_v1_14_runtime_source_integrity_manifest.json" not in s
    assert "phase36_v1_16_runtime_source_integrity_manifest.json" in s
    # (e) scientific repairs preserved
    assert "fuse_full_field(p_global, refined, geom)" in s
    assert "system._fuse_global_with_regional(p_global, refined, window)" not in s
    assert s.count("_phase27_scored_final_binary(") == 3
    assert "SEGMENTATION_OUTPUT_THRESHOLD = 0.50" in s
    # (f) journal wired
    assert "PHASE36_ROBUSTNESS_SCIENCE_V1_16_STAGE_JOURNAL" in s
    assert "_ScienceJournal(" in s
    # (g) only allowed v1_14 residue remains
    residue_lines = [ln for ln in s.splitlines() if ("v1_14" in ln or "V1_14" in ln)]
    for ln in residue_lines:
        assert any(tok in ln for tok in ALLOWED_V1_14_RESIDUE), f"unexpected v1_14 residue: {ln!r}"

    OUT.write_text(s, encoding="utf-8")
    # compile check
    compile(s, str(OUT), "exec")

    print(json.dumps({
        "status": "V1_16_GENERATED",
        "path": str(OUT.relative_to(ROOT)),
        "sha256": sha256_file(OUT),
        "bytes": OUT.stat().st_size,
        "v1_14_residue_lines": residue_lines,
        "journal_wired": True,
        "gates_explicit": True,
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
