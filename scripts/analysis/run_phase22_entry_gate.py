"""Phase 22 — entry gate (FAIL CLOSED).

Verifies every precondition required before ANY Phase-22 diagnostic inference may run.
Reads persisted artifacts only. Never trains, never evaluates, never touches TEST.

If any check fails the script writes reports/audits/phase22_entry_gate.json with
verdict PHASE22_ENTRY_GATE_FAIL and exits non-zero. It never repairs frozen Phase-21
science.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase22_entry_gate.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
OUT = AUD / "phase22_entry_gate.json"

PHASE21_EXP = "phase21_global_medfilm_fourdomain_seed42_clean_v3"
EXPECTED_TERMINAL = "PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED"
EXPECTED_PROTOCOL_SHA = "b74f1f9f429adbce374f0306180943b9f373f872e1e69e115b7d17e81414283c"

FREEZE = AUD / "phase21_final_freeze.json"
VAL = AUD / "phase21_val_evaluation.json"
PROTOCOL = AUD / "phase20_shared_global_baseline_protocol.json"
ARCH_BINDING = AUD / "phase21_global_medfilm_architecture_binding.json"
PER_IMAGE = TAB / "phase21_per_image_val_metrics.csv"
PRED_MANIFEST = TAB / "phase21_prediction_manifest.csv"
CHECKPOINT = ROOT / "checkpoints" / PHASE21_EXP / "best.pt"
PRED_DIR = ROOT / "reports" / "predictions" / PHASE21_EXP / "val"


def sha256(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    freeze = load(FREEZE)
    val = load(VAL)
    gov = freeze.get("governance", {})
    fb = freeze.get("frozen_bindings", {})
    locks = gov.get("test_locks", {})

    ckpt_sha = sha256(CHECKPOINT)
    proto_sha = sha256(PROTOCOL)
    arch_sha = sha256(ARCH_BINDING)

    # ---- persisted prediction inventory (per-domain npz count) ----
    pred_counts = {}
    if PRED_DIR.exists():
        for d in sorted(p.name for p in PRED_DIR.iterdir() if p.is_dir()):
            pred_counts[d] = len([f for f in (PRED_DIR / d).iterdir() if f.suffix == ".npz"])
    pred_total = sum(pred_counts.values())

    checks: list[dict] = []

    def chk(name: str, ok: bool, expected, observed, note: str = "") -> None:
        checks.append({
            "check": name,
            "pass": bool(ok),
            "expected": expected,
            "observed": observed,
            "note": note,
        })

    chk("phase21_final_freeze_exists", FREEZE.exists(), True, FREEZE.exists())
    chk("phase21_freeze_verified", freeze.get("freeze_verified") is True, True,
        freeze.get("freeze_verified"))
    chk("phase21_validation_problems_empty",
        freeze.get("validation_problems") == [], [],
        freeze.get("validation_problems"))
    chk("phase21_terminal_state", freeze.get("terminal_state") == EXPECTED_TERMINAL,
        EXPECTED_TERMINAL, freeze.get("terminal_state"))
    chk("phase22_eligible", freeze.get("phase22_eligible") is True, True,
        freeze.get("phase22_eligible"))
    chk("phase22_started_before_authorization", freeze.get("phase22_started") is False, False,
        freeze.get("phase22_started"),
        "must be false BEFORE this authorization; Phase-22 artifacts must not pre-exist")

    # No Phase-22 artifacts may exist yet (guards against a silent re-run).
    # Exclude this gate's own output: it is written by this script and is not
    # evidence that Phase-22 execution has begun.
    pre_existing = sorted(p.name for p in AUD.glob("phase22_*")
                          if p.name != OUT.name)
    chk("no_preexisting_phase22_audits", len(pre_existing) == 0, [], pre_existing)

    chk("phase21_checkpoint_sha_matches_freeze",
        ckpt_sha == freeze.get("training", {}).get("best_checkpoint_sha256"),
        freeze.get("training", {}).get("best_checkpoint_sha256"), ckpt_sha,
        "bound via phase21_final_freeze.json :: training.best_checkpoint_sha256")
    chk("phase21_canonical_val_inference_runs_1",
        val.get("canonical_val_inference_runs") == 1, 1,
        val.get("canonical_val_inference_runs"))
    chk("phase21_canonical_val_samples_808",
        val.get("samples_evaluated") == 808 and val.get("samples_expected") == 808,
        "808/808", f"{val.get('samples_evaluated')}/{val.get('samples_expected')}")
    chk("phase21_prediction_maps_808", pred_total == 808, 808, pred_total,
        f"per-domain: {pred_counts}")
    chk("phase21_per_image_metrics_table_exists", PER_IMAGE.exists(), True, PER_IMAGE.exists())
    chk("phase21_prediction_manifest_exists", PRED_MANIFEST.exists(), True,
        PRED_MANIFEST.exists())
    chk("frozen_protocol_sha_matches", proto_sha == EXPECTED_PROTOCOL_SHA,
        EXPECTED_PROTOCOL_SHA, proto_sha)
    chk("freeze_protocol_sha_matches", fb.get("protocol_sha256") == EXPECTED_PROTOCOL_SHA,
        EXPECTED_PROTOCOL_SHA, fb.get("protocol_sha256"))
    chk("architecture_binding_sha_matches",
        arch_sha == fb.get("architecture_binding_sha256"),
        fb.get("architecture_binding_sha256"), arch_sha)

    chk("train_population_5832", gov.get("train_population") == 5832, 5832,
        gov.get("train_population"))
    chk("val_population_808", gov.get("val_population") == 808, 808,
        gov.get("val_population"))
    chk("manifest_version_phase4_v3", gov.get("manifest_version") == "phase4_v3",
        "phase4_v3", gov.get("manifest_version"))

    chk("test_locked_all_zero",
        all(locks.get(k) == 0 for k in ("test_image_reads", "test_mask_reads",
                                        "test_inference", "test_visualization")),
        "all 0", locks)
    chk("test_reads_total_zero", gov.get("test_reads_total_observed") == 0, 0,
        gov.get("test_reads_total_observed"))
    chk("test_lock_clean", gov.get("test_lock_clean") is True, True,
        gov.get("test_lock_clean"))

    failed = [c for c in checks if not c["pass"]]
    verdict = "PHASE22_ENTRY_GATE_PASS" if not failed else "PHASE22_ENTRY_GATE_FAIL"

    payload = {
        "artifact": "phase22_entry_gate",
        "phase": 22,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "supervisor_authorization": (
            "Phase 22 explicitly AUTHORIZED by the current instruction; predecessor terminal "
            "state PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED."
        ),
        "verdict": verdict,
        "n_checks": len(checks),
        "n_passed": len(checks) - len(failed),
        "n_failed": len(failed),
        "checks": checks,
        "bindings": {
            "phase21_experiment_id": PHASE21_EXP,
            "phase21_checkpoint_sha256": ckpt_sha,
            "phase21_protocol_sha256": proto_sha,
            "phase21_architecture_binding_sha256": arch_sha,
            "phase21_reference_macro_dice": freeze.get("results", {}).get("macro_domain_dice"),
            "persisted_prediction_dir": f"reports/predictions/{PHASE21_EXP}/val",
            "persisted_prediction_counts": pred_counts,
        },
        "state_transition": {
            "phase21": "COMPLETE_FROZEN",
            "phase22": "AUTHORIZED_IN_PROGRESS" if not failed else "BLOCKED",
            "phase23": "NOT_STARTED",
        },
        "hard_boundaries": [
            "no model training", "no fine-tuning", "no architecture modification",
            "no benefit-predictor training", "no localizer/refiner/router training",
            "no pruning/quantization/distillation/NAS", "no TEST access",
            "no external-dataset evaluation", "no Phase-23 literature search",
            "Phase-21 canonical VAL pass must NOT be rerun or replaced",
        ],
        "test_reads": {"test_image_reads": 0, "test_mask_reads": 0,
                       "test_inference": 0, "test_visualization": 0},
    }

    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"WROTE {OUT}")
    print(f"VERDICT: {verdict}  ({len(checks) - len(failed)}/{len(checks)} passed)")
    if failed:
        print("\nBLOCKERS:")
        for c in failed:
            print(f"  - {c['check']}: expected {c['expected']!r}, observed {c['observed']!r}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
