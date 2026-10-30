import csv, json
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TAB = ROOT / "reports" / "tables"
AUD = ROOT / "reports" / "audits"

# ---------------------------------------------------------------------------
# §11 NOVELTY AXES  ->  phase23_novelty_axes.csv
# ---------------------------------------------------------------------------
AX_COLS = [
    "axis", "axis_name", "question",
    "already_explicitly_formulated", "status",
    "strongest_prior_art", "evidence", "defensible_residual", "confidence",
]

axes = [
 {
  "axis": "A", "axis_name": "PROBLEM FORMULATION",
  "question": "Is the problem 'predict whether an optional refinement will improve the current segmentation' already explicitly formulated?",
  "already_explicitly_formulated": "YES",
  "status": "OCCUPIED",
  "strongest_prior_art": "moon2024jfs (EXACT framing: 'judge the success of segmentation refinement'); russell1991metareasoning (abstract value-of-computation)",
  "evidence": "JFS abstract states it addresses the gap that 'no method has been developed that can determine the success of segmentation refinement'; Russell & Wefald formalise the same abstract question in 1991",
  "defensible_residual": "NONE at the level of problem FORMULATION — the question is explicitly asked and answered in segmentation before our work",
  "confidence": "HIGH",
 },
 {
  "axis": "B", "axis_name": "LEARNING TARGET",
  "question": "Has anyone explicitly trained a predictor on DeltaQ = refined outcome quality - global outcome quality for segmentation?",
  "already_explicitly_formulated": "NO",
  "status": "NOT_OCCUPIED_AS_A_LEARNED_SEGMENTATION_TARGET",
  "strongest_prior_art": "kunzel2019metalearners (CATE = E[Y(1)-Y(0)|x] — the identical FORMAL object, outside imaging); moon2024jfs (paired comparison but decision-only, untrained); zhao2026lfpc (implicit RL reward, not supervised)",
  "evidence": "No verified segmentation paper trains a supervised regressor on the paired GT-derived Dice gain of a refinement. The target formulation itself, however, is standard causal-inference practice (Kunzel et al. PNAS 2019).",
  "defensible_residual": "A SUPERVISED regression on the paired, GT-derived DeltaQ of a SEGMENTATION REFINEMENT, trained at the image level with a GT-free input space. The formal target is not novel; the instantiation is.",
  "confidence": "MEDIUM",
 },
 {
  "axis": "C", "axis_name": "DECISION MECHANISM",
  "question": "Has that predicted DeltaQ been used to decide execute/skip BEFORE expensive refinement?",
  "already_explicitly_formulated": "PARTIAL",
  "status": "PARTIALLY_OCCUPIED",
  "strongest_prior_art": "latotzke2021cascade + viola2001cascade (execute/skip before an expensive stage, with cost); shen2024meddanetv2 (per-sample compute decision before the model, medical); russell1991metareasoning (definitional)",
  "evidence": "Pre-execution escalate/stop gating is established in cascades and in medical dynamic architectures. None of these gates on a learned GT-derived DeltaQ of a refinement, and none preserves a refined output via rejection.",
  "defensible_residual": "The COMBINATION: a gate whose decision variable is a LEARNED paired-gain regression, applied to an OPTIONAL SEGMENTATION REFINEMENT, with fallback. The gate mechanism itself is not novel.",
  "confidence": "MEDIUM",
 },
 {
  "axis": "D", "axis_name": "SYSTEM INTEGRATION",
  "question": "Has this been combined with shared multi-domain medical segmentation + fallback/preservation + device/resource cost + small/tiny structures?",
  "already_explicitly_formulated": "NO",
  "status": "NOT_OCCUPIED_AS_A_COMBINATION",
  "strongest_prior_art": "butoi2023universeg / ma2024medsam (shared multi-domain, no gate); jiang2024m4oe (multi-domain + routing, no gain target); tian2026deferredseg (predict-then-route, human expert, no cost); zhang2024adaptivepatching (medical pre-computation allocation, no gain target)",
  "evidence": "Each pillar is individually occupied (see prior-art matrix). No verified work unifies: a frozen shared multi-domain segmentor + an optional refinement gated by a predicted paired gain + preservation-fallback + explicit resource cost + a tiny-structure trigger.",
  "defensible_residual": "The UNIFIED SYSTEM is the strongest residual. Novelty here is integration novelty, and must be argued as such (not as algorithmic novelty).",
  "confidence": "MEDIUM",
 },
]

with open(TAB / "phase23_novelty_axes.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=AX_COLS)
    w.writeheader()
    for r in axes:
        w.writerow(r)
print("novelty axes written")

# ---------------------------------------------------------------------------
# §16 COUNTERFACTUAL TERMINOLOGY AUDIT
# ---------------------------------------------------------------------------
cf = {
 "artifact": "phase23_counterfactual_terminology_audit",
 "phase": 23,
 "purpose": "decide whether 'counterfactual' / 'causal' language is technically defensible for the proposed DeltaQ formulation",
 "audited_quantity": "DeltaQ = Q(refined(x), y) - Q(global(x), y)",
 "questions": [
  {"question": "Are both potential outcomes observed during development?",
   "answer": "YES, but only JOINTLY, not as a true counterfactual. For each development image the system can compute BOTH Q(global) and Q(refined) because it may simply run the refinement during development. This is a fully observed paired design.",
   "implication": "Because neither arm is missing, there is no missing-data / identifiability problem."},
  {"question": "Is this simply supervised paired outcome prediction?",
   "answer": "YES. It is a supervised regression on an observed paired difference. It is exactly a T-learner-style estimate of a paired contrast where both arms are always observed.",
   "implication": "Supervised paired-outcome prediction is the accurate description."},
  {"question": "Is causal identification actually needed?",
   "answer": "NO. Causal identification machinery (ignorability, overlap, propensity weighting, IV) exists to handle a MISSING potential outcome. Here both outcomes are measured for every development unit, so no identification strategy is required.",
   "implication": "Invoking causal identification would be unnecessary and, worse, misdescribed."},
  {"question": "Would 'counterfactual refinement benefit' be technically defensible?",
   "answer": "WEAKLY / MISLEADING. The refinement is deterministic given (x, frozen model, frozen ROI rule). The 'effect' is therefore a deterministic function of the inputs and the frozen rule, not a stochastic individual treatment effect. Labelling it 'counterfactual' imports causal connotations (stochastic potential outcomes, unobserved counterfactuals) that the design does not have.",
   "implication": "Use paired-gain language; reserve 'counterfactual' for the strictly hypothetical framing if ever needed, with an explicit caveat."},
  {"question": "Is 'treatment effect' language misleading?",
   "answer": "YES, if used without qualification. 'Treatment' implies an intervention with a causal estimand and possibly confounding. Here the 'treatment' is a fixed computational procedure applied to a fixed input, and the estimand is a deterministic paired contrast.",
   "implication": "Avoid 'treatment effect' in the method naming; at most cite the formal analogy to CATE and state the difference."},
 ],
 "determinism_note": "The Phase-22 evidence (phase22_future_benefit_label_contract.json) fixes the label as delta_dice = dice(regional_fused) - dice(global) with a FROZEN decision rule and a FROZEN ROI rule. A frozen deterministic rule makes the 'effect' a deterministic contrast, further weakening any causal framing.",
 "outcome": "PREFER_PAIRED_REFINEMENT_GAIN",
 "allowed_wording": [
  "paired refinement gain",
  "paired benefit of the optional refinement",
  "predicted quality gain of the refinement over the global prediction",
  "benefit-aware routing (descriptive, not causal)"
 ],
 "disallowed_wording": [
  "counterfactual benefit (without an explicit caveat that both arms are observed)",
  "causal effect of the refinement",
  "treatment effect (unqualified)",
  "individual treatment effect"
 ],
 "residual_defensible_usage": "A single, clearly-caveated sentence may note the formal analogy: 'the target has the form of a conditional average treatment effect, but because both arms are observed for every development image the estimand is a deterministic paired contrast rather than a causal effect.'",
 "reviewer_credibility_note": "Using causal language where a paired design suffices invites reviewer rejection as overclaiming. The conservative term is stronger, not weaker.",
 "test_reads": 0,
 "generated_utc": datetime.now(timezone.utc).isoformat(),
}
(AUD / "phase23_counterfactual_terminology_audit.json").write_text(json.dumps(cf, indent=1), encoding="utf-8")
print("counterfactual terminology audit written")

# ---------------------------------------------------------------------------
# §17 CERTIFICATION TERMINOLOGY AUDIT
# ---------------------------------------------------------------------------
cert = {
 "artifact": "phase23_certification_terminology_audit",
 "phase": 23,
 "purpose": "decide whether the word 'certified' is defensible in the method name, given the evidence standard of each guarantee family",
 "candidate_terms_examined": [
  {"term": "calibrated confidence bound on predicted gain (A)",
   "what_it_would_mean": "a well-calibrated predictive interval / lower confidence bound on DeltaQ",
   "evidence_required": "calibration diagnostics (coverage vs nominal) on held-out data; no distribution-free claim",
   "achievable_now": "YES, in principle, but not yet demonstrated; Phase 22 shows the GT-free proxies are near-chance, so calibration is unproven",
   "status": "NOT_YET_EARNED"},
  {"term": "conformal guarantee (B)",
   "what_it_would_mean": "distribution-free finite-sample coverage of a prediction interval for DeltaQ",
   "evidence_required": "exchangeability assumption, a calibration set, explicit coverage/size trade-off",
   "achievable_now": "NO — requires a conformal construction and an exchangeability argument that do not exist yet; the refinement/ROI rules break naive exchangeability",
   "status": "NOT_EARNED"},
  {"term": "empirical risk threshold (C)",
   "what_it_would_mean": "the gate meets a pre-declared risk target on held-out data",
   "evidence_required": "a held-out, non-inspected evaluation population and a pre-declared risk level",
   "achievable_now": "NO — Phase 22's policies were all evaluated on the population they were inspected on (post-hoc, optimistic). No held-out protocol exists yet",
   "status": "NOT_EARNED"},
  {"term": "simple probability threshold (D)",
   "what_it_would_mean": "refine when p(DeltaQ > epsilon) exceeds a chosen threshold",
   "evidence_required": "only a fixed threshold; no guarantee claim",
   "achievable_now": "YES — this is a straightforward design choice, but it is NOT a certificate",
   "status": "ACHIEVABLE_BUT_NOT_A_CERTIFICATE"},
 ],
 "semantic_risk": "'Certified' in the machine-learning literature implies a GUARANTEE (conformal coverage, risk control, safety certificate). Using it for an uncalibrated threshold would be a terminological overclaim and a likely reviewer objection.",
 "outcome": "USE_CALIBRATED_IF_AND_ONLY_IF_CALIBRATION_IS_DEMONSTRATED_ELSE_USE_BENEFIT_AWARE_ONLY",
 "recommendation": "USE_BENEFIT_AWARE_ONLY",
 "recommendation_detail": "Adopt 'benefit-aware' (or 'gain-gated') as the defensible descriptor for the gate. The word 'certified' must be DROPPED from any provisional method name until EITHER (a) a conformal/risk-control construction is completed and validated on held-out data, OR (b) calibration coverage is demonstrated. Phase 23 cannot certify anything; it only rules out the claim for now.",
 "conditional_upgrade_path": "If, in a later phase, a conformal or risk-controlled construction on held-out data demonstrates coverage, the term may be revisited (USE_CALIBRATED or USE_RISK_CONTROLLED). That is a Phase-24+ decision and is explicitly NOT authorized here.",
 "reviewer_credibility_note": "An unearned 'certified' is the single easiest way to have the contribution dismissed. 'Benefit-aware' is both accurate and defensible today.",
 "test_reads": 0,
 "generated_utc": datetime.now(timezone.utc).isoformat(),
}
(AUD / "phase23_certification_terminology_audit.json").write_text(json.dumps(cert, indent=1), encoding="utf-8")
print("certification terminology audit written")
