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

from src.utils.manifest_guard import verify_manifests
from src.analysis.kub_object_size import (
    classify_view_type,
    compute_size_thresholds,
    assign_component_strata,
    assign_sample_strata
)

verify_manifests()

PROJECT_ROOT = Path(r'D:\Softfors\jup')
MANIFEST_DIR = PROJECT_ROOT / 'manifests'
TABLES_DIR = PROJECT_ROOT / 'reports' / 'tables'
FIGURES_DIR = PROJECT_ROOT / 'reports' / 'figures' / 'kub_object_size'
QUAL_DIR = PROJECT_ROOT / 'reports' / 'qualitative' / 'kub_size_taxonomy'
AUDIT_DIR = PROJECT_ROOT / 'reports' / 'audits'

TABLES_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
QUAL_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
colors_cat = {'Kidney_Stone': '#1f77b4', 'Bladder_Stone': '#ff7f0e', 'Ureteric_Stone': '#2ca02c'}
colors_strata = {'TINY': '#d62728', 'SMALL': '#ff7f0e', 'MEDIUM': '#bcbd22', 'LARGE': '#2ca02c'}

df_train_samples = pd.read_csv(TABLES_DIR / 'kub_train_sample_characteristics_v2.csv')
df_train_comps = pd.read_csv(TABLES_DIR / 'kub_train_components_v2.csv')
df_val_samples = pd.read_csv(TABLES_DIR / 'kub_val_sample_characteristics_v2.csv')

# 1. FOV / View-Type Inventory
df_train_samples['view_type'] = df_train_samples['image_path'].apply(classify_view_type)
df_val_samples['view_type'] = df_val_samples['image_path'].apply(classify_view_type)

inventory_rows = []
for split_name, df_sub in [('train', df_train_samples), ('val', df_val_samples)]:
    for _, row in df_sub.iterrows():
        inventory_rows.append({
            'sample_id': row['sample_id'],
            'split': split_name,
            'patient_id': row['patient_id'],
            'category': row['category'],
            'image_path': row['image_path'],
            'width': row['width'],
            'height': row['height'],
            'image_area': row['width'] * row['height'],
            'view_type': row['view_type'],
            'view_type_rule': r'Directory path semantics: \Images\ -> FULL_FIELD, \ROI\ -> ROI_CROP',
            'view_type_confidence': 'HIGH'
        })
df_inventory = pd.DataFrame(inventory_rows)
df_inventory.to_csv(TABLES_DIR / 'kub_view_type_inventory.csv', index=False)

# 2. FOV Heterogeneity Summary Table
fov_rows = []
for vtype in ['FULL_FIELD', 'ROI_CROP']:
    grp = df_train_samples[df_train_samples['view_type'] == vtype]
    fov_rows.append({
        'View_Type': vtype,
        'Samples': len(grp),
        'Patients': grp['patient_id'].nunique(),
        'Percent': len(grp) / len(df_train_samples) * 100,
        'Width_Median': grp['width'].median(),
        'Height_Median': grp['height'].median(),
        'Image_Area_Median': (grp['width'] * grp['height']).median(),
        'FG_Pixels_Median': grp['foreground_pixels'].median(),
        'FG_Ratio_Min': grp['foreground_ratio'].min(),
        'FG_Ratio_Median': grp['foreground_ratio'].median(),
        'FG_Ratio_Max': grp['foreground_ratio'].max()
    })
df_fov_summary = pd.DataFrame(fov_rows)
df_fov_summary.to_csv(TABLES_DIR / 'kub_fov_summary.csv', index=False)

# 3. Compute Size Thresholds on TRAIN FULL_FIELD Components
df_train_comps = df_train_comps.merge(df_train_samples[['sample_id', 'view_type', 'image_path']], on='sample_id')
thresholds = compute_size_thresholds(df_train_comps, df_train_samples)

print(f"Thresholds: Q25={thresholds['Q25']:.8f}, Q50={thresholds['Q50']:.8f}, Q75={thresholds['Q75']:.8f}")

df_size_thresh = pd.DataFrame([
    {'Stratum': 'TINY', 'Range_Condition': f'component_ratio <= {thresholds["Q25"]:.8f}', 'Q_Cutoff': 'Q25', 'Cutoff_Value': thresholds['Q25']},
    {'Stratum': 'SMALL', 'Range_Condition': f'{thresholds["Q25"]:.8f} < component_ratio <= {thresholds["Q50"]:.8f}', 'Q_Cutoff': 'Q50', 'Cutoff_Value': thresholds['Q50']},
    {'Stratum': 'MEDIUM', 'Range_Condition': f'{thresholds["Q50"]:.8f} < component_ratio <= {thresholds["Q75"]:.8f}', 'Q_Cutoff': 'Q75', 'Cutoff_Value': thresholds['Q75']},
    {'Stratum': 'LARGE', 'Range_Condition': f'component_ratio > {thresholds["Q75"]:.8f}', 'Q_Cutoff': 'Max', 'Cutoff_Value': df_train_comps[df_train_comps['view_type']=='FULL_FIELD']['component_ratio'].max()}
])
df_size_thresh.to_csv(TABLES_DIR / 'kub_size_thresholds.csv', index=False)

# Threshold JSON & MD Artifacts
thresh_json = {
    'taxonomy_version': 'kub_size_v1',
    'manifest_version': 'phase4_v2',
    'source_population': 'KUB TRAIN FULL_FIELD Components',
    'source_split': 'TRAIN',
    'source_view_type': 'FULL_FIELD',
    'connectivity': 8,
    'size_measure': 'component_ratio (component_pixels / image_area)',
    'full_field_train_component_count': thresholds['full_field_component_count'],
    'Q25': thresholds['Q25'],
    'Q50': thresholds['Q50'],
    'Q75': thresholds['Q75'],
    'strata_intervals': {
        'TINY': f'component_ratio <= {thresholds["Q25"]:.8f}',
        'SMALL': f'{thresholds["Q25"]:.8f} < component_ratio <= {thresholds["Q50"]:.8f}',
        'MEDIUM': f'{thresholds["Q50"]:.8f} < component_ratio <= {thresholds["Q75"]:.8f}',
        'LARGE': f'component_ratio > {thresholds["Q75"]:.8f}'
    },
    'clinical_interpretation': 'NONE (Dataset-relative strata)',
    'test_used': False,
    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
}
with open(AUDIT_DIR / 'kub_object_size_thresholds.json', 'w', encoding='utf-8') as f:
    json.dump(thresh_json, f, indent=2)

md_thresh = f"""# KUB Object-Size Thresholds (Taxonomy Version: `kub_size_v1`)

## Methodology
- **FOV Stratification**: KUB dataset contains two distinct acquisition types: `FULL_FIELD` (full radiography plates) and `ROI_CROP` (cropped ROI images).
- **Threshold Source**: Predeclared quartile cutouts (Q25, Q50, Q75) computed exclusively on **TRAIN FULL_FIELD connected components** (n={thresholds['full_field_component_count']}).
- **Primary Measure**: `component_ratio` = `component_pixels / image_area`.

## Frozen Threshold Cutoffs
- **Q25**: `{thresholds['Q25']:.8f}` (~0.015% of image area)
- **Q50**: `{thresholds['Q50']:.8f}` (~0.034% of image area)
- **Q75**: `{thresholds['Q75']:.8f}` (~0.083% of image area)

## Strata Definitions
- **TINY**: `component_ratio <= {thresholds['Q25']:.8f}`
- **SMALL**: `{thresholds['Q25']:.8f} < component_ratio <= {thresholds['Q50']:.8f}`
- **MEDIUM**: `{thresholds['Q50']:.8f} < component_ratio <= {thresholds['Q75']:.8f}`
- **LARGE**: `component_ratio > {thresholds['Q75']:.8f}`

*Note: These strata are dataset-relative for research evaluation and do not represent millimeter-based clinical stone sizes. VAL receives frozen TRAIN thresholds. TEST mask morphology remains locked.*
"""
with open(AUDIT_DIR / 'kub_object_size_thresholds.md', 'w', encoding='utf-8') as f:
    f.write(md_thresh)

# 4. Assign Strata to TRAIN Components & Samples
df_tr_comps_sized = assign_component_strata(df_train_comps, df_train_samples, thresholds)
df_tr_samples_sized = assign_sample_strata(df_train_samples, df_tr_comps_sized, thresholds)

df_tr_comps_sized.to_csv(TABLES_DIR / 'kub_train_components_sized.csv', index=False)

# 5. Assign Strata to VAL Components & Samples (Transfer frozen TRAIN thresholds)
from src.analysis.kub_characterization import analyze_kub_mask_v2
val_comp_records = []
val_sample_records = []
for _, row in df_val_samples.iterrows():
    res = analyze_kub_mask_v2(row['mask_path'], connectivity=8)
    comp_list = res.pop('components')
    c_pixels = [c['component_pixels'] for c in comp_list]
    largest_c_pixels = max(c_pixels) if c_pixels else 0
    smallest_c_pixels = min(c_pixels) if c_pixels else 0
    
    val_sample_records.append({
        'sample_id': row['sample_id'],
        'patient_id': row['patient_id'],
        'category': row['category'],
        'image_path': row['image_path'],
        'mask_path': row['mask_path'],
        'view_type': row['view_type'],
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
        'smallest_component_ratio': smallest_c_pixels / (res['width'] * res['height'])
    })
    for c in comp_list:
        val_comp_records.append({
            'sample_id': row['sample_id'],
            'patient_id': row['patient_id'],
            'category': row['category'],
            'image_path': row['image_path'],
            'view_type': row['view_type'],
            **c
        })
df_val_comps = pd.DataFrame(val_comp_records)
df_val_samples = pd.DataFrame(val_sample_records)

df_val_comps_sized = assign_component_strata(df_val_comps, df_val_samples, thresholds)
df_val_samples_sized = assign_sample_strata(df_val_samples, df_val_comps_sized, thresholds)

df_val_comps_sized.to_csv(TABLES_DIR / 'kub_val_components_sized.csv', index=False)
df_val_samples_sized.to_csv(TABLES_DIR / 'kub_val_samples_sized.csv', index=False)

# 6. Category x Size Table (TRAIN FULL_FIELD)
cat_size_rows = []
ff_tr_comps = df_tr_comps_sized[df_tr_comps_sized['view_type'] == 'FULL_FIELD']
for cat in ['Kidney_Stone', 'Bladder_Stone', 'Ureteric_Stone']:
    sub = ff_tr_comps[ff_tr_comps['category'] == cat]
    cat_size_rows.append({
        'Category': cat,
        'Tiny': (sub['size_stratum'] == 'TINY').sum(),
        'Small': (sub['size_stratum'] == 'SMALL').sum(),
        'Medium': (sub['size_stratum'] == 'MEDIUM').sum(),
        'Large': (sub['size_stratum'] == 'LARGE').sum(),
        'Total_Full_Field': len(sub)
    })
df_cat_size = pd.DataFrame(cat_size_rows)
df_cat_size.to_csv(TABLES_DIR / 'kub_size_distribution_by_category.csv', index=False)

# 7. TRAIN vs VAL Size Distribution Table (FULL_FIELD)
ff_val_comps = df_val_comps_sized[df_val_comps_sized['view_type'] == 'FULL_FIELD']
tv_size_rows = []
for split_name, df_sub in [('TRAIN', ff_tr_comps), ('VAL', ff_val_comps)]:
    tv_size_rows.append({
        'Split': split_name,
        'Tiny': (df_sub['fullfield_reference_stratum'] == 'TINY').sum(),
        'Small': (df_sub['fullfield_reference_stratum'] == 'SMALL').sum(),
        'Medium': (df_sub['fullfield_reference_stratum'] == 'MEDIUM').sum(),
        'Large': (df_sub['fullfield_reference_stratum'] == 'LARGE').sum(),
        'Total_Full_Field_Components': len(df_sub)
    })
df_tv_size = pd.DataFrame(tv_size_rows)
df_tv_size.to_csv(TABLES_DIR / 'kub_size_distribution_train_val.csv', index=False)

# 8. Patient x Size Summary Table
pat_size_rows = []
ff_tr_samples = df_tr_samples_sized[df_tr_samples_sized['view_type'] == 'FULL_FIELD']
total_pats = ff_tr_samples['patient_id'].nunique()
pat_size_rows.append({
    'Metric': 'Patient Count',
    'Tiny': ff_tr_samples[ff_tr_samples['contains_tiny_object']]['patient_id'].nunique(),
    'Small': ff_tr_samples[ff_tr_samples['contains_small_object']]['patient_id'].nunique(),
    'Medium': ff_tr_samples[ff_tr_samples['contains_medium_object']]['patient_id'].nunique(),
    'Large': ff_tr_samples[ff_tr_samples['contains_large_object']]['patient_id'].nunique(),
    'Total_FULL_FIELD_Patients': total_pats
})
df_pat_size = pd.DataFrame(pat_size_rows)
df_pat_size.to_csv(TABLES_DIR / 'kub_patient_size_summary.csv', index=False)

# 9. Multi-component Size Summary Table
mc_samples = df_tr_samples_sized[(df_tr_samples_sized['view_type'] == 'FULL_FIELD') & (df_tr_samples_sized['component_count'] > 1)]
mc_rows = []
for _, row in mc_samples.iterrows():
    comps = df_tr_comps_sized[df_tr_comps_sized['sample_id'] == row['sample_id']]
    strata_set = set(comps['size_stratum'].unique())
    mc_rows.append({
        'sample_id': row['sample_id'],
        'category': row['category'],
        'component_count': row['component_count'],
        'is_mixed_strata': len(strata_set) > 1,
        'has_tiny_and_larger': ('TINY' in strata_set) and (len(strata_set - {'TINY'}) > 0)
    })
df_mc_summary = pd.DataFrame(mc_rows) if len(mc_rows) > 0 else pd.DataFrame(columns=['sample_id', 'category', 'component_count', 'is_mixed_strata', 'has_tiny_and_larger'])
df_mc_summary.to_csv(TABLES_DIR / 'kub_multicomponent_size_summary.csv', index=False)

print("Saved all size taxonomy tables.")


# --- FIGURE GENERATION (PNG 300 DPI, SVG, PDF) ---

# Figure A: FOV Composition
fig, ax = plt.subplots(figsize=(7, 5))
fov_df = df_train_samples.groupby('view_type')['sample_id'].count().reset_index()
sns.barplot(x='view_type', y='sample_id', data=fov_df, hue='view_type', palette=['#1f77b4', '#ff7f0e'], legend=False, ax=ax)
ax.set_title('KUB Train FOV Type Composition (n=1979)', fontsize=12, fontweight='bold')
ax.set_xlabel('Field-of-View (FOV) Type', fontsize=10)
ax.set_ylabel('Sample Count', fontsize=10)
for p in ax.patches:
    ax.annotate(f'{int(p.get_height())}', (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center', va='bottom', fontsize=10, xytext=(0, 3), textcoords='offset points')
plt.tight_layout()
for ext in ['png', 'svg', 'pdf']:
    plt.savefig(FIGURES_DIR / f'kub_fov_composition.{ext}', dpi=300)
plt.close()

# Figure B: Image Dimensions by FOV Type
fig, ax = plt.subplots(figsize=(8, 5))
df_train_samples['image_area'] = df_train_samples['width'] * df_train_samples['height']
sns.boxplot(x='view_type', y='image_area', data=df_train_samples, hue='view_type', palette=['#1f77b4', '#ff7f0e'], legend=False, ax=ax)
ax.set_yscale('log')
ax.set_title('KUB Train Image Area Distribution by FOV Type (Log Scale)', fontsize=12, fontweight='bold')
ax.set_xlabel('FOV Type', fontsize=10)
ax.set_ylabel('Image Area (Pixels^2)', fontsize=10)
plt.tight_layout()
for ext in ['png', 'svg', 'pdf']:
    plt.savefig(FIGURES_DIR / f'kub_fov_dimension_distribution.{ext}', dpi=300)
plt.close()

# Figure C: FULL_FIELD Component-Size Distribution with Thresholds
fig, ax = plt.subplots(figsize=(8, 5))
sns.histplot(data=ff_tr_comps, x='component_ratio', element='step', log_scale=True, color='#2b5c8f', ax=ax)
ax.axvline(thresholds['Q25'], color='#d62728', linestyle='--', linewidth=2, label=f"Q25 (TINY): {thresholds['Q25']:.6f}")
ax.axvline(thresholds['Q50'], color='#ff7f0e', linestyle='--', linewidth=2, label=f"Q50 (SMALL): {thresholds['Q50']:.6f}")
ax.axvline(thresholds['Q75'], color='#2ca02c', linestyle='--', linewidth=2, label=f"Q75 (MEDIUM): {thresholds['Q75']:.6f}")
ax.set_title('KUB Train FULL_FIELD Component Ratio Distribution with Quartile Thresholds (n=1162)', fontsize=12, fontweight='bold')
ax.set_xlabel('Component Area / Image Area Ratio (Log Scale)', fontsize=10)
ax.set_ylabel('Component Count', fontsize=10)

# Figure D: Size-Stratum Distribution by Category (FULL_FIELD)
fig, ax = plt.subplots(figsize=(8, 5))
sns.countplot(x='category', hue='size_stratum', data=ff_tr_comps, palette=colors_strata, ax=ax)
ax.set_title('KUB Train FULL_FIELD Object Size Strata by Anatomical Category', fontsize=12, fontweight='bold')
ax.set_xlabel('Anatomical Category', fontsize=10)
ax.set_ylabel('Component Count', fontsize=10)
ax.legend(title='Size Stratum')
plt.tight_layout()
for ext in ['png', 'svg', 'pdf']:
    plt.savefig(FIGURES_DIR / f'kub_object_size_by_category.{ext}', dpi=300)
plt.close()

# Figure E: TRAIN vs VAL Size Distribution (FULL_FIELD)
fig, ax = plt.subplots(figsize=(8, 5))
sns.countplot(x='fullfield_reference_stratum', hue='split', data=pd.concat([
    ff_tr_comps.assign(split='TRAIN'),
    ff_val_comps.assign(split='VAL')
]), palette=['#1f77b4', '#ff7f0e'], ax=ax)
ax.set_title('KUB TRAIN vs VAL FULL_FIELD Object Size Stratum Transfer (Frozen Thresholds)', fontsize=12, fontweight='bold')
ax.set_xlabel('Object Size Stratum (Frozen TRAIN Thresholds)', fontsize=10)
ax.set_ylabel('Component Count', fontsize=10)
plt.tight_layout()
for ext in ['png', 'svg', 'pdf']:
    plt.savefig(FIGURES_DIR / f'kub_object_size_train_val.{ext}', dpi=300)
plt.close()

# Figure F: ROI vs FULL_FIELD Component Ratio Distribution
fig, ax = plt.subplots(figsize=(8, 5))
sns.kdeplot(data=df_tr_comps_sized, x='component_ratio', hue='view_type', common_norm=False, log_scale=True, fill=True, alpha=0.3, ax=ax)
ax.set_title('KUB Train Component Ratio Density: FULL_FIELD vs ROI_CROP', fontsize=12, fontweight='bold')
ax.set_xlabel('Component Area / Image Area Ratio (Log Scale)', fontsize=10)
ax.set_ylabel('Density', fontsize=10)
plt.tight_layout()
for ext in ['png', 'svg', 'pdf']:
    plt.savefig(FIGURES_DIR / f'kub_roi_vs_fullfield_object_ratio.{ext}', dpi=300)
plt.close()

# Figure G: Multi-Component Size Combinations
fig, ax = plt.subplots(figsize=(7, 5))
if len(df_mc_summary) > 0:
    sns.countplot(x='is_mixed_strata', data=df_mc_summary, palette=['#2ca02c', '#d62728'], hue='is_mixed_strata', legend=False, ax=ax)
    ax.set_title('KUB Multi-Component Images: Single vs Mixed Size Strata (n=210)', fontsize=12, fontweight='bold')
    ax.set_xlabel('Is Mixed Size Strata?', fontsize=10)
    ax.set_ylabel('Image Count', fontsize=10)
    ax.set_xticklabels(['Same Stratum', 'Mixed Strata'])
plt.tight_layout()
for ext in ['png', 'svg', 'pdf']:
    plt.savefig(FIGURES_DIR / f'kub_multicomponent_size_combinations.{ext}', dpi=300)
plt.close()

print("Saved all 7 publication figures (PNG/SVG/PDF).")

# --- QUALITATIVE PANELS ---
# 1. FULL_FIELD Qualitative Size Strata Panel (2 per stratum = 8 samples)
ff_samples_sized = df_tr_samples_sized[df_tr_samples_sized['view_type'] == 'FULL_FIELD'].copy()
qual_samples = []
for st in ['TINY', 'SMALL', 'MEDIUM', 'LARGE']:
    sub = ff_samples_sized[ff_samples_sized['dominant_object_stratum'] == st].sort_values(by='largest_component_ratio')
    if len(sub) >= 2:
        qual_samples.append(sub.iloc[len(sub)//3])
        qual_samples.append(sub.iloc[2*len(sub)//3])
    elif len(sub) == 1:
        qual_samples.append(sub.iloc[0])

qual_ff_df = pd.DataFrame(qual_samples).drop_duplicates(subset=['sample_id']).head(8)

fig, axes = plt.subplots(2, 4, figsize=(16, 8))
axes = axes.flatten()

for idx, (_, row) in enumerate(qual_ff_df.iterrows()):
    ax = axes[idx]
    img = Image.open(row['image_path']).convert('RGB')
    mask = Image.open(row['mask_path']).convert('L')
    
    mask_arr = np.array(mask) > 0
    img_arr = np.array(img).copy()
    img_arr[mask_arr, 0] = np.clip(img_arr[mask_arr, 0].astype(int) + 160, 0, 255)
    
    ax.imshow(img_arr)
    ax.set_title(f"{row['dominant_object_stratum']} | {row['category']}\nRatio: {row['largest_component_ratio']:.6f} | Px: {int(row['largest_component_ratio']*row['width']*row['height'])}", fontsize=8)
    ax.axis('off')

plt.suptitle('KUB Train FULL_FIELD Deterministic Qualitative Size Strata Panel', fontsize=13, fontweight='bold')
plt.tight_layout()
for ext in ['png', 'svg', 'pdf']:
    plt.savefig(QUAL_DIR / f'kub_size_strata_examples.{ext}', dpi=300)
plt.close()

# 2. ROI Qualitative Panel (4 ROI samples)
roi_samples_sized = df_tr_samples_sized[df_tr_samples_sized['view_type'] == 'ROI_CROP'].sort_values(by='foreground_ratio')
roi_qual_samples = [
    roi_samples_sized.iloc[0],
    roi_samples_sized.iloc[len(roi_samples_sized)//3],
    roi_samples_sized.iloc[2*len(roi_samples_sized)//3],
    roi_samples_sized.iloc[-1]
]
qual_roi_df = pd.DataFrame(roi_qual_samples)

fig, axes = plt.subplots(1, 4, figsize=(14, 3.5))
axes = axes.flatten()

for idx, (_, row) in enumerate(qual_roi_df.iterrows()):
    ax = axes[idx]
    img = Image.open(row['image_path']).convert('RGB')
    mask = Image.open(row['mask_path']).convert('L')
    
    mask_arr = np.array(mask) > 0
    img_arr = np.array(img).copy()
    img_arr[mask_arr, 0] = np.clip(img_arr[mask_arr, 0].astype(int) + 160, 0, 255)
    
    ax.imshow(img_arr)
    ax.set_title(f"ROI_CROP | {row['category']}\nSize: {row['width']}x{row['height']} | Ratio: {row['foreground_ratio']:.3f}", fontsize=8)
    ax.axis('off')

plt.suptitle('KUB Train ROI_CROP Deterministic Qualitative Panel (Demonstrating Cropped FOV)', fontsize=12, fontweight='bold')
plt.tight_layout()
for ext in ['png', 'svg', 'pdf']:
    plt.savefig(QUAL_DIR / f'kub_roi_examples.{ext}', dpi=300)
plt.close()

print("Saved qualitative panels (PNG/SVG/PDF).")

ax.legend(loc='upper right')
plt.tight_layout()
for ext in ['png', 'svg', 'pdf']:
    plt.savefig(FIGURES_DIR / f'kub_fullfield_object_size_thresholds.{ext}', dpi=300)
plt.close()

df_tr_samples_sized.to_csv(TABLES_DIR / 'kub_train_samples_sized.csv', index=False)

