"""Phase-20 legacy tested-project baseline evidence audit.

Documents the historical conventional segmentation baselines that actually exist
in the user's tested projects, so the Phase-20 architecture is chosen from
EVIDENCE rather than from preference. Every historical number is labelled

    LEGACY_PRIOR_EVIDENCE__NOT_CURRENT_PHASE20_RESULT

and must never be compared numerically against Phase-20 results.

Writes
------
reports/audits/phase20_legacy_baseline_selection_evidence.json
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
AUDIT_DIR = ROOT / "reports/audits"
LEGACY = Path(r"D:/Softfors")

LABEL = "LEGACY_PRIOR_EVIDENCE__NOT_CURRENT_PHASE20_RESULT"


def sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def main() -> int:
    # ---- A. Same-repository clean-v3 conventional architecture comparison ----
    # Phase 9 / Phase 10 ran ONE identical protocol over four conventional
    # architectures on clean-v3 KUB. This is the single most transferable piece
    # of architecture evidence in the repository because the protocol, manifest
    # version, resolution, loss, optimizer and selection metric are held fixed.
    kub_comparison = [
        {"architecture": "U-Net", "experiment_id": "phase9_kub_unet_baseline_seed42_512_clean_v3",
         "params": 7763041, "best_epoch": 44, "best_val_macro_dice": 0.7406133413314819,
         "final_epoch": 59, "stop_reason": "EARLY_STOP",
         "history_sha256": "7678a5822542cd356f85e9c153da460a87e58d85e7cd1221d8fb66e323f60217",
         "best_checkpoint_sha256": "7b955ba86464a2fec2d569ecb6124de1fa9a4e66d0b5d58b267be9a280b4c2c0"},
        {"architecture": "Attention U-Net", "experiment_id": "phase10_kub_attention_unet_seed42_512_clean_v3",
         "params": 7851285, "best_epoch": 54, "best_val_macro_dice": 0.7525129853960107,
         "final_epoch": 69, "stop_reason": "EARLY_STOP",
         "history_sha256": "ee5073f0bea745280ae7d9a8f651cc4cae72a18d408750623d838f7cd8d24e58",
         "best_checkpoint_sha256": "a49b19d66e43b57ed082ea6efc0ac10bccf444277abd3540dc68612bf30b88b3"},
        {"architecture": "UNet++", "experiment_id": "phase10_kub_unetpp_seed42_512_clean_v3",
         "params": 9159681, "best_epoch": 70, "best_val_macro_dice": 0.7641595156062713,
         "final_epoch": 85, "stop_reason": "EARLY_STOP",
         "history_sha256": "a733d8366278d2ddb1a44db0d94ff7525fb9b10afefba787abfd036c1fb1de5a",
         "best_checkpoint_sha256": "ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269"},
        {"architecture": "DeepLabV3+ (ResNet-50, no pretrained weights)",
         "experiment_id": "phase10_kub_deeplabv3plus_seed42_512_clean_v3",
         "params": 40347041, "best_epoch": 52, "best_val_macro_dice": 0.7509140344161673,
         "final_epoch": 67, "stop_reason": "EARLY_STOP",
         "history_sha256": "9c3a4611f0f38b474aa18537b0509bf9a4cb539baf077e6ba12c7880a73cd01f",
         "best_checkpoint_sha256": "f519027ba1a3a4d6212d83fecd4379f61f71bc05b0751924b9660da08d597dad"},
    ]
    best = max(kub_comparison, key=lambda r: r["best_val_macro_dice"])

    # ---- B. Legacy multi-domain projects -----------------------------------
    legacy_projects = [
        {
            "project": "final/medfilm_seg",
            "source": str(LEGACY / "final/medfilm_seg"),
            "domains": ["ISIC 2018", "BUSI", "Kvasir-SEG"],
            "domain_count": 3,
            "includes_kub": False,
            "task_ids": {"isic2018": 0, "busi": 1, "kvasir": 2},
            "shared_model": True,
            "baselines": ["unet", "attention_unet"],
            "proposed": "medfilm_seg",
            "historical_protocol": {
                "image_size": 256, "batch_size": 8, "optimizer": "AdamW",
                "learning_rate": 0.0003, "weight_decay": 0.0001,
                "scheduler": "CosineAnnealingLR", "mixed_precision": True,
                "early_stopping_patience": 12, "seed": 42,
                "threshold": "tuned (final selected 0.70)",
            },
            "historical_validation_result": {
                "U-Net": {"dice": 0.8453, "iou": 0.7321},
                "Attention U-Net": {"dice": 0.848794, "iou": 0.737309},
                "MedFiLM-Seg": {"dice": 0.866204, "iou": 0.763986},
                "MedFiLM-Seg Calibrated": {"dice": 0.87187, "iou": 0.772845},
                "datasetwise_medfilm": {"BUSI": 0.879813, "ISIC 2018": 0.873109,
                                        "Kvasir-SEG": 0.853746},
                "provenance": "final/medfilm_seg/reports/docx_result_report_generated/tables/"
                              "normalized_overall_model_comparison.csv",
            },
            "implementation_availability": "PARTIAL — the legacy src/models tree is empty on disk "
                                            "(cleaned); only result tables survive",
            "known_stability": "Reported as stable; superseded pipeline",
            "known_failure_mode": "Threshold-tuned final numbers; not comparable to a fixed "
                                  "0.5-threshold clean-v3 protocol",
            "reuse_recommendation": "REFERENCE_ONLY for hyperparameter shape; hyperparameters are "
                                    "explicitly NOT adopted (see phase19_legacy_evidence_reuse_map)",
            "evidence_label": LABEL,
        },
        {
            "project": "final/medfilm_seg_v2",
            "source": str(LEGACY / "final/medfilm_seg_v2"),
            "domains": ["ISIC 2018", "BUSI", "Kvasir-SEG"],
            "domain_count": 3,
            "includes_kub": False,
            "shared_model": True,
            "baselines": ["plain_weak_segmentation", "attention_unet_weak_segmentation",
                          "baseline_cam_classifier"],
            "historical_protocol": {"image_size": 384, "label_regime": "weak / CAM-seeded"},
            "historical_validation_result": {"note": "Weak-label pipeline; results not transferable "
                                                     "to a fully supervised mask contract"},
            "implementation_availability": "YES — final/medfilm_seg_v2/src_v2/models_v2/"
                                           "attention_unet_weak_segmentation_v2.py",
            "known_stability": "Stable",
            "known_failure_mode": "Sparse 0/1..254/255 weak-label encoding would corrupt the "
                                  "current full-mask contract",
            "reuse_recommendation": "DO_NOT_REUSE (Phase-19 legacy reuse map: scientific_risk HIGH)",
            "evidence_label": LABEL,
        },
        {
            "project": "Omni_segv2",
            "source": str(LEGACY / "Omni_segv2"),
            "domains": ["brats", "busi", "isic", "kits", "kvasir"],
            "domain_count": 5,
            "includes_kub": False,
            "shared_model": True,
            "baselines": ["multi-domain 2.5D/3D stream"],
            "historical_protocol": {"note": "2.5D-3D volumetric stream; different task set"},
            "historical_validation_result": {"note": "Different domain set and stream geometry; "
                                                     "no transferable per-domain 2D Dice"},
            "implementation_availability": "REFERENCE_ONLY",
            "known_stability": "Unknown for a 2D four-domain contract",
            "known_failure_mode": "Architecture targets volumetric input",
            "reuse_recommendation": "REFERENCE_ONLY (naming/modality vocabulary only)",
            "evidence_label": LABEL,
        },
        {
            "project": "safeseg",
            "source": str(LEGACY / "safeseg"),
            "domains": ["isic2018", "kits23", "mms", "montgomery"],
            "domain_count": 4,
            "includes_kub": False,
            "shared_model": True,
            "baselines": ["notebook-level experiments"],
            "historical_protocol": {"note": "Different domain set; no reusable code path"},
            "historical_validation_result": {"note": "Prior evidence only that one model can span "
                                                     "multiple medical domains"},
            "implementation_availability": "REFERENCE_ONLY",
            "known_stability": "Unknown",
            "known_failure_mode": "Domain set differs; not a KUB-bearing four-domain baseline",
            "reuse_recommendation": "REFERENCE_ONLY",
            "evidence_label": LABEL,
        },
    ]

    # ---- C. Architecture coverage matrix -----------------------------------
    coverage = [
        {"architecture": "U-Net", "repository_implementation": "src/models/unet.py",
         "factory_key": "unet", "params_at_base32_3ch": 7763041,
         "historical_four_domain_shared_model": False,
         "historical_clean_v3_kub": True, "binary_segmentation_compatible": True,
         "reuse_recommendation": "AVAILABLE_AS_ALTERNATIVE"},
        {"architecture": "Attention U-Net", "repository_implementation": "src/models/attention_unet.py",
         "factory_key": "attention_unet", "params_at_base32_3ch": 7851285,
         "historical_four_domain_shared_model": False,
         "historical_clean_v3_kub": True, "binary_segmentation_compatible": True,
         "reuse_recommendation": "AVAILABLE_AS_ALTERNATIVE"},
        {"architecture": "UNet++", "repository_implementation": "src/models/unetpp.py",
         "factory_key": "unetpp", "params_at_base32_3ch": 9159681,
         "historical_four_domain_shared_model": False,
         "historical_clean_v3_kub": True, "binary_segmentation_compatible": True,
         "reuse_recommendation": "SELECTED"},
        {"architecture": "DeepLabV3+", "repository_implementation": "src/models/deeplabv3plus.py",
         "factory_key": "deeplabv3plus", "params_at_base32_3ch": 40347041,
         "historical_four_domain_shared_model": False,
         "historical_clean_v3_kub": True, "binary_segmentation_compatible": True,
         "reuse_recommendation": "AVAILABLE_AS_ALTERNATIVE"},
        {"architecture": "Transformer / MiT-style U-Net",
         "repository_implementation": None, "factory_key": None,
         "params_at_base32_3ch": None,
         "historical_four_domain_shared_model": False,
         "historical_clean_v3_kub": False, "binary_segmentation_compatible": True,
         "reuse_recommendation": "NOT_IMPLEMENTED__NOT_A_CANDIDATE"},
    ]

    payload = {
        "artifact": "phase20_legacy_baseline_selection_evidence",
        "phase": "20",
        "evidence_label": LABEL,
        "policy": {
            "purpose": "Choose ONE Phase-20 architecture from prior evidence instead of repeating a "
                       "five-model sweep.",
            "historical_numbers_are_current_phase20_results": False,
            "historical_numbers_may_be_compared_to_phase20_results": False,
            "comparison_boundary": "Historical values are context for the CHOICE only. Phase-20 "
                                   "numbers stand alone and are never benchmarked against them.",
        },
        "finding_no_legacy_four_domain_shared_baseline": {
            "searched_projects": [p["project"] for p in legacy_projects],
            "kub_bearing_shared_baseline_found": False,
            "statement": "No legacy tested project trained a single shared model across a "
                         "KUB-bearing four-domain pool. The legacy shared multi-domain baselines "
                         "are three-domain (ISIC/BUSI/Kvasir) at 256 px (medfilm_seg) or "
                         "weak-label at 384 px (medfilm_seg_v2, DO_NOT_REUSE).",
            "consequence": "The architecture decision therefore rests on the same-repository "
                           "clean-v3 conventional comparison below, which holds the protocol fixed.",
        },
        "same_repository_clean_v3_conventional_comparison": {
            "scope": "KUB only, phase4_v3, 512 px, identical loss/optimizer/scheduler/selection "
                     "protocol across all four architectures",
            "evidence_label": LABEL,
            "results": kub_comparison,
            "ranking_by_best_val_macro_dice": [
                r["architecture"] for r in
                sorted(kub_comparison, key=lambda x: -x["best_val_macro_dice"])],
            "strongest": best["architecture"],
            "strongest_value": best["best_val_macro_dice"],
            "margin_over_next": round(best["best_val_macro_dice"] -
                                      sorted(kub_comparison, key=lambda x: -x["best_val_macro_dice"])[1]["best_val_macro_dice"], 8),
            "provenance": "reports/tables/phase10_*_clean_v3_best_val_summary.csv; "
                          "reports/audits/phase10_clean_v3_final_comparison_audit.json",
        },
        "legacy_projects": legacy_projects,
        "architecture_coverage_matrix": coverage,
        "selection_conclusion": {
            "selected_architecture": "UNet++",
            "reason": "Strongest conventional clean-v3 architecture in this repository under a "
                      "fixed protocol; already implemented and tested; binary-segmentation "
                      "compatible; requires no FiLM and no regional module.",
            "evidence": "same_repository_clean_v3_conventional_comparison",
            "selection_basis": "LEGACY_TESTED_PROJECT_PRIOR_EVIDENCE",
            "no_five_model_sweep_in_phase20": True,
        },
        "artifact_shas": {
            "reports/audits/phase10_clean_v3_final_comparison_audit.json":
                sha256(ROOT / "reports/audits/phase10_clean_v3_final_comparison_audit.json"),
            "reports/tables/phase09_clean_v3_best_val_summary.csv":
                sha256(ROOT / "reports/tables/phase09_clean_v3_best_val_summary.csv"),
            "reports/tables/phase10_unetpp_clean_v3_best_val_summary.csv":
                sha256(ROOT / "reports/tables/phase10_unetpp_clean_v3_best_val_summary.csv"),
            "reports/tables/phase10_attention_unet_clean_v3_best_val_summary.csv":
                sha256(ROOT / "reports/tables/phase10_attention_unet_clean_v3_best_val_summary.csv"),
            "reports/tables/phase10_deeplabv3plus_clean_v3_best_val_summary.csv":
                sha256(ROOT / "reports/tables/phase10_deeplabv3plus_clean_v3_best_val_summary.csv"),
        },
    }
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    out = AUDIT_DIR / "phase20_legacy_baseline_selection_evidence.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("=== LEGACY BASELINE EVIDENCE ===")
    print(f"label: {LABEL}")
    print(f"legacy KUB-bearing shared baseline found: "
          f"{payload['finding_no_legacy_four_domain_shared_baseline']['kub_bearing_shared_baseline_found']}")
    for r in kub_comparison:
        print(f"  {r['architecture']:<44} dice={r['best_val_macro_dice']:.6f} epoch={r['best_epoch']}")
    print(f"strongest: {best['architecture']} ({best['best_val_macro_dice']:.6f})")
    print(f"selected: {payload['selection_conclusion']['selected_architecture']}")
    print("artifact:", out.relative_to(ROOT), "| sha256:",
          hashlib.sha256(out.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
