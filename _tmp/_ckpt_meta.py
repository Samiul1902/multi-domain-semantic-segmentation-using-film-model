import torch, sys, json
p = r"D:/Softfors/jup/checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"
ck = torch.load(p, map_location="cpu", weights_only=False)
print("TYPE", type(ck))
if isinstance(ck, dict):
    for k, v in ck.items():
        if isinstance(v, dict):
            ks = list(v.keys())
            print(f"  {k}: dict[{len(ks)}] keys={ks[:6]}")
        elif hasattr(v, "shape"):
            print(f"  {k}: tensor{tuple(v.shape)}")
        else:
            print(f"  {k}: {type(v).__name__} = {str(v)[:120]}")
