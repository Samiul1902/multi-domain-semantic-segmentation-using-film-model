"""H2B SEC 12 -- CPU-only synthetic loss / gradient audit for SoftTargetFocalBCE.

No model construction. No CUDA. No project images or masks.
Pure scalar/tensor arithmetic on synthetic values.
"""
import json
import math
import sys
from pathlib import Path

import pandas as pd
import torch

ROOT = Path(r"D:\Softfors\jup")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.losses.soft_target_focal_bce import SoftTargetFocalBCE
AUDITS = ROOT / "reports" / "audits"
TABLES = ROOT / "reports" / "tables"

GAMMA = 2.0
TARGETS = [0.0, 0.25, 0.50, 0.75, 1.0]
PROBS = [0.01, 0.10, 0.25, 0.50, 0.75, 0.90, 0.99]

criterion = SoftTargetFocalBCE(gamma=GAMMA)


def logit_of(p: float) -> float:
    return math.log(p / (1.0 - p))


rows = []
for y in TARGETS:
    for p in PROBS:
        z = torch.tensor([[logit_of(p)]], dtype=torch.float32, requires_grad=True)
        t = torch.tensor([[y]], dtype=torch.float32)
        loss = criterion(z, t)
        loss.backward()
        g = float(z.grad.item())
        L = float(loss.item())
        finite = bool(math.isfinite(L) and math.isfinite(g))
        # dL/dp = (dL/dlogit) / (p(1-p)); a loss minimised at p=y must satisfy
        # sign(dL/dp) == sign(p - y).
        dp = p * (1.0 - p)
        dLdp = g / dp if dp > 0 else float("nan")
        if abs(p - y) < 1e-12:
            direction_ok = True
        else:
            direction_ok = (dLdp > 0) == (p > y)
        rows.append({
            "target": y,
            "probability": p,
            "logit": logit_of(p),
            "loss": L,
            "gradient_dL_dlogit": g,
            "finite": finite,
            "expected_direction_pass": bool(direction_ok),
        })

df = pd.DataFrame(rows)

# --- monotonicity for hard targets -------------------------------------------
def strictly_increasing(vals):
    return all(b > a for a, b in zip(vals, vals[1:]))

def strictly_decreasing(vals):
    return all(b < a for a, b in zip(vals, vals[1:]))

y0 = df[df.target == 0.0].sort_values("probability")
y1 = df[df.target == 1.0].sort_values("probability")
y0_increasing = strictly_increasing(y0.loss.tolist())
y1_decreasing = strictly_decreasing(y1.loss.tolist())

# --- soft-target minimiser near p == y ---------------------------------------
soft_min_ok = {}
for y in [0.25, 0.50, 0.75]:
    sub = df[df.target == y].sort_values("probability")
    losses = sub.loss.tolist()
    probs = sub.probability.tolist()
    argmin_i = min(range(len(losses)), key=lambda i: losses[i])
    soft_min_ok[str(y)] = {
        "argmin_probability": probs[argmin_i],
        "target": y,
        "abs_gap": abs(probs[argmin_i] - y),
        "ok": abs(probs[argmin_i] - y) <= 0.25,
    }

# --- symmetry: L(y=0,p=q) ~= L(y=1,p=1-q) ------------------------------------
sym_rows = []
for q in [0.01, 0.10, 0.25, 0.50, 0.75, 0.90, 0.99]:
    z0 = torch.tensor([[logit_of(q)]], dtype=torch.float32)
    l0 = float(criterion(z0, torch.tensor([[0.0]])).item())
    z1 = torch.tensor([[logit_of(1.0 - q)]], dtype=torch.float32)
    l1 = float(criterion(z1, torch.tensor([[1.0]])).item())
    sym_rows.append({"q": q, "L_y0_p_q": l0, "L_y1_p_1mq": l1, "abs_diff": abs(l0 - l1)})
sym_df = pd.DataFrame(sym_rows)
symmetry_max_abs_diff = float(sym_df.abs_diff.max())

# --- gradient-flow / non-detachment check ------------------------------------
z = torch.tensor([[logit_of(0.7)]], dtype=torch.float32, requires_grad=True)
t = torch.tensor([[0.3]], dtype=torch.float32)
crit = SoftTargetFocalBCE(gamma=GAMMA)
loss = crit(z, t)
loss.backward()
grad_norm = float(z.grad.abs().item())

# Explicitly verify the modulation term carries gradient: compare against a
# variant in which p IS detached from modulation.
p = torch.sigmoid(z.detach())
mod_detached = (p - t).abs().pow(GAMMA)
bce = torch.nn.functional.binary_cross_entropy_with_logits(z, t, reduction="none")
loss_detached = (mod_detached * bce).mean()
z2 = z.detach().clone().requires_grad_(True)
loss_detached2 = (mod_detached.detach() * torch.nn.functional.binary_cross_entropy_with_logits(z2, t, reduction="none")).mean()
loss_detached2.backward()
grad_detached = float(z2.grad.abs().item())

modulation_not_detached = bool(abs(grad_norm - grad_detached) > 1e-9)

# --- target contract enforcement ---------------------------------------------
contract = {}
try:
    crit(torch.zeros(1, 1), torch.tensor([[1.5]]))
    contract["out_of_range_rejected"] = False
except AssertionError:
    contract["out_of_range_rejected"] = True
try:
    crit(torch.zeros(1, 1), torch.tensor([[float("nan")]]))
    contract["nonfinite_rejected"] = False
except AssertionError:
    contract["nonfinite_rejected"] = True

all_finite = bool(df.finite.all())
all_direction_ok = bool(df.expected_direction_pass.all())

verdict = {
    "all_losses_and_gradients_finite": all_finite,
    "no_nan_no_inf": all_finite,
    "y0_loss_increases_with_p": y0_increasing,
    "y1_loss_increases_as_p_to_0": y1_decreasing,
    "soft_target_minimised_near_p_equals_y": all(v["ok"] for v in soft_min_ok.values()),
    "symmetry_L_y0_q_equals_L_y1_1mq": symmetry_max_abs_diff < 1e-5,
    "modulation_not_detached": modulation_not_detached,
    "all_rows_expected_direction_pass": all_direction_ok,
    "target_out_of_range_rejected": contract["out_of_range_rejected"],
    "target_nonfinite_rejected": contract["nonfinite_rejected"],
}
audit_pass = all(verdict.values())

# --- write table --------------------------------------------------------------
TABLES.mkdir(parents=True, exist_ok=True)
csv_path = TABLES / "post_phase13_h2b_soft_target_focal_gradient_sanity.csv"
df.to_csv(csv_path, index=False)

# --- write audit --------------------------------------------------------------
def sha(p):
    import hashlib
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

loss_module = ROOT / "src" / "losses" / "soft_target_focal_bce.py"

audit = {
    "artifact": "POST_PHASE13_H2B_SOFT_TARGET_FOCAL_LOSS_UNIT_AUDIT",
    "status": "PASS" if audit_pass else "FAIL",
    "execution": "CPU_ONLY_SYNTHETIC",
    "model_constructions": 0,
    "cuda_requests": 0,
    "project_images_or_masks_used": 0,
    "loss_module": {
        "path": "src/losses/soft_target_focal_bce.py",
        "sha256": sha(loss_module),
        "class": "SoftTargetFocalBCE",
        "gamma": GAMMA,
        "gamma_fixed_prospectively": True,
        "gamma_tuned_on_h2b_val": False,
    },
    "formula": "L = mean( |sigmoid(z) - y|^gamma * BCEWithLogits(z, y) ), gamma = 2.0",
    "modulation_detached": "NO",
    "gradient_flows_through_bce_term": True,
    "gradient_flows_through_modulation_term": True,
    "gradient_norm_loss_path": grad_norm,
    "gradient_norm_detached_variant": grad_detached,
    "target_grid": TARGETS,
    "probability_grid": PROBS,
    "checks": verdict,
    "soft_target_argmin": soft_min_ok,
    "symmetry_max_abs_diff": symmetry_max_abs_diff,
    "table": {
        "path": "reports/tables/post_phase13_h2b_soft_target_focal_gradient_sanity.csv",
        "sha256": sha(csv_path),
        "rows": int(len(df)),
        "columns": list(df.columns),
    },
    "hyperparameter_grid": 0,
    "alpha_sweep": 0,
    "beta_sweep": 0,
    "coefficient_search": 0,
}
(AUDITS / "post_phase13_h2b_soft_target_focal_loss_unit_audit.json").write_text(
    json.dumps(audit, indent=2), encoding="utf-8")

print("AUDIT PASS:", audit_pass)
for k, v in verdict.items():
    print(f"  {k}: {v}")
print("symmetry max abs diff:", symmetry_max_abs_diff)
print("rows:", len(df), "->", csv_path.name)
print("loss module sha:", audit["loss_module"]["sha256"])
