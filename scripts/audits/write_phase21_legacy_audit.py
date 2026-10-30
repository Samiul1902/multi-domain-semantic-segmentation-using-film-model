"""Phase 21 — write reports/audits/phase21_legacy_medfilm_architecture_audit.json.

Read-only audit of the historical MedFiLM implementation. This artifact records
what the legacy code ACTUALLY contained (files, classes, equations, insertion
sites, reuse classification). It never claims a historical model result as a
current Phase-21 result.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

ROOT = r"D:\Softfors\jup"
OUT = os.path.join(ROOT, "reports", "audits", "phase21_legacy_medfilm_architecture_audit.json")

LEGACY_FILES = {
    "medfilm_module": r"D:\Softfors\final\medfilm_seg_v2\src_v2\models_v2\medfilm_weak_segmentation_v2.py",
    "plain_topology": r"D:\Softfors\final\medfilm_seg_v2\src_v2\models_v2\plain_weak_segmentation_v2.py",
    "attention_unet_comparator": r"D:\Softfors\final\medfilm_seg_v2\src_v2\models_v2\attention_unet_weak_segmentation_v2.py",
    "legacy_global_config": r"D:\Softfors\final\medfilm_seg\configs\global_config.json",
    "legacy_training_contract": r"D:\Softfors\final\medfilm_seg_v2\configs_v2\medfilm_weak_segmentation_training_contract_v2.json",
}

LEGACY_GLOBAL_CONFIG = {
    "path": r"D:\Softfors\final\medfilm_seg\configs\global_config.json",
    "datasets_selected": ["isic2018", "busi", "kvasir"],
    "task_ids": {"isic2018": 0, "busi": 1, "kvasir": 2},
    "image_size": 256,
    "batch_size": 8,
    "num_workers": 0,
    "learning_rate": 0.0003,
    "weight_decay": 0.0001,
    "optimizer": "AdamW",
    "scheduler": "CosineAnnealingLR",
    "mixed_precision": True,
    "early_stopping_patience": 12,
    "proposed_epochs": 80,
    "adopted_for_phase21": False,
    "why_not_adopted": (
        "Three-domain only (no KUB). Hyperparameters belong to a superseded weak-label "
        "pipeline. Phase 21 inherits the frozen Phase-20 protocol JSON instead."
    ),
}


def sha256(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main() -> int:
    inspected = []
    for key, path in LEGACY_FILES.items():
        inspected.append(
            {
                "key": key,
                "path": path,
                "exists": os.path.exists(path),
                "sha256": sha256(path),
                "bytes": os.path.getsize(path) if os.path.exists(path) else None,
            }
        )

    audit = {
        "artifact": "phase21_legacy_medfilm_architecture_audit",
        "phase": 21,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": (
            "Record the historical tested MedFiLM implementation before freezing the Phase-21 "
            "Global MedFiLM architecture. Prior engineering evidence only."
        ),
        "evidence_status": "PRIOR_ENGINEERING_EXPERIMENTAL_EVIDENCE",
        "not_current_prospective_result": True,
        "claim_policy": (
            "No historical MedFiLM metric is claimed as a Phase-21 result. Historical numbers "
            "were produced under a different dataset population, weak-label loss and protocol."
        ),
        "files_inspected": inspected,
        "historical_class_names": {
            "film_module": "FeatureWiseLinearModulation",
            "film_model": "MedFiLMSharedEncoderMultiTaskSegmenter",
            "plain_model": "PlainSharedEncoderMultiTaskSegmenter",
            "encoder_block": "ResidualBlock",
            "decoder_block": "DecoderBlock",
            "conv_norm_act": "ConvNormAct",
            "weak_loss": "SparseSeedSegmentationLoss",
            "weak_loss_composite": "CollapseResistantWeakSegmentationLoss",
        },
        "film_equation": {
            "form": "F_hat = (1 + gamma(t)) * F + beta(t)",
            "gamma_definition": "gamma = tanh(gamma_raw)",
            "beta_definition": "beta = tanh(beta_raw)",
            "raw_source": "output = Linear(hidden_dim -> 2*C)(SiLU(Linear(embedding_dim -> hidden_dim)(task_embedding)))",
            "gamma_beta_split": "parameters.chunk(2, dim=1)",
            "broadcast": "gamma/beta unsqueezed to [B, C, 1, 1]",
            "bounded": True,
            "bound_reason": "Protect early weak-label training from large task-conditioned scale/shift.",
            "identity_at_init": True,
            "identity_mechanism": (
                "output Linear weight+bias zero-initialised -> gamma_raw=beta_raw=0 -> gamma=beta=0 "
                "-> F_hat = F exactly at initialisation while remaining trainable."
            ),
        },
        "task_embedding": {
            "implementation": "nn.Embedding(task_count, embedding_dim)",
            "embedding_dim_legacy": 32,
            "init": "nn.init.normal_(weight, mean=0.0, std=0.02)",
            "film_hidden_dim_legacy": 64,
            "input_validation": "_validate_task_ids: shape [B], non-empty, 0 <= id < task_count",
            "sole_conditioning_path": True,
        },
        "film_insertion_locations": {
            "count": 5,
            "sites": {
                "bridge": "after self.bridge(self.pool(skip4))",
                "decoder4": "after decoder4(bridge, skip4)",
                "decoder3": "after decoder3(decoded, skip3)",
                "decoder2": "after decoder2(decoded, skip2)",
                "decoder1": "after decoder1(decoded, skip1)",
            },
            "channel_map_legacy": {"bridge": 256, "decoder4": 192, "decoder3": 96, "decoder2": 48, "decoder1": 24},
            "order": ["bridge", "decoder4", "decoder3", "decoder2", "decoder1"],
        },
        "topology_features": {
            "residual_connections": True,
            "residual_mechanism": "ResidualBlock: skip (1x1 conv if channels differ else Identity) + SiLU(output + residual)",
            "squeeze_excitation": False,
            "deep_supervision": False,
            "attention_gates": False,
            "encoder_stages": ["encoder1", "encoder2", "encoder3", "encoder4", "bridge"],
            "pooling": "nn.MaxPool2d(kernel_size=2, stride=2)",
            "decoder_upsampling": "F.interpolate(mode='bilinear', align_corners=False) to skip size",
            "norm": "nn.GroupNorm(_group_count(C), C) with groups from (8,4,2,1)",
            "activation": "nn.SiLU(inplace=True)",
            "conv_bias": False,
            "legacy_channels": [24, 48, 96, 192, 256],
        },
        "input_adapter": {
            "legacy_image_shape": "[B, 3, H, W] (3-channel enforced)",
            "legacy_image_size": 256,
            "current_phase21_input": "[B, 3, H, W] at 512 px",
            "adaptation_required": False,
            "adaptation_note": (
                "The frozen Phase-20 protocol freezes channel_policy=RGB_3CH (native-L domains are "
                "deterministically replicated to 3 identical channels) and in_channels=3. Phase 21 "
                "inherits that EXACTLY, so the legacy 3-channel encoder first stage is already "
                "compatible. Only the spatial size changes (256 -> 512)."
            ),
            "inherited_channel_policy": "RGB_3CH",
            "inherited_in_channels": 3,
        },
        "heads": {
            "legacy_scheme": "per-task 1x1 Conv2d heads in an nn.ModuleDict keyed by str(task_id)",
            "legacy_reason": "Weak-label multi-class semantics differed per task",
            "phase21_decision": "DO_NOT_REUSE",
            "phase21_scheme": (
                "ONE shared 1x1 head producing a single foreground logit. Task identity enters ONLY "
                "through the FiLM embedding (the Phase-21 requirement: no dataset-specific head)."
            ),
        },
        "parameter_count": {
            "legacy_measured": False,
            "note": (
                "Legacy parameter count was not recorded in the inspected artifacts; the Phase-21 "
                "implementation must report its own measured parameter count."
            ),
        },
        "four_domain_compatibility": {
            "legacy_task_count": 3,
            "legacy_domains": ["isic2018", "busi", "kvasir"],
            "kub_present": False,
            "extension_needed": (
                "task_count must become 4 with task_id KUB=3; the FiLM mechanism is domain-agnostic "
                "and needs no structural change beyond the embedding table size."
            ),
            "compatible": True,
        },
        "pretrained_dependencies": {
            "external_pretrained_weights": False,
            "libraries": ["torch", "torch.nn", "torch.nn.functional"],
            "banned_libs_absent": ["timm", "transformers", "segmentation_models_pytorch", "einops"],
            "note": "Legacy MedFiLM was trained from scratch; no pretrained backbone.",
        },
        "reuse_classification": {
            "reuse_safe": [
                "FeatureWiseLinearModulation (equation, bounded tanh, zero-init identity)",
                "task_embedding nn.Embedding(task_count, dim) with normal_(0, 0.02) init",
                "5-site FiLM insertion pattern (bridge, decoder4..decoder1)",
                "ResidualBlock / DecoderBlock topology (residual, no SE, no deep supervision)",
                "film_parameters_for_tasks() diagnostic accessor",
                "_validate_task_ids contract (shape [B], range-checked)",
            ],
            "must_not_reuse": [
                "SparseSeedSegmentationLoss / CollapseResistantWeakSegmentationLoss (weak-label loss)",
                "weak_segmentation_dataset_v2 sparse 0/1..254/255 CAM-seed encoding",
                "per-task multi-class heads (Phase 21 requires ONE shared output definition)",
                "legacy weak-label image adapter / sparse-seed dataset (Phase 21 is fully supervised)",
                "legacy 3-domain task registry (Phase 21 is four-domain)",
                "legacy hyperparameters (256 px, batch 8, lr 3e-4, patience 12)",
            ],
            "reference_only": [
                "legacy global_config.json task-ID corroboration",
                "legacy metric-name vocabulary",
            ],
        },
        "ambiguities": [
            "Legacy FiLM sites operate on decoder feature maps only; no encoder-stage FiLM. Phase 21 "
            "preserves the 5-site decoder+bridge placement.",
            "Legacy output projection zero-init makes FiLM an exact identity at step 0; task "
            "conditioning therefore must be LEARNED. A weak conditioning effect at convergence is a "
            "possible outcome and must be reported honestly (CONDITIONING_EFFECT_WEAK), not hidden.",
            "Legacy embedding_dim=32 and film_hidden_dim=64 were tuned for a 3-domain weak-label "
            "problem; Phase 21 adopts them as the best-supported historical reference values and "
            "freezes them BEFORE training.",
            "Legacy task embedding init std 0.02 combined with zero-init FiLM output means the "
            "embedding gradient at step 0 is zero for gamma/beta; conditioning emerges after the "
            "output projection leaves zero.",
        ],
        "conclusion": (
            "A technically valid GLOBAL MedFiLM reference exists in legacy evidence and is reusable "
            "as a REFERENCE_ONLY engineering pattern. Phase 21 reconstructs it as ONE shared "
            "four-domain task-conditioned model with a single foreground head, inheriting the frozen "
            "Phase-20 training protocol. Legacy results are NOT current Phase-21 results."
        ),
        "test_reads": 0,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(audit, fh, indent=2, ensure_ascii=False)
    print("WROTE", OUT)
    print("n_files_inspected", len(inspected))
    print("all_exist", all(i["exists"] for i in inspected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
