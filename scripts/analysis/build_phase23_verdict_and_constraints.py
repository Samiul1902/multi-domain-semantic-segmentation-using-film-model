import csv, json
import pathlib
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TAB = ROOT / "reports" / "tables"
AUD = ROOT / "reports" / "audits"

# ---------------------------------------------------------------------------
# phase23_search_query_summary.csv
# ---------------------------------------------------------------------------
COLS = ["family", "label", "n_queries", "results_screened", "papers_retained",
        "highest_risk_found", "highest_risk_level"]
rows = [
 {"family": "A", "label": "multi-domain / universal medical segmentation", "n_queries": 4, "results_screened": 34, "papers_retained": 6, "highest_risk_found": "butoi2023universeg; ma2024medsam", "highest_risk_level": "MEDIUM"},
 {"family": "B", "label": "regional / coarse-to-fine refinement", "n_queries": 4, "results_screened": 31, "papers_retained": 7, "highest_risk_found": "isensee2021nnunet (always-run cascade)", "highest_risk_level": "MEDIUM"},
 {"family": "C", "label": "uncertainty-guided refinement", "n_queries": 4, "results_screened": 28, "papers_retained": 5, "highest_risk_found": "uhrnet2026 (current-uncertainty only)", "highest_risk_level": "MEDIUM"},
 {"family": "D", "label": "quality / error prediction", "n_queries": 4, "results_screened": 26, "papers_retained": 5, "highest_risk_found": "laves2018qualitypred; borges2024sdc", "highest_risk_level": "MEDIUM"},
 {"family": "E", "label": "counterfactual benefit / value-of-computation", "n_queries": 5, "results_screened": 40, "papers_retained": 9, "highest_risk_found": "russell1991metareasoning; kunzel2019metalearners", "highest_risk_level": "HIGH"},
 {"family": "F", "label": "conditional computation", "n_queries": 5, "results_screened": 33, "papers_retained": 6, "highest_risk_found": "graves2016act; wang2018skipnet", "highest_risk_level": "MEDIUM"},
 {"family": "G", "label": "mixture-of-experts / routing", "n_queries": 4, "results_screened": 29, "papers_retained": 6, "highest_risk_found": "jiang2024m4oe", "highest_risk_level": "HIGH"},
 {"family": "H", "label": "performance-preserving / safe routing", "n_queries": 5, "results_screened": 30, "papers_retained": 7, "highest_risk_found": "sanisoglu2026abstain; tan2026cls", "highest_risk_level": "MEDIUM"},
 {"family": "I", "label": "resource-aware / device-aware", "n_queries": 5, "results_screened": 27, "papers_retained": 5, "highest_risk_found": "zhang2023mobilesam", "highest_risk_level": "LOW"},
 {"family": "J", "label": "tiny-object / small-lesion", "n_queries": 5, "results_screened": 25, "papers_retained": 5, "highest_risk_found": "chou2024tinylessurvey; bouzid2023scaleaware", "highest_risk_level": "MEDIUM"},
 {"family": "K", "label": "falsification-first (disprove novelty)", "n_queries": 8, "results_screened": 44, "papers_retained": 8, "highest_risk_found": "moon2024jfs", "highest_risk_level": "HIGH"},
 {"family": "L", "label": "general-CV / ML precedence", "n_queries": 5, "results_screened": 36, "papers_retained": 9, "highest_risk_found": "latotzke2021cascade; viola2001cascade; ren2015fasterrcnn", "highest_risk_level": "HIGH"},
 {"family": "M", "label": "patent / prior-art scan (non-legal)", "n_queries": 5, "results_screened": 18, "papers_retained": 2, "highest_risk_found": "US 2026/0155254 A1 (general medical segmentation)", "highest_risk_level": "LOW"},
]
with open(TAB / "phase23_search_query_summary.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    for r in rows:
        w.writerow(r)
print("search query summary written")

# ---------------------------------------------------------------------------
# §13 NOVELTY CLAIM LADDER
# ---------------------------------------------------------------------------
ladder = {
 "artifact": "phase23_novelty_claim_ladder",
 "phase": 23,
 "purpose": "determine the MAXIMUM DEFENSIBLE claim level for the candidate contribution, conservatively",
 "levels": [
  {"level": 0, "template": "We investigate ...",
   "defensible_for_our_candidate": "YES",
   "justification": "unconditionally safe; the audit itself is an investigation"},
  {"level": 1, "template": "We propose ...",
   "defensible_for_our_candidate": "YES",
   "justification": "safe for the SYSTEM as a proposal; proposing a combination of known components is a proposal, not a novelty claim"},
  {"level": 2, "template": "We introduce a novel ...",
   "defensible_for_our_candidate": "QUALIFIED_YES",
   "justification": "defensible ONLY if scoped to the specific unoccupied combination (a learned GT-free predictor of the PAIRED refinement gain used as a PRE-EXECUTION gate within shared multi-domain medical segmentation with preservation-fallback). The word 'novel' must not attach to the gate concept, the paired-gain target, multi-domain modelling, or resource awareness individually — each is occupied (see phase23_prior_art_matrix.csv)."},
  {"level": 3, "template": "To the best of our knowledge, we are the first to ...",
   "defensible_for_our_candidate": "NO__NOT_SUPPORTED",
   "justification": "NOT supported: (i) the mechanism is precedented in metareasoning (1991), cascades (2001/2021) and treatment-effect meta-learners (2019); (ii) the problem framing exists in segmentation (moon2024jfs, ICIP 2025); (iii) no legal/systematic search has been performed. 'First' cannot be asserted on a single-session index search."},
 ],
 "recommended_maximum_level": 2,
 "recommended_maximum_scope": "a novel UNIFIED SYSTEM: a pre-execution, GT-free, benefit-aware gate for an optional refinement in shared multi-domain medical segmentation, supervised by the paired refinement gain, with preservation-fallback",
 "recommended_conservative_default": "Level 1 with a Level-2 sentence scoped strictly to the unoccupied combination",
 "forbidden_phrasings": [
  "first in the world",
  "never done before",
  "absolutely unique",
  "first to predict refinement benefit in segmentation",
  "novel value-of-computation framework",
  "novel counterfactual benefit prediction"
 ],
 "reason_for_conservatism": "Falsification-first search surfaced a same-framing segmentation paper (JFS), a 1991 formalisation of value-of-computation, a 2021 cascade gating method with cost, and a 2019 paired-gain meta-learner framework. Any of these alone collapses a Level-3 claim.",
 "test_reads": 0,
 "generated_utc": datetime.now(timezone.utc).isoformat(),
}
(AUD / "phase23_novelty_claim_ladder.json").write_text(json.dumps(ladder, indent=1), encoding="utf-8")
print("claim ladder written")

# ---------------------------------------------------------------------------
# §28 NOVELTY VERDICT
# ---------------------------------------------------------------------------
verdict = {
 "artifact": "phase23_novelty_verdict",
 "phase": 23,
 "candidate_name_provisional": "Counterfactual Benefit-Certified Refinement (CBCR) — PROVISIONAL, NAME NOT AUTHORIZED AS IS (see recommended_method_name_status)",
 "candidate_mechanism_summary": (
     "A frozen/shared global segmentor produces an initial mask; an optional expensive refinement exists; "
     "BEFORE running it, a lightweight GT-free predictor estimates the paired gain DeltaQ = Q(refined,GT) - Q(global,GT); "
     "the prediction gates EXECUTE vs SKIP; harmful refinements can be rejected so the global output is preserved; "
     "routing may include compute/device cost; applied within shared multi-domain medical segmentation."
 ),
 "overall_label": "PARTIALLY_OCCUPIED__NARROWER_NOVELTY_POSSIBLE",
 "overall_label_meaning": "major components exist; the exact formulation/integration appears different and a narrower contribution remains defensible",
 "closest_prior_works": [
  {"citation_key": "moon2024jfs", "why": "same problem framing ('was the refinement worth it?') and a paired coarse-vs-refined comparison with revert-on-failure, but POST-HOC and untrained", "risk": "HIGH"},
  {"citation_key": "russell1991metareasoning", "why": "formalises value-of-computation = expected benefit of a computation minus cost, decided before acting", "risk": "HIGH"},
  {"citation_key": "latotzke2021cascade", "why": "optimal execute/skip pass-on criteria before an expensive stage, with an explicit cost term", "risk": "HIGH"},
  {"citation_key": "kunzel2019metalearners", "why": "CATE = paired outcome difference — the identical formal target, outside imaging", "risk": "HIGH"},
  {"citation_key": "shen2024meddanetv2", "why": "medical, per-sample compute decision BEFORE the model, efficiency objective", "risk": "HIGH"},
  {"citation_key": "jiang2024m4oe", "why": "multi-domain medical segmentation with learned routing", "risk": "HIGH"},
  {"citation_key": "zhao2026lfpc", "why": "optimises an information-gain signal for a regional action (RL, not segmentation)", "risk": "HIGH"},
  {"citation_key": "moon2024jfs_alt", "why": "(see moon2024jfs)", "risk": "HIGH"},
 ],
 "algorithmic_novelty_status": "OCCUPIED_AT_THE_MECHANISM_LEVEL",
 "algorithmic_novelty_detail": (
     "The mechanism 'predict the benefit of a future computation, then execute/skip' is fully precedented "
     "(metareasoning 1991; cascades 2001/2021; learned deferral 2020). The paired-gain learning target is "
     "standard causal-inference machinery (CATE, 2019). No algorithmic novelty can be claimed for either."
 ),
 "problem_formulation_novelty_status": "OCCUPIED",
 "problem_formulation_novelty_detail": (
     "The exact question 'should I keep the refined mask or the coarse one?' is explicitly posed and answered "
     "in segmentation by JFS (ICIP 2025), and in the abstract by metareasoning. The formulation is not novel."
 ),
 "system_integration_novelty_status": "APPARENTLY_UNOCCUPIED",
 "system_integration_novelty_detail": (
     "No verified work unifies: a frozen shared multi-domain medical segmentor + an optional refinement gated by a "
     "LEARNED GT-derived paired-gain prediction evaluated PRE-EXECUTION + preservation-fallback + explicit "
     "resource/device cost + tiny-structure motivation. This is the strongest residual claim, and it is an "
     "INTEGRATION novelty."
 ),
 "evaluation_novelty_status": "PARTIALLY_UNOCCUPIED",
 "evaluation_novelty_detail": (
     "Phase 22 already established an evaluation-frame contribution (paired per-case DeltaQ with an oracle ceiling "
     "and routing regret under a frozen decision rule). Reporting benefit-awareness under an oracle ceiling + "
     "routing regret for segmentation refinement is not yet standard practice, but it is an evaluation-methodology "
     "contribution, not a new metric."
 ),
 "exactly_occupied_components": [
  "shared / universal multi-domain medical segmentation (UniverSeg, MedSAM, MedSAM2, MedUniSeg)",
  "task/modality conditioning incl. FiLM-style modulation",
  "mixture-of-experts / learned routing in medical segmentation (M4oE)",
  "regional / coarse-to-fine / high-resolution refinement (nnU-Net cascade, SegRefiner, scale-aware SR)",
  "uncertainty estimation and calibration (DEviS, SDC)",
  "uncertainty-guided refinement (UHR-Net and family)",
  "segmentation quality prediction without ground truth (Laves 2018, EvanySeg, SDC)",
  "error / failure prediction and abstention (Learning-to-Abstain, conformal risk control)",
  "conditional computation / early exit / dynamic resolution",
  "execute-vs-skip gating before an expensive computation, with cost (cascades; ACT; SkipNet)",
  "value-of-computation / metareasoning (Russell & Wefald 1991)",
  "paired-outcome / treatment-effect target formulation (CATE meta-learners)",
  "performance-preserving efficiency gains as an objective (adaptive-inference theory)",
  "resource / mobile / edge segmentation (MobileSAM, edge-adaptive nets)",
  "tiny-lesion / small-structure segmentation and zoom refinement",
  "post-hoc refined-vs-coarse acceptance with fallback (JFS)",
 ],
 "apparently_unoccupied_combination": [
  "a LEARNED, GT-FREE predictor of the PAIRED refinement gain DeltaQ = Q(refined,GT) - Q(global,GT) for segmentation, trained as a direct supervised regression (not an RL reward, not a statistical pass-on criterion)",
  "that prediction used as a PRE-EXECUTION execute/skip gate on an OPTIONAL refinement (so compute is saved, unlike JFS's post-hoc verifier)",
  "explicit preservation-fallback that retains the global output when the refinement is skipped or rejected",
  "unified with a frozen SHARED MULTI-DOMAIN medical segmentor and an explicit resource/device cost term",
  "motivated by tiny-structure difficulty (not claiming the tiny-object problem itself as novel)",
 ],
 "major_novelty_risks": [
  {"risk": "A reviewer identifies JFS (Moon et al., ICIP 2025) as already answering 'was the refinement worth it?'", "severity": "HIGH", "mitigation": "state explicitly that JFS decides POST-HOC and thus saves no compute; our claim is the PRE-EXECUTION, learned, GT-free gate"},
  {"risk": "'Value of computation' / metareasoning is a 1991 idea; the gate concept is not novel", "severity": "HIGH", "mitigation": "cite Russell & Wefald and cascades up front; claim only the segmentation instantiation and the learned paired-gain target"},
  {"risk": "The paired-gain target is standard CATE; claiming it as novel would be rejected", "severity": "HIGH", "mitigation": "cite Kunzel et al.; state that we instantiate, not invent, the target"},
  {"risk": "Med-DANet V2 already makes a pre-execution compute decision in medical segmentation", "severity": "HIGH", "mitigation": "distinguish the decision variable (expected Dice gain of a refinement vs crop/quantization policy)"},
  {"risk": "'Certified' implies a guarantee we cannot provide", "severity": "MEDIUM", "mitigation": "drop 'certified'; use 'benefit-aware / gain-gated'"},
  {"risk": "'Counterfactual' implies causal identification that the paired design does not require", "severity": "MEDIUM", "mitigation": "use 'paired refinement gain'; caveat any causal analogy"},
  {"risk": "Device/resource awareness may be read as engineering, not algorithmic, novelty", "severity": "MEDIUM", "mitigation": "classify device-awareness as ENGINEERING VALUE unless it is integrated with the benefit gate as an explicit utility term"},
  {"risk": "The tiny-object problem itself is not novel (tiny-lesion survey 2024)", "severity": "MEDIUM", "mitigation": "claim only how optional computation is ALLOCATED, never the tiny-object problem"},
 ],
 "required_reframing": [
  "Drop 'certified' from the method name -> use 'benefit-aware' (or 'gain-gated').",
  "Drop or heavily caveat 'counterfactual' -> use 'paired refinement gain'.",
  "Do NOT claim the gate mechanism, the paired-gain target, multi-domain modelling, or resource awareness as individually novel.",
  "Position the contribution as a SYSTEM/INTEGRATION novelty, explicitly downstream of metareasoning, cascades, CATE, and JFS.",
  "State the PRE-EXECUTION property as the primary mechanical difference from JFS (compute saving), and the LEARNED GT-free DeltaQ regression as the primary target difference.",
 ],
 "maximum_defensible_claim_level": 2,
 "maximum_defensible_claim_level_scope": "scoped strictly to the unoccupied combination (pre-execution, GT-free, learned paired-gain gate for an optional refinement within shared multi-domain medical segmentation with preservation-fallback); Level 3 is NOT defensible",
 "recommended_method_name_status": "RENAME",
 "recommended_method_name_status_detail": (
     "'Counterfactual Benefit-Certified Refinement' (CBCR) is TOO_STRONG on two words: 'Counterfactual' "
     "(paired design, not causal) and 'Certified' (no guarantee demonstrated). Recommended provisional rename: "
     "'Benefit-Aware Refinement Routing' (BARR) or 'Gain-Gated Refinement' (GGR). PROVISIONAL_ONLY — a final "
     "name is a Phase-24 decision."
 ),
 "phase24_allowed": True,
 "phase24_allowed_condition": "Phase 24 may proceed to a NARROWED architecture specification ONLY. The narrowed scope is defined in phase23_phase24_design_constraints.json. No implementation, training or TEST access is authorized by Phase 23.",
 "test_reads": 0,
 "training_jobs_started": 0,
 "phase24_started": False,
 "generated_utc": datetime.now(timezone.utc).isoformat(),
}
(AUD / "phase23_novelty_verdict.json").write_text(json.dumps(verdict, indent=1), encoding="utf-8")
print("novelty verdict written")

# ---------------------------------------------------------------------------
# §29 PHASE-24 DESIGN CONSTRAINTS
# ---------------------------------------------------------------------------
constraints = {
 "artifact": "phase23_phase24_design_constraints",
 "phase": 23,
 "status": "PHASE24_ELIGIBLE_NOT_STARTED",
 "scope": "HIGH-LEVEL CONSTRAINTS ONLY. No architecture, widths, losses, thresholds or predictor choice are specified here.",
 "high_level_constraints": [
  {"id": "C1", "constraint": "The benefit predictor MUST be pre-refinement: every input must be available BEFORE the expensive refinement is executed.", "rationale": "the compute-saving property is the primary mechanical difference from post-hoc verifiers (JFS)"},
  {"id": "C2", "constraint": "The predictor inputs MUST be GT-free at inference time.", "rationale": "Phase 22 showed GT-derived quantities are not deployable; the label may use GT, the input may not"},
  {"id": "C3", "constraint": "The training target MUST derive from the PAIRED refinement gain (refined quality minus global quality) under a frozen, pre-declared decision rule.", "rationale": "anchors the contribution to the audited target formulation; the rule must be frozen before training"},
  {"id": "C4", "constraint": "The expensive refinement MUST NOT be required in order to compute the gate signal.", "rationale": "otherwise no compute is saved and the pre-execution claim collapses"},
  {"id": "C5", "constraint": "A fallback MUST preserve the global output whenever the refinement is skipped or rejected.", "rationale": "'performance-preserving' is the load-bearing adjective; it must be enforced structurally"},
  {"id": "C6", "constraint": "If resource/device cost is retained, it MUST appear as an EXPLICIT term in the decision utility (e.g. gain minus lambda*cost), not as an implicit assumption.", "rationale": "otherwise the resource component is engineering, not a defensible contribution"},
  {"id": "C7", "constraint": "Development labels MUST be constructed from TRAIN only.", "rationale": "the predictor must not see the evaluation population during training"},
  {"id": "C8", "constraint": "The frozen Phase-22 VAL population (808 cases) MUST NOT be reused as benefit-predictor training data.", "rationale": "Phase 22's policies were all evaluated on the population they were inspected on; reusing it as training data would destroy any out-of-sample claim"},
  {"id": "C9", "constraint": "A held-out, never-inspected evaluation population MUST be designated BEFORE any routing policy is fitted.", "rationale": "the Phase-22 routing regrets are post-hoc and optimistically biased; out-of-sample evidence requires a held-out protocol"},
  {"id": "C10", "constraint": "The method name MUST NOT contain 'certified' or 'counterfactual' unless the corresponding evidence is produced (see terminology audits).", "rationale": "terminological overclaim is the easiest reviewer objection"},
  {"id": "C11", "constraint": "TEST MUST remain closed: 0 image reads, 0 mask reads, 0 inference, 0 visualizations.", "rationale": "project-wide governance"},
  {"id": "C12", "constraint": "Closest prior art (JFS, metareasoning, cascades, CATE, Med-DANet V2, M4oE) MUST be cited and explicitly differentiated in the Phase-24/25 write-up.", "rationale": "the contribution survives only if its margin to each is stated plainly"},
 ],
 "explicitly_not_decided_here": [
  "predictor architecture and capacity",
  "input feature set",
  "loss function (regression vs classification vs distributional)",
  "threshold or epsilon",
  "router mechanics",
  "which domains / how many",
  "refinement ROI rule changes",
  "evaluation metric suite",
 ],
 "phase24_task_statement_proposed": (
     "Specify a narrowed, pre-registered architecture and protocol for a pre-execution, GT-free, benefit-aware gate "
     "over an optional refinement within shared multi-domain medical segmentation, including an explicit "
     "resource-cost utility term and a preservation-fallback, with a held-out evaluation population designated "
     "in advance. No implementation, training or TEST access."
 ),
 "test_reads": 0,
 "generated_utc": datetime.now(timezone.utc).isoformat(),
}
(AUD / "phase23_phase24_design_constraints.json").write_text(json.dumps(constraints, indent=1), encoding="utf-8")
print("phase24 design constraints written")
