"""Phase 21 — exact analytical MAC counter for the Global MedFiLM reference.

This is NOT a third-party FLOP library. It is a closed-form count for the only
two layer types that dominate cost in this architecture:

    Conv2d   MACs = k_h * k_w * C_in * C_out * H_out * W_out
    Linear   MACs = in_features * out_features

It deliberately EXCLUDES GroupNorm affine/statistics, SiLU, MaxPool2d,
bilinear interpolation and the FiLM elementwise modulation, because those are
negligible relative to the convolutions and counting them would require
op-level instrumentation. The figure is therefore a LOWER BOUND on total
arithmetic, exact for convolution and linear layers.

Usage
-----
    # Global MedFiLM only (CPU, no CUDA init)
    ./.venv/Scripts/python.exe scripts/analysis/phase21_mac_count.py

    # All six panel models -> reports/tables/phase21_six_model_compute.csv
    # (run AFTER training so the GPU/CPU is free; uses GPU when available)
    ./.venv/Scripts/python.exe scripts/analysis/phase21_mac_count.py --all-models
"""
from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path

import pandas as pd
import torch
from torch import nn

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.models.film import GlobalMedFiLM  # noqa: E402

OUT = ROOT / "reports" / "audits" / "phase21_analytical_mac_count.json"
OUT_TABLE = ROOT / "reports" / "tables" / "phase21_six_model_compute.csv"

# Cross-check constants, NOT the source of truth. The values written to the CSV are
# always MEASURED from the constructed model; these exist only so that a silent
# architecture/regression change is caught loudly instead of being carried forward.
# The five baselines are taken from the frozen Phase-20B table
# (reports/tables/phase20b_five_model_comparison.csv); global_medfilm from the frozen
# Phase-21 architecture binding.
EXPECTED_PARAMS = {
    "unet": 7763041, "attention_unet": 7851285, "unetpp": 9159681,
    "deeplabv3plus": 40347041, "transformer_mit_unet": 16347777,
    "global_medfilm": 3523001,
}
DISPLAY = {"unet": "U-Net", "attention_unet": "Attention U-Net", "unetpp": "U-Net++",
           "deeplabv3plus": "DeepLabV3+", "transformer_mit_unet": "Transformer/MiT",
           "global_medfilm": "Global MedFiLM"}
MODEL_ORDER = ["unet", "attention_unet", "unetpp", "deeplabv3plus",
               "transformer_mit_unet", "global_medfilm"]


def conv_macs(module: nn.Conv2d, shape):
    h_out, w_out = shape[2], shape[3]
    k_h, k_w = module.kernel_size
    return k_h * k_w * module.in_channels * module.out_channels * h_out * w_out


def accepts_task_ids(model) -> bool:
    """True only for task-conditioned models (Global MedFiLM).

    The five Phase-20/20B baselines are declared ``forward(self, x)`` and would
    raise TypeError if a second positional argument were passed. This is detected
    from the signature rather than hard-coded, so the counter stays correct if the
    panel changes.
    """
    try:
        params = inspect.signature(model.forward).parameters
    except (TypeError, ValueError):
        return False
    positional = [
        p for p in params.values()
        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) and p.name != "self"
    ]
    return len(positional) >= 2


def count(model, device) -> tuple[int, list[dict]]:
    model = model.to(device).eval()
    records: list[dict] = []
    handles = []

    def hook(name):
        def fn(mod, inp, out):
            if isinstance(mod, nn.Conv2d):
                records.append({"layer": name, "type": "Conv2d",
                                "macs": int(conv_macs(mod, out.shape))})
            elif isinstance(mod, nn.Linear):
                records.append({"layer": name, "type": "Linear",
                                "macs": int(mod.in_features * mod.out_features)})
        return fn

    for name, mod in model.named_modules():
        if isinstance(mod, (nn.Conv2d, nn.Linear)):
            handles.append(mod.register_forward_hook(hook(name)))
    with torch.no_grad():
        x = torch.zeros(1, 3, 512, 512, device=device)
        if accepts_task_ids(model):
            model(x, torch.zeros(1, dtype=torch.long, device=device))
        else:
            model(x)
    for h in handles:
        h.remove()
    return sum(r["macs"] for r in records), records


def build_baseline(model_key: str):
    """Rebuild a frozen Phase-20/20B baseline exactly as its trainer did."""
    from src.models.factory import create_model
    if model_key == "unetpp":
        from src.models.unetpp import UNetPlusPlus
        return UNetPlusPlus(in_channels=3, out_channels=1, base_channels=32)
    if model_key == "transformer_mit_unet":
        from src.models.transformer_mit_unet import TransformerMiTUNet
        return TransformerMiTUNet(in_channels=3, out_channels=1, base_channels=32)
    if model_key == "deeplabv3plus":
        from src.models.deeplabv3plus import DeepLabV3Plus
        return DeepLabV3Plus(in_channels=3, out_channels=1, base_channels=32)
    return create_model(model_key, in_channels=3, out_channels=1, base_channels=32)


def resolve_device(spec: str) -> torch.device:
    """Resolve the measurement device explicitly.

    Do NOT rely on ``CUDA_VISIBLE_DEVICES=""`` in the shell: it was observed to be
    ignored on this host, which silently sent the sweep to the GPU while a training
    run was live. MAC counts are shape-based and therefore device-independent, so
    the numbers were still valid, but the provenance was wrong and the live run was
    put at unnecessary risk. An explicit flag makes the choice auditable.
    """
    if spec == "cpu":
        return torch.device("cpu")
    if spec == "cuda":
        if not torch.cuda.is_available():
            raise SystemExit("--device cuda requested but CUDA is not available")
        return torch.device("cuda:0")
    return torch.device("cuda:0") if torch.cuda.is_available() else torch.device("cpu")


def run_all_models(device_spec: str = "auto") -> int:
    device = resolve_device(device_spec)
    rows = []
    mismatches = []
    for key in MODEL_ORDER:
        model = GlobalMedFiLM(task_count=4) if key == "global_medfilm" else build_baseline(key)
        n_params = int(sum(p.numel() for p in model.parameters() if p.requires_grad))
        exp = EXPECTED_PARAMS.get(key)
        if exp is not None and n_params != exp:
            mismatches.append((key, n_params, exp))
            print(f"  !! PARAM MISMATCH {key}: measured {n_params:,} != expected {exp:,}")
        conditioned = accepts_task_ids(model)
        total, _ = count(model, device)
        rows.append({
            "model_key": key, "display_name": DISPLAY[key], "params": n_params,
            "params_expected": exp, "params_match": (exp is None or n_params == exp),
            "macs": int(total), "gmacs": round(total / 1e9, 4),
            "gflops_2x": round(total * 2 / 1e9, 4),
            "gmacs_per_mparam": round(total / 1e9 / (n_params / 1e6), 4),
            "task_ids_passed": conditioned,
            "input_shape": "1x3x512x512",
            "device": device.type,
            "method": "analytical Conv2d/Linear count (lower bound)",
        })
        del model
        if device.type == "cuda":
            torch.cuda.empty_cache()
        print(f"  {key:22s} params {n_params:>10,}  {total/1e9:>8.4f} G MACs")

    df = pd.DataFrame(rows)
    df["params_rank"] = df["params"].rank(method="min").astype(int)
    df["gmacs_rank"] = df["gmacs"].rank(method="min").astype(int)
    med_p = int(df.loc[df["model_key"] == "global_medfilm", "params"].iloc[0])
    med_g = float(df.loc[df["model_key"] == "global_medfilm", "gmacs"].iloc[0])
    df["params_vs_medfilm_x"] = (df["params"] / med_p).round(3)
    df["gmacs_vs_medfilm_x"] = (df["gmacs"] / med_g).round(3)
    df = df.sort_values("gmacs").reset_index(drop=True)

    df.to_csv(OUT_TABLE, index=False)
    print("\nWROTE", OUT_TABLE)
    print(df[["display_name", "params", "gmacs", "gflops_2x",
              "params_rank", "gmacs_rank",
              "params_vs_medfilm_x", "gmacs_vs_medfilm_x"]].to_string(index=False))
    print(f"\nGlobal MedFiLM is rank {int(df.loc[df.model_key=='global_medfilm','params_rank'].iloc[0])}/6 "
          f"on parameters and rank {int(df.loc[df.model_key=='global_medfilm','gmacs_rank'].iloc[0])}/6 "
          f"on compute.")

    if mismatches:
        print("\nFAIL CLOSED: measured parameter counts disagree with the frozen reference "
              "for " + ", ".join(m[0] for m in mismatches) +
              ". The comparison would be invalid; refusing to certify it.")
        return 3
    print("PARAMETER CROSS-CHECK PASS: all six measured counts match the frozen reference.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all-models", action="store_true",
                    help="Count all six panel models (run after training).")
    ap.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto",
                    help="Measurement device. Use 'cpu' while a training run is live; "
                         "the count is device-independent, so this only affects provenance "
                         "and GPU contention.")
    args = ap.parse_args()
    if args.all_models:
        return run_all_models(args.device)

    model = GlobalMedFiLM(task_count=4)
    device = resolve_device(args.device)
    total, records = count(model, device)

    by_type: dict[str, int] = {}
    by_block: dict[str, int] = {}
    for r in records:
        by_type[r["type"]] = by_type.get(r["type"], 0) + r["macs"]
        block = r["layer"].split(".")[0]
        by_block[block] = by_block.get(block, 0) + r["macs"]

    payload = {
        "artifact": "phase21_analytical_mac_count",
        "phase": 21,
        "method": "exact closed-form count for Conv2d and Linear layers",
        "not_a_third_party_flop_library": True,
        "excluded_ops": ["GroupNorm affine/statistics", "SiLU", "MaxPool2d",
                         "bilinear interpolation", "FiLM elementwise modulation",
                         "sigmoid"],
        "semantics": "LOWER BOUND on total arithmetic; exact for conv and linear layers",
        "input_shape": [1, 3, 512, 512],
        "batch_size": 1,
        "device": device.type,
        "task_ids_passed": True,
        "measured_parameter_count": int(
            sum(p.numel() for p in model.parameters() if p.requires_grad)),
        "parameter_count_cross_check_pass": (
            int(sum(p.numel() for p in model.parameters() if p.requires_grad))
            == EXPECTED_PARAMS["global_medfilm"]),
        "total_macs": int(total),
        "total_gmacs": round(total / 1e9, 4),
        "total_flops_convention": int(total * 2),
        "total_gflops_convention": round(total * 2 / 1e9, 4),
        "flops_note": "FLOPs = 2 x MACs (multiply + accumulate), the common convention",
        "by_layer_type": {k: {"macs": int(v), "gmacs": round(v / 1e9, 4)}
                          for k, v in sorted(by_type.items())},
        "by_block": {k: {"macs": int(v), "gmacs": round(v / 1e9, 4)}
                     for k, v in sorted(by_block.items(), key=lambda x: -x[1])},
        "n_counted_layers": len(records),
        "test_reads": 0,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"total MACs @ 1x3x512x512 : {total:,}  ({total/1e9:.4f} G MACs)")
    print(f"total FLOPs (2xMACs)     : {total*2:,}  ({total*2/1e9:.4f} G FLOPs)")
    print(f"counted layers           : {len(records)}")
    print("\nby block:")
    for k, v in sorted(by_block.items(), key=lambda x: -x[1]):
        print(f"  {k:16s} {v/1e9:>8.4f} G MACs  ({100*v/total:5.1f}%)")
    print("\nWROTE", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
