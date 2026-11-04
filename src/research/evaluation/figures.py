"""Reproducible descriptive figures from integrity-verified evaluation cells."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from . import reports
from src.research.deployment.artifacts import digest


def write_figures(root: Path, output: Path) -> dict:
    """Never selects cases or supplies missing measurements; refuses overwrite."""
    results = reports.collect_results(root)
    cells = [c for c in results["cells"] if c["status"] == "COMPLETE_VALIDATED"]
    if not cells:
        raise ValueError("no validated cells to plot")
    if len(results["evidence_classes"]) != 1:
        raise ValueError("mixed evidence classes must not share a figure")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    source_rows = reports.per_domain_rows(cells)
    with (output / "domain_source.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(source_rows[0]))
        writer.writeheader(); writer.writerows(source_rows)
    artifacts = ["domain_source.csv"]
    with plt.rc_context({"svg.hashsalt": "ra_medfilm_barr_descriptive_v1"}):
        fig, ax = plt.subplots(figsize=(10, 6))
        domains = list(dict.fromkeys(r["domain"] for r in source_rows))
        models = list(dict.fromkeys(r["model_key"] for r in source_rows))
        for i, model in enumerate(models):
            rows = [r for r in source_rows if r["model_key"] == model]
            ys = [float(r["dice"]) for r in rows]
            if not all(math.isfinite(y) for y in ys):
                raise ValueError("nonfinite domain measurement")
            ax.scatter([domains.index(r["domain"]) + .04 * (i - len(models) / 2) for r in rows],
                       ys, label=model, alpha=.7)
        ax.set_xticks(range(len(domains)), domains)
        ax.set_ylim(0, 1); ax.set_ylabel("Dice (each point is one seed/domain)")
        ax.set_title(results["banner"], fontsize=9); ax.legend(fontsize=6)
        fig.tight_layout()
        fig.savefig(output / "domain_comparison.png", dpi=160)
        plt.close(fig)
        artifacts.append("domain_comparison.png")
        # Cost is measured latency only. Analytical MACs are never substituted.
        cost = []
        for cell in cells:
            latency = (cell.get("efficiency") or {}).get("latency_ms_p50")
            if latency is not None and math.isfinite(float(latency)):
                cost.append({"model_key": cell["model_key"], "seed": cell["seed"],
                             "latency_ms_p50": float(latency), "dice": cell["equal_domain_macro_dice"]})
        if cost:
            fig, ax = plt.subplots(figsize=(9, 6))
            for row in cost:
                ax.scatter(row["latency_ms_p50"], row["dice"])
                ax.annotate(f"{row['model_key']} s{row['seed']}", (row["latency_ms_p50"], row["dice"]), fontsize=5)
            ax.set_xlabel("Measured inference latency p50 (ms)"); ax.set_ylabel("Macro-domain Dice")
            ax.set_ylim(0, 1); ax.set_title(results["banner"], fontsize=9)
            fig.tight_layout(); fig.savefig(output / "accuracy_latency.png", dpi=160); plt.close(fig)
            artifacts.append("accuracy_latency.png")
        (output / "latency_source.json").write_text(json.dumps(cost, indent=2, allow_nan=False))
        artifacts.append("latency_source.json")
    manifest = {"evidence_class": results["evidence_classes"][0], "banner": results["banner"],
                "accuracy_latency_status": "GENERATED" if cost else "PENDING_MEASURED_LATENCY",
                "claim_status": "NO_CLAIM", "scientific_validation": False,
                "files": {name: {"sha256": digest(output / name), "bytes": (output / name).stat().st_size}
                          for name in artifacts}}
    (output / "figure_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(write_figures(args.root, args.out), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
