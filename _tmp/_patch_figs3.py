import pathlib

p = pathlib.Path(r"D:\Softfors\jup\full_doc_report\Scripts\build_figures.py")
s = p.read_text(encoding="utf-8")

old = '''            img = np.array(Image.open(img_p).convert("RGB"))
            img512 = _fit512(img)
            gt = np.array(Image.open(gt_p).convert("L").resize((512, 512), Image.NEAREST)) > 0'''
new = '''            img = np.array(Image.open(img_p).convert("RGB"))
            img512 = _fit512(img)
            npz = ROOT / man[sid]["npz_path"]
            with np.load(npz) as z:
                gt = z["gt"] > 0'''
assert old in s
s = s.replace(old, new)

old2 = '''        img512 = _fit512(np.array(Image.open(img_p).convert("RGB")))
        gt = np.array(Image.open(gt_p).convert("L").resize((512, 512), Image.NEAREST)) > 0'''
new2 = '''        img512 = _fit512(np.array(Image.open(img_p).convert("RGB")))
        with np.load(ROOT / man[sid]["npz_path"]) as z:
            gt = z["gt"] > 0'''
assert old2 in s
s = s.replace(old2, new2)

p.write_text(s, encoding="utf-8")
print("PATCHED")
