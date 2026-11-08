"""Generate docs/REPOSITORY_MAP.md from the verified coverage matrix.

Map 2 is generated from full_doc_report/PHASEWISE_NOTEBOOK_COVERAGE.csv so the
phase index can never drift from the audited inventory.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "docs" / "REPOSITORY_MAP.md"
COV = ROOT / "full_doc_report" / "PHASEWISE_NOTEBOOK_COVERAGE.csv"

STATUS_LABEL = {
    "NOTEBOOK_COMPLETE": "notebook present",
    "NOTEBOOK_MISSING_RESULTS_EXIST": "reconstructed",
    "DOCUMENTATION_ONLY_PHASE": "documentation only",
    "REQUIRES_HUMAN_AUTHORIZATION": "gated (TEST consumed)",
    "NOTEBOOK_PRESENT_BUT_BROKEN": "broken",
    "NOTEBOOK_PRESENT_BUT_OBSOLETE": "obsolete",
}
EXP_LABEL = {
    "EXECUTED_WITH_RESULTS": "executed, results saved",
    "RESULTS_PRESENT_NO_RUN_ARTIFACTS": "results saved, run artifacts absent",
    "NOT_EXECUTED": "not executed",
    "NOT_AN_EXPERIMENT": "not an experiment",
    "NOT_APPLICABLE": "not applicable",
    "GATED_CONSUMED_ONE_SHOT": "gated, one-shot consumed",
}


def phase_rows():
    with COV.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def num(pid: str) -> int:
    try:
        return int("".join(ch for ch in pid if ch.isdigit()) or 0)
    except ValueError:
        return 0


def table(rows, title):
    out = [f"#### {title}", "",
           "| Phase | Directory | Purpose / notebook | Status | Experiment |",
           "|---|---|---|---|---|"]
    for r in rows:
        folder = r["phase_folder"].replace("notebooks/phasewise/", "")
        nb = r["original_notebook"]
        if nb == "NONE":
            gen = r["generated_notebook"]
            purpose = (f"[{Path(gen).name}](../full_doc_report/{gen})"
                       if gen else "no notebook")
        else:
            first = nb.split(";")[0]
            purpose = f"[{Path(first).name}](../{first})"
            if ";" in nb:
                purpose += f" (+{len(nb.split(';')) - 1} more)"
        st = STATUS_LABEL.get(r["notebook_status"], r["notebook_status"])
        ex = EXP_LABEL.get(r["experiment_status"], r["experiment_status"])
        out.append(f"| {r['phase_id']} | `{folder}` | {purpose} | {st} | {ex} |")
    out.append("")
    return out


def main() -> None:
    rows = phase_rows()
    rows_sorted = sorted(rows, key=lambda r: (num(r["phase_id"]), r["phase_folder"]))

    def band(lo, hi):
        return [r for r in rows_sorted if lo <= num(r["phase_id"]) <= hi]

    lines = [
        "# Repository Map",
        "",
        "Where everything lives. Every link below is a real repository-relative path.",
        "",
        "> Generated from `full_doc_report/PHASEWISE_NOTEBOOK_COVERAGE.csv` (57 audited",
        "> phase directories). Regenerate with",
        "> `.venv\\Scripts\\python.exe docs/generate_repository_map.py`.",
        "",
        "---",
        "",
        "## Map 1 — Project structure",
        "",
        "```text",
        "jup/",
        "├── README.md                     entry point (this documentation set)",
        "├── assets/figures/               methodology diagrams (svg/pdf/png)",
        "├── docs/                         repository + methodology + reproducibility docs",
        "├── src/                          library code",
        "│   ├── models/film/              GlobalMedFiLM backbone (G)",
        "│   ├── models/barr/              router, refiner, safety, FULL wrapper",
        "│   ├── models/                   conventional baselines",
        "│   ├── data/                     ROI transforms, datasets",
        "│   ├── metrics/                  Dice / IoU / HD95 implementations",
        "│   └── research/                 C1 / C2 / C3 + pipeline code",
        "├── scripts/training/             training entry points",
        "├── scripts/analysis/             evaluation + report builders",
        "├── notebooks/phasewise/          57 phase directories (research history)",
        "├── manifests/phase4_v3/          TRAIN5832 / VAL808 / TEST1683 splits",
        "├── experiments/                  per-epoch history.csv for 82 runs",
        "├── checkpoints/                  trained weights (git-ignored)",
        "├── reports/                      audits and tables (largely git-ignored)",
        "├── full_doc_report/              verified consolidation: notebooks, tables, figures",
        "└── tests/                        automated tests",
        "```",
        "",
        "| Need | Location |",
        "|---|---|",
        "| Full model implementation | [`src/models/barr/ra_medfilm_barr.py`](../src/models/barr/ra_medfilm_barr.py) |",
        "| Backbone implementation | [`src/models/film/global_medfilm.py`](../src/models/film/global_medfilm.py) |",
        "| Verified master notebook | [`full_doc_report/ReMedFiLM_COMPLETE_MASTER_VERIFIED.ipynb`](../full_doc_report/ReMedFiLM_COMPLETE_MASTER_VERIFIED.ipynb) |",
        "| Component registry | [`full_doc_report/REMEDFILM_FULL_COMPONENT_REGISTRY.json`](../full_doc_report/REMEDFILM_FULL_COMPONENT_REGISTRY.json) |",
        "| Method → code trace | [`docs/METHODOLOGY_IMPLEMENTATION_MAP.md`](METHODOLOGY_IMPLEMENTATION_MAP.md) |",
        "",
        "---",
        "",
        "## Map 2 — Phase-wise notebook index",
        "",
        f"{len(rows)} phase directories were audited. Status words are defined in",
        "[`full_doc_report/NOTEBOOK_RECOVERY_AND_RECONSTRUCTION.md`](../full_doc_report/NOTEBOOK_RECOVERY_AND_RECONSTRUCTION.md).",
        "",
    ]

    lines += table(band(0, 10), "Phases 00–10 — governance, data, baselines")
    lines += table(band(11, 19), "Phases 11–19 — failure analysis, localisation, refiner precursors")
    lines += table(band(20, 24), "Phases 20–24 — multi-domain baselines and the GlobalMedFiLM reference")
    lines += table(band(25, 29), "Phases 25–29 — BARR component development, integration, preservation, ablation, seeds")
    lines += table(band(30, 36), "Phases 30–36 — final development validation through robustness")
    lines += table(band(37, 40), "Phases 37–40 — evidence consolidation, protocol freeze, TEST, manuscript")

    post = [r for r in rows_sorted if not r["phase_id"][:2].isdigit()]
    if post:
        lines += table(post, "Post-phase and extension directories")

    lines += [
        "---",
        "",
        "## Map 3 — Model and checkpoint locations",
        "",
        "| Component | Code | Weights |",
        "|---|---|---|",
        "| **G** GlobalMedFiLM | [`src/models/film/global_medfilm.py`](../src/models/film/global_medfilm.py) | `checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt` |",
        "| **R_psi** Regional Refiner | [`src/models/barr/regional_refiner.py`](../src/models/barr/regional_refiner.py) | `checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt` |",
        "| **B_phi** Benefit Router | [`src/models/barr/phase25_models.py`](../src/models/barr/phase25_models.py) | `checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt` |",
        "| **S_omega** Post-Safety Gate | [`src/models/barr/phase25_models.py`](../src/models/barr/phase25_models.py) | `checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt` |",
        "| **FULL** assembly | [`src/models/barr/ra_medfilm_barr.py`](../src/models/barr/ra_medfilm_barr.py) | bundle of the four above |",
        "",
        "**Weights are not distributed with this repository.** `checkpoints/` and",
        "`*.pt` are excluded by `.gitignore`. The registry records each checkpoint's",
        "SHA-256 so a holder of the weights can verify identity:",
        "[`REMEDFILM_FULL_COMPONENT_REGISTRY.json`](../full_doc_report/REMEDFILM_FULL_COMPONENT_REGISTRY.json).",
        "",
        "| Registry field | Location |",
        "|---|---|",
        "| Component inventory (frozen, contains a units defect — see note) | [`reports/tables/phase26_component_inventory.csv`](../reports/tables/phase26_component_inventory.csv) |",
        "| Corrected parameter table | [`full_doc_report/tables/REMEDFILM_COMPONENT_PARAMETERS.csv`](../full_doc_report/tables/REMEDFILM_COMPONENT_PARAMETERS.csv) |",
        "| Backbone training closure | `experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/closure.json` |",
        "",
        "> The frozen `phase26_component_inventory.csv` stores **MACs** in G's",
        "> `parameters` column (31,551,740,928 instead of 3,523,001). Do not sum that",
        "> column. The corrected derived table is authoritative.",
        "",
        "---",
        "",
        "## Map 4 — Training and validation",
        "",
        "| Need | Location |",
        "|---|---|",
        "| Training entry points | [`scripts/training/`](../scripts/training/) |",
        "| Backbone training script | [`scripts/training/train_phase21_global_medfilm.py`](../scripts/training/train_phase21_global_medfilm.py) |",
        "| Optimizer / scheduler config | inside each `closure.json` / `run.json` under `experiments/` |",
        "| Per-epoch histories (82 runs) | `experiments/**/history.csv` |",
        "| Long-form epoch table | [`full_doc_report/tables/REMEDFILM_EPOCH_HISTORY.csv`](../full_doc_report/tables/REMEDFILM_EPOCH_HISTORY.csv) |",
        "| Run registry (best epoch, status) | [`full_doc_report/tables/TRAINING_RUN_REGISTRY.csv`](../full_doc_report/tables/TRAINING_RUN_REGISTRY.csv) |",
        "| Component-only epoch history | [`full_doc_report/REMEDFILM_COMPONENT_TRAINING_HISTORY.csv`](../full_doc_report/REMEDFILM_COMPONENT_TRAINING_HISTORY.csv) |",
        "| Internal evaluation | [`full_doc_report/REMEDFILM_FULL_VAL808_METRICS.csv`](../full_doc_report/REMEDFILM_FULL_VAL808_METRICS.csv) |",
        "| Per-sample internal scores | [`full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv`](../full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv) |",
        "| Data splits | [`manifests/phase4_v3/`](../manifests/phase4_v3/) |",
        "",
        "---",
        "",
        "## Map 5 — Scientific results",
        "",
        "| Result | Notebook | Table / figure |",
        "|---|---|---|",
        "| Six-model baseline comparison | §06 master | `full_doc_report/tables/REMEDFILM_MODEL_COMPARISON.csv` |",
        "| FULL ReMedFiLM validation | §07 master | [`REMEDFILM_FULL_VAL808_METRICS.csv`](../full_doc_report/REMEDFILM_FULL_VAL808_METRICS.csv) |",
        "| Per-domain metrics figure | §07 master | [`figures/Internal validation/`](../full_doc_report/figures/Internal%20validation/) |",
        "| Subgroup (KUB) evaluation | §09 master | `full_doc_report/figures/Internal validation/SG*.png` |",
        "| Segmentation galleries | §08 master | [`figures/Semantic segmentation/`](../full_doc_report/figures/Semantic%20segmentation/) |",
        "| External evaluation (884 cases) | §10 master | [`REMEDFILM_FULL_EXTERNAL_METRICS.csv`](../full_doc_report/REMEDFILM_FULL_EXTERNAL_METRICS.csv) |",
        "| 13-arm ablation | §12 master | [`REMEDFILM_ABLATION_AND_PROGRESSION.csv`](../full_doc_report/REMEDFILM_ABLATION_AND_PROGRESSION.csv) |",
        "| Component progression | §11 master | [`figures/Progression/`](../full_doc_report/figures/Progression/) |",
        "| Routing and safety | §13 master | [`figures/Routing and safety/`](../full_doc_report/figures/Routing%20and%20safety/) |",
        "| Statistics / reproducibility | §14 master | [`figures/Statistics/`](../full_doc_report/figures/Statistics/) |",
        "| Robustness | §15 master | [`figures/Robustness/`](../full_doc_report/figures/Robustness/) |",
        "| Efficiency | §16 master | [`figures/Efficiency/`](../full_doc_report/figures/Efficiency/) |",
        "| Historical TEST summary | §17 master | `reports/audits/phase39_final_test_v1_2_scientific_result.json` |",
        "",
        "Result reconciliation (0.837290 vs 0.837862):",
        "[`REMEDFILM_FULL_RESULT_RECONCILIATION.md`](../full_doc_report/REMEDFILM_FULL_RESULT_RECONCILIATION.md).",
        "",
        "---",
        "",
        "## Map 6 — Documentation and reproduction",
        "",
        "| Need | Location |",
        "|---|---|",
        "| Environment setup | [`docs/REPRODUCIBILITY_GUIDE.md`](REPRODUCIBILITY_GUIDE.md) |",
        "| Method → code trace | [`docs/METHODOLOGY_IMPLEMENTATION_MAP.md`](METHODOLOGY_IMPLEMENTATION_MAP.md) |",
        "| Tests | [`tests/`](../tests/) |",
        "| Safe analysis runner | [`full_doc_report/Scripts/execute_notebooks.py`](../full_doc_report/Scripts/execute_notebooks.py) |",
        "| Figure regeneration | [`full_doc_report/Scripts/build_figures.py`](../full_doc_report/Scripts/build_figures.py) |",
        "| Methodology figure source | [`assets/figures/generate_methodology.py`](../assets/figures/generate_methodology.py) |",
        "| Verification suites | [`full_doc_report/Scripts/verify_verified.py`](../full_doc_report/Scripts/verify_verified.py) |",
        "| Scientific QA record | [`REMEDFILM_FINAL_SCIENTIFIC_QA.md`](../full_doc_report/REMEDFILM_FINAL_SCIENTIFIC_QA.md) |",
        "| Pending experiments | [`PENDING_CONTROLLED_EXPERIMENTS.md`](../full_doc_report/PENDING_CONTROLLED_EXPERIMENTS.md) |",
        "",
    ]

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  ({len(lines)} lines, {len(rows)} phases)")


if __name__ == "__main__":
    main()
