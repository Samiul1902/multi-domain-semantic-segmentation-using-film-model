import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

CANONICAL_SCHEMA = [
    'experiment_id',
    'phase',
    'dataset',
    'split_scope',
    'model',
    'architecture',
    'seed',
    'image_size',
    'batch_size',
    'effective_batch_size',
    'optimizer',
    'learning_rate',
    'weight_decay',
    'scheduler',
    'loss',
    'threshold',
    'manifest_version',
    'status',
    'start_time',
    'end_time',
    'checkpoint_path',
    'best_val_dice',
    'git_commit',
    'notes'
]

def create_experiment_id(prefix, seed):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}_{stamp}_seed{seed}"

def normalize_record(record):
    norm = {}
    aliases = {
        'split': 'split_scope',
        'checkpoint': 'checkpoint_path',
        'validation_metrics': 'best_val_dice'
    }
    for k, v in record.items():
        target_k = aliases.get(k, k)
        norm[target_k] = v
        
    ordered = {}
    for col in CANONICAL_SCHEMA:
        ordered[col] = norm.get(col, "")
    return ordered

def register_experiment(record, project_root=r"D:\Softfors\jup"):
    directory = Path(project_root) / "experiments"
    directory.mkdir(parents=True, exist_ok=True)
    csv_path = directory / "registry.csv"
    json_path = directory / "registry.json"
    
    norm_rec = normalize_record(record)
    
    existing = []
    if json_path.exists():
        try:
            existing = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            existing = []
            
    existing = [r for r in existing if r.get('experiment_id') != norm_rec['experiment_id']]
    existing.append(norm_rec)
    
    json_path.write_text(json.dumps(existing, indent=2, default=str), encoding="utf-8")
    
    df = pd.DataFrame(existing)
    for col in CANONICAL_SCHEMA:
        if col not in df.columns:
            df[col] = ""
    df = df[CANONICAL_SCHEMA]
    df.to_csv(csv_path, index=False)
    
    return csv_path, json_path
