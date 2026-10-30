"""Phase39 final TEST execution source (v1.0) — FROZEN DURING PHASE38.

ONE-SHOT final untouched internal TEST evaluation of the frozen RA-MedFiLM-BARR
system. Implements ONLY the frozen protocol. Fails closed before any TEST
inference on any authority/consistency violation.

This file performs NO science at import time and NO science in Phase38.

Defect/attempt policy: see reports/audits/phase38_phase39_retry_failure_policy.json.
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

import scripts.analysis.phase39_final_test_common_v1_0 as C  # noqa: E402


# ====================================================================== #
# Fail-closed primitives
# ====================================================================== #
def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


class PreflightFailure(RuntimeError):
    """Raised BEFORE any TEST inference. Never a scientific failure."""


def _exclusive_write_json(rel: str, obj: dict) -> Path:
    p = C.ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "x", encoding="utf-8") as fh:   # exclusive-create; no overwrite
        json.dump(obj, fh, indent=2, ensure_ascii=False)
    return p


def _exclusive_write_csv(rel: str, header, rows) -> Path:
    p = C.ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "x", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return p


# ====================================================================== #
# Pre-inference fail-closed gates
# ====================================================================== #
def preflight() -> dict:
    """All gates that must pass BEFORE any TEST inference. Fail closed."""
    checks = {}

    # 1. Gate environment must be explicitly acknowledged.
    checks["gate_env_present"] = os.environ.get(C.GATE_ENV) == C.GATE_ENV_VALUE

    # 2. Interpreter check (fail closed on the canonical venv interpreter).
    venv_py = C.ROOT / ".venv" / "Scripts" / "python.exe"
    checks["interpreter_is_canonical_venv"] = Path(sys.executable).resolve() == venv_py.resolve()

    # 3. Authority bundle bound + hash recorded.
    bundle = C.ROOT / C.AUTHORITY_BUNDLE
    checks["authority_bundle_present"] = bundle.exists()

    # 4. Checkpoint SHA match (all four).
    checks["checkpoint_sha_match"] = all(
        (C.ROOT / c["checkpoint"]).exists() and _sha(C.ROOT / c["checkpoint"]) == c["sha256"]
        for c in C.COMPONENTS.values())

    # 5. Phase37 root manifest bound.
    p37 = C.ROOT / C.PHASE37_ROOT_MANIFEST
    checks["phase37_root_manifest_sha_match"] = (
        p37.exists() and _sha(p37) == C.PHASE37_ROOT_MANIFEST_SHA256)

    # 6. Output absence gate (no START/RESULT/FAILURE/PROCESS_EXIT target exists).
    targets = [C.OUT["START"], C.OUT["RESULT"], C.OUT["FAILURE"], C.OUT["PROCESS_EXIT"]]
    checks["all_output_targets_absent"] = all(not (C.ROOT / t).exists() for t in targets)

    # 7. TEST manifest present (path bound; NOT read here).
    checks["test_manifest_present"] = (C.ROOT / C.TEST_MANIFEST).exists()

    if not all(checks.values()):
        raise PreflightFailure(f"PHASE39_PREFLIGHT_FAILED: {checks}")
    return checks


def _load_test_manifest() -> list:
    """Read the TEST manifest (metadata). This is the FIRST authorized TEST access."""
    p = C.ROOT / C.TEST_MANIFEST
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _assert_population(rows) -> None:
    n = len(rows)
    if n != C.TEST_N:
        raise PreflightFailure(f"PHASE39_WRONG_POPULATION_CARDINALITY: {n} != {C.TEST_N}")
    seen = {str(r.get("task_id", r.get("task", ""))) for r in rows}
    allowed = {str(k) for k in C.TASKS}
    if not seen.issubset(allowed | {""}):
        raise PreflightFailure(f"PHASE39_UNEXPECTED_TASK_DOMAIN: {sorted(seen - allowed)}")


# ====================================================================== #
# Model loading (strict, fail-closed)
# ====================================================================== #
def load_models():
    import torch
    from src.models.film.global_medfilm import GlobalMedFiLM
    from src.models.barr.regional_refiner import BARRRegionalRefinerV1
    from src.utils.device import get_device

    device = get_device(require_cuda=True)
    if str(getattr(device, "type", device)) != C.CANONICAL_DEVICE_CONTRACT["required_device_type"]:
        raise PreflightFailure("PHASE39_CUDA_FAIL_CLOSED__NOT_CUDA")

    cfg = json.loads((C.ROOT / "configs/phase21_global_medfilm_fourdomain_clean_v3.yaml").read_text(encoding="utf-8")) \
        if (C.ROOT / "configs/phase21_global_medfilm_fourdomain_clean_v3.yaml").exists() else None
    # G config lives beside the checkpoint family; resolved via the frozen loader contract.
    g = GlobalMedFiLM()
    r_psi = BARRRegionalRefinerV1()
    # B_phi / S_omega classes are loaded via the frozen dynamic class loaders
    # (identical contract to the consumed Phase36 pipeline).
    from scripts.analysis.phase39_final_test_model_loader_v1_0 import load_router, load_somega
    b_phi = load_router()
    s_omega = load_somega()

    audit = {}
    for name, m in (("G", g), ("R_psi", r_psi), ("B_phi", b_phi), ("S_omega", s_omega)):
        ck = torch.load(C.ROOT / C.COMPONENTS[name]["checkpoint"], map_location="cpu", weights_only=False)
        res = m.load_state_dict(ck["model_state"], strict=True)
        m.eval(); m.requires_grad_(False)
        n_params = int(sum(p.numel() for p in m.parameters()))
        audit[name] = {
            "checkpoint_sha256": _sha(C.ROOT / C.COMPONENTS[name]["checkpoint"]),
            "checkpoint_sha256_expected": C.COMPONENTS[name]["sha256"],
            "parameter_count": n_params,
            "parameter_count_expected": C.COMPONENTS[name]["params"],
            "missing_keys": list(getattr(res, "missing_keys", [])),
            "unexpected_keys": list(getattr(res, "unexpected_keys", [])),
            "all_weights_finite": bool(all(bool(torch.isfinite(p).all()) for p in m.parameters())),
        }
    ok = (all(v["parameter_count"] == v["parameter_count_expected"] for v in audit.values())
          and all(not v["missing_keys"] and not v["unexpected_keys"] for v in audit.values())
          and all(v["all_weights_finite"] for v in audit.values())
          and all(v["checkpoint_sha256"] == v["checkpoint_sha256_expected"] for v in audit.values()))
    if not ok:
        raise PreflightFailure(f"PHASE39_COMPONENT_LOAD_FAILURE: {audit}")
    for m in (g, r_psi, b_phi, s_omega):
        m.to(device)
    return {"G": g, "R_psi": r_psi, "B_phi": b_phi, "S_omega": s_omega}, device, audit


# ====================================================================== #
# Science (frozen protocol) — executed ONLY in Phase39
# ====================================================================== #
def run_science(models, device, rows) -> dict:
    """The frozen RA-MedFiLM-BARR evaluation on the TEST population.

    Pipeline (frozen): G -> D75/POLICY_B global prob -> ROI(0.30/0.25/x1.5,
    canvas512/crop256) -> empty ROI => FORCED_SKIP -> B_phi utility gate ->
    R_psi -> S_omega(accept 0.50) -> D61 pad-aware fuse_full_field ->
    state machine {FORCED_SKIP,SKIP_GLOBAL,EXECUTE_THEN_ACCEPT,EXECUTE_THEN_REJECT}
    -> Dice/IoU/HD95 via src.metrics.evaluation_metrics.
    """
    counters = {
        "test_samples": len(rows), "test_image_reads": 0, "test_gt_reads": 0,
        "model_forwards": 0, "metric_evaluations": 0,
        "training": 0, "optimizer_steps": 0, "parameter_mutations": 0,
        "checkpoint_selections": 0, "threshold_selections": 0, "hyperparameter_selections": 0,
    }
    per_sample = []
    # NOTE: the per-sample loop invokes the frozen canonical inference helpers.
    # The loop body is intentionally the single frozen path (no perturbations).
    from scripts.analysis.phase39_final_test_inference_v1_0 import evaluate_sample
    for r in rows:
        sid = str(r.get("sample_id", r.get("id", "")))
        domain = str(r.get("domain", ""))
        task_id = int(r.get("task_id", r.get("task", -1)))
        if domain not in C.DOMAIN_ORDER or task_id not in C.TASKS:
            raise PreflightFailure(f"PHASE39_UNEXPECTED_TASK_DOMAIN: {domain}/{task_id}")
        out = evaluate_sample(models, device, r, counters)
        per_sample.append(out)
    return {"per_sample": per_sample, "counters": counters}


def _summarize(per_sample, counters) -> dict:
    import numpy as np
    rows = list(per_sample)
    domains = {}
    for r in rows:
        domains.setdefault(r["domain"], []).append(r)
    per_domain = []
    for d in C.DOMAIN_ORDER:
        sub = domains.get(d, [])
        if not sub:
            per_domain.append({"domain": d, "task_id": C.TASKS_REV.get(d), "n": 0,
                               "dice_mean": None, "dice_median": None})
            continue
        dice = np.asarray([x["dice"] for x in sub], dtype=np.float64)
        per_domain.append({"domain": d, "task_id": C.TASKS_REV.get(d),
                           "n": int(dice.size), "dice_mean": float(np.mean(dice)),
                           "dice_median": float(np.median(dice))})
    means = [d["dice_mean"] for d in per_domain if d.get("dice_mean") is not None]
    macro = float(np.mean(means)) if means else None
    return {"per_domain": per_domain, "macro_dice": macro}


# ====================================================================== #
# Artifact writers (write-once)
# ====================================================================== #
def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_start() -> None:
    _exclusive_write_json(C.OUT["START"], {
        "classification": "PHASE39_FINAL_TEST_START", "revision": C.REVISION,
        "phase": C.PHASE, "population": C.POPULATION_NAME, "test_n": C.TEST_N,
        "method": C.METHOD, "generated_utc": _now(),
        "one_shot": True, "attempt_consumed_on_open": True,
    })


def write_result(models_audit, science) -> None:
    summary = _summarize(science["per_sample"], science["counters"])
    obj = {
        "classification": C.CLASSIFICATION, "evidence_class": C.EVIDENCE_CLASS,
        "revision": C.REVISION, "phase": C.PHASE, "method": C.METHOD,
        "generated_utc": _now(), "population": C.POPULATION_NAME, "test_n": C.TEST_N,
        "component_load_audit": models_audit,
        "counters": science["counters"],
        "summary": summary,
        "phase30_qualifier": C.PHASE30_QUALIFIER,
        "source_sha256": _sha(Path(__file__)),
    }
    _exclusive_write_json(C.OUT["RESULT"], obj)
    # per-sample + per-domain tables (write-once)
    if science["per_sample"]:
        hdr = list(science["per_sample"][0].keys())
        _exclusive_write_csv(C.OUT["per_sample_table"], hdr,
                             [[r[h] for h in hdr] for r in science["per_sample"]])
    if summary["per_domain"]:
        hdr = list(summary["per_domain"][0].keys())
        _exclusive_write_csv(C.OUT["per_domain_summary"], hdr,
                             [[d[h] for h in hdr] for d in summary["per_domain"]])


def write_failure(exc: BaseException, phase: str) -> None:
    _exclusive_write_json(C.OUT["FAILURE"], {
        "classification": "PHASE39_FINAL_TEST_FAILURE", "revision": C.REVISION,
        "phase": C.PHASE, "generated_utc": _now(),
        "failure_stage": phase, "exception_type": type(exc).__name__, "exception": str(exc),
        "test_inference_started": phase == "SCIENCE_LOOP",
        "automatic_retry": False,
    })


def write_process_exit(rc: int) -> None:
    _exclusive_write_json(C.OUT["PROCESS_EXIT"], {
        "classification": "PHASE39_FINAL_TEST_PROCESS_EXIT", "revision": C.REVISION,
        "phase": C.PHASE, "process_exit_code": int(rc), "generated_utc": _now(),
    })


# ====================================================================== #
# Entry
# ====================================================================== #
def main() -> int:
    stage = "PREFLIGHT"
    try:
        preflight()
        stage = "TEST_MANIFEST_READ"
        rows = _load_test_manifest()
        _assert_population(rows)
        stage = "MODEL_LOAD"
        models, device, models_audit = load_models()
        # START is written after preflight + manifest + model load, immediately
        # before the one-shot science loop (the attempt is consumed here).
        write_start()
        stage = "SCIENCE_LOOP"
        science = run_science(models, device, rows)
        write_result(models_audit, science)
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
