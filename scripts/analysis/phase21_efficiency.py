"""Phase 21 — parameter / compute accounting (MEASUREMENT ONLY, no optimization).

Reports parameters, checkpoint size, training wall time and per-epoch time,
GPU latency + peak memory, and an OPTIONAL CPU latency benchmark. Nothing here
optimizes, prunes, quantizes or compresses anything.

MACs/FLOPs are reported as ``null`` because no trusted FLOP-counting
infrastructure (thop / fvcore / ptflops / torchinfo) is installed in this
environment; an untrusted estimate would be worse than an explicit gap.

Writes
------
reports/tables/phase21_efficiency_accounting.csv
reports/audits/phase21_efficiency_accounting.json

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/phase21_efficiency.py
"""
from __future__ import annotations

import json
import platform
import statistics
import sys
import time
from pathlib import Path

import pandas as pd
import torch

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from scripts.training.phase21_common import (  # noqa: E402
    CKPT_DIR,
    CONFIG,
    EXPERIMENT_ID,
    EXP_DIR,
    HISTORY_PATH,
    sha256_file,
)
from src.models.film import GlobalMedFiLM  # noqa: E402
from src.utils.test_lock import verify_test_lock  # noqa: E402

TABLE_DIR = ROOT / "reports" / "tables"
AUDIT_DIR = ROOT / "reports" / "audits"
CPU_REPEATS = 5
CPU_WARMUP = 2
GPU_REPEATS = 30
GPU_WARMUP = 5


def build_model():
    return GlobalMedFiLM(
        task_count=CONFIG["model"]["task_count"],
        in_channels=CONFIG["model"]["in_channels"],
        out_channels=CONFIG["model"]["out_channels"],
        channels=tuple(CONFIG["model"]["channels"]),
        task_embedding_dim=CONFIG["model"]["task_embedding_dim"],
        film_hidden_dim=CONFIG["model"]["film_hidden_dim"],
    )


def timed(fn, warmup: int, repeats: int):
    for _ in range(warmup):
        fn()
    samples = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - t0) * 1000.0)
    return {
        "median_ms": float(statistics.median(samples)),
        "mean_ms": float(statistics.fmean(samples)),
        "p05_ms": float(sorted(samples)[max(0, int(0.05 * len(samples)) - 1)]),
        "p95_ms": float(sorted(samples)[min(len(samples) - 1, int(0.95 * len(samples)))]),
        "stdev_ms": float(statistics.pstdev(samples)),
        "repeats": int(repeats), "warmup": int(warmup),
    }


def main() -> int:
    verify_test_lock(str(ROOT))
    rows = []

    best_path = CKPT_DIR / "best.pt"
    last_path = CKPT_DIR / "last.pt"
    ck = torch.load(best_path, map_location="cpu", weights_only=False)
    model = build_model()
    model.load_state_dict(ck["model_state"])
    n_params = int(sum(p.numel() for p in model.parameters() if p.requires_grad))
    n_params_all = int(sum(p.numel() for p in model.parameters()))

    def add(name, value, unit, note=""):
        rows.append({"metric": name, "value": value, "unit": unit, "note": note})

    add("measured_parameter_count", n_params, "parameters",
        "trainable, measured from the frozen architecture")
    add("measured_parameter_count_all", n_params_all, "parameters",
        "including any non-trainable parameters")
    add("best_checkpoint_bytes", best_path.stat().st_size, "bytes", "checkpoints/<exp>/best.pt")
    if last_path.exists():
        add("last_checkpoint_bytes", last_path.stat().st_size, "bytes",
            "checkpoints/<exp>/last.pt")
    add("best_checkpoint_sha256", sha256_file(best_path), "hex", "provenance")

    # ---- training timing (from the persisted history) --------------------- #
    hist = pd.read_csv(HISTORY_PATH)
    add("epochs_completed", int(len(hist)), "epochs", "from history.csv")
    add("mean_epoch_seconds", float(hist["epoch_seconds"].mean()), "s", "all completed epochs")
    add("median_epoch_seconds", float(hist["epoch_seconds"].median()), "s", "all completed epochs")
    add("min_epoch_seconds", float(hist["epoch_seconds"].min()), "s", "")
    add("max_epoch_seconds", float(hist["epoch_seconds"].max()), "s", "")
    add("total_training_seconds", float(hist["cumulative_seconds"].iloc[-1]), "s",
        "sum of epoch time incl. validation")

    # ---- MACs / FLOPs (analytical, no third-party FLOP library) ----------- #
    # A closed-form Conv2d/Linear count is exact for those layers and is a LOWER
    # BOUND on total arithmetic. It is produced by phase21_mac_count.py.
    mac_json = ROOT / "reports" / "audits" / "phase21_analytical_mac_count.json"
    mac_info = None
    if mac_json.exists():
        mac_info = json.loads(mac_json.read_text(encoding="utf-8"))
    add("macs", (mac_info or {}).get("total_macs"), "MACs",
        "analytical Conv2d/Linear count at 1x3x512x512 (LOWER BOUND; excludes norm/activation/"
        "pool/interpolation/FiLM elementwise ops)")
    add("gmacs", (mac_info or {}).get("total_gmacs"), "G MACs", "same count, giga-MACs")
    add("gflops_2x", (mac_info or {}).get("total_gflops_convention"), "G FLOPs",
        "FLOPs = 2 x MACs convention")
    if mac_info is None:
        add("macs_unavailable_reason", "phase21_analytical_mac_count.json not found", "text",
            "run scripts/analysis/phase21_mac_count.py first")

    # ---- GPU latency + peak memory ---------------------------------------- #
    if torch.cuda.is_available():
        device = torch.device("cuda:0")
        gmodel = build_model().to(device)
        gmodel.load_state_dict(ck["model_state"])
        gmodel.eval()
        gpu_stats = {}
        for bs in (1, 8):
            x = torch.randn(bs, 3, 512, 512, device=device)
            t = torch.zeros(bs, dtype=torch.long, device=device)
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
            with torch.no_grad():
                st = timed(lambda: gmodel(x, t), GPU_WARMUP, GPU_REPEATS)
            st["peak_memory_bytes"] = int(torch.cuda.max_memory_allocated())
            st["peak_memory_reserved_bytes"] = int(torch.cuda.max_memory_reserved())
            gpu_stats[f"batch_{bs}"] = st
            add(f"gpu_latency_median_batch{bs}", st["median_ms"], "ms",
                f"forward only, warmup={GPU_WARMUP}, repeats={GPU_REPEATS}, 512x512, no AMP")
            add(f"gpu_peak_memory_batch{bs}", st["peak_memory_bytes"], "bytes",
                "torch.cuda.max_memory_allocated during the timed forward")
        add("gpu_name", torch.cuda.get_device_name(0), "text", "")
        add("gpu_total_memory_bytes",
            int(torch.cuda.get_device_properties(0).total_memory), "bytes", "")
    else:
        gpu_stats = {}
        add("gpu_latency_median_batch1", None, "ms", "no CUDA device available")

    # ---- CPU latency benchmark (optional, synthetic, NOT TEST) ------------ #
    torch.set_num_threads(torch.get_num_threads())
    cmodel = build_model()
    cmodel.load_state_dict(ck["model_state"])
    cmodel.eval()
    cpu_stats = {}
    for bs in (1, 4):
        x = torch.randn(bs, 3, 512, 512)
        t = torch.zeros(bs, dtype=torch.long)
        with torch.no_grad():
            st = timed(lambda: cmodel(x, t), CPU_WARMUP, CPU_REPEATS)
        st["batch_size"] = bs
        st["input_size"] = [512, 512]
        cpu_stats[f"batch_{bs}"] = st
        add(f"cpu_latency_median_batch{bs}", st["median_ms"], "ms",
            f"forward only on SYNTHETIC input (never TEST), warmup={CPU_WARMUP}, "
            f"repeats={CPU_REPEATS}, threads={torch.get_num_threads()}")

    add("cpu_name", platform.processor() or platform.machine(), "text", "")
    add("cpu_logical_cores", __import__("os").cpu_count(), "cores", "")
    add("cpu_torch_threads", int(torch.get_num_threads()), "threads", "")
    add("benchmark_input_source", "synthetic random tensors at 512x512", "text",
        "TEST is never read; VAL images are not required for a latency benchmark")

    df = pd.DataFrame(rows)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABLE_DIR / "phase21_efficiency_accounting.csv", index=False)

    audit = {
        "artifact": "phase21_efficiency_accounting",
        "phase": 21,
        "experiment_id": EXPERIMENT_ID,
        "purpose": "MEASUREMENT ONLY. No optimization, pruning, quantization or compression.",
        "parameter_count": n_params,
        "checkpoint_bytes": int(best_path.stat().st_size),
        "gpu": gpu_stats,
        "cpu": cpu_stats,
        "macs": (mac_info or {}).get("total_macs"),
        "gmacs": (mac_info or {}).get("total_gmacs"),
        "gflops_2x": (mac_info or {}).get("total_gflops_convention"),
        "macs_method": ("analytical closed-form Conv2d/Linear count; LOWER BOUND on total "
                        "arithmetic (excludes GroupNorm, SiLU, pooling, interpolation and the FiLM "
                        "elementwise modulation). No third-party FLOP library was used."),
        "macs_by_block": (mac_info or {}).get("by_block"),
        "six_model_compute_table": "reports/tables/phase21_six_model_compute.csv",
        "macs_reason": ("no third-party FLOP-counting library is installed "
                        "(thop/fvcore/ptflops/torchinfo all absent); the analytical count above is "
                        "used instead and is exact for conv/linear layers"),
        "cpu_benchmark": {
            "source": "SYNTHETIC random input (never TEST, never required VAL)",
            "warmup": CPU_WARMUP, "repeats": CPU_REPEATS,
            "cpu_name": platform.processor() or platform.machine(),
            "logical_cores": __import__("os").cpu_count(),
            "torch_threads": int(torch.get_num_threads()),
            "batch_sizes": [1, 4], "input_size": [512, 512],
            "dispersion": "median plus p05/p95 and population stdev are reported",
        },
        "caveat": (
            "GPU latency is a forward-only micro-benchmark without AMP and is NOT the training "
            "throughput; per-epoch training time is reported separately from history.csv. The CPU "
            "benchmark ran while no training job was active."
        ),
        "test_reads": {"test_image_reads": 0, "test_mask_reads": 0,
                       "test_inference": 0, "test_visualization": 0},
    }
    (AUDIT_DIR / "phase21_efficiency_accounting.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8")

    print(df.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
