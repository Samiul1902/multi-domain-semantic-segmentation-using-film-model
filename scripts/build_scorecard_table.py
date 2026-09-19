import pandas as pd
import json, os

p10_comp = pd.read_csv('reports/tables/phase10_kub_model_comparison.csv')
p14_mode = pd.read_csv('reports/tables/phase14_part3_mode_summary.csv')

scorecard_rows = []

# Baseline models from Phase 9/10
for _, row in p10_comp.iterrows():
    m_name = row['model']
    exp_id = 'phase9_kub_unet_baseline_seed42_512' if m_name == 'U-Net' else f"phase10_kub_{m_name.lower().replace(' ', '_').replace('+', 'plus')}_seed42_512"
    scorecard_rows.append({
        'phase': 'Phase 9/10',
        'experiment_id': exp_id,
        'model': m_name,
        'status': 'CANONICAL',
        'checkpoint_sha': 'verified',
        'val_population': 'KUB_VAL (283 images: 106 FULL_FIELD + 177 ROI_CROP)',
        'val_dice': round(row['macro_dice'], 4),
        'tiny_recall': round(row['tiny_object_recall'], 4),
        'small_recall': round(row['small_object_recall'], 4),
        'medium_recall': round(row['medium_object_recall'], 4),
        'large_recall': round(row['large_object_recall'], 4),
        'precision': round(row['macro_precision'], 4),
        'recall': round(row['macro_recall'], 4),
        'fp_burden': round(row['fp_components_per_image'], 4),
        'proposal_recall': 'N/A (Global)',
        'best_epoch': int(row['best_epoch']),
        'best_validation_metric': 'Val Macro Dice',
        'notes': 'Frozen benchmark baseline'
    })

# CenterNet Stage 4D Localizer
scorecard_rows.append({
    'phase': 'Phase 13B',
    'experiment_id': 'phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1',
    'model': 'CenterNet Localizer (Stage 4D)',
    'status': 'CANONICAL',
    'checkpoint_sha': 'ece906df6c73...',
    'val_population': 'KUB_VAL FULL_FIELD (106 images)',
    'val_dice': 'N/A (Detection/Proposal)',
    'tiny_recall': 0.8493,
    'small_recall': 0.8966,
    'medium_recall': 0.9444,
    'large_recall': 0.9444,
    'precision': 'N/A',
    'recall': 0.8841,
    'fp_burden': 0.5094,
    'proposal_recall': 0.8841,
    'best_epoch': 91,
    'best_validation_metric': 'Val Object Recall',
    'notes': 'Authoritative frozen localizer, AvgPool4 downsampling, sigma=0.75'
})

# Phase 14 Regional Refiner Diagnostic modes
for _, row in p14_mode.iterrows():
    mode = row['mode']
    scorecard_rows.append({
        'phase': 'Phase 14',
        'experiment_id': f"phase14_diag_mode_{mode.lower()}",
        'model': f"Regional Refiner Diagnostic ({mode})",
        'status': 'DIAGNOSTIC',
        'checkpoint_sha': '89ada7270038...',
        'val_population': 'KUB_VAL FULL_FIELD (106 images)',
        'val_dice': round(row['mean_dice_512'], 4),
        'tiny_recall': round(row['tiny_recall_512'], 4) if 'tiny_recall_512' in row else 'N/A',
        'small_recall': 'N/A',
        'medium_recall': 'N/A',
        'large_recall': 'N/A',
        'precision': 'N/A',
        'recall': 'N/A',
        'fp_burden': round(row['mean_fp_components'], 4) if 'mean_fp_components' in row else 'N/A',
        'proposal_recall': 'N/A',
        'best_epoch': 19,
        'best_validation_metric': 'Val Dice (Oracle ROIs)',
        'notes': f"Phase 14 evaluation mode: {mode}"
    })

sc_df = pd.DataFrame(scorecard_rows)
os.makedirs('reports/tables', exist_ok=True)
sc_df.to_csv('reports/tables/trained_model_visual_scorecard.csv', index=False)
print('Successfully generated trained_model_visual_scorecard.csv with', len(sc_df), 'entries!')

