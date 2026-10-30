"""
Build source-derived SCHEMATIC diagrams for the methodology diagram evidence
package. These are drawn ONLY from frozen source constants/schemas.

GOVERNANCE: no model execution, no forward, no CUDA. Pure drawing from text/config.

Outputs (into existing_visual_references/):
  * global_medfilm_structure.png       (G block schematic)
  * pre_refinement_202d_feature_breakdown.png
  * post_safety_20d_breakdown.png
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"D:\Softfors\jup\reports\figures\methodology_diagram_package\existing_visual_references")
OUT.mkdir(parents=True, exist_ok=True)

def F(sz, bold=False):
    for name in (("arialbd.ttf" if bold else "arial.ttf"), "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, sz)
        except Exception:
            pass
    return ImageFont.load_default()

BLUE = (66, 133, 244); DARK = (30, 30, 30); GREY = (240, 240, 240)
GREEN = (76, 175, 80); ORANGE = (245, 152, 30); PURPLE = (150, 90, 190)
BORD = (120, 120, 120)

def box(dr, xy, text, fill, tcol=(255, 255, 255), fs=15, bold=True, wrap=None):
    x0, y0, x1, y1 = xy
    dr.rounded_rectangle(xy, radius=8, fill=fill, outline=BORD, width=2)
    f = F(fs, bold)
    lines = text.split("\n")
    total = len(lines) * (fs + 4)
    ty = (y0 + y1) / 2 - total / 2 + 2
    for ln in lines:
        w = dr.textlength(ln, font=f)
        dr.text(((x0 + x1) / 2 - w / 2, ty), ln, fill=tcol, font=f)
        ty += fs + 4

def arrow(dr, p, q, col=DARK, w=3):
    dr.line([p, q], fill=col, width=w)
    import math
    ang = math.atan2(q[1] - p[1], q[0] - p[0])
    L = 12
    for da in (math.radians(150), math.radians(-150)):
        dr.line([q, (q[0] + L * math.cos(ang + da), q[1] + L * math.sin(ang + da))], fill=col, width=w)

def global_medfilm():
    W, H = 1180, 760
    im = Image.new("RGB", (W, H), (255, 255, 255)); dr = ImageDraw.Draw(im)
    dr.text((30, 22), "GlobalMedFiLM (G) - shared residual U-Net + 5 FiLM task-conditioning sites", fill=DARK, font=F(21, True))
    dr.text((30, 52), "ARCHITECTURE_ID = global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1   |   params = 3,523,001   |   source: src/models/film/global_medfilm.py", fill=(90, 90, 90), font=F(12))
    # encoder (left column)
    enc = [("encoder1  24ch", 220), ("encoder2  48ch", 285), ("encoder3  96ch", 350), ("encoder4  192ch", 415)]
    for lab, y in enc:
        box(dr, (60, y, 250, y + 48), lab, BLUE, fs=14)
    box(dr, (60, 480, 250, 540), "bridge  256ch\n(FiLM site)", GREEN, fs=14)
    # decoder (right column), reversed
    dec = [("decoder4  192ch\n(FiLM site)", 220), ("decoder3  96ch\n(FiLM site)", 285), ("decoder2  48ch\n(FiLM site)", 350), ("decoder1  24ch\n(FiLM site)", 415)]
    for lab, y in dec:
        box(dr, (470, y, 660, y + 48), lab, BLUE, fs=12)
    # head
    box(dr, (470, 480, 660, 540), "shared 1x1 conv head\n-> logits [1,H,W]", ORANGE, fs=12)
    # skip connections
    for i, y in enumerate([220, 285, 350, 415]):
        arrow(dr, (250, y + 24), (470, y + 24), (150, 150, 150), 2)
    dr.text((300, 188), "skip connections", fill=(130, 130, 130), font=F(12))
    # task conditioning
    box(dr, (880, 120, 1130, 190), "task_id (int, 0..3)\nnn.Embedding(4, 32)", PURPLE, fs=13)
    box(dr, (880, 215, 1130, 300), "FiLM:  F_hat = (1+gamma)*F + beta\ngamma,beta = tanh(W e + b),  hidden=64\n5 sites: bridge, decoder4..1", PURPLE, fs=12)
    arrow(dr, (1005, 190), (1005, 215), DARK, 3)
    for y in (244, 309, 374, 439, 504):
        arrow(dr, (880, y), (660, y), PURPLE, 2)
    # fix the FiLM->head arrow: draw only to the FiLM-affected sites, not the head
    dr.rectangle((655, 504, 665, 545), fill=(255,255,255), outline=(255,255,255))
    dr.text((690, 555), "task conditioning enters ONLY through FiLM (no concat, no per-domain head)", fill=PURPLE, font=F(12, True))
    # io
    box(dr, (60, 620, 380, 690), "input: image [3, 512, 512] float [0,1]", GREY, DARK, fs=13)
    box(dr, (470, 620, 790, 690), "output: global logits -> p_global = sigmoid(logits)", GREY, DARK, fs=13)
    arrow(dr, (220, 620), (160, 268), BLUE, 2)
    arrow(dr, (565, 540), (565, 620), ORANGE, 2)
    im.save(OUT / "global_medfilm_structure.png"); print("global_medfilm_structure.png", im.size)

def f202():
    W, H = 1180, 560
    im = Image.new("RGB", (W, H), (255, 255, 255)); dr = ImageDraw.Draw(im)
    dr.text((30, 20), "Pre-refinement feature vector (202-D) - B_phi numeric input", fill=DARK, font=F(21, True))
    dr.text((30, 50), "source: data_cache/phase25b_barr_pre_refinement_features_v1_2/feature_group_offsets.json", fill=(90, 90, 90), font=F(12))
    groups = [
        ("bridge_global", 0, 32, BLUE), ("bridge_roi", 32, 64, (100, 150, 240)),
        ("decoder2_global", 64, 96, GREEN), ("decoder2_roi", 96, 128, (120, 200, 120)),
        ("decoder1_global", 128, 160, ORANGE), ("decoder1_roi", 160, 192, (250, 180, 90)),
        ("scalars (10)", 192, 202, PURPLE),
    ]
    x = 40; y = 110; scale = 4.4
    for name, a, b, col in groups:
        w = (b - a) * scale
        if name.startswith("scalars"):
            w = 110  # give the small group a readable fixed width
        box(dr, (x, y, x + w, y + 90), f"{name}\n[{a}:{b}]", col, fs=11)
        x += w + 6
    dr.text((40, 220), "deep = 192  (6 groups x 32: taps {bridge, decoder2, decoder1} x scopes {GLOBAL, ROI})   +   scalars = 10", fill=DARK, font=F(14, True))
    dr.text((40, 250), "numeric_dim = 202", fill=DARK, font=F(15, True))
    scal = ["entropy_proxy_mean", "frac_prob_within_0p05_of_boundary", "frac_prob_within_0p02_of_boundary",
            "mean_boundary_margin", "pred_foreground_fraction", "pred_foreground_pixels",
            "pred_roi_exists", "pred_empty", "predicted_roi_area_fraction", "predicted_roi_side"]
    box(dr, (40, 300, 1140, 520), "scalar order (indices 192-201):\n  " + "\n  ".join(f"{192+i}  {n}" for i, n in enumerate(scal)), PURPLE, fs=13, bold=False)
    im.save(OUT / "pre_refinement_202d_feature_breakdown.png"); print("pre_refinement_202d_feature_breakdown.png", im.size)

def f20():
    W, H = 1180, 620
    im = Image.new("RGB", (W, H), (255, 255, 255)); dr = ImageDraw.Draw(im)
    dr.text((30, 20), "S_omega input (20-D) = 16-D normalized numeric + 4-D task one-hot", fill=DARK, font=F(21, True))
    dr.text((30, 50), "source: reports/tables/phase25f_feature_schema_v1_0.csv ; SOMEGA_FINAL_INPUT_DIM=20", fill=(90, 90, 90), font=F(12))
    box(dr, (40, 100, 780, 250), "16-D numeric (indices 0-15), normalized FIT-only (ddof=0)\n"
        "0 global_prob_mean      1 refined_prob_mean\n2 mean_abs_prob_change   3 max_abs_prob_change\n"
        "4 frac_abs_prob_change_ge_0p10   5 global_entropy_mean\n6 refined_entropy_mean   7 global_foreground_fraction\n"
        "8 refined_foreground_fraction   9 binary_xor_fraction\n10 global_component_count   11 refined_component_count\n"
        "12 global_boundary_fraction   13 refined_boundary_fraction\n14 predicted_roi_area_fraction   15 predicted_roi_side_normalized",
        BLUE, fs=12, bold=False)
    box(dr, (820, 100, 1140, 250), "4-D task one-hot (16-19)\n\n16 task_0_ISIC\n17 task_1_BUSI\n18 task_2_KVASIR\n19 task_3_KUB", GREEN, fs=13)
    box(dr, (40, 300, 1140, 360), "concat  ->  20-D vector  ->  BARRPostSafetyV1 MLP (20 -> 32 -> 16 -> 1)  ->  scalar safety logit", ORANGE, fs=15)
    box(dr, (40, 400, 1140, 460), "ACCEPT iff sigmoid(logit) >= 0.50   (equivalently logit >= 0.0)", (200, 60, 60), fs=15)
    dr.text((40, 490), "no normalization layers inside S_omega (standard PyTorch Linear init)", fill=(90, 90, 90), font=F(13))
    im.save(OUT / "post_safety_20d_breakdown.png"); print("post_safety_20d_breakdown.png", im.size)

if __name__ == "__main__":
    global_medfilm(); f202(); f20()
