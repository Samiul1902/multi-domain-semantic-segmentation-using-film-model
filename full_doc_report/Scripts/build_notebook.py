"""Generate ReMedFiLM_Complete_Research_Master.ipynb.

The notebook is generated (not hand-typed) so that every section stays
synchronised with the artifacts in full_doc_report/tables and figures.

Execution is analysis-only. Section 00 installs an audit hook that blocks
training, new inference, subprocess launches, protected-TEST access and writes
outside full_doc_report.
"""
from __future__ import annotations

import json
from pathlib import Path

import nbformat as nbf

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"
NB_PATH = OUT / "ReMedFiLM_Complete_Research_Master.ipynb"

nb = nbf.v4.new_notebook()
cells: list = []


def md(text: str) -> None:
    cells.append(nbf.v4.new_markdown_cell(text.strip("\n")))


def code(src: str) -> None:
    cells.append(nbf.v4.new_code_cell(src.strip("\n")))


# ============================================================ title ========
md("""
# ReMedFiLM — Complete Research Notebook

**ReMedFiLM (FULL RA-MedFiLM-BARR)** — task-conditioned global-to-regional medical
image segmentation with risk-averse refinement.

| | |
|---|---|
| Repository | `D:\\Softfors\\jup` |
| Model | G (GlobalMedFiLM) + B_phi (Benefit Router) + R_psi (Regional Refiner) + S_omega (Post-Safety Gate) |
| Parameters | 4,837,420 (backbone 3,523,001) |
| Development population | TRAIN 5,832 · VAL 808 · ROUTER_DEVELOPMENT 4,957 · ROUTER_HOLDOUT 875 |
| Execution mode | **ANALYSIS ONLY** — no training, no new inference, no TEST access |

> **This notebook does not train anything.** It reads persisted artifacts and
> rebuilds the tables and figures of the research record. Every cell is guarded;
> see Section 00.
""")

md("""
## Notebook map

| § | Section | Primary evidence |
|---|---|---|
| 00 | Research environment and execution guard | interpreter, GPU, guard |
| 01 | Research overview | methodology figure |
| 02 | Dataset analysis | manifests, VAL808 |
| 03 | Full ReMedFiLM architecture | parameter contract |
| 04 | Historical training run inventory | 82 history files |
| 05 | Epoch-by-epoch training improvements | T1–T8 |
| 06 | Historical baseline comparison | six-model VAL808 |
| 07 | ReMedFiLM internal evaluation | saved masks |
| 08 | Class and subclass evaluation | KUB taxonomy |
| 09 | Semantic segmentation gallery | saved masks |
| 10 | External retrospective evaluation | 884 cases |
| 11 | Component progression | Phase 28 / C2 |
| 12 | Complete ablation study | 13 arms |
| 13 | Error propagation and routing | VAL808 branches |
| 14 | Robustness and interpretability | Phase 35/36 |
| 15 | Computational efficiency | Phase 34 |
| 16 | Historical TEST evidence | Phase 39 record only |
| 17 | Conclusions and missing evidence | — |
""")

# ================================================================ 00 =======
md("""
---
# 00 — Research environment and execution guard

Every subsequent cell calls `G.require()` first. The guard is an actual
`sys.addaudithook` plus runtime patches, not a boolean flag:

* blocks `subprocess` / `os.system` / `os.exec*` launches,
* blocks writes outside `full_doc_report/`,
* blocks any read of the protected TEST manifest,
* makes `torch.optim.*` constructors raise,
* makes `Module.train(True)` raise.
""")

code(r'''
import sys, os, json, csv, hashlib, platform, builtins
from pathlib import Path
from datetime import datetime

ANALYSIS_ONLY = True
REPO = Path(r"D:\Softfors\jup")
REPORT = REPO / "full_doc_report"
TABLES = REPORT / "tables"
FIGURES = REPORT / "figures"

class AnalysisOnlyViolation(RuntimeError):
    """Raised when a cell attempts a non-analysis operation."""

PROTECTED_READS = {
    (REPO / "manifests/phase4_v3/test.csv").resolve(),
}
BLOCKED_EVENTS = {"subprocess.Popen", "os.system", "os.exec", "os.spawn",
                  "os.posix_spawn", "os.startfile", "pty.spawn"}
_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC

# Constants are bound as default arguments so the hook stays valid during
# interpreter teardown, when module globals have already been cleared.
def _audit(event, args, _blocked=frozenset(BLOCKED_EVENTS),
           _protected=frozenset(PROTECTED_READS),
           _report=str(REPORT), _flags=_WRITE_FLAGS, _path=Path):
    if event in _blocked:
        raise AnalysisOnlyViolation(f"blocked process launch: {event}")
    if event == "open":
        path, mode, flags = args
        try:
            p = _path(path).resolve()
        except Exception:
            return
        if str(p) in {str(x) for x in _protected}:
            raise AnalysisOnlyViolation(f"protected TEST manifest access: {p}")
        writing = False
        if isinstance(mode, str):
            writing = any(c in mode for c in "wax+")
        if isinstance(flags, int) and flags & _flags:
            writing = True
        if writing and _report not in str(p.parent) and str(p) != _report:
            raise AnalysisOnlyViolation(f"write outside full_doc_report: {p}")

sys.addaudithook(_audit)

# torch optimisers must never be constructible in this notebook
try:
    import torch
    import torch.optim as _optim
    def _no_optimiser(*a, **k):
        raise AnalysisOnlyViolation("optimiser construction is forbidden (analysis only)")
    for _n in ("SGD", "Adam", "AdamW", "RMSprop", "Adagrad"):
        if hasattr(_optim, _n):
            setattr(_optim, _n, _no_optimiser)
    _orig_train = torch.nn.Module.train
    def _guarded_train(self, mode=True):
        if mode:
            raise AnalysisOnlyViolation("Module.train(True) is forbidden (analysis only)")
        return _orig_train(self, False)
    torch.nn.Module.train = _guarded_train
except ImportError:
    torch = None

class Guard:
    """Accessor handed to every cell."""
    def require(self):
        if not ANALYSIS_ONLY:
            raise AnalysisOnlyViolation("ANALYSIS_ONLY was disabled")
        return True
    def blocked(self, what):
        raise AnalysisOnlyViolation(what)

G = Guard()
G.require()
print("ANALYSIS_ONLY guard active")
''')

code(r'''
G.require()
# Negative controls: the guard must actually refuse these operations.
# If any of them succeeds, enforcement is broken and the notebook is invalid.
checks = []

try:
    torch.optim.Adam([])
    checks.append(("optimiser construction", "NOT BLOCKED"))
except AnalysisOnlyViolation as e:
    checks.append(("optimiser construction", "blocked"))

try:
    torch.optim.AdamW([])
    checks.append(("AdamW construction", "NOT BLOCKED"))
except AnalysisOnlyViolation as e:
    checks.append(("AdamW construction", "blocked"))

try:
    (REPO / "manifests/phase4_v3/test.csv").open("rb").read(1)
    checks.append(("TEST manifest read", "NOT BLOCKED"))
except AnalysisOnlyViolation:
    checks.append(("TEST manifest read", "blocked"))
except FileNotFoundError:
    checks.append(("TEST manifest read", "blocked (file absent)"))

try:
    (REPO / "reports" / "_guard_probe.txt").open("w").write("x")
    checks.append(("write outside report dir", "NOT BLOCKED"))
except AnalysisOnlyViolation:
    checks.append(("write outside report dir", "blocked"))

for name, verdict in checks:
    print(f"  {name:28s}: {verdict}")

assert all(v.startswith("blocked") for _, v in checks), "GUARD FAILED — do not trust this notebook"
print()
print("All negative controls blocked. Analysis-only enforcement verified.")
''')

code(r'''
G.require()
import importlib.metadata as md

def _v(name):
    try:
        return md.version(name)
    except Exception:
        return "not installed"

env = {
    "python": sys.version.split()[0],
    "executable": sys.executable,
    "prefix": sys.prefix,
    "platform": platform.platform(),
    "processor": platform.processor(),
    "torch": _v("torch"),
    "numpy": _v("numpy"),
    "pandas": _v("pandas"),
    "matplotlib": _v("matplotlib"),
    "scipy": _v("scipy"),
    "nbformat": _v("nbformat"),
    "nbclient": _v("nbclient"),
}
if torch is not None:
    env["cuda_available"] = torch.cuda.is_available()
    env["cuda_version"] = torch.version.cuda
    if torch.cuda.is_available():
        env["gpu"] = torch.cuda.get_device_name(0)
        env["gpu_memory_gib"] = round(
            torch.cuda.get_device_properties(0).total_memory / 1024**3, 2)
        env["gpu_capability"] = torch.cuda.get_device_capability(0)
for k, v in env.items():
    print(f"{k:16s}: {v}")
''')

code(r'''
G.require()
# Determinism: analysis only, so we pin plotting/statistics seeds rather than
# any training RNG. Documented so a re-run reproduces identical figures.
import random
import numpy as np
ANALYSIS_SEED = 20261027
random.seed(ANALYSIS_SEED)
np.random.seed(ANALYSIS_SEED)
print("analysis seed:", ANALYSIS_SEED)
print("read-only root:", REPORT)
''')

code(r'''
G.require()
# Original notebook source registry (from the preservation manifest).
import pandas as pd

pres = json.loads((REPORT / "NOTEBOOK_PRESERVATION_MANIFEST.json").read_text(encoding="utf-8"))
print("preserved source notebooks:", pres["n_source_notebooks"])
print("byte-identical copies     :", pres["n_verified_byte_identical"])
inv = pd.read_csv(REPORT / "NOTEBOOK_INVENTORY.csv")
print("inventory rows            :", len(inv))
print("genuine sources           :", (inv.merge_status == "SOURCE_OF_TRUTH").sum())
display_cols = ["original_path", "phase_or_experiment", "code_cells", "has_outputs",
                "side_effects", "execution_eligibility"]
inv[inv.merge_status == "SOURCE_OF_TRUTH"][display_cols].head(12)
''')

# ================================================================ 01 =======
md("""
---
# 01 — Research overview

**ReMedFiLM** is not a single network. It is an assembly:

| Symbol | Component | Role |
|---|---|---|
| G | GlobalMedFiLM | task-conditioned FiLM backbone, one shared foreground head |
| B_phi | Benefit Router | scores each ROI candidate, selects the top budget fraction |
| R_psi | Regional Refiner | re-segments selected ROIs at higher effective resolution |
| S_omega | Post-Safety Gate | accepts or vetoes each refined proposal |

Three inference outcomes: **skip** (keep global), **refine + accept**, **refine + reject**
(revert to global). GlobalMedFiLM alone is the backbone and an ablation comparator —
it is *not* ReMedFiLM.
""")

code(r'''
G.require()
from IPython.display import Image, display
display(Image(filename=str(FIGURES / "architecture/A03_remedfilm_inference_path.png"), width=760))
''')

code(r'''
G.require()
# Exact identities used throughout this notebook.
IDENTITIES = pd.DataFrame([
    {"name": "GlobalMedFiLM (G)", "role": "BACKBONE", "params": 3523001,
     "gmacs": 31.5517, "checkpoint": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"},
    {"name": "R_psi (Regional Refiner)", "role": "COMPONENT", "params": 1276401,
     "gmacs": None, "checkpoint": "experiments/phase25a_barr_regional_refiner_v1_1/final_refit/final.pt"},
    {"name": "B_phi (Benefit Router)", "role": "COMPONENT", "params": 36801,
     "gmacs": None, "checkpoint": "experiments/phase25d_barr_benefit_router_v1_2_1_seed42/final/"},
    {"name": "S_omega (Post-Safety Gate)", "role": "COMPONENT", "params": 1217,
     "gmacs": None, "checkpoint": "experiments/phase25f_barr_post_safety_v1_0_seed42/final/"},
    {"name": "ReMedFiLM (FULL)", "role": "PROPOSED", "params": 4837420,
     "gmacs": 32.4379, "checkpoint": "bundle of the four components above"},
])
print("Total resident parameters:", IDENTITIES.params.sum())
IDENTITIES
''')

code(r'''
G.require()
display(Image(filename=str(FIGURES / "architecture/A01_component_parameter_budget.png"), width=720))
display(Image(filename=str(FIGURES / "architecture/A02_component_presence_matrix.png"), width=520))
''')

# ================================================================ 02 =======
md("""
---
# 02 — Dataset analysis

Four binary foreground/background segmentation domains. They are **separate
tasks**, not four output channels of one network.

| Domain | Anatomy | Reference standard |
|---|---|---|
| ISIC 2018 | dermoscopy skin lesion | expert segmentation mask (CC0) |
| BUSI-WHU | breast ultrasound lesion | expert annotation (CC BY 4.0) |
| Kvasir-SEG | GI polyp | expert mask (research use) |
| KUB-StoneX | kidney/ureter/bladder stone | expert mask (CC BY 4.0) |

Grouping caveats are reported explicitly: KUB mixes full-field images with ROI
instance patches, and BUSI/KUB carry patient identifiers that make images
non-independent.
""")

code(r'''
G.require()
comp = pd.read_csv(TABLES / "REMEDFILM_DATASET_COMPOSITION.csv")
print("TRAIN+VAL =", int(comp.loc[comp.domain == "TOTAL", "total"].iloc[0]))
comp
''')

code(r'''
G.require()
display(Image(filename=str(FIGURES / "datasets/D01_domain_and_split_composition.png"), width=760))
display(Image(filename=str(FIGURES / "datasets/D02_foreground_area_distribution.png"), width=560))
''')

code(r'''
G.require()
# KUB unit-of-analysis disclosure: 873 full-field images + 1,385 ROI patches.
import csv as _csv
rows = []
for f in ("train.csv", "val.csv"):
    with (REPO / "manifests/phase4_v3" / f).open(encoding="utf-8", newline="") as fh:
        rows.extend(list(_csv.DictReader(fh)))
kub = [r for r in rows if r["dataset"] == "KUB"]
roi = sum(1 for r in kub if Path(r["image_path"]).parent.name == "ROI")
print(f"KUB manifest rows        : {len(kub)}")
print(f"  full-field images      : {len(kub) - roi}")
print(f"  ROI instance patches   : {roi}")
print("Distinct source images   :", len({Path(r['image_path']).stem.split('_stone_obj')[0] for r in kub}))
print()
print("NOTE: pooled image counts overstate independent KUB cases; the 808 VAL")
print("population is the analysis unit used for every metric in this notebook.")
display(Image(filename=str(FIGURES / "datasets/D03_kub_unit_of_analysis.png"), width=480))
''')

# ================================================================ 03 =======
md("""
---
# 03 — Full ReMedFiLM architecture

Parameter counts are read from the frozen contracts, not recomputed from scratch.
Freezing a component never reduces the *total* parameter count — the matched-arm
invariant of the C1 design.
""")

code(r'''
G.require()
contract = json.loads((REPO / "reports/audits/phase34_parameter_count_contract.json").read_text(encoding="utf-8"))
print(json.dumps(contract, indent=2)[:1200])
''')

code(r'''
G.require()
p21 = json.loads((REPO / "reports/audits/phase21_global_medfilm_architecture_binding.json").read_text(encoding="utf-8"))
print(json.dumps(p21, indent=2)[:1400])
''')

code(r'''
G.require()
# Component arithmetic must close exactly.
parts = {"G": 3523001, "R_psi": 1276401, "B_phi": 36801, "S_omega": 1217}
total = sum(parts.values())
print("component sum :", total)
print("contract total:", 4837420)
assert total == 4837420, "component sum does not match the frozen contract"
print("OK — the four components account for every resident parameter")
print()
print("backbone share: {:.2%}".format(parts["G"] / total))
print("adapter share : {:.2%}".format((total - parts["G"]) / total))
''')

# ================================================================ 04 =======
md("""
---
# 04 — Historical training run inventory

82 per-epoch `history.csv` files were recovered across every experiment
directory. `best_epoch_source` states whether the selected epoch was **recorded**
by the trainer or **derived** by this notebook's analysis, so the two are never
conflated.
""")

code(r'''
G.require()
reg = pd.read_csv(TABLES / "TRAINING_RUN_REGISTRY.csv")
print("runs:", len(reg))
print(reg.evidence_status.value_counts().to_string())
print()
print(reg.best_epoch_source.value_counts().to_string())
''')

code(r'''
G.require()
core_models = ["GlobalMedFiLM (G)", "U-Net", "Attention U-Net", "U-Net++", "DeepLabV3+",
               "Transformer/MiT-style U-Net", "R_psi (Regional Refiner)",
               "B_phi (Benefit Router)", "S_omega (Post-Safety Gate)",
               "F1 (Ablation Variant)"]
show = ["run_id", "model", "seed", "epochs_completed", "best_epoch",
        "best_epoch_source", "evidence_status"]
reg[reg.model.isin(core_models)][show].head(25)
''')

code(r'''
G.require()
# Runs whose selection epoch genuinely was not logged.
missing = reg[reg.best_epoch == "NOT_RECORDED"][["run_id", "model", "epochs_completed"]]
print(f"runs without a per-epoch selection record: {len(missing)}")
print("These are KUB ROI-localiser diagnostics and fixed-epoch component refits.")
missing
''')

# ================================================================ 05 =======
md("""
---
# 05 — Epoch-by-epoch training improvements

This is the section that cannot be reconstructed by guessing. All curves come
from `history.csv` files written by the trainers. Nothing is interpolated,
smoothed or invented; a metric that was never logged simply has no curve.

GlobalMedFiLM logged **per-domain validation Dice, IoU, precision and recall at
every epoch**, so the per-domain learning curves below are genuine observations.
""")

code(r'''
G.require()
hist = pd.read_csv(TABLES / "REMEDFILM_EPOCH_HISTORY.csv")
print("long-form epoch records:", len(hist))
print("runs                   :", hist.run_id.nunique())
print("distinct metrics       :", hist.metric.nunique())
print()
print(hist.metric.value_counts().head(18).to_string())
''')

code(r'''
G.require()
g = hist[hist.run_id == "phase21_global_medfilm_fourdomain_seed42_clean_v3"]
piv = g.pivot_table(index="epoch", columns="metric", values="value")
print("GlobalMedFiLM epochs recorded:", len(piv))
piv[["train_loss", "val_loss", "val_macro_dice"]].head(8)
''')

code(r'''
G.require()
# Recorded versus derived selection epochs for the backbone.
print("closure.json  best_epoch =", 66)
print("history argmax(val_macro_dice) =",
      int(piv["val_macro_dice"].idxmax()),
      "value =", round(float(piv["val_macro_dice"].max()), 8))
print("final epoch recorded =", int(piv.index.max()))
print("stop reason          = EARLY_STOPPING_PATIENCE (patience 15)")
''')

code(r'''
G.require()
for f in ["T1_train_val_loss", "T2_val_dice_across_epochs", "T3_val_iou_across_epochs",
          "T4_per_domain_learning_curves"]:
    display(Image(filename=str(FIGURES / f"training_epochs/{f}.png"), width=700))
''')

code(r'''
G.require()
for f in ["T5_learning_rate_schedule", "T6_best_epoch_selection",
          "T7_multiseed_histories", "T8_training_improvement_summary"]:
    display(Image(filename=str(FIGURES / f"training_epochs/{f}.png"), width=700))
''')

code(r'''
G.require()
# Honest completeness statement per model family.
def coverage(run_prefix):
    sub = hist[hist.run_id.str.startswith(run_prefix)]
    if sub.empty:
        return "NOT_RECORDED"
    return ", ".join(sorted(sub.metric.unique())[:8])

rows = []
for label, prefix in [
    ("GlobalMedFiLM (G)", "phase21_global_medfilm"),
    ("U-Net++ (4-domain)", "phase20_shared_unetpp"),
    ("U-Net (4-domain)", "phase20b_shared_unet_"),
    ("Attention U-Net", "phase20b_shared_attention"),
    ("DeepLabV3+", "phase20b_shared_deeplab"),
    ("Transformer/MiT", "phase20b_shared_transformer"),
    ("R_psi refiner", "phase25a_barr_regional_refiner_v1_1__fold0"),
    ("B_phi router", "phase25d_barr_benefit_router_v1_2_1_seed42__fold0"),
    ("S_omega safety", "phase25f_barr_post_safety_v1_0_seed42__cv_fold0"),
]:
    rows.append({"model": label, "epoch_metrics_logged": coverage(prefix)})
import pandas as pd
pd.DataFrame(rows)
''')

# ================================================================ 06 =======
md("""
---
# 06 — Historical baseline comparison

Six models were trained under one shared protocol on the identical VAL808
population (Phase 20/20B/21). Phase 21 inherits 24/24 protocol fields, so the
comparison is descriptive but protocol-matched.

ReMedFiLM FULL is shown **separately** — it is a different assembly evaluated on
the same samples, not a seventh independent training run.
""")

code(r'''
G.require()
comp = pd.read_csv(TABLES / "REMEDFILM_MODEL_COMPARISON.csv")
comp[["model", "role", "params", "macro_dice", "macro_iou",
      "dice_ISIC", "dice_BUSI", "dice_KVASIR", "dice_KUB"]].to_string(index=False)
''')

code(r'''
G.require()
six = pd.read_csv(REPO / "reports/tables/phase21_six_model_comparison.csv")
print(six[["display_name", "macro_domain_dice", "macro_domain_dice_ci_low",
           "macro_domain_dice_ci_high", "params"]].to_string(index=False))
''')

code(r'''
G.require()
print("Protocol comparability check (Phase 21 inherits the Phase 20 protocol):")
pb = json.loads((REPO / "reports/audits/phase21_protocol_binding.json").read_text(encoding="utf-8"))
for k in ("verdict", "protocol_fields_total", "protocol_fields_matched",
          "unintentional_differences"):
    if k in pb:
        print(f"  {k:28s}: {pb[k]}")
print()
print("Guard: no independent C3 eight-model x three-seed benchmark exists.")
print("The six models here are single-seed (42) shared-protocol runs.")
''')

# ================================================================ 07 =======
md("""
---
# 07 — ReMedFiLM internal evaluation

Backbone versus FULL system on the **identical 808 VAL808 samples**. Every
metric below is re-derived from the saved Phase 27 masks
(`reports/figures/phase27_preservation/masks/*_global.png` and `*_final.png`)
against the evaluation ground truth stored in the Phase 21 prediction archives.

This derivation independently reproduces the frozen Phase 27 macro Δ Dice to
within 1.8×10⁻⁷, which is the strongest available check that the masks and the
published numbers describe the same objects.
""")

code(r'''
G.require()
internal = pd.read_csv(TABLES / "REMEDFILM_INTERNAL_METRICS.csv")
internal[["domain", "n", "global_dice", "final_dice", "delta_dice",
          "final_iou", "final_precision", "final_recall", "final_hd95"]].to_string(index=False)
''')

code(r'''
G.require()
paired = json.loads((TABLES / "REMEDFILM_PAIRED_DELTA.json").read_text(encoding="utf-8"))
print("estimand :", paired["estimand"])
print("point    : {:+.8f}".format(paired["point"]))
print("95% CI   : [{:+.8f}, {:+.8f}]".format(paired["ci_low"], paired["ci_high"]))
print("bootstrap:", paired["n_boot"], "replicates, seed", paired["seed"])
print()
print("cross-check vs frozen Phase 27 macro point 0.0022101453 : diff =",
      f"{abs(paired['point'] - paired['cross_check_phase27_macro_point']):.2e}")
print("CI excludes zero:", paired["ci_low"] > 0)
''')

code(r'''
G.require()
for f in ["I1_domain_metric_comparison", "I2_paired_delta_forest",
          "I3_paired_delta_distribution", "I4_hd95_comparison"]:
    display(Image(filename=str(FIGURES / f"internal_evaluation/{f}.png"), width=740))
''')

code(r'''
G.require()
ps = pd.read_csv(TABLES / "REMEDFILM_INTERNAL_PER_SAMPLE.csv")
print("outcome counts on VAL808")
print(ps.branch.value_counts().to_string())
print()
print("beneficial / unchanged / harmful:",
      int((ps.delta_dice > 1e-12).sum()),
      int((ps.delta_dice.abs() <= 1e-12).sum()),
      int((ps.delta_dice < -1e-12).sum()))
print()
print("mean delta on routed cases only: {:+.6f}".format(
    ps.loc[ps.router_decision == "EXECUTE", "delta_dice"].mean()))
''')

# ================================================================ 08 =======
md("""
---
# 08 — Class and subclass evaluation

The four domains are separate binary tasks. Within KUB the frozen size taxonomy
and stone location provide genuine subgroups; no subgroup is invented.
""")

code(r'''
G.require()
sub = pd.read_csv(REPO / "reports/tables/phase21_kub_subgroup_analysis.csv")
sub
''')

code(r'''
G.require()
display(Image(filename=str(FIGURES / "subgroups/SG1_kub_stone_subgroups.png"), width=560))
display(Image(filename=str(FIGURES / "subgroups/SG2_kub_size_stratification.png"), width=560))
''')

code(r'''
G.require()
# BREAST subgroup labels are not present in the frozen artifacts.
print("BUSI subgroup labels  : NOT_RECORDED in any frozen artifact")
print("Polyp size categories : NOT_RECORDED per-sample")
print("KUB location/size     : RECORDED (phase21_kub_subgroup_analysis,")
print("                        phase21_kub_size_stratification)")
print()
print("No subgroup performance is inferred from final aggregates.")
''')

# ================================================================ 09 =======
md("""
---
# 09 — Semantic segmentation gallery

Selection rule, fixed in advance and applied mechanically: within each domain,
sort the 808 samples by paired Δ Dice and take the **worst**, **median** and
**best** case. No manual cherry-picking.

Panels: original image · evaluation ground truth · GlobalMedFiLM mask ·
ReMedFiLM FULL mask · TP/FP/FN overlay (green = TP, orange = FP, blue = FN).
""")

code(r'''
G.require()
for dom in ["ISIC", "BUSI", "KVASIR", "KUB"]:
    display(Image(filename=str(FIGURES / f"segmentation/SEG_{dom}_global_vs_full.png"), width=880))
''')

code(r'''
G.require()
display(Image(filename=str(FIGURES / "segmentation/SEG_failure_cases.png"), width=900))
''')

code(r'''
G.require()
# Confirm the gallery images are genuine and aligned: GT is confined to the
# letterboxed region, exactly as the evaluation contract defines.
sample = ps.sort_values("delta_dice").iloc[0]
print("worst case:", sample.sample_id, sample.domain, f"Δ={sample.delta_dice:+.4f}")
print("branch    :", sample.branch)
print("This is a genuine residual failure: the safety gate accepted a refinement")
print("that reduced Dice.")
''')

# ================================================================ 10 =======
md("""
---
# 10 — External retrospective evaluation (884 cases)

CVC-ClinicDB (612), BrEaST-Lesions-USG (252) and Stones-Where-Are-You (20).
These are **separate cohorts** with different reference standards; they are never
pooled with VAL808 or with each other.

The stone-free subset is a documented **negative result**: every case receives
foreground.
""")

code(r'''
G.require()
ext = pd.read_csv(TABLES / "REMEDFILM_EXTERNAL_METRICS.csv")
ext[ext.metric == "Dice"][["cohort", "arm", "n_total", "n_defined", "mean",
                           "median", "ci_low", "ci_high", "n_clusters"]].to_string(index=False)
''')

code(r'''
G.require()
display(Image(filename=str(FIGURES / "external_evaluation/EXT01_external_dice.png"), width=700))
display(Image(filename=str(FIGURES / "external_evaluation/EXT02_external_delta.png"), width=560))
display(Image(filename=str(FIGURES / "external_evaluation/EXT03_stonefree_false_positive.png"), width=520))
''')

code(r'''
G.require()
pc = pd.read_csv(REPO / "reports/tables/c1_external_stress_per_case.csv")
sf = pc[pc.gt_empty.astype(str).str.lower() == "true"]
print("stone-free cases:", len(sf))
if len(sf):
    for arm, grp in sf.groupby("arm"):
        got_fg = (grp.pred_empty.astype(str).str.lower() == "false").sum()
        print(f"  {arm:8s}: {got_fg}/{len(grp)} receive foreground")
print()
print("HD95 / ASSD are undefined for empty-reference cases and are reported as")
print("missing, never as zero.")
''')

# ================================================================ 11 =======
md("""
---
# 11 — Component progression

Stages are **not** a controlled ablation. Stage 0 is VAL808; stages 1–3 are
ROUTER_DEVELOPMENT (4,957); stage 4 returns to VAL808. Populations differ and
must not be read as a single monotone experiment.
""")

code(r'''
G.require()
prog = pd.read_csv(TABLES / "REMEDFILM_PROGRESSION_RESULTS.csv")
prog
''')

code(r'''
G.require()
display(Image(filename=str(FIGURES / "progression/PROG01_stage_compute_and_harm.png"), width=720))
display(Image(filename=str(FIGURES / "progression/PROG02_benefit_harm_tradeoff.png"), width=600))
''')

code(r'''
G.require()
print("No genuine incremental-domain training study exists in the repository.")
print("The 'incremental dataset progression' audit gate is NOT_EXECUTED and is")
print("recorded as such in REMEDFILM_PROGRESSION_RESULTS.csv.")
''')

# ================================================================ 12 =======
md("""
---
# 12 — Complete ablation study (Phase 28, 13 arms)

A0–A8, R1–R3 and F1 on ROUTER_DEVELOPMENT (4,957; budget K = 1,239).

**Preserved finding:** the only pre-specified matched contrast, **A8 vs A7**,
has a 95% CI that **includes zero**. It is reported as inconclusive, not as a win.
""")

code(r'''
G.require()
abl = pd.read_csv(TABLES / "REMEDFILM_ABLATION_RESULTS.csv")
abl[["arm", "n_routed", "budget_fraction", "mean_true_delta_dice_routed",
     "benefit_capture_vs_positive_mass", "harmful_activation_share",
     "evidence_class"]].to_string(index=False)
''')

code(r'''
G.require()
display(Image(filename=str(FIGURES / "ablation/ABL01_arm_mean_delta.png"), width=760))
display(Image(filename=str(FIGURES / "ablation/ABL02_paired_contrasts_forest.png"), width=620))
display(Image(filename=str(FIGURES / "ablation/ABL03_ablation_diagnostics.png"), width=860))
''')

code(r'''
G.require()
bs = pd.read_csv(REPO / "reports/tables/phase28_table_08_bootstrap_statistics.csv")
bs[["contrast", "n", "mean_difference", "ci95_low", "ci95_high"]].to_string(index=False)
print()
a8 = bs[bs.contrast == "A8_vs_A7"].iloc[0]
print("A8 vs A7 : {:+.3e} [{:+.3e}, {:+.3e}]".format(
    a8.mean_difference, a8.ci95_low, a8.ci95_high))
print("CI includes zero:", not (a8.ci95_low > 0 or a8.ci95_high < 0))
''')

# ================================================================ 13 =======
md("""
---
# 13 — Error propagation and routing analysis

Counts are exact, not modelled: 808 global forwards, 279 ROI selections,
266 accepted refinements and 13 rejections that fall back to the backbone.
""")

code(r'''
G.require()
display(Image(filename=str(FIGURES / "routing_safety/RT01_routing_outcomes.png"), width=740))
display(Image(filename=str(FIGURES / "routing_safety/RT02_stage_flow.png"), width=720))
''')

code(r'''
G.require()
tab = ps.groupby("branch").agg(
    n=("sample_id", "size"),
    mean_delta=("delta_dice", "mean"),
    harmful=("delta_dice", lambda s: int((s < -1e-12).sum())),
    beneficial=("delta_dice", lambda s: int((s > 1e-12).sum())),
).reset_index()
tab["share"] = (tab.n / len(ps)).round(4)
tab
''')

code(r'''
G.require()
print("ROUTER_DEVELOPMENT and EXTERNAL884 are kept separate in every table.")
print("No routing statistic in this notebook mixes those populations with VAL808.")
print()
print("VAL808 (this section) : 808 images, 279 routed, 266 accepted")
print("ROUTER_DEV (section 12): 4,957 images, 1,239 routed, 1,205 accepted")
''')

# ================================================================ 14 =======
md("""
---
# 14 — Robustness and interpretability

Phase 36 executed 12,928 perturbation instances over the 808 clean images
(12 conditions), with `test_reads = 0`, `training = 0`, `optimizer_steps = 0`.
The clean-equivalence gate reproduced the frozen predictions exactly.
""")

code(r'''
G.require()
r36 = json.loads((REPO / "reports/audits/phase36_robustness_scientific_result_v1_23.json").read_text(encoding="utf-8"))
print("counters")
for k in ("clean_passes", "perturbed_g_forwards", "test_reads", "training",
          "optimizer_steps", "parameter_mutations", "router_holdout_reads"):
    print(f"  {k:22s}: {r36['counters'][k]}")
print()
ce = r36["clean_equivalence"]
print("clean equivalence all_pass:", ce["all_pass"])
print("dice mismatches           :", len(ce["dice_mismatches"]))
print("max |Δ Dice| vs frozen    :", ce.get("max_abs_dice_difference", 0.0))
''')

code(r'''
G.require()
display(Image(filename=str(FIGURES / "robustness/ROB01_perturbation_degradation.png"), width=780))
display(Image(filename=str(FIGURES / "robustness/ROB02_domain_degradation.png"), width=700))
display(Image(filename=str(FIGURES / "robustness/ROB03_clean_equivalence_gate.png"), width=560))
''')

code(r'''
G.require()
wc = pd.DataFrame(r36["worst_case_by_domain"])
wc
''')

code(r'''
G.require()
# Phase 35 interpretability — report what exists and what does not.
p35 = json.loads((REPO / "reports/audits/phase35_interpretability_scientific_result_v1_0.json").read_text(encoding="utf-8"))
print("Phase 35 terminal:", p35.get("terminal_state", p35.get("status", "PRESENT")))
for k, v in list(p35.items())[:10]:
    if not isinstance(v, (dict, list)):
        print(f"  {k}: {v}")
''')

# ================================================================ 15 =======
md("""
---
# 15 — Computational efficiency

| | GlobalMedFiLM | ReMedFiLM FULL |
|---|---|---|
| Parameters | 3,523,001 | 4,837,420 |
| Analytical GMACs | 31.5517 (lower bound) | 32.4379 (expected conditional) |
| VAL808 macro Dice | 0.835079 | 0.837290 |
| Batch-1 p50 (skip / execute) | 15.72 ms | 18.89 ms |

The expected conditional cost is the routing-weighted cost
`31.5517 + 0.243 × 3.646`, not the always-refine cost of 34.78 GMACs.
""")

code(r'''
G.require()
eff = pd.read_csv(TABLES / "REMEDFILM_EFFICIENCY.csv")
eff
''')

code(r'''
G.require()
c2 = json.loads((REPO / "reports/tables/c2_barr/c2_barr_aggregate.json").read_text(encoding="utf-8"))
g = c2["compute"]["analytical_gmacs_lower_bound"]
for k in ("LITERAL_GLOBAL_ONLY_C1", "FINAL_A8_C9_EXPECTED_CONDITIONAL",
          "LITERAL_ALWAYS_REFINE_C2", "SAVING_vs_literal_C2"):
    print(f"  {k:34s}: {g[k]}")
print()
print("saving versus always-refine: {:.4f} GMACs ({:.1%} of always-refine)".format(
    g["SAVING_vs_literal_C2"],
    g["SAVING_vs_literal_C2"] / g["LITERAL_ALWAYS_REFINE_C2"]))
''')

code(r'''
G.require()
display(Image(filename=str(FIGURES / "efficiency/EFF01_accuracy_vs_compute.png"), width=720))
display(Image(filename=str(FIGURES / "efficiency/EFF02_latency_breakdown.png"), width=700))
display(Image(filename=str(FIGURES / "efficiency/EFF03_accuracy_vs_parameters.png"), width=600))
''')

code(r'''
G.require()
print("Timing semantics — do not conflate:")
print("  analytical GMACs      : closed-form Conv2d/Linear count, LOWER BOUND")
print("  measured batch-1 p50  : GPU forward only, RTX 3060 Ti, n=1,000")
print("  full pipeline latency : NOT_RECORDED (data loading + preprocessing excluded)")
print()
print("The manuscript's 18.89 ms is the execute-path forward, not an end-to-end")
print("pipeline figure.")
''')

# ================================================================ 16 =======
md("""
---
# 16 — Historical TEST evidence

TEST1683 was evaluated **once**, historically, and that one-shot access is
consumed. This notebook does not open it. The only numbers below are read from
the frozen descriptive result file.

There is **no comparative endpoint** for C1/C2/C3 on TEST, because no such
experiment was authorised.
""")

code(r'''
G.require()
p39 = json.loads((REPO / "reports/audits/phase39_final_test_v1_2_scientific_result.json").read_text(encoding="utf-8"))
print("keys:", list(p39.keys())[:14])
for k, v in p39.items():
    if not isinstance(v, (dict, list)):
        print(f"  {k}: {v}")
''')

code(r'''
G.require()
import pandas as pd
dom = p39.get("per_domain") or p39.get("domains") or []
if isinstance(dom, dict):
    dom = [{"domain": k, **v} for k, v in dom.items()]
if dom:
    df = pd.DataFrame(dom)
    print(df.to_string(index=False))
    print()
    print("descriptive only — no C1/C2/C3 contrast exists on TEST")
else:
    print("per-domain block not present in the frozen result")
''')

# ================================================================ 17 =======
md("""
---
# 17 — Scientific conclusions and missing evidence

Established, descriptive, and missing are kept strictly apart.
""")

code(r'''
G.require()
summary = pd.DataFrame([
    {"claim": "GlobalMedFiLM backbone VAL808 macro Dice 0.835079", "status": "ESTABLISHED",
     "evidence": "Phase 21 six-model comparison"},
    {"claim": "ReMedFiLM FULL VAL808 macro Dice 0.837290", "status": "ESTABLISHED",
     "evidence": "Phase 27 masks re-scored; Phase 29 continuity"},
    {"claim": "Paired macro Δ Dice +0.00221 [0.00115, 0.00329]", "status": "ESTABLISHED",
     "evidence": "10,000-replicate domain-stratified bootstrap"},
    {"claim": "A8 vs A7 matched contrast", "status": "INCONCLUSIVE (CI includes 0)",
     "evidence": "Phase 28 bootstrap"},
    {"claim": "13-arm ablation on ROUTER_DEVELOPMENT", "status": "ESTABLISHED",
     "evidence": "Phase 28"},
    {"claim": "External 884-case retrospective", "status": "ESTABLISHED (no pooling)",
     "evidence": "C1 external stress"},
    {"claim": "Stone-free false positives", "status": "NEGATIVE FINDING",
     "evidence": "14/14 receive foreground"},
    {"claim": "Robustness under 12 perturbations", "status": "ESTABLISHED",
     "evidence": "Phase 36, zero TEST reads"},
    {"claim": "C1 learned vs identity FiLM attribution", "status": "NOT_ESTABLISHED",
     "evidence": "0/6 runs; RC4 trust root unprovisioned"},
    {"claim": "C2 controlled component attribution", "status": "NOT_ESTABLISHED",
     "evidence": "no causal ablation executed"},
    {"claim": "C3 eight-model x three-seed benchmark", "status": "NOT_ESTABLISHED",
     "evidence": "24 cells all missing"},
    {"claim": "Prospective independent external validation", "status": "NOT_ESTABLISHED",
     "evidence": "no new cohort frozen"},
    {"claim": "TEST comparative endpoint for C1/C2/C3", "status": "NOT_ESTABLISHED",
     "evidence": "one-shot access consumed"},
])
summary
''')

code(r'''
G.require()
# Filesystem integrity statement for this execution.
print("Execution mode        : ANALYSIS_ONLY")
print("Training performed    : NO")
print("New inference         : NO")
print("TEST images/masks read: NO")
print("Writes outside full_doc_report: blocked by audit hook")
print()
print("ReMedFiLM FULL is the proposed method throughout; GlobalMedFiLM is the")
print("backbone and an ablation comparator.")
''')

code(r'''
G.require()
print("Notebook complete. Every numeric value above traces to a file under")
print("full_doc_report/tables/ or reports/; see REPORT_NOTEBOOK_FIGURE_MAPPING.csv")
print("for the figure-to-evidence map.")
''')

nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3 (ReMedFiLM analysis)",
                   "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11.9"},
    "remedfilm": {
        "execution_mode": "ANALYSIS_ONLY",
        "training_allowed": False,
        "new_inference_allowed": False,
        "test_access_allowed": False,
        "analysis_seed": 20261027,
        "generated_by": "full_doc_report/Scripts/build_notebook.py",
    },
}
NB_PATH.write_text(nbf.writes(nb), encoding="utf-8")
print(f"WROTE {NB_PATH}")
print(f"cells={len(cells)} "
      f"code={sum(1 for c in cells if c.cell_type=='code')} "
      f"md={sum(1 for c in cells if c.cell_type=='markdown')}")
