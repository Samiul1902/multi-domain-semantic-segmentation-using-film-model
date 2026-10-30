from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "notebooks" / "phasewise" / "phase_14_regional_refiner"
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


cells = [
    md(
        """
        # Phase 14 Regional Refiner: Complete Executed Research Record

        **Scope:** artifact-driven reconstruction of the completed Phase-14 clean-v3 Regional
        Refiner Diagnostic. This notebook loads saved history, tables, checkpoints, reports, and
        governance artifacts. It performs deterministic display arithmetic and plotting only.

        **Safety boundary:** no optimizer steps, model training, forward inference, checkpoint
        mutation, TEST reads, external TEST reads, hyperparameter search, Phase-15 work, or H3
        work are performed here.

        Terminal state:

        - `PHASE14_CLEAN_V3_COMPLETE__DIAGNOSTIC_PROPOSAL_BOTTLENECK`
        - Phase 15: `NOT_STARTED_AND_NOT_AUTHORIZED`
        - TEST: `CLOSED`
        """
    ),
    code(
        """
        from pathlib import Path
        import hashlib
        import json
        import pandas as pd
        import matplotlib.pyplot as plt
        from IPython.display import display, Image

        ROOT = Path(r"D:/Softfors/jup")
        AUDITS = ROOT / "reports" / "audits"
        TABLES = ROOT / "reports" / "tables"
        EXPERIMENT = ROOT / "experiments" / "phase14_kub_refiner_unet_a3_256_seed42_clean_v3"

        def load_json(relative):
            with (ROOT / relative).open("r", encoding="utf-8") as handle:
                return json.load(handle)

        def read_csv(relative):
            return pd.read_csv(ROOT / relative)

        training = load_json("reports/audits/phase14_clean_v3_final_training_closure.json")
        replay = load_json("reports/audits/phase14_clean_v3_checkpoint_selection_replay.json")
        resume = load_json("reports/audits/phase14_resume_equivalence_verification.json")
        freeze = load_json("reports/audits/phase14_clean_v3_freeze_manifest.json")
        population = load_json("reports/audits/phase14_clean_v3_population_freeze.json")
        reference = load_json("reports/audits/phase14_clean_v3_global_reference_freeze.json")
        diagnostic = load_json("reports/audits/phase14_clean_v3_diagnostic_evaluation.json")
        adjudication = load_json("reports/audits/phase14_clean_v3_formal_adjudication.json")
        reconciliation = load_json("reports/audits/phase14_clean_v3_final_governance_reconciliation.json")
        history_path = EXPERIMENT / "history.csv"
        history_raw = pd.read_csv(history_path)

        print("Repository root:", ROOT)
        print("Experiment:", training["experiment_id"])
        print("Saved history:", history_path)
        print("No training or inference is executed by this notebook.")
        """
    ),
    md(
        """
        ## 1. Scientific question and frozen protocol

        Phase 14 asked whether a regional refiner has useful potential under ideal Oracle ROI
        access, and how much of that potential survives when the same refiner receives the frozen
        predicted proposal stream. The three modes are diagnostic contrasts, not separately tuned
        systems: `GLOBAL_ONLY`, `ORACLE_REGIONAL`, and `PREDICTED_REGIONAL`.

        The clean-v3 protocol froze the KUB TRAIN/VAL populations, a 256x256 U-Net refiner,
        BCEDiceLoss, AdamW, CosineAnnealingLR, seed 42, AMP, and best validation crop Dice
        checkpoint selection. The proposal policy was threshold `0.1`, proposal margin `0.2`,
        top-k `5`, and NMS IoU `0.3`. ROI margin roles are distinct: refiner TRAIN/VAL crop
        construction `0.25`, Oracle downstream `0.20`, and predicted proposal `0.20`.

        H3 was not Phase 14 and was not started during this phase.
        """
    ),
    code(
        """
        cfg = training["configuration_as_executed"]
        margin_binding = training["role_margin_binding_as_executed"]
        config_table = pd.DataFrame([
            ("experiment_id", training["experiment_id"]),
            ("architecture", cfg["model"]),
            ("trainable_parameters", cfg["trainable_parameters"]),
            ("input_channels", 1), ("output_channels", 1), ("base_channels", 32),
            ("crop_resolution", "256 x 256"), ("loss", cfg["loss"]),
            ("optimizer", cfg["optimizer"]), ("learning_rate", "1e-4"),
            ("weight_decay", "1e-4"), ("scheduler", cfg["scheduler"]), ("T_max", 100),
            ("batch_size", cfg["batch_size"]), ("AMP", cfg["amp"]), ("seed", cfg["seed"]),
            ("max_epochs", cfg["max_epochs"]), ("patience", cfg["early_stopping"]["patience"]),
            ("checkpoint_metric", cfg["checkpoint_rule"]),
            ("TRAIN margin", margin_binding["ORACLE_DERIVED_REFINER_TRAIN_MARGIN"]),
            ("VAL margin", margin_binding["ORACLE_DERIVED_REFINER_VAL_MARGIN"]),
            ("Oracle downstream margin", margin_binding["ORACLE_DOWNSTREAM_MARGIN"]),
            ("Predicted proposal margin", margin_binding["PREDICTED_PROPOSAL_MARGIN"]),
            ("augmentation", "H/V flip; rotation +/-45 degrees; brightness/contrast +/-0.2"),
            ("frozen localizer checkpoint", diagnostic["checkpoints"]["stage4d_localizer"]["path"]),
            ("frozen global checkpoint", diagnostic["checkpoints"]["global_unetpp"]["path"]),
            ("proposal threshold", 0.1), ("proposal margin", 0.2), ("top_k", 5),
            ("NMS IoU", 0.3), ("fusion rule", "MAX probability replacement in proposal union"),
        ], columns=["parameter", "authoritative value"])
        display(config_table)
        """
    ),
    md(
        """
        ## 2. Dataset and population summary

        Current clean-v3 Phase-14 training is 770 TRAIN images and 1161 components. The
        diagnostic VAL population is 103 FULL_FIELD images and 152 components. Historical v2
        diagnostic population, 106 images and 156 components, is shown only as historical
        context. Crop accounting is preserved from the saved artifacts; discrepancies between
        independently saved crop summaries are displayed rather than explained without evidence.
        """
    ),
    code(
        """
        inventory = read_csv("reports/tables/phase14_part1_training_crop_inventory.csv")
        train_counts = freeze["datasets"]["train_population"]
        val_counts = freeze["datasets"]["val_population"]
        crop_row = inventory.iloc[0].to_dict()
        closure_crops = cfg.get("train_crops_constructed")
        population_table = pd.DataFrame([
            ("Phase-14 TRAIN clean-v3", train_counts["images"], train_counts["components"], None, None, None, closure_crops, None, "current authoritative population"),
            ("Phase-14 VAL clean-v3", val_counts["images"], val_counts["components"], None, None, None, None, 152, "current diagnostic population"),
            ("Crop inventory: TRAIN", None, None, crop_row["base_positives"], crop_row["perturbed_positives"], crop_row["background_negatives"], crop_row["total"], None, "saved crop inventory"),
            ("Historical v2 diagnostic", 106, 156, None, None, None, None, None, "historical only; not current clean-v3"),
        ], columns=["population", "images", "components", "base_positive_crops", "perturbation_crops", "background_crops", "total_actual_crops", "validation_crops", "status"])
        display(population_table)
        print("Closure train_crops_constructed:", closure_crops)
        print("Inventory total:", crop_row["total"])
        print("No retry-failure explanation is inferred from this artifact difference.")
        """
    ),
    md(
        """
        ## 3. Complete 71-epoch training history

        The full saved trajectory is displayed below, not reduced to head/tail rows. Original
        recorded columns are retained. Additional columns are display-only derivations. Timing
        values remain unchanged despite the documented host-clock-skew limitation.
        """
    ),
    code(
        """
        history = history_raw.copy()
        history["best_val_dice_so_far"] = history["val_crop_dice"].cummax()
        history["val_dice_change"] = history["val_crop_dice"].diff()
        history["epochs_since_best"] = history["epoch"] - history["best_epoch_so_far"]
        history["trainer_revision"] = history["epoch"].apply(lambda e: 3 if e <= 10 else 4)
        history["trainer_sha"] = history["trainer_revision"].map({
            3: training["checkpoint_lineage"]["segments"][0]["trainer_sha"],
            4: training["checkpoint_lineage"]["segments"][1]["trainer_sha"],
        })
        display(history)
        print("Complete history rows:", len(history))
        print("Recorded columns:", list(history_raw.columns))
        print("Timing caveat:", training["operational_history"]["host_clock_skew_impact"])
        """
    ),
    md("## 4. Training summary and selected checkpoint"),
    code(
        """
        final_row = history.iloc[-1]
        summary_table = pd.DataFrame([
            ("total epochs", training["outcome"]["total_epochs"]),
            ("best epoch", training["outcome"]["best_epoch"]),
            ("best val_crop_dice", training["outcome"]["best_val_crop_dice"]),
            ("final epoch", int(final_row["epoch"])), ("final train loss", final_row["train_loss"]),
            ("final val loss", final_row["val_loss"]), ("final val_crop_dice", final_row["val_crop_dice"]),
            ("initial learning rate", history.iloc[0]["learning_rate"]),
            ("final learning rate", final_row["learning_rate"]),
            ("early-stopping patience", cfg["early_stopping"]["patience"]),
            ("stop reason", training["outcome"]["stop_reason"]),
            ("total train crops", cfg["train_crops_constructed"]),
            ("total validation crops", cfg["val_crops_constructed"]),
            ("trainable parameters", cfg["trainable_parameters"]), ("batch size", cfg["batch_size"]),
            ("seed", cfg["seed"]), ("AMP", cfg["amp"]),
            ("best checkpoint SHA", training["outcome"]["best_checkpoint_sha256"]),
            ("latest checkpoint SHA", training["outcome"]["latest_checkpoint_sha256"]),
            ("history SHA", training["outcome"]["history_sha256"]),
            ("selected checkpoint", "epoch 56 / best.pt"),
        ], columns=["summary item", "value"])
        display(summary_table)
        """
    ),
    md("## 5. Training and validation loss"),
    code(
        """
        fig, ax = plt.subplots(figsize=(10, 5.5))
        ax.plot(history["epoch"], history["train_loss"], label="train_loss", linewidth=2)
        ax.plot(history["epoch"], history["val_loss"], label="val_loss", linewidth=2)
        ax.axvline(56, color="black", linestyle="--", label="selected best epoch 56")
        ax.axvline(71, color="gray", linestyle=":", label="termination epoch 71")
        ax.set(title="Training and Validation Loss vs Epoch", xlabel="Epoch", ylabel="Loss")
        ax.grid(True, alpha=0.3); ax.legend(); plt.show()
        """
    ),
    md("## 6. Validation crop Dice trajectory"),
    code(
        """
        new_best = history[history["is_new_best"]].copy()
        fig, ax = plt.subplots(figsize=(10, 5.5))
        ax.plot(history["epoch"], history["val_crop_dice"], label="raw val_crop_dice", linewidth=2)
        ax.plot(history["epoch"], history["best_val_dice_so_far"], label="best-so-far Dice", linestyle="--", linewidth=2)
        ax.scatter(new_best["epoch"], new_best["val_crop_dice"], color="tab:orange", label="historical new best", zorder=3)
        for _, row in new_best.iterrows():
            ax.annotate(str(int(row["epoch"])), (row["epoch"], row["val_crop_dice"]), xytext=(0, 7), textcoords="offset points", ha="center", fontsize=8)
        ax.axvline(56, color="black", linestyle="--", label="selected epoch 56")
        ax.scatter([56], [training["outcome"]["best_val_crop_dice"]], color="red", zorder=4)
        ax.set(title="Validation Crop Dice vs Epoch", xlabel="Epoch", ylabel="val_crop_dice")
        ax.grid(True, alpha=0.3); ax.legend(); plt.show()
        display(new_best[["epoch", "val_crop_dice", "train_loss", "val_loss", "learning_rate"]])
        """
    ),
    md("## 7. Learning-rate and early-stopping trajectories"),
    code(
        """
        fig, ax = plt.subplots(figsize=(10, 5.5))
        ax.plot(history["epoch"], history["learning_rate"], linewidth=2, color="tab:green")
        ax.axvline(56, color="black", linestyle="--", label="selected epoch 56")
        ax.set(title="Recorded Learning Rate vs Epoch", xlabel="Epoch", ylabel="learning_rate")
        ax.grid(True, alpha=0.3); ax.legend(); plt.show()

        fig, ax = plt.subplots(figsize=(10, 5.5))
        ax.plot(history["epoch"], history["bad_epochs"], label="bad_epochs", linewidth=2)
        ax.step(history["epoch"], history["best_epoch_so_far"], where="post", label="best_epoch_so_far", alpha=0.8)
        ax.scatter(history.loc[history["is_new_best"], "epoch"], history.loc[history["is_new_best"], "bad_epochs"], label="is_new_best", color="tab:orange", zorder=3)
        ax.axhline(15, color="red", linestyle=":", label="patience 15")
        ax.set(title="Early-Stopping / Bad-Epoch Counter vs Epoch", xlabel="Epoch", ylabel="counter / epoch index")
        ax.grid(True, alpha=0.3); ax.legend(); plt.show()
        display(new_best[["epoch", "val_crop_dice", "train_loss", "val_loss", "learning_rate"]])
        """
    ),
    md(
        """
        ## 8. Best-checkpoint progression

        The progression is loaded from the closure artifact and cross-checked against history.
        Epoch 56 is selected. The trajectory is not attributed to one trainer SHA.
        """
    ),
    code(
        """
        progression = pd.DataFrame(training["checkpoint_lineage"]["best_progression"])
        progression["absolute_gain_from_previous_best"] = progression["val_crop_dice"].diff()
        progression["cumulative_gain_from_first_best"] = progression["val_crop_dice"] - progression["val_crop_dice"].iloc[0]
        progression["status"] = progression["epoch"].apply(lambda e: "SELECTED" if e == 56 else "historical best")
        progression["trainer_revision"] = progression["epoch"].apply(lambda e: 3 if e <= 10 else 4)
        progression["trainer_sha"] = progression["trainer_revision"].map({3: training["checkpoint_lineage"]["segments"][0]["trainer_sha"], 4: training["checkpoint_lineage"]["segments"][1]["trainer_sha"]})
        display(progression)
        fig, ax = plt.subplots(figsize=(10, 5.5))
        ax.plot(progression["epoch"], progression["val_crop_dice"], marker="o", linewidth=2)
        selected = progression[progression["status"] == "SELECTED"]
        ax.scatter(selected["epoch"], selected["val_crop_dice"], color="red", s=80, zorder=3, label="SELECTED epoch 56")
        ax.set(title="Best-Checkpoint Progression", xlabel="Best epoch", ylabel="val_crop_dice")
        ax.grid(True, alpha=0.3); ax.legend(); plt.show()
        """
    ),
    md(
        """
        ## 9. Trainer revision, resume timeline, and bit-exact equivalence

        Epochs 1-10 were produced by trainer revision 3; epochs 11-71 were produced by revision
        4 after the RNG-device-coercion fix. The selected epoch-56 checkpoint was produced by
        revision 4 after all code fixes. The failed resume executed zero epochs.
        """
    ),
    code(
        """
        segments = pd.DataFrame([
            {"epoch_range": s["epochs"], "trainer_revision": s["trainer_revision"], "trainer_sha": s["trainer_sha"], "resume_relevance": s["note"], "scientific_computation_affected": "NO", "selected_checkpoint_caveat": "NO" if s["trainer_revision"] == 4 else "superseded checkpoint caveat"}
            for s in training["checkpoint_lineage"]["segments"]
        ])
        display(segments)
        fig, ax = plt.subplots(figsize=(10, 2.6))
        ax.barh(["trainer revision 3", "trainer revision 4"], [10, 61], left=[1, 11], color=["tab:orange", "tab:blue"])
        ax.set(title="Multi-SHA Training Lineage", xlabel="Epoch range", xlim=(0, 72))
        ax.grid(True, axis="x", alpha=0.3); plt.show()

        metric_rows = []
        for epoch in resume["metric_comparison"]["common_epochs"]:
            row = resume["metric_comparison"]["per_epoch"][str(epoch)]
            metric_rows.append({
                "epoch": epoch,
                "train_loss_match": row["train_loss"]["equal"],
                "val_loss_match": row["val_loss"]["equal"],
                "val_crop_dice_match": row["val_crop_dice"]["equal"],
                "learning_rate_match": row["learning_rate"]["equal"],
                "best_epoch_so_far_match": row["best_epoch_so_far"]["equal"],
                "bad_epochs_match": row["bad_epochs"]["equal"],
            })
        display(pd.DataFrame(metric_rows))
        print("Resume-equivalence verdict:", resume["classification"])
        """
    ),
    md(
        """
        ## 10. Epoch timing analysis

        Timing is operational metadata only. The saved duration and cumulative values are not
        altered. Host-clock skew affects wall-clock timestamps and the epoch timing field at an
        affected point; no scientific conclusion is drawn from timing.
        """
    ),
    code(
        """
        fig, ax = plt.subplots(figsize=(10, 5.5))
        ax.plot(history["epoch"], history["elapsed_seconds"], linewidth=1.8)
        ax.axvline(56, color="black", linestyle="--", label="selected epoch 56")
        ax.set(title="Epoch Duration vs Epoch", xlabel="Epoch", ylabel="elapsed_seconds")
        ax.grid(True, alpha=0.3); ax.legend(); plt.show()
        timing = history["elapsed_seconds"]
        display(pd.DataFrame([
            ("median epoch duration", timing.median()), ("mean epoch duration", timing.mean()),
            ("minimum epoch duration", timing.min()), ("maximum epoch duration", timing.max()),
            ("timing validity", training["operational_history"]["host_clock_skew_impact"]),
        ], columns=["summary item", "value"]))
        """
    ),
    md("## 11. Complete diagnostic mode table"),
    code(
        """
        mode_df = read_csv("reports/tables/phase14_clean_v3_mode_summary.csv")
        display(mode_df)
        """
    ),
    md("## 12. Diagnostic mode visual comparisons"),
    code(
        """
        for column, title, ylabel in [
            ("mean_dice", "Dice comparison", "Mean Dice"),
            ("tiny_recall90", "Tiny Recall@0.90 comparison", "Tiny Recall@0.90"),
            ("overall_recall90", "Overall Recall@0.90 comparison", "Overall Recall@0.90"),
            ("mean_fp_components_per_image", "False-positive burden comparison", "Mean FP components / image"),
        ]:
            fig, ax = plt.subplots(figsize=(8, 4.8))
            ax.bar(mode_df["mode"], mode_df[column], color=["tab:gray", "tab:green", "tab:red"])
            ax.set(title=title, ylabel=ylabel)
            ax.tick_params(axis="x", rotation=15); ax.grid(True, axis="y", alpha=0.3); plt.show()
        """
    ),
    md("## 13. Diagnostic contrasts and step-wise adjudication"),
    code(
        """
        contrast_definitions = {
            "Tg": ("Global Tiny Recall@0.90", "global baseline Tiny recall"),
            "To": ("Oracle Tiny Recall@0.90", "ideal-ROI Tiny recall"),
            "Tp": ("Predicted Tiny Recall@0.90", "frozen predicted-proposal Tiny recall"),
            "Dg": ("Global FULL_FIELD mean Dice", "global clean-v3 reference"),
            "Do": ("Oracle FULL_FIELD mean Dice", "ideal-ROI refiner Dice"),
            "Dp": ("Predicted FULL_FIELD mean Dice", "predicted-proposal cascade Dice"),
            "G": ("To - Tg", "Oracle refiner gain over global Tiny recall"),
            "R": ("(Tp - Tg) / G", "fraction of Oracle gain retained by predicted proposals"),
        }
        contrast_table = pd.DataFrame([
            {"symbol": s, "definition": contrast_definitions[s][0], "value": diagnostic["diagnostic_contrasts"][s], "interpretation": contrast_definitions[s][1], "gate relevance": "Step 1/2/3"}
            for s in ["Tg", "To", "Tp", "Dg", "Do", "Dp", "G", "R"]
        ])
        display(contrast_table)
        arithmetic = reconciliation["section_D_arithmetic_readjudication"]
        gate_rows = [
            ("Step 1", "G >= 0.05", arithmetic["step_1"]["G"]["value"], arithmetic["step_1"]["G"]["threshold"], arithmetic["step_1"]["G"]["pass"]),
            ("Step 1", "Do >= Dg - 0.02", arithmetic["step_1"]["Do"]["value"], arithmetic["step_1"]["Do"]["threshold"], arithmetic["step_1"]["Do"]["pass"]),
            ("Step 2", "R >= 0.50", arithmetic["step_2"]["R"]["value"], arithmetic["step_2"]["R"]["threshold"], arithmetic["step_2"]["R"]["pass"]),
        ]
        formal = arithmetic["step_3_formal_16_7"]["clauses"]
        gate_rows += [
            ("Step 3", "Tp >= Tg", formal["Tp"]["value"], formal["Tp"]["threshold"], formal["Tp"]["pass"]),
            ("Step 3", "Dp >= Dg - 0.02", formal["Dp"]["value"], formal["Dp"]["threshold"], formal["Dp"]["pass"]),
            ("Step 3", "Hard-Tiny >= 2/16", formal["HardTiny"]["recovered"], "2/16", formal["HardTiny"]["pass"]),
            ("Step 3", "Global-Empty >= 1/7", formal["GlobalEmpty"]["recovered"], "1/7", formal["GlobalEmpty"]["pass"]),
        ]
        display(pd.DataFrame(gate_rows, columns=["step", "gate", "observed", "threshold", "PASS"]))
        print("Final gates: Step 1 PASS; Step 2 FAIL; Step 3 FAIL")
        print("Final classification:", reconciliation["final_phase14_classification"])
        """
    ),
    md(
        """
        ## 14. Special-set provenance

        Formal frozen governance provenance is **Hard-Tiny 4/16** and **Global-Empty 3/7**.
        Later clean-v3 re-derived 15/5 sets are descriptive only and do not replace formal
        adjudication provenance.
        """
    ),
    code(
        """
        display(pd.DataFrame([
            ("FORMAL frozen", "Hard-Tiny", "4/16", "formal gate provenance"),
            ("FORMAL frozen", "Global-Empty", "3/7", "formal gate provenance"),
            ("Descriptive clean-v3 re-derived", "Hard-Tiny", "0/15", "descriptive only"),
            ("Descriptive clean-v3 re-derived", "Global-Empty", "1/5", "descriptive only"),
        ], columns=["provenance family", "set", "reported result", "status"]))
        """
    ),
    md(
        """
        ## 15. Governance incidents and operational record

        The record preserves the invalid pre-freeze implementation binding, RNG-device-coercion
        resume defect, host-clock skew, interruptions, successful resumes, failed resume, and
        multi-SHA lineage. The failed resume executed zero epochs; no data were lost and no
        epochs were recomputed. The selected checkpoint requires no code-only caveat.
        """
    ),
    code(
        """
        display(pd.DataFrame([
            ("Invalid pre-freeze implementation binding", "reports/audits/phase14_clean_v3_invalid_pre_freeze_implementation_binding.json", "historical incident; superseded additively"),
            ("RNG device-coercion resume defect", training["operational_history"]["failed_resume_cause"], "zero epochs executed; no scientific impact"),
            ("Host-clock skew", training["operational_history"]["host_clock_skew_impact"], "operational timing only"),
            ("Operational interruptions", training["operational_history"]["interruptions"], "trajectory preserved"),
            ("Successful resumes", training["operational_history"]["successful_resumes"], "resume evidence retained"),
            ("Failed resumes", training["operational_history"]["failed_resumes"], "failed attempt executed zero epochs"),
            ("Epochs recomputed", training["operational_history"]["epochs_ever_recomputed"], "none"),
            ("Data lost", training["operational_history"]["data_lost"], "none"),
        ], columns=["incident / item", "evidence", "impact"]))
        """
    ),
    md("## 16. Saved qualitative evidence"),
    code(
        """
        qualitative_candidates = [
            ROOT / "reports/qualitative/phase14_part3c/phase14_part3_qualitative_panel.png",
            ROOT / "reports/figures/phase14_part3c/phase14_part3_demo_visualization.png",
        ]
        found = [path for path in qualitative_candidates if path.exists()]
        if found:
            for path in found:
                print("Saved qualitative artifact:", path.relative_to(ROOT))
                display(Image(filename=str(path), width=1000))
        else:
            print("Qualitative prediction examples unavailable from saved Phase-14 artifacts; no new inference performed.")
        """
    ),
    md("## 17. Artifact provenance"),
    code(
        """
        provenance = [
            ("history.csv", "experiments/phase14_kub_refiner_unet_a3_256_seed42_clean_v3/history.csv", "complete 71-epoch trajectory", "authoritative"),
            ("training closure", "reports/audits/phase14_clean_v3_final_training_closure.json", "training and lineage closure", "authoritative"),
            ("experiment closure", "experiments/phase14_kub_refiner_unet_a3_256_seed42_clean_v3/closure.json", "run closure metadata", "authoritative"),
            ("freeze manifest", "reports/audits/phase14_clean_v3_freeze_manifest.json", "frozen protocol/configuration", "authoritative"),
            ("selection replay", "reports/audits/phase14_clean_v3_checkpoint_selection_replay.json", "disk-only 13/13 replay", "authoritative"),
            ("resume equivalence", "reports/audits/phase14_resume_equivalence_verification.json", "bit-exact resume evidence", "authoritative"),
            ("population freeze", "reports/audits/phase14_clean_v3_population_freeze.json", "clean-v3 VAL population", "authoritative"),
            ("global reference freeze", "reports/audits/phase14_clean_v3_global_reference_freeze.json", "Tg/Dg freeze", "authoritative"),
            ("diagnostic evaluation", "reports/audits/phase14_clean_v3_diagnostic_evaluation.json", "three-mode results", "authoritative"),
            ("formal adjudication", "reports/audits/phase14_clean_v3_formal_adjudication.json", "step-wise adjudication", "authoritative"),
            ("governance reconciliation", "reports/audits/phase14_clean_v3_final_governance_reconciliation.json", "formal 16/7 reconciliation", "authoritative"),
            ("ROI margin resolution", "reports/audits/phase14_roi_margin_role_resolution.json", "role-resolved margins", "authoritative"),
            ("trainer", "scripts/training/train_phase14_refiner.py", "training implementation lineage", "final bound SHA"),
            ("evaluator", "scripts/evaluation/evaluate_phase14_clean_v3_diagnostic.py", "diagnostic evaluator", "final corrected SHA"),
            ("best.pt", "checkpoints/phase14_kub_refiner_unet_a3_256_seed42_clean_v3/best.pt", "selected epoch-56 checkpoint", "authoritative"),
            ("latest.pt", "checkpoints/phase14_kub_refiner_unet_a3_256_seed42_clean_v3/latest.pt", "final epoch-71 checkpoint", "authoritative"),
            ("global checkpoint", "checkpoints/phase10_kub_unetpp_seed42_512_clean_v3/best.pt", "GLOBAL_ONLY baseline", "authoritative"),
            ("localizer checkpoint", "checkpoints/phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3/best.pt", "predicted ROI source", "authoritative"),
        ]
        rows = []
        for label, path, role, status in provenance:
            full = ROOT / path
            rows.append({"artifact": label, "path": path, "SHA-256": hashlib.sha256(full.read_bytes()).hexdigest() if full.exists() else "UNAVAILABLE", "role": role, "status": status if full.exists() else "unavailable"})
        display(pd.DataFrame(rows))
        """
    ),
    md(
        """
        ## 18. Scientific interpretation and transition

        Phase 14 established that regional refinement has clear potential under Oracle ROI access,
        while predicted proposal delivery fails to preserve that benefit. Proposal/localizer
        quality is therefore the binding diagnostic bottleneck. This justified the later
        post-Phase-14 root-cause investigation.

        Later H3 evidence is not inserted into this Phase-14 record. It is documented separately
        at `notebooks/phasewise/post_phase14_h3_proposal_supply/`.
        """
    ),
    md("## 19. Reproducibility assertions and current terminal state"),
    code(
        """
        phase14_terminal = "PHASE14_CLEAN_V3_COMPLETE__DIAGNOSTIC_PROPOSAL_BOTTLENECK"
        phase15_terminal = "NOT_STARTED_AND_NOT_AUTHORIZED"
        test_terminal = "CLOSED"
        assert len(history) == 71
        assert training["outcome"]["total_epochs"] == 71
        assert training["outcome"]["best_epoch"] == 56
        assert abs(training["outcome"]["best_val_crop_dice"] - history["val_crop_dice"].max()) < 1e-12
        assert replay["verdict"] == "REPLAY_PASS__FROZEN_RULE_HONOURED"
        replay_bools = [v for v in replay["checks"].values() if isinstance(v, bool)]
        assert len(replay_bools) == 13 and all(replay_bools)
        assert population["executable_counts"]["val_samples"] == 103
        assert population["executable_counts"]["authoritative_components"] == 152
        assert diagnostic["final_classification"] == "DIAGNOSTIC_PROPOSAL_BOTTLENECK"
        assert phase15_terminal == "NOT_STARTED_AND_NOT_AUTHORIZED"
        assert test_terminal == "CLOSED"
        print("PHASE 14:", phase14_terminal)
        print("Phase 15:", phase15_terminal)
        print("TEST:", test_terminal)
        print("Scientific consistency assertions: PASS")
        """
    ),
]

notebook_path = OUT / "phase_14_regional_refiner_pipeline.ipynb"
notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
notebook_path.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

readme_path = OUT / "README.md"
previous_sha = "F5A218FCD329F5FDC2D163D7CB59CD5252883C732D4BC904873ECD67C282D888"
readme = f"""# Phase 14 Regional Refiner

This folder documents the completed Phase-14 Regional Refiner Diagnostic on the frozen
clean-v3 population. The notebook is a reproducibility and research-results record:
it loads authoritative reports, tables, checkpoints, history, and scripts without
retraining or rerunning model inference.

## Notebook contents

`phase_14_regional_refiner_pipeline.ipynb` includes:

- full 71-epoch training history;
- training/validation loss curves;
- validation Dice trajectory and best-so-far curve;
- recorded scheduler trajectory;
- early-stopping trajectory;
- best-checkpoint progression;
- trainer revision and resume provenance;
- bit-exact resume-equivalence evidence;
- epoch timing analysis with host-clock-skew caveat;
- complete diagnostic mode tables and comparison figures;
- contrast, special-set, and step-wise adjudication tables;
- dataset/population and configuration tables;
- saved qualitative evidence when available;
- expanded artifact provenance with SHA-256;
- current Phase-14 terminal assertions.

## Authoritative scripts and artifacts

- `scripts/training/train_phase14_refiner.py`
- `scripts/evaluation/evaluate_phase14_clean_v3_diagnostic.py`
- `scripts/audits/verify_phase13_part1b_canonical_selection_replay.py`
- `reports/audits/phase14_clean_v3_final_training_closure.json`
- `reports/audits/phase14_clean_v3_checkpoint_selection_replay.json`
- `reports/audits/phase14_resume_equivalence_verification.json`
- `reports/audits/phase14_clean_v3_global_reference_freeze.json`
- `reports/audits/phase14_clean_v3_diagnostic_evaluation.json`
- `reports/audits/phase14_clean_v3_formal_adjudication.json`
- `reports/audits/phase14_clean_v3_final_governance_reconciliation.json`
- `reports/audits/phase14_clean_v3_freeze_manifest.json`

Complete history:
`experiments/phase14_kub_refiner_unet_a3_256_seed42_clean_v3/history.csv`

Checkpoints remain referenced in place:

- `checkpoints/phase14_kub_refiner_unet_a3_256_seed42_clean_v3/`
- `checkpoints/phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3/`
- `checkpoints/phase10_kub_unetpp_seed42_512_clean_v3/`

## Terminal adjudication

Phase 14: `PHASE14_CLEAN_V3_COMPLETE__DIAGNOSTIC_PROPOSAL_BOTTLENECK`

Phase 15: `NOT_STARTED_AND_NOT_AUTHORIZED`

TEST and external TEST: `CLOSED`

## H3 relationship

H3 is post-Phase-14 causal/root-cause work and is intentionally kept separate at
`notebooks/phasewise/post_phase14_h3_proposal_supply/`. H3 results are not backfilled
into this frozen Phase-14 notebook.

## Notebook provenance

- Pre-upgrade notebook SHA-256: `{previous_sha}`
- Upgraded notebook execution status: pending until the notebook is run
- Training/inference during notebook reconstruction: none

The executed notebook SHA and final execution status should be updated here after
successful execution.
"""
readme_path.write_text(readme, encoding="utf-8")
print(OUT)
