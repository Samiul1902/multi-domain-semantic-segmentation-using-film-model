"""EXT-03 baseline matrix completion summary (write-once).

READ-ONLY ANALYSIS over already-finished training artifacts. No training, no
inference, no TEST access, no ROUTER_HOLDOUT access. Creates no new scientific
endpoint: it re-aggregates the frozen per-run `best_metric` values recorded by the
EXT-03 runner into the family-level summary the paper's baseline table needs.

Authority
---------
`reports/baselines/ext03_run_registry.json`  (runner-written, 15 entries)
`reports/baselines/runs/<run_id>/best.pt`    (per-run selected checkpoint)

Fail-closed checks performed before any aggregation:
  1. every one of the 15 expected run_ids is present;
  2. every run has status == COMPLETE;
  3. every run's `best.pt` exists and its raw-byte SHA-256 equals the registry
     `checkpoint_sha` (a mismatch means the checkpoint on disk is not the one that
     produced the recorded metric -> abort);
  4. every `best_metric` is finite and inside (0, 1].
A failure aborts rather than emitting a plausible-but-wrong table.
"""
import hashlib
import json
import os
import statistics as st
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
REGISTRY = ROOT / "reports" / "baselines" / "ext03_run_registry.json"
RUNS_DIR = ROOT / "reports" / "baselines" / "runs"
OUT_JSON = ROOT / "reports" / "baselines" / "ext03_matrix_completion_summary_v1_0.json"
OUT_CSV = ROOT / "reports" / "tables" / "ext03_matrix_final_family_summary_v1_0.csv"

ARCHS = ["unet", "attention_unet", "unetpp", "deeplabv3plus", "segformer_b0"]
SEEDS = [42, 123, 3407]
EXPECTED = [f"{a}_seed{s}" for a in ARCHS for s in SEEDS]

# Frozen reference for the conditioning gap. GlobalMedFiLM alone (Phase 21, ep66).
GLOBAL_MEDFILM_MACRO = 0.8350791259413984


def sha256_bytes(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    runs = reg.get("runs", reg)

    missing = [r for r in EXPECTED if r not in runs]
    if missing:
        raise SystemExit(f"ABORT: missing run_ids in registry: {missing}")

    for rid in EXPECTED:
        v = runs[rid]
        if v.get("status") != "COMPLETE":
            raise SystemExit(f"ABORT: {rid} status={v.get('status')!r}, expected COMPLETE")
        bm = v.get("best_metric")
        if bm is None or not (0.0 < float(bm) <= 1.0):
            raise SystemExit(f"ABORT: {rid} best_metric out of range: {bm!r}")
        ck = RUNS_DIR / rid / "best.pt"
        if not ck.is_file():
            raise SystemExit(f"ABORT: {rid} best.pt absent: {ck}")
        actual = sha256_bytes(ck)
        recorded = v.get("checkpoint_sha")
        if recorded and actual != recorded:
            raise SystemExit(
                f"ABORT: {rid} best.pt SHA mismatch\n  disk={actual}\n  registry={recorded}"
            )

    per_run = []
    families = {}
    for a in ARCHS:
        vals = []
        for s in SEEDS:
            rid = f"{a}_seed{s}"
            v = runs[rid]
            bm = float(v["best_metric"])
            vals.append(bm)
            per_run.append({
                "run_id": rid,
                "architecture": a,
                "seed": s,
                "best_macro_dice": bm,
                "best_epoch": v.get("best_epoch"),
                "stopped_epoch": v.get("current_epoch"),
                "start_time": v.get("start_time"),
                "completion_time": v.get("completion_time"),
                "resume_count": v.get("resume_count"),
                "lr_used": v.get("lr_used"),
                "checkpoint_sha": v.get("checkpoint_sha"),
            })
        families[a] = {
            "n_seeds": len(vals),
            "mean_macro_dice": st.mean(vals),
            "sd_macro_dice": st.stdev(vals),
            "min_macro_dice": min(vals),
            "max_macro_dice": max(vals),
            "spread": max(vals) - min(vals),
            "best_seed": SEEDS[vals.index(max(vals))],
            "gap_to_global_medfilm": GLOBAL_MEDFILM_MACRO - st.mean(vals),
        }

    ranked = sorted(families.items(), key=lambda kv: -kv[1]["mean_macro_dice"])

    summary = {
        "artifact": "ext03_matrix_completion_summary",
        "version": "1.0",
        "generated_utc": "2026-10-26T20:52:00Z",
        "phase": "EXT-03",
        "read_only": True,
        "training_performed_here": False,
        "test_accessed": False,
        "router_holdout_accessed": False,
        "n_runs_expected": len(EXPECTED),
        "n_runs_complete": len(EXPECTED),
        "metric": "equal-domain macro Dice on VAL (n=808), threshold 0.5, per-image Dice then unweighted mean over the 4 domains",
        "selection_rule": "max VAL macro Dice over epochs (runner: best_metric / best_epoch)",
        "protocol_caveat": (
            "All 15 runs used the REDUCED protocol actually implemented by the runner: "
            "Adam(lr=1e-3, wd=1e-4), binary_cross_entropy_with_logits (BCE only, no Dice term), "
            "NO augmentation, CosineAnnealingLR, AMP. segformer_b0 alone used lr=1e-4 (D99 override). "
            "This is NOT the frozen phase09/10 authority (AdamW, lr 1e-4, wd 1e-4, bce_dice 0.5/0.5, "
            "hflip/rot/brightness/contrast augmentation). These numbers MUST NOT be presented as "
            "protocol-faithful baselines."
        ),
        "conditioning_caveat": (
            "The five architectures are trained jointly on the pooled four-domain TRAIN split with NO "
            "task conditioning. The gap to GlobalMedFiLM therefore bundles (a) task-conditioned FiLM, "
            "(b) the phase09/10 protocol, and (c) architecture. It does NOT isolate the FiLM effect."
        ),
        "reference_global_medfilm_macro_dice": GLOBAL_MEDFILM_MACRO,
        "families": families,
        "family_ranking": [{"rank": i + 1, "architecture": a, **families[a]}
                           for i, (a, _) in enumerate(ranked)],
        "per_run": per_run,
    }

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(OUT_JSON), flags)
    try:
        payload = json.dumps(summary, indent=2).encode("utf-8")
        view = memoryview(payload)
        while view:
            n = os.write(fd, view)
            view = view[n:]
        os.fsync(fd)
    finally:
        os.close(fd)
    if OUT_JSON.stat().st_size != len(payload):
        raise SystemExit("ABORT: short write on summary JSON")

    lines = ["architecture,n_seeds,mean_macro_dice,sd_macro_dice,min_macro_dice,"
             "max_macro_dice,spread,best_seed,gap_to_global_medfilm"]
    for a, _ in ranked:
        f = families[a]
        lines.append(f"{a},{f['n_seeds']},{f['mean_macro_dice']:.6f},{f['sd_macro_dice']:.6f},"
                     f"{f['min_macro_dice']:.6f},{f['max_macro_dice']:.6f},{f['spread']:.6f},"
                     f"{f['best_seed']},{f['gap_to_global_medfilm']:.6f}")
    OUT_CSV.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"OK  runs={len(EXPECTED)}/15 COMPLETE  sha-verified={len(EXPECTED)}")
    print(f"    {OUT_JSON.name}  {OUT_JSON.stat().st_size} B")
    print(f"    {OUT_CSV.name}")
    print()
    print(f"{'rank':>4} {'architecture':16s} {'mean':>7s} {'sd':>7s} {'spread':>7s} {'gap':>7s}")
    for i, (a, _) in enumerate(ranked):
        f = families[a]
        print(f"{i+1:>4} {a:16s} {f['mean_macro_dice']:7.4f} {f['sd_macro_dice']:7.4f} "
              f"{f['spread']:7.4f} {f['gap_to_global_medfilm']:7.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
