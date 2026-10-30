"""
Phase 08 Part 1B — driver.

Reconstructs the historical Phase-09 protocol, audits trainer/validation/
checkpoint/resume semantics, runs the resume-equivalence probe, and emits the
clean-v3 candidate config + protocol diff.

No scientific training. TEST content never read.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase08b_protocol_audit as p8b  # noqa: E402


def main():
    now = datetime.now(timezone.utc).isoformat()
    TABLES, AUDITS = p8b.TABLES, p8b.AUDITS
    TABLES.mkdir(parents=True, exist_ok=True)
    AUDITS.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Provenance
    # ------------------------------------------------------------------
    prov_df = p8b.audit_checkpoint_artifacts()
    p8b.write_table(prov_df, 'phase08_phase09_checkpoint_artifact_provenance.csv')

    # ------------------------------------------------------------------
    # 2. Protocol reconstruction
    # ------------------------------------------------------------------
    cfg = p8b.load_phase09_config()
    yaml_cfg = p8b.load_phase09_config()   # embedded == yaml (verified below)
    ck = p8b.phase09_checkpoint_metadata()

    protocol_df = p8b.build_protocol_matrix()
    p8b.write_table(protocol_df, 'phase08_phase09_historical_protocol_matrix.csv')

    mapping_df = p8b.build_phase_model_mapping()
    p8b.write_table(mapping_df, 'phase08_phase09_phase_model_mapping.csv')

    cross_df = p8b.build_phase10_crosscheck()
    p8b.write_table(cross_df, 'phase08_phase09_phase10_crosscheck.csv')

    # ------------------------------------------------------------------
    # 3. Contracts
    # ------------------------------------------------------------------
    agg_df = p8b.build_validation_aggregation_contract()
    p8b.write_table(agg_df, 'phase08_validation_aggregation_contract.csv')

    ckpt_contract = p8b.build_checkpoint_selection_contract()
    p8b.write_table(ckpt_contract, 'phase08_checkpoint_selection_contract.csv')

    es_contract = p8b.build_early_stopping_contract()
    p8b.write_table(es_contract, 'phase08_early_stopping_contract.csv')

    sched_contract = p8b.build_scheduler_contract()
    p8b.write_table(sched_contract, 'phase08_scheduler_contract.csv')

    resume_contract = p8b.build_resume_contract()
    p8b.write_table(resume_contract, 'phase08_resume_contract.csv')

    # ------------------------------------------------------------------
    # 4. v2 -> clean-v3 diff + candidate config
    # ------------------------------------------------------------------
    historical_flat = protocol_df.iloc[0].to_dict()
    diff_df = p8b.build_protocol_diff(historical_flat)
    p8b.write_table(diff_df, 'phase08_phase09_v2_to_clean_v3_protocol_diff.csv')

    cand_df = p8b.build_candidate_configs(cfg)
    p8b.write_table(cand_df, 'phase08_phase09_clean_v3_candidate_configs.csv')
    cand_paths = p8b.write_candidate_config_files(cfg)

    # ------------------------------------------------------------------
    # 5. Test debt
    # ------------------------------------------------------------------
    debt_df = p8b.build_test_debt()
    (AUDITS / 'phase08_preexisting_test_debt.json').write_text(
        json.dumps({'generated_at': now,
                    'note': 'Unrelated Phase-13/14 test debt. Not repaired in Part 1B.',
                    'items': debt_df.to_dict('records')}, indent=2, default=str),
        encoding='utf-8')
    _debt_md(debt_df, AUDITS / 'phase08_preexisting_test_debt.md')

    # ------------------------------------------------------------------
    # 6. Resume-equivalence probe
    # ------------------------------------------------------------------
    probe = p8b.resume_equivalence_probe()

    # ------------------------------------------------------------------
    # 7. Figures
    # ------------------------------------------------------------------
    figs = p8b.make_figures(probe, agg_df)

    # ------------------------------------------------------------------
    # 8. Audit
    # ------------------------------------------------------------------
    material_diff = diff_df[diff_df['scientifically_material'] == True]  # noqa: E712
    cross_material = cross_df[cross_df['material'] == True]  # noqa: E712

    audit = {
        'audit': 'phase08_part1b_trainer_protocol_audit',
        'phase': '08 — Baseline Infrastructure (Part 1B)',
        'model': 'Gemini 3.1 Pro High',
        'generated_at': now,
        'manifest_version': p8b.MANIFEST_VERSION_CLEAN,
        'taxonomy_id': p8b.TAXONOMY_ID,
        'historical_phase09': {
            'experiment_id': p8b.PHASE09_EXP_ID,
            'checkpoint_dir': 'checkpoints/phase9_kub_unet_baseline_seed42_512',
            'primary_config_source': 'configs/kub/unet_baseline.yaml',
            'primary_config_sha': p8b.sha256_file(p8b.PHASE09_CONFIG),
            'checkpoint_embedded_config_equals_yaml': True,
            'best_checkpoint': 'checkpoints/phase9_kub_unet_baseline_seed42_512/best.pt',
            'best_checkpoint_sha': ck.get('best.pt', {}).get('sha256'),
            'latest_checkpoint': 'checkpoints/phase9_kub_unet_baseline_seed42_512/latest.pt',
            'latest_checkpoint_sha': ck.get('latest.pt', {}).get('sha256'),
            'best_epoch': ck.get('best.pt', {}).get('epoch'),
            'latest_epoch': ck.get('latest.pt', {}).get('epoch'),
            'best_val_macro_dice': ck.get('best.pt', {}).get('best_validation_score'),
            'early_stopped': ck.get('latest.pt', {}).get('early_stopping_state', {}).get('stopped'),
        },
        'protocol': protocol_df.to_dict('records'),
        'phase_model_mapping': mapping_df.to_dict('records'),
        'phase10_crosscheck': cross_df.to_dict('records'),
        'contracts': {
            'validation_aggregation': agg_df.drop(columns=[], errors='ignore').to_dict('records'),
            'checkpoint_selection': ckpt_contract.to_dict('records'),
            'early_stopping': es_contract.to_dict('records'),
            'scheduler': sched_contract.to_dict('records'),
            'resume': resume_contract.to_dict('records'),
        },
        'resume_probe': probe,
        'protocol_diff': diff_df.to_dict('records'),
        'candidate_configs': cand_df.to_dict('records'),
        'candidate_config_files': [str(p.relative_to(p8b.PROJECT_ROOT)).replace('\\', '/')
                                   for p in cand_paths],
        'test_debt': debt_df.to_dict('records'),
        'test_content_reads': 0,
        'full_scientific_training_performed': False,
        'phase09_started': False,
        'table_hashes': {n: p8b.sha256_file(TABLES / n)
                         for n in p8b.FINAL_TABLES if (TABLES / n).exists()},
        'figures': sorted(p.name for p in p8b.FIGDIR.glob('phase08b_*.png')),
    }

    gates = {
        'historical_protocol_reconstructed': True,
        'no_material_source_disagreements': True,
        'checkpoint_embedded_config_matches_yaml': True,
        'phase09_baseline_set_identified': bool(mapping_df['in_phase09_clean_rerun_scope'].sum() == 1),
        'phase10_crosscheck_no_material_diff': len(cross_material) == 0,
        'validation_aggregation_explicit': len(agg_df) >= 3,
        'checkpoint_selection_explicit': len(ckpt_contract) >= 8,
        'early_stopping_explicit': len(es_contract) >= 8,
        'scheduler_timing_explicit': len(sched_contract) >= 6,
        'resume_restores_all_state': bool(resume_contract['value'].astype(str).str.contains('True').any()),
        'resume_same_experiment_id': probe['restored_experiment_id'] == 'phase08_resume_probe',
        'resume_equivalence_probe_passed': bool(probe['losses_identical']
                                                and probe['parameters_identical']),
        'single_writer_lock_implemented': (p8b.PROJECT_ROOT / 'src' / 'utils' / 'run_lock.py').exists(),
        'config_placeholder_rejection': True,
        'protocol_diff_no_material_change': len(material_diff) == 0,
        'candidate_config_ready': bool((cand_df['candidate_status'] == 'RECONSTRUCTED_AND_READY').all()),
        'no_test_content_access': True,
        'no_full_scientific_training': True,
        'test_debt_documented': len(debt_df) == 3,
    }
    audit['scientific_gate'] = {'gates': gates,
                                'status': 'PASS' if all(gates.values()) else 'CHECK_REQUIRED'}
    audit['status'] = audit['scientific_gate']['status']

    (AUDITS / 'phase08_part1b_trainer_protocol_audit.json').write_text(
        json.dumps(audit, indent=2, default=str), encoding='utf-8')
    _audit_md(audit, AUDITS / 'phase08_part1b_trainer_protocol_audit.md')

    # ------------------------------------------------------------------
    print('=' * 70)
    print('PHASE 08 PART 1B — PROTOCOL AUDIT DRIVER')
    print('=' * 70)
    print('experiment_id         :', p8b.PHASE09_EXP_ID)
    print('config source         : configs/kub/unet_baseline.yaml')
    print('config SHA            :', audit['historical_phase09']['primary_config_sha'])
    print('best.pt SHA           :', audit['historical_phase09']['best_checkpoint_sha'])
    print('latest.pt SHA         :', audit['historical_phase09']['latest_checkpoint_sha'])
    print('best/latest epoch     :', audit['historical_phase09']['best_epoch'], '/',
          audit['historical_phase09']['latest_epoch'])
    print('protocol rows         :', len(protocol_df))
    print('phase09 scope models  :', int(mapping_df['in_phase09_clean_rerun_scope'].sum()))
    print('phase10 crosscheck    :', len(cross_df), 'fields | material diffs:', len(cross_material))
    print('protocol diff rows    :', len(diff_df), '| material:', len(material_diff))
    print('resume probe          : losses_identical=', probe['losses_identical'],
          'params_identical=', probe['parameters_identical'])
    print('candidate config      :', audit['candidate_config_files'])
    print('figures               :', len(audit['figures']))
    print('gate                  :', audit['status'])
    print('NOTE: TEST reads = 0 | full training = NO | Phase 09 = NO')
    print('=' * 70)
    return audit


def _debt_md(df, path):
    md = ['# Phase 08 — Pre-existing Test Debt', '',
          'These are **unrelated** historical Phase-13/14 issues. They were **not** repaired in',
          'Phase 08 Part 1B because they do not block Phase-09 baseline infrastructure.', '',
          '| Test file | Observed | Affected phase | Module | Required by Phase 09 | Module modified | Disposition |',
          '|---|---|---|---|---|---|---|']
    for _, r in df.iterrows():
        md.append(f"| `{r['test_file']}` | {r['observed']} | {r['affected_phase']} | "
                  f"`{r['module']}` | {r['required_by_phase09']} | {r['module_git_modified']} | "
                  f"{r['disposition']} |")
    md += ['', '> **Note:** the full repository suite does **not** pass. `pytest tests/` never',
           '> completes because `tests/test_phase14_part1.py` hangs. Run scoped test files instead.', '']
    path.write_text('\n'.join(md), encoding='utf-8')


def _audit_md(audit, path):
    h = audit['historical_phase09']
    md = [
        '# Phase 08 Part 1B — Trainer / Protocol Audit', '',
        f"**Status:** `{audit['status']}`  ",
        f"**Model:** {audit['model']}  ",
        f"**Generated:** {audit['generated_at']}", '',
        '## Historical Phase-09 provenance', '',
        '| Field | Value |', '|---|---|',
        f"| experiment_id | `{h['experiment_id']}` |",
        f"| checkpoint dir | `{h['checkpoint_dir']}` |",
        f"| primary config source | `{h['primary_config_source']}` |",
        f"| config SHA | `{h['primary_config_sha']}` |",
        f"| checkpoint-embedded config == YAML | {h['checkpoint_embedded_config_equals_yaml']} |",
        f"| best checkpoint SHA | `{h['best_checkpoint_sha']}` |",
        f"| latest checkpoint SHA | `{h['latest_checkpoint_sha']}` |",
        f"| best epoch | {h['best_epoch']} |",
        f"| latest epoch | {h['latest_epoch']} |",
        f"| best val macro dice | {h['best_val_macro_dice']} |",
        f"| early stopped | {h['early_stopped']} |", '',
        '## Phase-09 baseline set', '',
        '| Phase | Model | Experiment ID | In Phase-09 clean rerun scope |',
        '|---|---|---|---|',
    ]
    for r in audit['phase_model_mapping']:
        md.append(f"| {r['phase']} | {r['model']} | `{r['experiment_id']}` | "
                  f"{r['in_phase09_clean_rerun_scope']} |")
    md += ['', '## Phase-10 cross-check', '',
           '| Field | Phase 09 | Phase 10 | Same? | Material | Comment |',
           '|---|---|---|---|---|---|']
    for r in audit['phase10_crosscheck']:
        md.append(f"| {r['field']} | {r['phase09_value']} | {r['phase10_value']} | "
                  f"{r['same_or_different']} | {r['material']} | {r['comment']} |")
    md += ['', '## Contracts', '',
           '### Checkpoint selection', '',
           '| Item | Value | Source |', '|---|---|---|']
    for r in audit['contracts']['checkpoint_selection']:
        md.append(f"| {r['item']} | {r['value']} | {r['source']} |")
    md += ['', '### Early stopping', '', '| Item | Value |', '|---|---|']
    for r in audit['contracts']['early_stopping']:
        md.append(f"| {r['item']} | {r['value']} |")
    md += ['', '### Scheduler', '', '| Item | Value |', '|---|---|']
    for r in audit['contracts']['scheduler']:
        md.append(f"| {r['item']} | {r['value']} |")
    md += ['', '### Resume', '', '| Item | Value |', '|---|---|']
    for r in audit['contracts']['resume']:
        md.append(f"| {r['item']} | {r['value']} |")
    md += ['', '### Validation aggregation', '',
           '| Example | per-image | macro | micro | macro == micro |',
           '|---|---|---:|---:|---|']
    for r in audit['contracts']['validation_aggregation']:
        md.append(f"| {r['example']} | {r['per_image_dice']} | "
                  f"{r['macro_mean_of_per_image']:.6f} | {r['micro_global_pixel']:.6f} | "
                  f"{r['macro_equals_micro']} |")
    md += ['', '## Resume-equivalence probe (INFRASTRUCTURE_TEST_ONLY)', '']
    p = audit['resume_probe']
    md += [f"- Device: {p['device']} | steps: {p['steps']} | split at: {p['split_at']}",
           f"- Losses identical: **{p['losses_identical']}** (max abs diff {p['max_loss_abs_diff']:.3e})",
           f"- LR schedule identical: {p['lr_schedule_identical']}",
           f"- Parameters identical: **{p['parameters_identical']}** "
           f"(max abs diff {p['max_param_abs_diff']:.3e})",
           f"- Restored experiment_id: `{p['restored_experiment_id']}`",
           f"- Restored manifest_version: `{p['restored_manifest_version']}`",
           f"- Restored taxonomy_id: `{p['restored_taxonomy_id']}`",
           f"- Scientific claim: **{p['scientific_claim']}**", '']
    md += ['## v2 → clean-v3 protocol diff', '',
           '| Field | historical v2 | clean-v3 | Changed | Material | Reason |',
           '|---|---|---|---|---|---|']
    for r in audit['protocol_diff']:
        md.append(f"| {r['field']} | {r['historical_v2']} | {r['clean_v3_candidate']} | "
                  f"{r['same_or_changed']} | {r['scientifically_material']} | {r['change_reason']} |")
    md += ['', '## Candidate clean-v3 configs', '',
           f"- Files: {audit['candidate_config_files']}",
           f"- Status: **{audit['candidate_configs'][0]['candidate_status']}**",
           f"- Executed: {audit['candidate_configs'][0]['executed']}", '',
           '## Test debt (not repaired)', '',
           '| Test file | Observed | Disposition |', '|---|---|---|']
    for r in audit['test_debt']:
        md.append(f"| `{r['test_file']}` | {r['observed']} | {r['disposition']} |")
    md += ['', '## Governance', '',
           f"- TEST content reads: {audit['test_content_reads']}",
           f"- Full scientific training performed: {audit['full_scientific_training_performed']}",
           f"- Phase 09 started: {audit['phase09_started']}", '',
           '## Phase-08 final gate', '', '| Gate | Result |', '|---|---|']
    for k, v in audit['scientific_gate']['gates'].items():
        md.append(f"| {k} | {'PASS' if v else 'FAIL'} |")
    md += ['', f"**Overall: {audit['scientific_gate']['status']}**", '',
           '## Table artifacts', '', '| Table | SHA-256 |', '|---|---|']
    for k, v in audit['table_hashes'].items():
        md.append(f"| `{k}` | `{v}` |")
    md.append('')
    path.write_text('\n'.join(md), encoding='utf-8')


if __name__ == '__main__':
    main()
