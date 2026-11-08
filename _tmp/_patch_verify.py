import pathlib

# ---- 1. add a real mask-geometry check to the acceptance suite ------------
p = pathlib.Path(r"D:\Softfors\jup\full_doc_report\Scripts\verify_verified.py")
s = p.read_text(encoding="utf-8")

anchor = '''    # 6. external ------------------------------------------------------------'''
geom = '''    # mask geometry across all 808 samples
    import numpy as _np
    from PIL import Image as _Img
    prows = load(ROOT / "reports/tables/phase27_val808_predictions.csv")
    pman = {r["sample_id"]: r for r in load(
        ROOT / "reports/tables/phase21_prediction_manifest.csv")}
    bad_geom, shapes = [], set()
    for r in prows:
        sid = r["sample_id"]
        with _np.load(ROOT / pman[sid]["npz_path"]) as z:
            gs = z["gt"].shape
        a = _np.array(_Img.open(ROOT / r["global_mask_path"]).convert("L")).shape
        b = _np.array(_Img.open(ROOT / r["final_mask_path"]).convert("L")).shape
        shapes.add((gs, a, b))
        if not (gs == a == b):
            bad_geom.append(sid)
    add("mask geometry consistent across all 808 samples", not bad_geom,
        f"shape sets={len(shapes)} mismatches={len(bad_geom)}")

''' + anchor

assert anchor in s
s = s.replace(anchor, geom, 1)
p.write_text(s, encoding="utf-8")
print("geometry check added")

# ---- 2. point the reconstruction summary at the verified master -----------
q = pathlib.Path(r"D:\Softfors\jup\full_doc_report\Scripts\finalize_reconstruction.py")
t = q.read_text(encoding="utf-8")
old = '    master = OUT / "ReMedFiLM_COMPLETE_MASTER.ipynb"'
new = '    master = OUT / "ReMedFiLM_COMPLETE_MASTER_VERIFIED.ipynb"'
assert old in t
t = t.replace(old, new)
q.write_text(t, encoding="utf-8")
print("summary target -> VERIFIED master")
