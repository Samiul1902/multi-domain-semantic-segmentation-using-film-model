import pathlib

p = pathlib.Path(r"D:\Softfors\jup\full_doc_report\Scripts\build_figures.py")
s = p.read_text(encoding="utf-8")

start = s.index("# ============================================================ segmentation ====")
end = s.index("# ==================================================== external evaluation ====")

new = '''# ============================================================ segmentation ====
def _img_from_gt(gt_path: str, domain: str) -> Path | None:
    s = gt_path
    if domain == "ISIC":
        c = s.replace("_segmentation.png", ".jpg") \\
             .replace("Task1_Training_GroundTruth", "Task1-2_Training_Input") \\
             .replace("Task1_Validation_GroundTruth", "Task1-2_Validation_Input") \\
             .replace("Task1_Test_GroundTruth", "Task1-2_Test_Input")
    elif domain == "BUSI":
        c = s.replace("\\\\gt\\\\", "\\\\img\\\\").replace("_anno.bmp", ".bmp")
    elif domain == "KVASIR":
        c = s.replace("\\\\masks\\\\", "\\\\images\\\\")
    else:
        c = s.replace("\\\\Masks\\\\", "\\\\Images\\\\").replace("_mask.png", ".png")
    q = Path(c)
    return q if q.exists() else None


def _fit512(img: np.ndarray) -> np.ndarray:
    """Aspect-preserving resize + centre pad, matching the frozen contract."""
    from PIL import Image as I
    h, w = img.shape[:2]
    sc = 512.0 / max(h, w)
    nh, nw = max(1, int(round(h * sc))), max(1, int(round(w * sc)))
    im = I.fromarray(img).resize((nw, nh), I.BILINEAR)
    out = np.zeros((512, 512, 3), dtype=np.uint8)
    y0, x0 = (512 - nh) // 2, (512 - nw) // 2
    out[y0:y0 + nh, x0:x0 + nw] = np.array(im)
    return out


def _overlay(img512, gt, pred):
    vis = img512.copy().astype(np.float32)
    tp = gt & pred
    fp = (~gt) & pred
    fn = gt & (~pred)
    vis[tp] = vis[tp] * 0.45 + np.array([0, 158, 115]) * 0.55
    vis[fp] = vis[fp] * 0.35 + np.array([213, 94, 0]) * 0.65
    vis[fn] = vis[fn] * 0.45 + np.array([0, 114, 178]) * 0.55
    return np.clip(vis, 0, 255).astype(np.uint8)


SEG_SELECTION: list[dict] = []


def _panel_figure(dom, picks, tag, title, filename, caption):
    """6-column gallery: image | GT | global | FULL | TP/FP/FN | metrics."""
    preds = {r["sample_id"]: r for r in load_csv(
        ROOT / "reports/tables/phase27_val808_predictions.csv")}
    man = {r["sample_id"]: r for r in load_csv(
        ROOT / "reports/tables/phase21_prediction_manifest.csv")}
    ps = {r["sample_id"]: r for r in load_csv(TABLES / "REMEDFILM_INTERNAL_PER_SAMPLE.csv")}

    fig, axes = plt.subplots(len(picks), 6, figsize=(12.4, 2.05 * len(picks)),
                             gridspec_kw={"width_ratios": [1, 1, 1, 1, 1, 0.95]})
    if len(picks) == 1:
        axes = np.array([axes])
    heads = ["Image", "Ground truth", "GlobalMedFiLM", "ReMedFiLM FULL",
             "TP / FP / FN", "Metrics"]
    for j, h in enumerate(heads):
        axes[0, j].set_title(h, fontsize=7.2)

    for i, sid in enumerate(picks):
        r = preds[sid]
        gt_p = Path(man[sid]["gt_mask_path"])
        img_p = _img_from_gt(str(gt_p), dom)
        if img_p is None:
            continue
        img512 = _fit512(np.array(Image.open(img_p).convert("RGB")))
        with np.load(ROOT / man[sid]["npz_path"]) as z:
            gt = z["gt"] > 0
        gm = np.array(Image.open(ROOT / r["global_mask_path"]).convert("L")) > 0
        fm = np.array(Image.open(ROOT / r["final_mask_path"]).convert("L")) > 0
        if gm.shape != (512, 512):
            gm = np.array(Image.fromarray(gm.astype(np.uint8) * 255)
                          .resize((512, 512), Image.NEAREST)) > 0
            fm = np.array(Image.fromarray(fm.astype(np.uint8) * 255)
                          .resize((512, 512), Image.NEAREST)) > 0

        panels = [img512,
                  np.repeat((gt * 255)[..., None], 3, 2),
                  np.repeat((gm * 255)[..., None], 3, 2),
                  np.repeat((fm * 255)[..., None], 3, 2),
                  _overlay(img512, gt, fm)]
        for j, pnl in enumerate(panels):
            axes[i, j].imshow(pnl)
            axes[i, j].set_xticks([])
            axes[i, j].set_yticks([])
            axes[i, j].grid(False)

        d0 = float(ps[sid]["global_dice"])
        d1 = float(ps[sid]["final_dice"])
        iou1 = float(ps[sid]["final_iou"])
        hd = ps[sid]["final_hd95"]
        br = r["state_machine_branch"].replace("_", " ").lower()
        txt = (f"sample {sid[:10]}\\n"
               f"G Dice {d0:.4f}\\n"
               f"R Dice {d1:.4f}\\n"
               f"$\\\\Delta$ {d1 - d0:+.4f}\\n"
               f"R IoU {iou1:.4f}\\n"
               f"R HD95 {float(hd):.1f} px\\n"
               f"{br}")
        ax = axes[i, 5]
        ax.axis("off")
        ax.text(0.02, 0.5, txt, fontsize=5.6, va="center", family="DejaVu Sans Mono")
        axes[i, 0].set_ylabel(dom, fontsize=7)

        SEG_SELECTION.append({
            "figure": filename, "panel": tag, "row": i + 1, "domain": dom,
            "sample_id": sid, "branch": r["state_machine_branch"],
            "global_dice": round(d0, 6), "final_dice": round(d1, 6),
            "delta_dice": round(d1 - d0, 6),
            "final_iou": round(iou1, 6),
            "final_hd95": (round(float(hd), 4) if hd not in ("", None) else ""),
            "source_image": str(img_p),
            "gt_mask": str(gt_p),
            "global_mask": r["global_mask_path"],
            "final_mask": r["final_mask_path"],
        })

    fig.suptitle(title, fontsize=9)
    fig.tight_layout()
    save(fig, "segmentation", filename, "SAVED_PREDICTIONS_VAL808", caption, "08/09",
         ["reports/tables/phase27_val808_predictions.csv",
          "reports/predictions/phase21_global_medfilm_fourdomain_seed42_clean_v3/",
          "full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv"])


def fig_segmentation() -> None:
    ps = {r["sample_id"]: r for r in load_csv(TABLES / "REMEDFILM_INTERNAL_PER_SAMPLE.csv")}
    man = {r["sample_id"]: r for r in load_csv(
        ROOT / "reports/tables/phase21_prediction_manifest.csv")}

    for dom in ("ISIC", "BUSI", "KVASIR", "KUB"):
        ids = [s for s, r in ps.items() if r["domain"] == dom and s in man]
        if len(ids) < 6:
            continue
        ids.sort(key=lambda s: float(ps[s]["delta_dice"]))
        picks = [ids[0], ids[len(ids) // 2], ids[-1]]  # worst, median, best
        _panel_figure(
            dom, picks, "worst/median/best",
            f"{dom} — deterministic selection: worst / median / best $\\\\Delta$ Dice "
            f"(not cherry-picked)",
            f"SEG_{dom}_global_vs_full",
            f"{dom}: original, ground truth, backbone mask, FULL mask, TP/FP/FN "
            f"overlay and per-sample metrics for the worst, median and best paired "
            f"improvement.")

    # A second gallery proving FULL differs from the backbone when refinement is accepted.
    for dom in ("ISIC", "BUSI", "KVASIR", "KUB"):
        acc = [s for s, r in ps.items()
               if r["domain"] == dom and r["branch"] == "EXECUTE_THEN_ACCEPT"]
        if not acc:
            continue
        acc.sort(key=lambda s: float(ps[s]["delta_dice"]))
        pick = [acc[len(acc) // 2]]  # median accepted refinement
        _panel_figure(
            dom, pick, "accepted refinement",
            f"{dom} — refinement ACCEPTED by the safety gate: FULL differs from the backbone",
            f"SEG_{dom}_refinement_accepted",
            f"{dom}: a single accepted refinement showing the FULL mask diverging "
            f"from the backbone mask. This is the visual proof that ReMedFiLM FULL is "
            f"not a relabelled GlobalMedFiLM output.")

    # Failure montage
    harm = sorted(ps.values(), key=lambda r: float(r["delta_dice"]))[:6]
    preds = {r["sample_id"]: r for r in load_csv(
        ROOT / "reports/tables/phase27_val808_predictions.csv")}
    fig, axes = plt.subplots(2, 6, figsize=(11.0, 4.0))
    for j, r in enumerate(harm):
        sid = r["sample_id"]
        if sid not in preds or sid not in man:
            continue
        dom = r["domain"]
        gt_p = Path(man[sid]["gt_mask_path"])
        img_p = _img_from_gt(str(gt_p), dom)
        if img_p is None:
            continue
        img512 = _fit512(np.array(Image.open(img_p).convert("RGB")))
        with np.load(ROOT / man[sid]["npz_path"]) as z:
            gt = z["gt"] > 0
        fm = np.array(Image.open(ROOT / preds[sid]["final_mask_path"])
                      .convert("L").resize((512, 512), Image.NEAREST)) > 0
        axes[0, j].imshow(img512)
        axes[0, j].set_title(dom, fontsize=7)
        axes[0, j].set_xticks([]); axes[0, j].set_yticks([])
        axes[1, j].imshow(_overlay(img512, gt, fm))
        axes[1, j].set_xlabel(f"$\\\\Delta$ {float(r['delta_dice']):+.3f}", fontsize=6)
        axes[1, j].set_xticks([]); axes[1, j].set_yticks([])
        SEG_SELECTION.append({
            "figure": "SEG_failure_cases", "panel": "harmful", "row": j + 1,
            "domain": dom, "sample_id": sid, "branch": r["branch"],
            "global_dice": round(float(r["global_dice"]), 6),
            "final_dice": round(float(r["final_dice"]), 6),
            "delta_dice": round(float(r["delta_dice"]), 6),
            "final_iou": round(float(r["final_iou"]), 6),
            "final_hd95": (round(float(r["final_hd95"]), 4)
                           if r["final_hd95"] not in ("", None) else ""),
            "source_image": str(img_p), "gt_mask": str(gt_p),
            "global_mask": preds[sid]["global_mask_path"],
            "final_mask": preds[sid]["final_mask_path"],
        })
    fig.suptitle("Worst six refinements by $\\\\Delta$ Dice — genuine failure cases",
                 fontsize=9)
    fig.tight_layout()
    save(fig, "segmentation", "SEG_failure_cases", "SAVED_PREDICTIONS_VAL808",
         "The six largest negative Delta Dice cases; the safety gate accepted these, "
         "so they are genuine residual failures.", "09",
         ["full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv"])

    import csv as _csv
    with (TABLES / "REMEDFILM_SEGMENTATION_SELECTION.csv").open("w", newline="",
                                                               encoding="utf-8") as fh:
        w = _csv.DictWriter(fh, fieldnames=list(SEG_SELECTION[0].keys()))
        w.writeheader()
        w.writerows(SEG_SELECTION)
    print(f"    segmentation selection rows: {len(SEG_SELECTION)}")


'''

s = s[:start] + new + s[end:]
p.write_text(s, encoding="utf-8")
print("PATCHED segmentation")
