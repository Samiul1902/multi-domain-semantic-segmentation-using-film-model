import json
import hashlib
from pathlib import Path
import pandas as pd

nb_dir = Path('notebooks')
nbs = sorted(list(nb_dir.glob('*.ipynb')))

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(4096), b''):
            h.update(c)
    return h.hexdigest()

phase_map = {
    '00_project_initialization.ipynb': ('Phase 0', 'CANONICAL_FROZEN'),
    '01_environment_and_data_audit.ipynb': ('Phase 1', 'CANONICAL_FROZEN'),
    '02_dataset_discovery.ipynb': ('Phase 2', 'CANONICAL_FROZEN'),
    '03_kub_forensic_audit.ipynb': ('Phase 3', 'CANONICAL_FROZEN'),
    '03_leakage_and_split_audit.ipynb': ('Phase 3', 'CANONICAL_FROZEN'),
    '04_kub_characterization.ipynb': ('Phase 4', 'CANONICAL_FROZEN'),
    '05_kub_object_size_taxonomy.ipynb': ('Phase 5', 'CANONICAL_FROZEN'),
    '06_kub_baseline_infrastructure.ipynb': ('Phase 8', 'CANONICAL_FROZEN'),
    '07_kub_unet_baseline_training.ipynb': ('Phase 9', 'CANONICAL_FROZEN'),
    '08_kub_baseline_comparison.ipynb': ('Phase 10', 'CANONICAL_FROZEN'),
    '09_kub_failure_analysis.ipynb': ('Phase 11', 'CANONICAL_FROZEN'),
    '09b_kub_manual_prediction_demo.ipynb': ('Phase 11B', 'CANONICAL_FROZEN'),
    '10_kub_oracle_roi_upper_bound.ipynb': ('Phase 12', 'CANONICAL_FROZEN'),
    '11_kub_predicted_roi_localizer.ipynb': ('Phase 13', 'CANONICAL_FROZEN'),
    '11b_kub_learned_localizer.ipynb': ('Phase 13B', 'CANONICAL_FROZEN'),
    '11c_kub_final_localizer_redesign.ipynb': ('Phase 13B', 'CANONICAL_FROZEN'),
    '12_phase14_15_gate_closure.ipynb': ('Phase 14/15 Admin', 'SUPERSEDED_ADMIN_CLOSURE'),
    '13_phase14_regional_refiner_diagnostic.ipynb': ('Phase 14', 'CANONICAL_FROZEN')
}

companion_requirements = {
    '00_project_initialization.ipynb': (False, 'Administrative setup only'),
    '01_environment_and_data_audit.ipynb': (False, 'Environment certification only'),
    '02_dataset_discovery.ipynb': (False, 'Catalog and file manifest discovery'),
    '03_kub_forensic_audit.ipynb': (False, 'Forensic integrity check'),
    '03_leakage_and_split_audit.ipynb': (False, 'Leakage audit'),
    '04_kub_characterization.ipynb': (True, 'Dataset characterization & visual inspection of KUB images'),
    '05_kub_object_size_taxonomy.ipynb': (True, 'Object size distribution & stone component taxonomy visuals'),
    '06_kub_baseline_infrastructure.ipynb': (False, 'Smoke test infrastructure'),
    '07_kub_unet_baseline_training.ipynb': (True, 'UNet baseline training curves & prediction visual companion'),
    '08_kub_baseline_comparison.ipynb': (True, 'Multi-architecture baseline comparison predictions & error maps'),
    '09_kub_failure_analysis.ipynb': (True, 'Failure case visual gallery & error taxonomy panel'),
    '09b_kub_manual_prediction_demo.ipynb': (False, 'Single interactive demo notebook'),
    '10_kub_oracle_roi_upper_bound.ipynb': (True, 'Oracle ROI zoom & boundary recovery prediction panels'),
    '11_kub_predicted_roi_localizer.ipynb': (True, 'Learned localizer heatmaps & proposal grid visualizations'),
    '11b_kub_learned_localizer.ipynb': (True, 'Compact CenterNet localizer training & heatmap visualizations'),
    '11c_kub_final_localizer_redesign.ipynb': (True, 'Final Stage-4D localizer heatmaps & 494 canonical proposals'),
    '12_phase14_15_gate_closure.ipynb': (False, 'Administrative gate evaluation'),
    '13_phase14_regional_refiner_diagnostic.ipynb': (True, 'Phase 14 16-case deep regional refinement visual companion')
}

rows = []
for p in nbs:
    with open(p, 'r', encoding='utf-8') as f:
        d = json.load(f)
    cells = d.get('cells', [])
    code = [c for c in cells if c.get('cell_type') == 'code']
    exec_code = [c for c in code if c.get('execution_count') is not None]
    text_content = ' '.join([''.join(c.get('source', [])) for c in cells]).lower()
    
    img_count = 0
    for c in code:
        for out in c.get('outputs', []):
            if out.get('output_type') == 'display_data':
                data = out.get('data', {})
                if 'image/png' in data or 'image/jpeg' in data:
                    img_count += 1
    
    phase, status = phase_map.get(p.name, ('Unknown', 'UNTRACKED'))
    needs_comp, comp_reason = companion_requirements.get(p.name, (False, ''))
    
    # Analyze visual properties
    has_plt = ('plt.' in text_content or 'matplotlib' in text_content)
    has_train_curve = ('loss' in text_content and 'epoch' in text_content) and ('curve' in text_content or 'history' in text_content)
    has_samples = ('sample' in text_content or 'raw_img' in text_content or 'image' in text_content) and ('imshow' in text_content or 'display' in text_content)
    has_pipe = ('pipeline' in text_content or 'step' in text_content or 'crop' in text_content or 'roi' in text_content)
    has_err = ('failure' in text_content or 'error' in text_content or 'fp' in text_content or 'fn' in text_content)
    has_agg = ('summary' in text_content or 'table' in text_content or 'df' in text_content or 'mean' in text_content)
    
    # Detailed predictions count estimation
    pred_count = 1 if p.name in ['09b_kub_manual_prediction_demo.ipynb', '13_phase14_regional_refiner_diagnostic.ipynb'] else 0
    if p.name == '13_phase14_regional_refiner_diagnostic.ipynb':
        pred_count = 1 # Cell 46 demo
    
    rows.append({
        'filename': p.name,
        'phase': phase,
        'status': status,
        'sha256': sha(p),
        'total_cells': len(cells),
        'code_cells': len(code),
        'executed_cells': len(exec_code),
        'sample_data_vis': 'YES' if has_samples else 'NO',
        'pipeline_vis': 'YES' if has_pipe else 'NO',
        'training_curves': 'YES' if has_train_curve else ('NA' if 'training' not in p.name and 'localizer' not in p.name and 'refiner' not in p.name else 'NO'),
        'aggregate_results': 'YES' if has_agg else 'NO',
        'prediction_examples_count': pred_count,
        'error_failure_vis': 'YES' if has_err else 'NO',
        'rendered_figures_present': 'YES' if img_count > 0 or has_plt else 'NO',
        'image_output_count': img_count,
        'companion_notebook_needed': 'YES' if needs_comp else 'NO',
        'companion_rationale': comp_reason
    })

df = pd.DataFrame(rows)
df.to_csv('reports/audits/notebook_visualization_inventory.csv', index=False)
with open('reports/audits/notebook_visualization_inventory.json', 'w', encoding='utf-8') as f:
    json.dump(rows, f, indent=2)

print("Inventory generated successfully. Total notebooks:", len(df))
print(df[['filename', 'phase', 'image_output_count', 'companion_notebook_needed']].to_string())

