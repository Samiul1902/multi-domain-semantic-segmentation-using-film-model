import torch
from src.metrics.segmentation import binary_metrics, aggregate_binary_metrics


@torch.no_grad()
def validate(model, loader, loss_function, device, threshold=0.5, amp=True):
    model.eval(); losses=[]; metric_batches=[]; subgroup={}
    for batch in loader:
        images=batch["image"].to(device); masks=batch["mask"].to(device)
        with torch.amp.autocast(device_type=device.type, enabled=amp and device.type=="cuda"):
            logits=model(images); loss=loss_function(logits,masks)
        losses.append(loss.item()); metrics=binary_metrics(logits,masks,threshold); metric_batches.append(metrics)
        for i,(view,category) in enumerate(zip(batch["view_type"],batch["category"])):
            for key,value in (("view_type",view),("category",category)):
                bucket=subgroup.setdefault((key,value),[])
                bucket.append({name:tensor[i:i+1].cpu() for name,tensor in metrics.items()})
    summary=aggregate_binary_metrics(metric_batches); summary["loss"]=sum(losses)/len(losses)
    subgroup_summary={f"{k}:{v}":{"n":len(items),**aggregate_binary_metrics(items)} for (k,v),items in subgroup.items()}
    return summary, subgroup_summary
