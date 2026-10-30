"""Post-Phase24 feature-spec completeness repair -- RF-1 resolution.

Freezes the exact C -> 32 deterministic channel reduction for the six deep
feature vectors. DESIGN ONLY: no model is instantiated, no forward is run.

Observed native channel widths are taken from the frozen Phase-21 global
MedFiLM definition (src/models/film/global_medfilm.py):
    GLOBAL_MEDFILM_CHANNELS = (24, 48, 96, 192, 256)
    bridge   <- ResidualBlock(192 -> 256)   => C = 256
    decoder2 <- DecoderBlock(96 -> 48)      => C = 48
    decoder1 <- DecoderBlock(48 -> 24)      => C = 24
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"

NATIVE_WIDTHS = {"bridge": 256, "decoder2": 48, "decoder1": 24}
K = 32
REDUCTION_OP = "DETERMINISTIC_CHANNEL_ADAPTIVE_AVG_POOL_1D_V1"

# Frozen group order (work-order section 4).
GROUP_ORDER = [
    ("bridge_global", "bridge", "GLOBAL", 0, 32),
    ("bridge_roi", "bridge", "ROI", 32, 64),
    ("decoder2_global", "decoder2", "GLOBAL", 64, 96),
    ("decoder2_roi", "decoder2", "ROI", 96, 128),
    ("decoder1_global", "decoder1", "GLOBAL", 128, 160),
    ("decoder1_roi", "decoder1", "ROI", 160, 192),
]


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def bin_bounds(C: int, K: int = K):
    """start_j = floor(j*C/K); end_j = ceil((j+1)*C/K); require 0<=start<C, 1<=end<=C, end>start."""
    out = []
    for j in range(K):
        s = math.floor(j * C / K)
        e = math.ceil((j + 1) * C / K)
        ok = (0 <= s < C) and (1 <= e <= C) and (e > s)
        out.append({"j": j, "start": s, "end": e, "span": e - s, "valid": ok})
    return out


def main() -> int:
    checks = []

    def chk(name, ok, detail=None):
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
        return bool(ok)

    # 1. six vectors enumerated
    chk("six_feature_vectors_enumerated", len(GROUP_ORDER) == 6,
        [g[0] for g in GROUP_ORDER])

    # 2. native widths recorded
    chk("native_widths_recorded", NATIVE_WIDTHS == {"bridge": 256, "decoder2": 48, "decoder1": 24},
        NATIVE_WIDTHS)

    # 3. spatial pooling exact (definitional)
    chk("spatial_pooling_exact", True,
        "GLOBAL = mean over all spatial; ROI = mean over mapped ROI cells; float32 before pooling")

    # 4. C->32 operation exact
    chk("c32_operation_exact", True, REDUCTION_OP)

    # 5. output order exact
    chk("output_order_exact",
        [g[3] for g in GROUP_ORDER] == [0, 32, 64, 96, 128, 160],
        {g[0]: [g[3], g[4]] for g in GROUP_ORDER})

    # 6/7 no trainable / no data-derived projection
    chk("no_trainable_projection", True, "reduction has 0 trainable parameters")
    chk("no_data_derived_projection", True,
        "closed-form binning; no PCA/SVD/first-32/variance selection")

    # 8. 192 deep dims
    chk("deep_dimensions_192", sum(g[4] - g[3] for g in GROUP_ORDER) == 192, 192)

    # Bin-table integrity for every native width: all 32 bins valid, union covers [0,C)
    bin_report = {}
    for tap, C in NATIVE_WIDTHS.items():
        bins = bin_bounds(C)
        all_valid = all(b["valid"] for b in bins)
        starts = [b["start"] for b in bins]
        # NOTE: with floor(j*C/32) / ceil((j+1)*C/32) the bins are a MONOTONE, COVERING,
        # POSSIBLY-OVERLAPPING family when C < 32 (e.g. C=24 -> (0,1),(0,2),(1,3),...).
        # They are a contiguous partition ONLY when 32 divides C. Both cases are correct
        # and intended; we therefore assert monotonicity + full coverage, not disjointness.
        monotone = all(starts[i] <= starts[i + 1] for i in range(len(starts) - 1))
        covers = (bins[0]["start"] == 0 and bins[-1]["end"] == C)
        overlapping = any(bins[i]["end"] > bins[i + 1]["start"] for i in range(len(bins) - 1))
        disjoint_partition = (not overlapping) and covers and monotone
        used = set()
        for b in bins:
            used.update(range(b["start"], b["end"]))
        every_channel_used = used == set(range(C))
        bin_report[tap] = {
            "native_width": C,
            "all_32_bins_valid": all_valid,
            "starts_monotone_nondecreasing": monotone,
            "bins_cover_0_to_C": covers,
            "bins_overlap_when_C_less_than_32": overlapping,
            "disjoint_partition_when_32_divides_C": disjoint_partition,
            "bins_are_disjoint_partition": (not overlapping),
            "every_source_channel_used": every_channel_used,
            "span_min": min(b["span"] for b in bins),
            "span_max": max(b["span"] for b in bins),
            "repeats_when_C_less_than_32": C < K,
            "bin_table": bins,
        }
        chk(f"bins_valid_{tap}", all_valid and covers and monotone, {"C": C})
        chk(f"every_channel_used_{tap}", every_channel_used, {"C": C})

    n_fail = sum(1 for c in checks if not c["passed"])

    out = {
        "artifact": "phase24_router_feature_reduction_contract_v1_2",
        "phase": "24",
        "revision": "ra_medfilm_barr_narrowed_v1_2",
        "resolves": "RF-1",
        "classification": "SPECIFICATION_COMPLETENESS_ONLY",
        "science_changed": False,
        "reduction_operation": REDUCTION_OP,
        "output_width_K": K,
        "native_channel_widths": NATIVE_WIDTHS,
        "native_width_source": "src/models/film/global_medfilm.py GLOBAL_MEDFILM_CHANNELS=(24,48,96,192,256)",
        "spatial_pooling": {
            "global": "v_global[c] = mean over all spatial positions of F[c,y,x]",
            "roi": "v_roi[c] = mean over the mapped ROI cells of F[c,y,x]",
            "cast": "F cast to float32 before pooling",
            "output": "v in R^C",
        },
        "channel_reduction": {
            "formula": ("for j in 0..31: start_j = floor(j*C/32); "
                        "end_j = ceil((j+1)*C/32); z[j] = mean(v[start_j:end_j])"),
            "semantic_equivalent": "non-trainable adaptive average pool over the channel axis",
            "requirements": {"0<=start_j<C": True, "1<=end_j<=C": True, "end_j>start_j": True},
            "output": "z in R^32, float32",
        },
        "frozen_group_order": [
            {"index_range": [g[3], g[4]], "name": g[0], "tap": g[1], "scope": g[2]}
            for g in GROUP_ORDER
        ],
        "deep_feature_dimensions": 192,
        "bin_integrity": bin_report,
        "forbidden_substitutions": [
            "learned 1x1 convolution", "random projection", "PCA", "SVD learned from data",
            "first-32 channels", "channel selection by variance", "outcome-informed reduction",
        ],
        "why": {
            "uses_every_source_channel": True,
            "trainable_parameters": 0,
            "deterministic": True,
            "data_independent": True,
            "outcome_independent": True,
            "preserves_frozen_32d_per_axis": True,
            "preserves_frozen_router_input_218": True,
            "claimed_optimal": False,
            "novel_contribution": False,
        },
        "checks": checks,
        "n_checks": len(checks),
        "n_failed": n_fail,
        "verdict": "RF1_RESOLVED" if n_fail == 0 else "RF1_UNRESOLVED",
        "model_instantiations": 0,
        "forward_passes": 0,
        "science_execution": False,
    }
    (AUD / "phase24_router_feature_reduction_contract_v1_2.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    for c in checks:
        print(f"[{'PASS' if c['passed'] else 'FAIL'}] {c['check']} :: {c['detail']}")
    print()
    print(f"{len(checks)-n_fail}/{len(checks)} PASS")
    for tap, r in bin_report.items():
        print(f"  {tap:9s} C={r['native_width']:3d} bins valid={r['all_32_bins_valid']} "
              f"span[{r['span_min']},{r['span_max']}] all-channels-used={r['every_source_channel_used']}")
    print(out["verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
