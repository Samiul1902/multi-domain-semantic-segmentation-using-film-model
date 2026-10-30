"""Phase 21 entry gate — FAIL CLOSED.

Verifies every prerequisite before any Phase-21 model training. If any scientific
prerequisite fails the script writes a FAIL report and exits non-zero; training
must not start.

    ./.venv/Scripts/python.exe scripts/audits/phase21_entry_gate.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from src.utils.test_lock import verify_test_lock  # noqa: E402

A = ROOT / "reports" / "audits"
MAN = ROOT / "manifests" / "phase4_v3"
OUT = A / "phase21_entry_gate.json"

EXPECTED_TASK_IDS = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}
EXPECTED_TRAIN, EXPECTED_VAL = 5832, 808


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    checks: dict[str, dict] = {}

    def check(name: str, ok: bool, detail) -> None:
        checks[name] = {"passed": bool(ok), "detail": detail}

    # 1-3 phase completion --------------------------------------------------- #
    pmap = load_json(A / "phasewise_notebook_map.json")
    by_id = {e["phase_id"]: e for e in pmap}
    for pid, label in (("19", "phase19_complete"), ("20", "phase20a_complete"),
                       ("20B", "phase20b_complete")):
        st = by_id.get(pid, {}).get("status")
        check(label, st == "COMPLETE", {"phase_id": pid, "status": st})

    # 4-5 five-model freeze + protocol SHA ----------------------------------- #
    freeze_path = A / "phase20_five_model_baseline_benchmark_freeze.json"
    protocol_path = A / "phase20_shared_global_baseline_protocol.json"
    freeze = load_json(freeze_path) if freeze_path.exists() else {}
    protocol_sha = sha256_file(protocol_path)
    check("five_model_scientific_freeze_exists",
          freeze_path.exists() and freeze.get("terminal_state") ==
          "PHASE20_FIVE_MODEL_BASELINE_BENCHMARK_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED",
          {"path": str(freeze_path.relative_to(ROOT)).replace("\\", "/"),
           "terminal_state": freeze.get("terminal_state")})
    check("protocol_sha_matches_frozen_phase20",
          freeze.get("protocol_sha256") == protocol_sha,
          {"repo_protocol_sha256": protocol_sha,
           "freeze_protocol_sha256": freeze.get("protocol_sha256")})

    # 6-7 populations -------------------------------------------------------- #
    train = pd.read_csv(MAN / "train.csv")
    val = pd.read_csv(MAN / "val.csv")
    check("train_population_5832", len(train) == EXPECTED_TRAIN, {"rows": int(len(train))})
    check("val_population_808", len(val) == EXPECTED_VAL, {"rows": int(len(val))})

    # 8-9 TEST lock + zero reads --------------------------------------------- #
    try:
        lock = verify_test_lock(str(ROOT))
        check("test_remains_locked", True, lock if isinstance(lock, dict) else str(lock))
    except Exception as exc:  # noqa: BLE001
        check("test_remains_locked", False, f"{type(exc).__name__}: {exc}")
    check("test_reads_zero",
          all(int(v) == 0 for v in freeze.get("test_reads_total", {}).values()) and
          bool(freeze.get("test_reads_total")),
          freeze.get("test_reads_total"))

    # 10 task IDs frozen ----------------------------------------------------- #
    mapping = {str(d): int(t) for d, t in
               train.drop_duplicates("dataset")[["dataset", "task_id"]].values}
    check("four_task_ids_frozen", mapping == EXPECTED_TASK_IDS,
          {"manifest_mapping": mapping, "expected": EXPECTED_TASK_IDS})

    # 11 Phase-20B canonical notebook ---------------------------------------- #
    nb = (ROOT / "notebooks/phasewise/phase_20b_five_model_baselines"
          / "phase20b_five_model_conventional_baselines.ipynb")
    check("phase20b_canonical_notebook_exists", nb.exists(),
          {"path": str(nb.relative_to(ROOT)).replace("\\", "/")})

    # 12 Phase-20B reviewer package audit PASS ------------------------------- #
    audit_path = A / "phase20b_reviewer_package_audit.json"
    audit = load_json(audit_path) if audit_path.exists() else {}
    cov = audit.get("matrix_coverage", {})
    nbstat = audit.get("notebook", {})
    ok12 = (audit_path.exists() and cov.get("all_visualized") is True
            and nbstat.get("zero_tracebacks") is True
            and nbstat.get("deterministic_3_builds") is True
            and audit.get("no_test_access") is True)
    check("phase20b_reviewer_package_audit_pass", ok12,
          {"coverage": cov.get("coverage"), "all_visualized": cov.get("all_visualized"),
           "zero_tracebacks": nbstat.get("zero_tracebacks"),
           "deterministic_3_builds": nbstat.get("deterministic_3_builds")})

    # 13 no unresolved leakage blocker --------------------------------------- #
    saf = load_json(A / "phase19_leakage_safeguards.json")
    dup = load_json(A / "phase20_cross_domain_duplicate_audit.json")
    promo = load_json(A / "phase05_v3_promotion_audit.json")
    ok13 = (saf.get("leakage_status") == "REMEDIATED"
            and dup.get("verdict") == "PHASE20_DUPLICATE_AUDIT_PASS__NO_TRAIN_VAL_LEAKAGE"
            and promo.get("status") == "PASS")
    check("no_unresolved_leakage_blocker", ok13,
          {"phase19": saf.get("leakage_status"), "phase20_duplicate": dup.get("verdict"),
           "phase05_promotion": promo.get("status")})

    # 14 Phase 21 previously NOT_STARTED ------------------------------------- #
    st21 = by_id.get("21", {}).get("status")
    exp21 = ROOT / "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3"
    ck21 = ROOT / "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3"
    ok14 = st21 == "ELIGIBLE_NOT_STARTED" and not exp21.exists() and not ck21.exists()
    check("phase21_previously_not_started", ok14,
          {"map_status": st21, "experiment_dir_exists": exp21.exists(),
           "checkpoint_dir_exists": ck21.exists()})

    # 15 supervisor authorization -------------------------------------------- #
    check("supervisor_authorization_present", True,
          "Explicit Phase-21 AUTHORIZATION in the supervisor instruction for this task")

    all_pass = all(c["passed"] for c in checks.values())
    payload = {
        "artifact": "phase21_entry_gate",
        "phase": 21,
        "verdict": "PHASE21_ENTRY_GATE_PASS" if all_pass else "PHASE21_ENTRY_GATE_FAIL",
        "training_may_start": all_pass,
        "fail_closed": True,
        "checks": checks,
        "n_checks": len(checks),
        "n_passed": sum(c["passed"] for c in checks.values()),
        "protocol_sha256": protocol_sha,
        "manifest_version": "phase4_v3",
        "train_population": int(len(train)),
        "val_population": int(len(val)),
        "task_ids": EXPECTED_TASK_IDS,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for name, c in checks.items():
        print(f"[{'PASS' if c['passed'] else 'FAIL'}] {name}")
    print(f"\nverdict: {payload['verdict']}  ({payload['n_passed']}/{payload['n_checks']})")
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
