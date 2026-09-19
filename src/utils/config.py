import yaml
import json
import os

def load_config(config_path):
    with open(config_path, 'r') as f:
        if config_path.endswith('.yaml'):
            return yaml.safe_load(f)
        elif config_path.endswith('.json'):
            return json.load(f)
    return None
