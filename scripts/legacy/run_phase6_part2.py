import os
import json
import hashlib
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image, ImageDraw

from src.analysis.kub_characterization import analyze_kub_mask

PROJECT_ROOT = Path(r'D:\Softfors\jup')
MANIFEST_DIR = PROJECT_ROOT / 'manifests'
TABLES_DIR = PROJECT_ROOT / 'reports' / 'tables'
FIGURES_DIR = PROJECT_ROOT / 'reports' / 'figures' / 'kub_characterization'
QUAL_DIR = PROJECT_ROOT / 'reports' / 'qualitative' / 'kub_characterization'
AUDIT_DIR = PROJECT_ROOT / 'reports' / 'audits'

df_samples = pd.read_csv(TABLES_DIR / 'kub_train_sample_characteristics.csv')
df_components = pd.read_csv(TABLES_DIR / 'kub_train_components.csv')

colors = {'Kidney_Stone': '#1f77b4', 'Bladder_Stone': '#ff7f0e', 'Ureteric_Stone': '#2ca02c'}

# 1. Patient Summary Table
pat_summary = df_samples.groupby('patient_id').agg(
    samples=('sample_id', 'count'),
    categories=('category', lambda x: ','.join(sorted(x.unique()))),
    med_fg_ratio=('foreground_ratio', 'median'),
    mean_component_count=('component_count', 'mean'),
    max_component_count=('component_count', 'max'),
    max_obj_pixels=('largest_component_pixels', 'max'),
    min_obj_pixels=('smallest_component_pixels', 'min')
).reset_index()
pat_summary.to_csv(TABLES_DIR / 'kub_train_patient_summary.csv', index=False)

# 2. Category Characteristics Table
cat_rows = []
for cat, grp in df_samples.groupby('category'):
    cat_comps = df_components[df_components['category'] == cat]
    cat_rows.append({
        'Category': cat,
        'Samples': len(grp),
        'Patients': grp['patient_id'].nunique(),
        'FG_Ratio_Mean': grp['foreground_ratio'].mean(),
        'FG_Ratio_Median': grp['foreground_ratio'].median(),
        'FG_Ratio_IQR': grp['foreground_ratio'].quantile(0.75) - grp['foreground_ratio'].quantile(0.25),
        'BBox_Ratio_Median': grp['bbox_ratio'].median(),
        'Component_Count_Mean': grp['component_count'].mean(),
        'Component_Count_Max': grp['component_count'].max(),
        'Component_Size_Median_Pixels': cat_comps['component_pixels'].median(),
        'Component_Size_Mean_Pixels': cat_comps['component_pixels'].mean()
    })
df_cat_char = pd.DataFrame(cat_rows)
df_cat_char.to_csv(TABLES_DIR / 'kub_category_characteristics.csv', index=False)

# 4. Foreground & Component Summary Tables
fg_stats = pd.DataFrame([
    {'Metric': 'Min', 'FG_Pixels': df_samples['foreground_pixels'].min(), 'FG_Ratio': df_samples['foreground_ratio'].min()},
    {'Metric': 'Q1', 'FG_Pixels': df_samples['foreground_pixels'].quantile(0.25), 'FG_Ratio': df_samples['foreground_ratio'].quantile(0.25)},
    {'Metric': 'Median', 'FG_Pixels': df_samples['foreground_pixels'].median(), 'FG_Ratio': df_samples['foreground_ratio'].median()},
    {'Metric': 'Mean', 'FG_Pixels': df_samples['foreground_pixels'].mean(), 'FG_Ratio': df_samples['foreground_ratio'].mean()},
    {'Metric': 'Q3', 'FG_Pixels': df_samples['foreground_pixels'].quantile(0.75), 'FG_Ratio': df_samples['foreground_ratio'].quantile(0.75)},
    {'Metric': 'Max', 'FG_Pixels': df_samples['foreground_pixels'].max(), 'FG_Ratio': df_samples['foreground_ratio'].max()}
])
fg_stats.to_csv(TABLES_DIR / 'kub_train_foreground_statistics.csv', index=False)

comp_stats = pd.DataFrame([
    {'Metric': 'Min', 'Comp_Pixels': df_components['component_pixels'].min(), 'Comp_Ratio': df_components['component_ratio'].min()},
    {'Metric': 'Q1', 'Comp_Pixels': df_components['component_pixels'].quantile(0.25), 'Comp_Ratio': df_components['component_ratio'].quantile(0.25)},
    {'Metric': 'Median', 'Comp_Pixels': df_components['component_pixels'].median(), 'Comp_Ratio': df_components['component_ratio'].median()},
    {'Metric': 'Mean', 'Comp_Pixels': df_components['component_pixels'].mean(), 'Comp_Ratio': df_components['component_ratio'].mean()},
    {'Metric': 'Q3', 'Comp_Pixels': df_components['component_pixels'].quantile(0.75), 'Comp_Ratio': df_components['component_ratio'].quantile(0.75)},
    {'Metric': 'Max', 'Comp_Pixels': df_components['component_pixels'].max(), 'Comp_Ratio': df_components['component_ratio'].max()}
])
comp_stats.to_csv(TABLES_DIR / 'kub_train_component_statistics.csv', index=False)

# 5. Train vs Val Distribution Summary
val_df = pd.read_csv(MANIFEST_DIR / 'val.csv')
kub_val = val_df[val_df['dataset'] == 'KUB'].copy()
val_samples = []
for _, row in kub_val.iterrows():
    res = analyze_kub_mask(row['mask_path'], connectivity=8)
    val_samples.append({
        'sample_id': row['sample_id'],
        'category': row['category'],
        'foreground_ratio': res['foreground_ratio'],
        'component_count': res['component_count']
    })
df_val_samples = pd.DataFrame(val_samples)

tv_summary = pd.DataFrame([
    {'Split': 'TRAIN', 'Samples': len(df_samples), 'Patients': df_samples['patient_id'].nunique(),
     'FG_Ratio_Median': df_samples['foreground_ratio'].median(), 'Comp_Count_Mean': df_samples['component_count'].mean()},
    {'Split': 'VAL', 'Samples': len(df_val_samples), 'Patients': kub_val['patient_id'].nunique(),
     'FG_Ratio_Median': df_val_samples['foreground_ratio'].median(), 'Comp_Count_Mean': df_val_samples['component_count'].mean()}
])
tv_summary.to_csv(TABLES_DIR / 'kub_train_val_distribution_summary.csv', index=False)

# --- FIGURE GENERATION (300 DPI PNG & SVG) ---

# Figure A: Category Composition
plt.figure(figsize=(7, 5))
ax = sns.barplot(x='category', y='sample_id', data=df_samples.groupby('category')['sample_id'].count().reset_index(), palette=colors)

# Figure B: Foreground Ratio Distribution by Category
plt.figure(figsize=(8, 5))
sns.boxplot(x='category', y='foreground_ratio', data=df_samples, palette=colors)
plt.yscale('log')
plt.title('KUB Train Foreground Ratio Distribution by Category (Log Scale)', fontsize=12, fontweight='bold')
plt.xlabel('Anatomical Stone Category', fontsize=10)
plt.ylabel('Foreground Ratio (Target / Image Area)', fontsize=10)
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'kub_foreground_ratio_by_category.png', dpi=300)
plt.savefig(FIGURES_DIR / 'kub_foreground_ratio_by_category.svg')
plt.close()

# Figure C: Component Size Distribution
plt.figure(figsize=(8, 5))
sns.histplot(data=df_components, x='component_ratio', hue='category', element='step', log_scale=True, palette=colors)
plt.title('KUB Train Connected Component Size Ratio Distribution (n=2687)', fontsize=12, fontweight='bold')
plt.xlabel('Component Area / Image Area Ratio (Log Scale)', fontsize=10)
plt.ylabel('Component Count', fontsize=10)
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'kub_component_size_distribution.png', dpi=300)
plt.savefig(FIGURES_DIR / 'kub_component_size_distribution.svg')
plt.close()

# Figure D: Components Per Image
plt.figure(figsize=(7, 5))
sns.countplot(x='component_count', data=df_samples, color='#2b5c8f')
plt.title('KUB Train Connected Components per Image (n=1979)', fontsize=12, fontweight='bold')
plt.xlabel('Number of Foreground Components', fontsize=10)
plt.ylabel('Image Count', fontsize=10)
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'kub_components_per_image.png', dpi=300)
plt.savefig(FIGURES_DIR / 'kub_components_per_image.svg')
plt.close()

# Figure E: Component Spatial Centroid Distribution
plt.figure(figsize=(7, 6))
for cat, grp in df_components.groupby('category'):
    plt.scatter(grp['centroid_x_norm'], grp['centroid_y_norm'], alpha=0.4, label=cat, color=colors[cat], s=15)
plt.gca().invert_yaxis()
plt.title('KUB Train Object Centroid Spatial Distribution (Normalized Coordinates)', fontsize=12, fontweight='bold')
plt.xlabel('Normalized X (0 = Left, 1 = Right)', fontsize=10)
plt.ylabel('Normalized Y (0 = Top, 1 = Bottom)', fontsize=10)
plt.legend(title='Category', loc='upper right')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'kub_component_centroids.png', dpi=300)
plt.savefig(FIGURES_DIR / 'kub_component_centroids.svg')
plt.close()

# Figure F: Train vs Val Distribution Comparison
df_samples_cp = df_samples.copy()
df_samples_cp['split'] = 'TRAIN'
df_val_samples['split'] = 'VAL'
combined_tv = pd.concat([df_samples_cp[['foreground_ratio', 'split']], df_val_samples[['foreground_ratio', 'split']]])

plt.figure(figsize=(7, 5))
sns.kdeplot(data=combined_tv, x='foreground_ratio', hue='split', common_norm=False, log_scale=True, fill=True, alpha=0.3)
plt.title('KUB Train vs Validation Foreground Ratio Density Comparison', fontsize=12, fontweight='bold')
plt.xlabel('Foreground Ratio (Log Scale)', fontsize=10)
plt.ylabel('Density', fontsize=10)
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'kub_train_val_distribution.png', dpi=300)
plt.savefig(FIGURES_DIR / 'kub_train_val_distribution.svg')
plt.close()

print("Saved all 6 publication figures and summary tables successfully.")

plt.title('KUB Train Segmentation Sample Distribution by Category (n=1979)', fontsize=12, fontweight='bold')
plt.xlabel('Anatomical Stone Category', fontsize=10)
plt.ylabel('Sample Count', fontsize=10)
for p in ax.patches:
    ax.annotate(f'{int(p.get_height())}', (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center', va='bottom', fontsize=10, xytext=(0, 3), textcoords='offset points')
plt.tight_layout()
plt.savefig(FIGURES_DIR / 'kub_category_composition.png', dpi=300)
plt.savefig(FIGURES_DIR / 'kub_category_composition.svg')
plt.close()


# 3. Overall Dataset Summary
ds_summary = pd.DataFrame([
    {'Statistic': 'Total Samples', 'Value': len(df_samples)},
    {'Statistic': 'Total Patients', 'Value': df_samples['patient_id'].nunique()},
    {'Statistic': 'Mean Image Width', 'Value': df_samples['width'].mean()},
    {'Statistic': 'Mean Image Height', 'Value': df_samples['height'].mean()},
    {'Statistic': 'Median Foreground Ratio', 'Value': df_samples['foreground_ratio'].median()},
    {'Statistic': 'Total Connected Components', 'Value': len(df_components)},
    {'Statistic': 'Mean Components / Image', 'Value': df_samples['component_count'].mean()},
    {'Statistic': 'Max Components in 1 Image', 'Value': df_samples['component_count'].max()}
])
ds_summary.to_csv(TABLES_DIR / 'kub_dataset_summary.csv', index=False)
