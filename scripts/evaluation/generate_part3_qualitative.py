import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Setup paths
reports_dir = Path("reports/figures/phase14_part3c")
reports_dir.mkdir(parents=True, exist_ok=True)
qual_dir = Path("reports/qualitative/phase14_part3c")
qual_dir.mkdir(parents=True, exist_ok=True)

def generate_qualitative():
    # Load image metrics
    df_img = pd.read_csv("reports/tables/phase14_part3_image_metrics.csv")
    
    # Define 4 conditions
    conditions = [
        {"name": "Condition 1: Global Missed, Predicted Improved", "mask": (df_img["global_dice_512"] < 0.1) & (df_img["predicted_dice_512"] > 0.5)},
        {"name": "Condition 2: Hard Tiny Improvement", "mask": (df_img["has_hard_tiny"] == True) & (df_img["predicted_dice_512"] > df_img["global_dice_512"])},
        {"name": "Condition 3: Regional Regression", "mask": (df_img["global_dice_512"] > df_img["predicted_dice_512"] + 0.1)},
        {"name": "Condition 4: Global Empty False Positive", "mask": (df_img["global_empty"] == True) & (df_img["predicted_empty_pred_flag_512"] == False)}
    ]
    
    selected_cases = []
    
    for cond in conditions:
        subset = df_img[cond["mask"]].sort_values("sample_id")
        if len(subset) > 0:
            selected_sample = subset.iloc[0]["sample_id"]
            reason = cond["name"]
        else:
            # Fallback
            subset = df_img.sort_values("sample_id")
            selected_sample = subset.iloc[len(selected_cases) % len(subset)]["sample_id"]
            reason = f"Fallback for {cond['name']}"
        selected_cases.append({"sample_id": selected_sample, "condition": reason})
        
    df_sel = pd.DataFrame(selected_cases)
    df_sel.to_csv("reports/tables/phase14_part3_qualitative_case_selection.csv", index=False)
    print("Saved selection to reports/tables/phase14_part3_qualitative_case_selection.csv")
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    axes = axes.flatten()
    for i, row in enumerate(selected_cases):
        ax = axes[i]
        ax.text(0.5, 0.5, f"{row['sample_id']}\n{row['condition']}", 
                ha='center', va='center', wrap=True)
        ax.set_xticks([])
        ax.set_yticks([])
    plt.tight_layout()
    plt.savefig(qual_dir / "phase14_part3_qualitative_panel.png", dpi=300)
    plt.close()

if __name__ == "__main__":
    generate_qualitative()

