"""Phase 39 coding verification — SYNTHETIC fixtures only, TEST1683 NEVER opened.

Verifies the protected single-pass evaluation software:
  * exactly-once evaluation and frozen-population identity
  * checkpoint-family identity (SHA binding, no silent fallback)
  * authorization checks / fail-closed preflight
  * no test-time tuning
  * atomic result publication
  * interrupted-attempt handling
  * duplicate-attempt refusal
  * audit-record integrity
  * fail-closed behaviour on every malformed input

CODING verdict:   CODE_COMPLETE_SYNTHETIC_VERIFIED
SCIENCE verdict:  REAL_TEST_EVALUATION_NOT_EXECUTED

Every population below is a handful of in-memory dictionaries. The protected
v1.2 script is exercised ONLY with its ROOT redirected to a temporary directory;
its real checkpoint/manifest paths are never read. No TEST cohort, no VAL cohort,
no checkpoint and no model forward is touched by this module.
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import sys
from pathlib import Path

import pytest

from src.research.deployment.artifacts import digest
from src.research.evaluation.single_pass import ConsumedAttemptError, run_once
from scripts.analysis import phase39_final_test_execution_v1_2 as P39

SYNTHETIC = "SYNTHETIC_TEST_ONLY"
SAMPLE_IDS = ("s1", "s2", "s3")
CODING_VERDICT = "CODE_COMPLETE_SYNTHETIC_VERIFIED"
SCIENCE_VERDICT = "REAL_TEST_EVALUATION_NOT_EXECUTED"


def _kwargs(**overrides):
    base = dict(
        preflight=lambda: {"fixture": True},
        load_population=lambda: [{"sample_id": i} for i in reversed(SAMPLE_IDS)],
        evaluate=lambda row: dict(row, dice=0.5, state="SKIP_GLOBAL"),
        expected_ids=SAMPLE_IDS,
        evidence_class=SYNTHETIC,
    )
    base.update(overrides)
    return base


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Exactly-once + audit-record integrity + atomic publication
# --------------------------------------------------------------------------- #
def test_exactly_once_evaluation_and_atomic_publication(tmp_path):
    out = tmp_path / "attempt"
    calls = []
    identity = {"family": "FULL", "seed": 42, "checkpoint_sha": "a" * 64,
                "authorization": "SYNTHETIC_PREFLIGHT_ONLY"}

    def preflight():
        assert not out.exists()
        return identity

    def load_population():
        # consumed marker must exist BEFORE any reader is initialised
        assert (out / "consumed.json").exists()
        assert not (out / "completion.json").exists()
        return [{"sample_id": i} for i in reversed(SAMPLE_IDS)]

    def evaluate(row):
        assert not (out / "completion.json").exists()
        calls.append(row["sample_id"])
        return dict(row, dice=0.5, state="SKIP_GLOBAL")

    kwargs = _kwargs(preflight=preflight, load_population=load_population,
                     evaluate=evaluate)
    completion = run_once(out, **kwargs)

    assert calls == list(SAMPLE_IDS)                       # frozen order, once each
    assert completion["status"] == "COMPLETE"
    assert completion["counts"] == {"population_rows": 3, "evaluation_attempts": 3,
                                    "completed_samples": 3}
    assert completion["preflight_identity"] == identity  # recorded verbatim, not minted
    assert completion["evidence_class"] == SYNTHETIC
    assert "grant" not in identity and "authorization_minted" not in completion

    files = {p.name for p in out.iterdir() if p.is_file()}
    assert files == {"consumed.json", "per_sample.json", "completion.json"}
    consumed = _read(out / "consumed.json")
    assert consumed["preflight_identity"] == identity
    assert consumed["evidence_class"] == SYNTHETIC
    assert consumed["automatic_retry"] is False

    per_sample = _read(out / "per_sample.json")
    assert per_sample["evidence_class"] == SYNTHETIC
    assert [r["sample_id"] for r in per_sample["records"]] == list(SAMPLE_IDS)
    # completion.json is the sole publication marker and binds the result bytes
    assert completion["per_sample_sha256"] == digest(out / "per_sample.json")
    assert _read(out / "completion.json") == completion


def test_checkpoint_family_identity_is_recorded_not_invented(tmp_path):
    out = tmp_path / "attempt"
    identity = {"family": "LITE", "seed": 123, "checkpoint_sha": "b" * 64,
                "component": "SYNTHETIC_FAMILY_FIXTURE"}
    completion = run_once(out, **_kwargs(preflight=lambda: identity))
    assert completion["preflight_identity"]["family"] == "LITE"
    assert completion["preflight_identity"]["checkpoint_sha"] == "b" * 64
    assert _read(out / "consumed.json")["preflight_identity"] == identity
    # run_once never grants anything: identity is opaque caller-supplied data
    assert set(completion) == {"status", "evidence_class", "counts",
                               "preflight_identity", "per_sample_sha256"}


# --------------------------------------------------------------------------- #
# Authorization, duplicate refusal, interruption, fail-closed
# --------------------------------------------------------------------------- #
def test_authorization_refusal_happens_before_output_and_reader(tmp_path):
    out = tmp_path / "attempt"

    def refuse():
        raise PermissionError("SYNTHETIC_AUTHORIZATION_REFUSED")

    with pytest.raises(PermissionError, match="SYNTHETIC_AUTHORIZATION_REFUSED"):
        run_once(out, **_kwargs(preflight=refuse,
                                load_population=lambda: pytest.fail("reader reached")))
    assert not out.exists()


def test_duplicate_attempt_is_refused_without_a_second_evaluation(tmp_path):
    out = tmp_path / "attempt"
    calls = []
    kwargs = _kwargs(evaluate=lambda row: (calls.append(row["sample_id"]),
                                           dict(row, dice=0.5))[1])
    run_once(out, **kwargs)
    before = list(calls)
    with pytest.raises(ConsumedAttemptError):
        run_once(out, **kwargs)
    assert calls == before
    assert len(_read(out / "per_sample.json")["records"]) == len(SAMPLE_IDS)


def test_interrupted_attempt_after_mkdir_is_consumed_forever(tmp_path):
    out = tmp_path / "attempt"
    out.mkdir()  # simulate a crash immediately after the exclusive mkdir
    calls = []

    def preflight():
        calls.append("preflight")
        return {"fixture": True}

    with pytest.raises(ConsumedAttemptError):
        run_once(out, **_kwargs(preflight=preflight,
                                load_population=lambda: pytest.fail("reader reached")))
    assert calls == []  # refused before invoking any authorization callback


def test_mid_evaluation_interruption_is_consumed_and_unpublished(tmp_path):
    out = tmp_path / "attempt"

    def evaluate(row):
        if row["sample_id"] == "s2":
            raise KeyboardInterrupt("SYNTHETIC_INTERRUPTION")
        return dict(row, dice=0.5, state="SKIP_GLOBAL")

    with pytest.raises(KeyboardInterrupt):
        run_once(out, **_kwargs(evaluate=evaluate))
    failure = _read(out / "failure.json")
    assert failure["status"] == "FAILED_CONSUMED"
    assert failure["exception_type"] == "KeyboardInterrupt"
    assert failure["counts"]["completed_samples"] == 1
    assert failure["counts"]["evaluation_attempts"] == 2
    assert failure["automatic_retry"] is False
    assert not (out / "completion.json").exists()
    assert not (out / "per_sample.json").exists()
    with pytest.raises(ConsumedAttemptError):
        run_once(out, **_kwargs())


@pytest.mark.parametrize("mode", ["population", "duplicate_population", "infer",
                                  "nonfinite", "wrong_sample_id"])
def test_fail_closed_on_malformed_synthetic_inputs(tmp_path, mode):
    out = tmp_path / "attempt"
    populations = {
        "population": [{"sample_id": "unfrozen"}],
        "duplicate_population": [{"sample_id": "s1"}, {"sample_id": "s1"}],
        "infer": [{"sample_id": "s1"}],
        "nonfinite": [{"sample_id": "s1"}],
        "wrong_sample_id": [{"sample_id": "s1"}],
    }

    def evaluate(row):
        if mode == "infer":
            raise RuntimeError("SYNTHETIC_INFERENCE_FAILURE")
        if mode == "wrong_sample_id":
            return {"sample_id": "someone_else", "dice": 0.5}
        if mode == "nonfinite":
            return dict(row, dice=float("nan"))
        return dict(row, dice=0.5)

    with pytest.raises((RuntimeError, ValueError)):
        run_once(out, **_kwargs(load_population=lambda: populations[mode],
                                evaluate=evaluate, expected_ids=("s1",)))
    assert not (out / "completion.json").exists()
    failure = _read(out / "failure.json")
    assert failure["status"] == "FAILED_CONSUMED"
    assert failure["automatic_retry"] is False
    with pytest.raises(ConsumedAttemptError):
        run_once(out, **_kwargs(expected_ids=("s1",)))


@pytest.mark.parametrize("bad", [
    dict(expected_ids=()),
    dict(expected_ids=("s1", "s1")),
    dict(evidence_class="AUTHORIZED_REAL_EVALUATION"),
    dict(evidence_class=""),
])
def test_invalid_contract_rejected_before_any_output(tmp_path, bad):
    out = tmp_path / "attempt"
    with pytest.raises(ValueError):
        run_once(out, **_kwargs(**bad))
    assert not out.exists()


def test_no_test_time_tuning_surface_exists():
    params = list(inspect.signature(run_once).parameters)
    assert params == ["output", "preflight", "load_population", "evaluate",
                      "expected_ids", "evidence_class"]
    forbidden = ("threshold", "tune", "calibrat", "learning_rate", "lr",
                 "checkpoint", "device", "epoch", "seed")
    assert not [p for p in params if any(f in p.lower() for f in forbidden)]
    # Frozen v1.2 constants are declarative, not adjustable from this surface.
    C = P39.C
    assert C.TEST_N == 1683
    assert C.SEGMENTATION_THRESHOLD == 0.50
    assert C.ROI_P_GLOBAL_THRESHOLD == 0.30
    assert C.S_OMEGA_ACCEPT_THRESHOLD == 0.50
    assert "no overwrite fallback" in C.WRITE_SEMANTICS
    assert "open(x" in C.WRITE_SEMANTICS


def test_summarize_is_pure_aggregation_without_tuning(tmp_path):
    records = [
        {"domain": "ISIC", "dice": 0.2}, {"domain": "ISIC", "dice": 0.4},
        {"domain": "BUSI", "dice": 0.6}, {"domain": "KUB", "dice": 0.8},
    ]
    summary = P39.summarize(records)
    by = {d["domain"]: d for d in summary["per_domain"]}
    assert [d["domain"] for d in summary["per_domain"]] == P39.C.DOMAIN_ORDER
    assert by["ISIC"]["n"] == 2 and by["ISIC"]["dice_mean"] == pytest.approx(0.3)
    assert by["KVASIR"]["n"] == 0 and by["KVASIR"]["dice_mean"] is None
    assert by["KUB"]["task_id"] == P39.C.TASKS_REV["KUB"]
    assert summary["macro_dice"] == pytest.approx((0.3 + 0.6 + 0.8) / 3)


# --------------------------------------------------------------------------- #
# Protected v1.2 static preflight — exercised with REDIRECTED synthetic ROOT only
# --------------------------------------------------------------------------- #
def _checks_from_preflight_failure(exc) -> dict:
    text = str(exc)
    marker = "PHASE39_V1_2_PREFLIGHT_FAILED: "
    assert marker in text
    return ast.literal_eval(text.split(marker, 1)[1])


def test_phase39_static_preflight_fails_closed_on_empty_synthetic_root(monkeypatch, tmp_path):
    monkeypatch.setattr(P39.C, "ROOT", tmp_path)
    monkeypatch.delenv(P39.C.GATE_ENV, raising=False)
    with pytest.raises(P39.PreflightFailure) as excinfo:
        P39.preflight_static()
    checks = _checks_from_preflight_failure(excinfo.value)
    assert checks["gate_env_present"] is False
    assert checks["checkpoint_sha_match"] is False
    assert checks["amendment_present"] is False
    assert checks["authority_bundle_present"] is False
    assert checks["phase37_root_manifest_sha_match"] is False
    assert checks["canonical_phase36_module_present"] is False
    assert checks["all_v1_2_output_targets_absent"] is True

    with pytest.raises(P39.PreflightFailure, match="HISTORY_GATE_FAILED"):
        P39.history_gate()


def test_phase39_checkpoint_sha_binding_and_no_silent_fallback(monkeypatch, tmp_path):
    """Synthetic component bytes bind the family; tampering or a missing key fails."""
    monkeypatch.setattr(P39.C, "ROOT", tmp_path)
    monkeypatch.delenv(P39.C.GATE_ENV, raising=False)
    components = {}
    for name in ("G", "B_phi", "R_psi", "S_omega"):
        rel = Path("synthetic_ckpts") / f"{name}.pt"
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        blob = f"SYNTHETIC_TEST_ONLY_{name}".encode()
        target.write_bytes(blob)
        components[name] = {"checkpoint": rel.as_posix(),
                           "sha256": hashlib.sha256(blob).hexdigest()}
    monkeypatch.setattr(P39.C, "COMPONENTS", components)

    with pytest.raises(P39.PreflightFailure) as ok:
        P39.preflight_static()
    assert _checks_from_preflight_failure(ok.value)["checkpoint_sha_match"] is True

    # One flipped byte must break the family identity.
    (tmp_path / components["G"]["checkpoint"]).write_bytes(b"TAMPERED")
    with pytest.raises(P39.PreflightFailure) as bad:
        P39.preflight_static()
    assert _checks_from_preflight_failure(bad.value)["checkpoint_sha_match"] is False

    # A missing sha256 key must raise, never resolve via an `or` fallback.
    (tmp_path / components["G"]["checkpoint"]).write_bytes(b"TAMPERED")
    broken = dict(components)
    broken["G"] = {"checkpoint": components["G"]["checkpoint"]}
    monkeypatch.setattr(P39.C, "COMPONENTS", broken)
    with pytest.raises(KeyError, match="sha256"):
        P39.preflight_static()


def test_phase39_main_refuses_without_opening_any_reader(monkeypatch, tmp_path):
    monkeypatch.setattr(P39.C, "ROOT", tmp_path)
    monkeypatch.delenv(P39.C.GATE_ENV, raising=False)
    monkeypatch.setattr(P39, "load_models", lambda: pytest.fail("model load reached"))
    monkeypatch.setattr(P39, "open_manifest", lambda _: pytest.fail("manifest opened"))
    assert P39.main() == 1
    failure = _read(tmp_path / P39.C.OUT["FAILURE"])
    assert "PREFLIGHT" in str(failure) or "HISTORY_GATE" in str(failure)
    assert failure["automatic_retry"] is False
    assert all(v is False for v in failure["observability"].values())
    assert not (tmp_path / P39.C.OUT["RESULT"]).exists()


def test_real_test_evaluation_is_explicitly_not_executed():
    """The protected cohort stays pending; synthetic verification is NOT science."""
    C = P39.C
    assert CODING_VERDICT != SCIENCE_VERDICT
    assert C.POPULATION_NAME == "TEST" and C.TEST_N == 1683
    assert C.EVIDENCE_CLASS.startswith("POST_PROTOCOL_TECHNICAL_RECOVERY")
    assert C.GATE_ENV == "PHASE39_FINAL_TEST_GATE"
    assert C.GATE_ENV_VALUE == "I_ACKNOWLEDGE_PHASE39_ONE_SHOT_TEST_EXECUTION"
    assert C.OUT["RESULT"].endswith("scientific_result.json")
    # This suite never sets the one-shot gate and never calls the real reader.
    assert SYNTHETIC == "SYNTHETIC_TEST_ONLY"
    assert "AUTHORIZED_FROZEN_EVALUATION" not in SYNTHETIC
