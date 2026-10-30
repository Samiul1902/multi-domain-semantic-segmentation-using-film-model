"""Build + execute the Phase-20 reviewer notebook.

    notebooks/phasewise/phase_20_multidomain_baselines/phase20_shared_global_unetpp_baseline.ipynb

The notebook imports the reusable module (src.analysis.phase20_baseline) so its
tables are byte-identical to the driver's artifacts. It reads the produced
artifacts and figures, renders every required section, and asserts the Phase-20
invariants. No training, no inference, no TEST.

SHA determinism: deterministic cell ids + stripped execution timestamps +
coalesced stream outputs, so repeated builds converge.

Run:
    D:\\Softfors\\jup\\.venv\\Scripts\\python.exe scripts/notebooks/build_phase20_notebook.py
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
NB_PATH = (ROOT / "notebooks/phasewise/phase_20_multidomain_baselines"
           / "phase20_shared_global_unetpp_baseline.ipynb")
NB_PATH.parent.mkdir(parents=True, exist_ok=True)

md = lambda s: nbformat.v4.new_markdown_cell(s.strip("\n"))          # noqa: E731
code = lambda s: nbformat.v4.new_code_cell(s.strip("\n"))            # noqa: E731

cells = []

# --- 1 ---------------------------------------------------------------------
cells.append(md("""
# Phase 20 — Shared Four-Domain Global Baseline (single frozen UNet++)

**Stage B: Multi-Domain Scaling — first scientific training phase**

**Project:** RA-MedFiLM-Seg++ (Regional Scale-Aware Feature Interleaving Multi-Domain Medical Segmentation)
**Target venue:** Q1 / A* peer-reviewed medical computer vision

---

## 1. Title / scope / governance

| Item | Value |
|---|---|
| Phase | 20 |
| Stage | Stage B: Multi-Domain Scaling |
| Title | Shared Multi-Domain Global Baseline |
| Architecture | **UNet++** (one shared parameter set, no FiLM, no regional module) |
| Experiment | `phase20_shared_unetpp_fourdomain_seed42_clean_v3` |
| Domains | ISIC (0), BUSI (1), KVASIR (2), KUB (3) |
| Manifest | `manifests/phase4_v3` (CANONICAL_ACTIVE_DEVELOPMENT) |
| Cohorts read | TRAIN and VAL only |
| TEST | `CLOSED` — 0 image reads, 0 mask reads, 0 inference, 0 visualizations |
| Model training in this phase | **YES — exactly one logical run** |

**Explicitly excluded from this phase:** FiLM, task embeddings, domain embeddings, any
regional mechanism, the Phase-13/H3 localizer, the Phase-14 refiner, Oracle ROIs,
proposal heatmaps, regional crops, routing, dataset-specific decoders or heads.
`task_id` is used for **sampling and reporting only** and is never a model input.
"""))

cells.append(code("""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from IPython.display import display, Image, Markdown

pd.set_option("display.width", 260)
pd.set_option("display.max_columns", 80)
pd.set_option("display.max_rows", 400)


def find_root():
    \"\"\"Repository-root discovery that does not depend on one shell, OS or hardcoded path.\"\"\"
    p = Path.cwd()
    for _ in range(6):
        if (p / "manifests").is_dir() and (p / "reports").is_dir() and (p / "src").is_dir():
            return p
        p = p.parent
    return Path("D:/Softfors/jup")


ROOT = find_root()
AUD = ROOT / "reports/audits"
TAB = ROOT / "reports/tables"
FIG = ROOT / "reports/figures/phase20_multidomain_baseline"
EXP_ID = "phase20_shared_unetpp_fourdomain_seed42_clean_v3"
EXP = ROOT / "experiments" / EXP_ID
CKP = ROOT / "checkpoints" / EXP_ID


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def jload(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


print("ROOT:", ROOT)
print("experiment:", EXP_ID)
"""))

# --- 2 ---------------------------------------------------------------------
cells.append(md("""
## 2. Phase-19 handoff

Phase 19 completed the prospective four-domain harmonization preparation. Phase 20
inherits its frozen contracts rather than re-deriving them. Every inherited artifact is
SHA-bound below, and the four-domain task mapping and development populations are
re-asserted from the manifests.
"""))

cells.append(code("""
AUTHORITY = {
    "stage_b_authorization": "reports/audits/stage_b_phase19_authorization.json",
    "stage_b_governance_state": "reports/audits/stage_b_governance_state.json",
    "phase19_protocol": "reports/audits/phase19_multidomain_harmonization_protocol.json",
    "phase19_task_id_registry": "reports/tables/phase19_task_id_registry.csv",
    "phase19_harmonized_schema": "reports/tables/phase19_harmonized_schema.csv",
    "phase19_phase20_entry_criteria": "reports/tables/phase19_phase20_entry_criteria.csv",
    "phase19_preprocessing_contract": "reports/audits/phase19_preprocessing_contract.json",
    "phase19_evaluation_contract": "reports/audits/phase19_evaluation_contract.json",
    "phase19_legacy_evidence_reuse_map": "reports/audits/phase19_legacy_evidence_reuse_map.json",
    "phase19_leakage_safeguards": "reports/audits/phase19_leakage_safeguards.json",
    "phase19_loader_smoke_test": "reports/audits/phase19_loader_smoke_test.json",
}
auth_rows = [{"artifact": k, "path": v, "sha256": sha256_file(ROOT / v)[:32] + "…"}
             for k, v in AUTHORITY.items()]
display(pd.DataFrame(auth_rows))

binding = jload(AUD / "phase20_phase19_authority_binding.json")
print("authority checks all passed:", binding["all_checks_passed"])
display(pd.DataFrame(sorted(binding["checks"].items()), columns=["check", "pass"]))
display(pd.DataFrame([binding["observed_task_id_registry"]]).T.rename(columns={0: "task_id"}))
display(pd.DataFrame(binding["observed_populations"]["TRAIN"], index=["TRAIN n"]).T
        .join(pd.DataFrame(binding["observed_populations"]["VAL"], index=["VAL n"]).T))
"""))

# --- 3 ---------------------------------------------------------------------
cells.append(md("""
## 3. Phase-20 scientific question

> **How well can ONE shared conventional segmentation model represent all four medical
> domains under the harmonized Stage-B data contract, WITHOUT task-conditioned FiLM and
> WITHOUT the regional mechanism?**

This baseline is the **prospective reference** for Phase 21 (Global MedFiLM). Phase 21
will ask whether task-conditioned FiLM improves *this* baseline. Phase 20 does **not**
attempt to prove MedFiLM and does **not** compare against Phase-21 results, which do not
exist yet. Keeping that causal comparison clean is the point of freezing this phase first.
"""))

# --- 4 ---------------------------------------------------------------------
cells.append(md("""
## 4. Legacy baseline evidence review

Historical conventional baselines that actually exist in the tested projects. Every value
below is labelled **`LEGACY_PRIOR_EVIDENCE__NOT_CURRENT_PHASE20_RESULT`** and must never
be compared numerically against Phase-20 results.
"""))

cells.append(code("""
legacy = jload(AUD / "phase20_legacy_baseline_selection_evidence.json")
print("evidence label:", legacy["evidence_label"])
print()
print("Finding — legacy KUB-bearing shared baseline:",
      legacy["finding_no_legacy_four_domain_shared_baseline"]["kub_bearing_shared_baseline_found"])
display(Markdown(legacy["finding_no_legacy_four_domain_shared_baseline"]["statement"]))

comp = legacy["same_repository_clean_v3_conventional_comparison"]
display(Markdown(f"**Same-repository clean-v3 conventional comparison** — {comp['scope']}"))
display(pd.DataFrame(comp["results"])[["architecture", "experiment_id", "params",
                                       "best_epoch", "best_val_macro_dice",
                                       "final_epoch", "stop_reason"]])
print("ranking:", comp["ranking_by_best_val_macro_dice"])
print("strongest:", comp["strongest"], "=", comp["strongest_value"],
      "| margin over next:", comp["margin_over_next"])
display(Markdown("**Legacy multi-domain projects**"))
display(pd.DataFrame(legacy["legacy_projects"])[
    ["project", "domain_count", "includes_kub", "baselines",
     "implementation_availability", "reuse_recommendation"]])
"""))

# --- 5 ---------------------------------------------------------------------
cells.append(md("""
## 5. Why ONE baseline instead of repeating five

The user's tested projects already contain extensive four-domain baseline experiments. The
task is therefore to **freeze one strong conventional baseline**, not to re-run an
architecture sweep. Repeating a five-model current experiment would spend hours confirming
what the legacy work already established, and would delay the Phase-21 reference.

The selection uses prior evidence only. `current_phase20_results_used_for_selection` is
`false`, and the freeze is verified below to predate training.
"""))

# --- 6 ---------------------------------------------------------------------
cells.append(md("""
## 6. Architecture freeze
"""))

cells.append(code("""
freeze = jload(AUD / "phase20_baseline_architecture_freeze.json")
display(pd.DataFrame([
    {"field": "frozen_architecture", "value": freeze["frozen_architecture"]},
    {"field": "repository_implementation", "value": freeze["repository_implementation"]},
    {"field": "architecture_descriptor", "value": freeze["architecture_descriptor"]},
    {"field": "selection_basis", "value": freeze["selection_basis"]},
    {"field": "selection_time", "value": freeze["selection_time"]},
    {"field": "current_phase20_results_used_for_selection",
     "value": freeze["current_phase20_results_used_for_selection"]},
    {"field": "evidence_label", "value": freeze["selection_evidence_summary"]["evidence_label"]},
]))
display(pd.DataFrame([{"forbidden module": m, "present": p}
                      for m, p in zip(freeze["model_contract"]["forbidden_modules"],
                                      freeze["model_contract"]["forbidden_modules_present"])]))
display(Markdown("**Rationale**"))
for r in freeze["rationale"]:
    display(Markdown(f"- {r}"))
assert freeze["selection_time"] == "PRE_TRAINING"
assert freeze["current_phase20_results_used_for_selection"] is False
assert freeze["model_contract"]["forbidden_modules_present"] == []
"""))

# --- 7 ---------------------------------------------------------------------
cells.append(md("""
## 7. Cross-domain duplicate audit

Phase 19 explicitly left one issue unresolved: cross-domain near-duplicate detection across
the newly combined four-domain pool. Phase 20 resolves it **before** training, using TRAIN
and VAL image content only.

Method: exact `sha256` of the raw image bytes, plus the **already-approved repository**
perceptual hash (32x32 L, 2-D DCT, top-left 8x8, median threshold, 64-bit) with the frozen
Hamming distance <= 6 candidate threshold.

**Blocking rule (declared before interpretation):** block training if ANY TRAIN<->VAL pair
is identical by content sha256 or at Hamming distance 0.
"""))

cells.append(code("""
dup = jload(AUD / "phase20_cross_domain_duplicate_audit.json")
print("verdict:", dup["verdict"])
print("pairs compared:", dup["populations"]["compared_pairs"])
print("candidate pairs:", dup["n_candidate_pairs"],
      "| blocking pairs:", dup["n_blocking_pairs"],
      "| exact sha matches:", dup["n_exact_content_sha_matches_train_val"],
      "| high-attention:", dup["candidates_high_attention"])
rows = []
for pair, v in dup["train_val_pairwise"].items():
    rows.append({"pair": pair, "kind": v["kind"], "pairs_compared": v["n_pairs_compared"],
                 "d=0": v["n_hamming_0"], "d1-2": v["n_hamming_1_2"],
                 "d3-4": v["n_hamming_3_4"], "d5-6": v["n_hamming_5_6"],
                 "min_hamming": v["min_hamming"]})
display(pd.DataFrame(rows))
display(Markdown("**Within-split descriptive duplicate counts**"))
display(pd.DataFrame(dup["within_split"]))
cand = pd.read_csv(TAB / "phase20_cross_domain_duplicate_candidates.csv")
if len(cand):
    display(Markdown(f"Candidate pairs ({len(cand)}), all within-dataset, all reported only:"))
    display(cand[["dataset_train", "dataset_val", "pair_kind", "hamming_distance",
                  "classification", "same_patient_id"]].head(40))
assert dup["training_may_start"] is True
assert dup["n_blocking_pairs"] == 0
"""))

# --- 8 ---------------------------------------------------------------------
cells.append(md("""
## 8. Phase-20 entry gate

Every Phase-19 Phase-20 entry criterion is evaluated independently against authoritative
artifacts rather than trusted from the Phase-19 `met` column alone.
"""))

cells.append(code("""
gate = jload(AUD / "phase20_entry_gate.json")
display(pd.DataFrame(gate["criteria"])[
    ["criterion_id", "criterion", "verdict", "blocking", "observed_state"]])
print("entry gate verdict:", gate["phase20_entry_gate_verdict"],
      "| hard fails:", gate["hard_fail_ids"])
print("residual criteria resolved by the Phase-20 audit:",
      gate["residual_criteria_resolved_by_phase20"])
pre = jload(AUD / "phase20_pre_execution_check.json")
print()
print("pre-execution check:", f"{pre['n_passed']}/{pre['n_checks']} PASS",
      "| training authorized:", pre["training_authorized"])
display(pd.DataFrame([{"check": k, **v} for k, v in pre["checks"].items()]))
assert gate["phase20_entry_gate_verdict"] == "PASS"
assert pre["all_checks_passed"] is True
"""))

# --- 9 ---------------------------------------------------------------------
cells.append(md("""
## 9. Dataset populations
"""))

cells.append(code("""
protocol = jload(AUD / "phase20_shared_global_baseline_protocol.json")
pops = protocol["dataset_populations"]
pop_df = pd.DataFrame({
    "TRAIN": pops["TRAIN"], "VAL": pops["VAL"],
})
pop_df.loc["TOTAL"] = [pops["TRAIN_total"], pops["VAL_total"]]
pop_df["TRAIN_share"] = (pop_df["TRAIN"] / pops["TRAIN_total"]).round(4)
display(pop_df)
display(pd.DataFrame([pops["task_ids"]]).T.rename(columns={0: "task_id"}))
print("protocol status:", protocol["status"])
"""))

# --- 10 --------------------------------------------------------------------
cells.append(md("""
## 10. Input / preprocessing contract

Phase 19 preserved both deterministic 1-channel and 3-channel converters, deferring the
architecture-wide decision to Phase 24. For Phase 20 only, an **operational** baseline
input contract is frozen: **3-channel** input, labelled
`PHASE20_BASELINE_OPERATIONAL_INPUT_ONLY`. It is **not** the final Phase-24 policy.
"""))

cells.append(code("""
pre_c = jload(AUD / "phase19_preprocessing_contract.json")
display(pd.DataFrame([
    {"item": "channel_policy", "value": protocol["input_representation"]["channel_policy"]},
    {"item": "contract label", "value": protocol["input_representation"]["contract_label"]},
    {"item": "not final Phase-24 policy",
     "value": protocol["input_representation"]["not_the_final_phase24_policy"]},
    {"item": "input_resolution", "value": protocol["input_resolution"]},
    {"item": "spatial policy", "value": pre_c["spatial"]["policy"]},
    {"item": "scale formula", "value": pre_c["spatial"]["scale_formula"]},
    {"item": "image resample", "value": pre_c["spatial"]["image_resample"]},
    {"item": "mask resample", "value": pre_c["spatial"]["mask_resample"]},
    {"item": "foreground rule", "value": pre_c["mask"]["foreground_rule"]},
    {"item": "intensity normalization", "value": pre_c["image"]["intensity_normalization"]},
]))
display(Markdown("**Model input excludes** (governance):"))
display(pd.DataFrame({"excluded from model input":
                      protocol["input_representation"]["model_input_excludes"]}))
display(Markdown("**Resolution decision**"))
display(pd.DataFrame([{"frozen": protocol["resolution_decision"]["frozen"],
                       "decision_time": protocol["resolution_decision"]["decision_time"],
                       "no_resolution_search": protocol["resolution_decision"]["no_resolution_search"]}]))
for e in protocol["resolution_decision"]["evidence"]:
    display(Markdown(f"- {e}"))
"""))

# --- 11 --------------------------------------------------------------------
cells.append(md("""
## 11. Domain-balanced sampling

TRAIN is strongly imbalanced: ISIC 2556 (43.8%), KUB 1978 (33.9%), KVASIR 696 (11.9%),
BUSI 602 (10.3%). ISIC alone is 4.2x BUSI. A plain shuffle would let ISIC and KUB dominate.
Phase 20 freezes a **domain-balanced** weighted sampler so each domain contributes an equal
expected share of every epoch.

`task_id` / `dataset` are used for **sampling only** and are never fed to the network.
"""))

cells.append(code("""
samp = jload(AUD / "phase20_sampling_policy_audit.json")
print("policy:", samp["policy_id"])
print(samp["policy"])
rows = []
for d, v in samp["expected_balanced_proportions"].items():
    e = samp["empirical_check"]["per_domain"][d]
    rows.append({"dataset": d, "pool_size": v["dataset_size"],
                 "pool_share": v["dataset_share_of_pool"],
                 "expected_sampling_proportion": v["expected_sampling_proportion"],
                 "empirical_proportion": e["proportion"], "empirical_count": e["count"]})
display(pd.DataFrame(rows))
display(Markdown(f"Effect: {samp['effect']}"))
print("governance:", samp["governance"])
"""))

# --- 12 --------------------------------------------------------------------
cells.append(md("""
## 12. Model architecture

One shared parameter set across all four domains. Single 1-channel binary logit output.
"""))

cells.append(code("""
from src.models.unetpp import UNetPlusPlus

model = UNetPlusPlus(in_channels=3, out_channels=1, base_channels=32)
n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"UNetPlusPlus params = {n_params:,} | in_channels=3 | out_channels=1 | base_channels=32")
mods = dict(model.named_modules())
forbidden = [n for n in mods
             if any(k in n.lower() for k in ("film", "localizer", "proposal", "roi",
                                             "regional", "task_embed", "domain_embed", "routing"))]
print("forbidden modules present:", forbidden)
print("output head:", model.head)
print("shared across domains:", True, "| one parameter set:", True)
assert not forbidden
assert model.head.out_channels == 1
"""))

# --- 13 --------------------------------------------------------------------
cells.append(md("""
## 13. Training configuration (frozen before training)

The configuration reuses the proven conventional clean-v3 training contract already
verified in this repository (Phase 9 / Phase 10 configs) rather than inventing new values.
No loss / optimizer / LR / scheduler sweep, no second seed.
"""))

cells.append(code("""
cfg_rows = [
    ("experiment_id", protocol["experiment_id"]),
    ("architecture", protocol["architecture"]),
    ("input channel policy", protocol["input_representation"]["channel_policy"]),
    ("input resolution", protocol["input_resolution"]),
    ("loss", f"{protocol['loss']['name']} (bce {protocol['loss']['bce_weight']} / "
             f"dice {protocol['loss']['dice_weight']}, eps {protocol['loss']['dice_epsilon']})"),
    ("optimizer", f"{protocol['optimizer']['name']} lr={protocol['learning_rate']} "
                  f"wd={protocol['weight_decay']}"),
    ("scheduler", f"{protocol['scheduler']['name']} T_max={protocol['scheduler']['T_max']} "
                  f"({protocol['scheduler']['step']})"),
    ("batch size", protocol["batch_size"]),
    ("eval batch size", protocol["eval_batch_size"]),
    ("num workers", protocol["num_workers"]),
    ("AMP", protocol["amp"]),
    ("seed", protocol["seed"]),
    ("max epochs", protocol["max_epochs"]),
    ("early stopping", f"patience {protocol['early_stopping']['patience']}, "
                       f"ties count as bad = {protocol['early_stopping']['ties_count_as_bad_epochs']}"),
    ("checkpoint metric", protocol["checkpoint_selection"]["metric"]),
    ("checkpoint tie-break", protocol["checkpoint_selection"]["tie_break"]),
    ("threshold", protocol["evaluation_metrics"]["threshold"]),
    ("logical runs authorized", protocol["single_run_authorization"]["logical_runs_authorized"]),
]
display(pd.DataFrame(cfg_rows, columns=["field", "value"]))
display(Markdown("**Code SHAs bound in the protocol**"))
display(pd.DataFrame(sorted(protocol["code_shas"].items(), key=lambda kv: kv[0]),
                     columns=["file", "sha256"]))
"""))

# --- 14 --------------------------------------------------------------------
cells.append(md("""
## 14. COMPLETE epoch table

One row per completed epoch. No epoch row is omitted, and the saved CSV is authoritative.
"""))

cells.append(code("""
history = pd.read_csv(EXP / "history.csv")
closure = jload(AUD / "phase20_training_closure.json")
print(f"epoch rows: {len(history)}")
display(history)
"""))

# --- 15-21 ----------------------------------------------------------------
cells.append(md("""
## 15-21. Training curves, early stopping, timing and best-checkpoint progression

Every curve is also saved under `reports/figures/phase20_multidomain_baseline/` and embedded
here, so the saved PNG is not the only copy.
"""))

cells.append(code("""
from src.analysis import phase20_baseline as pb

train_figs = pb.build_training_figures(history, closure)
for name, path in train_figs.items():
    display(Markdown(f"**{name}** — `{path.relative_to(ROOT)}`"))
    display(Image(filename=str(path)))
"""))

# --- 22 --------------------------------------------------------------------
cells.append(md("""
## 22. Resume / interruption history

Durability on this host comes from **resumability**, not detachment: the launching session's
process tree is torn down periodically, so the run is relaunched with `--resume` and continues
the SAME logical run. Resume is bit-exact **by construction** — the data order and every
stochastic augmentation for epoch *k* derive from `derive_epoch_seed(seed, k)`, so epoch *k*
never depends on how many epochs ran before it. No second independent run was ever started.
"""))

cells.append(code("""
from src.data.domain_balanced_sampler import derive_epoch_seed

print("resume events recorded in the checkpoint chain:", closure["resume_count"])
display(pd.DataFrame(closure["resume_events"]) if closure["resume_events"]
        else Markdown("_no interruption occurred during this run_"))
print("logical runs:", closure["logical_runs"],
      "| independent duplicate runs:", closure["independent_duplicate_runs"])
print("bit-exactness of the resume rule:")
display(pd.DataFrame([{"epoch": e, "derived_seed": derive_epoch_seed(42, e)}
                      for e in (1, 2, 3, 4, 5)]))
assert closure["independent_duplicate_runs"] == 0
"""))

# --- 23 --------------------------------------------------------------------
cells.append(md("""
## 23. Checkpoint-selection replay (disk only, no inference)

The frozen rule `phase20_macro_domain_mean_dice_v1` is replayed over the saved history and
must agree with both the stored best epoch and the epoch inside `best.pt`.
"""))

cells.append(code("""
replay = jload(AUD / "phase20_checkpoint_selection_replay.json")
display(pd.DataFrame([
    {"field": "selection_rule_id", "value": replay["selection_rule_id"]},
    {"field": "selection_metric", "value": replay["selection_metric"]},
    {"field": "tie_break", "value": replay["tie_break"]},
    {"field": "history_selected_epoch", "value": replay["history_selected_epoch"]},
    {"field": "stored_best_epoch", "value": replay["stored_best_epoch"]},
    {"field": "best_pt_epoch", "value": replay["best_pt_epoch"]},
    {"field": "best_pt_macro_domain_dice", "value": replay["best_pt_macro_domain_dice"]},
    {"field": "n_epochs_evaluated", "value": replay["n_epochs_evaluated"]},
    {"field": "n_improvements", "value": replay["n_improvements"]},
    {"field": "verdict", "value": replay["verdict"]},
]))
display(pd.DataFrame([{"check": k, "pass": v} for k, v in replay["checks"].items()]))
trace = pd.DataFrame(replay["selection_trace"])
display(trace[trace["improved"]])
assert replay["verdict"] == "PHASE20_CHECKPOINT_SELECTION_REPLAY_PASS"
"""))

# --- 24 --------------------------------------------------------------------
cells.append(md("""
## 24. Complete VAL evaluation

Exactly **one** canonical VAL forward pass over the 808 VAL samples of the four domains,
using `best.pt`. No TEST.
"""))

cells.append(code("""
val_eval = jload(AUD / "phase20_val_evaluation.json")
pred_man = jload(AUD / "phase20_prediction_manifest.json")
display(pd.DataFrame([
    {"field": "canonical_val_inference_runs", "value": val_eval["canonical_val_inference_runs"]},
    {"field": "val_population", "value": val_eval["val_population"]},
    {"field": "samples_evaluated", "value": val_eval["samples_evaluated"]},
    {"field": "domains_evaluated", "value": ", ".join(val_eval["domains_evaluated"])},
    {"field": "checkpoint_sha256", "value": val_eval["checkpoint_sha256"][:32] + "…"},
    {"field": "threshold", "value": val_eval["threshold"]},
    {"field": "prob maps persisted", "value": val_eval["prob_maps_persisted"]},
    {"field": "binary predictions persisted", "value": val_eval["binary_predictions_persisted"]},
]))
display(Markdown("**Prediction persistence** — this is the deliberate lesson from earlier "
                 "phases, where the absence of saved pixel predictions forced safe replays."))
display(pd.DataFrame([
    {"item": "format", "value": pred_man["storage"]["format"]},
    {"item": "prob dtype", "value": pred_man["storage"]["prob_dtype"]},
    {"item": "pred dtype", "value": pred_man["storage"]["pred_dtype"]},
    {"item": "npz keys", "value": ", ".join(pred_man["storage"].get("npz_keys", [])) or
                                 "prob, pred, gt"},
    {"item": "prediction root", "value": pred_man["prediction_root"]},
    {"item": "GT reference scheme", "value": pred_man["gt_reference_scheme"]},
    {"item": "allows later phases to avoid replay", "value": pred_man["allows_future_phases_to_avoid_replay"]},
]))
display(pd.DataFrame([pred_man["per_domain_counts"]]).T.rename(columns={0: "predictions"}))
"""))

# --- 25 --------------------------------------------------------------------
cells.append(md("""
## 25. Per-domain metric table (publication style)

`MACRO_DOMAIN` is the unweighted mean of the four per-domain per-image macro values.
`POOLED_DESCRIPTIVE` pools raw pixel counts and is **descriptive only** — it is never the
sole scientific summary, because pooled volume would let ISIC and KUB decide.
"""))

cells.append(code("""
domain_table = pd.read_csv(TAB / "phase20_domain_performance.csv")
show_cols = ["row_type", "dataset", "n", "dice", "iou", "precision", "recall",
             "specificity", "balanced_accuracy", "mcc", "hd95", "assd", "surface_dice",
             "roc_auc", "pr_auc", "brier", "ece", "mce",
             "dice_ci_low", "dice_ci_high"]
display(domain_table[show_cols])
display(Markdown("**Bootstrap 95% CI (deterministic: n_boot=2000, seed=42, percentile)**"))
display(pd.read_csv(TAB / "phase20_domain_bootstrap_ci.csv"))
"""))

# --- 26 --------------------------------------------------------------------
cells.append(md("""
## 26. Complete per-image table

The authoritative saved CSV holds **all 808 rows**. Only a preview is shown here so the
notebook stays readable; the full table is on disk and SHA-bound.
"""))

cells.append(code("""
per_image = pd.read_csv(TAB / "phase20_per_image_val_metrics.csv")
print(f"rows in authoritative CSV: {len(per_image)}")
print("columns:", ", ".join(per_image.columns))
display(per_image.head(12))
display(per_image.tail(12))
print("empty GT:", int(per_image["gt_empty"].sum()),
      "| empty prediction:", int(per_image["pred_empty"].sum()))
assert len(per_image) == 808
"""))

# --- 27 --------------------------------------------------------------------
cells.append(md("""
## 27. Confusion matrices

Raw pixel confusion and row-normalized confusion per domain, plus a pooled matrix that is
descriptive only.
"""))

cells.append(code("""
conf_df = pd.read_csv(TAB / "phase20_confusion_matrices.csv")
display(conf_df[["scope", "tp", "tn", "fp", "fn", "total", "gt_foreground", "gt_background",
                 "row_norm_gt_fg_tp", "row_norm_gt_fg_fn",
                 "row_norm_gt_bg_fp", "row_norm_gt_bg_tn"]])
conf_json = jload(AUD / "phase20_confusion_matrices.json")
for scope, m in conf_json["matrices"].items():
    display(Markdown(f"**{scope}** — raw `{m['raw']}` | row-normalized "
                     f"`[[{m['row_normalized'][0][0]:.4f}, {m['row_normalized'][0][1]:.4f}], "
                     f"[{m['row_normalized'][1][0]:.4f}, {m['row_normalized'][1][1]:.4f}]]`"))
display(Markdown("Rows = GT (foreground, background); columns = prediction "
                 "(foreground, background)."))
"""))

# --- 28-30 ----------------------------------------------------------------
cells.append(md("""
## 28-30. Boundary metrics, calibration metrics, uncertainty / bootstrap CIs
"""))

cells.append(code("""
calib = pd.read_csv(TAB / "phase20_calibration_ranking.csv")
display(Markdown("**Boundary metrics** (units = pixels; no physical spacing metadata exists)"))
display(domain_table[["row_type", "dataset", "n", "hd95", "assd", "surface_dice",
                      "hd95_valid_n", "surface_dice_valid_n"]])
display(Markdown("**Calibration + ranking** on a deterministic pixel subsample "
                 f"(stride {pb.CALIBRATION_STRIDE}, {pb.CALIBRATION_BINS} bins)"))
display(calib)
display(Markdown("**Uncertainty — deterministic percentile bootstrap** "
                 "(n_boot 2000, seed 42, alpha 0.05, resampling unit = image)"))
display(pd.read_csv(TAB / "phase20_domain_bootstrap_ci.csv")[
    ["scope", "metric", "estimate", "ci_low", "ci_high", "n", "n_boot", "seed", "resampling_unit"]])
"""))

cells.append(code("""
result_figs = pb.build_result_figures(domain_table, conf_json["matrices"], calib)
for name, path in result_figs.items():
    display(Markdown(f"**{name}** — `{path.relative_to(ROOT)}`"))
    display(Image(filename=str(path)))
"""))

# --- 31 --------------------------------------------------------------------
cells.append(md("""
## 31. KUB subgroup analysis

KUB is the reporting domain with known tiny-object difficulty. Subgroups come from valid
Phase-19 reporting metadata and are **reporting only** — they are never fed to the model and
are never treated as segmentation classes. Size strata use the frozen clean-v3 taxonomy
`kub_size_clean_v3_v1` (`component_ratio = component_pixels / (native_h * native_w)`,
FULL_FIELD only; ROI crops are `ROI_NOT_PRIMARY_BINNED`).
"""))

cells.append(code("""
display(Markdown("**KUB overall + native-category subgroups (reporting only)**"))
display(pd.read_csv(TAB / "phase20_kub_subgroup_analysis.csv"))
display(Markdown("**KUB size-stratified performance (frozen clean-v3 taxonomy, descriptive)**"))
display(pd.read_csv(TAB / "phase20_kub_size_stratification.csv"))
"""))

# --- 32 --------------------------------------------------------------------
cells.append(md("""
## 32. 64-case detailed prediction gallery

**Selection is deterministic and prediction-independent**: within each domain, VAL samples
are sorted by `sample_id` and an evenly spaced set of 16 indices is taken — 16 per domain,
**64 cases total**. The rule depends only on the manifest, so the same 64 sample IDs can be
reused in Phase 21 for a like-for-like comparison. Nothing is cherry-picked.

Each case shows 9 panels: A native image, B GT mask, C GT contour, D model input,
E probability map, F thresholded prediction, G TP/FP/FN error map, H prediction overlay,
I GT-vs-prediction contour overlay — plus per-case Dice / IoU / precision / recall.

Pages are paginated 4 cases per page so no panel becomes unreadable.
"""))

cells.append(code("""
sel = pd.read_csv(TAB / "phase20_gallery_selection.csv")
print("cases selected:", len(sel),
      "| per domain:", {k: int(v) for k, v in sel.groupby("dataset").size().items()})
print("selection rule:", sel["selection_rule"].iloc[0],
      "| prediction-dependent:", bool(sel["prediction_dependent"].any()))
display(sel.groupby("dataset")["sample_id"].apply(list).to_frame("selected sample_ids"))
vis = jload(AUD / "phase20_visualization_evidence.json")
assert len(sel) == 64
"""))

cells.append(code("""
for i, page in enumerate(sorted(FIG.glob("gallery_page_*.png"))):
    display(Markdown(f"**Gallery page {i+1}** — `{page.relative_to(ROOT)}`"))
    display(Image(filename=str(page)))
"""))

# --- 33 --------------------------------------------------------------------
cells.append(md("""
## 33. Success / failure analysis

Failure evidence is shown alongside success evidence. This analysis is **descriptive** and
does not alter the frozen checkpoint.
"""))

cells.append(code("""
sf = jload(AUD / "phase20_visualization_evidence.json")["success_failure_figures"]
for name, rel in sf.items():
    display(Markdown(f"**{name}** — `{rel}`"))
    display(Image(filename=str(ROOT / rel)))

per_image = pd.read_csv(TAB / "phase20_per_image_val_metrics.csv")
display(Markdown("**Per-domain Dice quantiles**"))
display(per_image.groupby("dataset")["dice"].describe()[["count", "mean", "std", "min",
                                                         "25%", "50%", "75%", "max"]])
display(Markdown("**Domain-specific failure patterns: empty predictions and FP/FN balance**"))
fails = per_image.assign(
    fp_ratio=per_image["fp"] / (per_image["fp"] + per_image["fn"]).replace(0, np.nan)
).groupby("dataset").agg(
    n=("sample_id", "size"),
    empty_prediction=("pred_empty", "sum"),
    empty_gt=("gt_empty", "sum"),
    mean_fp_ratio=("fp_ratio", "mean"),
    dice_lt_0_5=("dice", lambda s: int((s < 0.5).sum())),
)
display(fails)
"""))

# --- 34 --------------------------------------------------------------------
cells.append(md("""
## 34. Artifact provenance
"""))

cells.append(code("""
prov_paths = [
    "reports/audits/phase20_phase19_authority_binding.json",
    "reports/audits/phase20_entry_gate.json",
    "reports/audits/phase20_cross_domain_duplicate_audit.json",
    "reports/audits/phase20_legacy_baseline_selection_evidence.json",
    "reports/audits/phase20_baseline_architecture_freeze.json",
    "reports/audits/phase20_sampling_policy_audit.json",
    "reports/audits/phase20_shared_global_baseline_protocol.json",
    "reports/audits/phase20_pre_execution_check.json",
    "reports/audits/phase20_training_closure.json",
    "reports/audits/phase20_checkpoint_selection_replay.json",
    "reports/audits/phase20_val_evaluation.json",
    "reports/audits/phase20_prediction_manifest.json",
    "reports/audits/phase20_confusion_matrices.json",
    "reports/audits/phase20_visualization_evidence.json",
    "reports/audits/phase20_phase21_entry_criteria.json",
    "reports/tables/phase20_per_image_val_metrics.csv",
    "reports/tables/phase20_domain_performance.csv",
    "reports/tables/phase20_confusion_matrices.csv",
    "reports/tables/phase20_calibration_ranking.csv",
    "reports/tables/phase20_domain_bootstrap_ci.csv",
    "reports/tables/phase20_kub_subgroup_analysis.csv",
    "reports/tables/phase20_kub_size_stratification.csv",
    "reports/tables/phase20_gallery_selection.csv",
    "reports/tables/phase20_prediction_manifest.csv",
    f"experiments/{EXP_ID}/history.csv",
    f"checkpoints/{EXP_ID}/best.pt",
    f"checkpoints/{EXP_ID}/latest.pt",
]
display(pd.DataFrame([{"artifact": p, "sha256": sha256_file(ROOT / p)[:40] + "…",
                       "bytes": (ROOT / p).stat().st_size} for p in prov_paths]))
"""))

# --- 35 --------------------------------------------------------------------
cells.append(md("""
## 35. Known limitations

1. **Single seed.** One run, seed 42. Three-seed reproducibility belongs to Phase 29.
2. **No architecture comparison in this phase.** UNet++ was frozen from prior evidence; it
   is not compared here against U-Net / Attention U-Net / DeepLabV3+ on the four-domain pool.
3. **Operational input contract.** 3-channel input is a Phase-20 baseline choice, not the
   final Phase-24 architecture policy.
4. **Resolution frozen without a search.** 512 px was chosen prospectively from prior evidence
   and feasibility, not tuned.
5. **Boundary metrics are in pixels.** No physical pixel-spacing metadata exists, so HD95 /
   ASSD / surface Dice are not in millimetres.
6. **Calibration and ranking metrics use a deterministic pixel subsample**
   (stride 4), not every pixel.
7. **Pooled metrics are descriptive.** Macro-domain is the scientific summary.
8. **No TEST and no external validation.** Phase 39 owns the final TEST evaluation.
9. **Domain-balanced sampling changes the effective TRAIN distribution** (each domain ~25%),
   which is intentional but means epoch composition is not the raw manifest composition.
10. **Cross-domain near-duplicate detection used the approved 64-bit pHash** with the frozen
    Hamming <= 6 candidate threshold; pairs at 1-6 are reported, not adjudicated pixel-by-pixel.
"""))

# --- 36 --------------------------------------------------------------------
cells.append(md("""
## 36. Comparison to LEGACY prior values (historical, non-current)

The values below are context for why UNet++ was chosen. They are
**`LEGACY_PRIOR_EVIDENCE__NOT_CURRENT_PHASE20_RESULT`**: different splits, different
domain sets, and in the legacy multi-domain case a tuned threshold. They must **not** be read
as a Phase-20 benchmark and Phase-20 numbers must not be read as an improvement over them.
"""))

cells.append(code("""
legacy = jload(AUD / "phase20_legacy_baseline_selection_evidence.json")
display(Markdown("**Same-repository clean-v3 KUB-only conventional comparison (historical)**"))
display(pd.DataFrame(legacy["same_repository_clean_v3_conventional_comparison"]["results"])[
    ["architecture", "best_epoch", "best_val_macro_dice", "stop_reason"]])
display(Markdown("**Legacy three-domain shared baselines (historical, superseded pipeline)**"))
legacy_rows = []
for p in legacy["legacy_projects"]:
    if p.get("historical_validation_result", {}).get("U-Net"):
        for model, vals in p["historical_validation_result"].items():
            if isinstance(vals, dict) and "dice" in vals:
                legacy_rows.append({"project": p["project"], "model": model,
                                    "dice": vals["dice"], "iou": vals.get("iou"),
                                    "domains": p["domain_count"],
                                    "includes_kub": p["includes_kub"]})
display(pd.DataFrame(legacy_rows))
display(Markdown(f"**Phase-20 (current, clean-v3, four domains, threshold 0.5, macro over images)**"))
display(domain_table[["row_type", "dataset", "n", "dice", "iou"]])
display(Markdown("_Comparison boundary: Phase 20 is not intended to prove MedFiLM, and no "
                 "Phase-21 result exists yet. Historical values are context only._"))
"""))

# --- 37 --------------------------------------------------------------------
cells.append(md("""
## 37. Phase-21 entry criteria (prospective)
"""))

cells.append(code("""
p21 = jload(AUD / "phase20_phase21_entry_criteria.json")
display(pd.DataFrame(p21["criteria"])[["id", "criterion", "met", "observed"]])
print("all criteria met:", p21["all_criteria_met"])
print("Phase 21 status:", p21["status"])
print("Phase 21 started:", p21["phase21_started"],
      "| authorization required:", p21["authorization_required"])
assert p21["phase21_started"] is False
"""))

# --- 38 --------------------------------------------------------------------
cells.append(md("""
## 38. TEST lock
"""))

cells.append(code("""
from src.utils.test_lock import verify_test_lock

lock = verify_test_lock(str(ROOT))
display(pd.DataFrame([
    {"item": "manifest_version", "value": lock["manifest_version"]},
    {"item": "test_sample_count", "value": lock["test_sample_count"]},
    {"item": "frozen sha256", "value": lock["full_test_sha256"][:40] + "…"},
    {"item": "observed sha256", "value": sha256_file(ROOT / "manifests/test.csv")[:40] + "…"},
    {"item": "test_image_reads", "value": closure["test_reads"]["test_image_reads"]},
    {"item": "test_mask_reads", "value": closure["test_reads"]["test_mask_reads"]},
    {"item": "test_inference", "value": closure["test_reads"]["test_inference"]},
    {"item": "test_visualization", "value": closure["test_reads"]["test_visualization"]},
    {"item": "final TEST evaluation phase", "value": 39},
]))
assert sha256_file(ROOT / "manifests/test.csv") == lock["full_test_sha256"]
assert all(v == 0 for v in closure["test_reads"].values())
"""))

# --- 39 --------------------------------------------------------------------
cells.append(md("""
## 39. Terminal state
"""))

cells.append(code("""
state = {
    "phase_19": "COMPLETE / HARMONIZATION PREPARATION",
    "phase_20": "SHARED GLOBAL BASELINE COMPLETE",
    "phase_20_experiment": EXP_ID,
    "architecture": "UNet++ (shared, image-only, no FiLM, no regional module)",
    "best_epoch": closure["best_epoch"],
    "best_macro_domain_dice": closure["best_macro_domain_dice"],
    "stop_reason": closure["stop_reason"],
    "checkpoint_replay": replay["verdict"],
    "phase_21": "ELIGIBLE__NOT_STARTED",
    "test": "CLOSED",
}
display(pd.DataFrame(sorted(state.items()), columns=["governance item", "state"]))

display(Markdown("### Final assertions"))
assert protocol["status"] == "PHASE20_PROTOCOL_FROZEN__AWAITING_EXECUTION"
assert freeze["current_phase20_results_used_for_selection"] is False
assert dup["n_blocking_pairs"] == 0
assert pre["all_checks_passed"] is True
assert replay["verdict"] == "PHASE20_CHECKPOINT_SELECTION_REPLAY_PASS"
assert len(per_image) == 808
assert len(sel) == 64
assert closure["independent_duplicate_runs"] == 0
assert all(v == 0 for v in closure["test_reads"].values())
assert p21["phase21_started"] is False
print("✓ All Phase-20 assertions passed.")
print("TERMINAL STATE: PHASE20_SHARED_GLOBAL_BASELINE_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED")
"""))

# --------------------------------------------------------------------------- #
nb = nbformat.v4.new_notebook(cells=cells)
# Deterministic cell ids: nbformat assigns a RANDOM 8-char id per cell, which would
# change the notebook SHA on every rebuild even with identical content.
for _i, _c in enumerate(nb.cells):
    _c["id"] = f"p20{_i:03d}"
nbformat.write(nb, str(NB_PATH))
print(f"Wrote {NB_PATH} ({len(nb.cells)} cells)")
print("Executing ...")
client = NotebookClient(nb, kernel_name="jup-venv", timeout=3600,
                        resources={"metadata": {"path": str(ROOT)}})
client.execute()

# Normalize volatile execution artifacts for a stable content-addressed SHA.
for _c in nb.cells:
    if isinstance(_c.get("metadata"), dict):
        _c["metadata"].pop("execution", None)
    _outs = _c.get("outputs")
    if _outs:
        _merged = []
        for _o in _outs:
            if (_o.get("output_type") == "stream" and _merged
                    and _merged[-1].get("output_type") == "stream"
                    and _merged[-1].get("name") == _o.get("name")):
                _p = _merged[-1]
                _pt, _ct = _p.get("text", ""), _o.get("text", "")
                if isinstance(_pt, list):
                    _pt = "".join(_pt)
                if isinstance(_ct, list):
                    _ct = "".join(_ct)
                _p["text"] = _pt + _ct
            else:
                _merged.append(_o)
        _c["outputs"] = _merged
nbformat.write(nb, str(NB_PATH))

code_cells = [c for c in nb.cells if c.cell_type == "code"]
errors = sum(1 for c in code_cells for o in c.get("outputs", []) if o.get("output_type") == "error")
counts = [c.get("execution_count") for c in code_cells]
monotonic = all(counts[i] == i + 1 for i in range(len(counts)))
embedded = sum(1 for c in code_cells for o in c.get("outputs", [])
               if o.get("output_type") == "display_data" and "image/png" in o.get("data", {}))
html_tables = sum(1 for c in code_cells for o in c.get("outputs", [])
                  if o.get("output_type") == "display_data" and "text/html" in o.get("data", {}))

print(f"Cells: {len(nb.cells)} | markdown: {sum(1 for c in nb.cells if c.cell_type == 'markdown')} "
      f"| code: {len(code_cells)}")
print("Zero tracebacks:", "PASS" if errors == 0 else f"FAIL ({errors})")
print("Monotonic exec counts (1..%d): %s" % (len(code_cells), "PASS" if monotonic else "FAIL"))
print("Embedded PNG outputs:", embedded, "| HTML tables:", html_tables)
print("Notebook SHA:", hashlib.sha256(NB_PATH.read_bytes()).hexdigest())
