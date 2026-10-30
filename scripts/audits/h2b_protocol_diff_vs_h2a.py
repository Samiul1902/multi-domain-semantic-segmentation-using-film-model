"""H2B SEC 13 -- static one-axis diff audit: H2B protocol vs H2A protocol.

Static text/JSON comparison only. No execution, no CUDA, no model construction.
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\Softfors\jup")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
AUDITS = ROOT / "reports" / "audits"
TABLES = ROOT / "reports" / "tables"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


H2A = json.loads((AUDITS / "post_phase13_h2a_protocol_frozen.json").read_text("utf-8"))
h2a_tc = H2A["frozen_training_contract"]
h2a_pc = H2A["frozen_proposal_evaluation_contract"]

H2B_EXPERIMENT_ID = (
    "post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_"
    "softtargetfocalgamma2_deploymentbalance_seed42_clean_v3"
)
LOSS_SHA = sha(ROOT / "src" / "losses" / "soft_target_focal_bce.py")

SAME = "UNCHANGED"
# (field, h2a_value, h2b_value, scientific_role)
ROWS = [
    # --- provenance / identity (changed by construction, not scientific) ---
    ("experiment_id", H2A["experiment_id"], H2B_EXPERIMENT_ID, "PROVENANCE"),
    ("protocol_binding", "post_phase13_h2a_protocol_frozen.json",
     "post_phase13_h2b_protocol_frozen.json", "PROVENANCE"),
    ("loss_implementation_sha", "src/losses/localization.py::CenterNetFocalLoss",
     f"src/losses/soft_target_focal_bce.py::{LOSS_SHA[:16]}...", "PROVENANCE"),

    # --- THE single scientific axis ---
    ("loss_name", "CenterNetFocalLoss", "SoftTargetFocalBCE", "SCIENTIFIC_AXIS"),
    ("loss_mathematical_semantics",
     "L_pos=-(1-p)^alpha*log(p); L_neg=-(1-y)^beta*p^alpha*log(1-p); alpha=2,beta=4; target==1 is the positive condition",
     "L=mean(|sigmoid(z)-y|^2 * BCEWithLogits(z,y)); complete Gaussian target treated as continuous supervision; gamma=2.0",
     "SCIENTIFIC_AXIS"),

    # --- architecture (unchanged) ---
    ("architecture", h2a_tc["architecture"], h2a_tc["architecture"], "ARCHITECTURE"),
    ("backbone", "3-stage compact U-Net", "3-stage compact U-Net", "ARCHITECTURE"),
    ("in_channels", h2a_tc["in_channels"], 1, "ARCHITECTURE"),
    ("out_channels", h2a_tc["out_channels"], 1, "ARCHITECTURE"),
    ("base_channels", h2a_tc["base_channels"], 16, "ARCHITECTURE"),
    ("head_structure", "final 1x1 Conv2d(b,1)", "final 1x1 Conv2d(b,1)", "ARCHITECTURE"),
    ("head_initialization", "weight=0.0; bias=log(0.1/0.9)", "weight=0.0; bias=log(0.1/0.9)", "ARCHITECTURE"),
    ("weight_initialization", "kaiming_normal_(relu); bias zeros", "kaiming_normal_(relu); bias zeros", "ARCHITECTURE"),

    # --- target (unchanged) ---
    ("target_construction", h2a_tc["target"], h2a_tc["target"], "TARGET"),
    ("target_sigma", h2a_tc["sigma"], 0.75, "TARGET"),
    ("heatmap_resolution", h2a_tc["heatmap"], "128 x 128", "TARGET"),
    ("target_center_value", "1.0 at canonical center pixel", "1.0 at canonical center pixel", "TARGET"),
    ("target_range", "[0,1]", "[0,1]", "TARGET"),

    # --- data / split (unchanged) ---
    ("dataset", "clean-v3 FULL_FIELD", "clean-v3 FULL_FIELD", "DATA"),
    ("split", h2a_tc["TRAIN"] + " | " + h2a_tc["VAL"] + " | ROI " + h2a_tc["ROI"],
     h2a_tc["TRAIN"] + " | " + h2a_tc["VAL"] + " | ROI " + h2a_tc["ROI"], "DATA"),
    ("manifest", h2a_tc["manifest"], "phase4_v3", "DATA"),
    ("taxonomy", h2a_tc["taxonomy"], "kub_size_clean_v3_v1", "DATA"),
    ("input_resolution", h2a_tc["input"], "512 x 512", "DATA"),
    ("augmentation", h2a_tc["augmentation"], "UNCHANGED from clean-v3 Phase13", "DATA"),

    # --- optimization (unchanged) ---
    ("optimizer", h2a_tc["optimizer"], "AdamW", "OPTIMIZATION"),
    ("learning_rate", h2a_tc["lr"], 0.0001, "OPTIMIZATION"),
    ("weight_decay", h2a_tc["weight_decay"], 0.0001, "OPTIMIZATION"),
    ("scheduler", h2a_tc["scheduler"], "CosineAnnealingLR(T_max=100)", "OPTIMIZATION"),
    ("batch_size", h2a_tc["batch"], 4, "OPTIMIZATION"),
    ("amp_semantics", h2a_tc["amp"], "same accepted Phase13 semantics", "OPTIMIZATION"),
    ("seed", h2a_tc["seed"], 42, "OPTIMIZATION"),
    ("max_epochs", h2a_tc["max_epochs"], 100, "OPTIMIZATION"),
    ("workers", h2a_tc["workers"], 0, "OPTIMIZATION"),
    ("cuda", h2a_tc["cuda"], h2a_tc["cuda"], "OPTIMIZATION"),
    ("test", h2a_tc["test"], "forbidden", "GOVERNANCE"),

    # --- checkpoint selection (unchanged, inherited from H2A) ---
    ("checkpoint_selection",
     "6-term lexicographic: " + " > ".join(H2A["h2a_primary_checkpoint_tuple"]["tuple"]),
     "6-term lexicographic: " + " > ".join(H2A["h2a_primary_checkpoint_tuple"]["tuple"]),
     "CHECKPOINT_SELECTION"),
    ("checkpoint_selection_ties", "BAD_EPOCH", "BAD_EPOCH", "CHECKPOINT_SELECTION"),
    ("checkpoint_selection_patience", 15, 15, "CHECKPOINT_SELECTION"),
    ("best_pt_policy", "strict improvement only", "strict improvement only", "CHECKPOINT_SELECTION"),
    ("latest_pt_policy", "every completed epoch", "every completed epoch", "CHECKPOINT_SELECTION"),

    # --- proposal contract (unchanged) ---
    ("proposal_threshold", h2a_pc["threshold"], 0.10, "PROPOSAL"),
    ("proposal_margin", h2a_pc["margin"], 0.20, "PROPOSAL"),
    ("proposal_top_k", h2a_pc["top_k"], 5, "PROPOSAL"),
    ("proposal_nms_iou", h2a_pc["nms_iou"], 0.30, "PROPOSAL"),
    ("proposal_grid", h2a_pc["grid"], "NONE", "PROPOSAL"),
    ("threshold_search", h2a_pc["threshold_search"], "NONE", "PROPOSAL"),
    ("h1_selective_acceptance", "NOT_CARRIED", "NOT_CARRIED", "PROPOSAL"),

    # --- fusion / downstream (unchanged) ---
    ("fusion", "PREDICTED_REGION_FLOAT_GLOBAL_RETAINED", "PREDICTED_REGION_FLOAT_GLOBAL_RETAINED", "FUSION"),
    ("fusion_inside_union", "R(x) (never max(G,R))", "R(x) (never max(G,R))", "FUSION"),
    ("segmentation_checkpoints", "unet|attention_unet|unetpp|deeplabv3plus",
     "unet|attention_unet|unetpp|deeplabv3plus", "FUSION"),
    ("segmentation_threshold", 0.5, 0.5, "FUSION"),
    ("crop_restore", "square/padding-correct", "square/padding-correct", "FUSION"),
]

rows = []
for field, h2a_v, h2b_v, role in ROWS:
    changed = "YES" if str(h2a_v) != str(h2b_v) else "NO"
    rows.append({
        "field": field,
        "h2a_value": h2a_v,
        "h2b_value": h2b_v,
        "changed": changed,
        "scientific_role": role,
    })

df = pd.DataFrame(rows)
out = TABLES / "post_phase13_h2b_protocol_diff_vs_h2a.csv"
df.to_csv(out, index=False)

changed = df[df.changed == "YES"]
changed_scientific = changed[changed.scientific_role == "SCIENTIFIC_AXIS"]
changed_provenance = changed[changed.scientific_role == "PROVENANCE"]

print("total fields:", len(df))
print("changed:", len(changed))
print(changed[["field", "scientific_role"]].to_string(index=False))
print()
print("scientific-axis changes:", len(changed_scientific))
print("provenance changes:", len(changed_provenance))
print("csv sha:", sha(out))
