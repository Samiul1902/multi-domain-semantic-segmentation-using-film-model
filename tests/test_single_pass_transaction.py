import json

import pytest

from src.research.evaluation.single_pass import ConsumedAttemptError, run_once


def test_refusal_before_reader_or_output(tmp_path):
    def refuse():
        raise PermissionError("synthetic refusal")
    with pytest.raises(PermissionError):
        run_once(tmp_path / "attempt", preflight=refuse,
                 load_population=lambda: pytest.fail("reader reached"), evaluate=lambda row: row,
                 expected_ids=("s1",), evidence_class="SYNTHETIC_TEST_ONLY")
    assert not (tmp_path / "attempt").exists()


def test_success_once_and_complete_exports(tmp_path):
    calls = []
    def load():
        assert (tmp_path / "attempt/consumed.json").exists()
        return [{"sample_id": "s2"}, {"sample_id": "s1"}]
    def evaluate(row):
        calls.append(row["sample_id"])
        return dict(row, dice=.5)
    kwargs = dict(preflight=lambda: {"fixture": True}, load_population=load,
                  evaluate=evaluate, expected_ids=("s1", "s2"), evidence_class="SYNTHETIC_TEST_ONLY")
    result = run_once(tmp_path / "attempt", **kwargs)
    assert calls == ["s1", "s2"] and result["counts"]["completed_samples"] == 2
    with pytest.raises(ConsumedAttemptError):
        run_once(tmp_path / "attempt", **kwargs)
    assert calls == ["s1", "s2"]


@pytest.mark.parametrize("mode", ["population", "infer", "nonfinite"])
def test_failed_attempt_is_consumed_and_unpublished(tmp_path, mode):
    def evaluate(row):
        if mode == "infer":
            raise RuntimeError("synthetic inference failure")
        return dict(row, dice=float("nan"))
    root = tmp_path / "attempt"
    kwargs = dict(preflight=lambda: {"fixture": True},
        load_population=lambda: [{"sample_id": "wrong" if mode == "population" else "s1"}],
        evaluate=evaluate, expected_ids=("s1",), evidence_class="SYNTHETIC_TEST_ONLY")
    with pytest.raises((RuntimeError, ValueError)):
        run_once(root, **kwargs)
    assert not (root / "completion.json").exists()
    assert json.loads((root / "failure.json").read_text())["status"] == "FAILED_CONSUMED"
    with pytest.raises(ConsumedAttemptError):
        run_once(root, **kwargs)
