import unittest

class TestValidationAccumulator(unittest.TestCase):
    def test_validation_accumulator_no_duplicates(self):
        import pandas as pd
        from src.data.kub_localizer_dataset import KUBLocalizerDataset
        from torch.utils.data import DataLoader
        from src.models.factory import create_model
        from src.losses.localization import CenterNetFocalLoss
        import torch
        import sys
        from pathlib import Path
        import importlib.util
        
        spec = importlib.util.spec_from_file_location('train_script', 'scripts/training/train_phase13b_localizer.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        evaluate = mod.evaluate
        
        df_val = pd.read_csv('reports/tables/kub_val_samples_sized.csv').head(2)
        ds = KUBLocalizerDataset(df_val, 'VAL', 512, 3)
        loader = DataLoader(ds, batch_size=2)
        
        model = create_model('kub_localizer', in_channels=1, out_channels=1, base_channels=16).to(torch.device('cuda'))
        criterion = CenterNetFocalLoss(alpha=2.0, beta=4.0)
        
        phase13_components=pd.read_csv('reports/tables/phase13_predicted_roi_per_component.csv')
        component_table=phase13_components[['sample_id','component_id','min_y','max_y','min_x','max_x','kub_size_v1','global_detected']].copy()
        component_table['hard_tiny'] = False
        component_table['global_empty_image'] = False
        
        val_loss, search, cache, heatmap_diag = evaluate(model, loader, criterion, torch.device('cuda'), 512, component_table)
        
        self.assertEqual(len(cache), 2, f'Expected 2 elements in cache, got {len(cache)}')
        sample_ids = [c['sample_id'] for c in cache]
        self.assertEqual(len(set(sample_ids)), 2, 'Duplicate sample_ids found in cache!')
