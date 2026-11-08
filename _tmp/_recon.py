import csv, json, sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(r"D:/Softfors/jup")
rows = list(csv.DictReader(open(ROOT/"reports/tables/phase27_val808_predictions.csv", encoding="utf-8")))
print("cols:", list(rows[0].keys()))
print("n", len(rows))
print("sample:", {k: rows[0][k] for k in ("router_utility","router_decision","state_machine_branch","somega_logit","somega_accept")})
# distribution of router_utility
u = np.array([float(r["router_utility"]) for r in rows])
print("utility min/median/max:", round(u.min(),6), round(float(np.median(u)),6), round(u.max(),6))
for t in (-0.024358327623641256, 0.0):
    print(f"  n(utility > {t:.6f}) = {(u > t).sum()}")
