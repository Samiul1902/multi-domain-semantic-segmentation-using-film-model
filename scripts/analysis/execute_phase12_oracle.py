"""Execute corrected Phase-12 Oracle ROI inference on KUB FULL_FIELD VAL only."""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.analysis.oracle_roi import compute_square_crop,extract_gt_components,run_oracle_roi_image
from src.metrics.segmentation import hd95
from src.models.factory import create_model
from src.utils.checkpointing import load_training_checkpoint
from src.utils.manifest_guard import verify_manifests
from src.utils.test_lock import verify_test_lock
T=ROOT/'reports/tables'; C=ROOT/'data_cache/phase12_oracle_roi'; C.mkdir(parents=True,exist_ok=True); MARGINS=(10,25,50)
def mask_metrics(pred,gt):
 p=np.asarray(pred,bool); g=np.asarray(gt,bool); tp=int((p&g).sum()); fp=int((p&~g).sum()); fn=int((~p&g).sum()); e=1e-7
 return {'dice':(2*tp+e)/(2*tp+fp+fn+e),'iou':(tp+e)/(tp+fp+fn+e),'precision':(tp+e)/(tp+fp+e),'recall':(tp+e)/(tp+fn+e),'tp':tp,'fp':fp,'fn':fn}
def main():
 verify_manifests(); verify_test_lock(ROOT)
 if not torch.cuda.is_available(): raise RuntimeError('CUDA required; do not run long CPU Oracle inference')
 device=torch.device('cuda'); checkpoint=ROOT/'checkpoints/phase10_kub_unetpp_seed42_512/best.pt'; model=create_model('unetpp',in_channels=1,out_channels=1,base_channels=32).to(device); load_training_checkpoint(checkpoint,model,restore_rng=False,map_location=device); model.eval()
 samples=pd.read_csv(T/'kub_val_samples_sized.csv'); samples=samples[samples.view_type=='FULL_FIELD'].reset_index(drop=True); source=pd.read_csv(T/'kub_val_components_sized.csv'); source=source[source.view_type=='FULL_FIELD'].copy(); global_img=pd.read_csv(T/'phase10_unetpp_val_per_image.csv').set_index('sample_id'); global_comp=pd.read_csv(T/'phase10_unetpp_val_per_component.csv'); assert len(samples)==106 and len(source)==156
 image_rows=[]; component_rows=[]; geometry_rows=[]
 with torch.inference_mode():
  for index,row in samples.iterrows():
   sid=row.sample_id
   with Image.open(row.mask_path) as f: gt=np.asarray(f.convert('L'))>0
   h,w=gt.shape; comps,labels=extract_gt_components(gt); metadata=source[source.sample_id==sid].sort_values('component_id')
   if len(comps)!=len(metadata): raise RuntimeError(f'component mismatch {sid}')
   results={}; metrics={}
   for margin in MARGINS:
    result=run_oracle_roi_image(row.image_path,row.mask_path,model,device,margin/100,0.5); results[margin]=result; metrics[margin]=mask_metrics(result['mask_combined'],gt); metrics[margin].update(hd95(result['mask_combined'],gt)); directory=C/sid; directory.mkdir(parents=True,exist_ok=True); np.save(directory/f'probability_margin{margin}.npy',result['prob_combined']); np.save(directory/f'mask_margin{margin}.npy',result['mask_combined'])
   g=global_img.loc[sid]; gc=global_comp[global_comp.sample_id==sid].set_index('original_component_id'); image={'sample_id':sid,'patient_id':row.patient_id,'category':row.category,'original_H':h,'original_W':w,'component_count_original':len(comps),'global_dice':g.dice,'global_iou':g.iou,'global_precision':g.precision,'global_recall':g.recall,'global_hd95':g.hd95,'global_hd95_valid':g.hd95_valid,'global_empty_prediction':g.empty_prediction,'global_tp':g.true_positive_pixels,'global_fp':g.false_positive_pixels,'global_fn':g.false_negative_pixels,'global_detected_components_original':int(gc.detected.sum())}
   for margin in MARGINS:
    for name in ['dice','iou','precision','recall','tp','fp','fn','hd95','hd95_valid','empty_prediction']: image[f'oracle{margin}_{name}']=metrics[margin][name]
    image[f'oracle{margin}_detected_components_original']=sum(bool((results[margin]['mask_combined']&(labels==c['component_id'])).sum()) for c in comps)
   image['dice_delta_oracle25_minus_global']=image['oracle25_dice']-float(g.dice); image_rows.append(image)
   for c,(_,meta) in zip(comps,metadata.iterrows()):
    cid=c['component_id']; mask=labels==cid; entry={'sample_id':sid,'patient_id':row.patient_id,'category':row.category,'component_id':cid,'component_pixels':int(meta.component_pixels),'component_ratio':float(meta.component_ratio),'kub_size_v1':meta.size_stratum,'global_detected':bool(gc.loc[cid].detected),'bbox_min_y':c['min_y'],'bbox_max_y':c['max_y'],'bbox_min_x':c['min_x'],'bbox_max_x':c['max_x'],'original_H':h,'original_W':w}
    geometry={'sample_id':sid,'patient_id':row.patient_id,'category':row.category,'component_id':cid,'component_pixels':int(meta.component_pixels),'component_ratio':float(meta.component_ratio),'kub_size_v1':meta.size_stratum,'original_H':h,'original_W':w,**{f'bbox_{k}':c[k] for k in ['min_y','max_y','min_x','max_x','bbox_height','bbox_width']}}
    for margin in MARGINS:
     detected=bool((results[margin]['mask_combined']&mask).sum()); entry[f'oracle{margin}_detected']=detected; geom=compute_square_crop(c,(h,w),margin/100)
     for field in ['y1','y2','x1','x2','clip_y1','clip_y2','clip_x1','clip_x2','pad_top','pad_bottom','pad_left','pad_right','crop_side_pixels','effective_magnification']: geometry[f'margin{margin}_{field}']=geom[field]
    entry['recovered_by_oracle25']=entry['oracle25_detected'] and not entry['global_detected']; entry['lost_by_oracle25']=entry['global_detected'] and not entry['oracle25_detected']; component_rows.append(entry); geometry_rows.append(geometry)
   print(f'{index+1:03d}/106 {sid}',flush=True)
 pd.DataFrame(image_rows).to_csv(T/'phase12_oracle_roi_per_image.csv',index=False); pd.DataFrame(component_rows).to_csv(T/'phase12_oracle_roi_per_component.csv',index=False); pd.DataFrame(geometry_rows).to_csv(T/'phase12_oracle_crop_geometry.csv',index=False)
 (C/'provenance.json').write_text(json.dumps({'checkpoint':str(checkpoint),'threshold':.5,'margins':[.1,.25,.5],'population':'KUB FULL_FIELD VAL','images':106,'components':156,'fusion':'pixelwise_max_probability_then_threshold','model_input_channels':1,'gt_model_input':False,'test_reads':0},indent=2),encoding='utf-8')
if __name__=='__main__': main()
