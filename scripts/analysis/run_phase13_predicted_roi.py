"""Phase 13 predicted ROI proposal search on KUB FULL_FIELD VAL only."""
import hashlib,json,sys
from itertools import product
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from PIL import Image
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.data.transforms import SegmentationTransform
from src.inference.predicted_roi import generate_predicted_rois,evaluate_roi_coverage,union_roi_area_fraction
from src.models.factory import create_model
from src.utils.checkpointing import load_training_checkpoint
from src.utils.manifest_guard import verify_manifests
from src.utils.test_lock import verify_test_lock
T=ROOT/'reports/tables'; C=ROOT/'data_cache/phase13_predicted_roi'; A=ROOT/'reports/audits'; C.mkdir(parents=True,exist_ok=True); A.mkdir(parents=True,exist_ok=True)
THRESHOLDS=(.20,.25,.30,.35,.40,.45,.50,.55,.60); MARGINS=(.05,.10,.15); TOPKS=(1,2,3,5); NMS=(.30,.50,.70)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cache_probabilities():
 samples=pd.read_csv(T/'kub_val_samples_sized.csv'); samples=samples[samples.view_type=='FULL_FIELD'].reset_index(drop=True); transform=SegmentationTransform(512,False); checkpoint=ROOT/'checkpoints/phase10_kub_unetpp_seed42_512/best.pt'; device=torch.device('cuda'); model=create_model('unetpp',in_channels=1,out_channels=1,base_channels=32).to(device); load_training_checkpoint(checkpoint,model,restore_rng=False,map_location=device); model.eval(); rows=[]
 with torch.inference_mode():
  for i,row in samples.iterrows():
   with Image.open(row.image_path) as f: image=f.convert('L')
   with Image.open(row.mask_path) as f: dummy=f.convert('L')
   tensor,_,meta=transform(image,dummy)
   with torch.amp.autocast('cuda'): probability=torch.sigmoid(model(tensor.unsqueeze(0).to(device)))[0,0].float().cpu().numpy()
   np.save(C/f'{row.sample_id}_probability_512.npy',probability)
   rows.append({'sample_id':row.sample_id,'original_H':row.height,'original_W':row.width,'scale':meta.scale,'resized_height':meta.resized_height,'resized_width':meta.resized_width,'padding_left':meta.padding[0],'padding_top':meta.padding[1],'padding_right':meta.padding[2],'padding_bottom':meta.padding[3],'coarse_max_probability':float(probability.max())})
   print(f'{i+1:03d}/106 {row.sample_id}',flush=True)
 cache=pd.DataFrame(rows); cache.to_csv(C/'metadata.csv',index=False); (C/'provenance.json').write_text(json.dumps({'checkpoint':str(checkpoint),'checkpoint_sha256':sha(checkpoint),'split':'VAL_ONLY','FOV':'FULL_FIELD','images':106,'input':512,'preprocessing':'Phase-10 canonical','inference_mode':True,'threshold_grid':list(THRESHOLDS),'test_reads':0},indent=2),encoding='utf-8'); return cache
class Meta:
 def __init__(self,row): self.scale=float(row.scale); self.resized_height=int(row.resized_height); self.resized_width=int(row.resized_width); self.padding=(int(row.padding_left),int(row.padding_top),int(row.padding_right),int(row.padding_bottom))
def load_gt(samples,components):
 data={}
 for _,row in samples.iterrows():
  with Image.open(row.mask_path) as f: mask=np.asarray(f.convert('L'))>0
  labeled,count=label(mask,np.ones((3,3),int)); source=components[components.sample_id==row.sample_id].sort_values('component_id'); items=[]
  if count!=len(source): raise RuntimeError(f'component mismatch {row.sample_id}')
  for cid,(_,meta) in enumerate(source.iterrows(),1):
   component_mask=labeled==cid; ys,xs=np.where(component_mask)
   items.append({'component_id':cid,'mask':component_mask,'min_y':int(ys.min()),'max_y':int(ys.max()),'min_x':int(xs.min()),'max_x':int(xs.max()),'component_pixels':int(meta.component_pixels),'component_ratio':float(meta.component_ratio),'kub_size_v1':meta.kub_size_v1,'global_detected':bool(meta.global_detected)})
  data[row.sample_id]={'mask':mask,'components':items}
 return data


def evaluate_config(config,samples,cache,ground_truth):
 component_rows=[]; image_rows=[]
 for _,row in samples.iterrows():
  sid=row.sample_id; meta=Meta(cache.loc[sid]); probability=np.load(C/f'{sid}_probability_512.npy'); proposals=generate_predicted_rois(probability,meta,(int(row.height),int(row.width)),*config); gt=ground_truth[sid]; coverage=evaluate_roi_coverage(proposals,gt['components']); total_area,max_area=union_roi_area_fraction(proposals,(int(row.height),int(row.width)))
  matched_any=set(); unmatched90=0
  for proposal in proposals:
   outcomes=[evaluate_roi_coverage([proposal],[component])[0] for component in gt['components']]
   if any(result['any_overlap'] for result in outcomes): matched_any.add(proposal['rank'])
   if not any(result['covered90'] for result in outcomes): unmatched90+=1
  unmatched=len(proposals)-len(matched_any)
  for component,result in zip(gt['components'],coverage): component_rows.append({**{k:v for k,v in component.items() if k!='mask'},**result,'sample_id':sid,'patient_id':row.patient_id,'category':row.category})
  covered=sum(x['covered90'] for x in coverage); tiny=[x for x,c in zip(coverage,gt['components']) if c['kub_size_v1']=='TINY']; image_rows.append({'sample_id':sid,'patient_id':row.patient_id,'category':row.category,'component_count_original':len(coverage),'proposal_count':len(proposals),'total_roi_area_fraction':total_area,'maximum_roi_area_fraction':max_area,'zero_proposal':not proposals,'components_gt':len(coverage),'components_covered90':covered,'component_recall90':covered/len(coverage),'tiny_gt':len(tiny),'tiny_covered90':sum(x['covered90'] for x in tiny),'unmatched_proposals':unmatched,'proposals_failing90_all_gt':unmatched90})
 components=pd.DataFrame(component_rows); images=pd.DataFrame(image_rows)
 def recall(stratum,column='covered90'):
  subset=components[components.kub_size_v1==stratum]; return subset[column].mean()
 summary={'proposal_threshold':config[0],'margin':config[1],'top_k':config[2],'nms_iou':config[3],'overall_recall90':components.covered90.mean(),'tiny_recall90':recall('TINY'),'small_recall90':recall('SMALL'),'medium_recall90':recall('MEDIUM'),'large_recall90':recall('LARGE'),'overall_recall50':components.covered50.mean(),'overall_any_overlap_recall':components.any_overlap.mean(),'mean_component_coverage':components.coverage_fraction.mean(),'median_component_coverage':components.coverage_fraction.median(),'mean_proposals_per_image':images.proposal_count.mean(),'median_proposals_per_image':images.proposal_count.median(),'zero_proposal_images':int(images.zero_proposal.sum()),'mean_total_roi_area_fraction':images.total_roi_area_fraction.mean(),'median_total_roi_area_fraction':images.total_roi_area_fraction.median(),'mean_maximum_roi_area_fraction':images.maximum_roi_area_fraction.mean(),'unmatched_proposals':int(images.unmatched_proposals.sum()),'mean_unmatched_proposals_per_image':images.unmatched_proposals.mean()}
 return components,images,summary

def save_table(frame,name):
 path=T/name; frame.to_csv(path,index=False); headers=list(frame.columns); lines=['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,row))+' |' for row in frame.itertuples(index=False,name=None)]; path.with_suffix('.md').write_text('\n'.join(lines)+'\n',encoding='utf-8'); path.with_suffix('.tex').write_text(frame.to_latex(index=False),encoding='utf-8')
def main():
 verify_manifests(); verify_test_lock(ROOT)
 if not torch.cuda.is_available() and not (C/'metadata.csv').exists(): raise RuntimeError('CUDA required to create probability cache')
 samples=pd.read_csv(T/'kub_val_samples_sized.csv'); samples=samples[samples.view_type=='FULL_FIELD'].reset_index(drop=True); source=pd.read_csv(T/'phase12_oracle_roi_per_component.csv'); assert len(samples)==106 and len(source)==156
 cache=pd.read_csv(C/'metadata.csv').set_index('sample_id') if (C/'metadata.csv').exists() else cache_probabilities().set_index('sample_id'); gt=load_gt(samples,source); rows=[]
 for index,config in enumerate(product(THRESHOLDS,MARGINS,TOPKS,NMS),1):
  _,_,summary=evaluate_config(config,samples,cache,gt); rows.append(summary); print(f'{index:03d}/324 {config} recall90={summary["overall_recall90"]:.4f}',flush=True)
 search=pd.DataFrame(rows); search['selected']=False; ranked=search.sort_values(['overall_recall90','tiny_recall90','mean_proposals_per_image','mean_total_roi_area_fraction','proposal_threshold','top_k','margin','nms_iou'],ascending=[False,False,True,True,False,True,True,True]); selected_index=ranked.index[0]; search.loc[selected_index,'selected']=True; search.to_csv(T/'phase13_predicted_roi_search.csv',index=False); selected=search.loc[selected_index]; config=(selected.proposal_threshold,selected.margin,int(selected.top_k),selected.nms_iou); components,images,_=evaluate_config(config,samples,cache,gt)
 global_image=pd.read_csv(T/'phase10_unetpp_val_per_image.csv').set_index('sample_id'); images['global_empty_prediction']=images.sample_id.map(global_image.empty_prediction); images['global_empty_but_roi_found']=images.global_empty_prediction & ~images.zero_proposal
 components['global_segmentation_detected']=components.global_detected; components['global_miss_but_roi_localized']=~components.global_detected & components.covered90; components['best_roi_coordinates']=components.best_roi_coordinates.map(lambda x:json.dumps(x) if x else '')
 components.to_csv(T/'phase13_predicted_roi_per_component.csv',index=False); images.to_csv(T/'phase13_predicted_roi_per_image.csv',index=False)
 selection_rule='lexicographic: max recall90, max TINY recall90, min proposals/image, min ROI area, higher threshold, smaller Top-K, smaller margin, stricter(lower) NMS IoU'; selected_table=pd.DataFrame([{**selected.drop('selected').to_dict(),'selection_rule':selection_rule}]); save_table(selected_table,'phase13_predicted_roi_selected_config.csv')
 size=[]
 for stratum in ['TINY','SMALL','MEDIUM','LARGE']:
  subset=components[components.kub_size_v1==stratum]; size.append({'Size':stratum,'GT':len(subset),'covered90':int(subset.covered90.sum()),'missed':int((~subset.covered90).sum()),'recall90':subset.covered90.mean(),'mean_coverage':subset.coverage_fraction.mean(),'global_segmentation_detected':int(subset.global_detected.sum()),'global_misses_localized_by_predicted_roi':int(subset.global_miss_but_roi_localized.sum())})
 save_table(pd.DataFrame(size),'phase13_predicted_roi_size_summary.csv')
 multi=images[images.component_count_original>1]; save_table(pd.DataFrame([{'image_count':len(multi),'component_count':multi.components_gt.sum(),'all_localized_images':int((multi.components_covered90==multi.components_gt).sum()),'partial_localized_images':int(((multi.components_covered90>0)&(multi.components_covered90<multi.components_gt)).sum()),'none_localized_images':int((multi.components_covered90==0).sum()),'component_recall90':multi.components_covered90.sum()/multi.components_gt.sum(),'mean_fraction_components_covered':multi.component_recall90.mean(),'mean_proposals_per_image':multi.proposal_count.mean(),'top_k_saturation_images':int((multi.components_gt>config[2]).sum())}]),'phase13_predicted_roi_multicomponent.csv')
 print('SELECTED',config,selected.to_dict())
if __name__=='__main__': main()

