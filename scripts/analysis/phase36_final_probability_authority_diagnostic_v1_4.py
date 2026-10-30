#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.4
(D61 REPAIR-PROOF REPLAY WITH CRASH-SURVIVABLE OBSERVABILITY).

ADDITIVE revision of the v1.3 family
(``ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_4``).

v1.0 remains byte-for-byte frozen (FROZEN_NEVER_CONSUMED_NOT_AUTHORIZED).
v1.1 was executed exactly once and is CONSUMED_FAILED (retry FORBIDDEN).
v1.2 was executed exactly once and is CONSUMED_RESULT  (retry FORBIDDEN).
v1.3 was executed exactly once and is CONSUMED_TERMINAL_EVIDENCE_ANOMALY
     (D67; retry FORBIDDEN; root cause UNRESOLVED).  v1.4 is NOT a v1.3 retry.

Purpose (UNCHANGED from v1.3): GT-FREE determination of whether the frozen clean
end-to-end system, with the D61 canonical Phase27 ACCEPT-fusion repair, reproduces
the Phase27 FINAL persisted float16 prediction authority

    data_cache/phase27_barr_preservation_v1_0/phase27_val808_final_prob_f16.npy

SCIENTIFIC PATH IS IDENTICAL TO v1.3.  The ACCEPT branch calls the canonical
PAD-AWARE module-level Phase27 semantics

    _FROZEN_MOD.fuse_full_field(p_global, refined, geom)

with the SAME ``geom`` object produced by the canonical ROI path and the SAME
``refined`` array produced by the canonical R_psi forward.  The PAD-UNAWARE model
method ``system._fuse_global_with_regional(...)`` MUST remain ABSENT from the
repaired ACCEPT path (D61).  NO threshold / tolerance / sample-order / G / router /
ROI / R_psi / S_omega / f32->f16 comparison change.

THE ONLY CHANGES FROM v1.3 (observability, NOT science):
  1. crash-survivable STAGE JOURNAL   (write-once file per stage event under
     ``reports/audits/phase36_final_probability_authority_diagnostic_v1_4_journal/``);
  2. crash-survivable PROGRESS JOURNAL during the 808 clean-row loop
     (sparse GT-free checkpoints; no probabilities, no masks, no GT, no metrics);
  3. durable process/exit evidence produced by the companion supervisor
     (``supervise_..._v1_4.py``; never created or altered by this module);
  4. stronger terminal-evidence handling (journal-derived last durable stage
     recorded in the failure artifact).

Journaling is purely additive instrumentation: it NEVER writes, mutates or reads a
scientific tensor, and it cannot change a probability.  The D70 non-interference
test proves the journaling does not perturb the scientific core.

``scientific_output`` is False and ``robustness_result`` is False.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import socket
import sys
import traceback
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts" / "analysis") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

# --------------------------------------------------------------------------- #
# diagnostic-native authority tokens (v1.4)
# --------------------------------------------------------------------------- #
ONE_SHOT_ENV = "PHASE36_FINAL_PROB_AUTHORITY_EXECUTE"
LAUNCH_AUTHORITY_TOKEN = "PHASE36_FINAL_PROB_AUTHORITY_V1_4_LAUNCH_AUTHORITY"
FOREIGN_V1_14_LAUNCH_TOKEN = "PHASE36_V1_14_LAUNCH_AUTHORITY"

DIAGNOSTIC_REVISION = "ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_4"

FROZEN_V1_14_SOURCE = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
FROZEN_V1_14_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
FROZEN_V1_14_MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

DIAGNOSTIC_START = ROOT / "reports" / "audits" / "phase36_final_probability_authority_diagnostic_start_v1_4.json"
DIAGNOSTIC_RESULT = ROOT / "reports" / "audits" / "phase36_final_probability_authority_diagnostic_result_v1_4.json"
DIAGNOSTIC_FAILURE = ROOT / "reports" / "audits" / "phase36_final_probability_authority_diagnostic_failure_v1_4.json"

# ---- crash-survivable observability (NEW v1.4) ---------------------------- #
JOURNAL_DIR = (ROOT / "reports" / "audits"
               / "phase36_final_probability_authority_diagnostic_v1_4_journal")
STAGE_JOURNAL_ENV = "PHASE36_FINAL_PROB_AUTHORITY_DISABLE_JOURNAL"  # "1" disables (D70 only)

# ---- frozen v1.3 authorities (forensic binding; unchanged) ---------------- #
FROZEN_V1_3_DIAGNOSTIC_SHA = "b32a9db41a53b5007c6b9989bdbee22a0b7ea14587d222a3399980142dd9621e"
FROZEN_V1_3_LAUNCHER_SHA = "d5f9cd3dff302c849d195d909f6f2c9a59fbbbaaf359d859e69442d9fe05b504"
V1_3_START_SHA = "b984d09bf3a266de8d75b39b6ad2ff3236cce09915a7f2a5c874813af8c3c1c5"
EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

# D67/D68 PRESERVATION (v1.4 must NOT reinterpret the v1.3 anomaly).
D67_CLASSIFICATION = "POST_START_TERMINAL_EVIDENCE_ANOMALY"
D67_ATTEMPT_STATE = "CONSUMED_TERMINAL_EVIDENCE_ANOMALY"
D67_ROOT_CAUSE = "UNRESOLVED"
D67_TERMINATION_MECHANISM = "UNRESOLVED"
D68_CLASSIFICATION = "D67_TERMINAL_WRITE_REACH_OVERCLAIM"
D68_STATUS = "RECONCILED"
V1_3_STATE = "CONSUMED_TERMINAL_EVIDENCE_ANOMALY"
V1_3_RETRY = "FORBIDDEN"

# D66 remediation: the Phase27 score SHA is DERIVED from ONE canonical source
# constant and is NEVER re-typed downstream.  The canonical source is the frozen
# v1.3 launcher's re-used v1.2 dependency (``check_final_authority_preconsumption``),
# which carries the CORRECT value; this module also stores it ONCE.
PHASE27_SCORES_CSV = ROOT / "reports" / "tables" / "phase27_val808_per_sample_scores.csv"
# CANONICAL SOURCE CONSTANT (D66 remediation): this is the SINGLE place the Phase27
# score SHA is written.  It MUST NOT be manually retyped anywhere else in the v1.4
# family; downstream artifacts DERIVE it (hash the authority file programmatically
# or import this constant).  The value is assembled below from parts so that the
# incorrect historical transcription can never be introduced by copy/paste.
_P27_SCORES_CSV_SHA_PARTS = (
    "702133930ce14ac9513c992833396e3e250d08417",
    "b17d1032cbd260a405cfb12",   # NOTE: index 41 is 'b' (CORRECT), not 'a'
)
PHASE27_SCORES_CSV_SHA_CANONICAL = "".join(_P27_SCORES_CSV_SHA_PARTS)

# Phase27 FINAL persisted float16 prediction authority (the reproduction target).
PHASE27_FINAL_PROB_AUTHORITY = OrderedDict([
    ("path", "data_cache/phase27_barr_preservation_v1_0/phase27_val808_final_prob_f16.npy"),
    ("sha256", "506ab6c4e715a9106889e186c146b73903493c80a63258007954cf5deb3ea9cf"),
    ("shape", [808, 512, 512]),
    ("dtype", "float16"),
    ("sample_order", "frozen VAL808 population order (dataset asc, sample_id asc)"),
    ("role", "Phase27 frozen FINAL probability cache (authoritative reproduction target)"),
])
PHASE27_GLOBAL_PROB_AUTHORITY = OrderedDict([
    ("path", "data_cache/phase27_barr_preservation_v1_0/phase27_val808_global_prob_f16.npy"),
    ("sha256", "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13"),
    ("shape", [808, 512, 512]),
    ("dtype", "float16"),
])

SEGMENTATION_OUTPUT_THRESHOLD = 0.50
F16_HALF = np.float16(0.5)

# Prior-failure provenance (unchanged from the v1.0/v1.1/v1.2/v1.3 line).
PRIOR_FAILURE_PROVENANCE = OrderedDict([
    ("v1_14_science_start", OrderedDict([
        ("path", "reports/audits/phase36_robustness_science_start_v1_14.json"),
        ("sha256", "e2c42b05f4fd0450022d7bcde091c0bea13638788b4f83a123016ab894630e0a")])),
    ("v1_14_science_failure", OrderedDict([
        ("path", "reports/audits/phase36_robustness_science_failure_v1_14.json"),
        ("sha256", "0fcc3c211d7bcd53b4f8e53d7b09f518fd83a929e8a979c7174762958fff754b")])),
    ("v1_14_forensic_adjudication", OrderedDict([
        ("path", "reports/audits/phase36_v1_14_science_failure_forensic_adjudication.json"),
        ("sha256", "f1d4712ae7b3f0b333a22c852f99d6b3812218ffb258f8f58ddba62c7193c17e")])),
    ("forensic_reconciliation_v2", OrderedDict([
        ("path", "reports/audits/phase36_v1_14_science_failure_forensic_reconciliation_v2.json"),
        ("sha256", "cc9a3b502f59e3855c395b9d6afa2f5616f513d60af4756e4477a9370889cc3c")])),
    ("targeted_static_audit", OrderedDict([
        ("path", "reports/audits/phase36_clean_equivalence_targeted_static_audit_v1_0.json"),
        ("sha256", "8def086c44a7e80461c729f41ab61c0be347ef1589c94d6884a082adbde64ed4")])),
])
REQUIRED_STATIC_AUDIT_VERDICT = "STATIC_ROOT_CAUSE_NOT_ESTABLISHED"

# Consumed-evidence binding: the v1.2 clean-eq attempt + the D51 line.
CONSUMED_EVIDENCE_PROVENANCE = OrderedDict([
    ("v1_2_start_marker", OrderedDict([
        ("path", "reports/audits/phase36_clean_equivalence_diagnostic_start_v1_2.json"),
        ("sha256", "be93d494b1aa2aad3c900f442c16efe55bcbf0bd508a72df8f8b83e72cd7d2d3")])),
    ("v1_2_result", OrderedDict([
        ("path", "reports/audits/phase36_clean_equivalence_diagnostic_result_v1_2.json"),
        ("sha256", "b64f7e6282f9abb864a5d5bc438a22e1096aaf56e0a4e94fe53ba7c9bab6fa4a")])),
    ("d51_adjudication_v1_0", OrderedDict([
        ("path", "reports/audits/phase36_clean_equivalence_d51_numerical_authority_adjudication_v1_0.json"),
        ("sha256", "27ac7ada4ee39190d8823b8b1ff7e6e2beb304e2e7fc5778542883ac7eacc53a")])),
    ("d51_reconciliation_v1_1", OrderedDict([
        ("path", "reports/audits/phase36_clean_equivalence_d51_reconciliation_v1_1.json"),
        ("sha256", "d8e3e83e6c31004e610faef9d93c221c026eb8974c033f47fbff91106836758b")])),
])

# v1.1 CONSUMED evidence (bound BEFORE v1.4 consumption).
V1_1_CONSUMED_EVIDENCE = OrderedDict([
    ("v1_1_start", OrderedDict([
        ("path", "reports/audits/phase36_final_probability_authority_diagnostic_start_v1_1.json"),
        ("sha256", "0bfb452ef81e6e0c8880d9b333abcb6514dff7dbb3a37476da3242beeab73aec")])),
    ("v1_1_failure", OrderedDict([
        ("path", "reports/audits/phase36_final_probability_authority_diagnostic_failure_v1_1.json"),
        ("sha256", "9f1b38431228ec584150da37501199ea580b26339be6d8e20a2fcba72b5cd960")])),
    ("d56_failure_adjudication", OrderedDict([
        ("path", "reports/audits/phase36_final_probability_authority_diagnostic_v1_1_failure_adjudication_v1_0.json"),
        ("sha256", "b796cc8d49df32513d2c6a4c5700a253d66a49e171def1772e1617ff4855fc80")])),
])
V1_1_RESULT_PATH = "reports/audits/phase36_final_probability_authority_diagnostic_result_v1_1.json"

REQUIRED_V1_1_FAILURE_PREDICATES = OrderedDict([
    ("termination_kind", "EXCEPTION"),
    ("exception_type", "TypeError"),
    ("exception_message", "'module' object is not subscriptable"),
    ("failing_stage", "run_diagnostic"),
    ("marker_consumed", True),
    ("VAL_GT_READ", 0),
    ("final_authority_computed", False),
    ("result_write_attempted", False),
])

# v1.2 CONSUMED evidence (bound BEFORE v1.4 consumption; D61 provenance).
V1_2_CONSUMED_EVIDENCE = OrderedDict([
    ("v1_2_start", OrderedDict([
        ("path", "reports/audits/phase36_final_probability_authority_diagnostic_start_v1_2.json"),
        ("sha256", "88723028df230a8b1e2c98c8c248d2de44e73bcb95669efd9bd8d44cff4a69be")])),
    ("v1_2_result", OrderedDict([
        ("path", "reports/audits/phase36_final_probability_authority_diagnostic_result_v1_2.json"),
        ("sha256", "4a3753867e72f7cfbc357511475623bd0ecfff2dc0e3aca0f16ecbe1effa98d5")])),
    ("v1_2_result_adjudication_v1_0", OrderedDict([
        ("path", "reports/audits/phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_v1_0.json"),
        ("sha256", "562e238c5a1ce0581ed1eb1f763f0172826af0653753cfef6346528c1206ec1b")])),
    ("v1_2_result_adjudication_reconciliation_v1_1", OrderedDict([
        ("path", "reports/audits/phase36_final_probability_authority_diagnostic_v1_2_result_adjudication_reconciliation_v1_1.json"),
        ("sha256", "a85aaf4a0668effaecb148c3ada7a8f25c1bcd0216740e0c009df2115a3833bb")])),
])
V1_2_FAILURE_PATH = "reports/audits/phase36_final_probability_authority_diagnostic_failure_v1_2.json"

REQUIRED_V1_2_RESULT_PREDICATES = OrderedDict([
    ("classification", "D51_END_TO_END_FINAL_AUTHORITY_NOT_REPRODUCED"),
    ("final_f16_bit_identical_all", False),
    ("n_samples_with_any_f16_difference", 266),
    ("total_f16_element_mismatch_count", 28950719),
    ("max_abs_f16_difference", 0.9999996423721313),
    ("VAL_GT_READ", 0),
])

REQUIRED_D60_RECONCILED = "FINAL_AUTHORITY_MISMATCH_EXACTLY_LOCALIZED_TO_PHASE27_ACCEPT_FINAL_SOURCE"
REQUIRED_D61_CLASSIFICATION = "ACCEPT_FINAL_FUSION_SEMANTICS_DIVERGE_FROM_PHASE27"
REQUIRED_D61_STATUS = "ESTABLISHED"

# v1.3 CONSUMED evidence + D67/D68 adjudication authorities (bound BEFORE v1.4).
V1_3_CONSUMED_EVIDENCE = OrderedDict([
    ("v1_3_start", OrderedDict([
        ("path", "reports/audits/phase36_final_probability_authority_diagnostic_start_v1_3.json"),
        ("sha256", V1_3_START_SHA)])),
    ("d67_terminal_anomaly_adjudication_v1_0", OrderedDict([
        ("path", "reports/audits/phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_v1_0.json"),
        ("sha256", "3d3f943c19d5b419fb00bcf19748c0dd41ff8002ef26a4a3c51ad32ef6afecd5")])),
    ("d68_terminal_anomaly_reconciliation_v1_1", OrderedDict([
        ("path", "reports/audits/phase36_final_probability_authority_diagnostic_v1_3_terminal_evidence_anomaly_adjudication_reconciliation_v1_1.json"),
        ("sha256", "f6bbe602c5928e39d160629688cf697a73f65941a5d24d13c5ad4008a8dc0fc2")])),
    ("d66_governance_reconciliation_v1_0", OrderedDict([
        ("path", "reports/audits/phase36_final_probability_authority_diagnostic_v1_3_governance_reconciliation_v1_0.json"),
        ("sha256", "b0c01e40c4764514a01a9f082483a071634a0630d6c4c4640e1bb4ac2f829303")])),
])
V1_3_RESULT_PATH = "reports/audits/phase36_final_probability_authority_diagnostic_result_v1_3.json"
V1_3_FAILURE_PATH = "reports/audits/phase36_final_probability_authority_diagnostic_failure_v1_3.json"

# GT-content callables of the frozen module that MUST NEVER execute.
GT_FORBIDDEN_CALLABLES = ("_load_val_gt", "full_field_gt", "_dice", "_iou", "_hd95")

GT_CONTENT_INVARIANT = OrderedDict([
    ("no_mask_file_opened", True),
    ("no_Image_open_on_mask_path", True),
    ("_load_val_gt_never_executes", True),
    ("full_field_gt_never_executes", True),
    ("_dice_never_executes", True),
    ("_iou_never_executes", True),
    ("_hd95_never_executes", True),
    ("VAL_GT_READ_remains_zero", True),
    ("mask_path_metadata_validation_permitted", True),
])

D50_REASON = "FROZEN_V1_14_GATE_CONTAINS_FOREIGN_LAUNCH_AUTHORITY_SEMANTICS"

V14_SCIENCE_MARKERS = (
    ROOT / "reports" / "audits" / "phase36_robustness_science_start_v1_14.json",
    ROOT / "reports" / "audits" / "phase36_robustness_scientific_result_v1_14.json",
    ROOT / "reports" / "audits" / "phase36_robustness_science_failure_v1_14.json",
)

TERMINAL_RESULT_WRITE_FAILED = "TERMINAL_EVIDENCE_ANOMALY__RESULT_WRITE_FAILED_AFTER_COMPUTATION"
TERMINAL_NONFINITE = "TERMINAL_NONFINITE_FINAL_PROBABILITY__FAIL_CLOSED"

# D61 repair identity (recorded in every artifact) — IDENTICAL to v1.3.
D61_REPAIR_CLASSIFICATION = "D61_CANONICAL_ACCEPT_FUSION_REPAIR"
D61_CANONICAL_ACCEPT_CALL = "fuse_full_field(p_global, refined, geom)"
D61_OLD_ACCEPT_CALL = "system._fuse_global_with_regional(p_global, refined, window)"

# D61 replay classification (the scientific purpose is unchanged from v1.3).
D61_REPLAY_TOKEN = "PHASE36_FINAL_PROB_AUTHORITY_V1_4_D61_REPAIR_PROOF_REPLAY"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _import_frozen_v1_14():
    """Import the frozen v1.14 module by path (never mutating the source)."""
    if sha256_file(FROZEN_V1_14_SOURCE) != FROZEN_V1_14_EXEC_SHA:
        raise SystemExit(
            "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__FROZEN_V1_14_SOURCE_SHA_MISMATCH"
            "__NO_ATTEMPT_CONSUMED")
    spec = importlib.util.spec_from_file_location("_p36_v1_14_frozen_fpa_v14", FROZEN_V1_14_SOURCE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_p36_v1_14_frozen_fpa_v14"] = mod
    spec.loader.exec_module(mod)
    return mod


def _new_runtime_state() -> dict:
    """SHARED mutable runtime-evidence state (D53/D54 + v1.4 journal)."""
    return {
        "VAL_GT_READ": 0,
        "blocked_gt_calls": [],
        "final_authority_computed": False,
        "final_authority_comparison": None,
        "classification": None,
        "nonfinite_samples": {},
        "nonfinite_final_probability": False,
        "result_write_attempted": False,
        "result_write_completed": False,
        "terminal_classification": None,
        # v1.4: journal-derived terminal evidence
        "journal_last_durable_stage": None,
        "journal_last_complete_stage": None,
        "journal_first_started_not_completed_stage": None,
        "journal_records_written": 0,
    }


def _install_gt_guards(mod, runtime_state: dict) -> dict:
    """RUNTIME GT-CONTENT PROHIBITION (D53-aware)."""
    guard = {"installed": []}

    def _make_blocked(name):
        def _blocked(*_a, **_k):
            runtime_state["VAL_GT_READ"] = int(runtime_state.get("VAL_GT_READ", 0)) + 1
            runtime_state.setdefault("blocked_gt_calls", []).append(name)
            raise SystemExit(
                "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__GT_ACCESS_FORBIDDEN::"
                + name)
        return _blocked

    for name in GT_FORBIDDEN_CALLABLES:
        if hasattr(mod, name):
            setattr(mod, name, _make_blocked(name))
            guard["installed"].append(name)
    return guard


def _write_once_json(path: Path, payload: dict) -> bool:
    """Exclusive-create write of a JSON payload (durable, loud on short write)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=1, ensure_ascii=False, default=str).encode("utf-8")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        total = 0
        while total < len(data):
            n = os.write(fd, data[total:])
            if n is None or n <= 0:
                raise OSError(f"SHORT_WRITE at offset {total} of {len(data)} for {path}")
            total += n
        if total != len(data):
            raise OSError(f"SHORT_WRITE total={total} expected={len(data)} for {path}")
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(data):
        raise OSError(f"POST_WRITE_SIZE_MISMATCH for {path}")
    return True


# --------------------------------------------------------------------------- #
# CRASH-SURVIVABLE STAGE JOURNAL (NEW v1.4 — write-once per stage event)
# --------------------------------------------------------------------------- #
def _journal_enabled() -> bool:
    return os.environ.get(STAGE_JOURNAL_ENV) != "1"


def _journal_record(stage: str, event: str, attempt_id: str, revision: str, *, extra=None) -> str:
    """Write ONE durable stage-journal record (write-once; never overwrites).

    Returns the record filename.  The record is GT-free metadata ONLY: no
    probability, no mask, no GT, no metric.  Uses O_CREAT|O_EXCL + full write +
    fsync.  A journal write is instrumentation: it MUST NOT touch any scientific
    tensor.
    """
    seq = len(sorted(JOURNAL_DIR.glob("*.json"))) if JOURNAL_DIR.exists() else 0
    stage_s = _slug(stage)
    fname = f"{seq:03d}_{stage_s}__{_slug(event)}.json"
    path = JOURNAL_DIR / fname
    start_present = DIAGNOSTIC_START.exists()
    payload = OrderedDict([
        ("journal_artifact_kind", "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_V1_4_STAGE_JOURNAL"),
        ("revision", revision),
        ("attempt_id", attempt_id),
        ("stage", stage),
        ("event", event),
        ("utc", now()),
        ("pid", os.getpid()),
        ("host", socket.gethostname()),
        ("diagnostic_source_sha256", sha256_file(Path(__file__))),
        ("launcher_source_sha256", os.environ.get("PHASE36_FINAL_PROB_AUTHORITY_LAUNCHER_SHA256")),
        ("START_sha256_if_START_exists", (sha256_file(DIAGNOSTIC_START) if start_present else None)),
        ("START_present", bool(start_present)),
        ("scientific_output", False),
        ("contains_probabilities", False),
        ("contains_masks", False),
        ("contains_gt", False),
        ("contains_metrics", False),
    ])
    if extra:
        payload["detail"] = extra
    _write_once_json(path, payload)
    return fname


def _slug(s: str) -> str:
    out = []
    for ch in str(s):
        out.append(ch if (ch.isalnum() or ch in ("-", "_")) else "_")
    return "".join(out)[:80]


class _Journal:
    """Stage journal driver (BEGIN/COMPLETE per stage; crash-survivable)."""

    def __init__(self, attempt_id: str, revision: str, enabled: bool):
        self.attempt_id = attempt_id
        self.revision = revision
        self.enabled = bool(enabled)
        self.last_durable_stage = None
        self.last_complete_stage = None
        self.first_started_not_completed = None
        self._open: set = set()
        self.records = 0

    def begin(self, stage: str, *, extra=None):
        if not self.enabled:
            return
        _journal_record(stage, "BEGIN", self.attempt_id, self.revision, extra=extra)
        self.records += 1
        self._open.add(stage)
        self.last_durable_stage = stage
        if self.first_started_not_completed is None:
            self.first_started_not_completed = stage

    def complete(self, stage: str, *, extra=None):
        if not self.enabled:
            return
        _journal_record(stage, "COMPLETE", self.attempt_id, self.revision, extra=extra)
        self.records += 1
        self._open.discard(stage)
        self.last_durable_stage = stage
        self.last_complete_stage = stage
        if self.first_started_not_completed == stage:
            self.first_started_not_completed = None

    def progress(self, stage: str, *, extra=None):
        if not self.enabled:
            return
        _journal_record(stage, "PROGRESS", self.attempt_id, self.revision, extra=extra)
        self.records += 1
        self.last_durable_stage = stage

    def snapshot(self) -> dict:
        return {
            "journal_enabled": self.enabled,
            "journal_dir": str(JOURNAL_DIR.relative_to(ROOT)),
            "records_written": self.records,
            "last_durable_stage": self.last_durable_stage,
            "last_complete_stage": self.last_complete_stage,
            "first_started_not_completed_stage": self.first_started_not_completed,
            "open_stages": sorted(self._open),
        }


def _write_failure(*, termination_kind, runtime_state=None, exc_type=None, exc_msg=None,
                   failing_stage=None, extra=None, marker_consumed=True) -> bool:
    """Durable failure artifact.  D53/D54 + v1.4 journal-derived terminal evidence."""
    if DIAGNOSTIC_FAILURE.exists():
        print(json.dumps({"note": "FAILURE_ARTIFACT_ALREADY_EXISTS",
                          "path": str(DIAGNOSTIC_FAILURE)}))
        return False
    rs = runtime_state if runtime_state is not None else _new_runtime_state()

    partial_present = DIAGNOSTIC_RESULT.exists()
    partial_size = DIAGNOSTIC_RESULT.stat().st_size if partial_present else None
    partial_sha = (sha256_file(DIAGNOSTIC_RESULT) if partial_present else None)

    payload = {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_FAILURE",
        "revision": DIAGNOSTIC_REVISION,
        "automatic_retry": False,
        "overwrite_permitted": False,
        "termination_kind": termination_kind,
        "terminal_classification": rs.get("terminal_classification"),
        "exception": exc_type is not None,
        "exception_type": exc_type,
        "exception_message": exc_msg,
        "failing_stage": failing_stage,
        "marker_consumed": bool(marker_consumed),
        "VAL_GT_READ": int(rs.get("VAL_GT_READ", 0)),
        "blocked_gt_calls": list(rs.get("blocked_gt_calls", [])),
        "final_authority_computed": bool(rs.get("final_authority_computed", False)),
        "final_authority_comparison": rs.get("final_authority_comparison"),
        "classification": rs.get("classification"),
        "nonfinite_samples": dict(rs.get("nonfinite_samples", {})),
        "nonfinite_final_probability": bool(rs.get("nonfinite_final_probability", False)),
        "result_write_attempted": bool(rs.get("result_write_attempted", False)),
        "result_write_completed": bool(rs.get("result_write_completed", False)),
        "partial_result_present": bool(partial_present),
        "partial_result_size": partial_size,
        "partial_result_sha256": partial_sha,
        "runtime_state": _failure_runtime_state(rs),
        # v1.4 — journal-derived terminal evidence (stronger than v1.3)
        "journal_last_durable_stage": rs.get("journal_last_durable_stage"),
        "journal_last_complete_stage": rs.get("journal_last_complete_stage"),
        "journal_first_started_not_completed_stage":
            rs.get("journal_first_started_not_completed_stage"),
        "journal_records_written": int(rs.get("journal_records_written", 0)),
        "journal_dir": str(JOURNAL_DIR.relative_to(ROOT)),
        "d50_foreign_gate_call_omitted": True,
        "d50_reason": D50_REASON,
        "foreign_v1_14_launch_token_present": os.environ.get(FOREIGN_V1_14_LAUNCH_TOKEN) == "1",
        "frozen_v1_14_exec_source_sha256": FROZEN_V1_14_EXEC_SHA,
        "frozen_v1_14_manifest_sha256": FROZEN_V1_14_MANIFEST_SHA,
        "d61_repair_classification": D61_REPAIR_CLASSIFICATION,
        "gt_content_invariant": dict(GT_CONTENT_INVARIANT),
        "scientific_output": False,
        "robustness_result": False,
        "perturbation_executed": False,
        "generated_utc": now(),
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync (exclusive-create, write-once)",
    }
    if extra:
        payload.update(extra)
    try:
        _write_once_json(DIAGNOSTIC_FAILURE, payload)
        return True
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": "FAILURE_ARTIFACT_WRITE_FAILED",
                          "exception_type": type(exc).__name__,
                          "exception_message": str(exc)}, indent=1))
        return False


def _failure_runtime_state(rs: dict) -> dict:
    """Runtime state as recorded in a failure artifact (comparison included)."""
    return {
        "VAL_GT_READ": int(rs.get("VAL_GT_READ", 0)),
        "blocked_gt_calls": list(rs.get("blocked_gt_calls", [])),
        "final_authority_computed": bool(rs.get("final_authority_computed", False)),
        "final_authority_comparison": rs.get("final_authority_comparison"),
        "classification": rs.get("classification"),
        "nonfinite_samples": dict(rs.get("nonfinite_samples", {})),
        "nonfinite_final_probability": bool(rs.get("nonfinite_final_probability", False)),
        "result_write_attempted": bool(rs.get("result_write_attempted", False)),
        "result_write_completed": bool(rs.get("result_write_completed", False)),
        "terminal_classification": rs.get("terminal_classification"),
        "journal_last_durable_stage": rs.get("journal_last_durable_stage"),
        "journal_last_complete_stage": rs.get("journal_last_complete_stage"),
        "journal_first_started_not_completed_stage":
            rs.get("journal_first_started_not_completed_stage"),
    }


# --------------------------------------------------------------------------- #
# FINITE-PROBABILITY HARDENING (pure helpers — unit-testable without a model)
# --------------------------------------------------------------------------- #
def _finite_check(final_prob) -> bool:
    """True iff every element is finite (no NaN / +inf / -inf)."""
    return bool(np.isfinite(np.asarray(final_prob, dtype=np.float32)).all())


def _record_nonfinite(runtime_state: dict, sid, final_prob) -> int:
    """Record a non-finite sample (id + element count) into the shared state."""
    n = int(np.count_nonzero(~np.isfinite(np.asarray(final_prob, dtype=np.float32))))
    runtime_state.setdefault("nonfinite_samples", {})[sid] = n
    runtime_state["nonfinite_final_probability"] = True
    return n


# --------------------------------------------------------------------------- #
# D61 REPAIR — canonical-Phase27 ACCEPT-fusion core (IDENTICAL to v1.3).
# --------------------------------------------------------------------------- #
def _repaired_canonical_learned_core(ctx, image_b, task_id, *,
                                     g_logits=None, g_probability=None, g_taps=None,
                                     p_global_override=None,
                                     router_features_202_override=None,
                                     proposal_geometry=None,
                                     roi_window=None,
                                     action_available=None,
                                     forced_delta_hat_final=None,
                                     forced_s_omega_logit=None,
                                     counters=None) -> dict:
    """Faithful transcription of frozen v1.14 ``canonical_learned_core`` with the
    ACCEPT-branch fusion restored to the canonical Phase27 ``fuse_full_field``.

    IDENTICAL scientific path to v1.3 (D61 repair).  Journaling is NOT performed
    inside this function — instrumentation is external and cannot touch a tensor.
    """
    import torch
    mod = _FROZEN_MOD
    from src.models.barr.ra_medfilm_barr import (canonical_utility,
                                                 TAU_C8_FINAL_FLOAT)
    system = ctx["system"]
    device = ctx["device"]
    counters = counters if counters is not None else {}
    task_id = int(task_id)
    g_forwards = 0
    actual_r_psi_forwards = 0
    actual_s_omega_forwards = 0
    policy_control = bool(forced_delta_hat_final is not None
                          or forced_s_omega_logit is not None)
    forced_router_score = bool(forced_delta_hat_final is not None)
    forced_safety_logit = bool(forced_s_omega_logit is not None)

    # ---- STEP 1: GLOBAL STAGE (canonical numerical semantics) -------------- #
    if p_global_override is not None:
        p_global = np.asarray(p_global_override, dtype=np.float32)
        taps = g_taps
    else:
        if g_logits is None:
            x = image_b if torch.is_tensor(image_b) else torch.from_numpy(
                np.ascontiguousarray(np.asarray(image_b, dtype=np.float32)))
            if x.ndim == 3:
                x = x[None]
            x = x.to(device)
            t = torch.tensor([task_id], dtype=torch.long, device=device)
            out = mod.canonical_g_forward_batched(ctx, x, t)
            logits = out["logits"][0]
            p_global = np.asarray(out["probability"][0], dtype=np.float32)
            taps = {k: v[0] for k, v in out["taps"].items()}
            g_forwards = 1
        else:
            logits = np.asarray(g_logits, dtype=np.float32)
            taps = g_taps
            p_global = (np.asarray(g_probability, dtype=np.float32)
                        if g_probability is not None
                        else mod.canonical_probability_from_logits(logits))
    counters["g_forwards"] = counters.get("g_forwards", 0) + g_forwards

    # ---- STEP 2: ROI geometry (GT-free, 0.30 proposal threshold) ----------- #
    if proposal_geometry is not None:
        geom = dict(proposal_geometry)
        window = (int(geom["clip_y1"]), int(geom["clip_y2"]),
                  int(geom["clip_x1"]), int(geom["clip_x2"]))
    else:
        geom = mod._roi_geometry_from_prob(p_global, mod.ROI_PROPOSAL_THRESHOLD,
                                           mod.ROI_FRACTIONAL_MARGIN)
        window = (None if geom is None else
                  (int(geom["clip_y1"]), int(geom["clip_y2"]),
                   int(geom["clip_x1"]), int(geom["clip_x2"])))
    if roi_window is not None:
        window = roi_window
    available = (geom is not None) if action_available is None else bool(action_available)

    # ---- STEP 3: canonical 202-D ------------------------------------------ #
    if router_features_202_override is not None:
        rf202 = np.asarray(router_features_202_override, dtype=np.float32).reshape(-1)
    else:
        if taps is None:
            raise ValueError("CANONICAL_CORE_REQUIRES_202D_OR_G_TAPS")
        roi_row = mod._geo_row(geom) if geom is not None else mod._roi_row_from_window(
            0, p_global.shape[0], 0, p_global.shape[1], p_global.shape[0])
        rf202 = mod._assemble_202d(taps, p_global, roi_row)

    rf202 = np.asarray(rf202, dtype=np.float32).reshape(-1)
    if rf202.shape != (mod.ROUTER_NUMERIC_DIM,):
        raise ValueError(f"ROUTER_VECTOR_DIM_VIOLATION: {rf202.shape} != ({mod.ROUTER_NUMERIC_DIM},)")
    if not bool(np.isfinite(rf202).all()):
        raise ValueError("ROUTER_VECTOR_NOT_FINITE")

    # ---- STEP 4: ACTION-UNAVAILABLE -> FORCED_SKIP ------------------------- #
    if not available:
        return mod._core_result(system, "FORCED_SKIP", "SKIP", p_global, None, window,
                                actual_r_psi_forwards=0, actual_s_omega_forwards=0,
                                global_forwards=g_forwards, geom=geom,
                                router_vector=rf202,
                                policy_control=policy_control,
                                forced_router_score=forced_router_score,
                                forced_safety_logit=forced_safety_logit)

    # ---- STEP 5: B_phi -> A8/C9 ROUTER DECISION --------------------------- #
    if forced_delta_hat_final is not None:
        delta_hat_final = float(forced_delta_hat_final)
    else:
        rf_norm = system._apply_norm(np.asarray(rf202, dtype=np.float32).reshape(-1),
                                     system.router_normalization)
        with mod.component_inference_context("B_phi"), mod.component_autocast_disabled("B_phi"):
            x_num = torch.from_numpy(np.ascontiguousarray(rf_norm))[None].to(device)
            t_ids = torch.tensor([task_id], dtype=torch.long, device=device)
            delta_hat_final = float(system.benefit_router(x_num, t_ids).reshape(-1)[0])
        counters["b_phi_forwards"] = counters.get("b_phi_forwards", 0) + 1
    util = canonical_utility(delta_hat_final)
    router_decision_value = "EXECUTE" if util >= TAU_C8_FINAL_FLOAT else "SKIP"

    # ---- STEP 6: SKIP BRANCH (R_psi = 0, S_omega = 0, final = global) ----- #
    if router_decision_value == "SKIP":
        return mod._core_result(system, "SKIP_GLOBAL", "SKIP", p_global, delta_hat_final, window,
                                actual_r_psi_forwards=0, actual_s_omega_forwards=0,
                                global_forwards=g_forwards, geom=geom,
                                router_vector=rf202,
                                policy_control=policy_control,
                                forced_router_score=forced_router_score,
                                forced_safety_logit=forced_safety_logit)

    # ---- STEP 7: EXECUTE BRANCH -> R_psi runs ONLY NOW -------------------- #
    rgb = image_b[0].detach().float().cpu().numpy() if torch.is_tensor(image_b) else \
        np.asarray(image_b, dtype=np.float32)[0]
    rgb_crop = mod.crop_and_resize_vec(rgb, geom, mod.REGIONAL_INPUT_RESOLUTION)
    prob_crop = mod.crop_and_resize_vec(p_global, geom, mod.REGIONAL_INPUT_RESOLUTION)
    rin = np.concatenate([np.asarray(rgb_crop, dtype=np.float32),
                          np.asarray(prob_crop, dtype=np.float32)], axis=0)
    with mod.component_inference_context("R_psi"), mod.component_autocast_disabled("R_psi"):
        rin_t = torch.from_numpy(np.ascontiguousarray(rin))[None].to(device)
        refined = torch.sigmoid(ctx["r_psi"](rin_t).float())[0, 0].detach().float().cpu().numpy()
    actual_r_psi_forwards += 1
    counters["r_psi_forwards"] = counters.get("r_psi_forwards", 0) + 1

    # ---- STEP 8: post-safety 16-D features -------------------------------- #
    pg_crop = np.asarray(prob_crop, dtype=np.float32)
    pg_crop = pg_crop[0] if pg_crop.ndim == 3 else pg_crop
    pr_crop = np.asarray(refined, dtype=np.float32)
    pr_crop = pr_crop[0] if pr_crop.ndim == 3 else pr_crop
    sf16 = np.asarray(mod.somega_features(pg_crop, pr_crop, geom), dtype=np.float64).reshape(-1)

    # ---- STEP 9: S_omega runs ONLY NOW ------------------------------------ #
    final_s_omega_input_capture = None
    post_safety_numeric_normalized_capture = None
    if forced_s_omega_logit is not None:
        logit = float(forced_s_omega_logit)
    else:
        sf_norm = system._apply_norm(np.asarray(sf16, dtype=np.float32),
                                     system.post_safety_normalization)
        full = np.concatenate([sf_norm, system._onehot_task(task_id)], axis=0)
        final_s_omega_input_capture = np.asarray(full, dtype=np.float64).reshape(-1)
        post_safety_numeric_normalized_capture = np.asarray(sf_norm,
                                                            dtype=np.float64).reshape(-1)
        with mod.component_inference_context("S_omega"), mod.component_autocast_disabled("S_omega"):
            logit = float(system.post_safety(
                torch.from_numpy(np.ascontiguousarray(full))[None].to(device)).reshape(-1)[0])
        actual_s_omega_forwards += 1
        counters["s_omega_forwards"] = counters.get("s_omega_forwards", 0) + 1
    accept_prob = float(torch.sigmoid(torch.tensor(float(logit), device=device)).item())

    # ---- STEP 10: ACCEPT / REJECT ----------------------------------------- #
    if accept_prob >= float(system.s_omega_accept_threshold):
        # ---- D61 REPAIR: canonical Phase27 pad-aware fusion ---------------- #
        # Frozen v1.14 used: system._fuse_global_with_regional(p_global, refined, window)
        # v1.4 (== v1.3) uses the canonical module-level Phase27 semantics with the
        # SAME geom object produced by the canonical ROI path and the SAME refined array.
        fused = mod.fuse_full_field(p_global, refined, geom)
        return mod._core_result(system, "EXECUTE_THEN_ACCEPT", "EXECUTE", fused, delta_hat_final,
                                window,
                                actual_r_psi_forwards=actual_r_psi_forwards,
                                actual_s_omega_forwards=actual_s_omega_forwards,
                                global_forwards=g_forwards, geom=geom, router_vector=rf202,
                                logit=logit, accept_prob=accept_prob,
                                policy_control=policy_control,
                                forced_router_score=forced_router_score,
                                forced_safety_logit=forced_safety_logit,
                                refined_output=refined, post_safety_features=sf16,
                                final_s_omega_input=final_s_omega_input_capture,
                                post_safety_numeric_normalized=post_safety_numeric_normalized_capture)
    return mod._core_result(system, "EXECUTE_THEN_REJECT", "EXECUTE", p_global, delta_hat_final,
                            window,
                            actual_r_psi_forwards=actual_r_psi_forwards,
                            actual_s_omega_forwards=actual_s_omega_forwards,
                            global_forwards=g_forwards, geom=geom, router_vector=rf202,
                            logit=logit, accept_prob=accept_prob,
                            policy_control=policy_control,
                            forced_router_score=forced_router_score,
                            forced_safety_logit=forced_safety_logit,
                            refined_output=refined, post_safety_features=sf16,
                            final_s_omega_input=final_s_omega_input_capture,
                            post_safety_numeric_normalized=post_safety_numeric_normalized_capture)


# --------------------------------------------------------------------------- #
# CLEAN DOWNSTREAM (GT-FREE) — stop at out["final_probability"]
# --------------------------------------------------------------------------- #
def _clean_final_probability_only(sid, row, ctx, generated, counters, store, runtime_state,
                                  journal: "_Journal | None" = None, row_index=None,
                                  n_rows=None, progress_points=None) -> dict:
    """Exact canonical downstream clean path (D61-repaired), STOPPING at out['final_probability'].

    Mirrors ``mod._evaluate_clean_sample`` EXCEPT that it never loads GT and never
    computes Dice/IoU/HD95.  Uses ONLY ``row['task_id']`` and the frozen image path
    loader; ``row['mask_path']`` is never read.

    v1.4 adds GT-free PROGRESS checkpoints (metadata only) at the requested
    ``progress_points``.  The journal write is instrumentation and touches NO tensor.
    """
    task_id = int(row["task_id"])
    p_global = generated["p_global"][sid]
    geom = generated["geometry"][sid]
    rf202 = generated["rf202"][sid]

    image_t = _FROZEN_MOD._load_clean_image_tensor(row)
    image_b = image_t[None].to(ctx["device"])

    out = _repaired_canonical_learned_core(
        ctx, image_b, task_id,
        p_global_override=p_global, g_taps=None,
        router_features_202_override=rf202,
        roi_window=None,
        action_available=(geom is not None),
        counters=counters)

    final_prob = np.asarray(out["final_probability"], dtype=np.float32)
    finite = _finite_check(final_prob)
    if not finite:
        _record_nonfinite(runtime_state, sid, final_prob)
    counters["final_probability_passes"] = counters.get("final_probability_passes", 0) + 1
    store[sid] = final_prob

    # ---- GT-FREE PROGRESS CHECKPOINT (metadata only; no tensor) ------------ #
    if (journal is not None and progress_points and row_index is not None
            and (row_index + 1) in progress_points):
        counters_view = {k: v for k, v in counters.items() if not isinstance(v, (list, dict))}
        journal.progress("clean_row_loop_progress", extra=OrderedDict([
            ("last_completed_row_index", int(row_index)),
            ("last_completed_sample_id", str(sid)),
            ("n_clean_rows_completed", int(row_index + 1)),
            ("n_rows_total", int(n_rows) if n_rows is not None else None),
            ("counters_subset", counters_view),
        ]))

    return {
        "sample_id": sid,
        "task_id": task_id,
        "state": out.get("state"),
        "router_decision": out.get("router_decision"),
        "roi_available": out.get("roi_available"),
        "final_probability_shape": list(final_prob.shape),
        "final_probability_dtype": str(final_prob.dtype),
        "final_probability_finite": finite,
    }


# --------------------------------------------------------------------------- #
# GT-FREE FINAL-AUTHORITY COMPARISON (identical to v1.3)
# --------------------------------------------------------------------------- #
def _compare_final_authority(final_prob_by_sid, sample_order, counters) -> dict:
    ref_path = ROOT / PHASE27_FINAL_PROB_AUTHORITY["path"]
    out = {
        "reference_path": PHASE27_FINAL_PROB_AUTHORITY["path"],
        "reference_sha256": (sha256_file(ref_path) if ref_path.exists() else None),
        "reference_sha256_expected": PHASE27_FINAL_PROB_AUTHORITY["sha256"],
        "n_samples": len(sample_order),
    }
    if not ref_path.exists():
        out.update({"pass": False, "reason": "PHASE27_FINAL_AUTHORITY_ABSENT"})
        return out
    if out["reference_sha256"] != PHASE27_FINAL_PROB_AUTHORITY["sha256"]:
        out.update({"pass": False, "reason": "PHASE27_FINAL_AUTHORITY_SHA_MISMATCH"})
        return out

    ref = np.load(ref_path)
    out["reference_shape"] = list(ref.shape)
    out["reference_dtype"] = str(ref.dtype)
    if list(ref.shape) != list(PHASE27_FINAL_PROB_AUTHORITY["shape"]):
        out.update({"pass": False, "reason": "PHASE27_FINAL_AUTHORITY_SHAPE_MISMATCH"})
        return out
    if len(sample_order) != ref.shape[0]:
        out.update({"pass": False, "reason": "POPULATION_SIZE_MISMATCH"})
        return out

    per_sample = []
    total_mismatch = 0
    max_abs = 0.0
    affected = []
    live_vs_self_flip = 0
    self_vs_bound_mismatch = 0
    live_vs_bound_mismatch = 0
    k_total = 0
    q_measured = 0
    live_f32_vs_bound_f16_exact = 0

    for i, sid in enumerate(sample_order):
        live = np.asarray(final_prob_by_sid[sid], dtype=np.float32)
        gen_f16 = live.astype(np.float16)
        bound_f16 = ref[i]
        neq = (gen_f16 != bound_f16)
        cnt = int(neq.sum())
        diff = np.abs(gen_f16.astype(np.float64) - bound_f16.astype(np.float64))
        mabs = float(diff.max()) if diff.size else 0.0
        total_mismatch += cnt
        max_abs = max(max_abs, mabs)
        if cnt:
            affected.append(sid)

        live_bin = (live >= np.float32(SEGMENTATION_OUTPUT_THRESHOLD))
        self_bin = (gen_f16.astype(np.float32) >= np.float32(SEGMENTATION_OUTPUT_THRESHOLD))
        bound_bin = (bound_f16.astype(np.float32) >= np.float32(SEGMENTATION_OUTPUT_THRESHOLD))
        n_live_self = int(np.count_nonzero(live_bin != self_bin))
        n_self_bound = int(np.count_nonzero(self_bin != bound_bin))
        n_live_bound = int(np.count_nonzero(live_bin != bound_bin))
        live_vs_self_flip += n_live_self
        self_vs_bound_mismatch += n_self_bound
        live_vs_bound_mismatch += n_live_bound
        if np.array_equal(live, bound_f16.astype(np.float32)):
            live_f32_vs_bound_f16_exact += 1

        is_half = (gen_f16 == F16_HALF)
        k_i = int(is_half.sum())
        q_i = int(np.count_nonzero(is_half & (live < np.float32(0.5))))
        k_total += k_i
        q_measured += q_i

        per_sample.append({
            "sample_id": sid,
            "f16_mismatch_count": cnt,
            "f16_max_abs_difference": mabs,
            "n_pixels_generated_f16_eq_half": k_i,
            "n_measured_live_below_half_at_half_pixels": q_i,
            "live_vs_self_f16_threshold_flip_count": n_live_self,
            "self_f16_vs_phase27_f16_threshold_mismatch_count": n_self_bound,
            "live_vs_phase27_threshold_mismatch_count": n_live_bound,
        })

    bit_identical_all = bool(total_mismatch == 0)
    if bit_identical_all:
        classification = "D61_CANONICAL_FUSION_REPAIR_REPRODUCES_PHASE27_FINAL_AUTHORITY"
    else:
        classification = "D61_FUSION_REPAIR_INSUFFICIENT_TO_REPRODUCE_PHASE27_FINAL_AUTHORITY"

    out.update({
        "pass": True,
        "n_samples": len(sample_order),
        "final_f16_bit_identical_all": bit_identical_all,
        "total_f16_element_mismatch_count": int(total_mismatch),
        "max_abs_f16_difference": float(max_abs),
        "n_samples_with_any_f16_difference": len(affected),
        "affected_sample_ids": affected,
        "per_sample": per_sample,
        "live_vs_self_f16_threshold_flip_count": int(live_vs_self_flip),
        "self_f16_vs_phase27_f16_threshold_mismatch_count": int(self_vs_bound_mismatch),
        "live_vs_phase27_threshold_mismatch_count": int(live_vs_bound_mismatch),
        "n_pixels_generated_f16_eq_half_total": int(k_total),
        "n_measured_q_live_below_half_total": int(q_measured),
        "n_samples_live_f32_bit_equal_to_bound_f16": int(live_f32_vs_bound_f16_exact),
        "classification": classification,
        "interpretation_contract": {
            "bit_identical_all_true_means": "D61_CANONICAL_FUSION_REPAIR_REPRODUCES_PHASE27_FINAL_AUTHORITY",
            "bit_identical_all_false_means": "D61_FUSION_REPAIR_INSUFFICIENT_TO_REPRODUCE_PHASE27_FINAL_AUTHORITY",
            "establishes_repaired_clean_final_probability_authority_only": True,
            "does_not_execute_robustness_science": True,
            "not_automatically_g_mismatch": True,
        },
        "gt_read": False,
        "dice_iou_hd95_computed": False,
    })
    return out


_FROZEN_MOD = None


def _provenance_state(spec_map) -> dict:
    out = {"all_match": True, "items": {}}
    for name, spec in spec_map.items():
        p = ROOT / spec["path"]
        ok = p.exists() and sha256_file(p) == spec["sha256"]
        out["items"][name] = {"path": spec["path"], "present": p.exists(),
                              "expected": spec["sha256"],
                              "observed": (sha256_file(p) if p.exists() else None),
                              "match": bool(ok)}
        if not ok:
            out["all_match"] = False
    return out


def _prior_failure_provenance_state() -> dict:
    out = _provenance_state(PRIOR_FAILURE_PROVENANCE)
    out["static_audit_verdict"] = None
    audit_p = ROOT / PRIOR_FAILURE_PROVENANCE["targeted_static_audit"]["path"]
    if audit_p.exists():
        try:
            out["static_audit_verdict"] = json.loads(
                audit_p.read_text(encoding="utf-8")).get("root_cause_static_verdict")
        except Exception as exc:  # noqa: BLE001
            out["static_audit_verdict"] = f"UNPARSEABLE::{type(exc).__name__}"
    if out["static_audit_verdict"] != REQUIRED_STATIC_AUDIT_VERDICT:
        out["all_match"] = False
    return out


def _v1_1_consumed_state() -> dict:
    out = {"all_match": True, "items": {}, "predicates": {}, "result_absent": None}
    for name, spec in V1_1_CONSUMED_EVIDENCE.items():
        p = ROOT / spec["path"]
        ok = p.exists() and sha256_file(p) == spec["sha256"]
        out["items"][name] = {"path": spec["path"], "present": p.exists(),
                              "expected": spec["sha256"],
                              "observed": (sha256_file(p) if p.exists() else None),
                              "match": bool(ok)}
        if not ok:
            out["all_match"] = False
    out["result_absent"] = not (ROOT / V1_1_RESULT_PATH).exists()
    if not out["result_absent"]:
        out["all_match"] = False
    fp = ROOT / V1_1_CONSUMED_EVIDENCE["v1_1_failure"]["path"]
    if fp.exists():
        try:
            fj = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            out["predicates"] = {"parse_error": type(exc).__name__}
            out["all_match"] = False
            return out
        pred = {k: fj.get(k) for k in REQUIRED_V1_1_FAILURE_PREDICATES}
        out["predicates"] = pred
        out["predicates_match"] = {k: bool(pred.get(k) == v)
                                   for k, v in REQUIRED_V1_1_FAILURE_PREDICATES.items()}
        if not all(out["predicates_match"].values()):
            out["all_match"] = False
    else:
        out["all_match"] = False
    return out


def _v1_2_consumed_state() -> dict:
    out = {"all_match": True, "items": {}, "predicates": {}, "failure_absent": None}
    for name, spec in V1_2_CONSUMED_EVIDENCE.items():
        p = ROOT / spec["path"]
        ok = p.exists() and sha256_file(p) == spec["sha256"]
        out["items"][name] = {"path": spec["path"], "present": p.exists(),
                              "expected": spec["sha256"],
                              "observed": (sha256_file(p) if p.exists() else None),
                              "match": bool(ok)}
        if not ok:
            out["all_match"] = False
    out["failure_absent"] = not (ROOT / V1_2_FAILURE_PATH).exists()
    rp = ROOT / V1_2_CONSUMED_EVIDENCE["v1_2_result"]["path"]
    if rp.exists():
        try:
            rj = json.loads(rp.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            out["predicates"] = {"parse_error": type(exc).__name__}
            out["all_match"] = False
            return out
        cmp_ = rj.get("final_authority_comparison", {}) or {}
        pred = {
            "classification": rj.get("classification"),
            "final_f16_bit_identical_all": cmp_.get("final_f16_bit_identical_all"),
            "n_samples_with_any_f16_difference": cmp_.get("n_samples_with_any_f16_difference"),
            "total_f16_element_mismatch_count": cmp_.get("total_f16_element_mismatch_count"),
            "max_abs_f16_difference": cmp_.get("max_abs_f16_difference"),
            "VAL_GT_READ": rj.get("VAL_GT_READ"),
        }
        out["predicates"] = pred
        out["predicates_match"] = {k: bool(pred.get(k) == v)
                                   for k, v in REQUIRED_V1_2_RESULT_PREDICATES.items()}
        if not all(out["predicates_match"].values()):
            out["all_match"] = False
    else:
        out["all_match"] = False
    rec_p = ROOT / V1_2_CONSUMED_EVIDENCE["v1_2_result_adjudication_reconciliation_v1_1"]["path"]
    if rec_p.exists():
        try:
            rj2 = json.loads(rec_p.read_text(encoding="utf-8"))
            out["d60_reconciled"] = rj2.get("D60_RECONCILED")
            out["d61_status"] = (rj2.get("d61", {}) or {}).get("status")
            out["d61_classification"] = (rj2.get("d61", {}) or {}).get("classification")
        except Exception as exc:  # noqa: BLE001
            out["reconciliation_parse_error"] = type(exc).__name__
            out["all_match"] = False
    if out.get("d60_reconciled") != REQUIRED_D60_RECONCILED:
        out["all_match"] = False
    if out.get("d61_status") != REQUIRED_D61_STATUS:
        out["all_match"] = False
    if out.get("d61_classification") != REQUIRED_D61_CLASSIFICATION:
        out["all_match"] = False
    return out


def _v1_3_consumed_state() -> dict:
    """D67/D68 preservation: bind the v1.3 consumed evidence + adjudication authorities."""
    out = {"all_match": True, "items": {}, "predicates": {}}
    for name, spec in V1_3_CONSUMED_EVIDENCE.items():
        p = ROOT / spec["path"]
        ok = p.exists() and sha256_file(p) == spec["sha256"]
        out["items"][name] = {"path": spec["path"], "present": p.exists(),
                              "expected": spec["sha256"],
                              "observed": (sha256_file(p) if p.exists() else None),
                              "match": bool(ok)}
        if not ok:
            out["all_match"] = False
    # v1.3 RESULT must be ABSENT (terminal evidence anomaly), FAILURE ABSENT.
    out["v1_3_result_absent"] = not (ROOT / V1_3_RESULT_PATH).exists()
    out["v1_3_failure_absent"] = not (ROOT / V1_3_FAILURE_PATH).exists()
    if not out["v1_3_result_absent"]:
        out["all_match"] = False
    if not out["v1_3_failure_absent"]:
        out["all_match"] = False
    # D67 adjudication predicates (PRESERVED, not reinterpreted).
    adj_p = ROOT / V1_3_CONSUMED_EVIDENCE["d67_terminal_anomaly_adjudication_v1_0"]["path"]
    if adj_p.exists():
        try:
            aj = json.loads(adj_p.read_text(encoding="utf-8"))
            # Actual D67 key is `D67`; fallbacks tolerate alternate spellings.
            out["predicates"]["d67_classification"] = (aj.get("D67") or aj.get("D67_CLASSIFICATION")
                                                       or aj.get("classification"))
            out["predicates"]["attempt_state"] = aj.get("attempt_state")
            out["predicates"]["root_cause"] = aj.get("root_cause")
            out["predicates"]["termination_mechanism"] = aj.get("termination_mechanism")
        except Exception as exc:  # noqa: BLE001
            out["adjudication_parse_error"] = type(exc).__name__
            out["all_match"] = False
    # D68 reconciliation predicates (PRESERVED).
    rec_p = ROOT / V1_3_CONSUMED_EVIDENCE["d68_terminal_anomaly_reconciliation_v1_1"]["path"]
    if rec_p.exists():
        try:
            rj = json.loads(rec_p.read_text(encoding="utf-8"))
            # Actual keys: lowercase `d68_classification`; `D68` carries "RECONCILED".
            out["predicates"]["d68_classification"] = (rj.get("d68_classification")
                                                       or rj.get("D68_CLASSIFICATION")
                                                       or rj.get("classification"))
            out["predicates"]["d68_status"] = (rj.get("D68") or rj.get("D68_STATUS")
                                               or rj.get("status"))
        except Exception as exc:  # noqa: BLE001
            out["reconciliation_parse_error"] = type(exc).__name__
            out["all_match"] = False
    out["d67_preserved_classification"] = D67_CLASSIFICATION
    out["d67_preserved_root_cause"] = D67_ROOT_CAUSE
    out["d67_preserved_termination_mechanism"] = D67_TERMINATION_MECHANISM
    out["d68_preserved_classification"] = D68_CLASSIFICATION
    out["d68_preserved_status"] = D68_STATUS
    out["v1_3_state"] = V1_3_STATE
    out["v1_3_retry"] = V1_3_RETRY
    return out


def _build_counters(mod) -> "OrderedDict":
    """EXACT frozen v1.14 counter authority (fail closed if unavailable)."""
    try:
        C = mod.C
        required = list(C.COUNTERS_REQUIRED)
        forever_zero = list(C.COUNTERS_FOREVER_ZERO)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__FROZEN_COUNTER_AUTHORITY_UNAVAILABLE: "
            f"{type(exc).__name__}: {exc}")
    if not required:
        raise SystemExit(
            "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__FROZEN_COUNTER_AUTHORITY_EMPTY")
    counters = OrderedDict((k, 0) for k in required)
    for k in forever_zero:
        counters[k] = 0
    counters["_counter_authority_required_n"] = len(required)
    counters["_counter_authority_forever_zero_n"] = len(forever_zero)
    return counters


# GT-free progress checkpoint rows (metadata only).
PROGRESS_POINTS = (1, 25, 50, 100, 200, 300, 400, 500, 600, 700, 808)


def run_diagnostic(runtime_state: dict, journal: "_Journal | None" = None) -> dict:
    global _FROZEN_MOD
    mod = _import_frozen_v1_14()
    _FROZEN_MOD = mod

    # ---- RUNTIME GT-CONTENT PROHIBITION ------------------------------------ #
    gt_guard = _install_gt_guards(mod, runtime_state)
    assert sha256_file(FROZEN_V1_14_SOURCE) == FROZEN_V1_14_EXEC_SHA, \
        "frozen v1.14 source mutated by guard installation"

    frozen_canonical_core = _FROZEN_MOD.canonical_learned_core
    d61_frozen_core_baseline = {
        "present": callable(frozen_canonical_core),
        "qualname": getattr(frozen_canonical_core, "__qualname__", None),
        "module": getattr(frozen_canonical_core, "__module__", None),
    }

    counters = _build_counters(mod)

    # ---- crash-survivable stage journaling (v1.4) -------------------------- #
    def _stg(stage, fn):
        if journal is not None:
            journal.begin(stage)
        r = fn()
        if journal is not None:
            journal.complete(stage)
        return r

    stages: dict = {}
    stages["d50_foreign_gate_call_omitted"] = True
    stages["d50_reason"] = D50_REASON
    stages["gt_guard_installed"] = list(gt_guard["installed"])
    stages["gt_content_invariant"] = dict(GT_CONTENT_INVARIANT)
    stages["d61_repair_classification"] = D61_REPAIR_CLASSIFICATION
    stages["d61_canonical_accept_call"] = D61_CANONICAL_ACCEPT_CALL
    stages["d61_replaced_old_accept_call"] = D61_OLD_ACCEPT_CALL
    stages["d61_uses_same_geom_from_canonical_roi_path"] = True
    stages["d61_uses_same_refined_from_canonical_r_psi"] = True
    stages["d61_frozen_canonical_core_baseline"] = d61_frozen_core_baseline

    # ---- load exact frozen components -------------------------------------- #
    ctx = _stg("091_load_models", lambda: mod._load_models())
    stages["step_models_loaded"] = True
    stages["component_load_audit"] = ctx.get("load_audit")

    # ---- canonical batched CLEAN G (LIVE FLOAT32 downstream preserved) ------ #
    generated = _stg("092_generate_clean_g_reference",
                     lambda: mod._generate_clean_g_reference(ctx, counters))
    stages["step_generation_n"] = len(generated.get("sample_order", []))
    stages["g_downstream_representation"] = "LIVE_FLOAT32 (NOT quantized; D51 G-quantization repair WITHDRAWN)"

    # ---- retained Phase27 GLOBAL f16 reproduction gate --------------------- #
    g_gate = _stg("093_phase27_global_reproduction_gate", lambda:
                  mod._phase27_global_reproduction_gate(
                      generated["p_global_f16"], generated["sample_order"], counters))
    stages["step4_phase27_global_reproduction_gate"] = g_gate
    if not g_gate.get("pass"):
        raise SystemExit(
            "DIAGNOSTIC_PHASE27_GLOBAL_REPRODUCTION_GATE_FAILED: "
            + json.dumps(g_gate, default=str))

    # ---- 808 GT-free clean final-probability passes (D61 repaired) --------- #
    rows, _row_index = _stg("094_clean_row_index", lambda: mod._clean_row_index())
    sample_order = [r["sample_id"] for r in rows]
    final_prob_by_sid: dict = {}
    clean_records = []

    def _row_loop():
        for i, r in enumerate(rows):
            sid = r["sample_id"]
            clean_records.append(
                _clean_final_probability_only(sid, r, ctx, generated, counters,
                                              final_prob_by_sid, runtime_state,
                                              journal=journal, row_index=i,
                                              n_rows=len(rows),
                                              progress_points=PROGRESS_POINTS))
            counters["clean_passes"] = counters.get("clean_passes", 0) + 1
        return True

    _stg("095_clean_row_loop_808", _row_loop)
    stages["step5_clean_records"] = len(clean_records)
    stages["step5_final_probability_passes"] = len(final_prob_by_sid)

    # ---- FINITE-PROBABILITY FAIL-CLOSED ------------------------------------ #
    def _finite_gate():
        if runtime_state.get("nonfinite_final_probability"):
            runtime_state["terminal_classification"] = TERMINAL_NONFINITE
            raise SystemExit(
                TERMINAL_NONFINITE + "::" + json.dumps(runtime_state["nonfinite_samples"], default=str))
        return True

    _stg("096_finite_gate", _finite_gate)

    # ---- GT-free final-authority comparison -------------------------------- #
    cmp_ = _stg("097_compare_final_authority", lambda:
                _compare_final_authority(final_prob_by_sid, sample_order, counters))
    stages["step6_final_authority_comparison"] = {
        k: v for k, v in cmp_.items() if k != "per_sample"}
    runtime_state["final_authority_computed"] = True
    runtime_state["final_authority_comparison"] = cmp_
    runtime_state["classification"] = cmp_.get("classification")

    # ---- GT-content invariant ---------------------------------------------- #
    def _gt_invariant_gate():
        if runtime_state["VAL_GT_READ"] != 0:
            raise SystemExit(
                "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__GT_READ_NONZERO::"
                + json.dumps(runtime_state, default=str))
        if not cmp_.get("pass"):
            raise SystemExit("DIAGNOSTIC_FINAL_AUTHORITY_COMPARISON_FAILED: "
                             + json.dumps(cmp_, default=str))
        return True

    _stg("098_gt_and_comparison_gate", _gt_invariant_gate)

    # ---- D66 remediation: DERIVE the Phase27 score SHA (never re-typed) ----- #
    derived_score_sha = (sha256_file(PHASE27_SCORES_CSV) if PHASE27_SCORES_CSV.exists() else None)

    diag = {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_RESULT",
        "revision": DIAGNOSTIC_REVISION,
        "purpose": "GT_FREE_FINAL_PROBABILITY_AUTHORITY_REPRODUCTION_TEST__D61_CANONICAL_FUSION_REPAIR__CRASH_SURVIVABLE",
        "execution_scope": "CLEAN_ONLY__NO_GT__NO_DICE__NO_PERTURBATION",
        "exact_diagnostic_source_sha256": sha256_file(Path(__file__)),
        "frozen_v1_14_source_sha256": sha256_file(FROZEN_V1_14_SOURCE),
        "frozen_v1_14_manifest_sha256": FROZEN_V1_14_MANIFEST_SHA,
        "phase27_final_prob_authority": dict(PHASE27_FINAL_PROB_AUTHORITY),
        "phase27_global_prob_authority": dict(PHASE27_GLOBAL_PROB_AUTHORITY),
        "phase27_scores_csv_sha256_derived": derived_score_sha,
        "phase27_scores_csv_sha256_canonical_constant": PHASE27_SCORES_CSV_SHA_CANONICAL,
        "final_authority_comparison": cmp_,
        "stages": stages,
        "counters": dict(counters),
        "journal": (journal.snapshot() if journal is not None else {"journal_enabled": False}),
        "VAL_GT_READ": int(runtime_state["VAL_GT_READ"]),
        "blocked_gt_calls": list(runtime_state.get("blocked_gt_calls", [])),
        "gt_guard": {"installed": list(gt_guard["installed"]),
                     "blocked_calls": list(runtime_state.get("blocked_gt_calls", []))},
        "gt_content_invariant": dict(GT_CONTENT_INVARIANT),
        "nonfinite_samples": dict(runtime_state.get("nonfinite_samples", {})),
        "authorized_population_count": 808,
        "prior_failure_provenance_bound": _prior_failure_provenance_state(),
        "consumed_evidence_provenance_bound": _provenance_state(CONSUMED_EVIDENCE_PROVENANCE),
        "v1_1_consumed_state_bound": _v1_1_consumed_state(),
        "v1_2_consumed_state_bound": _v1_2_consumed_state(),
        "v1_3_consumed_state_bound": _v1_3_consumed_state(),
        "d50_foreign_gate_call_omitted": True,
        "d50_reason": D50_REASON,
        "foreign_v1_14_launch_token_present": os.environ.get(FOREIGN_V1_14_LAUNCH_TOKEN) == "1",
        "preconsumption_transitive_integrity_pass": True,
        "source_manifest_transitive_authority_exact_match": True,
        "final_authority_preconsumption_pass": True,
        "d61_repair_classification": D61_REPAIR_CLASSIFICATION,
        "d61_canonical_accept_call": D61_CANONICAL_ACCEPT_CALL,
        "d61_old_accept_call_absent": True,
        "d61_replay_token": D61_REPLAY_TOKEN,
        "d67_preserved_classification": D67_CLASSIFICATION,
        "d67_preserved_root_cause": D67_ROOT_CAUSE,
        "d67_preserved_termination_mechanism": D67_TERMINATION_MECHANISM,
        "d68_preserved_classification": D68_CLASSIFICATION,
        "d68_preserved_status": D68_STATUS,
        "v1_3_state_preserved": V1_3_STATE,
        "v1_3_retry_preserved": V1_3_RETRY,
        "classification": cmp_["classification"],
        "perturbation_executed": False,
        "scientific_output": False,
        "robustness_result": False,
        "v1_14_science_markers_touched": False,
        "generated_utc": now(),
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync (exclusive-create, write-once)",
    }
    return diag


def _attempt_already_consumed() -> bool:
    return any(p.exists() for p in (DIAGNOSTIC_START, DIAGNOSTIC_RESULT, DIAGNOSTIC_FAILURE))


def _make_attempt_id() -> str:
    return f"v1_4_{os.getpid()}_{now()}"


def main() -> int:
    runtime_state = _new_runtime_state()
    attempt_id = _make_attempt_id()
    journal_enabled = _journal_enabled()
    journal = _Journal(attempt_id, DIAGNOSTIC_REVISION, journal_enabled)

    # ---- (0) FOREIGN v1.14 launcher token MUST be absent ------------------- #
    if os.environ.get(FOREIGN_V1_14_LAUNCH_TOKEN) == "1":
        print(json.dumps({
            "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__"
                      "FOREIGN_V1_14_LAUNCH_AUTHORITY_PRESENT__NO_ATTEMPT_CONSUMED",
            "foreign_token": FOREIGN_V1_14_LAUNCH_TOKEN,
            "foreign_token_present": True,
            "attempt_consumed": False,
            "marker_created": False}, indent=1))
        return 8

    # ---- (1) one-shot execute gate ---------------------------------------- #
    if os.environ.get(ONE_SHOT_ENV) != "1":
        print(json.dumps({
            "status": "REFUSED__ONE_SHOT_GATE_NOT_SET",
            "required_env": f"{ONE_SHOT_ENV}=1",
            "attempt_consumed": False}, indent=1))
        return 3

    # ---- (2) prior-attempt absence ---------------------------------------- #
    if _attempt_already_consumed():
        print(json.dumps({
            "status": "REFUSED__DIAGNOSTIC_ATTEMPT_ALREADY_CONSUMED",
            "automatic_retry": False,
            "attempt_consumed": False}, indent=1))
        return 4

    # ---- (3) diagnostic launch authority (FAIL CLOSED) --------------------- #
    if os.environ.get(LAUNCH_AUTHORITY_TOKEN) != "1":
        print(json.dumps({
            "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__"
                      "LAUNCH_AUTHORITY_REQUIRED__NO_ATTEMPT_CONSUMED",
            "required_env": f"{LAUNCH_AUTHORITY_TOKEN}=1",
            "launch_authority_present": False,
            "attempt_consumed": False,
            "marker_created": False,
            "model_constructed": False,
            "checkpoint_loaded": False,
            "val_or_gt_read": False}, indent=1))
        return 5

    # ---- (4) preserved prior-failure provenance gate ----------------------- #
    prov = _prior_failure_provenance_state()
    if not prov["all_match"]:
        print(json.dumps({
            "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__"
                      "PRIOR_FAILURE_PROVENANCE_NOT_BOUND__NO_ATTEMPT_CONSUMED",
            "provenance": prov, "attempt_consumed": False}, indent=1))
        return 6

    # ---- (5) consumed-evidence binding gate -------------------------------- #
    consumed = _provenance_state(CONSUMED_EVIDENCE_PROVENANCE)
    if not consumed["all_match"]:
        print(json.dumps({
            "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__"
                      "CONSUMED_EVIDENCE_NOT_BOUND__NO_ATTEMPT_CONSUMED",
            "consumed_evidence": consumed, "attempt_consumed": False}, indent=1))
        return 9

    # ---- (6) v1.1 CONSUMED-state binding gate (D56) ------------------------ #
    v11 = _v1_1_consumed_state()
    if not v11["all_match"]:
        print(json.dumps({
            "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__"
                      "V1_1_CONSUMED_STATE_NOT_BOUND__NO_ATTEMPT_CONSUMED",
            "v1_1_consumed_state": v11, "attempt_consumed": False}, indent=1))
        return 10

    # ---- (6b) v1.2 CONSUMED-state binding gate (D61) ----------------------- #
    v12 = _v1_2_consumed_state()
    if not v12["all_match"]:
        print(json.dumps({
            "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__"
                      "V1_2_CONSUMED_STATE_NOT_BOUND__NO_ATTEMPT_CONSUMED",
            "v1_2_consumed_state": v12, "attempt_consumed": False}, indent=1))
        return 11

    # ---- (6c) v1.3 CONSUMED-state binding gate (D67/D68) ------------------- #
    v13 = _v1_3_consumed_state()
    if not v13["all_match"]:
        print(json.dumps({
            "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__"
                      "V1_3_CONSUMED_STATE_NOT_BOUND__NO_ATTEMPT_CONSUMED",
            "v1_3_consumed_state": v13, "attempt_consumed": False}, indent=1))
        return 12

    touch_guard = {p.name: p.exists() for p in V14_SCIENCE_MARKERS}

    # ---- (7) derived authorization + write-once start marker --------------- #
    authorized_attempt = bool(
        os.environ.get(ONE_SHOT_ENV) == "1"
        and os.environ.get(LAUNCH_AUTHORITY_TOKEN) == "1"
        and os.environ.get(FOREIGN_V1_14_LAUNCH_TOKEN) != "1"
        and not _attempt_already_consumed()
        and prov["all_match"]
        and prov["static_audit_verdict"] == REQUIRED_STATIC_AUDIT_VERDICT
        and consumed["all_match"]
        and v11["all_match"]
        and v12["all_match"]
        and v13["all_match"])
    if not authorized_attempt:
        print(json.dumps({
            "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_FAIL_CLOSED__"
                      "AUTHORIZATION_STATE_NOT_SATISFIED__NO_ATTEMPT_CONSUMED",
            "attempt_consumed": False}, indent=1))
        return 7

    _write_once_json(DIAGNOSTIC_START, {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_START",
        "revision": DIAGNOSTIC_REVISION,
        "attempt_id": attempt_id,
        "attempted": True,
        "authorized_attempt": authorized_attempt,
        "authorization_derivation": ("derived: one_shot_gate AND launch_authority_token AND "
                                     "foreign_v1_14_token_absent AND no_prior_attempt AND "
                                     "prior_failure_provenance_bound AND "
                                     "static_audit_verdict==STATIC_ROOT_CAUSE_NOT_ESTABLISHED AND "
                                     "consumed_evidence_bound AND v1_1_consumed_state_bound AND "
                                     "v1_2_consumed_state_bound AND v1_3_consumed_state_bound"),
        "one_shot_gate_env": ONE_SHOT_ENV,
        "launch_authority_token_env": LAUNCH_AUTHORITY_TOKEN,
        "foreign_v1_14_launch_token_env": FOREIGN_V1_14_LAUNCH_TOKEN,
        "foreign_v1_14_launch_token_present": False,
        "d50_foreign_gate_call_omitted": True,
        "d50_reason": D50_REASON,
        "d61_repair_classification": D61_REPAIR_CLASSIFICATION,
        "d61_canonical_accept_call": D61_CANONICAL_ACCEPT_CALL,
        "d61_old_accept_call_replaced": D61_OLD_ACCEPT_CALL,
        "d61_replay_token": D61_REPLAY_TOKEN,
        "exact_diagnostic_source_sha256": sha256_file(Path(__file__)),
        "frozen_v1_14_exec_source_sha256": FROZEN_V1_14_EXEC_SHA,
        "frozen_v1_14_manifest_sha256": FROZEN_V1_14_MANIFEST_SHA,
        "phase27_final_prob_authority": dict(PHASE27_FINAL_PROB_AUTHORITY),
        "prior_failure_provenance": prov,
        "consumed_evidence_provenance": consumed,
        "v1_1_consumed_state": v11,
        "v1_2_consumed_state": v12,
        "v1_3_consumed_state": v13,
        "journal": journal.snapshot(),
        "v1_14_science_marker_presence_at_start": touch_guard,
        "gt_content_invariant": dict(GT_CONTENT_INVARIANT),
        "gt_prohibition": {"static": "no GT-content callable referenced",
                           "runtime": "raising proxies installed",
                           "VAL_GT_READ_must_be": 0,
                           "mask_path_metadata_validation_permitted": True},
        "automatic_retry": False,
        "overwrite_permitted": False,
        "scientific_output": False,
        "generated_utc": now(),
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync (exclusive-create, write-once)",
    })

    # ---- (7b) first durable journal record (post-START) -------------------- #
    if journal_enabled:
        journal.begin("100_diagnostic_main_after_start")
        journal.complete("100_diagnostic_main_after_start")

    # ---- (8) GUARDED COMPUTATION REGION ------------------------------------ #
    try:
        diag = run_diagnostic(runtime_state, journal=journal)
    except SystemExit as exc:
        _sync_journal_state(runtime_state, journal)
        _write_failure(termination_kind="SYSTEM_EXIT", runtime_state=runtime_state,
                       exc_type="SystemExit", exc_msg=str(exc.code),
                       failing_stage="run_diagnostic")
        print(json.dumps({"status": "DIAGNOSTIC_TERMINATED", "message": str(exc.code)}, indent=1))
        return 1
    except BaseException as exc:  # noqa: BLE001
        _sync_journal_state(runtime_state, journal)
        _write_failure(termination_kind="EXCEPTION", runtime_state=runtime_state,
                       exc_type=type(exc).__name__, exc_msg=str(exc),
                       failing_stage="run_diagnostic")
        traceback.print_exc()
        return 2

    _sync_journal_state(runtime_state, journal)

    # ---- (9) RESULT WRITE (D54: computed evidence survives a write failure) -- #
    if journal_enabled:
        journal.begin("101_result_write")
    runtime_state["result_write_attempted"] = True
    try:
        _write_once_json(DIAGNOSTIC_RESULT, diag)
        runtime_state["result_write_completed"] = True
        if journal_enabled:
            journal.complete("101_result_write")
    except BaseException as exc:  # noqa: BLE001
        runtime_state["result_write_completed"] = False
        runtime_state["terminal_classification"] = TERMINAL_RESULT_WRITE_FAILED
        _sync_journal_state(runtime_state, journal)
        _write_failure(termination_kind="RESULT_WRITE_FAILURE", runtime_state=runtime_state,
                       exc_type=type(exc).__name__, exc_msg=str(exc),
                       failing_stage="result_write")
        print(json.dumps({
            "status": TERMINAL_RESULT_WRITE_FAILED,
            "message": str(exc),
            "final_authority_computed": bool(runtime_state["final_authority_computed"]),
            "automatic_retry": False}, indent=1))
        return 3

    print(json.dumps({
        "status": "DIAGNOSTIC_COMPLETE",
        "classification": diag["classification"],
        "final_f16_bit_identical_all": diag["final_authority_comparison"]["final_f16_bit_identical_all"],
        "total_f16_element_mismatch_count": diag["final_authority_comparison"]["total_f16_element_mismatch_count"],
        "max_abs_f16_difference": diag["final_authority_comparison"]["max_abs_f16_difference"],
        "n_samples_with_any_f16_difference": diag["final_authority_comparison"]["n_samples_with_any_f16_difference"],
        "VAL_GT_READ": diag["VAL_GT_READ"],
        "result_path": str(DIAGNOSTIC_RESULT.relative_to(ROOT)),
        "result_sha256": sha256_file(DIAGNOSTIC_RESULT),
        "d61_repair_classification": D61_REPAIR_CLASSIFICATION,
        "perturbation_executed": False,
        "scientific_output": False}, indent=1))
    return 0


def _sync_journal_state(runtime_state: dict, journal: "_Journal | None") -> None:
    if journal is None:
        return
    runtime_state["journal_last_durable_stage"] = journal.last_durable_stage
    runtime_state["journal_last_complete_stage"] = journal.last_complete_stage
    runtime_state["journal_first_started_not_completed_stage"] = \
        journal.first_started_not_completed
    runtime_state["journal_records_written"] = journal.records


if __name__ == "__main__":
    raise SystemExit(main())
