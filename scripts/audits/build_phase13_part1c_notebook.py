"""PHASE-13 PART-1C — reviewer notebook builder.

Builds notebooks/phasewise/phase_13_predicted_roi_localization/
phase13_clean_v3_best_checkpoint_proposal_analysis.ipynb

READ ONLY against frozen Part-1C tables. No inference on rerun. No threshold
search. No regional segmentation. No gate decision. TEST locked.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NB = (ROOT / "notebooks" / "phasewise" / "phase_13_predicted_roi_localization"
      / "phase13_clean_v3_best_checkpoint_proposal_analysis.ipynb")
FIG = ROOT / "reports" / "figures" / "phase13_part1c"
EXP = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"
TABLES = ROOT / "reports" / "tables"
AUDITS = ROOT / "reports" / "audits"


def md(t): return {"cell_type": "markdown", "metadata": {}, "source": t}
def code(s): return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": s}


def build_cells():
    c = []
    c.append(md(
        "# Phase 13 Part 1C — Frozen Best-Checkpoint Standalone GT-Free Proposal Analysis\n"
        "\n"
        "**READ-ONLY REVIEWER NOTEBOOK.**\n"
        "\n"
        "Performs: no training, no threshold search, no proposal grid, no regional\n"
        "segmentation, no GLOBAL/ORACLE/PREDICTED comparison, no gate decision, no TEST access.\n"
        "\n"
        "It reads the frozen Part-1C tables produced by the single authorized\n"
        "best-checkpoint full-VAL inference pass.\n"
    ))

    c.append(md("## 2. Frozen checkpoint / protocol identity\n"))
    c.append(code(
        "import json, hashlib\nfrom pathlib import Path\nimport pandas as pd, numpy as np\n"
        f"ROOT = Path(r'{ROOT}')\n"
        f"TABLES = ROOT / 'reports' / 'tables'\n"
        f"AUDITS = ROOT / 'reports' / 'audits'\n"
        f"EXP = '{EXP}'\n"
        "def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()\n"
        "PROTO = json.loads((AUDITS / 'phase13_part1c_best_checkpoint_proposal_protocol.json').read_text(encoding='utf-8'))\n"
        "AUDIT = json.loads((AUDITS / 'phase13_part1c_best_checkpoint_proposal_evaluation.json').read_text(encoding='utf-8'))\n"
        "print('protocol status   :', PROTO['status'])\n"
        "print('best epoch        :', PROTO['best_checkpoint_epoch'])\n"
        "print('best.pt sha       :', PROTO['best_checkpoint_sha'])\n"
        "print('physical best.pt  :', sha(ROOT / 'checkpoints' / EXP / 'best.pt'))\n"
        "print('sha match         :', PROTO['best_checkpoint_sha'] == sha(ROOT / 'checkpoints' / EXP / 'best.pt'))\n"
        "print('manifest/taxonomy :', PROTO['manifest'], '/', PROTO['taxonomy'])\n"
    ))

    c.append(md("## 3. Population integrity\n"))
    c.append(code(
        "case = pd.read_csv(TABLES / 'phase13_part1c_best_checkpoint_case_proposals.csv')\n"
        "prop = pd.read_csv(TABLES / 'phase13_part1c_best_checkpoint_proposals.csv')\n"
        "comp = pd.read_csv(TABLES / 'phase13_part1c_best_checkpoint_component_coverage.csv')\n"
        "print('VAL cases      :', len(case), '(expected 103)')\n"
        "print('VAL components :', len(comp), '(expected 152)')\n"
        "print('strata         :', comp.size_stratum.value_counts().to_dict())\n"
        "print('hard-Tiny      :', int(comp.hard_tiny.sum()), '(expected 15)')\n"
        "print('global-empty   :', comp[comp.global_empty_image].sample_id.nunique(), '(expected 5)')\n"
        "assert len(case) == 103 and len(comp) == 152\n"
        "assert int(comp.hard_tiny.sum()) == 15\n"
        "assert comp[comp.global_empty_image].sample_id.nunique() == 5\n"
    ))

    c.append(md("## 4. Proposal generation contract\n"))
    c.append(code(
        "cfg = PROTO\n"
        "print('threshold/margin/top_k/nms :', cfg['proposal_threshold'], cfg['proposal_margin'], cfg['proposal_top_k'], cfg['proposal_nms_iou'])\n"
        "print('proposal configurations    :', cfg['proposal_configurations'])\n"
        "print('grid search                :', cfg['grid_search'])\n"
        "print('heatmap                    :', cfg['heatmap'])\n"
        "print('GT used for proposal generation: NO (GT only after proposals exist)')\n"
        "print('total proposals            :', len(prop), '(expected 494)')\n"
    ))

    c.append(md("## 5. Bbox-vs-pixel semantics\n"))
    c.append(code(
        "print('PRIMARY   :', AUDIT['primary_coverage'])\n"
        "print('SECONDARY :', AUDIT['secondary_sensitivity'])\n"
        "print('pixel metrics are selection metrics:', False)\n"
    ))

    c.append(md("## 6. Aggregate reproduction gate\n"))
    c.append(code(
        "rg = AUDIT['reproduction_gate']\n"
        "print('status    :', rg['status'])\n"
        "print('mismatches:', len(rg['mismatches']))\n"
        "assert rg['status'] == 'PASS' and not rg['mismatches']\n"
        "for k, v in sorted(rg['expected_bbox'].items()):\n"
        "    print(f'  bbox  {k:32s} got={AUDIT[\"bbox_metrics\"][k]!r} expected={v!r}')\n"
    ))

    c.append(md("## 7. Canonical aggregate localization metrics (BBOX — PRIMARY)\n"))
    c.append(code(
        "for k, v in AUDIT['bbox_metrics'].items(): print(f'{k:32s} {v!r}')\n"
    ))

    c.append(md("## 8. Pixel sensitivity metrics (SECONDARY)\n"))
    c.append(code(
        "for k, v in AUDIT['pixel_metrics'].items(): print(f'{k:32s} {v!r}')\n"
    ))

    c.append(md("## 9. Proposal-count / ROI-area distributions\n"))
    c.append(code(
        "FIG = ROOT / 'reports' / 'figures' / 'phase13_part1c'\n"
        "FIG.mkdir(parents=True, exist_ok=True)\n"
        "import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt\n"
        "fig, ax = plt.subplots(1, 2, figsize=(11, 4))\n"
        "ax[0].hist(case['proposal_count'], bins=range(0, int(case['proposal_count'].max()) + 2), color='steelblue')\n"
        "ax[0].set_xlabel('proposals per image'); ax[0].set_ylabel('images'); ax[0].set_title('Proposal count')\n"
        "ax[1].hist(case['proposal_union_area_fraction'], bins=30, color='darkorange')\n"
        "ax[1].set_xlabel('union ROI area fraction'); ax[1].set_title('ROI area')\n"
        "for a in ax: a.grid(alpha=0.3)\n"
        "fig.tight_layout(); fig.savefig(FIG / 'proposal_distributions.png', dpi=120); plt.close(fig)\n"
        "print('mean proposals/image :', float(case['proposal_count'].mean()))\n"
        "print('mean ROI area frac   :', float(case['proposal_union_area_fraction'].mean()))\n"
    ))

    c.append(md("## 10. Size-stratified coverage\n"))
    c.append(code(
        "strat = pd.read_csv(TABLES / 'phase13_part1c_size_stratified_coverage.csv')\n"
        "print(strat[['stratum','n_components','bbox_covered90_count','bbox_covered90_rate',\n"
        "             'bbox_mean_coverage','pixel_covered90_count','pixel_covered90_rate']].to_string(index=False))\n"
    ))

    c.append(md("## 11. Hard-Tiny analysis\n"))
    c.append(code(
        "hard = comp[comp.hard_tiny]\n"
        "print('hard-Tiny components:', len(hard))\n"
        "print('bbox covered90 :', int(hard.bbox_covered90.sum()), '/', len(hard))\n"
        "print('pixel covered90:', int(hard.pixel_covered90.sum()), '/', len(hard))\n"
    ))

    c.append(md("## 12. Global-empty analysis\n"))
    c.append(code(
        "ge = comp[comp.global_empty_image]\n"
        "print('global-empty images:', ge.sample_id.nunique())\n"
        "print('bbox images covered90 :', len({r.sample_id for r in ge.itertuples() if r.bbox_covered90}), '/', ge.sample_id.nunique())\n"
        "print('pixel images covered90:', len({r.sample_id for r in ge.itertuples() if r.pixel_covered90}), '/', ge.sample_id.nunique())\n"
    ))

    c.append(md("## 13. Multi-component analysis\n"))
    c.append(code(
        "multi_ids = set(comp.groupby('sample_id').size().loc[lambda v: v > 1].index)\n"
        "multi = comp[comp.sample_id.isin(multi_ids)]\n"
        "print('multi-component images:', len(multi_ids))\n"
        "print('multi-component rows  :', len(multi))\n"
        "print('bbox recall90 :', float(multi.bbox_covered90.mean()))\n"
        "print('pixel recall90:', float(multi.pixel_covered90.mean()))\n"
    ))

    c.append(md("## 14. Proposal any-hit precision (DESCRIPTIVE ONLY)\n"))
    c.append(code(
        "p = AUDIT['proposal_any_hit_precision']\n"
        "print('proposal_bbox_any_hit_precision :', p['proposal_bbox_any_hit_precision'])\n"
        "print('proposal_pixel_any_hit_precision:', p['proposal_pixel_any_hit_precision'])\n"
        "print('role:', p['role'])\n"
    ))

    c.append(md("## 15. Bbox-vs-pixel disagreement analysis\n"))
    c.append(code(
        "d = AUDIT['bbox_pixel_disagreement']\n"
        "print('covered90 disagreements :', d['covered90_disagreements'])\n"
        "print('covered50 disagreements :', d['covered50_disagreements'])\n"
        "print('any-overlap disagreements:', d['any_overlap_disagreements'])\n"
        "print('mean bbox - pixel       :', d['mean_bbox_minus_pixel'])\n"
        "print('by stratum              :', d['by_stratum_mean'])\n"
    ))

    c.append(md("## 16. Uncovered-component inventory\n"))
    c.append(code(
        "unc = pd.read_csv(TABLES / 'phase13_part1c_uncovered_components.csv')\n"
        "print('uncovered (bbox_covered90 == False):', len(unc), '/', len(comp))\n"
        "print(unc.size_stratum.value_counts().to_dict())\n"
        "print(unc.head(15).to_string(index=False))\n"
    ))

    c.append(md("## 17. Historical v2 provenance-only context\n"))
    c.append(code(
        "ctx = pd.read_csv(TABLES / 'phase13_part1c_historical_context.csv')\n"
        "print(ctx.to_string(index=False))\n"
        "print()\n"
        "print('LABEL:', ctx['comparison_label'].iloc[0])\n"
        "print('No improvement/regression/significance/paired-delta claim is made.')\n"
    ))

    c.append(md(
        "## 18. 16-case deterministic proposal gallery\n"
        "\n"
        "Selection is SHA256(sample_id)-ordered, fixed **before** any outcome was read.\n"
        "Label: `DETERMINISTIC_PREDICTION_INDEPENDENT_GALLERY_ONLY`.\n"
        "\n"
        "**GT USED FOR REVIEW / EVALUATION ONLY — NOT FOR PROPOSAL GENERATION.**\n"
    ))
    c.append(code(
        "gallery = pd.read_csv(TABLES / 'phase13_part1c_gallery_selection.csv')\n"
        "print('gallery cases:', len(gallery), '/ 16')\n"
        "print(gallery.to_string(index=False))\n"
        "assert len(gallery) == 16\n"
    ))

    c.append(md("## 19. Limitations\n"))
    c.append(md(
        "- Proposal precision metrics are **descriptive only** (no IoU acceptance threshold).\n"
        "- Pixel-mask coverage is **secondary sensitivity**, never a selection metric.\n"
        "- The v2/v3 historical comparison spans **different populations**; no delta is claimed.\n"
        "- Exactly **one** authorized inference pass was performed; no tuning followed.\n"
        "- The gallery is prediction-independent and does not influence any metric.\n"
    ))

    c.append(md(
        "## 20. Explicit stop boundary\n"
        "\n"
        "**STOP.** No regional segmentation, no GLOBAL/ORACLE/PREDICTED comparison,\n"
        "no gate decision (`NOT_DECIDED`), no Phase 14. TEST not read.\n"
    ))
    c.append(code(
        "print('regional segmentation :', AUDIT['regional_segmentation'])\n"
        "print('gate decision         :', AUDIT['gate_decision'])\n"
        "print('training              :', AUDIT['training'])\n"
        "print('optimizer             :', AUDIT['optimizer'])\n"
        "print('grid configs          :', AUDIT['grid_configs'])\n"
        "print('TEST reads            :', AUDIT['test_reads'])\n"
        "print('next_action = WAIT_FOR_SUPERVISOR_PHASE13_PART1D_PREDICTED_REGION_SEGMENTATION_AUTHORIZATION')\n"
    ))

    c.append(md("## 21. Artifact SHA registry\n"))
    c.append(code(
        "reg = pd.read_csv(TABLES / 'phase13_part1b_training_artifact_registry.csv')\n"
        "print('registry rows:', len(reg), '| missing:', int((reg['exists'] != True).sum()))\n"
        "part1c = sorted(TABLES.glob('phase13_part1c_*.csv'))\n"
        "for f in part1c:\n"
        "    print(f'{sha(f)[:24]}  {f.name}')\n"
    ))
    return c


def main() -> int:
    import nbformat
    from nbclient import NotebookClient

    FIG.mkdir(parents=True, exist_ok=True)
    NB.parent.mkdir(parents=True, exist_ok=True)
    nb = nbformat.from_dict({
        "cells": build_cells(),
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4, "nbformat_minor": 5,
    })
    nbformat.write(nb, NB)
    NotebookClient(nb, timeout=600, kernel_name="python3",
                   resources={"metadata": {"path": str(ROOT)}}).execute()
    nbformat.write(nb, NB)

    cells = [x for x in nb.cells if x.cell_type == "code"]
    unexec = [i for i, x in enumerate(cells) if x.get("execution_count") is None]
    errs = [i for i, x in enumerate(cells)
            if any(o.get("output_type") == "error" for o in x.get("outputs", []))]
    print("notebook :", NB)
    print("cells    :", len(nb.cells), "| code:", len(cells))
    print("unexecuted:", len(unexec), "| errors:", len(errs))
    return 0 if not unexec and not errs else 1


if __name__ == "__main__":
    raise SystemExit(main())
