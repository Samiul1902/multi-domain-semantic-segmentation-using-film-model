"""Phase 8 infrastructure smoke audit. No epoch or scientific training."""
import gc, hashlib, json, sys
from pathlib import Path
import pandas as pd
import torch, yaml

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.data.kub_dataset import KUBDataset, TestAccessError
from src.data.loaders import create_loader
from src.data.transforms import SegmentationTransform
from src.losses.segmentation import BCEDiceLoss
from src.metrics.segmentation import binary_metrics
from src.models.factory import create_model
from src.utils.checkpointing import save_training_checkpoint, load_training_checkpoint
from src.utils.experiment import register_experiment
from src.utils.manifest_guard import verify_manifests
from src.utils.reproducibility import set_seed
from src.utils.test_lock import verify_test_lock
from src.visualization.training import plot_training_history

verify_manifests(); test_lock=verify_test_lock(ROOT)
config=yaml.safe_load((ROOT/"configs/kub/unet_baseline.yaml").read_text(encoding="utf-8"))
if not torch.cuda.is_available(): raise RuntimeError("CUDA unavailable; CPU smoke prohibited")
device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
set_seed(42)
train=KUBDataset(ROOT/"manifests/train.csv","TRAIN",SegmentationTransform(512,True),ROOT/"reports/tables/kub_train_samples_sized.csv")
val=KUBDataset(ROOT/"manifests/val.csv","VAL",SegmentationTransform(512,False),ROOT/"reports/tables/kub_val_samples_sized.csv")
assert len(train)==1979 and len(val)==283
try: KUBDataset(ROOT/"manifests/test.csv","TEST"); raise AssertionError("TEST was not blocked")
except TestAccessError: pass

experiment_id="phase8_unet_infrastructure_smoke_seed42"

attempts=[]; feasible=None
for batch_size in (4,2,1):
    gc.collect(); torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats()
    try:
        set_seed(42); model=create_model("unet",in_channels=1,out_channels=1,base_channels=32).to(device)
        optimizer=torch.optim.AdamW(model.parameters(),lr=1e-4,weight_decay=1e-4)
        scheduler=torch.optim.lr_scheduler.CosineAnnealingLR(optimizer,T_max=100)
        scaler=torch.amp.GradScaler("cuda",enabled=True); criterion=BCEDiceLoss()
        loader=create_loader(train,batch_size,True,42,0,True,False); batch=next(iter(loader))
        images=batch["image"].to(device); masks=batch["mask"].to(device); optimizer.zero_grad(set_to_none=True)
        with torch.amp.autocast("cuda",enabled=True): logits=model(images); loss=criterion(logits,masks)
        scaler.scale(loss).backward(); scaler.step(optimizer); scaler.update(); torch.cuda.synchronize()
        feasible=batch_size; smoke_loss=float(loss.item()); peak_allocated=int(torch.cuda.max_memory_allocated()); peak_reserved=int(torch.cuda.max_memory_reserved())
        attempts.append({"batch_size":batch_size,"status":"PASS","peak_allocated_bytes":peak_allocated,"peak_reserved_bytes":peak_reserved}); break
    except torch.OutOfMemoryError as error:
        attempts.append({"batch_size":batch_size,"status":"OOM","error":str(error)[:300]})
        del model,optimizer,scheduler,scaler; gc.collect(); torch.cuda.empty_cache()
if feasible is None: raise RuntimeError("No feasible CUDA batch size in 4->2->1")

# One deterministic VAL batch: plumbing only.
model.eval(); val_loader=create_loader(val,feasible,False,42,0,True,False); val_batch=next(iter(val_loader))
with torch.no_grad(),torch.amp.autocast("cuda",enabled=True):
    val_logits=model(val_batch["image"].to(device)); val_loss=criterion(val_logits,val_batch["mask"].to(device))
val_metrics={k:float(v.mean()) for k,v in binary_metrics(val_logits,val_batch["mask"].to(device),.5).items()}; val_metrics["loss"]=float(val_loss)
# Checkpoint save/load round-trip
experiment_id="phase8_unet_infrastructure_smoke_seed42"; checkpoint_dir=ROOT/"checkpoints"/experiment_id; checkpoint_dir.mkdir(parents=True,exist_ok=True)
manifest_meta=json.loads((ROOT/"manifests/manifest_metadata.json").read_text()); checkpoint=checkpoint_dir/"latest.pt"
fixed_input=torch.randn(1,1,64,64,device=device); model.eval()
with torch.no_grad(): before=model(fixed_input).cpu()
save_training_checkpoint(checkpoint,model,optimizer,scheduler,scaler,0,1,val_metrics["dice"],config,42,
                         [{"epoch":0,"status":"SMOKE_ONLY"}],"phase4_v2",manifest_meta["hashes"],
                         experiment_id,"unet",512,.5,None)
for parameter in model.parameters(): parameter.data.zero_()
state=load_training_checkpoint(checkpoint,model,optimizer,scheduler,scaler,False,device)
with torch.no_grad(): after=model(fixed_input).cpu()
checkpoint_equal=bool(torch.equal(before,after)); assert checkpoint_equal



# Determinism checks.
set_seed(42); init1=create_model("unet",in_channels=1,out_channels=1,base_channels=8)
h1=hashlib.sha256(b"".join(t.numpy().tobytes() for t in init1.state_dict().values())).hexdigest()
set_seed(42); init2=create_model("unet",in_channels=1,out_channels=1,base_channels=8)
h2=hashlib.sha256(b"".join(t.numpy().tobytes() for t in init2.state_dict().values())).hexdigest()
val_a=val[0]; val_b=val[0]; assert torch.equal(val_a["image"],val_b["image"]) and h1==h2


# Diagnostic assets and registries.
import numpy as np

import matplotlib.pyplot as plt
from PIL import Image
qual_dir=ROOT/"reports/qualitative/kub_baseline_infrastructure"; qual_dir.mkdir(parents=True,exist_ok=True)
metadata=pd.read_csv(ROOT/"reports/tables/kub_val_samples_sized.csv"); chosen=[]
for category in ("Kidney_Stone","Bladder_Stone","Ureteric_Stone"):
    for view in ("FULL_FIELD","ROI_CROP"):
        subset=metadata[(metadata.category==category)&(metadata.view_type==view)].sort_values("sample_id")
        if len(subset): chosen.append(subset.iloc[0])
fig,axes=plt.subplots(len(chosen),4,figsize=(12,3*len(chosen)),squeeze=False)
for row_axes,row in zip(axes,chosen):
    raw_image=Image.open(row.image_path).convert("L"); raw_mask=Image.open(row.mask_path).convert("L")
    image_t,mask_t,_=SegmentationTransform(512,False)(raw_image,raw_mask)
    for ax,array,title in zip(row_axes,[raw_image,np.asarray(raw_mask)>0,image_t.squeeze().numpy(),mask_t.squeeze().numpy()],
                              ["Original image","Binary mask","Resize + pad image","Resize + pad mask"]):
        ax.imshow(array,cmap="gray"); ax.set_title(f"{title}\n{row.category} | {row.view_type}"); ax.axis("off")
fig.tight_layout(); qual_path=qual_dir/"kub_preprocessing_diagnostics.png"; fig.savefig(qual_path,dpi=320,bbox_inches="tight"); plt.close(fig)

plot_paths=plot_training_history([{"epoch":0,"train_loss":smoke_loss,"val_loss":val_metrics["loss"],"val_dice":val_metrics["dice"],"learning_rate":1e-4}],ROOT/"reports/figures/kub_baseline_infrastructure","smoke_training_plumbing",True)
record={"experiment_id":experiment_id,"dataset":"KUB","split":"TRAIN+VAL_SMOKE_ONLY","model":"unet","architecture":"standard_unet_4_stage","seed":42,"image_size":512,"batch_size":feasible,"effective_batch_size":max(4,feasible),"optimizer":"AdamW","learning_rate":1e-4,"weight_decay":1e-4,"scheduler":"CosineAnnealingLR","epochs":0,"loss":"0.5_BCE+0.5_Dice","loss_weights":"0.5/0.5","augmentation":"baseline_conservative","threshold":.5,"roi_settings":"none","fusion":"none","best_epoch":"NOT_APPLICABLE","validation_metrics":"SMOKE_ONLY_NOT_SCIENTIFIC","checkpoint":str(checkpoint),"status":"SMOKE_TEST","phase":8,"manifest_version":"phase4_v2","notes":"One TRAIN batch and one VAL batch; no epoch, selection, or performance claim"}
register_experiment(record,ROOT)

result={"status":"PASS","phase":"8 - KUB Baseline Infrastructure","experiment_id":experiment_id,"manifest_version":"phase4_v2","test_lock_valid":True,"train_count":len(train),"val_count":len(val),"test_accessed":False,"device":str(device),"cuda_available":True,"gpu":torch.cuda.get_device_name(0),"gpu_total_memory_bytes":int(torch.cuda.get_device_properties(0).total_memory),"pytorch":torch.__version__,"cuda_runtime":torch.version.cuda,"amp":True,"parameter_count":sum(p.numel() for p in model.parameters()),"attempts":attempts,"feasible_batch_size":feasible,"effective_batch_size":max(4,feasible),"peak_allocated_bytes":peak_allocated,"peak_reserved_bytes":peak_reserved,"forward_shape":list(logits.shape),"smoke_loss":smoke_loss,"val_smoke_metrics":val_metrics,"checkpoint":str(checkpoint),"checkpoint_output_exact":checkpoint_equal,"initialized_model_hash_run1":h1,"initialized_model_hash_run2":h2,"deterministic_init":h1==h2,"deterministic_val":True,"qualitative_asset":str(qual_path),"plot_assets":[str(p) for p in plot_paths],"scientific_result":False,"label":"SMOKE_ONLY — NOT A SCIENTIFIC RESULT"}
(ROOT/"reports/audits/kub_baseline_infrastructure.json").write_text(json.dumps(result,indent=2),encoding="utf-8")

md_lines=["# Phase 8 — KUB Baseline Infrastructure Report","","## CUDA & Hardware",f"- CUDA Available: True",f"- GPU: {result['gpu']}",f"- PyTorch: {result['pytorch']}",f"- CUDA Runtime: {result['cuda_runtime']}","","## Infrastructure Smoke Pass",f"- Feasible Batch Size: {feasible}",f"- Peak Allocated VRAM: {peak_allocated} bytes",f"- Checkpoint Round-trip Output Equivalence: True",f"- Test Access Guard: PASS (Blocked)","","## Safeguards",f"- Test-lock artifact: `reports/audits/test_lock.json`",f"- Manifest guard: PASS",f"- Substantive training performed: NO"]
(ROOT/"reports/audits/kub_baseline_infrastructure.md").write_text("\n".join(md_lines)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))

val_metrics={k:float(v.mean()) for k,v in binary_metrics(val_logits,val_batch["mask"].to(device),.5).items()}; val_metrics["loss"]=float(val_loss)

# Full-state checkpoint round trip.
experiment_id="phase8_unet_infrastructure_smoke_seed42"; checkpoint_dir=ROOT/"checkpoints"/experiment_id; checkpoint_dir.mkdir(parents=True,exist_ok=True)
manifest_meta=json.loads((ROOT/"manifests/manifest_metadata.json").read_text()); checkpoint=checkpoint_dir/"latest.pt"
fixed_input=torch.randn(1,1,64,64,device=device); model.eval()
with torch.no_grad(): before=model(fixed_input).cpu()
save_training_checkpoint(checkpoint,model,optimizer,scheduler,scaler,0,1,val_metrics["dice"],config,42,[{"epoch":0,"status":"SMOKE_ONLY"}],"phase4_v2",manifest_meta["hashes"],experiment_id,"unet",512,.5,None)
for parameter in model.parameters(): parameter.data.zero_()
state=load_training_checkpoint(checkpoint,model,optimizer,scheduler,scaler,False,device)
with torch.no_grad(): after=model(fixed_input).cpu()
checkpoint_equal=bool(torch.equal(before,after)); assert checkpoint_equal

# Determinism checks.
set_seed(42); init1=create_model("unet",in_channels=1,out_channels=1,base_channels=8)
h1=hashlib.sha256(b"".join(t.numpy().tobytes() for t in init1.state_dict().values())).hexdigest()
set_seed(42); init2=create_model("unet",in_channels=1,out_channels=1,base_channels=8)
h2=hashlib.sha256(b"".join(t.numpy().tobytes() for t in init2.state_dict().values())).hexdigest()
val_a=val[0]; val_b=val[0]; assert torch.equal(val_a["image"],val_b["image"]) and h1==h2
