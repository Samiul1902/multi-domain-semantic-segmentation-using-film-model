"""
Build the four-domain montages for the methodology diagram evidence package.

GOVERNANCE: no model execution. Uses only the already-built representative
sample PNGs (raw VAL input / GT) created by build_methodology_package_samples.py.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"D:\Softfors\jup")
SAMPLES = ROOT / "reports" / "figures" / "methodology_diagram_package" / "representative_samples"
OUT = ROOT / "reports" / "figures" / "methodology_diagram_package"

ORDER = ["BUSI", "ISIC", "KUB", "KVASIR"]   # requested montage layout order
TASK_ID = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}
META = {
    "ISIC":   ("ISIC 2018", "dermoscopy (RGB)", "skin lesion"),
    "BUSI":   ("BUSI-WHU", "ultrasound (L->RGB)", "breast lesion"),
    "KVASIR": ("Kvasir-SEG", "endoscopy (RGB)", "colorectal polyp"),
    "KUB":    ("KUB-Stone", "radiograph (L/RGB)", "kidney/bladder/ureteric stone"),
}

PANEL = 320
PAD = 12
LABEL_H = 78
TITLE_H = 34

def _font(sz):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, sz)
        except Exception:
            pass
    return ImageFont.load_default()

def fit(img, box):
    img = img.convert("RGB")
    w, h = img.size
    s = min(box / w, box / h)
    nw, nh = max(1, int(w * s)), max(1, int(h * s))
    r = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", (box, box), (0, 0, 0))
    canvas.paste(r, ((box - nw) // 2, (box - nh) // 2))
    return canvas

def build(panel_filename, title, out_name):
    f_title = _font(20); f_dom = _font(17); f_sub = _font(13)
    cols = len(ORDER)
    W = PAD + cols * (PANEL + PAD)
    H = TITLE_H + PAD + PANEL + LABEL_H + PAD
    canvas = Image.new("RGB", (W, H), (255, 255, 255))
    dr = ImageDraw.Draw(canvas)
    dr.text((PAD, 8), title, fill=(0, 0, 0), font=f_title)
    for i, dom in enumerate(ORDER):
        x = PAD + i * (PANEL + PAD)
        y = TITLE_H + PAD
        p = SAMPLES / dom / panel_filename
        if p.exists():
            tile = fit(Image.open(p), PANEL)
        else:
            tile = Image.new("RGB", (PANEL, PANEL), (230, 230, 230))
        canvas.paste(tile, (x, y))
        full, mod, tgt = META[dom]
        ly = y + PANEL + 4
        dr.text((x, ly), f"{dom}  (task_id={TASK_ID[dom]})", fill=(0, 0, 0), font=f_dom)
        dr.text((x, ly + 20), full, fill=(60, 60, 60), font=f_sub)
        dr.text((x, ly + 35), mod, fill=(60, 60, 60), font=f_sub)
        dr.text((x, ly + 50), f"target: {tgt}", fill=(60, 60, 60), font=f_sub)
    canvas.save(OUT / out_name)
    print("wrote", out_name, canvas.size)

if __name__ == "__main__":
    build("01_input.png", "RA-MedFiLM-BARR - four-domain representative inputs (VAL808, ordinary samples)", "four_domain_input_montage.png")
    build("03_input_gt_overlay.png", "RA-MedFiLM-BARR - four-domain inputs with ground-truth boundaries (red)", "four_domain_input_gt_montage.png")
