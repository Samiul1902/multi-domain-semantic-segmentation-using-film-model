"""Build Phase-10 comparison tables, figures, panels, notebook inputs, and provenance."""
import hashlib, json, sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import torch
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.data.kub_dataset import KUBDataset
from src.data.transforms import SegmentationTransform
from src.models.factory import create_model
from src.utils.checkpointing import load_training_checkpoint
from src.utils.manifest_guard import verify_manifests
from src.utils.test_lock import verify_test_lock
T=ROOT/'reports/tables'; F=ROOT/'reports/figures/phase10_kub_comparison'; Q=ROOT/'reports/qualitative/phase10_kub_comparison'
F.mkdir(parents=True,exist_ok=True); Q.mkdir(parents=True,exist_ok=True)
MODELS=[('U-Net','unet','phase9_kub_unet_baseline_seed42_512','phase9_unet'),('Attention U-Net','attention_unet','phase10_kub_attention_unet_seed42_512','phase10_attention_unet'),('UNet++','unetpp','phase10_kub_unetpp_seed42_512','phase10_unetpp'),('DeepLabV3+','deeplabv3plus','phase10_kub_deeplabv3plus_seed42_512','phase10_deeplabv3plus')]

def read(stem,suffix): return pd.read_csv(T/f'{stem}_{suffix}.csv')
def save(frame,path):
 frame.to_csv(path,index=False); h=[str(x) for x in frame.columns]; lines=['| '+' | '.join(h)+' |','| '+' | '.join(['---']*len(h))+' |']; lines += ['| '+' | '.join(map(str,row))+' |' for row in frame.itertuples(index=False,name=None)]; path.with_suffix('.md').write_text('\n'.join(lines)+'\n',encoding='utf-8'); path.with_suffix('.tex').write_text(frame.to_latex(index=False),encoding='utf-8')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def lookup(frame,key,value,column): return float(frame.loc[frame[key]==value,column].iloc[0])

def phase9_multi():
 pi=read('phase9_unet','val_per_image'); pc=read('phase9_unet','val_per_component'); ff=pi[pi.view_type=='FULL_FIELD'].copy(); det=pc.groupby('sample_id').detected.agg(['sum','count']); ff=ff.join(det,on='sample_id'); ff['Component_Group']=np.where(ff.component_count>1,'MULTI_COMPONENT','SINGLE_COMPONENT'); x=ff.groupby('Component_Group').agg(N_Images=('sample_id','size'),Macro_Dice=('dice','mean'),Original_GT_Components=('count','sum'),Detected_Original_Components=('sum','sum')).reset_index(); x['Object_Recall']=x.Detected_Original_Components/x.Original_GT_Components; x['Missed_Object_Rate']=1-x.Object_Recall; return x

def build_tables():
 rows=[]; fair=[]; multi_frames=[]
 for display,key,exp,stem in MODELS:
  s=json.loads((ROOT/'experiments'/exp/'summary.json').read_text()); v=read(stem,'val_summary'); f=read(stem,'fov_summary'); c=read(stem,'category_summary'); z=read(stem,'size_summary'); o=read(stem,'object_summary'); m=phase9_multi() if key=='unet' else read(stem,'multicomponent_summary'); m.insert(0,'Model',display); multi_frames.append(m)
  if key=='unet':
   pi=read(stem,'val_per_image'); fp=float(pi.false_positive_components.mean()); params=s['parameter_count']; ep=s['epochs_completed']; be=s['best_epoch']; pb=eb=4; tt=s['total_training_seconds']; met=s['total_training_seconds']/ep; pga=max(pd.read_csv(ROOT/'experiments'/exp/'history.csv').peak_gpu_allocated); pgr=max(pd.read_csv(ROOT/'experiments'/exp/'history.csv').peak_gpu_reserved)
  else:
   fp=float(o.FP_Components_Per_Image.iloc[0]); params=s['parameter_count']; ep=s['epochs_completed']; be=s['best_epoch']; pb=s['physical_batch']; eb=s['effective_batch']; tt=s['training_seconds']; met=s['mean_epoch_seconds']; pga=s['peak_gpu_allocated']; pgr=s['peak_gpu_reserved']
  rows.append({'model':display,'parameters':params,'best_epoch':be,'epochs_completed':ep,'physical_batch':pb,'effective_batch':eb,'macro_dice':v.Macro_Dice.iloc[0],'macro_iou':v.Macro_IoU.iloc[0],'macro_precision':v.Macro_Precision.iloc[0],'macro_recall':v.Macro_Recall.iloc[0],'micro_dice':v.Micro_Dice.iloc[0],'micro_iou':v.Micro_IoU.iloc[0],'median_valid_hd95':v.Median_Valid_HD95.iloc[0],'mean_valid_hd95':v.Mean_Valid_HD95.iloc[0],'empty_prediction_rate':v.Empty_Prediction_Rate.iloc[0],'object_recall':o.Object_Recall.iloc[0],'missed_object_rate':o.Missed_Object_Rate.iloc[0],'fp_components_per_image':fp,'full_field_dice':lookup(f,'View_Type','FULL_FIELD','Macro_Dice'),'roi_crop_dice':lookup(f,'View_Type','ROI_CROP','Macro_Dice'),'tiny_object_recall':lookup(z,'Stratum','TINY','Object_Recall'),'small_object_recall':lookup(z,'Stratum','SMALL','Object_Recall'),'medium_object_recall':lookup(z,'Stratum','MEDIUM','Object_Recall'),'large_object_recall':lookup(z,'Stratum','LARGE','Object_Recall'),'training_wall_time':tt,'mean_epoch_time':met,'peak_gpu_allocated':pga,'peak_gpu_reserved':pgr})
  fair.append({'model':display,'seed':42,'resolution':512,'optimizer':'AdamW','learning_rate':1e-4,'weight_decay':1e-4,'scheduler':'CosineAnnealingLR','loss':'0.5 BCEWithLogitsLoss + 0.5 DiceLoss','threshold':0.5,'max_epochs':100,'patience':15,'preprocessing':'aspect-ratio resize + symmetric square padding','augmentation':'HFlip p=.5; rotation ±5°; brightness/contrast ±10%','physical_batch':pb,'effective_batch':eb,'initialization_policy':'random Kaiming; no pretrained weights','selection_metric':'true per-image VAL macro Dice'})
 comparison=pd.DataFrame(rows); fairness=pd.DataFrame(fair); multi=pd.concat(multi_frames,ignore_index=True); save(comparison,T/'phase10_kub_model_comparison.csv'); save(fairness,T/'phase10_kub_fairness_table.csv'); save(multi,T/'phase10_kub_multicomponent_comparison.csv'); return comparison,fairness,multi


def figures(comp,multi):
 sns.set_theme(style='whitegrid')
 def emit(fig,stem):
  for ext in ('png','svg','pdf'): fig.savefig(F/f'{stem}.{ext}',dpi=320,bbox_inches='tight')
  plt.close(fig)
 specs=[('phase10_overall_dice_iou',['macro_dice','macro_iou'],'Overall VAL overlap metrics'),('phase10_fov_performance',['full_field_dice','roi_crop_dice'],'VAL performance by FOV'),('phase10_size_recall',['tiny_object_recall','small_object_recall','medium_object_recall','large_object_recall'],'FULL_FIELD original-space object recall by kub_size_v1')]
 for stem,cols,title in specs:
  long=comp.melt('model',cols,var_name='Metric',value_name='Value'); fig,ax=plt.subplots(figsize=(10,5)); sns.barplot(long,x='model',y='Value',hue='Metric',palette='colorblind',ax=ax); ax.set_ylim(0,1); ax.set_title(title); ax.tick_params(axis='x',rotation=15); emit(fig,stem)
 cats=[]
 for display,key,exp,stem in MODELS:
  x=read(stem,'category_summary'); x['model']=display; cats.append(x)
 cat=pd.concat(cats); fig,ax=plt.subplots(figsize=(10,5)); sns.barplot(cat,x='Category',y='Macro_Dice',hue='model',palette='colorblind',ax=ax); ax.set_ylim(0,1); ax.set_title('VAL macro Dice by KUB category'); emit(fig,'phase10_category_dice')
 fig,ax=plt.subplots(figsize=(7,5)); sns.scatterplot(comp,x='fp_components_per_image',y='object_recall',hue='model',s=130,palette='colorblind',ax=ax); ax.set_xlim(left=0); ax.set_ylim(0,1); ax.set_title('Object recall versus false-positive component burden'); emit(fig,'phase10_object_recall_vs_fp')
 fig,ax=plt.subplots(figsize=(7,5)); sns.scatterplot(comp,x='parameters',y='macro_dice',hue='model',s=130,palette='colorblind',ax=ax); ax.set_ylim(0,1); ax.set_title('Parameter count versus VAL macro Dice'); emit(fig,'phase10_parameters_vs_dice')
 long=comp.melt('model',['training_wall_time','mean_epoch_time'],var_name='Metric',value_name='Seconds'); fig,ax=plt.subplots(figsize=(10,5)); sns.barplot(long,x='model',y='Seconds',hue='Metric',palette='colorblind',ax=ax); ax.set_ylim(bottom=0); ax.tick_params(axis='x',rotation=15); ax.set_title('Training-time efficiency'); emit(fig,'phase10_training_efficiency')
 fig,ax=plt.subplots(figsize=(9,5))
 for display,key,exp,stem in MODELS:
  h=pd.read_csv(ROOT/'experiments'/exp/'history.csv'); ax.plot(h.epoch,h.val_dice,label=display)
 ax.set_ylim(0,1); ax.set_xlabel('Epoch'); ax.set_ylabel('VAL macro Dice'); ax.legend(); ax.set_title('VAL macro Dice learning curves'); emit(fig,'phase10_val_dice_learning_curves')

def qualitative():
 dataset=KUBDataset(ROOT/'manifests/val.csv','VAL',SegmentationTransform(512,False),T/'kub_val_samples_sized.csv'); base=read('phase9_unet','val_per_image'); index_map={dataset[i]['sample_id']:i for i in range(len(dataset))}
 ff=base[base.view_type=='FULL_FIELD']; roi=base[base.view_type=='ROI_CROP']; tiny=ff[ff.dominant_object_stratum=='TINY']; multi=ff[ff.component_count>1]
 ids=[ff.iloc[len(ff)//2].sample_id,roi.iloc[len(roi)//2].sample_id,tiny.iloc[len(tiny)//2].sample_id,multi.iloc[len(multi)//2].sample_id,base.sort_values('dice').iloc[0].sample_id]; ids=list(dict.fromkeys(ids)); device=torch.device('cuda'); preds={}; metric_tables={}
 for display,key,exp,stem in MODELS:
  model=create_model(key,in_channels=1,out_channels=1,base_channels=32).to(device); load_training_checkpoint(ROOT/'checkpoints'/exp/'best.pt',model,restore_rng=False,map_location=device); model.eval(); metric_tables[display]=read(stem,'val_per_image').set_index('sample_id'); values=[]
  for sid in ids:
   x=dataset[index_map[sid]]['image'].unsqueeze(0).to(device)
   with torch.no_grad(),torch.amp.autocast('cuda'): values.append((torch.sigmoid(model(x))[0,0].cpu().numpy()>=.5))
  preds[display]=values; del model; torch.cuda.empty_cache()
 fig,axes=plt.subplots(len(ids),6,figsize=(16,3*len(ids)),squeeze=False)
 for i,sid in enumerate(ids):
  item=dataset[index_map[sid]]; axes[i,0].imshow(item['image'][0],cmap='gray'); axes[i,0].set_title(f"{sid}\n{item['category']} | {item['view_type']}"); axes[i,1].imshow(item['mask'][0],cmap='gray'); axes[i,1].set_title('GT')
  for j,(display,*_) in enumerate(MODELS): row=metric_tables[display].loc[sid]; axes[i,j+2].imshow(preds[display][i],cmap='gray'); axes[i,j+2].set_title(f'{display}\nD={row.dice:.3f} I={row.iou:.3f}')
  for ax in axes[i]: ax.axis('off')
 fig.suptitle('Common deterministic VAL comparison'); fig.tight_layout()
 for ext in ('png','svg','pdf'): fig.savefig(Q/f'phase10_common_sample_comparison.{ext}',dpi=320,bbox_inches='tight')
 plt.close(fig)
 failure_ids=base.sort_values('dice').head(4).sample_id.tolist(); (Q/'phase10_failure_sample_ids.json').write_text(json.dumps(failure_ids,indent=2),encoding='utf-8')
 # Deterministic cross-model failure metrics table; avoids new model-specific selection.
 failure=[]
 for sid in failure_ids:
  for display in metric_tables:
   row=metric_tables[display].loc[sid]; failure.append({'sample_id':sid,'model':display,'category':row.category,'FOV':row.view_type,'Dice':row.dice,'IoU':row.iou,'FP_Components':row.false_positive_components})
 failure=pd.DataFrame(failure); save(failure,T/'phase10_kub_failure_comparison.csv')
 fig,ax=plt.subplots(figsize=(11,5)); sns.barplot(failure,x='sample_id',y='Dice',hue='model',palette='colorblind',ax=ax); ax.set_ylim(0,1); ax.tick_params(axis='x',rotation=20); ax.set_title('Deterministic cross-model failure comparison')
 for ext in ('png','svg','pdf'): fig.savefig(Q/f'phase10_failure_comparison.{ext}',dpi=320,bbox_inches='tight')
 plt.close(fig); return ids,failure_ids

def main():
 verify_manifests(); verify_test_lock(ROOT); comp,fair,multi=build_tables(); figures(comp,multi); common,failure=qualitative(); print(comp.to_string(index=False)); print('common',common,'failure',failure)
if __name__=='__main__': main()
