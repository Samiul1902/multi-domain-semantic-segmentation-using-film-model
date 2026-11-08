import csv, numpy as np
from pathlib import Path
from PIL import Image
ROOT = Path(r"D:/Softfors/jup")
rows = list(csv.DictReader(open(ROOT/"reports/tables/phase27_val808_predictions.csv", encoding="utf-8")))
man = {r["sample_id"]: r for r in csv.DictReader(open(ROOT/"reports/tables/phase21_prediction_manifest.csv", encoding="utf-8"))}
shapes = {"gt": {}, "global": {}, "final": {}}
mismatch_gf = mismatch_gt = 0
for r in rows:
    sid = r["sample_id"]
    with np.load(ROOT/man[sid]["npz_path"]) as z:
        g = z["gt"].shape
    a = np.array(Image.open(ROOT/r["global_mask_path"]).convert("L")).shape
    b = np.array(Image.open(ROOT/r["final_mask_path"]).convert("L")).shape
    shapes["gt"][g] = shapes["gt"].get(g,0)+1
    shapes["global"][a] = shapes["global"].get(a,0)+1
    shapes["final"][b] = shapes["final"].get(b,0)+1
    if a != b: mismatch_gf += 1
    if a != g: mismatch_gt += 1
print("gt shapes     :", shapes["gt"])
print("global shapes :", shapes["global"])
print("final shapes  :", shapes["final"])
print("global != final shape :", mismatch_gf)
print("global != gt shape    :", mismatch_gt)
