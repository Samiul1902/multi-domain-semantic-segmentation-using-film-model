import torch, json
from pathlib import Path
for p in ["checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
          "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
          "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
          "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt"]:
    ck = torch.load(p, map_location="cpu", weights_only=False)
    print("=" * 70)
    print(p)
    print("  type:", type(ck).__name__)
    if isinstance(ck, dict):
        for k, v in ck.items():
            if isinstance(v, dict):
                n = sum(x.numel() for x in v.values() if hasattr(x, "numel"))
                print(f"    {k}: dict[{len(v)}] tensors, {n} elements, first={list(v)[:2]}")
            elif hasattr(v, "numel"):
                print(f"    {k}: tensor{tuple(v.shape)}")
            else:
                print(f"    {k}: {type(v).__name__} = {str(v)[:80]}")
