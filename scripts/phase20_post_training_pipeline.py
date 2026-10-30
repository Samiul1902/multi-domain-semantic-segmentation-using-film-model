"""Phase-20 POST-TRAINING pipeline runner (execution mechanism only).

Runs, in order and stopping on the first failure:

  1. checkpoint closure + disk-only selection replay   (must be REPLAY_PASS)
  2. canonical VAL evaluation, ONE pass over 808 samples, persisting predictions
  3. analysis driver (tables, figures, 64-case gallery, Phase-21 entry criteria)
  4. notebook build + execute, TWICE, to prove SHA determinism

Nothing here changes science: it only invokes the already-frozen, already-validated
scripts in the required order. Safe to re-run: every step is idempotent and reads
only persisted artifacts (step 2 is the single canonical inference pass and should
be run once; re-running it reproduces byte-identical predictions because VAL access
is deterministic).

Usage
-----
    ./.venv/Scripts/python.exe scripts/phase20_post_training_pipeline.py
    ./.venv/Scripts/python.exe scripts/phase20_post_training_pipeline.py --skip-notebook
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")
AUDIT_DIR = ROOT / "reports" / "audits"
NB_PATH = (ROOT / "notebooks/phasewise/phase_20_multidomain_baselines"
           / "phase20_shared_global_unetpp_baseline.ipynb")


def run(step: str, argv: list[str]) -> tuple[bool, float]:
    print("=" * 78)
    print(f"[{step}] {' '.join(argv)}")
    print("=" * 78, flush=True)
    t0 = time.time()
    proc = subprocess.run(argv, cwd=str(ROOT))
    dt = time.time() - t0
    ok = proc.returncode == 0
    print(f"\n[{step}] {'OK' if ok else 'FAILED'} (exit {proc.returncode}) in {dt:.1f}s\n", flush=True)
    return ok, dt


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-notebook", action="store_true")
    ap.add_argument("--skip-closure", action="store_true",
                    help="closure/replay artifacts already exist and are canonical; do not re-run.")
    ap.add_argument("--skip-eval", action="store_true",
                    help="canonical VAL evaluation already ran; NEVER run a second inference pass.")
    args = ap.parse_args()

    timings: dict[str, float] = {}
    results: list[tuple[str, bool]] = []

    # 0. preconditions -----------------------------------------------------
    if not (ROOT / "experiments/phase20_shared_unetpp_fourdomain_seed42_clean_v3"
            / "closure.json").exists():
        print("ABORT: trainer closure.json not found — training has not terminated yet.")
        print("       Let the run finish (relaunch with --resume after any teardown).")
        return 3
    print("closure.json present — training has terminated.\n")

    # 1. closure + replay --------------------------------------------------
    if args.skip_closure:
        print("[1/5 closure+replay] SKIPPED (--skip-closure); using existing artifacts.\n")
        verdict = read_json(AUDIT_DIR / "phase20_checkpoint_selection_replay.json")["verdict"]
        if verdict != "PHASE20_CHECKPOINT_SELECTION_REPLAY_PASS":
            print(f"STOP: existing replay verdict = {verdict}")
            return 2
    else:
        ok, dt = run("1/5 closure+replay", [PY, "scripts/audits/phase20_training_closure_and_replay.py"])
        timings["closure_replay"] = dt
        results.append(("closure+replay", ok))
        if not ok:
            print("STOP: checkpoint-selection replay did not pass; not proceeding.")
            return 2
        verdict = read_json(AUDIT_DIR / "phase20_checkpoint_selection_replay.json")["verdict"]
        if verdict != "PHASE20_CHECKPOINT_SELECTION_REPLAY_PASS":
            print(f"STOP: replay verdict = {verdict}")
            return 2

    # 2. canonical VAL evaluation (ONE pass, 808 samples) ------------------
    if args.skip_eval:
        print("[2/5 val evaluation] SKIPPED (--skip-eval); the single canonical pass already ran.\n")
        ev = read_json(AUDIT_DIR / "phase20_val_evaluation.json")
        if int(ev["samples_evaluated"]) != 808:
            print(f"STOP: existing evaluation covered {ev['samples_evaluated']} samples, expected 808.")
            return 2
    else:
        ok, dt = run("2/5 val evaluation", [PY, "scripts/evaluation/evaluate_phase20_val.py"])
        timings["val_evaluation"] = dt
        results.append(("val evaluation", ok))
        if not ok:
            print("STOP: canonical VAL evaluation failed.")
            return 2
        ev = read_json(AUDIT_DIR / "phase20_val_evaluation.json")
        if int(ev["samples_evaluated"]) != 808:
            print(f"STOP: evaluated {ev['samples_evaluated']} samples, expected 808.")
            return 2
        if any(int(v) != 0 for v in ev["test_reads"].values()):
            print(f"STOP: non-zero TEST reads {ev['test_reads']}")
            return 2

    # 3. analysis (pass A) -------------------------------------------------
    # NOTE: there is a genuine ordering dependency. The Phase-21 criterion P21-7
    # ("complete notebook executed") is a file-existence check, but the notebook
    # itself consumes the analysis outputs. So the pipeline runs the analysis
    # once to produce its tables, builds the notebook (which satisfies P21-7),
    # then re-runs the analysis so the persisted criteria reflect the notebook
    # that now exists, and finally rebuilds the notebook so its embedded criteria
    # table shows the final state.
    ok, dt = run("3/5 analysis (pass A)", [PY, "scripts/analysis/run_phase20_analysis.py"])
    timings["analysis_pass_a"] = dt
    results.append(("analysis (pass A)", ok))
    if not ok:
        print("STOP: analysis driver failed.")
        return 2

    if args.skip_notebook:
        print("(--skip-notebook) stopping after analysis pass A.")
        _summarize(results, timings)
        return 0

    import hashlib

    # 4. notebook #1 — exists so P21-7 can pass ----------------------------
    ok, dt = run("4/5 notebook build #1", [PY, "scripts/notebooks/build_phase20_notebook.py"])
    timings["notebook_build_1"] = dt
    results.append(("notebook build #1", ok))
    if not ok:
        print("STOP: notebook build/execute failed.")
        return 2

    # 5. analysis (pass B) — P21-7 flips to PASS --------------------------
    ok, dt = run("5/5 analysis (pass B)", [PY, "scripts/analysis/run_phase20_analysis.py"])
    timings["analysis_pass_b"] = dt
    results.append(("analysis (pass B)", ok))
    if not ok:
        print("STOP: analysis re-run failed.")
        return 2
    p21 = read_json(AUDIT_DIR / "phase20_phase21_entry_criteria.json")
    if not p21.get("all_criteria_met"):
        print("STOP: Phase-21 entry criteria not all met after pass B.")
        for c in p21["criteria"]:
            if not c["met"]:
                print(f"   FAIL {c['id']}: {c['criterion']} -> {c['observed']}")
        return 2

    # 6. notebook #2 (final) + #3 (determinism pair) ----------------------
    ok, dt = run("5/5 notebook build #2 (final)", [PY, "scripts/notebooks/build_phase20_notebook.py"])
    timings["notebook_build_2"] = dt
    results.append(("notebook build #2 (final)", ok))
    if not ok:
        print("STOP: notebook build #2 failed.")
        return 2
    sha2 = hashlib.sha256(NB_PATH.read_bytes()).hexdigest()

    ok, dt = run("5/5 notebook build #3 (determinism)", [PY, "scripts/notebooks/build_phase20_notebook.py"])
    timings["notebook_build_3"] = dt
    results.append(("notebook build #3", ok))
    if not ok:
        print("STOP: notebook build #3 failed.")
        return 2
    sha3 = hashlib.sha256(NB_PATH.read_bytes()).hexdigest()

    stable = sha2 == sha3
    results.append(("notebook SHA deterministic", stable))
    print(f"notebook SHA #2 (final) = {sha2}")
    print(f"notebook SHA #3         = {sha3}")
    print(f"notebook SHA deterministic: {'PASS' if stable else 'FAIL'}\n")
    (AUDIT_DIR / "phase20_notebook_determinism.json").write_text(json.dumps({
        "artifact": "phase20_notebook_determinism",
        "phase": 20,
        "notebook_path": str(NB_PATH.relative_to(ROOT)).replace("\\", "/"),
        "final_notebook_sha256": sha2,
        "rebuild_sha256": sha3,
        "deterministic": stable,
        "note": "notebook build #1 precedes the final analysis pass and therefore differs; "
                "determinism is proven between the two post-final-analysis builds (#2 and #3).",
        "method": "deterministic cell ids + stripped metadata.execution + coalesced stream outputs",
    }, indent=2), encoding="utf-8")

    _summarize(results, timings)
    return 0 if all(ok for _, ok in results) else 2


def _summarize(results: list[tuple[str, bool]], timings: dict[str, float]) -> None:
    print("=" * 78)
    print("PHASE-20 POST-TRAINING PIPELINE SUMMARY")
    print("=" * 78)
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    print()
    for k, v in timings.items():
        print(f"  {k:<24} {v:8.1f}s")
    print()
    print("STEP REMAINING (manual, judgment-heavy): synchronize")
    print("  reports/audits/dataset_visualization_coverage.csv")
    print("  reports/audits/trained_model_visualization_registry.csv/.json")
    print("  notebooks/phasewise README + index, PROJECT_MASTER_PLAN.md")
    print("Then produce the 71-item final report. Do NOT start Phase 21.")


if __name__ == "__main__":
    raise SystemExit(main())
