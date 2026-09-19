"""Deterministically infer VAL masks needed only for Phase-11 visual panels."""
from pathlib import Path
import json,sys
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.data.kub_dataset import KUBDataset
from src.data.transforms import SegmentationTransform
from src.models.factory import create_model
from src.utils.checkpointing import load_training_checkpoint
T=ROOT/'reports/tables'; Q=ROOT/'reports/qualitative/phase11_kub_failure_analysis'; Q.mkdir(parents=True,exist_ok=True)
x=pd.read_csv(T/'phase11_kub_failure_analysis_per_image.csv'); multi=pd.read_csv(T/'phase11_kub_multicomponent_failure.csv'); dataset=KUBDataset(ROOT/'manifests/val.csv','VAL',SegmentationTransform(512,False),T/'kub_val_samples_sized.csv'); index={dataset[i]['sample_id']:i for i in range(len(dataset))}
def first(frame,sort,ascending=False): return frame.sort_values(sort,ascending=ascending).iloc[0].sample_id
selectors=[('LOWEST_DICE_FULL_FIELD',first(x[x.FOV=='FULL_FIELD'],'dice',True)),('MISSED_TINY',first(x[x.failure_labels.str.contains('MISSED_TINY_COMPONENT',na=False)],'dice',True)),('PARTIAL_MULTI',first(x[x.failure_labels.str.contains('PARTIAL_MULTI_COMPONENT_DETECTION',na=False)],'dice',True)),('HIGH_FP',first(x,'fp_eval_components',False)),('EMPTY_PREDICTION',first(x[x.empty_prediction],'dice',True)),('HIGH_HD95_VALID',first(x[x.hd95_valid],'hd95',False))]
ids=[]; labels={}
for label_name,sid in selectors:
 if sid not in ids: ids.append(sid)
 labels.setdefault(sid,[]).append(label_name)
device=torch.device('cuda'); model=create_model('unetpp',in_channels=1,out_channels=1,base_channels=32).to(device); load_training_checkpoint(ROOT/'checkpoints/phase10_kub_unetpp_seed42_512/best.pt',model,restore_rng=False,map_location=device); model.eval(); table=x.set_index('sample_id')
fig,axes=plt.subplots(len(ids),4,figsize=(12,3*len(ids)),squeeze=False)
for i,sid in enumerate(ids):
 item=dataset[index[sid]]; image=item['image'][0].numpy(); gt=item['mask'][0].numpy()>0
 with torch.no_grad(),torch.amp.autocast('cuda'): pred=torch.sigmoid(model(item['image'].unsqueeze(0).to(device)))[0,0].cpu().numpy()>=.5
 overlay=np.zeros((*gt.shape,3)); overlay[...,0]=gt & ~pred; overlay[...,1]=gt & pred; overlay[...,2]=pred & ~gt; row=table.loc[sid]; title=f"{sid}\n{row.category} | {row.FOV}\nD={row.dice:.3f} I={row.iou:.3f} P={row.precision:.3f} R={row.recall:.3f}\n{';'.join(labels[sid])}"
 for j,(arr,cmap,name) in enumerate([(image,'gray','Image'),(gt,'gray','GT'),(pred,'gray','UNet++ prediction'),(overlay,None,'Error: FN red, TP green, FP blue')]): axes[i,j].imshow(arr,cmap=cmap); axes[i,j].axis('off'); axes[i,j].set_title(title if j==0 else name,fontsize=8)
fig.tight_layout()
for ext in ('png','svg','pdf'): fig.savefig(Q/f'phase11_unetpp_failure_panel.{ext}',dpi=320,bbox_inches='tight')
plt.close(fig); (Q/'phase11_unetpp_failure_selection.json').write_text(json.dumps({'selectors':selectors,'unique_sample_ids':ids},indent=2),encoding='utf-8')
# Same hard cases across all models.
models=[('U-Net','unet','phase9_kub_unet_baseline_seed42_512'),('Attention U-Net','attention_unet','phase10_kub_attention_unet_seed42_512'),('UNet++','unetpp','phase10_kub_unetpp_seed42_512'),('DeepLabV3+','deeplabv3plus','phase10_kub_deeplabv3plus_seed42_512')]; hard=ids[:4]; preds={}
for display,key,exp in models:
 m=create_model(key,in_channels=1,out_channels=1,base_channels=32).to(device); load_training_checkpoint(ROOT/'checkpoints'/exp/'best.pt',m,restore_rng=False,map_location=device); m.eval(); preds[display]=[]
 for sid in hard:
  with torch.no_grad(),torch.amp.autocast('cuda'): preds[display].append(torch.sigmoid(m(dataset[index[sid]]['image'].unsqueeze(0).to(device)))[0,0].cpu().numpy()>=.5)
 del m; torch.cuda.empty_cache()
fig,axes=plt.subplots(len(hard),6,figsize=(16,3*len(hard)),squeeze=False)
for i,sid in enumerate(hard):
 item=dataset[index[sid]]; axes[i,0].imshow(item['image'][0],cmap='gray'); axes[i,0].set_title(f"{sid}\n{item['category']} | {item['view_type']}\n{';'.join(labels[sid])}",fontsize=8); axes[i,1].imshow(item['mask'][0],cmap='gray'); axes[i,1].set_title('GT')
 for j,(display,key,exp) in enumerate(models): axes[i,j+2].imshow(preds[display][i],cmap='gray'); axes[i,j+2].set_title(display)
 for ax in axes[i]: ax.axis('off')
fig.tight_layout()
for ext in ('png','svg','pdf'): fig.savefig(Q/f'phase11_cross_model_hard_case_panel.{ext}',dpi=320,bbox_inches='tight')
plt.close(fig); (Q/'phase11_cross_model_selection.json').write_text(json.dumps(hard,indent=2),encoding='utf-8'); print(selectors)
