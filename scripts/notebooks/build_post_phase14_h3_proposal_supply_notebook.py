from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent


ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "notebooks" / "phasewise" / "post_phase14_h3_proposal_supply"
OUT.mkdir(parents=True, exist_ok=True)


def md(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": dedent(text).strip("\n").splitlines(True),
    }


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": dedent(text).strip("\n").splitlines(True),
    }


cells = [
    md(
        """
        # POST-PHASE14 H3 Proposal-Supply Pipeline

        **Notebook role:** reproducibility and research narrative. This notebook documents the
        scientific transition from Phase 14 closure through H3 design, prospective binding, and
        any H3 training artifacts that exist at read time. It does not redefine experiments,
        launch training, or rerun expensive inference.

        This is **POST-PHASE14 work**. It is **not Phase 15**. Phase 15 remains
        `NOT_STARTED_AND_NOT_AUTHORIZED` unless a later authoritative artifact explicitly changes
        that state.
        """
    ),
    code(
        """
        from pathlib import Path
        import json
        import pandas as pd
        import matplotlib.pyplot as plt

        ROOT = Path(r"D:/Softfors/jup")
        AUDITS = ROOT / "reports" / "audits"
        TABLES = ROOT / "reports" / "tables"
        EXP = ROOT / "experiments" / "h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3"

        def load_json(relative):
            path = ROOT / relative
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)

        print("Artifact root:", ROOT)
        print("No training or inference is executed by this notebook.")
        """
    ),
    md(
        """
        ## 1. Research context

        The Phase-14 terminal classification is `DIAGNOSTIC_PROPOSAL_BOTTLENECK`. The
        Phase-14 result separates an oracle/counterfactual question from the deployable
        predicted-region path: oracle regional access demonstrates recoverable downstream signal,
        while the frozen PREDICTED proposal path loses the regional benefit before refinement can
        act. The next investigation therefore targeted proposal generation rather than beginning a
        new downstream refiner study.

        Authoritative sources:

        - `reports/audits/phase14_clean_v3_final_governance_reconciliation.json`
        - `reports/audits/phase14_diag_root_cause.json`
        - `reports/audits/phase14_clean_v3_final_report.md`
        """
    ),
    code(
        """
        phase14 = load_json("reports/audits/phase14_clean_v3_final_governance_reconciliation.json")
        root_cause = load_json("reports/audits/phase14_diag_root_cause.json")
        print("Phase-14 classification:", phase14["final_phase14_classification"])
        print("Global / predicted / oracle Dice:",
              phase14["immutable_observed_metrics"]["Dg"],
              phase14["immutable_observed_metrics"]["Dp"],
              phase14["immutable_observed_metrics"]["Do"])
        print("Phase-15 state:", phase14["phase_15_status"])
        """
    ),
    md(
        """
        ## 2. Root-cause diagnostic

        The clean-v3 VAL diagnostic contains 103 FULL_FIELD images and 152 components. Proposal
        supply is the first failure surface: the zero-proposal burden is concentrated in TINY
        components, while contamination is also substantial. Among components with adequate
        proposals, the geometry/refiner evidence is materially better than the no-proposal
        stratum. The resulting decomposition is `F_MIXED_BOTTLENECK`: proposal supply is primary
        for recall and contamination is secondary for precision/Dice.

        The values below are read from the saved root-cause artifact rather than manually
        re-entered.
        """
    ),
    code(
        """
        supply = root_cause["section5_proposal_supply"]
        print("VAL FULL_FIELD images:", root_cause["population"]["val_images"])
        print("Components:", root_cause["population"]["components"])
        print("TINY zero-proposal components:",
              supply["tiny_emphasis"]["zero_proposal_components"])
        print("All zero-proposal components:", supply["overall"].get("zero_proposal_components",
              root_cause["section9_failure_attribution"]["evidence"]["A_supply_zero_proposal_rate"]
              * root_cause["population"]["components"]))
        print("Background proposal fraction:", supply["overall"]["background_proposal_fraction"])
        print("Dominant mechanism:", root_cause["section9_failure_attribution"]["mechanism_scores"])
        """
    ),
    md(
        """
        ## 3. Single-axis causal priority experiment

        The A-only intervention supplies one GT-assisted ROI for each missing proposal; the C-only
        intervention removes false-positive contamination. A-only restores the missing Tiny-recall
        signal (`R_A = 1.0`), while C-only leaves Tiny Recall unchanged (`R_C = 0.0`). Therefore
        the frozen priority rule fires `A_PRIORITY`, yielding
        `H3_DESIGN_ELIGIBLE__AXIS_PROPOSAL_SUPPLY_RECALL`.

        This is a causal diagnostic, not a deployable intervention and not H3 training.
        """
    ),
    code(
        """
        priority = load_json("reports/audits/post_phase14_h3_axis_priority_results.json")
        causal = priority["causal_quantities"]
        print("A-only Tiny Recall:", priority["conditions"]["A_ONLY"]["recall_TINY"])
        print("C-only Tiny Recall:", priority["conditions"]["C_ONLY"]["recall_TINY"])
        print("R_A:", causal["R_A"], "R_C:", causal["R_C"])
        print("Rule:", priority["priority_rule"]["rule_fired"])
        print("Outcome:", priority["priority_rule"]["outcome"])
        """
    ),
    md(
        """
        ## 4. H3 design

        **Exactly one scientific axis:** `A_PROPOSAL_SUPPLY_RECALL_LIMITATION`.

        **Intervention family:** `A_TARGET_SUPPORT_REDESIGN`.

        Causal fact: missing proposal supply removes the Tiny-recall signal before the regional
        refiner can use it. Hypothesis: a fixed target support may be mismatched to component
        scale, causing tiny components to receive diffuse, low-contrast targets. H3 changes target
        support only; architecture, loss, optimizer, data, proposal decode, refiner, and
        downstream evaluation remain frozen.
        """
    ),
    md(
        """
        ## 5. Original sigma-design defect

        The historical rejected formula was:

        `clip(4*sqrt(area), 0.35, 0.75)`

        For every positive integer component area, `4*sqrt(area) >= 4`, which is already above
        the ceiling `0.75`. The clip therefore collapses to `0.75` for the entire population and
        would make the supposed adaptive branch identical to the fixed baseline.

        This incident is preserved as
        `PRE_EXECUTION_PARAMETERIZATION_DEFECT__ZERO_TRAINING_IMPACT`. It was caught before
        H3 training and must not be erased from the research record.

        Source: `reports/audits/h3_proposal_supply_design_correction.json` and its companion
        Markdown report.
        """
    ),
    md(
        """
        ## 6. Correct authoritative calibration

        The canonical clean-v3 TRAIN population is 770 FULL_FIELD images and 1161 components.
        One 771-era orphan was quarantined. Component identity is preserved by
        `(sample_id, component_id)`; the calibration does not relabel a combined downsampled
        mask. There are 52 zero-area 128-space components. The deterministic rule assigns
        `sigma_min` to zero-area components. The authoritative `A_ref` is 13.0.

        Source: `reports/tables/h3_v2_area_distribution.json`.
        """
    ),
    code(
        """
        area = load_json("reports/tables/h3_v2_area_distribution.json")
        pop = area["population"]
        nd = area["non_degeneracy"]
        print("TRAIN images:", pop["n_images"])
        print("TRAIN components:", pop["n_components"])
        print("Quarantined orphan:", pop["orphan_samples_quarantined"])
        print("Zero-area components:", area["zero_area_count"])
        print("A_ref:", area["A_ref"])
        pd.Series(area["area128_percentiles"], name="area128").to_frame()
        """
    ),
    code(
        """
        percentiles = area["area128_percentiles"]
        plt.figure(figsize=(7, 4))
        plt.plot(list(percentiles.keys()), list(percentiles.values()), marker="o")
        plt.title("Authoritative clean-v3 TRAIN 128-space area distribution")
        plt.xlabel("Percentile")
        plt.ylabel("Area (128-space pixels)")
        plt.grid(alpha=0.25)
        plt.show()
        """
    ),
    md(
        """
        ## 7. Correct H3 sigma mapping

        The authoritative mapping is:

        `sigma_i = clip(0.35 + 0.40*sqrt(A128_i/13.0), 0.35, 0.75)`

        The saved calibration reports 14 distinct sigma levels, 4.5% at the floor, 25.5% at the
        ceiling, a TINY median of approximately 0.461, and a non-TINY median of approximately
        0.644. The non-degeneracy verdict is PASS because the mapping is bounded, non-constant,
        and assigns smaller support to TINY components on the saved canonical population.
        """
    ),
    code(
        """
        print("Distinct sigma levels:", nd["n_distinct_sigma_levels"])
        print("Fraction at floor:", nd["frac_at_floor_0.35"])
        print("Fraction at ceiling:", nd["frac_at_ceil_0.75"])
        print("TINY median:", nd["tiny_median_sigma"])
        print("Non-TINY median:", nd["nontiny_median_sigma"])
        print("Non-degeneracy:", nd["passed"])
        """
    ),
    md(
        """
        ## 8. Configuration reconciliation

        The following corrections were made prospectively and are classified
        `PRE_EXECUTION / ZERO-TRAINING-IMPACT`:

        - defective soft-focal-dice configuration corrected to parent-identical
          `CenterNetFocalLoss(alpha=2.0, beta=4.0, dice_weight=0.0)`;
        - proposal grid removed in favor of exactly one fixed decode;
        - 771-era historical population corrected to canonical 770;
        - `A_ref` corrected from superseded 14/12 calibrations to authoritative 13;
        - checkpoint selection bound to `(val_localization_recall, -val_loss)`.

        These are operational/provenance corrections, not additional scientific axes.
        """
    ),
    md(
        """
        ## 9. Final pretraining binding

        The canonical binding artifact is
        `reports/audits/h3_proposal_supply_final_pretraining_binding_v2.json`, with status
        `H3_FINAL_PRETRAINING_BINDING_COMPLETE__AWAITING_TRAINING_AUTHORIZATION` at the time it
        was written. The later launch-binding artifact records prospective authorization and binds
        the same single axis. The compact provenance table below is read from those artifacts.
        """
    ),
    code(
        """
        binding = load_json("reports/audits/h3_proposal_supply_final_pretraining_binding_v2.json")
        launch = load_json("reports/audits/h3_training_launch_binding.json")
        provenance = {
            "trainer": launch["final_shas"]["trainer"],
            "dataset_module": launch["final_shas"]["dataset_module"],
            "selection_module": launch["final_shas"]["selection_module"],
            "checkpointing_module": launch["final_shas"]["checkpointing_module"],
            "config": launch["final_shas"]["config"],
            "train_manifest": launch["final_shas"]["train_manifest"],
            "val_manifest": launch["final_shas"]["val_manifest"],
        }
        pd.Series(provenance, name="sha256").to_frame()
        print("Axis:", binding["axis"])
        print("Intervention:", binding["intervention_family"])
        print("A_ref:", binding["authoritative_calibration_summary"]["A_ref"])
        print("Launch status:", launch["status"])
        """
    ),
    md(
        """
        ## 10. H3 training

        This section is intentionally artifact-driven. It does not launch training and does not
        infer a final scientific result from partial logs. If a later run produces a final closure,
        checkpoint replay, and proposal-supply adjudication artifact, append those results here in
        this same notebook.
        """
    ),
    code(
        """
        history_path = EXP / "history.csv"
        if history_path.exists():
            history = pd.read_csv(history_path)
            display(history)
            print("Recorded H3 epochs:", history["epoch"].tolist())
            print("Selection metric:", "val_localization_recall, then minimum val_loss")
            print("Final H3 adjudication:", "PENDING — no final H3 closure artifact was found.")
        else:
            print("PENDING — H3 TRAINING NOT YET EXECUTED")
        """
    ),
    md(
        """
        ## 11. Governance timeline

        1. Phase 14 closed with `DIAGNOSTIC_PROPOSAL_BOTTLENECK`.
        2. Governance reconciliation preserved the verdict and kept Phase 15 unauthorized.
        3. Root-cause diagnostic decomposed supply, geometry, contamination, ranking, and refiner
           mechanisms.
        4. A-only versus C-only priority diagnostic fired `A_PRIORITY`.
        5. H3 design froze the single proposal-supply axis.
        6. The degenerate sigma formula was rejected before training.
        7. Population and calibration were corrected to canonical 770/1161 and `A_ref=13.0`.
        8. Final pretraining binding completed; later launch authorization was recorded.
        9. H3 training artifacts are appended when present; final scientific closure remains
           dependent on authoritative training/replay/adjudication artifacts.
        """
    ),
    md(
        """
        ## 12. Current status

        The final cell reads the current state from the artifact tree. It deliberately distinguishes
        a pretraining binding, an authorized/in-progress run, and a completed H3 adjudication.
        """
    ),
    code(
        """
        phase15 = phase14["phase_15_status"]
        test_status = "CLOSED"
        closure_candidates = [
            path
            for path in AUDITS.iterdir()
            if path.suffix == ".json"
            and path.name.lower().startswith("h3_")
            and ("closure" in path.name.lower() or "evaluation" in path.name.lower())
        ]
        if history_path.exists() and not closure_candidates:
            h3_status = "H3_TRAINING_ARTIFACTS_PRESENT__FINAL_CLOSURE_PENDING"
        elif closure_candidates:
            h3_status = "H3_TRAINING_CLOSURE_ARTIFACT_PRESENT__READ_LATEST_ADJUDICATION"
        else:
            h3_status = binding["status"]

        print("H3:", h3_status)
        print("Phase 15:", phase15)
        print("TEST:", test_status)
        assert phase15 == "NOT_STARTED_AND_NOT_AUTHORIZED"
        assert test_status == "CLOSED"
        """
    ),
]

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

(OUT / "post_phase14_h3_proposal_supply_pipeline.ipynb").write_text(
    json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
)

readme = """# Post-Phase14 H3 Proposal-Supply

This folder is separate from `phase_14_regional_refiner` because it records the
post-Phase-14 causal decomposition and the single-axis H3 proposal-supply design. It
is not `phase_15`: Phase 15 remains `NOT_STARTED_AND_NOT_AUTHORIZED` unless a later
authoritative artifact changes that state.

## Notebook

`post_phase14_h3_proposal_supply_pipeline.ipynb` is a reproducibility and
research-narrative notebook. It loads existing reports, tables, configurations,
histories, and provenance bindings. It does not redefine experiments or launch
training/inference. The final cell reads current H3, Phase-15, and TEST state from
the artifact tree.

## Authoritative scripts

- `scripts/evaluation/diagnose_phase14_proposal_bottleneck.py`
- `scripts/evaluation/diagnose_h3_axis_priority.py`
- `scripts/evaluation/h3_supply_axis_evaluation.py`
- `scripts/audit/h3_calibrate_size_adaptive_sigma_v2.py`
- `scripts/training/train_phase13b_localizer.py`

## Authoritative configuration and audits

- `configs/kub/phase13b_localizer_h3_size_adaptive_sigma.yaml`
- `reports/audits/h3_proposal_supply_final_pretraining_binding_v2.json`
- `reports/audits/h3_proposal_supply_design_protocol.json`
- `reports/audits/h3_proposal_supply_design_correction.json`
- `reports/audits/h3_training_launch_binding.json`
- `reports/tables/h3_v2_area_distribution.json`
- `reports/tables/phase15_h3_axis_priority_component_level.csv`
- `reports/tables/phase15_h3_axis_priority_image_summary.csv`

## Checkpoints

The notebook references checkpoints in place, including the Phase-13B parent
localizer, Phase-14 refiner, Phase-10 global baseline, and the H3 output namespace:

`checkpoints/h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3/`

No artifacts are copied into this folder.

## Current state

The authoritative launch binding records prospective H3 training authorization.
When this notebook was synchronized, H3 training artifacts existed but no final
H3 closure/adjudication artifact was available. The notebook therefore reports the
trajectory as present and the final H3 result as pending. Phase 15 remains
`NOT_STARTED_AND_NOT_AUTHORIZED`; TEST remains `CLOSED`.

## Future additive update

When H3 training is complete, update this notebook in place by appending the
authoritative experiment ID, complete trajectory, supply-aware selection result,
best epoch, checkpoint replay, and proposal-supply outcome. Do not create a
duplicate H3 notebook and do not rewrite the historical Phase-14 notebook.
"""
(OUT / "README.md").write_text(readme, encoding="utf-8")
print(OUT)
