"""Phase 25F — POST-SAFETY SPECIFICATION REPAIR  §33.

Additive, deterministic status sync across the six control documents plus
PHASE_INDEX.md. Preserves the blocked-attempt provenance statement and records a
before/after SHA audit.

Output: reports/audits/phase25f_spec_repair_docs_sync.json
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
import phase25f_spec_repair_common as C  # noqa: E402

DOCS = ["docs/ARCHITECTURE.md", "docs/DESIGN.md", "docs/MEMORY.md", "docs/PRD.md",
        "docs/RULES.md", "docs/TASKS.md", "notebooks/phasewise/PHASE_INDEX.md"]

STATUS_OLD = "Phase25F: **NOT_STARTED**. Phase25G: **NOT_STARTED**."
STATUS_NEW = ("Phase25F post-safety specification v1.0 (`ra_medfilm_barr_post_safety_v1_0`): "
              "**COMPLETE_FROZEN** (execution **EXECUTION_ELIGIBLE_NOT_STARTED**). "
              "Phase25G: **NOT_STARTED**.")

LV_OLD = "**Last verified:** 2026-10-01 — Phase25E scientific policy evaluation COMPLETE_FROZEN"
LV_NEW = ("**Last verified:** 2026-10-01 — Phase25F post-safety specification v1.0 COMPLETE_FROZEN "
          "(Phase25E policy evaluation complete)")

TERMINAL_ANCHOR = ("Terminal: `PHASE25E_RESOURCE_GATE_POLICY_EVALUATION_COMPLETE__OOF_FIXED_BUDGET_"
                   "FRONTIER_AND_FINAL_DEV_THRESHOLDS_FROZEN__PHASE25F_ELIGIBLE_NOT_STARTED`.")

PHASE25F_BLOCK = """
## Phase25F post-safety specification v1.0 — COMPLETE_FROZEN (2026-10-01)

Phase25F post-safety specification (`ra_medfilm_barr_post_safety_v1_0`): **COMPLETE_FROZEN**; Phase25F execution: **EXECUTION_ELIGIBLE_NOT_STARTED**. The first blocked Phase25F attempt (`PHASE25F_BLOCKED__POST_SAFETY_EXECUTION_SPEC_INCOMPLETE`; 54 blocking fields, 12 hard-stop conditions) is preserved verbatim as **BLOCKED_ATTEMPT_PROVENANCE** (no audit overwritten or deleted).

The repair prospectively froze the exact S_omega input vector (20-D = 16 numeric + 4 one-hot task), the leakage-safe OOF post-refinement source (Phase25C fold-specific `_tmp_refined_crop_prob_<DOMAIN>.npy`, provenance-proven and promoted to `data_cache/phase25f_barr_post_safety_v1_0/oof_refined_crop_prob.npy`), `BARRPostSafetyV1` (`Linear(20,32)->SiLU->Linear(32,16)->SiLU->Linear(16,1)`, **1,217** trainable parameters, raw logit output), the training objective (`BCEWithLogitsLoss`, mean reduction, no class weighting / pos_weight / label smoothing), the reused Phase25D five-fold CV identity manifests (FIT / EARLY_STOP / OUTER_TARGET), FIT-only ddof=0 normalization of the 16 numeric features, the fixed ACCEPT/FALLBACK threshold (`sigmoid >= 0.50` / `logit >= 0.0`; distinct from the 0.30 ROI-proposal and 0.50 segmentation-output thresholds), the Phase25E SKIP interaction state machine, the final-refit rule (exact median of the five best epochs, seed 42, LAST_FIXED_EPOCH checkpoint), and A7/A8 ownership (Phase25F constructs the C9 artifact on ROUTER_DEVELOPMENT; Phase25G owns the integrated A7-vs-A8 / C8-vs-C9 evaluation).

All 73 specification fields are now complete; `blocking_fields = []` and `hard_stop_conditions_triggered = []`. **No model was constructed, no training ran, no forward pass occurred, no refinement or DeltaDice was regenerated, and no threshold was tuned.** ROUTER_HOLDOUT, VAL808 and TEST remain closed; Phase25G is NOT_STARTED.

Evidence: `reports/audits/phase25f_post_safety_spec_completion_v1_0.json`, `phase25f_oof_refinement_source_contract_v1_0.json`, `phase25f_oof_refinement_source_promotion.json`, `phase25f_feature_equation_contract_v1_0.json`, `phase25f_feature_cache_determinism.json`, `phase25f_target_contract_v1_0.json`, `phase25f_architecture_contract_v1_0.json`, `phase25f_training_contract_v1_0.json`, `phase25f_decision_threshold_contract_v1_0.json`, `phase25f_state_machine_contract_v1_0.json`, `phase25f_final_refit_contract_v1_0.json`, `phase25f_a7_a8_ownership_ruling_v1_0.json`, `phase25f_spec_repair_no_execution.json`, `phase25f_spec_repair_final_check.json`.

Terminal: `PHASE25F_POST_SAFETY_SPEC_V1_0_COMPLETE__OOF_FEATURE_SOURCE_ARCHITECTURE_TRAINING_THRESHOLD_AND_OWNERSHIP_FROZEN__PHASE25F_EXECUTION_ELIGIBLE_NOT_STARTED`.
"""

SECONDARY = {
    "docs/MEMORY.md": [
        ("Phase 25F is `NOT_STARTED`.",
         "Phase 25F post-safety specification v1.0 is `COMPLETE_FROZEN`; Phase 25F execution is "
         "`EXECUTION_ELIGIBLE_NOT_STARTED`."),
        ("Phase 25F–25G NOT_STARTED",
         "Phase 25F post-safety specification COMPLETE_FROZEN (execution EXECUTION_ELIGIBLE_NOT_STARTED); "
         "Phase 25G NOT_STARTED"),
    ],
    "docs/TASKS.md": [
        ("**Phase 25F NOT_STARTED.**",
         "**Phase 25F post-safety specification v1.0 COMPLETE_FROZEN; execution "
         "EXECUTION_ELIGIBLE_NOT_STARTED.**"),
        ("| 25F | Post-safety + fusion | **NOT_STARTED** |",
         "| 25F | Post-safety + fusion | Specification **COMPLETE_FROZEN**; execution "
         "**EXECUTION_ELIGIBLE_NOT_STARTED** |"),
    ],
    "docs/RULES.md": [
        ("- **Phase25F = NOT_STARTED**.",
         "- **Phase25F = EXECUTION_ELIGIBLE_NOT_STARTED** (post-safety specification v1.0 "
         "`ra_medfilm_barr_post_safety_v1_0` COMPLETE_FROZEN)."),
        ("**Last verified:** 2026-10-01 — Phase25D COMPLETE canonical;\n"
         "Phase25E policy evaluation COMPLETE_FROZEN",
         "**Last verified:** 2026-10-01 — Phase25D COMPLETE canonical;\n"
         "Phase25E policy evaluation COMPLETE_FROZEN;\n"
         "Phase25F post-safety specification v1.0 COMPLETE_FROZEN"),
    ],
    "notebooks/phasewise/PHASE_INDEX.md": [
        ("  phase25f_post_safety_and_fusion.ipynb                         # NOT YET CREATED",
         "  phase25f_post_safety_and_fusion.ipynb                         # NOT YET CREATED "
         "(spec v1.0 COMPLETE_FROZEN; execution EXECUTION_ELIGIBLE_NOT_STARTED)"),
    ],
}


def main() -> int:
    audit = {
        "artifact": "phase25f_spec_repair_docs_sync",
        "phase": "25F",
        "stage": "CONTROL_DOC_STATUS_SYNC",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "additive_only": True,
        "blocked_attempt_provenance_preserved": True,
        "documents": {},
        "all_pass": True,
    }
    failures = []

    for rel in DOCS:
        p = ROOT / rel
        before_sha = C.sha256_file(p)
        text = p.read_text(encoding="utf-8")
        applied = []

        # A1 status sentence
        if STATUS_OLD in text:
            text = text.replace(STATUS_OLD, STATUS_NEW, 1)
            applied.append("status_sentence")
        else:
            failures.append(f"{rel}: status_sentence not found")

        # A2 Phase25F block after the Phase25E terminal line
        if TERMINAL_ANCHOR in text:
            text = text.replace(TERMINAL_ANCHOR, TERMINAL_ANCHOR + "\n" + PHASE25F_BLOCK, 1)
            applied.append("phase25f_block")
        else:
            failures.append(f"{rel}: terminal_anchor not found")

        # A3 last-verified
        if LV_OLD in text:
            text = text.replace(LV_OLD, LV_NEW, 1)
            applied.append("last_verified")

        # A4 doc-specific secondary
        for old, new in SECONDARY.get(rel, []):
            if old in text:
                text = text.replace(old, new, 1)
                applied.append(f"secondary:{old[:40]}")
            else:
                failures.append(f"{rel}: secondary not found: {old[:60]!r}")

        p.write_text(text, encoding="utf-8")
        after_sha = C.sha256_file(p)
        audit["documents"][rel] = {
            "before_sha256": before_sha,
            "after_sha256": after_sha,
            "changed": before_sha != after_sha,
            "edits_applied": applied,
        }

    # residual stale-marker scan
    stale_markers = ["Phase25F: **NOT_STARTED**", "**Phase25F = NOT_STARTED**",
                     "Phase 25F is `NOT_STARTED`"]
    residual = {}
    for rel in DOCS:
        t = (ROOT / rel).read_text(encoding="utf-8")
        hits = [m for m in stale_markers if m in t]
        if hits:
            residual[rel] = hits

    audit["residual_stale_markers"] = residual
    audit["residual_stale_marker_count"] = sum(len(v) for v in residual.values())
    audit["failures"] = failures
    audit["all_pass"] = (len(failures) == 0 and not residual)
    C.jdump(audit, C.AUD / "phase25f_spec_repair_docs_sync.json")

    print("docs synced:", sum(1 for v in audit["documents"].values() if v["changed"]), "/", len(DOCS))
    print("residual stale markers:", audit["residual_stale_marker_count"])
    if failures:
        print("FAILURES:", failures)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
