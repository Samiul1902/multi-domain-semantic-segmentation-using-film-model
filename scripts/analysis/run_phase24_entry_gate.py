"""Phase 24 — fail-closed entry gate.

Verifies every predecessor binding before ANY Phase-24 artifact is created.

Phase 21 : complete/frozen, Global MedFiLM best.pt SHA unchanged.
Phase 22 : complete/frozen, semantic repair + canonical notebook complete,
           diagnostic protocol unchanged, TEST counters all zero.
Phase 23 : novelty verdict present + correct, max claim level 2, RENAME,
           PREFER_PAIRED_REFINEMENT_GAIN / USE_BENEFIT_AWARE_ONLY,
           latest notebook SHA e9f78cce..., reviewer-visuals terminal present,
           phase24_allowed = true.
Plus     : no phase25_* artifact, no Phase25 work started, TEST all zero.

FAILS CLOSED (writes verdict PHASE24_ENTRY_GATE_FAIL and exits non-zero) if any
required binding is invalid. Never repairs frozen science.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase24_entry_gate.py
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"

PHASE21_BEST_SHA = "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"
PHASE23_NB_SHA = "e9f78ccefd96abad742fa5570a44110cd67c62f5510b99300448e44b961107b0"
PHASE23_NB_PATH = ("notebooks/phasewise/phase_23_literature_novelty/"
                   "phase23_literature_methodological_novelty_audit.ipynb")
PHASE21_CKPT = ("checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt")

PHASE22_PROTOCOL_SHA = "9d620d6c85276e1a9a086ec60172cdef3b94dc58fe8288222378d196dd4609b7"
PHASE22_FREEZE_SHA = "9a0aa2f8c1a2850770fb09f2838e95f0fe08b3b40e55ab1d10c3564841107bca"

# This gate's own output must not trip the "clean start" check on re-run.
SELF_OUTPUTS = {"phase24_entry_gate.json"}

checks: list[dict] = []


def sha(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def ck(name: str, ok: bool, detail: str = "") -> None:
    checks.append({"check": name, "pass": bool(ok), "detail": detail})


def _j(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    # ---------------- PHASE 21 ----------------
    best = ROOT / PHASE21_CKPT
    ck("phase21_checkpoint_present", best.exists(), str(best))
    ck("phase21_best_pt_sha_unchanged", sha(best) == PHASE21_BEST_SHA, (sha(best) or "")[:16])

    p21f = _j(AUD / "phase21_final_freeze.json")
    ck("phase21_freeze_present_and_verified",
       bool(p21f) and p21f.get("freeze_verified") is True,
       str(p21f.get("terminal_state"))[:60])

    # ---------------- PHASE 22 ----------------
    ck("phase22_protocol_sha_unchanged",
       sha(AUD / "phase22_diagnostic_protocol.json") == PHASE22_PROTOCOL_SHA)
    p22f = _j(AUD / "phase22_final_freeze.json")
    ck("phase22_freeze_present_and_verified",
       bool(p22f) and p22f.get("freeze_verified") is True)
    gov = p22f.get("governance", {}) or {}
    tl = gov.get("test_locks", {}) or p22f.get("test_reads", {}) or {}
    ck("phase22_test_counters_zero",
       all(int(tl.get(k, 0) or 0) == 0 for k in
           ("test_image_reads", "test_mask_reads", "test_inference", "test_visualization")),
       json.dumps(tl))
    ck("phase22_no_training", gov.get("training_jobs_started", None) == 0)
    ck("phase22_predictor_not_trained", gov.get("benefit_predictor_trained") is False)
    p22nb = (ROOT / "notebooks/phasewise/phase_22_resource_gap/"
             "phase22_resource_gap_analysis.ipynb")
    ck("phase22_canonical_notebook_present", p22nb.exists())

    # ---------------- PHASE 23 ----------------
    v = _j(AUD / "phase23_novelty_verdict.json")
    ck("phase23_verdict_present", bool(v))
    ck("phase23_overall_verdict_correct",
       v.get("overall_label") == "PARTIALLY_OCCUPIED__NARROWER_NOVELTY_POSSIBLE",
       str(v.get("overall_label")))
    ck("phase23_max_claim_level_2", v.get("maximum_defensible_claim_level") == 2)
    ck("phase23_naming_status_rename", v.get("recommended_method_name_status") == "RENAME")
    ck("phase23_phase24_allowed", v.get("phase24_allowed") is True)

    cf = _j(AUD / "phase23_counterfactual_terminology_audit.json")
    ct = _j(AUD / "phase23_certification_terminology_audit.json")
    ck("phase23_terminology_paired_refinement_gain",
       cf.get("outcome") == "PREFER_PAIRED_REFINEMENT_GAIN", str(cf.get("outcome")))
    ck("phase23_terminology_benefit_aware_only",
       ct.get("recommendation") == "USE_BENEFIT_AWARE_ONLY", str(ct.get("recommendation")))

    nb = ROOT / PHASE23_NB_PATH
    ck("phase23_notebook_present", nb.exists())
    ck("phase23_latest_notebook_sha_matches", sha(nb) == PHASE23_NB_SHA, (sha(nb) or "")[:16])

    rv = _j(AUD / "phase23_reviewer_visual_repair.json")
    ck("phase23_reviewer_visual_repair_present",
       rv.get("terminal_state") ==
       "PHASE23_REVIEWER_VISUALS_COMPLETE__SCIENCE_UNCHANGED__"
       "PHASE24_NARROWED_SPEC_ELIGIBLE_NOT_STARTED",
       str(rv.get("terminal_state"))[:70])
    integ = _j(AUD / "phase23_notebook_visual_integrity.json")
    ck("phase23_visual_integrity_passed", integ.get("all_passed") is True)
    ck("phase23_four_required_figures_valid",
       integ.get("valid_required_figures") == 4 and integ.get("corrupt") == 0)

    fc = _j(AUD / "phase23_reviewer_visual_final_check.json")
    ck("phase23_final_check_all_passed", fc.get("all_passed") is True,
       f"{fc.get('n_passed')}/{fc.get('n_checks')}")

    log = _j(AUD / "phase23_search_log.json")
    ck("phase23_corrected_query_ledger_63",
       log.get("totals", {}).get("queries_logged") == 63,
       str(log.get("totals", {}).get("queries_logged")))

    ldc = _j(AUD / "phase23_phase24_design_constraints.json")
    n_cons = len(ldc.get("high_level_constraints", []))
    ck("phase23_phase24_constraints_C1_C12_present", n_cons >= 12, f"{n_cons} constraints")

    # ---------------- governance / clean start ----------------
    p25 = sorted(p for p in list(AUD.glob("phase25_*")) + list(TAB.glob("phase25_*"))
                 + list((ROOT / "reports/figures").rglob("phase25_*")))
    ck("no_phase25_artifact", len(p25) == 0, f"{len(p25)} found")

    pre24 = sorted(p for p in list(AUD.glob("phase24_*")) + list(TAB.glob("phase24_*")))
    pre24 = [p for p in pre24 if p.name not in SELF_OUTPUTS]
    ck("no_preexisting_phase24_artifact", len(pre24) == 0,
       f"{len(pre24)}: {[p.name for p in pre24][:4]}")

    # TEST lock: read from the Phase-22 governance block, with fallbacks
    test_zero = False
    src = "none"
    for label, cand in (
        ("phase22.governance.test_locks", (p22f.get("governance") or {}).get("test_locks")),
        ("phase22.test_reads", p22f.get("test_reads")),
    ):
        if isinstance(cand, dict) and cand:
            test_zero = all(int(cand.get(k, 0) or 0) == 0 for k in
                            ("test_image_reads", "test_mask_reads", "test_inference",
                             "test_visualization"))
            src = label
            break
    ck("test_counters_all_zero", test_zero, src)

    # ---------------- verdict ----------------
    n_pass = sum(1 for c in checks if c["pass"])
    n_fail = len(checks) - n_pass
    verdict = "PHASE24_ENTRY_GATE_PASS" if n_fail == 0 else "PHASE24_ENTRY_GATE_FAIL"

    out = {
        "artifact": "phase24_entry_gate",
        "phase": 24,
        "purpose": "fail-closed predecessor verification before any Phase-24 design artifact",
        "verdict": verdict,
        "n_checks": len(checks),
        "n_passed": n_pass,
        "n_failed": n_fail,
        "checks": checks,
        "bindings": {
            "phase21_best_pt_sha256": sha(best),
            "phase22_freeze_sha256": sha(AUD / "phase22_final_freeze.json"),
            "phase22_protocol_sha256": sha(AUD / "phase22_diagnostic_protocol.json"),
            "phase23_notebook_sha256": sha(nb),
        },
        "no_training": True,
        "no_segmentation_inference": True,
        "no_router_inference": True,
        "test_reads": 0,
        "phase24_started": True,
        "phase25_started": False,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    (AUD / "phase24_entry_gate.json").write_text(json.dumps(out, indent=1), encoding="utf-8")

    for c in checks:
        print(f"  {'PASS' if c['pass'] else 'FAIL'}  {c['check']}"
              + (f"   [{c['detail']}]" if c["detail"] and not c["pass"] else ""))
    print()
    print(f"{n_pass}/{len(checks)} entry-gate checks passed")
    print(verdict)
    if n_fail:
        print("FAIL-CLOSED: entry gate failed; no Phase-24 artifact may be created.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
