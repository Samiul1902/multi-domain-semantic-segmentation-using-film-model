import json
import unittest
from pathlib import Path
import pandas as pd
from src.utils.experiment import register_experiment, CANONICAL_SCHEMA

ROOT = Path(r"D:\Softfors\jup")

class TestExperimentRegistry(unittest.TestCase):
    def test_registry_schema_and_alignment(self):
        sample_record = {
            "experiment_id": "test_registry_experiment_01",
            "phase": 8,
            "dataset": "KUB",
            "split_scope": "TRAIN+VAL_SMOKE_ONLY",
            "model": "unet",
            "architecture": "standard_unet_4_stage",
            "seed": 42,
            "image_size": 512,
            "batch_size": 4,
            "effective_batch_size": 4,
            "optimizer": "AdamW",
            "learning_rate": 1e-4,
            "weight_decay": 1e-4,
            "scheduler": "CosineAnnealingLR",
            "loss": "0.5_BCE+0.5_Dice",
            "threshold": 0.5,
            "manifest_version": "phase4_v2",
            "status": "SMOKE_TEST",
            "start_time": "2026-09-13T17:00:00Z",
            "end_time": "2026-09-13T17:01:00Z",
            "checkpoint_path": r"D:\Softfors\jup\checkpoints\test\latest.pt",
            "best_val_dice": "",
            "git_commit": "",
            "notes": "Unit test registration"
        }
        
        csv_path, json_path = register_experiment(sample_record, ROOT)
        
        # 1. Parse CSV
        df = pd.read_csv(csv_path)
        self.assertEqual(list(df.columns), CANONICAL_SCHEMA)
        
        # 2. Check row count and alignment for test record
        test_rows = df[df['experiment_id'] == "test_registry_experiment_01"]
        self.assertEqual(len(test_rows), 1)
        row = test_rows.iloc[0]
        self.assertEqual(row['seed'], 42)
        self.assertEqual(row['image_size'], 512)
        self.assertEqual(row['batch_size'], 4)
        self.assertEqual(row['optimizer'], "AdamW")
        self.assertEqual(row['status'], "SMOKE_TEST")
        self.assertEqual(row['dataset'], "KUB")
        self.assertEqual(row['model'], "unet")
        self.assertEqual(row['manifest_version'], "phase4_v2")
        
        # 3. JSON agreement
        with open(json_path, 'r', encoding='utf-8') as f:
            j_data = json.load(f)
        j_rec = next(r for r in j_data if r['experiment_id'] == "test_registry_experiment_01")
        self.assertEqual(j_rec['status'], "SMOKE_TEST")
        self.assertEqual(j_rec['optimizer'], "AdamW")
        self.assertEqual(j_rec['seed'], 42)
        
        # Clean up test entry from registry after test
        clean_json = [r for r in j_data if r.get('experiment_id') != "test_registry_experiment_01"]
        json_path.write_text(json.dumps(clean_json, indent=2), encoding="utf-8")
        clean_df = pd.DataFrame(clean_json)
        for col in CANONICAL_SCHEMA:
            if col not in clean_df.columns:
                clean_df[col] = ""
        clean_df = clean_df[CANONICAL_SCHEMA]
        clean_df.to_csv(csv_path, index=False)

if __name__ == '__main__':
    unittest.main()
