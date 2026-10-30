"""Phase 25A — RESOURCE ACCOUNTING for BARRRegionalRefinerV1.

Measures:
    * actual trainable parameters
    * analytical Conv / Linear MACs at input 1 x 4 x 256 x 256

MACs are reported SEPARATELY from latency, memory and energy. Any host forward
latency measured here is labelled HOST-SPECIFIC and is NOT a claim of mobile
readiness, real-time capability or CPU readiness.

Writes:
    reports/audits/phase25a_resource_accounting.json
    reports/tables/phase25a_resource_accounting.csv

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase25a_resource_accounting.py
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
UTC = datetime.now(timezone.utc).isoformat()

from src.models.barr import (  # noqa: E402
    BARRRegionalRefinerV1,
    BARR_REFINER_ARCHITECTURE_ID,
    BARR_REFINER_EXPECTED_PARAMETERS,
    count_parameters,
)
from src.utils.device import get_device  # noqa: E402

MODEL_SRC = ROOT / "src" / "models" / "barr" / "regional_refiner.py"
GLOBAL_MACS_AT_512 = 31.5517        # measured in Phase 21 (G MACs @ 1x3x512x512)
GLOBAL_PARAMS = 3_523_001


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    torch.manual_seed(42)
    model = BARRRegionalRefinerV1()
    model.eval()
    n_params = count_parameters(model)

    macs: list[dict] = []
    handles = []

    def conv_hook(module: nn.Conv2d, inp, out):
        k = module.kernel_size[0] * module.kernel_size[1]
        m = k * module.in_channels * module.out_channels * out.shape[-2] * out.shape[-1]
        macs.append({"layer": module._barr_name, "type": "conv2d",
                     "kernel": list(module.kernel_size),
                     "in_channels": module.in_channels, "out_channels": module.out_channels,
                     "out_hw": [int(out.shape[-2]), int(out.shape[-1])], "macs": int(m)})

    def linear_hook(module: nn.Linear, inp, out):
        m = module.in_features * module.out_features
        macs.append({"layer": module._barr_name, "type": "linear",
                     "in_features": module.in_features, "out_features": module.out_features,
                     "macs": int(m)})

    for name, module in model.named_modules():
        module._barr_name = name
        if isinstance(module, nn.Conv2d):
            handles.append(module.register_forward_hook(conv_hook))
        elif isinstance(module, nn.Linear):
            handles.append(module.register_forward_hook(linear_hook))

    x = torch.randn(1, 4, 256, 256)
    with torch.no_grad():
        y = model(x)
    for h in handles:
        h.remove()

    total_macs = int(sum(m["macs"] for m in macs))
    total_flops = 2 * total_macs
    by_type: dict[str, int] = {}
    for m in macs:
        by_type[m["type"]] = by_type.get(m["type"], 0) + m["macs"]

    # ---- host-specific latency (explicitly NOT a deployment claim) --------- #
    latency = None
    device = None
    if torch.cuda.is_available():
        device = get_device(require_cuda=True)
        gpu_model = BARRRegionalRefinerV1().to(device).eval()
        xg = torch.randn(1, 4, 256, 256, device=device)
        with torch.no_grad():
            for _ in range(10):
                gpu_model(xg)
            if device.type == "cuda":
                torch.cuda.synchronize()
            t0 = time.perf_counter()
            for _ in range(50):
                gpu_model(xg)
            if device.type == "cuda":
                torch.cuda.synchronize()
            latency = (time.perf_counter() - t0) / 50.0
        del gpu_model, xg

    out = {
        "artifact": "phase25a_resource_accounting",
        "phase": "25A",
        "purpose": "measure the regional refiner's trainable parameters and analytical MACs",
        "model": "BARRRegionalRefinerV1",
        "architecture_id": BARR_REFINER_ARCHITECTURE_ID,
        "source_file": "src/models/barr/regional_refiner.py",
        "source_sha256": sha(MODEL_SRC),
        "trainable_parameters": n_params,
        "expected_parameters": BARR_REFINER_EXPECTED_PARAMETERS,
        "parameters_match": bool(n_params == BARR_REFINER_EXPECTED_PARAMETERS),
        "input_shape": [1, 4, 256, 256],
        "output_shape": list(y.shape),
        "analytical_macs": total_macs,
        "analytical_gmacs": round(total_macs / 1e9, 6),
        "analytical_flops": total_flops,
        "analytical_gflops": round(total_flops / 1e9, 6),
        "macs_by_layer_type": by_type,
        "macs_definition": "multiply-accumulate operations; FLOPs = 2 x MACs",
        "macs_are_analytical": True,
        "macs_measured_by": "forward hooks on every Conv2d / Linear at input 1x4x256x256",
        "reported_separately": {
            "macs": "analytical, reported above",
            "latency": "HOST-SPECIFIC, reported below; NOT a deployment claim",
            "memory": "NOT measured in Phase 25A",
            "energy": "NOT measured in Phase 25A",
        },
        "host_specific_forward_latency_seconds": latency,
        "host_latency_label": "HOST_SPECIFIC" if latency is not None else None,
        "host_device": str(device) if device is not None else None,
        "host_platform": platform.platform(),
        "claims_not_made": ["mobile ready", "real-time", "CPU ready"],
        "context_vs_global": {
            "global_model": "Phase-21 Global MedFiLM",
            "global_parameters": GLOBAL_PARAMS,
            "global_gmacs_at_1x3x512x512": GLOBAL_MACS_AT_512,
            "refiner_gmacs_at_1x4x256x256": round(total_macs / 1e9, 6),
            "refiner_over_global_macs_ratio": round((total_macs / 1e9) / GLOBAL_MACS_AT_512, 6),
            "refiner_over_global_params_ratio": round(n_params / GLOBAL_PARAMS, 6),
            "note": "the refiner is an ADDITIONAL action; the integrated system cost is global + "
                    "refiner when the router elects to refine (Phase 25D measures the budget)",
        },
        "per_layer_macs": macs,
        "verdict": "PHASE25A_RESOURCE_ACCOUNTING_COMPLETE",
        "generated_utc": UTC,
        "test_reads": 0,
    }
    (AUD / "phase25a_resource_accounting.json").write_text(
        json.dumps(out, indent=1) + "\n", encoding="utf-8")

    TAB.mkdir(parents=True, exist_ok=True)
    rows = [{"resource": "trainable_parameters", "value": n_params, "unit": "count",
             "method": "measured", "claim": "measured"},
            {"resource": "analytical_macs", "value": total_macs, "unit": "MACs",
             "method": "analytical", "claim": "measured"},
            {"resource": "analytical_gmacs", "value": round(total_macs / 1e9, 6), "unit": "G MACs",
             "method": "analytical", "claim": "measured"},
            {"resource": "host_forward_latency", "value": latency, "unit": "seconds",
             "method": "host measurement", "claim": "HOST_SPECIFIC_NOT_DEPLOYMENT"},
            {"resource": "memory", "value": None, "unit": "n/a", "method": "not measured",
             "claim": "not measured"},
            {"resource": "energy", "value": None, "unit": "n/a", "method": "not measured",
             "claim": "not measured"}]
    pd.DataFrame(rows).to_csv(TAB / "phase25a_resource_accounting.csv", index=False)

    print("=" * 78)
    print("PHASE 25A — RESOURCE ACCOUNTING")
    print("=" * 78)
    print(f"  trainable parameters : {n_params:,}")
    print(f"  analytical MACs      : {total_macs:,}  ({total_macs/1e9:.6f} G MACs)")
    print(f"  analytical FLOPs     : {total_flops:,}  ({total_flops/1e9:.6f} G FLOPs)")
    print(f"  host latency         : {latency} (HOST_SPECIFIC)")
    print(f"  vs global G MACs     : {total_macs/1e9:.4f} vs {GLOBAL_MACS_AT_512} "
          f"= {(total_macs/1e9)/GLOBAL_MACS_AT_512:.4f}x")
    print(f"wrote {AUD / 'phase25a_resource_accounting.json'}")
    print("PHASE25A_RESOURCE_ACCOUNTING_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
