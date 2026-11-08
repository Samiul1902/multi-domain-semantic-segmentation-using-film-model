"""Part 5 — ReMedFiLM_COMPLETE_MASTER.ipynb, organised around the FULL workflow."""
from __future__ import annotations

from pathlib import Path

from nb_common import BOOTSTRAP, SELF_TEST, code, md, write

ROOT = Path(r"D:\Softfors\jup")
DEST = ROOT / "full_doc_report" / "ReMedFiLM_COMPLETE_MASTER.ipynb"

cells: list = []


def sec(n: str, title: str, body: str = "") -> None:
    cells.append(md(f"\n---\n\n# {n} — {title}\n\n{body}".rstrip()))


cells.append(md("""
# ReMedFiLM — Complete Research Master

**Proposed system:** ReMedFiLM = FULL RA-MedFiLM-BARR
**Composition:** G (GlobalMedFiLM) + B_phi (Benefit Router) + R_psi (Regional Refiner)
+ S_omega (Post-Safety Gate)
**Parameters:** 4,837,420 · **VAL808 macro Dice:** 0.837290 (seed 42)

This notebook is the single entry point to the project. It is organised around the
**FULL ReMedFiLM workflow**, not chronological phase numbers. Every number traces to
a frozen artifact; every figure is generated from saved evidence.

| | |
|---|---|
| Execution mode | `ANALYSIS_ONLY` — training, inference and TEST access are blocked |
| Analysis seed | 20261027 |
| Population discipline | TRAIN 5,832 · VAL 808 · ROUTER_DEV 4,957 · ROUTER_HOLDOUT 875 · TEST 1,683 (consumed) |

> GlobalMedFiLM alone is **not** ReMedFiLM. It is the backbone and an ablation comparator.
"""))

cells += [code(BOOTSTRAP), code(SELF_TEST)]

# ---------------------------------------------------------------- 01 -------
sec("01", "Research overview",
    "Why the architecture is global-to-regional, and why the assembly matters.")
cells += [
    code(r'''
print("The problem")
print("-----------")
print("Medical segmentation models trained per-domain are expensive; one shared")
print("model across ISIC/BUSI/KVASIR/KUB must handle very different lesion scales.")
print("KUB stones can be a few hundred pixels inside a 512x512 field, while ISIC")
print("lesions can occupy most of the frame.")
print()
print("The idea")
print("--------")
print("Let one task-conditioned global model do the easy 80% cheaply, and spend")
print("extra compute only where a learned router predicts a real benefit - with a")
print("safety gate that can veto a bad refinement.")
'''),
    code(r'''
fig("Architecture", "A03_remedfilm_inference_path", width=800)
'''),
    code(r'''
print("Four domains, four binary tasks")
print("-------------------------------")
for d, note in [("ISIC 2018", "dermoscopy, CC0"),
                ("BUSI-WHU", "breast ultrasound, CC BY 4.0"),
                ("Kvasir-SEG", "GI polyp, research use"),
                ("KUB-StoneX", "stone radiograph, CC BY 4.0")]:
    print(f"  {d:14s} {note}")
print()
print("These are separate binary foreground/background tasks, not four output")
print("channels of one network.")
'''),
]

# ---------------------------------------------------------------- 02 -------
sec("02", "ReMedFiLM architecture",
    "Exact components, parameters and inference outcomes, read from the frozen contract.")
cells += [
    code(r'''
parts = pd.read_csv(TABLES / "REMEDFILM_COMPONENT_PARAMETERS.csv")
parts[["symbol", "model_class", "role", "conditional", "parameters"]].to_string(index=False)
'''),
    code(r'''
comp = parts[parts.symbol != "FULL"].set_index("symbol").parameters.astype(int)
total = int(parts[parts.symbol == "FULL"].parameters.iloc[0])
print("component sum:", int(comp.sum()), "| contract total:", total)
assert int(comp.sum()) == total, "component arithmetic does not close"
print("OK — arithmetic closes")
print()
print("DATA DEFECT DISCLOSURE")
print("----------------------")
raw = pd.read_csv(REPO / "reports/tables/phase26_component_inventory.csv")
print("phase26_component_inventory.csv stores G.parameters =",
      int(raw[raw.symbol == "G"].parameters.iloc[0]))
print("That value is G's total MACs, not its parameter count. The frozen table is")
print("left unmodified; this notebook uses the corrected derived table above.")
print("Recorded as DEFECT-01 in SCIENTIFIC_CORRECTIONS.json.")
'''),
    code(r'''
fig("Architecture", "A01_component_parameter_budget", width=720)
fig("Architecture", "A02_component_presence_matrix", width=520)
'''),
    code(r'''
b = json.loads((REPO / "reports/audits/phase21_global_medfilm_architecture_binding.json").read_text(encoding="utf-8"))
for k in ("architecture_id", "film_sites", "film_equation", "task_embedding_dim", "heads"):
    if k in b:
        print(f"{k}: {b[k]}")
'''),
    code(r'''
print("ASSEMBLY — not joint training")
print("-----------------------------")
print("G, R_psi, B_phi and S_omega were fitted separately and sequentially, each")
print("against a frozen upstream. No optimiser ever saw all four at once.")
print("Every ReMedFiLM claim is a claim about this assembly.")
'''),
]

# ---------------------------------------------------------------- 03 -------
sec("03", "Dataset protocol",
    "What was trained on what, and the grouping limitations that follow.")
cells += [
    code(r'''
comp = pd.read_csv(TABLES / "REMEDFILM_DATASET_COMPOSITION.csv")
comp
'''),
    code(r'''
fig("Statistics", "STAT04_population_accounting", width=660)
fig("Statistics", "D01_domain_and_split_composition", width=780)
'''),
    code(r'''
print("Grouping limitations (disclosed, not corrected)")
print("-----------------------------------------------")
print("1. KUB mixes full-field radiographs with ROI instance patches:")
print("   2,258 manifest rows = 873 full images + 1,385 ROI patches.")
print("2. BUSI and KUB carry patient identifiers; images from one patient are")
print("   not independent, so image-level bootstrap CIs are optimistic.")
print("3. VAL808 draws ISIC images from three pooled source archives, which were")
print("   re-split; VAL/TEST sample overlap is zero.")
'''),
    code(r'''
fig("Statistics", "D02_foreground_area_distribution", width=600)
'''),
]

# ---------------------------------------------------------------- 04 -------
sec("04", "Historical component training",
    "What was actually trained, with which recipe, and in what order.")
cells += [
    code(r'''
cl = json.loads((REPO / "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/closure.json").read_text(encoding="utf-8"))
cfg = cl["configuration"]
print("G — GlobalMedFiLM backbone")
print("  population :", cfg["dataset"])
print("  epochs     :", cl["total_completed_epochs"], "| best", cl["best_epoch"],
      "| stop", cl["stop_reason"])
print("  optimizer  :", cfg["optimizer"]["name"], cfg["optimizer"]["learning_rate"])
print("  scheduler  :", cfg["scheduler"]["name"], cfg["scheduler"]["T_max"])
print("  loss       :", cfg["loss"]["name"], cfg["loss"]["bce_weight"], "/", cfg["loss"]["dice_weight"])
print("  batch      :", cfg["training"]["batch_size"], "| amp", cfg["training"]["amp"])
print("  selection  :", cfg["training"]["checkpoint_metric"])
print("  best ckpt  :", cl["best_checkpoint_sha256"][:32], "...")
print("  wall clock :", round(cl["total_elapsed_seconds"] / 3600, 2), "h")
'''),
    code(r'''
reg = pd.read_csv(TABLES / "TRAINING_RUN_REGISTRY.csv")
print("total runs:", len(reg))
print(reg.groupby("model_role").size().to_string())
print()
print("evidence status:")
print(reg.evidence_status.value_counts().to_string())
'''),
    code(r'''
comp = reg[reg.model_role.isin(["BACKBONE", "COMPONENT"])]
comp[["run_id", "model", "seed", "epochs_completed", "best_epoch",
      "best_epoch_source", "evidence_status"]].head(20)
'''),
    code(r'''
print("DEPENDENCY CHAIN")
print("----------------")
print("G   (21)   TRAIN5832 -> VAL808 selection")
print(" +-> R_psi (25A)  ROI crops, 3 cross-fitted folds + final refit")
print("      +-> B_phi (25D)  OOF gain labels, 5 CV folds + final")
print("           +-> S_omega (25F)  routed candidates, 5 CV folds + final")
print("                +-> assembly (26) -> eval (27/29/30)")
'''),
]

# ---------------------------------------------------------------- 05 -------
sec("05", "Epoch-wise training evidence",
    "Genuine per-epoch records only. Nothing interpolated.")
cells += [
    code(r'''
hist = pd.read_csv(TABLES / "REMEDFILM_EPOCH_HISTORY.csv")
print("records:", len(hist), "| runs:", hist.run_id.nunique(),
      "| metrics:", hist.metric.nunique())
hist.head(6)
'''),
    code(r'''
for name in ["T1_train_val_loss", "T2_val_dice_across_epochs",
             "T3_val_iou_across_epochs", "T4_per_domain_learning_curves"]:
    fig("Training curves", name, width=700)
'''),
    code(r'''
for name in ["T5_learning_rate_schedule", "T6_best_epoch_selection",
             "T7_multiseed_histories", "T8_training_improvement_summary"]:
    fig("Training curves", name, width=700)
'''),
    code(r'''
g = hist[hist.run_id == "phase21_global_medfilm_fourdomain_seed42_clean_v3"]
piv = g.pivot_table(index="epoch", columns="metric", values="value")
print("GlobalMedFiLM: 81 epochs x", piv.shape[1], "metrics")
print("best val_macro_dice:", round(float(piv.val_macro_dice.max()), 8),
      "at epoch", int(piv.val_macro_dice.idxmax()))
print("closure best_epoch :", 66)
'''),
]

# ---------------------------------------------------------------- 06 -------
sec("06", "Internal validation",
    "Backbone versus FULL on the identical 808 samples.")
cells += [
    code(r'''
m = pd.read_csv(TABLES / "REMEDFILM_INTERNAL_METRICS.csv")
m[["domain", "n", "global_dice", "final_dice", "delta_dice", "final_hd95"]].to_string(index=False)
'''),
    code(r'''
fig("Internal validation", "I1_domain_metric_comparison", width=800)
fig("Internal validation", "I2_paired_delta_forest", width=680)
'''),
    code(r'''
paired = json.loads((TABLES / "REMEDFILM_PAIRED_DELTA.json").read_text(encoding="utf-8"))
print("paired macro Δ Dice:", f"{paired['point']:+.8f}",
      f"[{paired['ci_low']:+.8f}, {paired['ci_high']:+.8f}]")
print("B =", paired["n_boot"], "| frozen Phase 27 agreement:",
      f"{abs(paired['point'] - paired['cross_check_phase27_macro_point']):.2e}")
'''),
    code(r'''
fig("Internal validation", "I3_paired_delta_distribution", width=760)
fig("Internal validation", "I4_hd95_comparison", width=580)
'''),
]

# ---------------------------------------------------------------- 07 -------
sec("07", "Segmentation galleries",
    "Deterministic selection: worst / median / best per domain.")
cells += [
    code(r'''
for dom in ["ISIC", "BUSI", "KVASIR", "KUB"]:
    fig("Semantic segmentation", f"SEG_{dom}_global_vs_full", width=900)
'''),
    code(r'''
fig("Semantic segmentation", "SEG_failure_cases", width=920)
'''),
    code(r'''
ps = pd.read_csv(TABLES / "REMEDFILM_INTERNAL_PER_SAMPLE.csv")
print("worst six refinements (accepted, therefore residual failures):")
print(ps.nsmallest(6, "delta_dice")[["sample_id", "domain", "global_dice",
                                     "final_dice", "delta_dice"]].to_string(index=False))
'''),
]

# ---------------------------------------------------------------- 08 -------
sec("08", "Class and subclass analysis",
    "Verified subgroups only — KUB stone location and size taxonomy.")
cells += [
    code(r'''
sub = pd.read_csv(REPO / "reports/tables/phase21_kub_subgroup_analysis.csv")
sub[["subgroup", "n", "dice", "iou", "precision", "recall", "hd95"]].to_string(index=False)
'''),
    code(r'''
fig("Internal validation", "SG1_kub_stone_subgroups", width=580)
fig("Internal validation", "SG2_kub_size_stratification", width=580)
'''),
    code(r'''
print("NOT_RECORDED: BUSI lesion subgroups, polyp size categories.")
print("Only KUB has a verified subgroup taxonomy in the frozen artifacts.")
'''),
]

# ---------------------------------------------------------------- 09 -------
sec("09", "External evaluation",
    "884 retrospective cases, three cohorts, never pooled.")
cells += [
    code(r'''
ext = pd.read_csv(TABLES / "REMEDFILM_EXTERNAL_METRICS.csv")
ext[ext.metric == "Dice"][["cohort", "arm", "n_total", "mean", "ci_low", "ci_high"]].to_string(index=False)
'''),
    code(r'''
fig("External evaluation", "EXT01_external_dice", width=740)
fig("External evaluation", "EXT03_stonefree_false_positive", width=560)
'''),
    code(r'''
pc = pd.read_csv(REPO / "reports/tables/c1_external_stress_per_case.csv")
sf = pc[pc.gt_empty.astype(str).str.lower() == "true"]
print("stone-free cases:", len(sf))
for arm, g in sf.groupby("arm"):
    print(f"  {arm:8s}: {(g.pred_empty.astype(str).str.lower() == 'false').sum()}/{len(g)} receive foreground")
print()
print("Preserved negative finding: the gate does not fix false positives on")
print("negative studies, because it scores refinement benefit, not lesion presence.")
'''),
]

# ---------------------------------------------------------------- 10 -------
sec("10", "Component progression",
    "Stage-wise compute and harm — across two different populations.")
cells += [
    code(r'''
prog = pd.read_csv(TABLES / "REMEDFILM_PROGRESSION_RESULTS.csv")
prog[["stage", "stage_name", "population", "mean_dice", "net_delta_pp",
      "harm_rate", "gmacs_lower_bound"]].to_string(index=False)
'''),
    code(r'''
fig("Progression", "PROG01_stage_compute_and_harm", width=740)
fig("Progression", "PROG02_benefit_harm_tradeoff", width=620)
'''),
]

# ---------------------------------------------------------------- 11 -------
sec("11", "Full ablation",
    "13 arms on ROUTER_DEVELOPMENT, with the negative A8-vs-A7 contrast preserved.")
cells += [
    code(r'''
abl = pd.read_csv(TABLES / "REMEDFILM_ABLATION_RESULTS.csv")
abl[["arm", "n_routed", "mean_true_delta_dice_routed", "harmful_activation_share",
     "benefit_capture_vs_positive_mass", "evidence_class"]].to_string(index=False)
'''),
    code(r'''
fig("Ablation", "ABL01_arm_mean_delta", width=780)
fig("Ablation", "ABL02_paired_contrasts_forest", width=660)
fig("Ablation", "ABL03_ablation_diagnostics", width=880)
'''),
    code(r'''
bs = pd.read_csv(REPO / "reports/tables/phase28_table_08_bootstrap_statistics.csv")
a8 = bs[bs.contrast == "A8_vs_A7"].iloc[0]
print("A8 vs A7:", f"{a8.mean_difference:+.3e}",
      f"[{a8.ci95_low:+.3e}, {a8.ci95_high:+.3e}]",
      "-> includes zero:", not (a8.ci95_low > 0 or a8.ci95_high < 0))
print()
print("The pre-specified matched contrast is inconclusive. The safety gate's")
print("marginal contribution is NOT statistically established.")
'''),
]

# ---------------------------------------------------------------- 12 -------
sec("12", "Error propagation",
    "Grounded stage counts and the prevented-versus-residual harm split.")
cells += [
    code(r'''
ps = pd.read_csv(TABLES / "REMEDFILM_INTERNAL_PER_SAMPLE.csv")
n = len(ps)
sel = int((ps.router_decision == "EXECUTE").sum())
acc = int((ps.branch == "EXECUTE_THEN_ACCEPT").sum())
rej = int((ps.branch == "EXECUTE_THEN_REJECT").sum())
print(f"images            : {n}")
print(f"router selected   : {sel} ({sel/n:.1%})")
print(f"router skipped    : {n - sel}")
print(f"safety accepted   : {acc}")
print(f"safety rejected   : {rej}")
'''),
    code(r'''
fig("Routing and safety", "RT02_stage_flow", width=740)
fig("Routing and safety", "RT01_routing_outcomes", width=760)
'''),
    code(r'''
ex = ps[ps.router_decision == "EXECUTE"]
accd = ex[ex.branch == "EXECUTE_THEN_ACCEPT"].delta_dice
rejd = ex[ex.branch == "EXECUTE_THEN_REJECT"].delta_dice
print(f"accepted n={len(accd)}  mean Δ {accd.mean():+.6f}  harmful {int((accd < -1e-12).sum())}")
print(f"rejected n={len(rejd)}  mean Δ {rejd.mean():+.6f}  harmful {int((rejd < -1e-12).sum())}")
print()
print(f"harm prevented: {-rejd[rejd < 0].sum():.4f}")
print(f"harm delivered: {-accd[accd < 0].sum():.4f}")
'''),
]

# ---------------------------------------------------------------- 13 -------
sec("13", "Statistical reproducibility",
    "Three downstream seeds on a shared frozen backbone.")
cells += [
    code(r'''
d = json.loads((REPO / "reports/audits/phase29_phase_d_three_seed_descriptive_summary.json").read_text(encoding="utf-8"))
pd.DataFrame([{"metric": m["metric"], "seed42": m["seed42"], "seed123": m["seed123"],
               "seed3407": m["seed3407"], "mean": m["mean"], "sd": m["sample_sd_ddof1"]}
              for m in d["per_metric"]]).round(8)
'''),
    code(r'''
fig("Statistics", "STAT01_seedwise_macro_metrics", width=760)
fig("Statistics", "STAT02_bootstrap_distribution", width=620)
'''),
    code(r'''
g = [m for m in d["per_metric"] if m["metric"] == "macro_global_dice"][0]
print("macro_global_dice SD across seeds:", g["sample_sd_ddof1"])
print("-> backbone identical; only downstream components were re-fitted")
print("-> NOT three independent end-to-end runs")
print("-> no p-values computed, none valid")
'''),
    code(r'''
fig("Statistics", "STAT03_seedwise_per_domain", width=700)
'''),
]

# ---------------------------------------------------------------- 14 -------
sec("14", "Robustness and interpretability",
    "12,928 perturbation instances, zero TEST reads, zero training.")
cells += [
    code(r'''
r = json.loads((REPO / "reports/audits/phase36_robustness_scientific_result_v1_23.json").read_text(encoding="utf-8"))
for k in ("clean_passes", "perturbed_g_forwards", "test_reads", "training", "optimizer_steps"):
    print(f"  {k:22s}: {r['counters'][k]}")
print("clean equivalence all_pass:", r["clean_equivalence"]["all_pass"])
'''),
    code(r'''
fig("Robustness", "ROB01_perturbation_degradation", width=800)
fig("Robustness", "ROB02_domain_degradation", width=720)
'''),
    code(r'''
rows = pd.DataFrame(r["image_rows"])
kub = rows[rows.domain == "KUB"].groupby("condition").paired_delta_dice.mean().sort_values()
print("KUB worst conditions:")
print(kub.head(5).round(4).to_string())
print()
print("Interpretability: Phase 35 produced task-conditioning diagnostics, not a")
print("causal attribution study. No saliency map is offered as causal evidence.")
'''),
]

# ---------------------------------------------------------------- 15 -------
sec("15", "Computational efficiency",
    "ReMedFiLM FULL plotted as its own point — the earlier report omitted it.")
cells += [
    code(r'''
eff = pd.read_csv(TABLES / "REMEDFILM_EFFICIENCY.csv")
eff.to_string(index=False)
'''),
    code(r'''
fig("Efficiency", "EFF01_accuracy_vs_compute", width=760)
fig("Efficiency", "EFF02_latency_breakdown", width=700)
'''),
    code(r'''
c2 = json.loads((REPO / "reports/tables/c2_barr/c2_barr_aggregate.json").read_text(encoding="utf-8"))
g = c2["compute"]["analytical_gmacs_lower_bound"]
print("G only            :", g["LITERAL_GLOBAL_ONLY_C1"])
print("FULL expected     :", g["FINAL_A8_C9_EXPECTED_CONDITIONAL"])
print("always-refine     :", g["LITERAL_ALWAYS_REFINE_C2"])
print()
print("CORRECTION: earlier reports quoted 34.72 GMACs and 83.79% Dice.")
print("  34.72 is the always-refine cost, not the deployed conditional cost.")
print("  83.79% matches no frozen artifact; re-scoring gives 0.837290.")
print("  Net gain is +0.221 pp, not +0.28 pp.")
'''),
    code(r'''
print("Four distinct 'compute' quantities — never conflate:")
print("  analytical GMACs (lower bound) | expected conditional | always-refine")
print("  measured batch-1 p50 (forward only) | full-pipeline latency NOT_RECORDED")
'''),
]

# ---------------------------------------------------------------- 16 -------
sec("16", "Historical TEST disclosure",
    "Read from the frozen summary only. TEST is not reopened.")
cells += [
    code(r'''
p39 = json.loads((REPO / "reports/audits/phase39_final_test_v1_2_scientific_result.json").read_text(encoding="utf-8"))
for k, v in p39.items():
    if not isinstance(v, (dict, list)):
        print(f"  {k}: {v}")
'''),
    code(r'''
dom = p39.get("per_domain") or p39.get("domains") or []
if isinstance(dom, dict):
    dom = [{"domain": k, **v} for k, v in dom.items()]
print(pd.DataFrame(dom).to_string(index=False) if dom else "per-domain block absent")
print()
print("One-shot access consumed. No C1/C2/C3 comparison exists on TEST.")
'''),
]

# ---------------------------------------------------------------- 17 -------
sec("17", "Conclusions and limitations",
    "Established, descriptive, and missing — kept strictly apart.")
cells += [
    code(r'''
summary = pd.DataFrame([
    ("GlobalMedFiLM VAL808 macro Dice 0.835079", "ESTABLISHED", "Phase 21"),
    ("ReMedFiLM FULL VAL808 macro Dice 0.837290", "ESTABLISHED", "Phase 27 re-scored"),
    ("Paired macro Δ +0.00221 [0.00115, 0.00329]", "ESTABLISHED", "10k bootstrap"),
    ("A8 vs A7 matched contrast", "INCONCLUSIVE (CI includes 0)", "Phase 28"),
    ("13-arm ablation on 4,957", "ESTABLISHED", "Phase 28"),
    ("External 884 retrospective", "ESTABLISHED (no pooling)", "C1 external"),
    ("Stone-free false positives", "NEGATIVE FINDING 14/14", "C1 external"),
    ("Robustness, 12 perturbations", "ESTABLISHED", "Phase 36"),
    ("C1 learned vs identity FiLM", "NOT_ESTABLISHED", "0/6 runs"),
    ("C2 causal component attribution", "NOT_ESTABLISHED", "not executed"),
    ("C3 8-model x 3-seed benchmark", "NOT_ESTABLISHED", "0/24 cells"),
    ("Prospective external validation", "NOT_ESTABLISHED", "no cohort"),
    ("TEST comparative endpoint", "NOT_ESTABLISHED", "access consumed"),
], columns=["claim", "status", "evidence"])
summary
'''),
    code(r'''
print("FINAL STATEMENT")
print("---------------")
print("ReMedFiLM FULL is the proposed method throughout; GlobalMedFiLM is its")
print("backbone and an ablation comparator.")
print()
print("No model was retrained. No new inference was run. TEST was not reopened.")
print("Missing experiments are disclosed, not simulated.")
'''),
    code(SELF_TEST),
]

write(DEST, cells, {"notebook": "COMPLETE_MASTER"})
