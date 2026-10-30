"""H3 supply-axis evaluation of the selected localizer (supervisor §9).

Loads the H3-selected best.pt checkpoint and evaluates it on the frozen VAL
population (103 canonical FULL_FIELD images / 152 GT components, 72 TINY) under
the FIXED decode (threshold=0.10, margin=0.20, top_k=5, nms=0.30). Reports the
supply-axis metrics and applies the primary acceptance criteria:
    zero-proposal TINY <= 20/72
    zero-proposal GT   <= 35/152
No Phase-14 refiner is involved. This is a read-only evaluation; it does NOT
modify the selected checkpoint.
"""
import sys,json
from pathlib import Path
import pandas as pd
import torch,yaml
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'scripts'/'training'))
import train_phase13b_localizer as TRAIN
from src.losses.localization import CenterNetFocalLoss
from src.utils.checkpointing import load_training_checkpoint

CONFIG=ROOT/'configs'/'kub'/'phase13b_localizer_h3_size_adaptive_sigma.yaml'
EXP_ID=TRAIN.H3_EXPERIMENT_ID
CHK=ROOT/'checkpoints'/EXP_ID
AUDITS=ROOT/'reports'/'audits'

# Primary-criteria denominators (canonical VAL, verified)
VAL_TINY_TOTAL=72
VAL_GT_TOTAL=152
ZERO_PROPOSAL_TINY_LIMIT=20
ZERO_PROPOSAL_GT_LIMIT=35

def build_component_table():
    T=TRAIN.T
    phase13_components=pd.read_csv(T/'phase13_predicted_roi_per_component.csv')
    phase13_images=pd.read_csv(T/'phase13_predicted_roi_per_image.csv')
    hard_keys=set(zip(phase13_components[(phase13_components.kub_size_v1=='TINY')&~phase13_components.global_detected].sample_id,
                      phase13_components[(phase13_components.kub_size_v1=='TINY')&~phase13_components.global_detected].component_id))
    empty_ids=set(phase13_images[phase13_images.global_empty_prediction].sample_id)
    component_table=phase13_components[['sample_id','component_id','min_y','max_y','min_x','max_x','kub_size_v1','global_detected']].copy()
    component_table['hard_tiny']=[(sid,cid) in hard_keys for sid,cid in zip(component_table.sample_id,component_table.component_id)]
    component_table['global_empty_image']=component_table.sample_id.isin(empty_ids)
    assert component_table.hard_tiny.sum()==16 and len(empty_ids)==7
    return component_table

def main():
    config=yaml.safe_load(Path(CONFIG).read_text())
    resolution=int(config['resolution']); h_res=int(config['heatmap_resolution'])
    A_ref=float(config['A_ref']); sigma_min=float(config['sigma_min']); sigma_max=float(config['sigma_max'])
    device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"[H3 EVAL] device={device} resolution={resolution} h_res={h_res}")

    # Frozen VAL population (H3 manifest filter)
    val_ds=TRAIN.KUBLocalizerDataset(TRAIN.T/'kub_val_samples_sized.csv','VAL',resolution,0.75,
                                     heatmap_resolution=h_res,size_adaptive_sigma=True,A_ref=A_ref,
                                     sigma_min=sigma_min,sigma_max=sigma_max,
                                     manifest_path=TRAIN.H3_MANIFEST_DIR/'val.csv')
    assert len(val_ds)==103, f"VAL population must be 103, got {len(val_ds)}"
    component_table=build_component_table()
    val_loader=DataLoader(val_ds,batch_size=4,shuffle=False,num_workers=0,pin_memory=True)

    model=TRAIN.create_model('kub_localizer',in_channels=1,out_channels=1,base_channels=16,heatmap_resolution=h_res).to(device)
    criterion=CenterNetFocalLoss(alpha=2.0,beta=4.0)
    best_pt=CHK/'best.pt'
    state=load_training_checkpoint(best_pt,model,optimizer=None,scheduler=None,scaler=None,restore_rng=False,map_location=str(device))
    assert state.get('experiment_id')==EXP_ID, f"best.pt experiment_id {state.get('experiment_id')} != {EXP_ID}"
    model.eval()

    val_loss,search,cache,heatmap_diag=TRAIN.evaluate(model,val_loader,criterion,device,resolution,component_table)
    thr,margin,top_k=TRAIN.H3_FROZEN_SELECTION_CONFIG
    m=TRAIN.h3_supply_axis_metrics(cache,component_table,thr,margin,top_k,0.30)

    zp_tiny=m['zero_proposal_tiny']; zp_gt=m['zero_proposal_gt']
    pass_tiny = zp_tiny <= ZERO_PROPOSAL_TINY_LIMIT
    pass_gt   = zp_gt   <= ZERO_PROPOSAL_GT_LIMIT
    primary_pass = pass_tiny and pass_gt

    report={
        'supervisor_ruling':'H3_FINAL_LAUNCH_SAFETY_CHECK_PLUS_PROSPECTIVE_TRAINING_AUTHORIZATION__SECTION_9',
        'experiment_id':EXP_ID,
        'evaluated_checkpoint':str(best_pt),
        'checkpoint_epoch':int(state.get('epoch',-1)),
        'checkpoint_best_validation_score':[float(x) for x in state.get('best_validation_score',[])] if state.get('best_validation_score') else None,
        'fixed_decode':{'threshold':thr,'margin':margin,'top_k':top_k,'nms_iou':0.30},
        'val_population':{'images':len(val_ds),'gt_components':m['total_gt_components'],'tiny_components':VAL_TINY_TOTAL},
        'supply_axis_metrics':{
            'val_localization_recall':m['val_localization_recall'],
            'per_size_recall90':m['per_size_recall90'],
            'any_overlap_recall':m['any_overlap_recall'],
            'coverage50_recall':m['coverage50_recall'],
            'mean_coverage':m['mean_coverage'],
            'zero_proposal_gt':zp_gt,
            'zero_proposal_tiny':zp_tiny,
            'total_proposals':m['total_proposals'],
            'mean_proposals_per_image':m['mean_proposals_per_image'],
            'precision':m['precision'],
            'background_fraction':m['background_fraction'],
        },
        'primary_criteria':{
            'zero_proposal_tiny':{'observed':zp_tiny,'limit':ZERO_PROPOSAL_TINY_LIMIT,'denominator':VAL_TINY_TOTAL,'pass':bool(pass_tiny)},
            'zero_proposal_gt':{'observed':zp_gt,'limit':ZERO_PROPOSAL_GT_LIMIT,'denominator':VAL_GT_TOTAL,'pass':bool(pass_gt)},
            'primary_pass':bool(primary_pass),
        },
        'val_loss':float(val_loss),
        'note':'Supply-axis evaluation only. No Phase-14 refiner invoked (supervisor §9).',
    }
    AUDITS.mkdir(parents=True,exist_ok=True)
    out_path=AUDITS/'h3_supply_axis_evaluation.json'
    out_path.write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    print(f"[H3 EVAL] PRIMARY CRITERIA: zero_proposal_tiny {zp_tiny}/72 (<=20: {pass_tiny}); zero_proposal_gt {zp_gt}/152 (<=35: {pass_gt}); PRIMARY_PASS={primary_pass}")
    return primary_pass

if __name__=='__main__':
    ok=main()
    sys.exit(0 if ok else 2)
