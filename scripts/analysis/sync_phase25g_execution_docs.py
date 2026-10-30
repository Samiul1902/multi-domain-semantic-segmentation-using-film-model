"""Phase25G §43 - project status sync after successful integrated evaluation.

Additive, idempotent.  Sets Phase25A-25G = COMPLETE_CANONICAL, Phase25 = COMPLETE_CANONICAL,
Phase26 = ELIGIBLE_NOT_STARTED, ROUTER_HOLDOUT = RESERVED_UNOPENED_FOR_PHASE30, Phase30 = NOT_STARTED,
TEST = LOCKED UNTIL PHASE39; records the Phase25G notebook SHA in PHASE_INDEX and the immutability list.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
import phase25g_common as C  # noqa: E402

DOCS = ["docs/ARCHITECTURE.md", "docs/DESIGN.md", "docs/MEMORY.md", "docs/PRD.md",
        "docs/RULES.md", "docs/TASKS.md", "notebooks/phasewise/PHASE_INDEX.md"]

NB = C.NB_DIR / "phase25g_integrated_controlled_evaluation.ipynb"
NB_SHA = C.sha256_file(NB)

R1_OLD = ("Phase25G specification v1.1: **COMPLETE_FROZEN**; Phase25G: "
          "**EXECUTION_ELIGIBLE_NOT_STARTED** (ROUTER_DEVELOPMENT only; "
          "ROUTER_HOLDOUT RESERVED_UNOPENED_FOR_PHASE30).")
R1_NEW = ("Phase25G specification v1.1: **COMPLETE_FROZEN**; Phase25G: **COMPLETE_CANONICAL** "
          "(ROUTER_DEVELOPMENT only; ROUTER_HOLDOUT RESERVED_UNOPENED_FOR_PHASE30). "
          "**Phase25 = COMPLETE_CANONICAL**; Phase26 = **ELIGIBLE_NOT_STARTED**.")

R2_OLD = "Phase25G: **EXECUTION_ELIGIBLE_NOT_STARTED** (ROUTER_DEVELOPMENT only)."
R2_NEW = "Phase25G: **COMPLETE_CANONICAL** (ROUTER_DEVELOPMENT only)."

R3_OLD = ("Current state: Phase25F = COMPLETE_CANONICAL; Phase25G spec = COMPLETE_FROZEN; "
          "Phase25G = EXECUTION_ELIGIBLE_NOT_STARTED; ROUTER_HOLDOUT = RESERVED_UNOPENED_FOR_PHASE30; "
          "Phase30 = NOT_STARTED; VAL808 = UNOPENED / continuity benchmark; "
          "TEST = LOCKED UNTIL PHASE39.")
R3_NEW = ("Current state: **Phase25 = COMPLETE_CANONICAL (25A-25G)**; Phase26 = ELIGIBLE_NOT_STARTED; "
          "ROUTER_HOLDOUT = RESERVED_UNOPENED_FOR_PHASE30; Phase30 = NOT_STARTED; "
          "VAL808 = UNOPENED / continuity benchmark; TEST = LOCKED UNTIL PHASE39.")

LV_OLD = ("**Last verified:** 2026-10-01 — Phase25G specification v1.1 COMPLETE_FROZEN "
          "(ROUTER_HOLDOUT RESERVED_UNOPENED_FOR_PHASE30; DEV-only integrated evaluation; "
          "Phase25G EXECUTION_ELIGIBLE_NOT_STARTED)")
LV_NEW = ("**Last verified:** 2026-10-01 — Phase25G integrated controlled development evaluation "
          "COMPLETE_CANONICAL (A7 vs A8 / C8 vs C9 / preservation / H3 frozen; Phase25 = COMPLETE_CANONICAL; "
          "Phase26 ELIGIBLE_NOT_STARTED; ROUTER_HOLDOUT RESERVED_UNOPENED_FOR_PHASE30; TEST LOCKED UNTIL PHASE39)")

ANCHOR = ("Terminal: `PHASE25G_SPEC_V1_1_COMPLETE__ROUTER_HOLDOUT_RESERVED_FOR_PHASE30__"
          "DEV_ONLY_INTEGRATED_EVALUATION_FROZEN__PHASE25G_EXECUTION_ELIGIBLE_NOT_STARTED`.")

BLOCK = f"""
## Phase25G integrated controlled development evaluation — COMPLETE_CANONICAL (2026-10-01)

Phase25G (`CANONICAL_PHASE25G_INTEGRATED_CONTROLLED_DEVELOPMENT_EVALUATION`, spec `ra_medfilm_barr_integrated_evaluation_v1_0`, repair v1.1) evaluated **A7 (C8: learned-gain + resource gate, always accept)** against **A8 (C9: same membership + S_omega post-safety)** over the complete frozen 20-policy grid (lambda {{0.00,0.25,0.50,1.00}} x budget {{0,10,25,50,100%}}) on **ROUTER_DEVELOPMENT (n=4957)**, reconstructed entirely from the frozen Phase25C OOF `delta_dice`, the Phase25E prospective C8 memberships and the Phase25F C9 decision manifest.

**No model was constructed, no training ran, no forward pass occurred, no refinement or DeltaDice was regenerated, and no threshold was tuned.** Evidence class = `CONTROLLED_META_LEVEL_OOF_DEVELOPMENT_EVIDENCE`.

**Lambda redundancy**: because the action cost is constant, C8 membership is structurally identical across lambda for a fixed budget — the four lambda replicas are **DUPLICATE MEMBERSHIP**, so only **5 unique membership sets** carry inferential weight.

**Results (5 unique budgets)**: post-safety (A8) weakly improves the macro-domain Dice delta at every informative budget and **reduces harmful replacements** (delta_dice < 0) monotonically with budget; preservation holds for every frozen policy (macro-domain lower 95% CI > -0.005). H3 is reported **descriptively only** — no numeric success threshold was pre-registered (`H3_NUMERICAL_SUCCESS_THRESHOLD_NOT_PRE_REGISTERED = true`). S_omega adds an analytical `a * 1168` MAC increment and **saves no compute**.

**No policy selected**: `lambda_selected = false`, `best_budget_selected = false`, `policy_selected = false`. R1/R2/R3/F1 belong to Phase28; C11 = `C11_NOT_EXECUTED`.

Notebook: `notebooks/phasewise/phase_25g_controlled_validation/phase25g_integrated_controlled_evaluation.ipynb` (SHA-256 `{NB_SHA}`, 41 sections, 9 figures, 3x byte-identical).

Evidence: `reports/audits/phase25g_final_freeze.json`, `phase25g_reconstruction_integrity.json`, `phase25g_a7_a8_identity_control_audit.json`, `phase25g_preservation_adjudication.json`, `phase25g_h3_result.json`, `phase25g_compute_accounting_audit.json`, `phase25g_notebook_determinism.json`, `reports/tables/phase25g_c8_c9_comparison.csv`.

Current state: **Phase25 = COMPLETE_CANONICAL (25A-25G)**; Phase26 = ELIGIBLE_NOT_STARTED; ROUTER_HOLDOUT = RESERVED_UNOPENED_FOR_PHASE30; Phase30 = NOT_STARTED; VAL808 = UNOPENED; TEST = LOCKED UNTIL PHASE39.

Terminal: `PHASE25G_INTEGRATED_CONTROLLED_DEVELOPMENT_EVALUATION_COMPLETE__A7_A8_C8_C9_PRESERVATION_AND_H3_FROZEN__PHASE25_COMPLETE__PHASE26_ELIGIBLE_NOT_STARTED`.
"""

IDX_DIR_OLD = ("  phase25g_controlled_validation.ipynb                          # NOT YET CREATED "
               "(spec v1.1 COMPLETE_FROZEN; EXECUTION_ELIGIBLE_NOT_STARTED; DEV-only)")
IDX_DIR_NEW = (f"  phase25g_integrated_controlled_evaluation.ipynb               "
               f"# COMPLETE_CANONICAL canonical SHA {NB_SHA}")

IDX_IMM_ANCHOR = ("- **Phase25E specification notebook** "
                  "(`phase25e_resource_gate_specification.ipynb`) — SHA-256 "
                  "`a431b3604021c0f4ffaaa6153302d674a38167b1792ab55d09a58a8ad2a5c41c`")
IDX_IMM_ADD = (f"{IDX_IMM_ANCHOR}\n\n"
               f"- **Phase25F canonical notebook** (`phase25f_post_safety_execution.ipynb`) — "
               f"SHA-256 `1ba9c08bee97e95926994b11268017e8d6b45150929ebe6edfca4dfe95715c90`\n"
               f"- **Phase25G canonical notebook** (`phase25g_integrated_controlled_evaluation.ipynb`) — "
               f"SHA-256 `{NB_SHA}`")


def main() -> int:
    audit = {
        "artifact": "phase25g_project_status_sync",
        "phase": "25G", "stage": "PROJECT_STATUS_SYNC",
        "method": "RA-MedFiLM-BARR",
        "additive_only": True,
        "notebook_sha256": NB_SHA,
        "documents": {}, "all_pass": True,
    }
    failures = []
    for rel in DOCS:
        p = ROOT / rel
        before = C.sha256_file(p)
        text = p.read_text(encoding="utf-8")
        applied = []
        if BLOCK.strip() in text:
            applied.append("already_synced")
        else:
            for old, new, tag in ((R1_OLD, R1_NEW, "status_sentence"),
                                  (R2_OLD, R2_NEW, "phase25g_block_status"),
                                  (R3_OLD, R3_NEW, "current_state"),
                                  (LV_OLD, LV_NEW, "last_verified")):
                if old in text:
                    text = text.replace(old, new, 1)
                    applied.append(tag)
                else:
                    failures.append(f"{rel}: {tag} not found")
            if ANCHOR in text:
                text = text.replace(ANCHOR, ANCHOR + "\n" + BLOCK, 1)
                applied.append("phase25g_execution_block")
            else:
                failures.append(f"{rel}: anchor not found")
            if rel == "notebooks/phasewise/PHASE_INDEX.md":
                if IDX_DIR_OLD in text:
                    text = text.replace(IDX_DIR_OLD, IDX_DIR_NEW, 1)
                    applied.append("index_dir_listing")
                if IDX_IMM_ANCHOR in text:
                    text = text.replace(IDX_IMM_ANCHOR, IDX_IMM_ADD, 1)
                    applied.append("immutability_list")
        p.write_text(text, encoding="utf-8")
        after = C.sha256_file(p)
        audit["documents"][rel] = {"before_sha256": before, "after_sha256": after,
                                   "changed": before != after, "edits_applied": applied}

    required = ["Phase25 = COMPLETE_CANONICAL", "Phase26 = ELIGIBLE_NOT_STARTED",
                "RESERVED_UNOPENED_FOR_PHASE30", "TEST = LOCKED UNTIL PHASE39"]
    presence = {rel: {k: (k in (ROOT / rel).read_text(encoding="utf-8")) for k in required} for rel in DOCS}
    missing = {r: [k for k, v in d.items() if not v] for r, d in presence.items()}
    missing = {k: v for k, v in missing.items() if v}
    audit["required_wording_presence"] = presence
    audit["required_wording_missing"] = missing
    audit["failures"] = failures
    audit["all_pass"] = (not failures and not missing)
    C.write_json(C.AUD / "phase25g_project_status_sync.json", audit)

    print("docs changed:", sum(1 for v in audit["documents"].values() if v["changed"]), "/", len(DOCS))
    print("missing wording:", missing)
    if failures:
        print("FAILURES:", failures)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
