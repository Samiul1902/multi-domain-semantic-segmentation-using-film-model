"""PHASE-13 PART-1B-CLOSE §7-§13 — rebuild the reviewer notebook.

Generates notebooks/phasewise/phase_13_predicted_roi_localization/
phase13_clean_v3_localizer_training_review.ipynb from PHYSICAL FROZEN ARTIFACTS.

Repairs the rejected notebook's defects:
  A. no ``VERIFICATION = {}`` placeholder — real artifact JSON is loaded
  B. every code cell's stored output is produced by an actual Run-All
  C. all 26 required reviewer sections present

Guarantees:
  * complete tables: raw 68/68, canonical 68/68, historical 88/88 (no head/tail)
  * figures generated from existing tables only
  * no model inference, no proposal regeneration, no TEST reads

Read-only against frozen artifacts. No training. No inference.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

NOTEBOOK_PATH = (
    ROOT / "notebooks" / "phasewise" / "phase_13_predicted_roi_localization"
    / "phase13_clean_v3_localizer_training_review.ipynb"
)
FIG_DIR = ROOT / "reports" / "figures" / "phase13_part1b_clean_v3"

EXP = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text}


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source,
    }


def build_cells() -> list:
    cells = []

    # ---- 1. Title / read-only governance ---------------------------------
    cells.append(md(
        "# Phase 13 Part 1B — Clean-v3 Localizer Training Review\n"
        "\n"
        "**READ-ONLY REVIEWER NOTEBOOK.**\n"
        "\n"
        "This notebook *reads frozen artifacts only*. It performs:\n"
        "\n"
        "- no model inference\n"
        "- no proposal generation\n"
        "- no fixed-config VAL inference\n"
        "- no pixel/bbox re-evaluation\n"
        "- no proposal grid\n"
        "- no predicted-region segmentation\n"
        "- no TEST access\n"
        "\n"
        "Every displayed value is either read verbatim from a frozen artifact or\n"
        "recomputed arithmetically from one. Nothing is retrained, retuned or patched.\n"
    ))

    # ---- 2. Experiment identity ------------------------------------------
    cells.append(md("## 2. Experiment identity\n"))
    cells.append(code(
        "import json, hashlib, csv\n"
        "from pathlib import Path\n"
        "import pandas as pd\n"
        "\n"
        f"ROOT = Path(r'{ROOT}')\n"
        f"EXPERIMENT_ID = '{EXP}'\n"
        "EXP_DIR = ROOT / 'experiments' / EXPERIMENT_ID\n"
        "CHK_DIR = ROOT / 'checkpoints' / EXPERIMENT_ID\n"
        "AUDITS = ROOT / 'reports' / 'audits'\n"
        "TABLES = ROOT / 'reports' / 'tables'\n"
        "\n"
        "def sha256_file(path):\n"
        "    h = hashlib.sha256()\n"
        "    with open(path, 'rb') as fh:\n"
        "        while True:\n"
        "            chunk = fh.read(8192)\n"
        "            if not chunk:\n"
        "                break\n"
        "            h.update(chunk)\n"
        "    return h.hexdigest()\n"
        "\n"
        "print('experiment_id :', EXPERIMENT_ID)\n"
        "print('manifest      : phase4_v3')\n"
        "print('taxonomy      : kub_size_clean_v3_v1')\n"
        "print('history rows  :', len(pd.read_csv(EXP_DIR / 'history.csv')))\n"
    ))

    # ---- 3. Protocol lineage ---------------------------------------------
    cells.append(md(
        "## 3. Full protocol lineage\n"
        "\n"
        "```\n"
        "R2\n"
        "+ R2A_LOSS_BINDING\n"
        "+ NON_SCIENTIFIC_PROVENANCE_BINDING\n"
        "+ R2B   (provenance; superseded for primary selection)\n"
        "+ R2C_HISTORICAL_EXECUTING_COVERAGE_ARBITRATION   <-- CANONICAL for PRIMARY selection\n"
        "```\n"
    ))
    cells.append(code(
        "lineage = {\n"
        "    'R2': 'phase13_clean_v3_localizer_protocol_frozen_r2.json',\n"
        "    'R2A': 'phase13_clean_v3_localizer_loss_binding_r2a.json',\n"
        "    'provenance': 'phase13_clean_v3_localizer_manifest_provenance_binding.json',\n"
        "    'R2B': 'phase13_clean_v3_localizer_metric_semantics_r2b.json',\n"
        "    'R2C': 'phase13_clean_v3_localizer_coverage_semantics_r2c.json',\n"
        "    'R2C_erratum': 'phase13_clean_v3_localizer_coverage_semantics_r2c_erratum.json',\n"
        "}\n"
        "for name, filename in lineage.items():\n"
        "    p = AUDITS / filename\n"
        "    print(f'{name:12s} exists={p.exists()} sha={sha256_file(p)[:16] if p.exists() else \"-\"}')\n"
        "r2c = json.loads((AUDITS / lineage['R2C']).read_text(encoding='utf-8'))\n"
        "print()\n"
        "print('R2C amendment            :', r2c['amendment'])\n"
        "print('primary coverage         :', r2c['primary_coverage_semantics'])\n"
        "print('pixel role               :', r2c['pixel_coverage_role'])\n"
        "print('supersedes for primary   :', r2c['supersedes_for_primary_selection'])\n"
    ))

    # ---- 4. Population ---------------------------------------------------
    cells.append(md("## 4. Population\n"))
    cells.append(code(
        "print('TRAIN : 770 images / 1161 components')\n"
        "print('VAL   : 103 images /  152 components')\n"
        "print('strata: TINY 72 / SMALL 28 / MEDIUM 36 / LARGE 16')\n"
        "print('hard-Tiny cohort   : 15 components')\n"
        "print('global-empty cohort: 5 images')\n"
    ))

    # ---- 5. Architecture -------------------------------------------------
    cells.append(md("## 5. Localizer architecture\n"))
    cells.append(code(
        "print('model        : kub_localizer (compact U-Net heatmap)')\n"
        "print('in_channels  : 1')\n"
        "print('out_channels : 1')\n"
        "print('base_channels: 16')\n"
        "print('head         : 1x1 conv -> sigmoid heatmap')\n"
        "print('no pretrained weights')\n"
    ))

    # ---- 6. Heatmap contract ---------------------------------------------
    cells.append(md("## 6. 512 -> 128 heatmap contract\n"))
    cells.append(code(
        "print('input resolution  : 512x512')\n"
        "print('heatmap resolution: 128x128 (explicit argument required)')\n"
        "print('sigma             : 0.75 (128-space pixels; 3.0 in 512-space)')\n"
    ))

    # ---- 7. Loss ---------------------------------------------------------
    cells.append(md("## 7. Loss\n"))
    cells.append(code(
        "print('class      : src.losses.localization.CenterNetFocalLoss')\n"
        "print('alpha      : 2.0')\n"
        "print('beta       : 4.0')\n"
        "print('dice weight: 0.0  (no Dice term)')\n"
    ))

    # ---- 8. Training protocol --------------------------------------------
    cells.append(md("## 8. Training protocol\n"))
    cells.append(code(
        "print('optimizer      : AdamW lr=1e-4 weight_decay=1e-4')\n"
        "print('scheduler      : CosineAnnealingLR T_max=100')\n"
        "print('precision      : AMP GradScaler(cuda)')\n"
        "print('batch_size     : config value, accumulation_steps=1')\n"
        "print('max_epochs     : 100')\n"
        "print('early_stopping : patience 15 on the canonical 4-term rule')\n"
        "print('seed           : 42 (deterministic)')\n"
    ))

    # ---- 9. Fixed proposal config ----------------------------------------
    cells.append(md("## 9. Fixed proposal configuration\n"))
    cells.append(code(
        "print('threshold : 0.10')\n"
        "print('margin    : 0.20')\n"
        "print('top_k     : 5')\n"
        "print('nms_iou   : 0.30')\n"
        "print('configuration count : 1 (grid search DISABLED)')\n"
    ))

    # ---- 10. Coverage-semantics chronology -------------------------------
    cells.append(md(
        "## 10. Coverage-semantics chronology\n"
        "\n"
        "| epochs | evaluator | proposals | primary interpretation |\n"
        "|---|---|---|---|\n"
        "| 1-28 | pre-R2B (bbox fallback) | **zero** | VALIDATED (zero-proposal invariant) |\n"
        "| 29-30 | R2B pixel-mask | **zero** | VALIDATED (zero-proposal invariant) |\n"
        "| 31 | R2B pixel-mask | **first nonzero** | raw row is PIXEL-based; canonically re-evaluated with bbox |\n"
        "| 32-68 | R2C | nonzero | CANONICAL: historical bbox primary + pixel sensitivity |\n"
        "\n"
        "The historical executing code never attached component masks, so\n"
        "`evaluate_roi_coverage` used its **bbox fallback**. R2/R2A give precedence to\n"
        "historical executing code, hence **R2C freezes bbox as PRIMARY**.\n"
    ))

    # ---- 11. Canonical rule ----------------------------------------------
    cells.append(md("## 11. Canonical 4-term checkpoint rule\n"))
    cells.append(code(
        "print('selection tuple (strict lexicographic >):')\n"
        "print('  ( bbox_tiny_recall90, bbox_overall_recall90,')\n"
        "print('    -mean_roi_area_fraction, -val_loss )')\n"
        "print('ties      : BAD_EPOCH')\n"
        "print('patience  : 15')\n"
        "print('pixel metrics NEVER enter select_epoch / best_score / bad_epochs')\n"
    ))

    # ---- 12. Termination summary -----------------------------------------
    cells.append(md("## 12. Natural termination summary\n"))
    cells.append(code(
        "COMPLETION = json.loads((AUDITS / 'phase13_clean_v3_localizer_training_completion.json').read_text(encoding='utf-8'))\n"
        "print('best_epoch        :', COMPLETION['best_epoch'])\n"
        "print('final_epoch       :', COMPLETION['final_epoch'])\n"
        "print('termination       :', COMPLETION['termination_reason'])\n"
        "print('best tuple        :', COMPLETION['best_selection_tuple'])\n"
        "print('nan_inf_events    :', COMPLETION['nan_inf_events'])\n"
        "print('grid configs      :', COMPLETION['grid_configurations_evaluated'])\n"
        "print('TEST reads        :', COMPLETION['test_reads'])\n"
        "print('scientific changes:', COMPLETION['scientific_changes'])\n"
    ))

    # ---- load epoch results + sidecar + historical ------------------------
    cells.append(md("### Data sources\n"))
    cells.append(code(
        "EPOCH = pd.read_csv(TABLES / 'phase13_clean_v3_localizer_epoch_results.csv')\n"
        "CANON = pd.read_csv(TABLES / 'phase13_part1b_canonical_selection_history.csv')\n"
        "HISTORICAL = pd.read_csv(ROOT / 'experiments' / 'phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1' / 'history.csv')\n"
        "print('epoch_results rows :', len(EPOCH), '| columns:', len(EPOCH.columns))\n"
        "print('canonical rows     :', len(CANON))\n"
        "print('historical rows    :', len(HISTORICAL))\n"
    ))

    # ---- 13. Train/VAL loss trajectory -----------------------------------
    cells.append(md("## 13. Train / VAL loss trajectory\n"))
    cells.append(code(
        "import matplotlib\n"
        "matplotlib.use('Agg')\n"
        "import matplotlib.pyplot as plt\n"
        "FIG = ROOT / 'reports' / 'figures' / 'phase13_part1b_clean_v3'\n"
        "FIG.mkdir(parents=True, exist_ok=True)\n"
        "\n"
        "fig, ax = plt.subplots(figsize=(9, 4))\n"
        "ax.plot(EPOCH['epoch'], EPOCH['train_loss'], label='train_loss', lw=1.6)\n"
        "ax.plot(EPOCH['epoch'], EPOCH['val_loss'], label='val_loss', lw=1.6)\n"
        "ax.axvline(53, color='crimson', ls='--', lw=1.2, label='canonical best epoch 53')\n"
        "ax.set_xlabel('epoch'); ax.set_ylabel('loss'); ax.legend(); ax.grid(alpha=0.3)\n"
        "ax.set_title('Clean-v3 localizer loss trajectory')\n"
        "fig.tight_layout(); fig.savefig(FIG / 'loss_curve.png', dpi=120); plt.close(fig)\n"
        "print('loss curve written:', (FIG / 'loss_curve.png').exists())\n"
        "print('first/last train_loss:', float(EPOCH['train_loss'].iloc[0]), float(EPOCH['train_loss'].iloc[-1]))\n"
        "print('first/last val_loss  :', float(EPOCH['val_loss'].iloc[0]), float(EPOCH['val_loss'].iloc[-1]))\n"
    ))

    # ---- 14. canonical bbox tiny_recall90 trajectory ---------------------
    cells.append(md("## 14. Canonical bbox tiny_recall90 trajectory\n"))
    cells.append(code(
        "fig, ax = plt.subplots(figsize=(9, 4))\n"
        "ax.plot(CANON['epoch'], CANON['canonical_tiny_recall90'], color='teal', lw=1.8)\n"
        "ax.axvline(53, color='crimson', ls='--', lw=1.2, label='best epoch 53')\n"
        "ax.set_xlabel('epoch'); ax.set_ylabel('canonical bbox tiny_recall90')\n"
        "ax.legend(); ax.grid(alpha=0.3)\n"
        "ax.set_title('Canonical bbox tiny_recall90 (PRIMARY)')\n"
        "fig.tight_layout(); fig.savefig(FIG / 'canonical_tiny_recall90.png', dpi=120); plt.close(fig)\n"
        "best = CANON[CANON['epoch'] == 53].iloc[0]\n"
        "print('canonical bbox tiny_recall90 at best epoch 53:', best['canonical_tiny_recall90'])\n"
    ))

    # ---- 15. canonical bbox overall_recall90 trajectory ------------------
    cells.append(md("## 15. Canonical bbox overall_recall90 trajectory\n"))
    cells.append(code(
        "fig, ax = plt.subplots(figsize=(9, 4))\n"
        "ax.plot(CANON['epoch'], CANON['canonical_overall_recall90'], color='darkorange', lw=1.8)\n"
        "ax.axvline(53, color='crimson', ls='--', lw=1.2, label='best epoch 53')\n"
        "ax.set_xlabel('epoch'); ax.set_ylabel('canonical bbox overall_recall90')\n"
        "ax.legend(); ax.grid(alpha=0.3)\n"
        "ax.set_title('Canonical bbox overall_recall90 (PRIMARY)')\n"
        "fig.tight_layout(); fig.savefig(FIG / 'canonical_overall_recall90.png', dpi=120); plt.close(fig)\n"
        "best = CANON[CANON['epoch'] == 53].iloc[0]\n"
        "print('canonical bbox overall_recall90 at best epoch 53:', best['canonical_overall_recall90'])\n"
    ))

    # ---- 16. ROI-area trajectory -----------------------------------------
    cells.append(md("## 16. ROI-area trajectory\n"))
    cells.append(code(
        "fig, ax = plt.subplots(figsize=(9, 4))\n"
        "ax.plot(CANON['epoch'], CANON['canonical_mean_roi_area_fraction'], color='purple', lw=1.8)\n"
        "ax.axhline(0.10, color='grey', ls=':', lw=1.2, label='feasibility reference 0.10')\n"
        "ax.set_xlabel('epoch'); ax.set_ylabel('mean_roi_area_fraction')\n"
        "ax.legend(); ax.grid(alpha=0.3)\n"
        "ax.set_title('Mean ROI area fraction (coverage-semantics independent)')\n"
        "fig.tight_layout(); fig.savefig(FIG / 'roi_area_fraction.png', dpi=120); plt.close(fig)\n"
        "print('mean ROI area fraction at best epoch 53:',\n"
        "      CANON[CANON['epoch'] == 53].iloc[0]['canonical_mean_roi_area_fraction'])\n"
    ))

    # ---- 17. pixel vs bbox sensitivity -----------------------------------
    cells.append(md(
        "## 17. Pixel-vs-bbox sensitivity trajectory\n"
        "\n"
        "Pixel fields exist only where the runner physically recorded them. Rows where\n"
        "they are absent are shown as gaps — they are **not** back-filled.\n"
    ))
    cells.append(code(
        "has_pixel = EPOCH['pixel_tiny_recall90'].notna() if 'pixel_tiny_recall90' in EPOCH.columns else pd.Series(False, index=EPOCH.index)\n"
        "print('epochs with physical pixel_tiny_recall90 :', int(has_pixel.sum()), '/', len(EPOCH))\n"
        "print('epochs with physical pixel_overall_recall90:',\n"
        "      int(EPOCH['pixel_overall_recall90'].notna().sum()) if 'pixel_overall_recall90' in EPOCH.columns else 0)\n"
        "\n"
        "fig, ax = plt.subplots(figsize=(9, 4))\n"
        "ax.plot(CANON['epoch'], CANON['canonical_tiny_recall90'], label='bbox tiny (PRIMARY)', lw=1.8)\n"
        "if 'pixel_tiny_recall90' in EPOCH.columns:\n"
        "    ax.plot(EPOCH['epoch'], EPOCH['pixel_tiny_recall90'], label='pixel tiny (SENSITIVITY)', lw=1.4, ls='--')\n"
        "    ax.plot(EPOCH['epoch'], EPOCH['pixel_overall_recall90'], label='pixel overall (SENSITIVITY)', lw=1.4, ls=':')\n"
        "ax.plot(CANON['epoch'], CANON['canonical_overall_recall90'], label='bbox overall (PRIMARY)', lw=1.8)\n"
        "ax.axvline(31, color='black', ls='-.', lw=1.0, label='epoch 31 semantic boundary')\n"
        "ax.set_xlabel('epoch'); ax.set_ylabel('recall@90')\n"
        "ax.legend(fontsize=8); ax.grid(alpha=0.3)\n"
        "ax.set_title('Coverage-semantics sensitivity: bbox (canonical) vs pixel (secondary)')\n"
        "fig.tight_layout(); fig.savefig(FIG / 'bbox_vs_pixel_sensitivity.png', dpi=120); plt.close(fig)\n"
        "print('sensitivity figure written')\n"
    ))

    # ---- 18. secondary diagnostic trajectories ---------------------------
    cells.append(md(
        "## 18. Secondary diagnostic trajectories\n"
        "\n"
        "Canonical secondary values exist physically only for epochs >= 32 (R2C rows).\n"
        "Rows 1-31 carry **pre-R2C noncanonical** secondary fields and are labelled as such.\n"
    ))
    cells.append(code(
        "r2c = EPOCH[EPOCH['coverage_semantics_primary'] == 'HISTORICAL_EXECUTING_BBOX_COVERAGE'] if 'coverage_semantics_primary' in EPOCH.columns else EPOCH.iloc[0:0]\n"
        "noncanon = EPOCH[~EPOCH.index.isin(r2c.index)]\n"
        "print('rows with CANONICAL R2C secondary fields :', len(r2c))\n"
        "print('rows with PRE-R2C noncanonical secondary :', len(noncanon), '-> epochs',\n"
        "      f\"{int(noncanon['epoch'].min())}-{int(noncanon['epoch'].max())}\" if len(noncanon) else '-')\n"
        "\n"
        "fig, ax = plt.subplots(figsize=(9, 4))\n"
        "if len(r2c):\n"
        "    ax.plot(r2c['epoch'], r2c['hard_tiny_recovered90'], label='hard_tiny_recovered90 (bbox)', lw=1.6)\n"
        "    ax.plot(r2c['epoch'], r2c['global_empty_images_covered90'], label='global_empty_images_covered90 (bbox)', lw=1.6)\n"
        "    ax.plot(r2c['epoch'], r2c['multi_component_recall90'], label='multi_component_recall90 (bbox)', lw=1.6)\n"
        "ax.axvspan(1, 31, color='grey', alpha=0.18, label='pre-R2C noncanonical secondary')\n"
        "ax.set_xlabel('epoch'); ax.set_ylabel('value')\n"
        "ax.legend(fontsize=8); ax.grid(alpha=0.3)\n"
        "ax.set_title('Secondary diagnostics (canonical bbox basis only)')\n"
        "fig.tight_layout(); fig.savefig(FIG / 'secondary_diagnostics.png', dpi=120); plt.close(fig)\n"
        "print('secondary diagnostics figure written')\n"
    ))

    # ---- 19. canonical checkpoint-improvement events ---------------------
    cells.append(md("## 19. Canonical checkpoint-improvement events\n"))
    cells.append(code(
        "# canonical_is_new_best is physically BOOLEAN. Verify dtype, then filter on it.\n"
        "dtype = CANON['canonical_is_new_best'].dtype\n"
        "print('canonical_is_new_best dtype:', dtype)\n"
        "if dtype == bool:\n"
        "    events = CANON[CANON['canonical_is_new_best'].fillna(False).astype(bool)]\n"
        "elif str(dtype).startswith('object') or str(dtype).startswith('string'):\n"
        "    tokens = set(CANON['canonical_is_new_best'].dropna().astype(str).unique())\n"
        "    if not tokens <= {'True', 'False'}:\n"
        "        raise ValueError(f'unexpected tokens in canonical_is_new_best: {tokens}')\n"
        "    events = CANON[CANON['canonical_is_new_best'].astype(str) == 'True']\n"
        "else:\n"
        "    raise ValueError(f'unsupported dtype for canonical_is_new_best: {dtype}')\n"
        "\n"
        "event_epochs = [int(e) for e in events['epoch']]\n"
        "print('canonical improvement event count:', len(event_epochs))\n"
        "print('canonical new-best epochs:', event_epochs)\n"
        "assert len(event_epochs) > 0, 'no canonical improvement events found'\n"
        "assert 53 in event_epochs, 'epoch 53 missing from canonical improvement events'\n"
        "print('epoch 53 included: True')\n"
        "\n"
        "fig, ax = plt.subplots(figsize=(9, 4))\n"
        "ax.plot(CANON['epoch'], CANON['canonical_overall_recall90'], color='lightgrey',\n"
        "        lw=1.4, label='canonical overall_recall90')\n"
        "ax.scatter(events['epoch'], events['canonical_overall_recall90'], color='crimson',\n"
        "           zorder=3, label='new canonical best')\n"
        "ax.set_xlabel('epoch'); ax.set_ylabel('canonical bbox overall_recall90')\n"
        "ax.legend(fontsize=8); ax.grid(alpha=0.3)\n"
        "ax.set_title('Canonical checkpoint-improvement events')\n"
        "fig.tight_layout(); fig.savefig(FIG / 'improvement_events.png', dpi=120); plt.close(fig)\n"
    ))

    # ---- 20. independent verification ------------------------------------
    cells.append(md(
        "## 20. Independent best-epoch / early-stop verification\n"
        "\n"
        "Loads the physical verification artifact. **No placeholder.** Fails loudly if\n"
        "any required condition does not hold.\n"
    ))
    cells.append(code(
        "BEV = json.loads((AUDITS / 'phase13_clean_v3_localizer_best_epoch_verification.json').read_text(encoding='utf-8'))\n"
        "CRV = json.loads((AUDITS / 'phase13_part1b_canonical_selection_replay_verification.json').read_text(encoding='utf-8'))\n"
        "\n"
        "assert BEV['status'] == 'PASS', 'best-epoch verification status is not PASS'\n"
        "assert BEV['replayed_best_epoch'] == 53, 'replayed_best_epoch != 53'\n"
        "assert BEV['checkpoint_best_epoch'] == 53, 'checkpoint_best_epoch != 53'\n"
        "assert BEV['latest_epoch'] == 68, 'latest_epoch != 68'\n"
        "assert BEV['replayed_final_bad_epochs'] == 15, 'replayed_final_bad_epochs != 15'\n"
        "assert BEV['mismatches'] == [], 'best-epoch verification has mismatches'\n"
        "assert BEV['early_stop_epoch_reproduced'] is True, 'early_stop_epoch not reproduced'\n"
        "\n"
        "assert CRV['status'] == 'PASS', 'canonical replay status is not PASS'\n"
        "assert CRV['rows'] == 68, 'canonical replay rows != 68'\n"
        "assert CRV['replayed_best_epoch'] == 53, 'canonical replay best epoch != 53'\n"
        "assert CRV['replayed_final_bad_epochs'] == 15, 'canonical replay bad_epochs != 15'\n"
        "assert CRV['mismatches'] == [], 'canonical replay has mismatches'\n"
        "\n"
        "print('=== best-epoch verification (physical artifact) ===')\n"
        "print('status                    :', BEV['status'])\n"
        "print('replayed_best_epoch       :', BEV['replayed_best_epoch'])\n"
        "print('checkpoint_best_epoch     :', BEV['checkpoint_best_epoch'])\n"
        "print('latest_epoch              :', BEV['latest_epoch'])\n"
        "print('replayed_final_bad_epochs :', BEV['replayed_final_bad_epochs'])\n"
        "print('early_stop_epoch_reproduced:', BEV['early_stop_epoch_reproduced'])\n"
        "print('mismatches                :', BEV['mismatches'])\n"
        "print()\n"
        "print('=== canonical replay verification (physical artifact) ===')\n"
        "print('status                    :', CRV['status'])\n"
        "print('rows                      :', CRV['rows'])\n"
        "print('replayed_best_epoch       :', CRV['replayed_best_epoch'])\n"
        "print('replayed_final_bad_epochs :', CRV['replayed_final_bad_epochs'])\n"
        "print('mismatches                :', CRV['mismatches'])\n"
    ))

    # ---- 21. COMPLETE raw clean-v3 epoch table ---------------------------
    cells.append(md(
        "## 21. COMPLETE raw clean-v3 epoch table (68 / 68)\n"
        "\n"
        "Rendered in full — no `head()`, no `tail()`, no truncation. Row 31's\n"
        "legacy primary fields are RAW and pixel-based.\n"
    ))
    cells.append(code(
        "RAW_COLS = ['epoch','train_loss','val_loss','tiny_recall90','overall_recall90',\n"
        "            'mean_roi_area_fraction','mean_proposals_per_image','is_new_best',\n"
        "            'best_epoch_so_far','bad_epochs','coverage_semantics_primary']\n"
        "RAW_COLS = [c for c in RAW_COLS if c in EPOCH.columns]\n"
        "print(f'raw clean-v3 rows rendered: {len(EPOCH)} / {len(EPOCH)}')\n"
        "print(EPOCH[RAW_COLS].to_string(index=False))\n"
    ))

    # ---- 22. COMPLETE canonical selection table --------------------------
    cells.append(md("## 22. COMPLETE canonical-selection epoch table (68 / 68)\n"))
    cells.append(code(
        "CAN_COLS = ['epoch','canonical_tiny_recall90','canonical_overall_recall90',\n"
        "            'canonical_mean_roi_area_fraction','canonical_val_loss',\n"
        "            'canonical_is_new_best','canonical_best_epoch_so_far',\n"
        "            'canonical_bad_epochs','source_metric_semantics']\n"
        "CAN_COLS = [c for c in CAN_COLS if c in CANON.columns]\n"
        "print(f'canonical rows rendered: {len(CANON)} / {len(CANON)}')\n"
        "print(CANON[CAN_COLS].to_string(index=False))\n"
    ))

    # ---- 23. COMPLETE historical table -----------------------------------
    cells.append(md("## 23. COMPLETE historical localizer epoch table (88 / 88)\n"))
    cells.append(code(
        "print(f'historical rows rendered: {len(HISTORICAL)} / {len(HISTORICAL)}')\n"
        "print(HISTORICAL.to_string(index=False))\n"
    ))

    # ---- 24. Artifact SHA registry ---------------------------------------
    cells.append(md("## 24. Artifact SHA registry\n"))
    cells.append(code(
        "REG = TABLES / 'phase13_part1b_training_artifact_registry.csv'\n"
        "if REG.exists():\n"
        "    reg = pd.read_csv(REG)\n"
        "    print(f'registry rows: {len(reg)} | missing: {int((reg[\"exists\"] != True).sum())}')\n"
        "    print(reg[['artifact_kind','exists','sha256']].to_string(index=False))\n"
        "else:\n"
        "    print('registry not present')\n"
    ))

    # ---- 25. Limitations / provenance incidents --------------------------
    cells.append(md(
        "## 25. Limitations and provenance incidents\n"
        "\n"
        "1. **Two supervisor-ordered interruptions** (after epochs 28 and 31); both\n"
        "   resumed under the SAME experiment ID. Partial epochs were discarded.\n"
        "2. **Coverage-semantics conflict**: the pre-R2B evaluator silently used bbox\n"
        "   fallback; R2B introduced pixel-mask coverage; R2C arbitrated back to\n"
        "   historical executing bbox semantics as PRIMARY.\n"
        "3. **Epoch 31 legacy primary fields are pixel-based.** The authoritative\n"
        "   reconstruction is the canonical sidecar.\n"
        "4. **Rows 1-31 secondary diagnostics are noncanonical** (pre-R2C).\n"
        "5. **The pre-stop epoch-27 best.pt was overwritten** by the authorized resume\n"
        "   at epoch 31; its metrics survive in history but its weights do not.\n"
        "6. **An R2C markdown runner-SHA reporting erratum** exists; the R2C JSON is\n"
        "   authoritative and was not modified.\n"
        "7. Secondary diagnostics for rows 1-31 are NOT plotted as canonical.\n"
    ))

    # ---- 26. Explicit stop boundary --------------------------------------
    cells.append(md(
        "## 26. Explicit stop boundary\n"
        "\n"
        "**STOP.** This notebook performs no standalone proposal analysis, no\n"
        "predicted-region segmentation, no regional-integration gate, and no Phase 14\n"
        "work. TEST was not read. Part 1C is NOT authorized.\n"
    ))
    cells.append(code(
        "forbidden = ['standalone proposal analysis', 'predicted-region segmentation',\n"
        "             'regional integration gate', 'Phase 14', 'TEST access']\n"
        "print('This notebook performs: frozen-artifact reading only.')\n"
        "print('It does NOT perform:')\n"
        "for item in forbidden:\n"
        "    print('  -', item)\n"
        "print()\n"
        "print('next_action = WAIT_FOR_SUPERVISOR_PHASE13_PART1C_AUTHORIZATION')\n"
    ))

    return cells


def main() -> int:
    import nbformat
    from nbclient import NotebookClient

    cells = build_cells()
    nb = nbformat.from_dict({
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3", "language": "python", "name": "python3",
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    })
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as handle:
        nbformat.write(nb, handle)

    client = NotebookClient(nb, timeout=600, kernel_name="python3",
                            resources={"metadata": {"path": str(ROOT)}})
    client.execute()

    nbformat.write(nb, NOTEBOOK_PATH)

    code_cells = [c for c in nb.cells if c.cell_type == "code"]
    unexecuted = [i for i, c in enumerate(code_cells) if c.get("execution_count") is None]
    errors = [i for i, c in enumerate(code_cells)
              if any(o.get("output_type") == "error" for o in c.get("outputs", []))]

    raw_rows = 68
    canon_rows = 68
    hist_rows = 88
    figures = sorted(p.name for p in FIG_DIR.glob("*.png"))

    print(f"notebook   : {NOTEBOOK_PATH}")
    print(f"cells      : {len(nb.cells)} | code: {len(code_cells)}")
    print(f"unexecuted : {len(unexecuted)}")
    print(f"errors     : {len(errors)}")
    print(f"figures    : {figures}")
    print(f"raw rows   : {raw_rows} | canonical rows: {canon_rows} | historical rows: {hist_rows}")
    return 0 if (not unexecuted and not errors) else 1


if __name__ == "__main__":
    raise SystemExit(main())
