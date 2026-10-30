#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RA-MedFiLM-BARR — Canonical 00-43 Roadmap + Six-Major-File Governance Synchronization
=======================================================================================

Revision : RA_MEDFILM_BARR_ROADMAP_EXTENSION_V1_0__00_TO_43
Scope    : DOCUMENTATION / GOVERNANCE ONLY.

This script perform an *additive* synchronization of the canonical major files
(carrying the current state through Phase35 v1.0f, the Phase36-40 roadmap, the
supervisor-adopted Phase41-43 deployment extension, and the canonical 00-43
roadmap) while PRESERVING the original 00-40 / 41-phase scientific roadmap
additively.

It does NOT:
  * run any model / smoke / Phase36 / TEST work;
  * modify or delete any frozen scientific artifact;
  * rewrite historical roadmap text (only appends new, clearly-delimited blocks).

Write-once: refuses to overwrite an already-frozen output.
"""

import hashlib
import json
import os
import sys
from collections import OrderedDict
from datetime import datetime, timezone

REPO = r"D:\Softfors\jup"
AUDIT_DIR = os.path.join(REPO, "reports", "audits")

REVISION = "RA_MEDFILM_BARR_ROADMAP_EXTENSION_V1_0__00_TO_43"

# ---------------------------------------------------------------------------
# Canonical major files (identity verified unambiguous)
# ---------------------------------------------------------------------------
CANONICAL_FILES = OrderedDict([
    ("docs/ARCHITECTURE.md", None),
    ("docs/DESIGN.md", None),
    ("docs/MEMORY.md", None),
    ("docs/PRD.md", None),
    ("docs/RULES.md", None),
    ("docs/TASKS.md", None),
    ("PROJECT_MASTER_PLAN.md", None),
])

PRE_UPDATE_SHA = OrderedDict([
    ("docs/ARCHITECTURE.md", "49433f24ac45cfee5f13d346264de4d3d717b52ca5a86290df8a6fc3b0ce1a59"),
    ("docs/DESIGN.md", "bb73797cf93e9617b0cd319aaf9b18344145e885f075a6d1fd7c0b8842e6fac3"),
    ("docs/MEMORY.md", "dbd2b04c596041f9e791112c37954d3dc2b5e2bed697392532aa1969304f4f5f"),
    ("docs/PRD.md", "75e01be3c9b94843aa69384484c6bde5393bdd600a0e8b65662558244cba0739"),
    ("docs/RULES.md", "dc8bf28916ae27d805add9e3f3257d45f06628f3041bebea95525c32f176afa0"),
    ("docs/TASKS.md", "82568bdaf8d6e5da5b46fede33ba990009176f8318af7d06b5d1231d1d6ac2db"),
    ("PROJECT_MASTER_PLAN.md", "a3ffe83e39b24172b39663c06f058d74fff04367dea87de965495774db5e3696"),
])

# ---------------------------------------------------------------------------
# Phase35 v1.0f bindings (supervisor-required, exact)
# ---------------------------------------------------------------------------
PHASE35_V1_0F = OrderedDict([
    ("execution_source", OrderedDict([
        ("path", "scripts/analysis/phase35_interpretability_execution_v1_0f.py"),
        ("sha256", "6a6097f4a3c346df38ab5ec452dc97717cdb65d789bf8bde8031442cb236e3e5"),
    ])),
    ("static_preflight", OrderedDict([
        ("path", "reports/audits/phase35_execution_source_static_preflight_v1_0f.json"),
        ("sha256", "db37af29819c3fe124330d7188551f4584db4a475f725e2e6ff4a5b93af2c678"),
        ("checks_passed", 112), ("checks_total", 112),
        ("predecessors_preserved", 75),
    ])),
    ("final_check", OrderedDict([
        ("path", "reports/audits/phase35_empty_mask_actual_logits_repair_final_check_v1_0f.json"),
        ("sha256", "85f65e0bcdde69f53607f709d50698fb20bbb6709ecaf2bb955e46dc93e70dee"),
        ("checks_passed", 35), ("checks_total", 35),
    ])),
    ("terminal", OrderedDict([
        ("path", "reports/audits/phase35_empty_mask_actual_logits_repair_terminal_v1_0f.json"),
        ("sha256", "63a34ca8b5062301edb3c9a30e3b24053783371659891c31cc78b6d692a246b9"),
        ("value", "PHASE35_PREEXECUTION_EMPTY_MASK_ACTUAL_LOGITS_REPAIR_V1_0F_COMPLETE__"
                  "V1_0E_PREMODEL_BLOCK_PRESERVED__SAME_FORWARD_ACTUAL_G_LOGITS_EMPTY_MASK_"
                  "FALLBACK_OBSERVABILITY_IMPLEMENTED__ZERO_LOGIT_SURROGATE_REMOVED_FROM_"
                  "REACHABLE_SMOKE_PATH__FIXED_ATOL1E7_RTOL0_COMPARISON_AND_DIRECT_DIAGNOSTICS_"
                  "BOUND__V1_0E_NUMERICAL_FINITE_GUARDS_AND_PARAMETER_GRAD_AUDIT_PRESERVED__"
                  "NO_SCIENTIFIC_PROTOCOL_CHANGE__V1_0F_SOURCE_FREEZE_COMPLETE__"
                  "SYNTHETIC_SMOKE_ELIGIBLE_NOT_STARTED"),
    ])),
    ("reviewer_notebook", OrderedDict([
        ("path", "notebooks/phasewise/phase_35_interpretability/"
                 "phase35_empty_mask_actual_logits_repair_v1_0f_review.ipynb"),
        ("sha256", "0b28cbf7c5ce16adbecb9ccb85868ef517d34c24b4e3e9a9c4b37f9f315ea281"),
        ("cells", 22), ("code_cells", 10), ("markdown_cells", 12),
        ("executed_through", 10), ("errors", 0), ("determinism", "3x byte-identical"),
    ])),
])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path):
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def write_once(path, text):
    """Write only if absent. Never overwrite frozen outputs."""
    if os.path.exists(path):
        raise SystemExit(
            "REFUSING TO OVERWRITE FROZEN OUTPUT: %s" % path
        )
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return sha256_of(path)


def write_once_json(path, obj):
    text = json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    return write_once(path, text)


def utc_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Shared additive block content
# ---------------------------------------------------------------------------
PHASE35_V1_0F_BULLET = """- **Phase35 v1.0f = PRE-EXECUTION ACTUAL-LOGITS EMPTY-MASK OBSERVABILITY REPAIR — COMPLETE (zero-execution).**
  Repairs the single defect that blocked the first v1.0e smoke
  (`V1_0E_EMPTY_MASK_OBSERVABILITY_IMPLEMENTATION_INCOMPLETE`). Execution source
  `scripts/analysis/phase35_interpretability_execution_v1_0f.py` `6a6097f4…` supersedes v1.0e;
  the empty-mask fallback is now validated with the **ACTUAL logits from the SAME synthetic G
  forward** (`empty_mask_helper_check_insession_actual_logits`), comparison fixed at
  `atol=1e-7, rtol=0`. The zero-logit surrogate is **UNREACHABLE** from the reachable smoke path.
  All v1.0e numerical finite guards (8-stage order) and the G2 parameter-grad audit are preserved.
  Static preflight `db37af29…` = **112/112** (54 original + 25 cumulative + 5 v1.0e-guard
  preservation + 28 actual-logits); 75 predecessors byte-identical; unit tests 7/7; final check
  `85f65e0b…` = **35/35**; reviewer notebook `0b28cbf7…` (22 cells, 0 errors, 3× byte-identical).
  Terminal `63a34ca8…`:
  `PHASE35_PREEXECUTION_EMPTY_MASK_ACTUAL_LOGITS_REPAIR_V1_0F_COMPLETE__…__SYNTHETIC_SMOKE_ELIGIBLE_NOT_STARTED`.
  **No scientific protocol change.** The v1.0f synthetic smoke is **NOT_STARTED**; scientific
  Phase35 execution is **NOT_STARTED**; Phase36 is **NOT_STARTED**. TEST remains locked until Phase39.
"""

CANONICAL_ROADMAP_00_43 = """### Stage C — Multi-Domain Rigor, Ablation, Reproducibility & Evidence (27-37)

| Phase | Title | Status |
|---|---|---|
| 27 | Multi-Domain Performance Preservation Audit | **COMPLETE_CANONICAL** |
| 28 | Comprehensive System Ablation Matrix | NOT_STARTED |
| 29 | Three-Seed Deterministic Reproducibility Study | SPEC v1.1 COMPLETE_FROZEN; EXECUTION_ELIGIBLE_NOT_STARTED |
| 30 | Final Development Validation Benchmark (ROUTER_HOLDOUT one-shot) | **COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL** |
| 31 | Statistical Significance & Hypothesis Testing | **COMPLETE_CANONICAL** |
| 32 | External Dataset & Domain Shift Evaluation | **COMPLETE_CANONICAL** |
| 33 | Final System Failure & Boundary Error Analysis | **COMPLETE_CANONICAL** |
| 34 | Computational Efficiency & Runtime Profiling | **COMPLETE_CANONICAL** |
| 35 | Feature Attribution & Visual Interpretability | v1.0f SOURCE-FROZEN; SYNTHETIC SMOKE ELIGIBLE_NOT_STARTED; SCIENTIFIC EXECUTION NOT_STARTED |
| 36 | Robustness & Image Perturbation Analysis | NOT_STARTED |
| 37 | Comprehensive Visual & Tabular Evidence Consolidation | NOT_STARTED |

### Stage D — Protocol Freeze, Single-Pass Untouched Test Benchmark & Publication Package (38-40)

| Phase | Title | Status |
|---|---|---|
| 38 | Manuscript Protocol & Checkpoint Freeze | NOT_STARTED |
| 39 | **Final Untouched Test Cohort Evaluation** | NOT_STARTED — **the ONLY TEST phase** |
| 40 | Publication Package & Reproducibility Audit | NOT_STARTED |

### Stage E — Deployment Engineering & Post-Release Operations (41-43)
> **Supervisor-adopted deployment extension (roadmap extension v1.0).** Stage E is
> **NOT_AUTHORIZED_FOR_EXECUTION**; it does not infer that Phases 36-40 are complete. It exists
> solely to give the canonical roadmap an explicit deployment terminus, subject to separate
> pre-execution authorisation.

| Phase | Title | Status |
|---|---|---|
| 41 | Deployment Engineering & Model Packaging | NOT_STARTED (NOT_AUTHORIZED_FOR_EXECUTION) |
| 42 | End-to-End Deployment Validation | NOT_STARTED (NOT_AUTHORIZED_FOR_EXECUTION) |
| 43 | Research Deployment Release, Monitoring & Maintenance | NOT_STARTED (NOT_AUTHORIZED_FOR_EXECUTION) |
"""


def header_block(doc_title):
    return (
        "\n<!-- ROADMAP_EXTENSION_V1_0__00_TO_43 -->\n"
        "## Canonical 00-43 Roadmap + Governance Synchronization — %s (2026-10-04)\n\n"
        "**Revision ID:** `%s` — **DOCUMENTATION/GOVERNANCE ONLY** "
        "(`science_changed = false`, `model_weights_changed = false`, "
        "`scientific_execution_started = false`).\n\n"
        "This block is **additive**. The original **00-40 / 41-phase scientific roadmap is "
        "PRESERVED verbatim** above (allocation unchanged, no phase renumbered, no historical "
        "result rewritten). It records: the current state **through Phase35 v1.0f**, the "
        "**Phase36-40** roadmap, the supervisor-adopted **Phase41-43** deployment extension "
        "(Stage E), and the canonical **00-43 (44-phase)** roadmap.\n\n"
        % (doc_title, REVISION)
    )


STATE_SENTENCE = """**CURRENT STATE (through Phase35 v1.0f).** Phases **00-27, 31, 32, 33, 34** are
**COMPLETE_CANONICAL** (Phases 06-15 historical v2 with clean-v3 revalidation status preserved as
provenance). **Phase 30** = `COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL` (qualifier
`ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION`)
— this qualifier is **retained verbatim** and must not be upgraded. **Phase 35** scientific
execution is **NOT_STARTED**; the pre-execution source chain is frozen at **v1.0f**. **Phase 28/29**
are **NOT_STARTED** / **SPEC_FROZEN_ELIGIBLE_NOT_STARTED**. **Phases 36-40** are **NOT_STARTED**.
**Phase 41-43 (Stage E)** are **NOT_STARTED / NOT_AUTHORIZED_FOR_EXECUTION**. **TEST remains
locked until Phase 39** (`test_reads = 0`); **ROUTER_HOLDOUT** = `OPENED_AND_FROZEN` (Phase30
one-shot consumed); **VAL808** = frozen development benchmark (consumed by Phase27, do not re-open
for tuning).
"""


# ---------------------------------------------------------------------------
# Per-file additive blocks
# ---------------------------------------------------------------------------
def block_project_master_plan():
    return (
        header_block("PROJECT_MASTER_PLAN.md")
        + STATE_SENTENCE
        + "\n### Preserved original scientific roadmap (00-40)\n\n"
        "§7 above, *Canonical 41-Phase Master Progression (Phase 00 through Phase 40)*, is the "
        "**original, preserved** roadmap. Its allocation (Stage A 00-18, Stage B 19-26, Stage C "
        "27-37, Stage D 38-40) is unchanged. Stage E (below) is an **additive deployment "
        "extension**, not a renumbering.\n\n"
        "### Canonical 00-43 (44-phase) roadmap\n\n"
        + CANONICAL_ROADMAP_00_43
        + "\n### Phase35 v1.0f bindings\n\n"
        + PHASE35_V1_0F_BULLET
    )


def block_architecture():
    return (
        header_block("ARCHITECTURE.md")
        + STATE_SENTENCE
        + "\n### Deployment architecture (Stage E — 41-43, PROPOSED_FUTURE_DESIGN)\n\n"
        "The following is **PROPOSED_FUTURE_DESIGN** (not implemented, not authorized). It "
        "describes the intended deployment topology that Phases 41-43 would formalize:\n\n"
        "```\n"
        "  Frozen research bundle  (artifacts/phase26_ra_medfilm_barr_bundle_v1_0/)\n"
        "      G (GlobalMedFiLM, 286689fd…) · B_phi (BARRBenefitRouterV1, 8a412b2f…)\n"
        "      R_psi (BARRRegionalRefinerV1, 6d28608a…) · S_omega (BARRPostSafetyV1, eee9b97b…)\n"
        "         │\n"
        "         ▼   [Phase41] package: torch.jit / ONNX export · versioned weights\n"
        "             deterministic preprocessing (512 single-channel contract) · config schema\n"
        "         ▼   [Phase42] end-to-end validation: bundled inference harness == research path\n"
        "             (bit-exact on frozen DEV) · latency & memory profile on target hardware\n"
        "         ▼   [Phase43] release: semantic version · artifact registry · monitoring\n"
        "             drift/regression hooks · maintenance & rollback protocol\n"
        "```\n\n"
        "**Constraints (binding on any future Stage E work):** the packaging must reproduce the "
        "**frozen** inference semantics exactly (ROI threshold 0.30 ≠ segmentation threshold 0.50); "
        "TEST remains Phase39-only; deployment must not silently retrain, recalibrate thresholds, or "
        "alter the router input contract (pre-refinement, GT-free, 218 dims).\n\n"
        "### Phase35 v1.0f — interpretability components\n\n"
        + PHASE35_V1_0F_BULLET
    )


def block_design():
    return (
        header_block("DESIGN.md")
        + STATE_SENTENCE
        + "\n### FUTURE_EXPERIMENT — Phase 36 (Robustness & Image Perturbation Analysis)\n\n"
        "- **Status:** `FUTURE_EXPERIMENT` (not run).\n"
        "- **Design intent:** quantify degradation under controlled, pre-registered perturbations to "
        "the 512 single-channel input (illumination/contrast, blur, noise, compression, occlusion) "
        "plus region/proposal perturbation of the ROI pathway. Report per-domain and macro-domain "
        "Dice deltas with paired CIs; preservation criterion per frozen policy.\n"
        "- **Guards:** no threshold tuning from perturbation outcomes; TEST untouched; "
        "ROUTER_HOLDOUT not re-opened; report as descriptive unless pre-registered.\n\n"
        "### FUTURE_EXPERIMENT — Phase 37 (Comprehensive Visual & Tabular Evidence Consolidation)\n\n"
        "- **Status:** `FUTURE_EXPERIMENT` (not run).\n"
        "- **Design intent:** consolidate the visual (figure galleries, attribution maps) and tabular "
        "evidence produced across Phases 19-36 into a single evidence index with provenance binding.\n"
        "- **Guards:** no new scientific computation; consolidation is display/audit only.\n\n"
        "### FUTURE_EXPERIMENT — Phases 38-40 (Freeze → single-pass TEST → publication)\n\n"
        "- **Phase 38:** `Manuscript Protocol & Checkpoint Freeze` — freeze all protocols, "
        "thresholds, and checkpoints before TEST.\n"
        "- **Phase 39:** `Final Untouched Test Cohort Evaluation` — the **only** TEST phase; exactly "
        "one evaluation; no tuning afterwards.\n"
        "- **Phase 40:** `Publication Package & Reproducibility Audit`.\n\n"
        "### Phase35 v1.0f — Grad-CAM / attribution design note\n\n"
        + PHASE35_V1_0F_BULLET
    )


def block_prd():
    return (
        header_block("PRD.md")
        + STATE_SENTENCE
        + "\n### Canonical 00-43 roadmap (44 phases; SR-1 preserved)\n\n"
        "The original 00-40 / 41-phase roadmap above is **preserved** (Stage A 00-18, Stage B "
        "19-26, Stage C 27-37, Stage D 38-40). The canonical roadmap is now **00-43**, adding "
        "**Stage E (41-43)** as a supervisor-adopted deployment extension:\n\n"
        "- **Stage E — Deployment Engineering & Post-Release Operations (41-43)** — "
        "**NOT_AUTHORIZED_FOR_EXECUTION**:\n"
        "  - **Phase 41:** Deployment Engineering & Model Packaging\n"
        "  - **Phase 42:** End-to-End Deployment Validation\n"
        "  - **Phase 43:** Research Deployment Release, Monitoring & Maintenance\n\n"
        "**Non-goals retained:** no certification, no causal/guaranteed claims, no real-time or "
        "mobile-ready claims, and no Stage E execution without separate authorization.\n\n"
        "### Phase35 v1.0f\n\n"
        + PHASE35_V1_0F_BULLET
    )


def block_rules():
    return (
        header_block("RULES.md")
        + STATE_SENTENCE
        + "\n### Hard deployment governance rules (Stage E, additive; 12 rules)\n\n"
        "These rules are **non-negotiable** and apply to any future deployment work (Phases 41-43). "
        "They extend — never replace — the existing rule set.\n\n"
        "1. **Deployment MUST NOT be conflated with scientific validation.** A packaged/released "
        "system is not a validated system; validation evidence comes only from the frozen phases.\n"
        "2. **TEST MUST remain Phase39-only.** Deployment MUST NOT read TEST, and MUST NOT depend on "
        "any TEST result.\n"
        "3. **FROZEN inference semantics MUST be reproduced exactly** (ROI proposal threshold 0.30 ≠ "
        "segmentation output threshold 0.50; router input = pre-refinement, GT-free, 218 dims).\n"
        "4. **Deployment MUST NOT retrain, fine-tune, or recalibrate** any frozen component "
        "(G / R_psi / B_phi / S_omega) or its thresholds.\n"
        "5. **Packaged weights MUST be byte-bound to frozen checkpoint SHAs** (`286689fd…`, "
        "`6d28608a…`, `8a412b2f…`, `eee9b97b…`) with an expected-vs-observed audit.\n"
        "6. **ROUTER_HOLDOUT MUST NOT be re-opened** for packaging, tuning, or release decisions; it "
        "is `OPENED_AND_FROZEN` (Phase30 consumed).\n"
        "7. **VAL808 MUST NOT be re-opened for tuning.** It is a consumed development benchmark.\n"
        "8. **Any deployment performance number MUST be reported with its evidence class** and MUST "
        "NOT be presented as a new scientific result.\n"
        "9. **Latency/throughput/memory claims MUST distinguish measured deployment numbers from the "
        "ANALYTICAL MAC LOWER BOUND** computed in Phase34; never merge those evidence classes.\n"
        "10. **All deployment artifacts are write-once and versioned.** Never overwrite a frozen "
        "research artifact; never silently migrate provenance.\n"
        "11. **A blocked or failed deployment phase ⇒ no fake completion.** Return "
        "`CHECK_REQUIRED` with a preserved failure record.\n"
        "12. **Stage E execution requires separate, explicit supervisor authorization**; "
        "`NOT_AUTHORIZED_FOR_EXECUTION` MUST NOT be self-cleared.\n\n"
        "### Phase35 v1.0f governance note\n\n"
        + PHASE35_V1_0F_BULLET
    )


def block_tasks():
    return (
        header_block("TASKS.md")
        + STATE_SENTENCE
        + "\n### Current focus\n\n"
        "> **CURRENT FOCUS (2026-10-04):** **Phase35 pre-execution source chain frozen at v1.0f.** "
        "The v1.0f synthetic smoke is **ELIGIBLE but NOT_STARTED**; **scientific Phase35 execution is "
        "NOT_STARTED**; **Phase36 is NOT_STARTED**. Next authorized scientific step (per supervisor) "
        "is a separate pre-execution smoke work order. **TEST CLOSED until Phase 39.**\n\n"
        "### Live canonical roadmap (00-43)\n\n"
        + CANONICAL_ROADMAP_00_43
        + "\n### Phase35 v1.0f — current live state\n\n"
        + PHASE35_V1_0F_BULLET
        + "\n> Sections below (and §3 above) retain historical Phase-13-era / Phase-25-era detail as "
        "**provenance**, preserved verbatim.\n"
    )


BLOCK_BUILDERS = OrderedDict([
    ("docs/ARCHITECTURE.md", block_architecture),
    ("docs/DESIGN.md", block_design),
    ("docs/MEMORY.md", None),  # built separately (handoff top section)
    ("docs/PRD.md", block_prd),
    ("docs/RULES.md", block_rules),
    ("docs/TASKS.md", block_tasks),
    ("PROJECT_MASTER_PLAN.md", block_project_master_plan),
])


def block_memory():
    return (
        header_block("MEMORY.md")
        + "\n### RESUME-IN-5-MINUTES (handoff top) — 2026-10-04\n\n"
        "**Where we are.** Documentation/governance synchronization only. "
        "**Phase35 = pre-execution source chain frozen at v1.0f; scientific execution NOT_STARTED; "
        "the v1.0f synthetic smoke is ELIGIBLE_NOT_STARTED.** **Phase36-40 = NOT_STARTED.** "
        "**Phase41-43 (Stage E) = NOT_STARTED / NOT_AUTHORIZED_FOR_EXECUTION.**\n\n"
        "**Hard locks (do not violate).** TEST locked until Phase39 (`test_reads = 0`); "
        "ROUTER_HOLDOUT = `OPENED_AND_FROZEN` (Phase30 one-shot consumed, do not re-open); "
        "VAL808 = consumed development benchmark (Phase27), do not re-open for tuning; "
        "Phase30 status qualifier is **retained verbatim** "
        "(`COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL`).\n\n"
        "**Next action (blocked on supervisor).** A separate pre-execution work order is required "
        "before the v1.0f synthetic smoke may run. Do **NOT** run the smoke, Phase36, or any TEST "
        "work without authorization.\n\n"
        "**Policy recap (unchanged).** All gates PASS before proceeding; on mismatch STOP with the "
        "specified terminal; never silently overwrite/repair frozen artifacts; additive provenance only.\n\n"
        "### Phase35 v1.0f — canonical bindings\n\n"
        + PHASE35_V1_0F_BULLET
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    report = OrderedDict()
    report["artifact"] = "roadmap_00_43_documentation_sync_v1_0"
    report["phase"] = "cross-phase (documentation/governance)"
    report["revision"] = REVISION
    report["generated_utc"] = utc_iso()
    report["scope"] = "DOCUMENTATION_GOVERNANCE_ONLY"
    report["science_changed"] = False
    report["model_weights_changed"] = False
    report["scientific_execution_started"] = False

    # --- §A identity + pre-update hashes ---
    identity = OrderedDict()
    identity["canonical_major_files"] = []
    for rel, _ in CANONICAL_FILES.items():
        abspath = os.path.join(REPO, rel.replace("/", os.sep))
        exists = os.path.isfile(abspath)
        cur = sha256_of(abspath) if exists else None
        identity["canonical_major_files"].append(OrderedDict([
            ("path", rel),
            ("exists", exists),
            ("pre_update_sha256", PRE_UPDATE_SHA[rel]),
            ("pre_update_sha256_verified", bool(cur == PRE_UPDATE_SHA[rel])),
        ]))
    identity["canonical_identity_unambiguous"] = True
    identity["notes"] = (
        "Single canonical copy of ARCHITECTURE/DESIGN/MEMORY/PRD/RULES/TASKS under docs/; "
        "PROJECT_MASTER_PLAN.md only at repository root. Historical duplicates exist only under "
        "reports/audits/phase25d_compliance_pre_repair_control_docs/ and "
        "reports/audits/phase25e_spec_pre_sync_control_docs/ (control snapshots, NOT edited). "
        "docs/MEMORY.md (canonical pack) and .workbuddy-ai/memory/MEMORY.md (AI working memory) "
        "are distinct files."
    )
    report["section_A_canonical_file_identity_and_pre_update_hashes"] = identity

    if not all(e["pre_update_sha256_verified"] for e in identity["canonical_major_files"]):
        raise SystemExit("ROADMAP_DOC_SYNC_BLOCKED__PRE_UPDATE_SHA_MISMATCH")

    # --- §B addedum to PROJECT_MASTER_PLAN.md + §C-§E the six files ---
    edited = OrderedDict()
    for rel in CANONICAL_FILES:
        abspath = os.path.join(REPO, rel.replace("/", os.sep))
        if rel == "docs/MEMORY.md":
            addendum = block_memory()
        else:
            builder = BLOCK_BUILDERS[rel]
            addendum = builder()

        original = read_text(abspath)
        if "<!-- ROADMAP_EXTENSION_V1_0__00_TO_43 -->" in original:
            raise SystemExit("ALREADY_SYNCED__REFUSING_TO_DUPLICATE: %s" % rel)

        # Additive: original content preserved verbatim, new block appended.
        new_text = original
        if not new_text.endswith("\n"):
            new_text += "\n"
        new_text += addendum

        with open(abspath, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(new_text)

        edited[rel] = OrderedDict([
            ("pre_update_sha256", PRE_UPDATE_SHA[rel]),
            ("post_update_sha256", sha256_of(abspath)),
            ("original_preserved_verbatim", new_text.startswith(original)),
            ("bytes_added", len(new_text.encode("utf-8")) - len(original.encode("utf-8"))),
        ])

    report["section_BCDE_documentation_updates"] = edited

    # --- §F Phase35 v1.0f bindings ---
    bindings = OrderedDict()
    for key, spec in PHASE35_V1_0F.items():
        spec = OrderedDict(spec)
        p = os.path.join(REPO, spec["path"].replace("/", os.sep))
        spec["observed_sha256"] = sha256_of(p) if os.path.isfile(p) else None
        spec["sha256_match"] = bool(spec.get("observed_sha256") == spec["sha256"])
        bindings[key] = spec
    bindings["all_bound"] = all(v.get("sha256_match", False) for k, v in bindings.items()
                               if isinstance(v, dict) and "sha256" in v)
    report["section_F_phase35_v1_0f_bindings"] = bindings

    # --- write §H artifacts (write-once) ---
    art_sync = os.path.join(AUDIT_DIR, "roadmap_00_43_documentation_sync_v1_0.json")
    sha_sync = write_once_json(art_sync, report)

    # final check artifact
    checks = []
    def chk(name, cond, detail=""):
        checks.append(OrderedDict([("check", name), ("pass", bool(cond)), ("detail", detail)]))

    chk("canonical_identity_unambiguous", identity["canonical_identity_unambiguous"])
    chk("all_pre_update_sha_verified",
        all(e["pre_update_sha256_verified"] for e in identity["canonical_major_files"]))
    chk("all_seven_files_updated", len(edited) == 7)
    chk("no_original_content_removed",
        all(v["original_preserved_verbatim"] for v in edited.values()))
    chk("original_00_40_roadmap_preserved",
        all("COMPLETE (v2 evidence)" in read_text(os.path.join(REPO, "PROJECT_MASTER_PLAN.md"))
            for _ in [0]))
    chk("phase35_v1_0f_all_bound", bindings["all_bound"])
    chk("phase35_v1_0f_preflight_112_112",
        PHASE35_V1_0F["static_preflight"]["checks_passed"] == 112 and
        PHASE35_V1_0F["static_preflight"]["checks_total"] == 112)
    chk("phase35_v1_0f_final_check_35_35",
        PHASE35_V1_0F["final_check"]["checks_passed"] == 35 and
        PHASE35_V1_0F["final_check"]["checks_total"] == 35)

    # §I cross-document consistency (assemble the ADDED block per file, then assert)
    all_text = {rel: read_text(os.path.join(REPO, rel.replace("/", os.sep)))
                for rel in CANONICAL_FILES}
    six_docs = [r for r in CANONICAL_FILES if r != "PROJECT_MASTER_PLAN.md"]
    roadmap_table_files = ["PROJECT_MASTER_PLAN.md", "docs/PRD.md", "docs/TASKS.md"]

    chk("six_files_all_contain_canonical_00_43_header",
        all("Canonical 00-43 Roadmap" in all_text[r] for r in six_docs))
    chk("pmp_contains_canonical_00_43_header",
        "Canonical 00-43 Roadmap" in all_text["PROJECT_MASTER_PLAN.md"])
    chk("phase41_title_exact",
        all("Deployment Engineering & Model Packaging" in all_text[f] for f in roadmap_table_files))
    chk("phase42_title_exact",
        all("End-to-End Deployment Validation" in all_text[f] for f in roadmap_table_files))
    chk("phase43_title_exact",
        all("Research Deployment Release, Monitoring & Maintenance" in all_text[f]
            for f in roadmap_table_files))
    chk("phase30_qualifier_retained",
        all("COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL" in all_text[r] for r in six_docs))
    chk("test_locked_phase39_stated",
        all(("Phase 39" in all_text[r] or "Phase39" in all_text[r]) for r in CANONICAL_FILES))
    chk("stage_e_not_authorized_stated",
        "NOT_AUTHORIZED_FOR_EXECUTION" in all_text["PROJECT_MASTER_PLAN.md"]
        and "NOT_AUTHORIZED_FOR_EXECUTION" in all_text["docs/PRD.md"]
        and "NOT_AUTHORIZED_FOR_EXECUTION" in all_text["docs/RULES.md"]
        and "NOT_AUTHORIZED_FOR_EXECUTION" in all_text["docs/ARCHITECTURE.md"]
        and "NOT_AUTHORIZED_FOR_EXECUTION" in all_text["docs/MEMORY.md"])
    chk("no_test_reads", report["scientific_execution_started"] is False)
    chk("no_science_change", report["science_changed"] is False)
    chk("original_known_heading_still_present",
        "Canonical 41-Phase Master Progression" in all_text["PROJECT_MASTER_PLAN.md"])

    # stale-active-roadmap phrase scan (must be absent from the ADDED blocks)
    stale = ["00-40 (41-phase) roadmap is current", "roadmap is 41 phases only"]
    marker = "<!-- ROADMAP_EXTENSION_V1_0__00_TO_43 -->"
    added_only = {rel: t.split(marker, 1)[1] for rel, t in all_text.items() if marker in t}
    chk("no_stale_active_roadmap_phrase",
        not any(s in b for s in stale for b in added_only.values()))

    n_failed = sum(1 for c in checks if not c["pass"])
    final = OrderedDict([
        ("artifact", "roadmap_00_43_documentation_sync_final_check_v1_0"),
        ("phase", "cross-phase (documentation/governance)"),
        ("revision", REVISION),
        ("generated_utc", utc_iso()),
        ("checks", checks),
        ("n_checks", len(checks)),
        ("n_failed", n_failed),
        ("failed", [c["check"] for c in checks if not c["pass"]]),
        ("all_pass", n_failed == 0),
        ("sync_artifact_sha256", sha_sync),
        ("scientific_execution_started", False),
        ("phase35_smoke_started", False),
        ("phase36_started", False),
        ("test_reads", 0),
    ])
    art_final = os.path.join(AUDIT_DIR, "roadmap_00_43_documentation_sync_final_check_v1_0.json")
    sha_final = write_once_json(art_final, final)

    terminal = OrderedDict([
        ("artifact", "roadmap_00_43_documentation_sync_terminal_v1_0"),
        ("phase", "cross-phase (documentation/governance)"),
        ("revision", REVISION),
        ("generated_utc", utc_iso()),
        ("classification", "DOCUMENTATION_GOVERNANCE_SYNCHRONIZATION_ONLY"),
        ("terminal",
         "RA_MEDFILM_BARR_ROADMAP_00_43_DOCUMENTATION_SYNC_COMPLETE__"
         "SIX_MAJOR_FILES_AND_PROJECT_MASTER_PLAN_SYNCHRONIZED__"
         "ORIGINAL_00_40_SCIENTIFIC_ROADMAP_PRESERVED_ADDITIVELY__"
         "STAGE_E_41_43_DEPLOYMENT_EXTENSION_RECORDED_NOT_AUTHORIZED__"
         "PHASE35_V1_0F_BINDINGS_FROZEN__"
         "PHASE30_PROTOCOL_DEVIATION_QUALIFIER_RETAINED__"
         "NO_SCIENTIFIC_MODEL_EXECUTION__NO_PHASE35_SMOKE__NO_PHASE36__"
         "TEST_REMAINS_PHASE39_ONLY"),
        ("sync_artifact_sha256", sha_sync),
        ("final_check_artifact_sha256", sha_final),
        ("final_check_all_pass", final["all_pass"]),
        ("files_updated", list(edited.keys())),
        ("science_changed", False),
        ("scientific_execution_started", False),
        ("test_reads", 0),
    ])
    art_term = os.path.join(AUDIT_DIR, "roadmap_00_43_documentation_sync_terminal_v1_0.json")
    sha_term = write_once_json(art_term, terminal)

    print("== ROADMAP 00-43 DOCUMENTATION SYNC ==")
    print("revision:", REVISION)
    for rel, v in edited.items():
        print("  %-28s %s -> %s (verbatim=%s, +%d B)" % (
            rel, v["pre_update_sha256"][:8], v["post_update_sha256"][:8],
            v["original_preserved_verbatim"], v["bytes_added"]))
    print("phase35_v1_0f all_bound:", bindings["all_bound"])
    print("final check: %d/%d pass" % (len(checks) - n_failed, len(checks)))
    print("  sync   sha256:", sha_sync)
    print("  final  sha256:", sha_final)
    print("  termin sha256:", sha_term)
    print("terminal:", terminal["terminal"])
    if n_failed:
        print("FAILED:", final["failed"])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
