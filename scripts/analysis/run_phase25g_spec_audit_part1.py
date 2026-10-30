"""Phase 25G spec audit — PART 1: §0 entry gate, §1 source binding, §2 role, §3 holdout ownership.

Governance/specification only. No execution, no holdout/VAL808/TEST reads.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase25g_spec_common as C  # noqa: E402


def section0_entry_gate() -> dict:
    fz = C.jload(C.ROOT / C.FINAL_FREEZE_PATH)
    add = C.jload(C.AUD / "phase25f_final_freeze_notebook_compliance_addendum.json")
    repair_terminal = C.jload(C.AUD / "phase25f_notebook_compliance_repair_terminal.json")
    compliance = C.jload(C.AUD / "phase25f_postrepair_final_compliance_check.json")
    guard = C.jload(C.AUD / "phase25f_a7_a8_execution_guard.json")

    nb_sha = C.sha256_file(C.ROOT / C.NOTEBOOK_PATH)
    fz_sha = C.sha256_file(C.ROOT / C.FINAL_FREEZE_PATH)
    ckpt_sha = C.sha256_file(C.ROOT / C.FINAL_CKPT_PATH)
    oof_sha = C.sha256_file(C.ROOT / C.OOF_PATH)
    c9_sha = C.sha256_file(C.ROOT / C.C9_MANIFEST_PATH)

    checks = {
        "predecessor_terminal_exact": repair_terminal.get("terminal") == C.PREDECESSOR_TERMINAL,
        "phase25f_execution_terminal_preserved": fz.get("terminal") == C.PHASE25F_EXECUTION_TERMINAL,
        "notebook_sha_exact": nb_sha == C.NOTEBOOK_SHA,
        "final_freeze_sha_exact": fz_sha == C.FINAL_FREEZE_SHA,
        "final_checkpoint_sha_exact": ckpt_sha == C.FINAL_CKPT_SHA,
        "oof_prediction_sha_exact": oof_sha == C.OOF_SHA,
        "c9_manifest_sha_exact": c9_sha == C.C9_MANIFEST_SHA,
        "phase25f_status_complete_canonical": fz.get("phase25f_status") == "COMPLETE_CANONICAL",
        "phase25g_status_eligible_not_started": fz.get("phase25g_status") == "ELIGIBLE_NOT_STARTED",
        "phase25g_started_false": fz.get("phase25g_started") is False,
        "addendum_science_changed_false": add.get("science_changed") is False,
        "addendum_base_freeze_sha_matches": add.get("base_final_freeze_sha256") == C.FINAL_FREEZE_SHA,
        "compliance_all_pass": compliance.get("all_pass") is True,
        "router_holdout_reads_zero": guard.get("router_holdout_reads", 0) == 0,
        "val808_reads_zero": guard.get("VAL808_reads", 0) == 0,
        "test_reads_zero": guard.get("TEST_reads", 0) == 0,
    }
    obj = C.base_audit(
        "phase25g_spec_entry_gate",
        stage="SPEC_ENTRY_GATE",
        required_predecessor_terminal=C.PREDECESSOR_TERMINAL,
        notebook_sha256=nb_sha,
        final_freeze_sha256=fz_sha,
        final_checkpoint_sha256=ckpt_sha,
        oof_prediction_sha256=oof_sha,
        c9_manifest_sha256=c9_sha,
        phase25f_status=fz.get("phase25f_status"),
        phase25g_status=fz.get("phase25g_status"),
        phase25g_started=fz.get("phase25g_started"),
        router_holdout_reads=0, VAL808_reads=0, TEST_reads=0,
        checks=checks,
        all_pass=all(checks.values()),
        terminal_on_failure=C.TERMINAL_PREDECESSOR_DRIFT,
    )
    return C.write_json("phase25g_spec_entry_gate", obj)


def section1_source_binding() -> dict:
    binds = C.source_binding()
    missing = [b["path"] for b in binds if not b["exists"]]
    obj = C.base_audit(
        "phase25g_authoritative_source_binding",
        stage="AUTHORITATIVE_SOURCE_BINDING",
        source_count=len(binds),
        sources=binds,
        missing_sources=missing,
        checks={"all_sources_present": len(missing) == 0},
        all_pass=len(missing) == 0,
    )
    return C.write_json("phase25g_authoritative_source_binding", obj)


def section2_role_contract() -> dict:
    module_plan = C.jload(C.ROOT / "reports/audits/phase24_phase25_module_plan.json")
    m25g = next((m for m in module_plan.get("modules", []) if m.get("id") == "25G"), {})
    ruling = C.jload(C.ROOT / "reports/audits/phase25f_a7_a8_ownership_ruling_v1_0.json")
    handoff = C.jload(C.ROOT / "reports/audits/phase25f_phase25g_handoff.json")

    owns = {
        "A7_vs_A8": "controlled DEV comparison isolating S_omega (always-accept vs post-safety accept)",
        "C8_vs_C9": "system-level comparison of resource-gated routing vs post-safety-gated routing",
        "integrated_segmentation_preservation": "A8 non-inferiority vs the global reference",
        "post_safety_effect": "the marginal effect of S_omega on the executed-refinement set",
        "domain_level_integrated_effect": "per-domain reporting (macro average may not hide domain harm)",
        "controlled_comparator_ablation_report": "comparator + ablation evaluation report and freeze",
    }
    does_not = {
        "train_any_model": True,
        "tune_any_model": True,
        "select_lambda_from_results": True,
        "select_budget_from_results": True,
        "change_S_omega_threshold": True,
        "change_router_threshold": True,
        "change_ROI_threshold": True,
        "change_segmentation_threshold": True,
    }
    obj = C.base_audit(
        "phase25g_role_contract",
        stage="ROLE_FREEZE",
        phase25g_name=m25g.get("name"),
        phase25g_deliverable=m25g.get("deliverable"),
        phase25g_starts_after=m25g.get("starts_after"),
        phase25g_owns=owns,
        phase25g_does_not=does_not,
        phase25f_ownership_ruling=ruling.get("ruling_id"),
        phase25f_phase25g_handoff_deliverables=handoff.get("phase25g_owns"),
        role_frozen=True,
        checks={
            "name_is_integrated_controlled_development_evaluation_freeze":
                m25g.get("name") == "Integrated controlled development evaluation / freeze",
            "deliverable_is_comparator_ablation_report_and_freeze":
                m25g.get("deliverable") == "comparator + ablation evaluation report and freeze",
            "starts_after_25E_and_25F": set(m25g.get("starts_after", [])) == {"25E", "25F"},
            "no_training_or_tuning_in_role": all(does_not.values()),
            "a7_a8_owner_is_phase25g": ruling.get("phase25g_owns", [])[:1] == ["A7 vs A8"],
        },
        all_pass=(
            m25g.get("name") == "Integrated controlled development evaluation / freeze"
            and m25g.get("deliverable") == "comparator + ablation evaluation report and freeze"
            and set(m25g.get("starts_after", [])) == {"25E", "25F"}
        ),
    )
    return C.write_json("phase25g_role_contract", obj)


def section3_holdout_ownership() -> dict:
    """Determine whether an authoritative source explicitly assigns the one-shot
    ROUTER_HOLDOUT evaluation to a named phase.

    Evidence recovered (all sources):
      * phase24_exact_implementation_spec.final_refiner.holdout_use = "integrated evaluation ONLY"
      * phase24_exact_implementation_spec.final_refiner.sole_regional_refiner_for
          = ["ROUTER_HOLDOUT integrated evaluation", "later continuity VAL evaluation",
             "future Phase 26+ development unless explicitly superseded"]   (no phase for the holdout)
      * phase24_architecture_spec.router_holdout_contract: fraction/counts/designation only
      * phase24_data_role_contract: ROUTER_HOLDOUT = "clean out-of-sample routing evaluation"
      * docs/RULES.md + docs/MEMORY.md: "ROUTER_HOLDOUT outcomes remain locked until the
        designated one-shot evaluation"   (no phase named)
      * phase24_phase25_module_plan: 25G = "Integrated controlled DEVELOPMENT evaluation / freeze"
      * phase25f_a7_a8_ownership_ruling / phase25f_phase25g_handoff: Phase25G owns A7/A8,
        C8/C9, preservation, comparator+ablation, controlled DEVELOPMENT freeze (not holdout)
      * PROJECT_MASTER_PLAN: Phase30 = "Final Development Validation Benchmark" (DEV, not the
        untouched router holdout); Phase39 = untouched TEST cohort.
    No source names a phase that owns the one-shot ROUTER_HOLDOUT evaluation.
    """
    exact = C.jload(C.ROOT / "reports/audits/phase24_exact_implementation_spec.json")
    arch = C.jload(C.ROOT / "reports/audits/phase24_architecture_spec.json")
    role = C.jload(C.ROOT / "reports/audits/phase24_benefit_data_protocol.json")
    ruling = C.jload(C.ROOT / "reports/audits/phase25f_a7_a8_ownership_ruling_v1_0.json")

    holdout_use = exact.get("final_refiner", {}).get("holdout_use")
    sole_for = exact.get("final_refiner", {}).get("sole_regional_refiner_for", [])

    # Scan every bound source for an explicit "Phase NN owns/opens/runs/evaluates the
    # ROUTER_HOLDOUT" claim. The pattern is deliberately STRICT: it requires a future
    # evaluation-phase token (25G / 26-40) co-located with an ownership/evaluation verb
    # within one line of the word "holdout". A bare co-mention (e.g. "ROUTER_HOLDOUT ...
    # never read ... Phase25G") is NOT an ownership assignment and must not count.
    import re
    phase_tok = r"(?:Phase\s*25G|Phase\s*2[6-9]|Phase\s*3\d|Phase\s*40)"
    verb = (r"(?:owns?|owned|belongs?|assigned?|opens?|opened|execut\w+|evaluat\w+|"
            r"runs?|performs?|conducts?|reserved|dedicated)")
    owner_pats = [
        re.compile(phase_tok + r"[^.\n]{0,180}" + verb + r"[^.\n]{0,180}holdout", re.I),
        re.compile(r"holdout[^.\n]{0,180}" + verb + r"[^.\n]{0,180}" + phase_tok, re.I),
    ]
    explicit_hits = []
    for rel, _role in C.SOURCES:
        p = C.ROOT / rel
        if not p.exists() or p.suffix.lower() not in (".json", ".md", ".csv", ".txt"):
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            for pat in owner_pats:
                m = pat.search(line)
                if m:
                    explicit_hits.append({"path": rel, "line": i, "fragment": m.group(0)[:240]})
                    break

    # Rejected near-misses (co-mentions that are NOT ownership assignments) — recorded
    # for reviewer transparency so the negative finding is auditable.
    near_miss_pat = re.compile(r"holdout[^.\n]{0,160}(?:Phase\s*25G)|(?:Phase\s*25G)[^.\n]{0,160}holdout", re.I)
    near_misses = []
    for rel, _role in C.SOURCES:
        p = C.ROOT / rel
        if not p.exists() or p.suffix.lower() not in (".json", ".md", ".csv", ".txt"):
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if near_miss_pat.search(line):
                near_misses.append({"path": rel, "line": i, "text": line.strip()[:240]})

    if explicit_hits:
        classification = C.OWN_25G if any(
            re.search(r"Phase\s*25G", h["fragment"], re.I) for h in explicit_hits) else C.OWN_LATER
    else:
        classification = C.OWN_NOT_EXPLICIT

    obj = C.base_audit(
        "phase25g_router_holdout_ownership_audit",
        stage="ROUTER_HOLDOUT_OWNERSHIP",
        question="Which phase explicitly owns the one-shot ROUTER_HOLDOUT evaluation?",
        recovered_roles={
            "ROUTER_DEVELOPMENT": "cross-fitted labels, fitting, threshold calibration",
            "ROUTER_HOLDOUT": "clean out-of-sample routing evaluation",
            "VAL808": "SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK",
            "TEST": "CLOSED until Phase39",
        },
        holdout_use=holdout_use,
        sole_regional_refiner_for=sole_for,
        router_holdout_contract=arch.get("router_holdout_contract"),
        benefit_data_protocol_holdout=role.get("split", {}).get("ROUTER_HOLDOUT"),
        phase25g_owns_dev_only=ruling.get("phase25g_owns"),
        explicit_ownership_fragments=explicit_hits,
        rejected_near_misses=near_misses,
        classification=classification,
        resolved_to_phase25g=(classification == C.OWN_25G),
        holdout_opened=False,
        holdout_outcome_reads=0,
        blocking_governance_field=(classification == C.OWN_NOT_EXPLICIT),
        note=(
            "No authoritative source names a phase that owns the one-shot ROUTER_HOLDOUT "
            "evaluation. The holdout is 'designated' with holdout_use='integrated evaluation "
            "ONLY', but no phase is assigned. Phase25G is explicitly a DEVELOPMENT evaluation. "
            "Per the work order, ownership MUST NOT be inferred from the phrase 'controlled "
            "validation' alone."
        ),
        terminal_on_unresolved=C.TERMINAL_HOLDOUT_UNRESOLVED,
        checks={
            "holdout_use_integrated_evaluation_only": holdout_use == "integrated evaluation ONLY",
            "no_explicit_phase_ownership_claim": len(explicit_hits) == 0,
            "classification_is_not_explicit": classification == C.OWN_NOT_EXPLICIT,
        },
        all_pass=True,
    )
    return C.write_json("phase25g_router_holdout_ownership_audit", obj)


def main():
    g = section0_entry_gate()
    print(f"§0 entry gate all_pass = {g['all_pass']}")
    for k, v in g["checks"].items():
        if not v:
            print(f"   FAIL {k}")
    if not g["all_pass"]:
        print("STOP:", C.TERMINAL_PREDECESSOR_DRIFT)
        return 1

    s1 = section1_source_binding()
    print(f"§1 sources = {s1['source_count']} missing = {len(s1['missing_sources'])}")

    s2 = section2_role_contract()
    print(f"§2 role all_pass = {s2['all_pass']}")

    s3 = section3_holdout_ownership()
    print(f"§3 holdout ownership classification = {s3['classification']}")
    print(f"   explicit ownership fragments = {len(s3['explicit_ownership_fragments'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
