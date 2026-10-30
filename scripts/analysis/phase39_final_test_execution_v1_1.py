"""Phase39 final TEST execution source (v1.1) — D98 dependency-closure repair.

Minimal delta from v1.0:
  (D98)   the extracted-class loader now injects the frozen module globals
          (FEATURE_DIM / HIDDEN / NUMERIC_IDX / ONEHOT_IDX);
  (order) all TEST-independent pre-inference work (authority/source gates,
          model construction + strict load, device binding, metric/comparator
          binding, output-absence) happens BEFORE first TEST-manifest access;
  (gate)  a v1.0 consumed-history gate runs first and fails closed on drift;
  (ns)    a distinct v1.1 output namespace.

scientific_delta_v1_0_to_v1_1 = 0. ONE-SHOT. Never auto-retry.
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

import scripts.analysis.phase39_final_test_common_v1_1 as C  # noqa: E402


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


class PreflightFailure(RuntimeError):
    """Raised BEFORE any TEST inference. Never a scientific failure."""


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


# ====================================================================== #
# v1.0 CONSUMED-HISTORY GATE (Task 9)
# ====================================================================== #
def v1_0_history_gate() -> dict:
    h = C.V1_0_HISTORY
    checks = {}
    fp = C.ROOT / h["failure_path"]
    pe = C.ROOT / h["process_exit_path"]
    jp = C.ROOT / h["journal_path"]
    checks["v1_0_failure_present"] = fp.exists()
    checks["v1_0_failure_sha_match"] = fp.exists() and _sha(fp) == h["failure_sha256"]
    checks["v1_0_process_exit_sha_match"] = pe.exists() and _sha(pe) == h["process_exit_sha256"]
    checks["v1_0_journal_sha_match"] = jp.exists() and _sha(jp) == h["journal_sha256"]
    checks["v1_0_RESULT_absent"] = not (C.ROOT / h["result_path"]).exists()
    checks["v1_0_START_absent"] = not (C.ROOT / h["start_path"]).exists()
    checks["v1_0_preinference"] = h["test_inference_started"] is False
    checks["same_version_rerun_forbidden"] = h["same_version_rerun_permitted"] is False
    if not all(checks.values()):
        raise PreflightFailure(f"PHASE39_V1_0_HISTORY_GATE_FAILED: {checks}")
    return checks


# ====================================================================== #
# Pre-inference gates (NO TEST access)
# ====================================================================== #
def preflight_static() -> dict:
    checks = {}
    venv_py = C.ROOT / ".venv" / "Scripts" / "python.exe"
    checks["gate_env_present"] = os.environ.get(C.GATE_ENV) == C.GATE_ENV_VALUE
    checks["interpreter_is_canonical_venv"] = Path(sys.executable).resolve() == venv_py.resolve()
    checks["authority_bundle_present"] = (C.ROOT / C.AUTHORITY_BUNDLE).exists()
    checks["checkpoint_sha_match"] = all(
        (C.ROOT / c["checkpoint"]).exists() and _sha(C.ROOT / c["checkpoint"]) == c["sha256"]
        for c in C.COMPONENTS.values())
    p37 = C.ROOT / C.PHASE37_ROOT_MANIFEST
    checks["phase37_root_manifest_sha_match"] = p37.exists() and _sha(p37) == C.PHASE37_ROOT_MANIFEST_SHA256
    targets = [C.OUT["START"], C.OUT["RESULT"], C.OUT["FAILURE"], C.OUT["PROCESS_EXIT"]]
    checks["all_v1_1_output_targets_absent"] = all(not (C.ROOT / t).exists() for t in targets)
    checks["test_manifest_path_configured"] = bool(C.TEST_MANIFEST)
    if not all(checks.values()):
        raise PreflightFailure(f"PHASE39_V1_1_PREFLIGHT_FAILED: {checks}")
    return checks


def load_models():
    import scripts.analysis.phase39_final_test_model_loader_v1_1 as loader
    return loader.build_all_models()


def bind_metric_comparator():
    from src.metrics import evaluation_metrics as M
    return {"metric_module": C.METRIC_MODULE,
            "dice": callable(getattr(M, "dice", None)),
            "iou": callable(getattr(M, "iou", None)),
            "hd95": callable(getattr(M, "hd95", None)),
            "comparators": ["C-gGLOBAL", "C-A7"]}


# ====================================================================== #
# FIRST TES T access (AFTER all static gates + model load)
# ====================================================================== #
def open_test_manifest() -> list:
    p = C.ROOT / C.TEST_MANIFEST
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def assert_population(rows) -> None:
    n = len(rows)
    if n != C.TEST_N:
        raise PreflightFailure(f"PHASE39_WRONG_POPULATION_CARDINALITY: {n} != {C.TEST_N}")


def run_science(models, device, rows) -> dict:
    counters = {"test_samples": len(rows), "test_image_reads": 0, "test_gt_reads": 0,
                "model_forwards": 0, "metric_evaluations": 0, "training": 0,
                "optimizer_steps": 0, "parameter_mutations": 0,
                "checkpoint_selections": 0, "threshold_selections": 0, "hyperparameter_selections": 0}
    per_sample = []
    from scripts.analysis.phase39_final_test_inference_v1_1 import evaluate_sample
    for r in rows:
        domain = str(r.get("domain", ""))
        task_id = int(r.get("task_id", r.get("task", -1)))
        if domain not in C.DOMAIN_ORDER or task_id not in C.TASKS:
            raise PreflightFailure(f"PHASE39_UNEXPECTED_TASK_DOMAIN: {domain}/{task_id}")
        per_sample.append(evaluate_sample(models, device, r, counters))
    return {"per_sample": per_sample, "counters": counters}


def summarize(per_sample) -> dict:
    import numpy as np
    domains = {}
    for r in per_sample:
        domains.setdefault(r["domain"], []).append(r)
    per_domain = []
    for d in C.DOMAIN_ORDER:
        sub = domains.get(d, [])
        if not sub:
            per_domain.append({"domain": d, "task_id": C.TASKS_REV.get(d), "n": 0,
                               "dice_mean": None, "dice_median": None})
            continue
        dice = np.asarray([x["dice"] for x in sub], dtype=np.float64)
        per_domain.append({"domain": d, "task_id": C.TASKS_REV.get(d), "n": int(dice.size),
                           "dice_mean": float(np.mean(dice)), "dice_median": float(np.median(dice))})
    means = [d["dice_mean"] for d in per_domain if d.get("dice_mean") is not None]
    return {"per_domain": per_domain, "macro_dice": (float(np.mean(means)) if means else None)}


def build_result(models_audit, metric_binding, science) -> dict:
    return {
        "classification": C.CLASSIFICATION, "evidence_class": C.EVIDENCE_CLASS,
        "revision": C.REVISION, "phase": C.PHASE, "method": C.METHOD,
        "generated_utc": _now(), "population": C.POPULATION_NAME, "test_n": C.TEST_N,
        "component_load_audit": models_audit, "metric_binding": metric_binding,
        "counters": science["counters"], "summary": summarize(science["per_sample"]),
        "phase30_qualifier": C.PHASE30_QUALIFIER, "source_sha256": _sha(Path(__file__)),
        "epistemic_label": "TEST_MEMBERSHIP_ACCESSED_ON_CONSUMED_V1_0_PREINFERENCE_ATTEMPT__NO_TEST_IMAGE_OR_GT_PIXELS_ACCESSED__NO_TEST_OUTCOME_OBSERVED",
    }


def write_start():
    _exclusive_write_json(C.OUT["START"], {
        "classification": "PHASE39_FINAL_TEST_START", "revision": C.REVISION, "phase": C.PHASE,
        "population": C.POPULATION_NAME, "test_n": C.TEST_N, "method": C.METHOD,
        "generated_utc": _now(), "one_shot": True, "attempt_consumed_on_open": True})


def write_result(models_audit, metric_binding, science):
    obj = build_result(models_audit, metric_binding, science)
    _exclusive_write_json(C.OUT["RESULT"], obj)
    if science["per_sample"]:
        hdr = list(science["per_sample"][0].keys())
        _exclusive_write_csv(C.OUT["per_sample_table"], hdr,
                             [[r[h] for h in hdr] for r in science["per_sample"]])
    pd = obj["summary"]["per_domain"]
    if pd:
        hdr = list(pd[0].keys())
        _exclusive_write_csv(C.OUT["per_domain_summary"], hdr, [[d[h] for h in hdr] for d in pd])


def write_failure(exc, stage):
    _exclusive_write_json(C.OUT["FAILURE"], {
        "classification": "PHASE39_FINAL_TEST_FAILURE", "revision": C.REVISION, "phase": C.PHASE,
        "generated_utc": _now(), "failure_stage": stage,
        "exception_type": type(exc).__name__, "exception": str(exc),
        "test_inference_started": stage == "SCIENCE_LOOP", "automatic_retry": False})


def write_process_exit(rc):
    _exclusive_write_json(C.OUT["PROCESS_EXIT"], {
        "classification": "PHASE39_FINAL_TEST_PROCESS_EXIT", "revision": C.REVISION,
        "phase": C.PHASE, "process_exit_code": int(rc), "generated_utc": _now()})


def main() -> int:
    stage = "V1_0_HISTORY_GATE"
    try:
        v1_0_history_gate()
        stage = "STATIC_PREFLIGHT"
        preflight_static()
        stage = "MODEL_LOAD"          # BEFORE any TEST access
        models, device, models_audit = load_models()
        stage = "METRIC_BINDING"
        metric_binding = bind_metric_comparator()
        if not (metric_binding["dice"] and metric_binding["iou"] and metric_binding["hd95"]):
            raise PreflightFailure("PHASE39_METRIC_BINDING_FAILED")
        stage = "TEST_MANIFEST_OPEN"  # FIRST TEST access
        rows = open_test_manifest()
        assert_population(rows)
        write_start()
        stage = "SCIENCE_LOOP"
        science = run_science(models, device, rows)
        write_result(models_audit, metric_binding, science)
        write_process_exit(0)
        return 0
    except Exception as exc:  # noqa: BLE001 -- fail closed, never auto-retry
        try:
            write_failure(exc, stage)
            write_process_exit(1)
        except FileExistsError:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
