"""Build Phase 12 Part 1A — historical reconstruction + clean-v3 protocol-freeze notebook."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(r'D:\Softfors\jup')))
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

nb = new_notebook()
nb.metadata['kernelspec'] = {'display_name': 'jup-venv', 'language': 'python', 'name': 'jup-venv'}
nb.metadata['language_info'] = {'name': 'python', 'version': '3.13.12'}
def md(t): nb.cells.append(new_markdown_cell(t))
def co(t): nb.cells.append(new_code_cell(t))

md("""# Phase 12 Part 1A — Historical Oracle Reconstruction + CLEAN-v3 Protocol Freeze

**Model:** Gemini 3.1 Pro High · **Date:** 2026-09-21
**Manifest:** `phase4_v3` · **Taxonomy:** `kub_size_clean_v3_v1`
**Strategy revision:** SR-1 (Regional-Aware Multi-Domain FiLM) · final system `RA-MedFiLM-Seg++` (`PROPOSED_NOT_IMPLEMENTED`)

---

> **PROTOCOL / DEFINITION PHASE ONLY.** Part 1A reconstructs the historical Phase-12 oracle
> protocol and prepares a **prospective** clean-v3 oracle protocol candidate.
>
> **No clean-v3 oracle inference is performed.** No training. No checkpoint/history/config/
> manifest changes. No TEST access. Phase 13 not started. Phases 14–18 not started.
> RA-MedFiLM not implemented. No baseline winner or single reference architecture selected.
>
> **Primary scientific question (Phase 12):** *does increasing effective local spatial
> resolution around the TRUE target provide an upper bound on how much segmentation failure
> could potentially be recovered by a regional pathway?*
""")

md("""## 2. Scope and Governance

| Rule | Status |
|---|---|
| Clean oracle inference passes | **0** |
| Training epochs / optimizer steps | **0 / 0** |
| Checkpoint / history / config / manifest changes | **0** |
| TEST image/mask/content reads | **0** |
| Phase 13 / Phases 14–18 | **NOT STARTED** |
| RA-MedFiLM implementation | **0** |
| Winner / single reference architecture | **NONE** |
| New post-hoc thresholds | **0** |

Model scope for future Part 1B: **all four** clean-v3 baselines (UNet, Attention U-Net,
UNet++, DeepLabV3+) — testing whether regional-resolution benefit is architecture-general
or architecture-specific.
""")

md("""## 3. SR-1 Regional-Mechanism Role

Under SR-1, KUB is the **regional-mechanism discovery / validation laboratory**. Phase 12
supplies evidence **for or against** incorporating a regional mechanism into future
`RA-MedFiLM-Seg++`. The regional mechanism is **not automatically promoted**.

Phase 12 + Phase 13 feed `REGIONAL_INTEGRATION_GATE_AFTER_PHASE13`
(outcomes: **GO / REVISE_LOCALIZER / NO_GO**). **Part 1A does not decide that outcome.**
""")

md("""## 4. Phase-11 Bridge Evidence (clean-v3, frozen)
""")
co("""import sys, json
from pathlib import Path
import pandas as pd
pd.set_option('display.max_rows', None); pd.set_option('display.max_columns', None)
pd.set_option('display.width', None); pd.set_option('display.max_colwidth', None)

PROJECT_ROOT = Path(r'D:\\Softfors\\jup')
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_12_oracle_roi' / 'code'))
import phase12_oracle_protocol as p

print('Phase-11 regime counts :', p.PHASE11_REGIME)
print('ALL_FOUR_LOW           :', p.PHASE11_ALL_FOUR_LOW, '/ 280')
print('hard cohort            :', p.PHASE11_HARD_COHORT)
print('top disagreement       :', p.PHASE11_TOP_DISAGREEMENT)
print('multi-component cases  :', p.PHASE11_MULTICOMPONENT_CASES)
print()
bridge = pd.read_csv(p.TABLES/'phase11_clean_v3_phase12_bridge_evidence.csv')
display(bridge[['evidence','value','verdict']])
print()
print('Phase-11 conclusion: MOTIVATES_ORACLE_ROI_TEST — NOT "ROI solves the problem".')
print('The Phase-11 FULL_FIELD/ROI values are OBSERVATIONAL acquisition-regime results,')
print('NOT oracle-ROI treatment effects.')
""")

md("""## 5. Historical Phase-12 Source Inventory
""")
co("""inv = p.build_source_inventory()
display(inv[['authority_rank','source_type','source_path','notes']])
print('\\nAll sources present:', bool((inv['notes']=='present').all()))
""")

md("""## 6. Historical Model / Split Scope
""")
co("""aud = p.load_historical_audit()
print('Historical model      :', aud['model'], f"({aud['experiment']})")
print('Historical checkpoint :', Path(aud['checkpoint']).name, '| SHA', aud['checkpoint_sha256'][:16]+'...')
print('Historical manifest   :', aud['manifest_version'])
print('Historical population :', aud['population'])
print('Historical threshold  :', aud['threshold'])
print()
print('NOTE: historically a SINGLE architecture (UNet++). Clean-v3 must use ALL FOUR.')
""")

md("""## 7. Historical Oracle Geometry (executing source: `src/analysis/oracle_roi.py`)
""")
co("""mx = p.build_protocol_matrix()
geo = mx[mx.concept.str.match('F_|G_|H_|I_|J_|K_|L_|M_|N_|O_')]
display(geo[['concept','historical_value','status']])
print()
print('Oracle unit  : PER_COMPONENT_BBOX (one square crop per native GT component)')
print('Margin       : round(margin * bbox_dim) per axis; margins {0.10,0.25,0.50}; primary 0.25')
print('Crop shape   : SQUARE (side = max(expanded_h, expanded_w), centred)')
print('Boundary     : clip to image + zero-pad to side')
print('Resolution   : 512x512 · image BILINEAR')
""")

md("""## 8. Historical Multi-Component Behaviour
""")
co("""mc = mx[mx.concept.str.startswith('F_')]
display(mc[['concept','historical_value','notes']])
print()
print('Each native GT component gets its OWN square crop; predictions are fused across crops')
print('via pixelwise MAX. A union/case bbox was NOT used historically.')
print('Implication: distant components are handled separately (no union-bbox resolution loss).')
""")

md("""## 9. Historical Mapping / Fusion
""")
co("""mf = mx[mx.concept.str.match('T_|U_|V_|W_|S_')]
display(mf[['concept','historical_value','notes']])
print()
print('Map-back : restore prob to (side,side) bilinear, strip pad, place at clip coords into a')
print('           ZERO-initialised full-size array.')
print('Fusion   : pixelwise MAX of restored component probabilities; threshold AFTER fusion.')
print('KEY: the global prediction is NOT retained outside the crop (outside = 0).')
""")

md("""## 10. Historical Metric Contract
""")
co("""print('Metrics            :', ', '.join(aud['metrics'].keys()))
print('Object recall defn : fraction of native GT components with >=1 overlapping predicted pixel')
print('Size taxonomy      : kub_size_v1 (HISTORICAL)')
print('FP caveat          :', aud['fp_caveat'])
print()
display(pd.read_csv(p.H_SUMMARY))
""")

md("""## 11. Historical Phase-12 → Phase-13 Rationale
""")
co("""print('Phase-13 gate      :', aud['phase13_gate'])
print('Phase-13 rationale :')
print(' >', aud['phase13_evidence'])
print()
print('HISTORICAL_v2_PROVENANCE_ONLY — recorded for understanding, never clean-v3 evidence.')
""")

md("""## 12. Historical Ambiguities / Conflicts
""")
co("""hist = json.loads((p.AUDITS/'phase12_historical_oracle_protocol_reconstruction.json').read_text(encoding='utf-8'))
for a in hist['ambiguities']:
    print(f"[{a['id']}] {a['item']}  ({a['status']})")
    print(f"     detail      : {a['detail']}")
    print(f"     disposition : {a['disposition']}")
    print()
print('Protocol-matrix status counts:', p.build_protocol_matrix().status.value_counts().to_dict())
""")

md("""## 13. CLEAN-v3 All-Four-Model Scope
""")
co("""print('Clean-v3 model scope:', [p.MODEL_DISPLAY[k] for k in p.CLEAN_V3_MODELS])
print('Reference model selected: NO')
print()
print('Purpose: test whether regional-resolution benefit is architecture-general or')
print('architecture-specific. UNet++ remains HISTORICAL provenance only.')
""")

md("""## 14. CLEAN-v3 FULL_FIELD Primary Population
""")
co("""print('Primary oracle population: KUB VAL FULL_FIELD =', p.PHASE11_REGIME['FULL_FIELD'], 'cases')
print('ROI acquisition cohort   :', p.PHASE11_REGIME['ROI'], 'cases — observational/descriptive context only')
print()
print('The FULL_FIELD regime is the native low-effective-resolution regime in which the')
print('regional hypothesis is scientifically relevant.')
print()
print('CAUTION: existing ROI acquisition cases are NOT oracle crops derived from the')
print('corresponding FULL_FIELD images, and no one-to-one pairing is assumed.')
""")

md("""## 15. Proposed Oracle Geometry (clean-v3 candidate)
""")
co("""cand_tbl = p.build_candidate_protocol()
display(cand_tbl[['field','proposed_clean_v3','scientifically_material','supervisor_decision_required']])
""")

md("""## 16. Proposed Multi-Component Rule
""")
co("""print('Multi-component candidate: one square crop per native GT component (carried forward).')
print('Fusion candidate         : pixelwise MAX of restored component probabilities.')
print()
print('Rationale: a single union bbox could lose the intended resolution benefit when')
print('components are far apart; per-component crops avoid that. Documented, not silently chosen.')
""")

md("""## 17. Proposed Regional Preprocessing
""")
co("""print('Canonical GLOBAL preprocessing (frozen):')
print('  aspect-preserving resize + centre/symmetric pad, target 512, image BILINEAR,')
print('  mask NEAREST, resize extent max(1, round(extent*scale))  (NOT int(...)), threshold 0.5')
print()
print('Regional CROP preprocessing (candidate):')
print('  crop original grayscale (convert L) -> zero-pad to square side -> resize 512 BILINEAR')
print('  -> /255.0 -> tensor (1,1,512,512); same frozen model reused on crops.')
print()
print('Regional crop preprocessing MUST be frozen before Part 1B.')
""")

md("""## 18. Proposed Mapping / Fusion
""")
co("""diff = p.build_protocol_diff()
mf = diff[diff.field.isin(['mapping_back_rule','global_outside_crop_rule','multiple_crop_fusion_rule'])]
display(mf)
print()
print('Two MATERIAL changes are escalated to the supervisor:')
print('  - mapping_back_rule      : restore in FLOAT (no uint8 quantisation)')
print('  - global_outside_crop_rule: retain global outside crop; report BOTH variants')
""")

md("""## 19. v2 → v3 Protocol Diff
""")
co("""display(diff)
print()
print('SAME/CHANGED:', diff.same_or_changed.value_counts().to_dict())
mat = diff[diff.scientifically_material]
print()
print('MATERIAL changes requiring supervisor decision:', len(mat))
display(mat[['field','historical_v2','proposed_clean_v3','change_reason']])
print()
print('Unauthorized material differences: 0 (none silently accepted).')
""")

md("""## 20. Prospective Metric Contract
""")
co("""display(p.build_metric_contract())
print()
print('Primary oracle effect is the PAIRED within-case, within-architecture delta:')
print('  delta_dice = oracle_dice - global_dice  (same FULL_FIELD case, same frozen model)')
""")

md("""## 21. Explicit Component Correspondence
""")
co("""display(p.build_correspondence_spec())
print()
print('This REPLACES the Phase-11 case-attributed size approximation: Phase 12 must use')
print('explicit native GT component identity + explicit mapping into regional coordinates,')
print('with detection = >=1 predicted pixel overlapping the mapped GT component.')
""")

md("""## 22. Phase-11 Frozen Cohort Bridge
""")
co("""display(p.build_cohort_bridge())
print()
print('These cohorts are pre-existing and frozen; they MUST NOT be reselected after seeing')
print('Phase-12 predictions (no cherry-picking).')
""")

md("""## 23. Future Visualization Protocol
""")
co("""display(p.build_viz_protocol())
print()
print('No plots are generated from clean oracle results in Part 1A.')
""")

md("""## 24. Regional Integration Gate Candidate
""")
co("""display(p.build_gate_candidate())
print()
print('All criteria are CANDIDATE_FOR_SUPERVISOR_FREEZE. No numeric threshold is frozen here.')
print('The gate is decided AFTER Phase 13. Part 1A does not choose GO / REVISE_LOCALIZER / NO_GO.')
""")

md("""## 25. Supervisor Decisions Required
""")
co("""for i, r in enumerate(json.loads((p.AUDITS/'phase12_clean_v3_oracle_protocol_candidate.json').read_text(encoding='utf-8'))['supervisor_decisions_required'], 1):
    print(f"{i}. {r['field']}")
    print(f"   historical_v2 : {r['historical_v2']}")
    print(f"   proposed      : {r['proposed_clean_v3']}")
    print(f"   reason        : {r['change_reason']}")
    print()
print('Until these are decided, the protocol remains a CANDIDATE (not frozen).')
""")

md("""## 26. Historical-v2 Separation

| | HISTORICAL v2 | CLEAN-v3 (future) |
|---|---|---|
| Manifest | `phase4_v2` | `phase4_v3` |
| Taxonomy | `kub_size_v1` | `kub_size_clean_v3_v1` |
| FULL_FIELD VAL | 106 | **103** |
| Model scope | UNet++ only | all four |

Historical Phase-12 numbers are **`HISTORICAL_v2_PROVENANCE_ONLY`** and must never be
presented as clean-v3 evidence.
""")

md("""## 27. Limitations

- Part 1A defines a protocol only; no clean-v3 oracle result exists yet.
- The historical design reused the **same global model** on crops — not a separate regional
  model; clean-v3 inherits that.
- Oracle-constrained FP is **artificially advantaged** and is not fairly comparable to
  deployable global inference (historical caveat).
- The historical `restore_crop_probability` quantises probabilities to uint8; the clean-v3
  candidate restores in float, which is a **material** change requiring supervisor sign-off.
- The historical oracle does not retain the global prediction outside the crop; the clean-v3
  candidate proposes reporting both variants — also **material**.
- Historical success was decided descriptively; **no numeric gate threshold was frozen**.
""")

# 28-31 upstream epoch tables
for i, k in enumerate(['unet','attention_unet','unetpp','deeplabv3plus'], start=28):
    d = {'unet':'UNet','attention_unet':'Attention U-Net','unetpp':'UNet++','deeplabv3plus':'DeepLabV3+'}[k]
    md(f"""## {i}. Upstream Frozen Training Provenance — {d}

Read-only from the frozen Phase-10 normalized epoch table. **Every epoch row is shown.**
""")
    co(f"""t = p.load_upstream_epoch_table('{k}')
v = p.verify_upstream_epoch_tables().query("model == '{d}'").iloc[0]
print('=== UPSTREAM {d} ===')
for kk in ['rows','expected_rows','row_count_matches','first_epoch','last_epoch',
           'missing_epochs','duplicate_epochs','contiguous']:
    print(f'  {{kk}}: {{v[kk]}}')
print()
assert v['row_count_matches'] and v['contiguous']
print(f"Rendering ALL {{len(t)}} epoch rows for {d}:")
display(t)
""")

md("""## 32. Artifact Registry
""")
co("""def _sh(rel):
    q = PROJECT_ROOT/rel
    return p.sha256_file(q) if q.exists() else 'N/A'
arts = [
 'reports/tables/phase12_historical_source_inventory.csv',
 'reports/tables/phase12_historical_oracle_protocol_matrix.csv',
 'reports/tables/phase12_v2_to_clean_v3_oracle_protocol_diff.csv',
 'reports/tables/phase12_clean_v3_oracle_protocol_candidate.csv',
 'reports/tables/phase12_clean_v3_component_correspondence_spec.csv',
 'reports/tables/phase12_clean_v3_future_metric_contract.csv',
 'reports/tables/phase12_clean_v3_future_visualization_protocol.csv',
 'reports/tables/regional_integration_gate_candidate_v1.csv',
 'reports/tables/phase12_phase11_frozen_cohort_bridge_plan.csv',
 'reports/audits/phase12_historical_oracle_protocol_reconstruction.json',
 'reports/audits/phase12_clean_v3_oracle_protocol_candidate.json',
 'notebooks/phasewise/phase_12_oracle_roi/code/phase12_oracle_protocol.py',
]
REG = pd.DataFrame([{'artifact': Path(a).name, 'path': a, 'sha256': _sh(a)} for a in arts])
rp = p.TABLES/'phase12_part1a_artifact_registry.csv'
REG.to_csv(rp, index=False)
print(f'Saved registry: {rp.name} ({len(REG)} entries)')
display(REG)
""")

md("""## 33. Stop Boundary
""")
co("""print('=== PHASE-12 PART-1A BOUNDARY ===')
print('Clean oracle inference passes : 0')
print('Training epochs               : 0')
print('Optimizer steps               : 0')
print('Checkpoint/history/config mods: 0')
print('TEST image/mask/content reads : 0')
print('New post-hoc thresholds       : 0')
print('Baseline winner / reference   : NONE')
print('Phase 12 Part 1B started      : NO')
print('Phase 13 started              : NO')
print('Regional mechanism promoted   : NO')
print('RA-MedFiLM implemented        : NO')
print()
print('ORACLE PROTOCOL STATUS: READY_FOR_SUPERVISOR_ORACLE_PROTOCOL_FREEZE')
print('NEXT: WAIT_FOR_SUPERVISOR_PHASE12_ORACLE_PROTOCOL_FREEZE_DECISION')
""")

out = Path(r'D:\Softfors\jup\notebooks\phasewise\phase_12_oracle_roi\phase12_clean_v3_oracle_regional_protocol_freeze.ipynb')
with open(out,'w',encoding='utf-8') as f:
    nbf.write(nb,f)
print(f'Notebook written: {out}')
print(f'Total cells: {len(nb.cells)}')
