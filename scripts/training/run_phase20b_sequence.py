"""Phase 20B - sequential driver for the four remaining conventional baselines.

Phase 20A (UNet++) is already trained and closed. Phase 20B must train the other
four conventional architectures under the IDENTICAL frozen Phase-20 protocol, and
it must do so **sequentially** - one GPU job at a time - so the five models are
trained under the same effective conditions and never contend for VRAM.

This driver enforces that:

  1. It walks the frozen order: unet -> attention_unet -> deeplabv3plus ->
     transformer_mit_unet.
  2. Before starting a model it waits until NO other Phase-20B run holds an active
     experiment lock. A model already running elsewhere is therefore never
     duplicated.
  3. A model whose ``closure.json`` shows natural termination
     (``EARLY_STOPPING_PATIENCE`` or ``MAX_EPOCHS``) is SKIPPED - it is complete.
  4. A model with an existing ``latest.pt`` is resumed (``--resume``), which
     continues the SAME logical run. It never starts a second independent run.
  5. If the trainer is killed by the execution harness, the driver retries with
     ``--resume`` (bounded), so the run continues rather than restarting.
  6. Exit code 2 from the trainer is the FAIL-CLOSED governance signal (binding
     SHA drift, failed pre-execution check, changed protocol). That is NOT
     retried: the driver stops and reports loudly, because papering over a
     governance failure would invalidate the benchmark.

Each model keeps exactly ONE logical run, seed 42, natural termination only. The
driver never stops a weak model early and never tunes a per-model threshold.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.utils.run_lock import inspect_lock  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts" / "training"))
from train_phase20b_shared_baseline import MODEL_REGISTRY, ORDER  # noqa: E402

NATURAL_STOP_REASONS = {"EARLY_STOPPING_PATIENCE", "MAX_EPOCHS"}
LOG_PATH = ROOT / "logs" / "phase20b_sequence.log"


def log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] {msg}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def exp_dir(model_key: str) -> Path:
    return ROOT / "experiments" / MODEL_REGISTRY[model_key]["experiment_id"]


def ckpt_dir(model_key: str) -> Path:
    return ROOT / "checkpoints" / MODEL_REGISTRY[model_key]["experiment_id"]


def is_complete(model_key: str) -> bool:
    closure = exp_dir(model_key) / "closure.json"
    if not closure.exists():
        return False
    try:
        data = json.loads(closure.read_text(encoding="utf-8"))
    except Exception:
        return False
    return data.get("stop_reason") in NATURAL_STOP_REASONS


def active_runs() -> list:
    """All Phase-20B experiments currently holding an ACTIVE run lock.

    The driver holds no lock itself, so every active lock - including one for the
    model it is about to start - means another process is already training and we
    must wait. This is what makes the sequence strictly serial.
    """
    out = []
    for key in ORDER:
        status = inspect_lock(exp_dir(key))
        if status.get("active"):
            out.append((key, status.get("reason")))
    return out


def wait_for_gpu_free(poll_seconds: int = 60) -> None:
    announced = False
    while True:
        busy = active_runs()
        if not busy:
            return
        if not announced:
            log(f"  waiting: another Phase-20B run is active -> {busy}")
            announced = True
        time.sleep(poll_seconds)


def run_model(model_key: str, max_attempts: int) -> bool:
    spec = MODEL_REGISTRY[model_key]
    display = spec["display_name"]
    exp = exp_dir(model_key)
    ckpt = ckpt_dir(model_key)

    if is_complete(model_key):
        closure = json.loads((exp / "closure.json").read_text(encoding="utf-8"))
        log(f"SKIP {display}: already complete "
            f"(best_epoch={closure.get('best_epoch')} "
            f"best_macro={closure.get('best_macro_domain_dice')} "
            f"stop={closure.get('stop_reason')})")
        return True

    wait_for_gpu_free()

    # The run we were waiting on may have just completed this very model.
    if is_complete(model_key):
        log(f"SKIP {display}: completed while waiting")
        return True

    trainer = ROOT / "scripts" / "training" / "train_phase20b_shared_baseline.py"
    for attempt in range(1, max_attempts + 1):
        resume = (ckpt / "latest.pt").exists()
        cmd = [sys.executable, str(trainer), "--model-key", model_key]
        if resume:
            cmd.append("--resume")
        log(f"START {display} attempt={attempt}/{max_attempts} resume={resume} "
            f"experiment={spec['experiment_id']}")
        t0 = time.time()
        rc = subprocess.call(cmd, cwd=str(ROOT))
        dt = time.time() - t0

        if rc == 0 and is_complete(model_key):
            closure = json.loads((exp / "closure.json").read_text(encoding="utf-8"))
            log(f"DONE {display} in {dt/3600:.2f}h "
                f"best_epoch={closure.get('best_epoch')} "
                f"best_macro={closure.get('best_macro_domain_dice')} "
                f"final_epoch={closure.get('final_epoch')} "
                f"stop={closure.get('stop_reason')} "
                f"resume_count={closure.get('resume_count')}")
            return True

        if rc == 2:
            log(f"ABORT {display}: FAIL-CLOSED governance signal (rc=2). "
                f"Not retrying; this needs human review.")
            return False

        log(f"  {display} attempt {attempt} ended rc={rc} after {dt/60:.1f} min; "
            f"will resume the SAME logical run")
        time.sleep(30)

    log(f"FAILED {display}: exhausted {max_attempts} attempts")
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase-20B sequential baseline driver.")
    ap.add_argument("--models", nargs="*", default=ORDER, choices=ORDER,
                    help="Subset/order of models to drive (default: all four).")
    ap.add_argument("--max-attempts", type=int, default=30,
                    help="Bounded resume attempts per model before giving up.")
    args = ap.parse_args()

    log("=" * 78)
    log(f"PHASE 20B SEQUENCE START models={args.models}")

    ok = True
    for key in args.models:
        if not run_model(key, args.max_attempts):
            ok = False
            break

    if ok:
        log("PHASE 20B SEQUENCE COMPLETE: all requested models naturally terminated")
    else:
        log("PHASE 20B SEQUENCE STOPPED EARLY")
    log("=" * 78)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
