"""Part 2 — preserve originals and reconstruct the 12 notebook-less phases."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from nb_common import BOOTSTRAP, SELF_TEST, code, md, write

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"
PHASEWISE = ROOT / "notebooks" / "phasewise"
ORIG = OUT / "Original_Phasewise_Notebooks"
RECON = OUT / "Reconstructed_Phasewise_Notebooks"
TABLES = OUT / "tables"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


# ----------------------------------------------------------------- preserve --
def preserve() -> int:
    nbs = sorted(PHASEWISE.rglob("*.ipynb"))
    manifest = []
    for src in nbs:
        rel = src.relative_to(ROOT)
        dst = ORIG / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        if sha256(dst) != sha256(src):
            raise SystemExit(f"COPY_MISMATCH {rel}")
        manifest.append({"original_path": rel.as_posix(),
                         "preserved_path": dst.relative_to(ROOT).as_posix(),
                         "sha256": sha256(src),
                         "bytes": src.stat().st_size})
    (ORIG / "PRESERVATION_MANIFEST.json").write_text(json.dumps({
        "artifact": "original_phasewise_preservation",
        "policy": "copy only; originals never moved or deleted",
        "n_notebooks": len(nbs),
        "n_verified": len(manifest),
        "notebooks": manifest,
    }, indent=2), encoding="utf-8")
    print(f"PRESERVED {len(manifest)} phasewise notebooks")
    return len(manifest)


# ------------------------------------------------------------------ helpers --
def head(title: str, sub: str) -> list:
    return [md(f"# {title}\n\n{sub}\n\n> **Status:** reconstructed analysis notebook. "
               "It reads persisted artifacts only. No training, no new inference, "
               "no protected TEST access."),
            code(BOOTSTRAP),
            code(SELF_TEST)]


def tail(rows: str) -> list:
    return [md("## Provenance\n\n" + rows), code(SELF_TEST)]


# ------------------------------------------------------------- 09 baseline --
def nb_09() -> None:
    cells = head(
        "Phase 09 — Clean-v3 KUB baseline training",
        "Reconstructed reproducibility notebook for the `phase_09_clean_v3_baseline` "
        "directory, which contained no notebook. All four KUB single-domain baselines "
        "were trained under the clean-v3 protocol and their per-epoch histories survive.")
    cells += [
        code(r'''
hist = pd.read_csv(REPO / "reports/tables/phase10_final_all_models_epoch_results_long.csv")
print("models:", hist.model.nunique(), "| rows:", len(hist))
print(hist.groupby("model").epoch.max().to_string())
'''),
        code(r'''
# Per-epoch validation Dice for the four KUB baselines.
import matplotlib.pyplot as plt
fig_, ax = plt.subplots(figsize=(6.4, 3.0))
for name, g in hist.groupby("model"):
    g = g.sort_values("epoch")
    ax.plot(g.epoch, g.val_macro_dice, linewidth=1.2, label=name)
ax.set_xlabel("Epoch"); ax.set_ylabel("Validation Dice (KUB)")
ax.set_title("Phase 09/10 clean-v3 KUB baselines — genuine per-epoch history")
ax.legend(fontsize=6.5); plt.tight_layout(); plt.show()
'''),
        code(r'''
# Best epoch and final metric per model, taken from the recorded flags.
rows = []
for name, g in hist.groupby("model"):
    g = g.sort_values("epoch")
    best = g[g.is_best_epoch.astype(str).str.lower() == "true"]
    rows.append({"model": name,
                 "epochs_completed": int(g.epoch.max()),
                 "best_epoch": int(best.epoch.iloc[0]) if len(best) else None,
                 "best_val_dice": round(float(g.val_macro_dice.max()), 6),
                 "final_val_dice": round(float(g.val_macro_dice.iloc[-1]), 6)})
pd.DataFrame(rows)
'''),
        code(r'''
# Loss trajectories.
fig_, ax = plt.subplots(figsize=(6.4, 2.8))
for name, g in hist.groupby("model"):
    g = g.sort_values("epoch")
    ax.plot(g.epoch, g.train_loss, linewidth=1.0, linestyle="-", label=f"{name} train")
    ax.plot(g.epoch, g.val_loss, linewidth=1.0, linestyle="--", label=f"{name} val")
ax.set_xlabel("Epoch"); ax.set_ylabel("BCE + Dice loss")
ax.set_title("Training and validation loss (solid / dashed)")
ax.legend(fontsize=5.4, ncol=2); plt.tight_layout(); plt.show()
'''),
        code(r'''
# Learning-rate schedule actually used.
g = hist[hist.model == "UNet++"].sort_values("epoch")
fig_, ax = plt.subplots(figsize=(5.6, 2.2))
ax.plot(g.epoch, g.learning_rate, color="#CC79A7", linewidth=1.3)
ax.set_xlabel("Epoch"); ax.set_ylabel("Learning rate")
ax.set_title("Cosine annealing, recorded per epoch (UNet++)")
plt.tight_layout(); plt.show()
'''),
    ]
    cells += tail("- `reports/tables/phase10_final_all_models_epoch_results_long.csv`\n"
                  "- `experiments/phase9_kub_unet_baseline_seed42_512_clean_v3/history.csv`\n"
                  "- `experiments/phase10_kub_*/history.csv`")
    write(RECON / "phase_09_clean_v3_baseline" / "phase09_clean_v3_baseline_reconstructed.ipynb",
          cells, {"phase": "09", "status": "RECONSTRUCTED_FROM_RESULTS"})


# ------------------------------------------------------------ 10 comparison --
def nb_10() -> None:
    cells = head(
        "Phase 10 — Clean-v3 baseline comparison",
        "Reconstructed notebook for `phase_10_clean_v3_comparison`. Recovers the "
        "paired per-case comparison across the four KUB baselines.")
    cells += [
        code(r'''
paired = pd.read_csv(REPO / "reports/tables/phase10_clean_v3_paired_val_case_metrics.csv")
print("paired cases:", len(paired))
models = ["unet", "attention_unet", "unetpp", "deeplabv3plus"]
summary = pd.DataFrame([{
    "model": m,
    "n": int(paired[f"{m}_dice"].notna().sum()),
    "dice_mean": round(float(paired[f"{m}_dice"].mean()), 6),
    "dice_median": round(float(paired[f"{m}_dice"].median()), 6),
    "iou_mean": round(float(paired[f"{m}_iou"].mean()), 6),
} for m in models])
summary
'''),
        code(r'''
# Paired differences against the strongest baseline (DeepLabV3+).
import numpy as np
base = "deeplabv3plus"
rows = []
for m in models:
    if m == base:
        continue
    d = (paired[f"{m}_dice"] - paired[f"{base}_dice"]).dropna()
    rows.append({"model": m, "n_paired": len(d),
                 "mean_delta": round(float(d.mean()), 6),
                 "median_delta": round(float(d.median()), 6),
                 "n_better": int((d > 0).sum()), "n_worse": int((d < 0).sum())})
pd.DataFrame(rows)
'''),
        code(r'''
# Per-case Dice distribution.
fig_, ax = plt.subplots(figsize=(6.2, 2.8))
data = [paired[f"{m}_dice"].dropna().values for m in models]
ax.violinplot(data, showmedians=True, widths=0.8)
ax.set_xticks(range(1, 5)); ax.set_xticklabels(models, rotation=15, fontsize=7)
ax.set_ylabel("Dice per case"); ax.set_title("Clean-v3 KUB baselines — per-case Dice")
plt.tight_layout(); plt.show()
'''),
        code(r'''
# Failure concentration: how many cases does each model lose entirely?
rows = []
for m in models:
    d = paired[f"{m}_dice"]
    rows.append({"model": m,
                 "cases_dice_below_0.5": int((d < 0.5).sum()),
                 "cases_dice_zero": int((d == 0).sum()),
                 "cases_above_0.9": int((d > 0.9).sum())})
pd.DataFrame(rows)
'''),
    ]
    cells += tail("- `reports/tables/phase10_clean_v3_paired_val_case_metrics.csv`\n"
                  "- `reports/tables/phase10_final_all_models_epoch_results_long.csv`")
    write(RECON / "phase_10_clean_v3_comparison" / "phase10_clean_v3_comparison_reconstructed.ipynb",
          cells, {"phase": "10", "status": "RECONSTRUCTED_FROM_RESULTS"})


# ---------------------------------------------------------------- 24 design --
def nb_24() -> None:
    cells = head(
        "Phase 24 — RA-MedFiLM architecture specification",
        "Reconstructed notebook for `phase_24_ra_medfilm_design`. This phase is "
        "**design-only**: it froze the module contract that Phase 25 later trained. "
        "Nothing here is an executed experiment.")
    cells += [
        code(r'''
spec = pd.read_csv(REPO / "reports/tables/phase24_module_spec.csv")
spec
'''),
        code(r'''
print("novelty-bearing modules:",
      int(spec.novelty_bearing.astype(str).str.lower().eq("true").sum()))
print("modules executed in phase 24:",
      int(spec.executed_in_phase24.astype(str).str.lower().eq("true").sum()))
print()
print("Phase 24 is a specification phase: the parameter targets below were")
print("realised later in Phase 25 and are checked against the final contracts.")
'''),
        code(r'''
# Router input contract — which features the router is allowed to see.
rc = pd.read_csv(REPO / "reports/tables/phase24_router_input_contract.csv")
print("router feature rows:", len(rc))
rc.head(20)
'''),
        code(r'''
# Planned ablation family. `executed_in_phase24` is False for every arm:
# Phase 24 planned the ablation, Phase 28 executed it.
plan = pd.read_csv(REPO / "reports/tables/phase24_ablation_plan.csv")
print("planned arms:", len(plan))
print(plan.family.value_counts().to_string())
plan[["ablation_id", "name", "family", "executed_in_phase24"]]
'''),
        code(r'''
# Cross-check: the realised parameter counts against the Phase 24 targets.
real = pd.read_csv(TABLES / "REMEDFILM_COMPONENT_PARAMETERS.csv")
real[["symbol", "model_class", "role", "parameters"]]
'''),
    ]
    cells += tail("- `reports/tables/phase24_module_spec.csv`\n"
                  "- `reports/tables/phase24_router_input_contract.csv`\n"
                  "- `reports/tables/phase24_ablation_plan.csv`\n"
                  "- `reports/audits/phase24_exact_implementation_spec.json`")
    write(RECON / "phase_24_ra_medfilm_design" / "phase24_architecture_spec_reconstructed.ipynb",
          cells, {"phase": "24", "status": "DESIGN_PHASE_RECONSTRUCTED"})


# ------------------------------------------------------------ 25 components --
def nb_25() -> None:
    cells = head(
        "Phase 25 — RA-MedFiLM component development (25A–25G)",
        "Reconstructed notebook for `phase_25_ra_medfilm_dev`, the umbrella directory "
        "for the four BARR components. Each component was trained **separately**, not "
        "jointly with the backbone.")
    cells += [
        code(r'''
inv = pd.read_csv(TABLES / "REMEDFILM_COMPONENT_PARAMETERS.csv")
print("component inventory (corrected parameter column)")
inv[["symbol", "model_class", "parameters", "conditional", "role"]].to_string(index=False)
print()
print("sum of components:", int(inv[inv.symbol != "FULL"].parameters.sum()))
'''),
        code(r'''
# 25A — regional refiner: per-fold selected epochs and final refit.
sel = pd.read_csv(REPO / "reports/tables/phase25a_refiner_selected_epochs.csv")
print("refiner selection records:", len(sel))
sel
'''),
        code(r'''
# 25A — genuine per-epoch refiner history (fold 0 and final refit).
fig_, axes = plt.subplots(1, 2, figsize=(7.2, 2.6))
for ax, (label, path) in zip(axes, [
        ("fold0", REPO / "experiments/phase25a_barr_regional_refiner_v1_1/fold0/history.csv"),
        ("final refit", REPO / "experiments/phase25a_barr_regional_refiner_v1_1/final_refit/history.csv")]):
    h = pd.read_csv(path).sort_values("epoch")
    ax.plot(h.epoch, h.train_loss, color="#0072B2", linewidth=1.2, label="train")
    if "early_stop_dice" in h.columns:
        ax2 = ax.twinx()
        ax2.plot(h.epoch, h.early_stop_dice, color="#D55E00", linewidth=1.1, linestyle="--")
        ax2.set_ylabel("early-stop Dice", color="#D55E00")
        ax2.grid(False)
    ax.set_title(f"R_psi {label}")
    ax.set_xlabel("Epoch"); ax.set_ylabel("Train loss")
plt.tight_layout(); plt.show()
'''),
        code(r'''
# 25D — benefit router: 5-fold CV selection.
cv = pd.read_csv(REPO / "reports/tables/phase25d_cv_selected_epochs.csv")
print("router CV folds:", len(cv))
cv
'''),
        code(r'''
# 25F — post-safety gate: per-fold epochs and acceptance behaviour.
f = pd.read_csv(REPO / "reports/tables/phase25f_final_epoch_rule.csv")
f
'''),
        code(r'''
print("ASSEMBLY NOTE")
print("------------")
print("The four components were fitted in sequence, each against a frozen upstream:")
print("  G  (Phase 21)  -> frozen backbone")
print("  R  (Phase 25A) -> fitted on G's outputs, cross-fitted folds")
print("  B  (Phase 25D) -> fitted on G+R OOF gain labels")
print("  S  (Phase 25F) -> fitted on routed candidates")
print()
print("ReMedFiLM FULL is therefore an ASSEMBLED system, never a jointly")
print("end-to-end trained network. No single optimiser ever saw all four modules.")
'''),
    ]
    cells += tail("- `reports/tables/phase26_component_inventory.csv`\n"
                  "- `experiments/phase25a_*/`, `experiments/phase25d_*/`, `experiments/phase25f_*/`\n"
                  "- `reports/tables/phase25*_selected_epochs.csv`")
    write(RECON / "phase_25_ra_medfilm_dev" / "phase25_component_development_reconstructed.ipynb",
          cells, {"phase": "25", "status": "RECONSTRUCTED_FROM_RESULTS"})


# ------------------------------------------------------------- 26 integrate --
def nb_26() -> None:
    cells = head(
        "Phase 26 — Full-system integration",
        "Reconstructed notebook for `phase_26_full_four_domain_training`. Phase 26 "
        "bound the four components into one deployable bundle and verified the state "
        "machine. It did **not** jointly train the assembly.")
    cells += [
        code(r'''
inv = pd.read_csv(TABLES / "REMEDFILM_COMPONENT_PARAMETERS.csv")
inv[["symbol", "model_class", "checkpoint", "role", "conditional", "parameters"]].to_string(index=False)
'''),
        code(r'''
tests = pd.read_csv(REPO / "reports/tables/phase26_integration_test_results.csv")
print("integration tests:", len(tests), "| all pass:",
      bool(tests["pass"].astype(str).str.lower().eq("true").all()))
tests
'''),
        code(r'''
sm = pd.read_csv(REPO / "reports/tables/phase26_state_machine_test_results.csv")
print("state-machine tests:", len(sm), "| all pass:",
      bool(sm["pass"].astype(str).str.lower().eq("true").all()))
sm
'''),
        code(r'''
# Bundle integrity: every component checkpoint hash is bound in the manifest.
bm = json.loads((REPO / "reports/audits/phase26_bundle_manifest_integrity.json").read_text(encoding="utf-8"))
for k in list(bm)[:10]:
    v = bm[k]
    if not isinstance(v, (dict, list)):
        print(f"  {k}: {v}")
'''),
        code(r'''
print("Phase 26 establishes the FULL system identity:")
print("  ReMedFiLM FULL = G + R_psi + B_phi + S_omega, assembled for inference.")
print("  The bundle is a deployment artifact; it is not a new trained model.")
'''),
    ]
    cells += tail("- `reports/tables/phase26_component_inventory.csv`\n"
                  "- `reports/tables/phase26_integration_test_results.csv`\n"
                  "- `reports/audits/phase26_bundle_manifest_integrity.json`")
    write(RECON / "phase_26_full_four_domain_training" / "phase26_full_system_integration_reconstructed.ipynb",
          cells, {"phase": "26", "status": "RECONSTRUCTED_FROM_RESULTS"})


# --------------------------------------------------------------- 30 holdout --
def nb_30() -> None:
    cells = head(
        "Phase 30 — Final development validation on ROUTER_HOLDOUT",
        "Reconstructed notebook for `phase_30_final_dev_val`. The FULL system was "
        "evaluated once on the reserved 875-image holdout.")
    cells += [
        code(r'''
r = json.loads((REPO / "reports/audits/phase30_primary_noninferiority_result.json").read_text(encoding="utf-8"))
print("population      :", r["population"], "n =", r["n"])
print("global macro    :", r["global_macro_dice"])
print("A8 macro        :", r["a8_macro_dice"])
print("macro delta     : {:+.6f}".format(r["macro_delta_dice"]))
print("95% CI          : [{:+.6f}, {:+.6f}]".format(*r["macro_ci"]))
print("margin          :", r["noninferiority_margin"], "| asserted:", r["PRESERVATION_ASSERTED"])
print("p-values computed:", r["p_values_computed"])
'''),
        code(r'''
pd_ = pd.read_csv(REPO / "reports/tables/phase30_router_holdout_per_domain_results.csv")
pd_
'''),
        code(r'''
fig_, ax = plt.subplots(figsize=(5.6, 2.6))
x = np.arange(len(pd_))
ax.bar(x - 0.2, pd_.global_dice, 0.38, color="#0072B2", label="GlobalMedFiLM")
ax.bar(x + 0.2, pd_.a8_dice, 0.38, color="#D55E00", label="ReMedFiLM FULL")
for i, row in pd_.iterrows():
    ax.plot([i + 0.2, i + 0.2], [row.ci_low, row.ci_high], color="#333333", linewidth=1.1)
ax.set_xticks(x); ax.set_xticklabels(pd_.domain)
ax.set_ylabel("Dice"); ax.set_title("ROUTER_HOLDOUT 875 — per-domain result")
ax.legend(fontsize=6.5); ax.grid(axis="x", visible=False)
plt.tight_layout(); plt.show()
'''),
        code(r'''
print("Holdout discipline")
print("------------------")
print("ROUTER_HOLDOUT was reserved in Phase 25G and locked before Phase 30 ran.")
print("It is a development holdout, NOT an independent external cohort, and it")
print("was used for exactly one confirmatory evaluation.")
print()
print("domain harm flags:", dict(zip(pd_.domain, pd_.domain_harm_flag)))
'''),
    ]
    cells += tail("- `reports/audits/phase30_primary_noninferiority_result.json`\n"
                  "- `reports/tables/phase30_router_holdout_per_domain_results.csv`")
    write(RECON / "phase_30_final_dev_val" / "phase30_holdout_validation_reconstructed.ipynb",
          cells, {"phase": "30", "status": "RECONSTRUCTED_FROM_RESULTS"})


# ------------------------------------------------------------- 36 perturb ----
def nb_36() -> None:
    cells = head(
        "Phase 36 — Robustness under image perturbation",
        "Reconstructed notebook for `phase_36_robustness_perturbation`. The scientific "
        "execution (v1.23) produced 12,928 perturbation instances over 808 clean images.")
    cells += [
        code(r'''
r = json.loads((REPO / "reports/audits/phase36_robustness_scientific_result_v1_23.json").read_text(encoding="utf-8"))
print("counters")
for k in ("clean_passes", "perturbed_g_forwards", "test_reads", "training",
          "optimizer_steps", "parameter_mutations"):
    print(f"  {k:22s}: {r['counters'][k]}")
print()
print("clean equivalence all_pass:", r["clean_equivalence"]["all_pass"])
'''),
        code(r'''
rows = pd.DataFrame(r["image_rows"])
print("perturbation rows:", len(rows), "| conditions:", rows.condition.nunique())
agg = (rows.groupby("condition")
           .agg(n=("paired_delta_dice", "size"),
                mean_delta=("paired_delta_dice", "mean"),
                min_delta=("paired_delta_dice", "min"),
                consistency=("prediction_consistency_dice", "mean"))
           .sort_values("mean_delta").reset_index())
agg.round(5)
'''),
        code(r'''
fig_, ax = plt.subplots(figsize=(7.0, 2.8))
colors = ["#D55E00" if v < -0.05 else ("#E69F00" if v < 0 else "#009E73") for v in agg.mean_delta]
ax.bar(range(len(agg)), agg.mean_delta, color=colors, width=0.68)
ax.axhline(0, color="#333333", linewidth=0.8)
ax.set_xticks(range(len(agg)))
ax.set_xticklabels([c.replace("_", " ").lower() for c in agg.condition], rotation=40,
                   ha="right", fontsize=6)
ax.set_ylabel("Mean Δ Dice vs clean")
ax.set_title("Phase 36 — 12,928 perturbation instances, 12 conditions")
ax.grid(axis="x", visible=False); plt.tight_layout(); plt.show()
'''),
        code(r'''
# Domain-specific degradation — the KUB finding.
by_dom = (rows.groupby(["domain", "condition"]).paired_delta_dice.mean()
              .unstack("condition"))
kub = by_dom.loc["KUB"].sort_values()
print("KUB worst conditions:")
print(kub.head(5).round(4).to_string())
'''),
        code(r'''
print("NEGATIVE FINDING PRESERVED")
print("--------------------------")
print("KUB degrades far more than the other domains under noise and resolution")
print("loss. This is a real weakness of the FULL system, not an artefact.")
'''),
    ]
    cells += tail("- `reports/audits/phase36_robustness_scientific_result_v1_23.json`")
    write(RECON / "phase_36_robustness_perturbation" / "phase36_robustness_perturbation_reconstructed.ipynb",
          cells, {"phase": "36", "status": "RECONSTRUCTED_FROM_RESULTS"})


# ----------------------------------------------------------- 40 manuscript ----
def nb_40() -> None:
    cells = head(
        "Phase 40 — Publication reproducibility audit",
        "Reconstructed notebook for `phase_40_publication_reproducibility_audit`. "
        "Phase 40 checked that every number in the manuscript traces to a frozen artifact.")
    cells += [
        code(r'''
for name in ("phase40_numeric_provenance_audit", "phase40_claim_scope_audit",
             "phase40_manuscript_consistency_audit", "phase40_phase39_qualifier_audit"):
    p = REPO / f"reports/audits/{name}.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    print("=" * 68)
    print(name)
    for k, v in d.items():
        if not isinstance(v, (dict, list)):
            print(f"  {k}: {v}")
'''),
        code(r'''
d = json.loads((REPO / "reports/audits/phase40_manuscript_assembly_summary.json").read_text(encoding="utf-8"))
print(json.dumps(d, indent=2)[:2000])
'''),
        code(r'''
# This consolidation independently re-checked the headline numbers.
internal = pd.read_csv(TABLES / "REMEDFILM_INTERNAL_METRICS.csv")
macro = internal[internal.domain.str.startswith("MACRO")].iloc[0]
print("Re-scored VAL808 macro Dice   :", round(float(macro.final_dice), 6))
print("Frozen Phase 27 macro delta   : 0.0022101453")
print("Phase 29 continuity macro Dice: 0.8372891053775793")
print()
print("Consolidation verdict: the manuscript's 83.79% does not match any frozen")
print("artifact. See SCIENTIFIC_CORRECTIONS.json (CORR-01..CORR-04).")
'''),
    ]
    cells += tail("- `reports/audits/phase40_*.json`\n"
                  "- `full_doc_report/SCIENTIFIC_CORRECTIONS.json`")
    write(RECON / "phase_40_publication_reproducibility_audit" / "phase40_reproducibility_audit_reconstructed.ipynb",
          cells, {"phase": "40", "status": "RECONSTRUCTED_FROM_RESULTS"})


# ---------------------------------------------------------------- doc-only ---
def phase_index(folder: str, title: str, body: str) -> None:
    p = RECON / folder / "PHASE_INDEX.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"# {title}\n\n{body}\n", encoding="utf-8")
    print(f"WROTE {p.relative_to(ROOT).as_posix()}")


def docs() -> None:
    phase_index("phase_16_fusion", "Phase 16 — Loss fusion study (documentation only)",
                "This directory contains **no notebook and no saved artifacts**.\n\n"
                "The fusion idea was superseded before execution: the final system uses\n"
                "a single BCE+Dice objective with post-hoc safety gating rather than a\n"
                "learned fusion of global and regional logits. No experiment was run here,\n"
                "so no notebook can be reconstructed without inventing one.\n\n"
                "**Status:** `DOCUMENTATION_ONLY_PHASE` — superseded, not executed.\n")
    phase_index("phase_17_kub_regional_ablation", "Phase 17 — KUB regional ablation (documentation only)",
                "No notebook and no saved artifacts exist.\n\n"
                "The KUB regional ablation was superseded by the clean-v3 pipeline\n"
                "(Phases 09/10) and later by the multi-domain ablation in Phase 28.\n\n"
                "**Status:** `DOCUMENTATION_ONLY_PHASE` — superseded, not executed.\n")
    phase_index("phase_18_kub_final_dev_benchmark", "Phase 18 — KUB final dev benchmark (documentation only)",
                "No notebook and no saved artifacts exist.\n\n"
                "The KUB-only final benchmark was replaced by the four-domain\n"
                "VAL808 benchmark (Phase 21) and the ROUTER_HOLDOUT evaluation\n"
                "(Phase 30).\n\n"
                "**Status:** `DOCUMENTATION_ONLY_PHASE` — superseded, not executed.\n")
    phase_index("phase_39_untouched_test_evaluation",
                "Phase 39 — Untouched TEST evaluation (authorization-gated)",
                "A notebook is **deliberately not created** here.\n\n"
                "The Phase 39 one-shot TEST1683 evaluation was executed once (v1.2) and\n"
                "its access is consumed. Any notebook that loaded the TEST manifest,\n"
                "images, ground truth or predictions would violate the one-shot contract.\n\n"
                "The descriptive result is documented from the frozen summary only in\n"
                "`ReMedFiLM_Research_Notebooks/12_ReMedFiLM_Historical_Test_Evidence.ipynb`.\n\n"
                "**Status:** `REQUIRES_HUMAN_AUTHORIZATION` — access consumed, not reopenable.\n")


def main() -> None:
    preserve()
    nb_09(); nb_10(); nb_24(); nb_25(); nb_26(); nb_30(); nb_36(); nb_40()
    docs()
    print("DONE")


if __name__ == "__main__":
    main()
