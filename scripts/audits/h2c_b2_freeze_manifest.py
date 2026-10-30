"""H2C-B2 SEC 5 -- freeze manifest (produced immediately before the first segmentation forward)."""
import hashlib
import json
from pathlib import Path

import torch

ROOT = Path(r"D:\Softfors\jup")
A = ROOT / "reports" / "audits"
T = ROOT / "reports" / "tables"
EID = ("post_phase13_h2c_kub_localizer_spatialhead3x3relu_r512_h128_sigmaeq075_"
       "centernetfocal_deploymentbalance_seed42_clean_v3")


def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


ck = torch.load(ROOT / "checkpoints" / EID / "best.pt", map_location="cpu", weights_only=False)
proto = json.loads((A / "post_phase13_h2c_protocol_frozen.json").read_text("utf-8"))

manifest = {
    "artifact": "POST_PHASE13_H2C_B2_FREEZE_MANIFEST",
    "status": "FROZEN_PRE_FIRST_SEGMENTATION_FORWARD",
    "created_utc": "2026-09-24T00:29:00Z",
    "h2c_experiment_id": EID,
    "h2c_b1_best_checkpoint_path": f"checkpoints/{EID}/best.pt",
    "h2c_b1_best_checkpoint_sha256": sha(ROOT / "checkpoints" / EID / "best.pt"),
    "selected_epoch": int(ck["epoch"]),
    "head_identity": "SPATIAL_DISCRIMINATIVE_HEAD_3X3_RELU_1X1_V1",
    "authoritative_h2c_protocol_sha": sha(A / "post_phase13_h2c_protocol_frozen.json"),
    "b2_specification": {
        "location": "reports/audits/post_phase13_h2c_protocol_frozen.json :: prospective_downstream_contract",
        "sha256": sha(A / "post_phase13_h2c_protocol_frozen.json"),
        "note": ("The frozen H2C protocol contains the frozen B2 downstream contract, evidence "
                 "dimensions A-D, four prospective outcome definitions, comparator discipline and "
                 "the execution split. Crop/restore and fusion are specified by reference to the "
                 "already-frozen Part1D square/padding-correct lineage."),
    },
    "proposal_policy_identity": {
        "source": "post_phase13_h2c_best_checkpoint_proposals.csv",
        "sha256": sha(T / "post_phase13_h2c_best_checkpoint_proposals.csv"),
        "threshold": 0.10, "margin": 0.20, "top_k": 5, "nms_iou": 0.30,
        "proposal_rows": 462,
    },
    "segmentation_checkpoint_identity": {
        "unet": sha(ROOT / "checkpoints/phase9_kub_unet_baseline_seed42_512_clean_v3/best.pt"),
        "attention_unet": sha(ROOT / "checkpoints/phase10_kub_attention_unet_seed42_512_clean_v3/best.pt"),
        "unetpp": sha(ROOT / "checkpoints/phase10_kub_unetpp_seed42_512_clean_v3/best.pt"),
        "deeplabv3plus": sha(ROOT / "checkpoints/phase10_kub_deeplabv3plus_seed42_512_clean_v3/best.pt"),
    },
    "dataset_split_identity": {
        "split": "VAL (phase4_v3 manifest)",
        "manifest_sha": sha(ROOT / "manifests/phase4_v3/val.csv"),
        "cases": 103, "components": 152, "ROI": "EXCLUDED",
    },
    "global_cache": {
        "manifest": "data_cache/phase13_part1d_b_predicted_region_clean_v3/global_512_manifest.csv",
        "sha256": sha(ROOT / "data_cache/phase13_part1d_b_predicted_region_clean_v3/global_512_manifest.csv"),
        "items": 412, "dtype": "float32",
    },
    "evaluation_script": {
        "path": "scripts/inference/post_phase13_h2c_downstream_eval.py",
        "sha256": sha(ROOT / "scripts/inference/post_phase13_h2c_downstream_eval.py"),
    },
    "relevant_configuration_shas": {
        "h2c_config": sha(ROOT / "configs/phase13_clean_v3" / f"{EID}.yaml"),
        "part1d_helper": sha(ROOT / "scripts/inference/phase13_part1d_predicted_region_inference.py"),
    },
    "random_seed": {"training_seed": 42, "downstream_deterministic": True,
                    "stochastic_operations_in_b2": "NONE"},
    "authorization_identity": "USER_SUPERVISOR_MESSAGE_POST_H2C_B1",
    "scientific_axis_change_count": 1,
    "test_read_counter": 0,
    "external_test_read_counter": 0,
    "downstream_forward_counter_before_b2": 0,

    "confirmations": {
        "NO_SCIENTIFIC_PARAMETER_SELECTED_USING_B2_RESULTS": True,
        "H2C_B2_IS_EVALUATION_ONLY": True,
    },
}
(A / "post_phase13_h2c_b2_freeze_manifest.json").write_text(
    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

md = ["# POST-PHASE13 H2C-B2 — Freeze Manifest", "",
      f"- **Status: {manifest['status']}**", "",
      "| field | value |", "|---|---|"]
for k in ("h2c_experiment_id", "h2c_b1_best_checkpoint_path", "h2c_b1_best_checkpoint_sha256",
          "selected_epoch", "head_identity", "authoritative_h2c_protocol_sha",
          "authorization_identity", "scientific_axis_change_count", "test_read_counter",
          "external_test_read_counter", "downstream_forward_counter_before_b2"):
    md.append(f"| {k} | `{manifest[k]}` |")
md += ["", "## Confirmations", "",
       f"- `NO_SCIENTIFIC_PARAMETER_SELECTED_USING_B2_RESULTS` = "
       f"**{manifest['confirmations']['NO_SCIENTIFIC_PARAMETER_SELECTED_USING_B2_RESULTS']}**",
       f"- `H2C_B2_IS_EVALUATION_ONLY` = "
       f"**{manifest['confirmations']['H2C_B2_IS_EVALUATION_ONLY']}**", "",
       "## Segmentation checkpoints", "", "| model | SHA-256 |", "|---|---|"]
for k, v in manifest["segmentation_checkpoint_identity"].items():
    md.append(f"| {k} | `{v}` |")
md += ["", "## Proposal policy", "",
       f"- source `{manifest['proposal_policy_identity']['source']}` "
       f"({manifest['proposal_policy_identity']['proposal_rows']} rows)",
       f"- threshold 0.10 / margin 0.20 / top_k 5 / NMS 0.30", ""]
(A / "post_phase13_h2c_b2_freeze_manifest.md").write_text("\n".join(md), encoding="utf-8")

print("freeze manifest written")
print("  best.pt sha:", manifest["h2c_b1_best_checkpoint_sha256"])
print("  selected epoch:", manifest["selected_epoch"])
print("  protocol sha:", manifest["authoritative_h2c_protocol_sha"])
print("  confirmations:", manifest["confirmations"])
