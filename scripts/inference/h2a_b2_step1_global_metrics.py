"""H2A-B2 Step 1: Compute global metrics from cache and save to pickle."""
import sys
from pathlib import Path
import numpy as np
import pickle

sys.path.insert(0, str(Path(r"D:\Softfors\jup")))
sys.path.insert(0, str(Path(r"D:\Softfors\jup") / "notebooks" / "phasewise" / "phase_12_oracle_roi" / "code"))
import phase12_oracle_inference as p12

CACHE = Path(r"D:\Softfors\jup") / "data_cache" / "phase13_part1d_b_predicted_region_clean_v3" / "global_512"
THRESHOLD = 0.5
MODELS = ["unet", "attention_unet", "unetpp", "deeplabv3plus"]

ff = p12.full_field_frame()
ff_ids = list(ff["sample_id"])

case_geom = {}
for _, r in ff.iterrows():
    gt = p12.native_gt(Path(r["mask_path"]))
    lab, n = p12.label(gt > 0, structure=p12.STRUCT8)
    case_geom[r["sample_id"]] = {"pre": p12.preprocess_geometry(gt.shape),
                                 "shape": gt.shape, "gt": gt, "lab": lab, "n": int(n)}

global_metrics = {}
gdet = {}
for key in MODELS:
    for sid in ff_ids:
        cg = case_geom[sid]
        arr = np.load(CACHE / key / f"{sid}.npy")
        G = p12.global_native(arr, cg["pre"], cg["shape"])
        pred = G >= THRESHOLD
        m = p12.native_metrics(cg["gt"], pred)
        det, missed = p12.component_detection(cg["gt"], pred, cg["lab"], cg["n"])
        m["detected_native_components"] = int(det)
        m["missed_native_components"] = int(missed)
        m["object_recall"] = float(det / cg["n"]) if cg["n"] else float("nan")
        global_metrics[(key, sid)] = m
        gdet.update({(key, sid, c): v for c, v in
                     {cid: bool(int((pred & (cg["lab"] == cid)).sum()) >= 1)
                      for cid in range(1, cg["n"] + 1)}.items()})

with open("data_cache/h2a_downstream_global_metrics.pkl", "wb") as f:
    pickle.dump({"global_metrics": global_metrics, "gdet": gdet}, f)
print("saved data_cache/h2a_downstream_global_metrics.pkl")
