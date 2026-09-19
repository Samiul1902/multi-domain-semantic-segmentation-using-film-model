"""Add post-generation evaluation diagnostics to selected Phase-13 tables."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from PIL import Image
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[2];T=ROOT/'reports/tables';C=ROOT/'data_cache/phase13_predicted_roi'
components=pd.read_csv(T/'phase13_predicted_roi_per_component.csv');images=pd.read_csv(T/'phase13_predicted_roi_per_image.csv');samples=pd.read_csv(T/'kub_val_samples_sized.csv').set_index('sample_id');cache=pd.read_csv(C/'metadata.csv').set_index('sample_id')
near_target=[]
for _,row in components.iterrows():
 meta=cache.loc[row.sample_id]; probability=np.load(C/f'{row.sample_id}_probability_512.npy'); left,top=int(meta.padding_left),int(meta.padding_top); scale=float(meta.scale)
 y1=max(top,int(np.floor(row.min_y*scale))+top);y2=min(top+int(meta.resized_height),int(np.ceil((row.max_y+1)*scale))+top);x1=max(left,int(np.floor(row.min_x*scale))+left);x2=min(left+int(meta.resized_width),int(np.ceil((row.max_x+1)*scale))+left)
 patch=probability[y1:y2,x1:x2];near_target.append(float(patch.max()) if patch.size else np.nan)
components['coarse_max_probability_near_target']=near_target
components.to_csv(T/'phase13_predicted_roi_per_component.csv',index=False)
strata=components.groupby('sample_id').kub_size_v1.apply(lambda values:';'.join(sorted(set(values))));images['size_strata']=images.sample_id.map(strata);images['coarse_max_probability']=images.sample_id.map(cache.coarse_max_probability);images['global_empty_components_covered90']=np.where(images.global_empty_prediction,images.components_covered90,0);images.to_csv(T/'phase13_predicted_roi_per_image.csv',index=False)
empty=images[images.global_empty_prediction][['sample_id','patient_id','category','component_count_original','size_strata','coarse_max_probability','proposal_count','zero_proposal','components_covered90','global_empty_but_roi_found']].copy();empty=empty.merge(components.groupby('sample_id').coarse_max_probability_near_target.max().rename('max_coarse_probability_near_target'),on='sample_id');empty.to_csv(T/'phase13_global_empty_case_analysis.csv',index=False)
zero=images[images.zero_proposal][['sample_id','patient_id','category','component_count_original','size_strata','coarse_max_probability']];zero.to_csv(T/'phase13_zero_proposal_analysis.csv',index=False)
print(empty.to_string(index=False))
