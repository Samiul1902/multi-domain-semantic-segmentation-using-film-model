"""
Post-H3 supervisor gate closure + Stage-B authorization artifact.

Records the supervisor governance transition that closes the H3 target-support
branch, defers the regional-mechanism phases (15-18), and authorizes the main
multi-domain program to begin at Phase 19.

This is a one-time decision record. It is generated once and then read (not
regenerated) by the Phase-19 notebook, so its SHA-256 stays a stable binding.

Run:
    D:\\Softfors\\jup\\.venv\\Scripts\\python.exe scripts/audits/build_stage_b_authorization.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

H3_ADJ = ROOT / "reports/audits/h3_formal_adjudication.json"
H3_GOV = ROOT / "reports/audits/h3_post_adjudication_governance_state.json"
OUT = ROOT / "reports/audits/stage_b_phase19_authorization.json"


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    adj = json.loads(H3_ADJ.read_text(encoding="utf-8"))

    # ---- FAIL CLOSED: verify the authoritative H3 state before changing governance
    expected_label = "H3_SUPPLY_REDESIGN_INSUFFICIENT"
    checks = {
        "scientific_label": adj["scientific_label"] == expected_label,
        "zero_proposal_tiny": adj["observed"]["zero_proposal_tiny_fraction"] == "22/72",
        "zero_proposal_gt": adj["observed"]["zero_proposal_gt_fraction"] == "27/152",
        "formal_TinyRecall_H3": adj["observed"]["formal_TinyRecall_H3_fraction"] == "59/72",
        "formal_R_H3": adj["observed"]["formal_R_H3_fraction"] == "2/15",
        "failure_boundary_fired": bool(adj["failure_boundary"]["fired"]),
        "selected_epoch_54": int(adj["selected_checkpoint"]["selected_epoch"]) == 54,
        "replay_pass": adj["checkpoint_selection_replay_verdict"] == "H3_CHECKPOINT_SELECTION_REPLAY_PASS",
        "test_reads_zero": int(adj["governance"]["test_reads"]) == 0,
    }
    if not all(checks.values()):
        failed = [k for k, v in checks.items() if not v]
        raise SystemExit(f"FAIL CLOSED — H3 adjudication state contradicts expectations: {failed}")
    print("H3 closure verification: PASS (9/9 checks)")

    gov = json.loads(H3_GOV.read_text(encoding="utf-8"))

    payload = {
        "artifact": "stage_b_phase19_authorization",
        "artifact_version": "v1",
        "status": "STAGE_B_AUTHORIZED__PHASE19_READY_TO_START",
        "decision_type": "SUPERVISOR_GOVERNANCE_TRANSITION",
        "decision_timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),

        "REGIONAL_BRANCH_SUPERVISOR_DECISION": {
            "CURRENT_H3_INTERVENTION": "CLOSED__FORMALLY_INSUFFICIENT",
            "REGIONAL_HYPOTHESIS": "PRESERVED_AS_DIAGNOSTICALLY_SUPPORTED_BY_ORACLE_BUT_NOT_DEPLOYABLY_RESOLVED",
            "PREDICTED_LOCALIZATION": "INSUFFICIENT_FOR_PROMOTION",
            "REGIONAL_MECHANISM": "NOT_PROMOTED_TO_MAIN_ARCHITECTURE_AT_THIS_TIME",
            "OPTION_B": "DEFERRED__NOT_AUTHORIZED",
            "OPTION_C": "DEFERRED__NOT_AUTHORIZED",
            "PHASE_15": "DEFERRED_CONDITIONAL__NOT_EXECUTED",
            "PHASE_16": "DEFERRED_CONDITIONAL__NOT_EXECUTED",
            "PHASE_17": "DEFERRED_CONDITIONAL__NOT_EXECUTED",
            "PHASE_18": "DEFERRED_CONDITIONAL__NOT_EXECUTED",
            "PHASE_19": "AUTHORIZED_TO_START",
            "TEST": "CLOSED",
        },
        "decision_interpretation_guardrails": {
            "is_not": [
                "regional hypothesis disproved",
                "Phase 15 completed",
                "Phase 15 failed",
                "Phases 16-18 completed",
                "H3 success",
            ],
            "is": "a deliberate supervisor decision to stop the unresolved localizer branch from "
                  "blocking the main multi-domain research program",
        },

        "h3_adjudication_binding": {
            "path": "reports/audits/h3_formal_adjudication.json",
            "sha256": sha256_file(H3_ADJ),
            "scientific_label": adj["scientific_label"],
            "governance_wrapper": adj["status"],
            "formal_values": {
                "zero_proposal_TINY": adj["observed"]["zero_proposal_tiny_fraction"],
                "zero_proposal_GT": adj["observed"]["zero_proposal_gt_fraction"],
                "formal_TinyRecall_H3": adj["observed"]["formal_TinyRecall_H3_fraction"],
                "formal_R_H3": adj["observed"]["formal_R_H3_fraction"],
                "failure_boundary": "FIRED",
                "selected_epoch": int(adj["selected_checkpoint"]["selected_epoch"]),
                "checkpoint_selection_replay": adj["checkpoint_selection_replay_verdict"],
                "test_reads": int(adj["governance"]["test_reads"]),
            },
            "verification": {"all_checks_passed": True, "checks": checks, "fail_closed": True},
        },
        "h3_governance_state_binding": {
            "path": "reports/audits/h3_post_adjudication_governance_state.json",
            "sha256": sha256_file(H3_GOV),
            "status": gov["status"],
        },

        "regional_evidence_preserved": {
            "status": "DEFERRED__NOT_PROMOTED",
            "explicitly_not": ["ERASED", "SUCCESSFULLY_INTEGRATED"],
            "preserved_evidence": [
                "Phase 12 Oracle regional-resolution benefit",
                "Phase 14 Oracle regional-refiner benefit",
                "Phase 13 predicted-localization limitations",
                "post-Phase14 root-cause analysis",
                "H3 supply improvement",
                "H3 downstream insufficiency",
                "H3 formal adjudication",
            ],
            "correct_summary": (
                "Oracle regional processing shows potential, but the current GT-free predicted "
                "localization path does not preserve enough practical benefit."
            ),
        },

        "deferred_phases_roadmap_preserved": {
            "renumbered": False,
            "deleted": False,
            "phase_15": {"title": "Regional Objective / Loss Study",
                         "scientific_execution": "NOT_EXECUTED",
                         "roadmap_status": "DEFERRED_CONDITIONAL_AFTER_H3_INSUFFICIENCY"},
            "phase_16": {"title": "Global-Regional Fusion / Routing",
                         "scientific_execution": "NOT_EXECUTED",
                         "roadmap_status": "DEFERRED_CONDITIONAL_AFTER_H3_INSUFFICIENCY"},
            "phase_17": {"title": "Regional Mechanism Ablation",
                         "scientific_execution": "NOT_EXECUTED",
                         "roadmap_status": "DEFERRED_CONDITIONAL_AFTER_H3_INSUFFICIENCY"},
            "phase_18": {"title": "Regional Mechanism Freeze",
                         "scientific_execution": "NOT_EXECUTED",
                         "roadmap_status": "DEFERRED_CONDITIONAL_AFTER_H3_INSUFFICIENCY"},
        },

        "stage_b_activation": {
            "stage": "Stage B: Multi-Domain Scaling",
            "active": True,
            "canonical_sequence": [
                {"phase": 19, "title": "Multi-Domain Dataset Harmonization", "authorized_by_this_task": True},
                {"phase": 20, "title": "Shared Multi-Domain Global Baseline", "authorized_by_this_task": False},
                {"phase": 21, "title": "Global MedFiLM Reference", "authorized_by_this_task": False},
                {"phase": 22, "title": "Multi-Domain Scale / Regional Gap Analysis", "authorized_by_this_task": False},
                {"phase": 23, "title": "Literature & Methodological Novelty Audit", "authorized_by_this_task": False},
                {"phase": 24, "title": "RA-MedFiLM-Seg++ Architecture Specification", "authorized_by_this_task": False},
                {"phase": 25, "title": "Controlled RA-MedFiLM Module Development", "authorized_by_this_task": False},
                {"phase": 26, "title": "Full Four-Domain RA-MedFiLM-Seg++ Training", "authorized_by_this_task": False},
            ],
        },

        "phase19_authorization": {
            "phase_id": "19",
            "title": "Multi-Domain Dataset Harmonization (ISIC, BUSI, Kvasir, KUB)",
            "status": "AUTHORIZED_TO_START",
            "scientific_purpose": "MULTI-DOMAIN DATASET HARMONIZATION",
            "primary_question": (
                "Can ISIC, BUSI, Kvasir and KUB be represented under one clean, deployment-valid, "
                "leakage-safe task/data contract suitable for later shared multi-domain training?"
            ),
            "is_model_training_phase": False,
            "training_authorized": False,
            "notebook": "notebooks/phasewise/phase_19_harmonization/phase19_multidomain_dataset_harmonization.ipynb",
            "protocol": "reports/audits/phase19_multidomain_harmonization_protocol.json",
        },

        "locks": {
            "test_lock": {
                "status": "CLOSED",
                "test_image_reads": 0, "test_mask_reads": 0,
                "test_inference": 0, "test_visualization": 0,
                "phase39_lock_weakened": False,
            },
            "external_test_lock": {"status": "CLOSED", "external_test_reads": 0},
            "future_phase_locks": {
                "phase_20": "NOT_STARTED_AND_NOT_AUTHORIZED",
                "phase_21": "NOT_STARTED_AND_NOT_AUTHORIZED",
                "phase_22": "NOT_STARTED_AND_NOT_AUTHORIZED",
                "phase_23": "NOT_STARTED_AND_NOT_AUTHORIZED",
                "phase_24": "NOT_STARTED_AND_NOT_AUTHORIZED",
                "phase_25": "NOT_STARTED_AND_NOT_AUTHORIZED",
                "phase_26": "NOT_STARTED_AND_NOT_AUTHORIZED",
            },
            "option_b": "DEFERRED__NOT_AUTHORIZED",
            "option_c": "DEFERRED__NOT_AUTHORIZED",
        },

        "execution_attestation": {
            "training_performed": False,
            "inference_performed": False,
            "optimizer_created": False,
            "backward_performed": False,
            "checkpoints_created": 0,
            "thresholds_changed": 0,
            "frozen_historical_artifacts_modified": 0,
            "test_reads": 0,
            "external_test_reads": 0,
            "phase_20_started": False,
            "medfilm_trained": False,
            "literature_search_performed": False,
        },

        "next_authorized_action": (
            "Execute Phase 19 (multi-domain dataset harmonization) — protocol and notebook "
            "preparation are complete; Phase-19 scientific execution/training remains gated on "
            "explicit supervisor authorization for model training."
        ),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"  sha256: {sha256_file(OUT)}")
    print(f"  status: {payload['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
