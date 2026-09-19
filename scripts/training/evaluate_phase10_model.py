"""Finalize one trained Phase-10 model on the complete VAL split only."""
import argparse, datetime, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import yaml
from PIL import Image, ImageOps
from scipy.ndimage import label

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from src.data.kub_dataset import KUBDataset
from src.data.transforms import SegmentationTransform
from src.metrics.object_metrics import object_metrics
from src.metrics.segmentation import binary_metrics, hd95
from src.models.factory import create_model
from src.utils.checkpointing import load_training_checkpoint
from src.utils.experiment import register_experiment
from src.utils.manifest_guard import verify_manifests
from src.utils.test_lock import verify_test_lock


def save_table(frame, path):
    frame.to_csv(path, index=False)
    headers = [str(column) for column in frame.columns]
    markdown = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    markdown.extend("| " + " | ".join(str(value) for value in row) + " |" for row in frame.itertuples(index=False, name=None))
    path.with_suffix(".md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    path.with_suffix(".tex").write_text(frame.to_latex(index=False), encoding="utf-8")


def summarize_group(frame, key):
    rows = []
    for value, group in frame.groupby(key):
        gt = int(group.gt_component_count.sum()); detected = int(group.detected_gt_components.sum())
        rows.append({key: value, "N_Samples": len(group), "Macro_Dice": group.dice.mean(),
                     "Macro_IoU": group.iou.mean(), "Macro_Precision": group.precision.mean(),
                     "Macro_Recall": group.recall.mean(), "Empty_Prediction_Rate": group.empty_prediction.mean(),
                     "Object_Recall": detected / gt, "FP_Components_Per_Image": group.false_positive_components.mean()})
    return pd.DataFrame(rows)


def evaluate(model_key):
    verify_manifests(); verify_test_lock(ROOT)
    config = yaml.safe_load((ROOT / "configs/kub/phase10_baselines.yaml").read_text(encoding="utf-8"))
    spec = next(x for x in config["models"] if x["key"] == model_key)
    exp_dir = ROOT / "experiments" / spec["experiment_id"]
    checkpoint_dir = ROOT / "checkpoints" / spec["experiment_id"]
    tables = ROOT / "reports/tables"; device = torch.device("cuda")
    summary_path = exp_dir / "summary.json"; experiment = json.loads(summary_path.read_text(encoding="utf-8"))
    model = create_model(model_key, in_channels=1, out_channels=1, base_channels=32).to(device)
    best = load_training_checkpoint(checkpoint_dir / "best.pt", model, restore_rng=False, map_location=device)
    model.eval()
    dataset = KUBDataset(ROOT / "manifests/val.csv", "VAL", SegmentationTransform(512, False),
                         tables / "kub_val_samples_sized.csv")
    source_components = pd.read_csv(tables / "kub_val_components_sized.csv")
    image_rows, component_rows = [], []
    for index in range(len(dataset)):
        item = dataset[index]; image = item["image"].unsqueeze(0).to(device); target = item["mask"].unsqueeze(0).to(device)
        with torch.no_grad(), torch.amp.autocast("cuda", enabled=True): logits = model(image)
        prediction = (torch.sigmoid(logits).squeeze().cpu().numpy() >= 0.5).astype(np.uint8)
        ground_truth = (item["mask"].squeeze().numpy() > 0).astype(np.uint8)
        metrics = binary_metrics(logits, target, 0.5); distance = hd95(prediction, ground_truth)
        objects = object_metrics(prediction, ground_truth, 1)
        tp = int(np.sum((prediction > 0) & (ground_truth > 0)))
        fp = int(np.sum((prediction > 0) & (ground_truth == 0))); fn = int(np.sum((prediction == 0) & (ground_truth > 0)))
        image_rows.append({"sample_id": item["sample_id"], "patient_id": item["patient_id"],
                           "category": item["category"], "view_type": item["view_type"],
                           "original_component_count": int(item["component_count"]),
                           "dice": metrics["dice"].item(), "iou": metrics["iou"].item(),
                           "precision": metrics["precision"].item(), "recall": metrics["recall"].item(),
                           "hd95": distance["hd95"], "hd95_valid": distance["hd95_valid"],
                           "empty_prediction": distance["empty_prediction"], "hd95_invalid_reason": distance["invalid_reason"],
                           "predicted_component_count": objects["predicted_component_count"],
                           "gt_evaluation_component_count": objects["gt_component_count"],
                           "detected_gt_components": objects["detected_gt_components"],
                           "missed_gt_components": objects["missed_gt_components"],
                           "false_positive_components": objects["false_positive_predicted_components"],
                           "true_positive_pixels": tp, "false_positive_pixels": fp, "false_negative_pixels": fn})
        with Image.open(item["mask_path"]) as mask_file: original_gt = np.asarray(mask_file.convert("L")) > 0
        original_labels, original_n = label(original_gt, structure=np.ones((3, 3)))
        source = source_components[source_components.sample_id == item["sample_id"]].sort_values("component_id")
        if original_n != len(source): raise RuntimeError(f"Original component mismatch: {item['sample_id']}")
        left, top, right, bottom = [int(x) for x in item["padding"].tolist()]
        resized_width, resized_height = 512 - left - right, 512 - top - bottom
        for component_id in range(1, original_n + 1):
            component_image = Image.fromarray((original_labels == component_id).astype(np.uint8) * 255)
            component_image = component_image.resize((resized_width, resized_height), Image.Resampling.NEAREST)
            component_image = ImageOps.expand(component_image, (left, top, right, bottom))
            resized = np.asarray(component_image) > 0; overlap = int(np.sum((prediction > 0) & resized))
            row = source.iloc[component_id - 1]
            component_rows.append({"sample_id": item["sample_id"], "patient_id": item["patient_id"],
                                   "category": item["category"], "view_type": item["view_type"],
                                   "original_component_id": component_id, "kub_size_v1_stratum": row["size_stratum"],
                                   "original_component_pixels": int(row["component_pixels"]),
                                   "original_component_ratio": float(row["component_ratio"]),
                                   "resized_component_pixels": int(resized.sum()), "detected": overlap >= 1,
                                   "overlap_pixels": overlap})
    images, components = pd.DataFrame(image_rows), pd.DataFrame(component_rows)
    stem = f"phase10_{model_key}"
    images.to_csv(tables / f"{stem}_val_per_image.csv", index=False)
    components.to_csv(tables / f"{stem}_val_per_component.csv", index=False)
    total_tp, total_fp, total_fn = images[["true_positive_pixels", "false_positive_pixels", "false_negative_pixels"]].sum()
    valid_hd = images.loc[images.hd95_valid, "hd95"]
    val_summary = pd.DataFrame([{"N_Samples": len(images), "Macro_Dice": images.dice.mean(), "Macro_IoU": images.iou.mean(),
        "Macro_Precision": images.precision.mean(), "Macro_Recall": images.recall.mean(),
        "Micro_Dice": 2*total_tp/(2*total_tp+total_fp+total_fn), "Micro_IoU": total_tp/(total_tp+total_fp+total_fn),
        "HD95_Valid_N": int(images.hd95_valid.sum()), "HD95_Invalid_N": int((~images.hd95_valid).sum()),
        "Empty_Predictions_N": int(images.empty_prediction.sum()), "Empty_Prediction_Rate": images.empty_prediction.mean(),
        "Median_Valid_HD95": valid_hd.median(), "Mean_Valid_HD95": valid_hd.mean()}])
    renamed = images.rename(columns={"gt_evaluation_component_count": "gt_component_count"})
    fov = summarize_group(renamed, "view_type").rename(columns={"view_type": "View_Type"})
    category = summarize_group(renamed, "category").rename(columns={"category": "Category"})
    ff_components = components[components.view_type == "FULL_FIELD"]
    size = ff_components.groupby("kub_size_v1_stratum").detected.agg(["size", "sum", "mean"]).reset_index()
    size.columns = ["Stratum", "Original_GT_Components", "Detected_Components", "Object_Recall"]

    gt = int(images.gt_evaluation_component_count.sum()); detected = int(images.detected_gt_components.sum())
    obj = pd.DataFrame([{"Evaluation_GT_Components": gt, "Predicted_Components": int(images.predicted_component_count.sum()),
        "Detected_GT_Components": detected, "Missed_GT_Components": int(images.missed_gt_components.sum()),
        "Object_Recall": detected/gt, "Missed_Object_Rate": int(images.missed_gt_components.sum())/gt,
        "False_Positive_Components": int(images.false_positive_components.sum()),
        "FP_Components_Per_Image": images.false_positive_components.mean()}])
    detection = components.groupby("sample_id").detected.agg(["sum", "count"])
    ff = images[images.view_type == "FULL_FIELD"].join(detection, on="sample_id")
    ff["Component_Group"] = np.where(ff.original_component_count > 1, "MULTI_COMPONENT", "SINGLE_COMPONENT")
    multi = ff.groupby("Component_Group").agg(N_Images=("sample_id", "size"), Macro_Dice=("dice", "mean"),
        Original_GT_Components=("count", "sum"), Detected_Original_Components=("sum", "sum")).reset_index()
    multi["Object_Recall"] = multi.Detected_Original_Components / multi.Original_GT_Components
    multi["Missed_Object_Rate"] = 1 - multi.Object_Recall
    for frame, suffix in ((val_summary,"val_summary"),(fov,"fov_summary"),(category,"category_summary"),
                          (size,"size_summary"),(obj,"object_summary"),(multi,"multicomponent_summary")):
        save_table(frame, tables / f"{stem}_{suffix}.csv")
    experiment.update(status="COMPLETED", best_epoch=int(best["epoch"]), validation_metrics=val_summary.iloc[0].to_dict(),
                      fov_metrics=fov.to_dict("records"), category_metrics=category.to_dict("records"),
                      size_metrics=size.to_dict("records"), object_metrics=obj.iloc[0].to_dict(),
                      multicomponent_metrics=multi.to_dict("records"), evaluation_space="512x512",
                      size_component_space="original", test_accessed=False)
    summary_path.write_text(json.dumps(experiment, indent=2), encoding="utf-8")
    register_experiment(registry_record_from_summary(spec, experiment), ROOT)
    print(json.dumps({"model": model_key, "macro_dice": val_summary.Macro_Dice.iloc[0], "best_epoch": best["epoch"]}))


def registry_record_from_summary(spec, summary):
    return {"experiment_id": spec["experiment_id"], "phase": 10, "dataset": "KUB", "split_scope": "TRAIN/VAL",
        "model": spec["key"], "architecture": spec["architecture"], "seed": 42, "image_size": 512,
        "batch_size": summary["physical_batch"], "effective_batch_size": summary["effective_batch"], "optimizer": "AdamW",
        "learning_rate": 1e-4, "weight_decay": 1e-4, "scheduler": "CosineAnnealingLR", "loss": "0.5_BCE+0.5_Dice",
        "threshold": 0.5, "manifest_version": "phase4_v2", "status": "COMPLETED", "start_time": "",
        "end_time": datetime.datetime.now(datetime.timezone.utc).isoformat(), "checkpoint_path": summary["best_checkpoint"],
        "best_val_dice": summary["best_val_dice_checkpoint_selection"], "git_commit": "",
        "notes": "Phase 10 fair baseline completed; VAL-only evaluation"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--model", required=True,
        choices=["attention_unet", "unetpp", "deeplabv3plus"]); evaluate(parser.parse_args().model)
