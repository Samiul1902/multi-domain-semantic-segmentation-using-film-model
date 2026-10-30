"""Phase 24 (1/4) — method naming decision + prior-art differentiation table.

DESIGN ONLY. No training, no inference, no TEST access.

Writes:
    reports/audits/phase24_method_naming_decision.json
    reports/tables/phase24_prior_art_differentiation.csv

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/build_phase24_naming_and_priorart.py
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
TAB.mkdir(parents=True, exist_ok=True)

RETIRED_NAME = "Counterfactual Benefit-Certified Refinement / CBCR"

# ---------------------------------------------------------------------------
# 1. METHOD NAMING DECISION (§4)
# ---------------------------------------------------------------------------
CANDIDATES = [
    {
        "candidate": "RA-MedFiLM-BARR",
        "expansion": "Resource-Aware MedFiLM with Benefit-Aware Refinement Routing",
        "acronym_ambiguity": (
            "MODERATE — 'BARR' is pronounceable and unique in this project, but 'RA' "
            "collides with 'Regional Attention' / 'Resource-Aware' / 'Risk-Averse' in adjacent "
            "literature, so the expansion MUST always be written out on first use."
        ),
        "terminology_collision": (
            "LOW-MODERATE — 'Benefit-Aware' is not a term of art claimed by any of the six "
            "closest works; but 'benefit' alone is generic and must be qualified as "
            "'paired refinement gain' in the abstract."
        ),
        "misleading_implication": (
            "LOW — 'Resource-Aware' is defensible because C6 forces an explicit lambda*C term. "
            "The name does NOT imply a measured device result, provided the paper states that "
            "cost is ANALYTICAL MACs in Phase 25 and that device measurement belongs to Phase 34."
        ),
        "clarity_vs_jfs": (
            "GOOD — the presence of both 'Benefit-Aware' and 'Routing' in the expansion makes the "
            "pre-execution decision explicit, which is exactly the axis on which JFS differs "
            "(JFS decides post-hoc). A reader who knows JFS will see the intended distinction."
        ),
        "consistency_with_phase23_boundary": (
            "CONSISTENT — no forbidden token appears ('counterfactual', 'certified', 'causal', "
            "'guaranteed' all absent). 'Resource-Aware' is retained as a name component only "
            "because C6 requires the cost term to be explicit."
        ),
        "verdict": "SELECTED",
        "note": (
            "Chosen because it encodes the two specification-level facts that carry the "
            "contribution: the routing is benefit-aware AND resource-aware. 'Benefit-Aware' "
            "matches the Phase-23 terminology outcome (USE_BENEFIT_AWARE_ONLY)."
        ),
    },
    {
        "candidate": "RA-MedFiLM-GGR",
        "expansion": "Resource-Aware MedFiLM with Gain-Gated Refinement",
        "acronym_ambiguity": (
            "LOW — 'GGR' is unique here."
        ),
        "terminology_collision": (
            "HIGH — 'Gating' is heavily overloaded: mixture-of-experts gating, attention gating, "
            "and the cascade 'gate' all use it. The Phase-23 audit explicitly found the gate "
            "MECHANISM occupied (metareasoning 1991; Latotzke 2021; Med-DANet V2). Naming the "
            "method after the occupied primitive invites the exact 'this is just a gate' objection."
        ),
        "misleading_implication": (
            "MODERATE — 'Gated' foregrounds the mechanism rather than the decision variable, which "
            "is the part Phase 23 found OCCUPIED. It also risks implying the contribution is the "
            "gate rather than the integrated system."
        ),
        "clarity_vs_jfs": (
            "WEAKER — 'Gain-Gated' does not by itself signal pre-execution; a reader could assume "
            "a post-hoc gate, which is JFS's setting. The distinction would have to be argued in "
            "prose rather than carried by the name."
        ),
        "consistency_with_phase23_boundary": (
            "CONSISTENT on forbidden tokens, but WEAKER on the Phase-23 boundary because it names "
            "the contribution after a primitive the audit classified as OCCUPIED."
        ),
        "verdict": "NOT_SELECTED",
        "note": "Rejected primarily for terminology collision with the occupied 'gating' primitive.",
    },
]

FORBIDDEN_IN_NAME = ["counterfactual", "certified", "causal", "guaranteed"]

decision = {
    "artifact": "phase24_method_naming_decision",
    "phase": 24,
    "purpose": "freeze ONE provisional research name for Phases 25-38",
    "retired_name": RETIRED_NAME,
    "retired_reason": (
        "Contains 'Counterfactual' (Phase-23 audit outcome PREFER_PAIRED_REFINEMENT_GAIN: both "
        "potential outcomes are fully observed, so there is no identification problem) and "
        "'Certified' (Phase-23 audit outcome USE_BENEFIT_AWARE_ONLY: no conformal, risk-control "
        "or calibration guarantee is earned). Both are unsupported overclaims."
    ),
    "candidates_evaluated": CANDIDATES,
    "selection_criteria": [
        "acronym ambiguity", "terminology collision", "misleading implication",
        "clarity relative to JFS", "consistency with the Phase-23 novelty boundary",
    ],
    "frozen_method_name": "RA-MedFiLM-BARR",
    "frozen_method_name_expansion":
        "Resource-Aware MedFiLM with Benefit-Aware Refinement Routing",
    "short_form": "BARR",
    "frozen_for_phases": "25-38",
    "forbidden_tokens_in_name": FORBIDDEN_IN_NAME,
    "forbidden_tokens_check": "PASS (none present in the frozen name or its expansion)",
    "required_first_use_form": (
        "'RA-MedFiLM-BARR (Resource-Aware MedFiLM with Benefit-Aware Refinement Routing)'. "
        "The expansion must appear on first use in every document; the bare acronym may not be "
        "used as the first mention."
    ),
    "required_terminology_companions": {
        "instead_of_counterfactual": "PREFER_PAIRED_REFINEMENT_GAIN",
        "instead_of_certified": "USE_BENEFIT_AWARE_ONLY",
    },
    "binding": (
        "This name is PROVISIONAL and DESIGN-LEVEL. It may not be used to assert a result. "
        "It carries no claim of novelty for any individual primitive."
    ),
    "no_training": True,
    "no_inference": True,
    "test_reads": 0,
    "generated_utc": datetime.now(timezone.utc).isoformat(),
}
(AUD / "phase24_method_naming_decision.json").write_text(
    json.dumps(decision, indent=1), encoding="utf-8")

# ---------------------------------------------------------------------------
# 2. PRIOR-ART DIFFERENTIATION TABLE (§32) — categorical, NOT ranked
# ---------------------------------------------------------------------------
PA_COLS = ["citation_key", "work", "year", "venue",
           "pre_execution", "learned_gain", "paired_gain_target", "GT_free_inference",
           "optional_refinement", "compute_saved_by_gate", "post_fallback",
           "shared_multidomain_medical", "explicit_resource_cost",
           "difference_from_our_spec"]

PA_ROWS = [
    ["moon2024jfs", "JFS: Joint refinement + selection for segmentation", 2024, "ICIP 2025 (arXiv:2407.04519)",
     "no (POST-HOC)", "no (untrained)", "partial (paired coarse-vs-refined comparison)",
     "n/a (no learned predictor)", "yes", "NO", "yes (revert-on-failure)",
     "no", "no",
     "CLOSEST ANALOGUE. Same framing ('was the refinement worth it?') and a paired comparison "
     "with revert-on-failure, BUT it decides AFTER the refinement has run, so it saves ZERO "
     "compute, and its decision rule is not a learned regression. Our spec moves the identical "
     "question BEFORE the action and learns it; that relocation is the entire margin."],

    ["russell1991metareasoning", "Russell & Wefald: Principles of metareasoning (value of computation)", 1991, "Artificial Intelligence 49(1-3)",
     "yes (definitional)", "no", "no", "n/a", "conceptual (any computation)", "yes (conceptual)",
     "no", "no", "yes (abstract cost term)",
     "FORMAL ANTECEDENT. Defines the value of a computation as expected benefit minus cost, "
     "decided before acting. Our spec is a concrete learned instantiation of this abstract "
     "principle inside a segmentation system; it contributes no new formal machinery."],

    ["viola2001cascade", "Viola & Jones: Rapid object detection using a boosted cascade", 2001, "CVPR 2001",
     "yes", "no (hand-designed cascade thresholds)", "no", "yes", "no (cascade stages, not a refinement)",
     "yes", "no", "no", "no",
     "MECHANISM PRECEDENT. Establishes execute/skip vetoing of an expensive stage. But the "
     "decision variable is a hand-designed detector response, not a learned paired quality gain, "
     "and there is no quality-preserving fallback to a higher-quality alternative output."],

    ["latotzke2021cascade", "Latotzke et al.: Optimal pass-on criteria for cascaded classifiers", 2021, "LOD 2021 (Springer LNCS)",
     "yes", "no (analytical criteria)", "no", "yes", "no", "yes", "no", "no", "yes (cost in the criterion)",
     "NEAREST MECHANISM. Derives optimal execute/skip criteria before an expensive stage with an "
     "explicit cost term. Differs in that the decision variable is a class-conditional likelihood "
     "ratio, not a regression on a paired continuous quality gain, and the task is classification, "
     "not dense segmentation with a preservable fallback output."],

    ["kunzel2019metalearners", "Kunzel et al.: Metalearners for estimating heterogeneous treatment effects (CATE)", 2019, "PNAS 116(10)",
     "n/a (estimand, not a system)", "yes (supervised T/X/S-learners)",
     "YES (E[Y(1)-Y(0)|x] is the identical formal object)", "yes", "n/a", "no",
     "no", "no", "no",
     "IDENTICAL FORMAL TARGET, OUTSIDE IMAGING. Our paired refinement gain is formally a "
     "conditional average treatment effect on a deterministic paired contrast. Phase 23 already "
     "concluded the target formulation is standard causal-inference practice; our spec claims no "
     "novelty for the estimand and only instantiates it within segmentation routing."],

    ["shen2022meddanet", "Med-DANet: Dynamic architecture network for efficient medical segmentation", 2022, "ECCV 2022",
     "yes", "no (learned band selection, not a quality gain)", "no", "yes", "no (architecture selection)",
     "yes", "no", "yes (medical)", "partial (efficiency objective)",
     "PRECEDENT FOR PER-SAMPLE COMPUTE DECISION IN MEDICAL SEGMENTATION. Selects an input "
     "resolution band before the forward pass. Differs: the decision variable is a learned "
     "architecture-selection score, not a predicted paired Dice gain, and there is no optional "
     "refinement acting on the output with a preservation fallback."],

    ["shen2024meddanetv2", "Med-DANet V2: dynamic architecture network v2", 2024, "WACV 2024",
     "yes", "no (learned band selection)", "no", "yes", "no", "yes", "no", "yes (medical)",
     "partial (efficiency objective)",
     "STRONGEST PRECEDENT FOR THE DECISION TIMING. Confirms that a pre-execution per-sample "
     "compute decision is established practice in medical segmentation. Differs in the decision "
     "variable (band score vs paired gain regression) and in the absence of a quality-preserving "
     "fallback output."],

    ["jiang2024m4oe", "M4oE: Multi-domain medical mixture-of-experts", 2024, "MICCAI 2024 (arXiv:2407.xxxxx)",
     "no (static per-image routing during the forward pass)", "no (expert selection, not a gain)",
     "no", "yes", "no", "partial (sparse expert activation)", "no",
     "YES (multi-domain medical)", "partial (sparse compute)",
     "PRECEDENT FOR MULTI-DOMAIN ROUTING IN MEDICAL SEGMENTATION. Routes to experts. Differs: "
     "routing selects which parameters compute, not WHETHER an optional refinement runs, and there "
     "is no learned pre-execution prediction of output-quality gain and no fallback output."],

    ["zhang2024adaptivepatching", "Adaptive patching for efficient medical image segmentation", 2024, "arXiv preprint (cs.CV)",
     "yes", "no (content-based patch allocation)", "no", "yes", "no (patch allocation)",
     "yes", "no", "yes (medical)", "yes (compute budget)",
     "PRECEDENT FOR PRE-COMPUTATION COMPUTE ALLOCATION IN MEDICAL IMAGING. Allocates patches "
     "based on content. Differs: allocates WHERE to compute, not WHETHER to run a refinement, and "
     "carries no learned paired-gain target and no preservation fallback."],

    ["mozannar2020defer", "Mozannar & Sontag: Consistent estimators for learning to defer", 2020, "ICML 2020",
     "yes (defer before deciding)", "yes (learned deferral policy)", "no (0-1 loss, not a paired gain)",
     "yes", "no (defers to a human expert)", "yes", "no (human takes over)",
     "no", "yes (expert cost term)",
     "STRUCTURAL ANALOGUE WITH A DIFFERENT RESOURCE. Learns when to defer to a costly expert "
     "with an explicit cost. Differs: the deferred actor is a human expert, the objective is a "
     "classification loss rather than a paired segmentation Dice gain, and the fallback is the "
     "model's own prediction, not a preserved higher-quality output."],

    ["ren2015fasterrcnn", "Faster R-CNN: region proposal network", 2015, "NeurIPS 2015",
     "yes (proposals before per-region heads)", "no", "no", "yes", "no (proposal stage)",
     "yes", "no", "no", "partial (proposal budget)",
     "PRECEDENT FOR A REGION-PROPOSAL STAGE PRECEDING AN EXPENSIVE PER-REGION HEAD. Its "
     "proposals are GT-free. Differs: proposals select WHERE to run a detector, not WHETHER a "
     "refinement of an already-produced mask is worth running; no paired-gain target."],

    ["isensee2021nnunet", "nnU-Net: a self-configuring method for medical image segmentation", 2021, "Nature Methods 18:203-211",
     "n/a (always-run cascade)", "no", "no", "yes", "no", "NO (cascade always runs)",
     "no", "yes (multi-dataset)", "no",
     "BASELINE ARCHITECTURE AND ALWAYS-RUN COUNTEREXAMPLE. Its coarse-to-fine cascade always "
     "executes the fine stage, which is exactly the regime we propose to gate. Cited as the "
     "architectural ancestor of the regional-refinement stage, not as a competing method."],
]

with (TAB / "phase24_prior_art_differentiation.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(PA_COLS)
    for r in PA_ROWS:
        w.writerow(r)

print("method naming decision written")
print("  frozen name      :", decision["frozen_method_name"])
print("  expansion        :", decision["frozen_method_name_expansion"])
print("  retired          :", RETIRED_NAME)
print("  forbidden tokens :", FORBIDDEN_IN_NAME, "->", decision["forbidden_tokens_check"])
print()
print(f"prior-art differentiation written: {len(PA_ROWS)} rows x {len(PA_COLS)} cols")
print("  NO ranking/scoring column present:", "score" not in " ".join(PA_COLS))
