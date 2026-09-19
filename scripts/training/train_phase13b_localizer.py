"""Train/resume one predeclared Phase-13B KUB heatmap localizer candidate."""
import argparse,datetime,json,math,sys,time
from itertools import product
from pathlib import Path
import numpy as np
import pandas as pd
import torch,yaml
from PIL import Image
from scipy.ndimage import label
from torch.utils.data import DataLoader
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from src.data.kub_localizer_dataset import KUBLocalizerDataset
from src.inference.learned_roi import generate_localizer_rois
from src.inference.predicted_roi import evaluate_roi_coverage,union_roi_area_fraction
from src.losses.localization import SoftFocalDiceLoss
from src.losses.localization import SoftFocalDiceLoss, CenterNetFocalLoss
from src.models.factory import create_model
from src.utils.checkpointing import save_training_checkpoint,load_training_checkpoint
from src.utils.experiment import register_experiment
from src.utils.manifest_guard import verify_manifests
from src.utils.reproducibility import set_seed,make_generator,seed_worker
from src.utils.test_lock import verify_test_lock

T=ROOT/'reports/tables';CONFIG=ROOT/'configs/kub/phase13b_localizer.yaml';THRESHOLDS=(.1,.2,.3,.4,.5);MARGINS=(.1,.2);TOPKS=(3,5)

class Meta:
 def __init__(self,scale,rh,rw,padding):self.scale=float(scale);self.resized_height=int(rh);self.resized_width=int(rw);self.padding=tuple(int(x) for x in padding)

def gt_components(mask_path, component_metadata):
 metadata=component_metadata.sort_values('component_id');items=[]
 for _,meta in metadata.iterrows():
  items.append({'component_id':int(meta.component_id),'min_y':int(meta.min_y),'max_y':int(meta.max_y),'min_x':int(meta.min_x),'max_x':int(meta.max_x),'kub_size_v1':meta.kub_size_v1,'hard_tiny':bool(meta.hard_tiny),'global_empty_image':bool(meta.global_empty_image)})
 return items

def evaluate(model,loader,criterion,device,resolution,component_table):
 from src.inference.predicted_roi import extract_predicted_components, non_max_suppression, apply_context_margin
 from tqdm import tqdm
 model.eval();losses=[];cache=[]
 all_max_probs=[];all_means=[];all_stds=[];fg_fractions={.1:[],.2:[],.3:[],.4:[],.5:[]}
 with torch.inference_mode():
  for batch in tqdm(loader, desc="[Val]", dynamic_ncols=True):
   image=batch['image'].to(device);target=batch['heatmap'].to(device)
   with torch.amp.autocast('cuda'):logits=model(image);loss=criterion(logits,target)
   losses.append(loss.item());probs=torch.sigmoid(logits).float().cpu().numpy()
   for i,sid in enumerate(batch['sample_id']):
    pm=probs[i,0]
    all_max_probs.append(float(pm.max()))
    all_means.append(float(pm.mean()))
    all_stds.append(float(pm.std()))
    for t in (.1,.2,.3,.4,.5):
     fg_fractions[t].append(float((pm>t).mean()))
    cache.append({'sample_id':sid,'patient_id':batch['patient_id'][i],'category':batch['category'][i],'mask_path':batch['mask_path'][i],'probability':pm,'height':int(batch['original_height'][i]),'width':int(batch['original_width'][i]),'meta':Meta(batch['scale'][i],batch['resized_height'][i],batch['resized_width'][i],batch['padding'][i])})
 mean_max_prob=float(np.mean(all_max_probs))
 median_max_prob=float(np.median(all_max_probs))
 p10_max_prob=float(np.percentile(all_max_probs,10))
 p50_max_prob=float(np.percentile(all_max_probs,50))
 p90_max_prob=float(np.percentile(all_max_probs,90))
 heatmap_diag={
  'mean_prob':float(np.mean(all_means)),
  'std_prob':float(np.mean(all_stds)),
  'mean_max_prob':mean_max_prob,
  'median_max_prob':median_max_prob,
  'p10_max_prob':p10_max_prob,
  'p50_max_prob':p50_max_prob,
  'p90_max_prob':p90_max_prob,
  'fg_frac_0.1':float(np.mean(fg_fractions[.1])),
  'fg_frac_0.2':float(np.mean(fg_fractions[.2])),
  'fg_frac_0.3':float(np.mean(fg_fractions[.3])),
  'fg_frac_0.4':float(np.mean(fg_fractions[.4])),
  'fg_frac_0.5':float(np.mean(fg_fractions[.5]))
 }
 for item in cache:
  metadata=component_table[component_table.sample_id==item['sample_id']];item['gt']=gt_components(item['mask_path'],metadata);item['comps']={}
  for t in THRESHOLDS:item['comps'][t]=extract_predicted_components(item['probability'],t,(item['height'],item['width']),item['meta'])
 rows=[]
 for threshold,margin,top_k in product(THRESHOLDS,MARGINS,TOPKS):
  cover=[];image_metrics=[]
  for item in cache:
   components=item['comps'][threshold][:100];components=non_max_suppression(components,.3)[:top_k];proposals=[]
   for rank,component in enumerate(components,start=1):proposals.append({'rank':rank,'score':component['max_probability'],'mean_probability':component['mean_probability'],'proposal_component_pixels_512':component['component_pixels_512'],'proposal_bbox':component['bbox'],'crop_geometry':apply_context_margin(component['bbox'],(item['height'],item['width']),margin)})
   gt=item['gt'];out=evaluate_roi_coverage(proposals,gt);area,_=union_roi_area_fraction(proposals,(item['height'],item['width']));cover.extend([{**result,'sample_id':item['sample_id'],**{key:component[key] for key in ('kub_size_v1','hard_tiny','global_empty_image')}} for result,component in zip(out,gt)]);image_metrics.append((len(proposals),area))
  frame=pd.DataFrame(cover);hard=frame[frame.hard_tiny];empty=frame[frame.global_empty_image];tiny=frame[frame.kub_size_v1=='TINY'];multi_ids=set(component_table.groupby('sample_id').size().loc[lambda values:values>1].index);multi=frame[frame.sample_id.isin(multi_ids)]
  mean_area=float(np.mean([x[1] for x in image_metrics]))
  feasible=(mean_area<=0.10) and (float(np.mean([x[0] for x in image_metrics]))<=5.0)
  rows.append({'threshold':threshold,'margin':margin,'top_k':top_k,'nms_iou':.3,'hard_tiny_recovered90':int(hard.covered90.sum()),'global_empty_images_covered90':int(empty.groupby('sample_id').covered90.any().sum()),'global_empty_components_covered90':int(empty.covered90.sum()),'tiny_recall90':float(tiny.covered90.mean()) if len(tiny) else 0.0,'overall_recall90':float(frame.covered90.mean()) if len(frame) else 0.0,'overall_recall50':float(frame.covered50.mean()) if len(frame) else 0.0,'any_overlap_recall':float(frame.any_overlap.mean()) if len(frame) else 0.0,'mean_coverage':float(frame.coverage_fraction.mean()) if len(frame) else 0.0,'multi_component_recall90':float(multi.covered90.mean()) if len(multi) else 0.0,'mean_proposals_per_image':float(np.mean([x[0] for x in image_metrics])),'mean_roi_area_fraction':mean_area,'feasible':feasible,'p90_roi_area_fraction':float(np.percentile([x[1] for x in image_metrics],90)),'max_roi_area_fraction':float(max([x[1] for x in image_metrics])),'median_roi_area_fraction':float(np.median([x[1] for x in image_metrics]))})
 return float(np.mean(losses)),pd.DataFrame(rows),cache,heatmap_diag

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--resolution',type=int,choices=[512,768],default=512)
 parser.add_argument('--heatmap_resolution',type=int,default=512)
 parser.add_argument('--sigma',type=float,required=True)
 parser.add_argument('--batch',type=int,default=4)
 parser.add_argument('--accum',type=int,default=1)
 parser.add_argument('--exp_id',type=str,default='')
 args=parser.parse_args();verify_manifests();verify_test_lock(ROOT)
 if not torch.cuda.is_available():raise RuntimeError('CUDA required')
 config=yaml.safe_load(CONFIG.read_text());resolution,sigma=args.resolution,args.sigma
 h_res = args.heatmap_resolution
 exp_id=args.exp_id or f'phase13b_kub_localizer_r{resolution}_h{h_res}_s{sigma}_seed42_v1'
 exp=ROOT/'experiments'/exp_id;chk=ROOT/'checkpoints'/exp_id
 exp.mkdir(parents=True,exist_ok=True);chk.mkdir(parents=True,exist_ok=True)
 set_seed(42,True);device=torch.device('cuda')
 train_ds=KUBLocalizerDataset(T/'kub_train_samples_sized.csv','TRAIN',resolution,sigma,heatmap_resolution=h_res)
 val_ds=KUBLocalizerDataset(T/'kub_val_samples_sized.csv','VAL',resolution,sigma,heatmap_resolution=h_res)
 assert len(train_ds)==771 and len(val_ds)==106
 phase13_components=pd.read_csv(T/'phase13_predicted_roi_per_component.csv')
 phase13_images=pd.read_csv(T/'phase13_predicted_roi_per_image.csv')
 hard_keys=set(zip(phase13_components[(phase13_components.kub_size_v1=='TINY')&~phase13_components.global_detected].sample_id,phase13_components[(phase13_components.kub_size_v1=='TINY')&~phase13_components.global_detected].component_id))
 empty_ids=set(phase13_images[phase13_images.global_empty_prediction].sample_id)
 component_table=phase13_components[['sample_id','component_id','min_y','max_y','min_x','max_x','kub_size_v1','global_detected']].copy()
 component_table['hard_tiny']=[(sid,cid) in hard_keys for sid,cid in zip(component_table.sample_id,component_table.component_id)]
 component_table['global_empty_image']=component_table.sample_id.isin(empty_ids)
 assert component_table.hard_tiny.sum()==16 and len(empty_ids)==7
 latest=chk/'latest.pt';batch=args.batch;acc=args.accum;generator_state=None
 model=create_model('kub_localizer',in_channels=1,out_channels=1,base_channels=16,heatmap_resolution=h_res).to(device)
 optimizer=torch.optim.AdamW(model.parameters(),lr=1e-4,weight_decay=1e-4)
 scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(optimizer,100)
 scaler=torch.amp.GradScaler('cuda')
 criterion=CenterNetFocalLoss(alpha=2.0, beta=4.0)
 history=[];start_epoch=1;best_score=None;bad_epochs=0;global_step=0
 runtime=json.loads(json.dumps(config))
 runtime['candidate']={'resolution':resolution,'heatmap_resolution':h_res,'sigma':sigma,'physical_batch':batch,'accumulation':acc,'effective_batch':batch*acc,'selection_version':'phase13b_feasible_selection_v1'}
 metadata=json.loads((ROOT/'manifests/manifest_metadata.json').read_text())
 if latest.exists():
  state=load_training_checkpoint(latest,model,optimizer,scheduler,scaler,True,device);start_epoch=state['epoch']+1;history=state['training_history'];best_score=tuple(state['best_validation_score']) if state.get('best_validation_score') else None;early=state.get('early_stopping_state') or {};bad_epochs=int(early.get('bad_epochs',0));global_step=state['global_step'];generator_state=(state.get('loader_generator_states') or {}).get('train')
  if (chk/'best.pt').exists():
   b_st=torch.load(chk/'best.pt',map_location='cpu',weights_only=False)
   if b_st.get('best_validation_score'):
    best_score=tuple(b_st['best_validation_score'])
    best_ep=b_st.get('epoch', start_epoch-1)
    bad_epochs=max(0, (start_epoch - 1) - best_ep)
 generator=make_generator(42)
 if generator_state is not None:generator.set_state(generator_state.detach().cpu().to(torch.uint8))
 train_loader=DataLoader(train_ds,batch_size=batch,shuffle=True,num_workers=0,pin_memory=True,worker_init_fn=seed_worker,generator=generator)
 val_loader=DataLoader(val_ds,batch_size=batch,shuffle=False,num_workers=0,pin_memory=True,worker_init_fn=seed_worker,generator=make_generator(42))
 record={'experiment_id':exp_id,'phase':'13B','dataset':'KUB','split_scope':'FULL_FIELD_TRAIN_VAL','model':'kub_localizer','architecture':'compact_unet_heatmap','seed':42,'image_size':resolution,'heatmap_size':h_res,'batch_size':batch,'effective_batch_size':batch*acc,'optimizer':'AdamW','learning_rate':1e-4,'weight_decay':1e-4,'scheduler':'CosineAnnealingLR','loss':'CenterNetFocal','threshold':'proposal_grid','manifest_version':'phase4_v2','status':'RUNNING','start_time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checkpoint_path':str(chk/'best.pt'),'best_val_dice':'LOCALIZATION_NOT_DICE','notes':f'sigma={sigma}; heatmap={h_res}; no pretrained weights'}
 register_experiment(record,ROOT);log=(exp/'training.log').open('a' if start_epoch>1 else 'w',encoding='utf-8')
 hard=pd.read_csv(T/'phase13_predicted_roi_per_component.csv');hard=set(zip(hard[(hard.kub_size_v1=='TINY')&~hard.global_detected].sample_id,hard[(hard.kub_size_v1=='TINY')&~hard.global_detected].component_id));empty=set(pd.read_csv(T/'phase13_predicted_roi_per_image.csv').query('global_empty_prediction').sample_id)
 
 # Verify initial p (before optimizer step 1)
 if start_epoch == 1:
  with torch.no_grad():
   init_test = torch.sigmoid(model(torch.zeros(1, 1, resolution, resolution, device=device)))
   init_p = float(init_test.mean())
   print(f"Pre-training verification: initial p = {init_p:.6f}")
   if not (0.09 <= init_p <= 0.11):
    raise RuntimeError(f"Initialization check failed: initial p={init_p:.6f}, expected ~0.10")

 for epoch in range(start_epoch,101):
  model.train();optimizer.zero_grad(set_to_none=True);losses=[];started=time.perf_counter();torch.cuda.reset_peak_memory_stats()
  from tqdm import tqdm
  train_pbar = tqdm(train_loader, desc=f"Epoch {epoch:03d}/100 [Train]", dynamic_ncols=True)
  for index,b in enumerate(train_pbar):
   with torch.amp.autocast('cuda'):loss=criterion(model(b['image'].to(device)),b['heatmap'].to(device))/acc
   scaler.scale(loss).backward();scaler.step(optimizer);scaler.update();optimizer.zero_grad(set_to_none=True);losses.append(loss.item()*acc);global_step+=1
   train_pbar.set_postfix({'loss': f"{np.mean(losses):.4f}"})
  
  val_loss,search,cache,heatmap_diag=evaluate(model,val_loader,criterion,device,resolution,component_table)
  feasible_configs=search[search.feasible]
  if len(feasible_configs)>0:
   best_cfg=feasible_configs.sort_values(['tiny_recall90','overall_recall90','mean_roi_area_fraction','mean_proposals_per_image','threshold','top_k','margin'],ascending=[False,False,True,True,False,True,True]).iloc[0]
   score=(float(best_cfg.tiny_recall90),float(best_cfg.overall_recall90),-float(best_cfg.mean_roi_area_fraction),-float(val_loss))
   improved=best_score is None or score>best_score
   bad_epochs=0 if improved else bad_epochs+1
   if improved: best_score=score
  else:
   best_cfg=search.sort_values(['mean_roi_area_fraction','mean_proposals_per_image'],ascending=[True,True]).iloc[0]
   score=None
   improved=False
   bad_epochs+=1
  scheduler.step()
  epoch_seconds=time.perf_counter()-started
  row={'epoch':epoch,'train_loss':float(np.mean(losses)),'val_loss':val_loss,'val_hard_tiny_recovered90':best_cfg.hard_tiny_recovered90,'val_global_empty_images_covered90':best_cfg.global_empty_images_covered90,'val_tiny_recall90':best_cfg.tiny_recall90,'val_overall_recall90':best_cfg.overall_recall90,'learning_rate':optimizer.param_groups[0]['lr'],'epoch_seconds':epoch_seconds,'peak_gpu_allocated':torch.cuda.max_memory_allocated(),'peak_gpu_reserved':torch.cuda.max_memory_reserved(),'feasible_config_count':len(feasible_configs),'localization_status':'FEASIBLE' if len(feasible_configs)>0 else 'INFEASIBLE','mean_roi_area_fraction':best_cfg.mean_roi_area_fraction,'mean_proposals_per_image':best_cfg.mean_proposals_per_image,'mean_max_heatmap':heatmap_diag['mean_max_prob'],'median_max_heatmap':heatmap_diag['median_max_prob']}
  history.append(row);early={'best':best_score,'bad_epochs':bad_epochs,'patience':15,'stopped':bad_epochs>=15 and best_score is not None}
  common=(model,optimizer,scheduler,scaler,epoch,global_step,best_score if best_score else (),runtime,42,history,'phase4_v2',metadata['hashes'],exp_id,'kub_localizer',resolution,float(best_cfg.threshold))
  save_training_checkpoint(latest,*common,early_stopping_state=early,loader_generator_states={'train':generator.get_state()})
  if improved:save_training_checkpoint(chk/'best.pt',*common,early_stopping_state=early,loader_generator_states={'train':generator.get_state()});best_score=score
  
  # Atomic write for history.csv with Windows retry
  tmp_csv = exp/'history.tmp.csv'
  pd.DataFrame(history).to_csv(tmp_csv,index=False)
  for _attempt in range(10):
   try:
    tmp_csv.replace(exp/'history.csv')
    break
   except PermissionError:
    time.sleep(0.5)
  search.to_csv(exp/f'val_search_epoch{epoch:03d}.csv',index=False)
  
  line=f'Epoch {epoch:03d} train_loss={row["train_loss"]:.6f} val_loss={val_loss:.6f} hard_tiny={int(best_cfg.hard_tiny_recovered90)}/16 empty={int(best_cfg.global_empty_images_covered90)}/7 tiny90={best_cfg.tiny_recall90:.6f} recall90={best_cfg.overall_recall90:.6f} feasible={len(feasible_configs)} best={improved} time={epoch_seconds:.1f}s\n'
  print(line.strip(),flush=True);log.write(line);log.flush()
  
  # Final tqdm-like output string summarizing the epoch as requested
  print(f"--> [Epoch {epoch:03d}/100] Tiny90: {best_cfg.tiny_recall90:.4f} | Recall90: {best_cfg.overall_recall90:.4f} | HardTiny: {int(best_cfg.hard_tiny_recovered90)}/16 | Empty: {int(best_cfg.global_empty_images_covered90)}/7 | Feasible: {len(feasible_configs)}/20 | Area: {best_cfg.mean_roi_area_fraction:.4f} | Props: {best_cfg.mean_proposals_per_image:.2f} | Patience: {bad_epochs}/15 | Time: {epoch_seconds:.1f}s")
  if early['stopped']:break
 status = 'TRAINED' if best_score is not None else 'NO_FEASIBLE_LOCALIZER'
 log.close();record.update(status=status,end_time=datetime.datetime.now(datetime.timezone.utc).isoformat(),notes=f'sigma={sigma}; completed epochs={len(history)}; candidate evaluation pending');register_experiment(record,ROOT)

if __name__=='__main__':main()