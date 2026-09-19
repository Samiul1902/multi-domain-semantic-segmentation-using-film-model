"""
DO_NOT_RUN_AFTER_PHASE4_FREEZE
Legacy script for rebuilding manifests.
Authoritative manifests are frozen under manifests/
"""

import os
import pandas as pd
import numpy as np
import hashlib
from pathlib import Path
import json
import datetime

# Settings
SEED = 42
RAW_ROOT = Path(r'D:\Softfors\omni_seg\data_raw')
KUB_PAIRS = Path(r'D:\Softfors\jup\reports\audits\kub_image_mask_pairs.csv')
MANIFEST_DIR = Path(r'D:\Softfors\jup\manifests')

def get_sample_id(row):
    return hashlib.md5((row['image_path'] + row['mask_path']).encode()).hexdigest()

print("manifest_rebuilder.py loaded successfully in verification mode.")
