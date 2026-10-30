#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 29 — PHASE C STAGE 2a-run: sequential R_psi chain for both new seeds.

Runs, in order, for each master seed in [123, 3407]:
    fold0, fold1, fold2, final-refit
each as ONE logical run through the frozen additive wrapper.

Designed to be re-entrant: a run whose ``run.json`` exists with a stop_reason is
skipped (the canonical trainer is idempotent on --resume). Safe to relaunch
after a harness teardown.

Usage:
    python phase29_phase_c_run_rpsi.py --master-seed 123
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase29_phase_c_common as C  # noqa: E402
import phase29_train_rpsi as R  # noqa: E402


def run_one(master_seed: int, role: str) -> dict:
    spec = R.build_run_spec(master_seed, role)
    run_json = Path(spec["run_experiment_dir"]) / "run.json"
    if run_json.exists():
        prev = C.read_json(run_json)
        if prev.get("stop_reason"):
            print(f"  [{role}] already complete "
                  f"(epochs={prev.get('epochs_completed')}, "
                  f"best={prev.get('best_epoch')}) -> skip")
            return {"role": role, "skipped": True, "run": prev}
    print(f"  [{role}] training seed={spec['training_seed']} ...", flush=True)
    out = R.launch(master_seed, role, resume=True)
    rec = C.read_json(run_json)
    print(f"  [{role}] rc={out.get('return_code')} "
          f"epochs={rec.get('epochs_completed')} best_epoch={rec.get('best_epoch')} "
          f"stop={rec.get('stop_reason')}")
    return {"role": role, "skipped": False, "run": rec}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master-seed", type=int, required=True, choices=[123, 3407])
    args = ap.parse_args()
    S = int(args.master_seed)

    print(f"=== R_psi chain seed{S}: fold0 fold1 fold2 final ===")
    results = []
    for role in ("fold0", "fold1", "fold2"):
        results.append(run_one(S, role))
    results.append(run_one(S, "final"))

    # ---- completeness check ---------------------------------------------- #
    # NOTE: the canonical trainer writes to <root>/<run>, i.e. the wrapper's
    # bare per-seed root. Do NOT add an "rpsi/" level here.
    root = C.rpsi_checkpoint_root(S)
    checks = {}
    for k in range(3):
        p = root / f"fold{k}" / "best.pt"
        checks[f"fold{k}_best_exists"] = p.exists()
        if p.exists():
            st = _load_seed(p)
            checks[f"fold{k}_seed_is_{S}"] = int(st.get("seed", -1)) == S
    fin = root / "final" / "final.pt"
    checks["final_exists"] = fin.exists()
    if fin.exists():
        st = _load_seed(fin)
        checks[f"final_seed_is_{S}"] = int(st.get("seed", -1)) == S
    all_pass = all(checks.values())
    C.write_json({
        "artifact": f"phase29_seed{S}_rpsi_chain",
        "phase": 29, "stage": "RPSI_CHAIN_COMPLETE",
        "method": C.METHOD, "generated_utc": C.now_utc(),
        "master_seed": S, "runs": results, "checks": checks,
        "all_pass": all_pass,
    }, C.AUD / f"phase29_seed{S}_rpsi_chain.json")
    print(f"[chain seed{S}] all_pass={all_pass} {checks}")
    return 0 if all_pass else 2


def _load_seed(p):
    import torch
    return torch.load(p, map_location="cpu", weights_only=False)


if __name__ == "__main__":
    raise SystemExit(main())
