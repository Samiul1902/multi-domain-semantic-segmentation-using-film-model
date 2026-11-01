"""Per-image exporter for any end-to-end system exposing ``infer(image, task_id)``.

The mask is used strictly after inference, only to score the output.  Samples are supplied
by the caller; this module never opens a dataset by itself.
"""
from __future__ import annotations

import time
from typing import Any, Callable, Iterable, Mapping

import numpy as np
import torch

from .matrix import per_image_record, summarize_records


def evaluate_routed_system(system: Any, samples: Iterable[Mapping[str, Any]], *, parameters: int,
                           macs: float | None = None, warmup: int = 2) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Run batch-1 inference over ``samples`` (dicts with sample_id, domain, task_id, image, mask)."""
    cuda = system.device.type == "cuda"
    if cuda:
        torch.cuda.reset_peak_memory_stats(system.device)
    records, latencies = [], []
    for i, sample in enumerate(samples):
        image = sample["image"]
        if cuda:
            torch.cuda.synchronize(system.device)
        start = time.perf_counter()
        out = system.infer(image, int(sample["task_id"]))
        if cuda:
            torch.cuda.synchronize(system.device)
        elapsed = (time.perf_counter() - start) * 1000.0
        if i >= warmup:
            latencies.append(elapsed)
        records.append(per_image_record(
            sample_id=str(sample["sample_id"]), domain=str(sample["domain"]),
            final_prob=out["final_probability"], global_prob=out["global_probability"],
            mask=np.asarray(sample["mask"]), state=out["state"]))
    peak = torch.cuda.max_memory_allocated(system.device) / 2 ** 20 if cuda else None
    summary = summarize_records(records, latency_ms=latencies, peak_memory_mib=peak,
                                parameters=parameters, macs=macs, has_routing=True)
    return records, summary


def evaluate_plain_model(model: torch.nn.Module, samples: Iterable[Mapping[str, Any]], *, device: str,
                         parameters: int, macs: float | None = None, takes_task: bool = False,
                         warmup: int = 2) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Single-network baseline / GlobalMedFiLM exporter; the global map is the output itself."""
    dev = torch.device(device)
    model = model.eval().to(dev)
    if dev.type == "cuda":
        torch.cuda.reset_peak_memory_stats(dev)
    records, latencies = [], []
    with torch.inference_mode():
        for i, sample in enumerate(samples):
            image = sample["image"].to(dev).float()
            if dev.type == "cuda":
                torch.cuda.synchronize(dev)
            start = time.perf_counter()
            logits = (model(image, task_ids=torch.tensor([int(sample["task_id"])], device=dev))
                      if takes_task else model(image))
            if dev.type == "cuda":
                torch.cuda.synchronize(dev)
            if i >= warmup:
                latencies.append((time.perf_counter() - start) * 1000.0)
            prob = torch.sigmoid(logits.float())[0, 0].cpu().numpy()
            records.append(per_image_record(sample_id=str(sample["sample_id"]), domain=str(sample["domain"]),
                                            final_prob=prob, global_prob=prob, mask=np.asarray(sample["mask"])))
    peak = torch.cuda.max_memory_allocated(dev) / 2 ** 20 if dev.type == "cuda" else None
    return records, summarize_records(records, latency_ms=latencies, peak_memory_mib=peak,
                                      parameters=parameters, macs=macs, has_routing=False)
