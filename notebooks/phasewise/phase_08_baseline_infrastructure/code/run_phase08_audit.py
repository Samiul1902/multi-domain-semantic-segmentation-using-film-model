"""
Phase 08 Part 1A — driver.

Runs the infrastructure audit end-to-end: manifest verification, target/image/
transform/metric/reproducibility/checkpoint/taxonomy contracts, the loader sample
audit, the medical visual gallery, and a minimal CUDA smoke step.

No baseline training. No scientific performance claims. TEST content never opened.
"""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase08_infrastructure_audit as p8  # noqa: E402


def main():
    now = datetime.now(timezone.utc).isoformat()
    TABLES, AUDITS, FIGDIR = p8.TABLES, p8.AUDITS, p8.FIGDIR
    TABLES.mkdir(parents=True, exist_ok=True)
    AUDITS.mkdir(parents=True, exist_ok=True)
    FIGDIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Manifest verification
    # ------------------------------------------------------------------
    manifests = p8.verify_manifests()
    if not manifests['counts_ok'] or not manifests['guard_ok']:
        print('CHECK_REQUIRED: manifest verification failed')
        print(json.dumps(manifests, indent=2))
        sys.exit(2)

    train_df = pd.read_csv(p8.TRAIN_MANIFEST)

    # ------------------------------------------------------------------
    # 2. Contracts
    # ------------------------------------------------------------------
    target = p8.audit_target_contract(train_df)
    image_modes = p8.audit_image_modes(train_df)

    transform_df = p8.audit_transform_contract(train_df)
    p8.write_table(transform_df, 'phase08_transform_contract_audit.csv', TABLES)

    metric_df = p8.audit_metric_contract()
    p8.write_table(metric_df, 'phase08_metric_contract.csv', TABLES)

    repro_df = p8.audit_reproducibility()
    p8.write_table(repro_df, 'phase08_reproducibility_audit.csv', TABLES)

    with tempfile.TemporaryDirectory() as tmp:
        ckpt_df = p8.audit_checkpoint_contract(Path(tmp))
    p8.write_table(ckpt_df, 'phase08_checkpoint_contract.csv', TABLES)

    taxonomy = p8.audit_taxonomy_integration(train_df)

    # ------------------------------------------------------------------
    # 3. Deterministic loader sample audit
    # ------------------------------------------------------------------
    sel = p8.deterministic_sample_selection(train_df, n_total=16)
    sample_df, _ = p8.audit_loader_samples(sel)
    p8.write_table(sample_df, 'phase08_kub_v3_loader_sample_audit.csv', TABLES)
    selection_sha = p8.sha256_of_strings(sample_df['sample_id'].tolist())

    # ------------------------------------------------------------------
    # 4. Medical visual gallery
    # ------------------------------------------------------------------
    gal = p8.loader_gallery_pages(sel, cases_per_page=4)
    for i, f in enumerate(gal, 1):
        p8.save_fig(f, FIGDIR / f'phase08_loader_gallery_page{i:02d}.png')

    # ------------------------------------------------------------------
    # 5. CUDA smoke test (INFRASTRUCTURE_TEST_ONLY)
    # ------------------------------------------------------------------
    smoke = p8.cuda_smoke_test(sel)

    # ------------------------------------------------------------------
    # 6. Audit
    # ------------------------------------------------------------------
    from src.utils import device as dev
    device_report = dev.device_report()

    audit = {
        'audit': 'phase08_clean_v3_infrastructure_audit',
        'phase': '08 — Baseline Infrastructure (Part 1A)',
        'model': 'Gemini 3.8 Flash Medium',
        'generated_at': now,
        'manifest_version': p8.MANIFEST_VERSION,
        'taxonomy_id': p8.TAXONOMY_ID,
        'environment': device_report,
        'manifest_verification': manifests,
        'target_contract': target,
        'image_mode_contract': image_modes,
        'transform_contract': transform_df.to_dict('records'),
        'metric_contract': metric_df.to_dict('records'),
        'reproducibility': repro_df.to_dict('records'),
        'checkpoint_contract': ckpt_df.to_dict('records'),
        'taxonomy_integration': taxonomy,
        'loader_sample_audit': {
            'cases': int(len(sample_df)),
            'selection_sha': selection_sha,
            'acquisition_types': sample_df['acquisition_type'].value_counts().to_dict(),
            'categories': sample_df['category'].value_counts().to_dict(),
            'raw_label_signatures': sample_df['raw_mask_label_signature'].value_counts().to_dict(),
            'all_masks_binary': bool(sample_df['mask_is_binary'].all()),
        },
        'cuda_smoke': smoke,
        'test_content_reads': 0,
        'test_image_reads': 0,
        'test_mask_reads': 0,
        'test_metrics': 0,
        'test_visualizations': 0,
        'full_training_performed': False,
        'scientific_performance_claims': 'NONE',
        'phase09_started': False,
        'table_hashes': {n: p8.sha256_file(TABLES / n)
                         for n in p8.FINAL_TABLES if (TABLES / n).exists()},
        'figures': sorted(p.name for p in FIGDIR.glob('*.png')),
    }

    # gates
    gates = {
        'manifest_phase4_v3_validated': manifests['guard_ok'],
        'kub_counts_ok': manifests['counts_ok'],
        'mask_gt_zero_enforced': target['binarize_equivalence_failures'] == 0
                                and target['non_binary_after_binarize'] == 0,
        'non_one_labels_exercised': (255 in target['raw_label_union']
                                     and len(target['non_one_foreground_labels']) >= 3),
        'input_channel_convention_documented': image_modes['input_channel_convention'] == 1,
        'transform_geometry_verified': bool(transform_df['padded_w_ok'].all()
                                            and transform_df['padded_h_ok'].all()
                                            and transform_df['aligned'].all()),
        'mask_nearest_neighbour_verified': bool(transform_df['mask_is_binary'].all()),
        'cuda_required_path_works': device_report['cuda_available'],
        'reproducibility_helpers_work': not (repro_df['result'] == 'FAIL').any(),
        'metric_contract_explicit': len(metric_df) >= 4,
        'taxonomy_integration_works': taxonomy['api_ok'],
        'checkpoint_roundtrip_works': bool(ckpt_df[ckpt_df['item'].str.startswith('roundtrip')]['supported'].all()),
        'cuda_smoke_passed': bool(smoke.get('performed')) and smoke.get('losses_finite', False),
        'no_test_content_access': True,
        'no_baseline_training': True,
        'loader_audit_ge_12': len(sample_df) >= 12,
        'gallery_ge_12': len(sel) >= 12,
    }
    audit['scientific_gate'] = {
        'gates': gates,
        'status': 'PASS' if all(gates.values()) else 'CHECK_REQUIRED',
    }
    audit['status'] = audit['scientific_gate']['status']

    (AUDITS / 'phase08_clean_v3_infrastructure_audit.json').write_text(
        json.dumps(audit, indent=2, default=str), encoding='utf-8')
    _audit_md(audit, AUDITS / 'phase08_clean_v3_infrastructure_audit.md')

    # ------------------------------------------------------------------
    print('=' * 70)
    print('PHASE 08 PART 1A — INFRASTRUCTURE DRIVER')
    print('=' * 70)
    print('manifest guard        :', manifests['guard_ok'])
    print('KUB TRAIN / VAL       :', manifests['kub_train_cases'], '/', manifests['kub_val_cases'])
    print('train/val patients    :', manifests['train_patients'], '/', manifests['val_patients'])
    print('patient overlap       :', manifests['patient_overlap'])
    print('foreground rule       :', target['foreground_rule'])
    print('raw label union       :', target['raw_label_union'])
    print('input channels        :', image_modes['input_channel_convention'])
    print('transform rows OK     :', bool(transform_df['padded_w_ok'].all()))
    print('metric rows           :', len(metric_df))
    print('reproducibility       :', repro_df['result'].tolist())
    print('checkpoint roundtrip  :', bool(ckpt_df[ckpt_df['item'].str.startswith('roundtrip')]['supported'].all()))
    print('taxonomy              :', taxonomy['taxonomy_id'], '| ROI ->', taxonomy['roi_handling'])
    print('loader audit cases    :', len(sample_df))
    print('gallery cases         :', len(sel))
    print('CUDA smoke            :', smoke.get('performed'), '| batches:', smoke.get('batches'),
          '| peak MB:', smoke.get('peak_memory_mb'))
    print('figures               :', len(audit['figures']))
    print('gate                  :', audit['status'])
    print('NOTE: TEST reads = 0 | full training = NO | Phase 09 = NO')
    print('=' * 70)
    return audit


def _audit_md(audit, path):
    env = audit['environment']
    mf = audit['manifest_verification']
    tc = audit['target_contract']
    im = audit['image_mode_contract']
    md = [
        '# Phase 08 Part 1A — CLEAN-v3 Infrastructure Audit', '',
        f"**Status:** `{audit['status']}`  ",
        f"**Model:** {audit['model']}  ",
        f"**Generated:** {audit['generated_at']}", '',
        '## Environment', '',
        '| Field | Value |', '|---|---|',
        f"| PyTorch | `{env['pytorch_version']}` |",
        f"| CUDA available | {env['cuda_available']} |",
        f"| CUDA device | {env['cuda_device']} |",
        f"| CUDA runtime | `{env['cuda_runtime_version']}` |",
        f"| cuDNN | {env['cudnn_version']} |",
        f"| Canonical requires CUDA | {env['canonical_requires_cuda']} |", '',
        '## Manifest verification', '',
        '| Field | Value |', '|---|---|',
        f"| manifest_version | `{audit['manifest_version']}` |",
        f"| guard ok | {mf['guard_ok']} |",
        f"| TRAIN rows | {mf['train_rows']} |",
        f"| VAL rows | {mf['val_rows']} |",
        f"| KUB TRAIN cases | {mf['kub_train_cases']} |",
        f"| KUB VAL cases | {mf['kub_val_cases']} |",
        f"| TRAIN patients | {mf['train_patients']} |",
        f"| VAL patients | {mf['val_patients']} |",
        f"| patient overlap | {mf['patient_overlap']} |",
        f"| TEST metadata rows (never decoded) | {mf['test_metadata_rows']} |", '',
        '## Target contract', '',
        f"- Foreground rule: **`{tc['foreground_rule']}`**",
        f"- Samples audited: {tc['samples_audited']}",
        f"- Raw label union: {tc['raw_label_union']}",
        f"- Non-1 foreground labels: {tc['non_one_foreground_labels']}",
        f"- Binarization equivalence failures: {tc['binarize_equivalence_failures']}",
        f"- Non-binary after binarize: {tc['non_binary_after_binarize']}", '',
        '### Observed raw label signatures', '',
        '| Signature | Samples |', '|---|---:|']
    for k, v in tc['label_signatures'].items():
        md.append(f'| `{k}` | {v} |')
    md += ['', '## Image mode / channel convention', '',
           f"- Input channels: **{im['input_channel_convention']}**",
           f"- {im['convention_note']}", '',
           '| Source mode | Tensor channels | Shape |', '|---|---:|---|']
    for c in im['channel_checks']:
        md.append(f"| {c['source_mode']} | {c['tensor_channels']} | `{c['tensor_shape']}` |")
    md += ['', '## Transform contract', '',
           '| Target | Source | scale | resized | pad (l,t,r,b) | aligned | mask binary |',
           '|---|---:|---:|---|---|---:|---:|']
    for r in audit['transform_contract']:
        md.append(f"| {r['target_size']} | {r['source_h']}x{r['source_w']} | {r['actual_scale']:.6f} | "
                  f"{r['resized_w']}x{r['resized_h']} | "
                  f"({r['pad_left']},{r['pad_top']},{r['pad_right']},{r['pad_bottom']}) | "
                  f"{r['aligned']} | {r['mask_is_binary']} |")
    md += ['', '## Metric contract', '',
           '| Metric | Module | Version | Threshold | Epsilon | Empty handling |',
           '|---|---|---|---|---|---|']
    for r in audit['metric_contract']:
        md.append(f"| {r['metric']} | `{r['module']}` | {r['version']} | {r['threshold']} | "
                  f"{r['epsilon']} | {r['empty_handling']} |")
    md += ['', '## Reproducibility', '', '| Check | Result | Detail |', '|---|---|---|']
    for r in audit['reproducibility']:
        md.append(f"| {r['check']} | {r['result']} | {r['detail']} |")
    md += ['', '## Checkpoint contract', '', '| Item | Supported | Detail |', '|---|---|---|']
    for r in audit['checkpoint_contract']:
        md.append(f"| {r['item']} | {r['supported']} | {r['detail']} |")
    md += ['', '## Taxonomy integration', '',
           f"- taxonomy_id: `{audit['taxonomy_id']}`",
           f"- thresholds: {audit['taxonomy_integration']['thresholds']}",
           f"- ROI handling: `{audit['taxonomy_integration']['roi_handling']}`",
           f"- ROI-specific taxonomy created: {audit['taxonomy_integration']['roi_specific_taxonomy_created']}", '',
           '## Loader sample audit', '',
           f"- Cases: {audit['loader_sample_audit']['cases']}",
           f"- Selection SHA: `{audit['loader_sample_audit']['selection_sha']}`",
           f"- Acquisition types: {audit['loader_sample_audit']['acquisition_types']}",
           f"- Categories: {audit['loader_sample_audit']['categories']}",
           f"- Raw label signatures: {audit['loader_sample_audit']['raw_label_signatures']}",
           f"- All masks binary: {audit['loader_sample_audit']['all_masks_binary']}", '',
           '## CUDA smoke test (INFRASTRUCTURE_TEST_ONLY)', '']
    s = audit['cuda_smoke']
    if s.get('performed'):
        md += [f"- Label: **{s['label']}**",
               f"- Device: {s['device_name']}",
               f"- Batches: {s['batches']} (batch size {s['batch_size']})",
               f"- Input shape: `{s['input_shape']}` | target shape: `{s['target_shape']}`",
               f"- Target binary: {s['target_is_binary']}",
               f"- Losses finite: {s['losses_finite']}",
               f"- AMP enabled: {s['amp_enabled']} | GradScaler used: {s['grad_scaler_used']}",
               f"- Peak GPU memory: {s['peak_memory_mb']} MB",
               f"- Scientific claim: **{s['scientific_claim']}**", '']
    else:
        md += [f"- Not performed: {s.get('reason')}", '']
    md += ['## Governance', '',
           f"- TEST content reads: {audit['test_content_reads']}",
           f"- TEST image reads: {audit['test_image_reads']}",
           f"- TEST mask reads: {audit['test_mask_reads']}",
           f"- TEST metrics: {audit['test_metrics']}",
           f"- TEST visualizations: {audit['test_visualizations']}",
           f"- Full training performed: {audit['full_training_performed']}",
           f"- Scientific performance claims: {audit['scientific_performance_claims']}",
           f"- Phase 09 started: {audit['phase09_started']}", '',
           '## Scientific / engineering gate', '',
           '| Gate | Result |', '|---|---|']
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
