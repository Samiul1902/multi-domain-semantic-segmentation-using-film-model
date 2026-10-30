"""Phase 21 — post-training pipeline orchestrator.

Runs the whole Phase-21 chain in the required order, fail-closed:

  1. canonical VAL evaluation (exactly ONE pass over 808 VAL samples)
  2. analysis (metrics, bootstrap, paired comparison, KUB strata, gallery)
  3. conditioning diagnostic + FiLM parameter sanity
  4. efficiency / compute accounting
  5. figures + inventories
  6. notebook build x3 -> byte-identical determinism proof
  7. final freeze
  8. additive governance sync

Never trains. Never touches TEST.

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/run_phase21_post_training_pipeline.py
    ./.venv/Scripts/python.exe scripts/analysis/run_phase21_post_training_pipeline.py --skip-eval
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
AUD = ROOT / "reports" / "audits"
NB_PATH = ROOT / "notebooks/phasewise/phase_21_global_medfilm/phase21_global_medfilm_reference.ipynb"
EXP = "phase21_global_medfilm_fourdomain_seed42_clean_v3"


def run(step: str, args: list[str]) -> None:
    print(f"\n=== [{step}] {' '.join(args)} ===", flush=True)
    t0 = time.time()
    r = subprocess.run([PY, *args], cwd=str(ROOT))
    print(f"=== [{step}] rc={r.returncode} ({time.time()-t0:.0f}s) ===", flush=True)
    if r.returncode != 0:
        raise SystemExit(f"FAIL-CLOSED: step '{step}' exited {r.returncode}")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-eval", action="store_true")
    ap.add_argument("--skip-notebook", action="store_true")
    args = ap.parse_args()

    closure = json.loads((ROOT / "experiments" / EXP / "phase21_training_closure.json")
                         .read_text(encoding="utf-8"))
    if closure.get("stop_reason") not in ("EARLY_STOPPING_PATIENCE", "MAX_EPOCHS"):
        raise SystemExit(f"FAIL-CLOSED: training not naturally terminated "
                         f"({closure.get('stop_reason')})")
    print(f"training closure OK: best_epoch={closure['best_epoch']} "
          f"macro={closure['best_macro_domain_dice']:.6f} stop={closure['stop_reason']}")

    if not args.skip_eval:
        run("canonical_val_eval", ["scripts/evaluation/evaluate_phase21_val.py"])
    run("analysis", ["scripts/analysis/run_phase21_analysis.py"])
    run("conditioning", ["scripts/analysis/phase21_conditioning_diagnostic.py"])
    run("mac_count_medfilm", ["scripts/analysis/phase21_mac_count.py", "--device", "cpu"])
    run("mac_count_six_models",
        ["scripts/analysis/phase21_mac_count.py", "--all-models", "--device", "cpu"])
    run("efficiency", ["scripts/analysis/phase21_efficiency.py"])

    print("\n=== [figures] building ===", flush=True)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from src.analysis import phase21_figures as F
    F.build_all(progress=print)
    inv = F.write_inventories()
    print("figures:", inv)

    # The reviewer notebook consumes phase21_final_freeze.json (it asserts the
    # terminal state), while the freeze requires the 3-build notebook determinism
    # proof. Resolve the cycle with a two-pass freeze:
    #   pass 1 - freeze runs and writes real content; it is EXPECTED to fail closed
    #            on the not-yet-proven determinism gate, but the artifact it writes
    #            already carries the real terminal state the notebook asserts.
    #   proof  - build the notebook 3x and prove byte-identity against the freeze.
    #   pass 2 - freeze re-runs against the completed proof and MUST verify clean.
    bootstrap_sha = None
    print("\n=== [freeze pass 1/2 - provisional] ===", flush=True)
    r = subprocess.run([PY, "scripts/analysis/write_phase21_freeze.py"], cwd=str(ROOT))
    if not (AUD / "phase21_final_freeze.json").exists():
        raise SystemExit("FAIL-CLOSED: freeze pass 1 did not write phase21_final_freeze.json")
    if not args.skip_notebook:
        det0 = {
            "artifact": "phase21_notebook_determinism",
            "phase": 21,
            "notebook_path": str(NB_PATH.relative_to(ROOT)).replace("\\", "/"),
            "builds": 0,
            "sha256_per_build": [],
            "three_builds_byte_identical": None,
            "status": "PENDING_FINAL_THREE_BUILD_PROOF",
            "test_reads": 0,
        }
        (AUD / "phase21_notebook_determinism.json").write_text(
            json.dumps(det0, indent=2), encoding="utf-8")
        print(f"freeze pass 1 rc={r.returncode} (determinism gate pending, expected)")

    if not args.skip_notebook:
        shas = []
        for i in (1, 2, 3):
            print(f"\n=== [notebook build {i}/3] ===", flush=True)
            r = subprocess.run([PY, "scripts/notebooks/build_phase21_notebook.py"], cwd=str(ROOT))
            if r.returncode != 0:
                raise SystemExit(f"FAIL-CLOSED: notebook build {i} exited {r.returncode}")
            shas.append(sha(NB_PATH))
            print(f"build {i} sha256 = {shas[-1]}")

        identical = len(set(shas)) == 1
        if args.skip_notebook:
            identical = None
        det = {
            "artifact": "phase21_notebook_determinism",
            "phase": 21,
            "notebook_path": str(NB_PATH.relative_to(ROOT)).replace("\\", "/"),
            "builds": 3,
            "sha256_per_build": shas,
            "three_builds_byte_identical": identical,
            "deterministic_practices": [
                "deterministic cell ids (p21000..p21NNN)",
                "stripped metadata.execution",
                "coalesced stream outputs",
                "fixed pandas Styler uuids via set_uuid",
                "normalised object memory addresses (0x... -> 0xADDR)",
                "stable output ordering",
            ],
            "test_reads": 0,
        }
        (AUD / "phase21_notebook_determinism.json").write_text(
            json.dumps(det, indent=2), encoding="utf-8")
        if not identical:
            raise SystemExit("FAIL-CLOSED: notebook builds are NOT byte-identical")
        print("3-build determinism: PASS")


    print("\n=== [freeze pass 2/2 - verified] ===", flush=True)
    run("freeze", ["scripts/analysis/write_phase21_freeze.py"])

    run("governance_sync", ["scripts/analysis/sync_phase21_governance.py"])

    print("\n=== PHASE 21 POST-TRAINING PIPELINE COMPLETE ===")
    print("generated_utc:", datetime.now(timezone.utc).isoformat())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
