"""
Generate Figure 4 (Internal VAL808) and Figure 5 (External pilot) prediction panels
for the RA-MedFiLM scientific report.

Verified scope of these figures (see reports/audits/c1_external_evidence_v1_0):
- The ONLY network executed is GlobalMedFiLM (checkpoint
  checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt,
  SHA-256 286689fd...5ba1b7, 3,523,001 parameters).
- BARR (R_psi / B_phi / S_omega) is NOT executed here. No route decision record
  exists for any external case, so no figure may assert a BARR action.
- Exactly ONE case per dataset is shown. These are illustrative single cases,
  not dataset-level performance estimates.
- "Presentation label" strings are curated metadata supplied by the analyst.
  They are NOT model outputs and NOT pixelwise subclass predictions.

Panels per row (5 columns):
    1. Input image
    2. Ground-truth mask
    3. Predicted probability map
    4. Predicted segmentation overlay
    5. TP/FP/FN/TN error classification map

Error-map colour key (fixed):
    TP  #00E600  True Positive  - correctly segmented foreground
    FP  #FF2020  False Positive - over-segmented background
    FN  #2060FF  False Negative - missed foreground
    TN  #181818  True Negative  - correctly excluded background

Dice / IoU / precision / recall / specificity / accuracy are computed from the
same prediction and the same ground truth shown in the row.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import json
import numpy as np
import torch
import torchvision.transforms.functional as TF
from PIL import Image, ImageDraw
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from src.models.film.global_medfilm import GlobalMedFiLM

OUT_DIR = Path("paper_doc")
OUT_DIR.mkdir(parents=True, exist_ok=True)

CKPT = "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"
CKPT_SHA256 = "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"

TP_RGB = (0, 230, 0)      # #00E600
FP_RGB = (255, 32, 32)    # #FF2020
FN_RGB = (32, 96, 255)    # #2060FF
TN_RGB = (24, 24, 24)     # #181818


def build_error_matrix(pred_bin: np.ndarray, gt_bin: np.ndarray) -> np.ndarray:
    """RGB error map: TP green, FP red, FN blue, TN charcoal."""
    h, w = pred_bin.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    rgb[pred_bin & gt_bin] = TP_RGB
    rgb[pred_bin & (~gt_bin)] = FP_RGB
    rgb[(~pred_bin) & gt_bin] = FN_RGB
    rgb[(~pred_bin) & (~gt_bin)] = TN_RGB
    return rgb


def compute_advanced_metrics(pred_bin: np.ndarray, gt_bin: np.ndarray) -> dict:
    tp = int((pred_bin & gt_bin).sum())
    fp = int((pred_bin & (~gt_bin)).sum())
    fn = int(((~pred_bin) & gt_bin).sum())
    tn = int(((~pred_bin) & (~gt_bin)).sum())

    dice = (2.0 * tp / (2.0 * tp + fp + fn)) if (2 * tp + fp + fn) > 0 else 1.0
    iou = (float(tp) / (tp + fp + fn)) if (tp + fp + fn) > 0 else 1.0
    prec = (float(tp) / (tp + fp)) if (tp + fp) > 0 else 0.0
    rec = (float(tp) / (tp + fn)) if (tp + fn) > 0 else 0.0
    spec = (float(tn) / (tn + fp)) if (tn + fp) > 0 else 1.0
    acc = (float(tp + tn) / (tp + tn + fp + fn))

    return {
        "dice": dice * 100.0,
        "iou": iou * 100.0,
        "prec": prec * 100.0,
        "rec": rec * 100.0,
        "spec": spec * 100.0,
        "acc": acc * 100.0,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }


def create_panel_figure(
    cases: list[dict],
    title: str,
    subtitle: str,
    out_filename: str,
    footnote: str,
):
    """Render a len(cases) x 5 panel grid.

    Row labels are drawn with fig.text at a fixed left anchor inside a widened
    left margin. The previous implementation used Axes.set_ylabel with a large
    labelpad, which pushed the multi-line label off the canvas so that the case
    identity, metrics and status were unreadable in the published PNG.
    """
    n = len(cases)
    fig = plt.figure(figsize=(21, 4.1 * n + 2.0), dpi=300)
    plt.subplots_adjust(top=0.90, bottom=0.13, left=0.215, right=0.985,
                        hspace=0.34, wspace=0.14)

    fig.suptitle(title, fontsize=16, fontweight="bold", y=0.975, color="#1e3d59")
    fig.text(0.5, 0.945, subtitle, fontsize=10, ha="center", style="italic", color="#555555")

    col_headers = [
        "Column 1\nInput Image",
        "Column 2\nGround Truth Mask",
        "Column 3\nPrediction Probability Map",
        "Column 4\nPredicted Segmentation Overlay\n(Yellow = Predicted Region)",
        "Column 5\nError Classification\n(TP / FP / FN / TN)",
    ]

    for r_idx, c_data in enumerate(cases):
        m = c_data["metrics"]

        # Row label: identity + metrics + explicit provenance of the label text.
        row_label = (
            f"{c_data['class_name']}\n"
            f"Presentation label (analyst metadata,\n"
            f"not a model output): {c_data['presentation_label']}\n"
            f"Case: {c_data['case_id']}\n"
            f"--------------------------------\n"
            f"Dice {m['dice']:.2f}%  |  IoU {m['iou']:.2f}%\n"
            f"Prec {m['prec']:.2f}%  |  Recall {m['rec']:.2f}%\n"
            f"Spec {m['spec']:.2f}%  |  Acc {m['acc']:.2f}%\n"
            f"TP {m['tp']:,}  FP {m['fp']:,}  FN {m['fn']:,}"
        )

        # Col 1: input image
        ax1 = fig.add_subplot(n, 5, r_idx * 5 + 1)
        ax1.imshow(c_data["img"])
        ax1.set_xticks([]); ax1.set_yticks([])
        if r_idx == 0:
            ax1.set_title(col_headers[0], fontsize=10.5, fontweight="bold", pad=8)
        pos = ax1.get_position()
        fig.text(0.012, (pos.y0 + pos.y1) / 2, row_label, fontsize=8.0,
                 ha="left", va="center", family="DejaVu Sans", linespacing=1.45)

        # Col 2: ground truth
        ax2 = fig.add_subplot(n, 5, r_idx * 5 + 2)
        ax2.imshow(c_data["gt"], cmap="gray", vmin=0, vmax=1)
        ax2.set_xticks([]); ax2.set_yticks([])
        if r_idx == 0:
            ax2.set_title(col_headers[1], fontsize=10.5, fontweight="bold", pad=8)
        ax2.set_xlabel(f"GT area: {m['tp'] + m['fn']:,} px", fontsize=8.5, labelpad=4)

        # Col 3: probability map
        ax3 = fig.add_subplot(n, 5, r_idx * 5 + 3)
        ax3.imshow(c_data["prob"], cmap="plasma", vmin=0.0, vmax=1.0)
        ax3.set_xticks([]); ax3.set_yticks([])
        if r_idx == 0:
            ax3.set_title(col_headers[2], fontsize=10.5, fontweight="bold", pad=8)
        ax3.set_xlabel("Sigmoid confidence [0, 1]", fontsize=8.5, labelpad=4)

        # Col 4: predicted overlay
        ax4 = fig.add_subplot(n, 5, r_idx * 5 + 4)
        overlay = np.array(c_data["img"]).copy()
        pred_bin = c_data["pred"]
        overlay[pred_bin] = (0.5 * overlay[pred_bin] + 0.5 * np.array([255, 230, 0])).astype(np.uint8)
        ax4.imshow(overlay)
        ax4.set_xticks([]); ax4.set_yticks([])
        if r_idx == 0:
            ax4.set_title(col_headers[3], fontsize=10.5, fontweight="bold", pad=8)
        ax4.set_xlabel(f"Pred area: {m['tp'] + m['fp']:,} px", fontsize=8.5, labelpad=4)

        # Col 5: error map
        ax5 = fig.add_subplot(n, 5, r_idx * 5 + 5)
        ax5.imshow(build_error_matrix(pred_bin, c_data["gt"]))
        ax5.set_xticks([]); ax5.set_yticks([])
        if r_idx == 0:
            ax5.set_title(col_headers[4], fontsize=10.5, fontweight="bold", pad=8)
        ax5.set_xlabel(f"TP {m['tp']:,} | FP {m['fp']:,} | FN {m['fn']:,}",
                       fontsize=8.5, labelpad=4, fontweight="bold")

    legend_elements = [
        mpatches.Patch(facecolor="#00e600", edgecolor="black", label="TP  True Positive (#00E600)"),
        mpatches.Patch(facecolor="#ff2020", edgecolor="black", label="FP  False Positive (#FF2020)"),
        mpatches.Patch(facecolor="#2060ff", edgecolor="black", label="FN  False Negative (#2060FF)"),
        mpatches.Patch(facecolor="#181818", edgecolor="black", label="TN  True Negative (#181818)"),
    ]
    fig.legend(handles=legend_elements, loc="lower center", ncol=4, fontsize=10,
               frameon=True, facecolor="#f9f9f9", edgecolor="#cccccc",
               title="Pixel error classification key", title_fontsize=10,
               bbox_to_anchor=(0.5, 0.055))

    fig.text(0.012, 0.012, footnote, fontsize=7.6, ha="left", va="bottom",
             color="#444444", style="italic")

    save_path = OUT_DIR / out_filename
    fig.savefig(save_path, dpi=300)
    plt.close(fig)
    print(f"Successfully generated {save_path.resolve()}")


def generate_all():
    print("Loading GlobalMedFiLM checkpoint...")
    model = GlobalMedFiLM()
    ckpt = torch.load(CKPT, map_location="cpu", weights_only=False)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    n_params = sum(p.numel() for p in model.parameters())
    assert n_params == 3523001, n_params
    print(f"  params={n_params}  (Global FiLM only; BARR not loaded)")

    def infer(img_path, task_id):
        img_pil = Image.open(img_path).convert("RGB").resize((512, 512), Image.Resampling.BILINEAR)
        tensor = TF.to_tensor(img_pil).unsqueeze(0)
        with torch.no_grad():
            prob = torch.sigmoid(model(tensor, torch.tensor([task_id], dtype=torch.long))).squeeze().cpu().numpy()
        return img_pil, prob, (prob > 0.5)

    def gt_std(mask_path):
        return (np.array(Image.open(mask_path).convert("L").resize((512, 512), Image.Resampling.NEAREST)) > 127)

    # ------------------------------------------------------------------
    # Figure 4: internal VAL808 (all four cases verified present in
    # manifests/phase4_v3/val.csv; none in train.csv)
    # ------------------------------------------------------------------
    O = "D:/Softfors/omni_seg/data_raw"
    internal_meta = [
        dict(class_name="ISIC 2018  (dermoscopy)", presentation_label="pigmented lesion",
             task_id=0,
             img=f"{O}/isic2018/ISIC2018_Task1-2_Training_Input/ISIC_0013798.jpg",
             mask=f"{O}/isic2018/ISIC2018_Task1_Training_GroundTruth/ISIC_0013798_segmentation.png",
             case_id="ISIC_0013798"),
        dict(class_name="BUSI  (breast ultrasound)", presentation_label="hypoechoic mass",
             task_id=1,
             img=f"{O}/BUSI_WHU Breast Cancer Ultrasound Image  Dataset/BUSI-WHU/img/00170.bmp",
             mask=f"{O}/BUSI_WHU Breast Cancer Ultrasound Image  Dataset/BUSI-WHU/gt/00170_anno.bmp",
             case_id="00170.bmp"),
        dict(class_name="Kvasir-SEG  (GI endoscopy)", presentation_label="colorectal polyp",
             task_id=2,
             img=f"{O}/Kvasir-SEG/images/cju1alwgo30z60855fm3y23sm.jpg",
             mask=f"{O}/Kvasir-SEG/masks/cju1alwgo30z60855fm3y23sm.jpg",
             case_id="cju1alwgo30z..."),
        dict(class_name="KUB-StoneX  (abdominal radiograph)", presentation_label="bladder calculus",
             task_id=3,
             img=f"{O}/KUB-Stone/KUB-Stonex/Bladder_Stone/Images/00001-00-2500001.png",
             mask=f"{O}/KUB-Stone/KUB-Stonex/Bladder_Stone/Masks/00001-00-2500001_mask.png",
             case_id="00001-00-2500001", kub_binary=True),
    ]

    internal_cases = []
    for item in internal_meta:
        img_pil, prob, pred = infer(item["img"], item["task_id"])
        if item.get("kub_binary"):
            raw = np.array(Image.open(item["mask"]))
            gt = (np.array(Image.fromarray((raw > 0).astype(np.uint8) * 255)
                           .resize((512, 512), Image.Resampling.NEAREST)) > 0)
        else:
            gt = gt_std(item["mask"])
        internal_cases.append(dict(
            class_name=item["class_name"], presentation_label=item["presentation_label"],
            case_id=item["case_id"], img=np.array(img_pil), gt=gt, prob=prob, pred=pred,
            metrics=compute_advanced_metrics(pred, gt)))

    create_panel_figure(
        cases=internal_cases,
        title="Figure 4: Single-case predictions and pixel error breakdown on the internal validation cohort (VAL808)",
        subtitle="Four illustrative cases, one per modality. Global MedFiLM only. Not a dataset-level performance estimate.",
        out_filename="fig4_internal_4domain_predictions.png",
        footnote=("Model: GlobalMedFiLM, 3,523,001 parameters, checkpoint SHA-256 "
                  f"{CKPT_SHA256[:16]}...   |   All four cases verified present in the VAL808 split "
                  "(manifests/phase4_v3/val.csv); none is a TRAIN sample.\n"
                  "n = 1 case per modality \u2014 illustrative only, not a dataset-level performance estimate.   |   "
                  "Presentation labels are analyst metadata, not model outputs."),
    )

    # ------------------------------------------------------------------
    # Figure 5: external pilot
    # ------------------------------------------------------------------
    E = "D:/Softfors/final/external_test_ds"
    external_cases = []

    img_pil, prob, pred = infer(f"{E}/HAM10000/images/ISIC_0024306.jpg", 0)
    gt = gt_std(f"{E}/HAM10000/masks/ISIC_0024306.png")
    external_cases.append(dict(
        class_name="HAM10000 / ISIC-2018 Task 3  (dermoscopy)",
        presentation_label="melanocytic naevus (NV) per dataset label",
        case_id="ISIC_0024306", img=np.array(img_pil), gt=gt, prob=prob, pred=pred,
        metrics=compute_advanced_metrics(pred, gt)))

    img_pil, prob, pred = infer(f"{E}/CVC-ClinicDB/PNG/Original/1.png", 2)
    gt = gt_std(f"{E}/CVC-ClinicDB/PNG/Ground Truth/1.png")
    external_cases.append(dict(
        class_name="CVC-ClinicDB  (GI endoscopy)",
        presentation_label="colonic polyp (frame 1)",
        case_id="1.png", img=np.array(img_pil), gt=gt, prob=prob, pred=pred,
        metrics=compute_advanced_metrics(pred, gt)))

    img_pil, prob, pred = infer(f"{E}/BrEaST-Lesions_USG-images_and_masks/case001.png", 1)
    gt = gt_std(f"{E}/BrEaST-Lesions_USG-images_and_masks/case001_tumor.png")
    external_cases.append(dict(
        class_name="BrEaST-Lesions-USG  (breast ultrasound)",
        presentation_label="breast lesion (case 001)",
        case_id="case001.png", img=np.array(img_pil), gt=gt, prob=prob, pred=pred,
        metrics=compute_advanced_metrics(pred, gt)))

    coco = json.loads(Path(f"{E}/Stones_where_are_you-.v3i.coco-segmentation/test/_annotations.coco.json").read_text())
    ann = [a for a in coco["annotations"] if a["category_id"] == 7 and a["image_id"] == 3][0]
    info = [im for im in coco["images"] if im["id"] == 3][0]
    m_img = Image.new("L", (info["width"], info["height"]), 0)
    poly = [(ann["segmentation"][0][i], ann["segmentation"][0][i + 1])
            for i in range(0, len(ann["segmentation"][0]), 2)]
    ImageDraw.Draw(m_img).polygon(poly, outline=1, fill=1)
    gt = (np.array(m_img.resize((512, 512), Image.Resampling.NEAREST)) > 0)
    img_pil, prob, pred = infer(
        f"{E}/Stones_where_are_you-.v3i.coco-segmentation/test/{info['file_name']}", 3)
    external_cases.append(dict(
        class_name="Stones_where_are_you? v3  (abdominal radiograph)",
        presentation_label="radio-opaque calculus (COCO category 7)",
        case_id=info["file_name"][:18] + "...", img=np.array(img_pil), gt=gt, prob=prob, pred=pred,
        metrics=compute_advanced_metrics(pred, gt)))

    create_panel_figure(
        cases=external_cases,
        title="Figure 5: Single-case zero-shot predictions and pixel error breakdown on external datasets",
        subtitle=("Four illustrative cases, one per dataset, from the external pilot. Global MedFiLM only \u2014 "
                  "no BARR routing, refiner or safety gate was executed, so no BARR decision is shown."),
        out_filename="fig5_external_4domain_predictions.png",
        footnote=("Model: GlobalMedFiLM, 3,523,001 parameters \u2014 no BARR component was loaded or executed.   |   "
                  "n = 1 case per dataset: illustrative only, and MUST NOT be read as dataset-level external validation.\n"
                  "HAM10000 here is the ISIC-2018 Task 3 archive, which ships no segmentation masks; the mask used has "
                  "undocumented provenance, so its Dice is not a verified external score.   |   "
                  "Presentation labels are analyst metadata, not model outputs."),
    )


if __name__ == "__main__":
    generate_all()
