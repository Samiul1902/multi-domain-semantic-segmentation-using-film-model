import os
import json
import hashlib
import time
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image, ImageDraw

from src.analysis.kub_characterization import analyze_kub_mask_v2

PROJECT_ROOT = Path(r'D:\Softfors\jup')
MANIFEST_DIR = PROJECT_ROOT / 'manifests'
TABLES_DIR = PROJECT_ROOT / 'reports' / 'tables'
FIGURES_DIR = PROJECT_ROOT / 'reports' / 'figures' / 'kub_characterization'
QUAL_DIR = PROJECT_ROOT / 'reports' / 'qualitative' / 'kub_characterization'
AUDIT_DIR = PROJECT_ROOT / 'reports' / 'audits'

TABLES_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
QUAL_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
colors = {'Kidney_Stone': '#1f77b4', 'Bladder_Stone': '#ff7f0e', 'Ureteric_Stone': '#2ca02c'}

# Load Manifests
train_df = pd.read_csv(MANIFEST_DIR / 'train.csv')
val_df = pd.read_csv(MANIFEST_DIR / 'val.csv')

kub_train = train_df[train_df['dataset'] == 'KUB'].copy()
kub_val = val_df[val_df['dataset'] == 'KUB'].copy()

assert len(kub_train) == 1979, f"Expected 1979 KUB TRAIN samples, got {len(kub_train)}"
assert len(kub_val) == 283, f"Expected 283 KUB VAL samples, got {len(kub_val)}"

# 1. Analyze TRAIN Samples
sample_records = []
component_records = []

for _, row in kub_train.iterrows():
    res = analyze_kub_mask_v2(row['mask_path'], connectivity=8)
    comp_list = res.pop('components')
    
    c_pixels = [c['component_pixels'] for c in comp_list]
    largest_c_pixels = max(c_pixels) if c_pixels else 0
    smallest_c_pixels = min(c_pixels) if c_pixels else 0
    median_c_pixels = float(np.median(c_pixels)) if c_pixels else 0.0
    
    sample_rec = {
        'sample_id': row['sample_id'],
        'patient_id': row['patient_id'],
        'category': row['category'],
        'image_path': row['image_path'],
        'mask_path': row['mask_path'],
        'width': res['width'],
        'height': res['height'],
        'aspect_ratio': res['aspect_ratio'],
        'foreground_pixels': res['foreground_pixels'],
        'foreground_ratio': res['foreground_ratio'],
        'bbox_width': res['bbox_width'],
        'bbox_height': res['bbox_height'],
        'bbox_area': res['bbox_area'],
        'bbox_ratio': res['bbox_ratio'],
        'component_count': res['component_count'],
        'largest_component_pixels': largest_c_pixels,
        'largest_component_ratio': largest_c_pixels / (res['width'] * res['height']),
        'smallest_component_pixels': smallest_c_pixels,
        'smallest_component_ratio': smallest_c_pixels / (res['width'] * res['height']),
        'median_component_pixels': median_c_pixels
    }
    sample_records.append(sample_rec)
    
    for c in comp_list:
        c_rec = {
            'sample_id': row['sample_id'],
            'patient_id': row['patient_id'],
            'category': row['category'],
            **c
        }
        component_records.append(c_rec)

df_samples = pd.DataFrame(sample_records)
df_components = pd.DataFrame(component_records)
df_samples.to_csv(TABLES_DIR / 'kub_train_sample_characteristics_v2.csv', index=False)
df_components.to_csv(TABLES_DIR / 'kub_train_components_v2.csv', index=False)


# 2. Analyze VAL Samples
val_sample_records = []
for _, row in kub_val.iterrows():
    res = analyze_kub_mask_v2(row['mask_path'], connectivity=8)
    val_sample_records.append({
        'sample_id': row['sample_id'],
        'patient_id': row['patient_id'],
        'category': row['category'],
        'image_path': row['image_path'],
        'mask_path': row['mask_path'],
        'width': res['width'],
        'height': res['height'],
        'aspect_ratio': res['aspect_ratio'],
        'foreground_pixels': res['foreground_pixels'],
        'foreground_ratio': res['foreground_ratio'],
        'bbox_width': res['bbox_width'],
        'bbox_height': res['bbox_height'],
        'bbox_area': res['bbox_area'],
        'bbox_ratio': res['bbox_ratio'],
        'component_count': res['component_count']
    })

df_val_samples = pd.DataFrame(val_sample_records)
assert (df_val_samples['component_count'] >= 1).all(), "Found empty VAL mask!"
df_val_samples.to_csv(TABLES_DIR / 'kub_val_sample_characteristics_v2.csv', index=False)

# 3. Patient Summary Table
pat_summary = df_samples.groupby('patient_id').agg(
    samples=('sample_id', 'count'),
    categories=('category', lambda x: ','.join(sorted(x.unique()))),
    med_fg_ratio=('foreground_ratio', 'median'),
    mean_component_count=('component_count', 'mean'),
    max_component_count=('component_count', 'max'),
    max_obj_pixels=('largest_component_pixels', 'max'),
    min_obj_pixels=('smallest_component_pixels', 'min')
).reset_index()
pat_summary.to_csv(TABLES_DIR / 'kub_train_patient_summary_v2.csv', index=False)

# 4. Category Characteristics Table
cat_rows = []
for cat in ['Kidney_Stone', 'Bladder_Stone', 'Ureteric_Stone']:
    grp = df_samples[df_samples['category'] == cat]
    cat_comps = df_components[df_components['category'] == cat]
    cat_rows.append({
        'Category': cat,
        'Samples': len(grp),
        'Patients': grp['patient_id'].nunique(),
        'FG_Ratio_Min': grp['foreground_ratio'].min(),
        'FG_Ratio_Q1': grp['foreground_ratio'].quantile(0.25),
        'FG_Ratio_Median': grp['foreground_ratio'].median(),
        'FG_Ratio_Mean': grp['foreground_ratio'].mean(),
        'FG_Ratio_Q3': grp['foreground_ratio'].quantile(0.75),
        'FG_Ratio_Max': grp['foreground_ratio'].max(),
        'FG_Ratio_IQR': grp['foreground_ratio'].quantile(0.75) - grp['foreground_ratio'].quantile(0.25),
        'BBox_Ratio_Median': grp['bbox_ratio'].median(),
        'Component_Count_Mean': grp['component_count'].mean(),
        'Component_Count_Max': grp['component_count'].max(),
        'Component_Size_Median_Pixels': cat_comps['component_pixels'].median(),
        'Component_Size_Mean_Pixels': cat_comps['component_pixels'].mean()
    })
df_cat_char = pd.DataFrame(cat_rows)
df_cat_char.to_csv(TABLES_DIR / 'kub_category_characteristics_v2.csv', index=False)

# 5. Overall Dataset Summary Table
ds_summary = pd.DataFrame([
    {'Statistic': 'Total TRAIN Samples', 'Value': len(df_samples)},
    {'Statistic': 'Total TRAIN Patients', 'Value': df_samples['patient_id'].nunique()},
    {'Statistic': 'Image Width (Min / Median / Max)', 'Value': f"{df_samples['width'].min()} / {int(df_samples['width'].median())} / {df_samples['width'].max()}"},
    {'Statistic': 'Image Height (Min / Median / Max)', 'Value': f"{df_samples['height'].min()} / {int(df_samples['height'].median())} / {df_samples['height'].max()}"},
    {'Statistic': 'Foreground Ratio (Min / Median / Max)', 'Value': f"{df_samples['foreground_ratio'].min():.6f} / {df_samples['foreground_ratio'].median():.6f} / {df_samples['foreground_ratio'].max():.6f}"},
    {'Statistic': 'Total Connected Components (8-connectivity)', 'Value': len(df_components)},
    {'Statistic': 'Mean Components / Image', 'Value': df_samples['component_count'].mean()},
    {'Statistic': 'Max Components in 1 Image', 'Value': df_samples['component_count'].max()}
])
ds_summary.to_csv(TABLES_DIR / 'kub_dataset_summary_v2.csv', index=False)

# 6. Foreground & Component Summary Tables
fg_stats = pd.DataFrame([
    {'Metric': 'Min', 'FG_Pixels': df_samples['foreground_pixels'].min(), 'FG_Ratio': df_samples['foreground_ratio'].min()},
    {'Metric': 'Q1', 'FG_Pixels': df_samples['foreground_pixels'].quantile(0.25), 'FG_Ratio': df_samples['foreground_ratio'].quantile(0.25)},
    {'Metric': 'Median', 'FG_Pixels': df_samples['foreground_pixels'].median(), 'FG_Ratio': df_samples['foreground_ratio'].median()},
    {'Metric': 'Mean', 'FG_Pixels': df_samples['foreground_pixels'].mean(), 'FG_Ratio': df_samples['foreground_ratio'].mean()},
    {'Metric': 'Q3', 'FG_Pixels': df_samples['foreground_pixels'].quantile(0.75), 'FG_Ratio': df_samples['foreground_ratio'].quantile(0.75)},
    {'Metric': 'Max', 'FG_Pixels': df_samples['foreground_pixels'].max(), 'FG_Ratio': df_samples['foreground_ratio'].max()}
])
fg_stats.to_csv(TABLES_DIR / 'kub_train_foreground_statistics_v2.csv', index=False)

comp_stats = pd.DataFrame([
    {'Metric': 'Min', 'Comp_Pixels': df_components['component_pixels'].min(), 'Comp_Ratio': df_components['component_ratio'].min()},
    {'Metric': 'Q1', 'Comp_Pixels': df_components['component_pixels'].quantile(0.25), 'Comp_Ratio': df_components['component_ratio'].quantile(0.25)},
    {'Metric': 'Median', 'Comp_Pixels': df_components['component_pixels'].median(), 'Comp_Ratio': df_components['component_ratio'].median()},
    {'Metric': 'Mean', 'Comp_Pixels': df_components['component_pixels'].mean(), 'Comp_Ratio': df_components['component_ratio'].mean()},
    {'Metric': 'Q3', 'Comp_Pixels': df_components['component_pixels'].quantile(0.75), 'Comp_Ratio': df_components['component_ratio'].quantile(0.75)},
    {'Metric': 'Max', 'Comp_Pixels': df_components['component_pixels'].max(), 'Comp_Ratio': df_components['component_ratio'].max()}
])
comp_stats.to_csv(TABLES_DIR / 'kub_train_component_statistics_v2.csv', index=False)

# 7. Train vs Val Distribution Summary Table
tv_summary = pd.DataFrame([
    {'Split': 'TRAIN', 'Samples': len(df_samples), 'Patients': df_samples['patient_id'].nunique(),
     'FG_Ratio_Min': df_samples['foreground_ratio'].min(), 'FG_Ratio_Median': df_samples['foreground_ratio'].median(), 'FG_Ratio_Max': df_samples['foreground_ratio'].max(),
     'Comp_Count_Mean': df_samples['component_count'].mean()},
    {'Split': 'VAL', 'Samples': len(df_val_samples), 'Patients': kub_val['patient_id'].nunique(),
     'FG_Ratio_Min': df_val_samples['foreground_ratio'].min(), 'FG_Ratio_Median': df_val_samples['foreground_ratio'].median(), 'FG_Ratio_Max': df_val_samples['foreground_ratio'].max(),
     'Comp_Count_Mean': df_val_samples['component_count'].mean()}
])
tv_summary.to_csv(TABLES_DIR / 'kub_train_val_distribution_summary_v2.csv', index=False)

print("Saved all v2 tables.")

assert len(pat_summary) == 318, f"Expected 318 TRAIN patients, got {len(pat_summary)}"

# --- FIGURE GENERATION (PNG 300 DPI, SVG, PDF) ---

# Figure A: Category Composition
fig, ax = plt.subplots(figsize=(7, 5))
cat_df = df_samples.groupby('category')['sample_id'].count().reset_index()
sns.barplot(x='category', y='sample_id', data=cat_df, hue='category', palette=colors, legend=False, ax=ax)
ax.set_title('KUB Train Segmentation Sample Distribution by Category (n=1979)', fontsize=12, fontweight='bold')
ax.set_xlabel('Anatomical Stone Category', fontsize=10)
ax.set_ylabel('Sample Count', fontsize=10)
for p in ax.patches:
    ax.annotate(f'{int(p.get_height())}', (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center', va='bottom', fontsize=10, xytext=(0, 3), textcoords='offset points')
plt.tight_layout()
for ext in ['png', 'svg', 'pdf']:
    plt.savefig(FIGURES_DIR / f'kub_category_composition_v2.{ext}', dpi=300)
plt.close()

# Figure B: Foreground Ratio Distribution by Category
fig, ax = plt.subplots(figsize=(8, 5))
sns.boxplot(x='category', y='foreground_ratio', data=df_samples, hue='category', palette=colors, legend=False, ax=ax)
ax.set_yscale('log')
ax.set_title('KUB Train Foreground Ratio Distribution by Category (Log Scale)', fontsize=12, fontweight='bold')
ax.set_xlabel('Anatomical Stone Category', fontsize=10)
ax.set_ylabel('Foreground Ratio (Target / Image Area)', fontsize=10)
plt.tight_layout()
for ext in ['png', 'svg', 'pdf']:
    plt.savefig(FIGURES_DIR / f'kub_foreground_ratio_by_category_v2.{ext}', dpi=300)
plt.close()

# Figure C: Component Size Distribution
fig, ax = plt.subplots(figsize=(8, 5))
sns.histplot(data=df_components, x='component_ratio', hue='category', element='step', log_scale=True, palette=colors, ax=ax)
ax.set_title(f'KUB Train Connected Component Size Ratio Distribution (n={len(df_components)})', fontsize=12, fontweight='bold')
ax.set_xlabel('Component Area / Image Area Ratio (Log Scale)', fontsize=10)
ax.set_ylabel('Component Count', fontsize=10)
plt.tight_layout()
for ext in ['png', 'svg', 'pdf']:
    plt.savefig(FIGURES_DIR / f'kub_component_size_distribution_v2.{ext}', dpi=300)
plt.close()


# Figure D: Components Per Image
fig, ax = plt.subplots(figsize=(7, 5))
sns.countplot(x='component_count', data=df_samples, color='#2b5c8f', ax=ax)
ax.set_title('KUB Train Connected Components per Image (n=1979)', fontsize=12, fontweight='bold')
ax.set_xlabel('Number of Foreground Components', fontsize=10)
ax.set_ylabel('Image Count', fontsize=10)
for p in ax.patches:
    ax.annotate(f'{int(p.get_height())}', (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center', va='bottom', fontsize=10, xytext=(0, 3), textcoords='offset points')
plt.tight_layout()
for ext in ['png', 'svg', 'pdf']:
    plt.savefig(FIGURES_DIR / f'kub_components_per_image_v2.{ext}', dpi=300)
plt.close()

# Figure E: Component Spatial Centroid Distribution
fig, ax = plt.subplots(figsize=(7, 6))
for cat, grp in df_components.groupby('category'):
    ax.scatter(grp['centroid_x_norm'], grp['centroid_y_norm'], alpha=0.4, label=cat, color=colors[cat], s=15)
ax.invert_yaxis()
ax.set_title('KUB Train Object Centroid Spatial Distribution (Normalized Coordinates)', fontsize=12, fontweight='bold')
ax.set_xlabel('Normalized X (0 = Left, 1 = Right)', fontsize=10)
ax.set_ylabel('Normalized Y (0 = Top, 1 = Bottom)', fontsize=10)
ax.legend(title='Category', loc='upper right')
plt.tight_layout()
for ext in ['png', 'svg', 'pdf']:
    plt.savefig(FIGURES_DIR / f'kub_component_centroids_v2.{ext}', dpi=300)
plt.close()

# Figure F: Train vs Val Distribution Comparison
df_samples_cp = df_samples.copy()
df_samples_cp['split'] = 'TRAIN'
df_val_samples_cp = df_val_samples.copy()
df_val_samples_cp['split'] = 'VAL'
combined_tv = pd.concat([df_samples_cp[['foreground_ratio', 'split']], df_val_samples_cp[['foreground_ratio', 'split']]])

fig, ax = plt.subplots(figsize=(7, 5))
sns.kdeplot(data=combined_tv, x='foreground_ratio', hue='split', common_norm=False, log_scale=True, fill=True, alpha=0.3, ax=ax)
ax.set_title('KUB Train vs Validation Foreground Ratio Density Comparison', fontsize=12, fontweight='bold')
ax.set_xlabel('Foreground Ratio (Log Scale)', fontsize=10)
ax.set_ylabel('Density', fontsize=10)
plt.tight_layout()
for ext in ['png', 'svg', 'pdf']:
    plt.savefig(FIGURES_DIR / f'kub_train_val_distribution_v2.{ext}', dpi=300)
plt.close()

print("Saved all 6 publication figures (PNG/SVG/PDF).")

# --- QUALITATIVE PANEL (12 SAMPLES, TRAIN ONLY) ---
selected_samples = []
for cat in ['Kidney_Stone', 'Bladder_Stone', 'Ureteric_Stone']:
    sub = df_samples[df_samples['category'] == cat].sort_values(by='foreground_ratio')
    n = len(sub)
    selected_samples.extend([
        sub.iloc[0],
        sub.iloc[n // 4],
        sub.iloc[n // 2],
        sub.iloc[-1]
    ])

qual_df = pd.DataFrame(selected_samples).drop_duplicates(subset=['sample_id']).head(12)

fig, axes = plt.subplots(4, 3, figsize=(12, 14))
axes = axes.flatten()

for idx, (_, row) in enumerate(qual_df.iterrows()):
    ax = axes[idx]
    img = Image.open(row['image_path']).convert('RGB')
    mask = Image.open(row['mask_path']).convert('L')
    
    mask_arr = np.array(mask) > 0
    img_arr = np.array(img).copy()
    img_arr[mask_arr, 0] = np.clip(img_arr[mask_arr, 0].astype(int) + 160, 0, 255)
    
    ax.imshow(img_arr)
    ax.set_title(f"{row['category']}\nFG Px: {row['foreground_pixels']} | Ratio: {row['foreground_ratio']:.4f} | Comps: {row['component_count']}", fontsize=8)
    ax.axis('off')

plt.suptitle('KUB Train 12-Sample Deterministic Qualitative Panel (Image + Red Overlay)', fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig(QUAL_DIR / 'kub_train_qualitative_panel_v2.png', dpi=300)
plt.close()

def get_file_sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while chunk := f.read(8192): h.update(chunk)
    return h.hexdigest()

# Provenance JSON
hash_samples = get_file_sha256(TABLES_DIR / 'kub_train_sample_characteristics_v2.csv')
hash_components = get_file_sha256(TABLES_DIR / 'kub_train_components_v2.csv')
hash_val_samples = get_file_sha256(TABLES_DIR / 'kub_val_sample_characteristics_v2.csv')

prov_json = {
    'manifest_version': 'phase4_v2',
    'manifest_hashes': {
        'all_paired.csv': get_file_sha256(MANIFEST_DIR / 'all_paired.csv'),
        'train.csv': get_file_sha256(MANIFEST_DIR / 'train.csv'),
        'val.csv': get_file_sha256(MANIFEST_DIR / 'val.csv'),
        'test.csv': get_file_sha256(MANIFEST_DIR / 'test.csv')
    },
    'foreground_definition': 'foreground = (mask > 0).astype(uint8)',
    'component_connectivity': 8,
    'train_sample_count': len(df_samples),
    'val_sample_count': len(df_val_samples),
    'test_mask_access': False,
    'source_table_hashes': {
        'kub_train_sample_characteristics_v2.csv': hash_samples,
        'kub_train_components_v2.csv': hash_components,
        'kub_val_sample_characteristics_v2.csv': hash_val_samples
    },
    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
}

with open(AUDIT_DIR / 'kub_characterization_provenance.json', 'w', encoding='utf-8') as f:
    json.dump(prov_json, f, indent=2)

print("Phase 6-R2 analysis pipeline executed successfully.")


df_components = pd.DataFrame(component_records)

# Invariant Assertions
assert len(df_samples) == 1979, f"Sample count {len(df_samples)} != 1979"
assert (df_samples['component_count'] >= 1).all(), "Found empty TRAIN mask!"
assert len(df_components) == df_samples['component_count'].sum(), "Component row count != sum of component counts"
cat_counts = df_samples['category'].value_counts().to_dict()
assert cat_counts == {'Kidney_Stone': 1133, 'Bladder_Stone': 635, 'Ureteric_Stone': 211}, f"Unexpected cat counts: {cat_counts}"

print("All TRAIN invariant assertions PASSED.")

df_samples.to_csv(TABLES_DIR / 'kub_train_sample_characteristics_v2.csv', index=False)
df_components.to_csv(TABLES_DIR / 'kub_train_components_v2.csv', index=False)
