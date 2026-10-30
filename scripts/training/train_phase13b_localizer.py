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
from src.training.clean_v3_selection import select_h3_supply_epoch, build_h3_supply_selection_tuple, H3_SUPPLY_TERM_NAMES

T=ROOT/'reports/tables';CONFIG=ROOT/'configs/kub/phase13b_localizer.yaml';THRESHOLDS=(.1,.2,.3,.4,.5);MARGINS=(.1,.2);TOPKS=(3,5)
H3_FROZEN_SELECTION_CONFIG=(0.10,0.20,5)  # threshold, margin, top_k (nms fixed at 0.30)
H3_EXPERIMENT_ID='h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3'
H3_CHECKPOINT_NAMESPACE='checkpoints/h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3/'
H3_MANIFEST_DIR=ROOT/'manifests'/'phase4_v3'
H3_A_REF=13.0
H3_ORPHAN_QUARANTINED='ef36ad8332b2f33882dc668a5b6846e5'

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

def h3_supply_axis_metrics(cache, component_table, thr, margin, top_k, nms):
    """Frozen-decode supply-axis metrics for H3 checkpoint selection + §9 eval.

    Reproduces the EXACT fixed-decode proposal generation used inside evaluate()
    (threshold=thr, margin=margin, top_k=top_k, nms=nms), then computes
    component-level coverage over the GT component table. Returns a flat dict of
    the supply-axis quantities required by the supervisor ruling (per-size recall,
    zero-proposal GT/TINY, any-overlap recall, coverage>=0.5/0.9, precision,
    background fraction, proposals/image).
    """
    from src.inference.predicted_roi import (extract_predicted_components,
        non_max_suppression, apply_context_margin, evaluate_roi_coverage)
    per_component=[]; proposals_per_image=[]; overlapping_proposals=0; total_proposals=0
    for item in cache:
        components=item['comps'][thr][:100]
        components=non_max_suppression(components,nms)[:top_k]
        proposals=[]
        for rank,component in enumerate(components,start=1):
            proposals.append({'rank':rank,'score':component['max_probability'],'mean_probability':component['mean_probability'],'proposal_component_pixels_512':component['component_pixels_512'],'proposal_bbox':component['bbox'],'crop_geometry':apply_context_margin(component['bbox'],(item['height'],item['width']),margin)})
        proposals_per_image.append(len(proposals)); total_proposals+=len(proposals)
        metadata=component_table[component_table.sample_id==item['sample_id']]
        gt=gt_components(item['mask_path'],metadata)
        out=evaluate_roi_coverage(proposals,gt)
        overlap_ranks=set()
        for result,component in zip(out,gt):
            per_component.append({**result,'sample_id':item['sample_id'],'kub_size_v1':component['kub_size_v1'],'hard_tiny':bool(component['hard_tiny']),'global_empty_image':bool(component['global_empty_image']),'component_id':component['component_id']})
            if result['any_overlap'] and not (isinstance(result['best_proposal_rank'],float) and np.isnan(result['best_proposal_rank'])):
                overlap_ranks.add(int(result['best_proposal_rank']))
        overlapping_proposals+=len(overlap_ranks)
    df=pd.DataFrame(per_component); n=len(df)
    def _rec(sub): return float(sub['covered90'].mean()) if len(sub) else 0.0
    size_recall={s:_rec(df[df.kub_size_v1==s]) for s in ('TINY','SMALL','MEDIUM','LARGE')}
    return {
        'val_localization_recall':_rec(df),
        'per_size_recall90':size_recall,
        'any_overlap_recall':float(df['any_overlap'].mean()) if n else 0.0,
        'coverage50_recall':float(df['covered50'].mean()) if n else 0.0,
        'mean_coverage':float(df['coverage_fraction'].mean()) if n else 0.0,
        'zero_proposal_gt':int((~df['any_overlap']).sum()),
        'zero_proposal_tiny':int(((~df['any_overlap'])&(df.kub_size_v1=='TINY')).sum()),
        'total_gt_components':n,
        'total_proposals':total_proposals,
        'mean_proposals_per_image':float(np.mean(proposals_per_image)) if proposals_per_image else 0.0,
        'precision':float(overlapping_proposals/total_proposals) if total_proposals else 0.0,
        'background_fraction':float(1.0-overlapping_proposals/total_proposals) if total_proposals else 0.0,
    }

def pre_launch_safety_checks(args,config,h_res,size_adaptive,A_ref,sigma_min,sigma_max,selection_rule,exp_id,chk,train_ds,val_ds,model,optimizer,scheduler,criterion):
    """FAIL-CLOSED supervisor §3 reconfirmation of execution-exact configuration.

    Every assertion here MUST pass before the first optimizer step. Any failure
    raises RuntimeError and aborts launch (no partial run, no checkpoint written).
    This is a pure OPERATIONAL gate — it asserts, it does not change, the frozen
    scientific configuration.
    """
    fails=[]
    def check(name,cond):
        if not cond: fails.append(name)
    check('seed42', int(config.get('seed',42))==42 and getattr(args,'seed',42)==42)
    check('resolution512', args.resolution==512)
    check('heatmap128', h_res==128)
    check('size_adaptive_true', bool(size_adaptive) is True)
    check('A_ref13', abs(float(A_ref)-H3_A_REF)<1e-9)
    check('sigma_min035', abs(float(sigma_min)-0.35)<1e-9)
    check('sigma_max075', abs(float(sigma_max)-0.75)<1e-9)
    check('exp_id_h3', exp_id==H3_EXPERIMENT_ID)
    check('chk_namespace', str(chk).replace('\\','/').endswith(H3_CHECKPOINT_NAMESPACE.rstrip('/')))
    # Parent-identical KUBLocalizer: same factory call as Phase-13B.
    check('model_parent_localizer', type(model).__name__=='KUBLocalizer' or getattr(model,'__class__',None).__name__=='KUBLocalizer')
    check('loss_parent', type(criterion).__name__=='CenterNetFocalLoss' and getattr(criterion,'alpha',None)==2.0 and getattr(criterion,'beta',None)==4.0 and getattr(criterion,'dice_weight',0.0)==0.0)
    optimizer_group = optimizer.param_groups[0]
    optimizer_initial_lr = float(optimizer_group.get('initial_lr', optimizer_group['lr']))
    check('optim_adamw', type(optimizer).__name__=='AdamW' and abs(optimizer_initial_lr-1e-4)<1e-9 and abs(optimizer_group['weight_decay']-1e-4)<1e-9)
    check('sched_cosine100', type(scheduler).__name__=='CosineAnnealingLR' and getattr(scheduler,'T_max',None)==100)
    check('max_epochs100', int(config.get('training',{}).get('max_epochs',100))==100)
    check('patience15', int(config.get('training',{}).get('patience',15))==15)
    check('decode_frozen', H3_FROZEN_SELECTION_CONFIG==(0.10,0.20,5))
    check('nms030', config.get('proposal_policy',{}).get('fixed_decode',{}).get('nms_iou',0.30)==0.30)
    check('one_config_per_epoch', int(config.get('proposal_configurations_evaluated_per_epoch',1))==1)
    check('grid_search_disabled', config.get('proposal_policy',{}).get('grid_search_enabled',True) is False)
    check('selection_max_recall', selection_rule=='max_localization_recall')
    check('tiebreak_min_loss', config.get('checkpoint_selection',{}).get('rule','')=='max_localization_recall')
    # §2 population enforcement
    check('train770', len(train_ds)==770)
    check('val103', len(val_ds)==103)
    check('orphan_excluded', H3_ORPHAN_QUARANTINED not in set(train_ds.frame['sample_id'].astype(str)))
    check('train_all_in_manifest', set(train_ds.frame['sample_id'].astype(str)).issubset(set(pd.read_csv(H3_MANIFEST_DIR/'train.csv')['sample_id'].astype(str))))
    check('val_all_in_manifest', set(val_ds.frame['sample_id'].astype(str)).issubset(set(pd.read_csv(H3_MANIFEST_DIR/'val.csv')['sample_id'].astype(str))))
    if fails:
        raise RuntimeError('PRE_LAUNCH_SAFETY_CHECKS_FAILED: '+', '.join(fails))
    return True

def main():
 parser=argparse.ArgumentParser()
 parser.add_argument('--config',type=str,default=str(CONFIG))
 parser.add_argument('--resolution',type=int,choices=[512,768],default=512)
 parser.add_argument('--heatmap_resolution',type=int,default=None,help='Output heatmap resolution; if omitted, read from --config (H3 default 128)')
 parser.add_argument('--sigma',type=float,required=True)
 parser.add_argument('--size_adaptive_sigma',action='store_true',help='H3: size-adaptive sigma per component (default off = Phase-13B behaviour)')
 parser.add_argument('--selection_rule',type=str,default=None,choices=[None,'feasible','max_localization_recall'],help='Checkpoint selection rule (default from --config)')
 parser.add_argument('--batch',type=int,default=4)
 parser.add_argument('--accum',type=int,default=1)
 parser.add_argument('--exp_id',type=str,default='')
 parser.add_argument('--h3',action='store_true',help='H3 OPERATIONAL mode: force H3 experiment id, manifest-filtered 770/103 population, frozen decode+selection, FAIL-CLOSED pre-launch safety checks')
 parser.add_argument('--dry_run',action='store_true',help='H3 final pre-training binding dry-run: build config/flags/model/loss/optimizer/scheduler, verify decode+selection; NO training step/epoch')
 args=parser.parse_args();verify_manifests();verify_test_lock(ROOT)
 if (not args.dry_run) and (not torch.cuda.is_available()):raise RuntimeError('CUDA required')
 config=yaml.safe_load(Path(args.config).read_text());resolution,sigma=args.resolution,args.sigma
 # Resolve heatmap resolution: explicit flag wins; otherwise read from config
 # (H3 config fixes heatmap_resolution=128). Phase-13B legacy default 512.
 h_res = args.heatmap_resolution if args.heatmap_resolution is not None else int(config.get('heatmap_resolution', 512))
 # --- H3 OPERATIONAL BINDING (supervisor §1/§2/§3) -----------------------------
 # Pure OPERATIONAL enforcement. In --h3 mode we FORCE the frozen H3 experiment id,
 # manifest-filtered 770/103 population, frozen decode + selection rule, and
 # parent-identical scientific configuration. No scientific axis is altered.
 h3_mode = bool(args.h3)
 if h3_mode:
     exp_id = config.get('experiment_id', H3_EXPERIMENT_ID)
     if exp_id != H3_EXPERIMENT_ID:
         raise RuntimeError(f'H3 exp_id mismatch: config={exp_id!r} expected={H3_EXPERIMENT_ID!r}')
     size_adaptive = True
     A_ref = H3_A_REF
     sigma_min = 0.35
     sigma_max = 0.75
     selection_rule = 'max_localization_recall'
     # Frozen single decode + grid-search disabled are asserted by pre_launch.
 else:
     # Phase-13B behaviour (backward compatible)
     size_adaptive = bool(args.size_adaptive_sigma or config.get('size_adaptive_sigma', False))
     A_ref = float(config.get('A_ref', 14.0))
     sigma_min = float(config.get('sigma_min', 0.35))
     sigma_max = float(config.get('sigma_max', 0.75))
     selection_rule = args.selection_rule or (config.get('checkpoint_selection') or {}).get('rule', 'feasible')
 if selection_rule not in ('feasible', 'max_localization_recall'):
     raise ValueError(f"unknown selection_rule {selection_rule!r}")
 if (not h3_mode) and (not args.exp_id):
     # Legacy Phase-13B auto id (only when NOT in H3 mode and no explicit id)
     exp_id = args.exp_id or f'phase13b_kub_localizer_r{resolution}_h{h_res}_s{sigma}_seed42_v1'
     if size_adaptive:
         exp_id = f'{exp_id}__h3_size_adaptive_Aref{A_ref:g}'
 exp=ROOT/'experiments'/exp_id;chk=ROOT/'checkpoints'/exp_id
 exp.mkdir(parents=True,exist_ok=True);chk.mkdir(parents=True,exist_ok=True)
 set_seed(42,True);device=torch.device('cpu' if args.dry_run else 'cuda')
 # H3 manifest-filtered population (supervisor §2). Empty (None) => Phase-13B
 # FULL_FIELD-only behaviour (771/106, may include the 1 TRAIN orphan).
 train_manifest = H3_MANIFEST_DIR/'train.csv' if h3_mode else None
 val_manifest = H3_MANIFEST_DIR/'val.csv' if h3_mode else None
 train_ds=KUBLocalizerDataset(T/'kub_train_samples_sized.csv','TRAIN',resolution,sigma,heatmap_resolution=h_res,size_adaptive_sigma=size_adaptive,A_ref=A_ref,sigma_min=sigma_min,sigma_max=sigma_max,manifest_path=train_manifest)
 val_ds=KUBLocalizerDataset(T/'kub_val_samples_sized.csv','VAL',resolution,sigma,heatmap_resolution=h_res,size_adaptive_sigma=size_adaptive,A_ref=A_ref,sigma_min=sigma_min,sigma_max=sigma_max,manifest_path=val_manifest)
 if not args.dry_run:
  if h3_mode:
   assert len(train_ds)==770, f'H3 TRAIN population must be 770 canonical images, got {len(train_ds)} (orphan not excluded?)'
   assert len(val_ds)==103, f'H3 VAL population must be 103 canonical images, got {len(val_ds)}'
   assert H3_ORPHAN_QUARANTINED not in set(train_ds.frame['sample_id'].astype(str)), 'H3 TRAIN orphan must be excluded'
  else:
   assert len(train_ds)==771 and len(val_ds)==106
 if not args.dry_run:
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
 if args.dry_run:
  import hashlib as _hl
  def _sha(p): return _hl.sha256(Path(p).read_bytes()).hexdigest()
  d_thr,d_margin,d_topk=H3_FROZEN_SELECTION_CONFIG
  decode_ok=(d_thr in THRESHOLDS) and (d_margin in MARGINS) and (d_topk in TOPKS)
  sel_tuple=build_h3_supply_selection_tuple(0.9,0.1)
  sel_names=list(H3_SUPPLY_TERM_NAMES)
  loss_parent=(type(criterion).__name__=='CenterNetFocalLoss' and getattr(criterion,'alpha',None)==2.0 and getattr(criterion,'beta',None)==4.0)
  opt_ok=(type(optimizer).__name__=='AdamW' and abs(optimizer.param_groups[0]['lr']-1e-4)<1e-9 and abs(optimizer.param_groups[0]['weight_decay']-1e-4)<1e-9)
  sched_ok=(type(scheduler).__name__=='CosineAnnealingLR' and getattr(scheduler,'T_max',None)==100)
  man_dir=ROOT/'manifests'/'phase4_v3'
  train_man=pd.read_csv(man_dir/'train.csv');val_man=pd.read_csv(man_dir/'val.csv')
  train_man_ids=set(train_man['sample_id'].astype(str));val_man_ids=set(val_man['sample_id'].astype(str))
  sized_train_ff=set(train_ds.frame['sample_id'].astype(str));sized_val_ff=set(val_ds.frame['sample_id'].astype(str))
  canon_train=sized_train_ff & train_man_ids;canon_val=sized_val_ff & val_man_ids
  orphan_train=sorted(sized_train_ff - train_man_ids);orphan_val=sorted(sized_val_ff - val_man_ids)
  if h3_mode:
      pop_class='H3_CANONICAL_POPULATION_ENFORCED';pop_note='H3 manifest filter applied at dataset construction: TRAIN/VAL restricted to canonical v3 manifest membership (770/103), orphan excluded.'
  else:
      pop_class='PRE_EXECUTION_CALIBRATION_POPULATION_MISMATCH';pop_note='Sized-table TRAIN FULL_FIELD (771) includes 1 orphan absent from the v3 manifest; canonical H3 population is the manifest-filtered 770. Use --h3 to enforce.'
  report={
   'dry_run':True,'h3_mode':h3_mode,'training_steps_executed':0,'config_resolves':True,'config_path':args.config,
   'flags':{'size_adaptive_sigma':size_adaptive,'A_ref':A_ref,'sigma_min':sigma_min,'sigma_max':sigma_max,'selection_rule':selection_rule,'h3_experiment_id':exp_id if h3_mode else None},
   'decode_config':{'threshold':d_thr,'margin':d_margin,'top_k':d_topk,'nms_iou':0.30,'in_grid':decode_ok,'grid_search_disabled':True},
   'proposal_configurations_evaluated_per_epoch':int(config.get('proposal_configurations_evaluated_per_epoch',1)),
   'checkpoint_selection':{'rule':selection_rule,'tuple':list(sel_tuple),'term_names':sel_names,'is_2_term':(len(sel_tuple)==2 and sel_names==['val_localization_recall','negative_val_loss'])},
   'loss':{'type':type(criterion).__name__,'alpha':getattr(criterion,'alpha',None),'beta':getattr(criterion,'beta',None),'dice_weight':getattr(criterion,'dice_weight',None),'parent_identical':loss_parent},
   'optimizer':{'type':type(optimizer).__name__,'lr':optimizer.param_groups[0]['lr'],'weight_decay':optimizer.param_groups[0]['weight_decay'],'parent_identical':opt_ok},
   'scheduler':{'type':type(scheduler).__name__,'T_max':getattr(scheduler,'T_max',None),'parent_identical':sched_ok},
   'model_built':True,'model_param_count':int(sum(p.numel() for p in model.parameters())),
   'manifests':{'train_csv_sha256':_sha(man_dir/'train.csv'),'val_csv_sha256':_sha(man_dir/'val.csv'),'train_manifest_rows':int(len(train_man)),'val_manifest_rows':int(len(val_man))},
   'population':{'sized_table_train_full_field':int(len(sized_train_ff)),'sized_table_val_full_field':int(len(sized_val_ff)),'canonical_train_full_field':int(len(canon_train)),'canonical_val_full_field':int(len(canon_val)),'orphan_train_quarantined':orphan_train,'orphan_val_quarantined':orphan_val,'classification':pop_class,'note':pop_note},
   'exact_training_command':f'python scripts/training/train_phase13b_localizer.py --h3 --config {args.config} --sigma 0.75' + (' --dry_run' if args.dry_run else ''),
  }
  print(json.dumps(report,indent=2));return
 runtime=json.loads(json.dumps(config))
 runtime['candidate']={'resolution':resolution,'heatmap_resolution':h_res,'sigma':sigma,'physical_batch':batch,'accumulation':acc,'effective_batch':batch*acc,'selection_version':('h3_supply_max_localization_recall_v1' if selection_rule=='max_localization_recall' else 'phase13b_feasible_selection_v1'),'size_adaptive_sigma':size_adaptive,'A_ref':A_ref,'sigma_min':sigma_min,'sigma_max':sigma_max}
 metadata=json.loads((ROOT/'manifests/manifest_metadata.json').read_text())
 if latest.exists():
  state=load_training_checkpoint(latest,model,optimizer,scheduler,scaler,True,device);start_epoch=state['epoch']+1;history=state['training_history'];best_score=tuple(state['best_validation_score']) if state.get('best_validation_score') else None;early=state.get('early_stopping_state') or {};bad_epochs=int(early.get('bad_epochs',0));global_step=state['global_step'];generator_state=(state.get('loader_generator_states') or {}).get('train')
  if (chk/'best.pt').exists():
   b_st=torch.load(chk/'best.pt',map_location='cpu',weights_only=False)
   if b_st.get('best_validation_score'):
    best_score=tuple(b_st['best_validation_score'])
    best_ep=b_st.get('epoch', start_epoch-1)
    bad_epochs=max(0, (start_epoch - 1) - best_ep)
 # §5 OPERATIONAL resume safety: never resume from a Phase-13B / Phase-14 / other
 # experiment's checkpoint. The isolated H3 namespace already prevents cross-dir
 # contamination; this guard additionally verifies the persisted experiment_id.
 if h3_mode and latest.exists():
  if state.get('experiment_id') != H3_EXPERIMENT_ID:
   raise RuntimeError(f"H3 resume guard: checkpoint experiment_id={state.get('experiment_id')!r} != {H3_EXPERIMENT_ID!r}; refusing to resume from a non-H3 checkpoint (supervisor §5)")
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

 # §3 + §6: FAIL-CLOSED pre-launch safety checks, then write the launch binding
 # BEFORE epoch 1 (supervisor §3/§6). The launch binding records the frozen
 # contract and sets status H3_TRAINING_PROSPECTIVELY_AUTHORIZED__READY_TO_LAUNCH.
 if h3_mode:
  pre_launch_safety_checks(args,config,h_res,size_adaptive,A_ref,sigma_min,sigma_max,selection_rule,exp_id,chk,train_ds,val_ds,model,optimizer,scheduler,criterion)
  import hashlib as _hl2
  def _sha2(p): return _hl2.sha256(Path(p).read_bytes()).hexdigest()
  _d_thr,_d_margin,_d_topk=H3_FROZEN_SELECTION_CONFIG
  AUDITS=ROOT/'reports'/'audits'
  launch_binding={
   'supervisor_ruling':'H3_FINAL_LAUNCH_SAFETY_CHECK_PLUS_PROSPECTIVE_TRAINING_AUTHORIZATION',
   'experiment_id':H3_EXPERIMENT_ID,
   'checkpoint_namespace':H3_CHECKPOINT_NAMESPACE,
   'classification':'OPERATIONAL_OUTPUT_ISOLATION__NO_SCIENTIFIC_AXIS_CHANGE',
   'scientific_axis':'A_PROPOSAL_SUPPLY_RECALL_LIMITATION / A_TARGET_SUPPORT_REDESIGN (single authorized axis)',
   'output_paths':{'experiments':str(exp),'checkpoints':str(chk),'best_checkpoint':str(chk/'best.pt'),'latest_checkpoint':str(chk/'latest.pt'),'history':str(exp/'history.csv')},
   'final_shas':{
     'trainer':_sha2(Path(__file__)),
     'dataset_module':_sha2(ROOT/'src/data/kub_localizer_dataset.py'),
     'selection_module':_sha2(ROOT/'src/training/clean_v3_selection.py'),
     'checkpointing_module':_sha2(ROOT/'src/utils/checkpointing.py'),
     'config':_sha2(Path(args.config)),
     'train_manifest':_sha2(H3_MANIFEST_DIR/'train.csv'),
     'val_manifest':_sha2(H3_MANIFEST_DIR/'val.csv'),
   },
   'train_population':{'images':len(train_ds),'canonical_components':1161,'orphan_excluded':H3_ORPHAN_QUARANTINED not in set(train_ds.frame['sample_id'].astype(str))},
   'val_population':{'images':len(val_ds),'canonical_components':152,'tiny_components':72},
   'fixed_decode':{'threshold':_d_thr,'margin':_d_margin,'top_k':_d_topk,'nms_iou':0.30},
   'selection_tuple':{'terms':list(H3_SUPPLY_TERM_NAMES),'rule':'MAX val_localization_recall then MIN val_loss','tuple':list(build_h3_supply_selection_tuple(0.9,0.1))},
   'scientific_config':{'seed':42,'resolution':resolution,'heatmap_resolution':h_res,'size_adaptive_sigma':True,'A_ref':A_ref,'sigma_min':sigma_min,'sigma_max':sigma_max,'loss':'CenterNetFocalLoss(alpha=2.0,beta=4.0,dice_weight=0.0)','optimizer':'AdamW(lr=1e-4,wd=1e-4)','scheduler':'CosineAnnealingLR(T_max=100)','max_epochs':100,'patience':15,'proposal_configurations_evaluated_per_epoch':1,'grid_search_enabled':False},
   'test_reads':0,
   'exact_training_command':f'python scripts/training/train_phase13b_localizer.py --h3 --config {args.config} --sigma 0.75',
   'status':'H3_TRAINING_PROSPECTIVELY_AUTHORIZED__READY_TO_LAUNCH',
   'written_before_epoch_1':True,
   'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  }
  AUDITS.mkdir(parents=True,exist_ok=True)
  if latest.exists() and (AUDITS/'h3_training_launch_binding.json').exists():
   print(f"[H3 LAUNCH BINDING] preserved for same-run resume -> {AUDITS/'h3_training_launch_binding.json'}")
  else:
   (AUDITS/'h3_training_launch_binding.json').write_text(json.dumps(launch_binding,indent=2))
   (exp/'h3_training_launch_binding.json').write_text(json.dumps(launch_binding,indent=2))
  print(f"[H3 LAUNCH BINDING] written — status {launch_binding['status']} -> {AUDITS/'h3_training_launch_binding.json'}")

 for epoch in range(start_epoch,101):
  model.train();optimizer.zero_grad(set_to_none=True);losses=[];started=time.perf_counter();torch.cuda.reset_peak_memory_stats()
  from tqdm import tqdm
  train_pbar = tqdm(train_loader, desc=f"Epoch {epoch:03d}/100 [Train]", dynamic_ncols=True)
  for index,b in enumerate(train_pbar):
   with torch.amp.autocast('cuda'):loss=criterion(model(b['image'].to(device)),b['heatmap'].to(device))/acc
   scaler.scale(loss).backward();scaler.step(optimizer);scaler.update();optimizer.zero_grad(set_to_none=True);losses.append(loss.item()*acc);global_step+=1
   train_pbar.set_postfix({'loss': f"{np.mean(losses):.4f}"})
  
  val_loss,search,cache,heatmap_diag=evaluate(model,val_loader,criterion,device,resolution,component_table)
  if selection_rule == 'max_localization_recall':
    # Frozen H3 supply-axis rule: MAXIMISE VAL_LOCALIZATION_RECALL at the fixed
    # decode (thr=0.10, margin=0.20, top_k=5; nms=0.30 is hardcoded in evaluate),
    # tiebreak MINIMISE VAL_LOSS. VAL_LOCALIZATION_RECALL == overall_recall90 at
    # that exact configuration in the search grid.
    thr, margin, top_k = H3_FROZEN_SELECTION_CONFIG
    frow = search[(search.threshold == thr) & (search.margin == margin) & (search.top_k == top_k)]
    feasible_configs = frow  # the single frozen config evaluated per epoch (H3)
    if len(frow):
      loc_recall = float(frow['overall_recall90'].iloc[0])
      best_cfg = frow.iloc[0]
      outcome = select_h3_supply_epoch(loc_recall, val_loss, best_score=best_score,
                                       best_epoch=None, bad_epochs=bad_epochs,
                                       epoch=epoch, patience=15)
      score = outcome.score; improved = outcome.is_new_best; bad_epochs = outcome.bad_epochs
      if improved: best_score = outcome.best_score
    else:
      best_cfg = search.sort_values(['mean_roi_area_fraction','mean_proposals_per_image'],ascending=[True,True]).iloc[0]
      score=None; improved=False; bad_epochs+=1
  else:
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
  # §4 H3 supply-axis checkpoint-selection execution contract: persist the frozen
  # decode, per-size VAL recall, zero-proposal GT/TINY counts, and the 2-term
  # selection tuple. best.pt is updated ONLY by (val_localization_recall, -val_loss).
  h3_metrics = None
  if selection_rule == 'max_localization_recall':
    _t,_m,_k = H3_FROZEN_SELECTION_CONFIG
    h3_metrics = h3_supply_axis_metrics(cache, component_table, _t, _m, _k, 0.30)
  scheduler.step()
  epoch_seconds=time.perf_counter()-started
  row={'epoch':epoch,'train_loss':float(np.mean(losses)),'val_loss':val_loss,'val_hard_tiny_recovered90':best_cfg.hard_tiny_recovered90,'val_global_empty_images_covered90':best_cfg.global_empty_images_covered90,'val_tiny_recall90':best_cfg.tiny_recall90,'val_overall_recall90':best_cfg.overall_recall90,'learning_rate':optimizer.param_groups[0]['lr'],'epoch_seconds':epoch_seconds,'peak_gpu_allocated':torch.cuda.max_memory_allocated(),'peak_gpu_reserved':torch.cuda.max_memory_reserved(),'feasible_config_count':len(feasible_configs),'localization_status':'FEASIBLE' if len(feasible_configs)>0 else 'INFEASIBLE','mean_roi_area_fraction':best_cfg.mean_roi_area_fraction,'mean_proposals_per_image':best_cfg.mean_proposals_per_image,'mean_max_heatmap':heatmap_diag['mean_max_prob'],'median_max_heatmap':heatmap_diag['median_max_prob']}
  if h3_metrics is not None:
    row.update({
      'fixed_decode':{'threshold':_t,'margin':_m,'top_k':_k,'nms_iou':0.30},
      'val_localization_recall':h3_metrics['val_localization_recall'],
      'per_size_recall90':h3_metrics['per_size_recall90'],
      'any_overlap_recall':h3_metrics['any_overlap_recall'],
      'coverage50_recall':h3_metrics['coverage50_recall'],
      'mean_coverage':h3_metrics['mean_coverage'],
      'zero_proposal_gt':h3_metrics['zero_proposal_gt'],
      'zero_proposal_tiny':h3_metrics['zero_proposal_tiny'],
      'total_gt_components':h3_metrics['total_gt_components'],
      'total_proposals':h3_metrics['total_proposals'],
      'precision':h3_metrics['precision'],
      'background_fraction':h3_metrics['background_fraction'],
      'selection_tuple':list(build_h3_supply_selection_tuple(h3_metrics['val_localization_recall'], val_loss)),
      'selection_term_names':list(H3_SUPPLY_TERM_NAMES),
    })
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
