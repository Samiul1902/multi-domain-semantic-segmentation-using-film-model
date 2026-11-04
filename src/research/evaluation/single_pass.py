"""Reusable one-shot transaction; authorization and readers remain external.

This module contains no data paths and supplies no authorization. The caller must
bind its existing phase-specific authorization, checkpoint, protocol and split
validators in ``preflight``. A consumed attempt can never be resumed or retried.
The completion manifest is published only after every result file is durable.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, Iterable, Mapping, Any

from src.research.deployment.artifacts import digest


class ConsumedAttemptError(RuntimeError):
    pass


def _write(path: Path, payload: Any) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, sort_keys=True, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def run_once(output: Path, *, preflight: Callable[[], Mapping[str, Any]],
             load_population: Callable[[], Iterable[Mapping[str, Any]]],
             evaluate: Callable[[Mapping[str, Any]], Mapping[str, Any]],
             expected_ids: tuple[str, ...], evidence_class: str) -> dict:
    """Consume after authorization, before reader initialization; fail closed.

    The preflight callback must raise on refusal. Its returned identity is recorded
    verbatim, not interpreted as a newly minted grant. No real reader is provided
    by this utility. Test fixtures cannot be installed as production credentials.
    """
    if not expected_ids or len(set(expected_ids)) != len(expected_ids):
        raise ValueError("nonempty unique frozen population IDs required")
    if evidence_class not in {"SYNTHETIC_TEST_ONLY", "AUTHORIZED_FROZEN_EVALUATION"}:
        raise ValueError("explicit evidence class required")
    output = Path(output)
    if output.exists():
        raise ConsumedAttemptError(str(output))
    identity = dict(preflight())  # Before even creating output or invoking a reader.
    # Atomic mkdir also arbitrates two concurrent attempts with the same ID.
    try:
        output.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise ConsumedAttemptError(str(output)) from exc
    _write(output / "consumed.json", {"preflight_identity": identity,
                                     "evidence_class": evidence_class, "automatic_retry": False})
    counts = {"population_rows": 0, "evaluation_attempts": 0, "completed_samples": 0}
    try:
        rows = list(load_population())
        counts["population_rows"] = len(rows)
        ids = tuple(row["sample_id"] for row in rows)
        if len(set(ids)) != len(ids) or set(ids) != set(expected_ids):
            raise ValueError("population differs from frozen identity")
        by_id = {row["sample_id"]: row for row in rows}
        results = []
        for sample_id in expected_ids:
            counts["evaluation_attempts"] += 1
            result = dict(evaluate(by_id[sample_id]))
            if result.get("sample_id") != sample_id:
                raise ValueError("evaluation output sample identity mismatch")
            results.append(result)
            counts["completed_samples"] += 1
        _write(output / "per_sample.json", {"evidence_class": evidence_class, "records": results})
        completion = {"status": "COMPLETE", "evidence_class": evidence_class,
                      "counts": counts, "preflight_identity": identity,
                      "per_sample_sha256": digest(output / "per_sample.json")}
        _write(output / "completion.json", completion)  # Sole publication marker, always last.
        return completion
    except BaseException as exc:
        _write(output / "failure.json", {"status": "FAILED_CONSUMED", "counts": counts,
                    "exception_type": type(exc).__name__, "reason": str(exc), "automatic_retry": False})
        raise
