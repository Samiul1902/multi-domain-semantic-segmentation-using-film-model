import csv, numpy as np
from pathlib import Path
from PIL import Image

ROOT = Path(r"D:/Softfors/jup")
rows = list(csv.DictReader(open(ROOT/"reports/tables/phase27_val808_predictions.csv", encoding="utf-8")))
man = {r["sample_id"]: r for r in csv.DictReader(open(ROOT/"reports/tables/phase21_prediction_manifest.csv", encoding="utf-8"))}

def load(p):
    return (np.array(Image.open(ROOT/p).convert("L")) > 0)

def dice(a, b):
    s = a.sum() + b.sum()
    if s == 0:
        return 1.0
    return float(2.0 * np.logical_and(a, b).sum() / s)

# cache masks
gt, gl, fi = {}, {}, {}
for r in rows:
    sid = r["sample_id"]
    with np.load(ROOT/man[sid]["npz_path"]) as z:
        gt[sid] = z["gt"] > 0
    gl[sid] = load(r["global_mask_path"])
    fi[sid] = load(r["final_mask_path"])

# does final == global for SKIP rows?
skip = [r for r in rows if r["state_machine_branch"] == "SKIP_GLOBAL"]
same = sum(1 for r in skip if np.array_equal(fi[r["sample_id"]], gl[r["sample_id"]]))
print(f"SKIP rows: {len(skip)}, final==global: {same}")

def macro(policy_mask):
    by = {}
    for r in rows:
        d = dice(policy_mask(r), gt[r["sample_id"]])
        by.setdefault(r["dataset"], []).append(d)
    per = {k: float(np.mean(v)) for k, v in by.items()}
    return float(np.mean(list(per.values()))), per

# canonical: always use final
m, per = macro(lambda r: fi[r["sample_id"]])
print(f"\ncanonical (final for all)        : {m:.6f}")
print("   per domain:", {k: round(v, 6) for k, v in per.items()})

# accepted-only refinement
acc = {r["sample_id"] for r in rows if r["state_machine_branch"] == "EXECUTE_THEN_ACCEPT"}
m2, _ = macro(lambda r: fi[r["sample_id"]] if r["sample_id"] in acc else gl[r["sample_id"]])
print(f"accepted-only refinement         : {m2:.6f}")

# top-k by utility, accept if in acc
u = {r["sample_id"]: float(r["router_utility"]) for r in rows}
order = sorted(u, key=lambda s: -u[s])
for k in (183, 185, 181, 279):
    sel = set(order[:k])
    m3, per3 = macro(lambda r: fi[r["sample_id"]] if (r["sample_id"] in sel and r["sample_id"] in acc) else gl[r["sample_id"]])
    print(f"top-{k:3d} by utility, safety-gated : {m3:.6f}   target 0.837862 -> diff {abs(m3-0.837862):.6f}")
