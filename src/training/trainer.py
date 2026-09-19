"""Single reusable TRAIN/VAL trainer; TEST is never accepted."""
import time
import torch
from .evaluator import validate


class EarlyStopping:
    def __init__(self, patience=15): self.patience=patience; self.best=float("-inf"); self.bad_epochs=0
    def update(self, score):
        if score>self.best: self.best=score; self.bad_epochs=0; return False
        self.bad_epochs+=1; return self.bad_epochs>=self.patience


class Trainer:
    def __init__(self, model, optimizer, scheduler, loss_function, device, amp=True,
                 gradient_accumulation_steps=1, threshold=0.5, patience=15):
        self.model=model; self.optimizer=optimizer; self.scheduler=scheduler; self.loss_function=loss_function
        self.device=device; self.amp=amp and device.type=="cuda"; self.accumulation=gradient_accumulation_steps
        self.threshold=threshold; self.scaler=torch.amp.GradScaler("cuda",enabled=self.amp)
        self.early_stopping=EarlyStopping(patience); self.global_step=0; self.history=[]

    def train_one_epoch(self, loader, max_batches=None):
        if getattr(loader.dataset,"split","").upper()!="TRAIN": raise ValueError("Trainer optimization requires TRAIN data")
        self.model.train(); self.optimizer.zero_grad(set_to_none=True); losses=[]; start=time.perf_counter()
        for index,batch in enumerate(loader):
            if max_batches is not None and index>=max_batches: break
            images=batch["image"].to(self.device); masks=batch["mask"].to(self.device)
            with torch.amp.autocast(device_type=self.device.type,enabled=self.amp):
                logits=self.model(images); loss=self.loss_function(logits,masks)/self.accumulation
            self.scaler.scale(loss).backward()
            if (index+1)%self.accumulation==0:
                self.scaler.step(self.optimizer); self.scaler.update(); self.optimizer.zero_grad(set_to_none=True)
            losses.append(loss.item()*self.accumulation); self.global_step+=1
        return {"loss":sum(losses)/len(losses),"seconds":time.perf_counter()-start}

    def validate(self, loader, max_batches=None):
        if getattr(loader.dataset,"split","").upper()!="VAL": raise ValueError("Development validation requires VAL data")
        if max_batches is not None:
            import itertools
            loader=itertools.islice(loader,max_batches)
        return validate(self.model,loader,self.loss_function,self.device,self.threshold,self.amp)
