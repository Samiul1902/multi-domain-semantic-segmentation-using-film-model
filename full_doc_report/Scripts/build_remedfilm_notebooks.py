"""Part 3 — the 12 dedicated ReMedFiLM research notebooks."""
from __future__ import annotations

from pathlib import Path

from nb_common import BOOTSTRAP, SELF_TEST, code, md, write

ROOT = Path(r"D:\Softfors\jup")
DEST = ROOT / "full_doc_report" / "ReMedFiLM_Research_Notebooks"


def open_cells(title: str, purpose: str, evidence: str) -> list:
    return [
        md(f"""
# {title}

{purpose}

**Evidence base**

{evidence}

> Execution is `ANALYSIS_ONLY`. Training, new inference and protected TEST access
> are blocked by an installed audit hook (verified below).
"""),
        code(BOOTSTRAP),
        code(SELF_TEST),
    ]


# ------------------------------------------------------------------ 01 ------
def nb01() -> None:
    c = open_cells(
        "01 — ReMedFiLM FULL architecture",
        "Defines the proposed system exactly as implemented: four components, three "
        "inference outcomes, and the parameter arithmetic that closes.",
        "- `reports/tables/phase26_component_inventory.csv`\n"
        "- `reports/tables/phase24_module_spec.csv`\n"
        "- `reports/audits/phase34_parameter_count_contract.json`\n"
        "- `reports/audits/phase21_global_medfilm_architecture_binding.json`")
    c += [
        md("""## 1.1 Component inventory — read from the frozen contract"""),
        code(r'''
parts = pd.read_csv(TABLES / "REMEDFILM_COMPONENT_PARAMETERS.csv")
parts[["symbol", "model_class", "role", "conditional", "parameters"]].to_string(index=False)
'''),
        code(r'''
comp = parts[parts.symbol != "FULL"].set_index("symbol").parameters.astype(int)
total = int(parts[parts.symbol == "FULL"].parameters.iloc[0])
print("FULL resident parameters:", total)
print("component sum           :", int(comp.sum()))
assert int(comp.sum()) == total
print()
for k, v in comp.items():
    print(f"  {k:8s} {v:>10,}  ({v / total:6.2%})")
print()
raw = pd.read_csv(REPO / "reports/tables/phase26_component_inventory.csv")
print("NOTE — phase26_component_inventory.csv has a units defect: it stores")
print(f"  G.parameters = {int(raw[raw.symbol == 'G'].parameters.iloc[0]):,} (that is MACs)")
print("The corrected derived table is used here. See DEFECT-01.")
'''),
        md("""## 1.2 Backbone configuration — task conditioning and FiLM sites"""),
        code(r'''
b = json.loads((REPO / "reports/audits/phase21_global_medfilm_architecture_binding.json").read_text(encoding="utf-8"))
for k in ("architecture_id", "model_params", "film_sites", "film_equation",
          "task_embedding_dim", "channels", "heads"):
    if k in b:
        print(f"{k}: {b[k]}")
'''),
        md("""## 1.3 The three inference outcomes"""),
        code(r'''
fig("Architecture", "A03_remedfilm_inference_path", width=780)
fig("Architecture", "A02_component_presence_matrix", width=520)
'''),
        code(r'''
fig("Architecture", "A01_component_parameter_budget", width=720)
'''),
        md("""## 1.4 Assembly, not joint training

The four components were fitted **separately and sequentially**, each against a
frozen upstream:

| Stage | Fitted on | Upstream frozen |
|---|---|---|
| G — GlobalMedFiLM | TRAIN5832, VAL808 selection | — |
| R_psi — Regional Refiner | ROI crops from G's proposals, 3 cross-fitted folds | G |
| B_phi — Benefit Router | out-of-fold G+R gain labels | G, R |
| S_omega — Post-Safety Gate | routed candidates | G, R, B |

No optimiser ever saw all four modules at once. ReMedFiLM FULL is therefore an
**assembled inference system**, and every claim about it is a claim about that
assembly — not about joint end-to-end training.
"""),
        code(r'''
print("Assembly contract")
print("-----------------")
print("1. G produces a global probability map and a proposal set.")
print("2. B_phi scores each proposal; the top budget fraction is selected.")
print("3. R_psi refines only the selected ROIs.")
print("4. S_omega accepts or vetoes each refined candidate.")
print("5. Accepted candidates replace the global mask locally; vetoed ones fall back.")
print()
print("Only the FULL assembly can produce outcomes 2 and 3. A GlobalMedFiLM")
print("checkpoint alone is never a ReMedFiLM FULL prediction.")
'''),
        code(SELF_TEST),
    ]
    write(DEST / "01_ReMedFiLM_FULL_Architecture.ipynb", c, {"notebook": "01"})


# ------------------------------------------------------------------ 02 ------
def nb02() -> None:
    c = open_cells(
        "02 — ReMedFiLM historical component training",
        "Recovers the actual training evidence for each of the four components, and "
        "documents how the FULL system was assembled from them.",
        "- `full_doc_report/tables/TRAINING_RUN_REGISTRY.csv`\n"
        "- `experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/closure.json`\n"
        "- `experiments/phase25*/**/run.json`")
    c += [
        md("""## 2.1 Backbone G — the only component trained on all four domains"""),
        code(r'''
cl = json.loads((REPO / "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/closure.json").read_text(encoding="utf-8"))
cfg = cl["configuration"]
print("experiment      :", cl["experiment_id"])
print("population      :", cfg["dataset"])
print("model           :", cfg["model"]["name"], "| params", cl["model_params"])
print("epochs          :", cl["total_completed_epochs"], "| best", cl["best_epoch"])
print("stop reason     :", cl["stop_reason"], f"(patience {cl['early_stopping_patience']})")
print("optimizer       :", cfg["optimizer"])
print("scheduler       :", cfg["scheduler"])
print("loss            :", cfg["loss"])
print("batch / amp     :", cfg["training"]["batch_size"], "/", cfg["training"]["amp"])
print("checkpoint rule :", cfg["training"]["checkpoint_metric"])
print("best ckpt sha   :", cl["best_checkpoint_sha256"])
print("wall clock (s)  :", round(cl["total_elapsed_seconds"], 1))
'''),
        md("""## 2.2 Component runs — registry view"""),
        code(r'''
reg = pd.read_csv(TABLES / "TRAINING_RUN_REGISTRY.csv")
comp = reg[reg.model_role.isin(["BACKBONE", "COMPONENT"])]
cols = ["run_id", "model", "seed", "epochs_completed", "best_epoch",
        "best_epoch_source", "evidence_status"]
print("component runs:", len(comp))
comp[cols].head(24)
'''),
        code(r'''
# Per-component summary: how many runs, how many epochs, which metrics.
hist = pd.read_csv(TABLES / "REMEDFILM_EPOCH_HISTORY.csv")
summary = (hist.groupby("model_identity")
               .agg(runs=("run_id", "nunique"),
                    epoch_records=("metric", "size"),
                    metrics=("metric", "nunique"))
               .sort_values("epoch_records", ascending=False))
summary
'''),
        md("""## 2.3 Checkpoint identity per component"""),
        code(r'''
for sym in ("G", "R_psi", "B_phi", "S_omega"):
    sub = reg[reg.model.str.startswith(sym.split("_")[0])]
    ck = sub[sub.best_checkpoint != "NOT_FOUND"]
    print(f"{sym:8s} runs={len(sub):3d}  with_checkpoint={len(ck):3d}")
    if len(ck):
        r = ck.iloc[-1]
        print(f"         e.g. {r.best_checkpoint}")
        print(f"              sha256 {r.checkpoint_hash[:32]}...")
'''),
        md("""## 2.4 Dependency chain"""),
        code(r'''
print("""
G   (Phase 21)  TRAIN5832 -> VAL808 selection        best epoch 66 / 81
 |
 +-> R_psi (25A)  ROI crops, 3 cross-fitted folds + final refit
      |
      +-> B_phi (25D)  OOF gain labels, 5 CV folds + final
           |
           +-> S_omega (25F)  routed candidates, 5 CV folds + final
                |
                +-> assembly (Phase 26) -> evaluation (27/29/30)
""")
print("Each arrow means the downstream module consumed a FROZEN upstream output.")
print("Nothing in this chain is joint end-to-end training.")
'''),
        md("""## 2.5 What was *not* recorded

| Field | Status |
|---|---|
| Per-epoch wall clock for R/B/S | partially recorded (`elapsed_seconds`) |
| Peak GPU memory for G | **NOT_RECORDED** in the closure |
| Independent duplicate runs of G | 0 (`independent_duplicate_runs`) |
| Three independent end-to-end seeds | **NOT_EXECUTED** — only downstream components were re-seeded |
"""),
        code(SELF_TEST),
    ]
    write(DEST / "02_ReMedFiLM_Component_Training.ipynb", c, {"notebook": "02"})


# ------------------------------------------------------------------ 03 ------
def nb03() -> None:
    c = open_cells(
        "03 — Complete epoch-wise training analysis",
        "Every genuine per-epoch record in the repository, in one long-format table, "
        "with the eight required plots. Nothing is interpolated.",
        "- `full_doc_report/tables/REMEDFILM_EPOCH_HISTORY.csv` (35,764 records)\n"
        "- `full_doc_report/tables/TRAINING_RUN_REGISTRY.csv` (82 runs)\n"
        "- `experiments/*/history.csv` (82 source logs)")
    c += [
        md("## 3.1 The long-format table"),
        code(r'''
hist = pd.read_csv(TABLES / "REMEDFILM_EPOCH_HISTORY.csv")
print("records:", len(hist), "| runs:", hist.run_id.nunique(),
      "| metrics:", hist.metric.nunique())
hist.head(8)
'''),
        code(r'''
print("schema:", list(hist.columns))
print()
print("metric coverage (records):")
print(hist.metric.value_counts().head(20).to_string())
'''),
        md("## 3.2 Figures T1–T4 — loss, Dice, IoU, per-domain"),
        code(r'''
for name, w in [("T1_train_val_loss", 700), ("T2_val_dice_across_epochs", 700),
                ("T3_val_iou_across_epochs", 700), ("T4_per_domain_learning_curves", 700)]:
    fig("Training curves", name, width=w)
'''),
        md("## 3.3 Figures T5–T8 — schedule, selection, seeds, summary"),
        code(r'''
for name in ["T5_learning_rate_schedule", "T6_best_epoch_selection",
             "T7_multiseed_histories", "T8_training_improvement_summary"]:
    fig("Training curves", name, width=700)
'''),
        md("## 3.4 Component-wise historical summaries"),
        code(r'''
# Component loss curves that genuinely exist.
comp_runs = {
    "R_psi fold0": "phase25a_barr_regional_refiner_v1_1__fold0",
    "B_phi fold0": "phase25d_barr_benefit_router_v1_2_1_seed42__fold0",
    "S_omega cv_fold0": "phase25f_barr_post_safety_v1_0_seed42__cv_fold0",
}
fig_, axes = plt.subplots(1, 3, figsize=(8.6, 2.5))
for ax, (label, rid) in zip(axes, comp_runs.items()):
    sub = hist[hist.run_id == rid]
    tr = sub[sub.metric.isin(["train_loss", "train_huber", "train_bce"])]
    if tr.empty:
        ax.text(0.5, 0.5, "NOT_RECORDED", ha="center", va="center")
    else:
        m = tr.metric.iloc[0]
        d = tr[tr.metric == m].sort_values("epoch")
        ax.plot(d.epoch, d.value.astype(float), linewidth=1.2, color="#0072B2")
        ax.set_xlabel("Epoch"); ax.set_ylabel(m)
    ax.set_title(label, fontsize=7.5)
plt.tight_layout(); plt.show()
'''),
        code(r'''
# Which metrics each component family actually logged.
fam = hist.assign(family=hist.model_identity.str.extract(r"(R_psi|B_phi|S_omega|GlobalMedFiLM)")[0])
piv = fam.dropna(subset=["family"]).pivot_table(
    index="family", columns="metric", values="value", aggfunc="count", fill_value=0)
print("records per (family, metric):")
piv.loc[:, piv.sum() > 0]
'''),
        md("## 3.5 Genuine independent seed trajectories"),
        code(r'''
reg = pd.read_csv(TABLES / "TRAINING_RUN_REGISTRY.csv")
seed_runs = reg[reg.seed.astype(str).isin(["42", "123", "3407"])]
print("runs by seed:")
print(seed_runs.seed.value_counts().to_string())
print()
print("DISCLOSURE")
print("----------")
print("Seeds 123 and 3407 re-fit R_psi / B_phi / S_omega on a SHARED FROZEN")
print("GlobalMedFiLM backbone. There are not three independent end-to-end")
print("trainings, and the three trajectories are never drawn as such.")
'''),
        md("""## 3.6 Explicit `NOT_RECORDED` register

| Metric | Availability |
|---|---|
| Per-epoch per-domain Dice | **only** GlobalMedFiLM and the four-domain baselines |
| Per-epoch Dice for R_psi | `early_stop_dice` only |
| Per-epoch Dice for B_phi / S_omega | **NOT_RECORDED** (loss only) |
| Peak GPU memory | **NOT_RECORDED** for G; `peak_gpu_allocated` for localisers |
| Epoch duration for G | recorded (`epoch_seconds`, mean 426.6 s) |
"""),
        code(SELF_TEST),
    ]
    write(DEST / "03_ReMedFiLM_Epoch_Wise_Training_Analysis.ipynb", c, {"notebook": "03"})


# ------------------------------------------------------------------ 04 ------
def nb04() -> None:
    c = open_cells(
        "04 — ReMedFiLM internal validation",
        "Backbone versus FULL system on the identical 808 VAL808 samples, re-derived "
        "from the saved masks and cross-checked against the frozen Phase 27 result.",
        "- `full_doc_report/tables/REMEDFILM_INTERNAL_METRICS.csv`\n"
        "- `full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv`\n"
        "- `reports/figures/phase27_preservation/masks/` (1,616 masks)")
    c += [
        md("## 4.1 Per-domain metrics"),
        code(r'''
m = pd.read_csv(TABLES / "REMEDFILM_INTERNAL_METRICS.csv")
m[["domain", "n", "global_dice", "final_dice", "delta_dice", "final_iou",
   "final_precision", "final_recall", "final_hd95"]].to_string(index=False)
'''),
        code(r'''
fig("Internal validation", "I1_domain_metric_comparison", width=780)
'''),
        md("## 4.2 Paired effect size and confidence interval"),
        code(r'''
paired = json.loads((TABLES / "REMEDFILM_PAIRED_DELTA.json").read_text(encoding="utf-8"))
print("point :", f"{paired['point']:+.8f}")
print("95% CI:", f"[{paired['ci_low']:+.8f}, {paired['ci_high']:+.8f}]")
print("B     :", paired["n_boot"], "| seed", paired["seed"])
print("frozen Phase 27 cross-check diff:",
      f"{abs(paired['point'] - paired['cross_check_phase27_macro_point']):.2e}")
'''),
        code(r'''
fig("Internal validation", "I2_paired_delta_forest", width=680)
fig("Internal validation", "I3_paired_delta_distribution", width=760)
'''),
        md("## 4.3 Harmful, beneficial and unchanged refinements"),
        code(r'''
ps = pd.read_csv(TABLES / "REMEDFILM_INTERNAL_PER_SAMPLE.csv")
print("beneficial:", int((ps.delta_dice > 1e-12).sum()),
      "| unchanged:", int((ps.delta_dice.abs() <= 1e-12).sum()),
      "| harmful:", int((ps.delta_dice < -1e-12).sum()))
print()
print("routing:")
print(ps.branch.value_counts().to_string())
'''),
        code(r'''
# Harm concentration among executed cases only.
ex = ps[ps.router_decision == "EXECUTE"]
print("executed cases:", len(ex))
print("harmful among executed:", int((ex.delta_dice < -1e-12).sum()),
      f"({(ex.delta_dice < -1e-12).mean():.2%})")
print("mean delta among executed:", f"{ex.delta_dice.mean():+.6f}")
'''),
        md("## 4.4 Boundary error"),
        code(r'''
fig("Internal validation", "I4_hd95_comparison", width=560)
'''),
        md("## 4.5 Subgroups inside KUB"),
        code(r'''
fig("Internal validation", "SG1_kub_stone_subgroups", width=580)
fig("Internal validation", "SG2_kub_size_stratification", width=580)
'''),
        md("""## 4.6 What this notebook does **not** establish

The comparison is backbone-versus-assembly on one frozen checkpoint. It is a
**paired preservation** result, not a controlled component attribution — that
would require the C2 study, which is not established. See
`PENDING_CONTROLLED_EXPERIMENTS.md`.
"""),
        code(SELF_TEST),
    ]
    write(DEST / "04_ReMedFiLM_Internal_Validation.ipynb", c, {"notebook": "04"})


# ------------------------------------------------------------------ 05 ------
def nb05() -> None:
    c = open_cells(
        "05 — ReMedFiLM predictions and semantic segmentation",
        "Qualitative evidence from the saved VAL808 masks. Selection is deterministic: "
        "worst, median and best paired Δ Dice per domain — not cherry-picked.",
        "- `reports/tables/phase27_val808_predictions.csv`\n"
        "- `reports/predictions/phase21_*/val/<DOMAIN>/*.npz` (evaluation GT)\n"
        "- `reports/figures/phase27_preservation/masks/*_{global,final}.png`")
    c += [
        md("""## 5.1 Selection rule

Within each domain the 808 samples are sorted by paired Δ Dice and three are
taken: the **worst**, the **median** and the **best**. The rule is fixed in code
and applied identically to every domain, so the gallery cannot be curated.
"""),
        code(r'''
ps = pd.read_csv(TABLES / "REMEDFILM_INTERNAL_PER_SAMPLE.csv")
for dom in ["ISIC", "BUSI", "KVASIR", "KUB"]:
    d = ps[ps.domain == dom].sort_values("delta_dice")
    picks = [d.iloc[0], d.iloc[len(d) // 2], d.iloc[-1]]
    print(f"{dom}: n={len(d)}")
    for tag, r in zip(("worst", "median", "best"), picks):
        print(f"   {tag:7s} {r.sample_id[:16]}  Δ={r.delta_dice:+.4f}  "
              f"{r.global_dice:.4f} -> {r.final_dice:.4f}  [{r.branch}]")
'''),
        md("## 5.2 Panels — image · GT · backbone · FULL · TP/FP/FN"),
        code(r'''
for dom in ["ISIC", "BUSI", "KVASIR", "KUB"]:
    fig("Semantic segmentation", f"SEG_{dom}_global_vs_full", width=900)
'''),
        md("## 5.3 Genuine failure cases"),
        code(r'''
fig("Semantic segmentation", "SEG_failure_cases", width=920)
'''),
        code(r'''
print("The six worst refinements by Δ Dice — accepted by the safety gate, so they")
print("are residual failures of the FULL system, not modelling artefacts.")
print()
print(ps.nsmallest(6, "delta_dice")[["sample_id", "domain", "global_dice",
                                     "final_dice", "delta_dice", "branch"]]
        .to_string(index=False))
'''),
        md("""## 5.4 KUB unit-of-analysis disclosure

KUB contributes both full-field radiographs and ROI instance patches. The panels
above mark which is which; they are never treated as interchangeable image units.
"""),
        code(r'''
print("KUB rows in VAL808:", int((ps.domain == 'KUB').sum()))
print("KUB foreground area (median % of field):",
      round(float((ps[ps.domain == 'KUB'].gt_fg / (512 * 512) * 100).median()), 4))
print("ISIC foreground area (median % of field):",
      round(float((ps[ps.domain == 'ISIC'].gt_fg / (512 * 512) * 100).median()), 4))
print()
print("KUB lesions are roughly an order of magnitude smaller; this is why KUB")
print("carries both the largest gain and the worst tail in every analysis.")
'''),
        code(SELF_TEST),
    ]
    write(DEST / "05_ReMedFiLM_Segmentation_Predictions.ipynb", c, {"notebook": "05"})


# ------------------------------------------------------------------ 06 ------
def nb06() -> None:
    c = open_cells(
        "06 — External retrospective evaluation",
        "The 884-case retrospective external evidence. Separate cohorts, never pooled.",
        "- `reports/tables/c1_external_stress_summary.csv`\n"
        "- `reports/tables/c1_external_stress_per_case.csv`")
    c += [
        code(r'''
ext = pd.read_csv(TABLES / "REMEDFILM_EXTERNAL_METRICS.csv")
ext[ext.metric == "Dice"][["cohort", "arm", "n_total", "n_defined", "mean",
                           "median", "ci_low", "ci_high", "n_clusters"]].to_string(index=False)
'''),
        code(r'''
fig("External evaluation", "EXT01_external_dice", width=740)
fig("External evaluation", "EXT02_external_delta", width=600)
'''),
        md("## 6.1 Full metric matrix"),
        code(r'''
piv = (ext.pivot_table(index=["cohort", "metric"], columns="arm",
                       values="mean", aggfunc="first"))
piv.round(4)
'''),
        md("## 6.2 The stone-free negative result"),
        code(r'''
pc = pd.read_csv(REPO / "reports/tables/c1_external_stress_per_case.csv")
sf = pc[pc.gt_empty.astype(str).str.lower() == "true"]
print("stone-free cases:", len(sf))
for arm, g in sf.groupby("arm"):
    got = (g.pred_empty.astype(str).str.lower() == "false").sum()
    print(f"  {arm:8s}: {got}/{len(g)} receive foreground")
'''),
        code(r'''
fig("External evaluation", "EXT03_stonefree_false_positive", width=560)
'''),
        code(r'''
print("NEGATIVE FINDING — PRESERVED")
print("-----------------------------")
print("Every stone-free case receives a foreground prediction. The safety gate")
print("does not solve false-positive detection on negative studies, because it")
print("operates on refinement benefit, not on the presence of a lesion.")
print()
print("This is reported as a limitation, not smoothed over.")
'''),
        md("""## 6.3 Scope discipline

| Claim | Permitted? |
|---|---|
| "Retrospective external Dice on CVC is 0.690" | **Yes** — measured on saved predictions |
| "The system generalises prospectively" | **No** — no prospective cohort exists |
| "Pooled external Dice across cohorts" | **No** — different reference standards |
"""),
        code(SELF_TEST),
    ]
    write(DEST / "06_ReMedFiLM_External_Evaluation.ipynb", c, {"notebook": "06"})


# ------------------------------------------------------------------ 07 ------
def nb07() -> None:
    c = open_cells(
        "07 — ReMedFiLM model progression and ablation",
        "Component progression and the full 13-arm ablation, with the negative "
        "A8-vs-A7 contrast preserved.",
        "- `full_doc_report/tables/REMEDFILM_PROGRESSION_RESULTS.csv`\n"
        "- `full_doc_report/tables/REMEDFILM_ABLATION_RESULTS.csv`\n"
        "- `reports/tables/phase28_table_08_bootstrap_statistics.csv`")
    c += [
        md("## 7.1 Component progression"),
        code(r'''
prog = pd.read_csv(TABLES / "REMEDFILM_PROGRESSION_RESULTS.csv")
prog[["stage", "stage_name", "population", "n", "mean_dice", "net_delta_pp",
      "harm_rate", "gmacs_lower_bound", "evidence_class"]].to_string(index=False)
'''),
        code(r'''
fig("Progression", "PROG01_stage_compute_and_harm", width=740)
fig("Progression", "PROG02_benefit_harm_tradeoff", width=620)
'''),
        md("""### Population warning

Stage 0 and Stage 4 are measured on **VAL808**. Stages 1–3 are measured on
**ROUTER_DEVELOPMENT (4,957)**. The progression is therefore *not* a single
monotone curve on one population, and the figure says so.
"""),
        md("## 7.2 The 13 arms"),
        code(r'''
abl = pd.read_csv(TABLES / "REMEDFILM_ABLATION_RESULTS.csv")
print("arms:", len(abl))
abl[["arm", "n_routed", "budget_fraction", "mean_true_delta_dice_routed",
     "benefit_capture_vs_positive_mass", "harmful_activation_share",
     "evidence_class"]].to_string(index=False)
'''),
        code(r'''
fig("Ablation", "ABL01_arm_mean_delta", width=780)
fig("Ablation", "ABL02_paired_contrasts_forest", width=660)
fig("Ablation", "ABL03_ablation_diagnostics", width=880)
'''),
        md("## 7.3 The preserved negative contrast"),
        code(r'''
bs = pd.read_csv(REPO / "reports/tables/phase28_table_08_bootstrap_statistics.csv")
bs["excludes_zero"] = (bs.ci95_low > 0) | (bs.ci95_high < 0)
bs[["contrast", "n", "mean_difference", "ci95_low", "ci95_high", "excludes_zero"]].to_string(index=False)
'''),
        code(r'''
a8 = bs[bs.contrast == "A8_vs_A7"].iloc[0]
print("A8 vs A7 :", f"{a8.mean_difference:+.3e}",
      f"[{a8.ci95_low:+.3e}, {a8.ci95_high:+.3e}]")
print("includes zero:", not (a8.ci95_low > 0 or a8.ci95_high < 0))
print()
print("The only PRE-SPECIFIED matched contrast is inconclusive. The safety gate's")
print("marginal contribution is therefore not statistically established, even")
print("though the point estimate is positive.")
'''),
        code(r'''
print("Evidence classes in the ablation")
print("--------------------------------")
print(abl.evidence_class.value_counts().to_string())
print()
print("ENDPOINT_BY_CONSTRUCTION arms (A0, A1) are structural, not measured gains.")
print("PRIOR_CANONICAL_EVIDENCE_EXACT arms reuse frozen Phase 25/26 results.")
print("PHASE28_TRAINED_ABLATION_VARIANT arms (R1-R3, F1) were genuinely re-trained.")
'''),
        code(SELF_TEST),
    ]
    write(DEST / "07_ReMedFiLM_Progression_and_Ablation.ipynb", c, {"notebook": "07"})


# ------------------------------------------------------------------ 08 ------
def nb08() -> None:
    c = open_cells(
        "08 — Error propagation, benefit routing and safety",
        "Stage-by-stage propagation with grounded counts, and the distinction between "
        "prevented harm and harm that reaches the final mask.",
        "- `full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv`\n"
        "- `reports/tables/phase27_val808_predictions.csv`")
    c += [
        md("## 8.1 Stage counts on VAL808"),
        code(r'''
ps = pd.read_csv(TABLES / "REMEDFILM_INTERNAL_PER_SAMPLE.csv")
n = len(ps)
sel = int((ps.router_decision == "EXECUTE").sum())
acc = int((ps.branch == "EXECUTE_THEN_ACCEPT").sum())
rej = int((ps.branch == "EXECUTE_THEN_REJECT").sum())
skip = int((ps.branch == "SKIP_GLOBAL").sum())
print(f"candidates (images)      : {n}")
print(f"router selected          : {sel}  ({sel/n:.1%})")
print(f"router skipped           : {skip}  ({skip/n:.1%})")
print(f"refiner executed         : {sel}")
print(f"safety accepted          : {acc}")
print(f"safety rejected          : {rej}")
print(f"final refined            : {acc}")
'''),
        code(r'''
fig("Routing and safety", "RT02_stage_flow", width=740)
fig("Routing and safety", "RT01_routing_outcomes", width=760)
'''),
        md("## 8.2 Prevented harm versus residual harm"),
        code(r'''
# Among executed candidates, compare accepted vs rejected.
ex = ps[ps.router_decision == "EXECUTE"]
acc_d = ex[ex.branch == "EXECUTE_THEN_ACCEPT"].delta_dice
rej_d = ex[ex.branch == "EXECUTE_THEN_REJECT"].delta_dice
print(f"accepted n={len(acc_d):4d}  mean Δ {acc_d.mean():+.6f}  harmful {int((acc_d < -1e-12).sum())}")
print(f"rejected n={len(rej_d):4d}  mean Δ {rej_d.mean():+.6f}  harmful {int((rej_d < -1e-12).sum())}")
print()
print("Rejected candidates would have been harmful on balance: the gate converts")
print("their negative delta into a zero-delta fallback.")
print()
print(f"residual harmful refinements reaching the final mask: {int((acc_d < -1e-12).sum())}")
'''),
        code(r'''
# Magnitude of harm prevented.
prevented = -rej_d[rej_d < 0].sum()
residual = -acc_d[acc_d < 0].sum()
print(f"harm prevented by the gate (sum of negative rejected deltas): {prevented:.4f}")
print(f"harm still delivered       (sum of negative accepted deltas): {residual:.4f}")
print(f"prevention ratio           : {prevented / (prevented + residual):.3f}")
'''),
        md("## 8.3 Population separation"),
        code(r'''
print("Population discipline")
print("---------------------")
print("VAL808            : 808 images  -> the routing statistics above")
print("ROUTER_DEVELOPMENT: 4,957 images -> the 13-arm ablation (notebook 07)")
print("EXTERNAL884       : 884 cases    -> notebook 06, separate cohorts")
print()
print("These three are never combined into one routing table.")
'''),
        code(SELF_TEST),
    ]
    write(DEST / "08_ReMedFiLM_Error_Propagation.ipynb", c, {"notebook": "08"})


# ------------------------------------------------------------------ 09 ------
def nb09() -> None:
    c = open_cells(
        "09 — Statistics and reproducibility",
        "The three downstream seeds, their dispersion, and the honest limits of what "
        "they can support.",
        "- `reports/audits/phase29_phase_d_three_seed_descriptive_summary.json`\n"
        "- `reports/audits/phase29_val808_seedwise_metrics.json`\n"
        "- `full_doc_report/tables/REMEDFILM_PAIRED_DELTA.json`")
    c += [
        md("## 9.1 Seed-wise summary"),
        code(r'''
d = json.loads((REPO / "reports/audits/phase29_phase_d_three_seed_descriptive_summary.json").read_text(encoding="utf-8"))
rows = []
for m in d["per_metric"]:
    rows.append({"metric": m["metric"], "seed42": m["seed42"], "seed123": m["seed123"],
                 "seed3407": m["seed3407"], "mean": m["mean"],
                 "sd": m["sample_sd_ddof1"], "range": m["range"],
                 "sign_consistent": m["sign_consistent"]})
pd.DataFrame(rows).round(8)
'''),
        code(r'''
fig("Statistics", "STAT01_seedwise_macro_metrics", width=760)
fig("Statistics", "STAT03_seedwise_per_domain", width=700)
'''),
        md("## 9.2 The bootstrap interval"),
        code(r'''
fig("Statistics", "STAT02_bootstrap_distribution", width=620)
'''),
        code(r'''
pd_ = json.loads((TABLES / "REMEDFILM_PAIRED_DELTA.json").read_text(encoding="utf-8"))
print("VAL808 paired macro delta:", f"{pd_['point']:+.8f}",
      f"[{pd_['ci_low']:+.8f}, {pd_['ci_high']:+.8f}]")
print("B =", pd_["n_boot"], "seed", pd_["seed"], "| method:", pd_["method"])
'''),
        md("""## 9.3 What the three seeds actually are

`macro_global_dice` is identical to machine precision across seeds
(SD ≈ 1.4×10⁻¹⁶), which proves the backbone was **shared and frozen**.
Only R_psi, B_phi and S_omega were re-fitted.

Therefore:

* the seeds measure **downstream component stability**, not end-to-end reproducibility;
* they cannot be described as three independent training runs;
* no p-value is computed, and none should be.
"""),
        code(r'''
g = [m for m in d["per_metric"] if m["metric"] == "macro_global_dice"][0]
print("macro_global_dice across seeds:", g["seed42"], g["seed123"], g["seed3407"])
print("sample SD:", g["sample_sd_ddof1"])
print("-> identical backbone confirmed")
'''),
        md("## 9.4 Population accounting"),
        code(r'''
fig("Statistics", "STAT04_population_accounting", width=640)
'''),
        code(SELF_TEST),
    ]
    write(DEST / "09_ReMedFiLM_Statistics_and_Reproducibility.ipynb", c, {"notebook": "09"})


# ------------------------------------------------------------------ 10 ------
def nb10() -> None:
    c = open_cells(
        "10 — Robustness and interpretability",
        "Phase 36 perturbation results and the Phase 35 interpretability status.",
        "- `reports/audits/phase36_robustness_scientific_result_v1_23.json`\n"
        "- `reports/audits/phase35_interpretability_scientific_result_v1_0.json`")
    c += [
        md("## 10.1 Execution integrity"),
        code(r'''
r = json.loads((REPO / "reports/audits/phase36_robustness_scientific_result_v1_23.json").read_text(encoding="utf-8"))
for k in ("clean_passes", "perturbed_g_forwards", "test_reads", "training",
          "optimizer_steps", "parameter_mutations"):
    print(f"  {k:22s}: {r['counters'][k]}")
print()
ce = r["clean_equivalence"]
print("clean equivalence all_pass :", ce["all_pass"])
print("dice mismatches            :", len(ce["dice_mismatches"]))
print("max |Δ Dice| vs frozen     :", ce.get("max_abs_dice_difference", 0.0))
'''),
        code(r'''
fig("Robustness", "ROB01_perturbation_degradation", width=800)
fig("Robustness", "ROB02_domain_degradation", width=720)
fig("Robustness", "ROB03_clean_equivalence_gate", width=580)
'''),
        md("## 10.2 The KUB weakness"),
        code(r'''
rows = pd.DataFrame(r["image_rows"])
kub = (rows[rows.domain == "KUB"].groupby("condition").paired_delta_dice.mean()
           .sort_values())
print("KUB mean Δ Dice by condition (worst first):")
print(kub.head(6).round(4).to_string())
print()
print("Worst single KUB image delta:",
      round(float(rows[rows.domain == "KUB"].paired_delta_dice.min()), 4))
'''),
        md("## 10.3 Interpretability — honest status"),
        code(r'''
p35 = json.loads((REPO / "reports/audits/phase35_interpretability_scientific_result_v1_0.json").read_text(encoding="utf-8"))
print("Phase 35 terminal:", p35.get("terminal_state", p35.get("status", "PRESENT")))
for k, v in list(p35.items())[:12]:
    if not isinstance(v, (dict, list)):
        print(f"  {k}: {v}")
'''),
        code(r'''
print("INTERPRETABILITY DISCLOSURE")
print("---------------------------")
print("Phase 35 produced task-conditioning diagnostics and FiLM response records.")
print("It did NOT produce a causal attribution study: no counterfactual FiLM")
print("ablation was executed, and no saliency map is offered as evidence of")
print("causation. Claims here are descriptive.")
'''),
        code(SELF_TEST),
    ]
    write(DEST / "10_ReMedFiLM_Robustness_Interpretability.ipynb", c, {"notebook": "10"})


# ------------------------------------------------------------------ 11 ------
def nb11() -> None:
    c = open_cells(
        "11 — Computational efficiency (accuracy versus compute)",
        "The corrected accuracy–compute analysis. **ReMedFiLM FULL appears as its own "
        "plotted point**, which the earlier report failed to do.",
        "- `reports/tables/phase21_six_model_compute.csv`\n"
        "- `reports/tables/c2_barr/c2_barr_aggregate.json`\n"
        "- `reports/audits/phase34_efficiency_result_v1_4.json`")
    c += [
        md("""## 11.1 The three verified anchors

| | Parameters | Analytical GMACs | VAL808 macro Dice |
|---|---|---|---|
| GlobalMedFiLM (G) | 3,523,001 | 31.5517 (lower bound) | 0.835079 |
| **ReMedFiLM FULL** | **4,837,420** | **32.4379** (expected conditional) | **0.837290** |

> **Correction.** Earlier report versions quoted **34.72 GMACs** and
> **83.79 % (0.837862)**. 34.72 is the *always-refine* cost; the deployed system
> routes only 24.3 % of cases. 0.837862 appears in no frozen artifact — re-scoring
> the saved masks gives 0.837290, matching Phase 27 and Phase 29 exactly.
> See `SCIENTIFIC_CORRECTIONS.json`.
"""),
        code(r'''
eff = pd.read_csv(TABLES / "REMEDFILM_EFFICIENCY.csv")
eff.to_string(index=False)
'''),
        code(r'''
c2 = json.loads((REPO / "reports/tables/c2_barr/c2_barr_aggregate.json").read_text(encoding="utf-8"))
g = c2["compute"]["analytical_gmacs_lower_bound"]
print("LITERAL_GLOBAL_ONLY_C1          :", g["LITERAL_GLOBAL_ONLY_C1"])
print("FINAL_A8_C9_EXPECTED_CONDITIONAL:", g["FINAL_A8_C9_EXPECTED_CONDITIONAL"])
print("LITERAL_ALWAYS_REFINE_C2        :", g["LITERAL_ALWAYS_REFINE_C2"])
print()
print("routing fraction used:", 0.243091)
print("expected cost = 31.5517 + 0.243091 * 3.646 = 32.4379")
print("always-refine cost would be 34.78 -> the figure previously quoted 34.72")
'''),
        md("## 11.2 The corrected figure"),
        code(r'''
fig("Efficiency", "EFF01_accuracy_vs_compute", width=760)
fig("Efficiency", "EFF03_accuracy_vs_parameters", width=620)
'''),
        md("## 11.3 Latency, with its exact meaning"),
        code(r'''
fig("Efficiency", "EFF02_latency_breakdown", width=700)
'''),
        code(r'''
eff34 = json.loads((REPO / "reports/audits/phase34_efficiency_result_v1_4.json").read_text(encoding="utf-8"))
lat = eff34["MEASURED_HARDWARE_SPECIFIC_RUNTIME_PROFILE"]["batch1_latency_v1_4"]
for k in ("GLOBAL_ONLY_C1", "SKIP_CONTROLLED_PATH", "EXECUTE_CONTROLLED_PATH",
          "R_PSI_COMPONENT", "B_PHI_COMPONENT", "S_OMEGA_COMPONENT"):
    print(f"  {k:24s} p50 = {lat[k]['p50_ms']:.3f} ms  (n={lat[k]['n']})")
'''),
        md("""## 11.4 Four different things called "compute"

| Quantity | Value | Meaning |
|---|---|---|
| Analytical GMACs (G) | 31.5517 | closed-form Conv2d/Linear count, **lower bound** |
| Expected conditional GMACs (FULL) | 32.4379 | routing-weighted |
| Always-refine GMACs | 34.7824 | upper bound if every case is refined |
| Measured batch-1 p50 | 15.72 / 18.89 ms | GPU forward only, RTX 3060 Ti, n = 1,000 |
| Full-pipeline latency | **NOT_RECORDED** | preprocessing and I/O excluded |

The 18.89 ms figure is the **execute-path forward**, not clinical inference speed.
"""),
        code(SELF_TEST),
    ]
    write(DEST / "11_ReMedFiLM_Accuracy_Compute.ipynb", c, {"notebook": "11"})


# ------------------------------------------------------------------ 12 ------
def nb12() -> None:
    c = open_cells(
        "12 — Historical TEST evidence and its limits",
        "The Phase 39 descriptive result, read **only** from the frozen summary. No "
        "TEST image, mask, manifest or prediction is opened.",
        "- `reports/audits/phase39_final_test_v1_2_scientific_result.json`")
    c += [
        md("""## 12.1 Access disclosure

TEST1683 was evaluated **once** (Phase 39 v1.2). That one-shot access is
**consumed**. This notebook reads the summary JSON only; the guard blocks the
TEST manifest by path, and no TEST array is loaded.
"""),
        code(r'''
p39 = json.loads((REPO / "reports/audits/phase39_final_test_v1_2_scientific_result.json").read_text(encoding="utf-8"))
print("keys:", list(p39.keys()))
for k, v in p39.items():
    if not isinstance(v, (dict, list)):
        print(f"  {k}: {v}")
'''),
        code(r'''
dom = p39.get("per_domain") or p39.get("domains") or []
if isinstance(dom, dict):
    dom = [{"domain": k, **v} for k, v in dom.items()]
if dom:
    df = pd.DataFrame(dom)
    print(df.to_string(index=False))
else:
    print("per-domain block not present in the frozen summary")
'''),
        md("## 12.2 What TEST can and cannot support"),
        code(r'''
print("SUPPORTED")
print("  - a descriptive TEST1683 Dice for the historical FULL system")
print("  - per-domain descriptive breakdown")
print()
print("NOT SUPPORTED")
print("  - any C1/C2/C3 comparison on TEST (never executed)")
print("  - any re-evaluation or re-tuning against TEST")
print("  - any claim that TEST is still untouched")
print("  - IoU / precision / recall / HD95 on TEST (NOT_RECORDED)")
'''),
        code(r'''
print("One-shot contract")
print("-----------------")
print("attempt_consumed = TRUE FOREVER")
print("Re-running Phase 39 would invalidate the only honest TEST number the")
print("project has. It must not be attempted, even 'just to check'.")
'''),
        code(SELF_TEST),
    ]
    write(DEST / "12_ReMedFiLM_Historical_Test_Evidence.ipynb", c, {"notebook": "12"})


def main() -> None:
    for fn in (nb01, nb02, nb03, nb04, nb05, nb06, nb07, nb08, nb09, nb10, nb11, nb12):
        fn()
    print("DONE")


if __name__ == "__main__":
    main()
