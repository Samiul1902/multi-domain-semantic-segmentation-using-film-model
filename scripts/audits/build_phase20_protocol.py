"""Phase-20 architecture freeze + frozen protocol + prospective sampling audit.

The architecture is frozen and SHA-bound BEFORE any Phase-20 training result
exists. ``current_phase20_results_used_for_selection`` is therefore ``false``
by construction and can be re-verified after training.

Writes
------
reports/audits/phase20_baseline_architecture_freeze.json
reports/audits/phase20_shared_global_baseline_protocol.json
reports/audits/phase20_sampling_policy_audit.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.data.domain_balanced_sampler import (
    BALANCED_SAMPLING_POLICY_ID,
    build_domain_balanced_sampler,
    expected_domain_proportions,
)
from src.training.phase20_selection import SELECTION_RULE_ID

AUDIT_DIR = ROOT / "reports/audits"
MANIFEST_DIR = ROOT / "manifests/phase4_v3"
EXPERIMENT_ID = "phase20_shared_unetpp_fourdomain_seed42_clean_v3"

CODE_FILES = [
    "scripts/training/train_phase20_shared_unetpp.py",
    "src/models/unetpp.py",
    "src/models/unet.py",
    "src/data/multidomain_dataset.py",
    "src/data/transforms.py",
    "src/data/loaders.py",
    "src/data/domain_balanced_sampler.py",
    "src/losses/segmentation.py",
    "src/training/phase20_selection.py",
    "src/metrics/evaluation_metrics.py",
    "src/utils/targets.py",
    "src/utils/test_lock.py",
    "src/utils/device.py",
    "src/utils/reproducibility.py",
    "src/utils/run_lock.py",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    tr = pd.read_csv(MANIFEST_DIR / "train.csv")
    va = pd.read_csv(MANIFEST_DIR / "val.csv")
    train_counts = {k: int(v) for k, v in tr.groupby("dataset").size().items()}
    val_counts = {k: int(v) for k, v in va.groupby("dataset").size().items()}

    evidence_path = AUDIT_DIR / "phase20_legacy_baseline_selection_evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))

    # ---- 1. architecture freeze ------------------------------------------
    freeze = {
        "artifact": "phase20_baseline_architecture_freeze",
        "phase": 20,
        "experiment_id": EXPERIMENT_ID,
        "frozen_architecture": "UNet++",
        "repository_implementation": "src/models/unetpp.py",
        "factory_key": "unetpp",
        "architecture_descriptor": "unetpp_nested_4_level_no_deep_supervision_base32",
        "model_contract": {
            "in_channels": 3,
            "out_channels": 1,
            "base_channels": 32,
            "output": "single binary segmentation logit channel",
            "shared_parameters_across_domains": True,
            "forbidden_modules": ["FiLM", "task_embedding", "domain_embedding",
                                  "regional_branch", "localizer", "ROI_proposal", "routing",
                                  "dataset_specific_decoder", "dataset_specific_head"],
            "forbidden_modules_present": [],
        },
        "selection_basis": "LEGACY_TESTED_PROJECT_PRIOR_EVIDENCE",
        "selection_time": "PRE_TRAINING",
        "current_phase20_results_used_for_selection": False,
        "selection_evidence_artifact": "reports/audits/phase20_legacy_baseline_selection_evidence.json",
        "selection_evidence_sha256": sha256(evidence_path),
        "selection_evidence_summary": {
            "same_repository_clean_v3_ranking": evidence[
                "same_repository_clean_v3_conventional_comparison"]["ranking_by_best_val_macro_dice"],
            "unetpp_best_val_macro_dice_legacy_kub": evidence[
                "same_repository_clean_v3_conventional_comparison"]["strongest_value"],
            "margin_over_next": evidence[
                "same_repository_clean_v3_conventional_comparison"]["margin_over_next"],
            "evidence_label": "LEGACY_PRIOR_EVIDENCE__NOT_CURRENT_PHASE20_RESULT",
        },
        "rationale": [
            "Already implemented and tested in this repository (src/models/unetpp.py, "
            "Phase-10 clean-v3).",
            "Strongest conventional clean-v3 architecture in the repository under a fixed "
            "protocol (best VAL macro Dice 0.764160 vs 0.752513 / 0.750914 / 0.740613).",
            "Compatible with binary segmentation and a single 1-channel output head.",
            "Requires no FiLM and no regional module, so it is a clean image-only reference "
            "for Phase 21.",
        ],
        "immutability": {
            "architecture_will_not_be_switched_after_training": True,
            "no_architecture_search_in_phase20": True,
            "no_post_hoc_restart_from_epoch_1": True,
        },
    }
    write_json(AUDIT_DIR / "phase20_baseline_architecture_freeze.json", freeze)

    # ---- 2. prospective sampling audit -----------------------------------
    datasets = tr["dataset"].tolist()
    expected = expected_domain_proportions(datasets)
    # empirical check with the frozen generator (deterministic)
    sampler = build_domain_balanced_sampler(datasets, base_seed=42, epoch=1)
    drawn = list(iter(sampler))
    drawn_ds = pd.Series([datasets[i] for i in drawn])
    empirical = {k: {"count": int(v), "proportion": round(float(v) / len(drawn), 6)}
                 for k, v in drawn_ds.value_counts().items()}
    sampling_audit = {
        "artifact": "phase20_sampling_policy_audit",
        "phase": 20,
        "policy_id": BALANCED_SAMPLING_POLICY_ID,
        "policy": "WeightedRandomSampler with per-sample weight 1/n_domain, "
                  "num_samples = len(TRAIN) = 5832, replacement = True",
        "purpose": "prevent ISIC and KUB from dominating BUSI and Kvasir",
        "governance": {"task_id_used_for_sampling_only": True,
                       "task_id_passed_to_model_forward": False,
                       "dataset_used_for_bookkeeping_only": True},
        "unbalanced_pool": {d: train_counts[d] for d in sorted(train_counts)},
        "unbalanced_pool_proportions": {d: round(train_counts[d] / len(datasets), 6)
                                        for d in sorted(train_counts)},
        "expected_balanced_proportions": expected,
        "empirical_check": {
            "seed_base": 42, "epoch": 1, "num_drawn": len(drawn), "per_domain": empirical,
            "note": "Deterministic check of the frozen generator; not a scientific result.",
        },
        "effect": "each domain contributes ~25% of the sampled batches instead of "
                  f"ISIC {round(train_counts['ISIC']/len(datasets)*100,1)}% / "
                  f"KUB {round(train_counts['KUB']/len(datasets)*100,1)}% / "
                  f"KVASIR {round(train_counts['KVASIR']/len(datasets)*100,1)}% / "
                  f"BUSI {round(train_counts['BUSI']/len(datasets)*100,1)}%",
    }
    write_json(AUDIT_DIR / "phase20_sampling_policy_audit.json", sampling_audit)

    # ---- 3. frozen protocol ----------------------------------------------
    protocol = {
        "artifact": "phase20_shared_global_baseline_protocol",
        "phase_id": 20,
        "stage": "B",
        "title": "Shared Multi-Domain Global Baseline (single frozen UNet++, no FiLM, no regional module)",
        "status": "PHASE20_PROTOCOL_FROZEN__AWAITING_EXECUTION",
        "primary_question": "How well can ONE shared conventional segmentation model represent all "
                            "four medical domains under the harmonized Stage-B data contract, "
                            "WITHOUT task-conditioned FiLM and WITHOUT the regional mechanism?",
        "is_model_training_phase": True,
        "experiment_id": EXPERIMENT_ID,
        "architecture": "unetpp_nested_4_level_no_deep_supervision_base32",
        "architecture_selection_evidence": "reports/audits/phase20_baseline_architecture_freeze.json",
        "input_representation": {
            "channel_policy": "RGB_3CH",
            "contract_label": "PHASE20_BASELINE_OPERATIONAL_INPUT_ONLY",
            "not_the_final_phase24_policy": True,
            "rules": ["native RGB domains remain deterministic RGB",
                      "native-L domains are deterministically replicated to 3 identical channels",
                      "no learned modality adapter",
                      "no domain-specific normalization branch"],
            "intensity_normalization": "divide by 255.0 -> [0, 1]",
            "model_input_excludes": ["task_id", "dataset_id", "KUB category", "patient_id",
                                     "case_id", "foreground_fraction", "mask-derived metadata"],
        },
        "input_resolution": 512,
        "resolution_decision": {
            "frozen": 512,
            "decision_time": "PRE_TRAINING",
            "no_resolution_search": True,
            "did_not_compare": ["256 vs 384", "256 vs 512", "384 vs 512"],
            "evidence": [
                "No legacy KUB-bearing four-domain shared baseline exists "
                "(reports/audits/phase20_legacy_baseline_selection_evidence.json).",
                "The legacy fully-supervised shared three-domain baseline used 256 px "
                "(medfilm_seg) but belongs to a superseded pipeline whose hyperparameters the "
                "Phase-19 reuse map explicitly does NOT adopt.",
                "The frozen architecture's own repository clean-v3 evidence (Phase-10 UNet++) "
                "was obtained at 512 px.",
                "512 is the Phase-19 preprocessing default_size and preserves KUB tiny-object "
                "detail, which is the project's central difficulty.",
                "A throughput probe (execution mechanism only) confirmed 512 px at batch 4 with "
                "4 loader workers costs ~7.3 min/epoch against ~7.0 min/epoch of GPU time, so "
                "512 is operationally affordable.",
            ],
            "supported_sizes_available": [256, 512, 768, 1024],
        },
        "preprocessing_contract_id": "phase19_preprocessing_contract_v1",
        "preprocessing_contract_sha256": sha256(
            AUDIT_DIR / "phase19_preprocessing_contract.json"),
        "evaluation_contract_id": "phase19_evaluation_contract_v1",
        "evaluation_contract_sha256": sha256(
            AUDIT_DIR / "phase19_evaluation_contract.json"),
        "dataset_populations": {
            "manifest_version": "phase4_v3",
            "TRAIN": train_counts, "VAL": val_counts,
            "TRAIN_total": int(len(tr)), "VAL_total": int(len(va)),
            "task_ids": {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3},
        },
        "sampling_policy": {
            "policy_id": BALANCED_SAMPLING_POLICY_ID,
            "type": "domain_balanced_weighted",
            "num_samples_per_epoch": int(len(tr)),
            "replacement": True,
            "task_id_role": "sampling_only__never_a_model_input",
            "audit": "reports/audits/phase20_sampling_policy_audit.json",
        },
        "loss": {"name": "bce_dice", "bce_weight": 0.5, "dice_weight": 0.5, "dice_epsilon": 1e-6},
        "optimizer": {"name": "AdamW", "learning_rate": 1e-4, "weight_decay": 1e-4},
        "learning_rate": 1e-4,
        "weight_decay": 1e-4,
        "scheduler": {"name": "CosineAnnealingLR", "T_max": 100,
                      "step": "per_epoch_after_train_and_val"},
        "batch_size": 4,
        "eval_batch_size": 8,
        "num_workers": 4,
        "amp": True,
        "seed": 42,
        "max_epochs": 100,
        "early_stopping": {"enabled": True, "patience": 15,
                           "ties_count_as_bad_epochs": True,
                           "check_after_checkpoint_save": True},
        "checkpoint_selection": {
            "rule_id": SELECTION_RULE_ID,
            "metric": "macro_domain_mean_validation_dice",
            "formula": "mean(Dice_ISIC, Dice_BUSI, Dice_KVASIR, Dice_KUB)",
            "per_domain_aggregation": "unweighted mean of per-image Dice within the domain",
            "tie_break": "lower validation loss",
            "not_used": ["pooled/micro pixel Dice", "KUB alone", "weighted Dice"],
            "replayed_from_disk_after_training": True,
        },
        "evaluation_metrics": {
            "per_domain_and_macro": ["dice", "iou", "precision", "recall", "specificity",
                                     "balanced_accuracy", "mcc"],
            "boundary": ["hd95", "assd", "surface_dice"],
            "calibration": ["brier", "ece", "mce"],
            "ranking": ["roc_auc", "average_precision"],
            "summary_statistics": ["mean", "median", "sd", "iqr", "bootstrap_95_ci"],
            "threshold": 0.5,
            "boundary_unit": "pixel",
            "implementation": "src.metrics.evaluation_metrics",
            "bootstrap": {"n_boot": 2000, "seed": 42, "alpha": 0.05, "unit": "image"},
        },
        "single_run_authorization": {
            "logical_runs_authorized": 1,
            "seed": 42,
            "no_architecture_alternatives": True,
            "no_post_hoc_restart_from_epoch_1": True,
            "resume_is_same_logical_run": True,
            "second_seed_belongs_to_phase_29": True,
        },
        "test_locks": {"test_image_reads": 0, "test_mask_reads": 0, "test_inference": 0,
                       "test_visualization": 0,
                       "final_test_evaluation_phase": 39,
                       "enforced_by": ["src.utils.test_lock", "src.data.loaders.create_loader",
                                       "src.data.multidomain_dataset.MultiDomainDataset"]},
        "output_isolation": {
            "experiment_dir": f"experiments/{EXPERIMENT_ID}",
            "checkpoint_dir": f"checkpoints/{EXPERIMENT_ID}",
            "overwrites_legacy_checkpoints": False,
            "overwrites_stage_a_checkpoints": False,
        },
        "code_shas": {f: sha256(ROOT / f) for f in CODE_FILES},
        "entry_conditions": {
            "phase19_authority_binding": "reports/audits/phase20_phase19_authority_binding.json",
            "entry_gate": "reports/audits/phase20_entry_gate.json",
            "duplicate_audit": "reports/audits/phase20_cross_domain_duplicate_audit.json",
            "pre_execution_check": "reports/audits/phase20_pre_execution_check.json",
        },
        "governance": {
            "training_performed": False,
            "inference_performed": False,
            "checkpoints_created": 0,
            "film_used": False,
            "regional_module_used": False,
            "localizer_used": False,
            "roi_proposal_used": False,
            "task_conditioning_used": False,
            "test_reads": 0,
        },
    }
    write_json(AUDIT_DIR / "phase20_shared_global_baseline_protocol.json", protocol)

    print("=== PHASE-20 ARCHITECTURE FREEZE ===")
    print(f"frozen: {freeze['frozen_architecture']} | basis: {freeze['selection_basis']} "
          f"| time: {freeze['selection_time']} | results_used: "
          f"{freeze['current_phase20_results_used_for_selection']}")
    print()
    print("=== SAMPLING AUDIT ===")
    for d, v in expected.items():
        e = empirical[d]
        print(f"  {d:<8} pool_share={v['dataset_share_of_pool']:.4f} -> expected="
              f"{v['expected_sampling_proportion']:.4f} empirical={e['proportion']:.4f} "
              f"({e['count']} samples)")
    print()
    print("=== PROTOCOL ===")
    print("status:", protocol["status"])
    print("experiment:", protocol["experiment_id"])
    print("code SHAs bound:", len(protocol["code_shas"]))
    for k in ("reports/audits/phase20_baseline_architecture_freeze.json",
              "reports/audits/phase20_sampling_policy_audit.json",
              "reports/audits/phase20_shared_global_baseline_protocol.json"):
        print(f"  {sha256(ROOT/k)}  {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
