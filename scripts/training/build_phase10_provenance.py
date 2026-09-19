"""Write final Phase-10 provenance from retained artifacts."""
import hashlib,json,pathlib,sys
import pandas as pd
import torch
ROOT=pathlib.Path(__file__).resolve().parents[2]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
experiments=['phase10_kub_attention_unet_seed42_512','phase10_kub_unetpp_seed42_512','phase10_kub_deeplabv3plus_seed42_512']
models={}; hashes={}
for exp in experiments:
 s=json.loads((ROOT/'experiments'/exp/'summary.json').read_text()); ck=ROOT/'checkpoints'/exp
 models[exp]={'model':s['display_name'],'architecture':s['architecture'],'parameters':s['parameter_count'],'epochs':s['epochs_completed'],'best_epoch':s['best_epoch'],'physical_batch':s['physical_batch'],'effective_batch':s['effective_batch'],'initialization':s['initialization'],'best_val_dice_selection':s['best_val_dice_checkpoint_selection'],'final_macro_dice':s['validation_metrics']['Macro_Dice']}
 hashes[exp]={'best_pt':sha(ck/'best.pt'),'latest_pt':sha(ck/'latest.pt'),'history_csv':sha(ROOT/'experiments'/exp/'history.csv'),'summary_json':sha(ROOT/'experiments'/exp/'summary.json')}
 for f in (ROOT/'reports/tables').glob('phase10_'+s['model']+'_*'):
  if f.is_file(): hashes[exp][f.name]=sha(f)
manifest=json.loads((ROOT/'manifests/manifest_metadata.json').read_text())['hashes']; notebook=ROOT/'notebooks/08_kub_baseline_comparison.ipynb'
audit={'phase':'10 - KUB Fair Baseline Model Comparison','status':'PASS','experiment_ids':experiments,'models':models,'frozen_protocol':{'seed':42,'resolution':512,'optimizer':'AdamW','learning_rate':1e-4,'weight_decay':1e-4,'scheduler':'CosineAnnealingLR','loss':'0.5 BCEWithLogitsLoss + 0.5 DiceLoss','threshold':0.5,'max_epochs':100,'patience':15,'selection_metric':'true per-image VAL macro Dice','pretrained_weights':False},'manifest_version':'phase4_v2','manifest_hashes':manifest,'artifact_hashes':hashes,'comparison_table_sha256':sha(ROOT/'reports/tables/phase10_kub_model_comparison.csv'),'fairness_table_sha256':sha(ROOT/'reports/tables/phase10_kub_fairness_table.csv'),'notebook_sha256':sha(notebook),'source_commit':'UNAVAILABLE_NO_COMMIT','pytorch_version':torch.__version__,'cuda_version':torch.version.cuda,'gpu':torch.cuda.get_device_name(0),'test_accessed':False,'test_metrics':'NONE','external_accessed':False,'experiment_a_modified':False,'phase_11_executed':False,'statistics':'single-seed descriptive comparisons only; no significance claims'}
out=ROOT/'reports/audits/phase10_kub_baseline_comparison.json'; out.write_text(json.dumps(audit,indent=2),encoding='utf-8')
comparison=pd.read_csv(ROOT/'reports/tables/phase10_kub_model_comparison.csv'); headers=list(comparison.columns); lines=['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']; lines += ['| '+' | '.join(map(str,row))+' |' for row in comparison.itertuples(index=False,name=None)]; md='# Phase 10 — KUB Fair Baseline Model Comparison\n\n**Status: PASS**\n\n'+'\n'.join(lines)+'\n\nSingle-seed descriptive comparison only; no formal significance or causality claims. `kub_size_v1` is original-space; object comparison is 512×512 evaluation-space. TEST metrics: NONE. External data: not accessed. Experiment A: untouched. Phase 11: not executed.\n'; (ROOT/'reports/audits/phase10_kub_baseline_comparison.md').write_text(md,encoding='utf-8')
print(out)
