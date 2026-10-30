"""Phase 25G — SUPERVISOR HOLDOUT-OWNERSHIP RULING  §15.

Additive, deterministic status sync across the six control documents plus
PHASE_INDEX.md. Preserves the historical blocked Phase25G state as provenance and
records a before/after SHA audit.

Output: reports/audits/phase25g_spec_v1_1_docs_sync.json
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
import phase25g_spec_common as C  # noqa: E402

DOCS = ["docs/ARCHITECTURE.md", "docs/DESIGN.md", "docs/MEMORY.md", "docs/PRD.md",
        "docs/RULES.md", "docs/TASKS.md", "notebooks/phasewise/PHASE_INDEX.md"]

STATUS_OLD = "Phase25G: **ELIGIBLE_NOT_STARTED**."
STATUS_NEW = ("Phase25G specification v1.1: **COMPLETE_FROZEN**; Phase25G: "
              "**EXECUTION_ELIGIBLE_NOT_STARTED** (ROUTER_DEVELOPMENT only; "
              "ROUTER_HOLDOUT RESERVED_UNOPENED_FOR_PHASE30).")

TERMINAL_ANCHOR = ("Terminal: `PHASE25F_POST_SAFETY_EXECUTION_COMPLETE__OOF_SAFETY_"
                   "PREDICTIONS_FINAL_CHECKPOINT_AND_C9_ARTIFACTS_FROZEN__"
                   "PHASE25G_ELIGIBLE_NOT_STARTED`.")

LV_OLD = ("**Last verified:** 2026-10-01 — Phase25F post-safety execution COMPLETE_CANONICAL "
          "(BARRPostSafetyV1 trained; 4957 OOF predictions; C9 artifact frozen; Phase25G ELIGIBLE_NOT_STARTED)")
LV_NEW = ("**Last verified:** 2026-10-01 — Phase25G specification v1.1 COMPLETE_FROZEN "
          "(ROUTER_HOLDOUT RESERVED_UNOPENED_FOR_PHASE30; DEV-only integrated evaluation; "
          "Phase25G EXECUTION_ELIGIBLE_NOT_STARTED)")

BLOCK = """
## Phase25G specification v1.1 — COMPLETE_FROZEN (2026-10-01)

Phase25F execution: **COMPLETE_CANONICAL**. Phase25G specification v1.1 (`ra_medfilm_barr_integrated_evaluation_v1_0`): **COMPLETE_FROZEN**; Phase25G: **EXECUTION_ELIGIBLE_NOT_STARTED** (ROUTER_DEVELOPMENT only).

**SUPERVISOR RULING (G1)**: ROUTER_HOLDOUT phase ownership = **Phase30** (Final Development Validation Benchmark), one-shot clean out-of-sample development validation. ROUTER_HOLDOUT = **RESERVED_UNOPENED_FOR_PHASE30**; it MUST NOT be opened by Phase25G, Phase26, Phase27, Phase28 or Phase29. Phase30 is the first eligible owner, subject to a separate pre-execution one-shot protocol freeze. The ruling is additive / prospective / pre-outcome (`science_changed = false`) and resolves the single Phase25G governance blocker.

Phase25G population = **ROUTER_DEVELOPMENT (4957)**; evaluation sources: Phase25C OOF delta_dice, Phase25E frozen prospective C8 memberships, Phase25F OOF S_omega probabilities/decisions and the Phase25F C9 manifest (no new model inference). The repaired completeness matrix (`phase25g_specification_completeness_v1_1.csv`) has 28 rows, `blocking_fields = []`, `hard_stop_conditions = []`; the five conditional holdout-execution fields are marked `NOT_APPLICABLE_TO_PHASE25G__HOLDOUT_RESERVED_FOR_PHASE30`.

**Blocked provenance preserved**: the pre-ruling state `PHASE25G_BLOCKED__ONE_SHOT_HOLDOUT_OWNERSHIP_UNRESOLVED` (spec `INCOMPLETE__HOLDOUT_OWNERSHIP_UNRESOLVED`, blocking field `ROUTER_HOLDOUT ownership`) and its artifacts remain verbatim (no audit or table overwritten).

Current state: Phase25F = COMPLETE_CANONICAL; Phase25G spec = COMPLETE_FROZEN; Phase25G = EXECUTION_ELIGIBLE_NOT_STARTED; ROUTER_HOLDOUT = RESERVED_UNOPENED_FOR_PHASE30; Phase30 = NOT_STARTED; VAL808 = UNOPENED / continuity benchmark; TEST = LOCKED UNTIL PHASE39.

Evidence: `reports/audits/phase25g_router_holdout_ownership_supervisor_ruling_v1_0.json`, `phase25g_holdout_reservation_for_phase30.json`, `phase25g_specification_repair_addendum.json`, `phase25g_specification_final_check_v1_1.json`, `phase25g_specification_governance_v1_1.json`, `phase25g_holdout_ownership_repair_final_check.json`, `phase30_router_holdout_deferred_contract_stub.json`.

Terminal: `PHASE25G_SPEC_V1_1_COMPLETE__ROUTER_HOLDOUT_RESERVED_FOR_PHASE30__DEV_ONLY_INTEGRATED_EVALUATION_FROZEN__PHASE25G_EXECUTION_ELIGIBLE_NOT_STARTED`.
"""

SECONDARY = {
    "notebooks/phasewise/PHASE_INDEX.md": [
        ("  phase25g_controlled_validation.ipynb                          # NOT YET CREATED",
         "  phase25g_controlled_validation.ipynb                          # NOT YET CREATED "
         "(spec v1.1 COMPLETE_FROZEN; EXECUTION_ELIGIBLE_NOT_STARTED; DEV-only)"),
    ],
}


def main() -> int:
    audit = {
        "artifact": "phase25g_spec_v1_1_docs_sync",
        "phase": "25G",
        "stage": "CONTROL_DOC_STATUS_SYNC",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "additive_only": True,
        "blocked_state_provenance_preserved": True,
        "documents": {},
        "all_pass": True,
    }
    failures = []

    for rel in DOCS:
        p = ROOT / rel
        before_sha = C.sha256_file(p)
        text = p.read_text(encoding="utf-8")
        applied = []

        if BLOCK.strip() in text:
            applied.append("already_synced")
        else:
            if STATUS_OLD in text:
                text = text.replace(STATUS_OLD, STATUS_NEW, 1)
                applied.append("status_sentence")
            else:
                failures.append(f"{rel}: status_sentence not found")

            if TERMINAL_ANCHOR in text:
                text = text.replace(TERMINAL_ANCHOR, TERMINAL_ANCHOR + "\n" + BLOCK, 1)
                applied.append("phase25g_block")
            else:
                failures.append(f"{rel}: terminal_anchor not found")

            if LV_OLD in text:
                text = text.replace(LV_OLD, LV_NEW, 1)
                applied.append("last_verified")

            for old, new in SECONDARY.get(rel, []):
                if old in text:
                    text = text.replace(old, new, 1)
                    applied.append(f"secondary:{old[:40]}")

        p.write_text(text, encoding="utf-8")
        after_sha = C.sha256_file(p)
        audit["documents"][rel] = {
            "before_sha256": before_sha,
            "after_sha256": after_sha,
            "changed": before_sha != after_sha,
            "edits_applied": applied,
        }

    # required-wording presence check
    required = [
        "Phase25G spec = COMPLETE_FROZEN",
        "RESERVED_UNOPENED_FOR_PHASE30",
        "TEST = LOCKED UNTIL PHASE39",
    ]
    presence = {}
    for rel in DOCS:
        t = (ROOT / rel).read_text(encoding="utf-8")
        presence[rel] = {k: (k in t) for k in required}
    missing = {rel: [k for k, v in d.items() if not v] for rel, d in presence.items()}
    missing = {k: v for k, v in missing.items() if v}

    audit["required_wording_presence"] = presence
    audit["required_wording_missing"] = missing
    audit["failures"] = failures
    audit["all_pass"] = (len(failures) == 0 and not missing)
    C.jdump(audit, C.AUD / "phase25g_spec_v1_1_docs_sync.json")

    print("docs synced:", sum(1 for v in audit["documents"].values() if v["changed"]), "/", len(DOCS))
    print("required wording missing:", missing)
    if failures:
        print("FAILURES:", failures)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
