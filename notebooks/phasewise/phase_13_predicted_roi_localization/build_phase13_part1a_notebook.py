"""Build Phase 13 Part 1A — historical localizer reconstruction + clean-v3 protocol-freeze notebook."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(r'D:\Softfors\jup')))
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

nb = new_notebook()
nb.metadata['kernelspec'] = {'display_name': 'jup-venv', 'language': 'python', 'name': 'jup-venv'}
nb.metadata['language_info'] = {'name': 'python', 'version': '3.13.12'}


def md(t):
    nb.cells.append(new_markdown_cell(t))


def co(t):
    nb.cells.append(new_code_cell(t))


md("""# Phase 13 Part 1A — Historical Localizer Reconstruction + CLEAN-v3 Protocol Freeze

**Date:** 2026-09-21
**Manifest:** `phase4_v3` · **Taxonomy:** `kub_size_clean_v3_v1`
**Strategy revision:** SR-1 (Regional-Aware Multi-Domain FiLM) · final system `RA-MedFiLM-Seg++` (`PROPOSED_NOT_IMPLEMENTED`)

---

> **PROTOCOL / DEFINITION PHASE ONLY.** Part 1A reconstructs the historical Phase-13 /
> Phase-13B localizer protocol and prepares a **prospective** clean-v3 localizer + proposal
> protocol candidate.
>
> **No localizer training. No localizer inference. No proposal generation.**
> No checkpoint/history/config/manifest changes. No TEST access. Phase 14 not executed.
> Phases 14–18 not started. RA-MedFiLM not implemented. No winner or single reference
> architecture selected. `REGIONAL_INTEGRATION_GATE_AFTER_PHASE13` remains **NOT_DECIDED**.
>
> **Primary scientific question (Phase 13):** *can a GT-free region proposal / localization
> mechanism retain enough of the Phase-12 oracle regional-resolution benefit while
> controlling FP burden and preserving global segmentation quality?*
""")

md("""## 1. Scope and Governance

| Rule | Status |
|---|---|
| Localizer training epochs / optimizer steps | **0 / 0** |
| Localizer inference passes | **0** |
| Proposals generated on real images | **0** |
| Checkpoint / history / config / manifest changes | **0** |
| TEST image/mask/content reads | **0** |
| Phase 14 executed | **NO** |
| Phases 15–18 | **NOT STARTED** |
| RA-MedFiLM implementation | **0** |
| Winner / single reference architecture | **NONE** |
| `REGIONAL_INTEGRATION_GATE_AFTER_PHASE13` | **NOT_DECIDED** |
""")

co("""import sys, json
from pathlib import Path
import pandas as pd
pd.set_option('display.max_rows', None); pd.set_option('display.max_columns', None)
pd.set_option('display.width', None); pd.set_option('display.max_colwidth', 80)

PROJECT_ROOT = Path(r'D:\\Softfors\\jup')
CODE_DIR = PROJECT_ROOT / 'notebooks/phasewise/phase_13_predicted_roi_localization/code'
for p in (str(PROJECT_ROOT), str(CODE_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import phase13_localizer_protocol as p13
TABLES = PROJECT_ROOT / 'reports/tables'
AUDITS = PROJECT_ROOT / 'reports/audits'

# Read-only: regenerate the tables from the frozen artifacts so the notebook and the
# module provably produce identical output. Nothing is trained, inferred or generated.
hashes = p13.write_all(write_audits=True)
print(f'wrote {len(hashes)} artifacts')
print(f'TEST content reads: 0  |  training: 0  |  inference: 0  |  proposals: 0')
""")

md("""## 2. Historical Population (phase4_v2)

The historical Phase-13 / Phase-13B localizer study ran under **`phase4_v2`**, not clean-v3.
This is the single most important reconstruction fact: the frozen Stage-4D numbers
(Tiny 53/73, overall 100/156) belong to the **historical** population and must not be
compared with clean-v3 numbers as if the splits matched.
""")

co("""hist_pop = pd.DataFrame([
    {'split': 'TRAIN', 'acquisition': 'FULL_FIELD', 'images': 771, 'components': 1162},
    {'split': 'VAL', 'acquisition': 'FULL_FIELD', 'images': 106, 'components': 156},
    {'split': 'VAL', 'acquisition': 'ROI_CROP', 'images': 177, 'components': 333 - 156},
])
display(hist_pop)
print('historical VAL FULL_FIELD size strata (kub_size_v1):', p13.VAL_STRATA_HIST)
print('historical manifest:', p13.MANIFEST_HIST, '| taxonomy:', p13.TAXONOMY_HIST)
""")

md("""## 3. Historical Source Inventory

Reconstructed with the source-precedence ladder: executing source (rank 1) > persisted
audit/table (rank 2) > executed notebook (rank 3) > frozen protocol/README (rank 4) >
prose. Downstream Phase-14 audits are included at rank 2 as **evidence of the historical
train/inference relationship**, not as a Phase-13 source of truth.
""")

co("""src_inv = pd.read_csv(TABLES / 'phase13_historical_source_inventory.csv')
display(src_inv[['source_path', 'source_type', 'authority_rank', 'notes']])
print('MISSING sources:', src_inv[src_inv['notes'] != 'present']['source_path'].tolist() or 'none')
""")

md("""## 4. Historical Stage Inventory

Phase 13 developed through eight recorded stages, including three failed / corrected
iterations. The final Stage-4D-R2 is the authoritative localizer.
""")

co("""stages = pd.read_csv(TABLES / 'phase13_historical_stage_inventory.csv')
display(stages[['stage_id', 'stage_name', 'experiment_id', 'status']])
display(stages[['stage_id', 'outcome_summary']])
""")

md("""## 5. Historical Localizer Protocol Matrix

Every concept reconstructed from the executing source or a persisted artifact. Note the
selection rule: Phase 13 is **localization-only** — segmentation Dice is deliberately
never a localizer selection or reporting target.
""")

co("""proto = pd.read_csv(TABLES / 'phase13_historical_localizer_protocol_matrix.csv')
display(proto[['concept', 'historical_value', 'unit', 'status']])
print('status counts:', proto['status'].value_counts().to_dict())
""")

md("""## 6. Historical Checkpoint Provenance + Handoff-Claim Verification

All nine claims in the Phase-13 handoff note are re-verified directly against the frozen
Stage-4D evaluation artifact and the on-disk checkpoint bytes.
""")

co("""ckpt = pd.read_csv(TABLES / 'phase13_historical_checkpoint_provenance.csv')
display(ckpt[['experiment_id', 'role', 'sha256', 'sha256_matches_claim', 'best_epoch', 'status']])

handoff = pd.read_csv(TABLES / 'phase13_historical_handoff_verification.csv')
display(handoff)
assert (handoff['verdict'] == 'VERIFIED').all(), 'handoff claim mismatch'
print('ALL HANDOFF CLAIMS VERIFIED')
""")

md("""## 7. Findings

### 7.1 `HISTORICAL_TRAIN_INFERENCE_PROPOSAL_DISTRIBUTION_MISMATCH` — **VERIFIED**

The historical Phase-14 regional refiner was **trained** on GT-derived base crops plus
GT-perturbed crops plus random background negatives (Option A3: 1162 + 2324 + 1542 = 5028
crops/epoch), but **evaluated** on frozen Stage-4D **predicted** proposals (Condition C).

The Phase-14 Step-3 failure (`D_p = 0.383905` vs `D_g = 0.652776`, driven by 5.43 FP
components/image vs 0.37 baseline) is therefore at least partly attributable to this
distribution gap and is **not** a clean measurement of predicted-proposal regional
refinement.
""")

co("""rec = json.loads((AUDITS / 'phase13_historical_localizer_protocol_reconstruction.json').read_text(encoding='utf-8'))
find = rec['findings']
for k, v in find.items():
    print(f"{k}: {v['status']}")
print()
mismatch = find['HISTORICAL_TRAIN_INFERENCE_PROPOSAL_DISTRIBUTION_MISMATCH']
print('EVIDENCE:')
for e in mismatch['evidence']:
    print(' -', e)
print()
print('STATEMENT:', mismatch['statement'])
print()
print('CONSEQUENCE:', mismatch['consequence'])
print()
print('CLEAN-V3 ACTION:', mismatch['clean_v3_action'])
""")

md("""### 7.2 Latent inference defect, label ambiguity, and an artifact gap

Three further findings were recorded. The latent defect is a **verified** bug in the
historical inference helper that must be fixed (or an output-resolution contract frozen)
before any clean-v3 reuse.
""")

co("""for k in ['LATENT_INFERENCE_HEATMAP_RESOLUTION_OMISSION',
          'STAGE4D_DESIGN_AUDIT_LABEL_AMBIGUITY',
          'MISSING_VAL_SEARCH_EPOCH_079']:
    v = find[k]
    print(f"--- {k} [{v['status']}]")
    print(v['statement'])
    print('   action:', v['clean_v3_action'])
    print()

print('Phase-14 historical gate arithmetic (v2, coverage90):', p13.PHASE14_GATE)
print('Phase-14 classification:', rec['phase14_classification'])
""")

md("""## 8. Clean-v3 Population Specification

The clean-v3 FULL_FIELD population was recomputed from the manifest and a TRAIN/VAL mask
census (`mask > 0`, 8-connectivity). **TEST was never read.** The VAL component count
(152) independently reproduces the Phase-12 clean-v3 oracle population.
""")

co("""pop = pd.read_csv(TABLES / 'phase13_clean_v3_training_population_spec.csv')
display(pop)
print('census cache:', p13.POPULATION_CENSUS_CACHE.name,
      '->', p13.POPULATION_CENSUS)
""")

md("""## 9. Historical vs Clean-v3 Localizer Protocol Diff

Twenty-seven protocol fields compared. Material changes are flagged for supervisor
decision; the scientific core of the localizer (architecture, 128 output, sigma 0.75,
CenterNet focal + soft Dice, AdamW, cosine, the 20-config proposal grid, coverage 0.90)
is carried over unchanged.
""")

co("""diff = pd.read_csv(TABLES / 'phase13_v2_to_clean_v3_localizer_protocol_diff.csv')
display(diff[['field', 'historical_v2', 'proposed_clean_v3', 'same_or_changed',
              'scientifically_material', 'supervisor_decision_required']])
print('SAME:', (diff['same_or_changed'] == 'SAME').sum(),
      '| CHANGED:', (diff['same_or_changed'] == 'CHANGED').sum())
print('material changes:', diff.loc[diff['scientifically_material'], 'field'].tolist())
""")

co("""cand = pd.read_csv(TABLES / 'phase13_clean_v3_localizer_protocol_candidate.csv')
display(cand)
""")

md("""## 10. Proposal Postprocessing Contract

The 14-step postprocessing chain is carried over byte-for-byte. The one trap worth
repeating: `apply_context_margin` returns an **already expanded** `crop_geometry`, so
consumers must not expand it again.
""")

co("""post = pd.read_csv(TABLES / 'phase13_clean_v3_proposal_postprocessing_candidate.csv')
display(post[['step', 'proposed_clean_v3', 'change_reason']])
""")

md("""## 11. Proposal Metric Contract

Coverage90 is the primary localization hit definition. Two prospective additions are
flagged (`NEW`): proposal precision and unmatched proposals per image — these exist
because the historical Phase-14 failure was an FP-clutter failure that was only diagnosed
post hoc.
""")

co("""mc = pd.read_csv(TABLES / 'phase13_clean_v3_proposal_metric_contract.csv')
display(mc)
print('NEW metrics:', mc.loc[mc['historical_status'].str.startswith('NEW'), 'metric'].tolist())
print('EXCLUDED:', mc.loc[mc['role'].str.startswith('EXCLUDED'), 'metric'].tolist())
""")

md("""## 12. Downstream Integration Candidate

The Phase-13 -> Phase-14 handoff, with the distribution-mismatch fix promoted to an
explicit material change.
""")

co("""ds = pd.read_csv(TABLES / 'phase13_clean_v3_downstream_integration_candidate.csv')
display(ds[['item', 'proposed_clean_v3', 'scientifically_material', 'supervisor_decision_required']])
""")

md("""## 13. Oracle-Retention Metric Contract (dimension B arithmetic)

`T_g` (global coverage90), `T_o` (oracle coverage90), `T_p` (predicted coverage90),
`G = T_o - T_g`, `R = (T_p - T_g) / G`. The historical v2 values are shown for context
only. **None of the clean-v3 values exist yet** — Phase 13 exists to measure them. If
`G <= 0`, retention is undefined and the gate must report `NO_GO` / `REVISE` rather than
a ratio.
""")

co("""ret = pd.read_csv(TABLES / 'phase13_oracle_retention_metric_contract.csv')
display(ret[['symbol', 'name', 'status', 'notes']])
print()
print('historical v2 retention:', {k: p13.PHASE14_GATE[k] for k in ('T_g', 'T_o', 'T_p', 'G', 'R')})
print('clean-v3 retention: NOT_YET_COMPUTED (population 103/152)')
""")

md("""## 14. Gate Dimension B Candidate + C/D Bridge

Dimension B (`PRACTICAL_LOCALIZATION_RETENTION`) is the only gate dimension Phase 13 can
move. Dimensions C and D are re-examined with Phase-13 evidence; dimension A is already
`SUPPORTED_DESCRIPTIVE_EVIDENCE` from Phase 12. **No numeric threshold is frozen.**
""")

co("""gb = pd.read_csv(TABLES / 'phase13_gate_dimension_b_candidate.csv')
display(gb)

cd = pd.read_csv(TABLES / 'phase13_gate_dimensions_cd_bridge.csv')
display(cd)
""")

md("""## 15. Future Visualization Protocol

Declared **before** results exist, so the Phase-13 evidence package cannot be
retro-fitted to a convenient visual.
""")

co("""viz = pd.read_csv(TABLES / 'phase13_future_visualization_protocol.csv')
display(viz)
""")

md("""## 16. Artifact Registry

Content-addressed SHA-256 for every Part-1A artifact.
""")

co("""reg = pd.DataFrame([{'artifact': k, 'sha256': v} for k, v in sorted(hashes.items())])
display(reg)
""")

md("""## 17. Governance Summary and STOP

- TEST content reads **0**; TEST metrics **NONE**; external data **NONE**.
- Localizer training **0**; localizer inference **0**; proposals generated **0**.
- No checkpoint / history / config / manifest was modified.
- Phase 14 **not executed**; Phases 15–18 **not started**.
- No winner declared; no reference architecture selected.
- Regional mechanism **not promoted**; `REGIONAL_INTEGRATION_GATE_AFTER_PHASE13` **NOT_DECIDED**.
- Final architecture `RA-MedFiLM-Seg++` remains **`PROPOSED_NOT_IMPLEMENTED`**.

**STOP after Phase 13 Part 1A — awaiting supervisor review of the protocol candidate.**
""")

co("""print('PHASE 13 PART 1A — COMPLETE (protocol/definition only)')
print('test_reads=0  training=0  inference=0  proposals=0  phase14_executed=False')
print('gate=NOT_DECIDED  winner=none  reference_model=none  regional_mechanism_promoted=False')
""")

out = Path(r'D:\Softfors\jup\notebooks\phasewise\phase_13_predicted_roi_localization'
           r'\phase13_clean_v3_localizer_protocol_freeze.ipynb')
# Deterministic cell ids: nbformat otherwise assigns a random id per cell, which makes the
# executed notebook hash non-reproducible across rebuilds.
for i, cell in enumerate(nb.cells):
    cell['id'] = f'p13a{i:03d}'
nbf.write(nb, str(out))
print('wrote', out, '| cells:', len(nb.cells))
