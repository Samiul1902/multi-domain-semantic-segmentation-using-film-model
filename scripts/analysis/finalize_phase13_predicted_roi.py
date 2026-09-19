"""Finalize Phase-13 figures, qualitative panel, notebook inputs, and provenance."""
import hashlib,json,sys
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd
import seaborn as sns
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.inference.predicted_roi import generate_predicted_rois
from src.utils.manifest_guard import verify_manifests
from src.utils.test_lock import verify_test_lock
T=ROOT/'reports/tables'; C=ROOT/'data_cache/phase13_predicted_roi'; F=ROOT/'reports/figures/phase13_predicted_roi'; Q=ROOT/'reports/qualitative/phase13_predicted_roi'; A=ROOT/'reports/audits'; F.mkdir(parents=True,exist_ok=True);Q.mkdir(parents=True,exist_ok=True)
def emit(fig,name,directory=F):
 for ext in ('png','svg','pdf'): fig.savefig(directory/f'{name}.{ext}',dpi=320,bbox_inches='tight')
 plt.close(fig)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
class Meta:
 def __init__(self,row): self.scale=float(row.scale);self.resized_height=int(row.resized_height);self.resized_width=int(row.resized_width);self.padding=(int(row.padding_left),int(row.padding_top),int(row.padding_right),int(row.padding_bottom))
def figures(search,components,images,size,multi):
 sns.set_theme(style='whitegrid'); best=search.groupby('proposal_threshold').overall_recall90.max().reset_index(); fig,ax=plt.subplots(figsize=(8,5));sns.lineplot(best,x='proposal_threshold',y='overall_recall90',marker='o',ax=ax);ax.set_ylim(0,1);ax.set_title('Best Recall90 by Proposal Threshold');emit(fig,'phase13_proposal_recall_vs_threshold')
 best=search.groupby('proposal_threshold').tiny_recall90.max().reset_index();fig,ax=plt.subplots(figsize=(8,5));sns.lineplot(best,x='proposal_threshold',y='tiny_recall90',marker='o',ax=ax);ax.set_ylim(0,1);ax.set_title('Best TINY Recall90 by Threshold');emit(fig,'phase13_tiny_recall_vs_threshold')
 fig,ax=plt.subplots(figsize=(8,5));sns.scatterplot(search,x='mean_total_roi_area_fraction',y='overall_recall90',hue='proposal_threshold',size='top_k',ax=ax);ax.set_ylim(0,1);ax.set_title('Localization Recall–ROI Area Trade-off');emit(fig,'phase13_recall_vs_roi_area_tradeoff')
 fig,ax=plt.subplots(figsize=(8,5));sns.scatterplot(search,x='mean_proposals_per_image',y='overall_recall90',hue='margin',style='top_k',ax=ax);ax.set_ylim(0,1);ax.set_title('Localization Recall–Proposal Count Trade-off');emit(fig,'phase13_recall_vs_proposal_count')
 fig,ax=plt.subplots(figsize=(8,5));sns.barplot(size,x='Size',y='recall90',hue='Size',legend=False,ax=ax);ax.set_ylim(0,1);ax.set_title('Selected Configuration Localization by kub_size_v1');emit(fig,'phase13_size_stratum_localization')
 missed=components[~components.global_detected].groupby('kub_size_v1').covered90.agg(['size','sum']).reset_index();fig,ax=plt.subplots(figsize=(8,5));missed=missed.melt('kub_size_v1',var_name='Measure',value_name='Count');sns.barplot(missed,x='kub_size_v1',y='Count',hue='Measure',ax=ax);ax.set_title('Global Misses Localized by Predicted ROI');emit(fig,'phase13_global_miss_recovery_localization')
 fig,ax=plt.subplots(figsize=(8,5));vals=multi.iloc[0][['all_localized_images','partial_localized_images','none_localized_images']];sns.barplot(x=vals.index,y=vals.values,ax=ax);ax.tick_params(axis='x',rotation=20);ax.set_title('Multi-component Localization');emit(fig,'phase13_multicomponent_localization')
 pivot=search[(search.margin==.15)&(search.nms_iou==.3)].pivot(index='proposal_threshold',columns='top_k',values='overall_recall90');fig,ax=plt.subplots(figsize=(7,6));sns.heatmap(pivot,annot=True,fmt='.3f',vmin=0,vmax=1,ax=ax);ax.set_title('Recall90 Heatmap (margin=.15, NMS=.30)');emit(fig,'phase13_proposal_parameter_heatmap')
 fig,ax=plt.subplots(figsize=(8,5));sns.histplot(components,x='coverage_fraction',hue='kub_size_v1',element='step',stat='count',ax=ax);ax.set_xlim(0,1);ax.axvline(.9,color='red',ls='--');ax.set_title('Selected Configuration Component Coverage');emit(fig,'phase13_component_coverage_distribution')

def qualitative(components,images,selected):
 samples=pd.read_csv(T/'kub_val_samples_sized.csv').set_index('sample_id'); cache=pd.read_csv(C/'metadata.csv').set_index('sample_id'); threshold=float(selected.proposal_threshold);margin=float(selected.margin);top_k=int(selected.top_k);nms=float(selected.nms_iou)
 criteria=[]
 def add(label,frame,sort=None,ascending=True):
  if len(frame):
   row=frame.sort_values(sort,ascending=ascending).iloc[0] if sort else frame.iloc[0]; criteria.append((label,row.sample_id))
 missed_tiny=components[(components.kub_size_v1=='TINY')&~components.global_detected];add('GLOBAL_MISSED_TINY_LOCALIZED',missed_tiny[missed_tiny.covered90]);add('GLOBAL_MISSED_TINY_NOT_LOCALIZED',missed_tiny[~missed_tiny.covered90]);add('GLOBAL_EMPTY_ROI_FOUND',images[images.global_empty_but_roi_found]);multi=images[images.component_count_original>1];add('MULTI_ALL_LOCALIZED',multi[multi.components_covered90==multi.components_gt]);add('MULTI_PARTIAL',multi[(multi.components_covered90>0)&(multi.components_covered90<multi.components_gt)]);add('HIGH_UNMATCHED',images,'unmatched_proposals',False);add('ZERO_PROPOSAL',images[images.zero_proposal])
 unique=[]; labels={}
 for label_name,sid in criteria:
  if sid not in unique: unique.append(sid)
  labels.setdefault(sid,[]).append(label_name)
 fig,axes=plt.subplots(len(unique),4,figsize=(14,3.2*len(unique)),squeeze=False)
 for i,sid in enumerate(unique):
  row=samples.loc[sid]; probability=np.load(C/f'{sid}_probability_512.npy'); meta=Meta(cache.loc[sid]); proposals=generate_predicted_rois(probability,meta,(int(row.height),int(row.width)),threshold,margin,top_k,nms)
  with Image.open(row.image_path) as f:image=np.asarray(f.convert('L'))
  with Image.open(row.mask_path) as f:gt=np.asarray(f.convert('L'))>0
  axes[i,0].imshow(image,cmap='gray');axes[i,0].set_title(f'{sid}\n{row.category}\n{";".join(labels[sid])}',fontsize=7)
  axes[i,1].imshow(probability,cmap='magma',vmin=0,vmax=1);axes[i,1].set_title('GLOBAL PROBABILITY (512)')
  axes[i,2].imshow(image,cmap='gray');axes[i,2].set_title('PREDICTED ROI BOXES (red)')
  for p in proposals:
   g=p['crop_geometry'];axes[i,2].add_patch(Rectangle((g['clip_x1'],g['clip_y1']),g['clip_x2']-g['clip_x1'],g['clip_y2']-g['clip_y1'],fill=False,color='red',lw=2))
  axes[i,3].imshow(image,cmap='gray');axes[i,3].contour(gt,levels=[.5],colors='lime',linewidths=1);axes[i,3].set_title('GT EVALUATION ONLY (green)')
  for ax in axes[i]:ax.axis('off')
 fig.suptitle('GT-free predicted proposals; GT shown only in separate evaluation overlay');fig.tight_layout();emit(fig,'phase13_predicted_roi_localization_panel',Q);(Q/'phase13_predicted_roi_panel_selection.json').write_text(json.dumps({'criteria':criteria,'unique_sample_ids':unique,'GT_used_to_generate_proposals':False},indent=2),encoding='utf-8')
 return criteria

def main():
 verify_manifests();verify_test_lock(ROOT);search=pd.read_csv(T/'phase13_predicted_roi_search.csv');components=pd.read_csv(T/'phase13_predicted_roi_per_component.csv');images=pd.read_csv(T/'phase13_predicted_roi_per_image.csv');selected=pd.read_csv(T/'phase13_predicted_roi_selected_config.csv').iloc[0];size=pd.read_csv(T/'phase13_predicted_roi_size_summary.csv');multi=pd.read_csv(T/'phase13_predicted_roi_multicomponent.csv');figures(search,components,images,size,multi);criteria=qualitative(components,images,selected);print(selected.to_dict());print(criteria)
if __name__=='__main__':main()

