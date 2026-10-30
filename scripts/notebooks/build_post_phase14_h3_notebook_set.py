from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "notebooks" / "phasewise" / "post_phase14_h3_proposal_supply"
OUT.mkdir(parents=True, exist_ok=True)


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": dedent(text).strip("\n").splitlines(True)}


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": dedent(text).strip("\n").splitlines(True),
    }


DISCOVERY = """
from pathlib import Path
import hashlib
import json
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

def discover_repo(start=None):
    candidates = []
    if start is not None:
        candidates.append(Path(start).resolve())
    candidates.extend([Path.cwd().resolve(), Path.cwd().resolve().parent])
    try:
        candidates.append(Path(__file__).resolve())
    except NameError:
        pass
    for candidate in candidates:
        current = candidate if candidate.is_dir() else candidate.parent
        for root in (current, *current.parents):
            if all((root / name).is_dir() for name in ("scripts", "reports", "manifests", "notebooks")):
                return root
    fallback = Path(r"D:/Softfors/jup")
    if all((fallback / name).is_dir() for name in ("scripts", "reports", "manifests", "notebooks")):
        return fallback
    raise RuntimeError("Repository root not found: expected scripts/, reports/, manifests/, notebooks/.")

ROOT = discover_repo()
AUDITS = ROOT / "reports" / "audits"
TABLES = ROOT / "reports" / "tables"

def load_json(relative):
    with (ROOT / relative).open("r", encoding="utf-8") as handle:
        return json.load(handle)

def read_csv(relative):
    return pd.read_csv(ROOT / relative)

def sha(relative):
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()

print("Repository root:", ROOT)
print("No training or inference is executed by this notebook.")
"""


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


root_cause_cells = [
    md(
        """
        # 01 — Post-Phase14 Proposal Root-Cause Diagnostic

        This is a reproducibility notebook for the completed post-Phase14 causal decomposition.
        It loads saved JSON/CSV artifacts only. It does not retrain, run inference, access TEST,
        start Phase 15, or perform H3 training/evaluation.

        Phase-14 terminal state: `DIAGNOSTIC_PROPOSAL_BOTTLENECK`.
        Final root-cause classification: `F_MIXED_BOTTLENECK`.
        """
    ),
    code(DISCOVERY),
    code(
        """
        root_cause = load_json("reports/audits/phase14_diag_root_cause.json")
        mode_summary = read_csv("reports/tables/phase14_clean_v3_mode_summary.csv")
        proposal_by_stratum = root_cause["section5_proposal_supply"]["by_stratum"]
        print("Population:", root_cause["population"])
        print("Frozen proposal policy: threshold=0.10, margin=0.20, top_k=5, NMS IoU=0.30")
        """
    ),
    md("## 1. Population and proposal supply"),
    code(
        """
        strata = list(proposal_by_stratum)
        supply = pd.DataFrame([
            {
                "stratum": s,
                **proposal_by_stratum[s],
            }
            for s in strata
        ])
        display(supply[[
            "stratum", "n_components", "zero_proposal_components", "zero_proposal_rate",
            "proposal_recall_any_overlap", "proposal_recall_cov_ge_0.50",
            "proposal_recall_cov_ge_0.90", "best_proposal_coverage_mean",
            "best_proposal_coverage_median", "best_proposal_bbox_iou_mean",
        ]])
        overall = root_cause["section5_proposal_supply"]["overall"]
        overall_table = pd.DataFrame([
            ("total proposals", overall["n_proposals_total"]),
            ("proposals/image mean", overall["proposals_per_image_mean"]),
            ("proposals/image median", overall["proposals_per_image_median"]),
            ("proposals/image p90", overall["proposals_per_image_p90"]),
            ("TP proposals", overall["n_tp_proposals"]),
            ("TP fraction (%)", overall["proposal_precision_TP_fraction"]),
            ("background FP proposals", overall["n_fp_background_proposals"]),
            ("background FP fraction (%)", overall["background_proposal_fraction"]),
            ("duplicate proposals", overall["n_duplicate_proposals"]),
            ("duplicate burden (%)", overall["duplicate_proposal_rate"]),
            ("zero-proposal GT components", sum(proposal_by_stratum[s]["zero_proposal_components"] for s in strata)),
        ], columns=["metric", "value"])
        display(overall_table)
        """
    ),
    md("## 2. Supply recall, geometry, and conditional refiner behavior"),
    code(
        """
        fig, ax = plt.subplots(figsize=(8, 4.8))
        ax.bar(supply["stratum"], supply["zero_proposal_rate"], color="tab:red")
        ax.set(title="Zero-Proposal GT Components by Size Stratum", xlabel="Size stratum", ylabel="Percent")
        ax.grid(True, axis="y", alpha=0.3); plt.show()

        fig, ax = plt.subplots(figsize=(8, 4.8))
        ax.plot(supply["stratum"], supply["proposal_recall_any_overlap"], marker="o", label="any overlap")
        ax.plot(supply["stratum"], supply["proposal_recall_cov_ge_0.90"], marker="o", label="coverage >= 0.90")
        ax.set(title="Proposal Recall by Size Stratum", xlabel="Size stratum", ylabel="Percent")
        ax.grid(True, alpha=0.3); ax.legend(); plt.show()

        geometry = pd.DataFrame([root_cause["section6_geometry_bridge"]])
        display(geometry.T.rename(columns={0: "value"}))
        conditional = []
        for key, value in root_cause["section7_conditional_refiner"]["by_coverage_stratum"].items():
            conditional.append({"coverage_stratum": key, **value})
        display(pd.DataFrame(conditional))
        """
    ),
    code(
        """
        coverage = pd.DataFrame([
            ("COV_GE_0.90", 60, 0.9955, 0.8621, 55.0),
            ("COV_0.50_0.90", 12, 0.7760, 0.3910, 66.67),
            ("COV_LT_0.50", 1, 0.1175, 0.0245, 100.0),
            ("NO_MATCHED_PROPOSAL", 79, 0.0, 0.0, 35.44),
        ], columns=["coverage stratum", "components", "mean best proposal coverage",
                    "mean refiner crop coverage", "refiner improves global rate (%)"])
        display(coverage)
        fig, ax = plt.subplots(figsize=(8, 4.8))
        ax.bar(coverage["coverage stratum"], coverage["mean refiner crop coverage"], color="tab:purple")
        ax.set(title="Refiner Crop Coverage by Proposal-Coverage Stratum",
               xlabel="Coverage stratum", ylabel="Mean refiner crop coverage")
        ax.tick_params(axis="x", rotation=20); ax.grid(True, axis="y", alpha=0.3); plt.show()
        """
    ),
    md("## 3. Counterfactual comparisons"),
    code(
        """
        counter = root_cause["section8_counterfactuals"]
        dice = pd.DataFrame({
            "condition": ["GLOBAL_ONLY", "PREDICTED", "ORACLE_SEL", "FP_REMOVED"],
            "mean Dice": [
                counter["image_dice"]["GLOBAL_ONLY_mean"],
                counter["image_dice"]["PREDICTED_mean"],
                counter["image_dice"]["ORACLE_SEL_mean"],
                counter["image_dice"]["FP_REMOVED_mean"],
            ],
        })
        display(dice)
        fp = pd.DataFrame({
            "condition": ["PREDICTED", "ORACLE_SEL", "FP_REMOVED"],
            "FP components/image": [counter["fp_burden"][f"{x}_mean"] for x in ["PREDICTED", "ORACLE_SEL", "FP_REMOVED"]],
        })
        display(fp)
        recall = pd.DataFrame(counter["component_recall90"]).T
        display(recall)

        fig, ax = plt.subplots(figsize=(8, 4.8))
        ax.bar(dice["condition"], dice["mean Dice"], color=["tab:gray", "tab:red", "tab:green", "tab:blue"])
        ax.set(title="Dice Counterfactual Comparison", xlabel="Condition", ylabel="Mean Dice")
        ax.grid(True, axis="y", alpha=0.3); plt.show()

        fig, ax = plt.subplots(figsize=(8, 4.8))
        ax.bar(fp["condition"], fp["FP components/image"], color=["tab:red", "tab:green", "tab:blue"])
        ax.set(title="False-Positive Burden Counterfactual Comparison",
               xlabel="Condition", ylabel="Mean FP components / image")
        ax.grid(True, axis="y", alpha=0.3); plt.show()
        """
    ),
    md("## 4. Mechanism attribution and terminal interpretation"),
    code(
        """
        attribution = root_cause["section9_failure_attribution"]
        mechanism = pd.DataFrame([
            ("A_PROPOSAL_SUPPLY_RECALL_LIMITATION", attribution["mechanism_scores"]["A_PROPOSAL_SUPPLY_RECALL_LIMITATION"], "primary"),
            ("B_PROPOSAL_GEOMETRY_LIMITATION", attribution["mechanism_scores"]["B_PROPOSAL_GEOMETRY_LIMITATION"], "refuted"),
            ("C_PROPOSAL_CONTAMINATION_LIMITATION", attribution["mechanism_scores"]["C_PROPOSAL_CONTAMINATION_LIMITATION"], "secondary"),
            ("D_PROPOSAL_RANKING_LIMITATION", attribution["mechanism_scores"]["D_PROPOSAL_RANKING_LIMITATION"], "refuted"),
            ("E_REFINER_DOMAIN_SHIFT_ON_PREDICTED_CROPS", attribution["mechanism_scores"]["E_REFINER_DOMAIN_SHIFT_ON_PREDICTED_CROPS"], "refuted"),
        ], columns=["mechanism", "score", "role"])
        display(mechanism)
        fig, ax = plt.subplots(figsize=(10, 4.8))
        ax.barh(mechanism["mechanism"], mechanism["score"], color=["tab:red", "tab:gray", "tab:orange", "tab:gray", "tab:gray"])
        ax.set(title="Mechanism-Score Comparison", xlabel="Mechanism score", ylabel="Mechanism")
        ax.grid(True, axis="x", alpha=0.3); plt.show()
        print("Dominant:", attribution["dominant_mechanism"])
        print("Primary:", attribution["primary_mechanism"])
        print("Secondary:", attribution["secondary_mechanism"])
        assert attribution["dominant_mechanism"] == "F_MIXED_BOTTLENECK"
        assert attribution["primary_mechanism"] == "A_PROPOSAL_SUPPLY_RECALL_LIMITATION"
        assert attribution["secondary_mechanism"] == "C_PROPOSAL_CONTAMINATION_LIMITATION"
        assert root_cause["governance"]["test_split_reads"] == 0
        assert root_cause["governance"].get("external_test_reads", 0) == 0
        assert root_cause["governance"].get("external_data_used", False) is False
        print("TEST: CLOSED; Phase 15: NOT_STARTED_AND_NOT_AUTHORIZED")
        """
    ),
    md("## 5. Provenance and boundary"),
    code(
        """
        provenance_paths = [
            "reports/audits/phase14_diag_root_cause.json",
            "reports/tables/phase14_diag_proposal_level.csv",
            "reports/tables/phase14_diag_component_level.csv",
            "reports/tables/phase14_diag_geometry_bridge.csv",
            "reports/tables/phase14_diag_conditional_refiner.csv",
            "reports/tables/phase14_clean_v3_mode_summary.csv",
        ]
        display(pd.DataFrame([{"path": p, "SHA-256": sha(p)} for p in provenance_paths]))
        print("No new inference or training was performed.")
        """
    ),
]

axis_cells = [
    md(
        """
        # 02 — H3 Axis-Priority Diagnostic

        This notebook records the prospectively frozen A-only versus C-only causal priority
        diagnostic. It uses saved results only and does not train H3, evaluate a checkpoint,
        access TEST, or authorize Phase 15.
        """
    ),
    code(DISCOVERY),
    code(
        """
        axis = load_json("reports/audits/post_phase14_h3_axis_priority_results.json")
        conditions = axis["conditions"]
        print("Scientific question: which single causal axis has priority for the missing regional Tiny-recall signal?")
        print("Frozen interventions: A_ONLY=GT-assisted supply completion; C_ONLY=FP removal; A+C=upper bound.")
        """
    ),
    md("## 1. Frozen conditions and complete comparison"),
    code(
        """
        rows = []
        for condition, metrics in conditions.items():
            rows.append({"condition": condition, **metrics})
        comparison = pd.DataFrame(rows)
        display(comparison)
        quantities = pd.DataFrame([
            ("R_A", axis["causal_quantities"]["R_A"], "A-only retained fraction of Oracle Tiny-recall gap"),
            ("R_C", axis["causal_quantities"]["R_C"], "C-only retained fraction of Oracle Tiny-recall gap"),
            ("R_AC", axis["causal_quantities"]["R_AC"], "A+C retained fraction of Oracle Tiny-recall gap"),
        ], columns=["quantity", "value", "definition"])
        display(quantities)
        """
    ),
    md("## 2. Causal priority visualizations"),
    code(
        """
        for column, title, ylabel in [
            ("recall_TINY", "Tiny Recall Comparison Across Conditions", "Tiny Recall"),
            ("dice_mean", "Dice Comparison Across Conditions", "Mean Dice"),
            ("fp_components_per_image", "False-Positive Burden Across Conditions", "FP components / image"),
        ]:
            fig, ax = plt.subplots(figsize=(9, 4.8))
            ax.bar(comparison["condition"], comparison[column], color=["tab:gray", "tab:red", "tab:orange", "tab:blue", "tab:green", "tab:purple"])
            ax.set(title=title, xlabel="Condition", ylabel=ylabel)
            ax.tick_params(axis="x", rotation=20); ax.grid(True, axis="y", alpha=0.3); plt.show()
        fig, ax = plt.subplots(figsize=(8, 4.8))
        r = quantities["value"]
        ax.bar(quantities["quantity"], r, color=["tab:red", "tab:orange", "tab:blue"])
        ax.set(title="Causal Retention Quantities", xlabel="Quantity", ylabel="R value")
        ax.grid(True, axis="y", alpha=0.3); plt.show()
        """
    ),
    md("## 3. Necessity, sufficiency, and priority rule"),
    code(
        """
        necessity = pd.DataFrame([
            ("A_supply", axis["causal_necessity"]["A_supply"]),
            ("C_contamination", axis["causal_necessity"]["C_contamination"]),
        ], columns=["axis", "causal necessity"])
        sufficiency = pd.DataFrame([
            ("A_supply", axis["causal_sufficiency"]["A_supply"]),
            ("C_contamination", axis["causal_sufficiency"]["C_contamination"]),
        ], columns=["axis", "causal sufficiency"])
        display(necessity); display(sufficiency)
        print("Priority rule:", axis["priority_rule"]["rule_fired"])
        print("Outcome:", axis["priority_rule"]["outcome"])
        print("Selected axis:", axis["priority_rule"]["eligible_axis"])
        assert axis["priority_rule"]["rule_fired"] == "A_PRIORITY"
        assert axis["h3_readiness"]["outcome"] == "H3_DESIGN_ELIGIBLE__AXIS_PROPOSAL_SUPPLY_RECALL"
        assert axis["h3_readiness"]["eligible_axis"] == "A_PROPOSAL_SUPPLY_RECALL_LIMITATION"
        print("Phase 15: NOT_STARTED_AND_NOT_AUTHORIZED; TEST: CLOSED")
        """
    ),
    md("## 4. Provenance and next-state boundary"),
    code(
        """
        paths = [
            "reports/audits/post_phase14_h3_axis_priority_results.json",
            "reports/audits/post_phase14_h3_axis_priority_protocol.json",
            "reports/audits/post_phase14_h3_axis_priority_execution_audit.json",
            "reports/tables/phase15_h3_axis_priority_component_level.csv",
            "reports/tables/phase15_h3_axis_priority_image_summary.csv",
            "reports/tables/phase15_h3_axis_priority_aonly_injected.csv",
            "reports/tables/phase15_h3_axis_priority_ac_component_level.csv",
        ]
        display(pd.DataFrame([{"path": p, "SHA-256": sha(p)} for p in paths]))
        print("This diagnostic selected one axis; it did not authorize Phase 15 or H3 training.")
        """
    ),
]

design_cells = [
    md(
        """
        # 03 — H3 Design and Final Pretraining Binding

        This notebook records the completed design, pre-execution defect discovery, correction,
        canonical calibration, implementation binding, and dry-run gate. It does not launch or
        evaluate H3 training. The final pretraining state is
        `H3_FINAL_PRETRAINING_BINDING_COMPLETE__AWAITING_TRAINING_AUTHORIZATION`.
        """
    ),
    code(DISCOVERY),
    code(
        """
        correction = load_json("reports/audits/h3_proposal_supply_design_correction.json")
        binding = load_json("reports/audits/h3_proposal_supply_final_pretraining_binding_v2.json")
        protocol = load_json("reports/audits/h3_proposal_supply_design_protocol.json")
        checklist = load_json("reports/audits/h3_proposal_supply_pre_execution_checklist.json")
        selection = load_json("reports/audits/h3_proposal_supply_checkpoint_selection_rule.json")
        launch = load_json("reports/audits/h3_training_launch_binding.json")
        area_distribution = load_json("reports/tables/h3_v2_area_distribution.json")
        area_audit = read_csv("reports/tables/h3_v2_component_area_audit.csv")
        print("Axis:", binding["axis"])
        print("Intervention:", binding["intervention_family"])
        """
    ),
    md("## 1. Axis, intervention, defect, and correction"),
    code(
        """
        display(pd.DataFrame([
            ("selected axis", binding["axis"]),
            ("intervention family", binding["intervention_family"]),
            ("correct mechanistic wording", binding["intervention_wording"]),
            ("defective mapping", correction["supersedes"]["defective_formula"]),
            ("defect classification", correction["supersedes"]["defect_classification"]),
            ("corrected mapping", binding["corrected_mapping"]),
            ("A_ref", binding["authoritative_a_ref"]),
        ], columns=["item", "authoritative record"]))
        print("Degeneracy proof: for every area_i >= 1, 4*sqrt(area_i) >= 4 >= 0.75, so clipping yields sigma=0.75.")
        """
    ),
    md("## 2. Historical calibration reconciliation"),
    code(
        """
        cal = binding["authoritative_calibration_summary"]
        display(pd.DataFrame([
            ("superseded A_ref=14.0", cal["superseded_calibrations"]["14.0"]),
            ("superseded A_ref=12.0", cal["superseded_calibrations"]["12.0"]),
            ("canonical TRAIN images", cal["population"]["n_images"]),
            ("canonical TRAIN components", cal["population"]["n_components"]),
            ("orphan quarantined", cal["population"]["orphan_samples_quarantined"]),
            ("zero-area components", cal["zero_area_count"]),
            ("authoritative A_ref", cal["A_ref"]),
            ("mapping", binding["corrected_mapping"]),
        ], columns=["item", "value"]))
        print("Historical A_ref=14 and 12 are superseded because their relabeled populations violated component cardinality.")
        """
    ),
    md("## 3. Authoritative area distribution and sigma mapping"),
    code(
        """
        percentiles = pd.DataFrame([area_distribution["area128_percentiles"]])
        display(percentiles)
        print("Area distribution source: reports/tables/h3_v2_area_distribution.json")
        """
    ),
    code(
        """
        sigma_stats = binding["authoritative_calibration_summary"]["non_degeneracy"]
        sigma_table = pd.DataFrame([
            ("distinct sigma levels", sigma_stats["n_distinct_sigma_levels"]),
            ("fraction at floor 0.35", sigma_stats["frac_at_floor_0.35"]),
            ("fraction at ceiling 0.75", sigma_stats["frac_at_ceil_0.75"]),
            ("median sigma", sigma_stats["median_sigma"]),
            ("TINY median sigma", sigma_stats["tiny_median_sigma"]),
            ("non-TINY median sigma", sigma_stats["nontiny_median_sigma"]),
            ("TINY < non-TINY", sigma_stats["tiny_lt_nontiny"]),
            ("all in bounds", sigma_stats["all_in_bounds"]),
            ("non-degeneracy passed", sigma_stats["passed"]),
        ], columns=["metric", "value"])
        display(sigma_table)
        areas = area_audit.copy()
        area_col = "area_128"
        areas["sigma_display_only"] = (0.35 + 0.40 * (areas[area_col] / 13.0).pow(0.5)).clip(0.35, 0.75)
        areas.loc[areas[area_col] == 0, "sigma_display_only"] = 0.35
        tiny = areas[areas["size_stratum"] == "TINY"]["sigma_display_only"]
        non_tiny = areas[areas["size_stratum"] != "TINY"]["sigma_display_only"]

        fig, ax = plt.subplots(figsize=(8, 4.8))
        ax.hist(areas["sigma_display_only"], bins=14, color="tab:blue", alpha=0.8)
        ax.set(title="Adaptive Sigma Distribution", xlabel="sigma", ylabel="Component count")
        ax.grid(True, axis="y", alpha=0.3); plt.show()

        fig, ax = plt.subplots(figsize=(7, 4.8))
        ax.boxplot([tiny, non_tiny], tick_labels=["TINY", "non-TINY"], showmeans=True)
        ax.set(title="TINY vs non-TINY Adaptive Sigma", ylabel="sigma")
        ax.grid(True, axis="y", alpha=0.3); plt.show()

        fig, ax = plt.subplots(figsize=(8, 4.8))
        ax.scatter(areas[area_col], areas["sigma_display_only"], s=5, alpha=0.25)
        ax.set(title="Authoritative Component Area vs Adaptive Sigma",
               xlabel="area_128", ylabel="sigma")
        ax.grid(True, alpha=0.3); plt.show()

        floor = (areas["sigma_display_only"] == 0.35).mean()
        ceil = (areas["sigma_display_only"] == 0.75).mean()
        fig, ax = plt.subplots(figsize=(6, 4.5))
        ax.bar(["floor 0.35", "ceiling 0.75"], [floor, ceil], color=["tab:orange", "tab:green"])
        ax.set(title="Sigma Floor/Ceiling Proportions", ylabel="Fraction of components")
        ax.grid(True, axis="y", alpha=0.3); plt.show()
        print("Display-only sigma medians:", tiny.median(), non_tiny.median())
        """
    ),
    md("## 4. Configuration and implementation reconciliation"),
    code(
        """
        reconciliation = binding["reconciliation_compliance_map"]
        display(pd.DataFrame(list(reconciliation.items()), columns=["gate", "correction/status"]))
        display(pd.DataFrame([
            ("loss", "CenterNetFocalLoss(alpha=2.0,beta=4.0,dice_weight=0.0)", "parent-identical"),
            ("proposal grid", "singleton decode: 0.10 / 0.20 / 5 / 0.30", "grid disabled"),
            ("population", "canonical 770 images / 1161 components", "one orphan quarantined"),
            ("selection", "(val_localization_recall, -val_loss)", "two-term tuple"),
        ], columns=["item", "final binding", "status"]))
        """
    ),
    md("## 5. Dry-run, backward compatibility, and final checklist"),
    code(
        """
        dry = binding["dry_run_result"]
        display(pd.DataFrame([
            ("training steps executed", dry["training_steps_executed"]),
            ("config resolves", dry["config_resolves"]),
            ("singleton decode", dry["proposal_configurations_evaluated_per_epoch"]),
            ("selection tuple", dry["checkpoint_selection"]),
            ("loss", dry["loss"]),
            ("optimizer", dry["optimizer"]),
            ("scheduler", dry["scheduler"]),
            ("model param count", dry["model_param_count"]),
            ("manifests resolved", dry["manifests_resolved"]),
        ], columns=["dry-run item", "value"]))
        display(pd.DataFrame([
            (item["id"], item["status"], item["item"])
            for item in checklist["checklist"] if item["id"] in {"C12", "C13", "C14", "C15"}
        ], columns=["check", "status", "definition"]))
        print("Backward compatibility:", correction["backward_compatibility_and_h3_branch_tests"]["result"])
        """
    ),
    md("## 6. Complete implementation and manifest provenance"),
    code(
        """
        impl = binding["implementation_sha256"]
        impl_table = pd.DataFrame([{"artifact": k, "SHA-256": v, "role": "implementation binding"} for k, v in impl.items()])
        display(impl_table)
        manifest_table = pd.DataFrame([{"artifact": k, "SHA-256": v, "role": "manifest binding"} for k, v in binding["manifest_bindings"].items()])
        display(manifest_table)
        frozen_table = pd.DataFrame([
            {"artifact": v["path"], "SHA-256": v["sha256"], "role": v["role"]}
            for v in binding["frozen_checkpoint_bindings"].values() if isinstance(v, dict) and "path" in v
        ])
        display(frozen_table)
        assert binding["authoritative_a_ref"] == 13.0
        assert dry["training_steps_executed"] == 0
        assert checklist["current_status"] == "H3_FINAL_PRETRAINING_BINDING_COMPLETE__AWAITING_TRAINING_AUTHORIZATION"
        print("Phase 15: NOT_STARTED_AND_NOT_AUTHORIZED; TEST: CLOSED")
        """
    ),
]

scaffold_cells = [
    md(
        """
        # 04 — H3 Training

        ## STATUS

        **H3 TRAINING CURRENTLY IN PROGRESS — FINAL CLOSURE PENDING**

        This is a pending scaffold only. It does not fabricate training results, poll or
        interfere with the active process, restart training, run evaluation, or access TEST.
        Once authoritative closure exists, append the complete epoch history, curves,
        selection replay, checkpoint provenance, and runtime population verification here.
        """
    ),
    code(DISCOVERY),
    code(
        """
        import os
        experiment = ROOT / "experiments" / "h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3"
        launch = load_json("reports/audits/h3_training_launch_binding.json")
        print("Experiment:", launch["experiment_id"])
        print("Launch status:", launch["status"])
        print("Current artifacts:", sorted(p.name for p in experiment.glob("*")) if experiment.exists() else "experiment directory unavailable")
        print("Final closure: NOT AVAILABLE")
        print("No training or inference was started by this scaffold.")
        """
    ),
]


def write(name: str, cells: list[dict]) -> None:
    (OUT / name).write_text(json.dumps(notebook(cells), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


write("01_proposal_root_cause_diagnostic.ipynb", root_cause_cells)
write("02_h3_axis_priority_diagnostic.ipynb", axis_cells)
write("03_h3_design_and_pretraining_binding.ipynb", design_cells)
write("04_h3_training.ipynb", scaffold_cells)

master_path = OUT / "post_phase14_h3_proposal_supply_pipeline.ipynb"
master_cells = [
    md(
        """
        # Post-Phase14 / H3 Proposal-Supply Research Pipeline

        Master index for the stepwise research record. This notebook links the completed
        post-Phase14 causal/design steps and clearly marks pending future H3 steps. It does not
        duplicate large result tables, train models, run inference, evaluate H3, access TEST, or
        start Phase 15.
        """
    ),
    code(DISCOVERY),
    code(
        """
        import hashlib
        entries = [
            ("01", "01_proposal_root_cause_diagnostic.ipynb", "proposal/localizer root-cause diagnostic", "COMPLETE", "F_MIXED_BOTTLENECK"),
            ("02", "02_h3_axis_priority_diagnostic.ipynb", "A-only vs C-only causal priority", "COMPLETE", "H3_DESIGN_ELIGIBLE__AXIS_PROPOSAL_SUPPLY_RECALL"),
            ("03", "03_h3_design_and_pretraining_binding.ipynb", "H3 design, corrections, calibration, binding", "COMPLETE", "H3_FINAL_PRETRAINING_BINDING_COMPLETE__AWAITING_TRAINING_AUTHORIZATION"),
            ("04", "04_h3_training.ipynb", "H3 training record", "IN PROGRESS / CLOSURE PENDING", "H3 TRAINING CURRENTLY IN PROGRESS — FINAL CLOSURE PENDING"),
            ("05", "05_h3_supply_axis_evaluation.ipynb", "H3 supply-axis evaluation", "DEFERRED", "NOT AUTHORIZED / NO CLOSURE"),
            ("06", "06_h3_adjudication.ipynb", "Formal H3 adjudication", "DEFERRED", "NOT AUTHORIZED / NO RESULTS"),
        ]
        index = pd.DataFrame(entries, columns=["step", "notebook", "purpose", "status", "scientific state"])
        index["notebook SHA-256"] = [
            hashlib.sha256((ROOT / "notebooks/phasewise/post_phase14_h3_proposal_supply" / name).read_bytes()).hexdigest()
            if (ROOT / "notebooks/phasewise/post_phase14_h3_proposal_supply" / name).exists() else "PENDING"
            for _, name, *_ in entries
        ]
        display(index)
        print("Phase 14 is separate and complete; Phase 15 remains NOT_STARTED_AND_NOT_AUTHORIZED; TEST is CLOSED.")
        """
    ),
    md(
        """
        ## Authoritative chain

        01 reads `phase14_diag_root_cause.json` and saved diagnostic tables.  
        02 reads `post_phase14_h3_axis_priority_results.json` and saved A/C tables.  
        03 reads the H3 design/correction/final-binding artifacts and calibration tables.  
        04 is a pending scaffold because H3 training has artifacts but no final closure.  
        05 and 06 remain intentionally deferred until authorization and authoritative results.

        H3 is post-Phase14 work. It is not Phase 15 and does not authorize Phase 15.
        """
    ),
]
write("post_phase14_h3_proposal_supply_pipeline.ipynb", master_cells)

readme = """# Post-Phase14 / H3 Proposal-Supply Notebook Set

This folder is the stepwise research record for the post-Phase14 proposal-supply branch.
It is separate from the Phase-14 Regional Refiner notebook because it documents causal
decomposition, axis prioritization, H3 design, pre-execution corrections, calibration,
and H3 training boundaries after Phase-14 closure.

It is not Phase 15. Phase 15 remains `NOT_STARTED_AND_NOT_AUTHORIZED`. TEST and external
TEST remain `CLOSED`.

## Notebook index

| Step | Notebook | Purpose | Status | Executed | Terminal state |
|---|---|---|---|---|---|
| 01 | `01_proposal_root_cause_diagnostic.ipynb` | Proposal/localizer root-cause decomposition | Complete | Yes | `F_MIXED_BOTTLENECK` |
| 02 | `02_h3_axis_priority_diagnostic.ipynb` | A-only vs C-only causal priority | Complete | Yes | `H3_DESIGN_ELIGIBLE__AXIS_PROPOSAL_SUPPLY_RECALL` |
| 03 | `03_h3_design_and_pretraining_binding.ipynb` | H3 design, correction, calibration, binding | Complete | Yes | `H3_FINAL_PRETRAINING_BINDING_COMPLETE__AWAITING_TRAINING_AUTHORIZATION` |
| 04 | `04_h3_training.ipynb` | H3 training record | Scaffold | Yes, scaffold only | `H3 TRAINING CURRENTLY IN PROGRESS — FINAL CLOSURE PENDING` |
| 05 | `05_h3_supply_axis_evaluation.ipynb` | Authorized H3 supply evaluation | Deferred | No | No authoritative evaluation |
| 06 | `06_h3_adjudication.ipynb` | Formal H3 adjudication | Deferred | No | No authorized adjudication |

Notebook SHA-256 values are recorded in the executed master index.

## Authoritative artifacts

- `reports/audits/phase14_diag_root_cause.json`
- `reports/audits/post_phase14_h3_axis_priority_results.json`
- `reports/audits/h3_proposal_supply_design_protocol.json`
- `reports/audits/h3_proposal_supply_design_correction.json`
- `reports/audits/h3_proposal_supply_final_pretraining_binding_v2.json`
- `reports/audits/h3_proposal_supply_pre_execution_checklist.json`
- `reports/audits/h3_training_launch_binding.json`
- `reports/tables/phase15_h3_axis_priority_component_level.csv`
- `reports/tables/phase15_h3_axis_priority_image_summary.csv`
- `reports/tables/phase15_h3_axis_priority_aonly_injected.csv`
- `reports/tables/phase15_h3_axis_priority_ac_component_level.csv`
- `reports/tables/h3_v2_area_distribution.json`
- `reports/tables/h3_v2_component_area_audit.csv`

## Training boundary

Existing H3 experiment artifacts indicate training is in progress, but no final H3 training
closure or authorized supply-axis evaluation/adjudication exists. Notebook 04 therefore remains
a non-fabricating scaffold. It must be updated additively after authoritative closure; notebooks
05 and 06 must remain deferred until their respective authorization gates pass.

No notebook in this synchronization started training, ran inference, accessed TEST, or started
Phase 15.
"""
(OUT / "README.md").write_text(readme, encoding="utf-8")
print(OUT)
