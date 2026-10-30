"""Phase39 final TEST execution source — v1.2 (post-protocol technical recovery).

Authority: reports/audits/phase39_post_protocol_technical_recovery_amendment.json.
Reuses frozen canonical Phase36 v1.23 inference. ONE-SHOT. No auto-retry.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import scripts.analysis.phase39_final_test_common_v1_2 as C  # noqa: E402


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


class PreflightFailure(RuntimeError):
    pass


def _exclusive_write_json(rel, obj):
    p = C.ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "x", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
    return p


def _exclusive_write_csv(rel, header, rows):
    p = C.ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "x", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return p


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_observability():
    return {"manifest_access_started": False, "test_image_access_started": False,
            "test_gt_access_started": False, "model_forward_started": False,
            "metric_evaluation_started": False}


def history_gate() -> dict:
    checks = {}
    for ver, h in C.HISTORY.items():
        for k in ("failure", "process_exit", "journal"):
            p = C.ROOT / h[f"{k}_path"]
            checks[f"{ver}_{k}_present"] = p.exists()
            checks[f"{ver}_{k}_sha_match"] = p.exists() and _sha(p) == h[f"{k}_sha256"]
        checks[f"{ver}_RESULT_absent"] = not (C.ROOT / h["result_path"]).exists()
    for ver in C.HISTORY:
        if "start_path" in C.HISTORY[ver]:
            sp = C.ROOT / C.HISTORY[ver]["start_path"]
            checks[f"{ver}_start_sha_match"] = sp.exists() and _sha(sp) == C.HISTORY[ver]["start_sha256"]
    if not all(checks.values()):
        raise PreflightFailure(f"PHASE39_V1_2_HISTORY_GATE_FAILED: {checks}")
    return checks


def preflight_static() -> dict:
    checks = {}
    venv_py = C.ROOT / ".venv" / "Scripts" / "python.exe"
    checks["gate_env_present"] = os.environ.get(C.GATE_ENV) == C.GATE_ENV_VALUE
    checks["interpreter_is_canonical_venv"] = Path(sys.executable).resolve() == venv_py.resolve()
    checks["amendment_present"] = (C.ROOT / C.AMENDMENT).exists()
    checks["authority_bundle_present"] = (C.ROOT / C.AUTHORITY_BUNDLE).exists()
    checks["checkpoint_sha_match"] = all(
        (C.ROOT / c["checkpoint"]).exists() and _sha(C.ROOT / c["checkpoint"]) == c["sha256"]
        for c in C.COMPONENTS.values())
    p37 = C.ROOT / C.PHASE37_ROOT_MANIFEST
    checks["phase37_root_manifest_sha_match"] = p37.exists() and _sha(p37) == C.PHASE37_ROOT_MANIFEST_SHA256
    checks["canonical_phase36_module_present"] = (C.ROOT / C.CANONICAL_PHASE36_MODULE).exists()
    targets = [C.OUT["START"], C.OUT["RESULT"], C.OUT["FAILURE"], C.OUT["PROCESS_EXIT"]]
    checks["all_v1_2_output_targets_absent"] = all(not (C.ROOT / t).exists() for t in targets)
    if not all(checks.values()):
        raise PreflightFailure(f"PHASE39_V1_2_PREFLIGHT_FAILED: {checks}")
    return checks


def load_models():
    import scripts.analysis.phase36_robustness_execution_v1_23 as P36
    ctx = P36._load_models()          # returns the canonical context dict
    return ctx, ctx["load_audit"]


def open_manifest(obs):
    obs["manifest_access_started"] = True
    with open(C.ROOT / C.TEST_MANIFEST, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def summarize(records) -> dict:
    import numpy as np
    by_dom = {}
    for r in records:
        by_dom.setdefault(r["domain"], []).append(r)
    per_domain = []
    for d in C.DOMAIN_ORDER:
        sub = by_dom.get(d, [])
        if not sub:
            per_domain.append({"domain": d, "task_id": C.TASKS_REV[d], "n": 0, "dice_mean": None, "dice_median": None})
            continue
        dice = np.asarray([x["dice"] for x in sub], dtype=np.float64)
        per_domain.append({"domain": d, "task_id": C.TASKS_REV[d], "n": int(dice.size),
                           "dice_mean": float(np.mean(dice)), "dice_median": float(np.median(dice))})
    means = [d["dice_mean"] for d in per_domain if d["dice_mean"] is not None]
    return {"per_domain": per_domain, "macro_dice": (float(np.mean(means)) if means else None)}


def write_start():
    _exclusive_write_json(C.OUT["START"], {
        "classification": "PHASE39_FINAL_TEST_START", "revision": C.REVISION, "phase": C.PHASE,
        "population": C.POPULATION_NAME, "test_n": C.TEST_N, "method": C.METHOD,
        "generated_utc": _now(), "one_shot": True, "attempt_consumed_on_open": True,
        "authority": C.AMENDMENT})


def write_result(load_audit, counters, records):
    summ = summarize(records)
    obj = {"classification": C.CLASSIFICATION, "evidence_class": C.EVIDENCE_CLASS,
           "revision": C.REVISION, "phase": C.PHASE, "method": C.METHOD, "generated_utc": _now(),
           "population": C.POPULATION_NAME, "test_n": C.TEST_N,
           "component_load_audit": load_audit, "counters": counters, "summary": summ,
           "phase30_qualifier": C.PHASE30_QUALIFIER,
           "source_sha256": _sha(Path(__file__)),
           "manifest_schema_domain_field": C.DOMAIN_FIELD}
    _exclusive_write_json(C.OUT["RESULT"], obj)
    if records:
        hdr = list(records[0].keys())
        _exclusive_write_csv(C.OUT["per_sample_table"], hdr, [[r[h] for h in hdr] for r in records])
    pd = summ["per_domain"]
    hdr = list(pd[0].keys())
    _exclusive_write_csv(C.OUT["per_domain_summary"], hdr, [[d[h] for h in hdr] for d in pd])


def write_failure(exc, stage, obs, counters):
    _exclusive_write_json(C.OUT["FAILURE"], {
        "classification": "PHASE39_FINAL_TEST_FAILURE", "revision": C.REVISION, "phase": C.PHASE,
        "generated_utc": _now(), "failure_stage": stage,
        "exception_type": type(exc).__name__, "exception": str(exc),
        "observability": obs, "counters": counters, "automatic_retry": False})


def write_process_exit(rc):
    _exclusive_write_json(C.OUT["PROCESS_EXIT"], {
        "classification": "PHASE39_FINAL_TEST_PROCESS_EXIT", "revision": C.REVISION,
        "phase": C.PHASE, "process_exit_code": int(rc), "generated_utc": _now()})


def main() -> int:
    stage = "V1_0_V1_1_HISTORY_GATE"
    obs = _new_observability()
    counters = {}
    try:
        history_gate()
        stage = "STATIC_PREFLIGHT"
        preflight_static()
        stage = "MODEL_LOAD"
        ctx, load_audit = load_models()
        stage = "MANIFEST_OPEN"
        rows = open_manifest(obs)
        stage = "POPULATION_VALIDATE"
        import scripts.analysis.phase39_final_test_inference_v1_2 as X
        if len(rows) != C.TEST_N:
            raise PreflightFailure(f"PHASE39_WRONG_POPULATION_CARDINALITY: {len(rows)} != {C.TEST_N}")
        ok, errors = X.validate_population(rows)
        if not ok:
            raise PreflightFailure(f"PHASE39_MANIFEST_SCHEMA_INVALID: {errors}")
        write_start()
        stage = "SCIENCE_LOOP"
        generated = X.generate_g_artifacts(ctx, rows, counters)
        records = X.evaluate_population(ctx, rows, generated, counters, obs)
        write_result(load_audit, counters, records)
        write_process_exit(0)
        return 0
    except Exception as exc:  # noqa: BLE001
        try:
            write_failure(exc, stage, obs, counters)
            write_process_exit(1)
        except FileExistsError:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
