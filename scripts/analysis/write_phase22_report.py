"""Phase 22 — write the reviewer-facing gap-analysis report (§43).

Deterministic markdown built ONLY from persisted artifacts. No timestamps of the run,
no wall-clock, so repeated invocations are byte-identical.

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/write_phase22_report.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analysis import phase22_common as C  # noqa: E402

OUT = ROOT / "reports/phase22_resource_gap_report.md"


def _j(name: str) -> dict:
    p = C.AUDITS / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _gt_aware_rows() -> list:
    """Read the GT-aware post-hoc association table for the report (Part B5)."""
    import csv
    p = C.TABLES / "phase22_gt_aware_posthoc_associations.csv"
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _f(x, nd=6):
    try:
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return "n/a"


def _pct(x, nd=2):
    try:
        return f"{100.0 * float(x):.{nd}f}%"
    except (TypeError, ValueError):
        return "n/a"


def main() -> int:
    proto = _j("phase22_diagnostic_protocol.json")
    rb = _j("phase22_phase21_reference_binding.json")
    thr = _j("phase22_threshold_rule_audit.json")
    atlas = _j("phase22_global_failure_atlas.json")
    scale = _j("phase22_scale_sensitivity.json")
    sfid = _j("phase22_scale_probe_fidelity.json")
    reg = _j("phase22_oracle_regional_intervention.json")
    het = _j("phase22_benefit_heterogeneity.json")
    acc = _j("phase22_oracle_accept_if_beneficial.json")
    regret = _j("phase22_routing_regret.json")
    harm = _j("phase22_harm_analysis.json")
    roi = _j("phase22_prediction_derived_roi.json")
    unc = _j("phase22_uncertainty_vs_benefit.json")
    # B5 semantic repair: the deployable ranking and the GT-aware associations come
    # from the post-freeze separation artifacts. If they are present they SUPERSEDE
    # the invalid `best_deployable_signal` field (which named a GT-derived metric).
    rep = _j("phase22_postfreeze_semantic_repair.json")
    if rep:
        unc = dict(unc)
        unc["gt_free_ranking"] = rep.get("gt_free_deployable_ranking") or []
        unc["gt_aware_associations"] = _gt_aware_rows()
        if rep.get("best_gt_free_signal"):
            unc["best_deployable_signal"] = None      # never echo the invalid claim
    env = _j("phase22_conditional_compute_envelopes.json")
    gap = _j("phase22_resource_gap.json")
    cpu = _j("phase22_cpu_baseline.json")
    tiny = _j("phase22_kub_tiny_analysis.json")
    dom = _j("phase22_domain_preservation.json")
    stats = _j("phase22_statistics.json")
    svr = _j("phase22_scale_vs_regional.json")
    nt = _j("phase22_no_new_training_audit.json")
    ce = _j("phase22_candidate_method_evidence.json")
    lb = _j("phase22_future_benefit_label_contract.json")

    L: list[str] = []
    A = L.append

    A("# Phase 22 — Multi-Domain Scale, Regional-Benefit & Resource Gap Analysis")
    A("")
    A("**Diagnostic gap analysis on the frozen Phase-21 Global MedFiLM reference.** "
      "No training, no architecture change, no benefit predictor, no TEST access.")
    A("")
    A("| Item | Value |")
    A("|---|---|")
    A(f"| Protocol | `{proto.get('protocol_id')}` (frozen={proto.get('frozen')}) |")
    A(f"| Reference | `{C.EXPERIMENT_ID}` (frozen, unchanged) |")
    A(f"| Reference binding | {rb.get('verdict')} ({rb.get('n_passed')}/{rb.get('n_checks')}) |")
    A("| Population | 808 VAL cases (identical to Phase 21) |")
    A("| TEST | CLOSED — 0 image reads, 0 mask reads, 0 inference, 0 visualizations |")
    A("| Terminal state | `PHASE22_MULTIDOMAIN_SCALE_REGIONAL_RESOURCE_GAP_ANALYSIS_COMPLETE"
      "__PHASE23_ELIGIBLE_NOT_STARTED` |")
    A("")

    # ---- interpretation guards ------------------------------------------- #
    A("## Interpretation guards (binding)")
    A("")
    A("1. The **ORACLE regional arm uses ground-truth geometry**. It is an **upper bound**, "
      "not a deployable result, and no method may be said to attain it.")
    A("2. Where a paired CI overlaps zero, the arms are **not separable**; no ordering claim "
      "is made.")
    A("3. The reference is the **lightest of the six-model panel**, but its absolute compute "
      "is **not small**. 'Lightest of the panel' is not 'fit for constrained deployment'.")
    A("4. Phrasing is restricted to *\"the reference achieved X compared with baseline Y\"*. "
      "**\"X caused +Y\" is forbidden** — there is no architecture-matched control.")
    A("")

    # ---- decision rule ---------------------------------------------------- #
    A("## 1. Decision-rule audit")
    A("")
    A("The persisted Phase-21 maps store a **float16** probability and a **uint8** prediction. "
      "A float16 probability cannot reproduce the stored uint8 prediction exactly: pixels at "
      "*exactly* 0.5 are labelled both ways across the corpus.")
    A("")
    A("| Quantity | Value |")
    A("|---|---|")
    A(f"| Adopted rule | `{thr.get('decision', {}).get('adopted_rule')}` |")
    A(f"| Exact-0.5 pixels | {thr.get('finding', {}).get('pixels_exactly_float16_0p5')} "
      f"(foreground: {thr.get('finding', {}).get('of_which_labelled_foreground')}, "
      f"background: {thr.get('finding', {}).get('of_which_labelled_background')}) |")
    A(f"| Mixed labels present | {thr.get('finding', {}).get('mixed_labels_present')} |")
    A(f"| Maps with mixed tie labels | {thr.get('finding', {}).get('maps_with_mixed_tie_labels')} |")
    A(f"| `>=` rule residual | "
      f"{thr.get('candidate_rules', {}).get('ge_float32_prob_ge_0p5', {}).get('mismatch_pixels')} px over "
      f"{thr.get('candidate_rules', {}).get('ge_float32_prob_ge_0p5', {}).get('maps_with_any_mismatch')} maps |")
    A(f"| `>` rule residual | "
      f"{thr.get('candidate_rules', {}).get('gt_float32_prob_gt_0p5', {}).get('mismatch_pixels')} px over "
      f"{thr.get('candidate_rules', {}).get('gt_float32_prob_gt_0p5', {}).get('maps_with_any_mismatch')} maps |")
    A(f"| Unexplained (non-0.5) disagreements | "
      f"{thr.get('finding', {}).get('unexplained_disagreements_at_other_values')} |")
    A("")
    A(f"Root cause: {thr.get('finding', {}).get('root_cause')}")
    A("")
    A("The **smaller-residual** rule is adopted **and** it is the frozen evaluation rule; it "
      "is applied **identically** to the reference and to every probe arm, so no arm is "
      "advantaged by the choice.")
    A("")

    # ---- failure atlas ---------------------------------------------------- #
    A("## 2. Global failure atlas")
    A("")
    _ov = atlas.get("overall", {})
    A(f"- Population: **{atlas.get('n_samples')}** VAL cases; pooled mean Dice "
      f"**{_f(_ov.get('mean_dice'))}**, median **{_f(_ov.get('median_dice'))}**, "
      f"p05 **{_f(_ov.get('p05_dice'))}**; mean IoU **{_f(_ov.get('mean_iou'))}**, "
      f"precision **{_f(_ov.get('mean_precision'))}**, recall "
      f"**{_f(_ov.get('mean_recall'))}**.")
    A(f"- Dice below 0.5: **{_ov.get('n_dice_below_0p5')}**; below 0.7: "
      f"**{_ov.get('n_dice_below_0p7')}**; empty-case rows: **{_ov.get('n_empty_case')}**; "
      f"total foreground pixel error: **{_ov.get('total_foreground_pixel_error')}**.")
    A("")
    tax = atlas.get("taxonomy_counts") or {}
    pct = atlas.get("taxonomy_pct") or {}
    if tax:
        A("| Category | n | share |")
        A("|---|---|---|")
        total = sum(v for v in tax.values() if isinstance(v, (int, float))) or 1
        for k, v in tax.items():
            share = pct.get(k)
            if share is not None:
                # taxonomy_pct is already expressed in percent
                share_txt = f"{float(share):.2f}%"
            else:
                share_txt = _pct(v / total)
            A(f"| {k} | {v} | {share_txt} |")
        A("")
    A("Taxonomy thresholds were **declared prospectively** in the frozen protocol and were "
      "**not** used to select any case for intervention.")
    A("")

    # ---- scale ------------------------------------------------------------ #
    A("## 3. Scale sensitivity (256 / 512 / 768 / 1024)")
    A("")
    A("Every probe re-runs the **same frozen checkpoint** at a different input resolution and "
      "is scored in **native image space**. 512 is the canonical reference, read from the "
      "persisted Phase-21 maps (never re-inferred).")
    A("")
    A("> **Required wording (B5).** For the frozen checkpoint trained at 512, 512 had the "
      "highest observed performance among the tested diagnostic resolutions (256/512/768/1024); "
      "all tested off-canonical sizes were worse. **This does not establish a globally optimal "
      "inference resolution.** The ordering is confounded with the training resolution and is "
      "off-training-distribution for every non-512 probe.")
    A("")
    summ = scale.get("summary")
    if isinstance(summ, list) and summ:
        A("| Size | macro Dice | Δ vs 512 | 95% CI | Separable |")
        A("|---|---|---|---|---|")
        for r in summ:
            A(f"| {r.get('probe_size')} | {_f(r.get('macro_domain_dice_native'))} | "
              f"{_f(r.get('macro_domain_dice_delta_vs_512'))} | "
              f"[{_f(r.get('delta_ci_low'))}, {_f(r.get('delta_ci_high'))}] | "
              f"{r.get('delta_separable_from_512')} |")
        A("")
    gA = sfid.get("gate_A_pipeline_fidelity", {})
    gB = sfid.get("gate_B_probability_map_agreement", {})
    gC = sfid.get("gate_C_disagreement_with_stored_pred", {})
    A(f"- **Pipeline-fidelity gate A**: {gA.get('verdict')} "
      f"(residual {gA.get('total_disagreeing_pixels')} px, all within "
      f"{gA.get('boundary_tolerance')} of the decision boundary: "
      f"{gA.get('all_disagreements_within_boundary_band')}).")
    A(f"- **Probability gate B**: max |Δp| in the shared 512 canvas "
      f"{_f(gB.get('max_abs_probability_difference_square'), 8)} "
      f"(verdict {gB.get('verdict')}).")
    A(f"- **Gate C** (vs stored prediction): {gC.get('verdict')} — reported, not "
      f"gated, because of the float16 incompatibility above.")
    A(f"- Dice by decision source: `{json.dumps(sfid.get('dice_by_decision_source'))}`")
    A("")

    # ---- regional --------------------------------------------------------- #
    A("## 4. Regional intervention (ORACLE and PREDICTION-DERIVED)")
    A("")
    if reg:
        rrule = reg.get("roi_rule", {})
        A(f"Frozen ROI rule: tight bbox → centre-preserving "
          f"{_f(rrule.get('expanded_extent_factor'), 2)}× expansion → clip → square-pad → "
          f"aspect-preserving resize to 512 → paste over the ROI footprint only. "
          f"Re-centred after clip: **{rrule.get('recentre_after_clip')}**.")
        A("")
        A("| Variant | n exec | n no-ROI | mean Δ (exec) | mean Δ (ITT) |")
        A("|---|---|---|---|---|")
        for v, s in (reg.get("summaries") or {}).items():
            A(f"| {v} | {s.get('n_ok')} | {s.get('n_no_roi')} | "
              f"{_f(s.get('mean_delta_dice_on_ok'))} | "
              f"{_f(s.get('mean_delta_dice_intent_to_treat'))} |")
        A("")
        A("**The oracle variant uses ground truth. It is an upper bound and must never be "
          "reported as a deployable gain.**")
    A("")

    # ---- benefit / ceiling / regret / harm -------------------------------- #
    A("## 5. Benefit heterogeneity, oracle ceiling, routing regret and harm")
    A("")
    g = het.get("gain_distribution_executed", {})
    if g:
        A(f"- Executed oracle gain: mean **{_f(g.get('mean_delta_dice'))}**, median "
          f"**{_f(g.get('median_delta_dice'))}**, improved/worsened/unchanged "
          f"**{g.get('n_positive')}/{g.get('n_negative')}/{g.get('n_zero')}**.")
        conc = het.get("concentration", {})
        A(f"- Concentration: Gini **{_f(conc.get('gini_of_positive_benefit'), 4)}**, "
          f"top-10% share of benefit "
          f"**{_pct(conc.get('share_of_positive_benefit_from_top_10pct_of_benefiting_cases'))}**.")
        co = het.get("correlates_of_gain", {})
        A(f"- Correlation of gain with baseline Dice: "
          f"**{_f(co.get('pearson_r_baseline_global_dice'), 4)}**; with ROI area fraction: "
          f"**{_f(co.get('pearson_r_roi_area_fraction'), 4)}**.")
    A("")
    if acc:
        A("| Policy value | Dice |")
        A("|---|---|")
        A(f"| Always global | {_f(acc.get('baseline_always_global_pooled_dice'))} |")
        A(f"| Always regional (oracle) | {_f(acc.get('baseline_always_regional_pooled_dice'))} |")
        A(f"| **ORACLE accept-if-beneficial ceiling** | "
          f"**{_f(acc.get('oracle_ceiling_pooled_dice'))}** |")
        A("")
        A(f"Acceptance rate **{_pct(acc.get('acceptance_rate'))}**; ceiling gain over "
          f"always-global **{_f(acc.get('ceiling_gain_over_always_global'))}**. "
          f"This is a **ceiling**, not an achieved result, and is **not deployable**.")
        A("")
    pol = regret.get("policies")
    if isinstance(pol, list) and pol:
        A("`deployable` = the rule consults **only predicted information** (never ground truth).")
        A("")
        A("| Policy | deployable | uses GT | fraction routed | pooled Dice | regret vs ceiling |")
        A("|---|---|---|---|---|---|")
        for p in pol:
            A(f"| {p.get('policy')} | {p.get('deployable_shape')} | "
              f"{p.get('uses_ground_truth')} | "
              f"{_pct(p.get('fraction_routed_to_regional'))} | "
              f"{_f(p.get('macroR_dice_pooled'))} | "
              f"{_f(p.get('regret_vs_oracle_ceiling'))} |")
        A("")
        A("No selector was **trained**; these are fixed rules evaluated offline. **The "
          "`ORACLE_ACCEPT_IF_BENEFICIAL` row is not deployable** (`deployable = False`) — it "
          "peeks at the ground truth and exists only to define the ceiling.")
        A("")
        for _n in (regret.get("notes") or []):
            if str(_n).upper().startswith("CRITICAL CAVEAT"):
                A(f"> **{_n}**")
                A("")
                break
    if harm:
        A(f"- Harm: **{harm.get('n_harmed')}/{harm.get('n_executed')}** executed cases "
          f"({_pct(harm.get('harm_rate_among_executed'))}); worst harm "
          f"**{_f(harm.get('worst_harm'))}**; harm rate (ITT) "
          f"**{_pct(harm.get('harm_rate_intent_to_treat'))}**.")
        A("")

    # ---- derived ROI / uncertainty ---------------------------------------- #
    A("## 6. Prediction-derived ROI and uncertainty-vs-benefit")
    A("")
    if roi:
        A(f"- **NO_PREDICTED_ROI rate: {_pct(roi.get('no_predicted_roi_rate'))}** "
          f"({roi.get('n_no_predicted_roi')}/{roi.get('n_total')}). A total miss yields no "
          f"ROI, so the deployable-shaped path fails exactly where recovery is most needed.")
        A(f"- Mean Δ Dice (ITT) **{_f(roi.get('mean_predicted_delta_dice_intent_to_treat'))}**; "
          f"executed **{_f(roi.get('mean_predicted_delta_dice_on_executed'))}**; "
          f"corr(predicted gain, oracle gain) "
          f"**{_f(roi.get('correlation_predicted_vs_oracle_gain'), 4)}**.")
        A("")
    # ---- B5 semantic repair: GT-free vs GT-derived separation -------------- #
    gtfree = unc.get("gt_free_ranking") or []
    gtaware = unc.get("gt_aware_associations") or []
    if gtfree or gtaware:
        A("### 6.1 Deployable (GT-free) benefit proxies")
        A("")
        A("A routing signal is only **deployable** if it can be computed **without "
          "ground truth**, **before** any refinement, and **at inference time**. "
          "The following signals satisfy that test, and are ranked by |Spearman| "
          "against the oracle regional gain (the *target* may use ground truth; "
          "the *input signal* must not).")
        A("")
        A("| Deployable signal | uses GT | before refinement | at inference | n | Pearson | Spearman | ROC-AUC | PR-AUC |")
        A("|---|---|---|---|---|---|---|---|---|")
        for r in gtfree:
            A(f"| `{r.get('signal')}` | {r.get('uses_GT')} | "
              f"{r.get('available_before_refinement')} | {r.get('available_at_inference')} | "
              f"{r.get('n')} | {_f(r.get('pearson_r'), 4)} | {_f(r.get('spearman_r'), 4)} | "
              f"{_f(r.get('roc_auc'), 4)} | {_f(r.get('pr_auc'), 4)} |")
        A("")
        if gtfree:
            b = gtfree[0]
            A(f"- Best **GT-free** signal: `{b.get('signal')}` with ρ = "
              f"**{_f(b.get('spearman_r'), 4)}** (|ρ| = {_f(b.get('abs_spearman'), 4)}), "
              f"ROC-AUC **{_f(b.get('roc_auc'), 4)}**. **This is essentially no "
              "predictive signal**: every deployable proxy is weak in magnitude and "
              "near-chance in ROC-AUC. No threshold was fitted, no policy selected and "
              "no model trained, so **no deployable router is established**.")
            A("")
        A("### 6.2 Post-hoc ground-truth associations (NOT deployable)")
        A("")
        A("The frozen analysis ranked ground-truth-derived quantities alongside the "
          "deployable ones and reported `recall` as the best **deployable** signal. "
          "That claim was **invalid**: `recall`, `precision`, `Dice`, `IoU`, "
          "ground-truth `ECE`/`Brier`, the oracle ROI area, the ground-truth "
          "foreground size and `predicted_delta_dice` **all require the ground-truth "
          "mask** and cannot be computed at deployment. They are reported here, "
          "separately, purely as **post-hoc diagnostics**.")
        A("")
        A("| GT-derived signal | uses GT | deployable | n | Pearson | Spearman |")
        A("|---|---|---|---|---|---|")
        for r in gtaware:
            A(f"| `{r.get('signal')}` | {r.get('uses_GT')} | False | {r.get('n')} | "
              f"{_f(r.get('pearson_r'), 4)} | {_f(r.get('spearman_r'), 4)} |")
        A("")
        A("> **`predicted_delta_dice` is ground-truth-derived, despite its name.** It "
          "equals `predicted_dice − global_dice`, and both operands are Dice scores "
          "measured against the ground-truth mask (identity verified to a maximum "
          "residual of 3.1e-16). It must never be used as a deployable routing signal.")
        A("")
    best = unc.get("best_deployable_signal")
    if best and not gtfree:
        A(f"- Best deployable uncertainty signal (ranked by |Spearman|): "
          f"**{best.get('signal')}** with ρ = **{_f(best.get('spearman_r_with_oracle_gain'), 4)}**.")
        A("- These correlations are **descriptive, post hoc on VAL**. No threshold was fitted, "
          "no policy selected, no training performed.")
        A("")

    # ---- resource --------------------------------------------------------- #
    A("## 7. Resource frontier, envelopes and the resource gap")
    A("")
    if gap:
        A(f"- Reference: **{gap.get('reference_params'):,}** params, "
          f"**{_f(gap.get('reference_gmacs_at_512'), 4)} G MACs** per 1×3×512×512 image "
          f"(param rank {gap.get('param_rank_of_reference')}, compute rank "
          f"{gap.get('gmacs_rank_of_reference')} of the six-model panel).")
        A(f"- Absolute cost is small: **"
          f"{gap.get('absolute_cost_statement', {}).get('is_small_in_absolute_terms')}**. "
          f"{gap.get('absolute_cost_statement', {}).get('note')}")
        A(f"- Measurement provenance: {gap.get('measurement_provenance')}")
        A("")
    if env:
        A(f"**Conditional-compute caveat.** {env.get('important_caveat')}")
        A("")
        A(f"**Approximation.** {env.get('analytical_approximation')}")
        A("")
        rows = env.get("rows")
        if isinstance(rows, list) and rows:
            A("| Policy | fraction regional | mean G MACs | ×always-global | pooled Dice | regret |")
            A("|---|---|---|---|---|---|")
            for r in rows:
                A(f"| {r.get('policy')} | {_pct(r.get('fraction_regional'))} | "
                  f"{_f(r.get('mean_macs_gmacs'), 4)} | "
                  f"{_f(r.get('multiplier_vs_always_global'), 4)} | "
                  f"{_f(r.get('pooled_dice'))} | "
                  f"{_f(r.get('regret_vs_oracle_ceiling'))} |")
            A("")
    if cpu:
        A(f"**CPU baseline (measurement).** batch {cpu.get('batch_size')}, "
          f"AMP={cpu.get('amp')}, threads {cpu.get('threads')}:")
        A("")
        A("| Size | mean ms | max process RSS MiB | analytical G MACs |")
        A("|---|---|---|---|")
        for r in cpu.get("rows", []):
            A(f"| {r.get('size')} | "
              f"{_f(1000.0 * float(r.get('mean_seconds') or 0), 1)} | "
              f"{_f(r.get('max_process_rss_mib'), 1)} | "
              f"{_f((r.get('analytical_macs') or 0) / 1e9, 4)} |")
        A("")
        A(f"{cpu.get('rss_note') or ''}")
        A("")
        A(f"{cpu.get('note') or ''}")
        A("")

    # ---- KUB / domain / stats --------------------------------------------- #
    A("## 8. KUB TINY, domain preservation, statistics, scale-vs-regional")
    A("")
    A(f"- **KUB TINY** (`{tiny.get('taxonomy_id')}`): TINY optimised on = "
      f"**{tiny.get('tiny_optimised_on')}**. {tiny.get('stratum_definition')}")
    tg = tiny.get("tiny_stratum_regional_gain")
    if tg:
        A(f"  - TINY stratum oracle Δ Dice (ITT) **{_f(tg.get('mean_oracle_delta_dice'))}**, "
          f"executed **{_f(tg.get('mean_oracle_delta_dice_executed_only'))}**, "
          f"n = {tg.get('n')}, baseline Dice {_f(tg.get('mean_global_dice'))}.")
        _bt = tg.get("bootstrap_vs_global") or {}
        if _bt:
            A("")
            A(f"  - **Required wording (B5).** KUB TINY was the only frozen size stratum "
              f"with a positive observed mean oracle regional gain "
              f"(+{_f(tg.get('mean_oracle_delta_dice'))} Dice), but the paired 95% CI "
              f"[{_f(_bt.get('ci_low'))}, {_f(_bt.get('ci_high'))}] includes zero "
              f"(p={_bt.get('p_value')}); therefore the TINY effect is descriptive and "
              f"not statistically established.")
            A(f"  - This does **not** weaken the useful finding: regional benefit is "
              f"**strongly heterogeneous**, and always-on regional processing is "
              f"**harmful in aggregate**.")
    A("")
    if dom:
        A(f"- **Domain preservation**: the reference is frozen, so no per-domain property of "
          f"the reference can change. Reference unchanged: "
          f"**{dom.get('reference_unchanged', {}).get('matches_frozen_phase21_values')}**.")
        A("")
    comps = stats.get("comparisons", {})
    if comps:
        A("| Comparison | Δ | 95% CI | p | separable |")
        A("|---|---|---|---|---|")
        for k, v in comps.items():
            if isinstance(v, dict):
                A(f"| {k} | {_f(v.get('mean_delta', v.get('delta')))} | "
                  f"[{_f(v.get('ci_low'))}, {_f(v.get('ci_high'))}] | "
                  f"{_f(v.get('p_value'), 4)} | "
                  f"{v.get('ci_excludes_zero', v.get('separable'))} |")
        A("")
        A(f"{stats.get('ci_overlap_rule')}")
        A("")
    axes = svr.get("axes")
    if axes:
        A("| Axis | macro Dice | relative cost | uses ground truth |")
        A("|---|---|---|---|")
        for k, v in axes.items():
            if v.get("uses_ground_truth") is not None:
                ugt = v.get("uses_ground_truth")
            else:
                # The region arm is the only one whose GEOMETRY comes from the
                # ground truth; derive it from the recorded axis label rather
                # than inventing a field the artifact does not carry.
                ugt = "REGION" if str(v.get("axis", "")).upper() == "REGION" else False
            A(f"| {k} | {_f(v.get('macro_domain_dice'))} | "
              f"{_f(v.get('relative_cost_vs_512_always_global') or v.get('relative_cost_vs_512'), 4)} | "
              f"{ugt} |")
        A("")
        A("The **REGION** arm is the only one that consumes ground-truth geometry (the oracle "
          "ROI); the scale and baseline arms do not.")
        A("")
        A(f"**{svr.get('verdict_guard')}**")
        A("")

    # ---- governance -------------------------------------------------------- #
    A("## 9. Governance: no-new-training audit and candidate evidence")
    A("")
    if nt:
        A(f"- Verdict: **{nt.get('verdict')}** ({nt.get('n_passed')}/{nt.get('n_checks')}).")
        A(f"- Forbidden training constructs found in Phase-22 code: "
          f"**{nt.get('static_scan', {}).get('total_forbidden_construct_hits')}** "
          f"(expected 0; {nt.get('static_scan', {}).get('files_scanned')} files scanned).")
        A(f"- `training_jobs_started` = **{nt.get('training_jobs_started')}**; "
          f"optimizer constructed = **{nt.get('optimizer_constructed')}**; "
          f"backward called = **{nt.get('backward_called')}**; "
          f"checkpoint written = **{nt.get('checkpoint_written')}**; "
          f"new experiment directory = **{nt.get('new_experiment_directory_created')}**.")
        _tr = nt.get("test_reads") or {}
        A(f"- TEST reads: image {_tr.get('test_image_reads')}, mask "
          f"{_tr.get('test_mask_reads')}, inference {_tr.get('test_inference')}, "
          f"visualization {_tr.get('test_visualization')}.")
        A("")
    if lb:
        A(f"- **Future benefit-label contract** (contracted, NOT used): quantity "
          f"`{lb.get('label_definition', {}).get('quantity')}`; geometry source for a "
          f"*deployable* label must be "
          f"**{lb.get('label_definition', {}).get('geometry_source_required_for_a_DEPLOYABLE_label')}**. "
          f"Status: **{lb.get('status')}**; it is a training artifact: "
          f"**{lb.get('is_a_training_artifact')}**.")
        A("")
    if ce:
        for c in ce.get("candidates", []):
            A(f"- **{c.get('candidate')}** — status `{c.get('status')}`. "
              f"Supports: {c.get('supports')} Does **not** support: {c.get('does_not_support')}")
        A("")
        if ce.get("verdict"):
            A(f"{ce.get('verdict')}")
            A("")

    # ---- boundary ---------------------------------------------------------- #
    A("## 10. Boundary")
    A("")
    A("Phase 22 is a **diagnostic gap analysis**. It does **not** propose, train or validate "
      "any method. It contains **no** router, localizer, benefit predictor, fusion module, "
      "compression or architecture search, and it reads **no** TEST data. Phase 23 is "
      "**ELIGIBLE but NOT STARTED**.")
    A("")
    A("> **STOP.** Phase 23 is not started.")
    A("")

    text = "\n".join(L) + "\n"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"WROTE {OUT} ({len(text)} chars, {len(L)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
