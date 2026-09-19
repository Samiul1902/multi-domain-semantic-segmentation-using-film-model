import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

def generate_figures():
    reports_dir = Path("reports/figures/phase14_part3c")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    df_mode = pd.read_csv("reports/tables/phase14_part3_mode_summary.csv")
    df_img = pd.read_csv("reports/tables/phase14_part3_image_metrics.csv")
    df_comp = pd.read_csv("reports/tables/phase14_part3_component_metrics.csv")
    df_runtime = pd.read_csv("reports/tables/phase14_part3_runtime.csv")
    df_hc = pd.read_csv("reports/tables/phase14_part3_hardcase_summary.csv")
    
    # Figure A: Overall Dice Boxplot (Unchanged data, regenerated for freshness)
    plt.figure(figsize=(10, 6))
    dice_data = []
    for mode, pfx in [("GLOBAL_ONLY", "global"), ("ORACLE_REGIONAL", "oracle"), ("PREDICTED_REGIONAL", "predicted")]:
        dice_data.append(pd.DataFrame({
            "Mode": mode,
            "Dice (512-Space)": df_img[f"{pfx}_dice_512"]
        }))
    df_dice = pd.concat(dice_data)
    sns.boxplot(data=df_dice, x="Mode", y="Dice (512-Space)")
    plt.title("Figure A: Overall Dice Coefficient by Mode")
    plt.tight_layout()
    plt.savefig(reports_dir / "figure_A_overall_dice.png", dpi=300)
    plt.close()
    
    # Figure B: Authoritative Object Recall by Stratum
    plt.figure(figsize=(12, 6))
    strata = ["TINY", "SMALL", "MEDIUM", "LARGE"]
    modes = ["GLOBAL_ONLY", "ORACLE_REGIONAL", "PREDICTED_REGIONAL"]
    
    recall_data = []
    for mode in modes:
        for stratum in strata:
            recall = df_mode.loc[df_mode["mode"] == mode, f"object_recall_{stratum.lower()}_512"].iloc[0]
            recall_data.append({"Mode": mode, "Stratum": stratum, "Object Recall": recall})
            
    df_recall = pd.DataFrame(recall_data)
    sns.barplot(data=df_recall, x="Stratum", y="Object Recall", hue="Mode")
    plt.title("Figure B: Component Object Detection Recall by Size Stratum (overlap >= 1 px)")
    plt.ylim(0, 1.05)
    plt.tight_layout()
    plt.savefig(reports_dir / "figure_B_recall_stratum.png", dpi=300)
    plt.close()
    
    # Figure C: False Positives per Image
    plt.figure(figsize=(10, 6))
    fp_data = []
    for mode, pfx in [("GLOBAL_ONLY", "global"), ("ORACLE_REGIONAL", "oracle"), ("PREDICTED_REGIONAL", "predicted")]:
        fp_data.append(pd.DataFrame({
            "Mode": mode,
            "FP Components": df_img[f"{pfx}_fp_components"]
        }))
    df_fp = pd.concat(fp_data)
    sns.boxplot(data=df_fp, x="Mode", y="FP Components")
    plt.title("Figure C: False Positive Components per Image")
    plt.tight_layout()
    plt.savefig(reports_dir / "figure_C_false_positives.png", dpi=300)
    plt.close()
    
    # Figure D: Reconciled Hard-Case Recovery (True Negatives & Missed Targets)
    plt.figure(figsize=(10, 6))
    empty_data = []
    for mode in modes:
        rec = df_hc.loc[df_hc["mode"] == mode, "global_empty_recovered_512"].iloc[0]
        empty_data.append({"Mode": mode, "Empty Images Recovered": rec})
    df_empty = pd.DataFrame(empty_data)
    sns.barplot(data=df_empty, x="Mode", y="Empty Images Recovered")
    plt.title("Figure D: Global-Empty Image Stone Target Recovery (Total = 7)")
    plt.ylim(0, 7.5)
    plt.tight_layout()
    plt.savefig(reports_dir / "figure_D_empty_images.png", dpi=300)
    plt.close()
    
    # Figure E: Proposal Burden
    df_pb = pd.read_csv("reports/tables/phase14_part3_roi_proposal_burden.csv")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    sns.barplot(data=df_pb, x="mode", y="mean_proposals", ax=axes[0])
    axes[0].set_title("Mean Proposals per Image")
    sns.barplot(data=df_pb, x="mode", y="mean_roi_area_fraction", ax=axes[1])
    axes[1].set_title("Mean ROI Area Fraction")
    plt.suptitle("Figure E: ROI Proposal Burden")
    plt.tight_layout()
    plt.savefig(reports_dir / "figure_E_proposal_burden.png", dpi=300)
    plt.close()
    
    # Figure F: Pipeline Component Runtime Stacked Bar
    plt.figure(figsize=(10, 6))
    pred_rt = df_runtime[df_runtime["pipeline"] == "PREDICTED_REGIONAL"].copy()
    pred_rt = pred_rt[pred_rt["component"] != "Total Pipeline"]
    
    plt.bar("PREDICTED_REGIONAL", pred_rt.loc[pred_rt["component"]=="Global UNet++", "mean_ms"].iloc[0], label="Global UNet++")
    bottom = pred_rt.loc[pred_rt["component"]=="Global UNet++", "mean_ms"].iloc[0]
    
    plt.bar("PREDICTED_REGIONAL", pred_rt.loc[pred_rt["component"]=="Stage-4D Localizer", "mean_ms"].iloc[0], bottom=bottom, label="Localizer")
    bottom += pred_rt.loc[pred_rt["component"]=="Stage-4D Localizer", "mean_ms"].iloc[0]
    
    plt.bar("PREDICTED_REGIONAL", pred_rt.loc[pred_rt["component"]=="Regional Refiner UNet", "mean_ms"].iloc[0], bottom=bottom, label="Refiner")
    bottom += pred_rt.loc[pred_rt["component"]=="Regional Refiner UNet", "mean_ms"].iloc[0]
    
    plt.bar("PREDICTED_REGIONAL", pred_rt.loc[pred_rt["component"]=="Aggregation & Fusion", "mean_ms"].iloc[0], bottom=bottom, label="Fusion")
    
    plt.title("Figure F: PREDICTED_REGIONAL Runtime Decomposition")
    plt.ylabel("Mean Time (ms)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(reports_dir / "figure_F_runtime_stacked.png", dpi=300)
    plt.close()
    
    # Figure G: Reconciled Operating Point vs Historical Gate
    plt.figure(figsize=(8, 8))
    plt.scatter([df_mode.loc[df_mode["mode"]=="GLOBAL_ONLY", "mean_dice_512"].iloc[0]], 
                [df_mode.loc[df_mode["mode"]=="GLOBAL_ONLY", "object_recall_tiny_512"].iloc[0]], label="GLOBAL_ONLY", s=120, color='blue')
    plt.scatter([df_mode.loc[df_mode["mode"]=="ORACLE_REGIONAL", "mean_dice_512"].iloc[0]], 
                [df_mode.loc[df_mode["mode"]=="ORACLE_REGIONAL", "object_recall_tiny_512"].iloc[0]], label="ORACLE_REGIONAL", s=120, color='green')
    plt.scatter([df_mode.loc[df_mode["mode"]=="PREDICTED_REGIONAL", "mean_dice_512"].iloc[0]], 
                [df_mode.loc[df_mode["mode"]=="PREDICTED_REGIONAL", "object_recall_tiny_512"].iloc[0]], label="PREDICTED_REGIONAL", s=120, color='orange')
    
    # Plot historical gates
    plt.axvline(x=0.652776, color='r', linestyle='--', label='Historical Dice Gate (0.6528)')
    plt.axhline(y=0.780822, color='b', linestyle='--', label='Historical TINY Recall Gate (0.7808)')
    plt.title("Figure G: Model Operating Point vs Historical Gate (Authoritative Object Recall)")
    plt.xlabel("Mean Dice (512-Space)")
    plt.ylabel("TINY Object Recall (512-Space, overlap >= 1 px)")
    plt.ylim(0.5, 1.05)
    plt.xlim(0.3, 0.9)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(reports_dir / "figure_G_gate_scatter.png", dpi=300)
    plt.close()
    print("Regenerated all Phase-14 Part-3C figures with reconciled metrics.")

if __name__ == "__main__":
    generate_figures()
