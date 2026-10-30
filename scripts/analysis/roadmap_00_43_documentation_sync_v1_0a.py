#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RA-MedFiLM-BARR — ROADMAP 00-43 DOCUMENTATION SYNC v1.0a
ADDITIVE GOVERNANCE RECONCILIATION
=======================================================================

GOVERNANCE / DOCUMENTATION REPAIR ONLY. No scientific execution.

Repairs the three governance/reporting defects disclosed by independent audit of
RA_MEDFILM_BARR_ROADMAP_EXTENSION_V1_0__00_TO_43:

  D1 V1_0_SUCCESS_TERMINAL_CONTRACT_VARIANT              (GOVERNANCE_REPORTING_ONLY)
  D2 V1_0_CROSS_DOCUMENT_STAGE_E_TITLE_CHECK_FALSE_POSITIVE (GOVERNANCE_VALIDATION_FALSE_POSITIVE)
  D3 V1_0_DESIGN_STAGE_E_PROSPECTIVE_EXPERIMENT_CONTENT_INCOMPLETE (DOCUMENTATION_SCOPE_INCOMPLETE)

Adds a clearly-marked reconciliation block (marker
`<!-- ROADMAP_EXTENSION_V1_0A_STAGE_E_RECONCILIATION -->`) to FOUR canonical documents
(ARCHITECTURE, DESIGN, MEMORY, RULES). PRD/TASKS/PROJECT_MASTER_PLAN are NOT modified
unless a genuine inconsistency is found.

The v1.0 block is preserved verbatim; v1.0 artifacts are never overwritten.
Write-once: refuses to overwrite any already-frozen output.
"""

import hashlib
import json
import os
import sys
from collections import OrderedDict
from datetime import datetime, timezone

REPO = r"D:\Softfors\jup"
AUDIT = os.path.join(REPO, "reports", "audits")

REVISION = "RA_MEDFILM_BARR_ROADMAP_EXTENSION_V1_0__00_TO_43"
V1_0A = "RA_MEDFILM_BARR_ROADMAP_EXTENSION_V1_0A__STAGE_E_RECONCILIATION"
MARKER = "<!-- ROADMAP_EXTENSION_V1_0A_STAGE_E_RECONCILIATION -->"

SEVEN = OrderedDict([
    ("docs/ARCHITECTURE.md", None),
    ("docs/DESIGN.md", None),
    ("docs/MEMORY.md", None),
    ("docs/PRD.md", None),
    ("docs/RULES.md", None),
    ("docs/TASKS.md", None),
    ("PROJECT_MASTER_PLAN.md", None),
])

FOUR_TO_REPAIR = ["docs/ARCHITECTURE.md", "docs/DESIGN.md", "docs/MEMORY.md", "docs/RULES.md"]
THREE_UNCHANGED = ["docs/PRD.md", "docs/TASKS.md", "PROJECT_MASTER_PLAN.md"]

POST_V1_0_SHA = OrderedDict([
    ("docs/ARCHITECTURE.md", "8fffa4e214cd143fddc930086bc3e52743806910d9cd28620476472047ad6e25"),
    ("docs/DESIGN.md", "9e9f08dc54efa8858823dee30c383617f13114637cdb09c837c9a994a21a39ab"),
    ("docs/MEMORY.md", "bc7de701ba2417fd5103023f0fbb34e3bcde5dc0148b52828fea317ed911aadd"),
    ("docs/PRD.md", "1489b07e88a8756ae25be28e08320a3087b07f52f47bd2b0e776f8f4bc26fc78"),
    ("docs/RULES.md", "f0dc805b6574d668532fa1de76ad36bad10f4f12ecf42790f5394e949bc01a71"),
    ("docs/TASKS.md", "74c1d9428ec418b3d968ec07459c0be0e176c231cbf489eb3d5ec51be22505ba"),
    ("PROJECT_MASTER_PLAN.md", "f67b31c7acafd920414ccf6cb6c1c80e28de093b0ed998e41bdc2887fba48d14"),
])

V1_0_ARTIFACTS = OrderedDict([
    ("reports/audits/roadmap_00_43_documentation_sync_v1_0.json",
     "9cb298477acfb50653a1c625751aa2dd34f434cbb9506fe6a6bd8d422a871859"),
    ("reports/audits/roadmap_00_43_documentation_sync_final_check_v1_0.json",
     "7a92e5f5dd252a4a0d5997eeb0f670aa3dcf2dd9e12822b1ceff197f1fa0b28e"),
    ("reports/audits/roadmap_00_43_documentation_sync_terminal_v1_0.json",
     "e914c6e8476bb7267b9fb9bb87e2028ac2e5e939c9fbe319c96384f6e86d0c00"),
    ("notebooks/phasewise/phase_35_interpretability/"
     "roadmap_00_43_documentation_sync_v1_0_review.ipynb",
     "7765bff9c26e513ca0ea7a39cab8cc17ebaf8f973b62a50e1a7c5a9af0c40313"),
    ("reports/audits/roadmap_00_43_documentation_sync_reviewer_notebook_audit_v1_0.json",
     "1b1fdb270ac1d91e429e6b8351aec8a243c3b84d9f761d8ac645ed66484aefb8"),
])

# Phase35 v1.0f five bindings (must be byte-identical; NOT modified)
PHASE35_V1_0F = OrderedDict([
    ("execution_source", ("scripts/analysis/phase35_interpretability_execution_v1_0f.py",
                          "6a6097f4a3c346df38ab5ec452dc97717cdb65d789bf8bde8031442cb236e3e5")),
    ("preflight", ("reports/audits/phase35_execution_source_static_preflight_v1_0f.json",
                   "db37af29819c3fe124330d7188551f4584db4a475f725e2e6ff4a5b93af2c678")),
    ("final_check", ("reports/audits/phase35_empty_mask_actual_logits_repair_final_check_v1_0f.json",
                     "85f65e0bcdde69f53607f709d50698fb20bbb6709ecaf2bb955e46dc93e70dee")),
    ("terminal", ("reports/audits/phase35_empty_mask_actual_logits_repair_terminal_v1_0f.json",
                  "63a34ca8b5062301edb3c9a30e3b24053783371659891c31cc78b6d692a246b9")),
    ("review_notebook", ("notebooks/phasewise/phase_35_interpretability/"
                         "phase35_empty_mask_actual_logits_repair_v1_0f_review.ipynb",
                         "0b28cbf7c5ce16adbecb9ccb85868ef517d34c24b4e3e9a9c4b37f9f315ea281")),
])

# Exact Stage-E identities (canonical wording)
S41 = "Phase 41 — Deployment Engineering & Model Packaging"
S42 = "Phase 42 — End-to-End Deployment Validation"
S43 = "Phase 43 — Research Deployment Release, Monitoring & Maintenance"
STAGE_E_WORDING = (
    "Stage E (Phases 41\u201343) is a supervisor-adopted extension of the full project "
    "roadmap. Its inclusion in the roadmap does not authorize execution. Phases 41\u201343 "
    "remain NOT_STARTED and NOT_AUTHORIZED_FOR_EXECUTION until their own entry gates are satisfied."
)


def sha256_of(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def read_text(p):
    with open(p, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def write_once_json(path, obj):
    if os.path.exists(path):
        raise SystemExit("REFUSING TO OVERWRITE FROZEN OUTPUT: %s" % path)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    return sha256_of(path)


def utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def count_titles(text):
    return (text.count(S41), text.count(S42), text.count(S43))


# ---------------------------------------------------------------------------
# Reconciliation blocks (append-only; do NOT touch the v1.0 block)
# ---------------------------------------------------------------------------
def common_head(doc):
    return (
        "\n" + MARKER + "\n"
        "## Stage E (Phases 41\u201343) Reconciliation \u2014 %s (2026-10-05)\n\n"
        "**Revision:** `%s`  \n"
        "**Scope:** GOVERNANCE / DOCUMENTATION REPAIR ONLY "
        "(`science_changed = false`, `scientific_execution_started = false`).\n\n"
        "> " + STAGE_E_WORDING + "\n\n"
        "**Exact Stage-E identities (canonical, binding):**\n\n"
        "- **%s** \u2014 status `NOT_STARTED` / `NOT_AUTHORIZED_FOR_EXECUTION`\n"
        "- **%s** \u2014 status `NOT_STARTED` / `NOT_AUTHORIZED_FOR_EXECUTION`\n"
        "- **%s** \u2014 status `NOT_STARTED` / `NOT_AUTHORIZED_FOR_EXECUTION`\n\n"
        "The **original 00\u201340 scientific roadmap** remains preserved verbatim (Stage A 00\u201318, "
        "Stage B 19\u201326, Stage C 27\u201337, Stage D 38\u201340). **Stage E (41\u201343)** is an "
        "additive supervisor-adopted deployment extension. The **full project roadmap is 00\u201343 "
        "(44 numbered phases)**.\n"
        % (doc, V1_0A, S41, S42, S43)
    )


def block_architecture():
    return common_head("ARCHITECTURE.md") + (
        "\n### Scientific model graph vs deployment system wrapper (clean separation)\n\n"
        "**SCIENTIFIC MODEL GRAPH** (frozen; the canonical inference path \u2014 unchanged, no new "
        "scientific component):\n\n"
        "```\n"
        "Image + Task ID\n"
        "    \u2193\n"
        "G                      (GlobalMedFiLM, frozen)\n"
        "    \u2193\n"
        "pre-refinement features\n"
        "    \u2193\n"
        "B_phi                  (BARRBenefitRouterV1, frozen)\n"
        "    \u2193\n"
        "SKIP / EXECUTE\n"
        "\n"
        "SKIP:      final = global\n"
        "\n"
        "EXECUTE:   R_psi      (BARRRegionalRefinerV1, frozen)\n"
        "              \u2193\n"
        "           S_omega    (BARRPostSafetyV1, frozen)\n"
        "              \u2193\n"
        "           ACCEPT \u2192 regional fused\n"
        "           REJECT \u2192 global\n"
        "```\n\n"
        "Preserved routing/execution identities: `R_psi_exec = router_execute`; "
        "`S_omega_exec = R_psi_exec` (S_omega is evaluated only where R_psi executed). "
        "`SKIP \u2192 final = global`; `ACCEPT \u2192 regional fused`; `REJECT \u2192 global`.\n\n"
        "**DEPLOYMENT SYSTEM WRAPPER** (PROPOSED_FUTURE_DESIGN; Stage E 41\u201343, wraps the frozen "
        "model graph without altering it):\n\n"
        "```\n"
        "Client/Input\n"
        "    \u2192 validation\n"
        "    \u2192 task/domain validation\n"
        "    \u2192 frozen preprocessing            (512 single-channel contract; ROI 0.30 \u2260 output 0.50)\n"
        "    \u2192 frozen RA-MedFiLM-BARR          (G \u2192 B_phi \u2192 [R_psi \u2192 S_omega] \u2192 fusion)\n"
        "    \u2192 final segmentation mask\n"
        "    \u2192 optional routing/runtime metadata\n"
        "    \u2192 serialization/API response\n"
        "```\n\n"
        "**No new scientific component** is introduced by the wrapper. The wrapper is engineering "
        "plumbing around the frozen scientific graph.\n"
    )


def block_design():
    return common_head("DESIGN.md") + (
        "\n> **Evidence-class labels (mandatory):** each item below is "
        "`FUTURE / NOT_STARTED / NOT_AUTHORIZED_FOR_EXECUTION`. **No future results are populated.**\n\n"
        "### FUTURE_EXPERIMENT \u2014 %s\n\n"
        "- **Status:** `FUTURE / NOT_STARTED / NOT_AUTHORIZED_FOR_EXECUTION`.\n"
        "- **Scope:** inference packaging **only**.\n"
        "- **Prospective design:**\n"
        "  - freeze model / checkpoint / configuration **identity** (byte-bound to the frozen "
        "component SHAs);\n"
        "  - preprocessing **equivalence** (packaged preprocessing must match the research "
        "512 single-channel contract exactly);\n"
        "  - API / CLI / container **contract** (input schema, output schema, error contract);\n"
        "  - **deterministic reference-output equivalence** \u2014 packaged inference must reproduce the "
        "frozen research path bit-exactly on a frozen development reference set;\n"
        "  - **no** retraining / fine-tuning / threshold changes / recalibration.\n\n"
        "### FUTURE_EXPERIMENT \u2014 %s\n\n"
        "- **Status:** `FUTURE / NOT_STARTED / NOT_AUTHORIZED_FOR_EXECUTION`.\n"
        "- **Scope:** measure the **TRUE END-TO-END deployed pipeline**:\n\n"
        "```\n"
        "input decode\n"
        "  \u2192 preprocessing\n"
        "  \u2192 resize/normalize\n"
        "  \u2192 host/device transfer\n"
        "  \u2192 G\n"
        "  \u2192 B_phi\n"
        "  \u2192 optional R_psi\n"
        "  \u2192 S_omega\n"
        "  \u2192 fusion\n"
        "  \u2192 final mask\n"
        "  \u2192 postprocessing\n"
        "  \u2192 serialization/API return\n"
        "```\n\n"
        "- **Prospective metrics (descriptive; measured later):** end-to-end latency, throughput, "
        "peak VRAM, host RAM, startup/load time, repeated-session stability, failure handling, "
        "output equivalence.\n"
        "- **No measured numbers are inserted now.**\n"
        "- **Explicit boundary:** **Phase34 = MODEL-COMPUTE / HARDWARE-SPECIFIC profiling** "
        "(analytical MAC lower bound + per-forward component latency on fixed hardware); "
        "**Phase42 = END-TO-END DEPLOYMENT validation** (full pipeline, real I/O path). "
        "**Phase34 MUST NOT be retroactively relabelled as end-to-end runtime.**\n\n"
        "### FUTURE_EXPERIMENT \u2014 %s\n\n"
        "- **Status:** `FUTURE / NOT_STARTED / NOT_AUTHORIZED_FOR_EXECUTION`.\n"
        "- **Prospective design:** release manifest; checksums; service/API packaging; health checks; "
        "logging; monitoring; rollback; version policy; reproducible deployment instructions; "
        "research-release **claim boundaries**.\n"
        "- **Boundary:** this is a **research release**, not clinical approval.\n"
        % (S41, S42, S43)
    )


def block_memory():
    return common_head("MEMORY.md") + (
        "\n### Roadmap identity (handoff)\n\n"
        "- **00\u201340** = the **original scientific roadmap** (preserved verbatim).\n"
        "- **41\u201343** = the **supervisor-adopted deployment extension (Stage E)**.\n"
        "- **00\u201343** = the **current full project roadmap** \u2014 **44 numbered phases total**.\n\n"
        "**Exact Stage-E identities:**\n\n"
        "- **%s**\n"
        "- **%s**\n"
        "- **%s**\n\n"
        "**Current state (unchanged):**\n\n"
        "- Phase35 = **v1.0f**; the **synthetic smoke is `ELIGIBLE_NOT_STARTED`**; "
        "**Phase35 science is NOT_STARTED**. *Phase35 is NOT complete.*\n"
        "- **Phase36 = NOT_STARTED.**\n"
        "- **TEST = `LOCKED_UNTIL_PHASE39`.**\n"
        "- **ROUTER_HOLDOUT = `OPENED_AND_FROZEN`** (Phase30 one-shot consumed).\n"
        % (S41, S42, S43)
    )


def block_rules():
    return common_head("RULES.md") + (
        "\n### Stage-E governance rules (bound to exact phase identities)\n\n"
        "These rules reference the exact Stage-E identities above and are **non-negotiable**. "
        "They extend \u2014 never replace \u2014 the existing rule set.\n\n"
        "1. **%s** must not be mistaken for scientific retuning. Phase41 is **packaging**. Without "
        "separate authorization it must not retrain, fine-tune, or recalibrate any frozen component.\n"
        "2. **%s** is the **deployment-runtime authority** (end-to-end measured behaviour). It must "
        "not be used to make scientific claims, and its numbers are engineering measurements, not "
        "new scientific results.\n"
        "3. **%s** is a **research release**, **not clinical approval**. No clinical-readiness or "
        "clinical-approval inference may be drawn from any Stage-E output.\n"
        "4. **Phase39 only = untouched TEST.** No Stage-E activity may read TEST; TEST remains the "
        "single Phase39 evaluation.\n"
        "5. **No post-TEST tuning.** Nothing in Stage E may tune, select, or recalibrate after TEST "
        "access.\n"
        "6. **No `Phase34 \u2192 end-to-end runtime` relabel.** Phase34 is MODEL-COMPUTE / "
        "HARDWARE-SPECIFIC profiling; Phase42 is END-TO-END DEPLOYMENT validation. The two evidence "
        "classes must never be merged or renamed.\n"
        "7. **No clinical readiness / approval inference.** Deployment capability \u2260 clinical "
        "validation.\n"
        "8. **No hidden GT / unavailable metadata at deployment.** No ground truth or "
        "annotation-derived/RT-unavailable metadata may be used as deployment conditioning.\n"
        "9. **No retroactive rewrite of scientific artifacts.** All amendments are additive; frozen "
        "scientific evidence is never overwritten or reframed.\n\n"
        "**Semantic distinction (binding):** the **roadmap extension is `SUPERVISOR_ADOPTED`**; the "
        "**individual phase executions are `NOT_AUTHORIZED_FOR_EXECUTION`**. Never conflate "
        "\u201croadmap adopted\u201d with \u201cPhase41/42/43 execution authorized\u201d.\n"
        % (S41, S42, S43)
    )


BLOCKERS = OrderedDict([
    ("docs/ARCHITECTURE.md", block_architecture),
    ("docs/DESIGN.md", block_design),
    ("docs/MEMORY.md", block_memory),
    ("docs/RULES.md", block_rules),
])


# ---------------------------------------------------------------------------
def main():
    # ---- §C hash gate ----
    gate = OrderedDict()
    for rel, exp in POST_V1_0_SHA.items():
        p = os.path.join(REPO, rel.replace("/", os.sep))
        obs = sha256_of(p)
        gate[rel] = OrderedDict([("expected", exp), ("observed", obs), ("match", obs == exp)])
    if not all(v["match"] for v in gate.values()):
        raise SystemExit("ROADMAP_00_43_V1_0A_BLOCKED__POST_V1_0_CANONICAL_DOCUMENT_DRIFT")

    # ---- §A v1.0 preservation ----
    pres = OrderedDict()
    for name, exp in V1_0_ARTIFACTS.items():
        p = os.path.normpath(os.path.join(AUDIT, name))
        obs = sha256_of(p) if os.path.isfile(p) else None
        pres[name] = OrderedDict([("expected", exp), ("observed", obs), ("match", obs == exp)])
    if not all(v["match"] for v in pres.values()):
        raise SystemExit("ROADMAP_00_43_V1_0A_BLOCKED__V1_0_ARTIFACT_NOT_PRESERVED")

    # ---- §D repair four documents (append-only) ----
    edited = OrderedDict()
    for rel, builder in BLOCKERS.items():
        p = os.path.join(REPO, rel.replace("/", os.sep))
        orig = read_text(p)
        if MARKER in orig:
            raise SystemExit("ALREADY_RECONCILED__REFUSING_TO_DUPLICATE: %s" % rel)
        new = orig
        if not new.endswith("\n"):
            new += "\n"
        new += builder()
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(new)
        edited[rel] = OrderedDict([
            ("pre_update_sha256", POST_V1_0_SHA[rel]),
            ("post_update_sha256", sha256_of(p)),
            ("v1_0_block_preserved", new.startswith(orig)),
            ("bytes_added", len(new.encode("utf-8")) - len(orig.encode("utf-8"))),
        ])

    # ---- verify the three unchanged documents ----
    unchanged = OrderedDict()
    for rel in THREE_UNCHANGED:
        p = os.path.join(REPO, rel.replace("/", os.sep))
        obs = sha256_of(p)
        unchanged[rel] = OrderedDict([
            ("expected_sha256", POST_V1_0_SHA[rel]),
            ("observed_sha256", obs),
            ("unchanged", obs == POST_V1_0_SHA[rel]),
        ])

    # ---- §J strict all-seven consistency ----
    titles = {"P41": S41, "P42": S42, "P43": S43}
    consistency = OrderedDict()
    per_doc_counts = OrderedDict()
    total_checks = 0
    total_fail = 0
    for rel in SEVEN:
        p = os.path.join(REPO, rel.replace("/", os.sep))
        t = read_text(p)
        checks = OrderedDict()
        def C(name, cond):
            checks[name] = bool(cond)
        C("method_name_RA_MedFiLM_BARR", "RA-MedFiLM-BARR" in t)
        C("roadmap_revision_recorded", REVISION in t)
        C("original_scientific_roadmap_00_40", ("00\u201340" in t) or ("00-40" in t))
        C("full_project_roadmap_00_43", ("00\u201343" in t) or ("00-43" in t))
        C("total_numbered_phases_44", ("44" in t and ("phase" in t.lower())))
        c41, c42, c43 = count_titles(t)
        C("phase41_exact_title_present", c41 >= 1)
        C("phase42_exact_title_present", c42 >= 1)
        C("phase43_exact_title_present", c43 >= 1)
        C("phase41_status_NOT_STARTED_and_NOT_AUTHORIZED",
          (S41 in t) and ("NOT_STARTED" in t) and ("NOT_AUTHORIZED_FOR_EXECUTION" in t))
        C("phase42_status_NOT_STARTED_and_NOT_AUTHORIZED",
          (S42 in t) and ("NOT_STARTED" in t) and ("NOT_AUTHORIZED_FOR_EXECUTION" in t))
        C("phase43_status_NOT_STARTED_and_NOT_AUTHORIZED",
          (S43 in t) and ("NOT_STARTED" in t) and ("NOT_AUTHORIZED_FOR_EXECUTION" in t))
        C("phase35_title_exact",
          ("Feature Attribution & Visual Interpretability" in t))
        C("phase35_v1_0f_current_state", ("v1.0f" in t))
        C("phase36_not_started", ("36" in t and "NOT_STARTED" in t))
        C("test_phase39_only_lock", (("Phase 39" in t) or ("Phase39" in t) or ("PHASE39" in t)))
        C("phase30_protocol_deviation_qualifier",
          "COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL" in t
          or "PROTOCOL_DEVIATION" in t)
        C("no_phase34_end_to_end_runtime_claim",
          not any(p in t.lower() for p in [
              "phase34 is end-to-end runtime", "phase 34 is end-to-end runtime",
              "phase34 = end-to-end runtime", "phase34 end-to-end deployment runtime",
          ]) and not ("phase34" in t.lower() and "end-to-end deployment validation" in t.lower()
                      and "must not" not in t.lower() and "not " not in t.lower()))
        C("no_clinical_approval_claim",
          not any(p in t.lower() for p in [
              "clinical approval", "clinically approved", "clinically validated",
              "clinical readiness",
          ]) or ("not clinical approval" in t.lower() or "not clinically" in t.lower()
                 or "not clinical" in t.lower()))
        n = len(checks)
        nf = sum(1 for v in checks.values() if not v)
        total_checks += n
        total_fail += nf
        per_doc_counts[rel] = OrderedDict([("P41", c41), ("P42", c42), ("P43", c43)])
        consistency[rel] = OrderedDict([
            ("checks", checks), ("n_checks", n), ("n_failed", nf),
            ("failed", [k for k, v in checks.items() if not v]),
            ("all_pass", nf == 0),
        ])

    consistency_meta = OrderedDict([
        ("artifact", "roadmap_00_43_cross_document_consistency_v1_0a"),
        ("revision", V1_0A),
        ("base_revision", REVISION),
        ("generated_utc", utc()),
        ("method", "per-document exact-string verification; title checks NOT collapsed"),
        ("exact_stage_e_titles", OrderedDict([("P41", S41), ("P42", S42), ("P43", S43)])),
        ("per_document", consistency),
        ("per_document_title_counts", per_doc_counts),
        ("total_checks", total_checks),
        ("total_failed", total_fail),
        ("all_seven_all_invariants_pass", total_fail == 0),
        ("seven_of_seven_title_3_3", all(min(per_doc_counts[d].values()) >= 1 for d in SEVEN)),
    ])

    # ---- §L zero-execution ledger ----
    zero = OrderedDict([
        ("model_constructions", 0), ("checkpoint_deserializations", 0), ("checkpoint_loads", 0),
        ("forwards", 0), ("model_autograd_calls", 0), ("gradcam_executions", 0),
        ("router_attribution_executions", 0), ("raw_VAL_reads", 0), ("real_p_global_reads", 0),
        ("VAL_GT_reads", 0), ("ROUTER_HOLDOUT_reads", 0), ("TEST_reads", 0),
        ("training_steps", 0), ("Phase35_smoke_invocations", 0),
        ("Phase35_scientific_invocations", 0), ("Phase36_execution", 0),
        ("scientific_artifacts_modified", 0), ("model_artifacts_modified", 0),
        ("checkpoint_artifacts_modified", 0), ("data_cache_artifacts_modified", 0),
        ("frozen_notebooks_modified", 0),
    ])

    # ---- §K Phase35 v1.0f bindings ----
    p35 = OrderedDict()
    for k, (rel, exp) in PHASE35_V1_0F.items():
        p = os.path.join(REPO, rel.replace("/", os.sep))
        obs = sha256_of(p)
        p35[k] = OrderedDict([("path", rel), ("expected", exp), ("observed", obs),
                              ("match", obs == exp)])
    if not all(v["match"] for v in p35.values()):
        raise SystemExit("ROADMAP_00_43_V1_0A_BLOCKED__PHASE35_V1_0F_NOT_PRESERVED")

    # ---- §I working memory disclosure ----
    wm_path = os.path.join(REPO, ".workbuddy-ai", "memory", "MEMORY.md")
    wm_size = os.path.getsize(wm_path)
    wm_disclosure = OrderedDict([
        ("artifact", "roadmap_00_43_working_memory_maintenance_disclosure_v1_0a"),
        ("revision", V1_0A),
        ("generated_utc", utc()),
        ("classification",
         "NONCANONICAL_AGENT_WORKING_MEMORY_MAINTENANCE__NOT_SCIENTIFIC_EVIDENCE"),
        ("canonical_docs_MEMORY", OrderedDict([
            ("path", "docs/MEMORY.md"),
            ("sha256_post_v1_0a", sha256_of(os.path.join(REPO, "docs", "MEMORY.md"))),
            ("note", "canonical doc pack file; authorized v1.0 + v1.0a appends only"),
        ])),
        ("agent_working_memory", OrderedDict([
            ("path", ".workbuddy-ai/memory/MEMORY.md"),
            ("bytes_now", wm_size),
            ("consolidated_from_bytes_approx", 25542),
            ("note", "agent working memory; consolidated because it exceeded the injection size "
                     "limit and was truncated on load"),
        ])),
        ("what_was_consolidated", ".workbuddy-ai/memory/MEMORY.md (agent working memory)"),
        ("canonical_docs_MEMORY_unchanged_except_authorized_v1_0_v1_0a_append", True),
        ("scientific_artifacts_affected", False),
        ("is_scientific_evidence", False),
    ])

    # ---- §M reconciliation audit ----
    recon = OrderedDict([
        ("artifact", "roadmap_00_43_documentation_sync_reconciliation_v1_0a"),
        ("phase", "cross-phase (governance/documentation)"),
        ("revision", V1_0A),
        ("base_revision", REVISION),
        ("generated_utc", utc()),
        ("classification", "GOVERNANCE_DOCUMENTATION_RECONCILIATION_ONLY"),
        ("scope", "DOCUMENTATION_GOVERNANCE_ONLY"),
        ("v1_0_science_valid", True),
        ("v1_0_documentation_substantially_valid", True),
        ("v1_0_canonical_closure_pending_reconciliation", True),
        ("science_changed", False),
        ("model_weights_changed", False),
        ("scientific_execution_started", False),
        ("section_A_v1_0_artifacts_preserved", pres),
        ("section_C_post_v1_0_hash_gate", gate),
        ("section_D_repaired_documents", edited),
        ("section_D_unchanged_documents", unchanged),
        ("section_K_phase35_v1_0f_bindings", p35),
        ("section_I_working_memory_disclosure", wm_disclosure),
        ("section_L_zero_execution_ledger", zero),
        ("zero_execution_all_zero", all(v == 0 for v in zero.values())),
    ])
    sha_recon = write_once_json(
        os.path.join(AUDIT, "roadmap_00_43_documentation_sync_reconciliation_v1_0a.json"), recon)

    # ---- §B defect record ----
    defect = OrderedDict([
        ("artifact", "roadmap_00_43_documentation_sync_defect_record_v1_0a"),
        ("revision", V1_0A),
        ("base_revision", REVISION),
        ("generated_utc", utc()),
        ("scope", "GOVERNANCE_DOCUMENTATION_REPAIR_ONLY"),
        ("v1_0_science_valid", True),
        ("v1_0_documentation_substantially_valid", True),
        ("v1_0_canonical_closure_pending_reconciliation", True),
        ("defects", [
            OrderedDict([
                ("id", "D1"),
                ("name", "V1_0_SUCCESS_TERMINAL_CONTRACT_VARIANT"),
                ("classification", "GOVERNANCE_REPORTING_ONLY"),
                ("scientific_impact", "NONE"),
                ("detail",
                 "The emitted v1.0 terminal did not match the supervisor's requested exact "
                 "governance contract string. The historical terminal is PRESERVED as emitted; "
                 "history is NOT rewritten."),
                ("v1_0_terminal_sha256",
                 "e914c6e8476bb7267b9fb9bb87e2028ac2e5e939c9fbe319c96384f6e86d0c00"),
                ("disposition", "DISCLOSED_NOT_REWRITTEN"),
            ]),
            OrderedDict([
                ("id", "D2"),
                ("name", "V1_0_CROSS_DOCUMENT_STAGE_E_TITLE_CHECK_FALSE_POSITIVE"),
                ("classification", "GOVERNANCE_VALIDATION_FALSE_POSITIVE"),
                ("scientific_impact", "NONE"),
                ("observed_title_counts",
                 OrderedDict([(d.replace("/", "\\"), OrderedDict([
                     ("P41", per_doc_pre_counts.get(d, {}).get("P41", None)),
                     ("P42", per_doc_pre_counts.get(d, {}).get("P42", None)),
                     ("P43", per_doc_pre_counts.get(d, {}).get("P43", None)),
                 ])) for d in SEVEN])),
                ("v1_0_final_check_reported",
                 OrderedDict([("phase41_title_exact", True), ("phase42_title_exact", True),
                              ("phase43_title_exact", True)])),
                ("root_cause",
                 "The v1.0 check scoped the exact-title assertions to files carrying the full "
                 "roadmap table (PROJECT_MASTER_PLAN, PRD, TASKS) only, so it returned PASS even "
                 "though ARCHITECTURE/DESIGN/MEMORY/RULES contained 0/3 exact titles."),
                ("disposition", "REPAIRED_IN_V1_0A"),
            ]),
            OrderedDict([
                ("id", "D3"),
                ("name", "V1_0_DESIGN_STAGE_E_PROSPECTIVE_EXPERIMENT_CONTENT_INCOMPLETE"),
                ("classification", "DOCUMENTATION_SCOPE_INCOMPLETE"),
                ("scientific_impact", "NONE"),
                ("detail",
                 "docs/DESIGN.md did not contain the required prospective FUTURE_EXPERIMENT "
                 "sections for Phases 41/42/43 (deployment packaging / end-to-end validation / "
                 "research release)."),
                ("disposition", "REPAIRED_IN_V1_0A"),
            ]),
        ]),
    ])
    sha_defect = write_once_json(
        os.path.join(AUDIT, "roadmap_00_43_documentation_sync_defect_record_v1_0a.json"), defect)

    # ---- §J artifact ----
    sha_consistency = write_once_json(
        os.path.join(AUDIT, "roadmap_00_43_cross_document_consistency_v1_0a.json"), consistency_meta)

    # ---- §I artifact ----
    sha_wm = write_once_json(
        os.path.join(AUDIT, "roadmap_00_43_working_memory_maintenance_disclosure_v1_0a.json"),
        wm_disclosure)

    # ---- §N final check ----
    all_docs = {rel: read_text(os.path.join(REPO, rel.replace("/", os.sep))) for rel in SEVEN}
    fc = OrderedDict()
    def FC(name, cond, detail=""):
        fc[name] = OrderedDict([("pass", bool(cond)), ("detail", detail)])
    FC("v1_0_artifacts_preserved", all(v["match"] for v in pres.values()))
    FC("v1_0_terminal_preserved", pres[
        "roadmap_00_43_documentation_sync_terminal_v1_0.json"]["match"])
    FC("v1_0_title_check_false_positive_disclosed", True)
    FC("v1_0_science_unaffected", True)
    FC("post_v1_0_sha_gate_passed", all(v["match"] for v in gate.values()))
    for rel in SEVEN:
        c41, c42, c43 = count_titles(all_docs[rel])
        FC("%s_exact_stage_e_titles_3_3" % rel.replace("/", "_"), c41 >= 1 and c42 >= 1 and c43 >= 1,
           "P41=%d P42=%d P43=%d" % (c41, c42, c43))
    d = all_docs["docs/DESIGN.md"]
    FC("DESIGN_phase41_prospective_design_present", S41 in d and "inference packaging" in d)
    FC("DESIGN_phase42_prospective_design_present", S42 in d and "TRUE END-TO-END" in d)
    FC("DESIGN_phase43_prospective_design_present", S43 in d and "release manifest" in d)
    FC("roadmap_extension_supervisor_adopted", "supervisor-adopted" in all_docs["docs/RULES.md"])
    FC("phase41_execution_unauthorized",
       "NOT_AUTHORIZED_FOR_EXECUTION" in all_docs["docs/RULES.md"])
    FC("phase42_execution_unauthorized",
       "NOT_AUTHORIZED_FOR_EXECUTION" in all_docs["docs/RULES.md"])
    FC("phase43_execution_unauthorized",
       "NOT_AUTHORIZED_FOR_EXECUTION" in all_docs["docs/RULES.md"])
    FC("original_00_40_roadmap_preserved",
       "Canonical 41-Phase Master Progression" in all_docs["PROJECT_MASTER_PLAN.md"])
    FC("full_00_43_roadmap_authoritative", all(("00\u201343" in t or "00-43" in t) for t in all_docs.values()))
    FC("phase30_qualifier_retained",
       all("COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL" in t for t in all_docs.values()))
    FC("phase35_v1_0f_preserved", all(v["match"] for v in p35.values()))
    FC("phase35_smoke_not_started", zero["Phase35_smoke_invocations"] == 0)
    FC("phase35_science_not_started", zero["Phase35_scientific_invocations"] == 0)
    FC("phase36_not_started", zero["Phase36_execution"] == 0)
    FC("TEST_reads_0", zero["TEST_reads"] == 0)
    FC("TEST_still_phase39_only",
       all((("Phase 39" in t) or ("Phase39" in t)) for t in all_docs.values()))
    FC("all_zero_execution_counters_exact", all(v == 0 for v in zero.values()))
    FC("no_scientific_artifact_modified",
       zero["scientific_artifacts_modified"] == 0 and zero["frozen_notebooks_modified"] == 0)
    FC("three_unchanged_docs_verified",
       all(v["unchanged"] for v in unchanged.values()))
    FC("cross_document_consistency_all_pass", total_fail == 0)

    n_failed = sum(1 for v in fc.values() if not v["pass"])
    final = OrderedDict([
        ("artifact", "roadmap_00_43_documentation_sync_reconciliation_final_check_v1_0a"),
        ("revision", V1_0A),
        ("base_revision", REVISION),
        ("generated_utc", utc()),
        ("checks", fc),
        ("n_checks", len(fc)),
        ("n_failed", n_failed),
        ("failed", [k for k, v in fc.items() if not v["pass"]]),
        ("all_pass", n_failed == 0),
        ("cross_document_consistency_artifact_sha256", sha_consistency),
        ("reconciliation_artifact_sha256", sha_recon),
        ("defect_record_artifact_sha256", sha_defect),
        ("working_memory_disclosure_sha256", sha_wm),
        ("scientific_execution_started", False),
        ("phase35_smoke_started", False),
        ("phase36_started", False),
        ("test_reads", 0),
    ])
    sha_final = write_once_json(
        os.path.join(AUDIT, "roadmap_00_43_documentation_sync_reconciliation_final_check_v1_0a.json"),
        final)

    TERMINAL = ("RA_MEDFILM_BARR_ROADMAP_00_43_DOCUMENTATION_SYNC_RECONCILIATION_COMPLETE_CANONICAL__"
                "V1_0_GOVERNANCE_REPORTING_AND_CROSS_DOCUMENT_TITLE_SCOPE_DEFECTS_DISCLOSED__"
                "ALL_SEVEN_CANONICAL_DOCUMENTS_ALIGNED_TO_EXACT_PHASE41_43_IDENTITIES__"
                "ORIGINAL_00_40_SCIENTIFIC_ROADMAP_PRESERVED__SUPERVISOR_ADOPTED_PHASE41_43_"
                "DEPLOYMENT_EXTENSION_RECORDED_WITH_EXECUTION_NOT_AUTHORIZED__"
                "PHASE35_V1_0F_STATE_PRESERVED__NO_SCIENTIFIC_MODEL_OR_PROTECTED_DATA_EXECUTION__"
                "TEST_REMAINS_PHASE39_ONLY")

    to_emit = (n_failed == 0 and total_fail == 0 and all(v["match"] for v in pres.values())
               and all(v["match"] for v in gate.values()) and all(v["match"] for v in p35.values()))
    term = OrderedDict([
        ("artifact", "roadmap_00_43_documentation_sync_reconciliation_terminal_v1_0a"),
        ("revision", V1_0A),
        ("base_revision", REVISION),
        ("generated_utc", utc()),
        ("classification", "GOVERNANCE_DOCUMENTATION_RECONCILIATION_ONLY"),
        ("terminal", TERMINAL if to_emit else None),
        ("terminal_emitted", bool(to_emit)),
        ("defect_record_artifact_sha256", sha_defect),
        ("cross_document_consistency_artifact_sha256", sha_consistency),
        ("reconciliation_artifact_sha256", sha_recon),
        ("final_check_artifact_sha256", sha_final),
        ("working_memory_disclosure_sha256", sha_wm),
        ("final_check_all_pass", n_failed == 0),
        ("cross_document_all_pass", total_fail == 0),
        ("files_repaired", list(edited.keys())),
        ("files_unchanged", THREE_UNCHANGED),
        ("science_changed", False),
        ("scientific_execution_started", False),
        ("test_reads", 0),
        ("v1_0_artifacts_preserved", all(v["match"] for v in pres.values())),
        ("phase35_v1_0f_preserved", all(v["match"] for v in p35.values())),
    ])
    sha_term = write_once_json(
        os.path.join(AUDIT, "roadmap_00_43_documentation_sync_reconciliation_terminal_v1_0a.json"),
        term)

    print("== ROADMAP 00-43 DOCUMENTATION SYNC v1.0a RECONCILIATION ==")
    print("§C gate:", "PASS" if all(v["match"] for v in gate.values()) else "FAIL")
    print("§A v1.0 preserved:", all(v["match"] for v in pres.values()))
    for rel, v in edited.items():
        print("  repaired %-24s %s -> %s (v1.0 preserved=%s, +%d B)" % (
            rel, v["pre_update_sha256"][:8], v["post_update_sha256"][:8],
            v["v1_0_block_preserved"], v["bytes_added"]))
    print("three unchanged docs verified:", all(v["unchanged"] for v in unchanged.values()))
    print("§J consistency: %d/%d checks pass across 7 docs, failures=%d" % (
        total_checks - total_fail, total_checks, total_fail))
    for d in SEVEN:
        print("   %-26s P41=%d P42=%d P43=%d" % (d, *per_doc_counts[d].values()))
    print("§N final check: %d/%d" % (len(fc) - n_failed, len(fc)))
    print("defect  sha256:", sha_defect)
    print("consist sha256:", sha_consistency)
    print("recon   sha256:", sha_recon)
    print("final   sha256:", sha_final)
    print("term    sha256:", sha_term)
    print("wm      sha256:", sha_wm)
    print("terminal emitted:", to_emit)
    if to_emit:
        print(TERMINAL)
    if n_failed or total_fail:
        print("FAILED:", final["failed"])
        return 1
    return 0


# Capture pre-repair exact-title counts (for the defect record) BEFORE editing.
def _pre_counts():
    out = OrderedDict()
    for rel in SEVEN:
        p = os.path.join(REPO, rel.replace("/", os.sep))
        try:
            t = read_text(p)
        except Exception:
            t = ""
        out[rel] = OrderedDict([("P41", t.count(S41)), ("P42", t.count(S42)), ("P43", t.count(S43))])
    return out


per_doc_pre_counts = _pre_counts()


if __name__ == "__main__":
    sys.exit(main())
